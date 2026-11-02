"""Källarens innerväggar KL1–KL10: lätta väggar med stomme 45×95 C24 c/c 600 (syll, reglar och hammarband) och gips
13 på båda sidor, 121 mm, från bottenplattans överkant (z −2 250) till mellanbjälklagets underkant (z −150).

Väggarna står i rörens linjer, så att rören P4, P6–P14, P16 och P19 döljs i stommen (VKR 80 i regelfacket 95): en
regel som skulle träffa ett rör flyttas till dess sida, och syllen och hammarbandet är avbrutna vid rören. KL8 har
reglar 45×120 (146 mm), eftersom avloppets stam Ø110 från badrummet går ned i dess linje bredvid röret P4. Dörrhålen
KD1–KD5 är för dörrar M9×20 (KD3 M8×20), håltagning 900 (800) × 2 010 för karmen 890 (790) × 1 990, med ett
överstycke under hammarbandet; rumshöjden 2 100 rymmer inte en dörr M×21. Dörrbladen och karmarna finns inte i
modellen.

Rummen: teknikrummet norr om KL8–KL10 (värmepumpen TK-VP står innanför knycken KL9–KL10), hallen mellan KL1 och KL8 med
dörren KD1 till rummet söder om KL1 (väster om KL2; rummet öster om KL2 når man genom KD3 i KL3), trapphallen öster
om KL3 (KD2) mellan KL4 och KL6 med KD4 söderut, och det stora rummet i högra huskroppen öster om KL5 och KL7 (KD5).
KL5 börjar vid KL4, eftersom trappan går ut över dess linje norr om den.

Där två väggar möts går den ena igenom (stommen till den andras bortre sida) och den andra slutar mot dess stomme,
med en regel i den genomgående väggen vid anslutningen; mot källarväggarna slutar stommen mot deras gips (kallare.py).
Gipsen är en skiva per väggyta som på källarväggarna (kallare.skivor): i innerhörn går skivan längs x fram till
hörnet, i ytterhörn och runt fria ändar går den förbi och täcker den andras kant. I dörrhålen slutar gipsen vid
regeln (karmen täcker smygen).
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import cache

from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from modellering import Montage, Placering

from trebodar import skelett as S
from trebodar.byggdelar import polygon as P
from trebodar.byggdelar.regelvagg import Plan
from trebodar.byggdelar.virke import fmt
from trebodar.hus.grund import kallarvaggar as K
from trebodar.hus.grund import pelare as R
from trebodar.material import GIPS

from .kallare import GIPS_T, skivor

T = 95.0                         # stommen (KL8 T_KL8)
T_KL8 = 120.0                    # avloppsstammen Ø110 i stommen
B = 45.0                         # virkets bredd: syll, regel, hammarband och överstycke
CC = 600.0
HOJD = K.Z1 - K.Z0               # 2 100
H_HAL = 2010.0                   # dörrhålens höjd (karm 1 990)
FRIGANG = 5.0                    # mellan rören och virket
_H = T / 2
# avloppets stam från badrummet ned genom källaren (avloppssystem.bbrep, Ø110), i KL8 öster om röret P4
AVLOPPSSTAM = (3040.0, 7675.0, 110.0)
_GIPSYTA = K.KARNA / 2 + K.CELL + GIPS_T     # källarväggarnas gipsyta från kärnans centrumlinje


def _c(namn: str) -> float:
    return next(v.c for v in K.VAGGAR if v.namn == namn)


@dataclass(frozen=True)
class Innervagg:
    kod: str
    riktning: str                # "h" längs x, "v" längs y
    c: float                     # centrumlinjen (y för h, x för v)
    a: float                     # stommen längs linjen, a < b
    b: float
    beskrivning: str
    t: float = T                 # stommens tjocklek

    @property
    def h(self) -> float:
        return self.t / 2

    @property
    def langd(self) -> float:
        return self.b - self.a

    @property
    def vagg(self) -> S.Vaggdef:
        """Väggens system: u från a längs linjen, w genom stommen (0–t)."""
        if self.riktning == "h":
            return S.Vaggdef(self.kod, (self.a, self.c - self.h), (1.0, 0.0), self.langd, self.t, self.beskrivning)
        return S.Vaggdef(self.kod, (self.c + self.h, self.a), (0.0, 1.0), self.langd, self.t, self.beskrivning)

    def placering(self) -> Placering:
        return Placering.flytt(0.0, 0.0, K.Z0) @ self.vagg.placering()

    def stomme(self) -> Polygon:
        """Stommen i plan."""
        if self.riktning == "h":
            return box(self.a, self.c - self.h, self.b, self.c + self.h)
        return box(self.c - self.h, self.a, self.c + self.h, self.b)

    def uw(self, x0: float, y0: float, x1: float, y1: float) -> tuple[float, float, float, float]:
        """Rektangeln i plan i väggens system: (u0, u1, w0, w1)."""
        if self.riktning == "h":
            return x0 - self.a, x1 - self.a, y0 - (self.c - self.h), y1 - (self.c - self.h)
        return y0 - self.a, y1 - self.a, self.c + self.h - x1, self.c + self.h - x0


@dataclass(frozen=True)
class Dorrhal:
    kod: str
    vagg: str
    a: float                     # hålet längs väggens linje (x eller y)
    b: float
    dorr: str                    # dörrens modul


# x-värdet för KL2 och KL9 och KL8:s fria ände efter skissen i ärendet; KL9 60 mm från värmepumpen
X_KL2, X_KL9, X_KL8 = 2800.0, 3600.0, 2400.0
Y_KL10 = _c("V4") - _GIPSYTA - _H - GIPS_T            # gipsen mot V4/V19:s hörn i liv med dess gips
_P = R.PELARE
VAGGAR = {v.kod: v for v in (
    Innervagg("KL1", "h", _P["P8"][1], _c("V21") + _GIPSYTA, _P["P10"][0] - _H,
              "från V21 till KL3 i rörens P8–P10 linje"),
    Innervagg("KL2", "v", X_KL2, _c("V7") + _GIPSYTA, _P["P8"][1] - _H, "från V7 till KL1"),
    Innervagg("KL3", "v", _P["P10"][0], _c("V7") + _GIPSYTA, _c("V4") - _GIPSYTA,
              "från V7 till hörnet V4/V19 i rörets P10 linje"),
    Innervagg("KL4", "h", _P["P11"][1], _P["P10"][0] + _H, _P["P14"][0] - _H,
              "från KL3 till KL5 i rörens P11–P14 linje, söder om trappan"),
    Innervagg("KL5", "v", _P["P14"][0], _c("V8") + _GIPSYTA, _P["P11"][1] + _H,
              "från hörnet V8/V17 till KL4 i rörens P19, P16 och P14 linje"),
    Innervagg("KL6", "h", _P["P6"][1], _P["P6"][0] - R.VKR / 2 - FRIGANG - B, _c("V15") + _H,
              "från rörets P6 västra sida till KL7 i rörens P6 och P7 linje, norr om trappan"),
    Innervagg("KL7", "v", _c("V15"), _P["P6"][1] + _H, _c("V6") - _GIPSYTA, "från KL6 till hörnet V6/V15"),
    Innervagg("KL8", "h", _P["P4"][1], X_KL8, X_KL9 + _H,
              "teknikrummets vägg i rörets P4 och avloppsstammens linje, fri ände i väster", T_KL8),
    Innervagg("KL9", "v", X_KL9, Y_KL10 + _H, _P["P4"][1] - T_KL8 / 2, "knycken väster om värmepumpen"),
    Innervagg("KL10", "h", Y_KL10, X_KL9 - _H, _P["P10"][0] - _H, "teknikrummets vägg söder om värmepumpen till KL3"),
)}
DORRHAL = (
    Dorrhal("KD1", "KL1", 730.0, 1630.0, "M9×20"),
    Dorrhal("KD2", "KL3", 6200.0, 7100.0, "M9×20"),
    Dorrhal("KD3", "KL3", 4040.0, 4840.0, "M8×20"),
    Dorrhal("KD4", "KL4", 5870.0, 6770.0, "M9×20"),
    Dorrhal("KD5", "KL7", 6382.0, 7282.0, "M9×20"),
)


def _ror(v: Innervagg) -> list[tuple[float, float]]:
    """Rören och avloppsstammen i väggen: deras utbredning längs u med frigången, sammanslagna."""
    genom = [(namn, x + k * R.VKR, y, R.VKR / 2) for namn, (x, y) in _P.items() for k in range(R.ANTAL.get(namn, 1))]
    genom.append(("avloppsstammen", AVLOPPSSTAM[0], AVLOPPSSTAM[1], AVLOPPSSTAM[2] / 2))
    ut: list[tuple[float, float]] = []
    for namn, x, y, r in genom:
        langs, tvars = (x, y) if v.riktning == "h" else (y, x)
        if not (v.a < langs < v.b and abs(tvars - v.c) < v.h):
            continue
        assert abs(tvars - v.c) + r <= v.h, f"{namn} ryms inte i {v.kod}"
        u = langs - v.a
        ut.append((u - r - FRIGANG, u + r + FRIGANG))
    ut.sort()
    sammanslagna: list[tuple[float, float]] = []
    for a, b in ut:
        if sammanslagna and a <= sammanslagna[-1][1]:
            sammanslagna[-1] = (sammanslagna[-1][0], max(b, sammanslagna[-1][1]))
        else:
            sammanslagna.append((a, b))
    return sammanslagna


def _hal(v: Innervagg) -> list[tuple[float, float]]:
    return [(d.a - v.a, d.b - v.a) for d in DORRHAL if d.vagg == v.kod]


def _anslutningar(v: Innervagg) -> list[float]:
    """Mitten (u) av de väggar som slutar mot den här väggens sida mellan dess ändar."""
    ut = []
    for o in VAGGAR.values():
        if o.riktning == v.riktning or not any(abs(e - (v.c + s * v.h)) < 1e-6 for e in (o.a, o.b) for s in (-1, 1)):
            continue
        if v.a + o.t < o.c < v.b - o.t:
            ut.append(o.c - v.a)
    return ut


def _sträckor(L: float, bort: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Sträckorna av 0–L utanför `bort`, utan stumpar kortare än virkets bredd."""
    rest = box(0.0, 0.0, L, 1.0).difference(unary_union([box(a, -1.0, b, 2.0) for a, b in bort] or [Polygon()]))
    return [(q.bounds[0], q.bounds[2]) for q in P.polygoner(rest) if q.bounds[2] - q.bounds[0] >= B]


