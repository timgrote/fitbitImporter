"""
Streamlit-compatible Fitbit OAuth handler.
Provides browser-only authentication without terminal interaction.
"""
import streamlit as st
import requests
import base64
import secrets
import configparser
from urllib.parse import urlencode, parse_qs, urlparse
import json
from pathlib import Path
from datetime import datetime, timedelta
import subprocess
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import webbrowser


class CallbackHandler(BaseHTTPRequestHandler):
    """Handle OAuth callback from Fitbit."""
    
    def do_GET(self):
        """Handle GET request with OAuth callback."""
        if self.path.startswith('/callback'):
            # Parse the callback URL
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            
            if 'code' in params:
                # Store the auth code for the main thread
                self.server.auth_code = params['code'][0]
                self.server.auth_state = params.get('state', [None])[0]
                
                # Send success response
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                
                success_html = """
                <html>
                <head><title>Fitbit Authorization Complete</title></head>
                <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                    <h1 style="color: #4CAF50;">✅ Authorization Successful!</h1>
                    <p>You can now close this window and return to the dashboard.</p>
                    <p>Your Fitbit data will begin downloading automatically.</p>
                    <script>setTimeout(() => window.close(), 3000);</script>
                </body>
                </html>
                """
                
                self.wfile.write(success_html.encode())
            else:
                # Authorization failed
                self.server.auth_code = None
                self.server.auth_error = params.get('error', ['Unknown error'])[0]
                
                self.send_response(400)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                
                error_html = """
                <html>
                <head><title>Fitbit Authorization Failed</title></head>
                <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                    <h1 style="color: #f44336;">❌ Authorization Failed</h1>
                    <p>Please try again or check your Fitbit app settings.</p>
                    <script>setTimeout(() => window.close(), 5000);</script>
                </body>
                </html>
                """
                
                self.wfile.write(error_html.encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress HTTP server logs."""
        pass


class StreamlitFitbitAuth:
    """Handle Fitbit OAuth flow entirely within Streamlit."""
    
    def __init__(self, config_file='myfitbit.ini'):
        """Initialize with config file."""
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        
        # Get credentials from config
        self.client_id = self.config.get('fitbit', 'client_id')
        self.client_secret = self.config.get('fitbit', 'client_secret')
        
        # OAuth settings - read from config file
        self.redirect_uri = self.config.get('fitbit', 'redirect_uri', fallback='http://localhost:8080/callback')
        self.scope = "activity heartrate location nutrition profile settings sleep social weight"
        self.token_file = Path('.streamlit_fitbit_tokens.json')
        
    def get_authorization_url(self):
        """Generate authorization URL."""
        # Generate state for security
        state = secrets.token_urlsafe(32)
        st.session_state.oauth_state = state
        
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': self.scope,
            'state': state
        }
        
        auth_url = f"https://www.fitbit.com/oauth2/authorize?{urlencode(params)}"
        return auth_url
    
    def start_callback_server(self):
        """Start temporary HTTP server to catch OAuth callback."""
        # Parse port from redirect URI
        parsed_uri = urlparse(self.redirect_uri)
        port = parsed_uri.port or 8080
        
        server = HTTPServer(('localhost', port), CallbackHandler)
        server.auth_code = None
        server.auth_state = None
        server.auth_error = None
        
        return server
    
    def authorize_automatically(self):
        """Complete OAuth flow automatically with temporary server."""
        try:
            # Start callback server
            server = self.start_callback_server()
            
            # Start server in background thread
            server_thread = threading.Thread(target=server.serve_forever)
            server_thread.daemon = True
            server_thread.start()
            
            # Generate authorization URL (don't auto-open in WSL)
            auth_url = self.get_authorization_url()
            # Store URL for UI to display
            self.current_auth_url = auth_url
            
            # Wait for callback (with timeout)
            timeout = 120  # 2 minutes
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                if server.auth_code is not None:
                    # Got authorization code
                    server.shutdown()
                    
                    # Verify state matches
                    if server.auth_state != st.session_state.get('oauth_state'):
                        return False, "Invalid OAuth state"
                    
                    # Exchange code for tokens
                    if self.exchange_code_for_tokens(server.auth_code):
                        return True, "Authentication successful!"
                    else:
                        return False, "Token exchange failed"
                
                elif hasattr(server, 'auth_error') and server.auth_error:
                    server.shutdown()
                    return False, f"Authorization error: {server.auth_error}"
                
                time.sleep(0.5)
            
            # Timeout
            server.shutdown()
            return False, "Authorization timeout - please try again"
            
        except Exception as e:
            return False, f"Authorization error: {str(e)}"
    
    def handle_callback(self, callback_url=None):
        """Handle the OAuth callback from URL parameters or manual input."""
        # First check URL parameters (in case redirect worked)
        query_params = st.query_params
        
        if 'code' in query_params and 'state' in query_params:
            code = query_params['code']
            state = query_params['state']
            
            # Verify state matches
            if state != st.session_state.get('oauth_state'):
                st.error("❌ Invalid OAuth state. Please try again.")
                return False
                
            # Exchange code for tokens
            return self.exchange_code_for_tokens(code)
        
        # Handle manual callback URL input
        if callback_url and callback_url.startswith(('http://localhost:', 'http://127.0.0.1:')):
            from urllib.parse import urlparse, parse_qs
            
            parsed = urlparse(callback_url)
            params = parse_qs(parsed.query)
            
            if 'code' in params and 'state' in params:
                code = params['code'][0]
                state = params['state'][0]
                
                # Verify state matches
                if state != st.session_state.get('oauth_state'):
                    st.error("❌ Invalid OAuth state. Please try again.")
                    return False
                    
                # Exchange code for tokens
                return self.exchange_code_for_tokens(code)
        
        return False
    
    def exchange_code_for_tokens(self, code):
        """Exchange authorization code for access tokens."""
        token_url = "https://api.fitbit.com/oauth2/token"
        
        # Prepare credentials for Basic Auth
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'client_id': self.client_id,
            'grant_type': 'authorization_code',
            'redirect_uri': self.redirect_uri,
            'code': code
        }
        
        try:
            response = requests.post(token_url, headers=headers, data=data)
            
            if response.status_code == 200:
                tokens = response.json()
                self.save_tokens(tokens)
                return True
            else:
                st.error(f"❌ Token exchange failed: {response.text}")
                return False
                
        except Exception as e:
            st.error(f"❌ Token exchange error: {str(e)}")
            return False
    
    def save_tokens(self, tokens):
        """Save tokens to file."""
        # Add expiration timestamp
        expires_in = tokens.get('expires_in', 3600)
        expires_at = datetime.now() + timedelta(seconds=expires_in)
        tokens['expires_at'] = expires_at.isoformat()
        
        with open(self.token_file, 'w') as f:
            json.dump(tokens, f, indent=2)
    
    def load_tokens(self):
        """Load saved tokens."""
        if not self.token_file.exists():
            return None
            
        try:
            with open(self.token_file, 'r') as f:
                tokens = json.load(f)
                
            # Check if token is expired
            expires_at = datetime.fromisoformat(tokens.get('expires_at', '1970-01-01'))
            if datetime.now() > expires_at:
                return None  # Token expired
                
            return tokens
        except Exception:
            return None
    
    def is_authenticated(self):
        """Check if we have valid authentication."""
        tokens = self.load_tokens()
        return tokens is not None
    
    def get_auth_header(self):
        """Get authorization header for API requests."""
        tokens = self.load_tokens()
        if not tokens:
            return None
            
        return f"Bearer {tokens['access_token']}"
    
    def revoke_tokens(self):
        """Revoke tokens and delete local file."""
        tokens = self.load_tokens()
        if tokens:
            # Revoke with Fitbit
            try:
                revoke_url = "https://api.fitbit.com/oauth2/revoke"
                headers = {'Authorization': f"Bearer {tokens['access_token']}"}
                data = {'token': tokens['access_token']}
                requests.post(revoke_url, headers=headers, data=data)
            except:
                pass  # Ignore errors during revoke
                
        # Delete local file
        if self.token_file.exists():
            self.token_file.unlink()
    
    def run_authenticated_update(self, progress_callback=None):
        """Run update command with valid authentication."""
        if not self.is_authenticated():
            return False, "Not authenticated"
            
        try:
            from streamlit_fitbit_client import StreamlitFitbitClient
            
            # Use our custom client with progress callback
            client = StreamlitFitbitClient(self.config_file, progress_callback=progress_callback)
            
            # Download recent 6 days of data
            success = client.run_recent_update(days=6)
            
            if success:
                return True, "Data updated successfully using browser authentication!"
            else:
                return False, "Update failed - check API connection"
                
        except Exception as e:
            return False, f"Error during update: {str(e)}"


def render_auth_ui():
    """Render the authentication UI in Streamlit."""
    st.sidebar.markdown("---")
    st.sidebar.header("🔐 Fitbit Authentication")
    
    auth = StreamlitFitbitAuth()
    
    # Check for manual callback URL input
    if 'callback_url' in st.session_state and st.session_state.callback_url:
        if auth.handle_callback(st.session_state.callback_url):
            st.sidebar.success("✅ Successfully authenticated with Fitbit!")
            st.session_state.callback_url = ""  # Clear the callback URL
            st.rerun()
            return auth
        else:
            st.sidebar.error("❌ Authentication failed. Please try again.")
            st.session_state.callback_url = ""
    
    # Handle OAuth callback from URL parameters
    if auth.handle_callback():
        st.sidebar.success("✅ Successfully authenticated with Fitbit!")
        st.rerun()
        return auth
    
    # Check current auth status
    if auth.is_authenticated():
        st.sidebar.success("✅ Authenticated with Fitbit")
        
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("🔄 Update Data", type="primary"):
                return auth, "update"
        with col2:
            if st.button("🚪 Logout"):
                auth.revoke_tokens()
                st.rerun()
        
        return auth, "authenticated"
    
    else:
        st.sidebar.warning("⚠️ Not authenticated with Fitbit")
        
        st.sidebar.markdown("""
        **Click the button below to authenticate with Fitbit:**
        
        • A browser window will open for authorization
        • Log in with your Fitbit account (Google/email/etc.)  
        • Authorization will complete automatically
        • Return here when done!
        """)
        
        if st.sidebar.button("🔐 Authenticate with Fitbit", type="primary"):
            # Start the authorization process
            st.session_state.auth_in_progress = True
            st.rerun()
        
        # Handle ongoing authorization
        if st.session_state.get('auth_in_progress', False):
            with st.sidebar:
                status_container = st.empty()
                
                status_container.info("🚀 Starting Fitbit authorization...")
                
                # Start callback server in background
                try:
                    server = auth.start_callback_server()
                    server_thread = threading.Thread(target=server.serve_forever)
                    server_thread.daemon = True
                    server_thread.start()
                    
                    # Generate auth URL
                    auth_url = auth.get_authorization_url()
                    
                    # Show the authorization URL
                    status_container.info("🔗 **Click the link below to authorize:**")
                    
                    st.sidebar.markdown(f"""
                    <a href="{auth_url}" target="_blank" style="
                        display: inline-block;
                        background-color: #4CAF50;
                        color: white;
                        padding: 1rem 1.5rem;
                        border: none;
                        border-radius: 0.5rem;
                        text-decoration: none;
                        font-weight: bold;
                        font-size: 1.1em;
                        margin: 1rem 0;
                        text-align: center;
                        width: 90%;
                    ">🔐 Authorize Fitbit Access</a>
                    """, unsafe_allow_html=True)
                    
                    st.sidebar.markdown("""
                    **After clicking the link above:**
                    1. Log in to Fitbit (Google/email/etc.)
                    2. Click "Allow" to authorize access
                    3. Wait here - authorization will complete automatically!
                    """)
                    
                    # Check for callback completion
                    progress_bar = st.sidebar.progress(0)
                    timeout = 120  # 2 minutes
                    check_interval = 1  # Check every second
                    
                    for i in range(0, timeout, check_interval):
                        progress = i / timeout
                        progress_bar.progress(progress)
                        
                        if hasattr(server, 'auth_code') and server.auth_code is not None:
                            # Got authorization code
                            server.shutdown()
                            
                            # Verify state
                            if server.auth_state == st.session_state.get('oauth_state'):
                                # Exchange code for tokens
                                if auth.exchange_code_for_tokens(server.auth_code):
                                    status_container.success("✅ Authentication successful!")
                                    st.session_state.auth_in_progress = False
                                    progress_bar.progress(1.0)
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    status_container.error("❌ Token exchange failed")
                                    st.session_state.auth_in_progress = False
                            else:
                                status_container.error("❌ Invalid OAuth state")
                                st.session_state.auth_in_progress = False
                            break
                            
                        elif hasattr(server, 'auth_error') and server.auth_error:
                            server.shutdown()
                            status_container.error(f"❌ Authorization error: {server.auth_error}")
                            st.session_state.auth_in_progress = False
                            break
                        
                        time.sleep(check_interval)
                    else:
                        # Timeout reached
                        server.shutdown()
                        status_container.error("⏰ Authorization timeout - please try again")
                        st.session_state.auth_in_progress = False
                    
                    if st.sidebar.button("❌ Cancel Authorization"):
                        server.shutdown()
                        st.session_state.auth_in_progress = False
                        st.rerun()
                        
                except Exception as e:
                    status_container.error(f"❌ Authorization error: {str(e)}")
                    st.session_state.auth_in_progress = False
        
        return auth, "not_authenticated"