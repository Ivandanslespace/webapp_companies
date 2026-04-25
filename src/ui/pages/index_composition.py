"""Page portefeuille (PTF) + bench + tableau CIQ + détail entreprise + graphiques fan."""
from __future__ import annotations

import dash
import dash_mantine_components as dmc
from dash import dcc, html
from dash.dash_table import DataTable

from src.data.index_screen_repository import get_index_screen_repository
from src.data.ptf_column_groups import default_summary_column_names, filter_groups_for_ciq
from src.data.ptf_repository import get_ptf_repository
from src.data.schemas_ciq import (
    CIQ_COL_FACTSET_ECONOMY,
    CIQ_COL_FACTSET_IND,
    CIQ_COL_ICB_SUPERSECTOR,
)

dash.register_page(__name__, path="/indice", name="Composition indice")


def _fmt_date(ts) -> str:
    try:
        return ts.strftime("%Y-%m-%d")
    except Exception:
        return str(ts)


def layout() -> html.Div:
    idx = get_index_screen_repository()
    ptf_repo = get_ptf_repository()
    av = set(idx.df.columns)
    indices = idx.list_indices()
    index_data = [{"value": ic.column, "label": ic.label} for ic in indices]
    default_bench = (
        "Weight in MSCI WORLD"
        if any(ic.column == "Weight in MSCI WORLD" for ic in indices)
        else (indices[0].column if indices else None)
    )
    dates_l: list[str] = []
    if default_bench:
        dates_l = [_fmt_date(d) for d in idx.available_dates_for_index(default_bench)]
    default_date = dates_l[-1] if dates_l else None

    ptf_names = ptf_repo.list_ptf_names()
    default_ptf = ptf_names[0] if ptf_names else None

    dcols = default_summary_column_names(av, default_bench or "")
    groups = filter_groups_for_ciq(av)
    col_options: list[dict] = []
    for g in groups:
        for lab, c in g.entries:
            col_options.append({"label": f"{g.label} — {lab}", "value": c})
    group_add_opts = [{"value": g.id, "label": g.label} for g in groups]

    return html.Div(
        [
            # session：navigation hors page puis retour sans perdre filtres / société sélectionnée
            dcc.Store(id="ptf-selected-isin", data=None, storage_type="session"),
            dcc.Store(id="ptf-active-metric", data=None, storage_type="session"),
            dmc.Title("Portefeuille & comparaison sectorielle (bench)", order=2, c="#111827"),
            dmc.Space(h=12),
            dmc.Paper(
                withBorder=True,
                radius="md",
                p="md",
                children=dmc.Stack(
                    gap="sm",
                    children=[
                        dmc.SimpleGrid(
                            cols={"base": 1, "sm": 2, "lg": 4},
                            spacing="md",
                            children=[
                                dmc.Select(
                                    id="ptf-name",
                                    label="Portefeuille (PTF)",
                                    data=[{"value": n, "label": n} for n in ptf_names],
                                    value=default_ptf,
                                    searchable=True,
                                    clearable=False,
                                    persistence=True,
                                    persistence_type="session",
                                ),
                                dmc.Select(
                                    id="ptf-bench",
                                    label="Benchmark (pondération)",
                                    data=index_data,
                                    value=default_bench,
                                    searchable=True,
                                    clearable=False,
                                    persistence=True,
                                    persistence_type="session",
                                ),
                                dmc.Select(
                                    id="ptf-date",
                                    label="Date",
                                    data=[{"value": d, "label": d} for d in dates_l],
                                    value=default_date,
                                    searchable=True,
                                    clearable=False,
                                    persistence=True,
                                    persistence_type="session",
                                ),
                                dmc.Select(
                                    id="ptf-add-group",
                                    label="Ajouter un groupe de colonnes",
                                    data=group_add_opts,
                                    value=None,
                                    clearable=True,
                                    placeholder="Choisir…",
                                    persistence=True,
                                    persistence_type="session",
                                ),
                            ],
                        ),
                        dmc.MultiSelect(
                            id="ptf-cols",
                            label="Colonnes affichées (résumé par défaut)",
                            data=col_options,
                            value=dcols,
                            searchable=True,
                            clearable=True,
                            nothingFoundMessage="Aucune colonne",
                            persistence=True,
                            persistence_type="session",
                        ),
                        dmc.Text(
                            "Pairs (gris) : même bench, secteur = code « Benchmark ICB Supersector » "
                            f"mappé (libellé ICB dans {CIQ_COL_ICB_SUPERSECTOR}) si dispo, sinon "
                            f"{CIQ_COL_FACTSET_IND}, sinon {CIQ_COL_FACTSET_ECONOMY} ; "
                            "région : West Europe / North America / Mid East & autres (Others). "
                            f"Jusqu'à 80 courbes pairs. ",
                            size="xs",
                            c="#6B7280",
                        ),
                    ],
                ),
            ),
            dmc.Space(h=12),
            dmc.Text(
                "Sélectionnez une ligne (case à gauche) pour afficher description, actualités et graphiques. "
                "Fiche dédiée : ouvrir `/company/<ISIN>` dans un nouvel onglet depuis le catalogue ou en remplaçant l’ISIN.",
                size="xs",
                c="#6B7280",
            ),
            dmc.Space(h=8),
            dmc.Paper(
                withBorder=True,
                radius="md",
                p="md",
                children=html.Div(
                    dcc.Loading(
                        type="default",
                        children=DataTable(
                            id="ptf-table",
                            data=[],
                            columns=[],
                            page_size=25,
                            row_selectable="single",
                            selected_rows=[],
                            active_cell=None,
                            cell_selectable=True,
                            sort_action="native",
                            style_table={"overflowX": "auto", "minWidth": "600px"},
                            style_cell={"textAlign": "left", "padding": "6px 10px", "fontSize": "13px"},
                            style_header={"fontWeight": 600, "backgroundColor": "#F3F4F6"},
                        ),
                    ),
                    style={"overflowX": "auto", "maxHeight": "480px", "overflowY": "auto"},
                ),
            ),
            dmc.Space(h=16),
            dmc.Grid(
                gutter="md",
                children=[
                    dmc.GridCol(
                        span={"base": 12, "lg": 8},
                        children=html.Div(id="ptf-desc-wrap"),
                    ),
                    dmc.GridCol(
                        span={"base": 12, "lg": 4},
                        children=html.Div(id="ptf-news-wrap"),
                    ),
                ],
            ),
            dmc.Space(h=12),
            dmc.Paper(
                withBorder=True,
                radius="md",
                p="md",
                children=dmc.Stack(
                    gap="sm",
                    children=[
                        dmc.Text("Scores (facteurs) — historique vs pairs bench", fw=600),
                        dcc.Graph(
                            id="ptf-graph-factors",
                            config={"displaylogo": False},
                            style={"height": "1400px"},
                        ),
                    ],
                ),
            ),
            dmc.Space(h=12),
            dmc.Paper(
                withBorder=True,
                radius="md",
                p="md",
                children=dmc.Stack(
                    gap="sm",
                    children=[
                        dmc.Text(id="ptf-metric-title", children="Autre indicateur (cliquer une cellule hors facteurs)"),
                        dcc.Graph(
                            id="ptf-graph-metric",
                            config={"displaylogo": False},
                            style={"height": "400px"},
                        ),
                    ],
                ),
            ),
        ]
    )
