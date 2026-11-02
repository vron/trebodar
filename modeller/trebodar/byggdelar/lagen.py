"""Stommens delar och deras lägen i huset, ur montagen: för skikt och delar som ska gå runt eller ansluta mot
stommen (isoleringen, de invändiga skikten, ströläkten), så att de följer med när stommen ändras i stället för att
ha egna siffror.

Lägena är omslutande lådor (x0, y0, z0, x1, y1, z1) i husets koordinater (prefabstommens montage placeras utan
förflyttning i huset), för takets stomme exakta tvärsnitt i (x, z). Montagen byggs en gång per körning.
"""
from __future__ import annotations

from functools import cache

from shapely.geometry import Polygon, box

from modellering import Lada as Ratblock
from modellering import Montage, Prisma, i_foraldern, omslutande

Lada = tuple[float, float, float, float, float, float]
Lage = tuple[str, str, Lada]             # (grupp, delens namn, låda), t.ex. ("Innerväggar/Vägg 1B", "1B-R01", …)
Tvarsnitt = tuple[str, Polygon, float, float]       # (delens namn, tvärsnittet i (x, z), y0, y1)


def lagen(m: Montage) -> tuple[Lage, ...]:
    """Montagets delar med grupp, namn och omslutande låda i montagets system."""
    ut = []
    for vag, d, p in m.platta():
        b = omslutande(d.form)
        if b is not None:
            grupp, namn = vag.rsplit("/", 1)
            ut.append((grupp, namn, i_foraldern(b, p)))
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
    from trebodar.hus.stomme.prefab.takbalkar import takbalkar
    from trebodar.hus.stomme.prefab.takstolar import takstolar as T
    return tvarsnitt_y(takbalkar.montage()) + tvarsnitt_y(T.montage())


@cache
def prefab() -> tuple[Lage, ...]:
    """Ytterväggarna, de bärande innerväggarna och stolparna."""
    from trebodar.hus.stomme.prefab.innervaggar import innervaggar
    from trebodar.hus.stomme.prefab.stolpar import stolpar
    from trebodar.hus.stomme.prefab.yttervaggar import yttervaggar
    return tuple(x for m in (yttervaggar.montage(), innervaggar.montage(), stolpar.montage()) for x in lagen(m))


@cache
def takstolar() -> tuple[Lage, ...]:
    """Takstolarnas delar, grupperna "Takstolar/Takstol <kod>"."""
    from trebodar.hus.stomme.prefab.takstolar import takstolar as T
    return lagen(T.montage())
