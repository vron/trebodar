"""Arbetsritningar för gjutningen av plattorna (#86): allt extra som ska in i mellanbjälklaget (AR-03) och
bottenplattan (AR-04) före gjutningen, ett blad per tema, ur samma data som installationernas ritningar (el,
tappvatten, avlopp, golvvärme, ventilation, köldbärare): elens ingjutna rör och var de går upp och ned, tappvattnets
rör-i-rör, stigare och hylsor, avloppets genomföringar och golvbrunnar, golvvärmens slingor och tillopp (och var man
får borra eller skruva), alla hål och ursparingar och ingjutningsgodset (pelarnas topp- och fotplåtar). Plattornas
egen konstruktion och armering står på R-03–R-06.

Varje blad har plattans snitt, väggarna på plattan streckade (och källarens tunna under mellanbjälklaget),
punkterna numrerade med en tabell över deras lägen x, y i mm från mellanbjälklagets kanter (K-05:s origo, som på
R-04, R-05 och R-06) och vad de är, och en teckenförklaring. Ritas med `./mod gjutning ritning` (i ritningar/, i
./bygg).
"""
from __future__ import annotations

import math
import re
from collections.abc import Callable, Sequence
from typing import Any
from pathlib import Path

from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

from .planritning import (MINSTA_HAL, VAGGAR, Blad, Vy, blad, kompilera, norrpil, origo, papper, plan, polygoner,
                          rita_ytor, svm, vy)

SERIE = "AR-03 Gjutning av mellanbjälklaget"
SERIE_BP = "AR-04 Gjutning av bottenplattan"
SKALA = 75.0
OMRADE = (-500.0, 14300.0, -300.0, 16200.0)          # bladens område (x0, x1, y0, y1) [mm]
MB = (-150.0, 0.0)                                    # mellanbjälklagets under- och överkant
BP = (-2350.0, -2250.0)                               # bottenplattans
R_PUNKT = 0.55                                        # lodrätt rör, ut ur plattan [pappersmm]
NORR = (12900.0, 15300.0)                             # norrpilens läge
FRIZON = 50.0                                         # avståndet från rören i plattan där man inte borrar [mm]
HAL_AVSTAND = 20.0                                    # minsta betong mellan två hål eller ett hål och en plåt [mm]

Punkt = tuple[str, str, float, float, str]            # nummer, vad, x, y, mått


Z = tuple[float, float]                               # plattans under- och överkant


def _i_plattan(a: list[float], b: list[float], z: Z) -> bool:
    return z[0] - 1.0 < a[2] < z[1] + 1.0 and z[0] - 1.0 < b[2] < z[1] + 1.0


def _genom(a: list[float], b: list[float], z: Z) -> str | None:
    """Lodrätt stycke genom plattans över- eller underkant: "upp" eller "ned", annars None."""
    if math.hypot(b[0] - a[0], b[1] - a[1]) > 1.0:
        return None
    lo, hi = sorted((a[2], b[2]))
    if lo < z[1] - 1.0 < z[1] + 1.0 < hi:
        return "upp"
    if lo < z[0] - 1.0 < z[0] + 1.0 < hi:
        return "ned"
    return None


def _vagratt(vag: list[list[float]], z: Z) -> list[list[tuple[float, float]]]:
    """Rörets vågräta följder i plattan (i plan)."""
    ut: list[list[tuple[float, float]]] = []
    cur: list[tuple[float, float]] = []
    for a, b in zip(vag, vag[1:]):
        if _i_plattan(a, b, z) and math.hypot(b[0] - a[0], b[1] - a[1]) > 1.0:
            if not cur:
                cur = [(a[0], a[1])]
            cur.append((b[0], b[1]))
        elif cur:
            ut.append(cur)
            cur = []
    if cur:
        ut.append(cur)
    return ut


