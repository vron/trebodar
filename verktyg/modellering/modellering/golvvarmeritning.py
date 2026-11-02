"""Golvvärmeritningar ur modellens golvvärme (utdraget ur trebodar.hus.installationer.golvvarme), i ritningsmallen
(A3): kretsarna ingjutna i mellanbjälklaget (plan 1) och i bottenplattan (källaren) med zonerna, tilloppen från
fördelarna och järnen i rörens nivå, och fördelarna på V5 i en vy mot norr. Planerna och vyn ur modellens snitt
(STEP-filen).
"""
from __future__ import annotations

import math
from pathlib import Path

from shapely.geometry import Polygon
from shapely.ops import unary_union

from .planritning import (MINSTA_HAL, VAGGAR, Blad, Vy, blad, figur, kompilera, norrpil, papper, plan, polygoner,
                          rita_ytor, sektion, sv, svm, vy)

SERIE = "VG-01 Golvvärme"
SKALA, SKALA_VY = 100.0, 20.0
PLAN1 = (-200.0, 14100.0, -200.0, 16100.0)          # planernas område (x0, x1, y0, y1) [mm]
KALLARE = (-200.0, 14000.0, -200.0, 12700.0)
VY_X = (6150.0, 7900.0)                             # vyn mot V5 (norrut) från planet y = Y_VY
Y_VY = 7050.0
VY_Z = (-2450.0, 100.0)
R_STIG = 0.45                                       # lodrätt rör [pappersmm]


def _lodratt(a: list[float], b: list[float]) -> bool:
    return math.hypot(b[0] - a[0], b[1] - a[1]) < 1.0 and abs(b[2] - a[2]) > 1.0


def _i_nivan(a: list[float], b: list[float], z: float) -> bool:
    return abs(a[2] - z) < 1.0 and abs(b[2] - z) < 1.0


def _teckenforklaring(rader: list[tuple[object, str]]) -> dict:
    ut = []
    for s, t in rader:
        if isinstance(s, dict):
            ut.append({**s, "text": t})
        elif callable(s):
            ut.append({**figur(s), "text": t})
        else:
            ut.append(dict(form="linje", stil=s, text=t))
    return dict(typ="symboler", rader=ut)


def _jarn(v: Vy) -> None:
    v.cirkel(0.0, 0.0, 0.25, fyll="svart", stil=None)


TECKEN = [
    ("gv", "golvvärmens rör, ingjutna (slingor och tillopp)"),
    (dict(form="yta", fyll="#fbe9dc", stil="fin"), "slingans yta (zonen)"),
    (_jarn, "järn genom rörens nivå (källarväggarnas lodräta järn, balkarnas järn)"),
]


def _anvisningar(utdrag: dict, *ovriga: str) -> list[dict]:
    r, niv = utdrag["ror"], utdrag["nivaer"]
    return [
        dict(typ="rubrik", text="Anvisningar"),
        dict(typ="lista", sz=7.0, rader=[
            "Golvvärmen ur modellen (modeller/trebodar/hus/installationer/golvvarme), ritad med ./mod golvvarme "
            "ritning. En slinga per zon, dubbelslinga i meander (fram och retur bredvid varandra) från fördelarna "
            "på V5 i källaren.",
            f"Rören gjuts in: i mellanbjälklaget ovanför tappvattnets rör (z {svm(niv['golvvärmen i mellanbjälklaget'])}"
            f"), i bottenplattan mellan näten (z {svm(niv['golvvärmen i bottenplattan'])}). De fästs vid nätet före "
            "gjutningen och tryckprovas före och under gjutningen.",
            f"Rör: {r['slingor']}, slingan med tilloppen högst {r['max_langd']:g} m. Matarledningar från "
            f"värmepumpen: {r['matare']}. Produkterna är ännu inte valda.",
            "Tilloppen ligger i stråk, c/c 50 som nätens maskor, och går upp eller ned i betongen mellan nätets järn "
            "vid fördelaren. Slingorna håller 150 mm från väggarna och från järnen som går genom rörens nivå; "
            "stråken går över källarväggarnas järn i dörröppningarna eller mellan två järn.",
            *ovriga,
        ]),
    ]


