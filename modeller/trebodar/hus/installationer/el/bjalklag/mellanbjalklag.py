"""Grupprören ingjutna i mellanbjälklaget (#50, #51): ett rör per grupp från gruppcentralen i teknikrummet till
gruppens första punkt på plan 1 (../grupper.py), och därifrån vidare mellan punkterna (../kedjor.py).

Rören går upp ur centralens ovansida rakt in i bjälklaget, i två rader mellan underkantsnätets järn: den främre
(RAD_A) ovanför centralen och den bakre (RAD_B) i V3:s cellplast bakom gipsen (rören går in i väggen ur centralens
ovansida). Där finns plats för dem väster om ventilationens kanal FF3-K2, som går över centralens östra del. I
bjälklaget går de klena rören (Ø16) i elrörens övre nivå, över tappvattnet och golvvärmen (montering.BJALKLAG "MB"),
och hällens grova rör (Ø20) i den undre, i tappvattnets nivå men fritt från dess rör ("MB-UK").

Rören går i stråk, ett rör per fil (..strak: filen genom rörets stigare, stråket förskjutet i sidled), och viker av
ur stråket mot sin punkt, det som viker av först ytterst mot sin sida, så att de inte korsar varandra:

- S från den främre raden norrut, österut förbi ventilationens stigare (FF3-K2) och norrut öster om badrummet till
  badrummet och sovrummet i vänstra huskroppen;
- E från den främre raden norrut och österut genom glipan mellan V19:s och V15:s järn till köket och högra
  huskroppen, och norrut till gången;
- N från den bakre raden söderut över V3 och västerut till hallen och vardagsrummet (plattan på mark);
- hällens rör (Ø20) från den bakre raden söderut över V3 och österut i den undre nivån, söder om tappvattnets rör,
  genom glipan mellan V20:s och V15:s järn till hällens anslutning på 3NV.

Rören går upp ur bjälklaget till punktens dosa lodrätt under den, mellan överkantsnätets järn (../dragning.py).
Brandlarmets matningsdosa D01 (BL-D01, ../../brandlarm) matas från allrummets dimmer genom bjälklaget.
"""
from __future__ import annotations

from collections.abc import Sequence

from shapely.geometry import LineString, Point

from ...montering import BJALKLAG, KALLARTAK, Vek, kallartak
from ...strak import Strak, fri, vag
from ...teknikrum import GRUPPCENTRAL, Z_GC_TOPP
from ..dragning import upp_ur_bjalklaget
from ..grupper import BRANDLARM_D01
from ..katalog import BRANDLARM_MATNING, FXP16, FXP20
from ..punkter import Dosa, Ror
from ..typer import Rortyp
from ..rum import allrum, badrum, gastrum, hall, kok, sovrum

NAMN = "Mellanbjälklag"

_TOPP = GRUPPCENTRAL.anslutningar["topp"]
X_RAD = (_TOPP[0] - 292.0, 2735.0)          # rörens x på centralens ovansida: från dess västra kant till kanalen
CC = 21.0                                    # stigarnas avstånd i raderna (Ø16, 5 mm emellan)
RAD_A = _TOPP[1] - 42.0                      # främre raden, ovanför centralen
RAD_B = _TOPP[1] + 103.0                     # bakre raden, i V3:s cellplast bakom gipsen
SPEL = 5.0
OVER = 15.0                                  # rören in i väggen ur centralens ovansida så högt över den


def _rad(y: float, z: float, r: float = 8.0, over_v3: Sequence[float] = ()) -> list[float]:
    """Stigarnas x i en rad: tätt (CC) från centralens västra kant, där röret går fritt mellan järnen från källarens
    tak till nivån z (och, för rören som går ur raden över V3, i nivåerna över V3 mellan dess järn)."""
    ut: list[float] = []
    x = X_RAD[0]
    while x <= X_RAD[1]:
        if (not ut or x - ut[-1] >= CC - 1e-6) and fri(Point(x, y), r, KALLARTAK, z, SPEL) and all(
                fri(LineString([(x, y), (x, y + 400.0)]), 10.0, h - 1.0, h + 1.0, SPEL) for h in over_v3):
            ut.append(x)
        x += 1.0
    return ut


