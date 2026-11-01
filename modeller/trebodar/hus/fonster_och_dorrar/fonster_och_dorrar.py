"""Fönster och dörrar, förenklade: karm runt öppningen och glas eller dörrblad. Ytterväggarnas öppningar står i
oppningar.py; innerdörrarna har Onshape-modellens mått.

Karmen går från fasadens utsida (w −65) 149 mm in i väggen, 70 mm bred; glas 24 mm och dörrblad 40 mm i karmens
mitt.
"""
from __future__ import annotations

from modellering import Del, Montage, Placering, box

from trebodar import skelett as S
from trebodar.byggdelar.virke import fmt
from trebodar.material import DORRBLAD, GLAS, KARM

from .oppningar import OPPNINGAR, Oppning

W0, W1 = -S.T_FASAD, -S.T_FASAD + 149.0        # karmens djup i väggen
KARM_B = 70.0


def enhet(o: Oppning) -> Montage:
    m = Montage(o.kod, o.kod, f"{o.typ.capitalize()} {fmt(o.bredd)}×{fmt(o.hojd)}" +
                (f" ({o.onshape} i Onshape)" if o.onshape else ""))
    dorr = o.typ in ("dörr", "skjutdörr")
    zi0 = o.z0 + (0.0 if dorr or o.typ == "fönsterdörr" else KARM_B)
    karm = box(o.u0, o.u1, W0, W1, o.z0, o.z1) - box(o.u0 + KARM_B, o.u1 - KARM_B, W0 - 1, W1 + 1, zi0, o.z1 - KARM_B)
    m.lagg(Del(f"Karm {o.typ} {fmt(o.bredd)}×{fmt(o.hojd)}", karm, KARM), Placering(), f"{o.kod}-KARM")
    if o.typ == "dörr":
        blad = box(o.u0 + KARM_B, o.u1 - KARM_B, -10.0, 30.0, zi0 + 10, o.z1 - KARM_B)
        m.lagg(Del(f"Dörrblad {fmt(o.bredd - 2 * KARM_B)}×{fmt(o.z1 - KARM_B - zi0 - 10)}", blad, DORRBLAD),
               Placering(), f"{o.kod}-BLAD")
    else:
        glas = box(o.u0 + KARM_B, o.u1 - KARM_B, 0.0, 24.0, zi0 + (KARM_B if o.typ != "fönster" else 0.0),
                   o.z1 - KARM_B)
        m.lagg(Del(f"Glas {fmt(o.bredd - 2 * KARM_B)}×{fmt(o.z1 - KARM_B - zi0)}", glas, GLAS), Placering(),
               f"{o.kod}-GLAS")
    return m


# innerdörrar: (kod, x0, x1, y0, y1, riktning) med karmens utsträckning; dörrbladet 40 mm i väggens mitt.
# Som i Onshape-modellen utom: ID2 börjar efter karmstolpen LD2_2 och väggen 2C, ID5 slutar före den nya stolpen
# LN1_1 och ID6 börjar vid stolpen LD4_1 (140×140).
INNERDORRAR = (
    ("ID1", 3263.0, 3357.0, 7055.0, 8035.0, "y"),
    ("ID2", 9358.0, 9452.0, 5995.0, 6872.0, "y"),
    ("ID3", 10980.0, 11074.0, 3671.0, 4651.0, "y"),
    ("ID4", 10980.0, 11074.0, 5562.0, 6542.0, "y"),
    ("ID5", 10565.0, 11545.0, 2748.0, 2842.0, "x"),
    ("ID6", 4545.0, 5617.0, 5900.0, 5995.0, "x"),
)


def innerdorr(kod: str, x0: float, x1: float, y0: float, y1: float, langs: str) -> Montage:
    m = Montage(kod, kod, "Innerdörr (förenklad)")
    if langs == "y":
        sidor = (box(x0, x0 + 20, y0, y1, 0, 2200), box(x1 - 20, x1, y0, y1, 0, 2200))
        blad = box(0.5 * (x0 + x1) - 20, 0.5 * (x0 + x1) + 20, y0 + 37.5, y1 - 37.5, 35, 2175)
    else:
        sidor = (box(x0, x1, y0, y0 + 20, 0, 2200), box(x0, x1, y1 - 20, y1, 0, 2200))
        blad = box(x0 + 37.5, x1 - 37.5, 0.5 * (y0 + y1) - 20, 0.5 * (y0 + y1) + 20, 35, 2175)
    for i, s in enumerate(sidor, 1):
        m.lagg(Del(f"Dörrfoder {kod}", s, KARM), Placering(), f"{kod}-FODER{i}")
    m.lagg(Del(f"Dörrblad {kod}", blad, DORRBLAD), Placering(), f"{kod}-BLAD")
    return m


def montage() -> Montage:
    m = Montage("Fönster och dörrar", beskrivning="Fönster, ytterdörrar och innerdörrar (förenklade)")
    ytter = Montage("Ytterväggarnas fönster och dörrar")
    for kod, lst in OPPNINGAR.items():
        for o in lst:
            ytter.lagg(enhet(o), S.YTTERVAGGAR[kod].placering())
    m.lagg(ytter)
    inner = Montage("Innerdörrar")
    for d in INNERDORRAR:
        inner.lagg(innerdorr(*d))
    m.lagg(inner)
    return m
