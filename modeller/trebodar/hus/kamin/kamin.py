"""Kaminen (#102, #109): Rais 600:3 (glas på tre sidor) i en murad, putsad och kalkad skorsten i allrummet, mot väggen
2C mitt under nocken, från golvet till halva höjden (Z_MUR), och en isolerad skorsten därifrån genom 2C, garderoben och
taket.

Insatsen (Rais 600:3, installationsmanualen): 678 × 610 × 402 (bredd, höjd, djup), frontram 684 × 627, glas framtill
och på båda sidorna, rökstos Ø150 överst, 188 mm bakom fronten (antaget som för Rais 600), underkanten 450 över golvet
(golvet till dörrens underkant minst 300). Den står på två stöd av kalciumsilikat och sitter i liv med skorstenens
front och sidor, så att glaset syns på tre sidor.

Skorstenen (rum.KAMINMUR): 684 bred som insatsens ram och 1 680 hög, mot 2C:s gips, med ett lock av
lättbetong. Sidorna och baksidan är murade av
lättbetong 100 (värmemotstånd 0,9 m²K/W, minst som 50 mm Skamotec 225 enligt manualen), fronten ovanför och under
insatsen är 50 mm kalciumsilikat (Skamotec 225; tunnare än murverket, så att den isolerade skorstenen ryms över
stosen). Utsidan är kalkputs 10 på nät, kalkad i Jotun 1563 Mørk strandsand. Insatsen har 50 mm luft till baksidans murverk (manualen: avståndet
till skivorna 50) och ryms i hålet (minst 678 × 615 × 375); hålet är 2 mm större än ramen runt om, eftersom stålet
utvidgar sig. Konvektionsöppningar i sidorna (inte i fronten, #109): 320 cm² under och 550 cm² över insatsen (minst
250 och 500), och
direkt över den övre en obrännbar plåt av kalciumsilikat 50 (manualen), 1 500 över golvet; innertaket är minst 500
över öppningen och 1 000 över dörrens överkant. Golvet är betong (mellanbjälklaget), så golvplåt behövs inte.
Möbler minst 950 framför dörren och 500 från sidoglasen.

Skorstenen är isolerad, Ø150/Ø250 rostfri (ett CE-märkt systemskorsten med 50 mm deklarerat avstånd till brännbart,
G50), ända ned till stosen (manualen): lodrätt till Z_BOJ och i en enda förskjutning 45° snett bakåt genom nischens
baksida och 2C:s skikt mot garderoben (i nischen, inga reglar) in i garderoben, och lodrätt genom garderobens tak,
innertaket och taket till 1 000 mm över nocken, med regnhuv: två böjar, sotningsbar uppifrån. Genom taket går den väster
om nockbalken NB3, mellan takbalken T09 och takstolen 2C. Minst 50 mm till allt brännbart (nischens reglar, skikten,
läkten, takbalken, nockbalken); ovanför insatsen är skorstenens sidor därför kalciumsilikat 50 i stället för lättbetong.
Nockbalken ligger rakt ovanför kaminen, så skorstenen kan inte gå rakt upp. I garderoben står ett skydd av gips runt
skorstenen och kanalen (HOLJE), minst 50 mm från skorstenen, med en inspektionslucka för sotaren och
brandskyddskontrollen. Hålen genom 2C:s skikt, garderobens tak, innertaket, isoleringen och taket skärs i hus.py.

Förbränningsluften (Rais AirSystem): flexslang Ø100 från anslutningen under insatsen bakåt under den till utrymmet
bakom insatsen, och därifrån en isolerad kanal Ø100/Ø140 upp bakom insatsen och samma väg som skorstenen under den,
genom 2C och garderoben, lodrätt genom taket med huv väster om skorstenen; därför är skorstenen 700 djup och inte
560.
"""
from __future__ import annotations

import math

from modellering import Del, Form, Kapad, Material, Montage, Placering, box, cylinder

from trebodar import skelett as S
from trebodar.byggdelar import taklager as L
from trebodar.byggdelar.ror import ror, stang
from trebodar.hus.invandigt.skikt import innertak_vid
from trebodar.hus.rum import KAMINMUR
from trebodar.material import GIPS, GLAS, KALCIUMSILIKAT, KALKPUTS, KAMIN, LATTBETONG, ROSTFRITT

