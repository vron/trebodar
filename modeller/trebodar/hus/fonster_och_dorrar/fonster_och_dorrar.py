"""Fönster och dörrar, förenklade: karm runt öppningen och glas eller dörrblad. Ytterväggarnas öppningar och
innerdörrarna (skjutdörrar utanpå väggen, planritning 201 rev 02) står i oppningar.py.

Karmen går från fasadens utsida (w −65) 149 mm in i väggen, 70 mm bred; glas 24 mm och dörrblad 40 mm i karmens
mitt.
"""
from __future__ import annotations

from modellering import Del, Montage, Placering, box

from trebodar import skelett as S
from trebodar.byggdelar.virke import fmt
from trebodar.hus.invandigt.invandigt import SKIVOR_T
from trebodar.material import DORRBLAD, GLAS, KARM

from .oppningar import INNERDORRAR, OPPNINGAR, Innerdorr, Oppning

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


SKJUT_T, SKJUT_GLAPP, OVERLAPP = 40.0, 10.0, 30.0       # skjutdörrens blad, avståndet till väggens skikt


def skjutdorr(d: Innerdorr) -> tuple[Montage, Placering]:
    """Skjutdörren utanpå väggen, stängd: bladet täcker öppningen och skenan går en dörrbredd till åt det håll dörren
    öppnas, men inte in över en annan dörr på samma sida av väggen."""
    from trebodar.hus.invandigt.vaggar import skiktets_tjocklek, vaggdef
    v = vaggdef(d.vagg)
    t = skiktets_tjocklek(d.vagg, d.sida, (d.u0 + d.u1) / 2)
    yta = -t if d.sida < 0 else v.tjocklek + t                      # skiktets yta, skenan sitter på den
    wa, wb = sorted((yta + d.sida * SKJUT_GLAPP, yta + d.sida * (SKJUT_GLAPP + SKJUT_T)))
    sa, sb = sorted((yta, yta + d.sida * (2 * SKJUT_GLAPP + SKJUT_T)))
    a, b = d.u0 - d.fore, d.u1 + d.efter
    grannar = [(o.u0 - o.fore, o.u1 + o.efter) for o in INNERDORRAR if o.vagg == d.vagg and o.sida == d.sida and o != d]
    if d.mot > 0:
        s0, s1 = a, min([b + d.bredd] + [g0 - 10.0 for g0, _ in grannar if g0 >= b])
    else:
        s0, s1 = max([a - d.bredd] + [g1 + 10.0 for _, g1 in grannar if g1 <= a]), b
    s0, s1 = max(s0, min(a, SKIVOR_T + 10.0)), min(s1, max(b, v.langd - SKIVOR_T - 10.0))     # inte förbi grannväggarna
    m = Montage(d.kod, d.kod, f"Skjutdörr {fmt(d.bredd)}×{fmt(d.hojd)}, {d.rum}")
    m.lagg(Del(f"Dörrblad {fmt(b - a)}×{fmt(d.hojd + 30)}", box(a, b, wa, wb, 10.0, d.hojd + 40.0), DORRBLAD),
           Placering(), f"{d.kod}-BLAD")
    m.lagg(Del(f"Skena {fmt(s1 - s0)}", box(s0, s1, sa, sb, d.hojd + 40.0, d.hojd + 80.0), KARM), Placering(),
           f"{d.kod}-SKENA")
    return m, v.placering()


def montage() -> Montage:
    m = Montage("Fönster och dörrar", beskrivning="Fönster, ytterdörrar och innerdörrar (förenklade)")
    ytter = Montage("Ytterväggarnas fönster och dörrar")
    for kod, lst in OPPNINGAR.items():
        for o in lst:
            ytter.lagg(enhet(o), S.YTTERVAGGAR[kod].placering())
    m.lagg(ytter)
    inner = Montage("Innerdörrar", beskrivning="Skjutdörrar (planritning 201 rev 02)")
    for d in INNERDORRAR:
        inner.lagg(*skjutdorr(d))
    m.lagg(inner)
    return m
