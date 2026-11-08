"""Ändbrädorna (ärende #31): väggarna som slutar fritt i ett rum (1B, 1D, 2A och 2B) får en bräda av oljad ask 22
över änden, som smygen runt fönstren: från golvet till innertaket och över skikten på båda sidorna, med fibrerna på
höjden.

I badrummet går våtrumsskikten runt den fria änden (väggbiten L19, vaggar.FRIA_ANDAR_VATRUM): sidornas skikt går förbi
änden så långt som skikten innanför dem, och ändens skikt (plywood, gips, tätskikt och kakel) täcker änden och
sidoskiktens kanter, så att tätskiktet och kaklet är hela runt hörnen."""
from __future__ import annotations

from shapely.geometry import Polygon

from modellering import Del, Montage

from trebodar import skelett as S
from trebodar.byggdelar.virke import fmt, virke_i_lada
from trebodar.material import ASK

from .lattvaggar import VAGGAR
from .skikt import HOJD, SKIVOR_T, SKIVOR_VATRUM, kapad_vid_taket, upp_till_taket
from .vaggar import FRIA_ANDAR_VATRUM

T = 22.0
ANDAR = (("1B", 1), ("1D", 1), ("2A", 0), ("2B", 1))      # väggen och änden (0 början, 1 slutet) som slutar fritt


def yta(kod: str, ande: int) -> Polygon:
    """Brädans yta i planen: utanför väggens ände, över stommen och skikten på båda sidorna."""
    v = S.INNERVAGGAR[kod]
    (ox, oy), (ux, uy) = v.origo, v.u
    u0, u1 = (-T, 0.0) if ande == 0 else (v.langd, v.langd + T)
    w0, w1 = -SKIVOR_T, v.tjocklek + SKIVOR_T
    return Polygon([(ox + ux * u - uy * w, oy + uy * u + ux * w) for u, w in ((u0, w0), (u1, w0), (u1, w1), (u0, w1))])


def _vatrum(m: Montage, kod: str, ande: int) -> None:
    """Våtrumsskikten över den fria änden: varje skikt utanför sidornas skikt på samma djup (d från stommen), över
    stommen och sidoskikten ut till skiktets yttre yta."""
    v = VAGGAR[kod]
    (ox, oy), (ux, uy) = v.origo, v.u
    d = 0.0
    for namn, t, typ, mat in SKIVOR_VATRUM:
        u0, u1 = (-d - t, -d) if ande == 0 else (v.langd + d, v.langd + d + t)
        w0, w1 = -d - t, v.tjocklek + d + t
        p = Polygon([(ox + ux * u - uy * w, oy + uy * u + ux * w) for u, w in ((u0, w0), (u1, w0), (u1, w1), (u0, w1))])
        m.lagg(Del(f"{namn} {fmt(t)} ände vägg {kod}", upp_till_taket(p, 0.0), mat), namn=f"{kod}-ANDE-{typ}")
        d += t


def montage() -> Montage:
    m = Montage("Ändbrädor", beskrivning="Ändbrädor av oljad ask 22 där väggarna slutar fritt, och våtrumsskikten runt "
                                         "badrummets fria ände")
    for kod, ande in ANDAR:
        p = yta(kod, ande)
        x0, y0, x1, y1 = p.bounds
        d, pl = virke_i_lada(x0, x1, y0, y1, 0.0, HOJD, "z", ASK)
        f = kapad_vid_taket(d.form, p, inv=pl.invers())     # kapad vid innertaket, i brädans system
        m.lagg(Del(f"Ändbräda ask {fmt(T)} vägg {kod}", f, ASK), pl, f"{kod}-ANDE")
    for kod, ande in FRIA_ANDAR_VATRUM:
        _vatrum(m, kod, ande)
    return m
