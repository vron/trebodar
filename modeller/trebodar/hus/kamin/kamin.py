"""Kaminen (#102): Rais 600:3 (glas på tre sidor) i en murad, putsad och kalkad skorsten i allrummet, mot väggen 2C
från golvet rakt upp till innertaket, och en isolerad skorsten därifrån genom taket.

Insatsen (Rais 600:3, installationsmanualen): 678 × 610 × 402 (bredd, höjd, djup), frontram 684 × 627, glas framtill
och på båda sidorna, rökstos Ø150 överst, 188 mm bakom fronten (antaget som för Rais 600), underkanten 450 över golvet
(golvet till dörrens underkant minst 300). Den står på två stöd av kalciumsilikat och sitter i liv med skorstenens
front och sidor, så att glaset syns på tre sidor.

Skorstenen (rum.KAMINMUR): 684 bred som insatsens ram och 700 djup, mot 2C:s gips. Sidorna och baksidan är murade av
lättbetong 100 (värmemotstånd 0,9 m²K/W, minst som 50 mm Skamotec 225 enligt manualen), fronten ovanför och under
insatsen är 50 mm kalciumsilikat (Skamotec 225; tunnare än murverket, så att den isolerade skorstenen ryms över
stosen). Utsidan är kalkputs 10 på nät, kalkad. Insatsen har 50 mm luft till baksidans murverk (manualen: avståndet
till skivorna 50) och ryms i hålet (minst 678 × 615 × 375); hålet är 2 mm större än ramen runt om, eftersom stålet
utvidgar sig. Konvektionsöppningar i fronten: 308 cm² under och 550 cm² över insatsen (minst 250 och 500), och
direkt över den övre en obrännbar plåt av kalciumsilikat 50 (manualen), 1 600 över golvet; innertaket är minst 500
över öppningen och 1 000 över dörrens överkant. Golvet är betong (mellanbjälklaget), så golvplåt behövs inte.
Möbler minst 950 framför dörren och 500 från sidoglasen.

Skorstenen är isolerad, Ø150/Ø250 rostfri, ända ned till stosen (manualen): 100 mm lodrätt, 45° bakåt och åt väster
och lodrätt genom plåten, innertaket och taket till 800 mm över nocken, med regnhuv. Genom taket går den i facket
mellan takstolen 2C och takbalken vid y 6 550 (50 mm till trä), nordväst om stålbandet T2SO-B05, som går snett över
facket mot nocken; därför står skorstenen med mitten i x 6 455 och inte mitt för nocken. Hålen genom innertaket,
isoleringen och taket skärs i hus.py.

Förbränningsluften (Rais AirSystem): flexslang Ø100 från anslutningen under insatsen bakåt under den till utrymmet
bakom insatsen, och därifrån en isolerad kanal Ø100/Ø140 lodrätt upp bakom insatsen, genom plåten, innertaket och
taket med huv; därför är skorstenen 700 djup och inte 560. Kanalen går öster om skorstenen, sydost om stålbandet.
"""
from __future__ import annotations

import math

from shapely.geometry import box as plan_box

from modellering import Del, Form, Kapad, Material, Montage, Placering, box, cylinder

