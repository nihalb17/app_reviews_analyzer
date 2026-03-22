#!/usr/bin/env python3
"""
Google OAuth Setup for MCP Google Drive Server

This script helps set up Google OAuth authentication required for the 
@modelcontextprotocol/server-gdrive MCP server.

Prerequisites:
1. Google Cloud Project with Google Drive API enabled
2. OAuth 2.0 credentials (Desktop application type)

Usage:
    python setup_google_auth.py
"""

import json
import os
import sys
from pathlib import Path
import urllib.parse
import urllib.request
import http.server
import socketserver
import threading
import webbrowser

# Configuration
CLIENT_ID = input("Enter your Google OAuth Client ID: ").strip()
CLIENT_SECRET = input("Enter your Google OAuth Client Secret: ").strip()
REDIRECT_URI = "http://localhost:8080/callback"
SCOPES = "https://www.googleapis.com/auth/drive.file https://www.googleapis.com/auth/documents"

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"

# Global variable to capture auth code
auth_code = None


class CallbackHandler(http.server.BaseHTTPRequestHandler):
    """HTTP handler for OAuth callback"""
    
    def do_GET(self):
        global auth_code
        
        # Parse query parameters
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        
        if 'code' in params:
            auth_code = params['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
                <html>
                <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                    <h1 style="color: #00D09C;">Authentication Successful!</h1>
                    <p>You can close this window and return to the terminal.</p>
                </body>
                </html>
            """)
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<h1>Authentication Failed</h1>")
    
    def log_message(self, format, *args):
        pass  # Suppress logs


def start_local_server():
    """Start local HTTP server to receive OAuth callback"""
    with socketserver.TCPServer(("", 8080), CallbackHandler) as httpd:
        httpd.handle_request()


def get_access_token(auth_code: str) -> dict:
    """Exchange auth code for access token"""
    data = {
        "code": auth_code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    
    req = urllib.request.Request(
        TOKEN_URL,
        data=urllib.parse.urlencode(data).encode(),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST"
    )
    
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode())


def main():
    print("=" * 60)
    print("Google OAuth Setup for MCP Google Drive")
    print("=" * 60)
    print()
    
    if not CLIENT_ID or not CLIENT_SECRET:
        print("ERROR: Client ID and Client Secret are required!")
        print()
        print("To get these:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project or select existing")
        print("3. Enable Google Drive API and Google Docs API")
        print("4. Go to Credentials → Create Credentials → OAuth client ID")
        print("5. Select 'Desktop application' type")
        print("6. Copy the Client ID and Client Secret")
        return 1
    
    # Build auth URL
    auth_params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "response_type": "code",
        "access_type": "offline",
        "prompt": "consent"
    }
    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(auth_params)}"
    
    print("Starting local server for OAuth callback...")
    server_thread = threading.Thread(target=start_local_server)
    server_thread.daemon = True
    server_thread.start()
    
    print()
    print("Opening browser for authentication...")
    webbrowser.open(auth_url)
    
    print("Waiting for authentication...")
    while auth_code is None:
        pass
    
    print("Authentication code received!")
    print("Exchanging for access token...")
    
    try:
        token_data = get_access_token(auth_code)
        
        # Save credentials
        credentials = {
            "type": "authorized_user",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "refresh_token": token_data.get("refresh_token"),
            "access_token": token_data.get("access_token")
        }
        
        # Determine save location
        home_dir = Path.home()
        
        # Try to find gdrive-server credentials location
        possible_paths = [
            home_dir / ".gdrive-server-credentials.json",
            home_dir / ".config" / "gdrive-server" / "credentials.json",
            Path("gdrive-credentials.json")
        ]
        
        print()
        print("=" * 60)
        print("Authentication Successful!")
        print("=" * 60)
        print()
        print("Save the following credentials to one of these locations:")
        print()
        for path in possible_paths:
            print(f"  - {path}")
        print()
        print("Credentials JSON:")
        print("-" * 60)
        print(json.dumps(credentials, indent=2))
        print("-" * 60)
        print()
        
        # Save to default location
        save_path = possible_paths[0]
        save_path.write_text(json.dumps(credentials, indent=2))
        print(f"Credentials saved to: {save_path}")
        print()
        print("You can now use the MCP Google Drive server!")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
