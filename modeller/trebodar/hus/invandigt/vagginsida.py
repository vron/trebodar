"""Ytterväggarnas insida (F-01): ångbroms, liggande installationsläkt 45×45 c/c 600, OSB 12 och gips 13, i badrummet
plywood 15, gips 12, tätskikt och kakel.

Insidan går från bjälklaget upp till innertaket, kapad längs det så att gipsen möts i en skarp linje; gavlarnas
insida följer taket upp till takbalkarnas underkant och innertaket slutar mot den. Långsidorna går mellan gavlarna och
gavlarnas insida börjar vid långsidornas insida. I dalarna, där en gavel går förbi en långsidas ände (ytterhörn sett
inifrån), går skikten runt hörnet var för sig: gavelns fram till långsidans och långsidans förbi gaveln. Delar som
står mot insidan (bärande innerväggar och deras skikt, stolpar, dalbalkarnas ändar, takets stomme vid gavlarna) går
skikten runt.
"""
from __future__ import annotations

from functools import cache

from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

from modellering import Montage, Placering, lada

from trebodar import skelett as S
from trebodar.byggdelar import polygon as P
from trebodar.byggdelar.genomforing import genomfor
from trebodar.byggdelar.regelvagg import Plan
from trebodar.hus.fonster_och_dorrar.oppningar import OPPNINGAR
from trebodar.hus.rum import BADRUM
from trebodar.hus.stomme import lagen
from trebodar.hus.tak.takytor import tak_underkant

from . import vaggar
from .skikt import GRUND, INSIDA_T, INSIDA_VATRUM_T, LAKT, SKIVLAGER, innertak_underkant, insida_t

@cache
def _hinder() -> tuple[list[tuple[Polygon, float, float]], list[tuple[Polygon, float, float]]]:
    """Delar som står mot ytterväggarnas insida, som (plan, z0, z1): de bärande innerväggarnas delar och skikt,
    stolparnas delar och dalbalkarnas ändar; för skivorna också de lätta väggarnas stommar."""
    ut = list(vaggar.barande_skikt())
    for grupp, _, (x0, y0, z0, x1, y1, z1) in lagen.prefab():
        if not grupp.startswith("Ytterväggar/"):
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
        x, y, _ = pl.punkt((u, S.T_STOMME, 0.0))
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
        for a, b in _badrum_langs(kod, 0.0, v.langd, S.T_STOMME, S.T_STOMME + INSIDA_VATRUM_T):
            horn = [pl.punkt((u, S.T_STOMME + w, 0))[:2] for u in (a, b) for w in (INSIDA_T, INSIDA_VATRUM_T)]
            xs, ys = [x for x, _ in horn], [y for _, y in horn]
            ut.append((min(xs), max(xs), min(ys), max(ys)))
    return ut


def _stomme(kod: str) -> Polygon:
    """Ytterväggens stomme i plan."""
    v = S.YTTERVAGGAR[kod]
    pl = v.placering()
    return Polygon([pl.punkt((u, w, 0.0))[:2] for u, w in ((0.0, 0.0), (v.langd, 0.0), (v.langd, S.T_STOMME),
                                                            (0.0, S.T_STOMME))])


@cache
def _ytterhorn(kod: str, slut: bool) -> bool:
    """Väggens början eller slut är ett ytterhörn sett inifrån: rummet fortsätter förbi änden vid väggens insida.
    Så är det i dalarna, där en gavel går förbi en långsidas ände (1NO–2SO, 2SV–1NV, 2NV–3NO och 2SV–3SO)."""
    v = S.YTTERVAGGAR[kod]
    x, y, _ = v.placering().punkt((v.langd + 1.0 if slut else -1.0, S.T_STOMME + 1.0, 0.0))
    p = Point(x, y)
    hus = Polygon(S.KONTUR).buffer(S.STOMME_UT, join_style=2)
    return hus.contains(p) and not any(_stomme(k).contains(p) for k in S.YTTERVAGGAR)


def _u_granser(kod: str, a: float, b: float) -> tuple[float, float]:
    """Skiktet a–b (från stommens insida) längs väggen: långsidorna mellan gavlarna, gavlarna från långsidornas
    insida. I ett ytterhörn går gavelns skikt fram till långsidans skikt (a förbi änden) och långsidans skikt förbi
    gaveln och täcker gavelns skikt (gavelns tjocklek och b förbi änden), så att skikten möts var för sig."""
    v = S.YTTERVAGGAR[kod]
    gavel = kod not in S.TAKFALL
    forbi = a if gavel else S.T_STOMME + b
    u0 = -forbi if _ytterhorn(kod, False) else S.T_STOMME + insida_t(kod, S.T_STOMME + 1.0) if gavel else 0.0
    u1 = (v.langd + forbi if _ytterhorn(kod, True) else
          v.langd - S.T_STOMME - insida_t(kod, v.langd - S.T_STOMME - 1.0) if gavel else v.langd)
    return u0, u1