from trebodar import skelett as S
from trebodar.byggdelar import taklager as L
from trebodar.byggdelar.ror import ror, stang
from trebodar.hus.invandigt.skikt import innertak_vid, kapad_vid_taket
from trebodar.hus.rum import KAMINMUR
from trebodar.material import GLAS, KALCIUMSILIKAT, KALKPUTS, KAMIN, LATTBETONG, ROSTFRITT

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
Y_FRONT = MY1                               # insatsens front i liv med putsen
KONV_UNDER, KONV_OVER = (440.0, 70.0), (440.0, 125.0)    # bredd, höjd (308 och 550 cm²)
Z_KONV_UNDER = 250.0
H_KASSE = 1600.0                            # plåten över den övre konvektionsöppningen
STOD_B = 60.0
# rökröret och skorstenen
SKORSTEN_D, SKORSTEN_INRE = 250.0, 150.0
FRI = 50.0                                  # avstånd till brännbart vid genomföringen
X_SK, Y_SK = 6350.0, 6365.0                 # skorstenens mitt över böjen: i facket, nordväst om stålbandet
OVER_NOCK = 800.0
# förbränningsluften
LUFT_D, LUFT_FRAN_FRONT = 100.0, 122.0      # flexslangen och anslutningen under insatsen (bakom fronten)
LUFT_ISOL = 20.0                            # kanalens isolering
LUFT_Z = 200.0                              # slangen under insatsen
X_LUFT, Y_LUFT = 6600.0, MY0 + MUR + LUFT_D / 2 + LUFT_ISOL      # kanalen bakom insatsen
LUFT_FRI = 5.0                              # hålen runt kanalen
HUV_OVER = 300.0                            # kanalens ände över taket, under huven

assert abs(MY0 - (S.INNERVAGGAR["2C"].origo[1] + S.INNERVAGGAR["2C"].tjocklek + 25.0)) < 0.5, "mot 2C:s gips"
assert abs(MX1 - MX0 - RAM[0]) < 0.5, "skorstenen är lika bred som insatsens ram"


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
    return [(X_MITT, y, Z_INSATS), (X_MITT, y, LUFT_Z), (X_LUFT, Y_LUFT, LUFT_Z), (X_LUFT, Y_LUFT, LUFT_Z + 150.0)]


def _halet() -> Form:
    """Hålet för insatsen genom fronten och sidorna."""
    zm = Z_INSATS + KROPP[2] / 2
    return box(MX0 - 1.0, MX1 + 1.0, Y_FRONT - RAM[2] - KROPP[1] - SPEL, Y_FRONT + 1.0, zm - RAM[1] / 2 - SPEL,
               zm + RAM[1] / 2 + SPEL)


def _konvektion() -> list[Form]:
    """Konvektionsöppningarna genom fronten och putsen."""
    return [box(X_MITT - b / 2, X_MITT + b / 2, Y_FRONT - PUTS - KS_T - 1.0, Y_FRONT + 1.0, z, z + h)
            for (b, h), z in ((KONV_UNDER, Z_KONV_UNDER), (KONV_OVER, H_KASSE - KS_T - KONV_OVER[1]))]


def _upp(x0: float, x1: float, y0: float, y1: float) -> Form:
    """Lådan från golvet upp till innertaket."""
    return kapad_vid_taket(box(x0, x1, y0, y1, 0.0, 6000.0), plan_box(x0, y0, x1, y1))