_A = _rad(RAD_A, BJALKLAG["MB"])
_B = _rad(RAD_B, BJALKLAG["MB"], over_v3=(BJALKLAG["MB"], BJALKLAG["MB-UK"]))

# stråken: stigarna och stråkets brytpunkter (det första stycket vinkelrätt mot raden)
# den främre raden: S de västra (utom stigaren vid tappvattnets stigare BA-DU1-KV, som S går förbi), E de östra; den
# bakre raden: N de västra, och österut till ön och hällen
S_STIG, E_STIG = _A[0:6], _A[6:12]
N_STIG, ON_STIG, HALL_STIG, KA_STIG, G24_STIG = _B[:2], _B[2], _B[5], _B[4], _B[3]   # KA_STIG: källarens stora
#                       rum (G17), G24_STIG: dess uttag och FF3 (längre söderut än G17, så västligare, utan att korsa)
Y_S, X_S, Y_S_SLUT = 8400.0, 3480.0, 4380.0     # S: österut i y, norrut i x till V7:s vinkeljärn
Y_E, X_E_SLUT = 8587.0, 13100.0                 # E: österut i y, i glipan mellan V19:s och V15:s järn och norr om
#                                                 V3:s vinkeljärn, till V14:s vinkeljärn
Y_N = 9400.0                                     # N: västerut i y
Y_ON = 9645.0                                    # till ön och hällen: österut i y, genom glipan mellan V20:s och V15:s
#                                                  järn, öns rör i den övre nivån och hällens rakt under det i den undre
X_HALL = 13000.0                                 # hällens rör till y för hällens anslutning, före V14:s vinkeljärn


def _mitt(xs: Sequence[float]) -> float:
    return (min(xs) + max(xs)) / 2


def _strak(namn: str, xs: Sequence[float], y0: float, punkter: Sequence[tuple[float, float]]) -> Strak:
    return Strak(namn, ((_mitt(xs), y0), *punkter))


STRAK = {
    "S": _strak("S", S_STIG, RAD_A, ((_mitt(S_STIG), Y_S), (X_S, Y_S), (X_S, Y_S_SLUT))),
    "E": _strak("E", E_STIG, RAD_A, ((_mitt(E_STIG), Y_E), (X_E_SLUT, Y_E))),
}


def ur_raden(x: float, rad: float, niva: str) -> tuple[Vek, ...]:
    """Röret ur centralens ovansida (bakre raden: in i väggen) och upp till nivån i bjälklaget."""
    z = BJALKLAG[niva]
    if rad == RAD_A:
        return (x, rad, Z_GC_TOPP), (x, rad, z)
    return (x, _TOPP[1] + 40.0, Z_GC_TOPP), (x, _TOPP[1] + 40.0, Z_GC_TOPP + OVER), (x, rad, Z_GC_TOPP + OVER), (x, rad, z)


def i_straket(x: float, strak: str, mal: Sequence[tuple[float, float]], upp: tuple[Vek, ...]) -> tuple[Vek, ...]:
    """Från stigaren x i den främre raden längs sin fil i stråket till punkten närmast mal[0], genom mal (i plan) och
    upp till dosan."""
    z = BJALKLAG["MB"]
    return ((x, RAD_A, Z_GC_TOPP), *vag((x, RAD_A, z), z, STRAK[strak], tuple(mal), upp))


_PUNKT = {p.id: p for m in (allrum, badrum, gastrum, hall, kok, sovrum) for p in m.PUNKTER}


