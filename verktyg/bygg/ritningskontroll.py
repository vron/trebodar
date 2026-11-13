"""Kontroll av de byggda ritningarna: ingen text får ligga utanför eller över bladets ram (en tabell som har vuxit ur
bladet). Körs sist i ./bygg med pymupdf:

    uv run --no-project --with pymupdf python ritningskontroll.py ritningar/

Skriver bladen med text nedanför eller över ramens nederkant (fel, stoppar bygget) och text över ramens sidor
(anmärkning). Bladets fotrad under ramen och ritningsnumret i namnrutan hör till mallen och räknas inte.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pymupdf

UTAN_KALLA = ("200 ", "201 ")          # bygglovsritningarna: färdiga pdf:er utan mall
TOL = 1.0                              # pt


def _kandidater(sida: pymupdf.Page) -> list[tuple[float, float, float, float]]:
    return [tuple(round(v) for v in d["rect"]) for d in sida.get_drawings()
            if d["rect"].width > 0.8 * sida.rect.width and d["rect"].height > 0.8 * sida.rect.height]


def ramen(d: pymupdf.Document) -> pymupdf.Rect | None:
    """Bladens ram: den ritade rektangeln som täcker nästan hela sidan och finns på flest blad (mallens ram; ett blad
    kan ha andra stora rektanglar, t.ex. en vys klippning)."""
    antal: dict[tuple[float, float, float, float], int] = {}
    for sida in d:
        for r in set(_kandidater(sida)):
            antal[r] = antal.get(r, 0) + 1
    if not antal:
        return None
    flest = max(antal.values())
    return pymupdf.Rect(min((r for r, n in antal.items() if n == flest), key=lambda r: (r[2] - r[0]) * (r[3] - r[1])))


def kontroll(mapp: Path) -> tuple[list[str], list[str]]:
    fel, anm = [], []
    for pdf in sorted(mapp.glob("*.pdf")):
        if pdf.name.startswith(UTAN_KALLA):
            continue
        nr = pdf.name.split(" ")[0]
        with pymupdf.open(pdf) as d:
            R = ramen(d)
            if R is None:
                continue
            for i, sida in enumerate(d, 1):
                ordn = sida.get_text("words")
                # mallens egna rader: de som innehåller bladets nummer (fotraden och namnrutan)
                egna = {round(o[1]) for o in ordn if re.fullmatch(rf"{re.escape(nr)}\.\d+", o[4].replace("⁠", ""))}
                ovriga = [o for o in ordn if not any(abs(round(o[1]) - y) <= 2 for y in egna)]
                under = [o[4] for o in ovriga if o[3] > R.y1 + TOL]
                sidor = [o[4] for o in ovriga if o[3] <= R.y1 + TOL and (o[0] < R.x0 - TOL or o[2] > R.x1 + TOL)]
                if under:
                    fel.append(f"{nr}.{i}: {len(under)} ord nedanför eller över ramens nederkant ({' '.join(under[:6])} …)")
                if sidor:
                    anm.append(f"{nr}.{i}: {len(sidor)} ord över ramens sidor ({' '.join(sidor[:6])} …)")
    return fel, anm


if __name__ == "__main__":
    fel, anm = kontroll(Path(sys.argv[1]))
    for rad in anm:
        print(f"  anmärkning {rad}")
    for rad in fel:
        print(f"  FEL {rad}")
    if fel:
        raise SystemExit("Ritningar med text utanför bladet: gör plats för tabellen eller dela den i spalter.")
    print(f"ritningarna: ingen text utanför bladen ({len(anm)} anmärkningar)")
