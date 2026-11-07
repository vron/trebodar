"""Källaren (#51): arbetsrummens belysning efter användarens indelning av rummen, 3000 K.

- Arbetsrummen (kostnaden styr): tunna utanpåliggande LED-paneler LEDVANCE PANEL COMPACT 600 (../katalog.py), var
  och en ansluten i en ingjuten dosa ovanför sig, mellan underkantsnätets järn och fri från rören i bjälklaget: sex i
  det stora rummet i högra huskroppen (öster om KL5 och KL7) och en i vart och ett av de två små rummen söder om KL1
  (väster och öster om KL2). Rummen och hur de motsvarar användarens (antaget, ärende #51): det stora rummet på
  nordvästra sidan är det stora rummet, det lilla rummet i sydostliga änden de två små rummen.
- De trevliga rummen (rummet vid trappan, tvättstugan, de två små rummen vid V2 och rummet söder om KL4) får sin
  belysning när spotarnas ingjutning är bestämd (#51); teknikrummet får ingen belysning nu.

Brytarna sitter vid dörrarna, 1 050 mm över golvet. Rören går ingjutna i bjälklaget, i elrörens undre nivå där den är
fri från tappvattnet och annars i den övre, och mellan brytarna i KL-väggarnas regelfack strax under taket:

- det stora rummet (G17): gruppens rör från centralen till en ingjuten kopplingsdosa i rummets tak (KA-D1), och
  därifrån till brytaren på KL7 och till panelerna;
- de små rummen (G18): gruppens rör från centralen i stråket S, ned i KL1 och i dess regelfack till det västra rummets
  brytare; därifrån till rummets panel och genom bjälklaget till det östra rummets brytare och dess panel. Rören går
  rakt upp ur brytarnas dosor, sida vid sida.

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
from ...montering import BJALKLAG, KALLARTAK, PLAN, Montering, Vek, kallartak
from ...strak import fri, mellan_jarnen
from ...vatten.system import vatten
from .. import kedjor
from ..bjalklag import mellanbjalklag as MB
from ..katalog import BRYTARE_1, FXP16, INGJUTNINGSDOSA, PANEL_600, UTTAG_1_IP44, UTTAG_2_IP44
from ...montering import kallarvagg
from ...teknikrum import GC_MATT, X_GC
from . import teknikrum
from ..punkter import Apparat, Dosa, Lampa, Ror, Rum, Tandgrupp

RUM = Rum("KA", "Källare", plan=0)
NAMN = RUM.namn

Z_BRYTARE = PLAN[0] + 1050.0
SPEL = 15.0                                  # fritt mellan de ingjutna dosorna och rören i bjälklaget
GENOMSTANSNING = 720.0                       # rörens genomstansningszon (6d, K-05): inga dosor där


def _c(namn: str) -> float:
    return next(v.c for v in K.VAGGAR if v.namn == namn)


_V = K.KARNA / 2 + K.CELL + GIPS_T            # källarväggarnas gipsyta från kärnans mitt
_KL = KL["KL1"].h + GIPS_T                    # KL-väggarnas gipsyta från stommens mitt

# arbetsrummen (golvets yta innanför väggarnas gips)
STORA_RUMMET = box(_c("V15") + _V, _c("V9") + _V, _c("V14") - _V, _c("V1") - _V)
SMA_V = box(_c("V21") + _V, _c("V7") + _V, KL["KL2"].c - _KL, KL["KL1"].c - _KL)
SMA_O = box(KL["KL2"].c + _KL, _c("V7") + _V, KL["KL3"].c - _KL, KL["KL1"].c - _KL)


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


def dosans_lage(x: float, y: float, rum: Polygon) -> tuple[float, float]:
    """Den ingjutna dosans läge närmast (x, y) i rummet: fri från rören i bjälklaget och genomstansningszonerna, och
    mellan underkantsnätets järn."""
    r = INGJUTNINGSDOSA.diameter / 2
    inne = rum.buffer(-300.0)
    for steg in range(0, 1201, 50):
        for dx, dy in sorted({(sx * steg, sy * j) for sx in (-1, 1) for sy in (-1, 1) for j in range(0, steg + 1, 50)}
                             | {(sx * j, sy * steg) for sx in (-1, 1) for sy in (-1, 1) for j in range(0, steg + 1, 50)},
                             key=lambda d: math.hypot(*d)):
            q = Point(x + dx, y + dy)
            if not inne.contains(q) or _hinder().contains(q):
                continue
            jx, jy = mellan_jarnen([(q.x, q.y)], KALLARTAK, KALLARTAK + INGJUTNINGSDOSA.djup, r, spel=5.0)
            p = Point(q.x + jx, q.y + jy)
            if inne.contains(p) and not _hinder().contains(p):
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

# den ingjutna kopplingsdosan i det stora rummets tak, i dess nordvästra hörn, dit gruppens rör kommer från centralen
D_STORA = dosans_lage(_c("V15") + _V + 300.0, 9750.0, STORA_RUMMET)


def _pa_kl(kod: str, langs: float, sida: int, z: float = Z_BRYTARE) -> Montering:
    """På en KL-väggs gips vid langs (x för väggar längs x, y för väggar längs y), sida +1 eller −1 mot växande y
    (längs x) eller x (längs y), z från plan 1:s golv."""
    v = KL[kod]
    c = v.c + sida * (v.h + GIPS_T)
    p, n = ((langs, c), (0.0, float(sida))) if v.riktning == "h" else ((c, langs), (float(sida), 0.0))
    return Montering((p[0], p[1], z), (n[0], n[1], 0.0), "vagg", kod)


BRYTARE = {
    "KA-B5": Apparat("KA-B5", BRYTARE_1, _pa_kl("KL7", 6300.0, 1), styr=("KA-T6",)),      # vid KD5, i det stora rummet
    "KA-B6": Apparat("KA-B6", BRYTARE_1, _pa_kl("KL1", 1800.0, -1), styr=("KA-T7",)),     # vid KD1, i det västra rummet
    "KA-B7": Apparat("KA-B7", BRYTARE_1, _pa_kl("KL3", 4950.0, -1), styr=("KA-T8",)),     # vid KD3, i det östra rummet
}
# tvättstugan (hallen väster om teknikrummet): två uttag IP44 på V3 och tvättmaskinens och torktumlarens uttag på V21
# norr om tvättmaskinens tappställe KA-TM1 (y 8 420), alla i teknikrummets uttagshöjd
X_TVATT_UTTAG = (1800.0, 700.0)
Y_MASKINER = (8860.0, 8935.0)                 # tvättmaskinen, torktumlaren: två enkla uttag i en dubbel ram
UTTAG = [
    *[Apparat(f"KA-U{i + 1}", UTTAG_2_IP44, kallarvagg("V3", x, teknikrum.Z_UTTAG, -1))
      for i, x in enumerate(X_TVATT_UTTAG)],
    *[Apparat(f"KA-U{i + 3}", UTTAG_1_IP44, kallarvagg("V21", y, teknikrum.Z_UTTAG, 1)) for i, y in enumerate(Y_MASKINER)],
]
PUNKTER = [*PANELER, Dosa("KA-D1", INGJUTNINGSDOSA, kallartak(*D_STORA)), *BRYTARE.values(), *UTTAG]
_P = BRYTARE


def upp_ur_vaggen(p: Apparat, forskjutning: Sequence[float]) -> list[tuple[Vek, Vek]]:
    """Rören rakt upp ur brytarens dosa i KL-väggens regelfack och in i bjälklaget (elrörens undre nivå), sida vid
    sida längs väggen (forskjutning från brytaren), alla förskjutna lika mycket längs väggen (och högst 30 mm tvärs)
    så att de går mellan underkantsnätets järn: per rör (punkten i väggen i dosans höjd, punkten i bjälklaget)."""
    m = p.lage
    v = KL[m.ref]
    langs = (1.0, 0.0) if v.riktning == "h" else (0.0, 1.0)
    pts = [(m.punkt[0] + f, v.c) if v.riktning == "h" else (v.c, m.punkt[1] + f) for f in forskjutning]
    dx, dy = mellan_jarnen(pts, KALLARTAK, BJALKLAG["MB-UK"], FXP16.ytterdiameter / 2, langs=langs, tvars=30.0)
    return [((x + dx, y + dy, m.punkt[2]), (x + dx, y + dy, BJALKLAG["MB-UK"])) for x, y in pts]


@cache
def _hindren() -> list[tuple[LineString | Point, float, float, float]]:
    """Det som källarens rör i bjälklaget ska gå fria från: plan 1:s elrör (stråken och kedjorna), tappvattnet och
    avloppet: (linjen i plan, radien, lägsta och högsta z)."""
    v = vatten()
    seg = [(a, b, r.typ.yttre / 2) for r in v.ror.values() for a, b in zip(v.vag(r), v.vag(r)[1:])]
    seg += [(a, b, r.typ.ytterdiameter / 2) for r in (*MB.ROR, *kedjor.ROR) for a, b in zip(r.via, r.via[1:])]
    seg += [(a, b, led.d / 2) for led in avloppets().values() for a, b in zip(led.vag, led.vag[1:])]
    return [(LineString([a[:2], b[:2]]) if math.dist(a[:2], b[:2]) > 0.5 else Point(a[:2]), r,
             min(a[2], b[2]), max(a[2], b[2])) for a, b, r in seg
            if max(a[2], b[2]) > KALLARTAK - 1.0 and min(a[2], b[2]) < PLAN[1] + 1.0]


def _fritt(pts: Sequence[tuple[float, float]], z: float) -> bool:
    """Om rören (Ø16) genom punkterna i nivån z går fria från hindren och armeringsjärnen."""
    r = FXP16.ytterdiameter / 2
    linje = LineString(pts)
    for g, rr, z0, z1 in _hindren():
        if z1 >= z - r - rr - 5.0 and z0 <= z + r + rr + 5.0 and linje.distance(g) < r + rr + 5.0:
            return False
    return fri(linje, r, z - r, z + r, 5.0)


def i_bjalklaget(pts: Sequence[tuple[float, float]]) -> tuple[Vek, ...]:
    """Röret i bjälklaget genom punkterna (i plan): varje sträcka i elrörens undre nivå om den är fri, annars i den
    övre (lodrätt emellan där nivån byts)."""
    ut: list[Vek] = []
    for a, b in zip(pts, pts[1:]):
        z = next((z for z in (BJALKLAG["MB-UK"], BJALKLAG["MB"]) if _fritt([a, b], z)), BJALKLAG["MB-UK"])
        if ut and abs(ut[-1][2] - z) > 0.5:
            ut.append((a[0], a[1], z))
        elif not ut:
            ut.append((a[0], a[1], z))
        ut.append((b[0], b[1], z))
    return tuple(ut)


def _panel(lampa: Lampa) -> tuple[float, float]:
    return lampa.lage.punkt[0], lampa.lage.punkt[1]


_P01, _P02, _P03, _P04, _P05, _P06, _P07, _P08 = (_panel(p) for p in PANELER)
_B6, _B7 = _P["KA-B6"], _P["KA-B7"]
_U5 = upp_ur_vaggen(_P["KA-B5"], (300.0, 340.0))         # norr om brytaren, bort från dörren KD5: panelerna, gruppen
_U6 = upp_ur_vaggen(_B6, (-40.0, 0.0, 40.0))              # till panelen, till det östra rummets brytare, gruppens rör
_U7 = upp_ur_vaggen(_B7, (-40.0, 0.0))                    # till panelen, från det västra rummets brytare


def _till(u: tuple[Vek, Vek]) -> tuple[Vek, ...]:
    """Ned ur bjälklaget i väggen till dosan (u: punkten i väggen, punkten i bjälklaget)."""
    return u[1], u[0]


def _fran(u: tuple[Vek, Vek]) -> tuple[Vek, ...]:
    return u[0], u[1]


def _xy(u: tuple[Vek, Vek]) -> tuple[float, float]:
    return u[1][0], u[1][1]


X_OVER = 13090.0          # det stora rummet: röret till brytaren går tvärs stråket E, tappvattnet till UF1 och
#                           avloppet AV20 i den övre nivån här (öster om ugnens rör G11, väster om V14:s vinkeljärn), där
#                           golvvärmen inte går (köksbänken), så att det byter nivå utan att korsa slingorna
Y_VAST = 7400.0           # söder om V6 och V15, norr om panelraden, till brytaren på KL7


def _ror(id_: str, fran: str, till: str, via: Sequence[Vek]) -> Ror:
    """Röret genom via, utan punkter som upprepas."""
    ut: list[Vek] = []
    for q in via:
        if not ut or math.dist(q, ut[-1]) > 0.5:
            ut.append(q)
    return Ror(id_, FXP16, fran, till, via=tuple(ut))


Y_STORA = 9750.0          # gruppens rör till det stora rummet: österut i y, norr om rören till ön och hällen, genom
#                           glipan mellan V20:s och V15:s järn


_X_FIL = MB.STRAK["S"].fil((MB.S_STIG[1], MB.RAD_A)).coords[-1][0]       # filen söderut över källaren
Y_KL1_N = KL["KL1"].c + 180.0     # de små rummens grupprör västerut ur stråket S, norr om KL1
Y_OSTER = 5700.0                  # från det västra till det östra rummets brytare, under stråket S och söder om
#                                   tappvattnet från UF2

_V3_EPS = kallarvagg("V3", 0.0, 0.0, -1).punkt[1] + 63.0      # mitt i V3:s och V21:s cellplast bakom gipsen
_V21_EPS = kallarvagg("V21", 0.0, 0.0, 1).punkt[0] - 63.0
_ZU = teknikrum.Z_UTTAG + PLAN[0]
_X_UT = X_GC - GC_MATT[0] / 2                            # centralens västra ände


def _tvatten(n: int, x0: float, dz: float) -> tuple[Vek, ...]:
    """Röret till maskinens uttag n (0 tvättmaskinen, 1 torktumlaren): ur centralens baksida i V3:s cellplast
    västerut dz under uttagens höjd, runt hörnet in i V21:s och söderut till uttaget."""
    y = Y_MASKINER[n]
    return (*teknikrum.bakifran(x0, _ZU - dz), (_V21_EPS, _V3_EPS, _ZU - dz), (_V21_EPS, y, _ZU - dz), (_V21_EPS, y, _ZU))


ROR: list[Ror] = [
    # tvättstugan: uttagen på V3 (G20) och maskinernas (G21, G22) ur centralens baksida västerut i V3:s cellplast,
    # under uttagen (torktumlaren 50 mm, tvättmaskinen 100 mm, så att rören inte korsar varandra vid V21)
    _ror("G20-M", "GC", "KA-U1", (*teknikrum.bakifran(_X_UT + 20.0, _ZU), (X_TVATT_UTTAG[0], _V3_EPS, _ZU))),
    _ror("G20-R1", "KA-U1", "KA-U2", ((X_TVATT_UTTAG[0], _V3_EPS, _ZU), (X_TVATT_UTTAG[1], _V3_EPS, _ZU))),
    _ror("G21-M", "GC", "KA-U3", _tvatten(0, _X_UT + 40.0, 100.0)),
    _ror("G22-M", "GC", "KA-U4", _tvatten(1, _X_UT + 60.0, 50.0)),
    # gruppernas rör från centralen: de små rummen i stråket S, under dess andra filer västerut och ned i KL1; det
    # stora rummet ur den bakre raden norrut över V3 i den undre nivån (under rören österut till ön) och österut i den
    # övre till kopplingsdosan
    _ror("G18-M", "GC", "KA-B6", (*MB.i_straket(MB.S_STIG[1], "S", ((_X_FIL, Y_KL1_N),), ()),
                                  *i_bjalklaget([(_X_FIL, Y_KL1_N), (_xy(_U6[2])[0], Y_KL1_N), _xy(_U6[2])]),
                                  *_till(_U6[2]))),
    _ror("G17-M", "GC", "KA-D1", (*MB.ur_raden(MB.KA_STIG, MB.RAD_B, "MB-UK"),
                                  *i_bjalklaget([(MB.KA_STIG, MB.RAD_B), (MB.KA_STIG, Y_STORA), (D_STORA[0], Y_STORA),
                                                 D_STORA]))),
    # det stora rummet: från kopplingsdosan norrut och österut över öns rör, söderut tvärs stråket E vid X_OVER och
    # västerut till brytaren på KL7; panelerna i den norra raden från kopplingsdosan, de andra från brytaren
    _ror("G17-R1", "KA-D1", "KA-B5", (*i_bjalklaget([D_STORA, (X_OVER, D_STORA[1]), (X_OVER, 8300.0), (X_OVER, Y_VAST),
                                                     (_xy(_U5[1])[0], Y_VAST), _xy(_U5[1])]),
                                      *_till(_U5[1]))),
    _ror("KA-R6-1", "KA-D1", "KA-P05", i_bjalklaget([D_STORA, (D_STORA[0], _P05[1]), _P05])),
    _ror("KA-R6-2", "KA-P05", "KA-P06", i_bjalklaget([_P05, _P06])),
    _ror("KA-R6-3", "KA-B5", "KA-P03", (*_fran(_U5[0])[:1], *i_bjalklaget([_xy(_U5[0]), (_P03[0], _xy(_U5[0])[1]), _P03]))),
    _ror("KA-R6-4", "KA-P03", "KA-P04", i_bjalklaget([_P03, _P04])),
    _ror("KA-R6-5", "KA-P04", "KA-P02", i_bjalklaget([_P04, _P02])),
    _ror("KA-R6-6", "KA-P02", "KA-P01", i_bjalklaget([_P02, _P01])),
    # de små rummen: från det västra rummets brytare till dess panel och söderut och österut (under stråket S) till
    # det östra rummets brytare, och därifrån till dess panel
    _ror("KA-R7-1", "KA-B6", "KA-P07", (*_fran(_U6[0])[:1], *i_bjalklaget([_xy(_U6[0]), (_P07[0], _xy(_U6[0])[1]), _P07]))),
    _ror("G18-R1", "KA-B6", "KA-B7", (*_fran(_U6[1])[:1], *i_bjalklaget([_xy(_U6[1]), (_xy(_U6[1])[0], Y_OSTER),
                                                                      (_xy(_U7[1])[0], Y_OSTER), _xy(_U7[1])]),
                                      *_till(_U7[1]))),
    _ror("KA-R8-1", "KA-B7", "KA-P08", (*_fran(_U7[0])[:1], *i_bjalklaget([_xy(_U7[0]), (_P08[0], _xy(_U7[0])[1]), _P08]))),
]
