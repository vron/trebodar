"""Golvstosarna i källaren: rören upp genom bottenplattan strax innanför väggen, mellan plattans armeringsjärn."""
from __future__ import annotations

from trebodar.hus.grund.grund import H_PLATTA

from ...montering import PLAN, Montering, Vek, golv
from ...strak import mellan_jarnen
from ..typer import Dosatyp

R = 12.5                                # skyddsrörets radie (rör-i-rör 16/25)


def stos(x: float, y: float, dosa: Dosatyp, kallt: Vek | None = None,
         langs: tuple[float, float] | None = (0.0, 1.0)) -> Montering:
    """Stosens mitt på källarens golv nära (x, y), flyttad längs väggen (langs; None: åt alla håll) så lite som behövs
    för att rören (kallt och varmt cc isär längs kallt, standard x) går fria mellan bottenplattans järn."""
    k = kallt or (1.0, 0.0, 0.0)
    h = dosa.cc / 2
    pts = [(x + k[0] * h, y + k[1] * h), (x - k[0] * h, y - k[1] * h)] if dosa.cc else [(x, y)]
    dx, dy = mellan_jarnen(pts, PLAN[0] - H_PLATTA, PLAN[0], R, langs=langs)
    return golv(x + dx, y + dy, plan=0)
