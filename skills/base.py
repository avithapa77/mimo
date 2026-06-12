from abc import ABC, abstractmethod
from config import setup_logging
import logging

setup_logging()
logger = logging.getLogger(__name__)

class BaseSkill(ABC):

    @abstractmethod
    def execute(self, device: dict, action: str, params: dict = None) -> dict:
        """
        Execute an action on a device.

        Args:
            device:  Full device row from MySQL {device_id, name, type, state, gateway_id}
            action:  One of: turn_on, turn_off, lock, unlock, set_temp, status
            params:  Optional extra params e.g. {"temperature": 22}

        Returns:
            {"success": True/False, "new_state": "...", "message": "..."}
        """
        pass

    def status(self, device: dict) -> dict:
        """Default status handler — returns current DB state."""
        return {
            "success":   True,
            "new_state": device["state"],
            "message":   f"{device['name']} is currently {device['state']}"
        }
