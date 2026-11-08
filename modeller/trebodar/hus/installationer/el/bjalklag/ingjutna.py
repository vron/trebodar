"""Elrören ingjutna i mellanbjälklaget (#87): kartorna över elrörens två nivåer och rörens vägar i dem, raka och
sneda, direkt från punkt till punkt med mjuka böjar (../../plattan.py).

Rören går runt hålen och bjälklagets kanter (KANT), utanför pelarnas kontrollsnitt för genomstansning
(GENOMSTANSNING_KARNA, 2d från pelarens kant, K-05) och helst utanför genomstansningszonen (GENOMSTANSNING, 6d, där en
meter räknas som ZON_FAKTOR meter), genom banden av vinkeljärn vid kanterna och väggarna bara mellan järnen och längs
dem, mellan källarväggarnas lodräta järn och runt det som går lodrätt genom nivån: tappvattnets och avloppets rör,
hylsorna, golvbrunnen, ventilationens kanaler och de andra elrörens stigare. I den undre nivån, tappvattnets, går de
också runt tappvattnets och avloppets rör i den och de ingjutna dosorna i källarens tak. I golvvärmens stråk (plan 1)
byter de inte nivå och korsar inte varandra, eftersom rampen och korsningen går genom golvvärmens nivå.

Rören dras i tur och ordning (Ingjutning): varje nytt går runt de tidigare rörens stigare och helst inte genom
rören (de korsar dem brant, där vägen hellre byter nivå); rör som går ut åt var sitt håll från samma ställe går i
knippen (knippe, solfjader). Där två rör ändå går i varandra i samma nivå går det ena förbi det andra i en kort svacka
(korsningar).

Koordinater i mm (K-05), z från plan 1:s golv.
"""
from __future__ import annotations

import math
from collections.abc import Sequence
from functools import cache

import numpy as np
from shapely.geometry import LineString, Point
from shapely.geometry.base import BaseGeometry
from shapely.ops import nearest_points, unary_union
from shapely.strtree import STRtree

from trebodar.hus.grund.pelare import PELARE

from ...avlopp.ledningar import golvbrunnar, ledningar as avloppets
from ...genomforingar import bjalklaget
from ...golvvarme import plan1 as GV1
from ...golvvarme.katalog import GOLVVARMEROR
from ...golvvarme.punkter import FIL as GV_FIL
from ...montering import BJALKLAG, KALLARTAK, PLAN, Vek
from ...plattan import MINSTA_RADIE, Karta, Punkt, bage_punkter, jarnfri, kartor, ledning, rundad_linje, vag2
from ...vatten.system import vatten
from ...ventilation.system import ventilation
from ..punkter import Ror
from ..typer import Rortyp

KANT = 60.0                     # rören håller sig så långt från bjälklagets kanter och trapphålet
GENOMSTANSNING_KARNA = 300.0    # pelarnas kontrollsnitt (2d från pelarens kant, K-05): rören går utanför
GENOMSTANSNING = 720.0          # genomstansningszonen (6d, K-05): rören går helst utanför
ZON_FAKTOR = 1.25               # en meter i genomstansningszonen räknas som så många meter

Stigare = tuple[float, float, float]          # något som går lodrätt genom nivån: läge i plan och radie


def _lodrata_stycken(vag_: Sequence[Vek], r: float, z0: float, z1: float) -> list[Stigare]:
    return [(a[0], a[1], r) for a, b in zip(vag_, vag_[1:])
            if math.dist(a[:2], b[:2]) < 1.0 and min(a[2], b[2]) < z1 and max(a[2], b[2]) > z0]


@cache
def genom_nivan(z0: float, z1: float) -> tuple[Stigare, ...]:
    """Det som går lodrätt genom höjderna z0–z1 i bjälklaget: tappvattnets och avloppets rör (kopparrören i sina
    hylsor), golvbrunnen och ventilationens kanaler."""
    ut: list[Stigare] = []
    v = vatten()
    hylsor = {r: d for r, _, _, d in v.hylsor()}
    for r in v.ror.values():
        ut += _lodrata_stycken(v.vag(r), hylsor.get(r.id, r.typ.yttre) / 2, z0, z1)
    for led in avloppets().values():
        ut += _lodrata_stycken(led.vag, led.d / 2, z0, z1)
    ut += [(x, y, d / 2) for x, y, d, z in golvbrunnar().values() if KALLARTAK < z < PLAN[1] + 1.0]
    ven = ventilation()
    for g in ven.grenar.values():
        for s in ven.stycken(g):
            ut += _lodrata_stycken((s.a, s.b), math.hypot(*s.yttre) / 2, z0, z1)
    return tuple(ut)


FORENKLA = 12.0                              # tappvattnets svep förenklade så mycket i kartorna [mm]


@cache
def i_nivan(z0: float, z1: float) -> tuple[tuple[LineString, float], ...]:
    """Tappvattnets och avloppets vågräta rör i höjderna z0–z1 (den undre nivån): linjen i plan och radien."""
    ut: list[tuple[LineString, float]] = []         # svepen förenklade (färre hörn i kartorna), radien lika mycket större
    v = vatten()
    vagar: list[tuple[Sequence[Vek], float]] = [(v.vag(r), r.typ.yttre / 2) for r in v.ror.values()]
    vagar += [(led.vag, led.d / 2) for led in avloppets().values()]
    for vag_, r in vagar:                       # i följd i nivån: en linje (tappvattnets svep har många punkter)
        linje: list[tuple[float, float]] = []
        for a, b in zip(vag_, vag_[1:]):
            if math.dist(a[:2], b[:2]) > 1.0 and min(a[2], b[2]) - r < z1 and max(a[2], b[2]) + r > z0:
                if linje and math.dist(linje[-1], a[:2]) < 1e-6:
                    linje.append(b[:2])
                else:
                    if len(linje) > 1:
                        ut.append((LineString(linje).simplify(FORENKLA), r + FORENKLA))
                    linje = [a[:2], b[:2]]
        if len(linje) > 1:
            ut.append((LineString(linje).simplify(FORENKLA), r + FORENKLA))
    return tuple(ut)


