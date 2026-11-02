"""Dalarna mellan huskropparna, vågräta dallinjer längs dalbalkarna DB2 och DB4.

Kilar av plywood på råsponten med fall 1:60 från mitten mot ändarna, som på dallinjen
stiger från noll vid ändarna till högst i mitten och på sidorna går ned till råsponten 300 mm ut, och en rändal av
plåt på underlagspapp över kilarna och remsan; takets papp och plåt slutar vid rändalen. Dalarna slutar vid den
kortare kroppens gavel, där dallinjen ligger i den längre kroppens fasadliv. Där tar en ändlåda av plåt emot vattnet:
105 × 100 i hörnet mellan fasaderna under gavelutsticket, botten 40 mm under dalens botten och en rörstos Ø75 falsad
i botten med eget stuprör Ø75 ned i hörnet, 20 mm från båda fasaderna (plåtslagarens detalj). Rändalen, den kortare
kroppens utstick och den längre kroppens tak viks ned i lådan; lådans yttre kant är 30 mm hög, lägre än de andra,
så att vattnet rinner över den och ut från huset om stosen sätts igen. Den längre kroppens takfot och ränna slutar
vid gavelutstickets kant (takytor.py, ande) och rännans stuprör sitter i dess andra ände.
"""
from __future__ import annotations

import math

from modellering import Del, Form, Montage, Placering, Union, box, polyeder

from trebodar import skelett as S
from trebodar.byggdelar import taklager as L
from trebodar.byggdelar.polygon import prisma_y
from trebodar.byggdelar.ror import ror, stang
from trebodar.byggdelar.virke import fmt
from trebodar.hus.fasad.markniva import mark_vid
from trebodar.material import PLYWOOD, TAKPLAT

from .takkanter import STUPROR_MARK
from .takytor import REGIONER

LADA_DJUP = 40.0             # dalens ändlåda: botten under dalens botten
LADA_BRADD = 30.0            # ändlådans yttre kant (bräddavlopp), lägre än de andra kanterna
STOS_D, STOS_L = 75.0, 80.0  # rörstosen i ändlådans botten (och dalens stuprör)
STOS_FRI = 20.0              # rörstosens och dalens stuprörs avstånd från fasaderna i hörnet


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
def randal(dal: str) -> Montage:
    """Kilarna, rändalens papp och plåt i dalen längs balken dal."""
    b = S.BALKAR[dal]
    sidor = [(kod, r) for kod, rs in REGIONER.items() for r in rs if r.nedre.x == b.x and not r.ande]
    y0, y1 = min(r.y0 for _, r in sidor), max(r.y1 for _, r in sidor)
    ym, h = (y0 + y1) / 2, (y1 - y0) / 2 * L.RANDAL_FALL
    kilar: list[Form] = []
    ytor: list[tuple[Punkt, Punkt, Punkt]] = []
    for kod in sorted({k for k, _ in sidor}):
        t = S.TAKFALL[kod]
        xv, xw = b.x, b.x + t.riktning * L.RANDAL_B

        def z(x: float) -> float:
            return L.z_skikt(t, x, L.RASPONT[1])
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
    for n, (ye, s) in enumerate(((y0, -1.0), (y1, 1.0)), 1):
        for typ, d in _dalens_ande(dal, ye, s):
            m.lagg(d, Placering(), f"{dal}-{typ}{n}")
    return m
def _dalens_ande(dal: str, ye: float, s: float) -> list[tuple[str, Del]]:
    """Dalens ände vid den kortare kroppens gavel (fasadlivet ye, utåt s = ±1): ändlådan (LA) i hörnet under
    gavelutsticket, rörstosen (RS) i dess botten och stupröret (ST) ned i hörnet."""
    xd = S.BALKAR[dal].x
    langre = {kod for kod, rs in REGIONER.items() for r in rs
              if r.ande and r.nedre.x == xd and abs((r.y1 if s < 0 else r.y0) - ye) < 1e-6}
    kort = next(kod for kod, rs in REGIONER.items() for r in rs if r.nedre.x == xd and kod not in langre)
    t = S.TAKFALL[kort]
    sida = math.copysign(1.0, S.HUSKROPPAR[t.kropp].nock - xd)       # mot den kortare kroppen

    def X(u: float) -> float:
        return xd + sida * u

    def Y(v: float) -> float:
        return ye + s * v

    def ruta(u0: float, u1: float, v0: float, v1: float, z0: float, z1: float) -> Form:
        (xa, xb), (ya, yb) = sorted((X(u0), X(u1))), sorted((Y(v0), Y(v1)))
        return box(xa, xb, ya, yb, z0, z1)
    B, G = L.DALANDE_B, L.GAVEL_UT
    zv = L.z_skikt(t, xd, L.PLAT[1])                  # plåtens överkant i dallinjen (båda takfallen)
    zk = L.z_skikt(t, X(B), L.PLAT[1])                # den kortare kroppens plåt vid lådans sida
    zb = zv - LADA_DJUP
    xs, ys = X(STOS_D / 2 + STOS_FRI), Y(STOS_D / 2 + STOS_FRI)
    botten = ruta(0.0, B, 0.0, G, zb, zb + L.PLAT_T) - stang((xs, ys, zb - 1.0), (xs, ys, zb + L.PLAT_T + 1.0), STOS_D)
    ya, yb = sorted((Y(0.0), Y(L.PLAT_T)))
    lada = Union((botten,
                  ruta(0.0, L.PLAT_T, 0.0, G, zb, zv),                   # mot den längre kroppens tak
                  ruta(B - L.PLAT_T, B, 0.0, G, zb, zk),                 # mot den kortare kroppens utstick
                  ruta(0.0, B, G - L.PLAT_T, G, zb, zb + LADA_BRADD),    # yttre kanten, bräddavlopp
                  prisma_y([(X(0.0), zb), (X(B), zb), (X(B), zk), (X(0.0), zv)], ya, yb)))     # mot rändalen
    # marken vid stupröret: den högsta vid de två fasaderna i hörnet
    gavel = next(k for k, v in S.YTTERVAGGAR.items() if k[0] == str(t.kropp) and k not in S.TAKFALL
                 and abs(v.placering().punkt((0.0, -S.T_FASAD, 0.0))[1] - ye) < 1.0)
    z_mark = max(mark_vid(k, S.YTTERVAGGAR[k].placering().invers().punkt((xs, ys, 0.0))[0])
                 for k in (gavel, *langre))
    za = zb - STOS_L
    return [("LA", Del(f"Dalens ändlåda {fmt(B)}×{fmt(G)}, plåt 0,6", lada, TAKPLAT)),
            ("RS", Del(f"Rörstos Ø{fmt(STOS_D)}", ror((xs, ys, zb + L.PLAT_T), (xs, ys, za), STOS_D, L.PLAT_T), TAKPLAT)),
            ("ST", Del(f"Stuprör Ø{fmt(STOS_D)} L={fmt(za - z_mark - STUPROR_MARK)}",
                       ror((xs, ys, za), (xs, ys, z_mark + STUPROR_MARK), STOS_D, L.PLAT_T), TAKPLAT))]


def montage() -> Montage:
    m = Montage("Dalar", beskrivning="Kilar, rändalar och ändlådor med rörstos och stuprör")
    for dal in ("DB2", "DB4"):
        m.lagg(randal(dal))
    return m
