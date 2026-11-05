"""Ljusplaner: belysningsstyrkan [lux] på en vågrät mätyta (renderad i Blender, blender/scen.matyta) som en plan i
ritningsmallen (A3): belysningsstyrkan i färg (fasta steg, så att planerna går att jämföra) inom huset, isolinjer,
armaturerna och medel-, minsta och största värde och jämnhet (minsta / medel) per rum och delområde. Rummen är de
slutna ytorna mellan väggarna i modellens snitt (STEP-filen), utan en kantzon på 0,5 m längs väggarna
(SS-EN 12464-1); en öppen planlösning delas mellan rummens namn.
"""
from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

import contourpy
import matplotlib.pyplot as plt
import numpy as np
import shapely
from shapely import voronoi_polygons
from shapely.geometry import LineString, MultiPoint, Point, Polygon
from shapely.ops import unary_union

from .elritning import R_LAMPA, symbol
from .karna import ROT
from .planritning import Blad, Vy, blad, figur, norrpil, papper, plan, polygoner, rita_ytor, sv, vy

NIVAER = [0, 10, 20, 50, 75, 100, 150, 200, 300, 500, 750, 1000, 2000, 5000]
ISOLINJER = [50, 100, 200, 300, 500]
GLIPA = 30.0                     # rummens slutning: glipor i snittet upp till 2 × GLIPA
KANTZON = 500.0                  # utan kantzonen längs väggarna i rummens statistik [mm]
SKALOR = (20.0, 50.0, 75.0, 100.0)
PLATS = (205.0, 240.0)           # planens största bredd och höjd på bladet [mm]
FORSTORING = 4                   # rastrets bildpunkter per mätruta och led (bilinjärt mellan rutorna)
INREDNING = ("Hus/Inredning", "Hus/Kamin")      # inredningen på mätytan, som lämnas utanför statistiken
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


def inredningen(snitten: Sequence[list[dict]]) -> Any:
    """Inredningens yta i planet ur snitten genom den (matytor.INREDNING_SNITT): delarnas ytor, glipor upp till
    2 × GLIPA slutna och hålen fyllda (skåpens och lådornas ringar)."""
    u = unary_union([y.buffer(GLIPA, join_style=2) for d in snitten for y in polygoner(d, bara=INREDNING)
                     if y.area > 0])
    return unary_union([Polygon(g.exterior) for g in getattr(u, "geoms", [u]) if not g.is_empty]).buffer(
        -GLIPA, join_style=2)


def huset(delar: list[dict]) -> Polygon:
    """Husets yta i planet: snittets ytor med glipor slutna, utan hål."""
    u = unary_union([y.buffer(GLIPA, join_style=2) for y in polygoner(delar) if y.area > 0])
    return unary_union([Polygon(g.exterior) for g in getattr(u, "geoms", [u]) if g.area > 1e6]).buffer(
        -GLIPA, join_style=2)


def _statistik(lux: np.ndarray, x: np.ndarray, y: np.ndarray, yta: Any) -> dict[str, float] | None:
    """Medel, minsta och största värde och jämnhet i rutorna vars mitt ligger inom ytan (med hål, en eller flera)."""
    inne = shapely.contains_xy(yta, x, y)
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


def _ruta(r: tuple[float, float, float, float]) -> Polygon:
    """Rutan (x0, x1, y0, y1) som yta."""
    return Polygon([(r[0], r[2]), (r[1], r[2]), (r[1], r[3]), (r[0], r[3])])


def _etikettlage(rum: Any, mitt: Point, b: float, h: float, upptaget: list[tuple[float, float, float, float]],
                 steg: float) -> tuple[float, float]:
    """Etikettens mitt (rutan b × h, modellens mm) i rummet: närmast mitt bland lägena där rutan ligger i rummet och
    inte täcker det som är upptaget (armaturerna och deras id, delområdena och etiketterna: rutor x0, y0, x1, y1);
    finns inget sådant läge, det som täcker minst."""
    rx0, ry0, rx1, ry1 = rum.bounds
    mx, my = np.meshgrid(np.arange(rx0 + b / 2, rx1 - b / 2 + 1.0, steg),
                         np.arange(ry0 + h / 2, ry1 - h / 2 + 1.0, steg))
    gx, gy = mx.ravel(), my.ravel()
    i = shapely.contains(rum, shapely.box(gx - b / 2, gy - h / 2, gx + b / 2, gy + h / 2)) if gx.size else gx > 0
    if i.any():
        gx, gy = gx[i], gy[i]
        u = np.array(upptaget, dtype=float).reshape(1, -1, 4)
        dx = np.minimum(gx[:, None] + b / 2, u[..., 2]) - np.maximum(gx[:, None] - b / 2, u[..., 0])
        dy = np.minimum(gy[:, None] + h / 2, u[..., 3]) - np.maximum(gy[:, None] - h / 2, u[..., 1])
        tackt = (np.clip(dx, 0, None) * np.clip(dy, 0, None)).sum(axis=1)
        k = np.lexsort((np.hypot(gx - mitt.x, gy - mitt.y), tackt))[0]
        return float(gx[k]), float(gy[k])
    return mitt.x, mitt.y


