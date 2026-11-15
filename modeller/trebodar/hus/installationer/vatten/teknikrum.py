"""Tappvattnet i teknikrummet: fördelarna i fördelarskåpet (..teknikrum.FORDELARSKAP på V19), rörens ordning från
fördelarna, stråken i mellanbjälklaget och matarledningarna.

- Fördelarna: varmvattnets stam bakom och kallvattnets framför i skåpet, utgångarna uppåt. Varje rör har en egen fil,
  c/c 50 längs V19 från norr, och kallvattnets och varmvattnets utgångar sitter i sina rörs filer: rören går upp ur
  skåpets öppna ovansida rakt in i mellanbjälklaget och vidare i en nivå utan att korsa varandra (den bakre radens rör
  går mellan den främre radens). Stammarna och den första filen ligger så att rören går upp mellan
  underkantsnätets järn.
- Tappställenas ordning (ORDNING, från norr) bestämmer filerna i stråken: rören viker av åt det håll där deras fil
  ligger ytterst. Ett tappställes två rör ligger bredvid varandra, det som viker av först ytterst (system.py).
- Stråken, ingjutna i mellanbjälklaget: O österut över V19 (mellan dess lodräta järn) med varmvattnet till
  underfördelaren UF1 under köket; S2, S och V västerut. Stommens bultar ska ha minst 200 mm till rören
  (stomme/forankring.py), och de bärande väggarna korsas bara i passagerna (../passager.py, #114): strax väster om
  skåpet går stråken bort från 1C och smalnar av (c/c TAT i stället för FIL, skyddsrören nästan mot varandra). S2
  (duschen, underfördelaren UF2 och källarens tvättho längs V7), S (badkaret och tvättstället) och V (längs V21) går
  norr om 1C genom 1B:s passage, S2 och S sedan i var sin passage genom 1A; duschens rör viker av österut söder om
  1A och går under badrummet till blandaren på L11.
- Matarledningarna (#139). Servisen (PEM 32) kommer upp under köket vid V14, till vattenmätaren på väggen. Från
  mätaren går tre ledningar: kallvattnet till underfördelaren UF1 (köket, PEX 22 på väggen), huvudledningen (PEM 32
  i skyddsrör, samma dimension som servisen) ned genom bottenplattan, under den västerut i cellplasten och upp i
  teknikrummet vid V3, och en klenare (PEM 20 i skyddsrör) under plattan till tvätthoet KA-TH2 i källarrummet, som
  bara har kallvatten. I mellanbjälklaget går därför bara varmvattnet till UF1 österut. I teknikrummet (PEX 22):
  huvudledningen till kallvattnets fördelare (inlopp i södra änden), kallvattnet vidare genom fördelaren till
  värmepumpens varmvattenberedare (genomgång i norra änden) och varmvattnet därifrån till varmvattnets fördelare
  (inlopp i norra änden, 1 m). De går över värmepumpen.
"""
from __future__ import annotations

from trebodar.hus.grund import grund as G

from ..montering import KALLARTAK, Vek, i_vaggen, kallarvagg
from ..strak import Strak, glipa, mellan_jarnen
from ..teknikrum import FORDELARSKAP, HUVUDLEDNING, VARMEPUMP, VATTENMATARE, Z_GOLV
from .katalog import PEM_20, PEM_32, PEX_22
from .punkter import FIL, R_ROR, Z_ROR, Fordelare, Ror, Tappstalle, anslutning
from .typer import Fordelartyp

_SK = FORDELARSKAP.lage.punkt                                   # på V19:s gips, normalen västerut
X = {"VV": _SK[0] - 25.0, "KV": _SK[0] - 95.0}                  # stammarna: varmvattnet bakom, kallvattnet framför
Z = {"VV": Z_GOLV + 1450.0, "KV": Z_GOLV + 1150.0}
# den första filen (norr), mellan nätets järn; de tre nordligaste filerna är tomma sedan kökets kallvatten och
# källarrummets tvättho matas från vattenmätaren (#139), så att de andra rören ligger kvar i sina lägen
_Y0 = _SK[1] - FORDELARSKAP.matt[0] / 2 + 65.0 + 3 * FIL
Y_FIL0 = _Y0 + mellan_jarnen([(x, _Y0 + k * FIL) for x in X.values() for k in range(-1, 18)], KALLARTAK, Z_ROR,
                             R_ROR, langs=(0.0, 1.0))[1]

