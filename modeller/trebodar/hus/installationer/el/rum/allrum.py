"""Allrummet: spotar i snedtaket och dimmern vid sovrummets dörr.

Två rader med tre spotar (Junistar Exclusive, vridbar 40°, riktad lodrätt ned trots taklutningen 30°) parallellt
med nocken, omkring 1 200 mm på var sida om den, mitt emellan installationsskiktets läkt, och en dimmer med två
kanaler på väggen 2C (allrumssidan) bredvid sovrummets skjutdörr, utanför bladet i öppet läge. Ledningarna går i
rör: från dimmern upp i väggen och i innertakets installationsskikt längs raderna (läkten går längs y); till den
nordvästra raden går röret i väggen 2C över kaminens öppning. Matningen går ned i väggen och i mellanbjälklaget
(bjalklag/mellanbjalklag.py).
"""
from __future__ import annotations

from trebodar import skelett as S

from ..katalog import DIMMER_2, FXP16, JUNISTAR_EXCLUSIVE
from ..lakt import mellan_lakten
from ...montering import i_vagg, tak, vagg, vid_tak
from ..punkter import Apparat, Ror, Rum, Tandgrupp, lampor

RUM = Rum("AL", "Allrum", plan=1)
NAMN = RUM.namn

NOCK = S.BALKAR["NB3"].x                     # mittre huskroppens nock
RADER = {"2SO": NOCK - 1200.0, "2NV": NOCK + 1200.0}          # önskat läge, flyttas till mitt mellan läkten
Y = (7300.0, 8650.0, 10000.0)
DIMMER_U = 1350.0                            # längs 2C: förbi skjutdörrens blad (ID6) i öppet läge

TANDGRUPPER = [
    Tandgrupp("AL-T1", "Allrum, spotar sydost"),
    Tandgrupp("AL-T2", "Allrum, spotar nordväst"),
]

PUNKTER = [
    *lampor("AL-L", JUNISTAR_EXCLUSIVE, [tak(mellan_lakten("2SO", RADER["2SO"], y), y) for y in Y], "AL-T1"),
    *lampor("AL-L", JUNISTAR_EXCLUSIVE, [tak(mellan_lakten("2NV", RADER["2NV"], y), y) for y in Y], "AL-T2", start=4),
    Apparat("AL-B1", DIMMER_2, vagg("2C", DIMMER_U, 1050.0, sida=1), styr=("AL-T1", "AL-T2")),
]

_UPP = vid_tak("2C", DIMMER_U)
_OVER_KAMIN = 2250.0                         # över kaminens öppning i 2C (överkant 2 045)
_NV_U = mellan_lakten("2NV", RADER["2NV"], Y[0]) - S.INNERVAGGAR["2C"].origo[0]

ROR = [
    Ror("AL-R02", FXP16, "AL-B1", "AL-L01", via=_UPP),
    Ror("AL-R03", FXP16, "AL-L01", "AL-L02"),
    Ror("AL-R04", FXP16, "AL-L02", "AL-L03"),
    Ror("AL-R05", FXP16, "AL-B1", "AL-L04",
        via=(i_vagg("2C", DIMMER_U, _OVER_KAMIN), i_vagg("2C", _NV_U, _OVER_KAMIN), *vid_tak("2C", _NV_U))),
    Ror("AL-R06", FXP16, "AL-L04", "AL-L05"),
    Ror("AL-R07", FXP16, "AL-L05", "AL-L06"),
]
