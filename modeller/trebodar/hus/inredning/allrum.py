"""Möblerna i allrummet (#103): matbordet med sex stolar, mitt under de två PH 5 (AL-L10 och AL-L11), och två
fåtöljer Mathsson Eva hög vid kaminen.

Bordet: skiva 2 200 × 1 000 av oljad ask med rundade hörn, 740 hög, på fyra ben, längs x som lamporna; tre stolar
på varje långsida, med sitsen 450 hög och 100 in under bordet. Bordet och stolarna är inte valda; de visar platsen.

Fåtöljerna (Mathsson Mi 473 Eva hög, flätad linnegjord, mathsson.se): 600 bred, 740 djup och 1 100 hög, sitsen 340;
ram av betsad björk och böjlimmad ek (brun), sits och rygg av naturell sadelgjord av lin, utan huvudkudde. De står
snett på var sin sida om kaminen, vända mot rummet, enligt skissen i ärendet, och minst 500 från kaminens sidoglas
(Rais 600:3: möbler minst 500 från sidoglasen och 950 framför dörren).
"""
from __future__ import annotations

import math

from shapely.geometry import LineString, box as plan_box

from modellering import Del, Form, Material, Montage, Placering, box, prisma

from trebodar import skelett as S
from trebodar.hus.installationer.el.rum.allrum import PH5_X, PH5_Y
from trebodar.hus.rum import KAMINMUR
from trebodar.material import ASK, EVA_RAM, LINNEGJORD

# bordet och stolarna
BORD = (2200.0, 1000.0, 740.0, 30.0)      # längd, bredd, höjd, skivans tjocklek
HORN_R = 150.0
BEN = 60.0
STOL = (450.0, 450.0, 450.0, 900.0)       # bredd, djup, sitshöjd, ryggens överkant
UNDER = 100.0                             # sitsen in under bordet
STOLAR_X = (-650.0, 0.0, 650.0)
# fåtöljerna: (d, h) i profilen, d från framkanten bakåt
EVA = (600.0, 740.0)
ARM = [(650.0, 18.0), (120.0, 18.0), (60.0, 380.0), (120.0, 600.0), (520.0, 600.0)]     # meden, framben och armstöd
SITS = [(40.0, 420.0), (330.0, 340.0), (600.0, 560.0), (700.0, 1090.0)]                 # sitsen och ryggen
ARM_T, ARM_H, SIDA_T, SIDA_H, GJORD_T = 30.0, 36.0, 30.0, 50.0, 6.0
SIDOGLAS_FRI = 500.0
EVA_LAGEN = ((-1, 1350.0, 450.0, 25.0), (1, 1350.0, 450.0, 25.0))      # sida, från mitten, framför kaminen, vridning°


def _bordet(m: Montage) -> None:
    cx, cy = S.HUSKROPPAR[2].nock, PH5_Y                 # mitt mellan lamporna, PH5_X på var sida om nocken
    assert PH5_X > 0.0
    L, B, H, t = BORD
    skiva = plan_box(cx - L / 2 + HORN_R, cy - B / 2 + HORN_R, cx + L / 2 - HORN_R, cy + B / 2 - HORN_R).buffer(HORN_R)
    m.lagg(Del("Matbord, skiva oljad ask", prisma(list(skiva.exterior.coords)[:-1], t, z0=H - t), ASK), Placering(),
           "AR-BORD")
    for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1)), 1):
        x = cx + sx * (L / 2 - 100.0)
        y = cy + sy * (B / 2 - 100.0)
        m.lagg(Del("Matbord, ben", box(x - BEN / 2, x + BEN / 2, y - BEN / 2, y + BEN / 2, 0.0, H - t), ASK),
               Placering(), f"AR-BORD-BEN{i}")
    b, d, hs, hr = STOL
    nr = 0
    for sida in (-1, 1):
        yf = cy + sida * (B / 2 - UNDER)                  # sitsens framkant
        for dx in STOLAR_X:
            nr += 1
            x = cx + dx
            y0, y1 = sorted((yf, yf + sida * d))
            yb0, yb1 = (y1 - 20.0, y1) if sida > 0 else (y0, y0 + 20.0)       # ryggen
            kod = f"AR-STOL{nr}"
            s0, s1 = (y0, y1 - 30.0) if sida > 0 else (y0 + 30.0, y1)            # sitsen fram till bakbenen
            m.lagg(Del("Matstol, sits", box(x - b / 2, x + b / 2, s0, s1, hs - 20.0, hs), ASK), Placering(),
                   f"{kod}-SITS")
            for k, (xx, yy) in enumerate(((x - b / 2, y0), (x + b / 2 - 30.0, y0), (x - b / 2, y1 - 30.0),
                                          (x + b / 2 - 30.0, y1 - 30.0)), 1):
                bak = (yy > y0 + 1.0) == (sida > 0)
                m.lagg(Del("Matstol, ben", box(xx, xx + 30.0, yy, yy + 30.0, 0.0, hr if bak else hs - 20.0), ASK),
                       Placering(), f"{kod}-BEN{k}")
            m.lagg(Del("Matstol, rygg", box(x - b / 2 + 30.0, x + b / 2 - 30.0, yb0, yb1, hr - 250.0, hr), ASK),
                   Placering(), f"{kod}-RYGG")


