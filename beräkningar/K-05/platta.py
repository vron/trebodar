"""
Linjärelastisk plattmodell (Kirchhoff) med DKT-element (Batoz 1980).

Enheter: N, mm, MPa.  w positiv nedåt (i lastens riktning).
Moment per längdenhet (Nmm/mm = kNm/m): mx, my positiva när undersidan är dragen, mxy vridmoment.

Geometri: en yttre polygon, valfria hål, valfria inre linjer (väggar) och punkter (pelare, punktlaster)
som läggs in i nätet så att stöd och laster hamnar på noder.

Stöd:
  linje  – w = 0 längs en polyline (vägg, fritt upplag)
  yta    – fjädrar/w = 0 över en rektangel (pelarhuvud eller pelarplåt)
  punkt  – en nod
Laster: jämnt utbredd över hela plattan eller en polygon, linjelast, punktlast.
"""
from __future__ import annotations

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
import triangle as tr
from matplotlib.tri import Triangulation, LinearTriInterpolator
from shapely.geometry import Polygon, Point, LineString
from matplotlib.path import Path as MplPath


# ------------------------------------------------------------------ element
GP = np.array([[2 / 3, 1 / 6, 1 / 6], [1 / 6, 2 / 3, 1 / 6], [1 / 6, 1 / 6, 2 / 3]])
GW = np.array([1 / 3, 1 / 3, 1 / 3])
EDGES = ((1, 2), (2, 0), (0, 1))     # mittnod 3, 4, 5 ligger på sidan mitt emot hörn 0, 1, 2


def _geom(xy):
    x, y = xy[:, 0], xy[:, 1]
    b = np.array([y[1] - y[2], y[2] - y[0], y[0] - y[1]])
    c = np.array([x[2] - x[1], x[0] - x[2], x[1] - x[0]])
    A2 = x[0] * b[0] + x[1] * b[1] + x[2] * b[2]
    return b, c, A2


def _T(xy):
    """Rotationer (βx, βy) i 6 noder ur elementets 9 frihetsgrader [w, θx, θy]×3 (θ = ∂w/∂x, ∂w/∂y)."""
    T = np.zeros((12, 9))
    for k in range(3):                              # hörn
        T[2 * k, 3 * k + 1] = 1
        T[2 * k + 1, 3 * k + 2] = 1
    for m, (i, j) in enumerate(EDGES):              # mittnoder: Kirchhoff längs sidan
        d = xy[j] - xy[i]
        L = np.hypot(*d)
        c, s = d / L
        # ws_m = 1.5(wj-wi)/L - 0.25(ws_i+ws_j),  wn_m = 0.5(wn_i+wn_j)
        ws = np.zeros(9); wn = np.zeros(9)
        ws[3 * i] = -1.5 / L; ws[3 * j] = 1.5 / L
        for n in (i, j):
            ws[3 * n + 1] += -0.25 * c; ws[3 * n + 2] += -0.25 * s
            wn[3 * n + 1] += 0.5 * -s;  wn[3 * n + 2] += 0.5 * c
        r = 2 * (3 + m)
        T[r] = c * ws - s * wn
        T[r + 1] = s * ws + c * wn
    return T


def _B(xy, L, T=None, geo=None):
    """Krökning χ = [∂βx/∂x, ∂βy/∂y, ∂βx/∂y + ∂βy/∂x] = B u i punkten med arekoordinater L."""
    b, c, A2 = geo if geo is not None else _geom(xy)
    T = _T(xy) if T is None else T
    L1, L2, L3 = L
    # derivator av kvadratiska formfunktioner med avseende på L1..L3
    dN = np.array([
        [4 * L1 - 1, 0, 0],
        [0, 4 * L2 - 1, 0],
        [0, 0, 4 * L3 - 1],
        [0, 4 * L3, 4 * L2],
        [4 * L3, 0, 4 * L1],
        [4 * L2, 4 * L1, 0],
    ])
    dNx = dN @ b / A2
    dNy = dN @ c / A2
    Bb = np.zeros((3, 12))
    Bb[0, 0::2] = dNx
    Bb[1, 1::2] = dNy
    Bb[2, 0::2] = dNy
    Bb[2, 1::2] = dNx
    return Bb @ T


