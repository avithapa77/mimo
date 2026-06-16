"""
mimo.py — MiMo AI with MCP tool calling

MiMo calls MCP tools directly. The AI decides which tool to call
and with what parameters — true MCP usage.
"""

import json
from groq import Groq
from config import GROQ_API_KEY, setup_logging
import logging

setup_logging()
logger = logging.getLogger(__name__)

# ── MCP tool definitions — what MiMo knows it can call ───────────────────────
MIMO_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "turn_on_light",
            "description": "Turn on a smart light",
            "parameters": {
                "type": "object",
                "properties": {
                    "device_id":  {"type": "string", "description": "Device ID e.g. dev_21"},
                    "gateway_id": {"type": "string", "description": "Gateway ID e.g. gw_kathmandu_home2"}
                },
                "required": ["device_id", "gateway_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "turn_off_light",
            "description": "Turn off a smart light",
            "parameters": {
                "type": "object",
                "properties": {
                    "device_id":  {"type": "string"},
                    "gateway_id": {"type": "string"}
                },
                "required": ["device_id", "gateway_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lock_door",
            "description": "Lock a smart door lock",
            "parameters": {
                "type": "object",
                "properties": {
                    "device_id":  {"type": "string"},
                    "gateway_id": {"type": "string"}
                },
                "required": ["device_id", "gateway_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "unlock_door",
            "description": "Unlock a smart door lock",
            "parameters": {
                "type": "object",
                "properties": {
                    "device_id":  {"type": "string"},
                    "gateway_id": {"type": "string"}
                },
                "required": ["device_id", "gateway_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_temperature",
            "description": "Set AC unit temperature in Celsius",
            "parameters": {
                "type": "object",
                "properties": {
                    "device_id":   {"type": "string"},
                    "gateway_id":  {"type": "string"},
                    "temperature": {"type": "integer", "description": "Target temp 16-30°C"}
                },
                "required": ["device_id", "gateway_id", "temperature"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_device_status",
            "description": "Get current state of a device",
            "parameters": {
                "type": "object",
                "properties": {
                    "device_id": {"type": "string"}
                },
                "required": ["device_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_devices",
            "description": "List all devices and their states for a gateway",
            "parameters": {
                "type": "object",
                "properties": {
                    "gateway_id": {"type": "string"}
                },
                "required": ["gateway_id"]
            }
        }
    }
]


def mimo(system_prompt: str, english_command: str) -> list:
    """
    MiMo uses tool calling to pick the right device action.
    Returns list of tool call dicts: [{name, arguments}]
    """
    client = Groq(api_key=GROQ_API_KEY)

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": english_command},
        ],
        tools=MIMO_TOOLS,
        tool_choice="auto",
        temperature=0.1,
        max_tokens=512,
    )

    message = response.choices[0].message
    logger.info(f"[MIMO] finish_reason: {response.choices[0].finish_reason}")

    if message.tool_calls:
        results = []
        for tool_call in message.tool_calls:
            name      = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            logger.info(f"[MIMO] Tool call: {name}({arguments})")
            results.append({"name": name, "arguments": arguments})
        return results

    # Fallback: MiMo responded with text instead of a tool call
    logger.info(f"[MIMO] Text response (no tool call): {message.content}")
    return [{"name": "clarify", "arguments": {"message": message.content}}]
