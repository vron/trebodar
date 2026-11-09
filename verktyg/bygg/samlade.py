"""Handlingarna samlade för utskrift: alla sidor i handlingsförteckningens ordning, uppdelade efter pappersformat i en
pdf med A4-sidorna (rapporterna, bygglovsbeslutet och ansökan) och en med A3-sidorna (ritningarna), med ett bokmärke
per handling. Större sidor skalas till A3, liggande. Körs från startsida.py med pymupdf:

    uv run --no-project --with pymupdf python samlade.py A4.pdf A3.pdf handlingar.json

handlingar.json: [[titel, sökväg], …] i ordning.
"""
from __future__ import annotations

import json
import sys

import pymupdf

A4_MAX = 842.0 * 1.15            # sidor med den längre sidan högst så lång [pt] hamnar i A4-filen
A3 = (1190.55, 841.89)           # A3 liggande [pt]


def samla(a4: str, a3: str, handlingar: list[list[str]]) -> tuple[int, int]:
    ut = {"A4": pymupdf.open(), "A3": pymupdf.open()}
    toc: dict[str, list[list]] = {"A4": [], "A3": []}
    for titel, sokvag in handlingar:
        with pymupdf.open(sokvag) as d:
            for i, sida in enumerate(d):
                w, h = sida.rect.width, sida.rect.height
                fmt = "A4" if max(w, h) <= A4_MAX else "A3"
                mal = ut[fmt]
                if not toc[fmt] or toc[fmt][-1][1] != titel:
                    toc[fmt].append([1, titel, mal.page_count + 1])
                if fmt == "A4" or abs(max(w, h) - A3[0]) < 30.0:
                    mal.insert_pdf(d, from_page=i, to_page=i)
                else:                           # större än A3: skalad till A3 liggande (eller stående)
                    bw, bh = A3 if w >= h else (A3[1], A3[0])
                    ny = mal.new_page(width=bw, height=bh)
                    ny.show_pdf_page(ny.rect, d, i)
    for fmt, fil in (("A4", a4), ("A3", a3)):
        ut[fmt].set_toc(toc[fmt])
        ut[fmt].save(fil, garbage=3, deflate=True)
    return ut["A4"].page_count, ut["A3"].page_count


if __name__ == "__main__":
    a4_, a3_, lista = sys.argv[1:4]
    with open(lista, encoding="utf-8") as f:
        n4, n3 = samla(a4_, a3_, json.load(f))
    print(f"  samlade: {n4} sidor A4, {n3} sidor A3")
