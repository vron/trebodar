"""Brandlarmets ritningar ur modellens brandlarm (utdraget ur trebodar.hus.installationer.brandlarm.larm), i
ritningsmallen (A3): planerna för plan 1 och källaren med brandvarnarna, dosorna, kablarnas vägar och
stigarna genom mellanbjälklaget, och listan (markdown). Planerna ur modellens snitt (STEP-filen).
"""
from __future__ import annotations

import math
from collections.abc import Callable
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from .planritning import Blad, Vy, blad, figur, kompilera, norrpil, papper, plan, plan_ytor, sv, vy

SERIE = "E-02 Brandlarm"
SKALA = 75.0
PLAN1 = (-500.0, 14300.0, -300.0, 16300.0)          # planernas område (x0, x1, y0, y1) [mm]
R_VARNARE, R_STIGARE, DOSA = 2.3, 1.1, 1.3            # symbolernas mått på papperet [mm]

Pkt = tuple[float, float]


# ------------------------------------------------------------------ symboler (pappersmått)

def varnare(v: Vy, X: float, Y: float, r: float = R_VARNARE) -> None:
    """Brandvarnare: cirkel med en mindre fylld cirkel (rökdetektorn)."""
    v.cirkel(X, Y, r, fyll="vit", stil="normal")
    v.cirkel(X, Y, r * 0.42, fyll="svart", stil=None)


def dosa(v: Vy, X: float, Y: float) -> None:
    """Kopplingsdosa: liten kvadrat."""
    h = v.m(DOSA / 2)
    v.polygon([(X - h, Y - h), (X + h, Y - h), (X + h, Y + h), (X - h, Y + h)], "vit", "normal")


def stigare(v: Vy, X: float, Y: float) -> None:
    """Kabeln lodrätt genom mellanbjälklaget: cirkel med kryss."""
    v.cirkel(X, Y, R_STIGARE, fyll="vit", stil="ok_tunn")
    k = v.m(R_STIGARE) * math.sqrt(0.5)
    v.linje([(X - k, Y - k), (X + k, Y + k)], "ok_tunn")
    v.linje([(X - k, Y + k), (X + k, Y - k)], "ok_tunn")


TECKEN: list[tuple[Callable[[Vy], None] | dict, str]] = [
    (lambda w: varnare(w, 0.0, 0.0, 1.25), "brandvarnare 230 V med reservbatteri, i taket"),
    (lambda w: dosa(w, 0.0, 0.0), "kopplingsdosa (D01 matningen)"),
    (dict(form="linje", stil="ok"), "brandlarmets kabel (sammankopplingen)"),
    (lambda w: stigare(w, 0.0, 0.0), "kabeln genom mellanbjälklaget, i hylsa (stigare)"),
]


def _teckenforklaring() -> dict:
    return dict(typ="symboler", rader=[{**s, "text": t} if isinstance(s, dict) else {**figur(s), "text": t}
                                       for s, t in TECKEN])


def _langs(v: Vy, a: Pkt, b: Pkt, txt: str, hinder: BaseGeometry, sz: float = 5.2, avstand: float = 0.8) -> None:
    """Text längs sträckan a–b, på dess vänstra sida: mitt på sträckan eller, om texten där går över en vägg
    (hinder), där den går fri."""
    t = np.subtract(b, a) / math.dist(a, b)
    ang = math.degrees(math.atan2(t[1], t[0]))
    if ang > 90.5 or ang < -89.5:
        ang += 180.0
    n = np.array([-math.sin(math.radians(ang)), math.cos(math.radians(ang))])
    halv = v.m(len(txt) * sz * 0.353 * 0.55) / 2 + v.m(0.5)               # textens halva längd med marginal
    hoj = v.m(sz * 0.353 + 0.3)                                             # textens höjd med marginal
    for f in (0.5, 0.35, 0.65, 0.25, 0.75, 0.15, 0.85):
        q = np.add(a, np.multiply(f, np.subtract(b, a))) + n * v.m(avstand)
        ruta = Polygon([q - t * halv, q + t * halv, q + t * halv + n * hoj, q - t * halv + n * hoj])
        if halv <= f * math.dist(a, b) <= math.dist(a, b) - halv and not ruta.intersects(hinder):
            break
    else:
        q = np.add(a, np.multiply(0.5, np.subtract(b, a))) + n * v.m(avstand)
    v.text(q[0], q[1], txt, a="cb", sz=sz, rot=round(ang, 2), col="ok")


# ------------------------------------------------------------------ planerna

