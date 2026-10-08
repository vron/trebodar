"""Kontroll av lastvägen över Lecaväggarna. Huvudmodellen: plattan vilar på ytterväggarnas inre Lecaskikt och
lasterna som står över väggarna läggs på upplagslinjen. Här: också det yttre skiktet bär (bara tryck, iterativt) och
lasterna står där de står. Kombination 6.10b med snö som huvudlast, full nyttig last. Skriver ytterskikt.json."""
import os, sys, json; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from modell import bygg, b, H
from platta import Dmat, wood_armer
from omhyllande import utjamna_linje, ULS
import laster as LA

BAND = float(os.environ.get("BAND", 250))
cg, cq, cs = ULS["6.10b S"]
pv = np.array([(p["x"], p["y"]) for p in LA.alla()["punkter"] if p["plats"] == "vägg"])
out = {}
for ys in (False, True):
    P, f = bygg(k_ror=None, ytterskikt=ys)
    F = cg * f["G"] + cq * (f["Q"] + f["V"] + f["QT"]) + cs * f["S"]
    D = Dmat(b.Ecm * H ** 3 / 12 / (1 - 0.2 ** 2), 0.2)
    slappt = 0
    for it in range(30):
        r = P.los(F)
        drag = {n for s_ in P.stod if s_["namn"].startswith("Y") for n in s_["noder"]
                if 3 * n in P.springs and r.R[3 * n] < 0}
        if not drag:
            break
        for n in drag:
            del P.springs[3 * n]
        slappt += len(drag)
        P.styvhet(D)
    wa = wood_armer(*r.m_nod.T)
    mo = np.maximum(-utjamna_linje(r, wa[2], "x", BAND), -utjamna_linje(r, wa[3], "y", BAND))
    mu = np.maximum(utjamna_linje(r, wa[0], "x", BAND), utjamna_linje(r, wa[1], "y", BAND))
    nara = np.min(np.hypot(P.xy[:, None, 0] - pv[None, :, 0], P.xy[:, None, 1] - pv[None, :, 1]), axis=1) < 600
    Rn = r.reaktioner()
    i = int(np.argmax(np.where(nara, mo, -1e9)))
    zoner = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resultat.json")))["zoner"]
    zon = [z["namn"] for z in zoner if z["bounds"][0] <= P.xy[i, 0] <= z["bounds"][2] and z["bounds"][1] <= P.xy[i, 1] <= z["bounds"][3]]
    d = dict(mo=float(mo.max()) / 1e3, mu=float(mu.max()) / 1e3, mo_nara=float(mo[nara].max()) / 1e3,
             mu_nara=float(mu[nara].max()) / 1e3, Y=sum(v for k, v in Rn.items() if k.startswith("Y")) / 1e3,
             V=sum(v for k, v in Rn.items() if k.startswith("V")) / 1e3, iter=it, slappta=slappt,
             P=max(v for k, v in Rn.items() if k.startswith("P")) / 1e3, xy=[float(v) for v in P.xy[i]], zon=zon)
    out["med" if ys else "utan"] = d
    print(ys, d, flush=True)
json.dump(out, open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ytterskikt.json"), "w"), indent=1)
