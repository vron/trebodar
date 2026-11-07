"""Produkterna i elinstallationen. Armaturerna är valda produkter med tillverkarens data; dosor, apparater och rör är
tills vidare allmänna typer med vanliga mått (produkterna väljs senare).
"""
from __future__ import annotations

import math

from .typer import Apparattyp, Armaturtyp, Dosatyp, Pendel, Rortyp, Tubhuvud

# ------------------------------------------------------------------ armaturer

# SG Armaturen Junistar Exclusive, infälld och vridbar 40°, för snedtak: databladet för 903201 och fotometrifilen
# (EULUMDAT, 730 lm ur fördelningen, största ljusstyrka 1 015 cd). Frontring Ø94, håltagning Ø83, 53 mm över
# takytan, separat drivdon 101 × 51 × 22 på kabel, 10 mm till brännbart i ljusets riktning. Monteringsanvisningen
# (rev. 15.08.2023): får inte täckas med isolering; i en SG-box eller i ett hålrum minst 56 mm från takytan och om
# minst 4 l.
JUNISTAR_EXCLUSIVE = Armaturtyp(
    "JUNISTAR-EXCL", "Junistar Exclusive In/Outdoor White 730lm 2700K Ra>95 Trailing edge", "SG Armaturen", "903201",
    "https://www.sg-as.com/int/en/products/outdoor/downlight-outdoor/junistar-exclusive/"
    "junistar-exclusive-in-outdoor-white-9w-led-2700k",
    produkt="ARM-JUNISTAR",
    ljusflode=730.0, effekt=11.0, fargtemperatur=2700.0, ra=95.0, stralvinkel=42.0, vridbar=40.0, ip="IP44/IP20",
    dimring="bakkant", ring_d=94.0, hal_d=83.0, djup=53.0, lysande_d=48.0, brandavstand=10.0, min_djup=56.0,
    min_volym=4.0, drivdon=(101.0, 51.0, 22.0), fotometri="sg-armaturen/junistar-exclusive/903201.ldt",
    fotometri_url="https://www.sg-as.com/int/en/file/techfile/1QA9/7021989032014_Junistar%20Exclusive%20InOutdoor"
                  "%20White%20730lm%202700K%20Ra%2098-33026.ldt")

# SG Armaturen Tube Mini R, infälld dosa med frontplatta och en tub på en stam, vridbar 350° kring stammen och lutbar
# 90°: databladet för 320696 och fotometrifilen (880 lm ur fördelningen, största ljusstyrka 1 824 cd, lysande yta
# Ø54). Frontplatta Ø94, håltagning Ø83, 51 mm över takytan, 50 mm till brännbart i ljusets riktning (databladets
# "distance to flammable materials", som för Tube Micro R är märkningen 0,01 m i ljusets riktning); tub Ø59 × 160
# (linjeritningen), stammen och leden mätta ur linjeritningen; svart bländskydd i fronten. Drivdonet sitter i dosan.
# IsoSafe: monteringsanvisningen (rev. 04.02.2025) visar den i installationsskiktet under isoleringen, med isoleringen
# direkt på dosan och i SG:s boxar.
TUBE_MINI_R = Armaturtyp(
    "TUBE-MINI-R", "Tube Mini R White 880lm 2700K Ra 98 Trailing edge", "SG Armaturen", "320696",
    "https://www.sg-as.com/products/tube-mini-r/320696",
    produkt="ARM-TUBE",
    ljusflode=880.0, effekt=14.0, fargtemperatur=2700.0, ra=98.0, stralvinkel=40.0, vridbar=90.0, ip="IP20",
    dimring="bakkant", ring_d=94.0, hal_d=83.0, djup=51.0, lysande_d=54.0, brandavstand=50.0, isoleras=True,
    drivdon=None, fotometri="sg-armaturen/tube-mini-r/320696.ldt",
    fotometri_url="https://www.sg-as.com/int/en/file/techfile/KLBE/7021983206961_Tube%20Mini%20R%20White%20880lm"
                  "%202700K%20Ra%2098%20Trailing%20edge%20dimming.ldt",
    symbol="tubspot", huvud=Tubhuvud(diameter=59.0, langd=160.0, stam=62.0, stam_d=12.0, led=55.0, indrag=18.0))

