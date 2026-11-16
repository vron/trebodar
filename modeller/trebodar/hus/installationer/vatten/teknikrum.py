"""Tappvattnet i teknikrummet: fördelarna i fördelarskåpet (..teknikrum.FORDELARSKAP, högt och smalt på V3), rörens
ordning från fördelarna, stråken i mellanbjälklaget, rören under bottenplattan till källarens tappställen och
matarledningarna.

- Fördelarna, två par (användarens kommentar): upptill till mellanbjälklaget (FD-KV, FD-VV, utgångarna uppåt) och
  nedtill till källarens tappställen (FD-KVN, FD-VVN, utgångarna nedåt). Varmvattnets stam bakom och kallvattnets
  framför; varje rör har en egen fil, c/c 50 längs V3 från väster, och utgångarna sitter i sina rörs filer.
- Mellanbjälklaget: rören går upp ur skåpets ovansida rakt in i bjälklaget mellan underkantsnätets järn och vidare i en
  nivå utan att korsa varandra. Tappställenas ordning (ORDNING, från väster) bestämmer filerna: rören viker av åt det
  håll där deras fil ligger ytterst, ett tappställes två rör bredvid varandra, det som viker av först ytterst
  (system.py). Stråken går norrut från skåpet: S och S2 västerut söder om 1C (minst 200 mm från dess bultar) och
  smalnar av (c/c TAT, skyddsrören nästan mot varandra), norr om 1C genom 1B:s passage och i var sin passage genom 1A
  (../passager.py, #114); O österut över V19 (mellan dess lodräta järn) med varmvattnet till underfördelaren UF1
  under köket. S2 har duschen, WC:n och tvätten i badrummet (UF2 finns inte längre: huvudfördelarna räcker sedan
  källarens tappställen går under bottenplattan), S badkaret och tvättställets golvdosa.
- Källaren (användarens kommentar): rören går ned genom skåpets botten och bottenplattan mellan armeringsjärnen, under
  plattan i cellplasten under dess balkar (Z_UNDER, som huvudledningen), och upp genom plattan strax innanför
  väggen vid tappstället (golvstosar, under bänken). Mellan bottenplattans armeringsnät ryms bara golvvärmen (21 mm).
  N1 västerut längs V3 och norrut längs V21 till tvätten (KA-TM1, KA-TH1), N2 österut och norrut öster om golvbrunnen
  GB2 till det framtida badrummet (KB-DU1, KB-WC1, KB-TS1). Där en grupp viker av ligger den inre filen så att rören
  inte korsar varandra.
- Matarledningarna (#139). Servisen (PEM 32) kommer upp under köket vid V14, till vattenmätaren på väggen. Från
  mätaren går tre ledningar: kallvattnet till underfördelaren UF1 (köket, PEX 22 på väggen), huvudledningen (PEM 32
  i skyddsrör, samma dimension som servisen) ned genom bottenplattan, under den västerut i cellplasten och upp i
  teknikrummet vid V3 (TK-HL), och en klenare (PEM 20 i skyddsrör) under plattan till tvätthoet KA-TH2 i
  källarrummet, som bara har kallvatten, upp genom plattan strax innanför V15. I teknikrummet (PEX 22): huvudledningen
  längs V3 till den nedre kallvattenfördelarens inlopp, genom den och vidare upp i skåpet till den övre och därifrån
  till värmepumpens varmvattenberedare; varmvattnet från beredaren till den övre varmvattenfördelaren och vidare ned
  i skåpet till den nedre. Ledningarna till och från värmepumpen går under taket.
"""
from __future__ import annotations

import math

from shapely.geometry import Polygon, box

from trebodar.hus.grund import grund as G

from ..montering import KALLARTAK, Vek, i_vaggen, kallarvagg
from ..strak import Strak, glipa, mellan_jarnen
from ..teknikrum import FORDELARSKAP, HUVUDLEDNING, VARMEPUMP, VATTENMATARE, Z_GOLV
from .katalog import PEM_20, PEM_32, PEX_22
from .punkter import FIL, R_ROR, Z_ROR, Fordelare, Ror, Tappstalle, anslutning
from .typer import Fordelartyp