@cache
def golvvarmens_strak() -> BaseGeometry:
    """Där golvvärmens tillopp går i stråk i plan 1:s golv (../../golvvarme/plan1.py), i plan: där elrören inte byter
    nivå och inte går under eller över ett annat rör (rampen och korsningen går genom golvvärmens nivå; golvvärmens
    slingor går runt dem, men stråken ligger fast). Stråkens filer i zonernas ordning, två per zon."""
    filer: dict[str, list[int]] = {}
    for i, z in enumerate(GV1.ZONER):
        filer.setdefault(z.strak, []).extend((2 * i, 2 * i + 1))
    mitt = {s: GV1.X0 + (min(f) + max(f)) / 2 * GV_FIL for s, f in filer.items()}
    return unary_union([LineString(st.punkter).buffer((len(filer[s_]) - 1) * GV_FIL / 2 + GOLVVARMEROR.d / 2,
                                                      cap_style="flat", join_style="mitre")
                        for s_, st in GV1.strak(mitt).items()])


NIVAER = ("MB", "MB-UK")                     # kartornas ordning: den övre nivån, den undre
UNDRE_KOSTNAD = 0.15                         # de klena rören håller sig helst i den övre nivån (per mm i den undre)
SPEL_ROR = 5.0                               # fritt mellan två ingjutna rör och mellan ett rör och en stigare
NARA_DOSAN = 150.0                           # rör som möts i en punkt får gå närmare varandra så nära den

Ror3 = tuple[float, float, float, float, float]      # något lodrätt genom bjälklaget: x, y, radie, z0, z1


@cache
def kartor_el(r: float, hojd: float | None = None) -> tuple[Karta, ...]:
    """Kartorna för elrör med radien r (i plan; hojd: den halva höjden, om den är mindre, för ett knippe rör sida vid
    sida) i den övre och den undre nivån (NIVAER), med gemensamma noder så att vägen kan byta nivå: runt pelarna och
    det som går lodrätt genom nivån, och i den undre nivån runt tappvattnets och avloppets rör. Andra elrör, deras
    stigare och de ingjutna dosorna är hinder för varje väg för sig (hinder)."""
    h_ = hojd or r
    hinder: list[list[BaseGeometry]] = []
    karnor = [Point(x, y).buffer(GENOMSTANSNING_KARNA, quad_segs=2) for x, y in PELARE.values()]
    for niva in NIVAER:
        z = BJALKLAG[niva]
        h: list[BaseGeometry] = [Point(x, y).buffer(rr, quad_segs=1) for x, y, rr in genom_nivan(z - h_, z + h_)]
        if niva == "MB-UK":
            h += [g.buffer(rr, quad_segs=1) for g, rr in i_nivan(z - h_, z + h_)]
        hinder.append(h)
    zoner = [(x, y, GENOMSTANSNING) for x, y in PELARE.values()]
    # en stigare i en pelares kontrollsnitt (en dosa på en vägg över pelaren) leds rakt ut ur det
    return kartor(bjalklaget().buffer(-KANT, join_style="mitre"), hinder, [BJALKLAG[n] for n in NIVAER], r, zoner,
                  ZON_FAKTOR, karnor, hojd, golvvarmens_strak())


def hinder(r: float, stigare: Sequence[Ror3] = (), dosor: Sequence[Stigare] = (),
           utom: Sequence[Punkt] = ()) -> tuple[list[BaseGeometry], ...]:
    """Hindren för ett rör med radien r i varje nivå (NIVAER): andra rörs stigare (x, y, radie och höjderna de går
    mellan) och i den undre nivån de ingjutna dosorna (läge och radie), inte de vid punkterna utom (rörets egna)."""
    ut: tuple[list[BaseGeometry], ...] = ([], [])
    for i, niva in enumerate(NIVAER):
        z = BJALKLAG[niva]
        for x, y, rr, z0, z1 in stigare:
            if z0 < z + r and z1 > z - r and all(math.dist((x, y), u) > 1.0 for u in utom):
                ut[i].append(Point(x, y).buffer(rr + r + SPEL_ROR, quad_segs=2))
        if niva == "MB-UK":
            ut[i].extend(Point(x, y).buffer(rr + r + SPEL_ROR, quad_segs=2) for x, y, rr in dosor
                         if all(math.dist((x, y), u) > 1.0 for u in utom))
    return ut


PLAN1 = (0.0, UNDRE_KOSTNAD)                 # extra kostnad per mm i nivåerna: plan 1:s rör håller sig i den övre
KALLAREN = (UNDRE_KOSTNAD, 0.0)              # och källarens i den undre (under plan 1:s)


def ingjutet(kartor_: Sequence[Karta], a: Punkt, b: Punkt, fran: Sequence[str] = NIVAER,
             till: Sequence[str] = NIVAER, hinder_: Sequence[Sequence[BaseGeometry]] = (),
             led_a: dict[str, Sequence[Punkt]] | None = None, kost: tuple[float, float] = PLAN1,
             ror: Sequence[Sequence[BaseGeometry]] = (), radie_a: float | None = None,
             extra: Sequence[Sequence[Punkt]] = (), led_b: dict[str, Sequence[Punkt]] | None = None
             ) -> tuple[tuple[Vek, ...], tuple[float, ...]]:
    """Röret från a till b (där det går lodrätt in i och ut ur bjälklaget) genom nivåerna, in i nivåerna fran och ut
    ur nivåerna till, runt hindren i varje nivå (hinder(): stigare och dosor) och helst inte genom de andra rören (ror,
    upptaget_av()): brytpunkterna och deras radier."""
    d = vag2(kartor_, a, b, [NIVAER.index(n) for n in fran], [NIVAER.index(n) for n in till], hinder_,
             {NIVAER.index(n): v for n, v in (led_a or {}).items()},
             {NIVAER.index(n): v for n, v in (led_b or {}).items()}, kost_niva=kost, mjuka=ror, radie_a=radie_a,
             extra_noder=extra, dyr_korsning=golvvarmens_strak())
    return d.punkter, d.radier


