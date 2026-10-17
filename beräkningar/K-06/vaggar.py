"""
K-06: källarväggar av Sundolitt Kub 350-150 (betongkärna 150 mm) mot jordtryck, SS-EN 1992-1-1 med EKS 12.

Färdigt läge: väggen hålls i botten av bottenplattan och i toppen av mellanbjälklaget (TG 2216: vägg som stöds i topp
och botten) och räknas som en lodrät strimla, fritt upplagd mellan fogen mot bottenplattan och mellanbjälklagets
mittplan. Jordtrycket är vilojordtryck, med det kvarstående trycket från packningen intill väggen (Ingold) som undre
gräns, plus last på marken. Lasterna från plan 1 som står utanför kärnan ger ett moment i väggens topp.

Byggskedet: V3 och V20 återfylls innan mellanbjälklaget gjuts (fyllningen bär plattan på mark) och har då fri
överkant. De räknas med brottlinjeteori: bärning åt två håll, inspända i hörnen och ledade i botten. Betongens
hållfasthet vid återfyllningen räknas med SS-EN 1992-1-1 3.1.2, och härdningstiden med mognadsålder (bilaga B).

    python vaggar.py      -> tabell per vägg och byggskedet
"""
import json
import math
import os

import numpy as np

import indata as I

HERE = os.path.dirname(os.path.abspath(__file__))
R05 = json.load(open(os.path.join(I.K05, "resultat.json"), encoding="utf-8"))
VAGG05 = {v["namn"]: v for v in R05["vaggar"]}
_fi = os.path.join(HERE, "innervaggar.json")
INNER = json.load(open(_fi, encoding="utf-8")) if os.path.exists(_fi) else None    # innervaggar.py
from omhyllande import ULS as ULS05      # noqa: E402  (K-05:s kombinationer för lasterna från plan 1)

GD = 0.91
# ULS: (γ för jordtryck och permanent ytlast, γ för nyttig last på marken)
ULS_JORD = {"6.10a": (GD * 1.35, GD * 1.5 * 0.7), "6.10b": (GD * 1.2, GD * 1.5)}
H = I.H_VAGG / 1000                          # m, fri höjd
LS = (I.H_VAGG + I.H_MB / 2) / 1000          # m, spännvidd: fogen mot bottenplattan till mellanbjälklagets mittplan
FYK, GS, GC = 500.0, 1.15, 1.5
FYD = FYK / GS
E_TOPP = (I.T_VAGG / 2 - I.KI - 17.5) / 1000      # m, lasterna över väggen (K-05: 17,5 mm innanför plattkanten)
                                                  # från kärnans mitt


def q06(namn):
    """Väggens last per meter i den samverkande modellen (kontroll06.json), annars 0."""
    f = os.path.join(HERE, "kontroll06.json")
    if not os.path.exists(f):
        return 0.0
    return max((v["q"] for u in json.load(open(f, encoding="utf-8")).values() for v in u["vaggar"]
                if v["namn"] == namn), default=0.0)


# ------------------------------------------------------------------ betong och armering
def fck_t(t, fck=I.FCK_V, s=0.25):
    """f_ck(t) [MPa] vid (mognads)ålder t dygn, SS-EN 1992-1-1 3.1.2(5)–(6); s = 0,25 (N) eller 0,20 (R)."""
    if t >= 28:
        return fck
    b = math.exp(s * (1 - math.sqrt(28 / t)))
    return b * (fck + 8) - 8


def fctm_t(t, fck=I.FCK_V, s=0.25):
    """f_ctm(t) [MPa], 3.1.2(9) med α = 1 före 28 dygn."""
    fctm = 0.30 * fck ** (2 / 3)
    return fctm if t >= 28 else math.exp(s * (1 - math.sqrt(28 / t))) * fctm


def mognad(T):
    """Faktor för mognadsålder vid temperaturen T [°C], SS-EN 1992-1-1 (B.10): t_T = Σ faktor · Δt."""
    return math.exp(-(4000 / (273 + T) - 13.65))


def As(dia, s):
    return math.pi * dia ** 2 / 4 * 1000 / s     # mm²/m


def d_lodrat(dia):
    """Lodräta järn på insidan, innanför de vågräta (som ligger ytterst i elementens hållare)."""
    return I.T_KARNA - I.C_IN - I.ARM_H["d"] - dia / 2


