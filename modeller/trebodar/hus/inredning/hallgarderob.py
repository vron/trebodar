"""Hallens garderob (#96): i hallen väster om 1B, mellan 1A, 1B och väggbiten L20 vid 1B:s ände, 500 djup från 1B:s
yta mot hallen till frontens yta, så att den ser ut som en del av väggen.

Väggarna är lätta väggar i invandigt/lattvaggar.py (L20 och fronten L21, med skikten som de andra innerväggarna);
öppningen i fronten mellan ändreglarna står i oppningar.INNEROPPNINGAR. Här är smygen i öppningen (vitmålad furu 15,
som i sovrummets garderob), en mittstolpe av samma furu och fyra släta dörrblad 22, två på var sida om stolpen,
målade med ljusblå äggoljetempera, i liv med väggens yta, med dolda gångjärn och tryckspärrar (inga handtag).
"""
from __future__ import annotations

from modellering import Del, Montage, Placering

from trebodar.byggdelar.virke import fmt, virke_i_lada
from trebodar.hus.fonster_och_dorrar.oppningar import INNEROPPNINGAR
from trebodar.hus.invandigt.lattvaggar import T
from trebodar.hus.invandigt.vaggar import skiktets_tjocklek, vaggdef
from trebodar.material import FONSTERTRA, TEMPERA_BLA

SMYG_T, BLAD_T = 15.0, 22.0
STOLPE = 45.0                   # mittstolpen mellan dörrparen
SPEL = 3.0                      # mellan bladen och ovanför dem
GOLV = 10.0                     # bladens underkant över golvet


def montage() -> Montage:
    m = Montage("Hallens garderob", beskrivning="Garderob i hallen (#96): smyg av vitmålad furu och fyra släta dörrar "
                                                "i ljusblå tempera i liv med väggen")
    v = vaggdef("L21")
    _, u0, u1, _, h, _ = next(o for o in INNEROPPNINGAR if o[0] == "L21")
    um = (u0 + u1) / 2
    x_rum = v.origo[0] - T - skiktets_tjocklek("L21", 1, um)        # rummets yta (w > T är mot hallen, x avtar)
    x_in = v.origo[0] + skiktets_tjocklek("L21", -1, um)            # insidans yta
    y0, y1 = v.origo[1] + u0, v.origo[1] + u1
    ym = (y0 + y1) / 2
    for namn, (ya, yb, za, zb, fiber) in (("N", (y0, y0 + SMYG_T, 0.0, h, "z")),
                                          ("S", (y1 - SMYG_T, y1, 0.0, h, "z")),
                                          ("M", (ym - STOLPE / 2, ym + STOLPE / 2, 0.0, h - SMYG_T, "z")),
                                          ("O", (y0 + SMYG_T, y1 - SMYG_T, h - SMYG_T, h, "y"))):
        d, pl = virke_i_lada(x_rum, x_in, ya, yb, za, zb, fiber, FONSTERTRA)
        bit = "Mittstolpe" if namn == "M" else "Smygbräda"
        m.lagg(Del(f"{bit} {fmt(x_in - x_rum)}×{fmt(yb - ya)} hallens garderob", d.form, FONSTERTRA), pl,
               f"HG-{'STOLPE' if namn == 'M' else 'SMYG-' + namn}")
    b = (ym - STOLPE / 2 - y0 - SMYG_T - SPEL) / 2                    # två blad i varje halva, hängda i smygen och stolpen
    z0, z1 = GOLV, h - SMYG_T - SPEL
    for nr, a in enumerate((y0 + SMYG_T, ym - STOLPE / 2 - b, ym + STOLPE / 2, y1 - SMYG_T - b), start=1):
        d, pl = virke_i_lada(x_rum, x_rum + BLAD_T, a, a + b, z0, z1, "z", TEMPERA_BLA)
        m.lagg(Del(f"Garderobsdörr slät tempera ljusblå {fmt(b)}×{fmt(z1 - z0)}", d.form, TEMPERA_BLA), pl,
               f"HG-BLAD{nr}")
    return m