def _kretsar(v: Vy, kretsar: dict, plan_: int, z: float) -> None:
    """Zonernas ytor, rören i nivån z och kretsarnas beteckning (id och längd)."""
    with v.lager("zoner"):
        for k in kretsar.values():
            if k["plan"] == plan_:
                v.polygon([tuple(p) for p in k["yta"]], "#fbe9dc", "fin")
    with v.lager("ror"):
        for k in kretsar.values():
            if k["plan"] != plan_:
                continue
            for a, b in zip(k["vag"], k["vag"][1:]):
                if _i_nivan(a, b, z):
                    v.linje([(a[0], a[1]), (b[0], b[1])], "gv")
    with v.lager("kretsar"):
        for kid, k in kretsar.items():
            if k["plan"] != plan_:
                continue
            c = Polygon(k["yta"]).representative_point()
            v.ptext(c.x, c.y, 0.0, 0.0, f"{kid}\n{sv(k['langd'], 0)} m", a="cm", sz=6.2, b=True, bg=True)


def _jarnen(v: Vy, jarn: list[list[list[float]]]) -> None:
    with v.lager("jarn"):
        for g in jarn:
            if len(g) == 1:
                v.cirkel(g[0][0], g[0][1], 0.25, fyll="svart", stil=None)
            else:
                v.linje([tuple(p) for p in g], "tunn")


def _fordelaren(v: Vy, utdrag: dict, plan_: int) -> None:
    """Fördelarens läge (stammarna i plan) med beteckningen."""
    with v.lager("fordelare"):
        f = [x for x in utdrag["fordelare"].values() if x["plan"] == plan_]
        x0, x1 = min(x["start"][0] for x in f), max(x["slut"][0] for x in f)
        y0, y1 = min(x["start"][1] for x in f) - 16.0, max(x["start"][1] for x in f) + 16.0
        v.rekt(x0, y0, x1, y1, "#c9c2a8", "tunn")
        v.hanvisning(((x0 + x1) / 2, y0), ((x0 + x1) / 2 + v.m(8.0), y0 - v.m(10.0)),
                     f"FD{plan_} på V5 i källaren", a="lm", sz=5.6)


def _tabell(utdrag: dict, plan_: int) -> list[dict]:
    rader = [[kid, k["namn"], sv(k["area"], 1), f"{k['cc']:g}", sv(k["langd"], 0), sv(k["volym"], 1),
              f"{k['utgang']['fram']}/{k['utgang']['retur']}"]
             for kid, k in utdrag["kretsar"].items() if k["plan"] == plan_]
    summa = [k for k in utdrag["kretsar"].values() if k["plan"] == plan_]
    return [
        dict(typ="rubrik", text="Kretsar"),
        dict(typ="tabell", kolumner=["Krets", "Rum", "m²", "c/c", "m", "l", "Utg."],
             bredd=(0.55, 1.45, 0.3, 0.3, 0.3, 0.3, 0.4), just=["l", "l", "r", "r", "r", "r", "r"], sz=5.8,
             rader=rader),
        dict(typ="text", sz=5.8, rader=[
            f"m²: slingans yta. m: rörets längd från fördelaren och tillbaka, l: vattenvolymen. Utg.: utgången på "
            f"framledningens och returens fördelare. Summa {sv(sum(k['langd'] for k in summa), 0)} m, "
            f"{sv(sum(k['area'] for k in summa), 0)} m² slingor."]),
    ]


def _plan(v: Vy, hela: Vy, utdrag: dict, plan_: int, snitt_: list[dict], omr: tuple[float, ...], p0: tuple[float, float],
          rubrik: str, norr: tuple[float, float], pil: tuple[float, float]) -> None:
    """En våning: väggarna ur snittet, zonerna, rören i nivån, järnen, fördelarens läge och rubriken."""
    z = PLAN_Z[plan_](utdrag)
    plan(v, snitt_)
    _kretsar(v, utdrag["kretsar"], plan_, z)
    _jarnen(v, utdrag["jarn"][plan_])
    _fordelaren(v, utdrag, plan_)
    norrpil(v, *pil, norr)
    with hela.lager("rubrik"):
        hela.rubrik(*papper(hela, p0[0], p0[1] - 6.0), rubrik, round(v.s))
        hela.skalstock(*papper(hela, p0[0], p0[1] + (omr[3] - omr[2]) / v.s + 5.0), langd_m=5, steg_m=1)


PLAN_Z = {1: lambda u: u["nivaer"]["golvvärmen i mellanbjälklaget"],
          0: lambda u: u["nivaer"]["golvvärmen i bottenplattan"]}


