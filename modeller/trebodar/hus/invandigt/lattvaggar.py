"""De lätta väggarnas lägen (planritning 201 rev 02) och fickdörrarnas fickor i väggarna.

Här står bara lägena, så att stommen (de bärande väggarna, hus/stomme) kan läsa fickorna utan att bero på skikten;
stommarna och skikten byggs i vaggar.py. Väggarna i en grupp (inredningen, t.ex. garderoben i sovrummet) byggs av
sin egen modul i hus/inredning; här finns de för lägena (installationernas montering) och för de andra väggarnas
skikt, som går fram till dem.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from trebodar import skelett as S
from trebodar.hus.fonster_och_dorrar.oppningar import INNERDORRAR, Innerdorr

from .skikt import FOLIE, LAKT, SKIVOR_T

T = 70.0                        # de lätta väggarnas stomme
H_VIRKE = 45.0                  # syll, hammarband och överstycke
FICKA_SKENA = 50.0              # fickdörrens skena under överstycket (bladets överkant 10 över öppningen)
_PX, _PY, _NY = (1.0, 0.0), (0.0, 1.0), (0.0, -1.0)
_DIAG = (math.sqrt(0.5), -math.sqrt(0.5))
X_3NV = S.TAKFALL["3NV"].x_insida - FOLIE - LAKT                        # 3NV:s installationsskikt
Y_1NO = S.YTTERVAGGAR["1NO"].origo[1] + S.T_STOMME + FOLIE + LAKT       # 1NO:s installationsskikt


@dataclass(frozen=True)
class Lattvagg:
    kod: str
    origo: tuple[float, float]           # som skelett.Vaggdef: stommens början på sidan w = 0
    u: tuple[float, float]
    langd: float
    beskrivning: str
    syll: bool = True
    grupp: str = ""                      # inredningen: byggs av sin egen modul

    @property
    def vagg(self) -> S.Vaggdef:
        return S.Vaggdef(self.kod, self.origo, self.u, self.langd, T, self.beskrivning)


# garderoben i sovrummet i mittre huskroppen (hus/inredning/garderob.py): rummets sida (w = 0) från stolpen LD4_1
# nedåt, snett 45° och längs trapphålets norra vägg L6 fram till L7; skikten mot rummet är de vanliga
GARDEROB = "Garderob sovrum"
_G_HORN = 600.0                          # det sneda hörnet: 600 × 600
_G_X, _G_Y = 4405.0, 4989.5              # stolpen LD4_1:s västra sida, L6:s norra sida (mot sovrummet)
LATTA = (
    Lattvagg("L1", (9440.0, 2760.0), _PX, X_3NV - 9440.0, "mellan sovrummet och kontoret i höger huskropp"),
    Lattvagg("L2", (11050.0, 2830.0), _PY, 6612.0 - 2830.0, "korridoren i höger huskropp"),
    Lattvagg("L3", (11050.0, 4651.0), _PX, X_3NV - 11050.0, "mellan kontoren (på stolpen LN1_2:s syll)", syll=False),
    Lattvagg("L4", (11050.0, 6542.0), _PX, X_3NV - 11050.0, "mellan kontoret och köket (på huvudstolpens syll)",
             syll=False),
    Lattvagg("L9", (2595.0, Y_1NO), _PY, 5265.0 - Y_1NO, "badrummet mot sovrummet i mittre huskroppen"),
    Lattvagg("L10", (2595.0, 5195.0), _PX, 3275.0 - 2595.0, "badrummets hörn"),
    Lattvagg("L11", (3345.0, 5195.0), _PY, 8185.0 - 5195.0, "badrummet mot allrummet"),
    Lattvagg("L12", (3345.0, 5925.0), _PX, 4405.0 - 3345.0, "över fickdörren mellan allrummet och sovrummet",
             syll=False),
    Lattvagg("L6", (7348.0, 4989.5), _PX, 9370.0 - 7348.0, "trapphålets norra sida, mot sovrummet"),
    Lattvagg("L7", (7348.0, 4989.5), _PY, 5900.0 - 4989.5, "trapphålets västra sida, mot kaminens kåpa"),
    Lattvagg("L13", (6068.0, 5452.0), _PX, 7278.0 - 6068.0, "kaminens kåpa, norra sidan"),
    Lattvagg("L14", (6138.0, 5522.0), _PY, 5900.0 - 5522.0, "kaminens kåpa, västra sidan"),
    Lattvagg("GC", (_G_X, 5900.0), _NY, 5900.0 - (_G_Y + _G_HORN), "garderoben, vid stolpen LD4_1", grupp=GARDEROB),
    Lattvagg("GB", (_G_X, _G_Y + _G_HORN), _DIAG, _G_HORN * math.sqrt(2.0), "garderobens sneda hörn",
             grupp=GARDEROB),
    Lattvagg("GA", (_G_X + _G_HORN, _G_Y), _PX, 7278.0 - SKIVOR_T - (_G_X + _G_HORN),
             "garderobens front med dörrarna, fram till L7:s skikt", grupp=GARDEROB),
)
VAGGAR = {lv.kod: lv.vagg for lv in LATTA}


def vaggdef(kod: str) -> S.Vaggdef:
    return VAGGAR[kod] if kod in VAGGAR else S.INNERVAGGAR[kod]


def fickor(kod: str) -> list[tuple[float, float, float, Innerdorr]]:
    """Fickdörrarnas fickor i väggen (u0, u1, fickans överkant med skena och överstycke, dörren): fickan i dörrens
    egen vägg och fickor som går vidare in i en vägg i samma linje (ID6 från L12 in i 2C)."""
    v = vaggdef(kod)
    Pi = v.placering().invers()
    ut = []
    for d in INNERDORRAR:
        if not d.ficka:
            continue
        dv = vaggdef(d.vagg)
        pd = dv.placering()
        (u0, w0, _), (u1, w1, _) = (Pi.punkt(pd.punkt((u, dv.tjocklek / 2, 0.0))) for u in d.fickan)
        if abs(w1 - w0) > 1.0 or not 0.0 < w0 < v.tjocklek:
            continue
        a, b = max(0.0, min(u0, u1)), min(v.langd, max(u0, u1))
        if b - a > 1.0:
            ut.append((a, b, d.hojd + FICKA_SKENA + H_VIRKE, d))
    return ut
