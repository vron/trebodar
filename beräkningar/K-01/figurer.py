"""Figurer till K-01: tvärsnitt, skruvbild i plan och en översikt per balk (stöd, M, V, skruvzoner)."""
import math

import matplotlib

matplotlib.use("svg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Polygon, Rectangle  # noqa: E402

# Carlito: systemets typsnitt, eller beräkningar/.fonts om det inte är installerat
import os as _os  # noqa: E402
from matplotlib import font_manager as _fm  # noqa: E402
_FONTS = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), ".fonts")
if _os.path.isdir(_FONTS):
    for _f in sorted(_os.listdir(_FONTS)):
        if _f.lower().endswith(".ttf"):
            _fm.fontManager.addfont(_os.path.join(_FONTS, _f))
plt.rcParams.update({"font.family": "Carlito", "font.size": 7.5, "svg.fonttype": "none",
                     "hatch.linewidth": 0.35, "axes.linewidth": 0.5, "xtick.major.width": 0.5,
                     "ytick.major.width": 0.5, "xtick.major.size": 2.5, "ytick.major.size": 2.5,
                     "xtick.labelsize": 6.5, "ytick.labelsize": 6.5})
INK = "#1e1e1e"
STAL = "#cfd3d8"
TRA = "#f1e6cf"
TRA_LINJE = "#c9b48a"
GRID = "#9a9a9a"
M_POS = "#b7c9de"
M_NEG = "#e2bdb3"
V_FILL = "#d3d5d8"
LW = 0.6
SLASH = [(-1, -1), (1, 1)]


def sv(x, n=0):
    s = f"{x:,.{n}f}".replace(",", " ").replace(".", ",")
    return s.replace("-", "−")


# ------------------------------------------------------------------ måttsättning
def matt_h(ax, x0, x1, y, txt, ext_from=None, fs=7, pos="over", gap=None):
    ax.plot([x0, x1], [y, y], color=INK, lw=0.45, solid_capstyle="butt")
    ax.plot([x0, x1], [y, y], ls="none", marker=SLASH, ms=4.5, mew=0.7, color=INK)
    if ext_from is not None:
        for xx, ye in zip((x0, x1), ext_from if isinstance(ext_from, (list, tuple)) else (ext_from, ext_from)):
            ax.plot([xx, xx], [ye, y + (y - ye) * 0.0], color=INK, lw=0.35)
    if txt:
        g = gap if gap is not None else 0
        ax.text((x0 + x1) / 2, y + g, txt, ha="center", va="bottom" if pos == "over" else "top", fontsize=fs)


def matt_v(ax, x, y0, y1, txt, fs=7, side="right"):
    ax.plot([x, x], [y0, y1], color=INK, lw=0.45)
    ax.plot([x, x], [y0, y1], ls="none", marker=SLASH, ms=4.5, mew=0.7, color=INK)
    ax.text(x + (4 if side == "right" else -4), (y0 + y1) / 2, txt, ha="left" if side == "right" else "right",
            va="center", fontsize=fs)


