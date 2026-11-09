"""Stålbanden (K-04): kryss av stålband 40×2,0 (byggdelar/stalband.py) i väggarnas och takfallens fält. De
stabiliserar stommen mot horisontella laster utan att skivorna räknas: väggarna för lasterna ned till bjälklaget och
takfallen för dem i takets plan till väggarna.

- Väggarna: fältet mellan två stående delar (u ungefär vid deras mitt i väggens system; banden går till den
  närmaste hela regeln eller stolpen), från syllens mitt vid den ena till hammarbandets mitt vid den andra, infällda
  i stommens yta w 0.
- Takfallen: fältet mellan två lägen y (takbalkarnas eller gavelstolarnas mitt), från takfoten (ytterväggens mitt)
  eller dalbalkens sida till nockbalkens sida, infällda i takbalkarnas överkant; inte över takfönstren och
  ventilationens kanaler genom taket (takhuvar och takfläktar).

Fälten är valda i K-04, som räknar stommen med banden: ändras ett fält, räknas K-04 om med ./bygg K-04.
"""
from __future__ import annotations

import numpy as np

from modellering import Montage

from trebodar import skelett as S
from trebodar.byggdelar.stalband import band
from trebodar.hus.installationer.ventilation.delar import Avluft, Kanal
from trebodar.hus.installationer.ventilation.system import MODULER
from trebodar.hus.stomme import lagen
from trebodar.hus.stomme.prefab.takbalkar.takbalkar import FALT, balkens_sida

R = 45.0

# väggarnas fält med kryss: (u, u) i väggens system, ungefär vid de stående delarnas mitt
VAGGAR: dict[str, tuple[tuple[float, float], ...]] = {
    "1NO": ((1772.5, 2977.5), (3622.5, 4287.5)),
    "1SO": ((22.5, 1095.5), (2940.5, 5012.5), (6147.5, 8295.5), (8295.5, 10695.5), (11340.5, 12157.5)),
    "1SV": ((22.5, 1112.5), (3257.5, 4347.5)),
    "1NV": ((1887.5, 3012.5),),
    "2NO": ((3067.5, 4222.5),),
    "2NV": ((22.5, 882.5),),
    "2SO": ((1612.5, 3472.5),),
    "3NO": ((1617.5, 2822.5),),
    "3NV": ((1382.5, 2237.5), (4782.5, 7095.0), (9992.5, 11357.5)),
    "3SV": ((1717.5, 2752.5),),
    "1B": ((22.5, 1002.5), (1207.5, 2187.5)),
    "2B": ((22.5, 1202.5), (1202.5, 2402.5)),
    "2C": ((2841.5, 4285.0),),
}

# takfallens fält med kryss: längs hela takfallet mellan gavlarna, fält om högst FALT_TAK mellan takbalkarnas eller
# gavelstolarnas mitt, inte över takfönstren och kanalerna genom taket (KANAL_MARGINAL från kanalens yta) och delade där
# dalbalken slutar
FALT_TAK = 2400.0
KANAL_MARGINAL = 50.0


def staende(kod: str) -> list[tuple[float, float]]:
    """Väggens hela stående delar (reglar och stolpar från syllen och minst 1,5 m upp): (u i mitten, överkant z). En
    stolpe som går förbi hammarbandet upp till en balk (som stolparna i 1B:s ändar) räknas till hammarbandets
    underkant, så att bandet slutar i hammarbandets höjd och inte i balken."""
    v = S.VAGGAR[kod]
    o, u = np.array(v.origo), np.array(v.u)
    delar = lagen.vagg(kod)
    hb = [d.lada[5] for d in delar if d.typ == "H"]
    ut = []
    for d in delar:
        x0, y0, z0, x1, y1, z1 = d.lada
        a, b = sorted(float((np.array(p) - o) @ u) for p in ((x0, y0), (x1, y1)))
        if b - a <= 100.0 and z0 <= 60.0 and z1 >= 1500.0:
            if hb and z1 >= max(hb) - 1.0:
                z1 = max(hb) - R
            ut.append(((a + b) / 2, z1))
    return sorted(ut)


