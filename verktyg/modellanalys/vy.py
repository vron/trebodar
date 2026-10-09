"""
3D-bilder (pyvista/VTK, offscreen): valfria vyer, klipp med exakta snittlock, spöken, markeringar,
etiketter och koordinatrutnät. Parallellprojektion som standard.
"""
import re

import numpy as np
import pyvista as pv
import shapely

from geometri import Plan, snitt

pv.global_theme.allow_empty_mesh = True

VYER = {
    "iso": "-x-y+z", "iso-sv": "-x-y+z", "iso-so": "+x-y+z", "iso-nv": "-x+y+z", "iso-no": "+x+y+z",
    "ovan": "+z", "under": "-z", "fram": "-y", "bak": "+y", "vanster": "-x", "hoger": "+x",
}
KANT = "#222222"
MARKERING = "#e8112d"


def riktning(s):
    """Kamerans riktning från målet: 'iso', '+x-y+z', 'ovan' … eller 'az,el' i grader (az från +x mot +y)."""
    s = VYER.get(s.strip(), s.strip())
    if re.fullmatch(r"([+-][xyz])+", s):
        v = np.zeros(3)
        for tecken, a in re.findall(r"([+-])([xyz])", s):
            v["xyz".index(a)] += 1 if tecken == "+" else -1
    else:
        az, el = np.radians([float(t) for t in s.split(",")])
        v = np.array([np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)])
    return v / np.linalg.norm(v)


def tolka_klipp(s):
    """'z<13000' behåll z under 13000, 'x>-3000' behåll x över, 'o=… n=…' behåll sidan mot -n.
    Returnerar (plan, behåll positiv sida?)."""
    m = re.fullmatch(r"\s*([xyz])\s*([<>])\s*(-?[\d.]+)\s*", s)
    if m:
        return Plan.tolka(f"{m.group(1)}={m.group(3)}"), m.group(2) == ">"
    return Plan.tolka(s), False


def polydata(V, F):
    return pv.PolyData(np.asarray(V, float), np.c_[np.full(len(F), 3), F].ravel()) if len(F) else pv.PolyData()


def _klipp(mesh, klipp):
    for plan, pos in klipp:
        if mesh.n_points == 0:
            break
        mesh = mesh.clip(normal=plan.n, origin=plan.o, invert=not pos)
    return mesh


def _hex(f):
    return "#%02x%02x%02x" % tuple(int(round(255 * min(1, max(0, c)))) for c in f[:3])


def _lock(m, delar, klipp, farg_for):
    """Snittlock: exakta snittytor i varje klippplan, trianguliserade och klippta mot övriga plan."""
    ut = []
    for i, (plan, pos) in enumerate(klipp):
        ovriga = [k for j, k in enumerate(klipp) if j != i]
        for s in snitt(m, delar, plan):
            if s.yta.is_empty:
                continue
            tri = shapely.constrained_delaunay_triangles(s.yta)
            P = [np.array(t.exterior.coords)[:3] for t in tri.geoms]
            if not P:
                continue
            P = np.concatenate(P)
            mesh = _klipp(polydata(plan.till3d(P), np.arange(len(P)).reshape(-1, 3)), ovriga)
            if mesh.n_points:
                ut.append((s.del_, mesh, farg_for(s.del_)))
    return ut


