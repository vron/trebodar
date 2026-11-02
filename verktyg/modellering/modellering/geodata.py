"""Geodata för omgivningen: höjder och marktäcke runt platsen i modellens koordinater, för renderingen.

Källor (öppna data):
- Höjd: AWS Terrain Tiles (Terrarium, zoom 14, ca 5 m pixlar; i Sverige ungefär 25 m upplösning, EU-DEM/Copernicus).
- Kust, berg i dagen, skog, åker, våtmark, vatten, byggnader och vägar: OpenStreetMap genom Overpass API,
  © OpenStreetMap-bidragsgivare, ODbL.

Koordinater: WGS 84 → SWEREF 99 TM-zon (Gauss–Krüger, Lantmäteriets formler, GRS 80) → modellens (rotation och
förflyttning, passade mot punkter med kända koordinater i båda, t.ex. fasadens hörn). Höjderna över havet blir
modellens z med platsens höjd för z = 0.

Kustlinjen avgör land och hav (höjdmodellen är för grov vid stranden): kustlinjerna och områdets kant delar området i
ytor, och höjden mitt i ytan avgör om den är land eller hav. Marktäcket blir masker (0–1) i ett rutnät, lätt
utjämnade, och byggnaderna en lista med hörn och höjd.

    hamta(lat, lon, radie, mapp)          ladda ner till mapp/nedladdat (en gång)
    bygg(mapp, passning, radie, cell, z0) rutnät, masker och byggnader i mapp/
"""
from __future__ import annotations

import glob
import json
import math
import os
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import numpy as np

A_GRS80, F_GRS80 = 6378137.0, 1 / 298.257222101
ZOOM = 14
OVERPASS = "https://overpass-api.de/api/interpreter"
TERRARIUM = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"

# marktäckets klasser: (namn, OSM-taggar); masker i tre bilder med fyra kanaler var
KLASSER = [
    ("berg", [("natural", "bare_rock"), ("natural", "rock"), ("natural", "stone"), ("natural", "cliff")]),
    ("skog", [("landuse", "forest"), ("natural", "wood")]),
    ("vatten", [("natural", "water"), ("water", "*"), ("waterway", "riverbank")]),
    ("aker", [("landuse", "farmland"), ("landuse", "meadow"), ("landuse", "farmyard")]),
    ("vatmark", [("natural", "wetland")]),
    ("sand", [("natural", "beach"), ("natural", "sand")]),
    ("vag", []),
    ("stig", []),
    ("tradgard", [("landuse", "residential"), ("landuse", "grass"), ("leisure", "pitch"), ("leisure", "park"),
                  ("landuse", "recreation_ground")]),
    ("snar", [("natural", "scrub"), ("natural", "heath")]),
    ("hav", []),
    ("byggnad", []),
]
VAGBREDD = {"motorway": 10, "trunk": 9, "primary": 8, "secondary": 7, "tertiary": 6, "unclassified": 4.5,
            "residential": 4.5, "service": 3.0, "track": 2.5, "living_street": 4, "road": 4}
STIGBREDD = {"path": 1.2, "footway": 1.5, "cycleway": 2.0, "steps": 1.5, "bridleway": 2.0}


# ------------------------------------------------------------------ koordinater

