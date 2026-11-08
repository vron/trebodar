"""Ventilationsritningar ur modellens ventilation (utdraget ur trebodar.hus.installationer.ventilation), i
ritningsmallen (A3): planerna för plan 1 och källaren (kanalerna med frånluft, stigarledningarna, donen, fläktarna,
avluftsdonen och flödena) och en sektion längs källarrummets kanal upp genom väggen 1C till taket, med
genomföringarna. Planerna och sektionen ur modellens snitt (STEP-filen).
"""
from __future__ import annotations

import math
from collections.abc import Callable
from pathlib import Path

import numpy as np
from shapely.geometry import LineString, Polygon

from .planritning import Blad, Vy, blad, figur, kompilera, norrpil, papper, plan, sektion, sv, svm, vy

SERIE = "VL-01 Ventilation"
SKALA, SKALA_SEKTION = 75.0, 50.0
PLAN1 = (-500.0, 14300.0, -300.0, 16300.0)          # planernas område (x0, x1, y0, y1) [mm]
TABELLER = dict(x=226.0, y=14.0, w=98.0)            # tabellerna till höger om planerna [pappersmm]
R_FLAKT = 1.6                                       # fläktsymbolens radie på papperet [mm]

Pkt = tuple[float, float]


# ------------------------------------------------------------------ symboler (pappersmått)

def flakt(v: Vy, X: float, Y: float, riktning: Pkt = (1.0, 0.0)) -> None:
    """Fläkt (SS-EN 12792): cirkel med en triangel som pekar i luftens riktning."""
    v.cirkel(X, Y, R_FLAKT, fyll="vit", stil="normal")
    d = np.asarray(riktning, float)
    d = d / float(np.hypot(*d))
    n = np.array([-d[1], d[0]])
    c = np.array([X, Y])
    r = v.m(R_FLAKT)
    v.linje([tuple(c + d * r), tuple(c - d * r * 0.5 + n * r * 0.87), tuple(c - d * r * 0.5 - n * r * 0.87),
             tuple(c + d * r)], "tunn")


def stigare(v: Vy, X: float, Y: float, b: float, h: float, bredd_langs: Pkt, rund: bool) -> None:
    """Lodrät kanal (stigarledning) i plan: tvärsnittet med frånluftens färg och en diagonal."""
    if rund:
        v.cirkel(X, Y, b / 2, fyll="franluft", stil="tunn", modell=True)
        k = b / 2 * math.sqrt(0.5)
        v.linje([(X - k, Y - k), (X + k, Y + k)], "tunn")
        return
    u = np.asarray(bredd_langs, float)
    u = u / float(np.hypot(*u)) if np.hypot(*u) > 1e-6 else np.array([1.0, 0.0])
    n = np.array([-u[1], u[0]])
    c = np.array([X, Y])
    horn = [c - u * b / 2 - n * h / 2, c + u * b / 2 - n * h / 2, c + u * b / 2 + n * h / 2, c - u * b / 2 + n * h / 2]
    v.polygon([tuple(p) for p in horn], "franluft", "tunn")
    v.linje([tuple(horn[0]), tuple(horn[2])], "tunn")


def avluft(v: Vy, X: float, Y: float, ut: Pkt) -> None:
    """Avluft genom fasaden: pil ut från huset."""
    d = np.asarray(ut, float) / float(np.hypot(*ut))
    a = np.array([X, Y]) + d * v.m(0.6)
    v.linje([tuple(a), tuple(a + d * v.m(3.0))], "normal")
    v.pil(tuple(a + d * v.m(4.2)), tuple(d), langd=1.3, bredd=1.0)


def frandon(v: Vy, X: float, Y: float, d: float) -> None:
    """Frånluftsdon: cirkel med F."""
    v.cirkel(X, Y, max(d / 2 / v.s, 1.4), fyll="vit", stil="normal")
    v.text(X, Y, "F", a="cm", sz=5.5, b=True)


# ------------------------------------------------------------------ hjälp

def _halvbredd(typ: dict, bredd_langs: list[float]) -> float:
    """Kanalens halva bredd i plan för ett vågrätt stycke (med isoleringen)."""
    b, h, iso = typ["b"], typ["h"], typ["isolering"]
    if typ["form"] == "rund":
        return b / 2 + iso
    liggande = abs(bredd_langs[2]) < 0.5
    return (b if liggande else h) / 2 + iso


