"""Inköpslistans specialprodukter i modellen: delar och montage med `produkt` (en kod i inköpslistan), med deras
instanser, och kontrollen av koderna mot inköpslistan.

En specialprodukt väljs, beställs eller tillverkas för sig (vitvaror, fönster, armaturer, specialtillverkat stål
och limträ …), till skillnad från vanligt material (virke, skivor, isolering, armering, kabel, rör). Modellen märker produkten där den skapas (`Del(..., produkt=)`,
`Montage(..., produkt=)`), så att antalet och instanserna följer modellen; inköpslistan (en toml-fil med en
`[[produkt]]` per kod) har det som inte är geometri: vald produkt, status, ansvarig roll och skede. En produkt som
inte är modellerad anger sin omfattning i listan."""
from __future__ import annotations

import tomllib
from pathlib import Path

from .modell import Montage


def instanser(rot: Montage) -> dict[str, list[dict[str, object]]]:
    """Specialprodukterna i modellen: kod -> instanserna (sökväg, instansens namn, typ och antal delar), i trädets
    ordning. En del eller ett montage inuti ett montage med samma kod hör till den produkten och räknas inte."""
    ut: dict[str, list[dict[str, object]]] = {}

    def ga(m: Montage, vag: str, kod_ovan: str | None) -> None:
        for i in m.barn:
            x, v = i.barn, f"{vag}/{i.namn}"
            kod = x.produkt
            if kod and kod != kod_ovan:
                ut.setdefault(kod, []).append({
                    "sokvag": v, "namn": i.namn,
                    "typ": (x.beskrivning or x.namn) if isinstance(x, Montage) else x.namn,
                    "delar": x.antal_delar() if isinstance(x, Montage) else 1})
            if isinstance(x, Montage):
                ga(x, v, kod or kod_ovan)

    ga(rot, rot.namn, rot.produkt)
    return ut


def kontroll(rot: Montage, lista: Path) -> tuple[dict[str, list[dict[str, object]]], list[str]]:
    """Modellens koder mot inköpslistan: varje kod i modellen står i listan, och varje produkt i listan finns i
    modellen eller anger sin omfattning (inte modellerad), inte båda. Returnerar instanserna och felen."""
    inst = instanser(rot)
    koder = {p["kod"]: p for p in tomllib.loads(lista.read_text(encoding="utf-8")).get("produkt", [])}
    fel = [f"{k}: {len(v)} i modellen (t.ex. {v[0]['sokvag']}) men inte i inköpslistan"
           for k, v in inst.items() if k not in koder]
    fel += [f"{k}: i inköpslistan men inte i modellen; märk den i modellen (produkt=) eller ange omfattning"
            for k, p in koder.items() if k not in inst and "omfattning" not in p]
    fel += [f"{k}: {len(inst[k])} i modellen, men inköpslistan anger omfattning (inte modellerad): ta bort den"
            for k, p in koder.items() if k in inst and "omfattning" in p]
    return inst, fel
