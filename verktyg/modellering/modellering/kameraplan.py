"""Kameraplanen: inomhusbildernas kameror (trebodar.vyer.INNE) på planer ur modellens snitt, plan 1 och källaren
(STEP-filen, verktyg/modellanalys `ma snitt`), med läge, riktning, bildvinkel och nummer, rummens namn och
förteckningen över bilderna. Ett blad i ritningsmallen (A3), plan 1 i 1:75 och källaren i 1:150.
"""
from __future__ import annotations

import math
from collections import Counter
from collections.abc import Callable
from pathlib import Path

from .planritning import Vy, blad, figur, kompilera, norrpil, papper, plan, snitt, sv, vy

SKALA, SKALA_K = 75.0, 150.0      # plan 1, källaren (bara två bilder)
NUMMER = "I-01"
PLAN1 = (-500.0, 14300.0, -300.0, 16300.0)       # planernas områden (x0, x1, y0, y1) [mm]
KALLARE = (-200.0, 14000.0, -100.0, 12800.0)
# objektivens färger: linjen (ritningsmallens stil och textfärg), kameran och bildvinkelns kil (genomskinlig)
OBJEKTIV = {"öga": ("uk", "#2c4a6e", "#2c4a6e26"), "vid": ("ok", "#b5463a", "#b5463a26")}
# vynamnens ord (ASCII i filnamnen) i förteckningen
ORD = {"kok": "köket", "fran": "från", "oversikt": "översikt", "fonster": "fönstret", "golvfonster": "golvfönstret",
       "altandorr": "altandörren", "dorr": "dörren", "tradgard": "trädgården", "entre": "entrén", "hall": "hallen",
       "kamin": "kaminen", "allrum": "allrummet", "uteplats": "uteplatsen", "sovrum": "sovrummet",
       "trappan": "trappan", "ned": "ned"}

__all__ = ["rita", "snitt"]


def _kil(v: Vy, x: float, y: float, rikt: float, fov: float, r: float, objektiv: str) -> None:
    """Kameran: bildvinkelns kil, riktningen och kamerans punkt (r i modellens mm)."""
    stil, punkt, kil = OBJEKTIV[objektiv]
    n = 16
    bage = [(x + r * math.cos(rikt + fov * (i / n - 0.5)), y + r * math.sin(rikt + fov * (i / n - 0.5)))
            for i in range(n + 1)]
    v.polygon([(x, y), *bage], kil, stil + "_tunn")
    v.linje([(x, y), (x + r * math.cos(rikt), y + r * math.sin(rikt))], stil + "_tunn")
    v.cirkel(x, y, 0.65, fyll=punkt, stil=None)


def _etikett(v: Vy, x: float, y: float, rikt: float, upptagna: list[tuple[float, float]],
             kameror: list[tuple[float, float]]) -> tuple[float, float]:
    """Etikettens läge: bakom kameran om det är ledigt, annars snett bakom eller vid sidan."""
    for dv in (0, 45, -45, 90, -90, 135, -135):
        for r in (v.m(3.6), v.m(5.0)):
            a = rikt + math.pi + math.radians(dv)
            ex, ey = x + r * math.cos(a), y + r * math.sin(a)
            if all(math.dist((ex, ey), e) > v.m(5.0) for e in upptagna) and \
                    all(math.dist((ex, ey), k) > v.m(2.6) for k in kameror):
                return ex, ey
    return x - v.m(3.6) * math.cos(rikt), y - v.m(3.6) * math.sin(rikt)


def _fov(lins: float) -> float:
    """Bildvinkeln vågrätt för en fullformatssensor (36 mm bred) [rad]."""
    return 2 * math.atan(18.0 / lins)


