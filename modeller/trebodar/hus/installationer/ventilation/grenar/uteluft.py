"""Uteluftsdon i ytterväggarna (#108): två vanliga väggventiler Ø100 utöver ventilerna i fönsterkarmarna, en i
sovrummet (västra väggen 2SO, norr om fönsterdörren) och en i det lilla sovrummet (norra gaveln 3NO, mellan fönstren:
användarens märke i #108, där rummet kallas gästrummet), för
ersättningsluften när köksfläkten forceras. Det undertryck som återstår accepteras (kaminen tar sin förbränningsluft
utifrån i en egen kanal).

Donen sitter 2 300 mm över golvet (över fönstrens överkant), mitt i ett regelfack, med hylsan rakt genom ytterväggen
och galler på fasaden. De har ingen fläkt och räknas inte till frånluften: flödet är vad undertrycket drar in.
"""
from __future__ import annotations

from ...montering import utsida, vagg
from ..delar import Avluft, Don, Gren, Kanal
from ..katalog import GALLER_100, UTELUFTSDON_100, VAGGHYLSA_100

Z = 2300.0
# (id, namnet, rummet, väggen, läget längs väggen: mitt i regelfacket)
LAGEN = (("UL1", "Uteluftsdon i sovrummet", "Sovrum", "2SO", 2012.0),                        # 2SO-R08 till 2SO-R09
         ("UL2", "Uteluftsdon i det lilla sovrummet", "Sovrum, litet", "3NO", 1940.0))       # 3NO-R08 till 3NO-R09

UTELUFT = tuple(
    Gren(id_, namn, rum, 0.0, (
        Don(f"{id_}-D1", UTELUFTSDON_100, vagg(kod, u, Z)),
        Kanal(f"{id_}-K1", VAGGHYLSA_100),                       # genom ytterväggen
        Avluft(f"{id_}-A1", GALLER_100, utsida(kod, u, Z)),
    ), uteluft=True, beskrivning=(
        f"Väggventil Ø100 genom ytterväggen {kod}, ställbar med filter på insidan och galler på fasaden.",))
    for id_, namn, rum, kod, u in LAGEN)
