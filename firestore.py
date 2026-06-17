"""
firestore.py — Replaces db.py

All MySQL calls replaced with Firestore.
No more sessions table — Firebase Auth handles sessions on the client.

Collections:
    users/{uid}            — name, email, created_at
    gateways/{gateway_id}  — user_id, label, lat, lng
    devices/{device_id}    — gateway_id, name, type, state

Init pattern handles both environments:
    Local dev  — uses serviceAccountKey.json
    Cloud Run  — uses the attached service account automatically
"""

import os
import firebase_admin
from firebase_admin import credentials, firestore
from math import radians, cos, sin, asin, sqrt
from config import setup_logging, FIREBASE_SERVICE_ACCOUNT, MAX_GATEWAY_DISTANCE_KM
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

db = firestore.client()


# ── Users ─────────────────────────────────────────────────────────────────────

def get_or_create_user(uid: str, email: str, name: str) -> dict:
    """Get user from Firestore, or create them on first login."""
    doc_ref = db.collection("users").document(uid)
    doc     = doc_ref.get()

    if doc.exists:
        return {"uid": uid, **doc.to_dict()}

    from datetime import datetime
    user = {
        "name":       name,
        "email":      email,
        "created_at": datetime.utcnow().isoformat(),
    }
    doc_ref.set(user)
    logger.info(f"Created new user {uid} — {email}")
    return {"uid": uid, **user}


def get_user(uid: str) -> dict:
    doc = db.collection("users").document(uid).get()
    if not doc.exists:
        raise Exception(f"User {uid} not found")
    return {"uid": uid, **doc.to_dict()}


# ── Gateways ──────────────────────────────────────────────────────────────────

def get_gateway(gateway_id: str) -> dict:
    doc = db.collection("gateways").document(gateway_id).get()
    if not doc.exists:
        raise Exception(f"Gateway {gateway_id} not found")
    return {"gateway_id": gateway_id, **doc.to_dict()}


def get_user_gateways(uid: str) -> list:
    docs = db.collection("gateways").where("user_id", "==", uid).stream()
    gateways = [{"gateway_id": d.id, **d.to_dict()} for d in docs]
    if not gateways:
        raise Exception(f"No gateways registered for user {uid}")
    return gateways


# ── Devices ───────────────────────────────────────────────────────────────────

def get_devices(gateway_id: str) -> list:
    docs = db.collection("devices").where("gateway_id", "==", gateway_id).stream()
    return [{"device_id": d.id, **d.to_dict()} for d in docs]


def get_device_by_id(device_id: str) -> dict:
    doc = db.collection("devices").document(device_id).get()
    if not doc.exists:
        raise Exception(f"Device {device_id} not found")
    return {"device_id": device_id, **doc.to_dict()}


def update_device_state(device_id: str, new_state: str):
    db.collection("devices").document(device_id).update({"state": new_state})
    logger.info(f"{device_id} -> {new_state}")


# ── GPS ───────────────────────────────────────────────────────────────────────

def haversine(lat1, lng1, lat2, lng2) -> float:
    R = 6371
    lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
    a = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lng2 - lng1) / 2) ** 2
    return R * 2 * asin(sqrt(a))


def get_nearest_gateway(uid: str, lat: float, lng: float) -> str:
    gateways = get_user_gateways(uid)
    nearest  = min(gateways, key=lambda g: haversine(lat, lng, float(g["lat"]), float(g["lng"])))
    distance = haversine(lat, lng, float(nearest["lat"]), float(nearest["lng"]))

    logger.info(f"[GPS] Nearest: {nearest['label']} — {distance:.2f}km away")

    if distance > MAX_GATEWAY_DISTANCE_KM:
        raise Exception(
            f"You are {distance:.1f}km from your nearest home ({nearest['label']}). "
            f"Please select a gateway manually."
        )
    return nearest["gateway_id"]
