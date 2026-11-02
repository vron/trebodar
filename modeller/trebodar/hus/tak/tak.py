"""Yttertaket ovanpå takbalkarna (F-01, U-03), ett montage per takfall och ett för takfönstren.

Skikt från takbalkarna och utåt: hårdboard 3 mm, ströläkt 34×45 (luftspalten), råspont 20, underlagspapp och
bandtäckt zink-magnesiumplåt 0,6. Plåten ligger i banor 525 mm breda längs takfallet, med stående falsar 25 mm
höga mellan banorna (halva falsen på var bana) och lika breda kantbanor vid gavlarna. Ströläkten ligger på varje
takbalk och takstol och två mellan i varje fack (så att hårdboarden inte trycks upp mot råsponten när isoleringen
blåses in), med uppehåll 600 mm ovanför och nedanför takfönstren (U-03). Skikten slutar lodrätt i nock- och
dallinjerna och i gavlarnas fasadliv. Vid takfoten slutar hårdboarden på isolerstoppet i ytterväggens liv
(isolering.py), ströläkten vid takbalkarnas ände och råsponten, pappen och plåten 20 mm utanför den.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Sequence

from modellering import Del, Material, Montage, Placering, lada

from trebodar import skelett as S
from trebodar.byggdelar import lagen
from trebodar.byggdelar import taklager as L
from trebodar.byggdelar.regelvagg import Plan
from trebodar.byggdelar.virke import fmt
from trebodar.hus.stomme.prefab.takbalkar.takbalkar import FALT, Takfonster
from trebodar.material import C24_LAKT, GLAS, HDF, KARM, PAPP, RASPONT, TAKPLAT


@dataclass(frozen=True)
class Region:
    y0: float
    y1: float
    nedre: L.Kant                    # takfot eller dal
    nock: L.Kant
    ande: bool = False               # vid dalens ände: under grannkroppens gavelutstick, där ändlådan sitter


def _f(kropp: int) -> tuple[float, float]:
    k = S.HUSKROPPAR[kropp]
    return k.y0 - S.STOMME_UT - S.T_FASAD, k.y1 + S.STOMME_UT + S.T_FASAD


def _lodr(x: float) -> L.Kant:
    return L.Kant("lodratt", x)


Y1, Y2, Y3 = _f(1), _f(2), _f(3)
DB4, DB2 = S.BALKAR["DB4"].x, S.BALKAR["DB2"].x
NOCK = {k: S.HUSKROPPAR[k].nock for k in (1, 2, 3)}
G = L.GAVEL_UT


def _takfall(kod: str, *delar: tuple[float, float, float, bool]) -> list[Region]:
    """Takfallets regioner (y0, y1, nedre kant, vid dalens ände) upp till nocken."""
    return [Region(y0, y1, _lodr(x), _lodr(NOCK[S.TAKFALL[kod].kropp]), ande) for y0, y1, x, ande in delar]


# Vid dalarnas ändar går den längre kroppens dalregion gavelutsticket ut förbi den kortare kroppens gavel (ande), så
# att takfoten och rännan slutar där och dalens ändlåda (takkanter.py) får plats under den kortare kroppens utstick.
REGIONER = {
    "1SO": _takfall("1SO", (Y1[0], Y1[1], FALT["1SO"].takfot, False)),
    "1NV": _takfall("1NV", (Y1[0], Y2[1], DB4, False), (Y2[1], Y2[1] + G, DB4, True),
                    (Y2[1] + G, Y1[1], FALT["1NV"].takfot, False)),
    "2SO": _takfall("2SO", (Y2[0], Y1[0] - G, FALT["2SO"].takfot, False), (Y1[0] - G, Y1[0], DB4, True),
                    (Y1[0], Y2[1], DB4, False)),
    "2NV": _takfall("2NV", (Y2[0], Y3[0] - G, FALT["2NV"].takfot, False), (Y3[0] - G, Y3[0], DB2, True),
                    (Y3[0], Y2[1], DB2, False)),
    "3SO": _takfall("3SO", (Y3[0], Y2[1], DB2, False), (Y2[1], Y2[1] + G, DB2, True),
                    (Y2[1] + G, Y3[1], FALT["3SO"].takfot, False)),
    "3NV": _takfall("3NV", (Y3[0], Y3[1], FALT["3NV"].takfot, False)),
}


def tak_underkant(x: float, y: float) -> float | None:
    """Takets hårdboards undersida (takbalkarnas överkant) i punkten (x, y), om taket täcker den."""
    z = []
    for kod, rs in REGIONER.items():
        t = S.TAKFALL[kod]
        for r in rs:
            xa, xb = sorted((r.nedre.x, r.nock.x))
            if r.y0 - 1e-6 <= y <= r.y1 + 1e-6 and xa - 1e-6 <= x <= xb + 1e-6:
                z.append(t.z_overkant(x))
    return min(z) if z else None


OMLUFT = 600.0               # uppehåll i ströläkten ovanför och nedanför takfönstren, längs takfallet (U-03)
FALS_CC = 525.0              # plåtbanornas bredd (falsarnas delning längs y)
FALS_B = 8.0                 # falsens bredd, hälften på var bana
FALS_FRI = 30.0              # falsarna minst så långt från fönstrens och regionernas kanter
assert dict(TAKPLAT.rendering)["avstand"] == FALS_CC         # renderingens banor

SKIKT = (("Hårdboard", "HD", L.HARDBOARD, HDF), ("Råspont", "RP", L.RASPONT, RASPONT),
         ("Underlagspapp", "UP", L.PAPP, PAPP), ("Takplåt", "TP", L.PLAT, TAKPLAT))


def kant_takfot(kod: str) -> float:
    """Råspontens, pappens och plåtens kant vid takfoten (x): RASPONT_UT utanför takbalkarnas ände."""
    return FALT[kod].takfot - S.TAKFALL[kod].riktning * L.RASPONT_UT


def _dalens_slut(x_dal: float, kropp: int) -> float:
    """Där en dal slutar mot kroppens gavel slutar utsticket över gaveln vid dalens ändlåda (takkanter.py)."""
    return x_dal + math.copysign(L.DALANDE_B, S.HUSKROPPAR[kropp].nock - x_dal)


def regioner(kod: str, typ: str) -> list[Region]:
    """Skiktets regioner. Vid takfoten slutar hårdboarden i ytterväggens liv (isolerstoppet) och råsponten, pappen
    och plåten RASPONT_UT utanför takbalkarnas ände. Vid gavlarna går råsponten, pappen och plåten ut till vindskivan
    (GAVEL_UT); där en dal slutar mot en gavel slutar utsticket vid dalens ändlåda. Vid dalens ände (ande) slutar
    hårdboarden i väggens liv som vid takfoten och de andra skikten i dallinjen, mot ändlådan."""
    t, f = S.TAKFALL[kod], FALT[kod]
    tackning = typ in ("RP", "UP", "TP")
    x = t.x_utsida if typ == "HD" else kant_takfot(kod) if tackning else f.takfot
    # i dalarna slutar pappen och plåten vid rändalen (takkanter.py)
    xd = t.riktning * L.RANDAL_B if typ in ("UP", "TP") else 0.0
    rs = [Region(r.y0, r.y1, _lodr(x), r.nock) if r.nedre.x == f.takfot else
          Region(r.y0, r.y1, _lodr(t.x_utsida if typ == "HD" else r.nedre.x), r.nock, True) if r.ande else
          Region(r.y0, r.y1, _lodr(r.nedre.x + xd), r.nock) for r in REGIONER[kod]]
    if not tackning:
        return rs
    g = L.GAVEL_UT - L.VINDSKIVA[0]
    y0, y1 = min(r.y0 for r in rs), max(r.y1 for r in rs)
    ut = list(rs)
    for r in rs:
        for kant, (a, b) in ((r.y0, (r.y0 - g, r.y0)), (r.y1, (r.y1, r.y1 + g))):
            if kant in (y0, y1):
                nedre = r.nedre if r.nedre.x == x else _lodr(_dalens_slut(r.nedre.x - xd, t.kropp))
                ut.append(Region(a, b, nedre, r.nock))
    return ut


def _skiva(t: S.Takfall, kod: str, namn: str, typ: str, w: tuple[float, float], material: Material,
           fonster: tuple[Takfonster, ...], falsar: Sequence[float] = ()) -> Montage:
    """Skiktet i bitar: y-intervall mellan regionernas kanter, fönstren (vid fönstren en bit nedanför och en
    ovanför öppningen) och falsarna (plåtbanor med halva falsen vid de kanter som är falsar)."""
    p = Plan(kod, f"{namn} {kod}", 1.0, beskrivning=material.beskrivning, material=material)
    for r in regioner(kod, typ):
        fo = [f for f in fonster if r.y0 < f.y0 < r.y1]
        fs = {y for y in falsar if r.y0 < y < r.y1}
        ys = sorted({r.y0, r.y1, *(f.y0 for f in fo), *(min(f.y1, r.y1) for f in fo), *fs})
        for a, b in zip(ys, ys[1:]):
            f = next((f for f in fo if f.y0 <= a and b <= f.y1), None)
            kanter = [(r.nedre, r.nock)] if f is None else [(r.nedre, L.Kant("vinkelrat", f.x_ned)),
                                                           (L.Kant("vinkelrat", f.x_upp), r.nock)]
            for k0, k1 in kanter:
                q = L.profil(t, *w, k0, k1)
                if not q:
                    continue
                if not falsar:
                    p.profil(q, a, b, typ=typ)
                    continue
                # banan: delens z går från b (0) mot a; halva falsen vid de kanter som är falsar
                fals = L.profil(t, *L.FALS, k0, k1)
                h = min(FALS_B / 2, b - a)
                tillagg = [(fals, z0, h) for z0, kant in ((0.0, b), (b - a - h, a)) if fals and kant in fs]
                p.profil(q, a, b, typ=typ, tillagg=tillagg, bas_namn=f"{namn} bana {fmt(b - a)}")
    return p.montage()


def _falsar(kod: str, fonster: tuple[Takfonster, ...]) -> list[float]:
    """Falsarnas lägen (y) i takfallet: banor FALS_CC breda och lika breda kantbanor vid gavlarna; en fals nära en
    fönsterkant eller en regionkant flyttas FALS_FRI från den."""
    rs = REGIONER[kod]
    y0, y1 = min(r.y0 for r in rs), max(r.y1 for r in rs)
    n = int((y1 - y0) // FALS_CC)
    kant = (y1 - y0 - (n - 1) * FALS_CC) / 2
    hinder = {r.y0 for r in rs} | {r.y1 for r in rs} | {f.y0 for f in fonster} | {f.y1 for f in fonster}
    ut = []
    for k in range(n):
        y = y0 + kant + k * FALS_CC
        for e in sorted(hinder, key=lambda e: abs(e - y)):
            if abs(y - e) < FALS_FRI:
                y = e + FALS_FRI if y >= e else e - FALS_FRI
        ut.append(y)
    return ut


def _takstolar(kropp: int) -> set[float]:
    """Takstolarnas ytterbalkar i huskroppen (lägsta y): på var sida om nocken stolens högsta sneda delar (X), de
    med överkanten i takplanet."""
    nock = S.HUSKROPPAR[kropp].nock
    sidor: dict[tuple[str, bool], list[tuple[float, float]]] = {}
    for grupp, namn, (x0, y0, _, x1, _, z1) in lagen.takstolar():
        if grupp.rsplit(" ", 1)[-1].startswith(str(kropp)) and re.fullmatch(r"\w+-X\d+", namn):
            sidor.setdefault((grupp, x0 + x1 > 2 * nock), []).append((z1, y0))
    return {y0 for ds in sidor.values() for z1, y0 in ds if z1 > max(z for z, _ in ds) - 1.0}


def _lakt_lagen(kod: str) -> list[float]:
    """Ströläktens lägen (lägsta y): på takbalkar och takstolar, två mellan i varje fack (jämnt fördelade)."""
    t = S.TAKFALL[kod]
    stod = sorted(set(FALT[kod].y) | _takstolar(t.kropp))
    ut = list(stod)
    for a, b in zip(stod, stod[1:]):
        if b - a > 90:
            n = max(0, round((b - a) / 200.0) - 1)
            ut += [a + (b - a) * k / (n + 1) for k in range(1, n + 1)]
    return sorted(ut)


def _strolakt(t: S.Takfall, kod: str, fonster: tuple[Takfonster, ...]) -> Montage:
    p = Plan(kod, f"Ströläkt {kod}", 45.0, beskrivning="Ströläkt 34×45 C24 (luftspalten 34 mm)", material=C24_LAKT)
    for y in _lakt_lagen(kod):
        # regionen vid läktens mitt; en läkt som når in över dalens ände slutar där, före ändlådan
        r = next((r for r in REGIONER[kod] if r.ande and r.y0 < y + 45 and y < r.y1), None) or \
            next((r for r in REGIONER[kod] if r.y0 <= y + 22.5 < r.y1), None)
        if r is None:
            continue
        # sträckor längs takfallet: hela, utom vid fönster (öppningen och uppehållen ovanför och nedanför)
        snitt = [(r.nedre, r.nock)]
        for f in fonster:
            if not (f.y0 - OMLUFT < y + 45 and y < f.y1 + OMLUFT and r.y0 < f.y0 < r.y1):
                continue
            inne = f.y0 <= y and y + 45 <= f.y1
            a = L.Kant("vinkelrat", L.langs(t, f.x_ned, -OMLUFT))
            b = L.Kant("vinkelrat", L.langs(t, f.x_ned, 0.0))
            c = L.Kant("vinkelrat", L.langs(t, f.x_upp, 0.0))
            d = L.Kant("vinkelrat", L.langs(t, f.x_upp, OMLUFT))
            snitt = [(r.nedre, a), (b, c), (d, r.nock)] if not inne else [(r.nedre, a), (d, r.nock)]
        for k0, k1 in snitt:
            if (k1.x - k0.x) * t.riktning < 100.0 * S.COS:      # kortare än 100 mm längs takfallet: ingen läkt
                continue
            q = L.profil(t, *L.STROLAKT, k0, k1)
            if q:
                p.profil(q, y, y + 45, typ="SL")
    return p.montage()


def takfall(kod: str) -> Montage:
    t = S.TAKFALL[kod]
    fonster = FALT[kod].fonster
    m = Montage(f"Takfall {kod}", beskrivning=f"Yttertak, {S.HUSKROPPAR[t.kropp].namn}")
    m.lagg(_skiva(t, kod, "Hårdboard", "HD", L.HARDBOARD, HDF, fonster))
    m.lagg(_strolakt(t, kod, fonster))
    for namn, typ, w, mat in SKIKT[1:]:
        m.lagg(_skiva(t, kod, namn, typ, w, mat, fonster, _falsar(kod, fonster) if typ == "TP" else ()))
    return m


def _takplan(t: S.Takfall, x: float, y: float) -> Placering:
    """Takplanets system i punkten (x, y) i takbalkarnas plan: u uppåt längs planet, v längs y (tecken så att
    systemet är högerhänt), w utåt vinkelrätt mot planet."""
    r = t.riktning
    u = (r * S.COS, 0.0, S.SIN)
    v = (0.0, float(r), 0.0)
    w = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
    return Placering(((u[0], v[0], w[0]), (u[1], v[1], w[1]), (u[2], v[2], w[2])), (x, y, t.z_overkant(x)))


def takfonster(kod_falt: str, f: Takfonster) -> Montage:
    """Takfönster i öppningen mellan avväxlingarna och takbalkarna: karm från takbalkarnas underkant till 100 mm
    över plåten och glas, förenklat."""
    t = S.TAKFALL[kod_falt]
    L_ = abs(f.x_upp - f.x_ned) / S.COS
    B = f.y1 - f.y0
    y_start = f.y0 if t.riktning > 0 else f.y1
    p = _takplan(t, f.x_ned, y_start)
    m = Montage(f.kod, f.kod, f"Takfönster {B:g}×{L_:.0f} (förenklat)")
    karm = lada(L_, B, 330.0, (0.0, 0.0, -170.0)) - lada(L_ - 120, B - 120, 330.0, (60.0, 60.0, -170.0))
    m.lagg(Del(f"Takfönster karm {B:g}×{L_:.0f}", karm, KARM), p, f"{f.kod}-KARM")
    m.lagg(Del(f"Takfönster glas {B - 120:g}×{L_ - 120:.0f}", lada(L_ - 120, B - 120, 24.0, (60.0, 60.0, 106.0)),
               GLAS), p, f"{f.kod}-GLAS")
    return m


def montage() -> Montage:
    m = Montage("Tak", beskrivning="Yttertak: hårdboard, ströläkt 34×45, råspont, underlagspapp, plåt (F-01)")
    for kod in ("1SO", "1NV", "2SO", "2NV", "3SO", "3NV"):
        m.lagg(takfall(kod))
    from .takkanter import montage as takkanter
    m.lagg(takkanter())
    tf = Montage("Takfönster")
    for kod, f in FALT.items():
        for fo in f.fonster:
            tf.lagg(takfonster(kod, fo))
    m.lagg(tf)
    return m