_SK = FORDELARSKAP.lage.punkt                                   # på V3:s gips, normalen norrut (−y)
Y = {"VV": _SK[1] - 25.0, "KV": _SK[1] - 95.0}                  # stammarna: varmvattnet bakom, kallvattnet framför
Z = {"VV": Z_GOLV + 1900.0, "KV": Z_GOLV + 1700.0}              # de övre (till mellanbjälklaget)
Z_NED = {"VV": Z_GOLV + 1500.0, "KV": Z_GOLV + 1300.0}          # de nedre (till källarens tappställen), strax under
#                                                                 de övre: rören går ned i skåpet (kort varmvattentid)
_X0 = _SK[0] - FORDELARSKAP.matt[0] / 2 + FIL + 40.0     # den första filen (väster): stammens ände (en fil västerut)
#                                                         40 från skåpets sida


def _forsta_fria(filer: range, z0: float, z1: float, r: float) -> float:
    """Den första filens x från _X0 österut där alla filerna går fria från järnen mellan z0 och z1."""
    for dx in range(0, 151, 5):
        try:
            mellan_jarnen([(_X0 + dx + k * FIL, y) for y in Y.values() for k in filer], z0, z1, r, langst=0.0)
        except ValueError:
            continue
        return _X0 + dx
    raise ValueError(f"inga fria filer inom 150 mm öster om {_X0:g}")


X_FIL0 = _forsta_fria(range(-1, 11), KALLARTAK, Z_ROR, R_ROR)                   # de övre: mellanbjälklagets järn
X_FIL0_NED = _forsta_fria(range(0, 2), Z_GOLV - G.H_PLATTA, Z_GOLV, 14.0)        # de nedre: bottenplattans


def _fri_ned(fil: int) -> bool:
    """Om filen går fri från bottenplattans järn rakt under skåpet (både kall- och varmvattnets rör, Ø28)."""
    try:
        mellan_jarnen([(X_FIL0_NED + fil * FIL, y) for y in Y.values()], Z_GOLV - G.H_PLATTA, Z_GOLV, 14.0, langst=0.0)
    except ValueError:
        return False
    return True


# de nedre fördelarnas filer i ordning: de som går fria från järnen (en bygel i V3:s kantbalk står i vägen för en)
FILER_NED = tuple(f for f in range(12) if _fri_ned(f))

# tappställe eller underfördelare (underfordelare.py): (stråk, stråkets ben där rören viker av; None: närmast), från
# väster; S längst västerut (badkaret viker av västerut först), sedan S2 (WC:n och tvätten innerst, duschen ytterst)
# och O österut
ORDNING: dict[str, tuple[str, int | None]] = {
    "BA-BK1": ("S", 6),             # västerut, först
    "BA-TS1": ("S", 6),             # tvättställets golvdosa vid stråkets slut
    "BA-WC1": ("S2", 6),            # österut till L9
    "BA-TM1": ("S2", 6),            # österut till L10
    "BA-DU1": ("S2", 6),            # viker av österut söder om 1A och svängen, under badrummet till nischen och L11
    "UF1": ("O", None),             # underfördelaren under köket, på V14 (bara varmvattnet: kallvattnet från mätaren)
}
# källarens tappställen från de nedre fördelarna, under bottenplattan: (grupp, ordning i gruppen) från väster
ORDNING_NED: dict[str, str] = {"KA-TM1": "N1", "KA-TH1": "N1", "KB-WC1": "N2", "KB-DU1": "N2", "KB-TS1": "N2"}

