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

from trebodar import skelett as S
from trebodar.hus.stomme.prefab.innervaggar import innervaggar
from trebodar.hus.stomme.prefab.stolpar import stolpar
from trebodar.hus.stomme.prefab.takbalkar import takbalkar
from trebodar.hus.stomme.prefab.takstolar import takstolar as T
from trebodar.hus.stomme.prefab.yttervaggar import yttervaggar

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
    return tvarsnitt_y(takbalkar.montage()) + tvarsnitt_y(T.montage())


@cache
def prefab() -> tuple[Lage, ...]:
    """Ytterväggarna, de bärande innerväggarna och stolparna."""
    return tuple(x for m in (yttervaggar.montage(), innervaggar.montage(), stolpar.montage()) for x in lagen(m))


@cache
def takstolar() -> tuple[Lage, ...]:
    """Takstolarnas delar, grupperna "Takstolar/Takstol <kod>"."""
    return lagen(T.montage())


# takets fack mellan takbalkarna, gavlarna och takstolarna (isoleringen och innertaket)
GAVELVAGGAR = {1: ("1NO", "1SV"), 2: ("2NO", "2SV"), 3: ("3NO", "3SV")}
TAKSTOLSVAGGAR = set(T.STOLAR) & set(S.INNERVAGGAR)       # innerväggar med takstol (mittstolen 2C)


def _med_takstol(kod: str) -> tuple[float, float]:
    """Väggens utbredning i y med takstolen som står på den (gavelstolen 2NO har sneda delar och mittstolen 2C
    toppklossar utanför väggens tjocklek)."""
    v = S.VAGGAR[kod]
    ys = [v.origo[1], v.origo[1] + v.w[1] * v.tjocklek]
    ys += [y for g, _, (_, y0, _, _, y1, _) in takstolar() if g.endswith(f"/Takstol {kod}") for y in (y0, y1)]
    return min(ys), max(ys)


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
              if int(kod_v[0]) == t.kropp and abs(v.u[0]) > 0.5]
    for y0, y1 in hinder:
        ut = [d for a, b in ut for d in ((a, min(b, y0)), (max(a, y1), b)) if d[1] - d[0] > 30]
    f = takbalkar.FALT[kod]
    if f.dal:
        for yd in (S.BALKAR[f.dal].y0, S.BALKAR[f.dal].y1):
            ut = [d for a, b in ut for d in (((a, yd), (yd, b)) if a < yd < b else ((a, b),)) if d[1] - d[0] > 30]
    return ut
