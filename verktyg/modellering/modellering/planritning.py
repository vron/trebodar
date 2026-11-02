"""Gemensamt för ritningarna ur modellen (kameraplanen, elritningarna): snitt ur STEP-filen (verktyg/modellanalys
`ma snitt`) och plan i skala på ett A3-blad.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Polygon  # noqa: E402

BLAD = (420.0, 297.0)                    # A3 liggande, mm
# delarna i snittet: utelämnade (sökvägens början) och fyllningen (första träffen i sökvägen)
UTOM = ("Mark/", "Hus/Armering", "Hus/Grund/Plattan", "Hus/Grund/Fasadsten", "Hus/Installationer", "Hus/Tak")
FYLLNING = (("-GLAS", "#bfe0f2"), ("-BLAD", "#c9ab84"), ("Fönster och dörrar", "#8f7f6c"), ("Hus/Stomme", "#5a5a5a"),
            ("Hus/Grund", "#5a5a5a"), ("Hus/Kamin", "#3c3c3c"), ("Hus/Fasad", "#8c8c8c"), ("Hus/Isolering", "#e3dccb"),
            ("Hus/Invändigt", "#a9a9a9"), ("Hus/Trappa", "#c9a46e"), ("Hus/Mellanbjälklag", "#d9d6cf"))


def snitt(ma: Path, step: Path, z: float, json_ut: Path) -> list[dict]:
    """Delarnas snittytor i planet z (mm) ur STEP-filen (och snittets bild bredvid JSON-filen)."""
    subprocess.run([str(ma), "snitt", f"z={z:g}", "--fil", str(step), "--json", str(json_ut), "--inga-etiketter",
                    "--ut", str(json_ut.with_suffix(".png"))], check=True, capture_output=True)
    return json.loads(json_ut.read_text(encoding="utf-8"))["delar"]


def fyllning(sokvag: str) -> str:
    return next((f for k, f in FYLLNING if k in sokvag), "#b5b5b5")


def plan(fig: plt.Figure, lage_mm: tuple[float, float], omrade: tuple[float, float, float, float],
         delar: list[dict], rubrik: str, skala: float, utom: tuple[str, ...] = UTOM, alfa: float = 1.0,
         bara: tuple[str, ...] = ()) -> plt.Axes:
    """Ett plan i skalan: axlarna med nedre vänstra hörnet i lage_mm på bladet, omrade (x0, x1, y0, y1) i mm, och
    snittets delar (utom de utelämnade, bara de i `bara` om den anges) med alfa (blekare bakgrund)."""
    x0, x1, y0, y1 = omrade
    w, h = (x1 - x0) / skala, (y1 - y0) / skala
    ax = fig.add_axes((lage_mm[0] / BLAD[0], lage_mm[1] / BLAD[1], w / BLAD[0], h / BLAD[1]))
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal")
    ax.axis("off")
    for d in delar:
        if d["sokvag"].startswith(utom) or (bara and not d["sokvag"].startswith(bara)):
            continue
        f = fyllning(d["sokvag"])
        for yta in d["ytor"]:
            ax.add_patch(Polygon(yta[0], closed=True, fc=f, ec="#303030", lw=0.15, alpha=alfa))
    ax.text(x0, y1, rubrik, fontsize=11, weight="bold", va="top")
    return ax
