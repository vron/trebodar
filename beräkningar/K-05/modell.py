"""
K-05: FE-modell av mellanbjälklaget med verklig geometri (bild/geometri.json) och laster enligt laster.py.

    python modell.py            -> lastsummor, jämvikt och stödreaktioner per rör
"""
import json
import os

import numpy as np
from shapely.geometry import LineString, Point

from platta import Platta, Dmat
from ec2 import Betong
import laster as LA

HERE = os.path.dirname(os.path.abspath(__file__))
G = json.load(open(os.path.join(HERE, "bild", "geometri.json"), encoding="utf-8"))
H = LA.H_PLATTA
b = Betong(fck=25)                     # C25/30, styvheten påverkar reaktionerna lite
PLAT = 200.0                           # rörets lastyta i modellen, rör + ingjutning [mm]
A_ROR, L_ROR = 4 * 4 * (80 - 4), 2100  # VKR 80×80×4: area [mm²], längd [mm]
# Dubbelrör: två rör VKR 80×80×4 tätt intill varandra, det andra förskjutet (dx, dy) från modellens rör [mm].
# P7 står i trapphålets hörn och behöver två rörs lastyta för genomstansningen (160 × 80 mm).
DUBBELROR = {"P7": (80.0, 0.0)}
FIN = float(os.environ.get("FIN", 1.0))   # skala på den lokala förfiningen (konvergensstudie)
K_EPS = 0.01                           # bäddmodul för plattan på mark, E/t för cellplasten [N/mm³], mjukt (på säker sida)
# utbredda laster [N/mm²]
GK = (LA.G_BETONG + LA.G_GOLV) * 1e-3          # 4,25 kN/m²
QK = LA.Q_NYTTIG * 1e-3                        # 2,0 kN/m²
QV = LA.Q_VAGG * 1e-3                          # 0,7 kN/m², lätta väggar
GD = 0.91
LASTER = LA.alla()


def rorstod():
    """Rörens stöd: (namn, x, y, bx, by, antal rör), (x, y) = stödets mitt. Ett dubbelrör är ett stöd mitt
    mellan rören med lastytan över båda (rör + ingjutning) och dubbla styvheten."""
    ut = []
    for i, (x, y) in enumerate(G["pelare"], 1):
        n = f"P{i}"
        dx, dy = DUBBELROR.get(n, (0.0, 0.0))
        ut.append((n, x + dx / 2, y + dy / 2, PLAT + abs(dx), PLAT + abs(dy), 2 if n in DUBBELROR else 1))
    return ut


def over_vagg(x, y, marg=175.0):
    return LA.over_vagg(x, y, marg)


