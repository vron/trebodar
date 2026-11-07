"""Elritningar ur modellens elinstallation (utdraget ur trebodar.hus.installationer.el), i ritningsmallen (A3, 1:75):
elplanen för plan 1 (armaturer, apparater och dosor med symboler, tändgruppernas styrning från brytare och dimrar,
rören i väggar och innertak), rören i mellanbjälklaget (ingjutna rör med punkternas koordinater, dosorna och var
rören går upp i väggarna), på planer ur modellens snitt (STEP-filen), och förteckningen över plan 1:s apparater,
dosor och rör.
"""
from __future__ import annotations

import math
from collections.abc import Callable
from pathlib import Path

import numpy as np
from shapely.ops import unary_union

from .planritning import (MINSTA_HAL, VAGGAR, Blad, Vy, blad, figur, kompilera, norrpil, origo, papper, plan,
                          polygoner, rita_ytor, sv, svm, vy)

SKALA = 75.0
PLAN1 = (-500.0, 14300.0, -300.0, 16300.0)        # planens område (x0, x1, y0, y1) [mm]
KALLARTAK = -150.0                                 # källarens tak: mellanbjälklagets underkant [mm]
SERIE = "E-01 Elinstallation"
R_LAMPA, R_APPARAT = 1.5, 0.9                     # symbolernas radie på papperet [mm]
TABELLER = dict(x=226.0, y=14.0, w=98.0)          # tabellerna till höger om planen [pappersmm]
NARA = 250.0                                      # apparater närmare än så på samma vägg ritas bredvid varandra [mm]
SZ_ETIKETT = 5.4                                  # etiketternas textstorlek [pt]
# etiketternas lägen i tur och ordning (du, dv pappersmm från punkten, ankare): närmast symbolen först
LAGEN_LAMPA = [(1.9, 0.5, "lb"), (1.9, -0.5, "lt"), (-1.9, 0.5, "rb"), (-1.9, -0.5, "rt"), (0.0, 2.4, "cb"),
               (0.0, -2.4, "ct"), (3.4, 1.8, "lb"), (3.4, -1.8, "lt"), (-3.4, 1.8, "rb"), (-3.4, -1.8, "rt"),
               (0.0, 4.2, "cb"), (0.0, -4.2, "ct")]
LAGEN_APPARAT = [(1.6, -1.4, "lt"), (1.6, 1.4, "lb"), (-1.6, -1.4, "rt"), (-1.6, 1.4, "rb"), (0.0, -2.2, "ct"),
                 (0.0, 2.2, "cb"), (3.2, -2.6, "lt"), (3.2, 2.6, "lb"), (-3.2, -2.6, "rt"), (-3.2, 2.6, "rb")]

Punkt = tuple[float, float]


def symbol(v: Vy, slag: str, X: float, Y: float, kanaler: int = 1) -> None:
    """Symbolen i modellpunkten (X, Y), i pappersmått (i stil med SS-EN 60617): armatur (cirkel med kryss; på stam
    med fylld mitt, pendel med en ring runt), brytare (cirkel med snett streck och ett tvärstreck per kanal), dimmer
    (dessutom en pil genom cirkeln), uttag (cirkel med streck), kopplingsdosa (kvadrat) och ingjutningsdosa (kvadrat
    med diagonal)."""
    c = np.array([X, Y])
    if slag in ("spot", "tubspot", "pendel", "vagglampa"):
        if slag in ("pendel", "vagglampa"):
            v.cirkel(X, Y, R_LAMPA + 0.6, fyll="vit", stil="tunn")
        if slag == "vagglampa":
            r, y = v.m(R_LAMPA + 0.6), Y - v.m(R_LAMPA + 1.2)
            v.linje([(X - r, y), (X + r, y)], "normal")
        v.cirkel(X, Y, R_LAMPA, fyll="vit", stil="normal")
        k = v.m(R_LAMPA) * math.sqrt(0.5)
        v.linje([(X - k, Y - k), (X + k, Y + k)], "tunn")
        v.linje([(X - k, Y + k), (X + k, Y - k)], "tunn")
        if slag == "tubspot":
            v.cirkel(X, Y, 0.55, fyll="svart", stil=None)
    elif slag in ("brytare", "dimmer"):
        v.cirkel(X, Y, R_APPARAT, fyll="vit", stil="normal")
        u = np.array([1.0, 1.0]) / math.sqrt(2)
        n = np.array([-u[1], u[0]])
        a, b = c + u * v.m(R_APPARAT), c + u * v.m(R_APPARAT + 2.2)
        v.linje([tuple(a), tuple(b)], "normal")
        for i in range(max(1, kanaler)):
            q = b - u * v.m(0.7 * i)
            v.linje([tuple(q), tuple(q + n * v.m(0.9))], "normal")
        if slag == "dimmer":
            d = np.array([1.0, -1.0]) / math.sqrt(2)
            s0, s1 = c - d * v.m(2.0), c + d * v.m(2.0)
            v.linje([tuple(s0), tuple(s1 - d * v.m(0.8))], "tunn")
            v.pil(tuple(s1), tuple(d), langd=1.0, bredd=0.8)
    elif slag == "uttag":
        v.cirkel(X, Y, R_APPARAT, fyll="vit", stil="normal")
        v.linje([(X - v.m(1.5), Y), (X + v.m(1.5), Y)], "normal")
    else:
        s = v.m(0.75)
        v.rekt(X - s, Y - s, X + s, Y + s, fyll="vit", stil="normal")
        if slag == "ingjutningsdosa":
            v.linje([(X - s, Y - s), (X + s, Y + s)], "tunn")


