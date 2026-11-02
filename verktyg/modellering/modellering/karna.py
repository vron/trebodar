"""Kärnan: recept -> OCCT B-rep, egenskaper och triangelnät, med beständig cache och parallell beräkning.

Varje unikt recept (nyckel = hash av receptet) byggs en gång. Resultatet (B-rep i OCCT:s binärformat, egenskaper
och triangelnät) sparas i en SQLite-fil, så nästa körning bara bygger det som ändrats. Saknade recept byggs i
parallella processer (ett recept per uppgift, alla kärnor) när de är många, annars i den egna processen.
"""
from __future__ import annotations

import io
import json
import math
import os
import sqlite3
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass
from multiprocessing import get_context
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
from OCP.Bnd import Bnd_Box, Bnd_OBB
from OCP.BinTools import BinTools
from OCP.BRep import BRep_Builder, BRep_Tool
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common, BRepAlgoAPI_Cut, BRepAlgoAPI_Fuse
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepBuilderAPI import (BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeFace, BRepBuilderAPI_MakePolygon,
                                BRepBuilderAPI_MakeSolid, BRepBuilderAPI_MakeWire, BRepBuilderAPI_Sewing,
                                BRepBuilderAPI_Transform)
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepGProp import BRepGProp
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder, BRepPrimAPI_MakePrism, BRepPrimAPI_MakeRevol
from OCP.BRepTools import BRepTools
from OCP.GeomAPI import GeomAPI_Interpolate
from OCP.gp import gp_Ax1, gp_Ax2, gp_Circ, gp_Dir, gp_Pnt, gp_Trsf, gp_Vec
from OCP.GProp import GProp_GProps
from OCP.ShapeFix import ShapeFix_Solid
from OCP.TopAbs import TopAbs_FACE, TopAbs_REVERSED, TopAbs_SHELL, TopAbs_SOLID
from OCP.TopExp import TopExp_Explorer
from OCP.TopLoc import TopLoc_Location
from OCP.TopoDS import TopoDS, TopoDS_Shape
from OCP.collections import HArray1_gp_Pnt, List_TopoDS_Shape

from . import form as F
from .placering import Placering

KARNA_VERSION = 2              # höj när byggandet av former ändras (ogiltigförklarar cachen)
ROT = Path(__file__).resolve().parents[3]                       # repots rot
STANDARD_CACHE = Path(__file__).resolve().parents[1] / ".cache" / "former.sqlite"
NAT_KORDA = 0.5                # triangulering: största kordavvikelse [mm], minst; större för stora delar
NAT_KORDA_REL = 0.0005         # ... som andel av delens diagonal
NAT_VINKEL = 0.3               # triangulering: största vinkelavvikelse [rad]
FUZZY = 1e-6                   # toleransen i booleska operationer [mm]


# ------------------------------------------------------------------ OCCT-hjälp

def trsf(p: Placering) -> gp_Trsf:
    t = gp_Trsf()
    R, v = p.R, p.t
    t.SetValues(R[0][0], R[0][1], R[0][2], v[0], R[1][0], R[1][1], R[1][2], v[1], R[2][0], R[2][1], R[2][2], v[2])
    return t


def placerad(s: TopoDS_Shape, p: Placering) -> TopoDS_Shape:
    """Formen flyttad (delar geometri med originalet)."""
    return s if p.ar_identitet() else s.Moved(TopLoc_Location(trsf(p)))


def bbox(s: TopoDS_Shape, optimal: bool = True) -> tuple[float, float, float, float, float, float]:
    b = Bnd_Box()
    if optimal:
        BRepBndLib.AddOptimal_s(s, b, False, False)
    else:
        BRepBndLib.Add_s(s, b, True)
    mn, mx = b.CornerMin(), b.CornerMax()
    return (mn.X(), mn.Y(), mn.Z(), mx.X(), mx.Y(), mx.Z())


def volym(s: TopoDS_Shape) -> float:
    g = GProp_GProps()
    BRepGProp.VolumeProperties_s(s, g)
    return float(g.Mass())


def _polygon(pts: Sequence[F.P2]) -> object:
    poly = BRepBuilderAPI_MakePolygon()
    for x, y in pts:
        poly.Add(gp_Pnt(x, y, 0.0))
    poly.Close()
    return poly.Wire()


def _area(pts: Sequence[F.P2]) -> float:
    a = np.asarray(pts, dtype=float)
    return float(0.5 * np.sum(a[:, 0] * np.roll(a[:, 1], -1) - np.roll(a[:, 0], -1) * a[:, 1]))


