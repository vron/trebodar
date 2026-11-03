"""Köket: tubspotar som lyser upp mot snedtaket, spotar mot bänken, tre Stav över köksön och uttag ovanför fönstren
(belysningsplanen i ärende #8).

Två rader med tre Tube Mini R nära takfoten på var sida om nocken, mitt emellan installationsskiktets läkt, vinklade
tvärs över rummet mot mitten av det motsatta takfallet. En rad med sex Junistar Exclusive i takfallet 3NV, riktade mot
bänkens mitt (450 mm från väggen, 900 mm över golvet), alltså lutade mot väggen. Tre Stav i råmässing hänger över
köksön i nockens riktning, 700 mm över öns bänkskiva, mitt över ön (hus/inredning/koksbank.py).

Dimmern (två kanaler) och brytaren (Stav går inte att dimra) sitter på 2B mot gången, i facket närmast köket mitt
emot gaveln L16 av kökets inbyggnad (som under förrådet bara är två gipsskivor, ärende #21), brytaren över dimmern:
rören går upp i väggen och i installationsskiktet till varje rad. Uttagen
till kylen och frysen sitter på L4 i förrådet ovanför dem (nås genom luckan); sladdarna går upp genom springan längs
L4.
"""
from __future__ import annotations

from trebodar import skelett as S
from trebodar.hus.inredning.koksbank import ON_X, ON_Y
from trebodar.hus.stomme.prefab.takbalkar.takbalkar import TF2

from ..katalog import BRYTARE_1, DIMMER_2, FXP16, JUNISTAR_EXCLUSIVE, STAV, TUBE_MINI_R, UTTAG_1
from ..lakt import mellan_lakten
from ...montering import i_tak, tak, vagg, vid_tak
from ..punkter import Apparat, Lampa, Ror, Rum, Tandgrupp, mot, ovan_fonstret

RUM = Rum("KO", "Kök", plan=1)
NAMN = RUM.namn

NOCK = S.BALKAR["NB1"].x                     # högra huskroppens nock
Y_TUB = (8120.0, 9590.0, 11295.0)
RADER = {"3SO": 10070.0, "3NV": 13385.0}    # tubspotarna: önskat läge, flyttas till mitt mellan läkten
MAL = {"3SO": (NOCK + S.TAKFALL["3NV"].x_insida) / 2, "3NV": (NOCK + S.TAKFALL["3SO"].x_insida) / 2}
SPOT_X = 12970.0                             # spotarna mot bänken
Y_SPOT = (7745.0, 8495.0, 9245.0, 9995.0, 10745.0, 11495.0)
BANK_X = S.YTTERVAGGAR["3NV"].origo[0] - S.T_STOMME - 70.0 - 450.0     # bänkens mitt: 450 mm från väggens yta
BANK_Z = 900.0
STAV_X, Y_STAV, O_Z = ON_X, (ON_Y - 465.0, ON_Y, ON_Y + 465.0), 900.0    # Stav över ön, öns bänkskiva
U_B = 6007.0                                 # dimmern och brytaren på 2B, mitt i facket vid köket (y 7 072)
Z_B = (1050.0, 1130.0)                       # dimmern och brytaren över den
Z_UTTAG = 2300.0                             # uttagen till kylen och frysen, i förrådet
X_TF2 = (TF2.x_upp + NOCK) / 2               # rören till Stav förbi takfönstret TF2, mellan det och nocken

TANDGRUPPER = [
    Tandgrupp("KO-T1", "Kök, tubspotar mot taket"),
    Tandgrupp("KO-T2", "Kök, spotar mot bänken"),
    Tandgrupp("KO-T3", "Kök, Stav över ön", dimbar=False),
]


def _tubar(kod: str, start: int) -> list[Lampa]:
    """En rad tubspotar i takfallet kod, riktade mot det motsatta takfallet."""
    ut = []
    for i, y in enumerate(Y_TUB):
        m = tak(mellan_lakten(kod, RADER[kod], y), y)
        ut.append(Lampa(f"KO-L{start + i:02d}", TUBE_MINI_R, m, "KO-T1", riktning=mot(m, tak(MAL[kod], y).punkt)))
    return ut


def _spotar(start: int) -> list[Lampa]:
    ut = []
    for i, y in enumerate(Y_SPOT):
        m = tak(mellan_lakten("3NV", SPOT_X, y), y)
        ut.append(Lampa(f"KO-L{start + i:02d}", JUNISTAR_EXCLUSIVE, m, "KO-T2", riktning=mot(m, (BANK_X, y, BANK_Z))))
    return ut


PUNKTER = [
    *_tubar("3SO", 1),
    *_tubar("3NV", 4),
    *_spotar(7),
    *[Lampa(f"KO-L{13 + i:02d}", STAV, tak(STAV_X, y), "KO-T3", underkant=O_Z + 700.0) for i, y in enumerate(Y_STAV)],
    Apparat("KO-B1", DIMMER_2, vagg("2B", U_B, Z_B[0], sida=-1), styr=("KO-T1", "KO-T2")),
    Apparat("KO-B2", BRYTARE_1, vagg("2B", U_B, Z_B[1], sida=-1), styr=("KO-T3",)),
    Apparat("KO-U1", UTTAG_1, ovan_fonstret("3NV", 7215.0)),
    Apparat("KO-U2", UTTAG_1, ovan_fonstret("3NV", 9025.0)),
    Apparat("KO-U3", UTTAG_1, ovan_fonstret("3SV", 1745.0)),
    Apparat("KO-U4", UTTAG_1, vagg("L4", 250.0, Z_UTTAG, sida=1)),       # kylen (x 11 300)
    Apparat("KO-U5", UTTAG_1, vagg("L4", 1040.0, Z_UTTAG, sida=1)),      # frysen (x 12 090)
]


_VID_2B = vid_tak("2B", U_B, sida=-1)

ROR = [
    Ror("KO-R01", FXP16, "KO-B1", "KO-L01", via=_VID_2B),
    Ror("KO-R02", FXP16, "KO-L01", "KO-L02"),
    Ror("KO-R03", FXP16, "KO-L02", "KO-L03"),
    Ror("KO-R04", FXP16, "KO-B1", "KO-L04", via=_VID_2B),
    Ror("KO-R05", FXP16, "KO-L04", "KO-L05"),
    Ror("KO-R06", FXP16, "KO-L05", "KO-L06"),
    Ror("KO-R07", FXP16, "KO-B1", "KO-L07", via=_VID_2B),
    *[Ror(f"KO-R{8 + i:02d}", FXP16, f"KO-L{7 + i:02d}", f"KO-L{8 + i:02d}") for i in range(5)],
    Ror("KO-R13", FXP16, "KO-B2", "KO-L13", via=(*_VID_2B, i_tak(X_TF2, _VID_2B[1][1]), i_tak(X_TF2, Y_STAV[0]))),
    Ror("KO-R14", FXP16, "KO-L13", "KO-L14"),
    Ror("KO-R15", FXP16, "KO-L14", "KO-L15"),
]
