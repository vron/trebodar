"""Det lilla kontoret i högra huskroppen: en glob i opalglas, dimmern vid dörren och ett uttag ovanför fönstret i
3NV (belysningsplanen i ärende #8).

Globen hänger med underkanten 2,1 m över golvet. Dimmern sitter på L2 (rumssidan) intill fickdörren ID3; röret går
upp i väggen och i installationsskiktet till takkoppen.
"""
from __future__ import annotations

from ..katalog import DIMMER_1, FXP16, GLOB_250, UTTAG_1
from ...montering import tak, vagg, vid_tak
from ..punkter import Apparat, Lampa, Ror, Rum, Tandgrupp, ovan_fonstret

RUM = Rum("KL", "Kontor, litet", plan=1)
NAMN = RUM.namn

U_B = 991.0                                   # dimmern längs L2, intill dörren ID3 (u 25–841)

TANDGRUPPER = [Tandgrupp("KL-T1", "Kontor litet, glob")]

PUNKTER = [
    Lampa("KL-L01", GLOB_250, tak(12085.0, 3425.0), "KL-T1", underkant=2100.0),
    Apparat("KL-B1", DIMMER_1, vagg("L2", U_B, 1050.0, sida=-1), styr=("KL-T1",)),
    Apparat("KL-U1", UTTAG_1, ovan_fonstret("3NV", 2300.0)),
]

ROR = [Ror("KL-R01", FXP16, "KL-B1", "KL-L01", via=vid_tak("L2", U_B, sida=-1))]
