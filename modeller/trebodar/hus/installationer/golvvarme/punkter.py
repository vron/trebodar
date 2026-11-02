"""Golvvärmens beståndsdelar och hur slingorna läggs.

- Zoner (Zon): de uppvärmda ytorna, en slinga per zon: en rektangel eller polygon som skärs med golvet (betongen
  utan väggarna, trapphålet och kaminen) med ett avstånd till väggarna, utan tilloppens stråk och det som ska hållas
  fritt (golvdosor). Rördelningen cc, radernas riktning och var slingan börjar (start, där tilloppen kommer).
- Slingor (slinga): dubbelslingor i meander, framledningen och returen bredvid varandra (cc isär), raderna 2·cc isär
  längs zonens riktning från hörnet närmast start; framledningen går ut till vändpunkten och returen tillbaka.
- Fördelare (Fordelare): framledningens och returens stammar, med utgångar i tilloppens filer (som tappvattnets), c/c
  50 som armeringsnätens maskor (s150): rören går upp eller ned i betongen mellan nätets järn.
- Tilloppen följer stråk (..strak.Strak) från fördelaren till zonerna, en fil per rör, och slingan med sina två
  tillopp är ett rör från framledningens utgång till returens. Tilloppen viker av vinkelrätt från stråket mot
  slingans början, så slingans rader går vinkelrätt mot stråkets sista sträcka (eller längs den, när stråket slutar
  vid zonen).
- Järnen som går genom rörens nivå (källarväggarnas lodräta järn i mellanbjälklaget, balkarnas järn i bottenplattan)
  är hinder: slingorna håller sig JARN från dem, och stråken går över väggarna i dörröppningarna eller mellan järnen.

Koordinater i mm (K-05), z från plan 1:s golv.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from shapely.geometry import LineString, Polygon, box

from ..montering import Vek, flytt
from .typer import Fordelartyp

FIL = 50.0                              # tilloppens avstånd i stråken och fördelarnas utgångar (c/c)
MARGINAL = 150.0                        # slingornas avstånd till väggar och kanter
FRITT = 150.0                           # avstånd till golvdosor och rör genom betongen
JARN = 150.0                            # slingornas avstånd till järnen som går genom rörens nivå

P2 = tuple[float, float]


@dataclass(frozen=True)
class Zon:
    """En uppvärmd yta med en slinga: rektangeln (x0, y0, x1, y1) eller polygonen yta, utan polygonerna i utom."""
    id: str
    namn: str
    yta: tuple[float, float, float, float] | tuple[P2, ...]
    cc: float
    riktning: str               # raderna längs "x" eller "y"
    start: P2                   # slingan börjar i hörnet närmast, där tilloppen kommer
    strak: str
    utom: tuple[tuple[P2, ...], ...] = ()

    def polygon(self) -> Polygon:
        y = self.yta
        p = box(*y) if len(y) == 4 and not isinstance(y[0], tuple) else Polygon(y)  # type: ignore[arg-type]
        for u in self.utom:
            p = p.difference(Polygon(u))
        return p


@dataclass(frozen=True)
class Fordelare:
    """Framledningens eller returens stam längs riktning: utgångarna i filerna `filer` (filen 0 i lage, c/c FIL),
    utgång n i filen filer[n − 1]; ändarna en fil före den första och efter den sista."""
    id: str
    typ: Fordelartyp
    media: str                  # "fram" eller "retur"
    lage: Vek
    riktning: Vek
    filer: tuple[int, ...]

    @property
    def utgangar(self) -> int:
        return len(self.filer)

    def utgang(self, n: int) -> Vek:
        fil = -1 if n == 0 else max(self.filer) + 1 if n == self.utgangar + 1 else self.filer[n - 1]
        return flytt(self.lage, self.riktning, fil * FIL)


def slinga(yta: Polygon, cc: float, riktning: str, start: P2) -> tuple[list[P2], list[P2]] | None:
    """Dubbelslingan i ytan (se modulen): framledningen från början till vändpunkten och returen från vändpunkten
    tillbaka, i plan; None om ytan är för liten."""
    inre = yta.buffer(-cc / 2, join_style="mitre")
    if inre.is_empty:
        return None
    inre = max(getattr(inre, "geoms", [inre]), key=lambda g: g.area)

    def xy(u: float, v: float) -> P2:
        return (u, v) if riktning == "y" else (v, u)

    def uv(p: P2) -> P2:
        return (p[0], p[1]) if riktning == "y" else (p[1], p[0])

    b = inre.bounds
    u0, u1 = (b[0], b[2]) if riktning == "y" else (b[1], b[3])
    su, sv = uv(start)
    steg = 2 * cc if abs(su - u0) <= abs(su - u1) else -2 * cc
    u = u0 + 1.0 if steg > 0 else u1 - 1.0
    rader: list[tuple[float, float, float]] = []                 # (u, v_a, v_b)
    while (u <= u1 - 1.0 + 1e-6) if steg > 0 else (u >= u0 + 1.0 - 1e-6):
        lo, hi = (b[1] - 10, b[3] + 10) if riktning == "y" else (b[0] - 10, b[2] + 10)
        s = LineString([xy(u, lo), xy(u, hi)]).intersection(inre)
        delar = [g for g in getattr(s, "geoms", [s]) if g.geom_type == "LineString" and g.length > 1.0]
        if not delar:
            break
        g = max(delar, key=lambda g: g.length)
        va, vb = sorted(uv(c)[1] for c in g.coords)
        rader.append((u, va, vb))
        u += steg
    if not rader:
        return None
    hog = abs(sv - rader[0][2]) < abs(sv - rader[0][1])        # första raden börjar i den höga änden
    mitt: list[P2] = []
    for i, (u, va, vb) in enumerate(rader):
        borjan_hog = hog if i % 2 == 0 else not hog
        a, e = (vb, va) if borjan_hog else (va, vb)
        if i + 1 < len(rader):                                  # vänd vid den gemensamma änden
            n = rader[i + 1]
            e = min(e, n[2]) if not borjan_hog else max(e, n[1])
        if i > 0:
            a = mitt[-1][1] if riktning == "y" else mitt[-1][0]
        mitt += [xy(u, a), xy(u, e)]
    linje = LineString(mitt)
    fram = list(linje.offset_curve(cc / 2, join_style="mitre").coords)
    retur = list(linje.offset_curve(-cc / 2, join_style="mitre").coords)
    return fram, list(reversed(retur))


def langd(vag: Sequence[tuple[float, ...]]) -> float:
    return sum(((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2 + ((b[2] - a[2]) if len(a) > 2 else 0.0) ** 2) ** 0.5
               for a, b in zip(vag, vag[1:]))
