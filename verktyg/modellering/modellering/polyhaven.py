"""Poly Havens tillgångar (CC0, polyhaven.com) för omgivningen i renderingen: markens texturer och modellerna av
träden, stenarna, buskarna och gräset (blender/omgivning.py, TEXTURER och MODELLER) och himlarna (HIMLAR:
fotograferade himlar utan mark, "pure skies", för det kameran ser, blender/scen.py). `./mod omgivning --hamta` laddar ner det som saknas till
tillgångarnas mapp (vyer.GEODATA["tillgangar"], versionshanteras inte)."""
from __future__ import annotations

import json
import os
import urllib.request

API = "https://api.polyhaven.com/files/"
TEXTURER = {"rock_01": "2k", "leafy_grass": "2k", "forrest_ground_03": "2k"}
KARTOR = (("Diffuse", "diff"), ("Rough", "rough"), ("Displacement", "disp"))
MODELLER = {"pine_tree_01": "1k", "fir_tree_01": "1k", "namaqualand_boulder_04": "2k", "namaqualand_boulder_06": "2k",
            "shrub_01": "1k", "shrub_02": "1k", "shrub_03": "1k", "shrub_04": "1k", "grass_medium_02": "1k"}
# himlarna: vädret och solens höjd i bilden [°] (mätt: den ljusaste punkten), i 8K (22 bildpunkter per grad)
HIMLAR = {
    "syferfontein_18d_clear_puresky": ("sol", 18.5),
    "rustig_koppie_puresky": ("sol", 28.3),
    "kloofendal_43d_clear_puresky": ("sol", 43.1),
    "table_mountain_1_puresky": ("halvklart", 12.8),
    "kloofendal_38d_partly_cloudy_puresky": ("lätt mulet", 37.8),
    "kloofendal_overcast_puresky": ("mulet", 0.0),
}
HIMMEL_RES = "8k"
VADRENS_ORDNING = ("sol", "halvklart", "lätt mulet", "mulet")


def himmel(mapp: str, vader: str, sol_hojd: float) -> str | None:
    """Himlen i mapp för vädret med solens höjd närmast (i grannvädret om vädret saknas), eller None (ingen nedladdad,
    eller solen under horisonten)."""
    if sol_hojd < 0.0:
        return None
    finns = {n: v for n, v in HIMLAR.items() if os.path.exists(_himmelfil(mapp, n))}
    if not finns:
        return None
    i = VADRENS_ORDNING.index(vader) if vader in VADRENS_ORDNING else 0
    namn = min(finns, key=lambda n: (abs(VADRENS_ORDNING.index(finns[n][0]) - i),
                                     0.0 if finns[n][0] == "mulet" else abs(finns[n][1] - sol_hojd)))
    return _himmelfil(mapp, namn)


def _himmelfil(mapp: str, namn: str) -> str:
    return os.path.join(mapp, "himlar", f"{namn}_{HIMMEL_RES}.hdr")


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
    for namn in HIMLAR:
        if not os.path.exists(_himmelfil(mapp, namn)):
            _hamta(_filer(namn, kontakt)["hdri"][HIMMEL_RES]["hdr"]["url"], _himmelfil(mapp, namn), kontakt)
            nya.append(namn)
    return nya
