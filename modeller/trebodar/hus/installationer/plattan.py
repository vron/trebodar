"""Rör ingjutna i mellanbjälklaget utan räta vinklar (#87): rören går raka, snett där det behövs, direkt från punkt till
punkt, med mjuka böjar med stor radie runt det som de inte får gå genom.

En nivå i bjälklaget beskrivs som en karta (Karta) för rör med en viss radie i plan (och halv höjd, för ett knippe rör
sida vid sida): där rörets mittlinje får gå (bjälklaget innanför kanterna, utan hålen och hindren, som är förstorade
med rörets radie och SPEL), zonerna som rören helst går utanför (t.ex. pelarnas genomstansningszon: en meter i en zon
räknas som ZON_FAKTOR meter) och järnen i nivån. De vågräta järnen i nivån (vinkeljärnen vid kanterna) blir band som
rören går runt och genom bara mellan järnen; de lodräta (källarväggarnas, som når upp i bjälklaget) går rören mellan.
Kartorna för flera nivåer (kartor) har gemensamma noder, så att vägen kan byta nivå där båda är fria (inte i ej_byte,
t.ex. golvvärmens stråk).

Vägen mellan två punkter (vag2) är den billigaste genom nivåerna i kartornas synlighetsgraf, med hindrens utspringande
hörn som noder och en marginal (MARGINAL) till hindren så att böjarna ryms, och svängarna räknade (SVANG): runt det som
är upptaget (andra rörs stigare) och helst inte genom andra rör i samma nivå (KORS per korsning och KORS_LANGS per mm
längs röret, mer där korsningen inte får ligga) och inte där de byter nivå. Extra noder runt vägens ändar (RING) och
där den går snett genom ett annat rör låter den korsa brant eller gå runt. En punkt i ett hinder (en stigare i en vägg
eller bland vinkeljärnen vid en ytterväggs kant) leds först rakt ut till det fria, längs järnen och inom bjälklaget.
Där vägen går över en rad lodräta järn läggs den mitt i glipan mellan två järn (glipor). Hörnen rundas (rundad) med den
största radien upp till BOJ_RADIE som håller rörets mittlinje i det fria och fri från järnen och det som är upptaget.

Kartorna byggs en gång per nivå och rör (cache hos den som bygger dem). Synlighetsgrafen och vägarna är dyra (en dryg
halv minut för alla elrören) och rena funktioner av sina indata, så de sparas i ramverkets minne (modellering.minne)
under en kontrollsumma över indata och den här filen: oförändrade kartor och punkter ger vägarna direkt, och en ändring
i indata eller koden räknar om dem. Koordinater i mm (K-05).
"""
from __future__ import annotations

import heapq
import math
from collections.abc import Callable, Sequence
from typing import TypeVar
from dataclasses import dataclass

import numpy as np
import shapely
from shapely.geometry import LineString, Point, Polygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union
from shapely.strtree import STRtree

from modellering import minne

from trebodar.hus.armering.armering import jarnen_i_nivan

from .genomforingar import kallarvaggarna

Punkt = tuple[float, float]
_KOD = minne.kod(__file__)     # minnets nyckel: den här filen och bibliotekens versioner

BOJ_RADIE = 600.0              # böjarnas största radie i plan
MINSTA_RADIE = 60.0            # och den minsta (FXP16:s minsta böjradie): i trängre hörn bryts röret skarpt
MARGINAL = 80.0                # vägen läggs så långt från hindren (utom ut till punkterna), så att böjarna ryms
ZON_FAKTOR = 3.0               # en meter i en zon räknas som så många meter
SPEL = 5.0                     # fritt mellan rörets yta och hindren och järnen
LEDNING = 1500.0               # så långt leds en punkt i ett hinder rakt ut till det fria
SVANG = 1500.0                 # en radians sväng i vägen kostar som så många mm (raka vägar före korta)
_BAND_AVSTAND = 260.0          # vågräta järn i nivån med högst så långt emellan bildar ett band


@dataclass(frozen=True, eq=False)
class Karta:
    """En nivå i bjälklaget (z: rörens mitt) för rör med radien r."""
    r: float
    z: float
    fritt: BaseGeometry                          # där rörets mittlinje får gå
    marg: BaseGeometry                           # det fria med marginalen, där vägen läggs
    hinder: tuple[BaseGeometry, ...]             # hindren, förstorade, i sammanhängande delar
    trad: STRtree                                # över hindren
    zoner: np.ndarray                            # zonerna, cirklar: x, y, radie (n × 3)
    faktor: float
    noder: np.ndarray                            # synlighetsgrafens noder (n × 2)
    grannar: tuple[tuple[tuple[int, float], ...], ...]
    staver: tuple[tuple[LineString, float], ...]     # vågräta järn i nivån (Ø)
    lodrata: tuple[tuple[Point, float], ...]         # lodräta järn genom nivån (Ø)
    jarntrad: STRtree                                # över järnen (staver, sedan lodrata)
    band: tuple[Polygon, ...] = ()                   # banden av vågräta järn (förstorade)
    slappa: tuple[Polygon, ...] = ()                 # hinder som en punkt i dem får ledas ut ur (förstorade)
    enskilda: tuple[BaseGeometry, ...] = ()          # hindren var för sig (förstorade), utom de som släpper ut
    enskilda_trad: STRtree | None = None
    ej_byte: BaseGeometry | None = None              # där vägen inte byter nivå (t.ex. golvvärmens stråk)
    nyckel: str = ""                                 # kontrollsumman över kartans indata (minnet, vag2)


@dataclass(frozen=True)
class _Band:
    """En rad parallella vågräta järn: rektangeln runt dem (förstorad), riktningen ("x" eller "y"), järnens lägen
    tvärs riktningen och deras utsträckning längs den."""
    yta: Polygon
    rikt: str
    lagen: tuple[float, ...]
    langs: tuple[float, float]
    d: float