def _genomforing(v: Vy, X: float, Y: float) -> None:
    """Där röret går upp eller ned ur planet (i en vägg eller dosa)."""
    v.cirkel(X, Y, 0.7, fyll="svart", stil=None)


def _pil(v: Vy, X: float, Y: float, r: list[float]) -> None:
    """Ljusets riktning i planet för en riktad armatur: pil från symbolens kant."""
    lp = math.hypot(r[0], r[1])
    if lp < 0.05:                                     # lodrätt (inom 3°)
        return
    d = np.array([r[0], r[1]]) / lp
    a = np.array([X, Y]) + d * v.m(R_LAMPA)
    v.linje([tuple(a), tuple(a + d * v.m(2.4))], "normal")
    v.pil(tuple(a + d * v.m(3.4)), tuple(d), langd=1.3, bredd=1.0)


def _grupp(utdrag: dict, g: str) -> int:
    """Tändgruppens nummer i ritningsmallens färger (styr0, tand0, …)."""
    return sorted(utdrag["tandgrupper"]).index(g) % 8


def _bage(v: Vy, p0: Punkt, p1: Punkt, r0: float, r1: float, k: float = 0.18) -> list[Punkt]:
    """Styrningens båge från p0 till p1 (andragradskurva), utan delarna inom symbolerna (r0, r1 pappersmm)."""
    a, b = np.asarray(p0, float), np.asarray(p1, float)
    d = b - a
    c = (a + b) / 2 + k * np.array([-d[1], d[0]])
    t = np.linspace(0.0, 1.0, 33)[:, None]
    q = (1 - t) ** 2 * a + 2 * (1 - t) * t * c + t ** 2 * b
    return [(float(x), float(y)) for x, y in q
            if math.dist((x, y), p0) > v.m(r0 + 0.3) and math.dist((x, y), p1) > v.m(r1 + 0.3)]


def _foljder(vag: list[list[float]], inne: Callable[[list[float]], bool]) -> list[tuple[int, int]]:
    """Index (första, sista) för rörets sammanhängande följder av brytpunkter där inne(p) gäller."""
    ut: list[tuple[int, int]] = []
    start = None
    for i, p in enumerate(vag):
        if inne(p) and start is None:
            start = i
        if start is not None and (not inne(p) or i == len(vag) - 1):
            slut = i if inne(p) else i - 1
            if slut > start:
                ut.append((start, slut))
            start = None
    return ut


def _ryms(v: Vy, a: Punkt, b: Punkt, txt: str, sz: float) -> bool:
    """Om texten ryms längs sträckan a–b (textens bredd som i ritningsmallens måttlinjer)."""
    return math.dist(a, b) / v.s > len(txt) * 0.19 * sz + 2.0


def _langs(v: Vy, a: Punkt, b: Punkt, txt: str, sz: float = 5.0, col: str = "gra") -> None:
    """Text längs sträckan a–b, ovanför dess mitt."""
    t = np.subtract(b, a) / math.dist(a, b)
    ang = math.degrees(math.atan2(t[1], t[0]))
    if ang > 90.5 or ang < -89.5:
        ang += 180.0
    n = np.array([-math.sin(math.radians(ang)), math.cos(math.radians(ang))])
    q = (np.asarray(a) + np.asarray(b)) / 2 + n * v.m(0.6)
    v.text(q[0], q[1], txt, a="cb", sz=sz, rot=round(ang, 2), col=col)


def _langs_lada(v: Vy, a: Punkt, b: Punkt, txt: str, sz: float = 5.0) -> tuple[float, float, float, float]:
    """Den omslutande lådan (modellmått) för texten längs a–b som _langs ritar den."""
    t = np.subtract(b, a) / math.dist(a, b)
    n = np.array([-t[1], t[0]])
    q = (np.asarray(a) + np.asarray(b)) / 2
    lg, h = v.m(len(txt) * 0.19 * sz) / 2, v.m(0.6 + sz * 0.43)
    horn = [q + t * s_ + n * d for s_ in (-lg, lg) for d in (-h, h)]
    return (min(c[0] for c in horn), min(c[1] for c in horn), max(c[0] for c in horn), max(c[1] for c in horn))


def _xy(vag: list[list[float]]) -> list[Punkt]:
    """Rörets brytpunkter i planet, utan upprepade (lodräta delar)."""
    ut: list[Punkt] = []
    for p in vag:
        if not ut or math.dist(ut[-1], (p[0], p[1])) > 1.0:
            ut.append((p[0], p[1]))
    return ut


def _rubrik(v: Vy, text: str) -> None:
    v.rubrik(*papper(v, 24.0, 21.0), text, round(v.s))
    with v.lager("skalstock"):
        v.skalstock(*papper(v, 24.0, 27.0 + (PLAN1[3] - PLAN1[2]) / v.s + 8.0), langd_m=5, steg_m=1)


Rad = tuple[Callable[[Vy], None] | str, str] | dict


def _teckenforklaring(rader: list[Rad]) -> dict:
    """Teckenförklaringen: (ritad symbol eller linjestil, text), eller en färdig rad (dict)."""
    return dict(typ="symboler", rader=[r if isinstance(r, dict) else
                                       {**(figur(r[0]) if callable(r[0]) else dict(form="linje", stil=r[0])),
                                        "text": r[1]} for r in rader])


