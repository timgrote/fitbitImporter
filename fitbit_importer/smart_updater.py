#!/usr/bin/env python3
"""Smart incremental updater for Fitbit data."""

import os
from pathlib import Path
from datetime import datetime, timedelta, date
import pandas as pd
import click
from typing import Dict, List, Tuple, Optional, Set
import configparser
from .data_analyzer import DataAnalyzer
from .export import export_with_date_range


class SmartUpdater:
    """Intelligently update Fitbit data by filling gaps and getting recent data."""
    
    def __init__(self, data_folder: str = 'data',
                 api_folder: str = 'fitbit_download',
                 config_file: str = 'myfitbit.ini'):
        """Initialize the smart updater."""
        self.data_folder = Path(data_folder)
        self.api_folder = Path(api_folder)
        self.config_file = config_file
        
        # Load config
        self.config = configparser.ConfigParser()
        if Path(config_file).exists():
            self.config.read(config_file)
            
        # Get update preferences
        self.max_gap_days = int(self.config.get('auto_update', 'max_gap_days', fallback='30'))
        self.update_recent_days = int(self.config.get('auto_update', 'update_recent_days', fallback='7'))
        priority_types = self.config.get('auto_update', 'priority_types', 
                                       fallback='heart_rate,sleep,activity_summary')
        self.priority_types = [t.strip() for t in priority_types.split(',')]
        
        # Initialize analyzer
        self.analyzer = DataAnalyzer(data_folder=data_folder)
        
    def find_latest_data_date(self) -> Optional[date]:
        """Find the most recent date across all data types."""
        analysis = self.analyzer.analyze_all_data()
        latest_dates = []
        
        for data_type, info in analysis.items():
            if info['exists'] and info['date_range']:
                latest_dates.append(info['date_range'][1])
                
        return max(latest_dates) if latest_dates else None
        
    def find_priority_gaps(self) -> List[Tuple[date, date, str, int]]:
        """Find gaps in priority data types that should be filled."""
        analysis = self.analyzer.analyze_all_data()
        priority_gaps = []
        
        for data_type in self.priority_types:
            if data_type in analysis and analysis[data_type]['exists']:
                gaps = analysis[data_type]['gaps']
                for gap_start, gap_end, gap_days in gaps:
                    if gap_days <= self.max_gap_days:
                        priority_gaps.append((gap_start, gap_end, data_type, gap_days))
                        
        # Sort by gap size (smaller gaps first for efficiency)
        priority_gaps.sort(key=lambda x: x[3])
        return priority_gaps
        
    def calculate_download_strategy(self, dry_run: bool = False) -> Dict:
        """Calculate what needs to be downloaded."""
        strategy = {
            'recent_data': None,
            'priority_gaps': [],
            'total_days': 0,
            'estimated_requests': 0
        }
        
        # Find latest date and calculate recent data need
        latest_date = self.find_latest_data_date()
        today = datetime.now().date()
        
        if latest_date:
            days_behind = (today - latest_date).days
            if days_behind > 0:
                recent_start = latest_date + timedelta(days=1)
                recent_end = today
                strategy['recent_data'] = (recent_start, recent_end, days_behind)
                strategy['total_days'] += days_behind
        else:
            # No data exists, get recent days only
            recent_start = today - timedelta(days=self.update_recent_days)
            strategy['recent_data'] = (recent_start, today, self.update_recent_days)
            strategy['total_days'] += self.update_recent_days
            
        # Find priority gaps to fill
        priority_gaps = self.find_priority_gaps()
        strategy['priority_gaps'] = priority_gaps
        
        for _, _, _, gap_days in priority_gaps:
            strategy['total_days'] += gap_days
            
        # Estimate API requests (roughly 1 request per day per data type)
        # We download multiple types per day, so estimate conservatively
        strategy['estimated_requests'] = strategy['total_days'] * 4  # 4 main data types
        
        return strategy
        
    def print_download_strategy(self, strategy: Dict):
        """Print what will be downloaded."""
        click.echo("\n" + "="*60)
        click.echo("SMART UPDATE STRATEGY")
        click.echo("="*60)
        
        total_days = strategy['total_days']
        estimated_requests = strategy['estimated_requests']
        estimated_hours = max(1, estimated_requests / 150)  # Fitbit rate limit
        
        click.echo(f"📊 Total days to download: {total_days}")
        click.echo(f"🔄 Estimated API requests: {estimated_requests}")
        click.echo(f"⏱️  Estimated time: {estimated_hours:.1f} hours")
        
        # Recent data
        if strategy['recent_data']:
            start, end, days = strategy['recent_data']
            click.echo(f"\n📅 Recent data: {start} to {end} ({days} days)")
            
        # Priority gaps
        if strategy['priority_gaps']:
            click.echo(f"\n🔧 Priority gaps to fill: {len(strategy['priority_gaps'])}")
            for gap_start, gap_end, data_type, gap_days in strategy['priority_gaps'][:5]:
                click.echo(f"   {data_type}: {gap_start} to {gap_end} ({gap_days} days)")
            if len(strategy['priority_gaps']) > 5:
                click.echo(f"   ... and {len(strategy['priority_gaps']) - 5} more gaps")
        else:
            click.echo("\n✅ No priority gaps found!")
            
        # Rate limit warning
        if estimated_hours > 2:
            click.echo(f"\n⚠️  Large download detected!")
            click.echo(f"   This will take ~{estimated_hours:.1f} hours due to Fitbit rate limits")
            click.echo(f"   Consider using --recent-only for faster updates")
            
    def update_config_for_download(self, start_date: date, end_date: date):
        """Update config file with date range for download."""
        # Read current config
        if not self.config.has_section('export'):
            self.config.add_section('export')
            
        self.config.set('export', 'start_date', start_date.strftime('%Y-%m-%d'))
        self.config.set('export', 'end_date', end_date.strftime('%Y-%m-%d'))
        
        # Write config
        with open(self.config_file, 'w') as f:
            self.config.write(f)
            
    def download_date_range(self, start_date: date, end_date: date, 
                          description: str = "") -> bool:
        """Download data for a specific date range with rate limit handling."""
        try:
            days = (end_date - start_date).days + 1
            click.echo(f"\n📥 Downloading {description}: {start_date} to {end_date} ({days} days)")
            
            # Rate limit warning
            estimated_requests = days * 4  # 4 main data types
            if estimated_requests > 50:
                estimated_time = max(1, estimated_requests / 150)  # 150 requests/hour limit
                click.echo(f"⏱️  Estimated time: {estimated_time:.1f} hours (due to rate limits)")
            
            # Update config with date range
            self.update_config_for_download(start_date, end_date)
            
            # Download data using our export function
            export_with_date_range(self.config_file, str(self.api_folder))
            
            click.echo(f"✅ Successfully downloaded {description}")
            
            # Small delay between downloads to be API-friendly
            if estimated_requests > 10:
                import time
                click.echo("⏳ Brief pause to respect API limits...")
                time.sleep(2)
                
            return True
            
        except Exception as e:
            click.echo(f"❌ Error downloading {description}: {e}")
            # Check if it's a rate limit error
            if '429' in str(e).lower() or 'rate limit' in str(e).lower():
                click.echo("⚠️  Rate limit reached - download will resume automatically")
                import time
                time.sleep(60)  # Wait 1 minute before continuing
            return False
            
    def execute_download_strategy(self, strategy: Dict, recent_only: bool = False) -> Dict:
        """Execute the download strategy."""
        results = {'recent_success': False, 'gaps_filled': 0, 'gaps_failed': 0}
        
        # Download recent data first (most important)
        if strategy['recent_data']:
            start, end, days = strategy['recent_data']
            success = self.download_date_range(start, end, f"recent data ({days} days)")
            results['recent_success'] = success
            
        # Skip gaps if recent_only mode
        if recent_only:
            click.echo("\n⏭️  Skipping gap filling (recent-only mode)")
            return results
            
        # Download priority gaps
        for gap_start, gap_end, data_type, gap_days in strategy['priority_gaps']:
            success = self.download_date_range(
                gap_start, gap_end, 
                f"{data_type} gap ({gap_days} days)"
            )
            if success:
                results['gaps_filled'] += 1
            else:
                results['gaps_failed'] += 1
                
        return results
        
    def run_update(self, dry_run: bool = False, recent_only: bool = False, 
                  fill_gaps: bool = True) -> Dict:
        """Run the smart update process."""
        click.echo("\n🔄 SMART FITBIT DATA UPDATE")
        click.echo("="*40)
        
        # Calculate download strategy
        strategy = self.calculate_download_strategy(dry_run)
        
        # Show what will be downloaded
        self.print_download_strategy(strategy)
        
        if dry_run:
            click.echo("\n🧪 DRY RUN - No data will be downloaded")
            return {'dry_run': True}
            
        if strategy['total_days'] == 0:
            click.echo("\n✨ Your data is already up to date!")
            return {'up_to_date': True}
            
        # Confirm with user for large downloads
        if strategy['estimated_requests'] > 300:  # ~2 hours
            if not click.confirm("\nProceed with large download?"):
                click.echo("Download cancelled by user")
                return {'cancelled': True}
                
        # Execute downloads
        click.echo("\n" + "="*60)
        click.echo("EXECUTING DOWNLOADS")
        click.echo("="*60)
        
        # Apply mode filters
        if recent_only:
            strategy['priority_gaps'] = []  # Skip gaps
        elif not fill_gaps:
            strategy['recent_data'] = None  # Skip recent data
            
        results = self.execute_download_strategy(strategy, recent_only)
        
        # Merge new data
        if results.get('recent_success') or results.get('gaps_filled', 0) > 0:
            click.echo("\n🔄 Merging downloaded data...")
            from .data_merger import DataMerger
            merger = DataMerger(
                data_folder=str(self.data_folder),
                api_folder=str(self.api_folder)
            )
            merge_results = merger.merge_all_data()
            merger.print_merge_summary(merge_results)
            
        return results
        
    def print_final_summary(self, results: Dict):
        """Print summary of update results."""
        click.echo("\n" + "="*60)
        click.echo("UPDATE COMPLETE")
        click.echo("="*60)
        
        if results.get('dry_run'):
            click.echo("🧪 Dry run completed - no changes made")
        elif results.get('up_to_date'):
            click.echo("✨ Data was already up to date!")
        elif results.get('cancelled'):
            click.echo("⏹️  Update cancelled by user")
        else:
            if results.get('recent_success'):
                click.echo("✅ Recent data downloaded successfully")
            else:
                click.echo("❌ Recent data download failed")
                
            gaps_filled = results.get('gaps_filled', 0)
            gaps_failed = results.get('gaps_failed', 0)
            
            if gaps_filled > 0:
                click.echo(f"✅ Filled {gaps_filled} data gaps")
            if gaps_failed > 0:
                click.echo(f"❌ Failed to fill {gaps_failed} data gaps")
                
            click.echo(f"\n📊 Run 'python main.py analyze' to see your updated dataset")
            
        click.echo("="*60)


@click.command()
@click.option('--data-folder', default='data', help='Data folder to analyze')
@click.option('--dry-run', is_flag=True, help='Show what would be downloaded without doing it')
@click.option('--recent-only', is_flag=True, help='Only download recent data, skip gap filling')
@click.option('--fill-gaps', is_flag=True, help='Only fill gaps, skip recent data')
def main(data_folder, dry_run, recent_only, fill_gaps):
    """Smart update: automatically download missing Fitbit data."""
    updater = SmartUpdater(data_folder=data_folder)
    results = updater.run_update(dry_run=dry_run, recent_only=recent_only, 
                               fill_gaps=fill_gaps)
    updater.print_final_summary(results)


if __name__ == "__main__":
    main()