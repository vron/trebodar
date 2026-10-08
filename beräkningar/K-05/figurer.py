"""Figurer till K-05 i samma stil som K-01 (Carlito, svart linje, ljusa fyllningar, snedstreck på måttlinjer)."""
import json

import numpy as np

import matplotlib
import matplotlib.ticker

matplotlib.use("svg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Polygon, Rectangle  # noqa: E402
import matplotlib.patheffects as pe  # noqa: E402
HALO = [pe.withStroke(linewidth=2.2, foreground="white")]
from shapely.geometry import LineString, Polygon as SPoly  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

plt.rcParams.update({"font.family": "Carlito", "font.size": 7.5, "svg.fonttype": "none",
                     "hatch.linewidth": 0.35, "axes.linewidth": 0.5})
INK = "#1e1e1e"
BETONG = "#ecebe7"
MARK = "#f4ecdc"
LECA = "#b9b3a9"
ISOL = "#f7f3df"
STAL = "#5a5f66"
FRI = "#c0504d"
LAST = "#2c4a6e"
PLAN1 = "#9db7d1"
GRID = "#9a9a9a"
LW = 0.6
SLASH = [(-1, -1), (1, 1)]


def sv(x, n=0):
    return f"{x:,.{n}f}".replace(",", " ").replace(".", ",").replace("-", "−")


def matt(ax, p0, p1, off, txt, fs=6.5, ext=True):
    """Måttlinje mellan p0 och p1 (axelparallell), förskjuten off (mm) vinkelrätt, med hjälplinjer."""
    (x0, y0), (x1, y1) = p0, p1
    if y0 == y1:                                    # horisontell
        y = y0 + off
        ax.plot([x0, x1], [y, y], color=INK, lw=0.45)
        ax.plot([x0, x1], [y, y], ls="none", marker=SLASH, ms=4.5, mew=0.7, color=INK)
        if ext:
            for xx in (x0, x1):
                ax.plot([xx, xx], [y0 + (120 if off > 0 else -120), y + (100 if off > 0 else -100)], color=INK, lw=0.3)
        ax.text((x0 + x1) / 2, y + (60 if off > 0 else -60), txt, ha="center", va="bottom" if off > 0 else "top", fontsize=fs)
    else:                                           # vertikal
        x = x0 + off
        ax.plot([x, x], [y0, y1], color=INK, lw=0.45)
        ax.plot([x, x], [y0, y1], ls="none", marker=SLASH, ms=4.5, mew=0.7, color=INK)
        if ext:
            for yy in (y0, y1):
                ax.plot([x0 + (120 if off > 0 else -120), x + (100 if off > 0 else -100)], [yy, yy], color=INK, lw=0.3)
        ax.text(x + (70 if off > 0 else -70), (y0 + y1) / 2, txt, ha="center", va="bottom" if off < 0 else "top",
                fontsize=fs, rotation=90)


def vaggband(w, E, alla=()):
    """Lecaväggens isolering (mittre 150) och hela tjocklek (350) som shapely-polygoner. Ändar som möter en
    annan vägg förlängs så att hörnen blir hela."""
    ax, c, a, b = w[:4]
    def mot(v):
        return any(o[0] != ax and abs(o[1] - v) < 1 and o[2] - 1 <= c <= o[3] + 1 for o in alla)
    a = a - E if mot(a) else a
    b = b + E if mot(b) else b
    if ax == "h":
        L = LineString([(a, c), (b, c)])
    else:
        L = LineString([(c, a), (c, b)])
    return L.buffer(75, cap_style="flat"), L.buffer(175, cap_style="flat"), L


def _vaggar(ax, G, fc=LECA, ec=INK, lw=0.35, zorder=2):
    """Lecaväggarna som en sammanhängande yta (350 mm), klippt mot plattan."""
    hela = [vaggband(w, G["E"], G["vagg"])[1] for w in G["vagg"]]
    u = unary_union(hela).intersection(SPoly(G["kontur"]).buffer(0))
    for g in getattr(u, "geoms", [u]):
        ax.add_patch(Polygon(list(g.exterior.coords), closed=True, fc=fc, ec=ec, lw=lw, zorder=zorder))


def _matt(ax):
    """Yttermått enligt Plattor (mm)."""
    matt(ax, (0, 15900), (4310, 15900), 700, sv(4310))
    matt(ax, (4310, 12510), (9500, 12510), 700, sv(5190), ext=False)
    ax.plot([4310, 4310], [15900 - 4890 + 120, 12510 + 800], color=INK, lw=0.3)
    matt(ax, (9500, 12510), (13810, 12510), 700, sv(4310))
    matt(ax, (9500, 11010), (9500, 12510), -500, sv(1500))
    matt(ax, (0, 3590), (4500, 3590), -700, sv(4500))
    matt(ax, (4500, 0), (9310, 0), -700, sv(4810))
    matt(ax, (9310, 1000), (13810, 1000), -700, sv(4500))
    matt(ax, (0, 0), (13810, 0), -1500, sv(13810), ext=False)
    ax.plot([0, 0], [-1600, 3590 - 120], color=INK, lw=0.3)
    ax.plot([13810, 13810], [-1600, 1000 - 120], color=INK, lw=0.3)
    matt(ax, (4500, 0), (4500, 3590), -700, sv(3590))
    matt(ax, (0, 3590), (0, 15900), -700, sv(12310))
    matt(ax, (0, 0), (0, 15900), -1500, sv(15900), ext=False)
    ax.plot([-1600, 4500 - 120], [0, 0], color=INK, lw=0.3)
    ax.plot([-1600, -120], [15900, 15900], color=INK, lw=0.3)
    matt(ax, (13810, 0), (13810, 1000), 700, sv(1000), ext=False)
    ax.plot([9310 + 120, 13810 + 800], [0, 0], color=INK, lw=0.3)
    matt(ax, (13810, 1000), (13810, 12510), 700, sv(11510))
    ox, oy = -1300, -2300
    ax.annotate("", (ox + 900, oy), (ox, oy), arrowprops=dict(arrowstyle="-|>", lw=0.6, color=INK, mutation_scale=7))
    ax.annotate("", (ox, oy + 900), (ox, oy), arrowprops=dict(arrowstyle="-|>", lw=0.6, color=INK, mutation_scale=7))
    ax.text(ox + 950, oy, "x", va="center", fontsize=7); ax.text(ox, oy + 950, "y", ha="center", fontsize=7)


def _vagg_etikett(ax, G, fs=5.6):
    """Väggnamn V1–V21 (upplagslinjernas ordning) vid väggens mitt, på plattans insida."""
    cx, cy = SPoly(G["kontur"]).centroid.coords[0]
    for i, w in enumerate(G["vagg"], 1):
        ax_, c, a, b = w[:4]
        m = (a + b) / 2
        if ax_ == "h":
            x, y = m, c + (330 if c < cy else -330)
            rot = 0
        else:
            x, y = c + (330 if c < cx else -330), m
            rot = 90
        if b - a < 900:          # korta väggbitar: etiketten längs väggen bredvid
            rot = 0
        x, y = {"V13": (8560, 560), "V17": (8730, 960)}.get(f"V{i}", (x, y))
        ax.text(x, y, f"V{i}", fontsize=fs, ha="center", va="center", color="#555", style="italic", rotation=rot,
                zorder=9, path_effects=HALO)


def rita_geometri(path, G, plat=200):
    """Plattan, Lecaväggarna (V1–V21) och rören (P1–P19)."""
    kontur, hal, pel, mark = G["kontur"], G["hal"], G["pelare"], G["mark"]
    fig, ax = plt.subplots(figsize=(6.6, 7.2))
    ax.add_patch(Polygon(kontur, closed=True, fc=BETONG, ec="none", zorder=0))
    ax.add_patch(Polygon(mark, closed=True, fc=MARK, ec="none", hatch="....", zorder=1, lw=0))
    ax.add_patch(Polygon(mark, closed=True, fc="none", ec=GRID, lw=0.4, ls=(0, (3, 2)), zorder=1))
    _vaggar(ax, G)
    ax.add_patch(Polygon(kontur, closed=True, fc="none", ec=INK, lw=LW * 1.4, zorder=5))
    ax.add_patch(Polygon(hal, closed=True, fc="white", ec=INK, lw=LW, zorder=5))
    (hx0, hy0), (hx1, hy1) = hal[0], hal[2]
    ax.plot([hx0, hx1], [hy0, hy1], color=GRID, lw=0.35, zorder=5)
    ax.plot([hx0, hx1], [hy1, hy0], color=GRID, lw=0.35, zorder=5)
    for i, (x, y) in enumerate(pel, 1):
        ax.add_patch(Rectangle((x - 70, y - 70), 140, 140, fc=STAL, ec="white", lw=0.4, zorder=8))
        under = i in (12, 13, 14)          # vid trapphålets underkant: etiketten under röret
        ax.text(x + 140, y - 120 if under else y + 120, f"P{i}", fontsize=6.3, ha="left", va="top" if under else "bottom",
                zorder=9, path_effects=HALO)
    _vagg_etikett(ax, G)
    ax.text(2155, 12700, "på mark", ha="center", va="center", fontsize=6.8, style="italic", color="#444",
            zorder=4, bbox=dict(fc=MARK, ec="none", pad=1.2))
    ax.text((hx0 + hx1) / 2, (hy0 + hy1) / 2, "trapphål", ha="center", va="center", fontsize=6.3, style="italic",
            color="#444", zorder=6, bbox=dict(fc="white", ec="none", pad=0.4))
    _matt(ax)
    items = [
        (Rectangle((0, 0), 1, 1, fc=LECA, ec=INK, lw=0.35), "Lecavägg 350 (Leca 100 + isolering 150 + Leca 100)"),
        (Rectangle((0, 0), 1, 1, fc=STAL, ec="none"), "stålrör VKR 80×80×4"),
        (Rectangle((0, 0), 1, 1, fc=MARK, ec=GRID, lw=0.4, hatch="...."), "platta på mark (cellplast)"),
    ]
    ax.legend([i for i, _ in items], [t for _, t in items], loc="upper center", bbox_to_anchor=(0.5, -0.005),
              ncol=2, frameon=False, fontsize=6.6, handlelength=1.6, handleheight=1.0, columnspacing=1.4)
    ax.set_xlim(-2300, 13810 + 1300)
    ax.set_ylim(-2400, 15900 + 1200)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.savefig(path, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


VAGGLAST = "#6f8fb3"


def rita_laster(path, G, L):
    """Laster från plan 1: punktlaster (fyllda på plattan, ofyllda över Lecavägg) och linjelaster."""
    fig, ax = plt.subplots(figsize=(6.6, 7.0))
    ax.add_patch(Polygon(G["kontur"], closed=True, fc=BETONG, ec="none", zorder=0))
    ax.add_patch(Polygon(G["mark"], closed=True, fc=MARK, ec="none", hatch="....", zorder=1, lw=0))
    _vaggar(ax, G, fc="#d6d2cb", ec="#8a8a8a", lw=0.3)
    ax.add_patch(Polygon(G["kontur"], closed=True, fc="none", ec=INK, lw=LW * 1.2, zorder=5))
    ax.add_patch(Polygon(G["hal"], closed=True, fc="white", ec=INK, lw=LW, zorder=5))
    for x, y in G["pelare"]:
        ax.add_patch(Rectangle((x - 60, y - 60), 120, 120, fc="#9a9a9a", ec="none", zorder=4))
    cx, cy = SPoly(G["kontur"]).centroid.coords[0]
    # ytterväggar: tunn linje över Lecavägg, tjock där väggen står på plattan
    for w in L["vaggar"]:
        pr = w["prov"]
        for k in range(len(pr)):
            p = pr[k]
            on = p["plats"] != "vägg"
            if k + 1 < len(pr):
                q = pr[k + 1]
                ax.plot([p["x"], q["x"]], [p["y"], q["y"]], color=LAST if on else VAGGLAST, lw=2.4 if on else 1.1,
                        solid_capstyle="butt", zorder=6, alpha=0.9 if on else 0.8)
        (x0, y0), (x1, y1) = w["p0"], w["p1"]
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        if y0 == y1:
            dy = -420 if my < cy else 420
            # gavlar som ligger mot en annan huskropp: etiketten utanför i rätt riktning
            if w["namn"] in ("qY7",):
                dy = 420
            ax.text(mx, my + dy, w["namn"], ha="center", va="center", fontsize=6.2, color=LAST, zorder=10,
                    path_effects=HALO)
        else:
            dx = -430 if mx < cx else 430
            if w["namn"] in ("qY2", "qY12", "qY8", "qY6"):
                dx = -dx if w["namn"] in ("qY8", "qY6") else dx
            ax.text(mx + dx, my, w["namn"], ha="center", va="center", fontsize=6.2, color=LAST, rotation=90, zorder=10,
                    path_effects=HALO)
    for l in L["linjer"]:
        (x0, y0), (x1, y1) = l["pl"]
        ax.plot([x0, x1], [y0, y1], color=LAST, lw=2.4, solid_capstyle="butt", zorder=6, alpha=0.9)
    ll = [l for l in L["linjer"] if l["namn"] == "qD2"]
    ax.text(ll[0]["pl"][0][0] + 160, 3000, "qD2", fontsize=6.2, color=LAST, rotation=90, va="center", zorder=10,
            path_effects=HALO)
    t = [l for l in L["linjer"] if l["namn"] == "qT"]
    ax.text((t[0]["pl"][0][0] + t[1]["pl"][0][0]) / 2 - 400, t[0]["pl"][0][1] - 120, "qT (båda kortsidorna)", fontsize=5.8,
            color=LAST, ha="center", va="top", zorder=10, path_effects=HALO)
    # punktlaster
    flytt = {"LD2_1": (150, -330, "left"), "LD2_2": (150, 60, "left"), "LD4_1": (-150, 150, "right"),
             "LD2_3": (150, 150, "left"), "LD4_2": (150, -330, "left"), "LD2_4": (-150, -330, "right"),
             "LA6": (150, 150, "left"),
             "LA3": (150, 150, "left"), "LA2": (-150, 150, "right")}
    for p in L["punkter"]:
        x, y = p["x"], p["y"]
        fyll = p["plats"] != "vägg"
        ax.plot([x], [y], marker="v", ms=6.4, mfc=LAST if fyll else "white", mec=LAST, mew=0.9, zorder=11)
        dx, dy, ha = flytt.get(p["namn"], (150 if x < cx else -150, 150, "left" if x < cx else "right"))
        if p["namn"].startswith("LA"):
            dx = 160 if x < cx else -160; ha = "left" if x < cx else "right"
            dy = 160 if y < cy else -330
            if p["namn"] in flytt:
                dx, dy, ha = flytt[p["namn"]]
        ax.text(x + dx, y + dy, p["namn"], fontsize=6.2, ha=ha, va="bottom", color=LAST,
                weight="bold", zorder=12, path_effects=HALO)
    ax.text(2155, 12700, "på mark", ha="center", va="center", fontsize=6.5, style="italic", color="#666", zorder=4,
            bbox=dict(fc=MARK, ec="none", pad=1.2))
    items = [
        (plt.Line2D([0], [0], ls="none", marker="v", ms=6.4, mfc=LAST, mec=LAST), "punktlast på plattan"),
        (plt.Line2D([0], [0], ls="none", marker="v", ms=6.4, mfc="white", mec=LAST, mew=0.9),
         "punktlast över Lecavägg (direkt till väggen)"),
        (plt.Line2D([0], [0], color=LAST, lw=2.4), "linjelast på plattan"),
        (plt.Line2D([0], [0], color=VAGGLAST, lw=1.1), "ytterväggens linjelast över Lecavägg"),
        (Rectangle((0, 0), 1, 1, fc="#d6d2cb", ec="#8a8a8a", lw=0.3), "Lecavägg"),
        (Rectangle((0, 0), 1, 1, fc="#9a9a9a", ec="none"), "rör"),
    ]
    ax.legend([i for i, _ in items], [t for _, t in items], loc="upper center", bbox_to_anchor=(0.5, -0.0),
              ncol=2, frameon=False, fontsize=6.6, handlelength=1.6, handleheight=1.0, columnspacing=1.4)
    ax.set_xlim(-900, 13810 + 900)
    ax.set_ylim(-900, 15900 + 700)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.savefig(path, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


def inatgaende_horn(kontur):
    """Plattans inåtgående hörn (inre vinkel 270°) med riktningen in i plattan längs bisektrisen."""
    k = np.asarray(kontur, float)
    n = len(k)
    area = 0.5 * sum(k[i, 0] * k[(i + 1) % n, 1] - k[(i + 1) % n, 0] * k[i, 1] for i in range(n))
    out = []
    for i in range(n):
        a, b, c = k[i - 1], k[i], k[(i + 1) % n]
        cr = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
        if cr * area < 0:
            u = (a - b) / np.linalg.norm(a - b); v = (c - b) / np.linalg.norm(c - b)
            bis = -(u + v); bis /= np.linalg.norm(bis)        # in i plattan
            out.append((b, bis))
    return out


def rita_armering(path, G, R):
    """Överkantens tilläggsjärn (zoner), diagonaljärn vid inåtgående hörn och trapphålets hörn."""
    fig, ax = plt.subplots(figsize=(6.0, 6.6))
    ax.add_patch(Polygon(G["kontur"], closed=True, fc=BETONG, ec="none", zorder=0))
    _bas(ax, G, pelare=False)
    for zn in R["zoner"]:
        x0, y0, x1, y1 = zn["bounds"]
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc="#e2bdb3", ec=INK, lw=0.5, alpha=0.85, hatch="++",
                               zorder=2))
        ax.text(x0 + 60, y1 - 60, zn["namn"], ha="left", va="top", fontsize=6.5, weight="bold",
                zorder=9, path_effects=HALO)
    # diagonaljärn: 2 Ø10 L = 1,2 m, vinkelrätt mot bisektrisen, 150 mm in från hörnet
    hal = G["hal"]
    hx = [p[0] for p in hal]; hy = [p[1] for p in hal]
    hcx, hcy = sum(hx) / 4, sum(hy) / 4
    diag = [(b, bis) for b, bis in inatgaende_horn(G["kontur"])]
    for p in hal:
        b = np.array(p, float); bis = b - np.array([hcx, hcy]); bis /= np.linalg.norm(bis)
        diag.append((b, bis))
    for b, bis in diag:
        t = np.array([-bis[1], bis[0]])
        for off in (150, 250):
            c = b + bis * off
            p0, p1 = c - t * 600, c + t * 600
            ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color=FRI, lw=0.9, zorder=8, solid_capstyle="butt")
    for p in R["pelare"]:
        x, y = p["x"], p["y"]
        ax.add_patch(Rectangle((x - 40, y - 40), 80, 80, fc=STAL, ec="none", zorder=9))
        ax.text(x + 150, y + 130, p["namn"], fontsize=6, zorder=9, path_effects=HALO)
    items = [(Rectangle((0, 0), 1, 1, fc="#e2bdb3", ec=INK, lw=0.5, hatch="++"), "tilläggsjärn i överkant, båda riktningarna"),
             (plt.Line2D([0], [0], color=FRI, lw=0.9), "diagonaljärn 2 Ø10, L = 1,2 m, i överkant"),
             (Rectangle((0, 0), 1, 1, fc=STAL, ec="none"), "rör 80×80")]
    ax.legend([i for i, _ in items], [t for _, t in items], loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=2,
              frameon=False, fontsize=6.6, handlelength=1.6, handleheight=1.0)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    return len(diag)


