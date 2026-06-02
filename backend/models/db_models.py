"""
Database Models — SQLAlchemy ORM
Tabel: crabs, health_records, species_database, detection_logs
"""

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text,
    ForeignKey, Enum as SAEnum, JSON, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from core.database import Base


# ── Enums ─────────────────────────────────────────────────────────────────────

class SpeciesEnum(str, enum.Enum):
    BAKAU = "Kepiting Bakau"
    RAJUNGAN = "Kepiting Rajungan"
    LUMPUR = "Kepiting Lumpur"
    BATU = "Kepiting Batu"
    UNKNOWN = "Unknown"


class GenderEnum(str, enum.Enum):
    JANTAN = "Jantan"
    BETINA = "Betina"
    UNKNOWN = "Unknown"


class HealthStatusEnum(str, enum.Enum):
    SEHAT = "Sehat"
    KURANG_SEHAT = "Kurang Sehat"
    SAKIT = "Sakit"
    MATI = "Mati"
    UNKNOWN = "Unknown"


# ── Models ────────────────────────────────────────────────────────────────────

class SpeciesDatabase(Base):
    """Database referensi spesies kepiting dari web scraping."""
    __tablename__ = "species_database"

    id = Column(Integer, primary_key=True, index=True)
    species_name = Column(String(100), unique=True, nullable=False)
    scientific_name = Column(String(150))
    family = Column(String(100))
    habitat = Column(Text)
    characteristics = Column(Text)
    morphology = Column(Text)
    growth_pattern = Column(Text)
    common_diseases = Column(Text)
    average_weight_min_g = Column(Float)
    average_weight_max_g = Column(Float)
    average_length_min_cm = Column(Float)
    average_length_max_cm = Column(Float)
    distribution = Column(Text)
    source_url = Column(String(500))
    reference_images = Column(JSON)  # List of image paths
    additional_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    crabs = relationship("Crab", back_populates="species_info")


class Crab(Base):
    """Data utama kepiting hasil deteksi."""
    __tablename__ = "crabs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Species & Classification
    species = Column(SAEnum(SpeciesEnum), default=SpeciesEnum.UNKNOWN, index=True)
    species_confidence = Column(Float, default=0.0)
    species_database_id = Column(Integer, ForeignKey("species_database.id"), nullable=True)
    
    # Gender
    gender = Column(SAEnum(GenderEnum), default=GenderEnum.UNKNOWN, index=True)
    gender_confidence = Column(Float, default=0.0)
    
    # Health
    health_status = Column(SAEnum(HealthStatusEnum), default=HealthStatusEnum.UNKNOWN, index=True)
    health_confidence = Column(Float, default=0.0)
    
    # Physical Measurements
    weight_g = Column(Float, nullable=True)
    length_cm = Column(Float, nullable=True)
    width_cm = Column(Float, nullable=True)
    
    # Body Parts Completeness
    left_claw = Column(Boolean, default=True)
    right_claw = Column(Boolean, default=True)
    legs_complete = Column(Boolean, default=True)
    shell_damage = Column(Boolean, default=False)
    
    # Detection Scores
    detection_confidence = Column(Float, default=0.0)
    
    # Images
    image_cam1 = Column(String(500), nullable=True)  # Path to camera 1 image
    image_cam2 = Column(String(500), nullable=True)  # Path to camera 2 image
    
    # Bounding Box (dari kamera atas)
    bbox_x1 = Column(Float, nullable=True)
    bbox_y1 = Column(Float, nullable=True)
    bbox_x2 = Column(Float, nullable=True)
    bbox_y2 = Column(Float, nullable=True)
    
    # Tracking
    track_id = Column(Integer, nullable=True, index=True)
    session_id = Column(String(50), nullable=True, index=True)
    
    # Additional data
    raw_analysis = Column(JSON)  # Full AI output JSON
    notes = Column(Text, nullable=True)
    
    # Relationships
    species_info = relationship("SpeciesDatabase", back_populates="crabs")
    health_records = relationship("HealthRecord", back_populates="crab")
    detection_logs = relationship("DetectionLog", back_populates="crab")

    # Indexes
    __table_args__ = (
        Index("ix_crabs_timestamp_species", "timestamp", "species"),
        Index("ix_crabs_timestamp_health", "timestamp", "health_status"),
    )


class HealthRecord(Base):
    """Riwayat kesehatan kepiting dari waktu ke waktu."""
    __tablename__ = "health_records"

    id = Column(Integer, primary_key=True, index=True)
    crab_id = Column(Integer, ForeignKey("crabs.id"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    health_status = Column(SAEnum(HealthStatusEnum), nullable=False)
    health_confidence = Column(Float, default=0.0)
    
    # Physical observations
    shell_color = Column(String(50), nullable=True)
    shell_condition = Column(String(100), nullable=True)
    body_condition = Column(String(100), nullable=True)
    
    # Measurements at this record
    weight_g = Column(Float, nullable=True)
    length_cm = Column(Float, nullable=True)
    width_cm = Column(Float, nullable=True)
    
    # Diagnosis
    diagnosis = Column(Text, nullable=True)
    treatment_notes = Column(Text, nullable=True)
    
    # Images
    image_path = Column(String(500), nullable=True)
    
    # Analysis data
    analysis_data = Column(JSON)
    
    # Relationship
    crab = relationship("Crab", back_populates="health_records")


class DetectionLog(Base):
    """Log setiap sesi deteksi — untuk audit dan debugging."""
    __tablename__ = "detection_logs"

    id = Column(Integer, primary_key=True, index=True)
    crab_id = Column(Integer, ForeignKey("crabs.id"), nullable=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Detection details
    camera_id = Column(Integer, nullable=False)  # 1 or 2
    frame_number = Column(Integer, nullable=True)
    session_id = Column(String(50), nullable=True, index=True)
    
    # YOLO output
    detection_confidence = Column(Float)
    bbox_raw = Column(JSON)  # Raw bounding box coords
    
    # Processing time
    inference_time_ms = Column(Float)
    total_processing_time_ms = Column(Float)
    
    # Status
    status = Column(String(50), default="success")
    error_message = Column(Text, nullable=True)
    
    # Image
    frame_image_path = Column(String(500), nullable=True)
    
    # Relationship
    crab = relationship("Crab", back_populates="detection_logs")

    __table_args__ = (
        Index("ix_detection_logs_session_camera", "session_id", "camera_id"),
    )


class ScrapingLog(Base):
    """Log aktivitas web scraping."""
    __tablename__ = "scraping_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    source = Column(String(200))
    url = Column(String(500))
    status = Column(String(50))
    records_scraped = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    duration_seconds = Column(Float, nullable=True)
