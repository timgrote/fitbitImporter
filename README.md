# Fitbit Data Importer

A comprehensive Python tool to extract, process, and merge your personal Fitbit data from multiple sources into AI-ready CSV files.

## 🎯 Overview

Fitbit Data Importer combines the best of both worlds:
- **Google Takeout archives** for complete historical data (years of data, instantly)
- **Fitbit API downloads** for recent data and filling gaps
- **Smart merging** to create a unified, comprehensive dataset

### ✨ Key Features

- **📦 Google Takeout Support**: Process your downloaded Fitbit archives instantly
- **🔄 API Integration**: Fill gaps and get recent data via Fitbit API
- **🧠 Smart Merging**: Intelligently combines both data sources
- **📊 Comprehensive Data**: Heart rate, sleep, activity, calories, HRV, SpO2, temperature
- **🤖 AI-Ready**: Clean CSV format perfect for analysis with Claude, ChatGPT, etc.
- **⚡ High Performance**: Process years of data in minutes
- **🔒 Privacy First**: All data stays on your machine

## 📋 Supported Data Types

| Data Type | Google Takeout | Fitbit API | Granularity |
|-----------|----------------|------------|-------------|
| ❤️ **Heart Rate** | ✅ | ✅ | Every 5-15 seconds |
| 😴 **Sleep** | ✅ | ✅ | Nightly + stages |
| 🔥 **Calories** | ✅ | ✅ | Every minute |
| 👣 **Steps** | ✅ | ✅ | Every 15 minutes |
| 📏 **Distance** | ✅ | ✅ | Every 15 minutes |
| 🫁 **SpO2** | ✅ | ✅ | Nightly |
| 🌡️ **Temperature** | ✅ | ❌ | Every minute |
| ❤️‍🩹 **HRV** | ✅ | ❌ | Daily summary |
| 📈 **Activity Summary** | ❌ | ✅ | Daily totals |

## 🚀 Quick Start

### 1. Installation

```bash
git clone https://github.com/yourusername/fitbitImporter.git
cd fitbitImporter
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Get Your Google Takeout Data (Recommended)

This gives you years of data instantly:

1. **Request Your Data**:
   - Go to [Google Takeout](https://takeout.google.com)
   - Select **Fitbit** (deselect everything else)
   - Choose ZIP format, click "Create export"
   - Download the ZIP file(s) when ready

2. **Place Your Data**:
   ```bash
   mkdir takeout_data
   # Drop your downloaded ZIP files into takeout_data/
   mv ~/Downloads/takeout-*.zip takeout_data/
   ```

3. **Process Your Data**:
   ```bash
   python main.py process-takeout
   ```

### 3. Set Up Fitbit API (For Recent Data & Gaps)

1. **Get API Credentials**:
   - Go to [dev.fitbit.com](https://dev.fitbit.com)
   - Register a new app, choose **"Personal"** type
   - Set Redirect URL: `http://localhost:8080/callback`
   - Save your Client ID and Client Secret

2. **Configure Credentials**:
   ```bash
   cp myfitbit.ini.template myfitbit.ini
   # Edit myfitbit.ini with your credentials
   ```

   ```ini
   [fitbit]
   client_id = YOUR_CLIENT_ID
   client_secret = YOUR_CLIENT_SECRET
   
   [export]
   start_date = 2024-08-29
   end_date = 2024-08-31
   ```

3. **Download Recent Data**:
   ```bash
   python main.py export
   ```

4. **Merge Everything**:
   ```bash
   python main.py merge
   ```

## 📊 Command Reference

### Core Commands

```bash
# Process Google Takeout ZIP files
python main.py process-takeout --takeout-folder takeout_data

# Download data via Fitbit API for specific date range
python main.py export --config myfitbit.ini

# Analyze your data and identify gaps
python main.py analyze

# Merge API downloads with Takeout data
python main.py merge

# See all options
python main.py --help
```

### Advanced Usage

```bash
# Analyze specific folder
python main.py analyze --data-folder my_data --export-gaps

# Dry run merge (see what would happen)
python main.py merge --dry-run

# Process Takeout data to custom folder
python main.py process-takeout --output-folder processed_data
```

## 📁 Data Organization

After processing, your data will be organized like this:

```
data/
├── heart_rate/
│   ├── 2023-11-22.csv    # High-freq HR readings
│   ├── 2023-11-23.csv
│   └── ...
├── sleep/
│   ├── 2023-11-23.csv    # Sleep stages, efficiency
│   └── ...
├── calories/
│   ├── 2023-11-21.csv    # Minute-by-minute burn
│   └── ...
├── steps/
├── distance/
├── spo2/
├── temperature/
├── hrv/
├── sleep_score/
└── activity_summary/     # From API only
    ├── 2024-08-29.csv
    └── ...
```

