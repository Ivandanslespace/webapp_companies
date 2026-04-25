"""Callbacks page PTF / bench (remplace l’ancien mode indice+metric)."""
from __future__ import annotations

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from dash import Input, Output, State, callback, no_update, callback_context
import dash_mantine_components as dmc

from src.data.index_screen_repository import get_index_screen_repository
from src.data.ptf_column_groups import (
    FACTOR_SCORE_COLUMNS,
    METADATA_DATA_TABLE_IDS,
    filter_groups_for_ciq,
)
from src.data.schemas_ciq import (
    CIQ_COL_DATE,
    CIQ_COL_ISIN,
    CIQ_COL_NAME,
    WEIGHT_IN_PREFIX,
)
from src.data.ptf_repository import get_ptf_repository
from src.data.schemas_ptf import PTF_COL_ISIN, PTF_COL_WEIGHT
from src.services.ptf_table import merge_ptf_ciq
from src.services.peer_fan import peer_fan_timeseries
from src.data.repository import get_repository
from src.ui.components.description_panel import render_description_panel
from src.ui.components.news_timeline import render_news_timeline

_GRAY = "rgba(120,120,120,0.2)"
_ACCENT = "#0F766E"
_BLUE = "#1E40AF"


def _fmt(d: str | None) -> str:
    if d is None:
        return ""
    return pd.Timestamp(d).strftime("%Y-%m-%d")


def _round2(v) -> float | None:
    """Valeur numérique : 2 décimales (affichage)."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    try:
        return round(float(v), 2)
    except (TypeError, ValueError):
        return None


def _weight_to_pct2(v) -> float | None:
    """Poids 0–1 → pourcentage numérique (×100), 2 décimales."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    try:
        return round(float(v) * 100.0, 2)
    except (TypeError, ValueError):
        return None


def _is_bench_weight_col(cid: str) -> bool:
    return isinstance(cid, str) and cid.startswith(WEIGHT_IN_PREFIX)


@callback(
    Output("ptf-date", "data"),
    Output("ptf-date", "value"),
    Input("ptf-bench", "value"),
)
def _ptf_bench_dates(bench: str | None):
    if not bench:
        return [], None
    r = get_index_screen_repository()
    ds = r.available_dates_for_index(bench)
    data = [{"value": _fmt(x), "label": _fmt(x)} for x in ds]
    v = data[-1]["value"] if data else None
    return data, v