# ------------------------------------------------------------------ pendlar
# Ljuskällan sitter i armaturens sockel och är inte vald (utom Stav, där den ingår): ljusflödet är ljuskällans, och
# armaturens skärmar och glas formar ljuset i renderingen (Pendel). Opalglasets transmission är en uppskattning.

# Louis Poulsen PH 5, Monochrome White: Ø500, höjd 267, E27 högst 75 W, sladd 3 m, 2,1 kg (Lampmasters, art. 6090322).
# Skärmarna mätta ur produktbilden (el.py): toppskärmen Ø301 med en krona Ø175 under, huvudskärmen Ø500, mellanskivan,
# kupan Ø208 och det frostade glaset Ø117 i botten; ljuset går genom glaset, mellan huvudskärmen och kupan, och
# genom springan runt kronan upp mot toppskärmen.
PH5 = Armaturtyp(
    "PH5", "PH 5 Monochrome White, E27", "Louis Poulsen", "EAN 5714693431151",
    "https://www.lampmasters.co.uk/p/ph-5-pendant-monochrome-white-louis-poulsen-6090322.html",
    produkt="ARM-PH5",
    ljusflode=1055.0, effekt=9.5, fargtemperatur=2700.0, ra=90.0, stralvinkel=0.0, vridbar=0.0, ip="IP20",
    dimring="bakkant", ring_d=100.0, hal_d=0.0, djup=0.0, lysande_d=117.0, brandavstand=0.0, drivdon=None,
    fotometri="", fotometri_url="", symbol="pendel",
    pendel=Pendel("ph5", 500.0, 267.0, kalla=208.0, kalla_d=60.0,
                  ljuskalla="E27 LED A60 1 055 lm 2 700 K Ra 90 (ej vald)",
                  lysande_yta=2 * math.pi * 57.0 * 23.0 + math.pi * 55.0 ** 2, lysande_andel=0.3,
                  takkopp=(100.0, 30.0)))


def _vl45(d: float, h: float, artikel: str, effekt: float, flode: float, lampa: str) -> Armaturtyp:
    """Louis Poulsen VL45 Radiohus, mässing och opalglas (tre lager munblåst glas, det mellersta vitt): globen lika
    hög som bred, ett fäste av mässing och vit sladd 4 m (David Village Lighting, produktblad LA4362)."""
    return Armaturtyp(
        f"VL45-{d:.0f}", f"VL45 Radiohus Ø{d:.0f}, mässing/opal", "Louis Poulsen", artikel,
        "https://www.davidvillagelighting.co.uk/product/Louis-Poulsen-VL-45-Radiohus-Pendant/17235",
        produkt="ARM-VL45",
        ljusflode=flode, effekt=effekt, fargtemperatur=2700.0, ra=90.0, stralvinkel=0.0, vridbar=0.0, ip="IP20",
        dimring="bakkant", ring_d=90.0, hal_d=0.0, djup=0.0, lysande_d=d, brandavstand=0.0, drivdon=None,
        fotometri="", fotometri_url="", symbol="pendel",
        pendel=Pendel("vl45", d, h, kalla=h - d / 2, kalla_d=35.0 if d < 200 else 60.0, ljuskalla=lampa,
                      lysande_yta=1.12 * math.pi * d ** 2, lysande_andel=1.0, transmission=0.7))


# VL45 i tre storlekar (Ø175, Ø250, Ø370; höjden med fästet 246, 328 och 448), lampan högst 5,7, 10 och 11 W LED
VL45_175 = _vl45(175.0, 246.0, "6090238 (Lampmasters)", 4.9, 470.0, "E14 LED 470 lm 2 700 K Ra 90 (ej vald)")
VL45_250 = _vl45(250.0, 328.0, "ej vald", 7.5, 806.0, "E27 LED 806 lm 2 700 K Ra 90 (ej vald)")
VL45_370 = _vl45(370.0, 448.0, "ej vald", 10.0, 1055.0, "E27 LED 1 055 lm 2 700 K Ra 90 (ej vald)")

