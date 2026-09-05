import subprocess
import socket
import sys
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger("ProcessManager")

class ProcessManager:
    def __init__(self):
        self.active_processes: Dict[str, Dict[str, Any]] = {}

    def find_free_port(self, start_port: int = 3000) -> int:
        """Find an open TCP port on localhost."""
        for port in range(start_port, start_port + 100):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(('127.0.0.1', port)) != 0:
                    return port
        return start_port

    def start_static_server(self, project_name: str, directory_path: Path) -> Dict[str, Any]:
        """Start a lightweight Python HTTP server for a static web application."""
        if project_name in self.active_processes:
            self.stop_process(project_name)

        port = self.find_free_port()
        cmd = [sys.executable, "-m", "http.server", str(port)]
        
        try:
            process = subprocess.Popen(
                cmd,
                cwd=str(directory_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            preview_url = f"http://127.0.0.1:{port}"
            self.active_processes[project_name] = {
                "process": process,
                "port": port,
                "url": preview_url,
                "type": "static",
                "directory": str(directory_path)
            }
            logger.info(f"Started web app server for {project_name} at {preview_url}")
            return {
                "status": "running",
                "port": port,
                "url": preview_url,
                "message": f"Application running at {preview_url}"
            }
        except Exception as e:
            logger.error(f"Failed to start server for {project_name}: {e}")
            return {"status": "error", "error": str(e)}

    def stop_process(self, project_name: str) -> bool:
        """Stop a running background server."""
        if project_name in self.active_processes:
            entry = self.active_processes[project_name]
            try:
                entry["process"].terminate()
                entry["process"].wait(timeout=2)
            except Exception:
                try:
                    entry["process"].kill()
                except Exception:
                    pass
            del self.active_processes[project_name]
            return True
        return False

    def list_running(self) -> Dict[str, Any]:
        """List all active project servers."""
        return {
            name: {"url": data["url"], "port": data["port"], "directory": data["directory"]}
            for name, data in self.active_processes.items()
        }

process_manager = ProcessManager()