def _cirkel(x: float, y: float, d: float) -> object:
    c = gp_Circ(gp_Ax2(gp_Pnt(x, y, 0.0), gp_Dir(0, 0, -1)), d / 2)    # medurs sett ovanifrån: hål
    return BRepBuilderAPI_MakeWire(BRepBuilderAPI_MakeEdge(c).Edge()).Wire()


def _bool(op: type, a: TopoDS_Shape, verktyg: list[TopoDS_Shape]) -> TopoDS_Shape:
    alg = op()
    la, lb = List_TopoDS_Shape(), List_TopoDS_Shape()
    la.Append(a)
    for v in verktyg:
        lb.Append(v)
    alg.SetArguments(la)
    alg.SetTools(lb)
    alg.SetFuzzyValue(FUZZY)
    alg.SetRunParallel(False)
    alg.Build()
    if not alg.IsDone():
        raise RuntimeError("boolesk operation misslyckades")
    alg.SimplifyResult()
    return alg.Shape()


_MINNE: dict[str, TopoDS_Shape] = {}


def bygg(f: F.Form) -> TopoDS_Shape:
    """Receptet som B-rep (minnescache i processen)."""
    k = f.nyckel()
    s = _MINNE.get(k)
    if s is None:
        s = _bygg(f)
        _MINNE[k] = s
    return s


def _bygg(f: F.Form) -> TopoDS_Shape:
    if isinstance(f, F.Lada):
        o = f.origo
        return BRepPrimAPI_MakeBox(gp_Pnt(*o), gp_Pnt(o[0] + f.dx, o[1] + f.dy, o[2] + f.dz)).Shape()
    if isinstance(f, F.Prisma):
        yttre = f.kontur if _area(f.kontur) > 0 else tuple(reversed(f.kontur))
        mf = BRepBuilderAPI_MakeFace(_polygon(yttre), True)
        for h in f.hal:
            mf.Add(_polygon(h if _area(h) < 0 else tuple(reversed(h))))
        for x, y, d in f.cirkelhal:
            mf.Add(_cirkel(x, y, d))
        s = BRepPrimAPI_MakePrism(mf.Face(), gp_Vec(0, 0, f.tjocklek)).Shape()
        if f.z0:
            s = BRepBuilderAPI_Transform(s, trsf(Placering.flytt(z=f.z0)), True).Shape()
        return s
    if isinstance(f, F.Cylinder):
        return BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(*f.origo), gp_Dir(0, 0, 1)), f.radie, f.hojd).Shape()
    if isinstance(f, F.Polyeder):
        return _polyeder(f)
    if isinstance(f, F.Varv):
        return _varv(f)
    if isinstance(f, F.Transf):
        return BRepBuilderAPI_Transform(bygg(f.form), trsf(f.placering), True).Shape()
    if isinstance(f, F.Diff):
        return _bool(BRepAlgoAPI_Cut, bygg(f.bas), [bygg(v) for v in f.verktyg])
    if isinstance(f, F.Union):
        return _bool(BRepAlgoAPI_Fuse, bygg(f.delar[0]), [bygg(v) for v in f.delar[1:]])
    if isinstance(f, F.Snitt):
        return _bool(BRepAlgoAPI_Common, bygg(f.delar[0]), [bygg(v) for v in f.delar[1:]])
    if isinstance(f, F.Kapad):
        s = bygg(f.form)
        b = bbox(s, optimal=False)
        L = 4 * max(b[3] - b[0], b[4] - b[1], b[5] - b[2], 1.0) + 1000
        p = Placering.axlar(f.punkt, _vinkelratt(f.normal), f.normal)
        halvrum = BRepBuilderAPI_Transform(BRepPrimAPI_MakeBox(gp_Pnt(-L, -L, 0), gp_Pnt(L, L, L)).Shape(),
                                           trsf(p), True).Shape()
        return _bool(BRepAlgoAPI_Cut, s, [halvrum])
    if isinstance(f, F.Speglad):
        t = gp_Trsf()
        t.SetMirror(gp_Ax2(gp_Pnt(*f.punkt), gp_Dir(*f.normal)))
        return BRepBuilderAPI_Transform(bygg(f.form), t, True).Shape()
    if isinstance(f, F.Importerad):
        s = TopoDS_Shape()
        fil = ROT / f.fil
        if fil.suffix == ".bbrep":
            BinTools.Read_s(s, str(fil))
        else:
            BRepTools.Read_s(s, str(fil), BRep_Builder())
        return s
    raise TypeError(f"okänt recept: {type(f).__name__}")


