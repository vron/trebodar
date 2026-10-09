"""
K-05 Mellanbjälklag och källarpelare: alla kontroller av plattan och rören.

    python berakning.py        -> resultat.json och figurer (fig_*.svg), därefter rapport/ (Typst)

Steg: omhyllande snittkrafter (omhyllande.py) för rör med verklig axialstyvhet och styva rör, utjämning av
momenttoppar, böjning med tilläggsjärn i överkant, genomstansning per rör, stolplaster på plattan, tvärkraft,
långtidsnedböjning enligt 7.4.3, sprickbredd, minimiarmering, rörens knäckning, vindlyft, reaktioner på
Lecaväggarna och kontroll mot handberäkning och SINTEF (kontroll.py).
"""
import json
import os
import math

import numpy as np
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

from ec2 import (Betong, Stal, Armering, Lager, MRd, As_min, vRdc, vmin, k_size, sprickbredd, pelare_knackning,
                 huvudplat)
from modell import bygg, G as GEO, GK, QK, QV, H, LASTER
from omhyllande import kor, utjamna_linje, ULS
from analys import nedbojning

# ------------------------------------------------------------------ indata
B = Betong(fck=25)                    # C25/30
S = Stal(fyk=500)                     # B500B
C_UK = 20                             # täckskikt underkant [mm] (Plattor.pdf)
C_OK = int(__import__("os").environ.get("C_OK", 25))  # täckskikt överkant [mm]; Plattor.pdf anger 45
BAND = float(__import__("os").environ.get("BAND", 250))   # utjämningsbredd för momenttoppar [mm], ≈ 2d
KONV = 1.2                            # stödmoment i överkant × 1,2: nätkänslighet vid väggändar (validering/konvergens.py)
ZON = 1.25                            # tilläggsjärnen i zonerna för 1,25 × 1,2 = 1,5 × FE (validering/vaggande.py)
E_LECA, T_LECA, H_VAGG = 2000.0, 100.0, 2600.0   # Lecaväggen som fjäder i rörlastfallet [MPa, mm, mm]
PLAT = 200.0                          # huvudplåt där den behövs [mm]
ROR = (80, 4)                         # VKR 80×80×4
FY_ROR = 235.0
L_ROR = 2100.0
TOPPLAT = (80.0, 8.0, 235.0)           # topplåt på röret: sida, tjocklek, fy [mm, mm, MPa]
TOPPLAT_STOR = {"P7": (160.0, 25.0, 355.0)}   # större topplåt vid röret i trapphålets hörn
GD = 0.91
PSI2_Q, PSI2_S = 0.3, 0.1             # EKS tabell B-1
UTN_MAX = 0.95                        # val av utförande vid rören: minst 5 % marginal (rörlägen ±40 mm)
SANK = 10.0                           # och högst 100 % om överkantsarmeringen ligger 10 mm för lågt (utförande)
POST = (90.0, 95.0)                   # minsta stolpe 2 × 45×95 [mm], belastad yta för stolplast på plattan


NAT_UK, NAT_OK = (10, 150), (8, 150)  # nät: Ø10 s150 i underkant (x yttre), Ø8 s150 i överkant (x övre)


def arm(extra=None, sank=0.0):
    """Näten enligt NAT_UK, NAT_OK. extra = (dia, cc) tilläggsjärn i ök, i nätets lager.
    sank: överkantsarmeringen ligger så mycket lägre [mm] (känslighet för utförandet)."""
    du, do = NAT_UK[0], NAT_OK[0]
    a = Armering(H, ux=Lager(du, NAT_UK[1], H - C_UK - du / 2), uy=Lager(du, NAT_UK[1], H - C_UK - du - du / 2),
                 ox=Lager(do, NAT_OK[1], C_OK + do / 2 + sank), oy=Lager(do, NAT_OK[1], C_OK + do + do / 2 + sank))
    if extra:
        dia, cc = extra
        As = a.ox.As + math.pi * dia ** 2 / 4 / cc
        # tilläggsjärnen ligger i nätets lager; verksam höjd räknas till tilläggsjärnets centrum
        a.ox = Lager(math.sqrt(4 * As * cc / math.pi), cc, C_OK + dia / 2 + sank)
        a.oy = Lager(math.sqrt(4 * As * cc / math.pi), cc, C_OK + dia + dia / 2 + sank)
    return a


TILLAGG = [(8, 150), (10, 150), (12, 150), (12, 100)]


def mrd_ok(a):
    return MRd(a.ox.As, H - a.ox.y, B, S)[0], MRd(a.oy.As, H - a.oy.y, B, S)[0]


def mrd_uk(a):
    return MRd(a.ux.As, a.ux.y, B, S)[0], MRd(a.uy.As, a.uy.y, B, S)[0]


def f1(x, n=1):
    s = f"{x:,.{n}f}".replace(",", " ").replace(".", ",")
    return s.replace("-", "−")


R = {"indata": dict(fck=B.fck, fctm=B.fctm, Ecm=B.Ecm, fcd=B.fcd, fyd=S.fyd, c_uk=C_UK, c_ok=C_OK, band=BAND,
                    plat=PLAT, konv=KONV, zon=ZON, h=H, gk=GK * 1e3, qk=QK * 1e3, qv=QV * 1e3, nat_uk=NAT_UK, nat_ok=NAT_OK, sank=SANK)}

# ------------------------------------------------------------------ 1. omhyllande
print("omhyllande ...")
P1, env1, lf1 = kor(None)        # verklig rörstyvhet
P2, env2, lf2 = kor(1e9)         # styva rör
# styva rör och fjädrande Lecaväggar (E·t/h): ger störst rörlaster (validering/vaggande.py)
P3, env3, lf3 = kor(1e9, vagg_k=E_LECA * T_LECA / H_VAGG)
del lf3
assert P1.nn == P2.nn == P3.nn
envs = (env1, env2, env3)
env = {k: (np.maximum.reduce([e[k] for e in envs]) if k in ("mux", "muy") else np.minimum.reduce([e[k] for e in envs]))
       for k in ("mux", "muy", "mox", "moy")}
Rpel = {n: max(e["R"][n] for e in envs) for n in env1["R"]}
Rkomb = {n: max(envs, key=lambda e: e["R"][n])["Rkomb"][n] for n in env1["R"]}
r0 = lf1["G"]
sm = {"mux": utjamna_linje(r0, env["mux"], "x", BAND), "muy": utjamna_linje(r0, env["muy"], "y", BAND),
      "mox": KONV * utjamna_linje(r0, env["mox"], "x", BAND), "moy": KONV * utjamna_linje(r0, env["moy"], "y", BAND)}
