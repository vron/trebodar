"""Rör ingjutna i mellanbjälklaget (betong 150 mm, z −150 … 0): från väggarna på plan 1 (rören går upp genom
bjälklagets överkant in i regelfacken) till ingjutningsdosor i källarens tak, där matningen från centralen kommer in.

Centralen sitter i teknikrummet i källaren, med vattencentralen; matningen därifrån till dosorna ritas i ärende #51,
och tills dess slutar rören i ingjutningsdosorna.
"""
from __future__ import annotations

from trebodar import skelett as S

from ..katalog import FXP20, INGJUTNINGSDOSA
from ...montering import i_bjalklag, i_vagg, kallartak
from ..punkter import Dosa, Ror
from ..rum.allrum import DIMMER_U

NAMN = "Mellanbjälklag"

_2C = S.INNERVAGGAR["2C"]
_2C_X, _2C_Y = _2C.origo[0] + DIMMER_U, _2C.origo[1] + _2C.tjocklek / 2      # under dimmern, mitt i väggen

PUNKTER = [
    Dosa("MB-D01", INGJUTNINGSDOSA, kallartak(6200.0, 5500.0)),
]

ROR = [
    Ror("MB-R01", FXP20, "AL-B1", "MB-D01",
        via=(i_vagg("2C", DIMMER_U, 0.0), i_bjalklag(_2C_X, _2C_Y), i_bjalklag(6200.0, _2C_Y - 300.0),
             i_bjalklag(6200.0, 5500.0))),
]