def rendera(m, ut, delar, fran=("iso",), klipp=(), spok=(), markera=(), etiketter=(), storlek=(1600, 1200),
            rutnat=False, perspektiv=False, fokus=None, kanter=True, titel=None, zoom=1.0, lock=True):
    """Rendera delarna till PNG. fran: en eller flera vyer (flera ger ett rutnät av delbilder)."""
    fran = list(fran)
    klipptext = ", ".join(k if isinstance(k, str) else k[0].namn for k in klipp)
    klipp = [tolka_klipp(k) if isinstance(k, str) else k for k in klipp]
    spok_id = {d.id for d in spok}
    mark_id = {d.id for d in markera}
    visade = [d for d in delar]
    farg_for = lambda d: MARKERING if d.id in mark_id else _hex(d.farg)

    # slå ihop nät per (färg, opacitet) – få aktörer går fort att rendera
    grupper = {}
    for d in visade:
        V, F = m.nat(d)
        if not len(F):
            continue
        nyckel = (farg_for(d), 0.12 if d.id in spok_id else 1.0)
        grupper.setdefault(nyckel, []).append(polydata(V, F))
    nat = []
    for (f, op), lista in grupper.items():
        mesh = _klipp(pv.merge(lista) if len(lista) > 1 else lista[0], klipp)
        if mesh.n_points:
            nat.append((mesh, f, op))
    lockdelar = _lock(m, [d for d in visade if d.id not in spok_id], klipp, farg_for) if (klipp and lock) else []

    n = len(fran)
    rader, kol = (1, 1) if n == 1 else (1, 2) if n == 2 else ((n + 1) // 2, 2) if n <= 4 else ((n + 2) // 3, 3)
    p = pv.Plotter(off_screen=True, window_size=storlek, shape=(rader, kol), border=False)
    p.set_background("white")
    if fokus:
        b = m.bbox(fokus)
    else:
        bs = [x[0].bounds for x in nat if x[2] == 1.0] or [x[0].bounds for x in nat]
        bs = np.array(bs)
        b = (bs[:, 0].min(), bs[:, 2].min(), bs[:, 4].min(), bs[:, 1].max(), bs[:, 3].max(), bs[:, 5].max())
    granser = (b[0], b[3], b[1], b[4], b[2], b[5])
    for k, vy in enumerate(fran):
        p.subplot(k // kol, k % kol)
        for mesh, f, op in nat:
            p.add_mesh(mesh, color=f, opacity=op, smooth_shading=False, specular=0.1,
                       show_edges=False, lighting=True)
            if kanter and op == 1.0:
                e = mesh.extract_feature_edges(boundary_edges=True, feature_edges=False,
                                               manifold_edges=False, non_manifold_edges=False)
                if e.n_points:
                    p.add_mesh(e, color=KANT, line_width=1, lighting=False)
        for d, mesh, f in lockdelar:
            p.add_mesh(mesh, color=f, lighting=True, ambient=0.25)
            if kanter:
                e = mesh.extract_feature_edges(boundary_edges=True, feature_edges=False,
                                               manifold_edges=False, non_manifold_edges=False)
                if e.n_points:
                    p.add_mesh(e, color="black", line_width=1.6, lighting=False)
        if etiketter:
            pts = np.array([d.tyngdpunkt for d in etiketter])
            p.add_point_labels(pts, [d.namn for d in etiketter], font_size=11, point_size=6,
                               shape_opacity=0.65, always_visible=True, point_color="black")
        r = riktning(vy)
        c = np.array([(b[0] + b[3]) / 2, (b[1] + b[4]) / 2, (b[2] + b[5]) / 2])
        diag = np.linalg.norm(np.array(b[3:]) - np.array(b[:3]))
        upp = (0, 1, 0) if abs(r[2]) > 0.999 else (0, 0, 1)
        p.camera_position = [tuple(c + r * diag * 2), tuple(c), upp]
        p.reset_camera(bounds=granser)
        if not perspektiv:
            # tät inramning: projicera bbox-hörnen på bildens axlar
            p.enable_parallel_projection()
            hoger = np.cross(-r, upp); hoger /= np.linalg.norm(hoger)
            uppv = np.cross(hoger, -r)
            H = np.array([[b[i], b[j], b[kk]] for i in (0, 3) for j in (1, 4) for kk in (2, 5)]) - c
            w2, h2 = np.abs(H @ hoger).max(), np.abs(H @ uppv).max()
            aspekt = (storlek[0] / kol) / (storlek[1] / rader)
            p.camera.parallel_scale = max(h2, w2 / aspekt) * 1.06
        p.camera.zoom(zoom)
        if rutnat:
            p.show_bounds(bounds=granser, grid="back", location="outer", fmt="%.0f", font_size=9,
                          xtitle="x (mm)", ytitle="y (mm)", ztitle="z (mm)", color="#444444")
        p.add_axes(line_width=2, labels_off=False)
        text = f"{vy}" + (f"   klipp: {klipptext}" if klipp else "")
        if titel and k == 0:
            text = f"{titel}\n{text}"
        p.add_text(text, font_size=9, color="black", position="upper_left")
    p.screenshot(str(ut))
    p.close()
    return ut
