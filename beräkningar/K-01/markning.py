"""Plåtarnas skurna märke (indata.toml [markning]), i plåtens koordinater: x från plåtens ände mot balkens nordöstra
ände, y från kanten mot balkens framsida. Används av modeller/balkplattor/generera.py och R-01.

Märket: lika många hål Ø d_balk som balkens nummer, ett + (överplåt) eller − (underplåt) av raka spår och, på
balkar med flera plåtbitar, lika många hål Ø d_bit som bitens nummer."""


def markning(M: dict, balknr: int, bit: int, n_bitar: int, lage: str) -> tuple[list, list]:
    """Hål [(x, y, d)] och raka spår [(x0, y0, x1, y1)] för plåten balknr-bit-lage (lage "O" eller "U")."""
    hal = [(M["x0"] + i * M["delning"], M["y_balk"], M["d_balk"]) for i in range(balknr)]
    l, b, x0, yc = M["tecken_l"], M["tecken_b"], M["x0"], M["y_tecken"]
    xc = x0 + l / 2
    spar = [(x0, yc - b / 2, x0 + l, yc + b / 2)]
    if lage == "O":
        spar.append((xc - b / 2, yc - l / 2, xc + b / 2, yc + l / 2))
    if n_bitar > 1:
        hal += [(x0 + l + M["delning_bit"] * (i + 1), yc, M["d_bit"]) for i in range(bit)]
    return hal, spar


def kontur_plus(M: dict) -> list[tuple[float, float]]:
    """Plustecknets ytterkontur (12 hörn) för DXF, med samma mått som spåren i markning()."""
    l, b, x0, yc = M["tecken_l"], M["tecken_b"], M["x0"], M["y_tecken"]
    xc, h, a = x0 + l / 2, b / 2, l / 2
    return [(xc - a, yc - h), (xc - h, yc - h), (xc - h, yc - a), (xc + h, yc - a), (xc + h, yc - h), (xc + a, yc - h),
            (xc + a, yc + h), (xc + h, yc + h), (xc + h, yc + a), (xc - h, yc + a), (xc - h, yc + h), (xc - a, yc + h)]
