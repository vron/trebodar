"""Badrummet (planritning 201 rev 02 och användarens markeringar): duschen i nordöstra hörnet med blandaren på 1C,
badkaret längs 1SO, WC:n på L9 och tvättstället vid gaveln 1NO under fönstret 1NO-F1. Rören kommer upp genom
bjälklaget från stråket S i mellanbjälklaget: i väggarnas regelfack till väggdosorna (duschen, WC:n) och genom golvet
i skåpet eller under badkaret (golvdosorna).

Duschens blandare sitter i regelfacket mellan stolpen LN5_1 och regeln 1C-R01 (x 2 245–2 488), väster om
ventilationens kanal FF3 i facket intill. WC:ns väggdosa i regelfacket mellan L9-R02 och L9-R03. Tvättställets rör
kommer från stråkets slut norr om V7:s vinkeljärn, var för sig (kallt öster om varmt).
"""
from __future__ import annotations

from trebodar import skelett as S
from trebodar.hus.invandigt.vaggar import vaggdef

from ...montering import golv, vagg
from ..katalog import (BADKAR, DUSCH, GOLVDOSA, ROR_I_ROR_15, ROR_I_ROR_16, ROR_I_ROR_18, TVATTSTALL, VAGGDOSA,
                       VAGGDOSA_BLANDARE, WC)
from ..punkter import Rum, Tappstalle
from ..teknikrum import Y_S

RUM = Rum("BA", "Badrum", plan=1)

X_DUSCH = 2366.0                            # blandarens mitt på 1C
Y_WC = 4682.0                               # WC:ns väggdosa på L9

TAPPSTALLEN = [
    Tappstalle("BA-DU1", DUSCH, VAGGDOSA_BLANDARE, vagg("1C", X_DUSCH - S.INNERVAGGAR["1C"].origo[0], 1000.0, sida=-1),
               ROR_I_ROR_16),
    Tappstalle("BA-BK1", BADKAR, GOLVDOSA, golv(600.0, 7000.0), ROR_I_ROR_18, kallt=(0.0, 1.0, 0.0)),
    Tappstalle("BA-WC1", WC, VAGGDOSA, vagg("L9", Y_WC - vaggdef("L9").origo[1], 180.0, sida=1), ROR_I_ROR_15),
    Tappstalle("BA-TS1", TVATTSTALL, GOLVDOSA, golv(1220.0, 4050.0), ROR_I_ROR_15, kallt=(1.0, 0.0, 0.0),
               via=(None, Y_S)),
]
