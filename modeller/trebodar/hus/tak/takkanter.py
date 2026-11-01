"""Takkanterna (planritning 201: takutstick 100 runt hela huset).

Vid takfoten: takfotsbräda 22×145 på takbalkarnas ändar med luftspalt 25 mm upp till råsponten (U-03:s luftintag,
med nät), takfotsplåt 0,6 över råspontens framkant med droppnäsa över hängrännan, och halvrunda hängrännor Ø125 med
gavlar. Stuprör Ø87 vid dalarnas ändar och vid de långa takfötternas ändar, från rännan till 150 mm över marken längs
fasaden. Vid gavlarna: vindskiva 22×145 ytterst i utsticket, med överkanten i plåtens överkant, och vindskivebeslag
0,6 över vindskivan och 50 mm in på plåten. Råsponten, pappen och plåten går ut till vindskivan (tak.py). Rännorna
ligger vågrätt (fallet mot stuprören är inte modellerat) och rännkrokarna är inte modellerade.
"""
from __future__ import annotations

import math

from modellering import Del, Montage, Placering, Union

from trebodar import skelett as S
from trebodar.byggdelar import taklager as L
from trebodar.byggdelar.regelvagg import Plan
from trebodar.byggdelar.ror import ror
from trebodar.byggdelar.virke import fmt
from trebodar.hus.fasad.fasad import PANEL, mark_vid
from trebodar.hus.stomme.prefab.takbalkar.takbalkar import FALT
from trebodar.material import TAKPLAT

from .tak import REGIONER, Region, kant_takfot, regioner

PLAT_T = 0.6
RANNA_D, STUPROR_D = 125.0, 87.0
RANNA_SPEL = 3.0             # rännans bakkant framför takfotsplåten
NASA = (20.0, 10.0)          # droppnäsan: ut, ned
STUPROR_FRI = 30.0           # stuprörets avstånd från panelen
STUPROR_KANT = 150.0         # stuprörets läge från takfotens ände
STUPROR_MARK = 150.0         # stuprörets ände över marken


def _z(t: S.Takfall, x: float, w: float) -> float:
    """z för punkten w (vinkelrätt) över takbalkarnas överkant vid x."""
    return t.z_overkant(x) + w / S.COS


def _takfoter(kod: str) -> list[tuple[Region, bool, bool]]:
    """Takfallets takfotsregioner med om början och slutet ligger vid en gavel (annars vid en dal)."""
    rs = REGIONER[kod]
    y0, y1 = min(r.y0 for r in rs), max(r.y1 for r in rs)
    return [(r, r.y0 == y0, r.y1 == y1) for r in rs if r.nedre.x == FALT[kod].takfot]


def _takfot(kod: str) -> Montage:
    """Takfotsbräda, takfotsplåt och hängränna längs takfallets takfötter."""
    t = S.TAKFALL[kod]
    r_ = t.riktning
    xe = kant_takfot(kod)                              # råspontens kant och takfotsbrädans utsida
    xi = FALT[kod].takfot
    topp = _z(t, xe, L.RASPONT[0]) - L.LUFT_TAKFOT     # takfotsbrädans överkant
    bt, bh = L.VINDSKIVA
    brada = [(xi, topp - bh), (xe, topp - bh), (xe, topp), (xi, topp)]
    zp, zb = _z(t, xe, L.PLAT[1]), topp - 10.0         # takfotsplåten från plåtens överkant till 10 mm förbi brädan
    ut, ned = NASA
    plat = [(xe, zp), (xe, zb), (xe - r_ * ut, zb - ned), (xe - r_ * ut, zb - ned + 0.8),
            (xe - r_ * PLAT_T, zb + 0.5), (xe - r_ * PLAT_T, zp)]
    R = RANNA_D / 2
    xr, zr = xe - r_ * (PLAT_T + RANNA_SPEL + R), zb - ned - 5.0       # rännans mitt och överkant
    n = 24
    yttre = [(xr + R * math.cos(math.pi + math.pi * i / n), zr + R * math.sin(math.pi + math.pi * i / n))
             for i in range(n + 1)]
    inre = [(xr + (R - PLAT_T) * math.cos(math.pi + math.pi * i / n),
             zr + (R - PLAT_T) * math.sin(math.pi + math.pi * i / n)) for i in range(n, -1, -1)]
    kropp = S.HUSKROPPAR[t.kropp]
    panel = PANEL[t.kropp]
    p = Plan(kod, f"Takfot {kod}", 1.0, beskrivning=f"Takfot, {kropp.namn}", material=panel)
    g_brada = L.GAVEL_UT - bt                          # takfotsbrädan till vindskivan
    for r, gavel0, gavel1 in _takfoter(kod):
        a, b = r.y0 - (L.GAVEL_UT if gavel0 else -1.0), r.y1 + (L.GAVEL_UT if gavel1 else -1.0)
        p.profil(brada, r.y0 - (g_brada if gavel0 else 0.0), r.y1 + (g_brada if gavel1 else 0.0), typ="TB",
                 material=panel, bas_namn=f"Takfotsbräda {fmt(bt)}×{fmt(bh)}")
        p.profil(plat, a, b, typ="TF", material=TAKPLAT, bas_namn="Takfotsplåt 0,6")
        p.profil(yttre + inre, a, b, typ="HR", material=TAKPLAT, bas_namn=f"Hängränna Ø{fmt(RANNA_D)}")
        for y in (a - 1.0, b):                         # rännans gavlar
            p.profil(yttre, y, y + 1.0, typ="RG", material=TAKPLAT, bas_namn=f"Rännans gavel Ø{fmt(RANNA_D)}")
    return p.montage()


