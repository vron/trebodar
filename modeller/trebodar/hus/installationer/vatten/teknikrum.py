"""Tappvattnet i teknikrummet: fördelarna i fördelarskåpet (..teknikrum.FORDELARSKAP på V19), fördelarnas utgångar
till tappställena, stråken i mellanbjälklaget och matarledningarna.

- Fördelarna: varmvattnets stam bakom och kallvattnets framför i skåpet, utgångarna uppåt c/c 40 från söder. Rören
  går upp ur skåpets öppna ovansida, in i mellanbjälklaget underifrån och västerut i det, varmvattnet överst (den
  bakre radens rör går över den främre radens), så att de inte korsar varandra. Samma utgång på båda fördelarna går
  till samma tappställe.
- Utgångarnas ordning (UTGANGAR) bestämmer filerna i stråken: rören viker av åt det håll där deras fil ligger ytterst.
  Från söder: stråket O (som viker av söderut först), S och V.
- Stråken, ingjutna i mellanbjälklaget: O söderut väster om skåpet och österut till källarrummet och köket; S västerut
  och söderut till badrummet och V7; V västerut och söderut längs V21.
- Matarledningarna (PEX 22) i teknikrummet: servisen till vattenmätaren, vattenmätaren till kallvattnets fördelare
  (inlopp i norra änden), kallvattnet vidare genom fördelaren till värmepumpens varmvattenberedare (genomgång i södra
  änden) och varmvattnet därifrån till varmvattnets fördelare (inlopp i södra änden, 1 m). De går under
  ventilationens kanal FF3, över värmepumpen.
"""
from __future__ import annotations

from ..montering import Vek
from ..teknikrum import FORDELARSKAP, SERVIS, VARMEPUMP, VATTENMATARE, Z_GOLV
from .katalog import FORDELARE_KV, FORDELARE_VV, PEX_22
from .punkter import Fordelare, Ror, Strak

_SK = FORDELARSKAP.lage.punkt                                   # på V19:s gips, normalen västerut
X_VV, X_KV = _SK[0] - 35.0, _SK[0] - 75.0                       # stammarna: varmvattnet bakom, kallvattnet framför
Y_UT = _SK[1] - FORDELARSKAP.matt[0] / 2 + 60.0                 # utgång 1 (söder)
Z_SKAP = _SK[2] + FORDELARSKAP.matt[2] / 2                      # skåpets ovansida

FD_VV = Fordelare("FD-VV", FORDELARE_VV, "VV", (X_VV, Y_UT, Z_GOLV + 1450.0), (0.0, 1.0, 0.0))
FD_KV = Fordelare("FD-KV", FORDELARE_KV, "KV", (X_KV, Y_UT, Z_GOLV + 1150.0), (0.0, 1.0, 0.0))
FORDELARE = [FD_VV, FD_KV]

# tappställe: (utgång på båda fördelarna, stråk), från söder
UTGANGAR: dict[str, tuple[int, str]] = {
    "KA-TH2": (1, "O"),             # källarrummet: viker av norrut till V15
    "KO-DB1": (2, "O"),
    "BA-DU1": (3, "S"),             # viker av söderut till väggen 1C före stråkets hörn
    "BA-WC1": (4, "S"),             # österut till L9
    "KA-TH3": (5, "S"),             # stråkets slut, längs V7
    "BA-TS1": (6, "S"),             # västerut
    "BA-BK1": (7, "S"),             # västerut, först
    "KA-TH1": (8, "V"),
    "KA-TM1": (9, "V"),             # västerut till V21, först
}


def _y(strak: str) -> float:
    """y för stråkets första sträcka: mitt för dess utgångar."""
    ys = [FD_KV.utgang(n)[1] for n, s in UTGANGAR.values() if s == strak]
    return (min(ys) + max(ys)) / 2


# stråken och deras slut utanför vinkeljärnen vid ytterväggarna (punkter.HINDER), där varmvattnet inte ryms över
# kallvattnet: rören går därifrån var för sig till tappställena
X_O, Y_O, X_O_SLUT = 4190.0, 8290.0, 13050.0   # O söderut väster om skåpet, österut mellan V19:s och V15:s järn
X_S, Y_S = 1500.0, 4320.0                       # S söderut under badrummet, till V7
X_V = 750.0                                     # V söderut längs V21
STRAK = {s.id: s for s in (
    Strak("O", ((_SK[0], _y("O")), (X_O, _y("O")), (X_O, Y_O), (X_O_SLUT, Y_O))),
    Strak("S", ((_SK[0], _y("S")), (X_S, _y("S")), (X_S, Y_S))),
    Strak("V", ((_SK[0], _y("V")), (X_V, _y("V")), (X_V, 7500.0))),
)}

_VP, _VM, _SV = VARMEPUMP.anslutningar, VATTENMATARE.anslutningar, SERVIS.anslutningar
Z_MATAR = _VP["VV-ut"][2] + 40.0                # matarledningarna över värmepumpen, under kanalen FF3


def _p(x: float, y: float, z: float) -> Vek:
    return (x, y, z)


_KV0, _KV11, _VV0 = FD_KV.utgang(0), FD_KV.utgang(FORDELARE_KV.utgangar + 1), FD_VV.utgang(0)
ROR = [
    Ror("VA-KV1", PEX_22, "KV", "TK-SV:ut", "TK-VM:in",
        via=(_p(_SV["ut"][0], _SV["ut"][1], _VM["in"][2] - 75.0), _p(_VM["in"][0], _VM["in"][1], _VM["in"][2] - 75.0))),
    Ror("VA-KV2", PEX_22, "KV", "TK-VM:ut", f"FD-KV:{FORDELARE_KV.utgangar + 1}",
        via=(_p(_VM["ut"][0], _VM["ut"][1], Z_SKAP + 50.0), _p(X_KV, _VM["ut"][1], Z_SKAP + 50.0),
             _p(X_KV, _KV11[1], Z_SKAP + 50.0))),
    Ror("VA-KV3", PEX_22, "KV", "FD-KV:0", "TK-VP:KV-in",
        via=(_p(X_KV, _KV0[1], Z_MATAR), _p(X_KV, _VP["KV-in"][1], Z_MATAR))),
    Ror("VA-VV1", PEX_22, "VV", "TK-VP:VV-ut", "FD-VV:0",
        via=(_p(_VP["VV-ut"][0], _VP["VV-ut"][1], Z_MATAR), _p(X_VV, _VP["VV-ut"][1], Z_MATAR),
             _p(X_VV, _VV0[1], Z_MATAR))),
]
