"""Poly Havens tillgångar (CC0, polyhaven.com) för omgivningen i renderingen: markens texturer och modellerna av
träden och stenarna (blender/omgivning.py, TEXTURER och MODELLER). `./mod omgivning --hamta` laddar ner det som
saknas till tillgångarnas mapp (vyer.GEODATA["tillgangar"], versionshanteras inte)."""
from __future__ import annotations

import json
import os
import urllib.request

API = "https://api.polyhaven.com/files/"
TEXTURER = {"rock_01": "2k", "leafy_grass": "2k", "forrest_ground_03": "2k"}
KARTOR = (("Diffuse", "diff"), ("Rough", "rough"), ("Displacement", "disp"))
MODELLER = {"pine_tree_01": "1k", "fir_tree_01": "1k", "namaqualand_boulder_04": "2k", "namaqualand_boulder_06": "2k"}


def _hamta(url: str, fil: str, kontakt: str) -> bool:
    """Filen från url, om den saknas (via en .tmp-fil, så att en avbruten nedladdning inte blir kvar)."""
    if os.path.exists(fil) and os.path.getsize(fil) > 0:
        return False
    os.makedirs(os.path.dirname(fil), exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": kontakt})
    with urllib.request.urlopen(req, timeout=600) as r, open(fil + ".tmp", "wb") as f:
        while b := r.read(1 << 20):
            f.write(b)
    os.replace(fil + ".tmp", fil)
    return True


def _filer(namn: str, kontakt: str) -> dict:
    req = urllib.request.Request(API + namn, headers={"User-Agent": kontakt})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def hamta(mapp: str, kontakt: str = "trebodar") -> list[str]:
    """Det som saknas i mapp: texturer/<namn>/<namn>_<karta>_<upplösning>.jpg och modeller/<namn>/ (blend-filen med
    sina bilder). Ger de tillgångar som något laddades ner för."""
    nya = []
    for namn, res in TEXTURER.items():
        filer = None
        for karta, kort in KARTOR:
            fil = os.path.join(mapp, "texturer", namn, f"{namn}_{kort}_{res}.jpg")
            if os.path.exists(fil):
                continue
            filer = filer or _filer(namn, kontakt)
            if _hamta(filer[karta][res]["jpg"]["url"], fil, kontakt) and namn not in nya:
                nya.append(namn)
    for namn, res in MODELLER.items():
        if os.path.exists(os.path.join(mapp, "modeller", namn, f"{namn}_{res}.blend")):
            continue
        b = _filer(namn, kontakt)["blend"][res]["blend"]
        for rel, v in b.get("include", {}).items():
            _hamta(v["url"], os.path.join(mapp, "modeller", namn, rel), kontakt)
        _hamta(b["url"], os.path.join(mapp, "modeller", namn, os.path.basename(b["url"])), kontakt)
        nya.append(namn)
    return nya
