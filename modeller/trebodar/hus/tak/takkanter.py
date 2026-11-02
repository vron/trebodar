"""Takkanterna (planritning 201: takutstick 100 runt hela huset).

Vid takfoten finns ingen takfotsbräda: takbalkarnas ändar är synliga och fasadens panel går upp mellan dem
(fasad.py), så att luftintaget till takets luftspalt (U-03) är öppningen ovanför panelen. Takfotsplåt 0,6 över
råspontens framkant, 35 mm ned under råsponten och med droppnäsa över hängrännan, och halvrunda hängrännor Ø125
med gavlar. Stuprör Ø87 vid dalarnas ändar och vid de långa takfötternas ändar, från rännan till 150 mm över marken
längs fasaden. Vid gavlarna: vindskiva 22×145 ytterst i utsticket, med överkanten i plåtens överkant, och
vindskivebeslag 0,6 vikt runt vindskivan: från 50 mm in på plåten över vindskivans överkant, ned över hela framsidan
och 15 mm in under den. Råsponten, pappen och plåten går ut till vindskivan (tak.py). Rännorna ligger vågrätt
(fallet mot stuprören är inte modellerat) och rännkrokarna (på råsponten) är inte modellerade.

I dalarna (vågräta dallinjer): kilar av plywood på råsponten med fall 1:60 från mitten mot ändarna, som på dallinjen
stiger från noll vid ändarna till högst i mitten och på sidorna går ned till råsponten 300 mm ut, och en rändal av
plåt på underlagspapp över kilarna och remsan; takets papp och plåt slutar vid rändalen. Vattnet rinner ut i
grannkroppens takfotsränna, där dalen slutar mot en gavel, och vidare i stupröret där.
"""
from __future__ import annotations

import math

from modellering import Del, Form, Montage, Placering, Union, polyeder

from trebodar import skelett as S
from trebodar.byggdelar import taklager as L
from trebodar.byggdelar.regelvagg import Plan
from trebodar.byggdelar.ror import ror
from trebodar.byggdelar.virke import fmt
from trebodar.hus.fasad.fasad import PANEL, mark_vid
from trebodar.hus.stomme.prefab.takbalkar.takbalkar import FALT
from trebodar.material import PLYWOOD, TAKPLAT

from .tak import REGIONER, Region, kant_takfot, regioner

PLAT_T = 0.6
RANNA_D, STUPROR_D = 125.0, 87.0
RANNA_SPEL = 3.0             # rännans bakkant framför takfotsplåten
NASA = (20.0, 10.0)          # droppnäsan: ut, ned
PLAT_NED = 35.0              # takfotsplåtens raka del under råspontens underkant, ovanför droppnäsan
VIK_IN = 15.0                # vindskivebeslagets vikning in under vindskivan
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


def _ranna(kod: str) -> tuple[float, float, float]:
    """Takfotsplåtens nedre kant ovanför droppnäsan (z) och hängrännans mitt (x) och överkant (z)."""
    t = S.TAKFALL[kod]
    xe = kant_takfot(kod)
    zb = _z(t, xe, L.RASPONT[0]) - PLAT_NED
    return zb, xe - t.riktning * (PLAT_T + RANNA_SPEL + RANNA_D / 2), zb - NASA[1] - 5.0


def _takfot(kod: str) -> Montage:
    """Takfotsplåt och hängränna längs takfallets takfötter."""
    t = S.TAKFALL[kod]
    r_ = t.riktning
    xe = kant_takfot(kod)                              # råspontens kant
    zp = _z(t, xe, L.PLAT[1])                          # takfotsplåten från plåtens överkant
    zb, xr, zr = _ranna(kod)
    ut, ned = NASA
    plat = [(xe, zp), (xe, zb), (xe - r_ * ut, zb - ned), (xe - r_ * ut, zb - ned + 0.8),
            (xe - r_ * PLAT_T, zb + 0.5), (xe - r_ * PLAT_T, zp)]
    R = RANNA_D / 2
    n = 24
    yttre = [(xr + R * math.cos(math.pi + math.pi * i / n), zr + R * math.sin(math.pi + math.pi * i / n))
             for i in range(n + 1)]
    inre = [(xr + (R - PLAT_T) * math.cos(math.pi + math.pi * i / n),
             zr + (R - PLAT_T) * math.sin(math.pi + math.pi * i / n)) for i in range(n, -1, -1)]
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
            nedre = r.nedre
            if abs(nedre.x - kant_takfot(kod)) > 1e-6:
                # där en dal slutar: vindskivan slutar före grannkroppens takfotsplåt, som rännan går under
                nedre = L.Kant("lodratt", nedre.x + t.riktning * 25.0)
            skiva = L.profil(t, w1 - bh, w1, nedre, r.nock)
            topp = L.profil(t, w1, w1 + PLAT_T, nedre, r.nock)
            fram = L.profil(t, w1 - bh - PLAT_T, w1 + PLAT_T, nedre, r.nock)
            under = L.profil(t, w1 - bh - PLAT_T, w1 - bh, nedre, r.nock)
            if not (skiva and topp and fram and under):
                continue
            y0, y1 = sorted((yk, kant))
            p.profil(skiva, y0, y1, typ="VS", bas_namn=f"Vindskiva {fmt(bt)}×{fmt(bh)}")
            # beslaget i en del: överkanten (huvudprofilen, y a–b), framsidan och vikningen under vindskivan
            a, b = sorted((yk - inat * PLAT_T, kant + inat * 50.0))
            vik = [(fram, sorted((yk - inat * PLAT_T, yk))), (under, sorted((yk - inat * PLAT_T, yk + inat * VIK_IN)))]
            p.profil(topp, a, b, typ="VB", material=TAKPLAT, bas_namn="Vindskivebeslag 0,6",
                     tillagg=[(q, b - y1, y1 - y0) for q, (y0, y1) in vik])
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
    _, xr, zr = _ranna(kod)
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