def _varv(f: F.Varv) -> TopoDS_Shape:
    """Profilen i xz-planet (x = r) som en yta, raka kanter och splinekurvor, vriden ett varv kring z."""
    mw = BRepBuilderAPI_MakeWire()
    for typ, pts in f.profil:
        p3 = [gp_Pnt(r, 0.0, z) for r, z in pts]
        if typ == "linje":
            for a, b in zip(p3, p3[1:]):
                mw.Add(BRepBuilderAPI_MakeEdge(a, b).Edge())
            continue
        arr = HArray1_gp_Pnt(1, len(p3))
        for i, p in enumerate(p3, 1):
            arr.SetValue(i, p)
        ip = GeomAPI_Interpolate(arr, False, 1e-6)
        ip.Perform()
        if not ip.IsDone():
            raise RuntimeError("profilens kurva kunde inte interpoleras")
        mw.Add(BRepBuilderAPI_MakeEdge(ip.Curve()).Edge())
    if not mw.IsDone():
        raise RuntimeError("profilen blev ingen sluten kontur")
    yta = BRepBuilderAPI_MakeFace(mw.Wire(), True).Face()
    return BRepPrimAPI_MakeRevol(yta, gp_Ax1(gp_Pnt(0.0, 0.0, 0.0), gp_Dir(0.0, 0.0, 1.0)), 2 * math.pi).Shape()


def _polyeder(f: F.Polyeder) -> TopoDS_Shape:
    """Plana ytor ur hörnen, sydda till ett skal och en solid med utåtvända ytor."""
    sy = BRepBuilderAPI_Sewing(1e-4)
    for yta in f.ytor:
        poly = BRepBuilderAPI_MakePolygon()
        for i in yta:
            poly.Add(gp_Pnt(*f.horn[i]))
        poly.Close()
        sy.Add(BRepBuilderAPI_MakeFace(poly.Wire(), True).Face())
    sy.Perform()
    ex = TopExp_Explorer(sy.SewedShape(), TopAbs_SHELL)
    if not ex.More():
        raise RuntimeError("polyedern blev inget skal")
    fix = ShapeFix_Solid(BRepBuilderAPI_MakeSolid(TopoDS.Shell(ex.Current())).Solid())
    fix.Perform()
    return fix.Solid()


def _vinkelratt(n: Sequence[float]) -> tuple[float, float, float]:
    v = np.array(n, dtype=float)
    a = np.array([1.0, 0, 0]) if abs(v[0]) < 0.9 else np.array([0, 1.0, 0])
    u = np.cross(v, a)
    u /= np.linalg.norm(u)
    return (float(u[0]), float(u[1]), float(u[2]))


# ------------------------------------------------------------------ egenskaper och nät

@dataclass(frozen=True)
class Egenskaper:
    volym: float                                  # mm³
    area: float                                   # mm²
    bbox: tuple[float, float, float, float, float, float]    # i delens eget system
    tyngdpunkt: tuple[float, float, float]
    matt: tuple[float, float, float]              # minsta omslutande låda, längst först (materiallistan)
    solider: int
    giltig: bool


@dataclass(frozen=True)
class Nat:
    V: np.ndarray                                 # (n, 3) float32, mm
    N: np.ndarray                                 # (n, 3) float32
    F: np.ndarray                                 # (m, 3) uint32
    Y: np.ndarray                                 # (m,) uint32, ytans index per triangel


def _matt(f: F.Form, s: TopoDS_Shape) -> tuple[float, float, float]:
    """Kapmått: exakt för rätblock och prismor (minsta rektangel kring profilen), annars OCCT:s OBB. En union
    får basens (första delens) mått, t.ex. en plåt med falsar."""
    g = f
    while isinstance(g, (F.Transf, F.Union)):
        g = g.form if isinstance(g, F.Transf) else g.delar[0]
    if isinstance(g, F.Lada):
        d = [g.dx, g.dy, g.dz]
    elif isinstance(g, F.Prisma):
        d = [*_minsta_rektangel(np.asarray(g.kontur, dtype=float)), g.tjocklek]
    elif isinstance(g, (F.Diff, F.Kapad)) and isinstance(_bas(g), (F.Lada, F.Prisma)):
        d = list(_matt(_bas(g), s))
    else:
        o = Bnd_OBB()
        BRepBndLib.AddOBB_s(s, o, False, True, False)
        d = [2 * o.XHSize(), 2 * o.YHSize(), 2 * o.ZHSize()]
    a, b, c = sorted((round(float(v), 3) for v in d), reverse=True)
    return (a, b, c)


