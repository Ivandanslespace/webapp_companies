"""Callbacks de la page d'analyse sectorielle (PTF, bench, onglet ICB19, univers = bench ∩ secteur)."""
from __future__ import annotations

from collections import OrderedDict

import plotly.graph_objects as go
import pandas as pd
from dash import Input, Output, State, callback, clientside_callback, no_update, callback_context
import dash_mantine_components as dmc

from src.data.index_screen_repository import get_index_screen_repository
from src.data.ptf_column_groups import (
    FACTOR_SCORE_COLUMNS,
    filter_groups_for_ciq,
)
from src.data.schemas_ciq import (
    CIQ_COL_ISIN,
    CIQ_COL_NAME,
    CIQ_COL_ICB_SUPERSECTOR,
    WEIGHT_IN_PREFIX,
)
from src.data.ptf_repository import get_ptf_repository
from src.services.ptf_table import attach_ptf_weight_to_ciq
from src.data.repository import get_repository
from src.ui.components.description_panel import render_description_panel
from src.ui.components.news_timeline import render_news_timeline

from src.callbacks.index_composition import (  # réutilise constantes + figures pairs
    _fmt as _fmt_date,
    _round2,
    _weight_to_pct2,
    _is_bench_weight_col,
    build_peer_factor_figure,
    build_peer_metric_figure,
)
from src.services.drawer_figure_cache import (
    get_ind_factor_dict,
    get_ind_metric_bundle,
    ind_factor_cache_key,
    ind_metric_cache_key,
    set_ind_factor,
    set_ind_metric_bundle,
)

_MAX_IND_DETAIL = 20
_ind_detail_cache: OrderedDict[str, tuple] = OrderedDict()


def _ind_detail_cache_get(isin: str) -> tuple | None:
    if isin not in _ind_detail_cache:
        return None
    _ind_detail_cache.move_to_end(isin)
    return _ind_detail_cache[isin]


def _ind_detail_cache_set(isin: str, desc, news_df) -> None:
    news_c = news_df.copy() if hasattr(news_df, "copy") else news_df
    _ind_detail_cache[isin] = (desc, news_c)
    while len(_ind_detail_cache) > _MAX_IND_DETAIL:
        _ind_detail_cache.popitem(last=False)

@callback(
    Output("ind-ptf-date", "data"),
    Output("ind-ptf-date", "value"),
    Input("ind-ptf-bench", "value"),
)
def _ind_bench_dates(bench: str | None):
    if not bench:
        return [], None
    r = get_index_screen_repository()
    ds = r.available_dates_for_index(bench)
    data = [{"value": _fmt_date(x), "label": _fmt_date(x)} for x in ds]
    v = data[-1]["value"] if data else None
    return data, v


@callback(
    Output("ind-ptf-cols", "value", allow_duplicate=True),
    Input("ind-ptf-add-group", "value"),
    State("ind-ptf-cols", "value"),
    State("ind-ptf-bench", "value"),
    prevent_initial_call=True,
)
def _ind_append_group(grp: str | None, cur: list | None, bench: str | None):
    if not grp or cur is None:
        return no_update
    r = get_index_screen_repository()
    av = set(r.df.columns)
    groups = filter_groups_for_ciq(av)
    g = next((x for x in groups if x.id == grp), None)
    if not g:
        return no_update
    add = [c for _, c in g.entries if c in av]
    if bench and bench in av and bench not in add:
        pass
    nxt = list(dict.fromkeys([*cur, *add]))
    return nxt


@callback(
    Output("ind-selected-isin", "data"),
    Output("ind-active-metric", "data"),
    Input("ind-ptf-name", "value"),
    Input("ind-ptf-bench", "value"),
    Input("ind-ptf-date", "value"),
    Input("ind-ptf-cols", "value"),
    Input("ind-icb-tabs", "value"),
)
def _ind_clear_stores_on_filter(
    _ptf: str | None,
    _bench: str | None,
    _date: str | None,
    _cols: list | None,
    _sector: str | None,
):
    """Réinitialise la sélection dès qu’un filtre (PTF, bench, date, colonnes, onglet) change."""
    return None, None