def Dmat(D, nu, Dy=None):
    """Isotrop (Dy=None) eller ortotrop böjstyvhet [Nmm²/mm]."""
    if Dy is None:
        return D * np.array([[1, nu, 0], [nu, 1, 0], [0, 0, (1 - nu) / 2]])
    Dx = D
    Dm = np.sqrt(Dx * Dy)
    return np.array([[Dx, nu * Dm, 0], [nu * Dm, Dy, 0], [0, 0, (1 - nu) / 2 * Dm]])


# ------------------------------------------------------------------ modell
class Platta:
    def __init__(self, kontur, hal=(), linjer=(), punkter=(), rektanglar=(), hmax=150.0, finare=()):
        """
        kontur      [(x, y), ...] mm, moturs eller medurs
        hal         lista av polygoner (öppningar)
        linjer      polylinjer som ska finnas i nätet (väggar, linjelaster)
        punkter     punkter som ska vara noder (punktlaster)
        rektanglar  (xc, yc, bx, by) som ska finnas i nätet (pelarhuvuden), bx, by mm
        hmax        största elementsida [mm]
        finare      [(x, y, r, h)]: elementsida h inom radien r från (x, y)
        """
        self.kontur = Polygon(kontur)
        self.hal = [Polygon(h) for h in hal]
        V, S, H = [], [], []

        def add_poly(p, closed=True):
            i0 = len(V)
            V.extend(p)
            n = len(p)
            for k in range(n - 1 + closed):
                S.append((i0 + k, i0 + (k + 1) % n))

        add_poly(list(kontur))
        for h in hal:
            add_poly(list(h))
            H.append(Polygon(h).representative_point().coords[0])
        for l in linjer:
            add_poly(list(l), closed=False)
        for (xc, yc, bx, by) in rektanglar:
            add_poly([(xc - bx / 2, yc - by / 2), (xc + bx / 2, yc - by / 2), (xc + bx / 2, yc + by / 2),
                      (xc - bx / 2, yc + by / 2)])
            V.append((xc, yc))
        V.extend(punkter)
        # dela långa segment så att randen får rätt elementstorlek
        V2, S2 = list(V), []
        for a, b in S:
            pa, pb = np.array(V2[a]), np.array(V2[b])
            n = max(1, int(np.ceil(np.hypot(*(pb - pa)) / hmax)))
            idx = [a]
            for k in range(1, n):
                V2.append(tuple(pa + (pb - pa) * k / n))
                idx.append(len(V2) - 1)
            idx.append(b)
            S2 += list(zip(idx[:-1], idx[1:]))
        V2 = np.array(V2, float)
        # slå ihop dubbla punkter
        uniq, inv = np.unique(np.round(V2, 6), axis=0, return_inverse=True)
        inv = inv.ravel()
        S2 = np.array([(inv[a], inv[b]) for a, b in S2 if inv[a] != inv[b]])
        geo = dict(vertices=uniq, segments=S2)
        if H:
            geo["holes"] = np.array(H)
        amax = 0.433 * hmax ** 2
        self.finare = list(finare)
        if self.finare:
            mesh = tr.triangulate(geo, "pq30a%.1f" % amax)
            for _ in range(4):                      # förfina runt valda punkter
                xy, t = mesh["vertices"], mesh["triangles"]
                cen = xy[t].mean(axis=1)
                a = np.full(len(t), amax)
                for (x, y, r, h) in self.finare:
                    dist = np.hypot(cen[:, 0] - x, cen[:, 1] - y)
                    hh = np.where(dist < r, h, h + (dist - r) * 0.5)
                    a = np.minimum(a, 0.433 * hh ** 2)
                mesh = tr.triangulate(dict(vertices=xy, segments=mesh["segments"], triangles=t,
                                           triangle_max_area=a, **({"holes": geo["holes"]} if H else {})), "rpq30a")
        else:
            mesh = tr.triangulate(geo, "pq30a%.1f" % amax)
        used = np.unique(mesh["triangles"])
        ny = -np.ones(len(mesh["vertices"]), int); ny[used] = np.arange(len(used))
        self.oanvanda = mesh["vertices"][np.setdiff1d(np.arange(len(mesh["vertices"])), used)]
        self.xy = mesh["vertices"][used]
        self.tri = ny[mesh["triangles"]]
        self.nn = len(self.xy)
        self.ne = len(self.tri)
        self.ndof = 3 * self.nn
        self._T = [_T(self.xy[t]) for t in self.tri]
        self._geo = [_geom(self.xy[t]) for t in self.tri]
        self.area = np.array([g[2] / 2 for g in self._geo])
        self.Bg = np.array([[_B(self.xy[t], L, self._T[e], self._geo[e]) for L in GP] for e, t in enumerate(self.tri)])
        self.Bc = np.array([[_B(self.xy[t], L, self._T[e], self._geo[e]) for L in np.eye(3)] for e, t in enumerate(self.tri)])
        self.B0 = np.array([_B(self.xy[t], (1 / 3, 1 / 3, 1 / 3), self._T[e], self._geo[e]) for e, t in enumerate(self.tri)])
        self.edofs = (np.repeat(3 * self.tri, 3, axis=1) + np.tile([0, 1, 2], 3)).astype(int)
        self.cen = self.xy[self.tri].mean(axis=1)
        self.fixed = {}          # dof -> föreskrivet värde (0)
        self.springs = {}        # dof -> styvhet N/mm
        self.tang = []           # (nod, c, s): straff på lutningen längs linjestöd
        self.stod = []           # (namn, typ, nodlista)
        self.D = None

    # ---------------------------------------------------------- nätfrågor
    def nod(self, x, y):
        return int(np.argmin(np.hypot(self.xy[:, 0] - x, self.xy[:, 1] - y)))

    def noder_pa_linje(self, pl, tol=1.0):
        ls = LineString(pl)
        return [i for i, p in enumerate(self.xy) if ls.distance(Point(p)) < tol]

    def noder_i_rekt(self, xc, yc, bx, by, tol=1.0):
        return [i for i, (x, y) in enumerate(self.xy)
                if abs(x - xc) <= bx / 2 + tol and abs(y - yc) <= by / 2 + tol]

    # ---------------------------------------------------------- stöd
    def stod_linje(self, namn, pl, k=None):
        """Linjestöd: w = 0 (k=None) eller fjäder k [N/mm per mm]."""
        nod = self.noder_pa_linje(pl)
        self._lagg_stod(namn, "linje", nod, k, pl)

    def stod_rekt(self, namn, xc, yc, bx, by, k=None):
        """Pelarhuvud bx×by: w = 0 i alla noder (k=None) eller total axialstyvhet k [N/mm] fördelad på noderna."""
        nod = self.noder_i_rekt(xc, yc, bx, by)
        self._lagg_stod(namn, "rekt", nod, k, (xc, yc, bx, by))

    def stod_mark(self, namn, poly, k):
        """Platta på mark/isolering: bäddmodul k [N/mm³] inom polygonen, fördelad på noderna efter area."""
        Pg = Polygon(poly)
        nod = set()
        for e, t in enumerate(self.tri):
            if Pg.contains(Point(self.xy[t].mean(axis=0))):
                for n in t:
                    self.springs[3 * n] = self.springs.get(3 * n, 0) + k * self.area[e] / 3
                    nod.add(int(n))
        self.stod.append(dict(namn=namn, typ="mark", noder=sorted(nod), k=k, geo=poly))

    def stod_punkt(self, namn, x, y, k=None):
        self._lagg_stod(namn, "punkt", [self.nod(x, y)], k, (x, y))

    def _lagg_stod(self, namn, typ, nod, k, geo):
        assert nod, namn
        if k is None:
            for n in nod:
                self.fixed[3 * n] = 0.0
        else:
            kk = k / len(nod) if typ != "linje" else None
            if typ == "linje":       # fördela per tillhörande längd
                ls = LineString(geo)
                s = np.array([ls.project(Point(self.xy[n])) for n in nod])
                o = np.argsort(s); s = s[o]; nod = [nod[i] for i in o]
                w = np.zeros(len(s))
                w[:-1] += np.diff(s) / 2; w[1:] += np.diff(s) / 2
                for n, wi in zip(nod, w):
                    self.springs[3 * n] = self.springs.get(3 * n, 0) + k * wi
            else:
                for n in nod:
                    self.springs[3 * n] = self.springs.get(3 * n, 0) + kk
        if typ == "linje" and k is None:      # hårt fritt upplag: ∂w/∂s = 0 längs stödet
            for a, b in zip(geo[:-1], geo[1:]):
                d = np.subtract(b, a); c, s_ = d / np.hypot(*d)
                for n in self.noder_pa_linje([a, b]):
                    self.tang.append((n, c, s_))
        self.stod.append(dict(namn=namn, typ=typ, noder=list(nod), k=k, geo=geo))

    # ---------------------------------------------------------- styvhet
    def styvhet(self, Delem):
        """Delem: 3×3 (samma i alla element) eller array (ne, 3, 3)."""
        Delem = np.asarray(Delem)
        if Delem.ndim == 2:
            Delem = np.broadcast_to(Delem, (self.ne, 3, 3))
        self.Delem = Delem
        Ke = np.einsum("egji,ejk,egkl,g,e->eil", self.Bg, Delem, self.Bg, GW, self.area, optimize=True)
        rows = np.repeat(self.edofs, 9, axis=1).ravel()
        cols = np.tile(self.edofs, (1, 9)).ravel()
        K = sp.coo_matrix((Ke.reshape(self.ne, 81).ravel(), (rows, cols)), shape=(self.ndof, self.ndof)).tocsr()
        if self.springs:
            d = np.array(list(self.springs)); k = np.array(list(self.springs.values()))
            K = K + sp.coo_matrix((k, (d, d)), shape=K.shape).tocsr()
        if self.tang:
            kp = 1e4 * float(np.max(Delem[:, 0, 0]))
            r, c_, v = [], [], []
            for n, c, s_ in self.tang:
                d = [3 * n + 1, 3 * n + 2]; m = kp * np.array([[c * c, c * s_], [c * s_, s_ * s_]])
                for i in range(2):
                    for j in range(2):
                        r.append(d[i]); c_.append(d[j]); v.append(m[i, j])
            K = K + sp.coo_matrix((v, (r, c_)), shape=K.shape).tocsr()
        self.K = K
        return K

    # ---------------------------------------------------------- laster
    def last_yta(self, q, poly=None):
        """Jämnt utbredd last q [MPa = N/mm²] på hela plattan eller inom polygonen (elementens tyngdpunkt)."""
        f = np.zeros(self.ndof)
        inne = np.ones(self.ne, bool) if poly is None else MplPath(np.asarray(poly, float)).contains_points(self.cen)
        np.add.at(f, 3 * self.tri[inne].ravel(), np.repeat(q * self.area[inne] / 3, 3))
        return f

    def last_punkt(self, P, x, y):
        f = np.zeros(self.ndof)
        f[3 * self.nod(x, y)] += P
        return f

    def last_linje(self, p, pl):
        """Linjelast p [N/mm] längs en polyline som finns i nätet."""
        f = np.zeros(self.ndof)
        nod = self.noder_pa_linje(pl)
        ls = LineString(pl)
        s = np.array([ls.project(Point(self.xy[n])) for n in nod])
        o = np.argsort(s); s = s[o]; nod = [nod[i] for i in o]
        w = np.zeros(len(s)); w[:-1] += np.diff(s) / 2; w[1:] += np.diff(s) / 2
        for n, wi in zip(nod, w):
            f[3 * n] += p * wi
        return f

    def last_krokning(self, chi0):
        """Ekvivalent last från fri initialkrökning χ0 (ne, 3) i matematisk mening (∂²w/∂x² ...)."""
        f = np.zeros(self.ndof)
        fe = np.einsum("egji,ejk,ek,g,e->ei", self.Bg, self.Delem, chi0, GW, self.area, optimize=True)
        np.add.at(f, self.edofs.ravel(), fe.ravel())
        return f

    # ---------------------------------------------------------- lösning
    def los_flera(self, F):
        """Linjär lösning för flera lastvektorer (kolumner i F) med en faktorisering."""
        free = np.setdiff1d(np.arange(self.ndof), np.array(list(self.fixed), int))
        lu = spla.splu(self.K[free][:, free].tocsc())
        out = []
        for f in F:
            u = np.zeros(self.ndof); u[free] = lu.solve(f[free])
            R = f - self.K @ u
            for d, k in self.springs.items():
                R[d] = k * u[d]
            out.append(Resultat(self, u, R, f))
        return out

    def los(self, f, chi0=None):
        free = np.setdiff1d(np.arange(self.ndof), np.array(list(self.fixed), int))
        u = np.zeros(self.ndof)
        Kff = self.K[free][:, free].tocsc()
        u[free] = spla.spsolve(Kff, f[free])
        R = f - self.K @ u                      # reaktion uppåt positiv i fasta frihetsgrader
        for d, k in self.springs.items():
            R[d] = k * u[d]                     # fjäderns kraft på plattan (uppåt)
        return Resultat(self, u, R, f, chi0)


