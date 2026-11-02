"""Isoleringen: träfiber mellan takbalkarna (F-01: 170 mm) och mineralull i ytterväggarnas regelfack (95 mm).

Taket: i varje fack mellan takbalkar (och takstolarnas ytterbalkar), från isolerstoppet vid takfoten till
nockbalkens eller dalbalkens sida, mellan takbalkarnas över- och underkant (vågrätt avskuren i hammarbandets
överkant) och utanför takfönstrens öppningar och avväxlingar. Isolerstoppet är en regel 45 mm, bultad på
hammarbandet i ytterväggens liv i varje fack vid takfoten, upp till takbalkarnas överkant och kapad efter takplanet;
hårdboarden slutar på den. Väggarna: regelfacken, dvs. väggens yta minus alla reglar och
öppningar, genom hela stommen.
"""
from __future__ import annotations

from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from modellering import Del, Montage, i_foraldern, omslutande

from trebodar import skelett as S
from trebodar.hus.stomme import lagen
from trebodar.byggdelar import polygon as P
from trebodar.byggdelar import taklager as L
from trebodar.byggdelar.regelvagg import Plan
from trebodar.byggdelar.virke import fmt
from trebodar.hus.fonster_och_dorrar.oppningar import OPPNINGAR
from trebodar.hus.stomme.prefab.takbalkar.takbalkar import FALT, balkens_sida
from trebodar.hus.stomme.prefab.yttervaggar.yttervaggar import VAGGAR as VAGGMODULER
from trebodar.material import C24, MINERALULL, TRAFIBER

def tak(kod: str) -> Montage:
    t = S.TAKFALL[kod]
    f = FALT[kod]
    p = Plan(kod, f"Takisolering {kod}", 1.0, beskrivning=TRAFIBER.beskrivning, material=TRAFIBER)
    # mot balkarna slutar isoleringen vid upplagsregelns yttre sida
    ovre = L.Kant("lodratt", balkens_sida(f.nock, t) - t.riktning * 45.0)
    dal = S.BALKAR[f.dal] if f.dal else None
    for y0, y1 in lagen.fack(kod):
        ym = 0.5 * (y0 + y1)
        if dal and dal.y0 <= ym <= dal.y1:
            nedre = L.Kant("lodratt", balkens_sida(dal.kod, t) + t.riktning * 45.0)
        else:
            # takfoten: isolerstoppet på hammarbandet, isoleringen innanför
            ut, inne = L.Kant("lodratt", t.x_utsida), L.Kant("lodratt", t.x_utsida + t.riktning * L.STOPP_T)
            q = L.profil(t, -S.TAKBALK_H, 0.0, ut, inne)
            assert q
            stopp = Polygon(q).intersection(box(-1e5, S.H_VAGG, 1e5, 1e5))
            # i takfönstrens fack går kortlingen till takfoten mitt i facket
            ky = [0.5 * (fo.y0 + fo.y1) for fo in f.fonster if fo.y0 - 1 <= y0 and y1 <= fo.y1 + 1]
            for a0, a1 in ([(y0, ky[0] - 22.5), (ky[0] + 22.5, y1)] if ky else [(y0, y1)]):
                p.profil([(float(x), float(z)) for x, z in list(stopp.exterior.coords)[:-1]], a0, a1, typ="IS",
                         material=C24, bas_namn=f"Isolerstopp {fmt(L.STOPP_T)}×{fmt(stopp.bounds[3] - S.H_VAGG)}")
            nedre = inne
        bitar = [(nedre, ovre, y0, y1)]
        for fo in f.fonster:
            if fo.y0 - 1 <= y0 and y1 <= fo.y1 + 1:            # fönstrets fack: under och över avväxlingarna
                a = L.Kant("vinkelrat", L.langs(t, fo.x_ned, -45.0))
                b = L.Kant("vinkelrat", L.langs(t, fo.x_upp, 45.0))
                km = 0.5 * (fo.y0 + fo.y1)
                bitar = [(nedre, a, y0, km - 22.5), (nedre, a, km + 22.5, y1),
                         (b, ovre, y0, km - 22.5), (b, ovre, km + 22.5, y1)]
        for k0, k1, a0, a1 in bitar:
            q = L.profil(t, -S.TAKBALK_H, 0.0, k0, k1)
            if not q:
                continue
            poly = Polygon(q).intersection(box(-1e5, S.H_VAGG, 1e5, 1e5))
            if poly.area > 100:
                p.profil([(float(x), float(z)) for x, z in list(poly.exterior.coords)[:-1]], a0, a1, typ="TI",
                         material=TRAFIBER)
    return p.montage()


def vagg(kod: str) -> Montage:
    """Regelfacken i ytterväggen: ytor som delarna och öppningarna (i u–z) helt omsluter."""
    upptaget = []
    for i in VAGGMODULER[kod].montage().barn:
        assert isinstance(i.barn, Del)
        b = omslutande(i.barn.form)
        assert b is not None
        u0, _, z0, u1, _, z1 = i_foraldern(b, i.placering)
        upptaget.append(box(u0, z0, u1, z1))
    for o in OPPNINGAR.get(kod, []):
        upptaget.append(box(o.u0, o.z0, o.u1, o.z1))
    U = unary_union(upptaget)
    fack = [Polygon(r) for g in P.polygoner(U) for r in g.interiors]
    p = Plan(kod, f"Väggisolering {kod}", S.T_STOMME, beskrivning=MINERALULL.beskrivning, material=MINERALULL)
    for g in fack:
        if g.area > 45 * 45 and min(g.bounds[2] - g.bounds[0], g.bounds[3] - g.bounds[1]) > 20:
            p.skiva(P.kontur(g), P.hal(g), 0.0, S.T_STOMME, "VI", MINERALULL, f"Mineralull 95 {kod}")
    return p.montage()


def montage() -> Montage:
    m = Montage("Isolering", beskrivning="Träfiber 170 mellan takbalkarna, mineralull 95 i ytterväggarna")
    t = Montage("Tak")
    for kod in S.TAKFALL:
        t.lagg(tak(kod))
    m.lagg(t)
    v = Montage("Ytterväggar")
    for kod in S.YTTERVAGGAR:
        v.lagg(vagg(kod), S.YTTERVAGGAR[kod].placering())
    m.lagg(v)
    return m