def vaggens_band(kod: str) -> Montage:
    v = S.VAGGAR[kod]
    o, u, w = np.array([*v.origo, 0.0]), np.array([*v.u, 0.0]), np.array([*v.w, 0.0])
    st = staende(kod)
    m = Montage(f"Stålband {kod}", kod, f"Stålband i kryss i väggen {kod}")
    i = 0
    for a, b in VAGGAR[kod]:
        (ua, za), (ub, zb) = (min(st, key=lambda s: abs(s[0] - x)) for x in (a, b))
        for (p, zp), (q, zq) in (((ua, R / 2), (ub, zb + R / 2)), ((ub, R / 2), (ua, za + R / 2))):
            d, pl = band(o + p * u + np.array([0, 0, zp]), o + q * u + np.array([0, 0, zq]), w)
            i += 1
            m.lagg(d, pl, f"{kod}-B{i:02d}")
    return m


def _kanaler_genom_taket(kod: str) -> list[tuple[float, float]]:
    """Ventilationens kanaler genom takfallet (till takhuvarna och takfläktarna): (y0, y1) med marginalen."""
    ut = []
    for mod in MODULER:
        a, k = mod.GREN.kedja[-1], mod.GREN.kedja[-2]
        if isinstance(a, Avluft) and isinstance(k, Kanal) and a.lage.yta == "yttertak" and a.lage.ref == kod:
            r = k.typ.yttre[0] / 2 + KANAL_MARGINAL
            ut.append((a.lage.punkt[1] - r, a.lage.punkt[1] + r))
    return ut


def takfallets_falt(kod: str) -> list[tuple[float, float]]:
    """Takfallets fält med kryss: (y, y) mellan de bärande delarnas mitt (takbalkarna och gavelstolarnas
    ytterbalkar), högst FALT_TAK breda och inte över takfönstren och kanalerna genom taket."""
    t, f = S.TAKFALL[kod], FALT[kod]
    gavlar = []
    for g in lagen.GAVELVAGGAR[t.kropp]:
        x = [d for d in lagen.takstol(g) if d.typ == "X"]
        if x:                                        # ytterbalkarna: överkanten i takplanet, högst upp i stolen
            topp = max(d.lada[5] for d in x)
            gavlar.append(next(0.5 * (d.lada[1] + d.lada[4]) for d in x if d.lada[5] == topp))
    ys = sorted({round(y + R / 2, 3) for y in f.y} | {round(y, 3) for y in gavlar})
    hinder = [(fo.y0, fo.y1) for fo in f.fonster] + _kanaler_genom_taket(kod)
    ut, a = [], ys[0]
    while a < ys[-1] - 1.0:
        mojliga = [y for y in ys if a + 300.0 < y <= a + FALT_TAK + 1.0
                   and not any(a < h1 and y > h0 for h0, h1 in hinder)]
        if not mojliga:                              # ett takfönster: nästa fält börjar efter det
            a = min(y for y in ys if y > a + 1.0)
            continue
        ut.append((a, max(mojliga)))
        a = max(mojliga)
    return ut


def takfallets_band(kod: str) -> Montage:
    """Banden från den nedre kanten (dalbalkens sida där dalbalken är, annars takfotsväggens mitt) vid det ena
    fältets läge till nockbalkens sida vid det andra."""
    t, f = S.TAKFALL[kod], FALT[kod]
    s, c = S.SIN, S.COS
    inat = np.array([t.riktning * s, 0.0, -c])
    upp = balkens_sida(f.nock, t)
    dal = S.BALKAR[f.dal] if f.dal else None

    def ner(y: float) -> float:
        if dal and dal.y0 - 1.0 <= y <= dal.y1 + 1.0:
            return balkens_sida(dal.kod, t)
        return t.x_insida - t.riktning * S.T_STOMME / 2

    m = Montage(f"Stålband takfall {kod}", kod, f"Stålband i kryss i takfallet {kod}")
    i = 0
    for ya, yb in takfallets_falt(kod):
        for (y0, y1) in ((ya, yb), (yb, ya)):
            p = np.array([ner(y0), y0, t.z_overkant(ner(y0))])
            q = np.array([upp, y1, t.z_overkant(upp)])
            d, pl = band(p, q, inat)
            i += 1
            m.lagg(d, pl, f"T{kod}-B{i:02d}")
    return m


def montage() -> Montage:
    m = Montage("Stålband", beskrivning="Stålband 40×2,0 S350GD+Z275 i kryss, infällda (K-04)")
    vaggar = Montage("Väggar", beskrivning="Stålband i väggarnas fält")
    for kod in VAGGAR:
        vaggar.lagg(vaggens_band(kod))
    tak = Montage("Takfall", beskrivning="Stålband i takfallen, på takbalkarna")
    for kod in FALT:
        tak.lagg(takfallets_band(kod))
    m.lagg(vaggar)
    m.lagg(tak)
    return m
