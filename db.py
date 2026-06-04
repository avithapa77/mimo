import secrets
import mysql.connector
from math import radians, cos, sin, asin, sqrt
from datetime import datetime, timedelta
from config import DB_CONFIG, MAX_GATEWAY_DISTANCE_KM,setup_logging
import logging

setup_logging()
logger = logging.getLogger(__name__)

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)

def get_user(user_id: str) -> dict:
    conn = get_connection()
    cur  = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    user = cur.fetchone()
    conn.close()
    if not user:
        raise Exception(f"User {user_id} not found")
    return user

def get_gateway(gateway_id: str) -> dict:
    conn = get_connection()
    cur  = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM gateways WHERE gateway_id = %s", (gateway_id,))
    gateway = cur.fetchone()
    conn.close()
    if not gateway:
        raise Exception(f"Gateway {gateway_id} not found")
    return gateway

def get_devices(gateway_id: str) -> list:
    conn = get_connection()
    cur  = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM devices WHERE gateway_id = %s", (gateway_id,))
    devices = cur.fetchall()
    conn.close()
    return devices

def update_device_state(device_id: str, new_state: str):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(
        "UPDATE devices SET state = %s WHERE device_id = %s",
        (new_state, device_id)
    )
    conn.commit()
    conn.close()
    logger.info(f" {device_id} → {new_state}")

def haversine(lat1, lng1, lat2, lng2) -> float:
    R = 6371
    lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
    a = sin((lat2-lat1)/2)**2 + cos(lat1)*cos(lat2)*sin((lng2-lng1)/2)**2
    return R * 2 * asin(sqrt(a))

def get_nearest_gateway(user_id: str, lat: float, lng: float) -> str:
    conn = get_connection()
    cur  = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM gateways WHERE user_id = %s", (user_id,))
    gateways = cur.fetchall()
    conn.close()

    if not gateways:
        raise Exception(f"No gateways registered for user {user_id}")

    nearest  = min(gateways, key=lambda g: haversine(lat, lng, float(g["lat"]), float(g["lng"])))
    distance = haversine(lat, lng, float(nearest["lat"]), float(nearest["lng"]))

    logger.info(f"[GPS] Nearest: {nearest['label']} — {distance:.2f}km away")

    if distance > MAX_GATEWAY_DISTANCE_KM:
        raise Exception(
            f"You are {distance:.1f}km from your nearest home ({nearest['label']}). "
            f"Please select a gateway manually."
        )

    return nearest["gateway_id"]


def create_session(user_id: str) -> str:
    """Generate a refresh token and store it in DB. Returns the token."""
    refresh_token = secrets.token_urlsafe(64)
    expires_at    = datetime.now() + timedelta(days=30)

    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(
        "INSERT INTO sessions (refresh_token, user_id, expires_at) VALUES (%s, %s, %s)",
        (refresh_token, user_id, expires_at)
    )
    conn.commit()
    conn.close()
    logger.info(f" Created for {user_id}, expires {expires_at.date()}")
    return refresh_token

def get_session(refresh_token: str) -> dict:
    """Look up a refresh token. Raises if invalid or expired."""
    conn = get_connection()
    cur  = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM sessions WHERE refresh_token = %s", (refresh_token,))
    session = cur.fetchone()
    conn.close()

    if not session:
        raise Exception("Invalid refresh token")
    if session["expires_at"] < datetime.now():
        raise Exception("Refresh token expired — please log in again")
    return session

def delete_session(refresh_token: str):
    """Delete a session (logout)."""
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("DELETE FROM sessions WHERE refresh_token = %s", (refresh_token,))
    conn.commit()
    conn.close()
    logger.info(f"[SESSION] Deleted")
