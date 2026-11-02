"""Tappvattnet i teknikrummet: fördelarna i fördelarskåpet (..teknikrum.FORDELARSKAP på V19), rörens ordning från
fördelarna, stråken i mellanbjälklaget och matarledningarna.

- Fördelarna: varmvattnets stam bakom och kallvattnets framför i skåpet, utgångarna uppåt. Varje rör har en egen fil,
  c/c 40 längs V19 från söder, och kallvattnets och varmvattnets utgångar sitter i sina rörs filer: rören går upp ur
  skåpets öppna ovansida rakt in i mellanbjälklaget och vidare i en nivå utan att korsa varandra (den bakre radens rör
  går mellan den främre radens).
- Tappställenas ordning (ORDNING, från söder) bestämmer filerna i stråken: rören viker av åt det håll där deras fil
  ligger ytterst. Ett tappställes två rör ligger bredvid varandra, det som viker av först ytterst (system.py).
- Stråken, ingjutna i mellanbjälklaget: O österut över V19 till källarrummet och köket; S västerut och söderut till
  badrummet och längs V7; V västerut och söderut längs V21.
- Matarledningarna (PEX 22) i teknikrummet: servisen till vattenmätaren, vattenmätaren till kallvattnets fördelare
  (inlopp i norra änden), kallvattnet vidare genom fördelaren till värmepumpens varmvattenberedare (genomgång i södra
  änden) och varmvattnet därifrån till varmvattnets fördelare (inlopp i södra änden, 1 m). De går under
  ventilationens kanal FF3, över värmepumpen.
"""
from __future__ import annotations

from ..montering import Vek, i_vaggen, kallarvagg
from ..teknikrum import FORDELARSKAP, SERVIS, VARMEPUMP, VATTENMATARE, Z_GOLV
from .katalog import PEX_22
from ..strak import Strak
from .punkter import Fordelare, Ror
from .typer import Fordelartyp

_SK = FORDELARSKAP.lage.punkt                                   # på V19:s gips, normalen västerut
X = {"VV": _SK[0] - 35.0, "KV": _SK[0] - 75.0}                  # stammarna: varmvattnet bakom, kallvattnet framför
Z = {"VV": Z_GOLV + 1450.0, "KV": Z_GOLV + 1150.0}
Y_FIL0 = _SK[1] - FORDELARSKAP.matt[0] / 2 + 80.0               # den första filen (söder)

# tappställe: (stråk, stråkets ben där rören viker av; None: närmast), från söder
ORDNING: dict[str, tuple[str, int | None]] = {
    "KO-DB1": ("O", None),
    "KA-TH2": ("O", None),          # källarrummet: viker av norrut till V15 före köket
    "BA-DU1": ("S", 0),             # viker av söderut till väggen 1C före stråkets hörn
    "BA-WC1": ("S", 1),             # österut till L9
    "KA-TH3": ("S", 2),             # stråkets slut, längs V7
    "BA-TS1": ("S", 1),             # västerut
    "BA-BK1": ("S", 1),             # västerut, först
    "KA-TH1": ("V", 1),
    "KA-TM1": ("V", 1),             # västerut till V21, först
}

X_O = 13400.0                                   # O österut till köket
X_S, X_V = 1500.0, 450.0                        # S söderut under badrummet, V längs V21
Y_V7 = i_vaggen(kallarvagg("V7", 0.0, 0.0, 1), (0.0, 0.0, 0.0))[1]       # S längs V7:s cellplast


def strak(mitt: dict[str, float]) -> dict[str, Strak]:
    """Stråken, med deras första sträcka genom mitten av sina filer (mitt: y per stråk)."""
    return {s.id: s for s in (
        Strak("O", ((X["KV"] - 100.0, mitt["O"]), (X_O, mitt["O"]))),
        Strak("S", ((X["VV"] + 100.0, mitt["S"]), (X_S, mitt["S"]), (X_S, Y_V7), (3800.0, Y_V7))),
        Strak("V", ((X["VV"] + 100.0, mitt["V"]), (X_V, mitt["V"]), (X_V, 7500.0))),
    )}


def fordelare(media: str, typ: Fordelartyp, filer: tuple[int, ...]) -> Fordelare:
    """Fördelaren för media med utgångarna i filerna (längs V19 norrut från Y_FIL0)."""
    return Fordelare(f"FD-{media}", typ, media, (X[media], Y_FIL0, Z[media]), (0.0, 1.0, 0.0), filer)


_VP, _VM, _SV = VARMEPUMP.anslutningar, VATTENMATARE.anslutningar, SERVIS.anslutningar
Z_MATAR = _VP["VV-ut"][2] + 40.0                # matarledningarna över värmepumpen, under kanalen FF3
Z_OVER_SKAP = _SK[2] + FORDELARSKAP.matt[2] / 2 + 50.0


def _p(x: float, y: float, z: float) -> Vek:
    return (x, y, z)


def matarledningar(fd_kv: Fordelare, fd_vv: Fordelare) -> list[Ror]:
    """Matarledningarna till fördelarnas ändar."""
    kv0, kv_n, vv0 = fd_kv.utgang(0), fd_kv.utgang(fd_kv.utgangar + 1), fd_vv.utgang(0)
    return [
        Ror("VA-KV1", PEX_22, "KV", "TK-SV:ut", "TK-VM:in",
            via=(_p(_SV["ut"][0], _SV["ut"][1], _VM["in"][2] - 75.0),
                 _p(_VM["in"][0], _VM["in"][1], _VM["in"][2] - 75.0))),
        Ror("VA-KV2", PEX_22, "KV", "TK-VM:ut", f"FD-KV:{fd_kv.utgangar + 1}",
            via=(_p(_VM["ut"][0], _VM["ut"][1], Z_OVER_SKAP), _p(X["KV"], _VM["ut"][1], Z_OVER_SKAP),
                 _p(X["KV"], kv_n[1], Z_OVER_SKAP))),
        Ror("VA-KV3", PEX_22, "KV", "FD-KV:0", "TK-VP:KV-in",
            via=(_p(X["KV"], kv0[1], Z_MATAR), _p(X["KV"], _VP["KV-in"][1], Z_MATAR))),
        Ror("VA-VV1", PEX_22, "VV", "TK-VP:VV-ut", "FD-VV:0",
            via=(_p(_VP["VV-ut"][0], _VP["VV-ut"][1], Z_MATAR), _p(X["VV"], _VP["VV-ut"][1], Z_MATAR),
                 _p(X["VV"], vv0[1], Z_MATAR))),
    ]
