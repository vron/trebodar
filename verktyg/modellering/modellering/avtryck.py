"""Modellens fingeravtryck: varje dels sökväg, namn, material, omslutande låda (i världen), volym och tyngdpunkt.

Spara ett före en omstrukturering och jämför efter (`./mod avtryck spara`, `./mod avtryck jamfor`): geometrin är
oförändrad om inga delar har försvunnit, tillkommit eller ändrats. Delar som bara har flyttats i modellträdet (samma
namn och geometri under en annan grupp) paras på namnet och redovisas för sig, liksom delar med samma geometri som
har fått ett annat delnamn (t.ex. "kapad 1" i stället för "kapad 4" när två likadana delar blir samma del).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from .karna import Karna
from .modell import Montage

LADA_TOL = 0.01              # mm
VOLYM_TOL = 1e-6             # relativt (och minst 1 mm³)
TP_TOL = 0.05                # tyngdpunkten, mm

Avtryck = dict[str, object]


def berakna(rot: Montage, karna: Karna) -> dict[str, Avtryck]:
    """Fingeravtrycket per delinstans, med sökvägen som nyckel."""
    karna.forbered(d.form for _, d, _ in rot.platta())
    ut: dict[str, Avtryck] = {}
    for vag, d, p in rot.platta():
        e = karna.egenskaper(d.form)
        x0, y0, z0, x1, y1, z1 = e.bbox
        horn = np.array([[x, y, z] for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]) @ np.array(p.R).T + p.t
        tp = np.array(p.R) @ np.array(e.tyngdpunkt) + p.t
        ut[vag] = {"del": d.namn, "material": d.material.namn,
                   "lada": [round(float(v), 4) for v in (*horn.min(0), *horn.max(0))],
                   "volym": round(float(e.volym), 2), "tyngdpunkt": [round(float(v), 3) for v in tp]}
    return ut


def spara(rot: Montage, karna: Karna, fil: Path) -> int:
    a = berakna(rot, karna)
    fil.parent.mkdir(parents=True, exist_ok=True)
    fil.write_text(json.dumps(a, ensure_ascii=False, indent=0), encoding="utf-8")
    return len(a)


def _lika(a: Avtryck, b: Avtryck) -> bool:
    return a["del"] == b["del"] and _samma_geometri(a, b)


def _samma_geometri(a: Avtryck, b: Avtryck) -> bool:
    if a["material"] != b["material"]:
        return False
    la, lb = np.array(a["lada"]), np.array(b["lada"])
    ta, tb = np.array(a["tyngdpunkt"]), np.array(b["tyngdpunkt"])
    va, vb = float(a["volym"]), float(b["volym"])        # type: ignore[arg-type]
    return (bool(np.all(np.abs(la - lb) <= LADA_TOL)) and bool(np.all(np.abs(ta - tb) <= TP_TOL))
            and abs(va - vb) <= max(1.0, VOLYM_TOL * max(abs(va), abs(vb))))


@dataclass
class Jamforelse:
    antal: tuple[int, int]
    borta: list[str] = field(default_factory=list)
    nya: list[str] = field(default_factory=list)
    flyttade: list[tuple[str, str]] = field(default_factory=list)
    omdopta: list[tuple[str, str, str]] = field(default_factory=list)     # sökväg, delnamn före och efter
    andrade: list[str] = field(default_factory=list)

    @property
    def lika(self) -> bool:
        return not (self.borta or self.nya or self.andrade)


def jamfor(rot: Montage, karna: Karna, fil: Path) -> Jamforelse:
    """Jämför modellen med det sparade fingeravtrycket."""
    fore: dict[str, Avtryck] = json.loads(fil.read_text(encoding="utf-8"))
    nu = berakna(rot, karna)
    r = Jamforelse((len(fore), len(nu)))
    for k in sorted(fore.keys() & nu.keys()):
        if _lika(fore[k], nu[k]):
            continue
        if _samma_geometri(fore[k], nu[k]):
            r.omdopta.append((k, str(fore[k]["del"]), str(nu[k]["del"])))
        else:
            r.andrade.append(k)
    borta, nya = sorted(fore.keys() - nu.keys()), sorted(nu.keys() - fore.keys())
    # flyttade: samma delnamn (sista ledet) och samma geometri
    kvar = {v.rsplit("/", 1)[-1]: v for v in nya}
    for v in borta:
        w = kvar.get(v.rsplit("/", 1)[-1])
        if w is not None and _lika(fore[v], nu[w]):
            r.flyttade.append((v, w))
            del kvar[w.rsplit("/", 1)[-1]]
        else:
            r.borta.append(v)
    r.nya = sorted(kvar.values())
    return r
