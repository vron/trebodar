"""
Enkel renderare för axonometriska bilder till R-00: plana polygoner i 3D, parallellprojektion, djupbuffert, platt
skuggning och konturer där ytorna byter (ID-buffert). Ger en bild (PNG) och projicerade punkter för hänvisningarna.

Kroppar byggs som prismor ur en plan polygon (shapely, med hål) mellan två höjder, eller som lådor med godtycklig
riktning (balkar, takbalkar). Snitt med lodräta plan görs i planet innan kropparna byggs, så att snittytorna blir
kropparnas egna sidor.
"""
import numpy as np
import shapely
from PIL import Image, ImageFilter
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient


# ------------------------------------------------------------------ kamera
class Kamera:
    """Parallellprojektion. az: varifrån man tittar, grader från +x mot +y; el: höjdvinkel över horisonten."""

    def __init__(self, az, el):
        a, e = np.radians(az), np.radians(el)
        self.d = -np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])   # mot scenen
        u = np.cross(self.d, [0.0, 0.0, 1.0])
        self.u = u / np.linalg.norm(u)                                                 # åt höger
        self.v = np.cross(self.u, self.d)                                              # uppåt

    def proj(self, P):
        P = np.asarray(P, float)
        return np.stack([P @ self.u, P @ self.v, P @ self.d], axis=-1)


# ------------------------------------------------------------------ kroppar
class Scen:
    def __init__(self, klipp=None):
        """klipp: (multi)polygon i planet; prismorna klipps till den (lodrätt snitt, snittytorna blir sidor)."""
        self.ytor = []          # (polygoner [(n,3), …] i samma plan, normal, färg, yt-id)
        self.n = 0
        self.klipp = klipp

    def _yta(self, pts, normal, farg):
        """En plan yta, en eller flera konvexa polygoner (trianglar) med samma id, så att konturen bara ritas runt
        hela ytan."""
        self.n += 1
        polys = pts if isinstance(pts, list) and pts and np.ndim(pts[0]) == 2 else [pts]
        self.ytor.append(([np.asarray(q, float) for q in polys], np.asarray(normal, float), farg, self.n))

    def prisma(self, poly, z0, z1, farg, dx=(0.0, 0.0, 0.0)):
        """Prisma ur en (multi)polygon mellan z0 och z1, förskjuten dx (sprängskiss)."""
        dx = np.asarray(dx, float)
        if self.klipp is not None:
            poly = poly.intersection(self.klipp)
        for p in getattr(poly, "geoms", [poly]):
            if p.geom_type != "Polygon":
                continue
            if p.is_empty or p.area < 1.0:
                continue
            p = orient(p.simplify(0), 1.0)
            tris = _trianglar(p)
            for z, nz in ((z1, 1.0), (z0, -1.0)):
                self._yta([[(x + dx[0], y + dx[1], z + dx[2]) for x, y in (t if nz > 0 else t[::-1])] for t in tris],
                          (0, 0, nz), farg)
            for ring in [p.exterior] + list(p.interiors):
                c = list(ring.coords)
                for (x0, y0), (x1, y1) in zip(c[:-1], c[1:]):
                    L = np.hypot(x1 - x0, y1 - y0)
                    if L < 1e-6:
                        continue
                    nrm = (( y1 - y0) / L, -(x1 - x0) / L, 0.0)
                    q = [(x0, y0, z0), (x1, y1, z0), (x1, y1, z1), (x0, y0, z1)]
                    self._yta([(a + dx[0], b + dx[1], z + dx[2]) for a, b, z in q], nrm, farg)

    def lada(self, p0, p1, b, h, farg, upp=(0.0, 0.0, 1.0), dx=(0.0, 0.0, 0.0)):
        """Låda längs linjen p0–p1, bredd b (vinkelrätt i horisontalplanet), höjd h (åt 'upp' från linjen, som
        balkens underkant). Takbalkar, stål- och limträbalkar."""
        p0, p1, dx = np.asarray(p0, float) + dx, np.asarray(p1, float) + dx, np.asarray(dx, float)
        t = p1 - p0
        t = t / np.linalg.norm(t)
        s = np.cross(t, upp)
        if np.linalg.norm(s) < 1e-9:
            s = np.array([1.0, 0.0, 0.0])
        s = s / np.linalg.norm(s)
        n = np.cross(s, t)
        n = n / np.linalg.norm(n)
        P = {}
        for i, a in enumerate((p0, p1)):
            for j, sb in enumerate((-b / 2, b / 2)):
                for k, nh in enumerate((0.0, h)):
                    P[i, j, k] = a + s * sb + n * nh
        sid = [((0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1), -s), ((0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0), s),
               ((0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0), -t), ((1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1), t),
               ((0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0), -n), ((0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1), n)]
        for *q, nrm in sid:
            self._yta([P[k] for k in q], nrm, farg)

    def stang(self, x0, x1, y0, y1, z0, z1, farg, dx=(0.0, 0.0, 0.0)):
        """Rätblock (axelriktat)."""
        self.prisma(shapely.box(x0, y0, x1, y1), z0, z1, farg, dx)


