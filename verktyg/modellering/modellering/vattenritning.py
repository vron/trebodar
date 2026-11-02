"""Tappvattenritningar ur modellens tappvatten (utdraget ur trebodar.hus.installationer.vatten), i ritningsmallen
(A3): rören ingjutna i mellanbjälklaget med tappställena på plan 1 och i källaren (var rören kommer ut ur bjälklaget,
upp i väggarna och golvdosorna eller ned i källarväggarnas cellplast), och teknikrummet (plan och vy mot V19 med
fördelarna, matarledningarna, värmepumpen och ventilationens kanal). Planerna och vyn ur modellens snitt (STEP-filen).
"""
from __future__ import annotations

import math
from collections.abc import Callable
from pathlib import Path

import numpy as np
from shapely.geometry import LineString
from shapely.ops import unary_union

from .planritning import (MINSTA_HAL, VAGGAR, Blad, Vy, blad, figur, kompilera, norrpil, papper, plan, polygoner,
                          rita_ytor, sektion, sv, svm, vy)

SERIE = "VS-01 Tappvatten"
SKALA_BJALKLAG, SKALA_TEKNIK = 50.0, 20.0
BJALKLAG = (-300.0, 14000.0, 3300.0, 9700.0)        # bjälklagets område med rören (x0, x1, y0, y1) [mm]
TEKNIK = (3050.0, 4500.0, 7100.0, 9150.0)            # teknikrummets plan
X_VY = 3600.0                                        # vyn mot V19 (österut) från planet x = X_VY
Z_VY = (-2450.0, 50.0)                               # vyns höjd
R_TAPP = 1.8                                         # tappställets symbol [pappersmm]
R_STIG = 0.55                                        # lodrätt rör (ut ur bjälklaget, i väggen) [pappersmm]
Z_UK, Z_OK = -150.0, 0.0                             # mellanbjälklagets under- och överkant

Pkt = tuple[float, float]
Rad = tuple[Callable[[Vy], None] | str | dict, str]


# ------------------------------------------------------------------ symboler och hjälp

def tappstalle(v: Vy, X: float, Y: float, symbol: str) -> None:
    """Tappställe: cirkel med beteckningen (TS, DU, BK, WC, DB, TM, UV)."""
    v.cirkel(X, Y, R_TAPP, fyll="vit", stil="normal")
    v.text(X, Y, symbol, a="cm", sz=5.0, b=True)


def stigare(v: Vy, X: float, Y: float, media: str, ned: bool = False) -> None:
    """Lodrätt rör i mediets färg: upp ur bjälklaget (fylld cirkel) eller ned ur det (ring)."""
    v.cirkel(X, Y, R_STIG + (0.1 if ned else 0.0), fyll=media.lower(), stil=None)
    if ned:
        v.cirkel(X, Y, R_STIG * 0.5, fyll="vit", stil=None)


def _lodratt(a: list[float], b: list[float]) -> bool:
    return math.hypot(b[0] - a[0], b[1] - a[1]) < 1.0 and abs(b[2] - a[2]) > 1.0


def _vagratt(a: list[float], b: list[float]) -> bool:
    return abs(b[2] - a[2]) < 1.0 and math.hypot(b[0] - a[0], b[1] - a[1]) > 1.0


def _i_ordning(ror: dict) -> list[tuple[str, dict]]:
    """Rören, varmvattnet först."""
    return sorted(ror.items(), key=lambda kv: kv[1]["media"] != "VV")


def _teckenforklaring(rader: list[Rad]) -> dict:
    ut = []
    for s, t in rader:
        if isinstance(s, dict):
            ut.append({**s, "text": t})
        elif callable(s):
            ut.append({**figur(s), "text": t})
        else:
            ut.append(dict(form="linje", stil=s, text=t))
    return dict(typ="symboler", rader=ut)


TECKEN: list[Rad] = [
    ("vv", "varmvatten (VV), rör-i-rör ingjutet i mellanbjälklaget"),
    ("kv", "kallvatten (KV), rör-i-rör ingjutet i mellanbjälklaget"),
    (lambda w: stigare(w, 0.0, 0.0, "VV"), "upp ur bjälklaget (i väggen eller golvdosan), varmvatten"),
    (lambda w: stigare(w, 0.0, 0.0, "KV"), "upp ur bjälklaget, kallvatten"),
    (lambda w: stigare(w, 0.0, 0.0, "VV", ned=True), "ned ur bjälklaget (i källarväggen eller till fördelarskåpet)"),
    (lambda w: tappstalle(w, 0.0, 0.0, "TS"), "tappställe (TS tvättställ, DU dusch, BK badkar, WC, DB diskbänk, "
                                               "TM tvättmaskin, TH tvättho)"),
]