def _halvbredd_xz(typ: dict, bredd_langs: list[float], riktning: Pkt) -> float:
    """Kanalens halva bredd i sektionens plan (x, z) vinkelrätt mot stycket (med isoleringen)."""
    b, h, iso = typ["b"], typ["h"], typ["isolering"]
    if typ["form"] == "rund":
        return b / 2 + iso
    lodratt = abs(riktning[1]) > abs(riktning[0])
    i_planet = abs(bredd_langs[0]) > 0.5 if lodratt else abs(bredd_langs[2]) > 0.5
    return (b if i_planet else h) / 2 + iso


def _langs(v: Vy, a: Pkt, b: Pkt, txt: str, sz: float = 5.2, col: str = "ink", avstand: float = 0.6) -> None:
    t = np.subtract(b, a) / math.dist(a, b)
    ang = math.degrees(math.atan2(t[1], t[0]))
    if ang > 90.5 or ang < -89.5:
        ang += 180.0
    n = np.array([-math.sin(math.radians(ang)), math.cos(math.radians(ang))])
    q = (np.asarray(a) + np.asarray(b)) / 2 + n * v.m(avstand)
    v.text(q[0], q[1], txt, a="cb", sz=sz, rot=round(ang, 2), col=col)


def _i_vaningen(z: float, vaning: tuple[float, float]) -> bool:
    return vaning[0] - 1.0 <= z <= vaning[1] + 1.0


def _teckenforklaring(rader: list[tuple[Callable[[Vy], None] | str | dict, str]]) -> dict:
    ut = []
    for s, t in rader:
        if isinstance(s, dict):
            ut.append({**s, "text": t})
        elif callable(s):
            ut.append({**figur(s), "text": t})
        else:
            ut.append(dict(form="linje", stil=s, text=t))
    return dict(typ="symboler", rader=ut)


def _kanalprov(w: Vy) -> None:
    w.rekt(-4.0, -0.8, 4.0, 0.8, fyll="franluft", stil="tunn")


TECKEN: list[tuple[Callable[[Vy], None] | str | dict, str]] = [
    (_kanalprov, "kanal med frånluft (yttermått, med isolering)"),
    (lambda w: stigare(w, 0.0, 0.0, 2.2, 2.2, (1.0, 0.0), True), "lodrät kanal (stigarledning)"),
    (lambda w: flakt(w, 0.0, 0.0), "fläkt (triangeln i luftens riktning)"),
    (lambda w: frandon(w, 0.0, 0.0, 2.6), "frånluftsdon"),
    (lambda w: avluft(w, -3.0, 0.0, (1.0, 0.0)), "avluft genom fasaden (galler) eller taket (takhuv, takfläkt)"),
    ("dold", "över snittet: köksfläktens kåpa, takhuven"),
]


# ------------------------------------------------------------------ planerna