def _vindskivor(kod: str) -> Montage:
    """Vindskivor och vindskivebeslag i gavlarnas utstick (där takfallet slutar mot en gavel)."""
    t = S.TAKFALL[kod]
    bt, bh = L.VINDSKIVA
    w1 = L.PLAT[1]
    p = Plan(kod, f"Vindskivor {kod}", 1.0, beskrivning="Vindskivor och vindskivebeslag", material=PANEL[t.kropp])
    rs = regioner(kod, "TP")
    y_min, y_max = min(r.y0 for r in rs), max(r.y1 for r in rs)
    for r in rs:
        for kant, inat in ((y_min, 1.0), (y_max, -1.0)):
            if abs((r.y0 if inat > 0 else r.y1) - kant) > 1e-6:
                continue
            yk = kant - inat * bt                      # utstickets yttre kant
            nedre = r.nedre
            if abs(nedre.x - kant_takfot(kod)) > 1e-6:
                # där en dal slutar: vindskivan slutar före grannkroppens takfotsplåt, som rännan går under
                nedre = L.Kant("lodratt", nedre.x + t.riktning * 25.0)
            skiva = L.profil(t, w1 - bh, w1, nedre, r.nock)
            topp = L.profil(t, w1, w1 + PLAT_T, nedre, r.nock)
            lapp = L.profil(t, w1 + PLAT_T - 45.0, w1 + PLAT_T, nedre, r.nock)
            if not (skiva and topp and lapp):
                continue
            for prof, (a, b), typ, namn, mat in (
                    (skiva, sorted((yk, kant)), "VS", f"Vindskiva {fmt(bt)}×{fmt(bh)}", PANEL[t.kropp]),
                    (topp, sorted((yk, kant + inat * 50.0)), "VB", "Vindskivebeslag 0,6", TAKPLAT),
                    (lapp, sorted((yk, yk - inat * PLAT_T)), "VB", "Vindskivebeslag 0,6, kant", TAKPLAT)):
                p.profil(prof, a, b, typ=typ, material=mat, bas_namn=namn)
    return p.montage()


def _stupror_lagen() -> list[tuple[str, float]]:
    """Stuprören: vid dalarnas ändar (takfotens ände mot en dal) och vid båda ändarna av takfötter utan dal."""
    ut = []
    for kod in REGIONER:
        tf = _takfoter(kod)
        har_dal = any(not (g0 and g1) for _, g0, g1 in tf)
        for r, gavel0, gavel1 in tf:
            for y, gavel, inat in ((r.y0, gavel0, 1.0), (r.y1, gavel1, -1.0)):
                if not gavel or not har_dal:
                    ut.append((kod, y + inat * STUPROR_KANT))
    return ut


def _stupror(kod: str, y: float) -> Del:
    t = S.TAKFALL[kod]
    r_ = t.riktning
    xe = kant_takfot(kod)
    topp = _z(t, xe, L.RASPONT[0]) - L.LUFT_TAKFOT
    zr = topp - 10.0 - NASA[1] - 5.0
    xr = xe - r_ * (PLAT_T + RANNA_SPEL + RANNA_D / 2)
    v = S.YTTERVAGGAR[kod]
    x_fasad = t.x_utsida - r_ * S.T_FASAD
    xs = x_fasad - r_ * (STUPROR_FRI + STUPROR_D / 2)
    z_mark = mark_vid(kod, v.placering().invers().punkt((xs, y, 0.0))[0])
    a = (xr, y, zr - RANNA_D / 2)
    b = (xr, y, a[2] - 60.0)
    c = (xs, y, b[2] - abs(xr - xs))                   # 45° in mot fasaden
    d = (xs, y, z_mark + STUPROR_MARK)
    form = Union(tuple(ror(p, q, STUPROR_D, PLAT_T) for p, q in ((a, b), (b, c), (c, d))))
    return Del(f"Stuprör Ø{fmt(STUPROR_D)} L={fmt(b[2] - d[2] + 60.0)}", form, TAKPLAT)


def montage() -> Montage:
    m = Montage("Takkanter", beskrivning="Takfotsbrädor, takfotsplåt, hängrännor, stuprör, vindskivor och beslag")
    for kod in REGIONER:
        if _takfoter(kod):
            m.lagg(_takfot(kod))
        m.lagg(_vindskivor(kod))
    sr = Montage("Stuprör")
    for i, (kod, y) in enumerate(sorted(_stupror_lagen()), 1):
        sr.lagg(_stupror(kod, y), Placering(), f"ST{i}")
    m.lagg(sr)
    return m
