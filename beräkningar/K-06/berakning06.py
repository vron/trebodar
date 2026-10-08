"""
K-06: bottenplattan i den samverkande modellen (modell06), båda utförandena (L300 och L400).

För varje utförande räknas två styvheter:
  kort  korttidsstyvhet (cellplast E_k, Leca och betong utan krypning) – brottgräns
  lång  långtidsstyvhet (cellplast 0,4 E_k, Leca och betong med krypning, Lecans krympning) – brottgräns och bruks
Lastfall: G, snö per huskropp, nyttig last per fält på mellanbjälklaget (K-05:s mönster), nyttig last i källaren,
Lecaväggarnas krympning (bara lång). Kombinationer som i K-05.

    python berakning06.py   -> res06_<utf>.npz och res06.json
"""
import itertools
import json
import os
import sys
import time

import numpy as np

import indata as I
import modell06 as M
from platta import wood_armer
from omhyllande import ULS, SNO, utjamna_linje
from laster import KROPPAR

HERE = os.path.dirname(os.path.abspath(__file__))
PSI2_Q, PSI2_S = 0.3, 0.1
EPS_FALT, EPS_BALK = "S100", "S200"
P_MAL = 30.0             # kPa: plintarnas storlek väljs för ungefär samma långtidstryck som under väggarna
BAND = 250.0


def k_mark(variant):
    """Plattan på mark på plan 1: 400 mm S100."""
    ke = I.EPS_KS if variant == "lång" else 1.0
    return ke * I.EPS["S100"]["Ek"] * 1e-3 / I.EPS_MARK


def plintar(N_qp):
    """Plintens sida [mm] för långtidstrycket P_MAL, 600–1400 mm i steg om 100 mm."""
    b = np.sqrt(np.asarray(N_qp) / P_MAL) * 1000
    return np.clip(np.ceil(b / 100) * 100, 600, 1400)


def lastfall(S, F, variant):
    names = ["G", "S_V", "S_M", "S_H", "Qb"] + [f"Q{i}" for i in range(len(F["Q"]))]
    cols = [F["G"], F["S_V"], F["S_M"], F["S_H"], F["Qb"]] + list(F["Q"])
    if variant == "lång":
        names.append("SV")
        cols.append(M.svinn(S.kopp, S.ndof, I.SVINN_LECA))
    U = S.lu.solve(np.column_stack(cols))
    return dict(zip(names, U.T))


