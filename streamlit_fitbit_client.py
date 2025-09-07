"""
Streamlit-compatible Fitbit API client that uses stored tokens.
Bypasses myfitbit's interactive OAuth for seamless dashboard integration.
"""
import requests
import json
from datetime import datetime, timedelta, date
from pathlib import Path
import configparser
import time
import subprocess
import os


class StreamlitFitbitClient:
    """Fitbit API client using pre-authenticated tokens from Streamlit OAuth."""
    
    def __init__(self, config_file='myfitbit.ini', progress_callback=None):
        """Initialize with config file."""
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        
        # API settings
        self.base_url = "https://api.fitbit.com"
        self.token_file = Path('.streamlit_fitbit_tokens.json')
        
        # Progress callback for UI updates
        self.progress_callback = progress_callback
        
        # Data folder from config
        self.data_folder = Path(self.config.get('paths', 'output_folder', fallback='data'))
        self.data_folder.mkdir(exist_ok=True)
    
    def log(self, message):
        """Log message to callback or console."""
        if self.progress_callback:
            self.progress_callback(message)
        else:
            print(message)
        
    def load_tokens(self):
        """Load authentication tokens."""
        if not self.token_file.exists():
            return None
        
        try:
            with open(self.token_file, 'r') as f:
                tokens = json.load(f)
            
            # Check if token is expired
            expires_at = datetime.fromisoformat(tokens.get('expires_at', '1970-01-01'))
            if datetime.now() > expires_at:
                return None
                
            return tokens
        except Exception:
            return None
    
    def get_headers(self):
        """Get authorization headers."""
        tokens = self.load_tokens()
        if not tokens:
            return None
            
        return {
            'Authorization': f"Bearer {tokens['access_token']}",
            'Accept': 'application/json'
        }
    
    def api_request(self, endpoint, params=None):
        """Make authenticated API request with rate limiting."""
        headers = self.get_headers()
        if not headers:
            raise Exception("Not authenticated")
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.get(url, headers=headers, params=params)
            
            # Handle rate limiting
            if response.status_code == 429:
                self.log("⏰ Rate limit reached, waiting 60 seconds...")
                time.sleep(60)
                response = requests.get(url, headers=headers, params=params)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                raise Exception("Authentication expired - please re-authenticate")
            raise Exception(f"API request failed: {e}")
    
    def download_heart_rate(self, date_str):
        """Download heart rate data for a specific date."""
        self.log(f"📊 Downloading heart rate data for {date_str}")
        
        try:
            # Get intraday heart rate data (1-minute detail)
            endpoint = f"/1/user/-/activities/heart/date/{date_str}/1d/1min.json"
            data = self.api_request(endpoint)
            
            # Save raw data
            output_file = self.data_folder / 'heart_rate' / f'{date_str}.csv'
            output_file.parent.mkdir(exist_ok=True)
            
            # Convert to CSV format
            if 'activities-heart-intraday' in data and 'dataset' in data['activities-heart-intraday']:
                with open(output_file, 'w') as f:
                    f.write("time,heart_rate\\n")
                    for entry in data['activities-heart-intraday']['dataset']:
                        f.write(f"{entry['time']},{entry['value']}\\n")
                        
                self.log(f"💾 Saved heart rate data: {output_file}")
            else:
                self.log(f"⚠️ No heart rate data available for {date_str}")
                
        except Exception as e:
            self.log(f"❌ Error downloading heart rate for {date_str}: {e}")
    
    def download_sleep(self, date_str):
        """Download sleep data for a specific date."""
        self.log(f"😴 Downloading sleep data for {date_str}")
        
        try:
            endpoint = f"/1.2/user/-/sleep/date/{date_str}.json"
            data = self.api_request(endpoint)
            
            # Save raw data
            output_file = self.data_folder / 'sleep' / f'{date_str}.csv'
            output_file.parent.mkdir(exist_ok=True)
            
            # Convert to CSV format
            if 'sleep' in data and data['sleep']:
                with open(output_file, 'w') as f:
                    f.write("startTime,endTime,duration,efficiency,stages_deep,stages_light,stages_rem,stages_wake\\n")
                    for sleep_log in data['sleep']:
                        start = sleep_log.get('startTime', '')
                        end = sleep_log.get('endTime', '')
                        duration = sleep_log.get('duration', 0) // 60000  # Convert to minutes
                        efficiency = sleep_log.get('efficiency', 0)
                        
                        # Sleep stages (if available)
                        stages = sleep_log.get('levels', {}).get('summary', {})
                        deep = stages.get('deep', {}).get('minutes', 0)
                        light = stages.get('light', {}).get('minutes', 0)
                        rem = stages.get('rem', {}).get('minutes', 0)
                        wake = stages.get('wake', {}).get('minutes', 0)
                        
                        f.write(f"{start},{end},{duration},{efficiency},{deep},{light},{rem},{wake}\\n")
                        
                self.log(f"💾 Saved sleep data: {output_file}")
            else:
                self.log(f"⚠️ No sleep data available for {date_str}")
                
        except Exception as e:
            self.log(f"❌ Error downloading sleep for {date_str}: {e}")
    
    def download_activity(self, date_str):
        """Download activity data for a specific date."""
        self.log(f"🏃 Downloading activity data for {date_str}")
        
        try:
            # Get steps intraday data
            endpoint = f"/1/user/-/activities/steps/date/{date_str}/1d/1min.json"
            steps_data = self.api_request(endpoint)
            
            # Get daily activity summary
            endpoint = f"/1/user/-/activities/date/{date_str}.json"
            activity_data = self.api_request(endpoint)
            
            # Save steps data
            steps_file = self.data_folder / 'steps' / f'{date_str}.csv'
            steps_file.parent.mkdir(exist_ok=True)
            
            if 'activities-steps-intraday' in steps_data and 'dataset' in steps_data['activities-steps-intraday']:
                with open(steps_file, 'w') as f:
                    f.write("time,steps\\n")
                    for entry in steps_data['activities-steps-intraday']['dataset']:
                        f.write(f"{entry['time']},{entry['value']}\\n")
                        
                self.log(f"💾 Saved steps data: {steps_file}")
            
            # Save activity summary
            if 'summary' in activity_data:
                summary_file = self.data_folder / 'activity_summary' / f'{date_str}.csv'
                summary_file.parent.mkdir(exist_ok=True)
                
                summary = activity_data['summary']
                with open(summary_file, 'w') as f:
                    f.write("date,steps,distance,calories,active_minutes\\n")
                    f.write(f"{date_str},{summary.get('steps', 0)},{summary.get('distances', [{}])[0].get('distance', 0)},{summary.get('caloriesOut', 0)},{summary.get('veryActiveMinutes', 0) + summary.get('fairlyActiveMinutes', 0)}\\n")
                
                self.log(f"💾 Saved activity summary: {summary_file}")
                
        except Exception as e:
            self.log(f"❌ Error downloading activity for {date_str}: {e}")
    
    def download_date_range(self, start_date, end_date):
        """Download data for a date range."""
        self.log(f"🚀 Starting download from {start_date} to {end_date}")
        
        current_date = start_date
        total_days = (end_date - current_date).days + 1
        day_count = 0
        
        while current_date <= end_date:
            day_count += 1
            date_str = current_date.strftime('%Y-%m-%d')
            
            self.log(f"📅 Day {day_count}/{total_days}: {date_str}")
            
            # Download all data types for this date
            self.download_heart_rate(date_str)
            self.download_sleep(date_str)
            self.download_activity(date_str)
            
            # Small delay between dates to be nice to the API
            time.sleep(1)
            
            current_date += timedelta(days=1)
        
        self.log(f"✅ Download complete! {total_days} days processed.")
        return True
    
    def run_recent_update(self, days=6):
        """Download recent data (last N days)."""
        today = date.today()
        start_date = today - timedelta(days=days-1)
        
        self.log(f"🔄 Downloading recent {days} days: {start_date} to {today}")
        
        return self.download_date_range(start_date, today)


def test_authenticated_client():
    """Test the authenticated client."""
    client = StreamlitFitbitClient()
    
    # Check if we have valid tokens
    if not client.load_tokens():
        client.log("❌ No valid authentication tokens found")
        return False
    
    try:
        # Test with just today's data
        today = date.today()
        success = client.download_date_range(today, today)
        return success
    except Exception as e:
        client.log(f"❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    # Test the client
    test_authenticated_client()