"""Delar som ännu läses ur Onshape-modellen (BREP i modeller/referens/delar/, K-05:s koordinater): marken och
installationerna. De ersätts av kod när de modelleras."""
from __future__ import annotations

import hashlib
from pathlib import Path

from modellering import Importerad

ROT = Path(__file__).resolve().parents[3]
MAPP = Path("modeller") / "referens" / "delar"


def importerad(fil: str) -> Importerad:
    vag = MAPP / fil
    return Importerad(str(vag), hashlib.sha1((ROT / vag).read_bytes()).hexdigest()[:16])

