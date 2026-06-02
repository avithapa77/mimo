from config import CLIENT_ID
from db import get_user, get_gateway, get_devices

def build_mimo_prompt(user_id: str, gateway_id: str) -> str:
    user    = get_user(user_id)
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

Reply ONLY with valid JSON — no markdown, no extra text.
Format: {{"action": "<action>", "device_id": "<id>", "explanation": "<one sentence>"}}
Valid actions: turn_on, turn_off, lock, unlock, set_temp, status, clarify
Only use device IDs listed above. If unclear, use action=clarify."""
