"""Köket: kylen, frysen, skåpen och skafferiets dörr och hyllor i kökets inbyggnad (ärende #20;
hus/invandigt/kokets_inbyggnad.py: väggarna, smygarna och förrådet ovanför), och bänken och ön (ärende #21,
koksbank.py, med skåpen i koksskap.py).

Kylen (A) och frysen (B) är integrerade vitvaror för nischer 560 breda och 1 780 respektive 880 höga (förenklade som
lådor, 556 breda och 545 djupa med dörren), på en sockel 100 (två reglar och en bottenskiva) med ett sockelgaller 40
mm innanför fronten, där luften till vitvarorna tas in. Över kylen ett skåp upp till öppningen och över frysen ett
högskåp med två hyllor, av vit melamin 16. Fronterna, vitmålade 19 i liv med väggen, 3 mm från smygarna och
varandra, sitter på vitvarornas dörrar och på skåpen, med ett handtag av oljad ask vid den fria kanten (ärende #78;
kylen hängd mot gaveln, frysen mot skafferiet, så att deras handtag sitter intill varandra). Bakom vitvarorna och
skåpen är spalten mot L4, där luften går upp till förrådet. Skafferiet (C) har en dörr av samma slag som fronterna,
hängd i smygen mot frysen och öppnas utåt, och hyllor av vit melamin 19 längs L4 och 3NV.
"""
from __future__ import annotations

from modellering import Del, Montage, Placering, box

from trebodar.byggdelar.virke import fmt
from trebodar.hus.invandigt.kokets_inbyggnad import H_OPPNING, SKAFFERI, fritt
from trebodar.hus.invandigt.lattvaggar import K_SMYG, K_YTA
from trebodar.material import ASK, C24, SKAPSTOMME, SOCKELGALLER, VIT_FRONT, VITVARA

from . import koksbank

FRONT_T, SPEL = 19.0, 3.0
SOCKEL, SOCKEL_IN, GALLER_T = 100.0, 40.0, 20.0           # sockelns höjd, gallret innanför fronten, gallrets djup
SOCKELREGEL, BOTTEN_T = 45.0, 19.0                         # sockelns reglar och bottenskiva
DJUP = 545.0                                              # vitvarornas och skåpens djup bakom fronten
VITVARA_B = 556.0
SKAP_T, HYLLA_T = 16.0, 19.0
Z_TOPP = H_OPPNING - K_SMYG                               # öppningens överkant under smygen
GANGJARN = {"Kyl": -1, "Frys": 1, "Skafferi": -1}          # dörrarnas gångjärn: vid den lägre (−1) eller högre x
HANDTAG = (20.0, 30.0, 400.0)                             # handtagen: bredd, djup ut från fronten, längd (högst)
HANDTAG_KANT, HANDTAG_Z = 40.0, 1050.0                    # handtagets kant från dörrens fria kant; dess mitt över golvet


def _handtag(namn: str, x0: float, x1: float, za: float, zb: float) -> Del:
    """Handtaget av oljad ask på fronten x0–x1, za–zb, vid den fria kanten (mitt emot gångjärnen): lodrätt, högst 40 %
    av frontens höjd, med mitten HANDTAG_Z över golvet eller så nära det som fronten tillåter."""
    b, d, lmax = HANDTAG
    lang = min(lmax, 0.4 * (zb - za))
    zm = min(max(HANDTAG_Z, za + lang / 2 + 100.0), zb - lang / 2 - 100.0)
    xa = x1 - HANDTAG_KANT - b if GANGJARN[namn] < 0 else x0 + HANDTAG_KANT
    return Del(f"Handtag ask {fmt(b)}×{fmt(d)}×{fmt(lang)}", box(xa, xa + b, K_YTA, K_YTA + d, zm - lang / 2,
                                                               zm + lang / 2), ASK, produkt="HANDTAG")
NISCHER = {"Kyl": ("Integrerat kylskåp", 1769.0, ()),     # (vitvaran, dess höjd, hyllornas överkant i skåpet)
           "Frys": ("Integrerat frysskåp", 873.0, (1360.0, 1730.0))}
DORR_Z = 10.0                                             # skafferidörrens underkant
HYLLOR = (450.0, 850.0, 1250.0, 1650.0)                  # skafferiets hyllor, överkant
HYLLA_DJUP = 300.0