def sammanfoga(*delar: tuple[Sequence[Vek], Sequence[float]]) -> tuple[tuple[Vek, ...], tuple[float, ...]]:
    """Brytpunkterna och radierna i följd (delarna: brytpunkter och radier, eller brytpunkter med tomma radier), utan
    punkter som upprepas."""
    via: list[Vek] = []
    rad: list[float] = []
    for pts, radier in delar:
        for i, q in enumerate(pts):
            r = radier[i] if i < len(radier) else 0.0
            if via and math.dist(q, via[-1]) < 0.5:
                rad[-1] = max(rad[-1], r)
                continue
            via.append((float(q[0]), float(q[1]), float(q[2])))
            rad.append(r)
    return tuple(via), tuple(rad)


def linjerna(ro: Ror) -> tuple[list[LineString], ...]:
    """Rörets mittlinje i varje nivå (NIVAER) i bjälklaget, med bågarna rundade."""
    ut: tuple[list[LineString], ...] = ([], [])
    via = list(ro.via)
    rad = list(ro.radier) + [0.0] * (len(via) - len(ro.radier))
    for i, niva in enumerate(NIVAER):
        z = BJALKLAG[niva]
        for grupp in _foljder([m for m, q in enumerate(via) if abs(q[2] - z) < 1.0]):
            pts = [(via[m][0], via[m][1]) for m in grupp]
            if len(pts) > 1:
                ut[i].append(LineString(rundad_linje(pts, [rad[m] for m in grupp])))
    return ut


def _andar(ro: Ror) -> list[Punkt]:
    """Rörets ändar i bjälklaget: där det går lodrätt in i och ut ur nivåerna."""
    nivaer = {BJALKLAG[n] for n in NIVAER}
    i = [m for m, q in enumerate(ro.via) if any(abs(q[2] - z) < 1.0 for z in nivaer)]
    return [(ro.via[i[0]][0], ro.via[i[0]][1]), (ro.via[i[-1]][0], ro.via[i[-1]][1])] if i else []


def upptaget_av(ror: Sequence[Ror], r: float, mots: Sequence[Punkt] = ()) -> tuple[list[BaseGeometry], ...]:
    """Det som rören upptar i elrörens nivåer (NIVAER), förstorat så att ett rör med radien r går fritt: deras
    sträckor i varje nivå, med bågarna rundade; rör som slutar i en av punkterna mots (där det nya röret börjar eller
    slutar, i samma dosa) inte så nära den (NARA_DOSAN)."""
    ut: tuple[list[BaseGeometry], ...] = ([], [])
    for ro in ror:
        nara = [q for q in mots if any(math.dist(q, e) < 60.0 for e in _andar(ro))]
        klipp = unary_union([Point(q).buffer(NARA_DOSAN) for q in nara]) if nara else None
        for i, linjer in enumerate(linjerna(ro)):
            for linje in linjer:
                g = linje.buffer(ro.typ.ytterdiameter / 2 + r + SPEL_ROR, quad_segs=2)
                ut[i].append(g.difference(klipp) if klipp is not None and g.intersects(klipp) else g)
    return ut


def konflikter(ror: Sequence[Ror]) -> list[tuple[int, int]]:
    """Rören (index) som går i varandra i samma nivå i bjälklaget, utom där de möts i samma dosa."""
    lin = [linjerna(ro) for ro in ror]
    ut: list[tuple[int, int]] = []
    for i in range(len(ror)):
        for j in range(i + 1, len(ror)):
            gr = ror[i].typ.ytterdiameter / 2 + ror[j].typ.ytterdiameter / 2 - 0.5
            mots = [q for q in _andar(ror[i]) if any(math.dist(q, e) < 60.0 for e in _andar(ror[j]))]
            for a_, b_ in zip(lin[i], lin[j]):
                if any(la.distance(lb) < gr and (not mots or any(
                        la.difference(Point(q).buffer(NARA_DOSAN)).distance(lb) < gr for q in mots))
                       for la in a_ for lb in b_):
                    ut.append((i, j))
                    break
    return ut


def _foljder(index: Sequence[int]) -> list[list[int]]:
    """Index i följd (utan luckor) i grupper."""
    ut: list[list[int]] = []
    for m in index:
        if ut and m == ut[-1][-1] + 1:
            ut[-1].append(m)
        else:
            ut.append([m])
    return ut