def bygg(hmax=200.0, k_ror=None, utan=(), ytterskikt=False, vagg_k=None):
    """Returnerar plattan och lastvektorerna (N):
    Gp  plattans egentyngd och golv (för vindlyft)
    G   alla permanenta laster (Gp + väggar, stolpar, qD2, trappan)
    Q   nyttig last 2,0 kN/m² på hela plattan;  V  lätta väggar 0,7 kN/m²;  QT  trappans nyttiga last
    S   snö via stolpar, väggar och qD2 (S_V, S_M, S_H: per huskropp);  W  vindlyft (dimensionerande, K-01 R_min) på stolpar på plattan och qD2
    Laster över Lecaväggar förs till närmaste upplagslinje (ovan[stödnamn] = (Gk, Sk) i kN).
    ytterskikt=True (kontroll): ytterväggarnas yttre Lecaskikt blir också upplag och lasterna över väggarna
    står där de står."""
    pel = rorstod()
    stod = G["stod"]
    stodlin = [[(a, c), (bb, c)] if ax == "h" else [(c, a), (c, bb)] for ax, c, a, bb in stod]
    linjer = list(stodlin) + [l["pl"] for l in LASTER["linjer"] if l["namn"] == "qD2"]
    ytter = []
    if ytterskikt:                                  # yttre Lecaskiktets mitt, 35 mm in från plattans kant
        for ax, c, a, bb, typ, cs in G["vagg"]:
            if typ != "yttre":
                continue
            co = c - np.sign(cs - c) * (G["E"] - 35)
            ytter.append([(a + 5, co), (bb - 5, co)] if ax == "h" else [(co, a + 5), (co, bb - 5)])
        linjer += ytter
    punkter = [(p["x"], p["y"]) for p in LASTER["punkter"] if p["plats"] != "vägg" or ytterskikt]
    stolpar = [(p["x"], p["y"]) for p in LASTER["punkter"] if p["plats"] == "platta"]
    P = Platta(G["kontur"], hal=[G["hal"]], linjer=linjer + [list(map(tuple, G["mark"])) + [tuple(G["mark"][0])]],
               punkter=punkter, rektanglar=[(x, y, bx, by) for _, x, y, bx, by, _ in pel], hmax=hmax,
               finare=[(x, y, 1.5 * PLAT, 50 * FIN) for _, x, y, _, _, _ in pel] +
                      [(x, y, 300.0, 80.0 * FIN) for pl in stodlin for x, y in pl] +    # väggändar och hörn
                      [(x, y, 400.0, 60.0 * FIN) for x, y in stolpar])                  # stolpar på plattan
    for i, pl in enumerate(stodlin):
        if f"V{i + 1}" not in utan:                 # utan: väggar som plattan lyfter från
            P.stod_linje(f"V{i + 1}", pl, k=vagg_k)     # vagg_k: väggen som fjäder [N/mm per mm] (kontroll)
    for i, pl in enumerate(ytter):                  # fjädrar, så att de kan släppas där de får drag
        P.stod_linje(f"Y{i + 1}", pl, k=1e4)
    k = 210000 * A_ROR / L_ROR if k_ror is None else k_ror
    for n, x, y, bx, by, antal in pel:
        if n not in utan:                           # utan: rör som inte bär (lyfter från plattan)
            P.stod_rekt(n, x, y, bx, by, k=None if k is None else antal * k)
    P.stod_mark("mark", G["mark"], K_EPS)
    P.styvhet(Dmat(b.Ecm * H ** 3 / 12 / (1 - 0.2 ** 2), 0.2))

    sn = {s_["namn"]: s_ for s_ in P.stod}
    linjestod = [(f"V{i + 1}", LineString(pl), np.array(sn[f"V{i + 1}"]["noder"])) for i, pl in enumerate(stodlin)
                 if f"V{i + 1}" in sn]
    ovan = {n: [0.0, 0.0] for n, _, _ in linjestod}

    def nod_last(x, y, plats_):
        """Nod för en last i (x, y): över vägg -> närmaste nod på närmaste upplagslinje, annars närmaste nod."""
        if plats_ != "vägg" or ytterskikt:
            return P.nod(x, y), None
        n, L, nod = min(linjestod, key=lambda t: t[1].distance(Point(x, y)))
        if L.distance(Point(x, y)) > 450:           # väggen är borttagen i modellen (utan)
            assert utan, (x, y)
            return P.nod(x, y), None
        j = nod[np.argmin(np.hypot(P.xy[nod, 0] - x, P.xy[nod, 1] - y))]
        return int(j), n

    nd = P.ndof
    f = {k_: np.zeros(nd) for k_ in ("Gp", "G", "Q", "V", "QT", "S", "W", "S_V", "S_M", "S_H")}
    f["Gp"] = P.last_yta(GK)
    f["G"] += f["Gp"]
    f["Q"] = P.last_yta(QK)
    f["V"] = P.last_yta(QV)
    for p in LASTER["punkter"]:
        j, n = nod_last(p["x"], p["y"], p["plats"])
        f["G"][3 * j] += p["Gk"] * 1e3
        f["S"][3 * j] += p["Sk"] * 1e3
        for kr, v in p["Sb"].items():
            f["S_" + kr][3 * j] += v * 1e3
        if p["plats"] == "platta":
            f["W"][3 * j] += p["Wd"] * 1e3
        if n:
            ovan[n][0] += p["Gk"]; ovan[n][1] += p["Sk"]
    for w in LASTER["vaggar"]:
        for s in w["prov"]:
            j, n = nod_last(s["x"], s["y"], s["plats"])
            f["G"][3 * j] += s["G"] * 1e3
            f["S"][3 * j] += s["S"] * 1e3
            f["S_" + s["kropp"]][3 * j] += s["S"] * 1e3
            if n:
                ovan[n][0] += s["G"]; ovan[n][1] += s["S"]
    for l in LASTER["linjer"]:
        f["G"] += P.last_linje(l["gk"], l["pl"])
        fs = P.last_linje(l["sk"], l["pl"])
        f["S"] += fs
        for kr, v in l["skropp"].items():
            f["S_" + kr] += v * fs
        f["QT"] += P.last_linje(l["qk"], l["pl"])
        f["W"] += P.last_linje(l["wd"], l["pl"])
    P.ovan = ovan
    assert abs((f["S_V"] + f["S_M"] + f["S_H"] - f["S"]).sum()) < 1e-6 * abs(f["S"].sum())
    return P, f


if __name__ == "__main__":
    import sys
    P, f = bygg(k_ror=float(sys.argv[1]) if len(sys.argv) > 1 else None)
    print(f"element {P.ne}, noder {P.nn}")
    tot = {k: v[0::3].sum() / 1e3 for k, v in f.items()}
    print("total last kN:", {k: round(v, 1) for k, v in tot.items()})
    res = P.los_flera([f["G"], f["S"]])
    for nm, r in zip("GS", res):
        R = r.reaktioner()
        print(nm, "jämvikt:", round(sum(R.values()) / 1e3, 1), " rör:", round(sum(v for k, v in R.items() if k[0] == "P") / 1e3, 1),
              " väggar:", round(sum(v for k, v in R.items() if k[0] == "V") / 1e3, 1), " mark:", round(R["mark"] / 1e3, 1))
    print("ovanifrån direkt på väggar (Gk, Sk):", {k: [round(x, 1) for x in v] for k, v in P.ovan.items() if v[0]})