D_H_IN = I.T_KARNA - I.C_IN - I.ARM_H["d"] / 2     # vågräta järn vid insidan
D_H_UT = I.T_KARNA - I.C_UT - I.ARM_H["d"] / 2     # vågräta järn vid utsidan


def MRd(As_, d, fck=I.FCK_V):
    """kNm/m, rektangulärt spänningsblock, b = 1 000 mm."""
    fcd = fck / GC
    x = As_ * FYD / (0.8 * fcd * 1000)
    return As_ * FYD * (d - 0.4 * x) / 1e6


def MRd_N(N, As_, d, h=I.T_KARNA, fck=I.FCK_V):
    """kNm/m kring tvärsnittets mitt med normalkraften N [kN/m] (tryck positivt), dragna järn As_ som flyter."""
    fcd = fck / GC
    x = (N * 1e3 + As_ * FYD) / (0.8 * fcd * 1000)
    assert x < 0.6 * d, x
    return (0.8 * x * fcd * 1000 * (h / 2 - 0.4 * x) + As_ * FYD * (d - h / 2)) / 1e6


def VRdc(As_, d, fck=I.FCK_V):
    """kN/m, 6.2.2 utan tvärkraftsarmering."""
    k = min(1 + math.sqrt(200 / d), 2.0)
    rho = min(As_ / (1000 * d), 0.02)
    v = max(0.18 / GC * k * (100 * rho * fck) ** (1 / 3), 0.035 * k ** 1.5 * math.sqrt(fck))
    return v * d


def fbd(fctm, eta1=1.0):
    """Dimensionerande vidhäftningshållfasthet 8.4.2: 2,25 η1 η2 f_ctd, f_ctd = 0,7 f_ctm / γc (α_ct = 1)."""
    return 2.25 * eta1 * 0.7 * fctm / GC


# ------------------------------------------------------------------ geometri
def vaggar():
    """Väggarna från K-05 med längd, ändar och fyllning, och fasaden med öppningarna som en vägg mellan sina hörn."""
    out = []
    for i, (ax, c, a, b, typ, cs) in enumerate(I.G05["vagg"], 1):
        n = f"V{i}"
        f = I.FYLL.get(n, dict(h=(0.0, 0.0), ande=("h", "h")))
        out.append(dict(namn=n, ax=ax, c=c, a=a, b=b, typ=typ, L=(b - a) / 1000, fyll=f["h"], ande=f["ande"],
                        platta=f.get("platta", False), fasad=False))
    vagg = {v["namn"]: v for v in out}
    for n, f in I.FYLL.items():
        if "fasad" in f:
            lin, (v1, v2) = vagg[f["fasad"]["linje"]], (vagg[x] for x in f["fasad"]["mellan"])
            a, b = sorted((v1["c"], v2["c"]))
            out.append(dict(namn=n, ax=lin["ax"], c=lin["c"], a=a, b=b, typ="yttre", L=(b - a) / 1000, fyll=f["h"],
                            ande=f["ande"], platta=False, fasad=True, omfattar=f["fasad"]["omfattar"]))
    return out


# ------------------------------------------------------------------ jordtryck
def sig_jord(z):
    """Karakteristiskt horisontaltryck från jorden [kPa] på djupet z [m]: vilojordtryck, med det kvarstående
    packningstrycket som undre gräns (Ingold: γ z / K_a nära ytan, sedan σ_komp)."""
    z = np.clip(np.asarray(z, float), 0, None)
    s = np.maximum(I.K0 * I.GAMMA_JORD * z, np.minimum(I.SIG_KOMP, I.GAMMA_JORD * z / I.KA))
    return np.where(z > 0, s, 0.0)


def ytlast(v, bygg=False):
    """Ytlast på marken intill väggen: (permanent, nyttig) [kPa]."""
    if v["platta"]:
        return (I.G_BYGG, I.Q_BYGG) if bygg else (I.G_MARK, I.Q_MARK_PLATTA)
    return 0.0, I.Q_MARK


def tryck_fn(hf, g, q, gG, gQ):
    """Dimensionerande tryck p(y) [kPa], y [m] uppåt från bottenplattan, fyllning till hf."""
    def p(y):
        y = np.asarray(y, float)
        return np.where(y < hf, gG * (sig_jord(hf - y) + I.K0 * g) + gQ * I.K0 * q, 0.0)
    return p


