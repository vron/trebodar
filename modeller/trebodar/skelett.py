"""Skelettet: husets globala referensgeometri. Alla delar härleder sina lägen härifrån.

Koordinater som i K-05 (mm): x och y från skärningen mellan mellanbjälklagets kanter, z från bjälklagets
överkant. Huskroppar 1 (vänster), 2 (mittre) och 3 (höger); väderstreck NO, SO, SV och NV som i väggarnas namn
(gavlarna mot NO och SV, långsidorna mot SO och NV). Nock- och dalbalkarnas linjer numreras från höger: NB1, DB2,
NB3, DB4, NB5 (K-01).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from modellering import Placering

# ------------------------------------------------------------------ nivåer och mått
H_BJALKLAG = 150.0          # mellanbjälklagets tjocklek (z −150 … 0)
H_VAGG = 2490.0             # ytterväggarnas höjd: hammarbandets överkant
T_STOMME = 95.0             # väggstommen 45×95
STOMME_UT = 30.0            # stommens utsida utanför bjälklagets kant (K-05)
T_FASAD = 65.0              # utegips 10 + ströläkt 12 + spikläkt 21 + panel 22
TAKVINKEL = 30.0
TAN = math.tan(math.radians(TAKVINKEL))
COS = math.cos(math.radians(TAKVINKEL))
SIN = math.sin(math.radians(TAKVINKEL))
TAKBALK_B = 45.0
TAKBALK_H = 170.0
TAKBALK_HV = TAKBALK_H / COS        # takbalkens höjd i lodled
TAKBALK_CC = 600.0
TAKFOT_UTSPRANG = 70.0      # takbalkarnas ände utanför fasaden (vågrätt)
TAKLYFT = 10.0              # takplanen ligger 10 mm över Onshape-modellens, så att skiva och luftspalt går över
                            # dalbalkarna (balkarna är 200 höga i stället för HEA 200:s 190, underkanten oförändrad)

# Mellanbjälklagets kontur (K-05) och trapphål
KONTUR = ((4500.0, 0.0), (9310.0, 0.0), (9310.0, 1000.0), (13810.0, 1000.0), (13810.0, 12510.0),
          (9500.0, 12510.0), (9500.0, 11010.0), (4310.0, 11010.0), (4310.0, 15900.0), (0.0, 15900.0),
          (0.0, 3590.0), (4500.0, 3590.0))
TRAPPHAL = ((7348.0, 5059.5), (9418.0, 5059.5), (9418.0, 5887.5), (7348.0, 5887.5))


@dataclass(frozen=True)
class Huskropp:
    nr: int
    namn: str
    x0: float                # bjälklagets kant (stommens utsida = kant − 30)
    x1: float
    y0: float
    y1: float
    nock: float              # nockbalkens centrumlinje

    @property
    def halvbredd(self) -> float:
        """Från nocken till stommens utsida."""
        return self.nock - self.x0 + STOMME_UT


HUSKROPPAR = {
    1: Huskropp(1, "vänstra huskroppen", 0.0, 4310.0, 3590.0, 15900.0, 2155.0),
    2: Huskropp(2, "mittre huskroppen", 4500.0, 9310.0, 0.0, 11010.0, 6905.0),
    3: Huskropp(3, "högra huskroppen", 9500.0, 13810.0, 1000.0, 12510.0, 11655.0),
}


# ------------------------------------------------------------------ väggar

@dataclass(frozen=True)
class Vaggdef:
    """En väggs läge. Väggens system: origo i väggens början på dess yttre yta (w = 0) vid bjälklagets överkant,
    u längs väggen, w = z × u (för ytterväggar inåt, eftersom u går moturs runt huskroppen sett ovanifrån),
    z uppåt."""
    kod: str
    origo: tuple[float, float]
    u: tuple[float, float]       # riktning längs väggen (enhetsvektor i planet)
    langd: float
    tjocklek: float
    beskrivning: str

    @property
    def w(self) -> tuple[float, float]:
        return (-self.u[1], self.u[0])

    def placering(self) -> Placering:
        ux, uy = self.u
        wx, wy = self.w
        return Placering(((ux, wx, 0.0), (uy, wy, 0.0), (0.0, 0.0, 1.0)), (self.origo[0], self.origo[1], 0.0))


_PX, _NX, _PY, _NY = (1.0, 0.0), (-1.0, 0.0), (0.0, 1.0), (0.0, -1.0)

YTTERVAGGAR = {v.kod: v for v in (
    Vaggdef("1NO", (-30.0, 3560.0), _PX, 4595.0, T_STOMME, "vänstra huskroppens gavel mot NO"),
    Vaggdef("1SO", (-30.0, 15835.0), _NY, 12180.0, T_STOMME, "vänstra huskroppens långsida mot SO"),
    Vaggdef("1SV", (4340.0, 15930.0), _NX, 4370.0, T_STOMME, "vänstra huskroppens gavel mot SV"),
    Vaggdef("1NV", (4340.0, 11040.0), _PY, 4795.0, T_STOMME, "vänstra huskroppens långsida mot NV"),
    Vaggdef("2NO", (4470.0, -30.0), _PX, 4870.0, T_STOMME, "mittre huskroppens gavel mot NO"),
    Vaggdef("2NV", (9340.0, 65.0), _PY, 905.0, T_STOMME, "mittre huskroppens långsida mot NV"),
    Vaggdef("2SV", (9565.0, 11040.0), _NX, 5320.0, T_STOMME, "mittre huskroppens gavel mot SV"),
    Vaggdef("2SO", (4470.0, 3560.0), _NY, 3495.0, T_STOMME, "mittre huskroppens långsida mot SO"),
    Vaggdef("3NO", (9245.0, 970.0), _PX, 4595.0, T_STOMME, "högra huskroppens gavel mot NO"),
    Vaggdef("3NV", (13840.0, 1065.0), _PY, 11380.0, T_STOMME, "högra huskroppens långsida mot NV"),
    Vaggdef("3SV", (13840.0, 12540.0), _NX, 4370.0, T_STOMME, "högra huskroppens gavel mot SV"),
    Vaggdef("3SO", (9470.0, 12445.0), _NY, 1405.0, T_STOMME, "högra huskroppens långsida mot SO"),
)}

# Bärande innerväggar: kroppens nummer och en bokstav i växande y. Mått som i Onshape-modellen.
INNERVAGGAR = {v.kod: v for v in (
    Vaggdef("1A", (65.0, 7115.0), _PX, 1995.0, 70.0, "vänstra huskroppen, y 7 150, från långsidan till nocken"),
    Vaggdef("1B", (2130.0, 7115.0), _PY, 2210.0, 70.0, "vänstra huskroppen, under nockbalk 5, y 7 115–9 325"),
    Vaggdef("1C", (2060.0, 8185.0), _PX, 1285.0, 70.0, "vänstra huskroppen, y 8 220, med stolpen LN5_1"),
    Vaggdef("1D", (65.0, 10952.5), _PX, 2078.0, 95.0, "vänstra huskroppen, y 11 000, med stolpen LN5_2"),
    Vaggdef("2A", (6917.0, 2152.5), _PX, 2453.0, 95.0, "mittre huskroppen, y 2 200, med stolpen LN3_1"),
    Vaggdef("2B", (9440.0, 1065.0), _PY, 6297.0, 70.0, "under dalbalk 2, med stolparna LD2_1–LD2_3"),
    Vaggdef("2C", (4417.0, 5900.0), _PX, 4953.0, 95.0, "mittre huskroppen, y 5 950, med takstolen 2C"),
)}

VAGGAR = {**YTTERVAGGAR, **INNERVAGGAR}


# ------------------------------------------------------------------ takfall

@dataclass(frozen=True)
class Takfall:
    """Ett takfall: takbalkarnas överkant ligger i ett plan med lutningen 30°, stigande mot nocken.
    Takbalkens underkant går 10 mm (TAKLYFT) över takfotsväggens hammarband vid dess insida."""
    kod: str                     # som takfotsväggen, t.ex. "1SO"
    kropp: int
    x_insida: float              # takfotsväggens insida
    riktning: int                # +1 om planet stiger mot växande x, −1 annars

    def z_underkant(self, x: float) -> float:
        return H_VAGG + TAKLYFT + self.riktning * (x - self.x_insida) * TAN

    def z_overkant(self, x: float) -> float:
        """Takbalkarnas överkant (det bärande takplanet) i läget x."""
        return self.z_underkant(x) + TAKBALK_HV


TAKFALL = {t.kod: t for t in (
    Takfall("1SO", 1, 65.0, +1), Takfall("1NV", 1, 4245.0, -1),
    Takfall("2SO", 2, 4565.0, +1), Takfall("2NV", 2, 9245.0, -1),
    Takfall("3SO", 3, 9565.0, +1), Takfall("3NV", 3, 13745.0, -1),
)}


# ------------------------------------------------------------------ nock- och dalbalkar (K-01)

@dataclass(frozen=True)
class Balklinje:
    kod: str                     # NB1, DB2 ...
    k01: str                     # namnet i K-01, t.ex. "Nockbalk 1"
    typ: str                     # "nock" eller "dal"
    x: float                     # centrumlinje
    y0: float
    y1: float
    uk: float                    # underkant (som HEA 200 i Onshape-modellen)

    @property
    def ok(self) -> float:
        return self.uk + BALK_H


BALK_B = 190.0
BALK_H = 200.0
_UK_NOCK = TAKFALL["1SO"].z_overkant(2155.0 - 100.0) - TAKLYFT - 190.0      # HEA 200: överkant i takbalkarnas
_UK_NOCK3 = TAKFALL["2SO"].z_overkant(6905.0 - 100.0) - TAKLYFT - 190.0     # överkant vid flänsens kant
_UK_DAL = TAKFALL["2SO"].z_overkant(4405.0) - TAKLYFT - 190.0               # i takplanens skärning

BALKAR = {b.kod: b for b in (
    Balklinje("NB1", "Nockbalk 1", "nock", 11655.0, 970.0, 12540.0, _UK_NOCK),
    Balklinje("DB2", "Dalbalk 2", "dal", 9405.0, 970.0, 11040.0, _UK_DAL),
    Balklinje("NB3", "Nockbalk 3", "nock", 6905.0, -30.0, 11040.0, _UK_NOCK3),
    Balklinje("DB4", "Dalbalk 4", "dal", 4405.0, 3560.0, 11040.0, _UK_DAL),
    Balklinje("NB5", "Nockbalk 5", "nock", 2155.0, 3560.0, 15930.0, _UK_NOCK),
)}

# Onshape-modellens globala system -> K-05 (exakt, ur modellens koordinater; K-05 avrundar till 0,1 mm)
ONSHAPE_TILL_K05 = Placering.flytt(12147.71107, 1292.10135, -13939.88713)
