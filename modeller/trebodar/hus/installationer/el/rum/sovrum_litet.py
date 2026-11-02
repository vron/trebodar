"""Det lilla sovrummet i högra huskroppen: fyra spotar lutade mot gaveln och mot väggen L1, dimmern vid dörren och
ett uttag ovanför fönstret i 3NO (belysningsplanen i ärende #8).

Två rader med två Junistar Exclusive längs x (en på var sida om nocken), mitt emellan installationsskiktets läkt:
raden närmast gaveln 3NO lutad 20° mot gaveln och raden närmast L1 mot L1 (armaturen tål 40° från sin axel, som
snedtaket lutar 30° tvärs). En tändgrupp per rad och en dimmer med två kanaler på L1 (rumssidan) intill dörren ID5.
"""
from __future__ import annotations

from ..katalog import DIMMER_2, FXP16, JUNISTAR_EXCLUSIVE, UTTAG_1
from ..lakt import mellan_lakten
from ...montering import tak, vagg, vid_tak
from ..punkter import Apparat, Lampa, Ror, Rum, Tandgrupp, lutad, ovan_fonstret

RUM = Rum("SL", "Sovrum, litet", plan=1)
NAMN = RUM.namn

RADER = ((1500.0, -1.0, "SL-T1"), (2355.0, 1.0, "SL-T2"))   # y, riktningen mot väggen och tändgruppen
X = (("3SO", 11305.0), ("3NV", 12505.0))      # önskat x, flyttas till mitt mellan läkten
LUTNING = 20.0
U_B = 1610.0                                  # dimmern längs L1, intill dörren ID5 (u 610–1 460)

TANDGRUPPER = [
    Tandgrupp("SL-T1", "Sovrum litet, spotar mot gaveln"),
    Tandgrupp("SL-T2", "Sovrum litet, spotar mot L1"),
]

PUNKTER = [
    *[Lampa(f"SL-L{2 * i + j + 1:02d}", JUNISTAR_EXCLUSIVE, tak(mellan_lakten(kod, x, y), y), tand,
            riktning=lutad((0.0, s), LUTNING))
      for i, (y, s, tand) in enumerate(RADER) for j, (kod, x) in enumerate(X)],
    Apparat("SL-B1", DIMMER_2, vagg("L1", U_B, 1050.0, sida=-1), styr=("SL-T1", "SL-T2")),
    Apparat("SL-U1", UTTAG_1, ovan_fonstret("3NO", 1065.0)),
]

ROR = [
    Ror("SL-R01", FXP16, "SL-B1", "SL-L03", via=vid_tak("L1", U_B, sida=-1)),
    Ror("SL-R02", FXP16, "SL-L03", "SL-L04"),
    Ror("SL-R03", FXP16, "SL-B1", "SL-L01", via=vid_tak("L1", U_B, sida=-1)),
    Ror("SL-R04", FXP16, "SL-L01", "SL-L02"),
]
