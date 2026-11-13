"""Ytterväggarnas insida (F-01): ångbroms, liggande installationsläkt 45×45 c/c 600 med mineralull mellan läkten
(U-05; skikt.ULL_I_VAGGARNA), OSB 12 och gips 13, i badrummet
plywood 15, gips 12, tätskikt och kakel; i gaveln 1SV (reglar 45×145) ångbroms, OSB och gips direkt på
reglarna, med OSB:n fram till långsidornas stomme i hörnen (skjuvskiva i K-04) och långsidornas skikt mot den.

Vid fönstren och dörrarna går skikten fram till karmens linje (10 mm in i regelverkets öppning, över drevningen),
med installationsläkt runt öppningen i samma linje, så att smygen (fonster_och_dorrar.py) ligger an mot dem utan
språng. Insidan går från bjälklaget upp till innertaket, kapad längs det så att gipsen möts i en skarp linje; gavlarnas
insida följer taket upp till takbalkarnas underkant och innertaket slutar mot den. Långsidorna går mellan gavlarna och
gavlarnas insida börjar vid långsidornas insida. I dalarna, där en gavel går förbi en långsidas ände (ytterhörn sett
inifrån), går skikten runt hörnet var för sig: gavelns fram till långsidans och långsidans förbi gaveln. Delar som
står mot insidan (bärande innerväggar och deras skikt, stolpar, dalbalkarnas ändar, takets stomme vid gavlarna) går
skikten runt.
"""
from __future__ import annotations

from functools import cache
from typing import Any

from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

from modellering import Montage, Placering, lada

from trebodar import skelett as S
from trebodar.byggdelar import polygon as P
from trebodar.byggdelar.genomforing import genomfor
from trebodar.byggdelar.regelvagg import Plan
from trebodar.hus.fonster_och_dorrar.oppningar import DORRAR, OPPNINGAR
from trebodar.hus.rum import BADRUM
from trebodar.hus.stomme import lagen
from trebodar.hus.tak.takytor import tak_underkant
from trebodar.material import MINERALULL

from . import vaggar
from .skikt import (INSIDA_T, INSIDA_VATRUM_T, LAKT, ULL_I_VAGGARNA, grund, i_badrum, innertak_underkant, insida_vanlig_t,
                    installationsskikt, skivlager)

@cache
def _hinder() -> tuple[list[tuple[Polygon, float, float]], list[tuple[Polygon, float, float]]]:
    """Delar som står mot ytterväggarnas insida, som (plan, z0, z1): de bärande innerväggarnas delar och skikt,
    stolparnas delar och dalbalkarnas ändar; för skivorna också de lätta väggarnas stommar."""
    ut = list(vaggar.barande_skikt())
    for d in lagen.innervaggar() + lagen.stolpar():
        x0, y0, z0, x1, y1, z1 = d.lada
        ut.append((box(x0, y0, x1, y1), z0, z1))
    for b in S.BALKAR.values():
        ut.append((box(b.x - S.BALK_B / 2, b.y0, b.x + S.BALK_B / 2, b.y1), b.uk, b.ok))
    return ut, ut + vaggar.stommar()


def _yta(kod: str, u0: float, u1: float) -> Polygon:
    """Ytterväggens insida i väggens (u, z): vid takfoten upp till innertaket vid skiktens yta mot rummet (skikten
    kapas sedan längs innertaket, _kapa_vid_innertaket), på gavlarna längs taket upp till takbalkarnas underkant
    (innertaket slutar mot gavelns insida)."""
    v = S.YTTERVAGGAR[kod]
    if kod in S.TAKFALL:
        t = S.TAKFALL[kod]
        return box(u0, 0.0, u1, innertak_underkant(t, t.x_insida + t.riktning * INSIDA_VATRUM_T) + 1.0)
    pl = v.placering()

    def z(u: float) -> float:
        x, y, _ = pl.punkt((u, v.tjocklek, 0.0))
        zt = tak_underkant(x, y)
        assert zt is not None, (kod, u)
        return zt - S.TAKBALK_HV
    # brytpunkter: nocken och dalarna (där gaveln går förbi en långsidas ände ligger grannkroppens takfall över den)
    brott = [S.HUSKROPPAR[int(kod[0])].nock] + [b.x for b in S.BALKAR.values() if b.typ == "dal"]
    us = sorted({u0, u1} | {u for u in ((x - v.origo[0]) * v.u[0] for x in brott) if u0 < u < u1})
    return Polygon([(u0, 0.0), (u1, 0.0)] + [(u, z(u)) for u in reversed(us)])