def rita_tvarsnitt(path, R):
    """Plattans tvärsnitt med armeringslagren och täckskikten (skala 1:5 ungefär)."""
    ind = R["indata"]
    h, cu, co = ind["h"], ind["c_uk"], ind["c_ok"]
    du, cu_cc = ind["nat_uk"]; do, co_cc = ind["nat_ok"]
    fig, ax = plt.subplots(figsize=(5.2, 1.7))
    W = 500
    ax.add_patch(Rectangle((0, 0), W, h, fc=BETONG, ec=INK, lw=0.7))
    yb1 = cu + du / 2; yb2 = cu + du + du / 2          # x yttre, y inre
    yt1 = h - co - do / 2; yt2 = h - co - do - do / 2
    ax.plot([10, W - 10], [yb2, yb2], color=INK, lw=1.4)
    ax.plot([10, W - 10], [yt2, yt2], color=INK, lw=1.1)
    for x in np.arange(50, W, cu_cc):
        ax.add_patch(plt.Circle((x, yb1), du / 2, fc=INK, ec="none"))
    for x in np.arange(50, W, co_cc):
        ax.add_patch(plt.Circle((x, yt1), do / 2, fc=INK, ec="none"))
    # mått: höjd och täckskikt
    def vm(x, y0, y1, txt, side=1):
        ax.annotate("", (x, y0), (x, y1), arrowprops=dict(arrowstyle="<->", lw=0.5, mutation_scale=5, shrinkA=0, shrinkB=0))
        ax.text(x - 8 * side, (y0 + y1) / 2, txt, fontsize=6.3, va="center", ha="right" if side > 0 else "left")
    vm(-25, 0, h, f"{h:.0f}")
    vm(25, h - co, h, f"{co}", side=-1)
    vm(25, 0, cu, f"{cu}", side=-1)
    # etiketter med hänvisningslinjer
    lab = [(yt1, h + 22, f"Ø{do} s{co_cc}, x-riktning (ytterst)"), (yt2, h - 20, f"Ø{do} s{co_cc}, y-riktning"),
           (yb2, 48, f"Ø{du} s{cu_cc}, y-riktning"), (yb1, -12, f"Ø{du} s{cu_cc}, x-riktning (ytterst)")]
    for yb, yl, t in lab:
        ax.plot([W - 30, W + 60, W + 90], [yb, yl, yl], color=GRID, lw=0.4)
        ax.text(W + 95, yl, t, fontsize=6.4, va="center")
    ax.text(W / 2, -30, "C25/30, XC1, B500B", ha="center", va="top", fontsize=6.5, style="italic")
    ax.set_xlim(-80, W + 520); ax.set_ylim(-55, h + 40)
    ax.set_aspect("equal"); ax.axis("off")
    fig.savefig(path, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


if __name__ == "__main__":
    import laster
    G = json.load(open("bild/geometri.json"))
    rita_geometri("fig_geometri.svg", G)
    rita_laster("fig_laster.svg", G, laster.alla())


# ------------------------------------------------------------------ resultatfigurer
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.tri import Triangulation  # noqa: E402

BLA = LinearSegmentedColormap.from_list("bla", ["#f4f7fb", "#b7c9de", "#5d7fa6", "#2c4a6e"])
ROD = LinearSegmentedColormap.from_list("rod", ["#fbf5f3", "#e2bdb3", "#c0796a", "#8a3b2e"])
GRA = LinearSegmentedColormap.from_list("gra", ["#f6f6f4", "#cfd3d8", "#8f969e", "#3a3f45"])


def _bas(ax, G, pelare=True, vaggar=True, etiketter=False):
    """Plattans kontur, trapphål, väggar (tunt) och rör som underlag i resultatplanerna."""
    if vaggar:
        for w in G["vagg"]:
            k, h_, L = vaggband(w, G["E"], G["vagg"])
            g = h_.intersection(SPoly(G["kontur"]).buffer(0))
            for gg in getattr(g, "geoms", [g]):
                ax.add_patch(Polygon(list(gg.exterior.coords), closed=True, fc="none", ec="#7d7d7d", lw=0.35,
                                     zorder=6))
    ax.add_patch(Polygon(G["kontur"], closed=True, fc="none", ec=INK, lw=0.8, zorder=7))
    ax.add_patch(Polygon(G["hal"], closed=True, fc="white", ec=INK, lw=0.6, zorder=7))
    if pelare:
        for i, (x, y) in enumerate(G["pelare"], 1):
            ax.add_patch(Rectangle((x - 60, y - 60), 120, 120, fc=INK, ec="white", lw=0.3, zorder=8))
            if etiketter:
                ax.text(x + 120, y + 100, f"P{i}", fontsize=5.6, zorder=9, path_effects=HALO)
    ax.set_xlim(-300, 14100); ax.set_ylim(-300, 16200)
    ax.set_aspect("equal"); ax.axis("off")


def _konturplot(ax, xy, tri, z, cmap, nivaer, G, maske=None):
    T = Triangulation(xy[:, 0], xy[:, 1], tri)
    if maske is not None:
        T.set_mask(maske)
    cs = ax.tricontourf(T, z, levels=nivaer, cmap=cmap, extend="max", zorder=1)
    return cs, T


def rita_moment(path, G, F, R):
    """Dimensionerande moment i under- och överkant (utjämnade), med nätets bärförmåga markerad."""
    xy, tri = F["xy"], F["tri"]
    uk = np.maximum(F["s_mux"], F["s_muy"]) / 1e3
    ok = np.maximum(-F["s_mox"], -F["s_moy"]) / 1e3
    fig, axs = plt.subplots(1, 2, figsize=(6.85, 4.35))
    b = R["bojning"]
    for ax, z, cmap, titel, mrd in ((axs[0], uk, BLA, "Underkant", min(b["uk"]["MRd_x"], b["uk"]["MRd_y"]) / 1e3),
                                     (axs[1], ok, ROD, "Överkant", min(b["ok"]["MRd_x"], b["ok"]["MRd_y"]) / 1e3)):
        niv = np.arange(0, 16.1, 2)
        cs, T = _konturplot(ax, xy, tri, np.clip(z, 0, None), cmap, niv, G)
        ax.tricontour(T, z, levels=[mrd], colors=[INK], linewidths=0.8, zorder=5)
        _bas(ax, G)
        if titel == "Överkant":
            for zn in R["zoner"]:
                x0, y0, x1, y1 = zn["bounds"]
                ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc="none", ec=INK, lw=0.5, ls=(0, (3, 2)), zorder=6))
        ax.set_title(f"{titel}: största av $m_x$, $m_y$ (kNm/m)", fontsize=7.5, pad=3)
        txt = (f"heldragen linje: nätets bärförmåga {sv(mrd, 1)} kNm/m" if z.max() > mrd else
               f"nätets bärförmåga {sv(mrd, 1)} kNm/m nås inte")
        ax.text(7000, -700, txt, ha="center", va="top", fontsize=6.3, style="italic", color="#444")
        cb = fig.colorbar(cs, ax=ax, orientation="horizontal", fraction=0.04, pad=0.08, aspect=40)
        cb.ax.tick_params(labelsize=6); cb.outline.set_linewidth(0.4)
    fig.subplots_adjust(wspace=0.04, left=0.01, right=0.99, top=0.95, bottom=0.04)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


