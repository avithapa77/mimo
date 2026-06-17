"""
firebase_auth.py — Replaces auth.py

Firebase Admin SDK verifies ID tokens sent from the React Native app.
No more JWT_SECRET, no more issue_jwt(), no more refresh token logic —
Firebase handles all of that on the client side.

Init pattern handles both environments:
    Local dev  — uses serviceAccountKey.json
    Cloud Run  — uses the attached service account automatically
"""

import os
import firebase_admin
from firebase_admin import auth, credentials
from config import setup_logging, FIREBASE_SERVICE_ACCOUNT
import logging

setup_logging()
logger = logging.getLogger(__name__)

# ── Initialize Firebase Admin SDK once ────────────────────────────────────────
if not firebase_admin._apps:
    if os.path.exists(FIREBASE_SERVICE_ACCOUNT):
        # Local dev — use the JSON key file
        cred = credentials.Certificate(FIREBASE_SERVICE_ACCOUNT)
        firebase_admin.initialize_app(cred)
        logger.info("Firebase initialized with service account file (local dev)")
    else:
        # Cloud Run — use the attached service account automatically
        firebase_admin.initialize_app()
        logger.info("Firebase initialized with default credentials (Cloud Run)")


def verify_firebase_token(id_token: str) -> dict:
    """
    Verify a Firebase ID token sent from the mobile app.
    Replaces validate_token() from auth.py.

    Returns:
        { "uid": "...", "email": "...", "name": "..." }

    Raises:
        Exception if token is invalid, expired, or tampered with
    """
    try:
        decoded = auth.verify_id_token(id_token)
        logger.info(f"Verified Firebase token for {decoded.get('email')}")
        return {
            "uid":   decoded["uid"],
            "email": decoded.get("email"),
            "name":  decoded.get("name", ""),
        }
    except auth.ExpiredIdTokenError:
        raise Exception("Firebase token expired — user must re-authenticate")
    except auth.InvalidIdTokenError:
        raise Exception("Invalid Firebase token")
    except Exception as e:
        raise Exception(f"Token verification failed: {e}")
