"""Köldbärarledningarna till bergvärmepumpen: två skyddsrör Ø110 från energibrunnen i trädgården in under källaren och
upp genom bottenplattan i teknikrummet, där kollektorslangarna (i skyddsrören) går vidare till värmepumpens anslutningar
(..teknikrum.VARMEPUMP, KB-in och KB-ut). Slangarna dras in genom rören efteråt, så rören har bara böjar om högst 15°
(VINKEL): lodrätt upp genom plattan, en sväng till vågrätt med böjar om 15° under plattans cellplast och makadam,
vågrätt söderut under källarens vänstra del och ut till brunnen, med en sidoförskjutning om 15° utanför huset.

Rören går lodrätt genom plattan mellan armeringsnätens järn (..strak.mellan_jarnen) och golvvärmen håller sig fri från
dem (golvvarme/system.py). Brunnens läge är ungefärligt (användarens markering). Koordinater i mm (K-05), z från plan 1:s
golv (källarens golv z −2 250).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from functools import cache

from shapely.geometry import LineString

from trebodar.hus.grund.grund import H_PLATTA

from ..genomforingar import Genomforing, Stycke, genomforingar
from ..montering import PLAN, Vek
from ..strak import mellan_jarnen

D = 110.0                                   # skyddsrörens ytterdiameter
CC = 140.0                                  # rörens avstånd
VINKEL = 15.0                               # största böj [°]
S_BOJ = 120.0                               # sträckan mellan svängens böjar
Z_GOLV = PLAN[0]
Z_TOPP = Z_GOLV + 100.0                     # rörens ände över golvet i teknikrummet
Z_VAG = Z_GOLV - 650.0                      # rörens mitt under plattan: under cellplasten och makadamen, under
                                            # avloppet och under dräneringen (installationer/dranering) söder om V7
UPP = (3840.0, 8200.0)                      # upp genom plattan (mitt mellan rören), användarens markering
BRUNN = (3500.0, -2000.0)                   # energibrunnen, ungefärligt
Y_SIDA = 1000.0                             # sidoförskjutningen börjar (utanför huset, söder om V7)
RIKTNING = {"KB-in": 1, "KB-ut": -1}        # rören öster och väster om mitten


@dataclass(frozen=True)
class Ledning:
    id: str
    anslutning: str                         # värmepumpens anslutning (TK-VP:KB-in …)
    vag: tuple[Vek, ...]


def _riktningar(n: int) -> list[tuple[float, float, float]]:
    """Riktningarna genom svängen från nedåt till söderut, VINKEL i taget."""
    return [(0.0, -math.sin(math.radians(VINKEL * k)), -math.cos(math.radians(VINKEL * k))) for k in range(n + 1)]


def _vag(x: float, y: float) -> tuple[Vek, ...]:
    """Ett rör från änden över golvet: lodrätt ned, svängen till söderut, söderut till sidoförskjutningen, snett mot
    brunnen (VINKEL) och söderut till den."""
    n = round(90.0 / VINKEL)
    r = _riktningar(n)
    fall = S_BOJ * sum(d[2] for d in r[1:n])                    # svängens fall (negativt)
    p: list[Vek] = [(x, y, Z_TOPP), (x, y, Z_VAG - fall)]
    for d in r[1:n]:
        q = p[-1]
        p.append((q[0], q[1] + S_BOJ * d[1], q[2] + S_BOJ * d[2]))
    dx = BRUNN[0] + (x - UPP[0]) - x
    v = math.radians(VINKEL)
    langd = abs(dx) / math.sin(v)
    p.append((x, Y_SIDA, Z_VAG))
    p.append((x + dx, Y_SIDA - langd * math.cos(v), Z_VAG))
    p.append((x + dx, BRUNN[1], Z_VAG))
    return tuple(p)


@cache
def ledningar() -> dict[str, Ledning]:
    """Rören, upp genom plattan mellan armeringsnätens järn."""
    mitt = mellan_jarnen([(UPP[0] + s * CC / 2, UPP[1]) for s in RIKTNING.values()], Z_GOLV - H_PLATTA, Z_GOLV, D / 2)
    x0, y0 = UPP[0] + mitt[0], UPP[1] + mitt[1]
    return {f"KB{i}": Ledning(f"KB{i}", f"TK-VP:{a}", _vag(x0 + s * CC / 2, y0))
            for i, (a, s) in enumerate(RIKTNING.items(), 1)}


def stycken() -> list[Stycke]:
    return [Stycke(k.id, a, b, D, D, True, matt=f"Ø{D:g}") for k in ledningar().values()
            for a, b in zip(k.vag, k.vag[1:])]


def genomforingarna() -> tuple[list[Genomforing], list[str]]:
    return genomforingar(stycken())


def bojar(vag: tuple[Vek, ...]) -> list[float]:
    """Böjarnas vinklar [°] längs vägen."""
    ut = []
    for a, b, c in zip(vag, vag[1:], vag[2:]):
        u = [b[i] - a[i] for i in range(3)]
        w = [c[i] - b[i] for i in range(3)]
        cos = sum(p * q for p, q in zip(u, w)) / math.dist(a, b) / math.dist(b, c)
        ut.append(math.degrees(math.acos(max(-1.0, min(1.0, cos)))))
    return ut


def kontroll() -> tuple[list[str], list[str]]:
    """Fel och anmärkningar: böjar större än VINKEL, rören i varandra och genomföringarnas fel."""
    fel, anm = list(genomforingarna()[1]), []
    k = list(ledningar().values())
    for x in k:
        if max(bojar(x.vag)) > VINKEL + 0.01:
            fel.append(f"{x.id}: böj {max(bojar(x.vag)):.1f}° (högst {VINKEL:g}°)")
    for i, a in enumerate(k):
        for b in k[i + 1:]:
            d = LineString(a.vag).distance(LineString(b.vag))
            if d < D:
                fel.append(f"{a.id} och {b.id} går i varandra ({d:.0f} mm mellan mittlinjerna)")
    langd = sum(math.dist(p, q) for p, q in zip(k[0].vag, k[0].vag[1:])) / 1000.0
    anm.append(f"{len(k)} rör Ø{D:g}, {langd:.1f} m vardera, böjar om högst {VINKEL:g}°")
    return fel, anm


def utdrag() -> dict[str, object]:
    """Rören och genomföringarna för ritningen, som JSON."""
    return {"ledningar": {k.id: {"anslutning": k.anslutning, "vag": [list(q) for q in k.vag], "bojar": bojar(k.vag),
                                 "langd": sum(math.dist(a, b) for a, b in zip(k.vag, k.vag[1:]))}
                          for k in ledningar().values()},
            "d": D, "vinkel": VINKEL, "brunn": list(BRUNN), "z_golv": Z_GOLV, "z_vag": Z_VAG,
            "genomforingar": [{"del": g.del_, "atgard": g.atgard, "punkt": list(g.punkt), "element": g.element}
                              for g in genomforingarna()[0]]}
