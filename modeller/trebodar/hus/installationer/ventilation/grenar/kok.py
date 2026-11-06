"""Köket: köksfläkten på den nordvästra långsidan 3NV, mitt emellan fönstren 3NV-F4 och 3NV-F5 (1 × 1 m) över
hällen, utan egen fläkt, och takfläkten på taket rakt ovanför (ärende #59).

Kåpan (Fjäråskupan Carisma 70, vit) har underkanten 650 mm över hällen (bänken 900 mm över golvet), och skorstenen
går upp till innertaket. Utloppet Ø150 går upp i skorstenen, så långt mot takbalksfackets mitt som skorstenen rymmer,
genom innertaket och ångbromsen. Ovanför ångbromsen går en övergång till den större kanalen, isolerad Ø200, lodrätt
genom takets isolering, luftspalten och råsponten till takfläkten (Systemair TFSR 200 EC Sileo, tyst) på en sockel i
takplåten. Ströläkten kapas runt kanalen, med omluftning som runt takfönstren (U-03).
"""
from __future__ import annotations

from trebodar import skelett as S
from trebodar.hus.fonster_och_dorrar.oppningar import OPPNINGAR
from trebodar.hus.stomme.prefab.takbalkar.takbalkar import FALT

from ...montering import angbromsen, pa_tak, vagg
from ..delar import Avluft, Don, Gren, Kanal, Overgang
from ..katalog import ISOLERAD_200, KOKSFLAKT_CARISMA, RUND_150_200, SPIRO_150, TAKFLAKT_200

_F4, _F5 = (next(o for o in OPPNINGAR["3NV"] if o.kod == k) for k in ("3NV-F4", "3NV-F5"))
U = (_F4.u1 + _F5.u0) / 2                   # mitt emellan fönstren, längs väggen
Z_KAPA = 900.0 + 650.0                      # kåpans underkant: bänken + 650

_KAPA = vagg("3NV", U, Z_KAPA)
_N = _KAPA.normal
X = _KAPA.punkt[0] + _N[0] * KOKSFLAKT_CARISMA.utlopp            # utloppets mitt, ut från väggen (väggen går längs y)
Y = _KAPA.punkt[1] + _N[1] * KOKSFLAKT_CARISMA.utlopp

_BALKAR = FALT["3NV"].y                     # takbalkarnas lägen (lägsta y) i takfallet ovanför
FACK = (max(y for y in _BALKAR if y < Y) + S.TAKBALK_B, min(y for y in _BALKAR if y > Y))       # facket ovanför kåpan
_RYMS = KOKSFLAKT_CARISMA.skorsten[0] / 2 - KOKSFLAKT_CARISMA.anslutning / 2 - 5.0           # kanalen i skorstenen
YK = Y + max(-_RYMS, min(_RYMS, (FACK[0] + FACK[1]) / 2 - Y))                               # kanalen mot fackets mitt

_UT = (X, Y, Z_KAPA + KOKSFLAKT_CARISMA.h)                      # utloppet i kåpans överkant
_O1 = (X, YK, angbromsen(X, YK) + RUND_150_200.langd / 2)       # övergången från ångbromsen och uppåt


def _mm(x: float) -> str:
    return f"{x:,.0f}".replace(",", " ")


GREN = Gren("FF1", "Köksfläkten", "Kök", KOKSFLAKT_CARISMA.flode, (
    Don("FF1-D1", KOKSFLAKT_CARISMA, _KAPA),
    Kanal("FF1-K1", SPIRO_150, via=((X, YK, _UT[2] + 150.0),)),   # upp i skorstenen, mot fackets mitt
    Overgang("FF1-O1", RUND_150_200, _O1, (0.0, 0.0, 1.0)),
    Kanal("FF1-K2", ISOLERAD_200),                                 # genom takets isolering, luftspalten och råsponten
    Avluft("FF1-A1", TAKFLAKT_200, pa_tak(X, YK)),
), flode_normal=KOKSFLAKT_CARISMA.flode_normal, beskrivning=(
    "Kåpan Fjäråskupan Carisma 70, vit, utan egen fläkt, 650 mm över hällen; skorstenen går upp till innertaket.",
    f"Kanalen Ø150 går upp i skorstenen, {_mm(abs(YK - Y))} mm mot takbalksfackets mitt (y {_mm(FACK[0])}–"
    f"{_mm(FACK[1])}), genom innertaket och ångbromsen, som tätas med manschett; ovanför den en övergång till "
    "isolerad Ø200 lodrätt genom takets isolering, luftspalten och råsponten.",
    "Takfläkten Systemair TFSR 200 EC Sileo med backspjäll står på en sockel Ø300 i takplåten; ströläkten kapas runt "
    "kanalen med omluftning som runt takfönstren (U-03).",
))
