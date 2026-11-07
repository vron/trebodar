"""Avloppet från badrummet (ärende #52) och köket (ärende #49): avloppspunkterna på inredningens lägen (hus/badrum.py,
inredning/koksbank.py), badrummets ledningar under mellanbjälklaget till stammen och kökets rakt ned till grundledningen.
Resten av avloppet, stammen Ø110 i källarväggen KL8 öster om röret P4 och grundledningarna under bottenplattan, är
tills vidare Onshape-modellens (installationer.py, VVS), kapad under bjälklaget, där badrummets samlingsledning
ansluter till stammen (ärende #49: hela avloppet som egen installation).

Avloppspunkterna, var och en med ett rör lodrätt genom bjälklaget (hylsa i formen):
- golvbrunnen i duschen: kroppen ingjuten i bjälklaget med flänsen i dess överkant och lodrätt utlopp Ø75;
- WC:n: S-låset till ett rör Ø110 i golvet WC_AVLOPP från L9;
- tvättstället: vattenlåset Ø32 i skåpet till ett rör Ø50 genom golvet under tvättstället;
- badkaret: vattenlåset under karet till ett rör Ø50 genom golvet under karets mitt.

Under bjälklaget (i källarens tak, med överkanten UPPHANG under betongen): samlingsledningen Ø110 från WC:n norrut
genom källarväggen KL1 och längs KL8 österut till stammen, tvättställets ledning längs V7 till WC:ns, badkarets och
golvbrunnens till samlingsledningen. Fall: Ø110 minst 10 ‰ och de mindre minst 17 ‰ (tillverkarnas anvisningar för
avlopp i byggnad), lagda med FALL. Hålen genom bjälklaget ligger utanför rörens (P4, P8, P9) genomstansningszon 6d
utom golvbrunnens, som K-05 ska pröva (kontrollen redovisar hålen inom GENOMSTANSNING från rören).

Köket: diskhons avlopp (i hons bakre del, bakom diskbänksskåpets lådor) och diskmaskinens i ön (vattenlåset i sockeln
under skåpet O2) går rakt ned, Ø50 genom mellanbjälklaget, källaren och bottenplattan: diskhons längs källarväggen V14,
öns i linje med rören P1, P3 och P5. Under bottenplattan går de med en böj till var sin gren Ø110, vinkelrätt mot
grundledningen och med fallet FALL[110] till den. Grundledningen är tills vidare Onshape-modellens (GRUNDLEDNING, utan
fall); grenarna ansluter med vattengången ANSLUTNING_OVER över dess och går därför med överkanten något upp i
cellplasten under bottenplattan. Kökets luftning hör till luftningen i ärende #49.

Ledningarnas punkter är rörets mitt (x, y, z), z från plan 1:s golv (bjälklagets överkant).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from functools import cache

from trebodar import skelett as S
from trebodar.hus import badrum as B
from trebodar.hus.grund.pelare import PELARE
from trebodar.hus.inredning import koksbank as KB
from trebodar.hus.invandigt.kallare import GIPS_T
from trebodar.hus.invandigt.kallarens_innervaggar import B as KL_VIRKE
from trebodar.hus.invandigt.kallarens_innervaggar import VAGGAR as KL

Vek = tuple[float, float, float]

UPPHANG = 10.0                              # rörens överkant under bjälklagets underkant
FALL = {110.0: 0.010, 75.0: 0.020, 50.0: 0.020}     # lagt fall per ytterdiameter
FALL_MIN = {110.0: 0.010, 75.0: 0.017, 50.0: 0.017}  # minsta fall (tillverkarnas anvisningar)
FRI_HOJD = 1900.0                           # minsta fria höjd under rören i källaren (anmärkning)
GENOMSTANSNING = 720.0                      # rörens genomstansningszon i bjälklaget, 6d (anmärkning för hål inom den)
GODS = {110.0: 3.4, 75.0: 3.0, 50.0: 1.8, 40.0: 1.8, 32.0: 1.8}
STAM = (3040.0, 7675.0, 110.0)              # stammen (Onshape-modellen, kallarens_innervaggar.AVLOPPSSTAM)
Z_STAM = -190.0                             # stammens topp: Onshape-modellens stam kapad här (installationer.py)
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
# grundledningen under bottenplattan (Onshape-modellens, installationer.py): från stammen till husets hörn mot 3NO,
# mitten i z, Ø; köket ansluter till den (KOK)
GRUNDLEDNING = ((3040.0, 7675.0), (13840.0, 970.0), -2750.0, 110.0)
ANSLUTNING_OVER = 2.0                       # grenens vattengång över grundledningens där den ansluter
KOK = {"AV5": ("Diskbänken", KB.diskhons_avlopp()), "AV7": ("Diskmaskinen i ön", KB.ons_avlopp())}


@dataclass(frozen=True)
class Ledning:
    id: str
    namn: str
    d: float
    vag: tuple[Vek, ...]                    # rörets mitt
    till: str = ""                          # ledningen den ansluter till (tom: stammen)


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


@cache
def ledningar() -> dict[str, Ledning]:
    """Badrummets ledningar: samlingsledningen från WC:n till stammen och grenarna till den."""
    ut: dict[str, Ledning] = {}
    xs, ys = X_SAMLING, B.WC_Y
    sx, sy, sd = STAM
    samling = [(xs, ys, B.golvniva(xs, ys))] + _fall((xs, ys, Z_SAMLING),
                                                     [(xs, Y_KL8), (sx, Y_KL8), (sx, sy - sd / 2)], 110.0)
    ut["AV1"] = Ledning("AV1", "WC:n och samlingsledningen till stammen", 110.0, tuple(samling))
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
    # köket: rakt ned i grenen under bottenplattan och den till grundledningen
    for id_, (namn, (x, y)) in KOK.items():
        id_gren = f"AV{int(id_[2:]) + 1}"
        gren, z_bojen = _gren(x, y)
        ut[id_] = Ledning(id_, f"{namn}, rakt ned", 50.0, ((x, y, 0.0), (x, y, z_bojen)), id_gren)
        ut[id_gren] = Ledning(id_gren, f"{namn}, grenen under bottenplattan", 110.0, gren, "GL")
    return ut


def _gren(x: float, y: float, d: float = 110.0) -> tuple[tuple[Vek, Vek], float]:
    """Grenen Ø d under bottenplattan, vinkelrätt mot grundledningen från det lodräta röret i (x, y) till grundledningens
    yta, med fallet FALL[d] och vattengången ANSLUTNING_OVER över grundledningens där den ansluter; den börjar sin radie
    bakom det lodräta röret (böjen). Grenens ändar och dess mitt (z) under det lodräta röret."""
    (ax, ay), (bx, by), zg, dg = GRUNDLEDNING
    lg = math.hypot(bx - ax, by - ay)
    ux, uy = (bx - ax) / lg, (by - ay) / lg
    t = (x - ax) * ux + (y - ay) * uy
    fx, fy = ax + t * ux - x, ay + t * uy - y               # till foten på grundledningens mittlinje
    lang = math.hypot(fx, fy)
    vx, vy = fx / lang, fy / lang
    z_slut = zg - dg / 2 + d / 2 + ANSLUTNING_OVER
    z_bojen = z_slut + FALL[d] * (lang - dg / 2)
    return ((x - vx * d / 2, y - vy * d / 2, z_bojen + FALL[d] * d / 2),
            (x + vx * (lang - dg / 2), y + vy * (lang - dg / 2), z_slut)), z_bojen


def kontroll() -> tuple[list[str], list[str]]:
    """(fel, anmärkningar): fallet på de vågräta styckena, att de ligger under bjälklaget och ansluter ovanför
    vattengången i ledningen (eller grundledningen, "GL") som de går till, den fria höjden under dem i källaren (inte
    grenarna under bottenplattan) och hålen i bjälklaget inom rörens genomstansningszon."""
    fel: list[str] = []
    anm: list[str] = []
    led = ledningar()
    for ld in led.values():
        x0, y0, z0 = ld.vag[0]
        if z0 > -S.H_BJALKLAG:                                      # börjar i eller på bjälklaget: hål genom det
            pel, avst = min(((p, math.hypot(x0 - px, y0 - py)) for p, (px, py) in PELARE.items()), key=lambda q: q[1])
            if avst < GENOMSTANSNING:
                anm.append(f"{ld.id}: hålet i bjälklaget {avst:.0f} mm från röret {pel}, inom genomstansningszonen")
        lagst = math.inf
        for a, b in zip(ld.vag, ld.vag[1:]):
            lg = math.hypot(b[0] - a[0], b[1] - a[1])
            if lg < 1.0:
                continue                                            # lodrätt
            fall = (a[2] - b[2]) / lg
            if fall < FALL_MIN[ld.d] - 1e-6:
                fel.append(f"{ld.id}: fall {fall * 1000:.1f} ‰ vid ({a[0]:.0f}, {a[1]:.0f}), minst "
                           f"{FALL_MIN[ld.d] * 1000:.0f} ‰")
            if max(a[2], b[2]) + ld.d / 2 > -S.H_BJALKLAG + 1e-6:
                fel.append(f"{ld.id}: går i bjälklaget vid ({a[0]:.0f}, {a[1]:.0f})")
            if min(a[2], b[2]) > S.Z_BOTTENPLATTA:                 # i källaren
                lagst = min(lagst, a[2], b[2])
        fri = lagst - ld.d / 2 - S.Z_BOTTENPLATTA
        if fri < FRI_HOJD:
            anm.append(f"{ld.id}: fri höjd {fri:.0f} mm under röret i källaren")
        if ld.till:
            x, y, z = ld.vag[-1]
            zm, dm = (GRUNDLEDNING[2], GRUNDLEDNING[3]) if ld.till == "GL" else (_narmast(led[ld.till], x, y),
                                                                                  led[ld.till].d)
            if z - ld.d / 2 < zm - dm / 2 - 1e-6:
                fel.append(f"{ld.id}: ansluter under {'grundledningen' if ld.till == 'GL' else ld.till}s vattengång")
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
    """För listan: ledningarna med punkter, dimension och fall, och golvbrunnen."""
    return {"ledningar": {k: {"namn": v.namn, "d": v.d, "vag": [list(p) for p in v.vag], "till": v.till,
                              "vattengang": vattengang(v)} for k, v in ledningar().items()},
            "golvbrunn": {"punkt": list(B.GOLVBRUNN), "d": BRUNN[0], "djup": BRUNN[1], "golv": B.BRUNN_Z},
            "stam": {"punkt": list(STAM[:2]), "d": STAM[2], "topp": Z_STAM},
            "grundledning": {"fran": list(GRUNDLEDNING[0]), "till": list(GRUNDLEDNING[1]), "z": GRUNDLEDNING[2],
                             "d": GRUNDLEDNING[3]}, "fall": FALL, "fall_min": FALL_MIN}
