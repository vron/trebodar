"""Tappvattnets produkttyper: tappställen (vad som förbrukar vatten, med normflöden), anslutningsdosor, rör (rör-i-rör
och matarledningar) och fördelare. En typ beskriver en produkt en gång (katalog.py); punkterna refererar till den.
Mått i mm, flöden i l/s.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Tappstalletyp:
    """Ett tappställe och dess normflöden för kallvatten och varmvatten (0: ingen anslutning)."""
    kod: str
    namn: str
    kv: float
    vv: float
    symbol: str                 # kort beteckning på ritningarna, t.ex. "WC", "DU"


@dataclass(frozen=True)
class Dosatyp:
    """Anslutningen vid tappstället: väggdosa i väggen (rören upp i regelfacket), golvdosa (rören upp genom golvet i
    skåpet under tappstället), väggfäste utanpå källarens vägg eller hylsor ("hylsa": en ingjuten hylsa i bjälklaget
    per rör, b dess diameter, och kopparrören från underfördelaren under taket i källaren och rakt upp genom dem, med
    kopplingarna och avstängningarna i källaren); cc: avståndet mellan kallt och varmt. En underfördelares inlopp
    ("fördelare") är rören rakt ned ur bjälklaget till stammarnas början."""
    kod: str
    namn: str
    slag: str                   # "vägg", "golv", "utanpå", "hylsa" eller "fördelare"
    b: float
    h: float
    djup: float
    cc: float = 0.0


@dataclass(frozen=True)
class Rortyp:
    """Rör: PEX eller koppar (koden CU) med ytterdiametern d och godstjockleken t, i skyddsrör med ytterdiametern
    skydd (rör-i-rör; 0: utan)."""
    kod: str
    namn: str
    d: float
    t: float
    skydd: float = 0.0

    @property
    def d_inre(self) -> float:
        return self.d - 2 * self.t

    @property
    def area(self) -> float:
        """Invändig area [mm²]."""
        return math.pi * self.d_inre ** 2 / 4

    @property
    def liter_per_m(self) -> float:
        return self.area / 1000.0

    @property
    def yttre(self) -> float:
        """Ytterdiametern med skyddsröret."""
        return self.skydd or self.d

    @property
    def matt(self) -> str:
        return f"{self.d:g}/{self.skydd:g}" if self.skydd else f"{self.d:g}"


@dataclass(frozen=True)
class Fordelartyp:
    """Fördelare (stam med utgångar) för kallvatten eller varmvatten i fördelarskåpet."""
    kod: str
    namn: str
    utgangar: int
    delning: float              # avståndet mellan utgångarna [mm]
