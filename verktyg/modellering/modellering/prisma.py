"""Känn igen prismor: en solid med bara plana ytor där alla ytor utom två (botten och topp) är parallella med en
riktning. Ger profilen (polygon med hål) i ett plan vinkelrätt mot riktningen och tjockleksintervallet."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
from OCP.BRep import BRep_Tool
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.BRepTools import BRepTools_WireExplorer
from OCP.GeomAbs import GeomAbs_Plane
from OCP.TopAbs import TopAbs_FACE, TopAbs_REVERSED, TopAbs_WIRE
from OCP.TopExp import TopExp_Explorer
from OCP.TopoDS import TopoDS, TopoDS_Shape

from .placering import Placering


@dataclass(frozen=True)
class PrismaInfo:
    axel: tuple[float, float, float]          # extrusionsriktning (enhetsvektor) i formens system
    u: tuple[float, float, float]             # profilens första axel
    v: tuple[float, float, float]             # profilens andra axel (u × v = axel)
    w0: float                                 # tjockleksintervall längs axeln
    w1: float
    yttre: tuple[tuple[float, float], ...]    # profilens yttre kontur (moturs i (u, v))
    hal: tuple[tuple[tuple[float, float], ...], ...]

    def placering(self) -> Placering:
        """Profilens system (u, v, axel) i formens system, origo i formens origo."""
        R = np.column_stack([self.u, self.v, self.axel])
        return Placering.fran_matris(np.vstack([np.column_stack([R, [0, 0, 0]]), [0, 0, 0, 1]]))


def _ytor(s: TopoDS_Shape) -> list[tuple[object, np.ndarray, float]] | None:
    ut = []
    ex = TopExp_Explorer(s, TopAbs_FACE)
    while ex.More():
        f = TopoDS.Face(ex.Current())
        a = BRepAdaptor_Surface(f)
        if a.GetType() != GeomAbs_Plane:
            return None
        ax = a.Plane().Axis()
        d, o = ax.Direction(), ax.Location()
        n = np.array([d.X(), d.Y(), d.Z()])
        if f.Orientation() == TopAbs_REVERSED:
            n = -n
        ut.append((f, n, float(n @ np.array([o.X(), o.Y(), o.Z()]))))
        ex.Next()
    return ut


def _area(p: np.ndarray) -> float:
    return float(0.5 * np.sum(p[:, 0] * np.roll(p[:, 1], -1) - np.roll(p[:, 0], -1) * p[:, 1]))


def _rensa(p: list[tuple[float, float]], tol: float = 1e-7) -> list[tuple[float, float]]:
    """Ta bort upprepade och kolinjära hörn."""
    q = [pt for i, pt in enumerate(p) if np.hypot(pt[0] - p[i - 1][0], pt[1] - p[i - 1][1]) > tol]
    ut = []
    n = len(q)
    for i in range(n):
        a, b, c = np.array(q[i - 1]), np.array(q[i]), np.array(q[(i + 1) % n])
        e, f = b - a, c - b
        if abs(e[0] * f[1] - e[1] * f[0]) > tol * max(1.0, float(np.linalg.norm(e) * np.linalg.norm(f))):
            ut.append(q[i])
    return ut


def kann_igen(s: TopoDS_Shape, kandidater: Sequence[Sequence[float]] | None = None) -> PrismaInfo | None:
    """Prismainformation om formen är ett prisma längs någon av kandidatriktningarna (standard: ytornas normaler)."""
    ytor = _ytor(s)
    if ytor is None:
        return None
    normaler = [n for _, n, _ in ytor]
    riktningar = [np.asarray(k, float) / np.linalg.norm(k) for k in kandidater] if kandidater else normaler
    provade: list[np.ndarray] = []
    for a in riktningar:
        if any(abs(abs(a @ p) - 1) < 1e-9 for p in provade):
            continue
        provade.append(a)
        if any(1e-9 < abs(n @ a) < 1 - 1e-9 for n in normaler):
            continue
        lock = [(f, n, d) for f, n, d in ytor if abs(abs(n @ a) - 1) < 1e-9]
        botten = [(f, n, d) for f, n, d in lock if n @ a < 0]
        topp = [(f, n, d) for f, n, d in lock if n @ a > 0]
        if len(botten) != 1 or len(topp) != 1:
            continue
        w0 = -botten[0][2]
        w1 = topp[0][2]
        # profilens axlar: u vinkelrät mot a (helst längs en världsaxel), v = a × u
        e = np.eye(3)
        k = int(np.argmin([abs(a @ ei) for ei in e]))
        u = e[k] - (e[k] @ a) * a
        u /= np.linalg.norm(u)
        # välj u längs den världsaxel som ligger i planet om någon gör det
        for ei in e:
            if abs(ei @ a) < 1e-12:
                u = ei.copy()
                break
        v = np.cross(a, u)
        slingor = []
        wex = TopExp_Explorer(botten[0][0], TopAbs_WIRE)
        while wex.More():
            we = BRepTools_WireExplorer(TopoDS.Wire(wex.Current()), TopoDS.Face(botten[0][0]))
            pts = []
            while we.More():
                p = BRep_Tool.Pnt_s(we.CurrentVertex())
                c = np.array([p.X(), p.Y(), p.Z()])
                pts.append((float(c @ u), float(c @ v)))
                we.Next()
            slingor.append(_rensa(pts))
            wex.Next()
        slingor.sort(key=lambda p: -abs(_area(np.array(p))))
        yttre = slingor[0] if _area(np.array(slingor[0])) > 0 else slingor[0][::-1]
        hal = tuple(tuple(h if _area(np.array(h)) < 0 else h[::-1]) for h in slingor[1:])
        return PrismaInfo(tuple(map(float, a)), tuple(map(float, u)), tuple(map(float, v)), w0, w1,  # type: ignore[arg-type]
                          tuple(yttre), hal)
    return None
