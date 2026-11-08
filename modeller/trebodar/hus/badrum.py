"""Badrummets planering (ärende #52, användarens skiss): inredningens lägen och golvets fall, som inredningen
(hus/inredning/badrum.py), golvet (hus/invandigt/badrumsgolv.py), tappvattnet, avloppet och elen läser. Varje läge
står här en gång, så att rummet itereras på ett ställe och allt annat följer med.

Rummet (BADRUM i hus/rum.py) mellan väggarnas färdiga ytor (kakel): gaveln 1NO och långsidan 1SO, de lätta väggarna L9
och L10 mot sovrummet och L11 mot allrummet med fickdörren ID1, de bärande 1A och 1B och nischen mellan 1B, 1C och
L11. Från skissen:

- **Duschen** i nischen, med två glasdörrar mot rummet i 1A:s linje och golvbrunnen i nischen.
- **Badkaret** fristående längs 1SO under takfönstret TF1, med en väggmonterad blandare på 1SO vid karets mitt (#97).
- **WC:n** golvstående mot L9, mitt för skissens.
- **Badrumsbänken** längs 1NO från 1SO till L9, med tvättstället mitt under fönstret 1NO-F1; spegeln på L9 mellan
  bänken och WC:n (#97).
- **Väggbiten** L19 från L11 fram till L9:s yta, i liv med ID1:s smyg, och det **inbyggda skåpet** i nischen mellan L10
  och L19 med fronten i L9:s yta, inklätt ovanför upp till innertaket (#98).
- **Handdukstorken** på 1A mellan badkaret och duschen.

Golvet: klinker på tätskikt och fix på en fallavjämning på mellanbjälklaget (som inte ändras: plattan är 150 mm med
armering i två lager och ingjutna rör, och röret P4 står under duschen). Fallet enligt GVK Säkra Våtrum 2026 (6.4):
i duschen mot golvbrunnen minst 7 och högst 30 mm/m, mellan brunnen och väggarna högst 40 mm/m, på övrig yta mot
duschen 2–10 mm/m och inget bakfall, och golvbrunnens fläns minst 20 mm under tätskiktets uppvik vid dörren (tröskeln).
Golvbrunnen står med flänsen i bjälklagets överkant; duschens golv är ett kuvert med fyra plan från brunnen upp till
duschens kant (FALL_DUSCH högre), och övrig yta lutar mot duschen: väster om 1B även mot öster, så att vattnet längs 1A
rinner mot duschen, och i skåpets nisch mot väster, ut ur nischen. Vattnet rinner aldrig mot dörren: golvet vid dörren
lutar längs väggen mot duschen, och tröskeln är högre.
"""
from __future__ import annotations

from dataclasses import dataclass

from shapely.geometry import Point, Polygon, box

from modellering import Form, Kapad

from trebodar import skelett as S
from trebodar.hus.fonster_och_dorrar.oppningar import DORRSMYG_T, INNERDORRAR, OPPNINGAR
from trebodar.hus.invandigt.lattvaggar import T, VAGGAR
from trebodar.hus.invandigt.skikt import INSIDA_VATRUM_T, SKIVOR_VATRUM_T

# ------------------------------------------------------------------ väggarnas färdiga ytor (kaklet)

X_1SO = S.YTTERVAGGAR["1SO"].origo[0] + S.T_STOMME + INSIDA_VATRUM_T
Y_1NO = S.YTTERVAGGAR["1NO"].origo[1] + S.T_STOMME + INSIDA_VATRUM_T
X_L9 = VAGGAR["L9"].origo[0] - T - SKIVOR_VATRUM_T
Y_L10 = VAGGAR["L10"].origo[1] + T + SKIVOR_VATRUM_T
X_L11 = VAGGAR["L11"].origo[0] - T - SKIVOR_VATRUM_T
Y_1A = S.INNERVAGGAR["1A"].origo[1] - SKIVOR_VATRUM_T
X_1B = S.INNERVAGGAR["1B"].origo[0] + SKIVOR_VATRUM_T
Y_1C = S.INNERVAGGAR["1C"].origo[1] - SKIVOR_VATRUM_T
Y_L19S = VAGGAR["L19"].origo[1] - SKIVOR_VATRUM_T                     # väggbitens sida mot skåpet
Y_L19N = VAGGAR["L19"].origo[1] + T + SKIVOR_VATRUM_T                 # och mot dörren

