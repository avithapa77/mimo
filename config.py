import os
from dotenv import load_dotenv
import logging
load_dotenv()

MIMO_VERSION = "MiMo v0.1"
CLIENT_ID    = "malati_mobile_v1"

# ── Firebase ──────────────────────────────────────────────────────────────────
FIREBASE_SERVICE_ACCOUNT = os.getenv("FIREBASE_SERVICE_ACCOUNT", "serviceAccountKey.json")
FIREBASE_PROJECT_ID       = os.getenv("FIREBASE_PROJECT_ID", "malati-499506")

# ── Groq ──────────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ── GPS ───────────────────────────────────────────────────────────────────────
MAX_GATEWAY_DISTANCE_KM = 1.0

# ── M5 — MCP Gateway (future Raspberry Pi) ────────────────────────────────────
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000")

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s- [%(filename)s]- %(funcName)s()- %(message)s"
    )