Punkt = tuple[float, float, float]


def _tunn(tri: tuple[Punkt, Punkt, Punkt], t0: float, t1: float) -> Form:
    """Skikt över triangeln, t0–t1 längs dess normal uppåt."""
    a, b, c = tri
    u = [b[i] - a[i] for i in range(3)]
    v = [c[i] - a[i] for i in range(3)]
    n = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]
    ln = math.sqrt(sum(x * x for x in n)) * (1.0 if n[2] > 0 else -1.0)
    n = [x / ln for x in n]
    horn = [tuple(p[i] + n[i] * t for i in range(3)) for t in (t0, t1) for p in tri]
    return polyeder(horn, [[0, 1, 2], [3, 4, 5], [0, 1, 4, 3], [1, 2, 5, 4], [2, 0, 3, 5]])


def _randal(dal: str) -> Montage:
    """Kilarna, rändalens papp och plåt i dalen längs balken dal."""
    b = S.BALKAR[dal]
    sidor = [(kod, r) for kod, rs in REGIONER.items() for r in rs if r.nedre.x == b.x]
    y0, y1 = min(r.y0 for _, r in sidor), max(r.y1 for _, r in sidor)
    ym, h = (y0 + y1) / 2, (y1 - y0) / 2 * L.RANDAL_FALL
    kilar: list[Form] = []
    ytor: list[tuple[Punkt, Punkt, Punkt]] = []
    for kod in sorted({k for k, _ in sidor}):
        t = S.TAKFALL[kod]
        xv, xw = b.x, b.x + t.riktning * L.RANDAL_B

        def z(x: float) -> float:
            return _z(t, x, L.RASPONT[1])
        for ye in (y0, y1):
            A, B = (xv, ye, z(xv)), (xw, ye, z(xw))
            C, D, E = (xw, ym, z(xw)), (xv, ym, z(xv) + h), (xv, ym, z(xv))
            kilar.append(polyeder([A, E, C, D], [[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]]))
            ytor += [(A, B, C), (A, C, D)]
    m = Montage(f"Rändal {dal}", beskrivning=f"Kilar med fall 1:{1 / L.RANDAL_FALL:.0f} och rändal längs {dal}")
    m.lagg(Del(f"Kilar plywood, fall 1:{1 / L.RANDAL_FALL:.0f}, högst {h:.0f}", Union(tuple(kilar)), PLYWOOD),
           Placering(), f"{dal}-KIL")
    tj = L.PLAT[1] - L.PAPP[0]                 # papp och plåt i en del (skikten följer de vikta ytorna)
    m.lagg(Del("Rändal, plåt 0,6 på underlagspapp", Union(tuple(_tunn(tri, 0.0, tj) for tri in ytor)), TAKPLAT),
           Placering(), f"{dal}-RD")
    return m


def montage() -> Montage:
    m = Montage("Takkanter", beskrivning="Takfotsplåt, hängrännor, stuprör, vindskivor, vindskivebeslag och rändalar")
    for dal in ("DB2", "DB4"):
        m.lagg(_randal(dal))
    for kod in REGIONER:
        if _takfoter(kod):
            m.lagg(_takfot(kod))
        m.lagg(_vindskivor(kod))
    sr = Montage("Stuprör")
    for i, (kod, y) in enumerate(sorted(_stupror_lagen()), 1):
        sr.lagg(_stupror(kod, y), Placering(), f"ST{i}")
    m.lagg(sr)
    return m
