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
# köksfläktens kanal genom taket till takfläkten: större än kåpans utlopp, för låg hastighet och tyst fläkt (3,5 m/s
# vid 111 l/s)
ISOLERAD_200 = Kanaltyp("ISO200", "Spirokanal Ø200, isolerad 50 mm mineralull med folie", "rund", 200.0, 200.0,
                        isolering=50.0)
# genom ytterväggen: isolerad hylsa (kondens)
VAGGHYLSA_100 = Kanaltyp("VH100", "Väggenomföring Ø100, isolerad 20 mm", "rund", 100.0, 100.0, isolering=20.0)
# i en lätt vägg (stomme 45 × 70): platt kanal med samma tvärsnitt som Ø125
PLATT_125 = Kanaltyp("PL204", "Plattkanal 204 × 60, plast (motsvarar Ø125)", "platt", 204.0, 60.0)

RUND_PLATT_125 = Overgangstyp("OV125-RP", "Övergång Ø125 – 204 × 60", SPIRO_125, PLATT_125, 140.0)
PLATT_RUND_125 = Overgangstyp("OV125-PR", "Övergång 204 × 60 – Ø125, isolerad", PLATT_125, ISOLERAD_125, 140.0)
RUND_150_200 = Overgangstyp("OV150-200", "Övergång Ø150 – Ø200, isolerad", SPIRO_150, ISOLERAD_200, 150.0)

# ------------------------------------------------------------------ don och fläktar

FRANLUFTSDON_125 = Dontyp("FD125", "Frånluftsdon Ø125, vitlackerat (ej valt)", 125.0, 190.0, 40.0, 20.0)

# vägghängd köksfläkt utan egen fläkt (takfläkten nedan): en kåpa av vit pulverlackerad rostfri plåt från ramen
# 698 × 500 i underkanten upp till innertaket, avsmalnande med samma vinkel på bredden och djupet till 180 × 240 vid
# innertaket (#104, specialtillverkad), med fettfilter och utlopp Ø150 för extern fläkt; forcerat 400 m³/h, normalt
# 200 m³/h
KOKSFLAKT_CARISMA = Koksflakttyp("KAPA70", "Köksfläktskåpa av vit pulverlackerad rostfri plåt, avsmalnande till "
                                 "innertaket, för extern fläkt", "", "", b=698.0, d=500.0, h=150.0,
                                 skorsten=(180.0, 240.0), anslutning=150.0, utlopp=120.0, flode=111.0, flode_normal=56.0,
                                 produkt="KOKSFLAKT", avsmalnande=True)

# badrumsfläkt i röret genom ytterväggen, fuktstyrd, med backspjäll
VAGGFLAKT_100 = Vaggflakttyp("VF100", "Badrumsfläkt för vägg Ø100, fuktstyrd med backspjäll (ej vald)", "", "",
                             anslutning=100.0, front=(175.0, 175.0, 35.0), flode=15.0, flode_normal=10.0)

KANALFLAKT_125 = Kanalflakttyp("KAF125", "Kanalfläkt Ø125, rund (ej vald)", "", "", anslutning=125.0, d=250.0,
                               langd=230.0, flode=50.0)

# ------------------------------------------------------------------ avluftsdon

# takfläkten till köksfläkten: bottenplattan Ø439, huset Ø364, höjden 187 (Systemairs måttabell); 216 l/s fritt
# och 108 l/s vid 284 Pa, så kåpans 111 l/s tas tyst på halvt varvtal. Bottenplattan skruvas på en sockel Ø300 av
# takplåt (hålcirkeln Ø250) runt den isolerade kanalen Ø200 genom taket
TAKFLAKT_200 = Avluftstyp("TFSR200", "Takfläkt Systemair TFSR 200 EC Sileo med backspjäll", "takfläkt", 200.0, 439.0,
                          187.0, backspjall=True, hus=364.0, sockel=200.0, sockel_d=300.0, produkt="TAKFLAKT")
GALLER_100 = Avluftstyp("YG100", "Ytterväggsgaller Ø100, aluminium, svart (ej valt)", "galler", 100.0, 160.0, 160.0,
                        djup=35.0)
TAKHUV_125 = Avluftstyp("TH125", "Takhuv Ø125 för bandtäckt plåttak, zink-magnesium (ej vald)", "takhuv", 125.0,
                        280.0, 350.0)
