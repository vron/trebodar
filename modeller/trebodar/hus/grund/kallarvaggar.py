"""Källarväggarna V1–V21 (K-05, K-06): Sundolitt Kub 350-150, en armerad betongkärna 150 mm i kvarsittande form av
cellplast 100 mm på var sida. Linjerna är kärnornas centrumlinjer (K-05). Kärnorna gjuts ihop i hörn och
anslutningar (R-05.4 detalj D): i ett hörn går den liggande väggens kärna igenom, i en T-anslutning den genomgående.
Öppningarna (R-05): fönster F1–F3 med betongbröstning och dörrar D1–D3; öppningarnas smyg och bröstning har 100 mm
cellplast.

Höjd: från bottenplattans överkant (z −2 250) till mellanbjälklagets underkant (z −150).
"""
from __future__ import annotations

from dataclasses import dataclass

from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from modellering import Del, Material, Montage, Placering

from trebodar import skelett as S
from trebodar.byggdelar.polygon import polygoner, prisma_ur
from trebodar.material import BETONG, CELLPLAST

Z0, Z1 = -2250.0, -S.H_BJALKLAG
KARNA, CELL = 150.0, 100.0


@dataclass(frozen=True)
class Kallarvagg:
    namn: str
    riktning: str            # "h" längs x, "v" längs y
    c: float                 # kärnans centrumlinje (y för h, x för v)
    a: float
    b: float
    typ: str                 # "yttre" eller "inre"


VAGGAR = [Kallarvagg(*v) for v in (
    ("V1", "h", 12365, 9645, 13665, "yttre"), ("V2", "h", 10865, 4545, 9645, "yttre"),
    ("V3", "h", 9205, 145, 4545, "yttre"), ("V4", "h", 7515, 4545, 5280, "inre"),
    ("V5", "h", 7515, 6380, 7810, "inre"), ("V6", "h", 7515, 8910, 9645, "inre"),
    ("V7", "h", 3735, 145, 4645, "yttre"), ("V8", "h", 1145, 9165, 9540, "yttre"),
    ("V9", "h", 1145, 11240, 13665, "yttre"), ("V10", "h", 145, 4645, 5020, "yttre"),
    ("V11", "h", 145, 6020, 6410, "yttre"), ("V12", "h", 145, 7410, 7990, "yttre"),
    ("V13", "h", 145, 8790, 9165, "yttre"), ("V14", "v", 13665, 1145, 12365, "yttre"),
    ("V15", "v", 9645, 7515, 10865, "inre"), ("V16", "v", 9645, 10865, 12365, "yttre"),
    ("V17", "v", 9165, 145, 1145, "yttre"), ("V18", "v", 4645, 145, 3735, "yttre"),
    ("V19", "v", 4545, 7515, 9205, "inre"), ("V20", "v", 4545, 9205, 10865, "yttre"),
    ("V21", "v", 145, 3735, 9205, "yttre"),
)]
# öppningarna mellan två väggars fria ändar: (namn, vägg före, vägg efter, bröstningens höjd över bottenplattan)
OPPNINGAR = (("F1", "V10", "V11", 1400.0), ("F2", "V11", "V12", 1400.0), ("F3", "V12", "V13", 800.0),
             ("D1", "V8", "V9", 0.0), ("D2", "V4", "V5", 0.0), ("D3", "V5", "V6", 0.0))


def _punkt(v: Kallarvagg, t: float) -> tuple[float, float]:
    return (t, v.c) if v.riktning == "h" else (v.c, t)


def _ande(v: Kallarvagg, t: float) -> str:
    """"hörn" (annan väggs ände i samma punkt), "t" (på en annan väggs linje) eller "fri"."""
    p = _punkt(v, t)
    for w in VAGGAR:
        if w is v:
            continue
        for tw in (w.a, w.b):
            if abs(_punkt(w, tw)[0] - p[0]) < 1 and abs(_punkt(w, tw)[1] - p[1]) < 1:
                return "hörn"
        q = p[1] if w.riktning == "h" else p[0]
        s = p[0] if w.riktning == "h" else p[1]
        if abs(q - w.c) < 1 and w.a + 1 < s < w.b - 1:
            return "t"
    return "fri"


def _rekt(v: Kallarvagg, a: float, b: float, halv: float) -> Polygon:
    return box(a, v.c - halv, b, v.c + halv) if v.riktning == "h" else box(v.c - halv, a, v.c + halv, b)


def _karna(v: Kallarvagg) -> tuple[float, float]:
    """Kärnans utsträckning längs linjen."""
    ut = []
    for t, tecken in ((v.a, -1), (v.b, 1)):
        e = _ande(v, t)
        if e == "hörn":
            ut.append(t + tecken * KARNA / 2 if v.riktning == "h" else t - tecken * KARNA / 2)
        elif e == "t":
            ut.append(t - tecken * KARNA / 2)
        else:
            ut.append(t)
    return ut[0], ut[1]


