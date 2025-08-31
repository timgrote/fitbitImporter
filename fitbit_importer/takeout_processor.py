#!/usr/bin/env python3
"""Process Google Takeout Fitbit data and convert to unified format."""

import os
import sys
import json
import zipfile
import shutil
from pathlib import Path
from datetime import datetime
import pandas as pd
import click
from typing import Dict, List, Optional
import configparser


class TakeoutProcessor:
    """Process Google Takeout Fitbit data exports."""
    
    # High-value directories to extract
    TARGET_PATHS = {
        'calories': 'Fitbit/Global Export Data/calories-*.json',
        'steps': 'Fitbit/Global Export Data/steps-*.json',
        'distance': 'Fitbit/Global Export Data/distance-*.json',
        'altitude': 'Fitbit/Global Export Data/altitude-*.json',
        'heart_rate': 'Fitbit/Global Export Data/heart_rate-*.json',
        'sleep': 'Fitbit/Global Export Data/sleep-*.json',
        'spo2_csv': 'Fitbit/Global Export Data/estimated_oxygen_variation-*.csv',
        'temperature_wrist': 'Fitbit/Temperature/Wrist Temperature*.csv',
        'temperature_device': 'Fitbit/Temperature/Device Temperature*.csv',
        'hrv': 'Fitbit/Heart Rate Variability/*.csv',
        'sleep_score': 'Fitbit/Sleep Score/*.csv',
        'vo2_max': 'Fitbit/Global Export Data/demographic_vo2_max-*.json',
    }
    
    def __init__(self, takeout_folder: str = 'takeout_data', 
                 output_folder: str = 'data',
                 config_file: str = 'myfitbit.ini'):
        """Initialize the processor with folder paths."""
        self.takeout_folder = Path(takeout_folder)
        self.output_folder = Path(output_folder)
        
        # Load config if exists
        self.config = configparser.ConfigParser()
        if Path(config_file).exists():
            self.config.read(config_file)
            # Override paths from config if specified
            if self.config.has_section('paths'):
                if self.config.has_option('paths', 'takeout_folder'):
                    self.takeout_folder = Path(self.config.get('paths', 'takeout_folder'))
                if self.config.has_option('paths', 'output_folder'):
                    self.output_folder = Path(self.config.get('paths', 'output_folder'))
        
        # Create output directories
        self.output_folder.mkdir(parents=True, exist_ok=True)
        
    def find_zip_files(self) -> List[Path]:
        """Find all ZIP files in the takeout folder."""
        if not self.takeout_folder.exists():
            click.echo(f"Takeout folder not found: {self.takeout_folder}")
            return []
            
        zip_files = list(self.takeout_folder.glob('*.zip'))
        click.echo(f"Found {len(zip_files)} ZIP file(s) in {self.takeout_folder}")
        return zip_files
        
    def extract_and_process_zip(self, zip_path: Path) -> Dict[str, int]:
        """Extract and process a single ZIP file."""
        stats = {'files_processed': 0, 'files_skipped': 0}
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # List all files in the ZIP
            all_files = zip_ref.namelist()
            
            # Process calories data (JSON)
            calories_files = [f for f in all_files if 'Global Export Data/calories-' in f and f.endswith('.json')]
            for file_path in calories_files:
                self.process_calories_json(zip_ref, file_path)
                stats['files_processed'] += 1
                
            # Process steps data (JSON)
            steps_files = [f for f in all_files if 'Global Export Data/steps-' in f and f.endswith('.json')]
            for file_path in steps_files:
                self.process_steps_json(zip_ref, file_path)
                stats['files_processed'] += 1
                
            # Process distance data (JSON)
            distance_files = [f for f in all_files if 'Global Export Data/distance-' in f and f.endswith('.json')]
            for file_path in distance_files:
                self.process_distance_json(zip_ref, file_path)
                stats['files_processed'] += 1
                
            # Process heart rate data (JSON) - note: uses underscores not hyphens
            heart_rate_files = [f for f in all_files if 'Global Export Data/heart_rate-' in f and f.endswith('.json')]
            for file_path in heart_rate_files:
                self.process_heart_rate_json(zip_ref, file_path)
                stats['files_processed'] += 1
                
            # Process SpO2 data (CSV)
            spo2_files = [f for f in all_files if 'estimated_oxygen_variation-' in f and f.endswith('.csv')]
            for file_path in spo2_files:
                self.process_spo2_csv(zip_ref, file_path)
                stats['files_processed'] += 1
                
            # Process temperature data (CSV)
            temp_files = [f for f in all_files if 'Temperature/' in f and f.endswith('.csv')]
            for file_path in temp_files:
                self.process_temperature_csv(zip_ref, file_path)
                stats['files_processed'] += 1
                
            # Process HRV data (CSV)
            hrv_files = [f for f in all_files if 'Heart Rate Variability/' in f and f.endswith('.csv')]
            for file_path in hrv_files:
                self.process_hrv_csv(zip_ref, file_path)
                stats['files_processed'] += 1
                
            # Process sleep data (JSON)
            sleep_files = [f for f in all_files if 'Global Export Data/sleep-' in f and f.endswith('.json')]
            for file_path in sleep_files:
                self.process_sleep_json(zip_ref, file_path)
                stats['files_processed'] += 1
                
            # Process sleep score data (CSV)
            sleep_score_files = [f for f in all_files if 'Sleep Score/sleep_score.csv' in f]
            for file_path in sleep_score_files:
                self.process_sleep_score_csv(zip_ref, file_path)
                stats['files_processed'] += 1
                
        return stats
        
    def process_calories_json(self, zip_ref: zipfile.ZipFile, file_path: str):
        """Process calories JSON data and convert to CSV."""
        try:
            with zip_ref.open(file_path) as f:
                data = json.load(f)
                
            if not data:
                return
                
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Parse and standardize datetime
            df['datetime'] = pd.to_datetime(df['dateTime'], format='%m/%d/%y %H:%M:%S')
            df['date'] = df['datetime'].dt.date
            df['time'] = df['datetime'].dt.time
            df['calories'] = df['value'].astype(float)
            
            # Group by date and save daily files
            for date, day_data in df.groupby('date'):
                output_dir = self.output_folder / 'calories'
                output_dir.mkdir(parents=True, exist_ok=True)
                
                output_file = output_dir / f"{date}.csv"
                day_data[['datetime', 'calories']].to_csv(output_file, index=False)
                
        except Exception as e:
            click.echo(f"Error processing {file_path}: {e}")
            
    def process_steps_json(self, zip_ref: zipfile.ZipFile, file_path: str):
        """Process steps JSON data and convert to CSV."""
        try:
            with zip_ref.open(file_path) as f:
                data = json.load(f)
                
            if not data:
                return
                
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Parse and standardize datetime
            df['datetime'] = pd.to_datetime(df['dateTime'], format='%m/%d/%y %H:%M:%S')
            df['date'] = df['datetime'].dt.date
            df['steps'] = df['value'].astype(int)
            
            # Group by date and save daily files
            for date, day_data in df.groupby('date'):
                output_dir = self.output_folder / 'steps'
                output_dir.mkdir(parents=True, exist_ok=True)
                
                output_file = output_dir / f"{date}.csv"
                day_data[['datetime', 'steps']].to_csv(output_file, index=False)
                
        except Exception as e:
            click.echo(f"Error processing {file_path}: {e}")
            
    def process_distance_json(self, zip_ref: zipfile.ZipFile, file_path: str):
        """Process distance JSON data and convert to CSV."""
        try:
            with zip_ref.open(file_path) as f:
                data = json.load(f)
                
            if not data:
                return
                
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Parse and standardize datetime
            df['datetime'] = pd.to_datetime(df['dateTime'], format='%m/%d/%y %H:%M:%S')
            df['date'] = df['datetime'].dt.date
            df['distance'] = df['value'].astype(float)
            
            # Group by date and save daily files
            for date, day_data in df.groupby('date'):
                output_dir = self.output_folder / 'distance'
                output_dir.mkdir(parents=True, exist_ok=True)
                
                output_file = output_dir / f"{date}.csv"
                day_data[['datetime', 'distance']].to_csv(output_file, index=False)
                
        except Exception as e:
            click.echo(f"Error processing {file_path}: {e}")
            
    def process_heart_rate_json(self, zip_ref: zipfile.ZipFile, file_path: str):
        """Process heart rate JSON data and convert to CSV."""
        try:
            with zip_ref.open(file_path) as f:
                data = json.load(f)
                
            if not data:
                return
                
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Parse and standardize datetime
            df['datetime'] = pd.to_datetime(df['dateTime'], format='%m/%d/%y %H:%M:%S')
            df['date'] = df['datetime'].dt.date
            
            # Extract heart rate from nested value structure
            # value is a dict like {"bpm": 80, "confidence": 3}
            df['heart_rate'] = df['value'].apply(lambda x: x.get('bpm') if isinstance(x, dict) else x)
            df['confidence'] = df['value'].apply(lambda x: x.get('confidence') if isinstance(x, dict) else None)
            
            # Group by date and save daily files
            for date, day_data in df.groupby('date'):
                output_dir = self.output_folder / 'heart_rate'
                output_dir.mkdir(parents=True, exist_ok=True)
                
                output_file = output_dir / f"{date}.csv"
                day_data[['datetime', 'heart_rate', 'confidence']].to_csv(output_file, index=False)
                
        except Exception as e:
            click.echo(f"Error processing {file_path}: {e}")
            
    def process_spo2_csv(self, zip_ref: zipfile.ZipFile, file_path: str):
        """Process SpO2 CSV data."""
        try:
            with zip_ref.open(file_path) as f:
                df = pd.read_csv(f)
                
            if df.empty:
                return
                
            # Extract date from filename
            filename = Path(file_path).name
            date_str = filename.replace('estimated_oxygen_variation-', '').replace('.csv', '')
            
            # Parse date
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except:
                # Try other format
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
                
            # Standardize column names
            if 'timestamp' in df.columns:
                df['datetime'] = pd.to_datetime(df['timestamp'])
            
            # Save to output
            output_dir = self.output_folder / 'spo2'
            output_dir.mkdir(parents=True, exist_ok=True)
            
            output_file = output_dir / f"{date}.csv"
            df.to_csv(output_file, index=False)
            
        except Exception as e:
            click.echo(f"Error processing {file_path}: {e}")
            
    def process_temperature_csv(self, zip_ref: zipfile.ZipFile, file_path: str):
        """Process temperature CSV data."""
        try:
            with zip_ref.open(file_path) as f:
                df = pd.read_csv(f)
                
            if df.empty:
                return
                
            # Determine temperature type from filename
            filename = Path(file_path).name
            if 'Wrist' in filename:
                temp_type = 'wrist'
            else:
                temp_type = 'device'
                
            # Extract date from filename
            # Format: "Wrist Temperature - 2024-08-29.csv"
            date_str = filename.split(' - ')[-1].replace('.csv', '')
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Standardize columns
            if 'recorded_time' in df.columns:
                df['datetime'] = pd.to_datetime(df['recorded_time'])
                
            df['temp_type'] = temp_type
            
            # Save to output
            output_dir = self.output_folder / 'temperature'
            output_dir.mkdir(parents=True, exist_ok=True)
            
            output_file = output_dir / f"{date}_{temp_type}.csv"
            df.to_csv(output_file, index=False)
            
        except Exception as e:
            click.echo(f"Error processing {file_path}: {e}")
            
    def process_hrv_csv(self, zip_ref: zipfile.ZipFile, file_path: str):
        """Process HRV CSV data."""
        try:
            with zip_ref.open(file_path) as f:
                df = pd.read_csv(f)
                
            if df.empty:
                return
                
            # Extract date from filename
            filename = Path(file_path).name
            # Format: "Daily Heart Rate Variability Summary - 2024-08-29.csv"
            if ' - ' in filename:
                date_str = filename.split(' - ')[-1].replace('.csv', '')
                # Handle various date formats in filename
                date_str = date_str.split('(')[0].strip()  # Remove (1), (2) etc
                
                try:
                    # Try YYYY-MM-DD format
                    date = datetime.strptime(date_str, '%Y-%m-%d').date()
                except:
                    try:
                        # Try YYYY-MM format
                        date = datetime.strptime(date_str + '-01', '%Y-%m-%d').date()
                    except:
                        return  # Skip if can't parse date
                        
            # Save to output
            output_dir = self.output_folder / 'hrv'
            output_dir.mkdir(parents=True, exist_ok=True)
            
            output_file = output_dir / f"{date}.csv"
            df.to_csv(output_file, index=False)
            
        except Exception as e:
            click.echo(f"Error processing {file_path}: {e}")
            
    def process_sleep_json(self, zip_ref: zipfile.ZipFile, file_path: str):
        """Process sleep JSON data and convert to CSV."""
        try:
            with zip_ref.open(file_path) as f:
                data = json.load(f)
                
            if not data:
                return
                
            # Sleep data is more complex - contains multiple sleep sessions
            all_sleep_data = []
            
            for session in data:
                if 'dateOfSleep' in session:
                    sleep_date = session['dateOfSleep']
                    
                    # Extract key metrics
                    sleep_summary = {
                        'date': sleep_date,
                        'startTime': session.get('startTime'),
                        'endTime': session.get('endTime'),
                        'duration': session.get('duration'),
                        'minutesToFallAsleep': session.get('minutesToFallAsleep'),
                        'minutesAsleep': session.get('minutesAsleep'),
                        'minutesAwake': session.get('minutesAwake'),
                        'minutesAfterWakeup': session.get('minutesAfterWakeup'),
                        'efficiency': session.get('efficiency'),
                        'restlessCount': session.get('restlessCount'),
                        'restlessDuration': session.get('restlessDuration'),
                        'awakeCount': session.get('awakeCount'),
                        'awakeDuration': session.get('awakeDuration'),
                    }
                    
                    # Add sleep stages if available
                    if 'levels' in session and 'summary' in session['levels']:
                        stages = session['levels']['summary']
                        sleep_summary.update({
                            'deep_minutes': stages.get('deep', {}).get('minutes'),
                            'light_minutes': stages.get('light', {}).get('minutes'),
                            'rem_minutes': stages.get('rem', {}).get('minutes'),
                            'wake_minutes': stages.get('wake', {}).get('minutes'),
                        })
                    
                    all_sleep_data.append(sleep_summary)
            
            if all_sleep_data:
                # Convert to DataFrame
                df = pd.DataFrame(all_sleep_data)
                
                # Group by date and save
                for date in df['date'].unique():
                    day_data = df[df['date'] == date]
                    
                    output_dir = self.output_folder / 'sleep'
                    output_dir.mkdir(parents=True, exist_ok=True)
                    
                    output_file = output_dir / f"{date}.csv"
                    day_data.to_csv(output_file, index=False)
                    
        except Exception as e:
            click.echo(f"Error processing {file_path}: {e}")
            
    def process_sleep_score_csv(self, zip_ref: zipfile.ZipFile, file_path: str):
        """Process sleep score CSV data."""
        try:
            with zip_ref.open(file_path) as f:
                df = pd.read_csv(f)
                
            if df.empty:
                return
                
            # Sleep score has timestamp column with date
            if 'timestamp' in df.columns:
                # Parse the timestamp to extract date
                df['date'] = pd.to_datetime(df['timestamp']).dt.date
                
                # Group by date and save
                for date, day_data in df.groupby('date'):
                    output_dir = self.output_folder / 'sleep_score'
                    output_dir.mkdir(parents=True, exist_ok=True)
                    
                    output_file = output_dir / f"{date}.csv"
                    day_data.to_csv(output_file, index=False)
                    
        except Exception as e:
            click.echo(f"Error processing {file_path}: {e}")
            
    def process_all(self):
        """Process all ZIP files in the takeout folder."""
        zip_files = self.find_zip_files()
        
        if not zip_files:
            click.echo("No ZIP files found to process.")
            return
            
        total_stats = {'files_processed': 0, 'files_skipped': 0}
        
        with click.progressbar(zip_files, label='Processing ZIP files') as bar:
            for zip_file in bar:
                click.echo(f"\nProcessing: {zip_file.name}")
                stats = self.extract_and_process_zip(zip_file)
                total_stats['files_processed'] += stats['files_processed']
                total_stats['files_skipped'] += stats['files_skipped']
                
        click.echo(f"\nProcessing complete!")
        click.echo(f"Files processed: {total_stats['files_processed']}")
        click.echo(f"Files skipped: {total_stats['files_skipped']}")
        
        # Show what data was extracted
        self.show_data_summary()
        
    def show_data_summary(self):
        """Display a summary of extracted data."""
        click.echo("\nExtracted data summary:")
        
        for data_type in ['calories', 'steps', 'distance', 'heart_rate', 'spo2', 'temperature', 'hrv', 'sleep', 'sleep_score']:
            data_dir = self.output_folder / data_type
            if data_dir.exists():
                csv_files = list(data_dir.glob('*.csv'))
                if csv_files:
                    dates = sorted([f.stem.split('_')[0] for f in csv_files])  # Handle _wrist, _device suffixes
                    click.echo(f"  {data_type}: {len(csv_files)} days ({dates[0]} to {dates[-1]})")


@click.command()
@click.option('--takeout-folder', default='takeout_data', help='Folder containing Google Takeout ZIP files')
@click.option('--output-folder', default='data', help='Output folder for processed data')
@click.option('--config', default='myfitbit.ini', help='Config file path')
def main(takeout_folder, output_folder, config):
    """Process Google Takeout Fitbit data."""
    processor = TakeoutProcessor(takeout_folder, output_folder, config)
    processor.process_all()


if __name__ == "__main__":
    main()