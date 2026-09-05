@echo off
title J.A.R.V.I.S. Multi-Agent AI System
cd /d "%~dp0"
echo =============================================================
echo   INITIALIZING J.A.R.V.I.S. MULTI-AGENT STARK OS
echo =============================================================
echo.
echo Checking Ollama connectivity...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Ollama server does not seem to be running on port 11434!
    echo Please make sure 'ollama serve' is running in the background.
    echo.
)

where py >nul 2>&1
if %errorlevel% equ 0 (
    py -3 run_jarvis.py
) else (
    python run_jarvis.py
)

pause
