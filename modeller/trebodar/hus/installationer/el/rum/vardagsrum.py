"""Vardagsrummet i vänstra huskroppen: spotar lutade mot långsidorna, tre VL45 Radiohus i en klunga, dimrarna på 1D
och uttag ovanför fönstren (belysningsplanen i ärende #8).

Två rader med fyra Junistar Exclusive nära långsidorna, mitt emellan installationsskiktets läkt, lutade 9° från
lodlinjen mot närmaste långsida (snedtaket vrider redan armaturen 30° åt andra hållet, och den tål 40°). Tre VL45 i
de tre storlekarna hänger i en klunga nära nocken, på olika höjd: den största lägst. Dimrarna (två kanaler för
spotarna, en för VL45) sitter på 1D (vardagsrumssidan) vid öppningen mot hallen; rören går upp i väggen och längs
raderna i installationsskiktet.
"""
from __future__ import annotations

from ..katalog import DIMMER_1, DIMMER_2, FXP16, JUNISTAR_EXCLUSIVE, UTTAG_1, VL45_175, VL45_250, VL45_370
from ..lakt import mellan_lakten
from ...montering import tak, vagg, vid_tak
from ..punkter import Apparat, Lampa, Ror, Rum, Tandgrupp, lutad, ovan_fonstret

RUM = Rum("VR", "Vardagsrum", plan=1)
NAMN = RUM.namn

RADER = (("1SO", 565.0, (11465.0, 12665.0, 13865.0, 15065.0), -1.0, "VR-T1"),
         ("1NV", 3570.0, (11530.0, 12730.0, 13930.0, 15130.0), 1.0, "VR-T2"))   # takfall, x, y, mot väggen
LUTNING = 9.0
# VL45: typ, läge och underkant över golvet (den största lägst)
VL45 = ((VL45_250, 1740.0, 13245.0, 1950.0), (VL45_370, 2065.0, 13515.0, 1700.0), (VL45_175, 1725.0, 13645.0, 2150.0))
U_B = 1850.0                                  # dimrarna längs 1D, vid öppningen mot hallen

TANDGRUPPER = [
    Tandgrupp("VR-T1", "Vardagsrum, spotar sydost"),
    Tandgrupp("VR-T2", "Vardagsrum, spotar nordväst"),
    Tandgrupp("VR-T3", "Vardagsrum, VL45"),
]

PUNKTER = [
    *[Lampa(f"VR-L{4 * i + j + 1:02d}", JUNISTAR_EXCLUSIVE, tak(mellan_lakten(kod, x, y), y), tand,
            riktning=lutad((s, 0.0), LUTNING))
      for i, (kod, x, ys, s, tand) in enumerate(RADER) for j, y in enumerate(ys)],
    *[Lampa(f"VR-L{9 + i:02d}", t, tak(x, y), "VR-T3", underkant=z) for i, (t, x, y, z) in enumerate(VL45)],
    Apparat("VR-B1", DIMMER_2, vagg("1D", U_B, 1050.0, sida=1), styr=("VR-T1", "VR-T2")),
    Apparat("VR-B2", DIMMER_1, vagg("1D", U_B + 80.0, 1050.0, sida=1), styr=("VR-T3",)),
    Apparat("VR-U1", UTTAG_1, ovan_fonstret("1NV", 1000.0)),
    Apparat("VR-U2", UTTAG_1, ovan_fonstret("1SO", 3445.0)),
    Apparat("VR-U3", UTTAG_1, ovan_fonstret("1SO", 1645.0)),
]

ROR = [
    Ror("VR-R01", FXP16, "VR-B1", "VR-L01", via=vid_tak("1D", U_B, sida=1)),
    *[Ror(f"VR-R{2 + i:02d}", FXP16, f"VR-L{1 + i:02d}", f"VR-L{2 + i:02d}") for i in range(3)],
    Ror("VR-R05", FXP16, "VR-B1", "VR-L05", via=vid_tak("1D", U_B, sida=1)),
    *[Ror(f"VR-R{6 + i:02d}", FXP16, f"VR-L{5 + i:02d}", f"VR-L{6 + i:02d}") for i in range(3)],
    Ror("VR-R09", FXP16, "VR-B2", "VR-L09", via=vid_tak("1D", U_B + 80.0, sida=1)),
    Ror("VR-R10", FXP16, "VR-L09", "VR-L10"),
    Ror("VR-R11", FXP16, "VR-L10", "VR-L11"),
]
