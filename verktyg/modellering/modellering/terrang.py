"""Marken runt huset för renderingen (ärende #26): Lantmäteriets markhöjdmodell och de egna inmätningarna, som ersätter
den grova höjdmodellen (Terrarium, geodata.py) där de finns. Används bara av omgivningen i Blender (`mod omgivning`),
inte av modellen.

Källor i `lokalt/terrang` (versionshanteras inte):
- `hojd/`: Lantmäteriets markhöjdmodell (marken utan byggnader och vegetation, RH 2000) i SWEREF 99 TM: fine (1 m)
  över tomten, surroundings (2,5 m) runt omkring. veryfine (0,25 m) används inte: den är fine uppsamplad till närmaste
  punkt (block om 4 × 4 lika höjder), som ger marken trappsteg.
- `punkter/points.csv`: inmätta punkter (GNSS, SWEREF 99 12 00, RH 2000) med kategori i namnet: berg, gras, tomt och
  drener ligger på marken; altan, hus, sten, odling, syren och trad på föremål (träden och stenarna i omgivningen står
  på trad- och stenpunkterna).

Bäddar (upphöjda partier med låg växtlighet, som inte syns i höjdmodellen) läggs till över tomten: marken höjs inom
polygonen, med en mjuk slänt och lite bucklig; växtligheten är en mask för marken (nara_lag.png) och punkter för
växterna (gräs och små buskar, nara_objekt.json).

Höjderna: den finaste rutnätet som täcker en punkt, bilinjärt. Mot de inmätta markpunkterna stämmer Lantmäteriets
höjder väl (berget: median −0,05 m); marken rättas ändå mot dem nära punkterna, med en utjämnad korrektion (Gauss,
σ RATT_SIGMA), så att den går genom inmätningarna. Punkter som avviker mer än RATT_MAX räknas inte (troligen på ett
föremål). Mot Terrarium övergår höjderna mjukt inom KANT m från Lantmäteriets ytterkant.
"""
from __future__ import annotations

import csv
import json
import math
import os
import re
from collections.abc import Sequence

import numpy as np

from .geodata import Passning, sweref, wgs84

TM = dict(lon0=15.0, k0=0.9996, fn=0.0, fe=500000.0)             # SWEREF 99 TM
FILER = (("fine", 1.0), ("surroundings", 2.5))                    # finast först
MARK = ("berg", "gras", "tomt", "drener")
RATT_SIGMA, RATT_VIKT, RATT_MAX = 1.5, 0.5, 0.5
KANT = 40.0
NARA_CELL = 0.25
TACKE_SIGMA = {"berg": 2.0, "gras": 2.0, "trad": 4.0}             # marktäckets maskers räckvidd kring punkterna
STEN_AVST = 0.7                                                  # punkter närmare än så hör till samma sten
TRAD_AVST = 1.0                                                  # och till samma träd (mätt flera gånger)
HUS_FRI = 1.5                                                    # inga träd eller stenar så nära fasaden [m]
VAXT_AVST = 0.22                                                 # bäddarnas växter: rutnätet (slumpat i rutorna) [m]
OMRADE_KAT = ("tomt", "gras", "trad", "hus", "altan")            # tomtens punkter (berget är inmätt längre ut)
OMRADE_KANT = 3.0                                                # tomtens område, utanför punkternas hölje [m]


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


