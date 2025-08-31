#!/usr/bin/env python3
"""Merge API download data with processed Google Takeout data."""

import os
from pathlib import Path
from datetime import datetime, timedelta, date
import pandas as pd
import click
from typing import Dict, List, Optional
import configparser
import shutil
import json


class DataMerger:
    """Merge Fitbit API data with Google Takeout processed data."""
    
    def __init__(self, data_folder: str = 'data',
                 api_folder: str = 'fitbit_download',
                 config_file: str = 'myfitbit.ini'):
        """Initialize the merger with folder paths."""
        self.data_folder = Path(data_folder)
        self.api_folder = Path(api_folder) 
        
        # Load config if exists
        self.config = configparser.ConfigParser()
        if Path(config_file).exists():
            self.config.read(config_file)
            if self.config.has_section('paths'):
                if self.config.has_option('paths', 'output_folder'):
                    self.data_folder = Path(self.config.get('paths', 'output_folder'))
                if self.config.has_option('paths', 'api_downloads'):
                    self.api_folder = Path(self.config.get('paths', 'api_downloads'))
                    
    def find_api_data(self) -> Dict:
        """Find all API data files and organize by type and date."""
        api_data = {
            'activity_summary': {},
            'heart_rate': {},
            'sleep': {},
            'steps': {}
        }
        
        if not self.api_folder.exists():
            return api_data
            
        # Search for CSV files in API folder structure (YYYY/MM/DD/*.csv)
        for csv_file in self.api_folder.rglob('*.csv'):
            # Extract date from path: fitbit_download/2024/08/29/activity_summary.csv
            path_parts = csv_file.parts
            if len(path_parts) >= 4:
                try:
                    year, month, day = path_parts[-4], path_parts[-3], path_parts[-2]
                    file_date = date(int(year), int(month), int(day))
                    data_type = csv_file.stem  # filename without extension
                    
                    if data_type in api_data:
                        api_data[data_type][file_date] = csv_file
                        
                except (ValueError, IndexError):
                    continue
                    
        return api_data
        
    def find_takeout_data(self) -> Dict:
        """Find all processed Takeout data files."""
        takeout_data = {}
        
        if not self.data_folder.exists():
            return takeout_data
            
        # Search each data type folder
        for data_type_dir in self.data_folder.iterdir():
            if data_type_dir.is_dir():
                data_type = data_type_dir.name
                takeout_data[data_type] = {}
                
                for csv_file in data_type_dir.glob('*.csv'):
                    try:
                        # Handle different filename formats (YYYY-MM-DD.csv or YYYY-MM-DD_type.csv)
                        date_part = csv_file.stem.split('_')[0]
                        file_date = datetime.strptime(date_part, '%Y-%m-%d').date()
                        takeout_data[data_type][file_date] = csv_file
                    except ValueError:
                        continue
                        
        return takeout_data
        
    def merge_activity_summary(self, api_file: Path, takeout_date: date) -> bool:
        """Merge API activity summary with Takeout data for a specific date."""
        try:
            # Read API activity summary
            api_df = pd.read_csv(api_file)
            
            if api_df.empty:
                return False
                
            # API data has comprehensive activity metrics that Takeout lacks
            # Create activity_summary folder if it doesn't exist
            output_dir = self.data_folder / 'activity_summary'
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Save API data as the primary activity summary
            output_file = output_dir / f"{takeout_date}.csv"
            api_df.to_csv(output_file, index=False)
            
            click.echo(f"  Added API activity summary for {takeout_date}")
            return True
            
        except Exception as e:
            click.echo(f"  Error merging activity summary for {takeout_date}: {e}")
            return False
            
    def merge_data_type(self, data_type: str, api_data: Dict, takeout_data: Dict) -> Dict:
        """Merge a specific data type, preferring API data for overlapping dates."""
        results = {'added': 0, 'updated': 0, 'skipped': 0}
        
        # Get all dates that have API data
        api_dates = set(api_data.get(data_type, {}).keys())
        takeout_dates = set(takeout_data.get(data_type, {}).keys())
        
        click.echo(f"\n📊 Merging {data_type}:")
        click.echo(f"  API data: {len(api_dates)} days")
        click.echo(f"  Takeout data: {len(takeout_dates)} days")
        
        # Process API data
        for api_date, api_file in api_data.get(data_type, {}).items():
            try:
                if data_type == 'activity_summary':
                    success = self.merge_activity_summary(api_file, api_date)
                    if success:
                        results['added'] += 1
                else:
                    # For other data types, API data supplements Takeout
                    # Check if we already have Takeout data for this date
                    if api_date in takeout_dates:
                        click.echo(f"  📅 {api_date}: Has Takeout data, keeping original")
                        results['skipped'] += 1
                    else:
                        # Copy API data to fill gap
                        output_dir = self.data_folder / data_type
                        output_dir.mkdir(parents=True, exist_ok=True)
                        
                        output_file = output_dir / f"{api_date}.csv"
                        shutil.copy2(api_file, output_file)
                        
                        click.echo(f"  📅 {api_date}: Added API data")
                        results['added'] += 1
                        
            except Exception as e:
                click.echo(f"  ❌ {api_date}: Error - {e}")
                
        return results
        
    def merge_all_data(self) -> Dict:
        """Merge all API data with Takeout data."""
        click.echo("\n" + "="*60)
        click.echo("MERGING API DATA WITH TAKEOUT DATA")
        click.echo("="*60)
        
        # Find all data
        api_data = self.find_api_data()
        takeout_data = self.find_takeout_data()
        
        click.echo(f"\n📂 API folder: {self.api_folder}")
        click.echo(f"📂 Data folder: {self.data_folder}")
        
        overall_results = {}
        
        # Merge each data type
        all_data_types = set(list(api_data.keys()) + list(takeout_data.keys()))
        
        for data_type in sorted(all_data_types):
            if data_type in api_data and api_data[data_type]:
                results = self.merge_data_type(data_type, api_data, takeout_data)
                overall_results[data_type] = results
            else:
                click.echo(f"\n📊 {data_type}: No API data to merge")
                
        return overall_results
        
    def print_merge_summary(self, results: Dict):
        """Print summary of merge operations."""
        click.echo("\n" + "-"*50)
        click.echo("MERGE SUMMARY")
        click.echo("-"*50)
        
        total_added = total_updated = total_skipped = 0
        
        for data_type, stats in results.items():
            click.echo(f"\n✅ {data_type.upper()}")
            click.echo(f"   Added: {stats['added']} files")
            click.echo(f"   Updated: {stats['updated']} files") 
            click.echo(f"   Skipped: {stats['skipped']} files")
            
            total_added += stats['added']
            total_updated += stats['updated']
            total_skipped += stats['skipped']
            
        click.echo(f"\n🎯 TOTALS:")
        click.echo(f"   📥 Added: {total_added}")
        click.echo(f"   🔄 Updated: {total_updated}")
        click.echo(f"   ⏭️  Skipped: {total_skipped}")
        
        click.echo("\n" + "="*60)


@click.command()
@click.option('--data-folder', default='data', help='Processed data folder')
@click.option('--api-folder', default='fitbit_download', help='API downloads folder')
@click.option('--dry-run', is_flag=True, help='Show what would be merged without doing it')
def main(data_folder, api_folder, dry_run):
    """Merge API downloads with processed Takeout data."""
    if dry_run:
        click.echo("🧪 DRY RUN MODE - No files will be modified")
        
    merger = DataMerger(data_folder=data_folder, api_folder=api_folder)
    
    if dry_run:
        # Just show what would be merged
        api_data = merger.find_api_data()
        takeout_data = merger.find_takeout_data()
        
        click.echo("\nAPI Data Found:")
        for data_type, files in api_data.items():
            if files:
                dates = sorted(files.keys())
                click.echo(f"  {data_type}: {len(files)} days ({dates[0]} to {dates[-1]})")
                
        click.echo("\nTakeout Data Found:")  
        for data_type, files in takeout_data.items():
            if files:
                dates = sorted(files.keys())
                click.echo(f"  {data_type}: {len(files)} days ({dates[0]} to {dates[-1]})")
    else:
        results = merger.merge_all_data()
        merger.print_merge_summary(results)


if __name__ == "__main__":
    main()