"""
mimo_mcp_server.py — Real MCP server for MiMo device skills

This exposes  device skills as proper MCP tools that any
MCP-compatible AI (including MiMo via Groq) can discover and call.

python mimo_mcp_server.py
"""

from mcp.server.fastmcp import FastMCP
from db import get_devices, get_device_by_id, update_device_state
from skill_registry import execute_skill
from config import setup_logging
import logging

setup_logging()
logger = logging.getLogger(__name__)

# ── Create the MCP server ─────────────────────────────────────────────────────
mcp = FastMCP("MiMo Smart Home")


# ── Tool 1: Turn on a light ───────────────────────────────────────────────────
@mcp.tool()
def turn_on_light(device_id: str, gateway_id: str) -> str:

    device = get_device_by_id(device_id)
    result = execute_skill(device, "turn_on")
    if result["success"]:
        update_device_state(device_id, result["new_state"])
    logger.info(f"[MCP] turn_on_light: {result['message']}")
    return result["message"]


# ── Tool 2: Turn off a light ──────────────────────────────────────────────────
@mcp.tool()
def turn_off_light(device_id: str, gateway_id: str) -> str:

    device = get_device_by_id(device_id)
    result = execute_skill(device, "turn_off")
    if result["success"]:
        update_device_state(device_id, result["new_state"])
    logger.info(f"[MCP] turn_off_light: {result['message']}")
    return result["message"]


# ── Tool 3: Lock a door ───────────────────────────────────────────────────────
@mcp.tool()
def lock_door(device_id: str, gateway_id: str) -> str:

    device = get_device_by_id(device_id)
    result = execute_skill(device, "lock")
    if result["success"]:
        update_device_state(device_id, result["new_state"])
    logger.info(f"[MCP] lock_door: {result['message']}")
    return result["message"]


# ── Tool 4: Unlock a door ─────────────────────────────────────────────────────
@mcp.tool()
def unlock_door(device_id: str, gateway_id: str) -> str:
    device = get_device_by_id(device_id)
    result = execute_skill(device, "unlock")
    if result["success"]:
        update_device_state(device_id, result["new_state"])
    logger.info(f"[MCP] unlock_door: {result['message']}")
    return result["message"]


# ── Tool 5: Set AC temperature ────────────────────────────────────────────────
@mcp.tool()
def set_temperature(device_id: str, gateway_id: str, temperature: int) -> str:

    device = get_device_by_id(device_id)
    result = execute_skill(device, "set_temp", {"temperature": temperature})
    if result["success"]:
        update_device_state(device_id, result["new_state"])
    logger.info(f"[MCP] set_temperature: {result['message']}")
    return result["message"]


# ── Tool 6: Get device status ─────────────────────────────────────────────────
@mcp.tool()
def get_device_status(device_id: str) -> str:

    device = get_device_by_id(device_id)
    result = execute_skill(device, "status")
    logger.info(f"[MCP] get_device_status: {result['message']}")
    return result["message"]


# ── Tool 7: List all devices for a gateway ────────────────────────────────────
@mcp.tool()
def list_devices(gateway_id: str) -> str:

    devices = get_devices(gateway_id)
    if not devices:
        return f"No devices found for gateway {gateway_id}"

    lines = [f"Devices in {gateway_id}:"]
    for d in devices:
        lines.append(f"  - {d['name']} (id={d['device_id']}, type={d['type']}, state={d['state']})")
    result = "\n".join(lines)
    logger.info(f"[MCP] list_devices: {len(devices)} devices")
    return result


# ── Run the server ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logger.info("[MCP] MiMo MCP server starting (stdio transport)...")
    mcp.run(transport="stdio")
