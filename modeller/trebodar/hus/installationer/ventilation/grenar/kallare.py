"""Källarrummet (mellan källarväggarna V19/V20, V2, V15 och V4–V6, under allrummet): frånluft med kanalfläkt, upp
genom en vägg på plan 1 och ut genom taket, utan att kanalen syns på plan 1.

Rummet har inga väggar ovanför på plan 1 (allrummet), och dess ytterväggar V2 och V20 står mot marken. Kanalen går
därför under källarens tak från frånluftsdonet i rummets nordvästra hörn, genom innerväggen V19 (kärnborrning) till
källarens vänstra del, och upp i den bärande innerväggen 1C mellan badrummet och hallen, rakt ovanför (y 8 220):

- i 1C i regelfacket mellan reglarna 1C-R01 och 1C-R02 (x 2 532–3 088), som platt kanal 204 × 60 i stommen 45 × 70
  (samma tvärsnitt som Ø125), genom en ursparing i mellanbjälklaget och genom syll och hammarband;
- ovanför innertakets ångbroms i facket mellan takbalkarna i y 7 850–8 405 (takfallet 1NV), som isolerad kanal Ø125
  rakt upp till en takhuv 650 mm (i plan) nedanför nocken, 1,6 m från dalen mot mittre huskroppen.

Kanalfläkten sitter i källaren (åtkomlig för service); kanalen efter fläkten har övertryck och ska vara tät.
"""
from __future__ import annotations

from trebodar import skelett as S

from ...montering import KALLARTAK, angbromsen, pa_tak, under_kallartak
from ..delar import Avluft, Don, Flakt, Gren, Kanal, Overgang, fri
from ..katalog import (FRANLUFTSDON_125, ISOLERAD_125, KANALFLAKT_125, PLATT_125, PLATT_RUND_125, RUND_PLATT_125,
                       SPIRO_125, TAKHUV_125)

Y = S.INNERVAGGAR["1C"].origo[1] + S.INNERVAGGAR["1C"].tjocklek / 2       # väggen 1C:s mitt
X_STIG = 2810.0                             # mitt i regelfacket 1C-R01–1C-R02
X_DON, Y_DON = 4950.0, 10400.0              # rummets nordvästra hörn
X_FLAKT = 3950.0                            # i källarens vänstra del, 400 mm väster om V19
Z = KALLARTAK - 155.0                       # kanalens mitt under taket (fläkten 30 mm under betongen)

_O1 = (X_STIG, Y, KALLARTAK - 15.0 - RUND_PLATT_125.langd / 2)          # utloppet 15 mm under betongen
_O2 = (X_STIG, Y, angbromsen(X_STIG, Y) + PLATT_RUND_125.langd / 2)          # från ångbromsen och uppåt

GREN = Gren("FF3", "Källarrummet", "Källarrummet", 10.0, (
    Don("FF3-D1", FRANLUFTSDON_125, fri((X_DON, Y_DON, Z - 200.0), (0.0, 0.0, -1.0))),
    Kanal("FF3-K1", SPIRO_125, via=(under_kallartak(X_DON, Y_DON, 155.0), under_kallartak(X_DON, Y, 155.0))),
    Flakt("FF3-FL1", KANALFLAKT_125, (X_FLAKT, Y, Z), (-1.0, 0.0, 0.0)),
    Kanal("FF3-K2", SPIRO_125, via=(under_kallartak(X_STIG, Y, 155.0),)),
    Overgang("FF3-O1", RUND_PLATT_125, _O1, (0.0, 0.0, 1.0)),
    Kanal("FF3-K3", PLATT_125),                                   # genom bjälklaget och upp i 1C
    Overgang("FF3-O2", PLATT_RUND_125, _O2, (0.0, 0.0, 1.0)),
    Kanal("FF3-K4", ISOLERAD_125),                                # genom takets isolering
    Avluft("FF3-A1", TAKHUV_125, pa_tak(X_STIG, Y)),
), flode_normal=10.0)
