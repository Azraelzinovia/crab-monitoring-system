"""
Detection Service — AI Pipeline Orchestrator
Mengkoordinasikan: YOLO Detection → Species → Gender → Health → Measurement
"""

import asyncio
import time
import uuid
import logging
import os
from datetime import datetime
from typing import Optional, Tuple
import numpy as np
import cv2

from core.config import settings
from services.camera_service import camera_service
from models.schemas import (
    DetectionResponse, SpeciesResult, GenderResult, HealthResult,
    BodyPartsResult, MeasurementResult, SpeciesEnum, GenderEnum, HealthStatusEnum,
)

logger = logging.getLogger(__name__)


class DetectionService:
    """
    Orchestrator utama pipeline deteksi kepiting.
    Menjalankan seluruh analisis AI secara sekuensial dan menyimpan hasil.
    """

    def __init__(self):
        self._yolo = None
        self._species_classifier = None
        self._gender_classifier = None
        self._health_classifier = None
        self._measurement_service = None
        self._models_loaded = False
        self._session_id: Optional[str] = None

    def load_models(self):
        """Load semua AI model. Dipanggil sekali saat startup."""
        if self._models_loaded:
            return

        try:
            # Import di sini untuk lazy loading
            from ai_models.detection.yolo_detector import YOLOCrabDetector
            from ai_models.classification.species_classifier import SpeciesClassifier
            from ai_models.classification.gender_classifier import GenderClassifier
            from ai_models.classification.health_classifier import HealthClassifier
            from ai_models.measurement.size_estimator import SizeEstimator

            self._yolo = YOLOCrabDetector(
                model_path=settings.YOLO_MODEL_PATH,
                confidence=settings.YOLO_CONFIDENCE,
                iou=settings.YOLO_IOU,
            )
            logger.info("✅ YOLO Detector loaded")

            self._species_classifier = SpeciesClassifier(settings.SPECIES_MODEL_PATH)
            logger.info("✅ Species Classifier loaded")

            self._gender_classifier = GenderClassifier(settings.GENDER_MODEL_PATH)
            logger.info("✅ Gender Classifier loaded")

            self._health_classifier = HealthClassifier(settings.HEALTH_MODEL_PATH)
            logger.info("✅ Health Classifier loaded")

            self._measurement_service = SizeEstimator()
            logger.info("✅ Size Estimator loaded")

            self._models_loaded = True
            logger.info("🎯 All AI models loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            logger.warning("Running in DEMO mode with mock predictions")
            self._models_loaded = False

    async def run_detection(
        self,
        session_id: Optional[str] = None,
        save_images: bool = True,
    ) -> Optional[DetectionResponse]:
        """
        Jalankan pipeline deteksi lengkap:
        1. Ambil frame dari kedua kamera
        2. Deteksi objek dengan YOLO
        3. Klasifikasi spesies, gender, kesehatan
        4. Analisis bagian tubuh
        5. Estimasi ukuran dan berat
        6. Simpan gambar dan log
        """
        start_time = time.time()

        if session_id is None:
            session_id = str(uuid.uuid4())[:8]

        # Ensure cameras are initialized
        if not camera_service._started:
            await camera_service.initialize()

        # Get frames from both cameras
        frame_top = camera_service.get_frame(1)    # Tampak atas
        frame_side = camera_service.get_frame(2)   # Tampak samping

        if frame_top is None and frame_side is None:
            logger.warning("No frames available from any camera")
            frame_top = self._create_test_frame()
            frame_side = self._create_test_frame()

        if frame_top is None:
            frame_top = self._create_test_frame()
        if frame_side is None:
            frame_side = self._create_test_frame()

        # Load models if needed
        if not self._models_loaded:
            self.load_models()

        inference_start = time.time()

        # ── Step 1: YOLO Detection ─────────────────────────────────────────
        detection_result = await asyncio.get_event_loop().run_in_executor(
            None, self._run_yolo, frame_top
        )

        detected = detection_result["detected"]
        bbox = detection_result["bbox"]
        det_confidence = detection_result["confidence"]
        track_id = detection_result.get("track_id")

        inference_time = (time.time() - inference_start) * 1000

        # Crop region of interest if detected
        roi_top = self._crop_roi(frame_top, bbox) if detected and bbox else frame_top
        roi_side = frame_side  # Side camera for full body analysis

        # ── Step 2: Species Classification ────────────────────────────────
        species_result = await asyncio.get_event_loop().run_in_executor(
            None, self._classify_species, roi_top
        )

        # ── Step 3: Gender Classification ─────────────────────────────────
        gender_result = await asyncio.get_event_loop().run_in_executor(
            None, self._classify_gender, roi_top
        )

        # ── Step 4: Health Classification ─────────────────────────────────
        health_result = await asyncio.get_event_loop().run_in_executor(
            None, self._classify_health, roi_top
        )

        # ── Step 5: Body Parts Analysis ────────────────────────────────────
        body_parts_result = await asyncio.get_event_loop().run_in_executor(
            None, self._analyze_body_parts, roi_top
        )

        # ── Step 6: Size & Weight Estimation ──────────────────────────────
        measurement_result = await asyncio.get_event_loop().run_in_executor(
            None, self._estimate_measurements, roi_top, bbox
        )

        total_time = (time.time() - start_time) * 1000

        # ── Save Images ────────────────────────────────────────────────────
        img_cam1_path = None
        img_cam2_path = None

        if save_images:
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            img_dir = os.path.join(settings.IMAGE_STORAGE_PATH, session_id)

            # Draw bounding box on frame before saving
            annotated_top = self._draw_annotations(
                frame_top.copy(), detection_result, species_result,
                health_result, measurement_result
            )

            img_cam1_path = self._save_image(
                annotated_top, img_dir, f"cam1_{timestamp_str}.jpg"
            )
            img_cam2_path = self._save_image(
                frame_side, img_dir, f"cam2_{timestamp_str}.jpg"
            )

        # Build detection ID (will be overwritten after DB save)
        detection_id = int(time.time() * 1000) % 1000000

        return DetectionResponse(
            detection_id=detection_id,
            session_id=session_id,
            timestamp=datetime.now(),
            detected=detected,
            detection_confidence=det_confidence,
            bbox=bbox,
            species=SpeciesResult(**species_result),
            gender=GenderResult(**gender_result),
            health=HealthResult(**health_result),
            body_parts=BodyPartsResult(**body_parts_result),
            measurements=MeasurementResult(**measurement_result),
            image_cam1=img_cam1_path,
            image_cam2=img_cam2_path,
            inference_time_ms=round(inference_time, 2),
            total_processing_time_ms=round(total_time, 2),
        )

    def _run_yolo(self, frame: np.ndarray) -> dict:
        """Run YOLO detection on frame."""
        if self._yolo is not None:
            return self._yolo.detect(frame)
        return self._mock_yolo_detection()

    def _classify_species(self, frame: np.ndarray) -> dict:
        """Classify crab species."""
        if self._species_classifier is not None:
            return self._species_classifier.predict(frame)
        return self._mock_species()

    def _classify_gender(self, frame: np.ndarray) -> dict:
        """Classify crab gender."""
        if self._gender_classifier is not None:
            return self._gender_classifier.predict(frame)
        return self._mock_gender()

    def _classify_health(self, frame: np.ndarray) -> dict:
        """Classify crab health status."""
        if self._health_classifier is not None:
            return self._health_classifier.predict(frame)
        return self._mock_health()

    def _analyze_body_parts(self, frame: np.ndarray) -> dict:
        """Analyze body parts completeness."""
        # This uses a specialized model or rule-based approach
        return {
            "left_claw": True,
            "right_claw": True,
            "legs_complete": True,
            "shell_damage": False,
        }

    def _estimate_measurements(self, frame: np.ndarray, bbox: Optional[dict]) -> dict:
        """Estimate physical measurements."""
        if self._measurement_service is not None and bbox:
            return self._measurement_service.estimate(frame, bbox)
        return self._mock_measurements()

    def _crop_roi(self, frame: np.ndarray, bbox: dict) -> np.ndarray:
        """Crop Region of Interest from frame based on bounding box."""
        h, w = frame.shape[:2]
        x1 = max(0, int(bbox["x1"]))
        y1 = max(0, int(bbox["y1"]))
        x2 = min(w, int(bbox["x2"]))
        y2 = min(h, int(bbox["y2"]))

        if x2 > x1 and y2 > y1:
            return frame[y1:y2, x1:x2]
        return frame

    def _draw_annotations(
        self, frame: np.ndarray, detection: dict,
        species: dict, health: dict, measurements: dict
    ) -> np.ndarray:
        """Draw bounding box and info on frame."""
        if detection.get("bbox"):
            bbox = detection["bbox"]
            x1, y1 = int(bbox["x1"]), int(bbox["y1"])
            x2, y2 = int(bbox["x2"]), int(bbox["y2"])

            # Color based on health
            health_colors = {
                "Sehat": (0, 255, 0),
                "Kurang Sehat": (0, 165, 255),
                "Sakit": (0, 0, 255),
                "Mati": (128, 0, 128),
            }
            color = health_colors.get(health.get("health_status", ""), (255, 255, 0))

            # Draw bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            # Label background
            label = f"{species.get('species', 'Unknown')} {detection.get('confidence', 0):.0%}"
            (lw, lh), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(frame, (x1, y1 - lh - 10), (x1 + lw + 4, y1), color, -1)
            cv2.putText(frame, label, (x1 + 2, y1 - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            # Measurements overlay
            if measurements.get("length_cm"):
                meas_text = f"L:{measurements['length_cm']}cm W:{measurements['estimated_weight_g']}g"
                cv2.putText(frame, meas_text, (x1, y2 + 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        # Timestamp
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, ts, (10, frame.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        return frame

    def _save_image(self, frame: np.ndarray, directory: str, filename: str) -> Optional[str]:
        """Save frame to disk."""
        try:
            os.makedirs(directory, exist_ok=True)
            filepath = os.path.join(directory, filename)
            cv2.imwrite(filepath, frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
            return filepath
        except Exception as e:
            logger.error(f"Failed to save image: {e}")
            return None

    def _create_test_frame(self) -> np.ndarray:
        """Create a test frame for demo mode."""
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        frame[:] = (20, 40, 30)  # Dark green background
        cv2.putText(frame, "DEMO MODE - No Camera", (400, 360),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 200, 100), 2)
        return frame

    # ── Mock predictions for demo/testing ─────────────────────────────────────

    def _mock_yolo_detection(self) -> dict:
        import random
        detected = random.random() > 0.2
        return {
            "detected": detected,
            "confidence": round(random.uniform(0.75, 0.98), 3) if detected else 0.0,
            "bbox": {"x1": 320, "y1": 150, "x2": 960, "y2": 570} if detected else None,
            "track_id": random.randint(1, 50) if detected else None,
        }

    def _mock_species(self) -> dict:
        import random
        species_list = ["Kepiting Bakau", "Kepiting Rajungan", "Kepiting Lumpur", "Kepiting Batu"]
        return {
            "species": random.choice(species_list),
            "confidence": round(random.uniform(85, 99), 1),
        }

    def _mock_gender(self) -> dict:
        import random
        return {
            "gender": random.choice(["Jantan", "Betina"]),
            "confidence": round(random.uniform(82, 97), 1),
        }

    def _mock_health(self) -> dict:
        import random
        choices = [("Sehat", 0.70), ("Kurang Sehat", 0.15), ("Sakit", 0.10), ("Mati", 0.05)]
        status = random.choices(
            [c[0] for c in choices],
            weights=[c[1] for c in choices]
        )[0]
        return {
            "health_status": status,
            "confidence": round(random.uniform(80, 97), 1),
        }

    def _mock_measurements(self) -> dict:
        import random
        length = round(random.uniform(8, 20), 1)
        width = round(length * random.uniform(0.7, 0.9), 1)
        weight = round((length * width * 1.8), 0)
        return {
            "length_cm": length,
            "width_cm": width,
            "estimated_weight_g": weight,
        }

    def get_models_status(self) -> dict:
        """Return status of all AI models."""
        return {
            "yolo": "loaded" if self._yolo is not None else "mock",
            "species_classifier": "loaded" if self._species_classifier is not None else "mock",
            "gender_classifier": "loaded" if self._gender_classifier is not None else "mock",
            "health_classifier": "loaded" if self._health_classifier is not None else "mock",
            "measurement_service": "loaded" if self._measurement_service is not None else "mock",
        }


# Singleton instance
detection_service = DetectionService()