class Resultat:
    def __init__(self, P: Platta, u, R, f, chi0=None):
        self.P, self.u, self.R, self.f = P, u, R, f
        self.w = u[0::3]
        self.chi0 = chi0
        self._moment()

    def _moment(self, chi0=None):
        P = self.P
        nn, ne = P.nn, P.ne
        chi0 = np.zeros((ne, 3)) if self.chi0 is None else self.chi0
        ue = self.u[P.edofs]                                         # (ne, 9)
        chic = np.einsum("ekij,ej->eki", P.Bc, ue) - chi0[:, None, :]
        mc = -np.einsum("eij,ekj->eki", P.Delem, chic)              # (ne, 3 hörn, 3)
        me = -np.einsum("eij,ej->ei", P.Delem, np.einsum("eij,ej->ei", P.B0, ue) - chi0)
        mn = np.zeros((nn, 3)); an = np.zeros(nn)
        for k in range(3):
            np.add.at(mn, P.tri[:, k], mc[:, k] * P.area[:, None])
            np.add.at(an, P.tri[:, k], P.area)
        self.m_nod = mn / an[:, None]      # Nmm/mm, utjämnat
        self.m_el = me                     # i elementens tyngdpunkt
        self._tri = Triangulation(P.xy[:, 0], P.xy[:, 1], P.tri)
        self._ip = [LinearTriInterpolator(self._tri, self.m_nod[:, k]) for k in range(3)]
        self._ipw = LinearTriInterpolator(self._tri, self.w)

    def m(self, x, y):
        return np.array([float(ip(x, y)) for ip in self._ip])

    def w_at(self, x, y):
        return float(self._ipw(x, y))

    def reaktion(self, namn):
        s = next(s for s in self.P.stod if s["namn"] == namn)
        return float(sum(self.R[3 * n] for n in s["noder"]))

    def reaktioner(self):
        """Reaktion per stöd; en nod som hör till flera stöd räknas till det första."""
        sedd, out = set(), {}
        for s in self.P.stod:
            nod = [n for n in s["noder"] if n not in sedd]
            sedd.update(nod)
            out[s["namn"]] = float(sum(self.R[3 * n] for n in nod))
        return out

    def snitt(self, p0, p1, n=201, komp=0):
        """Moment längs en linje: (s, m) med m = komponent komp (0 mx, 1 my, 2 mxy)."""
        p0, p1 = np.array(p0, float), np.array(p1, float)
        t = np.linspace(0, 1, n)
        pts = p0 + np.outer(t, p1 - p0)
        m = np.array(self._ip[komp](pts[:, 0], pts[:, 1]))
        return t * np.hypot(*(p1 - p0)), m

    def medel(self, p0, p1, komp=0, n=401):
        """Medelmoment längs en linje (Nmm/mm)."""
        s, m = self.snitt(p0, p1, n, komp)
        ok = ~np.isnan(m)
        return np.trapezoid(m[ok], s[ok]) / (s[ok][-1] - s[ok][0])


