package api

import (
	"context"
	"fmt"
	"net/http"
	"time"
	
	"golang.org/x/oauth2"
)

type AuthManager struct {
	config       *oauth2.Config
	token        *oauth2.Token
	authCodeChan chan string
	server       *http.Server
}

func NewAuthManager(clientID, clientSecret, redirectURI string) *AuthManager {
	return &AuthManager{
		config: &oauth2.Config{
			ClientID:     clientID,
			ClientSecret: clientSecret,
			RedirectURL:  redirectURI,
			Scopes: []string{
				"activity",
				"heartrate",
				"location",
				"nutrition",
				"profile",
				"settings",
				"sleep",
				"social",
				"weight",
			},
			Endpoint: oauth2.Endpoint{
				AuthURL:  "https://www.fitbit.com/oauth2/authorize",
				TokenURL: "https://api.fitbit.com/oauth2/token",
			},
		},
		authCodeChan: make(chan string, 1),
	}
}

func (am *AuthManager) GetAuthURL() string {
	return am.config.AuthCodeURL("state", oauth2.AccessTypeOffline)
}

func (am *AuthManager) StartCallbackServer() error {
	mux := http.NewServeMux()
	mux.HandleFunc("/callback", am.handleCallback)
	
	am.server = &http.Server{
		Addr:    ":8080",
		Handler: mux,
	}
	
	go func() {
		if err := am.server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			fmt.Printf("Callback server error: %v\n", err)
		}
	}()
	
	return nil
}

func (am *AuthManager) handleCallback(w http.ResponseWriter, r *http.Request) {
	code := r.URL.Query().Get("code")
	if code == "" {
		http.Error(w, "No authorization code received", http.StatusBadRequest)
		return
	}
	
	am.authCodeChan <- code
	
	w.Header().Set("Content-Type", "text/html")
	fmt.Fprintf(w, `
		<html>
		<body>
			<h1>Authorization Successful!</h1>
			<p>You can close this window and return to the application.</p>
			<script>window.close();</script>
		</body>
		</html>
	`)
}

func (am *AuthManager) WaitForAuthCode(timeout time.Duration) (string, error) {
	select {
	case code := <-am.authCodeChan:
		return code, nil
	case <-time.After(timeout):
		return "", fmt.Errorf("timeout waiting for authorization code")
	}
}

func (am *AuthManager) ExchangeCodeForToken(ctx context.Context, code string) (*oauth2.Token, error) {
	token, err := am.config.Exchange(ctx, code)
	if err != nil {
		return nil, err
	}
	am.token = token
	return token, nil
}

func (am *AuthManager) GetClient(ctx context.Context, token *oauth2.Token) *http.Client {
	return am.config.Client(ctx, token)
}

func (am *AuthManager) RefreshToken(ctx context.Context, token *oauth2.Token) (*oauth2.Token, error) {
	tokenSource := am.config.TokenSource(ctx, token)
	newToken, err := tokenSource.Token()
	if err != nil {
		return nil, err
	}
	am.token = newToken
	return newToken, nil
}

func (am *AuthManager) StopCallbackServer() error {
	if am.server != nil {
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		return am.server.Shutdown(ctx)
	}
	return nil
}