def _ror_zon(el: dict, vatten: dict, avlopp: dict, golvvarme: dict, z: Z, plan_: int) -> object:
    """Rören i plattan (alla installationernas, vågräta och lodräta) med FRIZON runt om: där borrar och skruvar man
    inte."""
    g: list[object] = []
    for ror, d in ((el["ror"], "diameter"), (vatten["ror"], None), (avlopp["ledningar"], "d")):
        for r in ror.values():
            r_ = (r[d] if d else 20.0) / 2 + FRIZON
            g += [LineString(f).buffer(r_) for f in _vagratt(r["vag"], z)]
            g += [Point(a[0], a[1]).buffer(r_) for a, b in zip(r["vag"], r["vag"][1:])
                  if math.hypot(b[0] - a[0], b[1] - a[1]) < 1.0 and min(a[2], b[2]) < z[1] and max(a[2], b[2]) > z[0]]
    for h in vatten.get("hylsor", []):
        g.append(Point(*h["punkt"]).buffer(h["d"] / 2 + FRIZON))
    for kr in golvvarme["kretsar"].values():
        if kr["plan"] == plan_:
            pts = [(q[0], q[1]) for q in kr["vag"] if z[0] < q[2] < z[1]]
            if len(pts) > 1:
                g.append(LineString(pts).buffer(10.0 + FRIZON))
    return unary_union(g)


def _matt(t: str) -> tuple[float, float]:
    """Hålets mått ur texten ("Ø50", "250 × 100") som bredd och djup [mm]."""
    tal = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", t)]
    return (tal[0], tal[0]) if t.startswith("Ø") or len(tal) == 1 else (tal[0], tal[1])


def kontroll(platta: object, hal: list[dict], plattor: list[dict], punkter: dict[str, list[Punkt]]
             ) -> tuple[list[str], list[str]]:
    """Ritningens punkter mot modellen: fel för punkter utanför plattan och hål i en pelares plåt, anmärkningar för
    hål som går i varandra (blir en ursparing). platta: plattans yta i snittet; hal: hålen ({punkt, matt,
    element}); plattor: plåtarna; punkter: bladens punkter."""
    fel: list[str] = []
    anm: list[str] = []
    yta = platta.buffer(1.0)  # type: ignore[attr-defined]
    for blad_, pts in punkter.items():
        for _, vad, x, y, _ in pts:
            if not yta.contains(Point(x, y)):
                fel.append(f"{blad_}: {vad} ({x:.0f}, {y:.0f}) ligger utanför plattan")
    former = []
    for h in hal:
        b, d = _matt(h["matt"])
        x, y = h["punkt"][:2]
        former.append((h["element"], Point(x, y).buffer(b / 2) if h["matt"].startswith("Ø")
                       else box(x - b / 2, y - d / 2, x + b / 2, y + d / 2)))
    for i, (a, fa) in enumerate(former):
        for b, fb in former[i + 1:]:
            if fa.distance(fb) < HAL_AVSTAND:
                anm.append(f"{a} och {b}: hålen går i varandra eller har under {HAL_AVSTAND:g} mm betong emellan "
                           f"({fa.distance(fb):.0f} mm); de blir en ursparing")
        for pl in plattor:
            (x, y), (bb, dd) = pl["mitt"], pl["matt"]
            if fa.distance(box(x - bb / 2, y - dd / 2, x + bb / 2, y + dd / 2)) < HAL_AVSTAND:
                fel.append(f"{a}: hålet går i {pl['namn']} eller under {HAL_AVSTAND:g} mm från den")
    return fel, anm


# ------------------------------------------------------------------ teman: (ritar, punkterna)

