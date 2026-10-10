"""Kontroll av mellanbjälklagets geometri i K-05 (beräkningar/K-05/bild/geometri.json) mot Onshape-modellen.

    .venv/bin/python kontroll_geometri05.py

geometri.json är K-05:s egen källfil och används av K-05, K-06 och R-03. Den uppdateras för hand. Den här
kontrollen läser modellen (modeller/trebodar.step), räknar fram kontur, hål, väggar (vagg, stod), rör, mark, fria
kanter och E på samma sätt som i källfilen och redovisar skillnaderna. Den skriver ingenting.
stolpar, balkar, takstol och linjelaster i källfilen beskriver trästommen på plan 1 och kontrolleras inte här.

Koordinater i mm, x åt höger, y uppåt, origo i skärningen mellan plattkanterna x = 0 och y = 0 (plattans nedre
vänstra hörn, som i K-05).

vagg: [riktning, centrumlinje, a, b, "yttre"/"inre", upplagslinje]. a och b är den vinkelräta väggens centrumlinje
i hörn och T-anslutningar, och väggens fysiska ände vid en fri ände (öppning), mätt strax under bjälklaget.
Ytterväggarnas upplagslinje ligger UPPL in från centrumlinjen, innerväggarnas i centrumlinjen.
"""
import json
import os
import sys

import numpy as np
from shapely.geometry import Polygon

HERE = os.path.dirname(os.path.abspath(__file__))
ROT = os.path.abspath(os.path.join(HERE, "..", ".."))
KALLA = os.path.join(ROT, "beräkningar", "K-05", "bild", "geometri.json")
sys.path.insert(0, HERE)
from geometri import Plan, linjeprob, snitt  # noqa: E402
from jamfor import jamfor, redovisa  # noqa: E402
from modell import Modell  # noqa: E402

UPPL = 100.0                 # ytterväggarnas upplagslinje innanför väggens centrumlinje [mm]
Z_VAGG = -200.0              # nivå för väggarnas ändar och öppningar: strax under bjälklaget (uk -150)
Z_MITT = -1000.0             # nivå för väggarnas centrumlinje

m = Modell(tyst=True)
_pl = [d for d in m.delar if d.namn == "Mittenplatta"][0]
O = np.array([_pl.bbox[0], _pl.bbox[1], _pl.bbox[5]])          # origo och bjälklagets överkant
LECA = m.valj("Bkärna,Isoskal")


def r3(v):
    """Flyttal med högst tre decimaler (koden räknar med flyttal i geometri.json)."""
    return round(float(v), 3)


def heltal(v):
    v = round(float(v), 3)
    return int(v) if v == int(v) else v


def prob(p1, p2, z, delar=LECA):
    """Sträckor [(t0, t1)] längs linjen p1→p2 (2D, K-05) på nivån z, sammanslagna, t i mm från p1."""
    P1 = np.r_[p1, z] + O
    P2 = np.r_[p2, z] + O
    iv = sorted((t0, t1) for t0, t1, *_ in linjeprob(m, delar, P1, P2))
    ut = []
    for a, b in iv:
        if ut and a <= ut[-1][1] + 0.01:
            ut[-1][1] = max(ut[-1][1], b)
        else:
            ut.append([a, b])
    return ut


gammal = json.load(open(KALLA, encoding="utf-8"))

# ---------------------------------------------------------------- platta och trapphål
pl = Plan.tolka(f"z={O[2] - 75}").flytta(O[0], O[1])
yta = [s.yta for s in snitt(m, [_pl], pl)][0]
yttre = np.array(yta.exterior.coords)[:-1]
inre = np.array(yta.interiors[0].coords)[:-1]
kontur = [[heltal(v) for v in yttre[np.argmin(np.hypot(*(yttre - p).T))]] for p in np.array(gammal["kontur"], float)]
assert len(yttre) == len(kontur) and abs(Polygon(kontur).area - Polygon(yttre).area) < 1, \
    "konturen har ändrat form – kontrollera hörnens ordning"
hx0, hy0 = inre.min(0)
hx1, hy1 = inre.max(0)
hal = [[r3(hx0), r3(hy0)], [r3(hx1), r3(hy0)], [r3(hx1), r3(hy1)], [r3(hx0), r3(hy1)]]

# ---------------------------------------------------------------- rör (numreringen P1–P19 behålls)
ror = [d for d in m.delar if d.namn.startswith("K Pillar")]
mitt = np.array([[(d.bbox[0] + d.bbox[3]) / 2 - O[0], (d.bbox[1] + d.bbox[4]) / 2 - O[1]] for d in ror])
pelare, tagna = [], set()
for x, y in gammal["pelare"]:
    j = int(np.argmin(np.hypot(mitt[:, 0] - x, mitt[:, 1] - y)))
    assert j not in tagna and np.hypot(*(mitt[j] - (x, y))) < 150, (x, y)
    tagna.add(j)
    pelare.append([r3(mitt[j, 0]), r3(mitt[j, 1])])
