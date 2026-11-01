"""Kontroller av modellen: krockar (gemensam volym), kontakter (anliggande plana ytor och deras area), glipor
(minsta avstånd under en gräns) och delar utan kontakt med något annat.

Grovsållning med omslutande lådor i världen (svep längs x), sedan exakt kontroll per par i parallella processer.
Resultatet per par sparas i kärnans cache med nyckel från de två recepten och deras relativa placering, så att en
ny körning bara räknar par som ändrats.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from multiprocessing import get_context
from pathlib import Path
from typing import Any

import numpy as np

from .karna import Karna
from .modell import Del, Montage
from .placering import Placering

KONTROLL_VERSION = 2
TOL_KONTAKT = 0.01          # ytor närmare än så räknas som anliggande [mm]
TOL_KROCK = 5.0             # gemensam volym över detta är en krock [mm³]
TOL_NUMERISK = 0.01         # 0,01–5 mm³: numeriska skärvor (t.ex. mot krökta ytor), redovisas för sig
GLIPA = 2.0                 # avstånd under detta (men över TOL_KONTAKT) redovisas som glipa [mm]


@dataclass
class Resultat:
    delar: int
    par: int
    krockar: list[tuple[str, str, float]] = field(default_factory=list)       # (a, b, volym mm³)
    kontakter: list[tuple[str, str, float]] = field(default_factory=list)     # (a, b, area mm²)
    glipor: list[tuple[str, str, float]] = field(default_factory=list)        # (a, b, avstånd mm)
    fria: list[str] = field(default_factory=list)                             # delar utan kontakt
    tillatna: list[tuple[str, str, float, str]] = field(default_factory=list)  # (a, b, volym, motivering)
    skarvor: list[tuple[str, str, float]] = field(default_factory=list)        # numeriska skärvor
    sekunder: float = 0.0
    nya_par: int = 0


def _varldslada(bb: tuple[float, ...], p: Placering) -> np.ndarray:
    x0, y0, z0, x1, y1, z1 = bb
    horn = np.array([[x, y, z] for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)])
    v = horn @ np.array(p.R).T + np.array(p.t)
    return np.concatenate([v.min(0), v.max(0)])


def _parnyckel(ka: str, kb: str, rel: Placering) -> str:
    M = np.round(rel.matris()[:3], 6) + 0.0
    return hashlib.sha1(f"{KONTROLL_VERSION}|{ka}|{kb}|{M.tobytes().hex()}".encode()).hexdigest()


# ------------------------------------------------------------------ arbetsprocessen

_W: dict[str, object] = {}


def _init(cachefil: str) -> None:
    _W["db"] = sqlite3.connect(cachefil)
    _W["former"] = {}
    _W["ytor"] = {}


def _form(k: str):  # type: ignore[no-untyped-def]
    from .karna import _brep_fran_bytes
    f = _W["former"]
    if k not in f:  # type: ignore[operator]
        r = _W["db"].execute("select brep from former where nyckel = ?", (k,)).fetchone()  # type: ignore[attr-defined]
        f[k] = _brep_fran_bytes(r[0])  # type: ignore[index]
    return f[k]  # type: ignore[index]


def _plana_ytor(k: str) -> list[tuple[np.ndarray, float, Any]]:
    """Plana ytor i formens eget system: (normal utåt, d, polygon i ytans plan (shapely))."""
    yc = _W["ytor"]
    if k in yc:  # type: ignore[operator]
        return yc[k]  # type: ignore[index, no-any-return]
    from OCP.BRep import BRep_Tool
    from OCP.BRepAdaptor import BRepAdaptor_Surface
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    from OCP.GeomAbs import GeomAbs_Plane
    from OCP.TopAbs import TopAbs_FACE, TopAbs_REVERSED
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopLoc import TopLoc_Location
    from OCP.TopoDS import TopoDS
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    s = _form(k)
    BRepMesh_IncrementalMesh(s, 0.2, False, 0.2, False)
    ut = []
    ex = TopExp_Explorer(s, TopAbs_FACE)
    while ex.More():
        f = TopoDS.Face(ex.Current())
        a = BRepAdaptor_Surface(f)
        if a.GetType() == GeomAbs_Plane:
            ax = a.Plane().Axis()
            n = np.array([ax.Direction().X(), ax.Direction().Y(), ax.Direction().Z()])
            if f.Orientation() == TopAbs_REVERSED:
                n = -n
            o = ax.Location()
            d = float(n @ np.array([o.X(), o.Y(), o.Z()]))
            loc = TopLoc_Location()
            tri = BRep_Tool.Triangulation_s(f, loc)
            if tri is not None:
                tr = loc.Transformation()
                P = np.array([[(p := tri.Node(i).Transformed(tr)).X(), p.Y(), p.Z()]
                              for i in range(1, tri.NbNodes() + 1)])
                T = np.array([tri.Triangle(i).Get() for i in range(1, tri.NbTriangles() + 1)]) - 1
                u, v = _bas(n)
                Q = P @ np.column_stack([u, v])
                poly = unary_union([Polygon(Q[t]) for t in T]).buffer(0)
                ut.append((n, d, poly))
        ex.Next()
    yc[k] = ut  # type: ignore[index]
    return ut


def _bas(n: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    a = np.array([1.0, 0, 0]) if abs(n[0]) < 0.9 else np.array([0, 1.0, 0])
    u = np.cross(n, a)
    u /= np.linalg.norm(u)
    return u, np.cross(n, u)


def _kontaktarea(ka: str, kb: str, rel: Placering) -> float:
    """Area där plana ytor i A och B (B placerad med rel i A:s system) ligger an mot varandra."""
    from shapely.affinity import affine_transform
    R = np.array(rel.R)
    t = np.array(rel.t)
    A = 0.0
    yb = _plana_ytor(kb)
    for na, da, pa in _plana_ytor(ka):
        for nb0, db0, pb in yb:
            nb = R @ nb0
            if na @ nb > -1 + 1e-9:
                continue
            db = db0 + nb @ t                      # B:s plan i A:s system: nb·x = db
            if abs(da + db) > TOL_KONTAKT:
                continue
            # B:s polygon från B:s ytbas till A:s ytbas
            ub, vb = _bas(nb0)
            ua, va = _bas(na)
            # punkt i B:s plan: x = db0*nb0 + s*ub + r*vb  -> i A: R x + t -> koordinater i A:s bas
            o = R @ (db0 * nb0) + t
            m = [float((R @ ub) @ ua), float((R @ vb) @ ua), float((R @ ub) @ va), float((R @ vb) @ va),
                 float(o @ ua), float(o @ va)]
            q = affine_transform(pb, m)
            A += pa.intersection(q).area
    return A


def _avstand(sa, sb) -> float:  # type: ignore[no-untyped-def]
    from OCP.BRepExtrema import BRepExtrema_DistShapeShape
    d = BRepExtrema_DistShapeShape(sa, sb)
    d.Perform()
    return float(d.Value()) if d.IsDone() else float("nan")


def _par(uppgift: tuple[str, str, str, tuple[tuple[float, ...], ...]]) -> tuple[str, str]:
    """-> (parnyckel, json med volym, area, avstånd)."""
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
    from .karna import placerad, volym
    pk, ka, kb, M = uppgift
    rel = Placering.fran_matris(np.array(M))
    sa = _form(ka)
    sb = placerad(_form(kb), rel)
    c = BRepAlgoAPI_Common(sa, sb)
    v = volym(c.Shape()) if c.IsDone() else float("nan")
    r: dict[str, float] = {"volym": v}
    if not v > TOL_KROCK:
        r["area"] = _kontaktarea(ka, kb, rel)
        if r["area"] <= 0.5:
            r["avstand"] = _avstand(sa, sb)
    return pk, json.dumps(r)


def _jobb(paket: list[tuple[str, str, str, tuple[tuple[float, ...], ...]]]) -> list[tuple[str, str]]:
    return [_par(u) for u in paket]


# ------------------------------------------------------------------ kontrollen

def kor(rot: Montage, karna: Karna, marginal: float = GLIPA, arbetare: int | None = None,
        tillatna: dict[frozenset[str], str] | None = None) -> Resultat:
    """`tillatna`: materialpar (frozenset av två materialnamn) vars överlapp är avsiktliga, med motivering."""
    t0 = time.perf_counter()
    poster: list[tuple[str, Del, Placering]] = list(rot.platta())
    karna.forbered(d.form for _, d, _ in poster)
    nycklar = [karna.nyckel(d.form) for _, d, _ in poster]
    B = np.array([_varldslada(karna.egenskaper(d.form).bbox, p) for _, d, p in poster])
    ordning = np.argsort(B[:, 0])
    kandidater: list[tuple[int, int]] = []
    aktiva: list[int] = []
    for i in ordning:
        aktiva = [j for j in aktiva if B[j, 3] >= B[i, 0] - marginal]
        for j in aktiva:
            if np.all(B[i, 1:3] <= B[j, 4:6] + marginal) and np.all(B[j, 1:3] <= B[i, 4:6] + marginal):
                kandidater.append((min(i, j), max(i, j)))
        aktiva.append(i)
    db = karna.db
    db.execute("create table if not exists par (nyckel text primary key, resultat text)")
    uppgifter: dict[str, tuple[str, str, str, tuple[tuple[float, ...], ...]]] = {}
    parnycklar: list[str] = []
    for i, j in kandidater:
        ka, kb = nycklar[i], nycklar[j]
        pa, pb = poster[i][2], poster[j][2]
        if kb < ka:
            ka, kb, pa, pb = kb, ka, pb, pa
        rel = pa.invers() @ pb
        pk = _parnyckel(ka, kb, rel)
        parnycklar.append(pk)
        if pk not in uppgifter:
            uppgifter[pk] = (pk, ka, kb, tuple(tuple(r) for r in rel.matris().tolist()))
    kanda: dict[str, dict[str, float]] = {}
    lista = list(uppgifter)
    for k in range(0, len(lista), 500):
        del_ = lista[k:k + 500]
        for pk, js in db.execute(f"select nyckel, resultat from par where nyckel in ({','.join('?' * len(del_))})",
                                 del_):
            kanda[pk] = json.loads(js)
    saknas = [uppgifter[pk] for pk in lista if pk not in kanda]
    if saknas:
        cachefil = db.execute("pragma database_list").fetchone()[2]
        n = arbetare or max(1, (os.cpu_count() or 2) - 1)
        if len(saknas) > 40 and n > 1:
            storlek = max(4, len(saknas) // (n * 4))
            paket = [saknas[k:k + storlek] for k in range(0, len(saknas), storlek)]
            with ProcessPoolExecutor(max_workers=n, mp_context=get_context("spawn"), initializer=_init,
                                     initargs=(cachefil,)) as ex:
                res = [r for lst in ex.map(_jobb, paket) for r in lst]
        else:
            _init(cachefil)
            res = _jobb(saknas)
        with db:
            db.executemany("insert or replace into par values (?, ?)", res)
        for pk, js in res:
            kanda[pk] = json.loads(js)
    ut = Resultat(delar=len(poster), par=len(kandidater), nya_par=len(saknas))
    kontakt = np.zeros(len(poster), dtype=bool)
    kanter: list[tuple[str, str]] = []
    for (i, j), pk in zip(kandidater, parnycklar):
        r = kanda[pk]
        a, b = poster[i][0], poster[j][0]
        if r["volym"] > TOL_KROCK:
            par = frozenset((poster[i][1].material.namn, poster[j][1].material.namn))
            if tillatna and par in tillatna:
                ut.tillatna.append((a, b, r["volym"], tillatna[par]))
            else:
                ut.krockar.append((a, b, r["volym"]))
            kontakt[i] = kontakt[j] = True
        elif r.get("area", 0.0) > 0.5:
            ut.kontakter.append((a, b, r["area"]))
            if r["volym"] > TOL_NUMERISK:
                ut.skarvor.append((a, b, r["volym"]))
            kontakt[i] = kontakt[j] = True
        elif r["volym"] > TOL_NUMERISK:
            ut.skarvor.append((a, b, r["volym"]))
            kontakt[i] = kontakt[j] = True
        elif TOL_KONTAKT < r.get("avstand", 1e9) < marginal:
            ut.glipor.append((a, b, r["avstand"]))
        elif r.get("avstand", 1e9) <= TOL_KONTAKT:
            kontakt[i] = kontakt[j] = True                 # kant- eller punktkontakt
            kanter.append((a, b))
    # glipor mellan delar som båda ligger an mot en tredje del (t.ex. skikt med ett skikt emellan) redovisas inte
    grannar: dict[str, set[str]] = {}
    for a, b in [(a, b) for a, b, _ in ut.kontakter + ut.krockar] + kanter:
        grannar.setdefault(a, set()).add(b)
        grannar.setdefault(b, set()).add(a)
    ut.glipor = [(a, b, d) for a, b, d in ut.glipor if not (grannar.get(a, set()) & grannar.get(b, set()))]
    ut.fria = [poster[i][0] for i in range(len(poster)) if not kontakt[i]]
    ut.sekunder = time.perf_counter() - t0
    return ut


def rapport(r: Resultat, fil: Path | None = None) -> str:
    rader = ["# Kontroll av modellen", "",
             f"{r.delar} delar, {r.par} par nära varandra ({r.nya_par} nya), {r.sekunder:.1f} s.", "",
             f"## Krockar ({len(r.krockar)})", ""]
    rader += [f"- `{a}` och `{b}`: {v:.0f} mm³" for a, b, v in sorted(r.krockar, key=lambda x: -x[2])]
    rader += ["", f"## Tillåtna överlapp ({len(r.tillatna)})", ""]
    rader += [f"- `{a}` och `{b}`: {v:.0f} mm³ ({m})" for a, b, v, m in r.tillatna]
    rader += ["", f"## Numeriska skärvor 0,01–5 mm³ ({len(r.skarvor)})", ""]
    rader += [f"- `{a}` och `{b}`: {v:.2f} mm³" for a, b, v in r.skarvor]
    rader += ["", f"## Glipor 0,01–2 mm ({len(r.glipor)})", ""]
    rader += [f"- `{a}` och `{b}`: {d:.3f} mm" for a, b, d in sorted(r.glipor, key=lambda x: x[2])]
    rader += ["", f"## Delar utan kontakt med andra ({len(r.fria)})", ""]
    rader += [f"- `{a}`" for a in r.fria]
    rader += ["", f"## Kontakter ({len(r.kontakter)})", ""]
    rader += [f"- `{a}` och `{b}`: {A:.0f} mm²" for a, b, A in r.kontakter]
    txt = "\n".join(rader) + "\n"
    if fil:
        fil.parent.mkdir(parents=True, exist_ok=True)
        fil.write_text(txt, encoding="utf-8")
    return txt
