"""
Beräkning av nock- och dalbalkar som stål–trä-komposit (plattstål + limträliv).

    python berakning.py            -> nock_och_dalbalkar_K-01.pdf

Läser indata.toml, räknar enligt SS-EN 1990/1991/1993/1995 med EKS (analys.py),
ritar figurer och sätter ihop PDF via Typst (mall.typ).
Kräver: pip install typst matplotlib numpy scipy
"""
import json
import math
import tomllib
from pathlib import Path

import numpy as np

from analys import Balkanalys, Kompositbalk

HERE = Path(__file__).parent
IN = tomllib.loads((HERE / "indata.toml").read_text(encoding="utf-8"))


def fmt(x, n=1):
    """Svenskt decimalkomma, avrundning halv uppåt, mellanslag som tusentalsavgränsare."""
    from decimal import Decimal, ROUND_HALF_UP
    q = Decimal(repr(float(x))).quantize(Decimal(1).scaleb(-n), rounding=ROUND_HALF_UP)
    if q == 0:
        q = abs(q)
    s = f"{q:,.{n}f}".replace(",", " ").replace(".", ",")
    return s.replace("-", "−")


def pct(u):
    return fmt(100 * u, 0)


# ------------------------------------------------------------------ indata
geo, st, tr, sk, la, mo = IN["geometri"], IN["stal"], IN["tra"], IN["skruv"], IN["laster"], IN["modell"]
b, t, H = geo["b"], geo["t_pl"], geo["h_tot"]
Ht = geo.get("h_tra", H)                                              # limträ utan plåt
hw = H - 2 * t
Es, Et, Gt = st["E"], tr["E0mean"], tr["Gmean"]
A1, I1, I2, a1 = b * t, b * t ** 3 / 12, b * hw ** 3 / 12, (t + hw) / 2
psi0, psi2, kdef, kmod, gd = la["psi0"], la["psi2"], tr["k_def"], tr["k_mod"], la["gamma_d"]
E2fin = Et / (1 + psi2 * kdef)                                        # EC5 2.3.2.2(2)

# ------------------------------------------------------------------ laster
cos_a = math.cos(math.radians(la["takvinkel"]))
g_tak_h = la["g_tak"] / cos_a                                        # kN/m² horisontell projektion
m_balk = (2 * b * t * st["densitet"] + b * hw * tr["rho_mean"]) * 1e-6  # kg/m, med plåt
m_utan = (2 * b * IN["distans"]["tjocklek"] * IN["distans"]["densitet"] + b * hw * tr["rho_mean"]) * 1e-6   # kg/m, utan plåt
g_balk = m_balk * 9.81 / 1000                                        # kN/m
g_utan = m_utan * 9.81 / 1000
# vind (SS-EN 1991-1-4 med EKS): hastighetstryck, terrängtyp och formfaktorer för tak, vind längs nocken
vi = IN["vind"]
z0 = {0: 0.003, 1: 0.01, 2: 0.05, 3: 0.3, 4: 1.0}[vi["terrang"]]
kr = 0.19 * (z0 / 0.05) ** 0.07
cr = kr * math.log(max(vi["z"], 1.0) / z0)
Iv = 1 / math.log(max(vi["z"], 1.0) / z0)
qb = 0.5 * 1.25 * vi["vb"] ** 2 / 1000                              # kN/m²
qp = (1 + 7 * Iv) * cr ** 2 * qb
cnet = {z: vi["cpe"][z] - vi["cpi"] for z in ("G", "H", "I")}       # sug + invändigt övertryck
LAST = {}
for typ in ("nock", "dal"):
    lb, snb = la[typ]["lastbredd"], la[typ]["snobredd"]
    G = g_tak_h * lb + g_balk
    S = la["s_k"] * snb
    W = {z: qp * cnet[z] * lb for z in cnet}                           # kN/m, uppåt negativ
    LAST[typ] = dict(lastbredd=lb, snobredd=snb, g_tak=g_tak_h * lb, G=G, G_utan=g_tak_h * lb + g_utan, S=S, W=W,
                     qW={z: (g_tak_h * lb + g_balk) + gd * 1.5 * W[z] for z in W},
                     q610a=gd * (1.35 * G + 1.5 * psi0 * S), q610b=gd * (1.2 * G + 1.5 * S),
                     qgynn=1.0 * G + gd * 1.5 * S, qperm=gd * 1.35 * G, qk=G + S)
    LAST[typ]["perm_rel"] = (LAST[typ]["qperm"] / 0.6) / (LAST[typ]["q610b"] / kmod)   # k_mod 0,6 permanent

