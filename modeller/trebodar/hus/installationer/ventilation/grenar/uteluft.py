"""Uteluftsdon i ytterväggarna: vanliga väggventiler Ø100 utöver ventilerna i fönsterkarmarna.

- I sovrummet (västra väggen 2SO, norr om fönsterdörren) och i det lilla sovrummet (norra gaveln 3NO, mellan fönstren:
  användarens märke i #108, där rummet kallas gästrummet), för ersättningsluften när köksfläkten forceras. Det
  undertryck som återstår accepteras (kaminen tar sin förbränningsluft utifrån i en egen kanal). De sitter 2 300 mm
  över golvet, över fönstrens överkant.
- I skafferiet (#143), genom ytterväggen 3NV över den översta hyllan och under skafferiets tak (2 100), så att
  skafferiet kan hållas kallare med ventilen öppen. Luften går vidare under skafferidörren till köket och frånluften.

Donen sitter mitt i ett regelfack (skafferiets: mellan väggen L4 och regeln 3NV-R22), med hylsan rakt genom
ytterväggen och galler på fasaden. De har ingen fläkt och räknas inte till frånluften: flödet är vad undertrycket
drar in.
"""
from __future__ import annotations

from ...montering import utsida, vagg
from ..delar import Avluft, Don, Gren, Kanal
from ..katalog import GALLER_100, UTELUFTSDON_100, VAGGHYLSA_100

Z = 2300.0
Z_SKAFFERI = 1960.0             # över den översta hyllan (1 650) och installationsläkten vid 1 800–1 845, donet Ø160
                                # under skafferiets tak (2 100)
# (id, namnet, rummet, väggen, läget längs väggen: mitt i regelfacket, höjden)
LAGEN = (("UL1", "Uteluftsdon i sovrummet", "Sovrum", "2SO", 2012.0, Z),                       # 2SO-R08 till 2SO-R09
         ("UL2", "Uteluftsdon i det lilla sovrummet", "Sovrum, litet", "3NO", 1940.0, Z),      # 3NO-R08 till 3NO-R09
         ("UL3", "Uteluftsdon i skafferiet", "Skafferi", "3NV", 5761.0, Z_SKAFFERI))         # L4 till 3NV-R22

UTELUFT = tuple(
    Gren(id_, namn, rum, 0.0, (
        Don(f"{id_}-D1", UTELUFTSDON_100, vagg(kod, u, z)),
        Kanal(f"{id_}-K1", VAGGHYLSA_100),                       # genom ytterväggen
        Avluft(f"{id_}-A1", GALLER_100, utsida(kod, u, z)),
    ), uteluft=True, beskrivning=(
        f"Väggventil Ø100 genom ytterväggen {kod}, ställbar med filter på insidan och galler på fasaden.",))
    for id_, namn, rum, kod, u, z in LAGEN)
