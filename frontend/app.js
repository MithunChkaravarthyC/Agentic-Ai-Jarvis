// J.A.R.V.I.S. Multi-Agent HUD Client Engine

class JarvisClient {
    constructor() {
        this.ws = null;
        this.speechRecognition = null;
        this.isListening = false;
        this.voiceEnabled = true;
        this.currentAudio = null;

        this.initDOM();
        this.initSpeechRecognition();
        this.initWebSocket();
        this.bindEvents();
    }

    initDOM() {
        this.chatContainer = document.getElementById("chatContainer");
        this.chatInput = document.getElementById("chatInput");
        this.sendBtn = document.getElementById("sendBtn");
        this.voiceBtn = document.getElementById("voiceBtn");
        this.arcReactor = document.getElementById("arcReactor");
        this.audioWave = document.getElementById("audioWave");
        this.reactorStatus = document.getElementById("reactorStatus");
        this.ollamaStatus = document.getElementById("ollamaStatus");
        this.voiceToggle = document.getElementById("voiceSynthesisToggle");
        this.thoughtLog = document.getElementById("thoughtLog");
        this.liveScreenshotImg = document.getElementById("liveScreenshotImg");
        this.browserUrlDisplay = document.getElementById("browserUrlDisplay");
        this.previewIframe = document.getElementById("previewIframe");
        this.iframePlaceholder = document.getElementById("iframePlaceholder");
        this.activeAppName = document.getElementById("activeAppName");
        this.externalAppBtn = document.getElementById("externalAppBtn");
        this.approvalModal = document.getElementById("approvalModal");
        this.modalDetails = document.getElementById("modalDetails");
        this.modalScreenshotImg = document.getElementById("modalScreenshotImg");
        this.confirmPaymentBtn = document.getElementById("confirmPaymentBtn");
        this.cancelPaymentBtn = document.getElementById("cancelPaymentBtn");
        this.resetSessionBtn = document.getElementById("resetSessionBtn");
    }

    initWebSocket() {
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            console.log("[HUD] Connected to Jarvis Core WebSocket.");
            this.ollamaStatus.textContent = "CONNECTED";
            this.ollamaStatus.className = "metric-val status-online";
        };

        this.ws.onmessage = (event) => {
            try {
                const packet = JSON.parse(event.data);
                this.handleServerEvent(packet.type, packet.data);
            } catch (err) {
                console.error("[HUD] WS Parse Error:", err);
            }
        };

        this.ws.onerror = (err) => {
            console.error("[HUD] WS Connection Error:", err);
            this.resetAllAgentStatus();
        };