def _band(staver: Sequence[tuple[LineString, float]], rr: float, omrade: BaseGeometry) -> list[_Band]:
    """Raderna av parallella vågräta järn med samma utsträckning (vinkeljärnen längs en vägg) som rektanglar,
    förstorade med rr, förlängda ut till områdets kant om den är nära (rören går inte mellan järnen och kanten)."""
    grupper: dict[tuple[str, int, int], list[tuple[float, LineString, float]]] = {}
    for g, d in staver:
        (x0, y0), (x1, y1) = g.coords[0], g.coords[-1]
        if abs(x1 - x0) >= abs(y1 - y0):
            nyckel, pos = ("x", round(min(x0, x1) / 50.0), round(max(x0, x1) / 50.0)), (y0 + y1) / 2
        else:
            nyckel, pos = ("y", round(min(y0, y1) / 50.0), round(max(y0, y1) / 50.0)), (x0 + x1) / 2
        grupper.setdefault(nyckel, []).append((pos, g, d))
    kant = omrade.boundary
    ut: list[_Band] = []
    for (rikt, _, _), lst in grupper.items():
        lst.sort(key=lambda t: t[0])
        rader: list[list[tuple[float, LineString, float]]] = [[lst[0]]]
        for t in lst[1:]:
            if t[0] - rader[-1][-1][0] > _BAND_AVSTAND:
                rader.append([])
            rader[-1].append(t)
        for rad in rader:
            x0, y0, x1, y1 = unary_union([g for _, g, _ in rad]).bounds
            d = max(d for _, _, d in rad)
            dmax = d / 2 + rr
            if rikt == "y":                           # i rader längs x: byt axlarna, räkna som för "x" och byt tillbaka
                x0, y0, x1, y1 = y0, x0, y1, x1
            s0, s1 = x0, x1
            y0, y1 = y0 - dmax, y1 + dmax
            avst = [kant.distance(Point(x_, (y0 + y1) / 2) if rikt == "x" else Point((y0 + y1) / 2, x_))
                    for x_ in (x0, x1)]
            if min(avst) < 700.0:                     # förläng mot kanten längs järnen, i den ände där den är nära
                if avst[0] <= avst[1]:
                    x0 -= avst[0] + 50.0
                else:
                    x1 += avst[1] + 50.0
            hörn = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
            ut.append(_Band(Polygon(hörn if rikt == "x" else [(b, a) for a, b in hörn]), rikt,
                            tuple(t[0] for t in rad), (s0, s1), d))
    return ut


def _passager(band: Sequence[_Band], rr: float, marg: BaseGeometry, fritt: BaseGeometry,
              fri_fran_jarn: Callable[[BaseGeometry], bool]) -> list[tuple[Punkt, Punkt]]:
    """Passagerna genom banden mitt emellan två järn (längs järnen), där båda ändarna når det fria med marginalen
    (högst 300 mm utanför bandet) och resten av passagen går i det fria: rören går genom ett band av vinkeljärn bara
    så, mellan järnen."""
    ut: list[tuple[Punkt, Punkt]] = []
    for b in band:
        for a, c in zip(b.lagen, b.lagen[1:]):
            if c - a < 2 * (rr + b.d / 2):
                continue
            m = (a + c) / 2

            def punkt(s: float) -> Punkt:
                return (s, m) if b.rikt == "x" else (m, s)
            lo = next((s for s in np.arange(b.langs[0] - rr - 2.0, b.langs[0] - 300.0, -10.0)
                       if marg.contains(Point(punkt(float(s))))), None)
            hi = next((s for s in np.arange(b.langs[1] + rr + 2.0, b.langs[1] + 300.0, 10.0)
                       if marg.contains(Point(punkt(float(s))))), None)
            if lo is None or hi is None:
                continue
            linje = LineString([punkt(float(lo)), punkt(float(hi))])
            utanfor = linje.difference(b.yta)
            if (utanfor.is_empty or fritt.contains(utanfor)) and fri_fran_jarn(linje):
                ut.append((punkt(float(lo)), punkt(float(hi))))
    return ut


def _glipor_i_raderna(lodrata: Sequence[tuple[Point, float]], rr: float) -> list[Punkt]:
    """Noderna i raderna av lodräta järn (källarväggarnas, kärnans mittlinje): mitt i varje glipa mellan två järn där
    ett rör ryms, och förbi radens ändar."""
    ut: list[Punkt] = []
    for _, (_, karna) in kallarvaggarna().items():
        omr = karna.buffer(40.0)
        rad = [(g, d) for g, d in lodrata if omr.contains(g)]
        if not rad:
            continue
        x0, y0, x1, y1 = karna.bounds
        langs_x = x1 - x0 >= y1 - y0
        c = (y0 + y1) / 2 if langs_x else (x0 + x1) / 2
        t: list[float] = []
        for s_ in sorted(g.x if langs_x else g.y for g, _ in rad):
            if not t or s_ - t[-1] > 30.0:
                t.append(s_)
        d = max(d_ for _, d_ in rad)
        bredd = 2 * (rr + d / 2)
        lagen = [(a + b_) / 2 for a, b_ in zip(t, t[1:]) if b_ - a > bredd] + [t[0] - bredd, t[-1] + bredd]
        ut += [((m, c) if langs_x else (c, m)) for m in lagen]
    return ut


def _reflexa(geom: BaseGeometry, ut_: float = 1.0, fritt: BaseGeometry | None = None) -> np.ndarray:
    """Hörnen där den fria ytan går in (hindrens utspringande hörn), flyttade ut_ längs bisektrisen ut i det fria (mindre
    om punkten då hamnar utanför fritt)."""
    ut: list[np.ndarray] = []
    for p in getattr(geom, "geoms", [geom]):
        for ring, yttre in [(p.exterior, True), *((i, False) for i in p.interiors)]:
            c = np.asarray(ring.coords)[:-1]
            if len(c) < 3:
                continue
            if yttre != ring.is_ccw:                  # det fria till vänster: yttre ringen moturs, hålen medurs
                c = c[::-1]
            a, b, cc = np.roll(c, 1, axis=0), c, np.roll(c, -1, axis=0)
            kryss = (b[:, 0] - a[:, 0]) * (cc[:, 1] - b[:, 1]) - (b[:, 1] - a[:, 1]) * (cc[:, 0] - b[:, 0])
            for q, k, pa, pc in zip(b, kryss, a, cc):
                if k < -1e-6:
                    u = (q - pa) / max(float(np.linalg.norm(q - pa)), 1e-9)
                    w = (pc - q) / max(float(np.linalg.norm(pc - q)), 1e-9)
                    n = -(np.array([u[1], -u[0]]) + np.array([w[1], -w[0]]))
                    n = n / max(float(np.linalg.norm(n)), 1e-9)
                    for f in (ut_, ut_ / 2, ut_ / 4, 2.0):
                        if fritt is None or fritt.contains(Point(q + f * n)):
                            ut.append(q + f * n)
                            break
    return np.array(ut).reshape(-1, 2)


@dataclass(frozen=True, eq=False)
class _Yta:
    """En nivås fria yta och järn, före grafen: kandidaterna till noder och passagerna genom banden."""
    r: float
    z: float
    fritt: BaseGeometry
    marg: BaseGeometry
    delar: tuple[BaseGeometry, ...]
    zon: np.ndarray
    faktor: float
    staver: tuple[tuple[LineString, float], ...]
    lodrata: tuple[tuple[Point, float], ...]
    jarntrad: STRtree
    kandidater: np.ndarray
    passager: tuple[tuple[Punkt, Punkt], ...]
    band: tuple[Polygon, ...]
    slappa: tuple[Polygon, ...]
    enskilda: tuple[BaseGeometry, ...]


