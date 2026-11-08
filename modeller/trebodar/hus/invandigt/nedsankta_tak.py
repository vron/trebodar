"""Nedsänkta innertak (#106) i de två små likadana rummen i högra huskroppen bortom köket: det lilla kontoret (mellan
L1 och L3) och gästrummet (mellan L3 och L4), båda från L2 till ytterväggen 3NV. Det tredje lilla rummet, mot gaveln
3NO, har kvar det snedda innertaket.

Ett plant tak så högt att stolpen LN1_3:s snedsträvor (underkant z 2 825) precis döljs: takreglar 45×95 längs x c/c
600 och längs väggarna, med överkanten i snedsträvornas underkant, upphängda i takbalkarna, och gips 2 × 12,5 under
dem, från L2 till där det snedda innertaket mot 3NV sjunker till det plana takets höjd. Det snedda innertaket
ovanför är kvar (dolt).
"""
from __future__ import annotations

from functools import cache

from shapely.geometry import Polygon

from modellering import Del, Montage, Placering, box

from trebodar.hus.stomme import lagen
from trebodar.material import C24, GIPS

from .lattvaggar import T, VAGGAR, X_3NV
from .skikt import SKIVA, SKIVOR_T, innertak_vid, kapad_vid_taket

REGEL = (45.0, 95.0)            # takreglarna: bredd, höjd
CC = 600.0


@cache
def regel_ok() -> float:
    """Takreglarnas överkant: snedsträvornas underkant (stolpen LN1_3)."""
    return min(d.lada[2] for d in lagen.stolpe("LN1_3") if d.typ == "D")


def z_tak() -> float:
    """Det nedsänkta takets undersida (gipsens yta) över golvet."""
    return regel_ok() - REGEL[1] - 2 * SKIVA


def _dar_snedtaket_nar(z: float, x0: float, x1: float, y: float) -> float:
    """x där det snedda innertaket mot 3NV sjunker till höjden z (mellan x0 och x1)."""
    for _ in range(40):
        xm = (x0 + x1) / 2
        x0, x1 = (xm, x1) if innertak_vid(xm, y) > z else (x0, xm)
    return x0


def rummen() -> dict[str, tuple[float, float, float, float]]:
    """Rummen mellan väggarnas färdiga ytor (x0, x1, y0, y1): från L2 till där det snedda innertaket mot 3NV möter
    det nedsänkta takets gips."""
    x0 = VAGGAR["L2"].origo[0] + T + SKIVOR_T
    x1 = _dar_snedtaket_nar(z_tak(), 11655.0, X_3NV - SKIVOR_T, VAGGAR["L3"].origo[1])
    y_l1 = VAGGAR["L1"].origo[1] + T + SKIVOR_T
    y_l3 = VAGGAR["L3"].origo[1]
    y_l4 = VAGGAR["L4"].origo[1]
    return {"Kontor, litet": (x0, x1, y_l1, y_l3 - SKIVOR_T),
            "Gästrum": (x0, x1, y_l3 + T + SKIVOR_T, y_l4 - SKIVOR_T)}


def montage() -> Montage:
    m = Montage("Nedsänkta tak", beskrivning="Plana innertak i det lilla kontoret och gästrummet (#106): takreglar "
                                             "45×95 och gips 2 × 12,5")
    zr = regel_ok()
    zg = z_tak()
    b, h = REGEL
    for i, (namn, (x0, x1g, y0, y1)) in enumerate(rummen().items(), start=1):
        kod = f"NT{i}"
        x1 = _dar_snedtaket_nar(zr, x0, x1g, (y0 + y1) / 2) - 5.0     # där snedtaket når reglarnas överkant
        n = int((y1 - y0 - b) // CC) + 1
        ys = [y0 + k * (y1 - y0 - b) / max(n, 1) for k in range(n + 1)]
        for k, y in enumerate(ys, start=1):                 # längs x, c/c högst CC, de yttersta mot väggarna
            m.lagg(Del(f"Takregel 45×95 {namn}", box(x0 + b, x1 - b, y, y + b, zr - h, zr), C24), Placering(),
                   f"{kod}-R{k:02d}")
        for k, x in enumerate((x0, x1 - b), start=1):       # tvärs, i x-ändarna
            m.lagg(Del(f"Takregel 45×95 {namn}", box(x, x + b, y0, y1, zr - h, zr), C24), Placering(),
                   f"{kod}-K{k}")
        for k, (za, zb) in enumerate(((zg + SKIVA, zg + 2 * SKIVA), (zg, zg + SKIVA)), start=1):
            xg = _dar_snedtaket_nar(za, x0, x1g, (y0 + y1) / 2) + 1.0    # gipsen fram till snedtaket, kapad längs
            yta = Polygon([(x0, y0), (xg, y0), (xg, y1), (x0, y1)])           # dess yta så att de möts i en linje
            m.lagg(Del(f"Gips 12,5 nedsänkt tak {namn}", kapad_vid_taket(box(x0, xg, y0, y1, za, zb), yta), GIPS),
                   Placering(), f"{kod}-GI{k}")
    return m
