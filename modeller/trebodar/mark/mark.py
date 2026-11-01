"""Marken: berg, uppfyllnad och sovrumsavsatsen, som i Onshape-modellen (referensdelar), schaktet i berget runt
plattan på mark och fyllningen mot källarväggarna.

Schaktet går 100 mm utanför plattan på mark (hus/grund: L-element, cellplast, makadam och dränerande fyllning under
plattan); mellan L-elementen och schaktets kant ligger makadam upp till markytan, där berget eller uppfyllnaden låg.
Mot källarväggarnas utsida ligger dränerande fyllning upp till K-06:s fyllnadshöjder (linjärt mellan väggens ändar),
där Onshape-modellens mark inte når upp.
"""
from __future__ import annotations

from shapely.geometry import Point, Polygon
from shapely.geometry import box as rektangel
from shapely.ops import unary_union

from modellering import Del, Diff, Form, Montage, Placering, minus, polyeder

from trebodar import skelett as S
from trebodar.byggdelar import lagen
from trebodar.byggdelar.polygon import polygoner, prisma_ur
from trebodar.byggdelar.referensdel import importerad
from trebodar.hus.grund import fasadsten, kallarvaggar
from trebodar.hus.grund.grund import H_L_MARK, MARK_PLATTA, MARK_UK, markplatta, markschakt
from trebodar.material import BERG, FYLLNING, MAKADAM, MARK

Z_BP = S.Z_BOTTENPLATTA
# fyllnadshöjd över bottenplattan vid väggens ände a och b (K-06), mot källarväggarnas utsida
FYLLNAD = {"V1": (1800.0, 1800.0), "V2": (2000.0, 2000.0), "V7": (2000.0, 2000.0), "V9": (0.0, 800.0),
           "V14": (800.0, 1800.0), "V16": (2000.0, 2000.0), "V18": (2000.0, 2000.0), "V21": (2000.0, 2000.0)}
FYLLNAD_B = 1500.0               # fyllningens bredd från väggen


def _husets_fotavtryck() -> Form:
    """Källaren med fasadstenen och plattan på mark, som prisma från under bottenplattan till bjälklaget."""
    # stängning (+600, −530) så att öppningarna i fasaden räknas till huset
    p = kallarvaggar.ytterkontur().buffer(600.0, join_style=2).buffer(-530.0, join_style=2)
    p = p.union(Polygon(MARK_PLATTA).buffer(30.0, join_style=2))
    return prisma_ur(Polygon(max(polygoner(p), key=lambda g: g.area).exterior), -2900.0, 0.0)


def _fyllnad(v: kallarvaggar.Kallarvagg, ha: float, hb: float) -> Form:
    """Fyllningen mot väggens utsida, FYLLNAD_B bred, från markmodellens underkant upp till fyllnadshöjden: linjärt
    längs väggen mellan ändarna och vågrätt förbi dem, där den möter grannväggarnas fyllning."""
    halv = kallarvaggar.KARNA / 2 + kallarvaggar.CELL
    mitt = (v.a + v.b) / 2
    prov = (mitt, v.c + halv + 10.0) if v.riktning == "h" else (v.c + halv + 10.0, mitt)
    s = -1.0 if kallarvaggar.ytterkontur().contains(Point(prov)) else 1.0       # utsidans riktning
    w0, w1 = sorted((v.c + s * halv, v.c + s * (halv + FYLLNAD_B)))
    us = (v.a - FYLLNAD_B, v.a, v.b, v.b + FYLLNAD_B)
    zs = (Z_BP + ha, Z_BP + ha, Z_BP + hb, Z_BP + hb)

    def punkt(u: float, w: float, z: float) -> tuple[float, float, float]:
        return (u, w, z) if v.riktning == "h" else (w, u, z)
    horn = [punkt(u, w, z) for u, zt in zip(us, zs) for w, z in ((w0, MARK_UK), (w1, MARK_UK), (w1, zt), (w0, zt))]
    ytor = [[0, 1, 2, 3], [12, 13, 14, 15]]
    for i in range(3):
        a, b = 4 * i, 4 * i + 4
        ytor += [[a, b, b + 1, a + 1], [a + 3, a + 2, b + 2, b + 3], [a, a + 3, b + 3, b], [a + 1, b + 1, b + 2, a + 2]]
    return polyeder(horn, ytor)


def montage() -> Montage:
    m = Montage("Mark", beskrivning="Berg, uppfyllnad och sovrumsavsats (ur Onshape-modellen), schaktet runt plattan "
                                    "på mark och fyllningen mot källarväggarna (K-06)")
    hus = _husets_fotavtryck()
    schakt = prisma_ur(markschakt(), MARK_UK - 10.0, 10.0)
    berg0, upp0, avsats0 = importerad("berg.bbrep"), importerad("uppfyllnad.bbrep"), importerad("sovrumsavsats.bbrep")
    m.lagg(Del("Berg", berg0 - schakt, BERG), Placering(), "Berg")
    m.lagg(Del("Uppfyllnad", minus(upp0, [hus, avsats0, schakt]), MARK), Placering(), "Uppfyllnad")
    m.lagg(Del("Sovrumsavsats", minus(avsats0, [hus, schakt]), FYLLNING), Placering(), "Sovrumsavsats")
    # makadam mellan L-elementen och schaktets kant, upp till markytan där berget eller uppfyllnaden låg
    for i, g in enumerate(polygoner(markschakt().difference(markplatta()[0]), 1e3), 1):
        ring = prisma_ur(g, -H_L_MARK, 10.0)
        m.lagg(Del("Makadam runt plattan på mark", (ring & berg0) | (ring & upp0), MAKADAM), Placering(), f"MA-{i}")
    # fyllningen mot källarväggarna, utanför väggarna och fasadstenen, där marken inte når upp
    sten = unary_union([rektangel(x0, y0, x1, y1) for _, _, (x0, y0, _, x1, y1, _) in lagen.lagen(fasadsten.montage())])
    hinder = [prisma_ur(kallarvaggar.ytterkontur(), MARK_UK - 10.0, 10.0), berg0, upp0, avsats0, schakt]
    # fasadstenens kluvna yta följs inte: fyllningen slutar 5 mm utanför stenarnas omslutande lådor
    hinder += [prisma_ur(g, MARK_UK - 10.0, 10.0) for g in polygoner(sten.buffer(5.0, join_style=2))]
    vaggar = {v.namn: v for v in kallarvaggar.VAGGAR}
    tidigare: list[Form] = []
    for namn, (ha, hb) in FYLLNAD.items():
        band = f = _fyllnad(vaggar[namn], ha, hb)
        for h in hinder + tidigare:
            f = Diff(f, (h,))    # ett verktyg i taget (inte a - b, som slår ihop): överlappande verktyg gav fel
        m.lagg(Del(f"Fyllning mot {namn}", f, FYLLNING), Placering(), f"FK-{namn}")
        tidigare.append(band)
    return m
