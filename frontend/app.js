// J.A.R.V.I.S. Multi-Agent HUD Client Engine

class JarvisClient {
    constructor() {
        this.ws = null;
        this.recognition = null;
        this.isListening = false;
        this.voiceEnabled = true;
        this.voiceEngine = "zero_latency"; // Default to instant 0ms OS voice!
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
        this.voiceEngineSelect = document.getElementById("voiceEngineSelect");
        if (this.voiceEngineSelect) {
            this.voiceEngine = this.voiceEngineSelect.value || "zero_latency";
            this.voiceEngineSelect.addEventListener("change", (e) => {
                this.voiceEngine = e.target.value;
            });
        }
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
        this.hudLiveClock = document.getElementById("hudLiveClock");

        // MediaPipe Gesture Controls
        this.gestureToggleBtn = document.getElementById("gestureToggleBtn");
        this.gestureStatusText = document.getElementById("gestureStatusText");
        this.gestureFeedbackBadge = document.getElementById("gestureFeedbackBadge");
        this.gestureBadgeTimer = null;

        this.initClockTicker();
    }

    initClockTicker() {
        const updateClock = () => {
            if (this.hudLiveClock) {
                const now = new Date();
                this.hudLiveClock.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true });
            }
        };
        updateClock();
        setInterval(updateClock, 1000);
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
                this.speak(data.audio_url, data.message);
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
                    const browserTab = document.querySelector('.vtab[data-tab="liveView"]');
                    if (browserTab) browserTab.click();
                }
                break;

            case "jarvis_response":
                this.resetAllAgentStatus();
                this.appendMessage("jarvis", data.reply, data);
                this.speak(data.audio_url, data.reply);
                if (data.project) {
                    this.displayCreatedApp(data.project);
                }
                if (data.booking && data.booking.requires_approval) {
                    this.showApprovalModal(data.booking);
                }
                if (data.details && data.details.portal_url) {
                    try {
                        window.open(data.details.portal_url, "_blank");
                    } catch (e) {}
                }
                const shotUrl = (data.details && data.details.screenshot_url) || data.screenshot_url;
                if (shotUrl) {
                    this.liveScreenshotImg.src = shotUrl;
                    this.liveScreenshotImg.style.display = "block";
                    const placeholder = document.querySelector(".browser-placeholder");
                    if (placeholder) placeholder.style.display = "none";
                    if (this.browserUrlDisplay) {
                        if (data.type === "screen_perception") {
                            this.browserUrlDisplay.textContent = "screen://display-primary (MiniCPM-V Perception)";
                        } else if (data.type === "webcam_perception") {
                            this.browserUrlDisplay.textContent = "camera://lens-0 (Jarvis Eye MiniCPM-V Optics)";
                        } else {
                            this.browserUrlDisplay.textContent = "playwright://viewport";
                        }
                    }
                    const browserTab = document.querySelector('.vtab[data-tab="liveView"]');
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
                this.speak(data.audio_url, data.message);
                break;

            case "gesture_status":
                if (this.gestureToggleBtn && this.gestureStatusText) {
                    if (data.gesture_tracking) {
                        this.gestureToggleBtn.classList.add("active");
                        this.gestureStatusText.textContent = "GESTURES: ACTIVE";
                    } else {
                        this.gestureToggleBtn.classList.remove("active");
                        this.gestureStatusText.textContent = "GESTURES: STANDBY";
                    }
                }
                break;

            case "gesture_detected":
                this.showGestureFeedback(data);
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
        const totalAmount = details.total || bookingData.summary?.match(/\u20B9[\d,.]+/u)?.[0] || "\u20B9399.00";
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

    showGestureFeedback(data) {
        if (!data) return;
        const gesture = data.gesture;
        const action = data.action;
        const label = data.label || gesture;

        // Visual Feedback Badge on HUD Header
        if (this.gestureFeedbackBadge) {
            this.gestureFeedbackBadge.textContent = label;
            this.gestureFeedbackBadge.style.display = "inline-flex";
            this.gestureFeedbackBadge.classList.remove("pulse");
            void this.gestureFeedbackBadge.offsetWidth;
            this.gestureFeedbackBadge.classList.add("pulse");

            if (this.gestureBadgeTimer) clearTimeout(this.gestureBadgeTimer);
            this.gestureBadgeTimer = setTimeout(() => {
                if (this.gestureFeedbackBadge) this.gestureFeedbackBadge.style.display = "none";
            }, 3000);
        }

        // Action 1: Silence speech / stop audio playback
        if (action === "silence_speech") {
            if (this.currentAudio) {
                try {
                    this.currentAudio.pause();
                    this.currentAudio.currentTime = 0;
                } catch (e) {}
                this.currentAudio = null;
            }
            if (window.speechSynthesis) {
                window.speechSynthesis.cancel();
            }
            this.setReactorState("STANDBY", "STANDBY");
            this.appendMessage("jarvis", "✋ *Speech silenced by Open Palm gesture.*");
        }

        // Action 2: Confirm Payment / Approve Security Gate
        else if (action === "confirm_payment") {
            if (this.approvalModal && this.approvalModal.classList.contains("active")) {
                this.confirmPaymentBtn.click();
            }
        }

        // Action 3: Cancel Payment / Reject Security Gate
        else if (action === "cancel_payment") {
            if (this.approvalModal && this.approvalModal.classList.contains("active")) {
                this.cancelPaymentBtn.click();
            }
        }

        // Action 4: Wake / Toggle Voice Listening
        else if (action === "wake_listening") {
            if (!this.isListening) {
                this.toggleListening();
            }
        }
    }

    appendMessage(sender, text, meta = {}) {
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

        // Time Widget HTML
        let widgetHtml = "";
        if (meta && meta.time_data) {
            const t = meta.time_data;
            widgetHtml = `
                <div class="hud-embedded-card time-card">
                    <div class="card-top">
                        <span class="card-badge">⏱️ ${t.card_title || 'ATOMIC TIMEKEEPING'}</span>
                        <span class="tz-pill">${t.timezone}</span>
                    </div>
                    <div class="card-hero-metric">
                        <span class="big-time">${t.time_12h}</span>
                        <span class="time-24h">${t.time_24h} (24H)</span>
                    </div>
                    <div class="card-details-row">
                        <span>📅 ${t.day}</span>
                        <span>🗓️ ${t.date}</span>
                        <span>📍 ${t.city}</span>
                    </div>
                </div>
            `;
        }

        // Weather Widget HTML
        if (meta && meta.weather_data && meta.weather_data.status === "success") {
            const w = meta.weather_data;
            widgetHtml = `
                <div class="hud-embedded-card weather-card">
                    <div class="card-top">
                        <span class="card-badge"><span class="w-icon">${w.icon || '🌤️'}</span> ${w.display_location || w.city}</span>
                        <span class="condition-pill">${w.condition}</span>
                    </div>
                    <div class="weather-main-row">
                        <div class="temp-block">
                            <span class="temp-big">${w.temperature_c}°C</span>
                            <span class="temp-sub">/ ${w.temperature_f}°F</span>
                        </div>
                        <div class="feels-block">
                            <span>Feels like</span>
                            <strong>${w.feels_like_c}°C</strong>
                        </div>
                    </div>
                    <div class="weather-metrics-grid">
                        <div class="wm-node">
                            <span class="wm-lbl">HUMIDITY</span>
                            <span class="wm-val">${w.humidity}%</span>
                        </div>
                        <div class="wm-node">
                            <span class="wm-lbl">WIND</span>
                            <span class="wm-val">${w.wind_speed_kmh} km/h ${w.wind_direction}</span>
                        </div>
                        <div class="wm-node">
                            <span class="wm-lbl">PRESSURE</span>
                            <span class="wm-val">${w.pressure_hpa} hPa</span>
                        </div>
                        <div class="wm-node">
                            <span class="wm-lbl">CLOUD COVER</span>
                            <span class="wm-val">${w.cloud_cover}%</span>
                        </div>
                    </div>
                    <div class="weather-card-footer">
                        <span>Daily: <strong>${w.temp_min_c}°C</strong> to <strong>${w.temp_max_c}°C</strong></span>
                        <span class="live-dot-tag">● LIVE OPEN-METEO SENSORS</span>
                    </div>
                </div>
            `;
        }

        // Screen / Webcam Perception Screenshot Widget
        if (meta && (meta.screenshot_url || (meta.details && meta.details.screenshot_url))) {
            const shot = meta.screenshot_url || meta.details.screenshot_url;
            const tele = meta.telemetry || (meta.details && meta.details.telemetry) || {};
            const isWebcam = meta.type === "webcam_perception" || (meta.details && meta.details.action_type === "webcam_perception");
            const badgeTitle = isWebcam ? "📷 PHYSICAL OPTICS SNAPSHOT (JARVIS EYE)" : "📷 SCREEN PERCEPTION SNAPSHOT";
            widgetHtml += `
                <div class="hud-embedded-card screenshot-card" style="margin-top:12px; background:rgba(0,240,255,0.04); border:1px solid rgba(0,240,255,0.25); border-radius:8px; padding:10px; overflow:hidden;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; font-size:11px; color:#00f0ff; letter-spacing:1px; text-transform:uppercase; font-weight:700;">
                        <span>${badgeTitle}</span>
                        <span>${tele.resolution ? tele.resolution[0] + 'x' + tele.resolution[1] : '1280x720'} | ${tele.file_size_kb || 23} KB</span>
                    </div>
                    <a href="${shot}" target="_blank" title="Click to open full screenshot in new tab">
                        <img src="${shot}" alt="Captured Screen" style="width:100%; max-height:220px; object-fit:contain; border-radius:4px; border:1px solid rgba(0,240,255,0.2); transition:transform 0.2s;" onmouseover="this.style.transform='scale(1.01)'" onmouseout="this.style.transform='scale(1)'"/>
                    </a>
                    <div style="display:flex; justify-content:space-between; margin-top:6px; font-size:10px; color:#94a3b8;">
                        <span>Infer: <strong>${tele.infer_time_ms || 0}ms</strong> | Total: <strong>${tele.total_time_ms || 0}ms</strong></span>
                        <span style="color:#00f0ff;">⚡ MiniCPM-V (VRAM Evicted)</span>
                    </div>
                </div>
            `;
        }

        msgCard.innerHTML = `
            <div class="msg-avatar">${avatarLetter}</div>
            <div class="msg-content">
                <div class="msg-sender">${senderName}</div>
                <div class="msg-body">
                    ${formattedText}
                    ${widgetHtml}
                </div>
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

    // --- Instant Real-Time Speech-to-Text (Continuous Natural Speech Recognition) ---
    initSpeechRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            console.warn("[ASR] Native SpeechRecognition not supported in this browser. Please use Chrome, Edge, or Brave.");
            this.recognition = null;
            return;
        }

        this.recognition = new SpeechRecognition();
        this.recognition.continuous = true; // Stay listening continuously while user speaks
        this.recognition.interimResults = true;
        this.recognition.lang = 'en-US';
        this.recognitionSilenceTimer = null;
        this.silenceDelay = 3500; // 3.5 seconds of silence after speaking before auto-sending

        this.recognition.onstart = () => {
            this.isListening = true;
            this.voiceBtn.classList.add("listening");
            this.setReactorState("ACTIVE", "LISTENING (SPEAK FREELY)...");
        };

        this.recognition.onresult = (event) => {
            let fullTranscript = "";
            let interimTranscript = "";

            for (let i = 0; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    fullTranscript += event.results[i][0].transcript + " ";
                } else {
                    interimTranscript += event.results[i][0].transcript;
                }
            }

            const currentText = (fullTranscript + interimTranscript).trim();
            if (currentText) {
                this.chatInput.value = currentText;
                this.setReactorState("ACTIVE", `HEARD: "${currentText.slice(-28)}"`);

                // Reset silence timer whenever user speaks
                if (this.recognitionSilenceTimer) {
                    clearTimeout(this.recognitionSilenceTimer);
                }

                // Wait for natural 3.5s pause after speaking before auto-transmitting
                this.recognitionSilenceTimer = setTimeout(() => {
                    console.log("[ASR] Full message captured after complete sentence, transmitting...");
                    this.stopListening(true);
                }, this.silenceDelay);
            }
        };

        this.recognition.onerror = (event) => {
            console.warn("[ASR] Recognition error:", event.error);
            if (event.error === 'no-speech') {
                // Ignore transient no-speech pauses while waiting for user
                return;
            }
            this.stopListening(false);
        };

        this.recognition.onend = () => {
            if (this.isListening) {
                const text = this.chatInput.value.trim();
                if (!text) {
                    // Seamlessly keep listening if user hasn't started talking yet
                    try {
                        this.recognition.start();
                        return;
                    } catch (e) {}
                } else if (!this.recognitionSilenceTimer) {
                    // If recognition disconnected and text exists, finalize and transmit
                    this.stopListening(true);
                    return;
                }
            }
            this.isListening = false;
            this.voiceBtn.classList.remove("listening");
            this.setReactorState("STANDBY", "STANDBY");
        };
    }

    stopListening(shouldSend = false) {
        if (this.recognitionSilenceTimer) {
            clearTimeout(this.recognitionSilenceTimer);
            this.recognitionSilenceTimer = null;
        }

        this.isListening = false;
        this.voiceBtn.classList.remove("listening");
        this.setReactorState("STANDBY", "STANDBY");

        if (this.recognition) {
            try {
                this.recognition.stop();
            } catch (e) {}
        }

        if (shouldSend) {
            const text = this.chatInput.value.trim();
            if (text && text.length > 1) {
                this.sendMessage();
            }
        }
    }

    toggleListening() {
        if (!this.recognition) {
            alert("Speech recognition requires a supported browser (Google Chrome, Microsoft Edge, or Brave).");
            return;
        }

        if (this.isListening) {
            // User manually clicked mic to finish speaking -> transmit immediately
            this.stopListening(true);
        } else {
            // Start listening
            try {
                this.chatInput.value = "";
                if (this.recognitionSilenceTimer) {
                    clearTimeout(this.recognitionSilenceTimer);
                    this.recognitionSilenceTimer = null;
                }
                this.isListening = true;
                this.recognition.start();
            } catch (e) {
                console.warn("[ASR] Start recognition note:", e);
                try {
                    this.recognition.stop();
                    setTimeout(() => {
                        this.isListening = true;
                        this.recognition.start();
                    }, 200);
                } catch (e2) {}
            }
        }
    }

    // --- Instant Zero-Latency Voice Engine ---
    speak(audioUrl, textFallback = "") {
        if (!this.voiceEnabled) return;

        // Clean markdown, formatting symbols, and normalize dotted J.A.R.V.I.S. to fluent "Jarvis"
        let clean = (textFallback || "")
            .replace(/\bJ\.?A\.?R\.?V\.?I\.?S\.?\b/gi, 'Jarvis')
            .replace(/[*_~#`^|\\[\]]/g, '')
            .replace(/\(.*?\)/g, '')
            .replace(/<[^>]*>/g, '')
            .trim();

        // Mode 1: 0ms Zero-Latency (Immediate Browser OS Neural Synthesis)
        if (this.voiceEngine === "zero_latency" && clean) {
            this.speakBrowserFallback(clean);
            return;
        }

        // Mode 2: Studio Neural (Edge-TTS) with seamless instant fallback
        if (this.currentAudio) {
            try {
                this.currentAudio.pause();
                this.currentAudio.currentTime = 0;
            } catch (e) {}
            this.currentAudio = null;
        }

        if (window.speechSynthesis) {
            window.speechSynthesis.cancel();
        }

        if (audioUrl) {
            const audio = new Audio(audioUrl);
            audio.preload = "auto";
            this.currentAudio = audio;

            audio.onplay = () => this.setReactorState("ACTIVE", "SPEAKING (JARVIS NEURAL)");
            audio.onended = () => {
                this.setReactorState("STANDBY", "STANDBY");
                if (this.currentAudio === audio) this.currentAudio = null;
            };
            audio.onerror = (err) => {
                console.warn("[HUD] Edge-TTS playback note, falling back to 0ms WebSpeech:", err);
                if (this.currentAudio === audio) this.currentAudio = null;
                if (clean) this.speakBrowserFallback(clean);
            };

            audio.play().catch(e => {
                console.warn("[HUD] Audio autoplay requires user gesture:", e);
                if (clean) this.speakBrowserFallback(clean);
            });
        } else if (clean) {
            this.speakBrowserFallback(clean);
        }
    }

    speakBrowserFallback(text) {
        if (!window.speechSynthesis || !this.voiceEnabled) return;
        let clean = (text || "")
            .replace(/\bJ\.?A\.?R\.?V\.?I\.?S\.?\b/gi, 'Jarvis')
            .replace(/[*_~#`^|\\[\]]/g, '')
            .replace(/\(.*?\)/g, '')
            .trim();
        if (!clean) return;

        // Cancel previous utterances to avoid speech stacking
        window.speechSynthesis.cancel();

        const utterance = new SpeechSynthesisUtterance(clean);
        utterance.lang = "en-GB";

        // Prioritize natural British voices (George, Ryan, UK English, Hazel, Oliver)
        const getPreferredVoice = () => {
            const voices = window.speechSynthesis.getVoices();
            return voices.find(v => 
                v.lang === "en-GB" || 
                v.name.includes("UK") || 
                v.name.includes("British") || 
                v.name.includes("George") ||
                v.name.includes("Ryan") ||
                v.name.includes("Oliver") ||
                v.name.includes("Natural")
            ) || voices.find(v => v.lang.startsWith("en"));
        };

        const preferred = getPreferredVoice();
        if (preferred) utterance.voice = preferred;
        utterance.rate = 1.05; // Crisp executive cadence

        utterance.onstart = () => this.setReactorState("ACTIVE", "SPEAKING (0ms INSTANT)");
        utterance.onended = () => this.setReactorState("STANDBY", "STANDBY");
        utterance.onerror = () => this.setReactorState("STANDBY", "STANDBY");

        window.speechSynthesis.speak(utterance);
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

        if (this.gestureToggleBtn) {
            this.gestureToggleBtn.addEventListener("click", () => {
                if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                    this.ws.send(JSON.stringify({ action: "toggle_gestures" }));
                }
            });
        }

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
