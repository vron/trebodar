"""Stommens delar och deras lägen i huset, ur montagen: för skikt och delar som ska gå runt eller ansluta mot
stommen (isoleringen, de invändiga skikten, ströläkten), så att de följer med när stommen ändras i stället för att
ha egna siffror.

Lägena är omslutande lådor (x0, y0, z0, x1, y1, z1) i husets koordinater (prefabstommens montage placeras utan
förflyttning i huset), för takets stomme exakta tvärsnitt i (x, z). Montagen byggs en gång per körning.
"""
from __future__ import annotations

import re
from functools import cache
from typing import NamedTuple

from shapely.geometry import Polygon, box

from modellering import Lada as Ratblock
from modellering import Montage, Prisma, i_foraldern, omslutande

from trebodar import skelett as S
from trebodar.hus.stomme.prefab.innervaggar import innervaggar as _innerv
from trebodar.hus.stomme.prefab.stolpar import stolpar as _stolpar
from trebodar.hus.stomme.prefab.takbalkar import takbalkar
from trebodar.hus.stomme.prefab.takstolar import takstolar as T
from trebodar.hus.stomme.prefab.yttervaggar import yttervaggar as _ytterv

Lada = tuple[float, float, float, float, float, float]
Tvarsnitt = tuple[str, Polygon, float, float]       # (delens namn, tvärsnittet i (x, z), y0, y1)


class Lage(NamedTuple):
    """En stomdels läge: elementet den hör till (väggens, stolpens eller takstolens kod), delens namn och dess
    omslutande låda (x0, y0, z0, x1, y1, z1) i huset."""
    element: str
    namn: str
    lada: Lada

    @property
    def typ(self) -> str:
        """Delens typ ur namnet <element>-<typ><nr>: R regel, S syll, H hammarband, L liggande, D diagonal, U
        underram, X ytterbalk, K kloss, P spikplåt …"""
        m = re.fullmatch(rf"{re.escape(self.element)}-([A-Za-z]+)\d+", self.namn)
        return m.group(1) if m else ""


def ladar(m: Montage) -> tuple[Lada, ...]:
    """Montagets delars omslutande lådor i montagets system."""
    ut = []
    for _, d, p in m.platta():
        b = omslutande(d.form)
        if b is not None:
            ut.append(i_foraldern(b, p))
    return tuple(ut)


def _per_element(m: Montage) -> tuple[Lage, ...]:
    """Delarna i montagets element (barnmontagen, med sin kod), i montagets system."""
    ut = []
    for i in m:
        assert isinstance(i.barn, Montage) and i.barn.kod, (m.namn, i.namn)
        for vag, d, p in i.barn.platta(i.placering):
            b = omslutande(d.form)
            if b is not None:
                ut.append(Lage(i.barn.kod, vag.rsplit("/", 1)[-1], i_foraldern(b, p)))
    return tuple(ut)


def tvarsnitt_y(m: Montage) -> tuple[Tvarsnitt, ...]:
    """Montagets prismor med axeln längs y och rätblock (takbalkar, takstolarnas delar): det exakta tvärsnittet i
    (x, z) och utbredningen i y. Lådorna i lagen omsluter de sneda delarna med marginal."""
    ut = []
    for vag, d, p in m.platta():
        f, namn = d.form, vag.rsplit("/", 1)[1]
        if isinstance(f, Ratblock):
            x0, y0, z0, x1, y1, z1 = i_foraldern(omslutande(f), p)          # type: ignore[arg-type]
            ut.append((namn, box(x0, z0, x1, z1), y0, y1))
        elif isinstance(f, Prisma) and abs(abs(p.R[1][2]) - 1.0) < 1e-9:
            y0, y1 = sorted(p.punkt((0.0, 0.0, z))[1] for z in (f.z0, f.z0 + f.tjocklek))
            ut.append((namn, Polygon([(x, z) for x, _, z in (p.punkt((u, v, f.z0)) for u, v in f.kontur)]), y0, y1))
    return tuple(ut)


@cache
def takets_stomme() -> tuple[Tvarsnitt, ...]:
    """Takbalkarna och takstolarna (med avväxlingar, kortlingar och upplagsreglar) som tvärsnitt."""
    return tvarsnitt_y(takbalkar.montage()) + tvarsnitt_y(T.montage())


