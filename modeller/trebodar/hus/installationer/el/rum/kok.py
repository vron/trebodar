"""Köket: tubspotar som lyser upp mot snedtaket, spotar mot bänken, tre Stav över köksön och uttag ovanför fönstren
(belysningsplanen i ärende #8).

Två rader med tre Tube Mini R en bit upp på takfallen på var sida om nocken (två läktfack högre än vid takfoten; den
under takfönstret TF2 nära takfoten, eftersom fönstret tar takfallet ovanför), mitt emellan installationsskiktets läkt,
vinklade tvärs över rummet mot mitten av det motsatta takfallet. En rad med sex Junistar Exclusive i takfallet 3NV,
riktade mot bänkens mitt (450 mm från väggen, 900 mm över golvet), alltså lutade mot väggen. Tre Stav i råmässing hänger
över köksön i nockens riktning, 700 mm över öns bänkskiva, mitt över ön (hus/inredning/koksbank.py).

Dimmern (två kanaler) och brytaren (Stav går inte att dimra) sitter på 2B mot gången, i facket närmast köket mitt
emot gaveln L16 av kökets inbyggnad (som under förrådet bara är två gipsskivor, ärende #21), brytaren över dimmern:
rören går upp i väggen och i installationsskiktet till varje rad. Uttagen
till kylen och frysen sitter på L4 i förrådet ovanför dem (nås genom luckan); sladdarna går upp genom springan längs
L4.

Apparaterna och uttagen vid bänken och ön (#50, grupperna i ../grupper.py):

- hällen fast ansluten, 400 V, i en anslutningsdosa på 3NV bakom hällens skåp (KO-D1), och köksfläkten i ett uttag
  på 3NV inne i fläktens kåpa (KO-U13);
- ugnen eller mikron i ett uttag på 3NV i skafferiet (KO-U6), eftersom köket inte har någon ugn ritad;
- vid bänken dubbla uttag 250 mm över bänkskivan där väggen är fri från fönster (KO-U8 vid bänkens början, KO-U9
  efter fönstret 3NV-F5, KO-U10 på 3SV före fönstret 3SV-F1), med de befintliga ovanför fönstren på samma grupp; rören
  i ytterväggens installationsskikt, under fönstren eller ovanför dem;
- i ön dubbla uttag på ryggen mot benutrymmet (KO-U11, KO-U12, under bänkskivan) och diskmaskinens uttag på ryggen
  bakom skåpet bredvid maskinen (KO-U7); rören upp ur mellanbjälklaget i öns rygg.
"""
from __future__ import annotations

from trebodar import skelett as S
from trebodar.hus.inredning.koksbank import FOGAR_ON, ON_X, ON_Y, SIDA_T, X_ON_FRONT, Y_HALL
from trebodar.hus.inredning.koksskap import DJUP, FRONT_T
from trebodar.hus.stomme.prefab.takbalkar.takbalkar import TF2

from ..katalog import ANSLUTNING_3FAS, BRYTARE_1, DIMMER_2, FXP16, JUNISTAR_EXCLUSIVE, STAV, TUBE_MINI_R, UTTAG_1, UTTAG_2
from ..lakt import mellan_lakten
from ...montering import Montering, i_tak, i_vagg, langs_vaggen, tak, vagg, vid_tak
from ..punkter import Apparat, Lampa, Ror, Rum, Tandgrupp, mot, ovan_fonstret

RUM = Rum("KO", "Kök", plan=1)
NAMN = RUM.namn

