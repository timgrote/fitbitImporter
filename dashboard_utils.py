#!/usr/bin/env python3
"""Utility functions for loading and processing Fitbit data for the dashboard."""

import pandas as pd
import streamlit as st
from pathlib import Path
from datetime import datetime, timedelta, date
from typing import Dict, List, Tuple, Optional
import glob
import os

@st.cache_data
def find_latest_data_date(data_folder: str = 'data') -> Optional[date]:
    """Find the most recent date across all data types."""
    data_path = Path(data_folder)
    latest_date = None
    
    for data_type_dir in data_path.iterdir():
        if data_type_dir.is_dir():
            csv_files = list(data_type_dir.glob('*.csv'))
            if csv_files:
                # Extract dates from filenames
                dates = []
                for csv_file in csv_files:
                    try:
                        file_date = datetime.strptime(csv_file.stem, '%Y-%m-%d').date()
                        dates.append(file_date)
                    except ValueError:
                        continue
                
                if dates:
                    max_date = max(dates)
                    if latest_date is None or max_date > latest_date:
                        latest_date = max_date
    
    return latest_date

@st.cache_data
def get_date_range_for_data(data_folder: str = 'data') -> Tuple[Optional[date], Optional[date]]:
    """Get the full date range available in the data."""
    data_path = Path(data_folder)
    min_date = None
    max_date = None
    
    for data_type_dir in data_path.iterdir():
        if data_type_dir.is_dir():
            csv_files = list(data_type_dir.glob('*.csv'))
            if csv_files:
                dates = []
                for csv_file in csv_files:
                    try:
                        file_date = datetime.strptime(csv_file.stem, '%Y-%m-%d').date()
                        dates.append(file_date)
                    except ValueError:
                        continue
                
                if dates:
                    if min_date is None or min(dates) < min_date:
                        min_date = min(dates)
                    if max_date is None or max(dates) > max_date:
                        max_date = max(dates)
    
    return min_date, max_date

@st.cache_data
def load_data_type(data_type: str, start_date: date, end_date: date, 
                   data_folder: str = 'data') -> pd.DataFrame:
    """Load data for a specific type within a date range."""
    data_path = Path(data_folder) / data_type
    
    if not data_path.exists():
        return pd.DataFrame()
    
    dfs = []
    current_date = start_date
    
    while current_date <= end_date:
        csv_file = data_path / f"{current_date.strftime('%Y-%m-%d')}.csv"
        if csv_file.exists():
            try:
                df = pd.read_csv(csv_file)
                if not df.empty:
                    # Add file date as metadata for potential use later
                    df['_file_date'] = current_date
                    # Ensure we have a date column
                    if 'date' not in df.columns and 'datetime' not in df.columns:
                        df['date'] = current_date
                    dfs.append(df)
            except Exception as e:
                st.warning(f"Error loading {csv_file}: {e}")
        
        current_date += timedelta(days=1)
    
    if dfs:
        combined_df = pd.concat(dfs, ignore_index=True)
        
        # Convert datetime columns if they exist
        for col in ['datetime', 'startTime', 'endTime']:
            if col in combined_df.columns:
                combined_df[col] = pd.to_datetime(combined_df[col], errors='coerce')
        
        # Ensure date column exists
        if 'date' in combined_df.columns:
            combined_df['date'] = pd.to_datetime(combined_df['date'], errors='coerce').dt.date
        elif 'datetime' in combined_df.columns:
            # Extract date from datetime column
            try:
                combined_df['datetime'] = pd.to_datetime(combined_df['datetime'], errors='coerce')
                combined_df['date'] = combined_df['datetime'].dt.date
            except Exception:
                # Fallback: use file date
                if '_file_date' in combined_df.columns:
                    combined_df['date'] = combined_df['_file_date']
        else:
            # No datetime column, use file date
            if '_file_date' in combined_df.columns:
                combined_df['date'] = combined_df['_file_date']
        
        # Clean up temporary column
        if '_file_date' in combined_df.columns:
            combined_df = combined_df.drop('_file_date', axis=1)
            
        return combined_df
    
    return pd.DataFrame()

@st.cache_data
def get_health_summary(start_date: date, end_date: date, data_folder: str = 'data') -> Dict:
    """Get summary statistics for the date range."""
    summary = {}
    
    # Heart rate summary
    hr_data = load_data_type('heart_rate', start_date, end_date, data_folder)
    if not hr_data.empty and 'heart_rate' in hr_data.columns:
        summary['avg_heart_rate'] = hr_data['heart_rate'].mean()
        summary['resting_heart_rate'] = hr_data['heart_rate'].quantile(0.1)  # Rough estimate
        summary['max_heart_rate'] = hr_data['heart_rate'].max()
    
    # Sleep summary
    sleep_data = load_data_type('sleep', start_date, end_date, data_folder)
    if not sleep_data.empty:
        if 'minutesAsleep' in sleep_data.columns:
            summary['avg_sleep_hours'] = sleep_data['minutesAsleep'].mean() / 60
        if 'efficiency' in sleep_data.columns:
            summary['avg_sleep_efficiency'] = sleep_data['efficiency'].mean()
    
    # Steps summary
    steps_data = load_data_type('steps', start_date, end_date, data_folder)
    if not steps_data.empty and 'steps' in steps_data.columns:
        # Group by date and sum steps for daily totals
        if 'date' in steps_data.columns:
            daily_steps = steps_data.groupby('date')['steps'].sum()
            summary['avg_daily_steps'] = daily_steps.mean()
            summary['total_steps'] = daily_steps.sum()
        else:
            summary['total_steps'] = steps_data['steps'].sum()
    
    # Calories summary
    calories_data = load_data_type('calories', start_date, end_date, data_folder)
    if not calories_data.empty and 'calories' in calories_data.columns:
        if 'date' in calories_data.columns:
            daily_calories = calories_data.groupby('date')['calories'].sum()
            summary['avg_daily_calories'] = daily_calories.mean()
            summary['total_calories'] = daily_calories.sum()
        else:
            summary['total_calories'] = calories_data['calories'].sum()
    
    return summary

