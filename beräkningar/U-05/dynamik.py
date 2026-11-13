"""
U-05: timsimulering av ett år (eller flera) med tre tillstånd: rummet på plan 1 (luften och de lätta delarna),
mellanbjälklaget (betongen med golvvärmens plan) och källaren (luften och bottenplattans betong).

Konduktanserna mellan noderna och ute/mark är byggnadsmodellens (byggnad.py); infiltrationen och luftutbytet i
trapphålet räknas om varje timme. Marken (3D-modellens markyta) får en trög temperatur: årsmedlet plus månadens
avvikelse, dämpad och fördröjd enligt den periodiska metoden i SS-EN ISO 13370 (bilaga).

Huset kan användas bara under helgerna (drift.narvaro): när det står tomt går frånluften ned och internlasten är bara
grundlasten.

Golvvärmen styrs mot börvärdet i rummet några timmar framåt (styrhorisonten): varje timme ges den konstanta värme som
skulle ge börvärdet efter horisonten, aldrig negativ och högst värmepumpens effekt. Det liknar en verklig reglering av
en trög golvvärme; rummet kan en stund bli något kallare eller varmare än börvärdet. Blir rummet varmare än
vädringsgränsen vädras det (värmen förs bort gratis). Implicit Euler, en timme per steg.
"""
from __future__ import annotations

import math

import numpy as np

import byggnad as B
import klimat as KL
import komponenter as KO

NOD = ("inne", "varme", "kallare")


def kapaciteter(P, ar):
    """Nodernas värmekapacitet [J/K]."""
    M = P["material"]
    D = P["dynamik"]
    A1 = ar["Atemp_plan1"]
    Ak = ar["Atemp_kallare"]
    V1 = A1 * D["rumshojd_plan1"]
    from shapely.geometry import Polygon
    A_mb = Polygon(P["_kontur"]).area - Polygon(P["_trapphal"]).area
    C_i = 1200 * V1 + D["lattvikt_kJ_m2K"] * 1000 * A1
    C_h = M["betong"]["rc"] * 1e6 * P["bjalklag"]["h"] / 1000 * A_mb
    C_b = 1200 * Ak * 2.1 + D["lattvikt_kallare_kJ_m2K"] * 1000 * Ak + \
        M["betong"]["rc"] * 1e6 * P["bottenplatta"]["betong"] / 1000 * Ak
    return dict(inne=C_i, varme=C_h, kallare=C_b)


def markens_temperatur(P, K, Hg_iso):
    """Markytans tröga temperatur: årsmedel + η · (30 dygns medel, fördröjt) − årsmedel. η = H_pe/H_g ur SS-EN ISO
    13370 för källaren, fördröjningen i månader 1,5 − 0,42 ln(δ/(d_t + 1))."""
    T = K["T"]
    Tm = float(T.mean())
    eta, lag_man = Hg_iso["eta"], Hg_iso["lag"]
    n = 30 * 24
    kum = np.cumsum(np.r_[np.full(n, T[:n].mean()), T])
    glid = (kum[n:] - kum[:-n]) / n
    lag = int(round(lag_man * 730))
    glid_f = np.r_[np.full(lag, glid[0]), glid[:-lag] if lag else glid]
    return Tm + eta * (glid_f - Tm), Tm


def iso13370_period(P, ar, lam=2.0, rc=2.0e6):
    """Dämpningen (H_pe/H_g) och fördröjningen för källaren enligt SS-EN ISO 13370:s periodiska metod (bilaga)."""
    from mark3d import kallarens_kontur
    from shapely.geometry import Polygon
    p = Polygon(kallarens_kontur())
    A, Pm = p.area, p.length
    Bp = A / (0.5 * Pm)
    Rf = 0.1 / 1.7 + 0.3 / 0.038
    Rw = 0.1 / 0.036 + 0.15 / 1.7 + 0.1 / 0.038
    z = 1.0
    dt = 0.35 + lam * (0.17 + Rf + 0.04)
    dw = lam * (0.13 + Rw + 0.04)
    delta = math.sqrt(3.15e7 * lam / (math.pi * rc))
    from tester import iso13370_kallare
    Hg = iso13370_kallare(lam, math.sqrt(A), math.sqrt(A), z, Rf, Rw, 0.35)[0]
    Hpe = 0.37 * Pm * lam * (math.exp(-z / delta) * math.log(delta / dt + 1) +
                             2 * (1 - math.exp(-z / delta)) * math.log(delta / dw + 1))
    lag = 1.5 - 0.42 * math.log(delta / (dt + 1))
    return dict(eta=Hpe / Hg, lag=lag, delta=delta, B=Bp, dt=dt, dw=dw, Hg=Hg, Hpe=Hpe)


