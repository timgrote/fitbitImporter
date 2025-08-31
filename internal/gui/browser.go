package gui

import (
	"log"
	"os/exec"
	"runtime"
)

func openBrowser(url string) {
	var err error
	
	switch runtime.GOOS {
	case "linux":
		err = exec.Command("xdg-open", url).Start()
	case "windows":
		err = exec.Command("rundll32", "url.dll,FileProtocolHandler", url).Start()
	case "darwin":
		err = exec.Command("open", url).Start()
	default:
		log.Printf("Unsupported platform. Please open manually: %s", url)
		return
	}
	
	if err != nil {
		log.Printf("Failed to open browser: %v", err)
		log.Printf("Please open manually: %s", url)
	}
}