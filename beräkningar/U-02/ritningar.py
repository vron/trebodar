"""
U-02 Fasadsten på källarväggarna, infästning (F-01 avsnitt 6), A3 med ../ritningsmall:

    U-02.1  Sektion och detaljer                         1:10, 1:2,5, 1:2
    U-02.2  Fasad, konsol, positioner och dimensionering 1:20, 1:2,5, 1:5

Underlag: indata.toml och resultat.json (berakning.py). Allt ritas i verkliga koordinater i mm: x = 0 i
betongkärnans yttre yta (utåt positivt), y = 0 i stödvinkelns överkant (stenens underkant). I fasaden (U-02.2) är
x längs väggen. ritningsmall/ritning.py skalar till papperet.

Filen är uppdelad i:
    1. Underlag           mått ur indata och resultat
    2. Byggdelar          vägg, sten, konsol, ankare (ritas i flera vyer)
    3. Vyer               en funktion per vy
    4. Blad               högerkolumn, tabeller och ritningshuvud
    5. main               skriver U-02.x.json och PDF:en i ritningar/

    python beräkningar/U-02/berakning.py
    python beräkningar/U-02/ritningar.py
"""
import json
import math
import os
import sys
import tomllib

HERE = os.path.dirname(os.path.abspath(__file__))
BER = os.path.dirname(HERE)
ROT = os.path.dirname(BER)
UT = os.path.join(ROT, "ritningar")
sys.path.insert(0, os.path.join(BER, "ritningsmall"))
from ritning import Vy, Blad, huvud, sv, PROJEKT  # noqa: E402

# ================================================================== 1. underlag
IN = tomllib.loads(open(os.path.join(HERE, "indata.toml"), encoding="utf-8").read())
R = json.load(open(os.path.join(HERE, "resultat.json"), encoding="utf-8"))

NR = IN["projekt"]["dokument"]
REV, DATUM = IN["projekt"]["revision"], IN["projekt"]["datum"]
UNDERLAG = "Kub TG 2216, K-06"
REVISIONER = [dict(rev=REV, avser="Första utgåvan", datum=DATUM, sign=PROJEKT["signatur"])]

KARNA, EPS, GIPS = IN["vagg"]["karna"], IN["vagg"]["eps"], IN["vagg"]["gips"]
X = R["lagen"]
X_BRUK, X_STB, X_STF = X["bruk"], X["sten_bak"], X["sten_fram"]      # 106, 115, 155
X_MITT = X["sten_mitt"]                                                # 135, stiftets läge
FOG = IN["sten"]["fog"]
SB, SH = IN["sten"]["exempel"]                                         # 790 × 390
MOD_X, MOD_Y = SB + FOG, SH + FOG                                      # 800 × 400
H_MAX = IN["sten"]["H_max"]
NSKIFT = round(H_MAX / MOD_Y)                                          # 5 skift i exemplet
K = IN["konsol"]
W = IN["vinkel"]
U = IN["uha"]
P = IN["plugg"]
INJ = IN["injektion"]
X_FRAM_VINKEL = X_STF - 5                                              # vinkelns framkant, 5 mm innanför stenen
X_ANDPLAT = K["andplat_x"]                                             # 138

# färger utöver mallens
STEN = "#cfc9bf"
BRUK = "#e6dfd2"
PUR = "#f2e6b0"
GJUT = "#d8d2c6"


def pos(n):
    """Positionsnumret som text (samma nummer i positionsförteckningen på U-02.2)."""
    return str(n)


# ================================================================== 2. byggdelar
def vagg(v, y0, y1, inne=True, bruk_fran=None, bruk_till=None, bryt=(True, True), x_in=None):
    """Kub-väggen i snitt mellan y0 och y1: betongkärna, cellplast ute (och inne med gips) samt armeringsbruk."""
    with v.lager("vagg"):
        xk = -KARNA if x_in is None else x_in
        v.rekt(xk, y0, 0, y1, fyll="betong", stil=None)
        v.rekt(0, y0, EPS, y1, fyll="eps", stil=None)
        v.linje([(0, y0), (0, y1)], "tunn"); v.linje([(EPS, y0), (EPS, y1)], "tunn")
        if inne:
            v.rekt(-KARNA - EPS, y0, -KARNA, y1, fyll="eps", stil=None)
            v.rekt(-KARNA - EPS - GIPS, y0, -KARNA - EPS, y1, fyll="vit", stil=None)
            for x in (-KARNA, -KARNA - EPS, -KARNA - EPS - GIPS):
                v.linje([(x, y0), (x, y1)], "tunn")
        b0 = y0 if bruk_fran is None else bruk_fran
        b1 = y1 if bruk_till is None else bruk_till
        v.rekt(EPS, b0, X_BRUK, b1, fyll=BRUK, stil=None)
        v.linje([(X_BRUK, b0), (X_BRUK, b1)], "tunn")
        xa = (-KARNA - EPS - GIPS) if inne else xk
        if bryt[0]:
            v.brott((xa - 15, y0), (X_BRUK + 15, y0), "tunn")
        if bryt[1]:
            v.brott((xa - 15, y1), (X_BRUK + 15, y1), "tunn")


def sten(v, y0, y1, fastmassa=True):
    """En sten i snitt (40 mm) med fästmassan bakom."""
    with v.lager("sten"):
        if fastmassa:
            v.rekt(X_BRUK, y0, X_STB, y1, fyll=BRUK, stil=None)
        v.rekt(X_STB, y0, X_STF, y1, fyll=STEN, stil="tunn")


def vinkel_snitt(v):
    """Stödvinkeln (bockad plåt) i snitt: vågrätt ben under stenen, lodrätt ben nedåt längst fram."""
    t = W["t"]
    with v.lager("stal"):
        v.polygon([(X_STB, 0), (X_FRAM_VINKEL, 0), (X_FRAM_VINKEL, -W["liv"]), (X_FRAM_VINKEL - t, -W["liv"]),
                   (X_FRAM_VINKEL - t, -t), (X_STB, -t)], fyll="stal", stil=None)