def sol(P, K):
    """Solvärmen genom fönstren [W] per timme: till plan 1 och till källaren."""
    D = P["drift"]
    V = P["velfac"]
    lage = {v["kod"]: v for v in P["mangder"]["lage"]}
    F = D["solavskarmning"] * P["dynamik"]["skuggning"]
    q1 = np.zeros(len(K["T"]))
    qk = np.zeros(len(K["T"]))
    cache = {}
    for kod, typ, b, h, van, vagg in P["oppningar"]["lista"]:
        f = KO.fonster(P, typ, b, h)
        if f["Ag"] <= 0:
            continue
        u = lage[vagg]["u"]
        az = KL.azimut(P, u[1], -u[0])               # utåtriktad normal (u_y, −u_x)
        if az not in cache:
            dir_, dif, ct = KL.instralning(K, az, 90.0, P["klimat"]["markreflektion"])
            cache[az] = dir_ * KL.iam(ct) + dif * 0.85
        q = cache[az] * f["Ag"] * V["g"] * F
        if van == 1:
            q1 += q
        else:
            qk += q
    TF = P["takfonster"]
    for tf in TF["takfall"]:
        az = KL.azimut(P, -1, 0) if tf.endswith("SO") else KL.azimut(P, 1, 0)
        dir_, dif, ct = KL.instralning(K, az, 30.0, P["klimat"]["markreflektion"])
        Ag = (TF["b"] - 2 * 80) * (TF["h"] - 2 * 80) / 1e6
        q1 += (dir_ * KL.iam(ct) + dif * 0.85) * Ag * TF["g"] * F
    return q1, qk


