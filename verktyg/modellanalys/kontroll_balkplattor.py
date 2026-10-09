"""
Kontroll av balkplåtarnas skärfiler (modeller/balkplattor) mot K-01: hålens lägen och diameter.

    ./.venv/bin/python kontroll_balkplattor.py

Läser varje plåts STEP-fil (exakt B-rep: cylindriska hålytor med axel och radie) och DXF-fil (cirklar i lagret
HAL, ytterkontur i lagret KONTUR) och jämför med K-01:s hålbilder (beräkningar/K-01/halbild_*.csv) och med
skruvens håldiameter och plåtens mått i K-01:s indata.toml. Läser filerna oberoende av generera.py.
Skriver "allt stämmer" eller avvikelserna.
"""
import csv
import math
import re
import sys
import tomllib
from pathlib import Path

from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.BRepBndLib import BRepBndLib
from OCP.Bnd import Bnd_Box
from OCP.GeomAbs import GeomAbs_Cylinder
from OCP.IFSelect import IFSelect_RetDone
from OCP.STEPControl import STEPControl_Reader
from OCP.TopAbs import TopAbs_FACE
from OCP.TopExp import TopExp_Explorer
from OCP.TopoDS import TopoDS

ROT = Path(__file__).resolve().parent.parent.parent
K01 = ROT / "beräkningar" / "K-01"
PLATAR = ROT / "modeller" / "balkplattor"
IN = tomllib.loads((K01 / "indata.toml").read_text(encoding="utf-8"))
B, T = float(IN["geometri"]["b"]), float(IN["geometri"]["t_pl"])
D = float(IN["skruv"]["hal"])
KORT = {"nockbalk": "NB", "dalbalk": "DB"}
TOL = 0.01  # mm


def halbilder():
    """{plåtnamn: (längd, [(x, y), ...])} enligt K-01, x från plåtens ände."""
    ut = {}
    for fil in sorted(K01.glob("halbild_*.csv")):
        m = re.match(r"halbild_(nockbalk|dalbalk)(\d+)\.csv", fil.name)
        rader = [r for r in fil.read_text(encoding="utf-8").splitlines() if not r.startswith("#")]
        for r in csv.DictReader(rader, delimiter=";"):
            a, c = float(r["plat_fran"]), float(r["plat_till"])
            for lage, kol in (("O", "y_over"), ("U", "y_under")):
                namn = f"{KORT[m.group(1)]}{m.group(2)}-{r['bit']}-{lage}"
                ut.setdefault(namn, (c - a, []))[1].append((float(r["x_mm"]) - a, float(r["y_over" if lage == "O" else "y_under"])))
    return ut


def step_hal(fil):
    """Hålen i STEP-filen: (x, y, diameter) per cylindrisk yta, och plåtens bbox."""
    rd = STEPControl_Reader()
    assert rd.ReadFile(str(fil)) == IFSelect_RetDone, fil
    rd.TransferRoots()
    s = rd.OneShape()
    box = Bnd_Box()
    BRepBndLib.Add_s(s, box)
    hal = []
    ex = TopExp_Explorer(s, TopAbs_FACE)
    while ex.More():
        ad = BRepAdaptor_Surface(TopoDS.Face(ex.Current()))
        if ad.GetType() == GeomAbs_Cylinder:
            c = ad.Cylinder()
            ax, p = c.Axis().Direction(), c.Location()
            assert abs(abs(ax.Z()) - 1) < 1e-9, "hålet är inte vinkelrätt mot plåten"
            hal.append((p.X(), p.Y(), 2 * c.Radius()))
        ex.Next()
    lo, hi = box.CornerMin(), box.CornerMax()
    return hal, (lo.X(), lo.Y(), lo.Z(), hi.X(), hi.Y(), hi.Z())


