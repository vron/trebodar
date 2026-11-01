"""Kaminen: Rais 600 (frontmodell med glas, ritning 11-0000-6550) i öppningen i väggen 2C (planritning 201), mot
allrummet, med kroppen i en kåpa av kalciumsilikat på sovrumssidan (de lätta väggarna L7, L13 och L14 och
skikten mot kåpan, invandigt/vaggar.py) och rökröret till en isolerad skorsten genom taket.

Insatsen: kropp 720 × 611 × 402 (stål, ihålig), frontram 758 × 627 med glas 560 × 438, rökstos Ø147 överst mitt på,
188 mm bakom fronten; underkanten 450 över golvet (antaget). Runt fronten en omfattning av kalciumsilikat 25 mm i
väggens liv. Rökröret Ø150 går först lodrätt, sedan 45° förbi nockbalk 3 och fram till skorstenen, som står i facket
mellan takbalken vid y 5 415 och takstolen 2C. Skorstenen: isolerad, Ø150/Ø250 rostfri, från 300 mm under innertaket
till 800 mm över nocken, med regnhuv. Hålet genom innertaket, isoleringen och taket har 50 mm avstånd till
skorstenen (GENOMFORING, skärs i husets skikt i hus.py).
"""
from __future__ import annotations

import math

from modellering import Del, Form, Montage, Placering, box, cylinder

from trebodar import skelett as S
from trebodar.byggdelar import taklager as L
from trebodar.material import GLAS, KALCIUMSILIKAT, KAMIN, ROSTFRITT

# insatsen (Rais 600)
KROPP = (720.0, 402.0, 611.0)               # bredd, djup, höjd
RAM = (758.0, 627.0, 10.0)                  # frontram: bredd, höjd, tjocklek
GLASET = (560.0, 438.0)
STOS_D, STOS_FRAN_FRONT, STOS_H = 147.0, 188.0, 40.0
VAGG_T = 5.0                                # kroppens plåt
Z_INSATS = 450.0                            # underkanten över golvet (antaget)
# öppningen i 2C och läget
# insatsens mitt 30 mm väster om öppningens mitt (oppningar.INNEROPPNINGAR), fri från kåpans östra vägg L7
X_MITT = S.INNERVAGGAR["2C"].origo[0] + (1983.0 + 2993.0) / 2 - 30.0
Y_FRONT = S.INNERVAGGAR["2C"].origo[1] + S.INNERVAGGAR["2C"].tjocklek + 25.0   # skiktets yta mot allrummet
OMFATTNING = (6400.0, 7410.0, 0.0, 2045.0)  # öppningen: x0, x1, z0, z1
# rökröret och skorstenen
ROR_D, ROR_T = 150.0, 1.5
SKORSTEN_D, SKORSTEN_INRE = 250.0, 150.0
FRI = 50.0                                  # avstånd till brännbart vid genomföringen
X_SK, Y_SK = 6590.0, 5710.0                 # skorstenens mitt: förbi nockbalken och dess upplagsregel, i facket
OVER_NOCK = 800.0


def _ror(a: tuple[float, float, float], b: tuple[float, float, float], d: float, t: float) -> Form:
    """Rör med ytterdiametern d och godset t från a till b."""
    v = [b[i] - a[i] for i in range(3)]
    langd = math.sqrt(sum(c * c for c in v))
    x = (1.0, 0.0, 0.0) if abs(v[0]) < 0.9 * langd else (0.0, 1.0, 0.0)
    return (cylinder(d / 2, langd) - cylinder(d / 2 - t, langd)).placerad(Placering.axlar(a, x, v))


def _z_tak(x: float) -> float:
    """Takplåtens överkant i nocken (mittre huskroppen)."""
    return S.TAKFALL["2SO"].z_overkant(x) + L.PLAT[1] / S.COS


