"""
Body Part Detector — Deteksi kelengkapan organ kepiting
Capit kiri/kanan, kaki, dan kondisi cangkang
"""

try:
    import cv2  # type: ignore[import]
    CV2_AVAILABLE = True
except ImportError:
    cv2 = None  # type: ignore[assignment]
    CV2_AVAILABLE = False
import numpy as np
import logging
from typing import Dict

logger = logging.getLogger(__name__)


class BodyPartDetector:
    """
    Analisis kelengkapan organ tubuh kepiting via Computer Vision.

    Metode:
    - Segmentasi simetri bilateral (capit kiri vs kanan)
    - Analisis area relatif untuk deteksi kaki yang hilang
    - Deteksi kerusakan cangkang via edge analysis
    """

    def __init__(self):
        # Threshold untuk menentukan kelengkapan organ (0-1)
        self.claw_symmetry_threshold = 0.35
        self.leg_area_threshold = 0.30
        self.shell_damage_threshold = 0.15

    def analyze(self, image: np.ndarray) -> Dict:
        """
        Analisis kelengkapan organ dari gambar tampak atas.

        Returns:
            {
                "left_claw": bool,
                "right_claw": bool,
                "legs_complete": bool,
                "shell_damage": bool
            }
        """
        if image is None or image.size == 0:
            return self._default_result()

        try:
            h, w = image.shape[:2]
            mid_x = w // 2

            # Split kiri dan kanan
            left_half  = image[:, :mid_x]
            right_half = image[:, mid_x:]

            # Deteksi capit via area signifikan di ujung gambar
            left_claw  = self._detect_claw(left_half, side="left")
            right_claw = self._detect_claw(right_half, side="right")

            # Deteksi kaki via area lateral
            legs_complete = self._detect_legs(image)

            # Deteksi kerusakan cangkang via edge irregularity
            shell_damage = self._detect_shell_damage(image)

            return {
                "left_claw": left_claw,
                "right_claw": right_claw,
                "legs_complete": legs_complete,
                "shell_damage": shell_damage,
            }

        except Exception as e:
            logger.error(f"Body part detection error: {e}")
            return self._default_result()

    def _detect_claw(self, half_image: np.ndarray, side: str) -> bool:
        """Deteksi keberadaan capit di setengah gambar."""
        try:
            gray = cv2.cvtColor(half_image, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if not contours:
                return False

            total_area = half_image.shape[0] * half_image.shape[1]
            object_area = sum(cv2.contourArea(c) for c in contours)
            ratio = object_area / total_area

            return ratio > self.claw_symmetry_threshold

        except Exception:
            return True  # Default: assume present

    def _detect_legs(self, image: np.ndarray) -> bool:
        """Deteksi kelengkapan kaki via analisis lateral area."""
        try:
            h, w = image.shape[:2]
            # Area kaki di bagian lateral (25% atas dan bawah)
            top_band    = image[:h//4, :]
            bottom_band = image[3*h//4:, :]

            def band_activity(band):
                gray = cv2.cvtColor(band, cv2.COLOR_BGR2GRAY)
                _, thresh = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY)
                return np.count_nonzero(thresh) / thresh.size

            top_ratio    = band_activity(top_band)
            bottom_ratio = band_activity(bottom_band)

            # Jika kedua sisi aktif — kaki lengkap
            return top_ratio > self.leg_area_threshold and bottom_ratio > self.leg_area_threshold

        except Exception:
            return True

    def _detect_shell_damage(self, image: np.ndarray) -> bool:
        """Deteksi kerusakan cangkang via edge irregularity."""
        try:
            gray   = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            edges  = cv2.Canny(blurred, 50, 150)

            # Hitung edge density
            edge_density = np.count_nonzero(edges) / edges.size

            # Edge terlalu tinggi = cangkang tidak mulus / rusak
            return edge_density > self.shell_damage_threshold

        except Exception:
            return False

    def _default_result(self) -> Dict:
        return {
            "left_claw": True,
            "right_claw": True,
            "legs_complete": True,
            "shell_damage": False,
        }