def rita(plan1: list[dict], kallare: list[dict], vyer: dict[str, dict], rum: dict[str, tuple],
         trapphal: list[tuple[float, float]], norr: tuple[float, float], ut: Path, mapp: Path) -> list[Path]:
    """Kameraplanen som pdf (ut); bladets JSON och pdf i mappen."""
    v1 = vy(SKALA, PLAN1, 24.0, 27.0)
    vk = vy(SKALA_K, KALLARE, 24.0 + (PLAN1[1] - PLAN1[0]) / SKALA + 5.0, 27.0)
    plan(v1, plan1)
    plan(vk, kallare)
    with v1.lager("trappa"):
        v1.polygon(trapphal, None, "dold")
        xs, ys = zip(*trapphal)
        ym = (min(ys) + max(ys)) / 2 - v1.m(2.4)
        v1.linje([(max(xs) - v1.m(2.5), ym), (min(xs) + v1.m(5.5), ym)], "tunn")
        v1.pil((min(xs) + v1.m(3.0), ym), (-1, 0), langd=2.2, bredd=1.2)
        v1.text(min(xs) + v1.m(4.5), ym + v1.m(0.6), "ned", a="lb", sz=6.2, col="gra")
    for v in (v1, vk):
        with v.lager("rum"):
            for namn, lage in rum.values():
                if (len(lage) > 2 and lage[2] == "k") == (v is vk):
                    v.text(lage[0], lage[1], namn, a="cm", sz=8, i=True, col="gra")
    kameror = {namn: (k["kamera"][0], k["kamera"][1]) for namn, k in vyer.items()}
    etiketter: list[tuple[float, float]] = []
    for namn, k in vyer.items():
        nr = namn.split("-")[0]
        (x, y, z), (tx, ty, _) = k["kamera"], k["mal"]
        v = vk if z < 0 else v1
        rikt = math.atan2(ty - y, tx - x)
        with v.lager("kameror"):
            _kil(v, x, y, rikt, _fov(float(k["lins"])), 1500.0 if k["objektiv"] == "öga" else 1150.0,
                 str(k["objektiv"]))
        ex, ey = _etikett(v, x, y, rikt, etiketter, [q for n, q in kameror.items() if n != namn])
        etiketter.append((ex, ey))
        with v.lager("nummer"):
            v.text(ex, ey, nr, a="cm", sz=7, b=True, col=OBJEKTIV[str(k["objektiv"])][0], bg=True)
    norrpil(v1, 7300.0, 14600.0, norr)
    for v, omr, rubrik in ((v1, PLAN1, "Plan 1"), (vk, KALLARE, "Källaren")):
        v.rubrik(*papper(v, (omr[0] - v.X0) / v.s, 21.0), f"{rubrik}, snitt 1,2 m över golvet", round(v.s))
    with v1.lager("skalstock"):
        v1.skalstock(*papper(v1, 24.0, 27.0 + (PLAN1[3] - PLAN1[2]) / SKALA + 8.0), langd_m=5, steg_m=1)
    # objektiven: brännvidd, bildvinkel och kamerans vanligaste höjd på plan 1
    objektiv = {}
    for obj in OBJEKTIV:
        ks = [k for k in vyer.values() if k["objektiv"] == obj]
        hojd = Counter(round(k["kamera"][2]) for k in ks if k["kamera"][2] > 0).most_common(1)[0][0]
        objektiv[obj] = (float(ks[0]["lins"]), math.degrees(_fov(float(ks[0]["lins"]))), hojd)
    rader = []
    for namn, k in vyer.items():
        nr, vynamn = namn.split("-", 1)
        rumnyckel = str(k["rum"])
        ord_ = vynamn[len(rumnyckel) + 1:].split("-")[:-1]          # vyns ord utan rummet och objektivet
        rader.append([nr, rum[rumnyckel][0], " ".join(ORD.get(o, o) for o in ord_), str(k["objektiv"])])

    def legend(obj: str) -> Callable[[Vy], None]:
        return lambda v: _kil(v, -2.6, 0.0, 0.0, math.radians(objektiv[obj][1]), 2.9, obj)

    kol: list[dict] = [
        dict(typ="rubrik", text="Anvisningar"),
        dict(typ="lista", sz=7.0, rader=[
            "Inomhusbildernas kameror: läge, riktning och bildvinkel (vågrätt). Kameran är vågrät och lodräta linjer "
            "blir lodräta i bilderna, utom I28 (trappan, kameran lutad nedåt).",
            "Kamerorna och vyerna står i modellens vyer.py (INNE). Bilderna renderas i 4K med renderingar/rendera.sh "
            "(./mod rendera) och versionshanteras inte.",
            "Planerna är snitt ur modellen (STEP-filen) 1,2 m över golvet; ritningen ritas med ./mod kameraplan.",
        ]),
        dict(typ="rubrik", text="Teckenförklaring"),
        dict(typ="symboler", rader=[
            {**figur(legend(obj)), "text": f"{obj}: {sv(objektiv[obj][0])} mm, bildvinkel {sv(objektiv[obj][1])}°, "
                                           f"kameran {sv(objektiv[obj][2] / 1000, 2)} m över golvet"}
            for obj in OBJEKTIV] + [
            dict(form="linje", stil="dold", text="trapphålet"),
        ]),
        dict(typ="rubrik", text="Bilderna, renderingar/inne/<namn>.png"),
        dict(typ="tabell", kolumner=["Bild", "Rum", "Vy", "Objektiv"], bredd=(0.5, 1.15, 1.6, 0.6),
             just=["l", "l", "l", "l"], sz=6.4, rader=rader),
    ]
    b = blad(NUMMER, ["Inomhusbilder I01–I30", "Kameraplan"], f"1:{SKALA:g}, 1:{SKALA_K:g}", "Modellen", kol,
             [v1, vk])
    return kompilera([(NUMMER, b)], mapp, ut)
