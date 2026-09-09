"""
gesture_detector.py — Real-Time On-Demand Hand Gesture Recognition for J.A.R.V.I.S.
Utilizes MediaPipe Tasks GestureRecognizer running on CPU (TFLite XNNPACK delegate).
Guarantees zero persistent VRAM residency to preserve 8GB VRAM limit on RTX 4060.
"""

import os
import time
import logging
import threading
from collections import deque
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

logger = logging.getLogger("GestureDetector")

# Base directory paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODEL_PATH = BASE_DIR / "backend" / "models" / "gesture_recognizer.task"

# Canonical Action Mappings
GESTURE_ACTION_MAP = {
    "Open_Palm": {
        "gesture": "OPEN_PALM",
        "action": "silence_speech",
        "label": "✋ OPEN PALM (SILENCE)",
        "description": "Stop and silence current speech / audio playback"
    },
    "Thumb_Up": {
        "gesture": "THUMBS_UP",
        "action": "confirm_payment",
        "label": "👍 THUMBS UP (APPROVE)",
        "description": "Approve security gate / confirm booking & payment"
    },
    "Thumb_Down": {
        "gesture": "THUMBS_DOWN",
        "action": "cancel_payment",
        "label": "👎 THUMBS DOWN (REJECT)",
        "description": "Reject security gate / cancel pending booking"
    },
    "Victory": {
        "gesture": "PEACE_SIGN",
        "action": "wake_listening",
        "label": "✌️ PEACE / VICTORY (WAKE)",
        "description": "Toggle voice listening status"
    },
    "Pointing_Up": {
        "gesture": "POINT_UP",
        "action": "scroll_next",
        "label": "☝️ POINT UP (NEXT)",
        "description": "Acknowledge / navigate viewport"
    },
    "Closed_Fist": {
        "gesture": "FIST",
        "action": "standby",
        "label": "✊ CLOSED FIST (STANDBY)",
        "description": "Return to standby mode"
    }
}