def tryck_k(v, x):
    """Karakteristiskt vilojordtryck vid botten [kPa] och resultant [kN/m] i läget x (m från ände a), utan
    packningstryck (global stabilitet)."""
    ha, hb = v["fyll"]
    hf = ha + (hb - ha) * x / v["L"]
    g, q = ytlast(v)
    return I.K0 * (I.GAMMA_JORD * hf + g + q), I.K0 * (0.5 * I.GAMMA_JORD * hf ** 2 + (g + q) * hf)


def tryck_komp(v, x):
    """Karakteristisk resultant [kN/m] med packningstrycket."""
    ha, hb = v["fyll"]
    hf = ha + (hb - ha) * x / v["L"]
    g, q = ytlast(v)
    z = np.linspace(0, hf, 401)
    return float(np.trapezoid(sig_jord(z), z) + I.K0 * (g + q) * hf)


# ------------------------------------------------------------------ strimla mellan bottenplattan och bjälklaget
def strimla(hf, g, q, M_topp=0.0, n=2000):
    """Lodrät strimla, fritt upplagd på höjderna 0 och LS, med jordtrycket och toppmomentet M_topp [kNm/m, drag i
    insidan]. Största moment, dess höjd, reaktioner [kN/m] och kombination."""
    ys = (np.arange(n) + 0.5) / n * LS
    dy = LS / n
    best = None
    for komb, (gG, gQ) in ULS_JORD.items():
        p = tryck_fn(hf, g, q, gG, gQ)(ys)
        F = p.sum() * dy
        Rt = (p * ys).sum() * dy / LS + M_topp / LS
        Rb = F - Rt
        Mj = np.cumsum((F - (p * ys).sum() * dy / LS) - np.cumsum(p) * dy) * dy     # jordtrycket ensamt
        Mt = Mj + M_topp * ys / LS                                                  # och toppmomentet
        i = int(np.argmax(Mt))
        r = dict(M=float(Mt[i]), y=float(ys[i]), Rb=float(Rb), Rt=float(Rt), komb=komb,
                 V18=float(abs(Rb - p[ys < I.H_GJUT1 / 1000].sum() * dy)), ys=ys, Mlinje=Mt, Mjord=float(Mj.max()))
        if best is None or r["M"] > best["M"]:
            best = r
    return best


def q_ovan(namn):
    """Dimensionerande linjelast [kN/m] från plan 1 som står direkt över väggen (K-05), medel över väggen."""
    w = VAGG05.get(namn)
    if w is None:
        return 0.0
    L = w["L"] / 1000
    return max(cg * w["ovan_G"] + cs * w["ovan_S"] for cg, cq, cs in ULS05.values()) / L


def valj_lodrat(M):
    """Första lodräta armering i I.ARM_V som bär M [kNm/m]."""
    for dia, s in I.ARM_V:
        if MRd(As(dia, s), d_lodrat(dia)) >= M:
            return dia, s
    raise ValueError(M)


def dimensionera(v):
    """Färdigt läge för en vägg med fyllning: största fyllning längs väggen, toppmoment från lasterna över väggen."""
    hf = max(v["fyll"])
    g, q = ytlast(v)
    qo = 0.0 if v["fasad"] else q_ovan(v["namn"])
    Mt = qo * E_TOPP
    s = strimla(hf, g, q, Mt)
    return dict(hf=hf, q_ovan=qo, M_topp=Mt, **{k: s[k] for k in ("M", "y", "Rb", "Rt", "komb", "V18", "Mjord")})


# ------------------------------------------------------------------ fasaden med öppningarna
def fasad(v, Mstrimla):
    """Pelarna mellan öppningarna bär jordtrycket från sin bredd och halva öppningarna intill, lodrätt mellan
    plattorna. Bröstningen under öppningarna spänner vågrätt mellan pelarna."""
    geo = {f"V{i}": w for i, w in enumerate(I.G05["vagg"], 1)}
    pel = [geo[n] for n in v["omfattar"]]
    a0, b0 = v["a"], v["b"]
    out = []
    for k, w in enumerate(pel):
        bredd = (w[3] - w[2]) / 1000
        vanster = (w[2] - pel[k - 1][3]) / 2000 if k > 0 else (w[2] - a0) / 1000
        hoger = (pel[k + 1][2] - w[3]) / 2000 if k < len(pel) - 1 else (b0 - w[3]) / 1000
        f = (bredd + vanster + hoger) / bredd
        out.append(dict(namn=v["omfattar"][k], b=bredd, faktor=f, M=f * Mstrimla))
    oppn = max((pel[k + 1][2] - pel[k][3]) / 1000 for k in range(len(pel) - 1))
    hf = max(v["fyll"])
    g, q = ytlast(v)
    p_max = float(tryck_fn(hf, g, q, *ULS_JORD["6.10a"])(0.0))
    p_max = max(p_max, float(tryck_fn(hf, g, q, *ULS_JORD["6.10b"])(0.0)))
    Mb = p_max * oppn ** 2 / 8
    arm = As(I.OPPNING["d"], 1) * I.OPPNING["n"] / 1000 / min(I.BROSTNING)    # mm²/m över bröstningens höjd
    return dict(pelare=out, oppning=oppn, p=p_max, M_brostning=Mb,
                MRd_brostning=MRd(arm + As(I.ARM_H["d"], I.ARM_H["s"]), D_H_IN))


