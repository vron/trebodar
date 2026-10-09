"""
Exakta geometrifrågor mot B-rep (OCP): plansnitt, linjeprober, punktfrågor, avstånd, krockar och ytanalys.
Alla koordinater i mm, globalt system.
"""
import re
from dataclasses import dataclass

import numpy as np
import shapely
from shapely.geometry import LineString, MultiPolygon, Polygon
from shapely.ops import polygonize, unary_union

AXEL = {"x": np.array([1.0, 0, 0]), "y": np.array([0, 1.0, 0]), "z": np.array([0, 0, 1.0])}


def tal3(s):
    """'1,2,3' -> np.array([1,2,3])"""
    v = np.array([float(t) for t in re.split(r"[,; ]+", s.strip()) if t])
    if len(v) != 3:
        raise ValueError(f"väntade tre tal: {s!r}")
    return v


# ---- plan --------------------------------------------------------------------------------------

@dataclass
class Plan:
    o: np.ndarray        # punkt i planet
    n: np.ndarray        # enhetsnormal
    u: np.ndarray        # 2D-axel 1 (vågrätt i ritningen)
    v: np.ndarray        # 2D-axel 2 (lodrätt i ritningen)
    namn: str            # "z=12500"
    axlar: tuple         # etiketter för (u, v), t.ex. ("x", "y")
    normalaxel: str      # "z" eller "n"

    @classmethod
    def tolka(cls, s):
        """'z=12500', 'x=-3000', 'y=4000' eller 'o=x,y,z n=nx,ny,nz' (godtyckligt plan)."""
        s = s.strip()
        m = re.fullmatch(r"([xyz])\s*=\s*(-?[\d.]+)", s)
        if m:
            a, c = m.group(1), float(m.group(2))
            u, v = {"x": ("y", "z"), "y": ("x", "z"), "z": ("x", "y")}[a]
            return cls(AXEL[a] * c, AXEL[a].copy(), AXEL[u].copy(), AXEL[v].copy(), f"{a}={c:g}", (u, v), a)
        m = re.fullmatch(r"o\s*=\s*([^n]+?)\s*[ ;]\s*n\s*=\s*(.+)", s)
        if not m:
            raise ValueError(f"okänt plan: {s!r} (exempel: z=12500 eller 'o=0,0,12500 n=0,1,1')")
        o, n = tal3(m.group(1)), tal3(m.group(2))
        n = n / np.linalg.norm(n)
        u = np.cross(AXEL["z"], n) if abs(n[2]) < 0.9 else np.cross(AXEL["y"], n)
        u /= np.linalg.norm(u)
        v = np.cross(n, u)
        if abs(n[2]) < 0.9 and v[2] < 0:
            u, v = -u, -v
        return cls(o, n, u, v, s, ("u", "v"), "n")

    def flytta(self, du, dv):
        """Lägg 2D-origo i (du, dv) (i planets koordinater), t.ex. för att mäta i en ritnings system."""
        self.o = self.o + self.u * du + self.v * dv
        return self

    def till2d(self, P):
        P = np.atleast_2d(P) - self.o
        return np.c_[P @ self.u, P @ self.v]

    def till3d(self, uv):
        uv = np.atleast_2d(uv)
        return self.o + uv[:, :1] * self.u + uv[:, 1:2] * self.v

    def avstand(self, P):
        return (np.atleast_2d(P) - self.o) @ self.n

    def korsar(self, bbox, marg=0.0):
        hörn = np.array([[bbox[i], bbox[j], bbox[k]] for i in (0, 3) for j in (1, 4) for k in (2, 5)])
        d = self.avstand(hörn)
        return d.min() <= marg and d.max() >= -marg

    def gp(self):
        from OCP.gp import gp_Dir, gp_Pln, gp_Pnt
        return gp_Pln(gp_Pnt(*self.o), gp_Dir(*self.n))


# ---- hjälp -------------------------------------------------------------------------------------