# ------------------------------------------------------------------ skruv Ø10, rak, vinkelrät mot fogen
d, d1, lef = sk["d"], sk["d1"], sk["l_ef"]
My = sk["My_Rk"] * 1000                                                # Nmm
rho_k, rho_m = tr["rho_k"], tr["rho_mean"]
d_ef = 1.1 * d1                                                       # EC5 8.7.1(3)
f_h = 0.082 * (1 - 0.01 * d_ef) * rho_k                              # EC5 (8.32), d_ef > 6 mm (8.7.1(4))
f_axk = 0.52 * d ** -0.5 * lef ** -0.1 * rho_k ** 0.8                # EC5 (8.39)
k_d = min(d / 8, 1.0)                                                 # EC5 (8.40)
F_ax = f_axk * d * lef * k_d / (1.2 * math.cos(math.radians(90)) ** 2 + math.sin(math.radians(90)) ** 2)  # (8.38), α = 90°
jc_0 = f_h * lef * d_ef * (math.sqrt(2 + 4 * My / (f_h * d_ef * lef ** 2)) - 1)   # EC5 (8.10c) utan lindragseffekt
jd_0 = 2.3 * math.sqrt(My * f_h * d_ef)                                            # (8.10d)
je = f_h * lef * d_ef                                                              # (8.10e)
jc = jc_0 + min(F_ax / 4, jc_0)                                       # lindragseffekt ≤ 100 % för skruv, 8.2.2(2)
jd = jd_0 + min(F_ax / 4, jd_0)
FvRk = min(jc, jd, je)
mod = "c" if FvRk == jc else ("d" if FvRk == jd else "e")
FRd = kmod * FvRk / sk["gamma_M"]
Kser = rho_m ** 1.5 * d / 23                                          # EC5 tabell 7.1 (förborrat)
K_up = 2 / 3 * 2.0 * Kser                                             # 7.1(3) stål–trä ×2, 2.2.2(2) K_u = 2/3 K_ser
K_low = 2 / 3 * Kser / (1 + psi2 * kdef)                              # utan stålfaktor, slutvärde 2.3.2.2(2)

# ------------------------------------------------------------------ stål
eps = math.sqrt(235 / st["fy"])
lam1 = 93.9 * eps
i_pl = t / math.sqrt(12)


def NbRd(Lcr):
    """Knäckning av plåten mellan skruvar i samma rad, kurva c (EC3 6.3.1)."""
    lb = np.asarray(Lcr, float) / i_pl / lam1
    phi = 0.5 * (1 + 0.49 * (lb - 0.2) + lb ** 2)
    chi = np.minimum(1.0, 1 / (phi + np.sqrt(phi ** 2 - lb ** 2)))
    return chi * A1 * st["fy"] / st["gamma_M1"]


A_hal = sk["hal"] * t                                                 # cylindriskt hål, ingen försänkning
A_net = A1 - 2 * A_hal                                                # två hål i samma snitt (konservativt)
A_net3 = A1 - 3 * A_hal                                               # tre rader
NuRd = 0.9 * A_net * st["fu"] / st["gamma_M2"]                        # EC3 6.2.3
NuRd3 = 0.9 * A_net3 * st["fu"] / st["gamma_M2"]
fyd = st["fy"] / st["gamma_M0"]
fmd = kmod * tr["fmk"] / tr["gamma_M"]
fvd = kmod * tr["fvk"] / tr["gamma_M"]
tauRd = tr["k_cr"] * fvd
fc90d = kmod * tr["fc90k"] / tr["gamma_M"]

P = dict(G={k: v["G"] for k, v in LAST.items()}, S={k: v["S"] for k, v in LAST.items()},
         Gtak={k: v["g_tak"] for k, v in LAST.items()}, g_med=g_balk, g_utan=g_utan,
         vind=dict(e=vi["e"] * 1000, w={k: v["W"] for k, v in LAST.items()}),
         gamma_d=gd, psi0=psi0, psi0_T=la["psi0_T"], EI0=2 * Es * I1 + E2fin * I2, EA=Es * A1, a=a1, K_up=K_up, K_low=K_low,
         F_Rd=FRd, Es=Es, Et=Et, A1=A1, I1=I1, t=t, b=b, hw=hw, h_tra=Ht, E2fin=E2fin, I2=I2, fyd=fyd, fmd=fmd, tauRd=tauRd,
         NbRd=NbRd, NuRd=NuRd, NuRd3=NuRd3, ande=float(sk["ande"]), ande_plat=float(sk["ande_plat"]),
         k_vagg=float(mo["k_vagg"]), alfa_s=st["alfa"], alfa_t=tr["alfa"], temperatur=IN["temperatur"],
         s_tre_rader=float(sk["s_tre_rader"]), rader={2: [float(v) for v in sk["rader2"]], 3: [float(v) for v in sk["rader3"]]},
         a1_rad=7.0 * d)
k_lim = float(IN["lim"]["k_lim"])
L_slapp = float(IN["lim"]["L_slapp"])
c_T1, c_T2 = gd * 1.5 * la["psi0_T"], gd * 1.5             # temperatur som följdlast resp. huvudlast

# ------------------------------------------------------------------ bruksgräns (lim + skruv)
EI_st = 2 * Es * (I1 + A1 * a1 ** 2)
EI_full = EI_st + Et * I2
EI_tra190 = Et * b * Ht ** 3 / 12
GA = Gt * b * hw
EI_hea = Es * 36.92e6


def w_falt(A, G, S, lo, hi, a_, b_, k_fn):
    """Fritt upplagt fält (stöd a_, b_; modellens del lo–hi) med krypning i trädelen (2.3.2.2(1)):
    w_fin = w(G; E0/(1+kdef)) + w(S; E0/(1+ψ2 kdef)) + skjuvdeformation. k_fn(fak) ger fogens styvhet per element."""
    i0 = int(np.argmin(np.abs(A.xn - lo))); i1 = int(np.argmin(np.abs(A.xn - hi)))
    xs = A.xn[i0:i1 + 1]
    na = int(np.argmin(np.abs(xs - a_))); nb = int(np.argmin(np.abs(xs - b_)))
    w = np.zeros(len(xs))
    for q, fak in ((G, kdef), (S, psi2 * kdef)):
        EI0, EA, EIw = A.egenskaper(Et / (1 + fak))
        m = Kompositbalk(xs, EI0[i0:i1], EA[i0:i1], a1, k_fn(fak)[i0:i1], EIw[i0:i1])
        U, _, _ = m.los(np.full((i1 - i0, 1), q), [na, nb])
        w += -U[0:3 * len(xs):3, 0]
        xm = np.clip(xs, a_, b_) - a_
        w += q * xm * (b_ - a_ - xm) / (2 * Gt / (1 + fak) * b * hw)     # skjuvdeformation (liv 170, konservativt)
    A.egenskaper(E2fin)
    sel = (xs >= a_) & (xs <= b_)
    return float(w[sel].max())