def dxf_hal(fil):
    """Cirklar i lagret HAL och ytterkonturens hörn ur DXF-filen (enkel läsning av gruppkoder)."""
    rader = fil.read_text(encoding="utf-8", errors="replace").splitlines()
    par = [(rader[i].strip(), rader[i + 1].strip()) for i in range(0, len(rader) - 1, 2)]
    ents, cur, i_ent = [], None, False
    for k, v in par:
        if k == "0":
            if cur:
                ents.append(cur)
            cur = {"typ": v, "kod": []} if i_ent else None
            if v == "SECTION":
                i_ent = None
        elif k == "2" and i_ent is None:
            i_ent = v == "ENTITIES"
        elif cur is not None:
            cur["kod"].append((k, v))
    cirklar, kontur = [], []
    for e in ents:
        d = {}
        for k, v in e["kod"]:
            d.setdefault(k, []).append(v)
        lager = d.get("8", [""])[0]
        if e["typ"] == "CIRCLE" and lager == "HAL":
            cirklar.append((float(d["10"][0]), float(d["20"][0]), 2 * float(d["40"][0])))
        elif e["typ"] == "LWPOLYLINE" and lager == "KONTUR":
            kontur = list(zip(map(float, d["10"]), map(float, d["20"])))
    return cirklar, kontur


def jamfor(namn, kalla, krav, hal):
    fel = []
    if len(hal) != len(krav):
        fel.append(f"{namn} ({kalla}): {len(hal)} hål, K-01 har {len(krav)}")
    for x, y, dia in hal:
        if abs(dia - D) > TOL:
            fel.append(f"{namn} ({kalla}): hål Ø{dia:.2f} vid ({x:.1f}; {y:.1f}), ska vara Ø{D:g}")
    kvar = list(hal)
    for x, y in krav:
        j = min(range(len(kvar)), key=lambda k: math.hypot(kvar[k][0] - x, kvar[k][1] - y)) if kvar else None
        if j is None or math.hypot(kvar[j][0] - x, kvar[j][1] - y) > TOL:
            fel.append(f"{namn} ({kalla}): hål saknas vid ({x:.0f}; {y:.0f})")
        else:
            kvar.pop(j)
    return fel


K = halbilder()
filer = sorted(p.stem for p in PLATAR.glob("*.step"))
fel = [f"{n}: finns i K-01 men inte som fil" for n in sorted(set(K) - set(filer))]
fel += [f"{n}: fil utan hålbild i K-01" for n in sorted(set(filer) - set(K))]
n_hal = 0
for namn in sorted(set(K) & set(filer)):
    L, krav = K[namn]
    sh, (x0, y0, z0, x1, y1, z1) = step_hal(PLATAR / f"{namn}.step")
    if max(abs(x0), abs(y0), abs(z0), abs(x1 - L), abs(y1 - B), abs(z1 - T)) > TOL:
        fel.append(f"{namn} (STEP): plåten är {x1 - x0:.1f} × {y1 - y0:.1f} × {z1 - z0:.1f}, ska vara {L:.0f} × {B:.0f} × {T:.0f}")
    fel += jamfor(namn, "STEP", krav, sh)
    dh, kontur = dxf_hal(PLATAR / f"{namn}.dxf")
    if sorted(kontur) != sorted([(0.0, 0.0), (L, 0.0), (L, B), (0.0, B)]):
        fel.append(f"{namn} (DXF): ytterkonturen {kontur} stämmer inte med {L:.0f} × {B:.0f}")
    fel += jamfor(namn, "DXF", krav, dh)
    n_hal += len(krav)

print(f"{len(filer)} plåtar, {n_hal} hål Ø{D:g} enligt K-01 ({IN['skruv']['produkt']}).")
if fel:
    print(f"{len(fel)} avvikelser:")
    print("\n".join("  " + f for f in fel))
    sys.exit(1)
print("Allt stämmer: STEP- och DXF-filernas hål har K-01:s lägen och diameter, och plåtarna har rätt mått.")