def _badrum_langs(kod: str, u0: float, u1: float, w0: float, w1: float) -> list[tuple[float, float]]:
    """Badrummets utbredning längs väggen kod (u-intervall) i bandet w0–w1 från stommens yttre yta."""
    pl = S.YTTERVAGGAR[kod].placering()
    band = Polygon([pl.punkt((u0, w0, 0))[:2], pl.punkt((u1, w0, 0))[:2], pl.punkt((u1, w1, 0))[:2],
                    pl.punkt((u0, w1, 0))[:2]])
    Pi = pl.invers()
    ut = []
    for g in P.polygoner(BADRUM.intersection(band)):
        us = [Pi.punkt((x, y, 0.0))[0] for x, y in g.exterior.coords]
        ut.append((min(us), max(us)))
    return sorted(ut)


def badrumsremsor(t: S.Takfall) -> list[tuple[float, float, float, float]]:
    """Där badrummet ligger mot en gavel är gavelns insida tjockare och innertaket slutar vid den: remsorna (x0, x1,
    y0, y1) mellan den vanliga insidans och våtrumsskiktets yta."""
    ut = []
    for kod, v in S.YTTERVAGGAR.items():
        if kod in S.TAKFALL or int(kod[0]) != t.kropp:
            continue
        pl = v.placering()
        for a, b in _badrum_langs(kod, 0.0, v.langd, v.tjocklek, v.tjocklek + INSIDA_VATRUM_T):
            horn = [pl.punkt((u, v.tjocklek + w, 0))[:2] for u in (a, b) for w in (INSIDA_T, INSIDA_VATRUM_T)]
            xs, ys = [x for x, _ in horn], [y for _, y in horn]
            ut.append((min(xs), max(xs), min(ys), max(ys)))
    return ut


def _stomme(kod: str) -> Polygon:
    """Ytterväggens stomme i plan."""
    v = S.YTTERVAGGAR[kod]
    pl = v.placering()
    return Polygon([pl.punkt((u, w, 0.0))[:2] for u, w in ((0.0, 0.0), (v.langd, 0.0), (v.langd, v.tjocklek),
                                                            (0.0, v.tjocklek))])


@cache
def _ytterhorn(kod: str, slut: bool) -> bool:
    """Väggens början eller slut är ett ytterhörn sett inifrån: rummet fortsätter förbi änden vid väggens insida.
    Så är det i dalarna, där en gavel går förbi en långsidas ände (1NO–2SO, 2SV–1NV, 2NV–3NO och 2SV–3SO)."""
    v = S.YTTERVAGGAR[kod]
    x, y, _ = v.placering().punkt((v.langd + 1.0 if slut else -1.0, v.tjocklek + 1.0, 0.0))
    p = Point(x, y)
    hus = Polygon(S.KONTUR).buffer(S.STOMME_UT, join_style=2)
    return hus.contains(p) and not any(_stomme(k).contains(p) for k in S.YTTERVAGGAR)