P = P1
np.savez("falt.npz", xy=P.xy, tri=P.tri, **{k: v for k, v in env.items()}, **{"s_" + k: v for k, v in sm.items()})

# ------------------------------------------------------------------ 2. böjning
a0 = arm()
mux_rd, muy_rd = mrd_uk(a0)
mox_rd, moy_rd = mrd_ok(a0)
R["bojning"] = dict(
    uk=dict(MEd_x=sm["mux"].max(), MEd_y=sm["muy"].max(), topp_x=env["mux"].max(), topp_y=env["muy"].max(),
            MRd_x=mux_rd, MRd_y=muy_rd, d_x=a0.ux.y, d_y=a0.uy.y, As=a0.ux.As * 1e3),
    ok=dict(MEd_x=-sm["mox"].min(), MEd_y=-sm["moy"].min(), MRd_x=mox_rd, MRd_y=moy_rd, d_x=H - a0.ox.y,
            d_y=H - a0.oy.y, As=a0.ox.As * 1e3))
print(f"uk: MEd {sm['mux'].max()/1e3:.1f}/{sm['muy'].max()/1e3:.1f} (topp {env['mux'].max()/1e3:.1f}/{env['muy'].max()/1e3:.1f}) MRd {mux_rd/1e3:.1f}/{muy_rd/1e3:.1f}")
print(f"ök: MEd {-sm['mox'].min()/1e3:.1f}/{-sm['moy'].min()/1e3:.1f} MRd nät {mox_rd/1e3:.1f}/{moy_rd/1e3:.1f}")

# zoner där nätet i överkant inte räcker, även om armeringen ligger SANK mm för lågt (samma krav som för
# genomstansningen): utnyttjande per nod, sammanhängande områden -> rektanglar
mox_rl, moy_rl = mrd_ok(arm(sank=SANK))
utn_ok = np.maximum(-sm["mox"] / mox_rl, -sm["moy"] / moy_rl)
R["bojning"]["ok"].update(MRd_x_lag=mox_rl, MRd_y_lag=moy_rl)
from matplotlib.tri import Triangulation
over = utn_ok > 1.0
el_over = over[P.tri].any(1)
polys = [Polygon(P.xy[t]) for t in P.tri[el_over]]
LBD = 400.0                           # förankring ≈ 40Ø för Ø10
# största stödmoment intill lasterna över väggarna i kontrollmodellen med yttre skiktet (validering/ytterskikt.py)
_Y = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ytterskikt.json")
YTTER = json.load(open(_Y))["med"] if os.path.exists(_Y) else None
zoner = []
if polys:
    U = unary_union(polys).buffer(1.0)
    for g in getattr(U, "geoms", [U]):
        x0, y0, x1, y1 = g.bounds
        z = box(x0 - LBD, y0 - LBD, x1 + LBD, y1 + LBD).intersection(Polygon(GEO["kontur"]))
        m = np.array([Point(p).within(g.buffer(5)) for p in P.xy])
        Mx, My = -sm["mox"][m].min(), -sm["moy"][m].min()
        if YTTER and z.distance(Point(YTTER["xy"])) < 1.0:   # kontrollmodellen där också yttre Lecaskiktet bär
            Mx, My = max(Mx, KONV * YTTER["mo_nara"] * 1e3), max(My, KONV * YTTER["mo_nara"] * 1e3)
        val = None
        for t in TILLAGG:
            rx, ry = mrd_ok(arm(t, sank=SANK))
            if rx >= ZON * Mx and ry >= ZON * My:
                val = t
                break
        zoner.append(dict(bounds=[float(v) for v in z.bounds], MEd_x=Mx, MEd_y=My, tillagg=val,
                          cx=(x0 + x1) / 2, cy=(y0 + y1) / 2))
# slå ihop överlappande zoner
slut = []
for z in sorted(zoner, key=lambda z: -max(z["MEd_x"], z["MEd_y"])):
    bz = box(*z["bounds"])
    for s_ in slut:
        if box(*s_["bounds"]).intersects(bz):
            u = box(*s_["bounds"]).union(bz).bounds
            s_["bounds"] = list(u); s_["MEd_x"] = max(s_["MEd_x"], z["MEd_x"]); s_["MEd_y"] = max(s_["MEd_y"], z["MEd_y"])
            s_["tillagg"] = max(s_["tillagg"], z["tillagg"], key=lambda t: math.pi * t[0] ** 2 / 4 / t[1])
            break
    else:
        slut.append(z)
for i, z in enumerate(sorted(slut, key=lambda z: (-z["bounds"][3], z["bounds"][0])), 1):
    z["namn"] = f"Ö{i}"
    x0, y0, x1, y1 = z["bounds"]
    z["pelare"] = [f"P{j}" for j, (x, y) in enumerate(GEO["pelare"], 1) if x0 <= x <= x1 and y0 <= y <= y1]
    rx, ry = mrd_ok(arm(z["tillagg"]))
    z["MRd_x"], z["MRd_y"] = rx, ry
    print(f"  {z['namn']}: {x1 - x0:.0f}×{y1 - y0:.0f} mm, MEd {z['MEd_x']/1e3:.1f}/{z['MEd_y']/1e3:.1f}, Ø{z['tillagg'][0]}c{z['tillagg'][1]} MRd {rx/1e3:.1f}/{ry/1e3:.1f}, rör {z['pelare']}")
R["zoner"] = sorted(slut, key=lambda z: z["namn"])


def x_d(As, d):
    """Tryckzonens relativa höjd x/d (rektangulärt spänningsblock), för 5.6.2(2): x_u/d ≤ 0,25."""
    return As * S.fyd / (0.8 * B.fcd) / d


R["xd"] = dict(uk=x_d(arm().ux.As, arm().uy.y), ok=x_d(arm().ox.As, H - arm().oy.y),
               **{f"ok_{t[0]}_{t[1]}": x_d(arm(t).oy.As, H - arm(t).oy.y) for t in TILLAGG})


def zon_vid(x, y):
    for z in R["zoner"]:
        x0, y0, x1, y1 = z["bounds"]
        if x0 <= x <= x1 and y0 <= y <= y1:
            return z
    return None