def _och(namn: list[str]) -> str:
    """Namnen uppräknade: "a, b och c"."""
    return " och ".join([", ".join(namn[:-1]), namn[-1]] if len(namn) > 1 else namn)


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


def _panel(v: Vy, x: float, y: float, sida: float) -> None:
    """En taklampa ur vyernas LAMPOR (LED-panel) i sin storlek: en kvadrat med kryss."""
    h = sida / 2
    v.rekt(x - h, y - h, x + h, y + h, fyll="vit", stil="normal")
    v.linje([(x - h, y - h), (x + h, y + h)], "tunn")
    v.linje([(x - h, y + h), (x + h, y - h)], "tunn")


def _prov(v: Vy, rita: str) -> None:
    """Teckenförklaringens prov på belysningsstyrkans färg: en linje, en armatur eller en taklampa på en mörk ruta."""
    v.rekt(-4.5, -1.3, 4.5, 1.3, fyll=FARGER[4], stil=None)
    if rita == "armatur":
        symbol(v, "spot", 0.0, 0.0)
    elif rita == "panel":
        _panel(v, 0.0, 0.0, 2.0)
    else:
        v.linje([(-3.8, 0.0), (3.8, 0.0)], rita)


def rita(lux: np.ndarray, yta: Any, delar: list[dict], utdrag: dict, rumsnamn: dict[str, tuple],
         scenario: list[str], norr: tuple[float, float], nummer: str, arbete: Path,
         paneler: Sequence[tuple[float, float, float]] = (), hinder: Any = None,
         **huvud: str) -> tuple[Blad, list[dict[str, Any]]]:
    """Ljusplanens blad för mätytan (lux: rutnätet, rad 0 vid y0) och statistiken per rum och delområde, med
    elinstallationens armaturer och taklamporna (paneler: x, y och sida i mm) på planet; rastret i arbetsmappen
    (under repots rot, för Typst). hinder: inredningen på mätytan (inredningen()), som lämnas vit och utanför
    statistiken. huvud: bladets revision, datum och status (planritning.blad)."""
    x0, x1, y0, y1 = yta.omrade
    matt = Polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
    ny, nx = lux.shape
    cx = x0 + (np.arange(nx) + 0.5) * (x1 - x0) / nx
    cy = y0 + (np.arange(ny) + 0.5) * (y1 - y0) / ny
    X, Y = np.meshgrid(cx, cy)
    hus = huset(delar)
    # delområdena i en egen höjd (bänkskivorna): ytan där i stället för planet och inredningen under den
    hoga = [z for z in yta.zoner if z.hojd is not None and z.hojd != yta.hojd]
    upph = unary_union([_ruta(z.omrade) for z in hoga]) if hoga else Polygon()
    ivagen = hinder.intersection(hus).difference(upph) if hinder is not None else Polygon()
    if x1 - x0 > 6000.0:                                  # hela planet: huset med marginal
        hx0, hy0, hx1, hy1 = hus.bounds
        omrade = (hx0 - 400.0, hx1 + 400.0, hy0 - 400.0, hy1 + 400.0)
    else:                                                 # en del: ytan med omgivningen
        omrade = (x0 - 1500.0, x1 + 1500.0, y0 - 500.0, y1 + 500.0)
    skala = next((s for s in SKALOR if (omrade[1] - omrade[0]) / s <= PLATS[0] and (omrade[3] - omrade[2]) / s
                  <= PLATS[1]), SKALOR[-1])
    v = vy(skala, omrade, 24.0, 27.0)
    png = arbete / f"{nummer}-lux.png"
    raster(lux, (x0, x1, y0, y1), hus.difference(ivagen), png)
    with v.lager("lux"):
        v.bild(x0, y1, (x1 - x0) / skala, (y1 - y0) / skala, "/" + png.resolve().relative_to(ROT).as_posix())
        rita_ytor(v, ivagen.intersection(matt), None, "tunn")
    with v.lager("isolinjer"):
        _isolinjer(v, lux, cx, cy, hus.intersection(matt).difference(ivagen).difference(upph.buffer(yta.cell / 2)))
    ram = _ruta(omrade)
    plan(v, delar, ram=ram)
    # armaturerna och deras id, och taklamporna, som etiketterna inte ska täcka
    rum_plan = {k: r["plan"] for k, r in utdrag["rum"].items()}
    lampor = [(k, p["punkt"][0], p["punkt"][1]) for k, p in utdrag["punkter"].items()
              if p["slag"] == "lampa" and omrade[0] <= p["punkt"][0] <= omrade[1]
              and omrade[2] <= p["punkt"][1] <= omrade[3]
              and (rum_plan.get(p.get("rum", ""), yta.plan) == 1) == (yta.plan == 1)]
    r = v.m(R_LAMPA + 0.8)
    upptaget = ([(px - r, py - r, px + v.m(2.6 + 1.0 * len(k)), py + v.m(3.4)) for k, px, py in lampor]
                + [(px - sd / 2, py - sd / 2, px + sd / 2, py + sd / 2) for px, py, sd in paneler]
                + [(z.omrade[0], z.omrade[2], z.omrade[1], z.omrade[3]) for z in yta.zoner])
    # statistik per rum (namnen ur RUMSNAMN) och per delområde
    stat: list[dict[str, Any]] = []
    vaggar = unary_union(polygoner(delar))
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
            inre = max(getattr(inre, "geoms", [inre]), key=lambda g: g.area).intersection(matt)
            s = _statistik(lux, X, Y, inre.difference(ivagen).difference(upph))
            if s is None:
                continue
            stat.append({"namn": namn, **s})
            rita_ytor(v, inre, None, "matyta")
            rader = [namn, f"medel {sv(s['medel'])} lux", f"min {sv(s['minst'])} / max {sv(s['storst'])}"]
            b_, h_ = v.m(1.05 * max(len(t) for t in rader) + 1.5), v.m(2.45 * len(rader) + 1.0)
            ex, ey = _etikettlage(storst.intersection(matt).difference(ivagen).difference(upph),
                                  inre.representative_point(), b_, h_, upptaget, v.m(1.0))
            upptaget.append((ex - b_ / 2, ey - h_ / 2, ex + b_ / 2, ey + h_ / 2))
            v.text(ex, ey, "\n".join(rader), a="cm", sz=5.8, bg=True)
        for z in yta.zoner:
            ruta = _ruta(z.omrade)
            s = _statistik(lux, X, Y, ruta if z in hoga else ruta.difference(ivagen))
            rita_ytor(v, ruta, None, "delomrade")
            # etiketten längs delområdets längre sida, i det eller intill det (inte på väggarna) där den inte täcker
            # armaturerna
            text = z.namn + (f": medel {sv(s['medel'])} lux" if s else "")
            langs_y = z.omrade[3] - z.omrade[2] > z.omrade[1] - z.omrade[0]
            b_, h_ = v.m(1.05 * len(text) + 1.5), v.m(3.4)
            if langs_y:
                b_, h_ = h_, b_
            egen = (z.omrade[0], z.omrade[2], z.omrade[1], z.omrade[3])
            ex, ey = _etikettlage(ruta.buffer(max(b_, h_)).intersection(ram).difference(vaggar), ruta.centroid, b_, h_,
                                  [u for u in upptaget if u != egen], v.m(0.5))
            upptaget.append((ex - b_ / 2, ey - h_ / 2, ex + b_ / 2, ey + h_ / 2))
            v.text(ex, ey, text, a="cm", sz=5.8, bg=True, rot=90 if langs_y else 0)
            if s:
                stat.append({"namn": z.namn + (f" ({sv(z.hojd / 1000, 2)} m)" if z in hoga else ""), **s})
    # armaturerna på planet
    with v.lager("armaturer"):
        for k, px, py in lampor:
            symbol(v, utdrag["typer"][utdrag["punkter"][k]["typ"]]["symbol"], px, py)
            v.ptext(px, py, 1.8, 0.6, k, a="lb", sz=5.0, bg=True)
        for px, py, sida in paneler:
            _panel(v, px, py, sida)
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
            "ljusfördelning (tillverkarnas fotometrifiler), dagsljuset och reflexerna i rummen."
            + "".join(f" Delområdena {_och([z.namn for z in hoga if z.hojd == h])} mäts på en vågrät yta "
                      f"{sv(h / 1000, 2)} m över golvet."
                      for h in sorted({z.hojd for z in hoga})),
            *scenario,
            "Statistiken per rum utan en kantzon på 0,5 m längs väggarna (SS-EN 12464-1), i små rum mindre, och "
            "utan inredningen på mätytan (skåp, säng och bänkskivor, vita på planen); jämnheten U₀ = minsta / medel. "
            "Rummen är de slutna ytorna mellan väggarna; en öppen planlösning delas mellan rummens namn.",
            "Ritningen ritas med ./mod ljusplan (verktyg/modellering); mätytorna står i modellens el/matytor.py.",
        ]),
        dict(typ="rubrik", text="Teckenförklaring"),
        dict(typ="symboler", rader=[
            {**figur(lambda w: _prov(w, "iso")), "text": "isolinje, med belysningsstyrkan"},
            {**figur(lambda w: _prov(w, "matyta")), "text": "rummets yta i statistiken (utan kantzonen)"},
            {**figur(lambda w: _prov(w, "delomrade")), "text": "delområde med egen statistik"},
            {**figur(lambda w: _prov(w, "armatur")), "text": "armatur"},
            *([{**figur(lambda w: _prov(w, "panel")), "text": "taklampa (LED-panel)"}] if paneler else []),
        ]),
    ]
    b = blad(nummer, ["Ljusplan", str(yta.namn)], f"1:{skala:g}", "Modellen, rendering", kol,
             [v, _fargskala(xb, 20.0)], block, **huvud)
    return b, stat
