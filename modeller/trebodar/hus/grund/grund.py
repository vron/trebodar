"""Grunden och källaren: bottenplattan, källarväggarna V1–V21, rören P1–P19, plattan på mark på plan 1 och
fasadstenen.

Bottenplattan (K-06 utförande L400, R-04) med överkanten z −2 250: betong 100 på cellplast 300 (100 + 200, plastfolien
mellan i balkarnas underkant), kantbalk och balkar under innerväggarna 450 × 300 (med plattan) och plintar under
rören, alla på 100 mm cellplast S300, och L-element S300 höjd 400 längs kanten (ytterkanten i väggarnas ytterliv,
betongen börjar 100 mm innanför, i kärnans yttre yta). Plattan på mark på plan 1 (bakom V3 och V20, AR-02):
mellanbjälklaget i L-element 500 längs de fria kanterna (ytterkanten i väggarnas ytterliv), cellplast 350 under
plattan, makadam 150 och dränerande fyllning i ett schakt 100 mm utanför plattan. L-elementens rygg är avfasad 45° i
ovankant, FAS bred upptill, och betongen fyller fasen; vid plattan på marks fria hörn är ryggen urtagen i plattans
tjocklek och betongen gjuten ut i urtagen (R-06 detalj F). Fasadstenen (AR-01) i fasadsten.py.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from typing import Any

from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

from modellering import Del, Montage, Placering, box, minus

from trebodar import skelett as S
from trebodar.byggdelar.polygon import polygoner, prisma_ur, stympad
from trebodar.material import BETONG, CELLPLAST, CELLPLAST_S300, FYLLNING, MAKADAM

from . import fasadsten, kallarvaggar, pelare

ROT = Path(__file__).resolve().parents[4]
K06 = ROT / "beräkningar" / "K-06"
Z_BP = S.Z_BOTTENPLATTA
H_PLATTA, H_BALK, H_L = 100.0, 300.0, 400.0      # plattan, balkarna med plattan, L-elementen (K-06 L400)
B_BALK = 450.0                   # kantbalk och balkar under innerväggarna
L_BEN, B_L = 100.0, 600.0        # L-elementets rygg (betongen börjar vid dess insida) och bredd
FAS = 50.0                       # ryggen avfasad 45° i ovankant: FAS bred upptill, betongen fyller fasen
INRE_BALKAR = ("V15", "V19")     # balkar under innerväggarna, och linjen V4–V6 mellan dem (K-06)
# plattan på mark (AR-02): L-element 500 med fot 100, cellplast 100 + 250 under plattan, makadam 150
H_L_MARK, T_FOT_MARK, T_MAKADAM = 500.0, 100.0, 150.0
SCHAKT_UT = 100.0                # bergschaktet runt plattan på mark, utanför L-elementen
MARK_UK = -2315.0                # markmodellens underkant (Onshape-modellens berg och uppfyllnad)
MARK_PLATTA = ((0.0, 9205.0), (4545.0, 9205.0), (4545.0, 11010.0), (4310.0, 11010.0), (4310.0, 15900.0),
               (0.0, 15900.0))   # plattan på mark på plan 1 (K-05)
# plattan på marks fria hörn (LA9, LA10): ryggen urtagen HORN_UTKAP längs var kant från hörnet utom RYGG_KVAR närmast
# ytterkanten, i plattans tjocklek (R-06 detalj F, samma regel som R-05:s kallare.py)
HORN_UTKAP, RYGG_KVAR = 400.0, 30.0


@lru_cache(maxsize=1)
def plintar() -> dict[str, Polygon]:
    """Plintarna i plan per rör: kvadrater med sidan ur K-06, under fotplåtarnas mitt."""
    r = json.loads((K06 / "resultat.json").read_text(encoding="utf-8"))
    sida = {p["namn"]: float(p["b"]) for p in r["platta"][f"L{H_L:.0f}"]["plintar"]}
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
    m = Montage("Bottenplatta", beskrivning=f"Betong {H_PLATTA:.0f} på cellplast {H_L - H_PLATTA:.0f} med kantbalk, "
                                            f"balkar, plintar och L-element {H_L:.0f} (K-06, R-04)")
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
    m.lagg(Del(f"Kantbalk {B_BALK:.0f}×{H_BALK:.0f}", prisma_ur(kant, z_balk, Z_BP - H_PLATTA), BETONG), Placering(),
           "BP-KB")
    for i, q in enumerate(polygoner(inre, 1e4), 1):
        m.lagg(Del(f"Balk {B_BALK:.0f}×{H_BALK:.0f} under innervägg", prisma_ur(q, z_balk, Z_BP - H_PLATTA), BETONG),
               Placering(), f"BP-IB{i}")
    upptaget = unary_union([kant, inre])
    for namn, q in pl.items():
        for k, g in enumerate(polygoner(q.intersection(betong).difference(upptaget), 1e4)):
            m.lagg(Del(f"Plint {q.bounds[2] - q.bounds[0]:.0f}", prisma_ur(g, z_balk, Z_BP - H_PLATTA), BETONG),
                   Placering(), f"BP-PL-{namn}" + (f"-{k + 1}" if k else ""))
        upptaget = upptaget.union(q)
    # fasen i L-elementens rygg: betongen fyller den, ryggen är FAS bred upptill
    fas = stympad(betong, kontur.buffer(-(L_BEN - FAS), join_style=2), Z_BP - FAS, Z_BP, FAS * 1.5)
    m.lagg(Del(f"Betong i L-elementens fas {FAS:.0f}", minus(fas, [prisma_ur(betong, Z_BP - FAS, Z_BP)]), BETONG),
           Placering(), "BP-FAS")
    # cellplasten: L-elementen längs kanten, S300 under balkarna och plintarna, S100 i två lager under plattan, det
    # undre lika tjockt som L-elementens fot och plastfolien mellan dem i balkarnas underkant
    m.lagg(Del(f"L-element S300 höjd {H_L:.0f}",
               minus(prisma_ur(l_fot, z_fot, z_balk) | prisma_ur(kontur.difference(betong), z_balk, Z_BP), [fas]),
               CELLPLAST_S300), Placering(), "BP-L")
    under = unary_union([inre] + list(pl.values())).intersection(betong)
    for i, q in enumerate(polygoner(under.difference(l_fot), 1e4), 1):
        m.lagg(Del("Cellplast S300 100 under balk och plint", prisma_ur(q, z_fot, z_balk), CELLPLAST_S300),
               Placering(), f"BP-CS{i}")
    for i, (namn, q, z0, z1) in enumerate((("undre", kontur.buffer(-B_L, join_style=2), z_fot, z_balk),
                                          ("övre", betong.buffer(-B_BALK, join_style=2), z_balk, Z_BP - H_PLATTA)), 1):
        for k, g in enumerate(polygoner(q.difference(under), 1e4)):
            m.lagg(Del(f"Cellplast S100 {z1 - z0:.0f}, {namn} lagret", prisma_ur(g, z0, z1), CELLPLAST), Placering(),
                   f"BP-C{i}" + (f"-{k + 1}" if k else ""))
    return m


@lru_cache(maxsize=1)
def markplatta() -> tuple[Polygon, Any, Polygon, Polygon]:
    """Plattan på mark i väggarnas ytterliv (L-elementens ytterkant), dess fria kanter (inte mot källaren) och
    L-elementens rygg och fot i plan."""
    kallare = kallarvaggar.ytterkontur()
    p = max(polygoner(Polygon(MARK_PLATTA).buffer(S.STOMME_UT, join_style=2).difference(kallare)), key=lambda g: g.area)
    fri = p.exterior.difference(kallare)
    rygg = fri.buffer(L_BEN, cap_style="flat", join_style="mitre").intersection(p)
    fot = fri.buffer(B_L, cap_style="flat", join_style="mitre").intersection(p)
    return p, fri, rygg, fot


@lru_cache(maxsize=1)
def hornutkap() -> Any:
    """Urtagen i L-elementens rygg vid plattan på marks fria hörn, de konvexa hörnen där båda kanterna är fria (R-06
    detalj F). Mellanbjälklagets betong fyller dem."""
    p, fri, rygg, _ = markplatta()
    c = list(p.exterior.coords)[:-1]
    hornen = []
    for i, b in enumerate(c):
        a, d = c[i - 1], c[(i + 1) % len(c)]
        konvex = ((b[0] - a[0]) * (d[1] - b[1]) - (b[1] - a[1]) * (d[0] - b[0]) > 0) == p.exterior.is_ccw
        if konvex and all(LineString(k).difference(fri.buffer(1.0)).length < 1.0 for k in ((a, b), (b, d))):
            hornen.append(Point(b).buffer(HORN_UTKAP, cap_style="square"))
    kvar = fri.buffer(RYGG_KVAR, cap_style="flat", join_style="mitre")
    return unary_union(hornen).intersection(rygg).difference(kvar)


def markschakt() -> Polygon:
    """Schaktet i berget runt plattan på mark: SCHAKT_UT utanför de fria kanterna, fram till källarväggarna."""
    p, fri, _, _ = markplatta()
    return p.union(fri.buffer(SCHAKT_UT, cap_style="flat", join_style="mitre")).difference(kallarvaggar.ytterkontur())


def platta_pa_mark() -> Montage:
    m = Montage("Plattan på mark", beskrivning="L-element 500, cellplast 350 och makadam 150 under mellanbjälklaget "
                                                "på plan 1 (AR-02)")
    p, fri, rygg, fot = markplatta()
    z_uk, z_mak = -H_L_MARK, -H_L_MARK - T_MAKADAM
    z_fot = z_uk + T_FOT_MARK
    # fasen i L-elementens rygg: mellanbjälklagets betong fyller den (betongen når FAS från ytterkanten i överkant)
    utan_rygg = p.difference(rygg)
    fas = stympad(utan_rygg, p.difference(fri.buffer(L_BEN - FAS, cap_style="flat", join_style="mitre")), -FAS, 0.0,
                  FAS * 1.5)
    urtag = [prisma_ur(g, -S.H_BJALKLAG, 0.0) for g in polygoner(hornutkap())]   # mellanbjälklagets betong
    m.lagg(Del(f"L-element S300 höjd {H_L_MARK:.0f}",
               minus(prisma_ur(fot, z_uk, z_fot) | prisma_ur(rygg, z_fot, 0.0), [fas, *urtag]), CELLPLAST_S300),
           Placering(), "PM-L")
    m.lagg(Del(f"Betong i L-elementens fas {FAS:.0f}", minus(fas, [prisma_ur(utan_rygg, -FAS, 0.0), *urtag]), BETONG),
           Placering(), "PM-FAS")
    for i, g in enumerate(polygoner(p.difference(fot), 1e4)):
        m.lagg(Del("Cellplast S100 100, undre lagret", prisma_ur(g, z_uk, z_fot), CELLPLAST), Placering(),
               "PM-C1" + (f"-{i + 1}" if i else ""))
    for i, g in enumerate(polygoner(p.difference(rygg), 1e4)):
        m.lagg(Del("Cellplast S100 250, övre lagret", prisma_ur(g, z_fot, -S.H_BJALKLAG), CELLPLAST), Placering(),
               "PM-C2" + (f"-{i + 1}" if i else ""))
    schakt = markschakt()
    m.lagg(Del("Makadam 150", prisma_ur(schakt, z_mak, z_uk), MAKADAM), Placering(), "PM-M")
    m.lagg(Del("Dränerande fyllning", prisma_ur(schakt, MARK_UK, z_mak), FYLLNING), Placering(), "PM-F")
    return m


def montage() -> Montage:
    m = Montage("Grund", beskrivning="Bottenplatta, källarväggar, rör, plattan på mark och fasadsten")
    m.lagg(bottenplatta())
    m.lagg(kallarvaggar.montage())
    m.lagg(pelare.montage())
    m.lagg(platta_pa_mark())
    m.lagg(fasadsten.montage())
    return m