## 🤖 Using Your Data with AI

Your CSV data is perfect for AI analysis:

### Example Queries for Claude/ChatGPT:

- *"I'm uploading my heart rate data. Analyze patterns and identify when I'm most stressed."*
- *"Based on my sleep data, what factors correlate with my best sleep quality?"*
- *"Compare my activity levels before and after [date]. What changed?"*
- *"Find anomalies in my health data that might indicate illness."*

### Sample Data Structure:

**Heart Rate** (`heart_rate/2024-08-29.csv`):
```csv
datetime,heart_rate,confidence
2024-08-29 06:00:02,80,3
2024-08-29 06:00:17,81,3
```

**Sleep** (`sleep/2024-08-29.csv`):
```csv
date,startTime,endTime,minutesAsleep,efficiency,deep_minutes,light_minutes,rem_minutes
2024-08-29,2024-08-28T23:33:30.000,2024-08-29T08:14:00.000,451,95,56,258,137
```

## 🔍 Data Analysis

### Built-in Analysis

```bash
# Get comprehensive data report
python main.py analyze
```

**Sample output:**
```
FITBIT DATA ANALYSIS REPORT
============================
📅 Overall Date Range: 2023-11-21 to 2025-08-31
📊 Total Days Span: 650 days

✅ HEART_RATE: 573 days
✅ SLEEP: 507 days  
✅ CALORIES: 649 days
⚠️  Gaps found: 2024-06-08 to 2024-06-10 (3 days)

💡 Recommended API downloads: [specific date ranges]
```

### Export Gap Analysis

```bash
python main.py analyze --export-gaps
# Creates data_gaps.csv for detailed gap analysis
```

## ⚙️ Configuration

### File Locations

The tool looks for configuration in these locations:
1. `myfitbit.ini` (API credentials & date ranges)  
2. Command line options override config file
3. Default folders: `takeout_data/`, `data/`, `fitbit_download/`

### Sample Configuration

```ini
[fitbit]
client_id = YOUR_CLIENT_ID
client_secret = YOUR_CLIENT_SECRET

[export]
# Download specific date ranges
start_date = 2024-08-29
end_date = 2024-08-31

[paths]
takeout_folder = takeout_data
output_folder = data
api_downloads = fitbit_download
```

## 🔧 Troubleshooting

### Common Issues

**Google Takeout Processing:**
- **Empty ZIP files**: Some Takeout exports may not contain Fitbit data
- **Processing errors**: Check that ZIP files are fully downloaded
- **Missing data types**: Not all Fitbit devices record all metrics

**Fitbit API:**
- **"Invalid redirect_uri"**: Must match exactly in your app settings
- **"Unauthorized"**: App must be set to "Personal" type
- **Rate limits (HTTP 429)**: Normal for large exports, tool auto-resumes

**Data Quality:**
- **Missing heart rate**: Some recent files use different format (handled automatically)
- **Gaps in data**: Use `analyze` command to identify and fill gaps
- **Duplicate data**: Merger automatically prevents duplicates

### Debug Mode

```bash
python main.py export --debug
# Shows detailed API communication and processing steps
```

## 🏗️ Architecture

### Data Pipeline

1. **Google Takeout** → Extract & Convert → Standardized CSV
2. **Fitbit API** → Download → Standardized CSV  
3. **Smart Merger** → Combine sources → Unified Dataset

### Key Components

- **`takeout_processor.py`**: Extracts data from Takeout ZIP files
- **`export.py`**: Downloads data via Fitbit API with date ranges
- **`data_merger.py`**: Intelligently combines both sources
- **`data_analyzer.py`**: Analyzes coverage and identifies gaps

## 🤝 Contributing

We welcome contributions! Areas where help is needed:

- **Data Sources**: Support for other fitness tracker exports
- **Visualizations**: Built-in data visualization tools
- **Analysis**: Pre-built health insight algorithms
- **UI/UX**: Web or desktop interface
- **Testing**: More comprehensive test coverage

## 📄 License

MIT License - Your data, your rules.

## ⚠️ Privacy & Security

- **Local Processing**: All data stays on your machine
- **No Cloud**: We don't store, access, or transmit your data
- **Open Source**: Full transparency in data handling
- **Secure**: Uses official OAuth2 authentication

## 🆘 Support

- **Issues**: [GitHub Issues](../../issues)
- **Documentation**: See `docs/` folder
- **API Limits**: Automatically handled (150 requests/hour)

---

*Take control of your health data. Export it, analyze it, own it.* 💪