def _el(v: Vy, el: dict, z: Z) -> list[Punkt]:
    """Elens rör ingjutna i plattan (övre nivån orange, undre mörk) och var de går upp i väggarna (●) eller ned i
    källaren (○)."""
    punkter: list[Punkt] = []
    with v.lager("el"):
        for k, r in el["ror"].items():
            vag = r["vag"]
            for f in _vagratt(vag, z):
                niva = sum(p[2] for p in vag if z[0] < p[2] < z[1]) / max(1, sum(1 for p in vag if z[0] < p[2] < z[1]))
                v.linje(f, "ror_ingjutet" if niva > -75.0 else "ror_ingjutet_uk")
            for a, b in zip(vag, vag[1:]):
                g = _genom(a, b, z)
                if g:
                    v.cirkel(a[0], a[1], R_PUNKT, fyll="#c8661c" if g == "upp" else "vit", stil="tunn")
                    mal = r["till"] if (g == "upp") == (b[2] > a[2]) else r["fran"]
                    punkter.append(("", f"{k} {g} till {mal}", a[0], a[1], f"Ø{r['diameter']:g}"))
    return punkter


def _vatten(v: Vy, vt: dict, z: Z) -> list[Punkt]:
    punkter: list[Punkt] = []
    with v.lager("vatten"):
        for k, r in sorted(vt["ror"].items(), key=lambda kv: kv[1]["media"] != "VV"):
            for f in _vagratt(r["vag"], z):
                v.linje(f, r["media"].lower())
            for a, b in zip(r["vag"], r["vag"][1:]):
                g = _genom(a, b, z)
                if g:
                    v.cirkel(a[0], a[1], R_PUNKT, fyll=r["media"].lower() if g == "upp" else "vit", stil="tunn")
                    punkter.append(("", f"{k} {g}", a[0], a[1], f"{r['matt']}"))
        for h in vt.get("hylsor", []):
            x, y = h["punkt"]
            v.cirkel(x, y, max(h["d"] / 2 / v.s, 1.0), fyll=None, stil="normal")
            punkter.append(("", f"hylsa till {h['tappstalle']} ({h['ror']})", x, y, f"Ø{h['d']:g}"))
    return punkter


def _avlopp(v: Vy, av: dict, z: Z) -> list[Punkt]:
    punkter: list[Punkt] = []
    with v.lager("avlopp"):
        for k, led in av["ledningar"].items():
            vag = led["vag"]
            for f in _vagratt(vag, z):
                v.linje(f, "av_tunn")
            for a, b in zip(vag, vag[1:]):
                if _genom(a, b, z) or (math.hypot(b[0] - a[0], b[1] - a[1]) < 1.0 and min(a[2], b[2]) < z[1] - 1.0
                                       and max(a[2], b[2]) > z[0] + 1.0 and (a[2] > z[1] or b[2] > z[1])):
                    v.cirkel(a[0], a[1], max(led["d"] / 2 / v.s, 0.8), fyll=None, stil="av_tunn")
                    punkter.append(("", f"{k} {led['namn']}", a[0], a[1], f"Ø{led['d']:g}"))
                    break
        for k, g in av["golvbrunnar"].items():
            if z[0] - 1.0 < g["golv"] < z[1] + 1.0:
                x, y = g["punkt"]
                v.cirkel(x, y, max(g["d"] / 2 / v.s, 1.0), fyll="vit", stil="av")
                punkter.append(("", f"golvbrunn {k}", x, y, f"Ø{g['d']:g}"))
    return punkter


def _golvvarme(v: Vy, gv: dict, fritt: object, z: Z, plan_: int) -> list[Punkt]:
    """Golvvärmens slingor och tillopp i plattan och var man får borra eller skruva i den (fritt, grönt): under
    väggarna på den, minst FRIZON från alla rör i plattan."""
    with v.lager("golvvarme_vaggar"):
        rita_ytor(v, fritt, "#e8f1e1", None, MINSTA_HAL)
    with v.lager("golvvarme"):
        for k, kr in gv["kretsar"].items():
            if kr["plan"] == plan_:
                v.linje([(p[0], p[1]) for p in kr["vag"] if z[0] < p[2] < z[1]], "gv")
    punkter: list[Punkt] = []
    for k, f in gv["fordelare"].items():
        if f["plan"] == plan_:
            x, y = f["start"][:2]
            punkter.append(("", f"fördelaren {k}: rören in i plattan", x, y, ""))
    return punkter


