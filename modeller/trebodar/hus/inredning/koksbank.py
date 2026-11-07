"""Köksbänken och köksön (ärende #21): skåpen (koksskap.py) på plats, fogbrädorna mellan dem, sidorna, sparklisten,
bänkskivorna, diskhon, hällen och diskmaskinen.

Bänken är vinkelformad efter användarens skiss: längs 3NV från kökets inbyggnad till 3SV och längs 3SV västerut,
700 djup (bänkskivan Bricmate Jura 12 mm, 20 mm utanför fronterna). Hörnet är dött: bänken längs 3NV slutar vid den
korta bänkens fronter, och en fogbräda 22 × 22 står i hörnet. Längs 3NV en bräda 45 mot inbyggnaden (som kan passas
in på plats), sju lådskåp och fogbrädor 22 mitt över fogarna. Hällen (induktion 590 × 520) står i det fjärde skåpet,
mitt mellan fönstren 3NV-F4 och 3NV-F5 och under köksfläkten FF1 (som sitter mitt emellan dem); de tre skåpen
söder om den och skåpen längs 3SV är lika breda (599,1, fronterna 571,1) och de tre norr om den, mot inbyggnaden,
bredare (633,4, fronterna 605,4), så att sträckan går jämnt upp. Diskhon (undermonterad, 500 × 400) står i det andra
skåpet, över golvdosan KO-DB1 (hus/installationer/vatten/rum/kok.py). Längs 3SV tre lådskåp och en vit sida mot
rummet. Under skåpen en sparklist 90 hög, 60 mm innanför fronterna.

Ön: tre skåp med fronterna mot bänken längs 3NV och vita sidor utanför fogbrädorna, 1 000 djup, 1 100 fritt mellan
bänkskivorna och mitt för hällen (och mellan fönstren); på andra sidan är ön öppen för benen (ryggen vit). Det
nordligaste skåpet är diskmaskinen, en vanlig integrerad 60: skåpen på ön är så breda att diskmaskinens front är
standardens 596 och den går fritt mellan fogbrädorna (602), och nischen bakom är minst 600.
"""
from __future__ import annotations

from modellering import Del, Montage, Placering, box, prisma, svep

from trebodar import skelett as S
from trebodar.byggdelar.virke import fmt, virke_i_lada
from trebodar.hus.fonster_och_dorrar.oppningar import OPPNINGAR
from trebodar.hus.invandigt.lattvaggar import K_X1, K_YTA
from trebodar.hus.invandigt.skikt import INSIDA_T
from trebodar.material import ASK, BANKSKIVA, HALLGLAS, ROSTFRITT, VIT_SKIVA

from . import koksskap as K

