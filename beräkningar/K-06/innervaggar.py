"""
K-06: innerväggarna gjuts i ett med mellanbjälklaget (det översta halva skiftet med bjälklaget, som ytterväggarna).
Väggarna håller då emot när plattan vrider sig över dem. K-05:s FE-modell (upplagslinjer i väggarnas mitt) får
vridfjädrar längs innerväggarnas upplagslinjer, k = 4·E·I/h per meter (kärnan 150 mm, h = 2 100, fast inspänd fot,
C30/37 osprucken korttid: övre gräns för momentet i väggen). Samma kombinationer som K-05 (6.10a/b, nyttig last i
mönster, snö per huskropp) och dessutom 6.10b med permanent last gynnsam (1,0).

Redovisar per innervägg samtidiga normalkraft och moment i väggens topp i 500 mm-bitar (största moment, minsta
normalkraft) och, som kontroll av att K-05:s fritt upplagda plattmodell fortfarande gäller, hur plattans
dimensionerande moment och rörlasterna ändras med inspänningen. Skriver innervaggar.json.

    python innervaggar.py        (cirka 1 min)
"""
import itertools
import json
import os
import sys

import numpy as np
from matplotlib.path import Path as MplPath

import indata as I                 # sätter sys.path till K-05
import modell as M05
from omhyllande import falt, ULS, SNO
from laster import KROPPAR
from platta import Dmat, wood_armer
from ec2 import Betong

HERE = os.path.dirname(os.path.abspath(__file__))
G = M05.G
INRE = [i for i, w in enumerate(G["vagg"]) if w[4] == "inre"]
E_V = Betong(fck=I.FCK_V).Ecm                      # MPa
K_THETA = 4 * E_V * I.T_KARNA ** 3 / 12 / I.H_VAGG # Nmm/mm per rad
BIT = 500.0                                        # mm, längd som N och M medelvärdesbildas över
KOMB = dict(ULS, **{"6.10b Q, G gynnsam": (1.0, M05.GD * 1.5, M05.GD * 1.5 * 0.6)})


def bygg(inspand=True):
    """K-05:s modell; med inspand vridfjädrar på lutningen tvärs innerväggarnas upplagslinjer."""
    P, f = M05.bygg()
    lin = {}
    for i in INRE:
        ax, c, a, b = G["stod"][i]
        pl = [(a, c), (b, c)] if ax == "h" else [(c, a), (c, b)]
        nod = P.noder_pa_linje(pl)
        s = np.array([P.xy[n][0] if ax == "h" else P.xy[n][1] for n in nod])
        o = np.argsort(s)
        s, nod = s[o], [nod[j] for j in o]
        w = np.zeros(len(s)); w[:-1] += np.diff(s) / 2; w[1:] += np.diff(s) / 2
        dof = 2 if ax == "h" else 1                # θ = ∂w/∂y för väggar längs x, ∂w/∂x för väggar längs y
        if inspand:
            for n, wi in zip(nod, w):
                P.springs[3 * n + dof] = P.springs.get(3 * n + dof, 0.0) + K_THETA * wi
        lin[f"V{i + 1}"] = dict(nod=nod, s=s, w=w, dof=dof)
    P.styvhet(Dmat(M05.b.Ecm * M05.H ** 3 / 12 / (1 - 0.2 ** 2), 0.2))
    return P, f, lin


def los(inspand):
    P, f, lin = bygg(inspand)
    polys, monster = falt()
    qt = f["QT"][0::3]
    fQ = []
    for p in polys:
        fq = P.last_yta(M05.QK + M05.QV, p)
        fq[0::3] += np.where(MplPath(np.asarray(p, float)).contains_points(P.xy), qt, 0.0)
        fQ.append(fq)
    res = P.los_flera([f["G"]] + [f["S_" + k] for k in KROPPAR] + fQ)
    return P, lin, res[0], dict(zip(KROPPAR, res[1:1 + len(KROPPAR)])), res[1 + len(KROPPAR):], monster


def vaggkrafter(r, lin, kt):
    """Per vägg: N [kN/m] och M [kNm/m] i väggens topp, medelvärden över BIT, och bitarnas mitt s [mm]."""
    ut = {}
    for n, L in lin.items():
        nod, s, w = L["nod"], L["s"], L["w"]
        R = np.array([r.R[3 * k] for k in nod])
        M = np.array([kt * r.u[3 * k + L["dof"]] for k in nod])
        bitar = np.arange(s[0], s[-1] + 1e-6, BIT)
        N_, M_ = [], []
        for a in bitar:
            m = (s >= a - BIT / 2) & (s <= a + BIT / 2)
            N_.append(R[m].sum() / max(w[m].sum(), 1.0))
            M_.append((M[m] * w[m]).sum() / max(w[m].sum(), 1.0) / 1e3)
        ut[n] = (np.array(N_), np.array(M_), bitar)
    return ut