# Konsthantverk Stav, råmässing (Johan Carpner): en mässingsstav Ø6 och ett mässingsrör Ø30, höjd 350, sladd 3 m
# svart textil, E14 LED medföljer (max 10 W, flödet anges inte: antaget 470 lm), "direkt smal" ljusfördelning ut ur
# rörets botten (strålvinkeln antagen 40°). Takkoppen ingår inte: en takkopp i mässing.
STAV = Armaturtyp(
    "STAV", "Stav pendel, råmässing", "Konsthantverk", "Nordic Nest 562066-01",
    "https://www.nordicnest.com/brands/konsthantverk/stav-pendant/",
    produkt="ARM-STAV",
    ljusflode=470.0, effekt=4.5, fargtemperatur=2700.0, ra=90.0, stralvinkel=40.0, vridbar=0.0, ip="IP20",
    dimring="ingen", ring_d=80.0, hal_d=0.0, djup=0.0, lysande_d=24.0, brandavstand=0.0, drivdon=None,
    fotometri="", fotometri_url="", symbol="pendel",
    pendel=Pendel("stav", 30.0, 337.0, kalla=325.0, kalla_d=20.0, ljuskalla="E14 LED 470 lm 2 700 K (medföljer)",
                  lysande_yta=math.pi * 12.0 ** 2, lysande_andel=1.0, sladd="svart", takkopp=(80.0, 25.0),
                  takkopp_massing=True))

# Glob av opalglas Ø250 med vitt fäste och vit textilsladd, allmän (ej vald)
GLOB_250 = Armaturtyp(
    "GLOB-250", "Glob, opalglas Ø250, vitt fäste (ej vald)", "Allmän", "ej vald", "",
    produkt="ARM-GLOB",
    ljusflode=806.0, effekt=7.5, fargtemperatur=2700.0, ra=90.0, stralvinkel=0.0, vridbar=0.0, ip="IP20",
    dimring="bakkant", ring_d=90.0, hal_d=0.0, djup=0.0, lysande_d=250.0, brandavstand=0.0, drivdon=None,
    fotometri="", fotometri_url="", symbol="pendel",
    pendel=Pendel("glob", 250.0, 285.0, kalla=160.0, kalla_d=60.0, ljuskalla="E27 LED 806 lm 2 700 K Ra 90 (ej vald)",
                  lysande_yta=math.pi * 250.0 ** 2, lysande_andel=1.0, transmission=0.7))

# Vägglampa: glob av opalglas Ø160 under en kåpa av mässing, på en arm från en väggplatta, IP44, allmän (ej vald);
# över badrummets tvättställ (rum/badrum.py)
VAGGLAMPA = Armaturtyp(
    "VAGG-GLOB-160", "Vägglampa, glob av opalglas Ø160 på arm av mässing, IP44 (ej vald)", "Allmän", "ej vald", "",
    produkt="ARM-VAGGLAMPA",
    ljusflode=470.0, effekt=4.5, fargtemperatur=2700.0, ra=90.0, stralvinkel=0.0, vridbar=0.0, ip="IP44",
    dimring="bakkant", ring_d=100.0, hal_d=0.0, djup=0.0, lysande_d=160.0, brandavstand=0.0, drivdon=None,
    fotometri="", fotometri_url="", symbol="vagglampa",
    pendel=Pendel("glob", 160.0, 195.0, kalla=110.0, kalla_d=40.0, ljuskalla="E14 LED 470 lm 2 700 K Ra 90 (ej vald)",
                  lysande_yta=math.pi * 160.0 ** 2, lysande_andel=1.0, transmission=0.7, takkopp=(100.0, 20.0),
                  takkopp_massing=True, arm=170.0))

# ------------------------------------------------------------------ dosor (allmänna)

APPARATDOSA = Dosatyp("APPARATDOSA", "Apparatdosa för skiva, Ø68 (ej vald)", "apparatdosa", 68.0, 45.0)
KOPPLINGSDOSA = Dosatyp("KOPPLINGSDOSA", "Kopplingsdosa i innertakets installationsskikt (ej vald)", "kopplingsdosa",
                        80.0, 40.0, symbol="kopplingsdosa")
INGJUTNINGSDOSA = Dosatyp("INGJUTNINGSDOSA", "Ingjutningsdosa för betongbjälklag, takdosa (ej vald)", "ingjutningsdosa",
                          90.0, 70.0, symbol="ingjutningsdosa")
