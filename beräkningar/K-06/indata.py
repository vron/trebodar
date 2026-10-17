"""
K-06: förutsättningar. Geometri och laster från plan 1 hämtas från K-05 (../K-05), så att handlingarna
använder samma underlag.

Enheter: mm, N, MPa i FE-modellen; kN, m, kPa i tabeller.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
K05 = os.path.join(os.path.dirname(HERE), "K-05")
sys.path.insert(0, K05)

import json  # noqa: E402

G05 = json.load(open(os.path.join(K05, "bild", "geometri.json"), encoding="utf-8"))

# ------------------------------------------------------------------ nivåer och mått
H_VAGG = 2100.0          # fri höjd från bottenplattans överkant till mellanbjälklagets underkant (rörens längd)
T_VAGG = 350.0           # Kub 350-150: cellplast 100 + betong 150 + cellplast 100
T_KARNA = 150.0          # betongkärnan, i väggens mitt
T_EPS_V = 100.0          # cellplast EPS 120 på var sida om kärnan
KI = 30.0                # mellanbjälklagets kant ligger 30 mm innanför väggens ytterliv (K-05)
H_MB = 150.0             # mellanbjälklagets tjocklek (K-05)
B_BALK = 450.0           # kantbalkens bredd: L-elementets bredd 550 minus det yttre benet 100
T_FOT = 100.0            # cellplast under kantbalk och plintar (L-elementets fot)
L_BEN = 100.0            # L-elementets yttre ben: L-elementets ytterkant i väggens ytterliv, betongen 100 mm innanför,
                         # så att väggens yttre cellplast står på benet och kärnan på kantbalkens yttersta 150 mm
H_PLATTA = 100.0         # bottenplattans tjocklek i fält (Plattor.pdf)
# bottenplattans utförande: L-element L300, 200 mm cellplast under plattan och 200 mm hög kantbalk (300 med foten)
UTFORANDEN = {
    "L300": dict(H=300.0, t_eps=200.0, h_balk=200.0),
}

# ------------------------------------------------------------------ jord och fyllning
GAMMA_JORD = 18.0        # kN/m³, dränerande friktionsmaterial (krossat berg, grus)
FI_JORD = 40.0           # friktionsvinkel för dränerande kross [°]
K0 = 1 - math.sin(math.radians(FI_JORD))                                   # vilojordtryck
KA = (1 - math.sin(math.radians(FI_JORD))) / (1 + math.sin(math.radians(FI_JORD)))   # aktivt jordtryck
Q_MARK = 2.5             # kN/m², nyttig last på marken intill väggen (gångyta, trädgård), inga fordon närmare än 2 m
# Packning intill väggen (Ingold 1979): kvarstående horisontaltryck σ = √(2 P γ / π), P = vibroplattans linjelast
# (tyngd och centrifugalkraft per meter bredd). Gäller inom 1 m från väggen; längre ut får fyllningen packas tyngre.
VIBROPLATTA = dict(massa=100.0, F=15.0, b=0.5)     # kg, kN, m: lätt vibroplatta
P_PLATTA = (VIBROPLATTA["massa"] * 9.81e-3 + VIBROPLATTA["F"]) / VIBROPLATTA["b"]     # kN/m
SIG_KOMP = math.sqrt(2 * P_PLATTA * GAMMA_JORD / math.pi)                          # kPa
LAGER_FYLL = 0.2         # m, största lagertjocklek inom 1 m från väggen
# bakom V3 och V20: plattan på mark på plan 1 (K-05) med 400 mm cellplast
EPS_MARK = 400.0
H_FYLL_MARK = (H_VAGG - EPS_MARK) / 1000            # m, fyllning upp till cellplasten under plattan
G_MARK = 25 * 0.15 + 0.5 + 0.3 * EPS_MARK / 1000    # kN/m², betong, golv och cellplast
Q_MARK_PLATTA = 2.0 + 0.7                           # kN/m², nyttig last och lätta väggar
# byggskedet bakom V3 och V20, när plattan på mark gjuts: cellplasten (permanent) och färsk betong med arbetslast
# (SS-EN 1991-1-6 4.11.1), som nyttig last
G_BYGG = 0.3 * EPS_MARK / 1000
Q_BYGG = 25 * 0.15 + 1.5

# fyllnadshöjd (m) vid väggens ände a och b (a < b i väggens riktning, mitt i väggens centrumlinje)
# ändvillkor: "h" hörn eller T-anslutning (armeringen förs runt), "f" fri ände (öppning)
FYLL = {
    "V1": dict(h=(1.8, 1.8), ande=("h", "h")),
    "V2": dict(h=(2.0, 2.0), ande=("h", "h")),
    "V3": dict(h=(H_FYLL_MARK, H_FYLL_MARK), ande=("h", "h"), platta=True),
    "V7": dict(h=(2.0, 2.0), ande=("h", "h")),
    "V9": dict(h=(0.0, 0.8), ande=("f", "h")),
    "V14": dict(h=(0.8, 1.8), ande=("h", "h")),
    "V16": dict(h=(2.0, 2.0), ande=("h", "h")),
    "V18": dict(h=(2.0, 2.0), ande=("f", "h")),
    "V20": dict(h=(H_FYLL_MARK, H_FYLL_MARK), ande=("h", "h"), platta=True),
    "V21": dict(h=(2.0, 2.0), ande=("h", "h")),
    # Fasaden med öppningarna: under fönstren (bröstning 0,90 och 1,50 m) är väggen hel mellan hörnen vid V18 och
    # V17. Fyllningen 0,80 m (modellen) ligger mot den delen. Pelarna V10–V13 går upp till bjälklaget.
    "V10–V13": dict(h=(0.80, 0.80), ande=("h", "h"), fasad=dict(linje="V10", mellan=("V18", "V17"),
                                                                 omfattar=("V10", "V11", "V12", "V13"))),
}
BROSTNING = (0.80, 1.40)  # m, betongkärnans underkant i öppningarna över bottenplattan (modellen); smygen och
                          # bröstningen isoleras med 100 mm cellplast, färdig bröstning 0,90 och 1,50 m

# ------------------------------------------------------------------ källarväggarna: Sundolitt Kub 350-150 (U17)
KUB = dict(namn="Sundolitt Kub 350-150 (U17)", tg="SINTEF TG 2216", element=(1200.0, 600.0), halvt=300.0,
           eps="EPS 120 (EN 13163)")
# Betong enligt Sundolitt: B30 (NS-EN 206), största stenstorlek 16 mm, grovt ballast minskat 25 %, sättmått
# 180–200 mm. Räknas som C30/37.
FCK_V = 30.0
CEMENT = "N"             # cementklass enligt SS-EN 1992-1-1 3.1.2 (s = 0,25); R-cement (s = 0,20) går fortare
KRYP_V = 2.0             # slutligt kryptal för kärnan, belastad efter 28 dygn (SS-EN 1992-1-1 figur 3.1, inomhus/fuktig)
SVINN_V = 0.30e-3        # slutlig krympning: uttorkning RH 80 %, h0 = 150 mm, och autogen (SS-EN 1992-1-1 3.1.4)
# Armering B500B. Täckande betongskikt till de vågräta järnen, som ligger ytterst i elementens hållare.
C_IN, C_UT = 25.0, 30.0  # mot insidan (XC1) och mot utsidan, mot cellplast och jord (XC2), 50 år
ARM_H = dict(d=10, s=600, s_topp=300)     # 2 Ø10 per skift, ett vid var yta; s300 i de två översta skiften (TG 2216)
ARM_V = [(10, 300), (10, 200), (10, 150), (12, 150)]   # lodräta järn på insidan: TG 2216 anger Ø10 s300
STARTJARN = dict(d=10, s=300, ned=500, upp=1200)       # på utsidan, i kantbalken och upp i väggen (TG 2216)
SKARV = 500.0            # skarvlängd, och vinkeljärn 750 mm åt var håll i hörn (TG 2216)
VINKEL = dict(ned=650.0, in_=500.0)     # vinkeljärn till bjälklaget: ned i väggen och in under överkantsnätet (R-03)
OPPNING = dict(n=2, d=12, forankring=600)               # runt öppningar (TG 2216)
# Väggens egentyngd: kärna, cellplast och gips 13 mm. Fasadsten ovan mark på ytterväggarna (AR-01): granit 40 mm,
# fästmassa och armeringsbruk, från 50 mm under mark till mellanbjälklagets överkant.
G_KUB = 25 * T_KARNA / 1000 + 0.2 * 2 * T_EPS_V / 1000 + 0.11          # kN/m²
G_STEN = 1.3                                                             # kN/m²
H_GJUT1 = 1800.0         # första gjutningen: tre hela skift; det översta halva skiftet (300) gjuts med bjälklaget

# ------------------------------------------------------------------ cellplast (EPS-Sverige, WSP 10221233)
# karakteristisk tryckhållfasthet f_ck och E-modul E_k (kPa) enligt tabell 1.2.2a
EPS = {
    "S100": dict(fck=90.0, Ek=3000.0, kryp2=30.0),     # kryp2: långtidslast vid 2 % deformation (tillverkare)
    "S150": dict(fck=135.0, Ek=4500.0, kryp2=45.0),
    "S200": dict(fck=180.0, Ek=6000.0, kryp2=60.0),
    "S300": dict(fck=280.0, Ek=9000.0, kryp2=90.0),
}
# Cellplast: S100 under plattan, S300 under alla balkar och plintar (L-elementens fot under kantbalken, där väggens
# kärna står på balkens yttersta 150 mm). Bara två kvaliteter.
EPS_FALT, EPS_BALK = "S100", "S300"
EPS_GAMMA_M = 1.3        # med tillverkningskontroll
EPS_KR = {"P": (0.40, 0.45), "M": (0.50, 0.55), "S": (0.60, 0.65)}   # k_r för f_k < 200 resp. ≥ 200 kPa
EPS_KS = 0.40            # styvhet i bruksgränstillstånd för långtidslast (P, L)