def _u_granser(kod: str, a: float, b: float) -> tuple[float, float]:
    """Skiktet a–b (från stommens insida) längs väggen: långsidorna mellan gavlarna, gavlarna från långsidornas
    insida; gavlarna utan installationsskikt (1SV) från långsidornas stomme, och långsidornas skikt slutar
    mot dem. I ett ytterhörn går gavelns skikt fram till långsidans skikt (a förbi änden) och långsidans skikt förbi
    gaveln och täcker gavelns skikt (gavelns tjocklek och b förbi änden), så att skikten möts var för sig."""
    v = S.YTTERVAGGAR[kod]
    gavel = kod not in S.TAKFALL

    def forbi(slut: bool) -> float:
        """Hur långt skiktet går förbi änden i ett ytterhörn: gavelns fram till långsidans skikt, långsidans förbi
        gavelns stomme."""
        if gavel:
            return a
        x, y, _ = v.placering().punkt((v.langd + 1.0 if slut else -1.0, -1.0, 0.0))
        g = S.ytterstomme_vid(x, y)
        return (S.t_stomme(g) if g else S.T_STOMME) + b

    def langsidan(u: float) -> float:
        """Långsidans stomme och insida (med badrummet) vid gavelns u; gavlarna utan installationsskikt går till
        långsidans stomme (OSB:n, skjuvskiva i K-04, hela vägen till hörnet)."""
        if not installationsskikt(kod):
            return S.T_STOMME
        return S.T_STOMME + (INSIDA_VATRUM_T if i_badrum(kod, u) else INSIDA_T)

    def gaveln(slut: bool) -> float:
        """Där långsidan slutar mot en gavel utan installationsskikt slutar skikten mot gavelns insida."""
        x, y, _ = v.placering().punkt((v.langd + 1.0 if slut else -1.0, v.tjocklek / 2, 0.0))
        g = S.ytterstomme_vid(x, y)
        return 0.0 if g is None or installationsskikt(g) else insida_vanlig_t(g)
    if gavel:
        u0 = -forbi(False) if _ytterhorn(kod, False) else langsidan(S.T_STOMME + 1.0)
        u1 = v.langd + forbi(True) if _ytterhorn(kod, True) else v.langd - langsidan(v.langd - S.T_STOMME - 1.0)
    else:
        u0 = -forbi(False) if _ytterhorn(kod, False) else gaveln(False)
        u1 = v.langd + forbi(True) if _ytterhorn(kod, True) else v.langd - gaveln(True)
    return u0, u1


def insidans_plan(kod: str) -> Polygon:
    """Ytterväggens insida i plan, med de vanliga skikten (badrummets tjockare insida har innertaket i
    badrumsremsor)."""
    g = [_u_granser(kod, a, b) for _, a, b, _, _ in grund(kod) + skivlager(kod)["vanligt"]]
    u0, u1 = min(x[0] for x in g), max(x[1] for x in g)
    pl = S.YTTERVAGGAR[kod].placering()
    t, i = S.t_stomme(kod), insida_vanlig_t(kod)
    return Polygon([pl.punkt((u, w, 0.0))[:2] for u, w in ((u0, t), (u1, t), (u1, t + i), (u0, t + i))])


_YTOR: dict[str, list[tuple[float, Any, Any]]] = {}
_SKIVOR: dict[str, list[Any]] = {}


def barande_skivor(kod: str) -> Any:
    """OSB:n direkt på reglarna i en yttervägg utan installationsskikt (1SV, skjuvskiva i K-04): ytan i
    väggens (u, z); tom för väggarna med installationsskikt."""
    insida(kod)
    return unary_union(_SKIVOR.get(kod, []))


def synliga_ytor(kod: str) -> list[tuple[float, Any, Any]]:
    """Ytterväggens synliga yta (det yttersta skiktet): (w i väggens system, ytan i (u, z), materialet), för
    golvlisterna (#100)."""
    insida(kod)
    return _YTOR[kod]