def konsol_snitt(v, stanger=True, skruv=True):
    """Konsolen i snitt (sidovy): fotplåt mot betongen, fläns, ändplåt, gängstänger och skruv till vinkeln."""
    t = K["t"]
    fy0, fy1 = K["fot_y"]
    ly0, ly1 = K["flans_y"]
    ay0, ay1 = K["andplat_y"]
    with v.lager("stal"):
        v.rekt(0, fy0, t, fy1, fyll="stal", stil=None)
        v.rekt(t, ly0, X_ANDPLAT, ly1, fyll="#9aa0a8", stil="tunn")
        v.rekt(X_ANDPLAT, ay0, X_ANDPLAT + t, ay1, fyll="stal", stil=None)
    if stanger:
        with v.lager("ankare"):
            d = INJ["d"]
            for y in K["stang_y"]:
                v.rekt(-INJ["hef"] - 5, y - K["hal_d"] / 2, 0, y + K["hal_d"] / 2, fyll=GJUT, stil=None)
                v.rekt(-INJ["hef"], y - d / 2, t + 12, y + d / 2, fyll="#7d838b", stil="tunn")
                v.rekt(t, y - 10, t + 2, y + 10, fyll="stal", stil=None)          # bricka
                v.rekt(t + 2, y - 8.5, t + 10, y + 8.5, fyll="stal", stil=None)   # mutter
    if skruv:
        with v.lager("ankare"):
            ys = K["skruv_y"]
            v.rekt(X_ANDPLAT - 9, ys - 4, X_FRAM_VINKEL + 5, ys + 4, fyll="#7d838b", stil="tunn")
            v.rekt(X_FRAM_VINKEL, ys - 6.5, X_FRAM_VINKEL + 5, ys + 6.5, fyll="stal", stil=None)
            v.rekt(X_ANDPLAT - 7, ys - 6.5, X_ANDPLAT, ys + 6.5, fyll="stal", stil=None)


def uha_snitt(v, y, stift=True, enkel=False):
    """Halfen UHA-7 i liggfogen på höjden y (fogens mitt): stång Ø7 från ingjutningen till stiftet."""
    d = U["d"]
    x0 = -U["t0"]
    x1 = x0 + U["L"]
    with v.lager("ankare"):
        if not enkel:
            v.rekt(x0 - 5, y - U["hal_d"] / 2, 0, y + U["hal_d"] / 2, fyll=GJUT, stil=None)
        v.rekt(x0, y - d / 2, x1, y + d / 2, fyll="#7d838b", stil="tunn" if not enkel else None)
        if stift:
            sd, sl = U["stift"]
            v.rekt(X_MITT - sd / 2, y - sl / 2, X_MITT + sd / 2, y + sl / 2, fyll="stal", stil=None)


def str_plugg(v, y, enkel=False):
    """EJOT STR U 2G i snitt: hylsa genom cellplasten, 25 mm i betongen, tallrik Ø60 i armeringsbruket."""
    with v.lager("ankare"):
        v.rekt(-P["hef"], y - 4, EPS + 2, y + 4, fyll="#b9b3a9" if not enkel else "#9aa0a8", stil=None)
        v.rekt(EPS + 1, y - P["tallrik"] / 2, EPS + 3, y + P["tallrik"] / 2, fyll="#5a5f66", stil=None)


def etiketter(v, lst, x, dy, y_min=None, y_max=None, sz=6.6):
    """Etiketter i en kolumn vid x: (text, målpunkt, bubbla eller None). Varje etikett står i höjd med sin
    målpunkt, med minst dy pappersmm mellan etiketterna, inom y_min … y_max (modellmått)."""
    lst = sorted(lst, key=lambda e: -e[1][1])
    d = dy * v.s
    ys = []
    for _, mal, _ in lst:
        y = mal[1] if not ys else min(mal[1], ys[-1] - d)
        if y_max is not None:
            y = min(y, y_max)
        ys.append(y)
    if y_min is not None and ys and ys[-1] < y_min:
        lyft = y_min - ys[-1]
        ys = [y + lyft for y in ys]
        for i in range(1, len(ys)):
            ys[i] = min(ys[i], ys[i - 1] - d)
    with v.lager("text"):
        for (txt, mal, bub), yy in zip(lst, ys):
            if bub is not None:
                v.hanvisning(mal, (x + 2.1 * v.s, yy), txt, bubbla=bub, a="lm", sz=sz)
            else:
                v.hanvisning(mal, (x, yy), txt, a="lm", sz=sz)


