"""Innerväggarna: de lätta väggarna och skikten på de bärande och de lätta innerväggarna.

De lätta väggarna (LATTA) enligt planritning 201 rev 02 med modellens bärande väggar, stolpar och syllar: stomme
45×70 C24 med syll, reglar c/c 600 och vid ändar och dörrar, överstycke och kortreglar över dörrarna och hammarband
under innertaket (snett där taket lutar längs väggen). Där en stolpes syll ligger under väggen har väggen ingen egen.
Skikten (invandigt.SKIVOR, mot badrummet SKIVOR_VATRUM) på båda sidor av varje innervägg, från bjälklaget upp till
innertaket, med hål för dörrarna (oppningar.INNERDORRAR) och runt delar som sticker ut ur väggen (stolpar, klossar).

Möten: stommarna möts, och en lätt väggs stomme går fram till ytterväggens installationsskikt. Skikten möts: de
genomgående väggarnas skikt läggs först (ORDNING) och skikten på väggarna som möter dem slutar mot dem. Ytterväggarnas
insida går runt de bärande väggarna med deras skikt; de lätta väggarnas stommar går genom ytterväggarnas skivor.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import cache
from typing import Any

from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from modellering import Montage

from trebodar import skelett as S
from trebodar.byggdelar import lagen
from trebodar.byggdelar import polygon as P
from trebodar.byggdelar.regelvagg import Plan
from trebodar.hus.fonster_och_dorrar.oppningar import INNERDORRAR, INNEROPPNINGAR
from trebodar.hus.rum import BADRUM, KAMINKAPA
from trebodar.hus.tak.tak import REGIONER

from trebodar.material import C24_LAKT, KALCIUMSILIKAT

from .invandigt import FOLIE, GIPS_YTTRE_W, LAKT, SKIVOR, SKIVOR_T, SKIVOR_VATRUM, SKIVOR_VATRUM_T

SKIVOR_KAMIN = (("Kalciumsilikat", 50.0, "KS", KALCIUMSILIKAT),)      # mot kaminens kåpa (Rais: 50 mm)
FICKA_LAKT, FICKA_CC = 10.0, 300.0           # fickdörrens ficka: läkt 10×45 mot var sida, c/c
FICKA_SKENA = 50.0                           # fickdörrens skena under överstycket (bladets överkant 10 över öppningen)

T = 70.0                        # de lätta väggarnas stomme
CC = 600.0
H_VIRKE = 45.0                  # syll, hammarband och överstycke
_PX, _PY = (1.0, 0.0), (0.0, 1.0)
X_3NV = S.TAKFALL["3NV"].x_insida - FOLIE - LAKT                        # 3NV:s installationsskikt
Y_1NO = S.YTTERVAGGAR["1NO"].origo[1] + S.T_STOMME + FOLIE + LAKT       # 1NO:s installationsskikt


@dataclass(frozen=True)
class Lattvagg:
    kod: str
    origo: tuple[float, float]           # som skelett.Vaggdef: stommens början på sidan w = 0
    u: tuple[float, float]
    langd: float
    beskrivning: str
    syll: bool = True

    @property
    def vagg(self) -> S.Vaggdef:
        return S.Vaggdef(self.kod, self.origo, self.u, self.langd, T, self.beskrivning)


LATTA = (
    Lattvagg("L1", (9440.0, 2760.0), _PX, X_3NV - 9440.0, "mellan sovrummet och kontoret i höger huskropp"),
    Lattvagg("L2", (11050.0, 2830.0), _PY, 6612.0 - 2830.0, "korridoren i höger huskropp"),
    Lattvagg("L3", (11050.0, 4651.0), _PX, X_3NV - 11050.0, "mellan kontoren (på stolpen LN1_2:s syll)", syll=False),
    Lattvagg("L4", (11050.0, 6542.0), _PX, X_3NV - 11050.0, "mellan kontoret och köket (på huvudstolpens syll)",
             syll=False),
    Lattvagg("L9", (2595.0, Y_1NO), _PY, 5265.0 - Y_1NO, "badrummet mot sovrummet i mittre huskroppen"),
    Lattvagg("L10", (2595.0, 5195.0), _PX, 3275.0 - 2595.0, "badrummets hörn"),
    Lattvagg("L11", (3345.0, 5195.0), _PY, 8185.0 - 5195.0, "badrummet mot allrummet"),
    Lattvagg("L12", (3345.0, 5925.0), _PX, 4405.0 - 3345.0, "över skjutdörren mellan allrummet och sovrummet",
             syll=False),
    Lattvagg("L6", (7348.0, 4989.5), _PX, 9370.0 - 7348.0, "trapphålets norra sida, mot sovrummet"),
    Lattvagg("L7", (7348.0, 4989.5), _PY, 5900.0 - 4989.5, "trapphålets västra sida, mot kaminens kåpa"),
    Lattvagg("L13", (6288.0, 5452.0), _PX, 7278.0 - 6288.0, "kaminens kåpa, norra sidan"),
    Lattvagg("L14", (6358.0, 5522.0), _PY, 5900.0 - 5522.0, "kaminens kåpa, västra sidan"),
)
VAGGAR = {lv.kod: lv.vagg for lv in LATTA}
# skiktens ordning: genomgående väggar först, så att skikten på väggarna som möter dem slutar mot dem
ORDNING = ("1B", "2B", "1A", "1C", "1D", "2A", "2C", "L1", "L2", "L3", "L4", "L9", "L11", "L10", "L12", "L7", "L6",
           "L13", "L14")

Hinder = tuple[Polygon, float, float]


def innertak(x: float, y: float) -> float:
    """Innertakets underkant (den yttre gipsskivan) i punkten: takfallet vars område innehåller punkten (i nocken
    det lägsta)."""
    z = [S.TAKFALL[k].z_overkant(x) for k, rs in REGIONER.items() for r in rs
         if r.y0 - 1e-6 <= y <= r.y1 + 1e-6 and min(r.nedre.x, r.nock.x) - 1e-6 <= x <= max(r.nedre.x, r.nock.x) + 1e-6]
    return min(z) + GIPS_YTTRE_W[0] / S.COS if z else S.H_VAGG


def vaggdef(kod: str) -> S.Vaggdef:
    return VAGGAR[kod] if kod in VAGGAR else S.INNERVAGGAR[kod]


def _band(v: S.Vaggdef, u0: float, u1: float, w0: float, w1: float) -> Polygon:
    pl = v.placering()
    return Polygon([pl.punkt((u, w, 0.0))[:2] for u, w in ((u0, w0), (u1, w0), (u1, w1), (u0, w1))])


def _topp(v: S.Vaggdef, u0: float, u1: float, w0: float, w1: float) -> list[tuple[float, float]]:
    """Innertakets underkant över bandet w0–w1 längs väggen, (u, z) med brytpunkter i nock- och dallinjerna: det lägsta
    över bandets bredd."""
    pl = v.placering()
    us = {u0, u1}
    if abs(v.u[0]) > 0.5:
        us |= {u for b in S.BALKAR.values() if u0 < (u := (b.x - v.origo[0]) * v.u[0]) < u1}
    return [(u, min(innertak(*pl.punkt((u, w, 0.0))[:2]) for w in (w0, w1))) for u in sorted(us)]


def _yta(topp: list[tuple[float, float]]) -> Polygon:
    return Polygon([(topp[0][0], 0.0), (topp[-1][0], 0.0)] + topp[::-1])


def _i_vaggen(v: S.Vaggdef, band: Polygon, hinder: list[Hinder]) -> list[Polygon]:
    """Hindren som når in i bandet, som lådor i väggens (u, z)."""
    Pi = v.placering().invers()
    ut = []
    for poly, z0, z1 in hinder:
        g = poly.intersection(band)
        if g.area > 1.0:
            x0, y0, x1, y1 = g.bounds
            us = [Pi.punkt((x, y, 0.0))[0] for x in (x0, x1) for y in (y0, y1)]
            ut.append(box(min(us), z0, max(us), z1))
    return ut


@cache
def _delar() -> tuple[Hinder, ...]:
    """Stommens delar: ytterväggar, bärande innerväggar, stolpar och takstolar."""
    return tuple((box(x0, y0, x1, y1), z0, z1) for _, _, (x0, y0, z0, x1, y1, z1) in lagen.prefab() + lagen.takstolar())


def stommar() -> list[Hinder]:
    """De lätta väggarnas stommar i plan (för skikten och ytterväggarnas skivor)."""
    return [(_band(lv.vagg, 0.0, lv.langd, 0.0, T), 0.0, 10000.0) for lv in LATTA]


def _skivor(v: S.Vaggdef, sida: int) -> list[tuple[float, float, tuple[Any, ...]]]:
    """Skivorna längs väggens sida: (u0, u1, skivor), våtrumsskikt där badrummet ligger mot sidan och kalciumsilikat
    mot kaminens kåpa."""
    w = 0.0 if sida < 0 else v.tjocklek
    prov = _band(v, 0.0, v.langd, w + sida * 30.0, w + sida * 40.0)
    Pi = v.placering().invers()
    sarskilda = []
    for rum, skivor in ((BADRUM, SKIVOR_VATRUM), (KAMINKAPA, SKIVOR_KAMIN)):
        for g in P.polygoner(rum.intersection(prov)):
            x0, y0, x1, y1 = g.bounds
            us = [Pi.punkt((x, y, 0.0))[0] for x in (x0, x1) for y in (y0, y1)]
            sarskilda.append((max(0.0, min(us)), min(v.langd, max(us)), skivor))
    ut: list[tuple[float, float, tuple[Any, ...]]] = []
    u = 0.0
    for a, b, skivor in sorted(sarskilda, key=lambda t: t[0]):
        if a > u + 1.0:
            ut.append((u, a, SKIVOR))
        ut.append((a, b, skivor))
        u = b
    if u < v.langd - 1.0:
        ut.append((u, v.langd, SKIVOR))
    return ut


def skiktets_tjocklek(kod: str, sida: int, u: float) -> float:
    """Skivornas tjocklek på väggens sida vid u (25, mot badrummet 38)."""
    for a, b, skivor in _skivor(vaggdef(kod), sida):
        if a - 1e-6 <= u <= b + 1e-6:
            return sum(t for _, t, _, _ in skivor)
    return SKIVOR_T


def _ytterskivor() -> list[Hinder]:
    """Ytterväggarnas skivor (utanför installationsskiktet), som de lätta väggarnas skikt slutar mot."""
    ut = []
    for kod, v in S.YTTERVAGGAR.items():
        w = S.T_STOMME + FOLIE + LAKT
        ut.append((_band(v, 0.0, v.langd, w, w + SKIVOR_VATRUM_T), 0.0, 10000.0))
    return ut


@dataclass
class _Skikt:
    montage: dict[str, Montage] = field(default_factory=dict)
    band: dict[str, list[Hinder]] = field(default_factory=dict)


@cache
def _skikt() -> _Skikt:
    """Skikten på alla innerväggar, i ORDNING; varje väggs skikt slutar mot de väggar som lagts före."""
    res = _Skikt()
    lagda: list[Hinder] = []
    lattstommar = stommar()
    for kod in ORDNING:
        v = vaggdef(kod)
        latt = kod in VAGGAR
        hinder = list(_delar()) + lagda + [h for h, lv in zip(lattstommar, LATTA) if lv.kod != kod]
        if latt:
            hinder += _ytterskivor()
        dorrar = [box(d.u0, 0.0, d.u1, d.hojd) for d in INNERDORRAR if d.vagg == kod]
        dorrar += [box(u0, z0, u1, z1) for vagg, u0, u1, z0, z1, _ in INNEROPPNINGAR if vagg == kod]
        plan: dict[str, Plan] = {}
        res.band[kod] = []
        for sida in (-1, 1):
            w_yta = 0.0 if sida < 0 else v.tjocklek
            for a, b, skivor in _skivor(v, sida):
                tjock = sum(t for _, t, _, _ in skivor)
                w_ut = w_yta + sida * tjock
                band = _band(v, a, b, *sorted((w_yta, w_ut)))
                omrade = _yta(_topp(v, a, b, *sorted((w_yta, w_ut)))).difference(
                    unary_union(dorrar + _i_vaggen(v, band, hinder)))
                ws = w_yta
                for namn, t, typ, mat in skivor:
                    p = plan.setdefault(namn, Plan(kod, f"{namn} {kod}", t, material=mat))
                    w0, w1 = sorted((ws, ws + sida * t))
                    for q in P.polygoner(omrade, 100.0):
                        p.skiva(P.kontur(q), P.hal(q), w0, w1, typ, mat, f"{namn} {kod}")
                    ws += sida * t
                res.band[kod].append((band, 0.0, 10000.0))
        lagda += res.band[kod]
        m = Montage(f"Skikt {kod}", beskrivning="OSB och gips, mot badrummet plywood, gips, tätskikt och kakel")
        for p in plan.values():
            if p.bitar:
                m.lagg(p.montage())
        res.montage[kod] = m
    return res


def barande_skikt() -> list[Hinder]:
    """De bärande innerväggarnas skikt i plan (ytterväggarnas insida går runt dem)."""
    return [h for kod in S.INNERVAGGAR for h in _skikt().band[kod]]


def _stomme(lv: Lattvagg) -> Montage:
    v = lv.vagg
    p = Plan(lv.kod, f"Vägg {lv.kod}", T, beskrivning=f"Lätt vägg 45×70 C24, {lv.beskrivning}")
    L = lv.langd
    hindret = unary_union(_i_vaggen(v, _band(v, 0.0, L, 0.0, T), list(_delar())) or [Polygon()])
    topp = _topp(v, 0.0, L, 0.0, T)

    def ztopp(u: float) -> float:
        for (u0, z0), (u1, z1) in zip(topp, topp[1:]):
            if u0 - 1e-6 <= u <= u1 + 1e-6:
                return z0 + (z1 - z0) * (u - u0) / max(u1 - u0, 1e-9)
        return topp[-1][1]

    def lagg(typ: str, poly: Polygon) -> None:
        for q in P.polygoner(poly.difference(hindret), 100.0):
            p.profil(P.kontur(q), 0.0, T, typ=typ)

    dorrar = [d for d in INNERDORRAR if d.vagg == lv.kod]
    # dörrarnas utsträckning i stommen (öppningen och fickdörrarnas ficka) och överstyckets underkant
    spann = [(min(d.u0, *d.fickan), max(d.u1, *d.fickan)) if d.ficka else (d.u0, d.u1) for d in dorrar]
    over = [d.hojd + (FICKA_SKENA if d.ficka else 0.0) for d in dorrar]
    if lv.syll:
        for q in P.polygoner(box(0.0, 0.0, L, H_VIRKE).difference(
                unary_union([box(a, -1.0, b, H_VIRKE + 1.0) for a, b in spann] or [Polygon()]))):
            lagg("S", q)
    lagg("H", Polygon([(u, z - H_VIRKE) for u, z in topp] + [(u, z) for u, z in topp[::-1]]))
    # reglar: vid ändarna, c/c 600 och vid dörrarnas sidor (i dörröppningarna och fickorna bara kortreglar över
    # överstycket)
    lagen_u = sorted({0.0, L - H_VIRKE} | {a - H_VIRKE for a, _ in spann} | {b for _, b in spann})
    for k in range(1, int(L // CC) + 1):
        if all(abs(k * CC - u) >= H_VIRKE for u in lagen_u):
            lagen_u.append(k * CC)
    for u in sorted(lagen_u):
        if not 0.0 <= u <= L - H_VIRKE + 1e-6:
            continue
        z0 = next((zo + H_VIRKE for (a, b), zo in zip(spann, over) if u + H_VIRKE > a + 1e-6 and u < b - 1e-6),
                  H_VIRKE)
        lagg("R", Polygon([(u, z0), (u + H_VIRKE, z0), (u + H_VIRKE, ztopp(u + H_VIRKE) - H_VIRKE),
                           (u, ztopp(u) - H_VIRKE)]))
    for (a, b), zo in zip(spann, over):
        lagg("L", box(a, zo, b, zo + H_VIRKE))
    # fickdörrarnas fickor: läkt 10×45 c/c 300 mot båda sidorna, från golvet till överstycket
    for d, zo in zip(dorrar, over):
        if not d.ficka:
            continue
        a, b = d.fickan
        mun = d.u1 if d.mot > 0 else d.u0 - H_VIRKE          # läkten vid fickans öppning, sedan c/c mot fickans slut
        us = [mun + d.mot * k * FICKA_CC for k in range(int((b - a) // FICKA_CC) + 1)]
        for u in (u for u in us if a - 1e-6 <= u <= b - H_VIRKE + 1e-6):
            for w0, w1 in ((0.0, FICKA_LAKT), (T - FICKA_LAKT, T)):
                p.lada("F", u, u + H_VIRKE, w0, w1, 0.0, zo, "z", material=C24_LAKT)
    return p.montage()


def montage() -> Montage:
    m = Montage("Innerväggar", beskrivning="Lätta väggar 45×70 och skikten på innerväggarna")
    latta = Montage("Lätta väggar", beskrivning="Stomme 45×70 C24 (planritning 201 rev 02)")
    for lv in LATTA:
        latta.lagg(_stomme(lv), lv.vagg.placering())
    m.lagg(latta)
    skikt = Montage("Innerväggarnas skikt", beskrivning="OSB 12 och gips 13, mot badrummet plywood 15, gips 12, "
                                                        "tätskikt och kakel")
    for kod in ORDNING:
        skikt.lagg(_skikt().montage[kod], vaggdef(kod).placering())
    m.lagg(skikt)
    return m
