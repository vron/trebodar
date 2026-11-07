"""Avloppets ritning ur modellen (utdraget ur trebodar.hus.installationer.avlopp.ledningar), i ritningsmallen (A3):
källarens plan med alla ledningarna, grundledningarna under bottenplattan och rören i källarens tak, de lodräta rören
från plan 1 och till tvätthona, golvbrunnarna, stammen med rensningen och luftningen, grundledningen ut mot
förbindelsepunkten med vattengångens höjder (RH 2000), och tabellen över ledningarna. Planen ur modellens snitt genom
källaren (STEP-filen).
"""
from __future__ import annotations

import math
from collections.abc import Callable
from pathlib import Path

import numpy as np
from shapely.geometry import LineString, Point, Polygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from .draneringsritning import Texter
from .planritning import Blad, Vy, blad, figur, kompilera, norrpil, papper, plan, plan_ytor, sv, vy

SERIE = "VS-02 Avlopp"
SKALA = 100.0
PLANEN = (-700.0, 14700.0, -3500.0, 12900.0)     # planens område (x0, x1, y0, y1) [mm]: källaren och utloppet
SZ = 5.6                                          # texternas storlek [pt]
R_LODRATT, R_GB, R_STAM, R_LU = 0.75, 1.3, 1.2, 0.95   # symbolernas radie på papperet [mm]
PIL = "#8a5524"                                   # flödespilarna (ritningsmallens AV)
# avloppspunkterna på plan 1 och i källaren: ledningen vars första punkt är punkten och dess förkortning i planen
PUNKTER = {"AV1": "WC", "AV2": "TS", "AV3": "BK", "AV5": "DB", "AV14": "TH1", "AV16": "TH2", "AV18": "TH3",
           "AV21": "TM"}

Pkt = tuple[float, float]


def vg(u: dict, ld: dict, z: float) -> str:
    """Vattengången (rörets innerbotten: mitten − Ø/2 + godset) i RH 2000."""
    return "+" + sv((z - ld["d"] / 2 + u["gods"][ld["d"]] + u["rh0"]) / 1000, 3)


def _lager(u: dict, z: float, pumpad: bool = False) -> str:
    """Linjens stil efter höjden: under bottenplattan eller i källarens tak; det pumpade avloppet ingjutet i
    mellanbjälklaget tunt."""
    return "av_tunn" if pumpad else "av" if z < u["bottenplattan"] else "av_tak"


# ------------------------------------------------------------------ symboler (pappersmått)

def lodratt(v: Vy, X: float, Y: float) -> None:
    v.cirkel(X, Y, R_LODRATT, fyll="vit", stil="av_tunn")


def golvbrunn(v: Vy, X: float, Y: float) -> None:
    v.cirkel(X, Y, R_GB, fyll="vit", stil="av_tunn")
    k = v.m(R_GB) * math.sqrt(0.5)
    v.linje([(X - k, Y - k), (X + k, Y + k)], "tunn")
    v.linje([(X - k, Y + k), (X + k, Y - k)], "tunn")


def stam(v: Vy, X: float, Y: float) -> None:
    v.cirkel(X, Y, R_STAM, fyll="#8a5524", stil="av_tunn")


def luftning(v: Vy, X: float, Y: float) -> None:
    v.cirkel(X, Y, R_LU, fyll="vit", stil="lu")
    v.cirkel(X, Y, R_LU * 0.35, fyll="#8a5524", stil=None)


def flode(v: Vy, a: Pkt, b: Pkt) -> None:
    """Flödets riktning: en pil mitt på sträckan a–b."""
    t = np.subtract(b, a) / math.dist(a, b)
    m = np.add(a, b) / 2 + t * v.m(0.9)
    v.pil(tuple(m), tuple(t), langd=1.8, bredd=1.1, fyll=PIL)


def _flodestecken(v: Vy) -> None:
    v.linje([(-3.5, 0.0), (3.5, 0.0)], "av")
    flode(v, (-3.5, 0.0), (3.5, 0.0))


