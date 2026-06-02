"""
Script Inisialisasi Database
Membuat tabel, menerapkan schema, dan mengisi seed data
Jalankan: python scripts/init_db.py
"""

import asyncio
import sys
import os

# Tambahkan backend ke path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

async def main():
    print("🗄️  Inisialisasi Database Crab Monitoring System")
    print("=" * 50)

    try:
        from core.database import create_tables, engine
        from core.config import settings

        print(f"📡 Connecting to: {settings.DATABASE_URL[:50]}...")
        await create_tables()
        print("✅ Semua tabel berhasil dibuat")

        # Seed species data
        from sqlalchemy.ext.asyncio import AsyncSession
        from core.database import AsyncSessionLocal
        from models.db_models import SpeciesDatabase

        seed_data = [
            {
                "species_name": "Kepiting Bakau",
                "scientific_name": "Scylla serrata",
                "family": "Portunidae",
                "habitat": "Hutan mangrove, estuari, dan perairan payau di sepanjang pesisir tropis.",
                "characteristics": "Cangkang keras berwarna hijau kecoklatan hingga coklat tua. Capit besar dan kuat.",
                "average_weight_min_g": 100.0, "average_weight_max_g": 1200.0,
                "average_length_min_cm": 8.0, "average_length_max_cm": 20.0,
                "distribution": "Indo-Pasifik Barat: Asia Tenggara, India, Afrika Timur, Australia",
            },
            {
                "species_name": "Kepiting Rajungan",
                "scientific_name": "Portunus pelagicus",
                "family": "Portunidae",
                "habitat": "Perairan laut dangkal berpasir, padang lamun, dan terumbu karang.",
                "characteristics": "Cangkang biru kehijauan dengan bintik putih. Kaki belakang berbentuk dayung.",
                "average_weight_min_g": 50.0, "average_weight_max_g": 400.0,
                "average_length_min_cm": 6.0, "average_length_max_cm": 18.0,
                "distribution": "Indo-Pasifik: Jepang, Australia, India, Afrika Timur",
            },
            {
                "species_name": "Kepiting Lumpur",
                "scientific_name": "Scylla olivacea",
                "family": "Portunidae",
                "habitat": "Lumpur estuari, tambak, dan kawasan mangrove bersubstrat lunak.",
                "characteristics": "Cangkang coklat kemerahan hingga zaitun. Toleran salinitas rendah.",
                "average_weight_min_g": 80.0, "average_weight_max_g": 600.0,
                "average_length_min_cm": 6.0, "average_length_max_cm": 15.0,
                "distribution": "Asia Tenggara: Indonesia, Malaysia, Filipina, Thailand",
            },
            {
                "species_name": "Kepiting Batu",
                "scientific_name": "Charybdis feriata",
                "family": "Portunidae",
                "habitat": "Dasar berbatu dan berkarang di perairan laut dangkal hingga sedang.",
                "characteristics": "Cangkang keras dengan pola garis khas. Warna coklat atau merah bata.",
                "average_weight_min_g": 100.0, "average_weight_max_g": 800.0,
                "average_length_min_cm": 7.0, "average_length_max_cm": 17.0,
                "distribution": "Indo-Pasifik: Asia Tenggara, India, Laut Merah, Jepang",
            },
        ]

        async with AsyncSessionLocal() as session:
            for data in seed_data:
                # Upsert — skip jika sudah ada
                from sqlalchemy import select
                result = await session.execute(
                    select(SpeciesDatabase).where(SpeciesDatabase.species_name == data["species_name"])
                )
                if not result.scalar_one_or_none():
                    session.add(SpeciesDatabase(**data))
                    print(f"  ✅ Seed: {data['species_name']}")
                else:
                    print(f"  ⏭️  Skip (sudah ada): {data['species_name']}")
            await session.commit()

        print("\n🎉 Database siap digunakan!")

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Pastikan sudah install: pip install -r backend/requirements.txt")
    except Exception as e:
        print(f"❌ Error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
