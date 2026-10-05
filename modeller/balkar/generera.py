"""
Kompletta 3D-modeller av nock- och dalbalkarna (K-01): en STEP-sammanställning per balk.

    python generera.py

Varje balk består av separata delar med namn och färg:
    limträ 200×170 i hel längd, stålplåtar i över- och underkant och distansreglar 200×10 där plåt saknas.
Stålplåtarna läses in från ../balkplattor/*.step, så att geometrin är exakt densamma som i skärfilerna
(kör ../balkplattor/generera.py först). Balklängd, plåtlägen och distansreglarnas glipa läses från
../../beräkningar/K-01/indata.toml och hålbilderna.

Koordinater (mm): x längs balken från vänster ände, y = 0 vid balkens framsida, z = 0 vid balkens underkant.
Kräver: pip install cadquery
"""
import csv
import tomllib
from pathlib import Path

import cadquery as cq

HERE = Path(__file__).parent
ROT = HERE.parent.parent
K01 = ROT / "beräkningar" / "K-01"
PLATAR = HERE.parent / "balkplattor"
IN = tomllib.loads((K01 / "indata.toml").read_text(encoding="utf-8"))
B = IN["geometri"]["b"]                    # 200
T = IN["geometri"]["t_pl"]                 # 10
HW = IN["geometri"]["h_tra"]               # 170
GLIPA = IN["distans"]["glipa"]             # 5
KORT = {"nock": "NB", "dal": "DB"}

TRA = cq.Color(0.86, 0.70, 0.45)           # limträ
DIST = cq.Color(0.95, 0.88, 0.70)          # distansregel
STAL = cq.Color(0.45, 0.48, 0.52)          # stål


def bitar(namn):
    """Plåtbitar (nr, från, till) enligt hålbilden för balken."""
    fil = K01 / f"halbild_{namn.lower().replace(' ', '')}.csv"
    rader = [r for r in fil.read_text(encoding="utf-8").splitlines() if not r.startswith("#")]
    ut = {}
    for r in csv.DictReader(rader, delimiter=";"):
        ut[int(r["bit"])] = (float(r["plat_fran"]), float(r["plat_till"]))
    return [(nr, *ut[nr]) for nr in sorted(ut)]


def lador(L, b):
    """Sträckor utan plåt, med glipa mot plåtändarna."""
    fria, x = [], 0.0
    for _, a, c in b:
        if a - x > 0:
            fria.append((x, a - (GLIPA if a < L else 0)))
        x = c + (GLIPA if c < L and c > 0 else 0)
    if L - x > 0:
        fria.append((x, L))
    return [(a, c) for a, c in fria if c - a > 1]


def box(L, b, h):
    return cq.Workplane("XY").box(L, b, h, centered=False).val()


for balk in IN["balk"]:
    namn, L = balk["namn"], float(balk["total"])
    kort = f"{KORT[balk['typ']]}{namn.split()[-1]}"
    b = bitar(namn)
    assy = cq.Assembly(name=kort)
    assy.add(box(L, B, HW), name=f"{kort} limtra GL30c {B}x{HW}", color=TRA, loc=cq.Location((0, 0, T)))
    for nr, a, c in b:
        for lage, z in (("U", 0), ("O", T + HW)):
            p = cq.importers.importStep(str(PLATAR / f"{kort}-{nr}-{lage}.step")).val()
            assert abs(p.BoundingBox().xlen - (c - a)) < 1e-6
            assy.add(p, name=f"{kort}-{nr}-{lage}", color=STAL, loc=cq.Location((a, 0, z)))
    for i, (a, c) in enumerate(lador(L, b), 1):
        for lage, z in (("U", 0), ("O", T + HW)):
            assy.add(box(c - a, B, T), name=f"{kort} distansregel {i}-{lage}", color=DIST, loc=cq.Location((a, 0, z)))
    assy.export(str(HERE / f"{kort}.step"))
    print(f"{kort}: {L:.0f} mm, plåt {[(a, c) for _, a, c in b]}, distans {lador(L, b)}")
