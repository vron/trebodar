"""Ytskiktens språng och springor (ärende #36): de synliga ytorna av ytskiktens material (YTSKIKT i modellens
kontrollregler: gipsen, kaklet, kaminens målade front) ska vara jämna där två skivor möts i samma plan. Reglerna:
YTSKIKT (materialen) och YTSKIKT_UTOM (delar vars ytor får ha språng eller springor, med motivering).

Varje dels plana ytor (kärnans nät, trianglarna per B-rep-yta) i husets koordinater. En yta av ett ytskiktsmaterial
är synlig där ingen annan del ligger an mot den (en yta i samma plan med motsatt normal), och räknas om den synliga
delen är minst BREDD bred (skivornas kanter räknas inte). Två synliga ytor av olika delar med samma normal:

- språng: de möts (mindre än MOTS mm emellan i planet, längs minst LANGD mm) men ligger SPRANG–SPRANG_MAX mm från
  varandra längs normalen, så att den ena skivan står ut;
- springa: de ligger i samma plan med SPRINGA–SPRINGA_MAX mm emellan, och ingen annan del har en yta i planet som
  fyller springan (en smyg eller list i liv med skivorna).

Och två synliga ytor med vinkelräta normaler i ett inåthörn (#107): båda når ut i rummet framför den andra, den ena
får gå förbi hörnlinjen in bakom den andra väggens skikt (högst FORBI), och en springa är där den andra slutar
SPRINGA–SPRINGA_MAX mm före hörnlinjen längs minst LANGD, utan någon annan del i dess plan som fyller remsan.
"""
from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from collections.abc import Callable
from types import ModuleType

import numpy as np
import shapely
from shapely.geometry import Point, Polygon
from shapely.geometry.base import BaseGeometry

from .karna import Karna
from .modell import Montage
from .vagar import Huset

SPRANG, SPRANG_MAX = 0.3, 40.0          # språng längs normalen [mm]
SPRINGA, SPRINGA_MAX = 0.5, 30.0        # springor i planet [mm]
MOTS = 1.0                              # ytorna möts: så nära i planet [mm]
LANGD = 50.0                            # minsta längd där ytorna möts (språng) eller står mot varandra (springa)
BREDD = 30.0                            # minsta bredd på en synlig yta [mm]
PLAN = 0.2                              # samma plan [mm]
PROV = 5.0                              # rummets luft så långt framför ytan [mm]
RUM = 150.0                             # rummets luft: minst så fritt längs axlarna genom punkten [mm]
NORMAL = 1e-3                           # samma normal (avrundning)
FORBI = 60.0                            # i ett inåthörn går den ena ytan högst så långt förbi hörnlinjen [mm]
UTOM = ("Hus/Armering", "Hus/Installationer")   # delar som inte täcker ytorna (i betongen, genom skikten)


@dataclass
class Ytor:
    fel: list[str] = field(default_factory=list)
    ytor: int = 0                       # synliga ytor av ytskiktens material
    sekunder: float = 0.0


