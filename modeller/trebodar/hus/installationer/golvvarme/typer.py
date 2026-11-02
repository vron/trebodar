"""Golvvärmens produkttyper: rören (i slingorna, tilloppen och matarledningarna) och fördelarna. En typ beskriver en
produkt en gång (katalog.py). Mått i mm, längder i m.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Rortyp:
    """Rör med ytterdiametern d och godstjockleken t; max_langd: slingans längsta längd med tilloppen [m]."""
    kod: str
    namn: str
    d: float
    t: float
    max_langd: float = 0.0

    @property
    def liter_per_m(self) -> float:
        return math.pi * (self.d - 2 * self.t) ** 2 / 4 / 1000.0

    @property
    def matt(self) -> str:
        return f"{self.d:g} × {self.t:g}".replace(".", ",")


@dataclass(frozen=True)
class Fordelartyp:
    """Golvvärmefördelare: framledningens och returens stammar med utgångar för högst `kretsar` slingor."""
    kod: str
    namn: str
    kretsar: int
