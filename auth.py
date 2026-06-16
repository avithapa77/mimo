import jwt
import time
import httpx
from urllib.parse import urlencode
from config import (CLIENT_ID, JWT_SECRET, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI,
                    setup_logging, GOOGLE_AUTH_URL, GOOGLE_TOKEN_URL, GOOGLE_USERINFO_URL)
from db import create_session, get_session, get_user, get_connection
import logging

setup_logging()
logger = logging.getLogger(__name__)


# ── Step 1: Build the Google redirect URL ────────────────────────────────────
def get_google_auth_url(state: str = "") -> str:
    params = {
        "client_id":     GOOGLE_CLIENT_ID,
        "redirect_uri":  GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope":         "openid email profile",
        "access_type":   "offline",
        "prompt":        "select_account",
    }
    if state:
        params["state"] = state
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


# ── Step 2: Exchange Google code → user info ─────────────────────────────────
def _exchange_code_for_user(code: str) -> dict:
    token_resp = httpx.post(GOOGLE_TOKEN_URL, data={
        "code":          code,
        "client_id":     GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri":  GOOGLE_REDIRECT_URI,
        "grant_type":    "authorization_code",
    })
    token_resp.raise_for_status()
    tokens = token_resp.json()

    userinfo_resp = httpx.get(GOOGLE_USERINFO_URL, headers={
        "Authorization": f"Bearer {tokens['access_token']}"
    })
    userinfo_resp.raise_for_status()
    return userinfo_resp.json()


# ── Step 3: Issue a short-lived JWT access token ─────────────────────────────
def issue_jwt(user_id: str, extra_claims: dict = None) -> str:
    payload = {
        "sub":       user_id,
        "client_id": CLIENT_ID,
        "iat":       int(time.time()),
        "exp":       int(time.time()) + 3600,  # 1 hour
    }
    if extra_claims:
        payload.update(extra_claims)
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    logger.info(f"Access token issued for {user_id}")
    return token


# ── Step 4: Handle Google callback — upsert user, issue tokens ───────────────
def handle_google_callback(code: str) -> dict:
    user_info = _exchange_code_for_user(code)

    user_id = user_info.get("sub")
    email   = user_info.get("email")
    name    = user_info.get("name")

    if not user_id:
        raise Exception("Google did not return a user ID")

    logger.info(f"Google login — {email} ({name})")

    # Insert user if they don't exist yet (first-time Google login)
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT IGNORE INTO users (user_id, name) VALUES (%s, %s)",
            (user_id, name)
        )
        conn.commit()
        logger.info(f"User upserted: {user_id}")
    finally:
        conn.close()

    access_token  = issue_jwt(user_id, extra_claims={"email": email, "name": name})
    refresh_token = create_session(user_id)

    return {
        "access_token":  access_token,
        "refresh_token": refresh_token,
    }


# ── Step 5: Use refresh token to get a new access token ──────────────────────
def refresh_access_token(refresh_token: str) -> str:
    session = get_session(refresh_token)
    user_id = session["user_id"]
    user    = get_user(user_id)

    access_token = issue_jwt(user_id, extra_claims={"name": user["name"]})
    logger.info(f"Access token refreshed for {user_id}")
    return access_token


# ── Step 6: Validate access token ────────────────────────────────────────────
def validate_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        logger.info(f"Valid — user: {payload['sub']}, client: {payload['client_id']}")
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception("Token expired")
    except jwt.InvalidTokenError:
        raise Exception("Invalid token")
