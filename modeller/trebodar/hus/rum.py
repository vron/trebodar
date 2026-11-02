"""Rummen som påverkar byggdelarna, i plan (K-05:s koordinater): badrummet, där väggarna har våtrumsskikt.

Badrummet enligt planritning 201 rev 02 med modellens väggar: från gaveln 1NO och långsidan 1SO till de bärande
väggarna 1A, 1B och 1C och de lätta väggarna i x 2 560 och 3 310 (konturen i väggarnas mitt).
"""
from __future__ import annotations

from shapely.geometry import Point, Polygon

BADRUM = Polygon([(65.0, 3655.0), (2560.0, 3655.0), (2560.0, 5230.0), (3310.0, 5230.0), (3310.0, 8220.0),
                  (2095.0, 8220.0), (2095.0, 7150.0), (65.0, 7150.0)])


# kaminens kåpa på sovrumssidan av 2C (planritning 201): skikten mot den är kalciumsilikat 50 mm, så att kåpan med
# fronten i öppningen är Rais innbyggingskasse (min. 920 × 498 × 1600 mot brännbar vägg); 220 mm bredare mot väster
# än planritningen, för förbränningsluftens kanal bredvid insatsen och skorstenen (kamin.py)
KAMINKAPA = Polygon([(6138.0, 5522.0), (7278.0, 5522.0), (7278.0, 5900.0), (6138.0, 5900.0)])


def i_badrum(x: float, y: float) -> bool:
    return BADRUM.contains(Point(x, y))
