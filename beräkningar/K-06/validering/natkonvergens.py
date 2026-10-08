"""Nätkänslighet för den samverkande modellen: grundnät 200 mm (som i beräkningen) mot 140 mm, last G + S + Q
(kvasipermanent, långtid). Jämför största cellplasttryck, rörlaster och sättningar. Skriver natkonvergens.json."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import indata as I
import modell06 as M
from berakning06 import k_mark
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
plint = json.load(open(os.path.join(HERE, "kontroll06.json")))["L300"]["plint"]
out = []
for hmax in (200.0, 140.0):
    S = M.System("L300", plint, "S100", "S200", "lång", hmax=hmax, k_mark=k_mark("lång"))
    F, _ = M.laster(S.Pt, S.Pb)
    f = F["G"] + 0.481 * (sum(F["Q"]) + F["Qb"]) + 0.1 * F["S"]
    u = S.los(f)
    p = S.tryck(u)
    kr = S.krafter(u)
    out.append(dict(hmax=hmax, ne=int(S.Pb.ne), pmax=float(p.max()), wmax=float(u[S.nt:][0::3].max()),
                    ror={k: v / 1e3 for k, v in kr.items() if k[0] == "P"}))
    print(out[-1]["hmax"], out[-1]["ne"], round(out[-1]["pmax"], 1), round(out[-1]["wmax"], 2), flush=True)
    del S
json.dump(out, open(os.path.join(HERE, "natkonvergens.json"), "w"), indent=1)