def _plan(utdrag: dict, delar: list[dict], plan_nr: int, nummer: str, rubrik: str, norr: tuple[float, float] | None,
          ovriga: str) -> Blad:
    """Brandlarmet på en våning: kablarna (vågrätt på våningen), stigarna genom bjälklaget, dosorna och varnarna."""
    v = vy(SKALA, PLAN1, 24.0, 27.0)
    plan(v, delar)
    hinder = unary_union([u for u, _, _ in plan_ytor(delar)])
    z_bj = utdrag["nivaer"]["plan 1"]
    pa = (lambda z: z > z_bj - 1.0) if plan_nr == 1 else (lambda z: z < z_bj - 1.0)
    stigar: dict[tuple[int, int], str] = {}
    with v.lager("kablar"):
        for rid, r in utdrag["kablar"].items():
            vag = r["vag"]
            langsta: tuple[float, Pkt, Pkt] | None = None
            for a, b in zip(vag, vag[1:]):
                if math.hypot(b[0] - a[0], b[1] - a[1]) < 1.0:
                    if min(a[2], b[2]) < z_bj - 1.0 < max(a[2], b[2]):           # genom bjälklaget
                        stigar[(round(a[0]), round(a[1]))] = ("från källaren" if plan_nr == 1
                                                              else "upp till plan 1") + f" ({rid})"
                    continue
                if not (pa(a[2]) and pa(b[2])):
                    continue
                v.linje([(a[0], a[1]), (b[0], b[1])], "ok")
                lgd = math.hypot(b[0] - a[0], b[1] - a[1])
                if langsta is None or lgd > langsta[0]:
                    langsta = (lgd, (a[0], a[1]), (b[0], b[1]))
            if langsta and langsta[0] / v.s > 14.0:
                _langs(v, langsta[1], langsta[2], f"{rid} {sv(r['langd'] / 1000, 1)} m", hinder)
    with v.lager("stigare"):
        for (x, y), txt in stigar.items():
            stigare(v, x, y)
            v.ptext(x, y, 1.8, -1.6, txt, a="lt", sz=5.0, bg=True)
    with v.lager("dosor"):
        for did, d in utdrag["dosor"].items():
            p = d["punkt"]
            if (p[2] > z_bj - 1.0) == (plan_nr == 1):
                dosa(v, p[0], p[1])
                v.ptext(p[0], p[1], -1.6, 1.4, did + (" matning" if did == "D01" else ""), a="rb", sz=5.4, bg=True)
    with v.lager("varnare"):
        for vid, w in utdrag["varnare"].items():
            if w["plan"] != plan_nr:
                continue
            p = w["punkt"]
            varnare(v, p[0], p[1])
            txt = f"{vid} {w['rum'].lower()}\n{sv(w['over_golv'] / 1000, 2)} m ö.g."
            v.ptext(p[0], p[1], R_VARNARE + 0.8, 0.6, txt, a="lb", sz=5.6, bg=True)
    if norr:
        norrpil(v, 7300.0, 14600.0, norr)
    v.rubrik(*papper(v, 24.0, 21.0), rubrik, round(v.s))
    with v.lager("skalstock"):
        v.skalstock(*papper(v, 24.0, 27.0 + (PLAN1[3] - PLAN1[2]) / v.s + 8.0), langd_m=5, steg_m=1)
    varn = [[k, w["rum"], "plan 1" if w["plan"] == 1 else "källaren", sv(w["over_golv"] / 1000, 2)]
            for k, w in utdrag["varnare"].items()]
    kablar = [[k, r["fran"], r["till"], sv(r["langd"] / 1000, 1)] for k, r in utdrag["kablar"].items()]
    kol: list[dict] = [
        dict(typ="rubrik", text="Anvisningar"),
        dict(typ="lista", sz=7.0, rader=[
            "Brandvarnare för 230 V med reservbatteri, trådbundet sammankopplade: när en larmar larmar alla. Inte "
            "radio, eftersom radio genom betongbjälklaget mellan källaren och plan 1 vore osäkert.",
            f"En varnare i varje huvudutrymme, högt i taket nära rummets mitt; i snedtaken omkring "
            f"{sv(utdrag['avstand_nock'] / 1000, 1)} m från nocken i planet, mellan installationsskiktets läkt, "
            "eftersom röken tar lång tid till andra rum under de höga taken.",
            f"Kabeln: {utdrag['kabel']}. Matningen från elcentralen (läget inte bestämt) till matningsdosan D01; "
            "stammen går under källarens tak, med en stigare per huskropp genom mellanbjälklaget (mellan "
            "armeringens järn) och i en innerväggs regelfack upp till innertakets installationsskikt.",
            "Produkterna är inte valda (allmänna typer med vanliga mått). Ritningen ritas med ./mod brandlarm ritning.",
            ovriga,
        ]),
        dict(typ="rubrik", text="Teckenförklaring"),
        _teckenforklaring(),
        dict(typ="rubrik", text="Brandvarnare"),
        dict(typ="tabell", kolumner=["Id", "Rum", "Plan", "Höjd (m)"], bredd=(0.7, 1.9, 0.7, 0.6),
             just=["l", "l", "l", "r"], sz=6.4, rader=varn),
        dict(typ="rubrik", text="Kablar"),
        dict(typ="tabell", kolumner=["Kabel", "Från", "Till", "Längd (m)"], bredd=(0.6, 0.8, 0.8, 0.7),
             just=["l", "l", "l", "r"], sz=6.4, rader=kablar),
    ]
    return blad(nummer, ["Brandlarm", rubrik.split(",")[0]], f"1:{SKALA:g}", "Modellen", kol, [v])