TECKEN: list[tuple[Callable[[Vy], None] | dict, str]] = [
    (dict(form="linje", stil="av"), "grundledning Ø110 under bottenplattan"),
    (dict(form="linje", stil="av_tak"), "ledning i källarens tak, under mellanbjälklaget"),
    (dict(form="linje", stil="av_tunn"), "diskmaskinens pumpade avlopp, ingjutet i mellanbjälklaget"),
    (lambda w: _flodestecken(w), "flödets riktning"),
    (lambda w: lodratt(w, 0.0, 0.0), "lodrätt rör (från plan 1 eller tvätthoets anslutning)"),
    (lambda w: golvbrunn(w, 0.0, 0.0), "golvbrunn"),
    (lambda w: stam(w, 0.0, 0.0), "stammen Ø110 i KL8"),
    (lambda w: luftning(w, 0.0, 0.0), "luftningen upp i L11 och ut genom taket"),
]


def _teckenforklaring() -> dict:
    return dict(typ="symboler", rader=[{**s, "text": t} if isinstance(s, dict) else {**figur(s), "text": t}
                                       for s, t in TECKEN])


def _stycken(vag: list) -> list[tuple[list[Pkt], float]]:
    """Ledningens vågräta stycken i plan, i följd: punkterna och höjden där stycket börjar."""
    ut: list[tuple[list[Pkt], float]] = []
    for a, b in zip(vag, vag[1:]):
        if math.dist(a[:2], b[:2]) < 1.0:
            continue
        if ut and math.dist(ut[-1][0][-1], a[:2]) < 1.0 and _samma(ut[-1][1], a[2], b[2]):
            ut[-1][0].append((b[0], b[1]))
        else:
            ut.append(([(a[0], a[1]), (b[0], b[1])], a[2]))
    return ut


def _samma(z0: float, za: float, zb: float) -> bool:
    return (z0 < -2000.0) == (za < -2000.0) == (zb < -2000.0)


# ------------------------------------------------------------------ planen

