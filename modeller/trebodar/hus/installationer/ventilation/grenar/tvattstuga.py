"""Tvättstugan i källaren (under hallen och badrummet på plan 1): frånluft lodrätt upp till taket (#136).

Kanalen går lodrätt från donet och kanalfläkten under källarens tak, genom mellanbjälklaget och upp längst in i
hörnet i hallens garderob, mot väggarna 1A och 1B, genom garderobens tak och innertaket och isolerad genom taket till
en takhuv på takfallet 1SO. Kanalen står FRITT_1B från 1B:s yta, så att den isolerade kanalen genom taket går fri
från nockbalken NB5:s upplagsregel, och FRITT_1A från 1A:s yta, fri från takbalken som ligger på 1A.
"""
from __future__ import annotations

from trebodar.hus.invandigt.vaggar import skiktets_tjocklek, vaggdef

from ...montering import KALLARTAK, angbromsen, pa_tak
from ..delar import Avluft, Don, Flakt, Gren, Kanal, fri
from ..katalog import FRANLUFTSDON_100, ISOLERAD_100, KANALFLAKT_100, SPIRO_100, TAKHUV_100

FRITT_1B, FRITT_1A = 80.0, 40.0             # kanalens avstånd från garderobens väggar (ytorna)
_1A, _1B = vaggdef("1A"), vaggdef("1B")
# garderobens inre hörn: 1B:s yta mot hallen (väster) och 1A:s yta mot hallen (norr)
X = _1B.origo[0] - _1B.tjocklek - skiktets_tjocklek("1B", 1, 200.0) - FRITT_1B - SPIRO_100.b / 2
Y = _1A.origo[1] + _1A.tjocklek + skiktets_tjocklek("1A", 1, X - _1A.origo[0]) + FRITT_1A + SPIRO_100.b / 2
Z_FLAKT = KALLARTAK - 40.0 - KANALFLAKT_100.langd / 2       # fläkten 40 mm under betongen
Z_DON = Z_FLAKT - KANALFLAKT_100.langd / 2 - 150.0          # donets front

GREN = Gren("FF4", "Tvättstugan", "Tvättstugan", 15.0, (
    Don("FF4-D1", FRANLUFTSDON_100, fri((X, Y, Z_DON), (0.0, 0.0, -1.0))),
    Kanal("FF4-K1", SPIRO_100),
    Flakt("FF4-FL1", KANALFLAKT_100, (X, Y, Z_FLAKT), (0.0, 0.0, 1.0)),
    Kanal("FF4-K2", SPIRO_100, via=((X, Y, angbromsen(X, Y)),)),      # genom bjälklaget och upp i garderobens hörn
    Kanal("FF4-K3", ISOLERAD_100),                                    # genom takets isolering
    Avluft("FF4-A1", TAKHUV_100, pa_tak(X, Y)),
), flode_normal=5.0, beskrivning=(
    "Kanalen Ø100 går lodrätt från donet och kanalfläkten under källarens tak, genom en hylsa i mellanbjälklaget och "
    "upp längst in i hörnet i hallens garderob, mot väggarna 1A och 1B, och genom garderobens tak.",
    "Över innertaket går kanalen isolerad mellan takbalkarna till takhuven på takfallet 1SO; ångbromsen tätas runt "
    "kanalen med manschett.",
    "Fläkten är fuktstyrd: grundflöde 5 l/s och 15 l/s när tvätten torkar.",
))