def w_kontinuerlig(A, G, S, k_arr):
    """Nedböjning för den kontinuerliga balken (fält utan plåt): fältvis snö, stöden förankrade eller bara
    tryck (det största), hela lasten med E0/(1 + kdef) (konservativt för snön). Vägg som ensidigt underlag."""
    import itertools
    EI0, EA, EIw = A.egenskaper(Et / (1 + kdef))
    m = Kompositbalk(A.xn, EI0, EA, a1, k_arr, EIw)
    A.egenskaper(E2fin)
    Q = []
    for mask in itertools.product([0, 1], repeat=len(A.zoner)):
        q = A.G_el / A.G * G
        for i, on in enumerate(mask):
            if on:
                a_, b_ = A.zoner[i]
                q = q + np.where((A.xm > a_) & (A.xm < b_), S, 0.0)
        Q.append(q)
    Q = np.array(Q).T
    fasta = [n for n in A.n_huvud if n not in A.n_vagg]
    w = np.zeros(len(A.xn))
    for f_, e_ in ((fasta, []), ([], fasta)):
        U = m.los_kontakt(Q, f_, e_, A.fjader)[0]
        w = np.maximum(w, (-U[0:3 * len(A.xn):3, :]).max(axis=1))
    return w


def lmax_tra(G, S):
    """Längsta fritt upplagda fält för enbart limträ b×Ht: L/300 med krypning, böjning och tvärkraft."""
    from scipy.optimize import brentq
    I = b * Ht ** 3 / 12
    def w(L):
        return sum(q * (5 * L ** 4 / (384 * Et / (1 + f) * I) + L ** 2 / (8 * Gt / (1 + f) * b * Ht))
                   for q, f in ((G, kdef), (S, psi2 * kdef)))
    Lw = brentq(lambda L: w(L) - L / la["nedbojning_krav"], 500, 20000)
    qd_ = gd * (1.2 * G + 1.5 * S)
    LM = math.sqrt(8 * fmd * b * Ht ** 2 / 6 / qd_)
    LV = 2 * tauRd * b * Ht / 1.5 / qd_
    return min(Lw, LM, LV), Lw, LM


def txt(v):
    """Indatavärde som text: heltal som de är, decimaltal med decimalkomma utan onödiga nollor."""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return v
    if isinstance(v, int) or float(v).is_integer():
        return fmt(v, 0)
    if abs(v) < 1e-3:
        return f"{v:.0e}".replace("e-0", "·10^-").replace(".", ",")
    n = len(repr(float(v)).split(".")[1])
    return fmt(v, min(n, 3))


def txtd(dct):
    return {k: txt(v) for k, v in dct.items() if not isinstance(v, (dict, list))}


# ------------------------------------------------------------------ balkar
BOKST = "ABCDEFGHIJ"
balkar = []
UFULL, POSALLA, TEMP, LIM, UDIST = [], [], [], [], []
namn_k = [("skruv", "Skruv, last och temperatur"), ("plat", "Plåt, normalspänning"),
          ("knack", "Plåt, knäckning mellan skruvar"), ("netto", "Plåt, nettotvärsnitt"),
          ("livbojning", "Limträ, böjspänning"), ("livskjuv", "Limträ, skjuvspänning")]
