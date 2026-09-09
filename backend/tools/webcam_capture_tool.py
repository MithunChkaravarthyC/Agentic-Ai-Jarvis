"""
webcam_capture_tool.py — On-Demand Single-Shot Physical Camera Capture for J.A.R.V.I.S.
Captures a single high-fidelity frame from the user's webcam for physical object,
document, and scene understanding via MiniCPM-V.
Zero persistent VRAM overhead; immediately closes camera or samples from active stream.
"""

import os
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional

import cv2
from PIL import Image

from backend.config import SCREENSHOTS_DIR

logger = logging.getLogger("WebcamCaptureTool")


class WebcamCaptureTool:
    """Tool to capture single-shot webcam photos for physical world perception."""

    def __init__(self, camera_index: int = 0):
        self.camera_index = camera_index
        self.max_dimension = 1280
        self.jpeg_quality = 80
        SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    def capture(self, camera_index: Optional[int] = None) -> Dict[str, Any]:
        """
        Capture a single webcam frame with auto-exposure stabilization.
        Safely coordinates with GestureDetector if the camera is already open.
        """
        import numpy as np

        start_time = time.perf_counter()
        cam_idx = camera_index if camera_index is not None else self.camera_index
        timestamp = int(time.time() * 1000)
        output_filename = f"webcam_{timestamp}.jpg"
        output_path = SCREENSHOTS_DIR / output_filename

        frame = None
        source_mode = "dedicated_capture"

        # Check if gesture_detector is currently streaming on the same camera
        try:
            from backend.tools.gesture_detector import gesture_detector
            if gesture_detector.is_tracking:
                source_mode = "gesture_stream_sample"
                for _ in range(25):
                    latest = gesture_detector.get_latest_frame()
                    if latest is not None and np.mean(latest) > 5.0:
                        frame = latest
                        break
                    time.sleep(0.1)

                if frame is None and gesture_detector.is_tracking:
                    logger.warning("Active gesture stream frame pending; using fallback.")
                    return self._create_fallback_frame(output_path, start_time)
        except Exception as ge:
            logger.debug(f"Gesture stream check note: {ge}")

        # If not sampled from gesture stream, open dedicated camera capture
        if frame is None:
            # Backends to try in order of Windows compatibility
            backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY] if os.name == 'nt' else [cv2.CAP_ANY]
            
            for attempt in range(3):
                for backend_flag in backends:
                    cap = cv2.VideoCapture(cam_idx, backend_flag)
                    if not cap.isOpened():
                        continue

                    try:
                        # Attempt to set 1280x720, but accept native if unsupported
                        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

                        # Warmup read loop: read 6 frames so auto-exposure and white balance settle
                        captured_frame = None
                        for _ in range(6):
                            ret, temp_f = cap.read()
                            if ret and temp_f is not None:
                                captured_frame = temp_f

                        # If the frame is still too dark (exposure ramping up), grab up to 6 more
                        if captured_frame is not None and np.mean(captured_frame) < 18.0:
                            for _ in range(6):
                                ret, temp_f = cap.read()
                                if ret and temp_f is not None and np.mean(temp_f) >= 18.0:
                                    captured_frame = temp_f
                                    break

                        if captured_frame is not None:
                            frame = captured_frame
                            break
                    finally:
                        cap.release()

                if frame is not None:
                    break
                time.sleep(0.15)

        # Fallback if no webcam hardware is present or accessible
        if frame is None:
            logger.warning("Webcam capture unavailable; creating visual fallback frame.")
            return self._create_fallback_frame(output_path, start_time)

        # Process and compress frame
        h, w = frame.shape[:2]
        orig_res = (w, h)

        # Downscale if larger than max_dimension
        if max(w, h) > self.max_dimension:
            scale = self.max_dimension / float(max(w, h))
            new_w, new_h = int(w * scale), int(h * scale)
            frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
        else:
            new_w, new_h = w, h

        # Save as optimized JPEG
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality]
        cv2.imwrite(str(output_path), frame, encode_param)

        latency_ms = round((time.perf_counter() - start_time) * 1000.0, 1)
        file_size_kb = round(output_path.stat().st_size / 1024.0, 1)

        logger.info(
            f"[WebcamCapture] Mode: {source_mode} | Res: {orig_res} -> ({new_w}, {new_h}) | "
            f"Size: {file_size_kb} KB | Latency: {latency_ms} ms -> {output_filename}"
        )

        return {
            "status": "success",
            "image_path": str(output_path),
            "filename": output_filename,
            "url": f"/screenshots/{output_filename}",
            "latency_ms": latency_ms,
            "resolution": (new_w, new_h),
            "file_size_kb": file_size_kb,
            "source_mode": source_mode
        }

    def _create_fallback_frame(self, output_path: Path, start_time: float) -> Dict[str, Any]:
        """Generate high-fidelity fallback card when webcam is disabled or blocked."""
        from PIL import ImageDraw, ImageFont
        width, height = 1280, 720
        img = Image.new("RGB", (width, height), color=(6, 11, 25))
        draw = ImageDraw.Draw(img)

        # Draw tech border & gridlines
        draw.rectangle([(20, 20), (width - 20, height - 20)], outline=(0, 240, 255), width=2)
        draw.line([(40, 60), (width - 40, 60)], fill=(0, 240, 255), width=1)

        draw.text((50, 32), "J.A.R.V.I.S. OPTICAL SENSOR // STANDBY", fill=(0, 240, 255))
        draw.text((50, 120), "Physical Camera Lens Initializing...", fill=(248, 250, 252))
        draw.text((50, 160), "Object Detection & Scene Analysis Standing By", fill=(148, 163, 184))
        draw.text((50, 220), "Ensure webcam permissions are granted in Windows Settings.", fill=(245, 158, 11))

        img.save(str(output_path), "JPEG", quality=80)
        latency_ms = round((time.perf_counter() - start_time) * 1000.0, 1)
        file_size_kb = round(output_path.stat().st_size / 1024.0, 1)

        return {
            "status": "fallback",
            "image_path": str(output_path),
            "filename": output_path.name,
            "url": f"/screenshots/{output_path.name}",
            "latency_ms": latency_ms,
            "resolution": (width, height),
            "file_size_kb": file_size_kb,
            "source_mode": "fallback_renderer"
        }


# Global singleton instance
webcam_capture_tool = WebcamCaptureTool()
