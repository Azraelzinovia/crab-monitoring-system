"""
API Routes — Detection
POST /detect — Trigger AI detection
GET /detect/status — Detection service status
"""

from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
import uuid

from core.database import get_db
from models.db_models import Crab, DetectionLog
from models.schemas import DetectionRequest, DetectionResponse
from services.detection_service import detection_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/detect", response_model=DetectionResponse, summary="Jalankan deteksi kepiting")
async def detect_crab(
    request: DetectionRequest = DetectionRequest(),
    db: AsyncSession = Depends(get_db),
):
    """
    Jalankan pipeline deteksi kepiting secara lengkap:
    
    1. Ambil frame dari kedua kamera
    2. Deteksi objek dengan YOLOv8
    3. Klasifikasi spesies, jenis kelamin, dan kesehatan
    4. Analisis kelengkapan organ
    5. Estimasi ukuran dan berat
    6. Simpan ke database
    
    Returns hasil analisis lengkap dalam satu response.
    """
    try:
        session_id = request.session_id or str(uuid.uuid4())[:8]

        # Run AI detection pipeline
        result = await detection_service.run_detection(
            session_id=session_id,
            save_images=request.save_images,
        )

        if result is None:
            raise HTTPException(status_code=503, detail="Detection service tidak tersedia")

        # Save to database if crab was detected
        if result.detected:
            crab = Crab(
                species=result.species.species,
                species_confidence=result.species.confidence,
                gender=result.gender.gender,
                gender_confidence=result.gender.confidence,
                health_status=result.health.health_status,
                health_confidence=result.health.confidence,
                weight_g=result.measurements.estimated_weight_g,
                length_cm=result.measurements.length_cm,
                width_cm=result.measurements.width_cm,
                left_claw=result.body_parts.left_claw,
                right_claw=result.body_parts.right_claw,
                legs_complete=result.body_parts.legs_complete,
                shell_damage=result.body_parts.shell_damage,
                detection_confidence=result.detection_confidence,
                image_cam1=result.image_cam1,
                image_cam2=result.image_cam2,
                bbox_x1=result.bbox.get("x1") if result.bbox else None,
                bbox_y1=result.bbox.get("y1") if result.bbox else None,
                bbox_x2=result.bbox.get("x2") if result.bbox else None,
                bbox_y2=result.bbox.get("y2") if result.bbox else None,
                session_id=session_id,
                raw_analysis={
                    "species": result.species.model_dump(),
                    "gender": result.gender.model_dump(),
                    "health": result.health.model_dump(),
                    "body_parts": result.body_parts.model_dump(),
                    "measurements": result.measurements.model_dump(),
                },
            )
            db.add(crab)
            await db.flush()

            # Log detection
            log = DetectionLog(
                crab_id=crab.id,
                camera_id=1,
                session_id=session_id,
                detection_confidence=result.detection_confidence,
                bbox_raw=result.bbox,
                inference_time_ms=result.inference_time_ms,
                total_processing_time_ms=result.total_processing_time_ms,
                status="success",
            )
            db.add(log)
            await db.flush()

            # Update detection_id with actual DB id
            result.detection_id = crab.id

        logger.info(
            f"Detection complete: detected={result.detected}, "
            f"species={result.species.species}, "
            f"time={result.total_processing_time_ms:.1f}ms"
        )
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")


@router.get("/detect/status", summary="Status AI models dan detection service")
async def get_detection_status():
    """Ambil status semua AI model dan kamera."""
    from services.camera_service import camera_service
    
    models_status = detection_service.get_models_status()
    camera_status = camera_service.get_status()
    
    return {
        "models": models_status,
        "cameras": camera_status,
        "service_ready": True,
    }