def analys(utf, plint, variant, spara=True, ytter=False):
    """ytter: ytterväggarnas båda vangar bär, och lasterna över väggarna står där de står (modell06)."""
    t0 = time.time()
    S = M.System(utf, plint, EPS_FALT, EPS_BALK, variant, k_mark=k_mark(variant), ytter=ytter)
    F, monster = M.laster(S.Pt, S.Pb, verklig=ytter)
    U = lastfall(S, F, variant)
    nq = len(F["Q"])
    # snittkrafter per lastfall
    mt, mb = {}, {}
    for k, u in U.items():
        rt, rb = S.resultat(u, np.zeros(S.ndof))
        mt[k], mb[k] = rt.m_nod, rb.m_nod
    p_eps = {k: S.tryck(u) for k, u in U.items()}
    import snitt06 as SN
    sx = SN.Snitt(S)
    balk_lf, stans_lf, vagg_lf = {}, {}, {}
    for k, u in U.items():
        qx, qy = SN.skjuv_komp(S.Pb, mb[k])
        balk_lf[k] = sx.balk_lf(mb[k], qx, qy)
        stans_lf[k] = np.array(sx.stans_lf(p_eps[k]))
        vagg_lf[k] = sx.vagg_lf(u, I.SVINN_LECA if k == "SV" else 0.0)
    krafter = {k: S.krafter(u, I.SVINN_LECA if k == "SV" else 0.0) for k, u in U.items()}
    w_t = {k: u[:S.nt][0::3] for k, u in U.items()}
    w_b = {k: u[S.nt:][0::3] for k, u in U.items()}
    nt_, nb_ = S.Pt.nn, S.Pb.nn
    env = dict(t_mux=np.zeros(nt_), t_muy=np.zeros(nt_), t_mox=np.zeros(nt_), t_moy=np.zeros(nt_),
               b_mux=np.zeros(nb_), b_muy=np.zeros(nb_), b_mox=np.zeros(nb_), b_moy=np.zeros(nb_),
               p_max=np.zeros(nb_), p_min=np.full(nb_, 1e9), p_perm=None)
    kr_max, kr_komb = {}, {}
    balk_env, stans_env, vagg_env = {}, {}, {}
    sv = 1.0 if variant == "lång" else 0.0
    base = lambda d, cg: cg * d["G"] + sv * (d["SV"] if "SV" in d else 0)
    for (kn, (cg, cq, cs)), (mn, mask) in itertools.product(ULS.items(), monster.items()):
        for sn in SNO:
            def komb(d):
                return (base(d, cg) + cq * (sum(m_ * d[f"Q{i}"] for i, m_ in enumerate(mask)) + d["Qb"]) +
                        cs * sum((d["S_" + k] for k in sn), 0 * d["G"]))
            m = komb(mt)
            wa = wood_armer(m[:, 0], m[:, 1], m[:, 2])
            env["t_mux"] = np.maximum(env["t_mux"], wa[0]); env["t_muy"] = np.maximum(env["t_muy"], wa[1])
            env["t_mox"] = np.minimum(env["t_mox"], wa[2]); env["t_moy"] = np.minimum(env["t_moy"], wa[3])
            m = komb(mb)
            wa = wood_armer(m[:, 0], m[:, 1], m[:, 2])
            env["b_mux"] = np.maximum(env["b_mux"], wa[0]); env["b_muy"] = np.maximum(env["b_muy"], wa[1])
            env["b_mox"] = np.minimum(env["b_mox"], wa[2]); env["b_moy"] = np.minimum(env["b_moy"], wa[3])
            p = komb(p_eps)
            env["p_max"] = np.maximum(env["p_max"], p); env["p_min"] = np.minimum(env["p_min"], p)
            for j in range(len(sx.balkar)):
                Mb = komb({k: v[j][0] for k, v in balk_lf.items()})
                Vb = komb({k: v[j][1] for k, v in balk_lf.items()})
                bm = balk_env.setdefault(j, dict(Mmax=np.full(len(Mb), -1e9), Mmin=np.full(len(Mb), 1e9),
                                                  Vmax=np.zeros(len(Mb))))
                bm["Mmax"] = np.maximum(bm["Mmax"], Mb); bm["Mmin"] = np.minimum(bm["Mmin"], Mb)
                bm["Vmax"] = np.maximum(bm["Vmax"], np.abs(Vb))
            dV = komb(stans_lf)                                  # (rör, snitt) kN
            Nr = np.array([komb({k: kr[f"P{i + 1}"] for k, kr in krafter.items()}) for i in range(len(M.PEL))]) / 1e3
            netto = Nr[:, None] - dV
            stans_env["netto"] = np.maximum(stans_env.get("netto", -1e9 * np.ones_like(netto)), netto)
            stans_env["N"] = np.maximum(stans_env.get("N", -1e9 * np.ones(len(Nr))), Nr)
            for n in vagg_lf["G"]:
                vv = komb({k: v[n] for k, v in vagg_lf.items()})
                vagg_env[n] = max(vagg_env.get(n, -1e9), float(vv.max()))
            for n in krafter["G"]:
                v = komb({k: kr[n] for k, kr in krafter.items()})
                if v > kr_max.get(n, -1e18):
                    kr_max[n] = v; kr_komb[n] = f"{kn}, Q {mn}, snö {''.join(sn) or 'ingen'}"
    # permanent last enbart (för cellplastens hållfasthet vid permanent last)
    env["p_perm"] = 1.35 * M05GD * p_eps["G"] + sv * (p_eps["SV"] if "SV" in p_eps else 0)
    # bruksgräns: kvasipermanent (lätta väggar räknas som permanenta, som i K-05)
    def kvasi(d):
        q = sum(d[f"Q{i}"] for i in range(nq)) + d["Qb"]
        return d["G"] + (0.7 / 2.7 + PSI2_Q * 2.0 / 2.7) * q + PSI2_S * (d["S_V"] + d["S_M"] + d["S_H"]) + \
            sv * (d["SV"] if "SV" in d else 0)
    def kar(d):
        q = sum(d[f"Q{i}"] for i in range(nq)) + d["Qb"]
        return d["G"] + q + d["S_V"] + d["S_M"] + d["S_H"] + sv * (d["SV"] if "SV" in d else 0)
    sls = dict(p_qp=kvasi(p_eps), wt_qp=kvasi(w_t), wb_qp=kvasi(w_b), mt_qp=kvasi(mt), mb_qp=kvasi(mb),
               p_k=kar(p_eps), kr_qp={n: kvasi({k: kr[n] for k, kr in krafter.items()}) for n in krafter["G"]})
    lf = dict(mt=mt, mb=mb, p=p_eps, w_t=w_t, w_b=w_b, kr=krafter)
    # jämvikt: last = cellplastens reaktion under bottenplattan + bädden under plattan på mark (plan 1)
    km = np.array([S.Pt.springs.get(3 * n, 0.0) for n in range(S.Pt.nn)])
    env["jamvikt"] = {k: dict(last=float(F[k][0::3].sum() / 1e3) if k in F else None,
                              reaktion=float((S.Pb.k_nod * U[k][S.nt:][0::3]).sum() + (km * U[k][:S.nt][0::3]).sum()) / 1e3)
                      for k in ("G", "S_V", "S_M", "S_H", "Qb")}
    env["balk"] = [dict(namn=b["namn"], vagg=b["vagg"], rikt=b["rikt"], kant=b["kant"], s=b["s"], xy=b["xy"],
                        p0=b["p0"], p1=b["p1"], **balk_env[j]) for j, b in enumerate(sx.balkar)]
    env["stans"] = dict(netto=stans_env["netto"], N=stans_env["N"], d=[s_["d"] for s_ in sx.stans],
                        u=[[r["u"] for r in s_["reg"]] for s_ in sx.stans], a=[[r["a"] for r in s_["reg"]] for s_ in sx.stans])
    env["vagg"] = vagg_env
    if ytter:
        yk = [kp for kp in S.kopp if kp.get("vange") == "yttre"]
        fy = {k: np.array([M.kraft(kp, u) for kp in yk]) for k, u in U.items()}
        env["ytter_vange"] = dict(G_min=float(fy["G"].min()), G_sum=float(fy["G"].sum()),
                                  inre_G_sum=float(sum(M.kraft(kp, U["G"]) for kp in S.kopp
                                                       if kp["typ"] == "vägg" and kp.get("vange") != "yttre"
                                                       and M.VTYP[int(kp["namn"][1:]) - 1] == "yttre")))
    print(f"{utf} {variant}{' ytter' if ytter else ''}: {time.time() - t0:.0f} s, dof {S.ndof}")
    return S, env, sls, lf, dict(max=kr_max, komb=kr_komb), monster


