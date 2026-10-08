"""Nätkonvergens för en kombination (6.10b, snö som huvudlast, full nyttig last, mjuka och styva rör): största utjämnade
moment och största rörlast med olika grundnät och lokal förfining. Skriver konvergens.json."""
import os, sys, json; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import modell
from platta import wood_armer
from omhyllande import utjamna_linje, ULS

BAND = float(os.environ.get("BAND", 250))
cg, cq, cs = ULS["6.10b S"]
out = []
for kr, h, fin in [(k, h, fin) for k in (None, 1e9) for h, fin in ((300.0, 1.0), (200.0, 1.0), (200.0, 0.6), (200.0, 0.4))]:
    modell.FIN = fin
    P, f = modell.bygg(hmax=h, k_ror=kr)
    r = P.los(cg * f["G"] + cq * (f["Q"] + f["V"] + f["QT"]) + cs * f["S"])
    wa = wood_armer(*r.m_nod.T)
    mo = np.maximum(-utjamna_linje(r, wa[2], "x", BAND), -utjamna_linje(r, wa[3], "y", BAND))
    mu = np.maximum(utjamna_linje(r, wa[0], "x", BAND), utjamna_linje(r, wa[1], "y", BAND))
    i = int(np.argmax(mo))
    R = r.reaktioner()
    d = dict(ror="fjäder" if kr is None else "styv", h=h, fin=fin, ne=int(P.ne), mo=float(mo.max()) / 1e3, xy=[float(v) for v in P.xy[i]],
             mu=float(mu.max()) / 1e3, P10=R["P10"] / 1e3)
    out.append(d)
    print(d, flush=True)
    del P, r, wa
json.dump(out, open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "konvergens.json"), "w"), indent=1)
