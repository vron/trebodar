"""Källarens punkter (#51): rummen, panelerna och den ingjutna kopplingsdosan, brytarna och uttagen, och stigarna upp ur
väggarnas dosor in i bjälklaget. Rören: kallare.py; gruppernas rör från centralen genom bjälklaget till källaren
(FRAN_CENTRALEN): ../bjalklag/mellanbjalklag.py.

Koordinater i mm (K-05), z från plan 1:s golv (källarens golv z −2 250).
"""
from __future__ import annotations

import math
from collections.abc import Sequence
from functools import cache

from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

from trebodar.hus.grund import kallarvaggar as K
from trebodar.hus.grund.pelare import PELARE
from trebodar.hus.invandigt.kallarens_innervaggar import GIPS_T, VAGGAR as KL

from ...avlopp.ledningar import ledningar as avloppets
from ...montering import BJALKLAG, KALLARTAK, PLAN, Montering, Vek, kallartak, kallarvagg
from ...strak import mellan_jarnen
from ...teknikrum import GRUPPCENTRAL, X_GC
from ...vatten.system import vatten
from ..katalog import (ANSLUTNING, BRYTARE_1, FXP16, INGJUTNINGSDOSA, PANEL_600, UTTAG_1_IP44, UTTAG_2,
                       UTTAG_2_IP44)
from ..punkter import Apparat, Dosa, Lampa, Punkt, Rum, Tandgrupp, anslutning
from . import teknikrum

RUM = Rum("KA", "Källare", plan=0)
NAMN = RUM.namn

Z_BRYTARE = PLAN[0] + 1050.0
SPEL = 15.0                                  # fritt mellan de ingjutna dosorna och rören i bjälklaget
GENOMSTANSNING = 720.0                       # rörens genomstansningszon (6d, K-05): inga dosor där


def vaggens_c(namn: str) -> float:
    return next(v.c for v in K.VAGGAR if v.namn == namn)


V_GIPSYTA = K.KARNA / 2 + K.CELL + GIPS_T            # källarväggarnas gipsyta från kärnans mitt
KL_GIPSYTA = KL["KL1"].h + GIPS_T                    # KL-väggarnas gipsyta från stommens mitt

# arbetsrummen (golvets yta innanför väggarnas gips)
STORA_RUMMET = box(vaggens_c("V15") + V_GIPSYTA, vaggens_c("V9") + V_GIPSYTA, vaggens_c("V14") - V_GIPSYTA, vaggens_c("V1") - V_GIPSYTA)
SMA_V = box(vaggens_c("V21") + V_GIPSYTA, vaggens_c("V7") + V_GIPSYTA, KL["KL2"].c - KL_GIPSYTA, KL["KL1"].c - KL_GIPSYTA)
SMA_O = box(KL["KL2"].c + KL_GIPSYTA, vaggens_c("V7") + V_GIPSYTA, KL["KL3"].c - KL_GIPSYTA, KL["KL1"].c - KL_GIPSYTA)


@cache
def _ror_i_bjalklaget() -> list[tuple[LineString | Point, float]]:
    """Det som går i mellanbjälklagets undre del, där dosorna står (från undersidan till 70 mm upp): tappvattnets
    rör och avloppet genom bjälklaget, i plan med sin radie."""
    ut: list[tuple[LineString | Point, float]] = []
    v = vatten()
    segment = [(a, b, r.typ.yttre / 2) for r in v.ror.values() for a, b in zip(v.vag(r), v.vag(r)[1:])]
    segment += [(a, b, led.d / 2) for led in avloppets().values() for a, b in zip(led.vag, led.vag[1:])]
    topp = KALLARTAK + INGJUTNINGSDOSA.djup
    for a, b, r in segment:
        if max(a[2], b[2]) > KALLARTAK - 1.0 and min(a[2], b[2]) < topp + r:
            ut.append((LineString([a[:2], b[:2]]) if math.dist(a[:2], b[:2]) > 1.0 else Point(a[:2]), r))
    return ut


@cache
def _hinder() -> Polygon:
    """Där en ingjuten dosas mitt inte får stå: nära rören i bjälklaget och inom pelarnas genomstansningszon."""
    r = INGJUTNINGSDOSA.diameter / 2
    delar = [g.buffer(r + rr + SPEL) for g, rr in _ror_i_bjalklaget()]
    delar += [Point(x, y).buffer(GENOMSTANSNING + r) for x, y in PELARE.values()]
    return unary_union(delar)


