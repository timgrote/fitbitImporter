#!/usr/bin/env python3
"""Main entry point for Fitbit Data Importer."""

import sys
import os
import click
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@click.command()
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
def main(start_date, end_date, config, output_dir, use_myfitbit, debug):
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
        
        # Import and run myfitbit
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

if __name__ == "__main__":
    main()