ID1 = next(d for d in INNERDORRAR if d.kod == "ID1")
Y_DORR = (VAGGAR["L11"].origo[1] + ID1.u0, VAGGAR["L11"].origo[1] + ID1.u1)       # dörröppningen längs L11
assert abs(Y_L19N - (Y_DORR[0] + DORRSMYG_T)) < 0.01, "väggbiten L19 i liv med ID1:s smyg"
F1 = next(o for o in OPPNINGAR["1NO"] if o.kod == "1NO-F1")
X_FONSTER = S.YTTERVAGGAR["1NO"].origo[0] + (F1.u0 + F1.u1) / 2      # fönstrets mitt över bänken
Z_FONSTER = F1.z0                                                      # fönstrets underkant (regelverkets öppning)

# ------------------------------------------------------------------ golvet

KLINKER_T = 9.0                    # Bricmate J66 Jura Select 60 × 60, 9 mm
TATSKIKT_T = 5.0                   # tätskikt och fix
BYGGHOJD = KLINKER_T + TATSKIKT_T  # golvets ytskikt över fallavjämningen (och över brunnens fläns)
GOLVBRUNN = (2440.0, 7390.0)       # brunnens mitt: 272 mm från 1B och 290 mm innanför dörrarna
BRUNN_Z = BYGGHOJD                 # golvet vid brunnen: flänsen i bjälklagets överkant
FALL_DUSCH = 8.0                   # duschens kant över brunnen
Y_DUSCH = Y_1A + 23.0              # glasdörrarnas linje, duschens kant mot rummet
FALL_OVRIGT = 0.0025               # övrig yta mot duschen [mm/mm]: mot norr och väster om 1B mot öster
FALL_NISCH = 0.0025                # skåpets nisch mot väster

Plan3 = tuple[float, float, float]     # z = a x + b y + c


@dataclass(frozen=True)
class Fallyta:
    """En plan del av golvet: ytan i plan och planet för golvets färdiga yta (z = a x + b y + c)."""
    namn: str
    yta: Polygon
    plan: Plan3

    def z(self, x: float, y: float) -> float:
        a, b, c = self.plan
        return a * x + b * y + c


def _plan_genom(p: tuple[float, float, float], q: tuple[float, float, float], r: tuple[float, float, float]) -> Plan3:
    """Planet z = a x + b y + c genom tre punkter."""
    (x1, y1, z1), (x2, y2, z2), (x3, y3, z3) = p, q, r
    d = (x2 - x1) * (y3 - y1) - (x3 - x1) * (y2 - y1)
    a = ((z2 - z1) * (y3 - y1) - (z3 - z1) * (y2 - y1)) / d
    b = ((x2 - x1) * (z3 - z1) - (x3 - x1) * (z2 - z1)) / d
    return a, b, z1 - a * x1 - b * y1


Z_DUSCH = BRUNN_Z + FALL_DUSCH       # duschens kant och övrig yta vid duschen