def dosans_lage(x: float, y: float, rum: Polygon, hinder: Polygon | None = None) -> tuple[float, float]:
    """Den ingjutna dosans läge närmast (x, y) i rummet: fri från rören i bjälklaget och genomstansningszonerna (eller
    hinder, där dosans mitt inte får stå), och mellan underkantsnätets järn."""
    r = INGJUTNINGSDOSA.diameter / 2
    inne = rum.buffer(-300.0)
    stopp = _hinder() if hinder is None else hinder
    for steg in range(0, 1201, 50):
        for dx, dy in sorted({(sx * steg, sy * j) for sx in (-1, 1) for sy in (-1, 1) for j in range(0, steg + 1, 50)}
                             | {(sx * j, sy * steg) for sx in (-1, 1) for sy in (-1, 1) for j in range(0, steg + 1, 50)},
                             key=lambda d: math.hypot(*d)):
            q = Point(x + dx, y + dy)
            if not inne.contains(q) or stopp.contains(q):
                continue
            jx, jy = mellan_jarnen([(q.x, q.y)], KALLARTAK, KALLARTAK + INGJUTNINGSDOSA.djup, r, spel=5.0)
            p = Point(q.x + jx, q.y + jy)
            if inne.contains(p) and not stopp.contains(p):
                return p.x, p.y
    raise ValueError(f"ingen plats för en ingjuten dosa nära ({x:.0f}, {y:.0f})")


Y_RADER = (3140.0, 7100.0, 10100.0)          # det stora rummets panelrader: jämnt längs rummet, rören mellan panelerna
#                                              minst 300 mm från pelarna P1, P5 och P17 i rummets mittlinje


X_OSTRA = 12850.0                            # den östra panelraden: öster om brandlarmets kabel K08, som går under
#                                              taket längs x 12 417 till dosan DH (../../brandlarm)


def _paneler_stora() -> list[tuple[float, float]]:
    """Det stora rummets paneler: tre rader tvärs rummet, två i varje (på var sida om pelarnas linje)."""
    x0, _, x1, _ = STORA_RUMMET.bounds
    return [dosans_lage(x, y, STORA_RUMMET) for y in Y_RADER for x in (x0 + (x1 - x0) / 4, X_OSTRA)]


TANDGRUPPER = [
    Tandgrupp("KA-T6", "Källaren, det stora rummet", dimbar=False),
    Tandgrupp("KA-T7", "Källaren, det lilla rummet väster om KL2", dimbar=False),
    Tandgrupp("KA-T8", "Källaren, det lilla rummet öster om KL2", dimbar=False),
]

_STORA = _paneler_stora()
_PV = dosans_lage(SMA_V.centroid.x, SMA_V.centroid.y, SMA_V)
_PO = dosans_lage(SMA_O.centroid.x, SMA_O.centroid.y, SMA_O)
PANELER = [Lampa(f"KA-P{i + 1:02d}", PANEL_600, kallartak(x, y), "KA-T6") for i, (x, y) in enumerate(_STORA)]
PANELER += [Lampa("KA-P07", PANEL_600, kallartak(*_PV), "KA-T7"), Lampa("KA-P08", PANEL_600, kallartak(*_PO), "KA-T8")]

# den ingjutna kopplingsdosan i det stora rummets tak, i dess sydvästra hörn, dit gruppens rör kommer från centralen
D_STORA = dosans_lage(vaggens_c("V15") + V_GIPSYTA + 300.0, 9750.0, STORA_RUMMET)


def pa_kl(kod: str, langs: float, sida: int, z: float = Z_BRYTARE) -> Montering:
    """På en KL-väggs gips vid langs (x för väggar längs x, y för väggar längs y), sida +1 eller −1 mot växande y
    (längs x) eller x (längs y), z från plan 1:s golv."""
    v = KL[kod]
    c = v.c + sida * (v.h + GIPS_T)
    p, n = ((langs, c), (0.0, float(sida))) if v.riktning == "h" else ((c, langs), (float(sida), 0.0))
    return Montering((p[0], p[1], z), (n[0], n[1], 0.0), "vagg", kod)


