"""Kaminen: Rais 600 frontmodell (måttritning och monteringsanvisning 11-6520, rev. 12-06-2025) i öppningen i
väggen 2C (planritning 201), mot allrummet, inbyggd enligt anvisningen och med isolerad skorsten genom taket.

Insatsen: kropp 720 × 611 × 402 (stål, ihålig), frontram 758 × 627 med glas 560 × 438, rökstos Ø147 överst mitt på,
188 mm bakom fronten; underkanten 450 över golvet (antaget; dörrens underkant minst 250). Den står på två stöd av
kalciumsilikat med luft emellan.

Innbyggingskassen (anvisningen: 50 mm kalciumsilikat, Skamotec 225, mot brännbar vägg minst 1 600 × 920 × 498): kåpan
på sovrumssidan av 2C (de lätta väggarna L7, L13 och L14 med 50 mm kalciumsilikat på insidan, invandigt/vaggar.py) och
fronten i 2C:s öppning, 50 mm kalciumsilikat med hål 730 × 615 för insatsen och konvektionsöppningar 300 cm² under och
550 cm² över insatsen (minst 250 och 500). Öppningen är symmetrisk kring insatsen, så att fronten syns lika bred på
båda sidorna, och fronten är målad i väggarnas vita färg: kaminen sitter mitt i en vit vägg. Kassen är täckt med en obrännbar plåt 50 mm direkt över den övre
konvektionsöppningen, 1 600 över golvet, och skorstenens isolerade del börjar inne i kassen och går genom plåten.

Förbränningsluften (AirSystem, anvisningen: flexslang Ø100 upp till 5 m, Ø120 för 5–10 m; luftbehov minst 18 m³/h):
upp genom taket, inte genom källaren. Flexslang Ø100 från anslutningen under insatsen ned under den, genom det västra
stödet till kåpans västra del bredvid insatsen (kåpan är bredare där, rum.KAMINKAPA) och lodrätt upp genom plåten;
över plåten isolerad kanal (kall uteluft i varm kåpa ger annars kondens) bredvid skorstenen i samma fack, genom
innertaket och taket, med huv över taket. Kanalen är ca 4,7 m (hålen i innertaket, isoleringen och taket skärs i
hus.py).

Rökröret Ø150 går lodrätt 100 mm och sedan 45° till skorstenen, som står i facket mellan takbalken vid y 5 415 och
takstolen 2C. Skorstenen: isolerad, Ø150/Ø250 rostfri, från kassen till 800 mm över nocken, med regnhuv. Hålet genom
innertaket, isoleringen och taket har 50 mm avstånd till skorstenen (genomforing, skärs i husets skikt i hus.py).
"""
from __future__ import annotations

import math

from modellering import Del, Form, Montage, Placering, box, cylinder

from trebodar import skelett as S
from trebodar.byggdelar import taklager as L
from trebodar.byggdelar.ror import ror, stang
from trebodar.hus.fonster_och_dorrar.oppningar import INNEROPPNINGAR
from trebodar.hus.invandigt.skikt import innertak_vid
from trebodar.hus.rum import KAMINKAPA
from trebodar.material import GLAS, KALCIUMSILIKAT, KALCIUMSILIKAT_MALAD, KAMIN, ROSTFRITT