class Ingjutning:
    """Rören i bjälklaget dragna i tur och ordning: varje nytt rör går runt de andra rörens stigare (stigare), de
    ingjutna dosorna (dosor) och rören som redan är dragna (ror), i den nivå de går i."""

    def __init__(self, stigare: Sequence[Ror3] = (), dosor: Sequence[Stigare] = (), ror: Sequence[Ror] = ()):
        self.stigare = list(stigare)
        self.dosor = list(dosor)
        self.ror = list(ror)

    def dra(self, id_: str, typ: Rortyp, fran: str, till: str, a: Punkt, b: Punkt, fore: Sequence[Vek] = (),
            efter: Sequence[Vek] = (), nivaer: tuple[Sequence[str], Sequence[str]] = (NIVAER, NIVAER),
            slag: str = "230 V", kost: tuple[float, float] = PLAN1, led_a: dict[str, Sequence[Punkt]] | None = None,
            stigare: bool = True, prova: bool = False, radie_a: float | None = None,
            fore_radier: Sequence[float] = (), efter_radier: Sequence[float] = (), bage_a: float = 0.0,
            bage_b: float = 0.0, ocksa: Sequence[Ror] = (), led_b: dict[str, Sequence[Punkt]] | None = None) -> Ror:
        """Röret id_ från punkten fran till till: fore (t.ex. upp ur en dosa, eller i ett knippe, med hörnens radier
        fore_radier), i bjälklaget från a till b (där det går lodrätt in och ut, eller ur knippet) i nivåerna (in, ut)
        och efter (t.ex. ned i en vägg till en dosa, eller i ett knippe, med radierna efter_radier), runt de dragna
        rören och ocksa (t.ex. de andra rören i knippet). Hörnen i a och b (där röret lämnar och går in i ett knippe)
        rundas med radierna bage_a och bage_b, eller de största mindre som ryms. Röret och dess stigare blir hinder
        för de följande rören (inte om prova: bara vägen)."""
        r = typ.ytterdiameter / 2
        h = hinder(r, self.stigare, self.dosor, utom=(a, b))
        mjuka = upptaget_av([*self.ror, *ocksa], r, (a, b))
        # noder tvärs de rör som den raka linjen från a till b går snett genom, i varje nivå, och runt ändarna på de
        # rör som slutar nära den (så att vägen kan gå runt ett rör i stället för att korsa det)
        rakt = [_tvars([(*a, BJALKLAG[n]), (*b, BJALKLAG[n])], mjuka)[i] for i, n in enumerate(NIVAER)]
        ab = LineString([a, b]) if math.dist(a, b) > 1.0 else Point(a)
        w = 2 * r + SPEL_ROR + RUNT_ANDEN
        runt = [(e[0] + w * math.cos(v), e[1] + w * math.sin(v)) for ro in [*self.ror, *ocksa] for e in _andar(ro)
                if ab.distance(Point(e)) < NARA_LINJEN and min(math.dist(e, a), math.dist(e, b)) > w
                for v in np.linspace(0.0, 2 * math.pi, 8, endpoint=False)]
        rakt = [[*u, *runt] for u in rakt]
        mitt = ingjutet(kartor_el(r), a, b, nivaer[0], nivaer[1], h, led_a, kost, mjuka, radie_a, extra=rakt,
                        led_b=led_b)
        tvars = _tvars(mitt[0], mjuka)              # går vägen snett genom ett annat rör: igen, med noder tvärs det
        if any(tvars):
            mitt = ingjutet(kartor_el(r), a, b, nivaer[0], nivaer[1], h, led_a, kost, mjuka, radie_a,
                            extra=[[*u, *v] for u, v in zip(rakt, tvars)], led_b=led_b)
        via, radier = sammanfoga((fore, fore_radier), mitt, (efter, efter_radier))
        for p, bage in ((a, bage_a), (b, bage_b)):
            if bage > 0.0:
                radier = mjukt_horn(via, radier, p, bage, kartor_el(r))
        ro = Ror(id_, typ, fran, till, via=via, radier=radier, slag=slag)
        if not prova:
            self.lagg(ro, stigare)
        return ro

    def lagg(self, ro: Ror, stigare: bool = True) -> None:
        """Röret blir ett hinder för de följande rören, och dess stigare (där det går lodrätt in i och ut ur
        bjälklagets nivåer)."""
        self.ror.append(ro)
        if not stigare:
            return
        r = ro.typ.ytterdiameter / 2
        nivaer = {BJALKLAG[n] for n in NIVAER}
        i = [m for m, q in enumerate(ro.via) if any(abs(q[2] - z) < 1.0 for z in nivaer)]
        if not i:
            return
        for m, granne in ((i[0], i[0] - 1), (i[-1], i[-1] + 1)):
            q = ro.via[m]
            z0 = ro.via[granne][2] if 0 <= granne < len(ro.via) else q[2]
            lo, hi = sorted((z0, q[2]))
            self.stigare.append((q[0], q[1], r, lo - r, hi + r))

    def solfjader(self, bestallningar: Sequence[dict[str, object]]) -> list[Ror]:
        """Rör som går ut åt var sitt håll från samma ställe (centralen, drivdonsskåpet) i knippen (knippe()): rörens
        vägar i knippena (fore) är hinder för de andra, och rören dras i tur och ordning (bestallningarnas), vart och
        ett från där det lämnar sitt knippe (a) runt de tidigare. bestallningar: dra()-argumenten per rör."""
        def knippet(b: dict[str, object]) -> Ror:
            fore: tuple[Vek, ...] = tuple(b.get("fore", ()))                      # type: ignore[arg-type]
            efter: tuple[Vek, ...] = tuple(b.get("efter", ()))                    # type: ignore[arg-type]
            fr = list(b.get("fore_radier", ())) + [0.0] * len(fore)                   # type: ignore[call-overload]
            er = list(b.get("efter_radier", ())) + [0.0] * len(efter)                 # type: ignore[call-overload]
            return Ror(f"{b['id_']} i knippet", b["typ"], "", "", via=(*fore, *efter),   # type: ignore[arg-type]
                       radier=(*fr[:len(fore)], *er[:len(efter)]))
        knippen = [knippet(b) for b in bestallningar]
        return [self.dra(**b, ocksa=knippen[i + 1:]) for i, b in enumerate(bestallningar)]  # type: ignore[arg-type]