def ritningar(utdrag: dict, plan1: list[dict], kallare: list[dict], norr: tuple[float, float], arbete: Path,
              ut: Path) -> Path:
    """Brandlarmets ritningar (serien SERIE): plan 1 och källaren, som pdf i mappen ut (bladen för sig i
    arbetsmappen, under repots rot)."""
    pre = SERIE.split()[0]
    nr = [f"{pre}.{i}" for i in (1, 2)]
    bladen = [
        (nr[0], _plan(utdrag, plan1, 1, nr[0], "Plan 1, brandlarm", norr, f"Källaren: {nr[1]}.")),
        (nr[1], _plan(utdrag, kallare, 0, nr[1], "Källaren, brandlarm", None, f"Plan 1: {nr[0]}.")),
    ]
    pdf = ut / f"{SERIE}.pdf"
    kompilera(bladen, arbete, pdf)
    return pdf


def lista(utdrag: dict, kontroll: tuple[list[str], list[str]], krockar: list[str]) -> str:
    """Varnarna, dosorna, kablarna, genomföringarna, kontrollen och krockarna mot huset som markdown."""
    fel, anm = kontroll
    rad = ["# Brandlarmet", "", f"{len(utdrag['varnare'])} brandvarnare, trådbundet sammankopplade; "
           f"{utdrag['kabel']}.", "", f"## Kontroll: {len(fel)} fel, {len(anm)} anmärkningar", ""]
    rad += [f"- FEL {f}" for f in fel] + [f"- {a}" for a in anm]
    rad += ["", "## Krockar mot husets delar", ""] + ([f"- {k}" for k in krockar] or ["Inga."])
    rad += ["", "## Brandvarnare", "", "| Id | Rum | Plan | Höjd över golvet [mm] | x | y |",
            "|---|---|---|---|---|---|"]
    for k, w in utdrag["varnare"].items():
        p = w["punkt"]
        rad.append(f"| {k} | {w['rum']} | {'plan 1' if w['plan'] == 1 else 'källaren'} | {w['over_golv']:.0f} | "
                   f"{p[0]:.0f} | {p[1]:.0f} |")
    rad += ["", "## Dosor", "", "| Id | Vad | x | y |", "|---|---|---|---|"]
    rad += [f"| {k} | {d['namn']} | {d['punkt'][0]:.0f} | {d['punkt'][1]:.0f} |" for k, d in utdrag["dosor"].items()]
    rad += ["", "## Kablar", "", "| Kabel | Från | Till | Längd [m] | Böjar [°] | Punkter |",
            "|---|---|---|---|---|---|"]
    for k, r in utdrag["kablar"].items():
        pkt = " → ".join("(" + ", ".join(f"{c:.0f}" for c in p) + ")" for p in r["vag"])
        rad.append(f"| {k} | {r['fran']} | {r['till']} | {r['langd'] / 1000:.2f} | {r['bojar']:.0f} | {pkt} |")
    rad += ["", "## Genomföringar", "", "| Byggdel | Åtgärd | Mått | Kabel | x | y | z |",
            "|---|---|---|---|---|---|---|"]
    for x in utdrag["genomforingar"]:
        p = x["punkt"]
        rad.append(f"| {x['del']} | {x['atgard']} | {x['matt']} | {x['element']} | {p[0]:.0f} | {p[1]:.0f} | "
                   f"{p[2]:.0f} |")
    return "\n".join(rad) + "\n"