def _brostningsande(v: Kallarvagg, t: float) -> bool:
    """Änden vid ett fönster med bröstning: kärnan fortsätter som bröstning, smygens cellplast börjar ovanför."""
    return any(zb > 0 and ((va == v.namn and t == v.b) or (vb == v.namn and t == v.a)) for _, va, vb, zb in OPPNINGAR)


def _cellplast_rekt(v: Kallarvagg) -> Polygon:
    ka, kb = _karna(v)
    a = v.a - (KARNA / 2 + CELL) if _ande(v, v.a) != "fri" else ka - (0.0 if _brostningsande(v, v.a) else CELL)
    b = v.b + (KARNA / 2 + CELL) if _ande(v, v.b) != "fri" else kb + (0.0 if _brostningsande(v, v.b) else CELL)
    return _rekt(v, a, b, KARNA / 2 + CELL)


def _yta(namn: str, poly: Polygon, z0: float, z1: float, material: Material) -> Del:
    return Del(namn, prisma_ur(poly, z0, z1), material)


def montage() -> Montage:
    m = Montage("Källarväggar", beskrivning="Sundolitt Kub 350-150: betongkärna 150, cellplast 100 + 100 (K-06)")
    karnor = {v.namn: _rekt(v, *_karna(v), KARNA / 2) for v in VAGGAR}
    alla_karnor = unary_union(list(karnor.values()))
    tagen = Polygon()
    vaggar = {}
    for v in VAGGAR:
        cp = _cellplast_rekt(v).difference(alla_karnor).difference(tagen)
        tagen = tagen.union(cp)
        vaggar[v.namn] = (karnor[v.namn], cp)
    for v in VAGGAR:
        k, cp = vaggar[v.namn]
        g = Montage(v.namn, v.namn, f"Källarvägg {v.namn} ({v.typ}), K-06")
        g.lagg(_yta(f"Betongkärna {v.namn}", k, Z0, Z1, BETONG), Placering(), f"{v.namn}-K")
        for i, p in enumerate(polygoner(cp, 100.0), 1):
            g.lagg(_yta(f"Cellplast {v.namn}-{i}", p, Z0, Z1, CELLPLAST), Placering(), f"{v.namn}-C{i}")
        m.lagg(g)
    # bröstningar under fönstren: kärna mellan väggarnas kärnor, cellplast på sidorna och 100 mm ovanpå
    for namn, va, vb, zb in OPPNINGAR:
        if zb <= 0:
            continue
        A = next(v for v in VAGGAR if v.namn == va)
        B = next(v for v in VAGGAR if v.namn == vb)
        x0, x1 = _karna(A)[1], _karna(B)[0]
        g = Montage(f"Bröstning {namn}", f"{namn}-B", f"Betongbröstning under fönstret {namn} (R-05)")
        g.lagg(_yta(f"Betongbröstning {namn}", _rekt(A, x0, x1, KARNA / 2), Z0, Z0 + zb, BETONG), Placering(),
               f"{namn}-B-K")
        for sida, (h0, h1) in (("U", (-(KARNA / 2 + CELL), -KARNA / 2)), ("I", (KARNA / 2, KARNA / 2 + CELL))):
            r = box(x0, A.c + h0, x1, A.c + h1)
            g.lagg(_yta(f"Cellplast bröstning {namn}-{sida}", r, Z0, Z0 + zb, CELLPLAST), Placering(),
                   f"{namn}-B-C{sida}")
        # smygarnas cellplast ovanför bröstningen
        for i, (s0, s1) in enumerate(((x0, x0 + CELL), (x1 - CELL, x1)), 1):
            g.lagg(_yta(f"Cellplast smyg {namn}-{i}", box(s0, A.c - KARNA / 2 - CELL, s1, A.c + KARNA / 2 + CELL),
                        Z0 + zb, Z1, CELLPLAST), Placering(), f"{namn}-S{i}")
        g.lagg(_yta(f"Cellplast bröstning {namn} ovanpå", box(x0 + CELL, A.c - KARNA / 2 - CELL, x1 - CELL,
                                                               A.c + KARNA / 2 + CELL), Z0 + zb, Z0 + zb + CELL,
                    CELLPLAST), Placering(), f"{namn}-B-CO")
        m.lagg(g)
    return m


def ytterkontur() -> Polygon:
    """Källarens kontur (cellplastens utsida), för bottenplattan."""
    alla = unary_union([_cellplast_rekt(v) for v in VAGGAR] + [_rekt(v, *_karna(v), KARNA / 2) for v in VAGGAR])
    return Polygon(max(getattr(alla, "geoms", [alla]), key=lambda g: g.area).exterior)