@cache
def insida(kod: str) -> Montage:
    """Ytterväggens insida: ångbroms, liggande installationsläkt 45×45 c/c 600, OSB och gips (i badrummet plywood,
    gips, tätskikt och kakel)."""
    v = S.YTTERVAGGAR[kod]
    T = v.tjocklek
    lager = skivlager(kod)
    m = Montage(f"Insida {kod}", beskrivning="Ångbroms, installationsskikt 45" +
                (" med mineralull" if ULL_I_VAGGARNA else "") + ", OSB 12 och gips 13 (i badrummet plywood 15, gips 12, "
                "tätskikt och kakel)"
                if installationsskikt(kod) else
                "Ångbroms, OSB 12 och gips 13 direkt på reglarna")
    # skiktens utbredning längs väggen (_u_granser)
    granser = {(a, b): _u_granser(kod, a, b) for _, a, b, _, _ in grund(kod) + [x for ls in lager.values() for x in ls]}
    u0, u1 = min(g[0] for g in granser.values()), max(g[1] for g in granser.values())
    topp = _yta(kod, u0, u1).bounds[3]
    # öppningarna i karmens linje (dörrarna från golvet, fönstren under fönsterbänken: Oppning.inre)
    opp = [o for o in OPPNINGAR.get(kod, []) if o.z1 > 0.0]
    hal_lista = [box(o.inre[0], o.z0 if o.typ in DORRAR else o.inre[1], o.inre[2], o.inre[3]) for o in opp]
    # skivorna slutar SMYGLIST längre från karmen, för smyglisterna (utom i badrummet, med kakel runt om)
    hal_skivor = [box(*o.skivornas_hal) for o in opp if not i_badrum(kod, (o.u0 + o.u1) / 2)]
    # installationsläkten runt öppningarna i karmens linje: på sidorna, över och under fönstren
    ram = []
    for o in (opp if installationsskikt(kod) else []):
        ku0, kz0, ku1, kz1 = o.inre
        zb = o.z0 if o.typ in DORRAR else kz0 - LAKT
        ram += [box(ku0 - LAKT, zb, ku0, kz1 + LAKT), box(ku1, zb, ku1 + LAKT, kz1 + LAKT), box(ku0, kz1, ku1, kz1 + LAKT)]
        if o.typ not in DORRAR:
            ram.append(box(ku0, kz0 - LAKT, ku1, kz0))
    ram_u = unary_union(ram) if ram else Polygon()
    # delar som står mot väggens insida: deras utbredning i u och z tas bort
    pl = v.placering()
    band = Polygon([pl.punkt((u0, T, 0))[:2], pl.punkt((u1, T, 0))[:2], pl.punkt((u1, T + INSIDA_VATRUM_T, 0))[:2],
                    pl.punkt((u0, T + INSIDA_VATRUM_T, 0))[:2]])
    Pi = pl.invers()

    def oppet_mot(hinder: list[tuple[Polygon, float, float]], hal_bas: list[Polygon]) -> Polygon:
        hal = list(hal_bas)
        for poly, z0, z1 in hinder:
            g = poly.intersection(band)
            if g.area > 1.0:
                x0, y0, x1, y1 = g.bounds
                us = [Pi.punkt((x, y, 0.0))[0] for x in (x0, x1) for y in (y0, y1)]
                hal.append(box(min(us), z0, max(us), z1))
        return unary_union(hal) if hal else Polygon()
    oppet, oppet_skivor = oppet_mot(_hinder()[0], hal_lista), oppet_mot(_hinder()[1], hal_lista + hal_skivor)
    if kod not in S.TAKFALL:
        # gavlarna: takets stomme i skiktens band (takbalken och upplagsregeln över 1NO vid dalbalk 4), exakt
        y_lo, y_hi = band.bounds[1], band.bounds[3]
        tak = unary_union([Polygon([((x - v.origo[0]) * v.u[0], z) for x, z in q.exterior.coords])
                           for _, q, y0, y1 in lagen.takets_stomme() if min(y1, y_hi) - max(y0, y_lo) > 1.0])
        oppet, oppet_skivor = oppet.union(tak), oppet_skivor.union(tak)
    for namn, a, b, typ, mat in grund(kod):
        p = Plan(kod, f"{namn} {kod}", b - a, material=mat)
        ua, ub = granser[(a, b)]
        yta = _yta(kod, ua, ub)
        if namn == "Installationsskikt":
            # liggande läkt c/c 600 och överst i väggen (på gavlarna upp till snedtaket)
            rader = [0.0] + ([topp - LAKT] if kod in S.TAKFALL else [])
            rader += [z for z in (k * 600.0 for k in range(1, int(topp // 600) + 1))
                      if all(abs(z - r) >= LAKT for r in rader)]
            for z in sorted(rader):
                for q in P.polygoner(box(ua, z, ub, z + LAKT).intersection(yta).difference(oppet).difference(ram_u),
                                     45 * 100):
                    p.profil(P.kontur(q), T + a, T + b, typ=typ, material=mat)
            for r in ram:
                for q in P.polygoner(r.intersection(yta).difference(oppet), 45 * 100):
                    p.profil(P.kontur(q), T + a, T + b, typ=typ, material=mat)
            # mineralull mellan läkten (U-05): skiktets yta utom läkten
            lakt = unary_union([box(ua, z, ub, z + LAKT) for z in rader] + ram)
            ull = Plan(kod, f"Isolering i installationsskiktet {kod}", b - a, material=MINERALULL)
            for q in (P.polygoner(yta.difference(oppet).difference(lakt), 45 * 100) if ULL_I_VAGGARNA else ()):
                ull.skiva(P.kontur(q), P.hal(q), T + a, T + b, "II", MINERALULL, f"Mineralull {b - a:.0f} {kod}")
            m.lagg(p.montage())
            if ull.bitar:
                m.lagg(ull.montage())
            continue
        else:
            for q in P.polygoner(yta.difference(oppet)):
                p.skiva(P.kontur(q), P.hal(q), T + a, T + b, typ, mat, f"{namn} {kod}")
        m.lagg(p.montage())
    # skivorna: våtrumsskikt där badrummet ligger mot väggen (ytterväggarna i badrummet är målade, #105), annars OSB
    # och gips
    bad = _badrum_langs(kod, u0, u1, T, T + INSIDA_VATRUM_T)
    vatrum = unary_union([box(a, -1.0, b, topp + 1.0) for a, b in bad])
    vanligt = box(u0 - 1.0, -1.0, u1 + 1.0, topp + 1.0).difference(vatrum)
    plan: dict[str, Plan] = {}
    _YTOR[kod] = []
    _SKIVOR[kod] = []
    for omrade, skikt in ((vanligt, lager["vanligt"]), (vatrum, lager.get("vatrum_malat", []))):   # målade (#105)
        if not skikt:
            assert omrade.area < 1.0, kod
            continue
        namn_, a_, b_, _, mat_ = skikt[-1]
        _YTOR[kod].append((T + b_, _yta(kod, *granser[(a_, b_)]).intersection(omrade).difference(oppet_skivor),
                           mat_))
        for namn, a, b, typ, mat in skikt:
            p = plan.setdefault(namn, Plan(kod, f"{namn} {kod}", b - a, material=mat))
            for q in P.polygoner(_yta(kod, *granser[(a, b)]).intersection(omrade).difference(oppet_skivor)):
                p.skiva(P.kontur(q), P.hal(q), T + a, T + b, typ, mat, f"{namn} {kod}")
                if not installationsskikt(kod) and (namn, a) == skikt[0][:2]:
                    _SKIVOR[kod].append(q)
    for p in plan.values():
        if p.bitar:
            m.lagg(p.montage())
    if kod in S.TAKFALL:
        _kapa_vid_innertaket(m, kod, u0, u1)
    return m


def _kapa_vid_innertaket(m: Montage, kod: str, u0: float, u1: float) -> None:
    """Takfotsväggens insida kapas längs innertakets underkant, så att innertakets gips går över väggens skivor och
    möter dem i en skarp linje (väggens översta läkt och innertakets nedersta läkt bakom skivornas kanter)."""
    t = S.TAKFALL[kod]
    z0 = innertak_underkant(t, t.x_insida)
    w0 = S.T_STOMME - 100.0                    # verktyget börjar 100 mm utanför stommens insida, i planet
    origo = (u0 - 1000.0, w0, z0 - 100.0 * S.TAN)
    langs = 600.0
    verktyg = lada(u1 - u0 + 2000.0, langs, 1000.0).placerad(
        Placering.axlar(origo, (1.0, 0.0, 0.0), (0.0, -S.SIN, S.COS)))
    genomfor(m, verktyg, (u0 - 1000.0, w0 - 600.0, z0 - 200.0, u1 + 1000.0, w0 + langs, z0 + 1500.0))


def montage() -> Montage:
    m = Montage("Ytterväggarnas insida")
    for kod in S.YTTERVAGGAR:
        m.lagg(insida(kod), S.YTTERVAGGAR[kod].placering())
    return m
