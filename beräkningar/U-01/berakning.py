"""
U-01: bottenplattans temperatur och fukt under året. Tvådimensionell transient värmeledning i sektion A–A genom
källaren i periodiskt tillstånd (det marken når efter många år), med känslighetsfall, kontroller och fuktbalans.

    python berakning.py            -> U-01_bottenplatta_fukt.pdf
    python berakning.py figurer    -> bara grundfallet och figurerna

Läser indata.toml och väggarnas och rörens lägen ur ../K-05/bild/geometri.json (modellen), räknar med mark2d.py,
ritar figurer och sätter ihop PDF via Typst (mall.typ).
"""
import json
import sys
import time
import tomllib
from pathlib import Path

import matplotlib

matplotlib.use("svg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402
import numpy as np  # noqa: E402

import mark2d as M  # noqa: E402

HERE = Path(__file__).parent
FONTS = HERE.parent / ".fonts"
IN = tomllib.loads((HERE / "indata.toml").read_text(encoding="utf-8"))
G05 = json.load(open(HERE.parent / "K-05" / "bild" / "geometri.json", encoding="utf-8"))
VAGG = {f"V{i}": v for i, v in enumerate(G05["vagg"], 1)}
PEL = {f"P{i}": p for i, p in enumerate(G05["pelare"], 1)}
MANAD = ("januari", "februari", "mars", "april", "maj", "juni", "juli", "augusti", "september", "oktober",
         "november", "december")
TYPER = (("falt", "Platta i fält"), ("plint", "Plint"), ("kant", "Kantbalk"))


def fmt(x, n=1):
    from decimal import Decimal, ROUND_HALF_UP
    q = Decimal(repr(float(x))).quantize(Decimal(1).scaleb(-n), rounding=ROUND_HALF_UP)
    if q == 0:
        q = abs(q)
    s = f"{q:,.{n}f}".replace(",", " ").replace(".", ",")
    return s.replace("-", "−")


def datum(d):
    m = max(i for i, s in enumerate(M.MAN) if s <= d)
    return f"{d - M.MAN[m] + 1} {MANAD[m][:3] if m != 4 else 'maj'}"


def par(fall):
    """Parametrar i m för mark2d: grundfallet med fallets ändringar."""
    s, pl, kl, dr = IN["sektion"], IN["platta"], IN["klimat"], IN["drift"]
    P = dict(xc_v=VAGG[s["vagg_v"]][1] / 1000, xc_o=VAGG[s["vagg_o"]][1] / 1000, mark_v=s["mark_v"] / 1000,
             mark_o=s["mark_o"] / 1000, h_rum=s["h_rum"] / 1000, utforande=s["utforande"],
             plint=sorted(((n, PEL[n][0] / 1000, b / 1000) for n, b in IN["plintar"].items() if abs(PEL[n][1] - s["y"]) < b / 2),
                          key=lambda p: p[1]),
             vagg_skikt=IN["vagg"]["skikt"])
    P.update({k: v / 1000 for k, v in pl.items()})
    P.update(IN["material"]); P.update(kl); P.update(dr)
    P["nat"] = dict(IN["nat"])
    P["nat"].update({k: IN["nat"][k] / 1000 for k in ("h_fin", "h_falt", "h_vagg", "h_max")})
    for k, v in fall.items():
        if k in ("mark_v", "mark_o"):
            P[k] = v / 1000
        elif k == "utbredning":
            P["nat"][k] = v
        elif k != "namn":
            P[k] = v
    u = IN["utforande"][P["utforande"]]
    P["t_eps"], P["h_balk"] = u["t_eps"] / 1000, u["h_balk"] / 1000
    return P


def kondens(Tg, Tx, d, mu):
    """Fuktbalans dygnsvis (Glaser) i ytan Tx med marken Tg vid RF 100 % och cellplast d (m) emellan. Två varv av
    årscykeln; andra varvets största mängd (g/m²) och antal dygn med kondens."""
    g = IN["fukt"]["delta_luft"] / mu / d * (M.ps(Tg) - M.ps(Tx)) * M.DAG * 1000     # g/(m²·dygn)
    Mx, ut = 0.0, []
    for gg in np.concatenate([g, g]):
        Mx = max(0.0, Mx + gg)
        ut.append(Mx)
    ut = np.array(ut[365:])
    return float(ut.max()), int((ut > 0).sum())


def kor(fall, f=1.0, n=None, falt=()):
    t0 = time.time()
    P = par(fall)
    m = M.bygg(P, f)
    A = M.Ar(m, n or IN["nat"]["steg_per_dygn"])
    T0, it, avv = A.periodisk()
    K = M.kolumner(m)
    nk = len(K)
    To, Tu, Tf = np.zeros((nk, 365)), np.zeros((nk, 365)), np.full((nk, 365), np.nan)

    def spara(T, d):
        for i, c in enumerate(K):
            To[i, d], Tu[i, d] = M.ytT(T, c["over"]), M.ytT(T, c["under"])
            if "folie" in c:
                Tf[i, d] = M.ytT(T, c["folie"])

    _, F = A.kor(T0, spara=spara, falt=set(falt))
    dT = To - Tu
    mu = IN["fukt"]["mu_eps"]
    res = dict(namn=fall.get("namn", ""), P=P, m=m, A=A, T0=T0, it=it, avv=avv, K=K, To=To, Tu=Tu, Tf=Tf, F=F,
               celler=m["N"], tid=time.time() - t0)
    for typ, _ in TYPER:
        ii = [i for i, c in enumerate(K) if c["typ"] == typ]
        i = min(ii, key=lambda i: dT[i].min())
        d = int(dT[i].argmin())
        dk = P["t_fot"] if typ != "falt" else P["t_eps"]
        Mk, Mn = max(kondens(Tu[j], To[j], dk, mu) for j in ii)
        r = dict(i=i, x=K[i]["x"], dT=float(dT[i, d]), dag=d, n_neg=int((dT[i] < 0).sum()),
                 medel=float(min(dT[j].mean() for j in ii)), Tg=float(Tu[i, d]), Ts=float(To[i, d]), M=Mk, M_dygn=Mn,
                 vinter=float(dT[i][A.pa].mean()),
                 n_neg_alla=int(max((dT[j] < 0).sum() for j in ii)))
        if typ == "falt":
            r["M_folie"], r["M_folie_dygn"] = max(kondens(Tu[j], Tf[j], P["t_eps"] / 2, mu) for j in ii)
            r["dT_folie"] = float(min((Tf[j] - Tu[j]).min() for j in ii))
        res[typ] = r
    res["M"] = max(res["falt"]["M"], res["falt"]["M_folie"], res["plint"]["M"], res["kant"]["M"])
    res["M_dygn"] = max(res["falt"]["M_dygn"], res["falt"]["M_folie_dygn"], res["plint"]["M_dygn"], res["kant"]["M_dygn"])
    res["dT"] = min(res[t]["dT"] for t, _ in TYPER)
    res["n_neg"] = max(res[t]["n_neg_alla"] for t, _ in TYPER)
    print(f"{res['namn'][:40]:40s} " + " | ".join(f"{t} {res[t]['dT']:5.2f} K {datum(res[t]['dag']):>6s} x {res[t]['x']:5.2f}"
                                                for t, _ in TYPER)
          + f" | kondens {res['M']:5.1f} g/m², {res['n_neg']} dygn | {it} it, {res['tid']:.0f} s", flush=True)
    return res


# ------------------------------------------------------------------ beräkning
FALL = [dict(f) for f in IN["fall"]]
RES = [kor(FALL[0])]
bas = RES[0]
dag_v = int(bas["falt"]["dag"])                         # kritiskt dygn för plattan i fält och plintarna (våren)
dag_k = int(bas["kant"]["dag"])                         # kritiskt dygn för kantbalken (sensommaren)
DAG_F = {"vinter": 31, "var": dag_v, "kant": dag_k}
bas = kor(FALL[0], falt=DAG_F.values())
BARA_FIGURER = "figurer" in sys.argv[1:]
RES = [bas] + ([] if BARA_FIGURER else [kor(f) for f in FALL[1:]])
Q = bas["A"].balans(bas["T0"])
kontroll = {} if BARA_FIGURER else dict(nat=kor(dict(FALL[0], namn="Nät: halva cellstorleken"), f=0.5),
                tid=kor(dict(FALL[0], namn=f"Tidssteg: {24 // (2 * IN['nat']['steg_per_dygn'])} h"), n=2 * IN["nat"]["steg_per_dygn"]),
                rand=kor(dict(FALL[0], namn="Marken 4 husbredder åt sidorna och nedåt", utbredning=4.0)))

# ------------------------------------------------------------------ figurer
for _f in sorted(FONTS.glob("*.ttf")) if FONTS.is_dir() else []:
    font_manager.fontManager.addfont(str(_f))
plt.rcParams.update({"font.family": "Carlito", "font.size": 7.5, "svg.fonttype": "none", "axes.linewidth": 0.5,
                     "hatch.linewidth": 0.35, "xtick.major.width": 0.5, "ytick.major.width": 0.5})
INK, BLA, ROD = "#1e1e1e", "#2c4a6e", "#b5463a"
FARG = dict(mark="#efe6d2", makadam="#c7c2b8", betong="#d4d2cc", cellplast="#dde6f0", leca="#b9b3a9")
VISA = dict(mark="Fyllning och mark", makadam="Makadam", betong="Betong", cellplast="Cellplast", leca="Leca")
CM = 1 / 2.54


def rita_delar(ax, m, lw=0.4, fyll=True, kant=INK):
    P, g = m["P"], m["g"]
    if fyll:
        X0, X1 = m["ex"][0], m["ex"][-1]
        ax.add_patch(Rectangle((X0, m["ez"][0]), X1 - X0, P["h_rum"] - m["ez"][0], fc=FARG["mark"], ec="none", zorder=0))
        for x0, x1, zm in ((X0, g["xv"], P["mark_v"]), (g["xo"], X1, P["mark_o"])):
            ax.add_patch(Rectangle((x0, zm), x1 - x0, P["h_rum"] + 1, fc="white", ec="none", zorder=0.5))
        ax.add_patch(Rectangle((g["xiv"], 0), g["xio"] - g["xiv"], P["h_rum"], fc="white", ec="none", zorder=0.5))
    for namn, x0, x1, z0, z1 in m["D"]:
        ax.add_patch(Rectangle((x0, z0), x1 - x0, z1 - z0, fc=FARG[namn] if fyll else "none", ec=kant, lw=lw,
                               zorder=1 if fyll else 3))
    # folien mellan cellplastskikten och golvvärmen
    ax.plot([g["xv"] + P["b_balk"], g["xo"] - P["b_balk"]], [g["zfolie"]] * 2, color=BLA, lw=0.6, ls=(0, (3, 1.5)), zorder=4)
    ax.plot([g["gv"][0], g["gv"][1]], [g["gv"][2]] * 2, color=ROD, lw=0.8, ls=(0, (1, 1)), zorder=4)
    for x0, x1, zm in ((m["ex"][0], g["xv"], P["mark_v"]), (g["xo"], m["ex"][-1], P["mark_o"])):
        ax.plot([x0, x1], [zm, zm], color=INK, lw=0.7, zorder=4)


def matt(ax, p0, p1, txt, off, fs=6.3, rot=None):
    (x0, y0), (x1, y1) = p0, p1
    if abs(y1 - y0) < 1e-9:
        y = y0 + off
        ax.annotate("", (x0, y), (x1, y), arrowprops=dict(arrowstyle="<->", lw=0.4, color=INK, shrinkA=0, shrinkB=0))
        ax.text((x0 + x1) / 2, y + (0.012 if off > 0 else -0.012), txt, ha="center", va="bottom" if off > 0 else "top", fontsize=fs)
    else:
        x = x0 + off
        ax.annotate("", (x, y0), (x, y1), arrowprops=dict(arrowstyle="<->", lw=0.4, color=INK, shrinkA=0, shrinkB=0))
        ax.text(x + (0.012 if off > 0 else -0.012), (y0 + y1) / 2, txt, ha="left" if off > 0 else "right", va="center",
                fontsize=fs, rotation=rot or 0)


def rita_sektion(path, m):
    P, g = m["P"], m["g"]
    fig = plt.figure(figsize=(17 * CM, 11.6 * CM))
    gs = fig.add_gridspec(2, 2, width_ratios=[1, 1.55], height_ratios=[1.55, 1], hspace=0.12, wspace=0.08)
    # plan: källarens väggar, rören och sektionen
    ax = fig.add_subplot(gs[0, 0])
    for nm, w in VAGG.items():
        ax_, c, a, b = w[:4]
        xy = ([a, b], [c, c]) if ax_ == "h" else ([c, c], [a, b])
        ax.plot(np.array(xy[0]) / 1000, np.array(xy[1]) / 1000, color=INK, lw=2.4, solid_capstyle="projecting")
    for nm, (x, y) in PEL.items():
        ax.plot(x / 1000, y / 1000, "s", ms=2.2, color=INK)
    for nm, xc, b in P["plint"]:
        y = PEL[nm][1] / 1000
        ax.add_patch(Rectangle((xc - b / 2, y - b / 2), b, b, fc="none", ec=INK, lw=0.4, ls=(0, (2, 1))))
    ys = IN["sektion"]["y"] / 1000
    ax.plot([-1.3, 15.1], [ys, ys], color=ROD, lw=0.8, ls=(0, (6, 2, 1, 2)))
    for x, ha in ((-1.3, "right"), (15.1, "left")):
        ax.text(x, ys, " A ", ha=ha, va="center", fontsize=8, color=ROD, weight="bold")
    for nm, dx in ((IN["sektion"]["vagg_v"], -0.6), (IN["sektion"]["vagg_o"], 0.6)):
        ax.text(VAGG[nm][1] / 1000 + dx, 4.4, nm, ha="center", va="center", fontsize=6.3, style="italic", rotation=90)
    ax.set_xlim(-2.2, 16.0); ax.set_ylim(-0.8, 13.4); ax.set_aspect("equal")
    ax.set_xticks([0, 5, 10]); ax.set_yticks([0, 5, 10]); ax.tick_params(labelsize=6.3, length=2)
    ax.set_xlabel("x (m)", fontsize=6.5, labelpad=1); ax.set_ylabel("y (m)", fontsize=6.5, labelpad=1)
    ax.set_title("a) Källarens väggar och rör, plan", fontsize=7.5, loc="left")
    # detalj vid V21
    ax = fig.add_subplot(gs[0, 1])
    rita_delar(ax, m)
    xv, xiv = g["xv"], g["xiv"]
    t = [v / 1000 for v in P["vagg_skikt"]]
    matt(ax, (xv, 0.42), (xiv, 0.42), "", 0)
    for a, b, s in ((xv, xv + t[0], "100"), (xv + t[0], xv + t[0] + t[1], "150"), (xv + t[0] + t[1], xiv, "100")):
        ax.annotate("", (a, 0.42), (b, 0.42), arrowprops=dict(arrowstyle="<->", lw=0.4, color=INK, shrinkA=0, shrinkB=0))
        ax.text((a + b) / 2, 0.432, s, ha="center", va="bottom", fontsize=6.3)
    matt(ax, (xv, -P["h_balk"]), (xv + P["b_balk"], -P["h_balk"]), f"{P['b_balk'] * 1000:.0f}", -0.17)
    matt(ax, (xv - P["t_ben"], 0), (xv, 0), f"{P['t_ben'] * 1000:.0f}", 0.06)
    xr = 1.13
    for z0, z1, s in ((-P["h_platta"], 0, f"{P['h_platta'] * 1000:.0f}"), (g["zfolie"], -P["h_platta"], "100"),
                      (g["zf"], g["zfolie"], "100"), (g["zf"] - P["t_makadam"], g["zf"], f"{P['t_makadam'] * 1000:.0f}")):
        ax.annotate("", (xr, z0), (xr, z1), arrowprops=dict(arrowstyle="<->", lw=0.4, color=INK, shrinkA=0, shrinkB=0))
        ax.text(xr + 0.015, (z0 + z1) / 2, s, ha="left", va="center", fontsize=6.3)
    for z0, z1, s in ((-P["h_balk"], 0, f"{P['h_balk'] * 1000:.0f}"), (g["zk"], -P["h_balk"], f"{P['t_fot'] * 1000:.0f}")):
        xx = xv + P["b_balk"] - 0.04
        ax.annotate("", (xx, z0), (xx, z1), arrowprops=dict(arrowstyle="<->", lw=0.4, color=INK, shrinkA=0, shrinkB=0))
        ax.text(xx - 0.012, (z0 + z1) / 2, s, ha="right", va="center", fontsize=6.3)
    etik = [("Leca Isoblokk 35", (xv + 0.05, 0.25), (xv - 0.42, 0.33)),
            ("fyllning", (xv - 0.35, 0.05), (xv - 0.42, 0.18)),
            ("L-element: ben och fot\ncellplast 100", (xv - 0.08, -0.25), (xv - 0.62, -0.42)),
            ("makadam på berg", (xv + 0.6, g["zf"] - 0.08), (xv + 0.2, -0.56)),
            ("kantbalk", (xv + 0.36, -0.13), (xv + 0.1, -0.13)),
            ("plastfolie", (0.80, g["zfolie"]), (0.55, -0.27)),
            ("golvvärme", (0.62, g["gv"][2]), (0.66, 0.08)),
            ("platta 100 på cellplast\nS100 2 × 100", (0.95, -0.05), (0.80, 0.25))]
    for txt, p, q in etik:
        ax.annotate(txt, p, q, fontsize=6.3, ha="center", va="center", arrowprops=dict(arrowstyle="-", lw=0.35, color=INK),
                    bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.85))
    ax.set_xlim(xv - 0.85, 1.25); ax.set_ylim(-0.62, 0.52); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title("b) Detalj vid V21 (mått i mm). Samma vid V14", fontsize=7.5, loc="left")
    # hela sektionen
    ax = fig.add_subplot(gs[1, :])
    rita_delar(ax, m, lw=0.3)
    for nm, xc, b in P["plint"]:
        ax.text(xc, 0.12, nm, ha="center", va="bottom", fontsize=6.3)
        ax.plot([xc, xc], [0, P["h_rum"]], color="#777", lw=1.2, zorder=2)
    ax.text((g["xiv"] + g["xio"]) / 2, 1.25, "källare", ha="center", va="center", fontsize=7, style="italic", color="#555")
    for x, zm, ha in ((g["xv"] - 0.25, P["mark_v"], "right"), (g["xo"] + 0.25, P["mark_o"], "left")):
        ax.text(x, zm + 0.07, f"mark +{fmt(zm, 2)} m", ha=ha, va="bottom", fontsize=6.3)
    for nm, x in ((IN["sektion"]["vagg_v"], g["xv"] + 0.175), (IN["sektion"]["vagg_o"], g["xo"] - 0.175)):
        ax.text(x, P["h_rum"] + 0.08, nm, ha="center", va="bottom", fontsize=6.3, style="italic")
    matt(ax, (g["xv"], 0), (g["xo"], 0), f"{fmt(g['B'] * 1000, 0)}", -0.9)
    ax.text(-3.4, -1.45, f"Marken fortsätter {fmt(P['nat']['utbredning'] * g['B'], 0)} m åt sidorna och nedåt", fontsize=6.3,
            ha="left", va="center", style="italic", color="#555")
    ax.set_xlim(-3.5, g["xo"] + 3.5); ax.set_ylim(-1.75, P["h_rum"] + 0.35); ax.set_aspect("equal")
    ax.tick_params(labelsize=6.3, length=2)
    ax.set_xlabel("x (m)", fontsize=6.5, labelpad=1); ax.set_ylabel("z (m)", fontsize=6.5, labelpad=1)
    ax.set_title("c) Sektion A–A, z från bottenplattans överkant", fontsize=7.5, loc="left")
    h = [Rectangle((0, 0), 1, 1, fc=FARG[k], ec=INK, lw=0.4) for k in FARG]
    h += [plt.Line2D([], [], color=BLA, lw=0.6, ls=(0, (3, 1.5))), plt.Line2D([], [], color=ROD, lw=0.8, ls=(0, (1, 1)))]
    ax.legend(h, [VISA[k] for k in FARG] + ["Plastfolie", "Golvvärme"], loc="upper center", ncol=7, fontsize=6.5,
              frameon=False, bbox_to_anchor=(0.5, -0.24), handlelength=1.6, columnspacing=1.2)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


