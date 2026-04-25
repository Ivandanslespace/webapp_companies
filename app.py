"""Dash application factory and local development entry point."""
from __future__ import annotations

import dash

from config import settings
from src.ui.layout import build_layout


def create_app() -> dash.Dash:
    """Build and configure the Dash application."""
    app = dash.Dash(
        __name__,
        use_pages=True,
        pages_folder="src/ui/pages",
        assets_folder="src/assets",
        title=settings.APP_TITLE,
        update_title=None,
        suppress_callback_exceptions=True,
    )
    app.layout = build_layout()

    # Import callback modules for their registration side effects.
    # Placed here (after app/layout) so pages can reference component ids.
    import src.callbacks  # noqa: F401

    return app


app = create_app()
server = app.server  # Exposed for WSGI servers

if __name__ == "__main__":
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
