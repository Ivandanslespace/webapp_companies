"""Page d'analyse sectorielle : 19 onglets ICB19, univers = bench filtré par super-secteur + distinction PTF."""
from __future__ import annotations

import dash
import dash_mantine_components as dmc
from dash import dcc, html
from dash.dash_table import DataTable

from config.settings import ICB_MAPPING_CSV
from src.data.icb19_supersectors import icb_supersector_tab_label, load_icb19_supersector_labels
from src.data.index_screen_repository import get_index_screen_repository
from src.data.ptf_column_groups import default_summary_column_names, filter_groups_for_ciq
from src.data.ptf_repository import get_ptf_repository
from src.data.schemas_ciq import (
    CIQ_COL_FACTSET_ECONOMY,
    CIQ_COL_FACTSET_IND,
    CIQ_COL_ICB_SUPERSECTOR,
)

dash.register_page(__name__, path="/analyse-icb", name="Analyse sectorielle ICB")


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

    icb_list = load_icb19_supersector_labels()
    default_icb = icb_list[0] if icb_list else None
    dcc_tab_children = [
        dcc.Tab(
            label=icb_supersector_tab_label(lbl),
            value=lbl,
        )
        for lbl in icb_list
    ]

    return html.Div(
        className="page-industry-icb",
        children=[
            dcc.Store(id="ind-selected-isin", data=None),
            dcc.Store(id="ind-active-metric", data=None),
            dmc.Title("Analyse sectorielle (ICB19 × indice × portefeuille)", order=2, c="#111827"),
            dmc.Text(
                "Chaque sous-onglet correspond à un super-secteur ICB19 ; seules les sociétés "
                "dans ce secteur et avec un poids strictement positif dans l’indice choisi sont affichées. "
                "Fond de ligne : vert pâle = position PTF actuelle ; gris pâle = composante d’indice seule, hors PTF. "
                "Les colonnes sont identiques à la page « Composition indice » pour faciliter la comparaison.",
                size="sm",
                c="#4B5563",
            ),
            dmc.Space(h=10),
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
                                    id="ind-ptf-name",
                                    label="Portefeuille (PTF)",
                                    data=[{"value": n, "label": n} for n in ptf_names],
                                    value=default_ptf,
                                    searchable=True,
                                    clearable=False,
                                ),
                                dmc.Select(
                                    id="ind-ptf-bench",
                                    label="Benchmark (pondération)",
                                    data=index_data,
                                    value=default_bench,
                                    searchable=True,
                                    clearable=False,
                                ),
                                dmc.Select(
                                    id="ind-ptf-date",
                                    label="Date",
                                    data=[{"value": d, "label": d} for d in dates_l],
                                    value=default_date,
                                    searchable=True,
                                    clearable=False,
                                ),
                                dmc.Select(
                                    id="ind-ptf-add-group",
                                    label="Ajouter un groupe de colonnes",
                                    data=group_add_opts,
                                    value=None,
                                    clearable=True,
                                    placeholder="Choisir…",
                                ),
                            ],
                        ),
                        dmc.MultiSelect(
                            id="ind-ptf-cols",
                            label="Colonnes affichées (résumé par défaut)",
                            data=col_options,
                            value=dcols,
                            searchable=True,
                            clearable=True,
                            nothingFoundMessage="Aucune colonne",
                        ),
                        dmc.Text(
                            "Pairs (courbes grises) : même logique que « Composition indice » — "
                            f"secteur = {CIQ_COL_ICB_SUPERSECTOR} / {CIQ_COL_FACTSET_IND} / {CIQ_COL_FACTSET_ECONOMY} "
                            f"(cf. {ICB_MAPPING_CSV.name}).",
                            size="xs",
                            c="#6B7280",
                        ),
                    ],
                ),
            ),
            dmc.Space(h=12),
            html.Div(
                style={"overflowX": "auto", "width": "100%"},
                children=[
                    dcc.Tabs(
                        id="ind-icb-tabs",
                        value=default_icb,
                        vertical=False,
                        className="ind-icb-tabs-bar",
                        children=dcc_tab_children,
                    ),
                ],
            ),
            dmc.Space(h=12),
            dmc.Paper(
                withBorder=True,
                radius="md",
                p="md",
                children=html.Div(
                    dcc.Loading(
                        type="default",
                        children=DataTable(
                            id="ind-ptf-table",
                            data=[],
                            columns=[],
                            page_size=25,
                            row_selectable="single",
                            active_cell=None,
                            cell_selectable=True,
                            sort_action="native",
                            style_table={"overflowX": "auto", "minWidth": "600px"},
                            style_cell={"textAlign": "left", "padding": "6px 10px", "fontSize": "13px"},
                            style_header={"fontWeight": 600, "backgroundColor": "#F3F4F6"},
                            style_data_conditional=[
                                {
                                    "if": {"filter_query": "{ptf_w} > 0"},
                                    "backgroundColor": "rgba(16, 185, 129, 0.16)",
                                },
                                {
                                    "if": {"filter_query": "{ptf_w} = 0"},
                                    "backgroundColor": "rgba(156, 163, 175, 0.14)",
                                },
                            ],
                        ),
                    ),
                    style={"overflowX": "auto", "maxHeight": "520px", "overflowY": "auto"},
                ),
            ),
            dmc.Space(h=16),
            dmc.Grid(
                gutter="md",
                children=[
                    dmc.GridCol(
                        span={"base": 12, "lg": 9},
                        children=html.Div(id="ind-desc-wrap"),
                    ),
                    dmc.GridCol(
                        span={"base": 12, "lg": 3},
                        children=html.Div(id="ind-news-wrap"),
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
                            id="ind-graph-factors",
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
                        dmc.Text(id="ind-metric-title", children="Autre indicateur (cliquer une cellule hors facteurs)"),
                        dcc.Graph(
                            id="ind-graph-metric",
                            config={"displaylogo": False},
                            style={"height": "400px"},
                        ),
                    ],
                ),
            ),
        ],
    )
