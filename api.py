"""


Endpoints:
    GET  /auth/validate      — verify Firebase ID token, upsert user
    GET  /gateways           — list user's homes
    GET  /devices             — list devices for a gateway
    POST /device/action      — manually control a device
    POST /pipeline           — voice command execution
    POST /transcribe         — Nepali audio -> English text
    GET  /health              — health check
"""

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
import logging

from config import setup_logging
from firebase_auth import verify_firebase_token
from firestore import (
    get_or_create_user,
    get_user_gateways,
    get_devices,
    get_device_by_id,
    get_nearest_gateway,
    update_device_state,
)
from skill_registry import execute_skill
from build_mimo_prompt import build_mimo_prompt
from mimo import mimo
from transcribe import transcribe_audio

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Malati API", version="M4-firebase")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Verifies the Firebase ID token and upserts the user in Firestore.
    Raises 401 if token is missing, expired, or invalid.
    """
    try:
        decoded = verify_firebase_token(credentials.credentials)
        user    = get_or_create_user(decoded["uid"], decoded["email"], decoded["name"])
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


# ── Request models ─────────────────────────────────────────────────────────────

class DeviceActionRequest(BaseModel):
    device_id: str
    action:    str
    params:    Optional[dict] = {}

class PipelineRequest(BaseModel):
    command:    str
    gateway_id: Optional[str] = None
    lat:        Optional[float] = None
    lng:        Optional[float] = None


# ── GET /auth/validate ────────────────────────────────────────────────────────
@app.get("/auth/validate")
def auth_validate(user: dict = Depends(get_current_user)):
    """
    Verify the Firebase ID token is valid and return the user profile.
    Called by the Splash screen on app open.

    Request:  Authorization: Bearer <firebase_id_token>
    Response: { "valid": true, "user": { uid, email, name } }
    """
    logger.info(f"[API] /auth/validate — user: {user.get('uid')}")
    return {
        "valid": True,
        "user": {
            "uid":   user.get("uid"),
            "email": user.get("email"),
            "name":  user.get("name"),
        }
    }


# ── GET /gateways ─────────────────────────────────────────────────────────────
@app.get("/gateways")
def get_gateways_endpoint(user: dict = Depends(get_current_user)):
    """
    List all gateways (homes) for the logged-in user.
    Called by the Profile screen to populate the gateway switcher.

    Response: [ { gateway_id, label, lat, lng } ]
    """
    try:
        gateway_list = get_user_gateways(user["uid"])
        logger.info(f"[API] /gateways — {len(gateway_list)} for {user['uid']}")
        return gateway_list
    except Exception as e:
        logger.error(f"[API] /gateways failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── GET /devices ──────────────────────────────────────────────────────────────
@app.get("/devices")
def get_devices_endpoint(gateway_id: str, user: dict = Depends(get_current_user)):
    """
    List all devices for a gateway with current states.
    Called by the Devices screen

    Query param: ?gateway_id=gw_kathmandu_home
    Response: [ { device_id, name, type, state, gateway_id } ]
    """
    try:
        devices = get_devices(gateway_id)
        logger.info(f"[API] /devices — {len(devices)} for {gateway_id}")
        return devices
    except Exception as e:
        logger.error(f"[API] /devices failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── POST /device/action ───────────────────────────────────────────────────────
@app.post("/device/action")
def device_action(body: DeviceActionRequest, user: dict = Depends(get_current_user)):
    """
    Manually control a device from the Device Detail screen.
    Routes through the skill registry — same as the pipeline.

    Request:  { "device_id": "dev_21", "action": "turn_off", "params": {} }
    Response: { "success": true, "new_state": "off", "message": "Light turned off" }
    """
    try:
        device = get_device_by_id(body.device_id)
        result = execute_skill(device, body.action, body.params)
        logger.info(f"[API] /device/action — {body.action} on {body.device_id}: {result['message']}")

        if result["success"]:
            update_device_state(body.device_id, result["new_state"])

        return result
    except Exception as e:
        logger.error(f"[API] /device/action failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── POST /pipeline ────────────────────────────────────────────────────────────
@app.post("/pipeline")
def pipeline_endpoint(body: PipelineRequest, user: dict = Depends(get_current_user)):
    """
    Main voice command endpoint.
    Accepts a natural language command, runs the full MiMo pipeline,
    executes device actions, returns results.

    Request:  { "command": "Turn off the light", "gateway_id": "...", "lat": 27.7172, "lng": 85.3240 }
    Response: [ { "tool": "turn_off_light", "result": "Living Room Light turned off" } ]
    """
    try:
        uid        = user["uid"]
        gateway_id = body.gateway_id

        if gateway_id is None:
            if body.lat is None or body.lng is None:
                raise HTTPException(
                    status_code=400,
                    detail="Provide either gateway_id or lat/lng coordinates"
                )
            gateway_id = get_nearest_gateway(uid, body.lat, body.lng)

        logger.info(f"[API] /pipeline — command: '{body.command}' gateway: {gateway_id}")

        system_prompt = build_mimo_prompt(uid, gateway_id)
        tool_calls    = mimo(system_prompt, body.command)

        devices    = get_devices(gateway_id)
        device_map = {d["device_id"]: d for d in devices}

        results = []
        TOOL_ACTION_MAP = {
            "turn_on_light":    "turn_on",
            "turn_off_light":   "turn_off",
            "lock_door":        "lock",
            "unlock_door":      "unlock",
            "set_temperature":  "set_temp",
            "get_device_status":"status",
        }

        for call in tool_calls:
            tool_name = call["name"]
            args      = call["arguments"]

            if tool_name == "clarify":
                results.append({"tool": "clarify", "result": args.get("message")})
                continue

            if tool_name == "list_devices":
                lines = [f"{d['name']}: {d['state']}" for d in devices]
                results.append({"tool": "list_devices", "result": "\n".join(lines)})
                continue

            device_id = args.get("device_id")
            action    = TOOL_ACTION_MAP.get(tool_name)
            params    = {"temperature": args["temperature"]} if "temperature" in args else {}

            if not device_id or not action:
                continue

            device = device_map.get(device_id)
            if not device:
                continue

            skill_result = execute_skill(device, action, params)

            if skill_result["success"]:
                update_device_state(device_id, skill_result["new_state"])

            results.append({
                "tool":    tool_name,
                "result":  skill_result["message"],
                "success": skill_result["success"],
            })

        logger.info(f"[API] /pipeline complete — {len(results)} actions")
        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] /pipeline failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── POST /transcribe ──────────────────────────────────────────────────────────
@app.post("/transcribe")
async def transcribe_endpoint(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user)
):
    """
    Transcribe a Nepali audio file and return English translation.
    The mobile app should then pass "english" to POST /pipeline as the command.

    Request:  multipart/form-data, field "file" = audio (wav/mp3/m4a/webm/ogg/flac, max 25MB)
    Response: { "nepali": "...", "english": "..." }
    """
    try:
        allowed = {".wav", ".mp3", ".m4a", ".webm", ".ogg", ".flac"}
        ext = "." + file.filename.split(".")[-1].lower() if "." in file.filename else ".wav"
        if ext not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {ext}. Use wav, mp3, m4a, webm, ogg, or flac."
            )

        audio_bytes = await file.read()

        if len(audio_bytes) == 0:
            raise HTTPException(status_code=400, detail="Audio file is empty")

        if len(audio_bytes) > 25 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Audio file too large. Max 25MB.")

        logger.info(f"[API] /transcribe — file: {file.filename}, size: {len(audio_bytes)} bytes, user: {user.get('uid')}")

        result = transcribe_audio(audio_bytes, file.filename)

        logger.info(f"[API] /transcribe — english: '{result['english']}'")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] /transcribe failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    """Quick check that the server is running."""
    return {"status": "ok", "version": "M4-firebase"}
