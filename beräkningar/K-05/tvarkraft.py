"""
Tvärkraft genom ett kontrollsnitt: V = ∫ q·n ds längs en polylinje, ur FE-modellens tvärkraftsfält.
Snittkraften är linjär i lasterna och räknas per lastfall och kombineras sedan.
"""
import numpy as np
from matplotlib.tri import Triangulation
from shapely.geometry import LineString, MultiLineString, Polygon, box


def q_vektor(P, m_nod):
    """(qx, qy) per element [N/mm] ur momentfältets gradient."""
    xy = P.xy[P.tri]
    b = np.stack([xy[:, 1, 1] - xy[:, 2, 1], xy[:, 2, 1] - xy[:, 0, 1], xy[:, 0, 1] - xy[:, 1, 1]], 1)
    c = np.stack([xy[:, 2, 0] - xy[:, 1, 0], xy[:, 0, 0] - xy[:, 2, 0], xy[:, 1, 0] - xy[:, 0, 0]], 1)
    A2 = (b * xy[:, :, 0]).sum(1)[:, None]
    me = m_nod[P.tri]
    dx = (b[:, :, None] * me).sum(1) / A2
    dy = (c[:, :, None] * me).sum(1) / A2
    return np.stack([dx[:, 0] + dy[:, 2], dx[:, 2] + dy[:, 1]], 1)


class Snitt:
    """Punkter, normaler och längdelement längs ett (öppet eller slutet) snitt."""

    _finder = {}

    def __init__(self, P, geom, ds=10.0, centrum=None):
        if id(P) not in Snitt._finder:          # en sökstruktur per modell
            Snitt._finder[id(P)] = Triangulation(P.xy[:, 0], P.xy[:, 1], P.tri).get_trifinder()
        finder = Snitt._finder[id(P)]
        lines = list(geom.geoms) if isinstance(geom, MultiLineString) else [geom]
        pts, nrm, dl = [], [], []
        for L in lines:
            n = max(int(L.length / ds), 2)
            s = (np.arange(n) + 0.5) / n * L.length
            for si in s:
                p = L.interpolate(si); p2 = L.interpolate(min(si + 1, L.length)); p1 = L.interpolate(max(si - 1, 0))
                t = np.array([p2.x - p1.x, p2.y - p1.y]); t /= np.linalg.norm(t)
                nn = np.array([t[1], -t[0]])
                if centrum is not None and np.dot(nn, [p.x - centrum[0], p.y - centrum[1]]) < 0:
                    nn = -nn                      # normal pekar bort från det belastade området
                pts.append((p.x, p.y)); nrm.append(nn); dl.append(L.length / n)
        self.pts = np.array(pts); self.n = np.array(nrm); self.ds = np.array(dl)
        self.el = finder(self.pts[:, 0], self.pts[:, 1])
        ok = self.el >= 0
        self.pts, self.n, self.ds, self.el = self.pts[ok], self.n[ok], self.ds[ok], self.el[ok]
        self.langd = self.ds.sum()

    def kraft(self, q):
        """Tvärkraft genom snittet mot det belastade området: V = ∫ q·n ds, n utåt. För ett rör är V = reaktion −
        last innanför snittet (kontrollerat mot modellens reaktioner)."""
        return float((np.einsum("ij,ij->i", q[self.el], self.n) * self.ds).sum())
