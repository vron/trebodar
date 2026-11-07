"""Källaren (#51): belysningen efter användarens indelning av rummen, 3000 K i hela källaren.

- De trevliga rummen (vardagsbruk): infällda spotar SG Armaturen Junistar Tube Round (djupt försänkt ljuskälla, UGR
  < 19, 36°) ingjutna i betongtaket i SG:s ingjutningshus, i ett jämnt rutnät (c/c RUTNAT) i rummet. Rummen och hur
  de motsvarar modellens (antaget, ärende #51):
  - rummet där man kommer ned för trappan: trapphallen mellan KL3, KL4 och V4–V6;
  - tvättstugan: den västra delen av rummet vid V3 (väster om KL8, där teknikrummet kan få en vägg) och rummet söder
    om den mellan KL1 och KL8;
  - de två små rummen i sydväst: rummet norr om V4–V6 mellan V19, V2 och V15, belyst som två halvor (rummet har
    ingen vägg emellan i modellen);
  - det relativt stora rummet nordost om trappan: rummet mellan KL3, KL4 och KL5.
- Arbetsrummen (kostnaden styr): tunna utanpåliggande LED-paneler LEDVANCE PANEL COMPACT 600, var och en med en
  ingjuten dosa ovanför sig: det stora rummet i den högra huskroppen och de två små rummen mellan KL1 och V7.
- Teknikrummet (den östra delen av rummet vid V3) får ingen belysning nu.

Spotarnas ingjutningshus (Ø185, 111 högt) tar nästan hela bjälklaget, så de står fria från tappvattnets och elens
rör i bjälklaget, avloppet genom det, ventilationens kanaler under taket och genomstansningszonerna runt rören
(6d = 720 mm, K-05), och golvvärmen går runt dem; järnen läggs om runt dem. Brytarna sitter vid dörrarna, 1 050 mm
över golvet; rören går från brytaren upp i väggen in i bjälklaget och i elrörens nivå mellan spotarna (ingjutna).

Koordinater i mm (K-05), z från plan 1:s golv (källarens golv z −2 250).
"""
from __future__ import annotations

import math
from collections.abc import Sequence
from functools import cache

from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

from trebodar.hus.grund.pelare import PELARE

from ...avlopp.ledningar import golvbrunnar, ledningar as avloppets
from ...montering import BJALKLAG, KALLARTAK, PLAN, Montering, Vek, kallartak
from ...vatten.system import vatten
from ...ventilation.system import ventilation
from .. import kedjor
from ..bjalklag import mellanbjalklag
from ...strak import mellan_jarnen
from ..katalog import BRYTARE_1, DIMMER_1, DIMMER_2, FXP16, JUNISTAR_TUBE_ROUND, PANEL_600
from ..punkter import Apparat, Lampa, Ror, Rum, Tandgrupp

RUM = Rum("KA", "Källare", plan=0)
NAMN = RUM.namn

RUTNAT = 1200.0                 # spotarnas avstånd: jämnt ljus på golvet med 36° strålvinkel och 2,1 m takhöjd
FRAN_VAGG = 450.0               # spotarna minst så långt från väggarna
HUS_R = 175.0                   # ingjutningshusets största radie från spotens mitt (med drivdonets del)
SPEL = 25.0                     # fritt mellan husen och rören
GENOMSTANSNING = 720.0 + 92.5   # husets kammare utanför rörens genomstansningszon (6d)
Z_BRYTARE = PLAN[0] + 1050.0
Z_I_BJALKLAGET = BJALKLAG["MB"]
Z_I_VAGG = KALLARTAK - 60.0          # rören mellan brytarna i väggarna, strax under taket

# rummen (golvets yta innanför väggarnas gips); källarväggarna: kärnan 150, cellplast 100 och gips 13 på var sida
_V = 75.0 + 100.0 + 13.0
_KL = 47.5 + 13.0
TRAPPHALL = box(4531.0 + _KL, 4990.0 + _KL, 9645.0 - _KL, 7515.0 - _V).difference(
    box(7270.0, 4900.0, 9800.0, 5950.0 + _KL))                                 # utan trappan mellan KL4 och KL6
TVATTSTUGA = unary_union([box(145.0 + _V, 5820.0 + _KL, 2400.0, 9205.0 - _V),
                          box(2400.0, 5820.0 + _KL, 4531.0 - _KL, 7266.5 - _KL)])