# ================================================================== 3. vyer
def sektion_a():
    """A–A: väggen med 2,0 m sten på en stödvinkel, mellanbjälklaget ovanför. 1:10"""
    v = Vy(x=24, y=12, w=112, h=266, skala=10, X0=-330, Y1=2330)
    ytop = H_MAX                                                        # stenens överkant = bjälklagets underkant
    hb = 150
    with v.lager("mark"):
        v.polygon([(X_STF + 5, -250), (X_STF + 200, -250), (X_STF + 200, -60), (X_STF + 5, -60)],
                  fyll="jord", stil=None)
        v.linje([(X_BRUK, -60), (X_STF + 200, -60)], "normal")
    vagg(v, -250, ytop, bruk_till=ytop, bryt=(True, False))
    with v.lager("vagg"):
        # bjälklaget gjuts med väggens översta del; cellplasten ute fortsätter som kantform
        v.rekt(-330, ytop, 0, ytop + hb, fyll="betong", stil=None)
        v.linje([(-330, ytop), (-KARNA - EPS - GIPS, ytop)], "tunn")
        v.linje([(-330, ytop + hb), (0, ytop + hb)], "tunn")
        v.rekt(0, ytop, EPS, ytop + hb + 60, fyll="eps", stil=None)
        v.linje([(EPS, ytop), (EPS, ytop + hb + 60)], "tunn"); v.linje([(0, ytop), (0, ytop + hb)], "tunn")
        v.brott((-330, ytop - 30), (-330, ytop + hb + 30), "tunn")
        # väggen ovanför (arkitekt): ytterliv i linje med stenens framsida
        v.rekt(X_BRUK, ytop + 20, X_STF, ytop + 300, fyll=None, stil="dold")
        v.linje([(-150, ytop + hb), (-150, ytop + 300)], "dold")
    for k in range(NSKIFT):
        y0 = k * MOD_Y
        sten(v, y0, y0 + SH)
    with v.lager("sten"):
        for k in range(1, NSKIFT):
            v.rekt(X_STB, k * MOD_Y - FOG, X_STF, k * MOD_Y, fyll="#b8b1a5", stil=None)
    for k in range(1, NSKIFT + 1):
        uha_snitt(v, k * MOD_Y - FOG / 2, enkel=True)
    for k in (1, 3):
        str_plugg(v, k * MOD_Y + SH / 2, enkel=True)
    vinkel_snitt(v)
    konsol_snitt(v, stanger=True, skruv=False)
    with v.lager("stal"):
        # beslag över stenens överkant
        v.linje([(EPS + 2, ytop + 60), (EPS + 2, ytop + 4), (X_STF + 22, ytop - 6), (X_STF + 22, ytop - 22)], "normal")
    with v.lager("matt"):
        v.matty([0, H_MAX], X_STF + 40, [X_STF, X_STF], texter=[f"högst {sv(H_MAX)}"])
        v.mattx([0, EPS, X_STF], -180, [-60, -60, -60], texter=["100", "55"])
    etiketter(v, [
        ("beslag, fall utåt, droppkant\n15 mm utanför stenen", (X_STF + 15, ytop - 3), 12),
        ("Halfen UHA-7 i varje liggfog", (X_MITT, 4 * MOD_Y - FOG / 2), 11),
        ("granit 40, fog 10", (X_STF - 10, 3 * MOD_Y + 200), 5),
        ("fästmassa 9 (6–12)", (X_BRUK + 4, 3 * MOD_Y - 120), 4),
        ("armeringsbruk 6 med nät", (EPS + 3, 2 * MOD_Y + 250), 2),
        ("isolerplugg STR U 2G", (EPS - 30, 1 * MOD_Y + SH / 2), 3),
        ("Kub 350-150, kärna 150,\ncellplast 100 + 100", (-60, 1 * MOD_Y - 100), 1),
        ("stödvinkel", (X_FRAM_VINKEL - 2, -30), 7),
        ("konsol c/c 600", (60, -44), 8),
    ], 230, 7.0, y_min=-150, y_max=2250)
    with v.lager("text"):
        v.text(-KARNA / 2, ytop + hb / 2, "mellanbjälklag", a="cm", sz=6.0, col="gra")
        v.text(X_STF + 20, ytop + 160, "vägg ovan\n(arkitekt)", a="lm", sz=6.0, col="gra")
        v.text(X_STF + 60, -215, "färdig mark", a="lm", sz=6.0, col="gra", bg=True)
        v.text(-KARNA - EPS / 2, 900, "inne", a="cm", sz=6.4, col="gra", rot=90)
    with v.lager("rubrik"):
        v.rubrik(-320, -300, "SEKTION A–A", skala=10, sz=9)
    return v


def detalj_b():
    """B: nedre stöd, snitt genom en konsol. 1:2,5"""
    v = Vy(x=140, y=12, w=184, h=132, skala=2.5, X0=-112, Y1=186)
    yb0, yb1 = -112, 186
    fy0, fy1 = K["fot_y"]
    with v.lager("vagg"):
        v.rekt(-112, yb0, 0, yb1, fyll="betong", stil=None)
        v.linje([(0, yb0), (0, yb1)], "tunn")
        v.brott((-112, yb0 - 5), (-112, yb1 + 5), "tunn")
        # cellplast med urtag för fotplåten (fyllt med PUR-skum)
        v.rekt(0, yb0, EPS, fy0 - 10, fyll="eps", stil=None)
        v.rekt(0, fy1 + 10, EPS, yb1, fyll="eps", stil=None)
        v.rekt(K["t"], fy0 - 10, EPS, fy1 + 10, fyll=PUR, stil=None)
        v.linje([(EPS, yb0), (EPS, yb1)], "tunn")
        v.linje([(0, fy0 - 10), (EPS, fy0 - 10)], "fin"); v.linje([(0, fy1 + 10), (EPS, fy1 + 10)], "fin")
        # armeringsbruket, avbrutet där flänsen går igenom
        ly0, ly1 = K["flans_y"]
        v.rekt(EPS, yb0, X_BRUK, ly0 - 3, fyll=BRUK, stil=None)
        v.rekt(EPS, ly1 + 3, X_BRUK, yb1, fyll=BRUK, stil=None)
        v.linje([(X_BRUK, yb0), (X_BRUK, ly0 - 3)], "tunn"); v.linje([(X_BRUK, ly1 + 3), (X_BRUK, yb1)], "tunn")
        for y in (yb0, yb1):
            v.brott((-112, y), (X_BRUK + 10, y), "tunn")
    sten(v, 0, yb1)
    with v.lager("sten"):
        v.brott((X_BRUK - 10, yb1), (X_STF + 10, yb1), "tunn")
    vinkel_snitt(v)
    konsol_snitt(v)
    with v.lager("stal"):
        sd = 5
        v.rekt(X_MITT - 2.5, -W["t"] - 6, X_MITT + 2.5, 25, fyll="stal", stil=None)      # stift M5 i vinkeln
        v.rekt(X_MITT - 4, 0, X_MITT + 4, 30, fyll=None, stil="dold")                    # hål Ø8 i stenen
    with v.lager("matt"):
        v.mattx([0, EPS, X_BRUK, X_STB, X_STF], 170, [yb1, yb1, yb1, yb1, yb1])
        v.mattx([X_STB, X_FRAM_VINKEL, X_STF], -100, [-4, -W["liv"], -4])
        v.matty([fy0, K["stang_y"][0], 0, K["stang_y"][1], fy1], -95, [0, -INJ["hef"], 0, -INJ["hef"], 0])
        v.matty([-W["liv"], 0], X_STF + 30, [X_FRAM_VINKEL, X_STF])
        v.mattx([-INJ["hef"], 0], fy0 - 15, [K["stang_y"][0] - 6, -112], texter=[f"hef {INJ['hef']}"])
    etiketter(v, [
        ("granit 40", (X_STF - 8, 120), 5),
        ("fästmassa 9", (X_STB - 4, 80), 4),
        ("armeringsbruk 6 med nät", (X_BRUK - 3, 40), 2),
        ("stift M5 A4, 2 per sten, i hål Ø8", (X_MITT + 2, 15), None),
        ("stödvinkel 60 × 35 × 4", (X_FRAM_VINKEL - 2, -50), 7),
        ("M8 A4 i avlångt hål (±15)", (X_FRAM_VINKEL + 3, K["skruv_y"]), 10),
        ("konsol, plåt 8 mm", (90, -60), 8),
        ("FIS A M10 R i FIS V", (-40, K["stang_y"][0] - 3), 9),
        ("urtag fyllt med PUR-skum", (50, 60), 14),
    ], 192, 6.0, y_min=-118, y_max=172)
    with v.lager("rubrik"):
        v.rubrik(-105, -133, "DETALJ B  Nedre stöd, snitt genom konsol", skala=2.5, sz=9)
    return v


