"""Marken runt huset för renderingen (ärende #26): Lantmäteriets markhöjdmodell och de egna inmätningarna, som ersätter
den grova höjdmodellen (Terrarium, geodata.py) där de finns. Används bara av omgivningen i Blender (`mod omgivning`),
inte av modellen.

Källor i `lokalt/terrang` (versionshanteras inte):
- `hojd/`: Lantmäteriets markhöjdmodell (marken utan byggnader och vegetation, RH 2000) i SWEREF 99 TM: veryfine
  (0,25 m) och fine (1 m) över tomten, surroundings (2,5 m) runt omkring.
- `punkter/points.csv`: inmätta punkter (GNSS, SWEREF 99 12 00, RH 2000) med kategori i namnet: berg, gras, tomt och
  drener ligger på marken; altan, hus, sten, odling, syren och trad på föremål (för senare: stenar, träd, buskar).

Höjderna: den finaste rutnätet som täcker en punkt, bilinjärt. Mot de inmätta markpunkterna stämmer Lantmäteriets
höjder väl (berget: median −0,03 m); marken rättas ändå mot dem nära punkterna, med en utjämnad korrektion (Gauss,
σ RATT_SIGMA), så att den går genom inmätningarna. Punkter som avviker mer än RATT_MAX räknas inte (troligen på ett
föremål). Mot Terrarium övergår höjderna mjukt inom KANT m från Lantmäteriets ytterkant.
"""
from __future__ import annotations

import csv
import json
import os
import re

import numpy as np

from .geodata import Passning, sweref, wgs84

TM = dict(lon0=15.0, k0=0.9996, fn=0.0, fe=500000.0)             # SWEREF 99 TM
FILER = (("veryfine", 0.25), ("fine", 1.0), ("surroundings", 2.5))  # finast först
MARK = ("berg", "gras", "tomt", "drener")
RATT_SIGMA, RATT_VIKT, RATT_MAX = 1.5, 0.5, 0.5
KANT = 40.0
NARA_CELL = 0.25


class Rutnat:
    """Ett av Lantmäteriets rutnät i SWEREF 99 TM: höjden (RH 2000) i (N, E)."""

    def __init__(self, fil: str, cell: float):
        a = np.loadtxt(fil, delimiter=",")
        self.E, self.N = np.unique(a[:, 0]), np.unique(a[:, 1])
        self.cell = cell
        self.Z = np.full((len(self.N), len(self.E)), np.nan)
        self.Z[np.searchsorted(self.N, a[:, 1]), np.searchsorted(self.E, a[:, 0])] = a[:, 2]

    def prov(self, N: np.ndarray, E: np.ndarray) -> np.ndarray:
        fx, fy = (E - self.E[0]) / self.cell, (N - self.N[0]) / self.cell
        inne = (fx >= 0) & (fy >= 0) & (fx <= len(self.E) - 1) & (fy <= len(self.N) - 1)
        j = np.clip(fx.astype(int), 0, len(self.E) - 2)
        i = np.clip(fy.astype(int), 0, len(self.N) - 2)
        tx, ty = np.clip(fx - j, 0, 1), np.clip(fy - i, 0, 1)
        Z = self.Z
        z = (Z[i, j] * (1 - tx) * (1 - ty) + Z[i, j + 1] * tx * (1 - ty) + Z[i + 1, j] * (1 - tx) * ty
             + Z[i + 1, j + 1] * tx * ty)
        return np.where(inne, z, np.nan)

    def kant(self, N: np.ndarray, E: np.ndarray) -> np.ndarray:
        """Avståndet in från rutnätets ytterkant [m] (negativt utanför)."""
        return np.minimum.reduce([E - self.E[0], self.E[-1] - E, N - self.N[0], self.N[-1] - N])


def las(mapp: str) -> list[Rutnat]:
    return [Rutnat(os.path.join(mapp, "hojd", f"{namn}.xyz"), c) for namn, c in FILER
            if os.path.exists(os.path.join(mapp, "hojd", f"{namn}.xyz"))]