# tappställe eller underfördelare (underfordelare.py): (stråk, stråkets ben där rören viker av; None: närmast), från
# norr; stråken västerut går norr och söder om 1C (inte under den): duschen norr om, O emellan
ORDNING: dict[str, tuple[str, int | None]] = {
    "UF1": ("O", None),             # underfördelaren under köket, på V14 (bara varmvattnet: kallvattnet från mätaren)
    "BA-DU1": ("S2", 5),            # viker av österut söder om 1A och svängen, under badrummet till nischen och L11
    "UF2": ("S2", 5),               # underfördelaren under badrummet, österut till KL1
    "KA-TH3": ("S2", 6),            # stråkets slut, längs V7
    "BA-TS1": ("S", 5),             # västerut
    "BA-BK1": ("S", 5),             # västerut, först
    "KA-TH1": ("V", 3),
    "KA-TM1": ("V", 3),             # västerut till V21, först
}

DIREKT = ("KA-TH2",)                            # tappställen med rör direkt från vattenmätaren, under bottenplattan
X_O = 13400.0                                   # O österut till underfördelaren UF1 på V14
X_O_SODER, Y_O_KOK = 10000.0, 9450.0             # O till y Y_O_KOK före köket, förbi diskmaskinens hylsa i ön och
#                                                 diskmaskinens pumpade avlopp, och till UF1:s början från det hållet
TAT = 36.0                                      # rören i stråken efter avsmalningen (c/c): skyddsrören 25 och 28
X_SMAL = (4000.0, 3650.0)                       # avsmalningen, öster om 1C:s ände
Y_NORR = {"S2": 8546.0, "S": 8706.0, "V": 8829.0}   # S2, S och V västerut norr om 1C (minst 200 mm från dess
#                                                     bultar) och söder om gruppcentralens rör, genom 1B:s passage
Y_SVANG = (6800.0, 6400.0)                          # S2 och S viker av i sidled söder om 1A
X_S2, X_S, X_V = 1659.0, 1078.0, 450.0          # S2 och S söderut genom var sin passage i 1A, V längs V21
X_S2_SODER = 1440.0                             # S2 söder om 1A: väster om källarens elrör KA-R7 upp i bjälklaget
X_S_SODER = 1255.0                              # S söder om 1A: tvättställets rör vågrätt in i golvdosan från öster,
Y_S_SLUT = 3870.0                               # förbi tvättställets avlopp
Y_V7 = i_vaggen(kallarvagg("V7", 0.0, 0.0, 1), (0.0, 0.0, 0.0))[1] + 150.0      # S längs V7, rören viker av
#                                                                               till dess cellplast


def strak(mitt: dict[str, float]) -> dict[str, Strak]:
    """Stråken, med deras första sträcka genom mitten av sina filer (mitt: y per stråk); O går över V19 mitt i en glipa
    mellan väggens lodräta järn."""
    y_o = glipa("V19", Z_ROR, mitt["O"])
    x0, (xa, xb), k = X["VV"] + 100.0, X_SMAL, TAT / FIL

    def vasterut(id_: str, y: float, *resten: tuple[float, float]) -> Strak:
        p = ((x0, mitt[id_]), (xa, mitt[id_]), (xb, y), *resten)
        return Strak(id_, p, (1.0,) + (k,) * (len(p) - 2))
    return {s.id: s for s in (
        Strak("O", ((X["KV"] - 100.0, mitt["O"]), (_SK[0] + 80.0, mitt["O"]), (_SK[0] + 80.0, y_o), (X_O_SODER, y_o),
                    (X_O_SODER, Y_O_KOK), (X_O, Y_O_KOK))),
        vasterut("S2", Y_NORR["S2"], (X_S2, Y_NORR["S2"]), (X_S2, Y_SVANG[0]), (X_S2_SODER, Y_SVANG[1]), (X_S2_SODER, Y_V7),
                 (3800.0, Y_V7)),
        vasterut("S", Y_NORR["S"], (X_S, Y_NORR["S"]), (X_S, Y_SVANG[0]), (X_S_SODER, Y_SVANG[1]), (X_S_SODER, Y_S_SLUT)),
        vasterut("V", Y_NORR["V"], (X_V, Y_NORR["V"]), (X_V, 7500.0)),
    )}


def fordelare(media: str, typ: Fordelartyp, filer: tuple[int, ...]) -> Fordelare:
    """Fördelaren för media med utgångarna i filerna (längs V19 söderut från Y_FIL0)."""
    return Fordelare(f"FD-{media}", typ, media, (X[media], Y_FIL0, Z[media]), (0.0, 1.0, 0.0), filer)


_VP, _VM, _HL = VARMEPUMP.anslutningar, VATTENMATARE.anslutningar, HUVUDLEDNING.anslutningar
Z_MATAR = _VP["VV-ut"][2] + 40.0                # matarledningarna över värmepumpen
Z_OVER_SKAP = _SK[2] + FORDELARSKAP.matt[2] / 2 + 50.0
# under bottenplattan (#139): ledningarna i skyddsrör i cellplasten under plattans balkar (Z_UNDER), bredvid
# varandra; ned genom plattan vid V14 norr om mätaren, mellan armeringsjärnen (flyttade längs väggen)
Z_UNDER = Z_GOLV - G.H_BALK - 50.0
OVER_MATAREN = {"ut": 80.0, "th2": 160.0}        # ledningarna vänder så högt över mätarens anslutningar


