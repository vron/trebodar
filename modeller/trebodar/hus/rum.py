"""Rummen och ytorna som påverkar byggdelarna, i plan (K-05:s koordinater): badrummet, där väggarna har
våtrumsskikt, och kaminens murade skorsten i allrummet (#102), där golvvärmen inte ligger.

Badrummet enligt planritning 201 rev 02 med modellens väggar: från gaveln 1NO och långsidan 1SO till de bärande
väggarna 1A, 1B och 1C och de lätta väggarna i x 2 560 och 3 310 (konturen i väggarnas mitt).
"""
from __future__ import annotations

from shapely.geometry import Polygon

BADRUM = Polygon([(65.0, 3655.0), (2560.0, 3655.0), (2560.0, 5230.0), (3310.0, 5230.0), (3310.0, 8220.0),
                  (2095.0, 8220.0), (2095.0, 7150.0), (65.0, 7150.0)])


# kaminens murade skorsten (hus/kamin/kamin.py, #102, #109): mot 2C:s yta mot allrummet (y 6 020), 684 bred som insatsen
# Rais 600:3 och 700 djup, mitt under nocken (x 6 905)
KAMINMUR = Polygon([(6563.0, 6020.0), (7247.0, 6020.0), (7247.0, 6720.0), (6563.0, 6720.0)])
