"""Grunden och källaren: bottenplattan, källarväggarna V1–V21, rören P1–P19, plattan på mark på plan 1 och
fasadstenen.

Bottenplattan (K-06 utförande L300, R-04) med överkanten z −2 250: betong 100 på cellplast 200, kantbalk och balkar
under innerväggarna 450 × 200 (med plattan) och plintar under rören, alla på 100 mm cellplast S300, och L-element S300
längs kanten (ytterkanten i väggarnas ytterliv, betongen börjar 100 mm innanför, i kärnans yttre yta). Plattan på
mark på plan 1 (bakom V3 och V20): 400 mm cellplast under mellanbjälklaget på dränerande fyllning upp till 1,7 m över
bottenplattan. Fasadstenen (AR-01) i fasadsten.py.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

from modellering import Del, Montage, Placering, box, minus

from trebodar import skelett as S
from trebodar.byggdelar.polygon import polygoner, prisma_ur
from trebodar.material import BETONG, CELLPLAST, CELLPLAST_S300, FYLLNING

from . import fasadsten, kallarvaggar, pelare

ROT = Path(__file__).resolve().parents[4]
K06 = ROT / "beräkningar" / "K-06"
Z_BP = S.Z_BOTTENPLATTA
H_PLATTA, H_BALK, H_L = 100.0, 200.0, 300.0      # plattan, balkarna med plattan, L-elementen (K-06 L300)
B_BALK = 450.0                   # kantbalk och balkar under innerväggarna
L_BEN, B_L = 100.0, 600.0        # L-elementets rygg (betongen börjar vid dess insida) och bredd
INRE_BALKAR = ("V15", "V19")     # balkar under innerväggarna, och linjen V4–V6 mellan dem (K-06)
MARK_PLATTA = ((0.0, 9205.0), (4545.0, 9205.0), (4545.0, 11010.0), (4310.0, 11010.0), (4310.0, 15900.0),
               (0.0, 15900.0))   # plattan på mark på plan 1 (K-05)


@lru_cache(maxsize=1)
def plintar() -> dict[str, Polygon]:
    """Plintarna i plan per rör: kvadrater med sidan ur K-06, under fotplåtarnas mitt."""
    r = json.loads((K06 / "resultat.json").read_text(encoding="utf-8"))
    sida = {p["namn"]: float(p["b"]) for p in r["platta"]["L300"]["plintar"]}
    return {n: Polygon([(x - sida[n] / 2, y - sida[n] / 2), (x + sida[n] / 2, y - sida[n] / 2),
                        (x + sida[n] / 2, y + sida[n] / 2), (x - sida[n] / 2, y + sida[n] / 2)])
            for n, (x, y) in pelare.fotplat_mitt().items()}


def _inre_balkar(betong: Polygon) -> Polygon:
    """Balkarna under innerväggarna: hela linjerna, ändarna förlängda en halv balkbredd, fram till kantbalken."""
    v = {w.namn: w for w in kallarvaggar.VAGGAR}
    lin = [LineString([(v[n].c, v[n].a), (v[n].c, v[n].b)] if v[n].riktning == "v" else
                      [(v[n].a, v[n].c), (v[n].b, v[n].c)]) for n in INRE_BALKAR]
    lin.append(LineString([(v["V19"].c, v["V4"].c), (v["V15"].c, v["V4"].c)]))
    return unary_union([q.buffer(B_BALK / 2, cap_style="square") for q in lin]).intersection(betong)


def bottenplatta() -> Montage:
    m = Montage("Bottenplatta", beskrivning="Betong 100 på cellplast 200 med kantbalk, balkar, plintar och L-element "
                                            "(K-06, R-04)")
    kontur = kallarvaggar.ytterkontur()                          # väggarnas ytterliv = L-elementens ytterkant
    betong = kontur.buffer(-L_BEN, join_style=2)
    kant = betong.difference(betong.buffer(-B_BALK, join_style=2))
    inre = _inre_balkar(betong).difference(kant)
    pl = plintar()
    l_fot = kontur.difference(kontur.buffer(-B_L, join_style=2))
    z_balk, z_fot = Z_BP - H_BALK, Z_BP - H_L
    # plattan, med ursparingar för rörens fotplåtar (ingjutna i plintarnas överkant)
    urs = [box(x0, x1, y0, y1, Z_BP - pelare.FOT_T, Z_BP + 1) for x0, x1, y0, y1 in pelare.fotplatar()]
    m.lagg(Del("Bottenplatta betong 100", minus(prisma_ur(betong, Z_BP - H_PLATTA, Z_BP), urs), BETONG), Placering(),
           "BP-B")
    m.lagg(Del("Kantbalk 450×200", prisma_ur(kant, z_balk, Z_BP - H_PLATTA), BETONG), Placering(), "BP-KB")
    for i, q in enumerate(polygoner(inre, 1e4), 1):
        m.lagg(Del("Balk 450×200 under innervägg", prisma_ur(q, z_balk, Z_BP - H_PLATTA), BETONG), Placering(),
               f"BP-IB{i}")
    upptaget = unary_union([kant, inre])
    for namn, q in pl.items():
        for k, g in enumerate(polygoner(q.intersection(betong).difference(upptaget), 1e4)):
            m.lagg(Del(f"Plint {q.bounds[2] - q.bounds[0]:.0f}", prisma_ur(g, z_balk, Z_BP - H_PLATTA), BETONG),
                   Placering(), f"BP-PL-{namn}" + (f"-{k + 1}" if k else ""))
        upptaget = upptaget.union(q)
    # cellplasten: L-elementen längs kanten, S300 under balkarna och plintarna, S100 i två lager under plattan
    m.lagg(Del("L-element S300 höjd 300", prisma_ur(l_fot, z_fot, z_balk) | prisma_ur(kontur.difference(betong),
                                                                                         z_balk, Z_BP),
               CELLPLAST_S300), Placering(), "BP-L")
    under = unary_union([inre] + list(pl.values())).intersection(betong)
    for i, q in enumerate(polygoner(under.difference(l_fot), 1e4), 1):
        m.lagg(Del("Cellplast S300 100 under balk och plint", prisma_ur(q, z_fot, z_balk), CELLPLAST_S300),
               Placering(), f"BP-CS{i}")
    for i, (namn, q, z0, z1) in enumerate((("undre", kontur.buffer(-B_L, join_style=2), z_fot, z_balk),
                                          ("övre", betong.buffer(-B_BALK, join_style=2), z_balk, Z_BP - H_PLATTA)), 1):
        for k, g in enumerate(polygoner(q.difference(under), 1e4)):
            m.lagg(Del(f"Cellplast S100 100, {namn} lagret", prisma_ur(g, z0, z1), CELLPLAST), Placering(),
                   f"BP-C{i}" + (f"-{k + 1}" if k else ""))
    return m


def platta_pa_mark() -> Montage:
    m = Montage("Plattan på mark", beskrivning="Under mellanbjälklaget på plan 1: 400 cellplast på fyllning")
    # fram till källarväggarnas cellplast (V3, V20): källarens kontur tas bort
    p = Polygon(MARK_PLATTA).difference(kallarvaggar.ytterkontur())
    for i, g in enumerate(polygoner(p), 1):
        m.lagg(Del("Cellplast 400 under plattan på mark", prisma_ur(g, -S.H_BJALKLAG - 400.0, -S.H_BJALKLAG),
                   CELLPLAST), Placering(), f"PM-C{i}")
        m.lagg(Del("Dränerande fyllning", prisma_ur(g, Z_BP, -S.H_BJALKLAG - 400.0), FYLLNING), Placering(),
               f"PM-F{i}")
    return m


def montage() -> Montage:
    m = Montage("Grund", beskrivning="Bottenplatta, källarväggar, rör, plattan på mark och fasadsten")
    m.lagg(bottenplatta())
    m.lagg(kallarvaggar.montage())
    m.lagg(pelare.montage())
    m.lagg(platta_pa_mark())
    m.lagg(fasadsten.montage())
    return m