# insatsen (Rais 600:3, installationsmanualen)
KROPP = (678.0, 392.0, 610.0)               # bredd, djup bakom ramen, höjd
RAM = (684.0, 627.0, 10.0)                  # frontram: bredd, höjd, tjocklek
GLASET = (590.0, 470.0)                     # framtill (antaget)
SIDOGLAS = (290.0, 470.0)                   # på sidorna: längd bakåt, höjd (antaget)
STOS_D, STOS_FRAN_FRONT, STOS_H = 150.0, 188.0, 40.0
VAGG_T = 5.0                                # kroppens plåt
Z_INSATS = 450.0                            # kroppens underkant över golvet
SPEL = 2.0                                  # runt ramen i hålet
# skorstenen
MX0, MY0, MX1, MY1 = KAMINMUR.bounds        # putsens utsida; MY0 är 2C:s yta mot allrummet
X_MITT = (MX0 + MX1) / 2
PUTS, MUR, KS_T = 10.0, 100.0, 50.0         # kalkputs, lättbetong, kalciumsilikat
BAK = KS_T                                  # baksidan mot 2C: kalciumsilikat 50 (Rais: mot brännbar vägg)
LUFT_BAK = 50.0                             # luften mellan insatsen och baksidan (Rais: 50)
Y_FRONT = MY1                               # insatsens front i liv med putsen
# konvektionsöppningarna i skorstenens sidor, en på varje sida (#109: inte i fronten): längd längs sidan, höjd
KONV_UNDER, KONV_OVER = (200.0, 80.0), (250.0, 110.0)    # 2 × 160 = 320 och 2 × 275 = 550 cm² (minst 250 och 500)
Z_KONV_UNDER = 250.0
Y_KONV = 6080.0                             # öppningarnas bakre kant (i skorstenens synliga del, framför 2C)
H_KASSE = 1500.0                            # plåten över den övre konvektionsöppningen
STOD_B = 60.0
STOD_IN = 60.0                              # stöden så långt in från sidorna: luften från de nedre öppningarna
# rökröret och skorstenen
SKORSTEN_D, SKORSTEN_INRE = 250.0, 150.0
FRI = 50.0                                  # avstånd till brännbart vid genomföringen
Z_MUR = 1680.0                              # skorstenens överkant: så lågt som skorstenen genom nischen tillåter (#109)
Z_BOJ = 1110.0                              # skorstenen svänger 45° snett bakåt, genom nischen in i garderoben
Y_GARDEROB = 5710.0                         # förbränningsluftens kanal i garderoben
X_SK, Y_SK = 6635.0, 5635.0                 # och lodrätt genom taket väster om nockbalken NB3 (50 till trä), i facket
#                                            mellan takbalken T09 (y 5 460) och takstolen 2C (5 905), 50 till trä
Z_SIDA = 1071.0                             # sidornas murverk upp hit (hålets överkant); ovanför kalciumsilikat 50
OVER_NOCK = 1000.0                          # mynningen över nocken, som bygglovets fasadritning 205 (1,0 m över taket)
# förbränningsluften
LUFT_D, LUFT_FRAN_FRONT = 100.0, 122.0      # flexslangen och anslutningen under insatsen (bakom fronten)
LUFT_ISOL = 20.0                            # kanalens isolering
LUFT_Z = 200.0                              # slangen under insatsen
X_SLANG, Y_SLANG = 6880.0, 5800.0          # slangen rakt bakåt under insatsen, genom 2C in i garderoben
X_LUFT, Y_LUFT = 6275.0, Y_GARDEROB         # och lodrätt genom taket väster om skorstenen
LUFT_FRI = 5.0                              # hålen runt kanalen
HUV_OVER = 300.0                            # kanalens ände över taket, under huven