# ------------------------------------------------------------------ vertikal last
def vertikal(v, arm):
    """Normalkraft [kN/m] i toppen (lasterna från bjälklaget och plan 1, det största av K-05:s värde över 1 m och den
    samverkande modellens) plus egentyngd till halva höjden.
    Ytterväggar (lodräta järn på insidan): normalkraft och moment (jordtryck och toppmoment, eller bara
    toppmomentet från lasterna över väggen, och oavsiktlig excentricitet l0/400) mot momentkapaciteten med
    normalkraft; andra ordningens moment med nominell krökning (5.8.8, K_r = K_φ = 1) om slankheten överskrider
    gränsen i 5.8.3.1.
    Innerväggar (gjutna i ett med bjälklaget): lodräta järn I.ARM_INRE i kärnans mitt; toppmomentet och den minsta
    normalkraften ur K-05:s modell med väggarna som vridfjädrar (innervaggar.json). Den största normalkraften med
    det största momentet, och den minsta (drag nära hörnen) med sitt moment."""
    w05 = VAGG05[v["namn"]]
    q = max(w05["qd_max"], q06(v["namn"]))
    egen = 1.35 * GD * I.G_KUB * H / 2
    N = q + egen
    l0 = LS * 1000
    ei = l0 / 400
    lam = l0 / (I.T_KARNA / math.sqrt(12))
    n_rel = N * 1e3 / (I.T_KARNA * 1000 * I.FCK_V / GC)
    lam_lim = 20 * 0.7 * 1.1 * 0.7 / math.sqrt(max(n_rel, 1e-6))
    M_Ed = v.get("M_Ed") or q_ovan(v["namn"]) * E_TOPP
    if v["typ"] == "inre":
        iv = INNER["vaggar"][v["namn"]]
        dia, s = I.ARM_INRE
        d = I.T_KARNA / 2
        Ast = As(dia, s)
        M2 = N * (FYD / 200000) / (0.45 * d) * l0 ** 2 / 10 / 1000 if lam > lam_lim else 0.0
        M = iv["M"] + N * ei / 1000 + M2
        MR = MRd_N(N, Ast, d)
        Nt, Mt = iv["Nmin"], iv["M_Nmin"]
        MRt = MRd_N(Nt, Ast, d)
        return dict(N=N, M=M, M2=M2, MRd=MR, Mtopp=iv["M"], Nt=Nt, Mt=Mt, MRdt=MRt, NRdt=Ast * FYD / 1e3,
                    utn=max(M / MR, Mt / MRt, -Nt / (Ast * FYD / 1e3)), lam=lam, lam_lim=lam_lim, arm=(dia, s),
                    metod="inre")
    dia, s = arm
    d = d_lodrat(dia)
    M2 = N * (FYD / 200000) / (0.45 * d) * l0 ** 2 / 10 / 1000 if lam > lam_lim else 0.0
    M = M_Ed + N * ei / 1000 + M2
    MR = MRd_N(N, As(dia, s), d)
    return dict(N=N, M=M, M2=M2, MRd=MR, utn=M / MR, lam=lam, lam_lim=lam_lim, metod="armerad")


# ------------------------------------------------------------------ fogar
C_FOG, MY_FOG = 0.4, 0.7             # råa fogar (uppruggade), 6.2.5(2)


def fog(V, sigma_n, As_tv, fctd, fcd):
    """Skjuvning i en gjutfog [MPa], 6.2.5: v_Rdi = c f_ctd + μ σ_n + ρ f_yd μ ≤ 0,5 ν f_cd (järn vinkelräta)."""
    v = V * 1e3 / (I.T_KARNA * 1000)
    rho = As_tv / (I.T_KARNA * 1000)
    nu = 0.6 * (1 - fcd * GC / 250)
    vr = min(C_FOG * fctd + MY_FOG * sigma_n + rho * FYD * MY_FOG, 0.5 * nu * fcd)
    return dict(v=v, vr=vr, utn=v / vr)


