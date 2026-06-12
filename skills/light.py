"""
skills/light.py — Light skill (simulated)

Simulates a smart light (Philips Hue / Tuya).
To go real: replace the simulated calls with the actual SDK.

Philips Hue:   pip install phue
Tuya:          pip install tinytuya
"""

from skills.base import BaseSkill
from config import setup_logging
import logging

setup_logging()
logger = logging.getLogger(__name__)

class LightSkill(BaseSkill):

    VALID_ACTIONS = {"turn_on", "turn_off", "status"}

    def execute(self, device: dict, action: str, params: dict = None) -> dict:
        name = device["name"]

        if action not in self.VALID_ACTIONS:
            return {
                "success":   False,
                "new_state": device["state"],
                "message":   f"Light does not support action: {action}"
            }

        if action == "status":
            return self.status(device)

        if action == "turn_on":
            # ── SIMULATED ──────────────────────────────────────────
            # Real Philips Hue would be:
            #   from phue import Bridge
            #   b = Bridge(HUE_BRIDGE_IP)
            #   b.set_light(device["external_id"], "on", True)
            #
            # Real Tuya would be:
            #   import tinytuya
            #   d = tinytuya.OutletDevice(device["external_id"], ...)
            #   d.turn_on()
            # ───────────────────────────────────────────────────────
            logger.info(f"[LIGHT] [SIMULATED] Turning ON — {name}")
            return {
                "success":   True,
                "new_state": "on",
                "message":   f"{name} turned on"
            }

        if action == "turn_off":
            logger.info(f"[LIGHT] [SIMULATED] Turning OFF — {name}")
            return {
                "success":   True,
                "new_state": "off",
                "message":   f"{name} turned off"
            }
