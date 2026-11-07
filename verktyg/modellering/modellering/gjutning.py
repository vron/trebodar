"""Arbetsritningar för gjutningen av mellanbjälklaget (#86): allt extra som ska in i plattan före gjutningen, ett blad
per tema, ur samma data som installationernas ritningar (el, tappvatten, avlopp, golvvärme, ventilation): elens
ingjutna rör och var de går upp och ned, tappvattnets rör-i-rör, stigare och hylsor, avloppets genomföringar och
golvbrunnar, golvvärmens slingor och tillopp (och var man inte får borra eller skruva), och alla hål och
ursparingar. Plattans egen konstruktion och armering står på R-03–R-06.

Varje blad har plattans kontur, plan 1:s väggar streckade och källarens väggar tunna, punkterna numrerade med en
tabell över deras lägen x, y i mm från plattans kanter (K-05:s origo, som på R-05 och R-06) och vad de är, och en
teckenförklaring. Ritas med `./mod gjutning ritning` (AR-03 i ritningar/, i ./bygg).
"""
from __future__ import annotations

import math
from collections.abc import Callable
from pathlib import Path

from shapely.geometry import Polygon
from shapely.ops import unary_union

from .planritning import (MINSTA_HAL, VAGGAR, Blad, Vy, blad, kompilera, norrpil, origo, papper, plan, polygoner,
                          rita_ytor, svm, vy)

SERIE = "AR-03 Gjutning av mellanbjälklaget"
SKALA = 75.0
OMRADE = (-500.0, 14300.0, -300.0, 16200.0)          # bladens område (x0, x1, y0, y1) [mm]
Z_UK, Z_OK = -150.0, 0.0                              # mellanbjälklagets under- och överkant
R_PUNKT = 0.55                                        # lodrätt rör, ut ur plattan [pappersmm]
NORR = (12900.0, 15300.0)                             # norrpilens läge

Punkt = tuple[str, str, float, float, str]            # nummer, vad, x, y, mått


def _i_plattan(a: list[float], b: list[float]) -> bool:
    return Z_UK - 1.0 < a[2] < Z_OK + 1.0 and Z_UK - 1.0 < b[2] < Z_OK + 1.0


def _genom(a: list[float], b: list[float]) -> str | None:
    """Lodrätt stycke genom plattans över- eller underkant: "upp" eller "ned", annars None."""
    if math.hypot(b[0] - a[0], b[1] - a[1]) > 1.0:
        return None
    lo, hi = sorted((a[2], b[2]))
    if lo < Z_OK - 1.0 < Z_OK + 1.0 < hi:
        return "upp"
    if lo < Z_UK - 1.0 < Z_UK + 1.0 < hi:
        return "ned"
    return None


def _vagratt(vag: list[list[float]]) -> list[list[tuple[float, float]]]:
    """Rörets vågräta följder i plattan (i plan)."""
    ut: list[list[tuple[float, float]]] = []
    cur: list[tuple[float, float]] = []
    for a, b in zip(vag, vag[1:]):
        if _i_plattan(a, b) and math.hypot(b[0] - a[0], b[1] - a[1]) > 1.0:
            if not cur:
                cur = [(a[0], a[1])]
            cur.append((b[0], b[1]))
        elif cur:
            ut.append(cur)
            cur = []
    if cur:
        ut.append(cur)
    return ut


# ------------------------------------------------------------------ teman: (ritar, punkterna)

def _el(v: Vy, el: dict) -> list[Punkt]:
    """Elens rör ingjutna i plattan (övre nivån orange, undre mörk) och var de går upp i väggarna (●) eller ned i
    källaren (○)."""
    punkter: list[Punkt] = []
    with v.lager("el"):
        for k, r in el["ror"].items():
            vag = r["vag"]
            for f in _vagratt(vag):
                niva = sum(p[2] for p in vag if Z_UK < p[2] < Z_OK) / max(1, sum(1 for p in vag if Z_UK < p[2] < Z_OK))
                v.linje(f, "ror_ingjutet" if niva > -75.0 else "ror_ingjutet_uk")
            for a, b in zip(vag, vag[1:]):
                g = _genom(a, b)
                if g:
                    v.cirkel(a[0], a[1], R_PUNKT, fyll="#c8661c" if g == "upp" else "vit", stil="tunn")
                    mal = r["till"] if (g == "upp") == (b[2] > a[2]) else r["fran"]
                    punkter.append(("", f"{k} {g} till {mal}", a[0], a[1], f"Ø{r['diameter']:g}"))
    return punkter


def _vatten(v: Vy, vt: dict) -> list[Punkt]:
    punkter: list[Punkt] = []
    with v.lager("vatten"):
        for k, r in sorted(vt["ror"].items(), key=lambda kv: kv[1]["media"] != "VV"):
            for f in _vagratt(r["vag"]):
                v.linje(f, r["media"].lower())
            for a, b in zip(r["vag"], r["vag"][1:]):
                g = _genom(a, b)
                if g:
                    v.cirkel(a[0], a[1], R_PUNKT, fyll=r["media"].lower() if g == "upp" else "vit", stil="tunn")
                    punkter.append(("", f"{k} {g}", a[0], a[1], f"{r['matt']}"))
        for h in vt.get("hylsor", []):
            x, y = h["punkt"]
            v.cirkel(x, y, max(h["d"] / 2 / v.s, 1.0), fyll=None, stil="normal")
            punkter.append(("", f"hylsa till {h['tappstalle']} ({h['ror']})", x, y, f"Ø{h['d']:g}"))
    return punkter


