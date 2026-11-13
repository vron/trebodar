"""Badrummet (ärende #52) på inredningens lägen i hus/badrum.py: duschens blandare på L11 mitt i nischen, badkarets
blandare på 1SO mitt för karet (#97), WC:n på L9 och tvättstället i badrumsbänken längs 1NO. Rören kommer upp genom
bjälklaget från stråket S i mellanbjälklaget: i väggarnas regelfack eller installationsskikt till väggdosorna (duschen,
badkaret, WC:n) och genom golvet till golvdosan (tvättstället, i skåpet under det).

Tvättmaskinen i skåpet i nischen (#51, förberedd) har en egen väggdosa på L10 i glipan bredvid maskinerna, med kallt
från underfördelaren UF2 under badrummet, som också matar WC:n (underfordelare.py); de andra kommer från stråket S.

Duschens blandare sitter på L11 i nischens främre del, mitt i regelfacket mellan L11-R05 och L11-R06. WC:ns väggdosa sitter vid sidan av cisternen i regelfacket mellan L9-R02 och
L9-R03. Golvdosorna står i golvets färdiga yta (klinkern över fallavjämningen) och dosornas höjd räknas från golvet.
"""
from __future__ import annotations

from trebodar import skelett as S
from trebodar.hus import badrum as B
from trebodar.hus.invandigt.vaggar import vaggdef

from ...montering import Montering, vagg
from ..katalog import (BADKAR, DUSCH, GOLVDOSA, ROR_I_ROR_15, ROR_I_ROR_16, ROR_I_ROR_18, TVATTMASKIN, TVATTSTALL,
                       VAGGDOSA, VAGGDOSA_BLANDARE, WC)
from ..punkter import Rum, Tappstalle, Via

RUM = Rum("BA", "Badrum", plan=1)

Y_WC_DOSA = B.WC_Y - 180.0                  # WC:ns väggdosa vid sidan av cisternen, i regelfacket
Z_WC_DOSA = 150.0                           # över golvet
TS_DOSA = (B.X_TVATTSTALL - 160.0, B.Y_1NO + 150.0)     # tvättställets golvdosa i skåpet, vid sidan av vattenlåset


def _golv(x: float, y: float) -> Montering:
    """På badrummets golv: klinkerns yta (golvets fall, hus/badrum.py)."""
    return Montering((x, y, B.golvniva(x, y)), (0.0, 0.0, 1.0), "golv", "MB")


def _over_golvet(kod: str, u: float, z: float, sida: int) -> Montering:
    """På väggens färdiga yta vid u, z över golvet vid väggen."""
    m = vagg(kod, u, 0.0, sida)
    x, y, _ = m.punkt
    return vagg(kod, u, B.golvniva(x + m.normal[0] * 2.0, y + m.normal[1] * 2.0) + z, sida)


# duschens rör från stråket S2 söder om 1A (minst 200 mm från 1A:s och 1B:s bultar), under badrummet österut till
# nischen och längs L11 norrut till blandaren; varmvattnet ytterst, så att rören inte korsar varandra (#114)
DUSCHENS_VAG: dict[str, Via | tuple[Via, ...]] = {"KV": ((3200.0, 6250.0), (3200.0, None)), "VV": ((3164.0, 6286.0), (3164.0, None))}

TAPPSTALLEN = [
    Tappstalle("BA-DU1", DUSCH, VAGGDOSA_BLANDARE,
               _over_golvet("L11", B.Y_DUSCHBLANDARE - vaggdef("L11").origo[1], B.Z_DUSCHBLANDARE, 1),
               ROR_I_ROR_16, via=DUSCHENS_VAG),
    Tappstalle("BA-BK1", BADKAR, VAGGDOSA_BLANDARE,
               _over_golvet("1SO", S.YTTERVAGGAR["1SO"].origo[1] - B.BADKARSBLANDARE[1], B.Z_BADKARSBLANDARE, 1),
               ROR_I_ROR_18),
    Tappstalle("BA-WC1", WC, VAGGDOSA, _over_golvet("L9", Y_WC_DOSA - vaggdef("L9").origo[1], Z_WC_DOSA, 1),
               ROR_I_ROR_15),
    Tappstalle("BA-TS1", TVATTSTALL, GOLVDOSA, _golv(*TS_DOSA), ROR_I_ROR_15, kallt=(0.0, 1.0, 0.0)),
    Tappstalle("BA-TM1", TVATTMASKIN, VAGGDOSA,
               _over_golvet("L10", B.TVATT_VATTEN[0] - vaggdef("L10").origo[0], B.TVATT_VATTEN[1], 1), ROR_I_ROR_16),
]
