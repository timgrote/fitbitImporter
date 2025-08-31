# Fitbit Data Importer

A Python-based tool to export your personal Fitbit data to local CSV files for AI analysis and personal use.

## Overview

Fitbit Data Importer allows you to download all your personal health data from Fitbit and save it in CSV format on your local machine. Built on the proven `myfitbit` library, this tool provides a simple way to export your data for analysis by AI tools like Claude, ChatGPT, or custom analytics solutions.

### Key Features

- **Personal Data Access**: Uses Fitbit's Personal API for immediate access to your intraday data
- **Comprehensive Data Export**: Heart rate, sleep, activity, steps, HRV, SpO2, and more
- **Python-Based**: Easy to install and modify, no compilation required
- **AI-Ready Format**: Clean CSV output optimized for AI analysis
- **Rate Limit Handling**: Automatically manages Fitbit's 150 requests/hour limit
- **Incremental Sync**: Only downloads new data on subsequent runs
- **Proven Foundation**: Built on the mature `myfitbit` and `python-fitbit` libraries

## Why Python?

After initially attempting a Go implementation (see [docs/go-approach-summary.md](docs/go-approach-summary.md)), we switched to Python for several reasons:
- **No compilation issues**: Pure Python, works everywhere Python runs
- **Mature ecosystem**: Leverage existing Fitbit libraries with years of development
- **Better for data processing**: Native pandas support, easy CSV handling
- **Faster development**: Build on proven solutions instead of starting from scratch

## Data Types Supported

- **Heart Rate**: Intraday data with 1-minute granularity
- **Sleep**: Sleep stages, duration, efficiency, and restlessness
- **Activity**: Steps, distance, calories, active minutes, floors
- **Body Metrics**: Weight, BMI, body fat percentage
- **HRV**: Heart rate variability data
- **SpO2**: Blood oxygen saturation during sleep

## Getting Started

### Prerequisites

- Python 3.8 or later
- Fitbit Developer Account (for API credentials)

### Installation

#### Option 1: Install via pip (Recommended)

```bash
pip install myfitbit
```

#### Option 2: Install from source

```bash
git clone https://github.com/yourusername/fitbitImporter.git
cd fitbitImporter
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Setup Fitbit API Credentials

1. **Get Fitbit API Credentials**:
   - Go to [dev.fitbit.com](https://dev.fitbit.com)
   - Sign in and click "Manage" → "Register An App"
   - **Application Name**: Choose any name (e.g., "My Fitbit Exporter")  
   - **OAuth 2.0 Application Type**: Select **"Personal"** (Important!)
   - **Redirect URL**: Enter exactly: `http://localhost:8189/auth_code`
   - Save your **Client ID** and **Client Secret**

2. **Configure the Tool**:
   Create a `myfitbit.ini` file:
   ```ini
   [fitbit]
   client_id = YOUR_CLIENT_ID
   client_secret = YOUR_CLIENT_SECRET
   ```

### Usage

#### Export Your Data

```bash
# Export all available data
python -m myfitbit

# Generate HTML report
python -m myfitbit.report

# Or use our enhanced wrapper (coming soon)
python fitbit_export.py --start-date 2024-01-01 --end-date 2024-12-31
```

The tool will:
1. Open your browser for Fitbit authorization
2. Download your data respecting rate limits
3. Save data as CSV files organized by date
4. Resume from where it left off if interrupted

## Data Output

Data is organized in CSV files by date and type:

```
data/
├── 2025/
│   ├── 01/
│   │   ├── heart_rate.csv
│   │   ├── sleep.csv
│   │   ├── activity.csv
│   │   └── steps.csv
│   └── 02/
│       └── ...
└── exports/
    └── summary_2025-01.csv
```

## Using Your Data with AI

The CSV format is perfect for AI analysis. Example queries:

- "Analyze my sleep patterns over the last month"
- "Show correlations between my heart rate and activity levels"
- "Identify trends in my step count and suggest improvements"

## Privacy & Security

- **Local Storage**: All data stays on your machine
- **No Cloud**: We don't store or access your data
- **Open Source**: Full transparency in how your data is handled
- **Secure Authentication**: Uses OAuth2 with Fitbit's official API

## Development

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/fitbitImporter.git
cd fitbitImporter

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run with debug logging
python -m myfitbit --debug
```

### Building Standalone Executable

To create a standalone executable that doesn't require Python:

```bash
# Install PyInstaller
pip install pyinstaller

# Build executable
pyinstaller --onefile --name fitbit-importer main.py

# Find your executable in dist/
```

## Troubleshooting

**Common Issues:**

- **"Invalid redirect_uri" error**: Make sure the Redirect URL in your Fitbit app settings is exactly `http://localhost:8189/auth_code`
- **"Unauthorized" error**: Your app must be set to "Personal" type for intraday data access
- **Rate limit exceeded (HTTP 429)**: This is normal for large exports. The tool will automatically resume after an hour
- **No data appearing**: Some data types require specific Fitbit devices (e.g., SpO2 requires newer devices)
- **ModuleNotFoundError**: Make sure you've activated your virtual environment and installed requirements

## Libraries We Build On

This project leverages these excellent Python libraries:
- **[myfitbit](https://github.com/Knio/myfitbit)**: Core export functionality and rate limit handling
- **[python-fitbit](https://github.com/orcasgit/python-fitbit)**: Fitbit API client implementation
- **pandas**: Data processing and CSV handling
- **requests-oauthlib**: OAuth2 authentication

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Future Enhancements

- [ ] GUI wrapper for easier configuration
- [ ] Google Takeout import support
- [ ] Custom date range selection UI
- [ ] Progress bars for long exports
- [ ] Data visualization dashboard
- [ ] Automated daily backups

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This tool is not affiliated with Fitbit Inc. or Google. Use at your own risk. Always keep backups of important data.

## Support

- **Issues**: Report bugs and request features via [GitHub Issues](../../issues)
- **Documentation**: See [docs/](docs/) for detailed guides
- **API Rate Limits**: The tool automatically handles Fitbit's rate limits (150 req/hour)

---

*Your data belongs to you. Take control of it.*