def _planerna(utdrag: dict, mb: list[dict], plan1: list[dict], kallare: list[dict], norr: tuple[float, float],
              nummer: str, ovriga: str) -> Blad:
    """Plan 1 (kretsarna i mellanbjälklaget, plan 1:s väggar streckade och källarväggarna tunna) och källaren
    (kretsarna i bottenplattan) bredvid varandra, med kretsarnas tabeller under."""
    s = SKALA
    p1, p0 = (24.0, 30.0), (178.0, 30.0)
    vyer = []
    for plan_, omr, p, snitt_, rubrik, pil in (
            (1, PLAN1, p1, mb, "Plan 1, i mellanbjälklaget", (12800.0, 14800.0)),
            (0, KALLARE, p0, kallare, "Källaren, i bottenplattan", (2000.0, 11400.0))):
        v = Vy(p[0], p[1], (omr[1] - omr[0]) / s, (omr[3] - omr[2]) / s, s, omr[0], omr[3], klipp=True)
        hela = vy(s, omr, *p)
        _plan(v, hela, utdrag, plan_, snitt_, omr, p, rubrik, norr, pil)
        if plan_ == 1:
            with v.lager("vaggar"):
                rita_ytor(v, unary_union(polygoner(kallare, bara=("Hus/Grund",))), None, "hjalp", MINSTA_HAL)
                rita_ytor(v, unary_union(polygoner(plan1, bara=VAGGAR)), None, "dold", MINSTA_HAL)
        vyer += [v, hela]
    block = [dict(x=p1[0], y=p1[1] + (PLAN1[3] - PLAN1[2]) / s + 12.0, w=146.0, innehall=_tabell(utdrag, 1)),
             dict(x=p0[0], y=p0[1] + (KALLARE[3] - KALLARE[2]) / s + 12.0, w=140.0, innehall=_tabell(utdrag, 0))]
    kol = _anvisningar(utdrag, ovriga, "Plan 1: plan 1:s väggar är streckade och källarväggarna tunna; källarväggarnas "
                                       "lodräta järn når upp i bjälklaget och delar zonerna. Källaren: balkarnas "
                                       "överkantsjärn under V4–V6, V15 och V19 ligger i rörens nivå, så källarrummet "
                                       "norr om V4–V6 värms inte.") + [
        dict(typ="rubrik", text="Teckenförklaring"),
        _teckenforklaring(TECKEN + [("dold", "väggarna på plan 1"), ("hjalp", "källarväggarna (plan 1)")])]
    return blad(nummer, ["Golvvärme", "Plan 1 och källaren"], f"1:{s:g}", "Modellen", kol, vyer, block)


