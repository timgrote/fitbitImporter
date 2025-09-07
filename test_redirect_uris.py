#!/usr/bin/env python3
"""
Test different redirect URIs to find which one is configured in the Fitbit app.
"""

import configparser
from urllib.parse import urlencode
import secrets

def test_redirect_uri(redirect_uri):
    """Generate auth URL for testing different redirect URIs."""
    
    # Read config
    config = configparser.ConfigParser()
    config.read('myfitbit.ini')
    
    client_id = config.get('fitbit', 'client_id')
    scope = "activity heartrate location nutrition profile settings sleep social weight"
    
    # Generate state for security
    state = secrets.token_urlsafe(32)
    
    params = {
        'response_type': 'code',
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': scope,
        'state': state
    }
    
    auth_url = f"https://www.fitbit.com/oauth2/authorize?{urlencode(params)}"
    
    print(f"\n=== Testing Redirect URI: {redirect_uri} ===")
    print(f"Test URL: {auth_url}")
    print("\nIf this URI is correct, you should see the authorization page.")
    print("If not, you'll see the same 'invalid_request' error.")
    
    return auth_url

if __name__ == "__main__":
    print("🧪 FITBIT REDIRECT URI TESTER")
    print("=" * 50)
    
    # Common redirect URIs to test
    test_uris = [
        "http://localhost:8080/callback",
        "http://127.0.0.1:8080/callback", 
        "http://localhost:8189/auth_code",
        "http://127.0.0.1:8189/auth_code",
        "http://localhost:8080/auth_code",
        "http://127.0.0.1:8080/auth_code"
    ]
    
    for uri in test_uris:
        test_redirect_uri(uri)
        
    print("\n" + "=" * 50)
    print("🔍 INSTRUCTIONS:")
    print("1. Try each URL above in your browser")
    print("2. The correct one will show the Fitbit authorization page")
    print("3. The wrong ones will show 'invalid_request' error")
    print("4. Let me know which URI works!")