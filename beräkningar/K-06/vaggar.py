"""
K-06: källarväggar av isolerade lättklinkerblock mot jordtryck, SS-EN 1996-1-1 med EKS 12.

Väggen bärs i botten av bottenplattan, i toppen av mellanbjälklaget och på sidorna av hörn (armeringen förs runt
hörnet) eller stolpar. Bärförmågan mot jordtryck beräknas med brottlinjeteori (SS-EN 1996-1-1 5.5.5 och 6.6.2,
Leca Teknisk håndbok 7.4.4): horisontellt böjmoment från armeringen i liggfogarna, vertikalt från murverkets
böjdraghållfasthet och väggens egen normalkraft. Lasten är vilojordtryck (triangulärt) plus last på marken.

    python vaggar.py      -> tabell per vägg och system
"""
import json
import math
import os

import numpy as np

import indata as I

HERE = os.path.dirname(os.path.abspath(__file__))
R05 = json.load(open(os.path.join(I.K05, "resultat.json"), encoding="utf-8"))
VAGG05 = {v["namn"]: v for v in R05["vaggar"]}


def q06(namn):
    """Väggens last per meter i den samverkande modellen (kontroll06.json, största av L300 och L400), annars 0."""
    f = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kontroll06.json")
    if not os.path.exists(f):
        return 0.0
    return max((v["q"] for u in json.load(open(f, encoding="utf-8")).values() for v in u["vaggar"]
                if v["namn"] == namn), default=0.0)
GD = 0.91
# ULS: (γ för jordtryck och permanent ytlast, γ för nyttig last på marken)
ULS_JORD = {"6.10a": (GD * 1.35, GD * 1.5 * 0.7), "6.10b": (GD * 1.2, GD * 1.5)}
H = I.H_VAGG / 1000      # m


# ------------------------------------------------------------------ geometri
def vaggar():
    """Väggarna från K-05 med längd, ändar och fyllning, och fasaden med öppningarna (fri överkant) som en vägg
    mellan sina hörn."""
    out = []
    for i, (ax, c, a, b, typ, cs) in enumerate(I.G05["vagg"], 1):
        n = f"V{i}"
        f = I.FYLL.get(n, dict(h=(0.0, 0.0), ande=("h", "h")))
        out.append(dict(namn=n, ax=ax, c=c, a=a, b=b, typ=typ, L=(b - a) / 1000, fyll=f["h"], ande=f["ande"],
                        platta=f.get("platta", False), topp_fri=False))
    vagg = {v["namn"]: v for v in out}
    for n, f in I.FYLL.items():
        if "fasad" in f:
            lin, (v1, v2) = vagg[f["fasad"]["linje"]], (vagg[x] for x in f["fasad"]["mellan"])
            a, b = sorted((v1["c"], v2["c"]))
            out.append(dict(namn=n, ax=lin["ax"], c=lin["c"], a=a, b=b, typ="yttre", L=(b - a) / 1000, fyll=f["h"],
                            ande=f["ande"], platta=False, topp_fri=True))
    return out


# ------------------------------------------------------------------ last
def tryck(v, komb, x0=0.0, x1=None):
    """Dimensionerande jordtryck p(x, y) [kPa] på väggdelen x0..x1 (m från ände a), y uppåt från bottenplattan."""
    gG, gQ = ULS_JORD[komb]
    L = v["L"]
    x1 = L if x1 is None else x1
    ha, hb = v["fyll"]

    def p(X, Y):
        hf = ha + (hb - ha) * (x0 + X) / L
        jord = I.GAMMA_JORD * np.clip(hf - Y, 0, None)
        yt = gQ * I.Q_MARK * np.ones_like(Y)
        if v["platta"]:
            yt = yt + gG * I.G_MARK + gQ * I.Q_MARK_PLATTA
        return np.where(Y < hf, I.K0 * (gG * jord + yt), 0.0)
    return p


def tryck_k(v, x):
    """Karakteristiskt jordtryck vid botten [kPa] och resultant [kN/m] i läget x (m från ände a)."""
    ha, hb = v["fyll"]
    hf = ha + (hb - ha) * x / v["L"]
    q = I.Q_MARK + (I.G_MARK + I.Q_MARK_PLATTA if v["platta"] else 0.0)
    return I.K0 * (I.GAMMA_JORD * hf + q), I.K0 * (0.5 * I.GAMMA_JORD * hf ** 2 + q * hf)


