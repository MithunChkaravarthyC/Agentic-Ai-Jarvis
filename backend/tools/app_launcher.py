"""
app_launcher.py — Universal Windows Application Launcher for JARVIS
Uses Win32 ShellExecuteW & os.startfile to instantly launch desktop applications.
"""
import os
import re
import ctypes
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger("AppLauncher")

# ─── Direct name → executable / URL aliases ────────────────────────────────
ALIASES: Dict[str, str] = {
    # System
    "notepad": "notepad.exe",
    "note pad": "notepad.exe",
    "calc": "calc.exe",
    "calculator": "calc.exe",
    "paint": "mspaint.exe",
    "task manager": "taskmgr.exe",
    "taskmgr": "taskmgr.exe",
    "control panel": "control.exe",
    "settings": "ms-settings:",
    # Terminal / IDE
    "cmd": "cmd.exe",
    "command prompt": "cmd.exe",
    "terminal": "wt.exe",
    "powershell": "powershell.exe",
    "vs code": "code.cmd",
    "vscode": "code.cmd",
    "code": "code.cmd",
    # Browsers
    "chrome": "chrome.exe",
    "google chrome": "chrome.exe",
    "edge": "msedge.exe",
    "microsoft edge": "msedge.exe",
    "firefox": "firefox.exe",
    # Apps
    "spotify": "spotify.exe",
    "discord": "discord.exe",
    "zoom": "zoom.exe",
    "steam": "steam.exe",
    "blender": "blender.exe",
    # Websites
    "swiggy": "https://www.swiggy.com",
    "zomato": "https://www.zomato.com",
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    # MS Office
    "word": "winword.exe",
    "excel": "excel.exe",
    "powerpoint": "powerpnt.exe",
    "outlook": "outlook.exe",
    "teams": "teams.exe",
}

# Words to strip when cleaning user input
_NOISE_WORDS = [
    r"jarvis[,.]?", r"please", r"can you", r"could you", r"would you",
    r"open up", r"open", r"launch", r"start", r"run", r"start up",
    r"the\b", r"my\b",
    r"in my laptop", r"on my laptop", r"on my pc", r"in my pc",
    r"in my latop", r"on my latop",   # common typos
    r"in my computer", r"on my computer",
    r"for me", r"quickly", r"fast", r"please", r"now", r"application", r"app",
]
_NOISE_RE = re.compile(r"\b(?:" + "|".join(_NOISE_WORDS) + r")\b", re.IGNORECASE)


def _clean(text: str) -> str:
    """Strip all filler words and return the core app name."""
    cleaned = _NOISE_RE.sub("", text)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip(" .,!?")
    return cleaned.lower()


def _shell_open(target: str) -> bool:
    """Launch target using safe Win32 API to ensure it opens visibly on the user's desktop."""
    target_str = str(target)

    # Strategy 1: os.startfile (Native Windows interactive launch)
    try:
        os.startfile(target_str)
        logger.info(f"os.startfile('{target_str}') launched successfully")
        return True
    except Exception as exc:
        logger.debug(f"os.startfile failed: {exc}")

    # Strategy 2: Win32 ShellExecuteW
    try:
        result = ctypes.windll.shell32.ShellExecuteW(None, "open", target_str, None, None, 1)
        logger.info(f"ShellExecuteW('{target_str}') -> {result}")
        if result > 32:
            return True
    except Exception as exc:
        logger.debug(f"ShellExecuteW failed: {exc}")

    return False


