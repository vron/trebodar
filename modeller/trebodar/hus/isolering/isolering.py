"""Isoleringen: träfiber mellan takbalkarna (F-01: 170 mm) och mineralull i ytterväggarnas regelfack (95 mm).

Taket: i varje fack mellan takbalkar (och takstolarnas ytterbalkar), från ytterväggens utsida till nockbalkens
eller dalbalkens sida, mellan takbalkarnas över- och underkant (vågrätt avskuren i hammarbandets överkant) och
utanför takfönstrens öppningar och avväxlingar. Väggarna: regelfacken, dvs. väggens yta minus alla reglar och
öppningar, genom hela stommen.
"""
from __future__ import annotations

from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from modellering import Del, Montage, i_foraldern, omslutande

from trebodar import skelett as S
from trebodar.byggdelar import lagen
from trebodar.byggdelar import polygon as P
from trebodar.byggdelar import taklager as L
from trebodar.byggdelar.regelvagg import Plan
from trebodar.hus.fonster_och_dorrar.oppningar import OPPNINGAR
from trebodar.hus.stomme.prefab.takbalkar.takbalkar import FALT, _sida
from trebodar.hus.stomme.prefab.takstolar.takstolar import STOLAR
from trebodar.hus.stomme.prefab.yttervaggar.yttervaggar import VAGGAR as VAGGMODULER
from trebodar.material import MINERALULL, TRAFIBER

GAVELVAGGAR = {1: ("1NO", "1SV"), 2: ("2NO", "2SV"), 3: ("3NO", "3SV")}
TAKSTOLSVAGGAR = set(STOLAR) & set(S.INNERVAGGAR)       # innerväggar med takstol (mittstolen 2C)


def _med_takstol(kod: str) -> tuple[float, float]:
    """Väggens utbredning i y med takstolen som står på den (gavelstolen 2NO har sneda delar och mittstolen 2C
    toppklossar utanför väggens tjocklek)."""
    v = S.VAGGAR[kod]
    ys = [v.origo[1], v.origo[1] + v.w[1] * v.tjocklek]
    ys += [y for g, _, (_, y0, _, _, y1, _) in lagen.takstolar() if g.endswith(f"/Takstol {kod}") for y in (y0, y1)]
    return min(ys), max(ys)


def _gavel_insida(kod: str) -> float:
    """Gavelns insida (y) mot takets fack: gavelväggens eller gavelstolens, den som når längst in."""
    y0, y1 = _med_takstol(kod)
    return y1 if S.YTTERVAGGAR[kod].w[1] > 0 else y0


def _fack(kod: str) -> list[tuple[float, float]]:
    """Facken (y0, y1) mellan takbalkar och gavlarnas insida."""
    t = S.TAKFALL[kod]
    g0, g1 = GAVELVAGGAR[t.kropp]
    y_in0, y_in1 = _gavel_insida(g0), _gavel_insida(g1)
    kanter = [y_in0] + sorted(FALT[kod].y) + [y_in1]
    ut = []
    for a, b in zip(kanter, kanter[1:]):
        y0 = a if a == y_in0 else a + 45.0
        if b - y0 > 30:
            ut.append((y0, b))
    # facken delas där en bärande innervägg (med takstol) står, och vid dalbalkarnas ändar
    hinder = [_med_takstol(kod_v) for kod_v, v in S.INNERVAGGAR.items()
              if int(kod_v[0]) == t.kropp and abs(v.u[0]) > 0.5]
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
                       else t.x_utsida)
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
