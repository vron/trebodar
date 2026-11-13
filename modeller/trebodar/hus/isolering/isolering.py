"""Isoleringen: träfiber mellan takbalkarna (F-01: 170 mm) och mineralull i ytterväggarnas regelfack (95 mm) och i
gavelspetsarna. Mineralullen i installationsskikten hör till de invändiga skikten (vagginsida.py och innertak.py).

Taket: i varje fack mellan takbalkar (och takstolarnas ytterbalkar), från isolerstoppet vid takfoten till
nockbalkens eller dalbalkens sida (vid balken ovanför upplagsregeln), mellan takbalkarnas över- och underkant
(vågrätt avskuren i hammarbandets överkant) och utanför takfönstrens öppningar och avväxlingar. Isolerstoppet är en regel 45 mm, bultad på
hammarbandet i ytterväggens liv i varje fack vid takfoten, upp till takbalkarnas överkant och kapad efter takplanet;
hårdboarden slutar på den. Där en innerväggs övre hammarband (1A-H02) går upp mellan takbalkarna börjar isoleringen
över det. Väggarna: regelfacken, dvs. väggens yta minus alla reglar och
öppningar, genom hela stommen. Gavelspetsarna (U-05): gavelstolens fack från väggens överkant upp till takbalkarnas
överkant, genom väggens tjocklek och skuret kring stommens delar.
"""
from __future__ import annotations

from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from modellering import Del, Montage, i_foraldern, omslutande

from trebodar import skelett as S
from trebodar.hus.stomme import lagen
from trebodar.byggdelar import polygon as P
from trebodar.byggdelar import takbalk as TB
from trebodar.byggdelar import taklager as L
from trebodar.byggdelar.genomforing import genomfor_alla
from trebodar.byggdelar.regelvagg import Plan
from trebodar.byggdelar.virke import fmt
from trebodar.hus.fonster_och_dorrar.oppningar import OPPNINGAR
from trebodar.hus.stomme.prefab.takbalkar.takbalkar import FALT, balkens_sida
from trebodar.hus.stomme.prefab.takstolar.takstolar import STOLAR
from trebodar.hus.tak.takytor import tak_underkant
from trebodar.hus.stomme.prefab.yttervaggar.yttervaggar import VAGGAR as VAGGMODULER
from trebodar.material import C24, MINERALULL, TRAFIBER