@callback(
    Output("ind-ptf-table", "data"),
    Output("ind-ptf-table", "columns"),
    Input("ind-ptf-name", "value"),
    Input("ind-ptf-bench", "value"),
    Input("ind-ptf-date", "value"),
    Input("ind-ptf-cols", "value"),
    Input("ind-icb-tabs", "value"),
)
def _ind_table(
    ptf: str | None,
    bench: str | None,
    date: str | None,
    cols: list | None,
    sector: str | None,
):
    if not ptf or not bench or not date or not cols or not sector:
        return [], []
    prepo = get_ptf_repository()
    idx = get_index_screen_repository()
    asof = pd.Timestamp(date)
    hold = prepo.holdings_asof(ptf, asof)
    ciq = idx.constituents_asof(asof, bench)
    if ciq.empty:
        return [], []
    scol = CIQ_COL_ICB_SUPERSECTOR
    if scol not in ciq.columns:
        return [], []
    ciq = ciq[ciq[scol].astype(str).str.strip() == str(sector).strip()].copy()
    if ciq.empty:
        return [], []
    ciq = ciq.sort_values(
        by=[CIQ_COL_NAME] if CIQ_COL_NAME in ciq.columns else [CIQ_COL_ISIN]
    )
    extra = [c for c in cols if c in ciq.columns]
    merged = attach_ptf_weight_to_ciq(ciq, hold)
    merged = merged.sort_values(
        by=["ptf_w", CIQ_COL_NAME] if CIQ_COL_NAME in merged.columns else ["ptf_w", CIQ_COL_ISIN],
        ascending=[False, True],
    )
    rows = []
    for _, r in merged.iterrows():
        row: dict = {
            "isin": str(r[CIQ_COL_ISIN]) if r.get(CIQ_COL_ISIN) is not None else "",
            "name": r.get(CIQ_COL_NAME, "") if pd.notna(r.get(CIQ_COL_NAME)) else "",
            "ptf_w": _weight_to_pct2(r.get("ptf_w", None)),
        }
        for c in extra:
            v = r.get(c, None) if c in merged.columns else None
            if v is not None and pd.isna(v):
                v = None
            if _is_bench_weight_col(c):
                row[c] = _weight_to_pct2(v)
            else:
                row[c] = _round2(v) if v is not None else None
        rows.append(row)
    table_cols: list[dict] = [
        {"name": "ISIN", "id": "isin"},
        {"name": "Nom", "id": "name"},
        {
            "name": "Poids PTF (%)",
            "id": "ptf_w",
            "type": "numeric",
            "format": {"specifier": ",.2f"},
        },
    ]
    for c in extra:
        if c in (CIQ_COL_ISIN, CIQ_COL_NAME, "ptf_w"):
            continue
        col_def: dict = {
            "id": c,
            "type": "numeric",
            "format": {"specifier": ",.2f"},
        }
        if _is_bench_weight_col(c):
            col_def["name"] = f"{c} (%)"
        else:
            col_def["name"] = c
        table_cols.append(col_def)
    return rows, table_cols


@callback(
    Output("ind-desc-wrap", "children"),
    Output("ind-news-wrap", "children"),
    Input("ind-selected-isin", "data"),
)
def _ind_detail_panel(isin: str | None):
    if not isin:
        return (
            dmc.Text("Sélectionnez une ligne du tableau.", c="#6B7280"),
            dmc.Text("—", c="#6B7280"),
        )
    hit = _ind_detail_cache_get(isin)
    if hit is None:
        repo = get_repository()
        desc = repo.get_description(isin)
        news = repo.get_news(isin)
        _ind_detail_cache_set(isin, desc, news)
    else:
        desc, news = hit
    desc_c = (
        render_description_panel(desc) if desc is not None else dmc.Paper("—")
    )
    news_c = render_news_timeline(news)
    return desc_c, news_c


@callback(
    Output("ind-graph-factors", "figure"),
    Input("ind-selected-isin", "data"),
    Input("ind-ptf-bench", "value"),
    Input("ind-icb-tabs", "value"),
)
def _ind_factor_graphs(isin: str | None, bench: str | None, sector: str | None):
    empty = go.Figure()
    if not isin or not bench or not sector:
        return empty
    ridx = get_index_screen_repository()
    if bench not in ridx.df.columns:
        return empty
    key = ind_factor_cache_key(isin, bench, str(sector))
    hit = get_ind_factor_dict(key)
    if hit is not None:
        return hit
    H = ridx.history_for_index(bench)
    if H.empty:
        return empty
    fig = build_peer_factor_figure(H, isin)
    set_ind_factor(key, fig)
    return fig


@callback(
    Output("ind-graph-metric", "figure"),
    Output("ind-metric-title", "children"),
    Input("ind-selected-isin", "data"),
    Input("ind-active-metric", "data"),
    Input("ind-ptf-bench", "value"),
    Input("ind-icb-tabs", "value"),
)
def _ind_metric_graph(
    isin: str | None,
    active_m: str | None,
    bench: str | None,
    sector: str | None,
):
    empty_m = go.Figure()
    if not isin or not bench or not sector:
        return empty_m, "—"
    ridx = get_index_screen_repository()
    if bench not in ridx.df.columns:
        return empty_m, "—"
    key = ind_metric_cache_key(isin, bench, str(sector), active_m)
    bundle = get_ind_metric_bundle(key)
    if bundle is not None:
        return bundle
    H = ridx.history_for_index(bench)
    if H.empty:
        return empty_m, "—"
    fig, title = build_peer_metric_figure(H, isin, active_m)
    set_ind_metric_bundle(key, fig, str(title))
    return fig, title