assert abs(MY0 - S.INNERVAGGAR["2C"].origo[1]) < 0.5, "i 2C:s nisch, mot skikten på garderobens sida"
assert abs(MX1 - MX0 - RAM[0]) < 0.5, "skorstenen är lika bred som insatsens ram"
assert abs(X_MITT - S.BALKAR["NB3"].x) < 0.5, "kaminen mitt under nocken (#109)"
assert abs(MY1 - MY0 - (BAK + LUFT_BAK + KROPP[1] + RAM[2])) < 0.5, "skorstenen så grund som insatsen tillåter (#109)"


def _z_tak(x: float) -> float:
    """Takplåtens överkant i nocken (mittre huskroppen)."""
    return S.TAKFALL["2SO"].z_overkant(x) + L.PLAT[1] / S.COS


def _innertak_vid(x: float, y: float, r: float = 0.0) -> float:
    """Innertakets underkant vid (x, y), den lägsta inom avståndet r (taket lutar)."""
    return min(innertak_vid(x + dx, y + dy) for dx in (-r, 0.0, r) for dy in (-r, 0.0, r))


def genomforing() -> tuple[Form, tuple[float, float, float, float, float, float]]:
    """Hålet för skorstenen genom innertaket, isoleringen och taket, med lådan (för genomforing.genomfor)."""
    r = SKORSTEN_D / 2 + FRI
    z0, z1 = _innertak_vid(X_SK, Y_SK, r) - 2.0, _z_tak(S.HUSKROPPAR[2].nock) + OVER_NOCK + 20.0
    return cylinder(r, z1 - z0, (X_SK, Y_SK, z0)), (X_SK - r, Y_SK - r, z0, X_SK + r, Y_SK + r, z1)


def _z_luft_ut() -> float:
    """Kanalens ände över taket."""
    return _z_tak(X_LUFT + LUFT_D / 2 + LUFT_ISOL) + HUV_OVER


def luftkanalens_hal() -> tuple[Form, tuple[float, float, float, float, float, float]]:
    """Hålet för förbränningsluftens kanal genom innertaket, isoleringen och taket (för genomforing.genomfor)."""
    r = LUFT_D / 2 + LUFT_ISOL + LUFT_FRI
    z0, z1 = _innertak_vid(X_LUFT, Y_LUFT, r) - 2.0, _z_luft_ut() + 20.0
    return cylinder(r, z1 - z0, (X_LUFT, Y_LUFT, z0)), (X_LUFT - r, Y_LUFT - r, z0, X_LUFT + r, Y_LUFT + r, z1)


def _luftvag() -> list[tuple[float, float, float]]:
    """Förbränningsluftens flexslang: från anslutningen under insatsen till kanalen bakom insatsen."""
    y = Y_FRONT - LUFT_FRAN_FRONT
    return [(X_MITT, y, Z_INSATS), (X_MITT, y, LUFT_Z), (X_SLANG, y - 150.0, LUFT_Z),
            (X_SLANG, Y_SLANG + LUFT_D / 2 + LUFT_ISOL, LUFT_Z)]                     # in i kanalens ände


def skorstenens_vag() -> list[tuple[float, float, float]]:
    """Den isolerade skorstenens mittlinje: från rökstosen lodrätt, i en enda förskjutning 45° snett bakåt genom
    nischen och 2C:s skikt in i garderoben (två böjar, sotningsbar uppifrån) och lodrätt genom taket."""
    ys = Y_FRONT - STOS_FRAN_FRONT
    zt = Z_INSATS + KROPP[2] + STOS_H
    b = (X_SK, Y_SK, Z_BOJ + math.hypot(X_MITT - X_SK, ys - Y_SK))
    return [(X_MITT, ys, zt), (X_MITT, ys, Z_BOJ), b, (X_SK, Y_SK, _z_tak(S.HUSKROPPAR[2].nock) + OVER_NOCK)]


def kanalens_vag() -> list[tuple[float, float, float]]:
    """Förbränningsluftens isolerade kanal: från slangens ände i garderoben längs golvet och lodrätt genom garderobens
    tak och taket."""
    return [(X_SLANG, Y_SLANG, LUFT_Z), (X_LUFT, Y_LUFT, LUFT_Z), (X_LUFT, Y_LUFT, _z_luft_ut())]