# ------------------------------------------------------------------ LD4_2 i hörnet V2/V20
def hornlast(F=44.0, xy=(4420.0, 10970.0), post=(225.0, 95.0)):
    """Punktlasten LD4_2 [kN, dimensionerande] står utanför kärnornas hörn. Plattan (C25/30, d = 120 mm) för den med
    en tryckstrimla in i kärnan (a_v < 2d): tvärkraft längs kärnornas ytor med 6.2.2(6) och dragband i överkant."""
    geo = {f"V{i}": w for i, w in enumerate(I.G05["vagg"], 1)}
    cx, cy = geo["V20"][1], geo["V2"][1]
    ax_ = abs(cx - xy[0]) - I.T_KARNA / 2               # avstånd till kärnans yta
    ay_ = abs(xy[1] - cy) - I.T_KARNA / 2
    av = max(ax_, ay_)
    d = I.H_MB - 25 - 8 * 1.5
    fck, fcd = 25.0, 25.0 / GC
    u = 2 * (max(post) + 2 * av)                        # längs båda kärnornas ytor
    beta = max(av, 0.5 * d) / (2 * d)
    nu = 0.6 * (1 - fck / 250)
    VRdmax = 0.5 * u * d * nu * fcd / 1e3
    k = min(1 + math.sqrt(200 / d), 2.0)
    rho = As(8, 150) / (1000 * d)
    vRdc = max(0.18 / GC * k * (100 * rho * fck) ** (1 / 3), 0.035 * k ** 1.5 * math.sqrt(fck))
    VRdc = vRdc * u * d / 1e3
    z = 0.9 * d
    T = F * av / z                                       # kN
    TRd = As(8, 150) * u / 1000 * FYD / 1e3
    return dict(F=F, av=av, ax=ax_, ay=ay_, d=d, u=u, beta=beta, VRdmax=VRdmax, VRdc=VRdc, utn_max=F / VRdmax,
                utn_c=beta * F / VRdc, T=T, TRd=TRd, utn_T=T / TRd)


# ------------------------------------------------------------------ brottlinjeteori (byggskedet)
def brottlinje(L, Hv, p, mh, mh_v, mh_h, mv, ande, n=120, topp_fri=False):
    """Minsta lastfaktor λ = W_i / W_e över brottlinjemönstret med diagonaler från hörnen till (a, y0), (L−a, y0).
    Hv: väggens höjd. mh: positivt vågrätt moment, mh_v/mh_h: negativt moment vid vänster/höger kant (0 om ledad
    eller fri), mv: positivt lodrätt moment. ande: ("h"|"f", "h"|"f"). Botten och topp är ledat upplagda.
    topp_fri: överkanten är fri. För y0 < Hv förskjuts delen ovanför den vågräta brottlinjen vid y0 utan att vrida
    sig; för y0 ≥ Hv vrider sig den nedre delen kring botten utan vågrät brottlinje, och bara diagonalerna
    (projicerade på den vågräta axeln) ger inre arbete i den riktningen."""
    xs = (np.arange(n) + 0.5) / n * L
    ys = (np.arange(n) + 0.5) / n * Hv
    X, Y = np.meshgrid(xs, ys)
    P = p(X, Y)
    dA = (L / n) * (Hv / n)
    if P.sum() <= 0:
        return math.inf, None
    best = (math.inf, None)
    y0s = np.linspace(0.04, 0.96, 24) * Hv
    if topp_fri:
        y0s = np.r_[y0s, np.linspace(1.0, 6.0, 26) * Hv]
    sidor = (ande[0] == "h") + (ande[1] == "h")
    for a in np.r_[np.linspace(0.04, 1.0, 25) * L, [1.5 * L, 3 * L, 10 * L, 100 * L]]:
        if ande[0] != "h" and ande[1] != "h" and a > L:
            continue
        for y0 in y0s:
            if not topp_fri:
                plan = [Y / y0, (Hv - Y) / (Hv - y0)]
                Wi = mv * L * (1 / y0 + 1 / (Hv - y0))
            elif y0 < Hv:
                plan = [Y / y0, np.ones_like(Y)]
                Wi = mv * L / y0
            else:
                plan = [Y / y0]
                Wi = mv * min(L, sidor * a * Hv / y0) / y0
            if ande[0] == "h":
                plan.append(X / a); Wi += (mh + mh_v) * Hv / a
            if ande[1] == "h":
                plan.append((L - X) / a); Wi += (mh + mh_h) * Hv / a
            d = np.minimum.reduce(plan)
            We = (P * d).sum() * dA
            if We > 0 and Wi / We < best[0]:
                best = (Wi / We, (float(a), float(y0)))
    return best


