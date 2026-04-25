"""Fusion PTF (holdings) + snapshot CIQ à une date."""
from __future__ import annotations

import pandas as pd

from src.data.schemas_ciq import (
    CIQ_COL_DATE,
    CIQ_COL_ISIN,
    CIQ_COL_NAME,
)
from src.data.schemas_ptf import PTF_COL_ISIN, PTF_COL_WEIGHT


def merge_ptf_ciq(
    holdings: pd.DataFrame,
    ciq_asof: pd.DataFrame,
    extra_ciq_columns: list[str],
) -> pd.DataFrame:
    """``holdings`` : ISIN, Weight (PTF). ``ciq_asof`` : une date, une ligne par ISIN du bench."""
    h = holdings.rename(
        columns={PTF_COL_ISIN: "isin", PTF_COL_WEIGHT: "ptf_w"}
    )
    c = ciq_asof[[CIQ_COL_ISIN, CIQ_COL_NAME] + [c for c in extra_ciq_columns if c in ciq_asof.columns]].copy()
    c = c.rename(columns={CIQ_COL_ISIN: "isin", CIQ_COL_NAME: "name"})
    out = h.merge(c, on="isin", how="left")
    return out


def attach_ptf_weight_to_ciq(
    ciq_bench: pd.DataFrame,
    holdings: pd.DataFrame,
) -> pd.DataFrame:
    """Pour chaque ligne CIQ, ajoute ``ptf_w`` (0 si hors portefeuille). ``holdings`` : ISIN + Weight."""
    h = holdings.rename(
        columns={PTF_COL_ISIN: "isin", PTF_COL_WEIGHT: "ptf_w_src"}
    )
    wmap = h.drop_duplicates(subset=["isin"]).set_index("isin")["ptf_w_src"]
    wmap.index = wmap.index.astype(str)
    c = ciq_bench.copy()
    c["ptf_w"] = c[CIQ_COL_ISIN].astype(str).map(wmap).fillna(0.0)
    return c
