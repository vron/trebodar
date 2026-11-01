"""Former som data: recept (CSG-träd av oföränderliga värden) som kärnan översätter till exakt B-rep.

Geometriskripten bygger bara recept. De känner inte till OCCT eller exportformaten. Ett recept är hashbart (cache,
delade nät och produkter för likadana delar) och kan skrivas som JSON.

Konventioner: mm, högerhänt system. Virke definieras med lokala x längs fibrerna (materiallistans längd,
texturens riktning).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields, is_dataclass
from typing import Sequence

from .placering import Placering, Vek

P2 = tuple[float, float]
Kontur = tuple[P2, ...]
Hal = tuple[float, float, float]          # (x, y, diameter) för cirkulära hål i Prisma


class Form:
    """Basklass för recept. Operatorer: a - b (differens), a | b (union), a & b (snitt)."""

    def __sub__(self, o: Form) -> Form:
        if isinstance(self, Diff):
            return Diff(self.bas, self.verktyg + (o,))
        return Diff(self, (o,))

    def __or__(self, o: Form) -> Form:
        return Union((self, o))

    def __and__(self, o: Form) -> Form:
        return Snitt((self, o))

    def placerad(self, p: Placering) -> Form:
        return self if p.ar_identitet() else Transf(self, p)

    def kapad(self, punkt: Sequence[float], normal: Sequence[float]) -> Form:
        """Behåll den del som ligger bakom planet (mot normalens baksida) genom punkten."""
        return Kapad(self, _v(punkt), _v(normal))

    def speglad(self, punkt: Sequence[float], normal: Sequence[float]) -> Form:
        """Spegelbild i planet genom punkten med normalen."""
        return Speglad(self, _v(punkt), _v(normal))

    def data(self) -> object:
        return _data(self)

    def nyckel(self) -> str:
        return hashlib.sha1(json.dumps(_data(self), sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:20]


@dataclass(frozen=True)
class Lada(Form):
    """Rätblock från origo längs +x, +y, +z."""
    dx: float
    dy: float
    dz: float
    origo: Vek = (0.0, 0.0, 0.0)


@dataclass(frozen=True)
class Prisma(Form):
    """Polygon i lokala xy, med polygonhål och cirkulära hål, extruderad längs +z från z0 till z0 + tjocklek."""
    kontur: Kontur
    tjocklek: float
    hal: tuple[Kontur, ...] = ()
    z0: float = 0.0
    cirkelhal: tuple[Hal, ...] = ()


@dataclass(frozen=True)
class Cylinder(Form):
    """Cylinder längs +z från origo."""
    radie: float
    hojd: float
    origo: Vek = (0.0, 0.0, 0.0)


@dataclass(frozen=True)
class Diff(Form):
    bas: Form
    verktyg: tuple[Form, ...]


@dataclass(frozen=True)
class Union(Form):
    delar: tuple[Form, ...]


@dataclass(frozen=True)
class Snitt(Form):
    delar: tuple[Form, ...]


@dataclass(frozen=True)
class Transf(Form):
    form: Form
    placering: Placering


@dataclass(frozen=True)
class Kapad(Form):
    form: Form
    punkt: Vek
    normal: Vek


@dataclass(frozen=True)
class Speglad(Form):
    form: Form
    punkt: Vek
    normal: Vek


@dataclass(frozen=True)
class Importerad(Form):
    """Solid ur en BREP-fil (sökväg relativt repots rot). `sha` är filens innehållshash och ingår i nyckeln."""
    fil: str
    sha: str


def _v(p: Sequence[float]) -> Vek:
    return (float(p[0]), float(p[1]), float(p[2]))


def _data(o: object) -> object:
    if is_dataclass(o) and not isinstance(o, type):
        return {"_": type(o).__name__, **{f.name: _data(getattr(o, f.name)) for f in fields(o)}}
    if isinstance(o, (tuple, list)):
        return [_data(v) for v in o]
    if isinstance(o, float):
        r = round(o, 9)
        return 0.0 if r == 0 else r
    return o


# ------------------------------------------------------------------ byggstenar

def lada(dx: float, dy: float, dz: float, origo: Sequence[float] = (0.0, 0.0, 0.0)) -> Lada:
    return Lada(float(dx), float(dy), float(dz), _v(origo))


def box(x0: float, x1: float, y0: float, y1: float, z0: float, z1: float) -> Lada:
    """Rätblock mellan två hörn (koordinaterna i valfri ordning)."""
    xa, xb = sorted((x0, x1))
    ya, yb = sorted((y0, y1))
    za, zb = sorted((z0, z1))
    return Lada(xb - xa, yb - ya, zb - za, (float(xa), float(ya), float(za)))


def prisma(kontur: Sequence[Sequence[float]], tjocklek: float, hal: Sequence[Sequence[Sequence[float]]] = (),
           z0: float = 0.0, cirkelhal: Sequence[Sequence[float]] = ()) -> Prisma:
    return Prisma(tuple((float(x), float(y)) for x, y in kontur), float(tjocklek),
                  tuple(tuple((float(x), float(y)) for x, y in h) for h in hal), float(z0),
                  tuple((float(x), float(y), float(d)) for x, y, d in cirkelhal))


def rektangel(x0: float, y0: float, x1: float, y1: float) -> Kontur:
    return ((x0, y0), (x1, y0), (x1, y1), (x0, y1))


def cylinder(radie: float, hojd: float, origo: Sequence[float] = (0.0, 0.0, 0.0)) -> Cylinder:
    return Cylinder(float(radie), float(hojd), _v(origo))
