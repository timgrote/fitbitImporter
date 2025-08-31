package takeout

import (
	"archive/zip"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"time"
	
	"github.com/fitbitImporter/fitbitImporter/internal/data"
)

type Parser struct {
	exporter *data.Exporter
	stats    *ImportStats
}

func NewParser(exportDir string) (*Parser, error) {
	exporter, err := data.NewExporter(exportDir)
	if err != nil {
		return nil, err
	}
	
	return &Parser{
		exporter: exporter,
		stats: &ImportStats{
			DataTypes: make(map[string]int),
		},
	}, nil
}

func (p *Parser) ParseTakeoutZip(zipPath string, progressCallback func(msg string, percent float64)) error {
	startTime := time.Now()
	p.stats.ProcessingTime = time.Since(startTime)
	
	reader, err := zip.OpenReader(zipPath)
	if err != nil {
		return fmt.Errorf("failed to open zip: %w", err)
	}
	defer reader.Close()
	
	totalFiles := len(reader.File)
	processed := 0
	
	// Map to store data by date for batch processing
	heartRateByDate := make(map[string][]HeartRateJSON)
	sleepByDate := make(map[string][]SleepJSON)
	stepsByDate := make(map[string][]StepsJSON)
	
	progressCallback("Scanning files...", 0)
	
	for _, file := range reader.File {
		processed++
		percent := float64(processed) / float64(totalFiles) * 50 // First 50% for scanning
		
		// Skip directories
		if file.FileInfo().IsDir() {
			continue
		}
		
		fileName := filepath.Base(file.Name)
		
		// Process based on file patterns
		switch {
		case strings.HasPrefix(fileName, "heart_rate-") && strings.HasSuffix(fileName, ".json"):
			if err := p.parseHeartRateFile(file, heartRateByDate); err != nil {
				p.stats.ErrorCount++
				fmt.Printf("Error parsing %s: %v\n", fileName, err)
			} else {
				p.stats.DataTypes["heart_rate"]++
			}
			progressCallback(fmt.Sprintf("Processing heart rate: %s", fileName), percent)
			
		case strings.HasPrefix(fileName, "sleep-") && strings.HasSuffix(fileName, ".json"):
			if err := p.parseSleepFile(file, sleepByDate); err != nil {
				p.stats.ErrorCount++
				fmt.Printf("Error parsing %s: %v\n", fileName, err)
			} else {
				p.stats.DataTypes["sleep"]++
			}
			progressCallback(fmt.Sprintf("Processing sleep: %s", fileName), percent)
			
		case strings.HasPrefix(fileName, "steps-") && strings.HasSuffix(fileName, ".json"):
			if err := p.parseStepsFile(file, stepsByDate); err != nil {
				p.stats.ErrorCount++
				fmt.Printf("Error parsing %s: %v\n", fileName, err)
			} else {
				p.stats.DataTypes["steps"]++
			}
			progressCallback(fmt.Sprintf("Processing steps: %s", fileName), percent)
			
		case strings.Contains(file.Name, "Physical Activity") && strings.HasSuffix(fileName, ".csv"):
			// Handle activity CSV files from Google Takeout
			p.stats.DataTypes["activity"]++
			progressCallback(fmt.Sprintf("Processing activity: %s", fileName), percent)
		}
		
		p.stats.FilesProcessed++
	}
	
	// Export collected data to CSV files
	progressCallback("Exporting to CSV files...", 60)
	
	// Export heart rate data
	exportCount := 0
	totalExports := len(heartRateByDate) + len(sleepByDate) + len(stepsByDate)
	
	for date, records := range heartRateByDate {
		if err := p.exportHeartRateCSV(date, records); err != nil {
			p.stats.ErrorCount++
			fmt.Printf("Error exporting heart rate for %s: %v\n", date, err)
		}
		exportCount++
		percent := 60 + (float64(exportCount)/float64(totalExports))*40
		progressCallback(fmt.Sprintf("Exporting heart rate: %s", date), percent)
	}
	
	// Export sleep data
	for date, records := range sleepByDate {
		if err := p.exportSleepCSV(date, records); err != nil {
			p.stats.ErrorCount++
			fmt.Printf("Error exporting sleep for %s: %v\n", date, err)
		}
		exportCount++
		percent := 60 + (float64(exportCount)/float64(totalExports))*40
		progressCallback(fmt.Sprintf("Exporting sleep: %s", date), percent)
	}
	
	// Export steps data
	for date, records := range stepsByDate {
		if err := p.exportStepsCSV(date, records); err != nil {
			p.stats.ErrorCount++
			fmt.Printf("Error exporting steps for %s: %v\n", date, err)
		}
		exportCount++
		percent := 60 + (float64(exportCount)/float64(totalExports))*40
		progressCallback(fmt.Sprintf("Exporting steps: %s", date), percent)
	}
	
	p.stats.ProcessingTime = time.Since(startTime)
	progressCallback("Import complete!", 100)
	
	return nil
}

