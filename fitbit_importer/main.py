#!/usr/bin/env python3
"""Main entry point for Fitbit Data Importer."""

import sys
import os
import click
from pathlib import Path

# Load environment variables if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv is optional
    pass

@click.group()
def cli():
    """Fitbit Data Importer - Export and process your Fitbit data."""
    pass

@cli.command()
@click.option('--start-date', type=click.DateTime(formats=['%Y-%m-%d']), 
              help='Start date for data export (YYYY-MM-DD)')
@click.option('--end-date', type=click.DateTime(formats=['%Y-%m-%d']), 
              help='End date for data export (YYYY-MM-DD)')
@click.option('--config', type=click.Path(exists=True), 
              default='myfitbit.ini', help='Path to config file')
@click.option('--output-dir', type=click.Path(), 
              default='data', help='Output directory for CSV files')
@click.option('--use-myfitbit', is_flag=True, default=True,
              help='Use myfitbit library for export (default)')
@click.option('--debug', is_flag=True, help='Enable debug output')
def export(start_date, end_date, config, output_dir, use_myfitbit, debug):
    """Export Fitbit data to CSV files for AI analysis."""
    
    click.echo("Fitbit Data Importer v0.1.0")
    click.echo("=" * 40)
    
    # Set up output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    if use_myfitbit:
        click.echo("\nUsing myfitbit library for export...")
        click.echo(f"Config file: {config}")
        click.echo(f"Output directory: {output_path.absolute()}")
        
        # Check if config file has credentials
        config_path = Path(config)
        if not config_path.exists():
            click.echo("\nError: Config file not found!")
            click.echo("Please create myfitbit.ini with your Fitbit API credentials:")
            click.echo("\n[fitbit]")
            click.echo("client_id = YOUR_CLIENT_ID")
            click.echo("client_secret = YOUR_CLIENT_SECRET")
            sys.exit(1)
        
        # Read config to check for placeholder values
        with open(config_path, 'r') as f:
            config_content = f.read()
            if 'YOUR_CLIENT_ID' in config_content or 'YOUR_CLIENT_SECRET' in config_content:
                click.echo("\nError: Please update myfitbit.ini with your actual Fitbit API credentials!")
                click.echo("\nTo get credentials:")
                click.echo("1. Go to https://dev.fitbit.com")
                click.echo("2. Register a new app (Personal type)")
                click.echo("3. Set Redirect URL to: http://localhost:8189/auth_code")
                click.echo("4. Copy Client ID and Client Secret to myfitbit.ini")
                sys.exit(1)
        
        # Check if custom date range is configured
        import configparser
        config_parser = configparser.ConfigParser()
        config_parser.read(config_path)
        
        has_date_range = (config_parser.has_section('export') and 
                         (config_parser.has_option('export', 'start_date') or 
                          config_parser.has_option('export', 'end_date')))
        
        if has_date_range:
            # Use our custom export with date ranges
            click.echo("\nUsing custom export with date range...")
            try:
                from .export import export_with_date_range
                export_with_date_range(config, output_dir)
            except ImportError as e:
                click.echo(f"\nError importing custom export: {e}")
                sys.exit(1)
        else:
            # Use myfitbit for full export
            try:
                import myfitbit
                click.echo("\nStarting myfitbit export...")
                click.echo("Note: This will open your browser for Fitbit authorization")
                click.echo("Rate limits: 150 requests/hour - large exports may take time")
                
                # Run myfitbit as module
                if debug:
                    os.system(f"cd {output_path} && python -m myfitbit --debug")
                else:
                    os.system(f"cd {output_path} && python -m myfitbit")
                    
                click.echo("\nExport complete! Check the data directory for CSV files.")
                
            except ImportError as e:
                click.echo(f"\nError importing myfitbit: {e}")
                click.echo("Please install with: pip install myfitbit")
                sys.exit(1)
    else:
        click.echo("\nCustom export implementation coming soon...")
        click.echo("For now, using myfitbit is recommended.")

@cli.command()
@click.option('--config', default='myfitbit.ini', help='Path to config file')
def process_takeout(config):
    """Process Google Takeout Fitbit data.
    
    Folder locations are configured in myfitbit.ini under the [paths] section.
    By default, looks for ZIP files in 'takeout_data/' and outputs to 'data/'.
    """
    try:
        from .takeout_processor import TakeoutProcessor
    except ImportError as e:
        if 'pandas' in str(e):
            click.echo("❌ Missing required dependency: pandas")
            click.echo("\nTo install:")
            click.echo("  pip install pandas")
            click.echo("  # Or install all dependencies:")
            click.echo("  pip install -r requirements.txt")
            sys.exit(1)
        else:
            raise
    
    click.echo("Processing Google Takeout data...")
    processor = TakeoutProcessor(config_file=config)
    processor.process_all()

@cli.command()
@click.option('--config', default='myfitbit.ini', help='Path to config file')
@click.option('--export-gaps', is_flag=True, help='Export gaps to CSV')
def analyze(config, export_gaps):
    """Analyze data coverage and identify gaps.
    
    Data folder location is configured in myfitbit.ini under the [paths] section.
    """
    from .data_analyzer import DataAnalyzer
    
    analyzer = DataAnalyzer(config_file=config)
    analyzer.print_report()
    
    if export_gaps:
        analyzer.export_gaps_csv()

@cli.command()
@click.option('--config', default='myfitbit.ini', help='Path to config file')
@click.option('--dry-run', is_flag=True, help='Show what would be merged without doing it')
def merge(config, dry_run):
    """Merge API downloads with processed Takeout data.
    
    Folder locations are configured in myfitbit.ini under the [paths] section.
    """
    from .data_merger import DataMerger
    
    if dry_run:
        click.echo("🧪 DRY RUN MODE - No files will be modified")
        
    merger = DataMerger(config_file=config)
    
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

@cli.command()
@click.option('--config', default='myfitbit.ini', help='Path to Fitbit config file')
@click.option('--dry-run', is_flag=True, help='Show what would be downloaded without doing it')
@click.option('--recent-only', is_flag=True, help='Only download recent data, skip gap filling')
@click.option('--fill-gaps', is_flag=True, help='Only fill gaps, skip recent data')
def update(config, dry_run, recent_only, fill_gaps):
    """Smart update: automatically download missing Fitbit data.
    
    This command analyzes your existing data and intelligently downloads only 
    what's missing or new. Perfect for keeping your dataset current after
    initial Takeout processing.
    
    Folder locations are configured in myfitbit.ini under the [paths] section.
    
    Examples:
      python main.py update                    # Full smart update
      python main.py update --dry-run          # See what would be downloaded
      python main.py update --recent-only      # Only get recent data, skip gaps
      python main.py update --fill-gaps        # Only fill gaps, skip recent data
    """
    from .smart_updater import SmartUpdater
    
    # Check config file exists
    config_path = Path(config)
    if not config_path.exists():
        click.echo(f"\n❌ Config file not found: {config}")
        click.echo("Please create myfitbit.ini with your Fitbit API credentials")
        sys.exit(1)
    
    updater = SmartUpdater(config_file=config)
    results = updater.run_update(dry_run=dry_run, recent_only=recent_only, 
                               fill_gaps=fill_gaps)
    updater.print_final_summary(results)

if __name__ == "__main__":
    cli()