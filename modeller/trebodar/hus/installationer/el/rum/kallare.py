"""Källaren (#51): belysningen, uttagen i alla rum, tvättstugans maskiner och fläkten FF3:s anslutning, efter
användarens indelning av rummen, 3000 K.

Belysningen:
- Arbetsrummen (kostnaden styr): tunna utanpåliggande LED-paneler LEDVANCE PANEL COMPACT 600 (../katalog.py), var och
  en ansluten i en ingjuten dosa ovanför sig, mellan underkantsnätets järn och fri från rören i bjälklaget och pelarnas
  genomstansningszoner: sex i det stora rummet i högra huskroppen (öster om KL5 och KL7) och en i vart och ett av de
  två små rummen norr om KL1 (väster och öster om KL2). Rummen och hur de motsvarar användarens (antaget, ärende
  #51): det stora rummet på nordvästra sidan är det stora rummet, det lilla rummet i sydostliga änden de två små
  rummen.
- De trevliga rummen (trapphallen, tvättstugan, de två små rummen söder om V4–V6 och rummet norr om trapphallen):
  ljuslinjer i ask utanpå betongtaket (../katalog.ljuslinje, egen tillverkning, #51): en askprofil 56 × 22 med ett
  fräst spår underifrån, en aluminiumkanal i spåret, en COB-LED-list 24 V (Ra ≥ 97, R9 > 90, 3000 K) och en opal
  diffusor klippt i kanalen. Linjerna följer rummen och hur de används (LINJER), parallella med väggarna: längs
  trapphallen och en tvärs ned mot trappans fot, längs tvättstugans hall och en över bänken vid V21, en mitt i var och
  en av de två delarna söder om V4–V6 och två parallella i rummet norr om trapphallen, minst 500 mm från
  brandvarnarna. Ingen dosa i taket: 24 V går i egna ingjutna rör, skilda från 230 V-rören, som slutar i taket under
  profilens ände (rörändan pluggas och tätas vid gjutningen och täcks helt av armaturen); båda rörändarna står mellan
  underkantsnätets järn och fria från rören i bjälklaget (_placera), och ledaren går genom profilen till nästa linje.
  Drivdonen (24 V CV, fasdimbara med bakkant, ett per tändgrupp) sitter i drivdonsskåpet TK-LC på KL8 i teknikrummet
  (../../teknikrum.py), åtkomligt; vanliga vriddimrar vid ingångarna dimrar dem (DIMRAR; de två små rummen har ingen
  vägg emellan i modellen och är två tändgrupper på två dimrar i en dubbelram), och den dimrade fasen går i ett eget
  rör från varje dimmer till skåpet. Kretsarna (KRETSAR), ledarnas area och spänningsfallet: installation.py.
- Teknikrummet får ingen belysning nu.
- Brytarna och dimrarna sitter vid dörrarna, 1 050 mm över golvet; rören går rakt upp ur deras dosor, sida vid sida,
  i KL-väggarnas regelfack in i bjälklaget och ingjutna där, raka och sneda med mjuka böjar (#87,
  ../bjalklag/ingjutna.py), helst i elrörens undre nivå (under plan 1:s rör). Det stora rummet (G17): gruppens rör
  från den bakre raden över centralen (../bjalklag/mellanbjalklag.py) till en ingjuten kopplingsdosa i rummets tak
  (KA-D1), och därifrån till brytaren på KL7 och till panelerna. De andra rummen (G18): gruppens rör från den främre
  raden och ned i KL1 till det västra lilla rummets brytare, därifrån till rummets panel och genom bjälklaget till det
  östra rummets brytare och panel, och vidare till dimrarna i tur och ordning. Drivdonsskåpets rör (den dimrade fasen
  från dimrarna och 24 V till ljuslinjerna) går rakt upp ur skåpets ovansida i en rad och i knippen i elrörens undre
  nivå, norrut och söderut ur raden, där vart och ett viker av mot sin dimmer eller ljuslinje; G18:s rör mellan
  dimrarna går helst i den övre nivån, över knippena.

Uttagen (dubbla, i arbetsrummen, tvättstugan och teknikrummet 1 100 mm över golvet, i de trevliga rummen 250 mm) och
anslutningarna sitter på källarväggarna och KL-väggarna; rören går i källarväggarnas cellplast bakom gipsen och i
KL-väggarnas regelfack, vågrätt i golvzonen (Z_GOLVZON, under tappställenas rör) och upp eller ned till uttagen:
- tvättstugan (G20: två IP44 på V3; G21 och G22: tvättmaskinens och torktumlarens på V21 vid KA-TM1) ur centralens
  baksida i V3:s cellplast (teknikrummets uttag G19 i rum/teknikrum.py);
- de små rummen norr om KL1, rummet norr om trapphallen och trapphallen (G23): ur centralens baksida västerut i V3:s,
  norrut i V21:s och österut i V7:s cellplast, runt hörnet in i V18:s, och upp i V7:s och in i KL3:s och KL4:s
  regelfack, över dörren KD3;
- det stora rummet, rummen vid V2 och fläkten FF3 (G24): gruppens rör genom bjälklaget till fläktens anslutning på
  V20, därifrån genom bjälklaget till V15 och i V15:s, V16:s, V1:s och V14:s cellplast mellan det stora rummets uttag
  (under det stora rummets uttag), och i V20:s och V2:s till rummen vid V2.

Koordinater i mm (K-05), z från plan 1:s golv (källarens golv z −2 250).
"""
from __future__ import annotations