def _ytan(omrade: BaseGeometry, hinder: Sequence[BaseGeometry], z: float, r: float,
          zoner: Sequence[tuple[float, float, float]], faktor: float, slappa: Sequence[BaseGeometry] = (),
          hojd: float | None = None) -> _Yta:
    rr = r + SPEL
    jarn = jarnen_i_nivan(z - (hojd or r), z + (hojd or r))
    staver = tuple((g, d) for g, d in jarn if g.geom_type != "Point")
    lodrata = tuple((g, d) for g, d in jarn if g.geom_type == "Point")
    jarntrad = STRtree([g for g, _ in (*staver, *lodrata)])
    band = _band(staver, rr, omrade)
    jarnen = [g.buffer(rr + d / 2, quad_segs=2) for g, d in lodrata]
    H = unary_union([*(h.buffer(rr, quad_segs=2, join_style="mitre") for h in hinder), *(b.yta for b in band),
                     *jarnen])
    delar = tuple(getattr(H, "geoms", [H]))
    fritt = omrade.difference(H)
    marg = fritt.buffer(-MARGINAL, join_style="mitre")
    zon = np.array(list(zoner), dtype=float).reshape(-1, 3)
    shapely.prepare(fritt)
    shapely.prepare(marg)

    def fri_fran_jarn(g: BaseGeometry) -> bool:
        alla = (*staver, *lodrata)
        return all(g.distance(alla[int(i)][0]) >= r + alla[int(i)][1] / 2 + SPEL
                   for i in jarntrad.query(g.buffer(r + 6.0 + SPEL)))
    passager = _passager(band, rr, marg, fritt, fri_fran_jarn)
    # kandidaterna: det fria områdets inåtgående hörn (utom runt de lodräta järnen) MARGINAL ut i det fria, glipornas
    # mitt i järnens rader
    hornen = _reflexa(fritt, MARGINAL, fritt)
    if len(hornen) and lodrata:
        jc = np.array([[g.x, g.y] for g, _ in lodrata])
        dmin = np.min(np.hypot(hornen[:, None, 0] - jc[None, :, 0], hornen[:, None, 1] - jc[None, :, 1]), axis=1)
        hornen = hornen[dmin > rr + 6.0 + MARGINAL + 1.0]
    glipor_ = np.array(_glipor_i_raderna(lodrata, rr)).reshape(-1, 2)
    N = np.vstack([hornen, glipor_])
    return _Yta(r, z, fritt, marg, delar, zon, faktor, staver, lodrata, jarntrad, N, tuple(passager),
                tuple(b.yta for b in band), tuple(h.buffer(rr, quad_segs=2) for h in slappa),
                tuple(h.buffer(rr, quad_segs=2, join_style="mitre") for h in hinder
                      if not any(h is s_ for s_ in slappa)))


def _graf(y: _Yta, N: np.ndarray, ej_byte: BaseGeometry | None = None) -> Karta:
    """Kartan med synlighetsgrafen över noderna N (de som ligger i det fria) och passagerna genom banden."""
    N = N[shapely.contains(y.fritt, shapely.points(N))] if len(N) else N
    N = np.unique(np.round(np.vstack([N.reshape(-1, 2), *(np.array([p, q]) for p, q in y.passager)]), 1), axis=0)
    grannar: list[list[tuple[int, float]]] = [[] for _ in range(len(N))]
    if len(N) > 1:
        i, j = np.triu_indices(len(N), 1)
        ok = np.unpackbits(minne.sparad(
            minne.summa("synlighet", _KOD, y.fritt, N),
            lambda: np.packbits(shapely.contains(y.fritt, shapely.linestrings(np.stack([N[i], N[j]], axis=1))))),
            count=len(i)).astype(bool)
        kost = _kostnad(N[i[ok]], N[j[ok]], y.zon, y.faktor)
        for a, b_, c in zip(i[ok], j[ok], kost):
            grannar[int(a)].append((int(b_), float(c)))
            grannar[int(b_)].append((int(a), float(c)))
    index = {(float(x), float(y_)): n for n, (x, y_) in enumerate(N)}
    for p, q in y.passager:                       # passagerna genom banden, utanför det fria
        (px, py), (qx, qy) = np.round(np.array([p, q]), 1)
        ip, iq = index[(float(px), float(py))], index[(float(qx), float(qy))]
        c = float(_kostnad(np.array([p]), np.array([q]), y.zon, y.faktor)[0])
        grannar[ip].append((iq, c))
        grannar[iq].append((ip, c))
    nyckel = minne.summa("karta", _KOD, y.r, y.z, y.fritt, y.marg, y.delar, y.zon, y.faktor, N, y.passager, y.staver,
                         y.lodrata, y.band, y.slappa, y.enskilda, ej_byte)
    return Karta(y.r, y.z, y.fritt, y.marg, y.delar, STRtree(list(y.delar)), y.zon, y.faktor, N,
                 tuple(tuple(g) for g in grannar), y.staver, y.lodrata, y.jarntrad, y.band, y.slappa, y.enskilda,
                 STRtree(list(y.enskilda)) if y.enskilda else None, ej_byte, nyckel)




def kartor(omrade: BaseGeometry, hinder: Sequence[Sequence[BaseGeometry]], z: Sequence[float], r: float,
           zoner: Sequence[tuple[float, float, float]] = (), faktor: float = ZON_FAKTOR,
           slappa: Sequence[BaseGeometry] = (), hojd: float | None = None,
           ej_byte: BaseGeometry | None = None) -> tuple[Karta, ...]:
    """Kartorna för flera nivåer (hindren och z per nivå) med gemensamma noder, så att vägen kan byta nivå (vag2) där
    båda nivåerna är fria (inte i ej_byte). r: rörets radie i plan; hojd: dess halva höjd (järnen i nivån), om den är
    mindre (ett knippe rör sida vid sida)."""
    ytor = [_ytan(omrade, [*h, *slappa], z_, r, zoner, faktor, slappa, hojd) for h, z_ in zip(hinder, z, strict=True)]
    N = np.vstack([y.kandidater.reshape(-1, 2) for y in ytor])
    return tuple(_graf(y, N, ej_byte) for y in ytor)


