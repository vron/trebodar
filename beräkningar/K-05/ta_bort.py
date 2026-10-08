"""Screening: vad händer om rör tas bort? Allt annat lika (armering, zoner). Kör efter berakning.py:
    python ta_bort.py 2,6,13
"""
import json, math, sys, copy
import numpy as np
from shapely.geometry import Polygon, box
import modell
from ec2 import Betong, Stal, Armering, Lager, MRd, vRdc
from omhyllande import kor, utjamna_linje

B = Betong(fck=25); S = Stal(); H = 150.0; C_UK, C_OK = 20, 25
R0 = json.load(open("resultat.json"))
ZON = R0["zoner"]
PEL0 = [tuple(p) for p in modell.G["pelare"]]
hal = Polygon(modell.G["hal"])

def arm(extra=None):
    a = Armering(H, ux=Lager(10, 150, H - C_UK - 5), uy=Lager(10, 150, H - C_UK - 15),
                 ox=Lager(8, 150, C_OK + 4), oy=Lager(8, 150, C_OK + 12))
    if extra:
        dia, cc = extra
        As = a.ox.As + math.pi * dia ** 2 / 4 / cc
        a.ox = Lager(math.sqrt(4 * As * cc / math.pi), cc, C_OK + dia / 2)
        a.oy = Lager(math.sqrt(4 * As * cc / math.pi), cc, C_OK + dia + dia / 2)
    return a

def mrd_ok(a):
    return MRd(a.ox.As, H - a.ox.y, B, S)[0], MRd(a.oy.As, H - a.oy.y, B, S)[0]

def u1(x, y, c, d):
    yta = box(x - c / 2, y - c / 2, x + c / 2, y + c / 2)
    per1 = yta.buffer(2 * d, quad_segs=32).exterior
    u = per1.length
    if hal.distance(yta) <= 6 * d:
        vin = [math.atan2(py - y, px - x) for px, py in hal.exterior.coords]
        ref = math.atan2(hal.centroid.y - y, hal.centroid.x - x)
        rel = [(v - ref + math.pi) % (2 * math.pi) - math.pi for v in vin]
        a0, a1 = min(rel) + ref, max(rel) + ref
        kon = Polygon([(x, y)] + [(x + 1e5 * math.cos(a), y + 1e5 * math.sin(a)) for a in np.linspace(a0, a1, 60)])
        u -= per1.intersection(kon).length
    return u

def stans_basta(VEd, x, y):
    """Minsta utnyttjande utan huvudplåt (rör direkt, tillägg upp till Ø10 s150)."""
    best = 9
    for t in (None, (8, 150), (10, 150)):
        a = arm(t); d = H - (a.ox.y + a.oy.y) / 2
        rho = min(math.sqrt(a.ox.As / (H - a.ox.y) * a.oy.As / (H - a.oy.y)), 0.02)
        beta = 1.4 if hal.distance(box(x - 40, y - 40, x + 40, y + 40)) < 2 * d else 1.15
        best = min(best, beta * VEd / (u1(x, y, 80, d) * d) / vRdc(rho, d, B))
    return best

mesh_x, mesh_y = mrd_ok(arm())
zon_x, zon_y = mrd_ok(arm((8, 150)))
def i_zon(xy):
    m = np.zeros(len(xy), bool)
    for z in ZON:
        x0, y0, x1, y1 = z["bounds"]
        m |= (xy[:, 0] >= x0) & (xy[:, 0] <= x1) & (xy[:, 1] >= y0) & (xy[:, 1] <= y1)
    return m

if __name__ == "__main__":
    ut = {}
    fall = [tuple(int(v) for v in a.split(",")) for a in sys.argv[1:]] or [(i,) for i in range(1, len(PEL0) + 1)]
    for i in fall:
        modell.G["pelare"] = [p for j, p in enumerate(PEL0, 1) if j not in i]
        namn = [j for j in range(1, len(PEL0) + 1) if j not in i]
        P1, e1, lf1 = kor(None); P2, e2, lf2 = kor(1e9)
        env = {k: (np.maximum(e1[k], e2[k]) if k in ("mux", "muy") else np.minimum(e1[k], e2[k])) for k in ("mux", "muy", "mox", "moy")}
        r0 = lf1["G"]
        sm = {k: utjamna_linje(r0, env[k], "x" if k.endswith("x") else "y", 500.0) for k in env}
        uk = max(sm["mux"].max(), sm["muy"].max())
        z = i_zon(P1.xy)
        ok_ut = max((-sm["mox"][~z] / mesh_x).max(), (-sm["moy"][~z] / mesh_y).max())
        ok_in = max((-sm["mox"][z] / zon_x).max(), (-sm["moy"][z] / zon_y).max())
        ny_yta = float(((np.maximum(-sm["mox"] / mesh_x, -sm["moy"] / mesh_y) > 1) & ~z).sum())
        stans = {}
        for k, (x, y) in zip(namn, modell.G["pelare"]):
            V = max(e1["R"][f"P{namn.index(k) + 1}"], e2["R"][f"P{namn.index(k) + 1}"])
            stans[f"P{k}"] = (V / 1e3, stans_basta(V, x, y))
        worst = max(stans.items(), key=lambda kv: kv[1][1])
        ut[",".join(map(str, i))] = dict(uk=uk / 1e3, ok_ut=ok_ut, ok_in=ok_in, nya_noder=ny_yta, stans_max=worst[0], VEd=worst[1][0],
                     stans_utn=worst[1][1], stans=stans)
        print(f"utan P{i}: uk {uk/1e3:.1f} kNm/m, ök utanför zoner {ok_ut*100:.0f} % ({ny_yta:.0f} noder nya), i zoner {ok_in*100:.0f} %, "
              f"stans värst {worst[0]} {worst[1][0]:.1f} kN {worst[1][1]*100:.0f} %", flush=True)
        json.dump(ut, open("ta_bort_kombi.json", "w"), indent=1)