# ------------------------------------------------------------------ 3. genomstansning vid rören
from tvarkraft import q_vektor, Snitt  # noqa: E402
from matplotlib.path import Path as MplPath  # noqa: E402
from omhyllande import SNO  # noqa: E402
hal = Polygon(GEO["hal"])
platta_utan_hal = Polygon(GEO["kontur"], [GEO["hal"]])
stod_geo = [LineString([(a, c), (b_, c)] if ax == "h" else [(c, a), (c, b_)]) for ax, c, a, b_ in GEO["stod"]]
qv = {}
for nm, (Pp, lf) in {"fjäder": (P1, lf1), "styv": (P2, lf2)}.items():
    qv[nm] = dict(G=q_vektor(Pp, lf["G"].m_nod), S={k: q_vektor(Pp, r.m_nod) for k, r in lf["Sk"].items()},
                  Q=[q_vektor(Pp, r.m_nod) for r in lf["Q"]], P=Pp, monster=lf["monster"])


def _kombinera(aG, aS, aQ, monster):
    """Alla brottgränskombinationer av lastfallens värden (arrayer): ULS × nyttig last i mönster × snö."""
    for (cg, cq, cs) in ULS.values():
        for mask in monster.values():
            q_ = cq * sum(mk * a for mk, a in zip(mask, aQ))
            for sn in SNO:
                yield cg * aG + q_ + cs * sum((aS[k] for k in sn), 0.0 * aG)


def snitt_max(geom, centrum=None):
    """Största tvärkraft genom snittet över alla kombinationer och båda rörstyvheterna."""
    best, L = 0.0, 0.0
    for nm, d_ in qv.items():
        sn = Snitt(d_["P"], geom, centrum=centrum)
        if sn.langd < 1:
            return 0.0, 0.0
        L = sn.langd
        VG = np.array(sn.kraft(d_["G"])); VS = {k: sn.kraft(q) for k, q in d_["S"].items()}
        VQ = [sn.kraft(q) for q in d_["Q"]]
        for V in _kombinera(VG, VS, VQ, d_["monster"]):
            best = max(best, abs(float(V)))
    return best, L


def snitt_lokal(delar, centrum, w):
    """Nettokraft genom ett slutet kontrollsnitt och största tvärkraft per längdenhet, medelvärde över längden w,
    över alla kombinationer och båda rörstyvheterna. delar: snittets delar (LinearRing eller LineString)."""
    Vmax, vmax = 0.0, 0.0
    for nm, d_ in qv.items():
        sn = [Snitt(d_["P"], g, ds=5.0, centrum=centrum) for g in delar]
        proj = lambda q: [np.einsum("ij,ij->i", q[s_.el], s_.n) for s_ in sn]
        aG = proj(d_["G"]); aS = {k: proj(q) for k, q in d_["S"].items()}; aQ = [proj(q) for q in d_["Q"]]
        flat = lambda a: np.concatenate(a)
        ds = flat([s_.ds for s_ in sn])
        delning = np.cumsum([len(s_.ds) for s_ in sn])[:-1]
        sluten = [g.is_ring for g in delar]
        for a in _kombinera(flat(aG), {k: flat(v) for k, v in aS.items()}, [flat(v) for v in aQ], d_["monster"]):
            Vmax = max(Vmax, abs(float((a * ds).sum())))
            for part, ring, s_ in zip(np.split(a, delning), sluten, sn):
                n = max(int(round(w / s_.ds.mean())), 1)
                if len(part) <= n:
                    continue
                pad = np.r_[part[-n:], part, part[:n]] if ring else np.r_[np.full(n, part[0]), part, np.full(n, part[-1])]
                sm_ = np.convolve(pad, np.ones(n) / n, mode="same")[n:-n]
                vmax = max(vmax, float(np.abs(sm_).max()))
    return Vmax, vmax


def kontrollomkrets(x, y, yta, d):
    """Kontrollsnitt 2d från den belastade ytan (röret, eller röret och närliggande stolpar). u1 med avdrag för
    trapphålet enligt 6.4.2(3) (hål inom 6d): delen mellan tangenterna från rörets mitt till hålet räknas bort."""
    per1 = yta.buffer(2 * d, quad_segs=32).exterior
    u1, nara = per1.length, False
    if hal.distance(yta) <= 6 * d:
        nara = True
        vinklar = [math.atan2(py - y, px - x) for px, py in hal.exterior.coords]
        ref = math.atan2(hal.centroid.y - y, hal.centroid.x - x)
        rel = [(v - ref + math.pi) % (2 * math.pi) - math.pi for v in vinklar]
        a0_, a1_ = min(rel) + ref, max(rel) + ref
        kon = Polygon([(x, y)] + [(x + 1e5 * math.cos(a), y + 1e5 * math.sin(a)) for a in np.linspace(a0_, a1_, 60)])
        u1 -= per1.intersection(kon).length
    # snittet där det ligger i plattan (inte i trapphålet) för integrationen
    g = per1.difference(hal) if per1.intersects(hal) else per1
    delar = list(getattr(g, "geoms", [g]))
    return u1, nara, delar


STOLPAR_PL = [p for p in LASTER["punkter"] if p["plats"] == "platta"]
AS = lambda t: 0 if t is None else math.pi * t[0] ** 2 / 4 / t[1]
# tilläggsjärn som läggs oavsett beräkning: rör vid trapphålet och med stolpe snett intill (granskning)
MIN_TILLAGG = {"P7": (10, 150), "P14": (10, 150), "P17": (10, 150)}
nu_ = 0.6 * (1 - B.fck / 250)
VRDMAX = 0.4 * nu_ * B.fcd


def stolpyta(p, a=0.0):
    bx, by = p["yta"]
    cx, cy = p["mitt"]
    return box(cx - bx / 2, cy - by / 2, cx + bx / 2, cy + by / 2).buffer(a, quad_segs=16) if a else \
        box(cx - bx / 2, cy - by / 2, cx + bx / 2, cy + by / 2)


# lastfall per rörstyvhet: nodlaster (nedåt) och rörreaktioner (uppåt), för jämvikt kring ett område
fall_ = {}
for nm, (Pp, lf) in {"fjäder": (P1, lf1), "styv": (P2, lf2)}.items():
    f_ = lf["f"]
    fall_[nm] = dict(P=Pp, monster=lf["monster"],
                     G=(f_["G"][0::3], lf["G"].reaktioner()),
                     S={k: (f_["S_" + k][0::3], lf["Sk"][k].reaktioner()) for k in lf["Sk"]},
                     Q=[(fq[0::3], r.reaktioner()) for fq, r in zip(lf["fQ"], lf["Q"])])