# ------------------------------------------------------------------ byggskedet: V3 och V20 innan bjälklaget
BYGG_HOR = {"V3": (10, 300), "V20": (10, 600)}       # vågräta järn i båda ytorna under återfyllningen
L_VINKEL = 750.0                                       # vinkeljärnens ben i hörnen (TG 2216)


def bygg_v(v, t, s=0.25, lodrat=None):
    """V3/V20 med fri överkant (gjutna till H_GJUT1) och fyllning till H_FYLL_MARK vid ålder t: λ, spänning och
    förankring i hörnen, tvärkraft."""
    Hv = I.H_GJUT1 / 1000
    hf = max(v["fyll"])
    g, q = ytlast(v, bygg=True)
    fck = fck_t(t, s=s)
    dh, sh = BYGG_HOR[v["namn"]]
    dv, sv_ = lodrat
    mh = MRd(As(dh, sh), D_H_IN, fck)
    mhn = MRd(As(dh, sh), D_H_UT, fck)
    mv = MRd(As(dv, sv_), d_lodrat(dv), fck)
    lam = math.inf
    for gG, gQ in ULS_JORD.values():
        pf = tryck_fn(hf, g, q, gG, gQ)
        l, _ = brottlinje(v["L"], Hv, lambda X, Y: pf(Y), mh, mhn, mhn, mv, ("h", "h"), n=80, topp_fri=True)
        lam = min(lam, l)
    sig = FYD / min(lam, 10.0) if lam < 10 else FYD / 10
    lb = dh / 4 * sig / fbd(fctm_t(t, s=s), eta1=0.7)
    sk = strimla(hf, g, q)
    vr = VRdc(As(dv, sv_), d_lodrat(dv), fck)
    return dict(t=t, fck=fck, lam=lam, sig=sig, lb=lb, l0=L_VINKEL / 1.5, utn_lb=lb / (L_VINKEL / 1.5),
                V=max(sk["Rb"], sk["Rt"]), VRd=vr, utn_V=max(sk["Rb"], sk["Rt"]) / vr, mh=mh, mhn=mhn, mv=mv)


def bygg_ovriga(dim, arm, t, s=0.25):
    """Övriga väggar när bjälklaget har gjutits: väggens och bjälklagets betong vid ålder t (det översta skiftet
    gjuts med bjälklaget). Böjning och tvärkraft med jordtrycket, skarven mellan vinkeljärnen och de lodräta
    järnen (500 mm, lodräta järn, god vidhäftning) och gjutfogen vid H_GJUT1."""
    fck = fck_t(t, s=s)
    dia, sp = arm
    A = As(dia, sp)
    d = d_lodrat(dia)
    M = dim["Mjord"]
    MR = MRd(A, d, fck)
    V = max(dim["Rb"], dim["Rt"])
    VR = VRdc(A, d, fck)
    # skarven i toppen: vinkeljärnets lodräta ben (I.VINKEL["ned"] från benet under överkantsnätet) mot väggens
    # lodräta järn; momentet där skarven börjar, utan toppmomentet
    sk = strimla(dim["hf"], *dim["_ytlast"], 0.0)
    y_sk = (I.H_VAGG + I.H_MB - 46 - I.VINKEL["ned"]) / 1000
    Msk = float(np.interp(y_sk, sk["ys"], sk["Mlinje"]))
    sig = Msk * 1e6 / (A * 0.9 * d)
    lb = dia / 4 * sig / fbd(fctm_t(t, s=s), eta1=1.0)
    fctd = 0.7 * fctm_t(t, s=s) / GC
    f18 = fog(dim["V18"], 0.0, A, fctd, fck / GC)
    return dict(t=t, fck=fck, utn_M=M / MR, utn_V=V / VR, utn_lb=lb / (I.VINKEL["ned"] / 1.5), utn_fog=f18["utn"], sig=sig)


