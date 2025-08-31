#!/usr/bin/env python3
"""Fitbit Health Dashboard - Interactive Streamlit app for exploring your health data."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta, date
import numpy as np

from dashboard_utils import (
    find_latest_data_date,
    get_date_range_for_data, 
    load_data_type,
    get_health_summary,
    get_available_data_types,
    format_duration,
    calculate_default_date_range,
    aggregate_data_by_time,
    aggregate_heart_rate_by_time,
    format_number
)

# Page configuration
st.set_page_config(
    page_title="Fitbit Health Dashboard",
    page_icon="❤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Main title and description
st.title("❤️ Fitbit Health Dashboard")
st.markdown("Explore your comprehensive health data with interactive visualizations")

# Sidebar for controls
st.sidebar.header("📅 Data Controls")

# Check if data exists
available_data_types = get_available_data_types()
if not available_data_types:
    st.error("No data found! Please run `python main.py process-takeout` first to process your Fitbit data.")
    st.stop()

# Get available date range
min_date, max_date = get_date_range_for_data()
if not min_date or not max_date:
    st.error("Could not determine date range from data files.")
    st.stop()

# Default date range (last 7 days with data)
default_start, default_end = calculate_default_date_range()

st.sidebar.write(f"**Available data:** {min_date} to {max_date}")
st.sidebar.write(f"**Total days:** {(max_date - min_date).days + 1}")

# Date range picker
date_range = st.sidebar.date_input(
    "Select date range",
    value=(default_start, default_end),
    min_value=min_date,
    max_value=max_date
)

# Handle date range selection
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    # Single date selected, use as both start and end
    start_date = end_date = date_range if isinstance(date_range, date) else default_start

# Quick date range buttons
st.sidebar.write("**Quick selections:**")
col1, col2 = st.sidebar.columns(2)

with col1:
    if st.button("Last 7 days"):
        start_date, end_date = calculate_default_date_range()
        st.rerun()
    
    if st.button("Last 30 days"):
        latest = find_latest_data_date()
        if latest:
            start_date = latest - timedelta(days=29)
            end_date = latest
            st.rerun()

with col2:
    if st.button("Last 90 days"):
        latest = find_latest_data_date()
        if latest:
            start_date = latest - timedelta(days=89)
            end_date = latest
            st.rerun()
    
    if st.button("All data"):
        start_date = min_date
        end_date = max_date
        st.rerun()

# Time aggregation selector
st.sidebar.header("📊 View Options")
time_aggregation = st.sidebar.selectbox(
    "Time aggregation",
    ["Daily", "Weekly", "Monthly"],
    index=0,
    help="Choose how to group your data for easier viewing of long time periods"
)

# Data type selector
selected_data_types = st.sidebar.multiselect(
    "Choose data to display",
    available_data_types,
    default=['heart_rate', 'sleep', 'steps', 'calories'] if all(dt in available_data_types for dt in ['heart_rate', 'sleep', 'steps', 'calories']) else available_data_types[:4]
)

# Main dashboard content
days_selected = (end_date - start_date).days + 1
st.subheader(f"📈 Health Overview: {start_date} to {end_date} ({days_selected} days)")

# Load and display summary metrics
with st.spinner("Loading health data..."):
    summary = get_health_summary(start_date, end_date)

# Summary cards - Make steps and calories more prominent
col1, col2, col3, col4 = st.columns(4)

with col1:
    if 'avg_daily_steps' in summary:
        steps_delta = ""
        if summary['avg_daily_steps'] >= 10000:
            steps_delta = "🎯 Goal achieved!"
        elif summary['avg_daily_steps'] >= 8000:
            steps_delta = "📈 Close to goal"
        
        st.metric(
            "🚶 Daily Steps", 
            format_number(summary['avg_daily_steps']),
            steps_delta
        )
    else:
        st.metric("🚶 Daily Steps", "No data")

with col2:
    if 'avg_daily_calories' in summary:
        st.metric(
            "🔥 Daily Calories", 
            format_number(summary['avg_daily_calories']),
            f"Total: {format_number(summary.get('total_calories', 0))}"
        )
    else:
        st.metric("🔥 Daily Calories", "No data")

with col3:
    if 'avg_heart_rate' in summary:
        st.metric(
            "❤️ Average Heart Rate", 
            f"{summary['avg_heart_rate']:.0f} BPM",
            f"Resting: ~{summary.get('resting_heart_rate', 0):.0f} BPM"
        )
    else:
        st.metric("❤️ Average Heart Rate", "No data")

with col4:
    if 'avg_sleep_hours' in summary:
        sleep_delta = ""
        if summary['avg_sleep_hours'] >= 8:
            sleep_delta = "😴 Great sleep!"
        elif summary['avg_sleep_hours'] >= 7:
            sleep_delta = "😌 Good sleep"
        
        st.metric(
            "😴 Average Sleep", 
            format_duration(summary['avg_sleep_hours'] * 60),
            sleep_delta
        )
    else:
        st.metric("😴 Average Sleep", "No data")

# Charts section
st.header("📊 Interactive Charts")

# Create tabs for different chart types
tab1, tab2, tab3, tab4 = st.tabs(["❤️ Heart Rate", "😴 Sleep", "🏃 Activity", "📈 Trends"])

with tab1:
    if 'heart_rate' in selected_data_types and 'heart_rate' in available_data_types:
        st.subheader("Heart Rate Analysis")
        
        hr_data = load_data_type('heart_rate', start_date, end_date)
        
        if not hr_data.empty and 'heart_rate' in hr_data.columns:
            # Show data points info
            st.info(f"Processing {len(hr_data):,} heart rate readings")
            
            # Aggregate heart rate data by time period
            if 'date' in hr_data.columns or 'datetime' in hr_data.columns:
                # Use date if available, otherwise extract from datetime
                if 'date' in hr_data.columns:
                    date_col = 'date'
                else:
                    hr_data['date'] = pd.to_datetime(hr_data['datetime']).dt.date
                    date_col = 'date'
                
                # Aggregate by selected time period
                aggregated_hr = aggregate_heart_rate_by_time(hr_data, time_aggregation)
                
                if not aggregated_hr.empty:
                    # Daily average heart rate
                    fig = px.bar(
                        aggregated_hr,
                        x='period' if time_aggregation != "Daily" else 'date',
                        y='avg_hr',
                        title=f"{time_aggregation} Average Heart Rate",
                        labels={'avg_hr': 'Average Heart Rate (BPM)', 'period': 'Period', 'date': 'Date'},
                        color='avg_hr',
                        color_continuous_scale='Reds'
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Heart rate zones (min, resting, avg, max)
                    fig_zones = go.Figure()
                    x_axis = aggregated_hr['period'] if time_aggregation != "Daily" else aggregated_hr['date']
                    
                    fig_zones.add_trace(go.Scatter(
                        x=x_axis, y=aggregated_hr['min_hr'], 
                        mode='lines', name='Min HR', line=dict(color='lightblue')
                    ))
                    fig_zones.add_trace(go.Scatter(
                        x=x_axis, y=aggregated_hr['resting_hr'], 
                        mode='lines', name='Resting HR', line=dict(color='green')
                    ))
                    fig_zones.add_trace(go.Scatter(
                        x=x_axis, y=aggregated_hr['avg_hr'], 
                        mode='lines+markers', name='Average HR', line=dict(color='orange')
                    ))
                    fig_zones.add_trace(go.Scatter(
                        x=x_axis, y=aggregated_hr['max_hr'], 
                        mode='lines', name='Max HR', line=dict(color='red')
                    ))
                    
                    fig_zones.update_layout(
                        title=f"Heart Rate Zones Over Time ({time_aggregation})",
                        xaxis_title="Period" if time_aggregation != "Daily" else "Date",
                        yaxis_title="Heart Rate (BPM)",
                        height=400
                    )
                    st.plotly_chart(fig_zones, use_container_width=True)
            
            # Heart rate distribution
            fig_hist = px.histogram(
                hr_data.sample(min(10000, len(hr_data))),  # Sample for performance
                x='heart_rate',
                title="Heart Rate Distribution",
                labels={'heart_rate': 'Heart Rate (BPM)', 'count': 'Frequency'},
                nbins=50,
                color_discrete_sequence=['lightcoral']
            )
            st.plotly_chart(fig_hist, use_container_width=True)
            
        else:
            st.warning("No heart rate data available for selected date range")
    else:
        st.info("Heart rate data not selected or not available")

with tab2:
    if 'sleep' in selected_data_types and 'sleep' in available_data_types:
        st.subheader("Sleep Analysis")
        
        # Explain sleep efficiency
        with st.expander("💡 What is Sleep Efficiency?"):
            st.write("""
            **Sleep Efficiency** = (Time Actually Sleeping ÷ Time in Bed) × 100
            
            - **85%+ = Excellent** - You're sleeping most of the time you're in bed
            - **75-84% = Good** - Normal range for most adults  
            - **65-74% = Fair** - Some room for improvement
            - **<65% = Poor** - May indicate sleep issues
            
            This metric helps track sleep quality beyond just duration.
            """)
        
        sleep_data = load_data_type('sleep', start_date, end_date)
        
        if not sleep_data.empty:
            st.info(f"Displaying {len(sleep_data)} sleep sessions")
            
            # Sleep duration over time
            if 'date' in sleep_data.columns and 'minutesAsleep' in sleep_data.columns:
                sleep_data_copy = sleep_data.copy()
                sleep_data_copy['hoursAsleep'] = sleep_data_copy['minutesAsleep'] / 60
                
                # Aggregate sleep data by time period
                aggregated_sleep = aggregate_data_by_time(sleep_data_copy, time_aggregation, 'minutesAsleep')
                if not aggregated_sleep.empty:
                    aggregated_sleep['hoursAsleep'] = aggregated_sleep['minutesAsleep'] / 60
                    
                    fig = px.bar(
                        aggregated_sleep,
                        x='period' if time_aggregation != "Daily" else 'date',
                        y='hoursAsleep', 
                        title=f"{time_aggregation} Sleep Duration",
                        labels={'hoursAsleep': 'Hours of Sleep', 'period': 'Period', 'date': 'Date'},
                        color='hoursAsleep',
                        color_continuous_scale='Blues'
                    )
                    fig.add_hline(y=8, line_dash="dash", annotation_text="8 hours", line_color="green")
                    fig.add_hline(y=7, line_dash="dash", annotation_text="7 hours", line_color="orange")
                    st.plotly_chart(fig, use_container_width=True)
            
            # Sleep efficiency if available
            if 'efficiency' in sleep_data.columns:
                # For efficiency, we want to average it, not sum it
                if 'date' in sleep_data.columns:
                    sleep_eff_data = sleep_data.copy()
                    sleep_eff_data['date'] = pd.to_datetime(sleep_eff_data['date'])
                    
                    if time_aggregation == "Daily":
                        result = sleep_eff_data.groupby('date')['efficiency'].mean().reset_index()
                        result['period'] = result['date'].dt.strftime('%Y-%m-%d')
                    elif time_aggregation == "Weekly":
                        sleep_eff_data['week'] = sleep_eff_data['date'].dt.to_period('W-MON')
                        result = sleep_eff_data.groupby('week')['efficiency'].mean().reset_index()
                        result['date'] = result['week'].dt.start_time
                        result['period'] = result['week'].astype(str)
                    elif time_aggregation == "Monthly":
                        sleep_eff_data['month'] = sleep_eff_data['date'].dt.to_period('M')
                        result = sleep_eff_data.groupby('month')['efficiency'].mean().reset_index()
                        result['date'] = result['month'].dt.start_time
                        result['period'] = result['month'].dt.strftime('%Y-%m')
                    
                    fig_eff = px.bar(
                        result,
                        x='period' if time_aggregation != "Daily" else 'date',
                        y='efficiency',
                        title=f"{time_aggregation} Sleep Efficiency",
                        labels={'efficiency': 'Sleep Efficiency (%)', 'period': 'Period', 'date': 'Date'},
                        color='efficiency',
                        color_continuous_scale='Greens'
                    )
                    fig_eff.add_hline(y=85, line_dash="dash", annotation_text="Excellent (85%+)", line_color="green")
                    fig_eff.add_hline(y=75, line_dash="dash", annotation_text="Good (75%+)", line_color="orange")
                    st.plotly_chart(fig_eff, use_container_width=True)
            
            # Sleep stages if available
            if all(col in sleep_data.columns for col in ['deep_minutes', 'light_minutes', 'rem_minutes']):
                st.subheader("Sleep Stages Breakdown")
                
                # Calculate daily totals for each stage
                sleep_stages = sleep_data.groupby('date')[['deep_minutes', 'light_minutes', 'rem_minutes', 'wake_minutes']].sum().reset_index()
                
                fig_stages = go.Figure()
                fig_stages.add_trace(go.Bar(x=sleep_stages['date'], y=sleep_stages['deep_minutes'], name='Deep Sleep', marker_color='darkblue'))
                fig_stages.add_trace(go.Bar(x=sleep_stages['date'], y=sleep_stages['rem_minutes'], name='REM Sleep', marker_color='purple'))
                fig_stages.add_trace(go.Bar(x=sleep_stages['date'], y=sleep_stages['light_minutes'], name='Light Sleep', marker_color='lightblue'))
                if 'wake_minutes' in sleep_stages.columns:
                    fig_stages.add_trace(go.Bar(x=sleep_stages['date'], y=sleep_stages['wake_minutes'], name='Wake Time', marker_color='red'))
                
                fig_stages.update_layout(
                    title="Sleep Stages by Night",
                    xaxis_title="Date",
                    yaxis_title="Minutes",
                    barmode='stack',
                    height=400
                )
                st.plotly_chart(fig_stages, use_container_width=True)
                
        else:
            st.warning("No sleep data available for selected date range")
    else:
        st.info("Sleep data not selected or not available")

with tab3:
    st.subheader("Daily Activity Overview")
    
    # Create two columns for side-by-side activity charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Steps chart
        if 'steps' in available_data_types:
            steps_data = load_data_type('steps', start_date, end_date)
            
            if not steps_data.empty and 'steps' in steps_data.columns:
                if 'date' in steps_data.columns:
                    # Aggregate steps data by time period
                    aggregated_steps = aggregate_data_by_time(steps_data, time_aggregation, 'steps')
                    
                    if not aggregated_steps.empty:
                        fig_steps = px.bar(
                            aggregated_steps,
                            x='period' if time_aggregation != "Daily" else 'date',
                            y='steps',
                            title=f"🚶 {time_aggregation} Steps",
                            labels={'steps': 'Steps', 'period': 'Period', 'date': 'Date'},
                            color='steps',
                            color_continuous_scale='Greens'
                        )
                        
                        # Adjust goals based on time period
                        if time_aggregation == "Daily":
                            fig_steps.add_hline(y=10000, line_dash="dash", annotation_text="10K Goal", line_color="green")
                            fig_steps.add_hline(y=8000, line_dash="dash", annotation_text="8K", line_color="orange")
                        elif time_aggregation == "Weekly":
                            fig_steps.add_hline(y=70000, line_dash="dash", annotation_text="70K Weekly", line_color="green")
                        elif time_aggregation == "Monthly":
                            fig_steps.add_hline(y=300000, line_dash="dash", annotation_text="300K Monthly", line_color="green")
                        
                        fig_steps.update_layout(height=400)
                        st.plotly_chart(fig_steps, use_container_width=True)
                        
                        # Steps summary with proper formatting
                        total_steps = aggregated_steps['steps'].sum()
                        if time_aggregation == "Daily":
                            avg_steps = aggregated_steps['steps'].mean()
                            days_over_10k = (aggregated_steps['steps'] >= 10000).sum()
                            st.info(f"📊 **Steps Summary**: Avg {format_number(avg_steps)}/day • Total {format_number(total_steps)} • {days_over_10k}/{len(aggregated_steps)} days hit 10K goal")
                        else:
                            avg_steps = aggregated_steps['steps'].mean()
                            st.info(f"📊 **Steps Summary**: Avg {format_number(avg_steps)}/{time_aggregation.lower()} • Total {format_number(total_steps)}")
                else:
                    st.warning("Steps data found but no date information")
            else:
                st.warning("No steps data available for selected date range")
        else:
            st.warning("Steps data not available")
    
    with col2:
        # Calories chart
        if 'calories' in available_data_types:
            calories_data = load_data_type('calories', start_date, end_date)
            
            if not calories_data.empty and 'calories' in calories_data.columns:
                if 'date' in calories_data.columns:
                    # Aggregate calories data by time period
                    aggregated_calories = aggregate_data_by_time(calories_data, time_aggregation, 'calories')
                    
                    if not aggregated_calories.empty:
                        fig_cal = px.bar(
                            aggregated_calories,
                            x='period' if time_aggregation != "Daily" else 'date',
                            y='calories',
                            title=f"🔥 {time_aggregation} Calories Burned",
                            labels={'calories': 'Calories', 'period': 'Period', 'date': 'Date'},
                            color='calories',
                            color_continuous_scale='Oranges'
                        )
                        
                        # Adjust goals based on time period
                        if time_aggregation == "Daily":
                            fig_cal.add_hline(y=2000, line_dash="dash", annotation_text="2000 cal", line_color="orange")
                        elif time_aggregation == "Weekly":
                            fig_cal.add_hline(y=14000, line_dash="dash", annotation_text="14K Weekly", line_color="orange")
                        elif time_aggregation == "Monthly":
                            fig_cal.add_hline(y=60000, line_dash="dash", annotation_text="60K Monthly", line_color="orange")
                        
                        fig_cal.update_layout(height=400)
                        st.plotly_chart(fig_cal, use_container_width=True)
                        
                        # Calories summary with proper formatting
                        avg_calories = aggregated_calories['calories'].mean()
                        total_calories = aggregated_calories['calories'].sum()
                        
                        st.info(f"🔥 **Calories Summary**: Avg {format_number(avg_calories)}/{time_aggregation.lower()} • Total {format_number(total_calories)}")
                else:
                    st.warning("Calories data found but no date information")
            else:
                st.warning("No calories data available for selected date range")
        else:
            st.warning("Calories data not available")
    
    # Distance chart (full width if available)
    if 'distance' in available_data_types:
        st.subheader("🏃 Distance Traveled")
        distance_data = load_data_type('distance', start_date, end_date)
        
        if not distance_data.empty and 'distance' in distance_data.columns:
            if 'date' in distance_data.columns:
                # Aggregate distance data by time period
                aggregated_distance = aggregate_data_by_time(distance_data, time_aggregation, 'distance')
                
                if not aggregated_distance.empty:
                    fig_dist = px.line(
                        aggregated_distance,
                        x='period' if time_aggregation != "Daily" else 'date',
                        y='distance',
                        title=f"{time_aggregation} Distance Traveled",
                        labels={'distance': 'Distance (km)', 'period': 'Period', 'date': 'Date'},
                        markers=True
                    )
                    fig_dist.update_layout(height=300)
                    st.plotly_chart(fig_dist, use_container_width=True)
                    
                    # Distance summary
                    avg_distance = aggregated_distance['distance'].mean()
                    total_distance = aggregated_distance['distance'].sum()
                    st.info(f"🏃 **Distance Summary**: Avg {avg_distance:.1f} km/{time_aggregation.lower()} • Total {total_distance:.1f} km")
    
    # Combined activity overview
    st.subheader("📈 Activity Trends")
    
    # Try to combine steps, calories, and distance on one chart with aggregation
    activity_combined = pd.DataFrame()
    
    if 'steps' in available_data_types:
        steps_data = load_data_type('steps', start_date, end_date)
        if not steps_data.empty and 'date' in steps_data.columns:
            aggregated_steps = aggregate_data_by_time(steps_data, time_aggregation, 'steps')
            if not aggregated_steps.empty:
                activity_combined['Steps (÷10)'] = aggregated_steps['steps'] / 10  # Scale down for visualization
                activity_combined['date'] = aggregated_steps['date'] if time_aggregation == "Daily" else aggregated_steps['period']
    
    if 'calories' in available_data_types:
        calories_data = load_data_type('calories', start_date, end_date)
        if not calories_data.empty and 'date' in calories_data.columns:
            aggregated_calories = aggregate_data_by_time(calories_data, time_aggregation, 'calories')
            if not aggregated_calories.empty:
                if activity_combined.empty:
                    activity_combined['date'] = aggregated_calories['date'] if time_aggregation == "Daily" else aggregated_calories['period']
                activity_combined['Calories'] = aggregated_calories['calories']
    
    if not activity_combined.empty:
        activity_combined = activity_combined.reset_index(drop=True)
        
        fig_combined = px.line(
            activity_combined,
            x='date',
            y=[col for col in activity_combined.columns if col != 'date'],
            title=f"{time_aggregation} Activity Trends (Steps scaled ÷10 for comparison)",
            labels={'value': 'Activity Level', 'date': 'Period' if time_aggregation != "Daily" else 'Date', 'variable': 'Metric'}
        )
        fig_combined.update_layout(height=300)
        st.plotly_chart(fig_combined, use_container_width=True)

with tab4:
    st.subheader("Health Trends & Correlations")
    st.info("Advanced trend analysis coming soon! This will show correlations between sleep quality, heart rate variability, and activity levels.")

# Footer
st.markdown("---")
st.markdown("🚀 **Fitbit Health Dashboard** - Built with Streamlit and ❤️")
st.markdown(f"*Data range: {min_date} to {max_date} • Showing: {start_date} to {end_date}*")