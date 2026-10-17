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
from figurer import INK, BETONG, KARNA, EPS, STAL, FRI, HALO, sv  # noqa: E402

G = I.G05
MARKF = "#efe6d2"
EPSF = "#f3f6fa"
EPS2 = "#dde6f0"
JORD = "#d9cbb0"
DRAN = "#c7c2b8"
BLA = "#2c4a6e"
ROD = "#b5463a"
BRUN = "#8a6d3b"
GIPS = "#ffffff"
STEN = "#b9bcc0"


def _vaggar(ax, poly, lw=0.35):
    """Källarväggarna i plan: hela väggen (cellplast, 350) och den sammanhängande betongkärnan (150) ovanpå."""
    for j, fc, z in ((1, EPS, 4), (0, KARNA, 4.5)):
        u = unary_union([F05.vaggband(w, G["E"] + I.KI, G["vagg"])[j] for w in G["vagg"]]).intersection(poly.buffer(1))
        for p in getattr(u, "geoms", [u]):
            if p.area > 1:
                ax.add_patch(Polygon(list(p.exterior.coords), closed=True, fc=fc, ec=INK, lw=lw, zorder=z))
                for h in p.interiors:
                    ax.add_patch(Polygon(list(h.coords), closed=True, fc="none", ec=INK, lw=lw, zorder=z))


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
                "V11": (6210, 560), "V12": (7695, 560), "V16": (9975, 11615)}.get(f"V{i}", (x, y))
        ax.text(x, y, f"V{i}", fontsize=5.6, ha="center", va="center", color="#555", style="italic", rotation=rot,
                zorder=9, path_effects=HALO)


