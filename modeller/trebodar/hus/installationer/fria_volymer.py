"""Volymerna som installationernas rör, kablar och kanaler inte får gå in i (kontrollregler.FRIA_VOLYMER; prövas av
./mod kontroll och ./mod vagar, verktyg/modellering/modellering/vagar.py, ärende #34): fickdörrarnas fickor, där bladet
går in när dörren öppnas, i väggens stomme mellan skivorna, från golvet till skenan ovanför bladet."""
from __future__ import annotations

from trebodar.hus.fonster_och_dorrar.oppningar import INNERDORRAR

from .montering import PLAN, vaggdef

SKENA = 100.0                                   # skenan och upphängningen ovanför bladet


def fria_volymer() -> list[tuple[str, list[tuple[float, float]], float, float]]:
    """(namn, ytan i plan (x, y), z0, z1) per volym."""
    ut = []
    for d in INNERDORRAR:
        if not d.ficka:
            continue
        v = vaggdef(d.vagg)
        u0, u1 = d.fickan
        horn = ((u0, 0.0), (u1, 0.0), (u1, v.tjocklek), (u0, v.tjocklek))
        yta = [(v.origo[0] + v.u[0] * u + v.w[0] * w, v.origo[1] + v.u[1] * u + v.w[1] * w) for u, w in horn]
        ut.append((f"fickan till {d.kod} i {d.vagg}", yta, PLAN[1], PLAN[1] + d.hojd + SKENA))
    return ut
