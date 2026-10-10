"""Figurer till K-06 i samma stil som K-05."""
import math

import numpy as np
import matplotlib

matplotlib.use("svg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Polygon, Rectangle, Circle  # noqa: E402
from matplotlib.tri import Triangulation  # noqa: E402
from shapely.geometry import LineString, Polygon as SPoly, Point  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

import indata as I
import figurer as F05            # K-05
from figurer import INK, BETONG, LECA, ISOL, STAL, FRI, HALO, sv  # noqa: E402

G = I.G05
MARKF = "#efe6d2"
EPSF = "#f3f6fa"
EPS2 = "#dde6f0"
JORD = "#d9cbb0"
DRAN = "#c7c2b8"
BLA = "#2c4a6e"
ROD = "#b5463a"


def _vaggar(ax, poly):
    for w in G["vagg"]:
        k, h_, L = F05.vaggband(w, G["E"] + I.KI, G["vagg"])
        for g, fc in ((h_, LECA), (k, ISOL)):
            gg = g.intersection(poly.buffer(1))
            for p in getattr(gg, "geoms", [gg]):
                if p.area > 1:
                    ax.add_patch(Polygon(list(p.exterior.coords), closed=True, fc=fc, ec=INK if fc == LECA else "none",
                                         lw=0.3, zorder=4))


def _etiketter(ax, poly):
    cx, cy = poly.centroid.coords[0]
    for i, w in enumerate(G["vagg"], 1):
        ax_, c, a, b = w[:4]
        m = (a + b) / 2
        if ax_ == "h":
            x, y, rot = m, c + (330 if c < cy else -330), 0
        else:
            x, y, rot = c + (330 if c < cx else -330), m, 90
        if b - a < 900:
            rot = 0
        x, y = {"V13": (8560, 560), "V17": (8730, 960), "V8": (9340, 1600), "V10": (4820, 560),
                "V11": (6210, 560), "V12": (7695, 560)}.get(f"V{i}", (x, y))
        ax.text(x, y, f"V{i}", fontsize=5.6, ha="center", va="center", color="#555", style="italic", rotation=rot,
                zorder=9, path_effects=HALO)


def rita_kallare(path, R, poly):
    """Källaren: väggar, fyllning mot väggarna och stolpar för de två systemen."""
    fig, ax = plt.subplots(figsize=(6.0, 6.9))
    ax.add_patch(Polygon(list(poly.exterior.coords), closed=True, fc=BETONG, ec=INK, lw=0.7, zorder=1))
    mk = SPoly(G["mark"]).buffer(I.KI, join_style=2).difference(poly)
    for g in getattr(mk, "geoms", [mk]):
        ax.add_patch(Polygon(list(g.exterior.coords), closed=True, fc=MARKF, ec=INK, lw=0.5, hatch="..", zorder=1))
    ax.text(2100, 12900, "plattan på mark\n(plan 1, K-05)", ha="center", fontsize=6.5, zorder=9, path_effects=HALO)
    _vaggar(ax, poly)
    _etiketter(ax, poly)
    for i, (x, y) in enumerate(G["pelare"], 1):
        ax.add_patch(Rectangle((x - 60, y - 60), 120, 120, fc=STAL, ec="white", lw=0.3, zorder=8))
        ax.text(x + 120, y + 100, f"P{i}", fontsize=5.4, zorder=9, path_effects=HALO)
    # fyllning
    for v in R["vaggar"]:
        if max(v["fyll"]) <= 0:
            continue
        ax_, c, a, b = v["ax"], v["c"], v["a"], v["b"]
        # utsidan: på den sida som ligger utanför källaren
        if ax_ == "h":
            s = 1 if not poly.contains(Point((a + b) / 2, c + 400)) else -1
            p0, p1 = (a, c + s * 260), (b, c + s * 260)
            tx, ty, rot = (a + b) / 2, c + s * 520, 0
        else:
            s = 1 if not poly.contains(Point(c + 400, (a + b) / 2)) else -1
            p0, p1 = (c + s * 260, a), (c + s * 260, b)
            tx, ty, rot = c + s * 560, (a + b) / 2, 90
        ax.plot(*zip(p0, p1), color="#8a6d3b", lw=2.2, solid_capstyle="butt", zorder=5)
        h0, h1 = v["fyll"]
        nd = lambda h: 1 if abs(h - round(h, 1)) < 1e-9 else 2
        txt = sv(h0, nd(h0)) + " m" if abs(h0 - h1) < 1e-6 else f"{sv(h0, nd(h0))} → {sv(h1, nd(h1))} m"
        ax.text(tx, ty, txt, ha="center", va="center", fontsize=6.0, rotation=rot, color="#6b5320", zorder=9,
                path_effects=HALO)
    # stolpar
    for sys_, mk_, col, off in (("A", "o", BLA, -260), ("B", "^", ROD, 260)):
        for v in R["vaggar"]:
            e = v[sys_].get("1")
            if not e or not e.get("stolpar"):
                continue
            ax_, c, a, b = v["ax"], v["c"], v["a"], v["b"]
            n = e["stolpar"]
            for k in range(n):
                t = a + (b - a) * (k + 1) / (n + 1)
                if ax_ == "h":
                    x, y = t + off, c
                else:
                    x, y = c, t + off
                ax.plot([x], [y], marker=mk_, ms=5.5, color=col, mec="white", mew=0.4, zorder=10, ls="none")
    ax.text(6900, -1000, "fasad med öppningar: fyllning under fönstren", ha="center", fontsize=6.5)
    items = [(plt.Line2D([0], [0], color="#8a6d3b", lw=2.2), "fyllning mot väggen (höjd över bottenplattan)"),
             (plt.Line2D([0], [0], marker="o", ls="none", color=BLA, ms=5), "stålstolpe, system A (Leca)"),
             (plt.Line2D([0], [0], marker="^", ls="none", color=ROD, ms=5), "stålstolpe, system B (Benders)"),
             (Rectangle((0, 0), 1, 1, fc=STAL, ec="none"), "rör P1–P19 (K-05)")]
    ax.legend([i for i, _ in items], [t for _, t in items], loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=2,
              frameon=False, fontsize=6.4, handlelength=1.8)
    ax.set_xlim(-700, 14500); ax.set_ylim(-1200, 16300)
    ax.set_aspect("equal"); ax.axis("off")
    fig.savefig(path, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


def rita_bottenplatta(path, R, poly, kant, inre, plint_b):
    """Armeringsritning för bottenplattan (utförande L300)."""
    fig, ax = plt.subplots(figsize=(6.0, 6.9))
    ax.add_patch(Polygon(list(poly.exterior.coords), closed=True, fc=EPSF, ec=INK, lw=0.8, zorder=1))
    for g, hatch in ((kant, "////"), (inre, "////")):
        for p in getattr(g, "geoms", [g]):
            ax.add_patch(Polygon(list(p.exterior.coords), closed=True, fc="#d7d3cb", ec=INK, lw=0.4, hatch=hatch,
                                 zorder=2))
            for h in p.interiors:
                ax.add_patch(Polygon(list(h.coords), closed=True, fc=EPSF, ec=INK, lw=0.4, zorder=2))
    for i, ((x, y), b) in enumerate(zip(G["pelare"], plint_b), 1):
        ax.add_patch(Rectangle((x - b / 2, y - b / 2), b, b, fc="#e2bdb3", ec=INK, lw=0.5, zorder=3))
        ax.add_patch(Rectangle((x - 100, y - 100), 200, 200, fc=STAL, ec="none", zorder=4))
        ax.text(x, y - b / 2 - 90, f"P{i} {sv(b)}", ha="center", va="top", fontsize=5.3, zorder=9, path_effects=HALO)
    # diagonaljärn vid inåtgående hörn (överkant)
    for b, bis in F05.inatgaende_horn(list(poly.exterior.coords)[:-1]):
        t = np.array([-bis[1], bis[0]])
        for off in (150, 250):
            c = b + bis * off
            p0, p1 = c - t * 600, c + t * 600
            ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color=FRI, lw=0.9, zorder=8, solid_capstyle="butt")
    # S300 under kantbalken (L300)
    from shapely.geometry import box as _box
    for x0, y0, x1, y1 in I.S300_ZON["L300"]:
        z = _box(x0, y0, x1, y1).intersection(kant)
        for g in getattr(z, "geoms", [z]):
            if g.area > 1:
                ax.add_patch(Polygon(list(g.exterior.coords), closed=True, fc="none", ec=BLA, lw=1.1, hatch="xxxx",
                                     zorder=5))
                cx, cy = g.centroid.coords[0]
    # fickor för stålstolparna, system A (stolpens mitt 400 mm innanför Lecans ytterliv)
    for v in R["vaggar"]:
        e = v["A"].get("1")
        if not e or not e.get("stolpar"):
            continue
        w = next(w for i, w in enumerate(G["vagg"], 1) if f"V{i}" == v["namn"])
        ax_, c, a, b = w[:4]
        n = e["stolpar"]
        for k in range(n):
            t = a + (b - a) * (k + 1) / (n + 1)
            x, y = (t, c) if ax_ == "h" else (c, t)
            nrm = np.array([0.0, 1.0]) if ax_ == "h" else np.array([1.0, 0.0])
            if not poly.contains(Point(x + nrm[0] * 300, y + nrm[1] * 300)):
                nrm = -nrm
            d = 400 - poly.exterior.distance(Point(x, y))
            cx, cy = x + nrm[0] * d, y + nrm[1] * d
            wx, wy = (200, 100) if ax_ == "h" else (100, 200)
            ax.add_patch(Rectangle((cx - wx / 2, cy - wy / 2), wx, wy, fc=BLA, ec="none", zorder=6))
            ax.text(cx + nrm[0] * 380, cy + nrm[1] * 380, f"ficka ({v['namn']})", ha="center", va="center", fontsize=5.0,
                    color=BLA, zorder=9, path_effects=HALO, rotation=0 if ax_ == "h" else 90)
    items = [(Rectangle((0, 0), 1, 1, fc="#d7d3cb", ec=INK, lw=0.4, hatch="////"),
              "kantbalk och balk under innervägg, 450 bred"),
             (Rectangle((0, 0), 1, 1, fc=BLA, ec="none"), "ficka för stålstolpe, system A (figur 7)"),
             (Rectangle((0, 0), 1, 1, fc="none", ec=BLA, lw=1.1, hatch="xxxx"), "S300 under kantbalken, 1,0 m från hörnet"),
             (Rectangle((0, 0), 1, 1, fc="#e2bdb3", ec=INK, lw=0.5), "plint under rör (sida i mm)"),
             (plt.Line2D([0], [0], color=FRI, lw=0.9), "2 Ø10, L = 1,2 m, överkant, inåtgående hörn"),
             (Rectangle((0, 0), 1, 1, fc=EPSF, ec=INK, lw=0.5), "platta 100 mm på cellplast")]
    ax.legend([i for i, _ in items], [t for _, t in items], loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=2,
              frameon=False, fontsize=6.4, handlelength=1.8, handleheight=1.0)
    ax.set_xlim(-400, 14300); ax.set_ylim(-500, 12900)
    ax.set_aspect("equal"); ax.axis("off")
    fig.savefig(path, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


def rita_tryck(path, P_xy, tri, p, w, poly, tjock):
    """Cellplastens tryck (brottgräns, omhyllande) och långtidssättning (kvasipermanent)."""
    fig, axs = plt.subplots(1, 2, figsize=(6.4, 3.6))
    T = Triangulation(P_xy[:, 0], P_xy[:, 1], tri)
    for ax, z, lev, cm, titel in ((axs[0], p, np.arange(0, 85, 5), "YlOrBr", "Tryck mot cellplasten, brottgräns (kPa)"),
                                  (axs[1], w, np.arange(0.6, 1.75, 0.1), "Blues", "Sättning, långtid (mm)")):
        cs = ax.tricontourf(T, z, levels=lev, cmap=cm, extend="max")
        ax.add_patch(Polygon(list(poly.exterior.coords), closed=True, fc="none", ec=INK, lw=0.6))
        for g in getattr(tjock, "geoms", [tjock]):
            ax.add_patch(Polygon(list(g.exterior.coords), closed=True, fc="none", ec="#555", lw=0.25))
            for h in g.interiors:
                ax.add_patch(Polygon(list(h.coords), closed=True, fc="none", ec="#555", lw=0.25))
        cb = fig.colorbar(cs, ax=ax, orientation="horizontal", fraction=0.05, pad=0.02, aspect=30)
        cb.ax.tick_params(labelsize=6)
        cb.set_label(titel, fontsize=6.5)
        ax.set_aspect("equal"); ax.axis("off")
        ax.set_xlim(-300, 14100); ax.set_ylim(-300, 12900)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


def rita_kapacitet(path, kurvor, vaggar_):
    """λ mot vägglängd vid 2,0 m fyllning för systemen och armeringen, med väggarna markerade."""
    fig, ax = plt.subplots(figsize=(5.6, 2.7))
    stil = {("A", 1): (BLA, "-", "A: Sikksakk i varje fog"), ("A", 2): (BLA, "--", "A: Sikksakk i varannan fog"),
            ("B", 1): (ROD, "-", "B: bistål i varje skift"), ("B", 2): (ROD, "--", "B: bistål i vartannat skift")}
    for (s, var), (L, lam) in kurvor.items():
        c, ls, lab = stil[(s, var)]
        ax.plot(L, lam, color=c, ls=ls, lw=1.0, label=lab)
    ax.axhline(1.0, color=INK, lw=0.6)
    ax.axvline(6.0, color="#888", lw=0.6, ls=":")
    ax.text(6.05, 2.6, "Leca tabell 7.7a:\n6,0 m (varannan fog)", fontsize=6, va="top")
    for n, L in vaggar_:
        ax.plot([L, L], [0, 0.12], color="#6b5320", lw=0.8)
        ax.text(L, 0.14, n, fontsize=5.5, ha="center", rotation=90, va="bottom", color="#6b5320")
    ax.set_xlim(1, 8); ax.set_ylim(0, 3)
    ax.set_xlabel("Vägglängd mellan hörn eller stolpar (m)", fontsize=7)
    ax.set_ylabel("Lastfaktor λ", fontsize=7)
    ax.tick_params(labelsize=6.5)
    ax.legend(fontsize=6.2, frameon=False, ncol=2, loc="upper right")
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


# ------------------------------------------------------------------ detalj: vägg mot bottenplatta och bjälklag
def _rekt(ax, x0, y0, w, h, fc, ec=INK, lw=0.4, hatch=None, z=2):
    ax.add_patch(Rectangle((x0, y0), w, h, fc=fc, ec=ec, lw=lw, hatch=hatch, zorder=z))


def _not(ax, xy, txt, xyt, ha="left"):
    ax.annotate(txt, xy, xyt, fontsize=5.6, ha=ha, va="center",
                arrowprops=dict(arrowstyle="-", lw=0.35, color=INK, shrinkA=0, shrinkB=0), zorder=12)


def rita_detalj(path, sys_, h_balk=200.0, t_eps=200.0):
    """Sektion genom yttervägg mot jord: bottenplatta på L-element, vägg, bjälklag. Mått i mm, y = 0 överkant platta.
    Väggen visas med ett avbrott mitt på höjden."""
    fig, ax = plt.subplots(figsize=(6.3, 4.9))
    t_fot, hp = I.T_FOT, I.H_PLATTA
    yb = -h_balk
    ybot = yb - t_fot
    # berg och makadam
    _rekt(ax, -1500, ybot - 380, 3200, 230, "#cfcac2", hatch="xx", z=0)
    _rekt(ax, -1500, ybot - 150, 3200, 150, DRAN, z=0)
    # cellplast under plattan (två skikt), L-elementets fot och ben
    _rekt(ax, 450, -hp - t_eps, 1250, t_eps / 2, EPSF)
    _rekt(ax, 450, -hp - t_eps / 2, 1250, t_eps / 2, EPSF)
    ax.plot([450, 1700], [-hp - t_eps / 2] * 2, color=BLA, lw=0.8, ls=(0, (4, 2)), zorder=3)
    _rekt(ax, -100, ybot, 550, t_fot, EPS2)
    _rekt(ax, -100, yb, 100, h_balk, EPS2)
    ax.add_patch(Polygon([(0, yb), (450, yb), (450, -hp), (1700, -hp), (1700, 0), (350, 0), (350, -50), (0, -50)],
                         closed=True, fc=BETONG, ec=INK, lw=0.5, zorder=2))
    for x in (60, 280):
        ax.add_patch(Circle((x, yb + 45), 9, fc=INK, zorder=5))
        ax.add_patch(Circle((x, -50 - 35), 9, fc=INK, zorder=5))
    ax.plot([380, 1700], [-hp + 33] * 2, color=INK, lw=0.5, zorder=5)
    ax.plot([380, 1700], [-28] * 2, color=INK, lw=0.5, zorder=5)
    # vägg med avbrott
    for y0, h in ((-50, 760), (1310, 640)):
        _rekt(ax, 0, y0, 100, h, LECA, z=3)
        _rekt(ax, 100, y0, 150, h, ISOL, z=3)
        _rekt(ax, 250, y0, 100, h, LECA, z=3)
        for yy in np.arange(y0 + 205, y0 + h - 5, 207):
            ax.plot([0, 350], [yy, yy], color="#7d7d7d", lw=0.3, zorder=4)
            if sys_ == "A":
                xs = np.linspace(62, 288, 7)
                ax.plot(xs, yy + np.where(np.arange(7) % 2, 7, -7), color=FRI, lw=0.7, zorder=5)
            else:
                ax.add_patch(Circle((50, yy), 9, fc=FRI, zorder=5)); ax.add_patch(Circle((300, yy), 9, fc=FRI, zorder=5))
    for yy in (720, 1300):
        ax.plot([-80, 430], [yy - 30, yy + 30], color=INK, lw=0.5, zorder=6)
    yt = 1950
    _rekt(ax, 0, yt, 350, 200, LECA, z=3)
    _rekt(ax, 80, yt + 40, 190, 160, BETONG, z=4)
    for x in (130, 220):
        ax.add_patch(Circle((x, yt + 90), 9, fc=INK, zorder=5))
    _rekt(ax, 30, yt + 200, 1670, 150, BETONG, z=3)
    ax.plot([175, 175, 500], [yt + 70, yt + 310, yt + 310], color=INK, lw=0.8, zorder=6)
    ax.plot([352, 352], [-50, yt + 200], color="#888", lw=1.0, zorder=4)
    if sys_ == "A":
        ax.plot([-6, -6], [-50, yt + 150], color=INK, lw=0.7, zorder=4)
        ax.plot([-28, -28], [ybot - 40, 1950], color=INK, lw=0.7, ls=(0, (1.2, 1.0)), zorder=4)
        xf = -40
        utv = [("Weber Grå Slemming, 2 strykningar", (-6, 1500)),
               ("Platon grunnmursplate, knopparna mot väggen", (-28, 1700))]
    else:
        _rekt(ax, -106, -50, 100, 1960, "#e7e1c6", hatch="||", z=3)
        ax.plot([-6, -6], [-50, yt + 150], color=INK, lw=0.7, zorder=4)
        xf = -110
        utv = [("Weber grundningsbruk KC, heltäckande", (-6, 1550)),
               ("Isodrän (isolerande dränskiva) med geotextil", (-56, 1750))]
    ax.add_patch(Polygon([(-1500, ybot), (xf, ybot), (xf, 1700), (-1500, 1760)], closed=True,
                         fc="#ece3cf", ec="none", zorder=1))
    ax.plot([-1500, xf], [1760, 1700], color=INK, lw=0.7, zorder=4)
    ax.add_patch(Circle((-330, ybot + 70), 55, fc="white", ec=INK, lw=0.6, zorder=5))
    ax.plot([-1500, xf], [ybot - 4] * 2, color="#666", lw=0.5, ls=(0, (3, 1.5)), zorder=4)
    # etiketter: insida till höger, utsida till vänster
    hoger = [("bjälklag 150 (K-05)", (900, yt + 275)),
             (("Leca Iso U-blokk" if sys_ == "A" else "LECA balkblock") + " gjuts med bjälklaget, 2 Ø10", (220, yt + 120)),
             ("förankring Ø10 s600 från bjälklaget", (340, yt + 310)),
             (("Leca Isoblokk 35, weber M5" if sys_ == "A" else "LECA Isoblock 350 PUR, Flexoheft"), (300, 1600)),
             (("Sikksakk-armering i varje liggfog" if sys_ == "A" else "Bi 40 ob inne och Bi 37 rf ute, varje skift"),
              (175, 1310 + 205 + 207)),
             ("puts eller slamning på insidan, ingen ångspärr", (352, 1000)),
             ("urtag 50: plattans kant håller väggens fot", (350, -25)),
             ("glidskikt (papp) under första skiftet", (175, -50)),
             (f"kantbalk 450 × {sv(h_balk)}: 2 Ø10 uk + 2 Ø10 ök", (280, yb + 45)),
             ("platta 100: Ø6 s150 i över- och underkant", (1200, -hp + 33)),
             (f"L-element L{sv(h_balk + t_fot)}: fot 100 mm S200 (S300 vid hörnet V2/V20)", (225, ybot + 50)),
             (f"cellplast {sv(t_eps)} mm S100, plastfolie mellan skikten", (1200, -hp - t_eps * 0.5))]
    def kolumn(lst, x, ha):
        lst = sorted(lst, key=lambda t: -t[1][1])
        ys = np.linspace(yt + 380, ybot - 250, len(lst))
        for (txt, xy), y in zip(lst, ys):
            ax.annotate(txt, xy, (x, y), fontsize=6.0, ha=ha, va="center",
                        arrowprops=dict(arrowstyle="-", lw=0.35, color="#444", shrinkA=1, shrinkB=0), zorder=12)
    kolumn(hoger, 1900, "left")
    vanster = [("fall från huset ≥ 1:50 över 3 m", (-700, 1730))] + utv + [
        ("dränerande fyllning, fiberduk mot jorden", (-800, 800)),
        ("dränledning, vattengång under plattans cellplast", (-330, ybot + 70)),
        ("makadam på sprängt berg", (-900, ybot - 75))]
    kolumn(vanster, -1600, "right")
    ax.set_xlim(-3700, 4700); ax.set_ylim(ybot - 420, yt + 520)
    ax.set_aspect("equal"); ax.axis("off")
    fig.savefig(path, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)




def rita_lokala(path, h_balk=200.0, t_eps=200.0):
    """Lokala detaljer (L300) i skala 1 tum = 550 mm, med numrerade hänvisningar:
    (a) plint under rör, (b) stålstolpe topp, (c) stålstolpe fot, (d) balk under innervägg. Mått i mm."""
    SK = 550.0                                         # mm per tum
    W, Hf = 6.9, 5.45
    fig = plt.figure(figsize=(W, Hf))
    hp, tf = I.H_PLATTA, I.T_FOT
    yb, ybot = -h_balk, -h_balk - tf
    H = 2100.0

    def panel(x_in, y_in, xl, yl):
        """Axlar med nedre vänstra hörnet i (x_in, y_in) tum och gränserna xl, yl i mm."""
        w, h = (xl[1] - xl[0]) / SK, (yl[1] - yl[0]) / SK
        ax = fig.add_axes([x_in / W, y_in / Hf, w / W, h / Hf])
        ax.set_xlim(*xl); ax.set_ylim(*yl); ax.set_aspect("equal"); ax.axis("off")
        return ax

    def R(ax, x0, y0, w, h, fc, ec=INK, lw=0.4, hatch=None, z=2, ls="-"):
        ax.add_patch(Rectangle((x0, y0), w, h, fc=fc, ec=ec, lw=lw, hatch=hatch, zorder=z, ls=ls))

    def P(ax, pts, fc, z=2):
        ax.add_patch(Polygon(pts, closed=True, fc=fc, ec=INK, lw=0.5, zorder=z))

    def dot(ax, x, y, r=8):
        ax.add_patch(Circle((x, y), r, fc=INK, zorder=8))

    def stud(ax, x, y0, y1):
        ax.plot([x, x], [y0, y1], color=STAL, lw=1.6, zorder=6)
        ax.plot([x - 12, x + 12], [y1, y1], color=STAL, lw=2.4, zorder=6)

    def brott(ax, x0, x1, y):
        ax.plot([x0, x1], [y - 25, y + 25], color=INK, lw=0.6, zorder=9)

    def matt(ax, x0, x1, y, txt):
        ax.annotate("", (x0, y), (x1, y), arrowprops=dict(arrowstyle="<->", lw=0.45, color=INK, shrinkA=0, shrinkB=0))
        ax.text((x0 + x1) / 2, y - 20, txt, fontsize=6.0, ha="center", va="top")

    def grund(ax, x0, x1, a, b):
        R(ax, x0, ybot, x1 - x0, -hp - ybot, EPSF, z=1)
        R(ax, a, ybot, b - a, tf, EPS2, z=1)
        P(ax, [(x0, -hp), (a, -hp), (a, yb), (b, yb), (b, -hp), (x1, -hp), (x1, 0), (x0, 0)], BETONG)
        ax.plot([x0, x1], [-28, -28], color=INK, lw=0.55, zorder=5)
        ax.plot([x0, x1], [-hp + 33, -hp + 33], color=INK, lw=0.55, zorder=5)

    def nummer(ax, lst):
        for k, (txt, (px, py), (lx, ly)) in enumerate(lst, 1):
            ax.annotate(str(k), (px, py), (lx, ly), fontsize=5.8, ha="center", va="center", zorder=15,
                        bbox=dict(boxstyle="circle,pad=0.18", fc="white", ec=INK, lw=0.45),
                        arrowprops=dict(arrowstyle="-", lw=0.4, color="#333", shrinkA=0, shrinkB=0))

    def lista(x_in, y_in, titel, lst):
        fig.text(x_in / W, y_in / Hf, titel, fontsize=7.2, weight="bold", ha="left", va="bottom")
        for k, (txt, _, _) in enumerate(lst, 1):
            fig.text(x_in / W, (y_in - 0.06 - 0.115 * k) / Hf, f"{k}   {txt}", fontsize=6.2, ha="left", va="bottom")

    # ---------------------------------------------------------------- a) plint under rör
    xl, yl = (-900, 900), (-400, 520)
    ax = panel(0.05, 3.75, xl, yl)
    b_ = 1000.0
    grund(ax, -850, 850, -b_ / 2, b_ / 2)
    for x in np.arange(-450, 451, 150):
        dot(ax, x, yb + 34, 7)
    ax.plot([-470, 470], [yb + 42, yb + 42], color=INK, lw=0.55, zorder=5)
    R(ax, -100, -15, 200, 15, STAL, z=6)
    for x in (-60, 60):
        stud(ax, x, -15, -90)
    R(ax, -40, 0, 80, 500, "#9aa0a8", z=6)
    brott(ax, -90, 90, 450)
    matt(ax, -b_ / 2, b_ / 2, ybot - 50, "b = 600–1 200 (figur 6)")
    la = [("rör VKR 80×80×4 (K-05), svetsas på plåten", (40, 350), (300, 420)),
          ("fotplåt 200 × 200 × 15 S355, gjuts in i plinten", (-100, -8), (-420, 300)),
          ("4 svetsbultar Ø13, L = 75 mm", (-60, -70), (-420, 160)),
          ("platta 100: Ø6 s150 i över- och underkant", (-700, -28), (-700, 200)),
          ("plint: Ø8 s150 i underkant, båda riktningarna", (300, yb + 34), (650, 160)),
          (f"cellplast S200, {sv(tf)} mm under plinten", (200, yb - 50), (650, -330)),
          (f"cellplast S100, {sv(t_eps)} mm i två skikt", (-700, -200), (-700, -330))]
    nummer(ax, la)
    lista(0.1, 3.6, "a) Plint under rör", la)

    # ---------------------------------------------------------------- d) balk under innervägg
    xl, yl = (-800, 800), (-400, 470)
    ax = panel(0.25, 0.95, xl, yl)
    grund(ax, -750, 750, -225, 225)
    for x in (-160, 160):
        dot(ax, x, yb + 41); dot(ax, x, -36)
    ax.plot([-175, -175, 175, 175], [-25, yb + 30, yb + 30, -25], color=INK, lw=0.7, zorder=6)
    R(ax, -175, 0, 100, 450, LECA, z=3); R(ax, -75, 0, 150, 450, ISOL, z=3); R(ax, 75, 0, 100, 450, LECA, z=3)
    brott(ax, -230, 230, 400)
    matt(ax, -225, 225, ybot - 50, "450")
    ld = [("innervägg V4–V6, V15, V19", (0, 250), (-500, 330)),
          ("2 Ø10 i överkant", (160, -36), (520, 160)),
          ("U-byglar Ø6 s600", (175, -110), (520, -20)),
          ("2 Ø10 i underkant", (160, yb + 41), (520, -330)),
          (f"cellplast S200, {sv(tf)} mm under balken", (-120, yb - 50), (-520, -330)),
          (f"cellplast S100, {sv(t_eps)} mm", (-600, -200), (-600, 120))]
    nummer(ax, ld)
    lista(0.1, 0.8, "d) Balk under innervägg", ld)

    # ---------------------------------------------------------------- b) stolpens topp
    xl, yl = (-150, 1000), (1580, 2330)
    ax = panel(3.85, 4.05, xl, yl)
    R(ax, 0, H - 500, 100, 300, LECA, z=3); R(ax, 100, H - 500, 150, 300, ISOL, z=3); R(ax, 250, H - 500, 100, 300, LECA, z=3)
    R(ax, 0, 1900, 350, 200, LECA, z=3); R(ax, 80, 1940, 190, 160, BETONG, z=4)
    R(ax, 30, H, 970, 150, BETONG, z=3)
    R(ax, 350, H - 500, 100, 500 - 15 - 20, "#9aa0a8", z=5)
    brott(ax, -60, 520, H - 470)
    R(ax, 300, H - 15, 200, 15, STAL, z=6)
    for x in (330, 470):
        stud(ax, x, H, H + 75)
    R(ax, 360, H - 15 - 140, 80, 140, "none", lw=0.6, z=7, ls=(0, (2, 1)))
    R(ax, 393, 1950, 14, 60, "white", lw=0.45, z=7)
    dot(ax, 400, 1980, 6)
    lb = [("bjälklag 150 (K-05)", (800, H + 75), (800, 2290)),
          ("plåt 200 × 200 × 15 S355 med 4 svetsbultar Ø13, gjuts in", (480, H - 8), (650, 1950)),
          ("20 mm spel: stolpen bär inte bjälklaget", (400, H - 25), (650, 1830)),
          ("2 flattstål 80 × 10 på plåten, ett på var sida om stolpen", (440, H - 100), (650, 1710)),
          ("M12 8.8 genom flattstålen och stolpen, avlångt hål 14 × 54 lodrätt", (406, 1980), (650, 2070)),
          ("stålstolpe VKR 100×100×5 S355", (450, 1750), (650, 1610)),
          ("U-block gjuts med bjälklaget", (175, 1960), (-90, 2250))]
    nummer(ax, lb)
    lista(3.6, 3.6, "b) Stålstolpe, topp (system A: V14, V21)", lb)

    # ---------------------------------------------------------------- c) stolpens fot
    xl, yl = (-150, 1000), (-400, 500)
    ax = panel(3.85, 0.95, xl, yl)
    R(ax, -100, ybot, 550, tf, EPS2, z=1)
    R(ax, -100, yb, 100, h_balk, EPS2, z=1)
    R(ax, 450, ybot, 500, -hp - ybot, EPSF, z=1)
    P(ax, [(0, yb), (450, yb), (450, -hp), (950, -hp), (950, 0), (450, 0), (450, -50), (0, -50)], BETONG)
    for x in (60, 280):
        dot(ax, x, yb + 45); dot(ax, x, -85)
    ax.plot([470, 950], [-28, -28], color=INK, lw=0.55, zorder=5)
    R(ax, 0, -50, 100, 530, LECA, z=3); R(ax, 100, -50, 150, 530, ISOL, z=3); R(ax, 250, -50, 100, 530, LECA, z=3)
    R(ax, 350, -50, 100, 530, "#9aa0a8", z=5)
    R(ax, 450, -50, 22, 50, "#d0ccc4", hatch="....", z=5)
    brott(ax, -60, 520, 440)
    lc = [("stålstolpe VKR 100×100×5 S355", (400, 300), (700, 360)),
          ("Lecavägg mot jord", (50, 250), (-90, 380)),
          ("ficka: urtaget förlängt till balkens innerkant, 200 mm längs väggen; gjuts igen", (461, -25), (700, 160)),
          (f"kantbalk 450 × {sv(h_balk)}: 2 Ø10 i uk och ök", (280, yb + 45), (700, -330)),
          (f"L-element, fot {sv(tf)} mm S200", (150, ybot + 50), (-90, -380))]
    nummer(ax, lc)
    lista(3.6, 0.8, "c) Stålstolpe, fot", lc)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