def _bas(n: np.ndarray) -> np.ndarray:
    """Två axlar i planet med normalen n (3 × 2)."""
    a = np.array([1.0, 0.0, 0.0]) if abs(n[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    e1 = np.cross(n, a)
    e1 /= np.linalg.norm(e1)
    return np.column_stack([e1, np.cross(n, e1)])


def _plana(V: np.ndarray, F: np.ndarray, Y: np.ndarray) -> list[tuple[np.ndarray, float, np.ndarray]]:
    """Nätets plana ytor: (normal, avstånd längs normalen, trianglarna (k, 3, 3))."""
    T = V[F]
    N = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    A = np.linalg.norm(N, axis=1)
    ok = A > 1e-9
    T, N, A, Y = T[ok], N[ok] / A[ok, None], A[ok], Y[ok]
    ut = []
    ordning = np.argsort(Y, kind="stable")
    grans = np.flatnonzero(np.diff(Y[ordning])) + 1
    for idx in np.split(ordning, grans):
        n = (N[idx] * A[idx, None]).sum(axis=0)
        if np.linalg.norm(n) < 1e-9:
            continue
        n /= np.linalg.norm(n)
        if np.abs(N[idx] @ n - 1.0).max() > 1e-4:
            continue                                        # inte plan
        d = T[idx, :, :] @ n
        if np.ptp(d) > 0.05:
            continue
        ut.append((n, float(d.mean()), T[idx]))
    return ut


def _polygon(T: np.ndarray, bas: np.ndarray) -> Polygon:
    P = T @ bas                                             # (k, 3, 2)
    tri = shapely.polygons(np.concatenate([P, P[:, :1]], axis=1))
    if len(tri) == 1:
        return tri[0]
    try:
        return shapely.coverage_union_all(tri).buffer(0)          # snabbt där trianglarna möts i hörnen
    except shapely.errors.GEOSException:
        return shapely.union_all(tri).buffer(0)


def _mitt(g: BaseGeometry) -> Point:
    """Mitten av en smal remsa (där ytorna möts, springan): tyngdpunkten om den ligger på remsan."""
    c = g.centroid
    return c if g.buffer(0.5).contains(c) else g.representative_point()


def _nyckel(n: np.ndarray) -> tuple[int, int, int]:
    q = np.round(n / NORMAL).astype(int)
    return (int(q[0]), int(q[1]), int(q[2]))


def _inathorn(synliga: dict, ytor: dict, polygon: Callable, i_planet: Callable
              ) -> list[tuple[str, float, str, str, np.ndarray, np.ndarray]]:
    """Springor i inåthörnen (#107): två synliga ytor med vinkelräta normaler som vetter mot samma hörn (var och en
    framför den andras plan) och möts längs minst LANGD av hörnlinjen, där den ena (eller båda) slutar SPRINGA–
    SPRINGA_MAX mm före hörnlinjen och ingen annan del i dess plan fyller remsan."""
    alla = [(k, rel, dd, q, bas, n) for k, lst in synliga.items() for rel, dd, q, bas, n in lst]
    if len(alla) < 2:
        return []
    # ytornas lådor i 3D, för att bara pröva par som ligger nära varandra
    lador = []
    for _, _, dd, q, bas, n in alla:
        x0, y0, x1, y1 = q.bounds
        P = np.array([bas @ np.array([x, y]) + n * dd for x in (x0, x1) for y in (y0, y1)])
        lador.append((P.min(axis=0), P.max(axis=0)))
    lo = np.array([a for a, _ in lador])
    hi = np.array([b for _, b in lador])
    N = np.array([n for *_, n in alla])
    nara = np.all((lo[:, None, :] <= hi[None, :, :] + SPRINGA_MAX) & (lo[None, :, :] <= hi[:, None, :] + SPRINGA_MAX),
                  axis=2)
    vinkelrata = np.abs(N @ N.T) < 1e-3
    ut = []
    for i, j in zip(*np.nonzero(np.triu(nara & vinkelrata, 1))):
        ka, ra, da, qa, basa, na = alla[i]
        kb, rb, db, qb, basb, nb = alla[j]
        if ra == rb:
            continue
        t = np.cross(na, nb)                        # hörnlinjens riktning
        ca, cb = basa.T @ nb, basb.T @ na           # den andra ytans normal i ytans plan
        g = []
        fram = []
        intervall = []
        for q, c, d_annan, bas, nn, d_egen in ((qa, ca, db, basa, na, da), (qb, cb, da, basb, nb, db)):
            P = np.asarray(q.exterior.coords) if hasattr(q, "exterior") else np.zeros((0, 2))
            if len(P) == 0:
                break
            avst = P @ c - d_annan                  # framför den andra ytans plan: > 0
            g.append(float(avst.min()))
            fram.append(float(avst.max()))
            nara_p = P[avst < avst.min() + 1.0]      # kanten närmast hörnet
            u = (np.column_stack([nara_p[:, 0], nara_p[:, 1]]) @ (bas.T @ t))
            intervall.append((float(u.min()), float(u.max())))
        # inåthörn: båda ytorna når ut i rummet framför den andra; den ena får gå förbi hörnlinjen in bakom den andra
        # väggens skikt (högst FORBI), den andra slutar SPRINGA–SPRINGA_MAX före den
        if len(g) < 2 or min(fram) < LANGD or min(g) < -FORBI or max(g) <= SPRINGA or max(g) > SPRINGA_MAX:
            continue
        a0, a1 = max(intervall[0][0], intervall[1][0]), min(intervall[0][1], intervall[1][1])
        if a1 - a0 < LANGD:
            continue
        # remsan mellan den korta ytans kant och hörnlinjen, i dess plan: fylls den av en annan del?
        kort = 0 if g[0] >= g[1] else 1
        k, rel, dd, q, bas, nn = (ka, ra, da, qa, basa, na) if kort == 0 else (kb, rb, db, qb, basb, nb)
        c, d_annan = (ca, db) if kort == 0 else (cb, da)
        tt = bas.T @ t
        m0 = c * d_annan                            # hörnlinjen i planet, och remsan ut till kanten
        remsa = Polygon([m0 + tt * a0, m0 + tt * a1, m0 + tt * a1 + c * g[kort], m0 + tt * a0 + c * g[kort]])
        fyller = [polygon(k, m, k, bas) for m in i_planet(k, dd, 1.0) if ytor[k][m][0] not in (ra, rb)]
        if fyller and remsa.difference(shapely.union_all(fyller).buffer(0.5)).area < 0.1 * remsa.area:
            continue
        mitt = m0 + tt * (a0 + a1) / 2 + c * g[kort] / 2
        pt = bas @ mitt + nn * dd
        ut.append(("springa i inåthörnet", g[kort], ra, rb, pt, (na + nb) / np.linalg.norm(na + nb)))
    return ut


def kontrollera(rot: Montage, karna: Karna, regler: ModuleType) -> Ytor:
    t0 = time.perf_counter()
    ut = Ytor()
    material = set(getattr(regler, "YTSKIKT", ()))
    undantag = tuple(getattr(regler, "YTSKIKT_UTOM", {}))
    if not material:
        return ut
    # alla delars plana ytor per normal (för att se vad som täcker och fyller), ytskiktens utpekade
    ytor: dict[tuple[int, int, int], list[tuple[str, float, np.ndarray]]] = defaultdict(list)
    ytskikt: list[tuple[tuple[int, int, int], int, np.ndarray]] = []
    cache: dict[int, list[tuple[np.ndarray, float, np.ndarray]]] = {}
    for vag, d, p in rot.platta():
        rel = vag.split("/", 1)[1]
        if rel.startswith(UTOM):
            continue
        nat = karna.nat(d.form)
        if id(nat) not in cache:
            cache[id(nat)] = _plana(nat.V.astype(np.float64), nat.F.astype(np.int64), nat.Y.astype(np.int64))
        R, t = np.array(p.R), np.array(p.t)
        yt = d.material.namn in material and not rel.startswith(undantag)
        for n0, d0, T0 in cache[id(nat)]:
            n = R @ n0
            k = _nyckel(n)
            if yt:
                ytskikt.append((k, len(ytor[k]), n))
            ytor[k].append((rel, float(d0 + n @ t), T0 @ R.T + t))
    avstand = {k: np.array([dd for _, dd, _ in v]) for k, v in ytor.items()}
    polygoner: dict[tuple[tuple[int, int, int], tuple[int, int, int], int], Polygon] = {}

    def polygon(k: tuple[int, int, int], i: int, bas_k: tuple[int, int, int], bas: np.ndarray) -> Polygon:
        """Ytan i ytor[k][i] i planet med axlarna bas (för normalen bas_k), en gång."""
        if (bas_k, k, i) not in polygoner:
            polygoner[(bas_k, k, i)] = _polygon(ytor[k][i][2], bas)
        return polygoner[(bas_k, k, i)]

    def i_planet(k: tuple[int, int, int], d: float, tol: float) -> np.ndarray:
        return np.flatnonzero(np.abs(avstand[k] - d) < tol) if k in avstand else np.zeros(0, dtype=int)

    # de synliga delarna av ytskiktens ytor: utom där en annan del ligger an (samma plan, motsatt normal)
    synliga: dict[tuple[int, int, int], list[tuple[str, float, Polygon, np.ndarray, np.ndarray]]] = defaultdict(list)
    for k, i, n in ytskikt:
        rel, dd, _ = ytor[k][i]
        bas = _bas(n)
        poly = polygon(k, i, k, bas)
        mk = (-k[0], -k[1], -k[2])
        mot = [polygon(mk, j, k, bas) for j in i_planet(mk, -dd, PLAN) if ytor[mk][j][0] != rel]
        if mot:
            poly = poly.difference(shapely.union_all(mot).buffer(0.01))
        for q in getattr(poly, "geoms", [poly]):
            if q.area > 0 and q.buffer(-BREDD / 2).area > 0:
                synliga[k].append((rel, dd, q, bas, n))
    ut.ytor = sum(len(v) for v in synliga.values())
    # par av synliga ytor med samma normal
    kandidater: list[tuple[str, float, str, str, np.ndarray, np.ndarray]] = []
    for k, lst in synliga.items():
        polys = [q for _, _, q, _, _ in lst]
        trad = shapely.STRtree(polys)
        a_idx, b_idx = trad.query(polys, predicate="dwithin", distance=SPRINGA_MAX)
        for i, j in zip(a_idx.tolist(), b_idx.tolist()):
            if j <= i:
                continue
            ri, di, qi, bas, n = lst[i]
            rj, dj, qj, _, _ = lst[j]
            if ri == rj:
                continue
            delta = abs(di - dj)
            if delta > SPRANG_MAX:
                continue
            g = qi.distance(qj)
            if delta >= SPRANG and g < MOTS:
                if qi.intersection(qj).area > 1.0:
                    continue                                # lager på varandra, inte ett språng
                kant = qi.buffer(MOTS).intersection(qj.buffer(MOTS))
                if kant.area / (2 * MOTS) < LANGD:
                    continue
                vad, mått = "språng", delta
                a = _mitt(kant)
                pt = bas @ np.array([a.x, a.y]) + n * max(di, dj)
            elif delta < SPRANG and SPRINGA < g <= SPRINGA_MAX:
                # springan: remsan där ytorna, utvidgade 0,6 g var, går in i varandra (0,2 g bred)
                springa = qi.buffer(g * 0.6).intersection(qj.buffer(g * 0.6)).difference(qi.union(qj))
                if springa.area / (0.2 * g) < LANGD:
                    continue
                fyller = [polygon(k, m, k, bas) for m in i_planet(k, di, 1.0) if ytor[k][m][0] not in (ri, rj)]
                if fyller and springa.difference(shapely.union_all(fyller).buffer(0.5)).area < 0.1 * springa.area:
                    continue                                # en smyg eller list i liv med skivorna
                vad, mått = "springa", g
                a = _mitt(springa)
                pt = bas @ np.array([a.x, a.y]) + n * di
            else:
                continue
            kandidater.append((vad, mått, ri, rj, pt, n))
    kandidater += _inathorn(synliga, ytor, polygon, i_planet)
    # bara där ytorna vetter mot ett rum: punkten PROV mm framför dem är rummets luft, minst RUM fritt längs axlarna
    # (vagar.Huset), inte ett hålrum i en vägg eller ett bjälklag eller en annan del
    rapporterade: dict[tuple[str, str], tuple[float, str]] = {}
    huset = Huset(rot, karna, set()) if kandidater else None
    for vad, mått, ri, rj, pt, n in kandidater:
        if huset is None or min(huset.matt(pt + PROV * n, a) for a in np.eye(3)) < RUM:
            continue
        par = (min(ri, rj), max(ri, rj))
        text = f"{vad} {mått:.1f} mm mellan {ri} och {rj} vid ({pt[0]:.0f}, {pt[1]:.0f}, {pt[2]:.0f})"
        if par not in rapporterade or mått > rapporterade[par][0]:
            rapporterade[par] = (mått, text)
    ut.fel = [t for _, t in sorted(rapporterade.values(), key=lambda v: -v[0])]
    ut.sekunder = time.perf_counter() - t0
    return ut
