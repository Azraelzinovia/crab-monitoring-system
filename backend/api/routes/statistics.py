"""
API Routes — Statistics
GET /statistics — Dashboard aggregation data
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from datetime import datetime, timedelta
import logging

from core.database import get_db
from models.db_models import Crab
from models.schemas import (
    StatisticsResponse, DashboardStats,
    SpeciesDistribution, HealthDistribution, WeightTrend,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/statistics", response_model=StatisticsResponse, summary="Statistik dashboard lengkap")
async def get_statistics(db: AsyncSession = Depends(get_db)):
    """
    Ambil data statistik untuk dashboard monitoring:
    
    - **dashboard**: Total count, gender split, health summary
    - **species_distribution**: Distribusi per jenis kepiting
    - **health_distribution**: Distribusi kondisi kesehatan
    - **weight_trend**: Tren berat rata-rata per hari (30 hari terakhir)
    """
    # ── Dashboard Stats ────────────────────────────────────────────────────────
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())

    stats_result = await db.execute(
        select(
            func.count(Crab.id).label("total"),
            func.sum(case((Crab.gender == "Jantan", 1), else_=0)).label("male"),
            func.sum(case((Crab.gender == "Betina", 1), else_=0)).label("female"),
            func.sum(case((Crab.health_status == "Sehat", 1), else_=0)).label("healthy"),
            func.sum(case(
                (Crab.health_status.in_(["Sakit", "Mati"]), 1), else_=0
            )).label("sick"),
            func.sum(case((Crab.timestamp >= today_start, 1), else_=0)).label("today"),
            func.avg(Crab.weight_g).label("avg_weight"),
        )
    )
    row = stats_result.one()

    # Detection rate per hour (last 24 hours)
    yesterday = datetime.now() - timedelta(hours=24)
    recent_result = await db.execute(
        select(func.count(Crab.id)).where(Crab.timestamp >= yesterday)
    )
    recent_count = recent_result.scalar() or 0
    detection_rate = recent_count / 24.0

    dashboard = DashboardStats(
        total_crabs=row.total or 0,
        male_count=row.male or 0,
        female_count=row.female or 0,
        healthy_count=row.healthy or 0,
        sick_count=row.sick or 0,
        today_count=row.today or 0,
        avg_weight_g=round(row.avg_weight, 1) if row.avg_weight else None,
        detection_rate_per_hour=round(detection_rate, 2),
    )

    # ── Species Distribution ───────────────────────────────────────────────────
    species_result = await db.execute(
        select(Crab.species, func.count(Crab.id).label("count"))
        .group_by(Crab.species)
        .order_by(func.count(Crab.id).desc())
    )
    species_rows = species_result.all()
    total = dashboard.total_crabs or 1  # Avoid division by zero

    species_distribution = [
        SpeciesDistribution(
            species=str(r.species.value if hasattr(r.species, "value") else r.species),
            count=r.count,
            percentage=round((r.count / total) * 100, 1),
        )
        for r in species_rows
    ]

    # ── Health Distribution ────────────────────────────────────────────────────
    health_result = await db.execute(
        select(Crab.health_status, func.count(Crab.id).label("count"))
        .group_by(Crab.health_status)
        .order_by(func.count(Crab.id).desc())
    )
    health_rows = health_result.all()

    health_distribution = [
        HealthDistribution(
            health_status=str(r.health_status.value if hasattr(r.health_status, "value") else r.health_status),
            count=r.count,
            percentage=round((r.count / total) * 100, 1),
        )
        for r in health_rows
    ]

    # ── Weight Trend (last 30 days) ────────────────────────────────────────────
    thirty_days_ago = datetime.now() - timedelta(days=30)
    trend_result = await db.execute(
        select(
            func.date(Crab.timestamp).label("date"),
            func.avg(Crab.weight_g).label("avg_weight"),
            func.count(Crab.id).label("count"),
        )
        .where(Crab.timestamp >= thirty_days_ago)
        .where(Crab.weight_g.isnot(None))
        .group_by(func.date(Crab.timestamp))
        .order_by(func.date(Crab.timestamp))
    )
    trend_rows = trend_result.all()

    weight_trend = [
        WeightTrend(
            date=str(r.date),
            avg_weight_g=round(r.avg_weight, 1),
            count=r.count,
        )
        for r in trend_rows
    ]

    return StatisticsResponse(
        dashboard=dashboard,
        species_distribution=species_distribution,
        health_distribution=health_distribution,
        weight_trend=weight_trend,
    )