NOCK = S.BALKAR["NB1"].x                     # högra huskroppens nock
Y_TUB = (8120.0, 9590.0, 11295.0)
RADER = {"3SO": 10765.0, "3NV": 12690.0}    # tubspotarna: önskat läge, flyttas till mitt mellan läkten
UNDER_TF2 = 10070.0                          # tubspoten i 3SO under takfönstret TF2, som tar takfallet ovanför
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
_X_UNDER = mellan_lakten("3SO", UNDER_TF2, Y_TUB[0])    # KO-L01 under TF2: röret till KO-L02 längs y under fönstret
Z_BANKUTTAG = 1150.0                         # uttagen vid bänken: 250 över bänkskivan (888 + 12)
Z_HALL = 600.0                               # hällens anslutningsdosa bakom skåpet
Z_FLAKT = 2250.0                             # köksfläktens uttag inne i kåpan
Z_SKAFFERI = 1100.0                          # ugnen eller mikron i skafferiet
Y_BANKUTTAG = (7750.0, 11350.0)              # längs 3NV: vid bänkens början och efter 3NV-F5
X_BANKUTTAG = 11650.0                        # längs 3SV, före 3SV-F1
Y_SKAFFERI = 6950.0
X_ON_RYGG = X_ON_FRONT - FRONT_T - DJUP - SIDA_T         # öns rygg (ytan mot benutrymmet)
X_ON_ROR = X_ON_RYGG + 50.0                  # öns rör upp ur golvet i skåpens bakkant, bakom lådorna
Z_ON = 750.0                                 # öns uttag, under bänkskivan
Y_ON = (Y_HALL + 40.0, Y_HALL + 640.0)       # öns uttag på ryggen, bakom skåpen bredvid diskmaskinen
Y_DM = (FOGAR_ON[1] + FOGAR_ON[2]) / 2 - 150.0   # diskmaskinens uttag bakom skåpet bredvid maskinen
Z_DM = 200.0


def _3nv(y: float, z: float) -> Montering:
    return vagg("3NV", langs_vaggen("3NV", (0.0, y, 0.0)), z)


def _on(y: float, z: float) -> Montering:
    """På öns rygg mot benutrymmet (normalen åt väster)."""
    return Montering((X_ON_RYGG, y, z), (-1.0, 0.0, 0.0), "vagg", "Ön")

TANDGRUPPER = [
    Tandgrupp("KO-T1", "Kök, tubspotar mot taket"),
    Tandgrupp("KO-T2", "Kök, spotar mot bänken"),
    Tandgrupp("KO-T3", "Kök, Stav över ön", dimbar=False),
]


def _tubar(kod: str, start: int) -> list[Lampa]:
    """En rad tubspotar i takfallet kod, riktade mot det motsatta takfallet."""
    ut = []
    for i, y in enumerate(Y_TUB):
        x = UNDER_TF2 if kod == "3SO" and TF2.y0 <= y <= TF2.y1 else RADER[kod]
        m = tak(mellan_lakten(kod, x, y), y)
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
    Apparat("KO-U4", UTTAG_1, vagg("L4", 200.0, Z_UTTAG, sida=1)),       # kylen (x 11 250; röret upp minst 200 mm
    #                                                                       från huvudstolpens bultar, #114)
    Apparat("KO-U5", UTTAG_1, vagg("L4", 1040.0, Z_UTTAG, sida=1)),      # frysen (x 12 090)
    Apparat("KO-D1", ANSLUTNING_3FAS, _3nv(Y_HALL, Z_HALL)),
    Apparat("KO-U6", UTTAG_1, _3nv(Y_SKAFFERI, Z_SKAFFERI)),
    Apparat("KO-U7", UTTAG_1, _on(Y_DM, Z_DM)),
    Apparat("KO-U8", UTTAG_2, _3nv(Y_BANKUTTAG[0], Z_BANKUTTAG)),
    Apparat("KO-U9", UTTAG_2, _3nv(Y_BANKUTTAG[1], Z_BANKUTTAG)),
    Apparat("KO-U10", UTTAG_2, vagg("3SV", langs_vaggen("3SV", (X_BANKUTTAG, 0.0, 0.0)), Z_BANKUTTAG)),
    Apparat("KO-U11", UTTAG_2, _on(Y_ON[0], Z_ON)),
    Apparat("KO-U12", UTTAG_2, _on(Y_ON[1], Z_ON)),
    Apparat("KO-U13", UTTAG_1, _3nv(Y_HALL, Z_FLAKT)),
]


_VID_2B = vid_tak("2B", U_B, sida=-1)

ROR = [
    Ror("KO-R01", FXP16, "KO-B1", "KO-L01", via=_VID_2B),
    Ror("KO-R02", FXP16, "KO-L01", "KO-L02", via=(i_tak(_X_UNDER, Y_TUB[1]),)),
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
