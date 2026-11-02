"""Takstolar i den bärande väggens system (u längs väggen, w genom väggen, z uppåt), K-03.

En takstol står på väggens överkant (sätet) under en nockbalk och följer takfallen på båda sidor om den
(skelett.TAKFALL: takbalkarnas överkant):

- ytterbalkar 45×95 (X) med överkanten i takplanet och diagonaler 45×220 (D) under dem. Vid takfoten går ytterbalken
  ut till takbalkarnas ände och diagonalen till där dess överkant ligger TAKLYFT över sätet, båda med lodräta ändar;
  mot en dalbalk slutar båda vid balkens sida. I nocken slutar ytterbalkarna vid nockbalkens sida och diagonalerna går
  till balkens mitt, kapade plant i balkens underkant, så att balken ligger tätt mellan ytterbalkarna;
- en underram (U) mellan diagonalernas fötter, med ändarna längs diagonalernas underkant;
- ståndare 45×95 (R) c/c 600 från nocken, en mitt under balken och två på var sida, hakade runt underramen.
  Diagonalerna har ett vågrätt säte, halva ståndarens bredd, på varje ståndare: på mittståndaren i diagonalernas
  skärning, annars i ståndarens mitt;
- toppklossar 45 mm (K), lika höga som diagonalerna och 600 mm långa, på sidan av toppen: gavelstolarna har en kloss
  på insidan (utsidan är fasad) och mittstolen 2C en på den nordöstra sidan, inne i väggens tjocklek (på den
  sydvästra skulle den gå ut genom väggens gips);
- spikplåtar 2,0 mm (K-03, P) utanpå: vid fötterna 600×100 mitt på underramen och i toppen 400×100 under balken. På
  klossens sida ersätts toppens plåt av klossen, och plåtar som skulle ligga i en annan del utgår.

Stolens egna data (underramens höjd, ståndarnas lägen, spikplåtarna vid fötterna) står i stolens fil.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from shapely.geometry import Polygon, box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

from modellering import Montage

from .. import skelett as S
from ..material import SPIKPLAT
from .regelvagg import Plan

T = 45.0                     # delarnas tjocklek (w)
YTTERBALK_H = 95.0           # ytterbalkens höjd, vinkelrätt mot takplanet
DIAGONAL_H = 220.0
STANDARE_B = 45.0
STANDARE_D = 95.0            # ståndarens djup (w) från stolens sida: genom väggens tjocklek
STANDARE_CC = 600.0
STANDARE_ANTAL = 2           # ståndare på var sida om mittståndaren
SPIKREGEL_B = 95.0
KLOSS_T = 45.0
KLOSS_L = 600.0
SPIKPLAT_T = 2.0
FOTPLAT = (600.0, 100.0)
TOPPLAT = (400.0, 100.0)

Linje = Callable[[float], float]


def _dar(f: Linje, z: float) -> float:
    """Var den räta linjen f har höjden z."""
    a, b = f(0.0), f(1000.0)
    return 1000.0 * (z - a) / (b - a)


def _hornen(p: Polygon) -> list[tuple[float, float]]:
    """Polygonens hörn moturs från det lägsta (u, z), utan hörn mitt på en rak kant."""
    q = list(orient(p).exterior.coords)[:-1]
    ut = []
    for i, (u, z) in enumerate(q):
        (ua, za), (ub, zb) = q[i - 1], q[(i + 1) % len(q)]
        if abs((u - ua) * (zb - z) - (z - za) * (ub - u)) > 1e-6 * max(1.0, abs(ub - ua) + abs(zb - za)):
            ut.append((float(u), float(z)))
    i0 = min(range(len(ut)), key=lambda i: (round(ut[i][0], 6), round(ut[i][1], 6)))
    return ut[i0:] + ut[:i0]


def _remsa(ok: Linje, h: float, u0: float, u1: float) -> Polygon:
    """Virke med överkanten ok och höjden h vinkelrätt mot takplanet, mellan u0 och u1 (lodräta ändar)."""
    a, b = sorted((u0, u1))
    d = h / S.COS
    return Polygon([(a, ok(a) - d), (b, ok(b) - d), (b, ok(b)), (a, ok(a))])


@dataclass(frozen=True)
class _Sida:
    """Stolens ena sida: s = −1 (u mindre än nocken) eller +1, med takfallet där (väggen längs x från x0)."""
    s: int
    takfall: S.Takfall
    x0: float
    ux: float
    ande: float              # takbalkarnas ände vid takfoten, eller dalbalkens sida (u)
    dal: bool

    def tak(self, u: float) -> float:
        """Takbalkarnas överkant."""
        return self.takfall.z_overkant(self.x0 + self.ux * u)

    def underkant(self, u: float) -> float:
        """Takbalkarnas underkant."""
        return self.takfall.z_underkant(self.x0 + self.ux * u)

    def diagonal_ok(self, u: float) -> float:
        return self.tak(u) - YTTERBALK_H / S.COS

    def diagonal_uk(self, u: float) -> float:
        return self.tak(u) - (YTTERBALK_H + DIAGONAL_H) / S.COS

    def fot(self, ok: Linje, sate: float) -> float:
        """Ändens läge för en del med överkanten ok: vid dalbalkens sida, eller vid takfoten där överkanten ligger
        TAKLYFT över sätet."""
        return self.ande if self.dal else _dar(ok, sate + S.TAKLYFT)


def _sidor(kod: str, balk: str) -> tuple[_Sida, _Sida]:
    v = S.VAGGAR[kod]
    x0, ux = v.origo[0], v.u[0]                        # gavlarna går längs x
    b = S.BALKAR[balk]
    uc = (b.x - x0) * ux
    kropp = next(k.nr for k in S.HUSKROPPAR.values() if abs(k.nock - b.x) < 1)
    y = v.origo[1] + v.w[1] * v.tjocklek / 2           # stolens plan
    ut = []
    for s in (-1, 1):
        t = next(t for t in S.TAKFALL.values() if t.kropp == kropp and t.riktning * ux * s < 0)
        dalar = [(d.x - x0) * ux for d in S.BALKAR.values()
                 if d.typ == "dal" and d.y0 - 1.0 <= y <= d.y1 + 1.0 and ((d.x - x0) * ux - uc) * s > 0]
        ande = (min(dalar, key=lambda u: abs(u - uc)) - s * S.BALK_B / 2) if dalar else (t.x_takfot - x0) * ux
        ut.append(_Sida(s, t, x0, ux, ande, bool(dalar)))
    return ut[0], ut[1]


@dataclass
class Takstol(Plan):
    """En takstol. `balk` är nockbalken som vilar på toppen, `utsida` anger om w0 är fasad."""
    balk: str = "NB5"
    utsida: bool = True
    klossar: tuple[int, ...] = ()        # sidorna med toppkloss: −1 vid w0, +1 vid w1 (standard: insidan, eller båda)
    sate: float = S.H_VAGG
    w0: float = 0.0
    underram: float = 120.0
    topplat_spel: float = 8.0
    diagonaler: list[tuple[list[tuple[float, float]], float, float]] = field(default_factory=list)
    ovriga: list[tuple[Polygon, float, float]] = field(default_factory=list)
    plattor: list[tuple[float, float, float, float, float, bool]] = field(default_factory=list)

    @property
    def uc(self) -> float:
        """Nockbalkens mitt i väggens u."""
        v = S.VAGGAR[self.kod]
        return (S.BALKAR[self.balk].x - v.origo[0]) * v.u[0]

    def _sida(self, sida: int) -> tuple[float, bool]:
        """Ytan (w) och om plåten sitter utanpå åt −w."""
        return (self.w0, True) if sida < 0 else (self.w0 + T, False)

    def spikplat(self, u0: float, u1: float, z0: float, z1: float, w: float, utanpa_minus: bool) -> Takstol:
        """Spikplåt på ytan w (utanpå åt −w eller +w)."""
        self.plattor.append((u0, u1, z0, z1, w, utanpa_minus))
        return self

    def fotplat(self, u0: float, sida: int) -> Takstol:
        """Spikplåten vid en fot, från u0 längs stolen, mitt på underramen, på sidan −1 (w0) eller +1."""
        zm = self.sate + self.underram / 2
        return self.spikplat(u0, u0 + FOTPLAT[0], zm - FOTPLAT[1] / 2, zm + FOTPLAT[1] / 2, *self._sida(sida))

    def _del(self, p: Polygon, w0: float, w1: float, typ: str) -> None:
        self.ovriga.append((p, w0, w1))
        self.profil(_hornen(p), w0, w1, typ=typ)

    def montage(self) -> Montage:
        uk = S.BALKAR[self.balk].uk
        # toppklossar: diagonalernas profil inom ±300 mm från toppen
        topp = unary_union([Polygon(p) for p, _, _ in self.diagonaler])
        topp_u = [x for x, z in topp.exterior.coords if abs(z - uk) < 1e-6]
        uc = 0.5 * (min(topp_u) + max(topp_u))
        kloss = topp.intersection(box(uc - KLOSS_L / 2, -1e5, uc + KLOSS_L / 2, 1e5))
        w0 = min(a for _, a, _ in self.diagonaler)
        w1 = max(b for _, _, b in self.diagonaler)
        sidor = [(w0 - KLOSS_T, w0) if s < 0 else (w1, w1 + KLOSS_T)
                 for s in (self.klossar or ((1,) if self.utsida else (-1, 1)))]
        for a, b in sidor:
            k = kloss
            for poly, p0, p1 in self.ovriga:                # andra delar på klossens sida
                if min(b, p1) - max(a, p0) > 1e-6:
                    k = k.difference(poly)
            if k.geom_type != "Polygon":
                k = max(getattr(k, "geoms", [k]), key=lambda g: g.area)
            if k.geom_type == "Polygon" and k.area > 1000:
                self.profil(_hornen(k), a, b, typ="K")
        # spikplåtar: 2 mm utanpå; i toppen på båda sidor utom där klossarna sitter
        klossytor = {round(a if a >= w1 else b, 6) for a, b in sidor}
        z1 = uk - self.topplat_spel
        topplatar = [(self.uc - TOPPLAT[0] / 2, self.uc + TOPPLAT[0] / 2, z1 - TOPPLAT[1], z1, *self._sida(s))
                     for s in (-1, 1)]
        for u0, u1, z0, z1, w, minus in self.plattor + topplatar:
            if round(w, 6) in klossytor and z1 > uk - 150:
                continue
            ws = (w - SPIKPLAT_T, w) if minus else (w, w + SPIKPLAT_T)
            r = box(u0, z0, u1, z1)
            if any(min(ws[1], p1) - max(ws[0], p0) > 1e-6 and r.intersection(poly).area > 1e-3
                   for poly, p0, p1 in self.ovriga):
                continue                                    # plåten skulle ligga i en annan del
            self.lada("P", u0, u1, ws[0], ws[1], z0, z1, "u", SPIKPLAT)
        return super().montage()


def takstol(kod: str, balk: str, utsida: bool = True, klossar: tuple[int, ...] = (), sate: float = S.H_VAGG,
            w0: float = 0.0, underram: float = 120.0, hak: float = 0.0, standare: Sequence[float] | None = None,
            standardelar: bool = True, spikregel: float | None = None, topplat_spel: float = 8.0) -> Takstol:
    """Takstolen på väggen kod under nockbalken balk, enligt reglerna ovan. sate: väggens överkant; w0: stolens sida;
    underram: underramens höjd; hak: ståndarnas hak i underramen; standare: ståndarnas lägen (u, standard c/c 600 från
    nocken), utan delar om standardelar är falskt (bara sätena och haken); spikregel: spikreglar 45×95 på stolens
    insida, med underkanten så mycket över takbalkarnas underkant; topplat_spel: toppens spikplåt under balken."""
    v = S.VAGGAR[kod]
    t = Takstol(kod, f"Takstol {kod}", v.tjocklek, beskrivning=f"Takstol på väggen {kod} under {balk}",
                balk=balk, utsida=utsida, klossar=klossar, sate=sate, w0=w0, underram=underram,
                topplat_spel=topplat_spel)
    uc, uk = t.uc, S.BALKAR[balk].uk
    sidor = _sidor(kod, balk)

    def under(u: float) -> float:
        """Diagonalernas underkant."""
        return (sidor[0] if u <= uc else sidor[1]).diagonal_uk(u)

    lagen = [uc - STANDARE_B / 2 + k * STANDARE_CC for k in range(-STANDARE_ANTAL, STANDARE_ANTAL + 1)] \
        if standare is None else list(standare)
    saten = [(a, under(uc) if a < uc < a + STANDARE_B else under(a + STANDARE_B / 2)) for a in lagen]
    ww = (w0, w0 + T)
    ovan = box(-1e5, sate, 1e5, 1e5)
    for sd in sidor:
        balksida = uc + sd.s * S.BALK_B / 2
        d = _remsa(sd.diagonal_ok, DIAGONAL_H, sd.fot(sd.diagonal_ok, sate), uc).intersection(box(-1e5, sate, 1e5, uk))
        for a, z in saten:
            d = d.difference(box(a, sate - 1.0, a + STANDARE_B, z))
        pts = _hornen(d)
        t.diagonaler.append((pts, *ww))
        t.profil(pts, *ww, typ="D")
        if spikregel is not None:
            def ok_s(u: float, sd: _Sida = sd) -> float:
                return sd.underkant(u) + spikregel + T / S.COS

            t._del(_remsa(ok_s, T, sd.fot(ok_s, sate), balksida).intersection(ovan), w0 + T, w0 + T + SPIKREGEL_B, "X")
        t._del(_remsa(sd.tak, YTTERBALK_H, sd.ande, balksida).intersection(ovan), *ww, "X")
    # underramen mellan diagonalernas fötter, med hak för ståndarna
    zu = sate + underram
    ua, ub = ([_dar(sd.diagonal_uk, z) for z in (sate, zu)] for sd in sidor)
    u = Polygon([(ua[0], sate), (ub[0], sate), (ub[1], zu), (ua[1], zu)])
    for a in lagen if hak > 0 else ():
        u = u.difference(box(a, zu - hak, a + STANDARE_B, zu + 1.0))
    t._del(u, *ww, "U")
    for a, z in saten if standardelar else ():
        t.tvarprofil([(w0, zu - hak), (w0 + T, zu - hak), (w0 + T, sate), (w0 + STANDARE_D, sate),
                      (w0 + STANDARE_D, z), (w0, z)], a, a + STANDARE_B)
    return t