def _innertak(r: float = 0.0) -> float:
    """Innertakets underkant vid skorstenen, den lägsta inom avståndet r (taket lutar)."""
    from trebodar.hus.invandigt.vaggar import innertak
    return min(innertak(X_SK + dx, Y_SK + dy) for dx in (-r, 0.0, r) for dy in (-r, 0.0, r))


def genomforing() -> tuple[Form, tuple[float, float, float, float, float, float]]:
    """Hålet för skorstenen genom innertaket, isoleringen och taket, med lådan (för genomforing.genomfor)."""
    r = SKORSTEN_D / 2 + FRI
    z0, z1 = _innertak(r) - 2.0, _z_tak(S.HUSKROPPAR[2].nock) + OVER_NOCK + 20.0
    return cylinder(r, z1 - z0, (X_SK, Y_SK, z0)), (X_SK - r, Y_SK - r, z0, X_SK + r, Y_SK + r, z1)


def montage() -> Montage:
    m = Montage("Kamin", beskrivning="Rais 600 i väggen 2C med rökrör och isolerad skorsten genom taket")
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
    # omfattningen i öppningen, runt insatsens kropp
    ox0, ox1, oz0, oz1 = OMFATTNING
    om = box(ox0, ox1, Y_FRONT - 25.0, Y_FRONT, oz0, oz1) - box(x0, x0 + b, Y_FRONT - 26.0, Y_FRONT + 1, z0, z0 + h)
    m.lagg(Del("Omfattning kalciumsilikat 25", om, KALCIUMSILIKAT), Placering(), "KM-OMFATTNING")
    # rökstosen, rökröret och skorstenen
    ys = Y_FRONT - STOS_FRAN_FRONT
    zt = z0 + h
    m.lagg(Del(f"Rökstos Ø{STOS_D:g}", _ror((X_MITT, ys, zt), (X_MITT, ys, zt + STOS_H), STOS_D, 3.0), KAMIN),
           Placering(), "KM-STOS")
    horisontellt = math.hypot(X_MITT - X_SK, ys - Y_SK)
    a = (X_MITT, ys, zt + STOS_H)
    b1 = (X_MITT, ys, zt + STOS_H + 100.0)
    c = (X_SK, Y_SK, b1[2] + horisontellt)                      # 45°
    z_sk = _innertak(SKORSTEN_D / 2) - 300.0
    for i, (p, q) in enumerate(((a, b1), (b1, c), (c, (X_SK, Y_SK, z_sk))), 1):
        langd = math.dist(p, q)
        m.lagg(Del(f"Rökrör Ø{ROR_D:g} L={langd:.0f}", _ror(p, q, ROR_D, ROR_T), KAMIN), Placering(), f"KM-ROR{i}")
    z_topp = _z_tak(S.HUSKROPPAR[2].nock) + OVER_NOCK
    m.lagg(Del(f"Isolerad skorsten Ø{SKORSTEN_INRE:g}/Ø{SKORSTEN_D:g}",
               _ror((X_SK, Y_SK, z_sk), (X_SK, Y_SK, z_topp), SKORSTEN_D, (SKORSTEN_D - SKORSTEN_INRE) / 2), ROSTFRITT),
           Placering(), "KM-SKORSTEN")
    m.lagg(Del("Regnhuv", cylinder(SKORSTEN_D / 2 + FRI, 40.0, (X_SK, Y_SK, z_topp)), ROSTFRITT), Placering(), "KM-HUV")
    # takgenomföringens krage: täcker hålet i taket, från takets nedre sida upp 100 mm över dess övre
    r = SKORSTEN_D / 2 + FRI
    za, zb = _z_tak(X_SK - r) - 80.0, _z_tak(X_SK + r) + 100.0
    m.lagg(Del("Takgenomföring, krage", _ror((X_SK, Y_SK, za), (X_SK, Y_SK, zb), 2 * r, FRI), ROSTFRITT), Placering(),
           "KM-KRAGE")
    return m
