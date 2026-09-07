import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
GENERATED_PROJECTS_DIR = BASE_DIR / "generated_projects"
SCREENSHOTS_DIR = BASE_DIR / "backend" / "temp_screenshots"
AUDIO_DIR = BASE_DIR / "backend" / "temp_audio"
STATIC_DIR = BASE_DIR / "frontend"

GENERATED_PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# TTS Configuration (Edge-TTS Neural / Kokoro Fallback)
TTS_VOICE = os.getenv("JARVIS_TTS_VOICE", "en-GB-RyanNeural")  # Sophisticated British Male - J.A.R.V.I.S.
TTS_LANG_CODE = os.getenv("JARVIS_TTS_LANG", "en-GB")

# Model routing mapped to user's locally installed Ollama models
# Prioritizing GPU-accelerated models (llama3 / deepseek-r1) for instant sub-second responses
MODEL_ROUTING = {
    "intent_extractor": os.getenv("JARVIS_INTENT_MODEL", "llama3.2:1b"),
    "conversational_voice": os.getenv("JARVIS_CONVO_MODEL", "llama3.2:latest"),
    "orchestrator": os.getenv("JARVIS_ORCHESTRATOR_MODEL", "llama3.2:latest"),
    "reasoning": os.getenv("JARVIS_REASONING_MODEL", "DeepSeek-r1:8b"),
    "coder": os.getenv("JARVIS_CODER_MODEL", "qwen2.5-coder:7b"),  # 100% GPU accelerated for instant web app generation
    "vision": os.getenv("JARVIS_VISION_MODEL", "minicpm-v:latest"),
    "heavy_coder": "qwen2.5-coder:7b",
    "coder_fallback": "llama3.2:latest"
}

HOST = "0.0.0.0"
PORT = int(os.getenv("PORT", 8000))
HEADLESS_BROWSER = False  # False = Real Chromium browser opens visibly on screen!
