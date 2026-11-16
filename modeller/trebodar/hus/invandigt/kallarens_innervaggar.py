"""Källarens innerväggar KL1–KL12: lätta väggar med stomme 45×95 C24 c/c 600 (syll, reglar och hammarband) och gips
13 på båda sidor, 121 mm, från bottenplattans överkant (z −2 250) till mellanbjälklagets underkant (z −150).

KL12 är en kvartscirkel (användarens skiss): badrummets vägg mot gången, tangent mot KL4 och KL3:s linje, med radien
så stor att pelarna står kvar i väggarna (R 830: P10 i bågens ände, där KL1 och KL11 möter den, och P11 i KL4:s raka
del). Stommen är syll och hammarband sågade i båge ur 45 och reglar 45×95 radiellt c/c 300 längs bågen; gipsen två
lager böjbar gips 6,5 på varje sida (13 som på de andra väggarna). KL3 går från V7 till KL4 och KL11 från P10 till
V4, så att badrummet når ut till bågen.

Väggarna står i rörens linjer, så att rören P4, P6–P14, P16 och P19 döljs i stommen (VKR 80 i regelfacket 95): en
regel som skulle träffa ett rör flyttas till dess sida, och syllen och hammarbandet är avbrutna vid rören. KL8 har
reglar 45×120 (146 mm), eftersom avloppets stam Ø110 från badrummet går ned i dess linje bredvid röret P4. Dörrhålen
KD1–KD5 är för dörrar M9×20 (KD3 M8×20), håltagning 900 (800) × 2 010 för karmen 890 (790) × 1 990, med ett
överstycke under hammarbandet; rumshöjden 2 100 rymmer inte en dörr M×21. Dörrbladen och karmarna finns inte i
modellen.

Rummen: teknikrummet söder om KL8–KL10 (värmepumpen TK-VP står innanför knycken KL9–KL10), hallen mellan KL1 och KL8 med
dörren KD1 till rummet norr om KL1 (väster om KL2; rummet öster om KL2, det framtida badrummet, når man genom KD3 i
KL3), trapphallen öster om KL11 (KD2) mellan KL4 och KL6 med KD4 norrut, med gången innanför bågen KL12, och det stora
rummet i högra huskroppen öster om KL5 och KL7 (KD5).
KL5 börjar vid KL4, eftersom trappan går ut över dess linje söder om den.

Där två väggar möts går den ena igenom (stommen till den andras bortre sida) och den andra slutar mot dess stomme,
med en regel i den genomgående väggen vid anslutningen; mot källarväggarna slutar stommen mot deras gips (kallare.py).
Gipsen är en skiva per väggyta som på källarväggarna (kallare.skivor): i innerhörn går skivan längs x fram till
hörnet, i ytterhörn och runt fria ändar går den förbi och täcker den andras kant. I dörrhålen slutar gipsen vid
regeln (karmen täcker smygen).
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import cache

import math

from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from modellering import Del, Montage, Placering, prisma

from trebodar import skelett as S
from trebodar.byggdelar import polygon as P
from trebodar.byggdelar.regelvagg import Plan
from trebodar.byggdelar.virke import fmt
from trebodar.hus.grund import kallarvaggar as K
from trebodar.hus.grund import pelare as R
from trebodar.material import C24, GIPS

from .kallare import GIPS_T, skivor
from .lattvaggar import T as LATT_T
from .lattvaggar import VAGGAR as LATTA_VAGGAR

T = 95.0                         # stommen (KL8 T_KL8)
T_KL8 = 120.0                    # avloppsstammen Ø110 i stommen
B = 45.0                         # virkets bredd: syll, regel, hammarband och överstycke
CC = 600.0
HOJD = K.Z1 - K.Z0               # 2 100
H_HAL = 2010.0                   # dörrhålens höjd (karm 1 990)
FRIGANG = 5.0                    # mellan rören och virket
_H = T / 2
# avloppets stam genom källaren (hus/installationer/avlopp, Ø110; luftar grundledningen och är dess rensning), i KL8
# öster om röret P4, under badrummets vägg L11 (stommens mitt), så att luftningen går rakt upp i den
AVLOPPSSTAM = (LATTA_VAGGAR["L11"].origo[0] - LATT_T / 2, 7675.0, 110.0)
# badrummets avlopp rakt ned i närmaste källarvägg (användarens kommentar): badkarets i KL1 (under karet, väster om
# dörren KD1:s karmregel), tvättens i KL2 (vattenlåset på L10 rakt ovanför) och duschens golvbrunn i KL8 (röret under
# bjälklaget söderut in i väggen); x, y, Ø (Ø75 där de klenare ökar över källargolvet)
AVLOPP_I_VAGGARNA = {"AV3": (600.0, 5820.0, 75.0),
                     "AV21": (2800.0, LATTA_VAGGAR["L10"].origo[1] + LATT_T / 2, 75.0),
                     "AV4": (2500.0, 7675.0, 75.0)}
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
    Innervagg("KL3", "v", _P["P10"][0], _c("V7") + _GIPSYTA, _P["P11"][1] + _H,
              "från V7 till KL4 i rörets P10 linje, badrummets vägg mot öster"),
    Innervagg("KL4", "h", _P["P11"][1], _P["P10"][0] + _H, _P["P14"][0] - _H,
              "från KL3 till KL5 i rörens P11–P14 linje, norr om trappan"),
    Innervagg("KL5", "v", _P["P14"][0], _c("V8") + _GIPSYTA, _P["P11"][1] + _H,
              "från hörnet V8/V17 till KL4 i rörens P19, P16 och P14 linje"),
    Innervagg("KL6", "h", _P["P6"][1], _P["P6"][0] - R.VKR / 2 - FRIGANG - B, _c("V15") + _H,
              "från rörets P6 västra sida till KL7 i rörens P6 och P7 linje, söder om trappan"),
    Innervagg("KL7", "v", _c("V15"), _P["P6"][1] + _H, _c("V6") - _GIPSYTA, "från KL6 till hörnet V6/V15"),
    Innervagg("KL8", "h", _P["P4"][1], X_KL8, X_KL9 + _H,
              "teknikrummets vägg i rörets P4 och avloppsstammens linje, fri ände i väster", T_KL8),
    Innervagg("KL9", "v", X_KL9, Y_KL10 + _H, _P["P4"][1] - T_KL8 / 2, "knycken väster om värmepumpen"),
    Innervagg("KL10", "h", Y_KL10, X_KL9 - _H, _P["P10"][0] - _H, "teknikrummets vägg norr om värmepumpen till KL11"),
    Innervagg("KL11", "v", _P["P10"][0], _P["P10"][1] - _H, _c("V4") - _GIPSYTA,
              "från P10 (bågen KL12) till hörnet V4/V19 i rörets P10 linje"),
)}
DORRHAL = (
    Dorrhal("KD1", "KL1", 730.0, 1630.0, "M9×20"),
    Dorrhal("KD2", "KL11", 6200.0, 7100.0, "M9×20"),
    Dorrhal("KD3", "KL3", 4040.0, 4840.0, "M8×20"),
    Dorrhal("KD4", "KL4", 5870.0, 6770.0, "M9×20"),
    Dorrhal("KD5", "KL7", 6382.0, 7282.0, "M9×20"),
)



@dataclass(frozen=True)
class Bagvagg:
    """Lätt vägg i en kvartscirkel: centrumlinjen med radien r kring centrum, från vinkeln v0 till v1 (grader)."""
    kod: str
    centrum: tuple[float, float]
    r: float
    v0: float
    v1: float
    beskrivning: str

    def punkt(self, v: float, r: float) -> tuple[float, float]:
        a = math.radians(v)
        return self.centrum[0] + r * math.cos(a), self.centrum[1] + r * math.sin(a)

    def band(self, r0: float, r1: float, n: int = 180) -> Polygon:
        """Ringsektorn mellan radierna r0 och r1 i plan."""
        vs = [self.v0 + (self.v1 - self.v0) * i / n for i in range(n + 1)]
        return Polygon([self.punkt(v, r1) for v in vs] + [self.punkt(v, r0) for v in reversed(vs)])


# KL12: tangent mot KL4 (y P11) och KL3:s linje (x P10); radien så stor att P10 hamnar i bågens ände och P11 i KL4:s
# raka del (en kvartscirkel kan inte gå genom båda pelarna och möta väggarna utan knyck)
R_KL12 = _P["P10"][1] - _P["P11"][1]
BAGE = Bagvagg("KL12", (_P["P10"][0] + R_KL12, _P["P10"][1]), R_KL12, 180.0, 270.0,
               "kvartscirkel från KL4 till P10, badrummets vägg mot gången")
assert BAGE.punkt(270.0, R_KL12)[0] < _P["P11"][0] - R.VKR / 2 - FRIGANG, "P11 i KL4:s raka del"
CC_BAGE = 300.0                  # reglarna längs bågens centrumlinje (böjbar gips)
GIPS_BOJ = 6.5                   # böjbar gips, två lager


def _ror(v: Innervagg) -> list[tuple[float, float]]:
    """Rören och avloppsstammen i väggen: deras utbredning längs u med frigången, sammanslagna."""
    genom = [(namn, x + k * R.VKR, y, R.VKR / 2) for namn, (x, y) in _P.items() for k in range(R.ANTAL.get(namn, 1))]
    genom.append(("avloppsstammen", AVLOPPSSTAM[0], AVLOPPSSTAM[1], AVLOPPSSTAM[2] / 2))
    genom += [(f"avloppet {k}", x, y, d / 2) for k, (x, y, d) in AVLOPP_I_VAGGARNA.items()]
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
def _bagen() -> dict[str, list[Polygon]]:
    """Bågväggens delar i plan: stommens band (syll och hammarband), reglarnas fotavtryck och gipsens lager på
    gångens (inre) och badrummets (yttre) sida. Stommen och gipsen mot badrummet slutar mot de raka väggarnas stomme
    och gips; gipsen mot gången fortsätter tangent förbi deras gips (där deras skivor slutar i stället)."""
    g, h = BAGE, _H
    raka = unary_union([v.stomme() for v in VAGGAR.values()])
    raka_med_gips = raka.buffer(GIPS_T, join_style=2)
    pelaren = box(_P["P10"][0] - R.VKR / 2, _P["P10"][1] - R.VKR / 2, _P["P10"][0] + R.VKR / 2,
                  _P["P10"][1] + R.VKR / 2).buffer(FRIGANG, join_style=2)
    stomme = g.band(g.r - h, g.r + h).difference(raka).difference(pelaren)
    reglar = []
    n = max(2, math.ceil(g.r * math.radians(g.v1 - g.v0) / CC_BAGE))
    for i in range(n + 1):
        v = g.v0 + (g.v1 - g.v0) * i / n
        a, t = math.radians(v), B / 2
        rx, ry, tx, ty = math.cos(a), math.sin(a), -math.sin(a), math.cos(a)
        cx, cy = g.punkt(v, g.r)
        fot = Polygon([(cx + rx * dr + tx * dt, cy + ry * dr + ty * dt) for dr, dt in
                       ((-h, -t), (h, -t), (h, t), (-h, t))])
        if fot.intersection(stomme).area > 0.98 * fot.area:   # helt i bågens egen stomme (bandet är ett polygontåg)
            reglar.append(fot.intersection(stomme))           # regelns hörn inom bandet (gipsen ligger an mot det)
    lager = {}
    for sida, (r0, r1), hinder in (("inre", (g.r - h - GIPS_T, g.r - h), raka),
                                   ("yttre", (g.r + h, g.r + h + GIPS_T), raka_med_gips)):
        for k in range(2):
            band = g.band(r0 + k * GIPS_BOJ, r0 + (k + 1) * GIPS_BOJ).difference(hinder)
            lager[f"{sida}{k + 1}"] = list(P.polygoner(band, 100.0))
    return {"stomme": list(P.polygoner(stomme, 100.0)), "reglar": reglar, **lager}


def _klipp(rekt: tuple[float, ...], hinder: Polygon) -> list[tuple[float, float, float, float]]:
    """En rak gipsskiva i plan (x0, y0, x1, y1) utan det som bågväggen tar: de delar längs skivan som hindret inte når."""
    x0, y0, x1, y1 = rekt
    langs_x = x1 - x0 > y1 - y0
    bit = box(*rekt).intersection(hinder)
    if bit.area < 1.0:
        return [(x0, y0, x1, y1)]
    bx0, by0, bx1, by1 = bit.bounds
    a, b = (x0, x1) if langs_x else (y0, y1)
    ba, bb = (bx0, bx1) if langs_x else (by0, by1)
    ut = []
    for p0, p1 in ((a, ba), (bb, b)):
        if p1 - p0 >= 1.0:
            ut.append((p0, y0, p1, y1) if langs_x else (x0, p0, x1, p1))
    return ut


@cache
def _gips() -> dict[str, list[tuple[float, float, float, float]]]:
    """Gipsskivorna i plan per vägg i dess system: (u0, u1, w0, w1), utan det som bågväggen KL12 tar."""
    stommar = unary_union([v.stomme() for v in VAGGAR.values()])
    kallarvaggar = K.i_plan(K.Z0 + HOJD / 2).buffer(GIPS_T, join_style=2)
    rum = K.ytterkontur().difference(kallarvaggar).difference(stommar)
    agare: list[tuple[str, Polygon, str | None]] = [(v.kod, v.stomme(), v.riktning) for v in VAGGAR.values()]
    bagen = unary_union([q for delar in _bagen().values() for q in delar])
    ut: dict[str, list[tuple[float, float, float, float]]] = {kod: [] for kod in VAGGAR}
    for kod, rekt in skivor(stommar, rum, agare):
        for bit in _klipp(rekt, bagen):
            ut[kod].append(VAGGAR[kod].uw(*bit))
    return ut


def _bagvaggen() -> Montage:
    """KL12: syll och hammarband sågade i båge, reglarna radiellt och två lager böjbar gips på varje sida, i plan."""
    g = BAGE
    m = Montage(f"Vägg {g.kod}", g.kod, g.beskrivning)
    st = Montage("Stomme", beskrivning=f"Syll och hammarband 45 sågade i båge R {fmt(g.r)}, reglar 45×{fmt(T)} "
                                       f"radiellt c/c {fmt(CC_BAGE)}")
    d = _bagen()
    for i, q in enumerate(d["stomme"], start=1):
        for namn, z0 in (("S", K.Z0), ("H", K.Z1 - B)):
            st.lagg(Del(f"Bågsyll 45×{fmt(T)} R {fmt(g.r)}" if namn == "S" else f"Bågformat hammarband 45×{fmt(T)} "
                        f"R {fmt(g.r)}", prisma(P.kontur(q), B, z0=z0), C24), Placering(), f"{g.kod}-{namn}{i:02d}")
    for i, q in enumerate(d["reglar"], start=1):
        st.lagg(Del(f"Regel 45×{fmt(T)} L={fmt(HOJD - 2 * B)}", prisma(list(q.exterior.coords)[:-1], HOJD - 2 * B,
                                                                       z0=K.Z0 + B), C24),
                Placering(), f"{g.kod}-R{i:02d}")
    m.lagg(st)
    gi = Montage("Gips", beskrivning=f"Böjbar gips {fmt(GIPS_BOJ)}, två lager på varje sida")
    i = 0
    for lager in ("inre1", "inre2", "yttre1", "yttre2"):
        for q in d[lager]:
            i += 1
            gi.lagg(Del(f"Böjbar gips {fmt(GIPS_BOJ)} R {fmt(g.r)}", prisma(P.kontur(q), HOJD, z0=K.Z0), GIPS),
                    Placering(), f"{g.kod}-GI{i:02d}")
    m.lagg(gi)
    return m


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
                                                    "rören i stommen, dörrhål för M9×20 och M8×20, en vägg i "
                                                    "kvartscirkel")
    for v in VAGGAR.values():
        g = Montage(f"Vägg {v.kod}", v.kod, v.beskrivning)
        g.lagg(_stomme(v))
        g.lagg(_gipsen(v))
        m.lagg(g, v.placering())
    m.lagg(_bagvaggen())
    return m