def _skorstenen(m: Montage) -> None:
    """Murverket, fronten av kalciumsilikat, putsen, plåten över konvektionsöppningen och stöden under insatsen."""
    hal = _halet()
    konv = _konvektion()
    ix0, ix1 = MX0 + PUTS + MUR, MX1 - PUTS - MUR             # insidan mellan sidorna
    yf = Y_FRONT - PUTS                                       # frontens utsida (under putsen)
    delar: list[tuple[str, str, Form, Material]] = [
        ("MUR-V", "Murverk lättbetong 100, västra sidan", _upp(MX0 + PUTS, ix0, MY0, yf) - hal, LATTBETONG),
        ("MUR-O", "Murverk lättbetong 100, östra sidan", _upp(ix1, MX1 - PUTS, MY0, yf) - hal, LATTBETONG),
        ("MUR-B", "Murverk lättbetong 100, baksidan", _upp(ix0, ix1, MY0, MY0 + MUR), LATTBETONG),
    ]
    front: Form = _upp(ix0, ix1, yf - KS_T, yf) - hal
    for k in konv:
        front = front - k
    delar.append(("FRONT", f"Front kalciumsilikat {KS_T:g}", front, KALCIUMSILIKAT))
    puts: Form = (_upp(MX0, MX1, yf, Y_FRONT) | _upp(MX0, MX0 + PUTS, MY0, yf) | _upp(MX1 - PUTS, MX1, MY0, yf)) - hal
    for k in konv:
        puts = puts - k
    delar.append(("PUTS", f"Kalkputs {PUTS:g} på nät, kalkad", puts, KALKPUTS))
    for kod, namn, form, mat in delar:
        artikel = "Skamotec 225, 50 mm" if mat is KALCIUMSILIKAT else None
        m.lagg(Del(namn, form, mat, artikel=artikel), Placering(), f"KM-{kod}")
    # plåten över den övre konvektionsöppningen, med hål för skorstenen och kanalen
    plat = box(ix0, ix1, MY0 + MUR, yf - KS_T, H_KASSE - KS_T, H_KASSE) \
        - cylinder(SKORSTEN_D / 2, KS_T + 2.0, (X_SK, Y_SK, H_KASSE - KS_T - 1.0)) \
        - cylinder(LUFT_D / 2 + LUFT_ISOL + LUFT_FRI, KS_T + 2.0, (X_LUFT, Y_LUFT, H_KASSE - KS_T - 1.0))
    m.lagg(Del(f"Plåt över konvektionsöppningen, kalciumsilikat {KS_T:g}", plat, KALCIUMSILIKAT,
               artikel="Skamotec 225, 50 mm"), Placering(), "KM-PLAT")
    yb = Y_FRONT - RAM[2] - KROPP[1]
    for i, x0 in enumerate((ix0, ix1 - STOD_B), 1):
        m.lagg(Del(f"Stöd under insatsen, kalciumsilikat {STOD_B:g}", box(x0, x0 + STOD_B, yb, yf - KS_T, 0.0,
                                                                            Z_INSATS), KALCIUMSILIKAT),
               Placering(), f"KM-STOD{i}")


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
    m = Montage("Kamin", beskrivning="Rais 600:3 i en murad, putsad och kalkad skorsten mot 2C, med isolerad "
                                     "skorsten genom taket (#102)")
    _insatsen(m)
    _skorstenen(m)
    # rökstosen och den isolerade skorstenen från stosen
    ys = Y_FRONT - STOS_FRAN_FRONT
    zt = Z_INSATS + KROPP[2]
    m.lagg(Del(f"Rökstos Ø{STOS_D:g}", ror((X_MITT, ys, zt), (X_MITT, ys, zt + STOS_H), STOS_D, 3.0), KAMIN),
           Placering(), "KM-STOS")
    a = (X_MITT, ys, zt + STOS_H)
    b1 = (X_MITT, ys, zt + STOS_H + 100.0)
    c = (X_SK, Y_SK, b1[2] + math.hypot(X_MITT - X_SK, ys - Y_SK))          # 45°
    assert c[2] < H_KASSE - KS_T - 50.0, "böjen ligger under plåten"
    z_topp = _z_tak(S.HUSKROPPAR[2].nock) + OVER_NOCK
    t = (SKORSTEN_D - SKORSTEN_INRE) / 2
    skorsten: Form = ror(a, b1, SKORSTEN_D, t) | ror(b1, c, SKORSTEN_D, t) | ror(c, (X_SK, Y_SK, z_topp), SKORSTEN_D, t)
    langd = math.dist(a, b1) + math.dist(b1, c) + z_topp - c[2]
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
    za, zb = vag[-1][2], _z_luft_ut()
    dk = LUFT_D + 2 * LUFT_ISOL
    m.lagg(Del(f"Förbränningsluft, isolerad kanal Ø{LUFT_D:g}/Ø{dk:g} L={zb - za:.0f}",
               ror((X_LUFT, Y_LUFT, za), (X_LUFT, Y_LUFT, zb), dk, LUFT_ISOL + 0.5), ROSTFRITT), Placering(), "KM-LUFT2")
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
