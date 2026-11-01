"""Fasadstenen på källarväggarna (AR-01): beklädnadsgranit Bohus Grå i skift med slumpade längder och hörnstenar i
de utvändiga hörnen, en grupp per vägg.

Stenen har sågad baksida 15 mm utanför cellplasten (armeringsbruk och fästmassa) och kluven framsida, 30–50 mm
tjock. Skiften är 400 mm höga med fog 10 (det översta kapat till beklädnadens överkant), stenarna 600–1 200 långa i
steg om 100, med lodfogarna minst 150 från fogarna i skiftet under. Hörnstenarna har skänklarna 400 och 200 i
varannat skift. Fogbruket fyller fogarna 25 mm från stenens baksida. Stenens mått läses ur AR-01:s indata;
beklädnadens utbredning är densamma som i Onshape-modellen. Mönstret slumpas med ett frö per vägg, så att
modellen blir densamma vid varje bygge.

Väggarnas system: u längs väggen, w inåt med cellplastens yta i w = 0, z uppåt (skelett.Vaggdef).
"""
from __future__ import annotations

import random
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from shapely.geometry import box
from shapely.ops import unary_union

from modellering import Del, Montage, Placering

from trebodar import skelett as S
from trebodar.byggdelar import polygon as P
from trebodar.byggdelar.regelvagg import Plan
from trebodar.byggdelar.sten import Klyvning, hornsten, kluven_sten
from trebodar.byggdelar.virke import fmt
from trebodar.material import ARMERINGSBRUK, FOGBRUK, GRANIT

ROT = Path(__file__).resolve().parents[4]
AR01 = ROT / "beräkningar" / "AR-01"
FOGDJUP = 25.0               # fogbrukets djup från stenens baksida (stenen är minst 30 tjock)
FORSKJUTNING = 150.0         # minsta avstånd mellan lodfogar i skift som ligger på varandra
KORTAST = 300.0              # kortaste kapade sten


def indata() -> dict[str, Any]:
    return tomllib.loads((AR01 / "indata.toml").read_text(encoding="utf-8"))


@dataclass(frozen=True)
class Bekladnad:
    """Sammanhängande beklädnad runt utvändiga hörn: väggarna i ordning (u växande, hörnen mellan dem) och de fria
    ändarna i husets (x, y)."""
    vaggar: tuple[str, ...]
    start: tuple[float, float]
    slut: tuple[float, float]
    z0: float
    z1: float


BEKLADNAD = (Bekladnad(("3NO", "3NV", "3SV"), (9470.0, 970.0), (9470.0, 12540.0), -2150.0, -S.H_BJALKLAG),
             Bekladnad(("1SO",), (-30.0, 8060.0), (-30.0, 3560.0), -1540.0, -740.0))


@dataclass(frozen=True)
class _Matt:
    H: float                 # skifthöjd
    fog: float
    L: tuple[float, float]   # stenarnas längd
    ben: tuple[float, float]    # hörnstenarnas skänklar
    bak: float               # baksidan utanför cellplasten
    klyv: Klyvning


def _matt() -> _Matt:
    d = indata()
    st, sk = d["sten"], d["skikt"]
    return _Matt(st["hojd"], st["fog"], tuple(st["langd"]), tuple(st["horn"]), sk["armeringsbruk"] + sk["fastmassa"],
                 Klyvning(sk["sten_min"], sk["sten_max"]))


def _u(kod: str, p: tuple[float, float]) -> float:
    v = S.YTTERVAGGAR[kod]
    return (p[0] - v.origo[0]) * v.u[0] + (p[1] - v.origo[1]) * v.u[1]


def _horn(a: str, b: str, bak: float) -> tuple[float, float]:
    """Baksidornas skärning i hörnet mellan väggarna a och b, som u i a och i b."""
    va, vb = S.YTTERVAGGAR[a], S.YTTERVAGGAR[b]
    # baksidan i a: (p − origo_a)·w_a = −bak; i b likadant. Hörnet ligger på a:s baksida vid u där b:s baksida går.
    pa = (va.origo[0] - va.w[0] * bak, va.origo[1] - va.w[1] * bak)
    pb = (vb.origo[0] - vb.w[0] * bak, vb.origo[1] - vb.w[1] * bak)
    # a:s baksida: pa + s·u_a; skär b:s baksida (p − pb)·w_b = 0
    s = ((pb[0] - pa[0]) * vb.w[0] + (pb[1] - pa[1]) * vb.w[1]) / (va.u[0] * vb.w[0] + va.u[1] * vb.w[1])
    p = (pa[0] + s * va.u[0], pa[1] + s * va.u[1])
    return _u(a, p), _u(b, p)


