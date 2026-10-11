"""
K-06: huvudskript. Den samverkande modellen (berakning06.py, körs om res06_*.pkl saknas), kontrollerna av
bottenplattan (kontroll06.py), väggarna och byggskedet (vaggar.py) och global stabilitet. Skriver resultat.json.

    python berakning.py          (cirka 10 min första gången)
"""
import json
import math
import os
import subprocess
import sys

import numpy as np

import indata as I
import vaggar as VG

HERE = os.path.dirname(os.path.abspath(__file__))
GD = 0.91


def glidning():
    """Ojämnt jordtryck på huset (lägre fyllning vid fasaden med öppningarna) mot friktion under bottenplattan.
    Karakteristiskt vilojordtryck och, som jämförelse, med det kvarstående packningstrycket."""
    from shapely.geometry import Point
    import modell06 as M
    poly = M.kallare()
    rows = []
    s = {"K0": [0.0, 0.0], "komp": [0.0, 0.0]}
    for v in VG.vaggar():
        if max(v["fyll"]) <= 0:
            continue
        xs = np.linspace(0, v["L"], 41)
        R = {"K0": float(np.trapezoid([VG.tryck_k(v, x)[1] for x in xs], xs)),
             "komp": float(np.trapezoid([VG.tryck_komp(v, x) for x in xs], xs))}          # kN, karakteristiskt
        ax, c = v["ax"], v["c"]
        mid = (v["a"] + v["b"]) / 2
        ute = (lambda p: not poly.contains(Point(p)))
        # jorden står på den sida av väggen som ligger utanför källaren
        if ax == "h":
            rikt, k = (-1 if ute((mid, c + 400)) else 1), 1
        else:
            rikt, k = (-1 if ute((c + 400, mid)) else 1), 0
        for f in s:
            s[f][k] += rikt * R[f]
        rows.append(dict(namn=v["namn"], R=R["K0"], Rkomp=R["komp"], rikt=("y" if ax == "h" else "x"), tecken=rikt))
    S0 = M.System("L300", [1000.0] * len(M.PEL), "S100", "S200", "kort")
    F, _ = M.laster(S0.Pt, S0.Pb)
    Gtot = float(F["G"][0::3].sum()) / 1e3
    MY = 0.3                                     # friktion i svagaste skiktet (plastfolie mellan cellplastskikten)
    out = dict(vaggar=rows, G=Gtot, my=MY, Rd=MY * Gtot)
    for f, (sx, sy) in s.items():
        Fd = math.hypot(sx, sy) * 1.35 * GD
        out[f] = dict(Fx=sx, Fy=sy, Fd=Fd, utn=Fd / (MY * Gtot))
    return out


def main(om=False):
    if om or not all(os.path.exists(os.path.join(HERE, f"res06_{u}_{v}.pkl")) for u in ("L300", "L400")
                     for v in ("lång", "kort")):
        subprocess.run([sys.executable, os.path.join(HERE, "berakning06.py")], check=True, cwd=HERE)
    subprocess.run([sys.executable, os.path.join(HERE, "kontroll06.py")], check=True, cwd=HERE)
    R = dict(indata=dict(K0=I.K0, KA=I.KA, fi=I.FI_JORD, gamma=I.GAMMA_JORD, q=I.Q_MARK, h_fyll_mark=I.H_FYLL_MARK,
                         g_mark=I.G_MARK, q_mark=I.Q_MARK_PLATTA, H=I.H_VAGG, Ls=VG.LS, sig_komp=I.SIG_KOMP,
                         P_platta=I.P_PLATTA, g_bygg=I.G_BYGG, q_bygg=I.Q_BYGG, e_topp=VG.E_TOPP))
    rows, arm = VG.tabell()
    R["bygg"] = VG.byggskede(rows, arm)
    for r in rows:
        r.pop("_dim", None)
    R["vaggar"] = rows
    R["arm"] = arm
    R["hornlast"] = VG.hornlast()
    R["platta"] = json.load(open(os.path.join(HERE, "kontroll06.json"), encoding="utf-8"))
    R["glidning"] = glidning()
    json.dump(R, open(os.path.join(HERE, "resultat.json"), "w"), indent=1, ensure_ascii=False, default=float)
    print("klart")


if __name__ == "__main__":
    main("-om" in sys.argv)