def tid(krav, s=0.25, t0=3.0):
    """Minsta mognadsålder [dygn vid 20 °C] då krav(t, s) ≤ 1 (bisektion, minst t0 = 3 dygn, 3.1.2(5))."""
    if krav(t0, s) <= 1.0:
        return t0
    lo, hi = t0, 28.0
    if krav(hi, s) > 1.0:
        return math.inf
    for _ in range(40):
        m = 0.5 * (lo + hi)
        lo, hi = (lo, m) if krav(m, s) <= 1.0 else (m, hi)
    return hi


TEMP = (5.0, 10.0, 15.0, 20.0)
CEM = {"N": 0.25, "R": 0.20}


def dagar(t_eq, T):
    """Kalenderdygn vid medeltemperaturen T för mognadsåldern t_eq."""
    return t_eq / mognad(T)


def tid_hallfasthet(f_mal, s=0.25):
    """Mognadsålder då f_ck(t) når f_mal."""
    return tid(lambda t, s_: f_mal / max(fck_t(t, s=s_), 1e-9), s, t0=0.5)


# ------------------------------------------------------------------ tabell
def tabell():
    rows = []
    alla = vaggar()
    for v in alla:
        r = dict(namn=v["namn"], L=v["L"], fyll=v["fyll"], ande=v["ande"], typ=v["typ"], platta=v["platta"],
                 ax=v["ax"], c=v["c"], a=v["a"], b=v["b"], fasad=v["fasad"])
        if max(v["fyll"]) > 0:
            dim = dimensionera(v)
            dim["_ytlast"] = ytlast(v)
            r["dim"] = {k: x for k, x in dim.items() if not k.startswith("_")}
            r["_dim"] = dim
        rows.append(r)
    fyllda = [r for r in rows if "dim" in r]
    # lodräta järn per vägg: den glesaste armering i I.ARM_V som räcker, minst TG 2216:s Ø10 s300 (I.ARM_V[0]); i
    # ytterväggar utan fyllning TG 2216:s; i fasaden med öppningarna pelarna var för sig. arm: den tätaste, som
    # byggskedet räknas med.
    arm = max((valj_lodrat(r["dim"]["M"]) for r in fyllda), key=lambda a: As(*a))
    arm_vagg = {r["namn"]: (valj_lodrat(r["dim"]["M"]) if "dim" in r else tuple(I.ARM_V[0]))
                for r in rows if r["typ"] == "yttre" and not r["fasad"]}
    for r in fyllda:
        dm = r["dim"]
        dia, s = arm_vagg.get(r["namn"], tuple(I.ARM_V[0]))
        d = d_lodrat(dia)
        dm.update(arm=(dia, s), MRd=MRd(As(dia, s), d), VRd=VRdc(As(dia, s), d), d=d,
                  arm_min=valj_lodrat(dm["M"]))
        dm["utn_M"] = dm["M"] / dm["MRd"]
        dm["utn_V"] = max(dm["Rb"], dm["Rt"]) / dm["VRd"]
        # fogen mot bottenplattan: startjärnen, väggens egentyngd som normalkraft (gynnsam, γ = 1,0)
        sig_n = I.G_KUB * H / (I.T_KARNA / 1000) / 1000                       # MPa
        dm["fog_botten"] = fog(dm["Rb"], sig_n, As(I.STARTJARN["d"], I.STARTJARN["s"]), 0.7 * 2.6 / GC, 25 / GC)
        if r["fasad"]:
            v = next(x for x in alla if x["namn"] == r["namn"])
            v.update(M_Ed=dm["M"])
            r["fasad_d"] = fasad(v, dm["M"])
            for p in r["fasad_d"]["pelare"]:
                p["arm"] = valj_lodrat(p["M"])
                p["MRd"] = MRd(As(*p["arm"]), d_lodrat(p["arm"][0]))
                p["utn"] = p["M"] / p["MRd"]
                arm_vagg[p["namn"]] = p["arm"]
    for r in rows:
        if r["namn"] in VAGG05:
            v = dict(namn=r["namn"], typ=r["typ"], M_Ed=r.get("dim", {}).get("M", 0.0))
            r["vert"] = vertikal(v, arm_vagg.get(r["namn"], arm))
            if r["namn"] in arm_vagg:
                r["arm"] = list(arm_vagg[r["namn"]])
    return rows, arm