M05GD = 0.91


def spara(S, env, sls, lf, kr, plint, namn):
    import pickle
    pickle.dump(dict(env=env, sls=sls, kr=kr, plint=plint, xy_t=S.Pt.xy, tri_t=S.Pt.tri, xy_b=S.Pb.xy,
                     tri_b=S.Pb.tri, tjock=S.Pb.tjock, s300=S.Pb.s300, h_el=S.Pb.h_el, a_nod=S.Pb.a_nod,
                     k=(S.k_falt, S.k_balk), lf_p=lf["p"], lf_kr=lf["kr"],
                     mt_SV=lf["mt"].get("SV"), mt_G=lf["mt"]["G"], wt=lf["w_t"], wb=lf["w_b"]),
                open(os.path.join(HERE, namn), "wb"))


if __name__ == "__main__":
    # python berakning06.py [L300] [L400] [ytter] [omplint]
    #   grundmodellen, eller med "ytter" varianten där båda vangarna bär och lasterna står där de står.
    #   Plintarnas storlek tas ur grundmodellens tidigare körning, om den finns och "omplint" inte anges.
    import pickle
    arg = sys.argv[1:]
    ytter = "ytter" in arg
    for utf in [a for a in arg if a.startswith("L")] or ["L300", "L400"]:
        f0 = os.path.join(HERE, f"res06_{utf}_lång.pkl")
        if os.path.exists(f0) and "omplint" not in arg:
            plint = pickle.load(open(f0, "rb"))["plint"]
        else:
            # plintstorlek ur en första körning med 1,0 m plintar
            S0, _, sls0, _, _, _ = analys(utf, [1000.0] * len(M.PEL), "lång")
            Nqp = [sls0["kr_qp"][f"P{i + 1}"] / 1e3 for i in range(len(M.PEL))]
            plint = [float(b) for b in plintar(Nqp)]
            del S0
        print(utf, "plintar:", plint, flush=True)
        for variant in ("lång", "kort"):
            S, env, sls, lf, kr, monster = analys(utf, plint, variant, ytter=ytter)
            spara(S, env, sls, lf, kr, plint, f"res06_{utf}_{variant}{'_ytter' if ytter else ''}.pkl")
            if ytter:
                print("  yttre vangen:", {k: round(v / 1e3, 1) for k, v in env["ytter_vange"].items()}, flush=True)
            del S, env, sls, lf
