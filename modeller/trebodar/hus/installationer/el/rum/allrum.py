"""Allrummet: tubspotar som lyser upp mot snedtaket, två PH 5 över bordet, dimrarna vid sovrummets dörr och uttagen
ovanför skjutdörren mot sydväst (belysningsplanen i ärende #8).

Två rader med fyra Tube Mini R en bit upp på takfallen på var sida om nocken (två läktfack högre än vid takfoten), mitt
emellan installationsskiktets läkt, vinklade tvärs över rummet mot mitten av det motsatta takfallet, så att de lyser upp
taket. En femte på den sydöstra sidans tändgrupp sitter i allrummets västra del under vänstra huskroppens takfall och
lyser mot badrumsväggen L11:s övre del (tuben vrids högst 90° från stammen, så den kan inte riktas över dalen). Två PH 5
hänger över bordet, symmetriskt kring nocken, 600 mm över bordsskivan (0,72 m).

Dimrarna sitter på väggen 2C (allrumssidan) bredvid sovrummets fickdörr, öster om fickan: en med två
kanaler för spotarna och en för PH 5. Ledningarna går i rör: från dimrarna upp i väggen och i innertakets
installationsskikt längs raderna; till den nordvästra raden går röret i väggen 2C över kaminens öppning. Matningen
går ned i väggen och i mellanbjälklaget (bjalklag/mellanbjalklag.py).
"""
from __future__ import annotations

from trebodar import skelett as S

from ..katalog import DIMMER_1, DIMMER_2, FXP16, PH5, TUBE_MINI_R, UTTAG_1
from ..lakt import mellan_lakten
from ...montering import i_vagg, tak, vagg, vid_tak
from ..punkter import Apparat, Lampa, Ror, Rum, Tandgrupp, mot, ovan_fonstret

RUM = Rum("AL", "Allrum", plan=1)
NAMN = RUM.namn

NOCK = S.BALKAR["NB3"].x                     # mittre huskroppens nock
Y = (6745.0, 7945.0, 9145.0, 10345.0)
AVSTAND = 1380.0                             # spotarnas rader lika långt från nocken på båda sidor (#95)
RADER = {"2SO": NOCK - AVSTAND, "2NV": NOCK + AVSTAND}   # önskat läge, flyttas till mitt mellan läkten
# riktningen: mot mitten av det motsatta takfallet (mellan nocken och takfotsväggens insida)
MAL = {"2SO": (NOCK + S.TAKFALL["2NV"].x_insida) / 2, "2NV": (NOCK + S.TAKFALL["2SO"].x_insida) / 2}
VAST = (3965.0, 7705.0)                      # tubspoten i allrummets västra del (takfallet 1NV)
L11_X = 3400.0                               # badrumsväggen L11:s yta mot allrummet (ungefär)
PH5_X, PH5_Y, BORD = 460.0, 8975.0, 720.0   # PH 5: från nocken, längs y och bordsskivans höjd
DIMMER_U = 1350.0                            # längs 2C: öster om fickdörren ID6:s ficka (u 0–1 153)


def _rad(kod: str, start: int, tand: str) -> list[Lampa]:
    """En rad tubspotar i takfallet kod, riktade mot det motsatta takfallet."""
    ut = []
    for i, y in enumerate(Y):
        m = tak(mellan_lakten(kod, RADER[kod], y), y)
        ut.append(Lampa(f"AL-L{start + i:02d}", TUBE_MINI_R, m, tand, riktning=mot(m, tak(MAL[kod], y).punkt)))
    return ut


_V = tak(mellan_lakten("1NV", VAST[0], VAST[1]), VAST[1])

TANDGRUPPER = [
    Tandgrupp("AL-T1", "Allrum, tubspotar sydost"),
    Tandgrupp("AL-T2", "Allrum, tubspotar nordväst"),
    Tandgrupp("AL-T3", "Allrum, PH 5 över bordet"),
]

PUNKTER = [
    *_rad("2SO", 1, "AL-T1"),
    Lampa("AL-L05", TUBE_MINI_R, _V, "AL-T1",
          riktning=mot(_V, (L11_X, VAST[1], tak(L11_X, VAST[1]).punkt[2] - 350.0))),
    *_rad("2NV", 6, "AL-T2"),
    Lampa("AL-L10", PH5, tak(NOCK - PH5_X, PH5_Y), "AL-T3", underkant=BORD + 600.0),
    Lampa("AL-L11", PH5, tak(NOCK + PH5_X, PH5_Y), "AL-T3", underkant=BORD + 600.0),
    Apparat("AL-B1", DIMMER_2, vagg("2C", DIMMER_U, 1050.0, sida=1), styr=("AL-T1", "AL-T2")),
    Apparat("AL-B2", DIMMER_1, vagg("2C", DIMMER_U + 80.0, 1050.0, sida=1), styr=("AL-T3",)),
    Apparat("AL-U1", UTTAG_1, ovan_fonstret("2SV", 3825.0)),
    Apparat("AL-U2", UTTAG_1, ovan_fonstret("2SV", 1435.0)),
]

_OVER_KAMIN = 2250.0                         # över kaminens öppning i 2C (överkant 2 045)
_NV_U = mellan_lakten("2NV", RADER["2NV"], Y[0]) - S.INNERVAGGAR["2C"].origo[0]

ROR = [
    Ror("AL-R01", FXP16, "AL-B1", "AL-L01", via=vid_tak("2C", DIMMER_U)),
    Ror("AL-R02", FXP16, "AL-L01", "AL-L02"),
    Ror("AL-R03", FXP16, "AL-L02", "AL-L03"),
    Ror("AL-R04", FXP16, "AL-L03", "AL-L04"),
    Ror("AL-R05", FXP16, "AL-L01", "AL-L05"),
    Ror("AL-R06", FXP16, "AL-B1", "AL-L06",
        via=(i_vagg("2C", DIMMER_U, _OVER_KAMIN), i_vagg("2C", _NV_U, _OVER_KAMIN), *vid_tak("2C", _NV_U))),
    Ror("AL-R07", FXP16, "AL-L06", "AL-L07"),
    Ror("AL-R08", FXP16, "AL-L07", "AL-L08"),
    Ror("AL-R09", FXP16, "AL-L08", "AL-L09"),
    Ror("AL-R10", FXP16, "AL-B2", "AL-L10", via=vid_tak("2C", DIMMER_U + 80.0)),
    Ror("AL-R11", FXP16, "AL-L10", "AL-L11"),
]
