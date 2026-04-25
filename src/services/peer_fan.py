"""Séries temporelles « fan » : ancre + pairs (même secteur, même seau régional, bench)."""
from __future__ import annotations

import random
from typing import Optional

import pandas as pd

from src.data.schemas_ciq import (
    CIQ_COL_DATE,
    CIQ_COL_ISIN,
    CIQ_COL_REGION,
    PEER_INDUSTRY_COLS_ORDER,
)
from src.services.region_bucket import region_bucket_value

MAX_PEER_TRACES: int = 80


def _anchor_industry_key(r: pd.Series) -> Optional[tuple[str, str]]:
    """Premier champ secteur non vide, dans l'ordre ICB19 → FactSet Ind → FactSet Economy.

    Retour (nom_colonne, valeur_normalisée_en_minuscule) pour comparaison stricte.
    """
    for col in PEER_INDUSTRY_COLS_ORDER:
        if col not in r.index:
            continue
        v = r.get(col)
        if v is not None and pd.notna(v) and str(v).strip():
            return (col, str(v).strip().lower())
    return None


def _peers_on_date(
    sub: pd.DataFrame,
    anchor_isin: str,
) -> tuple[Optional[object], Optional[str], set[str]]:
    """(clef_ignorée, seau_région, isins_pairs) ; pairs = même industrie (col. alignée) + même seau + bench."""
    arow = sub[sub[CIQ_COL_ISIN] == anchor_isin]
    if arow.empty:
        return None, None, set()
    r0 = arow.iloc[0]
    ind_key = _anchor_industry_key(r0)
    if ind_key is None:
        return None, None, set()
    col, val = ind_key
    if col not in sub.columns:
        return None, None, set()
    buck = region_bucket_value(r0.get(CIQ_COL_REGION))
    s: set[str] = set()
    for _, r in sub.iterrows():
        if r[CIQ_COL_ISIN] == anchor_isin:
            continue
        rv = r.get(col)
        if pd.isna(rv) or str(rv).strip().lower() != val:
            continue
        if region_bucket_value(r.get(CIQ_COL_REGION)) != buck:
            continue
        s.add(str(r[CIQ_COL_ISIN]))
    return ind_key, buck, s


def peer_fan_timeseries(
    index_history: pd.DataFrame,
    anchor_isin: str,
    metric_col: str,
    *,
    seed: int = 42,
) -> tuple[Optional[pd.Series], dict[str, pd.Series], Optional[str]]:
    """Ancre : série complète dans l'historique bench. Pairs : points (date, valeur) si pair ce jour-là."""
    if index_history is None or index_history.empty:
        return None, {}, "Aucun historique bench"
    need = {CIQ_COL_DATE, CIQ_COL_ISIN, metric_col, CIQ_COL_REGION}
    if not need.issubset(index_history.columns):
        return None, {}, "Colonnes requises manquantes"
    if not any(c in index_history.columns for c in PEER_INDUSTRY_COLS_ORDER):
        return None, {}, "Aucune colonne secteur (ICB / FactSet)"

    H = index_history.copy()
    H[CIQ_COL_DATE] = pd.to_datetime(H[CIQ_COL_DATE], errors="coerce")
    H = H.dropna(subset=[CIQ_COL_DATE])

    dates = sorted(H[CIQ_COL_DATE].unique())
    peer_dates: dict[str, list[tuple[pd.Timestamp, float]]] = {}
    peer_union: set[str] = set()

    for d in dates:
        sub = H[H[CIQ_COL_DATE] == d]
        _i, _b, peers = _peers_on_date(sub, anchor_isin)
        if not peers:
            continue
        peer_union |= peers
        for pid in peers:
            gr = sub[sub[CIQ_COL_ISIN] == pid]
            if gr.empty:
                continue
            v = gr.iloc[0].get(metric_col)
            if v is None or (isinstance(v, float) and pd.isna(v)):
                continue
            peer_dates.setdefault(pid, []).append((pd.Timestamp(d), float(v)))

    if len(peer_union) > MAX_PEER_TRACES:
        rng = random.Random(seed)
        peer_list = sorted(peer_union)
        keep = set(rng.sample(peer_list, MAX_PEER_TRACES))
        peer_dates = {k: v for k, v in peer_dates.items() if k in keep}

    out_peers: dict[str, pd.Series] = {}
    for pid, pairs in peer_dates.items():
        if not pairs:
            continue
        pairs = sorted(pairs, key=lambda x: x[0])
        idx = [p[0] for p in pairs]
        vals = [p[1] for p in pairs]
        out_peers[pid] = pd.Series(vals, index=pd.DatetimeIndex(idx))

    arows = H[H[CIQ_COL_ISIN] == anchor_isin][[CIQ_COL_DATE, metric_col]].dropna(
        subset=[metric_col]
    )
    if arows.empty:
        anc_s: Optional[pd.Series] = None
    else:
        anc_s = arows.set_index(CIQ_COL_DATE)[metric_col].sort_index()
        anc_s = anc_s[~anc_s.index.duplicated(keep="last")]

    return anc_s, out_peers, None
