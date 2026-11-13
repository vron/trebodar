"""Grunden och källaren: bottenplattan, källarväggarna V1–V21, rören P1–P19, plattan på mark på plan 1 och
fasadstenen.

Bottenplattan (K-06 utförande L400, R-04) med överkanten z −2 250: betong 100 på cellplast 300 (100 + 200, plastfolien
mellan i balkarnas underkant), kantbalk och balkar under innerväggarna 450 × 300 (med plattan) och plintar under
rören, alla på det undre skiktet, 100 mm cellplast S300 i hela ytan, och L-element S300 höjd 400 längs kanten (ytterkanten i väggarnas ytterliv,
betongen börjar 100 mm innanför, i kärnans yttre yta). Plattan på mark på plan 1 (bakom V3 och V20, AR-02):
mellanbjälklaget i L-element 500 längs de fria kanterna (ytterkanten i väggarnas ytterliv), cellplast S300 350 under
plattan (K-06: S100 räcker inte under hörnstolparna), makadam 150 och dränerande fyllning i ett schakt 100 mm utanför plattan. Bottenplattans L-element har ryggen
avfasad 45° i ovankant, FAS bred upptill, och betongen fyller fasen. Plattan på marks L-element har ryggen urtagen i
mellanbjälklagets tjocklek utom de yttersta RYGG_KVAR, som kantisoleringen ovanpå källarväggarna, så att betongen går
fram till plattans kant och ytterväggarnas syll står på betongen som i resten av huset (K-05, R-06). Fasadstenen
(AR-01) i fasadsten.py.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from typing import Any

from shapely.geometry import LineString, Polygon
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
FAS = 50.0                       # bottenplattans rygg avfasad 45° i ovankant: FAS bred upptill, betongen fyller fasen
INRE_BALKAR = ("V15", "V19")     # balkar under innerväggarna, och linjen V4–V6 mellan dem (K-06)
# plattan på mark (AR-02): L-element 500 med fot 100, cellplast 100 + 250 under plattan, makadam 150
H_L_MARK, T_FOT_MARK, T_MAKADAM = 500.0, 100.0, 150.0
SCHAKT_UT = 100.0                # bergschaktet runt plattan på mark, utanför L-elementen
MARK_UK = -2315.0                # markens underkant (berget och uppfyllnaden i mark/marken.json)
MARK_PLATTA = ((0.0, 9205.0), (4545.0, 9205.0), (4545.0, 11010.0), (4310.0, 11010.0), (4310.0, 15900.0),
               (0.0, 15900.0))   # plattan på mark på plan 1 (K-05)
# plattan på mark: ryggen i mellanbjälklagets tjocklek, ut till plattans kant (samma regel som R-05:s kallare.py)
RYGG_KVAR = S.STOMME_UT


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
    # cellplasten: L-elementen längs kanten, det undre lagret S300 i hela ytan innanför deras fot (lika tjockt som
    # foten, också under balkarna och plintarna, utan urtag), plastfolien på det i balkarnas underkant och det övre
    # lagret S100 under plattan mellan balkarna och plintarna (K-06)
    m.lagg(Del(f"L-element S300 höjd {H_L:.0f}",
               minus(prisma_ur(l_fot, z_fot, z_balk) | prisma_ur(kontur.difference(betong), z_balk, Z_BP), [fas]),
               CELLPLAST_S300), Placering(), "BP-L")
    under = unary_union([inre] + list(pl.values())).intersection(betong)
    for k, g in enumerate(polygoner(kontur.buffer(-B_L, join_style=2), 1e4)):
        m.lagg(Del(f"Cellplast S300 {z_balk - z_fot:.0f}, undre lagret", prisma_ur(g, z_fot, z_balk), CELLPLAST_S300),
               Placering(), "BP-C1" + (f"-{k + 1}" if k else ""))
    for k, g in enumerate(polygoner(betong.buffer(-B_BALK, join_style=2).difference(under), 1e4)):
        m.lagg(Del(f"Cellplast S100 {Z_BP - H_PLATTA - z_balk:.0f}, övre lagret",
                   prisma_ur(g, z_balk, Z_BP - H_PLATTA), CELLPLAST), Placering(), "BP-C2" + (f"-{k + 1}" if k else ""))
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
def kantrygg() -> Any:
    """L-elementens rygg vid plattan på marks fria kanter i mellanbjälklagets tjocklek, RYGG_KVAR bred: plattans kant
    ligger där."""
    p, fri, _, _ = markplatta()
    return fri.buffer(RYGG_KVAR, cap_style="flat", join_style="mitre").intersection(p)


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
    m.lagg(Del(f"L-element S300 höjd {H_L_MARK:.0f}",
               prisma_ur(fot, z_uk, z_fot) | prisma_ur(rygg, z_fot, -S.H_BJALKLAG)
               | prisma_ur(kantrygg(), -S.H_BJALKLAG, 0.0), CELLPLAST_S300), Placering(), "PM-L")
    for i, g in enumerate(polygoner(p.difference(fot), 1e4)):
        m.lagg(Del("Cellplast S300 100, undre lagret", prisma_ur(g, z_uk, z_fot), CELLPLAST_S300), Placering(),
               "PM-C1" + (f"-{i + 1}" if i else ""))
    for i, g in enumerate(polygoner(p.difference(rygg), 1e4)):
        m.lagg(Del("Cellplast S300 250, övre lagret", prisma_ur(g, z_fot, -S.H_BJALKLAG), CELLPLAST_S300), Placering(),
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
