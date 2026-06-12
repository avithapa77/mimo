"""
skills/thermostat.py — Thermostat / AC skill (simulated)

Simulates a smart AC unit (Tuya / IR blaster).
To go real: replace simulated calls with actual SDK.
"""

from skills.base import BaseSkill
from config import setup_logging
import logging

setup_logging()
logger = logging.getLogger(__name__)

class ThermostatSkill(BaseSkill):

    VALID_ACTIONS = {"turn_on", "turn_off", "set_temp", "status"}
    MIN_TEMP = 16
    MAX_TEMP = 30

    def execute(self, device: dict, action: str, params: dict = None) -> dict:
        name   = device["name"]
        params = params or {}

        if action not in self.VALID_ACTIONS:
            return {
                "success":   False,
                "new_state": device["state"],
                "message":   f"Thermostat does not support action: {action}"
            }

        if action == "status":
            return self.status(device)

        if action == "turn_on":
            logger.info(f"[THERMOSTAT] [SIMULATED] Turning ON — {name}")
            return {
                "success":   True,
                "new_state": "on",
                "message":   f"{name} turned on"
            }

        if action == "turn_off":
            logger.info(f"[THERMOSTAT] [SIMULATED] Turning OFF — {name}")
            return {
                "success":   True,
                "new_state": "off",
                "message":   f"{name} turned off"
            }

        if action == "set_temp":
            temp = params.get("temperature")
            if temp is None:
                return {
                    "success":   False,
                    "new_state": device["state"],
                    "message":   "set_temp requires a temperature parameter"
                }
            if not (self.MIN_TEMP <= int(temp) <= self.MAX_TEMP):
                return {
                    "success":   False,
                    "new_state": device["state"],
                    "message":   f"Temperature must be between {self.MIN_TEMP} and {self.MAX_TEMP}°C"
                }
            # ── SIMULATED ──────────────────────────────────────────
            # Real Tuya AC would be:
            #   d.set_value("temp_set", int(temp))
            # ───────────────────────────────────────────────────────
            logger.info(f"[THERMOSTAT] [SIMULATED] Setting temp to {temp}°C — {name}")
            return {
                "success":   True,
                "new_state": f"on:{temp}C",
                "message":   f"{name} set to {temp}°C"
            }
