"""
Stålplåtar till nock- och dalbalkarna (K-01): en STEP-fil och en DXF-fil per plåt.

    python generera.py

Läser hålbilderna ../../beräkningar/K-01/halbild_*.csv och skriver en fil per plåtbit och läge
(över- respektive underplåt). Plåten ritas sedd ovanifrån i monterat läge:
    x = 0 vid plåtens ände närmast balkens vänstra ände, längs balken
    y = 0 vid plåtens kant mot balkens framsida
    z = 0 plåtens undersida, z = t plåtens ovansida
Kräver: pip install cadquery ezdxf
"""
import csv
import math
import re
from pathlib import Path

import cadquery as cq
import ezdxf
from OCP.IFSelect import IFSelect_RetDone
from OCP.Interface import Interface_Static
from OCP.STEPControl import STEPControl_AsIs, STEPControl_Writer

HERE = Path(__file__).parent
K01 = HERE.parent.parent / "beräkningar" / "K-01"
B, T, D = 200.0, 10.0, 10.5          # plåtens bredd och tjocklek, håldiameter [mm]
KORT = {"nockbalk": "NB", "dalbalk": "DB"}


def las(fil):
    rader = [r for r in fil.read_text(encoding="utf-8").splitlines() if not r.startswith("#")]
    bitar = {}
    for r in csv.DictReader(rader, delimiter=";"):
        b = bitar.setdefault(int(r["bit"]), dict(fran=float(r["plat_fran"]), till=float(r["plat_till"]), hal=[]))
        b["hal"].append((float(r["x_mm"]), float(r["y_over"]), float(r["y_under"])))
    return bitar


def plat(L, hal):
    s = cq.Workplane("XY").box(L, B, T, centered=False)
    return s.faces(">Z").workplane(origin=(0, 0, T)).pushPoints(hal).hole(D).val()


def step(shape, namn, fil):
    w = STEPControl_Writer()
    Interface_Static.SetCVal_s("write.step.schema", "AP214IS")
    Interface_Static.SetCVal_s("write.step.unit", "MM")
    Interface_Static.SetCVal_s("write.step.product.name", namn)
    w.Transfer(shape.wrapped, STEPControl_AsIs)
    assert w.Write(str(fil)) == IFSelect_RetDone
    txt = re.sub(r"PRODUCT\('[^']*','[^']*'", f"PRODUCT('{namn}','{namn}'", fil.read_text(), count=1)
    fil.write_text(txt)


def dxf(L, hal, fil):
    doc = ezdxf.new("R2010", setup=False)
    doc.units = ezdxf.units.MM
    msp = doc.modelspace()
    msp.add_lwpolyline([(0, 0), (L, 0), (L, B), (0, B)], close=True, dxfattribs={"layer": "KONTUR"})
    for x, y in hal:
        msp.add_circle((x, y), D / 2, dxfattribs={"layer": "HAL"})
    doc.saveas(fil)


rader = []
for fil in sorted(K01.glob("halbild_*.csv")):
    m = re.match(r"halbild_(nockbalk|dalbalk)(\d+)\.csv", fil.name)
    balk = f"{KORT[m.group(1)]}{m.group(2)}"
    for nr, b in las(fil).items():
        L = b["till"] - b["fran"]
        for lage, kol, txt in (("O", 1, "överplåt"), ("U", 2, "underplåt")):
            hal = [(h[0] - b["fran"], h[kol]) for h in b["hal"]]
            assert all(0 < x < L and 0 < y < B for x, y in hal)
            namn = f"{balk}-{nr}-{lage}"
            s = plat(L, hal)
            # kontroll: volym och antal hål
            V = L * B * T - len(hal) * math.pi * (D / 2) ** 2 * T
            assert abs(s.Volume() - V) / V < 1e-6, (namn, s.Volume(), V)
            assert sum(1 for f in s.Faces() if f.geomType() == "CYLINDER") == len(hal)
            step(s, namn, HERE / f"{namn}.step")
            dxf(L, hal, HERE / f"{namn}.dxf")
            rader.append((namn, f"{m.group(1).capitalize()} {m.group(2)}", nr, txt, L, b["fran"], b["till"], len(hal),
                          s.Volume() * 7.85e-6))
            print(f"{namn}: {L:.0f} × {B:.0f} × {T:.0f} mm, {len(hal)} hål")

# förteckning
tab = ["| Fil | Balk | Bit | Läge | Längd (mm) | Läge i balken (mm) | Hål | Vikt (kg) |", "|---|---|---|---|---|---|---|---|"]
for n, balk, nr, txt, L, a, b, nh, kg in rader:
    tab.append(f"| `{n}` | {balk} | {nr} | {txt} | {L:.0f} | {a:.0f}–{b:.0f} | {nh} | {kg:.1f} |".replace(".", ","))
tab.append(f"| **Summa** | | | | **{sum(r[4] for r in rader):.0f}** | | **{sum(r[7] for r in rader)}** | **{sum(r[8] for r in rader):.0f}** |")
readme = HERE / "README.md"
txt = readme.read_text(encoding="utf-8")
readme.write_text(txt[: txt.index("## Förteckning")] + "## Förteckning\n\n" + "\n".join(tab) + "\n", encoding="utf-8")
print(f"{len(rader)} plåtar, {sum(r[7] for r in rader)} hål")