def _tubspot(v: Vy) -> None:
    _pil(v, -1.0, 0.0, [1.0, 0.0, -0.5])
    symbol(v, "tubspot", -1.0, 0.0)


# teckenförklaringens symboler (symbolen på ritningen: ritad, text)
_LEGEND: dict[str, tuple[Callable[[Vy], None], str]] = {
    "spot": (lambda v: symbol(v, "spot", 0.0, 0.0), "armatur, infälld i taket"),
    "tubspot": (_tubspot, "armatur på stam (spot); pilen: ljusets riktning"),
    "pendel": (lambda v: symbol(v, "pendel", 0.0, 0.0), "pendel (i sladd från en takkopp)"),
    "vagglampa": (lambda v: symbol(v, "vagglampa", 0.0, 0.0), "vägglampa (på arm från väggen)"),
    "dimmer": (lambda v: symbol(v, "dimmer", -0.6, -0.5, 2), "dimmer; tvärstrecken: kanalerna"),
    "brytare": (lambda v: symbol(v, "brytare", -0.6, -0.5), "strömbrytare"),
    "uttag": (lambda v: symbol(v, "uttag", 0.0, 0.0), "vägguttag"),
    "kopplingsdosa": (lambda v: symbol(v, "kopplingsdosa", 0.0, 0.0), "kopplingsdosa"),
    "panel": (lambda v: symbol(v, "panel", 0.0, 0.0), "LED-panel utanpå taket (ansluten i en ingjuten dosa ovanför)"),
    "ingjutningsdosa": (lambda v: symbol(v, "ingjutningsdosa", 0.0, 0.0), "ingjuten dosa i källarens tak"),
}


class _Etiketter:
    """Etiketternas lägen: provar lägen runt punkten tills etiketten inte täcker en symbol eller en tidigare
    etikett (lådor i modellmått, textens storlek uppskattad ur antalet tecken)."""

    def __init__(self, v: Vy):
        self.v = v
        self.lador: list[tuple[float, float, float, float]] = []

    def symbol(self, X: float, Y: float, r: float) -> None:
        self.lador.append((X - self.v.m(r), Y - self.v.m(r), X + self.v.m(r), Y + self.v.m(r)))

    def satt(self, X: float, Y: float, txt: str, lagen: list[tuple[float, float, str]], **kw: object) -> None:
        rader = txt.split("\n")
        w = self.v.m(max(len(r) for r in rader) * SZ_ETIKETT * 0.19)
        h = self.v.m(len(rader) * SZ_ETIKETT * 0.43)
        val = lagen[0]
        for du, dv, a in lagen:
            x0 = X + self.v.m(du) - {"l": 0.0, "c": w / 2, "r": w}[a[0]]
            y0 = Y + self.v.m(dv) - (h if a[1] == "t" else 0.0)
            lada = (x0, y0, x0 + w, y0 + h)
            if not any(lada[0] < b[2] and b[0] < lada[2] and lada[1] < b[3] and b[1] < lada[3] for b in self.lador):
                val = (du, dv, a)
                break
        du, dv, a = val
        x0 = X + self.v.m(du) - {"l": 0.0, "c": w / 2, "r": w}[a[0]]
        y0 = Y + self.v.m(dv) - (h if a[1] == "t" else 0.0)
        self.lador.append((x0, y0, x0 + w, y0 + h))
        self.v.ptext(X, Y, du, dv, txt, a=a, sz=SZ_ETIKETT, **kw)


def _grupper(punkter: dict[str, dict]) -> list[list[str]]:
    """Apparaterna i grupper: de som sitter intill varandra (närmare än NARA) på samma vägg."""
    app = [k for k, p in punkter.items() if p["slag"] == "apparat"]
    ut: list[list[str]] = []
    sedda: set[str] = set()
    for k in app:
        if k in sedda:
            continue
        g = [q for q in app if q not in sedda and punkter[q]["ref"] == punkter[k]["ref"]
             and math.dist(punkter[q]["punkt"][:2], punkter[k]["punkt"][:2]) < NARA]
        sedda |= set(g)
        ut.append(g)
    return ut


def _ritlagen(v: Vy, punkter: dict[str, dict], grupper: list[list[str]]) -> dict[str, Punkt]:
    """Punkternas lägen på ritningen: apparater i en grupp isär längs väggen, 2,4 mm på papperet."""
    ut = {k: (p["punkt"][0], p["punkt"][1]) for k, p in punkter.items()}
    for g in grupper:
        if len(g) < 2:
            continue
        n = punkter[g[0]]["normal"]
        t = np.array([-n[1], n[0]]) / max(math.hypot(n[0], n[1]), 1e-9)
        mitt = np.mean([punkter[k]["punkt"][:2] for k in g], axis=0)
        for i, k in enumerate(sorted(g, key=lambda q: float(np.dot(punkter[q]["punkt"][:2], t)))):
            q = mitt + t * v.m(2.4) * (i - (len(g) - 1) / 2)
            ut[k] = (float(q[0]), float(q[1]))
    return ut


def _typnamn(t: dict) -> str:
    lampa = f"; {t['pendel']['ljuskalla']}" if "pendel" in t else ""
    return f"{t['tillverkare']} {t['namn']}, art. {t['artikel']}{lampa}"


