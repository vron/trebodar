"""Stålband för stabiliseringen (K-04): diagonala band 40×2,0 mm S350GD+Z275 i kryss, infällda i virkets yta (ett
urfräst spår, så att skivorna ligger plant) och spikade i varje del de korsar: i väggarnas fält från syllen till
hammarbandet och i takfallen på takbalkarnas överkant från takfoten eller dalbalken till nockbalken.

Ett band är en rak del från punkt till punkt längs bandets mittlinje i ytan, med tjockleken in i virket från ytan.
"""
from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from modellering import Del, Placering, lada

from ..material import STALBAND
from .virke import del_, fmt

B, T = 40.0, 2.0                 # bandets bredd och tjocklek


def band(p0: Sequence[float] | np.ndarray, p1: Sequence[float] | np.ndarray,
         inat: Sequence[float] | np.ndarray) -> tuple[Del, Placering]:
    """Band med mittlinjen från p0 till p1 i ytan och tjockleken från ytan längs `inat` (in i virket)."""
    a, b = np.asarray(p0, dtype=float), np.asarray(p1, dtype=float)
    L = float(np.linalg.norm(b - a))
    ex = (b - a) / L
    ez = np.asarray(inat, dtype=float)
    ez = ez - (ez @ ex) * ex
    ez = ez / np.linalg.norm(ez)
    ey = np.cross(ez, ex)
    d = del_(f"Stålband {fmt(B)}×{fmt(T)} L={fmt(L)}", lada(L, B, T), STALBAND)
    return d, Placering.axlar(tuple(a - ey * B / 2), tuple(ex), tuple(ez))
