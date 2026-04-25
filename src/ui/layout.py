"""应用外壳：MantineProvider + AppShell（固定顶栏 + 主内容 + 移动抽屉）。"""
from __future__ import annotations

import dash
import dash_mantine_components as dmc
from dash import dcc, html

from src.ui.components.app_header import build_app_header_content
from src.ui.theme import MANTINE_THEME


def build_layout() -> dmc.MantineProvider:
    """根布局，包裹 MantineProvider（浅色主题）。"""
    header, mobile_drawer = build_app_header_content()
    return dmc.MantineProvider(
        theme=MANTINE_THEME,
        forceColorScheme="light",
        children=html.Div(
            className="app-root",
            children=[
                dcc.Location(id="_url", refresh=False),
                dcc.Store(id="_scroll_reset_sink", data=0),
                dcc.Store(id="app-nav-open-store", data=False),
                dcc.Store(id="app-nav-anim", data=0),
                dmc.AppShell(
                    header={"height": 80, "offset": False},
                    padding=0,
                    withBorder=True,
                    transitionDuration=220,
                    transitionTimingFunction="cubic-bezier(0.16, 1, 0.3, 1)",
                    zIndex=300,
                    className="app-shell-root",
                    children=[
                        header,
                        dmc.AppShellMain(
                            p=0,
                            className="app-shell-main-outer",
                            children=html.Div(
                                id="app-page-wrap",
                                className="app-main app-page-wrap app-page-flip-0",
                                children=[dash.page_container],
                            ),
                        ),
                    ],
                ),
                mobile_drawer,
            ],
        ),
    )