import math
from collections.abc import Sequence
from functools import cache

from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

from trebodar.hus.grund import kallarvaggar as K
from trebodar.hus.grund.pelare import PELARE
from trebodar.hus.invandigt.kallarens_innervaggar import GIPS_T, VAGGAR as KL

from ...avlopp.ledningar import ledningar as avloppets
from ...montering import BJALKLAG, KALLARTAK, PLAN, Montering, Vek, kallartak
from ...plattan import SVANG
from ...strak import fri, mellan_jarnen
from ...vatten.system import vatten
from .. import kedjor
from ..bjalklag import mellanbjalklag as MB
from ..bjalklag.ingjutna import (KALLAREN, NIVAER, PLAN1, Ingjutning, genom_nivan, golvvarmens_strak, hinder,
                                i_nivan, kartor_el, knippe,
                                upptaget_av)
from ..katalog import (ANSLUTNING, ASKPROFIL, BRYTARE_1, DIMMER_LED, DIMMER_LED_2, FXP16, INGJUTNINGSDOSA,
                       PANEL_600, UTTAG_1_IP44, UTTAG_2, UTTAG_2_IP44, ljuslinje)
from ...montering import kallarvagg
from ...teknikrum import DRIVDONSSKAP, GC_MATT, X_GC, Z_GC_TOPP
from . import teknikrum
from ..punkter import Apparat, Dosa, Krets, Lampa, Punkt, Ror, Rum, Tandgrupp, anslutning

from . import kallarens_punkter as KP
from .kallarens_punkter import (BRYTARE, D_STORA, DOSOR, PANELER, S6, S_D2, SPEL, UTTAG_KS, UTTAG_SMA, UTTAG_STORA,
                                UTTAG_V2, X_TVATT_UTTAG, X_UTTAG_KL4, Y_FF3, Y_MASKINER, Y_UTTAG_KL3, Z_BRYTARE, Z_FF3,
                                Z_GOLVZON, KL_GIPSYTA, V_GIPSYTA, vaggens_c, pa_kl, panelens, xy, ned_i_dosan, stigarna, ur_dosan)

RUM, NAMN = KP.RUM, KP.NAMN
TANDGRUPPER = [*KP.TANDGRUPPER]
PUNKTER: list[Punkt] = [*KP.PUNKTER]


# ------------------------------------------------------------------ rören i väggarna


def _ror(id_: str, fran: str, till: str, via: Sequence[Vek]) -> Ror:
    """Röret genom via (i väggarna), utan punkter som upprepas."""
    ut: list[Vek] = []
    for q in via:
        if not ut or math.dist(q, ut[-1]) > 0.5:
            ut.append(q)
    return Ror(id_, FXP16, fran, till, via=tuple(ut))


def _eps(v: str) -> float:
    """Källarväggens cellplast mot rummet: mittens läge tvärs väggen (x för väggar längs y, y för väggar längs x)."""
    w = next(q for q in K.VAGGAR if q.namn == v)
    sida = {"V15": 1, "V16": 1, "V20": 1, "V18": 1, "V21": 1, "V7": 1, "V4": 1, "V1": -1, "V14": -1, "V2": -1,
            "V3": -1}[v]
    return w.c + sida * (K.KARNA / 2 + K.CELL / 2)


def _i_cellplasten(v: str, s_: float) -> tuple[float, float]:
    """Punkten i plan mitt i källarväggens cellplast (mot rummet) vid s_ längs väggen."""
    w = next(q for q in K.VAGGAR if q.namn == v)
    return (s_, _eps(v)) if w.riktning == "h" else (_eps(v), s_)


_V3_EPS, _V21_EPS, _V7_EPS = _eps("V3"), _eps("V21"), _eps("V7")      # mitt i cellplasten bakom gipsen
_ZU = teknikrum.Z_UTTAG + PLAN[0]
_X_UT = X_GC - GC_MATT[0] / 2                            # centralens västra ände


def _tvatten(n: int, x0: float, dz: float) -> tuple[Vek, ...]:
    """Röret till maskinens uttag n (0 tvättmaskinen, 1 torktumlaren): ur centralens baksida i V3:s cellplast
    västerut dz under uttagens höjd, runt hörnet in i V21:s och norrut till uttaget."""
    y = Y_MASKINER[n]
    return (*teknikrum.bakifran(x0, _ZU - dz), (_V21_EPS, _V3_EPS, _ZU - dz), (_V21_EPS, y, _ZU - dz), (_V21_EPS, y, _ZU))


_ZG = PLAN[0] + Z_GOLVZON


