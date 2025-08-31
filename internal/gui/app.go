package gui

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"
	
	"fyne.io/fyne/v2"
	"fyne.io/fyne/v2/app"
	"fyne.io/fyne/v2/container"
	"fyne.io/fyne/v2/dialog"
	"fyne.io/fyne/v2/layout"
	"fyne.io/fyne/v2/widget"
	"golang.org/x/oauth2"
	
	"github.com/fitbitImporter/fitbitImporter/internal/api"
	"github.com/fitbitImporter/fitbitImporter/internal/config"
	"github.com/fitbitImporter/fitbitImporter/internal/data"
	"github.com/fitbitImporter/fitbitImporter/internal/takeout"
)

type App struct {
	app         fyne.App
	window      fyne.Window
	config      *config.Config
	authManager *api.AuthManager
	client      *api.Client
	exporter    *data.Exporter
	
	// UI elements
	clientIDEntry     *widget.Entry
	clientSecretEntry *widget.Entry
	exportDirEntry    *widget.Entry
	startDateEntry    *widget.Entry
	endDateEntry      *widget.Entry
	statusLabel       *widget.Label
	progressBar       *widget.ProgressBar
	authButton        *widget.Button
	syncButton        *widget.Button
	importButton      *widget.Button
	dataTypeChecks    map[string]*widget.Check
}

func NewApp() (*App, error) {
	homeDir, _ := os.UserHomeDir()
	configPath := filepath.Join(homeDir, ".fitbitImporter", "config.json")
	
	cfg, err := config.LoadConfig(configPath)
	if err != nil {
		return nil, err
	}
	
	a := &App{
		app:    app.New(),
		config: cfg,
		dataTypeChecks: make(map[string]*widget.Check),
	}
	
	a.app.Settings().SetTheme(&fyneTheme{})
	a.setupUI()
	
	return a, nil
}

