"""Global application shell: navbar + page container."""
from __future__ import annotations

import dash
import dash_mantine_components as dmc
from dash import dcc, html

from src.ui.components.navbar import render_navbar


def build_layout() -> dmc.MantineProvider:
    """Return the root layout wrapped in MantineProvider (light scheme)."""
    from src.ui.theme import MANTINE_THEME

    return dmc.MantineProvider(
        theme=MANTINE_THEME,
        forceColorScheme="light",
        children=html.Div(
            className="app-root",
            children=[
                dcc.Location(id="_url", refresh=False),
                dcc.Store(id="_scroll_reset_sink", data=0),
                render_navbar(),
                html.Main(
                    dash.page_container,
                    className="app-main",
                ),
            ],
        ),
    )
