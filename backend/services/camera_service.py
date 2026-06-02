"""
Camera Service — Dual Camera Management untuk Raspberry Pi 5
Mendukung: Pi Camera v3, USB Camera, dan IP Camera
"""

import asyncio
import cv2
import numpy as np
import threading
import time
import logging
from typing import Optional, Dict, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import os

from core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class CameraFrame:
    """Container untuk frame kamera dengan metadata."""
    camera_id: int
    frame: np.ndarray
    timestamp: datetime
    frame_number: int


@dataclass
class CameraStatus:
    """Status kamera."""
    camera_id: int
    is_active: bool
    fps: float
    frame_count: int
    last_frame_time: Optional[datetime]
    error: Optional[str] = None


class CameraCapture:
    """Single camera capture thread."""

    def __init__(
        self,
        camera_id: int,
        device_index: int,
        width: int = 1280,
        height: int = 720,
        fps: int = 30,
    ):
        self.camera_id = camera_id
        self.device_index = device_index
        self.width = width
        self.height = height
        self.target_fps = fps

        self._cap: Optional[cv2.VideoCapture] = None
        self._frame: Optional[np.ndarray] = None
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._frame_count = 0
        self._fps = 0.0
        self._last_error: Optional[str] = None
        self._last_frame_time: Optional[datetime] = None

    def start(self) -> bool:
        """Start camera capture in background thread."""
        try:
            self._cap = cv2.VideoCapture(self.device_index)
            if not self._cap.isOpened():
                self._last_error = f"Cannot open camera {self.device_index}"
                logger.error(self._last_error)
                return False

            # Configure camera
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self._cap.set(cv2.CAP_PROP_FPS, self.target_fps)
            self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce latency

            # Try hardware acceleration
            self._cap.set(cv2.CAP_PROP_HW_ACCELERATION, cv2.VIDEO_ACCELERATION_ANY)

            self._running = True
            self._thread = threading.Thread(
                target=self._capture_loop,
                daemon=True,
                name=f"Camera-{self.camera_id}",
            )
            self._thread.start()
            logger.info(f"✅ Camera {self.camera_id} started (device: {self.device_index})")
            return True

        except Exception as e:
            self._last_error = str(e)
            logger.error(f"Failed to start camera {self.camera_id}: {e}")
            return False

    def _capture_loop(self):
        """Background frame capture loop."""
        fps_counter = 0
        fps_start = time.time()

        while self._running:
            try:
                ret, frame = self._cap.read()
                if not ret:
                    logger.warning(f"Camera {self.camera_id}: failed to read frame")
                    time.sleep(0.1)
                    continue

                with self._lock:
                    self._frame = frame
                    self._frame_count += 1
                    self._last_frame_time = datetime.now()

                # Calculate FPS
                fps_counter += 1
                elapsed = time.time() - fps_start
                if elapsed >= 1.0:
                    self._fps = fps_counter / elapsed
                    fps_counter = 0
                    fps_start = time.time()

            except Exception as e:
                logger.error(f"Camera {self.camera_id} capture error: {e}")
                self._last_error = str(e)
                time.sleep(0.5)

    def get_frame(self) -> Optional[np.ndarray]:
        """Get the latest frame (thread-safe)."""
        with self._lock:
            if self._frame is not None:
                return self._frame.copy()
            return None

    def get_jpeg(self, quality: int = 85) -> Optional[bytes]:
        """Get latest frame as JPEG bytes for streaming."""
        frame = self.get_frame()
        if frame is None:
            return None
        ret, buffer = cv2.imencode(
            ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality]
        )
        if ret:
            return buffer.tobytes()
        return None

    def stop(self):
        """Stop capture thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        if self._cap:
            self._cap.release()
        logger.info(f"Camera {self.camera_id} stopped")

    @property
    def status(self) -> CameraStatus:
        return CameraStatus(
            camera_id=self.camera_id,
            is_active=self._running and self._frame is not None,
            fps=self._fps,
            frame_count=self._frame_count,
            last_frame_time=self._last_frame_time,
            error=self._last_error,
        )


class CameraService:
    """
    Service pengelola dual kamera untuk sistem monitoring kepiting.
    Mendukung hot-reload kamera dan fallback ke dummy frame.
    """

    def __init__(self):
        self._cameras: Dict[int, CameraCapture] = {}
        self._started = False

    async def initialize(self):
        """Initialize semua kamera."""
        if self._started:
            return

        # Camera 1 — Top View
        cam1 = CameraCapture(
            camera_id=1,
            device_index=settings.CAMERA_1_INDEX,
            width=settings.CAMERA_1_WIDTH,
            height=settings.CAMERA_1_HEIGHT,
            fps=settings.CAMERA_FPS,
        )
        success1 = cam1.start()
        if success1:
            self._cameras[1] = cam1
        else:
            logger.warning("Camera 1 unavailable — using dummy mode")

        # Camera 2 — Side View
        cam2 = CameraCapture(
            camera_id=2,
            device_index=settings.CAMERA_2_INDEX,
            width=settings.CAMERA_2_WIDTH,
            height=settings.CAMERA_2_HEIGHT,
            fps=settings.CAMERA_FPS,
        )
        success2 = cam2.start()
        if success2:
            self._cameras[2] = cam2
        else:
            logger.warning("Camera 2 unavailable — using dummy mode")

        self._started = True
        await asyncio.sleep(0.5)  # Allow cameras to warm up
        logger.info(f"Camera service initialized — {len(self._cameras)} camera(s) active")

    def get_frame(self, camera_id: int) -> Optional[np.ndarray]:
        """Get current frame from specified camera."""
        if camera_id in self._cameras:
            return self._cameras[camera_id].get_frame()
        return self._create_dummy_frame(camera_id)

    def get_jpeg(self, camera_id: int, quality: int = 85) -> Optional[bytes]:
        """Get current frame as JPEG for HTTP streaming."""
        if camera_id in self._cameras:
            return self._cameras[camera_id].get_jpeg(quality)
        # Dummy frame for testing
        dummy = self._create_dummy_frame(camera_id)
        if dummy is not None:
            ret, buf = cv2.imencode(".jpg", dummy, [cv2.IMWRITE_JPEG_QUALITY, quality])
            return buf.tobytes() if ret else None
        return None

    def _create_dummy_frame(self, camera_id: int) -> np.ndarray:
        """Create dummy frame when camera is not available."""
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        frame[:] = (30, 30, 30)  # Dark background
        
        # Add text overlay
        text = f"Camera {camera_id} - Not Available"
        cv2.putText(frame, text, (400, 340), cv2.FONT_HERSHEY_SIMPLEX,
                    1.5, (100, 100, 100), 2)
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, timestamp, (480, 400), cv2.FONT_HERSHEY_SIMPLEX,
                    0.8, (80, 80, 80), 1)
        return frame

    def save_frame(self, camera_id: int, output_dir: str, filename: str) -> Optional[str]:
        """Save current frame to disk."""
        frame = self.get_frame(camera_id)
        if frame is None:
            return None

        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)
        cv2.imwrite(filepath, frame)
        return filepath

    def get_status(self) -> Dict[int, dict]:
        """Get status of all cameras."""
        status = {}
        for cam_id, cam in self._cameras.items():
            s = cam.status
            status[cam_id] = {
                "active": s.is_active,
                "fps": round(s.fps, 1),
                "frame_count": s.frame_count,
                "last_frame": s.last_frame_time.isoformat() if s.last_frame_time else None,
                "error": s.error,
            }
        # Add offline cameras
        for cam_id in [1, 2]:
            if cam_id not in status:
                status[cam_id] = {"active": False, "fps": 0, "frame_count": 0,
                                   "last_frame": None, "error": "Not initialized"}
        return status

    async def stop_all(self):
        """Stop all cameras."""
        for cam in self._cameras.values():
            cam.stop()
        self._cameras.clear()
        self._started = False

    async def mjpeg_stream(self, camera_id: int):
        """
        Async generator untuk MJPEG streaming.
        Digunakan oleh FastAPI StreamingResponse.
        """
        if not self._started:
            await self.initialize()

        frame_interval = 1.0 / settings.STREAM_FPS

        while True:
            start = time.time()
            jpeg = self.get_jpeg(camera_id, quality=settings.STREAM_QUALITY)

            if jpeg:
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n"
                )

            elapsed = time.time() - start
            sleep_time = max(0, frame_interval - elapsed)
            await asyncio.sleep(sleep_time)


# Singleton instance
camera_service = CameraService()
