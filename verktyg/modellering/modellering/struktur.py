"""Kontroll av modellpaketets struktur (körs med ./mod typ): modulerna beror på varandra i en riktning och bara genom
publika namn.

- inga importcykler mellan paketets moduler;
- inga privata namn (_namn) från en annan modul i paketet, varken importerade eller som modul._namn;
- inga importer av paketets moduler inne i funktioner (de döljer cykler och gör beroendena svåra att se);
- lagerordningen: en modul importerar inget som paketets regler förbjuder (lager: modulprefix -> förbjudna prefix).
"""
from __future__ import annotations

import ast
from pathlib import Path


def _moduler(rot: Path, paket: str) -> dict[str, Path]:
    return {".".join((paket, *p.relative_to(rot).with_suffix("").parts)): p
            for p in sorted(rot.rglob("*.py")) if "ut" not in p.relative_to(rot).parts}


def _mal(modul: str, nod: ast.ImportFrom) -> str:
    """Den importerade modulens fulla namn (relativa importer lösta)."""
    if nod.level == 0:
        return nod.module or ""
    bas = modul.split(".")[:-nod.level]
    return ".".join(bas + ([nod.module] if nod.module else []))


def _cykler(kanter: dict[str, set[str]]) -> list[list[str]]:
    """Grupper av moduler som når varandra (Tarjans algoritm)."""
    index: dict[str, int] = {}
    lag: dict[str, int] = {}
    stack: list[str] = []
    pa: set[str] = set()
    ut: list[list[str]] = []

    def besok(v: str) -> None:
        index[v] = lag[v] = len(index)
        stack.append(v)
        pa.add(v)
        for w in kanter.get(v, ()):
            if w not in index:
                besok(w)
                lag[v] = min(lag[v], lag[w])
            elif w in pa:
                lag[v] = min(lag[v], index[w])
        if lag[v] == index[v]:
            grupp = []
            while True:
                w = stack.pop()
                pa.discard(w)
                grupp.append(w)
                if w == v:
                    break
            if len(grupp) > 1:
                ut.append(sorted(grupp))

    for v in kanter:
        if v not in index:
            besok(v)
    return ut


def _under(modul: str, prefix: str) -> bool:
    return modul == prefix or modul.startswith(prefix + ".")


def kontrollera(rot: Path, paket: str, lager: dict[str, tuple[str, ...]] | None = None) -> list[str]:
    """Strukturfelen i paketet vars moduler ligger under rot (tom lista om strukturen är i ordning)."""
    moduler = _moduler(rot, paket)
    kanter: dict[str, set[str]] = {m: set() for m in moduler}
    fel: list[str] = []
    for modul, fil in moduler.items():
        trad = ast.parse(fil.read_text(encoding="utf-8"))
        i_funktion = {id(n) for f in ast.walk(trad) if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef))
                      for n in ast.walk(f)}
        alias: dict[str, str] = {}                      # namn i modulen -> paketets modul
        for nod in ast.walk(trad):
            if isinstance(nod, ast.ImportFrom):
                mal = _mal(modul, nod)
                if mal != paket and not mal.startswith(paket + "."):
                    continue
                for a in nod.names:
                    hel = f"{mal}.{a.name}"
                    malmodul = hel if hel in moduler else mal
                    if malmodul in moduler:
                        kanter[modul].add(malmodul)
                    if hel in moduler:
                        alias[a.asname or a.name] = hel
                    elif a.name.startswith("_"):
                        fel.append(f"{modul}: importerar det privata namnet {a.name} från {mal}")
                    if id(nod) in i_funktion:
                        fel.append(f"{modul}: importerar {malmodul} inne i en funktion")
            elif isinstance(nod, ast.Import):
                for a in nod.names:
                    if a.name in moduler:
                        kanter[modul].add(a.name)
                        alias[a.asname or a.name.split(".")[0]] = a.name
                        if id(nod) in i_funktion:
                            fel.append(f"{modul}: importerar {a.name} inne i en funktion")
        for nod in ast.walk(trad):
            if (isinstance(nod, ast.Attribute) and isinstance(nod.value, ast.Name) and nod.value.id in alias
                    and nod.attr.startswith("_") and not nod.attr.startswith("__")):
                fel.append(f"{modul}: använder det privata namnet {nod.attr} i {alias[nod.value.id]}")
    for grupp in _cykler(kanter):
        fel.append("importcykel: " + " ↔ ".join(grupp))
    for modul, mal in ((m, t) for m, ts in kanter.items() for t in ts):
        for prefix, forbjudna in (lager or {}).items():
            if _under(modul, prefix) and any(_under(mal, f) and not _under(mal, prefix) for f in forbjudna):
                fel.append(f"{modul}: importerar {mal} (lagerordningen: {prefix} får inte bero på {', '.join(forbjudna)})")
    return sorted(set(fel))
