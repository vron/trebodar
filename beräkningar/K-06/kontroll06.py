"""
K-06: kontroller av bottenplattan, cellplasten och mellanbjälklaget i den samverkande modellen.
Läser res06_<utf>_<variant>.pkl från berakning06.py. Skriver kontroll06.json.
"""
import json
import math
import os
import pickle

import numpy as np
from matplotlib.tri import Triangulation, LinearTriInterpolator

import indata as I
from ec2 import Betong, Stal, MRd, vmin, k_size

HERE = os.path.dirname(os.path.abspath(__file__))
B = Betong(fck=25)
S = Stal()
R05 = json.load(open(os.path.join(I.K05, "resultat.json"), encoding="utf-8"))
F05 = np.load(os.path.join(I.K05, "falt.npz"))
C_UK, C_OK = 30.0, 25.0        # täckskikt mot cellplast (distanser) och i överkant
BAND = 250.0
STANG = [(2, 10), (3, 10), (2, 12), (3, 12), (4, 12), (3, 16), (4, 16)]
NAT = (6, 150)                 # Ø6 s150 i båda lagren i fält (Plattor.pdf)
PLINT_ARM = (8, 150)           # plintarnas underkant, båda riktningarna
URTAG = 50.0                   # urtag i kantbalken under ytterväggen: kantbalkens höjd räknas h − 50
ROR_B, FOT_T, FOT_FY = 80.0, 15.0, 355.0     # rör 80×80, fotplåt 200 × 200 × 15 S355


def fot_beff(fcd):
    """Fotplåtens effektiva bredd, SS-EN 1993-1-8 6.2.5: c = t √(f_y / (3 f_jd)), f_jd = 2 f_cd (ger minst yta)."""
    c = FOT_T * math.sqrt(FOT_FY / (3 * 2 * fcd))
    return min(ROR_B + 2 * c, 200.0)


def _las(namn):
    return pickle.load(open(os.path.join(HERE, namn), "rb"))


def _sla_ihop(a, b):
    """Omhyllande av två körningar med samma nät (grundmodellen och varianten där båda vangarna bär)."""
    m = dict(a)
    env, eb = dict(a["env"]), b["env"]
    for k in ("t_mux", "t_muy", "b_mux", "b_muy", "p_max", "p_perm"):
        env[k] = np.maximum(env[k], eb[k])
    for k in ("t_mox", "t_moy", "b_mox", "b_moy", "p_min"):
        env[k] = np.minimum(env[k], eb[k])
    env["balk"] = [dict(x, Mmax=np.maximum(x["Mmax"], y["Mmax"]), Mmin=np.minimum(x["Mmin"], y["Mmin"]),
                        Vmax=np.maximum(x["Vmax"], y["Vmax"])) for x, y in zip(env["balk"], eb["balk"])]
    env["stans"] = dict(env["stans"], netto=np.maximum(env["stans"]["netto"], eb["stans"]["netto"]),
                        N=np.maximum(env["stans"]["N"], eb["stans"]["N"]))
    env["vagg"] = {k: max(env["vagg"].get(k, -1e9), eb["vagg"].get(k, -1e9)) for k in set(env["vagg"]) | set(eb["vagg"])}
    m["env"] = env
    m["kr"] = dict(max={k: max(v, b["kr"]["max"].get(k, -1e18)) for k, v in a["kr"]["max"].items()},
                   komb=a["kr"]["komb"])
    sls = dict(a["sls"])
    sls["p_qp"] = np.maximum(sls["p_qp"], b["sls"]["p_qp"])
    sls["p_k"] = np.maximum(sls["p_k"], b["sls"]["p_k"])
    m["sls"] = sls
    if a.get("mt_SV") is not None and b.get("mt_SV") is not None:
        m["mt_SV"] = np.where(np.abs(a["mt_SV"]) >= np.abs(b["mt_SV"]), a["mt_SV"], b["mt_SV"])
    return m


def las(utf, var, ytter=True):
    """Grundmodellen, omhyllad med varianten där båda vangarna bär (res06_<utf>_<var>_ytter.pkl) om den finns."""
    a = _las(f"res06_{utf}_{var}.pkl")
    fy = os.path.join(HERE, f"res06_{utf}_{var}_ytter.pkl")
    if ytter and os.path.exists(fy):
        return _sla_ihop(a, _las(os.path.basename(fy)))
    return a