def _hal(v: Vy, hal: list[dict], trapphal: list[list[float]]) -> list[Punkt]:
    punkter: list[Punkt] = []
    with v.lager("hal"):
        if trapphal:
            v.polygon([tuple(p) for p in trapphal], "#ffffff", "normal")
            xs, ys = [p[0] for p in trapphal], [p[1] for p in trapphal]
            punkter.append(("", "trapphålet", min(xs), min(ys), f"{max(xs) - min(xs):.0f} × {max(ys) - min(ys):.0f}"))
        for h in hal:
            x, y = h["punkt"][:2]
            v.cirkel(x, y, 1.0, fyll="vit", stil="normal")
            punkter.append(("", f"{h['element']}: {h['atgard']}", x, y, h["matt"]))
    return punkter


# ------------------------------------------------------------------ bladen

_PT = 25.4 / 72.0                                     # en punkt i mm
# etikettens lägen kring punkten: förskjutning (pappersmm, uppåt positiv) och textens ankare, närmast först
_LAGEN = [(1.2, 1.0, "lb"), (-1.2, 1.0, "rb"), (1.2, -1.0, "lt"), (-1.2, -1.0, "rt"), (1.6, 0.0, "lm"),
          (-1.6, 0.0, "rm"), (0.0, 1.6, "cb"), (0.0, -1.6, "ct")]


def _ruta(u: float, v: float, a: str, b: float, h: float) -> tuple[float, float, float, float]:
    """Textens ruta (u0, v0, u1, v1) i pappersmm (v uppåt) med ankaret a i (u, v)."""
    u0 = u - {"l": 0.0, "c": b / 2, "r": b}[a[0]]
    v0 = v - {"b": 0.0, "m": h / 2, "t": h}[a[1]]
    return u0, v0, u0 + b, v0 + h


def _numrera(v: Vy, punkter: list[Punkt], prefix: str, samla: tuple[float, float, float, float] | None = None,
             sz: float = 5.2, r: float = 1.4) -> list[list[str]]:
    """Punkterna numrerade (prefix + löpnummer i y och x) med sitt nummer vid sidan, och tabellens rader. Numret
    hamnar i det första läget runt punkten där det inte täcker ett annat nummer eller en annan punkts symbol (radien
    r pappersmm); går inget läge, längre ut med en hänvisningslinje. Punkterna i området samla (x0, x1, y0, y1),
    som en detalj visar, numreras i följd och får ett gemensamt nummer ("E12–E26")."""
    def i_samla(p: Punkt) -> bool:
        return samla is not None and samla[0] <= p[2] <= samla[1] and samla[2] <= p[3] <= samla[3]
    samlade = [p for p in punkter if i_samla(p)]
    forst = min(((round(p[3] / 50.0), p[2]) for p in samlade), default=(0, 0.0))
    ordnade = sorted(punkter, key=lambda p: (*forst, round(p[3] / 50.0), p[2]) if i_samla(p)
                     else (round(p[3] / 50.0), p[2], 0, 0.0))
    pts = [(x / v.s, y / v.s) for _, _, x, y, _ in ordnade]
    upptaget: list[tuple[float, float, float, float]] = []

    def krock(q: tuple[float, float, float, float], egen: int) -> float:
        u0, v0, u1, v1 = q
        yta = sum(max(0.0, min(u1, a1) - max(u0, a0)) * max(0.0, min(v1, b1) - max(v0, b0))
                  for a0, b0, a1, b1 in upptaget)
        for j, (pu, pv) in enumerate(pts):
            if j != egen and not (samla is not None and i_samla(ordnade[egen]) and i_samla(ordnade[j])):
                du, dv = max(u0 - pu, 0.0, pu - u1), max(v0 - pv, 0.0, pv - v1)
                if du * du + dv * dv < r * r:
                    yta += (r - math.hypot(du, dv)) * r
        return yta

    rader = []
    nummer = [f"{prefix}{i + 1}" for i in range(len(ordnade))]
    lappar: list[tuple[int, str, float, float]] = []        # (punktens index, numret, x, y)
    for i, p in enumerate(ordnade):
        rader.append([nummer[i], p[1], svm(round(p[2])), svm(round(p[3])), p[4]])
        if not i_samla(p):
            lappar.append((i, nummer[i], p[2], p[3]))
    if samlade:
        idx = [i for i, p in enumerate(ordnade) if i_samla(p)]
        xs, ys = [ordnade[i][2] for i in idx], [ordnade[i][3] for i in idx]
        lappar.append((idx[0], f"{nummer[idx[0]]}–{nummer[idx[-1]]}", max(xs), max(ys)))
    for i, nr, x, y in lappar:
        b, h = (0.55 * sz * len(nr) + 1.0) * _PT, (1.25 * sz + 2.0) * _PT
        u, w = x / v.s, y / v.s
        bast: tuple[float, float, float, str, tuple[float, float, float, float]] | None = None
        for k in (1.0, 2.2, 3.4):
            for du, dv, a in _LAGEN:
                q = _ruta(u + du * k, w + dv * k, a, b, h)
                c = krock(q, i)
                if bast is None or c < bast[0] - 1e-9:
                    bast = (c, du * k, dv * k, a, q)
                if c == 0.0:
                    break
            if bast is not None and bast[0] == 0.0:
                break
        assert bast is not None
        _, du, dv, a, q = bast
        upptaget.append(q)
        with v.lager("nummer"):
            if math.hypot(du, dv) > 2.5:
                v.linje([(x + du / math.hypot(du, dv) * 0.9 * v.s, y + dv / math.hypot(du, dv) * 0.9 * v.s),
                         (x + du * v.s, y + dv * v.s)], "tunn")
            v.ptext(x, y, du, dv, nr, a=a, sz=sz, b=True, bg=True)
    return rader