def _plan(u: dict, delar: list[dict], norr: tuple[float, float]) -> Vy:
    v = vy(SKALA, PLANEN, 24.0, 22.0)
    plan(v, delar)
    vaggar = unary_union([g for g, _, _ in plan_ytor(delar)])
    led = u["ledningar"]
    linjer: list[BaseGeometry] = []
    with v.lager("ledningar"):
        for lid, ld in led.items():
            if lid.startswith("LU"):
                continue
            for pkt, z in _stycken(ld["vag"]):
                v.linje(pkt, _lager(u, z, ld.get("pumpad", False)))
                linjer.append(LineString(pkt).buffer(v.m(0.5)))
                for a, b in zip(pkt, pkt[1:]):
                    if math.dist(a, b) / v.s > 12.0:
                        flode(v, a, b)
        ut = led["AV8"]["vag"]
        v.pil(tuple(ut[-1][:2]), tuple(np.subtract(ut[-1][:2], ut[-2][:2])), langd=2.6, bredd=1.6, fyll=PIL)
    x0, y1 = papper(v, 22.0, 20.0)
    x1, y0 = papper(v, 232.0, 270.0)
    symboler: list[BaseGeometry] = []
    with v.lager("symboler"):
        for lid, kort in PUNKTER.items():
            p = led[lid]["vag"][0]
            lodratt(v, p[0], p[1])
            symboler.append(Point(p[:2]).buffer(v.m(R_LODRATT + 0.3)))
        for gid, gb in u["golvbrunnar"].items():
            golvbrunn(v, *gb["punkt"])
            symboler.append(Point(gb["punkt"]).buffer(v.m(R_GB + 0.3)))
        sx, sy = u["stam"]["punkt"]
        stam(v, sx, sy)
        lx, ly = u["luftning"]["punkt"]
        luftning(v, lx, ly + v.m(2.2))
        v.linje([(lx, ly), (lx, ly + v.m(2.2) - v.m(R_LU))], "lu")
        dx, dy = u["diskmaskin"]
        v.polygon([(dx - v.m(0.8), dy - v.m(0.8)), (dx + v.m(0.8), dy - v.m(0.8)), (dx + v.m(0.8), dy + v.m(0.8)),
                   (dx - v.m(0.8), dy + v.m(0.8))], "vit", "av_tunn")
        symboler += [Point(sx, sy).buffer(v.m(R_STAM + 0.3)), Point(lx, ly + v.m(2.2)).buffer(v.m(R_LU + 0.3)),
                     Point(dx, dy).buffer(v.m(1.2))]
    texter = Texter(v, [vaggar.buffer(-v.m(0.3)), *linjer, *symboler], [],
                    Polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)]))
    hus = vaggar.convex_hull

    def bort(p: Pkt) -> Pkt:
        """Riktningen från husets mitt ut genom punkten."""
        c = hus.centroid
        d = np.subtract(p, (c.x, c.y))
        return tuple(d / max(float(np.hypot(*d)), 1e-9))   # type: ignore[return-value]

    with v.lager("texter"):
        for lid, kort in PUNKTER.items():
            p = tuple(led[lid]["vag"][0][:2])
            texter.satt(p, bort(p), [(f"{kort} {lid} Ø{led[lid]['d']:g}", "av")], sz=5.4)       # type: ignore[arg-type]
        for gid, gb in u["golvbrunnar"].items():
            p = tuple(gb["punkt"])
            namn = "GB (duschen, plan 1)" if gid == "GB" else gid
            texter.satt(p, bort(p), [(namn, "av")], sz=5.4)                                     # type: ignore[arg-type]
        texter.satt((lx, ly + v.m(2.2)), (-0.5, 1.0), [("AV7 stam Ø110 i KL8, rensning mot teknikrummet;", "av"),
                                                       ("LU luftning Ø50 i L11, Ø75 ut genom taket", "av"),
                                                       ("(se sektionen)", "gra")], sz=5.4, fran=(sx, sy))
        texter.satt((dx, dy), (-1.0, 0.3), [("DM diskmaskinen i ön, AV20 pumpat:", "av"),
                                            ("PEX 25 ingjutet till diskhons vattenlås", "av")], sz=5.4)
        # grundledningens höjder: där den börjar (vid GB1), vid GB2, där den går ut under V9 och där ritningen slutar
        gl = led["AV8"]
        pkt = gl["vag"]
        for i, q in ((0, "vid GB1"), (1, "vid GB2"), (2, "ut under V9")):
            p = (pkt[i][0], pkt[i][1])
            texter.satt(p, bort(p), [(f"AV8 {q}, VG {vg(u, gl, pkt[i][2])}", "av")], sz=5.4)
        e = pkt[-1]
        texter.satt(tuple(e[:2]), (1.0, -0.3), [
            ("AV8 mot förbindelsepunkten (fortsätter)", "av"), ("åt nordost, marken där ca +4,5", "av"),
            (f"VG {vg(u, gl, e[2])} där ritningen slutar", "av")], sz=6.0, langder=(2.0, 4.0, 6.0))
        # grenarnas nummer vid grenen
        for lid, ld in led.items():
            if lid.startswith("LU") or lid in ("AV8",):
                continue
            st = _stycken(ld["vag"])
            if not st:
                continue
            a, b = st[-1][0][-2], st[-1][0][-1]
            m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            t = np.subtract(b, a) / max(math.dist(a, b), 1e-9)
            texter.satt(m, (-t[1], t[0]), [(f"{lid} Ø{ld['d']:g}", "av")], sz=5.2,
                        langder=(1.5, 3.0, 4.5, 6.5))
    norrpil(v, 14300.0, 6500.0, norr)
    v.rubrik(*papper(v, 24.0, 20.0), "Källaren, avloppet under bottenplattan och i källarens tak", round(v.s))
    with v.lager("skalstock"):
        v.skalstock(*papper(v, 24.0, 22.0 + (PLANEN[3] - PLANEN[2]) / v.s + 6.0), langd_m=5, steg_m=1)
    return v


