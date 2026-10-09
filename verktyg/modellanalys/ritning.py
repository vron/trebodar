"""
2D-snittritningar (matplotlib) med exakta koordinater: snittytor fyllda i delens färg, valfri vy bortom
snittet (projicerade, skuggade trianglar, ljusare med avståndet), etiketter och mm-rutnät.
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import PolyCollection
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MPath
from shapely.geometry import MultiPolygon, Polygon, box

from geometri import snitt
from vy import _klipp, polydata


def _polygoner(g):
    if g.is_empty:
        return []
    if isinstance(g, Polygon):
        return [g]
    return [x for x in getattr(g, "geoms", []) if isinstance(x, Polygon)]


def _patch(poly, **kw):
    ringar = [poly.exterior] + list(poly.interiors)
    verts, koder = [], []
    for r in ringar:
        c = np.asarray(r.coords)
        verts.append(c)
        koder += [MPath.MOVETO] + [MPath.LINETO] * (len(c) - 2) + [MPath.CLOSEPOLY]
    return PathPatch(MPath(np.concatenate(verts), koder), **kw)


def _bortom(ax, m, delar, plan, bortom, omrade_poly):
    """Projicera det som syns bortom snittet (upp till |bortom| mm) med målarens algoritm."""
    s = np.sign(bortom)
    titt = s * plan.n
    alla_p, alla_f, alla_d = [], [], []
    for d in delar:
        horn = np.array([[d.bbox[i], d.bbox[j], d.bbox[k]] for i in (0, 3) for j in (1, 4) for k in (2, 5)])
        a = s * plan.avstand(horn)
        if a.max() < 0 or a.min() > abs(bortom):
            continue
        V, F = m.nat(d)
        if not len(F):
            continue
        mesh = polydata(V, F)
        mesh = mesh.clip(normal=titt, origin=plan.o, invert=False)
        if mesh.n_points == 0:
            continue
        mesh = mesh.clip(normal=titt, origin=plan.o + titt * abs(bortom), invert=True)
        if mesh.n_points == 0:
            continue
        mesh = mesh.triangulate()
        f = mesh.faces.reshape(-1, 4)[:, 1:]
        P = mesh.points[f]                               # (n, 3, 3)
        nrm = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0])
        L = np.linalg.norm(nrm, axis=1)
        ok = L > 1e-9
        P, nrm = P[ok], nrm[ok] / L[ok, None]
        syns = nrm @ titt < 0                            # vänd mot betraktaren
        P, nrm = P[syns], nrm[syns]
        if not len(P):
            continue
        djup = ((P.mean(1) - plan.o) @ titt)
        ljus = 0.5 + 0.5 * np.abs(nrm @ titt) * 0.6 + 0.4 * np.clip(nrm @ np.array([0.3, -0.4, 0.85]), 0, 1) * 0.5
        bas = np.array(d.farg[:3])[None, :] * np.clip(ljus, 0, 1.1)[:, None]
        dimma = np.clip(djup / abs(bortom), 0, 1)[:, None] * 0.55
        farg = np.clip(bas * (1 - dimma) + dimma, 0, 1)
        alla_p.append(np.stack([plan.till2d(P[:, i]) for i in range(3)], axis=1))
        alla_f.append(farg)
        alla_d.append(djup)
    if not alla_p:
        return None
    P, F, D = np.concatenate(alla_p), np.concatenate(alla_f), np.concatenate(alla_d)
    if omrade_poly is not None:
        x0, y0, x1, y1 = omrade_poly.bounds
        inom = ~((P[:, :, 0].max(1) < x0) | (P[:, :, 0].min(1) > x1) | (P[:, :, 1].max(1) < y0) | (P[:, :, 1].min(1) > y1))
        P, F, D = P[inom], F[inom], D[inom]
    ordning = np.argsort(-D)
    pc = PolyCollection(P[ordning], facecolors=F[ordning], edgecolors=F[ordning], linewidths=0.25, zorder=1)
    ax.add_collection(pc)
    return P.reshape(-1, 2).min(0).tolist() + P.reshape(-1, 2).max(0).tolist()


def rita_snitt(m, plan, delar, ut, bortom=0.0, omrade=None, etiketter=True, rutnat=None, titel=None,
               dpi=160, bredd=16.0, linjer_for_ytlosa=True):
    """Rita planets snitt genom delarna. Returnerar listan med SnittDel (geometri.snitt)."""
    sd = snitt(m, delar, plan)
    omr = box(omrade[0], omrade[2], omrade[1], omrade[3]) if omrade else None

    # gränser
    bs = [s.yta.bounds for s in sd if not s.yta.is_empty] + \
         [tuple(l.min(0)) + tuple(l.max(0)) for s in sd for l in s.linjer]
    fig, ax = plt.subplots(figsize=(bredd, bredd * 0.7))
    bb = _bortom(ax, m, delar, plan, bortom, omr) if bortom else None
    if bb:
        bs.append(tuple(bb))
    if not bs and not omr:
        plt.close(fig)
        return sd
    bs = np.array(bs)
    x0, y0, x1, y1 = (omrade[0], omrade[2], omrade[1], omrade[3]) if omrade else \
        (bs[:, 0].min(), bs[:, 1].min(), bs[:, 2].max(), bs[:, 3].max())
    marg = 0.03 * max(x1 - x0, y1 - y0, 1)

    for s in sorted(sd, key=lambda s: -s.yta.area):
        farg = s.del_.farg[:3]
        for poly in _polygoner(s.yta):
            ax.add_patch(_patch(poly, facecolor=farg, edgecolor="black", linewidth=0.7, zorder=3))
        if s.yta.is_empty and linjer_for_ytlosa:
            for l in s.linjer:
                ax.plot(l[:, 0], l[:, 1], color=farg, lw=1.2, zorder=3)

    if etiketter:
        vy_area = (x1 - x0) * (y1 - y0)
        for s in sd:
            polys = _polygoner(s.yta if omr is None else s.yta.intersection(omr))
            if not polys:
                continue
            stor = max(polys, key=lambda p: p.area)
            if stor.area < vy_area * 2e-5:
                continue
            rp = stor.representative_point()
            ax.annotate(f"{s.del_.namn} #{s.del_.id}", (rp.x, rp.y), fontsize=6, ha="center", va="center",
                        zorder=5, bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.7))

    ax.set_xlim(x0 - marg, x1 + marg)
    ax.set_ylim(y0 - marg, y1 + marg)
    ax.set_aspect("equal")
    # spegelvänd inte: betraktaren tittar längs bortom-sidan; vänd u-axeln om det behövs
    titt = (np.sign(bortom) if bortom else -1) * plan.n
    if bortom and np.dot(titt, -np.cross(plan.u, plan.v)) < 0:
        ax.invert_xaxis()
    ax.set_xlabel(f"{plan.axlar[0]} (mm)")
    ax.set_ylabel(f"{plan.axlar[1]} (mm)")
    if rutnat:
        from matplotlib.ticker import MultipleLocator
        ax.xaxis.set_major_locator(MultipleLocator(rutnat))
        ax.yaxis.set_major_locator(MultipleLocator(rutnat))
    ax.grid(True, lw=0.3, color="#888888", alpha=0.6, zorder=0)
    ax.tick_params(labelsize=7)
    plt.setp(ax.get_xticklabels(), rotation=90)
    tittriktning = "".join(f"{'+' if c > 0 else '-'}{a}" for a, c in zip("xyz", titt) if abs(c) > 1e-9) \
        if plan.normalaxel != "n" else f"({titt[0]:.2f},{titt[1]:.2f},{titt[2]:.2f})"
    t = f"Snitt {plan.namn}" + (f" – vy bortom {abs(bortom):g} mm, tittar mot {tittriktning}" if bortom else "")
    ax.set_title(f"{titel}\n{t}" if titel else t, fontsize=10)
    fig.tight_layout()
    fig.savefig(ut, dpi=dpi)
    plt.close(fig)
    return sd
