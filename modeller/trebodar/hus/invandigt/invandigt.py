"""Invändiga skikt (F-01): ångbroms (Intello Plus, åldringsbeständig plastfolie), installationsskikt 45×45 och gips
2 × 12,5 under takbalkarna och på ytterväggarnas insida.

Innertaket följer takfallen (snedtak) från ytterväggens insida till nock- eller dalbalkens sida, med uppehåll vid
de bärande innerväggarna och mittstolen och öppningar för takfönstren. Ytterväggarnas insida går från bjälklaget
upp till innertaket (gavlar: följer snedtaket). Lätta innerväggar är ännu inte modellerade.
"""
from __future__ import annotations

from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from modellering import Montage

from trebodar import skelett as S
from trebodar.byggdelar import taklager as L
from trebodar.byggdelar.regelvagg import Plan
from trebodar.hus.fonster_och_dorrar.oppningar import OPPNINGAR
from trebodar.hus.isolering.isolering import _fack
from trebodar.hus.stomme.prefab.takbalkar.takbalkar import FALT, _sida
from trebodar.material import ANGBROMS, C24, GIPS

FOLIE, LAKT, GIPS_T = 0.4, 45.0, 25.0
TAK_W = (-S.TAKBALK_H - FOLIE, -S.TAKBALK_H)                 # under takbalkarnas underkant
LAKT_W = (TAK_W[0] - LAKT, TAK_W[0])
GIPS_W = (LAKT_W[0] - GIPS_T, LAKT_W[0])
INSIDA_T = FOLIE + LAKT + GIPS_T
CC = 400.0