def _kostnad(P: np.ndarray, Q: np.ndarray, zon: np.ndarray, faktor: float) -> np.ndarray:
    """Sträckornas P–Q kostnad: längden, och längden i zonerna (cirklar) gånger faktor − 1 extra."""
    P, Q = np.asarray(P, dtype=float).reshape(-1, 2), np.asarray(Q, dtype=float).reshape(-1, 2)
    D = Q - P
    langd = np.hypot(D[:, 0], D[:, 1])
    if not len(zon) or faktor == 1.0 or not len(P):
        return langd
    # för varje sträcka och cirkel: t där |P + t D − C| = R, klippt till 0..1
    a = np.maximum((D * D).sum(axis=1), 1e-12)[:, None]
    F = P[:, None, :] - zon[None, :, :2]
    b = 2 * (F * D[:, None, :]).sum(axis=2)
    c = (F * F).sum(axis=2) - zon[None, :, 2] ** 2
    disk = b * b - 4 * a * c
    rot = np.sqrt(np.maximum(disk, 0.0))
    t1 = np.clip((-b - rot) / (2 * a), 0.0, 1.0)
    t2 = np.clip((-b + rot) / (2 * a), 0.0, 1.0)
    i_zon = np.where(disk > 0, t2 - t1, 0.0).sum(axis=1) * langd
    return langd + (faktor - 1.0) * i_zon


def jarnfri(k: Karta, g: BaseGeometry, utom: float = 0.0) -> bool:
    """Om röret längs g går fritt (SPEL) från järnen i nivån; utom: så nära g:s ändar gäller det inte (där röret går
    upp eller ned mellan järnen, som stigaren redan är placerad för)."""
    jarn = (*k.staver, *k.lodrata)
    for i in k.jarntrad.query(g.buffer(k.r + 6.0 + SPEL)):
        j, d = jarn[int(i)]
        if g.distance(j) < k.r + d / 2 + SPEL:
            if utom > 0.0 and g.geom_type == "LineString":
                a, b = Point(g.coords[0]), Point(g.coords[-1])
                if a.distance(j) < utom or b.distance(j) < utom:
                    continue
            return False
    return True


def ledning(k: Karta, p: Punkt, mot: Punkt, ut: Punkt | None = None,
            straff: Callable[[Punkt, Punkt], float] | None = None,
            fri: Callable[[Punkt, Punkt], bool] | None = None) -> list[Punkt]:
    """Från p rakt ut i det fria med marginalen: längs ut om den är given, annars i den av 16 riktningar som når dit
    kortast (vid lika den närmast mot, och med straffet, t.ex. för att korsa andra rör), fritt från järnen och utan
    att gå genom ett annat hinder än det p står i (och fri enligt fri, t.ex. från andra rörs stigare)."""
    if k.marg.contains(Point(p)):
        return []
    # ledningen får gå genom bandet av järn som p står i (mellan järnen) och närmast p, inte genom andra hinder
    # och genom de hinder som får släppa ut den (t.ex. en pelares kontrollsnitt som p står i)
    sma = [h for h in k.slappa if h.contains(Point(p))]
    eget = unary_union([Point(p).buffer(k.r + SPEL + 20.0), *(h.buffer(1.0) for h in sma),
                        *(b_.buffer(k.r + SPEL + 15.0, join_style="mitre") for b_ in k.band if b_.contains(Point(p)))])
    riktningar = [ut] if ut is not None else [(math.cos(a * math.pi / 8), math.sin(a * math.pi / 8)) for a in range(16)]
    mal = math.atan2(mot[1] - p[1], mot[0] - p[0])
    bast: tuple[float, Punkt] | None = None
    for u in riktningar:
        n = math.hypot(*u)
        u = (u[0] / n, u[1] / n)
        for s in np.arange(10.0, LEDNING + 1.0, 10.0):
            q = (p[0] + u[0] * s, p[1] + u[1] * s)
            if not k.marg.contains(Point(q)):
                continue
            seg = LineString([p, q])
            utanfor = seg.difference(eget)
            if not utanfor.is_empty and not k.fritt.buffer(1.0).contains(utanfor):
                break                                       # utanför bjälklaget (t.ex. över trapphålet)
            andra = [] if utanfor.is_empty else [int(i) for i in k.trad.query(utanfor)
                                                 if k.hinder[int(i)].intersects(utanfor)]
            # och inte genom ett annat hinder i det som p står i (t.ex. ett rör genom en pelares kontrollsnitt)
            if not andra and k.enskilda_trad is not None:
                andra = [int(i) for i in k.enskilda_trad.query(seg) if k.enskilda[int(i)].intersects(seg)
                         and not k.enskilda[int(i)].contains(Point(p))]
            if andra or not jarnfri(k, seg, utom=k.r + 10.0) or (fri is not None and not fri(p, q)):
                break
            vinkel = abs((math.atan2(u[1], u[0]) - mal + math.pi) % (2 * math.pi) - math.pi)
            varde = float(s) + 0.3 * SVANG * vinkel + (straff(p, q) if straff is not None else 0.0)
            if bast is None or varde < bast[0]:
                bast = (varde, q)
            break
    if bast is None:
        raise ValueError(f"ingen väg ut i det fria från ({p[0]:.0f}, {p[1]:.0f})")
    return [bast[1]]


def _synliga(k: Karta, p: Punkt) -> list[tuple[int, float]]:
    if not len(k.noder):
        return []
    linjer = shapely.linestrings(np.stack([np.broadcast_to(np.asarray(p), k.noder.shape), k.noder], axis=1))
    ok = shapely.contains(k.fritt, linjer)
    kost = _kostnad(np.broadcast_to(np.asarray(p, dtype=float), (int(ok.sum()), 2)), k.noder[ok], k.zoner, k.faktor)
    return [(int(i), float(c)) for i, c in zip(np.nonzero(ok)[0], kost)]




def _kost(k: Karta, p: Punkt, q: Punkt) -> float:
    return float(_kostnad(np.array([p]), np.array([q]), k.zoner, k.faktor)[0])


def _sving(a: Punkt, b: Punkt, c: Punkt) -> float:
    u = (b[0] - a[0], b[1] - a[1])
    w = (c[0] - b[0], c[1] - b[1])
    if math.hypot(*u) < 1e-6 or math.hypot(*w) < 1e-6:
        return 0.0
    return abs(math.atan2(u[0] * w[1] - u[1] * w[0], u[0] * w[0] + u[1] * w[1]))