# ------------------------------------------------------------------ bärförmåga
def moment_h(sys_, var):
    """Horisontellt moment [kNm/m] (fält och stöd) från armeringen, var = 1 (varje fog) eller 2 (varannan)."""
    S = I.SYSTEM[sys_]
    As = S["As_drag"] / (var * S["skift"]) * 1000          # mm²/m
    fyd = S["fyk"] / I.GAMMA_M_ARM
    fd = S["fk"] / I.GAMMA_M_MUR
    x = As * fyd / (0.8 * fd * 1000)
    z = min(S["d"] - 0.4 * x, 0.95 * S["d"])
    m = As * fyd * z / 1e6
    return (m if S["samverkan"] else 2 * m), dict(As=As, fyd=fyd, z=z, x=x)


def moment_v(sys_, N_inre):
    """Vertikalt moment [kNm/m] för båda vangerna: (f_xd1 + σ_d) t²/6, σ_d av normalkraften vid halva höjden."""
    S = I.SYSTEM[sys_]
    t = I.T_SKIKT
    fxd1 = S["fxk1"] / I.GAMMA_M_MUR
    egen = (S["vikt"] / 2 + I.PUTS / 2) * H / 2           # kN/m per vange vid halva höjden
    m = 0.0
    for N in (N_inre + egen, egen):
        m += (fxd1 + N * 1e3 / (t * 1000)) * t ** 2 / 6 / 1e3
    return m


def brottlinje(L, p, mh, mh_v, mh_h, mv, ande, n=120, topp_fri=False):
    """Minsta lastfaktor λ = W_i / W_e över brottlinjemönstret med diagonaler från hörnen till (a, y0), (L−a, y0).
    mh: positivt horisontellt moment, mh_v/mh_h: negativt moment vid vänster/höger kant (0 om ledad eller fri),
    mv: positivt vertikalt moment. ande: ("h"|"f", "h"|"f"). Botten och topp är ledat upplagda.
    topp_fri: överkanten är fri (bröstning under fönster). För y0 < H förskjuts delen ovanför den vågräta
    brottlinjen vid y0 utan att vrida sig; för y0 ≥ H vrider sig den nedre delen kring botten utan vågrät
    brottlinje, och bara diagonalerna (projicerade på den vågräta axeln) ger inre arbete i den riktningen."""
    xs = (np.arange(n) + 0.5) / n * L
    ys = (np.arange(n) + 0.5) / n * H
    X, Y = np.meshgrid(xs, ys)
    P = p(X, Y)
    dA = (L / n) * (H / n)
    if P.sum() <= 0:
        return math.inf, None
    best = (math.inf, None)
    y0s = np.linspace(0.04, 0.96, 24) * H
    if topp_fri:
        y0s = np.r_[y0s, np.linspace(1.0, 6.0, 26) * H]
    sidor = (ande[0] == "h") + (ande[1] == "h")
    for a in np.r_[np.linspace(0.04, 1.0, 25) * L, [1.5 * L, 3 * L, 10 * L, 100 * L]]:
        if ande[0] != "h" and ande[1] != "h" and a > L:
            continue
        for y0 in y0s:
            if not topp_fri:
                plan = [Y / y0, (H - Y) / (H - y0)]
                Wi = mv * L * (1 / y0 + 1 / (H - y0))
            elif y0 < H:
                plan = [Y / y0, np.ones_like(Y)]
                Wi = mv * L / y0
            else:
                plan = [Y / y0]
                Wi = mv * min(L, sidor * a * H / y0) / y0
            if ande[0] == "h":
                plan.append(X / a); Wi += (mh + mh_v) * H / a
            if ande[1] == "h":
                plan.append((L - X) / a); Wi += (mh + mh_h) * H / a
            d = np.minimum.reduce(plan)
            We = (P * d).sum() * dA
            if We > 0 and Wi / We < best[0]:
                best = (Wi / We, (float(a), float(y0)))
    return best


def kontroll(v, sys_, var, stolpar=0):
    """λ för väggen (eller varje fack mellan stolpar) med system och armering var n:te fog."""
    mh, _ = moment_h(sys_, var)
    w05 = VAGG05.get(v["namn"])
    if w05 is None or v.get("topp_fri", False):
        N = 0.0                                     # bröstning: ingen last från plattan
    else:
        N = 0.75 * max(w05["Gk"] - w05["ovan_G"], 0.0) / (w05["L"] / 1000)     # kN/m, permanent last från plattan
    mv = moment_v(sys_, N)
    n = stolpar + 1
    Lf = v["L"] / n
    res = []
    for k in range(n):
        x0 = k * Lf
        ande = (v["ande"][0] if k == 0 else "h", v["ande"][1] if k == n - 1 else "h")
        lam = math.inf
        for komb in ULS_JORD:
            p = tryck(v, komb, x0, x0 + Lf)
            l, _ = brottlinje(Lf, p, mh, mh if ande[0] == "h" else 0.0, mh if ande[1] == "h" else 0.0, mv, ande,
                              topp_fri=v.get("topp_fri", False))
            lam = min(lam, l)
        res.append(lam)
    return min(res), dict(mh=mh, mv=mv, N=N, Lf=Lf, lam_fack=res)