func (a *App) setupUI() {
	a.window = a.app.NewWindow("Fitbit Data Importer")
	a.window.Resize(fyne.NewSize(700, 550))
	a.window.CenterOnScreen()
	
	// Client credentials section
	a.clientIDEntry = widget.NewEntry()
	a.clientIDEntry.SetPlaceHolder("Enter Fitbit Client ID")
	a.clientIDEntry.SetText(a.config.Fitbit.ClientID)
	a.clientIDEntry.MultiLine = false
	
	// Use regular Entry instead of PasswordEntry for better clipboard support
	a.clientSecretEntry = widget.NewEntry()
	a.clientSecretEntry.SetPlaceHolder("Enter Fitbit Client Secret")
	a.clientSecretEntry.SetText(a.config.Fitbit.ClientSecret)
	a.clientSecretEntry.MultiLine = false
	
	// Add a checkbox to show/hide the secret
	showSecretCheck := widget.NewCheck("Show Secret", func(checked bool) {
		if checked {
			a.clientSecretEntry = widget.NewEntry()
			a.clientSecretEntry.SetText(a.config.Fitbit.ClientSecret)
		} else {
			a.clientSecretEntry = widget.NewPasswordEntry()
			a.clientSecretEntry.SetText(a.config.Fitbit.ClientSecret)
		}
		a.clientSecretEntry.SetPlaceHolder("Enter Fitbit Client Secret")
		a.clientSecretEntry.MultiLine = false
		a.clientSecretEntry.Refresh()
	})
	
	credentialsForm := container.New(layout.NewFormLayout(),
		widget.NewLabel("Client ID:"), a.clientIDEntry,
		widget.NewLabel("Client Secret:"), a.clientSecretEntry,
		widget.NewLabel(""), showSecretCheck,
	)
	
	// Export directory section
	a.exportDirEntry = widget.NewEntry()
	a.exportDirEntry.SetText(a.config.Storage.ExportDirectory)
	
	browseButton := widget.NewButton("Browse", func() {
		dialog.ShowFolderOpen(func(dir fyne.ListableURI, err error) {
			if err != nil || dir == nil {
				return
			}
			a.exportDirEntry.SetText(dir.Path())
		}, a.window)
	})
	
	exportDirSection := container.New(layout.NewBorderLayout(nil, nil, nil, browseButton),
		a.exportDirEntry, browseButton,
	)
	
	// Date range section
	a.startDateEntry = widget.NewEntry()
	a.startDateEntry.SetPlaceHolder("YYYY-MM-DD")
	a.startDateEntry.SetText(a.config.Sync.StartDate)
	
	a.endDateEntry = widget.NewEntry()
	a.endDateEntry.SetPlaceHolder("YYYY-MM-DD")
	a.endDateEntry.SetText(time.Now().Format("2006-01-02"))
	
	dateRangeForm := container.New(layout.NewFormLayout(),
		widget.NewLabel("Start Date:"), a.startDateEntry,
		widget.NewLabel("End Date:"), a.endDateEntry,
	)
	
	// Data type selection
	dataTypes := []string{"heart_rate", "sleep", "activity", "steps"}
	dataTypeContainer := container.New(layout.NewGridLayout(2))
	
	for _, dt := range dataTypes {
		check := widget.NewCheck(dt, nil)
		check.SetChecked(contains(a.config.Sync.DataTypes, dt))
		a.dataTypeChecks[dt] = check
		dataTypeContainer.Add(check)
	}
	
	// Status and progress
	a.statusLabel = widget.NewLabel("Ready to connect")
	a.progressBar = widget.NewProgressBar()
	
	// Action buttons
	a.authButton = widget.NewButton("Authorize with Fitbit", a.handleAuth)
	a.syncButton = widget.NewButton("Sync via API", a.handleSync)
	a.importButton = widget.NewButton("Import Google Takeout", a.handleImport)
	a.syncButton.Disable()
	
	if a.config.Fitbit.AccessToken != "" {
		a.statusLabel.SetText("Previously authorized")
		a.syncButton.Enable()
	}
	
	buttonContainer := container.New(layout.NewGridLayout(3),
		a.authButton, a.syncButton, a.importButton,
	)
	
	// Add instructions at the top
	instructions := widget.NewRichTextFromMarkdown(`
**Two ways to get your Fitbit data:**
1. **Google Takeout** (Fast): Export all data at once from Google → Import the zip file
2. **API Sync** (Slow): Real-time sync using Fitbit API credentials → May take hours for large date ranges

*Tip: Use Ctrl+V (or Cmd+V on Mac) to paste your credentials*
	`)
	instructions.Wrapping = fyne.TextWrapWord
	
	// Main layout
	content := container.NewVBox(
		instructions,
		widget.NewCard("Fitbit Credentials", "", credentialsForm),
		widget.NewCard("Export Directory", "", exportDirSection),
		widget.NewCard("Date Range", "", dateRangeForm),
		widget.NewCard("Data Types", "", dataTypeContainer),
		widget.NewSeparator(),
		buttonContainer,
		widget.NewSeparator(),
		a.statusLabel,
		a.progressBar,
	)
	
	scrollContainer := container.NewScroll(content)
	a.window.SetContent(scrollContainer)
}

func (a *App) handleAuth() {
	a.statusLabel.SetText("Authorizing...")
	
	clientID := a.clientIDEntry.Text
	clientSecret := a.clientSecretEntry.Text
	
	if clientID == "" || clientSecret == "" {
		dialog.ShowError(fmt.Errorf("Please enter Client ID and Client Secret"), a.window)
		a.statusLabel.SetText("Authorization failed")
		return
	}
	
	a.config.Fitbit.ClientID = clientID
	a.config.Fitbit.ClientSecret = clientSecret
	
	a.authManager = api.NewAuthManager(clientID, clientSecret, "http://localhost:8080/callback")
	
	// Start callback server
	if err := a.authManager.StartCallbackServer(); err != nil {
		dialog.ShowError(err, a.window)
		a.statusLabel.SetText("Failed to start callback server")
		return
	}
	
	authURL := a.authManager.GetAuthURL()
	
	// Open browser
	dialog.ShowConfirm("Authorization Required", 
		"Click OK to open your browser for Fitbit authorization", 
		func(ok bool) {
			if !ok {
				a.statusLabel.SetText("Authorization cancelled")
				return
			}
			
			// Open browser (platform-specific)
			openBrowser(authURL)
			
			go func() {
				// Wait for auth code
				code, err := a.authManager.WaitForAuthCode(5 * time.Minute)
				if err != nil {
					a.statusLabel.SetText("Authorization timeout")
					return
				}
				
				// Exchange for token
				ctx := context.Background()
				token, err := a.authManager.ExchangeCodeForToken(ctx, code)
				if err != nil {
					a.statusLabel.SetText("Failed to get access token")
					return
				}
				
				// Save token
				a.config.Fitbit.AccessToken = token.AccessToken
				a.config.Fitbit.RefreshToken = token.RefreshToken
				
				homeDir, _ := os.UserHomeDir()
				configPath := filepath.Join(homeDir, ".fitbitImporter", "config.json")
				a.config.Save(configPath)
				
				a.statusLabel.SetText("Authorization successful!")
				a.syncButton.Enable()
				
				// Stop callback server
				a.authManager.StopCallbackServer()
			}()
		}, a.window)
}