def byggskede(rows, arm):
    """Hållfasthet och härdningstid: V3/V20 innan bjälklaget, övriga väggar efter bjälklaget."""
    out = dict(A=dict(vaggar={}), B={})
    vv = {v["namn"]: v for v in vaggar()}
    for n in ("V3", "V20"):
        v = vv[n]
        f28 = bygg_v(v, 28.0, lodrat=arm)
        krav_lam = lambda t, s, v=v: 1.0 / bygg_v(v, t, s, lodrat=arm)["lam"]
        krav_lb = lambda t, s, v=v: bygg_v(v, t, s, lodrat=arm)["utn_lb"]
        krav_V = lambda t, s, v=v: bygg_v(v, t, s, lodrat=arm)["utn_V"]
        out["A"]["vaggar"][n] = dict(f28=f28, krav={k: {c: tid(f, s) for c, s in CEM.items()}
                                           for k, f in (("lam", krav_lam), ("forankring", krav_lb), ("V", krav_V))})
    # övriga väggar: den mest belastade (största jordtrycksmoment)
    r = max((r for r in rows if "dim" in r and not r["platta"]), key=lambda r: r["dim"]["Mjord"])
    dim = r["_dim"]
    f28 = bygg_ovriga(dim, arm, 28.0)
    krav = {k: {c: tid(lambda t, s, k=k: bygg_ovriga(dim, arm, t, s)[k], s) for c, s in CEM.items()}
            for k in ("utn_M", "utn_V", "utn_lb", "utn_fog")}
    out["B"] = dict(vagg=r["namn"], f28=f28, krav=krav)
    # krav på hållfastheten: f_ck vid den styrande mognadsåldern (samma för N och R, eftersom kraven gäller f_ck och
    # f_ctm, som båda följer β_cc(t)); regeln avrundas uppåt till 5 MPa och gäller all återfyllning
    tA = max(max(x["krav"][k]["N"] for k in x["krav"]) for x in out["A"]["vaggar"].values())
    tB = max(out["B"]["krav"][k]["N"] for k in out["B"]["krav"])
    out["A"]["fck"], out["B"]["fck"] = fck_t(tA), fck_t(tB)
    regel = 5 * math.ceil(max(out["A"]["fck"], out["B"]["fck"]) / 5 - 1e-9)
    out["regel"] = dict(fck=regel, fcm=regel + 8, andel=regel / I.FCK_V,
                        t_eq={c: tid_hallfasthet(regel, s) for c, s in CEM.items()})
    out["regel"]["dygn"] = {c: {T: max(3.0, dagar(out["regel"]["t_eq"][c], T)) for T in TEMP} for c in CEM}
    # frysning: minst 5 MPa innan betongen får frysa
    out["frys"] = {c: {T: dagar(tid_hallfasthet(5.0, s), T) for T in TEMP} for c, s in CEM.items()}
    return out


if __name__ == "__main__":
    print(f"K0 = {I.K0:.3f}, Ka = {I.KA:.3f}, packningstryck {I.SIG_KOMP:.1f} kPa (P = {I.P_PLATTA:.1f} kN/m)")
    rows, arm = tabell()
    print(f"lodrät armering på insidan: Ø{arm[0]} s{arm[1]}")
    for r in rows:
        t = f"{r['namn']:8s} L {r['L']:5.2f} fyll {r['fyll']}"
        if "dim" in r:
            d = r["dim"]
            t += (f" M {d['M']:5.1f} (jord {d['Mjord']:4.1f}, topp {d['M_topp']:3.1f}) / {d['MRd']:4.1f} = "
                  f"{d['utn_M']:.2f}  V {max(d['Rb'], d['Rt']):4.1f}/{d['VRd']:4.1f}  min Ø{d['arm_min'][0]}s"
                  f"{d['arm_min'][1]}  fog {d['fog_botten']['utn']:.2f}")
        if "vert" in r:
            t += f"  N {r['vert']['N']:5.1f} utn {r['vert']['utn']:.2f}"
        print(t)
        if "fasad_d" in r:
            print("   ", {p["namn"]: round(p["M"], 1) for p in r["fasad_d"]["pelare"]}, r["fasad_d"]["M_brostning"])
    print("hörnlast", {k: round(v, 2) for k, v in hornlast().items()})
    b = byggskede(rows, arm)
    for n, x in b["A"]["vaggar"].items():
        print(n, "λ28", round(x["f28"]["lam"], 2), "krav", x["krav"])
    print("B", b["B"]["vagg"], b["B"]["krav"])
    print("krav fck: A %.1f B %.1f, regel %s" % (b["A"]["fck"], b["B"]["fck"], b["regel"]), "\nfrys", b["frys"])