def stolpar_som_behovs(v, sys_, var, nmax=6):
    for n in range(nmax + 1):
        lam, d = kontroll(v, sys_, var, n)
        if lam >= 1.0:
            return n, lam, d
    return None, lam, d


# ------------------------------------------------------------------ Lecas förhandsgodkända regel (tabell 7.7a–c)
def leca_regel(v):
    """Största avstånd mellan avstivande väggar enligt Leca Teknisk håndbok tabell 7.7a–c, stein/grus, Isoblokk 35."""
    hf = max(v["fyll"])
    if hf <= 0:
        return None
    if hf <= 2.0:
        return dict(varannan=6.0, varje=6.0, tabell="7.7a")
    if hf <= 2.5:
        return dict(varannan=4.5, varje=5.5, tabell="7.7b")
    if hf <= 2.8:
        return dict(varannan=4.0, varje=5.0, tabell="7.7c")
    return None


# ------------------------------------------------------------------ stolpar (stålrör innanför väggen)
VKR = [(100, 5), (100, 6.3), (120, 5), (120, 6.3), (140, 6.3), (150, 8)]


def vkr_wpl(b, t):
    bi = b - 2 * t
    return (b ** 3 - bi ** 3) / 4 / 1e3       # cm³ (kvadratiskt rör, utan hörnradier)


def stolpe(v, sys_, var, n):
    """Stolpe mellan bottenplatta och bjälklag: last från fackbredden (Lf) med faktorn 1,25 för kontinuitet."""
    Lf = v["L"] / (n + 1)
    best = None
    ys = np.linspace(0, H, 401)
    for komb in ULS_JORD:
        for k in range(n):
            x = (k + 1) * Lf
            p = tryck(v, komb)(np.full_like(ys, x), ys)
            q = 1.25 * Lf * p                                 # kN/m längs stolpen
            Rtop = np.trapezoid(q * ys, ys) / H
            Rbot = np.trapezoid(q, ys) - Rtop
            V = Rbot - np.concatenate([[0], np.cumsum((q[1:] + q[:-1]) / 2 * np.diff(ys))])
            M = np.concatenate([[0], np.cumsum((V[1:] + V[:-1]) / 2 * np.diff(ys))])
            d = dict(komb=komb, x=x, Mmax=float(M.max()), Rtop=float(Rtop), Rbot=float(Rbot))
            if best is None or d["Mmax"] > best["Mmax"]:
                best = d
    for b, t in VKR:
        W = vkr_wpl(b, t)
        if W * 355 / 1e3 >= best["Mmax"]:
            best.update(vkr=(b, t), Wpl=W, MRd=W * 355 / 1e3, utn=best["Mmax"] / (W * 355 / 1e3))
            break
    return best


# ------------------------------------------------------------------ vertikal last (SS-EN 1996-1-1 6.1.2, bilaga G)
def phi_mitt(sys_, emk_t, hef_tef):
    S = I.SYSTEM[sys_]
    lam = hef_tef * math.sqrt(S["fk"] / (1000 * S["fk"]))
    A1 = 1 - 2 * emk_t
    u = (lam - 0.063) / (0.73 - 1.17 * emk_t)
    return A1 * math.exp(-u * u / 2)


SPRID = math.tan(math.radians(30))     # lastspridning 60° mot horisontalplanet (SS-EN 1996-1-1 6.1.3)