def _anvisningar(utdrag: dict, *ovriga: str) -> list[dict]:
    niv = utdrag["nivaer"]
    return [
        dict(typ="rubrik", text="Anvisningar"),
        dict(typ="lista", sz=7.0, rader=[
            "Tappvattnet ur modellen (modeller/trebodar/hus/installationer/vatten): rör-i-rör från fördelarskåpet i "
            "teknikrummet till varje tappställe (stjärnsystem, läckor syns i skåpet). Ritningen ritas med ./mod "
            "vatten ritning.",
            f"Rören gjuts in i mellanbjälklaget (R-06) i stråk, c/c 40 i en nivå närmast underkantsnätet "
            f"(z {svm(niv['rören i bjälklaget'])}); golvvärmen går ovanför. Rören läggs före gjutningen och kommer ut "
            f"ur bjälklaget mellan armeringsjärnen.",
            "På plan 1 går rören upp i väggarnas regelfack till väggdosorna (syllen urtas) eller genom golvet till "
            "golvdosorna; i källaren ned i källarväggens cellplast bakom gipsen (fräst spår) till väggdosorna. "
            "Väggdosorna i badrummet tätas mot tätskiktet (Säker Vatten).",
            "Varmvatten inom 10 s vid tappställets normflöde (BBR 6:62, Säker Vatten), räknat ur volymen från "
            "beredaren. Produkterna är ännu inte valda (allmänna typer med vanliga mått och normflöden).",
            *ovriga,
        ]),
    ]


def _tappstallen(v: Vy, tapp: dict, plan1: list[dict], kallare: list[dict]) -> None:
    """Tappställenas symboler med id, en bit från dosan i första riktningen där symbolen inte hamnar på en vägg på
    tappställets våning: väggdosor ut från väggen, golvdosor norr, söder, öster eller väster."""
    vaggar = {True: unary_union(polygoner(plan1, bara=VAGGAR)),
              False: unary_union(polygoner(kallare, bara=VAGGAR + ("Hus/Grund",)))}
    L = v.m(R_TAPP + 3.0)
    with v.lager("tappstallen"):
        for k, t in tapp.items():
            p, n = np.array(t["punkt"][:2]), np.array(t["normal"][:2])
            kandidater = [n] if t["slag"] != "golv" else [np.array(d) for d in ((0, 1), (0, -1), (1, 0), (-1, 0))]
            d = next((d for d in kandidater if not LineString([tuple(p + d * v.m(1.0)), tuple(p + d * L)]).buffer(
                v.m(R_TAPP)).intersects(vaggar[t["punkt"][2] > -1.0])), kandidater[0])
            c = p + d * L
            tappstalle(v, c[0], c[1], t["symbol"])
            v.linje([tuple(p), tuple(c - d * v.m(R_TAPP))], "tunn")
            a = "lm" if d[0] >= -0.5 else "rm"
            v.ptext(c[0], c[1], (R_TAPP + 0.8) * (1 if a == "lm" else -1), 0.0, k, a=a, sz=5.8, bg=True)


# ------------------------------------------------------------------ mellanbjälklaget