def wood_armer(mx, my, mxy):
    """Dimensionerande moment för under- (+) och överkant (−) enligt Wood–Armer. Returnerar
    (mx_u, my_u, mx_o, my_o) där underkant ≥ 0 och överkant ≤ 0."""
    mx, my, mxy = np.broadcast_arrays(*(np.asarray(v, float) for v in (mx, my, mxy)))
    a = np.abs(mxy)
    # underkant
    mxu = mx + a; myu = my + a
    with np.errstate(divide="ignore", invalid="ignore"):
        c1 = mxu < 0
        myu = np.where(c1, my + np.where(mx != 0, mxy ** 2 / np.abs(mx), 0), myu); mxu = np.where(c1, 0, mxu)
        c2 = myu < 0
        mxu = np.where(c2, mx + np.where(my != 0, mxy ** 2 / np.abs(my), 0), mxu); myu = np.where(c2, 0, myu)
        mxu = np.maximum(mxu, 0); myu = np.maximum(myu, 0)
        # överkant
        mxo = mx - a; myo = my - a
        c1 = mxo > 0
        myo = np.where(c1, my - np.where(mx != 0, mxy ** 2 / np.abs(mx), 0), myo); mxo = np.where(c1, 0, mxo)
        c2 = myo > 0
        mxo = np.where(c2, mx - np.where(my != 0, mxy ** 2 / np.abs(my), 0), mxo); myo = np.where(c2, 0, myo)
        mxo = np.minimum(mxo, 0); myo = np.minimum(myo, 0)
    return mxu, myu, mxo, myo
