"""Källarväggarnas insida: gips 13 mm direkt på cellplasten (brandskydd: cellplasten får inte vara oskyddad mot
rummen), från bottenplattan till mellanbjälklagets underkant. Gipsen sitter på ytterväggarnas insida och på båda
sidor av innerväggarna, runt de fria väggändarna i dörröppningarna D2 och D3, i fönstrens smyg från karmen och på
bröstningens cellplast mellan smygarna. Källardörren D1 finns inte i modellen: smygens gips går till kärnans
utsida, där karmen antas sitta i det yttre cellplastlagret.

En skiva per väggyta och höjdavsnitt. I innerhörn går skivan längs x fram till hörnet och skivan längs y slutar mot
den; i ytterhörn (väggändar och smyg) går skivan längs x förbi hörnet och täcker den andras kant.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from shapely.geometry import Point, Polygon
from shapely.geometry import box as rektangel
from shapely.ops import unary_union

from modellering import Del, Montage, Placering, box

from trebodar import skelett as S
from trebodar.byggdelar import fonster as F
from trebodar.byggdelar.virke import fmt
from trebodar.hus.fonster_och_dorrar.oppningar import OPPNINGAR, Oppning
from trebodar.hus.grund import kallarvaggar as K
from trebodar.material import GIPS

GIPS_T = 13.0
W_INSIDA = K.KARNA + 2 * K.CELL          # väggens insida från cellplastens utsida
PROV = GIPS_T / 2                        # provpunkternas avstånd från ytorna


@dataclass(frozen=True)
class Fonster:
    o: Oppning
    w_karm: float            # karmens insida i väggens w (från cellplastens utsida)
    oppning: Polygon         # öppningen i plan från fasaden till karmens insida
    smyg: Polygon            # smygarnas cellplast i plan
    brostning: Polygon       # bröstningen i plan (väggens hela tjocklek mellan väggarnas kärnor)


def _rekt_i_vagg(u0: float, u1: float, w0: float, w1: float) -> Polygon:
    """Rektangeln (u0–u1, w0–w1) i väggen 2NO:s system (källarfönstren), i plan."""
    pl = S.YTTERVAGGAR["2NO"].placering()
    hörn = [pl.punkt((u, w, 0.0))[:2] for u in (u0, u1) for w in (w0, w1)]
    xs, ys = [p[0] for p in hörn], [p[1] for p in hörn]
    return rektangel(min(xs), min(ys), max(xs), max(ys))


def _fonster() -> list[Fonster]:
    ut = []
    for o in OPPNINGAR["2NO"]:
        if o.z1 > 0:
            continue
        w_karm = -S.T_FASAD + F.PRODUKTER[o.typ][1]
        smyg = _rekt_i_vagg(o.u0 - K.CELL, o.u0, 0.0, W_INSIDA).union(_rekt_i_vagg(o.u1, o.u1 + K.CELL, 0.0, W_INSIDA))
        ut.append(Fonster(o, w_karm, _rekt_i_vagg(o.u0, o.u1, -1.0, w_karm), smyg,
                          _rekt_i_vagg(o.u0 - K.CELL, o.u1 + K.CELL, 0.0, W_INSIDA)))
    return ut


def _dorrar(inne: Polygon) -> list[Polygon]:
    """Ytterdörrarnas öppning i plan från väggens utsida till kärnans utsida (karmen i det yttre cellplastlagret)."""
    ut = []
    for _, rikt, liv, a, b in K.dorrar():
        mitt = (a + b) / 2
        inat = 1.0 if inne.contains(Point((mitt, liv + 10.0) if rikt == "h" else (liv + 10.0, mitt))) else -1.0
        w0, w1 = sorted((liv - inat, liv + inat * K.CELL))
        ut.append(rektangel(a, w0, b, w1) if rikt == "h" else rektangel(w0, a, w1, b))
    return ut


def skivor(vaggar: Polygon, rum: Polygon, agare: list[tuple[str, Polygon, str | None]]
            ) -> list[tuple[str, tuple[float, ...]]]:
    """Skivorna i plan i ett höjdavsnitt längs väggytorna mot rummen: (ägare, (x0, y0, x1, y1)). Ägarna: (namn,
    yta i plan, väggens riktning "h"/"v", None för fönstren)."""
    ut = []
    ringar = [r for q in getattr(vaggar, "geoms", [vaggar]) for r in (q.exterior, *q.interiors)]
    for ring in ringar:
        pts = list(ring.coords)
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            L = abs(bx - ax) + abs(by - ay)
            if L < 1.0:
                continue
            ex, ey = (bx - ax) / L, (by - ay) / L
            assert abs(ex) < 1e-9 or abs(ey) < 1e-9, "väggarna går längs x och y"
            sidor = [s for s in (1.0, -1.0) if any(
                rum.contains(Point(ax + ex * t * L - s * ey * PROV, ay + ey * t * L + s * ex * PROV))
                for t in (0.1, 0.3, 0.5, 0.7, 0.9))]
            if len(sidor) != 1:
                continue
            nx, ny = -sidor[0] * ey, sidor[0] * ex                  # mot rummet
            langs_x = abs(ex) > 0.5
            t0, t1 = 0.0, L
            for t, d in ((0.0, -1.0), (L, 1.0)):
                px, py = ax + ex * (t + d * PROV), ay + ey * (t + d * PROV)          # strax förbi änden
                inner = vaggar.contains(Point(px + nx * PROV, py + ny * PROV))     # väggen fortsätter framför
                ytter = (not vaggar.contains(Point(px - nx * PROV, py - ny * PROV))
                         and rum.contains(Point(px + nx * PROV, py + ny * PROV)))   # väggen slutar, rummet runt
                andring = GIPS_T if langs_x and ytter else -GIPS_T if not langs_x and inner else 0.0
                t0, t1 = (t0 - andring, t1) if t == 0.0 else (t0, t1 + andring)
            hörn = [(ax + ex * t + nx * w, ay + ey * t + ny * w) for t in (t0, t1) for w in (0.0, GIPS_T)]
            xs, ys = [p[0] for p in hörn], [p[1] for p in hörn]
            remsa = rektangel(min(xs), min(ys), max(xs), max(ys)).intersection(rum)
            # ägaren: väggen längs ytan 1 mm innanför den (i början, mitten och slutet), annars fönstret
            prov = [Point(ax + ex * t - nx, ay + ey * t - ny) for t in (min(50.0, L / 2), L / 2, max(L - 50.0, L / 2))]
            rikt = "h" if langs_x else "v"
            namn = next(n for urval in ([a for a in agare if a[2] == rikt], [a for a in agare if a[2] is None], agare)
                        for p in prov for n, q, _ in urval if q.contains(p))
            for q in getattr(remsa, "geoms", [remsa]):
                if q.geom_type != "Polygon" or q.area < GIPS_T:
                    continue
                assert abs(q.area - q.envelope.area) < 1e-3, "skivan ska vara en rektangel"
                ut.append((namn, tuple(round(c, 3) for c in q.bounds)))
    return ut


def montage() -> Montage:
    m = Montage("Källarväggarnas insida", beskrivning="Gips 13 på källarväggarnas cellplast (brandskydd)")
    fonster = _fonster()
    inne = K.ytterkontur()
    dorrar = _dorrar(inne)
    nivaer = sorted({K.Z0, K.Z1} | {f.o.z0 for f in fonster})
    langs: dict[tuple[str, tuple[float, ...]], list[tuple[float, float]]] = defaultdict(list)
    for z0, z1 in zip(nivaer, nivaer[1:]):
        zm = (z0 + z1) / 2
        vaggar = K.i_plan(zm).simplify(0)
        oppna = [f for f in fonster if f.o.z0 < zm]
        rum = inne.difference(vaggar).difference(unary_union(dorrar + [f.oppning for f in oppna]))
        agare: list[tuple[str, Polygon, str | None]] = [
            (f.o.kod, f.smyg if f in oppna else f.brostning, None) for f in fonster]
        agare += [(v.namn, K.cellplast_rekt(v), v.riktning) for v in K.VAGGAR]
        for namn, b in skivor(vaggar, rum, agare):
            hojd = langs[(namn, b)]
            if hojd and abs(hojd[-1][1] - z0) < 1e-6:
                hojd[-1] = (hojd[-1][0], z1)                          # samma skiva som i avsnittet under
            else:
                hojd.append((z0, z1))
    nr: dict[str, int] = defaultdict(int)
    for (namn, (x0, y0, x1, y1)), hojd in sorted(langs.items()):
        for z0, z1 in hojd:
            nr[namn] += 1
            m.lagg(Del(f"Gips 13 {namn}", box(x0, x1, y0, y1, z0, z1), GIPS), Placering(), f"{namn}-GI{nr[namn]:02d}")
    # bröstningarnas gips mellan smygarnas skivor, från karmen till väggens gipsyta
    for f in fonster:
        q = _rekt_i_vagg(f.o.u0 + GIPS_T, f.o.u1 - GIPS_T, f.w_karm, W_INSIDA + GIPS_T)
        x0, y0, x1, y1 = q.bounds
        m.lagg(Del(f"Gips 13 bröstning {fmt(x1 - x0)}×{fmt(y1 - y0)}", box(x0, x1, y0, y1, f.o.z0, f.o.z0 + GIPS_T),
                   GIPS), Placering(), f"{f.o.kod}-GIB")
    return m
