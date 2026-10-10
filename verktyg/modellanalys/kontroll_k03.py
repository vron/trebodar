"""
Kontroll av K-03:s geometri (beräkningar/K-03/geometri.json) mot Onshape-modellen: takbalkar, takfönster,
takstolar, stolpar och huvudstolpen.

    .venv/bin/python kontroll_k03.py

geometri.json är K-03:s egen källfil och uppdateras för hand. Den här kontrollen läser modeller/trebodar.step,
räknar fram samma data och redovisar skillnaderna. Den skriver ingenting. Koordinater som i K-05: x, y från
skärningen mellan mellanbjälklagets kanter, z från bjälklagets överkant, mm. Stolparna söks kring K-05:s
punktlaster (LN, LD, LA) eller kring sökpunkten i K-03:s indata.toml ([[stolpe]] sok); sökpunkten jämförs inte.
Väggarna (gipsskivorna) avgör åt vilket håll en stolpe är stagad.
"""
import json
import sys
import tomllib
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
ROT = HERE.parent.parent
K03 = ROT / "beräkningar" / "K-03"
sys.path.insert(0, str(HERE))
from jamfor import jamfor, redovisa  # noqa: E402
from modell import Modell  # noqa: E402

IN = tomllib.loads((K03 / "indata.toml").read_text(encoding="utf-8"))
G05 = json.load(open(ROT / "beräkningar" / "K-05" / "bild" / "geometri.json", encoding="utf-8"))
BALKAR = {"HEA200 NV": "N1", "HEA200 NVb": "D2", "HEA200 M": "N3", "HEA200 SEb": "D4", "HEA200 SE": "N5"}
SOK_STOLPE = 120.0          # stolpens delar: centrum inom detta avstånd från sökpunkten i plan [mm]
GLIPA_VAGG = 30.0           # stolpen räknas som stagad av en vägg om gipsskivan ligger högst så här långt bort [mm]
r1 = lambda v: round(float(v), 1)


def huvudaxlar(m, d, O):
    """Längd, bredd och höjd längs delens huvudaxlar (PCA på nätet) och längdriktningen."""
    V, _ = m.nat(d)
    V = np.asarray(V, float) - O
    c = V.mean(0)
    w, U = np.linalg.eigh(np.cov((V - c).T))
    U = U[:, ::-1]
    P = (V - c) @ U
    ext = P.max(0) - P.min(0)
    a = U[:, 0] * np.sign(U[np.argmax(np.abs(U[:, 0])), 0])
    return ext, a