def detalj_c():
    """C: Halfen UHA-7 i liggfogen. 1:2"""
    v = Vy(x=140, y=152, w=184, h=126, skala=2, X0=-112, Y1=118)
    yb0, yb1 = -100, 118
    vagg(v, yb0, yb1, inne=False, bryt=(True, True), x_in=-112)
    with v.lager("vagg"):
        v.brott((-112, yb0 - 5), (-112, yb1 + 5), "tunn")
        v.rekt(0, -10, EPS, 10, fyll=PUR, stil=None)                    # hålet genom cellplasten
    sten(v, yb0, -FOG / 2)
    sten(v, FOG / 2, yb1)
    with v.lager("sten"):
        v.rekt(X_STB, -FOG / 2, X_STF, FOG / 2, fyll="#b8b1a5", stil=None)
        v.brott((X_BRUK - 8, yb0), (X_STF + 8, yb0), "tunn"); v.brott((X_BRUK - 8, yb1), (X_STF + 8, yb1), "tunn")
        hd, hdj = U["hal_sten"]
        v.rekt(X_MITT - hd / 2, -FOG / 2 - hdj, X_MITT + hd / 2, -FOG / 2, fyll=GJUT, stil="tunn")
        v.rekt(X_MITT - hd / 2, FOG / 2, X_MITT + hd / 2, FOG / 2 + hdj, fyll=GJUT, stil="tunn")
    uha_snitt(v, 0)
    with v.lager("ankare"):
        hy_d, hy_l = U["hylsa"]
        v.rekt(X_MITT - hy_d / 2, FOG / 2 - 2, X_MITT + hy_d / 2, FOG / 2 - 2 + hy_l * 0.8, fyll=None, stil="tunn")
    with v.lager("matt"):
        v.mattx([-U["t0"], 0, X_MITT], -80, [-U["hal_d"] / 2, yb0, -FOG / 2 - U["hal_sten"][1]],
                texter=[f"≥ {U['t0']}", f"k = {sv(X_MITT)}"])
        v.mattx([-U["t0"], -U["t0"] + U["L"]], 40, [U["d"] / 2, U["d"] / 2], texter=[f"L = {U['L']}"])
        v.matty([-FOG / 2, FOG / 2], X_STF + 22, [X_STF, X_STF])
        v.matty([-FOG / 2 - U["hal_sten"][1], -FOG / 2], X_STF + 10, [X_MITT + 4, X_MITT + 4])
    etiketter(v, [
        ("hylsa Ø7,5 × 40 på stiftet\ni den övre stenen", (X_MITT + 3, 25), None),
        ("stift Ø5 × 70, hål Ø8 i stenen\nfyllda med cementbruk", (X_MITT + 2, -20), None),
        ("fog 10, fogbruk", (X_STF - 6, 0), 6),
        ("Halfen UHA-7-1-240, A4", (60, 3), 11),
        ("cementbruk i hål Ø17 (DIN 18516-3)", (-50, -U["hal_d"] / 2 + 2), None),
    ], 178, 8.0, y_min=-95, y_max=100)
    with v.lager("rubrik"):
        v.rubrik(-105, -112, "DETALJ C  Kvarhållning i liggfog", skala=2, sz=9)
    return v


