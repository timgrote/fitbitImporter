# Claude Development Notes

This file contains development commands and project context for Claude Code sessions.

## Project Overview

**Goal**: Create a Python-based Fitbit data export tool that downloads personal health data to CSV files for AI analysis.

**Tech Stack**: Python with myfitbit library, optional GUI with tkinter or web interface

**Target Users**: Individuals who want to analyze their Fitbit data with AI tools (Claude, ChatGPT, custom solutions)

## Key Design Decisions

- **Python-based**: Leverage mature ecosystem, avoid compilation issues
- **Build on existing libraries**: Use myfitbit and python-fitbit as foundation
- **No analysis features**: Focus purely on data export, let users choose their AI tools
- **CSV output**: Human-readable format perfect for AI ingestion  
- **Cross-platform**: Python runs everywhere, optional PyInstaller for executables
- **Personal API access**: Uses Fitbit's personal app classification for immediate intraday data access
- **Local storage only**: No cloud services, complete privacy

## Why We Switched from Go to Python

See [docs/go-approach-summary.md](docs/go-approach-summary.md) for details. Summary:
- Go + Fyne GUI had complex CGO cross-compilation issues
- Python has mature Fitbit libraries already solving our exact problem
- No compilation needed = simpler distribution and development
- Better for data processing with pandas integration

## Environment Setup

### Setup Python Environment (Fresh WSL/Ubuntu)
```bash
# Install Python and pip (run this on fresh WSL/Ubuntu instances)
sudo apt update
sudo apt install python3 python3-pip python3-venv -y

# Check Python version (need 3.8+)
python --version
python3 --version

# Check pip
pip --version
pip3 --version

# Check virtual environment
which python  # Should show venv path when activated
echo $VIRTUAL_ENV  # Shows current venv path

# System info
uname -a  # OS info
lsb_release -a  # Ubuntu/Debian version
```

## Development Commands

### Initial Setup
```bash
# Install Python and pip (WSL/Ubuntu/Debian)
sudo apt update
sudo apt install python3 python3-pip python3-venv -y

# Verify installation
python3 --version
pip3 --version

# Clone repository
git clone https://github.com/yourusername/fitbitImporter.git
cd fitbitImporter

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

### Using myfitbit (Core Library)
```bash
# Install myfitbit
pip install myfitbit

# Create config file (myfitbit.ini)
cat > myfitbit.ini << EOF
[fitbit]
client_id = YOUR_CLIENT_ID
client_secret = YOUR_CLIENT_SECRET
EOF

# Export data
python -m myfitbit

# Generate HTML report
python -m myfitbit.report

# With debug output
python -m myfitbit --debug
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=fitbit_importer

# Run specific test file
pytest tests/test_export.py

# Run with verbose output
pytest -v

# Run with debug output
pytest -s
```

### Code Quality
```bash
# Format code with black
black .

# Sort imports
isort .

# Lint with flake8
flake8 .

# Type checking with mypy
mypy .

# All quality checks
black . && isort . && flake8 . && mypy .
```

### Building Executables
```bash
# Install PyInstaller
pip install pyinstaller

# Build single-file executable
pyinstaller --onefile --name fitbit-importer main.py

# Build with custom icon (Windows)
pyinstaller --onefile --icon=icon.ico --name fitbit-importer main.py

# Build for different platforms (must run on target OS)
# Linux
pyinstaller --onefile --name fitbit-importer-linux main.py

# Windows (run on Windows)
pyinstaller --onefile --name fitbit-importer.exe main.py

