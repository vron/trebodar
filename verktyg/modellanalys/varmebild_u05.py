"""Värmebild av huset: värmeflödets täthet [W/m²] ut genom husets yttre ytor i U-05:s grundfall (0 °C ute,
stationärt), som 3D-bilder från fyra håll utan marken. En kontroll för ögat: ytor med oväntat stort eller litet flöde
syns direkt.

    ./ma varmebild_u05.py

Underlaget räknas av varmebild_u05_data.py med beräkningarnas Python-miljö (3D-modellens temperaturfält, ungefär en
minut) och sparas i ut/U-05_varmebild.npz; det räknas om när U-05:s resultat är nyare. Fönstrens och dörrarnas lägen
(karmarna) tas ur modellen. Bilderna hamnar i ut/: från söder och norr och underifrån, med hela skalan och med en
skala som slutar vid 8 W/m² (fönstren, dörrarna och mellanbjälklagets kant blir då mörkast), så att skillnaderna i
väggar, tak och grund syns. Skriver ingenting annat.
"""
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
import pyvista as pv

HERE = Path(__file__).resolve().parent
ROT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from modell import Modell  # noqa: E402

UT = HERE / "ut"
NPZ = UT / "U-05_varmebild.npz"
DATA = HERE / "varmebild_u05_data.py"
RES = ROT / "beräkningar" / "U-05" / "resultat.json"
UTANFOR = 30.0                                  # fönstrens ytor ritas strax utanför väggens yta [mm]


def underlag():
    UT.mkdir(exist_ok=True)
    if not NPZ.exists() or NPZ.stat().st_mtime < max(RES.stat().st_mtime, DATA.stat().st_mtime):
        subprocess.run([str(ROT / "beräkningar" / ".venv" / "bin" / "python"), str(DATA), str(NPZ)], check=True)
    return np.load(NPZ, allow_pickle=False)


def karmar():
    """Karmarnas omslutande lådor (x0, y0, z0, x1, y1, z1) i K-05:s koordinater [mm], per kod."""
    m = Modell(tyst=True)
    pl = [d for d in m.delar if d.namn == "MB-B"][0]
    O = np.array([pl.bbox[0], pl.bbox[1], pl.bbox[5]])
    return {d.namn[:-5]: np.r_[np.array(d.bbox[:3]) - O, np.array(d.bbox[3:]) - O]
            for d in m.delar if d.namn.endswith("-KARM")}


def main():
    pv.OFF_SCREEN = True
    d = underlag()
    tan = math.tan(math.radians(float(d["lutning"])))
    dal = sorted(float(x) for x in d["dal"])

    def z_tak(x):
        nock, halv, z0 = d["tak"][0 if x < dal[0] else (1 if x < dal[1] else 2)]
        return (z0 + (halv - abs(x - nock)) * tan) / 1000 + 0.33
    q_f = dict(zip((str(k) for k in d["fonster_kod"]), (float(v) for v in d["fonster_q"])))
    ytor, q, kontur = [], [], []
    for kod, (x0, y0, z0, x1, y1, z1) in karmar().items():
        if kod not in q_f:
            print(f"OBS: {kod} finns i modellen men inte i U-05")
            continue
        if kod.startswith("TF"):
            bitar = [[(x0, y0, z_tak(x0) * 1000 + UTANFOR), (x1, y0, z_tak(x1) * 1000 + UTANFOR),
                      (x1, y1, z_tak(x1) * 1000 + UTANFOR), (x0, y1, z_tak(x0) * 1000 + UTANFOR)]]
        elif x1 - x0 < y1 - y0:                    # vägg längs y: en yta på var sida om väggen, den inre döljs
            bitar = [[(x, y0, z0), (x, y1, z0), (x, y1, z1), (x, y0, z1)] for x in (x0 - UTANFOR, x1 + UTANFOR)]
        else:
            bitar = [[(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)] for y in (y0 - UTANFOR, y1 + UTANFOR)]
        for b in bitar:
            ytor.append(np.array(b, float) / 1000)
            q.append(q_f[kod])
            kontur.append(ytor[-1])
    # konturer också runt takfallen och långsidornas väggar (gavlarna är uppdelade i remsor)
    for Q, n in zip(d["extra"], (str(n) for n in d["namn"])):
        if n.startswith("tak") or (n.startswith("vägg") and n.split()[1][1:] in ("SO", "NV")):
            kontur.append(Q.astype(float))
    quads = np.concatenate([d["quads"], d["extra"], np.array(ytor)]).astype(float)
    varde = np.concatenate([d["q"], d["qx"], np.array(q)]).astype(float)
    n = len(quads)
    nat = pv.PolyData(quads.reshape(-1, 3), np.hstack([np.full((n, 1), 4), np.arange(4 * n).reshape(n, 4)]).ravel())
    nat.cell_data["q"] = varde
    linjer = pv.line_segments_from_points(np.array([p for Q in kontur for a, b in zip(Q, np.roll(Q, -1, axis=0))
                                                    for p in (a, b)]))
    c = np.array([6.9, 8.0, 0.4])
    vyer = {"1_fran_soder": ((-17, 21, 13), "Från söder: fasaderna mot sydost och sydväst"),
            "2_fran_norr": ((17, -21, 13), "Från norr: fasaderna mot nordväst och nordost"),
            "3_underifran_soder": ((-17, 21, -15), "Underifrån, från söder"),
            "4_underifran_norr": ((17, -21, -15), "Underifrån, från norr")}
    T = [float(x) for x in d["T"]]
    for skala, vmax in (("hela", 24.0), ("lag", 8.0)):
        for nyckel, (riktning, titel) in vyer.items():
            pl = pv.Plotter(off_screen=True, window_size=(1800, 1250))
            pl.set_background("#5f6368")
            pl.add_mesh(nat, scalars="q", cmap="OrRd", clim=(0.0, vmax), lighting=False,
                        above_color="#3b0008" if vmax < 20 else None,
                        scalar_bar_args=dict(title="W/m²", color="white", vertical=True, position_x=0.91,
                                             position_y=0.2, height=0.6, width=0.045, title_font_size=24,
                                             label_font_size=20, fmt="%.0f", above_label=f"över {vmax:.0f}"))
            pl.add_mesh(linjer, color="#1e1e1e", line_width=1.5, lighting=False)
            pl.camera_position = [tuple(c + riktning), tuple(c), (0, 0, 1)]
            pl.camera.zoom(1.08)
            pl.add_text(f"{titel}. Värmeflödet ut genom ytan vid {T[0]:.0f} °C ute, {T[1]:.0f} °C på plan 1 och "
                        f"{T[2]:.1f} °C i källaren" + (f"; över {vmax:.0f} W/m² mörkast" if vmax < 20 else ""),
                        position="upper_left", font_size=12, color="white")
            fil = UT / f"U-05_varmebild_{skala}_{nyckel}.png"
            pl.screenshot(str(fil))
            pl.close()
            print(fil.relative_to(HERE))
    return 0


if __name__ == "__main__":
    sys.exit(main())