def _sektion(u: dict) -> Vy:
    """Stammen och luftningen i en schematisk sektion: från böjen till grundledningen upp genom bottenplattan, källaren,
    mellanbjälklaget, L11 och taket till luftningshuven, med höjderna (RH 2000)."""
    led = u["ledningar"]
    st, lu1, lu2 = led["AV7"]["vag"], led["LU1"]["vag"], led["LU2"]["vag"]
    z_botten, z_tak = st[1][2] - 400.0, lu2[-1][2] + u["luftning"]["huv"][1] + 300.0
    v = vy(SKALA, (-1500.0, 3000.0, z_botten, z_tak), 24.0, 212.0)
    rh0 = u["rh0"]

    def niva(z: float, text: str, stil: str = "fin") -> None:
        v.linje([(-1400.0, z), (1400.0, z)], stil)
        v.text(1500.0, z, f"{text} +{sv((z + rh0) / 1000, 3)}", a="lm", sz=5.4, col="gra")
    with v.lager("nivåer"):
        niva(lu2[-1][2], "takets yta")
        niva(u["luftning"]["okning"], "innertaket, ångbromsen (Ø50 → Ø75)")
        v.linje([(-1400.0, 0.0), (1400.0, 0.0)], "fin")
        v.linje([(-1400.0, u["kallartak"]), (1400.0, u["kallartak"])], "fin")
        v.text(1500.0, 0.0, f"plan 1 golv +{sv(rh0 / 1000, 3)}, källarens tak "
               f"+{sv((u['kallartak'] + rh0) / 1000, 3)}", a="lm", sz=5.4, col="gra")
        niva(u["bottenplattan"], "källargolvet")
        niva(u["bottenplattan"] - 400.0, "bottenplattans cellplast, underkant", "dold")
    with v.lager("rör"):
        v.linje([(0.0, st[1][2]), (0.0, st[0][2])], "av")
        v.linje([(0.0, st[1][2]), (1200.0, st[1][2] - 12.0)], "av")
        v.linje([(0.0, lu1[0][2]), (0.0, lu1[-1][2])], "av_tunn")
        huv = lu2[-1][2] + u["luftning"]["huv"][1]                     # huvens överkant
        v.linje([(0.0, lu2[0][2]), (0.0, huv - 60.0)], "lu")
        v.polygon([(-80.0, huv - 60.0), (80.0, huv - 60.0), (80.0, huv - 10.0), (-80.0, huv - 10.0)], "vit", "av_tunn")
        a1 = led["AV1"]["vag"][-1]
        v.linje([(1200.0, a1[2] + 12.0), (55.0, a1[2])], "av_tak")
        rz = u["stam"]["rensning"]
        v.linje([(0.0, rz), (180.0, rz)], "av")
    with v.lager("texter"):
        v.ptext(1200.0, a1[2], 0.8, 0.0, "AV1 från badrummet", a="lm", sz=5.4, col="av")
        v.ptext(180.0, rz, 0.8, 0.0, "rensning", a="lm", sz=5.4, col="av")
        v.ptext(1200.0, st[1][2], 0.0, -0.8, "till grundledningen AV8", a="rt", sz=5.4, col="av")
        v.ptext(0.0, (st[0][2] + st[1][2]) / 2, -0.8, 0.0, "AV7 Ø110 i KL8", a="rm", sz=5.4, col="av")
        v.ptext(0.0, (lu1[0][2] + lu1[-1][2]) / 2, -0.8, 0.0, "LU1 Ø50 i L11", a="rm", sz=5.4, col="av")
        v.ptext(80.0, lu2[-1][2] + u["luftning"]["huv"][1] - 35.0, 0.8, 0.0, "luftningshuv; LU2 Ø75 isolerad genom "
                "takets isolering", a="lm", sz=5.4, col="av")
    v.rubrik(*papper(v, 24.0, 205.0), "Stammen och luftningen, sektion (schematisk)", round(v.s))
    return v


