"""
Size Estimator — Estimasi ukuran dan berat kepiting
Menggunakan kalibrasi kamera dan Computer Vision measurement.
"""

import cv2
import numpy as np
import logging
from typing import Optional, Dict, Tuple
import json
import os

logger = logging.getLogger(__name__)

# Default calibration constants (adjust via calibration process)
# pixels per centimeter untuk resolusi 1280x720
DEFAULT_PIXELS_PER_CM = 42.5

# Weight estimation formula (empirical for common crab species)
# Weight (g) = a * Length^b * Width^c (allometric equation)
WEIGHT_COEFFICIENTS = {
    "Kepiting Bakau": {"a": 0.0012, "b": 2.8, "c": 1.2},
    "Kepiting Rajungan": {"a": 0.0008, "b": 2.6, "c": 1.4},
    "Kepiting Lumpur": {"a": 0.0010, "b": 2.7, "c": 1.3},
    "Kepiting Batu": {"a": 0.0015, "b": 2.9, "c": 1.1},
    "default": {"a": 0.0011, "b": 2.75, "c": 1.25},
}


class CameraCalibration:
    """Kalibrasi kamera menggunakan checkerboard pattern."""

    def __init__(self, calibration_file: str = "ai_models/calibration/camera_params.json"):
        self.calibration_file = calibration_file
        self.pixels_per_cm = DEFAULT_PIXELS_PER_CM
        self.camera_matrix = None
        self.dist_coeffs = None
        self._load_calibration()

    def _load_calibration(self):
        """Load kalibrasi tersimpan."""
        if os.path.exists(self.calibration_file):
            try:
                with open(self.calibration_file) as f:
                    data = json.load(f)
                self.pixels_per_cm = data.get("pixels_per_cm", DEFAULT_PIXELS_PER_CM)
                if "camera_matrix" in data:
                    self.camera_matrix = np.array(data["camera_matrix"])
                if "dist_coeffs" in data:
                    self.dist_coeffs = np.array(data["dist_coeffs"])
                logger.info(f"✅ Camera calibration loaded: {self.pixels_per_cm} px/cm")
            except Exception as e:
                logger.warning(f"Failed to load calibration: {e}")

    def calibrate_from_checkerboard(
        self, images: list, board_size: Tuple = (9, 6), square_size_cm: float = 2.5
    ) -> Dict:
        """
        Kalibrasi kamera dari gambar checkerboard.
        
        Args:
            images: List of calibration images
            board_size: (cols, rows) inner corners
            square_size_cm: Physical size of each square in cm
            
        Returns:
            Calibration parameters
        """
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

        # Prepare object points
        objp = np.zeros((board_size[0] * board_size[1], 3), np.float32)
        objp[:, :2] = np.mgrid[0:board_size[0], 0:board_size[1]].T.reshape(-1, 2)
        objp *= square_size_cm

        objpoints = []
        imgpoints = []

        for img in images:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            ret, corners = cv2.findChessboardCorners(gray, board_size, None)

            if ret:
                corners_refined = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
                objpoints.append(objp)
                imgpoints.append(corners_refined)

        if len(objpoints) < 5:
            logger.warning("Not enough calibration images")
            return {}

        h, w = images[0].shape[:2]
        ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(
            objpoints, imgpoints, (w, h), None, None
        )

        # Calculate pixels per cm from calibration
        # Use known square size and detected corner spacing
        if len(imgpoints) > 0:
            corner_spacing = np.linalg.norm(
                imgpoints[0][0] - imgpoints[0][1]
            )
            self.pixels_per_cm = corner_spacing / square_size_cm

        self.camera_matrix = mtx
        self.dist_coeffs = dist

        # Save calibration
        self._save_calibration()

        return {
            "pixels_per_cm": round(self.pixels_per_cm, 2),
            "rms_error": round(ret, 4),
        }

    def _save_calibration(self):
        """Save calibration parameters to file."""
        os.makedirs(os.path.dirname(self.calibration_file), exist_ok=True)
        data = {
            "pixels_per_cm": self.pixels_per_cm,
        }
        if self.camera_matrix is not None:
            data["camera_matrix"] = self.camera_matrix.tolist()
        if self.dist_coeffs is not None:
            data["dist_coeffs"] = self.dist_coeffs.tolist()

        with open(self.calibration_file, "w") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Calibration saved to {self.calibration_file}")

    def pixels_to_cm(self, pixels: float) -> float:
        return pixels / self.pixels_per_cm