def _plan(utdrag: dict, delar: list[dict], vaning: tuple[float, float], nummer: str, titel: str, rubrik: str,
          norr: tuple[float, float] | None, ovriga: str) -> Blad:
    """Ventilationen på en våning (z-intervallet vaning): kanalerna, stigarna, donen, fläktarna och avluftsdonen."""
    v = vy(SKALA, PLAN1, 24.0, 27.0)
    plan(v, delar)
    el, typer = utdrag["element"], utdrag["typer"]
    visade: set[str] = set()
    stigar: dict[tuple[int, int], list[str]] = {}
    with v.lager("kanaler"):
        for k, e in el.items():
            if e["slag"] != "kanal":
                continue
            typ = typer[e["typ"]]
            vag = e["vag"]
            langsta: tuple[float, Pkt, Pkt] | None = None
            for a, b in zip(vag, vag[1:]):
                if math.dist(a, b) < 1.0:
                    continue
                if math.hypot(b[0] - a[0], b[1] - a[1]) < 1.0:                # lodrätt: stigare genom bjälklaget
                    z0, z1 = sorted((a[2], b[2]))
                    if z0 < vaning[1] and z1 > vaning[0] and (z0 < vaning[0] - 1.0 or z1 > vaning[1] + 1.0):
                        stigare(v, a[0], a[1], typ["b"] + 2 * typ["isolering"], typ["h"] + 2 * typ["isolering"],
                                (e["bredd_langs"][0], e["bredd_langs"][1]), typ["form"] == "rund")
                        riktning = "från källaren" if z0 < vaning[0] - 1.0 else "upp till plan 1"
                        stigar.setdefault((round(a[0]), round(a[1])), []).append(f"{k} {typ['matt']} {riktning}")
                        visade.add(k)
                    continue
                if not (_i_vaningen(a[2], vaning) and _i_vaningen(b[2], vaning)):
                    continue
                hb = _halvbredd(typ, e["bredd_langs"])
                v.polygon(list(LineString([a[:2], b[:2]]).buffer(hb, cap_style=2).exterior.coords), "franluft",
                          "tunn")
                visade.add(k)
                lgd = math.hypot(b[0] - a[0], b[1] - a[1])
                if langsta is None or lgd > langsta[0]:
                    langsta = (lgd, (a[0], a[1]), (b[0], b[1]))
            if langsta and langsta[0] / v.s > len(f"{k} {typ['matt']}") * 0.19 * 5.2 + 3.0:
                _langs(v, langsta[1], langsta[2], f"{k} {typ['matt']}",
                       avstand=_halvbredd(typ, e["bredd_langs"]) / v.s + 0.6)
    with v.lager("stigare"):
        for (x, y), namn in stigar.items():
            v.ptext(x, y, -2.6, -2.2, "\n".join(dict.fromkeys(namn)), a="rt", sz=5.0, bg=True)
    flode = {g: f"{sv(d['flode'])} l/s" + (f" (grund {sv(d['flode_normal'])})" if d["flode_normal"] and
                                            d["flode_normal"] != d["flode"] else "")
             for g, d in utdrag["grenar"].items()}
    with v.lager("element"):
        for k, e in el.items():
            if e["slag"] == "kanal":
                continue
            typ = typer[e["typ"]]
            p = e["punkt"]
            if e["slag"] == "don" and typ["slag"] == "köksfläkt" and _i_vaningen(p[2], vaning):
                n = np.array(e["normal"][:2])
                u = np.array([-n[1], n[0]])
                c = np.array(p[:2])
                kapa = [c - u * typ["b"] / 2, c + u * typ["b"] / 2, c + u * typ["b"] / 2 + n * typ["d"],
                        c - u * typ["b"] / 2 + n * typ["d"]]
                v.polygon([tuple(q) for q in kapa], None, "dold")
                sb, sd = typ["skorsten"]
                sk = [c - u * sb / 2, c + u * sb / 2, c + u * sb / 2 + n * sd, c - u * sb / 2 + n * sd]
                v.polygon([tuple(q) for q in sk], None, "dold")
                m = c + n * typ["d"] * 0.62
                flakt(v, m[0], m[1], tuple(-n))
                v.ptext(m[0], m[1], -2.4, 0.0, f"{k} köksfläkt\n{flode[e['gren']]}", a="rm", sz=5.4, bg=True)
                visade.add(k)
            elif e["slag"] == "don" and typ["slag"] == "väggfläkt" and _i_vaningen(p[2], vaning):
                n = np.array(e["normal"][:2])
                c = np.array(p[:2]) + n * v.m(R_FLAKT + 0.3)
                flakt(v, c[0], c[1], tuple(-n))
                v.ptext(c[0], c[1], 2.4 * n[0] + 1.6, 2.4 * n[1] - 1.0, f"{k} väggfläkt\n{flode[e['gren']]}", a="lt",
                        sz=5.4, bg=True)
                visade.add(k)
            elif e["slag"] == "don" and _i_vaningen(p[2], vaning):
                frandon(v, p[0], p[1], typ["front_d"])
                v.ptext(p[0], p[1], 2.2, 1.2, f"{k} frånluftsdon\n{flode[e['gren']]}", a="lb", sz=5.4, bg=True)
                visade.add(k)
            elif e["slag"] == "flakt" and _i_vaningen(p[2], vaning):
                r = np.array(e["riktning"][:2])
                flakt(v, p[0], p[1], tuple(r))
                v.ptext(p[0], p[1], 0.0, -R_FLAKT - 1.0, f"{k} kanalfläkt", a="ct", sz=5.4, bg=True)
                visade.add(k)
            elif e["slag"] == "avluft" and typ["slag"] == "galler" and vaning[0] >= -1.0:
                n = np.array(e["normal"][:2])
                avluft(v, p[0], p[1], tuple(n))
                q = np.array(p[:2]) + n * v.m(5.0)
                v.text(q[0], q[1] - v.m(1.2), f"{k} galler", a="lt" if n[0] >= 0 else "rt", sz=5.2, bg=True)
                visade.add(k)
            elif e["slag"] == "avluft" and typ["slag"] in ("takhuv", "takfläkt") and vaning[0] >= -1.0:
                v.cirkel(p[0], p[1], typ["b"] / 2, None, "dold", modell=True)
                v.ptext(p[0], p[1], 2.6, 2.0, f"{k} {typ['slag']}", a="lb", sz=5.4, bg=True)
                visade.add(k)
    if norr:
        norrpil(v, 7300.0, 14600.0, norr)
    v.rubrik(*papper(v, 24.0, 21.0), rubrik, round(v.s))
    with v.lager("skalstock"):
        v.skalstock(*papper(v, 24.0, 27.0 + (PLAN1[3] - PLAN1[2]) / v.s + 8.0), langd_m=5, steg_m=1)
    grenar = utdrag["grenar"]
    rader = [[g, d["namn"], d["rum"], sv(d["flode"]), sv(d["flode_normal"]), sv(d["tryckfall"], 1)]
             for g, d in grenar.items() if any(x in visade for x in d["element"])]
    kanaler = [[k, typer[e["typ"]]["matt"] + (" isol." if typer[e["typ"]]["isolering"] else ""),
                sv(e["langd"] / 1000, 2), f"{sv(e['bojar'])}°", sv(e["hastighet"], 1)]
               for k, e in el.items() if e["slag"] == "kanal" and k in visade]
    block = [dict(**TABELLER, innehall=[
        dict(typ="rubrik", text="Frånluft"),
        dict(typ="tabell", kolumner=["Gren", "Fläkt", "Rum", "l/s", "grund", "Pa"],
             bredd=(0.5, 1.1, 1.0, 0.45, 0.5, 0.45), just=["l", "l", "l", "r", "r", "r"], sz=6.4, rader=rader),
        dict(typ="text", sz=6.2, rader=["Flödet forcerat och grundflödet. Pa: kanalernas tryckfall ungefär (friktion "
                                        "och böjar, utan don och avluftsdon)."]),
        dict(typ="rubrik", text="Kanaler"),
        dict(typ="tabell", kolumner=["Kanal", "Mått", "Längd (m)", "Böjar", "m/s"], bredd=(0.8, 1.1, 0.7, 0.6, 0.5),
             just=["l", "l", "r", "r", "r"], sz=6.4, rader=kanaler),
        dict(typ="rubrik", text="Produkter"),
        dict(typ="tabell", kolumner=["Element", "Produkt"], bredd=(0.6, 3.0), just=["l", "l"], sz=6.2,
             rader=[[k, typer[e["typ"]]["namn"]] for k, e in el.items() if e["slag"] != "kanal" and k in visade]),
    ])]
    kol: list[dict] = [
        dict(typ="rubrik", text="Anvisningar"),
        dict(typ="lista", sz=7.0, rader=[
            "Ventilationen ur modellen (modeller/trebodar/hus/installationer/ventilation): frånluft med egen fläkt per "
            "gren, från donet i rummet till avluften ute. Ritningen ritas med ./mod ventilation ritning.",
            "Kanalernas yttermått i skala; lodräta kanaler som tvärsnitt med diagonal. Produkterna är ännu inte "
            "valda (allmänna typer med vanliga mått och flöden).",
            ovriga,
            "Ersättningsluft (uteluftsdon eller spjäll som öppnar med köksfläkten) är inte projekterad; kaminen kräver "
            "att huset inte får undertryck.",
        ]),
        dict(typ="rubrik", text="Teckenförklaring"),
        _teckenforklaring(TECKEN),
    ]
    return blad(nummer, ["Ventilation", titel], f"1:{SKALA:g}", "Modellen", kol, [v], block)