def netto(omr, ror_inne):
    """Största |kraft genom randen av området omr| över alla kombinationer: rörens reaktioner inom området
    minus lasterna inom området (jämvikt). ror_inne: rör vars reaktion ligger inom området."""
    best = 0.0
    for nm, d_ in fall_.items():
        Pp = d_["P"]
        g = omr.buffer(0)
        mask = MplPath(np.asarray(g.exterior.coords)).contains_points(Pp.xy)
        val = lambda fv, R_: sum(R_[n] for n in ror_inne) - float(fv[mask].sum())
        VG = np.array(val(*d_["G"]))
        VS = {k: val(*v) for k, v in d_["S"].items()}
        VQ = [val(*v) for v in d_["Q"]]
        for V in _kombinera(VG, VS, VQ, d_["monster"]):
            best = max(best, abs(float(V)))
    return best


def hal_kon(x, y):
    """Området mellan tangenterna från (x, y) till trapphålet (6.4.2(3))."""
    vinklar = [math.atan2(py - y, px - x) for px, py in hal.exterior.coords]
    ref = math.atan2(hal.centroid.y - y, hal.centroid.x - x)
    rel = [(v - ref + math.pi) % (2 * math.pi) - math.pi for v in vinklar]
    a0_, a1_ = min(rel) + ref, max(rel) + ref
    return Polygon([(x, y)] + [(x + 1e5 * math.cos(v), y + 1e5 * math.sin(v)) for v in np.linspace(a0_, a1_, 60)])


def ror_yta(n, x, y):
    """Rörets belastade yta: topplåten, med effektiv bredd enligt SS-EN 1993-1-8 6.2.5 för en större plåt,
    c = t sqrt(fy / (3 fjd)), fjd = 2 fcd (största värdet, ger minst yta). Returnerar (yta, bredd, plåt)."""
    b, t, fy = TOPPLAT_STOR.get(n, TOPPLAT)
    beff = b if b <= ROR[0] else min(b, ROR[0] + 2 * t * math.sqrt(fy / (3 * 2 * B.fcd)))
    return box(x - beff / 2, y - beff / 2, x + beff / 2, y + beff / 2), beff, (b, t, fy)


def omkrets(x, y, yta, a):
    """Kontrollsnitt på avståndet a från ytan: längd med avdrag för trapphålet (6.4.2(3)), snittets delar i
    plattan (för den lokala tvärkraften) och området innanför (för jämvikten)."""
    omr = yta.buffer(a, quad_segs=32)
    per = omr.exterior
    u, nara = per.length, False
    if hal.distance(yta) <= 6 * (H - C_OK - 10):
        nara = True
        u -= per.intersection(hal_kon(x, y)).length
    g = per.difference(hal) if per.intersects(hal) else per
    return u, nara, list(getattr(g, "geoms", [g])), omr


def stans(cx, cy, yta, V, t, sank=0.0, ror=None, hull=None):
    """Genomstansning enligt 6.4 för lasten V på ytan yta med hela lasten (ingen avlastning av närliggande
    laster). ρ_l och d ur överkantsarmeringen (nät + tillägg t), som ligger sank mm lägre. Snittet ritas för den
    verkliga höjden. ror: rörets namn -> även FE-modellens största lokala tvärkraft längs snittet och, som
    information, nettokraften genom snittet ur jämvikt. hull: röret och stolpar inom 2d tillsammans; då tas
    FE-tvärkraften längs snittet runt dem (rörets eget snitt går genom eller intill stolpens lastyta)."""
    a_ = arm(t, sank=sank)
    d = H - (a_.ox.y + a_.oy.y) / 2
    rho = min(math.sqrt(a_.ox.As / (H - a_.ox.y) * a_.oy.As / (H - a_.oy.y)), 0.02)
    vr = vRdc(rho, d, B)
    u1, nara, delar, omr = omkrets(cx, cy, yta, 2 * d)
    beta = 1.4 if hal.distance(yta) < 2 * d else 1.15
    vEd_f = beta * V / (u1 * d)
    vloc, Vnet = 0.0, None
    if ror:
        delar_fe = delar if hull is None else omkrets(cx, cy, hull, 2 * d)[2]
        _, vloc = snitt_lokal(delar_fe, (cx, cy), d)
        Vnet = netto(omr, [ror])
    vEd = max(vEd_f, vloc / d)
    return dict(d=d, rho=rho, u1=u1, beta=beta, V=V, vEd_f=vEd_f, vEd_fe=vloc / d, vEd=vEd, vRdc=vr, utn=vEd / vr,
                nara=nara, Vnet=Vnet)


TILL_LISTA = [(8, 150), (10, 150), (12, 150), (12, 100)]
FEL = []


def valj(cx, cy, yta, V, bas, ror=None, u0=None, hull=None):
    """Minsta tillägg (i ök) så att utnyttjandet ≤ UTN_MAX och ≤ 1,0 med armeringen SANK mm för lågt."""
    for t in [bas] + TILL_LISTA:
        t = max(bas, t, key=AS) if (bas and t) else (t or bas)
        s_ = stans(cx, cy, yta, V, t, ror=ror, hull=hull)
        s_l = stans(cx, cy, yta, V, t, sank=SANK, ror=ror, hull=hull)
        utn0 = 0.0 if u0 is None else s_["beta"] * V / (u0 * s_["d"]) / VRDMAX
        if s_["utn"] <= UTN_MAX and s_l["utn"] <= 1.0 and utn0 <= 1.0:
            return t, s_, s_l, utn0
    print(f"  !! inget tillägg räcker vid ({cx:.0f}, {cy:.0f}): V {V/1e3:.1f}, utn {s_['utn']:.2f}, −{SANK:.0f} mm "
          f"{s_l['utn']:.2f}, kant {utn0:.2f}, u1 {s_['u1']:.0f}, β {s_['beta']}, vEd β {s_['vEd_f']:.2f} FE {s_['vEd_fe']:.2f}")
    FEL.append((cx, cy))
    return t, s_, s_l, utn0