def _blad(u: dict, delar: list[dict], norr: tuple[float, float]) -> Blad:
    led = u["ledningar"]

    def langd(vag: list) -> float:
        return sum(math.dist(a, b) for a, b in zip(vag, vag[1:])) / 1000

    rader = []
    for k, ld in led.items():
        vgg = ld["vattengang"]
        st = [(a, b) for a, b in zip(ld["vag"], ld["vag"][1:]) if math.dist(a[:2], b[:2]) >= 1.0]
        fall = sv(1000 * (st[0][0][2] - st[0][1][2]) / math.dist(st[0][0][:2], st[0][1][:2]), 0) if st else "lodrätt"
        if ld.get("pumpad"):
            fall = "pumpat"
        rader.append([k, ld["namn"].replace(", grenen under bottenplattan", ", grenen").replace(", rakt ned", ""),
                      f"{ld['d']:g}", sv(langd(ld["vag"]), 1), fall,
                      vg(u, ld, vgg[0] + ld["d"] / 2) if vgg else "–", vg(u, ld, vgg[1] + ld["d"] / 2) if vgg else "–"])
    lu = u["luftning"]
    kol: list[dict] = [
        dict(typ="rubrik", text="Anvisningar"),
        dict(typ="lista", sz=6.4, rader=[
            "Allt avlopp går med självfall till den kommunala förbindelsepunkten, som ligger längre ned åt nordost "
            "längs vattenledningen, med marken på cirka +4,5. Rör av PP för avlopp i byggnad; under bottenplattan "
            "markavloppsrör Ø110.",
            f"Fall: Ø110 minst 10 ‰, klenare minst 17 ‰ (tillverkarnas anvisningar), lagt 10 ‰ respektive 20 ‰. "
            "Grundledningarna ligger under bottenplattans cellplast, grenarna vinkelrätt mot grundledningen och "
            "anslutna med 45° grenrör. Direkt utanför källarväggen V9 faller grundledningen brant (två böjar 45°) "
            "under dräneringen runt grunden.",
            "Stammen Ø110 står i källarväggen KL8, med rensning 0,5 m över golvet (lock genom gipsen mot "
            "teknikrummet). Badrummets ledningar hänger i källarens tak till stammen; köket går rakt ned längs "
            "källarväggen V14.",
            f"Luftningen går rakt upp från stammen i KL8 och badrummets vägg L11, Ø{lu['d'][0]:g} i väggen och "
            f"Ø{lu['d'][1]:g} isolerad från innertaket ut genom taket till en luftningshuv av plåt; syll och "
            "hammarband urtas. Hålen i mellanbjälklaget för luftningen och duschens golvbrunn ligger inom rörets P4 "
            "genomstansningszon (K-05).",
            "Golvbrunnarna i källaren gjuts in i bottenplattan med flänsen i dess överkant; tvättmaskinen töms i GB1. "
            "Tvätthona TH1–TH3 får var sin anslutning Ø50 i golvet framför väggdosan.",
            "Diskmaskinen i köksön har pumpat avlopp (AV20): maskinens egen pump trycker vattnet genom ett rör PEX 25 "
            "utan fall, ingjutet i mellanbjälklaget på tappvattnets nivå, från anslutningen i golvet under maskinen "
            "till diskbänksskåpet bakom lådorna och upp till diskhons vattenlås (anslutning för diskmaskin, med en ögla "
            f"under bänkskivan). Diskmaskinen ska tillåta minst {sv(u['dm_slang'], 0)} m avloppsslang.",
            "Tvätten i badrummets skåp (förberedd för tvättmaskin och torktumlare): vattenlåset på väggen L10, Ø50 "
            "ned i väggen och genom bjälklaget (AV21) till samlingsledningen, under KL2:s hammarband genom väggen.",
            f"Höjderna: vattengången (VG, rörets innerbotten) i RH 2000; plan 1 ±0 = +{sv(u['rh0'] / 1000, 3)}, "
            f"källargolvet +{sv((u['bottenplattan'] + u['rh0']) / 1000, 3)}.",
            "Produkterna är inte valda (allmänna typer med vanliga mått). Ritningen ritas med ./mod avlopp ritning.",
        ]),
        dict(typ="rubrik", text="Teckenförklaring"),
        _teckenforklaring(),
        dict(typ="rubrik", text="Ledningar"),
        dict(typ="tabell", kolumner=["Id", "Vad", "Ø", "Längd (m)", "Fall ‰", "VG början", "VG slut"],
             bredd=(0.42, 1.5, 0.32, 0.5, 0.48, 0.66, 0.66), just=["l", "l", "r", "r", "r", "r", "r"], sz=5.6,
             rader=rader),
    ]
    nr = f"{SERIE.split()[0]}.1"
    return blad(nr, ["Avlopp", "Källaren och grundledningarna"], f"1:{SKALA:g}", "Modellen", kol,
                [_plan(u, delar, norr), _sektion(u)])


def ritningar(utdrag: dict, kallaren: list[dict], norr: tuple[float, float], arbete: Path, ut: Path) -> Path:
    """Avloppets ritning (serien SERIE) som pdf i mappen ut (bladet för sig i arbetsmappen, under repots rot)."""
    nr = f"{SERIE.split()[0]}.1"
    pdf = ut / f"{SERIE}.pdf"
    kompilera([(nr, _blad(utdrag, kallaren, norr))], arbete, pdf)
    return pdf