def _bas(g: F.Form) -> F.Form:
    while isinstance(g, (F.Diff, F.Kapad, F.Transf)):
        g = g.bas if isinstance(g, F.Diff) else g.form
    return g


def _minsta_rektangel(P: np.ndarray) -> tuple[float, float]:
    """Minsta omslutande rektangel (sidor längs konvexa höljets kanter)."""
    best = (math.inf, 0.0, 0.0)
    n = len(P)
    for i in range(n):
        e = P[(i + 1) % n] - P[i]
        L = float(np.hypot(*e))
        if L < 1e-9:
            continue
        u = e / L
        v = np.array([-u[1], u[0]])
        a, b = P @ u, P @ v
        w, h = float(a.max() - a.min()), float(b.max() - b.min())
        if w * h < best[0] - 1e-9:
            best = (w * h, w, h)
    return best[1], best[2]


def egenskaper(f: F.Form, s: TopoDS_Shape) -> Egenskaper:
    g = GProp_GProps()
    BRepGProp.VolumeProperties_s(s, g)
    c = g.CentreOfMass()
    ga = GProp_GProps()
    BRepGProp.SurfaceProperties_s(s, ga)
    n = 0
    ex = TopExp_Explorer(s, TopAbs_SOLID)
    while ex.More():
        n += 1
        ex.Next()
    return Egenskaper(volym=float(g.Mass()), area=float(ga.Mass()), bbox=bbox(s),
                      tyngdpunkt=(c.X(), c.Y(), c.Z()), matt=_matt(f, s), solider=n,
                      giltig=bool(BRepCheck_Analyzer(s).IsValid()) and g.Mass() > 0)


def triangulera(s: TopoDS_Shape) -> Nat:
    """Triangelnät med egna hörn per yta (skarpa kanter). Kordavvikelsen växer med delens storlek; vinkelgränsen
    ger ändå minst ~20 segment per cirkel."""
    b = bbox(s, optimal=False)
    diag = math.dist(b[:3], b[3:])
    BRepMesh_IncrementalMesh(s, max(NAT_KORDA, NAT_KORDA_REL * diag), False, NAT_VINKEL, False)
    V, N, Fs, Y = [], [], [], []
    nv = 0
    ex = TopExp_Explorer(s, TopAbs_FACE)
    i = 0
    while ex.More():
        f = TopoDS.Face(ex.Current())
        loc = TopLoc_Location()
        tri = BRep_Tool.Triangulation_s(f, loc)
        if tri is not None and tri.NbTriangles() > 0:
            tr = loc.Transformation()
            pts = np.array([[(p := tri.Node(k).Transformed(tr)).X(), p.Y(), p.Z()]
                            for k in range(1, tri.NbNodes() + 1)])
            T = np.array([tri.Triangle(k).Get() for k in range(1, tri.NbTriangles() + 1)]) - 1
            if f.Orientation() == TopAbs_REVERSED:
                T = T[:, ::-1]
            nrm = np.cross(pts[T[:, 1]] - pts[T[:, 0]], pts[T[:, 2]] - pts[T[:, 0]])
            vn = np.zeros_like(pts)
            for k in range(3):
                np.add.at(vn, T[:, k], nrm)
            vn /= np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-30)
            V.append(pts)
            N.append(vn)
            Fs.append(T + nv)
            Y.append(np.full(len(T), i))
            nv += len(pts)
        i += 1
        ex.Next()
    if not V:
        z = np.zeros((0, 3))
        return Nat(z.astype(np.float32), z.astype(np.float32), z.astype(np.uint32), np.zeros(0, np.uint32))
    return Nat(np.vstack(V).astype(np.float32), np.vstack(N).astype(np.float32),
               np.vstack(Fs).astype(np.uint32), np.concatenate(Y).astype(np.uint32))


def _brep_till_bytes(s: TopoDS_Shape) -> bytes:
    b = io.BytesIO()
    BinTools.Write_s(s, b)
    return b.getvalue()


def brep_fran_bytes(data: bytes) -> TopoDS_Shape:
    s = TopoDS_Shape()
    BinTools.Read_s(s, io.BytesIO(data))
    return s


def _nat_till_bytes(n: Nat) -> bytes:
    b = io.BytesIO()
    np.savez(b, V=n.V, N=n.N, F=n.F, Y=n.Y)
    return b.getvalue()


def _nat_fran_bytes(data: bytes) -> Nat:
    z = np.load(io.BytesIO(data))
    return Nat(z["V"], z["N"], z["F"], z["Y"])