def rita_kallare(path, R, poly):
    """Källaren: väggarna (Kub 350-150), fyllningen mot väggarna och rören."""
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
    for v in R["vaggar"]:
        if max(v["fyll"]) <= 0:
            continue
        ax_, c, a, b = v["ax"], v["c"], v["a"], v["b"]
        if ax_ == "h":
            s = 1 if not poly.contains(Point((a + b) / 2, c + 400)) else -1
            p0, p1 = (a, c + s * 260), (b, c + s * 260)
            tx, ty, rot = (a + b) / 2, c + s * 520, 0
        else:
            s = 1 if not poly.contains(Point(c + 400, (a + b) / 2)) else -1
            p0, p1 = (c + s * 260, a), (c + s * 260, b)
            tx, ty, rot = c + s * 560, (a + b) / 2, 90
        col = ROD if v["platta"] else BRUN
        # kapa linjen där den möter en annan väggs fyllning (inåtgående hörn utanför källaren)
        seg = LineString([p0, p1]).difference(poly.buffer(60, join_style=2))
        for g in getattr(seg, "geoms", [seg]):
            if g.length > 1:
                ax.plot(*g.xy, color=col, lw=2.2, solid_capstyle="butt", zorder=5)
        h0, h1 = v["fyll"]
        nd = lambda h: 1 if abs(h - round(h, 1)) < 1e-9 else 2
        txt = sv(h0, nd(h0)) + " m" if abs(h0 - h1) < 1e-6 else f"{sv(h0, nd(h0))} → {sv(h1, nd(h1))} m"
        ax.text(tx, ty, txt, ha="center", va="center", fontsize=6.0, rotation=rot, color="#6b5320" if not v["platta"]
                else ROD, zorder=9, path_effects=HALO)
    ax.text(6900, -1000, "fasad med öppningar: fyllning under fönstren", ha="center", fontsize=6.5)
    items = [(Rectangle((0, 0), 1, 1, fc=KARNA, ec=INK, lw=0.35), "Kub 350-150: betongkärna 150"),
             (Rectangle((0, 0), 1, 1, fc=EPS, ec=INK, lw=0.35), "cellplast 100 på var sida"),
             (plt.Line2D([0], [0], color=BRUN, lw=2.2), "fyllning mot väggen (höjd över bottenplattan)"),
             (plt.Line2D([0], [0], color=ROD, lw=2.2), "fyllning före mellanbjälklaget (V3, V20)"),
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
    for g in (kant, inre):
        for p in getattr(g, "geoms", [g]):
            ax.add_patch(Polygon(list(p.exterior.coords), closed=True, fc="#d7d3cb", ec=INK, lw=0.4, hatch="////",
                                 zorder=2))
            for h in p.interiors:
                ax.add_patch(Polygon(list(h.coords), closed=True, fc=EPSF, ec=INK, lw=0.4, zorder=2))
    import modell06 as M
    for (namn, x, y, bx, by, antal), b in zip(M.ROR, plint_b):        # plinten centrerad under stödet (P7: två rör)
        ax.add_patch(Rectangle((x - b / 2, y - b / 2), b, b, fc="#e2bdb3", ec=INK, lw=0.5, zorder=3))
        fb = 200 + (bx - 80)                                            # fotplåt 200 × 200, vid två rör 280 × 200
        ax.add_patch(Rectangle((x - fb / 2, y - 100), fb, 200, fc=STAL, ec="none", zorder=4))
        ax.text(x, y - b / 2 - 90, f"{namn} {sv(b)}", ha="center", va="top", fontsize=5.3, zorder=9, path_effects=HALO)
    for b, bis in F05.inatgaende_horn(list(poly.exterior.coords)[:-1]):
        t = np.array([-bis[1], bis[0]])
        for off in (150, 250):
            c = b + bis * off
            p0, p1 = c - t * 600, c + t * 600
            ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color=FRI, lw=0.9, zorder=8, solid_capstyle="butt")
    ax.add_patch(Polygon(list(M.ytterkontur().exterior.coords), closed=True, fc="none", ec=INK, lw=0.5, ls="--",
                         zorder=5))
    items = [(Rectangle((0, 0), 1, 1, fc="#d7d3cb", ec=INK, lw=0.4, hatch="////"),
              "kantbalk och balk under innervägg, 450 bred, på S300"),
             (plt.Line2D([0], [0], color=INK, lw=0.5, ls="--"), "L-elementens ytterkant, väggarnas ytterliv"),
             (Rectangle((0, 0), 1, 1, fc="#e2bdb3", ec=INK, lw=0.5), "plint under rör (sida i mm)"),
             (plt.Line2D([0], [0], color=FRI, lw=0.9), "2 Ø10, L = 1,2 m, överkant, inåtgående hörn"),
             (Rectangle((0, 0), 1, 1, fc=EPSF, ec=INK, lw=0.5), "platta 100 mm på cellplast")]
    ax.legend([i for i, _ in items], [t for _, t in items], loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=2,
              frameon=False, fontsize=6.4, handlelength=1.8, handleheight=1.0)
    ax.set_xlim(-400, 14300); ax.set_ylim(-500, 12900)
    ax.set_aspect("equal"); ax.axis("off")
    fig.savefig(path, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


def rita_tryck(path, P_xy, tri, p, w, poly, tjock, p_max=None, w_niv=None):
    """Cellplastens tryck (brottgräns, omhyllande) och långtidssättning (kvasipermanent)."""
    fig, axs = plt.subplots(1, 2, figsize=(6.4, 3.6))
    T = Triangulation(P_xy[:, 0], P_xy[:, 1], tri)
    pn = np.arange(0, (p_max or 85) + 1, 5)
    wn = w_niv if w_niv is not None else np.arange(0.6, 1.75, 0.1)
    for ax, z, lev, cm, titel in ((axs[0], p, pn, "YlOrBr", "Tryck mot cellplasten, brottgräns (kPa)"),
                                  (axs[1], w, wn, "Blues", "Sättning, långtid (mm)")):
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


def rita_jordtryck(path, kurvor):
    """Vänster: horisontaltrycket mot en vägg med 2,0 m fyllning (vilojordtryck, packningstryck, dimensionerande).
    Höger: momentet i den lodräta strimlan och bärförmågan med Ø10 s300 och Ø10 s200."""
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.2, 3.1), gridspec_kw=dict(width_ratios=(1, 1.15), wspace=0.35))
    y, k0, komp, dim = kurvor["y"], kurvor["K0"], kurvor["komp"], kurvor["p_d"]
    hf = kurvor["hf"]
    a1.fill_betweenx(y, 0, dim, color="#efe6d2", lw=0)
    a1.plot(k0, y, color=BRUN, lw=0.9, ls="--", label="vilojordtryck $K_0 \\gamma z$")
    a1.plot(komp, y, color=BLA, lw=1.1, label="med packningstrycket (Ingold)")
    a1.plot(dim, y, color=INK, lw=0.9, label="dimensionerande, 6.10a")
    a1.axhline(hf, color="#888", lw=0.5, ls=":")
    a1.text(1, hf + 0.03, f"markyta, {sv(hf, 1)} m", fontsize=6, color="#555", va="bottom")
    a1.set_xlim(0, max(dim) * 1.15); a1.set_ylim(0, 3.0)
    a1.set_xlabel("Tryck (kPa)", fontsize=7); a1.set_ylabel("Höjd över bottenplattan (m)", fontsize=7)
    a1.legend(fontsize=5.8, frameon=False, loc="upper right")
    ym, M = kurvor["ym"], kurvor["M"]
    a2.plot(M, ym, color=INK, lw=1.1, label="$M_{Ed}$, jordtryck och lasterna över väggen")
    for MR, lab, ls in kurvor["MRd"]:
        a2.axvline(MR, color=ROD if "300" in lab else BLA, lw=0.8, ls=ls, label=lab)
    a2.set_xlim(0, max(r[0] for r in kurvor["MRd"]) * 1.1); a2.set_ylim(0, 3.0)
    a2.axhline(kurvor["Ls"], color="#888", lw=0.5, ls=":")
    a2.text(0.3, kurvor["Ls"] + 0.03, "mellanbjälklagets mittplan", fontsize=6, color="#555", va="bottom")
    a2.set_xlabel("Moment (kNm/m), drag i insidan", fontsize=7)
    a2.legend(fontsize=5.8, frameon=False, loc="upper right")
    for a in (a1, a2):
        a.tick_params(labelsize=6.5)
        for sp in ("top", "right"):
            a.spines[sp].set_visible(False)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