# LEDVANCE PANEL COMPACT 600 V 26W 830 UGR19 (EAN 4099854734465, Ahlsell 7029488), källarens arbetsrum (#51): 3 640 lm,
# 26 W, 3000 K, Ra > 80, UGR < 19, 595 × 595 × 34 med separat drivdon, utanpåliggande med tillverkarens ram för
# ytmontage (PANEL 600 SURFACE MOUNT KIT; ramens höjd antagen 75), ansluten i en ingjuten dosa ovanför sig
PANEL_600 = Armaturtyp(
    "PANEL-600", "PANEL COMPACT 600 V 26W 830 U19", "LEDVANCE", "4099854734465",
    "https://www.ledvance.com/sv-se/shortlink/4099854734465", produkt="ARM-PANEL",
    ljusflode=3640.0, effekt=26.0, fargtemperatur=3000.0, ra=80.0, stralvinkel=90.0, vridbar=0.0, ip="IP50/IP20",
    dimring="ingen", ring_d=0.0, hal_d=0.0, djup=0.0, lysande_d=575.0, brandavstand=0.0, drivdon=None,
    fotometri="ledvance/panel-compact-600/4099854734465.ldt",
    fotometri_url="https://www.ledvance.com/00_Free_To_Use/asset-13340714_LDT_file_Eulumdat_COMP_600_V_26W_830_U19"
                  "_3640lm.ldt",
    symbol="panel", panel=(595.0, 595.0, 75.0), dosa=INGJUTNINGSDOSA)
CENTRAL = Dosatyp("CENTRAL", "Gruppcentralen i teknikrummet (rörens början på dess ovansida)", "central", 0.0, 0.0,
                  symbol="central")
BRANDLARM_MATNING = Dosatyp("BL-MATNING", "Brandlarmets matningsdosa i källarens tak (brandlarm/larm.py, D01)",
                            "brandlarm", 0.0, 0.0, symbol="ingjutningsdosa")

# ------------------------------------------------------------------ apparater (allmänna)

DIMMER_1 = Apparattyp("DIMMER-1", "Dimmer, en kanal, bakkant (LED, ej vald)", "dimmer", 1, (80.0, 80.0), APPARATDOSA,
                      "dimmer")
DIMMER_2 = Apparattyp("DIMMER-2", "Dimmer, två kanaler, bakkant (LED, ej vald)", "dimmer", 2, (80.0, 80.0), APPARATDOSA,
                      "dimmer")
BRYTARE_1 = Apparattyp("BRYTARE-1", "Strömbrytare, en pol (ej vald)", "brytare", 1, (80.0, 80.0), APPARATDOSA,
                       "brytare")
UTTAG_2 = Apparattyp("UTTAG-2", "Vägguttag, dubbelt, jordat (ej valt)", "uttag", 2, (151.0, 80.0), APPARATDOSA, "uttag")
UTTAG_1 = Apparattyp("UTTAG-1", "Vägguttag, enkelt, jordat (ej valt)", "uttag", 1, (80.0, 80.0), APPARATDOSA, "uttag")
UTTAG_2_IP44 = Apparattyp("UTTAG-2-IP44", "Vägguttag, dubbelt, jordat, IP44 med lock (våtrum, ej valt)", "uttag", 2,
                          (151.0, 80.0), APPARATDOSA, "uttag")
UTTAG_1_IP44 = Apparattyp("UTTAG-1-IP44", "Vägguttag, enkelt, jordat, IP44 med lock (våtrum, ej valt)", "uttag", 1,
                          (80.0, 80.0), APPARATDOSA, "uttag")
ANSLUTNING = Apparattyp("ANSLUTNING", "Anslutning för fast ansluten apparat, med lock (ej vald)", "anslutning", 1,
                        (80.0, 80.0), APPARATDOSA, "anslutning")
ANSLUTNING_3FAS = Apparattyp("ANSLUTNING-3F", "Anslutning för fast ansluten apparat, 400 V (hällen, ej vald)",
                             "anslutning", 1, (80.0, 80.0), APPARATDOSA, "anslutning")

# ------------------------------------------------------------------ rör

FXP16 = Rortyp("FXP16", "Flexrör 16 mm", 16.0, 60.0)
FXP20 = Rortyp("FXP20", "Flexrör 20 mm", 20.0, 80.0)