def eps_fd(grad, varaktighet):
    e = I.EPS[grad]
    kr = I.EPS_KR[varaktighet][1 if int(grad[1:]) >= 200 else 0]      # deklarerad hållfasthet (σ10)
    return kr * e["fck"] / I.EPS_GAMMA_M


def utjamna(xy, tri, falt, rikt, Bw=BAND, n=11):
    ip = LinearTriInterpolator(Triangulation(xy[:, 0], xy[:, 1], tri), falt)
    acc = np.zeros(len(xy)); cnt = np.zeros(len(xy))
    for dt in np.linspace(-Bw / 2, Bw / 2, n):
        x = xy[:, 0] + (dt if rikt == "y" else 0); y = xy[:, 1] + (dt if rikt == "x" else 0)
        v = np.ma.filled(ip(x, y), np.nan); ok = ~np.isnan(v)
        acc[ok] += v[ok]; cnt[ok] += 1
    return acc / np.maximum(cnt, 1)


def mrd_nat(dia, cc, d):
    return MRd(math.pi * dia ** 2 / 4 / cc, d, B, S)[0]       # Nmm/mm


def balk_armering(M_kNm, d, b=I.B_BALK):
    """Minsta stångantal ur STANG som ger M_Rd ≥ M (rektangulärt tvärsnitt) och minimiarmering 9.2.1.1."""
    Asmin = max(0.26 * B.fctm / S.fyk * b * d, 0.0013 * b * d)
    for n, dia in STANG:
        As = n * math.pi * dia ** 2 / 4
        x = As * S.fyd / (0.8 * B.fcd * b)
        MR = As * S.fyd * (d - 0.4 * x) / 1e6
        if MR >= M_kNm and As >= Asmin:
            return dict(n=n, dia=dia, As=As, MRd=MR, utn=M_kNm / MR)
    return None


def balk_skjuv(V_kN, As, d, b=I.B_BALK):
    rho = min(As / (b * d), 0.02)
    k = k_size(d)
    vr = max(0.18 / 1.5 * k * (100 * rho * B.fck) ** (1 / 3), vmin(d, B))
    VRc = vr * b * d / 1e3
    out = dict(VRdc=VRc, utn=V_kN / VRc, bygel=None)
    if V_kN > VRc:
        # byglar: Asw/s = V / (0.9 d fywd cotθ), cotθ = 2,5; Ø6 tvåskäriga
        asw = V_kN * 1e3 / (0.9 * d * S.fyd * 2.5)
        s = 2 * math.pi * 3 ** 2 / asw
        out["bygel"] = min(math.floor(s / 50) * 50, 0.75 * d)
    return out


def stans(netto_kN, d, u, a, rho):
    """SS-EN 1992-1-1 6.4.4(2): v = β V / (u d) ≤ C k (100 ρ f_ck)^(1/3) · 2d/a (≥ v_min · 2d/a)."""
    k = k_size(d)
    vr = max(0.18 / 1.5 * k * (100 * rho * B.fck) ** (1 / 3), vmin(d, B)) * 2 * d / a
    v = 1.15 * netto_kN * 1e3 / (u * d)
    return v, vr


