"""Det framtida badrummet i källaren (användarens skiss), i rummet mellan KL2 och KL3 söder om V7, ut till bågväggen
KL12: duschen i hörnet mot KL2 och V7, WC:n mot KL2 vid KL1 och handfatet mot bågen. Förberett nu: stosarna för
kallt och varmt upp genom bottenplattan strax innanför väggarna (golvstosar, proppade), från de nedre fördelarna i
fördelarskåpet under plattan i cellplasten (teknikrum.ORDNING_NED, gruppen N2), och avloppen genom plattan
(../../avlopp: duschens golvbrunn GB4, WC:ns och handfatets stosar).

Rören kommer norrut under plattan öster om rummet och viker västerut (WC:n och duschen) eller österut (handfatet)
till sina stosar; kallt och varmt står så att det rör som viker av först ligger ytterst (teknikrum.ror_under_plattan).
"""
from __future__ import annotations

import math

from trebodar.hus.invandigt.kallarens_innervaggar import BAGE, GIPS_T, VAGGAR as KL

from ..katalog import DUSCH, GOLVSTOS, ROR_I_ROR_15, ROR_I_ROR_16, TVATTSTALL, WC
from ..punkter import Rum, Tappstalle
from .stos import stos

RUM = Rum("KB", "Framtida badrum i källaren", plan=0)

_KL2 = KL["KL2"].c + KL["KL2"].h + GIPS_T                   # KL2:s yta mot badrummet
FRAN_VAGGEN = 80.0                                        # stosarnas mitt från väggens gips
Y_DUSCH, Y_WC = 4300.0, 4950.0                            # duschens blandare (i duschen) och WC:ns stos (vid cisternen)
V_HANDFAT = 225.0                                         # handfatet mitt på bågen (grader kring dess centrum)
R_HANDFAT = BAGE.r + KL["KL3"].h + GIPS_T + 70.0          # handfatets stosar från bågens centrum (badrummets sida)
_a = math.radians(V_HANDFAT)
TANGENT = (-math.sin(_a), math.cos(_a), 0.0)             # längs bågen, mot nordost: kallt där, varmt mot sydväst
HANDFAT = (BAGE.centrum[0] + R_HANDFAT * math.cos(_a), BAGE.centrum[1] + R_HANDFAT * math.sin(_a))

TAPPSTALLEN = [
    # kallt söderut: det viker av först västerut och ligger västerut i stråket
    Tappstalle("KB-DU1", DUSCH, GOLVSTOS, stos(_KL2 + FRAN_VAGGEN, Y_DUSCH, GOLVSTOS, (0.0, 1.0, 0.0)), ROR_I_ROR_16,
               kallt=(0.0, 1.0, 0.0)),
    Tappstalle("KB-WC1", WC, GOLVSTOS, stos(_KL2 + FRAN_VAGGEN, Y_WC, GOLVSTOS), ROR_I_ROR_16),
    # klenare rör: varmvattnet når handfatet inom tiden (system.VV_TID)
    Tappstalle("KB-TS1", TVATTSTALL, GOLVSTOS, stos(*HANDFAT, GOLVSTOS, TANGENT, TANGENT[:2]), ROR_I_ROR_15,
               kallt=TANGENT),
]