def _plan1(utdrag: dict, plan_: int = 1) -> dict[str, dict]:
    """Planets punkter (plan 1, eller 0: källaren)."""
    rummen = {k for k, r in utdrag["rum"].items() if r["plan"] == plan_}
    return {k: p for k, p in utdrag["punkter"].items() if p.get("rum") in rummen}


def elplan(utdrag: dict, delar: list[dict], norr: tuple[float, float], nummer: str, bjalklaget: str,
           forteckningen: str, grupperna: str, plan_: int = 1) -> Blad:
    """Elplanen för plan 1 (eller källaren, plan_ 0): punkterna, styrningen och rören i väggar och innertak (i
    källaren i väggarna; rören i bjälklaget på bjälklagets ritning, bjalklaget; plan 1:s apparater, dosor och rör i
    förteckningen, forteckningen)."""
    v = vy(SKALA, PLAN1, 24.0, 27.0)
    plan(v, delar)
    punkter = _plan1(utdrag, plan_)
    kallare = plan_ == 0

    def pa_planet(p: list[float]) -> bool:
        """Rörets punkt i planets väggar och innertak (inte i bjälklaget)."""
        return p[2] < KALLARTAK - 1.0 if kallare else p[2] > -1.0
    typer = utdrag["typer"]
    grupper = _grupper(punkter)
    rit = _ritlagen(v, punkter, grupper)
    extra: dict[str, list[str]] = {k: [] for k in punkter}          # rör ned i bjälklaget vid punkten
    rortexter: list[tuple[Punkt, Punkt, str]] = []                  # ritas efter etiketterna, där de får plats
    with v.lager("ror"):
        for k, r in utdrag["ror"].items():
            if r["fran"] not in punkter and r["till"] not in punkter:
                continue
            vag = r["vag"]
            for i0, i1 in _foljder(vag, pa_planet):
                d = _xy(vag[i0:i1 + 1])
                if len(d) > 1:
                    v.linje(d, "ror")
                    a, b = max(zip(d, d[1:]), key=lambda s: math.dist(*s))
                    if _ryms(v, a, b, f"{k} {r['typ']}", 5.0):
                        rortexter.append((a, b, f"{k} {r['typ']}"))
            riktning = "upp" if kallare else "ned"
            for a, b in [(a, b) for p, q in zip(vag, vag[1:]) for a, b in ((p, q), (q, p))]:
                if pa_planet(a) and not pa_planet(b):     # in i bjälklaget vid a
                    nara = [q for q, p in punkter.items() if math.dist(p["punkt"][:2], a[:2]) < v.m(3)]
                    if nara:
                        extra[nara[0]].append(f"{k} {riktning} i bjälklaget")
                    else:
                        _genomforing(v, a[0], a[1])
                        v.ptext(a[0], a[1], 1.2, -1.2, f"{k} {riktning}", a="lt", sz=5.0, col="gra")
    with v.lager("styrning"):
        for k, p in punkter.items():
            for g in p.get("styr", []):
                for lid in utdrag["tandgrupper"][g]["lampor"]:
                    pts = _bage(v, rit[k], tuple(utdrag["punkter"][lid]["punkt"][:2]), R_APPARAT, R_LAMPA)
                    if len(pts) > 1:
                        v.linje(pts, f"styr{_grupp(utdrag, g)}")
    with v.lager("punkter"):
        etiketter = _Etiketter(v)
        for k, p in punkter.items():
            t = typer[p["typ"]]
            X, Y = rit[k]
            if p["slag"] == "lampa":
                _pil(v, X, Y, p["riktning"])
                symbol(v, t["symbol"], X, Y)
                etiketter.symbol(X, Y, R_LAMPA + 0.6)
            else:
                symbol(v, t["symbol"], X, Y, t.get("kanaler", 1))
                etiketter.symbol(X, Y, R_APPARAT + 0.6)
        for k, p in punkter.items():
            if p["slag"] == "lampa":
                etiketter.satt(*rit[k], f"{k}\n{p['tand']}", LAGEN_LAMPA, col=f"tand{_grupp(utdrag, p['tand'])}")
        for g in grupper:
            p = punkter[g[0]]
            hojd = {round(punkter[q]["over_golv"]) for q in g if punkter[q]["yta"] == "vagg"}
            text = [", ".join(g)] + [f"{svm(z)} över golv" for z in sorted(hojd)] + [e for q in g for e in extra[q]]
            X = float(np.mean([rit[q][0] for q in g]))
            Y = float(np.mean([rit[q][1] for q in g]))
            etiketter.satt(X, Y, "\n".join(text), LAGEN_APPARAT, bg=True)
    with v.lager("rortext"):
        for a, b, txt in rortexter:
            lada = _langs_lada(v, a, b, txt)
            if not any(lada[0] < q[2] and q[0] < lada[2] and lada[1] < q[3] and q[1] < lada[3]
                       for q in etiketter.lador):
                _langs(v, a, b, txt)
                etiketter.lador.append(lada)
    norrpil(v, 7300.0, 14600.0, norr)
    _rubrik(v, "Källaren, elplan" if kallare else "Plan 1, elplan")
    # tabellerna
    antal: dict[str, int] = {}
    for p in punkter.values():
        if p["slag"] == "lampa":
            antal[p["typ"]] = antal.get(p["typ"], 0) + 1
    armaturer = [[_typnamn(typer[kod]), str(n), sv(typer[kod]["ljusflode"]), sv(typer[kod]["effekt"]),
                  sv(typer[kod]["fargtemperatur"]), sv(typer[kod]["ra"]),
                  f"{sv(typer[kod]['stralvinkel'])}°" if typer[kod]["stralvinkel"] else "–",
                  f"ø{sv(typer[kod]['hal_d'])}" if typer[kod]["hal_d"] else "–"] for kod, n in antal.items()]
    tandgrupper = [g for g, tg in utdrag["tandgrupper"].items() if any(lid in punkter for lid in tg["lampor"])]
    block: list[dict] = [dict(**TABELLER, innehall=[
        dict(typ="rubrik", text="Armaturer"),
        dict(typ="tabell", kolumner=["Armatur", "St", "lm", "W", "K", "Ra", "Vinkel", "Hål"],
             bredd=(3.4, 0.4, 0.55, 0.45, 0.65, 0.45, 0.65, 0.55), just=["l"] + ["r"] * 7, sz=6.4, rader=armaturer),
        dict(typ="rubrik", text="Tändgrupper"),
        dict(typ="symboler", rader=[
            dict(form="linje", stil=f"styr{_grupp(utdrag, g)}",
                 text=f"{g} {utdrag['tandgrupper'][g]['namn']}: {', '.join(utdrag['tandgrupper'][g]['lampor'])}, "
                      f"{'dimbar' if utdrag['tandgrupper'][g]['dimbar'] else 'ej dimbar'}, från "
                      f"{', '.join(utdrag['tandgrupper'][g]['styrs_av'])}") for g in tandgrupper]),
    ])]
    slag = {typer[p["typ"]]["symbol"] for p in punkter.values()}
    legend: list[Rad] = [(_LEGEND[s][0], _LEGEND[s][1]) for s in _LEGEND if s in slag]
    legend += [("styr0", "styrning: brytaren eller dimmern och tändgruppens armaturer (färg per tändgrupp)"),
               ("ror", "rör i väggarna" if kallare else "rör i vägg och innertak")]
    anv = ([
        "Elinstallationen i källaren ur modellen (modeller/trebodar/hus/installationer/el, rum/kallare.py och "
        "rum/teknikrum.py): armaturer, apparater, dosor, tändgrupper och rör. Lägena följer husets geometri; "
        "ritningen ritas med ./mod el ritning.",
        "Panelerna sitter utanpå betongtaket och ansluts i en ingjuten dosa ovanför sig. Rören till dem och mellan "
        "rummen är ingjutna i mellanbjälklaget (" + bjalklaget + "): ur brytarnas dosor går de rakt upp i väggen in i "
        "bjälklaget. Rören som ritas här går i KL-väggarnas regelfack och i källarväggarnas cellplast bakom gipsen.",
        "Apparaternas höjd är centrum över färdigt golv. Gruppcentralen sitter på V3 i teknikrummet; grupperna och "
        f"deras rör: {grupperna}. Uttagen i teknikrummet och tvättstugan matas ur centralens baksida.",
        "De trevliga rummens belysning (trapphallen, tvättstugan, rummen vid V2 och rummet söder om trapphallen) och "
        "uttagen i trapphallen, rummen vid V2 och rummet söder om trapphallen bestäms i ärende #51. Fläkten FF3 ansluts "
        "vid fläkten på V20 (KA-D2).",
    ] if kallare else None)
    kol: list[dict] = [
        dict(typ="rubrik", text="Anvisningar"),
        dict(typ="lista", sz=7.0, rader=anv or [
            "Elinstallationen ur modellen (modeller/trebodar/hus/installationer/el): armaturer, apparater, dosor, "
            "tändgrupper och rör. Lägena följer husets geometri; ritningen ritas med ./mod el ritning.",
            "Armaturerna i innertaket sitter mellan läkten (c 400) i installationsskiktet, med drivdonet bredvid. "
            "Spotar på stam riktas enligt pilen.",
            "Pendlarna hänger i sladd från en takkopp; deras ljusflöde är ljuskällans (lampan i sockeln, inte vald "
            "utom i Stav).",
            "Apparaternas höjd är centrum över färdigt golv. Apparater intill varandra på samma vägg ritas bredvid "
            "varandra.",
            f"Rören i mellanbjälklaget: {bjalklaget}. Apparaterna, dosorna och rören: {forteckningen}. "
            f"Gruppcentralen sitter i teknikrummet i källaren, grupperna och deras rör: {grupperna}. Vid dosor "
            f"märkta ned i bjälklaget kommer gruppens rör från centralen upp i väggen.",
        ]),
        dict(typ="rubrik", text="Teckenförklaring"),
        _teckenforklaring(legend),
    ]
    return blad(nummer, ["Elinstallation", "Elplan källaren" if kallare else "Elplan plan 1"], f"1:{SKALA:g}",
                "Modellen", kol, [v], block)


