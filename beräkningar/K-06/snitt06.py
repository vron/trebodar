"""
K-06: snittkrafter som räknas per lastfall och sedan kombineras (allt är linjärt):
  balkmoment och tvärkraft längs kantbalkar och innerbalkar (plattans moment integrerat över balkbredden),
  väggkrafter per meter, nettokraft genom genomstansningssnitt vid rören (rörlast minus cellplasttryck innanför).
"""
import numpy as np
import scipy.sparse as sp
from matplotlib.path import Path as MplPath
from matplotlib.tri import Triangulation
from shapely.geometry import LineString, Point, box
from shapely.ops import unary_union

import indata as I
import modell06 as M

DS = 50.0                # avstånd mellan snitten längs balkarna [mm]
NB = 11                  # punkter över balkbredden
A_STANS = (0.5, 1.0, 1.5, 2.0)    # kontrollsnitt a / d


def skjuv_komp(P, m_nod):
    """qx = ∂mx/∂x + ∂mxy/∂y, qy = ∂mxy/∂x + ∂my/∂y per element [N/mm]."""
    xy = P.xy[P.tri]
    b = np.stack([xy[:, 1, 1] - xy[:, 2, 1], xy[:, 2, 1] - xy[:, 0, 1], xy[:, 0, 1] - xy[:, 1, 1]], 1)
    c = np.stack([xy[:, 2, 0] - xy[:, 1, 0], xy[:, 0, 0] - xy[:, 2, 0], xy[:, 1, 0] - xy[:, 0, 0]], 1)
    A2 = (b * xy[:, :, 0]).sum(1)[:, None]
    me = m_nod[P.tri]
    dx = (b[:, :, None] * me).sum(1) / A2
    dy = (c[:, :, None] * me).sum(1) / A2
    return dx[:, 0] + dy[:, 2], dx[:, 2] + dy[:, 1]


def balklinjer(Pb):
    """Balkarnas centrumlinjer som raka delar: (namn, p0, p1, riktning 'x'/'y')."""
    g = Pb.geo06
    ring = g["poly"].buffer(-I.B_BALK / 2, join_style=2).exterior
    cs = list(ring.coords)
    delar = []
    for k, (a, b) in enumerate(zip(cs[:-1], cs[1:])):
        if np.hypot(b[0] - a[0], b[1] - a[1]) < 1:
            continue
        rikt = "x" if abs(b[1] - a[1]) < 1 else "y"
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        nv = min(range(len(M.VAGGLIN)), key=lambda i: LineString(M.VAGGLIN[i]).distance(Point(mid)))
        d = LineString(M.VAGGLIN[nv]).distance(Point(mid))
        delar.append(dict(namn=f"kant {k + 1}", vagg=f"V{nv + 1}" if d < 300 else "öppning", p0=a, p1=b, rikt=rikt,
                          kant=True))
    for namn, a, b, rikt in (("inre V4–V6", (4540, 7510), (9640, 7510), "x"),
                             ("inre V15", (9640, 7510), (9640, 10860), "y"),
                             ("inre V19", (4540, 7510), (4540, 9200), "y")):
        delar.append(dict(namn=namn, vagg=namn.split()[1], p0=a, p1=b, rikt=rikt, kant=False))
    return delar


def _bary(Pb, pts):
    tr = Triangulation(Pb.xy[:, 0], Pb.xy[:, 1], Pb.tri)
    f = tr.get_trifinder()
    e = f(pts[:, 0], pts[:, 1])
    rows, cols, vals = [], [], []
    for i, (el, (x, y)) in enumerate(zip(e, pts)):
        if el < 0:
            continue
        n = Pb.tri[el]
        (x1, y1), (x2, y2), (x3, y3) = Pb.xy[n]
        det = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
        l1 = ((y2 - y3) * (x - x3) + (x3 - x2) * (y - y3)) / det
        l2 = ((y3 - y1) * (x - x3) + (x1 - x3) * (y - y3)) / det
        for nn, l in zip(n, (l1, l2, 1 - l1 - l2)):
            rows.append(i); cols.append(nn); vals.append(l)
    return e, sp.csr_matrix((vals, (rows, cols)), shape=(len(pts), Pb.nn))


