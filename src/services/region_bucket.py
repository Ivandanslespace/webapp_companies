"""Regroupement des régions d'échange en 3 seaux (West Europe, North America, Others)."""
from __future__ import annotations

import math

WEST_EUROPE = "west_europe"
NORTH_AMERICA = "north_america"
OTHERS = "others"


def region_bucket_value(region) -> str:
    if region is None or (isinstance(region, float) and math.isnan(region)):
        return OTHERS
    s = str(region).strip().lower()
    if s == "west europe":
        return WEST_EUROPE
    if s == "north america":
        return NORTH_AMERICA
    return OTHERS