def fasad_e():
    """E: fasad, exempel med sten 790 × 390 i halvstensförband, 2,0 m på en vinkel. x längs väggen. 1:20"""
    v = Vy(x=24, y=12, w=176, h=142, skala=20, X0=-260, Y1=2300)
    B = 2400
    with v.lager("mark"):
        v.polygon([(-150, -100), (B + 150, -100), (B + 150, -260), (-150, -260)], fyll="jord", stil=None)
        v.linje([(-150, -100), (B + 150, -100)], "normal")
    stenar = []
    with v.lager("sten"):
        v.rekt(0, -60, B, H_MAX, fyll=BRUK, stil=None)
        for k in range(NSKIFT):
            off = 0 if k % 2 == 0 else -MOD_X / 2
            y0 = k * MOD_Y
            x = off
            while x < B:
                a, b = max(x, 0), min(x + SB, B)
                if b - a > 50:
                    v.rekt(a, y0, b, y0 + SH, fyll=STEN, stil="tunn")
                    stenar.append((k, a, b))
                x += MOD_X
    # Halfen UHA i liggfogarna: två per sten i den undre stenens överkant, L/5 från ändarna
    uha = []
    for k, a, b in stenar:
        L_ = b - a
        lst = [a + L_ / 2] if L_ < 400 else [a + max(U["kant_sten"], round(L_ / 5 / 10) * 10),
                                            b - max(U["kant_sten"], round(L_ / 5 / 10) * 10)]
        for xx in lst:
            uha.append((xx, (k + 1) * MOD_Y - FOG / 2))
    with v.lager("ankare"):
        for xx, yy in uha:
            v.rekt(xx - 12, yy - 3.5, xx + 12, yy + 3.5, fyll="ok" if False else "#b5463a", stil=None)
    # isolerplugg i skiftens mitthöjd, c/c 600, förskjutna 300 mellan skiften
    plugg = []
    for k in range(NSKIFT):
        yy = k * MOD_Y + SH / 2
        x0 = 300 if k % 2 == 0 else 0
        for xx in range(x0, B + 1, P["cc_x"]):
            if P["s_min"] <= xx <= B - P["s_min"]:
                plugg.append((xx, yy))
    with v.lager("ankare"):
        for xx, yy in plugg:
            v.cirkel(xx, yy, P["tallrik"] / 2, fyll=None, stil="dold", modell=True)
    # stödvinkel och konsoler
    konsoler = [K["kant_max"]]
    while konsoler[-1] + K["cc"] < B - K["kant_max"]:
        konsoler.append(konsoler[-1] + K["cc"])
    konsoler.append(B - K["kant_max"])
    with v.lager("stal"):
        v.rekt(0, -W["liv"], B, 0, fyll="stal", stil=None)
        for xx in konsoler:
            v.rekt(xx - K["andplat_b"] / 2, K["andplat_y"][0], xx + K["andplat_b"] / 2, -W["liv"], fyll="#9aa0a8",
                   stil="tunn")
            v.rekt(xx - K["fot_b"] / 2, K["fot_y"][0], xx + K["fot_b"] / 2, K["fot_y"][1], fyll=None, stil="dold")
        v.linje([(-20, H_MAX + 8), (B + 20, H_MAX + 8)], "grov")
    with v.lager("matt"):
        v.mattx([0] + konsoler + [B], -330, [-W["liv"]] + [K["andplat_y"][0]] * len(konsoler) + [-W["liv"]])
        v.matty([k * MOD_Y for k in range(NSKIFT + 1)], -120, [0] * (NSKIFT + 1),
                texter=[f"{SH} + {FOG}"] * NSKIFT)
        k0 = [s for s in stenar if s[0] == 0]
        a0, b0 = k0[0][1], k0[0][2]
        y_m = H_MAX + 120
        u0 = [xx for xx, yy in uha if abs(yy - (NSKIFT * MOD_Y - FOG / 2)) < 1]
        top = [s for s in stenar if s[0] == NSKIFT - 1][0]
        v.mattx([top[1], u0[0], u0[1], top[2]], y_m, [H_MAX] * 4)
        px = sorted(xx for xx, yy in plugg if abs(yy - SH / 2) < 1)
        v.mattx([px[0], px[1]], SH / 2 + 60, [SH / 2, SH / 2], texter=[f"c/c {P['cc_x']}"])
    with v.lager("text"):
        v.text(B + 60, -30, "stödvinkel (7)\nkonsoler (8)", a="lm", sz=6.4)
        v.text(B + 60, MOD_Y - FOG / 2, "Halfen UHA-7 (11)", a="lm", sz=6.4)
        v.text(B + 60, MOD_Y + SH / 2, "isolerplugg (3)", a="lm", sz=6.4)
        v.text(B + 60, H_MAX + 8, "beslag (12)", a="lm", sz=6.4)
        v.text(-150, -140, "färdig mark", a="lm", sz=6.0, col="gra", bg=True)
    with v.lager("rubrik"):
        v.rubrik(-250, -420, f"FASAD E  Exempel, sten {SB} × {SH} i halvstensförband", skala=20, sz=9)
    return v, dict(uha=len(uha), plugg=len(plugg), konsoler=len(konsoler), stenar=len(stenar), B=B)