def manadsaxel(ax):
    ax.set_xticks(M.MAN); ax.set_xticklabels([s[0].upper() for s in MANAD]); ax.set_xlim(0, 365)
    ax.tick_params(labelsize=6.5, length=2)
    pa = bas["A"].pa
    for d0, d1 in ((0, M.MAN[IN["drift"]["golvvarme"][1]]), (M.MAN[IN["drift"]["golvvarme"][0] - 1], 365)):
        ax.axvspan(d0, d1, color="#f3ece0", zorder=0, lw=0)
    ax.grid(lw=0.3, color="#ccc")


def rita_ar(path, r):
    d = np.arange(365) + 0.5
    fig, axs = plt.subplots(1, 2, figsize=(17 * CM, 6.0 * CM))
    ax = axs[0]
    manadsaxel(ax)
    i = r["falt"]["i"]
    ax.plot(d, r["A"].Tute, color="#999", lw=0.7, label="Ute, markytan")
    ax.step(d, r["A"].Trum, color=INK, lw=0.6, ls=(0, (2, 1)), where="mid", label="Källarens luft")
    ax.plot(d, r["To"][i], color=ROD, lw=1.0, label="Plattans underkant")
    ax.plot(d, r["Tf"][i], color="#c98b3a", lw=0.8, label="Plastfolien")
    ax.plot(d, r["Tu"][i], color=BLA, lw=1.0, label="Marken under cellplasten")
    ax.set_ylim(-2, 30); ax.set_ylabel("°C", fontsize=6.5, labelpad=1)
    ax.legend(fontsize=6.3, loc="upper center", bbox_to_anchor=(0.5, -0.1), frameon=False, ncol=3, handlelength=1.6,
              columnspacing=1.0)
    ax.set_title(f"a) Temperaturer i fält, x = {fmt(r['falt']['x'], 2)} m", fontsize=7.5, loc="left")
    ax = axs[1]
    manadsaxel(ax)
    K = r["K"]
    dT = r["To"] - r["Tu"]
    B2 = (r["m"]["g"]["xv"] + r["m"]["g"]["xo"]) / 2
    kv = min((j for j, c in enumerate(K) if c["typ"] == "kant" and c["x"] < B2), key=lambda j: dT[j].min())
    ko = min((j for j, c in enumerate(K) if c["typ"] == "kant" and c["x"] > B2), key=lambda j: dT[j].min())
    jp = r["plint"]["i"]
    for j, lbl, col, ls in ((r["falt"]["i"], "Platta i fält", ROD, "-"), (jp, f"Plint {plintnamn(r['m'], K[jp]['x'])}", "#c98b3a", "-"),
                            (kv, "Kantbalk vid V21", BLA, (0, (3, 1))), (ko, "Kantbalk vid V14", BLA, "-")):
        ax.plot(d, dT[j], color=col, lw=0.9, ls=ls, label=f"{lbl}, x = {fmt(K[j]['x'], 2)} m")
    ax.axhline(0, color=INK, lw=0.6)
    ax.set_ylim(-2, 14); ax.set_ylabel("K", fontsize=6.5, labelpad=1)
    ax.legend(fontsize=6.3, loc="upper center", bbox_to_anchor=(0.5, -0.1), frameon=False, ncol=2, handlelength=1.6,
              columnspacing=1.0)
    ax.set_title("b) Temperaturskillnad över cellplasten, ΔT", fontsize=7.5, loc="left")
    fig.tight_layout(w_pad=1.5)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


