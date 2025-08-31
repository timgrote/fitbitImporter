package api

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
	
	"golang.org/x/oauth2"
	"golang.org/x/time/rate"
)

const (
	BaseURL = "https://api.fitbit.com"
	RateLimit = 150 // 150 requests per hour
)

type Client struct {
	httpClient  *http.Client
	rateLimiter *rate.Limiter
	baseURL     string
	token       *oauth2.Token
}

func NewClient(httpClient *http.Client, token *oauth2.Token) *Client {
	// 150 requests per hour with burst capability
	// Allow 10 immediate requests, then 2.5/minute sustained
	limiter := rate.NewLimiter(rate.Every(24*time.Second), 10)
	
	return &Client{
		httpClient:  httpClient,
		rateLimiter: limiter,
		baseURL:     BaseURL,
		token:       token,
	}
}

func (c *Client) makeRequest(ctx context.Context, method, endpoint string) ([]byte, error) {
	if err := c.rateLimiter.Wait(ctx); err != nil {
		return nil, fmt.Errorf("rate limiter error: %w", err)
	}
	
	url := c.baseURL + endpoint
	req, err := http.NewRequestWithContext(ctx, method, url, nil)
	if err != nil {
		return nil, err
	}
	
	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	
	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("API error: %d - %s", resp.StatusCode, string(body))
	}
	
	return io.ReadAll(resp.Body)
}

func (c *Client) GetHeartRateIntraday(ctx context.Context, date string) (*HeartRateData, error) {
	endpoint := fmt.Sprintf("/1/user/-/activities/heart/date/%s/1d/1min.json", date)
	data, err := c.makeRequest(ctx, "GET", endpoint)
	if err != nil {
		return nil, err
	}
	
	var result HeartRateData
	if err := json.Unmarshal(data, &result); err != nil {
		return nil, err
	}
	
	return &result, nil
}

func (c *Client) GetSleep(ctx context.Context, date string) (*SleepData, error) {
	endpoint := fmt.Sprintf("/1.2/user/-/sleep/date/%s.json", date)
	data, err := c.makeRequest(ctx, "GET", endpoint)
	if err != nil {
		return nil, err
	}
	
	var result SleepData
	if err := json.Unmarshal(data, &result); err != nil {
		return nil, err
	}
	
	return &result, nil
}

func (c *Client) GetActivity(ctx context.Context, date string) (*ActivityData, error) {
	endpoint := fmt.Sprintf("/1/user/-/activities/date/%s.json", date)
	data, err := c.makeRequest(ctx, "GET", endpoint)
	if err != nil {
		return nil, err
	}
	
	var result ActivityData
	if err := json.Unmarshal(data, &result); err != nil {
		return nil, err
	}
	
	return &result, nil
}

func (c *Client) GetSteps(ctx context.Context, date string) (*StepsData, error) {
	endpoint := fmt.Sprintf("/1/user/-/activities/steps/date/%s/1d/15min.json", date)
	data, err := c.makeRequest(ctx, "GET", endpoint)
	if err != nil {
		return nil, err
	}
	
	var result StepsData
	if err := json.Unmarshal(data, &result); err != nil {
		return nil, err
	}
	
	return &result, nil
}