"""
google_auth_server.py — Minimal local server to complete Google OAuth
Run this once to get a token, then your pipeline uses it.

Usage:
    python google_auth_server.py
    → Opens browser to Google login
    → Google redirects to localhost:8080/callback?code=...
    → Prints your JWT token
"""

import webbrowser
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from auth import get_google_auth_url, handle_google_callback

TOKEN = None  # Will be set after callback


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global TOKEN
        parsed = urlparse(self.path)

        if parsed.path != "/callback":
            self.send_response(404)
            self.end_headers()
            return

        params = parse_qs(parsed.query)

        # Google returned an error
        if "error" in params:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Google login failed.")
            print(f"[AUTH] Error from Google: {params['error']}")
            return

        # Exchange the code for a JWT
        code  = params["code"][0]
        TOKEN = handle_google_callback(code)

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Login successful! You can close this tab.")
        print(f"\n[AUTH] Your JWT:\n{TOKEN}\n")

        # Shut down server after successful login
        threading.Thread(target=self.server.shutdown).start()

    def log_message(self, format, *args):
        pass  # Silence default request logs


def login() -> str:
    """Open browser for Google login, return JWT when done."""
    server = HTTPServer(("localhost", 8080), CallbackHandler)
    url    = get_google_auth_url()

    print(f"[AUTH] Opening browser for Google login...")
    webbrowser.open(url)
    server.serve_forever()  # Blocks until callback received

    return TOKEN


if __name__ == "__main__":
    token = login()
    print(f"[AUTH] Token ready — paste into run_pipeline.py or store in session.")
