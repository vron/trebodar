"""Marken vid fasaderna: panelens underkant per vägg (u, z i väggens system), och marken själv, som stuprörens ände
och dräneringen följer.

Tabellen skrivs av verktyg/modellanalys/marknivaer.py ur den byggda modellen och körs om när marken ändras (ersätt
MARKNIVA med utskriften).
"""
from __future__ import annotations

from trebodar import skelett as S

Z_UK = -S.H_BJALKLAG          # fasadens underkant där marken inte når fasaden: bjälklagets underkant
# marken vid fasaden (u, z) per vägg: panelens underkant, utom där fasadstenen går upp till bjälklaget (STENVAGGAR,
# där linjen gäller stuprören). Ur den byggda modellen med verktyg/modellanalys/marknivaer.py: det högsta av marken,
# avsatserna, återfyllningen och grunden i ett band från stommen till 150 mm utanför panelen, 2,1–12,5 mm över det.
# Körs om när marken ändras (marknivåerna är inte bestämda, ärende #43).
MARKNIVA: dict[str, tuple[tuple[float, float], ...]] = {
    "1NO": ((-65, -1339), (185, -1339), (195, -739), (4425, -739)),
    "1SO": ((-138, -222), (2542, -222), (2552, -223), (3752, -497), (4562, -497), (4572, -306), (4962, -306),
            (4972, -152), (6182, -152), (6192, -306), (6582, -306), (6592, -461), (6882, -461), (6892, -616),
            (7182, -616), (7192, -770), (7482, -770), (7492, -925), (7762, -951), (7772, -737), (12282, -737),
            (12292, -1337), (12312, -1338)),
    "1SV": ((-65, -398), (2275, -223), (4435, -222)),
    "1NV": ((0, -409), (250, -409), (260, -394), (4930, -394)),
    "2NO": ((-65, -1449), (4885, -1449), (4895, -2247), (4935, -2247)),
    "2NV": ((-138, -2247), (902, -2247)),
    "2SV": ((105, -679), (1195, -694), (5015, -409), (5135, -409), (5145, -497), (5165, -497), (5175, -409),
            (5195, -409), (5205, -497), (5215, -497)),
    "2SO": ((80, -739), (3410, -841), (3420, -1441), (3630, -1448)),
    "3NO": ((105, -2247), (2885, -2247), (2895, -2147), (3185, -2147), (3195, -2047), (3485, -2047), (3495, -1947),
            (3785, -1947), (3795, -1847), (4085, -1847), (4095, -1747), (4385, -1747), (4395, -1647), (4405, -1419),
            (4655, -1419)),
    "3NV": ((-138, -1417), (11472, -1062), (11482, -960), (11512, -960)),
    "3SV": ((-65, -959), (4385, -662), (4405, -662), (4415, -774), (4435, -773)),
    "3SO": ((-138, -762), (992, -762), (1002, -679), (1402, -679)),
}


# marken själv vid fasaden (u, z) per vägg, utan grunden, fasadstenen, avsatserna och trapporna: där stenen går upp
# över marken ligger den lägre än MARKNIVA. Stuprörens ände och dräneringen och dagvattnet (täckningen, brunnarnas
# lock) följer den. Ur samma körning av verktyg/modellanalys/marknivaer.py
MARKEN: dict[str, tuple[tuple[float, float], ...]] = {
    "1NO": ((-65, -1339), (205, -1339), (215, -1740), (4425, -1740)),
    "1SO": ((-138, -222), (2542, -222), (2552, -223), (4582, -686), (4592, -1097), (7462, -1097), (7472, -925),
            (7492, -925), (11472, -1312), (12312, -1338)),
    "1SV": ((-65, -398), (2275, -223), (4435, -222)),
    "1NV": ((10, -409), (250, -409), (260, -394), (4930, -394)),
    "2NO": ((-65, -1449), (4875, -1449)),
    "2SV": ((105, -679), (1195, -694), (5005, -409), (5185, -409)),
    "2SO": ((80, -1740), (3360, -1840), (3370, -1716), (3380, -1441), (3400, -1441), (3630, -1448)),
    "3NO": ((2905, -2243), (4385, -1750), (4395, -1419), (4655, -1419)),
    "3NV": ((-138, -1417), (11472, -1062), (11482, -960), (11512, -960)),
    "3SV": ((-65, -959), (4385, -662), (4405, -662), (4415, -774), (4435, -773)),
    "3SO": ((-138, -762), (992, -762), (1002, -679), (1402, -679)),
}


def _langs(m: tuple[tuple[float, float], ...], u: float) -> float:
    for (ua, za), (ub, zb) in zip(m, m[1:]):
        if ua <= u <= ub:
            return za if ub == ua else za + (zb - za) * (u - ua) / (ub - ua)
    return float(m[0][1] if u < m[0][0] else m[-1][1])


def mark_vid(kod: str, u: float) -> float:
    """Marken vid fasaden i u (MARKNIVA, panelens underkant; Z_UK där marken inte når fasaden)."""
    return _langs(MARKNIVA.get(kod, ((0.0, Z_UK), (1.0, Z_UK))), u)


def marken_vid(kod: str, u: float) -> float:
    """Marken själv vid fasaden i u (MARKEN), utanför fasadstenen; MARKNIVA där marken inte finns i tabellen."""
    return _langs(MARKEN[kod], u) if kod in MARKEN else mark_vid(kod, u)
