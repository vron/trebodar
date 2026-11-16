"""Källaren (användarens markeringar och kommentarer): tvättmaskinen och ett tvättho vid västra ytterväggen V21 (under
en bänk) och ett tvättho i källarrummet vid V15:s västsida. Rören kommer upp genom bottenplattan strax innanför
väggen (golvstosar), inte i väggarna: tvättens från de nedre fördelarna i fördelarskåpet under plattan i cellplasten
(teknikrum.ORDNING_NED, gruppen N1), källarrummets tvättho (KA-TH2), som bara har kallvatten, direkt från
vattenmätaren under köket (#139, teknikrum.DIREKT).

Stosarna står mellan bottenplattans armeringsjärn (stos), kallt och varmt bredvid varandra ut från väggen: rören under
plattan kommer längs väggen och viker upp till stosen, det yttre röret längst bort (teknikrum.ror_under_plattan).
Tvätthonas avlopp står i golvet framför dem (../../avlopp, TVATTHON).
"""
from __future__ import annotations

from ...montering import kallarvagg
from ..katalog import GOLVSTOS, PEM_20, ROR_I_ROR_16, TVATTHO, TVATTHO_KALLT, TVATTMASKIN
from ..punkter import Rum, Tappstalle
from .stos import stos

RUM = Rum("KA", "Källare", plan=0)

FRAN_VAGGEN = {"TM": 70.0, "TH1": 150.0, "TH2": 90.0}     # stosarnas mitt från väggens gips
_V21 = kallarvagg("V21", 0.0, 0.0, 1).punkt[0]
_V15 = kallarvagg("V15", 0.0, 0.0, -1).punkt[0]

TAPPSTALLEN = [
    # kallvattnet närmast väggen: fritt från tvätthoets rör som går norrut öster om det
    Tappstalle("KA-TM1", TVATTMASKIN, GOLVSTOS, stos(_V21 + FRAN_VAGGEN["TM"], 8420.0, GOLVSTOS, (-1.0, 0.0, 0.0)),
               ROR_I_ROR_16, kallt=(-1.0, 0.0, 0.0)),
    # kallt närmast väggen (västerut): rören viker upp i den ordningen från filerna under plattan
    Tappstalle("KA-TH1", TVATTHO, GOLVSTOS, stos(_V21 + FRAN_VAGGEN["TH1"], 7800.0, GOLVSTOS, (-1.0, 0.0, 0.0)),
               ROR_I_ROR_16, kallt=(-1.0, 0.0, 0.0)),
    # vid V15 ligger balkens järn tätt: stosen flyttas åt alla håll
    Tappstalle("KA-TH2", TVATTHO_KALLT, GOLVSTOS, stos(_V15 - FRAN_VAGGEN["TH2"], 8630.0, GOLVSTOS, langs=None), PEM_20),
]