def bjalklag(utdrag: dict, delar: list[dict], ovan: list[dict], z: tuple[float, float], nummer: str,
             elplanen: str, punktbladet: str) -> tuple[Blad, list[list[str]]]:
    """Rören ingjutna i mellanbjälklaget (z0–z1): rören med punkterna numrerade, var rören går upp ur bjälklaget
    (in i väggarna ovanför) och dosorna, med plan 1:s väggar streckade; och punkternas rader (koordinaterna, till
    bladet punktbladet)."""
    v = vy(SKALA, PLAN1, 24.0, 27.0)
    plan(v, delar)
    with v.lager("vaggar_ovan"):
        rita_ytor(v, unary_union(polygoner(ovan, VAGGAR)), None, "dold", MINSTA_HAL)

    def inne(p: list[float]) -> bool:
        return z[0] - 1.0 <= p[2] <= z[1] + 1.0

    punkter: list[list[str]] = []
    ror: list[list[str]] = []
    with v.lager("ror"):
        for k, r in utdrag["ror"].items():
            vag = r["vag"]
            foljder = _foljder(vag, inne)
            if not foljder:
                continue
            ror.append([k, r["typ"], r["fran"], r["till"], sv(r["langd"] / 1000, 1), f"{sv(r['bojar'])}°"])
            for i0, i1 in foljder:
                d = _xy(vag[i0:i1 + 1])
                v.linje(d, "ror_ingjutet")
                a, b = max(zip(d, d[1:]), key=lambda s: math.dist(*s))
                if _ryms(v, a, b, f"{k} {r['typ']}", 5.6):
                    _langs(v, a, b, f"{k} {r['typ']}", sz=5.6, col="ok")
                else:                                       # kort rör: texten vid sidan, med hänvisningslinje
                    m = (np.asarray(a) + np.asarray(b)) / 2
                    t = np.subtract(b, a) / math.dist(a, b)
                    n = np.array([t[1], -t[0]]) if t[1] < 0 else np.array([-t[1], t[0]])
                    v.hanvisning(tuple(m), tuple(m + n * v.m(9.0)), f"{k} {r['typ']}", a="lm" if n[0] >= 0 else "rm",
                                 sz=5.6, punkt=False, col="ok")
                for j, q in enumerate(d):
                    anm = ""
                    if j in (0, len(d) - 1):
                        i, nasta = (i0, i0 - 1) if j == 0 else (i1, i1 + 1)
                        if 0 <= nasta < len(vag) and vag[nasta][2] > z[1] + 1.0:
                            anm = f"upp i väggen till {r['fran'] if j == 0 else r['till']}"
                            _genomforing(v, *q)
                        elif nasta < 0 or nasta >= len(vag):
                            anm = r["fran"] if j == 0 else r["till"]
                    # numret vid sidan av röret, växelvis åt höger och vänster
                    t = np.subtract(d[min(j + 1, len(d) - 1)], d[max(j - 1, 0)])
                    t = t / max(float(np.hypot(*t)), 1e-9)
                    n = np.array([-t[1], t[0]]) * (1 if j % 2 == 0 else -1)
                    v.ptext(q[0], q[1], 1.8 * n[0], 1.8 * n[1], str(j + 1), a="cm", sz=6.0, b=True, col="ok",
                            bg=True)
                    punkter.append([k, str(j + 1), svm(round(q[0])), svm(round(q[1])), anm])
    with v.lager("dosor"):
        for k, p in utdrag["punkter"].items():
            if p["slag"] == "dosa" and z[0] - 1.0 <= p["punkt"][2] <= z[1] + 1.0:
                X, Y = p["punkt"][:2]
                symbol(v, utdrag["typer"][p["typ"]]["symbol"], X, Y)
                v.ptext(X, Y, 1.4, -1.2, k, a="lt", sz=5.6, b=True, bg=True)
    origo(v)
    _rubrik(v, "Mellanbjälklaget, rör ingjutna i betongen")
    block: list[dict] = [dict(**TABELLER, innehall=[
        dict(typ="rubrik", text="Rör"),
        dict(typ="tabell", kolumner=["Rör", "Typ", "Från", "Till", "Längd (m)", "Böjar"],
             bredd=(0.8, 0.6, 0.6, 0.6, 0.7, 0.6), just=["l", "l", "l", "l", "r", "r"], sz=6.4, rader=ror),
    ])]
    kol: list[dict] = [
        dict(typ="rubrik", text="Anvisningar"),
        dict(typ="lista", sz=7.0, rader=[
            "Elrören gjuts in i mellanbjälklaget (R-06), mitt i betongen. Rörens punkter är numrerade längs varje "
            f"rör; deras lägen x, y i mm (K-05) står på {punktbladet}, med origo i skärningen mellan "
            "mellanbjälklagets kanter x = 0 och y = 0, som på R-05 och R-06.",
            f"Röret går upp i väggen ovanför (●) eller slutar i en ingjutningsdosa i källarens tak. Plan 1: "
            f"{elplanen}.",
            "Plan 1:s väggar är streckade. Ritningen ritas ur modellen med ./mod el ritning.",
        ]),
        dict(typ="rubrik", text="Teckenförklaring"),
        _teckenforklaring([
            dict(form="yta", fyll="betong", stil="tunn", text="mellanbjälklaget (snitt)"),
            ("ror_ingjutet", "rör ingjutet i bjälklaget, med punkternas nummer"),
            (lambda w: _genomforing(w, 0.0, 0.0), "röret går upp i väggen ovanför"),
            (lambda w: symbol(w, "ingjutningsdosa", 0.0, 0.0), "ingjutningsdosa i källarens tak"),
            ("dold", "väggarna på plan 1"),
        ]),
    ]
    return (blad(nummer, ["Elinstallation", "Rör i mellanbjälklaget"], f"1:{SKALA:g}", "Modellen", kol, [v], block),
            punkter)