def sweref(lat: np.ndarray | float, lon: np.ndarray | float, lon0: float = 12.0, k0: float = 1.0, fn: float = 0.0,
           fe: float = 150000.0) -> tuple[np.ndarray, np.ndarray]:
    """WGS 84 (grader) → SWEREF 99 TM-zon (N, E i m); standard zonen 12 00."""
    e2 = F_GRS80 * (2 - F_GRS80)
    n = F_GRS80 / (2 - F_GRS80)
    ah = A_GRS80 / (1 + n) * (1 + n * n / 4 + n ** 4 / 64)
    a_, b_ = e2, (5 * e2 ** 2 - e2 ** 3) / 6
    c_, d_ = (104 * e2 ** 3 - 45 * e2 ** 4) / 120, 1237 * e2 ** 4 / 1260
    b1 = n / 2 - 2 * n ** 2 / 3 + 5 * n ** 3 / 16 + 41 * n ** 4 / 180
    b2 = 13 * n ** 2 / 48 - 3 * n ** 3 / 5 + 557 * n ** 4 / 1440
    b3 = 61 * n ** 3 / 240 - 103 * n ** 4 / 140
    b4 = 49561 * n ** 4 / 161280
    fi, dl = np.radians(lat), np.radians(np.asarray(lon) - lon0)
    s = np.sin(fi)
    fis = fi - s * np.cos(fi) * (a_ + b_ * s ** 2 + c_ * s ** 4 + d_ * s ** 6)
    xi = np.arctan(np.tan(fis) / np.cos(dl))
    eta = np.arctanh(np.cos(fis) * np.sin(dl))
    N = k0 * ah * (xi + b1 * np.sin(2 * xi) * np.cosh(2 * eta) + b2 * np.sin(4 * xi) * np.cosh(4 * eta)
                   + b3 * np.sin(6 * xi) * np.cosh(6 * eta) + b4 * np.sin(8 * xi) * np.cosh(8 * eta)) + fn
    E = k0 * ah * (eta + b1 * np.cos(2 * xi) * np.sinh(2 * eta) + b2 * np.cos(4 * xi) * np.sinh(4 * eta)
                   + b3 * np.cos(6 * xi) * np.sinh(6 * eta) + b4 * np.cos(8 * xi) * np.sinh(8 * eta)) + fe
    return N, E


def wgs84(N: np.ndarray | float, E: np.ndarray | float, **zon: float) -> tuple[np.ndarray, np.ndarray]:
    """SWEREF 99 TM-zon → WGS 84 (lat, lon i grader), genom att lösa sweref() med Newtons metod."""
    N, E = np.asarray(N, dtype=float), np.asarray(E, dtype=float)
    lat = np.full_like(N, 59.0)
    lon = np.full_like(N, zon.get("lon0", 12.0))
    for _ in range(12):
        n0, e0 = sweref(lat, lon, **zon)
        lat = lat + (N - n0) / 111200.0
        lon = lon + (E - e0) / (111320.0 * np.cos(np.radians(lat)))
    return lat, lon