def _glatta(k: Karta, pts: list[Punkt], forsta: int, sista: int,
            straff: Callable[[Punkt, Punkt], float] | None = None,
            fri: Callable[[Punkt, Punkt], bool] | None = None) -> list[Punkt]:
    """Vägen rakare: brytpunkterna mellan två punkter (bland forsta..sista, inte ledningarnas) tas bort där en rak
    sträcka mellan dem är fri och billigare, med svängarna (SVANG per radian) och straffet för sträckorna (t.ex. för
    att korsa andra rör), t.ex. en omväg runt en zon med flera böjar."""
    pts = list(pts)

    def sving(i: int, q: list[Punkt]) -> float:
        return _sving(q[i - 1], q[i], q[i + 1]) if 0 < i < len(q) - 1 else 0.0

    def kost(q: list[Punkt], i: int, j: int) -> float:
        """Kostnaden för sträckorna i..j och svängarna i i..j (och i ändarna mot grannarna)."""
        return sum(_kost(k, q[m], q[m + 1]) + (straff(q[m], q[m + 1]) if straff else 0.0) for m in range(i, j)) + \
            SVANG * sum(sving(m, q) for m in range(i, j + 1))
    andrad = True
    while andrad:
        andrad = False
        for i in range(max(forsta - 1, 0), min(sista, len(pts) - 2)):
            for j in range(min(sista + 1, len(pts) - 1), i + 1, -1):
                if not k.fritt.contains(LineString([pts[i], pts[j]])) or (fri is not None and not fri(pts[i], pts[j])):
                    continue
                ny_ = pts[:i + 1] + pts[j:]
                if kost(ny_, i, i + 1) < kost(pts, i, j) - 1.0:
                    sista -= j - i - 1
                    pts = ny_
                    andrad = True
                    break
            if andrad:
                break
    return pts




def glipor(k: Karta, pts: Sequence[Punkt]) -> list[Punkt]:
    """Vägen genom raderna av lodräta järn (källarväggarnas, i nivån): där en sträcka går för nära ett järn läggs en
    brytpunkt mitt i den närmaste glipan i järnens rad, så att röret går mitt emellan två järn."""
    ut = [pts[0]]
    for q in pts[1:]:
        ut += _genom_raden(k, ut[-1], q, len(ut) == 1, q == pts[-1])
    return ut


def _genom_raden(k: Karta, p: Punkt, q: Punkt, forsta: bool, sista: bool, djup: int = 0) -> list[Punkt]:
    seg = LineString([p, q])
    if seg.length < 1.0 or jarnfri(k, seg, utom=(k.r + 10.0) if (forsta or sista) else 0.0):
        return [q]
    if djup > 6:
        return [q]                     # ingen glipa som går: sträckan som den är (krocken syns i kontrollerna)
    # järnet som sträckan går för nära, och dess rad: de lodräta järnen inom 400 mm på en linje genom det
    nara = [(g, d) for g, d in k.lodrata if seg.distance(g) < k.r + d / 2 + SPEL]
    if not nara:
        return [q]                     # ett vågrätt järn: sträckan som den är (krocken syns i kontrollerna)
    j0 = min(nara, key=lambda t: seg.project(t[0]))[0]
    rad = sorted((g for g, _ in k.lodrata if g.distance(j0) < 450.0), key=lambda g: (g.x, g.y))
    xs, ys = [g.x for g in rad], [g.y for g in rad]
    langs_x = (max(xs) - min(xs)) >= (max(ys) - min(ys))
    t = sorted(g.x if langs_x else g.y for g in rad)
    c = float(np.mean(ys if langs_x else xs))
    luckor = [(m, b - a) for a, b in zip(t, t[1:]) for m in [(a + b) / 2] if b - a > 2 * (k.r + 6.0 + SPEL)]
    # korsningen med radens linje
    linje = LineString([(min(t) - 2000.0, c), (max(t) + 2000.0, c)] if langs_x else
                       [(c, min(t) - 2000.0), (c, max(t) + 2000.0)])
    x = seg.intersection(linje)
    if x.is_empty or x.geom_type != "Point":
        return [q]
    s0 = x.x if langs_x else x.y
    for m, _ in sorted(luckor, key=lambda t_: abs(t_[0] - s0)):
        g = (m, c) if langs_x else (c, m)
        if k.fritt.contains(LineString([p, g])) and k.fritt.contains(LineString([g, q])):
            ut_ = _genom_raden(k, p, g, forsta, False, djup + 1)
            return ut_ + _genom_raden(k, g, q, False, sista, djup + 1)
    return [q]


def rundad(k: Karta, pts: Sequence[Punkt], radie: float = BOJ_RADIE,
           fri: Callable[[Punkt, Punkt], bool] | None = None) -> list[float]:
    """Hörnens radier (en per punkt, 0 i ändarna och där hörnet inte rundas): den största upp till radie där bågen
    håller rörets mittlinje i det fria (och fri enligt fri, t.ex. från andra rörs stigare) och fri från järnen, och
    tangenterna högst halva sträckorna (hela vid ändarna som går lodrätt)."""
    ut = [0.0] * len(pts)
    for i in range(1, len(pts) - 1):
        a, b, c = (np.asarray(pts[i - 1]), np.asarray(pts[i]), np.asarray(pts[i + 1]))
        lu, lw = float(np.linalg.norm(b - a)), float(np.linalg.norm(c - b))
        u, w = (b - a) / lu, (c - b) / lw
        vinkel = math.acos(max(-1.0, min(1.0, float(u @ w))))
        if vinkel < math.radians(0.5):
            continue
        tmax = min(lu if i == 1 else lu / 2, lw if i == len(pts) - 2 else lw / 2)
        r = min(radie, tmax / math.tan(vinkel / 2))
        while r >= MINSTA_RADIE:
            bp = bage_punkter(pts[i - 1], pts[i], pts[i + 1], r)
            bage = LineString(bp)
            if k.fritt.contains(bage) and jarnfri(k, bage) and (fri is None or all(fri(p, q) for p, q in zip(bp, bp[1:]))):
                ut[i] = r
                break
            r *= 0.8
    return ut


def bage_punkter(a: Punkt, b: Punkt, c: Punkt, r: float, steg: float = math.radians(5.0)) -> list[Punkt]:
    """Hörnet b mellan sträckorna a–b och b–c rundat med radien r: bågens punkter från tangentpunkten mot a till den
    mot c."""
    A, B, C = np.asarray(a, dtype=float), np.asarray(b, dtype=float), np.asarray(c, dtype=float)
    u = (B - A) / np.linalg.norm(B - A)
    w = (C - B) / np.linalg.norm(C - B)
    vinkel = math.acos(max(-1.0, min(1.0, float(u @ w))))
    if vinkel < 1e-6 or r <= 0.0:
        return [b]
    t = r * math.tan(vinkel / 2)
    p1, p2 = B - u * t, B + w * t
    sida = 1.0 if u[0] * w[1] - u[1] * w[0] > 0 else -1.0
    n = np.array([-u[1], u[0]]) * sida                  # mot bågens mittpunkt
    m = p1 + n * r
    a0 = math.atan2(p1[1] - m[1], p1[0] - m[0])
    steg_n = max(1, math.ceil(vinkel / steg))
    return [(float(m[0] + r * math.cos(a0 + sida * vinkel * s / steg_n)),
             float(m[1] + r * math.sin(a0 + sida * vinkel * s / steg_n))) for s in range(steg_n + 1)]


