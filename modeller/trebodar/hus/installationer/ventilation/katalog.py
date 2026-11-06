"""Produkterna i ventilationen, tills vidare allmänna typer med vanliga mått och flöden (produkterna väljs senare,
som elens dosor och apparater). Flöden i l/s (1 l/s = 3,6 m³/h).
"""
from __future__ import annotations

from .typer import Avluftstyp, Dontyp, Kanalflakttyp, Kanaltyp, Koksflakttyp, Overgangstyp, Vaggflakttyp

# ------------------------------------------------------------------ kanaler

SPIRO_100 = Kanaltyp("SPIRO100", "Spirokanal Ø100, förzinkad stålplåt", "rund", 100.0, 100.0)
SPIRO_125 = Kanaltyp("SPIRO125", "Spirokanal Ø125, förzinkad stålplåt", "rund", 125.0, 125.0)
SPIRO_150 = Kanaltyp("SPIRO150", "Spirokanal Ø150, förzinkad stålplåt", "rund", 150.0, 150.0)
# genom takets isolering: isolerad, så att den varma och fuktiga frånluften inte kondenserar i kanalen
ISOLERAD_125 = Kanaltyp("ISO125", "Spirokanal Ø125, isolerad 50 mm mineralull med folie", "rund", 125.0, 125.0,
                        isolering=50.0)
# köksfläktens kanal genom taket till takfläkten: den stora kanalen, för låg hastighet och tyst fläkt
ISOLERAD_250 = Kanaltyp("ISO250", "Spirokanal Ø250, isolerad 50 mm mineralull med folie", "rund", 250.0, 250.0,
                        isolering=50.0)
# genom ytterväggen: isolerad hylsa (kondens)
VAGGHYLSA_100 = Kanaltyp("VH100", "Väggenomföring Ø100, isolerad 20 mm", "rund", 100.0, 100.0, isolering=20.0)
# i en lätt vägg (stomme 45 × 70): platt kanal med samma tvärsnitt som Ø125
PLATT_125 = Kanaltyp("PL204", "Plattkanal 204 × 60, plast (motsvarar Ø125)", "platt", 204.0, 60.0)

RUND_PLATT_125 = Overgangstyp("OV125-RP", "Övergång Ø125 – 204 × 60", SPIRO_125, PLATT_125, 140.0)
PLATT_RUND_125 = Overgangstyp("OV125-PR", "Övergång 204 × 60 – Ø125, isolerad", PLATT_125, ISOLERAD_125, 140.0)
RUND_150_250 = Overgangstyp("OV150-250", "Övergång Ø150 – Ø250, isolerad", SPIRO_150, ISOLERAD_250, 150.0)

# ------------------------------------------------------------------ don och fläktar

FRANLUFTSDON_125 = Dontyp("FD125", "Frånluftsdon Ø125, vitlackerat (ej valt)", 125.0, 190.0, 40.0, 20.0)

# vägghängd köksfläkt med skorstenskåpa, utan egen fläkt (takfläkten nedan): kåpan 698 × 500 × 150, skorstenen
# 270 × 240 (Fjäråskupans måttritning); forcerat 400 m³/h, normalt 200 m³/h
KOKSFLAKT_CARISMA = Koksflakttyp("CAR70", "Köksfläkt Fjäråskupan Carisma 70, vit, för extern fläkt", "Fjäråskupan",
                                 "Carisma 70", b=698.0, d=500.0, h=150.0, skorsten=(270.0, 240.0), anslutning=150.0,
                                 utlopp=120.0, flode=111.0, flode_normal=56.0, produkt="KOKSFLAKT", sluttande=True)

# badrumsfläkt i röret genom ytterväggen, fuktstyrd, med backspjäll
VAGGFLAKT_100 = Vaggflakttyp("VF100", "Badrumsfläkt för vägg Ø100, fuktstyrd med backspjäll (ej vald)", "", "",
                             anslutning=100.0, front=(175.0, 175.0, 35.0), flode=15.0, flode_normal=10.0)

KANALFLAKT_125 = Kanalflakttyp("KAF125", "Kanalfläkt Ø125, rund (ej vald)", "", "", anslutning=125.0, d=250.0,
                               langd=230.0, flode=50.0)

# ------------------------------------------------------------------ avluftsdon

# takfläkten till köksfläkten: bottenplattan Ø485, huset Ø404, höjden 206 (Systemairs produktblad), på en sockel i
# takplåten med den isolerade kanalen Ø250 genom taket
TAKFLAKT_315 = Avluftstyp("TFSR315", "Takfläkt Systemair TFSR 315 Sileo med backspjäll", "takfläkt", 250.0, 485.0,
                          206.0, backspjall=True, hus=404.0, sockel=300.0, produkt="TAKFLAKT")
GALLER_100 = Avluftstyp("YG100", "Ytterväggsgaller Ø100, aluminium, svart (ej valt)", "galler", 100.0, 160.0, 160.0,
                        djup=35.0)
TAKHUV_125 = Avluftstyp("TH125", "Takhuv Ø125 för bandtäckt plåttak, zink-magnesium (ej vald)", "takhuv", 125.0,
                        280.0, 350.0)
