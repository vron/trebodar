"""K-03: figurer – översikt i plan, takbalkens upplag, vindsugets zoner, takstolen och huvudstolpen. Mått i mm."""
import math
from pathlib import Path

import matplotlib

matplotlib.use("svg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.patches import Polygon, Rectangle  # noqa: E402
import numpy as np  # noqa: E402

FONTS = Path(__file__).parent.parent / ".fonts"
for _f in sorted(FONTS.glob("*.ttf")) if FONTS.is_dir() else []:
    font_manager.fontManager.addfont(str(_f))
plt.rcParams.update({"font.family": "Carlito", "font.size": 7.5, "svg.fonttype": "none", "axes.linewidth": 0.5,
                     "hatch.linewidth": 0.35})
INK, BLA, ROD, GRA = "#1e1e1e", "#2c4a6e", "#b5463a", "#8a8a8a"
TRA, LIMTRA, STAL, PLATTA = "#e9d7b0", "#dcc38f", "#5a5f66", "#f1efe9"
TYPF = {"ÅII": "#c98b3a", "ÅIY": "#d9b36a", "ÅYI": "#6f8fb3", "ÅYY": "#a9bcd2"}
CM = 1 / 2.54
BALK = dict(b=190.0, h=200.0)          # nock- och dalbalkens tvärsnitt (K-01); sätts av berakning.py ur indata


def _spara(fig, path):
    fig.savefig(path, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


def oversikt(path, GEO, G05, ST, STOLPAR, huvud, brister):
    """Plan: nock- och dalbalkar, takbalkar per typ, takstolar, takfönster och stolpar (K-05:s beteckningar)."""
    fig, ax = plt.subplots(figsize=(17 * CM, 16.2 * CM))
    ax.add_patch(Polygon(G05["kontur"], closed=True, fc=PLATTA, ec=GRA, lw=0.6, zorder=0))
    for r in GEO["takbalkar"]:
        ax.plot([r["x0"], r["x1"]], [r["y"]] * 2, color=TYPF[r["typ"]], lw=0.9, zorder=1, solid_capstyle="butt")
    for b in GEO["balkar"]:
        ax.add_patch(Rectangle((b["x"] - BALK["b"] / 2, b["y0"]), BALK["b"], b["y1"] - b["y0"], fc=STAL, ec="none", zorder=3))
        namn = {"N": "Nockbalk ", "D": "Dalbalk "}[b["namn"][0]] + b["namn"][1]
        yt = {"N1": 9800, "D2": 2100, "N3": 9300, "D4": 8600, "N5": 13600}[b["namn"]]
        ax.text(b["x"], yt, namn, rotation=90, ha="center", va="center", fontsize=6.3, color="white", zorder=4,
                bbox=dict(fc=STAL, ec="none", pad=0.8))
    for t in ST:
        xs = [s["x0"] for s in t["staver"] if s["z0"] > 2000] + [s["x1"] for s in t["staver"] if s["z0"] > 2000]
        ax.plot([min(xs), max(xs)], [t["y"]] * 2, color=BLA, lw=2.6, zorder=2, solid_capstyle="butt")
        namn = t["namn"].replace("Stol ", "")
        dy = -300 if namn.endswith("NO") else 300           # gavelstolarnas etikett utanför taket, NO under och SV över
        ax.text((min(xs) + max(xs)) / 2 + (650 if namn in ("1NO", "1SV") else 0), t["y"] + dy, f"takstol {namn}", fontsize=6.3,
                color=BLA, va="center", ha="center", zorder=6, bbox=dict(fc="white", ec="none", pad=0.4, alpha=0.85))
    for f in GEO["fonster"]:
        ax.add_patch(Rectangle((f["x0"], f["y0"]), f["x1"] - f["x0"], f["y1"] - f["y0"], fc="white", ec=INK, lw=0.6,
                               hatch="////", zorder=4))
        ax.text((f["x0"] + f["x1"]) / 2, (f["y0"] + f["y1"]) / 2, f"TF{f['nr']}", ha="center", va="center", fontsize=6.5,
                zorder=5, bbox=dict(fc="white", ec="none", pad=0.6))
    for s in STOLPAR:
        p = s["p"]
        fel = s["namn"] in brister
        ax.add_patch(Rectangle((p["x"] - 90, p["y"] - 90), 180, 180, fc=ROD if fel else INK, ec="none", zorder=7))
        txt = s["namn"]
        dy =-230 if p["y"] > 15000 or (p["y"] > 3000 and p["y"] < 3800) or p["y"] > 12000 or p["y"] < 100 else 230
        dx = -130 if p["x"] > 13000 or (p["x"] > 4400 and p["x"] < 4600 and p["y"] < 3700) else 130
        ax.text(p["x"] + dx, p["y"] + dy, txt, fontsize=6.0, color=ROD if fel else INK, va="center", ha="left" if dx > 0 else "right",
                zorder=8, bbox=dict(fc="white", ec="none", pad=0.3, alpha=0.8))
    hp = huvud["p"]                                         # huvudstolpen som de andra stolparna
    ax.add_patch(Rectangle((hp["x"] - 90, hp["y"] - 90), 180, 180, fc=INK, ec="none", zorder=7))
    ax.text(hp["x"] + 130, hp["y"] + 230, huvud["namn"], fontsize=6.0, color=INK, va="center", ha="left", zorder=8,
            bbox=dict(fc="white", ec="none", pad=0.3, alpha=0.8))
    h = [plt.Line2D([], [], color=TYPF[k], lw=1.6) for k in TYPF]
    lbl = ["ÅII nock–dal, mitten", "ÅIY nock–takfot, mitten", "ÅYI nock–dal, sidorna", "ÅYY nock–takfot, sidorna"]
    h += [plt.Line2D([], [], color=STAL, lw=4), plt.Line2D([], [], color=BLA, lw=2.6),
          Rectangle((0, 0), 1, 1, fc="white", ec=INK, hatch="////", lw=0.6),
          plt.Line2D([], [], marker="s", color=INK, ls="none", ms=4)]
    lbl += ["nock- och dalbalk (K-01)", "takstol", "takfönster", "stolpe (K-05:s last)"]
    if brister:
        h.append(plt.Line2D([], [], marker="s", color=ROD, ls="none", ms=4))
        lbl.append("stolpe som inte räcker eller saknas")
    ax.legend(h, lbl, loc="upper right", fontsize=6.3, frameon=True, framealpha=0.95, edgecolor="none", ncol=2,
              bbox_to_anchor=(1.0, 1.0), handlelength=2.0, columnspacing=1.0)
    ax.set_xlim(-600, 14400); ax.set_ylim(-600, 16500); ax.set_aspect("equal")
    ax.set_xticks(range(0, 14001, 2000)); ax.set_yticks(range(0, 16001, 2000))
    ax.tick_params(labelsize=6.3, length=2)
    ax.set_xlabel("x (mm)", fontsize=6.5, labelpad=1); ax.set_ylabel("y (mm)", fontsize=6.5, labelpad=1)
    ax.grid(lw=0.25, color="#d6d6d6", zorder=-1)
    _spara(fig, path)


def vindsug(path, GEO, ST, e10, cc_rand, cc_ovrigt):
    """Plan: ströläktens linjer (takbalkar och takstolar) med randzonerna, e10 [mm] i plan från gavelkanter och fria
    takfötter, där läkten skruvas tätare."""
    fig, ax = plt.subplots(figsize=(8.4 * CM, 10.6 * CM))
    vid_balk = lambda x, y: any(abs(x - b["x"]) < 160 and b["y0"] - 50 <= y <= b["y1"] + 50 for b in GEO["balkar"])
    linjer = [(r["x0"], r["x1"], r["y"]) for r in GEO["takbalkar"]]
    for t in ST:                                          # takstolarnas diagonaler bär också läkt
        linjer += [(d["x0"], d["x1"], t["y"]) for d in t["staver"] if "diag" in d["namn"]]
    # gavelkanterna per takfall: ytterst bland takfallets linjer (takfallet = linjerna mot samma nockbalk på samma sida)
    nock = [b["x"] for b in GEO["balkar"] if b["namn"].startswith("N")]
    fall = {}
    for x0, x1, y in linjer:
        n = min(nock, key=lambda v: min(abs(x0 - v), abs(x1 - v)))
        fall.setdefault((n, (x0 + x1) / 2 < n), []).append((x0, x1, y))
    for (n, _), ls in fall.items():
        y0, y1 = min(l[2] for l in ls), max(l[2] for l in ls)
        xa, xe = min(l[0] for l in ls), max(l[1] for l in ls)
        ax.add_patch(Rectangle((xa, y0 - 120), xe - xa, y1 - y0 + 240, fc="#f3f1ec", ec="none", zorder=0))
        for x0, x1, y in ls:
            if y - y0 < e10 - 120 or y1 - y < e10 - 120:  # gavelzonen
                ax.plot([x0, x1], [y, y], color=ROD, lw=0.9, zorder=3, solid_capstyle="butt")
                continue
            ax.plot([x0, x1], [y, y], color=BLA, lw=0.45, zorder=2, solid_capstyle="butt")
            for xe_, s in ((x0, 1), (x1, -1)):            # fri takfot: änden som inte ligger vid en balk
                if not vid_balk(xe_, y):
                    ax.plot([xe_, xe_ + s * e10], [y, y], color=ROD, lw=0.9, zorder=3, solid_capstyle="butt")
    for b in GEO["balkar"]:
        ax.plot([b["x"]] * 2, [b["y0"], b["y1"]], color=INK, lw=0.7, ls=(0, (6, 2, 1, 2)) if b["namn"][0] == "N" else "-",
                zorder=4)
    for f in GEO["fonster"]:
        ax.add_patch(Rectangle((f["x0"], f["y0"]), f["x1"] - f["x0"], f["y1"] - f["y0"], fc="white", ec=INK, lw=0.5, zorder=5))
    h = [plt.Line2D([], [], color=ROD, lw=1.6), plt.Line2D([], [], color=BLA, lw=0.8),
         plt.Line2D([], [], color=INK, lw=0.7, ls=(0, (6, 2, 1, 2))), plt.Line2D([], [], color=INK, lw=0.7)]
    ax.legend(h, [f"randzon: läktens skruv c/c {cc_rand}", f"innerzon: c/c {cc_ovrigt}", "nockbalk", "dalbalk"], loc="upper right",
              fontsize=6.3, frameon=True, framealpha=0.95, edgecolor="none", handlelength=2.0, borderpad=0.3)
    ax.set_xlim(-500, 14300); ax.set_ylim(-500, 18400); ax.set_aspect("equal")
    ax.set_xticks(range(0, 14001, 2000)); ax.set_yticks(range(0, 16001, 2000))
    ax.tick_params(labelsize=6.0, length=2)
    ax.set_xlabel("x (mm)", fontsize=6.3, labelpad=1); ax.set_ylabel("y (mm)", fontsize=6.3, labelpad=1)
    _spara(fig, path)


def upplag(path, UP, TB, h_ef):
    """Takbalkens upplag mot nock- eller dalbalken: upplagsregel på balkens sida, hak i takbalken (snitt tvärs balken)."""
    fig, ax = plt.subplots(figsize=(11 * CM, 6.4 * CM))
    ta = math.tan(math.radians(30))
    H, pl, B = UP["balk_h"], UP["plat"], UP["balk_b"]
    rb, rh = UP["regel_b"], UP["regel_h"]
    hv = TB["h"] / math.cos(math.radians(30))
    zs = pl + rh                                          # sätets nivå
    ax.add_patch(Rectangle((-B / 2, 0), B, pl, fc=STAL, ec=INK, lw=0.5, zorder=3))
    ax.add_patch(Rectangle((-B / 2, H - pl), B, pl, fc=STAL, ec=INK, lw=0.5, zorder=3))
    ax.add_patch(Rectangle((-B / 2, pl), B, H - 2 * pl, fc=LIMTRA, ec=INK, lw=0.5, zorder=2))
    ax.text(0, H / 2, "nock- eller\ndalbalk\n(K-01)", ha="center", va="center", fontsize=6.3)
    for s in (1, -1):
        x0 = s * B / 2
        ax.add_patch(Rectangle((x0 if s > 0 else x0 - rb, pl), rb, rh, fc="#d9c08a", ec=INK, lw=0.5, zorder=3))
        top = lambda x: H - abs(x - x0) * ta
        und = lambda x: top(x) - hv
        xs, xr = x0 + s * 430, x0 + s * rb
        pts = [(x0, H), (xs, top(xs)), (xs, und(xs)), (xr, und(xr)), (xr, zs), (x0, zs)]
        ax.add_patch(Polygon(pts, closed=True, fc=TRA, ec=INK, lw=0.6, zorder=4))
        for zz in (pl + rh * 0.35, pl + rh * 0.7):
            ax.plot([x0 + s * (rb + 3), x0 - s * 55], [zz] * 2, color=INK, lw=0.9, zorder=6)
        xa = x0 + s * 120                                 # förankringsskruv: från takbalkens ovansida snett in i balken
        ax.plot([xa, x0 - s * 50], [top(xa) - 2, H - 135], color=ROD, lw=1.1, zorder=6)
    # hakets kvarvarande höjd vinkelrätt takbalken vid inre hörnet (höger sida)
    xr = B / 2 + rb
    ax.plot([xr, xr + (H - rb * ta - zs) * math.sin(math.radians(30)) * math.cos(math.radians(30))],
            [zs, zs + (H - rb * ta - zs) * math.cos(math.radians(30)) ** 2], color=BLA, lw=0.6, ls=(0, (2, 1)), zorder=7)
    ax.annotate(f"kvar vid hakets hörn:\n{h_ef:.0f} mm vinkelrätt takbalken", (xr + 20, zs + 40), (390, 300), fontsize=6.3, color=BLA,
                ha="left", va="center", arrowprops=dict(arrowstyle="-", lw=0.4, color=BLA))
    ax.annotate("upplagsregel 45×45 C24 på båda sidor,\nskruv Ø6×100 genom regeln in i limträet", (B / 2 + rb / 2, pl + rh / 2),
                (60, -330), fontsize=6.3, ha="left", va="center", zorder=9, arrowprops=dict(arrowstyle="-", lw=0.4, color=INK))
    ax.annotate("förankring mot lyft: skruv Ø6×160\nsnett genom takbalken in i balken", (-B / 2 - 60, H - 60), (-640, H + 95),
                fontsize=6.3, color=ROD, ha="left", va="center", arrowprops=dict(arrowstyle="-", lw=0.4, color=ROD))
    ax.text(-640, -330, "takbalk 45×170 C24, c/c 600, 30°.\nTakbalkens överkant i balkens överkant.", fontsize=6.3, ha="left", va="center")
    ax.set_xlim(-650, 680); ax.set_ylim(-390, 360); ax.set_aspect("equal"); ax.axis("off")
    _spara(fig, path)


def takstol(path, t, Pd, H, V):
    """Takstolen i elevation ur modellen, med laster och krafter: stavarna med sina snitt, toppklossen, plåtarna och
    nockbalken på sätet."""
    fig, ax = plt.subplots(figsize=(16 * CM, 6.2 * CM))
    import spikplat as SPK
    X_ = [s for s in t["staver"] if "extra" in s["namn"]]
    for s in t["staver"]:
        if s["z0"] < 2000:
            continue
        extra = "extra" in s["namn"]
        pol = (SPK.diagonal(s, next(x for x in X_ if x["az"] * s["az"] > 0)) if "diag" in s["namn"] else SPK.stav(s))
        ax.add_patch(Polygon(list(pol.exterior.coords), closed=True, fc="#f3ead6" if extra else TRA, ec=INK, lw=0.5,
                             zorder=2 if extra else 3))
    for p in t["platar"]:
        ax.add_patch(Rectangle((p["x0"], p["z0"]), p["x1"] - p["x0"], p["z1"] - p["z0"], fc="#b8bcc2", ec=INK, lw=0.4,
                               zorder=4, alpha=0.9))
    xt = t["x_topp"]
    zt = max(s["z1"] for s in t["staver"] if "diag" in s["namn"])          # sätet: nockbalkens underkant
    for k in t.get("klossar", []):
        ax.add_patch(Rectangle((k["x0"], k["z0"]), k["x1"] - k["x0"], k["z1"] - k["z0"], fc="none", ec=ROD, lw=0.8,
                               ls=(0, (3, 2)), zorder=6))
    ax.add_patch(Rectangle((xt - BALK["b"] / 2, zt), BALK["b"], BALK["h"], fc=STAL, ec=INK, lw=0.5, zorder=5))
    ax.annotate("nockbalk 3", (xt - BALK["b"] / 2, zt + BALK["h"] * 0.7), (xt - 700, zt + BALK["h"] + 250), fontsize=6.3,
                ha="right", va="center", arrowprops=dict(arrowstyle="-", lw=0.4, color=INK))
    ax.annotate("", (xt, zt + BALK["h"] + 20), (xt, zt + BALK["h"] + 420), arrowprops=dict(arrowstyle="-|>", lw=1.2, color=ROD))
    ax.text(xt + 60, zt + BALK["h"] + 320, f"$P_d$ = {Pd:.1f} kN".replace(".", ","), color=ROD, fontsize=7, ha="left")
    if t.get("klossar"):
        k = t["klossar"][0]
        ax.annotate("toppkloss 45 mm\npå ena sidan" if t["nk"] == 1 else f"{t['nk']} toppklossar 45 mm", (k["x1"], (k["z0"] + k["z1"]) / 2),
                    (xt + 900, zt + 150), color=ROD, fontsize=6.3, ha="left",
                    va="center", arrowprops=dict(arrowstyle="-", lw=0.4, color=ROD))
    xs = [s["x0"] for s in t["staver"] if "diag" in s["namn"]] + [s["x1"] for s in t["staver"] if "diag" in s["namn"]]
    zb = min(s["z0"] for s in t["staver"] if s["z0"] > 2000)
    for x in (min(xs), max(xs)):
        ax.annotate("", (x + (60 if x < xt else -60), zb - 20), (x + (60 if x < xt else -60), zb - 420),
                    arrowprops=dict(arrowstyle="-|>", lw=1.0, color=BLA))
        ax.text(x + (110 if x < xt else -110), zb - 330, f"{V:.1f} kN".replace(".", ","), color=BLA, fontsize=6.5,
                ha="left" if x < xt else "right")
    ax.text(xt, zb + 230, f"dragband: H = {H:.1f} kN".replace(".", ","), ha="center", fontsize=6.5, color=BLA)
    ax.set_xlim(min(xs) - 300, max(xs) + 300); ax.set_ylim(zb - 480, zt + BALK["h"] + 520); ax.set_aspect("equal"); ax.axis("off")
    _spara(fig, path)


def huvudstolpe(path, GEO, HS, kc, u):
    """Huvudstolpen i elevation (y–z): stolpe, topregel och strävor på båda sidor, nockbalk 1."""
    fig, ax = plt.subplots(figsize=(9.6 * CM, 9.0 * CM))
    D = {d["namn"]: d for d in GEO["huvudstolpe"]}
    v, t = D["R L3 VertVert"], D["R L3 VertTop"]
    y0, y1 = v["y0"], v["y1"]
    yc = (y0 + y1) / 2
    zt = t["z0"]
    e = HS["e"]
    ax.add_patch(Rectangle((y0, 0), y1 - y0, zt, fc=TRA, ec=INK, lw=0.6, zorder=3))
    ax.add_patch(Rectangle((yc - e - 60, zt), 2 * e + 120, t["z1"] - t["z0"], fc=TRA, ec=INK, lw=0.6, zorder=3))
    ax.add_patch(Rectangle((yc - e - 900, t["z1"]), 2 * e + 1800, BALK["h"], fc=STAL, ec=INK, lw=0.5, zorder=3))
    ax.text(yc - 1200, t["z1"] + 95, "nockbalk 1 (K-01)", color="white", fontsize=6.3, va="center")
    for s in (1, -1):
        yA, zA = (y1 if s > 0 else y0), zt - (e - (y1 - y0) / 2)
        yB, zB = yc + s * e, zt
        w = HS["strava_h"] / 2 * math.sqrt(2)
        pts = [(yA, zA - w), (yB + s * 0, zB - 0), (yB - s * w, zB), (yA, zA + 0)]
        pts = [(yA, zA), (yB, zB), (yB - s * HS["strava_h"] * math.sqrt(2), zB), (yA, zA + HS["strava_h"] * math.sqrt(2))]
        ax.add_patch(Polygon(pts, closed=True, fc=TRA, ec=INK, lw=0.6, zorder=4))
        ax.annotate("", (yB, t["z1"] + 195), (yB, t["z1"] + 480), arrowprops=dict(arrowstyle="-|>", lw=1.0, color=ROD))
    ax.text(yc + e + 40, t["z1"] + 380, f"strävan: högst {HS['F_strava']:.1f} kN".replace(".", ","), color=ROD, fontsize=6.3)
    ax.annotate("", (yc, -10), (yc, -330), arrowprops=dict(arrowstyle="<|-", lw=1.0, color=BLA))
    ax.text(yc + 60, -260, f"$N_d$ = {HS['N_d']:.1f} kN, $M_d$ = {HS['M_d']:.2f} kNm".replace(".", ","), color=BLA, fontsize=6.5)
    ax.annotate("", (yc + 330, 0), (yc + 330, HS["L"]), arrowprops=dict(arrowstyle="<->", lw=0.4))
    ax.text(yc + 360, HS["L"] / 2, f"{HS['L']:.0f}", rotation=90, va="center", fontsize=6.3)
    ax.annotate("", (yc, t["z1"] + 260), (yc + e, t["z1"] + 260), arrowprops=dict(arrowstyle="<->", lw=0.4))
    ax.plot([yc, yc], [t["z1"] + BALK["h"], t["z1"] + 300], color=INK, lw=0.4)
    ax.text(yc + e / 2, t["z1"] + 290, f"{e:.0f}", ha="center", fontsize=6.3)
    ax.text(yc - 80, 1500, "4 st 45×120 C24\nsida vid sida", rotation=90, ha="center", va="center", fontsize=6.3)
    ax.plot([yc - 1200, yc + 1200], [0, 0], color=INK, lw=1.0)
    ax.text(yc - 1150, 60, "bjälklag", fontsize=6.3)
    ax.set_xlim(yc - 1250, yc + 1250); ax.set_ylim(-420, t["z1"] + 560); ax.set_aspect("equal"); ax.axis("off")
    _spara(fig, path)
