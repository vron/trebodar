"""Altanen (ärende #30): trädäck av grånad tryckimpregnerad trall 34 × 135 framför skjutpartiet 2SV, mellan
kropparnas fasader 1NV och 3SO, från 2SV ut till gaveln 1SV:s linje, med överkanten i golvets höjd (plan 1, z 0;
skjutpartiets tröskel 33 över). Varje bräda är en egen del. Två val: LANGS (brädorna längs 2SV, annars tvärs) och
RAM (en ram av brädor runt om och brädorna innanför den, annars brädorna kant i kant över hela däcket); fogarna
fördelas lika, nära FOG.

Under brädorna bjälkar 45×145 tvärs brädorna, c/c högst 600 (med ram en extra bjälke under ramens bräda vid
ändarna), på bärlinor 2 × 45×145 längs brädorna, som står på betongplintar Ø200 gjutna i borrade hål i berget
(marken har hål för dem, mark.py). Längs de fria kanterna (ytterkanten och sidan förbi den högra kroppens hörn) en
sargbräda under brädorna, i liv med dem, som täcker bjälkändarna; stommen slutar innanför den. Stuprören DB4-ST2 och DB2-ST2 i de inre hörnen går ned genom däcket, med hål
runt dem. Kanterna mot fasaderna har FRI mm luft."""
from __future__ import annotations

import math

from modellering import Del, Form, Montage, Placering, cylinder, minus

from trebodar import skelett as S
from trebodar.byggdelar.virke import fmt, virke_i_lada
from trebodar.hus.tak.dalar import STOS_D, STOS_FRI
from trebodar.material import BETONG, TRALL, TRYCKIMP

LANGS = True                  # brädorna längs 2SV (x), annars tvärs (y)
RAM = True                    # en ram av brädor runt om
TRALL_T, TRALL_B = 34.0, 135.0
FOG = 5.0                     # fogarna mellan brädorna, ungefär (lika fördelade)
FRI = 10.0                    # luft mot fasaderna
REGEL = (45.0, 145.0)         # bjälkarna, tvärs brädorna
CC_REGEL = 600.0
BALK = (45.0, 145.0)          # bärlinorna: två sida vid sida, längs brädorna
CC_BALK = 1800.0              # högst, mellan bärlinorna (bjälkarnas spännvidd)
CC_PLINT = 1600.0             # högst, mellan plintarna längs bärlinan
INDRAG = 300.0                # bärlinornas och plintarnas indrag från däckets kanter (tvärs bärlinorna)
BALK_INDRAG = 150.0           # bärlinornas ändar innanför stommens kant (bjälkarna kragar ut)
PLINT_D, PLINT_UK = 200.0, -800.0
HAL_FRI = 10.0                # runt stuprören
SARG = (34.0, 145.0)          # sargbrädan längs de fria kanterna: tjocklek, höjd


def _fasad(kod: str) -> float:
    """Fasadens yta (panelens utsida), tvärs väggen: y för väggar längs x, x för väggar längs y."""
    p = S.YTTERVAGGAR[kod].placering().punkt((0.0, -S.T_FASAD, 0.0))
    return p[1] if abs(S.YTTERVAGGAR[kod].u[0]) > 0.5 else p[0]


X0, X1 = _fasad("1NV") + FRI, _fasad("3SO") - FRI
Y0, Y1 = _fasad("2SV") + FRI, _fasad("1SV")
Y_HORN = _fasad("3SV")                    # den högra kroppens hörn: sidan X1 är fri härifrån
# stuprören i de inre hörnen (dalar.py: STOS_FRI från fasaderna)
STUPROR = [(_fasad(kx) + s * (STOS_FRI + STOS_D / 2), _fasad("2SV") + STOS_FRI + STOS_D / 2)
           for kx, s in (("1NV", 1.0), ("3SO", -1.0))]
Z_REGEL = -TRALL_T
Z_BALK = Z_REGEL - REGEL[1]
Z_PLINT = Z_BALK - BALK[1]


def _ab(stomme: bool = False) -> tuple[float, float, float, float]:
    """Däcket längs brädorna (a) och tvärs (b): a0, a1, b0, b1; stommen slutar innanför sargen."""
    x1, y1 = (X1 - SARG[0], Y1 - SARG[0]) if stomme else (X1, Y1)
    return (X0, x1, Y0, y1) if LANGS else (Y0, y1, X0, x1)


def _xy(a0: float, a1: float, b0: float, b1: float) -> tuple[float, float, float, float]:
    return (a0, a1, b0, b1) if LANGS else (b0, b1, a0, a1)


def _jamnt(b0: float, b1: float, bredd: float, fog: float) -> list[tuple[float, float]]:
    """Brädor av bredden från b0 till b1 med lika fogar, nära fog."""
    n = max(1, round((b1 - b0 + fog) / (bredd + fog)))
    f = (b1 - b0 - n * bredd) / (n - 1) if n > 1 else 0.0
    return [(b0 + i * (bredd + f), b0 + i * (bredd + f) + bredd) for i in range(n)]


def _cc(a0: float, a1: float, b: float, cc: float) -> list[float]:
    """Lägen (början) för bitar av bredden b från a0 till a1, c/c högst cc, med en vid varje ände."""
    n = max(1, math.ceil((a1 - a0 - b) / cc))
    return [a0 + i * (a1 - a0 - b) / n for i in range(n + 1)]


