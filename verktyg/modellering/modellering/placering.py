"""Placering: stel transform (rotation + förflyttning) i mm. Punkten i föräldern = R · lokal + t."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

import numpy as np

Vek = tuple[float, float, float]
Rot = tuple[Vek, Vek, Vek]

_AXEL: dict[str, Vek] = {"x": (1.0, 0.0, 0.0), "y": (0.0, 1.0, 0.0), "z": (0.0, 0.0, 1.0),
                         "-x": (-1.0, 0.0, 0.0), "-y": (0.0, -1.0, 0.0), "-z": (0.0, 0.0, -1.0)}


def vek(v: Sequence[float] | str) -> np.ndarray:
    """Riktning som numpy-vektor; "x", "-y" osv. går också."""
    return np.array(_AXEL[v] if isinstance(v, str) else v, dtype=float)


def _cos_sin(grader: float) -> tuple[float, float]:
    """cos och sin, exakta för multiplar av 90°."""
    q = grader / 90.0
    if abs(q - round(q)) < 1e-12:
        return [(1.0, 0.0), (0.0, 1.0), (-1.0, 0.0), (0.0, -1.0)][round(q) % 4]
    r = math.radians(grader)
    return math.cos(r), math.sin(r)


def _rot(R: np.ndarray) -> Rot:
    R = np.where(np.abs(R) < 1e-15, 0.0, R)
    return (tuple(float(v) for v in R[0]), tuple(float(v) for v in R[1]),  # type: ignore[return-value]
            tuple(float(v) for v in R[2]))


def _v(a: np.ndarray | Sequence[float]) -> Vek:
    return (float(a[0]), float(a[1]), float(a[2]))


@dataclass(frozen=True)
class Placering:
    """Stel transform. `a @ b` betyder först b, sedan a."""
    R: Rot = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    t: Vek = (0.0, 0.0, 0.0)

    @staticmethod
    def flytt(x: float = 0.0, y: float = 0.0, z: float = 0.0) -> Placering:
        return Placering(t=(float(x), float(y), float(z)))

    @staticmethod
    def rot(axel: Sequence[float] | str, grader: float, kring: Sequence[float] = (0.0, 0.0, 0.0)) -> Placering:
        """Rotation `grader` (högerhandsregeln) kring en axel genom punkten `kring`."""
        a = vek(axel)
        a = a / np.linalg.norm(a)
        c, s = _cos_sin(grader)
        K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
        R = np.eye(3) * c + s * K + (1 - c) * np.outer(a, a)
        p = np.array(kring, dtype=float)
        return Placering(_rot(R), _v(p - R @ p))

    @staticmethod
    def axlar(origo: Sequence[float], x: Sequence[float] | str, z: Sequence[float] | str) -> Placering:
        """Lokalt system med origo och riktningarna för lokala x och z i föräldern (z görs vinkelrät mot x);
        y = z × x."""
        ex = vek(x)
        ex = ex / np.linalg.norm(ex)
        ez = vek(z)
        ez = ez - (ez @ ex) * ex
        ez = ez / np.linalg.norm(ez)
        ey = np.cross(ez, ex)
        return Placering(_rot(np.column_stack([ex, ey, ez])), _v(origo))

    @staticmethod
    def fran_matris(M: np.ndarray | Sequence[Sequence[float]]) -> Placering:
        A = np.asarray(M, dtype=float)
        return Placering(_rot(A[:3, :3]), _v(A[:3, 3]))

    def __matmul__(self, o: Placering) -> Placering:
        R1, R2 = np.array(self.R), np.array(o.R)
        return Placering(_rot(R1 @ R2), _v(R1 @ np.array(o.t) + np.array(self.t)))

    def punkt(self, p: Sequence[float]) -> Vek:
        """Punkt i lokala koordinater -> föräldern."""
        return _v(np.array(self.R) @ np.array(p, dtype=float) + np.array(self.t))

    def riktning(self, v: Sequence[float] | str) -> Vek:
        """Riktning i lokala koordinater -> föräldern (utan förflyttning)."""
        return _v(np.array(self.R) @ vek(v))

    def matris(self) -> np.ndarray:
        M = np.eye(4)
        M[:3, :3] = self.R
        M[:3, 3] = self.t
        return M

    def invers(self) -> Placering:
        R = np.array(self.R).T
        return Placering(_rot(R), _v(-R @ np.array(self.t)))

    def ar_identitet(self, tol: float = 1e-12) -> bool:
        return bool(np.allclose(self.matris(), np.eye(4), atol=tol))


IDENTITET = Placering()
flytt = Placering.flytt
rot = Placering.rot
axlar = Placering.axlar