BANK_DJUP, UTSTICK, BANK_T = 700.0, 20.0, 12.0          # bänkskivan och dess utstick utanför fronterna
FOG, BRADA = 22.0, 45.0                                 # fogbrädorna och brädan mot inbyggnaden
SIDA_T = 20.0                                           # de vita sidorna
SPARK_IN, SPARK_T = 60.0, 16.0                          # sparklisten: innanför fronterna, tjocklek
N_LANG, N_KORT = 7, 3
X_VAGG = K_X1                                           # 3NV:s insida
Y_SYD = S.YTTERVAGGAR["3SV"].origo[1] - S.T_STOMME - INSIDA_T     # 3SV:s insida
X_FRONT = X_VAGG - BANK_DJUP + UTSTICK                  # fronternas yta längs 3NV
Y_FRONT = Y_SYD - BANK_DJUP + UTSTICK                   # fronternas yta längs 3SV
# fogarna mellan skåpen (fogbrädornas mitt): längs 3NV från brädan mot inbyggnaden till hörnets fogbräda, med
# hällens skåp (det fjärde) mitt mellan fönstren 3NV-F4 och 3NV-F5; längs 3SV från hörnet västerut
_F4, _F5 = (next(o for o in OPPNINGAR["3NV"] if o.kod == k) for k in ("3NV-F4", "3NV-F5"))
Y_HALL = S.YTTERVAGGAR["3NV"].origo[1] + (_F4.u1 + _F5.u0) / 2      # mitt mellan fönstren
J0 = K_YTA + BRADA - FOG / 2
N_NORR = 3                                              # skåpen norr om hällen
P = (Y_FRONT + FOG / 2 - Y_HALL) / (N_LANG - N_NORR - 0.5)        # skåpens bredd, hällens och söder om den
P_NORR = (Y_HALL - P / 2 - J0) / N_NORR                           # skåpen norr om hällen
BREDDER_LANG = [P_NORR] * N_NORR + [P] * (N_LANG - N_NORR)
FOGAR_LANG = [J0 + sum(BREDDER_LANG[:k]) for k in range(N_LANG + 1)]
FOGAR_KORT = [X_FRONT + FOG / 2 - k * P for k in range(N_KORT + 1)]
TYPER_LANG = [K.LADSKAP, K.DISKBANKSSKAP, K.LADSKAP, K.HALLSKAP, K.LADSKAP, K.LADSKAP, K.LADSKAP]   # norrifrån
# ön: PASSAGE fritt mellan bänkskivorna, mitt för hällen, fronterna mot öster; skåpen så breda att diskmaskinens
# front är standardens (DISKMASKIN_FRONT)
PASSAGE, ON_DJUP = 1100.0, 1000.0
DISKMASKIN_FRONT = 596.0
P_ON = DISKMASKIN_FRONT + 2 * (K.T - K.OVER_SIDAN)
ON_X = X_FRONT - UTSTICK - PASSAGE - ON_DJUP / 2
ON_Y = Y_HALL
ON_LANGD = 3 * P_ON + FOG + 2 * SIDA_T
X_ON_FRONT = ON_X + ON_DJUP / 2 - UTSTICK
FOGAR_ON = [ON_Y - ON_LANGD / 2 + SIDA_T + FOG / 2 + k * P_ON for k in range(4)]
DISKHO = (500.0, 400.0, 200.0, 10.0)                    # öppningen längs bänken, tvärs, djup, godset (förenklat)
DISKHO_AVLOPP = 80.0            # avloppets mitt från hons bakre kant (insidan): bakom diskbänksskåpets lådor
HALL, HALL_T = (590.0, 520.0), 5.0                       # induktionshällen: glaset och dess tjocklek
HALL_KROPP, HALL_HAL = (520.0, 490.0, 52.0), (560.0, 490.0)   # kroppen under glaset och hålet i bänkskivan
assert P_ON - FOG >= K.DISKMASKIN[0] + 4.0, "diskmaskinen går fritt mellan fogbrädorna"
assert P_ON + FOG / 2 >= 600.0, "diskmaskinens nisch är minst 600"
# diskhons avlopp i skåpets djup (från stommens framkant), med vattenlåset Ø40 minst 40 mm bakom lådornas löpare
_Y_DISKHO_AVLOPP = (K.DJUP - K.T - DISKHO[1]) / 2 + DISKHO[1] - DISKHO_AVLOPP
assert _Y_DISKHO_AVLOPP - 20.0 - K.DISKBANKSSKAP.nl >= 40.0, "diskhons avlopp bakom lådorna"


# diskmaskinen i öns skåp O1: vattnets golvdosa och avloppets anslutning (det pumpade avloppsröret upp ur golvet) under
# maskinens bakre del, var sin sida om maskinens mitt (nås när maskinen dras ut); avloppet närmare nischens bakkant
DISKMASKIN_BAK = (100.0, 50.0)  # golvdosan och avloppet från nischens bakkant
DISKMASKIN_ISAR = 120.0         # golvdosan och avloppet från maskinens mitt


def diskmaskinens_anslutningar() -> tuple[tuple[float, float], tuple[float, float]]:
    """Diskmaskinens golvdosa för kallvattnet och avloppets anslutning i plan."""
    x = X_ON_FRONT - K.FRONT_T - K.DJUP
    y = (FOGAR_ON[0] + FOGAR_ON[1]) / 2
    return (x + DISKMASKIN_BAK[0], y + DISKMASKIN_ISAR), (x + DISKMASKIN_BAK[1], y - DISKMASKIN_ISAR)


def diskhons_avlopp() -> tuple[float, float]:
    """Diskhons avlopp i plan: i hons bakre del (DISKHO_AVLOPP), bakom diskbänksskåpets korta lådor, där vattenlåset
    står och avloppet går rakt ned genom golvet och källaren längs V14 (hus/installationer/avlopp)."""
    k = TYPER_LANG.index(K.DISKBANKSSKAP)
    x, y, _ = _lang(k).punkt((BREDDER_LANG[k] / 2, _Y_DISKHO_AVLOPP, 0.0))
    return x, y


def _lang(k: int) -> Placering:
    """Skåp k längs 3NV (norrifrån): vänster sida sett framifrån i söder, djupet österut."""
    return Placering.axlar((X_FRONT + K.FRONT_T, FOGAR_LANG[k + 1], 0.0), (0.0, -1.0, 0.0), (0.0, 0.0, 1.0))


def _kort(k: int) -> Placering:
    """Skåp k längs 3SV (österifrån): vänster sida i väster, djupet söderut."""
    return Placering.axlar((FOGAR_KORT[k + 1], Y_FRONT + K.FRONT_T, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0))


def _on(k: int) -> Placering:
    """Öns skåp k (norrifrån): vänster sida i norr, djupet västerut."""
    return Placering.axlar((X_ON_FRONT - K.FRONT_T, FOGAR_ON[k], 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))