@dataclass(frozen=True)
class Passning:
    """Modellens koordinater (mm) ↔ SWEREF 99 (N, E i m): E = e0 + (x cos θ − y sin θ)/1000,
    N = n0 + (x sin θ + y cos θ)/1000."""
    theta: float
    e0: float
    n0: float

    def till_sweref(self, x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        c, s = math.cos(self.theta), math.sin(self.theta)
        return self.n0 + (x * s + y * c) / 1000, self.e0 + (x * c - y * s) / 1000

    def till_modell(self, N: np.ndarray, E: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        c, s = math.cos(self.theta), math.sin(self.theta)
        de, dn = (np.asarray(E) - self.e0) * 1000, (np.asarray(N) - self.n0) * 1000
        return de * c + dn * s, -de * s + dn * c


def passa(modell: list[tuple[float, float]], sw: list[tuple[float, float]]) -> tuple[Passning, float]:
    """Rotation och förflyttning (minsta kvadrat) från modellens punkter (mm) till SWEREF (N, E i m), och största
    restfelet (mm)."""
    P = np.array(modell, dtype=float) / 1000
    Q = np.array([(e, n) for n, e in sw], dtype=float)
    pc, qc = P.mean(0), Q.mean(0)
    u, _, vt = np.linalg.svd((P - pc).T @ (Q - qc))
    r = (u @ vt).T
    t = qc - r @ pc
    fel = float(np.hypot(*((P @ r.T + t) - Q).T).max() * 1000)
    return Passning(math.atan2(r[1, 0], r[0, 0]), float(t[0]), float(t[1])), fel


# ------------------------------------------------------------------ nedladdning

def _ruta(lat: float, lon: float, z: int = ZOOM) -> tuple[float, float]:
    n = 2 ** z
    la = math.radians(lat)
    return (lon + 180) / 360 * n, (1 - math.log(math.tan(la) + 1 / math.cos(la)) / math.pi) / 2 * n


def omrade(lat: float, lon: float, radie: float) -> tuple[float, float, float, float]:
    """(syd, väst, nord, öst) i grader för en kvadrat med halva sidan radie (m) runt platsen."""
    dlat = radie / 111132.0
    dlon = radie / (111320.0 * math.cos(math.radians(lat)))
    return lat - dlat, lon - dlon, lat + dlat, lon + dlon


def hamta(lat: float, lon: float, radie: float, mapp: str, kontakt: str = "trebodar") -> None:
    """Ladda ner OpenStreetMap (Overpass) och höjdrutor (Terrarium) för området till mapp/nedladdat (bara det som
    saknas)."""
    s, w, n, e = omrade(lat, lon, radie)
    osm = os.path.join(mapp, "nedladdat", "osm")
    hojd = os.path.join(mapp, "nedladdat", "hojd")
    os.makedirs(osm, exist_ok=True)
    os.makedirs(hojd, exist_ok=True)
    fil = os.path.join(osm, "osm.json")
    if not os.path.exists(fil):
        b = f"({s:.5f},{w:.5f},{n:.5f},{e:.5f})"
        q = "[out:json][timeout:120];(" + "".join(
            f'{t}["{k}"]{b};' for k in ("natural", "landuse", "leisure", "water", "waterway", "building", "highway",
                                         "man_made") for t in ("way", "relation")) + ");out geom;"
        subprocess.run(["curl", "-s", "-m", "300", "-A", kontakt, "--data-urlencode", f"data={q}", OVERPASS, "-o", fil],
                       check=True)
    x0, y0 = _ruta(n, w)
    x1, y1 = _ruta(s, e)
    for x in range(int(x0), int(x1) + 1):
        for y in range(int(y0), int(y1) + 1):
            f = os.path.join(hojd, f"t{ZOOM}_{x}_{y}.png")
            if not os.path.exists(f):
                subprocess.run(["curl", "-s", "-m", "60", "-o", f, TERRARIUM.format(z=ZOOM, x=x, y=y)], check=True)


# ------------------------------------------------------------------ rutnät

def _mosaik(mapp: str) -> tuple[np.ndarray, int, int]:
    from matplotlib.image import imread
    rutor = glob.glob(os.path.join(mapp, "nedladdat", "hojd", f"t{ZOOM}_*.png"))
    xy = [tuple(int(v) for v in os.path.basename(f)[:-4].split("_")[1:]) for f in rutor]
    xs, ys = sorted({x for x, _ in xy}), sorted({y for _, y in xy})
    H = np.zeros((256 * len(ys), 256 * len(xs)), dtype=np.float64)
    for f, (x, y) in zip(rutor, xy):
        im = imread(f)[:, :, :3].astype(np.float64) * 255.0
        H[(y - ys[0]) * 256:(y - ys[0] + 1) * 256, (x - xs[0]) * 256:(x - xs[0] + 1) * 256] = \
            im[:, :, 0] * 256 + im[:, :, 1] + im[:, :, 2] / 256 - 32768
    return H, xs[0], ys[0]


def _hojd(H: np.ndarray, x0: int, y0: int, lat: np.ndarray, lon: np.ndarray) -> np.ndarray:
    """Höjden (bilinjärt) i mosaiken vid (lat, lon)."""
    n = 2 ** ZOOM
    px = ((lon + 180) / 360 * n - x0) * 256 - 0.5
    la = np.radians(lat)
    py = ((1 - np.log(np.tan(la) + 1 / np.cos(la)) / math.pi) / 2 * n - y0) * 256 - 0.5
    i0 = np.clip(np.floor(py).astype(int), 0, H.shape[0] - 2)
    j0 = np.clip(np.floor(px).astype(int), 0, H.shape[1] - 2)
    fy, fx = np.clip(py - i0, 0, 1), np.clip(px - j0, 0, 1)
    return (H[i0, j0] * (1 - fx) * (1 - fy) + H[i0, j0 + 1] * fx * (1 - fy) + H[i0 + 1, j0] * (1 - fx) * fy
            + H[i0 + 1, j0 + 1] * fx * fy)


def _polygoner(el: dict, till: Callable[[float, float], tuple[float, float]]) -> list[Any]:
    """OSM-elementets ytor (shapely) i modellens koordinater (m): slutna vägar och multipolygonernas ringar."""
    from shapely.geometry import LineString, Polygon
    from shapely.ops import linemerge, polygonize, unary_union
    if el["type"] == "way" and el.get("geometry"):
        p = [till(q["lat"], q["lon"]) for q in el["geometry"]]
        return [Polygon(p).buffer(0)] if len(p) >= 4 and p[0] == p[-1] else []
    if el["type"] == "relation":
        ytter: list[Any] = []
        inre: list[Any] = []
        for mm in el.get("members", []):
            if "geometry" in mm and len(mm["geometry"]) >= 2:
                ls = LineString([till(q["lat"], q["lon"]) for q in mm["geometry"]])
                (inre if mm.get("role") == "inner" else ytter).append(ls)
        if not ytter:
            return []
        y = unary_union(list(polygonize(linemerge(ytter))))
        if inre:
            y = y.difference(unary_union(list(polygonize(linemerge(inre)))))
        return [y.buffer(0)]
    return []


def _rastrera(mask: np.ndarray, geom: object, xs: np.ndarray, ys: np.ndarray) -> None:
    """Sätt mask = 1 i cellerna vars mitt ligger i geom (bara inom geometrins omslutande rektangel)."""
    import shapely
    if geom.is_empty:  # type: ignore[attr-defined]
        return
    x0, y0, x1, y1 = geom.bounds  # type: ignore[attr-defined]
    i0, i1 = np.searchsorted(ys, y0), np.searchsorted(ys, y1, side="right")
    j0, j1 = np.searchsorted(xs, x0), np.searchsorted(xs, x1, side="right")
    if i1 <= i0 or j1 <= j0:
        return
    shapely.prepare(geom)
    X, Y = np.meshgrid(xs[j0:j1], ys[i0:i1])
    mask[i0:i1, j0:j1] = np.maximum(mask[i0:i1, j0:j1], shapely.contains_xy(geom, X, Y))


def _klass(tags: dict) -> str | None:
    for namn, par in KLASSER:
        for k, v in par:
            if k in tags and (v == "*" or tags[k] == v):
                return namn
    return None


def _jamna(m: np.ndarray, sigma: float) -> np.ndarray:
    """Gaussisk utjämning (separabel), sigma i celler."""
    if sigma <= 0:
        return m
    r = int(math.ceil(3 * sigma))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    k /= k.sum()
    m = np.apply_along_axis(lambda v: np.convolve(np.pad(v, r, mode="edge"), k, mode="valid"), 0, m)
    return np.apply_along_axis(lambda v: np.convolve(np.pad(v, r, mode="edge"), k, mode="valid"), 1, m)


def bygg(mapp: str, passning: Passning, mitt_mm: tuple[float, float], radie: float, cell: float, z0: float,
         fri: float = 30.0) -> dict:
    """Rutnätet (cell m) runt modellens mitt: höjder (modellens z i m), marktäckets masker och byggnaderna (utom de
    inom fri m från modellens terräng, dvs. huset självt), i mapp/. Ger beskrivningen (omgivning.json)."""
    from matplotlib.image import imsave
    from shapely.geometry import LineString, Point, box
    from shapely.ops import polygonize, unary_union

    H, tx0, ty0 = _mosaik(mapp)
    osm = json.load(open(os.path.join(mapp, "nedladdat", "osm", "osm.json"), encoding="utf-8"))
    mx, my = mitt_mm[0] / 1000, mitt_mm[1] / 1000

    def till(lat: float, lon: float) -> tuple[float, float]:
        N, E = sweref(lat, lon)
        x, y = passning.till_modell(N, E)
        return float(x) / 1000, float(y) / 1000

    n = int(round(2 * radie / cell)) + 1
    xs = mx - radie + cell * np.arange(n)
    ys = my - radie + cell * np.arange(n)
    X, Y = np.meshgrid(xs, ys)                             # rad = y, kolumn = x
    N, E = passning.till_sweref(X * 1000, Y * 1000)
    lat, lon = wgs84(N, E)
    Z = _hojd(H, tx0, ty0, lat, lon)                       # meter över havet
    ram = box(xs[0], ys[0], xs[-1], ys[-1])
    masker = {k: np.zeros(X.shape) for k, _ in KLASSER}
    byggnader = []
    kust = []
    for el in osm["elements"]:
        t = el.get("tags", {})
        if t.get("natural") == "coastline" and el.get("geometry"):
            kust.append(LineString([till(q["lat"], q["lon"]) for q in el["geometry"]]))
            continue
        if "highway" in t and el.get("geometry"):
            b = VAGBREDD.get(t["highway"]) or STIGBREDD.get(t["highway"])
            if b:
                ls = LineString([till(q["lat"], q["lon"]) for q in el["geometry"]]).buffer(b / 2, cap_style=2)
                _rastrera(masker["vag" if t["highway"] in VAGBREDD else "stig"], ls, xs, ys)
            continue
        if "building" in t:
            for p in _polygoner(el, till):
                if p.is_empty or p.distance(Point(mx, my)) < fri:
                    continue
                vaningar = float(t.get("building:levels", 1) or 1)
                hojd = float(str(t.get("height", 0) or 0).split()[0] or 0) or (2.7 * vaningar + 2.2)
                c = p.centroid
                zmark = float(_hojd(H, tx0, ty0, *wgs84(*passning.till_sweref(np.array([c.x * 1000]),
                                                                               np.array([c.y * 1000]))))[0])
                for q in getattr(p, "geoms", [p]):
                    byggnader.append({"horn": [list(v) for v in q.exterior.coords[:-1]], "hojd": hojd,
                                      "z": zmark - z0, "typ": t.get("building", "yes")})
                _rastrera(masker["byggnad"], p, xs, ys)
            continue
        k = _klass(t)
        if k:
            for p in _polygoner(el, till):
                _rastrera(masker[k], p, xs, ys)
    # land och hav: kustlinjerna och områdets kant delar området i ytor; höjden mitt i ytan avgör
    hav = np.zeros(X.shape)
    if kust:
        linjer = unary_union([lin.intersection(ram) for lin in kust] + [ram.exterior])
        for yta in polygonize(linjer):
            pt = yta.representative_point()
            N1, E1 = passning.till_sweref(np.array([pt.x * 1000]), np.array([pt.y * 1000]))
            if float(_hojd(H, tx0, ty0, *wgs84(N1, E1))[0]) < 1.0:
                _rastrera(hav, yta, xs, ys)
    else:
        hav = (Z < 0.3).astype(float)
    masker["hav"] = hav
    # höjderna följer kusten: havet under havsytan, landet över (avtrappat mot stranden)
    Z = np.where(hav > 0.5, np.minimum(Z, -1.5 - 0.02 * _avstand(hav < 0.5, cell)), np.maximum(Z, 0.25))
    Z = _jamna(Z, 0.7)
    for k in masker:
        masker[k] = np.clip(_jamna(masker[k].astype(float), 0.8), 0.0, 1.0)
    namn = [k for k, _ in KLASSER]
    for i in range(3):
        rgba = np.stack([masker[namn[4 * i + j]] for j in range(4)], axis=-1)[::-1]      # bildens rad 0 = norr
        imsave(os.path.join(mapp, f"marktacke_{i}.png"), rgba)
    (Z - z0).astype(np.float32).tofile(os.path.join(mapp, "hojd.f32"))
    besk = {"x0": float(xs[0]), "y0": float(ys[0]), "cell": cell, "n": n, "z_hav": -z0,
            "kanaler": [namn[4 * i:4 * i + 4] for i in range(3)], "byggnader": byggnader,
            "kalla": "Höjd: AWS Terrain Tiles (Terrarium). Marktäcke, kust, byggnader och vägar: © OpenStreetMap-"
                     "bidragsgivare, ODbL."}
    json.dump(besk, open(os.path.join(mapp, "omgivning.json"), "w", encoding="utf-8"), ensure_ascii=False)
    return besk


def _avstand(land: np.ndarray, cell: float) -> np.ndarray:
    """Ungefärligt avstånd (m) till närmaste landcell (för havsbottnens lutning från stranden)."""
    d = np.where(land, 0.0, 1e9)
    for _ in range(2):
        for ax in (0, 1):
            for rikt in (1, -1):
                v = np.moveaxis(d, ax, 0)
                rng = range(1, v.shape[0]) if rikt > 0 else range(v.shape[0] - 2, -1, -1)
                for i in rng:
                    v[i] = np.minimum(v[i], v[i - rikt] + cell)
    return np.minimum(d, 400.0)
