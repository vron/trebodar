"""Natursten med sågad baksida och kluven framsida: raka stenar och hörnstenar (L-formade) som polyedrar, med
framsidan som ett oregelbundet triangelnät.

Stenens system: x längs fasaden, y genom fasaden med baksidan i y = 0 och framsidan utåt (y < 0), z uppåt.
Tjockleken varierar mellan t_min och t_max, tunnast vid kanterna som på kluven sten. Slumpen styrs av ett frö per
sten, så att modellen blir densamma vid varje bygge.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from modellering import Polyeder, polyeder

V3 = tuple[float, float, float]


@dataclass(frozen=True)
class Klyvning:
    """Den kluvna framsidans form."""
    t_min: float = 30.0              # tunnaste stenen (vid kanterna)
    t_max: float = 50.0              # tjockaste stenen
    kant: float = 6.0                # kanternas tjocklek högst t_min + kant
    ruta: float = 120.0              # ungefärlig storlek på framsidans fasetter
    jitter: float = 0.3              # de inre hörnens förskjutning, andel av rutan


def _antal(langd: float, ruta: float) -> int:
    return max(2, round(langd / ruta))


def _rutnat(rng: random.Random, x0: float, x1: float, nx: int, H: float, nz: int,
            k: Klyvning) -> list[list[tuple[float, float, float]]]:
    """Framsidans hörn (x, z, t) i rader j (z) och kolumner i (x). Kanthörnen ligger kvar i kanternas plan."""
    dx, dz = (x1 - x0) / nx, H / nz
    paritet = rng.randrange(2)               # inre hörn växelvis höga och låga (tydliga fasetter)
    rader = []
    for j in range(nz + 1):
        rad = []
        for i in range(nx + 1):
            kant_x, kant_z = i in (0, nx), j in (0, nz)
            x = x0 + i * dx + (0.0 if kant_x else rng.uniform(-k.jitter, k.jitter) * dx)
            z = j * dz + (0.0 if kant_z else rng.uniform(-k.jitter, k.jitter) * dz)
            if kant_x and kant_z:
                t = k.t_min + rng.uniform(0.0, k.kant / 2)
            elif kant_x or kant_z:
                t = k.t_min + rng.uniform(0.0, k.kant)
            else:
                hog = (i + j + paritet) % 2 == 0
                t = k.t_min + (k.t_max - k.t_min) * (rng.uniform(0.6, 1.0) if hog else rng.uniform(0.2, 0.55))
            rad.append((x, z, t))
        rader.append(rad)
    return rader


def _trianglar(rng: random.Random, idx: list[list[int]]) -> list[tuple[int, ...]]:
    """Rutnätets rutor delade i två trianglar längs en slumpad diagonal."""
    ut: list[tuple[int, ...]] = []
    for j in range(len(idx) - 1):
        for i in range(len(idx[0]) - 1):
            a, b, c, d = idx[j][i], idx[j][i + 1], idx[j + 1][i + 1], idx[j + 1][i]
            ut += [(a, b, c), (a, c, d)] if rng.random() < 0.5 else [(a, b, d), (b, c, d)]
    return ut


class _Horn:
    """Hörnlista utan dubbletter."""

    def __init__(self) -> None:
        self.p: list[V3] = []
        self._i: dict[V3, int] = {}

    def __call__(self, x: float, y: float, z: float) -> int:
        q = (round(x, 6), round(y, 6), round(z, 6))
        if q not in self._i:
            self._i[q] = len(self.p)
            self.p.append(q)
        return self._i[q]


def kluven_sten(L: float, H: float, fro: str, k: Klyvning = Klyvning()) -> Polyeder:
    """Rak sten L × H: baksidan i y = 0, x 0–L, z 0–H, framsidan kluven."""
    rng = random.Random(fro)
    g = _rutnat(rng, 0.0, L, _antal(L, k.ruta), H, _antal(H, k.ruta), k)
    h = _Horn()
    f = [[h(x, -t, z) for x, z, t in rad] for rad in g]
    b00, bL0, bLH, b0H = h(0, 0, 0), h(L, 0, 0), h(L, 0, H), h(0, 0, H)
    ytor = [(b00, b0H, bLH, bL0),
            (b00, bL0, *[f[0][i] for i in reversed(range(len(f[0])))]),
            (b0H, *f[-1], bLH),
            (b00, *[rad[0] for rad in f], b0H),
            (bL0, bLH, *[rad[-1] for rad in reversed(f)])]
    return polyeder(h.p, ytor + _trianglar(rng, f))


def hornsten(ben_a: float, ben_b: float, H: float, fro: str, k: Klyvning = Klyvning()) -> Polyeder:
    """Hörnsten i ett utvändigt hörn, med origo i baksidornas skärning. Skänkeln A ligger längs fasaden A (baksidan
    y = 0, x −ben_a … 0, framsidan y < 0), skänkeln B längs fasaden B (baksidan x = 0, y 0 … ben_b, framsidan
    x > 0). Hörnet mellan framsidorna är en gemensam kant."""
    rng = random.Random(fro)
    nz = _antal(H, k.ruta)
    # hörnkanten: tjockleken mot A och mot B i varje rad
    zs = [j * H / nz + (0.0 if j in (0, nz) else rng.uniform(-k.jitter, k.jitter) * H / nz) for j in range(nz + 1)]
    kant = [(k.t_min + rng.uniform(0.0, k.kant), k.t_min + rng.uniform(0.0, k.kant)) for _ in zs]
    ga = _rutnat(rng, -ben_a, 0.0, _antal(ben_a + k.t_max, k.ruta), H, nz, k)
    gb = _rutnat(rng, 0.0, ben_b, _antal(ben_b + k.t_max, k.ruta), H, nz, k)
    h = _Horn()
    # framsidan A: y = −t(x, z); sista kolumnen är hörnkanten (x = tB). Framsidan B: x = t(y, z); första kolumnen
    # är hörnkanten (y = −tA). Rutnätens z i hörnkolumnen ersätts med hörnkantens.
    fa = [[h(x, -t, z) for x, z, t in rad[:-1]] + [h(kant[j][1], -kant[j][0], zs[j])] for j, rad in enumerate(ga)]
    fb = [[h(kant[j][1], -kant[j][0], zs[j])] + [h(t, y, z) for y, z, t in rad[1:]] for j, rad in enumerate(gb)]
    a0, a1 = h(-ben_a, 0, 0), h(-ben_a, 0, H)
    o0, o1 = h(0, 0, 0), h(0, 0, H)
    b0, b1 = h(0, ben_b, 0), h(0, ben_b, H)
    ytor = [(a0, o0, o1, a1), (o0, b0, b1, o1),
            (a0, a1, *[rad[0] for rad in reversed(fa)]),
            (b0, *[rad[-1] for rad in fb], b1),
            (a0, *fa[0], *fb[0][1:], b0, o0),
            (a1, *fa[-1], *fb[-1][1:], b1, o1)]
    return polyeder(h.p, ytor + _trianglar(rng, fa) + _trianglar(rng, fb))