def main():
    m = Modell(tyst=True)
    platta = [d for d in m.valj("Mittenplatta") if d.namn == "Mittenplatta"][0]
    b = platta.bbox
    O = np.array([b[0], b[1], b[5]])                     # som K-05: plattkanternas skärning och plattans överkant
    stomme = m.valj("Regelstomme Ny")

    def bb(d):
        q = np.array(d.bbox) - np.concatenate([O, O])
        return dict(x0=r1(q[0]), y0=r1(q[1]), z0=r1(q[2]), x1=r1(q[3]), y1=r1(q[4]), z1=r1(q[5]))

    ut = dict(kalla=dict(fil=m.fil.name, hash=m.hash), origo=[r1(v) for v in O])
    # nock- och dalbalkar
    ut["balkar"] = []
    for d in stomme:
        if d.namn in BALKAR:
            q = bb(d)
            ut["balkar"].append(dict(namn=BALKAR[d.namn], modell=d.namn, x=r1((q["x0"] + q["x1"]) / 2),
                                     y0=q["y0"], y1=q["y1"], zu=q["z0"], zo=q["z1"]))
    # takbalkar
    ut["takbalkar"] = []
    for d in stomme:
        if d.namn.startswith("Å"):
            q = bb(d)
            ut["takbalkar"].append(dict(typ=d.namn.split(" [")[0], x0=q["x0"], x1=q["x1"],
                                        y=r1((q["y0"] + q["y1"]) / 2), z0=q["z0"], z1=q["z1"]))
    # takfönster: par av avväxlingsreglar med samma y-läge
    tf = [bb(d) | dict(namn=d.namn) for d in stomme if d.namn.startswith("R TF t")]
    grupper = {}
    for t in tf:
        grupper.setdefault((t["y0"], t["y1"], t["x0"] < 6905), []).append(t)
    ut["fonster"] = []
    for nr, ((y0, y1, _), ts) in enumerate(sorted(grupper.items(), key=lambda g: (g[0][1], g[0][0])), 1):
        ts.sort(key=lambda t: t["z0"])
        xa, xb = min(t["x0"] for t in ts), max(t["x1"] for t in ts)
        sida = [r for r in ut["takbalkar"] if r["x0"] <= xa + 1 and r["x1"] >= xb - 1]
        vid0 = [r for r in sida if y0 - 100 < r["y"] < y0]
        vid1 = [r for r in sida if y1 < r["y"] < y1 + 100]
        inne = [r for r in ut["takbalkar"] if y0 < r["y"] < y1 and r["x1"] > xa and r["x0"] < xb]
        ut["fonster"].append(dict(nr=nr, y0=y0, y1=y1, x0=ts[0]["x1"], x1=ts[-1]["x0"], z_under=ts[0]["z0"], z_over=ts[-1]["z0"],
                                  vaxlar=[[t["x0"], t["x1"], t["z0"], t["z1"]] for t in ts],
                                  trimmer=[len(vid0), len(vid1)], kortlingar=len(inne)))
    # takstolar
    ut["takstolar"] = []
    for T in IN["takstol"]:
        if T["namn"].startswith("Stol"):
            delar = [d for d in stomme if d.grupp.endswith(T["namn"] + " <1>")]
        else:                                             # takstolen ligger i gavelväggens grupp
            delar = [d for d in stomme if d.grupp.endswith(T["namn"] + " <1>") and d.namn.split(" [")[0] in (
                f"{T['namn']} diag", f"{T['namn']} extra", f"{T['namn']} bottom", "Sp 100x400", "Sp 100x600")]
        staver, platar = [], []
        for d in delar:
            q = bb(d)
            if d.namn.startswith("Sp "):
                platar.append(dict(namn=d.namn.split(" [")[0], x0=q["x0"], x1=q["x1"], z0=q["z0"], z1=q["z1"]))
                continue
            ext, a = huvudaxlar(m, d, O)
            staver.append(dict(namn=d.namn, x0=q["x0"], x1=q["x1"], z0=q["z0"], z1=q["z1"], y0=q["y0"], y1=q["y1"],
                               L=r1(ext[0]), h=r1(ext[1]), b=r1(ext[2]), ax=round(float(a[0]), 3), az=round(float(a[2]), 3)))
        y = float(np.mean([(s["y0"] + s["y1"]) / 2 for s in staver]))
        ut["takstolar"].append(dict(namn=T["namn"], y=r1(y), staver=staver, platar=platar))
    # väggar (gipsskivor) och stolpar
    gips = [bb(d) | dict(namn=d.namn) for d in m.valj("gyp_w*")]
    vert = []
    for d in stomme:
        q = bb(d)
        if q["z1"] - q["z0"] > 1000 and (q["x1"] - q["x0"]) < 200 and (q["y1"] - q["y0"]) < 200:
            vert.append(q | dict(namn=d.namn, grupp=d.grupp.split("/")[-1]))
    ut["stolpar"] = []
    sys.path.insert(0, str(ROT / "beräkningar" / "K-05"))
    import laster as L05                                  # stolparnas lägen: K-05:s punktlaster, sökpunkt i indata vid behov
    sok = {p["namn"]: (p["x"], p["y"]) for p in L05.punktlaster()}
    sok.update({S["namn"]: tuple(S["sok"]) for S in IN["stolpe"] if "sok" in S})
    for namn, (x, y) in sok.items():
        S = dict(namn=namn)
        delar = [v for v in vert if abs((v["x0"] + v["x1"]) / 2 - x) <= SOK_STOLPE and abs((v["y0"] + v["y1"]) / 2 - y) <= SOK_STOLPE]
        stagad = ""
        if delar:
            X0, X1 = min(v["x0"] for v in delar), max(v["x1"] for v in delar)
            Y0, Y1 = min(v["y0"] for v in delar), max(v["y1"] for v in delar)
            for g in gips:
                dx = max(g["x0"] - X1, 0, X0 - g["x1"])
                dy = max(g["y0"] - Y1, 0, Y0 - g["y1"])
                if dx <= GLIPA_VAGG and dy <= GLIPA_VAGG and g["z1"] > 2000:
                    stagad += "x" if (g["x1"] - g["x0"]) > (g["y1"] - g["y0"]) else "y"
        ut["stolpar"].append(dict(namn=S["namn"], sok=[x, y], stagad="".join(sorted(set(stagad))),
                                  delar=[dict(namn=v["namn"], grupp=v["grupp"], x0=v["x0"], x1=v["x1"], y0=v["y0"], y1=v["y1"],
                                              z0=v["z0"], z1=v["z1"]) for v in delar]))
    # huvudstolpens delar (för figuren)
    ut["huvudstolpe"] = [bb(d) | dict(namn=d.namn) for d in stomme if d.grupp.split("/")[-1].startswith("L3 Vert") and not d.namn.startswith("Sp")]
    kalla = json.loads((K03 / "geometri.json").read_text(encoding="utf-8"))
    kod = redovisa("K-03 geometri.json", jamfor(kalla, ut, utelamna=(".sok",)))
    # K-05:s stolplägen (laster.STOLPLAGEN) mot stolparnas mitt i modellen
    fel = []
    for s_ in ut["stolpar"]:
        d = s_["delar"]
        if s_["namn"] in L05.STOLPLAGEN and d:
            c = ((min(v["x0"] for v in d) + max(v["x1"] for v in d)) / 2, (min(v["y0"] for v in d) + max(v["y1"] for v in d)) / 2)
            fel += [f"{s_['namn']}: K-05 {L05.STOLPLAGEN[s_['namn']]}, modellen ({c[0]:.0f}, {c[1]:.0f})"
                    for k in (0, 1) if abs(L05.STOLPLAGEN[s_["namn"]][k] - c[k]) > 1.0][:1]
    return max(kod, redovisa("K-05 laster.STOLPLAGEN", fel))

if __name__ == "__main__":
    sys.exit(main())