func (p *Parser) parseHeartRateFile(file *zip.File, dataMap map[string][]HeartRateJSON) error {
	// Extract date from filename (heart_rate-2024-01-15.json)
	re := regexp.MustCompile(`heart_rate-(\d{4}-\d{2}-\d{2})\.json`)
	matches := re.FindStringSubmatch(file.Name)
	if len(matches) < 2 {
		return fmt.Errorf("could not extract date from filename: %s", file.Name)
	}
	date := matches[1]
	
	rc, err := file.Open()
	if err != nil {
		return err
	}
	defer rc.Close()
	
	data, err := io.ReadAll(rc)
	if err != nil {
		return err
	}
	
	var records []HeartRateJSON
	if err := json.Unmarshal(data, &records); err != nil {
		return err
	}
	
	dataMap[date] = append(dataMap[date], records...)
	p.stats.RecordsImported += len(records)
	
	// Update date range
	for _, record := range records {
		if p.stats.StartDate.IsZero() || record.DateTime.Before(p.stats.StartDate) {
			p.stats.StartDate = record.DateTime
		}
		if record.DateTime.After(p.stats.EndDate) {
			p.stats.EndDate = record.DateTime
		}
	}
	
	return nil
}

func (p *Parser) parseSleepFile(file *zip.File, dataMap map[string][]SleepJSON) error {
	// Extract date from filename
	re := regexp.MustCompile(`sleep-(\d{4}-\d{2}-\d{2})\.json`)
	matches := re.FindStringSubmatch(file.Name)
	if len(matches) < 2 {
		return fmt.Errorf("could not extract date from filename: %s", file.Name)
	}
	date := matches[1]
	
	rc, err := file.Open()
	if err != nil {
		return err
	}
	defer rc.Close()
	
	data, err := io.ReadAll(rc)
	if err != nil {
		return err
	}
	
	var records []SleepJSON
	if err := json.Unmarshal(data, &records); err != nil {
		// Try single record
		var record SleepJSON
		if err := json.Unmarshal(data, &record); err != nil {
			return err
		}
		records = []SleepJSON{record}
	}
	
	dataMap[date] = append(dataMap[date], records...)
	p.stats.RecordsImported += len(records)
	
	return nil
}

func (p *Parser) parseStepsFile(file *zip.File, dataMap map[string][]StepsJSON) error {
	// Extract date from filename
	re := regexp.MustCompile(`steps-(\d{4}-\d{2}-\d{2})\.json`)
	matches := re.FindStringSubmatch(file.Name)
	if len(matches) < 2 {
		return fmt.Errorf("could not extract date from filename: %s", file.Name)
	}
	date := matches[1]
	
	rc, err := file.Open()
	if err != nil {
		return err
	}
	defer rc.Close()
	
	data, err := io.ReadAll(rc)
	if err != nil {
		return err
	}
	
	var records []StepsJSON
	if err := json.Unmarshal(data, &records); err != nil {
		return err
	}
	
	dataMap[date] = append(dataMap[date], records...)
	p.stats.RecordsImported += len(records)
	
	return nil
}

func (p *Parser) exportHeartRateCSV(date string, records []HeartRateJSON) error {
	filename := filepath.Join(p.exporter.GetExportDir(), fmt.Sprintf("heart_rate_%s.csv", date))
	file, err := os.Create(filename)
	if err != nil {
		return err
	}
	defer file.Close()
	
	// Write header
	fmt.Fprintln(file, "Date,Time,HeartRate,Confidence")
	
	// Write records
	for _, record := range records {
		fmt.Fprintf(file, "%s,%s,%d,%d\n",
			record.DateTime.Format("2006-01-02"),
			record.DateTime.Format("15:04:05"),
			record.Value.Bpm,
			record.Value.Confidence,
		)
	}
	
	return nil
}

func (p *Parser) exportSleepCSV(date string, records []SleepJSON) error {
	filename := filepath.Join(p.exporter.GetExportDir(), fmt.Sprintf("sleep_%s.csv", date))
	file, err := os.Create(filename)
	if err != nil {
		return err
	}
	defer file.Close()
	
	// Write header
	fmt.Fprintln(file, "Date,StartTime,EndTime,Duration,MinutesAsleep,MinutesAwake,MinutesDeep,MinutesLight,MinutesREM,MinutesWake,Efficiency,Type")
	
	// Write records
	for _, record := range records {
		fmt.Fprintf(file, "%s,%s,%s,%d,%d,%d,%d,%d,%d,%d,%d,%s\n",
			record.DateOfSleep.Format("2006-01-02"),
			record.StartTime.Format("15:04:05"),
			record.EndTime.Format("15:04:05"),
			record.Duration,
			record.MinutesAsleep,
			record.MinutesAwake,
			record.Levels.Summary.Deep.Minutes,
			record.Levels.Summary.Light.Minutes,
			record.Levels.Summary.Rem.Minutes,
			record.Levels.Summary.Wake.Minutes,
			record.Efficiency,
			record.Type,
		)
	}
	
	return nil
}

func (p *Parser) exportStepsCSV(date string, records []StepsJSON) error {
	filename := filepath.Join(p.exporter.GetExportDir(), fmt.Sprintf("steps_%s.csv", date))
	file, err := os.Create(filename)
	if err != nil {
		return err
	}
	defer file.Close()
	
	// Write header
	fmt.Fprintln(file, "Date,Time,Steps")
	
	// Write records
	for _, record := range records {
		fmt.Fprintf(file, "%s,%s,%d\n",
			record.DateTime.Format("2006-01-02"),
			record.DateTime.Format("15:04:05"),
			record.Value,
		)
	}
	
	return nil
}

func (p *Parser) GetStats() *ImportStats {
	return p.stats
}