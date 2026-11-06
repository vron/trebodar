"""
Kontroll av K-03:s geometri (beräkningar/K-03/geometri.json) mot modellen: nock- och dalbalkar, takbalkar,
takfönster, takstolar, stolpar och huvudstolpen, och K-05:s stolplägen.

    .venv/bin/python kontroll_k03.py

geometri.json är K-03:s egen källfil och uppdateras för hand. Den här kontrollen läser modellen
(modeller/trebodar/ut/trebodar.step), parar källfilens delar med modellens på läget (källfilens namn är
Onshape-modellens, t.ex. takbalkstyperna och takstolarnas stavar, och jämförs inte) och redovisar per grupp
antalet och de största avvikelserna. Den skriver ingenting. Koordinater som i K-05: x, y från skärningen mellan
mellanbjälklagets kanter, z från bjälklagets överkant, mm. Stolparna söks kring K-03:s sökpunkter
(indata.toml, [[stolpe]] sok) och K-05:s punktlaster.
"""
import json
import re
import sys
import tomllib
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
ROT = HERE.parent.parent
K03 = ROT / "beräkningar" / "K-03"
sys.path.insert(0, str(HERE))
from modell import Modell  # noqa: E402

IN = tomllib.loads((K03 / "indata.toml").read_text(encoding="utf-8"))
BALKAR = {"N1": "NB1", "D2": "DB2", "N3": "NB3", "D4": "DB4", "N5": "NB5"}
TAKSTOLAR = {"Stol 1NO": "1NO", "Stol 1SV": "1SV", "Stol 2NO": "2NO", "Stol L2M": "2C", "Stol 2SV": "2SV",
             "Stol 3NO": "3NO", "3SV": "3SV"}
SOK_STOLPE = 120.0          # stolpens delar: centrum inom detta avstånd från sökpunkten i plan [mm]
TOL = 1.0                   # [mm]