def _bradlada(namn: str, kod: str, lada: tuple[float, float, float, float, float, float], m: Montage) -> None:
    """Lodrät bräda av ask (fibrerna på höjden)."""
    d, pl = virke_i_lada(*lada, "z", ASK)
    m.lagg(Del(namn, d.form, ASK), pl, kod)


def _ytan(pl: Placering, x0: float, x1: float, y0: float, y1: float) -> list[tuple[float, float]]:
    """Rektangeln (x0..x1, y0..y1) i skåpets system som plan i huset."""
    return [pl.punkt((x, y, 0.0))[:2] for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]


def _diskho(pl: Placering, bredd: float) -> tuple[Montage, list[tuple[float, float]]]:
    """Diskhon under bänkskivan mitt i skåpet (bredd) och blandaren bakom, och hålet i bänkskivan."""
    b, d, h, t = DISKHO
    x0, y0 = (bredd - b) / 2, (K.DJUP - K.T - d) / 2
    m = Montage("Diskho", beskrivning="Diskho av rostfritt stål, undermonterad, och blandare", produkt="DISKHO")
    ho = box(x0 - t, x0 + b + t, y0 - t, y0 + d + t, K.Z_TOPP - h, K.Z_TOPP) - box(x0, x0 + b, y0, y0 + d,
                                                                                    K.Z_TOPP - h + t, K.Z_TOPP + 1.0)
    m.lagg(Del(f"Diskho {fmt(b)}×{fmt(d)}", ho, ROSTFRITT), pl, "DISKHO")
    xm, yb, z = bredd / 2, y0 + d + t + 40.0, K.Z_TOPP + BANK_T
    pip = svep([pl.punkt(q) for q in ((xm, yb, z), (xm, yb, z + 300.0), (xm, y0 + d / 2, z + 300.0),
                                      (xm, y0 + d / 2, z + 230.0))], 12.0, 40.0)
    m.lagg(Del("Blandare", pip, ROSTFRITT), Placering(), "BLANDARE")
    return m, _ytan(pl, x0, x0 + b, y0, y0 + d)


def _hall(pl: Placering, bredd: float) -> tuple[Montage, list[tuple[float, float]]]:
    """Induktionshällen på bänkskivan mitt i skåpet (bredd), med kroppen i hålet, och hålet i bänkskivan."""
    (b, d), (kb, kd, kh), (hb, hd) = HALL, HALL_KROPP, HALL_HAL
    x0, y0 = (bredd - b) / 2, (K.DJUP - K.T - d) / 2
    kx, ky = (bredd - kb) / 2, y0 + (d - kd) / 2
    hx, hy = (bredd - hb) / 2, y0 + (d - hd) / 2
    z = K.Z_TOPP + BANK_T
    m = Montage("Häll", beskrivning="Induktionshäll 60, ytmonterad", produkt="HALL")
    m.lagg(Del(f"Induktionshäll {fmt(b)}×{fmt(d)}", box(x0, x0 + b, y0, y0 + d, z, z + HALL_T), HALLGLAS), pl, "HALL")
    m.lagg(Del(f"Hällens kropp {fmt(kb)}×{fmt(kd)}", box(kx, kx + kb, ky, ky + kd, z - kh, z), HALLGLAS), pl,
           "HALL-KROPP")
    return m, _ytan(pl, hx, hx + hb, hy, hy + hd)


