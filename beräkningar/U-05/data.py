"""U-05: indata med härledda storheter (konturen och trapphålet ur K-05:s geometri.json, väggarnas lägen) och fallens
ändringar."""
from __future__ import annotations

import copy
import json
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent


def las(fall=None):
    P = tomllib.loads((HERE / "indata.toml").read_text(encoding="utf-8"))
    g = json.loads((HERE.parent / "K-05" / "bild" / "geometri.json").read_text(encoding="utf-8"))
    P["_kontur"] = [(x / 1000, y / 1000) for x, y in g["kontur"]]
    P["_trapphal"] = [(x / 1000, y / 1000) for x, y in g["hal"]]
    P["_skelett"] = {v["kod"]: ((v["o"][0] / 1000, v["o"][1] / 1000), tuple(v["u"]), v["L"] / 1000)
                     for v in P["mangder"]["lage"]}
    P["_skarv_kallarfonster"] = P["uppskattade_skarvar"]["kallarfonster"]
    P["_psi_gavelkant"] = P["uppskattade_skarvar"]["gavelkant"]
    if fall:
        P = med_fall(P, fall)
    return P


def med_fall(P, fall):
    """Grundfallets indata med fallets ändringar ("avsnitt.nyckel" = värde, eller egna nycklar som ftx)."""
    P = copy.deepcopy(P)
    P["_fall"] = {}
    for k, v in fall.items():
        if k == "namn":
            continue
        if "." in k:
            a, b = k.split(".", 1)
            P[a][b] = v
        else:
            P["_fall"][k] = v
    return P