RUNT_ANDEN = 60.0                # noder runt andra rörs ändar så långt utanför dem
NARA_LINJEN = 2000.0             # för rören som slutar så nära den raka linjen mellan vägens ändar
SNETT = 150.0                    # en väg som går så långt genom ett annat rör i samma nivå korsar det för snett
TVARS = (-300.0, -150.0, 0.0, 150.0, 300.0)      # noderna på var sida om det, så långt isär längs vägen
TVARS_UT = 60.0                  # och så långt utanför det


def _tvars(punkter: Sequence[Vek], mjuka: Sequence[Sequence[BaseGeometry]]) -> list[list[Punkt]]:
    """Extra noder per nivå där vägen går snett genom ett annat rör (mjuka: rören förstorade, upptaget_av()): på var
    sida om det, så att vägen kan korsa det brant i stället."""
    ut: list[list[Punkt]] = [[] for _ in NIVAER]
    for i, niva in enumerate(NIVAER):
        z = BJALKLAG[niva]
        trad = STRtree(list(mjuka[i])) if i < len(mjuka) and mjuka[i] else None
        if trad is None:
            continue
        for p, q in zip(punkter, punkter[1:]):
            if abs(p[2] - z) > 1.0 or abs(q[2] - z) > 1.0 or math.dist(p[:2], q[:2]) < 1.0:
                continue
            seg = LineString([p[:2], q[:2]])
            u = _riktning_(p[:2], q[:2])
            n = (-u[1], u[0])
            for j in trad.query(seg):
                g = mjuka[i][int(j)]
                del_ = g.intersection(seg)
                if del_.length < SNETT:
                    continue
                m = del_.interpolate(0.5, normalized=True)
                # det andra rörets bredd tvärs vägen där
                bredd = LineString([(m.x - n[0] * 500.0, m.y - n[1] * 500.0),
                                    (m.x + n[0] * 500.0, m.y + n[1] * 500.0)]).intersection(g).length
                w = bredd / 2 + TVARS_UT
                ut[i] += [(m.x + u[0] * t + n[0] * sid * w, m.y + u[1] * t + n[1] * sid * w) for t in TVARS
                          for sid in (-1.0, 1.0)]
    return ut


def _tangent(via: Sequence[Vek], rad: Sequence[float], i: int) -> float:
    """Hur långt hörnet i:s båge går längs sträckorna (0 där det inte är ett hörn i plan)."""
    if not 0 < i < len(via) - 1 or rad[i] <= 0.0 or abs(via[i - 1][2] - via[i][2]) > 1.0 or \
            abs(via[i + 1][2] - via[i][2]) > 1.0:
        return 0.0
    u = (via[i][0] - via[i - 1][0], via[i][1] - via[i - 1][1])
    w = (via[i + 1][0] - via[i][0], via[i + 1][1] - via[i][1])
    c = (u[0] * w[0] + u[1] * w[1]) / max(math.hypot(*u) * math.hypot(*w), 1e-9)
    return rad[i] * math.tan(math.acos(max(-1.0, min(1.0, c))) / 2)


def mjukt_horn(via: Sequence[Vek], rad: Sequence[float], p: Punkt, radie: float,
               kartor_: Sequence[Karta]) -> tuple[float, ...]:
    """Radierna med hörnet i punkten p (i en av nivåerna) rundat med den största radien upp till radie som ryms
    mellan grannarnas bågar och håller bågen i det fria och fri från järnen."""
    ut = list(rad) + [0.0] * (len(via) - len(rad))
    nivaer = [BJALKLAG[n] for n in NIVAER]
    for i in range(1, len(via) - 1):
        q = via[i]
        if math.dist(q[:2], p) > 0.5 or not any(abs(q[2] - z) < 1.0 for z in nivaer):
            continue
        a_, c_ = via[i - 1], via[i + 1]
        if abs(a_[2] - q[2]) > 1.0 or abs(c_[2] - q[2]) > 1.0:
            break
        k = kartor_[min(range(len(nivaer)), key=lambda m: abs(nivaer[m] - q[2]))]
        u = (q[0] - a_[0], q[1] - a_[1])
        w = (c_[0] - q[0], c_[1] - q[1])
        cos_ = (u[0] * w[0] + u[1] * w[1]) / max(math.hypot(*u) * math.hypot(*w), 1e-9)
        vinkel = math.acos(max(-1.0, min(1.0, cos_)))
        if vinkel < math.radians(0.5):
            break
        tmax = min(math.hypot(*u) - _tangent(via, ut, i - 1), math.hypot(*w) - _tangent(via, ut, i + 1))
        r_ = min(radie, tmax / math.tan(vinkel / 2))
        while r_ >= MINSTA_RADIE:
            bage = LineString(bage_punkter(a_[:2], q[:2], c_[:2], r_))
            if k.fritt.contains(bage) and jarnfri(k, bage):
                ut[i] = max(ut[i], r_)
                break
            r_ *= 0.8
        break
    return tuple(ut)


# ------------------------------------------------------------------ korsningarna

# där två rör ändå korsar varandra i samma nivå går det ena förbi det andra: i den övre nivån ned under det (till
# golvvärmens nivå, golvvärmens slingor går runt), i den undre upp över det (emot det, under golvvärmen)
KORSNING_SPEL = {"MB": -1.0, "MB-UK": 0.0}
KORS_FRITT = 25.0                          # så långt på var sida om det andra röret ligger det på korsningens höjd
KORS_RAMP = 150.0                          # och lutar så lång sträcka dit


def _korsningspunkt(a: Ror, b: Ror) -> tuple[Punkt, int] | None:
    """Där rören a och b går i varandra i samma nivå (punkten på a:s mittlinje närmast b) och nivån."""
    la, lb = linjerna(a), linjerna(b)
    gr = a.typ.ytterdiameter / 2 + b.typ.ytterdiameter / 2 - 0.5
    bast: tuple[float, Punkt, int] | None = None
    for i, (xa, xb) in enumerate(zip(la, lb)):
        for p in xa:
            for q in xb:
                d = p.distance(q)
                if d < gr and (bast is None or d < bast[0]):
                    pa, _ = nearest_points(p, q)
                    bast = (d, (pa.x, pa.y), i)
    return None if bast is None else (bast[1], bast[2])


