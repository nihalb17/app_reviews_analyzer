"""
MCP Client for Google Doc Integration (Raw Protocol Implementation)

Handles communication with Google Docs via MCP (Model Context Protocol).
Implements MCP protocol directly without using the official SDK.

MCP Protocol: JSON-RPC 2.0 over stdio
"""

import json
import subprocess
import threading
import queue
import os
import urllib.request
import zipfile
import platform
from typing import Dict, Optional, Any
from pathlib import Path
import sys
import uuid

# Add parent directories to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))
from core.config import settings


class NodeJSManager:
    """Manages local Node.js installation for MCP server"""
    
    def __init__(self):
        self.node_dir = settings.DATA_DIR.parent / "node"
        self.node_exe = self._get_node_exe_path()
        self.npx_exe = self._get_npx_exe_path()
    
    def _get_node_exe_path(self) -> Path:
        """Get path to node executable"""
        if platform.system() == "Windows":
            return self.node_dir / "node.exe"
        return self.node_dir / "bin" / "node"
    
    def _get_npx_exe_path(self) -> Path:
        """Get path to npx executable"""
        if platform.system() == "Windows":
            return self.node_dir / "npx.cmd"
        return self.node_dir / "bin" / "npx"
    
    def is_installed(self) -> bool:
        """Check if Node.js is installed locally"""
        return self.node_exe.exists() and self.npx_exe.exists()
    
    def install(self) -> bool:
        """
        Download and install Node.js locally
        
        Returns:
            True if installation successful
        """
        try:
            print("Downloading Node.js...")
            
            # Determine download URL based on platform
            system = platform.system()
            machine = platform.machine()
            
            if system == "Windows":
                if machine == "AMD64":
                    url = "https://nodejs.org/dist/v20.11.0/node-v20.11.0-win-x64.zip"
                else:
                    url = "https://nodejs.org/dist/v20.11.0/node-v20.11.0-win-x86.zip"
                archive_name = "node.zip"
            elif system == "Darwin":
                if machine == "arm64":
                    url = "https://nodejs.org/dist/v20.11.0/node-v20.11.0-darwin-arm64.tar.gz"
                else:
                    url = "https://nodejs.org/dist/v20.11.0/node-v20.11.0-darwin-x64.tar.gz"
                archive_name = "node.tar.gz"
            else:  # Linux
                if machine == "aarch64":
                    url = "https://nodejs.org/dist/v20.11.0/node-v20.11.0-linux-arm64.tar.xz"
                else:
                    url = "https://nodejs.org/dist/v20.11.0/node-v20.11.0-linux-x64.tar.xz"
                archive_name = "node.tar.xz"
            
            # Create node directory
            self.node_dir.mkdir(parents=True, exist_ok=True)
            
            # Download archive
            archive_path = self.node_dir / archive_name
            urllib.request.urlretrieve(url, archive_path)
            print(f"Downloaded to: {archive_path}")
            
            # Extract archive
            print("Extracting Node.js...")
            if archive_name.endswith(".zip"):
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(self.node_dir)
            else:
                # For tar.gz and tar.xz, use tar command
                import tarfile
                with tarfile.open(archive_path, 'r:*') as tar_ref:
                    tar_ref.extractall(self.node_dir)
            
            # Move files from extracted directory to node_dir
            extracted_dirs = [d for d in self.node_dir.iterdir() if d.is_dir() and d.name.startswith("node-")]
            if extracted_dirs:
                extracted_dir = extracted_dirs[0]
                for item in extracted_dir.iterdir():
                    target = self.node_dir / item.name
                    if target.exists():
                        import shutil
                        shutil.rmtree(target) if target.is_dir() else target.unlink()
                    item.rename(target)
                extracted_dir.rmdir()
            
            # Clean up archive
            archive_path.unlink()
            
            print(f"Node.js installed at: {self.node_dir}")
            print(f"Node executable: {self.node_exe}")
            print(f"NPX executable: {self.npx_exe}")
            
            return self.is_installed()
            
        except Exception as e:
            print(f"Failed to install Node.js: {e}")
            return False
    
    def get_node_path(self) -> str:
        """Get path to node executable"""
        return str(self.node_exe) if self.node_exe.exists() else "node"
    
    def get_npx_path(self) -> str:
        """Get path to npx executable"""
        return str(self.npx_exe) if self.npx_exe.exists() else "npx"