def rita_nedbojning(path, G, N, R):
    """Långtidsnedböjning enligt 7.4.3 (kvasipermanent last)."""
    fig, axs = plt.subplots(1, 2, figsize=(6.85, 4.35))
    for ax, w, titel in ((axs[0], N["w"], "EC2 7.4.3, kvasipermanent last"),
                         (axs[1], N["w_spr"], "Helt sprucken, karakteristisk last, φ = 3")):
        ejm = N["ej_mark"] if "ej_mark" in N else np.ones(len(w), bool)
        top = max(1.0, float(np.ceil(N["w_spr"][ejm].max())))
        niv = np.arange(0, top + 0.01, 0.5)
        ej = N["ej_mark"] if "ej_mark" in N else np.ones(len(w), bool)
        maske = ~ej[N["tri"]].any(axis=1)
        cs, T = _konturplot(ax, N["xy"], N["tri"], np.clip(w, 0, None), GRA, niv, G, maske=maske)
        ax.add_patch(Polygon(G["mark"], closed=True, fc=MARK, ec="none", hatch="....", zorder=0.5, lw=0))
        _bas(ax, G)
        ax.set_title(f"{titel} (mm)", fontsize=7.5, pad=3)
        i = int(np.argmax(np.where(ej, w, -1e9)))
        ax.plot(*N["xy"][i], marker="o", ms=4, mfc="white", mec=INK, mew=0.7, zorder=10)
        ax.text(N["xy"][i][0] + 250, N["xy"][i][1], f"{sv(w[i], 1)} mm", fontsize=6.5, va="center", zorder=10,
                path_effects=HALO)
        cb = fig.colorbar(cs, ax=ax, orientation="horizontal", fraction=0.04, pad=0.04, aspect=40)
        cb.ax.tick_params(labelsize=6); cb.outline.set_linewidth(0.4)
        cb.ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, p: sv(v, 1)))
    fig.subplots_adjust(wspace=0.04, left=0.01, right=0.99, top=0.95, bottom=0.04)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
