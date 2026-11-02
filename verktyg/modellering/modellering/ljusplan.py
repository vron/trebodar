"""Ljusplaner: belysningsstyrkan [lux] på en vågrät mätyta (renderad i Blender, blender/scen.matyta) som en plan i
ritningsmallen (A3): belysningsstyrkan i färg (fasta steg, så att planerna går att jämföra) inom huset, isolinjer,
armaturerna och medel-, minsta och största värde och jämnhet (minsta / medel) per rum och delområde. Rummen är de
slutna ytorna mellan väggarna i modellens snitt (STEP-filen), utan en kantzon på 0,5 m längs väggarna
(SS-EN 12464-1); en öppen planlösning delas mellan rummens namn.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import contourpy
import matplotlib.pyplot as plt
import numpy as np
import shapely
from matplotlib.path import Path as Bana
from shapely import voronoi_polygons
from shapely.geometry import LineString, MultiPoint, Point, Polygon
from shapely.ops import unary_union

from .elritning import symbol
from .karna import ROT
from .planritning import Vy, blad, figur, kompilera, norrpil, papper, plan, polygoner, sv, vy

NIVAER = [0, 10, 20, 50, 75, 100, 150, 200, 300, 500, 750, 1000, 2000, 5000]
ISOLINJER = [50, 100, 200, 300, 500]
GLIPA = 30.0                     # rummens slutning: glipor i snittet upp till 2 × GLIPA
KANTZON = 500.0                  # utan kantzonen längs väggarna i rummens statistik [mm]
SKALOR = (20.0, 50.0, 75.0, 100.0)
PLATS = (205.0, 240.0)           # planens största bredd och höjd på bladet [mm]
FORSTORING = 4                   # rastrets bildpunkter per mätruta och led (bilinjärt mellan rutorna)
FARGER = ["#{:02x}{:02x}{:02x}".format(*(round(255 * c) for c in f[:3]))
          for f in plt.get_cmap("inferno")(np.linspace(0.08, 0.98, len(NIVAER) - 1))]


def rummen(delar: list[dict], rumsnamn: dict[str, tuple]) -> list[tuple[str, Polygon]]:
    """Rummen: de slutna ytorna mellan väggarna (hålen i unionen av snittets ytor, glipor upp till 60 mm slutna),
    med namnen ur RUMSNAMN som ligger i dem. En öppen planlösning (flera namn i samma yta) delas mellan namnen efter
    närmaste namn (Voronoi)."""
    u = unary_union([y.buffer(GLIPA, join_style=2) for y in polygoner(delar) if y.area > 0])
    ut: list[tuple[str, Polygon]] = []
    for g in getattr(u, "geoms", [u]):
        for h in g.interiors:
            yta = Polygon(h).buffer(GLIPA, join_style=2)
            if yta.area < 0.5e6:
                continue
            namn = [(n, Point(lage[0], lage[1])) for n, lage in rumsnamn.values() if yta.contains(Point(lage[0], lage[1]))]
            if len(namn) == 1:
                ut.append((namn[0][0], yta))
            elif len(namn) > 1:
                celler = voronoi_polygons(MultiPoint([p for _, p in namn]), extend_to=yta.envelope.buffer(1000.0))
                for c in getattr(celler, "geoms", [celler]):
                    for n, p in namn:
                        if c.contains(p):
                            ut.append((n, c.intersection(yta)))
    return ut


def huset(delar: list[dict]) -> Polygon:
    """Husets yta i planet: snittets ytor med glipor slutna, utan hål."""
    u = unary_union([y.buffer(GLIPA, join_style=2) for y in polygoner(delar) if y.area > 0])
    return unary_union([Polygon(g.exterior) for g in getattr(u, "geoms", [u]) if g.area > 1e6]).buffer(
        -GLIPA, join_style=2)


def _statistik(lux: np.ndarray, x: np.ndarray, y: np.ndarray, yta: Polygon) -> dict[str, float] | None:
    """Medel, minsta och största värde och jämnhet i rutorna vars mitt ligger inom ytan."""
    bana = Bana(np.asarray(yta.exterior.coords))
    inne = bana.contains_points(np.column_stack([x.ravel(), y.ravel()])).reshape(lux.shape)
    for h in yta.interiors:
        inne &= ~Bana(np.asarray(h.coords)).contains_points(np.column_stack([x.ravel(), y.ravel()])).reshape(lux.shape)
    if inne.sum() < 4:
        return None
    v = lux[inne]
    medel = float(v.mean())
    return {"medel": medel, "minst": float(v.min()), "storst": float(v.max()),
            "jamnhet": float(v.min() / medel) if medel > 0 else 0.0, "rutor": int(inne.sum())}


def _forstora(lux: np.ndarray, f: int) -> np.ndarray:
    """Rutnätet med f × f bildpunkter per ruta, bilinjärt mellan rutornas mittpunkter."""
    ny, nx = lux.shape
    u = (np.arange(nx * f) + 0.5) / f - 0.5
    w = (np.arange(ny * f) + 0.5) / f - 0.5
    rader = np.array([np.interp(u, np.arange(nx), r) for r in lux])
    return np.array([np.interp(w, np.arange(ny), k) for k in rader.T]).T


def raster(lux: np.ndarray, omrade: tuple[float, float, float, float], hus: Polygon, png: Path) -> None:
    """Belysningsstyrkan i färg (FARGER, fasta steg) inom huset, genomskinligt utanför, som PNG (rad 0 överst)."""
    x0, x1, y0, y1 = omrade
    stor = _forstora(lux, FORSTORING)
    ny, nx = stor.shape
    farg = np.array([[int(f[i:i + 2], 16) for i in (1, 3, 5)] for f in FARGER], dtype=np.uint8)
    rgba = np.zeros((ny, nx, 4), dtype=np.uint8)
    rgba[..., :3] = farg[np.clip(np.digitize(stor, NIVAER[1:-1]), 0, len(FARGER) - 1)]
    X, Y = np.meshgrid(x0 + (np.arange(nx) + 0.5) * (x1 - x0) / nx, y0 + (np.arange(ny) + 0.5) * (y1 - y0) / ny)
    shapely.prepare(hus)
    rgba[..., 3] = np.where(shapely.contains_xy(hus, X, Y), 255, 0)
    png.parent.mkdir(parents=True, exist_ok=True)
    plt.imsave(png, rgba[::-1])


def _isolinjer(v: Vy, lux: np.ndarray, cx: np.ndarray, cy: np.ndarray, hus: Polygon) -> None:
    """Isolinjerna (ISOLINJER) inom huset, med värdet på de längre linjerna."""
    gen = contourpy.contour_generator(cx, cy, lux)
    for niva in ISOLINJER:
        for a in gen.lines(niva):
            if len(a) < 2:
                continue
            g = LineString(a).simplify(v.m(0.15)).intersection(hus)
            for ln in getattr(g, "geoms", [g]):
                if isinstance(ln, LineString) and ln.length > v.m(3.0):
                    v.linje(list(ln.coords), "iso")
                    if ln.length > v.m(30.0):
                        q = ln.interpolate(0.5, normalized=True)
                        v.text(q.x, q.y, sv(niva), a="cm", sz=4.8, bg=True)


def _fargskala(x: float, y: float) -> Vy:
    """Färgskalan (pappersmm från bladets övre vänstra hörn): stegen med gränserna, högsta överst."""
    pv = Vy(0.0, 0.0, 420.0, 297.0, 1.0, 0.0, 0.0)
    h, b = 4.0, 6.0
    with pv.lager("fargskala"):
        pv.text(x, -y, "Belysningsstyrka, lux", a="lb", sz=8.5, b=True)
        for i, f in enumerate(reversed(FARGER)):
            pv.rekt(x, -(y + 2.5 + i * h), x + b, -(y + 2.5 + (i + 1) * h), fyll=f, stil="tunn")
        for i, niva in enumerate(reversed(NIVAER)):
            pv.text(x + b + 1.2, -(y + 2.5 + i * h), sv(niva), a="lm", sz=6.2)
    return pv


def _prov(v: Vy, rita: str) -> None:
    """Teckenförklaringens prov på belysningsstyrkans färg: en linje eller en armatur på en mörk ruta."""
    v.rekt(-4.5, -1.3, 4.5, 1.3, fyll=FARGER[4], stil=None)
    if rita == "armatur":
        symbol(v, "spot", 0.0, 0.0)
    else:
        v.linje([(-3.8, 0.0), (3.8, 0.0)], rita)


def rita(lux: np.ndarray, yta: Any, delar: list[dict], utdrag: dict, rumsnamn: dict[str, tuple],
         scenario: list[str], norr: tuple[float, float], nummer: str, arbete: Path, ut: Path) -> list[dict[str, Any]]:
    """Ljusplanen för mätytan (lux: rutnätet, rad 0 vid y0) som pdf (ut), med statistiken per rum och delområde
    (returneras); bladet och rastret i arbetsmappen (under repots rot, för Typst)."""
    x0, x1, y0, y1 = yta.omrade
    ny, nx = lux.shape
    cx = x0 + (np.arange(nx) + 0.5) * (x1 - x0) / nx
    cy = y0 + (np.arange(ny) + 0.5) * (y1 - y0) / ny
    X, Y = np.meshgrid(cx, cy)
    hus = huset(delar)
    if x1 - x0 > 6000.0:                                  # hela planet: huset med marginal
        hx0, hy0, hx1, hy1 = hus.bounds
        omrade = (hx0 - 400.0, hx1 + 400.0, hy0 - 400.0, hy1 + 400.0)
    else:                                                 # en del: ytan med omgivningen
        omrade = (x0 - 1500.0, x1 + 1500.0, y0 - 500.0, y1 + 500.0)
    skala = next((s for s in SKALOR if (omrade[1] - omrade[0]) / s <= PLATS[0] and (omrade[3] - omrade[2]) / s
                  <= PLATS[1]), SKALOR[-1])
    v = vy(skala, omrade, 24.0, 27.0)
    png = arbete / f"{nummer}-lux.png"
    raster(lux, (x0, x1, y0, y1), hus, png)
    with v.lager("lux"):
        v.bild(x0, y1, (x1 - x0) / skala, (y1 - y0) / skala, "/" + png.resolve().relative_to(ROT).as_posix())
    with v.lager("isolinjer"):
        _isolinjer(v, lux, cx, cy, hus.intersection(Polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])))
    plan(v, delar, ram=Polygon([(omrade[0], omrade[2]), (omrade[1], omrade[2]), (omrade[1], omrade[3]),
                                (omrade[0], omrade[3])]))
    # statistik per rum (namnen ur RUMSNAMN) och per delområde
    stat: list[dict[str, Any]] = []
    with v.lager("statistik"):
        for namn, r in rummen(delar, rumsnamn):
            lage = next(lg for n, lg in rumsnamn.values() if n == namn)
            if not (x0 <= lage[0] <= x1 and y0 <= lage[1] <= y1):
                continue
            delar_r = [g for g in getattr(r, "geoms", [r]) if isinstance(g, Polygon) and g.area > 0.2e6]
            if not delar_r:
                continue
            # statistiken utan en kantzon längs väggarna (SS-EN 12464-1: 0,5 m), i små rum mindre
            storst = max(delar_r, key=lambda g: g.area)
            inre = storst.buffer(-KANTZON)
            if inre.is_empty or inre.area < 0.25 * storst.area:
                inre = storst.buffer(-KANTZON / 4)
            inre = max(getattr(inre, "geoms", [inre]), key=lambda g: g.area)
            s = _statistik(lux, X, Y, inre)
            if s is None:
                continue
            stat.append({"namn": namn, **s})
            v.polygon(list(inre.exterior.coords), None, "matyta")
            c = inre.representative_point()
            v.text(c.x, c.y, f"{namn}\nmedel {sv(s['medel'])} lux\nmin {sv(s['minst'])} / max {sv(s['storst'])}",
                   a="cm", sz=5.8, bg=True)
        for namn, (a, b, c_, d_) in yta.zoner:
            s = _statistik(lux, X, Y, Polygon([(a, c_), (b, c_), (b, d_), (a, d_)]))
            v.rekt(a, c_, b, d_, None, "delomrade")
            v.ptext((a + b) / 2, d_, 0, 1.0, namn, a="cb", sz=5.8, bg=True)
            if s:
                stat.append({"namn": namn, **s})
    # armaturerna på planet
    with v.lager("armaturer"):
        for k, p in utdrag["punkter"].items():
            if p["slag"] != "lampa" or not (omrade[0] <= p["punkt"][0] <= omrade[1]
                                            and omrade[2] <= p["punkt"][1] <= omrade[3]):
                continue
            rum = utdrag["rum"].get(p.get("rum", ""), {})
            if rum and (rum["plan"] == 1) != (yta.plan == 1):
                continue
            symbol(v, utdrag["typer"][p["typ"]]["symbol"], p["punkt"][0], p["punkt"][1])
            v.ptext(p["punkt"][0], p["punkt"][1], 1.8, 0.6, k, a="lb", sz=5.0, bg=True)
    if yta.plan == 1 and x1 - x0 > 6000.0:
        norrpil(v, 7300.0, 14600.0, norr)
    v.rubrik(*papper(v, 24.0, 21.0), f"{yta.namn}, belysningsstyrka", round(skala))
    with v.lager("skalstock"):
        v.skalstock(*papper(v, 24.0, 27.0 + (omrade[3] - omrade[2]) / skala + 8.0),
                    langd_m=5 if (omrade[1] - omrade[0]) / skala > 5000.0 / skala + 10.0 else 2, steg_m=1)
    xb = 24.0 + (omrade[1] - omrade[0]) / skala + 8.0
    block: list[dict] = [dict(x=xb, y=20.0 + 2.5 + 4.0 * len(FARGER) + 4.0, w=min(326.0 - 4.0 - xb, 98.0), innehall=[
        dict(typ="rubrik", text="Rum och delområden, lux"),
        dict(typ="tabell", kolumner=["Rum", "Medel", "Min", "Max", "Jämnhet U₀"], bredd=(1.8, 0.7, 0.6, 0.7, 0.9),
             just=["l", "r", "r", "r", "r"], sz=6.6,
             rader=[[s_["namn"], sv(s_["medel"]), sv(s_["minst"]), sv(s_["storst"]), sv(s_["jamnhet"], 2)]
                    for s_ in sorted(stat, key=lambda q: str(q["namn"]))]),
    ])]
    kol: list[dict] = [
        dict(typ="rubrik", text="Anvisningar"),
        dict(typ="lista", sz=7.0, rader=[
            "Belysningsstyrkan " + (f"på en vågrät yta {sv(yta.hojd / 1000, 2)} m över golvet" if yta.hojd > 0
                                    else "på golvet")
            + f", i rutor om {sv(yta.cell)} mm, ur renderingen i Blender (Cycles): armaturernas uppmätta "
            "ljusfördelning (tillverkarnas fotometrifiler), dagsljuset och reflexerna i rummen.",
            *scenario,
            "Statistiken per rum utan en kantzon på 0,5 m längs väggarna (SS-EN 12464-1), i små rum mindre; "
            "jämnheten U₀ = minsta / medel. Rummen är de slutna ytorna mellan väggarna; en öppen planlösning delas "
            "mellan rummens namn.",
            "Ritningen ritas med ./mod ljusplan (verktyg/modellering); mätytorna står i modellens el/matytor.py.",
        ]),
        dict(typ="rubrik", text="Teckenförklaring"),
        dict(typ="symboler", rader=[
            {**figur(lambda w: _prov(w, "iso")), "text": "isolinje, med belysningsstyrkan"},
            {**figur(lambda w: _prov(w, "matyta")), "text": "rummets yta i statistiken (utan kantzonen)"},
            {**figur(lambda w: _prov(w, "delomrade")), "text": "delområde med egen statistik"},
            {**figur(lambda w: _prov(w, "armatur")), "text": "armatur"},
        ]),
    ]
    b = blad(nummer, ["Ljusplan", str(yta.namn)], f"1:{skala:g}", "Modellen, rendering", kol,
             [v, _fargskala(xb, 20.0)], block)
    kompilera([(nummer, b)], arbete, ut)
    return stat
