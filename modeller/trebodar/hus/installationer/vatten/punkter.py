"""Tappvattnets beståndsdelar och hur rören dras.

- Tappställen (Tappstalle): det som förbrukar vatten, med typ (normflöden), anslutning (dosa), montering på en yta
  (montering.py: vagg, golv, kallarvagg) och rörtyp. Kallvattnet ansluter till höger och varmvattnet till vänster sett
  mot dosan.
- Fördelare (Fordelare): kallvattnets och varmvattnets stammar i fördelarskåpet, med numrerade utgångar längs stammen;
  utgång 0 och utgången efter den sista är stammens ändar (inlopp och genomgång).
- Rör (Ror): från en fördelares utgång ("FD-KV:3"), en utrustning i teknikrummet ("TK-VP:VV-ut") eller ett tappställe
  till ett annat, med media (KV, VV) och brytpunkter. Rör-i-rör från fördelaren till varje tappställe (stjärnsystem:
  läckor syns i fördelarskåpet).
- Stråk (Strak): gemensamma vägar ingjutna i mellanbjälklaget, mellan armeringsnäten, med en fil per tappställe:
  varmvattnet överst och kallvattnet under det, i samma läge i plan. Filen går genom fördelarnas utgång: stråket
  förskjutet i sidled så att dess första sträcka går genom utgången. Röret följer filen till punkten närmast
  tappstället och går därifrån dit (vag): upp ur bjälklaget i väggens regelfack eller golvdosan på plan 1, eller ned
  ur bjälklaget i källarväggens cellplast bakom gipsen till väggdosan i källaren.

Koordinater i mm (K-05), z från plan 1:s golv.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from shapely.geometry import LineString, Point
from shapely.ops import substring, unary_union

from trebodar.hus.armering.armering import mellanbjalklagets_hinder, mellanbjalklagets_mellanrum

from ..montering import Montering, Vek, flytt, i_vaggen
from .typer import Dosatyp, Fordelartyp, Rortyp, Tappstalletyp

R_ROR = 14.0                            # största skyddsrörets radie (rör-i-rör 18/28)
_UK, _OK = mellanbjalklagets_mellanrum()
Z_KV = _UK + 2.0 + R_ROR                # kallvattnet närmast underkantsnätet
Z_VV = _OK - 2.0 - R_ROR                # varmvattnet närmast överkantsnätet
NIVA = {"VV": Z_VV, "KV": Z_KV}
# järnen under överkantsnätet (vinkeljärnen vid ytterväggarna, diagonaljärnen vid trapphålet): där går varmvattnet i
# kallvattnets nivå, efter filen (där kallvattnet har vikit av åt sitt håll)
HINDER = unary_union([LineString([q[:2] for q in pl]).buffer(d / 2 + R_ROR + 3.0)
                      for pl, d in mellanbjalklagets_hinder()])


@dataclass(frozen=True)
class Rum:
    kod: str                    # två bokstäver, början på tappställenas id (t.ex. "BA")
    namn: str
    plan: int                   # 1 (plan 1) eller 0 (källaren)


@dataclass(frozen=True)
class Tappstalle:
    """Ett tappställe: dosans mitt på ytan (normalen ut i rummet), rörtypen från fördelarna, för golvdosor riktningen
    från varmvattnet till kallvattnet (standard x) och en punkt i plan som rören går förbi efter stråket (via; None
    i en koordinat: anslutningens)."""
    id: str
    typ: Tappstalletyp
    dosa: Dosatyp
    lage: Montering
    ror: Rortyp
    kallt: Vek | None = None
    via: tuple[float | None, float | None] | None = None


@dataclass(frozen=True)
class Fordelare:
    """Kallvattnets eller varmvattnets fördelare: utgång 1 i lage, följande utgångar längs riktning."""
    id: str
    typ: Fordelartyp
    media: str                  # "KV" eller "VV"
    lage: Vek
    riktning: Vek = (1.0, 0.0, 0.0)

    def utgang(self, n: int) -> Vek:
        """Utgång n (0 och typ.utgangar + 1: stammens ändar)."""
        return flytt(self.lage, self.riktning, (n - 1) * self.typ.delning)


@dataclass(frozen=True)
class Ror:
    """Rör från fran till till genom brytpunkterna via: fördelarens utgång ("FD-KV:3"), utrustning
    ("TK-VP:KV-in") eller tappställe ("BA-DU1")."""
    id: str
    typ: Rortyp
    media: str                  # "KV" eller "VV"
    fran: str
    till: str
    via: tuple[Vek, ...] = ()


@dataclass(frozen=True)
class Strak:
    """En gemensam väg under källarens tak (punkter i plan, från fördelarskåpet), med en fil per tappställe."""
    id: str
    punkter: tuple[tuple[float, float], ...]

    def fil(self, p: Vek) -> LineString:
        """Filen genom punkten p (fördelarens utgång): stråket förskjutet i sidled (åt vänster positivt) så att dess
        första sträcka går genom p."""
        (x0, y0), (x1, y1) = self.punkter[0], self.punkter[1]
        d = ((p[1] - y0) * (x1 - x0) - (p[0] - x0) * (y1 - y0)) / math.hypot(x1 - x0, y1 - y0)
        linje = LineString(self.punkter)
        return linje.offset_curve(d, join_style="mitre") if abs(d) > 1e-6 else linje


def anslutning(t: Tappstalle, media: str) -> Vek:
    """Rörets ände vid tappstället: dosans mitt bakom ytan (väggdosa) eller på ytan; kallvattnet till höger och
    varmvattnet till vänster sett mot dosan, cc isär."""
    m, d = t.lage, t.dosa
    n = m.normal
    hoger = (-n[1], n[0], 0.0) if d.slag != "golv" else (t.kallt or (1.0, 0.0, 0.0))
    p = flytt(m.punkt, n, -d.djup / 2 if d.slag == "vägg" else d.djup / 2)
    return flytt(p, hoger, (d.cc / 2) * (1 if media == "KV" else -1)) if d.cc else p


def vag(ut: Vek, media: str, strak: Strak, genom: tuple[tuple[float, float], ...],
        slut: tuple[Vek, ...] = ()) -> tuple[Vek, ...]:
    """Rörets väg från fördelarens utgång ut: rakt upp i mellanbjälklaget till rörets nivå (NIVA), längs filen genom
    utgången till punkten närmast den första punkten i genom, därifrån genom punkterna i plan och vidare genom slut
    (t.ex. upp eller ned i en vägg)."""
    z = NIVA[media]
    fil = strak.fil(ut)
    a = fil.project(Point(ut[0], ut[1]))
    del_ = substring(fil, a, max(a, fil.project(Point(genom[0]))))
    langs = list(del_.coords) if del_.geom_type == "LineString" else [(del_.x, del_.y)]
    pl: list[tuple[float, float]] = []
    avvik = 0
    for i, (x, y) in enumerate([(ut[0], ut[1]), *langs, *genom]):
        if not pl or math.hypot(x - pl[-1][0], y - pl[-1][1]) > 0.5:
            pl.append((float(x), float(y)))
        if i == len(langs):
            avvik = len(pl) - 1                         # där röret lämnar filen
    punkter: list[Vek] = [(x, y, z) for x, y in pl[:avvik + 1]]
    for p0, p1 in zip(pl[avvik:], pl[avvik + 1:]):
        s = LineString([p0, p1])
        if z != Z_KV and s.intersects(HINDER):         # varmvattnet ned i kallvattnets nivå vid järnen
            g = s.intersection(HINDER)
            e = s.interpolate(min(s.project(Point(c)) for q in getattr(g, "geoms", [g]) for c in q.coords))
            punkter += [(e.x, e.y, z), (e.x, e.y, Z_KV)]
            z = Z_KV
        punkter.append((p1[0], p1[1], z))
    return (*_unika(punkter), *slut)


def _unika(punkter: list[Vek]) -> list[Vek]:
    """Punkterna utan upprepningar i följd."""
    ut: list[Vek] = []
    for q in punkter:
        if not ut or math.dist(q, ut[-1]) > 0.5:
            ut.append(q)
    return ut


def till_tappstallet(t: Tappstalle, media: str) -> tuple[tuple[tuple[float, float], ...], tuple[Vek, ...]]:
    """Rörets väg från stråket till tappstället: punkterna i plan (via och punkten lodrätt under eller över
    anslutningen, för väggdosor inne i väggen) och därifrån upp eller ned i väggen till dosans höjd."""
    a = anslutning(t, media)
    slut: tuple[Vek, ...] = ()
    if t.dosa.slag == "vägg":
        i = i_vaggen(t.lage, a)
        a, slut = i, (i,)
    genom: tuple[tuple[float, float], ...] = ((a[0], a[1]),)
    if t.via:
        genom = ((a[0] if t.via[0] is None else t.via[0], a[1] if t.via[1] is None else t.via[1]), *genom)
    return genom, slut


def ror(t: Tappstalle, n: int, strak: Strak, fordelare: dict[str, Fordelare]) -> list[Ror]:
    """Rören till tappstället från utgång n på fördelarna (samma nummer på kallvattnets och varmvattnets), längs
    filen i stråket: varmt och kallt, det som tappstället har."""
    ut = []
    for media, flode in (("VV", t.typ.vv), ("KV", t.typ.kv)):
        if flode > 0:
            fd = fordelare[media]
            genom, slut = till_tappstallet(t, media)
            ut.append(Ror(f"{t.id}-{media}", t.ror, media, f"{fd.id}:{n}", t.id,
                          vag(fd.utgang(n), media, strak, genom, slut)))
    return ut
