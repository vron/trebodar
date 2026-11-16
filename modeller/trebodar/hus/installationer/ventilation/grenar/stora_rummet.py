"""Det stora källarrummet (under högra huskroppen, mellan V1, V14, V9 och V15/V16): frånluft lodrätt upp till taket
(#134), och källarrummet väster om det (mellan V19/V20, V2, V15 och V4–V6), som får sin luft ut i det stora rummet
genom en överluftsöppning Ø100 i väggen V15.

Kanalen går lodrätt från donet och kanalfläkten under källarens tak, genom mellanbjälklaget och upp i kökets
inbyggnad, i spalten mellan kylen och väggen L4 (174 mm, där vitvarornas luft går upp till förrådet), så att den inte
tar plats ur skafferiet, genom förrådet och innertaket och isolerad genom taket till en takhuv på takfallet 3SO.
Kanalfläkten sitter i det stora rummet (åtkomlig för service).
"""
from __future__ import annotations

from trebodar.hus.invandigt.kokets_inbyggnad import fritt
from trebodar.hus.invandigt.vaggar import skiktets_tjocklek, vaggdef

from ...montering import KALLARTAK, angbromsen, kallarvagg, pa_tak
from ..delar import Avluft, Don, Flakt, Gren, Kanal, fri
from ..katalog import (FRANLUFTSDON_100, ISOLERAD_100, KANALFLAKT_100, OVERLUFTSDON_100, OVERLUFTSGALLER_100, SPIRO_100,
                       TAKHUV_100)

FRITT_L4 = 15.0                             # kanalens avstånd från väggen L4 (spalten bakom kylen)
FRAN_KYLENS_SIDA = 90.0                     # kanalens mitt från kylnischens västra sida: så långt från pelaren P5 som går
_L4 = vaggdef("L4")
# bakom kylen: i spalten mellan kylens baksida och L4:s yta mot köket
X = fritt("Kyl")[0] + FRAN_KYLENS_SIDA
Y = _L4.origo[1] + _L4.tjocklek + skiktets_tjocklek("L4", 1, X - _L4.origo[0]) + FRITT_L4 + SPIRO_100.b / 2
Z_FLAKT = KALLARTAK - 110.0 - KANALFLAKT_100.langd / 2      # fläkten under takarmaturen KA-P04:s kant intill
Z_DON = Z_FLAKT - KANALFLAKT_100.langd / 2 - 150.0          # donets front
Y_OVERLUFT, Z_OVERLUFT = 10100.0, 1900.0    # överluften genom V15: läget längs väggen och höjden över källarens golv

GREN = Gren("FF3", "Stora källarrummet", "Stora källarrummet", 10.0, (
    Don("FF3-D1", FRANLUFTSDON_100, fri((X, Y, Z_DON), (0.0, 0.0, -1.0))),
    Kanal("FF3-K1", SPIRO_100),
    Flakt("FF3-FL1", KANALFLAKT_100, (X, Y, Z_FLAKT), (0.0, 0.0, 1.0)),
    Kanal("FF3-K2", SPIRO_100, via=((X, Y, angbromsen(X, Y)),)),      # genom bjälklaget och upp bakom kylen
    Kanal("FF3-K3", ISOLERAD_100),                                    # genom takets isolering
    Avluft("FF3-A1", TAKHUV_100, pa_tak(X, Y)),
), flode_normal=5.0, beskrivning=(
    "Kanalen Ø100 går lodrätt från donet och kanalfläkten under källarens tak, genom en hylsa i mellanbjälklaget och "
    "upp i kökets inbyggnad, i spalten bakom kylen mot väggen L4, och genom förrådet ovanför.",
    "Över innertaket går kanalen isolerad mellan takbalkarna till takhuven på takfallet 3SO; ångbromsen tätas runt "
    "kanalen med manschett.",
    "Källarrummet väster om V15 får sin luft ut i det stora rummet genom överluftsöppningen ÖL1.",
))

OVERLUFT = Gren("OL1", "Överluft genom V15", "Källarrummet", 5.0, (
    Don("OL1-D1", OVERLUFTSDON_100, kallarvagg("V15", Y_OVERLUFT, Z_OVERLUFT, -1)),
    Kanal("OL1-K1", SPIRO_100),
    Avluft("OL1-A1", OVERLUFTSGALLER_100, kallarvagg("V15", Y_OVERLUFT, Z_OVERLUFT, 1)),
), flode_normal=5.0, overluft=True, beskrivning=(
    "Överluftsöppning Ø100 genom källarväggen V15 (kärnborrning mellan järnen), med galler på båda sidor: luften från "
    "källarrummet går ut i det stora rummet och vidare till FF3.",
))
