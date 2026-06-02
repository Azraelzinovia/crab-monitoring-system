"""
API Routes — System Health Check & Status
GET /health — System health status
"""

import time
import os
import psutil
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

from core.database import get_db
from core.config import settings
from models.schemas import SystemHealthResponse

logger = logging.getLogger(__name__)
router = APIRouter()

_start_time = time.time()


@router.get("/health", response_model=SystemHealthResponse, summary="Status kesehatan sistem")
async def system_health(db: AsyncSession = Depends(get_db)):
    """
    Cek status kesehatan seluruh komponen sistem:
    - Database connectivity
    - Camera status
    - AI model status
    - Storage availability
    - System uptime
    """
    # Database check
    db_status = "disconnected"
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")

    # Camera status
    from services.camera_service import camera_service
    camera_status = camera_service.get_status()

    # AI model status
    from services.detection_service import detection_service
    models_status = detection_service.get_models_status()

    # Storage check
    storage_path = settings.IMAGE_STORAGE_PATH
    storage_info = {"path": storage_path, "accessible": False, "free_gb": 0}
    try:
        os.makedirs(storage_path, exist_ok=True)
        disk = psutil.disk_usage(storage_path if os.path.exists(storage_path) else ".")
        storage_info = {
            "path": storage_path,
            "accessible": True,
            "free_gb": round(disk.free / (1024**3), 2),
            "used_percent": disk.percent,
        }
    except Exception as e:
        storage_info["error"] = str(e)

    uptime = time.time() - _start_time

    return SystemHealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        database=db_status,
        cameras={str(k): v for k, v in camera_status.items()},
        ai_models=models_status,
        storage=storage_info,
        uptime_seconds=round(uptime, 1),
    )


@router.get("/health/system", summary="Resource usage sistem (CPU, RAM, Disk)")
async def system_resources():
    """Cek penggunaan resource hardware Raspberry Pi."""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage(".")
        temperature = None

        # Read CPU temperature (Raspberry Pi specific)
        temp_files = [
            "/sys/class/thermal/thermal_zone0/temp",
            "/sys/devices/virtual/thermal/thermal_zone0/temp",
        ]
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                with open(temp_file) as f:
                    temperature = round(int(f.read().strip()) / 1000.0, 1)
                break

        return {
            "cpu": {
                "percent": cpu_percent,
                "cores": psutil.cpu_count(),
                "temperature_c": temperature,
            },
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "percent": memory.percent,
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "percent": disk.percent,
            },
            "uptime_seconds": round(time.time() - _start_time, 1),
        }
    except Exception as e:
        return {"error": str(e)}
