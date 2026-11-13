"""
U-05: värmeförluster och energibehov – huvudskript.

    python berakning.py            # allt: 3D-modellen (några minuter), skarvarna, fallen, timsimuleringen,
                                   # kontrollerna, figurerna, resultat.json och PDF
    python berakning.py rapport    # utan 3D-modellen: dess kopplingar ur resultat.json

Läser indata.toml, källarväggarnas lägen ur ../K-05/bild/geometri.json, plintarna ur ../K-06/resultat.json och
klimatet ur ../U-03/klimat_era5.csv.gz.
"""
from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("svg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402

import byggnad as B  # noqa: E402
import data  # noqa: E402
import dynamik as DY  # noqa: E402
import klimat as KL  # noqa: E402
import komponenter as KO  # noqa: E402
import mark3d  # noqa: E402
import varmepump as VP_  # noqa: E402
import skarvar as S  # noqa: E402
import tester  # noqa: E402

HERE = Path(__file__).resolve().parent
FONTS = HERE.parent / ".fonts"
CM = 1 / 2.54
INK, MUTED, BLA, ROD, GRA = "#1e1e1e", "#6b6b6b", "#2c4a6e", "#b5463a", "#9a9a9a"


def fmt(v, d=0):
    """Tal med mellanslag som tusentalsavgränsare och komma som decimaltecken."""
    if v is None:
        return "–"
    if abs(v) < 0.5 * 10 ** (-d):
        v = 0.0
    s = f"{v:,.{d}f}".replace(",", " ").replace(".", ",")
    return s.replace("-", "−")


def tiopot(v):
    """Tal i tiopotensform med upphöjda siffror, t.ex. 7·10⁻⁴."""
    if v == 0:
        return "0"
    e = int(math.floor(math.log10(abs(v))))
    m = v / 10 ** e
    sup = str(e).translate(str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹"))
    return f"{fmt(m, 1)}·10{sup}"


# ------------------------------------------------------------------ skarvar och byggdelar
def balkskarv(P, slag, inst=None):
    """Nockens eller dalens ψ: snittet med och utan stålplåtarna, vägt efter plåtarnas andel av balkarnas längd."""
    Bk = P["balkar"]["nockar" if slag == "nock" else "dalar"]
    andel = sum(b["plat"] for b in Bk) / sum(b["y"][1] - b["y"][0] for b in Bk)
    r = S.nock_dal(P, slag, isolerat_inst=inst)
    utan = S.nock_dal(P, slag, plat=False, isolerat_inst=inst)["psi"]
    r.update(psi_med=r["psi"], psi_utan=utan, plat_andel=andel, psi=andel * r["psi"] + (1 - andel) * utan)
    return r


def skarvar(P, inst=None):
    """Skarvarnas snitt. inst: installationsskiktet isolerat (None: som i indata)."""
    sk = dict(bjalklag_kallare=S.bjalklagskant_psi(P, "kallare", isolerat_inst=inst),
              bjalklag_mark=S.bjalklagskant_psi(P, "mark", isolerat_inst=inst),
              takfot=S.takfot(P, isolerat_inst=inst), nock=balkskarv(P, "nock", inst), dal=balkskarv(P, "dal", inst),
              fonster=S.fonsteranslutning(P, isolerat_inst=inst),
              horn=S.horn(P, isolerat_inst=inst), innerhorn=S.horn(P, isolerat_inst=inst, inre=True))
    P["_psi_innerhorn"] = sk["innerhorn"]["psi"]
    return sk


def bygg_element(P, L3, omg, et, sk, inst=None):
    ar = B.areor(P)
    E = B.element(P, L3, omg, et, sk, isolerat_inst=inst)
    A1 = sum(e.A for e in E if e.a == "inne" and e.b == "ute")
    A_kv = ar["kallare_omkrets"] * 2.1
    P["_A_om"] = A1 + A_kv + ar["Atemp_kallare"] + ar["platta_pa_mark"]
    return E, ar


# ------------------------------------------------------------------ ett fall
def kor_fall(P, L3, omg, et, K, fall, sk_bas):
    Pf = data.med_fall(P, fall)
    ftx = float(Pf["_fall"].get("ftx", 0.0))
    # skarvarna räknas om när installationsskiktets isolering ändras
    inst = lambda Q: (bool(Q["installation"]["isolerad"]), bool(Q["tak"]["installation_isolerad"]))
    sk = skarvar(Pf) if inst(Pf) != inst(P) else sk_bas
    Pf["_psi_innerhorn"] = sk["innerhorn"]["psi"]
    E, ar = bygg_element(Pf, L3, omg, et, sk)
    HT = B.H_transmission(E)
    stat = {}
    Tm = float(K["T"].mean())
    for namn, Te, Tmk in (("noll", 0.0, Tm), ("dim", Pf["_dim"]["T_e"], Pf["_dim"]["T_mark"])):
        r = B.stationart(Pf, E, Te, Tmk, ftx=ftx)
        stat[namn] = dict(T={k: float(v) for k, v in r["T"].items()}, Q_h=float(r["Q_h"]),
                          forluster={k: float(v) for k, v in B.forluster(r).items()},
                          q={k: float(v) for k, v in r["q"].items()}, q_trapp=float(r["q_trapp"]),
                          upp=float(r["G"][B.OMG.index("varme"), B.OMG.index("inne")] * (r["T"]["varme"] - r["T"]["inne"])),
                          ned=float(r["G"][B.OMG.index("varme"), B.OMG.index("kallare")] * (r["T"]["varme"] - r["T"]["kallare"])))
    Lg = B.langder(Pf)
    for namn in stat:
        stat[namn]["kant"] = {k: float(v) for k, v in kantflode(sk, Lg, stat[namn]["T"]).items()}
    sim = DY.simulera(Pf, E, K, ar, ftx=ftx)
    arsf = DY.arsforluster(Pf, E, sim, K)
    Th = {"ute": sim["T_e"], "inne": sim["T_i"], "kallare": sim["T_b"], "varme": sim["T_h"]}
    kant_ar = {k: float(v.sum() / 1000 / len(set(K["ar"].tolist()))) for k, v in kantflode(sk, Lg, Th).items()}
    ar_lista = sorted({int(a) for a in K["ar"]})
    Qh = {a: float(sim["Q_h"][K["ar"] == a].sum() / 1000) for a in ar_lista}
    en = energi(Pf, ar, Qh, sim, K)
    return dict(namn=fall.get("namn", "Grundfall"), P=Pf, E=E, ar=ar, HT=HT, stat=stat, sim=sim, arsf=arsf, Qh=Qh,
                energi=en, sk=sk, kant_ar=kant_ar)


def golvvarmens_yta(P):
    """Golvvärmens yta [m²]: mellanbjälklaget 150 mm innanför väggarnas insida, utan trapphålet (som i 3D)."""
    from shapely.geometry import Polygon
    return Polygon(P["_kontur"]).buffer(-0.285, join_style=2).difference(
        Polygon(P["_trapphal"]).buffer(0.15, join_style=2)).area


def energi(P, ar, Qh, sim, K):
    """Energibehov, värmepumpen timme för timme, köpt el och primärenergital (BBR 29), medel över åren."""
    D, V, VP, BB = P["drift"], P["ventilation"], P["varmepump"], P["bbr"]
    At = ar["Atemp"]
    n_ar = len(Qh)
    Q = float(np.mean(list(Qh.values())))
    andel = float(np.mean(sim["hemma"]))                 # andelen av tiden som någon är hemma
    Q_vad = D["vadring"] * At * andel
    Q_tvv = D["tappvarmvatten"] * At * andel
    vp = VP_.berakna(P, sim, golvvarmens_yta(P), Q_tvv)
    E_golv = float(vp["el"].sum() / 1000 / n_ar)
    E_uppv = E_golv + Q_vad / vp["SCOP"]
    E_tvv = Q_tvv / VP["COP_tvv"]
    timmar_vp = float((sim["Q_h"] > 0).sum() / n_ar)
    q_hemma = V["FF1"] + V["FF2"] + V["FF3"] + (V["FF1_forcerad"] - V["FF1"]) * V["forcering_min"] / 1440
    E_f = V["flaktel_W"] * float(np.mean(sim["q_fr"])) / q_hemma * 8.76 + VP["pumpel_W"] * timmar_vp / 1000
    EP = ((E_uppv / BB["Fgeo"]) + E_tvv + E_f) * BB["VF_el"] / At
    P_dim = float(np.percentile(sim["Q_h"], 99.9))
    uttag = float(vp["uttag"].sum() / 1000 / n_ar)
    # köpt el per månad [kWh] och den rörliga kostnaden [kr/år] med månadens elpris
    el_h = vp["el"] * (E_uppv / E_golv if E_golv > 0 else 1.0) + VP["pumpel_W"] * (sim["Q_h"] > 0) + \
        V["flaktel_W"] * sim["q_fr"] / q_hemma + E_tvv * 1000 / (andel * 8760) * sim["hemma"]
    E_man = [float(el_h[K["man"] == mm].sum() / 1000 / n_ar) for mm in range(1, 13)]
    pris = elpris(P)
    kostnad_man = [e * p / 100 for e, p in zip(E_man, pris)]
    # (månaderna räknar skottdagarna, årssummorna 8 760 h)
    assert abs(sum(E_man) / (E_uppv + E_tvv + E_f) - 1) < 0.002, (sum(E_man), E_uppv + E_tvv + E_f)
    return dict(Q=Q, Q_m2=Q / At, Q_vad=Q_vad, Q_tvv=Q_tvv, E_uppv=E_uppv, E_tvv=E_tvv, E_f=E_f,
                E=E_uppv + E_tvv + E_f, E_m2=(E_uppv + E_tvv + E_f) / At, EP=EP, P_dim=P_dim, Q_min=min(Qh.values()),
                Q_max=max(Qh.values()), timmar_vp=timmar_vp, SCOP=vp["SCOP"], eta=vp["eta"],
                T_fram_max=vp["T_fram_max"], T_kb_min=vp["T_kb_min"], T_kb_medel=vp["T_kb_medel"],
                cop_min=vp["cop_min"], el_max=float(np.percentile(vp["el"], 99.9)), uttag=uttag,
                uttag_m=uttag / VP["borrhal_L"], A_varme=golvvarmens_yta(P),
                SPF=(Q + Q_vad + Q_tvv) / (E_uppv + E_tvv + E_f), andel_hemma=andel,
                q_medel=float(np.mean(sim["q_fr"])), q_tom=float(sim["q_fr"][~sim["hemma"]].mean())
                if (~sim["hemma"]).any() else float(np.mean(sim["q_fr"])),
                T_kb_drift=vp["T_kb_drift"], R_berg=vp["R_berg"], E_man=E_man, kostnad_man=kostnad_man,
                kostnad=float(sum(kostnad_man)), pris_medel=float(sum(kostnad_man) / sum(E_man) * 100))


def elpris(P):
    """Det rörliga elpriset per månad [öre/kWh med moms]: spotprisets medel över åren, påslag, energiskatt och
    elnätets överföringsavgift."""
    EP = P["elpris"]
    return [float(np.mean([a[i] for a in EP["spot"]])) + EP["paslag"] + EP["energiskatt"] + EP["elnat"]
            for i in range(12)]


def kantflode(sk, Lg, T):
    """Värmen genom kantisoleringen (30 mm cellplast utanför mellanbjälklagets kant) [W] vid temperaturerna T
    (dict eller timserier), per typ av kant."""
    ut = {}
    for typ, l in (("kallare", Lg["bjalklagskant_kallare"]), ("mark", Lg["bjalklagskant_pm"])):
        c = sk[f"bjalklag_{typ}"]["kant"]
        ut[typ] = sum(v * T[o] for o, v in c.items()) * l
    return ut


def kallarkurva(r, K, iso, T_e=np.arange(-15.0, 15.5, 1.0)):
    """Stationärt, utan sol och internlast, med rummet på fallets temperatur: golvvärmens plan, källaren och
    golvvärmens effekt (upp, ned, direkt ut) mot utetemperaturen. Markytan har markens tröga temperatur:
    årsmedel + η (T_ute − årsmedel) (ISO 13370:s dämpning)."""
    P, E = r["P"], r["E"]
    Tm = float(K["T"].mean())
    ut = {k: [] for k in ("T_e", "T_h", "T_b", "Q_h", "upp", "ned", "trapp")}
    for te in T_e:
        x = B.stationart(P, E, float(te), Tm + iso["eta"] * (float(te) - Tm))
        G, T = x["G"], x["T"]
        ih, ii, ib = (B.OMG.index(o) for o in ("varme", "inne", "kallare"))
        ut["T_e"].append(float(te))
        ut["T_h"].append(float(T["varme"]))
        ut["T_b"].append(float(T["kallare"]))
        ut["Q_h"].append(float(x["Q_h"]))
        ut["upp"].append(float(G[ih, ii] * (T["varme"] - T["inne"])))
        ut["ned"].append(float(G[ih, ib] * (T["varme"] - T["kallare"])))
        ut["trapp"].append(float(x["q_trapp"]))
    return ut


def manadsstat(sim, K, nyckel="T_b"):
    """Månadens medel, lägsta och högsta timvärde över alla år."""
    man = K["man"]
    v = sim[nyckel]
    return dict(medel=[float(v[man == mm].mean()) for mm in range(1, 13)],
                min=[float(v[man == mm].min()) for mm in range(1, 13)],
                max=[float(v[man == mm].max()) for mm in range(1, 13)])


# ------------------------------------------------------------------ figurer
def stil():
    for f in sorted(FONTS.glob("*.ttf")) if FONTS.is_dir() else []:
        font_manager.fontManager.addfont(str(f))
    plt.rcParams.update({"font.family": "Carlito", "font.size": 7.5, "svg.fonttype": "none", "axes.linewidth": 0.5,
                         "xtick.major.width": 0.5, "ytick.major.width": 0.5, "axes.edgecolor": INK,
                         "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK, "axes.spines.top": False,
                         "axes.spines.right": False})


def falt(ax, m, T, lim=None, vmin=None, vmax=None, titel=""):
    ex, ez = m.kant
    Tm = np.ma.masked_invalid(T)
    pc = ax.pcolormesh(ex * 1000, ez * 1000, Tm.T, cmap="RdBu_r", vmin=vmin, vmax=vmax, shading="flat",
                       rasterized=True)
    lev = np.arange(math.floor(np.nanmin(T)), math.ceil(np.nanmax(T)) + 1, 1.0)
    ax.contour(m.mitt[0] * 1000, m.mitt[1] * 1000, Tm.T, levels=lev, colors=INK, linewidths=0.25, alpha=0.6)
    # materialgränser
    ax.contour(m.mitt[0] * 1000, m.mitt[1] * 1000, np.where(m.mat >= 0, m.mat, -1).T.astype(float),
               levels=np.arange(-0.5, len(m.material) + 0.5, 1.0), colors=INK, linewidths=0.35)
    if lim:
        ax.set_xlim(lim[0])
        ax.set_ylim(lim[1])
    ax.set_aspect("equal")
    ax.set_title(titel, fontsize=7.5, loc="left")
    ax.tick_params(labelsize=6.5)
    return pc


def figurer(R, sk, L3info):
    stil()
    bas = R[0]
    st = bas["stat"]["noll"]
    T = st["T"]
    # skarvarna
    fig, axs = plt.subplots(2, 2, figsize=(17 * CM, 15.5 * CM))
    d = sk["bjalklag_kallare"]["detalj"]["modell"]
    pc = falt(axs[0, 0], d, d.los(T), ((-800, 300), (-1150, 800)), -2, 28,
              "a) Bjälklagets kant över källarväggen (3NV)")
    d = sk["bjalklag_mark"]["detalj"]["modell"]
    falt(axs[0, 1], d, d.los(T), ((-800, 500), (-900, 800)), -2, 28, "b) Bjälklagets kant, plattan på mark (1SO)")
    d = sk["takfot"]["modell"]
    falt(axs[1, 0], d, d.los(T), ((-250, 1000), (1700, 3150)), -2, 28, "c) Takfoten (3NV)")
    d = sk["nock"]["modell"]
    falt(axs[1, 1], d, d.los(T), ((0, 1100), (-300, 500)), -2, 28, "d) Nocken (halva, symmetri i balkens mitt)")
    for ax in axs.ravel():
        ax.set_xlabel("mm", fontsize=6.5)
    cb = fig.colorbar(pc, ax=axs, shrink=0.6, pad=0.02)
    cb.set_label("°C", fontsize=7)
    cb.ax.tick_params(labelsize=6.5)
    fig.savefig(HERE / "fig_skarvar.svg", bbox_inches="tight")
    plt.close(fig)

    # förlusterna per kategori (0 °C ute)
    fl = st["forluster"]
    tot = sum(fl.values())
    ordn = sorted(fl.items(), key=lambda kv: kv[1])
    fig, ax = plt.subplots(figsize=(17 * CM, 7.0 * CM))
    y = np.arange(len(ordn))
    ax.barh(y, [v for _, v in ordn], color=BLA, height=0.62)
    for i, (k, v) in enumerate(ordn):
        ax.text(v + tot * 0.006, i, f"{fmt(v)} W  ({fmt(100 * v / tot, 1)} %)", va="center", fontsize=6.8, color=INK)
    ax.set_yticks(y, [k for k, _ in ordn], fontsize=7)
    ax.set_xlabel(f"Värmeförlust vid 0 °C ute, {fmt(R[0]['P']['drift']['T_inne'])} °C på plan 1 [W]")
    ax.set_xlim(0, max(fl.values()) * 1.3)
    ax.grid(axis="x", lw=0.3, color="#dddddd")
    ax.set_axisbelow(True)
    fig.savefig(HERE / "fig_forluster.svg", bbox_inches="tight")
    plt.close(fig)

    # månader och år
    sim, K = bas["sim"], R[0]["_K"]
    ar = K["ar"]
    man = K["man"]
    nar = len(np.unique(ar))
    Qm = np.array([sim["Q_h"][man == mm].sum() / 1000 / nar for mm in range(1, 13)])
    Sm = np.array([(sim["sol1"] + sim["solk"])[man == mm].sum() / 1000 / nar for mm in range(1, 13)])
    fig, axs = plt.subplots(1, 2, figsize=(17 * CM, 5.8 * CM), gridspec_kw=dict(width_ratios=[1.25, 1]))
    xm = np.arange(1, 13)
    axs[0].bar(xm - 0.18, Qm, color=BLA, width=0.34, label="Golvvärme")
    axs[0].bar(xm + 0.18, Sm, color="#e0a526", width=0.34, label="Sol genom fönstren")
    axs[0].legend(fontsize=6.5, frameon=False, loc="upper center")
    axs[0].set_xticks(range(1, 13), ["jan", "feb", "mar", "apr", "maj", "jun", "jul", "aug", "sep", "okt", "nov", "dec"],
                      fontsize=6.5)
    axs[0].set_ylabel("kWh/månad")
    axs[0].set_title("a) Golvvärmen och solen per månad, medel 2014–2023", fontsize=7.5, loc="left")
    axs[0].grid(axis="y", lw=0.3, color="#dddddd")
    axs[0].set_axisbelow(True)
    aa = sorted(bas["Qh"])
    axs[1].bar(aa, [bas["Qh"][a] / 1000 for a in aa], color=BLA, width=0.65)
    axs[1].set_ylabel("Golvvärme [MWh/år]")
    axs[1].set_title("b) Golvvärmen per år", fontsize=7.5, loc="left")
    axs[1].set_xticks(aa, [str(a)[2:] for a in aa], fontsize=6.5)
    axs[1].grid(axis="y", lw=0.3, color="#dddddd")
    axs[1].set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(HERE / "fig_ar.svg", bbox_inches="tight")
    plt.close(fig)

    # temperaturerna under ett år (dygnsmedel, ett typiskt år)
    a_vis = R[0]["_ar_vis"]
    s = ar == a_vis
    n = s.sum() // 24 * 24

    def dm(x):
        return x[s][:n].reshape(-1, 24).mean(axis=1)
    fig, ax = plt.subplots(figsize=(17 * CM, 6.0 * CM))
    dag = np.arange(n // 24)
    serier = (("Ute", dm(K["T"]), GRA), ("Mellanbjälklaget (golvvärmens plan)", dm(sim["T_h"]), ROD),
              ("Källaren", dm(sim["T_b"]), "#c98b3a"), ("Plan 1", dm(sim["T_i"]), BLA))
    for namn, v, c in serier:
        ax.plot(dag, v, color=c, lw=1.0 if namn != "Ute" else 0.7, label=namn)
    ax.set_xlim(0, 365)
    ax.set_ylabel("Dygnsmedel [°C]")
    ax.set_xticks([0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334],
                  ["jan", "feb", "mar", "apr", "maj", "jun", "jul", "aug", "sep", "okt", "nov", "dec"], fontsize=6.5)
    ax.grid(lw=0.3, color="#dddddd")
    ax.set_axisbelow(True)
    ax.legend(fontsize=6.8, frameon=False, ncol=4, loc="lower center", bbox_to_anchor=(0.5, 1.0))
    fig.savefig(HERE / "fig_temperaturer.svg", bbox_inches="tight")
    plt.close(fig)

    # källaren med 21 °C på plan 1: stationärt mot utetemperaturen och under året
    kk = R[0]["_kallarkurvor"]
    k21, k20 = kk["21"], kk["20"]
    fig, axs = plt.subplots(1, 2, figsize=(17 * CM, 6.2 * CM))
    ax = axs[0]
    for kur, ls, tx in ((k21, "-", "21 °C på plan 1"), (k20, "--", "20 °C på plan 1")):
        ax.plot(kur["T_e"], kur["T_h"], color=ROD, lw=1.1, ls=ls)
        ax.plot(kur["T_e"], kur["T_b"], color="#c98b3a", lw=1.1, ls=ls)
    ax.axhline(21.0, color=BLA, lw=0.8)
    ax.text(14.5, 21.15, "plan 1, 21 °C", color=BLA, fontsize=6.5, ha="right", va="bottom")
    ax.text(-14.5, k21["T_h"][0] + 0.2, "golvvärmens plan", color=ROD, fontsize=6.5, va="bottom")
    ax.text(-14.5, k21["T_b"][0] + 0.2, "källaren", color="#c98b3a", fontsize=6.5, va="bottom")
    ax.set_xlabel("Utetemperatur [°C]")
    ax.set_ylabel("°C")
    ax.set_title("a) Källaren och golvvärmens plan (streckat: 20 °C)", fontsize=7.5, loc="left")
    ax.grid(lw=0.3, color="#dddddd")
    ax.set_axisbelow(True)
    ax = axs[1]
    for nyck, c, tx in (("Q_h", INK, "golvvärmen"), ("upp", BLA, "upp till plan 1"), ("ned", "#c98b3a", "ned till källaren")):
        ax.plot(k21["T_e"], np.array(k21[nyck]) / 1000, color=c, lw=1.1)
        ax.text(k21["T_e"][2], k21[nyck][2] / 1000 + 0.15, tx, color=c, fontsize=6.5, va="bottom")
    ax.set_xlabel("Utetemperatur [°C]")
    ax.set_ylabel("kW")
    ax.set_ylim(bottom=0)
    ax.set_title("b) Golvvärmens effekt med 21 °C på plan 1", fontsize=7.5, loc="left")
    ax.grid(lw=0.3, color="#dddddd")
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(HERE / "fig_kallare.svg", bbox_inches="tight")
    plt.close(fig)

    ms = R[0]["_kallare_man"]
    fig, ax = plt.subplots(figsize=(17 * CM, 5.6 * CM))
    xm = np.arange(1, 13)
    for nyck, c, tx in (("21", "#c98b3a", "källaren, 21 °C på plan 1"), ("20", "#d9b98c", "källaren, 20 °C på plan 1")):
        m_ = ms[nyck]
        ax.fill_between(xm, m_["min"], m_["max"], color=c, alpha=0.18, lw=0)
        ax.plot(xm, m_["medel"], color=c, lw=1.3, marker="o", ms=3, label=tx)
    ax.plot(xm, ms["ute"], color=GRA, lw=0.9, marker="o", ms=2.5, label="ute")
    ax.set_xticks(xm, ["jan", "feb", "mar", "apr", "maj", "jun", "jul", "aug", "sep", "okt", "nov", "dec"], fontsize=6.5)
    ax.set_ylabel("°C")
    ax.grid(lw=0.3, color="#dddddd")
    ax.set_axisbelow(True)
    ax.legend(fontsize=6.8, frameon=False, ncol=3, loc="lower center", bbox_to_anchor=(0.5, 1.0))
    fig.savefig(HERE / "fig_kallare_ar.svg", bbox_inches="tight")
    plt.close(fig)

    # 3D-modellen: snitt y = 6 000 med temperaturen (grundfallet, 0 °C ute)
    if L3info.get("modell") is not None:
        m = L3info["modell"]
        Tf = m.los({**T})
        j = int(np.argmin(abs(m.mitt[1] - 6.0)))
        fig, ax = plt.subplots(figsize=(17 * CM, 7.5 * CM))
        ex, ez = m.kant[0], m.kant[2]
        Tm = np.ma.masked_invalid(Tf[:, j, :])
        pc = ax.pcolormesh(ex, ez, Tm.T, cmap="RdBu_r", vmin=-2, vmax=28, shading="flat", rasterized=True)
        ax.contour(m.mitt[0], m.mitt[2], Tm.T, levels=np.arange(0, 28, 1.0), colors=INK, linewidths=0.25, alpha=0.6)
        mat = np.where(m.mat[:, j, :] >= 0, m.mat[:, j, :], -1).astype(float)
        ax.contour(m.mitt[0], m.mitt[2], mat.T, levels=np.arange(-0.5, len(m.material) + 0.5, 1.0), colors=INK,
                   linewidths=0.3)
        ax.set_xlim(-3, 17)
        ax.set_ylim(-6, 0.6)
        ax.set_aspect("equal")
        ax.set_xlabel("x [m] (K-05)")
        ax.set_ylabel("z [m]")
        cb = fig.colorbar(pc, ax=ax, shrink=0.8, pad=0.01)
        cb.set_label("°C")
        fig.savefig(HERE / "fig_3d.svg", bbox_inches="tight")
        plt.close(fig)


# ------------------------------------------------------------------ huvudprogram
def main():
    rapport_bara = len(sys.argv) > 1 and sys.argv[1] == "rapport"
    t0 = time.time()
    P = data.las()
    K = KL.las(P)
    K["_sol"] = KL.solens_lage(K["tid"], P["klimat"]["lat"], P["klimat"]["lon"])
    # dimensionerande fall: lägsta dygnsmedeltemperaturen 2014–2023, markytan som den tröga marktemperaturen då
    n = len(K["T"]) // 24 * 24
    dm = K["T"][:n].reshape(-1, 24).mean(axis=1)
    P["_dim"] = dict(T_e=float(round(dm.min(), 1)), dag=str(K["tid"][int(np.argmin(dm)) * 24])[:10])
    tidigare = json.loads((HERE / "resultat.json").read_text(encoding="utf-8")) if (HERE / "resultat.json").exists() \
        else None
    L3info = {}
    if rapport_bara:
        g = tidigare["mark3d"]
        L3, omg, et = np.array(g["L"]), g["omg"], g["etiketter"]
        L3info = dict(g, modell=None)
        natkontroll = tidigare["natkontroll"]
        bryggor = tidigare["bryggor"]
    else:
        t = time.time()
        m, info = mark3d.bygg(P)
        L3 = m.koppling()
        omg, et = list(m.omgivningar), list(m.etiketter)
        L3info = dict(L=L3.tolist(), omg=omg, etiketter=et, N=int(info["N"]), form=list(info["form"]),
                      tid=time.time() - t, modell=m)
        print(f"3D-modellen: {info['N']} celler, {time.time() - t:.0f} s", flush=True)
        # nätkontroll: grövre nät och utan kantbalkar och plintar (jämförelse)
        mg, ig = mark3d.bygg(P, grov=2.0)
        Lg = mg.koppling()
        mb, _ = mark3d.bygg(P, grov=2.0, bryggor=False)
        Lb = mb.koppling()
        natkontroll = dict(N_grov=int(ig["N"]), L_grov=Lg.tolist(), omg_grov=list(mg.omgivningar),
                           et_grov=list(mg.etiketter))
        bryggor = dict(L=Lb.tolist(), omg=list(mb.omgivningar), et=list(mb.etiketter))
        print(f"3D-kontrollerna klara, {time.time() - t0:.0f} s", flush=True)
    sk = skarvar(P)
    # temperaturen i marken: trög (ISO 13370) i det dimensionerande fallet
    ar0 = B.areor(P)
    iso = DY.iso13370_period(P, ar0)
    Tm = float(K["T"].mean())
    man_min = min(range(1, 13), key=lambda mm: K["T"][K["man"] == mm].mean())
    P["_dim"]["T_mark"] = Tm + iso["eta"] * (float(K["T"][K["man"] == ((man_min - 3) % 12) + 1].mean()) - Tm)
    # fallen
    R = []
    for fall in P["fall"]:
        r = kor_fall(P, L3, omg, et, K, fall, sk)
        R.append(r)
        print(f"{r['namn']}: {r['energi']['Q'] / 1000:.1f} MWh/år, Um {sum(r['HT'].values()) / r['P']['_A_om']:.3f}",
              flush=True)
    R[0]["_K"] = K
    # kontroll: timsimuleringen med konstant väder ska ge det stationära resultatet
    bp = R[0]
    simk = DY.simulera(bp["P"], bp["E"], K, bp["ar"], konstant=dict(T_e=0.0, T_mark=float(K["T"].mean()), vind=4.0))
    rk = B.stationart(bp["P"], bp["E"], 0.0, float(K["T"].mean()))
    R[0]["_kontroll_dyn"] = (float(simk["Q_h"][-1]), float(rk["Q_h"]))
    ar_lista = sorted(R[0]["Qh"])
    R[0]["_ar_vis"] = min(ar_lista, key=lambda a: abs(R[0]["Qh"][a] - R[0]["energi"]["Q"]))
    # nätkontroll av skarvarna (halva cellstorleken)
    h0 = P["nat"]["h_2d"]
    Pn = data.las()
    Pn["nat"]["h_2d"] = h0 / 2
    nat2d = {}
    for namn, f in (("bjalklag_kallare", lambda Q: S.bjalklagskant_psi(Q, "kallare")["psi"]["ute-varme"]),
                    ("bjalklag_mark", lambda Q: S.bjalklagskant_psi(Q, "mark")["psi"]["ute-varme"]),
                    ("takfot", lambda Q: S.takfot(Q)["psi"]), ("nock", lambda Q: S.nock_dal(Q, "nock")["psi"]),
                    ("dal", lambda Q: S.nock_dal(Q, "dal")["psi"]), ("fonster", lambda Q: S.fonsteranslutning(Q)["psi"]),
                    ("horn", lambda Q: S.horn(Q)["psi"])):
        nat2d[namn] = [f(P), f(Pn)]
    # källaren med 21 °C (BEN-fallet) och 20 °C på plan 1
    r21 = next(r for r in R if r["namn"] == "Inne 21 °C")
    R[0]["_kallarkurvor"] = {"21": kallarkurva(r21, K, iso), "20": kallarkurva(R[0], K, iso)}
    R[0]["_kallare_man"] = {"21": manadsstat(r21["sim"], K), "20": manadsstat(R[0]["sim"], K),
                            "ute": [float(K["T"][K["man"] == mm].mean()) for mm in range(1, 13)]}
    # verktygens kontroller
    kontroller = tester.alla()
    figurer(R, sk, L3info)
    L3info.pop("modell", None)
    res = sammanstall(P, R, sk, L3info, natkontroll, bryggor, nat2d, kontroller, iso, K)
    (HERE / "resultat.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    if (HERE / "mall.typ").exists():
        pdf()
    print(f"Klart på {time.time() - t0:.0f} s", flush=True)


def sammanstall(P, R, sk, L3info, natkontroll, bryggor, nat2d, kontroller, iso, K):
    bas = R[0]
    E = bas["E"]
    ar = bas["ar"]
    HT = bas["HT"]
    A_om = bas["P"]["_A_om"]
    Lg = B.langder(P)
    Y = P["ytmotstand"]
    # byggdelarna
    vagg = []
    for v in P["mangder"]["vagg"]:
        r = KO.vaggtyp_U(P, v["typ"], v["f_tra"])
        vagg.append(dict(kod=v["kod"], typ=P["vaggtyp"][v["typ"]]["namn"], A=v["A"], f_tra=v["f_tra"], U=r["U"],
                         U_iso=r["U_iso"], U_min=r["U_undre_gr"], U_max=r["U_ovre_gr"],
                         A_gavel=B.gavelspets_area(P, v["kropp"]) if v["gavel"] else 0.0))
    A_tf = P["takfonster"]["b"] * P["takfonster"]["h"] / 1e6
    tak = [dict(kod=t["kod"], A=B.takarea(P, t) - t.get("takfonster", 0) * A_tf, f_tra=t["f_tra"],
                **{k: v for k, v in KO.tak_U(P, t["f_tra"]).items() if k != "modell"}) for t in P["mangder"]["takfall"]]
    gavel = {typ: KO.gavelspets_U(P, typ)["U"] for typ in ("v95", "v145", "v145u")}
    Pg = data.med_fall(P, {"gavelspets.isolerad": not P["gavelspets"]["isolerad"]})
    gavel_isol = KO.gavelspets_U(Pg, "v95")["U"]          # det andra utförandet (oisolerat i grundfallet)
    U_kv = KO.skiktat_U(P, P["kallarvagg"]["skikt"], Y["Rsi_vagrat"], Y["Rse"])
    fonster = []
    for kod, typ, b, h, van, vg in P["oppningar"]["lista"]:
        f = KO.fonster(P, typ, b, h)
        fonster.append(dict(kod=kod, typ=typ, vagg=vg, vaning=van, b=f["b"], h=f["h"], A=f["A"], U=f["U"],
                            andel_glas=f["Ag"] / f["A"] if f["A"] else 0.0))
    skarv = dict(
        bjalklag_kallare=dict(psi=sk["bjalklag_kallare"]["psi"], l=Lg["bjalklagskant_kallare"]),
        bjalklag_mark=dict(psi=sk["bjalklag_mark"]["psi"], l=Lg["bjalklagskant_pm"]),
        takfot=dict(psi=sk["takfot"]["psi"], l=Lg["takfot"]),
        nock=dict(psi=sk["nock"]["psi"], l=Lg["nock"], plat_andel=sk["nock"]["plat_andel"]),
        dal=dict(psi=sk["dal"]["psi"], l=Lg["dal"], plat_andel=sk["dal"]["plat_andel"]),
        fonster=dict(psi=sk["fonster"]["psi"],
                                                                  l=sum(e.l for e in E if e.namn.startswith("Fönstrens"))),
        horn=dict(psi=sk["horn"]["psi"], l=Lg["ytterhorn"], n=Lg["n_ytterhorn"]),
        innerhorn=dict(psi=sk["innerhorn"]["psi"], l=Lg["innerhorn"], n=Lg["n_innerhorn"]),
        gavelkant=dict(psi=P["_psi_gavelkant"], l=Lg["gavelkant"]),
        kallarfonster=dict(psi=P["_skarv_kallarfonster"]),
        takfonster=dict(psi=P["takfonster"]["psi"], l=4 * P["takfonster"]["b"] / 1000 * P["takfonster"]["antal"]))
    # 3D: kopplingarna mellan omgivningarna och nätkontrollen
    def koppl(L, omg):
        M = np.array(L).sum(axis=1)
        return {f"{omg[k]}-{omg[j]}": float(M[k, j]) for k in range(len(omg)) for j in range(len(omg)) if k < j}
    k3 = koppl(L3info["L"], L3info["omg"])
    kg = koppl(natkontroll["L_grov"], natkontroll["omg_grov"])
    kb = koppl(bryggor["L"], bryggor["omg"])
    Eb = B.element(P, np.array(bryggor["L"]), bryggor["omg"], bryggor["et"], sk)
    HTb = B.H_transmission(Eb)
    Eg = B.element(P, np.array(natkontroll["L_grov"]), natkontroll["omg_grov"], natkontroll["et_grov"], sk)
    HTg = B.H_transmission(Eg)
    # fallen
    fall = []
    for r in R:
        en = r["energi"]
        fall.append(dict(namn=r["namn"], H_T=sum(r["HT"].values()), Um=sum(r["HT"].values()) / r["P"]["_A_om"],
                         Q_noll=r["stat"]["noll"]["Q_h"], Q_dim=r["stat"]["dim"]["Q_h"],
                         T_b=r["stat"]["noll"]["T"]["kallare"], Q=en["Q"], Q_m2=en["Q_m2"], EP=en["EP"],
                         P_dim=en["P_dim"], E=en["E"], SCOP=en["SCOP"], kostnad=en["kostnad"],
                         kostnad_man=en["kostnad_man"], E_man=en["E_man"], T_inne=r["P"]["drift"]["T_inne"],
                         T_b_ar=float(r["sim"]["T_b"].mean())))
    # årsförlusterna per kategori, medel
    arsf = {k: float(np.mean(list(v.values()))) for k, v in bas["arsf"].items()}
    sim = bas["sim"]
    Ti = sim["T_i"]
    klim = dict(T_medel=float(K["T"].mean()), T_ar={int(a): float(K["T"][K["ar"] == a].mean()) for a in np.unique(K["ar"])},
                graddagar=KL.graddagar(K), dim=P["_dim"], ar=P["klimat"]["ar"],
                T_man=[float(K["T"][K["man"] == mm].mean()) for mm in range(1, 13)])
    sol = dict(plan1=float(sim["sol1"].sum() / 1000 / len(bas["Qh"])), kallare=float(sim["solk"].sum() / 1000 / len(bas["Qh"])),
               intern=float((sim["int1"].sum() + sim["intk"].sum()) / 1000 / len(bas["Qh"])))
    # gradtimmekontroll: förlustfaktorn gånger gradtimmarna minus tillgodogjorda tillskott (ISO 13790, förenklat)
    H_tot = sum(HT.values()) + float(np.mean(sim["H_vent"] + sim["H_inf"]))   # luften: medel över året
    gt = float(np.clip(P["drift"]["T_inne"] - K["T"], 0, None).sum() / 1000 / len(bas["Qh"]))
    vinst = sol["plan1"] + sol["kallare"] + sol["intern"]
    res = dict(
        projekt=P["projekt"],
        areor=ar, A_om=A_om, langder=Lg,
        vagg=vagg, tak=tak, gavel=gavel, gavel_isol=gavel_isol, U_kallarvagg=U_kv,
        U_kallargolv_1d=KO.skiktat_U(P, [["betong", 100], ["eps_mark", 300]], Y["Rsi_nedat"], 0.0),
        Uf=KO.velfac_Uf(P), fonster=fonster, skarv=skarv,
        HT=HT, H_T=sum(HT.values()), Um=sum(HT.values()) / A_om, HT_bryggor=HTb, HT_grov=HTg,
        mark3d=dict(L=L3info["L"], omg=L3info["omg"], etiketter=L3info["etiketter"], N=L3info["N"],
                    form=L3info["form"], koppling=k3, koppling_grov=kg, koppling_bryggor=kb,
                    N_grov=natkontroll["N_grov"]),
        natkontroll=natkontroll, bryggor=bryggor, nat2d=nat2d,
        stat=bas["stat"], fall=fall, arsforluster=arsf, Qh=bas["Qh"], energi=bas["energi"], kant_ar=bas["kant_ar"],
        kant_koeff={t: sk[f"bjalklag_{t}"]["kant"] for t in ("kallare", "mark")},
        kallarkurvor=R[0]["_kallarkurvor"], kallare_man=R[0]["_kallare_man"],
        klimat=klim, sol=sol, iso13370=iso, H_tot=H_tot, gradtimmar=gt, gradtimmar_Q=H_tot * gt - vinst,
        drift=dict(Ti_under_205=float((Ti < 20.5).sum() / len(bas["Qh"])), Ti_min=float(Ti.min()),
                   Ti_max=float(Ti.max()), Tb_medel=float(sim["T_b"].mean()), Tb_min=float(sim["T_b"].min()),
                   Tb_max=float(sim["T_b"].max()), Th_max=float(sim["T_h"].max()),
                   vadring=float(sim["vadring"].sum() / 1000 / len(bas["Qh"]))),
        kontroller=kontroller,
        indata={k: P[k] for k in ("material", "ytmotstand", "velfac", "ytterdorr", "takfonster", "ventilation",
                                   "infiltration", "drift", "varmepump", "bbr", "dynamik", "trapphal", "gavelspets",
                                   "uppskattade_skarvar", "bjalklag", "klimat", "nat")},
    )
    res["t"], res["tab"] = texter(res, R, P)
    return res


def pdf():
    import typst
    out = HERE / "U-05_varmeforluster.pdf"
    typst.compile(str(HERE / "mall.typ"), output=str(out), font_paths=["/usr/share/fonts", str(FONTS)])



# ------------------------------------------------------------------ texter och tabeller till rapporten
def kant_andel_varme(res, st0):
    """Andelen av värmen genom kantisoleringen som kommer från golvvärmen (koefficienten gånger temperaturen över
    utetemperaturen), vid 0 °C ute."""
    T = st0["T"]
    tot = varme = 0.0
    for typ, c in res["kant_koeff"].items():
        l = res["skarv"]["bjalklag_" + typ]["l"]
        for o, v in c.items():
            if o == "ute":
                continue
            tot += v * (T[o] - T["ute"]) * l
            if o == "varme":
                varme += v * (T[o] - T["ute"]) * l
    return varme / tot if tot else 0.0


def texter(res, R, P):
    f = fmt
    bas = R[0]
    en_ben = next(r for r in R if r["namn"].startswith("Helårsboende, inne 21"))["energi"]
    sol = res["sol"]
    k21 = res["kallarkurvor"]["21"]
    st0, std = res["stat"]["noll"], res["stat"]["dim"]
    fl0, fld = st0["forluster"], std["forluster"]
    tot0, totd = sum(fl0.values()), sum(fld.values())
    en = res["energi"]
    At = res["areor"]["Atemp"]
    ar = res["areor"]
    BB = P["bbr"]
    vagg = res["vagg"]
    Uv = [v["U"] for v in vagg if v["kod"] != "2SV"]
    ft = [v["f_tra"] for v in vagg if v["kod"] != "2SV"]
    A_gavel = sum(v["A_gavel"] for v in vagg)
    gU = res["gavel"]
    fonst = [x for x in res["fonster"] if x["typ"] not in ("ytterdörr", "pardörr")]
    sk = res["skarv"]
    k3, kg, kb = res["mark3d"]["koppling"], res["mark3d"]["koppling_grov"], res["mark3d"]["koppling_bryggor"]
    kontr = {k["namn"]: k for k in res["kontroller"]}
    iso_p = next(k for k in res["kontroller"] if k["namn"].startswith("Platta"))
    iso_k = next(k for k in res["kontroller"] if k["namn"].startswith("Uppvärmd"))
    q = st0["q"]
    T_ar = res["klimat"]["T_medel"]
    Th, Tb = st0["T"]["varme"], st0["T"]["kallare"]
    ned_andel = 100 * st0["ned"] / st0["Q_h"]
    T_in = P["drift"]["T_inne"]
    kant_W = st0["kant"]["kallare"] / sk["bjalklag_kallare"]["l"]
    gavel_fall = next((x for x in res["fall"] if x["namn"].startswith("Gavelspetsarna")), None)
    uppsk = sk["gavelkant"]["psi"] * sk["gavelkant"]["l"] + \
        sum(e["psi"] * 2 * (e["b"] + e["h"]) for e in [dict(psi=sk["kallarfonster"]["psi"], **x)
                                                       for x in res["fonster"] if x["vaning"] == 0])
    # ovan mark: källarväggarnas andel ovan mark (medel), ur markens nivåer vid fasaderna
    nivaer = [z for v in P["mark"]["niva"].values() for _, z in v]
    M_ = P["material"]
    lam_inst = KO.skikt_lam(P, "installation", 45.0)
    f_v = sum(v["f_tra"] * (v["A"] - v["A_gavel"]) for v in vagg) / sum(v["A"] - v["A_gavel"] for v in vagg)
    f_t = sum(x["f_tra"] * x["A"] for x in res["tak"]) / sum(x["A"] for x in res["tak"])
    R_in = 0.045 / lam_inst
    innanfor_v = R_in / (R_in + 0.095 / (f_v * M_["tra"]["lam"] + (1 - f_v) * M_["mineralull"]["lam"]))
    # taket, om installationsskiktet där isoleras
    R_in_t = 0.045 / KO.skikt_lam(P, "installation", 45.0, "uppat", True)
    innanfor_t = R_in_t / (R_in_t + 0.170 / (f_t * M_["tra"]["lam"] + (1 - f_t) * M_["trafiber"]["lam"]))
    inst_isol = bool(P["installation"]["isolerad"])
    # ångbromsens temperatur i väggen (1D mellan reglarna, homogeniserat) vid dimensionerande ute och inne
    Y_ = P["ytmotstand"]
    sk95 = P["vaggtyp"]["v95"]["skikt"]
    i_ab = [n for n, _ in sk95].index("installation") + 1
    def R_sk(n, t_):
        lam = (f_v * M_["tra"]["lam"] + (1 - f_v) * M_["mineralull"]["lam"]) if n == "stomme" else KO.skikt_lam(P, n, t_)
        return t_ / 1000 / lam
    R_ab_in = Y_["Rsi_vagrat"] + sum(R_sk(n, t_) for n, t_ in sk95[:i_ab])
    R_ab_ut = Y_["Rse_ventilerad_vagg"] + sum(R_sk(n, t_) for n, t_ in sk95[i_ab:])
    T_ab = T_in - (T_in - P["_dim"]["T_e"]) * R_ab_in / (R_ab_in + R_ab_ut)
    psat = lambda T: 610.94 * np.exp(17.625 * T / (T + 243.04))
    RF_ab = psat(T_ab) / psat(T_in)
    inst_fall = next((x for x in res["fall"] if x["namn"].startswith("Installationsskiktet i väggarna")), None)
    tak_fall = next((x for x in res["fall"] if x["namn"].startswith("Installationsskiktet i taket")), None)
    tak_isol = bool(P["tak"]["installation_isolerad"])
    t = dict(
        inst_fukt=(f" Med isoleringen i installationsskiktet ligger {f(100 * innanfor_v)} % av väggens värmemotstånd "
                   f"innanför ångbromsen, "
                   + ("mer än tumregelns tredjedel" if innanfor_v > 1 / 3 else "inom tumregelns tredjedel")
                   + f": vid {f(P['_dim']['T_e'], 1)} °C ute och {f(T_in)} °C inne blir ångbromsen {f(T_ab, 1)} °C "
                   f"mellan reglarna, daggpunkten för inneluft med {f(100 * RF_ab)} % relativ fuktighet."
                   if inst_isol else ""),
        kostnad=f(en["kostnad"]), pris_medel=f(en["pris_medel"]), driftar=f(P["varmepump"]["driftar"]),
        pris_ar=", ".join(str(a) for a in P["elpris"]["ar"][:-1]) + " och " + str(P["elpris"]["ar"][-1]),
        pris_paslag=f(P["elpris"]["paslag"]), pris_skatt=f(P["elpris"]["energiskatt"]), pris_nat=f(P["elpris"]["elnat"]),
        T_kb_drift=f(en["T_kb_drift"], 1), lam_karm=f(R[0]["sk"]["fonster"]["lam_karm"], 2),
        A_tak=f(sum(x["A"] for x in res["tak"]), 1),
        inst_extra=f((inst_fall["Q_noll"] - st0["Q_h"]) if inst_fall else 0.0),
        inst_ar=f(((inst_fall["Q"] - en["Q"]) / 1000) if inst_fall else 0.0, 1),
        tak_extra=f(abs(tak_fall["Q_noll"] - st0["Q_h"]) if tak_fall else 0.0),
        tak_ar=f((abs(tak_fall["Q"] - en["Q"]) / 1000) if tak_fall else 0.0, 1),
        tak_kr=f(abs(tak_fall["kostnad"] - en["kostnad"]) if tak_fall else 0.0),
        tak_innanfor=f(100 * innanfor_t),
        tak_text=("installationsskiktet under takbalkarna isolerat med 45 mm mineralull" if tak_isol
                  else "installationsskiktet under takbalkarna oisolerat"),
        U_tak=f(sum(x["U"] * x["A"] for x in res["tak"]) / sum(x["A"] for x in res["tak"]), 2),
        inst_text=("ett installationsskikt med 45 mm mineralull mellan läkten" if inst_isol
                   else "ett oisolerat installationsskikt"),
        inst_isolerad=inst_isol, q_tom=f(en["q_tom"]), q_medel=f(en["q_medel"]), andel_hemma=f(100 * en["andel_hemma"]),
        vent_ar_andel=f(100 * res["arsforluster"].get("Ventilation", 0) / sum(res["arsforluster"].values())),
        tomt_flode=f(P["ventilation"]["tomt_flode"], 2), grundlast=f(P["drift"]["grundlast_W"]),
        narvaro_text=("helgerna, fredag 18 till söndag 18" if P["drift"]["narvaro"] == "helg" else "hela tiden"),
        vent_andel=f(100 * fl0.get("Ventilation", 0) / tot0), q_franluft=f(q["franluft"]),
        U_vagg_spann=f"{f(min(Uv), 2)}–{f(max(Uv), 2)}", f_tra_spann=f"{f(100 * min(ft))}–{f(100 * max(ft))}",
        U_vagg_medel=f(sum(v["U"] * (v["A"] - v["A_gavel"]) for v in vagg) / sum(v["A"] - v["A_gavel"] for v in vagg), 2),
        f_tra_medel=f(100 * sum(v["f_tra"] * (v["A"] - v["A_gavel"]) for v in vagg) /
                      sum(v["A"] - v["A_gavel"] for v in vagg)),
        q_m2=f(q["franluft"] / At, 2), q_bbr=f(0.35 * At),
        A_gavel=f(A_gavel, 1), U_gavel=f"{f(min(gU.values()), 2)}–{f(max(gU.values()), 2)}",
        gavel_andel=f(100 * fl0.get("Gavelspetsar", 0) / tot0), Tb_noll=f(Tb, 1), Th_noll=f(Th, 1),
        ned_andel=f(ned_andel), Um=f(res["Um"], 2), Um_krav=f(BB["Um_krav"], 2), EP=f(en["EP"]), EP_krav=f(BB["EP_krav"]),
        h_2d=f(P["nat"]["h_2d"], 1), N3d=f(res["mark3d"]["N"] / 1e6, 1) + " miljoner", h_3d=f(P["nat"]["h_3d"]),
        mark_ut=f(P["mark"]["utbredning"] * 16.0), mark_djup=f(P["mark"]["djup"] / 1000 + 2.8),
        Ug=f(P["velfac"]["Ug"], 2), psi_g=f(P["velfac"]["psi_g"], 3), Uf=f(res["Uf"], 2),
        Uw_spann=f"{f(min(x['U'] for x in fonst), 2)}–{f(max(x['U'] for x in fonst), 2)}",
        kant_W=f(kant_W, 1), psi_fonster=f(sk["fonster"]["psi"], 3), T_ar=f(T_ar, 1),
        ned_W=f(k3.get("kallare-varme", 0)), upp_W=f(k3.get("inne-varme", 0)),
        bryggor_W=f(res["HT"].get("Källarens golv", 0) + res["HT"].get("Källarens väggar", 0)
                    - res["HT_bryggor"].get("Källarens golv", 0) - res["HT_bryggor"].get("Källarens väggar", 0), 1),
        iso_platta=f(100 * iso_p["avvikelse"], 1), iso_kallare=f(100 * iso_k["avvikelse"], 1),
        ovan_mark=f"markytan {f(-max(nivaer) / 1000, 1)}–{f(-min(nivaer) / 1000, 1)} m under bjälklagets överkant",
        FF1=f(P["ventilation"]["FF1"]), FF2=f(P["ventilation"]["FF2"]), FF3=f(P["ventilation"]["FF3"]),
        q50=f(P["infiltration"]["q50"], 1), q_extra=f(q["extra"], 1), q_trapp=f(st0["q_trapp"]),
        Q_noll=f(st0["Q_h"]), dim_Te=f(P["_dim"]["T_e"], 1), dim_dag=P["_dim"]["dag"], dim_Tm=f(P["_dim"]["T_mark"], 1),
        eta=f(res["iso13370"]["eta"], 2), lag=f(res["iso13370"]["lag"], 1),
        horisont=f(P["dynamik"]["styr_horisont_h"]), P_max=f(P["dynamik"]["P_max"]), T_vad=f(P["drift"]["T_vadring"]),
        ar_vis=str(R[0]["_ar_vis"]), H_tot=f(res["H_tot"]), gradtimmar=f(res["gradtimmar"]),
        gt_brutto=f(res["H_tot"] * res["gradtimmar"] / 1000, 1), gt_netto=f(res["gradtimmar_Q"] / 1000, 1),
        Q_ar=f(en["Q"] / 1000, 1),
        balans=tiopot(max(k.get("balans", 0.0) for k in res["kontroller"])),
        gavel_spar=f(fl0.get("Gavelspetsar", 0) * (1 - res["gavel_isol"] / gU["v95"])),
        uppsk_W=f(uppsk, 1), T_inne=f(T_in), g=f(P["velfac"]["g"], 2),
        sol_nytta=f(next(x["Q"] for x in res["fall"] if x["namn"].startswith("Utan sol")) - en["Q"]),
        sol_tot=f(sol["plan1"] + sol["kallare"]),
        sol_andel=f(100 * (next(x["Q"] for x in res["fall"] if x["namn"].startswith("Utan sol")) - en["Q"])
                    / (sol["plan1"] + sol["kallare"])),
        Tb21_noll=f(k21["T_b"][k21["T_e"].index(0.0)], 1), Th21_noll=f(k21["T_h"][k21["T_e"].index(0.0)], 1),
        Tb21_min15=f(k21["T_b"][0], 1), Tb21_plus15=f(k21["T_b"][-1], 1),
        Tb21_ar=f(float(np.mean(res["kallare_man"]["21"]["medel"])), 1),
        Tb21_minh=f(min(res["kallare_man"]["21"]["min"]), 1), Tb21_maxh=f(max(res["kallare_man"]["21"]["max"]), 1), l_kant=f(res["langder"]["bjalklagskant"], 1), E=f(en["E"]),
        T_berg=f(P["varmepump"]["T_berg"], 1),
        gavel_extra=f(next((x["Q_noll"] for x in res["fall"] if x["namn"].startswith("Gavelspetsarna")), st0["Q_h"])
                      - st0["Q_h"]),
        kant_noll=f(sum(st0["kant"].values())), kant_noll_andel=f(100 * sum(st0["kant"].values()) / tot0, 1),
        kant_ar=f(sum(res["kant_ar"].values())),
        kant_ar_andel=f(100 * sum(res["kant_ar"].values()) / sum(res["arsforluster"].values()), 1),
        kant_varme_andel=f(100 * kant_andel_varme(res, st0)),
        SCOP=f(en["SCOP"], 1), cop_min=f(en["cop_min"], 1), T_fram_max=f(en["T_fram_max"], 1),
        T_kb_min=f(en["T_kb_min"], 1), T_kb_medel=f(en["T_kb_medel"], 1), eta_vp=f(en["eta"], 2),
        uttag=f(en["uttag"]), uttag_m=f(en["uttag_m"]), SPF=f(en["SPF"], 1), A_varme=f(en["A_varme"]),
        EP_ben=f(en_ben["EP"]), E_ben=f(en_ben["E"]),
        skarv_H=f(sum(v for k, v in res["HT"].items() if k in ("Köldbryggor plan 1", "Mellanbjälklagets kant"))),
        skarv_andel=f(100 * sum(v for k, v in res["HT"].items() if k in ("Köldbryggor plan 1", "Mellanbjälklagets kant"))
                      / res["H_T"]),
        fonster_H=f(sk["fonster"]["psi"] * sk["fonster"]["l"], 1),
        kant_H=f(sum(v for k, v in sk["bjalklag_kallare"]["psi"].items() if "ute" in k or "mark" in k) *
                 sk["bjalklag_kallare"]["l"] + sum(v for k, v in sk["bjalklag_mark"]["psi"].items()
                                                   if "ute" in k or "mark" in k) * sk["bjalklag_mark"]["l"], 1), H_T_kort=f(res["H_T"]), Q_spann=f"{f(en['Q_min'] / 1000, 1)}–{f(en['Q_max'] / 1000, 1)}",
    )
    # sammanfattningen
    sam = [
        ["Uppvärmd area Atemp (plan 1 + källaren)", f"{f(At)} m²", f"{f(ar['Atemp_plan1'])} + {f(ar['Atemp_kallare'])} m²"],
        ["Transmissionsförluster H#sub[T]", f"{f(res['H_T'])} W/K", "alla rum lika varma"],
        ["Um (klimatskärmen, invändiga mått)", f"{f(res['Um'], 2)} W/m²K", f"BBR: högst {f(BB['Um_krav'], 2)}"],
        ["Golvvärmens effekt vid 0 °C ute", f"{f(st0['Q_h'] / 1000, 1)} kW", f"stationärt, {f(T_in)} °C inne, utan tillskott"],
        [f"Golvvärmens effekt vid {f(P['_dim']['T_e'], 1)} °C ute", f"{f(std['Q_h'] / 1000, 1)} kW",
         "kallaste dygnet 2014–2023"],
        ["Källarens temperatur vid 0 °C ute", f"{f(Tb, 1)} °C", "ingen egen värme"],
        ["Golvvärme under ett år", f"{f(en['Q'] / 1000, 1)} MWh", f"{f(en['Q_m2'])} kWh/m² Atemp, år {t['Q_spann']} MWh"],
        ["Värmepumpens årsvärmefaktor (golvvärmen)", f(en["SCOP"], 1), f"framledning högst {f(en['T_fram_max'], 1)} °C"],
        ["Köpt el (värme, varmvatten, fläktar, pumpar)", f"{f(en['E'])} kWh/år",
         f"{f(en['E_m2'], 1)} kWh/m² Atemp; rörlig kostnad {f(en['kostnad'])} kr/år"],
        ["Genom mellanbjälklagets kanter (30 mm cellplast)", f"{f(sum(st0['kant'].values()))} W",
         f"{f(100 * sum(st0['kant'].values()) / tot0, 1)} % av förlusterna vid 0 °C"],
        ["Primärenergital EP#sub[pet] (BEN, 21 °C)", f"{f(en_ben['EP'])} kWh/m²", f"BBR: högst {f(BB['EP_krav'])}"],
    ]
    sam = [[r[0], r[1], r[2]] for r in sam]
    # väggarna
    vaggar = [[v["kod"], v["typ"], f(v["A"], 1), f(100 * v["f_tra"]), f(v["U"], 3), f(v["U_iso"], 3),
               f"{f(v['U_min'], 3)}–{f(v['U_max'], 3)}"] for v in vagg]
    tk = res["tak"]
    byggdelar = [
        ["Tak (6 takfall)", f"{f(min(x['U'] for x in tk), 3)}–{f(max(x['U'] for x in tk), 3)}", f(sum(x["A"] for x in tk), 1),
         "takbalkar 45×170 c/c 600 (virke " + f"{f(100 * min(x['f_tra'] for x in tk))}–{f(100 * max(x['f_tra'] for x in tk))} %), träfiber 170, " + ("installationsskikt 45 med mineralull" if P["tak"]["installation_isolerad"] else "oisolerat installationsskikt") + ", gips 2 × 12,5; BBR 9:92: 0,13"],
        ["Gavelspetsar (isolerade)" if P["gavelspets"]["isolerad"] else "Gavelspetsar (oisolerade)",
         f"{f(gU['v95'], 2)} / {f(gU['v145u'], 2)}", f(A_gavel, 1),
         ("gavelstolens fack med mineralull; med installationsskikt / utan (1SV); oisolerade: "
          if P["gavelspets"]["isolerad"] else "gavelstolens fack med luft; isolerade: ") + f(res["gavel_isol"], 2)],
        ["Ytterväggar", t["U_vagg_spann"], f(sum(v["A"] - v["A_gavel"] for v in vagg), 1), "BBR 9:92: 0,18"],
        ["Källarväggar (1D)", f(res["U_kallarvagg"], 3), f(ar["kallare_omkrets"] * 2.1, 1),
         "Kub 350-150, gips; mot mark lägre (3D)"],
        ["Källargolv i fält (1D)", f(res["U_kallargolv_1d"], 3), f(ar["Atemp_kallare"], 1),
         "betong 100 på cellplast 300; med marken och kantbalkarna i 3D"],
        ["Fönster och fönsterdörrar, plan 1", t["Uw_spann"], f(sum(x["A"] for x in fonst if x["vaning"] == 1), 1),
         "VELFAC 200 ENERGY, SS-EN ISO 10077-1; BBR 9:92: 1,2"],
        ["Källarens fönster", f"{f(min(x['U'] for x in fonst if x['vaning'] == 0), 2)}–{f(max(x['U'] for x in fonst if x['vaning'] == 0), 2)}",
         f(sum(x["A"] for x in fonst if x["vaning"] == 0), 2), "VELFAC 200 ENERGY"],
        ["Ytterdörrar (1SO-D1, källarens D1)", f(P["ytterdorr"]["U"], 1),
         f(sum(x["A"] for x in res["fonster"] if x["typ"] in ("ytterdörr", "pardörr")), 1), "antaget, inte valda"],
        ["Takfönster TF1–TF3", f(P["takfonster"]["Uw"], 2), f(3 * 1.44, 2), "3-glas, i takets lutning, antaget"],
    ]
    # skarvarna
    def rad(namn, d, snitt, key=None):
        psi = d["psi"][key] if key else d["psi"]
        l = d.get("l", 0.0)
        return [namn, f(psi, 3), f(l, 1) if l else "–", f(psi * l, 1) if l else "–", snitt]
    skarvar_t = [
        rad("Mellanbjälklagets kant över källarvägg, golvvärmen–ute (ψ#sub[he])", sk["bjalklag_kallare"], "@fig-skarvar a", "ute-varme"),
        rad("… rummet–ute (ψ#sub[ie])", sk["bjalklag_kallare"], "", "inne-ute"),
        rad("… källaren–ute", sk["bjalklag_kallare"], "", "kallare-ute"),
        rad("Mellanbjälklagets kant, plattan på mark, golvvärmen–ute", sk["bjalklag_mark"], "@fig-skarvar b", "ute-varme"),
        rad("… rummet–ute", sk["bjalklag_mark"], "", "inne-ute"),
        rad("Takfot", sk["takfot"], "@fig-skarvar c"),
        rad(f"Nock (stålplåtar på {f(100 * sk['nock']['plat_andel'])} % av längden)", sk["nock"], "@fig-skarvar d"),
        rad(f"Dal (stålplåtar på {f(100 * sk['dal']['plat_andel'])} % av längden)", sk["dal"],
            "som nocken, med balken under takfallens möte"),
        rad("Fönster och fönsterdörrar, plan 1 (sidokarm)", sk["fonster"], "vågrätt snitt"),
        rad(f"Ytterhörn ({sk['horn']['n']} st)", sk["horn"], "vågrätt snitt"),
        rad(f"Innerhörn ({sk['innerhorn']['n']} st)", sk["innerhorn"], "vågrätt snitt"),
        rad("Gavelns takkant (uppskattat)", sk["gavelkant"], "–"),
        rad("Takfönstrens anslutning (antaget)", sk["takfonster"], "–"),
        ["Källarens fönster och dörr (uppskattat)", f(sk["kallarfonster"]["psi"], 3), "–", "–", "–"],
    ]
    # 3D
    namn3 = {"kallare-ute": "källaren–uteluften", "kallare-mark": "källaren–markytan", "ute-varme": "golvvärmen–uteluften",
             "varme-mark": "golvvärmen–markytan", "inne-varme": "golvvärmen–plan 1", "kallare-varme": "golvvärmen–källaren",
             "kallare-inne": "källaren–plan 1", "ute-inne": "plan 1–uteluften", "inne-mark": "plan 1–markytan"}
    koppling3d = []
    for k, v in k3.items():
        a, b = k.split("-")
        key = k if k in namn3 else f"{b}-{a}"
        if abs(v) < 0.05 or key not in namn3:
            continue
        g = kg.get(k, kg.get(f"{b}-{a}", 0.0))
        br = kb.get(k, kb.get(f"{b}-{a}", 0.0))
        koppling3d.append([namn3[key], f(v, 1), f(g, 1), f(br, 1)])
    # förlusterna
    kat = sorted(fl0, key=lambda k: -fl0[k])
    forl = [[k, f(fl0[k]), f"{f(100 * fl0[k] / tot0, 1)} %", f(fld.get(k, 0)), f"{f(100 * fld.get(k, 0) / totd, 1)} %"]
            for k in kat]
    forl.append(["Summa = golvvärmens effekt", f(tot0), "100 %", f(totd), "100 %"])
    temp = [["Golvvärmens effekt (W)", f(st0["Q_h"]), f(std["Q_h"])],
            ["– upp till plan 1 (W)", f(st0["upp"]), f(std["upp"])],
            ["– ned till källaren (W)", f(st0["ned"]), f(std["ned"])],
            ["– direkt ut och till marken (W)", f(st0["Q_h"] - st0["upp"] - st0["ned"]), f(std["Q_h"] - std["upp"] - std["ned"])],
            ["Golvvärmens plan (°C)", f(Th, 1), f(std["T"]["varme"], 1)],
            ["Källaren (°C)", f(Tb, 1), f(std["T"]["kallare"], 1)],
            ["Luftutbyte i trapphålet (l/s)", f(st0["q_trapp"]), f(std["q_trapp"])]]
    # årsbalansen
    af = res["arsforluster"]
    ab = [[k, f(v), f(v / At, 1)] for k, v in sorted(af.items(), key=lambda kv: -kv[1])]
    sol = res["sol"]
    ab += [["Summa förluster", f(sum(af.values())), f(sum(af.values()) / At, 1)],
           ["Sol genom fönstren (plan 1 och källaren)", f(sol["plan1"] + sol["kallare"]), f((sol["plan1"] + sol["kallare"]) / At, 1)],
           ["Internlast (hushållsel och personer)", f(sol["intern"]), f(sol["intern"] / At, 1)],
           ["Vädrat bort när det är för varmt", f(res["drift"]["vadring"]), f(res["drift"]["vadring"] / At, 1)],
           ["Golvvärme", f(en["Q"]), f(en["Q_m2"], 1)]]
    VP = P["varmepump"]
    Lg = res["langder"]
    eltak = BB["effekt_bas"] + 0.025 * (At - 130)
    energi_t = [
        ["Golvvärme (uppvärmning)", f"{f(en['Q'])} kWh/år", f"timsimuleringen, {f(T_in)} °C, medel 2014–2023"],
        ["Vädring", f"{f(en['Q_vad'])} kWh/år", f"BEN: 4 kWh/m² Atemp, hemma {f(100 * en['andel_hemma'])} % av tiden"],
        ["Tappvarmvatten", f"{f(en['Q_tvv'])} kWh/år", f"BEN: 20 kWh/m² Atemp, hemma {f(100 * en['andel_hemma'])} % av tiden"],
        ["El till uppvärmningen, E#sub[uppv]", f"{f(en['E_uppv'])} kWh/år", f"värmepumpen timme för timme, årsvärmefaktor {f(en['SCOP'], 1)}"],
        ["El till varmvattnet, E#sub[tvv]", f"{f(en['E_tvv'])} kWh/år", f"årsvärmefaktor {f(VP['COP_tvv'], 1)} (SS-EN 16147, typvärde)"],
        ["Fastighetsel, E#sub[f]", f"{f(en['E_f'])} kWh/år", "fläktarna och pumparna (uppskattat)"],
        ["Köpt el sammanlagt", f"{f(en['E'])} kWh/år", f"{f(en['E_m2'], 1)} kWh/m² Atemp; all värme / all el: {f(en['SPF'], 1)}"],
        ["Primärenergital EP#sub[pet], BEN (21 °C)", f"{f(en_ben['EP'])} kWh/m² och år", f"krav högst {f(BB['EP_krav'])}; köpt el {f(en_ben['E'])} kWh/år"],
        [f"Primärenergital vid {f(T_in)} °C", f"{f(en['EP'])} kWh/m² och år", "som ovan, med husets drift"],
        ["Um", f"{f(res['Um'], 2)} W/m²K", f"krav högst {f(BB['Um_krav'], 2)}"],
        ["Värmebehovets topp (99,9 % av timmarna)", f"{f(en['P_dim'] / 1000, 1)} kW", "värmepumpen 13 kW"],
        ["Värmepumpens el vid toppen", f"{f(en['el_max'] / 1000, 1)} kW",
         f"gräns för installerad eleffekt {f(eltak, 1)} kW (4,5 + 0,025 (Atemp − 130))"],
    ]
    vp_t = [
        ["Värmefaktor B0/W35 (SS-EN 14511)", f(VP["COP_B0W35"], 2), "NIBE S1256-13 (5,12 kW); ger η = " + f(en["eta"], 2)],
        ["Golvvärmens framledning, högst", f"{f(en['T_fram_max'], 1)} °C", f"golvvärmeplanet + {f(VP['R_ror'], 3)} m²K/W · q + {f(VP['dT_vatten'] / 2, 1)} K"],
        ["Köldbärarens medeltemperatur, när värmepumpen går / lägst", f"{f(en['T_kb_drift'], 1)} / {f(en['T_kb_min'], 1)} °C",
         f"berget {f(VP['T_berg'], 1)} °C, borrhål {f(VP['borrhal_L'])} m, efter {f(VP['driftar'])} års drift"],
        ["Värmefaktor, lägst", f(en["cop_min"], 1), "kallaste timmen"],
        ["Årsvärmefaktor för golvvärmen", f(en["SCOP"], 1), "värme / el, timme för timme"],
        ["Värme ur berget", f"{f(en['uttag'])} kWh/år", f"{f(en['uttag_m'])} kWh per meter borrhål och år"],
    ]
    # mellanbjälklagets kanter: värmen genom kantisoleringen
    kn = {"kallare": "Över källarväggarna", "mark": "Plattan på mark"}
    kant_t = []
    for typ, l in (("kallare", Lg["bjalklagskant_kallare"]), ("mark", Lg["bjalklagskant_pm"])):
        a0, ad, aa = st0["kant"][typ], std["kant"][typ], res["kant_ar"][typ]
        kant_t.append([kn[typ], f(l, 1), f(a0 / l, 1), f(a0), f"{f(100 * a0 / tot0, 1)} %", f(ad),
                       f"{f(100 * ad / totd, 1)} %", f(aa), f"{f(100 * aa / sum(af.values()), 1)} %"])
    a0, ad, aa = sum(st0["kant"].values()), sum(std["kant"].values()), sum(res["kant_ar"].values())
    l = Lg["bjalklagskant"]
    kant_t.append(["Summa", f(l, 1), f(a0 / l, 1), f(a0), f"{f(100 * a0 / tot0, 1)} %", f(ad), f"{f(100 * ad / totd, 1)} %",
                   f(aa), f"{f(100 * aa / sum(af.values()), 1)} %"])
    fall_t = [[x["namn"], f(x["H_T"]), f(x["Um"], 2), f(x["Q_dim"] / 1000, 1), f(x["Q"] / 1000, 1),
               f(x["E"] / 1000, 1), f(x["kostnad"]), f(x["EP"])] for x in res["fall"]]
    # kostnaden för grundfallet och andra innetemperaturer (samma användning, bara temperaturen ändrad)
    man = ["jan", "feb", "mar", "apr", "maj", "jun", "jul", "aug", "sep", "okt", "nov", "dec"]
    kost_t = []
    for x in sorted((x for x in res["fall"] if x["namn"] == "Grundfall" or x["namn"].startswith("Inne ")),
                    key=lambda x: x["T_inne"]):
        i = int(np.argmax(x["kostnad_man"]))
        kost_t.append([f"{f(x['T_inne'])} °C" + (" (grundfallet)" if x["namn"] == "Grundfall" else ""),
                       f(x["Q"] / 1000, 1), f(x["E"]), f(x["kostnad"]), f"{f(x['kostnad_man'][i])} ({man[i]})",
                       f(x["T_b_ar"], 1)])
    pris = elpris(P)
    pris_t = [[m_, f(float(np.mean([a[i] for a in P["elpris"]["spot"]])), 1), f(pris[i], 1), f(en["E_man"][i]),
               f(en["kostnad_man"][i])] for i, m_ in enumerate(man)]
    pris_t.append(["Året", f(float(np.mean(P["elpris"]["spot"])), 1), f(en["pris_medel"], 1) + " (vägt)", f(en["E"]),
                   f(en["kostnad"])])
    # kontrollerna
    kt = []
    for k in res["kontroller"]:
        if "fv" in k:
            kt.append([k["namn"], f(k["fv"], 4 if k["fv"] < 1 else 2), f(k["ref"], 4 if k["ref"] < 1 else 2),
                       f"{f(100 * k['avvikelse'], 2)} %"])
        elif "ordning" in k:
            kt.append([k["namn"] + " (fel vid h = 20, 10, 5 mm)",
                       " / ".join(tiopot(e) for _, e in k["fel"]), "andra ordningen",
                       f"ordning {f(k['ordning'], 2)}"])
    for v in vagg[:1]:
        kt.append([f"Vägg {v['kod']}: 2D mellan ISO 6946:s gränser", f(v["U"], 3), f"{f(v['U_min'], 3)}–{f(v['U_max'], 3)}",
                   "inom" if v["U_min"] <= v["U"] <= v["U_max"] else "utanför"])
    nn = {"bjalklag_kallare": "mellanbjälklagets kant över källarvägg (ψ#sub[he])",
          "bjalklag_mark": "mellanbjälklagets kant, plattan på mark (ψ#sub[he])", "takfot": "takfoten",
          "nock": "nocken", "dal": "dalen", "fonster": "fönstrets anslutning", "horn": "ytterhörnet"}
    for namn, (a, b) in res["nat2d"].items():
        kt.append([f"Nätkontroll, {nn.get(namn, namn)}: ψ med {f(P['nat']['h_2d'], 1)} och {f(P['nat']['h_2d'] / 2, 2)} mm",
                   f(a, 4), f(b, 4), f"{f(100 * (a / b - 1), 1)} %"])
    hg = sum(res["HT_grov"].values())
    kt.append(["Nätkontroll 3D: H#sub[T] med dubbelt så grovt nät", f(res["H_T"], 1), f(hg, 1), f"{f(100 * (res['H_T'] / hg - 1), 1)} %"])
    dyn = R[0].get("_kontroll_dyn")
    if dyn:
        kt.append(["Timsimuleringen med konstant väder mot stationärt (golvvärmens effekt)", f(dyn[0]), f(dyn[1]),
                   f"{f(100 * (dyn[0] / dyn[1] - 1), 3)} %"])
    kt.append(["Gradtimmar mot timsimuleringen (golvvärme per år)", f(res["gradtimmar_Q"] / 1000, 1) + " MWh", f(en["Q"] / 1000, 1) + " MWh",
               f"{f(100 * (res['gradtimmar_Q'] / en['Q'] - 1), 0)} %"])
    k21 = res["kallarkurvor"]["21"]
    kallare_t = []
    for te in (-15, -10, -5, 0, 5, 10, 15):
        i = k21["T_e"].index(float(te))
        kallare_t.append([f(te), f(k21["T_h"][i], 1), f(k21["T_b"][i], 1), f(k21["Q_h"][i] / 1000, 1),
                          f(k21["upp"][i] / 1000, 1), f(k21["ned"][i] / 1000, 1),
                          f"{f(100 * k21['ned'][i] / k21['Q_h'][i] if k21['Q_h'][i] > 0 else 0)} %", f(k21["trapp"][i])])
    tabs = dict(sammanfattning=sam, vaggar=vaggar, byggdelar=byggdelar, skarvar=skarvar_t, koppling3d=koppling3d,
                forluster=forl, temperaturer=temp, arsbalans=ab, energi=energi_t, fall=fall_t, kontroller=kt,
                varmepump=vp_t, kant=kant_t, kallare=kallare_t, kostnad=kost_t, elpris=pris_t)
    return t, tabs


if __name__ == "__main__":
    main()