@callback(
    Output("ptf-cols", "value", allow_duplicate=True),
    Input("ptf-add-group", "value"),
    State("ptf-cols", "value"),
    State("ptf-bench", "value"),
    prevent_initial_call=True,
)
def _ptf_append_group(grp: str | None, cur: list | None, bench: str | None):
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
    Output("ptf-table", "data"),
    Output("ptf-table", "columns"),
    Input("ptf-name", "value"),
    Input("ptf-bench", "value"),
    Input("ptf-date", "value"),
    Input("ptf-cols", "value"),
)
def _ptf_table(ptf: str | None, bench: str | None, date: str | None, cols: list | None):
    if not ptf or not bench or not date or not cols:
        return [], []
    prepo = get_ptf_repository()
    idx = get_index_screen_repository()
    asof = pd.Timestamp(date)
    hold = prepo.holdings_asof(ptf, asof)
    if hold.empty:
        return [], []
    ciq = idx.df
    ciq_d = ciq[ciq[CIQ_COL_DATE] == asof]
    extra = [c for c in cols if c in ciq.columns]
    merged = merge_ptf_ciq(hold, ciq_d, extra, ciq_full=ciq)
    disp = ["isin", "name", "ptf_w"] + [c for c in extra if c not in ("isin", "name")]
    disp = [x for i, x in enumerate(disp) if x not in disp[:i]]
    for c in extra:
        if c not in merged.columns and c in idx.df.columns:
            pass
    rows = []
    for _, r in merged.iterrows():
        row: dict = {
            "isin": r.get("isin", ""),
            "name": r.get("name", "") if pd.notna(r.get("name")) else "",
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
        if c in ("isin", "name", "ptf_w"):
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
    Output("ptf-desc-wrap", "children"),
    Output("ptf-news-wrap", "children"),
    Output("ptf-graph-factors", "figure"),
    Output("ptf-graph-metric", "figure"),
    Output("ptf-metric-title", "children"),
    Input("ptf-selected-isin", "data"),
    Input("ptf-active-metric", "data"),
    Input("ptf-bench", "value"),
)
def _ptf_detail_and_graphs(
    isin: str | None, active_m: str | None, bench: str | None
):
    repo = get_repository()
    empty = go.Figure()
    empty_m = go.Figure()
    if not isin:
        return (
            dmc.Text(
                "Cochez une ligne du tableau (sélection à gauche) pour charger description, actualités et graphiques.",
                c="#6B7280",
            ),
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


def _row_index_for_isin(data: list | None, isin_s: str) -> list[int]:
    if not data or not isin_s:
        return []
    for i, r in enumerate(data):
        if r.get("isin") is not None and str(r.get("isin")).strip() == isin_s:
            return [i]
    return []


@callback(
    Output("ptf-selected-isin", "data"),
    Output("ptf-active-metric", "data"),
    Output("ptf-table", "selected_rows"),
    Input("ptf-table", "data"),
    Input("ptf-table", "active_cell"),
    State("ptf-cols", "value"),
    State("ptf-selected-isin", "data"),
    State("ptf-active-metric", "data"),
)
def _ptf_data_or_cell(
    data: list | None,
    cell: dict | None,
    ptf_cols: list | None,
    cur_isin: str | None,
    cur_metric: str | None,
):
    """Tableau mis à jour ou clic cellule : ISIN + coches alignées (sans cycle avec selected_rows)."""
    if not callback_context.triggered:
        return no_update, no_update, no_update
    prop_id = callback_context.triggered[0]["prop_id"]
    ptf_cols = ptf_cols or []

    if prop_id == "ptf-table.data":
        if not data:
            return None, None, []
        valid = {str(r.get("isin")) for r in data if r.get("isin")}
        if cur_isin and str(cur_isin).strip() in valid:
            m = cur_metric
            if m and m not in ptf_cols:
                m = None
            isin_s = str(cur_isin).strip()
            return isin_s, m, _row_index_for_isin(data, isin_s)
        return None, None, []

    if not data:
        return no_update, no_update, no_update

    if prop_id == "ptf-table.active_cell" and cell:
        r, cid = cell.get("row"), cell.get("column_id")
        if r is None or cid is None or r >= len(data):
            return no_update, no_update, no_update
        row = data[r]
        isin = row.get("isin")
        if not isin:
            return no_update, no_update, no_update
        isin_s = str(isin).strip()
        sel = [r]
        if cid in ("isin", "name", "ptf_w"):
            return isin_s, None, sel
        if isinstance(cid, str) and cid.startswith(WEIGHT_IN_PREFIX):
            return isin_s, None, sel
        if cid not in ptf_cols:
            return isin_s, no_update, sel
        if cid in FACTOR_SCORE_COLUMNS:
            return isin_s, None, sel
        return isin_s, cid, sel

    return no_update, no_update, no_update


@callback(
    Output("ptf-selected-isin", "data", allow_duplicate=True),
    Output("ptf-active-metric", "data", allow_duplicate=True),
    Input("ptf-table", "selected_rows"),
    State("ptf-table", "data"),
    State("ptf-selected-isin", "data"),
    prevent_initial_call=True,
)
def _ptf_checkbox_row(
    selected_rows: list | None,
    data: list | None,
    cur_isin: str | None,
):
    """Coche ligne uniquement : si ISIN inchangé (sync serveur), ne pas écraser la métrique active."""
    if not data or not selected_rows:
        return no_update, no_update
    r = int(selected_rows[0])
    if r < 0 or r >= len(data):
        return no_update, no_update
    isin = data[r].get("isin")
    if not isin:
        return no_update, no_update
    isin_s = str(isin).strip()
    if isin_s == str(cur_isin or "").strip():
        return no_update, no_update
    return isin_s, None