def _pnt(p):
    from OCP.gp import gp_Pnt
    return gp_Pnt(*map(float, p))


def _utforska(s, typ):
    from OCP.TopExp import TopExp_Explorer
    e = TopExp_Explorer(s, typ)
    while e.More():
        yield e.Current()
        e.Next()


def solider(s):
    from OCP.TopAbs import TopAbs_SOLID
    from OCP.TopoDS import TopoDS
    return [TopoDS.Solid(x) for x in _utforska(s, TopAbs_SOLID)]


def inuti(s, p, tol=1e-6):
    """'in', 'pa' (på ytan) eller 'ut' för punkt p relativt formen s (alla solider)."""
    from OCP.BRepClass3d import BRepClass3d_SolidClassifier
    from OCP.TopAbs import TopAbs_IN, TopAbs_ON
    for so in solider(s):
        c = BRepClass3d_SolidClassifier(so, _pnt(p), tol)
        if c.State() == TopAbs_IN:
            return "in"
        if c.State() == TopAbs_ON:
            return "pa"
    return "ut"


def kantpunkter(e, avvikelse=0.5):
    """Punkter längs en kant: raka kanter exakt (ändpunkter), kurvor diskretiserade."""
    from OCP.BRepAdaptor import BRepAdaptor_Curve
    from OCP.GCPnts import GCPnts_TangentialDeflection
    from OCP.GeomAbs import GeomAbs_Line
    c = BRepAdaptor_Curve(e)
    if c.GetType() == GeomAbs_Line:
        return np.array([c.Value(c.FirstParameter()).Coord(), c.Value(c.LastParameter()).Coord()])
    d = GCPnts_TangentialDeflection(c, 0.05, avvikelse)
    return np.array([d.Value(i).Coord() for i in range(1, d.NbPoints() + 1)])


def bbox_avstand(a, b):
    a, b = np.asarray(a), np.asarray(b)
    g = np.maximum(0, np.maximum(a[:3] - b[3:], b[:3] - a[3:]))
    return float(np.linalg.norm(g))


def _segment_box(p1, p2, bbox, marg=1.0):
    lo, hi = np.asarray(bbox[:3]) - marg, np.asarray(bbox[3:]) + marg
    d = p2 - p1
    t0, t1 = 0.0, 1.0
    for i in range(3):
        if abs(d[i]) < 1e-12:
            if p1[i] < lo[i] or p1[i] > hi[i]:
                return False
        else:
            a, b = sorted(((lo[i] - p1[i]) / d[i], (hi[i] - p1[i]) / d[i]))
            t0, t1 = max(t0, a), min(t1, b)
            if t0 > t1:
                return False
    return True


# ---- plansnitt ---------------------------------------------------------------------------------

@dataclass
class SnittDel:
    del_: object
    yta: object          # shapely (Multi)Polygon i 2D, materialets snittyta (kan vara tom)
    linjer: list         # 2D-polylinjer (np N×2) för alla snittkanter


def snitt(m, delar, plan, avvikelse=0.3):
    """Exakt snitt av delarna med planet. Returnerar SnittDel per del som skärs."""
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Section
    from OCP.TopAbs import TopAbs_EDGE
    from OCP.TopoDS import TopoDS
    ut = []
    for d in delar:
        if not plan.korsar(d.bbox):
            continue
        s = m.form(d)
        sec = BRepAlgoAPI_Section(s, plan.gp(), False)
        sec.Approximation(False)
        sec.Build()
        if not sec.IsDone():
            continue
        linjer = []
        for e in _utforska(sec.Shape(), TopAbs_EDGE):
            p = kantpunkter(TopoDS.Edge(e), avvikelse)
            if len(p) >= 2:
                linjer.append(np.round(plan.till2d(p), 4))
        if not linjer:
            continue
        yta = Polygon()
        if d.volym > 0:
            ls = [LineString(l) for l in linjer if len(np.unique(l, axis=0)) >= 2]
            ytor = []
            for poly in polygonize(unary_union(ls)):
                if poly.area < 1e-6:
                    continue
                rp = poly.representative_point()
                if inuti(s, plan.till3d([rp.x, rp.y])[0], 1e-5) == "in":
                    ytor.append(poly)
            yta = unary_union(ytor) if ytor else Polygon()
        ut.append(SnittDel(d, yta, linjer))
    return ut


