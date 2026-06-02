"""
Web Scraper — Multi-source data collection untuk database kepiting
Sources: FAO, Wikipedia, ResearchGate, GBIF, WoRMS
"""

import asyncio
import aiohttp
import requests
from bs4 import BeautifulSoup
import time
import logging
import json
import os
from typing import Optional, Dict, List
from datetime import datetime
from urllib.parse import urljoin, quote
import re

logger = logging.getLogger(__name__)

# Target species
TARGET_SPECIES = [
    "Scylla serrata",           # Kepiting Bakau
    "Portunus pelagicus",       # Kepiting Rajungan
    "Scylla olivacea",          # Kepiting Lumpur
    "Charybdis feriata",        # Kepiting Batu
]

COMMON_NAMES = {
    "Scylla serrata": "Kepiting Bakau",
    "Portunus pelagicus": "Kepiting Rajungan",
    "Scylla olivacea": "Kepiting Lumpur",
    "Charybdis feriata": "Kepiting Batu",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


class WikipediaScraper:
    """Scraper data spesies kepiting dari Wikipedia."""

    BASE_URL = "https://en.wikipedia.org/w/api.php"

    def scrape(self, scientific_name: str) -> Optional[Dict]:
        """Scrape informasi spesies dari Wikipedia API."""
        try:
            params = {
                "action": "query",
                "format": "json",
                "titles": scientific_name,
                "prop": "extracts",
                "exintro": True,
                "explaintext": True,
                "exsectionformat": "plain",
            }

            resp = requests.get(self.BASE_URL, params=params, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            pages = data.get("query", {}).get("pages", {})
            for page_id, page_data in pages.items():
                if page_id == "-1":
                    continue

                extract = page_data.get("extract", "")
                common_name = COMMON_NAMES.get(scientific_name, "")

                return {
                    "scientific_name": scientific_name,
                    "common_name": common_name,
                    "description": extract[:2000] if extract else "",
                    "source_url": f"https://en.wikipedia.org/wiki/{quote(scientific_name)}",
                    "source": "Wikipedia",
                }

        except Exception as e:
            logger.error(f"Wikipedia scrape error for {scientific_name}: {e}")
        return None


class GBIFScraper:
    """
    Scraper dari GBIF (Global Biodiversity Information Facility).
    Mendapatkan data taksonomi, distribusi, dan habitat.
    """

    BASE_URL = "https://api.gbif.org/v1"

    def scrape(self, scientific_name: str) -> Optional[Dict]:
        """Get species data from GBIF API."""
        try:
            # Search for species
            search_url = f"{self.BASE_URL}/species/match"
            params = {"name": scientific_name, "strict": False}
            resp = requests.get(search_url, params=params, timeout=10)
            resp.raise_for_status()
            match_data = resp.json()

            if match_data.get("matchType") == "NONE":
                return None

            species_key = match_data.get("usageKey") or match_data.get("speciesKey")
            if not species_key:
                return None

            # Get detailed species info
            species_url = f"{self.BASE_URL}/species/{species_key}"
            resp = requests.get(species_url, timeout=10)
            resp.raise_for_status()
            species_data = resp.json()

            # Get vernacular names
            vernacular_url = f"{self.BASE_URL}/species/{species_key}/vernacularNames"
            resp = requests.get(vernacular_url, timeout=10)
            vernacular_data = resp.json() if resp.ok else {}
            
            vernacular_names = [
                v["vernacularName"] for v in vernacular_data.get("results", [])
                if v.get("language") in ["id", "en", None]
            ][:5]

            return {
                "scientific_name": scientific_name,
                "kingdom": species_data.get("kingdom", ""),
                "phylum": species_data.get("phylum", ""),
                "class": species_data.get("class", ""),
                "order": species_data.get("order", ""),
                "family": species_data.get("family", ""),
                "genus": species_data.get("genus", ""),
                "vernacular_names": vernacular_names,
                "gbif_key": species_key,
                "source_url": f"https://www.gbif.org/species/{species_key}",
                "source": "GBIF",
            }

        except Exception as e:
            logger.error(f"GBIF scrape error for {scientific_name}: {e}")
        return None


class FAOScraper:
    """
    Scraper dari FAO FishFinder database.
    Mendapatkan data fisheries dan karakteristik biologis.
    """

    BASE_URL = "https://www.fao.org/fishery/en/species"

    # FAO species codes untuk kepiting target
    FAO_CODES = {
        "Scylla serrata": "MUD",
        "Portunus pelagicus": "CRB",
        "Scylla olivacea": "SIO",
        "Charybdis feriata": "CRF",
    }

    def scrape(self, scientific_name: str) -> Optional[Dict]:
        """Scrape biological data from FAO."""
        try:
            species_code = self.FAO_CODES.get(scientific_name)
            if not species_code:
                return None

            url = f"{self.BASE_URL}/{species_code}"
            resp = requests.get(url, headers=HEADERS, timeout=15)

            if resp.status_code != 200:
                return None

            soup = BeautifulSoup(resp.content, "html.parser")

            # Extract biology information
            data = {
                "scientific_name": scientific_name,
                "common_name": COMMON_NAMES.get(scientific_name, ""),
                "source_url": url,
                "source": "FAO",
            }

            # Try to extract habitat, distribution info
            content_sections = soup.find_all(["div", "p", "section"])
            for section in content_sections:
                text = section.get_text(strip=True)
                if len(text) > 100:
                    if "habitat" in text.lower():
                        data["habitat"] = text[:500]
                    elif "distribut" in text.lower():
                        data["distribution"] = text[:500]
                    elif "biology" in text.lower() or "morpholog" in text.lower():
                        data["morphology"] = text[:500]

            return data

        except Exception as e:
            logger.error(f"FAO scrape error for {scientific_name}: {e}")
        return None


class WoRMSScraper:
    """
    Scraper dari WoRMS (World Register of Marine Species).
    Mendapatkan data taksonomi yang akurat.
    """

    BASE_URL = "https://www.marinespecies.org/rest"

    def scrape(self, scientific_name: str) -> Optional[Dict]:
        """Get taxonomic data from WoRMS REST API."""
        try:
            # Search for AphiaID
            search_url = f"{self.BASE_URL}/AphiaRecordsByName/{quote(scientific_name)}"
            params = {"like": False, "marine_only": True}
            resp = requests.get(search_url, params=params, timeout=10)
            resp.raise_for_status()
            records = resp.json()

            if not records:
                return None

            record = records[0]
            aphia_id = record.get("AphiaID")

            return {
                "scientific_name": scientific_name,
                "aphia_id": aphia_id,
                "status": record.get("status", ""),
                "kingdom": record.get("kingdom", ""),
                "phylum": record.get("phylum", ""),
                "class": record.get("class", ""),
                "order": record.get("order", ""),
                "family": record.get("family", ""),
                "genus": record.get("genus", ""),
                "isMarine": record.get("isMarine", 1),
                "source_url": f"https://www.marinespecies.org/aphia.php?p=taxdetails&id={aphia_id}",
                "source": "WoRMS",
            }

        except Exception as e:
            logger.error(f"WoRMS scrape error for {scientific_name}: {e}")
        return None


class CrabDataScraper:
    """
    Main scraper yang mengumpulkan data dari semua sumber
    dan menggabungkannya ke dalam format database.
    """

    def __init__(self, output_dir: str = "datasets/scraped"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        self.wikipedia = WikipediaScraper()
        self.gbif = GBIFScraper()
        self.fao = FAOScraper()
        self.worms = WoRMSScraper()

    def scrape_all(self) -> List[Dict]:
        """Scrape semua spesies dari semua sumber."""
        all_data = []

        for scientific_name in TARGET_SPECIES:
            common_name = COMMON_NAMES.get(scientific_name, scientific_name)
            logger.info(f"\n🦀 Scraping: {scientific_name} ({common_name})")

            species_data = {
                "scientific_name": scientific_name,
                "common_name": common_name,
                "scraped_at": datetime.now().isoformat(),
                "sources": {},
            }

            # Wikipedia
            logger.info(f"  → Wikipedia...")
            wiki_data = self.wikipedia.scrape(scientific_name)
            if wiki_data:
                species_data["sources"]["wikipedia"] = wiki_data
                species_data["description"] = wiki_data.get("description", "")
            time.sleep(1)

            # GBIF
            logger.info(f"  → GBIF...")
            gbif_data = self.gbif.scrape(scientific_name)
            if gbif_data:
                species_data["sources"]["gbif"] = gbif_data
                species_data["family"] = gbif_data.get("family", "")
                species_data["order"] = gbif_data.get("order", "")
            time.sleep(1)

            # FAO
            logger.info(f"  → FAO...")
            fao_data = self.fao.scrape(scientific_name)
            if fao_data:
                species_data["sources"]["fao"] = fao_data
                species_data["habitat"] = fao_data.get("habitat", "")
                species_data["distribution"] = fao_data.get("distribution", "")
            time.sleep(2)

            # WoRMS
            logger.info(f"  → WoRMS...")
            worms_data = self.worms.scrape(scientific_name)
            if worms_data:
                species_data["sources"]["worms"] = worms_data
            time.sleep(1)

            all_data.append(species_data)
            logger.info(f"  ✅ {common_name} scraped from {len(species_data['sources'])} sources")

        # Save to file
        output_file = os.path.join(self.output_dir, "species_data.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
        logger.info(f"\n✅ Data saved to {output_file}")

        return all_data

    def save_to_database(self, data: List[Dict], db_session):
        """Save scraped data to PostgreSQL database."""
        from models.db_models import SpeciesDatabase
        
        for species_data in data:
            try:
                # Convert to DB model
                db_entry = SpeciesDatabase(
                    species_name=species_data.get("common_name", ""),
                    scientific_name=species_data.get("scientific_name", ""),
                    family=species_data.get("family", ""),
                    habitat=species_data.get("habitat", ""),
                    characteristics=species_data.get("description", "")[:2000] if species_data.get("description") else "",
                    distribution=species_data.get("distribution", ""),
                    source_url=species_data.get("sources", {}).get("gbif", {}).get("source_url", ""),
                    additional_data=species_data.get("sources", {}),
                )
                db_session.merge(db_entry)
                db_session.commit()
                logger.info(f"Saved: {species_data.get('common_name')}")
            except Exception as e:
                logger.error(f"DB save error: {e}")
                db_session.rollback()


class KaggleScraper:
    """
    Download dataset kepiting dari Kaggle.
    Memerlukan Kaggle API key yang sudah dikonfigurasi.
    """

    def __init__(self, username: str, api_key: str):
        self.username = username
        self.api_key = api_key

    def download_datasets(self, output_dir: str = "datasets/kaggle"):
        """Download relevant crab datasets from Kaggle."""
        try:
            import kaggle
            os.environ["KAGGLE_USERNAME"] = self.username
            os.environ["KAGGLE_KEY"] = self.api_key

            os.makedirs(output_dir, exist_ok=True)

            # Search for crab-related datasets
            datasets_to_download = [
                "crab-age-prediction",
                "crabs-dataset",
                "sea-animals-image-dataset",
            ]

            for dataset in datasets_to_download:
                try:
                    api = kaggle.KaggleApi()
                    api.authenticate()
                    api.dataset_download_files(dataset, path=output_dir, unzip=True)
                    logger.info(f"✅ Downloaded: {dataset}")
                except Exception as e:
                    logger.warning(f"Failed to download {dataset}: {e}")

        except ImportError:
            logger.warning("Kaggle library not installed. Run: pip install kaggle")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = CrabDataScraper()
    data = scraper.scrape_all()
    print(f"\n✅ Scraped {len(data)} species records")
