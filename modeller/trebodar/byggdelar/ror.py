"""Raka rör och stänger mellan två punkter (rökrör, stuprör, hål för kanaler)."""
from __future__ import annotations

import math
from collections.abc import Sequence

from modellering import Form, Placering, cylinder


def _langs(a: Sequence[float], b: Sequence[float]) -> tuple[float, Placering]:
    """Längden a–b och systemet med z längs a–b. Placering.axlar behåller x och gör z vinkelrät mot den, så x tas
    vinkelrät mot axeln först."""
    v = [b[i] - a[i] for i in range(3)]
    langd = math.sqrt(sum(c * c for c in v))
    e = [c / langd for c in v]
    ref = (1.0, 0.0, 0.0) if abs(e[0]) < 0.9 else (0.0, 1.0, 0.0)
    s = sum(ref[i] * e[i] for i in range(3))
    x = tuple(ref[i] - s * e[i] for i in range(3))
    return langd, Placering.axlar(tuple(a), x, v)


def ror(a: Sequence[float], b: Sequence[float], d: float, t: float) -> Form:
    """Rör med ytterdiametern d och godset t från a till b."""
    langd, pl = _langs(a, b)
    return (cylinder(d / 2, langd) - cylinder(d / 2 - t, langd)).placerad(pl)


def stang(a: Sequence[float], b: Sequence[float], d: float) -> Form:
    """Massiv stång (eller hål) med diametern d från a till b."""
    langd, pl = _langs(a, b)
    return cylinder(d / 2, langd).placerad(pl)
