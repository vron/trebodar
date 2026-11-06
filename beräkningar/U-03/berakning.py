"""
U-03: takets luftspalt – luftflöde, fukt och mögelrisk timme för timme 2013–2023, hela taket som nätverk.

    python berakning.py           -> alla fall (parallellt, några minuter), figurer, resultat.json och PDF
    python berakning.py rapport   -> bara figurer, resultat.json och PDF ur sparade resultat (resultat/*.npz)
    python berakning.py fall bas  -> bara de angivna fallen

Läser indata.toml och klimat_era5.csv.gz. Nätverket byggs i geometri.py och räknas i modell.py.
"""
import os

os.environ.setdefault("VECLIB_MAXIMUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import copy  # noqa: E402
import json  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
import tomllib  # noqa: E402
from concurrent.futures import ProcessPoolExecutor  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402

import geometri  # noqa: E402
import modell  # noqa: E402

HERE = Path(__file__).parent
FONTS = HERE.parent / ".fonts"
UT = HERE / "resultat"
IN = tomllib.loads((HERE / "indata.toml").read_text(encoding="utf-8"))
FALL = {f["id"]: f for f in IN["fall"]}
SPALT = f'{IN["uppbyggnad"]["spalt"]:g}'                     # grundfallets spalt [mm], i texterna
REK_SPALT = FALL["rek"].get("spalt", IN["uppbyggnad"]["spalt"])   # det rekommenderade utförandets spalt [mm]
NYCKLAR = {"spalt": "uppbyggnad", "alfa_sol": "uppbyggnad", "celler": "modell", "varv": "modell", "zeta_takfot": "stromning"}


def fmt(x, n=1):
    s = f"{x:,.{n}f}".replace(",", " ").replace(".", ",")
    return s.replace("-", "−")


def indata_for(f):
    I = copy.deepcopy(IN)
    for k, sektion in NYCKLAR.items():
        if k in f:
            I[sektion][k] = f[k]
    if f.get("utan_fonster"):
        I["tak"]["fonster"] = []
    if "omluft_l" in f:
        I["stromning"]["omluft_l"] = f["omluft_l"]
    if "start" in f:                                         # taket stängs: beräkningen och utvärderingen börjar då
        I["klimat"]["utvardering"] = f["start"]
    return I


def kor_fall(fid):
    f = FALL[fid]
    I = indata_for(f)
    N = geometri.bygg(I, f.get("samling", False), f.get("gavel", False), f.get("omluft", False))
    K = modell.klimat(I, katalog=HERE)
    if "start" in f:
        m = K["t"] >= np.datetime64(f["start"])
        K = {k: (v[m] if isinstance(v, np.ndarray) and len(v) == len(m) else v) for k, v in K.items()}
    t0 = time.time()
    r = modell.kor(I, N, K, f, logg=lambda s: None)
    nat = r["nat"]
    g = N["gren"]
    UT.mkdir(exist_ok=True)
    np.savez_compressed(UT / f"{fid}.npz", Mr_max=r["Mr_max"], Mm_max=r["Mm_max"], Qfall=r["Qfall"],
                        dag_Mr=r["dag"]["Mr"], dag_Mm=r["dag"]["Mm"], dag_RHr=r["dag"]["RHr"], dag_u2=r["dag"]["u2"],
                        bad=r["bad"], cell_x=nat.cell_x, cell_y=nat.cell_y,
                        remsa=g["remsa"][nat.fall], x0=g["x0"][nat.fall], x1=g["x1"][nat.fall], fasad=nat.fasad,
                        L=g["L"][nat.fall], A_fl=nat.A_fl, yc=np.array([N["remsor"][s][0] for s in g["remsa"][nat.fall]]),
                        w=N["bredd"], t0=str(K["t"][0]), sek=time.time() - t0)
    return fid, time.time() - t0


def las(fid):
    return dict(np.load(UT / f"{fid}.npz"))


# ------------------------------------------------------------------ sammanställning
def sammanfatta(fid, d, K=None):
    nf = len(d["remsa"])
    nc = len(d["Mr_max"]) // nf
    Mf = d["Mr_max"].reshape(nf, nc).max(axis=1)
    Mmf = d["Mm_max"].reshape(nf, nc).max(axis=1)
    k = int(np.argmax(d["Mr_max"])); kf = k // nc
    t = np.datetime64(str(d["t0"])[:13]) + np.arange(len(d["Qfall"])).astype("timedelta64[h]")
    utv = t >= np.datetime64(FALL[fid].get("start", IN["klimat"]["utvardering"]))
    v = np.abs(d["Qfall"][utv]) / d["A_fl"]                                  # hastighet i spalten [m/s]
    vag = {}
    for s in np.unique(d["remsa"]):                                         # vägens längd: takfall som hänger ihop i x
        idx = np.where(d["remsa"] == s)[0]
        idx = idx[np.argsort(d["x0"][idx])]
        kedja = [[idx[0]]]
        for i in idx[1:]:
            (kedja[-1].append(i) if abs(d["x0"][i] - d["x1"][kedja[-1][-1]]) < 1 else kedja.append([i]))
        for kk in kedja:
            for i in kk:
                vag[i] = float(d["L"][kk].sum())
    dagar = np.datetime64(str(d["t0"])[:10]) + np.arange(d["dag_Mr"].shape[0])
    ar = dagar.astype("datetime64[Y]").astype(int) + 1970
    M_ar = {int(a): float(d["dag_Mr"][ar == a].max()) for a in np.unique(ar)}
    vag_c = np.repeat([vag[i] for i in range(nf)], nc)
    fon_f = np.zeros(nf, bool)                                                # remsorna med takfönster
    for f in IN["tak"]["fonster"]:
        fon_f |= (d["yc"] > f["y"][0]) & (d["yc"] < f["y"][1])
    fon_c = np.repeat(fon_f, nc)
    lang, kort = (vag_c > 15) & ~fon_c, (vag_c < 7) & ~fon_c
    M_ar_lang = {int(a): float(d["dag_Mr"][ar == a][:, lang].max()) for a in np.unique(ar)}
    M_ar_kort = {int(a): float(d["dag_Mr"][ar == a][:, kort].max()) for a in np.unique(ar)}
    A = d["L"] * d["w"]
    bad = d["bad"].reshape(nf, nc).any(axis=1) if d["bad"].any() else None
    fon = fon_f
    vfon = np.abs(d["Qfall"][utv][:, fon]) / d["A_fl"][fon] if fon.any() else None
    return dict(id=fid, namn=FALL[fid]["namn"], M=float(d["Mr_max"].max()), M_iso=float(d["Mm_max"].max()),
                Mf=Mf, Mmf=Mmf, kf=kf, fon_kf=bool(fon_f[kf]), fasad=float(d["fasad"][kf]), yc=float(d["yc"][kf]), x0=float(d["x0"][kf]),
                x1=float(d["x1"][kf]), vag=vag[kf], v_med=float(np.median(v[:, kf])), v_lag=float((v[:, kf] < 0.02).mean()),
                v_med_alla=float(np.median(v)), M_ar=M_ar, M_ar_lang=M_ar_lang, M_ar_kort=M_ar_kort,
                vag_f=np.array([vag[i] for i in range(nf)]),
                M_lang=float(d["Mr_max"][lang].max()), M_kort=float(d["Mr_max"][kort].max()),
                yta1=float(A[Mf >= 1].sum()), yta2=float(A[Mf >= 2].sum()), yta3=float(A[Mf >= 3].sum()), yta=float(A.sum()),
                M_fon=float(Mf[fon].max()) if fon.any() else None, v_fon=float(np.median(vfon)) if fon.any() else None,
                M_bad=float(Mf[bad].max()) if bad is not None else None,
                Miso_bad=float(Mmf[bad].max()) if bad is not None else None)


def rapport():
    import matplotlib
    matplotlib.use("svg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    for f_ in sorted(FONTS.glob("*.ttf")) if FONTS.is_dir() else []:
        font_manager.fontManager.addfont(str(f_))
    plt.rcParams.update({"font.family": "Carlito", "font.size": 7.5, "svg.fonttype": "none", "axes.linewidth": 0.5})
    D = {fid: las(fid) for fid in FALL if (UT / f"{fid}.npz").exists()}
    S = {fid: sammanfatta(fid, d) for fid, d in D.items()}
    for fid, s in S.items():
        print(f"{fid:22s} M_r {s['M']:5.2f}  M_iso {s['M_iso']:5.2f}  sämst y {s['yc']:6.0f} x {s['x0']:6.0f}–{s['x1']:6.0f} "
              f"fasad {s['fasad']:5.1f} väg {s['vag']:5.2f} m  v_med {s['v_med']:.3f} (alla {s['v_med_alla']:.3f})  "
              f"<0,02 m/s {s['v_lag']:.2f}  yta M≥1/2/3 {s['yta1']:.0f}/{s['yta2']:.0f}/{s['yta3']:.0f} av {s['yta']:.0f} m²"
              + (f"  bad {s['M_bad']:.2f}/{s['Miso_bad']:.2f}" if s['M_bad'] is not None else "")
              + (f"  fönsterremsor M {s['M_fon']:.2f} v {s['v_fon']:.3f}" if s['M_fon'] is not None else "")
              + f"  M lång/kort {s['M_lang']:.2f}/{s['M_kort']:.2f}")
    json.dump({fid: {k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in s.items() if k not in ("Mf", "Mmf", "vag_f")}
               for fid, s in S.items()}, open(HERE / "resultat_fall.json", "w"), ensure_ascii=False, indent=1)
    if all(f in S for f in ("bas", "omluft", "omluft_gavel", "omluft_samling_gavel")):
        fig_plan(plt, S, D)
    fig_omluft(plt)
    K = modell.klimat(IN, katalog=HERE)
    F = flodesstat(D, K) if all(f in D for f in ("omluft", "vind0")) else None
    if F and all(f in S for f in ("omluft", "vind05", "vind025", "oventilerad", "malad")):
        fig_ar(plt, S, F)
    return S, D, K, F


def fig_omluft(plt):
    """Principskiss: omluftning vid ett takfönster, sett uppifrån med nocken uppåt (mått i mm)."""
    from matplotlib.patches import Rectangle, FancyArrowPatch
    fig, ax = plt.subplots(figsize=(7.0, 2.6))
    y0f, y1f, L = -550, 550, 1750
    tra, lakt_c, oppn = "#ead9b5", "#8a6a36", "#7fb2e5"
    for x, b in ((-1200, 45), (1200, 45), (-600, 124), (600, 124)):          # takbalkar och avväxlingar (dubbla)
        ax.add_patch(Rectangle((x - b / 2, -L), b, 2 * L, facecolor=tra, edgecolor="#b89a62", lw=0.3))
    for ya, yb in ((y1f, L), (-L, y0f)):                                     # kortlingar
        ax.add_patch(Rectangle((-22.5, ya), 45, yb - ya, facecolor=tra, edgecolor="#b89a62", lw=0.3))
    ax.add_patch(Rectangle((-538, y0f), 1076, y1f - y0f, facecolor="#3b4a5a", edgecolor="none"))
    ax.text(0, 0, "takfönster", color="white", ha="center", va="center", fontsize=7)

    def lakt(x, ya, yb, uppeh):
        y = ya
        for g0, g1 in sorted(uppeh) + [(yb, yb)]:
            if g0 > y:
                ax.add_patch(Rectangle((x - 22.5, y), 45, g0 - y, facecolor=lakt_c, edgecolor="none"))
            if g1 > g0:
                ax.add_patch(Rectangle((x - 60, g0), 120, g1 - g0, facecolor=oppn, edgecolor="none", alpha=0.9))
            y = max(y, g1)
    ovan = [(y1f + 100, y1f + 250), (y1f + 650, y1f + 800)]                 # 2 × 150 = 300 mm per linje inom 1 m
    under = [(y0f - 250, y0f - 100), (y0f - 800, y0f - 650)]
    for x in (-600, 600):
        lakt(x, -L, L, ovan + under)
    lakt(0, y1f, L, [(y1f + 375, y1f + 525), (y1f + 900, y1f + 1050)])       # förskjutna mot avväxlingarnas uppehåll
    lakt(0, -L, y0f, [(y0f - 525, y0f - 375), (y0f - 1050, y0f - 900)])
    for x in (-1200, 1200):
        lakt(x, -L, L, [])
    pil = dict(arrowstyle="-|>", mutation_scale=7, lw=0.9, color="#1f5fa8")
    for sgn in (-1, 1):
        xi, xo = sgn * 300, sgn * 900
        ax.add_patch(FancyArrowPatch((xi, -L + 80), (xi, y0f - 200), **pil))
        ax.add_patch(FancyArrowPatch((xi, y0f - 175), (xo, y0f - 120), connectionstyle=f"arc3,rad={-0.35 * sgn}", **pil))
        ax.add_patch(FancyArrowPatch((xo, y0f - 60), (xo, y1f + 60), **pil))
        ax.add_patch(FancyArrowPatch((xo, y1f + 120), (xi, y1f + 175), connectionstyle=f"arc3,rad={-0.35 * sgn}", **pil))
        ax.add_patch(FancyArrowPatch((xi, y1f + 200), (xi, L - 80), **pil))
    # 1 m-zonen ovanför fönstret
    ax.annotate("", (1420, y1f), (1420, y1f + 1000), arrowprops=dict(arrowstyle="<->", lw=0.5, color="#333333", mutation_scale=5))
    ax.text(1480, y1f + 500, "1 000", fontsize=6, va="center", rotation=90)
    ax.text(0, L + 60, "mot nock", ha="center", va="bottom", fontsize=6.3)
    ax.text(0, -L - 60, "mot takfot", ha="center", va="top", fontsize=6.3)
    ax.text(1700, 1250, "Uppehåll i ströläkten (blått) på avväxlingarna och kortlingen:\n"
            f"minst {FALL['rek']['omluft_l']:g} mm fritt per läktlinje inom 1 m ovanför och\n"
            "under fönstret, högst 200 mm vardera, förskjutna\nmellan linjerna så att råsponten alltid bärs.", fontsize=6.3, va="center")
    ax.text(1700, -200, "Luften i de två facken som fönstret bryter går åt sidan\ngenom uppehållen, förbi fönstret i grannfacken och\n"
            f"tillbaka ovanför det. Ströläkten {REK_SPALT:g} mm hög.", fontsize=6.3, va="center")
    ax.text(1700, -1300, "Ljust: takbalk 45, avväxling (dubbel takbalk) och kortling.\nMörkt: ströläkt 45.", fontsize=6.3, va="center")
    ax.set_xlim(-1400, 4600); ax.set_ylim(-L - 250, L + 250); ax.set_aspect("equal"); ax.axis("off")
    fig.savefig(HERE / "fig_omluft.svg", bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


def flodesstat(D, K):
    """Luftens hastighet i spalten i fönsterfria remsor: väg 16,3 m (y ≈ 7 300) och 5,4 m (y ≈ 13 450), olika väder."""
    ut = {}
    lugn = K["U"] < 2.0
    sol = K["GHI"] > 300
    natt = K["GHI"] < 1
    utv = K["t"] >= np.datetime64(IN["klimat"]["utvardering"])
    villkor = {"alla": utv, "lugn_sol": utv & lugn & sol, "lugn_natt": utv & lugn & natt}
    for fid in ("omluft", "vind0"):
        d = D[fid]
        for namn, y in (("lang", 7300), ("kort", 13450)):
            i = np.where(np.abs(d["yc"] - y) < 300)[0]
            i = i[np.argmin(d["x0"][i])]
            v = np.abs(d["Qfall"][:, i]) / d["A_fl"][i]
            for vn, m in villkor.items():
                ut[f"{fid}_{namn}_{vn}"] = float(np.median(v[m]))
            ut[f"{fid}_{namn}_mot_NV"] = float((d["Qfall"][utv & lugn & sol, i] > 0).mean())   # SO → NV
    ut["andel_lugn_sol"] = float((utv & lugn & sol).sum() / utv.sum())
    return ut


def fig_ar(plt, S, F):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.0, 1.9), gridspec_kw=dict(width_ratios=[1.6, 1]))
    ar = list(range(2014, 2024))
    for fid, namn, c, ls in (("malad", "målad plåt, full vind", "#9a9a9a", "-"), ("omluft", "zink-magnesium, full vind", "#d4502f", "-"),
                             ("vind05", "vindtryck × 0,5", "#ec9a4a", "-"), ("vind025", "vindtryck × 0,25", "#f3c14a", "-"),
                             ("oventilerad", "oventilerad", "#4a6fa5", "-")):
        if fid not in S:
            continue
        a1.plot(ar, [S[fid]["M_ar"][a] for a in ar], color=c, lw=1.0, ls="-", marker="o", ms=2.2, label=namn)
        a1.plot(ar, [S[fid]["M_ar_lang"][a] for a in ar], color=c, lw=0.8, ls=(0, (3, 2)))
    a1.axhline(1.0, color="#555555", lw=0.5, ls=":")
    a1.set_xticks(ar); a1.set_xticklabels([str(a)[2:] for a in ar], fontsize=6.3); a1.tick_params(labelsize=6.3)
    a1.set_ylabel("M, största under året", fontsize=6.5)
    a1.set_title("a) Mögelindex på råspontens undersida. Heldraget: hela taket, streckat: väg 16,3 m utan fönsterfack", fontsize=7, loc="left")
    a1.legend(fontsize=6, frameon=False, ncol=2, loc="upper left")
    lab = ["alla timmar", "lugnt, sol", "lugnt, natt"]
    x = np.arange(3)
    for j, (fid, namn, c) in enumerate((("omluft", "vind och sol", "#4a6fa5"), ("vind0", "bara sol och stigkraft", "#e0a030"))):
        vals = [F[f"{fid}_lang_{v}"] for v in ("alla", "lugn_sol", "lugn_natt")]
        a2.bar(x + (j - 0.5) * 0.36, vals, 0.34, color=c, label=namn)
    a2.set_xticks(x); a2.set_xticklabels(lab, fontsize=6.3); a2.tick_params(labelsize=6.3)
    a2.set_ylabel("m/s, median", fontsize=6.5)
    a2.set_title("b) Luftens hastighet, väg 16,3 m", fontsize=7, loc="left")
    a2.legend(fontsize=6, frameon=False, loc="upper right")
    from matplotlib.ticker import FuncFormatter
    a2.yaxis.set_major_formatter(FuncFormatter(lambda v, p: fmt(v, 2)))
    for a in (a1, a2):
        for sp in ("top", "right"):
            a.spines[sp].set_visible(False)
    fig.tight_layout(w_pad=1.5)
    fig.savefig(HERE / "fig_ar.svg", bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


MFARG = [(0.5, "#f4f4f2", "< 0,5"), (1.0, "#f3dc8a", "0,5–1"), (2.0, "#ec9a4a", "1–2"), (3.0, "#d4502f", "2–3"),
         (np.inf, "#8e1f1f", "≥ 3")]


def mfarg(M):
    return next(c for g, c, _ in MFARG if M < g)


def fig_plan(plt, S, D):
    """Taket i plan: mögelindex på råspontens undersida, största värdet per takfall, för fyra utföranden."""
    from matplotlib.patches import Rectangle
    import math
    T = IN["tak"]
    linjer = geometri.nock_och_dallinjer(IN["byggnad"])
    paneler = (("bas", f"a) Som ritat, {SPALT} mm"), ("omluft", f"b) {SPALT} mm, omluftning vid fönstren"),
               ("omluft_gavel", "c) b + gavelöppningar"), ("vind025", "d) b, vindtryck × 0,25"),
               ("rek_vind025", f"e) {SPALT} mm, omluftning {FALL['rek']['omluft_l']:g} mm, × 0,25"),
               ("malad", "f) b med målad plåt"))
    paneler = tuple(p_ for p_ in paneler if p_[0] in S)
    fig, axs = plt.subplots(2, 3, figsize=(7.0, 5.2))
    axs = axs.ravel()
    th = math.radians(450 - T["azimut_x"])                      # norr i K-05:s koordinater: (sin θ, cos θ), θ = 450° − azimut för +x
    for ax, (fid, titel) in zip(axs, paneler):
        s, d = S[fid], D[fid]
        for i in range(len(d["remsa"])):
            x0, x1 = d["x0"][i] / 1000, d["x1"][i] / 1000
            yc, w = d["yc"][i] / 1000, d["w"][i]                     # remsans bredd är redan i m
            ax.add_patch(Rectangle((x0, yc - w / 2), x1 - x0, w, facecolor=mfarg(s["Mf"][i]), edgecolor="#c8c8c8", lw=0.12))
        for f in T["fonster"]:
            ax.add_patch(Rectangle((f["x"][0] / 1000, f["y"][0] / 1000), (f["x"][1] - f["x"][0]) / 1000, (f["y"][1] - f["y"][0]) / 1000,
                                   facecolor="#3b4a5a", edgecolor="none"))
        for typ, x, y0, y1 in linjer:
            ax.plot([x / 1000] * 2, [y0 / 1000, y1 / 1000], color="#333333", lw=0.55 if typ == "N" else 0.4,
                    ls="-" if typ == "N" else (0, (3, 2)))
        if FALL[fid].get("samling"):
            for typ, x, y0, y1 in linjer:
                ax.plot([x / 1000] * 2, [y0 / 1000, y1 / 1000], color="#1f5fa8", lw=1.8, alpha=0.35, solid_capstyle="butt")
        if FALL[fid].get("gavel"):
            for gv in T["gavlar"]:
                typ, x, y0, y1 = next(l for l in linjer if l[1] == gv["x"])
                y = (y0 if gv["ande"] == "y0" else y1) / 1000
                dy = -0.6 if gv["ande"] == "y0" else 0.6
                ax.annotate("", (x / 1000, y), (x / 1000, y + dy), arrowprops=dict(arrowstyle="<|-|>", lw=0.8, color="#1f5fa8",
                            shrinkA=0, shrinkB=0, mutation_scale=7))
        ax.set_title(titel, fontsize=7, loc="left", pad=2)
        ax.text(-0.2, -1.25, f"M max {fmt(s['M'], 2)}", fontsize=6.5, ha="left", va="top")
        ax.set_xlim(-0.6, 16.6); ax.set_ylim(-2.0, 16.9); ax.set_aspect("equal"); ax.axis("off")
    ax = axs[0]
    for y, txt in ((0.4, "5,9"), (2.2, "11,1"), (7.3, "16,3"), (11.85, "5,4"), (14.3, "5,4")):
        ax.text(14.25, y, txt, fontsize=5.5, ha="left", va="center", color="#555555")
    ax.text(14.25, 16.2, "väg, m", fontsize=5.5, ha="left", va="center", color="#555555")
    # takfallens riktning i vänster byggnads övre del (mot sydost vänster om nocken, mot nordväst höger)
    for xx, txt in ((1.0, "SO"), (3.3, "NV")):
        ax.text(xx, 16.35, txt, fontsize=5.5, ha="center", va="bottom", color="#333333")
    c = np.array([7.0, 14.0]); dn = np.array([math.sin(th), math.cos(th)])
    ax.annotate("", c + dn * 0.9, c - dn * 0.5, arrowprops=dict(arrowstyle="-|>", lw=0.6, color="#333333", mutation_scale=6))
    ax.text(*(c + dn * 1.5), "N", fontsize=6, ha="center", va="center")
    h = [Rectangle((0, 0), 1, 1, facecolor=c_, edgecolor="#bbbbbb", lw=0.3) for _, c_, _ in MFARG]
    fig.legend(h, [t for _, _, t in MFARG], loc="lower center", ncol=5, fontsize=6.5, frameon=False, handlelength=1.2,
               bbox_to_anchor=(0.5, -0.02), title="Mögelindex M på råspontens undersida, största värdet 2014–2023 per takfall",
               title_fontsize=6.5)
    fig.subplots_adjust(left=0.0, right=1.0, top=0.96, bottom=0.07, wspace=0.03, hspace=0.12)
    fig.savefig(HERE / "fig_plan.svg", bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


TABELL = [("Utförande", ["rek", "bas", "omluft", "omluft_gavel", "omluft_samling", "omluft_samling_gavel", "utan_fonster"]),
          ("Vind och spalt", ["rek_vind05", "rek_vind025", "vind05", "vind025", "vind0", "gavel_vind05", "s25", "s36", "s45", "s36_vind05",
                              "s25_vind025", "s36_vind025", "s45_vind025", "takfot_strypt", "takfot_strypt_vind025"]),
          ("Plåt", ["zm_ny", "zm_patina", "malad"]),
          ("Inneklimat och vindskiva", ["bad", "bad_sd10", "fukt6", "tomt15", "tomt_vinter", "rek_tomt15", "rek_tomt", "s36_tomt",
                                        "masonit006", "masonit06"]),
          ("Byggfukt och oventilerat", ["vat", "takfot_strypt_vat", "bas_vat", "oventilerad", "oventilerad_vat"])]
TABELL_ID = [f for _, ids in TABELL for f in ids]
KORT = {"rek": f"*Rekommenderat: {REK_SPALT:g} mm, omluftning {FALL['rek']['omluft_l']:g} mm*",
        "rek_vind05": "Rekommenderat, vindtryck × 0,5",
        "rek_vind025": "Rekommenderat, vindtryck × 0,25", "tomt15": "Tomt okt–apr: inne 15 °C, omluftning 600 mm",
        "rek_tomt15": "Rekommenderat, tomt: inne 15 °C", "rek_tomt": "Rekommenderat, tomt: inne 10 °C",
        "takfot_strypt_vind025": "Strypta takfötter, vindtryck × 0,25",
        "bas": f"Som ritat: fönstren bryter facken ({SPALT} mm)", "omluft": f"{SPALT} mm, omluftning 600 mm",
        "omluft_gavel": "+ gavelöppningar", "omluft_samling": "+ kanal längs nock och dal",
        "omluft_samling_gavel": "+ kanal och gavelöppningar", "vind05": "Vindtryck × 0,5", "vind025": "Vindtryck × 0,25",
        "vind0": "Ingen vind, bara sol och stigkraft", "gavel_vind05": "Gavelöppningar, vindtryck × 0,5", "s25": "Spalt 25 mm",
        "s45": "Spalt 45 mm", "s36": "Spalt 36 mm", "s25_vind025": "Spalt 25 mm, vindtryck × 0,25",
        "s36_vind025": "Spalt 36 mm, vindtryck × 0,25", "s36_vind05": "Spalt 36 mm, vindtryck × 0,5",
        "s36_tomt": "Spalt 36 mm, tomt okt–apr", "s45_vind025": "Spalt 45 mm, vindtryck × 0,25", "masonit006": "Vindskiva Sd 0,06 m", "masonit06": "Vindskiva Sd 0,6 m",
        "bad": "Badrummet fuktklass 4, Intello Plus", "bad_sd10": "Badrummet fuktklass 4, Sd 10 m där",
        "fukt6": "Hela huset fuktklass 3", "tomt_vinter": "Tomt okt–apr: inne 10 °C, omluftning 600 mm",
        "zm_ny": "Ny blank plåt: α 0,55, ε 0,12", "zm_patina": "Åldrad plåt: α 0,8, ε 0,4", "malad": "Målad plåt: α 0,6, ε 0,9",
        "takfot_strypt": "Strypta takfötter (4 × tryckfall)",
        "takfot_strypt_vat": "Strypta takfötter, råspont 20 % vid stängning", "vat": "Råspont 20 % vid stängning",
        "bas_vat": "Som ritat, råspont 20 % vid stängning", "oventilerad": "Oventilerad (takfötter stängda)",
        "oventilerad_vat": "Oventilerad, råspont 20 % vid stängning", "utan_fonster": "Utan takfönster"}


def lage(s):
    if s["M"] < 0.1:
        return "–"
    rikt = "SO" if abs(s["fasad"] - (IN["tak"]["azimut_x"] + 180) % 360) < 1 else "NV"
    return f"{rikt}, fönsterfack" if s["fon_kf"] else f"{rikt}, {fmt(s['vag'], 1)} m"


def resultat_json(S, D, K, F):
    import tomllib as _t
    g = IN["tak"]
    om = S["omluft"]
    rad = []
    for grupp, ids in TABELL:
        rad.append(dict(grupp=True, namn=grupp))
        for fid in ids:
            x = S[fid]
            rad.append(dict(grupp=False, id=fid, namn=KORT[fid], M=fmt(x["M"], 2), yta1=fmt(x["yta1"], 0),
                            Miso=fmt(x["M_iso"], 2), v=fmt(x["v_med_alla"], 2), var=lage(x)))
    utv = K["t"] >= np.datetime64(IN["klimat"]["utvardering"])
    # varför takfallen skiljer: sol nov–mars och råspontens RF under vintern i de korta vägarna (omluftningsfallet)
    man = K["t"].astype("datetime64[M]").astype(int) % 12 + 1
    vinter = utv & np.isin(man, [11, 12, 1, 2, 3])
    n_vintrar = vinter.sum() / (151 * 24)
    az_so, az_nv = (g["azimut_x"] + 180) % 360, g["azimut_x"] % 360
    sol = {k: float(modell.instralning(K, g["lutning"], a)[vinter].sum() / 1000 / n_vintrar) for k, a in (("SO", az_so), ("NV", az_nv))}
    d = D["omluft"]; nf = len(d["remsa"]); nc = len(d["Mr_max"]) // nf
    dagar = np.datetime64(str(d["t0"])[:10]) + np.arange(d["dag_RHr"].shape[0])
    dm = dagar.astype("datetime64[M]").astype(int) % 12 + 1
    dv = (dagar >= np.datetime64(IN["klimat"]["utvardering"])) & np.isin(dm, [11, 12, 1, 2, 3])
    kort = np.repeat(S["omluft"]["vag_f"] < 7, nc)
    rikt = np.repeat(np.where(np.abs(d["fasad"] - az_so) < 1, "SO", "NV"), nc)
    rf = {k: float(d["dag_RHr"][dv][:, kort & (rikt == k)].mean()) for k in ("SO", "NV")}
    R = {
        "projekt": IN["projekt"],
        "sam": dict(sol_SO=fmt(sol["SO"], 0), sol_NV=fmt(sol["NV"], 0), rf_SO=fmt(100 * rf["SO"], 0), rf_NV=fmt(100 * rf["NV"], 0)),
        "rek": dict(spalt=fmt(REK_SPALT, 0), omluft=fmt(FALL["rek"]["omluft_l"], 0),
                    oppning=fmt(REK_SPALT * FALL["rek"]["omluft_l"], 0)),
        "g": dict(lutning=fmt(g["lutning"], 0), spalt=fmt(IN["uppbyggnad"]["spalt"], 0), cc=fmt(g["cc"], 0), vag_max="16,3",
                  vagar="5,4, 5,9, 11,1 eller 16,3", remsor=str(len(np.unique(D["omluft"]["remsa"]))), celler=str(IN["modell"]["celler"]),
                  varv=str(IN["modell"]["varv"]), yta=fmt(om["yta"], 0)),
        "in": dict(ab="0,3–34 m", fukt=fmt(IN["inne"]["fukttillskott"], 0), bad=fmt(IN["inne"]["badrum"]["fukttillskott"], 0),
                   sd_mas=fmt(IN["uppbyggnad"]["sd_masonit"], 1), alfa=fmt(IN["uppbyggnad"]["alfa_sol"], 2),
                   eps=fmt(IN["uppbyggnad"]["eps_plat"], 2)),
        "kl": dict(period=f"{str(K['t'][0])[:4]}–{str(K['t'][-1])[:4]}", T=fmt(K["T"][utv].mean(), 1), RF=fmt(100 * K["RH"][utv].mean(), 0),
                   U=fmt(K["U"][utv].mean(), 1)),
        "fl": {k: (fmt(v, 2) if "andel" not in k and "mot_NV" not in k else fmt(100 * v, 0)) for k, v in (F or {}).items()},
        "tab": rad,
        "kontroll": dict(celler="12", M_celler=fmt(S["k_celler12"]["M"], 2) if "k_celler12" in S else "–",
                         varv="10", M_varv=fmt(S["k_varv10"]["M"], 2) if "k_varv10" in S else "–", M_bas=fmt(om["M"], 2),
                         massbalans="10⁻⁸"),
        "S": {fid: dict(M=fmt(x["M"], 2), M2=fmt(x["M"], 2), M_lang=fmt(x["M_lang"], 2), M_kort=fmt(x["M_kort"], 2),
                        Miso=fmt(x["M_iso"], 2), yta1=fmt(x["yta1"], 0), yta2=fmt(x["yta2"], 0), yta3=fmt(x["yta3"], 0),
                        v=fmt(x["v_med_alla"], 2), M_bad=fmt(x["M_bad"], 1) if x["M_bad"] is not None else "–",
                        Miso_bad=fmt(x["Miso_bad"], 2) if x["Miso_bad"] is not None else "–",
                        M_fon=fmt(x["M_fon"], 2) if x["M_fon"] is not None else "–",
                        v_fon=fmt(x["v_fon"], 2) if x["v_fon"] is not None else "–",
                        ar={str(a): fmt(v, 1) for a, v in x["M_ar"].items()},
                        ar_lang={str(a): fmt(v, 1) for a, v in x["M_ar_lang"].items()},
                        ar_kort={str(a): fmt(v, 1) for a, v in x["M_ar_kort"].items()}) for fid, x in S.items()},
    }
    (HERE / "resultat.json").write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8")
    return R


if __name__ == "__main__":
    arg = sys.argv[1:]
    if not arg or arg[0] == "fall":
        ids = arg[1:] if arg else list(FALL)

        def kostnad(fid):                              # varv × timmar: de längsta fallen först (jämn fördelning)
            f = FALL[fid]
            varv = 1 if f.get("oventilerad") else indata_for(f)["modell"]["varv"]
            return varv * (np.datetime64("2024-01-01") - np.datetime64(f.get("start", "2013-07-01"))).astype(int)
        ids.sort(key=kostnad, reverse=True)
        with ProcessPoolExecutor(max_workers=max(1, min(len(ids), (os.cpu_count() or 2) - 2))) as ex:
            for fid, sek in ex.map(kor_fall, ids):
                print(f"{fid}: {sek:.0f} s", flush=True)
    S, D, K, F = rapport()
    if all(f in S for f in TABELL_ID):
        resultat_json(S, D, K, F)
        import typst
        pdf = HERE / f"{IN['projekt']['dokument']}_takets_luftspalt.pdf"
        typst.compile(str(HERE / "mall.typ"), output=str(pdf), font_paths=["/usr/share/fonts", str(FONTS)])
        print(pdf.name)