def rundad_linje(pts: Sequence[Punkt], radier: Sequence[float]) -> list[Punkt]:
    """Polylinjen genom pts med hörnen rundade med radierna (för ritningarna)."""
    ut: list[Punkt] = [pts[0]]
    for i in range(1, len(pts) - 1):
        ut += bage_punkter(pts[i - 1], pts[i], pts[i + 1], radier[i]) if radier[i] > 0 else [pts[i]]
    return [*ut, pts[-1]]


BYTE = 800.0                   # ett byte av nivå kostar som så många mm (rampens två små böjar)
RAMP = 250.0                   # där röret byter nivå lutar det över så lång sträcka (mitt i ett fritt område)


@dataclass(frozen=True)
class Dragning:
    """Ett rörs väg genom nivåerna: brytpunkterna (z: nivån, i ramperna mellan två nivåer däremellan) och hörnens
    radier i plan."""
    punkter: tuple[tuple[float, float, float], ...]
    radier: tuple[float, ...]


def _bytespunkter(kartor: Sequence[Karta]) -> dict[tuple[int, int], tuple[int, int]]:
    """Noderna där vägen kan byta nivå (samma punkt i två nivåer, fri i båda en halv ramp runt sig): (nivå, nod) ->
    (annan nivå, nod)."""
    ut: dict[tuple[int, int], tuple[int, int]] = {}
    index = [{(float(x), float(y)): n for n, (x, y) in enumerate(k.noder)} for k in kartor]
    for la, ka in enumerate(kartor):
        for lb in range(la + 1, len(kartor)):
            kb = kartor[lb]
            gemensamma = [(q, na, index[lb][q]) for q, na in index[la].items() if q in index[lb]]
            if not gemensamma:
                continue
            skivor = shapely.buffer(shapely.points(np.array([q for q, _, _ in gemensamma])), RAMP / 2, quad_segs=4)
            ok = shapely.contains(ka.fritt, skivor) & shapely.contains(kb.fritt, skivor)
            for ej in (ka.ej_byte, kb.ej_byte):
                if ej is not None:
                    ok &= ~shapely.intersects(ej, skivor)
            for (q, na, nb), o in zip(gemensamma, ok):
                if o:
                    ut[(la, na)] = (lb, nb)
                    ut[(lb, nb)] = (la, na)
    return ut


_BYTEN: dict[tuple[int, ...], dict[tuple[int, int], tuple[int, int]]] = {}


KORS = 2000.0                  # att korsa ett annat rör i samma nivå kostar som så många mm (det ena går då förbi
#                                det andra, el/bjalklag/ingjutna.korsningar)
KORS_LANGS = 50.0              # och varje mm i det andra röret (längs det) så många mm till
KORS_DYR = 200000.0            # och så många till där korsningen inte får ligga (dyr_korsning, t.ex. golvvärmens stråk)
RING = (300.0, 800.0)          # extra noder runt vägens ändar på de här avstånden,
RING_RIKTNINGAR = 12           # åt så många håll,
RING_GRANNAR = 3000.0          # med kanter till kartans noder så nära


def vag2(kartor: Sequence[Karta], a: Punkt, b: Punkt, fran: Sequence[int], till: Sequence[int],
         upptaget: Sequence[Sequence[BaseGeometry]] = (), led_a: dict[int, Sequence[Punkt]] | None = None,
         led_b: dict[int, Sequence[Punkt]] | None = None, kost_niva: Sequence[float] = (),
         mjuka: Sequence[Sequence[BaseGeometry]] = (), radie_a: float | None = None,
         extra_noder: Sequence[Sequence[Punkt]] = (), glipor_: bool = True,
         dyr_korsning: BaseGeometry | None = None) -> Dragning:
    """Den billigaste vägen från a till b genom nivåerna (kartorna, med gemensamma noder från kartor()): röret går in i
    nivåerna fran vid a och ut ur nivåerna till vid b, byter nivå där båda är fria (BYTE, RAMP), går inte genom det
    som är upptaget i en nivå (andra rörs stigare) och helst inte genom de mjuka hindren (andra rör: KORS per hinder,
    så att vägen hellre byter nivå eller går runt). kost_niva: extra kostnad per mm i varje nivå (t.ex. för att hålla
    sig i en). extra_noder: fler noder per nivå för den här vägen (t.ex. bredvid andra rör, så att den kan gå jämsides
    med dem i stället för att korsa dem). dyr_korsning: där vägen helst inte korsar ett annat rör (KORS_DYR).

    Resultatet sparas i minnet under en kontrollsumma över kartorna och alla argumenten."""
    return minne.sparad(
        minne.summa("vag2", [k.nyckel for k in kartor], a, b, fran, till, upptaget, led_a, led_b, kost_niva, mjuka,
                    radie_a, extra_noder, glipor_, dyr_korsning),
        lambda: _vag2(kartor, a, b, fran, till, upptaget, led_a, led_b, kost_niva, mjuka, radie_a, extra_noder,
                      glipor_, dyr_korsning))


