import json
from config import MIMO_VERSION, setup_logging
from auth import validate_token
from build_mimo_prompt import build_mimo_prompt
from mimo import mimo
from db import get_nearest_gateway, get_devices, get_device_by_id, update_device_state
from google_auth_server import login
from skill_registry import execute_skill
import logging

setup_logging()
logger = logging.getLogger(__name__)

# ── Map MCP tool name → action for skill registry ────────────────────────────
TOOL_ACTION_MAP = {
    "turn_on_light":    "turn_on",
    "turn_off_light":   "turn_off",
    "lock_door":        "lock",
    "unlock_door":      "unlock",
    "set_temperature":  "set_temp",
    "get_device_status":"status",
    "list_devices":     "list",
}


def run_pipeline(english_command: str, token: str, lat: float = None, lng: float = None, gateway_id: str = None):

    logger.info(f"\n{'='*50}\n   {english_command}\n{'='*50}")

    # Auth
    claims  = validate_token(token)
    user_id = claims["sub"]

    # Auto-select gateway from GPS, or use manual override
    if gateway_id is None:
        if lat is None or lng is None:
            raise Exception("Provide either GPS coordinates (lat, lng) or a gateway_id")
        gateway_id = get_nearest_gateway(user_id, lat, lng)
    else:
        logger.info(f"Manual override — using gateway: {gateway_id}")

    system_prompt = build_mimo_prompt(user_id, gateway_id)
    logger.info(f"Loaded {gateway_id}")

    # MiMo decides — now returns tool calls instead of JSON actions
    tool_calls = mimo(system_prompt, english_command)

    # Execute each MCP tool call through the skill registry
    for call in tool_calls:
        tool_name = call["name"]
        args      = call["arguments"]

        logger.info(f"[MCP] Executing tool: {tool_name}({args})")

        # Handle clarify — MiMo wasn't sure what to do
        if tool_name == "clarify":
            logger.info(f"[MCP] MiMo needs clarification: {args.get('message')}")
            continue

        # Handle list_devices — no device action needed
        if tool_name == "list_devices":
            devices = get_devices(args["gateway_id"])
            for d in devices:
                logger.info(f"  {d['name']}: {d['state']}")
            continue

        # Get device and map tool → action
        device_id = args.get("device_id")
        action    = TOOL_ACTION_MAP.get(tool_name)
        params    = {"temperature": args["temperature"]} if "temperature" in args else {}

        if not device_id or not action:
            logger.warning(f"[MCP] Could not resolve tool: {tool_name}")
            continue

        device = get_device_by_id(device_id)

        # Route through skill registry
        result = execute_skill(device, action, params)
        logger.info(f"[SKILL] {result['message']}")

        # Only write to DB if skill succeeded
        if result["success"]:
            update_device_state(device_id, result["new_state"])
        else:
            logger.warning(f"[SKILL] Failed: {result['message']}")

    return tool_calls


if __name__ == "__main__":

    token = login()

    #####################################
    #  Get Real GPS and pass it here
    #####################################

    # Kathmandu home
    run_pipeline("Turn off the living room light", token, lat=27.7172, lng=85.3240)

    # Pokhara house
    run_pipeline("Turn on the garden light", token, lat=28.2096, lng=83.9856)

    # Too far from any home
    try:
        run_pipeline("Turn everything off", token, lat=26.0000, lng=80.0000)
    except Exception as e:
        logger.info(f"[ERROR] {e}")

    # Manual override
    run_pipeline("Is the front door locked?", token, gateway_id="gw_kathmandu_home2")

    # Set AC temperature
    run_pipeline("Set the AC to 22 degrees", token, gateway_id="gw_kathmandu_home2")