SMA_RUMMEN = box(4545.0 + _V, 7515.0 + _V, 9645.0 - _V, 10865.0 - _V)
RUMMET_NO = unary_union([box(4645.0 + _V, 145.0 + _V, 9070.0 - _KL, 4990.0 - _KL),
                         box(4531.0 + _KL, 3923.0, 4645.0 + _V, 4990.0 - _KL)])
STORA_RUMMET = unary_union([box(9645.0 + _V, 1145.0 + _V, 13665.0 - _V, 12365.0 - _V),
                            box(9070.0 + _KL, 1145.0 + _V, 9645.0 + _V, 5037.5)])
SMA_V = box(145.0 + _V, 3735.0 + _V, 2800.0 - _KL, 5820.0 - _KL)
SMA_O = box(2800.0 + _KL, 3735.0 + _V, 4531.0 - _KL, 5820.0 - _KL)


def _ror_i_bjalklaget() -> list[tuple[LineString | Point, float]]:
    """Det som går i eller genom mellanbjälklaget och som husen ska gå fria från: tappvattnets och elens rör (elens
    utom källarens egna), avloppet genom bjälklaget och golvbrunnarna i det, i plan med sin radie."""
    ut: list[tuple[LineString | Point, float]] = []
    v = vatten()
    segment = [(a, b, r.typ.yttre / 2) for r in v.ror.values() for a, b in zip(v.vag(r), v.vag(r)[1:])]
    segment += [(a, b, r.typ.ytterdiameter / 2) for r in (*mellanbjalklag.ROR, *kedjor.ROR)
                for a, b in zip(r.via, r.via[1:])]
    segment += [(a, b, led.d / 2) for led in avloppets().values() for a, b in zip(led.vag, led.vag[1:])]
    for a, b, r in segment:
        if max(a[2], b[2]) > KALLARTAK - 1.0 and min(a[2], b[2]) < PLAN[1] + 1.0:
            ut.append((LineString([a[:2], b[:2]]) if math.dist(a[:2], b[:2]) > 1.0 else Point(a[:2]), r))
    ut += [(Point(x, y), d / 2) for x, y, d, z in golvbrunnar().values() if z > KALLARTAK]
    return ut


@cache
def _hinder() -> Polygon:
    """Där en spots mitt inte får stå: nära rören i bjälklaget, under ventilationens kanaler och inom rörens
    genomstansningszon."""
    delar = [g.buffer(HUS_R + r + SPEL) for g, r in _ror_i_bjalklaget()]
    vent = ventilation()
    for g in (vent.grenar.values() if isinstance(vent.grenar, dict) else vent.grenar):
        for s in vent.stycken(g):
            if min(s.a[2], s.b[2]) < KALLARTAK - 1.0:
                linje = LineString([s.a[:2], s.b[:2]]) if math.dist(s.a[:2], s.b[:2]) > 1.0 else Point(s.a[:2])
                delar.append(linje.buffer(HUS_R + s.bredd / 2 + SPEL))
    delar += [Point(x, y).buffer(GENOMSTANSNING) for x, y in PELARE.values()]
    return unary_union(delar)