class RawMCPClient:
    """
    Raw MCP Client for Google Doc operations
    
    Implements MCP protocol directly using JSON-RPC over stdio.
    No SDK dependencies required.
    """
    
    def __init__(self, google_doc_id: str = None):
        self.google_doc_id = google_doc_id or settings.GOOGLE_DOC_ID
        self.document_url = f"https://docs.google.com/document/d/{self.google_doc_id}/edit"
        self.node_manager = NodeJSManager()
        self.mcp_server_package = "@a-bonus/google-docs-mcp"
        self.mcp_server_args = ["-y", self.mcp_server_package]
        self.process = None
        self.request_id = 0
        self.response_queue = queue.Queue()
        self.read_thread = None
        
        # Setup token file from environment variables (for production)
        self._setup_token_from_env()
    
    def _setup_token_from_env(self):
        """
        Create token.json from environment variables if they exist.
        This is needed for production environments where the token file
        doesn't exist but credentials are provided via env vars.
        """
        client_id = os.environ.get("GOOGLE_CLIENT_ID")
        client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
        refresh_token = os.environ.get("GOOGLE_REFRESH_TOKEN")
        
        print(f"Checking Google OAuth credentials...")
        print(f"  GOOGLE_CLIENT_ID: {'set' if client_id else 'NOT SET'}")
        print(f"  GOOGLE_CLIENT_SECRET: {'set' if client_secret else 'NOT SET'}")
        print(f"  GOOGLE_REFRESH_TOKEN: {'set' if refresh_token else 'NOT SET'}")
        
        if client_id and client_secret and refresh_token:
            # Check if token file already exists
            home_dir = Path.home()
            token_dir = home_dir / ".config" / "google-docs-mcp"
            token_file = token_dir / "token.json"
            
            print(f"Token file path: {token_file}")
            print(f"Token file exists: {token_file.exists()}")
            
            if not token_file.exists():
                print("Creating token.json from environment variables...")
                token_dir.mkdir(parents=True, exist_ok=True)
                
                token_data = {
                    "type": "authorized_user",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "refresh_token": refresh_token
                }
                
                with open(token_file, 'w') as f:
                    json.dump(token_data, f, indent=2)
                
                print(f"Token file created at: {token_file}")
            else:
                print(f"Token file already exists at: {token_file}")
        else:
            print("WARNING: Google OAuth credentials not fully configured!")
    
    def _ensure_nodejs(self) -> bool:
        """
        Ensure Node.js is available (system or local)
        
        Returns:
            True if Node.js is available
        """
        # Check system npx first
        import shutil
        if shutil.which("npx"):
            return True
        
        # Check local installation
        if self.node_manager.is_installed():
            return True
        
        # Try to install locally
        print("Node.js not found. Installing locally...")
        return self.node_manager.install()
    
    def _check_google_credentials(self) -> bool:
        """
        Check if Google OAuth credentials are configured
        
        Returns:
            True if credentials exist
        """
        home_dir = Path.home()
        
        print("Checking Google credential files...")
        
        # Check for @a-bonus/google-docs-mcp token
        bonus_paths = [
            home_dir / ".config" / "google-docs-mcp" / "token.json",
            home_dir / "AppData" / "Local" / "google-docs-mcp" / "token.json",  # Windows
        ]
        
        for path in bonus_paths:
            print(f"  Checking: {path} - {'EXISTS' if path.exists() else 'not found'}")
            if path.exists():
                print("Google credentials found via token file!")
                return True
        
        # Also check if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are set
        if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET:
            print("Google credentials found via environment variables!")
            return True
        
        print("WARNING: No Google credentials found!")
        return False
    
    def _get_npx_command(self) -> str:
        """Get the npx command to use (local or system)"""
        # Prefer local Node.js installation
        if self.node_manager.is_installed():
            return str(self.node_manager.npx_exe)
        
        # Fall back to system npx
        import shutil
        if shutil.which("npx"):
            return "npx"
        
        return "npx"
    
    def _fallback_save(self, content: str, note: str) -> Dict:
        """Fallback: Save content locally when MCP is not available"""
        output_file = settings.DATA_DIR / "google_doc_content.txt"
        settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Log the issue prominently
        print("=" * 60)
        print(f"WARNING: Google Doc NOT updated - {note}")
        print(f"Content saved locally to: {output_file}")
        print("=" * 60)
        
        return {
            "success": False,
            "error": "Google Doc update failed",
            "message": note,
            "document_url": self.document_url,
            "document_id": self.google_doc_id,
            "local_file": str(output_file),
            "content_length": len(content)
        }
    
    def _get_next_request_id(self) -> int:
        """Get next request ID for JSON-RPC"""
        self.request_id += 1
        return self.request_id
    
    def _send_request(self, method: str, params: dict = None) -> dict:
        """
        Send JSON-RPC request to MCP server
        
        Args:
            method: JSON-RPC method name
            params: Method parameters
            
        Returns:
            JSON-RPC response
        """
        request_id = self._get_next_request_id()
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method
        }
        if params:
            request["params"] = params
        
        # Send request
        request_line = json.dumps(request) + "\n"
        print(f"Sending: {request_line.strip()}")
        
        try:
            self.process.stdin.write(request_line.encode())
            self.process.stdin.flush()
        except BrokenPipeError:
            return {"error": "Server process closed connection"}
        
        # Read response using threading for cross-platform compatibility
        import threading
        import time
        
        response_container = {"data": None, "error": None, "server_logs": []}
        
        def read_response():
            try:
                # Keep reading lines until we get a valid JSON-RPC response with matching ID
                while True:
                    try:
                        response_line = self.process.stdout.readline()
                    except OSError as e:
                        # Process stdout is closed/invalid
                        print(f"[MCP] OSError reading from process: {e}")
                        print(f"[MCP] Process poll status: {self.process.poll()}")
                        break
                    
                    # Handle None (stream closed) or empty bytes
                    if response_line is None or response_line == b'':
                        print("[MCP] Server closed stdout stream")
                        break
                    
                    try:
                        decoded_line = response_line.decode().strip()
                    except UnicodeDecodeError as e:
                        print(f"[MCP] Unicode decode error: {e}")
                        continue
                    
                    # Skip empty lines
                    if not decoded_line:
                        continue
                    
                    # Skip log/info messages (lines that don't start with {)
                    if not decoded_line.startswith("{"):
                        print(f"[Server Log] {decoded_line}")
                        response_container["server_logs"].append(decoded_line)
                        continue
                    
                    # Try to parse as JSON
                    try:
                        parsed = json.loads(decoded_line)
                    except json.JSONDecodeError:
                        print(f"[Server Log] {decoded_line}")
                        response_container["server_logs"].append(decoded_line)
                        continue
                    
                    # Check if this is a notification (no 'id' field) - skip it
                    if "id" not in parsed:
                        # This is a notification, log it and continue
                        if "method" in parsed and parsed["method"] == "notifications/message":
                            msg = parsed.get("params", {}).get("data", {}).get("message", "")
                            print(f"[Notification] {msg}")
                        continue
                    
                    # Check if this response matches our request ID
                    if parsed.get("id") == request_id:
                        response_container["data"] = decoded_line
                        break
                    else:
                        # Response ID doesn't match, might be from a previous request
                        print(f"[Warning] Response ID mismatch: expected {request_id}, got {parsed.get('id')}")
                        
            except Exception as e:
                import traceback
                print(f"[MCP] Exception in read_response: {e}")
                traceback.print_exc()
                response_container["error"] = str(e)
        
        # Start reader thread
        reader_thread = threading.Thread(target=read_response)
        reader_thread.daemon = True
        reader_thread.start()
        
        # Wait for response with timeout (longer for initial auth)
        # First request may need more time for Google OAuth
        timeout = 60 if method == "initialize" else 30
        print(f"Waiting up to {timeout}s for response (method: {method})...")
        
        # Check periodically if process is still alive
        start_time = time.time()
        while reader_thread.is_alive() and (time.time() - start_time) < timeout:
            reader_thread.join(timeout=1)  # Check every second
            if self.process.poll() is not None:
                print(f"MCP server process died during request (exit code: {self.process.returncode})")
                # Try to read any remaining output
                try:
                    remaining = self.process.stdout.read()
                    if remaining:
                        print(f"Remaining output: {remaining.decode()[:500]}")
                except:
                    pass
                break
        
        if response_container["error"]:
            return {"error": response_container["error"]}
        
        if response_container["data"] is None:
            # Check if process is still alive
            if self.process.poll() is not None:
                error_msg = f"MCP server exited with code {self.process.returncode}"
            else:
                error_msg = "Timeout waiting for response"
            
            # Include any server logs we captured
            if response_container["server_logs"]:
                error_msg += f"\nServer logs: {response_container['server_logs'][-5:]}"  # Last 5 logs
            
            return {"error": error_msg}
        
        response_str = response_container["data"]
        # Only print first 100 chars to avoid flooding terminal
        preview = response_str[:100] if len(response_str) > 100 else response_str
        print(f"Received: {preview}...")
        
        if not response_str:
            return {"error": "Empty response from server"}
        
        try:
            return json.loads(response_str)
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Raw response: {response_str}")
            return {"error": f"Invalid JSON response: {response_str[:100]}"}
    
    def _initialize(self) -> bool:
        """
        Initialize MCP connection
        
        Returns:
            True if initialization successful
        """
        # Send initialize request
        init_params = {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "groww-reviews-analyzer",
                "version": "1.0.0"
            }
        }
        
        response = self._send_request("initialize", init_params)
        
        if "error" in response:
            print(f"MCP initialization error: {response['error']}")
            return False
        
        # Send initialized notification
        self._send_notification("initialized")
        return True
    
    def _send_notification(self, method: str, params: dict = None):
        """Send JSON-RPC notification (no response expected)"""
        notification = {
            "jsonrpc": "2.0",
            "method": method
        }
        if params:
            notification["params"] = params
        
        notification_line = json.dumps(notification) + "\n"
        self.process.stdin.write(notification_line.encode())
        self.process.stdin.flush()
    
    def _list_tools(self) -> list:
        """
        List available tools from MCP server
        
        Returns:
            List of available tools
        """
        response = self._send_request("tools/list")
        
        if "error" in response:
            print(f"Error listing tools: {response['error']}")
            return []
        
        return response.get("result", {}).get("tools", [])
    
    def _call_tool(self, tool_name: str, arguments: dict) -> dict:
        """
        Call a tool on the MCP server
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            Tool call result
        """
        params = {
            "name": tool_name,
            "arguments": arguments
        }
        
        response = self._send_request("tools/call", params)
        return response
    
    def _replace_google_doc_content(self, document_id: str, content: str) -> dict:
        """
        Replace the entire content of a Google Doc
        
        Args:
            document_id: Google Doc ID
            content: Text content to replace with
            
        Returns:
            Result dict
        """
        # Try replaceDocumentWithMarkdown first
        print(f"\nAttempting to replace document with {len(content)} characters...")
        result = self._call_tool(
            "replaceDocumentWithMarkdown",
            {
                "documentId": document_id,
                "markdown": content
            }
        )
        
        print(f"  Tool result keys: {list(result.keys())}")
        
        if "error" in result:
            error_msg = result.get('error', 'Unknown error')
            print(f"  Replace failed: {error_msg}")
            
            # Check if it's a "not found" error - document might need to be created
            if "not found" in str(error_msg).lower() or "404" in str(error_msg):
                print("  Document not found or not accessible")
            
            # Fallback to appendText
            print("  Trying appendText as fallback...")
            result = self._call_tool(
                "appendText",
                {
                    "documentId": document_id,
                    "text": content
                }
            )
            if "error" in result:
                print(f"  Append also failed: {result.get('error')}")
            else:
                print("  Content appended via fallback")
        elif "result" in result:
            print("  Replace succeeded")
        else:
            print(f"  Unexpected response structure: {result}")
        
        return result
    
    def _start_server(self) -> bool:
        """
        Start the MCP server process
        
        Returns:
            True if server started successfully
        """
        try:
            # Kill any existing MCP server processes to ensure clean state
            import subprocess as sp
            try:
                sp.run(["pkill", "-f", "google-docs-mcp"], capture_output=True)
                time.sleep(0.5)
            except:
                pass
            
            npx_cmd = self._get_npx_command()
            print(f"Starting MCP server with: {npx_cmd}")
            print(f"Package: {self.mcp_server_package}")
            
            # Verify npx is available
            import shutil
            npx_path = shutil.which(npx_cmd)
            if not npx_path:
                print(f"ERROR: {npx_cmd} not found in PATH")
                return False
            print(f"npx found at: {npx_path}")
            
            # Set up environment with local node if needed
            env = os.environ.copy()
            if not self.node_manager.is_installed():
                if not npx_path:
                    return False
            else:
                # Add local node to PATH
                env["PATH"] = str(self.node_manager.node_dir) + os.pathsep + env.get("PATH", "")
            
            # Add Google OAuth credentials to environment
            if settings.GOOGLE_CLIENT_ID:
                env["GOOGLE_CLIENT_ID"] = settings.GOOGLE_CLIENT_ID
            if settings.GOOGLE_CLIENT_SECRET:
                env["GOOGLE_CLIENT_SECRET"] = settings.GOOGLE_CLIENT_SECRET
            
            # Add refresh token if available (for production environments)
            refresh_token = os.environ.get("GOOGLE_REFRESH_TOKEN")
            if refresh_token:
                env["GOOGLE_REFRESH_TOKEN"] = refresh_token
            
            # Debug: print environment (without secrets)
            print(f"Environment variables set:")
            print(f"  GOOGLE_CLIENT_ID: {'set' if env.get('GOOGLE_CLIENT_ID') else 'NOT SET'}")
            print(f"  GOOGLE_CLIENT_SECRET: {'set' if env.get('GOOGLE_CLIENT_SECRET') else 'NOT SET'}")
            print(f"  GOOGLE_REFRESH_TOKEN: {'set' if env.get('GOOGLE_REFRESH_TOKEN') else 'NOT SET'}")
            
            # Start process with stderr redirected to stdout for debugging
            self.process = subprocess.Popen(
                [npx_cmd] + self.mcp_server_args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Merge stderr into stdout for debugging
                text=False,
                env=env,
                bufsize=0  # Unbuffered
            )
            
            print(f"Process started with PID: {self.process.pid}")
            
            # Give the server more time to start (OAuth can be slow)
            import time
            
            print("Waiting for MCP server to initialize...")
            
            # Check process status frequently during startup
            for i in range(10):
                time.sleep(0.5)
                poll_result = self.process.poll()
                if poll_result is not None:
                    # Process exited
                    print(f"MCP server exited during startup at iteration {i} with code: {poll_result}")
                    try:
                        # Try to read any output
                        output = self.process.stdout.read()
                        if output:
                            print(f"Server output: {output.decode()[:1000]}")
                    except Exception as e:
                        print(f"Could not read output: {e}")
                    return False
                print(f"  [{i+1}/10] Process still running (PID: {self.process.pid})")
            
            # Check if process is still running
            if self.process.poll() is not None:
                # Process exited immediately
                try:
                    output = self.process.stdout.read()
                    print(f"MCP server exited. Output: {output.decode()[:500]}")
                except:
                    pass
                return False
            
            print("MCP server process started, proceeding with initialization...")
            return True
        except Exception as e:
            print(f"Failed to start MCP server: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _stop_server(self):
        """Stop the MCP server process"""
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None
    
    def append_to_document(self, content: str) -> Dict:
        """
        Append content to the Google Doc using raw MCP protocol
        
        Args:
            content: Text content to append to the document
            
        Returns:
            Dictionary with operation result
        """
        if not self.google_doc_id:
            return {
                "success": False,
                "error": "Google Doc ID not configured",
                "message": "Please set GOOGLE_DOC_ID in .env file"
            }
        
        # Ensure Node.js is available
        if not self._ensure_nodejs():
            return self._fallback_save(
                content, 
                "Node.js could not be installed. Please install manually from https://nodejs.org/"
            )
        
        # Check Google OAuth credentials
        if not self._check_google_credentials():
            return self._fallback_save(
                content,
                "Google OAuth credentials not found. Run: python setup_google_auth.py"
            )
        
        try:
            # Start MCP server
            print("Starting MCP server...")
            if not self._start_server():
                return self._fallback_save(content, "Failed to start MCP server")
            
            # Initialize connection
            print("Initializing MCP connection...")
            if not self._initialize():
                self._stop_server()
                return self._fallback_save(content, "MCP initialization failed")
            
            # List available tools
            print("Listing available tools...")
            tools = self._list_tools()
            
            print(f"  Tools response: {tools}")
            
            if not tools:
                print("  ERROR: No tools returned from MCP server")
                print("  This may indicate:")
                print("    - Authentication failure (check GOOGLE_REFRESH_TOKEN)")
                print("    - Google Doc ID not accessible")
                print("    - MCP server in bad state")
                self._stop_server()
                return self._fallback_save(content, "No tools available from MCP server")
            
            # Find append/write tool
            append_tool = None
            for tool in tools:
                tool_name = tool.get("name", "").lower()
                if "append" in tool_name or "write" in tool_name or "update" in tool_name:
                    append_tool = tool
                    break
            
            if not append_tool:
                self._stop_server()
                return {
                    "success": False,
                    "error": "No append tool found",
                    "available_tools": [t.get("name") for t in tools]
                }
            
            tool_name = append_tool.get("name")
            print(f"Using tool: {tool_name}")
            
            # Call the tool using the replace helper method
            result = self._replace_google_doc_content(self.google_doc_id, content)
            
            # Stop server
            self._stop_server()
            
            if "error" in result:
                return {
                    "success": False,
                    "error": result["error"],
                    "message": "Tool call failed"
                }
            
            return {
                "success": True,
                "message": "Content appended to Google Doc via MCP (raw protocol)",
                "document_url": self.document_url,
                "document_id": self.google_doc_id,
                "tool_used": tool_name,
                "result": result.get("result")
            }
            
        except Exception as e:
            self._stop_server()
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to append content via MCP"
            }
    
    def get_document_url(self) -> str:
        """Get the Google Doc URL"""
        return self.document_url
    
    def is_configured(self) -> bool:
        """Check if Google Doc ID is configured"""
        return bool(self.google_doc_id)


# Alias for backward compatibility
MCPClient = RawMCPClient
