"""Dubbelsängen i sovrummet (ärende #27), för att se hur rummet räcker: madrass 160 × 200 cm, huvudgaveln mot
väggen 2B, mitt mellan väggarna 2A och L6 (gipsens ytor). Enkel: ben, sarg och huvudgavel av ask, ribbotten av
björkplywood, madrass, täcke och två kuddar."""
from __future__ import annotations

from modellering import Del, Montage, Placering, box

from trebodar import skelett as S
from trebodar.hus.invandigt.lattvaggar import vaggdef
from trebodar.hus.invandigt.skikt import SKIVOR_T
from trebodar.material import ASK, BJORKPLYWOOD, SANGKLADER

BREDD, LANGD = 1600.0, 2000.0               # madrassen
SARG_T, SARG_Z = 25.0, (150.0, 350.0)       # sargen: tjocklek, under- och överkant
BEN = 50.0                                  # benen under sargens hörn
GAVEL_T, GAVEL_H = 40.0, 1000.0             # huvudgaveln, från golvet
BOTTEN_T, BOTTEN_Z = 18.0, 250.0            # ribbotten, överkant
MADRASS_H = 220.0
TACKE_T, TACKE_FRAN_GAVEL = 60.0, 550.0     # täcket från huvudänden
KUDDE = (450.0, 600.0, 120.0)               # längs sängen, tvärs, höjd

# väggarnas ytor mot sovrummet: 2B (huvudgaveln) och 2A och L6 (sängen mitt emellan)
X_VAGG = S.INNERVAGGAR["2B"].origo[0] - S.INNERVAGGAR["2B"].tjocklek - SKIVOR_T
Y_MITT = ((S.INNERVAGGAR["2A"].origo[1] + S.INNERVAGGAR["2A"].tjocklek + SKIVOR_T)
          + (vaggdef("L6").origo[1] - SKIVOR_T)) / 2


def montage() -> Montage:
    m = Montage("Säng", beskrivning="Dubbelsäng 160 × 200 i sovrummet, huvudgaveln mot 2B")
    xh = X_VAGG - GAVEL_T                       # huvudgavelns framsida, sängens huvudände
    xf = xh - LANGD - SARG_T                    # fotänden (sargens utsida)
    y0, y1 = Y_MITT - BREDD / 2 - SARG_T, Y_MITT + BREDD / 2 + SARG_T
    z0, z1 = SARG_Z
    m.lagg(Del(f"Huvudgavel ask {GAVEL_T:g}", box(xh, X_VAGG, y0, y1, 0.0, GAVEL_H), ASK), Placering(), "SG-GAVEL")
    sarg = [(xf, xh, y0, y0 + SARG_T), (xf, xh, y1 - SARG_T, y1), (xf, xf + SARG_T, y0 + SARG_T, y1 - SARG_T)]
    for i, (a, b, c, d) in enumerate(sarg, 1):
        m.lagg(Del(f"Sarg ask {SARG_T:g}", box(a, b, c, d, z0, z1), ASK), Placering(), f"SG-SARG{i}")
    for i, (a, c) in enumerate(((xf, y0), (xf, y1 - BEN), (xh - BEN, y0), (xh - BEN, y1 - BEN)), 1):
        m.lagg(Del(f"Ben ask {BEN:g}", box(a, a + BEN, c, c + BEN, 0.0, z0), ASK), Placering(), f"SG-BEN{i}")
    xi0, yi0, yi1 = xf + SARG_T, y0 + SARG_T, y1 - SARG_T  # innanför sargen
    m.lagg(Del(f"Ribbotten björkplywood {BOTTEN_T:g}", box(xi0, xh, yi0, yi1, BOTTEN_Z - BOTTEN_T, BOTTEN_Z),
               BJORKPLYWOOD), Placering(), "SG-BOTTEN")
    zm = BOTTEN_Z + MADRASS_H
    m.lagg(Del(f"Madrass {BREDD:g} × {LANGD:g}", box(xi0, xh, yi0, yi1, BOTTEN_Z, zm), SANGKLADER), Placering(),
           "SG-MADRASS")
    m.lagg(Del("Täcke", box(xi0, xh - TACKE_FRAN_GAVEL, yi0, yi1, zm, zm + TACKE_T), SANGKLADER), Placering(),
           "SG-TACKE")
    kl, kb, kh = KUDDE
    for i, yc in enumerate((Y_MITT - BREDD / 4, Y_MITT + BREDD / 4), 1):
        m.lagg(Del("Kudde", box(xh - 30.0 - kl, xh - 30.0, yc - kb / 2, yc + kb / 2, zm, zm + kh), SANGKLADER),
               Placering(), f"SG-KUDDE{i}")
    return m
