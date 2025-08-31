package api

import "time"

// API Response Models
type HeartRateData struct {
	ActivitiesHeart []struct {
		DateTime string `json:"dateTime"`
		Value    struct {
			CustomHeartRateZones []interface{} `json:"customHeartRateZones"`
			HeartRateZones       []struct {
				CaloriesOut float64 `json:"caloriesOut"`
				Max         int     `json:"max"`
				Min         int     `json:"min"`
				Minutes     int     `json:"minutes"`
				Name        string  `json:"name"`
			} `json:"heartRateZones"`
			RestingHeartRate int `json:"restingHeartRate"`
		} `json:"value"`
	} `json:"activities-heart"`
	ActivitiesHeartIntraday struct {
		Dataset []struct {
			Time  string `json:"time"`
			Value int    `json:"value"`
		} `json:"dataset"`
		DatasetInterval int    `json:"datasetInterval"`
		DatasetType     string `json:"datasetType"`
	} `json:"activities-heart-intraday"`
}

type SleepData struct {
	Sleep []struct {
		DateOfSleep         string    `json:"dateOfSleep"`
		Duration            int       `json:"duration"`
		Efficiency          int       `json:"efficiency"`
		EndTime             time.Time `json:"endTime"`
		InfoCode            int       `json:"infoCode"`
		IsMainSleep         bool      `json:"isMainSleep"`
		LogId               int64     `json:"logId"`
		MinutesAfterWakeup  int       `json:"minutesAfterWakeup"`
		MinutesAsleep       int       `json:"minutesAsleep"`
		MinutesAwake        int       `json:"minutesAwake"`
		MinutesToFallAsleep int       `json:"minutesToFallAsleep"`
		StartTime           time.Time `json:"startTime"`
		TimeInBed           int       `json:"timeInBed"`
		Type                string    `json:"type"`
	} `json:"sleep"`
	Summary struct {
		Stages struct {
			Deep  int `json:"deep"`
			Light int `json:"light"`
			Rem   int `json:"rem"`
			Wake  int `json:"wake"`
		} `json:"stages"`
		TotalMinutesAsleep int `json:"totalMinutesAsleep"`
		TotalSleepRecords  int `json:"totalSleepRecords"`
		TotalTimeInBed     int `json:"totalTimeInBed"`
	} `json:"summary"`
}

type ActivityData struct {
	Activities []struct {
		ActivityId       int     `json:"activityId"`
		ActivityParentId int     `json:"activityParentId"`
		Calories         int     `json:"calories"`
		Description      string  `json:"description"`
		Distance         float64 `json:"distance"`
		Duration         int     `json:"duration"`
		HasStartTime     bool    `json:"hasStartTime"`
		IsFavorite       bool    `json:"isFavorite"`
		LogId            int64   `json:"logId"`
		Name             string  `json:"name"`
		StartTime        string  `json:"startTime"`
		Steps            int     `json:"steps"`
	} `json:"activities"`
	Summary struct {
		ActiveScore          int     `json:"activeScore"`
		ActivityCalories     int     `json:"activityCalories"`
		CaloriesBMR          int     `json:"caloriesBMR"`
		CaloriesOut          int     `json:"caloriesOut"`
		Distances            []Distance `json:"distances"`
		Elevation            float64 `json:"elevation"`
		FairlyActiveMinutes  int     `json:"fairlyActiveMinutes"`
		Floors               int     `json:"floors"`
		LightlyActiveMinutes int     `json:"lightlyActiveMinutes"`
		MarginalCalories     int     `json:"marginalCalories"`
		RestingHeartRate     int     `json:"restingHeartRate"`
		SedentaryMinutes     int     `json:"sedentaryMinutes"`
		Steps                int     `json:"steps"`
		VeryActiveMinutes    int     `json:"veryActiveMinutes"`
	} `json:"summary"`
}

type Distance struct {
	Activity string  `json:"activity"`
	Distance float64 `json:"distance"`
}

type StepsData struct {
	ActivitiesSteps []struct {
		DateTime string `json:"dateTime"`
		Value    string `json:"value"`
	} `json:"activities-steps"`
	ActivitiesStepsIntraday struct {
		Dataset []struct {
			Time  string `json:"time"`
			Value int    `json:"value"`
		} `json:"dataset"`
		DatasetInterval int    `json:"datasetInterval"`
		DatasetType     string `json:"datasetType"`
	} `json:"activities-steps-intraday"`
}