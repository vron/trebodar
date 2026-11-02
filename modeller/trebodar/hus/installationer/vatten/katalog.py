"""Produkterna i tappvattnet, tills vidare allmänna typer med vanliga mått och normflöden (Säker Vatten, BBR 6:6):
rör-i-rör från fördelarskåpet till varje tappställe, ingjutna i mellanbjälklaget, väggdosor och golvdosor vid
tappställena och matarledningar i teknikrummet.
"""
from __future__ import annotations

from .typer import Dosatyp, Fordelartyp, Rortyp, Tappstalletyp

# ------------------------------------------------------------------ tappställen (normflöden kallt, varmt)

TVATTSTALL = Tappstalletyp("TS", "Tvättställ", 0.1, 0.1, "TS")
DISKBANK = Tappstalletyp("DB", "Diskbänk (diskmaskinen ansluts i skåpet)", 0.2, 0.2, "DB")
DUSCH = Tappstalletyp("DU", "Dusch", 0.2, 0.2, "DU")
BADKAR = Tappstalletyp("BK", "Badkar", 0.3, 0.3, "BK")
WC = Tappstalletyp("WC", "WC", 0.1, 0.0, "WC")
TVATTMASKIN = Tappstalletyp("TM", "Tvättmaskin", 0.2, 0.0, "TM")
TVATTHO = Tappstalletyp("TH", "Tvättho", 0.2, 0.2, "TH")

# ------------------------------------------------------------------ anslutningar

VAGGDOSA_BLANDARE = Dosatyp("VD2", "Väggdosa för rör-i-rör, kallt och varmt c/c 160 (ej vald)", "vägg", 240.0, 120.0,
                            70.0, cc=160.0)
VAGGDOSA = Dosatyp("VD1", "Väggdosa för rör-i-rör (ej vald)", "vägg", 90.0, 90.0, 70.0)
GOLVDOSA = Dosatyp("GD", "Golvgenomföring för rör-i-rör i skåpet (ej vald)", "golv", 160.0, 80.0, 40.0, cc=60.0)

# ------------------------------------------------------------------ rör

ROR_I_ROR_15 = Rortyp("RIR15", "PEX 15 × 2,5 i skyddsrör 25 (rör-i-rör)", 15.0, 2.5, 25.0)
ROR_I_ROR_16 = Rortyp("RIR16", "PEX 16 × 2,0 i skyddsrör 25 (rör-i-rör)", 16.0, 2.0, 25.0)
ROR_I_ROR_18 = Rortyp("RIR18", "PEX 18 × 2,5 i skyddsrör 28 (rör-i-rör)", 18.0, 2.5, 28.0)
PEX_22 = Rortyp("PEX22", "PEX 22 × 3,0, isoleras i teknikrummet", 22.0, 3.0)

# ------------------------------------------------------------------ fördelare (stammens ändar: inlopp och genomgång)

FORDELARE_KV = Fordelartyp("FDKV", "Fördelare för kallvatten, rör-i-rör, 10 utgångar och genomgång (ej vald)", 10, 40.0)
FORDELARE_VV = Fordelartyp("FDVV", "Fördelare för varmvatten, rör-i-rör, 8 utgångar (ej vald)", 8, 40.0)