def kontroll(utf):
    L, K = las(utf, "lång"), las(utf, "kort")
    h = I.UTFORANDEN[utf]["h_balk"]
    tjock_el = L["tjock"]; tri = L["tri_b"]; xy = L["xy_b"]
    tn = np.zeros(len(xy), bool); tn[np.unique(tri[tjock_el])] = True
    out = dict(utf=utf, h=h, plint=L["plint"])
    # ---------------------------------------------------------------- cellplast
    pmax = np.maximum(L["env"]["p_max"], K["env"]["p_max"])
    pperm = np.maximum(L["env"]["p_perm"], K["env"]["p_perm"])
    pqp = L["sls"]["p_qp"]
    eps = {}
    s3 = np.zeros(len(xy), bool)
    if L.get("s300") is not None and np.any(L["s300"]):
        s3[np.unique(tri[L["s300"]])] = True
    zoner = [("balk", tn & ~s3, "S200"), ("falt", ~tn, "S100")] + ([("s300", s3, "S300")] if s3.any() else [])
    for zon, m, grad in zoner:
        i = int(np.argmax(np.where(m, pmax, -1)))
        eps[zon] = dict(grad=grad, uls=float(pmax[m].max()), uls_xy=xy[i].tolist(), perm=float(pperm[m].max()),
                        qp=float(pqp[m].max()), fdM=eps_fd(grad, "M"), fdP=eps_fd(grad, "P"),
                        kryp=I.EPS[grad]["kryp2"], min=float(min(L["env"]["p_min"][m].min(), K["env"]["p_min"][m].min())))
        e = eps[zon]
        e["utn"] = max(e["uls"] / e["fdM"], e["perm"] / e["fdP"], e["qp"] / e["kryp"])
        # andel av ytan med tryck över hållfastheten
        e["over_M"] = float((pmax[m] > e["fdM"]).mean())
    if s3.any():
        eps["s300"]["zon"] = I.S300_ZON[utf]
    # punkter där balkarnas cellplast (S200) överskrids
    over = tn & ~s3 & (pmax > eps["balk"]["fdM"])
    eps["S300_noder"] = xy[over].tolist()
    eps["S300"] = dict(fdM=eps_fd("S300", "M"), fdP=eps_fd("S300", "P"), kryp=I.EPS["S300"]["kryp2"])
    out["eps"] = eps
    out["sattning"] = dict(wmax=float(L["sls"]["wb_qp"].max()), wmin=float(L["sls"]["wb_qp"].min()),
                           wt_max=float(L["sls"]["wt_qp"].max()))
    # ---------------------------------------------------------------- platta i fält
    mu = np.maximum(np.maximum(L["env"]["b_mux"], K["env"]["b_mux"]), np.maximum(L["env"]["b_muy"], K["env"]["b_muy"]))
    mo = -np.minimum(np.minimum(L["env"]["b_mox"], K["env"]["b_mox"]), np.minimum(L["env"]["b_moy"], K["env"]["b_moy"]))
    falt_n = ~tn
    # utjämnat över 250 mm (som i K-05)
    mus = np.maximum(utjamna(xy, tri, np.maximum(L["env"]["b_mux"], K["env"]["b_mux"]), "x"),
                     utjamna(xy, tri, np.maximum(L["env"]["b_muy"], K["env"]["b_muy"]), "y"))
    mos = np.maximum(utjamna(xy, tri, -np.minimum(L["env"]["b_mox"], K["env"]["b_mox"]), "x"),
                     utjamna(xy, tri, -np.minimum(L["env"]["b_moy"], K["env"]["b_moy"]), "y"))
    d_uk = I.H_PLATTA - C_UK - NAT[0] * 1.5
    d_ok = I.H_PLATTA - C_OK - NAT[0] * 1.5
    MRu, MRo = mrd_nat(*NAT, d_uk), mrd_nat(*NAT, d_ok)
    # fält: bara noder minst 300 mm från tjocka delar (övergången hör till balken/plinten)
    from scipy.spatial import cKDTree
    dtj = cKDTree(xy[tn]).query(xy)[0]
    fm = falt_n & (dtj > 300)
    out["falt"] = dict(mu=float(mus[fm].max()) / 1e3, mo=float(mos[fm].max()) / 1e3, MRu=MRu / 1e3, MRo=MRo / 1e3,
                       mu_topp=float(mu[falt_n].max()) / 1e3, mo_topp=float(mo[falt_n].max()) / 1e3,
                       utn=float(max(mus[fm].max() / MRu, mos[fm].max() / MRo)),
                       overgang_u=float(mus[falt_n & (dtj <= 300)].max()) / 1e3,
                       overgang_o=float(mos[falt_n & (dtj <= 300)].max()) / 1e3)
    # ---------------------------------------------------------------- balkar
    d_b_uk = h - C_UK - 8 - 6
    d_b_ok = h - C_OK - 8 - 6
    balkar = []
    for bL, bK in zip(L["env"]["balk"], K["env"]["balk"]):
        if len(bL["s"]) == 0:
            continue
        Mmax = float(max(bL["Mmax"].max(), bK["Mmax"].max()))
        Mmin = float(min(bL["Mmin"].min(), bK["Mmin"].min()))
        Vmax = float(max(bL["Vmax"].max(), bK["Vmax"].max()))
        du, do = (d_b_uk - URTAG, d_b_ok - URTAG) if bL["kant"] else (d_b_uk, d_b_ok)   # kantbalk: h − urtaget
        uk = balk_armering(max(Mmax, 0), du)
        ok = balk_armering(max(-Mmin, 0), do)
        sk = balk_skjuv(Vmax, uk["As"] if uk else 0, du)
        balkar.append(dict(namn=bL["namn"], vagg=bL["vagg"], kant=bL["kant"], p0=bL["p0"], p1=bL["p1"],
                           L=float(np.hypot(*np.subtract(bL["p1"], bL["p0"]))), Msag=Mmax, Mhog=-Mmin, V=Vmax,
                           uk=uk, ok=ok, skjuv=sk, d_uk=du, d_ok=do))
    out["balkar"] = balkar
    # ---------------------------------------------------------------- plintar (rör)
    st = L["env"]["stans"]; stK = K["env"]["stans"]
    netto = np.maximum(st["netto"], stK["netto"])
    N = np.maximum(st["N"], stK["N"])
    pl = []
    beff = fot_beff(B.fcd)
    for i, b in enumerate(L["plint"]):
        d = st["d"][i]
        As = math.pi * PLINT_ARM[0] ** 2 / 4 / PLINT_ARM[1]      # i underkant, båda riktningarna
        rho = As / d
        rows = []
        # hela rörlasten (cellplastens tryck innanför snittet räknas inte av), lastyta = fotplåtens effektiva yta
        # snitt innanför plinten (a ≤ plintens utsprång från plåten)
        for a in (0.5 * d, d, 1.5 * d, 2 * d):
            if a > (b - beff) / 2:
                continue
            u = 4 * beff + 2 * math.pi * a
            v, vr = stans(N[i], d, u, a, rho)
            rows.append(dict(a=a, u=u, netto=float(N[i]), v=v, vr=vr, utn=v / vr))
        gov = max(rows, key=lambda r: r["utn"])
        # snitt i den tunna plattan, 2d från plintens kant (6.4.2, 6.4.4(1)), hela rörlasten
        dt = I.H_PLATTA - C_UK - NAT[0] * 1.5
        rho_t = math.pi * NAT[0] ** 2 / 4 / NAT[1] / dt
        u_t = 4 * b + 4 * math.pi * dt
        vr_t = max(0.18 / 1.5 * k_size(dt) * (100 * rho_t * B.fck) ** (1 / 3), vmin(dt, B))
        v_t = 1.15 * N[i] * 1e3 / (u_t * dt)
        ute = dict(d=dt, u=u_t, v=v_t, vr=vr_t, utn=v_t / vr_t)
        # böjning: jämnt tryck N/b² under plinten, konsol från plåtens kant
        p = N[i] / (b / 1000) ** 2
        l = (b - beff) / 2 / 1000
        m = p * l ** 2 / 2                          # kNm/m
        MR = mrd_nat(*PLINT_ARM, d) / 1e3
        pl.append(dict(namn=f"P{i + 1}", b=b, N=float(N[i]), d=d, beff=beff, stans=gov, utn_stans=gov["utn"],
                       ute=ute, utn_ute=ute["utn"],
                       m=m, MRd=MR, utn_boj=m / MR, p=p))
    out["plintar"] = pl
    # ---------------------------------------------------------------- mellanbjälklaget (K-05) i samverkan
    xt, tt = L["xy_t"], L["tri_t"]
    env_t = {k: (np.maximum if k.startswith("t_mu") else np.minimum)(L["env"][k], K["env"][k])
             for k in ("t_mux", "t_muy", "t_mox", "t_moy")}
    s_t = dict(mux=utjamna(xt, tt, env_t["t_mux"], "x"), muy=utjamna(xt, tt, env_t["t_muy"], "y"),
               mox=utjamna(xt, tt, env_t["t_mox"], "x"), moy=utjamna(xt, tt, env_t["t_moy"], "y"))
    s_5 = dict(mux=utjamna(xt, tt, F05["mux"], "x"), muy=utjamna(xt, tt, F05["muy"], "y"),
               mox=utjamna(xt, tt, F05["mox"], "x"), moy=utjamna(xt, tt, F05["moy"], "y"))
    bo = R05["bojning"]
    MRx = np.full(len(xt), bo["ok"]["MRd_x"]); MRy = np.full(len(xt), bo["ok"]["MRd_y"])
    zon = np.zeros(len(xt), bool)
    for z in R05["zoner"]:
        x0, y0, x1, y1 = z["bounds"]
        m = (xt[:, 0] >= x0) & (xt[:, 0] <= x1) & (xt[:, 1] >= y0) & (xt[:, 1] <= y1)
        MRx[m] = np.maximum(MRx[m], z["MRd_x"]); MRy[m] = np.maximum(MRy[m], z["MRd_y"]); zon |= m
    u_ok = np.maximum(-s_t["mox"] / MRx, -s_t["moy"] / MRy)
    u_uk = np.maximum(s_t["mux"] / bo["uk"]["MRd_x"], s_t["muy"] / bo["uk"]["MRd_y"])
    u5_ok = np.maximum(-s_5["mox"] / MRx, -s_5["moy"] / MRy)
    u5_uk = np.maximum(s_5["mux"] / bo["uk"]["MRd_x"], s_5["muy"] / bo["uk"]["MRd_y"])
    i_ok, i_uk = int(np.argmax(u_ok)), int(np.argmax(u_uk))
    out["topp"] = dict(u_ok=float(u_ok.max()), xy_ok=xt[i_ok].tolist(), u_uk=float(u_uk.max()), xy_uk=xt[i_uk].tolist(),
                       u5_ok=float(u5_ok.max()), u5_uk=float(u5_uk.max()),
                       okning_ok=float(np.max(u_ok - u5_ok)), okning_uk=float(np.max(u_uk - u5_uk)),
                       mo_max=float(-min(s_t["mox"].min(), s_t["moy"].min())) / 1e3,
                       mu_max=float(max(s_t["mux"].max(), s_t["muy"].max())) / 1e3)
    # krympningens moment i mellanbjälklaget (lastfall SV, långtid)
    # (sparat i lf för lång: bara tryck och krafter sparas; momentet räknas i berakning06 om det behövs)
    # ---------------------------------------------------------------- rörlaster och väggar mot K-05
    ror = []
    for i, p in enumerate(R05["pelare"]):
        n = f"P{i + 1}"
        Nk = max(L["kr"]["max"][n], K["kr"]["max"][n]) / 1e3
        ror.append(dict(namn=n, N=Nk, N05=p["VEd"] / 1e3, kvot=Nk / (p["VEd"] / 1e3), utn05=p["utn"],
                        lag05=p["utn_lag"], utn=p["utn"] * max(1.0, Nk / (p["VEd"] / 1e3)),
                        lag=p["utn_lag"] * max(1.0, Nk / (p["VEd"] / 1e3))))
    out["ror"] = ror
    vg = []
    for v in R05["vaggar"]:
        n = v["namn"]
        q = max(L["env"]["vagg"].get(n, 0), K["env"]["vagg"].get(n, 0))
        vg.append(dict(namn=n, q=q, q05=v["qd_max"]))
    out["vaggar"] = vg
    # sättning i mellanbjälklagets stödpunkter (kvasipermanent, långtid): rör och väggar
    from scipy.spatial import cKDTree
    import modell06 as M
    wt = L["sls"]["wt_qp"]; trt = cKDTree(xt)
    wr = np.array([wt[trt.query(p_)[1]] for p_ in M.PEL])
    wv = np.concatenate([[wt[trt.query(q)[1]] for q in np.linspace(pl[0], pl[1], 20)] for pl in M.STODLIN])
    out["sattning"].update(ror_min=float(wr.min()), ror_max=float(wr.max()), vagg_min=float(wv.min()),
                           vagg_max=float(wv.max()), skillnad=float(np.median(wv) - np.median(wr)))
    out["svinn"] = dict(m_max=float(np.abs(L["mt_SV"][:, :2]).max()) / 1e3)
    # fält: råa värden i tunna delen (utjämningen över 250 mm tar med balkarnas moment vid övergången), minst d från
    # balkar och plintar. Närmare än så är momentet en lokal topp vid den tjocka delens kant, störst i inåtgående
    # hörn mellan balkarna, där FE-lösningen är singulär; den redovisas som information (topp_*).
    fd = falt_n & (dtj > d_uk)
    out["falt"].update(mu_ra=float(mu[fd].max()) / 1e3, mo_ra=float(mo[fd].max()) / 1e3,
                       utn_ra=float(max(mu[fd].max() / MRu, mo[fd].max() / MRo)), d=float(d_uk),
                       topp_mu=float(mu[falt_n].max()) / 1e3, topp_xy=xy[falt_n][np.argmax(mu[falt_n])].tolist())
    # cellplastens största tryck medelvärdesbildat inom r = 150 mm (lokal hörntopp)
    trb = cKDTree(xy)
    zb = tn & ~s3
    i = int(np.argmax(np.where(zb, pmax, 0)))
    g = [j for j in trb.query_ball_point(xy[i], 150.0) if zb[j]]
    out["eps"]["balk"]["uls_medel"] = float((pmax[g] * L["a_nod"][g]).sum() / L["a_nod"][g].sum())
    # plattan på mark på plan 1 (K-05): tryck mot 400 mm cellplast
    from matplotlib.path import Path as MplPath
    from omhyllande import ULS, SNO, falt
    mk = MplPath(np.asarray(I.G05["mark"], float)).contains_points(xt)
    mark = {}
    for var, R_ in (("lång", L), ("kort", K)):
        km = (I.EPS_KS if var == "lång" else 1.0) * I.EPS["S100"]["Ek"] * 1e-3 / I.EPS_MARK
        w = R_["wt"]
        pk = {k: km * v[mk] * 1e3 for k, v in w.items()}
        nq = len([k for k in pk if k.startswith("Q") and k != "Qb"])
        _, monster = falt()
        best = np.zeros(mk.sum())
        for (cg, cq, cs) in ULS.values():
            for mask in monster.values():
                for sn in SNO:
                    p_ = cg * pk["G"] + cq * (sum(m_ * pk[f"Q{j}"] for j, m_ in enumerate(mask)) + pk["Qb"]) + \
                         cs * sum((pk["S_" + k] for k in sn), 0 * pk["G"]) + (pk["SV"] if "SV" in pk else 0)
                    best = np.maximum(best, p_)
        qp = pk["G"] + 0.481 * (sum(pk[f"Q{j}"] for j in range(nq)) + pk["Qb"]) + 0.1 * (pk["S_V"] + pk["S_M"] + pk["S_H"])
        mark[var] = dict(uls=float(best.max()), qp=float(qp.max()))
    out["mark"] = dict(uls=max(m["uls"] for m in mark.values()), qp=mark["lång"]["qp"], fdM=eps_fd("S100", "M"),
                       kryp=I.EPS["S100"]["kryp2"])
    return out