def vertikal(v, sys_):
    """Dimensionerande normalkraft per vange [kN/m] mot bärförmågan Φ t f_d. Ytterväggar: hela lasten (det största
    av K-05:s värde över 1 m och den samverkande modellens) på den inre vangen. Innerväggar: lika på båda vangerna. Korta pelare (L < 1 m):
    lasten sprids 60° åt ett håll ned till halva höjden (in i anslutande vägg)."""
    S = I.SYSTEM[sys_]
    w05 = VAGG05[v["namn"]]
    egen = 1.35 * GD * (S["vikt"] / 2 + I.PUTS / 2) * H
    q = max(w05["qd_max"], q06(v["namn"]))
    Ls = w05["L"] / 1000
    if Ls < 1.0:
        q = q * Ls / (Ls + SPRID * H / 2)
    N = q * (1.0 if v["typ"] == "yttre" else 0.5) + egen
    t = I.T_SKIKT
    fd = S["fk"] / I.GAMMA_M_MUR
    hef = 0.75 * I.H_VAGG
    einit = hef / 450
    em = max(einit, 0.05 * t)
    emk = max(em, 0.05 * t)
    Phi_m = phi_mitt(sys_, emk / t, hef / t)
    Phi_i = 1 - 2 * max(0.05 * t, einit) / t
    Phi = min(Phi_m, Phi_i)
    NRd = Phi * t * fd                         # kN/m (N/mm · ... : t[mm]·fd[MPa] = N/mm = kN/m)
    return dict(N=N, NRd=NRd, Phi=Phi, utn=N / NRd, lastvange="inre" if v["typ"] == "yttre" else "båda")


def reaktioner(v):
    """Dimensionerande reaktion mot bjälklaget (topp) och bottenplattan (botten) [kN/m] för en vertikal strimla
    vid största fyllning (övre gräns, väggen räknas som fritt upplagd mellan plattorna). Med fri överkant tar
    bottenplattan hela jordtrycket."""
    ys = np.linspace(0, H, 401)
    best = (0.0, 0.0)
    for komb in ULS_JORD:
        x = v["L"] if v["fyll"][1] >= v["fyll"][0] else 0.0
        p = tryck(v, komb)(np.full_like(ys, x), ys)
        Rt = 0.0 if v.get("topp_fri", False) else np.trapezoid(p * ys, ys) / H
        Rb = np.trapezoid(p, ys) - Rt
        best = (max(best[0], Rt), max(best[1], Rb))
    return best


def tabell():
    rows = []
    for v in vaggar():
        r = dict(namn=v["namn"], L=v["L"], fyll=v["fyll"], ande=v["ande"], typ=v["typ"], platta=v["platta"],
                 ax=v["ax"], c=v["c"], a=v["a"], b=v["b"], topp_fri=v.get("topp_fri", False))
        r["regel"] = leca_regel(v)
        for s in ("A", "B"):
            r[s] = {}
            if v["namn"] in VAGG05:                 # vertikal last: K-05:s väggar (fasaden: pelarna V10–V13)
                r[s]["vert"] = vertikal(v, s)
            if max(v["fyll"]) <= 0:
                continue
            for var in (2, 1):
                n, lam, d = stolpar_som_behovs(v, s, var)
                lam0, d0 = kontroll(v, s, var, 0)
                e = dict(stolpar=n, lam=lam, lam0=lam0, mh=d["mh"], mv=d["mv"], N=d["N"], Lf=d["Lf"])
                if n:
                    e["stolpe"] = stolpe(v, s, var, n)
                r[s][var] = e
        Rb, Rr = tryck_k(v, v["L"] * (1.0 if v["fyll"][1] >= v["fyll"][0] else 0.0))
        r["p_bot_k"], r["Rk"] = Rb, Rr
        if max(v["fyll"]) > 0:
            r["R_topp"], r["R_botten"] = reaktioner(v)
        rows.append(r)
    return rows


if __name__ == "__main__":
    print(f"K0 = {I.K0:.3f}")
    for s in ("A", "B"):
        for var in (2, 1):
            mh, d = moment_h(s, var)
            print(f"system {s}, armering var {var}:e fog: m_h = {mh:.2f} kNm/m  (As {d['As']:.0f} mm²/m, z {d['z']:.0f} mm)")
    for r in tabell():
        txt = f"{r['namn']:4s} L {r['L']:5.2f} fyll {r['fyll']} {r['ande']}"
        for s in ("A", "B"):
            vt = r[s].get("vert") or dict(N=0.0, NRd=float("nan"), utn=0.0)
            txt += f" | {s}: N {vt['N']:5.1f}/{vt['NRd']:5.1f} ({vt['utn']*100:3.0f} %)"
            for var in (2, 1):
                if var in r[s]:
                    e = r[s][var]
                    txt += f" v{var}: λ0 {e['lam0']:.2f} st {e['stolpar']}"
                    if e.get("stolpe"):
                        st = e["stolpe"]
                        txt += f" (VKR {st['vkr']} M {st['Mmax']:.1f})"
        print(txt)
