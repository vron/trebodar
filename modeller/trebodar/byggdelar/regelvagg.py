"""Regelväggar och andra plana stommar (takstolar) i väggens system: u längs väggen, w genom väggen (w 0 =
stommens yttre yta), z uppåt från bjälklagets överkant (skelett.Vaggdef).

Delarna får namn efter väggen, typ och ordning längs väggen: 1SO-R07 är den sjunde regeln i 1SO räknat i u-led.
Typer: S syll, H hammarband, R regel (stående), L liggande (överstycke, bröstning, kortling), D diagonal eller
annat snett virke, P spikplåt, K kloss.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from modellering import Del, Material, Montage, Placering

from .. import skelett as S
from ..material import C24
from . import virke
from .virke import virke_i_lada, virke_profil


@dataclass
class _Bit:
    typ: str
    del_: Del
    plac: Placering            # i väggens system
    sort: tuple[float, float]
    namn: str | None = None


@dataclass
class Plan:
    """Plana stommar (väggar, takstolar): delar i ett system (u, w, z) med namn efter typ och läge."""
    kod: str
    namn: str
    tjocklek: float
    hojd: float = S.H_VAGG               # hammarbandets överkant (standard för regel och hammarband)
    material: Material = C24
    beskrivning: str = ""
    bitar: list[_Bit] = field(default_factory=list)

    def lada(self, typ: str, u0: float, u1: float, w0: float, w1: float, z0: float, z1: float, fiber: str,
             material: Material | None = None, namn: str | None = None) -> Plan:
        """Rakt virke som fyller lådan, fibrer längs "u", "w" eller "z"."""
        d, p = virke_i_lada(u0, u1, w0, w1, z0, z1, {"u": "x", "w": "y", "z": "z"}[fiber], material or self.material)
        self.bitar.append(_Bit(typ, d, p, (min(u0, u1), min(z0, z1)), namn))
        return self

    def regel(self, u: float, z0: float = 45.0, z1: float | None = None, w0: float = 0.0, w1: float | None = None,
              b: float = 45.0, namn: str | None = None) -> Plan:
        """Stående regel från u till u + b."""
        return self.lada("R", u, u + b, w0, self.tjocklek if w1 is None else w1, z0,
                         self.hojd - 45.0 if z1 is None else z1, "z", namn=namn)

    def liggande(self, u0: float, u1: float, z0: float, h: float = 45.0, w0: float = 0.0, w1: float | None = None,
                 typ: str = "L", material: Material | None = None, namn: str | None = None) -> Plan:
        return self.lada(typ, u0, u1, w0, self.tjocklek if w1 is None else w1, z0, z0 + h, "u", material, namn)

    def syll(self, u0: float, u1: float, w0: float = 0.0, w1: float | None = None) -> Plan:
        return self.liggande(u0, u1, 0.0, w0=w0, w1=w1, typ="S")

    def hammarband(self, u0: float, u1: float, z1: float | None = None, w0: float = 0.0,
                   w1: float | None = None) -> Plan:
        return self.liggande(u0, u1, (self.hojd if z1 is None else z1) - 45.0, w0=w0, w1=w1, typ="H")

    def profil(self, pts: Sequence[Sequence[float]], w0: float = 0.0, w1: float | None = None, typ: str = "R",
               material: Material | None = None, namn: str | None = None,
               tillagg: Sequence[tuple[Sequence[Sequence[float]], float, float]] = (),
               bas_namn: str | None = None) -> Plan:
        """Virke med profilen (u, z) genom väggen från w0 till w1. `tillagg`: fler profiler (punkter, avstånd från
        w1, tjocklek) i samma del (virke_profil)."""
        w1 = self.tjocklek if w1 is None else w1
        d, p = virke_profil(pts, w1 - w0, material or self.material, tillagg=tillagg, bas_namn=bas_namn)
        # profilens system: x = u, y = z, extruderad längs −w från w1
        bas = Placering(((1.0, 0.0, 0.0), (0.0, 0.0, -1.0), (0.0, 1.0, 0.0)), (0.0, w1, 0.0))
        self.bitar.append(_Bit(typ, d, bas @ p, (min(x for x, _ in pts), min(z for _, z in pts)), namn))
        return self

    def skiva(self, pts: Sequence[Sequence[float]], hal: Sequence[Sequence[Sequence[float]]], w0: float, w1: float,
              typ: str, material: Material, namn_del: str, namn: str | None = None) -> Plan:
        """Skiva med kontur och hål i (u, z), från w0 till w1 genom väggen."""
        d = virke.skiva([tuple(p) for p in pts], w1 - w0, material, namn_del, [[tuple(p) for p in h] for h in hal])
        bas = Placering(((1.0, 0.0, 0.0), (0.0, 0.0, -1.0), (0.0, 1.0, 0.0)), (0.0, w1, 0.0))
        self.bitar.append(_Bit(typ, d, bas, (min(x for x, _ in pts), min(z for _, z in pts)), namn))
        return self

    def tvarprofil(self, pts: Sequence[Sequence[float]], u0: float, u1: float, typ: str = "R",
                   material: Material | None = None, namn: str | None = None) -> Plan:
        """Virke med profilen (w, z), från u0 till u1 längs väggen."""
        d, p = virke_profil(pts, u1 - u0, material or self.material)
        # profilens system: x = w, y = z, extruderad längs +u från u0
        bas = Placering(((0.0, 0.0, 1.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)), (u0, 0.0, 0.0))
        self.bitar.append(_Bit(typ, d, bas @ p, (u0, min(z for _, z in pts)), namn))
        return self

    def del_i(self, typ: str, d: Del, plac: Placering, sort: tuple[float, float], namn: str | None = None) -> Plan:
        """Godtycklig del placerad i väggens system."""
        self.bitar.append(_Bit(typ, d, plac, sort, namn))
        return self

    def montage(self) -> Montage:
        m = Montage(self.namn, self.kod, self.beskrivning)
        raknare: dict[str, int] = {}
        for b in sorted(self.bitar, key=lambda b: (b.typ, round(b.sort[0], 3), round(b.sort[1], 3))):
            if b.namn:
                n = b.namn
            else:
                raknare[b.typ] = raknare.get(b.typ, 0) + 1
                n = f"{self.kod}-{b.typ}{raknare[b.typ]:02d}"
            m.lagg(b.del_, b.plac, n)
        return m


def regelvagg(kod: str, hojd: float = S.H_VAGG, namn: str | None = None) -> Plan:
    v = S.VAGGAR[kod]
    return Plan(kod, namn or f"Vägg {kod}", v.tjocklek, hojd, beskrivning=v.beskrivning)
