"""
Crab Monitoring System - FastAPI Backend
Main Application Entry Point
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import logging
import os

from core.config import settings
from core.database import create_tables
from api.routes import crabs, detection, statistics, health, stream, species

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(settings.LOG_FILE, encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - startup and shutdown."""
    logger.info("🦀 Starting Crab Monitoring System...")
    
    # Create database tables
    await create_tables()
    logger.info("✅ Database tables initialized")
    
    # Create storage directories
    os.makedirs(settings.IMAGE_STORAGE_PATH, exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    logger.info("✅ Storage directories created")
    
    # Initialize camera service (lazy - will start on first request)
    logger.info("✅ System ready - Dashboard available at http://localhost:3000")
    
    yield
    
    # Shutdown
    logger.info("🔴 Shutting down Crab Monitoring System...")
    from services.camera_service import camera_service
    await camera_service.stop_all()
    logger.info("✅ Cameras stopped")


# Create FastAPI application
app = FastAPI(
    title="Crab Monitoring System API",
    description="""
## 🦀 Sistem Monitoring Kepiting Otomatis

API untuk sistem deteksi dan monitoring kepiting berbasis AI menggunakan:
- **YOLOv8** untuk deteksi objek
- **CNN Classifier** untuk klasifikasi spesies, jenis kelamin, dan kesehatan
- **Computer Vision** untuk estimasi ukuran dan berat

### Fitur Utama:
- Real-time detection dari dual kamera
- Klasifikasi 4 jenis kepiting
- Analisis kondisi fisik otomatis
- Estimasi berat via Computer Vision
- Live streaming via WebSocket
    """,
    version="1.0.0",
    contact={
        "name": "Crab Monitoring Team",
        "email": "support@crabmonitor.io",
    },
    license_info={
        "name": "MIT",
    },
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gzip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Static files for stored images
os.makedirs(settings.IMAGE_STORAGE_PATH, exist_ok=True)
app.mount("/storage", StaticFiles(directory="storage"), name="storage")

# Include API routers
app.include_router(crabs.router, prefix="/api/v1", tags=["Crabs"])
app.include_router(detection.router, prefix="/api/v1", tags=["Detection"])
app.include_router(statistics.router, prefix="/api/v1", tags=["Statistics"])
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(stream.router, prefix="/api/v1", tags=["Streaming"])
app.include_router(species.router, prefix="/api/v1", tags=["Species Database"])


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint — system info."""
    return {
        "system": "Crab Monitoring System",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "api_base": "/api/v1",
    }


@app.get("/health", tags=["Root"])
async def health_check():
    """Health check endpoint untuk monitoring sistem."""
    return {
        "status": "healthy",
        "database": "connected",
        "cameras": "active",
        "ai_models": "loaded",
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_DEBUG,
        workers=1,  # Single worker untuk Raspberry Pi
        log_level=settings.LOG_LEVEL.lower(),
    )
