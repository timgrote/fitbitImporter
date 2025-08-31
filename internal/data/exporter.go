package data

import (
	"encoding/csv"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	
	"github.com/fitbitImporter/fitbitImporter/internal/api"
)

type Exporter struct {
	exportDir string
}

func NewExporter(exportDir string) (*Exporter, error) {
	if err := os.MkdirAll(exportDir, 0755); err != nil {
		return nil, err
	}
	
	return &Exporter{
		exportDir: exportDir,
	}, nil
}

func (e *Exporter) GetExportDir() string {
	return e.exportDir
}

func (e *Exporter) ExportHeartRate(date string, data *api.HeartRateData) error {
	filename := filepath.Join(e.exportDir, fmt.Sprintf("heart_rate_%s.csv", date))
	file, err := os.Create(filename)
	if err != nil {
		return err
	}
	defer file.Close()
	
	writer := csv.NewWriter(file)
	defer writer.Flush()
	
	// Write header
	header := []string{"Date", "Time", "HeartRate", "RestingHR"}
	if err := writer.Write(header); err != nil {
		return err
	}
	
	// Get resting heart rate for the day
	restingHR := 0
	if len(data.ActivitiesHeart) > 0 {
		restingHR = data.ActivitiesHeart[0].Value.RestingHeartRate
	}
	
	// Write intraday data
	for _, point := range data.ActivitiesHeartIntraday.Dataset {
		record := []string{
			date,
			point.Time,
			strconv.Itoa(point.Value),
			strconv.Itoa(restingHR),
		}
		if err := writer.Write(record); err != nil {
			return err
		}
	}
	
	return nil
}

func (e *Exporter) ExportSleep(date string, data *api.SleepData) error {
	filename := filepath.Join(e.exportDir, fmt.Sprintf("sleep_%s.csv", date))
	file, err := os.Create(filename)
	if err != nil {
		return err
	}
	defer file.Close()
	
	writer := csv.NewWriter(file)
	defer writer.Flush()
	
	// Write header
	header := []string{"Date", "StartTime", "EndTime", "MinutesAsleep", "MinutesAwake", 
		"MinutesDeep", "MinutesLight", "MinutesREM", "MinutesWake", "Efficiency"}
	if err := writer.Write(header); err != nil {
		return err
	}
	
	// Write sleep records
	for _, sleep := range data.Sleep {
		if !sleep.IsMainSleep {
			continue
		}
		
		record := []string{
			sleep.DateOfSleep,
			sleep.StartTime.Format("15:04:05"),
			sleep.EndTime.Format("15:04:05"),
			strconv.Itoa(sleep.MinutesAsleep),
			strconv.Itoa(sleep.MinutesAwake),
			strconv.Itoa(data.Summary.Stages.Deep),
			strconv.Itoa(data.Summary.Stages.Light),
			strconv.Itoa(data.Summary.Stages.Rem),
			strconv.Itoa(data.Summary.Stages.Wake),
			strconv.Itoa(sleep.Efficiency),
		}
		if err := writer.Write(record); err != nil {
			return err
		}
	}
	
	return nil
}

func (e *Exporter) ExportActivity(date string, data *api.ActivityData) error {
	filename := filepath.Join(e.exportDir, fmt.Sprintf("activity_%s.csv", date))
	file, err := os.Create(filename)
	if err != nil {
		return err
	}
	defer file.Close()
	
	writer := csv.NewWriter(file)
	defer writer.Flush()
	
	// Write header
	header := []string{"Date", "Steps", "Distance", "Floors", "CaloriesOut", 
		"ActiveMinutes", "SedentaryMinutes", "FairlyActiveMinutes", "VeryActiveMinutes"}
	if err := writer.Write(header); err != nil {
		return err
	}
	
	// Calculate total active minutes
	activeMinutes := data.Summary.FairlyActiveMinutes + data.Summary.VeryActiveMinutes
	
	// Calculate total distance
	totalDistance := 0.0
	for _, d := range data.Summary.Distances {
		if d.Activity == "total" {
			totalDistance = d.Distance
			break
		}
	}
	
	record := []string{
		date,
		strconv.Itoa(data.Summary.Steps),
		fmt.Sprintf("%.2f", totalDistance),
		strconv.Itoa(data.Summary.Floors),
		strconv.Itoa(data.Summary.CaloriesOut),
		strconv.Itoa(activeMinutes),
		strconv.Itoa(data.Summary.SedentaryMinutes),
		strconv.Itoa(data.Summary.FairlyActiveMinutes),
		strconv.Itoa(data.Summary.VeryActiveMinutes),
	}
	if err := writer.Write(record); err != nil {
		return err
	}
	
	return nil
}

func (e *Exporter) ExportSteps(date string, data *api.StepsData) error {
	filename := filepath.Join(e.exportDir, fmt.Sprintf("steps_intraday_%s.csv", date))
	file, err := os.Create(filename)
	if err != nil {
		return err
	}
	defer file.Close()
	
	writer := csv.NewWriter(file)
	defer writer.Flush()
	
	// Write header
	header := []string{"Date", "Time", "Steps"}
	if err := writer.Write(header); err != nil {
		return err
	}
	
	// Write intraday steps data
	for _, point := range data.ActivitiesStepsIntraday.Dataset {
		record := []string{
			date,
			point.Time,
			strconv.Itoa(point.Value),
		}
		if err := writer.Write(record); err != nil {
			return err
		}
	}
	
	return nil
}