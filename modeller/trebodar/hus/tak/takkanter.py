"""Takkanterna (planritning 201: takutstick 100 runt hela huset).

Vid takfoten finns ingen takfotsbräda: takbalkarnas ändar är synliga och fasadens panel går upp mellan dem
(fasad.py), så att luftintaget till takets luftspalt (U-03) är öppningen ovanför panelen. Takfotsplåt 0,6 över
råspontens framkant, 35 mm ned under råsponten och med droppnäsa över hängrännan, och halvrunda hängrännor Ø125
med gavlar. Stuprör Ø87 vid ändarna av de takfötter som går från gavel till gavel, från rännan till 150 mm över
marken längs fasaden; en takfot som slutar vid en dal har inget eget stuprör, utan rännan rinner till dalens ändlåda
och stupröret i hörnet (ett stuprör per hörn, dalar.py). Vid
gavlarna: vindskiva 22×145 ytterst i utsticket, med överkanten i plåtens överkant, och vindskivebeslag 0,6 vikt runt
vindskivan: från 50 mm in på plåten över vindskivans överkant, ned över hela framsidan och 15 mm in under den.
Råsponten, pappen och plåten går ut till vindskivan (takytor.py). Rännorna ligger vågrätt (fallet mot stuprören är
inte modellerat) och rännkrokarna (på råsponten) är inte modellerade.

Dalarna (kilar, rändal och ändlådor med stuprör) i dalar.py.
"""
from __future__ import annotations

import math

from modellering import Del, Montage, Placering, Union

from trebodar import skelett as S
from trebodar.byggdelar import taklager as L
from trebodar.byggdelar.regelvagg import Plan
from trebodar.byggdelar.ror import ror
from trebodar.byggdelar.virke import fmt
from trebodar.hus.fasad.markniva import mark_vid
from trebodar.hus.stomme.prefab.takbalkar.takbalkar import FALT
from trebodar.material import PANEL, TAKPLAT

from .takytor import REGIONER, Region, kant_takfot, regioner

RANNA_D, STUPROR_D = 125.0, 87.0
RANNA_SPEL = 3.0             # rännans bakkant framför takfotsplåten
NASA = (20.0, 10.0)          # droppnäsan: ut, ned
PLAT_NED = 35.0              # takfotsplåtens raka del under råspontens underkant, ovanför droppnäsan
VIK_IN = 15.0                # vindskivebeslagets vikning in under vindskivan
STUPROR_FRI = 30.0           # stuprörets avstånd från panelen
STUPROR_KANT = 150.0         # stuprörets läge från takfotens ände
STUPROR_MARK = 150.0         # stuprörets ände över marken


def _takfoter(kod: str) -> list[tuple[Region, bool, bool]]:
    """Takfallets takfotsregioner med om början och slutet ligger vid en gavel (annars vid en dal)."""
    rs = REGIONER[kod]
    y0, y1 = min(r.y0 for r in rs), max(r.y1 for r in rs)
    return [(r, r.y0 == y0, r.y1 == y1) for r in rs if r.nedre.x == FALT[kod].takfot]


def _ranna(kod: str) -> tuple[float, float, float]:
    """Takfotsplåtens nedre kant ovanför droppnäsan (z) och hängrännans mitt (x) och överkant (z)."""
    t = S.TAKFALL[kod]
    xe = kant_takfot(kod)
    zb = L.z_skikt(t, xe, L.RASPONT[0]) - PLAT_NED
    return zb, xe - t.riktning * (L.PLAT_T + RANNA_SPEL + RANNA_D / 2), zb - NASA[1] - 5.0