def _vag2(kartor: Sequence[Karta], a: Punkt, b: Punkt, fran: Sequence[int], till: Sequence[int],
          upptaget: Sequence[Sequence[BaseGeometry]], led_a: dict[int, Sequence[Punkt]] | None,
          led_b: dict[int, Sequence[Punkt]] | None, kost_niva: Sequence[float],
          mjuka: Sequence[Sequence[BaseGeometry]], radie_a: float | None,
          extra_noder: Sequence[Sequence[Punkt]], glipor_: bool, dyr_korsning: BaseGeometry | None) -> Dragning:
    """vag2 utan minnet."""
    nyckel = tuple(id(k) for k in kartor)
    if nyckel not in _BYTEN:
        _BYTEN[nyckel] = _bytespunkter(kartor)
    byten = _BYTEN[nyckel]
    extra = list(kost_niva) + [0.0] * (len(kartor) - len(kost_niva))

    def lista(x: Sequence[Sequence[BaseGeometry]]) -> list[list[BaseGeometry]]:
        return [list(u) for u in (list(x) + [()] * len(kartor))[:len(kartor)]]
    upptagna, mjukt = lista(upptaget), lista(mjuka)
    trad = [STRtree(u) if u else None for u in upptagna]
    mjukt_trad = [STRtree(u) if u else None for u in mjukt]
    korsar: dict[tuple[int, Punkt, Punkt], float] = {}

    def fri(lager: int, p: Punkt, q: Punkt) -> bool:
        t = trad[lager]
        if t is None:
            return True
        linje = LineString([p, q])
        return not any(upptagna[lager][int(i)].intersects(linje) for i in t.query(linje))

    def straff(lager: int, p: Punkt, q: Punkt) -> float:
        t = mjukt_trad[lager]
        if t is None:
            return 0.0
        nyckel_ = (lager, p, q)
        if nyckel_ not in korsar:
            linje = LineString([p, q])
            traffar = [mjukt[lager][int(i)] for i in t.query(linje) if mjukt[lager][int(i)].intersects(linje)]
            bitar = [g.intersection(linje) for g in traffar]
            korsar[nyckel_] = sum(KORS + KORS_LANGS * b.length + (KORS_DYR if dyr_korsning is not None and
                                                                   b.intersects(dyr_korsning) else 0.0)
                                  for b in bitar)
        return korsar[nyckel_]

    def rampens_straff(la_: int, lb_: int, q: Punkt) -> float:
        """Andra rör där vägen byter nivå (i rampen, i båda nivåerna): KORS per rör."""
        skiva = Point(q).buffer(RAMP / 2, quad_segs=2)
        n = 0
        for lx in (la_, lb_):
            t_ = mjukt_trad[lx]
            if t_ is not None:
                n += sum(1 for i in t_.query(skiva) if mjukt[lx][int(i)].intersects(skiva))
        return KORS * n

    def kost(lager: int, c: float, langd: float, p: Punkt | None = None, q: Punkt | None = None) -> float:
        return c + extra[lager] * langd + (straff(lager, p, q) if p is not None and q is not None else 0.0)
    # ut i det fria ur a och b i varje nivå där det går
    starter: dict[int, tuple[list[Punkt], Punkt]] = {}
    for la in fran:
        try:
            led = list(led_a[la]) if led_a and la in led_a else ledning(
                kartor[la], a, b, straff=_i_lagret(straff, la), fri=_i_lagret(fri, la))
        except ValueError:
            continue
        starter[la] = (led, (led or [a])[-1])
    slut: dict[int, tuple[list[Punkt], Punkt]] = {}
    for lb in till:
        try:
            led = list(led_b[lb]) if led_b and lb in led_b else ledning(
                kartor[lb], b, a, straff=_i_lagret(straff, lb), fri=_i_lagret(fri, lb))
        except ValueError:
            continue
        slut[lb] = (led, (led or [b])[-1])
    if not starter or not slut:
        raise ValueError(f"ingen väg ut i det fria från ({(a if not starter else b)[0]:.0f}, "
                         f"{(a if not starter else b)[1]:.0f})")
    # de extra noderna (index efter kartans) och deras grannar: de givna och en krans runt vägens ändar i varje nivå
    # (RING), så att vägen kan gå ut åt alla håll, t.ex. tvärs över ett annat rör i stället för längs det
    pos: list[np.ndarray] = []
    egna: list[dict[int, list[tuple[int, float]]]] = []
    for lager, k in enumerate(kartor):
        givna = list(extra_noder[lager]) if lager < len(extra_noder) else []
        ring = [(c[0] + r_ * math.cos(v), c[1] + r_ * math.sin(v)) for c in
                ([starter[lager][1]] if lager in starter else []) + ([slut[lager][1]] if lager in slut else [])
                for r_ in RING for v in np.linspace(0.0, 2 * math.pi, RING_RIKTNINGAR, endpoint=False)]
        E = np.array(givna + ring, dtype=float).reshape(-1, 2)
        if len(E):
            E = E[shapely.contains(k.fritt, shapely.points(E))]
        alla_ = np.vstack([k.noder.reshape(-1, 2), E])
        n0 = len(k.noder)
        gr: dict[int, list[tuple[int, float]]] = {}
        for e in range(len(E)):
            # grannarna: de andra extra noderna och kartans noder i närheten
            nara = np.nonzero((np.hypot(*(alla_ - E[e]).T) < RING_GRANNAR) | (np.arange(len(alla_)) >= n0))[0]
            nara = nara[nara != n0 + e]
            linjer = shapely.linestrings(np.stack([np.broadcast_to(E[e], (len(nara), 2)), alla_[nara]], axis=1))
            idx = nara[shapely.contains(k.fritt, linjer)]
            kost_ = _kostnad(np.broadcast_to(E[e], (len(idx), 2)), alla_[idx], k.zoner, k.faktor)
            for m, c in zip(idx, kost_):
                gr.setdefault(n0 + e, []).append((int(m), float(c)))
                if m < n0:
                    gr.setdefault(int(m), []).append((n0 + e, float(c)))
        pos.append(alla_)
        egna.append(gr)

    def punkt_(lager: int, n: int) -> Punkt:
        return (float(pos[lager][n][0]), float(pos[lager][n][1]))

    def grannar_(lager: int, n: int) -> list[tuple[int, float]]:
        bas = list(kartor[lager].grannar[n]) if n < len(kartor[lager].noder) else []
        return bas + egna[lager].get(n, [])

    def synliga_(lager: int, p: Punkt) -> list[tuple[int, float]]:
        k = kartor[lager]
        ut_ = _synliga(k, p)
        E = pos[lager][len(k.noder):]
        if len(E):
            linjer = shapely.linestrings(np.stack([np.broadcast_to(np.asarray(p), E.shape), E], axis=1))
            ok = shapely.contains(k.fritt, linjer)
            idx = np.nonzero(ok)[0]
            kost_ = _kostnad(np.broadcast_to(np.asarray(p, dtype=float), (len(idx), 2)), E[idx], k.zoner, k.faktor)
            ut_ += [(len(k.noder) + int(i), float(c)) for i, c in zip(idx, kost_)]
        return ut_
    # A* över (nivå, nod), med avståndet till målet som underskattning; -1 är starten och -2 målet i en nivå
    bast: tuple[float, tuple[int, int] | None] = (math.inf, None)
    g: dict[tuple[int, int], float] = {}
    klar: set[tuple[int, int]] = set()
    fore: dict[tuple[int, int], tuple[int, int]] = {}
    ko: list[tuple[float, float, int, int, int, int]] = []
    malen = [B for _, B in slut.values()]

    def h(q: Punkt) -> float:
        return min(math.dist(q, B) for B in malen)
    for la, (_, A) in starter.items():
        for lb, (_, B) in slut.items():
            if la == lb and kartor[la].fritt.contains(LineString([A, B]) if math.dist(A, B) > 0.1 else Point(A)) \
                    and fri(la, A, B):
                c = kost(la, float(_kostnad(np.array([A]), np.array([B]), kartor[la].zoner, kartor[la].faktor)[0]),
                         math.dist(A, B), A, B)
                if c < bast[0]:
                    bast = (c, (la, -2))
                    fore[(la, -2)] = (la, -1)
        for n, c in synliga_(la, A):
            q = punkt_(la, n)
            if fri(la, A, q):
                c = kost(la, c, math.dist(A, q), A, q)
                if c < g.get((la, n), math.inf):
                    g[(la, n)] = c
                    fore[(la, n)] = (la, -1)
                    heapq.heappush(ko, (c + h(q), c, la, n, la, -1))
    mal = {lb: dict(synliga_(lb, B)) for lb, (_, B) in slut.items()}
    while ko:
        f, d, la, n, fl, fn = heapq.heappop(ko)
        if (la, n) in klar or d > g.get((la, n), math.inf) + 1e-9:
            continue
        klar.add((la, n))
        if f >= bast[0]:
            break
        q = punkt_(la, n)
        if la in mal and n in mal[la] and fri(la, q, slut[la][1]):
            c = d + kost(la, mal[la][n], math.dist(q, slut[la][1]), q, slut[la][1])
            if c < bast[0]:
                bast = (c, (la, -2))
                fore[(la, -2)] = (la, n)
        for m, c in grannar_(la, n):
            if (la, m) in klar:
                continue
            r_ = punkt_(la, m)
            ny = d + kost(la, c, math.dist(q, r_))
            if ny < g.get((la, m), math.inf) and fri(la, q, r_):
                ny += straff(la, q, r_)
            else:
                continue
            if ny < g.get((la, m), math.inf):
                g[(la, m)] = ny
                fore[(la, m)] = (la, n)
                heapq.heappush(ko, (ny + h(r_), ny, la, m, la, n))
        if (la, n) in byten and all(t is None or not any(
                upptagna[lx][int(i)].intersects(skiva) for i in t.query(skiva))
                for lx, t in ((la, trad[la]), (byten[(la, n)][0], trad[byten[(la, n)][0]]))
                for skiva in [Point(q).buffer(RAMP / 2, quad_segs=2)]):
            lb, m = byten[(la, n)]
            ny = d + BYTE + rampens_straff(la, lb, q)
            if (lb, m) not in klar and ny < g.get((lb, m), math.inf):
                g[(lb, m)] = ny
                fore[(lb, m)] = (la, n)
                heapq.heappush(ko, (ny + h(q), ny, lb, m, la, n))
    if bast[1] is None:
        raise ValueError(f"ingen väg från ({a[0]:.0f}, {a[1]:.0f}) till ({b[0]:.0f}, {b[1]:.0f})")
    # vägen: (nivå, punkt) från starten till målet
    steg: list[tuple[int, Punkt]] = []
    s = bast[1]
    while s[1] != -1:
        if s[1] != -2:
            steg.append((s[0], punkt_(s[0], s[1])))
        s = fore[s]
    la = s[0]
    lb = bast[1][0]
    steg.reverse()
    hela: list[tuple[int, Punkt]] = [(la, a), *((la, q) for q in starter[la][0]), *steg,
                                     *((lb, q) for q in slut[lb][0][::-1]), (lb, b)]
    return _dragningen(kartor, hela, radie_a if starter[la][0] else None, len(starter[la][0]), len(slut[lb][0]),
                       glipor_, straff, fri)


