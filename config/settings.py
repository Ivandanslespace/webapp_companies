"""Global application settings.

Centralized configuration: data paths, pagination, UI defaults.
Change values here to tune the app without touching UI or data code.
"""
from __future__ import annotations

from pathlib import Path

# --- Paths ---
ROOT_DIR: Path = Path(__file__).resolve().parent.parent
DATA_DIR: Path = ROOT_DIR / "data"

DES_PARQUET: Path = DATA_DIR / "last_DES.parquet"
NEWS_PARQUET: Path = DATA_DIR / "Last_NEWS_3months.parquet"
SCREEN_AGG_CIQ_PARQUET: Path = DATA_DIR / "screen_aggregateCIQ.parquet"
ICB_MAPPING_CSV: Path = DATA_DIR / "ICB_mapping.csv"
PTF_PARQUET: Path = DATA_DIR / "ptf.parquet"

# --- UI ---
APP_TITLE: str = "Panorama des Entreprises"
APP_SUBTITLE: str = "Descriptions & Actualités financières"

# Card grid pagination on the home page
CARDS_PER_PAGE: int = 24

# Max characters displayed in the card summary snippet
CARD_SUMMARY_CHARS: int = 180

# --- Server ---
HOST: str = "127.0.0.1"
PORT: int = 8050
DEBUG: bool = True
