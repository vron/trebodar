"""Kontoret i mittre huskroppen: fyra spotar lutade mot långsidorna och dimmern på 2A (belysningsplanen i ärende #8).

Två rader med två Junistar Exclusive nära långsidorna, mitt emellan installationsskiktets läkt, lutade 9° från
lodlinjen mot närmaste långsida (snedtaket vrider redan armaturen 30° åt andra hållet, och den tål 40°). Dimmern
sitter på 2A (kontorssidan); röret går upp i väggen och genom raderna i installationsskiktet.
"""
from __future__ import annotations

from ..katalog import DIMMER_1, FXP16, JUNISTAR_EXCLUSIVE
from ..lakt import mellan_lakten
from ...montering import tak, vagg, vid_tak
from ..punkter import Apparat, Lampa, Ror, Rum, Tandgrupp, lutad

RUM = Rum("KT", "Kontor", plan=1)
NAMN = RUM.namn

RADER = {"2SO": (5275.0, -1.0), "2NV": (8345.0, 1.0)}     # önskat x och riktningen mot väggen
Y = (850.0, 1650.0)
LUTNING = 9.0
U_B = 150.0                                   # dimmern längs 2A

TANDGRUPPER = [Tandgrupp("KT-T1", "Kontor, spotar mot väggarna")]

PUNKTER = [
    *[Lampa(f"KT-L{2 * i + j + 1:02d}", JUNISTAR_EXCLUSIVE, tak(mellan_lakten(kod, x, y), y), "KT-T1",
            riktning=lutad((s, 0.0), LUTNING))
      for i, (kod, (x, s)) in enumerate(RADER.items()) for j, y in enumerate(Y)],
    Apparat("KT-B1", DIMMER_1, vagg("2A", U_B, 1050.0, sida=-1), styr=("KT-T1",)),
]

ROR = [
    Ror("KT-R01", FXP16, "KT-B1", "KT-L04", via=vid_tak("2A", U_B, sida=-1)),
    Ror("KT-R02", FXP16, "KT-L04", "KT-L03"),
    Ror("KT-R03", FXP16, "KT-L03", "KT-L01"),
    Ror("KT-R04", FXP16, "KT-L01", "KT-L02"),
]