pel = []
ror_zoner = []
for j, (x, y) in enumerate(GEO["pelare"], 1):
    n = f"P{j}"
    VEd = Rpel[n]
    z = zon_vid(x, y)
    zb = z["tillagg"] if z else None
    bas = zb
    if n in MIN_TILLAGG:
        bas = max(bas, MIN_TILLAGG[n], key=AS) if bas else MIN_TILLAGG[n]
    ror, beff, plat = ror_yta(n, x, y)
    per0 = ror.exterior
    u0 = per0.length - (per0.intersection(hal_kon(x, y)).length if hal.distance(ror) < 2 * H else 0.0)
    d0 = H - C_OK - 10
    inom = [p for p in STOLPAR_PL if ror.distance(stolpyta(p)) < 2 * d0]
    hull = unary_union([ror] + [stolpyta(p) for p in inom]).convex_hull if inom else None
    t, s_, s_l, utn0 = valj(x, y, ror, VEd, bas, ror=n, u0=u0, hull=hull)
    if t != zb:                        # tilläggsjärn vid röret: 1,5 × 1,5 m
        ror_zoner.append(dict(bounds=[x - 750, y - 750, x + 750, y + 750], MEd_x=0.0, MEd_y=0.0, tillagg=t,
                              cx=x, cy=y, pelare=[n], orsak="genomstansning"))
    nara_st = [p["namn"] for p in STOLPAR_PL if ror.distance(stolpyta(p)) < 4 * s_["d"]]
    pk = pelare_knackning(VEd, ROR[0], ROR[1], L_ROR, fy=FY_ROR)
    pel.append(dict(namn=n, x=x, y=y, VEd=VEd, komb=Rkomb[n], VEd_fjader=env1["R"][n], VEd_styv=env2["R"][n], VEd_vagg=env3["R"][n],
                    R_lyft=min(e["R_lyft"][n] for e in envs), tillagg=t, knack=pk["utn"], NbRd=pk["NbRd"],
                    c=beff, plat=plat, u0=u0, gemensam=[p["namn"] for p in inom], utn0=utn0, utn_lag=s_l["utn"], u1_lag=s_l["u1"], stolpar=nara_st, **s_))
    print(f"  {n}: VEd {VEd/1e3:5.1f} (netto {s_['Vnet']/1e3:5.1f}) {nara_st}, u1 {s_['u1']:.0f}{' (hål)' if s_['nara'] else ''},"
          f" β {s_['beta']}, vEd β {s_['vEd_f']:.2f} FE {s_['vEd_fe']:.2f}, vRd,c {s_['vRdc']:.2f} -> {s_['utn']*100:.0f} %"
          f" (−{SANK:.0f} mm: u1 {s_l['u1']:.0f}, {s_l['utn']*100:.0f} %){(' + Ø%dc%d' % t) if t else ''}, kant {utn0*100:.0f} %")
for rz in ror_zoner:
    R["zoner"].append(rz)
# kontroll av jämvikten: nettokraft mot tvärkraft integrerad ur FE längs det slutna snittet (rör utan hål)
kvot = []
for p in pel:
    if not p["nara"] and not p["gemensam"]:      # snittet ska inte gå genom en stolpes lastyta
        per = box(p["x"] - 40, p["y"] - 40, p["x"] + 40, p["y"] + 40).buffer(2 * p["d"], quad_segs=32).exterior
        kvot.append(snitt_lokal([per], (p["x"], p["y"]), p["d"])[0] / p["Vnet"])
R["kontroll_netto"] = dict(min=min(kvot), max=max(kvot))
print(f"  integrerad / jämvikt: {min(kvot):.3f}–{max(kvot):.3f}")

# ------------------------------------------------------------------ 4. stolpar som står på plattan
stolp = []
for st in LASTER["punkter"]:
    nm = st["namn"]
    Rd = st["Rd"] * 1e3
    if st["plats"] != "platta":
        stolp.append(dict(namn=nm, fall="på vägg" if st["plats"] == "vägg" else "på mark", Rd=Rd)); continue
    cx, cy = st["mitt"]
    z = zon_vid(cx, cy)
    zb = z["tillagg"] if z else None
    t, s_, s_l, _ = valj(cx, cy, stolpyta(st), Rd, zb)
    if t != zb:
        R["zoner"].append(dict(bounds=[cx - 750, cy - 750, cx + 750, cy + 750], MEd_x=0.0, MEd_y=0.0, tillagg=t,
                               cx=cx, cy=cy, pelare=[], orsak=f"genomstansning, {nm}"))
    ror_n = [f"P{j}" for j, (x, y) in enumerate(GEO["pelare"], 1)
             if box(x - 40, y - 40, x + 40, y + 40).distance(stolpyta(st)) < 4 * s_["d"]]
    stolp.append(dict(namn=nm, fall="på plattan", Rd=Rd, yta=st["yta"], tillagg=t, ror=ror_n, utn_lag=s_l["utn"],
                      VRd=s_["vRdc"] * s_["u1"] * s_["d"] / s_["beta"], **s_))
    print(f"  {nm}: Rd {Rd/1e3:.1f} kN, yta {st['yta']}, u1 {s_['u1']:.0f}{' (hål)' if s_['nara'] else ''}, β {s_['beta']},"
          f" -> {s_['utn']*100:.0f} % (−{SANK:.0f} mm {s_l['utn']*100:.0f} %){(' + Ø%dc%d' % t) if t else ''}, rör {ror_n}")
R["stolpar"] = stolp

# stolpe B (LD4_1) på fotplåt: excentrisk last, ekvivalent tryckyta (L − 2e) × B, lokalt tryck 6.7, plåttjocklek
from laster import STOLPE_B, HAVARM_B  # noqa: E402
sB = next(p for p in LASTER["punkter"] if p["namn"] == "LD4_1")
LB, BB_ = sB["yta"]
eB = sB["e"]
b1, d1 = LB - 2 * eB, BB_
Ac0 = b1 * d1
b2, d2 = min(3 * b1, b1 + H), min(3 * d1, d1 + H)
kf = min(math.sqrt(b2 * d2 / Ac0), 3.0)
sig = sB["Rd"] * 1e3 / Ac0
utsprang = (LB - STOLPE_B[0]) / 2
t_fot = math.sqrt(4 * sig * utsprang ** 2 / 2 / 355.0)
R["stolpe_B"] = dict(N=sB["Rd"] * 1e3, M=sB["M_d"], e=eB, L=LB, B=BB_, b1=b1, Ac0=Ac0, kf=kf, sigma=sig, stolpe=STOLPE_B[0], havarm=HAVARM_B,
                     FRdu=Ac0 * B.fcd * kf, utn=sB["Rd"] * 1e3 / (Ac0 * B.fcd * kf), t_min=t_fot, t=15.0,
                     Wd=sB["Wd"])
