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
Under bjälklaget (i källarens tak, med överkanten UPPHANG under betongen) samlingsledningen Ø110 från WC:n norrut
genom källarväggen KL1 och längs KL8 österut till stammen, tvättställets ledning längs V7 till WC:ns, badkarets,
golvbrunnens och tvättens till samlingsledningen (tvättens under KL2:s hammarband genom väggen). Hålen genom bjälklaget ligger utanför rörens (P4, P8, P9) genomstansningszon 6d
utom golvbrunnens, som K-05 ska pröva (kontrollen redovisar hålen inom GENOMSTANSNING från rören).

Köket: diskhons avlopp (i hons bakre del, bakom diskbänksskåpets lådor) går rakt ned, Ø50 genom mellanbjälklaget,
källaren längs källarväggen V14 och bottenplattan, och med en böj till en gren Ø110 till grundledningen. Diskmaskinen
i ön (#50) har ett pumpat avlopp (AV20): maskinens egen pump trycker vattnet genom ett rör PEX 25 utan fall, ingjutet
i mellanbjälklaget på tappvattnets nivå, från anslutningen under maskinen till diskbänksskåpet bakom lådorna, där
slangen går upp till diskhons vattenlås (dess anslutning för diskmaskin, med en ögla under bänkskivan). Ett avlopp med
självfall ryms inte mellan armeringsnäten (#49). Röret går förbi tappvattnets matning till underfördelaren UF1, så att
det inte korsar den; maskinen ska tillåta så lång slang (DM_SLANG).

Stammen Ø110 står i källarväggen KL8 (kallarens_innervaggar.AVLOPPSSTAM) under badrummets vägg L11, från toppen
Z_STAM ned genom bottenplattan, med rensningen RENSNING över källargolvet mot teknikrummet, och går med en böj och en
kort sträcka till grundledningen.

Luftningen (avluftningen) går rakt upp från stammens topp, dold i väggarna: i KL8, genom mellanbjälklaget och upp i
L11:s regelfack (Ø50, LU1; väggens stomme 70 mm rymmer inte Ø75), och från innertakets installationsskikt en dimension
större (Ø75, LU2, mot frost) isolerad genom takets isolering och ut genom taket till luftningshuven (HUV).

Källaren: fem golvbrunnar (GOLVBRUNNAR_KALLARE, efter användarens skiss) med kroppen ingjuten i bottenplattans
betong och lodrätt utlopp Ø110; tvättmaskinen töms i golvbrunnen GB1 bredvid den. Tvätthona (tappvattnets
KA-TH1–KA-TH3, som inte är modellerade) får var sin anslutning Ø50 i golvet framför väggdosan (TVATTHO_AVSTAND), rakt
ned till en gren.

Grundledningen Ø110 under bottenplattan börjar i golvbrunnen GB1 vid tvätten, går österut genom GB2 i teknikrummet,
söder om köldbärarens rör där de går upp genom plattan, och därifrån rakt mot nordost ut under källarväggen V9
(UTLOPP). Direkt utanför väggen faller den brant under dräneringen runt grunden (UTLOPP_FALL) och fortsätter åt
nordost, längs dagvattnets utgående rör, mot förbindelsepunkten (UTLOPP_L av den ritas). Överkanten ligger
UNDER_CELLPLAST under bottenplattans cellplast där den börjar. Grenarna går vinkelrätt mot den (de nära varandra något
förskjutna, minst GREN_AVSTAND isär) och ansluter med vattengången ANSLUTNING_OVER över dess.

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
from trebodar.hus.invandigt.kallarens_innervaggar import AVLOPPSSTAM
from trebodar.hus.invandigt.kallarens_innervaggar import B as KL_VIRKE
from trebodar.hus.invandigt.kallarens_innervaggar import VAGGAR as KL
from trebodar.hus.invandigt.vaggar import vaggdef

from ..dranering.ledningar import UTLOPP_RIKTNING
from ..genomforingar import Stycke, genomforingar
from ..montering import I_BETONGEN, angbromsen, pa_tak
from ..strak import mellan_jarnen
from ..vatten.rum import kallare as vattnet_i_kallaren

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
X_SAMLING = B.X_L9 - B.WC_AVLOPP            # samlingsledningen norrut i WC:ns linje
Y_KL8 = KL["KL8"].c - KL["KL8"].h - GIPS_T - 10.0 - 55.0      # österut längs KL8, 10 mm från dess gips
# samlingsledningen går under KL1:s hammarband (FRI under det där den går genom väggen) och faller därifrån
FRI = 5.0
_Y_KL1 = KL["KL1"].c - KL["KL1"].h - GIPS_T                   # KL1:s gips mot söder
Z_SAMLING = -S.H_BJALKLAG - KL_VIRKE - FRI - 55.0 + FALL[110.0] * (_Y_KL1 - B.WC_Y)     # mitten vid WC:n
TVATTSTALL_AVLOPP = (B.X_TVATTSTALL, B.Y_1NO + 260.0)      # under tvättställets mitt (inredning/badrum.py)
BADKAR_AVLOPP = ((B.BADKAR_X[0] + B.BADKAR_X[1]) / 2, (B.BADKAR_Y[0] + B.BADKAR_Y[1]) / 2)
BADKAR_BOTTEN = B.Z_BADKAR + B.BADKAR_KAR                        # karets botten
BRUNN = (200.0, 100.0)                      # golvbrunnens kropp: diameter, djup under flänsen
BRUNN_SIL = (220.0, 230.0)                  # silen och klämringen (hålet i golvets skikt, badrumsgolv.BRUNN_HAL)
DISKHO = KB.diskhons_avlopp()               # diskhons avlopp i plan
# diskmaskinens pumpade avlopp (AV20): från anslutningen under maskinen till DM_SODER och snett till diskbänksskåpet
# bakom lådorna, förbi tappvattnets matning till UF1 (som kommer ned till underfördelaren vid y 8 825)
DM_ROR = 25.0                               # PEX 25 × 2,3
DM_ANSLUTNING = KB.diskmaskinens_anslutningar()[1]
DM_SODER = 8700.0                           # längs ön till hit, förbi matningen till UF1 (y 8 825)
DM_DISKBANK = (13500.0, 8200.0)             # upp i diskbänksskåpet bakom lådorna
DM_STOS = 100.0                             # rörets ände i diskbänksskåpet över golvet, där slangen ansluter (under
#                                             maskinen slutar det i golvet)
DM_SLANG = 4.0                              # så lång avloppsslang ska diskmaskinen tillåta (maskinen till vattenlåset) [m]
assert KB.FOGAR_LANG[1] + 100.0 <= DM_DISKBANK[1] <= KB.FOGAR_LANG[2] - 100.0, "röret upp i diskbänksskåpet"
# tvättens vattenlås på L10 i skåpet i badrummet: röret i väggens regelfack och genom bjälklaget (hus/badrum.py)
TVATT_AVLOPP = (B.TVATT_AVLOPP[0], vaggdef("L10").origo[1] + vaggdef("L10").tjocklek / 2)
_X_KL2 = KL["KL2"].c + KL["KL2"].t / 2 + GIPS_T                 # KL2:s gips mot öster, där tvättens ledning går genom
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
                       "GB4": (3850.0, 4180.0),            # vid tvätthoet KA-TH3 på V7 (skissen: 1,2 m söderut), så
                       "GB5": (11310.0, 3430.0)}           # att golvvärmens slinga ryms i rummet öster om KL2
BRUNN_KALLARE = (200.0, G.H_PLATTA)         # golvbrunnens kropp i källaren: diameter och djup (plattans betong)
TVATTHO_AVSTAND = 150.0                     # tvätthoets avlopp i golvet från väggens gips
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
    """Tvätthonas avlopp i golvet: TVATTHO_AVSTAND framför väggdosan (tappvattnets KA-TH1–KA-TH3)."""
    ut = {}
    for t in vattnet_i_kallaren.TAPPSTALLEN:
        if t.typ.kod == "TH":
            (x, y, _), (nx, ny, _) = t.lage.punkt, t.lage.normal
            ut[t.id] = (x + nx * TVATTHO_AVSTAND, y + ny * TVATTHO_AVSTAND)
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
    """Alla ledningar: badrummets till stammen, köket, stammen, grundledningen och källarens grenar till den."""
    ut: dict[str, Ledning] = {}
    xs, ys = X_SAMLING, B.WC_Y
    sx, sy, sd = STAM
    samling = [(xs, ys, B.golvniva(xs, ys))] + _fall((xs, ys, Z_SAMLING),
                                                     [(xs, Y_KL8), (sx, Y_KL8), (sx, sy - sd / 2)], 110.0)
    ut["AV1"] = Ledning("AV1", "WC:n och samlingsledningen till stammen", 110.0, tuple(samling), "AV7")
    # tvättställets: genom golvet under tvättstället, längs V7 och norrut till WC:ns lodräta rör
    xt, yt = B.X_TVATTSTALL, TVATTSTALL_AVLOPP[1]
    ts = [(xt, yt, B.golvniva(xt, yt))] + _fall((xt, yt, _under(50.0)),
                                                [(xs - 85.0, yt), (xs - 85.0, ys), (xs - 55.0, ys)], 50.0)
    ut["AV2"] = Ledning("AV2", "Tvättstället", 50.0, tuple(ts), "AV1")
    # badkarets: genom golvet under karets mitt, österut till samlingsledningen
    xb, yb = BADKAR_AVLOPP
    bk = [(xb, yb, B.golvniva(xb, yb))] + _fall((xb, yb, _under(50.0)), [(xs - 55.0, yb)], 50.0)
    ut["AV3"] = Ledning("AV3", "Badkaret", 50.0, tuple(bk), "AV1")
    # golvbrunnens: lodrätt utlopp ur kroppen, norrut till samlingsledningen längs KL8
    gx, gy = B.GOLVBRUNN
    gb = [(gx, gy, -BRUNN[1])] + _fall((gx, gy, _under(75.0)), [(gx, Y_KL8 - 55.0)], 75.0)
    ut["AV4"] = Ledning("AV4", "Golvbrunnen i duschen", 75.0, tuple(gb), "AV1")
    # tvätten i skåpet: ned i L10 och under bjälklaget västerut till samlingsledningen, under KL2:s hammarband
    xv, yv = TVATT_AVLOPP
    z_kl2 = -S.H_BJALKLAG - KL_VIRKE - FRI - 25.0                   # mitten under hammarbandet
    zv = z_kl2 + FALL[50.0] * (xv - _X_KL2)
    tv = [(xv, yv, B.golvniva(xv, B.Y_L10 + 50.0) + B.TVATT_AVLOPP[1])] + _fall((xv, yv, zv), [(xs + 55.0, yv)], 50.0)
    ut["AV21"] = Ledning("AV21", "Tvätten i badrummets skåp", 50.0, tuple(tv), "AV1")

    # grundledningen och grenarna till den, i ordning längs den (anslutningarna minst GREN_AVSTAND isär)
    gl = grundledningen()
    s1 = math.dist(*gl.punkter[:2])                                 # GB2, där ledningen viker mot nordost
    upptagna = [0.0, s1]

    def anslutning(x: float, y: float, s_min: float, s_max: float) -> float:
        s = gl.narmast(x, y, s_min, s_max)
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
    # stammen: lodrätt i KL8 och med en böj söderut till grundledningens första sträcka
    gren, _ = _gren(sx, sy, anslutning(sx, sy, GREN_AVSTAND, s1 - GREN_AVSTAND), False)
    ut["AV7"] = Ledning("AV7", "Stammen i KL8", GRUND, ((sx, sy, Z_STAM),) + gren, "AV8")
    # golvbrunnarna: GB1 och GB2 rakt ned i grundledningen, de andra med var sin gren
    nr = 9
    zk = S.Z_BOTTENPLATTA - BRUNN_KALLARE[1]                       # kropparnas botten
    for k, (x, y) in GOLVBRUNNAR_KALLARE.items():
        if k in ("GB1", "GB2"):
            zg = gl.langs(0.0 if k == "GB1" else s1)[2]
            vag: tuple[Vek, ...] = ((x, y, zk), (x, y, zg))
        else:
            gren, _ = _gren(x, y, anslutning(x, y, s1, gl.inne - GREN_AVSTAND), False)
            vag = ((x, y, zk),) + gren
        ut[f"AV{nr}"] = Ledning(f"AV{nr}", f"Golvbrunnen {k}", GRUND, vag, "AV8")
        nr += 1
    # köket och tvätthona: rakt ned Ø50 och med en böj till en gren
    for namn, (x, y), z_topp in (("Diskbänken", DISKHO, 0.0),
                                 *((f"Tvätthoet {k}", p, S.Z_BOTTENPLATTA + TVATTHO_STOS)
                                   for k, p in tvatthon().items())):
        i_lodratt = "AV5" if namn == "Diskbänken" else f"AV{nr}"
        i_gren = "AV6" if namn == "Diskbänken" else f"AV{nr + 1}"
        if namn != "Diskbänken":
            nr += 2
        s_min = GREN_AVSTAND if gl.narmast(x, y, 0.0, s1) < s1 - 1.0 else s1
        gren, z_bojen = _gren(x, y, anslutning(x, y, s_min, gl.inne - GREN_AVSTAND), True)
        ut[i_lodratt] = Ledning(i_lodratt, f"{namn}, rakt ned", 50.0, ((x, y, z_topp), (x, y, z_bojen)), i_gren)
        ut[i_gren] = Ledning(i_gren, f"{namn}, grenen under bottenplattan", GRUND, gren, "AV8")
    # diskmaskinen i ön: pumpat, ingjutet på tappvattnets nivå, upp mellan överkantsnätets järn i båda ändar
    z = I_BETONGEN["vatten"]
    ax, ay = _mellan_jarnen(DM_ANSLUTNING)
    bx, by = _mellan_jarnen(DM_DISKBANK)
    ut["AV20"] = Ledning("AV20", "Diskmaskinen i ön, pumpat till diskhons vattenlås", DM_ROR,
                         ((ax, ay, 0.0), (ax, ay, z), (ax, DM_SODER, z), (bx, by, z), (bx, by, DM_STOS)), "AV5",
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
        if ld.till:
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