def _tak(kod: str) -> Montage:
    t = S.TAKFALL[kod]
    f = FALT[kod]
    m = Montage(f"Innertak {kod}", beskrivning="Ångbroms, installationsskikt 45 och gips 2 × 12,5 under takbalkarna")
    ovre = L.Kant("lodratt", _sida(f.nock, t) - t.riktning * 10.0)      # 10 mm från nockbalken (huvudstolpen)
    dal = S.BALKAR[f.dal] if f.dal else None
    # sammanhängande sträckor i y (facken utan takbalkarnas uppdelning)
    strackor: list[list[float]] = []
    for y0, y1 in _fack(kod):
        if strackor and abs(strackor[-1][1] - y0) <= 45.0 + 1e-6:
            strackor[-1][1] = y1
        else:
            strackor.append([y0, y1])
    # vid gavlarna slutar innertaket vid gavelväggens insida (ångbroms, läkt och gips)
    if strackor:
        strackor[0][0] += INSIDA_T
        strackor[-1][1] -= INSIDA_T
    lager = {"folie": Plan(kod, f"Ångbroms tak {kod}", 1.0, material=ANGBROMS),
             "lakt": Plan(kod, f"Installationsskikt tak {kod}", 45.0, material=C24),
             "gips": Plan(kod, f"Gips tak {kod}", 1.0, material=GIPS)}
    for y0, y1 in strackor:
        ym = 0.5 * (y0 + y1)
        delar = [(y0, y1)]
        if dal and y0 < dal.y0 < y1:
            delar = [(y0, dal.y0), (dal.y0, y1)]
        if dal and y0 < dal.y1 < y1:
            delar = [d for a, b in delar for d in (((a, dal.y1), (dal.y1, b)) if a < dal.y1 < b else ((a, b),))]
        for a, b in delar:
            ym = 0.5 * (a + b)
            # vid dalbalken börjar innertaket vid upplagsregelns yttre sida
            nedre = L.Kant("lodratt", _sida(dal.kod, t) + t.riktning * 45.0 if dal and dal.y0 <= ym <= dal.y1
                           else t.x_insida)
            # fönsteröppningar: skikten skärs vinkelrätt vid öppningens kanter
            snitt = [(a, b, nedre, ovre)]
            for fo in f.fonster:
                if a < fo.y0 and fo.y1 < b:
                    kn = L.Kant("vinkelrat", fo.x_ned)
                    ku = L.Kant("vinkelrat", fo.x_upp)
                    snitt = [(a, fo.y0, nedre, ovre), (fo.y0, fo.y1, nedre, kn), (fo.y0, fo.y1, ku, ovre),
                             (fo.y1, b, nedre, ovre)]
            for s0, s1, k0, k1 in snitt:
                for namn, w, typ in (("folie", TAK_W, "AB"), ("gips", GIPS_W, "GI")):
                    q = L.profil(t, *w, k0, k1)
                    if q:
                        lager[namn].profil(q, s0, s1, typ=typ, material=ANGBROMS if namn == "folie" else GIPS)
                # installationsskiktets läkt längs y, c/c 400 längs takfallet
                q = L.profil(t, *LAKT_W, k0, k1)
                if not q:
                    continue
                ys = Polygon(q)
                x_lo, x_hi = ys.bounds[0], ys.bounds[2]
                langd = (x_hi - x_lo) / S.COS
                n = int(langd // CC)
                for i in range(n + 1):
                    s = min(i * CC, langd - LAKT)
                    # läktens läge: s mm upp längs planet från den nedre kanten
                    x_start = x_lo if t.riktning > 0 else x_hi
                    xa = x_start + t.riktning * s * S.COS
                    xb = x_start + t.riktning * (s + LAKT) * S.COS
                    pl = L.profil(t, *LAKT_W, L.Kant("vinkelrat", min(xa, xb)), L.Kant("vinkelrat", max(xa, xb)))
                    if pl:
                        lp = Polygon(pl).intersection(ys)
                        if lp.area > 100:
                            lager["lakt"].profil([(float(x), float(z)) for x, z in list(lp.exterior.coords)[:-1]], s0,
                                                 s1, typ="IL", material=C24)
    for p in lager.values():
        if p.bitar:
            m.lagg(p.montage())
    return m


def _hinder() -> list[tuple[Polygon, float, float]]:
    """Delar som står mot ytterväggarnas insida: bärande innerväggar, syllar, stolparnas syllar och dalbalkarnas
    ändar, som (plan, z0, z1)."""
    from trebodar.hus.stomme.prefab.innervaggar.syllar import SYLLAR
    ut = []
    for v in S.INNERVAGGAR.values():
        ox, oy = v.origo
        ux, uy = v.u
        wx, wy = v.w
        h = [(ox, oy), (ox + ux * v.langd, oy + uy * v.langd), (ox + ux * v.langd + wx * 115, oy + uy * v.langd + wy * 115),
             (ox + wx * 115, oy + wy * 115)]
        ut.append((Polygon(h).buffer(15.0, join_style=2), 0.0, 4000.0))
    for x0, x1, y0, y1 in SYLLAR:
        ut.append((box(x0, y0, x1, y1), 0.0, 45.0))
    ut.append((box(10980, 4651, 13745, 4721), 0.0, 45.0))            # syllen vid LN1_2
    ut.append((box(10980, 6542, 13745, 6612), 0.0, 45.0))            # syllen vid LN1_3
    for b in S.BALKAR.values():
        ut.append((box(b.x - S.BALK_B / 2, b.y0, b.x + S.BALK_B / 2, b.y1), b.uk, b.ok))
    return ut


HINDER = _hinder()


def _vagg_insida(kod: str) -> Montage:
    """Ytterväggens insida: ångbroms, liggande installationsläkt 45×45 c/c 600, gips 2 × 12,5."""
    v = S.YTTERVAGGAR[kod]
    m = Montage(f"Insida {kod}", beskrivning="Ångbroms, installationsskikt 45 och gips 2 × 12,5")
    # från grannväggarnas insidor: u från T_STOMME till langd − T_STOMME där väggen möter en annan vägg i hörnen
    # långsidorna står mellan gavlarna och går ut i hörnen; gavlarnas insida börjar vid långsidornas insida
    u0, u1 = S.T_STOMME + INSIDA_T, v.langd - S.T_STOMME - INSIDA_T
    if kod in ("1NV", "2SO", "2NV", "3SO", "1SO", "3NV"):
        u0, u1 = 0.0, v.langd
    topp = S.H_VAGG - 75.0
    yta = box(u0, 0.0, u1, topp)
    hal_lista = [box(o.u0, o.z0, o.u1, o.z1) for o in OPPNINGAR.get(kod, [])]
    # delar som står mot väggens insida: deras utbredning i u och z tas bort
    P = v.placering()
    band = Polygon([P.punkt((u0, S.T_STOMME, 0))[:2], P.punkt((u1, S.T_STOMME, 0))[:2],
                    P.punkt((u1, S.T_STOMME + INSIDA_T, 0))[:2], P.punkt((u0, S.T_STOMME + INSIDA_T, 0))[:2]])
    Pi = P.invers()
    for poly, z0, z1 in HINDER:
        g = poly.intersection(band)
        if g.area > 1.0:
            us = [Pi.punkt((x, y, 0.0))[0] for x, y in g.exterior.coords]
            hal_lista.append(box(min(us), z0, max(us), z1))
    hal = unary_union(hal_lista) if hal_lista else Polygon()
    w = S.T_STOMME
    for namn, t, typ, mat in (("Ångbroms", FOLIE, "AB", ANGBROMS), ("Installationsskikt", LAKT, "IL", C24),
                              ("Gips", GIPS_T, "GI", GIPS)):
        p = Plan(kod, f"{namn} {kod}", t, material=mat)
        if namn == "Installationsskikt":
            rader = [0.0, topp - LAKT]
            rader += [z for z in (k * 600.0 for k in range(1, int(topp // 600) + 1)) if all(abs(z - r) >= LAKT for r in rader)]
            for z in sorted(rader):
                g = box(u0, z, u1, min(z + LAKT, topp)).difference(hal)
                for q in getattr(g, "geoms", [g]):
                    if q.geom_type == "Polygon" and q.area > 45 * 100:
                        p.profil([(float(a), float(b)) for a, b in list(q.exterior.coords)[:-1]], w, w + t, typ=typ,
                                 material=mat)
        else:
            g = yta.difference(hal)
            for q in getattr(g, "geoms", [g]):
                p.skiva(list(q.exterior.coords)[:-1], [list(r.coords)[:-1] for r in q.interiors], w, w + t, typ, mat,
                        f"{namn} {kod}")
        m.lagg(p.montage())
        w += t
    return m


def montage() -> Montage:
    m = Montage("Invändigt", beskrivning="Ångbroms, installationsskikt och gips (F-01)")
    tak = Montage("Innertak")
    for kod in S.TAKFALL:
        tak.lagg(_tak(kod))
    m.lagg(tak)
    vagg = Montage("Ytterväggarnas insida")
    for kod in S.YTTERVAGGAR:
        vagg.lagg(_vagg_insida(kod), S.YTTERVAGGAR[kod].placering())
    m.lagg(vagg)
    return m