def genomforingar() -> list[tuple[Form, tuple[float, float, float, float, float, float], tuple[str, ...]]]:
    """Hålen för skorstenen och kanalen genom 2C:s skikt och isolering och garderobens tak (de sneda delarna, med
    avståndet FRI till brännbart), med lådan och montagen de skär (hus.py)."""
    ut: list[tuple[Form, tuple[float, float, float, float, float, float], tuple[str, ...]]] = []
    sv, lv = skorstenens_vag(), _luftvag()
    z_tak = 2145.0                                               # garderobens tak (inredning/garderob.py)
    rs, rl = SKORSTEN_D / 2 + FRI + 10.0, LUFT_D / 2 + LUFT_FRI      # 10 mm marginal mot nätets fasetter
    for a, b, r in ((sv[1], sv[2], rs), ((sv[2][0], sv[2][1], z_tak - 200.0), (sv[2][0], sv[2][1], z_tak + 200.0), rs),
                    (lv[2], lv[3], rl), ((X_LUFT, Y_LUFT, z_tak - 200.0), (X_LUFT, Y_LUFT, z_tak + 200.0),
                                         LUFT_D / 2 + LUFT_ISOL + LUFT_FRI)):
        lo = [min(a[i], b[i]) - r * 1.5 for i in range(3)]
        hi = [max(a[i], b[i]) + r * 1.5 for i in range(3)]
        ut.append((stang(a, b, 2 * r), (lo[0], lo[1], lo[2], hi[0], hi[1], hi[2]),
                   ("Invändigt", "Isolering", "Inredning")))
    return ut


def _halet() -> Form:
    """Hålet för insatsen genom fronten och sidorna."""
    zm = Z_INSATS + KROPP[2] / 2
    return box(MX0 - 1.0, MX1 + 1.0, Y_FRONT - RAM[2] - KROPP[1] - SPEL, Y_FRONT + 1.0, zm - RAM[1] / 2 - SPEL,
               zm + RAM[1] / 2 + SPEL)


def _konvektion() -> list[Form]:
    """Konvektionsöppningarna genom sidorna (murverket och putsen), under och över insatsen."""
    ut: list[Form] = []
    for (b, h), z in ((KONV_UNDER, Z_KONV_UNDER), (KONV_OVER, H_KASSE - KS_T - KONV_OVER[1] - 50.0)):
        for x0, x1 in ((MX0 - 1.0, MX0 + PUTS + MUR + 1.0), (MX1 - PUTS - MUR - 1.0, MX1 + 1.0)):
            ut.append(box(x0, x1, Y_KONV, Y_KONV + b, z, z + h))
    return ut


def _upp(x0: float, x1: float, y0: float, y1: float, z1: float = Z_MUR) -> Form:
    """Lådan från golvet upp till den murade delens överkant."""
    return box(x0, x1, y0, y1, 0.0, z1)


def _ror_genom(vag: list[tuple[float, float, float]], d: float) -> Form:
    """Hålet för röret (dess sneda del bakåt) genom murverket."""
    return stang(vag[1], vag[2], d + 20.0)