class Snitt:
    def __init__(self, S):
        Pb = S.Pb
        self.S = S
        self.balkar = []
        from shapely.prepared import prep
        TJ = prep(Pb.geo06["tjock"].buffer(1))
        for bk in balklinjer(Pb):
            p0, p1 = np.array(bk["p0"], float), np.array(bk["p1"], float)
            L = np.hypot(*(p1 - p0))
            t = (p1 - p0) / L
            n = np.array([-t[1], t[0]])
            s = np.arange(DS / 2, L, DS)
            off = np.linspace(-I.B_BALK / 2 * 0.98, I.B_BALK / 2 * 0.98, NB)
            w = np.full(NB, off[1] - off[0]); w[[0, -1]] /= 2
            pts = (p0[None, None, :] + s[:, None, None] * t + off[None, :, None] * n).reshape(-1, 2)
            inne = np.array([TJ.contains(Point(p)) for p in pts]).reshape(len(s), NB).all(1)
            e, Bm = _bary(Pb, pts)
            ok = (e.reshape(len(s), NB) >= 0).all(1) & inne
            self.balkar.append(dict(bk, s=s[ok], L=L, idx=ok, B=Bm, e=e.reshape(len(s), NB), w=w, ns=len(s),
                                    xy=(p0[None, :] + s[:, None] * t)[ok]))
        # rör: noder inom kontrollsnitten
        self.stans = []
        h = S.utf["h_balk"]
        d = h - 30 - 10
        for i, (_, x, y, bx, by, _) in enumerate(M.ROR):
            reg = []
            for a in A_STANS:
                g = box(x - bx / 2, y - by / 2, x + bx / 2, y + by / 2).buffer(a * d)
                m = MplPath(np.asarray(g.exterior.coords)).contains_points(Pb.xy)
                reg.append(dict(a=a * d, u=g.exterior.length, nod=np.where(m)[0]))
            self.stans.append(dict(namn=f"P{i + 1}", d=d, reg=reg))
        # väggar: fönster om 1 m
        self.vagg = {}
        for j, kp in enumerate(S.kopp):
            if kp["typ"] == "vägg":
                self.vagg.setdefault(kp["namn"], []).append((j, kp["s"]))

    def balk_lf(self, m_nod, qx, qy):
        """Moment [kNm] och tvärkraft [kN] längs varje balk för ett lastfall."""
        out = []
        for bk in self.balkar:
            k = 0 if bk["rikt"] == "x" else 1
            mv = (bk["B"] @ m_nod[:, k]).reshape(bk["ns"], NB)
            q = (qx if k == 0 else qy)[np.clip(bk["e"], 0, None)]
            Mb = (mv * bk["w"]).sum(1)[bk["idx"]] / 1e6
            Vb = (q * bk["w"]).sum(1)[bk["idx"]] / 1e3
            out.append((Mb, Vb))
        return out

    def stans_lf(self, p_kpa):
        """Cellplastens kraft [kN] innanför varje kontrollsnitt."""
        a = self.S.Pb.a_nod
        return [[float((p_kpa[r["nod"]] * a[r["nod"]]).sum() * 1e-6) for r in st["reg"]] for st in self.stans]

    def vagg_lf(self, u, eps=0.0):
        """Väggkraft per 1 m (största fönstret) per vägg [kN/m]."""
        out = {}
        for n, lst in self.vagg.items():
            f = np.array([M.kraft(self.S.kopp[j], u) - self.S.kopp[j]["k"] * eps * I.H_VAGG for j, _ in lst]) / 1e3
            s = np.array([s_ for _, s_ in lst])
            L = s.max() + (s[1] - s[0] if len(s) > 1 else 0) / 2
            Lw = min(1000.0, L)
            win = [(s >= s0) & (s <= s0 + Lw) for s0 in np.arange(0, max(L - Lw, 0) + 1, 50)]
            out[n] = np.array([f[m].sum() / (Lw / 1000) for m in win])
        return out
