"""Hallens garderob (#96): mellan 1B, 1C och väggbiten L20 vid 1B:s ände, 500 djup från 1B:s yta mot hallen till
frontens yta, så att den ser ut som en del av väggen.

Väggarna är lätta väggar i invandigt/lattvaggar.py (L20 och fronten L21, med skikten som de andra innerväggarna);
öppningen i fronten mellan ändreglarna står i oppningar.INNEROPPNINGAR. Här är smygen i öppningen (vitmålad furu 15,
som i sovrummets garderob) och två släta dörrblad 22, målade med ljusblå äggoljetempera, i liv med väggens yta, med
dolda gångjärn och tryckspärrar (inga handtag).
"""
from __future__ import annotations

from modellering import Del, Montage, Placering

from trebodar.byggdelar.virke import fmt, virke_i_lada
from trebodar.hus.fonster_och_dorrar.oppningar import INNEROPPNINGAR
from trebodar.hus.invandigt.lattvaggar import T
from trebodar.hus.invandigt.vaggar import skiktets_tjocklek, vaggdef
from trebodar.material import FONSTERTRA, TEMPERA_BLA

SMYG_T, BLAD_T = 15.0, 22.0
SPEL = 3.0                      # mellan bladen och ovanför dem
GOLV = 10.0                     # bladens underkant över golvet


def montage() -> Montage:
    m = Montage("Hallens garderob", beskrivning="Garderob i hallen (#96): smyg av vitmålad furu och två släta dörrar i "
                                                "ljusblå tempera i liv med väggen")
    v = vaggdef("L21")
    _, u0, u1, _, h, _ = next(o for o in INNEROPPNINGAR if o[0] == "L21")
    x_rum = v.origo[0] + skiktets_tjocklek("L21", -1, 500.0)        # rummets yta (w < 0 är mot hallen, x växer)
    x_in = v.origo[0] - T - skiktets_tjocklek("L21", 1, 500.0)      # insidans yta
    y0, y1 = v.origo[1] + u0, v.origo[1] + u1
    for namn, (ya, yb, za, zb, fiber) in (("S", (y0, y0 + SMYG_T, 0.0, h, "z")),
                                          ("N", (y1 - SMYG_T, y1, 0.0, h, "z")),
                                          ("O", (y0 + SMYG_T, y1 - SMYG_T, h - SMYG_T, h, "y"))):
        d, pl = virke_i_lada(x_in, x_rum, ya, yb, za, zb, fiber, FONSTERTRA)
        m.lagg(Del(f"Smygbräda {fmt(x_rum - x_in)}×{fmt(SMYG_T)} hallens garderob", d.form, FONSTERTRA), pl,
               f"HG-SMYG-{namn}")
    fri = y1 - y0 - 2 * SMYG_T
    b = (fri - SPEL) / 2
    z0, z1 = GOLV, h - SMYG_T - SPEL
    for namn, a in (("S", y0 + SMYG_T), ("N", y1 - SMYG_T - b)):          # hängda i smygen
        d, pl = virke_i_lada(x_rum - BLAD_T, x_rum, a, a + b, z0, z1, "z", TEMPERA_BLA)
        m.lagg(Del(f"Garderobsdörr slät tempera ljusblå {fmt(b)}×{fmt(z1 - z0)}", d.form, TEMPERA_BLA), pl,
               f"HG-BLAD-{namn}")
    return m
