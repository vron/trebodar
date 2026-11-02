"""Elritningar ur modellens elinstallation (utdraget ur trebodar.hus.installationer.el), i ritningsmallen (A3, 1:75):
elplanen för plan 1 (armaturer, apparater och dosor med symboler, tändgruppernas styrning från brytare och dimrar,
rören i väggar och innertak) och rören i mellanbjälklaget (ingjutna rör med punkternas koordinater, dosorna och var
rören går upp i väggarna), på planer ur modellens snitt (STEP-filen).
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
SERIE = "E-01 Elinstallation"
R_LAMPA, R_APPARAT = 1.5, 0.9                     # symbolernas radie på papperet [mm]
TABELLER = dict(x=226.0, y=14.0, w=98.0)          # tabellerna till höger om planen [pappersmm]

Punkt = tuple[float, float]


def symbol(v: Vy, slag: str, X: float, Y: float, kanaler: int = 1) -> None:
    """Symbolen i modellpunkten (X, Y), i pappersmått (i stil med SS-EN 60617): armatur (cirkel med kryss; på stam
    med fylld mitt), brytare (cirkel med snett streck och ett tvärstreck per kanal), dimmer (dessutom en pil genom
    cirkeln), uttag (cirkel med streck), kopplingsdosa (kvadrat) och ingjutningsdosa (kvadrat med diagonal)."""
    c = np.array([X, Y])
    if slag in ("spot", "tubspot"):
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
    "dimmer": (lambda v: symbol(v, "dimmer", -0.6, -0.5, 2), "dimmer; tvärstrecken: kanalerna"),
    "brytare": (lambda v: symbol(v, "brytare", -0.6, -0.5), "strömbrytare"),
    "uttag": (lambda v: symbol(v, "uttag", 0.0, 0.0), "vägguttag"),
    "kopplingsdosa": (lambda v: symbol(v, "kopplingsdosa", 0.0, 0.0), "kopplingsdosa"),
}


def _typnamn(t: dict) -> str:
    return f"{t['tillverkare']} {t['namn']}, art. {t['artikel']}"


def elplan(utdrag: dict, delar: list[dict], norr: tuple[float, float], nummer: str, bjalklaget: str) -> Blad:
    """Elplanen för plan 1: punkterna, styrningen och rören i väggar och innertak (rören i bjälklaget på
    bjälklagets ritning, bjalklaget)."""
    v = vy(SKALA, PLAN1, 24.0, 27.0)
    plan(v, delar)
    rummen = {k for k, r in utdrag["rum"].items() if r["plan"] == 1}
    punkter = {k: p for k, p in utdrag["punkter"].items() if p.get("rum") in rummen}
    typer = utdrag["typer"]
    extra: dict[str, list[str]] = {k: [] for k in punkter}          # rör ned i bjälklaget vid punkten
    with v.lager("ror"):
        for k, r in utdrag["ror"].items():
            if r["fran"] not in punkter and r["till"] not in punkter:
                continue
            vag = r["vag"]
            for i0, i1 in _foljder(vag, lambda p: p[2] > -1.0):
                d = _xy(vag[i0:i1 + 1])
                if len(d) > 1:
                    v.linje(d, "ror")
                    a, b = max(zip(d, d[1:]), key=lambda s: math.dist(*s))
                    if _ryms(v, a, b, f"{k} {r['typ']}", 5.0):
                        _langs(v, a, b, f"{k} {r['typ']}")
            for a, b in [(a, b) for p, q in zip(vag, vag[1:]) for a, b in ((p, q), (q, p))]:
                if a[2] > -1.0 >= b[2]:                  # ned i bjälklaget vid a
                    nara = [q for q, p in punkter.items() if math.dist(p["punkt"][:2], a[:2]) < v.m(3)]
                    if nara:
                        extra[nara[0]].append(f"{k} ned i bjälklaget")
                    else:
                        _genomforing(v, a[0], a[1])
                        v.ptext(a[0], a[1], 1.2, -1.2, f"{k} ned", a="lt", sz=5.0, col="gra")
    with v.lager("styrning"):
        for k, p in punkter.items():
            for g in p.get("styr", []):
                for lid in utdrag["tandgrupper"][g]["lampor"]:
                    pts = _bage(v, tuple(p["punkt"][:2]), tuple(utdrag["punkter"][lid]["punkt"][:2]), R_APPARAT,
                                R_LAMPA)
                    if len(pts) > 1:
                        v.linje(pts, f"styr{_grupp(utdrag, g)}")
    with v.lager("punkter"):
        for k, p in punkter.items():
            t = typer[p["typ"]]
            X, Y = p["punkt"][:2]
            if p["slag"] == "lampa":
                _pil(v, X, Y, p["riktning"])
                symbol(v, t["symbol"], X, Y)
                v.ptext(X, Y, 1.9, 0.5, f"{k}\n{p['tand']}", a="lb", sz=5.4, col=f"tand{_grupp(utdrag, p['tand'])}")
            else:
                symbol(v, t["symbol"], X, Y, t.get("kanaler", 1))
                text = [k] + ([f"{svm(round(p['over_golv']))} över golv"] if p["yta"] == "vagg" else []) + extra[k]
                v.ptext(X, Y, 1.6, -1.4, "\n".join(text), a="lt", sz=5.4, bg=True)
    norrpil(v, 7300.0, 14600.0, norr)
    _rubrik(v, "Plan 1, elplan")
    # tabellerna
    antal: dict[str, int] = {}
    for p in punkter.values():
        if p["slag"] == "lampa":
            antal[p["typ"]] = antal.get(p["typ"], 0) + 1
    armaturer = [[_typnamn(typer[kod]), str(n), sv(typer[kod]["ljusflode"]), sv(typer[kod]["effekt"]),
                  sv(typer[kod]["fargtemperatur"]), sv(typer[kod]["ra"]), f"{sv(typer[kod]['stralvinkel'])}°",
                  f"ø{sv(typer[kod]['hal_d'])}"] for kod, n in antal.items()]
    grupper = [g for g, tg in utdrag["tandgrupper"].items() if any(lid in punkter for lid in tg["lampor"])]
    apparater = [[k, typer[p["typ"]]["namn"],
                  {"vagg": f"vägg {p['ref']}", "tak": f"tak {p['ref']}"}.get(p["yta"], f"{p['yta']} {p['ref']}"),
                  svm(round(p["over_golv"])) if p["yta"] == "vagg" else "", ", ".join(p.get("styr", []))]
                 for k, p in punkter.items() if p["slag"] != "lampa"]
    ror = [[k, r["typ"], r["fran"], r["till"], sv(r["langd"] / 1000, 1), f"{sv(r['bojar'])}°"]
           for k, r in utdrag["ror"].items()
           if (r["fran"] in punkter or r["till"] in punkter) and all(q[2] > -1.0 for q in r["vag"])]
    block: list[dict] = [dict(**TABELLER, innehall=[
        dict(typ="rubrik", text="Armaturer"),
        dict(typ="tabell", kolumner=["Armatur", "St", "lm", "W", "K", "Ra", "Vinkel", "Hål"],
             bredd=(3.4, 0.4, 0.55, 0.45, 0.65, 0.45, 0.65, 0.55), just=["l"] + ["r"] * 7, sz=6.4, rader=armaturer),
        dict(typ="rubrik", text="Tändgrupper"),
        dict(typ="symboler", rader=[
            dict(form="linje", stil=f"styr{_grupp(utdrag, g)}",
                 text=f"{g} {utdrag['tandgrupper'][g]['namn']}: {', '.join(utdrag['tandgrupper'][g]['lampor'])}, "
                      f"{'dimbar' if utdrag['tandgrupper'][g]['dimbar'] else 'ej dimbar'}, från "
                      f"{', '.join(utdrag['tandgrupper'][g]['styrs_av'])}") for g in grupper]),
        dict(typ="rubrik", text="Apparater och dosor"),
        dict(typ="tabell", kolumner=["Id", "Typ", "Montering", "Över golv", "Styr"], bredd=(0.6, 2.4, 0.9, 0.7, 1.1),
             just=["l", "l", "l", "r", "l"], sz=6.4, rader=apparater),
        dict(typ="rubrik", text="Rör i väggar och innertak"),
        dict(typ="tabell", kolumner=["Rör", "Typ", "Från", "Till", "Längd (m)", "Böjar"],
             bredd=(0.8, 0.6, 0.6, 0.6, 0.7, 0.6), just=["l", "l", "l", "l", "r", "r"], sz=6.4, rader=ror),
    ])]
    slag = {typer[p["typ"]]["symbol"] for p in punkter.values()}
    legend: list[Rad] = [(_LEGEND[s][0], _LEGEND[s][1]) for s in _LEGEND if s in slag]
    legend += [("styr0", "styrning: brytaren eller dimmern och tändgruppens armaturer (färg per tändgrupp)"),
               ("ror", "rör i vägg och innertak")]
    kol: list[dict] = [
        dict(typ="rubrik", text="Anvisningar"),
        dict(typ="lista", sz=7.0, rader=[
            "Elinstallationen ur modellen (modeller/trebodar/hus/installationer/el): armaturer, apparater, dosor, "
            "tändgrupper och rör. Lägena följer husets geometri; ritningen ritas med ./mod el ritning.",
            "Armaturerna i innertaket sitter mellan läkten (c 400) i installationsskiktet, med drivdonet bredvid. "
            "Spotar på stam riktas enligt pilen.",
            "Apparaternas höjd är centrum över färdigt golv.",
            f"Rören i mellanbjälklaget: {bjalklaget}. Gruppcentralen och grupperna läggs till när centralens läge är "
            "bestämt.",
        ]),
        dict(typ="rubrik", text="Teckenförklaring"),
        _teckenforklaring(legend),
    ]
    return blad(nummer, ["Elinstallation", "Elplan plan 1"], f"1:{SKALA:g}", "Modellen", kol, [v], block)


def bjalklag(utdrag: dict, delar: list[dict], ovan: list[dict], z: tuple[float, float], nummer: str,
             elplanen: str) -> Blad:
    """Rören ingjutna i mellanbjälklaget (z0–z1): rören, punkterna med koordinater, var rören går upp ur bjälklaget
    (in i väggarna ovanför) och dosorna, med plan 1:s väggar streckade."""
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
        dict(typ="rubrik", text="Rörens punkter (mitt i röret)"),
        dict(typ="tabell", kolumner=["Rör", "Punkt", "x", "y", "Anmärkning"], bredd=(0.8, 0.5, 0.6, 0.6, 2.0),
             just=["l", "r", "r", "r", "l"], sz=6.4, rader=punkter),
    ])]
    kol: list[dict] = [
        dict(typ="rubrik", text="Anvisningar"),
        dict(typ="lista", sz=7.0, rader=[
            "Elrören gjuts in i mellanbjälklaget (R-06), mitt i betongen. Lägen x, y i mm (K-05) i rörens punkter: "
            "origo i skärningen mellan mellanbjälklagets kanter x = 0 och y = 0, som på R-05 och R-06.",
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
    return blad(nummer, ["Elinstallation", "Rör i mellanbjälklaget"], f"1:{SKALA:g}", "Modellen", kol, [v], block)


def ritningar(utdrag: dict, plan1: list[dict], mb: list[dict], norr: tuple[float, float], arbete: Path,
              ut: Path) -> Path:
    """Elritningarna (serien SERIE): elplanen för plan 1 och rören i mellanbjälklaget, som pdf i mappen ut (bladen
    för sig i arbetsmappen, under repots rot)."""
    nr = [f"{SERIE.split()[0]}.{i}" for i in (1, 2)]
    bladen = [(nr[0], elplan(utdrag, plan1, norr, nr[0], nr[1])),
              (nr[1], bjalklag(utdrag, mb, plan1, (-150.0, 0.0), nr[1], nr[0]))]
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
