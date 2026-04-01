package indexing

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"time"
)

// GoogleIndexingPayload represents the structure for Google Indexing API
type GoogleIndexingPayload struct {
	URL  string `json:"url"`
	Type string `json:"type"` // URL_UPDATED or URL_DELETED
}

// IndexingService handles communication with Google Search Console
type IndexingService struct {
	AccessToken string
}

// NotifyUrlChange sends a POST request to Google Indexing API
// T=0.8 - BoosterMode: Fast Indexing for Profit Singularity (9)
func (s *IndexingService) NotifyUrlChange(targetUrl string) error {
	const googleEndpoint = "https://indexing.googleapis.com/v3/urlNotifications:publish"

	payload := GoogleIndexingPayload{
		URL:  targetUrl,
		Type: "URL_UPDATED",
	}

	jsonData, err := json.Marshal(payload)
	if err != nil {
		return err
	}

	req, err := http.NewRequest("POST", googleEndpoint, bytes.NewBuffer(jsonData))
	if err != nil {
		return err
	}

	req.Header.Set("Content-Type", "application/json")
	if s.AccessToken != "" {
		req.Header.Set("Authorization", "Bearer "+s.AccessToken)
	}

	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("Google API returned status: %d", resp.StatusCode)
	}

	return nil
}