def main():
    m = Modell(tyst=True)
    O = np.array([*m.valj("MB-B")[0].bbox[:2], m.valj("MB-B")[0].bbox[5]])    # K-05:s origo och bjälklagets ök
    stomme = m.valj("Stomme")

    def lada(ds):
        b = np.array(m.bbox(ds)) - np.concatenate([O, O])
        return dict(x0=b[0], y0=b[1], z0=b[2], x1=b[3], y1=b[4], z1=b[5])

    kalla = json.loads((K03 / "geometri.json").read_text(encoding="utf-8"))
    rapport, fel = [], []

    def jamfor_tal(grupp, par, falt):
        """Största avvikelse per fält för parade (källfil, modell)."""
        if not par:
            return
        st = {f: max(abs(k[f] - mo[f]) for k, mo in par) for f in falt}
        avv = {f: v for f, v in st.items() if v > TOL}
        rapport.append(f"  {grupp}: {len(par)} parade" + (", största avvikelse " + ", ".join(
            f"{f} {v:.1f}" for f, v in avv.items()) if avv else ", stämmer"))
        if avv:
            fel.append(f"{grupp}: " + ", ".join(f"{f} upp till {v:.1f} mm" for f, v in avv.items()))

    def para(kallor, modeller, nyckel):
        """Para varje källfilsdel med närmaste modelldel (nyckel: funktion till en punkt)."""
        kvar, par = list(modeller), []
        for k in kallor:
            if not kvar:
                break
            j = int(np.argmin([np.hypot(*(np.subtract(nyckel(k), nyckel(mo)))) for mo in kvar]))
            par.append((k, kvar.pop(j)))
        return par, kvar

    # ---------------------------------------------------------------- nock- och dalbalkar
    rapport.append("Nock- och dalbalkar")
    par = []
    for b in kalla["balkar"]:
        q = lada([d for d in stomme if d.grupp.endswith("/" + BALKAR[b["namn"]])])
        par.append((b, dict(x=(q["x0"] + q["x1"]) / 2, y0=q["y0"], y1=q["y1"], zu=q["z0"], zo=q["z1"])))
    jamfor_tal("balkarna", par, ("x", "y0", "y1", "zu", "zo"))

    # ---------------------------------------------------------------- takbalkar
    rapport.append("Takbalkar")
    tb = []
    for d in stomme:
        if "/Takbalkar/" in d.sokvag and re.fullmatch(r"\w+-T\d+", d.namn):
            q = lada([d])
            tb.append(dict(x0=q["x0"], x1=q["x1"], y=(q["y0"] + q["y1"]) / 2, z0=q["z0"], z1=q["z1"]))
    rapport.append(f"  {len(kalla['takbalkar'])} i källfilen, {len(tb)} i modellen")
    if len(kalla["takbalkar"]) != len(tb):
        fel.append(f"takbalkar: {len(kalla['takbalkar'])} i källfilen, {len(tb)} i modellen")
    par, kvar = para(kalla["takbalkar"], tb, lambda r: ((r["x0"] + r["x1"]) / 2, r["y"]))
    jamfor_tal("takbalkarna", par, ("x0", "x1", "y", "z0", "z1"))

    # ---------------------------------------------------------------- takfönster (avväxlingarna)
    rapport.append("Takfönster")
    av = [lada([d]) for d in stomme if "/Takbalkar/" in d.sokvag and re.fullmatch(r"\w+-A\d+", d.namn)]
    grupper = {}
    for a in av:
        grupper.setdefault((round(a["y0"]), round(a["y1"])), []).append(a)
    tf = []
    for (y0, y1), ts in sorted(grupper.items()):
        ts.sort(key=lambda t: t["z0"])
        tf.append(dict(y0=y0, y1=y1, z_under=ts[0]["z0"], z_over=ts[-1]["z0"], n=len(ts)))
    par, _ = para(kalla["fonster"], tf, lambda f: ((f["y0"] + f["y1"]) / 2, 0.0))
    jamfor_tal("öppningarna", par, ("y0", "y1", "z_under", "z_over"))

    # ---------------------------------------------------------------- takstolar
    rapport.append("Takstolar")
    for T in kalla["takstolar"]:
        kod = TAKSTOLAR[T["namn"]]
        ds = [d for d in stomme if d.grupp.endswith(f"/Takstol {kod}") and re.fullmatch(r"\w+-[DXUR]\d+", d.namn)]
        staver = [lada([d]) for d in ds if d.namn.split("-")[1][0] in "DXU" or T["namn"] == "Stol 2SV"]
        par, kvar = para(T["staver"], staver, lambda s: ((s["x0"] + s["x1"]) / 2, (s["z0"] + s["z1"]) / 2))
        if len(T["staver"]) != len(staver):
            rapport.append(f"  {T['namn']} (Takstol {kod}): {len(T['staver'])} stavar i källfilen, {len(staver)} i modellen")
            fel.append(f"{T['namn']}: {len(T['staver'])} stavar i källfilen, {len(staver)} i modellen")
        jamfor_tal(f"{T['namn']} (Takstol {kod})", par, ("x0", "x1", "z0", "z1"))

    # ---------------------------------------------------------------- stolpar
    rapport.append("Stolpar")
    sys.path.insert(0, str(ROT / "beräkningar" / "K-05"))
    import laster as L05                                  # K-05:s punktlaster och stolplägen
    sok = {p["namn"]: (p["x"], p["y"]) for p in L05.punktlaster()}
    sok.update({S["namn"]: tuple(S["sok"]) for S in IN["stolpe"] if "sok" in S})
    vert = [(d, lada([d])) for d in stomme if d.storlek[2] > 1000 and d.storlek[0] < 200 and d.storlek[1] < 200]
    vert = [(d, q) for d, q in vert if q["z1"] > 100]     # inte källarväggarnas reglar under bjälklaget
    kalla_st = {s["namn"]: s for s in kalla["stolpar"]}
    for namn, (x, y) in sok.items():
        delar = [q for d, q in vert if abs((q["x0"] + q["x1"]) / 2 - x) <= SOK_STOLPE
                 and abs((q["y0"] + q["y1"]) / 2 - y) <= SOK_STOLPE]
        k = kalla_st.get(namn)
        kd = k["delar"] if k else []
        c_m = ((min(q["x0"] for q in delar) + max(q["x1"] for q in delar)) / 2,
               (min(q["y0"] for q in delar) + max(q["y1"] for q in delar)) / 2) if delar else None
        c_k = ((min(q["x0"] for q in kd) + max(q["x1"] for q in kd)) / 2,
               (min(q["y0"] for q in kd) + max(q["y1"] for q in kd)) / 2) if kd else None
        z_m = (min(q["z0"] for q in delar), max(q["z1"] for q in delar)) if delar else None
        z_k = (min(q["z0"] for q in kd), max(q["z1"] for q in kd)) if kd else None
        avv = []
        if len(delar) != len(kd):
            avv.append(f"{len(kd)} delar i källfilen, {len(delar)} i modellen")
        if c_m and c_k and max(abs(c_m[0] - c_k[0]), abs(c_m[1] - c_k[1])) > TOL:
            avv.append(f"mitt ({c_k[0]:.0f}, {c_k[1]:.0f}) → ({c_m[0]:.0f}, {c_m[1]:.0f})")
        if z_m and z_k and max(abs(z_m[0] - z_k[0]), abs(z_m[1] - z_k[1])) > TOL:
            avv.append(f"z {z_k[0]:.0f}–{z_k[1]:.0f} → {z_m[0]:.0f}–{z_m[1]:.0f}")
        rapport.append(f"  {namn}: " + ("; ".join(avv) if avv else "stämmer"))
        if avv:
            fel.append(f"stolpe {namn}: " + "; ".join(avv))
        if namn in L05.STOLPLAGEN and c_m:
            s = L05.STOLPLAGEN[namn]
            if max(abs(s[0] - c_m[0]), abs(s[1] - c_m[1])) > TOL:
                fel.append(f"K-05 laster.STOLPLAGEN {namn}: {s}, modellen ({c_m[0]:.0f}, {c_m[1]:.0f})")

    # ---------------------------------------------------------------- huvudstolpen (LN1_3 med strävor)
    rapport.append("Huvudstolpen")
    hs = [lada([d]) for d in stomme if d.grupp.endswith("/Stolpe LN1_3") and not re.fullmatch(r"\w+-[PS]\d+", d.namn)]
    par, _ = para(kalla["huvudstolpe"], hs, lambda s: ((s["y0"] + s["y1"]) / 2, (s["z0"] + s["z1"]) / 2))
    if len(kalla["huvudstolpe"]) != len(hs):
        fel.append(f"huvudstolpen: {len(kalla['huvudstolpe'])} delar i källfilen, {len(hs)} i modellen")
    jamfor_tal("huvudstolpens delar", par, ("x0", "x1", "y0", "y1", "z0", "z1"))

    print(f"modell: {m.fil.name} ({m.hash})")
    print("\n".join(rapport))
    if fel:
        print(f"\nK-03 geometri.json avviker från modellen ({len(fel)}):")
        print("\n".join("  " + f for f in fel))
        return 1
    print("\nK-03 geometri.json: allt stämmer med modellen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
