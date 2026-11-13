"""
U-05: husets nedre del i 3D: marken, källarens väggar och bottenplatta, mellanbjälklaget med golvvärmen och plattan
på mark, stationärt med finita volymer (fv.py, AMG-förbehandlad CG).

Koordinater som i K-05 (m): x, y från skärningen mellan mellanbjälklagets kanter, z från bjälklagets överkant.
Källarväggarnas linjer läses ur ../K-05/bild/geometri.json (kontrollerad mot modellen med kontroll_geometri05.py) och
plintarnas storlek ur ../K-06/resultat.json, som i U-01.

Omgivningar: rummet på plan 1 (inne), källaren (kallare), ute (uteluften och markytan) och golvvärmens plan
(varme, ett tunt lager i rörens nivå över de uppvärmda ytorna). Ytterväggarna ovanför bjälklaget finns inte med:
ytan under väggarna och plattans kant är adiabatiska, och skarvarna lägger till det som saknas (skarvar.py).
Källarens fönster och dörr räknas som vägg här och byts mot fönstren i byggnadsmodellen.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from matplotlib.path import Path as MPath

from fv import Modell, kanter

HERE = Path(__file__).resolve().parent
K05 = json.loads((HERE.parent / "K-05" / "bild" / "geometri.json").read_text(encoding="utf-8"))
K06 = json.loads((HERE.parent / "K-06" / "resultat.json").read_text(encoding="utf-8"))
T_KUB = (0.0125, 0.100, 0.150, 0.100)            # gips, cellplast, kärna, cellplast (inifrån)
HALV = 0.175                                      # halva väggens tjocklek utan gips


def kallarvaggar():
    """Källarväggarnas linjer [(riktning, läge, a, b, yttre)] i m."""
    return [(v[0], v[1] / 1000, v[2] / 1000, v[3] / 1000, v[4] == "yttre") for v in K05["vagg"]]


def kallarens_kontur():
    """Källarens kontur i väggarnas mittlinjer (polygon, m), ur de yttre väggarna."""
    pts = [(0.145, 3.735), (4.645, 3.735), (4.645, 0.145), (9.165, 0.145), (9.165, 1.145), (13.665, 1.145),
           (13.665, 12.365), (9.645, 12.365), (9.645, 10.865), (4.545, 10.865), (4.545, 9.205), (0.145, 9.205)]
    return pts


def pelare():
    pl = {p["namn"]: p["b"] / 1000 for p in K06["platta"]["L400"]["plintar"]}
    return [(x / 1000 + (0.04 if i == 7 else 0.0), y / 1000, pl[f"P{i}"])
            for i, (x, y) in enumerate(K05["pelare"], 1)]


def _inuti(poly, X, Y):
    return MPath(np.asarray(poly)).contains_points(np.c_[X.ravel(), Y.ravel()]).reshape(X.shape)


def _forskjut(poly, d):
    """Polygonen förskjuten d utåt (negativ inåt), med raka hörn (shapely)."""
    from shapely.geometry import Polygon
    p = Polygon(poly).buffer(d, join_style=2)
    return list(p.exterior.coords)


def markniva_funktion(P):
    """Markytans nivå z(x, y) [m] utanför huset: nivån vid närmaste punkt på stommens utsida (per fasad, ur
    indata), oförändrad utåt."""
    from shapely.geometry import LineString, Point
    S = P["_skelett"]
    segs = []
    for kod, (o, u, L) in S.items():
        prof = np.asarray(P["mark"]["niva"][kod], float)
        a = np.array(o)
        b = a + L * np.array(u)
        segs.append((LineString([a, b]), a, np.array(u), L, prof[:, 0] / 1000, prof[:, 1] / 1000))

    def z(x, y):
        out = np.empty(x.shape)
        pts = np.c_[x.ravel(), y.ravel()]
        best = np.full(len(pts), np.inf)
        val = np.zeros(len(pts))
        for ls, a, u, L, pu, pz in segs:
            # avstånd till sträckan
            ab = u * L
            t = np.clip(((pts - a) @ u), 0, L)
            q = a + np.outer(t, u)
            d = np.hypot(*(pts - q).T)
            bt = d < best
            best[bt] = d[bt]
            val[bt] = np.interp(t[bt], pu, pz)
        return val.reshape(x.shape)
    return z


def bygg(P, h=None, grov=1.0, bryggor=True):
    """3D-modellen. h: cellstorlek vid väggar och kanter [m]; grov: skalar alla cellstorlekar (nätkontroll);
    bryggor False: utan kantbalkar, balkar och plintar (cellplast 300 under hela bottenplattan, jämförelse)."""
    M = P["material"]
    Y = P["ytmotstand"]
    h = (h or P["nat"]["h_3d"] / 1000) * grov
    hmax = P["nat"]["h_3d_max"] / 1000 * grov
    kontur = np.array(P["_kontur"])
    platta = np.array(P["platta_pa_mark"]["kontur"]) / 1000
    trapp = np.array(P["_trapphal"])
    kk = kallarens_kontur()
    vaggar = kallarvaggar()
    B = P["bjalklag"]
    BP = P["bottenplatta"]
    hb = B["h"] / 1000
    z_bp = -2.25
    z_bp_b = z_bp - BP["betong"] / 1000
    z_eps = z_bp - (BP["betong"] + BP["eps"]) / 1000
    z_kb = z_bp - BP["kantbalk_h"] / 1000
    z_mak = z_eps - BP["makadam"] / 1000
    z_berg = P["mark"]["berg_z"] / 1000 - BP["makadam"] / 1000
    PM = P["platta_pa_mark"]
    z_pm_eps = -hb - PM["eps"] / 1000
    z_pm_mak = z_pm_eps - PM["makadam"] / 1000
    z_ror = -B["ror_z"] / 1000
    D = P["mark"]["djup"] / 1000
    bredd = max(np.ptp(kontur[:, 0]), np.ptp(kontur[:, 1]))
    ut = P["mark"]["utbredning"] * bredd
    x0, x1 = kontur[:, 0].min() - ut, kontur[:, 0].max() + ut
    y0, y1 = kontur[:, 1].min() - ut, kontur[:, 1].max() + ut
    z0 = z_mak - D
    # brytpunkter: väggarnas skikt, konturen och dess förskjutningar, plattan på mark, trapphålet, plintarna
    bx, by = [x0, x1], [y0, y1]
    fx, fy = [], []
    for r, lage, a, b, yttre in vaggar:
        # väggens skikt, och kantbalkens (ytterväggar) och balkens (innerväggar) kanter under den
        lag = [lage + s * d for s in (-1, 1) for d in (0.075, 0.175, 0.1875, 0.375 if yttre else 0.225)]
        (bx if r == "v" else by).extend(lag)
        (fx if r == "v" else fy).append((lage - 0.4, lage + 0.4, h))
        (by if r == "v" else bx).extend([a, b])
    for px, py in kontur:
        bx += [px, px + 0.03, px - 0.135, px - 0.285]
        by += [py, py + 0.03, py - 0.135, py - 0.285]
        bx += [px - 0.03, px - 0.07, px + 0.135, px + 0.285]
        by += [py - 0.03, py - 0.07, py + 0.135, py + 0.285]
        fx.append((px - 0.4, px + 0.4, h))
        fy.append((py - 0.4, py + 0.4, h))
    for px, py in platta:
        bx += [px - 0.07, px]
        by += [py - 0.07, py]
    for px, py in trapp:
        bx += [px, px - 0.15, px + 0.15]
        by += [py, py - 0.15, py + 0.15]
    for px, py, b in pelare():
        bx += [px - b / 2, px + b / 2]
        by += [py - b / 2, py + b / 2]
    bx = [v for v in bx if x0 <= v <= x1]
    by = [v for v in by if y0 <= v <= y1]
    # z: marken, bottenplattan, källaren (var 100 mm, så att marknivåerna hamnar nära), bjälklaget, rummet
    bz = [z0, z_berg, z_mak, z_eps, z_eps + BP["fot_eps"] / 1000, z_kb, z_bp_b, z_bp, z_pm_mak, z_pm_eps,
          -hb, z_ror - 0.002, z_ror + 0.002, 0.0, 0.05]
    bz += list(np.arange(z_bp, -hb, 0.1))
    fz = [(z_mak - 0.2, 0.05, 0.1 * grov), (z_eps - 0.05, z_bp + 0.05, h), (-hb - 0.05, 0.05, h)]
    ex = kanter(bx, fina=fx, h_max=hmax, tillvaxt=0.35)
    ey = kanter(by, fina=fy, h_max=hmax, tillvaxt=0.35)
    ez = kanter(bz, fina=fz, h_max=hmax, tillvaxt=0.35)
    m = Modell([ex, ey, ez])
    X, Y_, Z = np.meshgrid(*m.mitt, indexing="ij")
    X2, Y2 = X[:, :, 0], Y_[:, :, 0]
    zc = m.mitt[2]

    def kol(mask2d, za, zb):
        """3D-mask: kolumnerna mask2d mellan za och zb."""
        kz = (zc > za) & (zc < zb)
        return mask2d[:, :, None] & kz[None, None, :]

    # marken: berg under z_berg, fyllning över, upp till markytan utanför huset och upp till plattorna under huset
    zm = markniva_funktion(P)(X2, Y2)
    stomme_ut = _inuti(_forskjut(kontur, 0.03), X2, Y2)
    zm = np.where(stomme_ut, -hb, zm)
    berg = M["berg"]["lam"]
    m.mat[:] = m.nytt_material("berg", berg)
    fyll = m.nytt_material("fyllning", M["fyllning"]["lam"])
    m.mat[Z > z_berg] = fyll
    # ovan markytan utanför huset: uteluft
    over = (Z > zm[:, :, None]) & ~stomme_ut[:, :, None]
    m.tom_mask(over, "ute", Rs=Y["Rse"], etikett="markyta")
    # källaren: bottenplatta (betong 100, cellplast 300, makadam), kantbalkar och L-element under de yttre väggarna
    kall_ut = _inuti(_forskjut(kk, HALV), X2, Y2)                 # källarväggarnas yttre liv
    kall_in = _inuti(_forskjut(kk, -HALV - 0.0125), X2, Y2)       # gipsens yta
    lam_eps, lam_epsm, lam_b = M["eps"]["lam"], M["eps_mark"]["lam"], M["betong"]["lam"]
    m.mat[kol(kall_ut, z_mak, z_eps)] = m.nytt_material("makadam", M["makadam"]["lam"])
    m.mat[kol(kall_ut, z_eps, z_bp_b)] = m.nytt_material("eps_mark", lam_epsm)
    m.mat[kol(kall_ut, z_bp_b, z_bp)] = m.nytt_material("betong", lam_b)
    # kantbalken innanför L-elementets rygg (100), 450 bred, på cellplast 100
    rygg = kall_ut & ~_inuti(_forskjut(kk, HALV - BP["rygg_eps"] / 1000), X2, Y2)
    kb = _inuti(_forskjut(kk, HALV - BP["rygg_eps"] / 1000), X2, Y2) & \
        ~_inuti(_forskjut(kk, HALV - (BP["rygg_eps"] + BP["kantbalk_b"]) / 1000), X2, Y2)
    if bryggor:
        m.mat[kol(kb, z_kb, z_bp)] = m.nytt_material("betong", lam_b)
    m.mat[kol(rygg, z_eps, z_bp)] = m.nytt_material("eps_mark", lam_epsm)
    # balkar under innerväggarna och plintar, på cellplast 100
    for r, lage, a, b, yttre in (vaggar if bryggor else []):
        if yttre:
            continue
        msk = ((np.abs(X2 - lage) < 0.225) & (Y2 > a) & (Y2 < b)) if r == "v" else \
              ((np.abs(Y2 - lage) < 0.225) & (X2 > a) & (X2 < b))
        m.mat[kol(msk & kall_in, z_kb, z_bp)] = m.nytt_material("betong", lam_b)
    for px, py, b in (pelare() if bryggor else []):
        msk = (np.abs(X2 - px) < b / 2) & (np.abs(Y2 - py) < b / 2)
        m.mat[kol(msk, z_kb, z_bp)] = m.nytt_material("betong", lam_b)
    # källarväggarna (Kub 350-150 med gips) från bottenplattan till bjälklaget. Ytterväggarna följer källarens
    # kontur runt om, också förbi fönstren och dörren (som räknas som vägg här), med cellplasten och kärnan obrutna
    # runt hörnen. Innerväggarna följer K-05:s linjer med sina dörröppningar: en ände som möter en annan vägg går
    # in i den (kärnorna gjuts ihop), en fri ände slutar där linjen slutar.
    def ring(d0, d1):
        """Bandet mellan konturens förskjutningar d0 och d1 (utåt positivt)."""
        return _inuti(_forskjut(kk, d1), X2, Y2) & ~_inuti(_forskjut(kk, d0), X2, Y2)

    def moter(r, lage, t):
        """Om väggens ände (läget t längs väggen) ligger i en annan väggs mittlinje."""
        return any(r2 != r and abs(l2 - t) < 1e-6 and a2 - 1e-6 <= lage <= b2 + 1e-6 for r2, l2, a2, b2, _ in vaggar)

    inre_vagg = np.zeros(X2.shape, bool)
    inre_karna = np.zeros(X2.shape, bool)
    inre_gips = np.zeros(X2.shape, bool)
    for r, lage, a, b, yttre in vaggar:
        if yttre:
            continue
        s = X2 if r == "v" else Y2
        t = Y2 if r == "v" else X2
        fa, fb = float(moter(r, lage, a)), float(moter(r, lage, b))
        inre_vagg |= (t > a - HALV * fa) & (t < b + HALV * fb) & (np.abs(s - lage) < HALV)
        inre_karna |= (t > a - 0.075 * fa) & (t < b + 0.075 * fb) & (np.abs(s - lage) < 0.075)
        inre_gips |= (t > a - (HALV + 0.0125) * fa) & (t < b + (HALV + 0.0125) * fb) & \
            (np.abs(s - lage) < HALV + 0.0125)
    m.mat[kol((inre_gips & kall_in) | ring(-HALV - 0.0125, -HALV), z_bp, -hb)] = m.nytt_material("gips", M["gips"]["lam"])
    m.mat[kol((inre_vagg & kall_ut) | ring(-HALV, HALV), z_bp, -hb)] = m.nytt_material("eps", lam_eps)
    m.mat[kol(ring(0.075, HALV), z_bp, -hb)] = m.nytt_material("eps_mark", lam_epsm)
    karna = ring(-0.075, 0.075) | (inre_karna & _inuti(_forskjut(kk, 0.075), X2, Y2))
    m.mat[kol(karna, z_kb if bryggor else z_bp, -hb)] = m.nytt_material("betong", lam_b)
    # källarens luft: innanför gipsen, mellan bottenplattan och bjälklaget, utom innerväggarna
    luft = kall_in & ~inre_gips
    m.tom_mask(kol(luft, z_bp, -hb), "kallare", Rs=Y["Rsi_vagrat"], etikett="källarvägg")
    dz = m.d[2]
    k_golv = np.searchsorted(m.kant[2], z_bp + 1e-9) - 1        # första cellen över golvet
    k_tak = np.searchsorted(m.kant[2], -hb - 1e-9) - 1           # sista cellen under bjälklaget
    golv = np.zeros(m.form, bool)
    golv[:, :, k_golv] = luft
    m.tom_mask(golv, "kallare", Rs=Y["Rsi_nedat"], etikett="källargolv")
    tak = np.zeros(m.form, bool)
    tak[:, :, k_tak] = luft
    m.tom_mask(tak, "kallare", Rs=Y["Rsi_nedat"], etikett="källartak")
    # plattan på mark: cellplast 350 (L-elementens rygg 100 vid de fria kanterna), makadam 150
    pm = _inuti(platta, X2, Y2) & ~kall_ut
    pm_ut = _inuti(_forskjut(platta, 0.03), X2, Y2) & ~kall_ut
    m.mat[kol(pm_ut & ~_inuti(_forskjut(kk, HALV), X2, Y2), z_pm_mak, z_pm_eps)] = \
        m.nytt_material("makadam", M["makadam"]["lam"])
    m.mat[kol(pm_ut, z_pm_eps, -hb)] = m.nytt_material("eps_mark", lam_epsm)
    # mellanbjälklaget: betong 150 i konturen utom trapphålet
    kont = _inuti(kontur, X2, Y2)
    th = _inuti(trapp, X2, Y2)
    m.mat[kol(kont & ~th, -hb, 0.0)] = m.nytt_material("betong", lam_b)
    # trapphålet: källarens luft
    m.tom_mask(kol(th, -hb, 0.0), "kallare", Rs=Y["Rsi_vagrat"], etikett="trapphål")
    # plattans kant (30 mm till stommens utsida) och ytan under väggarna: adiabatiska (skarvarna)
    m.tom_mask(kol(stomme_ut & ~kont, -hb, 0.05), None)
    # rummet på plan 1 ovanför bjälklaget, innanför väggarnas insida
    rum = _inuti(_forskjut(kontur, -0.135), X2, Y2) & ~th
    m.tom_mask(kol(stomme_ut, 0.0, 1.0), None)
    m.tom_mask(kol(rum, 0.0, 1.0), "inne", Rs=P["ytmotstand"]["R_golvvarme"], etikett="golv")
    # golvvärmens plan: 150 mm från väggarnas insida och trapphålet
    varm = _inuti(_forskjut(kontur, -0.285), X2, Y2) & ~_inuti(_forskjut(trapp, 0.15), X2, Y2)
    m.tom_mask(kol(varm, z_ror - 0.0021, z_ror + 0.0021), "varme", Rs=0.0, etikett="golvvärme")
    # markytan är en egen omgivning (mark), så att den kan få en annan temperatur än luften (markens tröghet);
    # luften mot fasaden ovan mark (källarväggarnas utsida och plattan på marks sockel) är ute. Det understa lagret
    # tomma celler över marken räknas som markyta.
    ute = m.omg == m.omgivningar.index("ute")
    under = np.zeros(m.form, bool)
    under[:, :, 1:] = m.mat[:, :, :-1] >= 0
    nara = _inuti(_forskjut(kontur, 0.03 + 1.2 * h), X2, Y2) & ~stomme_ut
    mark = ute & (under | ~nara[:, :, None])
    m.tom_mask(mark, "mark", Rs=Y["Rse"], etikett="markyta")
    m.etik[ute & ~mark] = m.etikett("fasad")
    m.bygg()
    info = dict(N=m.N, form=m.form, h=h, z_bp=z_bp)
    return m, info