def _sma_uttagen() -> list[Ror]:
    """De små rummens uttag (G23): gruppens rör ur centralens baksida, ned i V3:s cellplast till golvzonen, västerut
    och runt hörnet norrut i V21:s till det första uttaget; därifrån rören mellan uttagen i golvzonen i V21:s och
    V7:s cellplast, var och ett upp till sitt uttag (rören som går vidare ned 30 mm bredvid)."""
    x0 = _X_UT + 100.0
    u0 = _i_cellplasten(*UTTAG_SMA[0][:2])
    ut = [_ror("G23-M", "GC", "KA-U5", (*teknikrum.bakifran(x0, _ZU - 150.0), (x0, _V3_EPS, _ZG),
                                        (_V21_EPS, _V3_EPS, _ZG), (u0[0], u0[1], _ZG), (u0[0], u0[1], _ZU)))]
    for i, ((va, sa, _), (vb, sb, _)) in enumerate(zip(UTTAG_SMA, UTTAG_SMA[1:])):
        riktning = -1.0 if va == "V21" else 1.0                  # norrut längs V21, österut längs V7
        a = _i_cellplasten(va, sa + 30.0 * riktning)
        b = _i_cellplasten(vb, sb)
        horn = [(_V21_EPS, _V7_EPS, _ZG)] if va != vb else []
        ut.append(_ror(f"G23-R{i + 1}", f"KA-U{i + 5}", f"KA-U{i + 6}",
                       ((a[0], a[1], _ZU), (a[0], a[1], _ZG), *horn, (b[0], b[1], _ZG), (b[0], b[1], _ZU))))
    # vidare österut i V7:s cellplast förbi KL3:s ände och runt hörnet norrut i V18:s, till rummet norr om
    # trapphallen (uttagen i golvzonen)
    a = _i_cellplasten("V7", UTTAG_SMA[-1][1] + 30.0)
    v18 = _eps("V18")
    ut.append(_ror("G23-R4", "KA-U8", "KA-U13", ((a[0], a[1], _ZU), (a[0], a[1], _ZG), (v18, _V7_EPS, _ZG),
                                                 (v18, UTTAG_KS[0][1], _ZG))))
    ut.append(_ror("G23-R5", "KA-U13", "KA-U14", ((v18, UTTAG_KS[0][1], _ZG), (v18, UTTAG_KS[1][1], _ZG))))
    # trapphallen: från det östra lilla rummets andra uttag upp i V7:s cellplast till strax under taket, österut till
    # KL3 och i dess regelfack söderut över dörren KD3 till uttaget på KL3; därifrån lägre (där inga dörrar är)
    # norrut till KL4 och österut i dess regelfack till uttaget där
    kl3, kl4 = KL["KL3"].c, KL["KL4"].c
    zh, zl = KALLARTAK - 60.0, KALLARTAK - 110.0
    a = _i_cellplasten("V7", UTTAG_SMA[-1][1] - 30.0)
    ut.append(_ror("G23-R6", "KA-U8", "KA-U18", ((a[0], a[1], _ZU), (a[0], a[1], zh), (kl3, _V7_EPS, zh),
                                                 (kl3, Y_UTTAG_KL3, zh), (kl3, Y_UTTAG_KL3, _ZG))))
    ut.append(_ror("G23-R7", "KA-U18", "KA-U17", ((kl3, Y_UTTAG_KL3 - 30.0, _ZG), (kl3, Y_UTTAG_KL3 - 30.0, zl),
                                                  (kl3, kl4, zl), (X_UTTAG_KL4, kl4, zl), (X_UTTAG_KL4, kl4, _ZG))))
    return ut


def _stora_uttagen() -> list[Ror]:
    """Det stora rummets uttag (G24) i golvzonen i V15:s, V16:s, V1:s och V14:s cellplast mellan uttagen, och rummen vid
    V2 från fläktens anslutning ned i V20:s cellplast. Gruppens rör från centralen till fläktens anslutning och därifrån
    till det första uttaget går i bjälklaget (nedan)."""
    ut = []
    hornen = {("V15", "V1"): (_eps("V16"), _eps("V1")), ("V1", "V14"): (_eps("V14"), _eps("V1"))}
    for i, ((va, sa, _), (vb, sb, _)) in enumerate(zip(UTTAG_STORA, UTTAG_STORA[1:])):
        riktning = -1.0 if (va, vb) == ("V14", "V14") else 1.0
        a = (_eps(va), sa + 30.0 * riktning) if va in ("V15", "V14") else (sa + 30.0, _eps(va))
        b = (_eps(vb), sb) if vb in ("V15", "V14") else (sb, _eps(vb))
        horn = [(*hornen[(va, vb)], _ZG)] if (va, vb) in hornen else []
        ut.append(_ror(f"G24-R{i + 2}", f"KA-U{i + 9}", f"KA-U{i + 10}",
                       ((a[0], a[1], _ZU), (a[0], a[1], _ZG), *horn, (b[0], b[1], _ZG), (b[0], b[1], _ZU))))
    # rummen vid V2: från fläktens anslutning ned i V20:s cellplast till golvzonen, söderut och runt hörnet österut i
    # V2:s till uttagen (i golvzonen)
    v20, v2 = _eps("V20"), _eps("V2")
    ut.append(_ror("G24-R5", "KA-D2", "KA-U15", ((v20, Y_FF3 - 30.0, PLAN[0] + Z_FF3), (v20, Y_FF3 - 30.0, _ZG),
                                                 (v20, v2, _ZG), (UTTAG_V2[0][1], v2, _ZG))))
    ut.append(_ror("G24-R6", "KA-U15", "KA-U16", ((UTTAG_V2[0][1], v2, _ZG), (UTTAG_V2[1][1], v2, _ZG))))
    return ut