BRYTARE = {
    "KA-B5": Apparat("KA-B5", BRYTARE_1, pa_kl("KL7", 6300.0, 1), styr=("KA-T6",)),      # vid KD5, i det stora rummet
    "KA-B6": Apparat("KA-B6", BRYTARE_1, pa_kl("KL1", 1800.0, -1), styr=("KA-T7",)),     # vid KD1, i det västra rummet
    "KA-B7": Apparat("KA-B7", BRYTARE_1, pa_kl("KL3", 4950.0, -1), styr=("KA-T8",)),     # vid KD3, i det östra rummet
}
# tvättstugan (hallen väster om teknikrummet): två uttag IP44 på V3 och tvättmaskinens och torktumlarens uttag på V21
# söder om tvättmaskinens tappställe KA-TM1 (y 8 420), alla i teknikrummets uttagshöjd
X_TVATT_UTTAG = (1800.0, 700.0)
Y_MASKINER = (8860.0, 8935.0)                 # tvättmaskinen, torktumlaren: två enkla uttag i en dubbel ram
UTTAG = [
    *[Apparat(f"KA-U{i + 1}", UTTAG_2_IP44, kallarvagg("V3", x, teknikrum.Z_UTTAG, -1))
      for i, x in enumerate(X_TVATT_UTTAG)],
    *[Apparat(f"KA-U{i + 3}", UTTAG_1_IP44, kallarvagg("V21", y, teknikrum.Z_UTTAG, 1)) for i, y in enumerate(Y_MASKINER)],
]
# arbetsrummen norr om KL1: två dubbla uttag i vardera rummet, på V21 och V7 i det västra och på V7 i det östra, i
# uttagshöjden 1 100 mm (G23)
Z_GOLVZON = 250.0                             # rören mellan dem i väggarnas cellplast, så högt över golvet
UTTAG_SMA = [("V21", 4800.0, 1), ("V7", 1500.0, 1), ("V7", 3200.0, 1), ("V7", 4100.0, 1)]
UTTAG += [Apparat(f"KA-U{i + 5}", UTTAG_2, kallarvagg(v, s_, teknikrum.Z_UTTAG, sida))
          for i, (v, s_, sida) in enumerate(UTTAG_SMA)]
# det stora rummet: fyra dubbla uttag, på V15, V1 och två på V14, i uttagshöjden; och fläkten FF3:s anslutning på V20
# vid fläkten (ventilation, FF3-FL1), 1 900 mm över golvet (G24)
Y_FF3, Z_FF3 = 9800.0, 1900.0
UTTAG_STORA = [("V15", 9830.0, 1), ("V1", 11600.0, -1), ("V14", 10000.0, -1), ("V14", 5000.0, -1)]
UTTAG += [Apparat("KA-D2", ANSLUTNING, kallarvagg("V20", Y_FF3, Z_FF3, 1))]
UTTAG += [Apparat(f"KA-U{i + 9}", UTTAG_2, kallarvagg(v, s_, teknikrum.Z_UTTAG, sida))
          for i, (v, s_, sida) in enumerate(UTTAG_STORA)]
# rummet norr om trapphallen (på V18, G23) och rummen vid V2 (på V2, G24): två dubbla uttag i vardera, 250 mm över
# golvet, i golvzonen där rören går
UTTAG_KS = [("V18", 2800.0, 1), ("V18", 1200.0, 1)]
UTTAG_V2 = [("V2", 5800.0, -1), ("V2", 8400.0, -1)]
UTTAG += [Apparat(f"KA-U{i + 13}", UTTAG_2, kallarvagg(v, s_, Z_GOLVZON, sida))
          for i, (v, s_, sida) in enumerate([*UTTAG_KS, *UTTAG_V2])]
# trapphallen: två dubbla uttag, på KL3 (norr om dörren KD2) och KL4 (väster om dörren KD4), 250 mm över golvet (G23)
Y_UTTAG_KL3, X_UTTAG_KL4 = 5600.0, 5300.0
UTTAG += [Apparat("KA-U17", UTTAG_2, pa_kl("KL4", X_UTTAG_KL4, 1, PLAN[0] + Z_GOLVZON)),
          Apparat("KA-U18", UTTAG_2, pa_kl("KL3", Y_UTTAG_KL3, 1, PLAN[0] + Z_GOLVZON))]
PUNKTER: list[Punkt] = [*PANELER, Dosa("KA-D1", INGJUTNINGSDOSA, kallartak(*D_STORA)), *BRYTARE.values(), *UTTAG]
_P = BRYTARE


H_TAK = 45.0                     # rören ur väggarnas dosor går lodrätt in i bjälklaget från så långt under taket
CC_VAGG = 40.0                   # stigarna ur samma dosa sida vid sida längs väggen, c/c


def _langs(p: Punkt) -> tuple[float, float]:
    """Väggens riktning vid punkten (KL-väggarna och källarväggarna)."""
    ref = p.lage.ref
    if ref in KL:
        return (1.0, 0.0) if KL[ref].riktning == "h" else (0.0, 1.0)
    return (1.0, 0.0) if next(q for q in K.VAGGAR if q.namn == ref).riktning == "h" else (0.0, 1.0)


