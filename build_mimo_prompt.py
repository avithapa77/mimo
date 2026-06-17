"""
build_mimo_prompt.py — Builds the system prompt for MiMo
"""

from config import CLIENT_ID, setup_logging
from firestore import get_user, get_gateway, get_devices
import logging

setup_logging()
logger = logging.getLogger(__name__)

def build_mimo_prompt(uid: str, gateway_id: str) -> str:
    logger.info("Building MiMo Prompt")
    user    = get_user(uid)
    gateway = get_gateway(gateway_id)
    devices = get_devices(gateway_id)

    devices_str = "\n".join(
        f"  - {d['name']} (id={d['device_id']}, type={d['type']}, state={d['state']})"
        for d in devices
    )

    return f"""You are MiMo, a smart home assistant for Nepali households.

USER: {user['name']} | App: {CLIENT_ID} | Gateway: {gateway['label']} ({gateway_id})

DEVICES:
{devices_str}

When the user gives a command, call the appropriate tool to control the device.
Always use the gateway_id "{gateway_id}" when calling tools that require it.
Only use device IDs listed above. If the request is unclear or no matching device exists, do not call a tool — instead respond with a clarifying question."""
