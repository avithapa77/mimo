"""
auth.py — Google OAuth 2.0 login + JWT issuance
Replaces fake_login.py with real Google authentication.

Flow:
  1. Redirect user to Google via get_google_auth_url()
  2. Google redirects back with ?code=...
  3. Call handle_google_callback(code) → returns your JWT
  4. Validate future requests with validate_token(token)

Required env vars (or config.py):
  CLIENT_ID        — your app's JWT client ID (unchanged from fake_login)
  JWT_SECRET       — your JWT signing secret (unchanged)
  GOOGLE_CLIENT_ID — from Google Cloud Console
  GOOGLE_CLIENT_SECRET
  GOOGLE_REDIRECT_URI — must match what's registered in Google Cloud Console
"""

import jwt
import time
import httpx
from urllib.parse import urlencode
from config import CLIENT_ID, JWT_SECRET, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI

# ── Google OAuth endpoints ────────────────────────────────────────────────────
GOOGLE_AUTH_URL  = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


# ── Step 1: Build the Google redirect URL ────────────────────────────────────
def get_google_auth_url(state: str = "") -> str:
    """
    Return the URL to redirect the user to for Google sign-in.
    
    Usage (Flask example):
        from flask import redirect
        return redirect(get_google_auth_url(state="csrf-token-here"))
    """
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


# ── Step 2: Exchange code → Google tokens → user info ────────────────────────
def _exchange_code_for_user(code: str) -> dict:
    """Exchange Google auth code for user profile info."""
    # Exchange code for tokens
    token_resp = httpx.post(GOOGLE_TOKEN_URL, data={
        "code":          code,
        "client_id":     GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri":  GOOGLE_REDIRECT_URI,
        "grant_type":    "authorization_code",
    })
    token_resp.raise_for_status()
    tokens = token_resp.json()

    # Fetch user info using the access token
    userinfo_resp = httpx.get(GOOGLE_USERINFO_URL, headers={
        "Authorization": f"Bearer {tokens['access_token']}"
    })
    userinfo_resp.raise_for_status()
    return userinfo_resp.json()


# ── Step 3: Issue your own JWT (same structure as fake_login.py) ──────────────
def issue_jwt(user_id: str, extra_claims: dict = None) -> str:
    """
    Issue a signed JWT for the given user_id.
    Mirrors fake_login.fake_login() — drop-in compatible.
    """
    payload = {
        "sub":       user_id,
        "client_id": CLIENT_ID,
        "iat":       int(time.time()),
        "exp":       int(time.time()) + 60 * 60 * 24 *30  # 30 days
    }
    if extra_claims:
        payload.update(extra_claims)

    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    print(f"[AUTH] Token issued for {user_id}")
    return token


# ── Combined callback handler ─────────────────────────────────────────────────
def handle_google_callback(code: str) -> str:
    """
    Call this with the ?code= value Google sends to your redirect URI.
    Returns a signed JWT for your application.

    Usage (Flask example):
        from flask import request
        code = request.args.get("code")
        token = handle_google_callback(code)
    """
    user_info = _exchange_code_for_user(code)

    user_id = user_info.get("sub")           # Google's unique user ID
    email   = user_info.get("email")
    name    = user_info.get("name")

    if not user_id:
        raise Exception("Google did not return a user ID")

    print(f"[AUTH] Google login successful — {email} ({name})")

    # Issue JWT with optional extra claims you may find useful
    return issue_jwt(user_id, extra_claims={
        "email": email,
        "name":  name,
    })


# ── Token validation (unchanged from fake_login.py) ───────────────────────────
def validate_token(token: str) -> dict:
    """Validate a JWT. Raises on expiry or tampering."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        print(f"[AUTH] Valid — user: {payload['sub']}, client: {payload['client_id']}")
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception("Token expired")
    except jwt.InvalidTokenError:
        raise Exception("Invalid token")
