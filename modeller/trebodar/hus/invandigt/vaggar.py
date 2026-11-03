"""Innerväggarna: de lätta väggarna och skikten på de bärande och de lätta innerväggarna.

De lätta väggarna (LATTA) enligt planritning 201 rev 02 med modellens bärande väggar, stolpar och syllar: stomme
45×70 C24 med syll, reglar c/c 600 och vid ändar och dörrar, överstycke och kortreglar över dörrarna och hammarband
under innertaket (snett där taket lutar längs väggen). Där en stolpes syll ligger under väggen har väggen ingen egen.
Skikten (invandigt.SKIVOR, mot badrummet SKIVOR_VATRUM) på båda sidor av varje innervägg, från bjälklaget upp till
innertaket, med hål för dörrarna (oppningar.INNERDORRAR) och där delar går genom ett skikt (stolpar, klossar), var
skikt för sig: når en del bara en bit in i skiktet går skiktet över den med ett urtag (gipsen över stolparna 45×95 i
de lätta väggarna, som sticker ut 12,5 mm, en halv millimeter mer än OSB:n).
Fickdörrarnas fickor: hela stommens tjocklek är fickan (inga reglar), och OSB:n byts mot brädor 12 mm på båda sidor
(gips 13 + bräda 12 + ficka 70 + bräda 12 + gips 13), upp till överstyckets överkant.

Möten: stommarna möts, och en lätt väggs stomme går fram till ytterväggens installationsskikt. Skikten möts: de
genomgående väggarnas skikt läggs först (ORDNING) och skikten på väggarna som möter dem slutar mot dem. Där en vägg
slutar mot en annan (ytterhörnet, Horn) möts skikten var för sig: väggens skikt går förbi änden fram till den andra
väggens skikt på samma djup och den andra väggens skikt förbi sin ände över skikten innanför, så att gipsen (och i
badrummet tätskiktet och kaklet) går runt hörnet och OSB:n inte syns; på den inre sidan slutar de mot den andra
väggens skikt. Ytterväggarnas insida går runt de bärande väggarna
med deras skikt; de lätta väggarnas stommar går genom ytterväggarnas skivor. Skikten går upp till innertaket: där
taket lutar tvärs över väggen (väggar längs y, under takfall som lutar i x) är skivornas överkant sned som taket.

Lägena och fickorna står i lattvaggar.py. Väggarna i en grupp byggs av sin egen modul: garderoben i
hus/inredning/garderob.py och kökets inbyggnad i kokets_inbyggnad.py.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import cache
from typing import Any

from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from modellering import Del, Kapad, Montage, Placering

from trebodar import skelett as S
from trebodar.hus.stomme import lagen
from trebodar.byggdelar import polygon as P
from trebodar.byggdelar import virke
from trebodar.byggdelar.regelvagg import Plan
from trebodar.hus.fonster_och_dorrar.oppningar import INNERDORRAR, INNEROPPNINGAR
from trebodar.hus.rum import BADRUM, KAMINKAPA

from trebodar.material import BRADA, KALCIUMSILIKAT

from .lattvaggar import FICKA_SKENA, H_VIRKE, LATTA, T, VAGGAR, Lattvagg, fickor, vaggdef  # noqa: F401
from .skikt import (FOLIE, GIPS_YTTRE_W, LAKT, SKIVOR, SKIVOR_T, SKIVOR_VATRUM, SKIVOR_VATRUM_T, innertak_vid,
                    innertakets_fall)

SKIVOR_KAMIN = (("Kalciumsilikat", 50.0, "KS", KALCIUMSILIKAT),)      # mot kaminens kåpa (Rais: 50 mm)
CC = 600.0
# skiktens ordning: genomgående väggar först, så att skikten på väggarna som möter dem slutar mot dem
ORDNING = ("1B", "2B", "1A", "1C", "1D", "2A", "2C", "L1", "L2", "L3", "L4", "L9", "L11", "L10", "L12", "L7", "L6",
           "L13", "L14")

Hinder = tuple[Polygon, float, float]


def _band(v: S.Vaggdef, u0: float, u1: float, w0: float, w1: float) -> Polygon:
    pl = v.placering()
    return Polygon([pl.punkt((u, w, 0.0))[:2] for u, w in ((u0, w0), (u1, w0), (u1, w1), (u0, w1))])


def _topp(v: S.Vaggdef, u0: float, u1: float, w0: float, w1: float, hogst: bool = False) -> list[tuple[float, float]]:
    """Innertakets underkant över bandet w0–w1 längs väggen, (u, z) med brytpunkter i nock- och dallinjerna: det lägsta
    över bandets bredd (hogst: det högsta)."""
    pl = v.placering()
    us = {u0, u1}
    if abs(v.u[0]) > 0.5:
        us |= {u for b in S.BALKAR.values() if u0 < (u := (b.x - v.origo[0]) * v.u[0]) < u1}
    valj = max if hogst else min
    return [(u, valj(innertak_vid(*pl.punkt((u, w, 0.0))[:2]) for w in (w0, w1))) for u in sorted(us)]


def _snett_tak(v: S.Vaggdef, u: float, w0: float, w1: float) -> tuple[tuple[float, float, float],
                                                                      tuple[float, float, float]] | None:
    """Innertakets plan (punkt, normal uppåt) i väggens system där taket lutar tvärs över bandet w0–w1 (väggar längs
    y under takfall som lutar i x), annars None."""
    if abs(v.u[0]) > 0.5:
        return None
    pl = v.placering()
    (xa, ya, _), (xb, yb, _) = pl.punkt((u, w0, 0.0)), pl.punkt((u, w1, 0.0))
    ta, tb = innertakets_fall(xa, ya), innertakets_fall(xb, yb)
    if ta is None or ta is not tb:
        return None
    za, zb = (ta.z_overkant(x) + GIPS_YTTRE_W[0] / S.COS for x in (xa, xb))
    if abs(za - zb) < 0.5:
        return None
    k = (zb - za) / (w1 - w0)                           # takets lutning längs w
    return (u, w0, za), (0.0, -k, 1.0)


@dataclass(frozen=True)
class Horn:
    """Ett ytterhörn där väggen slutar mot en annan: hur långt skikten går förbi änden till den andra väggens yttre
    yta, den andra väggen, dess ände i hörnet (0, 1) och dess sida bort från väggen."""
    forbi: float
    annan: str
    ande: int | None
    sida: int


def _horn(v: S.Vaggdef, kod: str) -> dict[tuple[int, int], Horn]:
    """Ytterhörnen vid väggens början (0) och slut (1), {(ände, sida): Horn}: där väggen slutar mot en annan
    innervägg i rät vinkel och den andra väggen inte fortsätter på sidan (hörnets utsida) går skikten runt hörnet
    (_forbi). På hörnets insida och i T-möten slutar skikten mot den andra väggens skikt (ORDNING)."""
    pl = v.placering()
    ut: dict[tuple[int, int], Horn] = {}
    for ande, (u_slut, steg) in enumerate(((0.0, -1.0), (v.langd, 1.0))):
        p = pl.punkt((u_slut + steg, v.tjocklek / 2, 0.0))
        for k in [*S.INNERVAGGAR, *(lv.kod for lv in LATTA if not lv.grupp)]:
            b = vaggdef(k)
            if k == kod or abs(b.u[0] * v.u[0] + b.u[1] * v.u[1]) > 0.1:
                continue
            Pb = b.placering().invers()
            ub, wb, _ = Pb.punkt(p)
            if not (0.0 <= ub <= b.langd and 0.0 <= wb <= b.tjocklek):
                continue
            _, w_slut, _ = Pb.punkt(pl.punkt((u_slut, v.tjocklek / 2, 0.0)))
            bort = 1 if w_slut < b.tjocklek / 2 else -1            # den andra väggens sida bort från väggen
            yta = b.tjocklek + skiktets_tjocklek(k, 1, ub) if bort > 0 else -skiktets_tjocklek(k, -1, ub)
            e = abs(yta - w_slut)
            stomme_b = _band(b, 0.0, b.langd, 0.0, b.tjocklek)
            for sida in (-1, 1):
                w0, w1 = (-SKIVOR_VATRUM_T, 0.0) if sida < 0 else (v.tjocklek, v.tjocklek + SKIVOR_VATRUM_T)
                ua, ub_ = sorted((u_slut, u_slut + steg * e))
                forbi = _band(v, ua, ub_, w0, w1)
                if forbi.intersection(stomme_b).area < 1.0:          # den andra väggen fortsätter inte här
                    # den andra väggens ände i hörnet: där väggens stomme slutar på sidan
                    u_horn = Pb.punkt(pl.punkt((u_slut, 0.0 if sida < 0 else v.tjocklek, 0.0)))[0]
                    b_ande = 0 if abs(u_horn) < 1.0 else 1 if abs(u_horn - b.langd) < 1.0 else None
                    ut[(ande, sida)] = Horn(e, k, b_ande, bort)
            break
    return ut


def _forbi(kod: str, ande: int, sida: int, inre: float, utanfor: float) -> float:
    """Hur långt ett skikt på väggens sida går förbi änden (inre och utanfor: skiktens tjocklek innanför och
    utanför det). I ett ytterhörn möts skikten var för sig: där väggen slutar mot en annan går skiktet fram till den
    andra väggens skikt på samma djup, och den andra väggens skikt går förbi sin ände över skikten innanför, så att
    gipsen och tätskiktet går runt hörnet och OSB:n inte syns."""
    h = _hornen()
    if (ande, sida) in h[kod]:
        return h[kod][(ande, sida)].forbi - utanfor
    mot = {(x.annan, x.ande, x.sida) for hv in h.values() for x in hv.values()}
    return inre if (kod, ande, sida) in mot else 0.0


@cache
def _hornen() -> dict[str, dict[tuple[int, int], Horn]]:
    return {kod: _horn(vaggdef(kod), kod) for kod in ORDNING}


def _yta(topp: list[tuple[float, float]]) -> Polygon:
    return Polygon([(topp[0][0], 0.0), (topp[-1][0], 0.0)] + topp[::-1])


def _i_skiktet(v: S.Vaggdef, band: Polygon, w0: float, w1: float, hinder: list[Hinder]
               ) -> tuple[list[Polygon], list[tuple[float, float, float, float, float, float]]]:
    """Hindren som når in i skiktet w0–w1 (bandet): hål i väggens (u, z) där de går genom hela skiktet, annars urtag
    (u0, u1, w0, w1, z0, z1) i skiktet, som då går över dem (t.ex. gipsen över en stolpe som sticker ut lite mer än
    OSB:ns tjocklek)."""
    Pi = v.placering().invers()
    hal, urtag = [], []
    for poly, z0, z1 in hinder:
        g = poly.intersection(band)
        if g.area > 1.0:
            pkt = [Pi.punkt((x, y, 0.0)) for x, y in g.exterior.coords]
            us, ws = [p[0] for p in pkt], [p[1] for p in pkt]
            if min(ws) <= w0 + 0.01 and max(ws) >= w1 - 0.01:
                hal.append(box(min(us), z0, max(us), z1))
            else:
                urtag.append((min(us), max(us), max(min(ws), w0), min(max(ws), w1), z0, z1))
    return hal, urtag


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
    return tuple((box(d.lada[0], d.lada[1], d.lada[3], d.lada[4]), d.lada[2], d.lada[5])
                 for d in lagen.prefab() + lagen.takstolar())


def stommar() -> list[Hinder]:
    """De lätta väggarnas stommar i plan (för skikten och ytterväggarnas skivor), utan inredningens."""
    return [(_band(lv.vagg, 0.0, lv.langd, 0.0, T), 0.0, 10000.0) for lv in LATTA if not lv.grupp]


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
        # fickdörrarnas fickor (också de som går in från en annan vägg): brädor i stället för OSB, upp till
        # överstyckets överkant
        fickzon = unary_union([box(a, 0.0, b, z1) for a, b, z1, _ in fickor(kod)] or [Polygon()])
        plan: dict[str, Plan] = {}
        res.band[kod] = []
        for sida in (-1, 1):
            w_yta = 0.0 if sida < 0 else v.tjocklek
            segment = _skivor(v, sida)
            for i, (a, b, skivor) in enumerate(segment):
                tjock = sum(t for _, t, _, _ in skivor)
                wa, wb = sorted((w_yta, w_yta + sida * tjock))
                tak = _snett_tak(v, (a + b) / 2, wa, wb)
                ws, inre = w_yta, 0.0
                for namn, t, typ, mat in skivor:
                    w0, w1 = sorted((ws, ws + sida * t))
                    utanfor = tjock - inre - t
                    ua = a - (_forbi(kod, 0, sida, inre, utanfor) if i == 0 else 0.0)
                    ub = b + (_forbi(kod, 1, sida, inre, utanfor) if i == len(segment) - 1 else 0.0)
                    band = _band(v, ua, ub, w0, w1)
                    hal, urtag = _i_skiktet(v, band, w0, w1, hinder)
                    omrade = _yta(_topp(v, ua, ub, wa, wb, hogst=tak is not None)).difference(
                        unary_union(dorrar + hal))
                    delar = [(namn, typ, mat, omrade)]
                    if namn == "OSB" and not fickzon.is_empty:
                        delar = [(namn, typ, mat, omrade.difference(fickzon)),
                                 ("Bräda", "BR", BRADA, omrade.intersection(fickzon))]
                    for namn_, typ_, mat_, yta in delar:
                        p = plan.setdefault(namn_, Plan(kod, f"{namn_} {kod}", t, material=mat_))
                        for q in P.polygoner(yta, 100.0):
                            x0, z0, x1, z1 = q.bounds
                            ur = [r for r in urtag if r[0] < x1 and r[1] > x0 and r[4] < z1 and r[5] > z0]
                            p.skiva(P.kontur(q), P.hal(q), w0, w1, typ_, mat_, f"{namn_} {kod}", kapa=tak, urtag=ur)
                    res.band[kod].append((band, 0.0, 10000.0))
                    ws += sida * t
                    inre += t
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


def _spann(lv: Lattvagg) -> tuple[list[tuple[float, float]], list[float]]:
    """Dörrarnas utsträckning i stommen (öppningen och fickorna, också fickor som går in från en annan vägg) och
    överstyckets underkant; en öppning och dess ficka är ett spann."""
    bitar = sorted([(d.u0, d.u1, d.hojd + (FICKA_SKENA if d.ficka else 0.0)) for d in INNERDORRAR if d.vagg == lv.kod]
                   + [(a, b, z1 - H_VIRKE) for a, b, z1, _ in fickor(lv.kod)])
    sammanslagna: list[list[float]] = []
    for a, b, zo in bitar:
        a, b = max(a, 0.0), min(b, lv.langd)
        if b - a < 1.0:
            continue
        if sammanslagna and a <= sammanslagna[-1][1] + 1.0:
            sammanslagna[-1][1:] = [max(sammanslagna[-1][1], b), max(sammanslagna[-1][2], zo)]
        else:
            sammanslagna.append([a, b, zo])
    return [(a, b) for a, b, _ in sammanslagna], [zo for _, _, zo in sammanslagna]


def _reglarnas_u(lv: Lattvagg, spann: list[tuple[float, float]]) -> list[float]:
    """Reglarnas u: vid ändarna, vid dörrarnas sidor och c/c 600; ändarna först, och en regel vid en dörr eller ficka
    som skulle överlappa en annan utgår."""
    L = lv.langd
    lagen_u: list[float] = []
    for u in [0.0, L - H_VIRKE] + sorted({a - H_VIRKE for a, _ in spann} | {b for _, b in spann}):
        if all(abs(u - v) >= H_VIRKE for v in lagen_u):
            lagen_u.append(u)
    for k in range(1, int(L // CC) + 1):
        if all(abs(k * CC - u) >= H_VIRKE for u in lagen_u):
            lagen_u.append(k * CC)
    return [u for u in sorted(lagen_u) if 0.0 <= u <= L - H_VIRKE + 1e-6]


def reglarna(kod: str) -> list[tuple[float, float]]:
    """De lätta väggarnas reglar (u0, u1) längs väggen, för installationer som går i regelfacken."""
    lv = next(lv for lv in LATTA if lv.kod == kod)
    return [(u, u + H_VIRKE) for u in _reglarnas_u(lv, _spann(lv)[0])]


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

    spann, over = _spann(lv)
    if lv.syll:
        for q in P.polygoner(box(0.0, 0.0, L, H_VIRKE).difference(
                unary_union([box(a, -1.0, b, H_VIRKE + 1.0) for a, b in spann] or [Polygon()]))):
            lagg("S", q)
    lagg("H", Polygon([(u, z - H_VIRKE) for u, z in topp] + [(u, z) for u, z in topp[::-1]]))
    # reglar: vid ändarna, c/c 600 och vid dörrarnas sidor (i dörröppningarna och fickorna bara kortreglar över
    # överstycket)
    for u in _reglarnas_u(lv, spann):
        z0 = next((zo + H_VIRKE for (a, b), zo in zip(spann, over) if u + H_VIRKE > a + 1e-6 and u < b - 1e-6),
                  H_VIRKE)
        lagg("R", Polygon([(u, z0), (u + H_VIRKE, z0), (u + H_VIRKE, ztopp(u + H_VIRKE) - H_VIRKE),
                           (u, ztopp(u) - H_VIRKE)]))
    for (a, b), zo in zip(spann, over):
        lagg("L", box(a, zo, b, zo + H_VIRKE))
    return p.montage()


def montage() -> Montage:
    m = Montage("Innerväggar", beskrivning="Lätta väggar 45×70 och skikten på innerväggarna")
    latta = Montage("Lätta väggar", beskrivning="Stomme 45×70 C24 (planritning 201 rev 02)")
    for lv in LATTA:
        if not lv.grupp:
            latta.lagg(_stomme(lv), lv.vagg.placering())
    m.lagg(latta)
    skikt = Montage("Innerväggarnas skikt", beskrivning="OSB 12 och gips 13, mot badrummet plywood 15, gips 12, "
                                                        "tätskikt och kakel")
    for kod in ORDNING:
        skikt.lagg(_skikt().montage[kod], vaggdef(kod).placering())
    m.lagg(skikt)
    return m
