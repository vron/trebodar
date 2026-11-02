"""Elinstallationens produkttyper: armaturer (ljusdata och mått), apparater (brytare, dimrar, uttag), dosor och rör.
En typ beskriver en produkt en gång (katalog.py); punkterna i rummen refererar till den.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Dosatyp:
    """Dosa: apparatdosa i vägg (för brytare och uttag), kopplingsdosa i innertaket eller ingjutningsdosa i betong."""
    kod: str
    namn: str
    slag: str                   # "apparatdosa", "kopplingsdosa", "ingjutningsdosa"
    diameter: float             # håltagningen eller dosans diameter [mm]
    djup: float                 # [mm]
    symbol: str = "dosa"        # symbolen på elritningarna


@dataclass(frozen=True)
class Apparattyp:
    """Brytare, dimmer eller uttag i en apparatdosa, med täckram."""
    kod: str
    namn: str
    slag: str                   # "brytare", "dimmer", "uttag"
    kanaler: int                # tändgrupper som apparaten styr, eller uttagen i ramen
    ram: tuple[float, float]    # täckramens bredd och höjd [mm]
    dosa: Dosatyp
    symbol: str                 # symbolen på elritningarna


@dataclass(frozen=True)
class Armaturtyp:
    """Armatur med tillverkarens data (datablad och fotometrifil) och mått för modellen och renderingen."""
    kod: str
    namn: str                   # tillverkarens namn på varianten
    tillverkare: str
    artikel: str                # tillverkarens artikelnummer
    url: str                    # produktsidan: datablad, fotometri, monteringsanvisning
    ljusflode: float            # armaturens ljusflöde [lm]
    effekt: float               # systemeffekt [W]
    fargtemperatur: float       # [K]
    ra: float                   # färgåtergivning, minst
    stralvinkel: float          # strålvinkel enligt databladet [°]
    vridbar: float              # hur långt ljuset kan riktas från armaturens axel [°] (0: fast)
    ip: str
    dimring: str                # "bakkant", "DALI" eller "ingen"
    ring_d: float               # frontringens diameter [mm]
    hal_d: float                # håltagningen [mm]
    djup: float                 # inbyggnadsdjupet ovanför takytan [mm]
    lysande_d: float            # den lysande ytans diameter [mm]
    brandavstand: float         # minsta avstånd till brännbart material [mm]
    drivdon: tuple[float, float, float] | None     # separat drivdon (längd, bredd, höjd) [mm]
    fotometri: str              # fotometrifilen (EULUMDAT) under lokalt/el/ (versionshanteras inte)
    fotometri_url: str          # var den hämtas (`./mod el hamta`)
    symbol: str = "spot"


@dataclass(frozen=True)
class Rortyp:
    """Elrör (flexibelt eller styvt) för ledningar i betong, väggar och innertak."""
    kod: str
    namn: str
    ytterdiameter: float        # [mm]
    bojradie: float             # minsta böjradie [mm]
