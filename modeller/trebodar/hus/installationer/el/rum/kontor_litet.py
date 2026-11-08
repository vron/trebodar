"""Det lilla kontoret i högra huskroppen: en glob i opalglas, dimmern vid dörren och ett uttag ovanför fönstret i
3NV (belysningsplanen i ärende #8).

Globen hänger med underkanten 2,1 m över golvet, från det nedsänkta taket (#106). Dimmern sitter på L1 (rumssidan) öster om stolpen LN1_1, eftersom
L2 vid dörren är fickdörren ID3:s ficka och L1 där fickdörren ID5:s; röret går upp i väggen och i installationsskiktet
till takkoppen.
"""
from __future__ import annotations

from ..katalog import DIMMER_1, FXP16, GLOB_250, UTTAG_1
from trebodar.hus.invandigt.nedsankta_tak import REGEL, regel_ok, z_tak

from ...montering import PLAN, Montering, i_vagg, vagg
from ..punkter import Apparat, Lampa, Ror, Rum, Tandgrupp, ovan_fonstret

RUM = Rum("KL", "Kontor, litet", plan=1)
NAMN = RUM.namn

U_B = 2560.0                                  # dimmern längs L1 (x 12 000), i facket öster om stolpen LN1_1

Z_REGLAR = regel_ok() - REGEL[1] / 2                    # röret mitt i det nedsänkta takets reglar (#106)


def nedsankt_tak(x: float, y: float) -> Montering:
    """I det nedsänkta taket (#106): gipsens undersida, normalen nedåt."""
    return Montering((x, y, PLAN[1] + z_tak()), (0.0, 0.0, -1.0), "tak", "NT")


TANDGRUPPER = [Tandgrupp("KL-T1", "Kontor litet, glob")]

PUNKTER = [
    Lampa("KL-L01", GLOB_250, nedsankt_tak(12085.0, 3425.0), "KL-T1", underkant=2100.0),
    Apparat("KL-B1", DIMMER_1, vagg("L1", U_B, 1050.0, sida=1), styr=("KL-T1",)),
    Apparat("KL-U1", UTTAG_1, ovan_fonstret("3NV", 2300.0)),
]

ROR = [Ror("KL-R01", FXP16, "KL-B1", "KL-L01",
           via=(i_vagg("L1", U_B, Z_REGLAR), (*vagg("L1", U_B, 0.0, sida=1).punkt[:2], PLAN[1] + Z_REGLAR),
                (12085.0, 3425.0, PLAN[1] + Z_REGLAR)))]   # i det nedsänkta takets reglar (#106)