def get_available_data_types(data_folder: str = 'data') -> List[str]:
    """Get list of available data types in the data folder."""
    data_path = Path(data_folder)
    if not data_path.exists():
        return []
    
    data_types = []
    for item in data_path.iterdir():
        if item.is_dir() and list(item.glob('*.csv')):
            data_types.append(item.name)
    
    return sorted(data_types)

def format_duration(minutes: float) -> str:
    """Format minutes into hours and minutes string."""
    if pd.isna(minutes):
        return "N/A"
    
    hours = int(minutes // 60)
    mins = int(minutes % 60)
    
    if hours > 0:
        return f"{hours}h {mins}m"
    else:
        return f"{mins}m"

def calculate_default_date_range(data_folder: str = 'data') -> Tuple[date, date]:
    """Calculate default date range (last 7 days with data)."""
    latest_date = find_latest_data_date(data_folder)
    
    if latest_date:
        # Default to last 7 days ending on latest date
        start_date = latest_date - timedelta(days=6)  # 7 days total including end date
        return start_date, latest_date
    else:
        # Fallback to last 7 days from today
        today = datetime.now().date()
        start_date = today - timedelta(days=6)
        return start_date, today

def aggregate_data_by_time(df: pd.DataFrame, aggregation: str, value_column: str) -> pd.DataFrame:
    """Aggregate data by time period (Daily, Weekly, Monthly)."""
    if df.empty or 'date' not in df.columns:
        return df
    
    # Ensure date column is datetime for grouping
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    
    if aggregation == "Daily":
        # Already daily - just group by date and sum
        result = df.groupby('date')[value_column].sum().reset_index()
        result['period'] = result['date'].dt.strftime('%Y-%m-%d')
        
    elif aggregation == "Weekly":
        # Group by week (Monday start)
        df['week'] = df['date'].dt.to_period('W-MON')
        result = df.groupby('week')[value_column].sum().reset_index()
        result['date'] = result['week'].dt.start_time
        result['period'] = result['week'].astype(str)
        
    elif aggregation == "Monthly":
        # Group by month
        df['month'] = df['date'].dt.to_period('M')
        result = df.groupby('month')[value_column].sum().reset_index()
        result['date'] = result['month'].dt.start_time
        result['period'] = result['month'].dt.strftime('%Y-%m')
    
    return result

def aggregate_heart_rate_by_time(df: pd.DataFrame, aggregation: str) -> pd.DataFrame:
    """Aggregate heart rate data by time period (uses mean instead of sum)."""
    if df.empty or 'date' not in df.columns:
        return df
    
    # Ensure date column is datetime for grouping
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    
    if aggregation == "Daily":
        # Calculate daily statistics
        result = df.groupby('date')['heart_rate'].agg([
            ('min_hr', 'min'),
            ('avg_hr', 'mean'), 
            ('max_hr', 'max'),
            ('resting_hr', lambda x: x.quantile(0.1))
        ]).reset_index()
        result['period'] = result['date'].dt.strftime('%Y-%m-%d')
        
    elif aggregation == "Weekly":
        # Group by week and average
        df['week'] = df['date'].dt.to_period('W-MON')
        result = df.groupby('week')['heart_rate'].agg([
            ('min_hr', 'min'),
            ('avg_hr', 'mean'), 
            ('max_hr', 'max'),
            ('resting_hr', lambda x: x.quantile(0.1))
        ]).reset_index()
        result['date'] = result['week'].dt.start_time
        result['period'] = result['week'].astype(str)
        
    elif aggregation == "Monthly":
        # Group by month and average
        df['month'] = df['date'].dt.to_period('M')
        result = df.groupby('month')['heart_rate'].agg([
            ('min_hr', 'min'),
            ('avg_hr', 'mean'), 
            ('max_hr', 'max'),
            ('resting_hr', lambda x: x.quantile(0.1))
        ]).reset_index()
        result['date'] = result['month'].dt.start_time
        result['period'] = result['month'].dt.strftime('%Y-%m')
    
    return result

def format_number(value: float, decimals: int = 0) -> str:
    """Format number with thousands separators."""
    if pd.isna(value):
        return "N/A"
    
    if decimals == 0:
        return f"{int(value):,}"
    else:
        return f"{value:,.{decimals}f}"