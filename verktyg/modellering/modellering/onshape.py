"""Onshape: ladda upp modellen (STEP) till ett nytt dokument i en mapp via Onshapes REST-API och vänta på importen.

API-nycklarna (Onshapes utvecklarsidor) läses ur en lokal fil som inte versionshanteras, standard `lokalt/onshape.json`
i repot: {"access_key": ..., "secret_key": ..., "mapp": ...}, eller ur miljövariablerna ONSHAPE_ACCESS_KEY och
ONSHAPE_SECRET_KEY. Nycklarna skrivs aldrig ut. Bara standardbiblioteket.
"""
from __future__ import annotations

import base64
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .karna import ROT

BAS = "https://cad.onshape.com"
API = "/api/v10"
NYCKELFIL = ROT / "lokalt" / "onshape.json"
STANDARDMAPP = "TrebodarAuto"
JSON = "application/json;charset=UTF-8; qs=0.09"


class OnshapeFel(RuntimeError):
    pass


@dataclass
class Klient:
    access_key: str
    secret_key: str

    @classmethod
    def ladda(cls, fil: Path = NYCKELFIL) -> tuple[Klient, dict[str, Any]]:
        """Klienten och övriga inställningar i nyckelfilen (t.ex. mappen)."""
        d: dict[str, Any] = json.loads(fil.read_text(encoding="utf-8")) if fil.exists() else {}
        a = os.environ.get("ONSHAPE_ACCESS_KEY") or d.get("access_key")
        s = os.environ.get("ONSHAPE_SECRET_KEY") or d.get("secret_key")
        if not a or not s:
            raise OnshapeFel(f"inga API-nycklar: lägg dem i {fil} eller i ONSHAPE_ACCESS_KEY/ONSHAPE_SECRET_KEY")
        return cls(a, s), d

    def anrop(self, metod: str, vag: str, data: object = None, kropp: bytes | None = None, typ: str | None = None,
              timeout: float = 120.0) -> Any:
        url = vag if vag.startswith("http") else BAS + vag
        nyckel = base64.b64encode(f"{self.access_key}:{self.secret_key}".encode()).decode()
        h = {"Authorization": f"Basic {nyckel}", "Accept": JSON}
        if data is not None:
            kropp, typ = json.dumps(data).encode(), JSON
        if typ:
            h["Content-Type"] = typ
        try:
            with urllib.request.urlopen(urllib.request.Request(url, kropp, h, method=metod), timeout=timeout) as s:
                svar = s.read()
        except urllib.error.HTTPError as e:
            raise OnshapeFel(f"{metod} {urllib.parse.urlsplit(url).path}: {e.code} "
                             f"{e.read()[:300].decode(errors='replace')}") from None
        return json.loads(svar) if svar else {}

    def mapp(self, namn: str) -> str:
        """Mappen med namnet på översta nivån; skapas om den saknas (samma anrop som Onshapes webbklient, det finns
        inte i det publicerade API:t)."""
        vag: str | None = "/api/globaltreenodes/magic/1?getPathToRoot=false&limit=50"
        while vag:
            d = self.anrop("GET", vag)
            for x in d.get("items", []):
                if x.get("jsonType") == "folder" and x.get("name") == namn:
                    return str(x["id"])
            vag = d.get("next")
        anv = self.anrop("GET", f"{API}/users/sessioninfo")
        return str(self.anrop("POST", "/api/folders", {"name": namn, "ownerId": anv["id"], "ownerType": 0})["id"])

    def dokument(self, namn: str, mapp_id: str, beskrivning: str = "", publik: bool = False) -> tuple[str, str]:
        """Nytt dokument i mappen: (dokument, arbetsyta). Gratiskonton kan bara skapa publika dokument."""
        try:
            d = self.anrop("POST", f"{API}/documents", {"name": namn, "parentId": mapp_id, "isPublic": publik,
                                                         "description": beskrivning})
        except OnshapeFel as e:
            if not publik and "public documents" in str(e):
                raise OnshapeFel("kontot kan bara skapa publika dokument (gratiskonto): ange --publik om modellen "
                                 "får vara synlig för alla i Onshape") from None
            raise
        return str(d["id"]), str(d["defaultWorkspace"]["id"])

    def importera(self, did: str, wid: str, fil: Path, vanta: float = 3600.0) -> dict[str, Any]:
        """Importera STEP-filen i dokumentet (sammanställningar behålls, färger följer med) och vänta på resultatet."""
        falt = {"translate": "true", "flattenAssemblies": "false", "yAxisIsUp": "false", "importAppearances": "true",
                "storeInDocument": "false", "allowFaultyParts": "true", "notifyUser": "false",
                "encodedFilename": urllib.parse.quote(fil.name)}
        kropp, typ = _formular(falt, "file", fil)
        tid = self.anrop("POST", f"{API}/translations/d/{did}/w/{wid}", kropp=kropp, typ=typ, timeout=900)["id"]
        start = time.time()
        while True:
            s: dict[str, Any] = self.anrop("GET", f"{API}/translations/{tid}")
            if s.get("requestState") == "DONE":
                return s
            if s.get("requestState") == "FAILED":
                raise OnshapeFel(f"importen misslyckades: {s.get('failureReason')}")
            if time.time() - start > vanta:
                raise OnshapeFel(f"importen pågår fortfarande efter {vanta:.0f} s (översättning {tid})")
            time.sleep(5)

    def flikar(self, did: str, wid: str) -> list[dict[str, Any]]:
        return list(self.anrop("GET", f"{API}/documents/d/{did}/w/{wid}/elements"))

    def delar(self, did: str, wid: str) -> list[dict[str, Any]]:
        """Alla delar i dokumentets Part Studios."""
        return list(self.anrop("GET", f"{API}/parts/d/{did}/w/{wid}", timeout=600))


def _formular(falt: dict[str, str], filfalt: str, fil: Path) -> tuple[bytes, str]:
    """multipart/form-data med fälten och filen."""
    g = uuid.uuid4().hex
    delar = [f'--{g}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode() for k, v in falt.items()]
    delar.append(f'--{g}\r\nContent-Disposition: form-data; name="{filfalt}"; filename="{fil.name}"\r\n'
                 f'Content-Type: application/octet-stream\r\n\r\n'.encode())
    delar += [fil.read_bytes(), f"\r\n--{g}--\r\n".encode()]
    return b"".join(delar), f"multipart/form-data; boundary={g}"


def ladda_upp(fil: Path, dokumentnamn: str, mapp: str | None = None, beskrivning: str = "", publik: bool = False,
              nyckelfil: Path = NYCKELFIL) -> tuple[str, Klient, str, str]:
    """Nytt dokument i mappen med STEP-filen importerad: (adress, klient, dokument, arbetsyta)."""
    k, inst = Klient.ladda(nyckelfil)
    mapp_id = k.mapp(mapp or str(inst.get("mapp", STANDARDMAPP)))
    did, wid = k.dokument(dokumentnamn, mapp_id, beskrivning, publik)
    k.importera(did, wid, fil)
    return f"{BAS}/documents/{did}/w/{wid}", k, did, wid