def plintnamn(m, x):
    return min(m["P"]["plint"], key=lambda p: abs(p[1] - x))[0]


def rita_falt(path, r):
    """Temperaturfält: hela sektionen vintertid och vid vårens kritiska dygn, och förstoringar med egen skala."""
    m = r["m"]
    g, P = m["g"], m["P"]
    X, Z = np.meshgrid(m["xc"], m["zc"], indexing="ij")
    fig = plt.figure(figsize=(17 * CM, 15.0 * CM))
    gs = fig.add_gridspec(3, 2, height_ratios=[1, 1, 1.12], hspace=0.36, wspace=0.10)
    hel = (-3.5, g["xo"] + 3.5, -4.0, P["h_rum"])
    xp = r["falt"]["x"]
    vast = r["kant"]["x"] < (g["xv"] + g["xo"]) / 2                 # kantbalken som avgör
    xk = g["xv"] if vast else g["xo"]
    kz = (xk - 2.4, xk + 1.6) if vast else (xk - 1.6, xk + 2.4)
    vk = IN["sektion"]["vagg_v" if vast else "vagg_o"]
    pan = [(gs[0, :], "vinter", hel, np.arange(-2, 28.5, 0.5), 2.0, "a) Vinter med golvvärme"),
           (gs[1, :], "var", hel, np.arange(-2, 28.5, 0.5), 2.0, "b) Våren, kritiskt dygn för plattan"),
           (gs[2, 0], "var", (xp - 2.2, xp + 2.2, -1.1, 0.35), np.arange(14, 19.01, 0.1), 0.5, "c) Förstoring av b"),
           (gs[2, 1], "kant", (*kz, -1.1, 0.9), np.arange(12, 20.01, 0.1), 0.5, f"d) Kantbalken vid {vk}, sensommaren")]
    for spec, nyck, (x0, x1, z0, z1), niv, steg, titel in pan:
        ax = fig.add_subplot(spec)
        dag = DAG_F[nyck]
        F = np.ma.masked_invalid(M.faltvarde(m, r["F"][dag]))
        cs = ax.contourf(X, Z, np.clip(F, niv[0], niv[-1]), levels=niv, cmap="RdYlBu_r", extend="neither")
        cl = ax.contour(X, Z, F, levels=np.arange(np.ceil(niv[0]), niv[-1] + 1e-9, steg), colors=INK, linewidths=0.3)
        ax.clabel(cl, fontsize=5.5, fmt=(lambda v: fmt(v, 0 if steg >= 1 else 1)), inline_spacing=1)
        rita_delar(ax, m, lw=0.3, fyll=False, kant="#444")
        ax.set_xlim(x0, x1); ax.set_ylim(z0, z1); ax.set_aspect("equal")
        ax.tick_params(labelsize=6.3, length=2)
        ax.set_title(f"{titel}, {datum(dag)}. Rum {fmt(r['A'].Trum[dag], 0)} °C, ute {fmt(r['A'].Tute[dag], 1)} °C"
                     if spec in (gs[0, :], gs[1, :]) else f"{titel}, {datum(dag)}", fontsize=7.5, loc="left")
        if spec not in (gs[0, :], gs[1, :]):
            cb = fig.colorbar(cs, ax=ax, orientation="horizontal", fraction=0.06, pad=0.14, aspect=40,
                              ticks=np.arange(niv[0], niv[-1] + 1e-9, 1.0))
            cb.ax.tick_params(labelsize=6.3, length=2); cb.set_label("°C", fontsize=6.5, labelpad=1)
        elif spec == gs[1, :]:
            pb, pa = ax.get_position(), fig.axes[0].get_position()
            cax = fig.add_axes([pb.x1 + 0.015, pb.y0, 0.011, pa.y1 - pb.y0])
            cb = fig.colorbar(cs, cax=cax, ticks=np.arange(0, 29, 4))
            cb.ax.tick_params(labelsize=6.3, length=2); cb.set_label("°C", fontsize=6.5)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


