#!/usr/bin/env python3
"""Analyze existing Fitbit data and identify gaps."""

import os
from pathlib import Path
from datetime import datetime, timedelta, date
import pandas as pd
import click
from typing import Dict, List, Tuple, Optional
import configparser


class DataAnalyzer:
    """Analyze Fitbit data to identify coverage and gaps."""
    
    def __init__(self, data_folder: str = 'data',
                 takeout_folder: str = 'existing_data',
                 api_folder: str = 'fitbit_downloads',
                 config_file: str = 'myfitbit.ini'):
        """Initialize the analyzer with folder paths."""
        self.data_folder = Path(data_folder)
        self.takeout_folder = Path(takeout_folder)
        self.api_folder = Path(api_folder)
        
        # Load config if exists
        self.config = configparser.ConfigParser()
        if Path(config_file).exists():
            self.config.read(config_file)
            if self.config.has_section('paths'):
                if self.config.has_option('paths', 'output_folder'):
                    self.data_folder = Path(self.config.get('paths', 'output_folder'))
                if self.config.has_option('paths', 'takeout_folder'):
                    self.takeout_folder = Path(self.config.get('paths', 'takeout_folder'))
                    
    def analyze_data_type(self, data_type: str) -> Dict:
        """Analyze a specific data type for coverage."""
        data_dir = self.data_folder / data_type
        
        if not data_dir.exists():
            return {
                'exists': False,
                'days': 0,
                'date_range': None,
                'gaps': []
            }
            
        # Find all CSV files
        csv_files = list(data_dir.glob('*.csv'))
        
        if not csv_files:
            return {
                'exists': True,
                'days': 0,
                'date_range': None,
                'gaps': []
            }
            
        # Extract dates from filenames
        dates = []
        for file in csv_files:
            try:
                # Handle different filename formats
                filename = file.stem
                # Remove suffixes like "_wrist" or "_device"
                date_part = filename.split('_')[0]
                file_date = datetime.strptime(date_part, '%Y-%m-%d').date()
                dates.append(file_date)
            except:
                continue
                
        if not dates:
            return {
                'exists': True,
                'days': 0,
                'date_range': None,
                'gaps': []
            }
            
        dates = sorted(dates)
        
        # Find gaps
        gaps = []
        for i in range(len(dates) - 1):
            current_date = dates[i]
            next_date = dates[i + 1]
            
            # If there's more than 1 day difference, we have a gap
            diff = (next_date - current_date).days
            if diff > 1:
                gap_start = current_date + timedelta(days=1)
                gap_end = next_date - timedelta(days=1)
                gaps.append((gap_start, gap_end, diff - 1))
                
        return {
            'exists': True,
            'days': len(dates),
            'date_range': (dates[0], dates[-1]),
            'dates': dates,
            'gaps': gaps
        }
        
    def analyze_all_data(self) -> Dict:
        """Analyze all data types."""
        data_types = ['calories', 'steps', 'distance', 'spo2', 'temperature', 'hrv', 
                     'heart_rate', 'sleep', 'activity_summary']
        
        analysis = {}
        for data_type in data_types:
            analysis[data_type] = self.analyze_data_type(data_type)
            
        return analysis
        
    def find_date_coverage(self, analysis: Dict) -> Tuple[Optional[date], Optional[date]]:
        """Find the overall date range across all data types."""
        all_starts = []
        all_ends = []
        
        for data_type, info in analysis.items():
            if info['date_range']:
                all_starts.append(info['date_range'][0])
                all_ends.append(info['date_range'][1])
                
        if all_starts:
            return min(all_starts), max(all_ends)
        return None, None
        
    def suggest_api_ranges(self, analysis: Dict) -> List[Tuple[date, date]]:
        """Suggest date ranges to download via API."""
        suggestions = []
        
        # Get overall coverage
        overall_start, overall_end = self.find_date_coverage(analysis)
        
        if not overall_end:
            # No data exists, suggest last 30 days
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)
            suggestions.append((start_date, end_date))
            return suggestions
            
        # Check if we need recent data
        days_since_last = (datetime.now().date() - overall_end).days
        if days_since_last > 1:
            # Suggest downloading recent data
            suggestions.append((overall_end + timedelta(days=1), datetime.now().date()))
            
        # Find common gaps across multiple data types
        gap_counts = {}
        for data_type, info in analysis.items():
            if info['exists'] and info['gaps']:
                for gap_start, gap_end, days in info['gaps']:
                    for d in range((gap_end - gap_start).days + 1):
                        gap_date = gap_start + timedelta(days=d)
                        gap_counts[gap_date] = gap_counts.get(gap_date, 0) + 1
                        
        # Suggest filling gaps that appear in multiple data types
        if gap_counts:
            # Group consecutive dates
            gap_dates = sorted([d for d, count in gap_counts.items() if count >= 2])
            if gap_dates:
                current_range_start = gap_dates[0]
                current_range_end = gap_dates[0]
                
                for gap_date in gap_dates[1:]:
                    if (gap_date - current_range_end).days == 1:
                        current_range_end = gap_date
                    else:
                        suggestions.append((current_range_start, current_range_end))
                        current_range_start = gap_date
                        current_range_end = gap_date
                        
                suggestions.append((current_range_start, current_range_end))
                
        return suggestions
        
    def print_report(self):
        """Print a detailed analysis report."""
        click.echo("\n" + "="*60)
        click.echo("FITBIT DATA ANALYSIS REPORT")
        click.echo("="*60)
        
        analysis = self.analyze_all_data()
        
        # Overall coverage
        overall_start, overall_end = self.find_date_coverage(analysis)
        
        if overall_start:
            click.echo(f"\n📅 Overall Date Range: {overall_start} to {overall_end}")
            total_days = (overall_end - overall_start).days + 1
            click.echo(f"📊 Total Days Span: {total_days} days")
        else:
            click.echo("\n⚠️  No data found in the data folder")
            
        # Per data type analysis
        click.echo("\n" + "-"*40)
        click.echo("DATA TYPE ANALYSIS")
        click.echo("-"*40)
        
        for data_type, info in analysis.items():
            if not info['exists']:
                click.echo(f"\n❌ {data_type.upper()}: No data folder")
                continue
                
            if info['days'] == 0:
                click.echo(f"\n⚪ {data_type.upper()}: Folder exists but no data")
                continue
                
            click.echo(f"\n✅ {data_type.upper()}")
            click.echo(f"   Days with data: {info['days']}")
            click.echo(f"   Date range: {info['date_range'][0]} to {info['date_range'][1]}")
            
            if info['gaps']:
                click.echo(f"   ⚠️  Gaps found: {len(info['gaps'])}")
                # Show first 3 gaps
                for gap_start, gap_end, days in info['gaps'][:3]:
                    click.echo(f"      - {gap_start} to {gap_end} ({days} days)")
                if len(info['gaps']) > 3:
                    click.echo(f"      ... and {len(info['gaps']) - 3} more gaps")
                    
        # Suggestions
        suggestions = self.suggest_api_ranges(analysis)
        
        if suggestions:
            click.echo("\n" + "-"*40)
            click.echo("RECOMMENDED API DOWNLOADS")
            click.echo("-"*40)
            
            for start_date, end_date in suggestions:
                days = (end_date - start_date).days + 1
                click.echo(f"\n📥 Download: {start_date} to {end_date} ({days} days)")
                
            # Update config suggestion
            click.echo("\n💡 To download these ranges, update myfitbit.ini:")
            click.echo("\n[export]")
            click.echo(f"start_date = {suggestions[0][0]}")
            click.echo(f"end_date = {suggestions[0][1]}")
        else:
            click.echo("\n✨ Data coverage looks complete!")
            
        click.echo("\n" + "="*60)
        
    def export_gaps_csv(self, output_file: str = 'data_gaps.csv'):
        """Export gaps analysis to CSV file."""
        analysis = self.analyze_all_data()
        
        gaps_data = []
        for data_type, info in analysis.items():
            if info['exists'] and info['gaps']:
                for gap_start, gap_end, days in info['gaps']:
                    gaps_data.append({
                        'data_type': data_type,
                        'gap_start': gap_start,
                        'gap_end': gap_end,
                        'days_missing': days
                    })
                    
        if gaps_data:
            df = pd.DataFrame(gaps_data)
            df.to_csv(output_file, index=False)
            click.echo(f"\n📄 Gaps report exported to: {output_file}")
        else:
            click.echo("\n✅ No gaps found to export")


@click.command()
@click.option('--data-folder', default='data', help='Processed data folder')
@click.option('--export-gaps', is_flag=True, help='Export gaps to CSV file')
def main(data_folder, export_gaps):
    """Analyze Fitbit data coverage and identify gaps."""
    analyzer = DataAnalyzer(data_folder=data_folder)
    analyzer.print_report()
    
    if export_gaps:
        analyzer.export_gaps_csv()


if __name__ == "__main__":
    main()