def _fyll(a: float, b: float, rng: random.Random, under: list[float], M: _Matt) -> list[tuple[float, float]]:
    """Stenar (u0, u1) från a till b med fog emellan: slumpade längder i steg om 100, den sista kapad, lodfogarna
    förskjutna från fogarna i skiftet under."""
    langder = [float(v) for v in range(int(M.L[0]), int(M.L[1]) + 1, 100)]
    ut: list[tuple[float, float]] = []
    u = a
    while b - u > M.L[1]:
        rest = b - u
        # resten efter stenen ska rymma en kapad sten
        kand = [L for L in langder if rest - L - M.fog >= KORTAST]
        rng.shuffle(kand)
        fria = [L for L in kand if all(abs(u + L + M.fog / 2 - j) >= FORSKJUTNING for j in under)]
        L = (fria or kand)[0]
        ut.append((u, u + L))
        u += L + M.fog
    if b - u > 1.0:
        ut.append((u, b))
    return ut


def _skift(M: _Matt, z0: float, z1: float) -> list[tuple[float, float]]:
    ut = []
    z = z0
    while z1 - z > 50.0:
        ut.append((z, min(z + M.H, z1)))
        z += M.H + M.fog
    return ut


def bekladnad(b: Bekladnad, M: _Matt) -> list[Montage]:
    n = len(b.vaggar)
    horn = [_horn(b.vaggar[i], b.vaggar[i + 1], M.bak) for i in range(n - 1)]
    ut = []
    for i, kod in enumerate(b.vaggar):
        u0 = horn[i - 1][1] if i > 0 else _u(kod, b.start)
        u1 = horn[i][0] if i < n - 1 else _u(kod, b.slut)
        rng = random.Random(f"fasadsten-{kod}")
        p = Plan(kod, f"Fasadsten {kod}", M.klyv.t_max, material=GRANIT,
                 beskrivning=f"Fasadsten på källarväggen under {kod} (AR-01)")
        stenar = []                                      # (u0, u1, z0, z1) i väggens elevation
        under: list[float] = []
        for k, (za, zb) in enumerate(_skift(M, b.z0, b.z1)):
            # hörnstenarnas skänklar: den långa skänkeln på väggen före hörnet i jämna skift
            ben_hit = M.ben[1] if k % 2 == 0 else M.ben[0]            # hörnet i slutet (stenen hör hit)
            ben_dit = M.ben[0] if k % 2 == 0 else M.ben[1]            # hörnet i början (stenen hör till väggen före)
            a = u0 + (ben_dit + M.fog if i > 0 else 0.0)
            e = u1 - (ben_hit + M.fog if i < n - 1 else 0.0)
            rad = _fyll(a, e, rng, under, M)
            for nr, (sa, sb) in enumerate(rad, 1):
                L = sb - sa
                d = Del(f"Fasadsten {fmt(L)}×{fmt(zb - za)}", kluven_sten(L, zb - za, f"{kod}-{k}-{nr}", M.klyv),
                        GRANIT, "Beklädnadsgranit Bohus Grå, kluven framsida, sågad baksida")
                p.del_i("ST", d, Placering.flytt(sa, -M.bak, za), (sa, za), f"{kod}-ST{k + 1}-{nr:02d}")
                stenar.append((sa, sb, za, zb))
            if i < n - 1:
                ben_b = M.ben[0] if k % 2 == 0 else M.ben[1]
                d = Del(f"Hörnsten {fmt(ben_hit)}/{fmt(ben_b)}×{fmt(zb - za)}",
                        hornsten(ben_hit, ben_b, zb - za, f"{kod}-H{k}", M.klyv), GRANIT,
                        "Hörnsten Bohus Grå, kluven framsida, sågad baksida")
                p.del_i("HS", d, Placering.flytt(u1, -M.bak, za), (u1, za), f"{kod}-HS{k + 1}")
                stenar.append((u1 - ben_hit, u1 + FOGDJUP, za, zb))
            if i > 0:
                stenar.append((u0, u0 + ben_dit, za, zb))
            under = [s + M.fog / 2 for _, s in rad[:-1]] + ([a - M.fog / 2] if i > 0 else []) + \
                    ([e + M.fog / 2] if i < n - 1 else [])
        # fogbruket i fogarna (hörnets fogar hör till väggen före hörnet) och armeringsbruk med fästmassa bakom
        yttre = box(u0, b.z0, u1 + (FOGDJUP if i < n - 1 else 0.0), b.z1)
        fog = yttre.difference(unary_union([box(s[0], s[2], s[1], s[3]) for s in stenar]))
        for g in P.polygoner(fog):
            p.skiva(P.kontur(g), P.hal(g), -M.bak - FOGDJUP, -M.bak, "FB", FOGBRUK, f"Fogbruk {kod}")
        bruk = box(u0 + (M.bak if i > 0 else 0.0), b.z0, u1, b.z1)
        p.skiva(P.kontur(bruk), [], -M.bak, 0.0, "FM", ARMERINGSBRUK, f"Armeringsbruk och fästmassa {kod}")
        ut.append(p.montage())
    return ut


def montage() -> Montage:
    M = _matt()
    m = Montage("Fasadsten", beskrivning="Beklädnadsgranit Bohus Grå på källarväggarna (AR-01), en grupp per vägg")
    for b in BEKLADNAD:
        for g, kod in zip(bekladnad(b, M), b.vaggar):
            m.lagg(g, S.YTTERVAGGAR[kod].placering())
    return m