def _avlopp(v: Vy, av: dict) -> list[Punkt]:
    punkter: list[Punkt] = []
    with v.lager("avlopp"):
        for k, led in av["ledningar"].items():
            vag = led["vag"]
            for f in _vagratt(vag):
                v.linje(f, "av_tunn")
            for a, b in zip(vag, vag[1:]):
                if _genom(a, b) or (math.hypot(b[0] - a[0], b[1] - a[1]) < 1.0 and min(a[2], b[2]) < Z_OK - 1.0
                                    and max(a[2], b[2]) > Z_UK + 1.0 and (a[2] > Z_OK or b[2] > Z_OK)):
                    v.cirkel(a[0], a[1], max(led["d"] / 2 / v.s, 0.8), fyll=None, stil="av_tunn")
                    punkter.append(("", f"{k} {led['namn']}", a[0], a[1], f"Ø{led['d']:g}"))
                    break
        for k, g in av["golvbrunnar"].items():
            if g["golv"] > Z_UK:
                x, y = g["punkt"]
                v.cirkel(x, y, max(g["d"] / 2 / v.s, 1.0), fyll="vit", stil="av")
                punkter.append(("", f"golvbrunn {k}", x, y, f"Ø{g['d']:g}"))
    return punkter


def _golvvarme(v: Vy, gv: dict, vaggar: Polygon) -> list[Punkt]:
    """Golvvärmens slingor och tillopp på plan 1 och var man inte får borra eller skruva i plattan: under plan 1:s
    väggar (slingorna går utanför dem) och i ett band runt slingorna."""
    with v.lager("golvvarme_vaggar"):
        rita_ytor(v, vaggar, "#e8f1e1", None, MINSTA_HAL)
    with v.lager("golvvarme"):
        for k, kr in gv["kretsar"].items():
            if kr["plan"] == 1:
                v.linje([(p[0], p[1]) for p in kr["vag"] if Z_UK < p[2] < Z_OK], "gv")
    punkter: list[Punkt] = []
    for k, f in gv["fordelare"].items():
        if f["plan"] == 1:
            x, y = f["start"][:2]
            punkter.append(("", f"fördelaren {k}, rören ned ur plattan", x, y, ""))
    return punkter


def _hal(v: Vy, hal: list[dict], trapphal: list[list[float]]) -> list[Punkt]:
    punkter: list[Punkt] = []
    with v.lager("hal"):
        v.polygon([tuple(p) for p in trapphal], "#ffffff", "normal")
        xs, ys = [p[0] for p in trapphal], [p[1] for p in trapphal]
        punkter.append(("", "trapphålet", min(xs), min(ys), f"{max(xs) - min(xs):.0f} × {max(ys) - min(ys):.0f}"))
        for h in hal:
            x, y = h["punkt"][:2]
            v.cirkel(x, y, 1.0, fyll="vit", stil="normal")
            punkter.append(("", f"{h['element']}: {h['atgard']}", x, y, h["matt"]))
    return punkter


# ------------------------------------------------------------------ bladen

def _numrera(v: Vy, punkter: list[Punkt], prefix: str) -> list[list[str]]:
    """Punkterna numrerade (prefix + löpnummer i y och x) med sitt nummer vid sidan, och tabellens rader."""
    rader = []
    for i, (_, vad, x, y, matt) in enumerate(sorted(punkter, key=lambda p: (round(p[3] / 50.0), p[2]))):
        nr = f"{prefix}{i + 1}"
        with v.lager("nummer"):
            v.ptext(x, y, 1.2, 1.0, nr, a="lb", sz=5.2, b=True, bg=True)
        rader.append([nr, vad, svm(round(x)), svm(round(y)), matt])
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
                if _genom(a, b_) == "ned" or (abs(a[0] - b_[0]) < 1.0 and abs(a[1] - b_[1]) < 1.0
                                               and min(a[2], b_[2]) < Z_UK < max(a[2], b_[2])):
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


