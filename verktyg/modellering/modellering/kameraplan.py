"""Kameraplanen: inomhusbildernas kameror (trebodar.vyer.INNE) på planritningar ur modellens snitt, plan 1 och
källaren (STEP-filen, med verktyg/modellanalys `ma snitt`), med läge, bildvinkel och nummer, rummens namn och en
förteckning över bilderna. A3, skala 1:75.
"""
from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrow, Polygon, Wedge  # noqa: E402

SKALA = 75.0
BLAD = (420.0, 297.0)                    # A3 liggande, mm
# delarna i snittet: utelämnade (sökvägens början) och fyllningen (första träffen i sökvägen)
UTOM = ("Mark/", "Hus/Armering", "Hus/Grund/Plattan", "Hus/Grund/Fasadsten", "Hus/Installationer", "Hus/Tak")
FYLLNING = (("-GLAS", "#bfe0f2"), ("-BLAD", "#c9ab84"), ("Fönster och dörrar", "#8f7f6c"), ("Hus/Stomme", "#5a5a5a"),
            ("Hus/Grund", "#5a5a5a"), ("Hus/Kamin", "#3c3c3c"), ("Hus/Fasad", "#8c8c8c"), ("Hus/Isolering", "#e3dccb"),
            ("Hus/Invändigt", "#a9a9a9"), ("Hus/Trappa", "#c9a46e"))
OBJEKTIVFARG = {"öga": "#1f66b0", "vid": "#cf4a24"}
# vynamnens ord (ASCII i filnamnen) i förteckningen
ORD = {"kok": "köket", "fran": "från", "oversikt": "översikt", "fonster": "fönstret", "golvfonster": "golvfönstret",
       "altandorr": "altandörren", "dorr": "dörren", "tradgard": "trädgården", "entre": "entrén", "hall": "hallen",
       "kamin": "kaminen", "allrum": "allrummet", "uteplats": "uteplatsen", "sovrum": "sovrummet",
       "trappan": "trappan", "ned": "ned"}


def snitt(ma: Path, step: Path, z: float, json_ut: Path) -> list[dict]:
    """Delarnas snittytor i planet z (mm) ur STEP-filen (och snittets bild bredvid JSON-filen)."""
    subprocess.run([str(ma), "snitt", f"z={z:g}", "--fil", str(step), "--json", str(json_ut), "--inga-etiketter",
                    "--ut", str(json_ut.with_suffix(".png"))], check=True, capture_output=True)
    return json.loads(json_ut.read_text(encoding="utf-8"))["delar"]


def _fyllning(sokvag: str) -> str:
    return next((f for k, f in FYLLNING if k in sokvag), "#b5b5b5")


def _plan(fig: plt.Figure, lage_mm: tuple[float, float], omrade: tuple[float, float, float, float],
          delar: list[dict], rubrik: str) -> plt.Axes:
    """Ett plan i skalan: axlarna med nedre vänstra hörnet i lage_mm på bladet, omrade (x0, x1, y0, y1) i mm."""
    x0, x1, y0, y1 = omrade
    w, h = (x1 - x0) / SKALA, (y1 - y0) / SKALA
    ax = fig.add_axes((lage_mm[0] / BLAD[0], lage_mm[1] / BLAD[1], w / BLAD[0], h / BLAD[1]))
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal")
    ax.axis("off")
    for d in delar:
        if d["sokvag"].startswith(UTOM):
            continue
        f = _fyllning(d["sokvag"])
        for yta in d["ytor"]:
            ax.add_patch(Polygon(yta[0], closed=True, fc=f, ec="#303030", lw=0.15))
    ax.text(x0, y1, rubrik, fontsize=11, weight="bold", va="top")
    return ax


def _etikett(x: float, y: float, rikt: float, upptagna: list[tuple[float, float]],
             kameror: list[tuple[float, float]]) -> tuple[float, float]:
    """Etikettens läge: bakom kameran om det är ledigt, annars snett bakom eller vid sidan (mm i planet)."""
    for dv in (0, 45, -45, 90, -90, 135, -135):
        for r in (360.0, 520.0):
            v = rikt + math.pi + math.radians(dv)
            ex, ey = x + r * math.cos(v), y + r * math.sin(v)
            if all(math.dist((ex, ey), e) > 480 for e in upptagna) and all(math.dist((ex, ey), k) > 260
                                                                          for k in kameror):
                return ex, ey
    return x - 360 * math.cos(rikt), y - 360 * math.sin(rikt)


