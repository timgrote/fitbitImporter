package takeout

import "time"

// Google Takeout JSON structures
type HeartRateJSON struct {
	DateTime time.Time `json:"dateTime"`
	Value    struct {
		Bpm        int `json:"bpm"`
		Confidence int `json:"confidence"`
	} `json:"value"`
}

type SleepJSON struct {
	DateOfSleep time.Time `json:"dateOfSleep"`
	StartTime   time.Time `json:"startTime"`
	EndTime     time.Time `json:"endTime"`
	Duration    int       `json:"duration"`
	MinutesAsleep int     `json:"minutesAsleep"`
	MinutesAwake  int      `json:"minutesAwake"`
	Efficiency    int      `json:"efficiency"`
	Type          string   `json:"type"`
	InfoCode      int      `json:"infoCode"`
	Levels        struct {
		Summary struct {
			Deep struct {
				Count   int `json:"count"`
				Minutes int `json:"minutes"`
			} `json:"deep"`
			Light struct {
				Count   int `json:"count"`
				Minutes int `json:"minutes"`
			} `json:"light"`
			Rem struct {
				Count   int `json:"count"`
				Minutes int `json:"minutes"`
			} `json:"rem"`
			Wake struct {
				Count   int `json:"count"`
				Minutes int `json:"minutes"`
			} `json:"wake"`
		} `json:"summary"`
		Data []struct {
			DateTime time.Time `json:"dateTime"`
			Level    string    `json:"level"`
			Seconds  int       `json:"seconds"`
		} `json:"data"`
	} `json:"levels"`
}

type StepsJSON struct {
	DateTime time.Time `json:"dateTime"`
	Value    int       `json:"value"`
}

type ActivityJSON struct {
	Date              string  `json:"date"`
	Steps             int     `json:"steps"`
	Distance          float64 `json:"distance"`
	Floors            int     `json:"floors"`
	Elevation         float64 `json:"elevation"`
	CaloriesOut       int     `json:"caloriesOut"`
	ActivityCalories  int     `json:"activityCalories"`
	SedentaryMinutes  int     `json:"sedentaryMinutes"`
	LightlyActiveMinutes int  `json:"lightlyActiveMinutes"`
	FairlyActiveMinutes  int  `json:"fairlyActiveMinutes"`
	VeryActiveMinutes    int  `json:"veryActiveMinutes"`
}

// Processing results
type ImportStats struct {
	FilesProcessed   int
	RecordsImported  int
	ErrorCount       int
	StartDate        time.Time
	EndDate          time.Time
	DataTypes        map[string]int
	ProcessingTime   time.Duration
}