ROR: list[Ror] = [
    *_sma_uttagen(),
    *_stora_uttagen(),
    # tvättstugan: uttagen på V3 (G20) och maskinernas (G21, G22) ur centralens baksida västerut i V3:s cellplast,
    # under uttagen (torktumlaren 50 mm, tvättmaskinen 100 mm, så att rören inte korsar varandra vid V21)
    _ror("G20-M", "GC", "KA-U1", (*teknikrum.bakifran(_X_UT + 20.0, _ZU), (X_TVATT_UTTAG[0], _V3_EPS, _ZU))),
    _ror("G20-R1", "KA-U1", "KA-U2", ((X_TVATT_UTTAG[0], _V3_EPS, _ZU), (X_TVATT_UTTAG[1], _V3_EPS, _ZU))),
    _ror("G21-M", "GC", "KA-U3", _tvatten(0, _X_UT + 40.0, 100.0)),
    _ror("G22-M", "GC", "KA-U4", _tvatten(1, _X_UT + 60.0, 50.0)),
]


# ------------------------------------------------------------------ de trevliga rummen: ljuslinjerna, dimrarna och drivdonen

# rummen (golvets yta innanför väggarnas gips): trapphallen öster om KL3 (utan trappan mellan KL4 och KL6),
# tvättstugan (hallen mellan KL1 och KL8 och rummet vid V3 väster om KL8), rummen söder om V4–V6 (en yta utan vägg
# emellan, belyst som två delar) och rummet norr om trapphallen (norr om KL4)
TRAPPHALL = box(KL["KL3"].c + KL_GIPSYTA, KL["KL4"].c + KL_GIPSYTA, KL["KL7"].c - KL_GIPSYTA, vaggens_c("V5") - V_GIPSYTA).difference(
    box(KL["KL6"].a - 60.0, KL["KL4"].c, KL["KL7"].c, KL["KL6"].c + KL_GIPSYTA))
TVATTSTUGA = unary_union([box(vaggens_c("V21") + V_GIPSYTA, KL["KL1"].c + KL_GIPSYTA, KL["KL8"].a, vaggens_c("V3") - V_GIPSYTA),
                          box(KL["KL8"].a, KL["KL1"].c + KL_GIPSYTA, KL["KL3"].c - KL_GIPSYTA, KL["KL10"].c - KL_GIPSYTA)])
RUMMEN_V2 = box(vaggens_c("V19") + V_GIPSYTA, vaggens_c("V5") + V_GIPSYTA, vaggens_c("V15") - V_GIPSYTA, vaggens_c("V2") - V_GIPSYTA)
RUMMET_KS = unary_union([box(vaggens_c("V18") + V_GIPSYTA, vaggens_c("V10") + V_GIPSYTA, KL["KL5"].c - KL_GIPSYTA, KL["KL4"].c - KL_GIPSYTA),
                         box(KL["KL3"].c + KL_GIPSYTA, vaggens_c("V7") + V_GIPSYTA, vaggens_c("V18") + V_GIPSYTA, KL["KL4"].c - KL_GIPSYTA)])

TANDGRUPPER += [
    Tandgrupp("KA-T1", "Källaren, trapphallen"),
    Tandgrupp("KA-T2", "Källaren, tvättstugan"),
    Tandgrupp("KA-T3", "Källaren, rummen söder om V4–V6, västra delen"),
    Tandgrupp("KA-T4", "Källaren, rummen söder om V4–V6, östra delen"),
    Tandgrupp("KA-T5", "Källaren, rummet norr om trapphallen"),
]

# dimrarna vid ingångarna, 1 050 mm över golvet: trapphallens vid trappans fot (på KL4 mellan pelarna P12 och P13),
# tvättstugans vid KD2, de två delarnas (två dimrar i en dubbelram) på V4 vid öppningen mellan V4 och V5, och rummet
# norr om trapphallen vid KD4 (väster om pelaren P11 i KL4); de på KL4 så långt från pelarna att rören upp ur dem går
# in i bjälklaget utanför pelarnas kontrollsnitt för genomstansning (#87). De dimrar drivdonen i teknikrummet: den
# dimrade fasen går i ett eget rör dit (230 V dimrad).
DIMRAR = {
    "KA-B1": Apparat("KA-B1", DIMMER_LED, pa_kl("KL4", 7250.0, 1), styr=("KA-T1",)),
    "KA-B2": Apparat("KA-B2", DIMMER_LED, pa_kl("KL3", 6100.0, -1), styr=("KA-T2",)),
    "KA-B3": Apparat("KA-B3", DIMMER_LED_2, kallarvagg("V4", 5150.0, Z_BRYTARE - PLAN[0], 1), styr=("KA-T3", "KA-T4")),
    "KA-B4": Apparat("KA-B4", DIMMER_LED, pa_kl("KL4", 5420.0, -1), styr=("KA-T5",)),
}