def _blad(nummer: str, tema: str, prefix: str, mb: list[dict], plan1: list[dict], kallare: list[dict],
          rita: Callable[[Vy], list[Punkt]], tecken: list[tuple[str, str]], anvisning: str,
          norr: tuple[float, float], extra: list[Vy] = ()) -> Blad:
    x0, x1, y0, y1 = OMRADE
    v = vy(SKALA, OMRADE, 24.0, 20.0)
    plan(v, mb)
    with v.lager("vaggar"):
        rita_ytor(v, unary_union(polygoner(kallare, bara=("Hus/Grund",))), None, "hjalp", MINSTA_HAL)
        rita_ytor(v, unary_union(polygoner(plan1, bara=VAGGAR)), None, "dold", MINSTA_HAL)
    punkter = rita(v)
    rader = _numrera(v, punkter, prefix)
    origo(v)
    norrpil(v, *NORR, norr)
    v.rubrik(*papper(v, 24.0, 14.0), f"Mellanbjälklaget: {tema}", round(SKALA))
    kol: list[dict] = [
        dict(typ="rubrik", text="Anvisningar"),
        dict(typ="lista", sz=7.0, rader=[
            anvisning,
            "Lägen x, y i mm från mellanbjälklagets kanter x = 0 och y = 0 (K-05:s origo, som på R-05 och R-06), i "
            "rörets eller hålets mitt. Mät från plattkanten; kontrollera mot tabellen.",
            "Plan 1:s väggar är streckade och källarens väggar tunna. Plattans konstruktion och armering: R-03–R-06.",
            "Ritas ur modellen med ./mod gjutning ritning; lägena är installationernas egna (E-01, VS-01, VS-02, VG-01).",
        ]),
        dict(typ="rubrik", text="Teckenförklaring"),
        dict(typ="symboler", rader=[dict(form="linje", stil=s, text=t) for s, t in tecken]),
        dict(typ="rubrik", text="Punkterna"),
        dict(typ="tabell", kolumner=["Nr", "Vad", "x", "y", "Mått"], bredd=(0.35, 2.4, 0.45, 0.45, 0.6),
             just=["l", "l", "r", "r", "l"], sz=5.2, rader=rader),
    ]
    return blad(nummer, ["Gjutning av mellanbjälklaget", tema], f"1:{SKALA:g}", "Modellen", kol, [v, *extra])


def ritningar(el: dict, vatten: dict, avlopp: dict, golvvarme: dict, hal: list[dict], trapphal: list[list[float]],
              mb: list[dict], plan1: list[dict], kallare: list[dict], norr: tuple[float, float], arbete: Path,
              ut: Path, jarn: list[dict], central: dict) -> Path:
    """AR-03.1–AR-03.5: elen, tappvattnet, avloppet, golvvärmen och hålen i mellanbjälklaget."""
    nr = [f"{SERIE.split()[0]}.{i}" for i in range(1, 6)]
    vaggar = unary_union(polygoner(plan1, bara=VAGGAR))
    bladen = [
        (nr[0], _blad(nr[0], "el", "E", mb, plan1, kallare, lambda v: _el(v, el),
                      [("ror_ingjutet", "elrör ingjutet, övre nivån (Ø16, z −51)"),
                       ("ror_ingjutet_uk", "elrör ingjutet, undre nivån (Ø20 och källarens rör, z −100)")],
                      "Elrören gjuts in före gjutningen, i sina nivåer: de klena över tappvattnet och golvvärmen, de "
                      "grova i tappvattnets nivå utan att korsa det. ● röret går upp i väggen ovanför, ○ ned i "
                      "källaren. Rören går upp mellan armeringsjärnen; ur gruppcentralen i två rader enligt detaljen "
                      "(måtten från centralens västra kant).", norr, [_detalj_centralen(el, jarn, central)])),
        (nr[1], _blad(nr[1], "tappvatten", "V", mb, plan1, kallare, lambda v: _vatten(v, vatten),
                      [("vv", "varmvatten, rör-i-rör ingjutet (z −94)"), ("kv", "kallvatten, rör-i-rör ingjutet")],
                      "Rör-i-rör läggs i stråken närmast underkantsnätet, c/c 50, och går upp och ned mellan "
                      "armeringsjärnen. Hylsorna (PP-avloppsrör) gjuts in mellan järnen; kopparrören dras senare.",
                      norr)),
        (nr[2], _blad(nr[2], "avlopp", "A", mb, plan1, kallare, lambda v: _avlopp(v, avlopp),
                      [("av_tunn", "avloppsrör genom eller i plattan"), ("av", "golvbrunn, kroppen ingjuten")],
                      "Avloppets rör genom plattan gjuts in eller sparas ur (järnen läggs om runt hålen); "
                      "golvbrunnens kropp gjuts in med flänsen i plattans överkant. Diskmaskinens pumpade avlopp "
                      "gjuts in i tappvattnets nivå.", norr)),
        (nr[3], _blad(nr[3], "golvvärme", "G", mb, plan1, kallare, lambda v: _golvvarme(v, golvvarme, vaggar),
                      [("gv", "golvvärmens slinga och tillopp (z −68)")],
                      "Golvvärmens rör läggs på underkantsnätets järn i slingorna. Borra och skruva i plattan bara "
                      "under plan 1:s väggar (grönt), där inga rör går; utanför dem kan det gå rör.", norr)),
        (nr[4], _blad(nr[4], "hål och ursparingar", "H", mb, plan1, kallare, lambda v: _hal(v, hal, trapphal),
                      [("normal", "hål eller ursparing")],
                      "Alla genomföringar i plattan: hål som sparas ur eller hylsor som gjuts in, med måttet "
                      "(håltagningen), och trapphålet. Järnen läggs om runt hålen enligt R-06.", norr)),
    ]
    pdf = ut / f"{SERIE}.pdf"
    kompilera(bladen, arbete, pdf)
    return pdf

