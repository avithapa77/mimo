
from skills.light      import LightSkill
from skills.lock       import LockSkill
from skills.thermostat import ThermostatSkill
from config import setup_logging
import logging

setup_logging()
logger = logging.getLogger(__name__)

# ── Registry: device type → skill instance ───────────────────────────────────
REGISTRY = {
    "light":      LightSkill(),
    "lock":       LockSkill(),
    "thermostat": ThermostatSkill(),
}


def execute_skill(device: dict, action: str, params: dict = None) -> dict:
    """
    Route an action to the correct skill based on device type.

    Args:
        device:  Full device row from MySQL
        action:  Action from MiMo (turn_on, turn_off, lock, etc.)
        params:  Optional params (e.g. temperature for set_temp)

    Returns:
        {"success": True/False, "new_state": "...", "message": "..."}
    """
    device_type = device.get("type")
    skill       = REGISTRY.get(device_type)

    if not skill:
        logger.warning(f"[MCP] No skill registered for device type: {device_type}")
        return {
            "success":   False,
            "new_state": device.get("state"),
            "message":   f"No skill available for device type: {device_type}"
        }

    logger.info(f"[MCP] Routing {action} → {device_type} skill ({device['name']})")
    return skill.execute(device, action, params)
