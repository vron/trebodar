"""Sparade resultat av dyra, rena beräkningar i modellens skript (t.ex. rörens vägval i bjälklagen).

Ett resultat sparas under en kontrollsumma över allt det beror på: indata (tal, text, numpy-fält, shapely-geometrier
och följder av dem) och koden som räknar (`kod`). Samma summa ger samma resultat, så minnet kan aldrig bli inaktuellt:
ändras indata eller koden blir summan en annan och resultatet räknas om. Filerna ligger i ramverkets cache
(`.cache/minne/`, versionshanteras inte); finns mappen inte eller går en fil inte att läsa räknas resultatet som
vanligt. De äldsta filerna tas bort när de blir fler än HOGST.
"""
from __future__ import annotations

import hashlib
import os
import pickle
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

import numpy as np
import shapely
from shapely.geometry.base import BaseGeometry

MAPP = Path(__file__).resolve().parents[1] / ".cache" / "minne"
HOGST = 6000                    # filer i minnet; därutöver tas de äldsta (minst nyligen lästa) bort
T = TypeVar("T")


def kod(*filer: str | Path) -> str:
    """Kontrollsumman över källfilerna som räknar resultatet och bibliotekens versioner."""
    h = hashlib.sha1(f"{shapely.__version__} {shapely.geos_version_string} {np.__version__}".encode())
    for f in filer:
        h.update(Path(f).read_bytes())
    return h.hexdigest()


def _mata(h: Any, x: Any) -> None:
    if x is None:
        h.update(b"N")
    elif isinstance(x, bytes):
        h.update(b"B" + len(x).to_bytes(8, "little") + x)
    elif isinstance(x, str):
        _mata(h, x.encode())
    elif isinstance(x, (bool, int, float, np.integer, np.floating)):
        h.update(b"T" + repr(float(x)).encode() if not isinstance(x, (bool, int, np.integer))
                 else b"I" + repr(int(x)).encode())
    elif isinstance(x, np.ndarray):
        h.update(b"A" + str(x.dtype).encode() + repr(x.shape).encode() + np.ascontiguousarray(x).tobytes())
    elif isinstance(x, BaseGeometry):
        _mata(h, shapely.to_wkb(x))
    elif isinstance(x, dict):
        h.update(b"D" + len(x).to_bytes(8, "little"))
        for k in sorted(x, key=repr):
            _mata(h, k)
            _mata(h, x[k])
    elif isinstance(x, (list, tuple)):
        h.update(b"L" + len(x).to_bytes(8, "little"))
        for v in x:
            _mata(h, v)
    else:
        raise TypeError(f"minne.summa: {type(x).__name__} kan inte ingå i en kontrollsumma")


def summa(*delar: Any) -> str:
    """Kontrollsumman över delarna: tal, text, bytes, numpy-fält, shapely-geometrier och följder och uppslag av dem."""
    h = hashlib.sha1()
    _mata(h, delar)
    return h.hexdigest()


def sparad(nyckel: str, rakna: Callable[[], T]) -> T:
    """Resultatet under nyckeln (en summa), räknat med rakna() om det inte finns. Ett ValueError från rakna() sparas
    också och kastas igen (en väg som inte finns ska inte sökas om varje gång)."""
    fil = MAPP / nyckel[:2] / nyckel
    try:
        with open(fil, "rb") as f:
            slag, varde = pickle.load(f)
        os.utime(fil)
    except (OSError, pickle.UnpicklingError, EOFError, ValueError):
        try:
            slag, varde = "ok", rakna()
        except ValueError as fel:
            slag, varde = "fel", fel.args
        try:
            fil.parent.mkdir(parents=True, exist_ok=True)
            tmp = fil.with_name(f"{fil.name}.{os.getpid()}.tmp")
            with open(tmp, "wb") as f:
                pickle.dump((slag, varde), f, protocol=pickle.HIGHEST_PROTOCOL)
            os.replace(tmp, fil)
        except OSError:
            pass
    if slag == "fel":
        raise ValueError(*varde)
    return varde  # type: ignore[no-any-return]


def stada() -> int:
    """Tar bort de äldsta filerna över HOGST; antalet borttagna."""
    try:
        filer = sorted((f for f in MAPP.glob("*/*") if f.is_file()), key=lambda f: f.stat().st_mtime)
    except OSError:
        return 0
    bort = filer[:max(0, len(filer) - HOGST)]
    for f in bort:
        try:
            f.unlink()
        except OSError:
            pass
    return len(bort)
