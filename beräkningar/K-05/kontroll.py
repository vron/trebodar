"""
Kontroll av FE-resultaten med handberäkning och mot SINTEF Byggforsk 522.871 tabell 24a.

Handberäkning: rörlaster ur belastningsytor (varje punkt på plattan bärs av närmaste stöd: rör, upplagslinje
eller plattan på mark), fältmoment och stödmoment ur strimlor, nedböjning för en helt sprucken strimla.
SINTEF: samma platta som i tabell 24a (150 mm, 3,0 m, Ø8 s200, B30) räknas med rapportens två metoder för nedböjning.
"""
import math

import numpy as np
from shapely.geometry import LineString, Polygon
from matplotlib.path import Path as MplPath

from ec2 import Betong, Stal, styvhet_effektiv, tvarsnitt
import laster as LA
from omhyllande import ULS

QD_G = LA.G_BETONG + LA.G_GOLV            # kN/m²
QD_Q = LA.Q_NYTTIG + LA.Q_VAGG


def belastningsytor(GEO, steg=50.0):
    """Närmaste stöd för varje punkt i ett rutnät över plattan. Returnerar punkter, ruta och index."""
    platta = MplPath(np.asarray(GEO["kontur"], float))
    hal = MplPath(np.asarray(GEO["hal"], float))
    mark = MplPath(np.asarray(GEO["mark"], float))
    x = np.arange(steg / 2, 13810, steg); y = np.arange(steg / 2, 15900, steg)
    X, Y = np.meshgrid(x, y); pts = np.c_[X.ravel(), Y.ravel()]
    ok = platta.contains_points(pts) & ~hal.contains_points(pts)
    pts = pts[ok]
    pel = np.array(GEO["pelare"], float)
    d = np.hypot(pts[:, None, 0] - pel[None, :, 0], pts[:, None, 1] - pel[None, :, 1])
    dl = []
    for ax, c, a, b in GEO["stod"]:
        if ax == "h":
            dx = np.clip(pts[:, 0], a, b) - pts[:, 0]; dy = c - pts[:, 1]
        else:
            dx = c - pts[:, 0]; dy = np.clip(pts[:, 1], a, b) - pts[:, 1]
        dl.append(np.hypot(dx, dy))
    D = np.c_[d, np.array(dl).T]
    idx = np.argmin(D, axis=1)                   # 0..18 rör, 19.. väggar
    idx[mark.contains_points(pts)] = -1          # på mark
    return pts, steg, idx


def laster_som_punkter():
    """Alla laster från plan 1 som punkter (x, y, Gk, Sk, Qk) i kN, linjelaster i bitar om 50 mm."""
    A = LA.alla()
    out = [(p["x"], p["y"], p["Gk"], p["Sk"], 0.0, p["plats"]) for p in A["punkter"]]
    for w in A["vaggar"]:
        out += [(s["x"], s["y"], s["G"], s["S"], 0.0, s["plats"]) for s in w["prov"]]
    for l in A["linjer"]:
        L = LineString(l["pl"]); n = max(int(L.length / 50), 1)
        for i in range(n):
            p = L.interpolate((i + 0.5) / n, normalized=True)
            out.append((p.x, p.y, l["gk"] * L.length / n / 1e3, l["sk"] * L.length / n / 1e3,
                        l["qk"] * L.length / n / 1e3, "platta"))
    return out


def w_strimla(L, h, lager, q, b, s, phi, ecs, full=False, beta=0.5):
    """Nedböjning i mitten av en fritt upplagd strimla [mm] (q i N/mm per mm bredd), krökning enligt 7.4.3."""
    xs = np.linspace(0, L, 401); M = q * xs * (L - xs) / 2
    k = []
    for m in M:
        EI, kc, _ = styvhet_effektiv(1e12 if full else m, h, lager, b, s, phi, ecs, 0 if full else beta)
        k.append(m / EI + kc)
    return float(np.trapezoid(np.array(k) * np.where(xs <= L / 2, xs / 2, (L - xs) / 2), xs))