if __name__ == "__main__":
    res = {}
    for utf in ("L300", "L400"):
        r = kontroll(utf)
        res[utf] = r
        e = r["eps"]
        print(f"== {utf}: plintar {r['plint']}")
        for z in [z_ for z_ in ("balk", "falt", "s300") if z_ in e]:
            x = e[z]
            print(f"  cellplast {z} {x['grad']}: ULS {x['uls']:.0f} ({x['fdM']:.0f}) vid {np.round(x['uls_xy'])}, perm {x['perm']:.0f} ({x['fdP']:.0f}), "
                  f"qp {x['qp']:.0f} ({x['kryp']:.0f}) -> {x['utn']*100:.0f} %, andel över {x['over_M']*100:.1f} %")
        print(f"  S300 behövs i {len(e['S300_noder'])} noder")
        f = r["falt"]
        print(f"  fält: mu {f['mu']:.1f} mo {f['mo']:.1f} kNm/m (MRd {f['MRu']:.1f}/{f['MRo']:.1f}) {f['utn']*100:.0f} %; övergång {f['overgang_u']:.1f}/{f['overgang_o']:.1f}")
        for b in r["balkar"]:
            uk, ok, sk = b["uk"], b["ok"], b["skjuv"]
            print(f"  {b['namn']:12s} {b['vagg']:9s} L {b['L']:6.0f}: M+ {b['Msag']:5.1f} M- {b['Mhog']:5.1f} V {b['V']:5.1f} | "
                  f"uk {uk['n'] if uk else '-'}Ø{uk['dia'] if uk else ''} ok {ok['n'] if ok else '-'}Ø{ok['dia'] if ok else ''} "
                  f"V/VRdc {sk['utn']:.2f} bygel {sk['bygel']}")
        for p in r["plintar"]:
            print(f"  {p['namn']:4s} b {p['b']:5.0f} N {p['N']:5.1f} stans {p['utn_stans']*100:3.0f} % (a {p['stans']['a']:.0f}) ute {p['utn_ute']*100:3.0f} % böj {p['utn_boj']*100:3.0f} %")
        t = r["topp"]
        print(f"  mellanbjälklag: ök {t['u_ok']*100:.0f} % (K-05-modellen {t['u5_ok']*100:.0f} %) vid {np.round(t['xy_ok'])}, uk {t['u_uk']*100:.0f} % ({t['u5_uk']*100:.0f} %) vid {np.round(t['xy_uk'])}")
        print("  rör:", " ".join(f"{x['namn']} {x['N']:.0f}/{x['N05']:.0f}" for x in r["ror"] if x["kvot"] > 1.0))
        print("  väggar:", " ".join(f"{x['namn']} {x['q']:.0f}/{x['q05']:.0f}" for x in r["vaggar"]))
    json.dump(res, open(os.path.join(HERE, "kontroll06.json"), "w"), indent=1, ensure_ascii=False, default=float)