def bygg(omgivning: str, mapp: str, passning: Passning, z0: float, hus: list[tuple[float, float]] | None = None,
         byggnader: Sequence[dict] = (), skog: Sequence[Sequence[tuple[float, float]]] = (),
         utan_trad: Sequence[tuple[float, float]] = (), nya_trad: Sequence[tuple[float, float]] = (),
         baddar: Sequence[dict] = (), buskar: Sequence[tuple[float, float]] = ()) -> dict:
    """Lägg Lantmäteriets höjder i omgivningens rutnät (omgivning/hojd.f32) och skriv ett fint rutnät över tomten
    (omgivning/nara.f32, NARA_CELL m) med rättningen mot de inmätta markpunkterna och bäddarna (hörn, höjd och slänt
    [m]). Det som saknas i OpenStreetMap läggs till (modellens mm): byggnaderna (hörn, höjd [m], valfritt tak och
    färger) och skogen (polygoner) i marktäcket; de inmätta träden nära punkterna utan_trad finns inte och träden i
    nya_trad och buskarna läggs till. Byggnadernas mark tas ur de nya höjderna. Ger statistiken."""
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
    upp, lag = _baddar(xs, ys, baddar)
    zn = zn + upp
    vaxter = _vaxter(xs, ys, zn - z0, baddar)
    j = np.clip(np.round((px - xs[0]) / NARA_CELL).astype(int), 0, len(xs) - 1)
    i = np.clip(np.round((py - ys[0]) / NARA_CELL).astype(int), 0, len(ys) - 1)
    efter = r - korr[i, j]
    (zn - z0).astype(np.float32).tofile(os.path.join(omgivning, "nara.f32"))
    _tacke(omgivning, xs, ys, px, py, p["kategori"])
    from matplotlib.image import imsave
    imsave(os.path.join(omgivning, "nara_lag.png"), np.clip(lag, 0, 1)[::-1], cmap="gray", vmin=0.0, vmax=1.0)
    _objekt(omgivning, xs, ys, zn - z0, px, py, p["H"] - z0, p["kategori"], hus,
            [(x / 1000, y / 1000) for x, y in utan_trad], [(x / 1000, y / 1000) for x, y in nya_trad],
            [(x / 1000, y / 1000) for x, y in buskar], vaxter)
    besk["nara"] = {"x0": float(xs[0]), "y0": float(ys[0]), "cell": NARA_CELL, "nx": len(xs), "ny": len(ys)}
    nya = [[(x / 1000, y / 1000) for x, y in b["horn"]] for b in byggnader]
    besk["byggnader"] += [{"horn": [list(q) for q in h], "hojd": float(b["hojd"]), "typ": "tillagd",
                           **{k: b[k] for k in ("tak", "farg", "takfarg") if k in b}} for h, b in zip(nya, byggnader)]
    for b in besk["byggnader"]:
        cx, cy = np.mean(b["horn"], axis=0)
        z = _bilinjar(zn - z0, xs[0], ys[0], NARA_CELL, cx, cy)
        b["z"] = float(z if np.isfinite(z) else _bilinjar(Z, besk["x0"], besk["y0"], cell, cx, cy))
    _masker(omgivning, besk, {"skog": [[(x / 1000, y / 1000) for x, y in q] for q in skog], "byggnad": nya})
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


def _baddar(xs: np.ndarray, ys: np.ndarray, baddar: Sequence[dict]) -> tuple[np.ndarray, np.ndarray]:
    """Bäddarna i det fina rutnätet: höjningen [m] (hojd inom polygonen, en mjuk slänt slant bred innanför kanten och
    lite bucklig) och den låga växtlighetens mask (bädden och en bit utanför slänten)."""
    import shapely
    upp, lag = np.zeros((len(ys), len(xs))), np.zeros((len(ys), len(xs)))
    for b in baddar:
        q = shapely.Polygon([(x / 1000, y / 1000) for x, y in b["horn"]])
        x0, y0, x1, y1 = q.buffer(1.0).bounds
        j0, j1 = np.searchsorted(xs, [x0, x1])
        i0, i1 = np.searchsorted(ys, [y0, y1])
        X, Y = np.meshgrid(xs[j0:j1], ys[i0:i1])
        pkt = shapely.points(X, Y)
        d = shapely.distance(pkt, q.exterior) * np.where(shapely.contains(q, pkt), 1.0, -1.0)    # in i bädden
        t = np.clip(d / b["slant"], 0.0, 1.0)
        buckla = 1.0 + 0.12 * np.sin(1.7 * X + 0.3) * np.sin(1.3 * Y + 1.1)
        upp[i0:i1, j0:j1] = np.maximum(upp[i0:i1, j0:j1], b["hojd"] * t * t * (3 - 2 * t) * buckla)
        v = np.clip((d + 0.4) / 0.6, 0.0, 1.0)
        lag[i0:i1, j0:j1] = np.maximum(lag[i0:i1, j0:j1], v * v * (3 - 2 * v))
    return upp, lag


