"""Pure filter functions used by the home page.

Keeping these as standalone pure functions makes them trivially unit-testable
without spinning up the Dash app.
"""
from __future__ import annotations

from typing import Iterable, Optional

import pandas as pd

from src.data.schemas import COL_COUNTRY, COL_ISIN, COL_NAME, COL_SECTOR


def apply_filters(
    df: pd.DataFrame,
    countries: Optional[Iterable[str]] = None,
    sectors: Optional[Iterable[str]] = None,
    query: Optional[str] = None,
) -> pd.DataFrame:
    """Filter a companies DataFrame by country, sector, and free-text query.

    - `countries` / `sectors`: None or empty iterable means "no filter".
    - `query`: matched against NAME and ISIN, case-insensitive substring.
    """
    result = df

    if countries:
        country_set = set(countries)
        result = result[result[COL_COUNTRY].isin(country_set)]

    if sectors:
        sector_set = set(sectors)
        result = result[result[COL_SECTOR].isin(sector_set)]

    if query:
        q = query.strip().lower()
        if q:
            name_hit = result[COL_NAME].astype(str).str.lower().str.contains(q, na=False)
            isin_hit = result[COL_ISIN].astype(str).str.lower().str.contains(q, na=False)
            result = result[name_hit | isin_hit]

    return result.reset_index(drop=True)


def paginate(df: pd.DataFrame, page: int, page_size: int) -> pd.DataFrame:
    """Return a single page slice (1-indexed page numbers)."""
    if page < 1:
        page = 1
    start = (page - 1) * page_size
    end = start + page_size
    return df.iloc[start:end].reset_index(drop=True)


def total_pages(n_items: int, page_size: int) -> int:
    """Compute the total number of pages for given item count."""
    if page_size <= 0 or n_items <= 0:
        return 1
    return (n_items + page_size - 1) // page_size