def _trianglar(p):
    """Trianglar som täcker polygonen (med hål)."""
    if len(p.exterior.coords) == 5 and not p.interiors and abs(p.area - p.minimum_rotated_rectangle.area) < 1e-6:
        c = list(p.exterior.coords)[:4]
        return [c[:3], [c[0], c[2], c[3]]]
    ut = []
    for t in shapely.constrained_delaunay_triangles(p).geoms:
        c = list(orient(t, 1.0).exterior.coords)[:3]
        ut.append(c)
    return ut


# ------------------------------------------------------------------ rendering
LJUS = np.array([-0.35, -0.55, 0.76])
LJUS = LJUS / np.linalg.norm(LJUS)


def _hex(f):
    f = f.lstrip("#")
    return np.array([int(f[i:i + 2], 16) for i in (0, 2, 4)], float)


def rendera(scen, kam, px_per_mm, ram=None, ss=2, kantfarg="#262626", bak="#ffffff", kantbredd=1):
    """Rendera scenen. px_per_mm: bildpunkter per modell-mm i slutbilden; ram: (umin, vmin, umax, vmax) i modellens
    skärmkoordinater (annars scenens utbredning). Returnerar (bild, avbildning) där avbildning(P) ger bildpunkter."""
    ytor = [([kam.proj(q) for q in pp], n, f, i) for pp, n, f, i in scen.ytor if np.dot(n, kam.d) < 1e-9]
    if ram is None:
        allt = np.vstack([q[:, :2] for pp, *_ in ytor for q in pp])
        ram = (*allt.min(0), *allt.max(0))
    umin, vmin, umax, vmax = ram
    k = px_per_mm * ss
    W, H = int(np.ceil((umax - umin) * k)) + 2, int(np.ceil((vmax - vmin) * k)) + 2
    djup = np.full((H, W), np.inf, np.float32)
    ids = np.zeros((H, W), np.int32)
    farg = np.empty((H, W, 3), np.uint8)
    farg[:] = _hex(bak)
    for pp, n, f, idn in ytor:
        sken = 0.62 + 0.38 * max(0.0, float(np.dot(n, LJUS))) if n[2] < 0.99 else 1.0
        c = np.clip(_hex(f) * sken, 0, 255).astype(np.uint8)
        for q in pp:
            x = (q[:, 0] - umin) * k
            y = (vmax - q[:, 1]) * k
            z = q[:, 2]
            for a in range(1, len(q) - 1):        # solfjäder (delytorna är konvexa: trianglar och fyrhörningar)
                _triangel(djup, ids, farg, (x[0], x[a], x[a + 1]), (y[0], y[a], y[a + 1]),
                          (z[0], z[a], z[a + 1]), c, idn)
    # konturer där yt-id byter
    kant = np.zeros((H, W), bool)
    kant[:, :-1] |= ids[:, :-1] != ids[:, 1:]
    kant[:-1, :] |= ids[:-1, :] != ids[1:, :]
    for _ in range(kantbredd - 1):                # bredare linjer: väx kanten en bildpunkt åt höger och nedåt
        kant[:, 1:] |= kant[:, :-1]
        kant[1:, :] |= kant[:-1, :]
    farg[kant] = _hex(kantfarg)
    bild = Image.fromarray(farg)
    if ss > 1:
        bild = bild.resize((W // ss, H // ss), Image.LANCZOS)

    def avbildning(P):
        Q = kam.proj(np.atleast_2d(P))
        return np.stack([(Q[:, 0] - umin) * px_per_mm, (vmax - Q[:, 1]) * px_per_mm], -1)

    return bild, avbildning, ram


def _triangel(djup, ids, farg, xs, ys, zs, c, idn):
    x0, x1 = int(max(np.floor(min(xs)), 0)), int(min(np.ceil(max(xs)), djup.shape[1] - 1))
    y0, y1 = int(max(np.floor(min(ys)), 0)), int(min(np.ceil(max(ys)), djup.shape[0] - 1))
    if x1 < x0 or y1 < y0:
        return
    (ax, bx, cx), (ay, by, cy) = xs, ys
    den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
    if abs(den) < 1e-12:
        return
    X, Y = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    w0 = ((by - cy) * (X - cx) + (cx - bx) * (Y - cy)) / den
    w1 = ((cy - ay) * (X - cx) + (ax - cx) * (Y - cy)) / den
    w2 = 1.0 - w0 - w1
    e = -1e-9
    inne = (w0 >= e) & (w1 >= e) & (w2 >= e)
    if not inne.any():
        return
    Z = (w0 * zs[0] + w1 * zs[1] + w2 * zs[2]).astype(np.float32)
    D = djup[y0:y1 + 1, x0:x1 + 1]
    m = inne & (Z < D - 0.05)
    D[m] = Z[m]
    ids[y0:y1 + 1, x0:x1 + 1][m] = idn
    farg[y0:y1 + 1, x0:x1 + 1][m] = c