func (a *App) handleSync() {
	a.statusLabel.SetText("Syncing data...")
	a.progressBar.SetValue(0)
	a.syncButton.Disable()
	
	// Update config
	a.config.Storage.ExportDirectory = a.exportDirEntry.Text
	a.config.Sync.StartDate = a.startDateEntry.Text
	
	selectedTypes := []string{}
	for dtype, check := range a.dataTypeChecks {
		if check.Checked {
			selectedTypes = append(selectedTypes, dtype)
		}
	}
	a.config.Sync.DataTypes = selectedTypes
	
	// Save config
	homeDir, _ := os.UserHomeDir()
	configPath := filepath.Join(homeDir, ".fitbitImporter", "config.json")
	a.config.Save(configPath)
	
	// Create exporter
	var err error
	a.exporter, err = data.NewExporter(a.config.Storage.ExportDirectory)
	if err != nil {
		dialog.ShowError(err, a.window)
		a.statusLabel.SetText("Failed to create exporter")
		a.syncButton.Enable()
		return
	}
	
	// Create API client
	ctx := context.Background()
	token := &oauth2.Token{
		AccessToken:  a.config.Fitbit.AccessToken,
		RefreshToken: a.config.Fitbit.RefreshToken,
		TokenType:    "Bearer",
	}
	
	httpClient := a.authManager.GetClient(ctx, token)
	a.client = api.NewClient(httpClient, token)
	
	// Start sync in background
	go a.performSync()
}

func (a *App) performSync() {
	startDate, _ := time.Parse("2006-01-02", a.startDateEntry.Text)
	endDate, _ := time.Parse("2006-01-02", a.endDateEntry.Text)
	
	totalDays := int(endDate.Sub(startDate).Hours() / 24) + 1
	totalRequests := totalDays * len(a.config.Sync.DataTypes)
	currentRequest := 0
	
	ctx := context.Background()
	
	// Estimate time for user feedback
	estimatedMinutes := totalRequests * 24 / 60 // 24 seconds per request converted to minutes
	a.statusLabel.SetText(fmt.Sprintf("Starting sync... (estimated time: %d minutes)", estimatedMinutes))
	
	for d := startDate; !d.After(endDate); d = d.AddDate(0, 0, 1) {
		dateStr := d.Format("2006-01-02")
		
		for _, dataType := range a.config.Sync.DataTypes {
			currentRequest++
			progress := float64(currentRequest) / float64(totalRequests)
			
			// Calculate remaining time
			remainingRequests := totalRequests - currentRequest
			remainingMinutes := remainingRequests * 24 / 60
			
			a.progressBar.SetValue(progress)
			a.statusLabel.SetText(fmt.Sprintf("Syncing %s %s... (%d/%d) ~%d min remaining", 
				dateStr, dataType, currentRequest, totalRequests, remainingMinutes))
			
			switch dataType {
			case "heart_rate":
				if data, err := a.client.GetHeartRateIntraday(ctx, dateStr); err == nil {
					a.exporter.ExportHeartRate(dateStr, data)
				} else {
					fmt.Printf("Error fetching heart rate for %s: %v\n", dateStr, err)
				}
			case "sleep":
				if data, err := a.client.GetSleep(ctx, dateStr); err == nil {
					a.exporter.ExportSleep(dateStr, data)
				} else {
					fmt.Printf("Error fetching sleep for %s: %v\n", dateStr, err)
				}
			case "activity":
				if data, err := a.client.GetActivity(ctx, dateStr); err == nil {
					a.exporter.ExportActivity(dateStr, data)
				} else {
					fmt.Printf("Error fetching activity for %s: %v\n", dateStr, err)
				}
			case "steps":
				if data, err := a.client.GetSteps(ctx, dateStr); err == nil {
					a.exporter.ExportSteps(dateStr, data)
				} else {
					fmt.Printf("Error fetching steps for %s: %v\n", dateStr, err)
				}
			}
		}
	}
	
	a.statusLabel.SetText("API sync completed!")
	a.syncButton.Enable()
	
	dialog.ShowInformation("Success", 
		fmt.Sprintf("Data exported to: %s\n\nFor faster exports of historical data, consider using Google Takeout instead.", 
			a.config.Storage.ExportDirectory), 
		a.window)
}