for nr, B in enumerate(IN["balk"], 1):
    stolpe = None
    if B.get("stolpe"):
        # dubbeltriangel vid stolpen: två strävor kopplade som en gungbräda, stolpens böjstyvhet som rotationsfjäder
        sp_, tr_ = B["stolpe"], B["triangel"]
        e_ = tr_["e"]
        EIp = sp_["E"] * sp_["b"] * sp_["h"] ** 3 / 12
        kth = 3 * EIp / sp_["L"] * (1 + sp_["d"] / sp_["L"])        # ledad i golvet, hållen i sidled upptill
        B["koppling"] = dict(x=tr_["x"], e=e_, kth=kth)
        stolpe = dict(e=e_, kth=kth)
    A = Balkanalys(B, P, elementlangd=mo["elementlangd"])
    Lq = Lq_ = LAST[B["typ"]]
    rad, lagen = A.dimensionera_och_kontrollera(sk["s_lista"], sk["s_max"], zon_min=sk["zon_min"], fonster=mo["fonster"])
    if IN.get("distans"):
        # skruvschemat ska klara både med och utan distansreglarnas samverkan
        A2 = Balkanalys(B, dict(P, h_tra=float(H)), elementlangd=mo["elementlangd"])
        A2.s_el = A.s_el
        if A2.verifiera(lagen) > 1.0 + 1e-9:
            rad2, lagen2 = A2.dimensionera_och_kontrollera(sk["s_lista"], sk["s_max"], zon_min=sk["zon_min"], fonster=mo["fonster"])
            s_el0 = A.s_el
            A.s_el = A2.s_el
            if A.verifiera(lagen2) <= 1.0 + 1e-9:
                rad, lagen = rad2, lagen2
                print(f"  {B['namn']}: skruvschemat dimensionerat med distansreglarna verkande")
            else:
                A.s_el = s_el0
                A.verifiera(lagen)
    s_akt = A.s_akt.copy()
    mu = A.max_utn()
    FT_skruv = A.FT
    # om limmet verkar: limfog med styvhet k_lim i hela plåtbitarna
    k_glue = np.where(A.plat_el, k_lim, 0.0)
    xf, Mfx, Mfn, Vf = A.full_samverkan(k_glue)
    U_full = A.utnyttjande(A.res_full, np.where(A.plat_el, 100.0, np.inf))
    # balkteorin beskriver inte skjuvspänningen i livets mitt närmare än en balkhöjd från en plåtände
    # (kraftinföring); där bedöms i stället limfogen nedan
    nara = np.zeros(A.ne, bool)
    for p0, p1 in A.platar:
        nara |= (np.abs(A.xm - p0) < H) | (np.abs(A.xm - p1) < H)
    U_full["livskjuv"] = np.where(nara & A.plat_el, 0.0, U_full["livskjuv"])
    q_lim = np.zeros(A.ne)
    for r_ in A.res_full:
        np.maximum.at(q_lim, r_["f"]["e"], (r_["k_el"][r_["f"]["e"]][:, None] * np.abs(r_["f"]["dl"])).max(axis=1))
    FT_lim = A.temperatur(np.where(A.plat_el, 100.0, np.inf), 1.0, andzon=False, k_full=k_glue)
    # limfogen, karakteristiska värden: snö huvudlast + ψ0·temperatur, eller temperatur huvudlast + ψ0·snö
    qk_ = Lq_["G"] + Lq_["S"]
    tau_L = q_lim / b * qk_ / A.qd
    tau_T = FT_lim["q"] / b
    tau_fog = np.maximum(tau_L + la["psi0_T"] * tau_T, tau_L * (Lq_["G"] + psi0 * Lq_["S"]) / qk_ + tau_T)
    iF = int(np.argmax(tau_fog))
    iL = int(np.argmax(tau_L))
    u_full = max(float(U_full[k].max()) for k in ("plat", "netto", "livbojning", "livskjuv"))
    UFULL.append(u_full)
    # känslighet: limmet släppt närmast plåtänderna (L_slapp), bara skruv där
    k_slapp = lambda fak: A.k_limfog(k_lim, s_akt, 2 * Kser / (1 + fak), L_slapp)[0]
    FT_slapp = A.temperatur(s_akt, 2 * Kser, andzon=True, k_full=k_slapp(psi2 * kdef))
    x, Mmax, Mmin, Vabs = A.omhyllning()             # omhyllande för alla modeller, med och utan lim
    reak = A.reaktioner()
    if stolpe:
        xd_, xl_, xr_ = B["triangel"]["x"], B["triangel"]["x"] - stolpe["e"], B["triangel"]["x"] + stolpe["e"]
        Nmax, Nmin, Mmx, FLm, FRm = 0.0, 0.0, 0.0, 0.0, 0.0
        for r_ in A.alla_kor():
            ix = {}
            for j_, xx_ in enumerate(r_["sup"]):
                for nm_, xv_ in (("D", xd_), ("L", xl_), ("R", xr_)):
                    if abs(xx_ - xv_) < 1.0:
                        ix[nm_] = j_
            if len(ix) < 3:
                continue
            RD_, FL_, FR_ = (r_["R"][ix[k_]] for k_ in ("D", "L", "R"))
            N_ = RD_ + FL_ + FR_
            Nmax = max(Nmax, float(N_.max())); Nmin = min(Nmin, float(N_.min()))
            Mmx = max(Mmx, float(np.abs((FR_ - FL_) * stolpe["e"]).max()))
            FLm = max(FLm, float(np.abs(FL_).max())); FRm = max(FRm, float(np.abs(FR_).max()))
        RDss = max(rr["Rmax"] for rr in reak if abs(rr["x"] - xd_) < 1e-6)
        FE, RD = max(FLm, FRm), RDss
        sp_ = B["stolpe"]
        Ap, Wp = sp_["b"] * sp_["h"], sp_["b"] * sp_["h"] ** 2 / 6
        Ltot = sp_["L"]                       # knutpunkten hålls i sidled av triangeln och balken
        lam = Ltot * math.sqrt(12) / sp_["h"]
        lrel = lam / math.pi * math.sqrt(sp_["fc0k"] / sp_["E005"])
        kk = 0.5 * (1 + 0.2 * (lrel - 0.3) + lrel ** 2)
        kc = 1 / (kk + math.sqrt(kk ** 2 - lrel ** 2))
        kh = min((150 / sp_["h"]) ** 0.2, 1.3)
        Nd, Md = max(Nmax, RDss), Mmx
        u_st = Nd / (kc * Ap * kmod * sp_["fc0k"] / sp_["gamma_M"]) + Md / (Wp * kh * kmod * sp_["fmk"] / sp_["gamma_M"])
        stolpe.update(FE=FE, RD=RD, Nd=Nd, Md=Md, kc=kc, u=u_st, Nmin=Nmin,
                      txt=dict(kth=fmt(stolpe["kth"] / 1e9, 2), FE=fmt(FE / 1e3, 1), Nmin=fmt(-Nmin / 1e3, 1), Fax=fmt(FE * math.sqrt(1 + (sp_["d"] / stolpe["e"]) ** 2) / 1e3, 1), Nd=fmt(Nd / 1e3, 1), Md=fmt(Md / 1e6, 1),
                               kc=fmt(kc, 2), u=pct(u_st), ok=bool(u_st <= 1.0), e=fmt(stolpe["e"], 0), text=sp_["text"], L=fmt(sp_["L"], 0)))
        lef_s = FE / (b * tr["k_c90"] * fc90d)
        stolpe["l_strava"] = next(l_ for l_ in range(1, 2000) if l_ + 2 * min(30.0, l_) >= lef_s)
        stolpe["txt"]["l_strava"] = fmt(stolpe["l_strava"], 0)
        print(f"  stolpe: N_min {Nmin/1e3:.1f} kN, F_strava {FE/1e3:.1f} kN, N_d {Nd/1e3:.1f} kN, M_d {Md/1e6:.2f} kNm, kc {kc:.2f}, utn {u_st:.2f}")
    # bruksgräns per fält: lim (k_lim) och, som jämförelse, enbart skruv; temperatur ψ0·w_T läggs till
    brg = []
    wT = FT_lim["w"]                                   # (fält, fall), nedåt positiv
    w_kont = w_kontinuerlig(A, Lq["G"], Lq["S"], k_glue)
    for jj, ((lo, hi, a_, b_), lab) in enumerate(zip(A.ss, zip(BOKST, BOKST[1:]))):
        L = b_ - a_
        har_plat = bool(A.plat_el[(A.xm > a_) & (A.xm < b_)].mean() > 0.5)   # fältet har plåt (inte bara vid stödet)
        wt = max(0.0, float(wT[jj].max()))
        if har_plat:
            wf = w_falt(A, Lq["G"], Lq["S"], lo, hi, a_, b_, lambda fak: np.where(A.plat_el, k_lim, 0.0))
        else:                                   # limträ utan plåt: del av den kontinuerliga balken
            sel_ = (A.xn > a_) & (A.xn < b_)
            wf = float(w_kont[sel_].max()) + sum(q * L ** 2 / (8 * Gt / (1 + f) * b * Ht)
                                                for q, f in ((Lq["G"], kdef), (Lq["S"], psi2 * kdef)))
            wt = 0.0
        wtot = wf + la["psi0_T"] * wt
        ws = (w_falt(A, Lq["G"], Lq["S"], lo, hi, a_, b_, k_slapp)
              + la["psi0_T"] * max(0.0, float(FT_slapp["w"][jj].max()))) if har_plat else None
        wsk = (w_falt(A, Lq["G"], Lq["S"], lo, hi, a_, b_,
                      lambda fak: A.k_fog(s_akt, 2 * Kser / (1 + fak))) + la["psi0_T"] * wt) if har_plat else None
        gr = L / la["nedbojning_krav"]
        brg.append(dict(fran=lab[0], till=lab[1], L=fmt(L, 0), w=fmt(wf, 1), wT=fmt(wt, 1), wtot=fmt(wtot, 1),
                        wgr=fmt(gr, 1), u=pct(wtot / gr), uval=wtot / gr, plat=har_plat,
                        ws=(fmt(ws, 1) if ws is not None else "–"), us=(pct(ws / gr) if ws is not None else "–"),
                        usval=(ws / gr if ws is not None else 0.0), wsk=(fmt(wsk, 1) if wsk is not None else "–"),
                        uskval=(wsk / gr if wsk is not None else 0.0)))
    # stöd
    stod, ankare = [], []
    for i, r in enumerate(reak):
        bok = BOKST[i]
        if stolpe and abs(r["x"] - B["triangel"]["x"]) < 1.0:
            # stolpen med dubbeltriangel: hela stolpkraften (balken direkt + båda strävorna)
            r = dict(r, Rmax=stolpe["Nd"], Rmin=stolpe["Nmin"], Rdirekt=r["Rmax"])
        over_plat = bool(A.plat_el[np.abs(A.xm - r["x"]) < 60].any())
        if r["vagg"]:
            stod.append(dict(bok=bok, x=f"{fmt(A.vagg[0], 0)}–{fmt(A.vagg[1], 0)}", Rmax=fmt(r["Rmax"] / 1e3, 1),
                             Rmin="–", lyft=False, l="–", vagg=True, Rvagg=fmt(r["Rvagg"] / 1e3, 0), plat=over_plat,
                             Rvagg_lyft=fmt(-r.get("Rvagg_lyft", 0.0) / 1e3, 1)))
            continue
        # EC5 6.1.5(1): tillägget på varje sida är högst 30 mm, högst l och högst avståndet till balkänden
        lef_req = r.get("Rdirekt", r["Rmax"]) / (b * tr["k_c90"] * fc90d)
        l_req = next(l_ for l_ in range(1, 2000)
                     if l_ + min(30.0, l_, max(r["x"] - l_ / 2, 0.0)) + min(30.0, l_, max(A.L - r["x"] - l_ / 2, 0.0)) >= lef_req)
        lyft = r["Rmin"] < -50.0
        if lyft:
            ankare.append(f"{bok}: {fmt(-r['Rmin'] / 1e3, 1)} kN")
        stod.append(dict(bok=bok, x=fmt(r["x"], 0), Rmax=fmt(r["Rmax"] / 1e3, 1), Rmin=fmt(r["Rmin"] / 1e3, 1),
                         lyft=lyft, l=fmt(l_req, 0), vagg=False, plat=over_plat))
    # plåtbitar och skruvzoner
    bitar = []
    for i, (p0, p1) in enumerate(A.platar):
        xy = lagen[i]
        bitar.append(dict(nr=i + 1, fran=fmt(p0, 0), till=fmt(p1, 0), L=fmt(p1 - p0, 0), n=len(xy),
                          massa=fmt((p1 - p0) / 1000 * A1 * 1e-6 * st["densitet"], 0)))
    zoner = [dict(bit=z[0] + 1, x=f"{fmt(z[1], 0)}–{fmt(z[2], 0)}", cc=fmt(z[5] * z[3], 0), rader=z[5], n=z[4]) for z in rad]
    n_plat = sum(len(v) for v in lagen.values())
    POSALLA.append(lagen)
    kontroller = [dict(namn=n, u=pct(mu[k][0]), x=fmt(mu[k][1], 0), ok=mu[k][0] <= 1.0) for k, n in namn_k]
    umax = max(v[0] for v in mu.values())
    fvk_cr = tr["k_cr"] * tr["fvk"]
    lim_d = dict(namn=B["namn"], tauL=fmt(tau_L.max(), 2), xL=fmt(A.xm[iL], 0), tauT=fmt(tau_T.max(), 2),
                 tau=fmt(tau_fog[iF], 2), x=fmt(A.xm[iF], 0), u=pct(tau_fog[iF] / fvk_cr), uval=tau_fog[iF] / fvk_cr,
                 uL=pct(tau_L.max() / fvk_cr))
    LIM.append(lim_d)
    # kontroll: distansreglarna fullt verkande (limträ som b×H där plåt saknas), samma skruvschema
    u_dist = None
    if IN.get("distans"):
        A2 = Balkanalys(B, dict(P, h_tra=float(H)), elementlangd=mo["elementlangd"])
        A2.s_el = A.s_el
        A2.verifiera(lagen)
        mu2 = A2.max_utn()
        A2.full_samverkan(np.where(A2.plat_el, k_lim, 0.0))
        U2 = A2.utnyttjande(A2.res_full, np.where(A2.plat_el, 100.0, np.inf))
        U2["livskjuv"] = np.where(nara & A2.plat_el, 0.0, U2["livskjuv"])
        u_dist = max(max(v[0] for v in mu2.values()), max(float(U2[k].max()) for k in ("plat", "netto", "livbojning", "livskjuv")))
        UDIST.append(u_dist)
    UF_k = {k: (pct(float(U_full[k].max())), fmt(A.xm[int(np.argmax(U_full[k]))], 0)) for k in ("plat", "netto", "livbojning", "livskjuv")}
    temp = dict(namn=B["namn"], F=fmt(FT_skruv["F"].max() / 1e3, 2), q=fmt(FT_lim["q"].max() / b, 2),
                sig=fmt(max(FT_skruv["sig"].max(), FT_lim["sig"].max()), 0),
                w=fmt(max(0.0, float(FT_lim["w"].max())), 1), Fv=FT_skruv["F"].max())
    TEMP.append(temp)
    bdict = dict(
        nr=nr, namn=B["namn"], typ=B["typ"], typtext="nockbalk" if B["typ"] == "nock" else "dalbalk",
        total=fmt(B["total"], 0), spann=" + ".join(fmt(s, 0) for s in B["spann"]),
        utstick=fmt((B["total"] - sum(B["spann"])) / 2, 0) if not B.get("vagg") else "0",
        vagg=bool(B.get("vagg")), strava=bool(B.get("strava")), stolpe=(stolpe["txt"] if stolpe else None),
        vagg_txt=(f"{fmt(B['vagg'][0], 0)}–{fmt(B['vagg'][1], 0)}" if B.get("vagg") else ""),
        G=fmt(Lq["G"], 2), S=fmt(Lq["S"], 2), qd=fmt(Lq["q610b"], 2),
        Mmax=fmt(Mmax.max() / 1e6, 1), Mmin=fmt(Mmin.min() / 1e6, 1), V=fmt(Vabs.max() / 1e3, 1),
        kontroller=kontroller, umax=pct(umax), u_full=pct(u_full),
        ok=A.konvergerad and A.verifierad and umax <= 1.0 and u_full <= 1.0 and all(z["uval"] <= 1.0 and z["usval"] <= 1.0 for z in brg),
        uf=UF_k, u_full_ok=u_full <= 1.0, us_max=pct(max(z["usval"] for z in brg)),
        stod=stod, ankare=ankare, brg=brg, zoner=zoner, bitar=bitar, n_plat=n_plat, n_balk=2 * n_plat,
        over_stod=[s["bok"] for s in stod if s["plat"]],
        stal_m=(sum(p1 - p0 for p0, p1 in A.platar) * 2 / 1000), 
        wmax_u=pct(max(z["uval"] for z in brg)),
        lyft_vagg=fmt(max((r_.get("wlyft", 0.0) for r_ in A.alla_kor()), default=0.0), 1),
        fig=f"fig_balk{nr}.svg",
    )
    bdict["stal_txt"] = fmt(bdict["stal_m"], 1)
    bdict["stal_kg"] = fmt(bdict["stal_m"] * A1 * 1e-6 * st["densitet"], 0)
    balkar.append(bdict)
    B["_A"], B["_env"], B["_rad"], B["_lagen"] = A, (x, Mmax, Mmin, Vabs), rad, lagen
    print(f"{B['namn']}: {2 * n_plat} skruv, max utn {umax:.2f}, limmad {u_full:.2f}, limfog {lim_d['uval']:.2f}, "
          f"distans {u_dist if u_dist is None else round(u_dist, 3)}, BRG {max(z['uval'] for z in brg):.2f}/{max(z['usval'] for z in brg):.2f}, konv {A.konvergerad}, verif {A.verifierad}")
    # hålbild per plåtbit (över- och underplåt; underplåtens rader speglade)
    with open(HERE / f"halbild_{B['namn'].lower().replace(' ', '')}.csv", "w", encoding="utf-8") as fh:
        fh.write(f"# {B['namn']}, total längd {B['total']} mm. Hål Ø{txt(sk['hal'])}, utan försänkning. "
                 f"x från vänster balkände, y från plåtens kant mot balkens framsida [mm].\n")
        fh.write("# Underplåtens rader är speglade (y_under = 200 - y_over) så att skruvarna i ytterraderna inte står mitt för varandra (mittraden y = 100 möts med 10 mm mellan spetsarna).\n")
        fh.write("bit;plat_fran;plat_till;nr;x_mm;y_over;y_under\n")
        for i, (p0, p1) in enumerate(A.platar):
            for k, (xp, yp) in enumerate(lagen[i], 1):
                fh.write(f"{i + 1};{p0:.0f};{p1:.0f};{k};{xp:.0f};{yp:.0f};{b - yp:.0f}\n")

