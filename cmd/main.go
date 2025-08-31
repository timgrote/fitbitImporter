package main

import (
	"log"
	"github.com/fitbitImporter/fitbitImporter/internal/gui"
)

func main() {
	app, err := gui.NewApp()
	if err != nil {
		log.Fatal("Failed to create application:", err)
	}
	
	app.Run()
}