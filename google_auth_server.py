import os
import webbrowser
import threading
import redis
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from auth import get_google_auth_url, handle_google_callback, refresh_access_token
from config import REDIS_HOST, REDIS_PORT, REDIS_DB, setup_logging
import logging

setup_logging()
logger = logging.getLogger(__name__)

REDIS = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=os.getenv("REDIS_PASSWORD"),
    ssl=True,
    decode_responses=True,
    db=REDIS_DB,
)
SESSION_KEY   = "mimo:refresh_token"   # key in Redis
SESSION_TTL   = 60 * 60 * 24 * 30     # 30 days in seconds
RESULT        = {}


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path != "/callback":
            self.send_response(404)
            self.end_headers()
            return

        params = parse_qs(parsed.query)

        if "error" in params:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Google login failed.")
            return

        code   = params["code"][0]
        tokens = handle_google_callback(code)

        # Save refresh token to Redis with 30-day TTL
        REDIS.setex(SESSION_KEY, SESSION_TTL, tokens["refresh_token"])
        logger.info(f" Refresh token saved to Redis (TTL: 30 days)")

        RESULT["access_token"] = tokens["access_token"]

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Login successful! You can close this tab.")

        threading.Thread(target=self.server.shutdown).start()

    def log_message(self, format, *args):
        pass


def login() -> str:
    """
    If a valid refresh token exists in Redis, use it silently and if not
    open browser for Google login.
    Returns a valid access token.
    """
    # Try to reuse Redis session
    refresh_token = REDIS.get(SESSION_KEY)
    if refresh_token:
        try:
            access_token = refresh_access_token(refresh_token)
            ttl_days     = REDIS.ttl(SESSION_KEY) // 86400
            logger.info(f" Reused Redis session ({ttl_days} days remaining)")
            return access_token
        except Exception as e:
            logger.info(f"Redis session invalid ({e}), re-logging in...")
            REDIS.delete(SESSION_KEY)

    # Full Google login
    server = HTTPServer(("localhost", 8080), CallbackHandler)
    logger.info("Opening browser for Google login...")
    auth_url = get_google_auth_url()
    
    webbrowser.open(auth_url)
    server.serve_forever()

    return RESULT["access_token"]


def logout():
    """Clear the session from Redis."""
    REDIS.delete(SESSION_KEY)
    logger.info("Logged out — Redis session cleared")

#
# if __name__ == "__main__":
#     token = login()
#     logger.info(f" Ready.")