def _skorstenen(m: Montage) -> None:
    """Murverket, fronten av kalciumsilikat, putsen, plåten över konvektionsöppningen och stöden under insatsen."""
    hal = _halet()
    konv = _konvektion()
    ix0, ix1 = MX0 + PUTS + MUR, MX1 - PUTS - MUR             # insidan mellan sidorna
    iu0, iu1 = MX0 + PUTS + KS_T, MX1 - PUTS - KS_T           # ovanför insatsen (tunnare sidor: skorstenen ryms)
    yf = Y_FRONT - PUTS                                       # frontens utsida (under putsen)
    konv_v: Form = konv[0] | konv[2]
    konv_o: Form = konv[1] | konv[3]
    delar: list[tuple[str, str, Form, Material]] = [
        ("MUR-V", "Murverk lättbetong 100, västra sidan", _upp(MX0 + PUTS, ix0, MY0, yf, Z_SIDA) - hal - konv_v,
         LATTBETONG),
        ("MUR-O", "Murverk lättbetong 100, östra sidan", _upp(ix1, MX1 - PUTS, MY0, yf, Z_SIDA) - hal - konv_o,
         LATTBETONG),
        ("SIDA-V", f"Sida kalciumsilikat {KS_T:g} ovanför insatsen, västra", box(MX0 + PUTS, iu0, MY0, yf, Z_SIDA, Z_MUR)
         - konv_v - _ror_genom(skorstenens_vag(), SKORSTEN_D), KALCIUMSILIKAT),
        ("SIDA-O", f"Sida kalciumsilikat {KS_T:g} ovanför insatsen, östra", box(iu1, MX1 - PUTS, MY0, yf, Z_SIDA, Z_MUR)
         - konv_o - _ror_genom(skorstenens_vag(), SKORSTEN_D), KALCIUMSILIKAT),
        ("BAK", f"Baksida kalciumsilikat {BAK:g}", _upp(ix0, ix1, MY0, MY0 + BAK)
         - _ror_genom(skorstenens_vag(), SKORSTEN_D) - stang(_luftvag()[2], _luftvag()[3], LUFT_D + 20.0),
         KALCIUMSILIKAT),
        ("LOCK", f"Lock kalciumsilikat {KS_T:g}", box(iu0, iu1, MY0 + BAK, yf - KS_T, Z_MUR - KS_T, Z_MUR),
         KALCIUMSILIKAT),
    ]
    front: Form = (box(ix0, ix1, yf - KS_T, yf, 0.0, Z_SIDA) | box(iu0, iu1, yf - KS_T, yf, Z_SIDA, Z_MUR)) - hal
    delar.append(("FRONT", f"Front kalciumsilikat {KS_T:g}", front, KALCIUMSILIKAT))
    puts: Form = (_upp(MX0, MX1, yf, Y_FRONT, Z_MUR + PUTS) | _upp(MX0, MX0 + PUTS, MY0, yf, Z_MUR + PUTS)
                  | _upp(MX1 - PUTS, MX1, MY0, yf, Z_MUR + PUTS) | box(MX0, MX1, MY0, Y_FRONT, Z_MUR, Z_MUR + PUTS)) - hal
    for k in konv:
        puts = puts - k
    delar.append(("PUTS", f"Kalkputs {PUTS:g} på nät, kalkad", puts, KALKPUTS))
    for kod, namn, form, mat in delar:
        artikel = "Skamotec 225, 50 mm" if mat is KALCIUMSILIKAT else None
        m.lagg(Del(namn, form, mat, artikel=artikel), Placering(), f"KM-{kod}")
    # plåten över den övre konvektionsöppningen, med hål för skorstenen och kanalen
    plat = box(iu0, iu1, MY0 + BAK, yf - KS_T, H_KASSE - KS_T, H_KASSE) - _ror_genom(skorstenens_vag(), SKORSTEN_D)
    m.lagg(Del(f"Plåt över konvektionsöppningen, kalciumsilikat {KS_T:g}", plat, KALCIUMSILIKAT,
               artikel="Skamotec 225, 50 mm"), Placering(), "KM-PLAT")
    yb = Y_FRONT - RAM[2] - KROPP[1]
    for i, x0 in enumerate((ix0 + STOD_IN, ix1 - STOD_IN - STOD_B), 1):
        m.lagg(Del(f"Stöd under insatsen, kalciumsilikat {STOD_B:g}", box(x0, x0 + STOD_B, yb, yf - KS_T, 0.0,
                                                                            Z_INSATS), KALCIUMSILIKAT),
               Placering(), f"KM-STOD{i}")


# skyddet runt skorstenen och kanalen i garderoben (#109): gips 13 framför dem och på sidorna, från golvet och 2C:s
# skikt till garderobens tak, minst 50 från skorstenen (dess avstånd till brännbart, G50), så att kläderna håller
# avstånd; med en inspektionslucka i fronten för sotaren och brandskyddskontrollen
HOLJE = (6100.0, 7130.0, 5440.0, 0.0)          # x0, x1, framsidans y, underkant
LUCKA = (6380.0, 6880.0, 1300.0, 2000.0)       # inspektionsluckan i fronten: x0, x1, z0, z1