def tm(passning: Passning, x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Modellens (x, y) i mm → SWEREF 99 TM (N, E)."""
    return sweref(*wgs84(*passning.till_sweref(x, y)), **TM)


def hojd(rutnat: list[Rutnat], N: np.ndarray, E: np.ndarray) -> np.ndarray:
    """Höjden ur det finaste rutnätet som täcker punkten (NaN utanför alla)."""
    z = np.full(np.shape(N), np.nan)
    for r in rutnat:
        z = np.where(np.isnan(z), r.prov(N, E), z)
    return z


def punkter(mapp: str) -> dict[str, np.ndarray]:
    """De inmätta punkterna: N, E (SWEREF 99 12 00), H, kategori och höjdens noggrannhet."""
    rader = list(csv.DictReader(open(os.path.join(mapp, "punkter", "points.csv"), encoding="utf-8")))

    def kategori(namn: str) -> str:
        k = re.sub(r"[\-0-9]*", "", namn)
        for a, b in (("nn", "n"), ("ggg", "g"), ("sss", "s"), ("ss", "s"), ("tomtg", "tomt")):
            k = k.replace(a, b)
        return k
    return {"N": np.array([float(r["Northing"]) for r in rader]), "E": np.array([float(r["Easting"]) for r in rader]),
            "H": np.array([float(r["Elevation"]) for r in rader]),
            "kategori": np.array([kategori(r["Name"]) for r in rader]),
            "noggrannhet": np.array([float(r["User_Vertical_Accuracy"]) for r in rader])}


def _sigma_rutor(cell: float) -> int:
    return int(np.ceil(3 * RATT_SIGMA / cell))


def rattning(xs: np.ndarray, ys: np.ndarray, px: np.ndarray, py: np.ndarray, r: np.ndarray) -> np.ndarray:
    """Korrektionen i rutnätet (xs, ys i m) ur avvikelserna r i punkterna (px, py): Σ w r / (Σ w + RATT_VIKT), w Gauss
    med σ RATT_SIGMA, så att den går mot noll långt från punkterna."""
    cell = float(xs[1] - xs[0])
    s, sw = np.zeros((len(ys), len(xs))), np.zeros((len(ys), len(xs)))
    k = _sigma_rutor(cell)
    for x, y, d in zip(px, py, r):
        j, i = int(round((x - xs[0]) / cell)), int(round((y - ys[0]) / cell))
        j0, j1, i0, i1 = max(j - k, 0), min(j + k + 1, len(xs)), max(i - k, 0), min(i + k + 1, len(ys))
        if j0 >= j1 or i0 >= i1:
            continue
        X, Y = np.meshgrid(xs[j0:j1], ys[i0:i1])
        w = np.exp(-((X - x) ** 2 + (Y - y) ** 2) / (2 * RATT_SIGMA ** 2))
        s[i0:i1, j0:j1] += w * d
        sw[i0:i1, j0:j1] += w
    return s / (sw + RATT_VIKT)


def bygg(omgivning: str, mapp: str, passning: Passning, z0: float) -> dict:
    """Lägg Lantmäteriets höjder i omgivningens rutnät (omgivning/hojd.f32) och skriv ett fint rutnät över tomten
    (omgivning/nara.f32, NARA_CELL m) med rättningen mot de inmätta markpunkterna. Ger statistiken."""
    besk = json.load(open(os.path.join(omgivning, "omgivning.json"), encoding="utf-8"))
    rut = las(mapp)
    # omgivningens rutnät: Lantmäteriet där det finns, mjukt mot Terrarium vid ytterkanten
    n, cell = besk["n"], besk["cell"]
    xs, ys = besk["x0"] + cell * np.arange(n), besk["y0"] + cell * np.arange(n)
    X, Y = np.meshgrid(xs, ys)
    N, E = tm(passning, X * 1000, Y * 1000)
    Zt = np.fromfile(os.path.join(omgivning, "hojd.f32"), dtype=np.float32).reshape(n, n).astype(float)
    zl = hojd(rut, N, E) - z0
    w = np.clip(np.max([r.kant(N, E) for r in rut], axis=0) / KANT, 0, 1)
    Z = np.where(np.isnan(zl), Zt, w * np.nan_to_num(zl) + (1 - w) * Zt)
    Z.astype(np.float32).tofile(os.path.join(omgivning, "hojd.f32"))
    # det fina rutnätet över det finaste rutnätets utbredning, i modellens koordinater
    f = rut[0]
    hn, he = sweref(*wgs84(f.N[[0, 0, -1, -1]], f.E[[0, -1, 0, -1]], **TM))      # hörnen: TM → 12 00
    hx, hy = passning.till_modell(hn, he)
    xs = np.arange(hx.min() / 1000, hx.max() / 1000, NARA_CELL)
    ys = np.arange(hy.min() / 1000, hy.max() / 1000, NARA_CELL)
    X, Y = np.meshgrid(xs, ys)
    N, E = tm(passning, X * 1000, Y * 1000)
    zn = f.prov(N, E)
    # rättningen mot de inmätta markpunkterna
    p = punkter(mapp)
    pn, pe = sweref(*wgs84(p["N"], p["E"]), **TM)
    lm = hojd(rut, pn, pe)
    px, py = passning.till_modell(p["N"], p["E"])
    px, py = px / 1000, py / 1000
    mark = np.isin(p["kategori"], MARK) & np.isfinite(lm)
    r = p["H"] - lm
    anv = mark & (np.abs(r) <= RATT_MAX)
    korr = rattning(xs, ys, px[anv], py[anv], r[anv])
    zn = zn + korr
    j = np.clip(np.round((px - xs[0]) / NARA_CELL).astype(int), 0, len(xs) - 1)
    i = np.clip(np.round((py - ys[0]) / NARA_CELL).astype(int), 0, len(ys) - 1)
    efter = r - korr[i, j]
    (zn - z0).astype(np.float32).tofile(os.path.join(omgivning, "nara.f32"))
    besk["nara"] = {"x0": float(xs[0]), "y0": float(ys[0]), "cell": NARA_CELL, "nx": len(xs), "ny": len(ys)}
    besk["kalla"] = ("Höjd: Lantmäteriets markhöjdmodell och egna inmätningar (GNSS) runt tomten, AWS Terrain Tiles "
                     "(Terrarium) utanför. Marktäcke, kust, byggnader och vägar: © OpenStreetMap-bidragsgivare, ODbL.")
    json.dump(besk, open(os.path.join(omgivning, "omgivning.json"), "w", encoding="utf-8"), ensure_ascii=False)
    stat = {}
    for k in sorted(set(p["kategori"])):
        m = (p["kategori"] == k) & np.isfinite(lm)
        if m.any():
            stat[k] = (int(m.sum()), float(np.median(r[m])), float(np.median(np.abs(r[m]))),
                       float(np.median(np.abs(efter[m]))), k in MARK)
    return {"nara": besk["nara"], "punkter": stat, "uteslutna": int((mark & ~anv).sum())}