def _vaxter(xs: np.ndarray, ys: np.ndarray, zn: np.ndarray, baddar: Sequence[dict]) -> list[list[float]]:
    """Bäddarnas växter (x, y, z): ett rutnät VAXT_AVST, slumpat inom rutorna, över bädden och slänten."""
    import shapely
    rng = np.random.default_rng(17)
    ut = []
    for b in baddar:
        q = shapely.Polygon([(x / 1000, y / 1000) for x, y in b["horn"]]).buffer(0.15)
        x0, y0, x1, y1 = q.bounds
        X, Y = np.meshgrid(np.arange(x0, x1, VAXT_AVST), np.arange(y0, y1, VAXT_AVST))
        X = X + rng.uniform(0, VAXT_AVST, X.shape)
        Y = Y + rng.uniform(0, VAXT_AVST, Y.shape)
        inne = shapely.contains(q, shapely.points(X, Y))
        for x, y in zip(X[inne], Y[inne]):
            z = _bilinjar(zn, xs[0], ys[0], NARA_CELL, float(x), float(y))
            if np.isfinite(z):
                ut.append([round(float(x), 3), round(float(y), 3), round(z, 3)])
    return ut


def _tacke(omgivning: str, xs: np.ndarray, ys: np.ndarray, px: np.ndarray, py: np.ndarray, kat: np.ndarray) -> None:
    """Marktäcket över tomten (nara_tacke.png, låga y nederst som i Blender): berg (R), gräsmatta (G) och barr under
    träden (B) ur de inmätta punkternas kategorier, Gauss kring punkterna; där inga punkter finns är alla noll
    (omgivningens hällmark)."""
    from matplotlib.image import imsave
    vikt = {}
    for k, sigma in TACKE_SIGMA.items():
        w = np.zeros((len(ys), len(xs)))
        cell = float(xs[1] - xs[0])
        r = int(np.ceil(3 * sigma / cell))
        for x, y in zip(px[kat == k], py[kat == k]):
            j, i = int(round((x - xs[0]) / cell)), int(round((y - ys[0]) / cell))
            j0, j1, i0, i1 = max(j - r, 0), min(j + r + 1, len(xs)), max(i - r, 0), min(i + r + 1, len(ys))
            if j0 >= j1 or i0 >= i1:
                continue
            X, Y = np.meshgrid(xs[j0:j1], ys[i0:i1])
            w[i0:i1, j0:j1] = np.maximum(w[i0:i1, j0:j1], np.exp(-((X - x) ** 2 + (Y - y) ** 2) / (2 * sigma ** 2)))
        vikt[k] = w
    berg, gras, barr = vikt["berg"], vikt["gras"], vikt["trad"] * (1 - vikt["gras"])
    summa = np.maximum(berg + gras + barr, 1.0)
    rgba = np.stack([berg / summa, gras / summa, barr / summa, np.ones_like(berg)], axis=-1)
    imsave(os.path.join(omgivning, "nara_tacke.png"), np.clip(rgba, 0, 1)[::-1])


def _bilinjar(z: np.ndarray, x0: float, y0: float, cell: float, x: float, y: float) -> float:
    ny, nx = z.shape
    fx, fy = min(max((x - x0) / cell, 0.0), nx - 1.001), min(max((y - y0) / cell, 0.0), ny - 1.001)
    j, i = int(fx), int(fy)
    tx, ty = fx - j, fy - i
    return float(z[i, j] * (1 - tx) * (1 - ty) + z[i, j + 1] * tx * (1 - ty) + z[i + 1, j] * (1 - tx) * ty
                 + z[i + 1, j + 1] * tx * ty)


def _masker(omgivning: str, besk: dict, polygoner: dict[str, list[list[tuple[float, float]]]]) -> None:
    """Lägg polygonerna (modellens m) i marktäckets masker (marktacke_*.png, kanalerna besk["kanaler"]), med mjuka
    kanter (en cell)."""
    from matplotlib.image import imread, imsave
    from matplotlib.path import Path
    n, cell = besk["n"], besk["cell"]
    X, Y = np.meshgrid(besk["x0"] + cell * np.arange(n), besk["y0"] + cell * np.arange(n))
    P = np.column_stack([X.ravel(), Y.ravel()])
    for i, kanaler in enumerate(besk["kanaler"]):
        if not any(polygoner.get(k) for k in kanaler):
            continue
        fil = os.path.join(omgivning, f"marktacke_{i}.png")
        im = imread(fil)[::-1].astype(float)                      # rad i = rutnätets y nr i, som när den skrevs
        for j, k in enumerate(kanaler):
            for q in polygoner.get(k, []):
                m = Path(q).contains_points(P).reshape(n, n).astype(float)
                for _ in range(2):                                  # mjuk kant: medel över 3 × 3 celler
                    mp = np.pad(m, 1, mode="edge")
                    m = np.mean([mp[a:a + n, b:b + n] for a in range(3) for b in range(3)], axis=0)
                im[..., j] = np.maximum(im[..., j], m)
        imsave(fil, np.clip(im, 0, 1)[::-1])