def _sank(ro: Ror, x: Punkt, niva: int, r_andra: float) -> Ror | None:
    """Röret med en korsning vid punkten x (i nivån) med ett rör med radien r_andra: på den raka sträcka i nivån som
    x ligger på går röret förbi det andra, under det i den övre nivån och över det i den undre (KORS_FRITT på var
    sida om x, med KORS_RAMP lutning före och efter), om sträckan räcker till."""
    z = BJALKLAG[NIVAER[niva]]
    via = list(ro.via)
    rad = list(ro.radier) + [0.0] * (len(via) - len(ro.radier))
    bast = None
    for m in range(len(via) - 1):
        p, q = via[m], via[m + 1]
        if abs(p[2] - z) > 1.0 or abs(q[2] - z) > 1.0:
            continue
        seg = LineString([p[:2], q[:2]])
        d = seg.distance(Point(x))
        if bast is None or d < bast[0]:
            bast = (d, m, seg.project(Point(x)), seg.length)
    if bast is None or bast[0] > 60.0:
        return None
    _, m, t, lg = bast
    p, q = via[m], via[m + 1]
    # korsningen på sträckans raka del: bågarna i dess ändar mindre om det behövs (minst MINSTA_RADIE)
    halv = KORS_FRITT + KORS_RAMP
    for i, plats in ((m, t - halv - 1.0), (m + 1, lg - t - halv - 1.0)):
        if _tangent(via, rad, i) <= plats:
            continue
        if plats <= 0.0:
            return None
        vinkel = 2 * math.atan(_tangent(via, rad, i) / rad[i])
        if plats / math.tan(vinkel / 2) < MINSTA_RADIE:
            return None
        rad[i] = plats / math.tan(vinkel / 2)
    sida = -1.0 if NIVAER[niva] == "MB" else 1.0
    zk = z + sida * (ro.typ.ytterdiameter / 2 + r_andra - KORSNING_SPEL[NIVAER[niva]])
    if abs(zk - GV1.Z) < ro.typ.ytterdiameter / 2 + GOLVVARMEROR.d / 2:      # genom golvvärmens nivå: inte i ett stråk
        f0, f1 = (t - halv) / lg, (t + halv) / lg
        bit = LineString([(p[0] + (q[0] - p[0]) * f, p[1] + (q[1] - p[1]) * f) for f in (f0, f1)])
        if bit.buffer(ro.typ.ytterdiameter / 2).intersects(golvvarmens_strak()):
            return None
    nya = []
    for s_, zz in ((t - halv, z), (t - KORS_FRITT, zk), (t + KORS_FRITT, zk), (t + halv, z)):
        f = s_ / lg
        nya.append((p[0] + (q[0] - p[0]) * f, p[1] + (q[1] - p[1]) * f, zz))
    via[m + 1:m + 1] = nya
    rad[m + 1:m + 1] = [0.0] * len(nya)
    return Ror(ro.id, ro.typ, ro.fran, ro.till, via=tuple(via), radier=tuple(rad), slag=ro.slag)


def korsningar(ror: Sequence[Ror], varv: int = 6) -> list[Ror]:
    """Rören där två ändå går i varandra i samma nivå i bjälklaget: det senare går under (eller över) det tidigare
    vid korsningen (_sank), annars det tidigare under det senare, där korsningen går fri från de andra rören (också
    deras korsningar)."""
    ut = list(ror)
    for _ in range(varv):
        par = konflikter(ut)
        if not par:
            break
        for i, j in par:
            for a_, b_ in ((j, i), (i, j)):
                x = _korsningspunkt(ut[a_], ut[b_])
                if x is None:
                    break
                ny = _sank(ut[a_], *x, r_andra=ut[b_].typ.ytterdiameter / 2)
                if ny is not None and _fri_korsning(ny, ut[a_], [r for m, r in enumerate(ut) if m != a_]):
                    ut[a_] = ny
                    break
    return ut


def _fri_korsning(ny: Ror, gammal: Ror, andra: Sequence[Ror]) -> bool:
    """Om korsningen i röret ny (det som skiljer det från gammal) går fritt från de andra rören i bjälklaget (deras
    mittlinjer i 3D, minst radierna emellan)."""
    nya = [q for q in ny.via if q not in gammal.via]
    if not nya:
        return True
    lo = np.min(np.array(nya), axis=0) - KORS_RAMP
    hi = np.max(np.array(nya), axis=0) + KORS_RAMP
    i0 = max(ny.via.index(nya[0]) - 1, 0)
    i1 = min(ny.via.index(nya[-1]) + 1, len(ny.via) - 1)
    bit = ny.via[i0:i1 + 1]
    for ro in andra:
        gr = ny.typ.ytterdiameter / 2 + ro.typ.ytterdiameter / 2 - 0.5
        for a, b in zip(ro.via, ro.via[1:]):
            if (np.minimum(a, b)[:2] > hi[:2] + gr).any() or (np.maximum(a, b)[:2] < lo[:2] - gr).any():
                continue
            if any(_avstand3(p, q, a, b) < gr for p, q in zip(bit, bit[1:])):
                return False
    return True


