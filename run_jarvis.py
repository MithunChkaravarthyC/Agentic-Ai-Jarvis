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
    
    # Check if core packages are already present to avoid slow continuous pip checking
    packages = ["fastapi", "uvicorn", "playwright", "httpx", "pydantic", "kokoro", "soundfile"]
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
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("0.0.0.0", port))
        s.close()
        return
    except OSError:
        pass
    finally:
        try:
            s.close()
        except Exception:
            pass

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
    """Attempt preferred port, fallback to next available port if locked."""
    free_port(preferred_port)
    import socket
    for port in [preferred_port, preferred_port + 1, preferred_port + 2]:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind(("0.0.0.0", port))
            s.close()
            return port
        except OSError:
            try:
                s.close()
            except Exception:
                pass
    return preferred_port

def auto_launch_browser(port: int):
    """Wait for server to bind and automatically pop open the JARVIS HUD in browser."""
    import threading
    import webbrowser

    def _open():
        time.sleep(1.2)
        url = f"http://localhost:{port}"
        print(f">> Launching JARVIS Interface in your browser: {url}")
        try:
            webbrowser.open(url, new=2)
        except Exception:
            try:
                os.startfile(url)
            except Exception:
                pass

    t = threading.Thread(target=_open, daemon=True)
    t.start()

def main():
    check_and_install_dependencies()
    port = int(os.getenv("PORT", 0)) or get_available_port(8000)
    os.environ["PORT"] = str(port)

    # Pre-warm Kokoro TTS engine in background for instant speech response
    print(">> Pre-warming Kokoro-82M TTS neural engine...")
    try:
        from backend.agents.tts_agent import tts_agent
        tts_agent.warmup()
    except Exception as e:
        print(f">> [Note] TTS warmup: {e}")

    print(">> Launching JARVIS Core Server...")
    print(f">> JARVIS HUD available at: http://localhost:{port}")
    print(">> Press Ctrl+C to terminate.")
    print("=======================================================")

    auto_launch_browser(port)
    
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=False)

if __name__ == "__main__":
    main()