def _fallytor() -> tuple[Fallyta, ...]:
    xb, yb = GOLVBRUNN
    hornen = [(X_1B, Y_DUSCH), (X_L11, Y_DUSCH), (X_L11, Y_1C), (X_1B, Y_1C)]
    kuvert = []
    for namn, (p, q) in zip(("fram", "öster", "bak", "väster"), zip(hornen, hornen[1:] + hornen[:1])):
        plan = _plan_genom((xb, yb, BRUNN_Z), (*p, Z_DUSCH), (*q, Z_DUSCH))
        kuvert.append(Fallyta(f"dusch {namn}", Polygon([(xb, yb), p, q]), plan))
    # övrig yta: öster om 1B mot norr (mot duschen), väster om 1B också mot öster; skåpets nisch dessutom mot väster
    ost = (0.0, -FALL_OVRIGT, Z_DUSCH + FALL_OVRIGT * Y_DUSCH)
    vast = (-FALL_OVRIGT, -FALL_OVRIGT, Z_DUSCH + FALL_OVRIGT * (Y_DUSCH + X_1B))
    nisch = (FALL_NISCH, -FALL_OVRIGT, Z_DUSCH + FALL_OVRIGT * Y_DUSCH - FALL_NISCH * X_L9)
    return (*kuvert,
            Fallyta("rummet", Polygon([(X_1SO, Y_1NO), (X_1B, Y_1NO), (X_1B, Y_1A), (X_1SO, Y_1A)]), vast),
            Fallyta("vid duschen", Polygon([(X_1B, Y_1NO), (X_L9, Y_1NO), (X_L9, Y_L19N), (X_L11, Y_L19N),
                                            (X_L11, Y_DUSCH), (X_1B, Y_DUSCH)]), ost),
            Fallyta("nischen", Polygon([(X_L9, Y_L10), (X_L11, Y_L10), (X_L11, Y_L19S), (X_L9, Y_L19S)]), nisch))


FALLYTOR = _fallytor()


def golvniva(x: float, y: float) -> float:
    """Golvets färdiga yta (klinkern) i punkten, över bjälklagets överkant."""
    p = Point(x, y)
    for f in FALLYTOR:
        if f.yta.buffer(1e-6).contains(p):
            return f.z(x, y)
    raise ValueError(f"({x:g}, {y:g}) är inte på badrummets golv")


def hogsta_golv(x0: float, x1: float, y0: float, y1: float) -> float:
    """Golvets högsta nivå under rektangeln (inredning som står på golvet: den högsta foten)."""
    return max(golvniva(x, y) for x in (x0, x1) for y in (y0, y1))


def lagsta_golv(x0: float, x1: float, y0: float, y1: float) -> float:
    """Golvets lägsta nivå under rektangeln."""
    return min(golvniva(x, y) for x in (x0, x1) for y in (y0, y1))


def pa_golvet(form: Form, x0: float, x1: float, y0: float, y1: float) -> Form:
    """Formen kapad efter golvets yta under rektangeln (det som står på golvet följer fallet): golvets plan är dalar
    mot brunnen, så golvet är det högsta av de plan som rektangeln ligger över."""
    r = box(x0, y0, x1, y1)
    for f in FALLYTOR:
        if f.yta.intersects(r) and f.yta.intersection(r).area > 1.0:
            a, b, c = f.plan
            form = Kapad(form, (x0, y0, a * x0 + b * y0 + c), (a, b, -1.0))
    return form


# ------------------------------------------------------------------ inredningen

# duschen: två glasdörrar 8 mm i Y_DUSCH mellan 1B och L11, hängda i väggarna, utåtgående; blandaren på 1C (där
# tappvattnets väggdosa sitter, vatten/rum/badrum.py) och takduschen och handduschen på en stång ovanför
DUSCHDORR_T, DUSCHDORR_H, DUSCHDORR_SPEL = 8.0, 2000.0, 8.0
X_DUSCHBLANDARE = (X_1B + X_L11) / 2       # blandarens mitt på 1C, mitt i nischen (#97; kanalen FF3 öster om den)
Z_DUSCHBLANDARE = 1000.0
Z_TAKDUSCH = 2150.0                         # takduschens underkant över golvet

# badkaret: fristående, ovalt, längs 1SO under takfönstret TF1, BADKAR_VAGG från väggen; blandaren på 1SO mitt för
# karet med pipen ut över kanten (#97)
BADKAR = (1700.0, 800.0, 600.0)             # längd, bredd, höjd
BADKAR_KAR = 60.0                           # karets botten över badkarets underkant
BADKAR_VAGG = 120.0
BADKAR_Y = (5200.0, 5200.0 + BADKAR[0])     # längs 1SO
BADKAR_X = (X_1SO + BADKAR_VAGG, X_1SO + BADKAR_VAGG + BADKAR[1])
BADKARSBLANDARE = (X_1SO, 6220.0)            # på 1SO:s kakel, 170 mm från karets mitt mot 1A: där rören går fria mellan
#                                              källarväggens och överkantsnätets järn och förbi karets avlopp
Z_BADKARSBLANDARE = 800.0                    # blandarens mitt över golvet (karets kant 600)
BADKARSPIP = 290.0                           # pipen från kaklet, ut över karets kant

