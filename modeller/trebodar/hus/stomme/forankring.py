"""Stommens förankring i mellanbjälklaget (#88): betongbultar genom syllarna ned i plattan.

Varje syll på plattan har en bult högst KANT_SYLL från vardera änden och högst CC isär, i facken mellan reglarna
(bulten dras uppifrån). I innerväggarna sitter bulten i syllens mitt. Ytterväggarnas syll står 30 mm utanför plattans
kant (K-05), så där sitter bulten FRAN_INSIDAN från syllens insida: kantavståndet till betongen blir då 45 mm. Vid
plattan på marks fria kanter står syllen på L-elementens rygg av cellplast, och en bult genom den når inte betongen:
där läggs ingen bult (utan_betong).
Bultarna borras efter gjutningen, minst FRITT från alla rör i plattan (elens, tappvattnets med hylsorna, avloppets
och golvvärmens): bulten flyttas längs syllen till närmaste fria läge i ett fack. AR-03.4 visar dem, och gjutningens
kontroll prövar avståndet.
"""
from __future__ import annotations

from functools import cache
from typing import Any

import numpy as np

from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

from modellering import Del, Montage, Placering, cylinder

from trebodar import skelett as S
from trebodar.material import BETONGBULT
from trebodar.hus.grund.grund import hornutkap, markplatta
from trebodar.hus.installationer.avlopp.ledningar import ledningar as avloppets
from trebodar.hus.installationer.el.installation import installation
from trebodar.hus.installationer.golvvarme.system import golvvarme
from trebodar.hus.installationer.vatten.system import vatten
from trebodar.hus.stomme import lagen

CC = 1200.0                 # bultarna högst så långt isär längs syllen [mm]
KANT_SYLL = 300.0           # och högst så långt från syllens ände
FRAN_INSIDAN = 20.0         # ytterväggarnas bult från syllens insida [mm]
FRITT_REGEL = 25.0          # bulten minst så långt från en regel (brickan och mutterdragaren)
D, DJUP, OVER = 12.0, 90.0, 15.0     # bultens diameter, djup i betongen och utstick över syllen (bricka och mutter)
FRITT = 50.0                # bulten minst så långt från rören i plattan [mm] (som AR-03.4:s gröna)


def _stycken(vag: Any, r: float) -> list[Any]:
    """Rörets delar i plattan (z −150 … 0) i plan, med radien r."""
    ut = []
    pts = list(vag)
    for a, b in zip(pts, pts[1:]):
        if min(a[2], b[2]) - r < 0.0 and max(a[2], b[2]) + r > -S.H_BJALKLAG:
            g = LineString([a[:2], b[:2]]) if abs(a[0] - b[0]) + abs(a[1] - b[1]) > 1.0 else Point(a[0], a[1])
            ut.append(g.buffer(r))
    return ut


@cache
def ror_i_plattan() -> Any:
    """Alla rör i mellanbjälklaget i plan (med sina radier): elens, tappvattnets (hylsorna), avloppets och
    golvvärmens."""
    g: list[Any] = []
    el = installation()
    for er in el.ror.values():
        g += _stycken(el.mittlinje(er), er.typ.ytterdiameter / 2)
    v = vatten()
    hylsor = {r: d for r, _, _, d in v.hylsor()}
    for vr in v.ror.values():
        g += _stycken(v.vag(vr), hylsor.get(vr.id, vr.typ.yttre) / 2)
    for led in avloppets().values():
        g += _stycken(led.vag, led.d / 2)
    utdrag: Any = golvvarme().utdrag()
    kretsar: dict[str, Any] = utdrag["kretsar"]
    for kr in kretsar.values():
        g += _stycken(kr["vag"], 10.0)
    return unary_union(g)


@cache
def betongen() -> Any:
    """Mellanbjälklagets betong i plan: vid plattan på marks fria kanter slutar den vid L-elementens rygg."""
    return Polygon(S.KONTUR, [S.TRAPPHAL]).difference(markplatta()[2].difference(hornutkap()))


@cache
def _lagen() -> tuple[tuple[tuple[str, float, float], ...], tuple[tuple[str, float, float], ...]]:
    """Bultarna (vägg, x, y) och de lägen där bulten genom syllen inte når betongen (plattan på marks kanter, där
    syllen står på L-elementens rygg av cellplast)."""
    ut: list[tuple[str, float, float]] = []
    utan: list[tuple[str, float, float]] = []
    ror = ror_i_plattan()
    betong = betongen()
    for kod, v in S.VAGGAR.items():
        delar = lagen.vagg(kod)
        o, u, w = np.array(v.origo), np.array(v.u), np.array(v.w)

        def us(d: lagen.Lage) -> tuple[float, float]:
            x0, y0, _, x1, y1, _ = d.lada
            a, b = sorted(float((np.array(p) - o) @ u) for p in ((x0, y0), (x1, y1)))
            return a, b
        syllar = [us(d) for d in delar if d.typ == "S" and d.lada[2] < 5.0]
        reglar = [us(d) for d in delar if d.typ != "S" and d.lada[2] < 60.0 and d.lada[5] - d.lada[2] > 1000.0]
        ww = v.tjocklek - FRAN_INSIDAN if kod in S.YTTERVAGGAR else v.tjocklek / 2

        def fri(x: float) -> bool:
            if not all(x < a - FRITT_REGEL or x > b + FRITT_REGEL for a, b in reglar):
                return False
            p = o + x * u + ww * w
            return bool(ror.distance(Point(p[0], p[1])) >= D / 2 + FRITT)

        for a, b in syllar:
            if b - a < 2 * FRITT_REGEL:
                continue
            n = max(2, int(np.ceil((b - a - 2 * KANT_SYLL) / CC)) + 1) if b - a > 2 * KANT_SYLL else 1
            mal = np.linspace(a + min(KANT_SYLL, (b - a) / 2), b - min(KANT_SYLL, (b - a) / 2), n) if n > 1 else \
                [(a + b) / 2]
            for x in mal:                      # närmaste läge i ett fack, inom syllen
                kand = [x + s * d for d in range(0, 400, 5) for s in (1, -1)]
                y = next((k for k in kand if a + FRITT_REGEL <= k <= b - FRITT_REGEL and fri(k)), None)
                if y is not None:
                    p = o + y * u + ww * w
                    q = (kod, round(float(p[0]), 1), round(float(p[1]), 1))
                    (ut if betong.contains(Point(p[0], p[1]).buffer(D)) else utan).append(q)
    return tuple(dict.fromkeys(ut)), tuple(dict.fromkeys(utan))


def bultar() -> tuple[tuple[str, float, float], ...]:
    """Bultarna: (vägg, x, y)."""
    return _lagen()[0]


def utan_betong() -> tuple[tuple[str, float, float], ...]:
    """Lägen där en bult genom syllen inte når betongen (ingen bult där; #88)."""
    return _lagen()[1]


def montage() -> Montage:
    m = Montage("Förankring", beskrivning="Betongbultar genom syllarna i mellanbjälklaget (#88)")
    for i, (kod, x, y) in enumerate(bultar(), 1):
        m.lagg(Del(f"Betongbult M{D:.0f} genom syllen", cylinder(D / 2, DJUP + 45.0 + OVER, (x, y, -DJUP)), BETONGBULT,
                   produkt="BETONGBULT-SYLL"), Placering(), f"BB{i:03d}")
    return m