def konsol_k():
    """K: konsolen för tillverkning, sidovy 1:2,5 och vy ovanifrån 1:5 (två vyer)."""
    v = Vy(x=206, y=12, w=118, h=104, skala=2.5, X0=-60, Y1=160)
    t = K["t"]
    fy0, fy1 = K["fot_y"]
    ly0, ly1 = K["flans_y"]
    ay0, ay1 = K["andplat_y"]
    with v.lager("stal"):
        v.rekt(0, fy0, t, fy1, fyll="stal", stil=None)
        v.rekt(t, ly0, X_ANDPLAT, ly1, fyll="#9aa0a8", stil="tunn")
        v.rekt(X_ANDPLAT, ay0, X_ANDPLAT + t, ay1, fyll="stal", stil=None)
        for y in K["stang_y"]:
            v.linje([(-6, y), (t + 6, y)], "axel")
        v.linje([(X_ANDPLAT - 6, K["skruv_y"]), (X_ANDPLAT + t + 6, K["skruv_y"])], "axel")
    with v.lager("matt"):
        v.mattx([0, t, X_ANDPLAT, X_ANDPLAT + t], fy1 + 14, [fy1, fy1, ly1, ay1])
        v.matty([fy0, K["stang_y"][0], 0, K["stang_y"][1], fy1], -30, [0, 0, 0, 0, 0])
        v.matty([ly0, ly1], X_ANDPLAT - 34, [X_ANDPLAT - 34, X_ANDPLAT - 34])
        v.matty([ay0, K["skruv_y"], ay1], X_ANDPLAT + t + 16, [X_ANDPLAT + t] * 3)
    with v.lager("text"):
        v.text(70, ly0 - 8, "fläns 8 × 80", a="ct", sz=6.2)
        v.text(X_ANDPLAT + t, ay0 - 10, "ändplåt 8 × 60 × 70,\navlångt hål 9 × 39 lodrätt", a="rt", sz=6.2)
        v.text(t + 6, fy1 - 4, "fotplåt 8 × 100 × 220,\n2 hål Ø12", a="lt", sz=6.2)
        v.text(t + 6, 2, "y = 0: stödvinkelns överkant", a="lb", sz=5.8, col="gra")
        v.linje([(-14, 0), (X_ANDPLAT + t + 6, 0)], "hjalp")
    o = Vy(x=206, y=118, w=118, h=46, skala=5, X0=-60, Y1=70)
    with o.lager("stal"):
        o.rekt(0, -K["fot_b"] / 2, t, K["fot_b"] / 2, fyll="stal", stil=None)
        o.rekt(t, -t / 2, X_ANDPLAT, t / 2, fyll="#9aa0a8", stil="tunn")
        o.rekt(X_ANDPLAT, -K["andplat_b"] / 2, X_ANDPLAT + t, K["andplat_b"] / 2, fyll="stal", stil=None)
        o.linje([(-10, 0), (X_ANDPLAT + t + 10, 0)], "axel")
    with o.lager("matt"):
        o.matty([-K["fot_b"] / 2, K["fot_b"] / 2], -25, [0, 0])
        o.matty([-K["andplat_b"] / 2, K["andplat_b"] / 2], X_ANDPLAT + t + 22, [X_ANDPLAT + t] * 2)
    with o.lager("text"):
        o.text(70, 40, "vy ovanifrån, 1:5", a="cb", sz=6.2, col="gra")
        o.text(70, -40, f"svets a = {K['a_svets']} runt om, EN 1.4404", a="ct", sz=6.2)
    with o.lager("rubrik"):
        o.rubrik(-55, -92, "KONSOL K  Tillverkning (pos 8)", skala=None, sz=9)
        o.text(-55, -92 - 4.2 * 5, "Skala 1:2,5 och 1:5", a="lb", sz=7.2, col="gra")
    return [v, o]


# ================================================================== 4. blad
BLADEN = [
    ("U-02.1", ["Fasadsten på källarväggarna", "Sektion och detaljer"], "1:10, 1:2,5, 1:2",
     "U-02.1 Fasadsten, sektion och detaljer"),
    ("U-02.2", ["Fasadsten på källarväggarna", "Fasad, konsol, positioner och dimensionering"], "1:20, 1:2,5, 1:5",
     "U-02.2 Fasadsten, fasad och positioner"),
]


def hd(nr):
    b = [x for x in BLADEN if x[0] == nr][0]
    return huvud(nr, b[1], b[2], UNDERLAG, DATUM, REV)


def positioner():
    """Positionsförteckning: samma nummer som bubblorna på U-02.1."""
    p, u, k, inj = R["plugg"], IN["uha"], IN["konsol"], IN["injektion"]
    rader = [
        ["1", "Vägg", "Sundolitt Kub 350-150 (U17), SINTEF TG 2216", "kärna 150 betong, cellplast 100 + 100", "–"],
        ["2", "Armeringsbruk med nät", "Mapei Mapetherm AR1 + Mapetherm Net, eller likvärdigt putssystem för "
         "cellplast med teknisk godkännande", "6 (5–7), nät i yttre tredjedelen, skarv 100", "hela stenytan, "
         "ned 200 under mark"],
        ["3", "Isolerplugg", f"{P['produkt']}, {P['eta']}", f"L = {P['L']}, tallrik Ø{P['tallrik']}, ≥ {P['hef']} i "
         "betongen (borrdjup ≥ 35)", f"c/c {P['cc_x']} i skiftens mitthöjd, förskjutna {P['cc_x'] // 2} "
         f"({sv(p['n'], 1)} st/m²)"],
        ["4", "Fästmassa", "Mapei Keraflex Maxi S1 (C2TE S1) eller likvärdig C2 S1 för natursten",
         "9 (6–12), kombinerad metod", "100 % täckning"],
        ["5", "Fasadsten", "granit, sågad baksida, frostbeständig (SS-EN 12371), vattenupptagning ≤ 0,5 %",
         "40; ≤ 1 200 × 600, ≤ 0,72 m²", f"exempel {SB} × {SH}"],
        ["6", "Fogbruk", "Mapei Ultracolor Plus (CG2WA)", "fog 10, fullt djup", "–"],
        ["7", "Stödvinkel", "bockad plåt 4, EN 1.4404; stift M5 A4 upp i stenen", "60 × 35, L ≤ 3 000, glipa 5",
         "under nedersta skiftet, 2 stift per sten"],
        ["8", "Konsol", "svetsad plåt 8, EN 1.4404, a = 4 runt om (konsol K, U-02.2)",
         "fotplåt 100 × 220, fläns 130 × 80, ändplåt 60 × 70", f"c/c ≤ {k['cc']}, ≤ {k['kant_max']} från "
         "vinkelns ände"],
        ["9", "Gängstång i injektionsmassa", "fischer FIS V (ETA-02/0024) + FIS A M10 R (A4-70), bricka och mutter A4",
         f"hål Ø{k['hal_d']}, hef {inj['hef']}", "2 per konsol"],
        ["10", "Skruv vinkel–konsol", "M8 × 30 A4-70, bricka, låsmutter", "–", "1 per konsol"],
        ["11", "Kvarhållningsankare", f"Halfen {u['typ']}, A4, typprovat; översta skiftet UHA-7-2-240 (fast "
         "halvstift)", f"hål Ø{u['hal_d']}, ingjutning ≥ {u['t0']} cementbruk; stifthål Ø8 × 35 i stenen",
         f"2 per sten och liggfog, c/c ≤ {u['cc']}, ≈ L/5 och ≥ {u['kant_sten']} från stenens hörn"],
        ["12", "Beslag", "plåt enligt arkitekt", "fall utåt, droppkant 15 utanför stenen", "stenens överkant"],
        ["13", "Rörelsefog", "bottningslist + Mapei Mapesil LM (neutral silikon för natursten)", "10",
         "inåtgående hörn, mot andra material, ≤ 6 m"],
        ["14", "Urtag vid konsolen", "lågexpanderande PUR-skum, slipas plant", "–", "–"],
    ]
    return dict(typ="tabell", kolumner=["Pos", "Del", "Produkt, material", "Mått (mm)", "Antal, avstånd"],
                bredd=(0, 0.9, 2.4, 1.7, 1.6), rader=rader, just=["l", "l", "l", "l", "l"], sz=6.4)


