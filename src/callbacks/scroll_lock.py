"""换页时恢复 document.body 滚动，避免抽屉关闭/离页后仍被 overflow:hidden 锁住。"""
from __future__ import annotations

from dash import Input, Output, clientside_callback

clientside_callback(
    """
    function(_pathname) {
        document.body.style.overflow = '';
        return 0;
    }
    """,
    Output("_scroll_reset_sink", "data"),
    Input("_url", "pathname"),
)
