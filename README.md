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

## Quick Start

1. **Download**: Get the latest release for your platform from [Releases](../../releases)
2. **Run**: Double-click the executable (no installation required)
3. **Authenticate**: Log in with your Fitbit account when prompted
4. **Configure**: Choose where to save your exported data
5. **Sync**: Click "Start Export" to begin downloading your data

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

### Configuration

Create a `config.json` file with your Fitbit API credentials:

```json
{
  "client_id": "your_fitbit_client_id",
  "client_secret": "your_fitbit_client_secret",
  "data_directory": "./data",
  "export_directory": "./exports"
}
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