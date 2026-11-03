"""Ändbrädorna (ärende #31): väggarna som slutar fritt i ett rum (1B, 1D, 2A och 2B) får en bräda av oljad ask 22
över änden, som smygen runt fönstren: från golvet till innertaket och över skikten på båda sidorna, med fibrerna på
höjden."""
from __future__ import annotations

from shapely.geometry import Polygon

from modellering import Del, Kapad, Montage

from trebodar import skelett as S
from trebodar.byggdelar.virke import fmt, virke_i_lada
from trebodar.material import ASK

from .skikt import HOJD, SKIVOR_T, takplan

T = 22.0
ANDAR = (("1B", 1), ("1D", 1), ("2A", 0), ("2B", 1))      # väggen och änden (0 början, 1 slutet) som slutar fritt


def yta(kod: str, ande: int) -> Polygon:
    """Brädans yta i planen: utanför väggens ände, över stommen och skikten på båda sidorna."""
    v = S.INNERVAGGAR[kod]
    (ox, oy), (ux, uy) = v.origo, v.u
    u0, u1 = (-T, 0.0) if ande == 0 else (v.langd, v.langd + T)
    w0, w1 = -SKIVOR_T, v.tjocklek + SKIVOR_T
    return Polygon([(ox + ux * u - uy * w, oy + uy * u + ux * w) for u, w in ((u0, w0), (u1, w0), (u1, w1), (u0, w1))])


def montage() -> Montage:
    m = Montage("Ändbrädor", beskrivning="Ändbrädor av oljad ask 22 där väggarna slutar fritt")
    for kod, ande in ANDAR:
        p = yta(kod, ande)
        x0, y0, x1, y1 = p.bounds
        d, pl = virke_i_lada(x0, x1, y0, y1, 0.0, HOJD, "z", ASK)
        f = d.form
        for pkt, n in takplan(p):                            # kapad vid innertaket, i brädans system
            f = Kapad(f, pl.invers().punkt(pkt), pl.invers().riktning(n))
        m.lagg(Del(f"Ändbräda ask {fmt(T)} vägg {kod}", f, ASK), pl, f"{kod}-ANDE")
    return m
