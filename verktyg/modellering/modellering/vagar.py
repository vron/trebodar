"""Installationernas vägar (ärende #34): att rören, kablarna och kanalerna går dolda i husets skikt, inte fritt genom
rummens luft eller genom fönstrens och takfönstrens öppningar, och inte in i volymer som ska hållas fria
(fickdörrarnas fickor). Reglerna står i modellens kontrollregler: LEDNINGAR (materialen), VAGAR_UTOM (delträd som
inte prövas, t.ex. ledningarna i marken), UTANPA (zoner där ledningarna får gå utanpå väggarna och taket), SYNLIGA
(delträd som får synas) och FRIA_VOLYMER.

Husets delar och installationernas övriga delar (dosorna, fördelarna, armaturerna, fläktarna; inte ledningarna själva
och inte armeringen) blir ett triangelnät med en sökstruktur (vtk). Varje ledningsdel
delas i kuber om STEG mm. Från punkternas mitt i varje kub mäts det fria måttet till husets ytor längs axlarna och
diagonalerna (strålar åt båda hållen, summan per riktning). Är det större än FRITT i alla riktningar står ledningen
fritt i ett rum, inte i ett skikt, ett hålrum eller en betongdel. I en UTANPA-zon är det tillåtet om ledningen går högst så långt från en yta
(utanpåliggande, en anmärkning); annars är det fel. Punkter i FRIA_VOLYMER är fel.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from types import ModuleType
from typing import Any

import numpy as np
import shapely
from shapely.geometry import Polygon
from vtkmodules.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray
from vtkmodules.vtkCommonCore import reference, vtkPoints
from vtkmodules.vtkCommonDataModel import vtkCellArray, vtkGenericCell, vtkPolyData, vtkStaticCellLocator

from .karna import Karna
from .modell import Montage

STEG = 100.0                    # ledningarnas kuber [mm]
FRITT = 400.0                   # minsta fria måttet längs en axel som räknas som rummets luft [mm]
STRALE = 3000.0                 # strålarnas längd [mm]
INSTALLATIONER = "Hus/Installationer/"
# axlarna, ytdiagonalerna och rymddiagonalerna (en åt varje håll)
RIKTNINGAR = [np.array(r, float) / np.linalg.norm(r) for r in
              ((1, 0, 0), (0, 1, 0), (0, 0, 1), (1, 1, 0), (1, -1, 0), (1, 0, 1), (1, 0, -1), (0, 1, 1), (0, 1, -1),
               (1, 1, 1), (1, 1, -1), (1, -1, 1), (1, -1, -1))]
UTOM = ("Hus/Armering",)        # husets delar som inte är ytor för vägarna (inuti betongen)


@dataclass
class Vagar:
    fel: list[str] = field(default_factory=list)
    anm: list[str] = field(default_factory=list)            # utanpåliggande, per del
    delar: int = 0
    kuber: int = 0
    sekunder: float = 0.0


class Huset:
    """Husets ytor som ett triangelnät med sökstruktur: fria mått längs axlarna och närmaste yta."""

    def __init__(self, rot: Montage, karna: Karna, ledningar: set[str]) -> None:
        V, F, self.namn, n = [], [], [], 0
        slut = [0]
        for vag, d, p in rot.platta():
            rel = vag.split("/", 1)[1]
            if d.material.namn in ledningar or rel.startswith(UTOM):
                continue
            nat = karna.nat(d.form)
            V.append(nat.V.astype(np.float64) @ np.array(p.R).T + np.array(p.t))
            F.append(nat.F.astype(np.int64) + n)
            n += len(nat.V)
            slut.append(slut[-1] + len(nat.F))
            self.namn.append(f"{d.material.namn} {rel.rsplit('/', 1)[-1]}")
        self.slut = np.array(slut)
        tri = np.concatenate(F)
        pkt = vtkPoints()
        pkt.SetData(numpy_to_vtk(np.concatenate(V), deep=True))
        celler = vtkCellArray()
        celler.SetData(numpy_to_vtkIdTypeArray(np.arange(0, 3 * len(tri) + 1, 3, dtype=np.int64), deep=True),
                       numpy_to_vtkIdTypeArray(tri.ravel(), deep=True))
        self.nat = vtkPolyData()
        self.nat.SetPoints(pkt)
        self.nat.SetPolys(celler)
        self.sok: Any = vtkStaticCellLocator()
        self.sok.SetDataSet(self.nat)
        self.sok.BuildLocator()
        self._t: Any = reference(0.0)
        self._sub: Any = reference(0)
        self._cell: Any = reference(0)
        self._x, self._pc, self._gc = [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], vtkGenericCell()

    def matt(self, c: np.ndarray, r: np.ndarray) -> float:
        """Det fria måttet genom punkten längs r (strålar åt båda hållen, högst STRALE åt vardera)."""
        summa = 0.0
        for s in (1.0, -1.0):
            q = c + s * STRALE * r
            if self.sok.IntersectWithLine(c.tolist(), q.tolist(), 0.001, self._t, self._x, self._pc, self._sub,
                                          self._cell, self._gc):
                summa += self._t.get() * STRALE
            else:
                summa += STRALE
        return summa

    def fritt(self, c: np.ndarray) -> bool:
        """Om det fria måttet genom punkten är större än FRITT i alla RIKTNINGAR: axlarna först, diagonalerna bara om
        axlarna är fria (där två tunna hålrum möts, t.ex. väggens regelfack och innertakets installationsskikt, är
        axlarna långa men diagonalen in i hörnet kort)."""
        return all(self.matt(c, r) > FRITT for r in RIKTNINGAR)

    def narmast(self, punkter: np.ndarray) -> tuple[float, str]:
        """Det kortaste avståndet från punkterna till husets ytor, och delen (material och namn)."""
        bast, del_ = np.inf, ""
        for q in punkter:
            x = [0.0, 0.0, 0.0]
            cell: Any = reference(0)
            sub: Any = reference(0)
            d2: Any = reference(0.0)
            self.sok.FindClosestPoint(q.tolist(), x, self._gc, cell, sub, d2)
            if d2.get() < bast:
                bast = d2.get()
                del_ = self.namn[int(np.searchsorted(self.slut, cell.get(), side="right")) - 1]
        return float(np.sqrt(bast)), del_


def kontrollera(rot: Montage, karna: Karna, regler: ModuleType, trad: str | None = None) -> Vagar:
    """Ledningsdelarnas vägar mot husets rum och de fria volymerna (alla installationer, eller delträdet trad)."""
    t0 = time.perf_counter()
    ut = Vagar()
    material = set(getattr(regler, "LEDNINGAR", ()))
    utom = tuple(getattr(regler, "VAGAR_UTOM", {}))
    synliga = tuple(getattr(regler, "SYNLIGA", {}))
    utanpa = sorted(getattr(regler, "UTANPA", ()), key=lambda z: z[1])
    volymer = [(namn, Polygon(yta), z0, z1) for namn, yta, z0, z1 in getattr(regler, "FRIA_VOLYMER", list)()]
    ledningar = [(vag.split("/", 1)[1], d, p) for vag, d, p in rot.platta()
                 if d.material.namn in material and vag.split("/", 1)[1].startswith(trad or INSTALLATIONER)
                 and not vag.split("/", 1)[1].startswith(utom)]
    if not ledningar:
        return ut
    huset = Huset(rot, karna, material)
    for rel, d, p in ledningar:
        nat = karna.nat(d.form)
        V = nat.V.astype(np.float64) @ np.array(p.R).T + np.array(p.t)
        C = V[nat.F.astype(np.int64)].mean(axis=1)
        namn = rel.removeprefix(INSTALLATIONER)
        for vnamn, yta, z0, z1 in volymer:
            inne = shapely.contains_xy(yta, C[:, 0], C[:, 1]) & (C[:, 2] > z0) & (C[:, 2] < z1)
            if inne.any():
                q = C[inne][0]
                ut.fel.append(f"{namn}: i {vnamn} vid ({q[0]:.0f}, {q[1]:.0f}, {q[2]:.0f})")
        _, kub = np.unique(np.floor(C / STEG).astype(np.int64), axis=0, return_inverse=True)
        kub = kub.ravel()
        ut.delar += 1
        fria: list[tuple[np.ndarray, float, str]] = []
        utanpa_max = 0.0
        for i in range(int(kub.max()) + 1):
            P = C[kub == i]
            c = P.mean(axis=0)
            ut.kuber += 1
            if rel.startswith(synliga) or not huset.fritt(c):
                continue
            avst, yta_ = huset.narmast(P[:: max(1, len(P) // 16)])
            zon = next((z for z in utanpa if c[2] < z[1]), None)
            if zon is not None and avst <= zon[2]:
                utanpa_max = max(utanpa_max, avst)
            else:
                fria.append((c, avst, yta_))
        if fria:
            c, avst, yta_ = max(fria, key=lambda f: f[1])
            ut.fel.append(f"{namn}: fritt i rummet ({len(fria) * STEG / 1000:.1f} m), vid ({c[0]:.0f}, {c[1]:.0f}, "
                          f"{c[2]:.0f}) {avst:.0f} mm från närmaste yta ({yta_})")
        if utanpa_max > 0.0:
            ut.anm.append(f"{namn}: utanpåliggande, högst {utanpa_max:.0f} mm från ytan")
    ut.sekunder = time.perf_counter() - t0
    return ut