def kor(R, P, lf, sm, env, GEO, arm, B, S):
    out = {}
    # ---------------- rörlaster
    pts, steg, idx = belastningsytor(GEO)
    lp = laster_som_punkter()
    lpts = np.array([(a[0], a[1]) for a in lp])
    pel = np.array(GEO["pelare"], float)
    # varje last till samma stöd som närmaste rutnätspunkt (laster över väggar går till väggen)
    from scipy.spatial import cKDTree
    tr = cKDTree(pts)
    _, j = tr.query(lpts)
    lidx = idx[j]
    for k, a in enumerate(lp):
        if a[5] == "vägg":
            lidx[k] = -2
    rader = []
    top = sorted(R["pelare"], key=lambda p: -p["VEd"])[:3]
    for p in top:
        i = int(p["namn"][1:]) - 1
        A = (idx == i).sum() * steg ** 2 / 1e6
        g = sum(a[2] for a, li in zip(lp, lidx) if li == i)
        sk = sum(a[3] for a, li in zip(lp, lidx) if li == i)
        qk = sum(a[4] for a, li in zip(lp, lidx) if li == i)
        pk = LA.alla()["punkter"]
        namn = [q["namn"] for k, q in enumerate(pk) if lidx[k] == i]
        Rd = max(cg * (QD_G * A + g) + cq * (QD_Q * A + qk) + cs * sk for cg, cq, cs in ULS.values())
        rader.append(dict(namn=p["namn"], A=A, Gk_ovan=g, Sk_ovan=sk, Qk_ovan=qk, stolpar=namn,
                          Rd=Rd, FE=p["VEd"] / 1e3))
    out["ror"] = rader
    # ---------------- moment i strimlor (6.10b med nyttig last som huvudlast)
    qd = max(cg * QD_G + cq * QD_Q for cg, cq, cs in ULS.values())     # kN/m²
    L = 2.5
    out["qd"] = qd
    out["L"] = L
    out["M_falt"] = qd * L ** 2 / 8
    out["M_stod"] = 1.3 * qd * L ** 2 / 8
    # FE: största utjämnade fältmoment minst 1 m från punktlaster på plattan och 0,5 m från rör
    xy = P.xy
    pl = np.array([(a["x"], a["y"]) for a in LA.alla()["punkter"] if a["plats"] == "platta"])
    dpl = np.min(np.hypot(xy[:, None, 0] - pl[None, :, 0], xy[:, None, 1] - pl[None, :, 1]), axis=1)
    dpe = np.min(np.hypot(xy[:, None, 0] - pel[None, :, 0], xy[:, None, 1] - pel[None, :, 1]), axis=1)
    mark = MplPath(np.asarray(GEO["mark"], float)).contains_points(xy)
    falt = (dpl > 1000) & (dpe > 500) & ~mark
    out["FE_falt"] = float(np.maximum(sm["mux"], sm["muy"])[falt].max() / 1e3)
    # FE: stödmoment över inre rör (minst 1 m från väggar och hålet), största inom 0,3 m från röret
    stod = [LineString([(a, c), (b, c)] if ax == "h" else [(c, a), (c, b)]) for ax, c, a, b in GEO["stod"]]
    hal = Polygon(GEO["hal"])
    from shapely.geometry import Point
    inre = [k for k, (x, y) in enumerate(GEO["pelare"]) if min(s.distance(Point(x, y)) for s in stod) > 1000
            and hal.distance(Point(x, y)) > 1000]
    ok_m = np.maximum(-sm["mox"], -sm["moy"])
    vals = [float(ok_m[np.hypot(xy[:, 0] - pel[k, 0], xy[:, 1] - pel[k, 1]) < 300].max() / 1e3) for k in inre]
    out["FE_stod"] = (min(vals), max(vals))
    out["FE_stod_namn"] = [f"P{k + 1}" for _, k in sorted(zip(vals, inre), reverse=True)[:3]]
    out["inre"] = [f"P{k + 1}" for k in inre]
    # ---------------- nedböjning, helt sprucken strimla
    a = arm()
    qk = QD_G + LA.Q_VAGG + LA.Q_NYTTIG
    Eeff = B.Ecm / 4
    ae = S.Es / Eeff
    t = tvarsnitt(150.0, [(a.ux.As, a.ux.y)], ae, "u")
    EI2 = Eeff * t["I2"]                              # Nmm²/mm
    out["EI2"] = EI2 * 1e3 / 1e12                     # MNm²/m
    out["w_strimla"] = 5 * qk * 1e-3 * (L * 1000) ** 4 / (384 * EI2)
    out["qk"] = qk
    out["w_FE"] = R["nedbojning"]["wmax_spr"]
    # ---------------- SINTEF 522.871 tabell 24a: 150 mm, 3,0 m, Ø8 s200, B30 (C30/37), täckskikt 25, XC1
    b30 = Betong(fck=30)
    As = math.pi * 8 ** 2 / 4 / 200
    lag = [(As, 150 - 25 - 4)]
    g = 3.75 + 0.7
    qp, qkar = (g + 0.3 * 2.0) / 1000, (g + 2.0) / 1000
    w1 = w_strimla(3000, 150, lag, qp, b30, S, b30.kryptal(150), b30.krympning(150))
    w2 = w_strimla(3000, 150, lag, qkar, b30, S, 3.0, 0.0, full=True)
    out["sintef"] = dict(w_ec2=w1, w_kons=w2, lim=3000 / 250, utn_ec2=w1 / 12, utn_kons=w2 / 12)
    print(f"handberäkning: {[(r['namn'], round(r['Rd'], 1), round(r['FE'], 1)) for r in rader]}")
    print(f"  fält {out['M_falt']:.1f} (FE {out['FE_falt']:.1f}), stöd {out['M_stod']:.1f} (FE {out['FE_stod']}), "
          f"w strimla {out['w_strimla']:.1f} (FE {out['w_FE']:.1f}); SINTEF EC2 {w1:.1f} mm, försiktig {w2:.1f} mm")
    return out
