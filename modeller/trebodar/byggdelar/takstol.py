"""Takstolar i den bärande väggens system (u längs väggen, w genom väggen, z uppåt), K-03.

Profilerna är takstolens delar som i Onshape-modellen. Reglerna här ger de ändringar som gäller alla takstolar:

- diagonalerna, ytterbalkarna ("extra", takets kant ovanpå diagonalen) och andra sneda delar under taket lyfts med
  takplanen (skelett.TAKLYFT); deras fötter förlängs ner till sätet (lodrätt i yttre änden, längs kanten i den inre);
- ståndarna förlängs upp till de lyfta diagonalerna;
- diagonalernas topp kapas plant i balkens underkant, och toppklossar 45 mm, lika höga som diagonalerna och 600 mm
  långa, skruvas på sidan av toppen: gavelstolarna har en kloss på insidan (utsidan är fasad) och mittstolen 2C en på
  den nordöstra sidan, inne i väggens tjocklek (på den sydvästra skulle den gå ut genom väggens gips);
- delarnas ändar mot nock- och dalbalkarna går fram till balkens sida, så att balken ligger tätt mellan dem
  (Onshape-modellens takstolar var gjorda för HEA 200, 200 bred med 3 mm spel, och slutade 8 mm från de 190 breda
  balkarna); underramens sneda ändar följer de lyfta diagonalerna;
- spikplåtarna är 2,0 mm (K-03) och sitter utanpå; plåtarna i toppen ersätts av klossarna på den sidan.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from modellering import Montage

from .. import skelett as S
from ..material import SPIKPLAT
from .regelvagg import Plan

KLOSS_T = 45.0
KLOSS_L = 600.0
SPIKPLAT_T = 2.0


def _lyft(pts: Sequence[Sequence[float]], d: float) -> list[tuple[float, float]]:
    """Profilen lyft d, med foten (den lägsta vågräta kanten, sätet) kvar på samma nivå: en lodrät ände förlängs,
    i yttre änden av en sned kant läggs en lodrät ände, och i den inre följer hörnet kanten ner till sätet."""
    P = [(float(u), float(z) + d) for u, z in pts]
    n = len(P)
    zmin = min(z for _, z in P)
    sate = next((i for i in range(n) if abs(P[i][1] - zmin) < 1e-6 and abs(P[(i + 1) % n][1] - zmin) < 1e-6
                 and abs(P[i][0] - P[(i + 1) % n][0]) > 1e-6), None)
    if sate is None:
        return P
    ia, ib = sate, (sate + 1) % n
    uc = sum(u for u, _ in P) / n
    yttre = ia if abs(P[ia][0] - uc) > abs(P[ib][0] - uc) else ib
    z0 = zmin - d
    ny: list[tuple[float, float]] = []
    for k in range(n):
        E = P[k]
        if k not in (ia, ib):
            ny.append(E)
            continue
        N = P[(k - 1) % n] if k == ia else P[(k + 1) % n]          # hörnets andra granne
        if abs(N[0] - E[0]) < 1e-6:
            ny.append((E[0], z0))                                    # lodrät ände: förläng
        elif k == yttre:
            under = (E[0], z0)                                       # sned yttre kant: lodrät ände
            ny += [E, under] if k == ia else [under, E]
        else:
            t = (z0 - E[1]) / (E[1] - N[1])
            ny.append((E[0] + (E[0] - N[0]) * t, z0))                # längs kanten ner till sätet
    return ny


@dataclass
class Takstol(Plan):
    """En takstol. `balk` är nock- eller dalbalken som vilar på toppen, `utsida` anger om w 0 är fasad."""
    balk: str = "NB5"
    utsida: bool = True
    klossar: tuple[int, ...] = ()        # sidorna med toppkloss: −1 vid w0, +1 vid w1 (standard: insidan, eller båda)
    diagonaler: list[tuple[list[tuple[float, float]], float, float]] = field(default_factory=list)
    ovriga: list[tuple[Polygon, float, float]] = field(default_factory=list)
    plattor: list[tuple[float, float, float, float, float, float, bool]] = field(default_factory=list)

    def _snappa(self, pts: Sequence[Sequence[float]]) -> list[tuple[float, float]]:
        """Hörn inom 0,01 mm från ett takplan läggs exakt i planet (Onshape-modellens tal har fyra decimaler)."""
        v = S.VAGGAR[self.kod]                         # takstolen heter som väggen den står på
        kropp = next(k.nr for k in S.HUSKROPPAR.values() if abs(k.nock - S.BALKAR[self.balk].x) < 1)
        plan = [t for t in S.TAKFALL.values() if t.kropp == kropp]
        ut = []
        for u, z in pts:
            x = v.origo[0] + v.u[0] * u
            for t in plan:
                for dz in (0.0, -95.0 / S.COS):            # takplanet och ytterbalkens (45×95) underkant
                    zp = t.z_overkant(x) + dz
                    if abs(z - zp) < 0.01:
                        z = zp
            ut.append((float(u), float(z)))
        return ut

    def _till_balkarna(self, pts: Sequence[Sequence[float]]) -> list[tuple[float, float]]:
        """Ändar som slutar strax utanför en nock- eller dalbalks sida förlängs längs delens kant till sidan."""
        v = S.VAGGAR[self.kod]
        y = v.origo[1] + v.w[1] * self.tjocklek / 2           # takstolens plan
        P = [(float(u), float(z)) for u, z in pts]
        n = len(P)
        ut = list(P)
        for b in S.BALKAR.values():
            if not b.y0 - 1.0 <= y <= b.y1 + 1.0:
                continue
            uc = (b.x - v.origo[0]) * v.u[0]
            for k, (u, z) in enumerate(P):
                d = abs(u - uc) - S.BALK_B / 2
                if not (0.5 < d < 12.0 and b.uk - 5.0 <= z <= b.ok + 120.0):     # även ovanför balken (taket)
                    continue
                grannar = (P[(k - 1) % n], P[(k + 1) % n])
                nu, nz = max(grannar, key=lambda q: abs(q[0] - u))
                if abs(nu - u) < 1e-6:
                    continue
                mal = uc + (S.BALK_B / 2 if u > uc else -S.BALK_B / 2)
                ut[k] = (mal, z + (z - nz) * (mal - u) / (u - nu))
        return ut

    def diagonal(self, pts: Sequence[Sequence[float]], w0: float, w1: float) -> Takstol:
        q = Polygon(self._till_balkarna(self._snappa(_lyft(pts, S.TAKLYFT))))
        uk = S.BALKAR[self.balk].uk
        q = q.difference(box(-1e5, uk, 1e5, 1e5))
        self.diagonaler.append(([(float(x), float(z)) for x, z in list(q.exterior.coords)[:-1]], w0, w1))
        self.profil(self.diagonaler[-1][0], w0, w1, typ="D")
        return self

    def sned(self, pts: Sequence[Sequence[float]], w0: float, w1: float, typ: str = "X") -> Takstol:
        """Sned del under taket (ytterbalk ovanpå diagonalen m.m.): lyfts med takplanet och kapas vid balken."""
        q = Polygon(self._till_balkarna(self._snappa(_lyft(pts, S.TAKLYFT))))
        uc, uk = self._balk_u(), S.BALKAR[self.balk].uk
        q = q.difference(box(uc - S.BALK_B / 2, uk, uc + S.BALK_B / 2, 1e5))
        if q.geom_type != "Polygon":
            q = max(q.geoms, key=lambda g: g.area)
        p = [(float(x), float(z)) for x, z in list(q.exterior.coords)[:-1]]
        self.ovriga.append((Polygon(p), w0, w1))
        self.profil(p, w0, w1, typ=typ)
        return self

    def _balk_u(self) -> float:
        """Balkens centrumlinje i väggens u (balkarna går längs y, gavelväggarna längs x)."""
        v = S.VAGGAR[self.kod]
        return (S.BALKAR[self.balk].x - v.origo[0]) * v.u[0]

    def underram(self, pts: Sequence[Sequence[float]], w0: float, w1: float) -> Takstol:
        """Underramen; sneda ändar mot diagonalerna flyttas upp TAKLYFT med dem: kantens ändpunkter glider längs de
        vågräta kanterna."""
        P = [(float(u), float(z)) for u, z in pts]
        n = len(P)
        p = list(P)
        for k in range(n):
            (ua, za), (ub, zb) = P[k], P[(k + 1) % n]
            if abs(ub - ua) > 1.0 and abs(zb - za) > 1.0:          # sned kant
                du = -S.TAKLYFT * (ub - ua) / (zb - za)
                for i in (k, (k + 1) % n):
                    p[i] = (p[i][0] + du, p[i][1])
        self.ovriga.append((Polygon(p), w0, w1))
        self.profil(p, w0, w1, typ="U")
        return self

    def stander(self, pts: Sequence[Sequence[float]], u0: float, u1: float) -> Takstol:
        """Stående del med profil (w, z), toppen förlängd upp till de lyfta diagonalerna."""
        zmax = max(z for _, z in pts)
        self.tvarprofil([(w, z + S.TAKLYFT if abs(z - zmax) < 1e-6 else z) for w, z in pts], u0, u1)
        return self

    def spikplat(self, u0: float, u1: float, z0: float, z1: float, w: float, utanpa_minus: bool) -> Takstol:
        """Spikplåt på ytan w (utanpå åt −w eller +w)."""
        self.plattor.append((u0, u1, z0, z1, w, 0.0, utanpa_minus))
        return self

    def montage(self) -> Montage:
        uk = S.BALKAR[self.balk].uk
        # toppklossar: diagonalernas profil inom ±300 mm från toppen
        topp = unary_union([Polygon(p) for p, _, _ in self.diagonaler])
        uc = topp.bounds[0] + 0.5 * (topp.bounds[2] - topp.bounds[0])
        topp_u = [x for x, z in topp.exterior.coords if abs(z - uk) < 1e-6]
        if topp_u:
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
                k = max(k.geoms, key=lambda g: g.area) if hasattr(k, "geoms") and k.geoms else k
            if k.geom_type == "Polygon" and k.area > 1000:
                self.profil([(float(x), float(z)) for x, z in list(k.exterior.coords)[:-1]], a, b, typ="K")
        # spikplåtar: 2 mm utanpå; toppens plåtar tas bort där klossarna sitter
        klossytor = {round(a if a >= w1 else b, 6) for a, b in sidor}
        for u0, u1, z0, z1, w, _, minus in self.plattor:
            if z1 > uk - 150 and round(w, 6) in klossytor:
                continue
            ws = (w - SPIKPLAT_T, w) if minus else (w, w + SPIKPLAT_T)
            r = box(u0, z0, u1, z1)
            if any(min(ws[1], p1) - max(ws[0], p0) > 1e-6 and r.intersection(poly).area > 1e-3
                   for poly, p0, p1 in self.ovriga):
                continue                                    # plåten skulle ligga i en annan del
            self.lada("P", u0, u1, ws[0], ws[1], z0, z1, "u", SPIKPLAT)
        return super().montage()


def takstol(kod: str, vagg: str, balk: str, utsida: bool, klossar: tuple[int, ...] = ()) -> Takstol:
    v = S.VAGGAR[vagg]
    return Takstol(kod, f"Takstol {kod}", v.tjocklek, beskrivning=f"Takstol på väggen {vagg} under {balk}",
                   balk=balk, utsida=utsida, klossar=klossar)
