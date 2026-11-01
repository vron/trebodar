"""Virke och skivor som delar: likadana bitar blir samma del (en produkt i STEP, ett nät i GLB, en rad i
materiallistan). Virkets lokala x går längs fibrerna (kaplängden), y är tjockleken och z bredden (b ≤ h)."""
from __future__ import annotations

import math
from typing import Sequence

import numpy as np

from modellering import Del, Lada, Material, Placering, Prisma, lada, prisma

_DELAR: dict[tuple[str, str], Del] = {}
_PROFILNR: dict[str, int] = {}
_E = {"x": np.array([1.0, 0.0, 0.0]), "y": np.array([0.0, 1.0, 0.0]), "z": np.array([0.0, 0.0, 1.0])}


def fmt(v: float) -> str:
    """Mått för namn: heltal utan decimaler, annars en decimal."""
    r = round(v, 1)
    return f"{r:.0f}" if abs(r - round(r)) < 1e-9 else f"{r:.1f}"


def del_(namn: str, form: Lada | Prisma, material: Material, beskrivning: str = "") -> Del:
    """Samma recept och material ger samma del."""
    k = (form.nyckel(), material.namn)
    if k not in _DELAR:
        _DELAR[k] = Del(namn, form, material, beskrivning)
    return _DELAR[k]


def virke(L: float, b: float, h: float, material: Material) -> Del:
    """Rakt virke b×h med kaplängden L."""
    b, h = sorted((b, h))
    return del_(f"{material.namn} {fmt(b)}×{fmt(h)} L={fmt(L)}", lada(L, b, h), material)


def virke_i_lada(x0: float, x1: float, y0: float, y1: float, z0: float, z1: float, fiber: str,
                 material: Material) -> tuple[Del, Placering]:
    """Virke som fyller lådan (i förälderns system) med fibrerna längs axeln `fiber` ("x", "y" eller "z")."""
    lo = {"x": min(x0, x1), "y": min(y0, y1), "z": min(z0, z1)}
    hi = {"x": max(x0, x1), "y": max(y0, y1), "z": max(z0, z1)}
    d = {a: hi[a] - lo[a] for a in "xyz"}
    ovr = sorted((a for a in "xyz" if a != fiber), key=lambda a: d[a])
    ab, ah = ovr[0], ovr[1]
    s = float(np.cross(_E[fiber], _E[ab]) @ _E[ah])
    R = np.column_stack([_E[fiber], _E[ab], s * _E[ah]])
    o = np.zeros(3)
    for i, a in enumerate("xyz"):
        o[i] = hi[a] if (a == ah and s < 0) else lo[a]
    return virke(d[fiber], d[ab], d[ah], material), Placering.fran_matris(np.vstack([np.column_stack([R, o]),
                                                                                     [0, 0, 0, 1]]))


def _minsta_rektangel(P: np.ndarray) -> tuple[float, float, float]:
    """(vinkel, längd, bredd) för minsta omslutande rektangel med en sida längs en kant i polygonen."""
    best = (math.inf, 0.0, 0.0, 0.0)
    for i in range(len(P)):
        e = P[(i + 1) % len(P)] - P[i]
        L = float(np.hypot(*e))
        if L < 1e-9:
            continue
        u = e / L
        v = np.array([-u[1], u[0]])
        a, b = P @ u, P @ v
        w, h = float(a.max() - a.min()), float(b.max() - b.min())
        if w * h < best[0] - 1e-6:
            ang = math.atan2(u[1], u[0])
            if w < h:
                w, h, ang = h, w, ang + math.pi / 2
            best = (w * h, ang, w, h)
    return best[1], best[2], best[3]


def virke_profil(pts: Sequence[Sequence[float]], t: float, material: Material, prefix: str = "") -> tuple[Del, Placering]:
    """Virke med en godtycklig profil i förälderns xy-plan, tjockleken t längs förälderns +z (z 0 … t).
    Delens eget x läggs längs profilens längdriktning (minsta omslutande rektangel)."""
    P = np.asarray(pts, dtype=float)
    ang, L, B = _minsta_rektangel(P)
    # vinklar nära multiplar av 90° avrundas, så att raka bitar får exakta placeringar
    q = ang / (math.pi / 2)
    c, s = (math.cos(ang), math.sin(ang))
    if abs(q - round(q)) < 1e-9:
        c, s = [(1.0, 0.0), (0.0, 1.0), (-1.0, 0.0), (0.0, -1.0)][round(q) % 4]
    Rm = np.array([[c, -s], [s, c]])
    lok = P @ Rm                                  # punkterna i det vridna systemet
    mn = lok.min(axis=0)
    lok = lok - mn
    lok = np.round(lok, 6)
    o = Rm @ mn
    form = prisma([tuple(p) for p in lok], t)
    if _area(lok) < 0:
        form = prisma([tuple(p) for p in lok[::-1]], t)
    nyckel = form.nyckel()
    k = (nyckel, material.namn)
    if k not in _DELAR:
        bas = f"{material.namn} {fmt(min(B, t))}×{fmt(max(B, t))} L={fmt(L)}"
        n = _PROFILNR[bas] = _PROFILNR.get(bas, 0) + 1
        _DELAR[k] = Del(f"{prefix}{bas} kapad {n}", form, material)
    pl = Placering(((c, -s, 0.0), (s, c, 0.0), (0.0, 0.0, 1.0)), (float(o[0]), float(o[1]), 0.0))
    return _DELAR[k], pl


def _area(p: np.ndarray) -> float:
    return float(0.5 * np.sum(p[:, 0] * np.roll(p[:, 1], -1) - np.roll(p[:, 0], -1) * p[:, 1]))


def skiva(kontur: Sequence[Sequence[float]], t: float, material: Material, namn: str,
          hal: Sequence[Sequence[Sequence[float]]] = ()) -> Del:
    """Skiva med kontur i eget xy-plan och tjockleken t längs +z."""
    return del_(namn, prisma(kontur, t, hal), material)
