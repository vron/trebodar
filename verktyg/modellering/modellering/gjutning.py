"""Arbetsritningar för gjutningen av plattorna (#86): allt extra som ska in i mellanbjälklaget (AR-03) och
bottenplattan (AR-04) före gjutningen, ett blad per tema, ur samma data som installationernas ritningar (el,
tappvatten, avlopp, golvvärme, ventilation, köldbärare): elens ingjutna rör och var de går upp och ned, tappvattnets
rör-i-rör, stigare och hylsor, avloppets genomföringar och golvbrunnar, golvvärmens slingor och tillopp (och var man
får borra eller skruva), alla hål och ursparingar och ingjutningsgodset (pelarnas topp- och fotplåtar). Plattornas
egen konstruktion och armering står på R-03–R-06.

Varje blad har plattans snitt, väggarna på plattan streckade (och källarens tunna under mellanbjälklaget),
punkterna numrerade och måttsatta från närmaste fasta referens (plattans kant, hålets kant, källarväggens liv; i rad
som måttkedjor), detaljer 1:10 där det är tätt (centralens och drivdonsskåpets rör, tappvattnets stigare vid V19,
köket vid V14), en tabell över punkternas lägen x, y i mm från mellanbjälklagets kanter (K-05:s origo, som på R-04,
R-05 och R-06) och vad de är, och en teckenförklaring. Punkterna kontrolleras mot modellen (kontroll). Ritas med
`./mod gjutning ritning` (i ritningar/, i ./bygg).
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


def _fordelarna(vt: dict) -> dict[str, list[tuple[str, list[float], list[float]]]]:
    """Tappvattnets fördelare och underfördelare under plattan som stänger (media, start och slut i plan) per
    fördelare: FD (huvudfördelarna i teknikrummet), UF1, UF2."""
    ut: dict[str, list[tuple[str, list[float], list[float]]]] = {}
    for f in vt.get("fordelare", {}).values():
        ut.setdefault("FD", []).append((f["media"], f["start"][:2], f["slut"][:2]))
    for k, uf in vt.get("underfordelare", {}).items():
        for st in uf.get("stammar", {}).values():
            ut.setdefault(k, []).append((st["media"], st["start"][:2], st["slut"][:2]))
    return ut


# ------------------------------------------------------------------ teman: (ritar, punkterna)

def _el(v: Vy, el: dict, z: Z) -> list[Punkt]:
    """Elens rör ingjutna i plattan (övre nivån orange, undre mörk), var de går upp i väggarna (●) eller ned i
    källaren (○), och de ingjutna dosorna i källarens tak (□): kopplingsdosorna och dosorna ovanför armaturerna som
    sitter utanpå taket."""
    punkter: list[Punkt] = []
    with v.lager("dosor"):
        for k, p in el["punkter"].items():
            t = el["typer"][p["typ"]]
            dosa = t.get("dosa") if p["slag"] == "lampa" else t if t.get("slag") == "ingjutningsdosa" else None
            if p["yta"] != "tak" or p["ref"] != "MB" or not dosa:
                continue
            x, y = p["punkt"][:2]
            s = max(dosa["diameter"] / 2, v.s * 0.7)
            v.rekt(x - s, y - s, x + s, y + s, "vit", "normal")
            vad = (f"dosa för {k} ({'panel' if t.get('symbol') == 'panel' else 'spot'})" if p["slag"] == "lampa"
                   else f"kopplingsdosa {k}")
            punkter.append(("", vad, x, y, f"Ø{dosa['diameter']:g} × {dosa['djup']:g}"))
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
            # rören som slutar i plattans undersida (ljuslinjernas 24 V): rörändan tätas vid gjutningen, armaturen
            # täcker den
            for i, mal in ((0, r["fran"]), (len(vag) - 1, r["till"])):
                q, nasta = vag[i], vag[1 if i == 0 else -2]
                if ("linje" in el["punkter"].get(mal, {}) and abs(q[2] - z[0]) < 1.0
                        and math.hypot(nasta[0] - q[0], nasta[1] - q[1]) < 1.0 and nasta[2] > q[2]):
                    v.cirkel(q[0], q[1], R_PUNKT, fyll="vit", stil="normal")
                    v.cirkel(q[0], q[1], R_PUNKT * 0.35, fyll="svart", stil=None)
                    punkter.append(("", f"{k} rörände för {mal} (24 V), tätas", q[0], q[1], f"Ø{r['diameter']:g}"))
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
    with v.lager("fordelare"):
        for namn, stanger in _fordelarna(vt).items():
            for _, a, b in stanger:
                v.polygon([tuple(q) for q in LineString([a, b]).buffer(25.0, cap_style=2).exterior.coords], None,
                          "dold")
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

Ruta = tuple[float, float, float, float]               # (u0, v0, u1, v1) i pappersmm, v uppåt
Kant = tuple[float, float, float]                     # (läge, från, till): en lodrät (x, y0, y1) eller vågrät kant
SZ_MATT = 4.6                                         # måttens text [pt]
AVSTAND_MATT = 1.3                                    # måttlinjen från punkten [pappersmm]


def _kanter(*geom: object) -> tuple[list[Kant], list[Kant]]:
    """Ytornas axelparallella kanter (ytterkant och hål) längre än 100 mm: de lodräta (x, y0, y1) och vågräta."""
    lod: list[Kant] = []
    vag: list[Kant] = []
    for g in geom:
        for p in getattr(g, "geoms", [g]):
            if not isinstance(p, Polygon) or p.area < 0.2e6:          # inte pelarna
                continue
            for ring in (p.exterior, *p.interiors):
                c = list(ring.coords)
                for (x0, y0), (x1, y1) in zip(c, c[1:]):
                    if abs(x1 - x0) < 0.5 and abs(y1 - y0) > 100.0:
                        lod.append((x0, min(y0, y1), max(y0, y1)))
                    elif abs(y1 - y0) < 0.5 and abs(x1 - x0) > 100.0:
                        vag.append((y0, min(x0, x1), max(x0, x1)))
    return lod, vag


def _narmast(a: float, b: float, kanter: list[Kant], lodratt: bool, betong: object) -> float | None:
    """Närmaste kant från läget a längs axeln (x, eller y om lodratt), vid b tvärs den (kanten ska täcka b), utom
    kanter genom a; måttet ska gå i betongen (inte över ett hål)."""
    kand = sorted((abs(k - a), k) for k, k0, k1 in kanter if k0 - 1.0 <= b <= k1 + 1.0 and abs(k - a) > 1.0)
    for _, k in kand:
        m = (b, (a + k) / 2) if lodratt else ((a + k) / 2, b)
        if betong.contains(Point(*m)):  # type: ignore[attr-defined]
            return k
    return None


def _textruta(v: Vy, x: float, y: float, txt: str, lodratt: bool, sida: int = 1) -> Ruta:
    """Måttextens ruta i pappersmm: ankare cb (sida 1: över en vågrät linje, till vänster om en lodrät, där texten är
    vriden 90°) eller ct (sida -1: under, till höger)."""
    b, h = len(txt) * 0.19 * SZ_MATT + 0.8, SZ_MATT * _PT + 0.4
    u, w = x / v.s, y / v.s
    if lodratt:
        return (u - h, w - b / 2, u, w + b / 2) if sida == 1 else (u, w - b / 2, u + h, w + b / 2)
    return (u - b / 2, w, u + b / 2, w + h) if sida == 1 else (u - b / 2, w - h, u + b / 2, w)


def _ledig(q: Ruta, upptaget: list[Ruta]) -> bool:
    return all(min(q[2], a[2]) <= max(q[0], a[0]) or min(q[3], a[3]) <= max(q[1], a[1]) for a in upptaget)


def _matt_linje(v: Vy, lagen: list[tuple[float, float]], lodratt: bool, upptaget: list[Ruta]) -> None:
    """Måttkedja längs en axel genom lagen (a, b): a längs axeln, b tvärs (kanten först, sedan punkterna i ordning),
    förskjuten AVSTAND_MATT ovanför (vågrät) eller till vänster om (lodrät) punkterna, med hjälplinjer från punkterna
    och snedstreck. Varje text hamnar mitt på sitt mått, på linjens andra sida eller utanför änden, där den inte
    täcker en annan text."""
    s = v.s
    xy = (lambda a, b: (b, a)) if lodratt else (lambda a, b: (a, b))
    sg = -1.0 if lodratt else 1.0                              # åt vänster (lodrät) eller uppåt (vågrät)
    bs = [b for _, b in lagen[1:]]
    r = (min(bs) if lodratt else max(bs)) + sg * AVSTAND_MATT * s
    aa: list[float] = []
    for a, _ in lagen:
        if not aa or abs(a - aa[-1]) > 1.0:
            aa.append(a)
    with v.lager("matt"):
        for i, (a, b) in enumerate(lagen):
            if i > 0:
                v.linje([xy(a, b + sg * 0.9 * s), xy(a, r + sg * 0.5 * s)], "matt")
        for a in aa:
            sl = 0.75 * s
            v.linje([xy(a - sl, r - sl), xy(a + sl, r + sl)], "tunn")
        v.linje([xy(min(aa) - 1.0 * s, r), xy(max(aa) + 1.0 * s, r)], "matt")
        for a, b in zip(aa, aa[1:]):
            txt = svm(round(abs(b - a)))
            bredd = len(txt) * 0.19 * SZ_MATT + 0.8
            ute = math.copysign((bredd / 2 + 1.2) * s, b - a)
            kand = ([((a + b) / 2, 1), ((a + b) / 2, -1)] if abs(b - a) / s > bredd + 0.6 else []) + \
                [(a - ute, 1), (b + ute, 1), (a - ute, -1), (b + ute, -1)]
            val = None
            for m, sida in kand:
                x, y = xy(m, r + sida * sg * 0.5 * s)
                q = _textruta(v, x, y, txt, lodratt, sida)
                if val is None:
                    val = (x, y, sida, q)
                if _ledig(q, upptaget):
                    val = (x, y, sida, q)
                    break
            assert val is not None
            x, y, sida, q = val
            v.text(x, y, txt, a="cb" if sida == 1 else "ct", sz=SZ_MATT, rot=90 if lodratt else 0)
            upptaget.append(q)


def _lagesmatt(v: Vy, punkter: list[Punkt], kanter: tuple[list[Kant], list[Kant]], betong: object,
               samla: Sequence[Omrade] = ()) -> list[Ruta]:
    """Punkternas lägen måttsatta från närmaste fasta referens (plattans kant, hålets kant, källarväggens liv) i x och
    y. Punkter i rad mot samma kant (inom 0,8 pappersmm) blir en måttkedja. Ett samlat område (en detalj) måttsätts
    här bara med sin första punkt; resten står i detaljen. Ger måttextens rutor (för numren)."""
    lod, vag = kanter
    ordnade = _ordna(punkter, samla)
    unika: dict[tuple[int, int], None] = {}
    sett: set[int] = set()
    for _, _, x, y, _ in ordnade:
        i = next((i for i, o in enumerate(samla) if _i(o, x, y)), None)
        if i is None or i not in sett:
            unika[(round(x), round(y))] = None
            if i is not None:
                sett.add(i)
    grupper: dict[tuple[bool, float, int], list[tuple[float, float]]] = {}
    for x, y in unika:
        for lodratt, a, b, ks in ((False, x, y, lod), (True, y, x, vag)):
            k = _narmast(a, b, ks, lodratt, betong)
            if k is not None:
                grupper.setdefault((lodratt, k, 1 if a > k else -1), []).append((a, b))
    upptaget: list[Ruta] = []
    tol = 0.8 * v.s
    for (lodratt, k, _), ab in sorted(grupper.items()):
        rad: list[tuple[float, float]] = []
        for pa, pb in sorted(ab, key=lambda q: q[1]):
            if rad and pb - rad[-1][1] > tol:
                _matt_linje(v, [(k, rad[0][1]), *sorted(rad, key=lambda q: abs(q[0] - k))], lodratt, upptaget)
                rad = []
            rad.append((pa, pb))
        if rad:
            _matt_linje(v, [(k, rad[0][1]), *sorted(rad, key=lambda q: abs(q[0] - k))], lodratt, upptaget)
    return upptaget


_PT = 25.4 / 72.0                                     # en punkt i mm
# etikettens lägen kring punkten: förskjutning (pappersmm, uppåt positiv) och textens ankare, närmast först
_LAGEN = [(1.2, 1.0, "lb"), (-1.2, 1.0, "rb"), (1.2, -1.0, "lt"), (-1.2, -1.0, "rt"), (1.6, 0.0, "lm"),
          (-1.6, 0.0, "rm"), (0.0, 1.6, "cb"), (0.0, -1.6, "ct")]


def _ruta(u: float, v: float, a: str, b: float, h: float) -> tuple[float, float, float, float]:
    """Textens ruta (u0, v0, u1, v1) i pappersmm (v uppåt) med ankaret a i (u, v)."""
    u0 = u - {"l": 0.0, "c": b / 2, "r": b}[a[0]]
    v0 = v - {"b": 0.0, "m": h / 2, "t": h}[a[1]]
    return u0, v0, u0 + b, v0 + h


Omrade = tuple[float, float, float, float]            # (x0, x1, y0, y1) [mm]
Nummer = dict[tuple[int, int], list[str]]             # punktens läge (avrundat) -> dess nummer


def _i(o: Omrade, x: float, y: float) -> bool:
    return o[0] <= x <= o[1] and o[2] <= y <= o[3]


def _placera(v: Vy, lappar: list[tuple[str, float, float]], hinder: list[tuple[float, float]], upptaget: list[Ruta],
             sz: float = 5.2, r: float = 1.4) -> None:
    """Numren (text, x, y) i det första läget runt sin punkt där de inte täcker en upptagen ruta eller en punkt i
    hinder (radien r pappersmm, utom den egna); går inget läge, längre ut med en hänvisningslinje."""
    pts = [(x / v.s, y / v.s) for x, y in hinder]

    def krock(q: Ruta, u: float, w: float) -> float:
        u0, v0, u1, v1 = q
        yta = sum(max(0.0, min(u1, a1) - max(u0, a0)) * max(0.0, min(v1, b1) - max(v0, b0))
                  for a0, b0, a1, b1 in upptaget)
        for pu, pv in pts:
            if abs(pu - u) > 1e-6 or abs(pv - w) > 1e-6:
                du, dv = max(u0 - pu, 0.0, pu - u1), max(v0 - pv, 0.0, pv - v1)
                if du * du + dv * dv < r * r:
                    yta += (r - math.hypot(du, dv)) * r
        return yta

    for nr, x, y in lappar:
        b, h = (0.55 * sz * len(nr) + 1.0) * _PT, (1.25 * sz + 2.0) * _PT
        u, w = x / v.s, y / v.s
        bast: tuple[float, float, float, str, Ruta] | None = None
        for k in (1.0, 2.2, 3.4):
            for du, dv, a in _LAGEN:
                q = _ruta(u + du * k, w + dv * k, a, b, h)
                c = krock(q, u, w)
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


def _ordna(punkter: list[Punkt], samla: Sequence[Omrade]) -> list[Punkt]:
    """Punkterna i numreringens ordning: i y och x, men varje samlat område (en detalj) i följd, där dess första
    punkt hade kommit."""
    def omr(p: Punkt) -> int | None:
        return next((i for i, o in enumerate(samla) if _i(o, p[2], p[3])), None)
    forst: dict[int, tuple[int, float]] = {}
    for p in punkter:
        if (i := omr(p)) is not None:
            k = (round(p[3] / 50.0), p[2])
            forst[i] = min(forst.get(i, k), k)

    def nyckel(p: Punkt) -> tuple[int, float, int, float]:
        i = omr(p)
        return (*forst[i], round(p[3] / 50.0), p[2]) if i is not None else (round(p[3] / 50.0), p[2], 0, 0.0)
    return sorted(punkter, key=nyckel)


def _numrera(v: Vy, punkter: list[Punkt], prefix: str, samla: Sequence[Omrade] = (),
             upptaget: list[Ruta] | None = None) -> tuple[list[list[str]], Nummer]:
    """Punkterna numrerade (prefix + löpnummer i y och x) med sitt nummer vid sidan (_placera), tabellens rader och
    numren per läge. Punkterna i ett område i samla, som en detalj visar, numreras i följd och får på planen ett
    gemensamt nummer ("E12–E26")."""
    ordnade = _ordna(punkter, samla)
    nummer = [f"{prefix}{i + 1}" for i in range(len(ordnade))]
    rader = [[nummer[i], p[1], svm(round(p[2])), svm(round(p[3])), p[4]] for i, p in enumerate(ordnade)]
    per_lage: Nummer = {}
    for i, p in enumerate(ordnade):
        per_lage.setdefault((round(p[2]), round(p[3])), []).append(nummer[i])
    lappar: list[tuple[str, float, float]] = []
    for (x, y), nr in per_lage.items():
        if not any(_i(o, x, y) for o in samla):
            lappar.append(("/".join(nr), x, y))
    for o in samla:
        idx = [i for i, p in enumerate(ordnade) if _i(o, p[2], p[3])]
        if idx:
            xs, ys = [ordnade[i][2] for i in idx], [ordnade[i][3] for i in idx]
            lappar.append((f"{nummer[idx[0]]}–{nummer[idx[-1]]}", max(xs), max(ys)))
    _placera(v, lappar, [(float(x), float(y)) for x, y in per_lage], list(upptaget or []))
    return rader, per_lage


TABELL_EL = (226.0, 14.0, 48.0)       # AR-03.1:s punkttabell i två spalter till höger på ritytan, över detaljen
DETALJ = (2330.0, 3060.0, 8820.0, 9140.0)           # el: rören ur gruppcentralen (x0, x1, y0, y1)
DETALJ_LC = (3090.0, 3670.0, 7690.0, 7935.0)         # el: rören ur drivdonsskåpet på KL8 (öster om P4)
DETALJ_VATTEN = (4150.0, 4500.0, 7980.0, 9080.0)     # tappvatten: stigarna ur källaren vid V19
DETALJ_KOK = (13280.0, 13520.0, 8300.0, 8900.0)      # köket vid V14: hylsorna, diskbänkens avlopp, UF1
DETALJER = (DETALJ, DETALJ_LC, DETALJ_VATTEN, DETALJ_KOK)
SKALA_DETALJ = 10.0
Element = dict                                        # detaljens innehåll: {"linje", "r", "fyll"} eller {"punkt", ...}
Detalj = Callable[[Nummer], list[Vy]]


def _ram(o: Omrade, plats: tuple[float, float], titel: str, under: Sequence[str] = (), topp: float = 0.0
         ) -> tuple[Vy, Vy]:
    """En detalj 1:10: vyn (klippt till området) och en oklippt, större vy runt den med ram, rubrik och undertexter
    (topp pappersmm över ramen, där det ska ritas något annat); måtten och numren ritas i den oklippta, utanför eller
    över ramen."""
    x0, x1, y0, y1 = o
    s = SKALA_DETALJ
    w, h, m = (x1 - x0) / s, (y1 - y0) / s, 16.0 + topp
    v = Vy(plats[0], plats[1], w, h, s, x0, y1, klipp=True)
    ram = Vy(plats[0] - m, plats[1] - m, w + 2 * m + 50.0, h + 2 * m, s, x0 - m * s, y1 + m * s)
    with ram.lager("ram"):
        ram.rekt(x0, y0, x1, y1, None, "tunn")
        rader = [f"Skala 1:{s:g}", *under]
        ram.text(x0, y1 + (topp + 2.0 + 2.6 * len(rader)) * s, titel, a="lb", sz=8, b=True)
        for i, t in enumerate(rader):
            ram.text(x0, y1 + (topp + 1.6 + 2.6 * (len(rader) - 1 - i)) * s, t, a="lb", sz=6.0, col="gra")
    return v, ram


def _jarnen(v: Vy, jarn: list[dict]) -> None:
    for j in jarn:
        pts = [tuple(q) for q in j["linje"]]
        if len(pts) == 1:
            v.cirkel(pts[0][0], pts[0][1], j["d"] / 2, fyll="#8a8f94", stil=None, modell=True)
        else:
            v.linje(pts, "stal")


def _detalj(titel: str, o: Omrade, plats: tuple[float, float], vaggar: object, jarn: list[dict],
            element: list[Element], kanter: tuple[list[Kant], list[Kant]]) -> Detalj:
    """Detalj 1:10 av ett tätt område: källarväggarna (grått), armeringsjärnen, rören och hålen i skala och
    punkternas nummer från planen, med måttkedjor utanför ramen från väggarnas liv inom området (annars från den
    första punkten, som är måttsatt på planen)."""
    x0, x1, y0, y1 = o
    pts = sorted({(round(e["punkt"][0]), round(e["punkt"][1])) for e in element if "punkt" in e},
                 key=lambda q: (q[1], q[0]))
    lod = [k for k, k0, k1 in kanter[0] if x0 < k < x1 and k0 <= min(q[1] for q in pts) and k1 >= max(q[1] for q in pts)]
    vag = [k for k, k0, k1 in kanter[1] if y0 < k < y1 and k0 <= min(q[0] for q in pts) and k1 >= max(q[0] for q in pts)]

    def rita(nummer: Nummer) -> list[Vy]:
        forsta = "/".join(nummer.get(pts[0], ["?"]))
        under = [f"x: måtten från {'väggens liv' if lod else forsta}", f"y: måtten från {'väggens liv' if vag else forsta}"]
        if not (lod and vag):
            under.append(f"{forsta} är måttsatt på planen")
        if fd := sorted({e["etikett"] for e in element if "etikett" in e}):
            under.append(f"streckat: {', '.join(fd)} under plattan")
        v, ram = _ram(o, plats, titel, under)
        with v.lager("detalj"):
            rita_ytor(v, vaggar.intersection(box(x0, y0, x1, y1)), "#e4e4df", None)  # type: ignore[attr-defined]
            for e in element:
                if "linje" in e and e.get("under"):
                    rita_ytor(v, LineString(e["linje"]).buffer(e["r"], cap_style=2), e["fyll"], e.get("stil", "tunn"))
            _jarnen(v, jarn)
            for e in element:
                if "linje" in e and not e.get("under"):
                    rita_ytor(v, LineString(e["linje"]).buffer(e["r"], cap_style=2), e["fyll"], e.get("stil", "tunn"))
            for e in element:
                if "punkt" in e:
                    v.cirkel(*e["punkt"], e["r"], fyll=e["fyll"], stil=e.get("stil", "tunn"), modell=True)

        s = SKALA_DETALJ
        xs = sorted({q[0] for q in pts})
        ys = sorted({q[1] for q in pts})
        with ram.lager("matt"):
            if lod:
                k = min(lod, key=lambda k: min(abs(k - x) for x in xs))
                kedja = sorted([k, *xs], key=lambda x: abs(x - k))[::-1]
            else:
                kedja = xs
            if len(kedja) > 1:
                fr = [min(q[1] for q in pts if q[0] == x) if x in xs else y0 for x in sorted(kedja)]
                ram.mattx(sorted(kedja), y0 - 6.0 * s, fr, sz=5.0)
            if vag:
                k = min(vag, key=lambda k: min(abs(k - y) for y in ys))
                kedja = sorted([k, *ys])
            else:
                kedja = ys
            if len(kedja) > 1:
                fr = [min(q[0] for q in pts if q[1] == y) if y in ys else x0 for y in kedja]
                ram.matty(kedja, x0 - 6.0 * s, fr, sz=5.0)
        _placera(ram, [("/".join(nummer.get(q, ["?"])), float(q[0]), float(q[1])) for q in pts],
                 [(float(x), float(y)) for x, y in pts], [], sz=5.0, r=0.9)
        return [v, ram]
    return rita


def _vatten_element(vt: dict, z: Z, o: Omrade) -> list[Element]:
    """Tappvattnets rör i plattan inom området i skala: de vågräta som band, stigarna (fyllda upp, vita ned) och
    hylsorna."""
    ut: list[Element] = []
    omr = box(o[0], o[2], o[1], o[3])
    for r in vt["ror"].values():
        ytter = float(re.findall(r"\d+(?:\.\d+)?", r["matt"])[-1])
        f = r["media"].lower()
        for led in _vagratt(r["vag"], z):
            if LineString(led).intersects(omr):
                ut.append({"linje": led, "r": ytter / 2, "fyll": f})
        for a, b in zip(r["vag"], r["vag"][1:]):
            g = _genom(a, b, z)
            if g and _i(o, a[0], a[1]):
                ut.append({"punkt": (a[0], a[1]), "r": ytter / 2, "fyll": f if g == "upp" else "vit", "stil": "tunn"})
    for h in vt.get("hylsor", []):
        if _i(o, *h["punkt"]):
            ut.append({"punkt": tuple(h["punkt"]), "r": h["d"] / 2, "fyll": None, "stil": "normal"})
    for namn, stanger in _fordelarna(vt).items():
        for media, a, b in stanger:
            if LineString([a, b]).intersects(omr):
                ut.append({"linje": [tuple(a), tuple(b)], "r": 25.0, "fyll": None, "stil": "dold", "under": True,
                           "etikett": f"{namn}-{media}"})
    return ut


def _hal_element(hal: list[dict], o: Omrade) -> list[Element]:
    """Hålen inom området i skala."""
    ut: list[Element] = []
    for h in hal:
        x, y = h["punkt"][:2]
        if _i(o, x, y):
            b, _ = _matt(h["matt"])
            ut.append({"punkt": (x, y), "r": b / 2, "fyll": "vit", "stil": "normal"})
    return ut


def _detalj_centralen(el: dict, jarn: list[dict], central: dict) -> Detalj:
    """Detalj 1:10 ovanför gruppcentralen: rörens stigare i de två raderna (den bakre i V3:s cellplast) mellan
    underkantsnätets järn och V3:s vinkeljärn, kanalen FF3-K2 och måtten från centralens västra kant (den främre
    raden under ramen, den bakre över)."""
    x0, x1, y0, y1 = DETALJ
    s = SKALA_DETALJ

    def rita(_: Nummer) -> list[Vy]:
        v, ram = _ram(DETALJ, (226.0, 180.0), "Detalj: rören ur gruppcentralen",
                      ["gruppernas nummer", "måtten från centralens västra kant"], topp=6.0)
        (cx, cy, _z), (b, d) = central["topp"], central["matt"]
        with v.lager("detalj"):
            v.rekt(cx - b / 2, cy - d / 2, cx + b / 2, cy + d / 2, "#efefec", "normal")
            v.linje([(x0, central["vagg"]), (x1, central["vagg"])], "normal")
            _jarnen(v, jarn)
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
                        v.ptext(a[0], a[1], 0.0, -1.3, nr.split("-")[0][1:], a="ct", sz=4.2, b=True, bg=True)
                        rader.setdefault(round(a[1]), []).append(a[0])
                        break
        with ram.lager("matt"):
            for i, (y, xs) in enumerate(sorted(rader.items())):
                xx = [cx - b / 2, *sorted(xs)]
                ram.mattx(xx, y0 - 5.0 * s if i == 0 else y1 + 4.0 * s, [y] * len(xx), sz=5.0)
        return [v, ram]
    return rita


def _detalj_skapet(el: dict, jarn: list[dict], skap: dict) -> Detalj:
    """Detalj 1:10 ovanför drivdonsskåpet på KL8: rörens stigare i en rad mitt på skåpets ovansida, mellan
    underkantsnätets järn, med rörens namn och måtten från skåpets västra kant (under ramen)."""
    x0, x1, y0, y1 = DETALJ_LC
    s = SKALA_DETALJ

    def rita(_: Nummer) -> list[Vy]:
        v, ram = _ram(DETALJ_LC, (226.0, 246.0), "Detalj: rören ur drivdonsskåpet",
                      ["rörens namn: 24 V till ljuslinjerna och dimrarnas faser", "måtten från skåpets västra kant"])
        (cx, cy, _z), (b, d), yv = skap["topp"], skap["matt"], skap["vagg"]
        with v.lager("detalj"):
            v.rekt(cx - b / 2, yv, cx + b / 2, yv + d, "#efefec", "normal")
            v.linje([(x0, yv), (x1, yv)], "normal")
            _jarnen(v, jarn)
        xs: list[float] = []
        with v.lager("stigare"):
            for nr, r in el["ror"].items():
                if "TK-LC" not in (r["fran"], r["till"]):
                    continue
                for a, b_ in zip(r["vag"], r["vag"][1:]):
                    if (_i(DETALJ_LC, a[0], a[1]) and math.hypot(a[0] - b_[0], a[1] - b_[1]) < 1.0
                            and min(a[2], b_[2]) < MB[0] < max(a[2], b_[2])):
                        v.cirkel(a[0], a[1], r["diameter"] / 2, fyll="#c8661c", stil="tunn", modell=True)
                        v.ptext(a[0], a[1], 0.0, 1.3, nr, a="lm", sz=4.2, rot=90, b=True, bg=True)
                        xs.append(a[0])
                        break
        with ram.lager("matt"):
            xx = [cx - b / 2, *sorted(xs)]
            ram.mattx(xx, y0 - 5.0 * s, [cy] * len(xx), sz=5.0)
        return [v, ram]
    return rita


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
          vaggarna: str, referenser: tuple[str, tuple[list[Kant], list[Kant]], object],
          rita: Callable[[Vy], list[Punkt]], tecken: list[tuple[str, str]], anvisning: str,
          norr: tuple[float, float], detaljer: Sequence[tuple[Omrade, Detalj]] = (),
          tabellen: tuple[float, float, float] | None = None) -> tuple[Blad, list[Punkt]]:
    """Ett blad: plattans snitt, väggarna på plattan (streckade) och under den (tunna), temats rör och punkter med
    lägesmått och nummer, detaljerna över täta områden, tabellen och anvisningarna. ovan, under: väggarnas ytor
    (shapely) eller None; referenser: (vad måtten utgår från, kanterna, plattans betong); tabellen: en lång tabell i
    två spalter på ritytan (vänsterkant och överkant på papperet och spaltens bredd, mm) i stället för i kolumnen."""
    v = vy(SKALA, OMRADE, 24.0, 20.0)
    plan(v, snitt_)
    with v.lager("vaggar"):
        if under is not None:
            rita_ytor(v, under, None, "hjalp", MINSTA_HAL)
        if ovan is not None:
            rita_ytor(v, ovan, None, "dold", MINSTA_HAL)
    punkter = rita(v)
    samla = [o for o, _ in detaljer]
    rader, nummer_ = _numrera(v, punkter, prefix, samla, _lagesmatt(v, punkter, referenser[1], referenser[2], samla))
    extra = [w for _, d in detaljer for w in d(nummer_)]
    origo(v)
    norrpil(v, *NORR, norr)
    v.rubrik(*papper(v, 24.0, 14.0), f"{platta}: {tema}", round(SKALA))
    kol: list[dict] = [
        dict(typ="rubrik", text="Anvisningar"),
        dict(typ="lista", sz=7.0, rader=[
            anvisning,
            f"Måtten går från närmaste fasta referens ({referenser[0]}) till rörets, hålets eller plåtens mitt; "
            "punkter i rad mot samma referens i en kedja. Tabellen ger lägena x, y i mm från mellanbjälklagets kanter "
            "x = 0 och y = 0 (K-05:s origo, som på R-04, R-05 och R-06), för kontroll.",
            f"{vaggarna} Plattans konstruktion och armering: R-03–R-06.",
            "Ritas ur modellen med ./mod gjutning ritning; lägena är installationernas egna (E-01, VS-01, VS-02, VG-01).",
        ]),
        dict(typ="rubrik", text="Teckenförklaring"),
        dict(typ="symboler", rader=[dict(form="linje", stil=st, text=t) for st, t in tecken]),
    ]

    def tabell(rad: list[list[str]], sz: float, matt: float = 0.6) -> dict:
        return dict(typ="tabell", kolumner=["Nr", "Vad", "x", "y", "Mått"], bredd=(0.35, 2.4, 0.45, 0.45, matt),
                    just=["l", "l", "r", "r", "l"], sz=sz, rader=rad)
    block: list[dict] = []
    if tabellen is not None and len(rader) > 40:
        x0, y0, w = tabellen
        n = -(-len(rader) // 2)
        block = [dict(x=x0 + i * (w + 3.0), y=y0, w=w, innehall=[
            dict(typ="rubrik", text="Punkterna" + (" forts." if i else "")), tabell(rader[i * n:(i + 1) * n], 4.6, 0.8)])
            for i in range(2)]
    else:
        kol += [dict(typ="rubrik", text="Punkterna"), tabell(rader, 5.2 if len(rader) <= 40 else 4.4)]
    return blad(nummer, [f"Gjutning av {platta.lower()}", tema], f"1:{SKALA:g}", "Modellen", kol,
                [v, *extra], block), punkter


def ritningar(el: dict, vatten: dict, avlopp: dict, golvvarme: dict, hal: dict[str, list[dict]],
              trapphal: list[list[float]], plattor: dict[str, list[dict]], snitt_: dict[str, list[dict]],
              norr: tuple[float, float], arbete: Path, ut: Path, jarn: list[dict], central: dict, skap: dict
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
    betong_mb = unary_union(polygoner(mb, bara=("Hus/Mellanbjälklag/MB-B",)))
    betong_bp = unary_union(polygoner(bp, bara=("Hus/Grund/Bottenplatta/BP-B",)))
    kant_mb = _kanter(betong_mb, grund)
    m_vagg = (vaggar_1, grund, "Plan 1:s väggar är streckade och källarens tunna.",
              ("plattans kant, trapphålets kant eller källarväggens liv, cellplastens yta", kant_mb, betong_mb))
    b_vagg = (vaggar_0, None, "Källarens väggar på plattan är streckade.",
              ("plattans kant", _kanter(betong_bp), betong_bp))

    def jarn_i(o: Omrade) -> list[dict]:
        omr = box(o[0], o[2], o[1], o[3])
        return [j for j in jarn if (Point(*j["linje"][0]) if len(j["linje"]) == 1 else LineString(j["linje"]))
                .intersects(omr)]

    def detalj(titel: str, o: Omrade, plats: tuple[float, float], element: list[Element]) -> tuple[Omrade, Detalj]:
        return o, _detalj(titel, o, plats, grund, jarn_i(o), element, kant_mb)
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
            "tappvattnets nivå utan att korsa det. ● röret går upp i väggen ovanför, ○ ned i källaren, ◉ rörände i "
            "undersidan (24 V till en ljuslinje i källaren: rörändan pluggas och tätas vid gjutningen och täcks sedan "
            "av armaturen). Rören går upp mellan armeringsjärnen; ur gruppcentralen i två rader och ur "
            "drivdonsskåpet på KL8 i en rad enligt detaljerna (måtten från centralens och skåpets västra kant).", norr,
            [(DETALJ, _detalj_centralen(el, jarn_i(DETALJ), central)),
             (DETALJ_LC, _detalj_skapet(el, jarn_i(DETALJ_LC), skap))], TABELL_EL),
        gor(nr[1], m, "tappvatten", "V", mb, *m_vagg, lambda v: _vatten(v, vatten, MB),
            [("vv", "varmvatten, rör-i-rör ingjutet (z −94)"), ("kv", "kallvatten, rör-i-rör ingjutet"),
             ("dold", "fördelarna under plattan (" + ", ".join(_fordelarna(vatten)) + ")")],
            "Rör-i-rör läggs i stråken närmast underkantsnätet, c/c 50, och går upp och ned mellan armeringsjärnen. "
            "Hylsorna (PP-avloppsrör) gjuts in mellan järnen; kopparrören dras senare. Där det är tätt: se "
            "detaljerna.", norr,
            [detalj("Detalj: stigarna ur källaren vid V19", DETALJ_VATTEN, (238.0, 44.0),
                    _vatten_element(vatten, MB, DETALJ_VATTEN)),
             detalj("Detalj: köket vid V14", DETALJ_KOK, (290.0, 44.0), _vatten_element(vatten, MB, DETALJ_KOK))]),
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
            "och trapphålet. Järnen läggs om runt hålen enligt R-06.", norr,
            [detalj("Detalj: köket vid V14", DETALJ_KOK, (240.0, 44.0), _hal_element(hal["MB"], DETALJ_KOK))]),
        gor(nr[5], m, "ingjutningsgods", "Ö", mb, *m_vagg, lambda v: _ovrigt(v, plattor["MB"]),
            [("normal", "stålplåt ingjuten i plattans underkant")],
            "Källarpelarnas topplåtar gjuts in i plattans underkant, mitt över pelarna (K-05, R-05).", norr),
    ]
    pdf.append(ut / f"{SERIE}.pdf")
    kompilera(bladen, arbete / "AR-03", pdf[-1])
    fel, anm = kontroll(betong_mb, hal["MB"], plattor["MB"],
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
    f, a = kontroll(betong_bp, hal["BP"], plattor["BP"],
                    {k: v for k, v in punkter.items() if k.startswith("AR-04")})
    return pdf, fel + f, anm + a
