"""Rummen och ytorna som påverkar byggdelarna, i plan (K-05:s koordinater): badrummet, där väggarna har
våtrumsskikt, och kaminens murade skorsten i allrummets hörn, där golvvärmen inte ligger.

Badrummet enligt planritning 201 rev 02 med modellens väggar: från gaveln 1NO och långsidan 1SO till de bärande
väggarna 1A, 1B och 1C och de lätta väggarna i x 2 560 och 3 310 (konturen i väggarnas mitt).
"""
from __future__ import annotations

import os

from shapely.geometry import Polygon
from shapely.geometry import box as plan_box

BADRUM = Polygon([(65.0, 3655.0), (2560.0, 3655.0), (2560.0, 5230.0), (3310.0, 5230.0), (3310.0, 8220.0),
                  (2095.0, 8220.0), (2095.0, 7150.0), (65.0, 7150.0)])


# kaminens murade skorsten (hus/kamin/kamin.py): i allrummets hörn mellan väggarna 2C och 2B, mot väggarnas gips
# (KAMIN_HORN), från golvet till innertaket. Två lägen att jämföra, valda med miljövariabeln TREBODAR_KAMIN:
# A (förvalt) med baksidan mot 2C och fronten mot rummet, B med baksidan mot 2B och fronten längs 2C.
# KAMIN_MATT: bredden längs baksidans vägg (insatsens ram och avståndet till sidoväggen) och djupet från den
KAMIN_LAGE = os.environ.get("TREBODAR_KAMIN", "A").upper()
assert KAMIN_LAGE in ("A", "B"), "TREBODAR_KAMIN är A eller B"
KAMIN_HORN = (9345.0, 6020.0)
KAMIN_MATT = ({"A": 1055.0, "B": 1115.0}[KAMIN_LAGE], 502.0)


def kamin_plan(p0: float, p1: float, q0: float, q1: float) -> tuple[float, float, float, float]:
    """Rutan p0–p1 (från sidoväggen, längs baksidans vägg) och q0–q1 (från baksidans vägg) i plan: x0, y0, x1, y1."""
    cx, cy = KAMIN_HORN
    if KAMIN_LAGE == "A":
        return cx - p1, cy + q0, cx - p0, cy + q1
    return cx - q1, cy + p0, cx - q0, cy + p1


KAMINMUR = plan_box(*kamin_plan(0.0, KAMIN_MATT[0], 0.0, KAMIN_MATT[1]))
