"""
Marken vid fasaderna: underlaget till `markniva.MARKNIVA` (panelens underkant) ur den byggda modellen.

För varje yttervägg mäts den högsta punkten på markens delar (berg, uppfyllnad, återfyllning, avsatser och makadam;
inte trätrappan, som står mot panelen) och grundens delar (fasadsten, plattan på marks makadam och fyllning) i ett
band från stommens utsida till 150 mm utanför panelen: snitt parallella med fasaden var 10 mm genom bandet (snittens
kanter, så att de stora markdelarna inte behöver bilda ytor), längs väggen var 10 mm. På väggar där fasadstenen går
upp till bjälklaget (fasad.STENVAGGAR) räknas stenen inte, där gäller linjen bara stuprören. Varje punkt tar det
högsta inom ±10 mm (så att linjen inte skär kanter mellan punkterna) och får 2,5 mm upplägg. Linjen förenklas:
brytpunkterna är mätpunkter och linjen går mellan dem högst 0,4 mm under och högst 10 mm över mätpunkterna, så att
panelen slutar 2,1–12,5 mm över marken. Skriver också MARKEN, marken själv i samma band (berg, uppfyllnad,
återfyllning och makadam; utan grunden, fasadstenen, avsatserna och trapporna), som stuprören och dräneringen
följer. Skriver tabellerna för hus/fasad/markniva.py; modellen ändras inte.

    .venv/bin/python marknivaer.py
"""
import math
import sys
from pathlib import Path

import numpy as np
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / "modellering"), str(HERE.parents[1] / "modeller")]
from geometri import Plan, snitt          # noqa: E402
from modell import Modell                 # noqa: E402
from trebodar import skelett as S         # noqa: E402
from trebodar.hus.fasad import fasad as F  # noqa: E402

BAND_UT = 150.0              # bandet utanför panelen
STEG = 10.0                  # mätpunkternas avstånd längs väggen och snittens genom bandet
UPPLAGG, UNDER, OVER = 2.5, 0.4, 10.0


def forenkla(us, zs):
    """Brytpunkter (mätpunkter) så att linjen mellan dem går högst UNDER under och högst OVER över mätpunkterna."""
    idx = [0, len(us) - 1]
    while True:
        varst, vi = 0.0, None
        for a, b in zip(idx, idx[1:]):
            for i in range(a + 1, b):
                zl = zs[a] + (zs[b] - zs[a]) * (us[i] - us[a]) / (us[b] - us[a])
                fel = max(zs[i] - zl - UNDER, zl - zs[i] - OVER)
                if fel > varst:
                    varst, vi = fel, i
        if vi is None:
            return [(us[i], zs[i]) for i in idx]
        idx = sorted(idx + [vi])


def mark_langs(m, kod, delar):
    """Högsta punkten (z) i bandet per mätpunkt u längs väggen, None där ingen del finns."""
    v = S.YTTERVAGGAR[kod]
    pl = v.placering()
    u0, u1 = F.fasadens_u(kod)
    us = np.arange(u0, u1 + 1e-6, STEG)
    zs = np.full(len(us), -np.inf)
    langs_x = abs(v.u[0]) > 0.5                       # väggen längs x: snitten är y = konstant
    for w in np.arange(-1.0, -(S.T_FASAD + BAND_UT) - 1e-6, -STEG):
        p = pl.punkt((0.0, w, 0.0))
        plan = Plan.tolka(f"y={p[1]:.3f}" if langs_x else f"x={p[0]:.3f}")
        # planets vågräta axel (x eller y) längs väggen: mätpunkterna i planets koordinater
        a = (v.origo[0] if langs_x else v.origo[1]) + (v.u[0] if langs_x else v.u[1]) * us
        for sd in snitt(m, delar, plan):
            for linje in sd.linjer:
                for (p0, z0), (p1, z1) in zip(linje[:-1], linje[1:]):
                    # inte kanternas ändpunkter: en del som bara når fram till mätpunkten räknas inte
                    i = (a > min(p0, p1) + 0.5) & (a < max(p0, p1) - 0.5)
                    if not i.any():
                        continue
                    zs[i] = np.maximum(zs[i], z0 + (a[i] - p0) * (z1 - z0) / (p1 - p0))
    return us, zs


def tabell(m, namn, delar_per_vagg):
    print(f"{namn}: dict[str, tuple[tuple[float, float], ...]] = {{")
    for kod in S.YTTERVAGGAR:
        us, zs = mark_langs(m, kod, delar_per_vagg(kod))
        finns = np.isfinite(zs)
        if not finns.any():
            continue
        us, zs = us[finns], zs[finns]
        zmax = np.array([zs[max(0, i - 1):i + 2].max() for i in range(len(zs))]) + UPPLAGG
        pkt = forenkla(list(us), list(zmax))
        rad = ", ".join(f"({u:g}, {math.ceil(z):g})" for u, z in pkt)
        print(f'    "{kod}": ({rad}),')
    print("}")


def main():
    m = Modell()
    mark = m.valj("Mark", utom="Trätrappa")
    grund = m.valj("Hus/Grund", utom="Källarväggar")
    utan_sten = [d for d in grund if "/Fasadsten" not in d.sokvag]
    tabell(m, "MARKNIVA", lambda kod: mark + (utan_sten if kod in F.STENVAGGAR else grund))
    # urvalet "Mark" tar också plattan på marks delar (Hus/Grund/Plattan på mark/PM-…)
    marken = [d for d in mark if not any(n in d.sokvag for n in ("avsats", "Källartrappa", "Entré", "trappa", "/PM-"))]
    tabell(m, "MARKEN", lambda kod: marken)


if __name__ == "__main__":
    main()
