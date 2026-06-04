import os
from dotenv import load_dotenv
import logging
load_dotenv()

MIMO_VERSION = "MiMo v0.1"
CLIENT_ID    = "malati_mobile_v1"

DB_CONFIG = {
    "user":        os.getenv("DB_USER"),
    "password":    os.getenv("DB_PASSWORD"),
    "database":    os.getenv("DB_NAME"),
    "unix_socket": os.getenv("DB_SOCKET"),
}

MAX_GATEWAY_DISTANCE_KM = 1.0

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - [%(classname)s] - %(levelname)s - %(message)s"
    )

