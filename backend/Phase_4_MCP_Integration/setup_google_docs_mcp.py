#!/usr/bin/env python3
"""
Setup script for @a-bonus/google-docs-mcp

This script helps authenticate with the Google Docs MCP server.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    print("=" * 60)
    print("Setup for @a-bonus/google-docs-mcp")
    print("=" * 60)
    print()
    
    # Check for Node.js
    node_dir = Path(__file__).parent / "node"
    if (node_dir / "node.exe").exists():
        # Use local Node.js
        env = os.environ.copy()
        env["PATH"] = str(node_dir) + os.pathsep + env.get("PATH", "")
        npx_cmd = str(node_dir / "npx.cmd")
    else:
        # Use system Node.js
        env = os.environ.copy()
        npx_cmd = "npx"
    
    # Get credentials from user
    client_id = input("Enter your Google OAuth Client ID: ").strip()
    client_secret = input("Enter your Google OAuth Client Secret: ").strip()
    
    if not client_id or not client_secret:
        print("ERROR: Client ID and Client Secret are required!")
        return 1
    
    # Set environment variables
    env["GOOGLE_CLIENT_ID"] = client_id
    env["GOOGLE_CLIENT_SECRET"] = client_secret
    
    print()
    print("Running authentication...")
    print("A browser will open for you to authorize the application.")
    print()
    
    # Run auth command
    try:
        result = subprocess.run(
            [npx_cmd, "-y", "@a-bonus/google-docs-mcp", "auth"],
            env=env,
            check=True
        )
        print()
        print("=" * 60)
        print("Authentication successful!")
        print("=" * 60)
        print()
        print("You can now run Phase 4 with the MCP integration.")
        print()
        print("Make sure to add these to your .env file:")
        print(f"GOOGLE_CLIENT_ID={client_id}")
        print(f"GOOGLE_CLIENT_SECRET={client_secret}")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Authentication failed: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
