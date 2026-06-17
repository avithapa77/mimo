"""
seed_firestore.py — One-time script to seed test gateways and devices

Run once after creating your Firebase project:
    python seed_firestore.py YOUR_FIREBASE_UID

Get YOUR_FIREBASE_UID from Firebase Console -> Authentication -> Users
after signing in once from the app.
"""

import sys
import firebase_admin
from firebase_admin import credentials, firestore
from config import FIREBASE_SERVICE_ACCOUNT

if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_SERVICE_ACCOUNT)
    firebase_admin.initialize_app(cred)

db = firestore.client()


def seed(uid: str):
    # Gateways
    db.collection("gateways").document("gw_kathmandu_home").set({
        "user_id": uid, "label": "Kathmandu Home", "lat": 27.7172, "lng": 85.3240
    })
    db.collection("gateways").document("gw_pokhara_house").set({
        "user_id": uid, "label": "Pokhara House", "lat": 28.2096, "lng": 83.9856
    })

    # Devices — Kathmandu
    db.collection("devices").document("dev_01").set({
        "gateway_id": "gw_kathmandu_home", "name": "Living Room Light", "type": "light", "state": "on"
    })
    db.collection("devices").document("dev_02").set({
        "gateway_id": "gw_kathmandu_home", "name": "Front Door Lock", "type": "lock", "state": "locked"
    })
    db.collection("devices").document("dev_03").set({
        "gateway_id": "gw_kathmandu_home", "name": "AC Unit", "type": "thermostat", "state": "off"
    })

    # Devices — Pokhara
    db.collection("devices").document("dev_10").set({
        "gateway_id": "gw_pokhara_house", "name": "Garden Light", "type": "light", "state": "off"
    })
    db.collection("devices").document("dev_11").set({
        "gateway_id": "gw_pokhara_house", "name": "Main Gate", "type": "lock", "state": "locked"
    })

    print(f"Seeded gateways and devices for user {uid}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python seed_firestore.py <firebase_uid>")
        sys.exit(1)
    seed(sys.argv[1])
