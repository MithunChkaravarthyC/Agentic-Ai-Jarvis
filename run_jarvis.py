import sys
import subprocess
import time
import os
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

def check_and_install_dependencies():
    print("=======================================================")
    print("   J.A.R.V.I.S. MULTI-AGENT PROTOCOL INITIALIZATION    ")
    print("=======================================================")
    
    packages = ["fastapi", "uvicorn", "playwright", "httpx", "pydantic", "edge_tts", "mss", "sounddevice", "numpy", "speech_recognition"]
    missing = []
    for pkg in packages:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)

    req_file = BASE_DIR / "requirements.txt"
    if missing and req_file.exists():
        print(f">> Installing missing dependencies: {missing}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(req_file)])
        except Exception as e:
            print(f"[Warning] Pip install encountered: {e}")
    else:
        print(">> Python runtime packages verified (instant startup).")

def free_port(port=8000):
    """Ensure port 8000 is clean and not locked by an old zombie process."""
    try:
        out = subprocess.check_output(f"netstat -ano | findstr :{port}", shell=True).decode(errors="ignore")
        for line in out.strip().splitlines():
            parts = line.split()
            if len(parts) >= 5 and "LISTENING" in line:
                pid = int(parts[-1])
                if pid != os.getpid():
                    print(f">> Freeing port {port} from previous process (PID {pid})...")
                    subprocess.call(f"taskkill /F /PID {pid}", shell=True)
                    time.sleep(1)
    except Exception:
        pass

def get_available_port(preferred_port=8000):
    """Clean port and return preferred port directly."""
    free_port(preferred_port)
    return preferred_port

def main():
    check_and_install_dependencies()
    port = int(os.getenv("PORT", 0)) or get_available_port(8000)
    os.environ["PORT"] = str(port)

    # Pre-warm TTS engine in background for instant speech response
    print(">> Pre-warming J.A.R.V.I.S. Neural TTS engine...")
    try:
        from backend.agents.tts_agent import tts_agent
        tts_agent.warmup()
    except Exception as e:
        print(f">> [Note] TTS warmup: {e}")

    print(">> Launching JARVIS Core Server...")
    print(f">> JARVIS Core listening at: http://localhost:{port}")
    print(">> [STANDBY MODE]: Chrome will NOT launch automatically.")
    print(">> [WAKE TRIGGER]: Clap twice (👏 👏) and say 'Wake up Jarvis' to activate Chrome!")
    print(">> Press Ctrl+C to terminate.")
    print("=======================================================")

    # Initialize Acoustic Wake Listener (Double Clap + "Wake up Jarvis")
    try:
        from backend.tools.wake_detector import start_wake_word_listener
        start_wake_word_listener(port)
    except Exception as e:
        print(f">> [Note] Acoustic wake listener: {e}")
    
    import uvicorn
    import traceback
    try:
        uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=False, log_level="info")
    except KeyboardInterrupt:
        print("\n>> JARVIS Core Server stopped by user.")
    except Exception as e:
        print(f"\n>> JARVIS Core Server encountered an error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()