DETALJ = (2330.0, 3060.0, 8820.0, 9140.0)           # centralens rör: området (x0, x1, y0, y1)
SKALA_DETALJ = 10.0


def _detalj_centralen(el: dict, jarn: list[dict], central: dict) -> Vy:
    """Detalj 1:10 ovanför gruppcentralen: rörens stigare i de två raderna (den bakre i V3:s cellplast) mellan
    underkantsnätets järn och V3:s vinkeljärn, kanalen FF3-K2 och måtten från centralens västra kant."""
    x0, x1, y0, y1 = DETALJ
    v = Vy(222.0, 150.0, (x1 - x0) / SKALA_DETALJ, (y1 - y0) / SKALA_DETALJ, SKALA_DETALJ, x0, y1, klipp=True)
    (cx, cy, _), (b, d) = central["topp"], central["matt"]
    with v.lager("detalj"):
        v.rekt(cx - b / 2, cy - d / 2, cx + b / 2, cy + d / 2, "#efefec", "normal")
        v.linje([(x0, central["vagg"]), (x1, central["vagg"])], "normal")
        for j in jarn:
            pts = [tuple(q) for q in j["linje"]]
            if len(pts) == 1:
                v.cirkel(pts[0][0], pts[0][1], j["d"] / 2, fyll="#8a8f94", stil=None, modell=True)
            else:
                v.linje(pts, "stal")
        k = central["kanal"]
        v.rekt(k[0], k[1], k[2], k[3], None, "dold")
    rader: dict[float, list[float]] = {}
    with v.lager("stigare"):
        for nr, r in el["ror"].items():
            if r["fran"] != "GC" or len(r["vag"]) < 3:
                continue
            for a, b_ in zip(r["vag"], r["vag"][1:]):
                if _genom(a, b_, MB) == "ned" or (abs(a[0] - b_[0]) < 1.0 and abs(a[1] - b_[1]) < 1.0
                                                   and min(a[2], b_[2]) < MB[0] < max(a[2], b_[2])):
                    v.cirkel(a[0], a[1], r["diameter"] / 2, fyll="#c8661c", stil="tunn", modell=True)
                    v.ptext(a[0], a[1], 0.0, -1.6, nr.split("-")[0][1:], a="ct", sz=4.2, b=True)
                    rader.setdefault(round(a[1]), []).append(a[0])
                    break
    for i, (y, xs) in enumerate(sorted(rader.items())):
        xx = [cx - b / 2, *sorted(xs)]
        v.mattx(xx, y - 60.0 - 40.0 * i, [y] * len(xx), sz=5.0)
    v.rubrik(x0 + 5.0 * SKALA_DETALJ, y1 + 12.0 * SKALA_DETALJ, "Detalj: rören ur gruppcentralen", round(SKALA_DETALJ),
             sz=8)
    return v