def berakna():
    # med inspänning: väggarnas toppmoment och normalkraft
    P, lin, rG, rS, rQ, monster = los(True)
    VG, VS, VQ = vaggkrafter(rG, lin, K_THETA), {k: vaggkrafter(r, lin, K_THETA) for k, r in rS.items()}, \
        [vaggkrafter(r, lin, K_THETA) for r in rQ]
    vagg = {n: dict(M=0.0, N_M=0.0, s_M=0.0, komb_M="", Nmin=1e9, M_Nmin=0.0, komb_N="") for n in lin}
    for (kn, (cg, cq, cs)), (mn, mask) in itertools.product(KOMB.items(), monster.items()):
        for sn in SNO:
            namn = f"{kn}, Q {mn}, snö {''.join(sn) or 'ingen'}"
            for n, d in vagg.items():
                N = cg * VG[n][0] + cs * sum(VS[k][n][0] for k in sn) + cq * sum(m * v[n][0] for m, v in zip(mask, VQ))
                M = cg * VG[n][1] + cs * sum(VS[k][n][1] for k in sn) + cq * sum(m * v[n][1] for m, v in zip(mask, VQ))
                j = int(np.argmax(np.abs(M)))
                if abs(M[j]) > d["M"]:
                    d.update(M=float(abs(M[j])), N_M=float(N[j]), s_M=float(VG[n][2][j]), komb_M=namn)
                j = int(np.argmin(N))
                if N[j] < d["Nmin"]:
                    d.update(Nmin=float(N[j]), M_Nmin=float(abs(M[j])), s_N=float(VG[n][2][j]), komb_N=namn)

    # plattans dimensionerande moment och rörlasterna med och utan inspänning (K-05:s kombinationer)
    def omhyllning(P, rG, rS, rQ, monster):
        env = [np.full(P.nn, -np.inf)] * 2 + [np.full(P.nn, np.inf)] * 2
        RG, RS, RQ = rG.reaktioner(), {k: r.reaktioner() for k, r in rS.items()}, [r.reaktioner() for r in rQ]
        ror = {n: -np.inf for n in RG if n.startswith("P")}
        for (kn, (cg, cq, cs)), (mn, mask) in itertools.product(ULS.items(), monster.items()):
            mq = sum(m * r.m_nod for m, r in zip(mask, rQ))
            for sn in SNO:
                wa = wood_armer(*(cg * rG.m_nod + cq * mq + cs * sum(rS[k].m_nod for k in sn)).T)
                env = [np.maximum(env[0], wa[0]), np.maximum(env[1], wa[1]),
                       np.minimum(env[2], wa[2]), np.minimum(env[3], wa[3])]
                for n in ror:
                    ror[n] = max(ror[n], cg * RG[n] + cs * sum(RS[k][n] for k in sn)
                                 + cq * sum(m * r[n] for m, r in zip(mask, RQ)))
        return [np.abs(e) / 1e3 for e in env], ror

    e1, r1 = omhyllning(P, rG, rS, rQ, monster)
    P0, _, rG0, rS0, rQ0, _ = los(False)
    e0, r0 = omhyllning(P0, rG0, rS0, rQ0, monster)
    assert P0.nn == P.nn
    okning = [e1[i] - e0[i] for i in range(4)]
    i, j = max(((i, int(np.argmax(o))) for i, o in enumerate(okning)), key=lambda t: okning[t[0]][t[1]])
    platta = dict(okning=float(okning[i][j]), var=[float(x) for x in P.xy[j]], fran=float(e0[i][j]),
                  till=float(e1[i][j]), lager=("underkant", "underkant", "överkant", "överkant")[i],
                  max_utan=[float(e.max()) for e in e0], max_med=[float(e.max()) for e in e1])
    dr = {n: (r1[n] - r0[n]) / 1e3 for n in r0}
    nr = max(dr, key=lambda n: abs(dr[n]))
    ut = dict(k=K_THETA / 1e3, E=E_V, vaggar=vagg, platta=platta, ror=dict(namn=nr, andring=dr[nr]))
    json.dump(ut, open(os.path.join(HERE, "innervaggar.json"), "w"), indent=1, ensure_ascii=False)
    return ut


if __name__ == "__main__":
    u = berakna()
    for n, d in u["vaggar"].items():
        print(f"{n}: M {d['M']:.2f} kNm/m (N {d['N_M']:.1f}), Nmin {d['Nmin']:.1f} kN/m (M {d['M_Nmin']:.2f})")
    print("platta:", u["platta"], "\nrör:", u["ror"])
