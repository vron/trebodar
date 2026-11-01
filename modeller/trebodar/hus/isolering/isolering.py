"""Isoleringen: träfiber mellan takbalkarna (F-01: 170 mm) och mineralull i ytterväggarnas regelfack (95 mm).

Taket: i varje fack mellan takbalkar (och takstolarnas ytterbalkar), från ytterväggens utsida till nockbalkens
eller dalbalkens sida, mellan takbalkarnas över- och underkant (vågrätt avskuren i hammarbandets överkant) och
utanför takfönstrens öppningar och avväxlingar. Väggarna: regelfacken, dvs. väggens yta minus alla reglar och
öppningar, genom hela stommen.
"""
from __future__ import annotations

from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from modellering import Montage, i_foraldern, omslutande

from trebodar import skelett as S
from trebodar.byggdelar import polygon as P
from trebodar.byggdelar import taklager as L
from trebodar.byggdelar.regelvagg import Plan
from trebodar.hus.fonster_och_dorrar.oppningar import OPPNINGAR
from trebodar.hus.stomme.prefab.takbalkar.takbalkar import FALT, _sida
from trebodar.hus.stomme.prefab.yttervaggar.yttervaggar import VAGGAR as VAGGMODULER
from trebodar.material import MINERALULL, TRAFIBER

GAVELVAGGAR = {1: ("1NO", "1SV"), 2: ("2NO", "2SV"), 3: ("3NO", "3SV")}
TAKFOTSVAGG_UT = {"1SO": -30.0, "1NV": 4340.0, "2SO": 4470.0, "2NV": 9340.0, "3SO": 9470.0, "3NV": 13840.0}


def _fack(kod: str) -> list[tuple[float, float]]:
    """Facken (y0, y1) mellan takbalkar och gavelväggarnas insida."""
    t = S.TAKFALL[kod]
    g0, g1 = GAVELVAGGAR[t.kropp]
    y_in0 = S.YTTERVAGGAR[g0].origo[1] + S.T_STOMME          # NO-gavelns insida
    if g0 == "2NO":
        y_in0 += 45.0                                          # takstolens inre sneda delar (2NO-X02, X03)
    y_in1 = S.YTTERVAGGAR[g1].origo[1] - S.T_STOMME          # SV-gavelns insida
    kanter = [y_in0] + sorted(FALT[kod].y) + [y_in1]
    ut = []
    for a, b in zip(kanter, kanter[1:]):
        y0 = a if a == y_in0 else a + 45.0
        if b - y0 > 30:
            ut.append((y0, b))
    # facken delas där en bärande innervägg eller mittstolen 2C (med toppklossar) står, och vid dalbalkarnas ändar
    hinder = {1: [(7115.0, 7185.0), (8185.0, 8255.0), (10952.5, 11047.5)], 2: [(2152.5, 2247.5), (5900.0, 6040.0)],
              3: []}[t.kropp]
    for y0, y1 in hinder:
        ut = [d for a, b in ut for d in ((a, min(b, y0)), (max(a, y1), b)) if d[1] - d[0] > 30]
    f = FALT[kod]
    if f.dal:
        for yd in (S.BALKAR[f.dal].y0, S.BALKAR[f.dal].y1):
            ut = [d for a, b in ut for d in (((a, yd), (yd, b)) if a < yd < b else ((a, b),)) if d[1] - d[0] > 30]
    return ut


def tak(kod: str) -> Montage:
    t = S.TAKFALL[kod]
    f = FALT[kod]
    p = Plan(kod, f"Takisolering {kod}", 1.0, beskrivning=TRAFIBER.beskrivning, material=TRAFIBER)
    # mot balkarna slutar isoleringen vid upplagsregelns yttre sida
    ovre = L.Kant("lodratt", _sida(f.nock, t) - t.riktning * 45.0)
    dal = S.BALKAR[f.dal] if f.dal else None
    for y0, y1 in _fack(kod):
        ym = 0.5 * (y0 + y1)
        nedre = L.Kant("lodratt", _sida(dal.kod, t) + t.riktning * 45.0 if dal and dal.y0 <= ym <= dal.y1
                       else TAKFOTSVAGG_UT[kod])
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
        b = omslutande(i.barn.form)                        # type: ignore[union-attr]
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
