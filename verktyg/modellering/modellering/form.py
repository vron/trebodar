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
from typing import Iterable, Sequence

import numpy as np

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
        k = self.__dict__.get("_nyckel")             # receptet är oföränderligt: nyckeln räknas en gång
        if k is None:
            k = hashlib.sha1(json.dumps(_data(self), sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:20]
            object.__setattr__(self, "_nyckel", k)
        return k


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
class Svep(Form):
    """Rör: en cirkel med radien svept längs polylinjen genom punkterna, med hörnen avrundade med bojradien (mindre där
    sträckorna är för korta för den)."""
    punkter: tuple[Vek, ...]
    radie: float
    bojradie: float


@dataclass(frozen=True)
class Polyeder(Form):
    """Sluten kropp av plana månghörningar: hörnen och ytorna som index i hörnen (i ordning runt ytan, valfri
    riktning). Grannytor delar hörn exakt. För fria former som stenens kluvna framsida."""
    horn: tuple[Vek, ...]
    ytor: tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class Varv(Form):
    """Rotationskropp: en sluten profil i (r, z), r ≥ 0, vriden ett varv kring z-axeln. Profilen är delar som möts i
    ändpunkterna, den sista i den förstas början: ("linje", punkter) raka streck mellan punkterna och ("kurva",
    punkter) en mjuk kurva (spline) genom punkterna, för lampskärmar, glober och svarvade delar."""
    profil: tuple[tuple[str, tuple[P2, ...]], ...]


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
    if isinstance(o, Form):                          # delrecept som delas mellan former räknas en gång
        d = o.__dict__.get("_data")
        if d is None:
            d = {"_": type(o).__name__, **{f.name: _data(getattr(o, f.name)) for f in fields(o)}}  # type: ignore[arg-type]
            object.__setattr__(o, "_data", d)
        return d
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


def svep(punkter: Sequence[Sequence[float]], radie: float, bojradie: float) -> Svep:
    """Rör längs polylinjen (punkter i föräldern), med avrundade hörn."""
    return Svep(tuple(_v(q) for q in punkter), float(radie), float(bojradie))


def polyeder(horn: Sequence[Sequence[float]], ytor: Sequence[Sequence[int]]) -> Polyeder:
    return Polyeder(tuple(_v(p) for p in horn), tuple(tuple(int(i) for i in y) for y in ytor))


def varv(*delar: tuple[str, Sequence[Sequence[float]]]) -> Varv:
    """Rotationskropp ur profilens delar ("linje" eller "kurva", punkter (r, z)), se Varv."""
    for typ, pts in delar:
        if typ not in ("linje", "kurva") or len(pts) < 2:
            raise ValueError(f"profilens del: {typ} med {len(pts)} punkter")
    return Varv(tuple((typ, tuple((float(r), float(z)) for r, z in pts)) for typ, pts in delar))


def minus(form: Form, verktyg: Iterable[Form]) -> Form:
    """form minus alla verktyg (en boolesk operation)."""
    v = tuple(verktyg)
    return Diff(form, v) if v else form


Lada6 = tuple[float, float, float, float, float, float]


def omslutande(f: Form) -> Lada6 | None:
    """Receptets omslutande låda (x0, y0, z0, x1, y1, z1) i dess eget system, utan kärnan: exakt för rätblock,
    prismor och cylindrar, annars en låda som säkert omsluter formen. None för importerade former."""
    if isinstance(f, Lada):
        o = f.origo
        return (o[0], o[1], o[2], o[0] + f.dx, o[1] + f.dy, o[2] + f.dz)
    if isinstance(f, Prisma):
        xs = [p[0] for p in f.kontur]
        ys = [p[1] for p in f.kontur]
        return (min(xs), min(ys), f.z0, max(xs), max(ys), f.z0 + f.tjocklek)
    if isinstance(f, Cylinder):
        o = f.origo
        return (o[0] - f.radie, o[1] - f.radie, o[2], o[0] + f.radie, o[1] + f.radie, o[2] + f.hojd)
    if isinstance(f, Polyeder):
        H = np.array(f.horn, dtype=float)
        return tuple(float(v) for v in (*H.min(0), *H.max(0)))  # type: ignore[return-value]
    if isinstance(f, Varv):
        # kurvorna kan bukta något utanför sina punkter: marginal
        rz = np.array([p for _, pts in f.profil for p in pts], dtype=float)
        r = float(rz[:, 0].max()) * 1.05 + 1.0
        dz = float(rz[:, 1].max() - rz[:, 1].min()) * 0.05 + 1.0
        return (-r, -r, float(rz[:, 1].min()) - dz, r, r, float(rz[:, 1].max()) + dz)
    if isinstance(f, (Diff, Kapad)):
        return omslutande(f.bas if isinstance(f, Diff) else f.form)
    if isinstance(f, (Union, Snitt)):
        lador = [omslutande(d) for d in f.delar]
        if any(b is None for b in lador):
            return None
        B = np.array(lador, dtype=float)
        if isinstance(f, Union):
            return tuple(float(v) for v in (*B[:, :3].min(0), *B[:, 3:].max(0)))  # type: ignore[return-value]
        return tuple(float(v) for v in (*B[:, :3].max(0), *B[:, 3:].min(0)))  # type: ignore[return-value]
    if isinstance(f, (Transf, Speglad)):
        b = omslutande(f.form)
        if b is None:
            return None
        horn = np.array([[x, y, z] for x in (b[0], b[3]) for y in (b[1], b[4]) for z in (b[2], b[5])])
        if isinstance(f, Transf):
            v = horn @ np.array(f.placering.R).T + np.array(f.placering.t)
        else:
            n = np.array(f.normal) / np.linalg.norm(f.normal)
            v = horn - 2 * ((horn - np.array(f.punkt)) @ n)[:, None] * n
        return tuple(float(c) for c in (*v.min(0), *v.max(0)))  # type: ignore[return-value]
    return None


def i_foraldern(b: Lada6, p: Placering) -> Lada6:
    """Omslutande låda för lådan b placerad med p."""
    horn = np.array([[x, y, z] for x in (b[0], b[3]) for y in (b[1], b[4]) for z in (b[2], b[5])])
    v = horn @ np.array(p.R).T + np.array(p.t)
    return tuple(float(c) for c in (*v.min(0), *v.max(0)))  # type: ignore[return-value]
