"""Gästrummet i högra huskroppen: en glob i opalglas, dimmern vid dörren och ett uttag ovanför fönstret i 3NV
(belysningsplanen i ärende #8).

Globen hänger med underkanten 2,1 m över golvet. Dimmern sitter på L2 (rumssidan) intill fickdörren ID4; röret går
upp i väggen och i installationsskiktet till takkoppen.
"""
from __future__ import annotations

from ..katalog import DIMMER_1, FXP16, GLOB_250, UTTAG_1
from ...montering import tak, vagg, vid_tak
from ..punkter import Apparat, Lampa, Ror, Rum, Tandgrupp, ovan_fonstret

RUM = Rum("GR", "Gästrum", plan=1)
NAMN = RUM.namn

U_B = 2882.0                                  # dimmern längs L2, intill dörren ID4 (u 1 891–2 732)

TANDGRUPPER = [Tandgrupp("GR-T1", "Gästrum, glob")]

PUNKTER = [
    Lampa("GR-L01", GLOB_250, tak(12030.0, 5325.0), "GR-T1", underkant=2100.0),
    Apparat("GR-B1", DIMMER_1, vagg("L2", U_B, 1050.0, sida=-1), styr=("GR-T1",)),
    Apparat("GR-U1", UTTAG_1, ovan_fonstret("3NV", 3998.0)),
]

ROR = [Ror("GR-R01", FXP16, "GR-B1", "GR-L01", via=vid_tak("L2", U_B, sida=-1))]
