package data

// CSV Export Models
type HeartRateCSV struct {
	Date      string
	Time      string
	HeartRate int
	RestingHR int
}

type SleepCSV struct {
	Date              string
	StartTime         string
	EndTime           string
	MinutesAsleep     int
	MinutesAwake      int
	MinutesDeep       int
	MinutesLight      int
	MinutesREM        int
	MinutesWake       int
	Efficiency        int
}

type ActivityCSV struct {
	Date                 string
	Steps                int
	Distance             float64
	Floors               int
	CaloriesOut          int
	ActiveMinutes        int
	SedentaryMinutes     int
	FairlyActiveMinutes  int
	VeryActiveMinutes    int
}

type StepsCSV struct {
	Date  string
	Time  string
	Steps int
}