def _avstand3(p0: Vek, p1: Vek, q0: Vek, q1: Vek) -> float:
    """Det minsta avståndet mellan sträckorna p0–p1 och q0–q1 i 3D."""
    P0, P1, Q0, Q1 = (np.asarray(v, dtype=float) for v in (p0, p1, q0, q1))
    u, v, w = P1 - P0, Q1 - Q0, P0 - Q0
    a, b, c, d, e = u @ u, u @ v, v @ v, u @ w, v @ w
    n = a * c - b * b
    s = 0.0 if n < 1e-9 else float(np.clip((b * e - c * d) / n, 0.0, 1.0))
    t = float(np.clip((b * s + e) / c, 0.0, 1.0)) if c > 1e-9 else 0.0
    s = float(np.clip((b * t - d) / a, 0.0, 1.0)) if a > 1e-9 else 0.0
    return float(np.linalg.norm(P0 + u * s - Q0 - v * t))


# ------------------------------------------------------------------ knippen: rören i filer genom det trånga

CC_KNIPPE = 22.0                 # rörens avstånd i ett knippe (Ø16 och Ø20 i ordning, några mm emellan)
STAM = 60.0                      # knippet går minst så långt rakt ut ur raden, vinkelrätt mot den
BAGE_KNIPPE = 100.0              # den innersta filens radie där knippet svänger, minst
AVVIK = math.radians(40.0)       # röret lämnar knippet så snett mot sin sida, rakt mot sitt mål
SNETT_MAX = 1000.0               # och brantare där målet ligger längre än så åt sidan (snett högst så långt)


def _forskjuten(pts: Sequence[Punkt], radier: Sequence[float], d: float) -> tuple[list[Punkt], list[float]]:
    """Polylinjen pts (hörnen med radierna) förskjuten d åt vänster: hörnen längs bisektrisen, radierna mindre på
    svängens insida och större på utsidan."""
    ut: list[Punkt] = []
    rad: list[float] = []
    for i, p in enumerate(pts):
        u = _riktning_(pts[i - 1], p) if i > 0 else None
        w = _riktning_(p, pts[i + 1]) if i + 1 < len(pts) else None
        nu = (-u[1], u[0]) if u else None
        nw = (-w[1], w[0]) if w else None
        if u is not None and w is not None and nu is not None and nw is not None:
            b = (nu[0] + nw[0], nu[1] + nw[1])
            cos_halv = max(0.2, (b[0] * nu[0] + b[1] * nu[1]) / max(math.hypot(*b), 1e-9))
            n = (b[0] / max(math.hypot(*b), 1e-9) / cos_halv, b[1] / max(math.hypot(*b), 1e-9) / cos_halv)
            vanster = u[0] * w[1] - u[1] * w[0] > 0                 # svängen moturs: vänster är insidan
            rad.append(max(0.0, radier[i] - d if vanster else radier[i] + d) if radier[i] > 0 else 0.0)
        else:
            n = nu or nw or (0.0, 0.0)
            rad.append(0.0)
        ut.append((p[0] + n[0] * d, p[1] + n[1] * d))
    return ut, rad


def _riktning_(p: Punkt, q: Punkt) -> Punkt:
    n = math.dist(p, q)
    return ((q[0] - p[0]) / n, (q[1] - p[1]) / n) if n > 1e-9 else (0.0, 0.0)