print(f"stolpe B: e {eB:.0f} mm, M {sB['M_d']:.2f} kNm, σ {sig:.2f} MPa, 6.7 {R['stolpe_B']['utn']*100:.0f} %, fotplåt t ≥ {t_fot:.1f} mm")
# lägg till rörzonerna bland överkantszonerna
# zoner som ligger helt inom en annan zon med minst lika mycket armering behövs inte
R["zoner"] = [z for z in R["zoner"] if not any(
    o is not z and box(*o["bounds"]).buffer(1).contains(box(*z["bounds"])) and AS(o["tillagg"]) >= AS(z["tillagg"])
    for o in R["zoner"])]
R["zoner"].sort(key=lambda z: (-round(z["bounds"][3], -2), z["bounds"][0]))
for i, z in enumerate(R["zoner"], 1):
    z.setdefault("orsak", "böjning")
    z["namn"] = f"Ö{i}"
    x0, y0, x1, y1 = z["bounds"]
    z["pelare"] = [f"P{j}" for j, (x, y) in enumerate(GEO["pelare"], 1) if x0 <= x <= x1 and y0 <= y <= y1]
    z["MRd_x"], z["MRd_y"] = mrd_ok(arm(z["tillagg"]))
# lokalt tryck under röret (6.7): topplåt 80×80 ger lastyta A_c0 = 80², spridning högst 150 mm (plattans
# tjocklek), högst 3 × 80 och högst till trapphålet
for p in pel:
    b1 = float(p["c"])
    dh = hal.distance(box(p["x"] - b1 / 2, p["y"] - b1 / 2, p["x"] + b1 / 2, p["y"] + b1 / 2))
    b2 = min(b1 + H, 3 * b1, b1 + 2 * dh)
    FRdu = b1 ** 2 * B.fcd * min(b2 / b1, 3.0)
    # topplåt: kvadratisk fritt upplagd platta, spännvidd = rörets innermått, brottlinjeteori m_p = q a² / 24
    a_in = ROR[0] - 2 * ROR[1]
    q = p["VEd"] / b1 ** 2
    t_topp = math.sqrt(4 * q * a_in ** 2 / 24 / FY_ROR) if p["plat"] == TOPPLAT else 0.0
    p.update(FRdu=FRdu, utn_lokal=p["VEd"] / FRdu, b2=b2, t_topp=t_topp)
R["lokal"] = dict(utn=max(p["utn_lokal"] for p in pel), namn=max(pel, key=lambda p: p["utn_lokal"])["namn"],
                  t_topp=max(p["t_topp"] for p in pel))
print(f"lokalt tryck: {R['lokal']['utn']*100:.0f} % ({R['lokal']['namn']}), topplåt t ≥ {R['lokal']['t_topp']:.1f} mm")
R["pelare"] = pel
R["ror"] = dict(NbRd=pelare_knackning(1, ROR[0], ROR[1], L_ROR, fy=FY_ROR)["NbRd"],
                lam=pelare_knackning(1, ROR[0], ROR[1], L_ROR, fy=FY_ROR)["lam"],
                chi=pelare_knackning(1, ROR[0], ROR[1], L_ROR, fy=FY_ROR)["chi"])


# ------------------------------------------------------------------ 5. tvärkraft vid väggar och väggändar
d_v = H - arm().oy.y
stodlinjer = unary_union(stod_geo)
# (a) väggändar: sista 0,5 m av upplagslinjen som belastad yta, kontrollsnitt 2d utanför
andar = []
for k, L in enumerate(stod_geo):
    for slut_ in (0, 1):
        E = np.array(L.coords[slut_]); A = np.array(L.coords[1 - slut_])
        t = (A - E) / np.linalg.norm(A - E)
        seg = LineString([E, E + t * min(500.0, L.length)])
        yta = seg.buffer(75, cap_style="flat")
        per = yta.buffer(2 * d_v, quad_segs=24).exterior
        # bort: där snittet korsar resten av väggen eller andra väggar, och utanför plattan
        rest = [LineString([E + t * 500.0, A])] if L.length > 500 else []
        bort = unary_union([g.buffer(75 + 2 * d_v - 1, cap_style="flat") for g in rest] +
                           [o.buffer(75, cap_style="flat") for kk, o in enumerate(stod_geo) if kk != k])
        snittg = per.difference(bort).intersection(platta_utan_hal)
        if snittg.is_empty or snittg.length < 50:
            continue
        cx, cy = seg.interpolate(0.5, normalized=True).coords[0]
        V, u = snitt_max(snittg, centrum=(cx, cy))
        z = zon_vid(*E)
        a = arm(z["tillagg"]) if z else arm()
        dd = H - (a.ox.y + a.oy.y) / 2
        rho = min(math.sqrt(a.ox.As / (H - a.ox.y) * a.oy.As / (H - a.oy.y)), 0.02)
        vEd = 1.15 * V / (u * dd)
        vr = vRdc(rho, dd, B)
        andar.append(dict(vagg=k + 1, x=float(E[0]), y=float(E[1]), V=V, u=u, d=dd, vEd=vEd, vRdc=vr, utn=vEd / vr))
andar.sort(key=lambda r: -r["utn"])
for r in andar[:6]:
    print(f"  väggände V{r['vagg']} ({r['x']:.0f}, {r['y']:.0f}): V {r['V']/1e3:.1f} kN, u {r['u']:.0f}, vEd {r['vEd']:.2f} vRd,c {r['vRdc']:.2f} -> {r['utn']*100:.0f} %")