def _dragningen(kartor: Sequence[Karta], hela: list[tuple[int, Punkt]], radie_a: float | None = None,
                led_a: int = 0, led_b: int = 0, glipor_: bool = True,
                straff: Callable[[int, Punkt, Punkt], float] | None = None,
                fri: Callable[[int, Punkt, Punkt], bool] | None = None) -> Dragning:
    """Brytpunkterna och radierna ur vägens steg (nivå, punkt): sträckorna i varje nivå glättade och genom järnens
    rader, ramperna där nivån byts och hörnen rundade (hörnet efter ledningen ut ur a med radien radie_a, om den är
    given och bågen ryms)."""
    # sträckorna i varje nivå (bytena: samma punkt i två nivåer)
    strackor: list[tuple[int, list[Punkt]]] = []
    for lager, q in hela:
        if strackor and strackor[-1][0] == lager:
            if math.dist(q, strackor[-1][1][-1]) > 0.5:
                strackor[-1][1].append(q)
        else:
            strackor.append((lager, [q]))
    for i, (lager, pts) in enumerate(strackor):
        k = kartor[lager]
        if len(pts) > 2:              # ledningarna (led_a och led_b punkter i ändarna) står kvar
            pts = _glatta(k, pts, 1 + (led_a if i == 0 else 0),
                          len(pts) - 2 - (led_b if i == len(strackor) - 1 else 0),
                          _i_lagret(straff, lager) if straff else None, _i_lagret(fri, lager) if fri else None)
        strackor[i] = (lager, glipor(k, pts) if len(pts) > 1 and glipor_ else pts)
    punkter: list[tuple[float, float, float]] = []
    radier: list[float] = []
    for i, (lager, pts) in enumerate(strackor):
        k = kartor[lager]
        r = rundad(k, pts, fri=_i_lagret(fri, lager) if fri else None) if len(pts) > 2 else [0.0] * len(pts)
        if i == 0 and radie_a is not None and len(pts) > 2:
            bage = LineString(bage_punkter(pts[0], pts[1], pts[2], radie_a))
            if k.fritt.contains(bage) and jarnfri(k, bage):
                r[1] = radie_a
        for j, q in enumerate(pts):
            # rampen: sista punkten i en sträcka och första i nästa är samma punkt; röret lutar RAMP/2 före och efter
            if j == len(pts) - 1 and i + 1 < len(strackor):
                nasta = strackor[i + 1]
                fore_ = pts[j - 1] if j > 0 else q
                efter = nasta[1][1] if len(nasta[1]) > 1 else q
                l1 = min(RAMP / 2, math.dist(fore_, q) / 2)
                l2 = min(RAMP / 2, math.dist(q, efter) / 2)
                u = _riktning(fore_, q)
                w = _riktning(q, efter)
                punkter.append((q[0] - u[0] * l1, q[1] - u[1] * l1, k.z))
                radier.append(0.0)
                punkter.append((q[0] + w[0] * l2, q[1] + w[1] * l2, kartor[nasta[0]].z))
                radier.append(0.0)
                continue
            if j == 0 and i > 0:
                continue                                  # bytespunkten, redan som rampens slut
            punkter.append((q[0], q[1], k.z))
            radier.append(r[j])
    return Dragning(tuple(punkter), tuple(radier))


T = TypeVar("T")


def _i_lagret(f: Callable[[int, Punkt, Punkt], T], lager: int) -> Callable[[Punkt, Punkt], T]:
    """f(lager, p, q) som en funktion av p och q i lagret."""
    def g(p: Punkt, q: Punkt) -> T:
        return f(lager, p, q)
    return g


def _riktning(p: Punkt, q: Punkt) -> Punkt:
    n = math.dist(p, q)
    return ((q[0] - p[0]) / n, (q[1] - p[1]) / n) if n > 1e-9 else (0.0, 0.0)