# ------------------------------------------------------------------ sektionen

def sektioner(utdrag: dict) -> list[tuple[str, float]]:
    """Grenarna som går genom mellanbjälklaget och sektionens y (där kanalen går genom bjälklaget)."""
    return [(x["element"].split("-")[0], x["punkt"][1]) for x in utdrag["genomforingar"]
            if x["del"] == "Mellanbjälklaget"]


def _sektion(utdrag: dict, delar: list[dict], gren: str, y: float, nummer: str, plan1: str, kallare: str) -> Blad:
    """Sektionen y = konstant längs grenens kanal (x, z): huset ur snittet och grenens kanaler, don, fläkt och
    avluftsdon, med genomföringarna. Området ur grenens geometri, från källarens golv till takhuven."""
    el, niv = utdrag["element"], utdrag["nivaer"]
    pkt = [p for k in utdrag["grenar"][gren]["element"] for p in (el[k]["vag"] if "vag" in el[k] else [el[k]["punkt"]])]
    xs, zs = [p[0] for p in pkt], [p[2] for p in pkt]
    omrade = (min(xs) - 1900.0, max(xs) + 5400.0, niv["källarens golv"] - 450.0, max(zs) + 800.0)
    v = vy(SKALA_SEKTION, omrade, 24.0, 27.0)
    ram = Polygon([(omrade[0], omrade[2]), (omrade[1], omrade[2]), (omrade[1], omrade[3]), (omrade[0], omrade[3])])
    sektion(v, delar, ram)
    typer = utdrag["typer"]
    mina = utdrag["grenar"][gren]["element"]
    with v.lager("kanaler"):
        for k in mina:
            e = el[k]
            if e["slag"] != "kanal":
                continue
            typ = typer[e["typ"]]
            for a, b in zip(e["vag"], e["vag"][1:]):
                if math.dist(a, b) < 1.0:
                    continue
                if abs(a[1] - y) < 50.0 and abs(b[1] - y) < 50.0:          # i sektionens plan
                    hb = _halvbredd_xz(typ, e["bredd_langs"], (b[0] - a[0], b[2] - a[2]))
                    v.polygon(list(LineString([(a[0], a[2]), (b[0], b[2])]).buffer(hb, cap_style=2).exterior.coords),
                              "franluft", "tunn")
                elif (a[1] - y) * (b[1] - y) <= 0.0 or min(abs(a[1] - y), abs(b[1] - y)) < 1.0:
                    # tvärs sektionen: kanalens tvärsnitt där den möter planet
                    p = a if abs(a[1] - y) < abs(b[1] - y) else b
                    v.cirkel(p[0], p[2], typ["b"] / 2 + typ["isolering"], "franluft", "tunn", modell=True)
            v.ptext(*_mitt(e["vag"]), 1.8, 0.0, f"{k} {typ['matt']}", a="lm", sz=5.4, bg=True)
    with v.lager("element"):
        for k in mina:
            e = el[k]
            typ = typer[e["typ"]]
            if e["slag"] == "flakt":
                p = e["punkt"]
                L, D = typ["langd"], typ["d"]
                if abs(e["riktning"][0]) < 0.5:                         # luften tvärs sektionen: fläkten framifrån
                    v.cirkel(p[0], p[2], D / 2, "vit", "normal", modell=True)
                    v.cirkel(p[0], p[2], 0.5, "svart", None)
                else:
                    v.rekt(p[0] - L / 2, p[2] - D / 2, p[0] + L / 2, p[2] + D / 2, fyll="vit", stil="normal")
                    flakt(v, p[0], p[2], (e["riktning"][0], e["riktning"][2]))
                v.ptext(p[0], p[2], 0.0, -D / 2 / v.s - 1.0, f"{k} kanalfläkt", a="ct", sz=5.4, bg=True)
            elif e["slag"] == "avluft" and typ["slag"] == "takhuv":
                p = e["punkt"]
                r = typ["anslutning"] / 2 + 3.0
                v.rekt(p[0] - r, p[2], p[0] + r, p[2] + typ["h"] - 60.0, fyll="#bdbdbd", stil="tunn")
                v.rekt(p[0] - typ["b"] / 2, p[2] + typ["h"] - 60.0, p[0] + typ["b"] / 2, p[2] + typ["h"] - 10.0,
                       fyll="#bdbdbd", stil="tunn")
                v.ptext(p[0], p[2] + typ["h"], 0.0, 1.0, f"{k} takhuv", a="cb", sz=5.4, bg=True)
            elif e["slag"] == "avluft" and typ["slag"] == "takfläkt":
                # sockeln från taket till den vågräta överkanten, fläktens bottenplatta och huset ovanpå
                p = e["punkt"]
                r, zs = typ["b"] / 2, p[2] + typ["sockel"]
                v.rekt(p[0] - r, p[2] - r * 0.6, p[0] + r, zs, fyll="#bdbdbd", stil="tunn")
                v.rekt(p[0] - r, zs, p[0] + r, zs + 10.0, fyll="#555555", stil="tunn")
                v.rekt(p[0] - typ["hus"] / 2, zs + 10.0, p[0] + typ["hus"] / 2, zs + typ["h"], fyll="#555555",
                       stil="tunn")
                v.ptext(p[0], zs + typ["h"], 0.0, 1.0, f"{k} takfläkt", a="cb", sz=5.4, bg=True)
    # genomföringarna: hänvisningar till en kolumn till höger om kanalen, i höjdordning
    gf = sorted((x for x in utdrag["genomforingar"] if x["element"] in mina), key=lambda x: -x["punkt"][2])
    x_kol = max(p[0] for k in mina if el[k]["slag"] == "kanal" for p in el[k]["vag"]) + v.m(14.0)
    with v.lager("genomforingar"):
        z_forra = 1e9
        for x in gf:
            p = x["punkt"]
            z = min(p[2], z_forra - v.m(6.0))
            z_forra = z
            v.hanvisning((p[0], p[2]), (x_kol, z), f"{x['del']}: {x['atgard']}, {x['matt']}", a="lm", sz=5.4)
    with v.lager("nivaer"):
        for txt, z in utdrag["nivaer"].items():
            txt = f"{'±0' if abs(z) < 0.5 else svm(z)} {txt}"
            v.linje([(omrade[0], z), (omrade[0] + v.m(10.0), z)], "tunn")
            v.ptext(omrade[0], z, 0.5, 0.6, txt, a="lb", sz=5.4)
    vagg = next((x["del"].lower() for x in utdrag["genomforingar"] if x["element"] in mina
                 and x["atgard"].startswith("i regelfacket")), "bjälklaget")
    v.rubrik(*papper(v, 24.0, 21.0), f"Sektion y = {svm(y)}, {utdrag['grenar'][gren]['namn'].lower()} upp genom "
             f"{vagg}", round(v.s))
    with v.lager("skalstock"):
        v.skalstock(*papper(v, 24.0, 27.0 + (omrade[3] - omrade[2]) / v.s + 8.0), langd_m=2, steg_m=1)
    alla = utdrag["genomforingar"]
    block = [dict(x=24.0, y=27.0 + (omrade[3] - omrade[2]) / v.s + 16.0, w=200.0, innehall=[
        dict(typ="rubrik", text="Genomföringar (alla grenar)"),
        dict(typ="tabell", kolumner=["Byggdel", "Åtgärd", "Mått", "Kanal", "x", "y", "z"],
             bredd=(1.1, 2.6, 0.6, 0.5, 0.45, 0.45, 0.45), just=["l", "l", "l", "l", "r", "r", "r"], sz=6.2,
             rader=[[x["del"], x["atgard"], x["matt"], x["element"], svm(round(x["punkt"][0])),
                     svm(round(x["punkt"][1])), svm(round(x["punkt"][2]))] for x in alla]),
    ])]
    kol: list[dict] = [
        dict(typ="rubrik", text="Anvisningar"),
        dict(typ="lista", sz=7.0, rader=[
            *utdrag["grenar"][gren]["beskrivning"],
            f"Höjder z från plan 1:s golv (mellanbjälklagets överkant); x, y i K-05:s koordinater. Planerna: {plan1}, "
            f"{kallare}.",
        ]),
        dict(typ="rubrik", text="Teckenförklaring"),
        _teckenforklaring([
            (dict(form="yta", fyll="betong", stil="tunn"), "betong"),
            (dict(form="yta", fyll="limtra", stil="tunn"), "stomme (trä)"),
            (dict(form="yta", fyll="isol", stil="fin"), "isolering"),
            (_kanalprov, "kanal med frånluft"),
            (lambda w: flakt(w, 0.0, 0.0), "fläkt"),
        ]),
    ]
    return blad(nummer, ["Ventilation", f"Sektion, {utdrag['grenar'][gren]['namn'].lower()}"],
                f"1:{SKALA_SEKTION:g}", "Modellen", kol, [v], block)