# ljuslinjerna (../katalog.ljuslinje) per tändgrupp, matade i rörens ordning från drivdonet: id, längd, önskad mitt och
# riktning från matningens ände. Längderna: den lysande längden en multipel av 150 mm, så att listen (klippbar var
# 50 mm) räcker hela vägen och rörändarna i båda ändar ryms mellan underkantsnätets järn (c/c 150). Lägena följer
# rummen och hur de används, minst 500 mm från brandvarnarna.
LINJER: dict[str, list[tuple[str, float, tuple[float, float], tuple[float, float]]]] = {
    # trapphallen: en linje längs hallens axel från dörren KD2 mot korridoren till KD5, mitt för öppningarna mot
    # rummen söder om V4–V6, och en tvärs ned mot trappans fot, som lyser upp de nedersta stegen (väster om trapphålet
    # och brandvarnaren BV-KT); var sitt rör från drivdonet
    "KA-T1": [("KA-L01", 3080.0, (6650.0, 6650.0), (1.0, 0.0)), ("KA-L02", 1430.0, (7130.0, 5870.0), (0.0, -1.0))],
    # tvättstugan: en linje längs hallen och en över bänken längs V21 med tvätthoet, tvättmaskinen och torktumlaren
    # (över bänkens främre halva, 600 djup: ljuset på bänken framför den som står där)
    "KA-T2": [("KA-L03", 3080.0, (2400.0, 6545.0), (-1.0, 0.0)), ("KA-L04", 1580.0, (760.0, 8150.0), (0.0, 1.0))],
    # rummen söder om V4–V6: en linje mitt i vardera delen, längs rummen
    "KA-T3": [("KA-L05", 2480.0, (5920.0, 9190.0), (0.0, 1.0))],
    "KA-T4": [("KA-L06", 2480.0, (8280.0, 9190.0), (0.0, 1.0))],
    # rummet norr om trapphallen: två parallella linjer längs rummet, symmetriskt mellan V18 och KL5, på var sin sida
    # om brandvarnaren BV-KN
    "KA-T5": [("KA-L07", 3080.0, (5770.0, 2530.0), (0.0, -1.0)), ("KA-L08", 3080.0, (8070.0, 2530.0), (0.0, 1.0))],
}
_RUMMET = {"KA-T1": TRAPPHALL, "KA-T2": TVATTSTUGA, "KA-T3": RUMMEN_V2, "KA-T4": RUMMEN_V2, "KA-T5": RUMMET_KS}
_STJARNA = {"KA-L02"}                         # matas med ett eget rör från drivdonet, inte från linjen före
_R = FXP16.ytterdiameter / 2


# ------------------------------------------------------------------ rören i bjälklaget (#87)
#
# Rören går raka och sneda direkt mellan stigarna, med mjuka böjar, runt det de inte får gå genom (../bjalklag/ingjutna.py),
# helst i elrörens undre nivå (under plan 1:s rör), och dras i tur och ordning: varje rör går runt de tidigare och deras
# stigare. Arbetsrummen först (deras rör och paneler), sedan ljuslinjerna, som placeras fria från dem, och sist
# dimrarnas rör och drivdonsskåpets.

_ING = Ingjutning([*MB.STIGARE, *kedjor.STIGARE], DOSOR, [*MB.ROR, *kedjor.ROR])
FRITT_STRAK = 100.0                          # rören går inte lodrätt genom golvvärmens nivå så nära dess stråk
_PK: dict[str, Punkt] = {p.id: p for p in PUNKTER}


def _dra(id_: str, fran: str, till: str, a: tuple[float, float], b: tuple[float, float],
         fore: Sequence[Vek] = (), efter: Sequence[Vek] = (), slag: str = "230 V",
         kost: tuple[float, float] = KALLAREN) -> Ror:
    """Röret genom bjälklaget (helst i den undre nivån, under plan 1:s rör), i den undre nivån in i en ingjuten dosa
    (från sidan) och ned i en vägg intill golvvärmens stråk, så att det inte går lodrätt genom golvvärmens nivå där."""
    def niva(p: tuple[float, float]) -> tuple[str, ...]:
        return ("MB-UK",) if any(math.dist(p, d[:2]) < 1.0 for d in DOSOR) or \
            golvvarmens_strak().distance(Point(p)) < FRITT_STRAK else NIVAER
    return _ING.dra(id_, FXP16, fran, till, a, b, fore=fore, efter=efter, slag=slag, kost=kost,
                    nivaer=(niva(a), niva(b)))


# det stora rummet (G17): gruppens rör från centralen till kopplingsdosan KA-D1 i rummets tak, därifrån till brytaren
# på KL7 (stigarna norr om brytaren, i regelfacket bort från dörren KD5) och till panelerna, i rader
_B5 = BRYTARE["KA-B5"]
_S5 = stigarna(_B5, [D_STORA, panelens(PANELER[2])], -100.0)          # från KA-D1, till KA-P03
_P01, _P02, _P03, _P04, _P05, _P06, _P07, _P08 = (panelens(p) for p in PANELER)
# de små rummen (G18): gruppens rör från centralen ned i KL1 till det västra rummets brytare, därifrån till dess panel och
# till det östra rummets brytare, och därifrån till dess panel och vidare till dimrarna
_B6, _B7 = BRYTARE["KA-B6"], BRYTARE["KA-B7"]
_D = DIMRAR
_S6 = S6                                                             # från centralen, till KA-P07, till KA-B7
_S7 = stigarna(_B7, [xy(_B6), _P08, xy(_D["KA-B4"])], -40.0)      # från KA-B6, till KA-P08, till KA-B4
# det stora rummets uttag och fläkten FF3 (G24): gruppens rör från centralen ned i V20:s cellplast till fläktens
# anslutning, och därifrån till det första uttaget på V15
_D2 = _PK["KA-D2"]
_U9 = _PK["KA-U9"]
_S_D2 = S_D2                                                         # från centralen, till KA-U9
_S_U9 = stigarna(_U9, [xy(_D2)], 0.0)