def dimensionering():
    L_, v, k, u, p = R["laster"], R["vinkel"], R["konsol"], R["uha"], R["plugg"]
    d = lambda x, n=2: sv(x, n)  # noqa: E731
    rader = [
        ["Stödvinkel, böjning", f"M = {d(v['M'])} kNm", f"σ = {d(v['sig'], 0)} / {d(v['f_d'], 0)} MPa",
         d(v['utn_M'])],
        ["Stödvinkel, nedböjning", f"{d(v['u'])} mm", f"L/500 = {d(v['u_grans'], 1)} mm", "–"],
        ["Stödvinkel, vridning", f"τ = {d(v['tau_T'], 0)} MPa", f"{d(v['f_d'] / math.sqrt(3), 0)} MPa",
         d(v['utn_T'])],
        ["Konsol, fläns och svets", f"V = {d(k['V'])} kN, M = {d(k['M'])} kNm", f"e = {d(k['e'], 0)} mm",
         d(max(k['utn_flans'], k['utn_svets']))],
        ["Gängstång M10, drag + tvär", f"N = {d(k['N'])}, V = {d(k['Vst'])} kN", f"NRd = {d(k['NRd'], 1)} kN",
         d(k['utn_N'])],
        ["Halfen UHA-7, vindsug", f"H = {d(u['H_max'])} kN", f"HH,Rd = {d(IN['uha']['HH_Rd'] / 1000)} kN",
         d(u['utn'])],
        ["Isolerplugg, vindsug", f"wd = {d(L_['wd'])} kN/m²", f"{d(p['n'], 1)} × {d(p['NRd'])} kN/m²",
         d(p['utn'])],
    ]
    return [
        dict(typ="text", sz=6.2, rader=[
            f"Sten {d(L_['g_sten'])} + fästmassa {d(L_['g_fast'])} = {d(L_['g'])} kN/m². Vinkeln bär "
            f"{sv(H_MAX / 1000, 1)} m sten: qd = 0,91 · 1,35 · {d(L_['qk'])} = {d(L_['qd'])} kN/m. Vindsug "
            f"wd = 0,91 · 1,5 · {sv(IN['vind']['cpe'], 1)} · {sv(IN['vind']['qp'], 2)} = {d(L_['wd'])} kN/m² (qp F-01).",
            "Stålet bär stenen ensamt om fästmassans fäste mot cellplasten går förlorat. Gängstänger: τRk,cr "
            f"{sv(INJ['tau_Rk_cr'], 1)} · ψc {sv(INJ['psi_c'], 2)} · ψ0sus {sv(INJ['psi0_sus'], 2)} (varaktig last), "
            f"γM {sv(INJ['gM'], 1)}. Halfen: FS 12/2024, k 130–150, sprucken betong. Plugg: NRk 1,5 kN, γM 2,0, "
            "minst 4 st/m² för natursten (DIBt Z-33.46-568). Beräkning: U-02/berakning.py."]),
        dict(typ="tabell", kolumner=["Kontroll", "Last", "Bärförmåga", "Utn."], bredd=(1.4, 1.5, 1.4, 0.4),
             rader=rader, just=["l", "l", "l", "r"], sz=6.4)]


