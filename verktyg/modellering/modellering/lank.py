"""Länkar in i webbvisaren (docs/modell, webb/index.html): en vy som JSON i adressen, #vy=<JSON, URL-kodad>, så att en
plats i modellen kan delas, t.ex. i ett ärende. Vyn har samma nycklar som visaren läser:

    kamera, mal        [x, y, z] i modellens mm (K-05); utan dem zoomas vyn till målen
    visa / tona        mål som visas ensamma eller med allt annat nedtonat
    dolj               mål som döljs
    zooma              mål att zooma till i stället för visa/tona
    fran, luft         riktningen från målet mot kameran [dx, dy, dz] och avståndet (1 = målen fyller bilden)
    snitt              {"x": mm, "y": mm, "z": mm, "vand": true}
    orto, brannvidd, verklig, kanter, text

Ett mål är en dels eller grupps sökväg, slutet av den, namnet (* står för vad som helst) eller material:<namn>.
`./mod lank` bygger adressen och prövar målen mot modellens delar; med --punkt, --fran och --avstand räknar den
kamerans läge för en närbild av en punkt.
"""
from __future__ import annotations

import json
import re
from collections.abc import Sequence
from urllib.parse import quote

BAS = "https://vron.github.io/trebodar/modell/"


def adress(vy: dict, bas: str = BAS) -> str:
    """Adressen till vyn i visaren."""
    return bas + "#vy=" + quote(json.dumps(vy, ensure_ascii=False, separators=(",", ":")), safe="")


def traffar(index: Sequence[dict], mal: str) -> list[str]:
    """Delarnas sökvägar som målet träffar, som i visaren: sökvägen (en del eller en grupp), slutet av den, eller
    namnet på en del eller grupp. index: delarna med sokvag och material."""
    if mal.startswith("material:"):
        return [d["sokvag"] for d in index if d["material"] == mal[9:]]
    vagar = [d["sokvag"] for d in index]
    ut = [v for v in vagar if v == mal or v.startswith(mal + "/")]
    if not ut:
        ut = [v for v in vagar if v.endswith("/" + mal) or f"/{mal}/" in v]
    if not ut:
        monster = re.compile("^" + ".*".join(re.escape(b) for b in mal.split("*")) + "$")
        ut = [v for v in vagar if any(monster.match(b) for b in v.split("/")[1:])]
    return ut


def kontrollera(index: Sequence[dict], vy: dict, utom: Sequence[str] = ()) -> list[str]:
    """Fel i vyns mål: de som inte träffar något i modellen eller bara sådant som inte är med i visaren (utom)."""
    fel = []
    for nyckel in ("visa", "tona", "dolj", "zooma"):
        for mal in vy.get(nyckel) or [] if isinstance(vy.get(nyckel), list) else []:
            t = traffar(index, mal)
            if not t:
                fel.append(f"{nyckel}: {mal} träffar ingenting i modellen")
            elif all(any(f"/{u}/" in v + "/" for u in utom) for v in t):
                fel.append(f"{nyckel}: {mal} finns inte i visaren (utelämnat: {', '.join(utom)})")
    return fel