# ---- linjeprob ---------------------------------------------------------------------------------

def linjeprob(m, delar, p1, p2):
    """Sträckor där linjen p1→p2 går genom delarna: [(t0, t1, del, P0, P1)] sorterat, t i mm från p1."""
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge
    from OCP.TopAbs import TopAbs_EDGE
    from OCP.TopoDS import TopoDS
    p1, p2 = np.asarray(p1, float), np.asarray(p2, float)
    L = np.linalg.norm(p2 - p1)
    r = (p2 - p1) / L
    kant = BRepBuilderAPI_MakeEdge(_pnt(p1), _pnt(p2)).Edge()
    ut = []
    for d in delar:
        if not _segment_box(p1, p2, d.bbox):
            continue
        c = BRepAlgoAPI_Common(m.form(d), kant)
        for e in _utforska(c.Shape(), TopAbs_EDGE):
            q = kantpunkter(TopoDS.Edge(e))
            t = (q - p1) @ r
            a, b = q[np.argmin(t)], q[np.argmax(t)]
            if t.max() - t.min() > 1e-6:
                ut.append((float(t.min()), float(t.max()), d, a, b))
    return sorted(ut, key=lambda x: (x[0], x[1]))


# ---- punkt, avstånd, krock ---------------------------------------------------------------------

def avstand(sa, sb):
    """(avstånd, punkt på a, punkt på b)"""
    from OCP.BRepExtrema import BRepExtrema_DistShapeShape
    x = BRepExtrema_DistShapeShape(sa, sb)
    if not x.IsDone() or x.NbSolution() == 0:
        return None
    return x.Value(), np.array(x.PointOnShape1(1).Coord()), np.array(x.PointOnShape2(1).Coord())


def punktfraga(m, delar, p, n=6):
    """(delar som innehåller p, [(avstånd, del, närmaste punkt)] för de n närmaste)."""
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeVertex
    p = np.asarray(p, float)
    pb = tuple(p) + tuple(p)
    inne = [d for d in delar if bbox_avstand(d.bbox, pb) == 0 and inuti(m.form(d), p) != "ut"]
    v = BRepBuilderAPI_MakeVertex(_pnt(p)).Vertex()
    kand = sorted(delar, key=lambda d: bbox_avstand(d.bbox, pb))
    nara, gräns = [], np.inf
    for d in kand:
        if bbox_avstand(d.bbox, pb) > gräns:
            break
        r = avstand(v, m.form(d))
        if r:
            nara.append((r[0], d, r[2]))
            nara.sort(key=lambda x: x[0])
            if len(nara) >= n:
                gräns = nara[n - 1][0]
    return inne, nara[:n]


def minsta_avstand(m, A, B):
    """Minsta avstånd mellan två urval: (avstånd, del a, del b, punkt a, punkt b)."""
    par = sorted(((bbox_avstand(a.bbox, b.bbox), a, b) for a in A for b in B if a.id != b.id),
                 key=lambda x: x[0])
    bast = None
    for lb, a, b in par:
        if bast and lb > bast[0]:
            break
        r = avstand(m.form(a), m.form(b))
        if r and (bast is None or r[0] < bast[0]):
            bast = (r[0], a, b, r[1], r[2])
    return bast


