"""Sovrummet i mittre huskroppen: en glob i opalglas, dimmern vid dörren från allrummet och ett uttag ovanför
fönstret i 1NO (belysningsplanen i ärende #8).

Globen hänger med underkanten 2,1 m över golvet. Dimmern sitter på 2C (sovrumssidan) intill skjutdörren ID6; röret
går upp i väggen och i installationsskiktet till takkoppen.
"""
from __future__ import annotations

from ..katalog import DIMMER_1, FXP16, GLOB_250, UTTAG_1
from ...montering import tak, vagg, vid_tak
from ..punkter import Apparat, Lampa, Ror, Rum, Tandgrupp, ovan_fonstret

RUM = Rum("SV", "Sovrum", plan=1)
NAMN = RUM.namn

U_B = 138.0                                   # dimmern längs 2C, intill dörröppningen (L12 slutar vid x 4 405)

TANDGRUPPER = [Tandgrupp("SV-T1", "Sovrum, glob")]

PUNKTER = [
    Lampa("SV-L01", GLOB_250, tak(7055.0, 3425.0), "SV-T1", underkant=2100.0),
    Apparat("SV-B1", DIMMER_1, vagg("2C", U_B, 1050.0, sida=-1), styr=("SV-T1",)),
    Apparat("SV-U1", UTTAG_1, ovan_fonstret("1NO", 3070.0)),
]

ROR = [Ror("SV-R01", FXP16, "SV-B1", "SV-L01", via=vid_tak("2C", U_B, sida=-1))]
