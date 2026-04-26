"""Global application settings.

Centralized configuration: data paths, pagination, UI defaults.
Change values here to tune the app without touching UI or data code.
"""
from __future__ import annotations

from pathlib import Path

# --- Paths ---
ROOT_DIR: Path = Path(__file__).resolve().parent.parent
DATA_DIR: Path = ROOT_DIR / "data"

DES_PARQUET: Path = DATA_DIR / "last_DES.parquet"
NEWS_PARQUET: Path = DATA_DIR / "Last_NEWS_3months.parquet"
SCREEN_AGG_CIQ_PARQUET: Path = DATA_DIR / "screen_aggregateCIQ.parquet"
ICB_MAPPING_CSV: Path = DATA_DIR / "ICB_mapping.csv"
PTF_PARQUET: Path = DATA_DIR / "ptf.parquet"

# --- UI ---
APP_TITLE: str = "Panorama des Entreprises"
APP_SUBTITLE: str = "Descriptions & Actualités financières"

# Card grid pagination on the home page
CARDS_PER_PAGE: int = 24

# Max characters displayed in the card summary snippet
CARD_SUMMARY_CHARS: int = 180

# --- Server ---
HOST: str = "127.0.0.1"
PORT: int = 8050
DEBUG: bool = True

# --- Page PTF / indice（业务人员主要改此处；列名需与 screen_aggregateCIQ 一致）---

# Benchmark 选择器默认项；None 时取 list_indices 第一个
DEFAULT_BENCHMARK: str | None = "Weight in MSCI WORLD"

# 默认日期：取该 bench 下日期列表的最后一个或第一个
PTF_DEFAULT_DATE_MODE: str = "latest"  # "latest" | "first"

# 主表 DataTable 每页行数
PTF_TABLE_PAGE_SIZE: int = 25

# 因子历史图：每项 (显示名, CIQ 列名)；顺序=图中 trace 顺序
FACTOR_TRACES: tuple[tuple[str, str], ...] = (
    ("Quality", "Quality Avg Percentile"),
    ("Growth", "Growth Avg Percentile"),
    ("Lowvol", "LowVol Avg Percentile"),
    ("Momentum", "MOM Score"),
    ("Value", "Dividend Avg Percentile"),
    ("ML", "Score ML"),
)

# MultiFactor 合成分数参与均值的列（与 FACTOR_TRACES 中 ML 开关独立时可在此增删 Score ML）
MULTIFACTOR_BASE_COLUMNS: tuple[str, ...] = (
    "Quality Avg Percentile",
    "Growth Avg Percentile",
    "LowVol Avg Percentile",
    "MOM Score",
    "Dividend Avg Percentile",
)

# 全站「因子列」判定（点击/排除逻辑）；与图中去掉 ML 时须同步去掉 "Score ML"
FACTOR_SCORE_COLUMNS_CONFIG: tuple[str, ...] = (
    "Multi Avg Percentile",
    "Score ML",
    "MOM Score",
    "LowVol Avg Percentile",
    "Growth Avg Percentile",
    "Dividend Avg Percentile",
    "Quality Avg Percentile",
)

# 主表 ptf-cols 默认选中的指标列（CIQ 名）；空元组 = 用 summary 组全选 + bench
PTF_DEFAULT_VISIBLE_COLUMNS: tuple[str, ...] = ()

# 竞争对手指标分组：id/label/entries（(显示名, 列名)）
PTF_METRIC_GROUPS: tuple[dict, ...] = (
    {
        "id": "summary",
        "label": "Summary",
        "entries": (
            ("ESG E", "ESG_E"),
            ("ESG S", "ESG_S"),
            ("ESG G", "ESG_G"),
            ("ESG analyst", "ESG_ANALYST_SCORE"),
            ("Carbon intensity (sales)", "CarbonIntensity_Sales"),
            ("MarketV EUR", "Benchmark Market Value Millions in EUR"),
            ("Multi score", "Multi Avg Percentile"),
            ("Score ML", "Score ML"),
        ),
    },
    {
        "id": "market",
        "label": "Market",
        "entries": (
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
    },
    {
        "id": "growth",
        "label": "Growth",
        "entries": (
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
    },
    {
        "id": "valorisation",
        "label": "Valorisation",
        "entries": (
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
    },
    {
        "id": "quali",
        "label": "Quali",
        "entries": (
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
    },
)