n_tot = sum(bb["n_balk"] for bb in balkar)

# jämförelse: samma plåtlayout utan temperaturpåverkan
n_utanT = None
if mo.get("jamfor_utan_temperatur", False):
    n_utanT = 0
    for B, bb in zip(IN["balk"], balkar):
        A0 = Balkanalys(B, dict(P, temperatur=[]), elementlangd=mo["elementlangd"])
        _, lag0 = A0.dimensionera_och_kontrollera(sk["s_lista"], sk["s_max"], zon_min=sk["zon_min"], fonster=mo["fonster"])
        bb["n_utanT"] = 2 * sum(len(v) for v in lag0.values())
        n_utanT += bb["n_utanT"]
    print(f"Utan temperatur: {n_utanT} skruv")

# ------------------------------------------------------------------ figurer
import figurer                                                    # noqa: E402
figurer.rita_sektion(HERE / "fig_sektion.svg", IN)
figurer.rita_plan(HERE / "fig_plan.svg", IN)
_c = 1 / (Es * A1) + 2 / (Et * b * hw)
figurer.rita_temp(HERE / "fig_temp.svg", math.sqrt(k_lim * _c), math.sqrt(2 * Kser / 100.0 * _c))
for nr, B in enumerate(IN["balk"], 1):
    B["_distans"] = bool(IN.get("distans"))
    figurer.rita_balk(HERE / f"fig_balk{nr}.svg", B, B["_A"], B["_env"], B["_rad"], BOKST)

