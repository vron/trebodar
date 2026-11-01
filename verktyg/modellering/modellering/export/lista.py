"""Materiallista (per unik del och per material) och index över alla delar (för kontroller och sökning)."""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from ..karna import Karna
from ..modell import Montage


def index(rot: Montage, karna: Karna, fil: Path) -> list[dict[str, object]]:
    """Alla delinstanser med sökväg, del, material, omslutande låda i världen, volym, massa och tyngdpunkt."""
    karna.forbered(d.form for _, d, _ in rot.platta())
    rader: list[dict[str, object]] = []
    for vag, d, p in rot.platta():
        e = karna.egenskaper(d.form)
        x0, y0, z0, x1, y1, z1 = e.bbox
        horn = np.array([[x, y, z] for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]) @ np.array(p.R).T + p.t
        tp = np.array(p.R) @ np.array(e.tyngdpunkt) + p.t
        rader.append({"sokvag": vag, "namn": vag.rsplit("/", 1)[-1], "del": d.namn, "material": d.material.namn,
                      "bbox": [round(float(v), 4) for v in (*horn.min(0), *horn.max(0))],
                      "volym": round(e.volym, 1), "massa": round(e.volym * 1e-9 * d.material.densitet, 3),
                      "tyngdpunkt": [round(float(v), 2) for v in tp], "matt": list(e.matt),
                      "giltig": e.giltig, "solider": e.solider})
    fil.parent.mkdir(parents=True, exist_ok=True)
    fil.write_text(json.dumps(rader, ensure_ascii=False, indent=0), encoding="utf-8")
    return rader


def materiallista(rot: Montage, karna: Karna, csvfil: Path, mdfil: Path) -> None:
    karna.forbered(d.form for _, d, _ in rot.platta())
    grupper: dict[tuple[str, str], dict[str, Any]] = {}
    for vag, d, _ in rot.platta():
        k = (d.material.namn, d.namn)
        if k not in grupper:
            e = karna.egenskaper(d.form)
            grupper[k] = {"material": d.material.namn, "beskrivning": d.material.beskrivning, "del": d.namn,
                          "enhet": d.material.enhet, "matt": e.matt, "volym": e.volym,
                          "massa": e.volym * 1e-9 * d.material.densitet, "antal": 0, "artikel": d.artikel or ""}
        grupper[k]["antal"] = int(grupper[k]["antal"]) + 1
    rader = sorted(grupper.values(), key=lambda g: (str(g["material"]), str(g["del"])))
    csvfil.parent.mkdir(parents=True, exist_ok=True)
    with open(csvfil, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["material", "del", "antal", "längd_mm", "bredd_mm", "tjocklek_mm", "volym_m3_st", "massa_kg_st",
                    "massa_kg", "artikel"])
        for g in rader:
            m = g["matt"]
            w.writerow([g["material"], g["del"], g["antal"], *(f"{v:.1f}" for v in m),
                        f"{float(g['volym']) * 1e-9:.6f}", f"{float(g['massa']):.2f}",
                        f"{float(g['massa']) * int(g['antal']):.1f}", g["artikel"]])
    tot: dict[str, list[float]] = defaultdict(lambda: [0.0, 0.0, 0.0])
    for g in rader:
        t = tot[f"{g['material']} – {g['beskrivning']}"]
        n = int(g["antal"])
        t[0] += n
        t[1] += float(g["volym"]) * 1e-9 * n
        t[2] += float(g["massa"]) * n
    md = ["# Materiallista", "", "| Material | Antal delar | Volym (m³) | Massa (kg) |", "|---|---:|---:|---:|"]
    md += [f"| {k} | {v[0]:.0f} | {v[1]:.3f} | {v[2]:.0f} |" for k, v in sorted(tot.items())]
    md += ["", "| Material | Del | Antal | Mått (mm) | Massa (kg) |", "|---|---|---:|---|---:|"]
    for g in rader:
        m = g["matt"]
        md.append(f"| {g['material']} | {g['del']} | {g['antal']} | {' × '.join(f'{v:g}' for v in m)} | "
                  f"{float(g['massa']) * int(g['antal']):.1f} |")
    mdfil.write_text("\n".join(md) + "\n", encoding="utf-8")
