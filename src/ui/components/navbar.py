"""导航已迁移至 app_header（AppShell 顶栏）。保留此模块名仅避免误用旧路径。"""
from __future__ import annotations

from src.ui.components.app_header import build_app_header_content

__all__ = ["build_app_header_content"]
