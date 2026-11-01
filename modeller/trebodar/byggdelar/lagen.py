"""Stommens delar och deras lägen i huset, ur montagen: för skikt och delar som ska gå runt eller ansluta mot
stommen (isoleringen, de invändiga skikten, ströläkten), så att de följer med när stommen ändras i stället för att
ha egna siffror.

Lägena är omslutande lådor (x0, y0, z0, x1, y1, z1) i husets koordinater (prefabstommens montage placeras utan
förflyttning i huset). Montagen byggs en gång per körning.
"""
from __future__ import annotations

from functools import cache

from modellering import Montage, i_foraldern, omslutande

Lada = tuple[float, float, float, float, float, float]
Lage = tuple[str, str, Lada]             # (grupp, delens namn, låda), t.ex. ("Innerväggar/Vägg 1B", "1B-R01", …)


def lagen(m: Montage) -> tuple[Lage, ...]:
    """Montagets delar med grupp, namn och omslutande låda i montagets system."""
    ut = []
    for vag, d, p in m.platta():
        b = omslutande(d.form)
        if b is not None:
            grupp, namn = vag.rsplit("/", 1)
            ut.append((grupp, namn, i_foraldern(b, p)))
    return tuple(ut)


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