ROR += [
    _dra("G17-R1", "KA-D1", "KA-B5", D_STORA, _S5[0], efter=ned_i_dosan(_B5, _S5[0])),
    _dra("KA-R6-1", "KA-D1", "KA-P05", D_STORA, _P05),
    _dra("KA-R6-2", "KA-P05", "KA-P06", _P05, _P06),
    _dra("KA-R6-3", "KA-B5", "KA-P03", _S5[1], _P03, fore=ur_dosan(_B5, _S5[1])),
    _dra("KA-R6-4", "KA-P03", "KA-P04", _P03, _P04),
    _dra("KA-R6-5", "KA-P04", "KA-P02", _P04, _P02),
    _dra("KA-R6-6", "KA-P02", "KA-P01", _P02, _P01),
    _dra("KA-R7-1", "KA-B6", "KA-P07", _S6[1], _P07, fore=ur_dosan(_B6, _S6[1])),
    _dra("G18-R1", "KA-B6", "KA-B7", _S6[2], _S7[0], fore=ur_dosan(_B6, _S6[2]), efter=ned_i_dosan(_B7, _S7[0])),
    _dra("KA-R8-1", "KA-B7", "KA-P08", _S7[1], _P08, fore=ur_dosan(_B7, _S7[1])),
    _dra("G24-R1", "KA-D2", "KA-U9", _S_D2[1], _S_U9[0], fore=ur_dosan(_D2, _S_D2[1]), efter=ned_i_dosan(_U9, _S_U9[0])),
]


@cache
def _rorandarnas_hinder() -> Polygon:
    """Där en ljuslinjes rörände inte får stå: nära det som går lodrätt genom bjälklaget och rören i det (plan 1:s
    och källarens, tappvattnet och avloppet)."""
    upp = upptaget_av(_ING.ror, _R)
    andra = [Point(x, y).buffer(rr + _R + SPEL) for x, y, rr, z0, z1 in _ING.stigare if z0 < BJALKLAG["MB"] + _R]
    vatten_ = [g.buffer(_R + rr + SPEL) for g, rr in i_nivan(KALLARTAK, BJALKLAG["MB"] + _R)]
    genom = [Point(x, y).buffer(_R + rr + SPEL) for x, y, rr in genom_nivan(KALLARTAK, BJALKLAG["MB"] + _R)]
    return unary_union([*upp[0], *upp[1], *andra, *vatten_, *genom])


def _profilen(mitt: tuple[float, float], u: tuple[float, float], langd: float) -> Polygon:
    a = (mitt[0] - u[0] * langd / 2, mitt[1] - u[1] * langd / 2)
    b = (mitt[0] + u[0] * langd / 2, mitt[1] + u[1] * langd / 2)
    return LineString([a, b]).buffer(ASKPROFIL.bredd / 2, cap_style="flat")


def _placera(rum: Polygon, mitt: tuple[float, float], u: tuple[float, float], langd: float,
             ut: bool) -> tuple[float, float]:
    """Ljuslinjens mitt närmast den önskade (högst 150 mm därifrån), där profilen ligger i rummet och rörändan i
    matningens ände (och i den andra, ut) går mellan underkantsnätets järn och fri från rören i bjälklaget."""
    s = langd / 2 - ASKPROFIL.ror_in
    stopp = _rorandarnas_hinder()
    inne = rum.buffer(-60.0)
    for steg in range(0, 151, 5):
        for dx, dy in sorted({(sx * steg, sy * j) for sx in (-1, 1) for sy in (-1, 1) for j in range(0, steg + 1, 5)}
                             | {(sx * j, sy * steg) for sx in (-1, 1) for sy in (-1, 1) for j in range(0, steg + 1, 5)},
                             key=lambda d: math.hypot(*d)):
            c = (mitt[0] + dx, mitt[1] + dy)
            andar = [(c[0] - u[0] * s, c[1] - u[1] * s)] + ([(c[0] + u[0] * s, c[1] + u[1] * s)] if ut else [])
            if not inne.contains(_profilen(c, u, langd)) or any(stopp.contains(Point(q)) for q in andar):
                continue
            if all(fri(Point(q), _R, KALLARTAK, BJALKLAG["MB"], 5.0) for q in andar):
                return c
    raise ValueError(f"ingen plats för ljuslinjen nära ({mitt[0]:.0f}, {mitt[1]:.0f})")


def _linjerna() -> dict[str, list[Lampa]]:
    ut: dict[str, list[Lampa]] = {}
    for tand, linjer in LINJER.items():
        for i, (lid, langd, mitt, u) in enumerate(linjer):
            nasta = i + 1 < len(linjer) and linjer[i + 1][0] not in _STJARNA
            x, y = _placera(_RUMMET[tand], mitt, u, langd, nasta)
            ut.setdefault(tand, []).append(Lampa(lid, ljuslinje(langd), kallartak(x, y), tand, langs=(u[0], u[1], 0.0)))
    return ut