def rita(plan1: list[dict], kallare: list[dict], vyer: dict[str, dict], rum: dict[str, tuple],
         trapphal: list[tuple[float, float]], norr: tuple[float, float], titel: str, ut: Path) -> None:
    fig = plt.figure(figsize=(BLAD[0] / 25.4, BLAD[1] / 25.4))
    a1 = _plan(fig, (8.0, 14.0), (-500.0, 14300.0, -300.0, 16300.0), plan1, "Plan 1 (snitt 1,2 m över golvet)")
    ak = _plan(fig, (218.0, 104.0), (0.0, 14000.0, 0.0, 12800.0), kallare, "Källaren (snitt 1,2 m över golvet)")
    xs, ys = zip(*trapphal)
    a1.add_patch(Polygon(trapphal, closed=True, fc="none", ec="#555555", lw=0.6, ls=(0, (4, 3))))
    a1.add_patch(FancyArrow(max(xs) - 250, (min(ys) + max(ys)) / 2 - 230, -(max(xs) - min(xs) - 700), 0.0, width=12,
                            head_width=160, head_length=220, color="#555555", lw=0))
    a1.text(min(xs) + 380, (min(ys) + max(ys)) / 2 - 230, "ned", fontsize=6, color="#555555", va="center")
    for namn, lage in rum.values():
        ax = ak if len(lage) > 2 and lage[2] == "k" else a1
        ax.text(lage[0], lage[1], namn, fontsize=8.5, style="italic", color="#6b6b6b", ha="center", va="center")
    kameror = {namn: (v["kamera"][0], v["kamera"][1]) for namn, v in vyer.items()}
    etiketter: list[tuple[float, float]] = []
    for namn, v in vyer.items():
        nr = namn.split("-")[0]
        (x, y, z), (tx, ty, _) = v["kamera"], v["mal"]
        ax = ak if z < 0 else a1
        farg = OBJEKTIVFARG[str(v["objektiv"])]
        fov = 2 * math.degrees(math.atan(18.0 / float(v["lins"])))
        rikt = math.atan2(ty - y, tx - x)
        r = 1500.0 if v["objektiv"] == "öga" else 1150.0
        c, s = math.cos(rikt), math.sin(rikt)
        ax.add_patch(Wedge((x, y), r, math.degrees(rikt) - fov / 2, math.degrees(rikt) + fov / 2, fc=farg, alpha=0.16,
                           ec=farg, lw=0.5))
        ax.plot([x, x + r * c], [y, y + r * s], color=farg, lw=0.7)
        ax.plot(x, y, "o", ms=3.6, color=farg, mec="white", mew=0.6)
        ex, ey = _etikett(x, y, rikt, etiketter, [k for n, k in kameror.items() if n != namn])
        etiketter.append((ex, ey))
        ax.text(ex, ey, nr, fontsize=7, weight="bold", color=farg, ha="center", va="center",
                bbox={"boxstyle": "round,pad=0.12", "fc": "white", "ec": "none", "alpha": 0.85})
    # norrpilen
    nx, ny = norr
    px, py = 7300.0, 14600.0
    a1.add_patch(FancyArrow(px - 500 * nx, py - 500 * ny, 1000 * nx, 1000 * ny, width=40, head_width=260,
                            head_length=320, color="#222222", lw=0, length_includes_head=True))
    a1.text(px + 820 * nx, py + 820 * ny, "N", fontsize=10, weight="bold", ha="center", va="center")
    # rubrik, teckenförklaring och förteckning
    fig.text(10 / BLAD[0], 287 / BLAD[1], titel, fontsize=15, weight="bold", va="top")
    fig.text(10 / BLAD[0], 278 / BLAD[1], "Inomhusbildernas kameror: läge, riktning och bildvinkel. Kameran vågrät, "
             "lodräta linjer lodräta (utom I28).", fontsize=8.5, va="top", color="#333333")
    for i, (obj, text) in enumerate((("öga", "öga: 40 mm (bildvinkel 48°), ögonhöjd 1,60 m"),
                                     ("vid", "vid: 20 mm (bildvinkel 84°), 1,45 m över golvet"))):
        fig.text(14 / BLAD[0], (270 - 5 * i) / BLAD[1], "●", color=OBJEKTIVFARG[obj], fontsize=9, va="top")
        fig.text(19 / BLAD[0], (270 - 5 * i) / BLAD[1], text, fontsize=8.5, va="top")
    fig.text(8 / BLAD[0], 6 / BLAD[1], f"Skala 1:{SKALA:g} (A3). Ur modellen (modeller/trebodar) med `./mod "
             "kameraplan`; bilderna med renderingar/rendera.sh.", fontsize=7.5, color="#555555")
    rader = []
    for namn, v in vyer.items():
        nr, vy = namn.split("-", 1)
        rumnyckel = str(v["rum"])
        ord_ = vy[len(rumnyckel) + 1:].split("-")[:-1]          # vyns ord utan rummet och objektivet
        rader.append((nr, rum[rumnyckel][0], " ".join(ORD.get(o, o) for o in ord_), str(v["objektiv"])))
    fig.text(218 / BLAD[0], 97 / BLAD[1], "Bilderna (renderingar/inne/<namn>.png)", fontsize=9, weight="bold",
             va="top")
    per = math.ceil(len(rader) / 2)
    for i, (nr, rumnamn, vy, obj) in enumerate(rader):
        kol, rad = divmod(i, per)
        x, y = (218 + 98 * kol) / BLAD[0], (90 - 5.2 * rad) / BLAD[1]
        fig.text(x, y, nr, fontsize=7.5, weight="bold", color=OBJEKTIVFARG[obj], va="top")
        fig.text(x + 9 / BLAD[0], y, f"{rumnamn}, {vy} ({obj})", fontsize=7.5, va="top")
    ut.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ut, dpi=200)
    plt.close(fig)
