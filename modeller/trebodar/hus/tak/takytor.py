"""Takets plan: takfallens regioner (y-intervall med samma nedre kant och nock) och takytan, för taket, takkanterna,
stommen, fasaden och de invändiga skikten.

En region går från den nedre kanten (takbalkarnas ände vid takfoten eller dallinjen) upp till nocken. Vid dalarnas
ändar går den längre kroppens dalregion gavelutsticket ut förbi den kortare kroppens gavel (ande), så att takfoten och
rännan slutar där och dalens ändlåda (dalar.py) får plats under den kortare kroppens utstick.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from trebodar import skelett as S
from trebodar.byggdelar import taklager as L
from trebodar.hus.stomme.prefab.takbalkar.takbalkar import FALT


@dataclass(frozen=True)
class Region:
    y0: float
    y1: float
    nedre: L.Kant                    # takfot eller dal
    nock: L.Kant
    ande: bool = False               # vid dalens ände: under grannkroppens gavelutstick, där ändlådan sitter


def _f(kropp: int) -> tuple[float, float]:
    k = S.HUSKROPPAR[kropp]
    return k.y0 - S.STOMME_UT - S.T_FASAD, k.y1 + S.STOMME_UT + S.T_FASAD


def _lodr(x: float) -> L.Kant:
    return L.Kant("lodratt", x)


Y1, Y2, Y3 = _f(1), _f(2), _f(3)
DB4, DB2 = S.BALKAR["DB4"].x, S.BALKAR["DB2"].x
NOCK = {k: S.HUSKROPPAR[k].nock for k in (1, 2, 3)}
G = L.GAVEL_UT


def _takfall(kod: str, *delar: tuple[float, float, float, bool]) -> list[Region]:
    """Takfallets regioner (y0, y1, nedre kant, vid dalens ände) upp till nocken."""
    return [Region(y0, y1, _lodr(x), _lodr(NOCK[S.TAKFALL[kod].kropp]), ande) for y0, y1, x, ande in delar]


# Vid dalarnas ändar går den längre kroppens dalregion gavelutsticket ut förbi den kortare kroppens gavel (ande), så
# att takfoten och rännan slutar där och dalens ändlåda (dalar.py) får plats under den kortare kroppens utstick.
REGIONER = {
    "1SO": _takfall("1SO", (Y1[0], Y1[1], FALT["1SO"].takfot, False)),
    "1NV": _takfall("1NV", (Y1[0], Y2[1], DB4, False), (Y2[1], Y2[1] + G, DB4, True),
                    (Y2[1] + G, Y1[1], FALT["1NV"].takfot, False)),
    "2SO": _takfall("2SO", (Y2[0], Y1[0] - G, FALT["2SO"].takfot, False), (Y1[0] - G, Y1[0], DB4, True),
                    (Y1[0], Y2[1], DB4, False)),
    "2NV": _takfall("2NV", (Y2[0], Y3[0] - G, FALT["2NV"].takfot, False), (Y3[0] - G, Y3[0], DB2, True),
                    (Y3[0], Y2[1], DB2, False)),
    "3SO": _takfall("3SO", (Y3[0], Y2[1], DB2, False), (Y2[1], Y2[1] + G, DB2, True),
                    (Y2[1] + G, Y3[1], FALT["3SO"].takfot, False)),
    "3NV": _takfall("3NV", (Y3[0], Y3[1], FALT["3NV"].takfot, False)),
}


def tak_underkant(x: float, y: float) -> float | None:
    """Takets hårdboards undersida (takbalkarnas överkant) i punkten (x, y), om taket täcker den."""
    z = []
    for kod, rs in REGIONER.items():
        t = S.TAKFALL[kod]
        for r in rs:
            xa, xb = sorted((r.nedre.x, r.nock.x))
            if r.y0 - 1e-6 <= y <= r.y1 + 1e-6 and xa - 1e-6 <= x <= xb + 1e-6:
                z.append(t.z_overkant(x))
    return min(z) if z else None





def kant_takfot(kod: str) -> float:
    """Råspontens, pappens och plåtens kant vid takfoten (x): RASPONT_UT utanför takbalkarnas ände."""
    return FALT[kod].takfot - S.TAKFALL[kod].riktning * L.RASPONT_UT


def _dalens_slut(x_dal: float, kropp: int) -> float:
    """Där en dal slutar mot kroppens gavel slutar utsticket över gaveln vid dalens ändlåda (dalar.py)."""
    return x_dal + math.copysign(L.DALANDE_B, S.HUSKROPPAR[kropp].nock - x_dal)


def regioner(kod: str, typ: str) -> list[Region]:
    """Skiktets regioner. Vid takfoten slutar hårdboarden i ytterväggens liv (isolerstoppet) och råsponten, pappen
    och plåten RASPONT_UT utanför takbalkarnas ände. Vid gavlarna går råsponten, pappen och plåten ut till vindskivan
    (GAVEL_UT); där en dal slutar mot en gavel slutar utsticket vid dalens ändlåda. Vid dalens ände (ande) slutar
    hårdboarden i väggens liv som vid takfoten och de andra skikten i dallinjen, mot ändlådan."""
    t, f = S.TAKFALL[kod], FALT[kod]
    tackning = typ in ("RP", "UP", "TP")
    x = t.x_utsida if typ == "HD" else kant_takfot(kod) if tackning else f.takfot
    # i dalarna slutar pappen och plåten vid rändalen (dalar.py)
    xd = t.riktning * L.RANDAL_B if typ in ("UP", "TP") else 0.0
    rs = [Region(r.y0, r.y1, _lodr(x), r.nock) if r.nedre.x == f.takfot else
          Region(r.y0, r.y1, _lodr(t.x_utsida if typ == "HD" else r.nedre.x), r.nock, True) if r.ande else
          Region(r.y0, r.y1, _lodr(r.nedre.x + xd), r.nock) for r in REGIONER[kod]]
    if not tackning:
        return rs
    g = L.GAVEL_UT - L.VINDSKIVA[0]
    y0, y1 = min(r.y0 for r in rs), max(r.y1 for r in rs)
    ut = list(rs)
    for r in rs:
        for kant, (a, b) in ((r.y0, (r.y0 - g, r.y0)), (r.y1, (r.y1, r.y1 + g))):
            if kant in (y0, y1):
                nedre = r.nedre if r.nedre.x == x else _lodr(_dalens_slut(r.nedre.x - xd, t.kropp))
                ut.append(Region(a, b, nedre, r.nock))
    return ut