def _mitt(vag: list[list[float]]) -> tuple[float, float]:
    """Mitten av vägens längsta stycke i sektionens plan (x, z)."""
    a, b = max(zip(vag, vag[1:]), key=lambda s: math.dist(s[0], s[1]))
    return (a[0] + b[0]) / 2, (a[2] + b[2]) / 2


def ritningar(utdrag: dict, plan1: list[dict], kallare: list[dict], snitt: dict[tuple[str, float], list[dict]],
              norr: tuple[float, float], arbete: Path, ut: Path) -> Path:
    """Ventilationsritningarna (serien SERIE): plan 1, källaren och en sektion per gren genom mellanbjälklaget (snitt:
    sektionernas snitt per (gren, y), se sektioner), som pdf i mappen ut (bladen för sig i arbetsmappen, under repots
    rot)."""
    pre = SERIE.split()[0]
    nr = [f"{pre}.{i}" for i in range(1, 3 + len(snitt))]
    sekt = ", ".join(nr[2:])
    niv = utdrag["nivaer"]
    bladen = [
        (nr[0], _plan(utdrag, plan1, (0.0, 1e5), nr[0], "Plan 1", "Plan 1, ventilation", norr,
                      f"Källaren: {nr[1]}; sektionerna: {sekt}.")),
        (nr[1], _plan(utdrag, kallare, (niv["källarens golv"], niv["källarens tak"]), nr[1], "Källaren",
                      "Källaren, ventilation", None, f"Plan 1: {nr[0]}; sektionerna: {sekt}.")),
        *[(n, _sektion(utdrag, delar, g, y, n, nr[0], nr[1])) for n, ((g, y), delar) in zip(nr[2:], snitt.items())],
    ]
    pdf = ut / f"{SERIE}.pdf"
    kompilera(bladen, arbete, pdf)
    return pdf