# insatsen (Rais 600, måttritning)
KROPP = (720.0, 402.0, 611.0)               # bredd, djup, höjd
RAM = (758.0, 627.0, 10.0)                  # frontram: bredd, höjd, tjocklek
GLASET = (560.0, 438.0)
STOS_D, STOS_FRAN_FRONT, STOS_H = 147.0, 188.0, 40.0
VAGG_T = 5.0                                # kroppens plåt
Z_INSATS = 450.0                            # underkanten över golvet (antaget)
# innbyggingskassen (anvisningen)
KS_T = 50.0                                 # kalciumsilikat
HAL = (730.0, 615.0)                        # hålet för insatsen i fronten
KONV_UNDER, KONV_OVER = (500.0, 60.0), (500.0, 110.0)    # konvektionsöppningarna: bredd, höjd (300 och 550 cm²)
Z_KONV_UNDER = 250.0                        # den nedre öppningens underkant
H_KASSE = 1600.0                            # plåten över den övre öppningen
STOD_B = 100.0                              # stöden under insatsen
_, _U0, _U1, _Z0, _Z1, _ = next(o for o in INNEROPPNINGAR if o[0] == "2C")
OPPNING = (S.INNERVAGGAR["2C"].origo[0] + _U0, S.INNERVAGGAR["2C"].origo[0] + _U1, _Z0, _Z1)   # i 2C: x0, x1, z0, z1
# läget: insatsen 50 mm från kåpans östra kalciumsilikat (väster om den är kanalen), fronten i skiktets yta mot
# allrummet
KAPA = KAMINKAPA.bounds                     # x0, y0, x1, y1 innanför de lätta väggarna
X_MITT = KAPA[2] - KS_T - 50.0 - KROPP[0] / 2
Y_FRONT = S.INNERVAGGAR["2C"].origo[1] + S.INNERVAGGAR["2C"].tjocklek + 25.0
# rökröret och skorstenen
ROR_D, ROR_T = 150.0, 1.5
SKORSTEN_D, SKORSTEN_INRE = 250.0, 150.0
FRI = 50.0                                  # avstånd till brännbart vid genomföringen
X_SK, Y_SK = 6590.0, 5710.0                 # skorstenens mitt: förbi nockbalken och dess upplagsregel, i facket
OVER_NOCK = 800.0
# förbränningsluften
LUFT_D, LUFT_FRAN_FRONT = 100.0, 122.0      # flexslangen och anslutningen under insatsen (bakom fronten)
LUFT_ISOL = 30.0                            # kanalens isolering över plåten
LUFT_Z = 200.0                              # slangen under insatsen
X_LUFT = KAPA[0] + KS_T + LUFT_D / 2 + LUFT_ISOL + 7.0     # kanalen i kåpans västra del, i skorstenens fack (y)
LUFT_FRI = 5.0                              # hålen runt kanalen
HUV_OVER = 300.0                            # kanalens ände över taket, under huven


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


def _luftvag() -> list[tuple[float, float, float]]:
    """Förbränningsluftens flexslang: från anslutningen under insatsen till plåtens överkant."""
    y = Y_FRONT - LUFT_FRAN_FRONT
    return [(X_MITT, y, Z_INSATS), (X_MITT, y, LUFT_Z), (X_LUFT, Y_SK, LUFT_Z), (X_LUFT, Y_SK, H_KASSE)]


def _z_luft_ut() -> float:
    """Kanalens ände över taket."""
    return _z_tak(X_LUFT + LUFT_D / 2 + LUFT_ISOL) + HUV_OVER


def luftkanalens_hal() -> tuple[Form, tuple[float, float, float, float, float, float]]:
    """Hålet för förbränningsluftens kanal genom innertaket, isoleringen och taket (för genomforing.genomfor)."""
    r = LUFT_D / 2 + LUFT_ISOL + LUFT_FRI
    z0, z1 = _innertak_vid(X_LUFT, Y_SK, r) - 2.0, _z_luft_ut() + 20.0
    return cylinder(r, z1 - z0, (X_LUFT, Y_SK, z0)), (X_LUFT - r, Y_SK - r, z0, X_LUFT + r, Y_SK + r, z1)


