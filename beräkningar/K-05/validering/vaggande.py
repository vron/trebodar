"""Stödmoment vid väggändar: stela upplagslinjer (huvudmodellen) mot väggar som fjädrar med Lecans axialstyvhet
E·t/h. En stel linje som slutar ger en singulär topp; en fjädrande vägg ger ett ändligt värde som konvergerar.
Kombination 6.10b med snö som huvudlast, full nyttig last, mjuka rör. Skriver vaggande.json."""
import os, sys, json; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import modell
from platta import wood_armer
from omhyllande import utjamna_linje, ULS

BAND = float(os.environ.get("BAND", 250))
T_SKIKT, H_VAGG = 100.0, 2600.0            # Lecaskiktets tjocklek och väggens höjd [mm]
cg, cq, cs = ULS["6.10b S"]
punkter = {"V15 väggände": (9640.0, 7510.0), "hörn vid plattan på mark (LD4_2)": (4605.0, 10825.0)}
out = []
for E in (None, 5000.0, 2000.0):
    for fin in (1.0, 0.6, 0.4):
        modell.FIN = fin
        k = None if E is None else E * T_SKIKT / H_VAGG
        for kr in (None, 1e9):
            P, f = modell.bygg(k_ror=kr, vagg_k=k)
            r = P.los(cg * f["G"] + cq * (f["Q"] + f["V"] + f["QT"]) + cs * f["S"])
            wa = wood_armer(*r.m_nod.T)
            mo = np.maximum(-utjamna_linje(r, wa[2], "x", BAND), -utjamna_linje(r, wa[3], "y", BAND))
            d = dict(E=E, fin=fin, ror="fjäder" if kr is None else "styv", ne=int(P.ne))
            for nm, (x, y) in punkter.items():
                d[nm] = float(mo[np.hypot(P.xy[:, 0] - x, P.xy[:, 1] - y) < 600].max()) / 1e3
            d["max"] = float(mo.max()) / 1e3
            d["P10"] = r.reaktioner()["P10"] / 1e3
            out.append(d)
            print(d, flush=True)
            del P, r, wa
json.dump(out, open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "vaggande.json"), "w"),
          indent=1, ensure_ascii=False)
