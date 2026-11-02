"""Produkterna i elinstallationen. Armaturerna är valda produkter med tillverkarens data; dosor, apparater och rör är
tills vidare allmänna typer med vanliga mått (produkterna väljs senare).
"""
from __future__ import annotations

from .typer import Apparattyp, Armaturtyp, Dosatyp, Rortyp, Tubhuvud

# ------------------------------------------------------------------ armaturer

# SG Armaturen Junistar Exclusive, infälld och vridbar 40°, för snedtak: databladet för 903201 och fotometrifilen
# (EULUMDAT, 730 lm ur fördelningen, största ljusstyrka 1 015 cd). Frontring Ø94, håltagning Ø83, 53 mm över
# takytan, separat drivdon 101 × 51 × 22 på kabel.
JUNISTAR_EXCLUSIVE = Armaturtyp(
    "JUNISTAR-EXCL", "Junistar Exclusive In/Outdoor White 730lm 2700K Ra>95 Trailing edge", "SG Armaturen", "903201",
    "https://www.sg-as.com/int/en/products/outdoor/downlight-outdoor/junistar-exclusive/"
    "junistar-exclusive-in-outdoor-white-9w-led-2700k",
    ljusflode=730.0, effekt=11.0, fargtemperatur=2700.0, ra=95.0, stralvinkel=42.0, vridbar=40.0, ip="IP44/IP20",
    dimring="bakkant", ring_d=94.0, hal_d=83.0, djup=53.0, lysande_d=48.0, brandavstand=10.0,
    drivdon=(101.0, 51.0, 22.0), fotometri="sg-armaturen/junistar-exclusive/903201.ldt",
    fotometri_url="https://www.sg-as.com/int/en/file/techfile/1QA9/7021989032014_Junistar%20Exclusive%20InOutdoor"
                  "%20White%20730lm%202700K%20Ra%2098-33026.ldt")

# SG Armaturen Tube Mini R, infälld dosa med frontplatta och en tub på en stam, vridbar 350° kring stammen och lutbar
# 90°: databladet för 320696 och fotometrifilen (880 lm ur fördelningen, största ljusstyrka 1 824 cd, lysande yta
# Ø54). Frontplatta Ø94, håltagning Ø83, 51 mm över takytan, 50 mm till brännbart; tub Ø59 × 160 (linjeritningen),
# stammen och leden mätta ur linjeritningen; svart bländskydd i fronten. Drivdonet sitter i dosan.
TUBE_MINI_R = Armaturtyp(
    "TUBE-MINI-R", "Tube Mini R White 880lm 2700K Ra 98 Trailing edge", "SG Armaturen", "320696",
    "https://www.sg-as.com/products/tube-mini-r/320696",
    ljusflode=880.0, effekt=14.0, fargtemperatur=2700.0, ra=98.0, stralvinkel=40.0, vridbar=90.0, ip="IP20",
    dimring="bakkant", ring_d=94.0, hal_d=83.0, djup=51.0, lysande_d=54.0, brandavstand=50.0, drivdon=None,
    fotometri="sg-armaturen/tube-mini-r/320696.ldt",
    fotometri_url="https://www.sg-as.com/int/en/file/techfile/KLBE/7021983206961_Tube%20Mini%20R%20White%20880lm"
                  "%202700K%20Ra%2098%20Trailing%20edge%20dimming.ldt",
    symbol="tubspot", huvud=Tubhuvud(diameter=59.0, langd=160.0, stam=62.0, stam_d=12.0, led=55.0, indrag=18.0))

# ------------------------------------------------------------------ dosor (allmänna)

APPARATDOSA = Dosatyp("APPARATDOSA", "Apparatdosa för skiva, Ø68 (ej vald)", "apparatdosa", 68.0, 45.0)
KOPPLINGSDOSA = Dosatyp("KOPPLINGSDOSA", "Kopplingsdosa i innertakets installationsskikt (ej vald)", "kopplingsdosa",
                        80.0, 40.0, symbol="kopplingsdosa")
INGJUTNINGSDOSA = Dosatyp("INGJUTNINGSDOSA", "Ingjutningsdosa för betongbjälklag, takdosa (ej vald)", "ingjutningsdosa",
                          90.0, 70.0, symbol="ingjutningsdosa")

# ------------------------------------------------------------------ apparater (allmänna)

DIMMER_1 = Apparattyp("DIMMER-1", "Dimmer, en kanal, bakkant (LED, ej vald)", "dimmer", 1, (80.0, 80.0), APPARATDOSA,
                      "dimmer")
DIMMER_2 = Apparattyp("DIMMER-2", "Dimmer, två kanaler, bakkant (LED, ej vald)", "dimmer", 2, (80.0, 80.0), APPARATDOSA,
                      "dimmer")
BRYTARE_1 = Apparattyp("BRYTARE-1", "Strömbrytare, en pol (ej vald)", "brytare", 1, (80.0, 80.0), APPARATDOSA,
                       "brytare")
UTTAG_2 = Apparattyp("UTTAG-2", "Vägguttag, dubbelt, jordat (ej valt)", "uttag", 2, (151.0, 80.0), APPARATDOSA, "uttag")

# ------------------------------------------------------------------ rör

FXP16 = Rortyp("FXP16", "Flexrör 16 mm", 16.0, 60.0)
FXP20 = Rortyp("FXP20", "Flexrör 20 mm", 20.0, 80.0)
