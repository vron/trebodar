"""Badrummets golv (ärende #52): fallavjämning på mellanbjälklaget, tätskikt och fix och klinker, med fallet mot
golvbrunnen som hus/badrum.py bestämmer (FALLYTOR: duschens kuvert och övrig yta mot duschen).

Varje plan del av golvet är en del per skikt, mellan väggarnas färdiga ytor, kapad efter sitt plan: avjämningen från
bjälklagets överkant upp till BYGGHOJD under golvets yta, tätskiktet och fixet och klinkern ovanpå. Golvbrunnen
(avloppet, hus/installationer/avlopp) står i ett hål i skikten; tätskiktet viks upp mot väggarnas tätskikt och mot
tröskeln i dörren (fönster och dörrar).
"""
from __future__ import annotations

from shapely.geometry import Point, Polygon

from modellering import Del, Form, Kapad, Montage, prisma

from trebodar.byggdelar import polygon as P
from trebodar.byggdelar.virke import fmt
from trebodar.hus.badrum import BYGGHOJD, FALLYTOR, GOLVBRUNN, KLINKER_T, TATSKIKT_T, Fallyta
from trebodar.material import FALLBRUK, KLINKER, TATSKIKT

BRUNN_HAL = 230.0              # hålet i skikten för golvbrunnens klämring
_HOJD = 200.0                  # prismornas höjd före kapningen


def _under(f: Fallyta, yta: Polygon, ned: float) -> Form:
    """Prismat över ytan från bjälklaget upp till ned mm under golvets yta (planet)."""
    a, b, c = f.plan
    x, y = yta.representative_point().coords[0]
    form: Form = prisma(P.kontur(yta), _HOJD, P.hal(yta))
    return Kapad(form, (x, y, a * x + b * y + c - ned), (-a, -b, 1.0))


def _skikt(f: Fallyta, yta: Polygon, z0: float, z1: float) -> Form:
    """Skiktet mellan z0 och z1 mm under golvets yta (z0 > z1)."""
    a, b, c = f.plan
    x, y = yta.representative_point().coords[0]
    return Kapad(_under(f, yta, z1), (x, y, a * x + b * y + c - z0), (a, b, -1.0))


def montage() -> Montage:
    m = Montage("Badrumsgolv", beskrivning="Badrummets golv: fallavjämning, tätskikt och fix och klinker Bricmate J66 "
                                           "Jura 60 × 60 med fall mot golvbrunnen")
    hal = Point(*GOLVBRUNN).buffer(BRUNN_HAL / 2, 32)
    for i, f in enumerate(FALLYTOR, start=1):
        bitar = list(P.polygoner(f.yta.difference(hal), 100.0))
        for j, yta in enumerate(bitar):
            n = f"{i}" if len(bitar) == 1 else f"{i}{'abcdef'[j]}"
            m.lagg(Del(f"Fallavjämning ({f.namn})", _under(f, yta, BYGGHOJD), FALLBRUK), namn=f"BA-FB{n}")
            m.lagg(Del(f"Tätskikt och fix {fmt(TATSKIKT_T)} ({f.namn})", _skikt(f, yta, BYGGHOJD, KLINKER_T), TATSKIKT),
                   namn=f"BA-TS{n}")
            m.lagg(Del(f"Klinker {fmt(KLINKER_T)} ({f.namn})", _skikt(f, yta, KLINKER_T, 0.0), KLINKER),
                   namn=f"BA-KL{n}")
    return m