@cache
def yttervaggar() -> tuple[Lage, ...]:
    """Ytterväggarnas delar."""
    return _per_element(_ytterv.montage())


@cache
def innervaggar() -> tuple[Lage, ...]:
    """De bärande innerväggarnas delar."""
    return _per_element(_innerv.montage())


@cache
def stolpar() -> tuple[Lage, ...]:
    """De fristående stolparnas delar."""
    return _per_element(_stolpar.montage())


@cache
def takstolar() -> tuple[Lage, ...]:
    """Takstolarnas delar."""
    return _per_element(T.montage())


def prefab() -> tuple[Lage, ...]:
    """Ytterväggarna, de bärande innerväggarna och stolparna."""
    return yttervaggar() + innervaggar() + stolpar()


def vagg(kod: str) -> tuple[Lage, ...]:
    """Väggens delar (ytter- eller innervägg)."""
    return tuple(d for d in yttervaggar() + innervaggar() if d.element == kod)


def stolpe(kod: str) -> tuple[Lage, ...]:
    return tuple(d for d in stolpar() if d.element == kod)


def takstol(kod: str) -> tuple[Lage, ...]:
    return tuple(d for d in takstolar() if d.element == kod)


# takets fack mellan takbalkarna, gavlarna och takstolarna (isoleringen och innertaket)
GAVELVAGGAR = {1: ("1NO", "1SV"), 2: ("2NO", "2SV"), 3: ("3NO", "3SV")}
TAKSTOLSVAGGAR = set(T.STOLAR) & set(S.INNERVAGGAR)       # innerväggar med takstol (mittstolen 2C)


def _med_takstol(kod: str) -> tuple[float, float]:
    """Väggens utbredning i y med takstolen som står på den (gavelstolen 2NO har sneda delar och mittstolen 2C
    toppklossar utanför väggens tjocklek)."""
    v = S.VAGGAR[kod]
    ys = [v.origo[1], v.origo[1] + v.w[1] * v.tjocklek]
    ys += [y for d in takstol(kod) for y in (d.lada[1], d.lada[4])]
    return min(ys), max(ys)


def under_takfallet(vagg: str, takfall: str) -> bool:
    """Om väggen står under takfallet: väggens utbredning i x når in mellan takfotsväggens insida och nocken (1A och 1D
    står bara under 1SO, 1C under både 1SO och 1NV)."""
    v, t = S.VAGGAR[vagg], S.TAKFALL[takfall]
    a, b = sorted((v.origo[0], v.origo[0] + v.u[0] * v.langd))
    c, d = sorted((t.x_insida, S.BALKAR[takbalkar.FALT[takfall].nock].x))
    return a < d - 1.0 and c + 1.0 < b


def _gavel_insida(kod: str) -> float:
    """Gavelns insida (y) mot takets fack: gavelväggens eller gavelstolens, den som når längst in."""
    y0, y1 = _med_takstol(kod)
    return y1 if S.YTTERVAGGAR[kod].w[1] > 0 else y0


def fack(kod: str) -> list[tuple[float, float]]:
    """Facken (y0, y1) mellan takbalkar och gavlarnas insida."""
    t = S.TAKFALL[kod]
    g0, g1 = GAVELVAGGAR[t.kropp]
    y_in0, y_in1 = _gavel_insida(g0), _gavel_insida(g1)
    kanter = [y_in0] + sorted(takbalkar.FALT[kod].y) + [y_in1]
    ut = []
    for a, b in zip(kanter, kanter[1:]):
        y0 = a if a == y_in0 else a + 45.0
        if b - y0 > 30:
            ut.append((y0, b))
    # facken delas där en bärande innervägg (med takstol) står, och vid dalbalkarnas ändar
    hinder = [_med_takstol(kod_v) for kod_v, v in S.INNERVAGGAR.items()
              if int(kod_v[0]) == t.kropp and abs(v.u[0]) > 0.5 and under_takfallet(kod_v, kod)]
    for y0, y1 in hinder:
        ut = [d for a, b in ut for d in ((a, min(b, y0)), (max(a, y1), b)) if d[1] - d[0] > 30]
    f = takbalkar.FALT[kod]
    if f.dal:
        for yd in (S.BALKAR[f.dal].y0, S.BALKAR[f.dal].y1):
            ut = [d for a, b in ut for d in (((a, yd), (yd, b)) if a < yd < b else ((a, b),)) if d[1] - d[0] > 30]
    return ut
