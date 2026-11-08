"""Golvlisterna (#100): oljad ask 15 × 35 längs golvet på alla gipsväggar på plan 1, på väggarnas synliga yta (det
yttersta skiktet där det är gips: inte kaklet och den målade våtrumsytan i badrummet eller kaminens
kalciumsilikat). Listen följer ytans underkant, så att den slutar vid dörröppningarna, och slutar där något står mot
väggen på golvet: inredningen (köket, garderoben, sängen), kaminen, dörrarnas och fönsterdörrarnas karmar och smygar
och ändbrädorna av ask. I inåthörnen slutar den ena listen mot den andra.
"""
from __future__ import annotations

from functools import cache
from typing import Any

from shapely.geometry import LineString, box as plan_box
from shapely.ops import unary_union

from modellering import Del, Montage, Placering, box

from trebodar import skelett as S
from trebodar.hus.fonster_och_dorrar import fonster_och_dorrar
from trebodar.hus.invandigt import andbrador, kokets_inbyggnad, vagginsida, vaggar
from trebodar.hus.invandigt.vaggar import vaggdef
from trebodar.hus.kamin import kamin
from trebodar.hus.stomme.lagen import ladar
from trebodar.material import ASK, GIPS

from . import garderob, kok, sang

LIST = (15.0, 35.0)             # tjocklek ut från väggen, höjd
PROV_Z = 10.0                   # ytans underkant prövas så högt över golvet
FRITT = 2.0                     # listen slutar så långt från det som står mot väggen
MINST = 50.0                    # kortare bitar läggs inte


@cache
def _hinder() -> Any:
    """Det som står mot väggarna vid golvet, i plan."""
    lador = [b for m in (garderob.montage(), sang.montage(), kok.montage(), kamin.montage(),
                         fonster_och_dorrar.montage(), andbrador.montage(), kokets_inbyggnad.montage())
             for b in ladar(m)]
    saker = [plan_box(x0, y0, x1, y1).buffer(FRITT, join_style=2)
             for x0, y0, z0, x1, y1, z1 in lador if z0 < LIST[1] and z1 > 0.0]
    # väggarnas skikt och stommar vid golvet (skikten går runt hörnen bakom andra väggars skikt)
    vaggarna = [plan_box(x0, y0, x1, y1)
                for m in (vagginsida.montage(), vaggar.montage()) for x0, y0, z0, x1, y1, z1 in ladar(m)
                if z0 < LIST[1] and z1 > 0.0]
    return unary_union(saker + vaggarna)


def _ytor() -> list[tuple[str, tuple[float, float], tuple[float, float], tuple[float, float], float, int, Any]]:
    """Gipsytorna: (vägg, origo, u, w, ytans w, riktningen ut i rummet längs w, ytan i (u, z))."""
    ut = []
    for kod, sida, w, yta, mat in vaggar.synliga_ytor():
        if mat is GIPS:
            v = vaggdef(kod)
            ut.append((kod, v.origo, v.u, v.w, w, sida, yta))
    for kod, v in S.YTTERVAGGAR.items():
        for w, yta, mat in vagginsida.synliga_ytor(kod):
            if mat is GIPS:
                ut.append((kod, v.origo, v.u, v.w, w, 1, yta))
    return ut


def montage() -> Montage:
    m = Montage("Golvlister", beskrivning="Golvlister av oljad ask 15 × 35 på gipsväggarna (#100)")
    t, h = LIST
    hinder = _hinder()
    lagda: list[Any] = []
    nr = 0
    for kod, (ox, oy), (ux, uy), (wx, wy), w, sida, yta in _ytor():
        linje = yta.intersection(LineString([(-1e5, PROV_Z), (1e5, PROV_Z)]))
        for seg in getattr(linje, "geoms", [linje]):
            if seg.is_empty or seg.length < MINST:
                continue
            u0, u1 = sorted(c[0] for c in seg.coords)

            def xy(u: float, ww: float) -> tuple[float, float]:
                return ox + ux * u + wx * ww, oy + uy * u + wy * ww
            # listens mittlinje mot det som står mot väggen: en list per fri sträcka
            mitt = LineString([xy(u0, w + sida * t / 2), xy(u1, w + sida * t / 2)]).difference(hinder)
            mitt = mitt.difference(unary_union(lagda)) if lagda else mitt      # inåthörnen: mot listen som ligger
            for g in getattr(mitt, "geoms", [mitt]):
                if g.is_empty or g.length < MINST:
                    continue
                (xa, ya), (xb, yb) = g.coords[0], g.coords[-1]
                ua, ub = sorted(((xa - ox) * ux + (ya - oy) * uy, (xb - ox) * ux + (yb - oy) * uy))
                hornen = [xy(ua, w), xy(ub, w), xy(ub, w + sida * t), xy(ua, w + sida * t)]
                x0, y0 = min(q[0] for q in hornen), min(q[1] for q in hornen)
                x1, y1 = max(q[0] for q in hornen), max(q[1] for q in hornen)
                nr += 1
                lagda.append(plan_box(x0, y0, x1, y1))
                m.lagg(Del(f"Golvlist ask {t:g}×{h:g} vägg {kod}", box(x0, x1, y0, y1, 0.0, h), ASK), Placering(),
                       f"GL{nr:03d}")
    return m