# (b) längs väggarna: snitt parallellt med upplagslinjen, d från väggens insida, i bitar om 1 m
langs = []
for k, L in enumerate(stod_geo):
    if L.length < 1500:
        continue
    for sida in (1, -1):
        off = L.parallel_offset(75 + d_v, "left" if sida > 0 else "right")
        inre = off.interpolate(500).coords[0], off.interpolate(off.length - 500).coords[0]
        mid = LineString(inre)
        n = max(int(mid.length // 1000), 1)
        for i_ in range(n):
            bit = LineString([mid.interpolate(i_ / n, normalized=True), mid.interpolate((i_ + 1) / n, normalized=True)])
            bit = bit.intersection(platta_utan_hal)
            if bit.is_empty or bit.length < 300:
                continue
            V, u = snitt_max(bit, centrum=L.interpolate(L.project(bit.centroid)).coords[0])
            langs.append(dict(vagg=k + 1, v=V / u, x=bit.centroid.x, y=bit.centroid.y))
vmaxl = max(langs, key=lambda r: r["v"])
vrd_l = vmin(d_v, B) * d_v
print(f"  längs väggar: max {vmaxl['v']:.1f} N/mm vid V{vmaxl['vagg']} ({vmaxl['x']:.0f}, {vmaxl['y']:.0f}), vRd {vrd_l:.1f} N/mm")
R["tvarkraft"] = dict(andar=andar, langs=dict(vEd=vmaxl["v"], vRd=vrd_l, utn=vmaxl["v"] / vrd_l, x=vmaxl["x"],
                                              y=vmaxl["y"], vagg=vmaxl["vagg"]), d=d_v)

# ------------------------------------------------------------------ 6. nedböjning
print("nedböjning ...")
phi = B.kryptal(H)
ecs = B.krympning(H)


def arm_fn(x, y):
    z = zon_vid(x, y)
    return arm(z["tillagg"]) if z else arm()


def f_kvasi(f):
    """Kvasipermanent last: G + lätta väggar (som permanent, på säker sida) + ψ2 Q + ψ2 S."""
    return f["G"] + f["V"] + PSI2_Q * (f["Q"] + f["QT"]) + PSI2_S * f["S"]


def f_kar(f):
    return f["G"] + f["V"] + f["Q"] + f["QT"] + f["S"]


Pn, fn = bygg(k_ror=None)
rn = nedbojning(Pn, f_kvasi(fn), arm(), B, S, phi, ecs, arm_fn=arm_fn)
Pc, fc = bygg(k_ror=None)
rc = nedbojning(Pc, f_kar(fc), arm(), B, S, 3.0, 0.0, fullt_sprucken=True, arm_fn=arm_fn)
Pk, fk = bygg(k_ror=None)
rk = nedbojning(Pk, f_kvasi(fk), arm(), B, S, 0.0, 0.0, arm_fn=arm_fn)   # korttid utan krympning, för jämförelse
# lokal spännvidd: avstånd mellan stöd i x- och y-led genom punkten
stodgeo = unary_union([stodlinjer.buffer(1)] + [box(x - PLAT / 2, y - PLAT / 2, x + PLAT / 2, y + PLAT / 2)
                                                 for x, y in GEO["pelare"]] + [Polygon(GEO["mark"])])
platta = Polygon(GEO["kontur"], [GEO["hal"]])


def spann(x, y):
    Ls = []
    for dx, dy in ((1, 0), (0, 1)):
        sida = []
        for sgn in (1, -1):
            ray = LineString([(x, y), (x + sgn * dx * 30000, y + sgn * dy * 30000)])
            inne = ray.intersection(platta.buffer(1))
            seg = min(inne.geoms, key=lambda g: g.distance(Point(x, y))) if hasattr(inne, "geoms") else inne
            hit = seg.intersection(stodgeo)
            sida.append(Point(x, y).distance(hit) if not hit.is_empty else None)
        if all(s_ is not None for s_ in sida):
            Ls.append(sum(sida))
        elif any(s_ is not None for s_ in sida):
            Ls.append(None)
    Lok = [L for L in Ls if L]
    return min(Lok) if Lok else None


from matplotlib.path import Path as _MP  # noqa: E402
ej_mark = ~_MP(np.asarray(GEO["mark"], float)).contains_points(Pn.xy, radius=1.0)


def utnyttj_nedb(res):
    w = np.where(ej_mark, res.w, -1e9)       # plattan på mark ingår inte (sättning i cellplasten, K-06)
    kand = np.argsort(-w)[:400]
    best = (0, None)
    for i in kand:
        L = spann(*res.P.xy[i])
        if L:
            u = w[i] / (L / 250)
            if u > best[0]:
                best = (u, dict(w=float(w[i]), L=L, x=float(res.P.xy[i, 0]), y=float(res.P.xy[i, 1])))
    return best


u_ec2, p_ec2 = utnyttj_nedb(rn)
u_spr, p_spr = utnyttj_nedb(rc)
R["nedbojning"] = dict(phi=phi, ecs=ecs, Eeff=B.Ecm / (1 + phi), wmax=float(rn.w[ej_mark].max()),
                       wmax_spr=float(rc.w[ej_mark].max()), wmax_kort=float(rk.w[ej_mark].max()),
                       wmark_spr=float(rc.w[~ej_mark].max()), ec2=dict(utn=u_ec2, **p_ec2), sprucken=dict(utn=u_spr, **p_spr),
                       iter=rn.iter)
np.savez("nedb.npz", xy=Pn.xy, tri=Pn.tri, w=rn.w, w_spr=rc.w, ej_mark=ej_mark)
print(f"  EC2: wmax {rn.w.max():.1f} mm; största w/(L/250) {u_ec2*100:.0f} % (w {p_ec2['w']:.1f}, L {p_ec2['L']:.0f}); helt sprucken {rc.w.max():.1f} mm, {u_spr*100:.0f} %")

# ------------------------------------------------------------------ 7. sprickbredd (kvasipermanent)
Pq, fq = bygg(k_ror=None)
rq = Pq.los(f_kvasi(fq))
from platta import wood_armer
wa = wood_armer(*rq.m_nod.T)
sq = {"ux": wa[0], "uy": wa[1], "ox": wa[2], "oy": wa[3]}     # utan utjämning (bruksgräns)
Mu = max(sq["ux"].max(), sq["uy"].max())
sp_u = sprickbredd(Mu, H, a0.ux.As, a0.uy.y, C_UK, 10, B, S)
# överkant: i zoner med tilläggsjärn och utanför
oz = np.array([zon_vid(*p) is not None for p in Pq.xy])
Mo_utan = max(-sq["ox"][~oz].min(), -sq["oy"][~oz].min())
Mo_med = max(-sq["ox"][oz].min(), -sq["oy"][oz].min()) if oz.any() else 0
sp_o_utan = sprickbredd(Mo_utan, H, a0.oy.As, H - a0.oy.y, C_OK, NAT_OK[0], B, S)
tmax = max((z["tillagg"] for z in R["zoner"]), key=lambda t: t[0], default=None)
ae = arm(tmax) if tmax else a0
sp_o_med = sprickbredd(Mo_med, H, ae.oy.As, H - ae.oy.y, C_OK, tmax[0] if tmax else NAT_OK[0], B, S)
R["spricka"] = dict(uk=dict(M=Mu, **sp_u), ok_nat=dict(M=Mo_utan, **sp_o_utan), ok_tillagg=dict(M=Mo_med, **sp_o_med))
print(f"sprickbredd: uk {sp_u['wk']:.2f} (M {Mu/1e3:.1f}), ök nät {sp_o_utan['wk']:.2f} (M {Mo_utan/1e3:.1f}), ök tillägg {sp_o_med['wk']:.2f} (M {Mo_med/1e3:.1f})")

# ------------------------------------------------------------------ 8. minimiarmering, avstånd
R["minarm"] = dict(uk=As_min(a0.uy.y, H, B, S) * 1e3, ok=As_min(H - a0.oy.y, H, B, S) * 1e3,
                   uk_har=a0.ux.As * 1e3, ok_har=a0.ox.As * 1e3)
R["jamvikt"] = {k: float(v[0::3].sum() / 1e3) for k, v in fn.items()}

# ------------------------------------------------------------------ 9. vindlyft
lyft_s = {k: min(utjamna_linje(lf["G"], e["lyft"][k], k[-1], BAND).min() for e, lf in ((env1, lf1), (env2, lf2)))
          for k in ("mox", "moy")}
R["lyft"] = dict(mox=-lyft_s["mox"], moy=-lyft_s["moy"],
                 Rmin=min(p["R_lyft"] for p in pel), Rmin_namn=min(pel, key=lambda p: p["R_lyft"])["namn"])
print(f"vindlyft: ök {R['lyft']['mox']/1e3:.1f}/{R['lyft']['moy']/1e3:.1f} kNm/m, minsta rörlast {R['lyft']['Rmin']/1e3:.1f} kN ({R['lyft']['Rmin_namn']})")
# Rören är inte förankrade i plattan: ett rör som får drag lyfter. Räkna om lyftfallet utan de rören.
utan = []
while True:
    Pu, fu = bygg(k_ror=1e9, utan=utan)          # styva rör ger störst drag
    ru = Pu.los(fu["Gp"] + fu["W"])
    Ru = ru.reaktioner()
    neg = [n for n, v in Ru.items() if n[0] == "P" and v < 0]
    if not neg:
        break
    utan += neg
if utan:
    from platta import wood_armer
    wa = wood_armer(*ru.m_nod.T)
    ox_u = utjamna_linje(ru, wa[2], "x", BAND); oy_u = utjamna_linje(ru, wa[3], "y", BAND)
    ux_u = utjamna_linje(ru, wa[0], "x", BAND); uy_u = utjamna_linje(ru, wa[1], "y", BAND)
    R["lyft"].update(utan=utan, mox_u=-ox_u.min(), moy_u=-oy_u.min(), mux_u=ux_u.max(), muy_u=uy_u.max(),
                     Rmin_u=min(v for n, v in Ru.items() if n[0] == "P"), w_upp=float(-ru.w.min()))
    print(f"  utan {utan}: ök {-ox_u.min()/1e3:.1f}/{-oy_u.min()/1e3:.1f}, uk {ux_u.max()/1e3:.1f}/{uy_u.max()/1e3:.1f} kNm/m,"
          f" lyft {-ru.w.min():.2f} mm")

# ------------------------------------------------------------------ 10. reaktioner på Lecaväggarna
vagg_r = []
for nm, (Pp, lf) in {"fjäder": (P1, lf1), "styv": (P2, lf2)}.items():
    sedd = set()
    for s_ in Pp.stod:
        nod = [n for n in s_["noder"] if n not in sedd]
        sedd.update(nod)
        if s_["typ"] != "linje":
            continue
        nod = np.array(nod)
        L = LineString(s_["geo"])
        sp = np.array([L.project(Point(Pp.xy[n])) for n in nod]); o = np.argsort(sp); sp, nod = sp[o], nod[o]
        RG = lf["G"].R[3 * nod]; RS = lf["S"].R[3 * nod]; RQ = sum(r.R[3 * nod] for r in lf["Q"])
        best = 0.0
        RSk = {k: r.R[3 * nod] for k, r in lf["Sk"].items()}
        Lw = min(1000.0, L.length)
        fon = [(sp >= sp[i]) & (sp <= sp[i] + Lw) for i in range(len(sp))]   # fönster om 1 m
        for cg, cq, cs in ULS.values():
            for sn in SNO:
                Rn = cg * RG + cq * RQ + cs * sum((RSk[k] for k in sn), 0.0 * RG)
                best = max(best, max(Rn[m].sum() / Lw for m in fon))
        vagg_r.append(dict(namn=s_["namn"], fall=nm, L=L.length, Gk=RG.sum() / 1e3, Qk=RQ.sum() / 1e3, Sk=RS.sum() / 1e3,
                           qd_max=best, ovan_G=float(Pp.ovan[s_["namn"]][0]), ovan_S=float(Pp.ovan[s_["namn"]][1])))
vr = []
for n in sorted({v["namn"] for v in vagg_r}, key=lambda t: int(t[1:])):
    a, b_ = [v for v in vagg_r if v["namn"] == n]
    d_ = {k: (max(a[k], b_[k]) if isinstance(a[k], float) else a[k]) for k in a if k != "fall"}
    vr.append(d_)
geo_v = {f"V{i + 1}": w for i, w in enumerate(GEO["vagg"])}
for v in vr:
    w = geo_v[v["namn"]]
    v["vagg"] = dict(ax=w[0], c=w[1], a=w[2], b=w[3], typ=w[4])
R["vaggar"] = vr
for v in vr:
    print(f"  {v['namn']:4s} L {v['L']:6.0f}  Gk {v['Gk']:6.1f} Qk {v['Qk']:6.1f} Sk {v['Sk']:6.1f} kN, varav ovan {v['ovan_G']:.1f}/{v['ovan_S']:.1f}, max {v['qd_max']:.1f} kN/m")

# ------------------------------------------------------------------ 11. handberäkning och SINTEF
import kontroll  # noqa: E402
R["kontroll"] = kontroll.kor(R, P1, lf1, sm, env, GEO, arm, B, S)
json.dump(R, open("resultat.json", "w"), indent=1, ensure_ascii=False, default=float)
print("klart", "FEL:" if FEL else "", FEL)
