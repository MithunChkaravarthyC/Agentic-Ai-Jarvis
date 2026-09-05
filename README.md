# 🤖 J.A.R.V.I.S. Autonomous Multi-Agent AI System

An autonomous, multi-agent AI assistant powered by your local **Ollama** models (`qwen3-coder:30b`, `DeepSeek-r1:8b`, `minicpm-v:latest`, `llama3:latest`), equipped with an Iron Man Stark Industries HUD interface, voice interaction, full-stack application building, Swiggy food ordering, and flight ticket booking automation.

---

## ⚡ Agent Routing Architecture

| Agent | Engine / Model | Core Responsibilities |
|---|---|---|
| **J.A.R.V.I.S. Master** | `llama3:latest` / `DeepSeek-r1:8b` | Conversational persona, slot-filling (asking for missing locations, dates, features), voice interaction & speech synthesis. |
| **ReasoningAgent** | `DeepSeek-r1:8b` | Chain-of-thought analysis, task decomposition, architectural planning & safety checks. |
| **CodeAgent** | `qwen3-coder:30b` | Full-stack web app generation (`index.html`, `styles.css`, `app.js`, `README.md`), automatic syntax validation & live server spawning. |
| **VisionAgent** | `minicpm-v:latest` | Multimodal browser screenshot inspection, cart total verification, seat map & booking review. |
| **BookingAgent** | Playwright Automation | Headful/headless browser execution for Swiggy food ordering and flight search, with an enforced **Security Confirmation Gate** before payment. |

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10+ installed
- Ollama running locally (`http://localhost:11434`) with your pre-downloaded models.

### 2. Launch JARVIS
Simply double-click:
```bat
start_jarvis.bat
```
Or run in PowerShell / Command Prompt:
```bash
python run_jarvis.py
```

### 3. Open HUD Interface
Navigate in Chrome or Edge to:
👉 **`http://localhost:8000`**

---

## 🎙️ How to Use JARVIS

### 1. 🏗️ Build a Web Application
- **Voice/Chat Command**: *"Jarvis, build a modern Kanban Task Board web application with drag and drop, priority tags, and local storage."*
- **What happens**:
  1. JARVIS acknowledges and consults `ReasoningAgent (DeepSeek-R1)` for task breakdown.
  2. `CodeAgent (Qwen-Coder)` creates full, production-ready files in `generated_projects/<app_name>/`.
  3. JARVIS launches a local server and renders an interactive **Live Preview Iframe** directly in the HUD!

### 2. 🍲 Order Food on Swiggy
- **Voice/Chat Command**: *"Jarvis, order a Chicken Biryani from Swiggy in Koramangala, Bangalore."*
- **What happens**:
  1. JARVIS asks for location/item if omitted.
  2. `BookingAgent (Playwright)` opens Swiggy, searches the dish, and adds it to the cart.
  3. `VisionAgent (MiniCPM-V)` reads the screen, verifies the order subtotal and items.
  4. **SECURITY GATE ENGAGED**: JARVIS halts at checkout and presents an authorization modal with live snapshot.
  5. Say *"Yes, confirm payment"* or click **CONFIRM & AUTHORIZE PAYMENT** to complete.

### 3. ✈️ Book Flight Tickets
- **Voice/Chat Command**: *"Jarvis, find and book a flight from Mumbai to Delhi for next Monday."*
- **What happens**:
  1. JARVIS initiates flight search on Google Flights / MakeMyTrip.
  2. Extracts airlines, departure timings, non-stop status, and lowest fares.
  3. Selects optimal flight, fills traveler details, and takes a snapshot.
  4. Prompts you for final confirmation before any transaction.

---

## 🛡️ Security Gate Protocol
No irreversible action (financial transaction or binding booking submission) is ever finalized automatically. The system will always stream a visual proof and pause for your explicit confirmation.