        this.ws.onclose = () => {
            console.warn("[HUD] WebSocket disconnected, attempting reconnect...");
            this.ollamaStatus.textContent = "DISCONNECTED";
            this.ollamaStatus.className = "metric-val text-red";
            this.resetAllAgentStatus();
            setTimeout(() => this.initWebSocket(), 2000);
        };
    }

    handleServerEvent(type, data) {
        switch (type) {
            case "system_ready":
                console.log("System Ready:", data);
                if (data.ollama && data.ollama.status === "online") {
                    this.ollamaStatus.textContent = `ONLINE (${data.ollama.models.length} MODELS)`;
                }
                break;

            case "user_echo":
                this.appendMessage("user", data.message);
                break;

            case "agent_status":
                this.updateAgentStatus(data.agent, data.status);
                break;

            case "thought_stream":
                this.appendThought(data.thought);
                break;

            case "app_created":
                this.displayCreatedApp(data);
                break;

            case "booking_pending":
                this.showApprovalModal(data);
                break;

            case "payment_result":
                this.hideApprovalModal();
                this.appendMessage("jarvis", data.message);
                if (data.audio_url) {
                    this.speak(data.audio_url);
                }
                if (data.portal_url) {
                    try {
                        window.open(data.portal_url, "_blank");
                    } catch (e) {
                        console.warn("Popup blocked, user can click direct link:", e);
                    }
                }
                if (data.screenshot_url) {
                    this.liveScreenshotImg.src = data.screenshot_url;
                    this.liveScreenshotImg.style.display = "block";
                    const placeholder = document.querySelector(".browser-placeholder");
                    if (placeholder) placeholder.style.display = "none";
                    const browserTab = document.querySelector('.vtab[data-tab="browserStream"]');
                    if (browserTab) browserTab.click();
                }
                break;

            case "jarvis_response":
                this.resetAllAgentStatus();
                this.appendMessage("jarvis", data.reply);
                if (data.audio_url) {
                    this.speak(data.audio_url);
                }
                if (data.booking && data.booking.requires_approval) {
                    this.showApprovalModal(data.booking);
                }
                if (data.details && data.details.portal_url) {
                    try {
                        window.open(data.details.portal_url, "_blank");
                    } catch (e) {}
                }
                if (data.details && data.details.screenshot_url) {
                    this.liveScreenshotImg.src = data.details.screenshot_url;
                    this.liveScreenshotImg.style.display = "block";
                    const placeholder = document.querySelector(".browser-placeholder");
                    if (placeholder) placeholder.style.display = "none";
                    const browserTab = document.querySelector('.vtab[data-tab="browserStream"]');
                    if (browserTab) browserTab.click();
                }
                break;

            case "audio_ready":
                if (data.audio_url) {
                    this.speak(data.audio_url);
                }
                break;

            case "session_reset":
                this.chatContainer.innerHTML = "";
                this.appendMessage("jarvis", data.message);
                if (data.audio_url) {
                    this.speak(data.audio_url);
                }
                break;
        }
    }

    updateAgentStatus(agentName, statusText) {
        const card = document.getElementById(`agent-${agentName}`);
        const statusEl = document.getElementById(`status-${agentName}`);
        if (card && statusEl) {
            card.className = "agent-card running";
            statusEl.textContent = statusText;
            const dot = card.querySelector(".agent-dot");
            if (dot) dot.className = "agent-dot dot-active";
        }
        this.setReactorState("ACTIVE", "PROCESSING");
    }

    resetAllAgentStatus() {
        ["ReasoningAgent", "CodeAgent", "VisionAgent", "SlotExtractor", "VoiceConvoAgent", "BookingAgent"].forEach(agent => {
            const card = document.getElementById(`agent-${agent}`);
            const statusEl = document.getElementById(`status-${agent}`);
            if (card && statusEl) {
                card.className = "agent-card";
                statusEl.textContent = "Idle";
                const dot = card.querySelector(".agent-dot");
                if (dot) dot.className = "agent-dot dot-idle";
            }
        });
        this.setReactorState("STANDBY", "STANDBY");
    }

    appendThought(thoughtText) {
        if (!thoughtText) return;
        this.thoughtLog.textContent = thoughtText;
        // Auto-switch to thought tab if user hasn't selected another
        const thoughtTab = document.querySelector('.vtab[data-tab="reasoningStream"]');
        if (thoughtTab) thoughtTab.click();
    }

    displayCreatedApp(appData) {
        this.activeAppName.textContent = appData.project_name;
        this.externalAppBtn.href = appData.preview_url;
        this.externalAppBtn.style.display = "inline-block";
        this.iframePlaceholder.style.display = "none";
        this.previewIframe.src = appData.preview_url;

        // Switch to App Preview Tab
        const appTab = document.querySelector('.vtab[data-tab="appPreview"]');
        if (appTab) appTab.click();
    }

    showApprovalModal(bookingData) {
        if (!bookingData) return;
        const payload = bookingData.confirmation_payload || bookingData.booking?.confirmation_payload || {};
        const details = payload.details || bookingData.details || {};
        const actionTitle = bookingData.action || payload.action_type || "Booking / Order";
        const totalAmount = details.total || bookingData.summary?.match(/₹[\d,.]+/)?.[0] || "₹399.00";
        const screenshotUrl = bookingData.screenshot_url || payload.details?.screenshot || details.screenshot;

        let detailsHtml = `<div style="margin-bottom: 12px; color:#00f0ff; font-weight: bold; letter-spacing: 1px;">⚡ ${actionTitle.toUpperCase()}</div>`;
        
        for (const [key, val] of Object.entries(details)) {
            if (key !== "screenshot" && key !== "vision_analysis" && key !== "action_type") {
                const label = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                detailsHtml += `<div style="display:flex; justify-content:space-between; margin-bottom: 8px; font-size: 14px;">
                    <span style="color:#94a3b8;">${label}:</span>
                    <span style="color:#f8fafc; font-weight:600;">${val}</span>
                </div>`;
            }
        }
        
        detailsHtml += `<div style="border-top:1px solid #334155; padding-top: 10px; margin-top: 10px; display:flex; justify-content:space-between; font-size: 16px;">
            <span style="color:#f59e0b; font-weight:bold;">TOTAL PAYABLE:</span>
            <span style="color:#10b981; font-weight:bold; font-size: 18px;">${totalAmount}</span>
        </div>`;

        this.modalDetails.innerHTML = detailsHtml;

        if (screenshotUrl) {
            this.modalScreenshotImg.src = screenshotUrl;
            this.modalScreenshotImg.style.display = "block";
            this.liveScreenshotImg.src = screenshotUrl;
            this.liveScreenshotImg.style.display = "block";
            const placeholder = document.querySelector(".browser-placeholder");
            if (placeholder) placeholder.style.display = "none";
        }

        this.approvalModal.classList.add("active");
        this.setReactorState("ALERT", "SECURITY GATE");
    }

    hideApprovalModal() {
        this.approvalModal.classList.remove("active");
        this.setReactorState("STANDBY", "STANDBY");
    }

    appendMessage(sender, text) {
        const msgCard = document.createElement("div");
        msgCard.className = `message-card ${sender === "user" ? "user-card" : "jarvis-card"}`;
        
        const avatarLetter = sender === "user" ? "U" : "J";
        const senderName = sender === "user" ? "USER" : "J.A.R.V.I.S.";

        // Basic Markdown parsing for bold and links
        let formattedText = text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\[(.*?)\]\((https?:\/\/.*?)\)/g, '<a href="$2" target="_blank" class="portal-link-btn" style="display:inline-flex; align-items:center; gap:8px; margin-top:10px; padding:8px 16px; background:linear-gradient(135deg, #00f0ff 0%, #0284c7 100%); color:#030712; font-weight:800; font-size:12px; text-transform:uppercase; letter-spacing:1px; border-radius:6px; text-decoration:none; box-shadow:0 0 15px rgba(0,240,255,0.4);">⚡ $1 &rarr;</a>')
            .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" style="color:#00f0ff;">$1</a>')
            .replace(/\n/g, '<br>');

        msgCard.innerHTML = `
            <div class="msg-avatar">${avatarLetter}</div>
            <div class="msg-content">
                <div class="msg-sender">${senderName}</div>
                <div class="msg-body">${formattedText}</div>
            </div>
        `;

        this.chatContainer.appendChild(msgCard);
        this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
    }

    setReactorState(state, text) {
        if (state === "ACTIVE" || state === "ALERT") {
            this.arcReactor.classList.add("active");
            this.audioWave.classList.add("active");
        } else {
            this.arcReactor.classList.remove("active");
            this.audioWave.classList.remove("active");
        }
        this.reactorStatus.textContent = text;
    }

    // --- Speech Recognition (Voice In) ---
    initSpeechRecognition() {
        const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRec) {
            console.warn("Speech Recognition API not supported in this browser.");
            return;
        }

        this.speechRecognition = new SpeechRec();
        this.speechRecognition.continuous = false;
        this.speechRecognition.interimResults = false;
        this.speechRecognition.lang = "en-US";

        this.speechRecognition.onstart = () => {
            this.isListening = true;
            this.voiceBtn.classList.add("listening");
            this.setReactorState("ACTIVE", "LISTENING...");
        };

        this.speechRecognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            this.chatInput.value = transcript;
            this.sendMessage();
        };

        this.speechRecognition.onerror = (event) => {
            console.error("Speech Recognition Error:", event.error);
            this.stopListening();
        };

        this.speechRecognition.onend = () => {
            this.stopListening();
        };
    }

    toggleListening() {
        if (!this.speechRecognition) {
            alert("Voice input requires Google Chrome or Chromium with Web Speech API support.");
            return;
        }
        if (this.isListening) {
            this.speechRecognition.stop();
        } else {
            this.speechRecognition.start();
        }
    }

    stopListening() {
        this.isListening = false;
        this.voiceBtn.classList.remove("listening");
        this.setReactorState("STANDBY", "STANDBY");
    }

    // --- Dedicated Kokoro-82M High-Fidelity Audio Playback ---
    speak(audioUrl) {
        if (!this.voiceEnabled || !audioUrl) return;

        // Stop any currently playing audio immediately to prevent overlap
        if (this.currentAudio) {
            try {
                this.currentAudio.pause();
                this.currentAudio.currentTime = 0;
            } catch (e) {}
            this.currentAudio = null;
        }

        const audio = new Audio(audioUrl);
        audio.preload = "auto";
        this.currentAudio = audio;

        audio.onplay = () => this.setReactorState("ACTIVE", "SPEAKING (KOKORO)");
        audio.onended = () => {
            this.setReactorState("STANDBY", "STANDBY");
            if (this.currentAudio === audio) {
                this.currentAudio = null;
            }
        };
        audio.onerror = (err) => {
            console.warn("[HUD] Kokoro audio playback error:", err);
            this.setReactorState("STANDBY", "STANDBY");
            if (this.currentAudio === audio) {
                this.currentAudio = null;
            }
        };

        // Instant sub-second playback
        audio.play().catch(e => {
            console.warn("[HUD] Audio playback waiting for first user gesture:", e);
            this.setReactorState("STANDBY", "STANDBY");
        });
    }

    sendMessage() {
        const text = this.chatInput.value.trim();
        if (!text) return;

        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            this.appendMessage("jarvis", "Connecting to J.A.R.V.I.S. Core server... Please try again in a moment, Sir.");
            this.initWebSocket();
            return;
        }

        this.ws.send(JSON.stringify({
            action: "user_message",
            message: text
        }));

        this.chatInput.value = "";
    }

    bindEvents() {
        this.sendBtn.addEventListener("click", () => this.sendMessage());
        this.chatInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        this.voiceBtn.addEventListener("click", () => this.toggleListening());
        this.voiceToggle.addEventListener("change", (e) => {
            this.voiceEnabled = e.target.checked;
            if (!this.voiceEnabled && this.currentAudio) {
                this.currentAudio.pause();
                this.currentAudio = null;
                this.setReactorState("STANDBY", "STANDBY");
            }
        });

        this.confirmPaymentBtn.addEventListener("click", () => {
            this.ws.send(JSON.stringify({ action: "confirm_payment" }));
        });

        this.cancelPaymentBtn.addEventListener("click", () => {
            this.ws.send(JSON.stringify({ action: "cancel_payment" }));
            this.hideApprovalModal();
        });

        this.resetSessionBtn.addEventListener("click", () => {
            this.ws.send(JSON.stringify({ action: "reset_session" }));
        });

        // Viewport Tab Switcher
        document.querySelectorAll(".vtab").forEach(tab => {
            tab.addEventListener("click", () => {
                document.querySelectorAll(".vtab").forEach(t => t.classList.remove("active"));
                document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));

                tab.classList.add("active");
                const targetPane = document.getElementById(`tab-${tab.dataset.tab}`);
                if (targetPane) targetPane.classList.add("active");
            });
        });
    }
}

// Quick Prompt Helper
window.sendQuickPrompt = function(promptText) {
    const input = document.getElementById("chatInput");
    if (input) {
        input.value = promptText;
        if (window.jarvisApp) window.jarvisApp.sendMessage();
    }
};

// Initialize on DOM ready
document.addEventListener("DOMContentLoaded", () => {
    window.jarvisApp = new JarvisClient();
});
