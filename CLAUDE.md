# Claude Development Notes

This file contains development commands and project context for Claude Code sessions.

## Project Overview

**Goal**: Create a cross-platform Fitbit data export tool that downloads personal health data to CSV files for AI analysis.

**Tech Stack**: Go with simple GUI (Fyne or Wails) for cross-platform distribution

**Target Users**: Individuals who want to analyze their Fitbit data with AI tools (Claude, ChatGPT, custom solutions)

## Key Design Decisions

- **No analysis features**: Focus purely on data export, let users choose their AI tools
- **CSV output**: Human-readable format perfect for AI ingestion  
- **Cross-platform executable**: Single binary distribution, no dependencies
- **Personal API access**: Uses Fitbit's personal app classification for immediate intraday data access
- **Local storage only**: No cloud services, complete privacy

## Development Commands

### Initial Setup
```bash
# Initialize Go module
go mod init github.com/yourusername/fitbitImporter

# Install dependencies (when added)
go mod tidy

# Build for current platform  
go build -o fitbit-importer

# Build for all platforms
GOOS=windows GOARCH=amd64 go build -o dist/fitbit-importer-windows.exe
GOOS=darwin GOARCH=amd64 go build -o dist/fitbit-importer-macos
GOOS=linux GOARCH=amd64 go build -o dist/fitbit-importer-linux
```

### Testing
```bash
# Run tests
go test ./...

# Run with race detection
go test -race ./...

# Test with coverage
go test -cover ./...
```

### Code Quality
```bash
# Format code
go fmt ./...

# Lint code (requires golangci-lint)
golangci-lint run

# Vet code
go vet ./...
```

## Project Structure (Planned)

```
fitbitImporter/
├── cmd/
│   └── main.go              # Entry point
├── internal/
│   ├── api/
│   │   ├── client.go        # Fitbit API client
│   │   ├── auth.go          # OAuth2 authentication
│   │   └── endpoints.go     # API endpoint definitions
│   ├── data/
│   │   ├── exporter.go      # CSV export logic
│   │   ├── models.go        # Data structures
│   │   └── storage.go       # File system operations
│   ├── gui/
│   │   ├── app.go           # GUI application
│   │   └── components.go    # UI components
│   └── config/
│       └── config.go        # Configuration management
├── docs/
│   └── setup.md             # Setup instructions
├── README.md
├── CLAUDE.md               # This file
├── .gitignore
├── go.mod
└── go.sum
```

## Fitbit API Context

**Authentication**: OAuth2 with Personal App classification
**Rate Limits**: 150 requests/hour per user
**Key Endpoints**:
- Heart Rate Intraday: `/1/user/-/activities/heart/date/[date]/1d/1min.json`
- Sleep: `/1.2/user/-/sleep/date/[date].json`
- Activity: `/1/user/-/activities/date/[date].json`

**Data Granularity**: Most metrics available at 1-minute intervals

## Next Development Steps

1. Initialize Go module and basic project structure
2. Implement Fitbit OAuth2 authentication flow
3. Create API client with rate limiting
4. Build CSV export functionality
5. Design simple GUI for configuration
6. Add incremental sync capabilities
7. Cross-platform build pipeline

## Dependencies (to be added)

```go
// Core dependencies
"golang.org/x/oauth2"           // OAuth2 authentication
"github.com/spf13/cobra"        // CLI framework (if CLI mode)
"github.com/spf13/viper"        // Configuration management

// GUI framework (choose one)
"fyne.io/fyne/v2"              // Native-looking GUI
// OR
"github.com/wailsapp/wails/v2" // Web-based GUI

// Utilities
"github.com/go-resty/resty/v2"  // HTTP client
"encoding/csv"                  // Built-in CSV support
"time"                         // Built-in time handling
```

## Configuration Format

```json
{
  "fitbit": {
    "client_id": "FITBIT_CLIENT_ID",
    "client_secret": "FITBIT_CLIENT_SECRET",
    "redirect_uri": "http://localhost:8080/callback"
  },
  "storage": {
    "data_directory": "./data",
    "export_directory": "./exports"
  },
  "sync": {
    "data_types": ["heart_rate", "sleep", "activity", "steps"],
    "start_date": "2024-01-01",
    "auto_sync": false
  }
}
```

## Build & Release Process

1. **Development**: `go run cmd/main.go`
2. **Testing**: Full test suite with mock API responses
3. **Building**: Cross-platform binaries for releases
4. **Distribution**: GitHub releases with pre-built executables

## Notes for Future Sessions

- Focus on simplicity and reliability over features
- Ensure robust error handling for API failures
- Make the tool resumable for large historical imports
- Keep GUI minimal - just credentials, paths, and sync button
- Consider adding progress indicators for long-running operations