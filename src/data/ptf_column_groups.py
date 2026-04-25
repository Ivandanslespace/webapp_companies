"""Groupes d'affichage PTF : libellé UI -> nom de colonne CIQ (screen_aggregateCIQ)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

# Les 7 « facteurs » (Scores) : 7 sous-graphiques par défaut, exclus du clic « autre metric »
FACTOR_SCORE_COLUMNS: frozenset[str] = frozenset(
    {
        "Multi Avg Percentile",
        "Score ML",
        "MOM Score",
        "LowVol Avg Percentile",
        "Growth Avg Percentile",
        "Dividend Avg Percentile",
        "Quality Avg Percentile",
    }
)

# Colonnes jamais interprétées comme métrique cliquable
METADATA_DATA_TABLE_IDS: frozenset[str] = frozenset(
    {"ptf_w", "isin", "name", "n"}
)


@dataclass(frozen=True)
class ColumnGroup:
    """Un groupe d'en-têtes (Summary, Market, …)."""

    id: str
    label: str
    # (libellé affiché, nom colonne CIQ) — exclut le poids bench, injecté à part
    entries: tuple[tuple[str, str], ...]


# Valeurs cibles (noms tels que dans le parquet CIQ). Vérifiées à l'exécution.
_RAW_GROUPS: tuple[ColumnGroup, ...] = (
    ColumnGroup(
        "summary",
        "Summary",
        (
            ("ESG E", "ESG_E"),
            ("ESG S", "ESG_S"),
            ("ESG G", "ESG_G"),
            ("ESG analyst", "ESG_ANALYST_SCORE"),
            ("Carbon intensity (sales)", "CarbonIntensity_Sales"),
            ("MarketV EUR", "Benchmark Market Value Millions in EUR"),
            ("Multi score", "Multi Avg Percentile"),
            ("Score ML", "Score ML"),
        ),
    ),
    ColumnGroup(
        "market",
        "Market",
        (
            ("Mom score", "MOM Score"),
            ("LowVol score", "LowVol Avg Percentile"),
            ("Perf5D", "Perf5D"),
            ("Perf1M", "Perf1M"),
            ("Perf3M", "Perf3M"),
            ("Perf6M", "Perf6M"),
            ("Daily Vol 60J", "Daily Vol 60J"),
            ("PMOM 12M1M", "PMOM 12M1M"),
            ("EPS NTM 3M Growth", "EPS NTM 3M Growth"),
            ("EPS Revision Ratio", "EPS Revision Ratio"),
            ("SP Price Target CIQ", "SP Price Target CIQ"),
            ("SP Price Close CIQ", "SP Price Close CIQ"),
            ("Pct_Short_Interest", "Pct_Short_Interest"),
        ),
    ),
    ColumnGroup(
        "growth",
        "Growth",
        (
            ("Growth score", "Growth Avg Percentile"),
            ("Sales Growth FY1", "Sales Growth FY1"),
            ("Gross Income Growth FY1", "Gross Income Growth FY1"),
            ("EPS Growth FY1", "EPS Growth FY1"),
            ("SP Est 5Y EPS Gr CIQ", "SP Est 5Y EPS Gr CIQ"),
            ("Revenue 5Y CAGR", "Revenue 5Y CAGR"),
            ("Gross Profit 5Y CAGR", "Gross Profit 5Y CAGR"),
            ("Ebitda 5Y CAGR", "Ebitda 5Y CAGR"),
            ("Ebit 5Y CAGR", "Ebit 5Y CAGR"),
            ("CFO 5Y CAGR", "CFO 5Y CAGR"),
            ("Const Earning 5Y CAGR", "Const Earning 5Y CAGR"),
        ),
    ),
    ColumnGroup(
        "valorisation",
        "Valorisation",
        (
            ("Value score", "Value Avg Percentile"),
            ("PE LTM", "PE LTM"),
            ("PE FY1", "PE FY1"),
            ("PB LTM", "PB LTM"),
            ("Price to Book FY1", "Price to Book FY1"),
            ("PFCF LTM", "PFCF LTM"),
            ("Price to FreeCF FY1", "Price to FreeCF FY1"),
            ("EV To EBITDA LTM", "EV To EBITDA LTM"),
            ("EV To EBITDA FY1", "EV To EBITDA FY1"),
            ("EV to Ebit FY1", "EV to Ebit FY1"),
            ("EV to Sales FY1", "EV to Sales FY1"),
            ("Price Cont Op Earning", "Price Cont Op Earning"),
            ("P to CFO", "P to CFO"),
        ),
    ),
    ColumnGroup(
        "quali",
        "Quali",
        (
            ("Dividend score", "Dividend Avg Percentile"),
            ("Quality score", "Quality Avg Percentile"),
            ("Gross Margin", "Gross Margin"),
            ("Ebitda Margin", "Ebitda Margin"),
            ("EBITDAm FY1", "EBITDAm FY1"),
            ("Cont Op Earning Margin", "Cont Op Earning Margin"),
            ("Oper Margin", "Oper Margin"),
            ("ROE avg FY0", "ROE avg FY0"),
            ("Asset TO exFIN", "Asset TO exFIN"),
            ("FCF Conversion", "FCF Conversion"),
            ("NetDebt to EBITDA exFIN", "NetDebt to EBITDA exFIN"),
            ("netD to EBITDA FY1", "netD to EBITDA FY1"),
            ("Net Debt to Ebit", "Net Debt to Ebit"),
            ("Net Debt to Tot Equity", "Net Debt to Tot Equity"),
            ("Net Debt to Market Cap", "Net Debt to Market Cap"),
            ("Current Ratio", "Current Ratio"),
        ),
    ),
)


def filter_groups_for_ciq(available: Iterable[str]) -> list[ColumnGroup]:
    """Ne garde que les entrées dont la colonne CIQ existe."""
    have = set(available)
    out: list[ColumnGroup] = []
    for g in _RAW_GROUPS:
        ent = tuple((lab, c) for lab, c in g.entries if c in have)
        if ent:
            out.append(
                ColumnGroup(
                    id=g.id,
                    label=g.label,
                    entries=ent,
                )
            )
    return out


def default_summary_column_names(available: set[str], bench_col: str) -> list[str]:
    """Colonnes par défaut : poids bench + colonnes du groupe Summary présentes dans ``available``."""
    cols: list[str] = []
    if bench_col in available:
        cols.append(bench_col)
    g = next((x for x in _RAW_GROUPS if x.id == "summary"), None)
    if g:
        for _lab, c in g.entries:
            if c in available and c not in cols:
                cols.append(c)
    return cols


def ciq_name_for_display_label(available: set[str], display: str) -> Optional[str]:
    for g in _RAW_GROUPS:
        for lab, c in g.entries:
            if lab == display and c in available:
                return c
    return None