def _grupper(x: np.ndarray, y: np.ndarray, z: np.ndarray, avst: float) -> list[list[tuple[float, float, float]]]:
    """Punkterna i grupper: de som ligger närmare än avst från någon i gruppen."""
    grupper: list[list[tuple[float, float, float]]] = []
    for q in zip(x.tolist(), y.tolist(), z.tolist()):
        nara = [g for g in grupper if any(math.hypot(q[0] - a[0], q[1] - a[1]) < avst for a in g)]
        grupper = [g for g in grupper if g not in nara] + [[q] + [a for g in nara for a in g]]
    return grupper


def _objekt(omgivning: str, xs: np.ndarray, ys: np.ndarray, zn: np.ndarray, px: np.ndarray, py: np.ndarray,
            pz: np.ndarray, kat: np.ndarray, hus: list[tuple[float, float]] | None,
            utan: Sequence[tuple[float, float]] = (), nya: Sequence[tuple[float, float]] = (),
            buskar: Sequence[tuple[float, float]] = (), vaxter: Sequence[Sequence[float]] = ()) -> None:
    """Träden, buskarna och stenarna över tomten (nara_objekt.json, modellens m): träden i de inmätta trädpunkterna
    på marken (punkterna närmare än TRAD_AVST är samma träd, mätt flera gånger; utom de inom TRAD_AVST från en punkt i
    utan, som inte finns) och de tillagda i nya, buskarna i buskar, bäddarnas växter, stenarna som grupper av
    stenpunkter
    (STEN_AVST) med läge, storlek och höjd över marken; inget inom HUS_FRI m från husets fasad (hus, mm: det som
    stod där är borta). Området är tomten, där träden är inmätta: det konvexa höljet
    kring punkterna i OMRADE_KAT (OMRADE_KANT m utanför); där står bara de inmätta träden."""
    from shapely.geometry import MultiPoint, Point, Polygon
    i = np.isin(kat, OMRADE_KAT)
    omrade = MultiPoint(list(zip(px[i], py[i]))).convex_hull.buffer(OMRADE_KANT).simplify(0.5)
    fasad = Polygon([(x / 1000, y / 1000) for x, y in hus]).buffer(HUS_FRI) if hus else None
    utanfor = np.array([fasad is None or not fasad.contains(Point(x, y)) for x, y in zip(px, py)])
    px, py, pz, kat = px[utanfor], py[utanfor], pz[utanfor], kat[utanfor]

    def mark(x: float, y: float) -> float:
        j = int(np.clip(round((x - xs[0]) / NARA_CELL), 0, len(xs) - 1))
        i = int(np.clip(round((y - ys[0]) / NARA_CELL), 0, len(ys) - 1))
        z = zn[i, j]
        return float(z) if np.isfinite(z) else float("nan")
    trad = []
    for g in _grupper(px[kat == "trad"], py[kat == "trad"], pz[kat == "trad"], TRAD_AVST):
        cx, cy = float(np.mean([a[0] for a in g])), float(np.mean([a[1] for a in g]))
        if all(math.hypot(cx - ux, cy - uy) > TRAD_AVST for ux, uy in utan):
            trad.append([cx, cy, mark(cx, cy)])
    trad += [[x, y, mark(x, y)] for x, y in nya]
    stenar = []
    for g in _grupper(px[kat == "sten"], py[kat == "sten"], pz[kat == "sten"], STEN_AVST):
        a = np.array(g)
        cx, cy = float(a[:, 0].mean()), float(a[:, 1].mean())
        zm = mark(cx, cy)
        if not np.isfinite(zm):
            continue
        storlek = float(max(0.5, 2 * np.hypot(a[:, 0] - cx, a[:, 1] - cy).max() + 0.3))
        stenar.append([cx, cy, zm, storlek, float(max(0.15, np.max(a[:, 2]) - zm))])
    json.dump({"trad": [t for t in trad if np.isfinite(t[2])], "stenar": stenar,
               "buskar": [[x, y, mark(x, y)] for x, y in buskar if np.isfinite(mark(x, y))], "vaxter": list(vaxter),
               "omrade": [[round(x, 2), round(y, 2)] for x, y in omrade.exterior.coords]},
              open(os.path.join(omgivning, "nara_objekt.json"), "w", encoding="utf-8"))
