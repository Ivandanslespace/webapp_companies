"""Callbacks de la page d'analyse sectorielle (PTF, bench, onglet ICB19, univers = bench ∩ secteur)."""
from __future__ import annotations

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from dash import Input, Output, State, callback, no_update, callback_context
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
from src.services.peer_fan import peer_fan_timeseries
from src.data.repository import get_repository
from src.ui.components.description_panel import render_description_panel
from src.ui.components.news_timeline import render_news_timeline

from src.callbacks.index_composition import (  # réutilise constantes
    _fmt as _fmt_date,
    _round2,
    _weight_to_pct2,
    _is_bench_weight_col,
)

_GRAY = "rgba(120,120,120,0.2)"
_ACCENT = "#0F766E"
_BLUE = "#1E40AF"


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
    Output("ind-graph-factors", "figure"),
    Output("ind-graph-metric", "figure"),
    Output("ind-metric-title", "children"),
    Input("ind-selected-isin", "data"),
    Input("ind-active-metric", "data"),
    Input("ind-ptf-bench", "value"),
)
def _ind_detail_and_graphs(
    isin: str | None, active_m: str | None, bench: str | None
):
    repo = get_repository()
    empty = go.Figure()
    empty_m = go.Figure()
    if not isin:
        return (
            dmc.Text("Sélectionnez une ligne du tableau.", c="#6B7280"),
            dmc.Text("—", c="#6B7280"),
            empty,
            empty_m,
            "Autre indicateur (cliquez une cellule hors facteurs dans le tableau)",
        )
    desc = repo.get_description(isin)
    news = repo.get_news(isin)
    desc_c = (
        render_description_panel(desc) if desc is not None else dmc.Paper("—")
    )
    news_c = render_news_timeline(news)

    if not bench:
        return desc_c, news_c, empty, empty_m, "—"
    ridx = get_index_screen_repository()
    if bench not in ridx.df.columns:
        return desc_c, news_c, empty, empty_m, "—"
    H = ridx.history_for_index(bench)

    nfac = len([c for c in FACTOR_SCORE_COLUMNS if c in H.columns])
    if nfac == 0:
        fig7 = go.Figure()
        fig7.update_layout(title="Aucun facteur (colonnes) dans les données", height=200)
    else:
        n_rows = nfac
        fig7 = make_subplots(
            rows=n_rows,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.04,
            subplot_titles=[c for c in FACTOR_SCORE_COLUMNS if c in H.columns],
        )
        rnum = 0
        for col in FACTOR_SCORE_COLUMNS:
            if col not in H.columns:
                continue
            rnum += 1
            anc, peers, _err = peer_fan_timeseries(H, isin, col)
            for _pid, ser in peers.items():
                fig7.add_trace(
                    go.Scattergl(
                        x=ser.index,
                        y=ser.values,
                        mode="lines",
                        line={"color": _GRAY, "width": 1},
                        showlegend=False,
                        hoverinfo="skip",
                    ),
                    row=rnum,
                    col=1,
                )
            if anc is not None and len(anc) > 0:
                fig7.add_trace(
                    go.Scatter(
                        x=anc.index,
                        y=anc.values,
                        mode="lines",
                        name=col,
                        line={"color": _ACCENT, "width": 2},
                    ),
                    row=rnum,
                    col=1,
                )
        fig7.update_layout(
            template="plotly_white",
            height=max(200, 190 * n_rows),
            showlegend=False,
            margin=dict(l=50, r=20, t=20, b=20),
        )
        fig7.update_yaxes(tickformat=".2f", hoverformat=".2f")

    mtitle = "Autre indicateur (cliquez une cellule hors facteurs)"
    figm = go.Figure()
    if (
        active_m
        and active_m in H.columns
        and active_m not in FACTOR_SCORE_COLUMNS
        and active_m not in ("isin", "name", "ptf_w", CIQ_COL_ISIN, CIQ_COL_NAME)
    ):
        mtitle = f"Historique : {active_m}"
        anc, peers, err = peer_fan_timeseries(H, isin, active_m)
        for _pid, ser in peers.items():
            figm.add_trace(
                go.Scattergl(
                    x=ser.index,
                    y=ser.values,
                    mode="lines",
                    line={"color": _GRAY, "width": 1},
                    showlegend=False,
                )
            )
        if anc is not None and len(anc) > 0:
            figm.add_trace(
                go.Scatter(
                    x=anc.index,
                    y=anc.values,
                    mode="lines+markers",
                    name=isin,
                    line={"color": _BLUE, "width": 2.2},
                )
            )
        if err:
            figm.update_layout(title=err, height=320)
        else:
            figm.update_layout(
                template="plotly_white",
                height=400,
                xaxis_title="Date",
                yaxis_title=active_m,
                margin=dict(l=50, r=20, t=20, b=40),
            )
            figm.update_yaxes(tickformat=".2f", hoverformat=".2f")
    else:
        figm.update_layout(
            title="Sélectionnez une colonne (hors 7 facteurs) dans le tableau",
            height=200,
        )

    return desc_c, news_c, fig7, figm, mtitle


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
