"""
API Routes — Crabs CRUD
GET /crabs, GET /crabs/{id}, POST /crabs, DELETE /crabs/{id}
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Optional
import logging

from core.database import get_db
from models.db_models import Crab, HealthRecord
from models.schemas import (
    CrabCreate, CrabResponse, CrabListResponse,
    HealthRecordCreate, HealthRecordResponse,
    SpeciesEnum, GenderEnum, HealthStatusEnum,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/crabs", response_model=CrabListResponse, summary="List semua kepiting")
async def list_crabs(
    page: int = Query(1, ge=1, description="Halaman"),
    size: int = Query(20, ge=1, le=100, description="Jumlah per halaman"),
    species: Optional[SpeciesEnum] = Query(None, description="Filter spesies"),
    gender: Optional[GenderEnum] = Query(None, description="Filter jenis kelamin"),
    health_status: Optional[HealthStatusEnum] = Query(None, description="Filter status kesehatan"),
    session_id: Optional[str] = Query(None, description="Filter session ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    Ambil daftar kepiting yang telah terdeteksi dengan filter dan pagination.
    
    - **page**: Nomor halaman (mulai dari 1)
    - **size**: Jumlah data per halaman (max 100)
    - **species**: Filter berdasarkan jenis kepiting
    - **gender**: Filter berdasarkan jenis kelamin
    - **health_status**: Filter berdasarkan kondisi kesehatan
    """
    query = select(Crab)

    if species:
        query = query.where(Crab.species == species)
    if gender:
        query = query.where(Crab.gender == gender)
    if health_status:
        query = query.where(Crab.health_status == health_status)
    if session_id:
        query = query.where(Crab.session_id == session_id)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination and ordering
    query = query.order_by(desc(Crab.timestamp)).offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    crabs = result.scalars().all()

    return CrabListResponse(
        total=total,
        page=page,
        size=size,
        crabs=[CrabResponse.model_validate(c) for c in crabs],
    )


@router.get("/crabs/{crab_id}", response_model=CrabResponse, summary="Detail kepiting by ID")
async def get_crab(crab_id: int, db: AsyncSession = Depends(get_db)):
    """Ambil detail kepiting berdasarkan ID."""
    result = await db.execute(select(Crab).where(Crab.id == crab_id))
    crab = result.scalar_one_or_none()

    if not crab:
        raise HTTPException(status_code=404, detail=f"Kepiting ID {crab_id} tidak ditemukan")

    return CrabResponse.model_validate(crab)


@router.post("/crabs", response_model=CrabResponse, status_code=201,
             summary="Tambah data kepiting manual")
async def create_crab(data: CrabCreate, db: AsyncSession = Depends(get_db)):
    """Tambah data kepiting secara manual (tanpa AI detection)."""
    crab = Crab(**data.model_dump())
    db.add(crab)
    await db.flush()
    await db.refresh(crab)
    return CrabResponse.model_validate(crab)


@router.delete("/crabs/{crab_id}", status_code=204, summary="Hapus data kepiting")
async def delete_crab(crab_id: int, db: AsyncSession = Depends(get_db)):
    """Hapus data kepiting berdasarkan ID."""
    result = await db.execute(select(Crab).where(Crab.id == crab_id))
    crab = result.scalar_one_or_none()

    if not crab:
        raise HTTPException(status_code=404, detail=f"Kepiting ID {crab_id} tidak ditemukan")

    await db.delete(crab)
    return None


# ── Health Records ────────────────────────────────────────────────────────────

@router.get("/crabs/{crab_id}/health-records", response_model=list[HealthRecordResponse],
            summary="Riwayat kesehatan kepiting")
async def get_health_records(crab_id: int, db: AsyncSession = Depends(get_db)):
    """Ambil riwayat kesehatan kepiting berdasarkan ID."""
    # Verify crab exists
    result = await db.execute(select(Crab).where(Crab.id == crab_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Kepiting ID {crab_id} tidak ditemukan")

    result = await db.execute(
        select(HealthRecord)
        .where(HealthRecord.crab_id == crab_id)
        .order_by(desc(HealthRecord.timestamp))
    )
    records = result.scalars().all()
    return [HealthRecordResponse.model_validate(r) for r in records]


@router.post("/crabs/{crab_id}/health-records", response_model=HealthRecordResponse,
             status_code=201, summary="Tambah catatan kesehatan")
async def create_health_record(
    crab_id: int,
    data: HealthRecordCreate,
    db: AsyncSession = Depends(get_db),
):
    """Tambah catatan kesehatan untuk kepiting."""
    result = await db.execute(select(Crab).where(Crab.id == crab_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Kepiting ID {crab_id} tidak ditemukan")

    record = HealthRecord(**data.model_dump())
    db.add(record)
    await db.flush()
    await db.refresh(record)
    return HealthRecordResponse.model_validate(record)