class SizeEstimator:
    """
    Estimasi ukuran fisik kepiting dari bounding box dan frame.
    """

    def __init__(self):
        self.calibration = CameraCalibration()

    def estimate(self, frame: np.ndarray, bbox: Dict, species: str = "default") -> Dict:
        """
        Estimasi panjang, lebar, dan berat kepiting.
        
        Args:
            frame: Frame kamera tampak atas
            bbox: Bounding box {"x1", "y1", "x2", "y2"}
            species: Nama spesies untuk rumus berat yang tepat
            
        Returns:
            {"length_cm", "width_cm", "estimated_weight_g"}
        """
        try:
            x1, y1, x2, y2 = (
                int(bbox["x1"]), int(bbox["y1"]),
                int(bbox["x2"]), int(bbox["y2"])
            )

            # Pixel dimensions
            pixel_width = x2 - x1
            pixel_height = y2 - y1

            # Get precise dimensions from contour analysis
            roi = frame[y1:y2, x1:x2]
            precise_dims = self._get_precise_dimensions(roi)

            if precise_dims:
                length_px, width_px = precise_dims
            else:
                # Fallback to bbox dimensions
                length_px = max(pixel_height, pixel_width)
                width_px = min(pixel_height, pixel_width)

            # Convert to cm
            length_cm = round(self.calibration.pixels_to_cm(length_px), 1)
            width_cm = round(self.calibration.pixels_to_cm(width_px), 1)

            # Estimate weight using allometric equation
            weight_g = self._estimate_weight(length_cm, width_cm, species)

            return {
                "length_cm": length_cm,
                "width_cm": width_cm,
                "estimated_weight_g": weight_g,
            }

        except Exception as e:
            logger.error(f"Size estimation error: {e}")
            return {"length_cm": None, "width_cm": None, "estimated_weight_g": None}

    def _get_precise_dimensions(self, roi: np.ndarray) -> Optional[Tuple[float, float]]:
        """
        Dapatkan dimensi presisi dari kontur kepiting dalam ROI.
        """
        if roi is None or roi.size == 0:
            return None

        try:
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)

            # Adaptive thresholding untuk separasi cangkang
            thresh = cv2.adaptiveThreshold(
                blurred, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV, 11, 2
            )

            # Morphological operations untuk membersihkan noise
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)

            contours, _ = cv2.findContours(
                cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            if not contours:
                return None

            # Ambil kontur terbesar (body kepiting)
            largest = max(contours, key=cv2.contourArea)

            if cv2.contourArea(largest) < 1000:  # Too small
                return None

            # Fitted ellipse untuk mendapatkan dimensi akurat
            if len(largest) >= 5:
                ellipse = cv2.fitEllipse(largest)
                axes = ellipse[1]  # (minor_axis, major_axis)
                return (max(axes), min(axes))

            # Fallback: bounding rect
            _, _, w, h = cv2.boundingRect(largest)
            return (max(w, h), min(w, h))

        except Exception as e:
            logger.debug(f"Contour measurement failed: {e}")
            return None

    def _estimate_weight(self, length_cm: float, width_cm: float, species: str) -> float:
        """
        Estimasi berat menggunakan persamaan alometrik.
        W = a * L^b * W^c
        """
        coeff = WEIGHT_COEFFICIENTS.get(species, WEIGHT_COEFFICIENTS["default"])
        weight = coeff["a"] * (length_cm ** coeff["b"]) * (width_cm ** coeff["c"])
        return round(weight, 1)