def _jobb(uppgift: tuple[str, F.Form]) -> tuple[str, bytes, str, bytes, float]:
    """Arbetsprocessens uppgift: bygg receptet, beräkna egenskaper och nät."""
    nyckel, f = uppgift
    t0 = time.perf_counter()
    s = bygg(f)
    e = egenskaper(f, s)
    n = triangulera(s)
    return nyckel, _brep_till_bytes(s), json.dumps(asdict(e)), _nat_till_bytes(n), time.perf_counter() - t0


# ------------------------------------------------------------------ cachen

class Karna:
    """Bygger recept med beständig cache. `forbered` bygger alla saknade recept (parallellt om de är många)."""

    def __init__(self, cachefil: Path = STANDARD_CACHE, arbetare: int | None = None, parallellgrans: int = 24):
        cachefil.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(cachefil))
        self.db.execute("create table if not exists former (nyckel text primary key, brep blob, "
                        "egenskaper text, nat blob)")
        self.arbetare = arbetare or max(1, (os.cpu_count() or 2) - 1)
        self.parallellgrans = parallellgrans
        self._former: dict[str, TopoDS_Shape] = {}
        self._egenskaper: dict[str, Egenskaper] = {}
        self._nat: dict[str, Nat] = {}
        self.statistik = {"byggda": 0, "cachade": 0, "sekunder": 0.0}

    @staticmethod
    def nyckel(f: F.Form) -> str:
        return f"{KARNA_VERSION}-{f.nyckel()}"

    def forbered(self, former: Iterable[F.Form]) -> None:
        t0 = time.perf_counter()
        unika: dict[str, F.Form] = {}
        for f in former:
            unika.setdefault(self.nyckel(f), f)
        kanda: set[str] = set()
        nycklar = list(unika)
        for i in range(0, len(nycklar), 500):
            del_ = nycklar[i:i + 500]
            q = f"select nyckel from former where nyckel in ({','.join('?' * len(del_))})"
            kanda.update(r[0] for r in self.db.execute(q, del_))
        saknas = [(k, unika[k]) for k in nycklar if k not in kanda]
        self.statistik["cachade"] += len(unika) - len(saknas)
        if saknas:
            if len(saknas) >= self.parallellgrans and self.arbetare > 1:
                with ProcessPoolExecutor(max_workers=min(self.arbetare, len(saknas)),
                                         mp_context=get_context("spawn")) as ex:
                    resultat = list(ex.map(_jobb, saknas, chunksize=max(1, len(saknas) // (4 * self.arbetare))))
            else:
                resultat = [_jobb(u) for u in saknas]
            with self.db:
                self.db.executemany("insert or replace into former values (?, ?, ?, ?)",
                                    [(k, b, e, n) for k, b, e, n, _ in resultat])
            self.statistik["byggda"] += len(saknas)
        self.statistik["sekunder"] += time.perf_counter() - t0

    def _rad(self, k: str, kolumn: str) -> bytes | str:
        r = self.db.execute(f"select {kolumn} from former where nyckel = ?", (k,)).fetchone()
        if r is None:
            raise KeyError(k)
        return r[0]  # type: ignore[no-any-return]

    def _sakra(self, f: F.Form) -> str:
        k = self.nyckel(f)
        if k not in self._egenskaper and self.db.execute("select 1 from former where nyckel = ?",
                                                          (k,)).fetchone() is None:
            self.forbered([f])
        return k

    def form(self, f: F.Form) -> TopoDS_Shape:
        k = self._sakra(f)
        if k not in self._former:
            self._former[k] = brep_fran_bytes(self._rad(k, "brep"))  # type: ignore[arg-type]
        return self._former[k]

    def egenskaper(self, f: F.Form) -> Egenskaper:
        k = self._sakra(f)
        if k not in self._egenskaper:
            d = json.loads(self._rad(k, "egenskaper"))
            self._egenskaper[k] = Egenskaper(volym=float(d["volym"]), area=float(d["area"]), bbox=tuple(d["bbox"]),
                                             tyngdpunkt=tuple(d["tyngdpunkt"]), matt=tuple(d["matt"]),
                                             solider=int(d["solider"]), giltig=bool(d["giltig"]))
        return self._egenskaper[k]

    def nat(self, f: F.Form) -> Nat:
        k = self._sakra(f)
        if k not in self._nat:
            self._nat[k] = _nat_fran_bytes(self._rad(k, "nat"))  # type: ignore[arg-type]
        return self._nat[k]
