"""Ventilationens produkttyper: kanaler, don där luften tas ut ur rummen (frånluftsdon, köksfläktar, väggfläktar),
kanalfläktar, övergångar mellan kanaltyper och avluftsdon där luften lämnar huset (galler på fasaden, huvar på taket).
En typ beskriver en produkt en gång (katalog.py); grenarna refererar till den. Mått i mm, flöden i l/s.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Kanaltyp:
    """Kanal: rund (b = h = ytterdiametern) eller platt (bredden b och tjockleken h), med isolering runt kanalen där
    den går genom kalla delar (takets isolering, ytterväggen)."""
    kod: str
    namn: str
    form: str                   # "rund" eller "platt"
    b: float
    h: float
    isolering: float = 0.0      # isoleringens tjocklek [mm]

    @property
    def area(self) -> float:
        """Kanalens tvärsnitt [mm²]."""
        return math.pi * self.b ** 2 / 4 if self.form == "rund" else self.b * self.h

    @property
    def yttre(self) -> tuple[float, float]:
        """Yttermåtten med isoleringen (bredd, tjocklek) [mm]."""
        return self.b + 2 * self.isolering, self.h + 2 * self.isolering

    @property
    def matt(self) -> str:
        """Måttet som det skrivs: Ø125 eller 204 × 60."""
        return f"Ø{self.b:g}" if self.form == "rund" else f"{self.b:g} × {self.h:g}"


@dataclass(frozen=True)
class Dontyp:
    """Frånluftsdon i tak eller vägg: frontens diameter, anslutningens diameter och djupet bakom fronten."""
    kod: str
    namn: str
    anslutning: float
    front_d: float
    djup: float
    flode: float                # största flöde [l/s]


@dataclass(frozen=True)
class Koksflakttyp:
    """Köksfläkt med egen fläkt, på väggen: kåpan (bredd längs väggen, djup ut från väggen, höjd), skorstenskåpan
    från kåpan upp till innertaket och utloppet i kåpans överkant."""
    kod: str
    namn: str
    tillverkare: str            # "" tills produkten är vald
    artikel: str
    b: float
    d: float
    h: float
    skorsten: tuple[float, float]       # skorstenskåpans bredd och djup
    anslutning: float                   # utloppets diameter
    utlopp: float                       # utloppets mitt från väggen
    flode: float                        # forcerat flöde [l/s]
    flode_normal: float                 # normalt flöde [l/s]
    produkt: str = ""           # specialprodukt i inköpslistan (IN-01): dess kod; tom: ingen


@dataclass(frozen=True)
class Vaggflakttyp:
    """Väggfläkt (badrum): fläkten i röret genom ytterväggen, frontkåpan på väggens insida."""
    kod: str
    namn: str
    tillverkare: str
    artikel: str
    anslutning: float           # rörets diameter
    front: tuple[float, float, float]   # frontkåpans bredd, höjd och djup
    flode: float                # forcerat flöde [l/s]
    flode_normal: float         # grundflöde [l/s]


@dataclass(frozen=True)
class Kanalflakttyp:
    """Rund kanalfläkt mellan två kanaler: husets diameter och längd, anslutningarna."""
    kod: str
    namn: str
    tillverkare: str
    artikel: str
    anslutning: float
    d: float
    langd: float
    flode: float                # största flöde [l/s] vid kanalsystemets tryckfall


@dataclass(frozen=True)
class Overgangstyp:
    """Övergång mellan två kanaltyper (rund och platt), längden längs kanalen."""
    kod: str
    namn: str
    fran: Kanaltyp
    till: Kanaltyp
    langd: float


@dataclass(frozen=True)
class Avluftstyp:
    """Avluftsdon där luften lämnar huset: galler på fasaden (fronten b × h, djup ut från fasaden) eller takhuv
    (huvens diameter b och höjd h över taket)."""
    kod: str
    namn: str
    slag: str                   # "galler" eller "takhuv"
    anslutning: float
    b: float
    h: float
    djup: float = 0.0
    backspjall: bool = False