def _nisch(namn: str) -> Montage:
    """Sockeln, vitvaran, skåpet ovanför och fronterna i en nisch."""
    vitvara, h, hyllor = NISCHER[namn]
    kod = namn.upper()
    m = Montage(namn, beskrivning=f"{vitvara} med sockel, skåp ovanför och vitmålade fronter")
    x0, x1 = fritt(namn)
    yf = K_YTA - FRONT_T                                  # fronternas baksida, vitvarans och skåpets framsida
    yb, yg = yf - DJUP, K_YTA - SOCKEL_IN - GALLER_T
    zr = SOCKEL - BOTTEN_T
    for i, (a, b) in enumerate(((x0, x0 + SOCKELREGEL), (x1 - SOCKELREGEL, x1)), start=1):
        m.lagg(Del(f"Sockelregel 45×{fmt(zr)}", box(a, b, yb, yg, 0.0, zr), C24), Placering(), f"{kod}-SOCKEL-R{i}")
    m.lagg(Del(f"Bottenskiva {fmt(BOTTEN_T)} sockel", box(x0, x1, yb, yg, zr, SOCKEL), SKAPSTOMME), Placering(),
           f"{kod}-SOCKEL-B")
    m.lagg(Del(f"Sockelgaller {fmt(x1 - x0)}×{fmt(SOCKEL)}", box(x0, x1, yg, yg + GALLER_T, 0.0, SOCKEL),
               SOCKELGALLER), Placering(), f"{kod}-SOCKEL-G")
    xm = (x0 + x1) / 2
    zs = SOCKEL + h
    m.lagg(Del(f"{vitvara} {fmt(VITVARA_B)}×{fmt(DJUP)}×{fmt(h)}",
               box(xm - VITVARA_B / 2, xm + VITVARA_B / 2, yb, yf, SOCKEL, zs), VITVARA, produkt=kod), Placering(), kod)
    # skåpet ovanför: sidor, botten, tak och hyllor
    skap = [("S1", box(x0, x0 + SKAP_T, yb, yf, zs, Z_TOPP)), ("S2", box(x1 - SKAP_T, x1, yb, yf, zs, Z_TOPP)),
            ("B", box(x0 + SKAP_T, x1 - SKAP_T, yb, yf, zs, zs + SKAP_T)),
            ("T", box(x0 + SKAP_T, x1 - SKAP_T, yb, yf, Z_TOPP - SKAP_T, Z_TOPP))]
    skap += [(f"H{i}", box(x0 + SKAP_T, x1 - SKAP_T, yb, yf - 20.0, z - SKAP_T, z)) for i, z in enumerate(hyllor, 1)]
    for k, f in skap:
        m.lagg(Del(f"Skåpstomme {fmt(SKAP_T)}", f, SKAPSTOMME), Placering(), f"{kod}-SKAP-{k}")
    # fronterna på vitvarans dörr och på skåpet
    for k, (za, zb) in (("1", (SOCKEL + SPEL, zs - SPEL)), ("2", (zs, Z_TOPP - SPEL))):
        m.lagg(Del(f"Front vitmålad {fmt(x1 - x0 - 2 * SPEL)}×{fmt(zb - za)}",
                   box(x0 + SPEL, x1 - SPEL, yf, K_YTA, za, zb), VIT_FRONT, produkt="INBYGGNADSFRONTER"), Placering(),
               f"{kod}-FRONT{k}")
        m.lagg(_handtag(namn, x0 + SPEL, x1 - SPEL, za, zb), Placering(), f"{kod}-HANDTAG{k}")
    return m


def _skafferi() -> Montage:
    m = Montage("Skafferi", beskrivning="Vitmålad dörr som fronterna och hyllor av vit melamin längs L4 och 3NV")
    x0, x1 = fritt("Skafferi")
    m.lagg(Del(f"Skafferidörr vitmålad {fmt(x1 - x0 - SPEL)}×{fmt(Z_TOPP - SPEL - DORR_Z)}",
               box(x0, x1 - SPEL, K_YTA - FRONT_T, K_YTA, DORR_Z, Z_TOPP - SPEL), VIT_FRONT,
               produkt="INBYGGNADSFRONTER"), Placering(), "SKAFFERI-DORR")
    m.lagg(_handtag("Skafferi", x0, x1 - SPEL, DORR_Z, Z_TOPP - SPEL), Placering(), "SKAFFERI-HANDTAG")
    sx0, sx1, sy0, sy1 = SKAFFERI
    for i, z in enumerate(HYLLOR, start=1):
        for k, f in (("L4", box(sx0, sx1, sy0, sy0 + HYLLA_DJUP, z - HYLLA_T, z)),
                     ("3NV", box(sx1 - HYLLA_DJUP, sx1, sy0 + HYLLA_DJUP, sy1, z - HYLLA_T, z))):
            m.lagg(Del(f"Hylla {fmt(HYLLA_T)}", f, SKAPSTOMME), Placering(), f"SKAFFERI-HYLLA-{k}-{i}")
    return m


def montage() -> Montage:
    m = Montage("Kök", beskrivning="Kyl, frys och skafferi i kökets inbyggnad (ärende #20), bänken och ön (ärende #21)")
    m.lagg(_nisch("Kyl"))
    m.lagg(_nisch("Frys"))
    m.lagg(_skafferi())
    m.lagg(koksbank.bank())
    m.lagg(koksbank.on())
    return m