def blad_detaljer():
    vyer = [sektion_a(), detalj_b(), detalj_c()]
    kol = [
        dict(typ="rubrik", text="Anvisningar"),
        dict(typ="lista", sz=6.9, rader=[
            "Gäller källarväggarnas ytterväggar av Sundolitt Kub 350-150 där fasadsten sätts ovan mark. Stenen "
            "bärs av fästmassan; stödvinkeln och Halfen-ankarna bär den ensamma om fästet mot cellplasten går "
            "förlorat (brand, åldring). Positioner, mått och kontroller: U-02.2.",
            "Cellplasten raspas plan före armeringsbruket. Det härdade armeringsbruket får avvika högst 2 mm "
            "över stenens längsta kant.",
            "Konsolerna (8) först: cellplasten skärs ur för fotplåten, hålen borras i betongkärnan och blåses "
            "rena, gängstängerna (9) injekteras. Konsolen dras fast när massan härdat. Urtaget fylls med "
            "PUR-skum (14) och slipas plant.",
            "Armeringsbruket (2) läggs i två omgångar med nätet i den yttre tredjedelen, skarvar 100 mm och "
            "diagonalnät vid öppningarnas hörn. Isolerpluggarna (3) sätts genom nätet i det första lagret; "
            "tallrikarna täcks direkt av det andra.",
            "Stödvinkeln (7) skruvas på konsolerna, rak och i våg. Stift M5 upp i stenarnas underkant, 2 per sten.",
            "Stenen (5) sätts med fästmassa (4) på både vägg och sten, 100 % täckning; lyft en sten då och då och "
            "kontrollera. Armeringsbruket härdar enligt produktbladet först, normalt cirka en vecka. Lägst +5 °C "
            "vid läggning och härdning.",
            "Halfen UHA-7 (11) sätts skift för skift: bruket och cellplasten borras igenom, Ø17 i betongen, hålet "
            "fuktas och fylls med cementbruk, ankaret trycks in, stiftet förs ned i den undre stenens hål och "
            "nästa sten sätts på stiftet. Stifthålen fylls med cementbruk; hylsan sitter i den övre stenen.",
            "Fogarna (6) fylls helt och komprimeras. Rörelsefogar (13) vid inåtgående hörn, mot andra material "
            "och högst var 6:e meter.",
            "Ingen cellplast får synas: beslag (12) över överkanten, sten eller plåt i öppningarnas smygar, "
            "armeringsbruket nedtill till 200 mm under mark.",
            "Avstånd till betongkärnans kanter (öppningar, väggens ände) och mellan infästningar minst 100 mm.",
        ]),
        dict(typ="rubrik", text="Teckenförklaring"),
        dict(typ="symboler", rader=[
            dict(form="yta", fyll="betong", stil="tunn", text="betong (Kub-kärna, bjälklag)"),
            dict(form="yta", fyll="eps", stil="tunn", text="cellplast (Kub)"),
            dict(form="yta", fyll=BRUK, stil="tunn", text="armeringsbruk, fästmassa"),
            dict(form="yta", fyll=STEN, stil="tunn", text="granit"),
            dict(form="yta", fyll="stal", stil=None, text="rostfritt stål EN 1.4404 (A4)"),
            dict(form="yta", fyll=GJUT, stil="tunn", text="injektionsmassa, cementbruk"),
            dict(form="yta", fyll=PUR, stil="tunn", text="PUR-skum"),
            dict(form="bubbla", txt="1", text="position, se U-02.2")]),
    ]
    return Blad(hd("U-02.1"), REVISIONER, kol, vyer)


def blad_fasad():
    ve, info = fasad_e()
    vyer = [ve] + konsol_k()
    block = [dict(x=24, y=168, w=300, innehall=[dict(typ="rubrik", text="Positionsförteckning"), positioner()]),
             dict(x=24, y=218, w=300, innehall=[dict(typ="rubrik", text="Dimensionering")] + dimensionering())]
    kol = [
        dict(typ="rubrik", text="Förutsättningar"),
        dict(typ="lista", sz=6.9, rader=[
            f"Källarväggar av Sundolitt Kub 350-150 (U17): betongkärna {KARNA} mm, cellplast {EPS} mm på var sida "
            "(SINTEF TG 2216). Betong enligt Sundolitt, räknas som C30/37.",
            f"Granit 40 mm, 108 kg/m². Sten högst 1 200 × 600 mm och 0,72 m² (största sten "
            f"{sv(R['sten']['kg_max'], 0)} kg). Stenhöjd på en stödvinkel högst {sv(H_MAX)} mm "
            "(modellen: 0,8–2,0 m).",
            "Stenens framsida 55 mm utanför cellplasten, 155 mm utanför betongkärnan; väggen blir cirka 405 mm.",
            "Allt stål rostfritt EN 1.4404 eller 1.4571 (A4), även skruv, mutter och bricka.",
            "Halfen-ankarna kräver 10 mm liggfog och minst 30 mm sten med 10 mm sten utanför stifthålet "
            "(DIN 18516-3). Stenleverantören redovisar brottlasten vid stifthål enligt SS-EN 13364; "
            f"dimensionerande last per stifthål {sv(R['uha']['H_stift'], 2)} kN.",
            "Fästmassa, armeringsbruk och fogbruk från samma leverantör; leverantören bekräftar systemet för "
            "40 mm granit på cellplast.",
            f"Fasad E visar ett exempel: {info['stenar']} stenar, {info['uha']} Halfen-ankare, {info['plugg']} "
            f"isolerplugg och {info['konsoler']} konsoler på {sv(info['B'] / 1000, 1)} m vägg.",
        ]),
        dict(typ="rubrik", text="Teckenförklaring"),
        dict(typ="symboler", rader=[
            dict(form="ruta", fyll="#b5463a", text="Halfen UHA-7 i liggfog (11)"),
            dict(form="linje", stil="dold", text="isolerplugg bakom stenen (3), fotplåt (8)"),
            dict(form="yta", fyll="stal", stil=None, text="stödvinkel (7), ändplåt (8)"),
            dict(form="yta", fyll=STEN, stil="tunn", text="granit"),
            dict(form="linje", stil="axel", text="centrumlinje"),
        ]),
    ]
    return Blad(hd("U-02.2"), REVISIONER, kol, vyer, block)


# ================================================================== 5. main
SERIE = "U-02 Fasadsten på källarväggarna"


def main(dolj=()):
    os.makedirs(UT, exist_ok=True)
    bladmapp = os.path.join(HERE, "blad")
    os.makedirs(bladmapp, exist_ok=True)
    fn = {"U-02.1": blad_detaljer, "U-02.2": blad_fasad}
    pdfer = []
    for nr, _, _, filnamn in BLADEN:
        b = fn[nr]()
        jp = os.path.join(HERE, f"{nr}.json")
        b.spara(jp)
        pdfer.append(os.path.join(bladmapp, filnamn + ".pdf"))
        b.kompilera(jp, pdfer[-1], ROT, dolj=dolj)
        print("blad/" + filnamn + ".pdf")
    Blad.serie(pdfer, os.path.join(UT, SERIE + ".pdf"))
    print(f"ritningar/{SERIE}.pdf ({len(pdfer)} sidor)")


if __name__ == "__main__":
    main()
