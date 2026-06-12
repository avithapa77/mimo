"""
skills/lock.py — Lock skill (simulated)

Simulates a smart lock (Tuya / ZigBee).
To go real: replace simulated calls with actual SDK.
"""

from skills.base import BaseSkill
from config import setup_logging
import logging

setup_logging()
logger = logging.getLogger(__name__)

class LockSkill(BaseSkill):

    VALID_ACTIONS = {"lock", "unlock", "status"}

    def execute(self, device: dict, action: str, params: dict = None) -> dict:
        name = device["name"]

        if action not in self.VALID_ACTIONS:
            return {
                "success":   False,
                "new_state": device["state"],
                "message":   f"Lock does not support action: {action}"
            }

        if action == "status":
            return self.status(device)

        if action == "lock":
            # ── SIMULATED ──────────────────────────────────────────
            # Real Tuya lock would be:
            #   import tinytuya
            #   d = tinytuya.Device(device["external_id"], ...)
            #   d.set_value("lock", True)
            # ───────────────────────────────────────────────────────
            logger.info(f"[LOCK] [SIMULATED] Locking — {name}")
            return {
                "success":   True,
                "new_state": "locked",
                "message":   f"{name} locked"
            }

        if action == "unlock":
            logger.info(f"[LOCK] [SIMULATED] Unlocking — {name}")
            return {
                "success":   True,
                "new_state": "unlocked",
                "message":   f"{name} unlocked"
            }