@callback(
    Output("ind-selected-isin", "data", allow_duplicate=True),
    Output("ind-active-metric", "data", allow_duplicate=True),
    Input("ind-ptf-table", "active_cell"),
    Input("ind-ptf-table", "selected_rows"),
    State("ind-ptf-table", "data"),
    State("ind-ptf-cols", "value"),
    prevent_initial_call=True,
)
def _ind_row_or_cell_selection(
    cell: dict | None,
    selected_rows: list | None,
    data: list | None,
    ptf_cols: list | None,
):
    """Priorité au clic sur une cellule ; sinon sélection de ligne (colonne d’index)."""
    ptf_cols = ptf_cols or []
    if not data:
        return no_update, no_update
    ids = [t["prop_id"] for t in (callback_context.triggered or [])]
    cell_event = any("active_cell" in p for p in ids)
    row_event = any("selected_rows" in p for p in ids)

    if cell_event and cell and cell.get("row") is not None and cell.get("column_id") is not None:
        r, cid = cell["row"], cell["column_id"]
        if r is None or cid is None or r >= len(data):
            return no_update, no_update
        row = data[r]
        isin = row.get("isin")
        if not isin:
            return no_update, no_update
        if cid in ("isin", "name", "ptf_w"):
            return isin, None
        if isinstance(cid, str) and cid.startswith(WEIGHT_IN_PREFIX):
            return isin, None
        if cid not in ptf_cols:
            return isin, no_update
        if cid in FACTOR_SCORE_COLUMNS:
            return isin, None
        return isin, cid

    if row_event and selected_rows:
        r = int(selected_rows[0])
        if 0 <= r < len(data):
            isin = data[r].get("isin")
            if isin:
                return isin, None
    return no_update, no_update


@callback(
    Output("ind-drawer-open", "data"),
    Input("ind-selected-isin", "data"),
    Input("ind-drawer-backdrop", "n_clicks"),
    Input("ind-drawer-close", "n_clicks"),
    Input("ind-drawer-reopen", "n_clicks"),
)
def _ind_drawer_open(isin, _nb, _nc, _nr):
    if not callback_context.triggered:
        return False
    tid = callback_context.triggered_id
    if tid in ("ind-drawer-backdrop", "ind-drawer-close"):
        return False
    if tid == "ind-drawer-reopen":
        return bool(isin)
    if tid == "ind-selected-isin":
        return bool(isin)
    return False


@callback(
    Output("ind-drawer-overlay", "className"),
    Input("ind-drawer-open", "data"),
)
def _ind_drawer_overlay_class(open_):
    base = "drawer-overlay"
    return f"{base} drawer-overlay--open" if open_ else base


@callback(
    Output("ind-drawer-fab-wrap", "style"),
    Input("ind-drawer-open", "data"),
    Input("ind-selected-isin", "data"),
)
def _ind_drawer_fab_style(open_, isin):
    show = bool(isin) and not open_
    return {"display": "block" if show else "none"}


@callback(
    Output("ind-drawer-seg", "value"),
    Input("ind-selected-isin", "data"),
    Input("ind-drawer-reopen", "n_clicks"),
)
def _ind_drawer_seg_reset(isin, _nr):
    return "description"


@callback(
    Output("ind-panel-description", "className"),
    Output("ind-panel-industry", "className"),
    Output("ind-panel-indicators", "className"),
    Input("ind-drawer-seg", "value"),
)
def _ind_drawer_panels(tab):
    tab = tab or "description"

    def one(k: str) -> str:
        b = "drawer-tab-panel"
        return f"{b} drawer-tab-panel--active" if tab == k else b

    return one("description"), one("industry"), one("indicators")


@callback(
    Output("ind-drawer-header", "children"),
    Input("ind-selected-isin", "data"),
    State("ind-ptf-table", "data"),
)
def _ind_drawer_header(isin, data):
    if not isin:
        return dmc.Text("—", size="sm", c="dimmed")
    name = str(isin)
    if data:
        for r in data:
            if str(r.get("isin", "")).strip() == str(isin).strip():
                nm = r.get("name")
                if nm:
                    name = str(nm)
                break
    return dmc.Stack(
        gap=4,
        children=[
            dmc.Text(name, fw=700, size="lg", lineClamp=3),
            dmc.Text(str(isin), size="xs", c="dimmed", ff="monospace"),
        ],
    )


clientside_callback(
    """
    function(open) {
        document.body.style.overflow = open ? 'hidden' : '';
        return 0;
    }
    """,
    Output("ind-drawer-scroll-helper", "data"),
    Input("ind-drawer-open", "data"),
)