# ------------------------------------------------------------------ tvärsnitt
def rita_sektion(path, IN):
    geo, sk, st, tr = IN["geometri"], IN["skruv"], IN["stal"], IN["tra"]
    b, t, H = geo["b"], geo["t_pl"], geo["h_tot"]
    hw = H - 2 * t
    fig, ax = plt.subplots(figsize=(3.9, 2.25))
    ax.add_patch(Rectangle((0, t), b, hw, fc=TRA, ec=INK, lw=LW, zorder=1))
    for k in range(1, 4):
        ax.plot([0, b], [t + k * hw / 4] * 2, color=TRA_LINJE, lw=0.4, zorder=1)
    for y0 in (0, H - t):
        ax.add_patch(Rectangle((0, y0), b, t, fc=STAL, ec=INK, lw=LW, hatch="//////", zorder=2))
    for y in (t, H - t):
        ax.plot([0, b], [y, y], color="#6b4f2a", lw=1.1, zorder=3)
    d, L, hh = sk["d"], sk["langd"], sk["huvud"]
    dk, da, ds = sk["huvud_d"], sk["ansats"], sk["ds"]
    g0 = L - sk["b_ganga"]                                   # gängans början under huvudet
    xr = list(sk["rader2"])

    def skruv(xc, top, dashed):
        sgn = -1 if top else 1
        y0 = H if top else 0
        ls = (0, (2.2, 1.4)) if dashed else "solid"
        fc = "none" if dashed else "#5a5f66"
        # huvud mot plåten, ansats i hålet, skaft och gänga
        ax.add_patch(Rectangle((xc - dk / 2, y0), dk, -sgn * hh, fc=fc, ec=INK, lw=0.5, ls=ls, zorder=4))
        tip = y0 + sgn * L
        prof = [(da / 2, 0), (da / 2, 4), (ds / 2, 12), (ds / 2, g0), (d / 2, g0), (d / 2, L - 6), (0, L)]
        body = [(xc + r, y0 + sgn * z) for r, z in prof] + [(xc - r, y0 + sgn * z) for r, z in reversed(prof[:-1])]
        ax.add_patch(Polygon(body, closed=True, fc=fc, ec=INK, lw=0.5, ls=ls, zorder=4))
        if not dashed:
            for yy in np.arange(y0 + sgn * (g0 + 2), tip - sgn * 8, sgn * 4.5):
                ax.plot([xc - d / 2, xc + d / 2], [yy, yy + sgn * 2.2], color="#d9dce0", lw=0.35, zorder=5)

    skruv(xr[0], True, False)
    skruv(xr[1], True, True)
    skruv(xr[1], False, False)
    skruv(xr[0], False, True)
    matt_h(ax, 0, b, H + 13, f"{b}", ext_from=H + 7)
    for x0, x1 in ((0, xr[0]), (xr[0], xr[1]), (xr[1], b)):
        matt_h(ax, x0, x1, -14, f"{x1 - x0:.0f}", pos="under", gap=-2.5)
    for xx in (0, xr[0], xr[1], b):
        ax.plot([xx, xx], [-6, -16], color=INK, lw=0.35)
    xm = b + 12
    for y0, y1, tx in ((H - t, H, f"{t}"), (t, H - t, f"{hw}"), (0, t, f"{t}")):
        matt_v(ax, xm, y0, y1, tx, fs=6.5)
    matt_v(ax, xm + 30, 0, H, f"{H}")
    for y in (0, t, H - t, H):
        ax.plot([b + 2, xm + (30 if y in (0, H) else 0) + 2], [y, y], color=INK, lw=0.3)
    xt = -10
    stal_txt = f"Plattstål {b}×{t}\n{st['kvalitet']}"
    ax.text(xt, H - t / 2 + 2, stal_txt, ha="right", va="center", fontsize=7, linespacing=1.15)
    ax.text(xt, t / 2 - 2, stal_txt, ha="right", va="center", fontsize=7, linespacing=1.15)
    ax.text(xt, H / 2 - 2, f"Limträ {tr['kvalitet']}\n{b}×{hw}", ha="right", va="center", fontsize=7, linespacing=1.15)
    ys = H - 52
    ax.text(xt, ys, f"Skruv\n{sk['produkt'].split(' ', 1)[1]}", ha="right", va="center", fontsize=7, linespacing=1.15)
    ax.plot([xt + 2, xr[0] - d / 2 - 1], [ys, ys], color=INK, lw=0.4, zorder=6)
    yl = 42
    ax.text(xt, yl, "Epoxilim", ha="right", va="center", fontsize=7)
    ax.plot([xt + 2, 22, 30], [yl, yl, t + 0.6], color=INK, lw=0.4, zorder=6)
    ax.text(b / 2, -30, "Med plåt. Streckat: skruv i andra raden.", ha="center", va="top", fontsize=6, style="italic", color="#444")
    # utan plåt
    x0 = b + 95
    ax.add_patch(Rectangle((x0, t), b * 0.55, hw, fc=TRA, ec=INK, lw=LW))
    for k in range(1, 4):
        ax.plot([x0, x0 + b * 0.55], [t + k * hw / 4] * 2, color=TRA_LINJE, lw=0.4)
    ds = IN.get("distans")
    if ds:
        for y0 in (0, H - t):
            ax.add_patch(Rectangle((x0, y0), b * 0.55, t, fc="#f4ecdc", ec=INK, lw=0.5, ls=(0, (2.5, 1.5)), zorder=2))
        under = "Utan plåt, streckat:\ndistansregel (förkortad bredd)."
    else:
        ax.plot([x0 - 6, x0 + b * 0.55 + 6], [H, H], color=INK, lw=0.35, ls=(0, (3, 2)))
        ax.plot([x0 - 6, x0 + b * 0.55 + 6], [0, 0], color=INK, lw=0.35, ls=(0, (3, 2)))
        under = "Utan plåt (förkortad bredd).\nStreckat: plåtens yta."
    ax.text(x0 + b * 0.275, H / 2, f"Limträ\n{b}×{hw}", ha="center", va="center", fontsize=7, linespacing=1.15)
    ax.text(x0 + b * 0.275, -30, under, ha="center", va="top", fontsize=6, style="italic", color="#444")
    ax.set_xlim(-92, x0 + b * 0.55 + 4)
    ax.set_ylim(-38, H + 26)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.savefig(path, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


# ------------------------------------------------------------------ skruvbild i plan
def rita_plan(path, IN):
    geo, sk = IN["geometri"], IN["skruv"]
    b = geo["b"]
    Ls = 760
    s = 100
    e0 = sk["ande_plat"]
    fig, ax = plt.subplots(figsize=(4.0, 1.4))
    # utanför plåtänden: distansregel med glipa (eller limträet)
    ds = IN.get("distans")
    if ds:
        gl = ds["glipa"]
        ax.add_patch(Rectangle((-70, 0), 70, b, fc=TRA, ec="none", zorder=0))
        ax.add_patch(Rectangle((-70, 0), 70 - gl, b, fc="#f4ecdc", ec=INK, lw=0.5, ls=(0, (2.5, 1.5)), zorder=1))
        ax.text(-37, b / 2, "distans-\nregel", ha="center", va="center", fontsize=6.3, style="italic", color="#444")
    else:
        ax.add_patch(Rectangle((-70, 0), 70, b, fc=TRA, ec="none", zorder=1))
    ax.add_patch(Rectangle((0, 0), Ls, b, fc=STAL, ec="none", zorder=1))
    ax.plot([-70, Ls], [0, 0], color=INK, lw=LW); ax.plot([-70, Ls], [b, b], color=INK, lw=LW)
    ax.plot([0, 0], [0, b], color=INK, lw=LW)
    zz = np.linspace(0, b, 9)
    ax.plot(Ls + 6 * np.sin(np.linspace(0, 2 * np.pi, 9)), zz, color=INK, lw=0.5)
    rows = [b - sk["rader2"][0], b - sk["rader2"][1]]
    xs = np.arange(e0, Ls - 20, s)
    for i, x in enumerate(xs):
        y = rows[i % 2]
        ax.add_patch(plt.Circle((x, y), 9, fc="white", ec=INK, lw=0.5, zorder=3))
        ax.add_patch(plt.Circle((x, y), sk["d"] / 2, fc="#5a5f66", ec="none", zorder=4))
    for y in rows:
        ax.plot([-10, Ls], [y, y], color=GRID, lw=0.35, ls=(0, (6, 2, 1, 2)), zorder=2)
    matt_h(ax, 0, xs[0], b + 16, f"{e0}", ext_from=b + 2)
    matt_h(ax, xs[0], xs[1], b + 16, "s", ext_from=(b + 2, b + 2))
    matt_h(ax, xs[1], xs[2], b + 16, "s", ext_from=(b + 2, b + 2))
    matt_h(ax, xs[0], xs[2], -16, "2s = c/c i raden", ext_from=(rows[0], rows[0]), pos="under", gap=-3)
    ax.plot([xs[0], xs[0]], [rows[0], -16], color=INK, lw=0.35)
    ax.plot([xs[2], xs[2]], [rows[0], -16], color=INK, lw=0.35)
    xm = Ls + 26
    for y0, y1 in ((0, rows[1]), (rows[1], rows[0]), (rows[0], b)):
        matt_v(ax, xm, y0, y1, f"{y1 - y0:.0f}", fs=6.5, side="right")
    ax.text(Ls / 2 + 60, b / 2, "plåt, sedd uppifrån", ha="center", va="center", fontsize=6.5, style="italic", color="#444")
    ax.text(-35, -6, "plåtände", ha="center", va="top", fontsize=6.5)
    ax.set_xlim(-75, Ls + 62)
    ax.set_ylim(-36, b + 44)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.savefig(path, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


# ------------------------------------------------------------------ balköversikt
def _zonfarg(s):
    lo, hi = math.log(25), math.log(200)
    u = min(1.0, max(0.0, (math.log(s) - lo) / (hi - lo)))
    mork, ljus = np.array([0x3a, 0x48, 0x5c]) / 255, np.array([0xe9, 0xed, 0xf2]) / 255
    return tuple(mork + (ljus - mork) * u), u


def rita_balk(path, B, A, env, rad, BOKST):
    x, Mmax, Mmin, V = env
    L = A.L
    sup = A.huvud
    fig = plt.figure(figsize=(6.85, 3.6))
    gs = fig.add_gridspec(4, 1, height_ratios=[1.3, 1.0, 0.72, 0.30], hspace=0.10,
                          left=0.075, right=0.995, top=0.995, bottom=0.085)
    ax0 = fig.add_subplot(gs[0])
    ax1 = fig.add_subplot(gs[1], sharex=ax0)
    ax2 = fig.add_subplot(gs[2], sharex=ax0)
    ax3 = fig.add_subplot(gs[3], sharex=ax0)
    pad = 0.035 * L
    # -------------------------------------------------- elevation
    ax = ax0
    tp = 0.13                                       # plåtens tjocklek i skissen (överdriven)
    ax.add_patch(Rectangle((0, tp), L, 1 - 2 * tp, fc=TRA, ec=INK, lw=LW, zorder=2))
    if B.get("_distans"):
        gr = [0.0] + [q for pp in A.platar for q in pp] + [L]
        for a_, b_ in zip(gr[0::2], gr[1::2]):
            if b_ - a_ > 1:
                for y0 in (0, 1 - tp):
                    ax.add_patch(Rectangle((a_, y0), b_ - a_, tp, fc="#f4ecdc", ec=INK, lw=0.35, ls=(0, (2.5, 1.5)), zorder=3))
    for p0, p1 in A.platar:
        for y0 in (0, 1 - tp):
            ax.add_patch(Rectangle((p0, y0), p1 - p0, tp, fc="#8d949c", ec=INK, lw=0.5, zorder=3))
        ax.text((p0 + p1) / 2, 1.5, f"plåt {sv(p1 - p0)}", ha="center", va="bottom", fontsize=6.3, style="italic", color="#333")
    tw = 0.011 * L
    if A.vagg:
        v0, v1 = A.vagg
        ax.add_patch(Rectangle((v0, -0.95), v1 - v0, 0.95, fc="white", ec=INK, lw=0.5, hatch="////", zorder=1))
        ax.text((v0 + v1) / 2, -0.47, "innervägg", ha="center", va="center", fontsize=7,
                bbox=dict(fc="white", ec="none", pad=1.0), zorder=5)
    tri = B.get("triangel")
    strava = B.get("strava") or ((tri["x"], tri["x"] + tri["e"]) if tri else None)
    ej_stod = bool(tri)
    for i, s in enumerate(sup):
        if A.vagg and A.vagg[0] - 1e-6 <= s <= A.vagg[1] + 1e-6:
            pass
        elif strava and abs(s - strava[0]) < 1e-6:
            pw = 0.0055 * L
            ax.add_patch(Rectangle((s - pw, -1.55), 2 * pw, 1.55, fc="#e6ddc8", ec=INK, lw=0.5, zorder=1))
        elif strava and abs(s - strava[1]) < 1e-6:
            pw = 0.0055 * L
            x0, y0 = strava[0] + pw, -1.05
            dx, dy = s - x0, 0 - y0
            n = math.hypot(dx / L * 12, dy) or 1
            ox, oy = 0.0045 * L * dy / n, -0.09 * (dx / L * 12) / n
            ax.add_patch(Polygon([(x0, y0 - 0.12), (x0, y0 + 0.12), (s + ox * 0, 0.0), (s + 0.009 * L, 0.0)], closed=True,
                                 fc="#e6ddc8", ec=INK, lw=0.5, zorder=1))
        else:
            ax.add_patch(Polygon([(s, 0), (s - tw, -0.62), (s + tw, -0.62)], closed=True, fc="white", ec=INK, lw=0.6, zorder=5))
            ax.plot([s - 1.6 * tw, s + 1.6 * tw], [-0.62, -0.62], color=INK, lw=0.6)
            for k in np.linspace(-1.4, 1.2, 6):
                ax.plot([s + k * tw, s + (k + 0.35) * tw], [-0.62, -0.78], color=INK, lw=0.35)
        ax.text(s, 1.18, BOKST[i], ha="center", va="bottom", fontsize=7.5, fontweight="bold")
    if ej_stod:                                   # sträva som fjädrande stöd
        pw = 0.0055 * L
        for sg_ in (1, -1):                       # strävor åt båda hållen
            s = strava[0] + sg_ * (strava[1] - strava[0])
            x0, y0 = strava[0] + sg_ * pw, -1.05
            ax.add_patch(Polygon([(x0, y0 - 0.12), (x0, y0 + 0.12), (s, 0.0), (s + sg_ * 0.009 * L, 0.0)], closed=True,
                                 fc="#e6ddc8", ec=INK, lw=0.5, zorder=1))
    # mått: spann
    ydim = -1.95
    pts = [0.0] + list(sup) + [L]
    pts = sorted(set(round(p, 3) for p in pts))
    for p0, p1 in zip(pts[:-1], pts[1:]):
        txt = sv(p1 - p0) if (p1 - p0) >= 0.035 * L else ""
        matt_h(ax, p0, p1, ydim, txt, fs=6.8, gap=0.06)
    for p in pts:
        ax.plot([p, p], [ydim - 0.12, -0.05 if p in (0.0, L) else ydim + 0.35], color=INK, lw=0.35)
    small = [(p0, p1) for p0, p1 in zip(pts[:-1], pts[1:]) if (p1 - p0) < 0.035 * L]
    for p0, p1 in small:
        ax.text(p0 + (p1 - p0) / 2, ydim - 0.28, sv(p1 - p0), ha="center", va="top", fontsize=5.8, color="#333")
    matt_h(ax, 0, L, 2.25, sv(L), fs=7, gap=0.06)
    ax.plot([0, 0], [1.85, 2.35], color=INK, lw=0.35)
    ax.plot([L, L], [1.85, 2.35], color=INK, lw=0.35)
    if strava:
        ax.text(strava[0] - 0.009 * L, -1.0, "stolpe med dubbla strävor",
                ha="right", va="center", fontsize=6.3, color="#333")
    ax.set_ylim(-2.5, 2.75)
    ax.axis("off")
    # -------------------------------------------------- moment (dragen sida nedåt: fältmoment ritas under axeln)
    ax = ax1
    Mx, Mn = Mmax / 1e6, Mmin / 1e6
    ax.fill_between(x, 0, Mx, color=M_POS, lw=0, zorder=2)
    ax.fill_between(x, 0, Mn, color=M_NEG, lw=0, zorder=2)
    ax.plot(x, Mx, color="#3c5a80", lw=0.6, zorder=3)
    ax.plot(x, Mn, color="#9a4a3a", lw=0.6, zorder=3)
    ax.axhline(0, color=INK, lw=0.5, zorder=4)
    ax.invert_yaxis()
    span = max(Mx.max(), -Mn.min(), 1)
    for p0, p1 in zip(pts[:-1], pts[1:]):
        sel = (x > p0) & (x < p1)
        if sel.sum() and Mx[sel].max() > 0.12 * span:
            i = np.argmax(np.where(sel, Mx, -1e9))
            ax.text(x[i], Mx[i] + 0.06 * span, sv(Mx[i], 1), ha="center", va="top", fontsize=6.3, color="#1f3b5c")
    for s in sup:
        sel = np.abs(x - s) < 0.02 * L
        if sel.sum() and Mn[sel].min() < -0.12 * span:
            i = np.argmin(np.where(sel, Mn, 1e9))
            ax.text(x[i], Mn[i] - 0.06 * span, sv(Mn[i], 1), ha="center", va="bottom", fontsize=6.3, color="#6e2a1e")
    ax.set_ylabel("M (kNm)", fontsize=7)
    lim = 1.32 * span
    ax.set_ylim(lim, -lim)
    # -------------------------------------------------- tvärkraft
    ax = ax2
    Vk = V / 1e3
    # utjämning för ritning: glidande max över ±60 mm (tar bort smala dalar vid fjädrande upplag)
    Vk = np.array([Vk[(x >= xi - 60) & (x <= xi + 60)].max() for xi in x])
    ax.fill_between(x, 0, Vk, color=V_FILL, lw=0, zorder=2)
    ax.plot(x, Vk, color="#555", lw=0.6, zorder=3)
    ax.axhline(0, color=INK, lw=0.5)
    vmax = Vk.max()
    for s in sup:
        sel = np.abs(x - s) < 0.03 * L
        if sel.sum():
            i = np.argmax(np.where(sel, Vk, -1))
            if Vk[i] > 0.25 * vmax:
                ax.text(s, Vk[i] + 0.05 * vmax, sv(Vk[i], 1), ha="center", va="bottom", fontsize=6.3, color="#333")
    ax.set_ylim(0, 1.32 * vmax)
    ax.set_ylabel("|V| (kN)", fontsize=7)
    # -------------------------------------------------- skruvzoner
    ax = ax3
    for z in rad:
        x0, x1, s = z[1], z[2], z[3]
        cc = s
        col, u = _zonfarg(s)
        ax.add_patch(Rectangle((x0, 0), x1 - x0, 1, fc=col, ec="white", lw=0.8))
        if x1 - x0 > 0.045 * L:
            ax.text((x0 + x1) / 2, 0.5, sv(cc), ha="center", va="center", fontsize=6.3,
                    color="white" if u < 0.5 else INK)
        elif x1 - x0 > 0.012 * L:
            ax.text((x0 + x1) / 2, 0.5, sv(cc), ha="center", va="center", fontsize=5.3, rotation=90,
                    color="white" if u < 0.5 else INK)
    ax.set_ylim(0, 1)
    ax.set_yticks([])
    ax.set_ylabel("s\n(mm)", fontsize=6.5, rotation=0, ha="right", va="center", labelpad=4)
    for a in (ax1, ax2, ax3):
        for s in sup:
            a.axvline(s, color=GRID, lw=0.4, ls=(0, (2, 2)), zorder=1)
        for sp_ in ("top", "right"):
            a.spines[sp_].set_visible(False)
    for a in (ax1, ax2):
        a.tick_params(axis="x", which="both", bottom=False, labelbottom=False)
        a.spines["bottom"].set_visible(False)
    ax3.set_xticks(np.arange(0, L + 1, 1000))
    ax3.set_xticklabels([f"{int(v / 1000)}" for v in np.arange(0, L + 1, 1000)])
    ax3.set_xlabel("x (m)", fontsize=7, labelpad=1)
    ax0.set_xlim(-pad, L + pad)
    fig.align_ylabels([ax1, ax2, ax3])
    fig.savefig(path, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


# ------------------------------------------------------------------ princip: temperaturkraft vid plåtände
def rita_temp(path, lam_lim, lam_skruv, L=4000.0):
    """Plåtkraft N(x) och skjuvkraft per längdenhet q(x) längs en plåtbit vid lika temperaturändring i plåtarna (kyla)."""
    x = np.linspace(-L / 2, L / 2, 801)
    fig, axs = plt.subplots(3, 1, figsize=(6.6, 2.9), sharex=True, gridspec_kw=dict(height_ratios=[0.8, 1, 1], hspace=0.25))
    ax = axs[0]
    ax.add_patch(Rectangle((-L / 2 - 500, -0.6), L + 1000, 1.0, fc=TRA, ec=INK, lw=LW))
    ax.add_patch(Rectangle((-L / 2, 0.4), L, 0.35, fc=STAL, ec=INK, lw=LW, hatch="//////"))
    for s_ in (-1, 1):
        ax.annotate("", xy=(s_ * (L / 2 - 450), 0.575), xytext=(s_ * (L / 2 - 20), 0.575),
                    arrowprops=dict(arrowstyle="-|>", lw=0.7, color="#b5452f", mutation_scale=7))
    ax.text(0, 0.95, "kall plåt vill krympa mer än limträet", ha="center", va="bottom", fontsize=7)
    ax.text(0, -0.1, "limträ", ha="center", va="center", fontsize=7, color="#555")
    ax.set_ylim(-0.7, 1.5); ax.axis("off")
    for lam, ls, lab in ((lam_lim, "-", "lim"), (lam_skruv, (0, (3, 2)), "enbart skruv")):
        N = 1 - np.cosh(lam * x) / np.cosh(lam * L / 2)
        q = lam * np.sinh(lam * np.abs(x)) / np.cosh(lam * L / 2)
        axs[1].plot(x, N, color=INK, lw=0.9, ls=ls, label=lab)
        axs[2].plot(x, q / lam_lim, color=INK, lw=0.9, ls=ls)
    axs[1].set_ylabel("plåtkraft\n$N / N_\\infty$", fontsize=7); axs[1].set_ylim(0, 1.15)
    axs[1].legend(fontsize=6.5, frameon=False, loc="lower center", ncol=2)
    axs[2].set_ylabel("skjuvkraft per\nlängdenhet\ni fogen", fontsize=7); axs[2].set_yticks([]); axs[2].set_ylim(0, 1.1)
    axs[2].set_xticks([-L / 2, 0, L / 2]); axs[2].set_xticklabels(["plåtände", "mitt", "plåtände"])
    for a in axs[1:]:
        for sp in ("top", "right"):
            a.spines[sp].set_visible(False)
    axs[2].annotate("spets vid änden", xy=(L / 2 - 30, 0.97), xytext=(L / 2 - 1300, 0.75), fontsize=6.5,
                    arrowprops=dict(arrowstyle="-", lw=0.4, color=INK))
    axs[2].text(0, 0.12, "ingen skjuvning mitt på plåten", ha="center", fontsize=6.5)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