def _band(bana: list[tuple[float, float]], h: float) -> list[tuple[float, float]]:
    """Profilen runt banan (d, z), h tjock."""
    p = LineString(bana).buffer(h / 2, cap_style="flat", join_style="round", quad_segs=6)
    return [(float(a), float(b)) for a, b in p.exterior.coords][:-1]


def _eva(m: Montage, kod: str, framkant: tuple[float, float], fram: tuple[float, float]) -> None:
    """En Eva hög: profilerna i (d bakåt, z) prismor över bredden (lokala z åt sidan)."""
    fx, fy = fram
    pl = Placering.axlar((framkant[0], framkant[1], 0.0), (-fx, -fy, 0.0), (-fy, fx, 0.0))
    w = EVA[0] / 2
    arm, sida, gjord = _band(ARM, ARM_H), _band(SITS, SIDA_H), _band(SITS, GJORD_T)
    delar: list[tuple[str, str, Form, Material]] = []
    for s, z0 in (("V", -w), ("H", w - ARM_T)):
        delar.append((f"ARM-{s}", "Eva hög, meden och armstödet, böjlimmad ek, brun", prisma(arm, ARM_T, z0=z0),
                      EVA_RAM))
    for s, z0 in (("V", -w + ARM_T), ("H", w - ARM_T - SIDA_T)):
        delar.append((f"SIDA-{s}", "Eva hög, sitsens sida, björk, brun", prisma(sida, SIDA_T, z0=z0), EVA_RAM))
    bredd = 2 * (w - ARM_T - SIDA_T)
    delar.append(("GJORD", "Eva hög, flätad sadelgjord av lin, naturell", prisma(gjord, bredd, z0=-bredd / 2),
                  LINNEGJORD))
    for k, namn, form, mat in delar:
        produkt = "FATOLJ" if k == "ARM-V" else None
        m.lagg(Del(namn, form, mat, artikel="Mathsson Mi 473 Eva hög" if produkt else None, produkt=produkt), pl,
               f"{kod}-{k}")


def _fatoljerna(m: Montage) -> None:
    x0, _, x1, y1 = KAMINMUR.bounds
    xm = (x0 + x1) / 2
    for i, (sida, dx, dy, vrid) in enumerate(EVA_LAGEN, 1):
        fram = (-sida * math.sin(math.radians(vrid)), math.cos(math.radians(vrid)))   # mot rummet, snett mot mitten
        cx, cy = xm + sida * dx, y1 + dy
        d = EVA[1]
        framkant = (cx + fram[0] * d / 2, cy + fram[1] * d / 2)
        _eva(m, f"AR-EVA{i}", framkant, fram)
        assert abs(cx - (x1 if sida > 0 else x0)) - math.hypot(*EVA) / 2 >= SIDOGLAS_FRI, "500 från sidoglaset"


def montage() -> Montage:
    m = Montage("Allrummet", beskrivning="Matbordet med sex stolar under PH-lamporna och två Eva hög vid kaminen "
                                         "(#103)")
    _bordet(m)
    _fatoljerna(m)
    return m
