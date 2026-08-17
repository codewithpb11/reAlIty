"""
reAlIty Web Launcher — finds a free port and auto-opens browser.
"""
import os
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

# Ensure we're in the project root (parent of webapp/)
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
os.chdir(PROJECT_ROOT)

def is_port_free(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('0.0.0.0', port))
            return True
        except OSError:
            return False

def find_free_port(start=15000, end=15100):
    for port in range(start, end):
        if is_port_free(port):
            return port
    raise RuntimeError("No free ports found in range!")

def wait_for_server(port, timeout=60):
    """Poll until the server responds or timeout."""
    url = f"http://127.0.0.1:{port}/health"
    for _ in range(timeout * 2):
        try:
            import urllib.request
            with urllib.request.urlopen(url, timeout=1) as r:
                if r.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(0.5)
    return False

if __name__ == "__main__":
    port = find_free_port()
    url = f"http://localhost:{port}"

    print(f"Starting reAlIty Web server...")
    print(f"(First run will load the AI model — this may take 30-60 seconds)")
    print(f"")
    print(f"Server will be at: {url}")
    print(f"")

    # Start uvicorn in a subprocess (non-blocking)
    cmd = [
        sys.executable, "-m", "uvicorn",
        "webapp.main:app",
        "--host", "0.0.0.0",
        "--port", str(port),
    ]
    proc = subprocess.Popen(cmd)

    # Wait for server to be ready, then open browser
    print("Waiting for server to start...")
    if wait_for_server(port, timeout=90):
        print(f"Server ready! Opening browser...")
        webbrowser.open(url)
    else:
        print("Server didn't respond in time, but it may still be loading.")
        print(f"Open {url} manually in a few moments.")

    # Keep running until user kills
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        proc.wait()