def _ovrigt(v: Vy, plattor: list[dict]) -> list[Punkt]:
    """Ingjutningsgodset: stålplåtarna som gjuts in (källarpelarnas topp- och fotplåtar), med mått."""
    punkter: list[Punkt] = []
    with v.lager("ovrigt"):
        for pl in plattor:
            (x, y), (b, d) = pl["mitt"], pl["matt"]
            v.rekt(x - b / 2, y - d / 2, x + b / 2, y + d / 2, "#8a8f94", "normal")
            punkter.append(("", pl["namn"], x, y, pl["text"]))
    return punkter


def _blad(nummer: str, platta: str, tema: str, prefix: str, snitt_: list[dict], ovan: object, under: object,
          vaggarna: str, rita: Callable[[Vy], list[Punkt]], tecken: list[tuple[str, str]], anvisning: str,
          norr: tuple[float, float], extra: Sequence[Vy] = (),
          samla: tuple[float, float, float, float] | None = None) -> tuple[Blad, list[Punkt]]:
    """Ett blad: plattans snitt, väggarna på plattan (streckade) och under den (tunna), temats rör och punkter,
    tabellen och anvisningarna. ovan, under: väggarnas ytor (shapely) eller None."""
    v = vy(SKALA, OMRADE, 24.0, 20.0)
    plan(v, snitt_)
    with v.lager("vaggar"):
        if under is not None:
            rita_ytor(v, under, None, "hjalp", MINSTA_HAL)
        if ovan is not None:
            rita_ytor(v, ovan, None, "dold", MINSTA_HAL)
    punkter = rita(v)
    rader = _numrera(v, punkter, prefix, samla)
    origo(v)
    norrpil(v, *NORR, norr)
    v.rubrik(*papper(v, 24.0, 14.0), f"{platta}: {tema}", round(SKALA))
    kol: list[dict] = [
        dict(typ="rubrik", text="Anvisningar"),
        dict(typ="lista", sz=7.0, rader=[
            anvisning,
            "Lägen x, y i mm från mellanbjälklagets kanter x = 0 och y = 0 (K-05:s origo, som på R-04, R-05 och "
            "R-06), i rörets, hålets eller plåtens mitt. Mät från plattkanten; kontrollera mot tabellen.",
            f"{vaggarna} Plattans konstruktion och armering: R-03–R-06.",
            "Ritas ur modellen med ./mod gjutning ritning; lägena är installationernas egna (E-01, VS-01, VS-02, VG-01).",
        ]),
        dict(typ="rubrik", text="Teckenförklaring"),
        dict(typ="symboler", rader=[dict(form="linje", stil=st, text=t) for st, t in tecken]),
        dict(typ="rubrik", text="Punkterna"),
        dict(typ="tabell", kolumner=["Nr", "Vad", "x", "y", "Mått"], bredd=(0.35, 2.4, 0.45, 0.45, 0.6),
             just=["l", "l", "r", "r", "l"], sz=5.2, rader=rader),
    ]
    return blad(nummer, [f"Gjutning av {platta.lower()}", tema], f"1:{SKALA:g}", "Modellen", kol,
                [v, *extra]), punkter