def _bjalklag(utdrag: dict, mb: list[dict], plan1: list[dict], kallare: list[dict], norr: tuple[float, float],
              nummer: str, ovriga: str) -> Blad:
    """Rören ingjutna i mellanbjälklaget (en fil per rör), var de kommer ut ur det (upp till plan 1, ned
    till källaren och fördelarskåpet) och tappställena, med plan 1:s väggar streckade och källarväggarna tunna."""
    s_, (x0, x1, y0, y1) = SKALA_BJALKLAG, BJALKLAG
    v = Vy(24.0, 30.0, (x1 - x0) / s_, (y1 - y0) / s_, s_, x0, y1, klipp=True)
    hela = vy(s_, BJALKLAG, 24.0, 30.0)                         # rubriken och skalstocken utanför ramen
    plan(v, mb)
    with v.lager("vaggar"):
        rita_ytor(v, unary_union(polygoner(kallare, bara=("Hus/Grund",))), None, "hjalp", MINSTA_HAL)
        rita_ytor(v, unary_union(polygoner(plan1, bara=VAGGAR)), None, "dold", MINSTA_HAL)
    tapp, ror = utdrag["tappstallen"], utdrag["ror"]
    with v.lager("ror"):
        for _, r in _i_ordning(ror):
            for a, b in zip(r["vag"], r["vag"][1:]):
                if _vagratt(a, b) and Z_UK < a[2] < Z_OK:
                    v.linje([(a[0], a[1]), (b[0], b[1])], r["media"].lower())
    with v.lager("ut ur bjälklaget"):
        for _, r in _i_ordning(ror):
            for a, b in zip(r["vag"], r["vag"][1:]):
                if _lodratt(a, b) and min(a[2], b[2]) < Z_OK < max(a[2], b[2]):
                    stigare(v, a[0], a[1], r["media"])
                elif _lodratt(a, b) and min(a[2], b[2]) < Z_UK < max(a[2], b[2]):
                    stigare(v, a[0], a[1], r["media"], ned=True)
    _tappstallen(v, tapp, plan1, kallare)
    with v.lager("strak"):
        for k, sp in utdrag["strak"].items():
            a, b = max(zip(sp, sp[1:]), key=lambda ab: math.dist(ab[0], ab[1]))
            c = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            ider = sorted((t for t, x in tapp.items() if x["strak"] == k), key=lambda t: tapp[t]["utgang"])
            v.ptext(c[0], c[1], 2.0, 2.0, f"Stråk {k}: " + ", ".join(ider), a="lb", sz=5.4, col="gra", bg=True)
        fs = utdrag["utrustning"]["TK-FS"]["punkt"]
        v.hanvisning((fs[0] - 60.0, fs[1]), (fs[0] - 60.0 - v.m(14.0), fs[1] + v.m(16.0)),
                     "fördelarskåpet TK-FS i källaren (VS-01.2)", a="rm", sz=5.4)
    norrpil(v, 11800.0, 9150.0, norr)
    with hela.lager("rubrik"):
        hela.rubrik(*papper(hela, 24.0, 24.0), "Mellanbjälklaget, rör för tappvatten ingjutna i betongen", round(s_))
        hela.skalstock(*papper(hela, 250.0, 20.0), langd_m=2, steg_m=1)
    under = 30.0 + (y1 - y0) / s_ + 8.0
    rader_t = [[k, t["typ"].split(" (")[0], t["rum"], sv(t["kv"], 1), sv(t["vv"], 1) if t["vv"] > 0 else "–",
                t["ror"], str(t["utgang"]), sv(t["vv_tid"], 1) if t["vv"] > 0 else "–"] for k, t in tapp.items()]
    rader_r = [[k, r["media"], r["matt"], r["fran"], sv(r["langd"] / 1000, 1), sv(r["volym"], 2)]
               for k, r in ror.items() if r["modul"] != "Teknikrum"]
    rader_g = [[x["del"], x["atgard"].replace(" (R-06)", ""), x["element"], svm(round(x["punkt"][0])),
                svm(round(x["punkt"][1]))] for x in utdrag["genomforingar"]]
    block = [
        dict(x=24.0, y=under, w=96.0, innehall=[
            dict(typ="rubrik", text="Tappställen"),
            dict(typ="tabell", kolumner=["Id", "Tappställe", "Rum", "KV", "VV", "Rör", "Utg.", "s"],
                 bredd=(0.75, 1.0, 0.7, 0.32, 0.32, 0.5, 0.32, 0.32), just=["l", "l", "l", "r", "r", "l", "r", "r"],
                 sz=5.8, rader=rader_t),
            dict(typ="text", sz=5.8, rader=["KV, VV: normflöden (l/s). Rör: PEX och skyddsrör (mm). Utg.: utgången "
                                            "på kallvattnets och varmvattnets fördelare. s: tiden till varmvatten "
                                            "vid normflödet."]),
            dict(typ="rubrik", text="Rör"),
            dict(typ="tabell", kolumner=["Rör", "Media", "Mått", "Från", "m", "l"],
                 bredd=(0.95, 0.4, 0.5, 0.75, 0.35, 0.4), just=["l", "l", "l", "l", "r", "r"], sz=5.8, rader=rader_r),
        ]),
        dict(x=126.0, y=under, w=196.0, innehall=[
            dict(typ="rubrik", text="Genomföringar och rör ut ur bjälklaget"),
            dict(typ="tabell", kolumner=["Byggdel", "Åtgärd", "Rör", "x", "y"], bredd=(0.8, 2.9, 0.75, 0.35, 0.35),
                 just=["l", "l", "l", "r", "r"], sz=5.6, rader=rader_g),
        ]),
    ]
    kol = _anvisningar(utdrag, ovriga, "Plan 1:s väggar är streckade och källarväggarna tunna. Lägen x, y i mm "
                                       "(K-05), origo som på R-05 och R-06.") + [
        dict(typ="rubrik", text="Teckenförklaring"), _teckenforklaring(TECKEN + [
            ("dold", "väggarna på plan 1"), ("hjalp", "källarväggarna")])]
    return blad(nummer, ["Tappvatten", "Rör i mellanbjälklaget"], f"1:{SKALA_BJALKLAG:g}", "Modellen", kol,
                [v, hela], block)