DIREKT = ("KA-TH2",)                            # tappställen med rör direkt från vattenmätaren, under bottenplattan
X_O = 13400.0                                   # O österut till underfördelaren UF1 på V14
X_O_SODER, Y_O_KOK = 10000.0, 9450.0             # O till y Y_O_KOK före köket, förbi diskmaskinens hylsa i ön och
#                                                 diskmaskinens pumpade avlopp, och till UF1:s början från det hållet
Y_O_OST = 8800.0                                # O österut från skåpet, söder om S och S2
X_V19 = 4437.0                                  # O över V19 (dess gips öster om värmepumpen + 80)
TAT = 36.0                                      # rörens avstånd i stråken efter avsmalningen (c/c): skyddsrören 25 och 28
SMAL = 350.0                                    # västerut i full bredd så långt, och avsmalningen lika långt
VAND = {"S2": 60.0, "S": 150.0}              # S och S2 viker västerut så långt söder om sin linje (filerna isär)
Y_NORR = {"S2": 8546.0, "S": 8706.0}            # S2 och S västerut söder om 1C (minst 200 mm från dess bultar) och
#                                                 genom 1B:s passage
Y_SVANG = (6800.0, 6400.0)                          # S2 och S viker av i sidled söder om 1A
X_S2, X_S = 1659.0, 1078.0                      # S2 och S söderut genom var sin passage i 1A
X_S2_SODER = 1440.0                             # S2 söder om 1A: väster om källarens elrör KA-R7 upp i bjälklaget
X_S_SODER = 1255.0                              # S söder om 1A: tvättställets rör vågrätt in i golvdosan från öster,
Y_S_SLUT = 3870.0                               # förbi tvättställets avlopp
Y_V7 = i_vaggen(kallarvagg("V7", 0.0, 0.0, 1), (0.0, 0.0, 0.0))[1] + 150.0      # S2 längs V7


def strak(mitt: dict[str, float]) -> dict[str, Strak]:
    """Stråken, med deras första sträcka genom mitten av sina filer (mitt: x per stråk), norrut från skåpet; O går
    över V19 mitt i en glipa mellan väggens lodräta järn."""
    y0, k = Y["VV"] + 100.0, TAT / FIL
    y_o = glipa("V19", Z_ROR, Y_O_OST)

    def vasterut(id_: str, *resten: tuple[float, float]) -> Strak:
        """Norrut från skåpet, västerut i full bredd och avsmalnande diagonalt till stråkets linje."""
        x, y = mitt[id_], Y_NORR[id_]
        p = ((x, y0), (x, y + VAND[id_]), (x - SMAL, y + VAND[id_]), (x - 2 * SMAL, y), *resten)
        return Strak(id_, p, (1.0, 1.0) + (k,) * (len(p) - 3))
    return {s.id: s for s in (
        Strak("O", ((mitt["O"], y0), (mitt["O"], Y_O_OST), (X_V19, Y_O_OST), (X_V19, y_o), (X_O_SODER, y_o),
                    (X_O_SODER, Y_O_KOK), (X_O, Y_O_KOK))),
        vasterut("S2", (X_S2, Y_NORR["S2"]), (X_S2, Y_SVANG[0]), (X_S2_SODER, Y_SVANG[1]), (X_S2_SODER, Y_V7),
                 (3800.0, Y_V7)),
        vasterut("S", (X_S, Y_NORR["S"]), (X_S, Y_SVANG[0]), (X_S_SODER, Y_SVANG[1]), (X_S_SODER, Y_S_SLUT)),
    )}


def rata_horn() -> Polygon:
    """Där rörens hörn lämnas räta: vid skåpet, där stråken viker västerut strax norr om utgångarna (svepen ryms inte
    mellan utgångarna och 1C:s bultar)."""
    return box(_SK[0] - 400.0, Y_NORR["S2"] + VAND["S2"] - 120.0, _SK[0] + 400.0, _SK[1] + 100.0)


def fordelare(media: str, typ: Fordelartyp, filer: tuple[int, ...], ned: bool = False) -> Fordelare:
    """Fördelaren för media med utgångarna i filerna (längs V3 österut från X_FIL0); ned: den nedre (källaren)."""
    return Fordelare(f"FD-{media}" + ("N" if ned else ""), typ, media,
                     (X_FIL0_NED if ned else X_FIL0, Y[media], (Z_NED if ned else Z)[media]), (1.0, 0.0, 0.0), filer)