# ------------------------------------------------------------------ resultat till mallen
R = {
    "projekt": IN["projekt"], "geo": dict(txtd(geo), t_pl_tal=t), "stal": txtd(st), "tra": txtd(tr), "skruv": dict(txtd(sk), rader2=[fmt(v, 0) for v in sk["rader2"]], langd_tal=sk["langd"], rader3=[fmt(v, 0) for v in sk["rader3"]]), "lim": IN["lim"],
    "laster": txtd(la), "modell": txtd(mo),
    "hw": hw, "intr": fmt(sk["langd"] - t, 0), "m_balk": fmt(m_balk, 0), "g_tak_h": fmt(g_tak_h, 3), "g_balk": fmt(g_balk, 2), "g_utan": fmt(g_utan, 2), "m_utan": fmt(m_utan, 0),
    "vindlast": {typ: dict(W={z: fmt(v_, 2) for z, v_ in LAST[typ]["W"].items()}, qW={z: fmt(v_, 2) for z, v_ in LAST[typ]["qW"].items()}) for typ in LAST},
    "vind": dict(vb=fmt(vi["vb"], 0), terrang=vi["terrang"], z=txt(vi["z"]), e=txt(vi["e"]), qb=fmt(qb, 2), qp=fmt(qp, 2), ce=fmt(qp / qb, 2),
                 cpe={z: fmt(vi["cpe"][z], 1) for z in cnet}, cpi=fmt(vi["cpi"], 1), cnet={z: fmt(cnet[z], 1) for z in cnet},
                 e10=fmt(vi["e"] / 10, 1), e2=fmt(vi["e"] / 2, 1), gW=fmt(gd * 1.5, 2)),
    "last": {k: {kk: (txt(vv) if kk in ("lastbredd", "snobredd") else fmt(vv, 2) if isinstance(vv, float) else vv)
                 for kk, vv in v.items()} for k, v in LAST.items()},
    "S_mu2": fmt(1.6 * la["s_k"] * LAST["dal"]["lastbredd"], 2),
    "gG_610a": fmt(gd * 1.35, 2), "gG_610b": fmt(gd * 1.2, 2), "gQ": fmt(gd * 1.5, 2), "gQ_610a": fmt(gd * 1.5 * psi0, 2),
    "d_ef": fmt(d_ef, 2), "f_h": fmt(f_h, 1), "f_axk": fmt(f_axk, 1), "F_ax": fmt(F_ax / 1e3, 2),
    "jc": fmt(jc / 1e3, 2), "jd": fmt(jd / 1e3, 2), "je": fmt(je / 1e3, 2), "FvRk": fmt(FvRk / 1e3, 2), "mod": mod,
    "FRd": fmt(FRd / 1e3, 2), "Kser": fmt(Kser / 1e3, 2), "K_up": fmt(K_up / 1e3, 2), "K_low": fmt(K_low / 1e3, 2),
    "E2fin": fmt(E2fin, 0), "a1": fmt(a1, 0), "fyd": fmt(fyd, 0), "fmd": fmt(fmd, 1), "fvd": fmt(fvd, 2),
    "tauRd": fmt(tauRd, 2), "fc90d": fmt(fc90d, 2), "kfc90d": fmt(tr["k_c90"] * fc90d, 2),
    "A_net": fmt(A_net, 0), "NuRd": fmt(NuRd / 1e3, 0), "Nb_400": fmt(NbRd(2 * sk["s_max"]) / 1e3, 0),
    "A_net3": fmt(A_net3, 0), "NuRd3": fmt(NuRd3 / 1e3, 0),
    "EI_st": fmt(EI_st / 1e12, 2), "EI_tr": fmt(Et * I2 / 1e12, 2), "EI_full": fmt(EI_full / 1e12, 2),
    "EI_hea": fmt(EI_hea / 1e12, 2), "GA": fmt(GA / 1e6, 1),
    "cc_min": fmt(3 * min(sk["s_lista"]), 0), "cc_max": fmt(2 * sk["s_max"], 0),
    "s_min": fmt(min(sk["s_lista"]), 0), "s_max": fmt(sk["s_max"], 0),
    "a1_min": fmt(5 * d, 0), "a2_min": fmt(4 * d, 0), "a3_min": fmt(max(7 * d, 80), 0), "a4_min": fmt(3 * d, 0),
    "a1ax_min": fmt(7 * d, 0), "a2ax_min": fmt(5 * d, 0), "a1cg_min": fmt(10 * d, 0), "a2cg_min": fmt(4 * d, 0),
    "N_plat_dr": fmt(2 * A1 * fyd / 1e3, 0),
    "balkar": balkar, "n_tot": n_tot, "n_utanT": n_utanT,
    "distans": IN.get("distans"), "u_dist": (pct(max(UDIST)) if UDIST else None),
    "w_max_all": pct(max(z["uval"] for bb in balkar for z in bb["brg"])), "us_max_all": pct(max(z["usval"] for bb in balkar for z in bb["brg"])),
    "FT_min": fmt(min(t_["Fv"] for t_ in TEMP) / 1e3, 1), "FT_max": fmt(max(t_["Fv"] for t_ in TEMP) / 1e3, 1),
    "brg_utan_lim": [fmt(z["uskval"], 2) for bb in balkar for z in bb["brg"] if z["plat"]],
    "L_utan_lim": (fmt(min(float(z["L"].replace(" ", "")) / float(z["wsk"].replace(",", ".")) for bb in balkar for z in bb["brg"] if z["plat"] and z["uskval"] > 1), 0), fmt(max(float(z["L"].replace(" ", "")) / float(z["wsk"].replace(",", ".")) for bb in balkar for z in bb["brg"] if z["plat"] and z["uskval"] > 1), 0)), "jfr": {k: fmt(v, 0) for k, v in IN.get("jamforelse", {}).items()}, "temp": TEMP, "lim_tab": LIM, "fvk_cr": fmt(tr["k_cr"] * tr["fvk"], 2),
    "lim_umax": pct(max(l["uval"] for l in LIM)), "lim_umin": pct(min(l["uval"] for l in LIM)), "L_slapp": fmt(L_slapp, 0),
    "lam_lim": fmt(math.sqrt(k_lim * (1 / (Es * A1) + 2 / (Et * b * hw))) * 1e3, 2),
    "u_full_max": pct(max(UFULL)),
    "cc_rad_min": fmt(min(float(np.min(np.diff(xy[xy[:, 1] == y, 0]))) for lg in POSALLA for xy in lg.values()
                          for y in set(xy[:, 1]) if (xy[:, 1] == y).sum() > 1), 0),
    "ok": all(bb["ok"] for bb in balkar),
    "stal_m": fmt(sum(bb["stal_m"] for bb in balkar), 1),
    "stal_kg": fmt(sum(bb["stal_m"] for bb in balkar) * A1 * 1e-6 * st["densitet"], 0),
    "n_bitar": sum(len(bb["bitar"]) for bb in balkar) * 2,
    "lmax_nock": fmt(lmax_tra(LAST["nock"]["G"], LAST["nock"]["S"])[0] / 1000, 2),
    "lmax_dal": fmt(lmax_tra(LAST["dal"]["G"], LAST["dal"]["S"])[0] / 1000, 2),
    "EI_tra190": fmt(EI_tra190 / 1e12, 2),
    "alfa_s": "12", "alfa_t": "5", "k_lim": fmt(k_lim, 0),
    "cT1": fmt(c_T1, 2), "cT2": fmt(c_T2, 2),
    "Ninf": fmt((st["alfa"] - tr["alfa"]) * 1 / (1 / (Es * A1) + 2 / (Et * b * hw)) / 1e3, 2),
    "temperatur": [dict(namn=T["namn"], over=fmt(T["over"], 0), under=fmt(T["under"], 0),
                        To=fmt(20 + T["over"], 0), Tu=fmt(20 + T["under"], 0)) for T in IN["temperatur"]],
}
(HERE / "resultat.json").write_text(json.dumps(R, ensure_ascii=False, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)), encoding="utf-8")

# ------------------------------------------------------------------ PDF
import typst  # noqa: E402
out = HERE / f"nock_och_dalbalkar_{IN['projekt']['dokument']}.pdf"
typst.compile(str(HERE / "mall.typ"), output=str(out), font_paths=["/usr/share/fonts"])
print(f"{out.name}: totalt {n_tot} skruv, OK = {R['ok']}")