_T = _linjerna()
LJUSLINJERNA = [p for lampor in _T.values() for p in lampor]
PUNKTER += [*LJUSLINJERNA, *DIMRAR.values()]

# 24 V-kretsarna: ett drivdon per tändgrupp i drivdonsskåpet (../../teknikrum.py), dimrat av dimmerns kanal
KRETSAR = [Krets(f"LK{i + 1}", "TK-LC", i, d.id, d.styr.index(tand), tand, tuple(p.id for p in _T[tand]))
           for i, (tand, d) in enumerate((t, next(d for d in DIMRAR.values() if t in d.styr)) for t in LINJER)]


def _xy_ror(p: Lampa, ut: bool = False) -> tuple[float, float]:
    """Ljuslinjens rörände i plan (matningens, eller ut: den andra)."""
    q = anslutning(p, ut)
    return q[0], q[1]


# ljuslinjernas rörändar: hinder för de andra rören (rakt ned till taket från rörets nivå)
_ING.stigare += [(q[0], q[1], _R, KALLARTAK, BJALKLAG["MB"] + _R) for p in LJUSLINJERNA
                 for q in (anslutning(p), anslutning(p, ut=True))]

# dimrarna (G18): matningen från det östra lilla rummets brytare till dimrarna i tur och ordning, och den dimrade fasen
# från varje dimmer i ett eget rör till drivdonsskåpet
_LC_TOPP = DRIVDONSSKAP.anslutningar["topp"]
_LC = (_LC_TOPP[0], _LC_TOPP[1])
_S4 = stigarna(_D["KA-B4"], [xy(_B7), _LC, xy(_D["KA-B1"])], -40.0)        # från KA-B7, till skåpet, till KA-B1
_S1 = stigarna(_D["KA-B1"], [xy(_D["KA-B4"]), xy(_D["KA-B2"]), _LC], -40.0)  # från KA-B4, till KA-B2, till skåpet
_S2 = stigarna(_D["KA-B2"], [xy(_D["KA-B1"]), xy(_D["KA-B3"]), _LC], 0.0)    # från KA-B1, till KA-B3, till skåpet
_S3 = stigarna(_D["KA-B3"], [xy(_D["KA-B2"]), _LC], 0.0)                     # från KA-B2, till skåpet

# dimrarnas stigare: hinder för de andra rören redan innan de dras (drivdonsskåpets knippen dras först)
_ING.stigare += [(q[0], q[1], _R, KALLARTAK, BJALKLAG["MB"] + _R) for q in (*_S4, *_S1, *_S2, *_S3)]

# drivdonsskåpets rör (den dimrade fasen från dimrarna och 24 V till ljuslinjerna): rakt upp ur skåpets ovansida i en
# rad, i ordning efter riktningen de går åt (från öster det som går mest österut), och därifrån direkt till sina punkter
X_STIGARE_MIN = 21.0                         # stigarnas avstånd över skåpet (Ø16, 5 mm emellan)


def _skapets_stigare(n: int) -> list[float]:
    """Stigarnas x över drivdonsskåpet (en rad mitt på ovansidan), från skåpets östra del västerut, fria från järnen
    från källarens tak till elrörens övre nivå."""
    ut: list[float] = []
    x = _LC_TOPP[0] + DRIVDONSSKAP.matt[0] / 2 - 30.0
    while len(ut) < n and x > _LC_TOPP[0] - DRIVDONSSKAP.matt[0] / 2 + 30.0:
        if (not ut or ut[-1] - x >= X_STIGARE_MIN - 1e-6) and fri(Point(x, _LC_TOPP[1]), _R, KALLARTAK,
                                                                     BJALKLAG["MB"], 5.0):
            ut.append(x)
        x -= 1.0
    if len(ut) < n:
        raise ValueError(f"bara {len(ut)} stigare ryms över drivdonsskåpet, {n} behövs")
    return ut


T1, T2, T3, T4, T5 = (_T[t] for t in LINJER)
# skåpets rör: (id, från, till, punkten i bjälklaget vid den andra änden, vägen in i dimmerns dosa, slag)
_SKAPETS = [
    ("KA-B1-LC", "KA-B1", _S1[2], ur_dosan(_D["KA-B1"], _S1[2])),
    ("KA-B2-LC", "KA-B2", _S2[2], ur_dosan(_D["KA-B2"], _S2[2])),
    ("KA-B3-LC", "KA-B3", _S3[1], ur_dosan(_D["KA-B3"], _S3[1])),
    ("KA-B4-LC", "KA-B4", _S4[1], ur_dosan(_D["KA-B4"], _S4[1])),
    ("LK1-1", T1[0].id, _xy_ror(T1[0]), ()),
    ("LK1-2", T1[1].id, _xy_ror(T1[1]), ()),
    ("LK2-1", T2[0].id, _xy_ror(T2[0]), ()),
    ("LK3-1", T3[0].id, _xy_ror(T3[0]), ()),
    ("LK4-1", T4[0].id, _xy_ror(T4[0]), ()),
    ("LK5-1", T5[0].id, _xy_ror(T5[0]), ()),
]