def _upp(p: str, niva: str = "MB", d: float = 16.0) -> tuple[Vek, ...]:
    """Röret upp ur bjälklaget till punktens dosa (../dragning.py)."""
    return upp_ur_bjalklaget(_PUNKT[p], niva=niva, d=d)


def _ror(grupp: str, strak: str, x: float, p: str, via_y: float | None = None, via_x: float | None = None) -> Ror:
    """Gruppens rör i stråket från stigaren x till punkten p: ur filen rakt mot punkten, eller först till y via_y
    (eller x via_x) och därifrån till punktens stigare, och upp till dosan."""
    upp = _upp(p)
    xt, yt = upp[0][0], upp[0][1]
    mal = [(xt, via_y)] if via_y is not None else [(via_x, yt)] if via_x is not None else []
    return Ror(f"{grupp}-M", FXP16, "GC", p, via=i_straket(x, strak, (*mal, (xt, yt)), upp[1:]))


def _over_v3(grupp: str, x: float, p: str, y: float, mal: Sequence[tuple[float, float]], typ: Rortyp = FXP16,
             niva: str = "MB") -> Ror:
    """Från den bakre raden söderut över V3 till y, och därifrån genom mal till punktens stigare och upp."""
    upp = _upp(p, niva=niva, d=typ.ytterdiameter)
    z = BJALKLAG[niva]
    plan = [(x, y), *mal, (upp[0][0], upp[0][1])]
    return Ror(f"{grupp}-M", typ, "GC", p, via=(*ur_raden(x, RAD_B, niva), *((a, b, z) for a, b in plan), *upp[1:]))


# brandlarmets matningsdosa D01 (../../brandlarm/larm.py): en punkt utan egen geometri, matad från allrummets dimmer
D01 = BRANDLARM_D01
PUNKTER = [
    Dosa("BL-D01", BRANDLARM_MATNING, kallartak(*D01)),
]

_ON = kok.X_ON_ROR
_HA = _upp("HA-B1")[0]
_HU = _upp("HA-U1")[0]
_KD = _upp("KO-D1", niva="MB-UK", d=20.0)[0]

ROR = [
    # S: stigarna från väster; det som viker av först ytterst (västerut i ordning norrut, österut sist); S_STIG[1]
    # går till källarens små rum (G18, ../rum/kallare.py)
    _ror("G05", "S", S_STIG[0], "BA-B1"),
    _ror("G09", "S", S_STIG[2], "BA-U3", via_y=5160.0),
    _ror("G08", "S", S_STIG[3], "BA-U2", via_y=5130.0),
    _ror("G07", "S", S_STIG[4], "BA-U1", via_y=Y_S_SLUT + 20.0),
    _ror("G03", "S", S_STIG[5], "SV-B1"),
    # E: norr om mitten det som viker av norrut (i ordning österut), söder om den det som viker av söderut
    _ror("G02", "E", E_STIG[0], "AL-B1"),
    _ror("G04", "E", E_STIG[1], "GR-B1"),
    _ror("G15", "E", E_STIG[2], "KO-U4"),
    _ror("G11", "E", E_STIG[3], "KO-U6", via_x=X_E_SLUT - 80.0),
    _ror("G12", "E", E_STIG[4], "KO-U8", via_x=X_E_SLUT - 55.0),
    _ror("G14", "E", E_STIG[5], "KO-U7", via_x=11200.0),
    # N och österut från den bakre raden söderut över V3
    _over_v3("G01", N_STIG[0], "HA-B1", Y_N - 32.0, [(_HA[0], Y_N - 32.0)]),
    _over_v3("G06", N_STIG[1], "HA-U1", Y_N + 32.0, [(_HU[0], Y_N + 32.0)]),
    _over_v3("G13", ON_STIG, "KO-U11", Y_ON, [(_ON, Y_ON)]),
    _over_v3("G10", HALL_STIG, "KO-D1", Y_ON, [(X_HALL, Y_ON), (X_HALL, _KD[1])], FXP20, "MB-UK"),
]
