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
            dcc.Store(id="ind-drawer-open", data=False),
            dcc.Store(id="ind-drawer-tab", data="description"),
            dcc.Store(id="ind-drawer-scroll-helper", data=0),
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
            html.Div(
                id="ind-drawer-overlay",
                className="drawer-overlay",
                children=[
                    html.Button(
                        id="ind-drawer-backdrop",
                        className="drawer-backdrop",
                        n_clicks=0,
                        type="button",
                        title="Fermer",
                        **{"aria-label": "Fermer le panneau"},
                    ),
                    html.Div(
                        className="drawer-panel",
                        children=[
                            html.Div(
                                className="drawer-panel-header",
                                children=[
                                    html.Div(
                                        id="ind-drawer-header",
                                        style={"flex": 1, "minWidth": 0},
                                    ),
                                    html.Button(
                                        "×",
                                        id="ind-drawer-close",
                                        className="drawer-close",
                                        n_clicks=0,
                                        type="button",
                                        title="Fermer",
                                        **{"aria-label": "Fermer"},
                                    ),
                                ],
                            ),
                            html.Div(
                                className="drawer-seg-wrap",
                                children=dmc.SegmentedControl(
                                    id="ind-drawer-seg",
                                    value="description",
                                    data=[
                                        {"label": "Description", "value": "description"},
                                        {"label": "Graphe industrie", "value": "industry"},
                                        {"label": "Indicateurs détaillés", "value": "indicators"},
                                    ],
                                    fullWidth=True,
                                ),
                            ),
                            html.Div(
                                className="drawer-panel-body",
                                children=[
                                    html.Div(
                                        id="ind-panel-description",
                                        className="drawer-tab-panel drawer-tab-panel--active",
                                        children=[
                                            dcc.Loading(
                                                type="circle",
                                                delay_show=200,
                                                color="#1E40AF",
                                                children=html.Div(id="ind-desc-wrap"),
                                            ),
                                            dmc.Space(h=12),
                                            dcc.Loading(
                                                type="circle",
                                                delay_show=200,
                                                color="#1E40AF",
                                                children=html.Div(id="ind-news-wrap"),
                                            ),
                                        ],
                                    ),
                                    html.Div(
                                        id="ind-panel-industry",
                                        className="drawer-tab-panel",
                                        children=[
                                            dmc.Text(
                                                "Scores (facteurs) — historique vs pairs bench",
                                                size="sm",
                                                fw=600,
                                            ),
                                            dmc.Space(h=8),
                                            dcc.Loading(
                                                type="circle",
                                                delay_show=200,
                                                color="#1E40AF",
                                                children=dcc.Graph(
                                                    id="ind-graph-factors",
                                                    config={"displaylogo": False},
                                                    style={"minHeight": "400px"},
                                                ),
                                            ),
                                        ],
                                    ),
                                    html.Div(
                                        id="ind-panel-indicators",
                                        className="drawer-tab-panel",
                                        children=[
                                            dcc.Loading(
                                                type="circle",
                                                delay_show=200,
                                                color="#1E40AF",
                                                children=dmc.Stack(
                                                    gap="sm",
                                                    children=[
                                                        dmc.Text(
                                                            id="ind-metric-title",
                                                            children="Autre indicateur (cliquer une cellule hors facteurs)",
                                                        ),
                                                        dcc.Graph(
                                                            id="ind-graph-metric",
                                                            config={"displaylogo": False},
                                                            style={"height": "400px"},
                                                        ),
                                                    ],
                                                ),
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(
                id="ind-drawer-fab-wrap",
                className="drawer-fab-wrap",
                style={"display": "none"},
                children=[
                    dmc.Button(
                        "Voir la fiche",
                        id="ind-drawer-reopen",
                        variant="filled",
                        size="sm",
                    ),
                ],
            ),
        ],
    )