func (a *App) handleImport() {
	a.statusLabel.SetText("Select Google Takeout zip file...")
	
	dialog.ShowFileOpen(func(reader fyne.URIReadCloser, err error) {
		if err != nil || reader == nil {
			a.statusLabel.SetText("Import cancelled")
			return
		}
		defer reader.Close()
		
		zipPath := reader.URI().Path()
		
		// Validate file extension
		if !strings.HasSuffix(strings.ToLower(zipPath), ".zip") {
			dialog.ShowError(fmt.Errorf("Please select a ZIP file"), a.window)
			a.statusLabel.SetText("Import cancelled - invalid file type")
			return
		}
		
		// Create parser
		parser, err := takeout.NewParser(a.exportDirEntry.Text)
		if err != nil {
			dialog.ShowError(err, a.window)
			a.statusLabel.SetText("Failed to create parser")
			return
		}
		
		// Disable buttons during import
		a.importButton.Disable()
		a.syncButton.Disable()
		a.authButton.Disable()
		
		// Progress callback
		progressCallback := func(msg string, percent float64) {
			a.statusLabel.SetText(msg)
			a.progressBar.SetValue(percent / 100.0)
		}
		
		// Parse in background
		go func() {
			defer func() {
				a.importButton.Enable()
				a.authButton.Enable()
				if a.config.Fitbit.AccessToken != "" {
					a.syncButton.Enable()
				}
			}()
			
			if err := parser.ParseTakeoutZip(zipPath, progressCallback); err != nil {
				a.statusLabel.SetText(fmt.Sprintf("Import failed: %v", err))
				dialog.ShowError(err, a.window)
				return
			}
			
			// Show success dialog with stats
			stats := parser.GetStats()
			message := fmt.Sprintf(`Import successful!

Files processed: %d
Records imported: %d
Errors: %d
Data types: %v
Processing time: %v
Date range: %s to %s

CSV files saved to: %s`,
				stats.FilesProcessed,
				stats.RecordsImported,
				stats.ErrorCount,
				getDataTypesList(stats.DataTypes),
				stats.ProcessingTime.Round(time.Second),
				stats.StartDate.Format("2006-01-02"),
				stats.EndDate.Format("2006-01-02"),
				a.exportDirEntry.Text)
			
			dialog.ShowInformation("Import Complete", message, a.window)
			a.statusLabel.SetText("Import completed successfully")
			a.progressBar.SetValue(0)
		}()
		
	}, a.window)
}

func getDataTypesList(dataTypes map[string]int) []string {
	var types []string
	for dtype, count := range dataTypes {
		types = append(types, fmt.Sprintf("%s (%d files)", dtype, count))
	}
	return types
}

func (a *App) Run() {
	a.window.ShowAndRun()
}

func contains(slice []string, item string) bool {
	for _, s := range slice {
		if s == item {
			return true
		}
	}
	return false
}