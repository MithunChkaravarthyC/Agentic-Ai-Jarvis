import os
import sys
import json
import logging
import asyncio
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.config import (
    STATIC_DIR,
    SCREENSHOTS_DIR,
    AUDIO_DIR,
    GENERATED_PROJECTS_DIR,
    MODEL_ROUTING,
    HOST,
    PORT
)
from backend.ollama_client import ollama_client
from backend.agents.jarvis_orchestrator import jarvis_orchestrator
from backend.agents.booking_agent import booking_agent
from backend.agents.tts_agent import tts_agent
from backend.tools.process_manager import process_manager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("JarvisServer")

app = FastAPI(title="JARVIS Multi-Agent AI System", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    """Prime neural models and warmup Kokoro-82M on server start."""
    try:
        asyncio.create_task(asyncio.to_thread(tts_agent.warmup))
    except Exception as e:
        logger.warning(f"Startup warmup note: {e}")

# Mount screenshots, audio, generated projects, and static frontend assets
app.mount("/screenshots", StaticFiles(directory=str(SCREENSHOTS_DIR)), name="screenshots")
app.mount("/audio", StaticFiles(directory=str(AUDIO_DIR)), name="audio")
app.mount("/projects", StaticFiles(directory=str(GENERATED_PROJECTS_DIR)), name="projects")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

class ChatRequest(BaseModel):
    message: str

class PaymentActionRequest(BaseModel):
    action: str  # "confirm" or "cancel"

class TTSRequest(BaseModel):
    text: str
    voice: str = None

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return HTMLResponse("<h2>JARVIS Dashboard loading...</h2>")

@app.get("/api/status")
async def get_system_status():
    ollama_info = await ollama_client.check_health()
    running_apps = process_manager.list_running()
    return {
        "status": "online",
        "models_configured": MODEL_ROUTING,
        "ollama": ollama_info,
        "tts": tts_agent.get_status(),
        "active_web_apps": running_apps,
        "pending_confirmation": booking_agent.pending_confirmation
    }

@app.post("/api/tts")
async def synthesize_speech(payload: TTSRequest):
    """REST endpoint for text-to-speech synthesis using Kokoro-82M."""
    tts_agent.cleanup_old_audio()
    result = await tts_agent.synthesize(payload.text, voice=payload.voice)
    return result

@app.post("/api/chat")
async def post_chat(payload: ChatRequest):
    response = await jarvis_orchestrator.handle_user_input(payload.message)
    return response

@app.post("/api/payment_action")
async def handle_payment(payload: PaymentActionRequest):
    if payload.action == "confirm":
        return booking_agent.confirm_payment()
    return booking_agent.cancel_payment()

@app.get("/api/projects")
async def list_projects():
    projects = []
    if GENERATED_PROJECTS_DIR.exists():
        for p in GENERATED_PROJECTS_DIR.iterdir():
            if p.is_dir():
                files = [f.name for f in p.iterdir()]
                projects.append({
                    "name": p.name,
                    "path": str(p),
                    "files": files
                })
    return {"projects": projects, "running": process_manager.list_running()}

# --- WebSocket for Realtime Voice, Chat & Telemetry ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("New WebSocket client connected to JARVIS HUD.")

    async def emit_ws_event(event_type: str, data: dict):
        try:
            await websocket.send_json({"type": event_type, "data": data})
        except Exception as e:
            logger.warning(f"Failed to send WS event {event_type}: {e}")

    try:
        # Initial greeting and status
        ollama_status = await ollama_client.check_health()
        await emit_ws_event("system_ready", {
            "greeting": "J.A.R.V.I.S. is online, Sir. Sub-agents (Qwen-Coder, DeepSeek-R1, MiniCPM-V, Playwright) are primed and standing by.",
            "ollama": ollama_status,
            "models": MODEL_ROUTING
        })

        async def stream_tts(text: str):
            """Synthesize TTS in the background and stream audio URL to the client."""
            if not text:
                return
            try:
                tts_result = await tts_agent.synthesize(text)
                if tts_result.get("audio_url"):
                    await emit_ws_event("audio_ready", {"audio_url": tts_result["audio_url"]})
                tts_agent.cleanup_old_audio()
            except Exception as tts_err:
                logger.warning(f"Background TTS error: {tts_err}")

        while True:
            raw_text = await websocket.receive_text()
            data = json.loads(raw_text)
            action = data.get("action")

            if action == "user_message":
                user_msg = data.get("message", "")
                await emit_ws_event("user_echo", {"message": user_msg})
                
                # Dispatch through orchestrator
                response = await jarvis_orchestrator.handle_user_input(
                    user_message=user_msg,
                    emit_event=emit_ws_event
                )

                # Emit instant text response with pipelined audio to the HUD!
                await emit_ws_event("jarvis_response", response)

                # If audio was not already attached via pipelining, generate in background
                reply_text = response.get("reply", "")
                if reply_text and not response.get("audio_url"):
                    asyncio.create_task(stream_tts(reply_text))

            elif action == "confirm_payment":
                res = booking_agent.confirm_payment()
                tts_res = await tts_agent.synthesize(res.get("message", ""))
                res["audio_url"] = tts_res.get("audio_url")
                await emit_ws_event("payment_result", res)

            elif action == "cancel_payment":
                res = booking_agent.cancel_payment()
                tts_res = await tts_agent.synthesize(res.get("message", ""))
                res["audio_url"] = tts_res.get("audio_url")
                await emit_ws_event("payment_result", res)

            elif action == "reset_session":
                jarvis_orchestrator.reset()
                msg = "Session context cleared, Sir."
                tts_res = await tts_agent.synthesize(msg)
                await emit_ws_event("session_reset", {"message": msg, "audio_url": tts_res.get("audio_url")})

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected.")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=HOST, port=PORT, reload=True)