# macOS (run on macOS)
pyinstaller --onefile --name fitbit-importer-macos main.py
```

## Project Structure

```
fitbitImporter/
├── fitbit_importer/
│   ├── __init__.py          # Package initialization
│   ├── main.py              # Entry point
│   ├── export.py            # Enhanced export functionality
│   ├── config.py            # Configuration management
│   ├── gui.py               # Optional GUI (tkinter)
│   └── utils.py             # Utility functions
├── tests/
│   ├── __init__.py
│   ├── test_export.py
│   ├── test_config.py
│   └── fixtures/            # Test data
├── docs/
│   ├── setup.md             # Setup instructions
│   └── go-approach-summary.md # Why we switched from Go
├── requirements.txt         # Production dependencies
├── requirements-dev.txt     # Development dependencies
├── setup.py                 # Package setup
├── README.md
├── CLAUDE.md               # This file
├── .gitignore
├── myfitbit.ini            # Fitbit API credentials (git-ignored)
└── .env                    # Environment variables (git-ignored)
```

## Fitbit API Context

**Authentication**: OAuth2 with Personal App classification
**Rate Limits**: 150 requests/hour per user
**Redirect URL**: `http://localhost:8189/auth_code` (myfitbit default)
**Key Endpoints**:
- Heart Rate Intraday: `/1/user/-/activities/heart/date/[date]/1d/1min.json`
- Sleep: `/1.2/user/-/sleep/date/[date].json`
- Activity: `/1/user/-/activities/date/[date].json`

**Data Granularity**: Most metrics available at 1-minute intervals

## Python Dependencies

### Core Dependencies (requirements.txt)
```txt
myfitbit>=1.0.0          # Core Fitbit export library
python-fitbit>=0.3.0     # Fitbit API client
pandas>=1.3.0            # Data processing
requests-oauthlib>=1.3.0 # OAuth2 support
python-dateutil>=2.8.0   # Date handling
click>=8.0.0             # CLI framework
python-dotenv>=0.19.0    # Environment variables
```

### Development Dependencies (requirements-dev.txt)
```txt
pytest>=7.0.0            # Testing framework
pytest-cov>=3.0.0        # Coverage reporting
black>=22.0.0            # Code formatter
isort>=5.10.0            # Import sorting
flake8>=4.0.0            # Linting
mypy>=0.950              # Type checking
pyinstaller>=5.0.0       # Executable building
```

### Optional GUI Dependencies
```txt
tkinter                  # Built-in with Python
# OR
flask>=2.0.0             # Web-based GUI
```

## Configuration Format

### myfitbit.ini (Required)
```ini
[fitbit]
client_id = YOUR_CLIENT_ID
client_secret = YOUR_CLIENT_SECRET
```

### config.json (Optional, for our enhancements)
```json
{
  "storage": {
    "data_directory": "./data",
    "export_directory": "./exports"
  },
  "sync": {
    "data_types": ["heart_rate", "sleep", "activity", "steps"],
    "start_date": "2024-01-01",
    "end_date": null,
    "auto_resume": true
  },
  "export": {
    "format": "csv",
    "include_raw": false,
    "compress": false
  }
}
```

## Development Workflow

1. **Setup**: Create venv, install dependencies
2. **Test myfitbit**: Verify basic export works
3. **Enhance**: Add our custom features on top
4. **Test**: Run pytest suite
5. **Build**: Create executable with PyInstaller
6. **Release**: Upload to GitHub releases

## Handling Rate Limits

myfitbit handles this automatically, but for reference:
- Fitbit allows 150 requests/hour
- 1 day of heart rate = 1 request
- Large exports may take hours
- Tool automatically resumes if interrupted
- HTTP 429 errors are normal and handled

## GitHub Actions for Python

```yaml
name: Python CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, '3.10', 3.11]
    
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    - name: Run tests
      run: pytest
    - name: Check code quality
      run: |
        black --check .
        flake8 .
```

## Notes for Future Sessions

- Start by testing myfitbit as-is to understand its capabilities
- Focus on enhancements that myfitbit doesn't provide
- Consider adding Google Takeout import as a faster alternative
- Keep the tool simple - resist feature creep
- Document any Fitbit API quirks discovered
- Consider rate limit warnings for large date ranges
- Test with different Fitbit device types (some don't have all metrics)