"""Källaren (#51): belysningen, uttagen i alla rum, tvättstugans maskiner och fläkten FF3:s anslutning, efter
användarens indelning av rummen, 3000 K.

Belysningen:
- Arbetsrummen (kostnaden styr): tunna utanpåliggande LED-paneler LEDVANCE PANEL COMPACT 600 (../katalog.py), var och
  en ansluten i en ingjuten dosa ovanför sig, mellan underkantsnätets järn och fri från rören i bjälklaget och pelarnas
  genomstansningszoner: sex i det stora rummet i högra huskroppen (öster om KL5 och KL7) och en i vart och ett av de
  två små rummen söder om KL1 (väster och öster om KL2). Rummen och hur de motsvarar användarens (antaget, ärende
  #51): det stora rummet på nordvästra sidan är det stora rummet, det lilla rummet i sydostliga änden de två små
  rummen.
- De trevliga rummen (trapphallen, tvättstugan, de två små rummen norr om V4–V6 och rummet söder om trapphallen):
  ljuslinjer i ask utanpå betongtaket (../katalog.ljuslinje, egen tillverkning, #51): en askprofil 56 × 22 med ett
  fräst spår underifrån, en aluminiumkanal i spåret, en COB-LED-list 24 V (Ra ≥ 97, R9 > 90, 3000 K) och en opal
  diffusor klippt i kanalen. Linjerna följer rummen och hur de används (LINJER), parallella med väggarna: längs
  trapphallen och en tvärs ned mot trappans fot, längs tvättstugans hall och en över bänken vid V21, en mitt i var och
  en av de två delarna norr om V4–V6 och två parallella i rummet söder om trapphallen, minst 500 mm från
  brandvarnarna. Ingen dosa i taket: 24 V går i egna ingjutna rör, skilda från 230 V-rören, som slutar i taket under
  profilens ände (rörändan pluggas och tätas vid gjutningen och täcks helt av armaturen); båda rörändarna står mellan
  underkantsnätets järn och fria från rören i bjälklaget (_placera), och ledaren går genom profilen till nästa linje.
  Drivdonen (24 V CV, fasdimbara med bakkant, ett per tändgrupp) sitter i drivdonsskåpet TK-LC på KL8 i teknikrummet
  (../../teknikrum.py), åtkomligt; vanliga vriddimrar vid ingångarna dimrar dem (DIMRAR; de två små rummen har ingen
  vägg emellan i modellen och är två tändgrupper på två dimrar i en dubbelram), och den dimrade fasen går i ett eget
  rör från varje dimmer till skåpet. Kretsarna (KRETSAR), ledarnas area och spänningsfallet: installation.py.
- Teknikrummet får ingen belysning nu.
- Brytarna och dimrarna sitter vid dörrarna, 1 050 mm över golvet; rören går rakt upp ur deras dosor, sida vid sida,
  i KL-väggarnas regelfack in i bjälklaget och ingjutna där (i_bjalklaget: elrörens undre nivå där den är fri, annars
  den övre; nivån byts bara där golvvärmen inte går). Det stora rummet (G17): gruppens rör från den bakre raden över
  centralen till en ingjuten kopplingsdosa i rummets tak (KA-D1), och därifrån till brytaren på KL7 (tvärs stråket E
  vid X_OVER) och till panelerna. De andra rummen (G18): gruppens rör i stråket S och ned i KL1 till det västra lilla
  rummets brytare, därifrån till rummets panel och genom bjälklaget till det östra rummets brytare och panel, och
  vidare till dimrarna i tur och ordning (söder om pelarna i KL4 och KL1). Drivdonsskåpets rör (den dimrade fasen
  från dimrarna och 24 V till ljuslinjerna) går rakt upp ur skåpets ovansida i en rad, söderut och i ett band
  österut i elrörens undre nivå (under golvvärmens stråk), där vart och ett viker av mot sin dimmer eller ljuslinje;
  G18:s rör går i den övre nivån där de korsar dem.

Uttagen (dubbla, i arbetsrummen, tvättstugan och teknikrummet 1 100 mm över golvet, i de trevliga rummen 250 mm) och
anslutningarna sitter på källarväggarna och KL-väggarna; rören går i källarväggarnas cellplast bakom gipsen och i
KL-väggarnas regelfack, vågrätt i golvzonen (Z_GOLVZON, under tappställenas rör) och upp eller ned till uttagen:
- tvättstugan (G20: två IP44 på V3; G21 och G22: tvättmaskinens och torktumlarens på V21 vid KA-TM1) ur centralens
  baksida i V3:s cellplast (teknikrummets uttag G19 i rum/teknikrum.py);
- de små rummen söder om KL1, rummet söder om trapphallen och trapphallen (G23): ur centralens baksida västerut i V3:s,
  söderut i V21:s och österut i V7:s cellplast, runt hörnet in i V18:s, och upp i V7:s och in i KL3:s och KL4:s
  regelfack, över dörren KD3;
- det stora rummet, rummen vid V2 och fläkten FF3 (G24): gruppens rör genom bjälklaget till fläktens anslutning på
  V20, därifrån genom bjälklaget till V15 och i V15:s, V16:s, V1:s och V14:s cellplast mellan det stora rummets uttag
  (under stråket E i bjälklaget), och i V20:s och V2:s till rummen vid V2.

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
from ..katalog import (ANSLUTNING, ASKPROFIL, BRYTARE_1, DIMMER_LED, DIMMER_LED_2, FXP16, INGJUTNINGSDOSA,
                       PANEL_600, UTTAG_1_IP44, UTTAG_2, UTTAG_2_IP44, ljuslinje)
from ...montering import kallarvagg
from ...teknikrum import DRIVDONSSKAP, GC_MATT, X_GC
from . import teknikrum
from ..punkter import Apparat, Dosa, Krets, Lampa, Punkt, Ror, Rum, Tandgrupp, anslutning

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
# arbetsrummen söder om KL1: två dubbla uttag i vardera rummet, på V21 och V7 i det västra och på V7 i det östra, i
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
# rummet söder om trapphallen (på V18, G23) och rummen vid V2 (på V2, G24): två dubbla uttag i vardera, 250 mm över
# golvet, i golvzonen där rören går
UTTAG_KS = [("V18", 2800.0, 1), ("V18", 1200.0, 1)]
UTTAG_V2 = [("V2", 5800.0, -1), ("V2", 8400.0, -1)]
UTTAG += [Apparat(f"KA-U{i + 13}", UTTAG_2, kallarvagg(v, s_, Z_GOLVZON, sida))
          for i, (v, s_, sida) in enumerate([*UTTAG_KS, *UTTAG_V2])]
# trapphallen: två dubbla uttag, på KL3 (söder om dörren KD2) och KL4 (väster om dörren KD4), 250 mm över golvet (G23)
Y_UTTAG_KL3, X_UTTAG_KL4 = 5600.0, 5300.0
UTTAG += [Apparat("KA-U17", UTTAG_2, _pa_kl("KL4", X_UTTAG_KL4, 1, PLAN[0] + Z_GOLVZON)),
          Apparat("KA-U18", UTTAG_2, _pa_kl("KL3", Y_UTTAG_KL3, 1, PLAN[0] + Z_GOLVZON))]
PUNKTER: list[Punkt] = [*PANELER, Dosa("KA-D1", INGJUTNINGSDOSA, kallartak(*D_STORA)), *BRYTARE.values(), *UTTAG]
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


Bit = tuple[LineString | Point, float, float, float]       # ett rörs raka bit: linjen i plan, radien, lägsta och högsta z


def _fritt(pts: Sequence[tuple[float, float]], z: float, andra: Sequence[Bit] = ()) -> bool:
    """Om rören (Ø16) genom punkterna i nivån z går fria från hindren (och andra) och armeringsjärnen."""
    r = FXP16.ytterdiameter / 2
    linje = LineString(pts)
    for g, rr, z0, z1 in (*_hindren(), *andra):
        if z1 >= z - r - rr - 5.0 and z0 <= z + r + rr + 5.0 and linje.distance(g) < r + rr + 5.0:
            return False
    return fri(linje, r, z - r, z + r, 5.0)


def i_bjalklaget(pts: Sequence[tuple[float, float]], andra: Sequence[Bit] = (),
                 dosor: Sequence[tuple[float, float]] = ()) -> tuple[Vek, ...]:
    """Röret i bjälklaget genom punkterna (i plan): varje sträcka i elrörens undre nivå om den är fri (från hindren
    och andra, och inte går genom någon av de ingjutna dosorna), annars i den övre (lodrätt emellan där nivån byts)."""
    ut: list[Vek] = []
    for a, b in zip(pts, pts[1:]):
        linje = LineString([a, b])
        genom = any(linje.distance(Point(c)) < INGJUTNINGSDOSA.diameter / 2 + FXP16.ytterdiameter / 2 + 5.0
                    for c in dosor)
        nivaer = (BJALKLAG["MB"],) if genom else (BJALKLAG["MB-UK"], BJALKLAG["MB"])
        z = next((z for z in nivaer if _fritt([a, b], z, andra)), nivaer[0])
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

def _eps(v: str) -> float:
    """Källarväggens cellplast mot rummet: mittens läge tvärs väggen (x för väggar längs y, y för väggar längs x)."""
    w = next(q for q in K.VAGGAR if q.namn == v)
    sida = {"V15": 1, "V16": 1, "V20": 1, "V18": 1, "V21": 1, "V7": 1, "V4": 1, "V1": -1, "V14": -1, "V2": -1,
            "V3": -1}[v]
    return w.c + sida * (K.KARNA / 2 + K.CELL / 2)


def _i_cellplasten(v: str, s_: float) -> tuple[float, float]:
    """Punkten i plan mitt i källarväggens cellplast (mot rummet) vid s_ längs väggen."""
    w = next(q for q in K.VAGGAR if q.namn == v)
    return (s_, _eps(v)) if w.riktning == "h" else (_eps(v), s_)


_V3_EPS, _V21_EPS, _V7_EPS = _eps("V3"), _eps("V21"), _eps("V7")      # mitt i cellplasten bakom gipsen
_ZU = teknikrum.Z_UTTAG + PLAN[0]
_X_UT = X_GC - GC_MATT[0] / 2                            # centralens västra ände


def _tvatten(n: int, x0: float, dz: float) -> tuple[Vek, ...]:
    """Röret till maskinens uttag n (0 tvättmaskinen, 1 torktumlaren): ur centralens baksida i V3:s cellplast
    västerut dz under uttagens höjd, runt hörnet in i V21:s och söderut till uttaget."""
    y = Y_MASKINER[n]
    return (*teknikrum.bakifran(x0, _ZU - dz), (_V21_EPS, _V3_EPS, _ZU - dz), (_V21_EPS, y, _ZU - dz), (_V21_EPS, y, _ZU))


_ZG = PLAN[0] + Z_GOLVZON


def _sma_uttagen() -> list[Ror]:
    """De små rummens uttag (G23): gruppens rör ur centralens baksida, ned i V3:s cellplast till golvzonen, västerut
    och runt hörnet söderut i V21:s till det första uttaget; därifrån rören mellan uttagen i golvzonen i V21:s och
    V7:s cellplast, var och ett upp till sitt uttag (rören som går vidare ned 30 mm bredvid)."""
    x0 = _X_UT + 100.0
    u0 = _i_cellplasten(*UTTAG_SMA[0][:2])
    ut = [_ror("G23-M", "GC", "KA-U5", (*teknikrum.bakifran(x0, _ZU - 150.0), (x0, _V3_EPS, _ZG),
                                        (_V21_EPS, _V3_EPS, _ZG), (u0[0], u0[1], _ZG), (u0[0], u0[1], _ZU)))]
    for i, ((va, sa, _), (vb, sb, _)) in enumerate(zip(UTTAG_SMA, UTTAG_SMA[1:])):
        riktning = -1.0 if va == "V21" else 1.0                  # söderut längs V21, österut längs V7
        a = _i_cellplasten(va, sa + 30.0 * riktning)
        b = _i_cellplasten(vb, sb)
        horn = [(_V21_EPS, _V7_EPS, _ZG)] if va != vb else []
        ut.append(_ror(f"G23-R{i + 1}", f"KA-U{i + 5}", f"KA-U{i + 6}",
                       ((a[0], a[1], _ZU), (a[0], a[1], _ZG), *horn, (b[0], b[1], _ZG), (b[0], b[1], _ZU))))
    # vidare österut i V7:s cellplast förbi KL3:s ände och runt hörnet söderut i V18:s, till rummet söder om
    # trapphallen (uttagen i golvzonen)
    a = _i_cellplasten("V7", UTTAG_SMA[-1][1] + 30.0)
    v18 = _eps("V18")
    ut.append(_ror("G23-R4", "KA-U8", "KA-U13", ((a[0], a[1], _ZU), (a[0], a[1], _ZG), (v18, _V7_EPS, _ZG),
                                                 (v18, UTTAG_KS[0][1], _ZG))))
    ut.append(_ror("G23-R5", "KA-U13", "KA-U14", ((v18, UTTAG_KS[0][1], _ZG), (v18, UTTAG_KS[1][1], _ZG))))
    # trapphallen: från det östra lilla rummets andra uttag upp i V7:s cellplast till strax under taket, österut till
    # KL3 och i dess regelfack norrut över dörren KD3 till uttaget på KL3; därifrån lägre (där inga dörrar är)
    # söderut till KL4 och österut i dess regelfack till uttaget där
    kl3, kl4 = KL["KL3"].c, KL["KL4"].c
    zh, zl = KALLARTAK - 60.0, KALLARTAK - 110.0
    a = _i_cellplasten("V7", UTTAG_SMA[-1][1] - 30.0)
    ut.append(_ror("G23-R6", "KA-U8", "KA-U18", ((a[0], a[1], _ZU), (a[0], a[1], zh), (kl3, _V7_EPS, zh),
                                                 (kl3, Y_UTTAG_KL3, zh), (kl3, Y_UTTAG_KL3, _ZG))))
    ut.append(_ror("G23-R7", "KA-U18", "KA-U17", ((kl3, Y_UTTAG_KL3 - 30.0, _ZG), (kl3, Y_UTTAG_KL3 - 30.0, zl),
                                                  (kl3, kl4, zl), (X_UTTAG_KL4, kl4, zl), (X_UTTAG_KL4, kl4, _ZG))))
    return ut


def ned_i_kallarvaggen(v: str, s_: float, z: float) -> tuple[Vek, Vek]:
    """Ned ur bjälklaget (elrörens undre nivå) i källarväggens cellplast vid s_ längs väggen, mellan
    underkantsnätets järn (förskjutet längs väggen), till höjden z: (punkten i bjälklaget, punkten i väggen)."""
    w = next(q for q in K.VAGGAR if q.namn == v)
    c = _eps(v)
    x, y = (s_, c) if w.riktning == "h" else (c, s_)
    langs = (1.0, 0.0) if w.riktning == "h" else (0.0, 1.0)
    dx, dy = mellan_jarnen([(x, y)], KALLARTAK, BJALKLAG["MB-UK"], FXP16.ytterdiameter / 2, langs=langs, tvars=30.0)
    return (x + dx, y + dy, BJALKLAG["MB-UK"]), (x + dx, y + dy, z)


Y_G24 = 9800.0            # det stora rummets grupprör österut i bjälklaget, i glipan mellan V20:s järn


def _stora_uttagen() -> list[Ror]:
    """Det stora rummets uttag och fläkten FF3 (G24): gruppens rör ur den bakre raden över centralen norrut över V3 och
    österut i bjälklaget, ned i V20:s cellplast till fläktens anslutning; därifrån upp och österut i bjälklaget och
    ned i V15:s cellplast till det första uttaget, och sedan i golvzonen i V15:s, V16:s, V1:s och V14:s cellplast
    mellan uttagen (under stråket E och tappvattnet till UF1, som går i bjälklaget)."""
    ff3 = ned_i_kallarvaggen("V20", Y_FF3, PLAN[0] + Z_FF3)
    ut = [_ror("G24-M", "GC", "KA-D2", (*MB.ur_raden(MB.G24_STIG, MB.RAD_B, "MB-UK"),
                                        *i_bjalklaget([(MB.G24_STIG, MB.RAD_B), (MB.G24_STIG, Y_G24),
                                                       (ff3[0][0], Y_G24), ff3[0][:2]]), ff3[1]))]
    upp = ned_i_kallarvaggen("V20", Y_FF3 + 40.0, PLAN[0] + Z_FF3)
    u9 = ned_i_kallarvaggen("V15", UTTAG_STORA[0][1], _ZU)
    ut.append(_ror("G24-R1", "KA-D2", "KA-U9", (upp[1], *i_bjalklaget([upp[0][:2], (upp[0][0], u9[0][1]), u9[0][:2]]),
                                                u9[1])))
    hornen = {("V15", "V1"): (_eps("V16"), _eps("V1")), ("V1", "V14"): (_eps("V14"), _eps("V1"))}
    for i, ((va, sa, _), (vb, sb, _)) in enumerate(zip(UTTAG_STORA, UTTAG_STORA[1:])):
        riktning = -1.0 if (va, vb) == ("V14", "V14") else 1.0
        a = (_eps(va), sa + 30.0 * riktning) if va in ("V15", "V14") else (sa + 30.0, _eps(va))
        b = (_eps(vb), sb) if vb in ("V15", "V14") else (sb, _eps(vb))
        horn = [(*hornen[(va, vb)], _ZG)] if (va, vb) in hornen else []
        ut.append(_ror(f"G24-R{i + 2}", f"KA-U{i + 9}", f"KA-U{i + 10}",
                       ((a[0], a[1], _ZU), (a[0], a[1], _ZG), *horn, (b[0], b[1], _ZG), (b[0], b[1], _ZU))))
    # rummen vid V2: från fläktens anslutning ned i V20:s cellplast till golvzonen, norrut och runt hörnet österut i
    # V2:s till uttagen (i golvzonen)
    v20, v2 = _eps("V20"), _eps("V2")
    ut.append(_ror("G24-R5", "KA-D2", "KA-U15", ((v20, Y_FF3 - 30.0, PLAN[0] + Z_FF3), (v20, Y_FF3 - 30.0, _ZG),
                                                 (v20, v2, _ZG), (UTTAG_V2[0][1], v2, _ZG))))
    ut.append(_ror("G24-R6", "KA-U15", "KA-U16", ((UTTAG_V2[0][1], v2, _ZG), (UTTAG_V2[1][1], v2, _ZG))))
    return ut


ROR: list[Ror] = [
    *_sma_uttagen(),
    *_stora_uttagen(),
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




# ------------------------------------------------------------------ de trevliga rummen: ljuslinjerna, dimrarna och drivdonen

# rummen (golvets yta innanför väggarnas gips): trapphallen öster om KL3 (utan trappan mellan KL4 och KL6),
# tvättstugan (hallen mellan KL1 och KL8 och rummet vid V3 väster om KL8), rummen norr om V4–V6 (en yta utan vägg
# emellan, belyst som två delar) och rummet söder om trapphallen (söder om KL4)
TRAPPHALL = box(KL["KL3"].c + _KL, KL["KL4"].c + _KL, KL["KL7"].c - _KL, _c("V5") - _V).difference(
    box(KL["KL6"].a - 60.0, KL["KL4"].c, KL["KL7"].c, KL["KL6"].c + _KL))
TVATTSTUGA = unary_union([box(_c("V21") + _V, KL["KL1"].c + _KL, KL["KL8"].a, _c("V3") - _V),
                          box(KL["KL8"].a, KL["KL1"].c + _KL, KL["KL3"].c - _KL, KL["KL10"].c - _KL)])
RUMMEN_V2 = box(_c("V19") + _V, _c("V5") + _V, _c("V15") - _V, _c("V2") - _V)
RUMMET_KS = unary_union([box(_c("V18") + _V, _c("V10") + _V, KL["KL5"].c - _KL, KL["KL4"].c - _KL),
                         box(KL["KL3"].c + _KL, _c("V7") + _V, _c("V18") + _V, KL["KL4"].c - _KL)])

TANDGRUPPER += [
    Tandgrupp("KA-T1", "Källaren, trapphallen"),
    Tandgrupp("KA-T2", "Källaren, tvättstugan"),
    Tandgrupp("KA-T3", "Källaren, rummen norr om V4–V6, västra delen"),
    Tandgrupp("KA-T4", "Källaren, rummen norr om V4–V6, östra delen"),
    Tandgrupp("KA-T5", "Källaren, rummet söder om trapphallen"),
]

# dimrarna vid ingångarna, 1 050 mm över golvet: trapphallens vid trappans fot (på KL4 mellan pelarna P12 och P13),
# tvättstugans vid KD2, de två delarnas (två dimrar i en dubbelram) på V4 vid öppningen mellan V4 och V5, och rummet
# söder om trapphallen vid KD4 (väster om pelaren P11 i KL4). De dimrar drivdonen i teknikrummet: den dimrade fasen
# går i ett eget rör dit (230 V dimrad).
DIMRAR = {
    "KA-B1": Apparat("KA-B1", DIMMER_LED, _pa_kl("KL4", 7150.0, 1), styr=("KA-T1",)),
    "KA-B2": Apparat("KA-B2", DIMMER_LED, _pa_kl("KL3", 6100.0, -1), styr=("KA-T2",)),
    "KA-B3": Apparat("KA-B3", DIMMER_LED_2, kallarvagg("V4", 5150.0, Z_BRYTARE - PLAN[0], 1), styr=("KA-T3", "KA-T4")),
    "KA-B4": Apparat("KA-B4", DIMMER_LED, _pa_kl("KL4", 5500.0, -1), styr=("KA-T5",)),
}

# ljuslinjerna (../katalog.ljuslinje) per tändgrupp, matade i rörens ordning från drivdonet: id, längd, önskad mitt och
# riktning från matningens ände. Längderna: den lysande längden en multipel av 150 mm, så att listen (klippbar var
# 50 mm) räcker hela vägen och rörändarna i båda ändar ryms mellan underkantsnätets järn (c/c 150). Lägena följer
# rummen och hur de används, minst 500 mm från brandvarnarna.
LINJER: dict[str, list[tuple[str, float, tuple[float, float], tuple[float, float]]]] = {
    # trapphallen: en linje längs hallens axel från dörren KD2 mot korridoren till KD5, mitt för öppningarna mot
    # rummen norr om V4–V6, och en tvärs ned mot trappans fot, som lyser upp de nedersta stegen (väster om trapphålet
    # och brandvarnaren BV-KT); var sitt rör från drivdonet
    "KA-T1": [("KA-L01", 3080.0, (6650.0, 6650.0), (1.0, 0.0)), ("KA-L02", 1430.0, (7130.0, 5870.0), (0.0, -1.0))],
    # tvättstugan: en linje längs hallen och en över bänken längs V21 med tvätthoet, tvättmaskinen och torktumlaren
    # (över bänkens främre halva, 600 djup: ljuset på bänken framför den som står där)
    "KA-T2": [("KA-L03", 3080.0, (2400.0, 6545.0), (-1.0, 0.0)), ("KA-L04", 1580.0, (760.0, 8150.0), (0.0, 1.0))],
    # rummen norr om V4–V6: en linje mitt i vardera delen, längs rummen
    "KA-T3": [("KA-L05", 2480.0, (5920.0, 9190.0), (0.0, 1.0))],
    "KA-T4": [("KA-L06", 2480.0, (8280.0, 9190.0), (0.0, 1.0))],
    # rummet söder om trapphallen: två parallella linjer längs rummet, symmetriskt mellan V18 och KL5, på var sin sida
    # om brandvarnaren BV-KN
    "KA-T5": [("KA-L07", 3080.0, (5770.0, 2530.0), (0.0, -1.0)), ("KA-L08", 3080.0, (8070.0, 2530.0), (0.0, 1.0))],
}
_RUMMET = {"KA-T1": TRAPPHALL, "KA-T2": TVATTSTUGA, "KA-T3": RUMMEN_V2, "KA-T4": RUMMEN_V2, "KA-T5": RUMMET_KS}
_STJARNA = {"KA-L02"}                         # matas med ett eget rör från drivdonet, inte från linjen före
_R = FXP16.ytterdiameter / 2


def _bitar(ror: Sequence[Ror]) -> list[Bit]:
    """Rörens raka bitar i bjälklaget."""
    ut: list[Bit] = []
    for r in ror:
        for a, b in zip(r.via, r.via[1:]):
            if max(a[2], b[2]) > KALLARTAK - 1.0 and min(a[2], b[2]) < PLAN[1] + 1.0:
                ut.append((LineString([a[:2], b[:2]]) if math.dist(a[:2], b[:2]) > 0.5 else Point(a[:2]),
                           r.typ.ytterdiameter / 2, min(a[2], b[2]), max(a[2], b[2])))
    return ut


_KALLARENS_ROR = list(ROR)                   # källarens rör till arbetsrummens paneler och till uttagen
_KALLARENS = _bitar(_KALLARENS_ROR)


@cache
def _rorandarnas_hinder() -> Polygon:
    """Där en ljuslinjes rörände inte får stå: nära det som röret ned till taket går genom, rören i bjälklaget (plan
    1:s stråk och kedjor, tappvattnet, avloppet och källarens andra rör)."""
    return unary_union([g.buffer(_R + rr + SPEL) for g, rr, z0, _ in (*_hindren(), *_KALLARENS)
                        if z0 < BJALKLAG["MB"] + _R])


def _profilen(mitt: tuple[float, float], u: tuple[float, float], langd: float) -> Polygon:
    a = (mitt[0] - u[0] * langd / 2, mitt[1] - u[1] * langd / 2)
    b = (mitt[0] + u[0] * langd / 2, mitt[1] + u[1] * langd / 2)
    return LineString([a, b]).buffer(ASKPROFIL.bredd / 2, cap_style="flat")


def _placera(rum: Polygon, mitt: tuple[float, float], u: tuple[float, float], langd: float,
             ut: bool) -> tuple[float, float]:
    """Ljuslinjens mitt närmast den önskade (högst 150 mm därifrån), där profilen ligger i rummet och rörändan i
    matningens ände (och i den andra, ut) går mellan underkantsnätets järn och fri från rören i bjälklaget."""
    s = langd / 2 - ASKPROFIL.ror_in
    stopp = _rorandarnas_hinder()
    inne = rum.buffer(-60.0)
    for steg in range(0, 151, 5):
        for dx, dy in sorted({(sx * steg, sy * j) for sx in (-1, 1) for sy in (-1, 1) for j in range(0, steg + 1, 5)}
                             | {(sx * j, sy * steg) for sx in (-1, 1) for sy in (-1, 1) for j in range(0, steg + 1, 5)},
                             key=lambda d: math.hypot(*d)):
            c = (mitt[0] + dx, mitt[1] + dy)
            andar = [(c[0] - u[0] * s, c[1] - u[1] * s)] + ([(c[0] + u[0] * s, c[1] + u[1] * s)] if ut else [])
            if not inne.contains(_profilen(c, u, langd)) or any(stopp.contains(Point(q)) for q in andar):
                continue
            if all(fri(Point(q), _R, KALLARTAK, BJALKLAG["MB"], 5.0) for q in andar):
                return c
    raise ValueError(f"ingen plats för ljuslinjen nära ({mitt[0]:.0f}, {mitt[1]:.0f})")


def _linjerna() -> dict[str, list[Lampa]]:
    ut: dict[str, list[Lampa]] = {}
    for tand, linjer in LINJER.items():
        for i, (lid, langd, mitt, u) in enumerate(linjer):
            nasta = i + 1 < len(linjer) and linjer[i + 1][0] not in _STJARNA
            x, y = _placera(_RUMMET[tand], mitt, u, langd, nasta)
            ut.setdefault(tand, []).append(Lampa(lid, ljuslinje(langd), kallartak(x, y), tand, langs=(u[0], u[1], 0.0)))
    return ut


_T = _linjerna()
LJUSLINJERNA = [p for lampor in _T.values() for p in lampor]
_DOSORNA = [(p.lage.punkt[0], p.lage.punkt[1]) for p in PANELER]
PUNKTER += [*LJUSLINJERNA, *DIMRAR.values()]

# 24 V-kretsarna: ett drivdon per tändgrupp i drivdonsskåpet (../../teknikrum.py), dimrat av dimmerns kanal
KRETSAR = [Krets(f"LK{i + 1}", "TK-LC", i, d.id, d.styr.index(tand), tand, tuple(p.id for p in _T[tand]))
           for i, (tand, d) in enumerate((t, next(d for d in DIMRAR.values() if t in d.styr)) for t in LINJER)]


def _cellplasten(v: str, sida: int) -> float:
    """Mitt i källarväggens cellplast på sidan sida (+1 mot växande y eller x, −1 mot avtagande)."""
    w = next(q for q in K.VAGGAR if q.namn == v)
    return w.c + sida * (K.KARNA / 2 + K.CELL / 2)


def _ur_cellplasten(v: str, sida: int, s_: Sequence[float], z: float) -> list[tuple[Vek, Vek]]:
    """Lodräta rör mellan bjälklaget (elrörens undre nivå) och höjden z i källarväggens cellplast, sida vid sida vid
    s_ längs väggen, förskjutna lika mycket längs väggen (och högst 30 mm tvärs) så att de går mellan
    underkantsnätets järn: per rör (punkten i bjälklaget, punkten i väggen)."""
    w = next(q for q in K.VAGGAR if q.namn == v)
    c = _cellplasten(v, sida)
    langs = (1.0, 0.0) if w.riktning == "h" else (0.0, 1.0)
    pts = [(s, c) if w.riktning == "h" else (c, s) for s in s_]
    dx, dy = mellan_jarnen(pts, KALLARTAK, BJALKLAG["MB-UK"], FXP16.ytterdiameter / 2, langs=langs, tvars=30.0)
    return [((x + dx, y + dy, BJALKLAG["MB-UK"]), (x + dx, y + dy, z)) for x, y in pts]


# rören upp ur dimrarnas dosor in i bjälklaget, sida vid sida: in (matningen), ut (till nästa dimmer) och den dimrade
# fasen till drivdonet
_D = DIMRAR
_U1 = upp_ur_vaggen(_D["KA-B1"], (-40.0, 0.0, 40.0))         # till KA-B2, från KA-B4, dimrad till drivdonet
_U2 = upp_ur_vaggen(_D["KA-B2"], (0.0, 40.0, 80.0))          # från KA-B1, till KA-B3, dimrad till drivdonet (norrut):
#                                                              norr om golvvärmens matarledningar VS1 under taket
_U4 = upp_ur_vaggen(_D["KA-B4"], (-40.0, 0.0, 40.0))         # från KA-B7, dimrad till drivdonet, till KA-B1
_U7B = upp_ur_vaggen(_B7, (60.0,))[0]                        # från KA-B7 till KA-B4
_X3 = _D["KA-B3"].lage.punkt[0]
_U3 = _ur_cellplasten("V4", 1, (_X3, _X3 + 40.0), _D["KA-B3"].lage.punkt[2])   # från KA-B2, dimrad till drivdonet

_NYA: list[Ror] = []                     # de trevliga rummens rör hittills (de senare går fria från dem)
_PUNKT = {p.id: p for p in PUNKTER}
NARA_DOSAN = 150.0                       # rör som möts i en punkt får gå närmare varandra så nära den (i plan)


def _rorandar(utom: set[str]) -> list[Bit]:
    """Ljuslinjernas rörändar (röret lodrätt ned till taket) som andra rör ska gå fria från, utom punkternas i utom."""
    ut: list[Bit] = []
    for p in LJUSLINJERNA:
        if p.id not in utom:
            for q in (anslutning(p), anslutning(p, ut=True)):
                ut.append((Point(q[0], q[1]), _R, KALLARTAK, BJALKLAG["MB"] + _R))
    return ut


def _andra(fran: str, till: str) -> list[Bit]:
    """Det i bjälklaget som ett nytt rör mellan fran och till ska gå fritt från: källarens andra rör (de som går till
    samma punkt utom nära den, där de möts i dosan) och ljuslinjernas rörändar."""
    nara = {q: Point(*anslutning(_PUNKT[q])[:2]) for q in {fran, till} if q in _PUNKT}
    ut: list[Bit] = []
    for r in (*_KALLARENS_ROR, *_NYA):
        delade = [nara[q] for q in {r.fran, r.till} & set(nara)]
        ut += [b for b in _bitar([r]) if not any(b[0].distance(c) < NARA_DOSAN for c in delade)]
    return ut + _rorandar({fran, till})


def _i_nivaer(pts: Sequence[tuple[float, float]], nivaer: Sequence[str], andra: Sequence[Bit],
              namn: str) -> tuple[Vek, ...]:
    """Röret i bjälklaget genom punkterna i de givna nivåerna (en per sträcka, lodrätt emellan där nivån byts),
    prövat mot andra och järnen; nivån byts bara där golvvärmens stråk inte går (se ROR)."""
    ut: list[Vek] = []
    for (a, b), niva in zip(zip(pts, pts[1:]), nivaer, strict=True):
        z = BJALKLAG[niva]
        if math.dist(a, b) > 0.5 and not _fritt([a, b], z, andra):
            raise ValueError(f"{namn}: sträckan ({a[0]:.0f}, {a[1]:.0f})–({b[0]:.0f}, {b[1]:.0f}) i {niva} är inte fri")
        if not ut or abs(ut[-1][2] - z) > 0.5:
            ut.append((a[0], a[1], z))
        ut.append((b[0], b[1], z))
    return tuple(ut)


def _dra(id_: str, fran: str, till: str, fore: Sequence[Vek], pts: Sequence[tuple[float, float]],
         efter: Sequence[Vek] = (), slag: str = "230 V", nivaer: Sequence[str] | None = None) -> Ror:
    """Röret från fran till till: fore (i väggen), i bjälklaget genom punkterna pts och efter (ned i väggen). Utan
    nivaer i elrörens undre nivå där den är fri (från källarens andra rör), annars den övre; med nivaer i dem."""
    plan = [q for i, q in enumerate(pts) if i == 0 or math.dist(q, pts[i - 1]) > 0.5]
    andra = _andra(fran, till)
    if nivaer is None:
        egna = [q for q in _DOSORNA if min(math.dist(q, plan[0]), math.dist(q, plan[-1])) > 1.0]
        mitt = i_bjalklaget(plan, andra, egna)
    else:
        mitt = _i_nivaer(plan, nivaer, andra, id_)
    r = Ror(id_, FXP16, fran, till, via=_utan_upprepade((*fore, *mitt, *efter)), slag=slag)
    _NYA.append(r)
    return r


def _utan_upprepade(via: Sequence[Vek]) -> tuple[Vek, ...]:
    ut: list[Vek] = []
    for q in via:
        if not ut or math.dist(q, ut[-1]) > 0.5:
            ut.append(q)
    return tuple(ut)


def _xy_ror(p: Lampa, ut: bool = False) -> tuple[float, float]:
    """Ljuslinjens rörände i plan (matningens, eller ut: den andra)."""
    q = anslutning(p, ut)
    return q[0], q[1]


# Nivåerna: drivdonsskåpets rör (24 V och de dimrade) går i elrörens undre nivå hela vägen, under golvvärmens stråk
# från fördelaren GV1 västerut över trapphallen och tvättstugans hall (y 6 725–7 075) och under stråket S; matningens
# rör mellan dimrarna (G18) går i den övre där de korsar dem. Nivån byts bara utanför golvvärmens stråk: vid väggarnas
# stigare och för G18-R5 vid X_TILL_V4, Y_BYT (mellan stråken), så att inga lodräta rör går genom dem (golvvärmens
# slingor går runt de lodräta rören, stråken inte).
_Y_SODER_P11 = 4600.0       # matningen från KA-B4 till KA-B1: söder om pelarna P11 och P12 i KL4
_Y_LANDNING = 5500.0        # matningen från KA-B1 till KA-B2: över trapphallens västra del, söder om pelaren P6
_X_KL3_OST = 4800.0         # och norrut öster om pelaren P10 (KL1, KL3) till tvättstugans dimmer
_X_TILL_V4 = 4850.0         # matningen från KA-B2 till KA-B3: norrut längs KL3 till V4
_Y_BYT = 7300.0             # där matningen till KA-B3 byter nivå, mellan golvvärmens stråk
_X_G18_BYT = 5700.0         # där matningen till KA-B2 byter nivå: väster om allrummets rör G02-R2 (x 5 847) och
#                             trapphålets diagonaljärn, som stänger den övre nivån

ROR += [
    # matningen (G18) från det östra lilla rummets brytare vidare till dimrarna i tur och ordning
    _dra("G18-R2", "KA-B7", "KA-B4", _fran(_U7B)[:1], [_xy(_U7B), (_xy(_U7B)[0], _xy(_U4[0])[1]), _xy(_U4[0])],
         _till(_U4[0])[1:], nivaer=("MB", "MB")),
    _dra("G18-R3", "KA-B4", "KA-B1", _fran(_U4[2])[:1],
         [_xy(_U4[2]), (_xy(_U4[2])[0], _Y_SODER_P11), (_xy(_U1[1])[0], _Y_SODER_P11), _xy(_U1[1])],
         _till(_U1[1])[1:], nivaer=("MB-UK", "MB-UK", "MB-UK")),
    _dra("G18-R4", "KA-B1", "KA-B2", _fran(_U1[0])[:1],
         [_xy(_U1[0]), (_xy(_U1[0])[0], _Y_LANDNING), (_X_G18_BYT, _Y_LANDNING), (_X_KL3_OST, _Y_LANDNING),
          (_X_KL3_OST, _xy(_U2[0])[1]), _xy(_U2[0])], _till(_U2[0])[1:], nivaer=("MB-UK", "MB-UK", "MB", "MB", "MB")),
    _dra("G18-R5", "KA-B2", "KA-B3", _fran(_U2[1])[:1],
         [_xy(_U2[1]), (_X_TILL_V4, _xy(_U2[1])[1]), (_X_TILL_V4, _Y_BYT), (_X_TILL_V4, _U3[0][0][1]),
          _U3[0][0][:2]], (_U3[0][1],), nivaer=("MB", "MB", "MB-UK", "MB-UK")),
]

# rören mellan drivdonsskåpet och rummen: rakt upp ur skåpets ovansida, söderut i bjälklaget och österut i ett band
# över tvättstugans hall in i trapphallen, där vart och ett viker av mot sin dimmer eller ljuslinje; bandet i ordning
# från norr, så att inget rör korsar ett annat i bandet: de som viker av norrut först ytterst i norr, de som viker av
# söderut först ytterst i söder
_LC_TOPP = DRIVDONSSKAP.anslutningar["topp"]
X_STIGARE_MIN = 21.0                         # stigarnas avstånd över skåpet (Ø16, 5 mm emellan)


def _skapets_stigare(n: int) -> list[float]:
    """Stigarnas x över drivdonsskåpet (en rad mitt på ovansidan), från skåpets östra del västerut, fria från järnen
    från källarens tak till elrörens undre nivå."""
    ut: list[float] = []
    x = _LC_TOPP[0] + DRIVDONSSKAP.matt[0] / 2 - 30.0
    while len(ut) < n and x > _LC_TOPP[0] - DRIVDONSSKAP.matt[0] / 2 + 30.0:
        if (not ut or ut[-1] - x >= X_STIGARE_MIN - 1e-6) and fri(Point(x, _LC_TOPP[1]), _R, KALLARTAK,
                                                                     BJALKLAG["MB-UK"], 5.0):
            ut.append(x)
        x -= 1.0
    if len(ut) < n:
        raise ValueError(f"bara {len(ut)} stigare ryms över drivdonsskåpet, {n} behövs")
    return ut


_ORDNING = ["KA-B3", "LK3", "LK4", "KA-B1", "LK1b", "KA-B4", "LK1", "LK5", "KA-B2", "LK2"]   # från norr
Y_BAND, CC_BAND = 7170.0, 40.0               # det nordligaste rörets y i bandet, och avståndet mellan rören
_X_STIG = dict(zip(_ORDNING, _skapets_stigare(len(_ORDNING))))
_Y = {k: Y_BAND - i * CC_BAND for i, k in enumerate(_ORDNING)}
_X_LK5 = 4680.0                              # 24 V till rummet söder om trapphallen: söderut mellan KL3 och G18-R4
X_TVATT_VAST = 650.0                         # tvättstugans två linjer: röret mellan dem norrut vid x 650, väster om
#                                              tappvattnets två rör till badrummet (y 6 915 och 6 975, som går västerut
#                                              till x 723 strax över den undre nivån)


def _bandet(k: str, mal: Sequence[tuple[float, float]]) -> list[tuple[float, float]]:
    """Från skåpets stigare k söderut till bandet, österut i det och vidare genom mal (i plan)."""
    x = _X_STIG[k]
    return [(x, _LC_TOPP[1]), (x, _Y[k]), (mal[0][0], _Y[k]), *mal]


def _upp(k: str) -> Vek:
    """Stigarens punkt på drivdonsskåpets ovansida."""
    return (_X_STIG[k], _LC_TOPP[1], _LC_TOPP[2])


def _undre(pts: Sequence[tuple[float, float]]) -> tuple[str, ...]:
    return ("MB-UK",) * (len([q for i, q in enumerate(pts) if i == 0 or math.dist(q, pts[i - 1]) > 0.5]) - 1)


def _matning(k: str, rid: str, p: Lampa, mal: Sequence[tuple[float, float]] = ()) -> Ror:
    """24 V från drivdonet (stigaren k) till ljuslinjens rörände, genom mal."""
    q = _xy_ror(p)
    pts = _bandet(k, [*(mal or [(q[0], _Y[k])]), q])
    return _dra(rid, "TK-LC", p.id, (_upp(k),), pts, slag="24 V", nivaer=_undre(pts))


def _dimrad(k: str, rid: str, dimmer: str, ur: tuple[Vek, Vek], mal: Sequence[tuple[float, float]] = ()) -> Ror:
    """Den dimrade fasen från dimmern (ur: punkten i väggen, punkten i bjälklaget) till drivdonsskåpet (stigaren k)."""
    pts = _bandet(k, [*mal, ur[1][:2]])[::-1]
    return _dra(rid, dimmer, "TK-LC", (ur[0],), pts, (_upp(k),), slag="230 V dimrad", nivaer=_undre(pts))


def _kedjan(rid: str, a: Lampa, b: Lampa, pts: Sequence[tuple[float, float]]) -> Ror:
    """24 V från ljuslinjen a:s andra ände till ljuslinjen b:s matning, genom pts."""
    hela = [_xy_ror(a, ut=True), *pts, _xy_ror(b)]
    return _dra(rid, a.id, b.id, (), hela, slag="24 V", nivaer=_undre(hela))


T1, T2, T3, T4, T5 = (_T[t] for t in LINJER)
ROR += [
    # den dimrade fasen från varje dimmer till drivdonsskåpet, i eget rör
    _dimrad("KA-B1", "KA-B1-LC", "KA-B1", _U1[2]),
    _dimrad("KA-B2", "KA-B2-LC", "KA-B2", _U2[2]),
    _dimrad("KA-B3", "KA-B3-LC", "KA-B3", (_U3[1][1], _U3[1][0])),
    _dimrad("KA-B4", "KA-B4-LC", "KA-B4", _U4[1]),
    # 24 V från drivdonen till ljuslinjerna: från skåpet till den första linjen i varje tändgrupp (trapphallens båda),
    # och därifrån till nästa
    _matning("LK1", "LK1-1", T1[0]),
    _matning("LK1b", "LK1-2", T1[1]),
    _matning("LK2", "LK2-1", T2[0]),
    _matning("LK3", "LK3-1", T3[0]),
    _matning("LK4", "LK4-1", T4[0]),
    _matning("LK5", "LK5-1", T5[0], [(_X_LK5, _Y["LK5"]), (_X_LK5, _xy_ror(T5[0])[1])]),
    _kedjan("LK2-2", T2[0], T2[1], [(X_TVATT_VAST, _xy_ror(T2[0], ut=True)[1]), (X_TVATT_VAST, _xy_ror(T2[1])[1])]),
    _kedjan("LK5-2", T5[0], T5[1], []),
]