def _holjet(m: Montage) -> None:
    x0, x1, yf, zb = HOLJE
    y_2c = S.INNERVAGGAR["2C"].origo[1] - 25.0                  # 2C:s gips mot sovrummet
    z_tak = 2145.0                                               # garderobens tak (inredning/garderob.py)
    t = 13.0
    lx0, lx1, lz0, lz1 = LUCKA
    for kod, namn, f in (("FRAM", "gips 13", box(x0, x1, yf, yf + t, zb, z_tak) - box(lx0, lx1, yf - 1, yf + t + 1, lz0, lz1)),
                         ("LUCKA", "inspektionslucka, gips 13", box(lx0, lx1, yf, yf + t, lz0, lz1)),
                         ("V", "gips 13", box(x0, x0 + t, yf + t, y_2c, zb, z_tak)),
                         ("O", "gips 13", box(x1 - t, x1, yf + t, y_2c, zb, z_tak))):
        m.lagg(Del(f"Skydd runt skorstenen i garderoben, {namn}", f, GIPS), Placering(), f"KM-SKYDD-{kod}")


def _insatsen(m: Montage) -> None:
    b, d, h = KROPP
    x0, x1 = X_MITT - b / 2, X_MITT + b / 2
    y1 = Y_FRONT - RAM[2]
    y0, z0 = y1 - d, Z_INSATS
    zm = z0 + h / 2
    sl, sh = SIDOGLAS
    sidoglas = [box(x, x + VAGG_T, y1 - 40.0 - sl, y1 - 40.0, zm - sh / 2, zm + sh / 2) for x in (x0, x1 - VAGG_T)]
    kropp: Form = box(x0, x1, y0, y1, z0, z0 + h) - box(x0 + VAGG_T, x1 - VAGG_T, y0 + VAGG_T, y1 + 1.0,
                                                         z0 + VAGG_T, z0 + h - VAGG_T)
    for g in sidoglas:
        kropp = kropp - g
    m.lagg(Del("Kamininsats Rais 600:3, kropp", kropp, KAMIN, artikel="Rais 600:3 (glas på tre sidor)",
               produkt="KAMIN"), Placering(), "KM-INSATS")
    rb, rh, rt = RAM
    gb, gh = GLASET
    ram = box(X_MITT - rb / 2, X_MITT + rb / 2, y1, Y_FRONT, zm - rh / 2, zm + rh / 2) - \
        box(X_MITT - gb / 2, X_MITT + gb / 2, y1 - 1.0, Y_FRONT + 1.0, zm - gh / 2, zm + gh / 2)
    m.lagg(Del("Frontram Rais 600:3", ram, KAMIN), Placering(), "KM-RAM")
    m.lagg(Del("Glas Rais 600:3, framtill", box(X_MITT - gb / 2, X_MITT + gb / 2, Y_FRONT - 4.0, Y_FRONT,
                                                 zm - gh / 2, zm + gh / 2), GLAS), Placering(), "KM-GLAS")
    for namn, g in zip("VO", sidoglas):
        m.lagg(Del("Glas Rais 600:3, sidan", g, GLAS), Placering(), f"KM-GLAS-{namn}")


