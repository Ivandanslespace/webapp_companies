"""Top navigation bar shown on every page."""
from __future__ import annotations

import dash_mantine_components as dmc
from dash import html
from dash_iconify import DashIconify

from config import settings


def render_navbar() -> html.Div:
    return html.Div(
        className="app-navbar",
        children=dmc.Group(
            justify="space-between",
            align="center",
            children=[
                dmc.Anchor(
                    href="/",
                    underline=False,
                    children=dmc.Group(
                        gap="sm",
                        align="center",
                        children=[
                            DashIconify(
                                icon="mdi:chart-bubble",
                                width=26,
                                color="#1E40AF",
                            ),
                            dmc.Stack(
                                gap=0,
                                children=[
                                    dmc.Text(
                                        settings.APP_TITLE,
                                        fw=700,
                                        size="lg",
                                        c="#111827",
                                    ),
                                    dmc.Text(
                                        settings.APP_SUBTITLE,
                                        size="xs",
                                        c="#6B7280",
                                    ),
                                ],
                            ),
                        ],
                    ),
                ),
                dmc.Group(
                    gap="lg",
                    children=[
                        dmc.Anchor(
                            "Entreprises",
                            href="/",
                            size="sm",
                            c="#111827",
                            underline=False,
                        ),
                        dmc.Anchor(
                            "Composition indice",
                            href="/indice",
                            size="sm",
                            c="#111827",
                            underline=False,
                        ),
                        dmc.Anchor(
                            "Analyse sectorielle ICB",
                            href="/analyse-icb",
                            size="sm",
                            c="#111827",
                            underline=False,
                        ),
                    ],
                ),
            ],
        ),
    )