def bank() -> Montage:
    """Bänken längs 3NV och 3SV: skåpen, fogbrädorna, brädan mot inbyggnaden, den vita sidan, sparklisten,
    bänkskivan, diskhon och hällen."""
    m = Montage("Bänken", beskrivning="Köksbänken längs 3NV och 3SV: lådskåp, fronter av fräst ask, bänkskiva Bricmate "
                                     "Jura 12")
    z0, z1 = K.SOCKEL, K.Z_TOPP - K.SPEL
    halen = []
    for k, (typ, bredd) in enumerate(zip(TYPER_LANG, BREDDER_LANG)):
        pl = _lang(k)
        m.lagg(K.skap(f"B{k + 1}", typ, bredd), pl)
        if typ is K.DISKBANKSSKAP:
            ho, hal = _diskho(pl, bredd)
            m.lagg(ho)
            halen.append(hal)
        if typ is K.HALLSKAP:
            hall, hal = _hall(pl, bredd)
            m.lagg(hall)
            halen.append(hal)
    for k in range(N_KORT):
        m.lagg(K.skap(f"B{N_LANG + k + 1}", K.LADSKAP, P), _kort(k))
    xf, xs = X_FRONT, X_FRONT + K.FRONT_T
    yf, ys = Y_FRONT, Y_FRONT + K.FRONT_T
    _bradlada(f"Bräda ask {fmt(BRADA)}×{fmt(K.FRONT_T)} mot inbyggnaden", "B-BRADA",
              (xf, xs, K_YTA, J0 + FOG / 2, z0, z1), m)
    for i, j in enumerate(FOGAR_LANG[1:], start=1):
        _bradlada(f"Fogbräda ask {fmt(FOG)}×{fmt(K.FRONT_T)}", f"B-FOG{i}", (xf, xs, j - FOG / 2, j + FOG / 2, z0, z1), m)
    for i, j in enumerate(FOGAR_KORT[1:], start=N_LANG + 1):
        _bradlada(f"Fogbräda ask {fmt(FOG)}×{fmt(K.FRONT_T)}", f"B-FOG{i}", (j - FOG / 2, j + FOG / 2, yf, ys, z0, z1), m)
    xv = FOGAR_KORT[-1] - FOG / 2                          # den vita sidan mot rummet, utanför den sista fogbrädan
    m.lagg(Del(f"Sida vit {fmt(SIDA_T)}", box(xv - SIDA_T, xv, yf, Y_SYD, 0.0, K.Z_TOPP), VIT_SKIVA), Placering(),
           "B-SIDA")
    # sparklisten: längs 3NV från inbyggnaden till listen längs 3SV, som går till den vita sidan
    xk, yk = xf + SPARK_IN, yf + SPARK_IN
    for kod, lada in (("B-SPARK1", (xk, xk + SPARK_T, K_YTA, yk, 0.0, K.SOCKEL)),
                      ("B-SPARK2", (xv, xk + SPARK_T, yk, yk + SPARK_T, 0.0, K.SOCKEL))):
        d, pl = virke_i_lada(*lada, "x" if kod == "B-SPARK2" else "y", ASK)
        m.lagg(Del(f"Sparklist ask {fmt(SPARK_T)}", d.form, ASK), pl, kod)
    kontur = [(xf - UTSTICK, K_YTA), (X_VAGG, K_YTA), (X_VAGG, Y_SYD), (xv - SIDA_T, Y_SYD),
              (xv - SIDA_T, yf - UTSTICK), (xf - UTSTICK, yf - UTSTICK)]
    m.lagg(Del(f"Bänkskiva Bricmate Jura {fmt(BANK_T)}", prisma(kontur, BANK_T, halen, z0=K.Z_TOPP), BANKSKIVA,
               produkt="BANKSKIVA"), Placering(), "B-SKIVA")
    return m


def on() -> Montage:
    """Ön: diskmaskinen och två lådskåp, fogbrädorna, de vita sidorna och ryggen, sparklisten och bänkskivan."""
    m = Montage("Ön", beskrivning="Köksön: diskmaskin och två lådskåp mot bänken, öppen för benen på andra sidan")
    m.lagg(K.diskmaskin("O1", P_ON), _on(0))
    for k in (1, 2):
        m.lagg(K.skap(f"O{k + 1}", K.LADSKAP, P_ON), _on(k))
    z0, z1 = K.SOCKEL, K.Z_TOPP - K.SPEL
    xs, xf = X_ON_FRONT - K.FRONT_T, X_ON_FRONT
    for i, j in enumerate(FOGAR_ON):
        _bradlada(f"Fogbräda ask {fmt(FOG)}×{fmt(K.FRONT_T)}", f"O-FOG{i + 1}", (xs, xf, j - FOG / 2, j + FOG / 2, z0, z1), m)
    xb = xs - K.DJUP                                       # skåpens rygg
    xv = ON_X - ON_DJUP / 2                                # bänkskivans västra kant
    y0, y1 = FOGAR_ON[0] - FOG / 2, FOGAR_ON[-1] + FOG / 2
    for kod, (a, b) in (("O-SIDA1", (y0 - SIDA_T, y0)), ("O-SIDA2", (y1, y1 + SIDA_T))):
        m.lagg(Del(f"Sida vit {fmt(SIDA_T)}", box(xv, xf, a, b, 0.0, K.Z_TOPP), VIT_SKIVA), Placering(), kod)
    m.lagg(Del(f"Rygg vit {fmt(SIDA_T)}", box(xb - SIDA_T, xb, y0, y1, 0.0, K.Z_TOPP), VIT_SKIVA), Placering(), "O-RYGG")
    d, pl = virke_i_lada(xf - SPARK_IN - SPARK_T, xf - SPARK_IN, y0, y1, 0.0, K.SOCKEL, "y", ASK)
    m.lagg(Del(f"Sparklist ask {fmt(SPARK_T)}", d.form, ASK), pl, "O-SPARK")
    m.lagg(Del(f"Bänkskiva Bricmate Jura {fmt(BANK_T)}",
               box(xv, xf + UTSTICK, y0 - SIDA_T, y1 + SIDA_T, K.Z_TOPP, K.Z_TOPP + BANK_T), BANKSKIVA,
               produkt="BANKSKIVA"), Placering(), "O-SKIVA")
    return m