def punktforteckning(punkter: list[list[str]], nummer: str, bjalklaget: str) -> Blad:
    """Rörens punkter i mellanbjälklaget (bladet bjalklaget) med koordinaterna, i tre spalter."""
    n = -(-len(punkter) // 3)
    block = [dict(x=24.0 + i * 101.0, y=14.0, w=97.0, innehall=[
        dict(typ="rubrik", text="Rörens punkter (mitt i röret)" + (" forts." if i else "")),
        dict(typ="tabell", kolumner=["Rör", "Punkt", "x", "y", "Anmärkning"], bredd=(0.8, 0.45, 0.55, 0.55, 2.0),
             just=["l", "r", "r", "r", "l"], sz=5.6, rader=punkter[i * n:(i + 1) * n])]) for i in range(3)]
    kol: list[dict] = [
        dict(typ="rubrik", text="Anvisningar"),
        dict(typ="lista", sz=7.0, rader=[
            f"Punkterna längs elrören i mellanbjälklaget, numrerade som på {bjalklaget}: lägen x, y i mm (K-05) i "
            "rörets mitt, med origo i skärningen mellan mellanbjälklagets kanter x = 0 och y = 0, som på R-05 och "
            "R-06. Anmärkning: punkten där röret går upp i väggen ovanför, eller dess ände.",
            "Förteckningen ritas ur modellen med ./mod el ritning.",
        ]),
    ]
    return blad(nummer, ["Elinstallation", "Rör i mellanbjälklaget, punkterna"], "–", "Modellen", kol, [], block)


def forteckning(utdrag: dict, nummer: str, elplanen: str) -> Blad:
    """Förteckningen över plan 1:s apparater och dosor och rören i väggar och innertak (tabeller)."""
    punkter = _plan1(utdrag)
    typer = utdrag["typer"]
    apparater = [[k, typer[p["typ"]]["namn"],
                  {"vagg": f"vägg {p['ref']}", "tak": f"tak {p['ref']}"}.get(p["yta"], f"{p['yta']} {p['ref']}"),
                  svm(round(p["over_golv"])) if p["yta"] == "vagg" else "", ", ".join(p.get("styr", []))]
                 for k, p in punkter.items() if p["slag"] != "lampa"]
    ror = [[k, r["typ"], r["fran"], r["till"], sv(r["langd"] / 1000, 1), f"{sv(r['bojar'])}°"]
           for k, r in utdrag["ror"].items()
           if (r["fran"] in punkter or r["till"] in punkter) and all(q[2] > -1.0 for q in r["vag"])]
    block: list[dict] = [
        dict(x=24.0, y=14.0, w=165.0, innehall=[
            dict(typ="rubrik", text="Apparater och dosor, plan 1"),
            dict(typ="tabell", kolumner=["Id", "Typ", "Montering", "Över golv", "Styr"],
                 bredd=(0.6, 2.6, 0.9, 0.7, 1.1), just=["l", "l", "l", "r", "l"], sz=6.4, rader=apparater)]),
        dict(x=200.0, y=14.0, w=120.0, innehall=[
            dict(typ="rubrik", text="Rör i väggar och innertak, plan 1"),
            dict(typ="tabell", kolumner=["Rör", "Typ", "Från", "Till", "Längd (m)", "Böjar"],
                 bredd=(0.8, 0.6, 0.6, 0.6, 0.7, 0.6), just=["l", "l", "l", "l", "r", "r"], sz=6.4, rader=ror)]),
    ]
    kol: list[dict] = [
        dict(typ="rubrik", text="Anvisningar"),
        dict(typ="lista", sz=7.0, rader=[
            f"Apparaterna, dosorna och rören på plan 1 (elplanen {elplanen}). Höjden är centrum över färdigt golv.",
            "Rörens längd och böjar mellan punkternas anslutningar (drivdonet vid armaturen, dosans mitt). Mer än "
            "270° böjar mellan två dosor är svårt att dra.",
            "Förteckningen ritas ur modellen med ./mod el ritning.",
        ]),
    ]
    return blad(nummer, ["Elinstallation", "Förteckning, plan 1"], "–", "Modellen", kol, [], block)


def gruppforteckning(utdrag: dict, nummer: str, bjalklaget: str) -> Blad:
    """Gruppcentralen och gruppförteckningen: varje grupp med säkring, faser, ledarnas area, jordfelsskydd, punkterna
    i rörens ordning och röret från centralen (tabell)."""
    c, ror = utdrag["central"], utdrag["ror"]
    rader = []
    for k, g in utdrag["grupper"].items():
        m = ror.get(f"{k}-M") or next((r for r in ror.values() if r["fran"] == "GC" and r.get("grupp") == k), None)
        lgd = sum(r["langd"] for r in ror.values() if r.get("grupp") == k) / 1000
        rader.append([k, g["namn"], g["sakring"], "3" if g["faser"] == 3 else "1", sv(g["area"], 1),
                      "typ A 30 mA" if g["jordfel"].startswith("personskydd") else "enligt tillverkaren",
                      ", ".join(g["punkter"]), f"Ø{sv(m['diameter'])}" if m else "–", sv(lgd, 1)])
    block: list[dict] = [dict(x=24.0, y=14.0, w=300.0, innehall=[
        dict(typ="rubrik", text="Grupper"),
        dict(typ="tabell", kolumner=["Grupp", "Namn", "Säkring", "Faser", "mm²", "Jordfel", "Punkter (i rörens ordning)",
                                     "Rör", "m"],
             bredd=(0.45, 2.6, 0.55, 0.4, 0.35, 0.9, 3.3, 0.4, 0.35), just=["l", "l", "r", "r", "r", "l", "l", "l", "r"],
             sz=6.4, rader=rader)])]
    kol: list[dict] = [
        dict(typ="rubrik", text="Anvisningar"),
        dict(typ="lista", sz=7.0, rader=[
            f"Gruppcentralen sitter i teknikrummet på V3 väster om vattenmätaren, med 800 mm fritt framför: "
            f"huvudbrytare {c['huvudbrytare']}, överspänningsskydd {c['overspanningsskydd']} och en "
            f"personskyddsautomat (dvärgbrytare och jordfelsbrytare typ A 30 mA) per grupp; värmepumpen enligt "
            f"dess tillverkare (typ B om den kräver det). Utförande enligt SS 436 40 00.",
            "Ledarna FK med skyddsledare i rör, 1,5 mm² för 10 A och 2,5 mm² för 16 A; hällen och värmepumpen 400 V "
            "med fem ledare i rör Ø20. En grupp per rör från centralen.",
            f"Varje grupps rör från centralen till dess första punkt går ingjutet i mellanbjälklaget ({bjalklaget}); "
            f"därifrån går rören mellan punkterna i apparatdosorna, i väggarna och innertaket (förgrenat i dosorna). "
            f"Belysningen matas genom brytarna och dimrarna som styr den. Längden är gruppens alla rör.",
            "Förteckningen ritas ur modellen med ./mod el ritning (modeller/trebodar/hus/installationer/el/grupper.py).",
        ]),
    ]
    return blad(nummer, ["Elinstallation", "Gruppförteckning"], "–", "Modellen", kol, [], block)


def ritningar(utdrag: dict, plan1: list[dict], mb: list[dict], kallare: list[dict], norr: tuple[float, float],
              arbete: Path, ut: Path) -> Path:
    """Elritningarna (serien SERIE): elplanen för plan 1, rören i mellanbjälklaget, förteckningen över plan 1:s
    apparater, dosor och rör, gruppförteckningen, rörens punkter i bjälklaget och källarens elplan, som pdf i mappen
    ut (bladen för sig i arbetsmappen, under repots rot)."""
    nr = [f"{SERIE.split()[0]}.{i}" for i in (1, 2, 3, 4, 5, 6)]
    mb_blad, mb_punkter = bjalklag(utdrag, mb, plan1, (-150.0, 0.0), nr[1], nr[0], nr[4])
    bladen = [(nr[0], elplan(utdrag, plan1, norr, nr[0], nr[1], nr[2], nr[3])),
              (nr[1], mb_blad),
              (nr[2], forteckning(utdrag, nr[2], nr[0])),
              (nr[3], gruppforteckning(utdrag, nr[3], nr[1])),
              (nr[4], punktforteckning(mb_punkter, nr[4], nr[1])),
              (nr[5], elplan(utdrag, kallare, norr, nr[5], nr[1], nr[2], nr[3], plan_=0))]
    pdf = ut / f"{SERIE}.pdf"
    kompilera(bladen, arbete, pdf)
    return pdf


def lista(utdrag: dict, kontroll: tuple[list[str], list[str]]) -> str:
    """Punktlista, tändgrupper, rörlista och kontrollen som markdown."""
    fel, anm = kontroll
    rad = ["# Elinstallationen", "", f"{len(utdrag['punkter'])} punkter, {len(utdrag['tandgrupper'])} tändgrupper, "
           f"{len(utdrag['ror'])} rör ({sum(r['langd'] for r in utdrag['ror'].values()) / 1000:.1f} m).", "",
           f"## Kontroll: {len(fel)} fel, {len(anm)} anmärkningar", ""]
    rad += [f"- FEL {f}" for f in fel] + [f"- {a}" for a in anm]
    rad += ["", "## Punkter", "", "| Id | Slag | Typ | x | y | z | Yta | Tändgrupp / styr |",
            "|---|---|---|---|---|---|---|---|"]
    for k, p in utdrag["punkter"].items():
        x, y, z = p["punkt"]
        rad.append(f"| {k} | {p['slag']} | {utdrag['typer'][p['typ']]['namn']} | {x:.0f} | {y:.0f} | {z:.0f} | "
                   f"{p['yta']} {p['ref']} | {p.get('tand', ', '.join(p.get('styr', [])))} |")
    rad += ["", "## Tändgrupper", "", "| Id | Namn | Lampor | Styrs av |", "|---|---|---|---|"]
    for k, t in utdrag["tandgrupper"].items():
        rad.append(f"| {k} | {t['namn']} | {', '.join(t['lampor'])} | {', '.join(t['styrs_av'])} |")
    rad += ["", "## Rör", "", "| Id | Typ | Från | Till | Längd [m] | Böjar [°] |", "|---|---|---|---|---|---|"]
    for k, r in utdrag["ror"].items():
        rad.append(f"| {k} | {r['typ']} | {r['fran']} | {r['till']} | {r['langd'] / 1000:.2f} | {r['bojar']:.0f} |")
    return "\n".join(rad) + "\n"
