import json
from config import MIMO_VERSION
from fake_login import fake_login, validate_token
from build_mimo_prompt import build_mimo_prompt
from mimo import mimo
from db import get_nearest_gateway, update_device_state

def run_pipeline(english_command: str, lat: float = None, lng: float = None, gateway_id: str = None):
    print(f"\n{'='*50}\n  {MIMO_VERSION} | {english_command}\n{'='*50}")

    # Step 3 — Auth
    token   = fake_login("user_001")
    claims  = validate_token(token)
    user_id = claims["sub"]

    # Step 4 — Auto-select gateway from GPS, or use manual override
    if gateway_id is None:
        if lat is None or lng is None:
            raise Exception("Provide either GPS coordinates (lat, lng) or a gateway_id")
        gateway_id = get_nearest_gateway(user_id, lat, lng)
    else:
        print(f"[GPS] Manual override — using gateway: {gateway_id}")

    system_prompt = build_mimo_prompt(user_id, gateway_id)
    print(f"[PROFILE] Loaded {gateway_id}")

    # MiMo decides
    results = mimo(system_prompt, english_command)

    # Write state changes back to MySQL
    state_map = {
        "turn_on":  "on",
        "turn_off": "off",
        "lock":     "locked",
        "unlock":   "unlocked",
    }
    for result in results:
        print(f"[ACTION]\n{json.dumps(result, indent=2)}")
        action    = result.get("action")
        device_id = result.get("device_id")
        if action in state_map and device_id:
            update_device_state(device_id, state_map[action])

    return results

if __name__ == "__main__":
    # Simulate user standing in Kathmandu (GPS auto-selects gw_kathmandu_home)
    run_pipeline("Turn off the living room light", lat=27.7172, lng=85.3240)

    # Simulate user standing in Pokhara (GPS auto-selects gw_pokhara_house)
    run_pipeline("Turn on the garden light", lat=28.2096, lng=83.9856)

    # Simulate user far from any home (raises exception)
    try:
        run_pipeline("Turn everything off", lat=26.0000, lng=80.0000)
    except Exception as e:
        print(f"[ERROR] {e}")

    # Manual override — no GPS needed
    run_pipeline("Is the front door locked?", gateway_id="gw_kathmandu_home")
