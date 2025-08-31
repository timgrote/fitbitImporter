package config

import (
	"encoding/json"
	"os"
	"path/filepath"
)

type Config struct {
	Fitbit  FitbitConfig  `json:"fitbit"`
	Storage StorageConfig `json:"storage"`
	Sync    SyncConfig    `json:"sync"`
}

type FitbitConfig struct {
	ClientID     string `json:"client_id"`
	ClientSecret string `json:"client_secret"`
	RedirectURI  string `json:"redirect_uri"`
	AccessToken  string `json:"access_token,omitempty"`
	RefreshToken string `json:"refresh_token,omitempty"`
}

type StorageConfig struct {
	DataDirectory   string `json:"data_directory"`
	ExportDirectory string `json:"export_directory"`
}

type SyncConfig struct {
	DataTypes []string `json:"data_types"`
	StartDate string   `json:"start_date"`
	AutoSync  bool     `json:"auto_sync"`
}

func DefaultConfig() *Config {
	homeDir, _ := os.UserHomeDir()
	return &Config{
		Fitbit: FitbitConfig{
			RedirectURI: "http://localhost:8080/callback",
		},
		Storage: StorageConfig{
			DataDirectory:   filepath.Join(homeDir, "FitbitData", "data"),
			ExportDirectory: filepath.Join(homeDir, "FitbitData", "exports"),
		},
		Sync: SyncConfig{
			DataTypes: []string{"heart_rate", "sleep", "activity", "steps"},
			StartDate: "2024-01-01",
			AutoSync:  false,
		},
	}
}

func LoadConfig(path string) (*Config, error) {
	config := DefaultConfig()
	
	data, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return config, nil
		}
		return nil, err
	}
	
	if err := json.Unmarshal(data, config); err != nil {
		return nil, err
	}
	
	return config, nil
}

func (c *Config) Save(path string) error {
	data, err := json.MarshalIndent(c, "", "  ")
	if err != nil {
		return err
	}
	
	dir := filepath.Dir(path)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return err
	}
	
	return os.WriteFile(path, data, 0600)
}