def krockar(m, A, B=None, minvol=1.0, framsteg=None):
    """Delpar vars solider överlappar (gemensam volym > minvol mm³): [(volym, a, b, bbox)]."""
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
    from OCP.BRepBndLib import BRepBndLib
    from OCP.BRepGProp import BRepGProp
    from OCP.Bnd import Bnd_Box
    from OCP.GProp import GProp_GProps
    A = [d for d in A if d.volym > 0]
    B = A if B is None else [d for d in B if d.volym > 0]
    ba, bb = np.array([d.bbox for d in A]), np.array([d.bbox for d in B])
    tol = 0.01
    over = ((ba[:, None, :3] < bb[None, :, 3:] - tol) & (bb[None, :, :3] < ba[:, None, 3:] - tol)).all(-1)
    par = {(min(A[i].id, B[j].id), max(A[i].id, B[j].id)) for i, j in zip(*np.nonzero(over)) if A[i].id != B[j].id}
    ut = []
    for k, (i, j) in enumerate(sorted(par)):
        if framsteg:
            framsteg(k, len(par))
        c = BRepAlgoAPI_Common(m.form(i), m.form(j))
        if not c.IsDone():
            continue
        g = GProp_GProps()
        BRepGProp.VolumeProperties_s(c.Shape(), g)
        if g.Mass() > minvol:
            b = Bnd_Box()
            BRepBndLib.Add_s(c.Shape(), b)
            ut.append((g.Mass(), m.del_(i), m.del_(j), b.CornerMin().Coord() + b.CornerMax().Coord()))
    return sorted(ut, key=lambda x: -x[0])


# ---- ytanalys ----------------------------------------------------------------------------------

def ytanalys(s):
    """Plana ytor grupperade per (normal, läge), cylindrar per (axel, radie). Exakta värden."""
    from OCP.BRepAdaptor import BRepAdaptor_Surface
    from OCP.BRepGProp import BRepGProp
    from OCP.GProp import GProp_GProps
    from OCP.GeomAbs import GeomAbs_Cylinder, GeomAbs_Plane
    from OCP.TopAbs import TopAbs_FACE, TopAbs_REVERSED
    from OCP.TopoDS import TopoDS
    plan, cyl, ovr = {}, {}, {}
    for f in _utforska(s, TopAbs_FACE):
        f = TopoDS.Face(f)
        a = BRepAdaptor_Surface(f)
        g = GProp_GProps()
        BRepGProp.SurfaceProperties_s(f, g)
        A = g.Mass()
        if a.GetType() == GeomAbs_Plane:
            pl = a.Plane()
            n = np.array(pl.Axis().Direction().Coord())
            if f.Orientation() == TopAbs_REVERSED:
                n = -n
            n = np.where(np.abs(n) < 1e-9, 0.0, n)
            d = float(np.dot(n, pl.Location().Coord()))
            k = (tuple(np.round(n, 6)), round(d, 3))
            e = plan.setdefault(k, [0, 0.0, g.CentreOfMass().Coord()])
            e[0] += 1; e[1] += A
        elif a.GetType() == GeomAbs_Cylinder:
            c = a.Cylinder()
            r = c.Radius()
            ax = np.array(c.Axis().Direction().Coord())
            if ax[np.argmax(np.abs(ax))] < 0:
                ax = -ax
            p = np.array(c.Axis().Location().Coord())
            p = p - np.dot(p, ax) * ax          # axelns punkt närmast origo (vinkelrät mot axeln)
            k = (tuple(np.round(ax, 6)), tuple(np.round(p, 3)), round(r, 4))
            e = cyl.setdefault(k, [0, 0.0])
            e[0] += 1; e[1] += A
        else:
            t = str(a.GetType()).split("_")[-1]
            e = ovr.setdefault(t, [0, 0.0])
            e[0] += 1; e[1] += A
    return plan, cyl, ovr


def horn(s):
    """Unika hörnpunkter (vertex) i formen."""
    from OCP.BRep import BRep_Tool
    from OCP.TopAbs import TopAbs_VERTEX
    from OCP.TopoDS import TopoDS
    p = np.array([BRep_Tool.Pnt_s(TopoDS.Vertex(v)).Coord() for v in _utforska(s, TopAbs_VERTEX)])
    return np.unique(np.round(p, 3), axis=0) if len(p) else p