def rutnat(rum: Polygon, steg: float = RUTNAT, fran_vagg: float = FRAN_VAGG) -> list[tuple[float, float]]:
    """Spotarnas lägen i rummet: ett rutnät c/c steg, förskjutet (i steg om 50 mm) så att flest punkter hamnar i
    rummet minst fran_vagg från väggarna och utanför hindren; punkterna i rader från söder, varannan rad baklänges."""
    inne = rum.buffer(-fran_vagg, join_style="mitre").difference(_hinder())
    x0, y0, x1, y1 = rum.bounds
    bast: list[tuple[float, float]] = []
    for dx in range(0, int(steg), 50):
        for dy in range(0, int(steg), 50):
            p = [(x0 + dx + i * steg, y0 + dy + j * steg) for j in range(int((y1 - y0) // steg) + 2)
                 for i in range(int((x1 - x0) // steg) + 2)]
            p = [q for q in p if inne.contains(Point(q))]
            if len(p) > len(bast):
                bast = p
    rader: dict[float, list[tuple[float, float]]] = {}
    for q in bast:
        rader.setdefault(q[1], []).append(q)
    ut: list[tuple[float, float]] = []
    for i, y in enumerate(sorted(rader)):
        ut += sorted(rader[y], reverse=i % 2 == 1)
    return ut


def _spotar(rum: Polygon, start: int, tand: str) -> list[Lampa]:
    return [Lampa(f"KA-L{start + i:02d}", JUNISTAR_TUBE_ROUND, kallartak(x, y), tand)
            for i, (x, y) in enumerate(rutnat(rum))]


def _paneler(lagen: Sequence[tuple[float, float]], start: int, tand: str) -> list[Lampa]:
    return [Lampa(f"KA-L{start + i:02d}", PANEL_600, kallartak(x, y), tand) for i, (x, y) in enumerate(lagen)]


def _vagg(namn: str, x: float, y: float, normal: tuple[float, float]) -> Montering:
    """På en källarväggs gips (x, y på ytan), 1 050 mm över golvet."""
    return Montering((x, y, Z_BRYTARE), (normal[0], normal[1], 0.0), "vagg", namn)


TANDGRUPPER = [
    Tandgrupp("KA-T1", "Källaren, trapphallen"),
    Tandgrupp("KA-T2", "Källaren, tvättstugan"),
    Tandgrupp("KA-T3", "Källaren, de två små rummen, västra halvan"),
    Tandgrupp("KA-T4", "Källaren, de två små rummen, östra halvan"),
    Tandgrupp("KA-T5", "Källaren, rummet nordost om trappan"),
    Tandgrupp("KA-T6", "Källaren, det stora rummet", dimbar=False),
    Tandgrupp("KA-T7", "Källaren, de små rummen mellan KL1 och V7", dimbar=False),
]

_X_MITT = (SMA_RUMMEN.bounds[0] + SMA_RUMMEN.bounds[2]) / 2
_x0, _y0, _x1, _y1 = STORA_RUMMET.bounds
_PANELER_STORA = [(x, y) for y in (_y0 + 1500.0, (_y0 + _y1) / 2, _y1 - 1500.0)
                  for x in (9832.5 + (_x1 - 9832.5) * 0.28, 9832.5 + (_x1 - 9832.5) * 0.72)]
_LAMPOR = [
    ("KA-T1", TRAPPHALL),
    ("KA-T2", TVATTSTUGA),
    ("KA-T3", SMA_RUMMEN.intersection(box(0.0, 0.0, _X_MITT, 1e6))),
    ("KA-T4", SMA_RUMMEN.intersection(box(_X_MITT, 0.0, 1e6, 1e6))),
    ("KA-T5", RUMMET_NO),
]


def _alla_lampor() -> list[Lampa]:
    ut: list[Lampa] = []
    for tand, rum in _LAMPOR:
        ut += _spotar(rum, len(ut) + 1, tand)
    ut += _paneler(_PANELER_STORA, len(ut) + 1, "KA-T6")
    ut += _paneler([SMA_V.centroid.coords[0], SMA_O.centroid.coords[0]], len(ut) + 1, "KA-T7")
    return ut


LAMPOR = _alla_lampor()

PUNKTER = [
    *LAMPOR,
    Apparat("KA-B1", DIMMER_1, _vagg("KL4", 7180.0, 4990.0 + _KL, (0.0, 1.0)), styr=("KA-T1",)),
    Apparat("KA-B2", DIMMER_1, _vagg("KL3", 4531.0 - _KL, 6100.0, (-1.0, 0.0)), styr=("KA-T2",)),
    Apparat("KA-B3", DIMMER_2, _vagg("V4", 5100.0, 7515.0 + _V, (0.0, 1.0)), styr=("KA-T3", "KA-T4")),
    Apparat("KA-B4", DIMMER_1, _vagg("KL4", 6850.0, 4990.0 - _KL, (0.0, -1.0)), styr=("KA-T5",)),
    Apparat("KA-B5", BRYTARE_1, _vagg("KL7", 9645.0 + _KL, 6300.0, (1.0, 0.0)), styr=("KA-T6",)),
    Apparat("KA-B6", BRYTARE_1, _vagg("KL1", 1700.0, 5820.0 - _KL, (0.0, -1.0)), styr=("KA-T7",)),
]


def _ner_i_vaggen(p: Apparat, z_bjalklag: float) -> tuple[Vek, ...]:
    """Från brytaren upp i väggen (KL-väggarnas regelfack, källarväggarnas cellplast bakom gipsen) in i bjälklaget
    till nivån z_bjalklag, mellan underkantsnätets järn: brytaren sitter på väggens gips, röret i väggen bakom."""
    m = p.lage
    inne = 60.0 if m.ref.startswith("KL") else 13.0 + 50.0           # regelfackets eller cellplastens mitt
    x, y = m.punkt[0] - m.normal[0] * inne, m.punkt[1] - m.normal[1] * inne
    langs = (abs(m.normal[1]), abs(m.normal[0]))
    dx, dy = mellan_jarnen([(x, y)], KALLARTAK, z_bjalklag, 8.0, langs=langs, tvars=0.0)
    return (x + dx, y + dy, m.punkt[2]), (x + dx, y + dy, z_bjalklag)


def _ordning(lampor: Sequence[Lampa], start: tuple[float, float]) -> list[Lampa]:
    """Lamporna rad för rad, raden närmast start först, varje rad från änden närmast den förra lampan."""
    rader: dict[float, list[Lampa]] = {}
    for l in lampor:
        rader.setdefault(round(l.lage.punkt[1]), []).append(l)
    ut: list[Lampa] = []
    p = start
    kvar = dict(rader)
    while kvar:
        y = min(kvar, key=lambda yy: (abs(yy - p[1]), min(abs(l.lage.punkt[0] - p[0]) for l in kvar[yy])))
        rad = sorted(kvar.pop(y), key=lambda l: l.lage.punkt[0])
        if abs(rad[-1].lage.punkt[0] - p[0]) < abs(rad[0].lage.punkt[0] - p[0]):
            rad.reverse()
        ut += rad
        p = (rad[-1].lage.punkt[0], rad[-1].lage.punkt[1])
    return ut


@cache
def _nivaernas_ror() -> dict[float, list[tuple[LineString, float]]]:
    """Rören som går vågrätt i elrörens nivåer: tappvattnet i den undre (MB-UK) och elens stråk i den övre (MB)."""
    v = vatten()
    undre = [(LineString([a[:2], b[:2]]), r.typ.yttre / 2) for r in v.ror.values()
             for a, b in zip(v.vag(r), v.vag(r)[1:])
             if abs(a[2] - b[2]) < 1.0 and abs(a[2] - BJALKLAG["MB-UK"]) < 30.0 and math.dist(a[:2], b[:2]) > 1.0]
    undre += [(LineString([a[:2], b[:2]]), r.typ.ytterdiameter / 2) for r in (*mellanbjalklag.ROR, *kedjor.ROR)
              for a, b in zip(r.via, r.via[1:])
              if abs(a[2] - BJALKLAG["MB-UK"]) < 1.0 and abs(b[2] - BJALKLAG["MB-UK"]) < 1.0
              and math.dist(a[:2], b[:2]) > 1.0]
    ovre = [(LineString([a[:2], b[:2]]), r.typ.ytterdiameter / 2) for r in (*mellanbjalklag.ROR, *kedjor.ROR)
            for a, b in zip(r.via, r.via[1:])
            if abs(a[2] - BJALKLAG["MB"]) < 1.0 and abs(b[2] - BJALKLAG["MB"]) < 1.0 and math.dist(a[:2], b[:2]) > 1.0]
    return {BJALKLAG["MB-UK"]: undre, BJALKLAG["MB"]: ovre}


def _fri_niva(linje: LineString) -> float:
    """Elrörens nivå för ett stycke i bjälklaget: den undre om den är fri från tappvattnet (och hällens rör), annars
    den övre om den är fri från elens stråk, annars den undre."""
    for z in (BJALKLAG["MB-UK"], BJALKLAG["MB"]):
        if all(linje.distance(g) >= 8.0 + r + 5.0 for g, r in _nivaernas_ror()[z]):
            return z
    return BJALKLAG["MB-UK"]


def _l_vag(a: Vek, b: Vek, andra: Sequence[tuple[float, float]], forst_y: bool = False) -> tuple[Vek, ...]:
    """Vägen i bjälklaget från a till b i en vinkel (först i x eller först i y, det som går fritt från de andra
    spotarnas hus; forst_y: helst först i y), på den nivå som är fri (_fri_niva), med lodräta stycken i a och b."""
    hornen = [(a[0], b[1]), (b[0], a[1])] if forst_y else [(b[0], a[1]), (a[0], b[1])]
    for h in hornen:
        linje = LineString([a[:2], h, b[:2]])
        if not any(linje.distance(Point(c)) < HUS_R + 8.0 + SPEL for c in andra):
            break
    else:
        h = hornen[0]
    z = _fri_niva(LineString([a[:2], h, b[:2]]))
    return (a[0], a[1], z), (h[0], h[1], z), (b[0], b[1], z)


def _gren(namn: str, fran: str, borjan: tuple[Vek, ...], lampor: Sequence[Lampa], forst_y: bool = False
          ) -> list[Ror]:
    """Rören från punkten fran genom borjan (väggen och upp i bjälklaget) till lamporna i tur och ordning, ingjutna i
    bjälklaget i vinklar fria från de andra spotarnas hus."""
    alla = [(l.lage.punkt[0], l.lage.punkt[1]) for l in LAMPOR]
    ut: list[Ror] = []
    a, f = borjan[-1], fran
    via: tuple[Vek, ...] = borjan[:-1]
    for i, l in enumerate(lampor):
        b = (l.lage.punkt[0], l.lage.punkt[1], a[2])
        andra = [c for c in alla if math.dist(c, b[:2]) > 1.0 and math.dist(c, a[:2]) > 1.0]
        ut.append(Ror(f"{namn}{i + 1}", FXP16, f, l.id, via=(*via, *_l_vag(a, b, andra, forst_y and i == 0))))
        a, f, via = b, l.id, ()
    return ut


def _vaggvag(brytare: Apparat, vagen: Sequence[tuple[float, float]], z_bjalklag: float = BJALKLAG["MB-UK"]
             ) -> tuple[Vek, ...]:
    """Från brytaren upp i väggen till strax under taket, längs väggarna genom vagen (i plan) och upp i bjälklaget
    vid den sista punkten."""
    upp = _ner_i_vaggen(brytare, Z_I_VAGG)
    x, y = vagen[-1]
    return (upp[0], upp[1], *((a, b, Z_I_VAGG) for a, b in vagen), (x, y, z_bjalklag))


_BRYTARE = {p.id: p for p in PUNKTER if isinstance(p, Apparat)}
_T = {t.id: [l for l in LAMPOR if l.tand == t.id] for t in TANDGRUPPER}


def _rakt(brytare: str, tand: str, namn: str) -> list[Ror]:
    """Från brytaren rakt upp i bjälklaget och till tändgruppens lampor rad för rad, först bort från väggen."""
    b = _BRYTARE[brytare]
    upp = _ner_i_vaggen(b, BJALKLAG["MB-UK"])
    return _gren(namn, brytare, upp, _ordning(_T[tand], upp[-1][:2]), forst_y=abs(b.lage.normal[1]) > 0.5)


# de två små rummen och det stora rummets norra rad: tappvattnets och elens rör i bjälklaget (stråket O, elens stråk E
# och rören till ön och hällen) ligger mellan brytaren och lamporna, så rören går dit i väggarnas cellplast (V4, V19,
# V20 och KL7, V15) och upp i bjälklaget vid raden
_EPS_V19 = 4545.0 + 75.0 + 50.0                  # mitt i V19:s och V20:s cellplast mot rummet
_EPS_V4 = 7515.0 + 75.0 + 50.0                   # mitt i V4:s cellplast mot rummet
_EPS_V15 = 9645.0 + 75.0 + 50.0
_rad = {t: sorted(_T[t], key=lambda l: (l.lage.punkt[1], l.lage.punkt[0])) for t in ("KA-T3", "KA-T4", "KA-T6")}


def _y(lampor: Sequence[Lampa]) -> list[float]:
    return sorted({round(l.lage.punkt[1]) for l in lampor})


def _norra(tand: str, y: float) -> list[Lampa]:
    return [l for l in _rad[tand] if round(l.lage.punkt[1]) == y]


_B3, _B5 = _BRYTARE["KA-B3"], _BRYTARE["KA-B5"]
_x3 = _B3.lage.punkt[0]
_t3, _t4 = _y(_T["KA-T3"]), _y(_T["KA-T4"])
ROR: list[Ror] = [
    *_rakt("KA-B1", "KA-T1", "KA-R1-"),
    *_rakt("KA-B2", "KA-T2", "KA-R2-"),
    *_gren("KA-R3A-", "KA-B3", _vaggvag(_B3, [(_x3, _EPS_V4), (_EPS_V19 - 35.0, _EPS_V4),
                                                (_EPS_V19 - 35.0, _t3[0])]), _norra("KA-T3", _t3[0])),
    *_gren("KA-R3B-", "KA-B3", _vaggvag(_B3, [(_x3 + 20.0, _EPS_V4), (_EPS_V19 - 12.0, _EPS_V4),
                                                (_EPS_V19 - 12.0, _t3[-1])]), _norra("KA-T3", _t3[-1])),
    *_gren("KA-R4A-", "KA-B3", _vaggvag(_B3, [(_x3 + 40.0, _EPS_V4), (_EPS_V19 + 11.0, _EPS_V4),
                                                (_EPS_V19 + 11.0, _t4[0] + 200.0)]),
           sorted(_norra("KA-T4", _t4[0]), key=lambda l: l.lage.punkt[0])),
    *_gren("KA-R4B-", "KA-B3", _vaggvag(_B3, [(_x3 + 60.0, _EPS_V4), (_EPS_V19 + 34.0, _EPS_V4),
                                                (_EPS_V19 + 34.0, _t4[-1] + 200.0)]),
           sorted(_norra("KA-T4", _t4[-1]), key=lambda l: l.lage.punkt[0])),
    *_rakt("KA-B4", "KA-T5", "KA-R5-"),
    *_gren("KA-R6A-", "KA-B5", _ner_i_vaggen(_B5, BJALKLAG["MB-UK"]),
           _ordning([l for l in _T["KA-T6"] if l.lage.punkt[1] < 9000.0], (_B5.lage.punkt[0], _B5.lage.punkt[1]))),
    *_gren("KA-R6B-", "KA-B5", _vaggvag(_B5, [(9645.0, _B5.lage.punkt[1]), (9645.0, 7515.0 - 60.0),
                                                (_EPS_V15, 7515.0 - 60.0), (_EPS_V15, _y(_T["KA-T6"])[-1])]),
           sorted(_norra("KA-T6", _y(_T["KA-T6"])[-1]), key=lambda l: l.lage.punkt[0])),
    *_rakt("KA-B6", "KA-T7", "KA-R7-"),
]


def _i_vaggarna(a: Apparat, b: Apparat, n: int, vagen: Sequence[tuple[float, float]], z: float = Z_I_VAGG) -> Ror:
    """Röret mellan två brytare i källarens väggar, strax under taket: upp i a:s vägg, genom vägarna i plan (KL-
    väggarnas regelfack och källarväggarnas cellplast bakom gipsen) och ned i b:s vägg."""
    ua, ub = _ner_i_vaggen(a, z)[0], _ner_i_vaggen(b, z)[0]
    return Ror(f"G17-R{n}", FXP16, a.id, b.id,
               via=((ua[0], ua[1], z), *((x, y, z) for x, y in vagen), (ub[0], ub[1], z)))


# gruppen G17 (../grupper.py): från centralen till tvättstugans brytare och därifrån mellan brytarna i väggarna (KL1,
# KL3, KL4, V4) och genom bjälklaget söder och öster om trappan till det stora rummets brytare på KL7
_KL3_X, _KL4_Y, _KL1_Y = 4531.0, 4990.0, 5820.0
_B = _BRYTARE
ROR += [
    _i_vaggarna(_B["KA-B2"], _B["KA-B6"], 1, [(_KL3_X, _KL1_Y), (_B["KA-B6"].lage.punkt[0], _KL1_Y)]),
    _i_vaggarna(_B["KA-B2"], _B["KA-B1"], 2, [(_KL3_X, _KL4_Y), (_B["KA-B1"].lage.punkt[0], _KL4_Y)]),
    Ror("G17-R3", FXP16, "KA-B1", "KA-B4"),
    _i_vaggarna(_B["KA-B1"], _B["KA-B3"], 4, [(_KL3_X + 30.0, _KL4_Y + 30.0), (_KL3_X + 30.0, 7515.0 + _V - 63.0 + 150.0),
                                             (_B["KA-B3"].lage.punkt[0], 7515.0 + _V - 63.0 + 150.0)]),
    Ror("G17-R5", FXP16, "KA-B1", "KA-B5",
        via=(*_ner_i_vaggen(_B["KA-B1"], BJALKLAG["MB-UK"]), (_B["KA-B1"].lage.punkt[0], _KL4_Y + 10.0, BJALKLAG["MB-UK"]),
             (9645.0, _KL4_Y + 10.0, BJALKLAG["MB-UK"]),
             *reversed(_ner_i_vaggen(_B["KA-B5"], BJALKLAG["MB-UK"])))),
]