def _takfot(kod: str) -> Montage:
    """Takfotsplåt och hängränna längs takfallets takfötter."""
    t = S.TAKFALL[kod]
    r_ = t.riktning
    xe = kant_takfot(kod)                              # råspontens kant
    zp = L.z_skikt(t, xe, L.PLAT[1])                          # takfotsplåten från plåtens överkant
    zb, xr, zr = _ranna(kod)
    ut, ned = NASA
    plat = [(xe, zp), (xe, zb), (xe - r_ * ut, zb - ned), (xe - r_ * ut, zb - ned + 0.8),
            (xe - r_ * L.PLAT_T, zb + 0.5), (xe - r_ * L.PLAT_T, zp)]
    R = RANNA_D / 2
    n = 24
    yttre = [(xr + R * math.cos(math.pi + math.pi * i / n), zr + R * math.sin(math.pi + math.pi * i / n))
             for i in range(n + 1)]
    inre = [(xr + (R - L.PLAT_T) * math.cos(math.pi + math.pi * i / n),
             zr + (R - L.PLAT_T) * math.sin(math.pi + math.pi * i / n)) for i in range(n, -1, -1)]
    p = Plan(kod, f"Takfot {kod}", 1.0, beskrivning=f"Takfot, {S.HUSKROPPAR[t.kropp].namn}", material=TAKPLAT)
    for r, gavel0, gavel1 in _takfoter(kod):
        a, b = r.y0 - (L.GAVEL_UT if gavel0 else -1.0), r.y1 + (L.GAVEL_UT if gavel1 else -1.0)
        p.profil(plat, a, b, typ="TF", bas_namn="Takfotsplåt 0,6")
        p.profil(yttre + inre, a, b, typ="HR", bas_namn=f"Hängränna Ø{fmt(RANNA_D)}")
        for y in (a - 1.0, b):                         # rännans gavlar
            p.profil(yttre, y, y + 1.0, typ="RG", bas_namn=f"Rännans gavel Ø{fmt(RANNA_D)}")
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
            nedre = r.nedre                            # vid en dal: dalens ändlåda
            skiva = L.profil(t, w1 - bh, w1, nedre, r.nock)
            topp = L.profil(t, w1, w1 + L.PLAT_T, nedre, r.nock)
            fram = L.profil(t, w1 - bh - L.PLAT_T, w1 + L.PLAT_T, nedre, r.nock)
            under = L.profil(t, w1 - bh - L.PLAT_T, w1 - bh, nedre, r.nock)
            if not (skiva and topp and fram and under):
                continue
            y0, y1 = sorted((yk, kant))
            p.profil(skiva, y0, y1, typ="VS", bas_namn=f"Vindskiva {fmt(bt)}×{fmt(bh)}")
            # beslaget i en del: överkanten (huvudprofilen, y a–b), framsidan och vikningen under vindskivan
            a, b = sorted((yk - inat * L.PLAT_T, kant + inat * 50.0))
            vik = [(fram, sorted((yk - inat * L.PLAT_T, yk))), (under, sorted((yk - inat * L.PLAT_T, yk + inat * VIK_IN)))]
            p.profil(topp, a, b, typ="VB", material=TAKPLAT, bas_namn="Vindskivebeslag 0,6",
                     tillagg=[(q, b - y1, y1 - y0) for q, (y0, y1) in vik])
    return p.montage()


def _stupror_lagen() -> list[tuple[str, float]]:
    """Rännornas stuprör: vid båda ändarna av takfötter som går från gavel till gavel. En takfot som slutar vid en dal
    rinner till dalens ändlåda, med stupröret i hörnet (dalar.py)."""
    ut = []
    for kod in REGIONER:
        for r, gavel0, gavel1 in _takfoter(kod):
            if gavel0 and gavel1:
                ut += [(kod, r.y0 + STUPROR_KANT), (kod, r.y1 - STUPROR_KANT)]
    return ut


def _stupror(kod: str, y: float) -> Del:
    t = S.TAKFALL[kod]
    r_ = t.riktning
    _, xr, zr = _ranna(kod)
    v = S.YTTERVAGGAR[kod]
    x_fasad = t.x_utsida - r_ * S.T_FASAD
    xs = x_fasad - r_ * (STUPROR_FRI + STUPROR_D / 2)
    z_mark = mark_vid(kod, v.placering().invers().punkt((xs, y, 0.0))[0])
    a = (xr, y, zr - RANNA_D / 2)
    b = (xr, y, a[2] - 60.0)
    c = (xs, y, b[2] - abs(xr - xs))                   # 45° in mot fasaden
    d = (xs, y, z_mark + STUPROR_MARK)
    form = Union(tuple(ror(p, q, STUPROR_D, L.PLAT_T) for p, q in ((a, b), (b, c), (c, d))))
    return Del(f"Stuprör Ø{fmt(STUPROR_D)} L={fmt(b[2] - d[2] + 60.0)}", form, TAKPLAT)


def montage() -> Montage:
    m = Montage("Takkanter", beskrivning="Takfotsplåt, hängrännor, stuprör, vindskivor och vindskivebeslag")
    for kod in REGIONER:
        if _takfoter(kod):
            m.lagg(_takfot(kod))
        m.lagg(_vindskivor(kod))
    sr = Montage("Stuprör")
    for i, (kod, y) in enumerate(sorted(_stupror_lagen()), 1):
        sr.lagg(_stupror(kod, y), Placering(), f"ST{i}")
    m.lagg(sr)
    return m
