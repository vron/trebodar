"""Köket: köksfläkten på den nordvästra långsidan 3NV, mitt emellan fönstren 3NV-F4 och 3NV-F5 (1 × 1 m) över
hällen, med utblås rakt genom väggen bakom skorstenskåpan.

Kåpans underkant 650 mm över hällen (bänken 900 mm över golvet). Utloppet går upp i skorstenskåpan och genom
ytterväggen 2 250 mm över golvet, mellan fönstrens överkant (2 100) och hammarbandet, i regelfacket mitt emellan
fönstren; gallret på fasaden har backspjäll.
"""
from __future__ import annotations

from trebodar.hus.fonster_och_dorrar.oppningar import OPPNINGAR

from ...montering import utsida, vagg
from ..delar import Avluft, Don, Gren, Kanal
from ..katalog import GALLER_150, KOKSFLAKT_60, SPIRO_150, VAGGHYLSA_150

_F4, _F5 = (next(o for o in OPPNINGAR["3NV"] if o.kod == k) for k in ("3NV-F4", "3NV-F5"))
U = (_F4.u1 + _F5.u0) / 2                   # mitt emellan fönstren, längs väggen
Z_KAPA = 900.0 + 650.0                      # kåpans underkant: bänken + 650
Z_GENOM = 2250.0                            # utblåset genom väggen

_KAPA = vagg("3NV", U, Z_KAPA)
_INNE = vagg("3NV", U, Z_GENOM).punkt
_UPP = (_INNE[0] + _KAPA.normal[0] * KOKSFLAKT_60.utlopp, _INNE[1] + _KAPA.normal[1] * KOKSFLAKT_60.utlopp, Z_GENOM)

GREN = Gren("FF1", "Köksfläkten", "Kök", KOKSFLAKT_60.flode, (
    Don("FF1-D1", KOKSFLAKT_60, _KAPA),
    Kanal("FF1-K1", SPIRO_150, via=(_UPP, _INNE)),              # upp i skorstenskåpan och in mot väggen
    Kanal("FF1-K2", VAGGHYLSA_150),                              # genom ytterväggen
    Avluft("FF1-A1", GALLER_150, utsida("3NV", U, Z_GENOM)),
), flode_normal=KOKSFLAKT_60.flode_normal)