def _kasse(m: Montage) -> None:
    """Innbyggingskassens front i öppningen, plåten över den och stöden under insatsen (kåpans väggar med
    kalciumsilikat hör till de lätta väggarna)."""
    ox0, ox1, oz0, oz1 = OPPNING
    yb = Y_FRONT - KS_T                         # frontens baksida
    hb, hh = HAL
    hal_z = Z_INSATS + KROPP[2] / 2 - hh / 2
    front: Form = box(ox0, ox1, yb, Y_FRONT, oz0, oz1)
    for x0, x1, z0, z1 in ((X_MITT - hb / 2, X_MITT + hb / 2, hal_z, hal_z + hh),
                           (X_MITT - KONV_UNDER[0] / 2, X_MITT + KONV_UNDER[0] / 2, Z_KONV_UNDER,
                            Z_KONV_UNDER + KONV_UNDER[1]),
                           (X_MITT - KONV_OVER[0] / 2, X_MITT + KONV_OVER[0] / 2, H_KASSE - KS_T - KONV_OVER[1],
                            H_KASSE - KS_T)):
        front = front - box(x0, x1, yb - 1.0, Y_FRONT + 1.0, z0, z1)
    m.lagg(Del(f"Front kalciumsilikat {KS_T:g} med konvektionsöppningar, målad", front, KALCIUMSILIKAT_MALAD,
               artikel="Skamotec 225, 50 mm"), Placering(), "KM-FRONT")
    # plåten: över kåpans insida (innanför kalciumsilikaten, mot 2C bara där väggen har öppningen) och öppningen i
    # väggen, med hål för skorstenen och kanalen
    ix0, iy0, ix1 = KAPA[0] + KS_T, KAPA[1] + KS_T, KAPA[2] - KS_T
    y_vagg = S.INNERVAGGAR["2C"].origo[1]       # 2C:s sida mot sovrummet
    za, zb = H_KASSE - KS_T, H_KASSE
    plat = box(ix0, ix1, iy0, y_vagg - KS_T, za, zb) | box(max(ix0, ox0), ix1, y_vagg - KS_T, y_vagg, za, zb) \
        | box(ox0, ox1, y_vagg, yb, za, zb)
    plat = plat - cylinder(SKORSTEN_D / 2, KS_T + 2.0, (X_SK, Y_SK, H_KASSE - KS_T - 1.0)) \
        - cylinder(LUFT_D / 2 + LUFT_FRI, KS_T + 2.0, (X_LUFT, Y_SK, H_KASSE - KS_T - 1.0))
    m.lagg(Del(f"Plåt över konvektionsöppningen, kalciumsilikat {KS_T:g}", plat, KALCIUMSILIKAT,
               artikel="Skamotec 225, 50 mm"), Placering(), "KM-PLAT")
    b, d, _ = KROPP
    p0, p1 = _luftvag()[1:3]                    # slangen under insatsen går genom det västra stödet
    slang = stang(p0, p1, LUFT_D + 2 * LUFT_FRI)
    for i, x0 in enumerate((X_MITT - b / 2, X_MITT + b / 2 - STOD_B), 1):
        stod: Form = box(x0, x0 + STOD_B, Y_FRONT - d, yb, 0.0, Z_INSATS)
        if i == 1:
            stod = stod - slang
        m.lagg(Del(f"Stöd under insatsen, kalciumsilikat {STOD_B:g}", stod, KALCIUMSILIKAT), Placering(), f"KM-STOD{i}")


