# Fitbit Data Importer

A cross-platform tool to export your personal Fitbit data to local CSV files for AI analysis and personal use.

## Overview

Fitbit Data Importer allows you to download all your personal health data from Fitbit and save it in CSV format on your local machine. The exported data can then be easily analyzed by AI tools like Claude, ChatGPT, or custom analytics solutions.

### Key Features

- **Personal Data Access**: Uses Fitbit's Personal API for immediate access to your intraday data
- **Comprehensive Data Export**: Heart rate, sleep, activity, steps, HRV, SpO2, and more
- **Cross-Platform**: Single executable for Windows, Mac, and Linux
- **AI-Ready Format**: Clean CSV output optimized for AI analysis
- **Rate Limit Handling**: Automatically manages Fitbit's 150 requests/hour limit
- **Incremental Sync**: Only downloads new data on subsequent runs
- **No Dependencies**: Portable executable with simple GUI

## Data Types Supported

- **Heart Rate**: Intraday data with 1-minute granularity
- **Sleep**: Sleep stages, duration, efficiency, and restlessness
- **Activity**: Steps, distance, calories, active minutes, floors
- **Body Metrics**: Weight, BMI, body fat percentage
- **HRV**: Heart rate variability data
- **SpO2**: Blood oxygen saturation during sleep

## Getting Started

### Two Methods to Export Your Fitbit Data

#### Method 1: Google Takeout (Recommended - Fast!)

**Best for**: Historical data, bulk exports of years of data

1. **Export from Google**:
   - Open the Fitbit app → Profile → "Your Fitbit data"
   - OR go directly to [takeout.google.com](https://takeout.google.com)
   - Select Fitbit data and request export
   - Wait 2-5 hours for Google to prepare your data
   - Download the ZIP file when ready

2. **Import to this app**:
   - Run the Fitbit Importer app
   - Choose your export directory
   - Click "Import Google Takeout"
   - Select the downloaded ZIP file
   - Wait a few minutes for processing (vs hours with API!)

#### Method 2: Fitbit API Sync (Real-time but Slow)

**Best for**: Daily/weekly syncs, staying up-to-date with recent data

1. **Get Fitbit API Credentials**:
   - Go to [dev.fitbit.com](https://dev.fitbit.com)
   - Sign in and click "Manage" → "Register An App"
   - **Application Name**: Choose any name (e.g., "My Fitbit Exporter")  
   - **OAuth 2.0 Application Type**: Select **"Personal"** (Important!)
   - **Redirect URL**: Enter exactly: `http://localhost:8080/callback`
   - Save your **Client ID** and **Client Secret**

2. **Sync via API**:
   - Run the app and enter your credentials
   - Click "Authorize with Fitbit" (opens browser)
   - Select date range and data types
   - Click "Sync via API" (may take hours for large date ranges)

### Quick Start

1. **Download**: Get the latest release for your platform from [Releases](../../releases)
2. **Run**: Double-click the executable (no installation required)
3. **Choose method**: Google Takeout (fast) or API sync (slow but real-time)

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

### Prerequisites

- Go 1.21 or later
- Fitbit Developer Account (for API credentials)

### Building from Source

```bash
git clone https://github.com/yourusername/fitbitImporter.git
cd fitbitImporter
go mod tidy
go build -o fitbit-importer
```

### Troubleshooting

**Common Issues:**

- **"Invalid redirect_uri" error**: Make sure the Redirect URL in your Fitbit app settings is exactly `http://localhost:8080/callback`
- **"Unauthorized" error**: Your app must be set to "Personal" type for intraday data access
- **Rate limit exceeded**: The app handles this automatically, but large date ranges may take time
- **No data appearing**: Some data types require specific Fitbit devices (e.g., SpO2 requires newer devices)

### Building from Source

If you want to build from source instead of using pre-built binaries:

```bash
# Install dependencies (Ubuntu/Debian)
sudo ./install-dependencies.sh

# Build the application
go build -o fitbit-importer cmd/main.go

# Run
./fitbit-importer
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This tool is not affiliated with Fitbit Inc. Use at your own risk. Always keep backups of important data.

## Support

- **Issues**: Report bugs and request features via [GitHub Issues](../../issues)
- **Documentation**: See [docs/](docs/) for detailed guides
- **API Rate Limits**: The tool automatically handles Fitbit's rate limits, but large historical imports may take several hours

---

*Your data belongs to you. Take control of it.*