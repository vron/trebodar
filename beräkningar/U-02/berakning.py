"""
U-02: nock- och dalbalkarna (K-01) vid lyft. Balken hänger i två punkter symmetriskt kring tyngdpunkten, med
stroppar i en triangel upp till kroken. Iterationen söker det minsta avstånd mellan lyftpunkterna som håller
utnyttjandet under målet i alla balkar; rapporten redovisar det rekommenderade avståndet. Som jämförelse (inte i
rapporten) räknas också lyft i en punkt och gaffeltruck i mitten.

    python berakning.py      -> U-02_lyft_balkar.pdf

Läser indata.toml och balkarna ur ../K-01/indata.toml (och K-01:s resultat.json för jämförelsen med de
dimensionerande snittkrafterna). Egentyngd: limträ med plåtar där plåt finns, annars limträ med distansreglar.
Styvhet: plåtarna fullt samverkande med limträet (limmade); utan plåt bara limträet 200 × 170.
"""
import json
import math
import tomllib
from pathlib import Path

import matplotlib

matplotlib.use("svg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402
import numpy as np  # noqa: E402

HERE = Path(__file__).parent
FONTS = HERE.parent / ".fonts"
IN = tomllib.loads((HERE / "indata.toml").read_text(encoding="utf-8"))
K01 = tomllib.loads((HERE.parent / "K-01" / "indata.toml").read_text(encoding="utf-8"))
R01 = json.load(open(HERE.parent / "K-01" / "resultat.json", encoding="utf-8"))
LY = IN["lyft"]

# ------------------------------------------------------------------ tvärsnitt och material (K-01)
g, st, tr, di = K01["geometri"], K01["stal"], K01["tra"], K01["distans"]
b, t, H = g["b"], g["t_pl"], g["h_tot"]
hw = H - 2 * t                                                         # limträ 170
Es, Et = st["E"], tr["E0mean"]
q_plat = (2 * b * t * st["densitet"] + b * hw * tr["rho_mean"]) * 1e-9 * 9.81      # N/mm (kN/m)
q_utan = (2 * b * di["tjocklek"] * di["densitet"] + b * hw * tr["rho_mean"]) * 1e-9 * 9.81
EI_plat = 2 * Es * (b * t ** 3 / 12 + b * t * ((t + hw) / 2) ** 2) + Et * b * hw ** 3 / 12
EI_utan = Et * b * hw ** 3 / 12
W_tra = b * hw ** 2 / 6
A_tra = b * hw
kh = min((600 / hw) ** 0.1, 1.1)                                       # SS-EN 1995-1-1 3.3(3), limträ
f_md = LY["k_mod"] * kh * tr["fmk"] / tr["gamma_M"]
f_c0d = LY["k_mod"] * 24.5 / tr["gamma_M"]                             # GL30c f_c,0,k = 24,5 (SS-EN 14080)
f_yd = st["fy"] / st["gamma_M0"]
FAKTOR = LY["gamma_G"] * LY["dyn"]
TH = math.radians(LY["vinkel"])


def sv(x, n=0):
    s = f"{x:,.{n}f}".replace(",", " ").replace(".", ",")
    return s.replace("-", "−")


def k01(namn, nyckel):
    """K-01:s dimensionerande värde (kNm eller kN) ur resultat.json, där talen är formaterade."""
    v = next(x for x in R01["balkar"] if x["namn"] == namn)[nyckel]
    return abs(float(str(v).replace("−", "-").replace(" ", "").replace(" ", "").replace(",", ".")))


def lyft(B, stod, n=4000, axial=True):
    """Balken B hängande i punkterna stod (förskjutning från tyngdpunkten, mm). Karakteristisk egentyngd; snittkrafter,
    spänningar (dimensionerande med FAKTOR) och nedböjning (karakteristisk)."""
    L = B["total"]
    x = np.linspace(0, L, n + 1); dx = x[1] - x[0]
    plat = np.zeros_like(x, bool)
    for a, c in B["platar"]:
        plat |= (x >= a) & (x <= c)
    q = np.where(plat, q_plat, q_utan)
    EI = np.where(plat, EI_plat, EI_utan)
    W = float(np.trapezoid(q, x)); xc = float(np.trapezoid(q * x, x)) / W
    sp = [xc + s for s in stod]
    if len(sp) == 1:
        R = [W]
    else:
        a, c = sp
        Rc = (np.trapezoid(q * x, x) - W * a) / (c - a)
        R = [W - Rc, Rc]
    V = -np.concatenate([[0], np.cumsum((q[1:] + q[:-1]) / 2 * dx)])
    for p, r in zip(sp, R):
        V += np.where(x >= p, r, 0.0)
    M = np.concatenate([[0], np.cumsum((V[1:] + V[:-1]) / 2 * dx)])           # positivt: dragen underkant
    k = M / EI
    th = np.concatenate([[0], np.cumsum((k[1:] + k[:-1]) / 2 * dx)])
    w = np.concatenate([[0], np.cumsum((th[1:] + th[:-1]) / 2 * dx)])
    if len(sp) == 1:
        i = int(np.argmin(abs(x - sp[0]))); w = w - w[i] - th[i] * (x - x[i])
    else:
        i, j = (int(np.argmin(abs(x - p))) for p in sp)
        w = w - w[i] - (w[j] - w[i]) / (x[j] - x[i]) * (x - x[i])
    # stropparna: tryck i balken mellan lyftpunkterna, R / tan θ
    N = np.zeros_like(x)
    if len(sp) == 2 and axial:
        N = np.where((x >= sp[0]) & (x <= sp[1]), R[0] / math.tan(TH), 0.0)
    Md, Nd = FAKTOR * M, FAKTOR * N
    s_tra = np.where(plat, np.abs(Md) * (hw / 2) * Et / EI_plat, np.abs(Md) / W_tra)
    s_stal = np.where(plat, np.abs(Md) * (H / 2) * Es / EI_plat, 0.0)
    u_tra = s_tra / f_md + Nd / A_tra / f_c0d
    u = np.maximum(u_tra, s_stal / f_yd)
    i = int(np.argmax(u))
    return dict(L=L, W=W / 1e3, xc=xc, sp=sp, R=[r / 1e3 for r in R], M=float(np.abs(M).max()) / 1e6,
                Md=float(np.abs(Md).max()) / 1e6, Md_plat=float(np.abs(Md[plat]).max()) / 1e6 if plat.any() else 0.0,
                Vd=float(np.abs(FAKTOR * V).max()) / 1e3, s_tra=float(s_tra.max()), s_stal=float(s_stal.max()),
                Nd=float(Nd.max()) / 1e3, u=float(u.max()), x_u=float(x[i]), plat_u=bool(plat[i]),
                w=float(np.abs(w).max()), x=x, M_x=M, plat=plat)


# ------------------------------------------------------------------ iteration: minsta avstånd per balk
BALKAR = K01["balk"]
smin = {}
for B in BALKAR:
    s = 0.0
    while s < B["total"]:
        r = lyft(B, [-s / 2, s / 2]) if s > 0 else lyft(B, [0.0])
        if r["u"] <= LY["mal"]:
            break
        s += LY["steg"]
    smin[B["namn"]] = s
S_REK = math.ceil(max(smin.values()) / LY["avrunda"]) * LY["avrunda"]
REK = [lyft(B, [-S_REK / 2, S_REK / 2]) for B in BALKAR]
EN = [lyft(B, [0.0]) for B in BALKAR]                                  # jämförelse: en punkt
TRUCK = [lyft(B, [-500.0, 500.0], axial=False) for B in BALKAR]        # jämförelse: gafflar c/c 1 m kring tyngdpunkten

print(f"f_md {f_md:.1f} MPa (k_h {kh:.2f}), faktor {FAKTOR:.2f}")
for B, r, e, tk in zip(BALKAR, REK, EN, TRUCK):
    print(f"{B['namn']}: L {r['L']}, {r['W']:.2f} kN, tp {r['xc']:.0f}; s_min {smin[B['namn']]:.0f}; "
          f"rek u {r['u']:.0%} w {r['w']:.0f}; en punkt u {e['u']:.0%} (x {e['x_u']:.0f}, plåt {e['plat_u']}) w {e['w']:.0f}; "
          f"truck u {tk['u']:.0%}")
print(f"rekommenderat avstånd {S_REK} mm")


# ------------------------------------------------------------------ figur: den styrande balken
def figur(path):
    fp = FONTS / "Carlito-Regular.ttf"
    if fp.exists():
        font_manager.fontManager.addfont(str(fp))
    plt.rcParams.update({"font.family": "Carlito", "font.size": 7, "svg.fonttype": "none"})
    j = int(np.argmax([smin[B["namn"]] for B in BALKAR]))
    B, r = BALKAR[j], REK[j]
    L = r["L"] / 1000
    fig, ax = plt.subplots(figsize=(6.7, 2.2))
    hb = 0.19
    ax.add_patch(plt.Rectangle((0, 0), L, hb, fc="#ecdcb8", ec="#2b2b2b", lw=0.6))
    for a, c in B["platar"]:
        for y0 in (0, hb - 0.03):
            ax.add_patch(plt.Rectangle((a / 1000, y0), (c - a) / 1000, 0.03, fc="#5a5f66", ec="none"))
    xc = r["xc"] / 1000
    xa, xb = (p / 1000 for p in r["sp"])
    hk = (xb - xa) / 2 * math.tan(TH)
    ax.plot([xa, xc, xb], [hb, hb + hk, hb], color="#b5463a", lw=0.9)
    ax.plot([xc, xc], [hb + hk, hb + hk + 0.35], color="#2b2b2b", lw=0.9)
    ax.plot([xc, xc], [-0.12, hb + 0.12], color="#2b2b2b", lw=0.5, ls=(0, (4, 2)))
    ax.text(xc + 0.1, -0.1, "tyngdpunkt", va="top", fontsize=7)
    ax.text(xa + 0.45, hb + 0.08, f"{LY['vinkel']}°", va="bottom", fontsize=7)
    ax.annotate("", (xa, -0.45), (xb, -0.45), arrowprops=dict(arrowstyle="<->", lw=0.5))
    for xx in (xa, xb):
        ax.plot([xx, xx], [-0.05, -0.55], color="#2b2b2b", lw=0.4)
    ax.text((xa + xb) / 2, -0.52, f"s = {sv(S_REK)}", ha="center", va="top", fontsize=7)
    ax.annotate("", (0, -1.05), (L, -1.05), arrowprops=dict(arrowstyle="<->", lw=0.5))
    ax.text(L / 2, -1.12, f"{B['namn']}, L = {sv(r['L'])}", ha="center", va="top", fontsize=7)
    ax.text(0, hb + 0.08, "x = 0", va="bottom", fontsize=7)
    ax.set_xlim(-0.3, L + 0.3); ax.set_ylim(-1.5, hb + hk + 0.45)
    ax.set_aspect("equal"); ax.axis("off")
    fig.savefig(path, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


figur(HERE / "fig_lyft.svg")

# ------------------------------------------------------------------ resultat och rapport
andel_M = max(r["Md_plat"] / max(k01(B["namn"], "Mmax"), k01(B["namn"], "Mmin")) for B, r in zip(BALKAR, REK))
andel_V = max(r["Vd"] / k01(B["namn"], "V") for B, r in zip(BALKAR, REK))
R = dict(
    projekt=IN["projekt"],
    ly=dict(dyn=sv(LY["dyn"], 1), gG=sv(LY["gamma_G"], 2), faktor=sv(FAKTOR, 2), kmod=sv(LY["k_mod"], 1),
            kh=sv(kh, 2), fmd=sv(f_md, 1), fyd=sv(f_yd, 0), vinkel=str(LY["vinkel"]), mal=f"{LY['mal']:.0%}".replace("%", " %"),
            s=sv(S_REK), steg=sv(LY["steg"]), avrunda=sv(LY["avrunda"]),
            q_plat=sv(q_plat, 2), q_utan=sv(q_utan, 2)),
    balkar=[dict(namn=B["namn"], L=sv(r["L"]), W=sv(r["W"], 1), xc=sv(r["xc"]),
                 x1=sv(r["sp"][0]), x2=sv(r["sp"][1]), smin=sv(smin[B["namn"]]),
                 F=sv(max(r["R"]) / math.sin(TH), 1), Md=sv(r["Md"], 1), s_tra=sv(r["s_tra"], 1),
                 s_stal=sv(r["s_stal"], 0), u=f"{r['u']:.0%}".replace("%", " %"), w=sv(r["w"], 0))
            for B, r in zip(BALKAR, REK)],
    styr=BALKAR[int(np.argmax([smin[B["namn"]] for B in BALKAR]))]["namn"],
    umax=f"{max(r['u'] for r in REK):.0%}".replace("%", " %"),
    andel_M=f"{andel_M:.0%}".replace("%", " %"), andel_V=f"{andel_V:.0%}".replace("%", " %"),
    jfr=dict(en={B["namn"]: dict(u=e["u"], w=e["w"], plat=e["plat_u"]) for B, e in zip(BALKAR, EN)},
             truck={B["namn"]: dict(u=tk["u"]) for B, tk in zip(BALKAR, TRUCK)}, smin=smin),
)
(HERE / "resultat.json").write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8")

import typst  # noqa: E402

pdf = HERE / f"{IN['projekt']['dokument']}_lyft_balkar.pdf"
typst.compile(str(HERE / "mall.typ"), output=str(pdf), font_paths=["/usr/share/fonts", str(FONTS)])
print(pdf.name)