def _ror_i_plan(v: Vy, ror: dict, z_min: float, inne: Callable[[list[float]], bool] = lambda q: True) -> None:
    """Rörens vågräta stycken över z_min (varmvattnet under kallvattnet) och de lodräta som punkter (de som är inne)."""
    with v.lager("ror"):
        for _, r in _i_ordning(ror):
            for a, b in zip(r["vag"], r["vag"][1:]):
                if _vagratt(a, b) and z_min <= a[2] < 0.0:
                    v.linje([(a[0], a[1]), (b[0], b[1])], r["media"].lower())
    with v.lager("stigare"):
        for _, r in _i_ordning(ror):
            for a, b in zip(r["vag"], r["vag"][1:]):
                if _lodratt(a, b) and min(a[2], b[2]) < 0.0 and inne(a):
                    stigare(v, a[0], a[1], r["media"])


def _utrustning(v: Vy, utdrag: dict, etiketter: bool = True) -> None:
    """Teknikrummets utrustning i plan: värmepumpen på golvet, skåpen och mätaren på väggarna."""
    with v.lager("utrustning"):
        for k, u in utdrag["utrustning"].items():
            b, d, h = u["matt"]
            if h <= 0:
                continue
            p, n = np.array(u["punkt"][:2]), np.array(u["normal"][:2])
            if u["yta"] == "golv":
                horn = [p + np.array([sx * b / 2, sy * d / 2]) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            else:
                t = np.array([n[1], -n[0]])
                horn = [p - t * b / 2, p + t * b / 2, p + t * b / 2 + n * d, p - t * b / 2 + n * d]
            v.polygon([tuple(q) for q in horn], "vit", "tunn")
            if etiketter:
                c = sum(horn) / 4
                v.text(c[0], c[1], k, a="cm", sz=5.0, col="gra")


# ------------------------------------------------------------------ teknikrummet

def _spegla(delar: list[dict]) -> list[dict]:
    """Snittet x = konstant (y, z) speglat i y, så att vyn ser österut (norr till vänster)."""
    return [{**d, "ytor": [[[[-p[0], p[1]] for p in ring] for ring in yta] for yta in d["ytor"]]} for d in delar]


def _kanal(vent: dict | None) -> tuple[list[tuple[list[float], list[float], float]], list[dict]]:
    """Ventilationens kanaler (stycken med diameter) och fläktar i källaren (z under källarens tak)."""
    if not vent:
        return [], []
    el, typer = vent["element"], vent["typer"]
    kanaler = [(a, b, typer[e["typ"]]["b"]) for e in el.values() if e["slag"] == "kanal"
               for a, b in zip(e["vag"], e["vag"][1:]) if max(a[2], b[2]) < -100.0]
    flaktar = [{**e, **typer[e["typ"]]} for e in el.values() if e["slag"] == "flakt"]
    return kanaler, flaktar


def _teknikrum(utdrag: dict, kallare: list[dict], vyn: list[dict], vent: dict | None, nummer: str,
               ovriga: str) -> Blad:
    """Teknikrummet (1:20): planen och vyn mot V19 med fördelarskåpet, fördelarna, rören upp till källarens tak,
    matarledningarna, värmepumpen och ventilationens kanal FF3. Vyerna klipps vid sina ramar; rubrikerna, filernas
    namn och skalstocken i en vy över hela bladet."""
    ror, niv = utdrag["ror"], utdrag["nivaer"]
    kanaler, flaktar = _kanal(vent)
    s = SKALA_TEKNIK
    x0, x1, y0, y1 = TEKNIK
    bp, be = (42.0, 34.0), (132.0, 34.0)                       # vyernas övre vänstra hörn [pappersmm]
    hela = vy(s, TEKNIK, *bp)                                   # över hela bladet, i planens koordinater
    # ---------------------------------------------------------------- planen
    p = Vy(bp[0], bp[1], (x1 - x0) / s, (y1 - y0) / s, s, x0, y1, klipp=True)
    plan(p, kallare)
    with p.lager("ventilation"):
        for a, b, d in kanaler:
            if _vagratt(a, b) and abs(a[1] - b[1]) < 1.0:
                p.rekt(min(a[0], b[0]), a[1] - d / 2, max(a[0], b[0]), a[1] + d / 2, None, "dold")
        for f in flaktar:
            q = f["punkt"]
            p.rekt(q[0] - f["langd"] / 2, q[1] - f["d"] / 2, q[0] + f["langd"] / 2, q[1] + f["d"] / 2, "vit", "dold")
            p.ptext(q[0], q[1], 0.0, 0.0, "FF3", a="cm", sz=5.0, col="gra")
    _utrustning(p, utdrag, etiketter=False)
    with p.lager("fordelare"):
        for f in utdrag["fordelare"].values():
            a, b = f["start"], f["slut"]
            p.polygon([(a[0] - 16, a[1]), (b[0] - 16, b[1]), (b[0] + 16, b[1]), (a[0] + 16, a[1])], "#c9c2a8",
                      "tunn")
    _ror_i_plan(p, ror, -2500.0)
    with hela.lager("etiketter"):
        for k, t in utdrag["tappstallen"].items():              # filerna västerut ut ur planen: tappställenas id
            r = next(x for x in ror.values() if x["till"] == k and x["media"] == ("VV" if t["vv"] > 0 else "KV"))
            for a, b in zip(r["vag"], r["vag"][1:]):
                if _vagratt(a, b) and min(a[0], b[0]) < x0 < max(a[0], b[0]) and y0 < a[1] < y1:
                    hela.ptext(x0, a[1], -1.0, 0.0, k, a="rm", sz=4.8)
        u = utdrag["utrustning"]
        for k, X, Y, ank in (("TK-VP", x0 + 60.0, 7700.0, "lm"), ("TK-FS", x0 + 60.0, 8250.0, "lm"),
                             ("TK-VM", x0 + 60.0, 9000.0, "lm")):
            if k in u:
                q = u[k]["punkt"]
                hela.hanvisning((q[0], q[1]), (X, Y), f"{k} {u[k]['namn'].split(' (')[0].split(',')[0].lower()}",
                                a=ank, sz=5.2)
        hela.rubrik(*papper(hela, bp[0], bp[1] - 6.0), "Teknikrummet, plan", round(s))
    # ---------------------------------------------------------------- vyn mot V19 (österut, norr till vänster): X = −y
    omr = (-y1, -y0, Z_VY[0], Z_VY[1])
    e = Vy(be[0], be[1], (y1 - y0) / s, (Z_VY[1] - Z_VY[0]) / s, s, omr[0], omr[3], klipp=True)
    sektion(e, _spegla(vyn))

    def synlig(a: list[float], b: list[float]) -> bool:          # mellan vyns plan och V19
        return X_VY - 1.0 <= min(a[0], b[0]) and max(a[0], b[0]) <= x1

    with e.lager("utrustning"):
        for k, u_ in utdrag["utrustning"].items():
            b_, d_, h_ = u_["matt"]
            if h_ <= 0:
                continue
            q, n = u_["punkt"], u_["normal"]
            if u_["yta"] == "golv":
                e.rekt(-(q[1] + d_ / 2), q[2], -(q[1] - d_ / 2), q[2] + h_, "vit", "tunn")
                e.ptext(-q[1], q[2] + h_ / 2, 0.0, 0.0, k, a="cm", sz=5.2, col="gra")
            elif abs(n[0]) > 0.5:                                   # på V19: framifrån
                e.rekt(-(q[1] + b_ / 2), q[2] - h_ / 2, -(q[1] - b_ / 2), q[2] + h_ / 2, None, "tunn")
                e.ptext(-q[1], q[2] - h_ / 2, 0.0, -1.0, f"{k} {b_:g} × {h_:g}, z {svm(q[2] - h_ / 2)} till "
                        f"{svm(q[2] + h_ / 2)}", a="ct", sz=5.0, bg=True)
            else:                                                   # på V3: från sidan
                ya, yb = sorted((q[1], q[1] + n[1] * d_))
                e.rekt(-yb, q[2] - h_ / 2, -ya, q[2] + h_ / 2, "vit", "tunn")
    with e.lager("ventilation"):
        for a, b, d in kanaler:
            if abs(a[1] - b[1]) < 1.0 and abs(a[2] - b[2]) < 1.0 and min(a[0], b[0]) < X_VY < max(a[0], b[0]):
                e.cirkel(-a[1], a[2], d / 2, None, "dold", modell=True)
        for f in flaktar:
            q = f["punkt"]
            if q[0] - f["langd"] / 2 > X_VY:
                e.rekt(-(q[1] + f["d"] / 2), q[2] - f["d"] / 2, -(q[1] - f["d"] / 2), q[2] + f["d"] / 2, None, "dold")
                e.ptext(-q[1], q[2], 0.0, 0.0, "FF3", a="cm", sz=5.0, col="gra")
    with e.lager("fordelare"):
        for k, f in utdrag["fordelare"].items():
            ya, yb, z = f["start"][1], f["slut"][1], f["start"][2]
            e.rekt(-yb, z - 16.0, -ya, z + 16.0, "#c9c2a8", "tunn")
            e.ptext(-yb, z, -0.8, 0.0, f"{k} z {svm(z)}", a="rm", sz=5.0, bg=True)
    with e.lager("ror"):
        for _, r in _i_ordning(ror):
            for a, b in zip(r["vag"], r["vag"][1:]):
                if abs(a[0] - b[0]) > 1.0 and min(a[0], b[0]) < X_VY < max(a[0], b[0]):     # genom vyns plan
                    e.cirkel(-a[1], a[2], r["yttre"] / 2, r["media"].lower(), None, modell=True)
                elif synlig(a, b) and math.hypot(b[1] - a[1], b[2] - a[2]) > 1.0:
                    e.linje([(-a[1], a[2]), (-b[1], b[2])], r["media"].lower())
    with e.lager("nivaer"):
        for txt, z in niv.items():
            if Z_VY[0] < z < Z_VY[1]:
                e.linje([(omr[1] - e.m(16.0), z), (omr[1], z)], "tunn")
                e.ptext(omr[1], z, -0.5, 0.4, f"{'±0' if abs(z) < 0.5 else svm(z)} {txt}", a="rb", sz=4.8)
    ev = vy(s, omr, *be)                                         # rubriken och skalstocken utanför vyns ram
    with ev.lager("rubrik"):
        ev.rubrik(*papper(ev, be[0], be[1] - 6.0), f"Vy mot V19 (österut) från x = {svm(X_VY)}", round(s))
        ev.skalstock(*papper(ev, be[0], be[1] + (Z_VY[1] - Z_VY[0]) / s + 6.0), langd_m=1, steg_m=0.5)
    matare = [[k, r["media"], r["matt"], f"{r['fran']} → {r['till']}", sv(r["langd"] / 1000, 2)]
              for k, r in ror.items() if r["modul"] == "Teknikrum"]
    utr = [[k, u_["namn"]] for k, u_ in utdrag["utrustning"].items()]
    block = [dict(x=24.0, y=176.0, w=100.0, innehall=[
        dict(typ="rubrik", text="Matarledningar"),
        dict(typ="tabell", kolumner=["Rör", "Media", "Mått", "Från → till", "m"], bredd=(0.55, 0.4, 0.35, 1.6, 0.35),
             just=["l", "l", "l", "l", "r"], sz=5.8, rader=matare),
        dict(typ="rubrik", text="Fördelare"),
        dict(typ="tabell", kolumner=["Id", "Fördelare"], bredd=(0.5, 2.8), just=["l", "l"], sz=5.8,
             rader=[[k, f["typ"]] for k, f in utdrag["fordelare"].items()]),
        dict(typ="rubrik", text="Utrustning"),
        dict(typ="tabell", kolumner=["Id", "Utrustning"], bredd=(0.5, 2.8), just=["l", "l"], sz=5.8, rader=utr),
    ])]
    kol = _anvisningar(
        utdrag,
        "Fördelarskåpet på V19 med varmvattnets fördelare bakom och kallvattnets framför: rören går upp ur skåpets "
        "öppna ovansida in i mellanbjälklaget, varje rör i sin fil (c/c 40). Matarledningarna "
        "under ventilationens kanal FF3, över värmepumpen; kallvattnet in i fördelarens norra ände och vidare genom "
        "den till beredaren.",
        "Skåpet får läckageindikering till golvbrunnen i teknikrummet (Säker Vatten); avloppet ritas senare. "
        "Servisens väg till huset är inte bestämd.",
        ovriga) + [dict(typ="rubrik", text="Teckenförklaring"), _teckenforklaring(TECKEN[:2] + [
            (lambda w: stigare(w, 0.0, 0.0, "VV"), "lodrätt rör, varmvatten"),
            (lambda w: stigare(w, 0.0, 0.0, "KV"), "lodrätt rör, kallvatten"),
            (dict(form="yta", fyll="betong", stil="tunn"), "betong"),
            ("dold", "ventilationens kanal och fläkt (FF3)"),
        ])]
    return blad(nummer, ["Tappvatten", "Teknikrummet"], f"1:{s:g}", "Modellen", kol, [p, hela, e, ev], block)


def ritningar(utdrag: dict, plan1: list[dict], kallare: list[dict], mb: list[dict], vyn: list[dict],
              vent: dict | None, norr: tuple[float, float], arbete: Path, ut: Path) -> Path:
    """Tappvattenritningarna (serien SERIE): rören i mellanbjälklaget med tappställena (snitten: plan 1, källaren och
    bjälklaget) och teknikrummet (vyn: snittet x = X_VY; vent: ventilationens utdrag, för kanalen i teknikrummet), som
    pdf i mappen ut (bladen för sig i arbetsmappen, under repots rot)."""
    pre = SERIE.split()[0]
    nr = [f"{pre}.{i}" for i in range(1, 3)]
    bladen = [
        (nr[0], _bjalklag(utdrag, mb, plan1, kallare, norr, nr[0], f"Teknikrummet: {nr[1]}.")),
        (nr[1], _teknikrum(utdrag, kallare, vyn, vent, nr[1], f"Rören i mellanbjälklaget: {nr[0]}.")),
    ]
    pdf = ut / f"{SERIE}.pdf"
    kompilera(bladen, arbete, pdf)
    return pdf


def lista(utdrag: dict, kontroll: tuple[list[str], list[str]], krockar: list[str]) -> str:
    """Tappställena, rören, genomföringarna, kontrollen och krockarna mot huset som markdown."""
    fel, anm = kontroll
    tapp, ror = utdrag["tappstallen"], utdrag["ror"]
    rad = ["# Tappvattnet", "", f"{len(tapp)} tappställen, {len(ror)} rör.", "",
           f"## Kontroll: {len(fel)} fel, {len(anm)} anmärkningar", ""]
    rad += [f"- FEL {f}" for f in fel] + [f"- {a}" for a in anm]
    rad += ["", "## Krockar mot husets delar", ""] + ([f"- {k}" for k in krockar] or ["Inga."])
    rad += ["", "## Tappställen", "", "| Id | Typ | Rum | KV [l/s] | VV [l/s] | Anslutning | Rör | Utgång | Stråk | "
            "Varmvatten [s] |", "|---|---|---|---|---|---|---|---|---|---|"]
    for k, t in tapp.items():
        vv = f"{t['vv_tid']:.1f}" if t["vv"] > 0 else "–"
        rad.append(f"| {k} | {t['typ']} | {t['rum']} | {t['kv']:g} | {t['vv']:g} | {t['dosa']} | {t['ror']} | "
                   f"{t['utgang']} | {t['strak']} | {vv} |")
    rad += ["", "## Rör", "", "| Id | Media | Rör | Från | Till | Längd [m] | Volym [l] |",
            "|---|---|---|---|---|---|---|"]
    for k, r in ror.items():
        rad.append(f"| {k} | {r['media']} | {r['typ']} | {r['fran']} | {r['till']} | {r['langd'] / 1000:.2f} | "
                   f"{r['volym']:.2f} |")
    rad += ["", "## Genomföringar", "", "| Byggdel | Åtgärd | Mått | Rör | x | y | z |",
            "|---|---|---|---|---|---|---|"]
    for x in utdrag["genomforingar"]:
        q = x["punkt"]
        rad.append(f"| {x['del']} | {x['atgard']} | {x['matt']} | {x['element']} | {q[0]:.0f} | {q[1]:.0f} | "
                   f"{q[2]:.0f} |")
    return "\n".join(rad) + "\n"
