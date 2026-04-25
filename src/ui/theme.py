"""Centralized design tokens: colors, typography, radius.

Single source of truth for the look & feel. Change here to re-skin the app.
"""
from __future__ import annotations

# --- Palette (light scheme) ---
COLOR_BG: str = "#FAFAFA"
COLOR_SURFACE: str = "#FFFFFF"
COLOR_PRIMARY: str = "#1E40AF"      # Deep blue — financial tone
COLOR_ACCENT: str = "#0F766E"       # Teal — positive accents
COLOR_TEXT: str = "#111827"
COLOR_TEXT_MUTED: str = "#6B7280"
COLOR_BORDER: str = "#E5E7EB"

# --- Radius & spacing ---
RADIUS_MD: str = "10px"
RADIUS_LG: str = "14px"

# --- Typography ---
FONT_FAMILY: str = (
    "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, "
    "'Helvetica Neue', Arial, sans-serif"
)

# --- Mantine theme dict consumed by MantineProvider ---
MANTINE_THEME: dict = {
    "fontFamily": FONT_FAMILY,
    "primaryColor": "blue",
    "defaultRadius": "md",
    "white": COLOR_SURFACE,
    "black": COLOR_TEXT,
    "headings": {
        "fontFamily": FONT_FAMILY,
        "fontWeight": "600",
    },
}