def montage() -> Montage:
    m = Montage("Kamin", beskrivning="Rais 600 i väggen 2C, inbyggd enligt anvisningen, med isolerad skorsten "
                                     "genom taket")
    b, d, h = KROPP
    x0, y0, z0 = X_MITT - b / 2, Y_FRONT - d, Z_INSATS
    kropp = box(x0, x0 + b, y0, Y_FRONT, z0, z0 + h) - box(x0 + VAGG_T, x0 + b - VAGG_T, y0 + VAGG_T,
                                                         Y_FRONT - VAGG_T, z0 + VAGG_T, z0 + h - VAGG_T)
    m.lagg(Del("Kamininsats Rais 600, kropp", kropp, KAMIN, artikel="Rais 600 (frontmodell, glas)"), Placering(),
           "KM-INSATS")
    rb, rh, rt = RAM
    zm = z0 + h / 2
    gb, gh = GLASET
    ram = box(X_MITT - rb / 2, X_MITT + rb / 2, Y_FRONT, Y_FRONT + rt, zm - rh / 2, zm + rh / 2) - \
        box(X_MITT - gb / 2, X_MITT + gb / 2, Y_FRONT - 1, Y_FRONT + rt + 1, zm - gh / 2, zm + gh / 2)
    m.lagg(Del("Frontram Rais 600", ram, KAMIN), Placering(), "KM-RAM")
    m.lagg(Del("Glas Rais 600", box(X_MITT - gb / 2, X_MITT + gb / 2, Y_FRONT, Y_FRONT + 4, zm - gh / 2, zm + gh / 2),
               GLAS), Placering(), "KM-GLAS")
    _kasse(m)
    # rökstosen, rökröret och skorstenen, vars isolerade del börjar i kassen
    ys = Y_FRONT - STOS_FRAN_FRONT
    zt = z0 + h
    m.lagg(Del(f"Rökstos Ø{STOS_D:g}", ror((X_MITT, ys, zt), (X_MITT, ys, zt + STOS_H), STOS_D, 3.0), KAMIN),
           Placering(), "KM-STOS")
    a = (X_MITT, ys, zt + STOS_H)
    b1 = (X_MITT, ys, zt + STOS_H + 100.0)
    c = (X_SK, Y_SK, b1[2] + math.hypot(X_MITT - X_SK, ys - Y_SK))          # 45°
    assert c[2] < H_KASSE - KS_T - 50.0, "skorstenens isolerade del ska börja i kassen"
    for i, (p, q) in enumerate(((a, b1), (b1, c)), 1):
        m.lagg(Del(f"Rökrör Ø{ROR_D:g} L={math.dist(p, q):.0f}", ror(p, q, ROR_D, ROR_T), KAMIN), Placering(),
               f"KM-ROR{i}")
    vag = _luftvag()
    slang: Form = ror(vag[0], vag[1], LUFT_D, 1.0)
    for a_, b_ in zip(vag[1:], vag[2:]):
        slang = slang | ror(a_, b_, LUFT_D, 1.0)
    langd = sum(math.dist(a_, b_) for a_, b_ in zip(vag, vag[1:]))
    m.lagg(Del(f"Förbränningsluft, flexslang Ø{LUFT_D:g} L={langd:.0f}", slang, ROSTFRITT,
               artikel="Rais AirSystem, flexslang Ø100"), Placering(), "KM-LUFT")
    za, zb = H_KASSE, _z_luft_ut()
    m.lagg(Del(f"Förbränningsluft, isolerad kanal Ø{LUFT_D:g}/Ø{LUFT_D + 2 * LUFT_ISOL:g} L={zb - za:.0f}",
               ror((X_LUFT, Y_SK, za), (X_LUFT, Y_SK, zb), LUFT_D + 2 * LUFT_ISOL, LUFT_ISOL + 0.5), ROSTFRITT),
           Placering(), "KM-LUFT2")
    # huven 60 mm över kanalens ände (luften in under den), på tre stag från kanalens kant
    rk = LUFT_D / 2 + LUFT_ISOL / 2
    stag = [stang((X_LUFT + rk * math.cos(v), Y_SK + rk * math.sin(v), zb),
                  (X_LUFT + rk * math.cos(v), Y_SK + rk * math.sin(v), zb + 60.0), 8.0)
            for v in (0.0, 2 * math.pi / 3, 4 * math.pi / 3)]
    huv: Form = cylinder(LUFT_D / 2 + LUFT_ISOL + 40.0, 40.0, (X_LUFT, Y_SK, zb + 60.0))
    for st in stag:
        huv = huv | st
    m.lagg(Del("Huv för förbränningsluften, på stag", huv, ROSTFRITT), Placering(), "KM-LUFTHUV")
    rl = LUFT_D / 2 + LUFT_ISOL + LUFT_FRI
    m.lagg(Del("Takgenomföring för förbränningsluften, krage",
               ror((X_LUFT, Y_SK, _z_tak(X_LUFT - rl) - 80.0), (X_LUFT, Y_SK, _z_tak(X_LUFT + rl) + 100.0), 2 * rl,
                   LUFT_FRI), ROSTFRITT), Placering(), "KM-LUFTKRAGE")
    z_topp = _z_tak(S.HUSKROPPAR[2].nock) + OVER_NOCK
    m.lagg(Del(f"Isolerad skorsten Ø{SKORSTEN_INRE:g}/Ø{SKORSTEN_D:g}",
               ror((X_SK, Y_SK, c[2]), (X_SK, Y_SK, z_topp), SKORSTEN_D, (SKORSTEN_D - SKORSTEN_INRE) / 2), ROSTFRITT),
           Placering(), "KM-SKORSTEN")
    m.lagg(Del("Regnhuv", cylinder(SKORSTEN_D / 2 + FRI, 40.0, (X_SK, Y_SK, z_topp)), ROSTFRITT), Placering(), "KM-HUV")
    # takgenomföringens krage: täcker hålet i taket, från takets nedre sida upp 100 mm över dess övre
    r = SKORSTEN_D / 2 + FRI
    za, zb = _z_tak(X_SK - r) - 80.0, _z_tak(X_SK + r) + 100.0
    m.lagg(Del("Takgenomföring, krage", ror((X_SK, Y_SK, za), (X_SK, Y_SK, zb), 2 * r, FRI), ROSTFRITT), Placering(),
           "KM-KRAGE")
    return m