def rita_hardning(path, fck_t, mognad, krav, frys, temp=(5, 10, 15, 20)):
    """Betongens hållfasthet f_ck(t) mot kalenderdygn vid olika medeltemperatur (N- och R-cement) med kravet för
    återfyllning och frysgränsen."""
    fig, ax = plt.subplots(figsize=(6.0, 2.8))
    dagar = np.linspace(0.5, 21, 300)
    farg = dict(zip(temp, ("#2c4a6e", "#5d7fa6", "#c0796a", "#8a3b2e")))
    for T in temp:
        for c, s, ls in (("N", 0.25, "-"), ("R", 0.20, "--")):
            f = [fck_t(d * mognad(T), s=s) for d in dagar]
            ax.plot(dagar, f, color=farg[T], lw=1.0, ls=ls, label=f"{sv(T)} °C" if c == "N" else None)
    ax.axhline(krav, color=INK, lw=0.8)
    ax.text(20.8, krav + 0.4, f"återfyllning: $f_{{ck}}(t)$ ≥ {sv(krav)} MPa", ha="right", va="bottom", fontsize=6.3)
    ax.axhline(frys, color="#888", lw=0.6, ls=":")
    ax.text(20.8, frys + 0.4, f"får frysa: {sv(frys)} MPa", ha="right", va="bottom", fontsize=6.3, color="#555")
    ax.set_xlim(0, 21); ax.set_ylim(0, 31)
    ax.set_xticks(range(0, 22, 3))
    ax.set_xlabel("Dygn efter gjutning, konstant medeltemperatur", fontsize=7)
    ax.set_ylabel("$f_{ck}(t)$ (MPa)", fontsize=7)
    ax.tick_params(labelsize=6.5)
    h, l = ax.get_legend_handles_labels()
    h += [plt.Line2D([0], [0], color="#666", lw=1.0), plt.Line2D([0], [0], color="#666", lw=1.0, ls="--")]
    l += ["cement klass N", "cement klass R"]
    ax.legend(h, l, fontsize=6.0, frameon=False, loc="upper center", ncol=6, bbox_to_anchor=(0.5, -0.2))
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


# ------------------------------------------------------------------ detalj: vägg mot bottenplatta och bjälklag
def _rekt(ax, x0, y0, w, h, fc, ec=INK, lw=0.4, hatch=None, z=2, ls="-"):
    ax.add_patch(Rectangle((x0, y0), w, h, fc=fc, ec=ec, lw=lw, hatch=hatch, zorder=z, ls=ls))


