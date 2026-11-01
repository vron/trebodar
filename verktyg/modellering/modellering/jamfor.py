"""Jämförelse med en referensmodell (STEP): varje referensdel paras med den genererade del som har störst gemensam
volym. Resultat: identiska delar, ändrade delar (med andel gemensam volym och förskjutning), borttagna delar och
nya delar, samt en namntabell från referensens namn till modellens.
"""
from __future__ import annotations

import csv
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common

from .karna import Karna, bbox, placerad, volym
from .modell import Montage
from .placering import Placering
from .referens import las


@dataclass
class Par:
    ref: str                     # referensens sökväg
    ny: str | None               # modellens sökväg
    v_ref: float
    v_ny: float
    gemensam: float
    flytt: tuple[float, float, float] = (0.0, 0.0, 0.0)   # tyngdpunktens förskjutning ny − ref [mm]

    @property
    def andel(self) -> float:
        return self.gemensam / max(self.v_ref, self.v_ny, 1e-9)

    @property
    def status(self) -> str:
        """identisk; städad (≥ 98 % gemensamt, t.ex. 2 mm fickor borttagna); ändrad (mer än hälften av båda
        gemensamt); ersatt (referensdelen ligger mest i en annan del, t.ex. en större); borttagen."""
        if self.ny is None:
            return "borttagen"
        if self.gemensam >= self.v_ref - 1.0 and self.gemensam >= self.v_ny - 1.0:
            return "identisk"
        if self.andel >= 0.98:
            return "städad"
        if self.gemensam >= 0.5 * self.v_ref and self.gemensam >= 0.5 * self.v_ny:
            return "ändrad"
        return "ersatt"


@dataclass
class Jamforelse:
    par: list[Par] = field(default_factory=list)
    nya: list[str] = field(default_factory=list)
    sekunder: float = 0.0


def jamfor(rot: Montage, karna: Karna, referens: Path, varld: Placering, urval: str | None = None,
           ny_urval: str | None = None) -> Jamforelse:
    t0 = time.perf_counter()
    ref = [r for r in las(referens, varld) if not urval or urval in "/".join(r.vag)]
    poster = [(v, d, p) for v, d, p in rot.platta() if not ny_urval or ny_urval in v]
    karna.forbered(d.form for _, d, _ in poster)
    ny_former = [placerad(karna.form(d.form), p) for _, d, p in poster]
    ny_lador = np.array([bbox(s, optimal=False) for s in ny_former])
    ny_vol = [karna.egenskaper(d.form).volym for _, d, _ in poster]
    ny_tp = [np.array(p.R) @ np.array(karna.egenskaper(d.form).tyngdpunkt) + p.t for _, d, p in poster]
    anvanda: dict[int, float] = {}
    ut = Jamforelse()
    for r in ref:
        s = r.varldsform()
        b = bbox(s, optimal=False)
        vr = volym(s)
        kand = np.where(np.all(ny_lador[:, :3] <= np.array(b[3:]) + 1.0, axis=1)
                        & np.all(ny_lador[:, 3:] >= np.array(b[:3]) - 1.0, axis=1))[0]
        bast, bv = None, 0.0
        for i in kand:
            c = BRepAlgoAPI_Common(s, ny_former[i])
            v = volym(c.Shape()) if c.IsDone() else 0.0
            if v > bv:
                bast, bv = int(i), v
        sokvag = "/".join(r.vag + (r.namn,))
        if bast is None or bv < 0.05 * vr:
            ut.par.append(Par(sokvag, None, vr, 0.0, 0.0))
            continue
        from OCP.GProp import GProp_GProps
        from OCP.BRepGProp import BRepGProp
        g = GProp_GProps()
        BRepGProp.VolumeProperties_s(s, g)
        c0 = g.CentreOfMass()
        d = ny_tp[bast] - np.array([c0.X(), c0.Y(), c0.Z()])
        ut.par.append(Par(sokvag, poster[bast][0], vr, ny_vol[bast], bv, (float(d[0]), float(d[1]), float(d[2]))))
        anvanda[bast] = anvanda.get(bast, 0.0) + bv
    ut.nya = [poster[i][0] for i in range(len(poster)) if anvanda.get(i, 0.0) < 0.05 * ny_vol[i]]
    ut.sekunder = time.perf_counter() - t0
    return ut


def rapport(j: Jamforelse, md: Path, namntabell: Path) -> str:
    st: dict[str, list[Par]] = {k: [] for k in ("identisk", "städad", "ändrad", "ersatt", "borttagen")}
    for p in j.par:
        st[p.status].append(p)
    rader = ["# Jämförelse med referensmodellen", "",
             f"{len(j.par)} referensdelar: " + ", ".join(f"{len(v)} {k}" for k, v in st.items())
             + f". {len(j.nya)} nya delar i modellen. {j.sekunder:.1f} s.", ""]
    for k, rubrik in (("ändrad", "Ändrade delar"), ("ersatt", "Ersatta delar (ligger mest i en annan del)"),
                      ("städad", "Städade delar (minst 98 % gemensam volym)")):
        rader += [f"## {rubrik}", "", "| Referens | Modellen | Gemensam volym | Tyngdpunktens förskjutning (mm) |",
                  "|---|---|---:|---|"]
        for p in sorted(st[k], key=lambda p: p.andel):
            rader.append(f"| {p.ref} | {p.ny} | {p.andel:.1%} | {p.flytt[0]:.1f}, {p.flytt[1]:.1f}, {p.flytt[2]:.1f} |")
        rader.append("")
    rader += ["## Borttagna delar", ""] + [f"- {p.ref}" for p in st["borttagen"]]
    rader += ["", "## Nya delar", ""] + [f"- {n}" for n in j.nya]
    txt = "\n".join(rader) + "\n"
    md.parent.mkdir(parents=True, exist_ok=True)
    md.write_text(txt, encoding="utf-8")
    with open(namntabell, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["referens", "modellen", "status", "gemensam_andel"])
        for p in j.par:
            w.writerow([p.ref, p.ny or "", p.status,
                        f"{p.gemensam / max(p.v_ref, p.v_ny, 1e-9):.4f}" if p.ny else ""])
    return txt
