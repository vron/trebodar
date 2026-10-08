"""
K-06: huvudskript. Väggarna (vaggar.py), den samverkande modellen (berakning06.py, körs om res06_*.pkl saknas),
kontrollerna av bottenplattan (kontroll06.py) och global stabilitet. Skriver resultat.json.

    python berakning.py          (cirka 8 min första gången)
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
    """Ojämnt jordtryck på huset (ingen fyllning vid fasaden med öppningarna) mot friktion under bottenplattan."""
    rows = []
    sx = sy = 0.0
    for v in VG.vaggar():
        if max(v["fyll"]) <= 0:
            continue
        xs = np.linspace(0, v["L"], 41)
        R = np.trapezoid([VG.tryck_k(v, x)[1] for x in xs], xs)         # kN, karakteristiskt
        ax, c = v["ax"], v["c"]
        # jorden står på den sida av väggen som ligger utanför källaren
        poly = __import__("modell06").kallare()
        from shapely.geometry import Point
        mid = (v["a"] + v["b"]) / 2
        ute = (lambda p: not poly.contains(Point(p)))
        if ax == "h":
            rikt = -1 if ute((mid, c + 400)) else 1                        # jord norr om väggen trycker söderut
            sy += rikt * R
        else:
            rikt = -1 if ute((c + 400, mid)) else 1
            sx += rikt * R
        rows.append(dict(namn=v["namn"], R=R, rikt=("y" if ax == "h" else "x"), tecken=rikt))
    import modell06 as M
    S0 = M.System("L300", [1000.0] * len(M.PEL), "S100", "S200", "kort")
    F, _ = M.laster(S0.Pt, S0.Pb)
    Gtot = float(F["G"][0::3].sum()) / 1e3
    Gmark = float((S0.Pt.k_mark if hasattr(S0.Pt, "k_mark") else 0) or 0)
    MY = 0.3                                     # friktion i svagaste skiktet (plastfolie mellan cellplastskikten)
    Fd = math.hypot(sx, sy) * 1.35 * GD
    return dict(vaggar=rows, Fx=sx, Fy=sy, Fd=Fd, G=Gtot, my=MY, Rd=MY * Gtot, utn=Fd / (MY * Gtot))


def main(om=False):
    for x in ("", "_ytter"):
        if om or not all(os.path.exists(os.path.join(HERE, f"res06_{u}_{v}{x}.pkl")) for u in ("L300", "L400")
                         for v in ("lång", "kort")):
            subprocess.run([sys.executable, os.path.join(HERE, "berakning06.py")] + (["ytter"] if x else []),
                           check=True, cwd=HERE)
    subprocess.run([sys.executable, os.path.join(HERE, "kontroll06.py")], check=True, cwd=HERE)
    R = dict(indata=dict(K0=I.K0, fi=I.FI_JORD, gamma=I.GAMMA_JORD, q=I.Q_MARK, h_fyll_mark=I.H_FYLL_MARK,
                         g_mark=I.G_MARK, q_mark=I.Q_MARK_PLATTA, H=I.H_VAGG, gM=I.GAMMA_M_MUR, gS=I.GAMMA_M_ARM))
    R["system"] = {s: dict(I.SYSTEM[s], mh={var: VG.moment_h(s, var)[0] for var in (1, 2)},
                           mh_detalj={var: VG.moment_h(s, var)[1] for var in (1, 2)}) for s in ("A", "B")}
    R["vaggar"] = VG.tabell()
    R["platta"] = json.load(open(os.path.join(HERE, "kontroll06.json"), encoding="utf-8"))
    R["glidning"] = glidning()
    json.dump(R, open(os.path.join(HERE, "resultat.json"), "w"), indent=1, ensure_ascii=False, default=float)
    print("klart")


if __name__ == "__main__":
    main("-om" in sys.argv)