def _reglar(v: Innervagg) -> list[float]:
    """Reglarnas början (u): ändarna, dörrhålens sidor, anslutningarna och c/c 600; vid ett rör vid dess sida, i
    dörrhålen inga."""
    L, hal, ror = v.langd, _hal(v), _ror(v)
    lagen: list[float] = []
    kandidater = ([0.0, L - B] + [a - B for a, _ in hal] + [b for _, b in hal] + [j - B / 2 for j in _anslutningar(v)]
                  + [k * CC for k in range(1, int(L // CC) + 1)])
    for u in kandidater:
        for a, b in ror:
            if u + B > a and u < b:
                sidor = [n for n in (a - B, b) if -1e-6 <= n <= L - B + 1e-6]
                u = min(sidor, key=lambda n: abs(n - u)) if sidor else -1.0
        if (-1e-6 <= u <= L - B + 1e-6 and all(u + B <= a + 1e-6 or u >= b - 1e-6 for a, b in hal + ror)
                and all(abs(u - n) >= B - 1e-6 for n in lagen)):
            lagen.append(u)
    return sorted(lagen)


def _stomme(v: Innervagg) -> Montage:
    p = Plan(v.kod, "Stomme", v.t, HOJD, beskrivning=f"45×{fmt(v.t)} C24 c/c 600, syll och hammarband")
    hal, ror = _hal(v), _ror(v)
    for a, b in _sträckor(v.langd, hal + ror):
        p.syll(a, b)
    for a, b in _sträckor(v.langd, ror):
        p.hammarband(a, b)
    for u in _reglar(v):
        p.regel(u)
    for a, b in hal:
        p.liggande(a, b, H_HAL)
    return p.montage()


@cache
def _gips() -> dict[str, list[tuple[float, float, float, float]]]:
    """Gipsskivorna i plan per vägg i dess system: (u0, u1, w0, w1)."""
    stommar = unary_union([v.stomme() for v in VAGGAR.values()])
    kallarvaggar = K.i_plan(K.Z0 + HOJD / 2).buffer(GIPS_T, join_style=2)
    rum = K.ytterkontur().difference(kallarvaggar).difference(stommar)
    agare: list[tuple[str, Polygon, str | None]] = [(v.kod, v.stomme(), v.riktning) for v in VAGGAR.values()]
    ut: dict[str, list[tuple[float, float, float, float]]] = {kod: [] for kod in VAGGAR}
    for kod, rekt in skivor(stommar, rum, agare):
        ut[kod].append(VAGGAR[kod].uw(*rekt))
    return ut


def _gipsen(v: Innervagg) -> Montage:
    p = Plan(v.kod, "Gips", v.t, HOJD, beskrivning="Gips 13 på båda sidor")
    hal = unary_union([box(a, -1.0, b, H_HAL) for a, b in _hal(v)] or [Polygon()])
    for u0, u1, w0, w1 in _gips()[v.kod]:
        yta = box(u0, 0.0, u1, HOJD)
        if w1 <= 1e-6 or w0 >= v.t - 1e-6:                 # väggens sidor; ändarnas skivor täcker stommen
            yta = yta.difference(hal)
        for q in P.polygoner(yta, 100.0):
            namn = f"Gips 13 {fmt(u1 - u0)}×{fmt(HOJD)}" + (" med dörrhål" if q.area < yta.envelope.area - 1 else "")
            p.skiva(P.kontur(q), [], w0, w1, "GI", GIPS, namn)
    return p.montage()


def montage() -> Montage:
    m = Montage("Källarens innerväggar", beskrivning="Lätta väggar 45×95 C24 c/c 600 med gips 13 på båda sidor, "
                                                    "rören i stommen, dörrhål för M9×20 och M8×20")
    for v in VAGGAR.values():
        g = Montage(f"Vägg {v.kod}", v.kod, v.beskrivning)
        g.lagg(_stomme(v))
        g.lagg(_gipsen(v))
        m.lagg(g, v.placering())
    return m
