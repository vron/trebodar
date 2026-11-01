"""Trappan till källaren, i trapphålet: brant rak trätrappa av furu från källarens golv (bottenplattan) upp till
plan 1 vid väggen 2B, där skjutdörren ID2 sitter. Den ryms i hålet, så att den fria höjden över den är hela
våningshöjden: vangstyckena står på golvet med framkanten i hålets västra kant och hänger i överkant mot den östra.

Två vangstycken 45×270 vid trapphålets långsidor och 10 steg 38 mm med öppna sättsteg mellan dem: 11 steghöjder à
2 250 / 11 = 204,5 och stegdjupet (2 070 − 50) / 10 = 202 (lutning 45°, 2h + g = 611), stegen 20 mm framför
sättstegets linje och vangstyckenas framkant 50 mm före det nedersta.
"""
from __future__ import annotations

from modellering import Del, Montage, Placering, box, prisma

from trebodar import skelett as S
from trebodar.byggdelar.virke import fmt
from trebodar.material import FURU

N_STEG = 11                       # steghöjder
FOT = 50.0                        # vangstyckets framkant före nedersta sättsteget
VANG_T, VANG_H = 45.0, 270.0      # vangstyckena, höjd vinkelrätt mot lutningen
STEG_T, NOS = 38.0, 20.0          # stegens tjocklek och nos
OVER = 70.0                       # vangstyckets överkant ovanför steglinjen (lodrätt)

X0, Y0 = S.TRAPPHAL[0]            # trapphålet: x 7 348–9 418, y 5 059,5–5 887,5
X1, Y1 = S.TRAPPHAL[2]


def montage() -> Montage:
    m = Montage("Trappa", beskrivning="Brant rak trätrappa av furu till källaren, i trapphålet "
                                      f"{fmt(X1 - X0)} × {fmt(Y1 - Y0)}")
    hojd = -S.Z_BOTTENPLATTA                          # golv till golv
    xb = X0 + FOT                                     # nedersta sättsteget
    h, g = hojd / N_STEG, (X1 - xb) / (N_STEG - 1)    # steghöjd och stegdjup
    lutning = h / g
    dz = VANG_H * (1 + lutning ** 2) ** 0.5           # vangstyckets höjd i lodled

    def steglinje(x: float) -> float:
        return S.Z_BOTTENPLATTA + h + (x - xb) * lutning

    # vangstycket i (x, z): framkanten i trapphålets västra kant, golvet, hålets östra kant och plan 1:s golv
    xf = X0
    x_golv = xb + (dz - OVER - h) / lutning           # där underkanten når golvet
    x_topp = xb + (-S.Z_BOTTENPLATTA - h - OVER) / lutning
    profil = [(xf, S.Z_BOTTENPLATTA), (x_golv, S.Z_BOTTENPLATTA), (X1, steglinje(X1) + OVER - dz), (X1, 0.0),
              (x_topp, 0.0), (xf, steglinje(xf) + OVER)]
    vang = Del(f"Vangstycke {VANG_T:g}×{VANG_H:g}", prisma(profil, VANG_T), FURU)
    # profilen i (x, z): prismat i (x, y) med höjden längs y, vridet så att y blir z
    vrid = Placering(((1.0, 0.0, 0.0), (0.0, 0.0, -1.0), (0.0, 1.0, 0.0)), (0.0, 0.0, 0.0))
    for namn, y in (("TR-V1", Y0 + VANG_T), ("TR-V2", Y1)):
        m.lagg(vang, Placering.flytt(0.0, y, 0.0) @ vrid, namn)
    for i in range(1, N_STEG):
        x = xb + (i - 1) * g
        z = S.Z_BOTTENPLATTA + i * h
        m.lagg(Del(f"Steg {Y1 - Y0 - 2 * VANG_T:g}×{g + NOS:g}×{STEG_T:g}",
                   box(x - NOS, x + g, Y0 + VANG_T, Y1 - VANG_T, z - STEG_T, z), FURU), Placering(), f"TR-S{i:02d}")
    return m