# WC:n golvstående med S-lås mot L9, mitt som i skissen; avloppet i golvet WC_AVLOPP från väggen
WC_Y = 4980.0
WC = (360.0, 650.0, 800.0)                  # bredd, djup, höjd (cisternen)
WC_AVLOPP = 190.0

# badrumsbänken längs 1NO från 1SO till L9: skåp av björkplywood med dörrar av fräst ask som köket, bänkskiva
# Bricmate Jura 12 och tvättstället undermonterat mitt under fönstret 1NO-F1
BANK_X = (X_1SO, X_L9)
BANK_DJUP = 500.0                           # bänkskivan, från 1NO
BANK_Z = 850.0                              # bänkskivans överkant över golvet
BANKSKIVA_T = 12.0
TVATTSTALL = (480.0, 300.0, 150.0)          # tvättställets insida: längs bänken, tvärs, djup
TVATTSTALL_GODS = 10.0                      # förenklat
X_TVATTSTALL = X_FONSTER

# spegeln på L9 mellan bänken och WC:n (#97); lampan över tvättstället på 1NO ovanför fönstret
SPEGEL = (Y_1NO + BANK_DJUP + 30.0, WC_Y - WC[0] / 2 - 30.0, 1050.0, 1850.0)   # y0, y1 (bänken, WC:n), z0, z1
LAMPA_TVATTSTALL = (X_TVATTSTALL, 2300.0)    # x, z

# skåpet i nischen mellan L10 och väggbiten L19, fronten i L9:s yta
SKAP_X = (X_L9, X_L11)
SKAP_Y = (Y_L10, Y_L19S)
SKAP_Z = 2100.0                             # skåpets överkant över golvet, som dörrarna

# tvätten i skåpet (#51), förberedd för en tvättmaskin och en torktumlare staplade (600 × 600, 1 750 höga med
# staplingssatsen) mot L19: vattnets väggdosa med avstängningen och avloppets vattenlås på L10 i glipan bredvid dem,
# och dubbeluttaget på L10 ovanför dem (användarens markering)
TVATT = (600.0, 600.0, 1750.0)              # maskinerna: bredd, djup, höjd staplade
TVATT_VATTEN = (2750.0, 1100.0)             # x, z över golvet
TVATT_AVLOPP = (3050.0, 650.0)
TVATT_UTTAG = (2950.0, 1950.0)
assert SKAP_Y[1] - SKAP_Y[0] >= TVATT[0] + 150.0, "skåpet rymmer maskinerna och glipan för anslutningarna"
assert SKAP_X[1] - SKAP_X[0] >= TVATT[1] + 100.0, "skåpet rymmer maskinerna och slangarna bakom dem"
assert SKAP_Z >= TVATT[2] + 300.0, "uttaget ryms ovanför maskinerna"

# handdukstorken på 1A mellan badkaret och duschen
HANDDUKSTORK = (1400.0, 1900.0, 400.0, 1600.0)     # x0, x1, z0, z1 över golvet

assert BADKARSPIP > BADKAR_VAGG + 60.0, "badkarets pip når ut över karets kant"
assert SPEGEL[0] >= Y_1NO + BANK_DJUP and SPEGEL[1] <= WC_Y - WC[0] / 2, "spegeln mellan bänken och WC:n"

# nivåer som inredningen och avloppet delar: golvet under bänken och badkaret (de står på dess högsta punkt),
# tvättställets och karets botten
Z_BANK = hogsta_golv(*BANK_X, Y_1NO, Y_1NO + BANK_DJUP)
Z_TVATTSTALL_BOTTEN = Z_BANK + BANK_Z - BANKSKIVA_T - TVATTSTALL[2] - TVATTSTALL_GODS
Z_BADKAR = hogsta_golv(*BADKAR_X, *BADKAR_Y)