class GestureDetector:
    """Autonomous CPU-based Hand Gesture Recognition Engine for J.A.R.V.I.S."""

    def __init__(self, model_path: Optional[Path] = None):
        self.model_path = model_path or MODEL_PATH
        self.is_tracking = False
        self.camera_index = 0
        self.cap: Optional[cv2.VideoCapture] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Debounce and consensus buffer
        self.history_len = 5
        self.history = deque(maxlen=self.history_len)
        self.last_emitted_gesture = "None"
        self.last_emitted_time = 0.0
        self.cooldown_seconds = 1.2  # Prevent duplicate rapid triggers

        # Callbacks (sync or async dispatcher)
        self.callbacks: List[Callable[[Dict[str, Any]], Any]] = []

        # Latest frame cache for zero-latency camera sharing with VisionAgent
        self.latest_frame = None
        self._frame_lock = threading.Lock()

        # Initialize MediaPipe Recognizer
        self.recognizer = self._init_recognizer()

    def get_latest_frame(self):
        """Thread-safe snapshot of the latest camera frame if tracking is active."""
        with self._frame_lock:
            if self.is_tracking and self.latest_frame is not None:
                return self.latest_frame.copy()
        return None

    def _init_recognizer(self):
        """Load MediaPipe GestureRecognizer with CPU XNNPACK delegate."""
        if not self.model_path.exists():
            logger.warning(f"Gesture model not found at {self.model_path}. Downloading...")
            import urllib.request
            self.model_path.parent.mkdir(parents=True, exist_ok=True)
            url = "https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/1/gesture_recognizer.task"
            urllib.request.urlretrieve(url, str(self.model_path))

        base_options = python.BaseOptions(model_asset_path=str(self.model_path))
        options = vision.GestureRecognizerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            num_hands=1,
            min_hand_detection_confidence=0.6,
            min_hand_presence_confidence=0.6,
            min_tracking_confidence=0.5
        )
        logger.info(f"[GestureDetector] Loaded MediaPipe GestureRecognizer from {self.model_path.name}")
        return vision.GestureRecognizer.create_from_options(options)

    def register_callback(self, callback: Callable[[Dict[str, Any]], Any]):
        """Register a callback handler for emitted gestures."""
        if callback not in self.callbacks:
            self.callbacks.append(callback)

    def classify_frame(self, frame_bgr) -> Optional[Dict[str, Any]]:
        """Classify a single OpenCV BGR image frame."""
        try:
            rgb_frame = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            recognition_result = self.recognizer.recognize(mp_image)

            if not recognition_result.gestures or not recognition_result.gestures[0]:
                return None

            top_gesture = recognition_result.gestures[0][0]
            category_name = top_gesture.category_name
            score = float(top_gesture.score)

            handedness = "Unknown"
            if recognition_result.handedness and recognition_result.handedness[0]:
                handedness = recognition_result.handedness[0][0].category_name

            mapping = GESTURE_ACTION_MAP.get(category_name, {
                "gesture": category_name,
                "action": "none",
                "label": category_name,
                "description": "Unmapped gesture"
            })

            return {
                "raw_category": category_name,
                "gesture": mapping["gesture"],
                "action": mapping["action"],
                "label": mapping["label"],
                "score": round(score, 3),
                "handedness": handedness,
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"[GestureDetector] Error classifying frame: {e}")
            return None

    def _process_gesture_consensus(self, detected: Optional[Dict[str, Any]]):
        """Apply rolling consensus and cooldown to prevent jitter."""
        current_gesture = detected["gesture"] if detected else "None"
        self.history.append(current_gesture)

        if len(self.history) < self.history_len:
            return

        # Check if the same gesture is present in at least 3 of the last 5 frames
        counts = {}
        for g in self.history:
            counts[g] = counts.get(g, 0) + 1

        top_g, top_count = max(counts.items(), key=lambda x: x[1])
        now = time.time()

        if top_g != "None" and top_count >= 3:
            if top_g != self.last_emitted_gesture or (now - self.last_emitted_time) > self.cooldown_seconds:
                self.last_emitted_gesture = top_g
                self.last_emitted_time = now

                payload = detected if (detected and detected["gesture"] == top_g) else {
                    "gesture": top_g,
                    "action": GESTURE_ACTION_MAP.get(top_g, {}).get("action", "none"),
                    "label": GESTURE_ACTION_MAP.get(top_g, {}).get("label", top_g),
                    "score": 0.95,
                    "timestamp": now
                }

                logger.info(f"[GestureDetector] >> Consensus Gesture Triggered: {payload['label']}")
                self._dispatch_callbacks(payload)

    def _dispatch_callbacks(self, payload: Dict[str, Any]):
        """Dispatch payload to registered callbacks."""
        for cb in self.callbacks:
            try:
                cb(payload)
            except Exception as e:
                logger.error(f"[GestureDetector] Callback execution error: {e}")

    def _tracking_loop(self):
        """Worker thread executing video capture and classification."""
        logger.info(f"[GestureDetector] Starting video capture on device {self.camera_index}...")
        self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW if os.name == 'nt' else cv2.CAP_ANY)
        
        if not self.cap.isOpened():
            # Try default without backend flag
            self.cap = cv2.VideoCapture(self.camera_index)

        if not self.cap.isOpened():
            logger.warning(f"[GestureDetector] Could not open camera {self.camera_index}. Tracking disabled.")
            self.is_tracking = False
            return

        # Configure camera resolution for low-latency CPU processing
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)

        last_activity_time = time.time()
        inactivity_timeout_seconds = 180.0  # Auto-release camera after 3 minutes of no hands detected

        while not self._stop_event.is_set():
            ret, frame = self.cap.read()
            if not ret or frame is None:
                time.sleep(0.03)
                continue

            with self._frame_lock:
                self.latest_frame = frame.copy()

            # Process every frame
            detected = self.classify_frame(frame)
            if detected:
                last_activity_time = time.time()
            elif (time.time() - last_activity_time) > inactivity_timeout_seconds:
                logger.info("[GestureDetector] Inactivity timeout (3 min without hand detection). Auto-releasing camera.")
                break

            self._process_gesture_consensus(detected)

            # Cap frame rate to ~25-30 FPS to minimize CPU usage
            time.sleep(0.035)

        self.is_tracking = False

        if self.cap:
            self.cap.release()
            self.cap = None
        logger.info("[GestureDetector] Video capture thread cleanly terminated.")

    def start(self, camera_index: int = 0) -> Dict[str, Any]:
        """Start on-demand gesture tracking."""
        if self.is_tracking:
            return {"status": "already_running", "message": "Gesture tracking is already active."}

        self.camera_index = camera_index
        self._stop_event.clear()
        self.history.clear()
        self.last_emitted_gesture = "None"
        self.is_tracking = True

        self._thread = threading.Thread(target=self._tracking_loop, daemon=True, name="JarvisGestureThread")
        self._thread.start()
        logger.info("[GestureDetector] Gesture tracking activated.")
        return {"status": "started", "message": "Gesture control activated. Standing by for hand gestures."}

    def stop(self) -> Dict[str, Any]:
        """Stop gesture tracking and release webcam."""
        if not self.is_tracking:
            return {"status": "not_running", "message": "Gesture tracking is not active."}

        self._stop_event.set()
        self.is_tracking = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._thread = None

        if self.cap:
            self.cap.release()
            self.cap = None

        logger.info("[GestureDetector] Gesture tracking deactivated.")
        return {"status": "stopped", "message": "Gesture control deactivated. Webcam released."}

    def toggle(self, camera_index: int = 0) -> Dict[str, Any]:
        """Toggle tracking status."""
        if self.is_tracking:
            return self.stop()
        else:
            return self.start(camera_index=camera_index)

    def simulate_gesture(self, gesture_name: str) -> Dict[str, Any]:
        """Simulate a gesture detection for automated testing without requiring a live camera."""
        mapping = GESTURE_ACTION_MAP.get(gesture_name, {
            "gesture": gesture_name,
            "action": "none",
            "label": gesture_name,
            "description": "Simulated gesture"
        })
        payload = {
            "raw_category": gesture_name,
            "gesture": mapping["gesture"],
            "action": mapping["action"],
            "label": mapping["label"],
            "score": 0.98,
            "handedness": "Right",
            "timestamp": time.time(),
            "simulated": True
        }
        self._dispatch_callbacks(payload)
        return payload


# Global singleton instance
gesture_detector = GestureDetector()