assert len(tagna) == len(ror)

# ---------------------------------------------------------------- Lecaväggar
G0 = gammal["vagg"]
cn = []                                           # exakt centrumlinje per vägg
for ax, c, a, b, *_ in G0:
    s = (a + b) / 2
    p1, p2 = ((s, c - 400), (s, c + 400)) if ax == "h" else ((c - 400, s), (c + 400, s))
    iv = prob(p1, p2, Z_MITT)
    lo, hi = c - 400 + iv[0][0], c - 400 + iv[-1][1]
    assert abs(hi - lo - 350) < 0.5, (ax, c, lo, hi)
    cn.append((lo + hi) / 2)


def hornvagg(i, v):
    """Index för den vinkelräta vägg vars centrumlinje väggen i:s ände v ligger på, annars None."""
    ax, c = G0[i][0], G0[i][1]
    for j, (ax2, c2, a2, b2, *_) in enumerate(G0):
        if ax2 != ax and abs(c2 - v) < 1 and a2 - 1 <= c <= b2 + 1:
            return j
    return None


vagg = []
for i, (ax, c, a, b, typ, cs) in enumerate(G0):
    c_ = cn[i]
    ander = []
    for k, v in ((0, a), (1, b)):
        j = hornvagg(i, v)
        if j is not None:
            ander.append(cn[j])
            continue
        # fri ände: väggens fysiska ände på linjen, strax under bjälklaget
        p1, p2 = ((min(a, b) - 1500, c_), (max(a, b) + 1500, c_)) if ax == "h" else ((c_, min(a, b) - 1500), (c_, max(a, b) + 1500))
        iv = [(min(a, b) - 1500 + t0, min(a, b) - 1500 + t1) for t0, t1 in prob(p1, p2, Z_VAGG)]
        s = (a + b) / 2
        bit = [t for t in iv if t[0] - 200 <= s <= t[1] + 200] or [min(iv, key=lambda t: min(abs(t[0] - s), abs(t[1] - s)))]
        ander.append(bit[0][0] if k == 0 else bit[0][1])
    up = c_ + np.sign(cs - c) * UPPL if typ == "yttre" else c_
    vagg.append([ax, r3(c_), r3(ander[0]), r3(ander[1]), typ, r3(up)])

# upplagslinjernas ändar följer den vinkelräta väggens upplagslinje (som tidigare)
stod = []
for i, w in enumerate(vagg):
    a_, b_ = w[2], w[3]
    for k in (2, 3):
        j = hornvagg(i, G0[i][k])
        if j is not None:
            if k == 2:
                a_ = vagg[j][5]
            else:
                b_ = vagg[j][5]
    stod.append([w[0], w[5], a_, b_])

# ---------------------------------------------------------------- plattan på mark och fria kanter
yH3 = max(w[1] for w in vagg if w[0] == "h" and w[2] < 1000)                  # V3
xV3 = min(w[1] for w in vagg if w[0] == "v" and 4000 < w[1] < 5000 and w[3] > yH3)   # V20
mark = [[0.0, yH3], [xV3, yH3], [xV3, 11010.0], [4310.0, 11010.0], [4310.0, 15900.0], [0.0, 15900.0]]


def oppningar(y_lin, c, x0, x1):
    """Öppningar i väggen (centrumlinje c) mellan x0 och x1 strax under bjälklaget, som sträckor på plattkanten y_lin."""
    iv = [(x0 + t0, x0 + t1) for t0, t1 in prob((x0, c), (x1, c), Z_VAGG)]
    return [[[r3(b), y_lin], [r3(a2), y_lin]] for (a, b), (a2, b2) in zip(iv, iv[1:]) if a2 - b > 1]


v18, v17 = vagg[17][1], vagg[16][1]                                           # hörnen vid fasaden med öppningar
fria = oppningar(0, vagg[9][1], v18, v17) + oppningar(1000, vagg[8][1], vagg[16][1], vagg[13][1])

E = r3(vagg[20][1])                                                          # V21: centrumlinjen innanför plattkanten
modell = dict(kontur=kontur, hal=hal, vagg=vagg, stod=stod, pelare=pelare, mark=mark, fria_kanter=fria, E=E)
if __name__ == "__main__":
    print(f"modell: {m.fil.name} ({m.hash}), origo {O[:2].round(3).tolist()}, bjälklagets ök z = {O[2]:.3f}")
    print("trapphål", hal)
    for i, w in enumerate(vagg, 1):
        print(f"  V{i:<3} {w}  upplag {stod[i - 1]}")
    for i, p in enumerate(pelare, 1):
        print(f"  P{i:<3} {p}")
    print("mark", mark, f"{Polygon(mark).area / 1e6:.2f} m²")
    print("fria kanter", fria)
    print("E", E)
    kalla = {k: gammal[k] for k in modell}
    sys.exit(redovisa("K-05 bild/geometri.json", jamfor(kalla, modell)))