def _fordelarna(utdrag: dict, kallare: list[dict], vyn: list[dict], nummer: str, ovriga: str) -> Blad:
    """Fördelarna på V5: planen (rören upp i mellanbjälklaget och ned i bottenplattan, tilloppen i båda) och vyn mot
    norr med stammarna, rören och matarledningarna."""
    s = SKALA_VY
    # ---------------------------------------------------------------- planen
    omr_p = (VY_X[0], VY_X[1], 6450.0, 7750.0)
    pp = (24.0, 34.0)
    p = Vy(pp[0], pp[1], (omr_p[1] - omr_p[0]) / s, (omr_p[3] - omr_p[2]) / s, s, omr_p[0], omr_p[3], klipp=True)
    hp = vy(s, omr_p, *pp)
    plan(p, kallare)
    with p.lager("ror"):
        for k in utdrag["kretsar"].values():
            z = PLAN_Z[k["plan"]](utdrag)
            for a, b in zip(k["vag"], k["vag"][1:]):
                if _i_nivan(a, b, z):
                    p.linje([(a[0], a[1]), (b[0], b[1])], "gv" if k["plan"] == 1 else "gv0")
    with p.lager("fordelare"):
        for f in utdrag["fordelare"].values():
            a, b = f["start"], f["slut"]
            p.rekt(a[0], a[1] - 16.0, b[0], a[1] + 16.0, "#c9c2a8", "tunn")
    with p.lager("stigare"):
        for k in utdrag["kretsar"].values():
            for a, b in zip(k["vag"], k["vag"][1:]):
                if _lodratt(a, b):
                    p.cirkel(a[0], a[1], R_STIG, fyll="gv", stil=None)
    with hp.lager("rubrik"):
        hp.rubrik(*papper(hp, pp[0], pp[1] - 6.0), "Fördelarna, plan", round(s))
    # ---------------------------------------------------------------- vyn mot V5 (norrut)
    omr = (VY_X[0], VY_X[1], VY_Z[0], VY_Z[1])
    be = (24.0, pp[1] + (omr_p[3] - omr_p[2]) / s + 20.0)
    e = Vy(be[0], be[1], (omr[1] - omr[0]) / s, (omr[3] - omr[2]) / s, s, omr[0], omr[3], klipp=True)
    sektion(e, vyn)
    with e.lager("fordelare"):
        for fid, f in utdrag["fordelare"].items():
            a, b = f["start"], f["slut"]
            e.rekt(a[0], a[2] - 16.0, b[0], a[2] + 16.0, "#c9c2a8", "tunn")
            e.ptext(a[0], a[2], -0.8, 0.0, f"{fid} z {svm(a[2])}", a="rm", sz=5.0, bg=True)
    with e.lager("ror"):
        for k in utdrag["kretsar"].values():
            for a, b in zip(k["vag"], k["vag"][1:]):
                if _lodratt(a, b) and VY_X[0] < a[0] < VY_X[1]:
                    e.linje([(a[0], a[2]), (b[0], b[2])], "gv")
        for vag in utdrag["matare"].values():
            for a, b in zip(vag, vag[1:]):
                if math.hypot(b[0] - a[0], b[2] - a[2]) > 1.0:
                    e.linje([(max(min(a[0], omr[1]), omr[0]), a[2]), (max(min(b[0], omr[1]), omr[0]), b[2])], "gv")
    with e.lager("nivaer"):
        for txt, zz in utdrag["nivaer"].items():
            if VY_Z[0] < zz < VY_Z[1]:
                e.linje([(omr[1] - e.m(14.0), zz), (omr[1], zz)], "tunn")
                e.ptext(omr[1], zz, -0.5, 0.4, f"{'±0' if abs(zz) < 0.5 else svm(zz)} {txt}", a="rb", sz=4.8)
    ev = vy(s, omr, *be)
    with ev.lager("rubrik"):
        ev.rubrik(*papper(ev, be[0], be[1] - 6.0), f"Fördelarna, vy mot V5 (norrut) från y = {svm(Y_VY)}", round(s))
        ev.skalstock(*papper(ev, be[0], be[1] + (omr[3] - omr[2]) / s + 5.0), langd_m=1, steg_m=0.5)
    fd = [[fid, f["media"], str(f["utgangar"]), svm(round(f["start"][0])), svm(round(f["start"][1])),
           svm(f["start"][2])] for fid, f in utdrag["fordelare"].items()]
    matare = [[k, sv(sum(math.dist(a, b) for a, b in zip(v, v[1:])) / 1000, 1)] for k, v in utdrag["matare"].items()]
    gf: dict[tuple[str, str], int] = {}
    for x in utdrag["genomforingar"]:
        gf[(x["del"], x["atgard"])] = gf.get((x["del"], x["atgard"]), 0) + 1
    block = [dict(x=24.0 + (omr[1] - omr[0]) / s + 14.0, y=34.0, w=190.0, innehall=[
        dict(typ="rubrik", text="Fördelare"),
        dict(typ="tabell", kolumner=["Id", "Stam", "Kretsar", "x", "y", "z"], bredd=(0.5, 0.5, 0.45, 0.4, 0.4, 0.4),
             just=["l", "l", "r", "r", "r", "r"], sz=5.8, rader=fd),
        dict(typ="text", sz=5.8, rader=[
            "FD1: plan 1, FD0: källaren. x: stammens västra ände, utgångarna c/c 50 österut. Rören går "
            "upp i mellanbjälklaget och ned i bottenplattan rakt ovanför och under utgångarna, mellan nätens järn."]),
        dict(typ="rubrik", text="Matarledningar"),
        dict(typ="tabell", kolumner=["Rör", "m"], bredd=(0.6, 0.3), just=["l", "r"], sz=5.8, rader=matare),
        dict(typ="text", sz=5.8, rader=[
            "VS1: från värmepumpen TK-VP i teknikrummet till FD1:s västra ände, under källarens tak. VS0: från FD1:s "
            "östra ände till FD0:s. Fram och retur i olika höjder."]),
        dict(typ="rubrik", text="Genomföringar"),
        dict(typ="tabell", kolumner=["Byggdel", "Åtgärd", "Rör"], bredd=(0.7, 2.2, 0.3), just=["l", "l", "r"],
             sz=5.8, rader=[[d, a, str(n)] for (d, a), n in gf.items()]),
    ])]
    kol = _anvisningar(utdrag, ovriga) + [
        dict(typ="rubrik", text="Teckenförklaring"), _teckenforklaring([
            ("gv", "golvvärmens rör: plan 1:s tillopp i mellanbjälklaget, matarledningarna"),
            ("gv0", "källarens tillopp i bottenplattan"),
            (lambda w: w.cirkel(0.0, 0.0, R_STIG, fyll="gv", stil=None), "rör upp eller ned i betongen"),
            (dict(form="yta", fyll="#c9c2a8", stil="tunn"), "fördelarens stam")])]
    return blad(nummer, ["Golvvärme", "Fördelarna"], f"1:{s:g}", "Modellen", kol, [p, hp, e, ev], block)


