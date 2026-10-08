"""
K-06: förutsättningar. Geometri och laster från plan 1 hämtas från K-05 (../K-05), så att handlingarna
använder samma underlag.

Enheter: mm, N, MPa i FE-modellen; kN, m, kPa i tabeller.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
K05 = os.path.join(os.path.dirname(HERE), "K-05")
sys.path.insert(0, K05)

import json  # noqa: E402

G05 = json.load(open(os.path.join(K05, "bild", "geometri.json"), encoding="utf-8"))

# ------------------------------------------------------------------ nivåer och mått
H_VAGG = 2100.0          # fri höjd från bottenplattans överkant till mellanbjälklagets underkant (rörens längd)
T_VAGG = 350.0           # Lecavägg 100 + 150 isolering + 100
T_SKIKT = 100.0          # ett Lecaskikt
KI = 30.0                # mellanbjälklagets kant ligger 30 mm innanför Lecans ytterliv (K-05)
B_BALK = 450.0           # kantbalkens bredd: L-elementets bredd 550 minus det yttre benet 100
T_FOT = 100.0            # cellplast under kantbalk och plintar (L-elementets fot)
H_PLATTA = 100.0         # bottenplattans tjocklek i fält (Plattor.pdf)
# två utföranden av bottenplattan (L-element 300 och 400): cellplast under plattan och kantbalkens höjd
UTFORANDEN = {
    "L300": dict(H=300.0, t_eps=200.0, h_balk=200.0),
    "L400": dict(H=400.0, t_eps=300.0, h_balk=300.0),
}

# ------------------------------------------------------------------ jord och fyllning
GAMMA_JORD = 18.0        # kN/m³, dränerande friktionsmaterial (krossat berg, grus)
FI_JORD = 40.0           # friktionsvinkel för dränerande kross [°]
K0 = 1 - __import__("math").sin(__import__("math").radians(FI_JORD))   # vilojordtryck, väggen hålls i topp och botten
Q_MARK = 2.5             # kN/m², nyttig last på marken intill väggen (gångyta, trädgård), inga fordon närmare än 2 m
# bakom V3 och V20: plattan på mark på plan 1 (K-05) med 400 mm cellplast
EPS_MARK = 400.0
H_FYLL_MARK = (H_VAGG - EPS_MARK) / 1000            # m, fyllning upp till cellplasten under plattan
G_MARK = 25 * 0.15 + 0.5 + 0.3 * EPS_MARK / 1000    # kN/m², betong, golv och cellplast
Q_MARK_PLATTA = 2.0 + 0.7                           # kN/m², nyttig last och lätta väggar

# fyllnadshöjd (m) vid väggens ände a och b (a < b i väggens riktning, mitt i väggens centrumlinje)
# ändvillkor: "h" hörn eller T-anslutning (armeringen förs runt, inspänd), "f" fri ände (öppning)
FYLL = {
    "V1": dict(h=(2.0, 2.0), ande=("h", "h")),
    "V2": dict(h=(2.0, 2.0), ande=("h", "h")),
    "V3": dict(h=(H_FYLL_MARK, H_FYLL_MARK), ande=("h", "h"), platta=True),
    "V7": dict(h=(2.0, 2.0), ande=("h", "h")),
    "V9": dict(h=(0.0, 0.8), ande=("f", "h")),
    "V14": dict(h=(0.8, 1.8), ande=("h", "h")),
    "V16": dict(h=(2.0, 2.0), ande=("h", "h")),
    "V18": dict(h=(0.0, 2.0), ande=("f", "h")),
    "V20": dict(h=(H_FYLL_MARK, H_FYLL_MARK), ande=("h", "h"), platta=True),
    "V21": dict(h=(2.0, 2.0), ande=("h", "h")),
}

# ------------------------------------------------------------------ murverk (EKS 12 avdelning H)
GAMMA_M_MUR = 2.1        # tabell H-1: block kategori I, specialmurbruk, utförandeklass II
GAMMA_M_ARM = 1.3        # tabell H-1: armeringens hållfasthet
SYSTEM = {
    "A": dict(namn="Leca Isoblokk 35 (Leca Norge)",
              fk=3.4,            # tabell H-4: lättklinkerblock 5 MPa, murbruk M2,5–M10 (weber M5)
              fxk1=0.15, fxk2=0.30,   # tabell H-6, M2,5–M10
              skift=207.0,       # blockhöjd 197 + fog 10 mm under mark
              vikt=13.2 * 10 / 100 + 0.25,  # kN/m²: 10 block/m² à 13,2 kg, bruk
              arm="Leca Sikksakk-armering 2 × Ø5 (fagverk mellan vangerna)",
              As_drag=19.5,      # mm², en stång i den dragna vangen
              fyk=500.0,
              d=287.5,           # Sikksakk 225 mm bred: stängerna 62,5 mm från väggens ytor
              samverkan=True),
    "B": dict(namn="LECA Isoblock 350 PUR (Benders)",
              fk=3.1,            # tabell H-4: lättklinkerblock 5 MPa, tunnfogsbruk (Flexoheft)
              fxk1=0.20, fxk2=0.30,   # tabell H-6, tunnfogsbruk
              skift=200.0,       # blockhöjd 197 + tunnfog
              vikt=16.0 * 10 / 100 + 0.1,
              arm="bistål Bi 40 ob (insida) och Bi 37 rf (utsida), ett per vange",
              As_drag=12.6,      # mm², en tråd Ø4 (den andra tråden ligger nära neutrallagret)
              fyk=500.0,         # Bi 37 rf (rostfri) räknas som 500 MPa; Bi 40 ob har 690
              d=64.0,            # vangens mitt + halva bistålets bredd 28/2
              samverkan=False),
}
PUTS = 2 * 0.010 * 18.0  # kN/m², puts/slamning på båda sidor

# ------------------------------------------------------------------ cellplast (EPS-Sverige, WSP 10221233)
# karakteristisk tryckhållfasthet f_ck och E-modul E_k (kPa) enligt tabell 1.2.2a
EPS = {
    "S100": dict(fck=90.0, Ek=3000.0, kryp2=30.0),     # kryp2: långtidslast vid 2 % deformation (tillverkare)
    "S150": dict(fck=135.0, Ek=4500.0, kryp2=45.0),
    "S200": dict(fck=180.0, Ek=6000.0, kryp2=60.0),
    "S300": dict(fck=280.0, Ek=9000.0, kryp2=90.0),
}
# S300 lokalt under kantbalken (x0, y0, x1, y1): hörnet V2/V20, där LD4_2 står, 1,0 m åt båda håll
S300_ZON = {"L300": [(4365.0, 10040.0, 5365.0, 11040.0)], "L400": []}
EPS_GAMMA_M = 1.3        # med tillverkningskontroll
EPS_KR = {"P": (0.40, 0.45), "M": (0.50, 0.55), "S": (0.60, 0.65)}   # k_r för f_k < 200 resp. ≥ 200 kPa
EPS_KS = 0.40            # styvhet i bruksgränstillstånd för långtidslast (P, L)

# ------------------------------------------------------------------ Lecaväggens styvhet (vertikalt)
E_LECA = 3400.0          # MPa, K_E · f_k (EKS tabell H, K_E = 1000)
KRYP_LECA = 2.0          # slutligt kryptal för lättklinkerblock (SS-EN 1996-1-1 tabell 3.3: 1,0–4,0)
SVINN_LECA = 0.40e-3     # slutlig krympning, deklarerat värde (DoP Leca Isoblokk: −0,40 mm/m)
