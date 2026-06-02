"""
Pydantic Schemas — Request/Response models for API
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ── Enums ─────────────────────────────────────────────────────────────────────

class SpeciesEnum(str, Enum):
    BAKAU = "Kepiting Bakau"
    RAJUNGAN = "Kepiting Rajungan"
    LUMPUR = "Kepiting Lumpur"
    BATU = "Kepiting Batu"
    UNKNOWN = "Unknown"


class GenderEnum(str, Enum):
    JANTAN = "Jantan"
    BETINA = "Betina"
    UNKNOWN = "Unknown"


class HealthStatusEnum(str, Enum):
    SEHAT = "Sehat"
    KURANG_SEHAT = "Kurang Sehat"
    SAKIT = "Sakit"
    MATI = "Mati"
    UNKNOWN = "Unknown"


# ── Species Classification ─────────────────────────────────────────────────────

class SpeciesResult(BaseModel):
    species: SpeciesEnum
    confidence: float = Field(..., ge=0, le=100, description="Confidence score 0-100%")


class GenderResult(BaseModel):
    gender: GenderEnum
    confidence: float = Field(..., ge=0, le=100)


class HealthResult(BaseModel):
    health_status: HealthStatusEnum
    confidence: float = Field(..., ge=0, le=100)


class BodyPartsResult(BaseModel):
    left_claw: bool
    right_claw: bool
    legs_complete: bool
    shell_damage: bool


class MeasurementResult(BaseModel):
    length_cm: Optional[float] = Field(None, ge=0, description="Panjang tubuh dalam cm")
    width_cm: Optional[float] = Field(None, ge=0, description="Lebar tubuh dalam cm")
    estimated_weight_g: Optional[float] = Field(None, ge=0, description="Estimasi berat dalam gram")


# ── Detection Request/Response ─────────────────────────────────────────────────

class DetectionRequest(BaseModel):
    session_id: Optional[str] = None
    save_images: bool = True
    run_all_analysis: bool = True


class DetectionResponse(BaseModel):
    detection_id: int
    session_id: str
    timestamp: datetime
    
    # Detection
    detected: bool
    detection_confidence: float
    
    # Bounding box
    bbox: Optional[dict] = None
    
    # Classifications
    species: SpeciesResult
    gender: GenderResult
    health: HealthResult
    body_parts: BodyPartsResult
    measurements: MeasurementResult
    
    # Images
    image_cam1: Optional[str] = None
    image_cam2: Optional[str] = None
    
    # Performance
    inference_time_ms: float
    total_processing_time_ms: float


# ── Crab Schemas ──────────────────────────────────────────────────────────────

class CrabBase(BaseModel):
    species: Optional[SpeciesEnum] = SpeciesEnum.UNKNOWN
    gender: Optional[GenderEnum] = GenderEnum.UNKNOWN
    health_status: Optional[HealthStatusEnum] = HealthStatusEnum.UNKNOWN
    weight_g: Optional[float] = None
    length_cm: Optional[float] = None
    width_cm: Optional[float] = None
    notes: Optional[str] = None


class CrabCreate(CrabBase):
    species_confidence: float = 0.0
    gender_confidence: float = 0.0
    health_confidence: float = 0.0
    detection_confidence: float = 0.0
    left_claw: bool = True
    right_claw: bool = True
    legs_complete: bool = True
    shell_damage: bool = False
    image_cam1: Optional[str] = None
    image_cam2: Optional[str] = None
    bbox_x1: Optional[float] = None
    bbox_y1: Optional[float] = None
    bbox_x2: Optional[float] = None
    bbox_y2: Optional[float] = None
    track_id: Optional[int] = None
    session_id: Optional[str] = None
    raw_analysis: Optional[dict] = None


class CrabResponse(CrabBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    timestamp: datetime
    species_confidence: float
    gender_confidence: float
    health_confidence: float
    detection_confidence: float
    left_claw: bool
    right_claw: bool
    legs_complete: bool
    shell_damage: bool
    image_cam1: Optional[str] = None
    image_cam2: Optional[str] = None
    track_id: Optional[int] = None
    session_id: Optional[str] = None


class CrabListResponse(BaseModel):
    total: int
    page: int
    size: int
    crabs: List[CrabResponse]


# ── Statistics Schemas ────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_crabs: int
    male_count: int
    female_count: int
    healthy_count: int
    sick_count: int
    today_count: int
    avg_weight_g: Optional[float] = None
    detection_rate_per_hour: float = 0.0


class SpeciesDistribution(BaseModel):
    species: str
    count: int
    percentage: float


class HealthDistribution(BaseModel):
    health_status: str
    count: int
    percentage: float


class WeightTrend(BaseModel):
    date: str
    avg_weight_g: float
    count: int


class StatisticsResponse(BaseModel):
    dashboard: DashboardStats
    species_distribution: List[SpeciesDistribution]
    health_distribution: List[HealthDistribution]
    weight_trend: List[WeightTrend]


# ── Health Record Schemas ─────────────────────────────────────────────────────

class HealthRecordCreate(BaseModel):
    crab_id: int
    health_status: HealthStatusEnum
    health_confidence: float = 0.0
    shell_color: Optional[str] = None
    shell_condition: Optional[str] = None
    body_condition: Optional[str] = None
    weight_g: Optional[float] = None
    length_cm: Optional[float] = None
    width_cm: Optional[float] = None
    diagnosis: Optional[str] = None
    treatment_notes: Optional[str] = None


class HealthRecordResponse(HealthRecordCreate):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    timestamp: datetime
    image_path: Optional[str] = None


# ── Species Database Schemas ──────────────────────────────────────────────────

class SpeciesDatabaseCreate(BaseModel):
    species_name: str
    scientific_name: Optional[str] = None
    family: Optional[str] = None
    habitat: Optional[str] = None
    characteristics: Optional[str] = None
    morphology: Optional[str] = None
    growth_pattern: Optional[str] = None
    common_diseases: Optional[str] = None
    average_weight_min_g: Optional[float] = None
    average_weight_max_g: Optional[float] = None
    average_length_min_cm: Optional[float] = None
    average_length_max_cm: Optional[float] = None
    distribution: Optional[str] = None
    source_url: Optional[str] = None


class SpeciesDatabaseResponse(SpeciesDatabaseCreate):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


# ── System Health Schemas ─────────────────────────────────────────────────────

class SystemHealthResponse(BaseModel):
    status: str
    database: str
    cameras: dict
    ai_models: dict
    storage: dict
    uptime_seconds: float
