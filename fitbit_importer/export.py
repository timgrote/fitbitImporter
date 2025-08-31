#!/usr/bin/env python3
"""Custom Fitbit export functionality with date range support."""

import os
import sys
import json
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import fitbit
from fitbit.api import Fitbit
import configparser
import click


class FitbitExporter:
    """Export Fitbit data with custom date ranges."""
    
    def __init__(self, config_file='myfitbit.ini'):
        """Initialize the exporter with config file."""
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        
        # Get credentials
        self.client_id = self.config.get('fitbit', 'client_id')
        self.client_secret = self.config.get('fitbit', 'client_secret')
        
        # Get date range if specified
        if self.config.has_option('export', 'start_date'):
            self.start_date = datetime.strptime(
                self.config.get('export', 'start_date'), '%Y-%m-%d'
            ).date()
        else:
            # Default to yesterday
            self.start_date = (datetime.now() - timedelta(days=1)).date()
            
        if self.config.has_option('export', 'end_date'):
            self.end_date = datetime.strptime(
                self.config.get('export', 'end_date'), '%Y-%m-%d'
            ).date()
        else:
            # Default to today
            self.end_date = datetime.now().date()
            
        self.redirect_uri = 'http://localhost:8080/callback'
        self.token_file = Path('.fitbit_token.json')
        self.client = None
        
    def authenticate(self):
        """Authenticate with Fitbit API."""
        # Check for existing token
        if self.token_file.exists():
            with open(self.token_file, 'r') as f:
                token = json.load(f)
                
            self.client = Fitbit(
                self.client_id,
                self.client_secret,
                access_token=token['access_token'],
                refresh_token=token['refresh_token'],
                expires_at=token['expires_at'],
                refresh_cb=self.save_token
            )
            click.echo("Using existing authentication token")
        else:
            # Need to authenticate
            click.echo("Opening browser for Fitbit authorization...")
            
            # We'll use the OAuth2 flow
            from fitbit.api import FitbitOauth2Client
            oauth = FitbitOauth2Client(
                self.client_id, 
                self.client_secret,
                redirect_uri=self.redirect_uri
            )
            
            # Get authorization URL
            url, _ = oauth.authorize_token_url()
            click.echo(f"\nPlease visit this URL to authorize: {url}")
            webbrowser.open(url)
            
            # Get the redirect URL from user
            click.echo("\nAfter authorizing, you'll be redirected to a URL starting with:")
            click.echo(f"{self.redirect_uri}?code=...")
            redirect_url = click.prompt("Please paste the full redirect URL here")
            
            # Extract code and get token
            code = redirect_url.split('code=')[1].split('&')[0] if 'code=' in redirect_url else redirect_url
            token = oauth.fetch_access_token(code)
            
            # Save token
            self.save_token(token)
            
            # Create client
            self.client = Fitbit(
                self.client_id,
                self.client_secret,
                access_token=token['access_token'],
                refresh_token=token['refresh_token'],
                expires_at=token['expires_at'],
                refresh_cb=self.save_token
            )
            click.echo("Authentication successful!")
            
    def save_token(self, token):
        """Save token to file."""
        with open(self.token_file, 'w') as f:
            json.dump(token, f)
            
    def export_data(self, output_dir='data'):
        """Export Fitbit data for the specified date range."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        click.echo(f"\nExporting data from {self.start_date} to {self.end_date}")
        
        # Calculate number of days
        delta = self.end_date - self.start_date
        total_days = delta.days + 1
        
        with click.progressbar(range(total_days), label='Exporting data') as bar:
            for day_offset in bar:
                current_date = self.start_date + timedelta(days=day_offset)
                date_str = current_date.strftime('%Y-%m-%d')
                
                # Create directory for this date
                date_dir = output_path / current_date.strftime('%Y/%m/%d')
                date_dir.mkdir(parents=True, exist_ok=True)
                
                try:
                    # Export different data types
                    self._export_heart_rate(current_date, date_dir)
                    self._export_sleep(current_date, date_dir)
                    self._export_activity(current_date, date_dir)
                    self._export_steps(current_date, date_dir)
                    
                except Exception as e:
                    click.echo(f"\nError exporting data for {date_str}: {e}")
                    
    def _export_heart_rate(self, date, output_dir):
        """Export heart rate data for a specific date."""
        try:
            date_str = date.strftime('%Y-%m-%d')
            
            # Get intraday heart rate data (1-minute intervals)
            hr_data = self.client.intraday_time_series(
                'activities/heart',
                base_date=date_str,
                detail_level='1min'
            )
            
            # Convert to DataFrame
            if 'activities-heart-intraday' in hr_data:
                dataset = hr_data['activities-heart-intraday']['dataset']
                if dataset:
                    df = pd.DataFrame(dataset)
                    df['date'] = date_str
                    df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'])
                    
                    # Save to CSV
                    csv_file = output_dir / 'heart_rate.csv'
                    df.to_csv(csv_file, index=False)
                    
        except Exception as e:
            if '429' not in str(e):  # Don't log rate limit errors
                click.echo(f"Could not export heart rate for {date}: {e}")
                
    def _export_sleep(self, date, output_dir):
        """Export sleep data for a specific date."""
        try:
            date_str = date.strftime('%Y-%m-%d')
            
            # Get sleep data
            sleep_data = self.client.get_sleep(date_str)
            
            if 'sleep' in sleep_data and sleep_data['sleep']:
                # Convert to DataFrame
                df = pd.DataFrame(sleep_data['sleep'])
                
                # Save to CSV
                csv_file = output_dir / 'sleep.csv'
                df.to_csv(csv_file, index=False)
                
        except Exception as e:
            if '429' not in str(e):
                click.echo(f"Could not export sleep for {date}: {e}")
                
    def _export_activity(self, date, output_dir):
        """Export activity summary for a specific date."""
        try:
            date_str = date.strftime('%Y-%m-%d')
            
            # Get activity summary
            activity_data = self.client.activities(date=date_str)
            
            if 'summary' in activity_data:
                # Convert to DataFrame
                df = pd.DataFrame([activity_data['summary']])
                df['date'] = date_str
                
                # Save to CSV
                csv_file = output_dir / 'activity_summary.csv'
                df.to_csv(csv_file, index=False)
                
        except Exception as e:
            if '429' not in str(e):
                click.echo(f"Could not export activity for {date}: {e}")
                
    def _export_steps(self, date, output_dir):
        """Export step data for a specific date."""
        try:
            date_str = date.strftime('%Y-%m-%d')
            
            # Get intraday step data
            steps_data = self.client.intraday_time_series(
                'activities/steps',
                base_date=date_str,
                detail_level='15min'
            )
            
            if 'activities-steps-intraday' in steps_data:
                dataset = steps_data['activities-steps-intraday']['dataset']
                if dataset:
                    df = pd.DataFrame(dataset)
                    df['date'] = date_str
                    df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'])
                    
                    # Save to CSV
                    csv_file = output_dir / 'steps.csv'
                    df.to_csv(csv_file, index=False)
                    
        except Exception as e:
            if '429' not in str(e):
                click.echo(f"Could not export steps for {date}: {e}")


def export_with_date_range(config_file='myfitbit.ini', output_dir='data'):
    """Main export function with date range support."""
    exporter = FitbitExporter(config_file)
    
    click.echo(f"Starting Fitbit export...")
    click.echo(f"Date range: {exporter.start_date} to {exporter.end_date}")
    
    # Authenticate
    exporter.authenticate()
    
    # Export data
    exporter.export_data(output_dir)
    
    click.echo("\nExport complete!")
    

if __name__ == "__main__":
    export_with_date_range()