def _hammarband_i_facken(t: S.Takfall) -> list[tuple[float, float, float]]:
    """Innerväggarnas hammarband som går upp mellan takfallets takbalkar (över takbalkarnas underkant): (y0, y1, hur
    långt upp över underkanten, vinkelrätt mot takplanet)."""
    ut = []
    for d in lagen.innervaggar():
        x0, y0, z0, x1, y1, z1 = d.lada
        if d.typ != "H" or not (min(t.x_insida, S.BALKAR[FALT[t.kod].nock].x) < 0.5 * (x0 + x1)
                                < max(t.x_insida, S.BALKAR[FALT[t.kod].nock].x)):
            continue
        # delen är 45 tjock vinkelrätt mot lutningen: underkanten i den låga änden (lådans z0) plus 45 / cos
        x_lag = x0 if t.riktning > 0 else x1
        upp = (z0 + 45.0 / S.COS - t.z_underkant(x_lag)) * S.COS
        if upp > 1.0:
            ut.append((y0, y1, upp))
    return ut


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
        # mellan upplagsregeln och balken går isoleringen fram till balken ovanför regeln
        vid_balk = [(f.nock, ovre)] + ([(dal.kod, nedre)] if dal and dal.y0 <= ym <= dal.y1 else [])
        for balk, kant in vid_balk:
            xs = balkens_sida(balk, t)
            zr = TB.regel_ok(t, balk, xs, 1 if xs > S.BALKAR[balk].x else -1)
            q = L.profil(t, -S.TAKBALK_H, 0.0, L.Kant("lodratt", xs), kant)
            if not q:
                continue
            ovan = Polygon(q).intersection(box(-1e5, zr, 1e5, 1e5))
            if ovan.geom_type != "Polygon" or ovan.area < 100:
                continue
            for a0, a1 in sorted({(a0, a1) for k0, k1, a0, a1 in bitar if kant in (k0, k1)}):
                p.profil([(float(x), float(z)) for x, z in list(ovan.exterior.coords)[:-1]], a0, a1, typ="TI",
                         material=TRAFIBER)
        hb = _hammarband_i_facken(t)
        for k0, k1, a0, a1 in bitar:
            # remsorna i y: över innerväggarnas hammarband börjar isoleringen över dem
            snitt = sorted({a0, a1} | {y for h0, h1, _ in hb for y in (h0, h1) if a0 < y < a1})
            for b0, b1 in zip(snitt, snitt[1:]):
                upp = max((u for h0, h1, u in hb if h0 < b1 - 1e-6 and b0 + 1e-6 < h1), default=0.0)
                q = L.profil(t, -S.TAKBALK_H + upp, 0.0, k0, k1)
                if not q:
                    continue
                poly = Polygon(q).intersection(box(-1e5, S.H_VAGG, 1e5, 1e5))
                if poly.area > 100:
                    p.profil([(float(x), float(z)) for x, z in list(poly.exterior.coords)[:-1]], b0, b1, typ="TI",
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
    t = S.t_stomme(kod)
    p = Plan(kod, f"Väggisolering {kod}", t, beskrivning=MINERALULL.beskrivning, material=MINERALULL)
    for g in fack:
        if g.area > 45 * 45 and min(g.bounds[2] - g.bounds[0], g.bounds[3] - g.bounds[1]) > 20:
            p.skiva(P.kontur(g), P.hal(g), 0.0, t, "VI", MINERALULL, f"Mineralull {t:.0f} {kod}")
    return p.montage()


def gavelspets(kod: str) -> Montage:
    """Mineralull i gavelspetsen: gavelstolens fack från väggens överkant (stolens säte) upp till takbalkarnas
    överkant, genom väggens tjocklek. Där gaveln går förbi en dal ligger grannkroppens takfall över den, med sin egen
    isolering mellan takbalkarna; där slutar gavelspetsens isolering i takbalkarnas underkant. Stommens delar
    (stolen, balkarna, takbalkarna och deras upplag) skärs ur."""
    v = S.YTTERVAGGAR[kod]
    pl = v.placering()
    t = v.tjocklek
    sate = min(d.lada[2] for d in lagen.takstol(kod) if d.typ == "U")      # underramen står på sätet
    nock = S.HUSKROPPAR[int(kod[0])].nock
    dalar = [b.x for b in S.BALKAR.values() if b.typ == "dal"]
    # husets egen kropp: mellan dalarna närmast nocken
    x_lo = max([x for x in dalar if x < nock], default=-1e9)
    x_hi = min([x for x in dalar if x > nock], default=1e9)

    def z(u: float, sida: float) -> float:
        """Isoleringens överkant vid u; i en dal på sidan sida (−1 eller 1) om dallinjen."""
        x, y, _ = pl.punkt((u, t / 2, 0.0))
        zt = tak_underkant(x, y)
        if zt is None:
            return sate
        return zt if x_lo < x + sida * v.u[0] * 1e-3 < x_hi else zt - S.TAKBALK_HV
    us = sorted({0.0, v.langd} | {u for u in ((x - v.origo[0]) * v.u[0] for x in [nock, *dalar]) if 0.0 < u < v.langd})
    ovre = [(u, z(u, sida)) for u in us for sida in (-1.0, 1.0) if 0.0 <= u + sida <= v.langd]
    yta = Polygon([(0.0, sate), (v.langd, sate)] + ovre[::-1]).buffer(0).intersection(box(-1e5, sate, 1e5, 1e5))
    p = Plan(kod, f"Gavelisolering {kod}", t, beskrivning=MINERALULL.beskrivning, material=MINERALULL)
    for g in P.polygoner(yta, 45 * 45):
        p.skiva(P.kontur(g), P.hal(g), 0.0, t, "GI", MINERALULL, f"Mineralull {t:.0f} gavelspets {kod}")
    m = p.montage()
    horn = [pl.punkt((u, w, zz)) for u in (0.0, v.langd) for w in (0.0, t) for zz in (sate, yta.bounds[3])]
    xs, ys, zs = ([h[i] for h in horn] for i in range(3))
    # bara delar som går in i gavelspetsen (1 mm), inte de som ligger an mot den
    genomfor_alla(m, lagen.former((min(xs) + 1.0, min(ys) + 1.0, min(zs) + 1.0, max(xs) - 1.0, max(ys) - 1.0,
                                   max(zs) - 1.0)), pl)
    return m


def montage() -> Montage:
    m = Montage("Isolering", beskrivning="Träfiber 170 mellan takbalkarna, mineralull 95 i ytterväggarna (145 i "
                                         "gavlarna 1SV och 2SV) och i gavelspetsarna")
    t = Montage("Tak")
    for kod in S.TAKFALL:
        t.lagg(tak(kod))
    m.lagg(t)
    v = Montage("Ytterväggar")
    for kod in S.YTTERVAGGAR:
        v.lagg(vagg(kod), S.YTTERVAGGAR[kod].placering())
    m.lagg(v)
    g = Montage("Gavelspetsar")
    for kod in STOLAR:
        if kod in S.YTTERVAGGAR:
            g.lagg(gavelspets(kod), S.YTTERVAGGAR[kod].placering())
    m.lagg(g)
    return m