def rita_detalj(path, arm, h_balk=200.0, t_eps=200.0):
    """Sektion genom yttervägg mot jord (Kub 350-150) på kantbalk i L-element (höjd 300), med mellanbjälklaget.
    Mått i mm, x = 0 i väggens ytterliv, y = 0 bottenplattans överkant. Väggen visas med ett avbrott.
    Numrerade hänvisningar med en lista till höger."""
    W, Hf = 6.6, 5.0
    fig = plt.figure(figsize=(W, Hf))
    t_fot, hp = I.T_FOT, I.H_PLATTA
    yb = -h_balk
    ybot = yb - t_fot
    H, hm = I.H_VAGG, I.H_MB
    k0, k1 = I.T_EPS_V, I.T_EPS_V + I.T_KARNA          # kärnans ytor
    xi = I.T_VAGG                                       # insida cellplast
    ym = 2000.0                                         # markyta vid väggen
    gap = (850.0, 1300.0)                               # avbrott i väggen
    xl, yl = (-1500, 1750), (ybot - 330, H + hm + 330)
    sk = (xl[1] - xl[0]) / (0.56 * W)                   # mm per tum
    ax = fig.add_axes([0.0, 0.5 - (yl[1] - yl[0]) / sk / Hf / 2, 0.56, (yl[1] - yl[0]) / sk / Hf])
    ax.set_xlim(*xl); ax.set_ylim(*yl); ax.set_aspect("equal"); ax.axis("off")
    # berg och makadam, cellplast, L-element
    _rekt(ax, -1500, ybot - 330, 3250, 180, "#cfcac2", hatch="xx", z=0)
    _rekt(ax, -1500, ybot - 150, 3250, 150, DRAN, z=0)
    # L-elementets rygg (100) och bredd (600) från ytterlivet, kantbalkens inre kant (550), ryggens avfasning (50)
    lb, bl, bk, fas = I.L_BEN, I.B_L, I.L_BEN + I.B_BALK, I.FAS
    _rekt(ax, bl, -hp - t_eps, 1750 - bl, t_eps / 2, EPSF)          # undre skiktet, från L-elementets fot
    _rekt(ax, bk, -hp - t_eps / 2, 1750 - bk, t_eps / 2, EPSF)      # övre skiktet, in över foten
    ax.plot([bk, 1750], [-hp - t_eps / 2] * 2, color=BLA, lw=0.8, ls=(0, (4, 2)), zorder=3)
    _rekt(ax, 0, ybot, bl, t_fot, EPS2)                  # L-elementets fot, S300
    ax.add_patch(Polygon([(0, yb), (lb, yb), (lb, -fas), (fas, 0), (0, 0)], closed=True, fc=EPS2, ec=INK, lw=0.5,
                         zorder=2))                      # ryggen under väggens cellplast, avfasad upptill
    ax.add_patch(Polygon([(lb, yb), (bk, yb), (bk, -hp), (1750, -hp), (1750, 0), (fas, 0), (lb, -fas)],
                         closed=True, fc=BETONG, ec=INK, lw=0.5, zorder=2))
    for x in (lb + 41, bk - 41):
        ax.add_patch(Circle((x, yb + 41), 9, fc=INK, zorder=5))        # på byglarna
        ax.add_patch(Circle((x, -42), 9, fc=INK, zorder=5))            # under överkantsnätet
    ax.plot([lb + 33, lb + 33, bk - 33, bk - 33], [-28, yb + 33, yb + 33, -28], color=INK, lw=0.6, zorder=5)
    ax.plot([lb + 30, 1750], [-hp + 33] * 2, color=INK, lw=0.5, zorder=5)     # näten går genom balken
    ax.plot([lb + 25, 1750], [-28] * 2, color=INK, lw=0.5, zorder=5)
    # väggen i två delar
    xs_h = (k0 + I.C_UT + 5, k1 - I.C_IN - 5)                       # vågräta järn
    x_v = k1 - I.C_IN - 10 - 5                                       # lodräta järn på insidan
    x_s = I.L_BEN + 41 + 14                                          # startjärn på utsidan, innanför balkens järn
    for y0, y1 in ((0, gap[0]), (gap[1], H)):
        _rekt(ax, 0, y0, k0, y1 - y0, EPS, z=3)
        _rekt(ax, k0, y0, I.T_KARNA, y1 - y0, KARNA, z=3)
        _rekt(ax, k1, y0, I.T_EPS_V, y1 - y0, EPS, z=3)
        _rekt(ax, xi, y0, 13, y1 - y0, GIPS, z=3)
        for yy in (600, 1200, 1800):
            if y0 < yy < y1:
                ax.plot([0, k0], [yy, yy], color="#8a8a8a", lw=0.3, zorder=4)
                ax.plot([k1, xi], [yy, yy], color="#8a8a8a", lw=0.3, zorder=4)
        for yy in (575, 1175, 1475, 1775, 2045):
            if y0 + 20 < yy < y1 - 10:
                for x in xs_h:
                    ax.add_patch(Circle((x, yy), 8, fc=INK, zorder=6))
    for yy in gap:
        ax.plot([-90, 440], [yy - 30, yy + 30], color=INK, lw=0.5, zorder=7)
    ax.plot([k0, k1], [I.H_GJUT1] * 2, color=INK, lw=0.7, ls=(0, (3, 1.5)), zorder=6)
    # järn
    ax.plot([x_v, x_v], [30, gap[0] - 15], color=FRI, lw=0.9, zorder=6)
    yv = H + hm - 25 - 16 - 5                            # vinkeljärnets vågräta ben, under överkantsnätet
    ax.plot([x_v, x_v], [gap[1] + 15, yv + 3], color=FRI, lw=0.9, zorder=6)
    ax.plot([x_v - 14, x_v - 14, x_v - 14 + I.VINKEL["in_"]], [yv - I.VINKEL["ned"], yv, yv], color=FRI, lw=0.9,
            zorder=6)
    ax.plot([x_s + 330, x_s, x_s], [yb + 41, yb + 41, gap[0] - 15], color=FRI, lw=0.9, zorder=6)   # foten in i balken
    # mellanbjälklaget och kantisoleringen; den yttre cellplasten i översta skiftet slutar i bjälklagets underkant
    ax.add_patch(Polygon([(I.KI, H), (1750, H), (1750, H + hm), (I.KI, H + hm)], closed=True, fc=BETONG, ec=INK,
                         lw=0.5, zorder=3))
    _rekt(ax, k0 + 0.4, H - 1, I.T_KARNA - 0.8, 2, KARNA, ec="none", z=3.5)
    _rekt(ax, 0, H, I.KI, hm, EPS, z=3)
    ax.plot([I.KI + 25, 1750], [H + hm - 33, H + hm - 33], color=INK, lw=0.5, zorder=6)
    ax.plot([I.KI + 25, 1750], [H + 28, H + 28], color=INK, lw=0.5, zorder=6)
    xc = I.KI + 17.5                                     # plan 1: ytterväggens centrum
    _rekt(ax, xc - 47.5, H + hm, 95, 45, "#e9dcc3", z=3)
    ax.annotate("", (xc, H + hm + 45), (xc, H + hm + 260),
                arrowprops=dict(arrowstyle="-|>", lw=0.8, color=BLA, mutation_scale=8), zorder=8)
    # utsida
    ax.plot([-6, -6], [yb + 40, ym + 60], color=INK, lw=0.7, ls=(0, (1.2, 1.0)), zorder=4)
    _rekt(ax, -55, ym - 50, 40, H + hm - ym + 50, STEN, z=3)
    _rekt(ax, -15, ym - 50, 15, H + hm - ym + 50, "#e8e6e1", z=3)
    ax.add_patch(Polygon([(-1500, ybot), (-60, ybot), (-60, ym), (-1500, ym - 70)], closed=True,
                         fc="#ece3cf", ec="none", zorder=1))
    ax.plot([-1500, -60], [ym - 70, ym], color=INK, lw=0.7, zorder=4)
    ax.add_patch(Circle((-330, ybot + 70), 55, fc="white", ec=INK, lw=0.6, zorder=5))
    ax.plot([-1500, -60], [ybot - 4] * 2, color="#666", lw=0.5, ls=(0, (3, 1.5)), zorder=4)
    # mått: skikten och höjderna
    def mattx(x0, x1, y, txt):
        ax.annotate("", (x0, y), (x1, y), arrowprops=dict(arrowstyle="<->", lw=0.4, color=INK, shrinkA=0, shrinkB=0))
        ax.text((x0 + x1) / 2, y + 18, txt, fontsize=5.6, ha="center", va="bottom")
    ym_ = (gap[0] + gap[1]) / 2
    for x0, x1 in ((0, k0), (k0, k1), (k1, xi)):
        ax.plot([x0, x0], [ym_ - 60, ym_ + 60], color=INK, lw=0.3)
        mattx(x0, x1, ym_, sv(x1 - x0))
    ax.plot([xi, xi], [ym_ - 60, ym_ + 60], color=INK, lw=0.3)

    def matty(x, y0, y1, txt):
        ax.annotate("", (x, y0), (x, y1), arrowprops=dict(arrowstyle="<->", lw=0.4, color=INK, shrinkA=0, shrinkB=0))
        ax.text(x + 25, (y0 + y1) / 2, txt, fontsize=5.6, ha="left", va="center", rotation=90)
    matty(1150, I.H_GJUT1, H, sv(H - I.H_GJUT1))
    matty(1150, H, H + hm, sv(hm))
    ax.plot([xi + 13, 1190], [I.H_GJUT1] * 2, color=INK, lw=0.3)
    dia, s = arm
    lst = [("mellanbjälklag 150 (K-05), gjuts med det översta halva skiftet", (1200, H + hm - 70), (1300, H + hm + 230)),
           (f"vinkeljärn Ø{dia} s{s} till bjälklaget, {sv(I.VINKEL['ned'])} + {sv(I.VINKEL['in_'])}, under nätet",
            (600, yv), (900, H + 330)),
           ("kantisolering 30; bjälklaget går 70 mm ut över cellplasten", (15, H + hm / 2), (-300, H + hm + 120)),
           ("ytterväggen på plan 1, centrum 52,5 mm utanför kärnan", (xc, H + hm + 200), (-250, H + hm + 290)),
           ("fasadsten 40 mm på armeringsbruk (AR-01)", (-35, 2150), (-450, 2280)),
           ("gjutfog: de tre hela skiften gjuts först, 1 800", (k0 + 20, I.H_GJUT1), (-300, 1820)),
           ("Sundolitt Kub 350-150: cellplast 100 + betong 150 + cellplast 100", (k0 + 75, 1600), (-400, 1600)),
           (f"lodräta järn Ø{dia} s{s} på insidan, upp till bjälklagets överkantsnät", (x_v, 1550), (900, 1650)),
           ("2 Ø10 per skift, ett vid var yta (s600; s300 i de två översta)", (xs_h[1], 1475), (900, 1420)),
           ("gips 13 mm, ingen ångspärr", (xi + 7, 1150 - 500), (900, 650)),
           (f"startjärn Ø{I.STARTJARN['d']} s{I.STARTJARN['s']} på utsidan, 1 200 upp, foten 330 in i kantbalken",
            (x_s, 450), (-400, 450)),
           (f"kantbalk 450 × {sv(h_balk)}: 2 Ø10 uk + 2 Ø10 ök, U-byglar Ø6 s600", (509, yb + 41), (700, yb - 60)),
           ("platta 100: Ø6 s150 i över- och underkant", (1300, -hp + 33), (1450, 200)),
           (f"cellplast {sv(t_eps)} mm S100 i två skikt, plastfolie mellan; det övre {sv(I.OMLOTT)} mm in över "
            "L-elementets fot", (1300, -hp - t_eps * 0.25), (1600, -230)),
           (f"L-element S300, höjd {sv(h_balk + t_fot)}, bredd {sv(I.B_L)} (t.ex. Finja): ryggen under väggens cellplast, "
            "avfasad upptill, fot 100 mm S300", (275, ybot + 50), (300, ybot - 230)),
           ("grundmursskiva, knopparna mot väggen, list upptill", (-6, 1100), (-400, 1150)),
           ("dränerande fyllning; inom 1 m lager ≤ 0,2 m och lätt vibroplatta", (-800, 600), (-1100, 900)),
           ("dränledning, vattengång under plattans cellplast", (-330, ybot + 70), (-700, ybot + 230)),
           ("makadam på sprängt berg", (-1000, ybot - 75), (-1300, ybot - 230)),
           ("fall från huset ≥ 1:50 över 3 m", (-1000, ym - 50), (-1250, ym + 230))]
    for k, (txt, (px, py), (lx, ly)) in enumerate(lst, 1):
        ax.annotate(str(k), (px, py), (lx, ly), fontsize=5.8, ha="center", va="center", zorder=15,
                    bbox=dict(boxstyle="circle,pad=0.18", fc="white", ec=INK, lw=0.45),
                    arrowprops=dict(arrowstyle="-", lw=0.4, color="#333", shrinkA=0, shrinkB=0))
    y0 = 0.5 + 0.5 * len(lst) * 0.205 / Hf
    for k, (txt, _, _) in enumerate(lst, 1):
        fig.text(0.585, y0 - k * 0.205 / Hf, f"{k}", fontsize=6.3, ha="right", va="center")
        fig.text(0.60, y0 - k * 0.205 / Hf, txt, fontsize=6.3, ha="left", va="center")
    fig.savefig(path, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


def rita_lokala(path, h_balk=200.0, t_eps=200.0):
    """Lokala detaljer (L300) i skala 1 tum = 550 mm, med numrerade hänvisningar: (a) plint under rör, (b) balk
    under innervägg, (c) yttre hörn i plan, (d) V3 mot V19/V20 i plan. Mått i mm."""
    SK = 550.0                                         # mm per tum
    W, Hf = 6.9, 5.45
    fig = plt.figure(figsize=(W, Hf))
    hp, tf = I.H_PLATTA, I.T_FOT
    yb, ybot = -h_balk, -h_balk - tf
    k0, kt, e = I.T_EPS_V, I.T_KARNA, I.T_EPS_V

    def panel(x_in, y_in, xl, yl):
        w, h = (xl[1] - xl[0]) / SK, (yl[1] - yl[0]) / SK
        ax = fig.add_axes([x_in / W, y_in / Hf, w / W, h / Hf])
        ax.set_xlim(*xl); ax.set_ylim(*yl); ax.set_aspect("equal"); ax.axis("off")
        return ax

    def R(ax, x0, y0, w, h, fc, ec=INK, lw=0.4, hatch=None, z=2, ls="-"):
        ax.add_patch(Rectangle((x0, y0), w, h, fc=fc, ec=ec, lw=lw, hatch=hatch, zorder=z, ls=ls))

    def P(ax, pts, fc, z=2, ec=INK, lw=0.5):
        ax.add_patch(Polygon(pts, closed=True, fc=fc, ec=ec, lw=lw, zorder=z))

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
    matt(ax, -b_ / 2, b_ / 2, ybot - 50, "b = 600–1 200")
    la = [("rör VKR 80×80×4 (K-05), svetsas på plåten", (40, 350), (300, 420)),
          ("fotplåt 200 × 200 × 15 S355, gjuts in i plinten", (-100, -8), (-420, 300)),
          ("4 svetsbultar Ø13, L = 75 mm", (-60, -70), (-420, 160)),
          ("platta 100: Ø6 s150 i över- och underkant", (-700, -28), (-700, 200)),
          ("plint: Ø8 s150 i underkant, båda riktningarna", (300, yb + 34), (650, 160)),
          (f"cellplast S300, {sv(tf)} mm under plinten", (200, yb - 50), (650, -330)),
          (f"cellplast S100, {sv(t_eps)} mm i två skikt", (-700, -200), (-700, -330))]
    nummer(ax, la)
    lista(0.1, 3.6, "a) Plint under rör", la)

    # ---------------------------------------------------------------- b) balk under innervägg
    xl, yl = (-800, 800), (-400, 470)
    ax = panel(0.25, 0.95, xl, yl)
    grund(ax, -750, 750, -225, 225)
    for x in (-165, 165):
        dot(ax, x, yb + 41); dot(ax, x, -42)
    ax.plot([-180, -180, 180, 180], [-28, yb + 33, yb + 33, -28], color=INK, lw=0.7, zorder=6)
    R(ax, -175, 0, e, 450, EPS, z=3); R(ax, -75, 0, kt, 450, KARNA, z=3); R(ax, 75, 0, e, 450, EPS, z=3)
    ax.plot([0, 0], [yb + 41, 420], color=FRI, lw=0.9, zorder=6)          # i kärnans mitt, foten längs balken
    ax.add_patch(Circle((0, yb + 41), 11, fc=FRI, zorder=7))
    brott(ax, -230, 230, 400)
    matt(ax, -225, 225, ybot - 50, "450")
    ld = [("innervägg Kub 350-150 (V4–V6, V15, V19)", (0, 250), (-500, 330)),
          ("startjärn Ø10 s300 i kärnans mitt, 1 200 upp, foten längs balken", (0, 120), (-520, 150)),
          ("2 Ø10 i överkant", (165, -42), (520, 160)),
          ("U-byglar Ø6 s600", (175, -110), (520, -20)),
          ("2 Ø10 i underkant", (165, yb + 41), (520, -330)),
          (f"cellplast S300, {sv(tf)} mm under balken", (-120, yb - 50), (-520, -330))]
    nummer(ax, ld)
    lista(0.1, 0.8, "b) Balk under innervägg", ld)

    # ---------------------------------------------------------------- c) yttre hörn i plan
    L_ = 1050.0
    xl, yl = (-250, 1100), (-250, 1050)
    ax = panel(3.85, 3.7, xl, yl)
    # väggarna: x = 0 och y = 0 i ytterlivet, väggarna inåt positivt
    for poly_, fc in (([(0, 0), (L_, 0), (L_, 350), (350, 350), (350, L_), (0, L_)], EPS),
                      ([(k0, k0), (L_, k0), (L_, k0 + kt), (k0 + kt, k0 + kt), (k0 + kt, L_), (k0, L_)], KARNA)):
        P(ax, poly_, fc, z=2)
    xo, xi_ = k0 + I.C_UT + 5, k0 + kt - I.C_IN - 5                   # vågräta järn vid utsidan och insidan
    lv = 750.0
    for x_ in (xo, xi_):                                               # vinkeljärn 750 + 750
        ax.plot([x_, x_, x_ + lv], [x_ + lv, x_, x_], color=FRI, lw=0.9, zorder=6)
    for x_, dx in ((xo, 14), (xi_, -14)):                              # raka järn, skarv 500 med vinkeljärnen
        ax.plot([x_ + lv - 500, L_ - 10], [x_ + dx] * 2, color=INK, lw=0.7, zorder=5)
        ax.plot([x_ + dx] * 2, [x_ + lv - 500, L_ - 10], color=INK, lw=0.7, zorder=5)
    brott(ax, L_ - 40, L_ + 20, 175)
    brott(ax, 145, 205, L_ - 10)
    ax.annotate("", (xo, -120), (xo + lv, -120), arrowprops=dict(arrowstyle="<->", lw=0.45, color=INK))
    ax.text(xo + lv / 2, -140, "750", fontsize=6.0, ha="center", va="top")
    ax.annotate("", (xo + lv - 500, -60), (xo + lv, -60), arrowprops=dict(arrowstyle="<->", lw=0.45, color=INK))
    ax.text(xo + lv - 250, -75, "500", fontsize=6.0, ha="center", va="top")
    lc = [("vinkeljärn Ø10, 750 + 750, vid båda ytorna, i varje skift", (xo, 600), (-150, 900)),
          ("vågräta järn, skarvas minst 500 med vinkeljärnen", (900, xo + 14), (950, -150)),
          ("betongkärna 150", (600, k0 + kt / 2), (950, 420)),
          ("cellplast 100", (600, 50), (950, 260))]
    nummer(ax, lc)
    ax.text(-180, -200, "ute (jord)", fontsize=6, color="#555", style="italic")
    ax.text(650, 700, "inne", fontsize=6, color="#555", style="italic")
    lista(3.6, 3.55, "c) Yttre hörn i plan, t.ex. V21/V3", lc)

    # ---------------------------------------------------------------- d) V3 mot V19/V20 i plan
    xl, yl = (-650, 1100), (-500, 600)
    ax = panel(3.75, 0.85, xl, yl)
    # V19/V20 lodrätt i bilden (x = −175…175), V3 åt höger (y = −175…175); fyllningen mellan V3 och V20 (uppe till
    # höger), källaren nedanför V3. Spegelvänd mot planen.
    P(ax, [(-175, -450), (175, -450), (175, -175), (1100, -175), (1100, 175), (175, 175), (175, 800), (-175, 800)],
      EPS, z=2)
    P(ax, [(-75, -450), (75, -450), (75, -75), (1100, -75), (1100, 75), (75, 75), (75, 800), (-75, 800)], KARNA, z=2)
    yo, yi = 75 - I.C_UT - 5, -75 + I.C_IN + 5                         # V3:s vågräta järn vid utsidan och insidan
    xf = -75 + I.C_UT + 5                                              # bortre ytan i V19/V20
    for y_, dy in ((yo, -14), (yi, 14)):
        ax.plot([1080, 400], [y_ + dy] * 2, color=INK, lw=0.7, zorder=5)
    ax.plot([900, xf, xf], [yo, yo, yo + 750 - (yo - xf) * 0], color=FRI, lw=0.9, zorder=6)
    ax.plot([900, xf + 18, xf + 18], [yi, yi, yi - 750 + 400], color=FRI, lw=0.9, zorder=6)
    brott(ax, 1040, 1100, 0)
    ld2 = [("V3: 2 Ø10 s300 i båda ytorna, hela höjden", (1000, yo - 14), (900, 400)),
           ("vinkeljärn Ø10 s300 från V3:s utsida genom kärnan, 750 längs V20:s bortre yta", (xf, 500), (-450, 600)),
           ("vinkeljärn Ø10 s300 från V3:s insida genom kärnan, 750 längs V19:s bortre yta", (xf + 18, -300),
            (-450, -350)),
           ("V20 och V19: betongkärnan går igenom", (0, 520), (420, 520))]
    brott(ax, -230, 230, 575)
    brott(ax, -230, 230, -475)
    nummer(ax, ld2)
    ax.text(600, 300, "fyllning", fontsize=6, color="#555", style="italic")
    ax.text(600, -300, "källare", fontsize=6, color="#555", style="italic")
    lista(3.6, 0.75, "d) V3 mot V19/V20 i plan (spegelvänd)", ld2)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
