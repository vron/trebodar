"""Stommens förankringsbeslag (K-03, K-04) i ett lokalt system vid den stående delens sida: x ut från sidan (längs
den liggande skänkeln), y längs sidan, z uppåt, origo i sidan mitt för beslaget på underlagets överkant.

- Vinkelbeslaget Simpson Strong-Tie ABR10525 (ETA-06/0106): en skänkel mot regeln eller stolpen och en på syllen
  eller plattan, 90 breda, med två hål för betongbultar bredvid ribban (BULT_U från sidan, ±BULT_V från mitten).
- Förankringsbeslaget Rothoblaas WHT340 (ETA-23/0813): plåten mot regeln, spikad med LBA, och bottenplattan med hålet
  för ankaret M16 (WHT_ANKARE från sidan).
"""
from __future__ import annotations

from modellering import Form, box, cylinder

# vinkelbeslaget: skänkeln mot den stående delen (höjd), skänkeln på underlaget (längd), bredden och godset
ABR_A, ABR_B, ABR_BREDD, ABR_T = 105.0, 105.0, 90.0, 2.5
BULT_U, BULT_V = 60.0, 22.5              # bultens hål: från sidan och från beslagets mitt (bredvid ribban)
HAL_D = 12.0                             # hålet för bulten M12 (i modellen bultens diameter, utan glipa)

# förankringsbeslaget WHT340: plåtens höjd, bredd och gods, bottenplattans djup och tjocklek (med brickan) och ankaret
WHT_H, WHT_B, WHT_T = 340.0, 60.0, 3.0
WHT_P, WHT_BOTTEN = 60.0, 9.0
WHT_ANKARE = 30.0                        # ankarets axel från sidan
WHT_D = 16.0


def vinkelbeslag(hal: tuple[float, ...] = (-BULT_V, BULT_V)) -> Form:
    """ABR10525 i det lokala systemet, med hålen vid y i hal."""
    f = box(0.0, ABR_B, -ABR_BREDD / 2, ABR_BREDD / 2, 0.0, ABR_T) | box(0.0, ABR_T, -ABR_BREDD / 2, ABR_BREDD / 2,
                                                                         0.0, ABR_A)
    for y in hal:
        f = f - cylinder(HAL_D / 2, ABR_T + 2.0, (BULT_U, y, -1.0))
    return f


def forankringsbeslag() -> Form:
    """WHT340 i det lokala systemet: plåten mot sidan och bottenplattan med hålet för ankaret."""
    f = box(0.0, WHT_T, -WHT_B / 2, WHT_B / 2, 0.0, WHT_H) | box(0.0, WHT_P, -WHT_B / 2, WHT_B / 2, 0.0, WHT_BOTTEN)
    return f - cylinder(WHT_D / 2, WHT_BOTTEN + 2.0, (WHT_ANKARE, 0.0, -1.0))
