"""Påtvingad sättning av rören i förhållande till väggarna: tillskottsmoment i mellanbjälklaget (långtid, osprucket)."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import modell
from platta import Dmat, wood_armer
from omhyllande import utjamna_linje
from ec2 import Betong
B = Betong(fck=25)
Eeff = B.Ecm / (1 + B.kryptal(150))
K = 1e9
def kor(sattning):
    P, _ = modell.bygg(k_ror=K)
    P.styvhet(Dmat(Eeff * 150 ** 3 / 12 / (1 - 0.04), 0.2))
    f = np.zeros(P.ndof)
    for s in P.stod:
        if s["typ"] == "rekt" and s["namn"] in sattning:
            kk = K / len(s["noder"])
            for n in s["noder"]:
                f[3 * n] += kk * sattning[s["namn"]]
    r = P.los(f)
    wa = wood_armer(*r.m_nod.T)
    ux = utjamna_linje(r, wa[0], "x", 250); uy = utjamna_linje(r, wa[1], "y", 250)
    ox = utjamna_linje(r, wa[2], "x", 250); oy = utjamna_linje(r, wa[3], "y", 250)
    return max(ux.max(), uy.max()) / 1e3, -min(ox.min(), oy.min()) / 1e3, r
alla = {f"P{i}": 1.0 for i in range(1, 20)}
for namn, s in (("alla rör 1 mm", alla), ("P10 2 mm", {"P10": 2.0}), ("P5 2 mm", {"P5": 2.0}),
                ("alla rör 2 mm", {k: 2.0 for k in alla})):
    u, o, r = kor(s)
    print(f"{namn}: tillskott uk {u:.1f} kNm/m, ök {o:.1f} kNm/m (E_eff {Eeff/1e3:.1f} GPa, osprucket)")