def knippe(kartor_: Sequence[Karta], stigare: Sequence[Punkt], ut: Punkt, mal: dict[str, Punkt],
           slut: Punkt, hinder_: Sequence[Sequence[BaseGeometry]] = (), lager: int = 0,
           kost: tuple[float, float] = PLAN1) -> tuple[dict[str, Punkt], dict[str, tuple[list[Punkt], list[float]]]]:
    """Ett knippe rör från en rad stigare (i ordning längs raden) åt hållet ut och vidare till sina mål: knippets mitt
    går rakt ut ur raden och därifrån (i den övre nivån, som ett rör så brett som knippet) mot slut, raka och sneda med
    mjuka böjar; varje rör går i sin fil (förskjuten CC_KNIPPE från grannen) och lämnar knippet där det är närmast
    målet, åt sin sida, det som lämnar först ytterst. Ger varje rörs stigare och dess väg i knippet (punkterna och
    radierna), till där det lämnar knippet. lager: knippets nivå (index i NIVAER)."""
    k = kartor_[lager]
    m = len(mal)
    bredd = (m - 1) * CC_KNIPPE
    c = ((stigare[0][0] + stigare[-1][0]) / 2, (stigare[0][1] + stigare[-1][1]) / 2)
    # knippets mitt: rakt ut ur raden (genom bandet) och vidare mot slut med knippets bredd
    kb = kartor_el(round(bredd / 2 + k.r, 1), k.r)
    # rakt ut ur raden (varje fil mellan järnen i ett band längs den) till det fria
    # (och så långt att knippet kan svänga med den innersta filen på radien BAGE_KNIPPE)
    tunn = max([STAM, bredd / 2 + BAGE_KNIPPE,
                *(math.dist(q, (led_ or [q])[-1]) for q in stigare for led_ in [ledning(k, q, slut, ut)])])

    def ute(karta: Karta, langd: float, langst: float) -> Punkt | None:
        while langd <= langst:
            q = (c[0] + ut[0] * langd, c[1] + ut[1] * langd)
            if karta.marg.contains(Point(q)):
                return q
            langd += 20.0
        return None

    def slutet(karta: Karta, fran_: Punkt) -> Punkt:
        """Knippets slut: i det fria vid det mål det går mot (ut ur ett hinder där, och vidare tills det ryms)."""
        led_ = ledning(k, slut, fran_)
        e_ = led_[-1] if led_ else slut
        u_ = _riktning_(slut, e_) if led_ else _riktning_(slut, fran_)
        for steg in range(0, 80):
            q = (e_[0] + u_[0] * 20.0 * steg, e_[1] + u_[1] * 20.0 * steg)
            if karta.marg.contains(Point(q)):
                return q
        return e_
    d = None
    for karta_ in (kb, kartor_):                   # hela knippet som ett brett rör, annars dess mitt som ett rör
        a_ = ute(karta_[lager], tunn, tunn + 600.0)
        if a_ is None:
            continue
        try:                                       # det breda mitt i glipan mellan två järn; mitten av det smala
            d = vag2(karta_, c, slutet(karta_[lager], a_), [lager], [lager], hinder_, {lager: [a_]}, {lager: []},
                     kost_niva=kost, glipor_=karta_ is kb)    # (en nödlösning) där det blir
            break
        except ValueError:
            continue
    if d is None:
        raise ValueError(f"ingen väg för knippet från ({c[0]:.0f}, {c[1]:.0f}) mot ({slut[0]:.0f}, {slut[1]:.0f})")
    mitt = [(q[0], q[1]) for q in d.punkter if abs(q[2] - k.z) < 1.0]
    radier = [r for q, r in zip(d.punkter, d.radier) if abs(q[2] - k.z) < 1.0]
    linje = LineString(mitt)
    forst_ute = linje.project(Point(mitt[1]))          # knippet har gått rakt ut ur raden (och bandet längs den)
    # var varje rör lämnar knippet: så långt före punkten närmast målet att det går därifrån snett (AVVIK) rakt till
    # målet, åt sin sida (vänster +1, höger −1)
    lamna: dict[str, tuple[float, int]] = {}
    sidled: dict[str, float] = {}
    vinkel: dict[str, float] = {}
    for g, p in mal.items():
        s_ = linje.project(Point(p))
        a_ = linje.interpolate(max(s_ - 1.0, 0.0))
        b_ = linje.interpolate(min(s_ + 1.0, linje.length))
        kryss = (b_.x - a_.x) * (p[1] - a_.y) - (b_.y - a_.y) * (p[0] - a_.x)
        sidled[g] = kryss / max(math.dist((a_.x, a_.y), (b_.x, b_.y)), 1e-9)     # målets avstånd åt vänster
        lamna[g] = (max(s_ - min(abs(sidled[g]), SNETT_MAX) / math.tan(AVVIK), forst_ute), 1 if kryss > 0 else -1)
        vinkel[g] = math.atan2(abs(sidled[g]), s_ - lamna[g][0])                 # riktningen därifrån till målet
    # knippet slutar där det sista röret lämnar det
    stopp = max(t for t, _ in lamna.values())
    if stopp < linje.length - 1.0:
        kvar = [q for q in mitt if linje.project(Point(q)) < stopp]
        e_ = linje.interpolate(stopp)
        mitt = [*kvar, (e_.x, e_.y)]
        radier = [*radier[:len(kvar)], 0.0]
        linje = LineString(mitt)
    # filerna från vänster till höger: de som lämnar åt vänster först ytterst, sist de som lämnar åt höger (först
    # ytterst); lämnar flera på samma ställe går det som viker av brantast ytterst
    def forst(g: str) -> tuple[float, float]:
        return (round(lamna[g][0] / 30.0), -vinkel[g])
    vanster = sorted((g for g in mal if lamna[g][1] > 0), key=forst)
    hoger = sorted((g for g in mal if lamna[g][1] < 0), key=forst)
    filer = [*vanster, *hoger[::-1]]
    # stigarna: radens ordning åt vänster om knippets riktning ut ur raden
    vanster_om = (-ut[1], ut[0])
    stig_ordning = sorted(stigare, key=lambda q: -(q[0] * vanster_om[0] + q[1] * vanster_om[1]))
    ut_stig: dict[str, Punkt] = {}
    ut_vag: dict[str, tuple[list[Punkt], list[float]]] = {}
    filerna: dict[str, tuple[list[Punkt], list[float]]] = {}
    lamnar: dict[str, float] = {}
    for j, g in enumerate(filer):
        s_ = stig_ordning[j]
        dj = (s_[0] - c[0]) * vanster_om[0] + (s_[1] - c[1]) * vanster_om[1]
        fil, frad = _forskjuten(mitt, radier, dj)
        fil[0] = s_                                        # filen börjar i stigaren
        # där röret lämnar filen: så långt före punkten närmast målet att det går snett (AVVIK) till målet
        fl = LineString(fil)
        t = fl.project(Point(mal[g]))
        q_ = fl.interpolate(t)
        filerna[g] = (fil, frad)
        lamnar[g] = min(max(t - min(math.dist((q_.x, q_.y), mal[g]), SNETT_MAX) / math.tan(AVVIK),
                            fl.project(Point(fil[1]))), fl.length)
    # på varje sida lämnar ett rör knippet efter dem som ligger utanför det (CC_KNIPPE längre fram), så att det inte
    # går ut genom deras filer
    for sida in (filer[:len(vanster)], filer[len(vanster):][::-1]):
        for g_ut, g in zip(sida, sida[1:]):
            lamnar[g] = min(max(lamnar[g], lamnar[g_ut] + CC_KNIPPE), LineString(filerna[g][0]).length)
    for j, g in enumerate(filer):
        s_ = stig_ordning[j]
        fil, frad = filerna[g]
        t = lamnar[g]
        # filens punkter fram till t
        langd = 0.0
        pts, rr = [fil[0]], [0.0]
        for i in range(1, len(fil)):
            seg = math.dist(fil[i - 1], fil[i])
            if langd + seg >= t:
                f = (t - langd) / max(seg, 1e-9)
                pts.append((fil[i - 1][0] + (fil[i][0] - fil[i - 1][0]) * f, fil[i - 1][1] + (fil[i][1] - fil[i - 1][1]) * f))
                rr.append(0.0)
                break
            langd += seg
            pts.append(fil[i])
            rr.append(frad[i])
        ut_stig[g] = s_
        ut_vag[g] = (pts, rr)
    return ut_stig, ut_vag
