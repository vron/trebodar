"""Modellanalysens cache (verktyg/modellanalys, `Modell`) direkt ur modellen: för STEP-filen som just skrevs, eller
utan STEP-fil (`mod bygg --format analys`, som modellanalysen kör när modellens källor har ändrats), och pekaren
bredvid STEP-filen (trebodar.analys.json) som modellanalysen läser den kodgenererade modellen genom.

Innehållet är detsamma som när modellanalysen läser STEP-filen (samma sökvägar, färger, egenskaper och funktioner
för egenskaperna och näten, `egenskaper` och `triangulera` i modellanalysens modell.py), men utan att läsa den:
egenskaperna räknas en gång per placerad del och näten en gång per recept, och båda sparas i kärnans cache, så
att en ändring av modellen bara räknar om det som ändrats. Varje del får en nyckel (receptet och placeringen) som
modellanalysen kan cacha snitt med.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import time
from functools import cache
from pathlib import Path
from types import ModuleType
from typing import Any

import numpy as np
from OCP.BRepBuilderAPI import BRepBuilderAPI_Copy
from OCP.Quantity import Quantity_Color

from ..karna import Karna, placerad
from ..modell import Del, Montage
from ..placering import IDENTITET, Placering
from .step import _farg

ANALYS_VERSION = 1             # höj när innehållet ändras (ogiltigförklarar de sparade egenskaperna och näten)
MODELLANALYS = Path(__file__).resolve().parents[3] / "modellanalys" / "modell.py"


@cache
def modellanalys() -> ModuleType:
    """Modellanalysens modell.py (cachens format och funktioner)."""
    spec = importlib.util.spec_from_file_location("modellanalys_modell", MODELLANALYS)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _srgb(hex_: str) -> list[float]:
    """CAD-färgen som modellanalysen läser den ur STEP-filen (sRGB 0–1, fyra decimaler)."""
    c = _farg(hex_)
    return [round(Quantity_Color.Convert_LinearRGB_To_sRGB_s(v), 4) for v in (c.Red(), c.Green(), c.Blue())]


def _nyckel(*delar: object) -> str:
    return hashlib.sha1("|".join(map(str, delar)).encode()).hexdigest()[:20]


def _peka(ma: ModuleType, step_fil: Path, katalog: Path) -> None:
    p = ma.pekare(step_fil)
    tmp = p.with_name(f".{p.name}.tmp")
    tmp.write_text(json.dumps({"katalog": katalog.name}) + "\n", encoding="utf-8")
    tmp.replace(p)


def skriv(rot: Montage, karna: Karna, step_fil: Path, med_step: bool = True) -> tuple[Path, int, float]:
    """Skriv cachen (om den saknas) för STEP-filen som just skrevs, eller utan STEP-fil (nyckeln är då modellens
    innehåll), och peka ut den. Returnerar katalogen, antalet delar vars egenskaper eller nät räknades och tiden."""
    t0 = time.perf_counter()
    ma = modellanalys()
    katalog = ma.cachekatalog(step_fil) if med_step else None
    if katalog is not None and ma._las_index(katalog) is not None:
        _peka(ma, step_fil, katalog)
        return katalog, 0, time.perf_counter() - t0
    noder: list[dict[str, object]] = []
    poster: list[tuple[str, str, Del, Placering]] = []

    def ga(m: Montage, sokvag: str, djup: int, namn: str, plac: Placering) -> None:
        noder.append({"sokvag": sokvag, "namn": namn, "djup": djup, "grupp": True})
        for i, n in zip(m.barn, ma.unika_namn([i.namn or "?" for i in m.barn])):
            v = f"{sokvag}/{n}" if sokvag else n
            p = plac @ i.placering
            if isinstance(i.barn, Montage):
                ga(i.barn, v, djup + 1, i.namn, p)
            else:
                noder.append({"sokvag": v, "namn": i.namn, "djup": djup + 1, "grupp": False, "id": len(poster)})
                poster.append((v, n, i.barn, p))
    ga(rot, "", 0, rot.namn, IDENTITET)
    karna.forbered(d.form for _, _, d, _ in poster)
    recept = [karna.nyckel(d.form) for _, _, d, _ in poster]
    instans = [_nyckel(ANALYS_VERSION, ma.FORMAT, k, p.matris().tobytes().hex()) for k, (*_, p) in zip(recept, poster)]
    natnyckel = {k: _nyckel(ANALYS_VERSION, ma.FORMAT, ma.NAT_LIN, ma.NAT_VINKEL, k) for k in recept}
    if katalog is None:                                # utan STEP-fil: nyckeln är modellens innehåll
        innehall = json.dumps([noder, [(v, n, d.material.cad_farg, k) for (v, n, d, _), k in zip(poster, instans)]])
        katalog = ma.CACHE / f"{step_fil.stem}-m{hashlib.sha1(innehall.encode()).hexdigest()[:11]}"
        if ma._las_index(katalog) is not None:
            _peka(ma, step_fil, katalog)
            ma._rensa(katalog)
            return katalog, 0, time.perf_counter() - t0

    db = karna.db
    db.execute("create table if not exists analys_del (nyckel text primary key, egenskaper text)")
    db.execute("create table if not exists analys_nat (nyckel text primary key, V blob, F blob)")

    def hamta(tabell: str, kolumner: str, nycklar: list[str]) -> dict[str, tuple[Any, ...]]:
        ut: dict[str, tuple[Any, ...]] = {}
        for i in range(0, len(nycklar), 500):
            del_ = nycklar[i:i + 500]
            for r in db.execute(f"select nyckel, {kolumner} from {tabell} where nyckel in "
                                f"({','.join('?' * len(del_))})", del_):
                ut[r[0]] = r[1:]
        return ut

    kanda_e = {k: json.loads(str(v[0])) for k, v in hamta("analys_del", "egenskaper", sorted(set(instans))).items()}
    nya_e = {}
    for k, (*_, d, p) in zip(instans, poster):
        if k not in kanda_e and k not in nya_e:
            nya_e[k] = ma.egenskaper(placerad(karna.form(d.form), p))
    kanda_n = {k: (np.frombuffer(v[0], np.float64).reshape(-1, 3), np.frombuffer(v[1], np.int32).reshape(-1, 3))
               for k, v in hamta("analys_nat", "V, F", sorted(set(natnyckel.values()))).items()}
    nya_n = {}
    for k, (*_, d, _) in zip(recept, poster):
        nk = natnyckel[k]
        if nk not in kanda_n and nk not in nya_n:
            # en kopia utan kärnans nät (finare, för webben), så att näten blir som när STEP-filen läses
            V, F = ma.triangulera(BRepBuilderAPI_Copy(karna.form(d.form), True, False).Shape())
            nya_n[nk] = (V.astype(np.float64), F.astype(np.int32))
    with db:
        db.executemany("insert or replace into analys_del values (?, ?)",
                       [(k, json.dumps(e)) for k, e in nya_e.items()])
        db.executemany("insert or replace into analys_nat values (?, ?, ?)",
                       [(k, V.tobytes(), F.tobytes()) for k, (V, F) in nya_n.items()])
    egen = kanda_e | nya_e
    nat = kanda_n | nya_n

    delar, natlista, former = [], [], []
    for i, ((sokvag, namn, d, p), k, rk) in enumerate(zip(poster, instans, recept)):
        delar.append({"id": i, "sokvag": sokvag, "namn": namn, "farg": _srgb(d.material.cad_farg), **egen[k],
                      "nyckel": k})
        V, F = nat[natnyckel[rk]]
        R, t = np.array(p.R, dtype=float), np.array(p.t, dtype=float)
        if np.linalg.det(R) < 0:                       # spegling vänder trianglarnas varv
            F = F[:, ::-1]
        natlista.append((V @ R.T + t, F))
        former.append(placerad(karna.form(d.form), p))
    ma.skriv_cache(katalog, step_fil, rot.namn, noder, delar, natlista, former)
    _peka(ma, step_fil, katalog)
    ma._rensa(katalog)
    return katalog, len(nya_e) + len(nya_n), time.perf_counter() - t0