def insidans_plan(kod: str) -> Polygon:
    """Ytterväggens insida i plan, med de vanliga skikten (badrummets tjockare insida har innertaket i
    badrumsremsor)."""
    g = [_u_granser(kod, a, b) for _, a, b, _, _ in GRUND + SKIVLAGER["vanligt"]]
    u0, u1 = min(x[0] for x in g), max(x[1] for x in g)
    pl = S.YTTERVAGGAR[kod].placering()
    return Polygon([pl.punkt((u, w, 0.0))[:2] for u, w in ((u0, S.T_STOMME), (u1, S.T_STOMME),
                                                            (u1, S.T_STOMME + INSIDA_T), (u0, S.T_STOMME + INSIDA_T))])


def insida(kod: str) -> Montage:
    """Ytterväggens insida: ångbroms, liggande installationsläkt 45×45 c/c 600, OSB och gips (i badrummet plywood,
    gips, tätskikt och kakel)."""
    v = S.YTTERVAGGAR[kod]
    m = Montage(f"Insida {kod}", beskrivning="Ångbroms, installationsskikt 45, OSB 12 och gips 13 (i badrummet plywood "
                                             "15, gips 12, tätskikt och kakel)")
    # skiktens utbredning längs väggen (_u_granser)
    granser = {(a, b): _u_granser(kod, a, b) for _, a, b, _, _ in GRUND + SKIVLAGER["vanligt"] + SKIVLAGER["vatrum"]}
    u0, u1 = min(g[0] for g in granser.values()), max(g[1] for g in granser.values())
    topp = _yta(kod, u0, u1).bounds[3]
    hal_lista = [box(o.u0, o.z0, o.u1, o.z1) for o in OPPNINGAR.get(kod, [])]
    # delar som står mot väggens insida: deras utbredning i u och z tas bort
    pl = v.placering()
    band = Polygon([pl.punkt((u0, S.T_STOMME, 0))[:2], pl.punkt((u1, S.T_STOMME, 0))[:2],
                    pl.punkt((u1, S.T_STOMME + INSIDA_VATRUM_T, 0))[:2],
                    pl.punkt((u0, S.T_STOMME + INSIDA_VATRUM_T, 0))[:2]])
    Pi = pl.invers()

    def oppet_mot(hinder: list[tuple[Polygon, float, float]]) -> Polygon:
        hal = list(hal_lista)
        for poly, z0, z1 in hinder:
            g = poly.intersection(band)
            if g.area > 1.0:
                x0, y0, x1, y1 = g.bounds
                us = [Pi.punkt((x, y, 0.0))[0] for x in (x0, x1) for y in (y0, y1)]
                hal.append(box(min(us), z0, max(us), z1))
        return unary_union(hal) if hal else Polygon()
    oppet, oppet_skivor = oppet_mot(_hinder()[0]), oppet_mot(_hinder()[1])
    if kod not in S.TAKFALL:
        # gavlarna: takets stomme i skiktens band (takbalken och upplagsregeln över 1NO vid dalbalk 4), exakt
        y_lo, y_hi = band.bounds[1], band.bounds[3]
        tak = unary_union([Polygon([((x - v.origo[0]) * v.u[0], z) for x, z in q.exterior.coords])
                           for _, q, y0, y1 in lagen.takets_stomme() if min(y1, y_hi) - max(y0, y_lo) > 1.0])
        oppet, oppet_skivor = oppet.union(tak), oppet_skivor.union(tak)
    for namn, a, b, typ, mat in GRUND:
        p = Plan(kod, f"{namn} {kod}", b - a, material=mat)
        ua, ub = granser[(a, b)]
        yta = _yta(kod, ua, ub)
        if namn == "Installationsskikt":
            # liggande läkt c/c 600 och överst i väggen (på gavlarna upp till snedtaket)
            rader = [0.0] + ([topp - LAKT] if kod in S.TAKFALL else [])
            rader += [z for z in (k * 600.0 for k in range(1, int(topp // 600) + 1))
                      if all(abs(z - r) >= LAKT for r in rader)]
            for z in sorted(rader):
                for q in P.polygoner(box(ua, z, ub, z + LAKT).intersection(yta).difference(oppet), 45 * 100):
                    p.profil(P.kontur(q), S.T_STOMME + a, S.T_STOMME + b, typ=typ, material=mat)
        else:
            for q in P.polygoner(yta.difference(oppet)):
                p.skiva(P.kontur(q), P.hal(q), S.T_STOMME + a, S.T_STOMME + b, typ, mat, f"{namn} {kod}")
        m.lagg(p.montage())
    # skivorna: våtrumsskikt där badrummet ligger mot väggen, annars OSB och gips
    bad = _badrum_langs(kod, u0, u1, S.T_STOMME, S.T_STOMME + INSIDA_VATRUM_T)
    vatrum = unary_union([box(a, -1.0, b, topp + 1.0) for a, b in bad])
    vanligt = box(u0 - 1.0, -1.0, u1 + 1.0, topp + 1.0).difference(vatrum)
    plan: dict[str, Plan] = {}
    for omrade, lager in ((vanligt, SKIVLAGER["vanligt"]), (vatrum, SKIVLAGER["vatrum"])):
        for namn, a, b, typ, mat in lager:
            p = plan.setdefault(namn, Plan(kod, f"{namn} {kod}", b - a, material=mat))
            for q in P.polygoner(_yta(kod, *granser[(a, b)]).intersection(omrade).difference(oppet_skivor)):
                p.skiva(P.kontur(q), P.hal(q), S.T_STOMME + a, S.T_STOMME + b, typ, mat, f"{namn} {kod}")
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