def ritningar(utdrag: dict, plan1: list[dict], kallare: list[dict], mb: list[dict], vyn: list[dict],
              norr: tuple[float, float], arbete: Path, ut: Path) -> Path:
    """Golvvärmeritningarna (serien SERIE): plan 1 och källaren (snitten: plan 1, källaren och mellanbjälklaget) och
    fördelarna (snitten: källaren och y = Y_VY), som pdf i mappen ut (bladen för sig i arbetsmappen)."""
    pre = SERIE.split()[0]
    nr = [f"{pre}.{i}" for i in range(1, 3)]
    bladen = [
        (nr[0], _planerna(utdrag, mb, plan1, kallare, norr, nr[0], f"Fördelarna: {nr[1]}.")),
        (nr[1], _fordelarna(utdrag, kallare, vyn, nr[1], f"Plan 1 och källaren: {nr[0]}.")),
    ]
    pdf = ut / f"{SERIE}.pdf"
    kompilera(bladen, arbete, pdf)
    return pdf


def lista(utdrag: dict, kontroll: tuple[list[str], list[str]], krockar: list[str]) -> str:
    """Kretsarna, fördelarna, genomföringarna, kontrollen och krockarna mot huset som markdown."""
    fel, anm = kontroll
    kr = utdrag["kretsar"]
    rad = ["# Golvvärmen", "", f"{len(kr)} kretsar, {len(utdrag['fordelare'])} fördelarstammar.", "",
           f"## Kontroll: {len(fel)} fel, {len(anm)} anmärkningar", ""]
    rad += [f"- FEL {f}" for f in fel] + [f"- {a}" for a in anm]
    rad += ["", "## Krockar mot husets delar", ""] + ([f"- {k}" for k in krockar] or ["Inga."])
    rad += ["", "## Kretsar", "", "| Krets | Rum | Våning | Yta [m²] | c/c | Längd [m] | Volym [l] | Utgång fram/retur |",
            "|---|---|---|---|---|---|---|---|"]
    for k_id, k in kr.items():
        rad.append(f"| {k_id} | {k['namn']} | {'plan 1' if k['plan'] == 1 else 'källaren'} | {k['area']:.1f} | "
                   f"{k['cc']:g} | {k['langd']:.1f} | {k['volym']:.1f} | {k['utgang']['fram']}/{k['utgang']['retur']} |")
    rad += ["", "## Fördelare", "", "| Id | Stam | Kretsar | Läge (x, y, z) |", "|---|---|---|---|"]
    for f_id, f in utdrag["fordelare"].items():
        rad.append(f"| {f_id} | {f['media']} | {f['utgangar']} | {', '.join(f'{c:.0f}' for c in f['start'])} |")
    rad += ["", "## Genomföringar", "", "| Byggdel | Åtgärd | Mått | Rör | x | y | z |",
            "|---|---|---|---|---|---|---|"]
    for x in utdrag["genomforingar"]:
        q = x["punkt"]
        rad.append(f"| {x['del']} | {x['atgard']} | {x['matt']} | {x['element']} | {q[0]:.0f} | {q[1]:.0f} | "
                   f"{q[2]:.0f} |")
    return "\n".join(rad) + "\n"