_VP, _VM, _HL = VARMEPUMP.anslutningar, VATTENMATARE.anslutningar, HUVUDLEDNING.anslutningar
Z_MATAR = _VP["VV-ut"][2] + 40.0                # matarledningarna över värmepumpen, under taket
# under bottenplattan (#139): ledningarna i skyddsrör i cellplasten under plattans balkar (Z_UNDER), bredvid
# varandra; ned genom plattan vid V14 norr om mätaren, mellan armeringsjärnen (flyttade längs väggen)
Z_UNDER = Z_GOLV - G.H_BALK - 50.0
OVER_MATAREN = {"ut": 80.0, "th2": 160.0}        # ledningarna vänder så högt över mätarens anslutningar
Z_HL = Z_GOLV + 150.0                           # huvudledningen längs V3 till den nedre fördelaren


def _ned(namn: str, onskat: float, r: float) -> float:
    """Där ledningen går ned genom bottenplattan vid V14 (y), nära onskat och mellan järnen."""
    x = _VM[namn][0]
    return onskat + mellan_jarnen([(x, onskat)], Z_UNDER, Z_GOLV, r, langs=(0.0, 1.0))[1]


Y_NED = {"ut": _ned("ut", _HL["in"][1], PEM_32.yttre / 2), "th2": _ned("th2", _HL["in"][1] - 80.0, PEM_20.yttre / 2)}


def _p(x: float, y: float, z: float) -> Vek:
    return (x, y, z)


def matarledningar(fd: dict[str, Fordelare]) -> list[Ror]:
    """Matarledningarna: servisen till vattenmätaren, huvudledningen under bottenplattan till teknikrummet och längs
    V3 till den nedre kallvattenfördelarens inlopp (östra änden), genom den och upp i skåpet till den övre (västra
    änden), därifrån till värmepumpens beredare, och varmvattnet från beredaren till den övre varmvattenfördelaren
    (östra änden), genom den och ned i skåpet till den nedre (västra änden)."""
    kvn, kv, vv, vvn = fd["KVN"], fd["KV"], fd["VV"], fd["VVN"]
    kvn_in, kvn_ut = kvn.utgang(kvn.utgangar + 1), kvn.utgang(0)
    kv_in, kv_ut = kv.utgang(0), kv.utgang(kv.utgangar + 1)
    vv_in, vv_ut = vv.utgang(vv.utgangar + 1), vv.utgang(0)
    vvn_in = vvn.utgang(0)
    xm, ym, zm = _VM["ut"]
    xh, yh, _ = _HL["in"]
    z_kv, z_vv = Z_MATAR, Z_MATAR + 50.0                        # till och från beredaren, över värmepumpen
    return [
        Ror("VA-KV1", PEM_32, "KV", "TK-SV:ut", "TK-VM:in"),
        Ror("VA-KV2", PEM_32, "KV", "TK-VM:ut", "TK-HL:in",
            via=(_p(xm, ym, zm + OVER_MATAREN["ut"]), _p(xm, Y_NED["ut"], zm + OVER_MATAREN["ut"]),
                 _p(xm, Y_NED["ut"], Z_UNDER), _p(xh, Y_NED["ut"], Z_UNDER), _p(xh, yh, Z_UNDER))),
        Ror("VA-KV4", PEX_22, "KV", "TK-HL:ut", f"FD-KVN:{kvn.utgangar + 1}",
            via=(_p(xh, yh, Z_HL), _p(xh, kvn_in[1], Z_HL), _p(kvn_in[0], kvn_in[1], Z_HL))),
        Ror("VA-KV5", PEX_22, "KV", "FD-KVN:0", "FD-KV:0",
            via=(_p(kvn_ut[0], kvn_ut[1], kv_in[2]),)),
        Ror("VA-KV3", PEX_22, "KV", f"FD-KV:{kv.utgangar + 1}", "TK-VP:KV-in",
            via=(_p(kv_ut[0], kv_ut[1], z_kv), _p(_VP["KV-in"][0], kv_ut[1], z_kv),
                 _p(_VP["KV-in"][0], _VP["KV-in"][1], z_kv))),
        Ror("VA-VV1", PEX_22, "VV", "TK-VP:VV-ut", f"FD-VV:{vv.utgangar + 1}",          # rakt, kort varmvattentid
            via=(_p(_VP["VV-ut"][0], _VP["VV-ut"][1], z_vv), _p(vv_in[0], vv_in[1], z_vv))),
        Ror("VA-VV2", PEX_22, "VV", "FD-VV:0", "FD-VVN:0", via=(_p(vv_ut[0], vv_ut[1], vvn_in[2]),)),
    ]


