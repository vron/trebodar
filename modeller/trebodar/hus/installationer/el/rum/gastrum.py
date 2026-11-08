"""Gästrummet i högra huskroppen: en glob i opalglas, dimmern vid dörren och ett uttag ovanför fönstret i 3NV
(belysningsplanen i ärende #8).

Globen hänger med underkanten 2,1 m över golvet, från det nedsänkta taket (#106). Dimmern sitter på L3 (rumssidan) intill fickdörren ID4, vid dess
låssida (L2 söder om dörren är dess ficka); röret går upp i väggen och i installationsskiktet till takkoppen.
"""
from __future__ import annotations

from ..katalog import DIMMER_1, FXP16, GLOB_250, UTTAG_1
from trebodar.hus.invandigt.nedsankta_tak import REGEL, regel_ok, z_tak

from ...montering import PLAN, Montering, i_vagg, vagg
from ..punkter import Apparat, Lampa, Ror, Rum, Tandgrupp, ovan_fonstret

RUM = Rum("GR", "Gästrum", plan=1)
NAMN = RUM.namn

U_B = 200.0                                   # dimmern längs L3 (x 11 250), intill dörren ID4 i L2

Z_REGLAR = regel_ok() - REGEL[1] / 2                    # röret mitt i det nedsänkta takets reglar (#106)


def nedsankt_tak(x: float, y: float) -> Montering:
    """I det nedsänkta taket (#106): gipsens undersida, normalen nedåt."""
    return Montering((x, y, PLAN[1] + z_tak()), (0.0, 0.0, -1.0), "tak", "NT")


TANDGRUPPER = [Tandgrupp("GR-T1", "Gästrum, glob")]

PUNKTER = [
    Lampa("GR-L01", GLOB_250, nedsankt_tak(12030.0, 5325.0), "GR-T1", underkant=2100.0),
    Apparat("GR-B1", DIMMER_1, vagg("L3", U_B, 1050.0, sida=1), styr=("GR-T1",)),
    Apparat("GR-U1", UTTAG_1, ovan_fonstret("3NV", 3998.0)),
]

ROR = [Ror("GR-R01", FXP16, "GR-B1", "GR-L01",
           via=(i_vagg("L3", U_B, Z_REGLAR), (*vagg("L3", U_B, 0.0, sida=1).punkt[:2], PLAN[1] + Z_REGLAR),
                (12030.0, 5325.0, PLAN[1] + Z_REGLAR)))]   # i det nedsänkta takets reglar (#106)
