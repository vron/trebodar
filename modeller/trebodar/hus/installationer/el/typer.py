"""Elinstallationens produkttyper: armaturer (ljusdata och mått; infällda, på stam eller pendlar), apparater (brytare,
dimrar, uttag), dosor och rör.
En typ beskriver en produkt en gång (katalog.py); punkterna i rummen refererar till den.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Dosatyp:
    """Dosa: apparatdosa i vägg (för brytare och uttag), kopplingsdosa i innertaket eller ingjutningsdosa i betong."""
    kod: str
    namn: str
    slag: str                   # "apparatdosa", "kopplingsdosa", "ingjutningsdosa"; "central" och "brandlarm" är
    #                             punkter utan egen geometri (centralen i teknikrummet, brandlarmets matningsdosa)
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
class Tubhuvud:
    """Spotens huvud under taket: en tub på en stam från frontplattan (infälld) eller takkoppen (utanpåliggande),
    vridbar kring stammen och lutbar i leden där stammen fäster i tubens sida (mått i mm)."""
    diameter: float             # tubens diameter
    langd: float                # tubens längd
    stam: float                 # stammens längd från frontplattan (takkoppen) till leden
    stam_d: float               # stammens diameter
    led: float                  # ledens läge längs tuben, från den bakre änden
    indrag: float               # reflektorn (den lysande ytan) så långt in från tubens front
    kopp: float = 0.0           # utanpåliggande: takkoppens höjd (frontplattans diameter är takkoppens); 0: infälld


@dataclass(frozen=True)
class Pendel:
    """Pendelarmatur: armaturen hänger i en sladd från en takkopp på innertaket, eller (vägglampa, arm > 0) under
    änden av en arm från en väggplatta. Formen ger geometrin ur måtten (el.py); ljuskällan (en lampa i armaturens
    sockel) sitter mitt i armaturen kalla under dess överkant. I renderingen formas ljuset av armaturens delar:
    skärmarna skuggar och reflekterar, glaset skuggar inte men lyser med sin luminans (flödet genom glaset fördelat
    på dess yta)."""
    form: str                   # "ph5", "vl45", "glob" eller "stav" (el.py)
    diameter: float             # armaturens största diameter [mm]
    hojd: float                 # från överkanten (där sladden går in) till underkanten [mm]
    kalla: float                # ljuskällans mitt under armaturens överkant [mm]
    kalla_d: float              # ljuskällans diameter [mm]
    ljuskalla: str              # lampan i sockeln, t.ex. "E27 LED 1 055 lm 2 700 K (ej vald)"
    lysande_yta: float          # glasets yta, där ljuset syns [mm²]
    lysande_andel: float        # andel av ljuskällans flöde som går ut genom glaset
    transmission: float = 1.0   # glasets transmission, för glas som omsluter ljuskällan (globerna)
    sladd: str = "vit"          # textilsladdens färg: "vit" eller "svart"
    takkopp: tuple[float, float] = (90.0, 25.0)       # takkoppens diameter och höjd [mm]
    takkopp_massing: bool = False                       # takkoppen (och globens kåpa) i mässing (annars vit)
    arm: float = 0.0            # vägglampa: armen från väggplattan (takkoppen på väggen) till armaturens överkant [mm]


@dataclass(frozen=True)
class Armaturtyp:
    """Armatur med tillverkarens data (datablad och fotometrifil) och mått för modellen och renderingen: infälld
    (ljuset ut genom takets hål), med ett huvud under taket (huvud, t.ex. en tub på en stam) eller en pendel (pendel).
    För pendlar är ljusflödet ljuskällans, ringen takkoppen och hålet, djupet och strålvinkeln 0 (ingen fotometrifil:
    ljuskällan lyser lika åt alla håll)."""
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
    ring_d: float               # frontringens eller frontplattans diameter [mm]
    hal_d: float                # håltagningen [mm]
    djup: float                 # inbyggnadsdjupet ovanför takytan [mm]
    lysande_d: float            # den lysande ytans diameter [mm]
    brandavstand: float         # minsta avstånd från den lysande ytan till brännbart material i ljusets riktning
                                # (databladets "distance to flammable materials", märkningen enligt EN 60598-1) [mm]
    drivdon: tuple[float, float, float] | None     # separat drivdon (längd, bredd, höjd) [mm]
    fotometri: str              # fotometrifilen (EULUMDAT) under lokalt/el/ (versionshanteras inte)
    fotometri_url: str          # var den hämtas (`./mod el hamta`)
    symbol: str = "spot"
    huvud: Tubhuvud | None = None               # huvudet under taket; None: infälld
    pendel: Pendel | None = None                # pendelarmatur
    produkt: str = ""           # specialprodukt i inköpslistan (IN-01): dess kod; tom: ingen
    isoleras: bool = False      # infälld: får täckas med värmeisolering (monteringsanvisningen; SG: IsoSafe)
    min_djup: float = 0.0       # infälld som inte får täckas: minsta fria höjd från takytan ovanför den [mm]
    min_volym: float = 0.0      # infälld som inte får täckas: minsta luftvolym i hålrummet runt den [l]
    panel: tuple[float, float, float] | None = None    # utanpåliggande panel: längd, bredd, höjd med ramen [mm]
    dosa: Dosatyp | None = None  # utanpåliggande på betong: den ingjutna dosan ovanför, där armaturen ansluts


@dataclass(frozen=True)
class Rortyp:
    """Elrör (flexibelt eller styvt) för ledningar i betong, väggar och innertak."""
    kod: str
    namn: str
    ytterdiameter: float        # [mm]
    bojradie: float             # minsta böjradie [mm]
