"""
API Routes — Species Database
GET /species — List species reference data
POST /species — Add new species data
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List
import logging

from core.database import get_db
from models.db_models import SpeciesDatabase
from models.schemas import SpeciesDatabaseCreate, SpeciesDatabaseResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/species", response_model=List[SpeciesDatabaseResponse],
            summary="List database spesies kepiting")
async def list_species(db: AsyncSession = Depends(get_db)):
    """Ambil semua data spesies kepiting dari database referensi."""
    result = await db.execute(
        select(SpeciesDatabase).order_by(SpeciesDatabase.species_name)
    )
    species_list = result.scalars().all()
    return [SpeciesDatabaseResponse.model_validate(s) for s in species_list]


@router.get("/species/{species_id}", response_model=SpeciesDatabaseResponse,
            summary="Detail spesies by ID")
async def get_species(species_id: int, db: AsyncSession = Depends(get_db)):
    """Ambil detail spesies berdasarkan ID."""
    result = await db.execute(
        select(SpeciesDatabase).where(SpeciesDatabase.id == species_id)
    )
    species = result.scalar_one_or_none()
    if not species:
        raise HTTPException(status_code=404, detail=f"Spesies ID {species_id} tidak ditemukan")
    return SpeciesDatabaseResponse.model_validate(species)


@router.post("/species", response_model=SpeciesDatabaseResponse, status_code=201,
             summary="Tambah data spesies baru")
async def create_species(data: SpeciesDatabaseCreate, db: AsyncSession = Depends(get_db)):
    """Tambah data referensi spesies kepiting baru."""
    # Check duplicate
    result = await db.execute(
        select(SpeciesDatabase).where(SpeciesDatabase.species_name == data.species_name)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=f"Spesies '{data.species_name}' sudah ada di database"
        )

    species = SpeciesDatabase(**data.model_dump())
    db.add(species)
    await db.flush()
    await db.refresh(species)
    return SpeciesDatabaseResponse.model_validate(species)
