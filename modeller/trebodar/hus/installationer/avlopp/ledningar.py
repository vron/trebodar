"""Avloppet som en egen installation (ärendena #52 och #49): avloppspunkterna på inredningens och installationernas
lägen, ledningarna från dem till stammen och grundledningen och grundledningen under bottenplattan ut ur huset mot
förbindelsepunkten. Allt går med självfall (förbindelsepunkten ligger längre ned åt nordost, med marken på cirka
+4,5). Inget annat i modellen bygger på ledningarnas lägen utom det som ska gå runt dem (golvvärmen, kontrollerna).

Plan 1, badrummet (#52), med var sitt rör lodrätt genom mellanbjälklaget (hylsa i formen):
- golvbrunnen i duschen: kroppen ingjuten i bjälklaget med flänsen i dess överkant och lodrätt utlopp Ø75;
- WC:n: S-låset till ett rör Ø110 i golvet WC_AVLOPP från L9;
- tvättstället: vattenlåset Ø32 i skåpet till ett rör Ø50 genom golvet under tvättstället;
- badkaret: vattenlåset under karet till ett rör Ø50 genom golvet under karets mitt;
- tvätten i skåpet i nischen (#51, förberedd för tvättmaskin och torktumlare): vattenlåset på L10 (hus/badrum.py) till
  ett rör Ø50 ned i väggen och genom bjälklaget.
Alla går rakt ned genom källaren och kopplas ihop under bottenplattan (#138), med var sin gren till grundledningen:
tvättställets längs V7, badkarets i KL1:s regelfack (vattenlåset under karet, över väggen) och tvättens i KL2:s
(vattenlåset på L10 rakt över den); WC:ns går under bjälklaget österut till KL2 och ned längs dess västra gips
(X_WC_NED), och golvbrunnens söderut in i KL8 och ned i dess regelfack (användarens kommentar: rören i väggarna, inte
fritt i rummen; lägena i hus/invandigt/kallarens_innervaggar.AVLOPP_I_VAGGARNA). Inget hänger i källarens tak utom
de två korta styckena. Hålen genom bjälklaget ligger utanför rörens (P4, P8, P9)
genomstansningszon 6d utom golvbrunnens, som K-05 ska pröva (kontrollen redovisar hålen inom GENOMSTANSNING från
rören).

Genom och under bottenplattan är rören minst INGJUTET_MIN (#137): de klenare (Ø50) ökar till Ø75 OKNING över
källargolvet, så att det ingjutna inte sätts igen.

Köket: diskhons avlopp (i hons bakre del, bakom diskbänksskåpets lådor) går rakt ned, Ø50 genom mellanbjälklaget
och källaren längs källarväggen V14, Ø75 genom bottenplattan, och med en böj till en gren Ø110 till grundledningen. Diskmaskinen
i ön (#50) har ett pumpat avlopp (AV20): maskinens egen pump trycker vattnet genom ett rör PEX 25 utan fall, ingjutet
i mellanbjälklaget på tappvattnets nivå, från anslutningen under maskinen i räta vinklar till diskbänksskåpet bakom
lådorna, där
slangen går upp till diskhons vattenlås (dess anslutning för diskmaskin, med en ögla under bänkskivan). Ett avlopp med
självfall ryms inte mellan armeringsnäten (#49). Röret går förbi tappvattnets matning till underfördelaren UF1, så att
det inte korsar den; maskinen ska tillåta så lång slang (DM_SLANG).

Stammen Ø110 står i källarväggen KL8 (kallarens_innervaggar.AVLOPPSSTAM) under badrummets vägg L11, från toppen
Z_STAM ned genom bottenplattan, med rensningen RENSNING över källargolvet mot teknikrummet, och går med en böj och en
kort sträcka till grundledningen. Den tar inget avlopp: den luftar grundledningen och är dess rensning.

Luftningen (avluftningen) går rakt upp från stammens topp, dold i väggarna: i KL8, genom mellanbjälklaget och upp i
L11:s regelfack (Ø50, LU1; väggens stomme 70 mm rymmer inte Ø75), och från innertakets installationsskikt en dimension
större (Ø75, LU2, mot frost) isolerad genom takets isolering och ut genom taket till luftningshuven (HUV).

Källaren: fem golvbrunnar (GOLVBRUNNAR_KALLARE, efter användarens skiss) med kroppen ingjuten i bottenplattans
betong och lodrätt utlopp Ø110; tvättmaskinen töms i golvbrunnen GB1 bredvid den och GB4 är duschens i det framtida
badrummet. Tvätthona och det framtida badrummets handfat (tappvattnets KA-TH1, KA-TH2 och KB-TS1, som inte är
modellerade) får var sin anslutning Ø75 i golvet bredvid golvstosen (BREDVID_STOSEN), rakt ned till en gren, och det
framtida WC:t en Ø110 (WC_KALLARE), proppade tills vidare.

Grundledningen Ø110 under bottenplattan börjar i golvbrunnen GB1 vid tvätten, går österut genom GB2 i teknikrummet,
norr om köldbärarens rör där de går upp genom plattan, och därifrån rakt mot nordost ut under källarväggen V9
(UTLOPP). Direkt utanför väggen faller den brant under dräneringen runt grunden (UTLOPP_FALL) och fortsätter åt
nordost, längs dagvattnets utgående rör, mot förbindelsepunkten (UTLOPP_L av den ritas). Överkanten ligger
UNDER_CELLPLAST under bottenplattans cellplast där den börjar. Grenarna går vinkelrätt mot den (de nära varandra något
förskjutna, minst GREN_AVSTAND isär, i ordning längs den så att de inte korsar varandra) och ansluter med vattengången
ANSLUTNING_OVER över dess.

Fall: Ø110 minst 10 ‰ och de klenare minst 17 ‰ (tillverkarnas anvisningar för avlopp i byggnad, t.ex. Pipelife),
lagda med FALL. Ledningarnas punkter är rörets mitt (x, y, z), z från plan 1:s golv (bjälklagets överkant).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from functools import cache

from trebodar import skelett as S
from trebodar.hus import badrum as B
from trebodar.hus.grund import grund as G
from trebodar.hus.grund import kallarvaggar as K
from trebodar.hus.grund.pelare import PELARE
from trebodar.hus.inredning import koksbank as KB
from trebodar.hus.invandigt.kallare import GIPS_T
from trebodar.hus.invandigt.kallarens_innervaggar import AVLOPP_I_VAGGARNA, AVLOPPSSTAM
from trebodar.hus.invandigt.kallarens_innervaggar import VAGGAR as KL
from trebodar.hus.invandigt.vaggar import vaggdef

from ..dranering.ledningar import UTLOPP_RIKTNING
from ..genomforingar import Stycke, genomforingar
from ..montering import I_BETONGEN, angbromsen, pa_tak
from ..strak import mellan_jarnen
from ..vatten.rum import kallarbadrum, kallare as vattnet_i_kallaren

Vek = tuple[float, float, float]

UPPHANG = 10.0                              # rörens överkant under bjälklagets underkant
FALL = {110.0: 0.010, 75.0: 0.020, 50.0: 0.020}     # lagt fall per ytterdiameter
FALL_MIN = {110.0: 0.010, 75.0: 0.017, 50.0: 0.017}  # minsta fall (tillverkarnas anvisningar)
FRI_HOJD = 1900.0                           # minsta fria höjd under rören i källaren (anmärkning)
GENOMSTANSNING = 720.0                      # rörens genomstansningszon i bjälklaget, 6d (anmärkning för hål inom den)
GODS = {110.0: 3.4, 75.0: 3.0, 50.0: 1.8, 40.0: 1.8, 32.0: 1.8, 25.0: 2.3}
STAM = AVLOPPSSTAM                          # stammens läge och Ø (i KL8)
Z_STAM = -200.0                             # stammens topp, där luftningen börjar (under KL8:s hammarband)
RENSNING = (S.Z_BOTTENPLATTA + 500.0, 1.0)  # stammens rensning: höjden och riktningen i y (mot teknikrummet)
LUFTNING = (50.0, 75.0)                     # luftningens Ø i väggen och genom taket
LUFT_ISOLERING = 30.0                       # luftningens isolering genom takets isolering
HUV = (160.0, 350.0)                        # luftningshuven av plåt på taket: huvens Ø och höjd över taket
# luftningen ligger så långt från stammens mitt i y (excentrisk övergång i stammens topp), mitt emellan takets
# ströläkt 1NV-SL45 och -SL46, inom KL8:s stomme och fri från L11:s regel
LUFT_DY = 25.0
X_SAMLING = B.X_L9 - B.WC_AVLOPP            # WC:ns rör genom golvet
INGJUTET_MIN = 75.0                         # rören genom och under bottenplattan är minst så grova (#137)
OKNING = 100.0                              # de klenare rörens ökning till INGJUTET_MIN, så högt över källargolvet
# WC:ns rör går under bjälklaget österut till KL2 och ned längs dess västra gips (10 mm från den)
X_WC_NED = KL["KL2"].c - KL["KL2"].t / 2 - GIPS_T - 10.0 - 55.0
# duschens golvbrunn: röret går under bjälklaget söderut in i KL8 (genom hammarbandets urtag) och ned i regelfacket
X_GB_NED, Y_GB_NED, _ = AVLOPP_I_VAGGARNA["AV4"]
TVATTSTALL_AVLOPP = (B.X_TVATTSTALL, B.Y_1NO + 260.0)      # under tvättställets mitt (inredning/badrum.py)
BADKAR_AVLOPP = AVLOPP_I_VAGGARNA["AV3"][:2]                    # under karet, över KL1
assert B.BADKAR_X[0] < BADKAR_AVLOPP[0] < B.BADKAR_X[1] and B.BADKAR_Y[0] < BADKAR_AVLOPP[1] < B.BADKAR_Y[1], \
    "badkarets avlopp under karet"
BADKAR_BOTTEN = B.Z_BADKAR + B.BADKAR_KAR                        # karets botten
BRUNN = (200.0, 100.0)                      # golvbrunnens kropp: diameter, djup under flänsen
BRUNN_SIL = (220.0, 230.0)                  # silen och klämringen (hålet i golvets skikt, badrumsgolv.BRUNN_HAL)
DISKHO = KB.diskhons_avlopp()               # diskhons avlopp i plan
# diskmaskinens pumpade avlopp (AV20): från anslutningen under maskinen längs ön till Y_DM, österut och norrut
# till diskbänksskåpet bakom lådorna, norr om tappvattnets matning till UF1 (som kommer ned till underfördelaren vid
# y 8 825)
DM_ROR = 25.0                               # PEX 25 × 2,3
DM_ANSLUTNING = KB.diskmaskinens_anslutningar()[1]
Y_DM = 8700.0                               # längs ön till hit, förbi matningen till UF1 (y 8 825)
DM_DISKBANK = (13500.0, 8200.0)             # upp i diskbänksskåpet bakom lådorna
DM_STOS = 100.0                             # rörets ände i diskbänksskåpet över golvet, där slangen ansluter (under
#                                             maskinen slutar det i golvet)
DM_SLANG = 4.0                              # så lång avloppsslang ska diskmaskinen tillåta (maskinen till vattenlåset) [m]
assert KB.FOGAR_LANG[1] + 100.0 <= DM_DISKBANK[1] <= KB.FOGAR_LANG[2] - 100.0, "röret upp i diskbänksskåpet"
# tvättens vattenlås på L10 i skåpet i badrummet: röret i väggens regelfack och genom bjälklaget (hus/badrum.py)
TVATT_AVLOPP = (B.TVATT_AVLOPP[0], vaggdef("L10").origo[1] + vaggdef("L10").tjocklek / 2)
assert max(abs(a - b) for a, b in zip(TVATT_AVLOPP, AVLOPP_I_VAGGARNA["AV21"][:2])) < 1e-6, "tvättens avlopp i KL2"
I_VAGGEN = ("LU1", "LU2", "AV21")           # ledningarna lodrätt i väggarnas regelfack, genom syll och hammarband

# ------------------------------------------------------------------ källaren och grundledningen
GRUND = 110.0                               # grundledningarnas Ø
Z_UK_CELLPLAST = S.Z_BOTTENPLATTA - G.H_L   # bottenplattans cellplasts underkant (L-elementen)
UNDER_CELLPLAST = 20.0                      # grundledningens överkant under cellplasten där den börjar
ANSLUTNING_OVER = 2.0                       # grenens vattengång över grundledningens där den ansluter
GREN_AVSTAND = 300.0                        # grenarnas anslutningar minst så långt isär längs grundledningen
# golvbrunnarna i källaren (användarens skiss): kroppen i bottenplattans betong, flänsen i dess överkant
GOLVBRUNNAR_KALLARE = {"GB1": (1520.0, 8430.0),            # vid tvätten (tvättmaskinen töms i den)
                       "GB2": (3770.0, 8510.0),            # i teknikrummet (fördelarskåpets läckageindikering)
                       "GB3": (8330.0, 9920.0),
                       "GB4": (3310.0, 4450.0),            # i det framtida badrummets dusch (skissen)
                       "GB5": (11310.0, 3430.0)}
BRUNN_KALLARE = (200.0, G.H_PLATTA)         # golvbrunnens kropp i källaren: diameter och djup (plattans betong)
# tvätthonas och handfatets avlopp bredvid golvstosen (dx, dy): tvätthona norr om stosen (vattnet kommer söderifrån),
# handfatet längs bågen förbi kallvattnet (vattnet kommer västerifrån)
BREDVID_STOSEN = {"KA-TH1": (0.0, -100.0), "KA-TH2": (0.0, -100.0),
                  "KB-TS1": (110.0 * kallarbadrum.TANGENT[0], 110.0 * kallarbadrum.TANGENT[1])}
WC_KALLARE = (3050.0, 5150.0)               # det framtida WC:ts golvavlopp Ø110 (skissen: mot KL2, 190 från gipsen)
TVATTHO_STOS = 80.0                         # anslutningens överkant över golvet
_V9 = next(v for v in K.VAGGAR if v.namn == "V9")
UTLOPP = (13000.0, _V9.c - K.KARNA / 2 - K.CELL)          # där grundledningen går ut under V9:s utsida
UTLOPP_L = 3000.0                           # så långt grundledningen ritas utanför huset
# grundledningen faller så mycket brant (två böjar 45°) direkt utanför väggen, under dräneringen runt grunden
UTLOPP_FALL = (100.0, 150.0)                # fallet och dess längd i plan


@dataclass(frozen=True)
class Ledning:
    id: str
    namn: str
    d: float
    vag: tuple[Vek, ...]                    # rörets mitt
    till: str = ""                          # ledningen den ansluter till (tom: ut mot förbindelsepunkten)
    pumpad: bool = False                    # tryckt av en pump, utan fall (diskmaskinen i ön)


def _under(d: float) -> float:
    """Rörets mitt under bjälklaget."""
    return -S.H_BJALKLAG - UPPHANG - d / 2


def _fall(start: Vek, plan: list[tuple[float, float]], d: float) -> list[Vek]:
    """Från start (rörets mitt) längs punkterna i plan med fallet FALL[d]."""
    ut = [start]
    for x, y in plan:
        a = ut[-1]
        ut.append((x, y, a[2] - FALL[d] * math.hypot(x - a[0], y - a[1])))
    return ut


def tvatthon() -> dict[str, tuple[float, float]]:
    """Tvätthonas och det framtida handfatets avlopp i golvet bredvid deras golvstosar (tappvattnets KA-TH1, KA-TH2
    och KB-TS1), på den sida där tappvattnet inte kommer under plattan (BREDVID_STOSEN)."""
    ut = {}
    for t in (*vattnet_i_kallaren.TAPPSTALLEN, *kallarbadrum.TAPPSTALLEN):
        if t.id in BREDVID_STOSEN:
            (x, y, _), (dx, dy) = t.lage.punkt, BREDVID_STOSEN[t.id]
            ut[t.id] = (x + dx, y + dy)
    assert set(ut) == set(BREDVID_STOSEN), "avloppen bredvid golvstosarna"
    return ut


@dataclass(frozen=True)
class _Grundledning:
    """Grundledningens mittlinje i plan (punkterna) och mittens z där den börjar; z faller FALL[GRUND] längs den och
    UTLOPP_FALL brant direkt utanför väggen (punkterna 2–3)."""
    punkter: tuple[tuple[float, float], ...]
    z0: float

    def langs(self, s: float) -> tuple[float, float, float]:
        """Punkten s längs ledningen (från dess början) med mittens z."""
        kvar, brant = s, 0.0
        for i, (a, b) in enumerate(zip(self.punkter, self.punkter[1:])):
            lg = math.dist(a, b)
            if kvar <= lg or b == self.punkter[-1]:
                t = kvar / lg
                if i == 2:
                    brant = UTLOPP_FALL[0] * min(t, 1.0)
                return a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]), self.z0 - FALL[GRUND] * s - brant
            if i == 2:
                brant = UTLOPP_FALL[0]
            kvar -= lg
        raise ValueError(s)

    def narmast(self, x: float, y: float, s_min: float, s_max: float) -> float:
        """s för punkten närmast (x, y) på ledningen mellan s_min och s_max."""
        bast, s0 = (math.inf, s_min), 0.0
        for a, b in zip(self.punkter, self.punkter[1:]):
            lg = math.dist(a, b)
            t = ((x - a[0]) * (b[0] - a[0]) + (y - a[1]) * (b[1] - a[1])) / lg ** 2
            s = min(max(s0 + t * lg, s_min), s_max)
            px, py, _ = self.langs(s)
            bast = min(bast, (math.hypot(px - x, py - y), s))
            s0 += lg
        return bast[1]

    @property
    def inne(self) -> float:
        """s där ledningen går ut under V9 (UTLOPP)."""
        return sum(math.dist(a, b) for a, b in zip(self.punkter[:3], self.punkter[1:3]))


@cache
def grundledningen() -> _Grundledning:
    (x1, y1), (x2, y2) = GOLVBRUNNAR_KALLARE["GB1"], GOLVBRUNNAR_KALLARE["GB2"]
    ux, uy = UTLOPP_RIKTNING
    brant = (UTLOPP[0] + ux * UTLOPP_FALL[1], UTLOPP[1] + uy * UTLOPP_FALL[1])
    ut = (UTLOPP[0] + ux * UTLOPP_L, UTLOPP[1] + uy * UTLOPP_L)
    return _Grundledning(((x1, y1), (x2, y2), UTLOPP, brant, ut), Z_UK_CELLPLAST - UNDER_CELLPLAST - GRUND / 2)


def _gren(x: float, y: float, s: float, bakom: bool) -> tuple[tuple[Vek, ...], float]:
    """Grenen Ø GRUND från det lodräta röret i (x, y) till grundledningens yta vid s, med fallet FALL[GRUND] och
    vattengången ANSLUTNING_OVER över grundledningens: grenens punkter och dess mitt (z) under det lodräta röret. Med
    bakom börjar grenen sin radie bakom det lodräta röret (ett eget, klenare rör som landar på grenen), annars i
    böjen (samma ledning)."""
    gl = grundledningen()
    fx, fy, zg = gl.langs(s)
    lang = math.hypot(fx - x, fy - y)
    vx, vy = (fx - x) / lang, (fy - y) / lang
    r = GRUND / 2
    z_slut = zg + ANSLUTNING_OVER
    z_bojen = z_slut + FALL[GRUND] * (lang - r)
    start = (x - vx * r, y - vy * r, z_bojen + FALL[GRUND] * r) if bakom else (x, y, z_bojen)
    return (start, (x + vx * (lang - r), y + vy * (lang - r), z_slut)), z_bojen


@cache
def ledningar() -> dict[str, Ledning]:
    """Alla ledningar: grundledningen, de lodräta rören från plan 1 och källaren med sina grenar till den, stammen,
    diskmaskinens pumpade avlopp och luftningen."""
    ut: dict[str, Ledning] = {}
    sx, sy, _ = STAM
    # grundledningen och grenarna till den, i ordning längs den (anslutningarna minst GREN_AVSTAND isär)
    gl = grundledningen()
    s1 = math.dist(*gl.punkter[:2])                                 # GB2, där ledningen viker mot nordost
    upptagna = [0.0, s1]

    def anslutning(x: float, y: float) -> float:
        """Där det lodräta rörets gren ansluter till grundledningen: närmast röret, på den första sträckan för dem
        som står närmast den, och flyttad nedströms tills den är GREN_AVSTAND från de andra."""
        s_min = GREN_AVSTAND if gl.narmast(x, y, 0.0, s1) < s1 - 1.0 else s1
        s = gl.narmast(x, y, s_min, gl.inne - GREN_AVSTAND)
        while any(abs(s - u) < GREN_AVSTAND for u in upptagna):
            s += GREN_AVSTAND / 3
        upptagna.append(s)
        return s
    ux, uy = gl.punkter[0][0] - gl.punkter[1][0], gl.punkter[0][1] - gl.punkter[1][1]
    lg0 = math.hypot(ux, uy)
    x0, y0 = gl.punkter[0][0] + ux / lg0 * GRUND / 2, gl.punkter[0][1] + uy / lg0 * GRUND / 2   # bakom GB1
    huvud = [(x0, y0, gl.z0 + FALL[GRUND] * GRUND / 2)] + [gl.langs(s) for s in (s1, gl.inne, gl.inne + UTLOPP_FALL[1],
                                                                                 gl.inne + UTLOPP_L)]
    ut["AV8"] = Ledning("AV8", "Grundledningen mot förbindelsepunkten", GRUND, tuple(huvud))
    # de lodräta rören med var sin gren under bottenplattan (#138): plan 1:s avlopp går rakt ned genom källaren och
    # kopplas ihop under bottenplattan, liksom köket, tvätthona, stammen och golvbrunnarna. Genom och under
    # bottenplattan är rören minst INGJUTET_MIN (#137): de klenare ökar OKNING över källargolvet.
    xs, ys = X_SAMLING, B.WC_Y
    xt, yt = B.X_TVATTSTALL, TVATTSTALL_AVLOPP[1]
    xb, yb = BADKAR_AVLOPP
    gx, gy = B.GOLVBRUNN
    xv, yv = TVATT_AVLOPP
    zk = S.Z_BOTTENPLATTA - BRUNN_KALLARE[1]                       # källarens golvbrunnars botten
    z_ok = S.Z_BOTTENPLATTA + OKNING
    # (lodrätt rör, ökning, gren), vad, Ø, punkten där det går ned, vägen dit uppifrån, grenen i samma ledning
    Rad = tuple[tuple[str, str, str], str, float, tuple[float, float], list[Vek], bool]
    rader: list[Rad] = [
        (("AV1", "", ""), "WC:n", GRUND, (X_WC_NED, ys),
         [(xs, ys, B.golvniva(xs, ys)), *_fall((xs, ys, _under(GRUND)), [(X_WC_NED, ys)], GRUND)], True),
        (("AV2", "AV22", "AV23"), "Tvättstället", 50.0, (xt, yt), [(xt, yt, B.golvniva(xt, yt))], False),
        (("AV3", "AV24", "AV25"), "Badkaret", 50.0, (xb, yb), [(xb, yb, B.golvniva(xb, yb))], False),
        (("AV4", "", "AV26"), "Golvbrunnen i duschen", 75.0, (X_GB_NED, Y_GB_NED),
         [(gx, gy, -BRUNN[1]), *_fall((gx, gy, _under(75.0)), [(X_GB_NED, Y_GB_NED)], 75.0)], False),
        (("AV21", "AV27", "AV28"), "Tvätten i badrummets skåp", 50.0, (xv, yv),
         [(xv, yv, B.golvniva(xv, B.Y_L10 + 50.0) + B.TVATT_AVLOPP[1])], False),
        (("AV5", "AV29", "AV6"), "Diskbänken", 50.0, DISKHO, [(*DISKHO, 0.0)], False),
        (("AV7", "", ""), "Stammen i KL8", GRUND, (sx, sy), [(sx, sy, Z_STAM)], True),
        *(((f"AV{11 + i}", "", ""), f"Golvbrunnen {k}", GRUND, p, [(*p, zk)], True)
          for i, (k, p) in enumerate(q for q in GOLVBRUNNAR_KALLARE.items() if q[0] not in ("GB1", "GB2"))),
        *(((f"AV{14 + 2 * i}", "", f"AV{15 + 2 * i}"), f"{'Handfatet' if k.startswith('KB') else 'Tvätthoet'} {k}",
           INGJUTET_MIN, p, [(*p, S.Z_BOTTENPLATTA + TVATTHO_STOS)], False) for i, (k, p) in enumerate(tvatthon().items())),
        (("AV30", "", ""), "Det framtida WC:t i källaren", GRUND, WC_KALLARE,
         [(*WC_KALLARE, S.Z_BOTTENPLATTA + TVATTHO_STOS)], True)]
    # GB1 och GB2 står på grundledningen och går rakt ned i den
    for lid, k, s in (("AV9", "GB1", 0.0), ("AV10", "GB2", s1)):
        x, y = GOLVBRUNNAR_KALLARE[k]
        ut[lid] = Ledning(lid, f"Golvbrunnen {k}", GRUND, ((x, y, zk), (x, y, gl.langs(s)[2])), "AV8")
    # grenarna i ordning längs grundledningen, de närmaste först där flera har samma närmaste punkt (väster om GB1),
    # så att de inte korsar varandra (kontroll)
    def ordning(r: Rad) -> tuple[float, float]:
        s = gl.narmast(r[3][0], r[3][1], 0.0, gl.inne)
        fx, fy, _ = gl.langs(s)
        return round(s), math.hypot(fx - r[3][0], fy - r[3][1])
    for (lid, okning, gren_id), vad, d, (x, y), ovan, samma in sorted(rader, key=ordning):
        gren, z_bojen = _gren(x, y, anslutning(x, y), not samma)
        if samma:                                                   # röret och grenen är en ledning Ø GRUND
            ut[lid] = Ledning(lid, vad + (", ned längs KL2" if lid == "AV1" else ""), d, (*ovan, *gren), "AV8")
            continue
        if okning:
            ut[lid] = Ledning(lid, f"{vad}, rakt ned", d, (*ovan, (x, y, z_ok)), okning)
            ut[okning] = Ledning(okning, f"{vad}, genom bottenplattan", INGJUTET_MIN, ((x, y, z_ok), (x, y, z_bojen)),
                                 gren_id)
        else:
            ut[lid] = Ledning(lid, f"{vad}, rakt ned", d, (*ovan, (x, y, z_bojen)), gren_id)
        ut[gren_id] = Ledning(gren_id, f"{vad}, grenen under bottenplattan", GRUND, gren, "AV8")
    # diskmaskinen i ön: pumpat, ingjutet på tappvattnets nivå, upp mellan överkantsnätets järn i båda ändar
    z = I_BETONGEN["vatten"]
    ax, ay = _mellan_jarnen(DM_ANSLUTNING)
    bx, by = _mellan_jarnen(DM_DISKBANK)
    ut["AV20"] = Ledning("AV20", "Diskmaskinen i ön, pumpat till diskhons vattenlås", DM_ROR,
                         ((ax, ay, 0.0), (ax, ay, z), (ax, Y_DM, z), (bx, Y_DM, z), (bx, by, z),
                          (bx, by, DM_STOS)), "AV5",
                         pumpad=True)
    # luftningen: rakt upp från stammens topp i L11 och från ångbromsen en dimension större ut genom taket
    lx, ly = sx, sy + LUFT_DY
    z_okning = angbromsen(lx, ly) - 10.0
    z_tak = pa_tak(lx, ly).punkt[2]
    ut["LU1"] = Ledning("LU1", "Luftningen i KL8 och L11", LUFTNING[0], ((lx, ly, Z_STAM), (lx, ly, z_okning)), "AV7")
    ut["LU2"] = Ledning("LU2", "Luftningen genom taket", LUFTNING[1], ((lx, ly, z_okning), (lx, ly, z_tak)), "LU1")
    return dict(sorted(ut.items(), key=lambda kv: (kv[0][:2] != "AV", int(kv[0][2:]))))


def _mellan_jarnen(p: tuple[float, float]) -> tuple[float, float]:
    """Ett lodrätt rör (DM_ROR) upp ur bjälklaget från tappvattnets nivå, flyttat så lite som behövs för att gå fritt
    mellan överkantsnätets järn."""
    dx, dy = mellan_jarnen([p], I_BETONGEN["vatten"], 0.0, DM_ROR / 2)
    return p[0] + dx, p[1] + dy


def golvbrunnar() -> dict[str, tuple[float, float, float, float]]:
    """Golvbrunnarna: läge i plan, kroppens diameter och golvets z (för det som ska gå runt dem, t.ex. golvvärmen)."""
    ut = {"GB": (*B.GOLVBRUNN, BRUNN[0], 0.0)}
    ut.update({k: (x, y, BRUNN_KALLARE[0], S.Z_BOTTENPLATTA) for k, (x, y) in GOLVBRUNNAR_KALLARE.items()})
    return ut


def kontroll() -> tuple[list[str], list[str]]:
    """(fel, anmärkningar): fallet på de vågräta styckena, att de ligger under mellanbjälklaget (i källarens tak) och
    under bottenplattans cellplast (grundledningarna), att de ansluter ovanför vattengången i ledningen de går till,
    den fria höjden under dem i källaren, hålen i mellanbjälklaget inom rörens genomstansningszon och luftningens väg
    genom väggen, innertaket och taket (genomforingar: regelfacket, takbalkarna och isoleringen)."""
    fel: list[str] = []
    anm: list[str] = []
    led = ledningar()
    for ld in led.values():
        for (x0, y0, za), (_, _, zb) in ((a, b) for a, b in zip(ld.vag, ld.vag[1:]) if math.dist(a[:2], b[:2]) < 1.0):
            if min(za, zb) < 0.0 and max(za, zb) > -S.H_BJALKLAG:   # lodrätt genom mellanbjälklaget: hål
                pel, avst = min(((p, math.hypot(x0 - px, y0 - py)) for p, (px, py) in PELARE.items()),
                                key=lambda q: q[1])
                if avst < GENOMSTANSNING:
                    anm.append(f"{ld.id}: hålet i bjälklaget {avst:.0f} mm från röret {pel}, inom "
                               "genomstansningszonen")
    # grenarna under bottenplattan ligger i samma nivå och får inte korsa varandra
    under = [(ld.id, a, b) for ld in led.values() if ld.id != "AV8" for a, b in zip(ld.vag, ld.vag[1:])
             if math.dist(a[:2], b[:2]) >= 1.0 and max(a[2], b[2]) < S.Z_BOTTENPLATTA]
    for i, (ida, a0, a1) in enumerate(under):
        for idb, b0, b1 in under[i + 1:]:
            if ida != idb and _korsar(a0, a1, b0, b1):
                fel.append(f"{ida} och {idb} korsar varandra under bottenplattan")
    _, luftfel = genomforingar([Stycke(k, a, b, d, d, True, LUFT_ISOLERING if k == "LU2" else 0.0, matt=f"Ø{d:g}")
                                for k, d in (("LU1", LUFTNING[0]), ("LU2", LUFTNING[1]))
                                for a, b in zip(led[k].vag, led[k].vag[1:])])
    fel += luftfel
    for ld in led.values():
        if ld.pumpad:                                               # ingjutet utan fall, ansluter ovanför golvet
            langd = sum(math.dist(a, b) for a, b in zip(ld.vag, ld.vag[1:]))
            anm.append(f"{ld.id} ({ld.namn}): Ø{ld.d:g} pumpat, {langd / 1000:.1f} m ingjutet och upp ur golvet")
            continue
        lagst = math.inf
        for a, b in zip(ld.vag, ld.vag[1:]):
            lg = math.hypot(b[0] - a[0], b[1] - a[1])
            if lg < 1.0:
                continue                                            # lodrätt
            fall = (a[2] - b[2]) / lg
            if fall < FALL_MIN[ld.d] - 1e-6:
                fel.append(f"{ld.id}: fall {fall * 1000:.1f} ‰ vid ({a[0]:.0f}, {a[1]:.0f}), minst "
                           f"{FALL_MIN[ld.d] * 1000:.0f} ‰")
            topp = max(a[2], b[2]) + ld.d / 2
            if min(a[2], b[2]) > S.Z_BOTTENPLATTA:                 # i källarens tak
                if topp > -S.H_BJALKLAG + 1e-6:
                    fel.append(f"{ld.id}: går i bjälklaget vid ({a[0]:.0f}, {a[1]:.0f})")
                lagst = min(lagst, a[2], b[2])
            elif topp > Z_UK_CELLPLAST + 1e-6:
                anm.append(f"{ld.id}: överkanten {topp - Z_UK_CELLPLAST:.0f} mm upp i cellplasten under bottenplattan "
                           f"vid ({a[0]:.0f}, {a[1]:.0f})")
        fri = lagst - ld.d / 2 - S.Z_BOTTENPLATTA
        if fri < FRI_HOJD:
            anm.append(f"{ld.id}: fri höjd {fri:.0f} mm under röret i källaren")
        if ld.till and vattengang(led[ld.till]) is not None:        # (lodrätt vidare i ett grövre rör: inget att pröva)
            x, y, z = ld.vag[-1]
            zm, dm = _narmast(led[ld.till], x, y), led[ld.till].d
            if z - ld.d / 2 < zm - dm / 2 - 1e-6:
                fel.append(f"{ld.id}: ansluter under {ld.till}s vattengång")
        langd = sum(math.dist(a, b) for a, b in zip(ld.vag, ld.vag[1:]))
        vg = vattengang(ld)
        anm.append(f"{ld.id} ({ld.namn}): Ø{ld.d:g}, {langd / 1000:.1f} m, "
                   + (f"vattengången från {vg[0]:.0f} till {vg[1]:.0f}" if vg else
                      f"lodrätt från {ld.vag[0][2]:.0f} till {ld.vag[-1][2]:.0f}"))
    return fel, anm


def _korsar(a0: Vek, a1: Vek, b0: Vek, b1: Vek) -> bool:
    """Sträckorna a0–a1 och b0–b1 korsar varandra i plan."""
    def sida(p: Vek, q: Vek, r: Vek) -> float:
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    return sida(a0, a1, b0) * sida(a0, a1, b1) < 0.0 and sida(b0, b1, a0) * sida(b0, b1, a1) < 0.0


def vattengang(ld: Ledning) -> tuple[float, float] | None:
    """Vattengången där ledningens första vågräta stycke börjar och i ledningens ände; None för en lodrät ledning."""
    for a, b in zip(ld.vag, ld.vag[1:]):
        if math.hypot(b[0] - a[0], b[1] - a[1]) >= 1.0:
            return a[2] - ld.d / 2, ld.vag[-1][2] - ld.d / 2
    return None


def _narmast(led: Ledning, x: float, y: float) -> float:
    """Ledningens mitt (z) i den punkt på dess vågräta stycken som ligger närmast (x, y) i plan."""
    bast = (math.inf, 0.0)
    for a, b in zip(led.vag, led.vag[1:]):
        lg2 = (b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2
        if lg2 < 1.0:
            continue
        t = min(1.0, max(0.0, ((x - a[0]) * (b[0] - a[0]) + (y - a[1]) * (b[1] - a[1])) / lg2))
        d = math.hypot(a[0] + t * (b[0] - a[0]) - x, a[1] + t * (b[1] - a[1]) - y)
        bast = min(bast, (d, a[2] + t * (b[2] - a[2])))
    return bast[1]


def utdrag() -> dict:
    """För listan och ritningen: ledningarna med punkter, dimension och vattengång, golvbrunnarna, stammen, tvätthonas
    anslutningar, diskmaskinens pumpade avlopp, tvätten i badrummet, luftningen och utloppet."""
    gl = grundledningen()
    led = ledningar()
    return {"ledningar": {k: {"namn": v.namn, "d": v.d, "vag": [list(p) for p in v.vag], "till": v.till,
                              "vattengang": None if v.pumpad else vattengang(v), "pumpad": v.pumpad}
                          for k, v in ledningar().items()},
            "golvbrunnar": {k: {"punkt": [x, y], "d": d, "golv": z} for k, (x, y, d, z) in golvbrunnar().items()},
            "stam": {"punkt": list(STAM[:2]), "d": STAM[2], "topp": Z_STAM, "rensning": RENSNING[0]},
            "luftning": {"punkt": list(led["LU1"].vag[0][:2]), "d": list(LUFTNING), "okning": led["LU2"].vag[0][2],
                         "tak": led["LU2"].vag[-1][2], "huv": list(HUV)},
            "tvatthon": {k: list(p) for k, p in tvatthon().items()},
            "diskmaskin": list(led["AV20"].vag[0][:2]), "diskmaskin_diskbank": list(led["AV20"].vag[-1][:2]),
            "tvatt": list(B.TVATT_AVLOPP), "dm_slang": DM_SLANG,
            "utlopp": {"punkt": list(UTLOPP), "z": gl.langs(gl.inne)[2], "d": GRUND},
            "fall": FALL, "fall_min": FALL_MIN, "gods": GODS, "rh0": S.PLATS.hojd * 1000.0,
            "bottenplattan": S.Z_BOTTENPLATTA, "kallartak": -S.H_BJALKLAG}