def _del(namn: str, kod: str, lada: tuple[float, float, float, float, float, float], fiber: str, mat: object,
         m: Montage) -> None:
    """Virke i lådan (x0, x1, y0, y1, z0, z1), med hål runt stuprören som når det."""
    x0, x1, y0, y1, z0, z1 = lada
    d, pl = virke_i_lada(x0, x1, y0, y1, z0, z1, fiber, mat)                  # type: ignore[arg-type]
    r = STOS_D / 2 + HAL_FRI
    hal: list[Form] = [cylinder(r, z1 - z0 + 2.0, (sx, sy, z0 - 1.0)).placerad(pl.invers())
                       for sx, sy in STUPROR if x0 - r < sx < x1 + r and y0 - r < sy < y1 + r]
    m.lagg(Del(namn, minus(d.form, hal) if hal else d.form, mat), pl, kod)     # type: ignore[arg-type]


def plintar() -> list[tuple[float, float]]:
    """Plintarnas mitt (x, y): under varje bärlina, c/c högst CC_PLINT."""
    a0, a1, b0, b1 = _ab(stomme=True)
    ut = []
    for b in _barlinor(b0, b1):
        for a in _cc(a0 + INDRAG - PLINT_D / 2, a1 - INDRAG + PLINT_D / 2, PLINT_D, CC_PLINT):
            x, _, y, _ = _xy(a + PLINT_D / 2, 0.0, b, 0.0)
            ut.append((x, y))
    return ut


def plintarnas_former() -> list[Form]:
    """Plintarna som cylindrar, för hålen i marken (mark.py)."""
    return [cylinder(PLINT_D / 2, Z_PLINT - PLINT_UK, (x, y, PLINT_UK)) for x, y in plintar()]


def _barlinor(b0: float, b1: float) -> list[float]:
    """Bärlinornas mitt tvärs brädorna."""
    return [b + BALK[0] for b in _cc(b0 + INDRAG - BALK[0], b1 - INDRAG + BALK[0], 2 * BALK[0], CC_BALK)]


def montage() -> Montage:
    m = Montage("Altan", beskrivning="Trädäck av grånad tryckimpregnerad trall 34×135 framför 2SV "
                                     f"({'längs' if LANGS else 'tvärs'}, {'med' if RAM else 'utan'} ram)")
    a0, a1, b0, b1 = _ab()
    fa, fb = ("x", "y") if LANGS else ("y", "x")                 # fibrerna längs a respektive b
    zt = (-TRALL_T, 0.0)
    namn = f"Trall {fmt(TRALL_T)}×{fmt(TRALL_B)} grånad"
    # brädorna: ramen och fältet innanför den
    r = TRALL_B + FOG if RAM else 0.0
    nr = 0
    if RAM:
        for i, (c0, c1) in enumerate(((b0, b0 + TRALL_B), (b1 - TRALL_B, b1)), 1):         # längs brädorna
            _del(namn, f"AL-RAM{i}", (*_xy(a0, a1, c0, c1), *zt), fa, TRALL, m)
        for i, (c0, c1) in enumerate(((a0, a0 + TRALL_B), (a1 - TRALL_B, a1)), 3):         # tvärs, vid ändarna
            _del(namn, f"AL-RAM{i}", (*_xy(c0, c1, b0 + r, b1 - r), *zt), fb, TRALL, m)
    for c0, c1 in _jamnt(b0 + r, b1 - r, TRALL_B, FOG):
        nr += 1
        _del(namn, f"AL-T{nr:02d}", (*_xy(a0 + r, a1 - r, c0, c1), *zt), fa, TRALL, m)
    # bjälkarna tvärs brädorna (med ram också under ramens inre kant vid ändarna), bärlinorna och plintarna
    s0, s1, t0, t1 = _ab(stomme=True)
    lagen = _cc(s0, s1, REGEL[0], CC_REGEL)
    if RAM:
        lagen = sorted(set(lagen) | {a0 + TRALL_B - REGEL[0], a1 - TRALL_B})
    for i, a in enumerate(lagen, 1):
        _del(f"Bjälke tryckimpregnerad {fmt(REGEL[0])}×{fmt(REGEL[1])}", f"AL-B{i:02d}",
             (*_xy(a, a + REGEL[0], t0, t1), Z_BALK, Z_REGEL), fb, TRYCKIMP, m)
    for i, b in enumerate(_barlinor(t0, t1), 1):
        for j, c in enumerate((b - BALK[0], b), 1):
            _del(f"Bärlina tryckimpregnerad {fmt(BALK[0])}×{fmt(BALK[1])}", f"AL-L{i}{'AB'[j - 1]}",
                 (*_xy(s0 + BALK_INDRAG, s1 - BALK_INDRAG, c, c + BALK[0]), Z_PLINT, Z_BALK), fa, TRYCKIMP, m)
    # sargen längs de fria kanterna, under brädorna
    zs = (-TRALL_T - SARG[1], -TRALL_T)
    sarg = f"Sargbräda {fmt(SARG[0])}×{fmt(SARG[1])} grånad"
    _del(sarg, "AL-S1", (X0, X1, Y1 - SARG[0], Y1, *zs), "x", TRALL, m)
    _del(sarg, "AL-S2", (X1 - SARG[0], X1, Y_HORN + FRI, Y1 - SARG[0], *zs), "y", TRALL, m)
    for i, f in enumerate(plintarnas_former(), 1):
        m.lagg(Del(f"Betongplint Ø{fmt(PLINT_D)}", f, BETONG), Placering(), f"AL-P{i:02d}")
    return m