rita_sektion(HERE / "fig_sektion.svg", bas["m"])
rita_ar(HERE / "fig_ar.svg", bas)
rita_falt(HERE / "fig_falt.svg", bas)
if BARA_FIGURER:
    sys.exit()

# ------------------------------------------------------------------ resultat till mallen
P, g = bas["P"], bas["m"]["g"]


def rad(r):
    out = dict(namn=r["namn"], M=fmt(r["M"], 1), n_neg=str(r["n_neg"]))
    for t, _ in TYPER:
        out[t] = fmt(r[t]["dT"], 1)
        out[t + "_dag"] = datum(r[t]["dag"])
    return out


def typrad(r, t, namn):
    x = r[t]
    return dict(namn=namn, dT=fmt(x["dT"], 1), dag=datum(x["dag"]), x=fmt(x["x"], 2), Ts=fmt(x["Ts"], 1), Tg=fmt(x["Tg"], 1),
                n_neg=str(x["n_neg_alla"]), medel=fmt(x["medel"], 1), M=fmt(x["M"], 1))


ma = IN["material"]
ok_vinkel = all(min(r[t]["dT"] for t, _ in TYPER) > 0 for r in RES[1:2])
R = {
    "projekt": IN["projekt"],
    "s": dict(y=fmt(IN["sektion"]["y"], 0), vv=IN["sektion"]["vagg_v"], vo=IN["sektion"]["vagg_o"],
              B=fmt(g["B"] * 1000, 0), mark_v=fmt(P["mark_v"], 2), mark_o=fmt(P["mark_o"], 2), h_rum=fmt(P["h_rum"], 2),
              plintar=", ".join(f"{n} ({fmt(b * 1000, 0)} mm)" for n, _, b in P["plint"]), utbredning=fmt(P["nat"]["utbredning"], 1),
              ut_m=fmt(P["nat"]["utbredning"] * g["B"], 0), djup=fmt(-bas["m"]["ez"][0], 0),
              t_eps=fmt(P["t_eps"] * 1000, 0), h_balk=fmt(P["h_balk"] * 1000, 0), gv_kant=fmt(P["golvvarme_kant"] * 1000, 0),
              gv_z=fmt(P["golvvarme_z"] * 1000, 0)),
    "mat": {k: dict(lam=fmt(v[0], 3 if v[0] < 0.1 else 2), rc=fmt(v[1], 2)) for k, v in ma.items()},
    "kl": dict(Tm=fmt(P["Tm"], 1), A=fmt(P["A"], 1), Tmax=fmt(P["Tm"] + P["A"], 1), Tmin=fmt(P["Tm"] - P["A"], 1),
               dag=datum(P["dag_max"]), Rse=fmt(P["Rse"], 2)),
    "dr": dict(T_gv=fmt(P["T_golvvarme"], 0), Tv=fmt(P["T_rum_vinter"], 0), Ts=fmt(P["T_rum_sommar"], 0),
               fran=MANAD[P["golvvarme"][0] - 1], till=MANAD[P["golvvarme"][1] - 1], Rsi_g=fmt(P["Rsi_golv"], 2),
               Rsi_v=fmt(P["Rsi_vagg"], 2)),
    "fukt": dict(mu=fmt(IN["fukt"]["mu_eps"], 0), M_ref=fmt(IN["fukt"]["M_ref"], 0)),
    "nat": dict(h=fmt(P["nat"]["h_fin"] * 1000, 0), celler=f"{bas['celler']:,}".replace(",", " "),
                celler2=f"{kontroll['nat']['celler']:,}".replace(",", " "), it=str(bas["it"]),
                exp=str(int(np.ceil(np.log10(max(bas["avv"], 1e-15))))), steg=str(24 // IN["nat"]["steg_per_dygn"])),
    "bas": {t: typrad(bas, t, n) for t, n in TYPER},
    "bas_folie": dict(dT=fmt(bas["falt"]["dT_folie"], 1), M=fmt(bas["falt"]["M_folie"], 1)),
    "bas_M": fmt(bas["M"], 1), "bas_n": str(bas["n_neg"]),
    "fall": [rad(r) for r in RES],
    "kontroll": [dict(namn=k["namn"], **{t: fmt(k[t]["dT"], 2) for t, _ in TYPER}) for k in [dict(bas, namn="Grundfall")] + list(kontroll.values())],
    "Q": dict(gv=fmt(Q["golvvarme"] / 3.6e6, 0), rum=fmt(-Q["rum"] / 3.6e6, 0), ute=fmt(-Q["ute"] / 3.6e6, 0),
              fel=fmt(max(100 * abs(Q["golvvarme"] + Q["rum"] + Q["ute"] - Q["lagrat"]) / Q["golvvarme"], 0.01), 2),
              gv_m2=fmt(Q["golvvarme"] / 3.6e6 / ((g["gv"][1] - g["gv"][0])), 0)),
    "min_fall": {r["namn"]: {t: fmt(r[t]["dT"], 1) for t, _ in TYPER} for r in RES},
}
# sammanfattning för texten
FN = {f["namn"]: r for f, r in zip(FALL, RES)}
R["sam"] = dict(
    medel=fmt(min(bas[t]["medel"] for t, _ in TYPER), 1),
    v_falt=fmt(bas["falt"]["vinter"], 1), v_plint=fmt(bas["plint"]["vinter"], 1), v_kant=fmt(bas["kant"]["vinter"], 1),
    M_max=fmt(max(r["M"] for r in RES), 0), M_dygn=str(max(r["M_dygn"] for r in RES)),
    min={n: fmt(r["dT"], 1) for n, r in FN.items()},
    L400=fmt(FN["Utförande L400"]["falt"]["dT"], 1),
)
(HERE / "resultat.json").write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"värmebalans: golvvärme {Q['golvvarme'] / 3.6e6:.0f}, rum {Q['rum'] / 3.6e6:.0f}, ute {Q['ute'] / 3.6e6:.0f}, "
      f"lagrat {Q['lagrat'] / 3.6e6:.2f} kWh/m")

import typst  # noqa: E402

pdf = HERE / f"{IN['projekt']['dokument']}_bottenplatta_fukt.pdf"
typst.compile(str(HERE / "mall.typ"), output=str(pdf), font_paths=["/usr/share/fonts", str(FONTS)])
print(pdf.name)
