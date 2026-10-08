"""
Omhyllande snittkrafter i brottgränstillstånd för mellanbjälklaget.

Lastfall: G (egentyngd, golv, väggar och stolpar på plan 1, qD2, trappan), Q per fält (nyttig last 2,0 och lätta
väggar 0,7 kN/m² samt trappans nyttiga last, i mönster), S snö via stolpar, väggar och qD2. Kombinationer enligt EKS
(6.10a, 6.10b med Q respektive S som huvudlast), nyttig last på hela plattan, i schackmönster eller i rader, och
snö med eller utan. Dessutom vindlyft: 1,0 × plattans egentyngd och golv + K-01:s R_min (dimensionerande). Rören
räknas både med sin verkliga axialstyvhet och som styva; båda fallen ingår i omhyllningen.
"""
import itertools
import numpy as np
from scipy.spatial import cKDTree

from modell import bygg, QK, QV, G as GEO
from laster import KROPPAR
from shapely.geometry import Point, Polygon
from matplotlib.path import Path as MplPath
from platta import wood_armer

GD = 0.91
ULS = {
    "6.10a": (GD * 1.35, GD * 1.5 * 0.7, GD * 1.5 * 0.6),
    "6.10b Q": (GD * 1.2, GD * 1.5, GD * 1.5 * 0.6),
    "6.10b S": (GD * 1.2, GD * 1.5 * 0.7, GD * 1.5),
}
# snö: på alla huskroppar, på en eller två av dem, eller ingen (ojämn snö mellan huskropparna)
SNO = [c for r in range(len(KROPPAR) + 1) for c in itertools.combinations(KROPPAR, r)]
NX, NY = 5, 5          # fält för nyttig last (cirka 2,8 × 3,2 m)


def falt():
    x = np.linspace(0, 13810, NX + 1); y = np.linspace(0, 15900, NY + 1)
    celler = [(i, j) for i in range(NX) for j in range(NY)]
    polys = [[(x[i], y[j]), (x[i + 1], y[j]), (x[i + 1], y[j + 1]), (x[i], y[j + 1])] for i, j in celler]
    monster = {"hela": [1] * len(celler), "inget": [0] * len(celler),
               "schack A": [(i + j) % 2 for i, j in celler], "schack B": [(i + j + 1) % 2 for i, j in celler],
               "rader x A": [i % 2 for i, j in celler], "rader x B": [(i + 1) % 2 for i, j in celler],
               "rader y A": [j % 2 for i, j in celler], "rader y B": [(j + 1) % 2 for i, j in celler]}
    return polys, monster


def skjuv(P, m_nod):
    """Tvärkraft per element ur momentfältets gradient: qx = ∂mx/∂x + ∂mxy/∂y, qy = ∂mxy/∂x + ∂my/∂y [N/mm]."""
    xy = P.xy[P.tri]                                   # (ne, 3, 2)
    b = np.stack([xy[:, 1, 1] - xy[:, 2, 1], xy[:, 2, 1] - xy[:, 0, 1], xy[:, 0, 1] - xy[:, 1, 1]], 1)
    c = np.stack([xy[:, 2, 0] - xy[:, 1, 0], xy[:, 0, 0] - xy[:, 2, 0], xy[:, 1, 0] - xy[:, 0, 0]], 1)
    A2 = (b * xy[:, :, 0]).sum(1)[:, None]
    me = m_nod[P.tri]                                  # (ne, 3 noder, 3 komp)
    dx = (b[:, :, None] * me).sum(1) / A2
    dy = (c[:, :, None] * me).sum(1) / A2
    qx = dx[:, 0] + dy[:, 2]
    qy = dx[:, 2] + dy[:, 1]
    return np.hypot(qx, qy)


def utjamna_linje(res, falt_, riktning, B=500.0, n=21):
    """Medelvärde över bredden B tvärs momentets riktning (9.4.1(2)): för mx längs y, för my längs x."""
    from matplotlib.tri import LinearTriInterpolator
    ip = LinearTriInterpolator(res._tri, falt_)
    P = res.P
    t = np.linspace(-B / 2, B / 2, n)
    acc = np.zeros(P.nn); cnt = np.zeros(P.nn)
    for dt in t:
        x = P.xy[:, 0] + (dt if riktning == "y" else 0)
        y = P.xy[:, 1] + (dt if riktning == "x" else 0)
        v = np.ma.filled(ip(x, y), np.nan)
        ok = ~np.isnan(v)
        acc[ok] += v[ok]; cnt[ok] += 1
    return acc / np.maximum(cnt, 1)


def utjamna(P, falt_, R=375.0):
    """Medelvärde av ett nodfält inom radien R (areaviktat), för momenttoppar vid rör och väggändar."""
    an = np.zeros(P.nn)
    for k in range(3):
        np.add.at(an, P.tri[:, k], P.area / 3)
    tr = cKDTree(P.xy)
    grp = tr.query_ball_point(P.xy, R)
    out = np.empty_like(falt_)
    for i, g in enumerate(grp):
        w = an[g]
        out[i] = (falt_[g] * w[:, None] if falt_.ndim > 1 else falt_[g] * w).sum(0) / w.sum()
    return out