def _ned(namn: str, onskat: float, r: float) -> float:
    """Där ledningen går ned genom bottenplattan vid V14 (y), nära onskat och mellan järnen."""
    x = _VM[namn][0]
    return onskat + mellan_jarnen([(x, onskat)], Z_UNDER, Z_GOLV, r, langs=(0.0, 1.0))[1]


Y_NED = {"ut": _ned("ut", _HL["in"][1], PEM_32.yttre / 2), "th2": _ned("th2", _HL["in"][1] - 80.0, PEM_20.yttre / 2)}


def _p(x: float, y: float, z: float) -> Vek:
    return (x, y, z)


def matarledningar(fd_kv: Fordelare, fd_vv: Fordelare) -> list[Ror]:
    """Matarledningarna: servisen till vattenmätaren, huvudledningen under bottenplattan till teknikrummet och till
    fördelarnas ändar."""
    kv0, kv_n, vv0 = fd_kv.utgang(0), fd_kv.utgang(fd_kv.utgangar + 1), fd_vv.utgang(0)
    xm, ym, zm = _VM["ut"]
    xh, yh, _ = _HL["in"]
    return [
        Ror("VA-KV1", PEM_32, "KV", "TK-SV:ut", "TK-VM:in"),
        Ror("VA-KV2", PEM_32, "KV", "TK-VM:ut", "TK-HL:in",
            via=(_p(xm, ym, zm + OVER_MATAREN["ut"]), _p(xm, Y_NED["ut"], zm + OVER_MATAREN["ut"]),
                 _p(xm, Y_NED["ut"], Z_UNDER), _p(xh, Y_NED["ut"], Z_UNDER), _p(xh, yh, Z_UNDER))),
        Ror("VA-KV4", PEX_22, "KV", "TK-HL:ut", f"FD-KV:{fd_kv.utgangar + 1}",
            via=(_p(xh, yh, Z_OVER_SKAP), _p(X["KV"], yh, Z_OVER_SKAP), _p(X["KV"], kv_n[1], Z_OVER_SKAP))),
        Ror("VA-KV3", PEX_22, "KV", "FD-KV:0", "TK-VP:KV-in",
            via=(_p(X["KV"], kv0[1], Z_MATAR), _p(X["KV"], _VP["KV-in"][1], Z_MATAR),
                 _p(_VP["KV-in"][0], _VP["KV-in"][1], Z_MATAR))),
        Ror("VA-VV1", PEX_22, "VV", "TK-VP:VV-ut", "FD-VV:0",
            via=(_p(_VP["VV-ut"][0], _VP["VV-ut"][1], Z_MATAR), _p(X["VV"], _VP["VV-ut"][1], Z_MATAR),
                 _p(X["VV"], vv0[1], Z_MATAR))),
    ]


def till_underfordelaren(uf: str, inlopp: Vek) -> Ror:
    """Kallvattnet från vattenmätaren till underfördelarens stam (utgång 0): upp längs väggen och längs den i stammens
    höjd."""
    x, y, _ = _VM["uf1"]
    return Ror(f"{uf}-KV", PEX_22, "KV", "TK-VM:uf1", f"{uf}-KV:0",
               via=(_p(x, y, inlopp[2]), _p(inlopp[0], y, inlopp[2])))


def till_tappstallet_under_plattan(t: Tappstalle) -> Ror:
    """Kallvattnet från vattenmätaren till ett tappställe i källaren (DIREKT): ned genom bottenplattan vid V14, under
    den till tappställets vägg och upp i väggens cellplast bakom gipsen till dosan."""
    x, y, z = _VM["th2"]
    a = anslutning(t, "KV")
    v = i_vaggen(t.lage, a)
    vy = v[1] + mellan_jarnen([(v[0], v[1])], Z_UNDER, Z_GOLV, PEM_20.yttre / 2, langs=(0.0, 1.0))[1]
    zo = z + OVER_MATAREN["th2"]
    return Ror(f"{t.id}-KV", PEM_20, "KV", "TK-VM:th2", t.id,
               via=(_p(x, y, zo), _p(x, Y_NED["th2"], zo), _p(x, Y_NED["th2"], Z_UNDER),
                    _p(v[0], Y_NED["th2"], Z_UNDER), _p(v[0], vy, Z_UNDER), _p(v[0], vy, a[2]), _p(v[0], v[1], a[2])))