def _i_vaggen(p: Punkt, f: float) -> tuple[float, float]:
    """Punkten i väggen ovanför dosan p, f längs väggen: KL-väggens regelfack eller källarväggens cellplast."""
    m = p.lage
    if m.ref in KL:
        v = KL[m.ref]
        return (m.punkt[0] + f, v.c) if v.riktning == "h" else (v.c, m.punkt[1] + f)
    w = next(q for q in K.VAGGAR if q.namn == m.ref)
    c = w.c + math.copysign(K.KARNA / 2 + K.CELL / 2, m.normal[1] if w.riktning == "h" else m.normal[0])
    return (m.punkt[0] + f, c) if w.riktning == "h" else (c, m.punkt[1] + f)


def stigarna(p: Punkt, mot: Sequence[tuple[float, float]], f0: float) -> list[tuple[float, float]]:
    """Stigarna upp ur dosan p i väggen till rören mot punkterna mot (en per rör, i den ordningen): sida vid sida
    längs väggen (CC_VAGG från f0, i ordning efter var punkterna ligger längs väggen, så att rören inte korsar
    varandra), alla förskjutna lika mycket längs väggen (och högst 30 mm tvärs) så att de går mellan
    underkantsnätets järn upp till elrörens övre nivå."""
    u = _langs(p)
    m = p.lage.punkt
    ordning = sorted(range(len(mot)), key=lambda i: (mot[i][0] - m[0]) * u[0] + (mot[i][1] - m[1]) * u[1])
    pts = [_i_vaggen(p, f0 + k * CC_VAGG) for k in range(len(mot))]
    dx, dy = mellan_jarnen(pts, KALLARTAK, BJALKLAG["MB"], FXP16.ytterdiameter / 2, langs=u, tvars=30.0)
    ut: list[tuple[float, float]] = [(0.0, 0.0)] * len(mot)
    for k, i in enumerate(ordning):
        ut[i] = (pts[k][0] + dx, pts[k][1] + dy)
    return ut


def panelens(lampa: Lampa) -> tuple[float, float]:
    return lampa.lage.punkt[0], lampa.lage.punkt[1]


def _fot(p: Punkt) -> Vek:
    """Där röret går in i väggdosan uppifrån: mitt över den, i dess överkant."""
    a = anslutning(p)
    dosa = p.typ.dosa if isinstance(p, Apparat) else p.typ if isinstance(p, Dosa) else None
    return (a[0], a[1], a[2] + (dosa.diameter / 2 if dosa is not None else 0.0))


def ur_dosan(p: Punkt, s: tuple[float, float]) -> tuple[Vek, ...]:
    """Röret upp ur väggdosan p (ur dess överkant) och i väggen till stigaren s under taket."""
    return _fot(p), (s[0], s[1], KALLARTAK - H_TAK)


def ned_i_dosan(p: Punkt, s: tuple[float, float]) -> tuple[Vek, ...]:
    """Röret från stigaren s under taket ned i väggen och in i väggdosan p uppifrån."""
    return (s[0], s[1], KALLARTAK - H_TAK), _fot(p)


def xy(p: Punkt) -> tuple[float, float]:
    return p.lage.punkt[0], p.lage.punkt[1]



# gruppernas rör från centralen genom bjälklaget till källaren (../bjalklag/mellanbjalklag.py): gruppen, punkten dit
# röret går, var det går ned ur bjälklaget och vägen därifrån in i punktens dosa (G17: den ingjutna kopplingsdosan i
# det stora rummets tak; G18: det västra lilla rummets brytare på KL1; G24: fläkten FF3:s anslutning på V20)
_GC = (X_GC, GRUPPCENTRAL.anslutningar["topp"][1])
_PK: dict[str, Punkt] = {p.id: p for p in PUNKTER}
S6 = stigarna(BRYTARE["KA-B6"], [_GC, panelens(PANELER[6]), xy(BRYTARE["KA-B7"])], -40.0)   # centralen, KA-P07, KA-B7
S_D2 = stigarna(_PK["KA-D2"], [_GC, xy(_PK["KA-U9"])], 0.0)                                # centralen, KA-U9
FRAN_CENTRALEN: dict[str, tuple[str, tuple[float, float], tuple[Vek, ...]]] = {
    "G17": ("KA-D1", D_STORA, ()),
    "G18": ("KA-B6", S6[0], ned_i_dosan(BRYTARE["KA-B6"], S6[0])),
    "G24": ("KA-D2", S_D2[0], ned_i_dosan(_PK["KA-D2"], S_D2[0])),
}
# de ingjutna dosorna i källarens tak (panelernas och kopplingsdosan): läge och radie
DOSOR = [(x, y, INGJUTNINGSDOSA.diameter / 2) for x, y in (*(panelens(p) for p in PANELER), D_STORA)]