def kor(k_ror, hmax=200.0, utan=(), ytterskikt=False, vagg_k=None):
    P, f = bygg(hmax=hmax, k_ror=k_ror, utan=utan, ytterskikt=ytterskikt, vagg_k=vagg_k)
    polys, monster = falt()
    # nyttig last per fält: 2,0 + 0,7 kN/m² och trappans nyttiga last i det fält där den står
    fQc = []
    qt = f["QT"][0::3]
    for p in polys:
        fq = P.last_yta(QK + QV, p)
        inne = MplPath(np.asarray(p, float)).contains_points(P.xy)
        fq[0::3] += np.where(inne, qt, 0.0)
        fQc.append(fq)
    tot = sum(fq[0::3].sum() for fq in fQc)
    assert abs(tot - (f["Q"] + f["V"] + f["QT"])[0::3].sum()) < 1e-3 * tot, "fälten täcker inte plattan"
    res = P.los_flera([f["G"], f["S"], f["Gp"], f["W"]] + [f["S_" + k] for k in KROPPAR] + fQc)
    rG, rS, rGp, rW = res[:4]
    rSk = dict(zip(KROPPAR, res[4:4 + len(KROPPAR)]))
    rQ = res[4 + len(KROPPAR):]
    namn_p = [f"P{i}" for i in range(1, len(GEO["pelare"]) + 1)]
    RG = rG.reaktioner()
    RSk = {k: r.reaktioner() for k, r in rSk.items()}
    RQ = [r.reaktioner() for r in rQ]
    env = dict(mux=np.zeros(P.nn), muy=np.zeros(P.nn), mox=np.zeros(P.nn), moy=np.zeros(P.nn),
               R={n: -1e18 for n in namn_p}, Rkomb={})
    mQ = [r.m_nod for r in rQ]
    for (kn, (cg, cq, cs)), (mn, mask) in itertools.product(ULS.items(), monster.items()):
        mq = sum(mk * m_ for mk, m_ in zip(mask, mQ))
        for sn in SNO:
            m = cg * rG.m_nod + cq * mq + cs * sum(rSk[k].m_nod for k in sn)
            wa = wood_armer(m[:, 0], m[:, 1], m[:, 2])
            env["mux"] = np.maximum(env["mux"], wa[0]); env["muy"] = np.maximum(env["muy"], wa[1])
            env["mox"] = np.minimum(env["mox"], wa[2]); env["moy"] = np.minimum(env["moy"], wa[3])
            for n in namn_p:
                R = cg * RG[n] + cs * sum(RSk[k][n] for k in sn) + cq * sum(mk * r[n] for mk, r in zip(mask, RQ))
                if R > env["R"][n]:
                    env["R"][n] = R; env["Rkomb"][n] = f"{kn}, Q {mn}, snö {''.join(sn) or 'ingen'}"
    # vindlyft: 1,0 Gp + W (W är redan dimensionerande)
    m = rGp.m_nod + rW.m_nod
    wa = wood_armer(m[:, 0], m[:, 1], m[:, 2])
    lyft = dict(mux=wa[0], muy=wa[1], mox=wa[2], moy=wa[3])
    env["mux"] = np.maximum(env["mux"], wa[0]); env["muy"] = np.maximum(env["muy"], wa[1])
    env["mox"] = np.minimum(env["mox"], wa[2]); env["moy"] = np.minimum(env["moy"], wa[3])
    RGp, RW = rGp.reaktioner(), rW.reaktioner()
    env["R_lyft"] = {n: RGp[n] + RW[n] for n in namn_p}
    env["lyft"] = lyft
    lf = dict(G=rG, S=rS, Sk=rSk, Q=rQ, Gp=rGp, W=rW, monster=monster, f=f, fQ=fQc)
    return P, env, lf


if __name__ == "__main__":
    import time
    for k in (None, 1e9):
        t = time.time()
        P, env, lf = kor(k)
        print(f"rör {'fjäder' if k is None else 'styva'}: ne {P.ne}, {time.time() - t:.0f} s")
        print("  max uk mx/my (kNm/m):", round(env["mux"].max() / 1e3, 1), round(env["muy"].max() / 1e3, 1))
        print("  min ök mx/my (kNm/m):", round(env["mox"].min() / 1e3, 1), round(env["moy"].min() / 1e3, 1))
        r0 = lf["G"]
        for B in (500.0, 750.0):
            ox = utjamna_linje(r0, env["mox"], "x", B); oy = utjamna_linje(r0, env["moy"], "y", B)
            ux = utjamna_linje(r0, env["mux"], "x", B); uy = utjamna_linje(r0, env["muy"], "y", B)
            print(f"  utjämnat över {B:.0f} mm: ök x {ox.min()/1e3:.1f} y {oy.min()/1e3:.1f}  uk x {ux.max()/1e3:.1f} y {uy.max()/1e3:.1f}")
            i = np.argmin(ox); j = np.argmin(oy)
            print("     ök x var:", P.xy[i].round(), " ök y var:", P.xy[j].round())
        top = sorted(env["R"].items(), key=lambda kv: -kv[1])[:5]
        print("  största rörlaster:", [(n, round(v / 1e3, 1), env["Rkomb"][n]) for n, v in top])