# källarens tappställen under bottenplattan: filerna, där grupperna viker av och lägena i cellplasten
Y_N1, Y_N2 = Y["KV"] - 60.0, Y["KV"] - 120.0     # den första (södra) filen för N1 och den sista (södra) för N2:
#                                                 N2 söder om golvbrunnen GB2 (N1 går västerut, N2 österut)
X_N2 = 3950.0                                   # N2:s första (västra) fil norrut, öster om golvbrunnen GB2


def ror_under_plattan(t: Tappstalle, media: str, fd: Fordelare, utgang: int, grupp: str, k: int, n: int) -> Ror:
    """Röret från den nedre fördelarens utgång till ett tappställe i källaren: ned genom skåpets botten och plattan,
    under den i cellplasten och upp genom plattan till golvstosen. k: rörets plats i gruppen från väster (n rör).
    N1: västerut i filen Y_N1 − (k)·FIL (de östra norr om de västra) och norrut vid stosen; N2: österut i filen
    Y_N2 − (n − 1 − k)·FIL (de västra norr om de östra), norrut i X_N2 + k·FIL och vid tappställets höjd västerut eller
    österut till stosen."""
    u = fd.utgang(utgang)
    a = anslutning(t, media)
    x, y = a[0], a[1]
    x_u, y_u = u[0], u[1]
    via: list[Vek] = [_p(x_u, y_u, Z_UNDER)]
    if grupp == "N1":
        yf = Y_N1 - k * FIL
        via += [_p(x_u, yf, Z_UNDER), _p(x, yf, Z_UNDER), _p(x, y, Z_UNDER)]
    else:
        yf = Y_N2 - (n - 1 - k) * FIL
        xf = X_N2 + k * FIL
        via += [_p(x_u, yf, Z_UNDER), _p(xf, yf, Z_UNDER), _p(xf, y, Z_UNDER), _p(x, y, Z_UNDER)]
    via = [q for i, q in enumerate(via) if i == 0 or math.dist(q, via[i - 1]) > 0.5]
    return Ror(f"{t.id}-{media}", t.ror, media, f"{fd.id}:{utgang}", t.id, tuple(via))


def till_underfordelaren(uf: str, inlopp: Vek) -> Ror:
    """Kallvattnet från vattenmätaren till underfördelarens stam (utgång 0): upp längs väggen och längs den i stammens
    höjd."""
    x, y, _ = _VM["uf1"]
    return Ror(f"{uf}-KV", PEX_22, "KV", "TK-VM:uf1", f"{uf}-KV:0",
               via=(_p(x, y, inlopp[2]), _p(inlopp[0], y, inlopp[2])))


def till_tappstallet_under_plattan(t: Tappstalle) -> Ror:
    """Kallvattnet från vattenmätaren till ett tappställe i källaren (DIREKT): ned genom bottenplattan vid V14, under
    den till tappställets stos och rakt upp genom plattan strax innanför väggen (användarens kommentar)."""
    x, y, z = _VM["th2"]
    a = anslutning(t, "KV")
    zo = z + OVER_MATAREN["th2"]
    return Ror(f"{t.id}-KV", PEM_20, "KV", "TK-VM:th2", t.id,
               via=(_p(x, y, zo), _p(x, Y_NED["th2"], zo), _p(x, Y_NED["th2"], Z_UNDER),
                    _p(a[0], Y_NED["th2"], Z_UNDER), _p(a[0], a[1], Z_UNDER)))