class AppLauncher:
    """Find and launch any desktop application or website on Windows in milliseconds."""

    def __init__(self):
        self._shortcuts: Optional[Dict[str, Path]] = None

    def _get_search_dirs(self):
        user_profile = Path(os.environ.get("USERPROFILE", "C:/Users/Mithun"))
        appdata = Path(os.environ.get("APPDATA", str(user_profile / "AppData" / "Roaming")))
        progdata = Path(os.environ.get("PROGRAMDATA", "C:/ProgramData"))
        localappdata = Path(os.environ.get("LOCALAPPDATA", str(user_profile / "AppData" / "Local")))

        return [
            user_profile / "OneDrive" / "Desktop",
            user_profile / "Desktop",
            appdata / "Microsoft" / "Windows" / "Start Menu" / "Programs",
            progdata / "Microsoft" / "Windows" / "Start Menu" / "Programs",
            localappdata / "Programs",
        ]

    def _build_cache(self):
        if self._shortcuts is not None:
            return
        self._shortcuts = {}
        for base in self._get_search_dirs():
            if not base.exists():
                continue
            try:
                # Fast shallow walk (max 2 levels deep) avoiding whole-disk traversal
                for root, dirs, files in os.walk(str(base)):
                    # Limit depth to 2 levels below base
                    rel = Path(root).relative_to(base)
                    if len(rel.parts) > 2:
                        dirs.clear()
                        continue
                    for f in files:
                        p = Path(root) / f
                        ext = p.suffix.lower()
                        if ext in {".lnk", ".url", ".exe"}:
                            key = p.stem.lower().replace(" ", "").replace("-", "")
                            if key not in self._shortcuts:
                                self._shortcuts[key] = p
            except Exception as e:
                logger.debug(f"Shortcut indexing error on {base}: {e}")

    def _find_shortcut(self, name: str) -> Optional[Path]:
        """Search cached Desktop + Start Menu shortcuts for a matching name."""
        self._build_cache()
        needle = name.lower().replace(" ", "").replace("-", "")
        if not needle:
            return None

        # Exact key match
        if needle in self._shortcuts:
            return self._shortcuts[needle]

        # Substring key match (e.g. 'kiro' matches 'kiro.lnk')
        for key, path in self._shortcuts.items():
            if needle == key or (len(needle) >= 3 and (needle in key or key in needle)):
                return path

        return None

    def open_application(self, user_input: str) -> Dict[str, Any]:
        """
        Given any free-form user instruction like:
          "open up calculator", "Jarvis open kiro fast", "launch notepad please"
        find and physically open the matching application on Windows.
        """
        core_name = _clean(user_input)
        if not core_name:
            core_name = user_input.strip().lower()

        logger.info(f"AppLauncher: cleaned name = '{core_name}' (from: '{user_input}')")

        # ── 1. Check Desktop & Start Menu shortcuts first (finds Kiro, Discord, etc. instantly)
        path = self._find_shortcut(core_name)
        if path and _shell_open(str(path)):
            display_name = path.stem.title()
            return _ok(display_name)

        # ── 2. Check known alias table (calculator, notepad, chrome, cmd)
        for alias, target in ALIASES.items():
            alias_clean = alias.replace(" ", "")
            if core_name == alias or core_name == alias_clean or core_name in alias_clean:
                # If target is in PATH or exists, or is a URL/system URI
                if ":" in target or shutil.which(target) or Path(target).exists() or _shell_open(target):
                    if _shell_open(target):
                        return _ok(alias.title())

        # ── 3. Check System PATH lookup
        found = shutil.which(core_name) or shutil.which(core_name.replace(" ", "")) or shutil.which(f"{core_name}.exe")
        if found and _shell_open(found):
            return _ok(core_name.title())

        # ── 4. Try as a direct shell execution if common Windows utility
        if core_name in ["calc", "notepad", "mspaint", "taskmgr", "cmd", "explorer"]:
            if _shell_open(f"{core_name}.exe"):
                return _ok(core_name.title())

        return {
            "status": "error",
            "app": core_name,
            "message": (
                f"I could not find '{core_name}' on your laptop, Sir. "
                f"Please make sure it is installed or pinned to your desktop."
            )
        }


def _ok(name: str) -> Dict[str, Any]:
    return {"status": "success", "app": name, "message": f"Opened {name} on your laptop, Sir."}


# Singleton
app_launcher = AppLauncher()

