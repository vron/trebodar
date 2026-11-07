"""Badrummet (ärende #52) på inredningens lägen i hus/badrum.py: spotar i taket, en vägglampa över tvättstället,
dimmern utanför dörren, ett uttag vid bänken och anslutningen till handdukstorken.

Sex Junistar Exclusive (IP44 underifrån) i panelen, mitt emellan installationsskiktets läkt, lodrätt nedåt: två över
bänken, två längs rummets östra del (WC:n och handdukstorken), en framför duschen vid dörren och skåpet och en i
duschen; taket är över 2,25 m överallt, så de sitter utanför zonerna kring badkaret och duschen (SS 436 40 00, 701).
Över badkaret ligger takfönstret TF1. Över tvättstället, ovanför fönstret 1NO-F1, en vägglampa med glob av opalglas
(IP44). Dimmern med två kanaler (spotarna, lampan över tvättstället) sitter utanför badrummet på L11 mot allrummet, på
dörren ID1:s låssida; röret går upp i väggen och i installationsskiktet till spotarna, och lampan över tvättstället
får sitt rör från spoten närmast den, ned i gavelns installationsskikt. Uttaget (dubbelt, IP44) sitter på L9 vid
bänkens ände, utanför zonerna; handdukstorken (elektrisk, IPX4, i zon 2 vid badkaret och duschen) är fast ansluten
till en dosa på 1A bakom den. Uttag och anslutningar matas från en jordfelsbrytare 30 mA i centralen (som inte är
placerad, ärende #51).
"""
from __future__ import annotations

from trebodar import skelett as S
from trebodar.hus import badrum as B
from trebodar.hus.invandigt.vaggar import vaggdef

from ..katalog import ANSLUTNING, APPARATDOSA, DIMMER_2, FXP16, JUNISTAR_EXCLUSIVE, UTTAG_1_IP44, UTTAG_2_IP44, VAGGLAMPA
from ..lakt import mellan_lakten
from ...montering import Montering, tak, vagg, vid_tak
from ...ventilation.grenar.badrum import U as U_FF2, Z as Z_FF2
from ..punkter import Apparat, Dosa, Lampa, Ror, Rum, Tandgrupp

RUM = Rum("BA", "Badrum", plan=1)
NAMN = RUM.namn

# spotarna: takfallet och önskat läge (flyttas till mitt mellan läkten)
SPOTAR = (("1SO", 700.0, 4250.0), ("1SO", 1800.0, 4250.0), ("1SO", 1800.0, 5300.0), ("1SO", 1800.0, 6850.0),
          ("1NV", 2850.0, 6650.0), ("1NV", 2700.0, 7650.0))
_L11 = vaggdef("L11")
U_B = B.ID1.u1 + 100.0                       # dimmern på L11 mot allrummet, på dörrens låssida (i regelfacket)
_L9 = vaggdef("L9")
U_UTTAG = B.Y_1NO + 250.0 - _L9.origo[1]     # uttaget på L9 vid bänkens ände
Z_UTTAG = B.Z_BANK + B.BANK_Z + 230.0
U_LAMPA = B.LAMPA_TVATTSTALL[0] - S.YTTERVAGGAR["1NO"].origo[0]
U_TORK = B.HANDDUKSTORK[0] + 60.0 - S.INNERVAGGAR["1A"].origo[0]
# tvätten i skåpet (#51): två enkla uttag IP44 i en dubbel ram vid användarens markering (B.TVATT_UTTAG), på L10
# ovanför maskinerna, tvättmaskinen och torktumlaren på var sin grupp; fläkten FF2 fast ansluten bredvid den
_L10 = vaggdef("L10")
U_TVATT = (B.TVATT_UTTAG[0] - 40.0 - _L10.origo[0], B.TVATT_UTTAG[0] + 40.0 - _L10.origo[0])
U_FLAKT = U_FF2 + 250.0


def _over_golvet(kod: str, u: float, z: float, sida: int) -> Montering:
    """På väggens färdiga yta vid u, z över golvet vid väggen (badrumsgolvets fall)."""
    m = vagg(kod, u, 0.0, sida)
    return vagg(kod, u, B.golvniva(m.punkt[0] + m.normal[0] * 2.0, m.punkt[1] + m.normal[1] * 2.0) + z, sida)



TANDGRUPPER = [
    Tandgrupp("BA-T1", "Badrum, spotar"),
    Tandgrupp("BA-T2", "Badrum, lampan över tvättstället"),
]

PUNKTER = [
    *[Lampa(f"BA-L{i + 1:02d}", JUNISTAR_EXCLUSIVE, tak(mellan_lakten(kod, x, y), y), "BA-T1")
      for i, (kod, x, y) in enumerate(SPOTAR)],
    Lampa("BA-L07", VAGGLAMPA, vagg("1NO", U_LAMPA, B.LAMPA_TVATTSTALL[1]), "BA-T2"),
    Apparat("BA-B1", DIMMER_2, vagg("L11", U_B, 1050.0, sida=-1), styr=("BA-T1", "BA-T2")),
    Apparat("BA-U1", UTTAG_2_IP44, vagg("L9", U_UTTAG, Z_UTTAG, sida=1)),
    Dosa("BA-D1", APPARATDOSA, vagg("1A", U_TORK, B.golvniva(B.HANDDUKSTORK[0] + 60.0, B.Y_1A - 5.0) + 500.0,
                                   sida=-1)),
    *[Apparat(f"BA-U{2 + i}", UTTAG_1_IP44, _over_golvet("L10", u, B.TVATT_UTTAG[1], 1)) for i, u in enumerate(U_TVATT)],
    Apparat("BA-D2", ANSLUTNING, vagg("1NO", U_FLAKT, Z_FF2)),
]

_VID_L11 = vid_tak("L11", U_B, sida=-1)
_VID_1NO = vid_tak("1NO", U_LAMPA)

ROR = [
    Ror("BA-R01", FXP16, "BA-B1", "BA-L05", via=_VID_L11),
    Ror("BA-R02", FXP16, "BA-L05", "BA-L06"),
    Ror("BA-R03", FXP16, "BA-L05", "BA-L04"),
    Ror("BA-R04", FXP16, "BA-L04", "BA-L03"),
    Ror("BA-R05", FXP16, "BA-L03", "BA-L02"),
    Ror("BA-R06", FXP16, "BA-L02", "BA-L01"),
    Ror("BA-R07", FXP16, "BA-L02", "BA-L07", via=(_VID_1NO[1], _VID_1NO[0])),
]