def lista(utdrag: dict, kontroll: tuple[list[str], list[str]], krockar: list[str]) -> str:
    """Grenarna, elementen, kanalerna, genomföringarna, kontrollen och krockarna mot huset som markdown."""
    fel, anm = kontroll
    el, typer = utdrag["element"], utdrag["typer"]
    rad = ["# Ventilationen", "", f"{len(utdrag['grenar'])} grenar (frånluft med egen fläkt), {len(el)} element.", "",
           f"## Kontroll: {len(fel)} fel, {len(anm)} anmärkningar", ""]
    rad += [f"- FEL {f}" for f in fel] + [f"- {a}" for a in anm]
    rad += ["", "## Krockar mot husets delar", ""] + ([f"- {k}" for k in krockar] or ["Inga."])
    rad += ["", "## Grenar", "", "| Gren | Namn | Rum | Flöde [l/s] | Grund [l/s] | Tryckfall [Pa] | Element |",
            "|---|---|---|---|---|---|---|"]
    for g, d in utdrag["grenar"].items():
        rad.append(f"| {g} | {d['namn']} | {d['rum']} | {d['flode']:g} | {d['flode_normal']:g} | "
                   f"{d['tryckfall']:.1f} | "
                   f"{', '.join(d['element'])} |")
    rad += ["", "## Element", "", "| Id | Slag | Produkt | Läge |", "|---|---|---|---|"]
    for k, e in el.items():
        lage = (f"{len(e['vag'])} punkter, {e['langd'] / 1000:.2f} m, {e['bojar']:.0f}°, {e['hastighet']:.1f} m/s"
                if e["slag"] == "kanal" else "(" + ", ".join(f"{c:.0f}" for c in e["punkt"]) + ")")
        rad.append(f"| {k} | {e['slag']} | {typer[e['typ']]['namn']} | {lage} |")
    rad += ["", "## Genomföringar", "", "| Byggdel | Åtgärd | Mått | Kanal | x | y | z |",
            "|---|---|---|---|---|---|---|"]
    for x in utdrag["genomforingar"]:
        p = x["punkt"]
        rad.append(f"| {x['del']} | {x['atgard']} | {x['matt']} | {x['element']} | {p[0]:.0f} | {p[1]:.0f} | "
                   f"{p[2]:.0f} |")
    return "\n".join(rad) + "\n"