def montage() -> Montage:
    m = Montage("Kamin", beskrivning="Rais 600:3 i en murad, putsad och kalkad skorsten mot 2C mitt under nocken, med "
                                     "isolerad skorsten genom garderoben och taket (#102, #109)")
    _insatsen(m)
    _skorstenen(m)
    _holjet(m)
    # rökstosen och den isolerade skorstenen från stosen
    ys = Y_FRONT - STOS_FRAN_FRONT
    zt = Z_INSATS + KROPP[2]
    m.lagg(Del(f"Rökstos Ø{STOS_D:g}", ror((X_MITT, ys, zt), (X_MITT, ys, zt + STOS_H), STOS_D, 3.0), KAMIN),
           Placering(), "KM-STOS")
    vag = skorstenens_vag()
    t = (SKORSTEN_D - SKORSTEN_INRE) / 2
    skorsten: Form = ror(vag[0], vag[1], SKORSTEN_D, t)
    for a_, b_ in zip(vag[1:], vag[2:]):
        skorsten = skorsten | ror(a_, b_, SKORSTEN_D, t)
    langd = sum(math.dist(a_, b_) for a_, b_ in zip(vag, vag[1:]))
    z_topp = vag[-1][2]
    m.lagg(Del(f"Isolerad skorsten Ø{SKORSTEN_INRE:g}/Ø{SKORSTEN_D:g} L={langd:.0f}", skorsten, ROSTFRITT,
               produkt="SKORSTEN"), Placering(), "KM-SKORSTEN")
    m.lagg(Del("Regnhuv", cylinder(SKORSTEN_D / 2 + FRI, 40.0, (X_SK, Y_SK, z_topp)), ROSTFRITT), Placering(), "KM-HUV")
    r = SKORSTEN_D / 2 + FRI
    za, zb = _z_tak(X_SK - r) - 80.0, _z_tak(X_SK + r) + 100.0
    k = (_z_tak(X_SK + 100.0) - _z_tak(X_SK)) / 100.0                   # takets lutning
    krage = Kapad(ror((X_SK, Y_SK, za), (X_SK, Y_SK, zb), 2 * r, FRI), (X_SK, Y_SK, _z_tak(X_SK) - 40.0), (k, 0.0, -1.0))
    m.lagg(Del("Takgenomföring, krage", krage, ROSTFRITT), Placering(), "KM-KRAGE")      # från 40 under takets yta
    # förbränningsluften
    vag = _luftvag()
    slang: Form = ror(vag[0], vag[1], LUFT_D, 1.0)
    for a_, b_ in zip(vag[1:], vag[2:]):
        slang = slang | ror(a_, b_, LUFT_D, 1.0)
    langd = sum(math.dist(a_, b_) for a_, b_ in zip(vag, vag[1:]))
    m.lagg(Del(f"Förbränningsluft, flexslang Ø{LUFT_D:g} L={langd:.0f}", slang, ROSTFRITT,
               artikel="Rais AirSystem, flexslang Ø100"), Placering(), "KM-LUFT")
    kv = kanalens_vag()
    dk = LUFT_D + 2 * LUFT_ISOL
    kanal: Form = ror(kv[0], kv[1], dk, LUFT_ISOL + 0.5)
    for a_, b_ in zip(kv[1:], kv[2:]):
        kanal = kanal | ror(a_, b_, dk, LUFT_ISOL + 0.5)
    zb = kv[-1][2]
    m.lagg(Del(f"Förbränningsluft, isolerad kanal Ø{LUFT_D:g}/Ø{dk:g} "
               f"L={sum(math.dist(a_, b_) for a_, b_ in zip(kv, kv[1:])):.0f}", kanal, ROSTFRITT), Placering(),
           "KM-LUFT2")
    rk = LUFT_D / 2 + LUFT_ISOL / 2                             # huven 60 över kanalens ände, på tre stag
    stag = [stang((X_LUFT + rk * math.cos(v), Y_LUFT + rk * math.sin(v), zb),
                  (X_LUFT + rk * math.cos(v), Y_LUFT + rk * math.sin(v), zb + 60.0), 8.0)
            for v in (0.0, 2 * math.pi / 3, 4 * math.pi / 3)]
    huv: Form = cylinder(dk / 2 + 40.0, 40.0, (X_LUFT, Y_LUFT, zb + 60.0))
    for st in stag:
        huv = huv | st
    m.lagg(Del("Huv för förbränningsluften, på stag", huv, ROSTFRITT), Placering(), "KM-LUFTHUV")
    rl = dk / 2 + LUFT_FRI
    m.lagg(Del("Takgenomföring för förbränningsluften, krage",
               ror((X_LUFT, Y_LUFT, _z_tak(X_LUFT - rl) - 80.0), (X_LUFT, Y_LUFT, _z_tak(X_LUFT + rl) + 100.0), 2 * rl,
                   LUFT_FRI), ROSTFRITT), Placering(), "KM-LUFTKRAGE")
    return m
