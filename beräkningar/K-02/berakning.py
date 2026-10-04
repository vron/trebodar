"""
K-02: stationär värmeledning i 2D kring nockbalken vintertid.

    python berakning.py            -> K-02_varmeflode_nockbalk.pdf

Läser indata.toml, räknar temperaturfältet med finita element (termik.py), ritar figurer och
sätter ihop PDF via Typst (mall.typ). Kräver: pip install typst matplotlib numpy scipy triangle
"""
import copy
import json
import math
import tomllib
from pathlib import Path

import matplotlib

matplotlib.use("svg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.tri as mtri  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Polygon  # noqa: E402

import termik  # noqa: E402

HERE = Path(__file__).parent
IN = tomllib.loads((HERE / "indata.toml").read_text(encoding="utf-8"))
g, ma, rd, ls, nat = IN["geometri"], IN["material"], IN["rand"], IN["luftskikt"], IN["nat"]


def fmt(x, n=1):
    from decimal import Decimal, ROUND_HALF_UP
    q = Decimal(repr(float(x))).quantize(Decimal(1).scaleb(-n), rounding=ROUND_HALF_UP)
    if q == 0:
        q = abs(q)
    s = f"{q:,.{n}f}".replace(",", " ").replace(".", ",")
    return s.replace("-", "−")


SIGMA = 5.67e-8
a = math.radians(g["takvinkel"])
B = g["balk_b"] / 2


def h_strl(T_c, eps):
    """Strålning mellan två parallella ytor vid medeltemperaturen T_c [°C]: 4 σ T³ / (1/ε + 1/ε − 1)."""
    return 4 * SIGMA * (T_c + 273.15) ** 3 / (2 / eps - 1)


def lam_luft(d_mm):
    """Ekvivalent λ för stillastående luftskikt med tjockleken d (inklusive strålning), SS-EN ISO 6946."""
    R = float(np.interp(d_mm, ls["d"], ls["R"]))
    return max(d_mm / 1000 / R, ls["lambda_min"]) if R > 0 else ls["lambda_min"]


def material(fall):
    f_tb = ma["takbalk_b"] / ma["takbalk_cc"]
    f_rg = ma["regel_b"] / ma["regel_cc"]
    lam_iso = ma["isolering"] if fall.get("utan_takbalkar") else (1 - f_tb) * ma["isolering"] + f_tb * ma["limtra"]
    y_a3 = info["a3"][1]

    def lam(rn, c):
        if rn.startswith("plat"):
            return ma["stal"]
        if rn == "limtra":
            return ma["limtra"]
        if rn == "masonit":
            return ma["masonit"]
        if rn == "isolering":
            return lam_iso
        if rn == "gips":
            return ma["gips"]
        if rn == "luft":
            x = c[0]
            if x < B:                                   # fickan under balken: tjockleken växer från mitten
                d = min(g["installation"], (-info["H"] - (y_a3 - x * math.tan(a))) * math.cos(a))
                if "eps_plat" in fall:                  # ledning + strålning mellan underplåt och gips
                    e1, e2 = fall["eps_plat"], rd["emissivitet"]
                    h_r = 4 * SIGMA * (rd["T_ficka"] + 273.15) ** 3 / (1 / e1 + 1 / e2 - 1)
                    return rd["lambda_luft"] + h_r * d / 1000
                return lam_luft(d)
            return (1 - f_rg) * lam_luft(g["installation"]) + f_rg * ma["limtra"]
        raise KeyError(rn)
    return lam, lam_iso


def kor(fall, out, namn):
    T_ute, T_inne = fall.get("T_ute", rd["T_ute"]), fall.get("T_inne", rd["T_inne"])
    h_r = h_strl(T_ute, rd["emissivitet"])
    h_ute = fall.get("h_ute", rd["h_ute_konv"] + h_r)
    h_inne = fall.get("h_inne", rd["h_inne"])
    h_plat = None
    if "eps_plat" in fall:
        e1, e2 = fall["eps_plat"], rd["emissivitet"]
        h_plat = rd["h_ute_konv"] + 4 * SIGMA * (T_ute + 273.15) ** 3 / (1 / e1 + 1 / e2 - 1)
    lam, lam_iso = material(fall)
    T, lam_e, q = termik.los(out, namn, lam, h_ute, T_ute, h_inne, T_inne, h_plat)
    To = termik.medel(out, T, namn, "plat_over")
    Tu = termik.medel(out, T, namn, "plat_under")
    return dict(namn=fall["namn"], T=T, lam_e=lam_e, q=2 * q[10], To=To, Tu=Tu, dT=Tu[0] - To[0],
                h_ute=h_ute, h_inne=h_inne, T_ute=T_ute, T_inne=T_inne, lam_iso=lam_iso)


# ------------------------------------------------------------------ geometri och nät
reg, ytter, inner, info = termik.geometri(g)
ytor = dict(plat_over=nat["max_yta_plat"], limtra=nat["max_yta_balk"], plat_under=nat["max_yta_plat"],
            masonit=nat["max_yta_tunn"], isolering=nat["max_yta_ovr"], luft=nat["max_yta_tunn"] * 2, gips=nat["max_yta_tunn"] * 2)
out, namn = termik.natverk(reg, ytter, inner, ytor)
FALL = [dict(f) for f in IN["kanslighet"]]
RES = [kor(f, out, namn) for f in FALL]
bas = RES[0]
for r in RES:
    print(f"{r['namn']:45s} över {r['To'][0]:6.2f}  under {r['Tu'][0]:6.2f}  skillnad {r['dT']:5.2f} K  q {r['q']:.1f} W/m")

# nätkontroll: halverade elementytor (två gånger)
ytor2 = {k: v / 4 for k, v in ytor.items()}
out2, namn2 = termik.natverk(reg, ytter, inner, ytor2)
bas2 = kor(FALL[0], out2, namn2)

# endimensionell kontroll vid modellens ände (långt från balken)
lam_f, lam_iso = material(FALL[0])
f_rg = ma["regel_b"] / ma["regel_cc"]
lam_inst = (1 - f_rg) * lam_luft(g["installation"]) + f_rg * ma["limtra"]
skikt = [("Luftspalt, ytövergång", 1 / bas["h_ute"]), ("Hård träfiberskiva", g["masonit"] / 1000 / ma["masonit"]),
         ("Isolering med takbalkar", g["isolering"] / 1000 / lam_iso), ("Installationsspalt", g["installation"] / 1000 / lam_inst),
         ("Gipsskiva", g["gips"] / 1000 / ma["gips"]), ("Rumssidan, ytövergång", 1 / bas["h_inne"])]
R1 = sum(r for _, r in skikt)
U1 = 1 / R1
# FE-temperatur på rumssidans yta vid modellens ände jämfört med 1D
X = out["vertices"]
E4 = info["E"][4]
i_end = int(np.argmin(np.linalg.norm(X - E4, axis=1)))
T_yta_1d = bas["T_inne"] - (bas["T_inne"] - bas["T_ute"]) * (1 / bas["h_inne"]) / R1
q1d = U1 * (bas["T_inne"] - bas["T_ute"])                         # W/m²
L_tak = 2 * g["tak_langd"] / 1000                                  # takytans längd i modellen, båda sidor [m]
psi = (bas["q"] - q1d * L_tak) / (bas["T_inne"] - bas["T_ute"])  # balkens tillskott [W/(m·K)] relativt takytan

# ------------------------------------------------------------------ figurer
FARG = dict(plat_over="#8d949c", plat_under="#8d949c", limtra="#e2c48f", masonit="#b5763c", isolering="#f2e27a",
            luft="#ffffff", gips="#d9d9d9")


def spegla(poly):
    return [(-x, y) for x, y in poly]


def rita_geometri(path):
    fig, ax = plt.subplots(figsize=(6.6, 2.7))
    for k, poly in reg.items():
        for p in (poly, spegla(poly)):
            ax.add_patch(Polygon(p, closed=True, fc=FARG[k], ec="#333", lw=0.35, hatch=("////" if k.startswith("plat") else None)))
    # luftspalt ovanför taket och rum under gipsen
    E0, E4 = info["E"][0], info["E"][4]
    top = [(-E0[0], E0[1]), (-B, 0), (B, 0), (E0[0], E0[1])]
    ax.fill([p[0] for p in top] + [E0[0], -E0[0]], [p[1] for p in top] + [E0[1] + 90, E0[1] + 90], color="#cfe0f2", lw=0, zorder=0)
    ax.fill([p[0] for p in top][::-1] + [-E0[0]], [y + 90 for y in [p[1] for p in top]][::-1] + [E0[1] + 90], color="#cfe0f2", lw=0, zorder=0)
    ax.text(-330, 20, f"luftspalt, {fmt(rd['T_ute'], 0)} °C", ha="center", va="center", fontsize=7)
    ax.text(0, -480, f"rum, +{fmt(rd['T_inne'], 0)} °C", ha="center", va="center", fontsize=7)
    s, n = info["s"], info["n"]
    lab = [("hård träfiberskiva " + fmt(g["masonit"], 0) + " mm", 1.5),
           ("träfiberisolering " + fmt(g["isolering"], 0) + " mm", g["masonit"] + g["isolering"] / 2),
           ("installationsspalt " + fmt(g["installation"], 0) + " mm", g["masonit"] + g["isolering"] + g["installation"] / 2),
           ("gipsskiva " + fmt(g["gips"], 0) + " mm", g["masonit"] + g["isolering"] + g["installation"] + g["gips"] / 2)]
    Eg = info["E"]
    xe = max(p[0] for p in Eg) + 40
    ylab = []
    for k_, (txt, dpt) in enumerate(lab):
        P_ = np.array([B, 0]) + g["tak_langd"] * s - dpt * n          # skiktets mitt vid modellens ände
        yl = P_[1] + 70 if not ylab else min(P_[1] + 40, ylab[-1] - 58)
        ylab.append(yl)
        ax.plot([P_[0], xe - 8], [P_[1], yl], color="#333", lw=0.4)
        ax.text(xe, yl, txt, fontsize=6.3, ha="left", va="center")
    ax.annotate("stålplåt 200×10", xy=(60, -5), xytext=(150, 160), fontsize=6.3, arrowprops=dict(arrowstyle="-", lw=0.4))
    ax.annotate("limträ 200×170", xy=(-50, -95), xytext=(-420, 160), fontsize=6.3, arrowprops=dict(arrowstyle="-", lw=0.4))
    ax.annotate("stålplåt 200×10", xy=(-60, -185), xytext=(-360, -300), fontsize=6.3, arrowprops=dict(arrowstyle="-", lw=0.4))
    ax.set_xlim(-info["E"][4][0] - 10, info["E"][4][0] + 290); ax.set_ylim(info["E"][4][1] - 10, 200)
    ax.set_aspect("equal"); ax.axis("off")
    fig.savefig(path, bbox_inches="tight", pad_inches=0.02); plt.close(fig)


def rita_falt(path, r, zoom=None):
    X = out["vertices"]; Tr = out["triangles"]
    Xf = np.r_[X, X * [-1, 1]]
    Tf = np.r_[Tr, Tr + len(X)]
    T = np.r_[r["T"], r["T"]]
    tri = mtri.Triangulation(Xf[:, 0], Xf[:, 1], Tf)
    fig, ax = plt.subplots(figsize=(6.6, 3.0 if zoom is None else 3.3))
    lev = np.arange(math.floor(r["T_ute"] / 5) * 5, r["T_inne"] + 5, 2.5)
    cf = ax.tricontourf(tri, T, levels=lev, cmap="RdYlBu_r")
    cs = ax.tricontour(tri, T, levels=lev[::2], colors="#222", linewidths=0.35)
    ax.clabel(cs, fmt=lambda v: fmt(v, 0), fontsize=5.5, inline_spacing=1)
    for k, poly in reg.items():
        for p in (poly, spegla(poly)):
            ax.add_patch(Polygon(p, closed=True, fc="none", ec="#333", lw=0.3))
    cb = fig.colorbar(cf, ax=ax, shrink=0.8, pad=0.01)
    cb.set_label("°C", fontsize=7); cb.ax.tick_params(labelsize=6)
    if zoom:
        ax.set_xlim(-zoom[0], zoom[0]); ax.set_ylim(zoom[1], zoom[2])
    ax.set_aspect("equal"); ax.axis("off")
    fig.savefig(path, bbox_inches="tight", pad_inches=0.02); plt.close(fig)


def rita_profil(path, r):
    """Temperatur längs nockens mittlinje (x = 0) från luftspalten till rummet."""
    X = out["vertices"]
    sel = np.abs(X[:, 0]) < 1e-6
    y, T = X[sel, 1], r["T"][sel]
    o = np.argsort(-y)
    fig, ax = plt.subplots(figsize=(3.2, 2.4))
    ax.plot(T[o], -y[o], color="#1e1e1e", lw=0.9)
    for y0, y1, c in ((0, g["plat_t"], "#8d949c"), (g["plat_t"] + g["tra_h"], info["H"], "#8d949c"),
                      (g["plat_t"], g["plat_t"] + g["tra_h"], "#f3e3c3"), (info["H"], -info["a3"][1], "#ffffff"),
                      (-info["a3"][1], -info["a4"][1], "#d9d9d9")):
        ax.axhspan(y0, y1, color=c, lw=0, zorder=0)
    ax.set_ylim(-info["a4"][1] + 5, -5); ax.set_xlim(r["T_ute"] - 2, r["T_inne"] + 2)
    ax.set_xlabel("temperatur (°C)", fontsize=7); ax.set_ylabel("djup från balkens ovansida (mm)", fontsize=7)
    ax.tick_params(labelsize=6.5)
    for sp_ in ("top", "right"):
        ax.spines[sp_].set_visible(False)
    ax.text(r["To"][0] + 1, 5, "överplåt", fontsize=6.3, va="center")
    ax.text(r["Tu"][0] - 1, info["H"] - 5, "underplåt", fontsize=6.3, va="center", ha="right")
    fig.savefig(path, bbox_inches="tight", pad_inches=0.02); plt.close(fig)


plt.rcParams.update({"font.family": "Carlito", "font.size": 7.5, "svg.fonttype": "none"})
rita_geometri(HERE / "fig_geometri.svg")
rita_falt(HERE / "fig_falt.svg", bas)
rita_falt(HERE / "fig_falt_zoom.svg", bas, zoom=(420, -330, 30))
rita_profil(HERE / "fig_profil.svg", bas)

# ------------------------------------------------------------------ resultat till mallen
T_lim = 20.0                                                      # limningstemperatur i K-01
K01 = IN.get("k01", {})
fall = []
for r in RES:
    fall.append(dict(namn=r["namn"], h_ute=fmt(r["h_ute"], 1), h_inne=fmt(r["h_inne"], 1), To=fmt(r["To"][0], 1), Tu=fmt(r["Tu"][0], 1),
                     dT=fmt(r["dT"], 1), dTo=fmt(r["To"][0] - T_lim, 0), dTu=fmt(r["Tu"][0] - T_lim, 0), q=fmt(r["q"], 1),
                     Tute=fmt(r["T_ute"], 0), Tinne=fmt(r["T_inne"], 0)))
f_tb = ma["takbalk_b"] / ma["takbalk_cc"]; f_rg = ma["regel_b"] / ma["regel_cc"]
R = {
    "projekt": IN["projekt"],
    "g": {k: fmt(v, 0) for k, v in g.items()},
    "m": {k: (fmt(v, 3) if v < 1 else fmt(v, 0)) for k, v in ma.items()},
    "rd": dict(T_ute=fmt(rd["T_ute"], 0), T_inne=fmt(rd["T_inne"], 0), h_konv=fmt(rd["h_ute_konv"], 1), eps=fmt(rd["emissivitet"], 1),
               h_r=fmt(h_strl(rd["T_ute"], rd["emissivitet"]), 1), h_ute=fmt(bas["h_ute"], 1), h_inne=fmt(rd["h_inne"], 1),
               Rsi=fmt(1 / rd["h_inne"], 2)),
    "lam_iso": fmt(lam_iso, 3), "lam_inst": fmt(lam_inst, 2), "lam_luft45": fmt(lam_luft(g["installation"]), 2),
    "f_tb": fmt(100 * f_tb, 1), "f_rg": fmt(100 * f_rg, 1),
    "luft_d": [fmt(v, 0) for v in ls["d"]], "luft_R": [fmt(v, 2) for v in ls["R"]],
    "noder": f"{len(out['vertices']):,}".replace(",", " "), "element": f"{len(out['triangles']):,}".replace(",", " "),
    "noder2": f"{len(out2['vertices']):,}".replace(",", " "),
    "bas": fall[0], "fall": fall,
    "To_min": fmt(bas["To"][1], 1), "To_max": fmt(bas["To"][2], 1), "Tu_min": fmt(bas["Tu"][1], 1), "Tu_max": fmt(bas["Tu"][2], 1),
    "dT_nat2": fmt(bas2["dT"], 2), "dT_nat1": fmt(bas["dT"], 2),
    "skikt": [dict(namn=n_, R=fmt(r_, 3)) for n_, r_ in skikt], "R1": fmt(R1, 2), "U1": fmt(U1, 3),
    "T_yta_1d": fmt(T_yta_1d, 2), "T_yta_fe": fmt(bas["T"][i_end], 2), "q1d": fmt(q1d, 2), "q2d": fmt(bas["q"], 1),
    "psi": fmt(psi, 3), "L_tak": fmt(L_tak, 1),
    "dT_min": fmt(min(r["dT"] for r in RES), 0), "dT_max": fmt(max(r["dT"] for r in RES), 0),
    "ute_min": fmt(min(r["To"][0] for r in RES), 0),
}
(HERE / "resultat.json").write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8")

import typst  # noqa: E402
pdf = HERE / f"{IN['projekt']['dokument']}_varmeflode_nockbalk.pdf"
typst.compile(str(HERE / "mall.typ"), output=str(pdf), font_paths=["/usr/share/fonts"])
print(f"{pdf.name}: plåtarnas temperaturskillnad {bas['dT']:.1f} K (nät 2: {bas2['dT']:.2f} K), 1D-yta FE {bas['T'][i_end]:.2f} / {T_yta_1d:.2f} °C")