def narvaro(P, K):
    """Om någon är hemma, per timme: alltid (BEN) eller helgerna (drift.helg: från och till, veckodag med måndag 0
    och timme i svensk normaltid; vädret är i UTC)."""
    D = P["drift"]
    n = len(K["T"])
    if D["narvaro"] == "alltid":
        return np.ones(n, bool)
    h = np.asarray(K["tid"]).astype("datetime64[h]").astype(np.int64) + 1          # UTC+1
    vecka = ((h // 24 + 3) % 7) * 24 + h % 24                                        # 1970-01-01 var en torsdag
    (d0, t0), (d1, t1) = D["helg"]
    return (vecka >= d0 * 24 + t0) & (vecka < d1 * 24 + t1)


def franluft(P, ar, hemma):
    """Frånluften [l/s] per timme och källarens del (FF3): grundflödena med köksfläktens forcering som medel över
    dygnet när någon är hemma, annars alla fläktar ned i samma proportion till tomt_flode per m² Atemp."""
    V = P["ventilation"]
    q0 = V["FF1"] + V["FF2"] + V["FF3"]
    forc = (V["FF1_forcerad"] - V["FF1"]) * V["forcering_min"] / (24 * 60)
    s = min(1.0, V["tomt_flode"] * ar["Atemp"] / q0) if V["tomt_sank"] else 1.0
    return np.where(hemma, q0 + forc, q0 * s), np.where(hemma, V["FF3"], V["FF3"] * s)


def interna(P, ar, hemma):
    """Internlasten [W] per timme, till plan 1 och källaren (fördelad på Atemp): när någon är hemma BEN:s medel över
    dygnet (hushållsel × andel och personvärme), annars grundlasten (kyl, frys och standby)."""
    D = P["drift"]
    Atemp = ar["Atemp"]
    q = D["hushallsel"] * D["hushallsel_internlast"] * Atemp * 1000 / 8760 + \
        D["personer"] * D["person_W"] * D["person_h"] / 24
    qt = np.where(hemma, q, D["grundlast_W"])
    a1 = ar["Atemp_plan1"] / Atemp
    return qt * a1, qt * (1 - a1)


def simulera(P, E, K, ar, ftx=0.0, konstant=None, T_mark_fast=None):
    """Timsimuleringen. konstant: dict med T_e (och utan sol och internlast) för en kontroll mot stationärt.
    Returnerar timserier och årssummor."""
    n = len(K["T"])
    T_e = K["T"].copy()
    vind = K["U10"].copy()
    q_sol1, q_solk = sol(P, K)
    if P.get("_fall", {}).get("utan_sol"):            # jämförelse: solens nytta
        q_sol1, q_solk = np.zeros_like(q_sol1), np.zeros_like(q_solk)
    hemma = narvaro(P, K) if konstant is None else np.ones(n, bool)
    qi1, qik = interna(P, ar, hemma)
    q_fr_t, q_ff3_t = franluft(P, ar, hemma)
    iso = iso13370_period(P, ar)
    T_m, T_ann = markens_temperatur(P, K, iso)
    if konstant is not None:
        T_e[:] = konstant["T_e"]
        T_m = np.full(n, konstant.get("T_mark", konstant["T_e"]))
        vind[:] = konstant.get("vind", 4.0)
        q_sol1[:] = q_solk[:] = qi1[:] = qik[:] = 0.0
    if T_mark_fast is not None:
        T_m = np.full(n, T_mark_fast)
    G = B.matris(E)
    O = B.OMG
    ii, ih, ib, ie, im = (O.index(x) for x in ("inne", "varme", "kallare", "ute", "mark"))
    C = kapaciteter(P, ar)
    Cv = np.array([C["inne"], C["varme"], C["kallare"]])
    dt = 3600.0
    D = P["drift"]
    Qmax = P["dynamik"]["P_max"] * 1000
    T_set = D["T_inne"]
    T_vad = D["T_vadring"]
    x = np.array([T_set, T_set + 4.0, T_set])
    ut = {k: np.zeros(n) for k in ("Q_h", "T_i", "T_h", "T_b", "vadring", "H_vent", "H_inf", "H_tr", "H_ff3")}
    # konstanta delar av systemmatrisen
    Gs = np.array([[0.0, G[ii, ih], G[ii, ib]],
                   [G[ih, ii], 0.0, G[ih, ib]],
                   [G[ib, ii], G[ib, ih], 0.0]])
    Ge = np.array([G[ii, ie], G[ih, ie], G[ib, ie]])
    Gm = np.array([G[ii, im], G[ih, im], G[ib, im]])
    sol_golv = P["dynamik"]["sol_till_golv"]
    N_hor = int(P["dynamik"]["styr_horisont_h"])
    for t in range(n):
        q_fr = q_fr_t[t]
        H_ff3 = B.RHO_C * q_ff3_t[t] / 1000
        q_inf = B.infiltration(P, x[0] - T_e[t], vind[t])
        q_tot = math.sqrt(q_fr ** 2 + q_inf ** 2)
        H_v = B.RHO_C * (q_fr * (1 - ftx) + (q_tot - q_fr)) / 1000
        H_tr = B.RHO_C * B.trapputbyte(P, x[2], x[0]) / 1000
        K_ = -Gs.copy()
        K_[0, 2] -= H_tr
        K_[2, 0] -= H_tr + H_ff3                     # källaren får luften från plan 1 (FF3)
        diag = Gs.sum(axis=1) + Ge + Gm
        diag[0] += H_v + H_tr
        diag[2] += H_tr + H_ff3
        K_[np.diag_indices(3)] = diag
        b = Ge * T_e[t] + Gm * T_m[t]
        b[0] += H_v * T_e[t] + qi1[t] + (1 - sol_golv) * q_sol1[t]
        b[1] += sol_golv * q_sol1[t]
        b[2] += qik[t] + q_solk[t]
        A = K_ + np.diag(Cv / dt)
        Ai = np.linalg.inv(A)
        Mx = Ai * (Cv / dt)[None, :]                # x_{n+1} = Mx x_n + Ai (b + e_h Q)
        # golvvärmens styrning: den konstanta värme som ger 21 °C i rummet om N timmar (med dagens
        # förutsättningar), tillämpad den här timmen; ett ögonblicksvärde skulle ge orimliga toppar genom
        # bjälklagets tröghet
        xa, xs = x.copy(), np.zeros(3)
        ab, ah = Ai @ b, Ai[:, 1]
        for _ in range(N_hor):
            xa = Mx @ xa + ab
            xs = Mx @ xs + ah
        Q = (T_set - xa[0]) / xs[0]
        Q = min(max(Q, 0.0), Qmax)
        xn = Mx @ x + ab + ah * Q
        vad = 0.0
        if xn[0] > T_vad and T_e[t] < xn[0]:
            s0 = Ai[:, 0]
            vad = (xn[0] - T_vad) / s0[0]
            xn = xn - vad * s0
        x = xn
        ut["Q_h"][t], ut["vadring"][t] = Q, vad
        ut["T_i"][t], ut["T_h"][t], ut["T_b"][t] = x
        ut["H_vent"][t] = B.RHO_C * q_fr * (1 - ftx) / 1000
        ut["H_inf"][t] = B.RHO_C * (q_tot - q_fr) / 1000
        ut["H_tr"][t] = H_tr
        ut["H_ff3"][t] = H_ff3
    ut["T_e"], ut["T_mark"], ut["sol1"], ut["solk"] = T_e, T_m, q_sol1, q_solk
    ut["int1"], ut["intk"] = qi1, qik
    ut["hemma"], ut["q_fr"] = hemma, q_fr_t
    ut["iso13370"] = iso
    ut["T_ann"] = T_ann
    return ut


def arsforluster(P, E, sim, K):
    """Förlusterna till ute och mark per kategori och år [kWh], ur timserierna."""
    T = {"inne": sim["T_i"], "varme": sim["T_h"], "kallare": sim["T_b"], "ute": sim["T_e"], "mark": sim["T_mark"]}
    ar = K["ar"]
    ut = {}
    for e in E:
        if (e.a in ("ute", "mark")) == (e.b in ("ute", "mark")):
            continue
        a, b = (e.a, e.b) if e.b in ("ute", "mark") else (e.b, e.a)
        q = e.H * (T[a] - T[b])
        ut.setdefault(e.kategori, np.zeros(len(q)))
        ut[e.kategori] += q
    ut["Ventilation"] = sim["H_vent"] * (sim["T_i"] - sim["T_e"]) + sim["H_ff3"] * (sim["T_b"] - sim["T_i"])
    ut["Infiltration"] = sim["H_inf"] * (sim["T_i"] - sim["T_e"])
    per_ar = {}
    for k, q in ut.items():
        per_ar[k] = {int(a): float(q[ar == a].sum() / 1000) for a in np.unique(ar)}
    return per_ar