def _skapets_ror() -> list[Ror]:
    """Drivdonsskåpets rör: stigarna i raden över skåpet, i knippen åt var sitt håll (ingjutna.knippe) i elrörens undre
    nivå, norrut eller söderut ur skåpet och västerut eller österut efter var den andra änden ligger, och därifrån
    direkt till den."""
    xs = sorted(_skapets_stigare(len(_SKAPETS)))          # från väster
    y = _LC_TOPP[1]
    kartor_ = kartor_el(_R)
    undre = NIVAER.index("MB-UK")
    # knippena: norrut ur skåpet till punkterna norr om det och söderut (mellan skåpet och tappvattnets stråk i den
    # undre nivån) till dem söder om det, västerut och österut
    delar: dict[str, list[tuple[str, str, tuple[float, float], tuple[Vek, ...]]]] = {}
    for t in _SKAPETS:
        delar.setdefault(("S" if t[2][1] > _LC_TOPP[1] else "N") + ("V" if t[2][0] < _LC_TOPP[0] else "O"),
                         []).append(t)
    ordning = [n for n in ("NV", "SV", "NO", "SO") if n in delar]
    lediga = list(xs)
    stig: dict[str, tuple[float, float]] = {}
    vagar: dict[str, tuple[list[tuple[float, float]], list[float]]] = {}
    for n in ordning:
        d = delar[n]
        block, lediga = (lediga[:len(d)], lediga[len(d):]) if n.endswith("V") else (lediga[-len(d):], lediga[:-len(d)])
        ut_ = (0.0, -1.0) if n.startswith("N") else (0.0, 1.0)
        mal = {t[0]: t[2] for t in d}
        slut_ = max(mal.values(), key=lambda q: math.dist(q, (_LC_TOPP[0], y)))
        hd = hinder(_R, [*_ING.stigare, *((q[0], q[1], _R, KALLARTAK, BJALKLAG["MB"] + _R) for q in mal.values())],
                    _ING.dosor, utom=[*((x, y) for x in block), slut_])
        st, vg = knippe(kartor_, [(x, y) for x in block], ut_, mal, slut_, hd, lager=undre, kost=KALLAREN)
        stig.update(st)
        vagar.update(vg)
    z = BJALKLAG["MB-UK"]
    # rören i tur och ordning efter var de lämnar sitt knippe
    bestallningar: list[dict[str, object]] = []
    for rid, pid, b, dosan in sorted(_SKAPETS, key=lambda t: LineString(vagar[t[0]][0]).length):
        s_ = stig[rid]
        pts, rr = vagar[rid]
        upp = (s_[0], s_[1], _LC_TOPP[2])
        i_knippet = tuple((q[0], q[1], z) for q in pts[:-1])
        rad = (0.0, *rr[:-1])
        if rid.startswith("LK"):
            bestallningar.append(dict(id_=rid, typ=FXP16, fran="TK-LC", till=pid, a=pts[-1], b=b,
                                      fore=(upp, *i_knippet), fore_radier=rad, bage_a=MB.LAMNA, led_a={"MB-UK": []},
                                      slag="24 V", kost=KALLAREN, nivaer=(("MB-UK",), NIVAER)))
        else:
            bestallningar.append(dict(id_=rid, typ=FXP16, fran=pid, till="TK-LC", a=b, b=pts[-1], fore=dosan,
                                      efter=(*i_knippet[::-1], upp), efter_radier=rad[::-1], bage_b=MB.LAMNA,
                                      led_b={"MB-UK": []}, slag="230 V dimrad", kost=KALLAREN,
                                      nivaer=(NIVAER, ("MB-UK",))))
    return sorted(_ING.solfjader(bestallningar), key=lambda r: [t[0] for t in _SKAPETS].index(r.id))


# först drivdonsskåpets knippen (de kan inte gå runt något) i den undre nivån, sedan dimrarnas matning i tur och
# ordning, helst i den övre (över knippena), och rören mellan ljuslinjerna, runt dem
ROR += [*_skapets_ror()]
ROR += [
    _dra("G18-R2", "KA-B7", "KA-B4", _S7[2], _S4[0], fore=ur_dosan(_B7, _S7[2]), efter=ned_i_dosan(_D["KA-B4"], _S4[0]), kost=PLAN1),
    _dra("G18-R3", "KA-B4", "KA-B1", _S4[2], _S1[0], fore=ur_dosan(_D["KA-B4"], _S4[2]),
         efter=ned_i_dosan(_D["KA-B1"], _S1[0]), kost=PLAN1),
    _dra("G18-R4", "KA-B1", "KA-B2", _S1[1], _S2[0], fore=ur_dosan(_D["KA-B1"], _S1[1]),
         efter=ned_i_dosan(_D["KA-B2"], _S2[0]), kost=PLAN1),
    _dra("G18-R5", "KA-B2", "KA-B3", _S2[1], _S3[0], fore=ur_dosan(_D["KA-B2"], _S2[1]),
         efter=ned_i_dosan(_D["KA-B3"], _S3[0]), kost=PLAN1),
    _dra("LK2-2", T2[0].id, T2[1].id, _xy_ror(T2[0], ut=True), _xy_ror(T2[1]), slag="24 V"),
    _dra("LK5-2", T5[0].id, T5[1].id, _xy_ror(T5[0], ut=True), _xy_ror(T5[1]), slag="24 V"),
]
