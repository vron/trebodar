"""Rören P1–P19 i källaren (K-05, R-05.5): VKR 80×80×4 S235 från bottenplattans överkant till mellanbjälklagets
underkant, topplåt 80×80×8 ingjuten i bjälklagets underkant och fotplåt 200×200×15 S355 ingjuten i plintens
överkant. P7 har två rör tätt intill varandra i x-led på en gemensam fotplåt 280×200×15."""
from __future__ import annotations

from modellering import Del, Montage, Placering, box, prisma

from trebodar import skelett as S
from trebodar.material import S235, S355

Z0, Z1 = S.Z_BOTTENPLATTA, -S.H_BJALKLAG
VKR, T_VKR = 80.0, 4.0
TOPP_T, FOT_T = 8.0, 15.0
# rörens mitt (K-05), P7 med två rör
PELARE = {"P1": (11670.0, 10625.0), "P2": (7101.659, 9154.763), "P3": (11670.0, 8625.0), "P4": (2870.0, 7675.0),
          "P5": (11670.0, 6625.0), "P6": (7420.0, 5950.0), "P7": (9470.0, 5950.0), "P8": (1931.0, 5820.0),
          "P9": (3231.0, 5820.0), "P10": (4531.0, 5820.0), "P11": (5770.0, 4990.0), "P12": (6870.0, 4990.0),
          "P13": (7970.0, 4990.0), "P14": (9070.0, 4990.0), "P15": (11670.0, 4685.0), "P16": (9070.0, 3590.0),
          "P17": (11670.0, 2545.0), "P18": (6990.0, 2190.0), "P19": (9070.0, 2190.0)}
ANTAL = {"P7": 2}

ROR = Del("VKR 80×80×4 L=2100", prisma([(0, 0), (VKR, 0), (VKR, VKR), (0, VKR)], Z1 - Z0,
                                        [[(T_VKR, T_VKR), (VKR - T_VKR, T_VKR), (VKR - T_VKR, VKR - T_VKR),
                                          (T_VKR, VKR - T_VKR)]]), S235, artikel="VKR 80×80×4 S235 (SS-EN 10219)")
TOPP = Del("Topplåt 80×80×8", box(0, VKR, 0, VKR, 0, TOPP_T), S235)


def plater(n: int) -> tuple[float, float]:
    return (200.0, 200.0) if n == 1 else (280.0, 200.0)


def fotplat(n: int) -> Del:
    b, d = plater(n)
    return Del(f"Fotplåt {b:g}×{d:g}×15", box(0, b, 0, d, 0, FOT_T), S355)


def montage() -> Montage:
    m = Montage("Rör", beskrivning="VKR 80×80×4 med topp- och fotplåtar (K-05, R-05.5)")
    for namn, (x, y) in PELARE.items():
        n = ANTAL.get(namn, 1)
        g = Montage(namn, namn, f"Rör {namn}" + (", två rör" if n > 1 else ""))
        for k in range(n):
            xk = x + k * VKR
            suffix = f"-{k + 1}" if n > 1 else ""
            g.lagg(ROR, Placering.flytt(xk - VKR / 2, y - VKR / 2, Z0), f"{namn}{suffix}-R")
            g.lagg(TOPP, Placering.flytt(xk - VKR / 2, y - VKR / 2, Z1), f"{namn}{suffix}-T")
        b, d = plater(n)
        xm = x + (n - 1) * VKR / 2
        g.lagg(fotplat(n), Placering.flytt(xm - b / 2, y - d / 2, Z0 - FOT_T), f"{namn}-F")
        m.lagg(g)
    return m


def topplatar() -> list[tuple[float, float, float, float]]:
    """Topplåtarnas utbredning i plan (x0, x1, y0, y1), för ursparingar i mellanbjälklaget."""
    ut = []
    for namn, (x, y) in PELARE.items():
        for k in range(ANTAL.get(namn, 1)):
            xk = x + k * VKR
            ut.append((xk - VKR / 2, xk + VKR / 2, y - VKR / 2, y + VKR / 2))
    return ut


def fotplat_mitt() -> dict[str, tuple[float, float]]:
    """Fotplåtarnas mitt i plan per rör (för P7 mellan rören): lastytans mitt, där plinten står."""
    return {namn: (x + (ANTAL.get(namn, 1) - 1) * VKR / 2, y) for namn, (x, y) in PELARE.items()}


def fotplatar() -> list[tuple[float, float, float, float]]:
    ut = []
    for namn, (xm, y) in fotplat_mitt().items():
        b, d = plater(ANTAL.get(namn, 1))
        ut.append((xm - b / 2, xm + b / 2, y - d / 2, y + d / 2))
    return ut