def ritningar(el: dict, vatten: dict, avlopp: dict, golvvarme: dict, hal: dict[str, list[dict]],
              trapphal: list[list[float]], plattor: dict[str, list[dict]], snitt_: dict[str, list[dict]],
              norr: tuple[float, float], arbete: Path, ut: Path, jarn: list[dict], central: dict
              ) -> tuple[list[Path], list[str], list[str]]:
    """AR-03 (mellanbjälklaget: elen, tappvattnet, avloppet, golvvärmen, hålen och ingjutningsgodset) och AR-04
    (bottenplattan: golvvärmen, avloppet, hålen och ingjutningsgodset), och kontrollen av deras punkter mot modellen
    (fel och anmärkningar). snitt_: mellanbjälklaget, plan 1, källaren och bottenplattan."""
    mb, plan1, kallare, bp = (snitt_[k] for k in ("mb", "plan1", "kallare", "bp"))
    vaggar_1 = unary_union(polygoner(plan1, bara=VAGGAR))
    vaggar_0 = unary_union(polygoner(kallare, bara=("Hus/Grund", "Hus/Invändigt")))
    fritt_1 = vaggar_1.difference(_ror_zon(el, vatten, avlopp, golvvarme, MB, 1))
    fritt_0 = vaggar_0.difference(_ror_zon(el, vatten, avlopp, golvvarme, BP, 0))
    grund = unary_union(polygoner(kallare, bara=("Hus/Grund",)))
    m_vagg = (vaggar_1, grund, "Plan 1:s väggar är streckade och källarens tunna.")
    b_vagg = (vaggar_0, None, "Källarens väggar på plattan är streckade.")
    borra = (f"Borra och skruva i plattan bara i det gröna: under {{}} väggar och minst {FRIZON:g} mm från alla rör "
             "i plattan (alla installationernas).")
    punkter: dict[str, list[Punkt]] = {}

    def gor(nummer: str, *a: Any, **kw: Any) -> tuple[str, Blad]:
        bl, pts = _blad(nummer, *a, **kw)
        punkter[nummer] = pts
        return nummer, bl

    pdf = []
    nr = [f"{SERIE.split()[0]}.{i}" for i in range(1, 7)]
    m = "Mellanbjälklaget"
    bladen = [
        gor(nr[0], m, "el", "E", mb, *m_vagg, lambda v: _el(v, el, MB),
            [("ror_ingjutet", "elrör ingjutet, övre nivån (Ø16, z −51)"),
             ("ror_ingjutet_uk", "elrör ingjutet, undre nivån (Ø20 och källarens rör, z −100)")],
            "Elrören gjuts in före gjutningen, i sina nivåer: de klena över tappvattnet och golvvärmen, de grova i "
            "tappvattnets nivå utan att korsa det. ● röret går upp i väggen ovanför, ○ ned i källaren. Rören går upp "
            "mellan armeringsjärnen; ur gruppcentralen i två rader enligt detaljen (måtten från centralens västra "
            "kant).", norr, [_detalj_centralen(el, jarn, central)], DETALJ),
        gor(nr[1], m, "tappvatten", "V", mb, *m_vagg, lambda v: _vatten(v, vatten, MB),
            [("vv", "varmvatten, rör-i-rör ingjutet (z −94)"), ("kv", "kallvatten, rör-i-rör ingjutet")],
            "Rör-i-rör läggs i stråken närmast underkantsnätet, c/c 50, och går upp och ned mellan armeringsjärnen. "
            "Hylsorna (PP-avloppsrör) gjuts in mellan järnen; kopparrören dras senare.", norr),
        gor(nr[2], m, "avlopp", "A", mb, *m_vagg, lambda v: _avlopp(v, avlopp, MB),
            [("av_tunn", "avloppsrör genom eller i plattan"), ("av", "golvbrunn, kroppen ingjuten")],
            "Avloppets rör genom plattan gjuts in eller sparas ur (järnen läggs om runt hålen); golvbrunnens kropp "
            "gjuts in med flänsen i plattans överkant. Diskmaskinens pumpade avlopp gjuts in i tappvattnets nivå.",
            norr),
        gor(nr[3], m, "golvvärme", "G", mb, *m_vagg, lambda v: _golvvarme(v, golvvarme, fritt_1, MB, 1),
            [("gv", "golvvärmens slinga och tillopp (z −68)")],
            "Golvvärmens rör läggs på underkantsnätets järn i slingorna. " + borra.format("plan 1:s"), norr),
        gor(nr[4], m, "hål och ursparingar", "H", mb, *m_vagg, lambda v: _hal(v, hal["MB"], trapphal),
            [("normal", "hål eller ursparing")],
            "Alla genomföringar i plattan: hål som sparas ur eller hylsor som gjuts in, med måttet (håltagningen), "
            "och trapphålet. Järnen läggs om runt hålen enligt R-06.", norr),
        gor(nr[5], m, "ingjutningsgods", "Ö", mb, *m_vagg, lambda v: _ovrigt(v, plattor["MB"]),
            [("normal", "stålplåt ingjuten i plattans underkant")],
            "Källarpelarnas topplåtar gjuts in i plattans underkant, mitt över pelarna (K-05, R-05).", norr),
    ]
    pdf.append(ut / f"{SERIE}.pdf")
    kompilera(bladen, arbete / "AR-03", pdf[-1])
    fel, anm = kontroll(unary_union(polygoner(mb, bara=("Hus/Mellanbjälklag",))), hal["MB"], plattor["MB"],
                        {k: v for k, v in punkter.items() if k.startswith("AR-03")})
    nr = [f"{SERIE_BP.split()[0]}.{i}" for i in range(1, 5)]
    b = "Bottenplattan"
    bladen = [
        gor(nr[0], b, "golvvärme", "G", bp, *b_vagg, lambda v: _golvvarme(v, golvvarme, fritt_0, BP, 0),
            [("gv", "golvvärmens slinga och tillopp, mellan armeringsnäten")],
            "Golvvärmens rör läggs mellan armeringsnäten i slingorna, en per rum. " + borra.format("källarens"),
            norr),
        gor(nr[1], b, "avlopp", "A", bp, *b_vagg, lambda v: _avlopp(v, avlopp, BP),
            [("av_tunn", "avloppsrör genom plattan"), ("av", "golvbrunn, kroppen ingjuten")],
            "Golvbrunnarnas kroppar gjuts in med flänsen i plattans överkant; rören genom plattan till "
            "grundledningen under cellplasten (VS-02) gjuts in.", norr),
        gor(nr[2], b, "hål och genomföringar", "H", bp, *b_vagg, lambda v: _hal(v, hal["BP"], []),
            [("normal", "hål eller genomföring")],
            "Alla genomföringar i plattan, med rörets eller brunnens mått. Rören kommer underifrån, ur marken: de "
            "läggs före gjutningen och gjuts in mellan armeringsjärnen (R-04); golvbrunnarnas kroppar gjuts in med "
            "flänsen i överkant.", norr),
        gor(nr[3], b, "ingjutningsgods", "Ö", bp, *b_vagg, lambda v: _ovrigt(v, plattor["BP"]),
            [("normal", "stålplåt ingjuten i plintens överkant")],
            "Källarpelarnas fotplåtar gjuts in i plintarnas överkant (K-05, K-06, R-05).", norr),
    ]
    pdf.append(ut / f"{SERIE_BP}.pdf")
    kompilera(bladen, arbete / "AR-04", pdf[-1])
    f, a = kontroll(unary_union(polygoner(bp, bara=("Hus/Grund/Bottenplatta",))), hal["BP"], plattor["BP"],
                    {k: v for k, v in punkter.items() if k.startswith("AR-04")})
    return pdf, fel + f, anm + a
