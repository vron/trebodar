"""
U-02 Fasadsten på källarväggarna, infästning (F-01 avsnitt 6), A3 med ../ritningsmall:

    U-02.1  Sektion och detaljer                         1:10, 1:2,5, 1:2
    U-02.2  Fasad, positioner och dimensionering         1:20

Underlag: indata.toml och resultat.json (berakning.py). Allt ritas i verkliga koordinater i mm: x = 0 i
betongkärnans yttre yta (utåt positivt), y = 0 i stödvinkelns överkant (stenens underkant). I fasaden (U-02.2) är
x längs väggen. ritningsmall/ritning.py skalar till papperet.

Filen är uppdelad i:
    1. Underlag           mått ur indata och resultat
    2. Byggdelar          vägg, sten, vinkel, stång, plugg (ritas i flera vyer)
    3. Vyer               en funktion per vy
    4. Blad               högerkolumn, tabeller och ritningshuvud
    5. main               skriver U-02.x.json och PDF:en i ritningar/

    python beräkningar/U-02/berakning.py
    python beräkningar/U-02/ritningar.py
"""
import json
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

REV, DATUM = IN["projekt"]["revision"], IN["projekt"]["datum"]
UNDERLAG = "Kub TG 2216, K-06"
REVISIONER = [dict(rev=REV, avser="Första utgåvan", datum=DATUM, sign=PROJEKT["signatur"])]

KARNA, EPS, GIPS = IN["vagg"]["karna"], IN["vagg"]["eps"], IN["vagg"]["gips"]
X = R["lagen"]
X_BRUK, X_STB, X_STF = X["bruk"], X["sten_bak"], X["sten_fram"]      # 106, 115, 155
X_VF = X["vinkel_fram"]                                                # 150, vinkelns framkant
FOG = IN["sten"]["fog"]
SB, SH = IN["sten"]["exempel"]                                         # 790 × 390
MOD_X, MOD_Y = SB + FOG, SH + FOG                                      # 800 × 400
H_MAX = IN["sten"]["H_max"]
NSKIFT = round(H_MAX / MOD_Y)                                          # 5 skift i exemplet
W = IN["vinkel"]
S = IN["stang"]
P = IN["plugg"]
P_DJUP = P["L"] - (EPS + 3)                                            # pluggens längd i betongen (tallriken på första lagret)
NYCKEL, MUTTER_H, BRICKA = 24, 13, 3                                   # M16

# färger utöver mallens
STEN = "#cfc9bf"
BRUK = "#e6dfd2"
GJUT = "#d8d2c6"
STAL_L = "#9aa0a8"
STANG = "#7d838b"


# ================================================================== 2. byggdelar
def vagg(v, y0, y1, inne=True, bruk_till=None, bryt=(True, True), x_in=None):
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
        b1 = y1 if bruk_till is None else bruk_till
        v.rekt(EPS, y0, X_BRUK, b1, fyll=BRUK, stil=None)
        v.linje([(X_BRUK, y0), (X_BRUK, b1)], "tunn")
        xa = (-KARNA - EPS - GIPS) if inne else xk
        if bryt[0]:
            v.brott((xa - 15, y0), (X_BRUK + 15, y0), "tunn")
        if bryt[1]:
            v.brott((xa - 15, y1), (X_BRUK + 15, y1), "tunn")


def sten(v, y0, y1):
    """En sten i snitt (40 mm) med fästmassan bakom."""
    with v.lager("sten"):
        v.rekt(X_BRUK, y0, X_STB, y1, fyll=BRUK, stil=None)
        v.rekt(X_STB, y0, X_STF, y1, fyll=STEN, stil="tunn")


def vinkel_snitt(v):
    """Stödvinkeln i snitt: lodrätt liv nedåt mot armeringsbruket, vågrätt ben under stenen."""
    t = W["t"]
    with v.lager("stal"):
        v.polygon([(X_BRUK, 0), (X_VF, 0), (X_VF, -t), (X_BRUK + t, -t), (X_BRUK + t, -W["liv"]),
                   (X_BRUK, -W["liv"])], fyll="stal", stil=None)


def stang_snitt(v, enkel=False):
    """Gängstång M16 genom cellplasten i injektionsmassa, mutter och bricka på båda sidor om vinkelns liv."""
    y, d, t = S["y"], S["d"], W["t"]
    x_in = X_BRUK - BRICKA - MUTTER_H                                   # inre mutterns baksida
    x_ut = X_BRUK + t
    with v.lager("ankare"):
        if not enkel:
            v.rekt(-S["hef"] - 5, y - S["hal_d"] / 2, 0, y + S["hal_d"] / 2, fyll=GJUT, stil=None)
            v.rekt(x_in - 4, y - 22, X_BRUK, y + 22, fyll="vit", stil=None)      # urtag för inre mutter
        v.rekt(-S["hef"], y - d / 2, x_ut + BRICKA + MUTTER_H + 5, y + d / 2, fyll=STANG,
               stil="tunn" if not enkel else None)
        for x0, x1, h in ((x_in, x_in + MUTTER_H, NYCKEL), (x_in + MUTTER_H, X_BRUK, 32),
                          (x_ut, x_ut + BRICKA, 32), (x_ut + BRICKA, x_ut + BRICKA + MUTTER_H, NYCKEL)):
            v.rekt(x0, y - h / 2, x1, y + h / 2, fyll="stal", stil=None)


def str_plugg(v, y, enkel=False):
    """EJOT STR U 2G i snitt: hylsa genom cellplasten in i betongen, tallrik Ø60 på första lagret bruk."""
    with v.lager("ankare"):
        v.rekt(-P_DJUP, y - 4, EPS + 3, y + 4, fyll="#b9b3a9" if not enkel else STAL_L, stil=None)
        v.rekt(EPS + 1, y - P["tallrik"] / 2, EPS + 3.5, y + P["tallrik"] / 2, fyll="#5a5f66", stil=None)


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
        v.linje([(X_BRUK + W["t"], -60), (X_STF + 200, -60)], "normal")
    vagg(v, -250, ytop, bryt=(True, False))
    with v.lager("vagg"):
        # bjälklaget gjuts med väggens översta del; cellplasten ute fortsätter som kantform
        v.rekt(-330, ytop, 0, ytop + hb, fyll="betong", stil=None)
        v.linje([(-330, ytop), (-KARNA - EPS - GIPS, ytop)], "tunn")
        v.linje([(-330, ytop + hb), (0, ytop + hb)], "tunn")
        v.rekt(0, ytop, EPS, ytop + hb + 60, fyll="eps", stil=None)
        v.linje([(EPS, ytop), (EPS, ytop + hb + 60)], "tunn"); v.linje([(0, ytop), (0, ytop + hb)], "tunn")
        v.brott((-330, ytop - 30), (-330, ytop + hb + 30), "tunn")
        v.rekt(X_BRUK, ytop + 20, X_STF, ytop + 300, fyll=None, stil="dold")
        v.linje([(-150, ytop + hb), (-150, ytop + 300)], "dold")
    for k in range(NSKIFT):
        sten(v, k * MOD_Y, k * MOD_Y + SH)
    with v.lager("sten"):
        for k in range(1, NSKIFT):
            v.rekt(X_STB, k * MOD_Y - FOG, X_STF, k * MOD_Y, fyll="#b8b1a5", stil=None)
    for k in range(NSKIFT):
        str_plugg(v, k * MOD_Y + SH / 2, enkel=True)
    vinkel_snitt(v)
    stang_snitt(v, enkel=True)
    with v.lager("stal"):
        v.linje([(EPS + 2, ytop + 60), (EPS + 2, ytop + 4), (X_STF + 22, ytop - 6), (X_STF + 22, ytop - 22)],
                "normal")
    with v.lager("matt"):
        v.matty([0, H_MAX], X_STF + 40, [X_STF, X_STF], texter=[f"högst {sv(H_MAX)}"])
        v.mattx([0, EPS, X_STF], -180, [-60, -60, -60], texter=["100", "55"])
    etiketter(v, [
        ("beslag, fall utåt, droppkant\n15 mm utanför stenen", (X_STF + 15, ytop - 3), 9),
        ("granit 40, fog 10", (X_STF - 10, 3 * MOD_Y + 250), 5),
        ("fästmassa 9 (6–12)", (X_BRUK + 4, 3 * MOD_Y - 100), 4),
        ("armeringsbruk 6 med nät", (EPS + 3, 2 * MOD_Y + 300), 2),
        ("isolerplugg, 4,2 st/m²", (EPS - 30, 1 * MOD_Y + SH / 2), 3),
        ("Kub 350-150, kärna 150,\ncellplast 100 + 100", (-60, 1 * MOD_Y - 120), 1),
        ("stödvinkel", (X_VF - 2, -2.5), 7),
        ("gängstång M16 c/c 300", (40, S["y"]), 8),
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
    """B: stödvinkeln på gängstång genom cellplasten. 1:2,5"""
    v = Vy(x=140, y=12, w=184, h=132, skala=2.5, X0=-122, Y1=176)
    yb0, yb1 = -122, 176
    vagg(v, yb0, yb1, inne=False, bryt=(True, True), x_in=-122)
    with v.lager("vagg"):
        v.brott((-122, yb0 - 5), (-122, yb1 + 5), "tunn")
    sten(v, 0, yb1)
    with v.lager("sten"):
        v.brott((X_BRUK - 10, yb1), (X_STF + 10, yb1), "tunn")
    vinkel_snitt(v)
    stang_snitt(v)
    with v.lager("matt"):
        v.mattx([0, EPS, X_BRUK, X_STB, X_STF], 160, [yb1] * 5)
        v.mattx([X_BRUK, X_STB, X_VF, X_STF], -98, [-W["liv"], -W["t"], -W["t"], -W["t"]])
        v.mattx([-S["hef"], 0], -60, [S["y"] - S["hal_d"] / 2] * 2, texter=[f"hef {S['hef']}"])
        v.matty([-W["liv"], 0], X_STF + 22, [X_BRUK + W["t"], X_STF])
        v.matty([S["y"], 0], X_STF + 10, [X_BRUK + W["t"] + BRICKA + MUTTER_H, X_VF])
    etiketter(v, [
        ("granit 40", (X_STF - 8, 110), 5),
        ("fästmassa 9", (X_STB - 4, 70), 4),
        ("armeringsbruk 6 med nät", (X_BRUK - 3, 30), 2),
        ("stödvinkel 60 × 44 × 5, EN 1.4404", (X_VF - 3, -2.5), 7),
        ("mutter och bricka på båda sidor om\nlivet; den inre i urtag i cellplasten",
         (X_BRUK + W["t"] + BRICKA + 6, S["y"] + 8), None),
        ("gängstång M16 A4-70 i FIS V", (-40, S["y"]), 8),
    ], 182, 7.0, y_min=-112, y_max=150)
    with v.lager("rubrik"):
        v.rubrik(-115, -138, "DETALJ B  Stödvinkel på gängstång genom cellplasten", skala=2.5, sz=9)
    return v


def detalj_c():
    """C: armeringsbruk med nät och isolerplugg genom nätet. 1:2"""
    v = Vy(x=140, y=158, w=184, h=118, skala=2, X0=-90, Y1=108)
    yb0, yb1 = -80, 108
    with v.lager("vagg"):
        v.rekt(-90, yb0, 0, yb1, fyll="betong", stil=None)
        v.rekt(0, yb0, EPS, yb1, fyll="eps", stil=None)
        v.rekt(EPS, yb0, X_BRUK, yb1, fyll=BRUK, stil=None)
        for x in (0, EPS, X_BRUK):
            v.linje([(x, yb0), (x, yb1)], "tunn")
        v.linje([(EPS + 4.2, yb0), (EPS + 4.2, -P["tallrik"] / 2 - 3), (EPS + 3.6, -P["tallrik"] / 2),
                 (EPS + 3.6, P["tallrik"] / 2), (EPS + 4.2, P["tallrik"] / 2 + 3), (EPS + 4.2, yb1)], "dold")
        v.brott((-90, yb0 - 5), (-90, yb1 + 5), "tunn")
        for y in (yb0, yb1):
            v.brott((-90, y), (X_STF + 10, y), "tunn")
    sten(v, yb0, yb1)
    str_plugg(v, 0)
    with v.lager("matt"):
        v.mattx([-P_DJUP, 0, EPS, X_BRUK], -66, [-4, yb0, yb0, yb0],
                texter=[f"{round(P_DJUP)}", "100", "6"])
        v.mattx([-P_DJUP, EPS + 3.5], 55, [4, P["tallrik"] / 2], texter=[f"L = {P['L']}"])
    etiketter(v, [
        ("granit 40", (X_STF - 8, 70), 5),
        ("fästmassa 9", (X_STB - 4, 45), 4),
        ("andra lagret armeringsbruk", (X_BRUK - 1, 22), None),
        ("tallrik på första lagret, genom nätet", (EPS + 2, -10), None),
        ("nät i yttre tredjedelen", (EPS + 4.2, -45), None),
        ("EJOT STR U 2G, L = 155, tallrik Ø60", (40, 0), 3),
    ], 170, 7.0, y_min=-60, y_max=95)
    with v.lager("rubrik"):
        v.rubrik(-85, -100, "DETALJ C  Armeringsbruk och isolerplugg genom nätet", skala=2, sz=9)
    return v


def fasad_e():
    """E: fasad, exempel med sten 790 × 390 i halvstensförband, 2,0 m på en vinkel. x längs väggen. 1:20"""
    B = 4000
    v = Vy(x=24, y=12, w=300, h=150, skala=20, X0=-300, Y1=2300)
    with v.lager("mark"):
        v.polygon([(-150, -100), (B + 150, -100), (B + 150, -260), (-150, -260)], fyll="jord", stil=None)
        v.linje([(-150, -100), (B + 150, -100)], "normal")
    stenar = []
    with v.lager("sten"):
        v.rekt(0, 0, B, H_MAX, fyll=BRUK, stil=None)
        for k in range(NSKIFT):
            off = 0 if k % 2 == 0 else -MOD_X / 2
            x = off
            while x < B:
                a, b = max(x, 0), min(x + SB, B)
                if b - a > 50:
                    v.rekt(a, k * MOD_Y, b, k * MOD_Y + SH, fyll=STEN, stil="tunn")
                    stenar.append((k, a, b))
                x += MOD_X
    plugg = []
    for k in range(NSKIFT):
        yy = k * MOD_Y + SH / 2
        x0 = P["cc_x"] // 2 if k % 2 == 0 else 0
        for xx in range(x0, B + 1, P["cc_x"]):
            if P["s_min"] <= xx <= B - P["s_min"]:
                plugg.append((xx, yy))
    with v.lager("ankare"):
        for xx, yy in plugg:
            v.cirkel(xx, yy, P["tallrik"] / 2, fyll=None, stil="dold", modell=True)
    n = -(-(B - 2 * S["kant_max"]) // S["cc"])                          # antal fack, c/c ≤ 300, jämnt fördelade
    cc = (B - 2 * S["kant_max"]) / n
    stanger = [S["kant_max"] + i * cc for i in range(n + 1)]
    with v.lager("stal"):
        v.rekt(0, -W["liv"], B, 0, fyll="stal", stil=None)
        for xx in stanger:
            v.rekt(xx - NYCKEL / 2, S["y"] - NYCKEL / 2, xx + NYCKEL / 2, S["y"] + NYCKEL / 2, fyll=STAL_L,
                   stil="tunn")
        v.linje([(-20, H_MAX + 8), (B + 20, H_MAX + 8)], "grov")
    with v.lager("matt"):
        v.mattx([0] + stanger[:3] + [stanger[-1], B], -330,
                [-W["liv"]] + [S["y"] - NYCKEL / 2] * 3 + [S["y"] - NYCKEL / 2, -W["liv"]],
                texter=[sv(S["kant_max"]), sv(cc), sv(cc), f"… {n} × {sv(cc)} …", sv(S["kant_max"])])
        v.matty([k * MOD_Y for k in range(NSKIFT + 1)], -120, [0] * (NSKIFT + 1), texter=[f"{SH} + {FOG}"] * NSKIFT)
        px = sorted(xx for xx, yy in plugg if abs(yy - SH / 2) < 1)
        v.mattx([px[0], px[1]], SH / 2 + 60, [SH / 2, SH / 2], texter=[f"c/c {P['cc_x']}"])
        top = [s for s in stenar if s[0] == NSKIFT - 1][0]
        v.mattx([top[1], top[2], top[2] + FOG], H_MAX + 120, [H_MAX] * 3)
    with v.lager("text"):
        v.text(B + 80, -30, "stödvinkel (7) på\ngängstänger M16 (8)", a="lm", sz=6.4)
        v.text(B + 80, MOD_Y + SH / 2, "isolerplugg (3) bakom\nstenen, i skiftens mitt", a="lm", sz=6.4)
        v.text(B + 80, H_MAX + 8, "beslag (9)", a="lm", sz=6.4)
        v.text(B + 80, 3 * MOD_Y + SH / 2, "sten (5) limmad\nmot armeringsbruket", a="lm", sz=6.4)
        v.text(-150, -140, "färdig mark", a="lm", sz=6.0, col="gra", bg=True)
    with v.lager("rubrik"):
        v.rubrik(-290, -440, f"FASAD E  Exempel, sten {SB} × {SH} i halvstensförband", skala=20, sz=9)
    return v, dict(plugg=len(plugg), stanger=len(stanger), stenar=len(stenar), B=B)


# ================================================================== 4. blad
BLADEN = [
    ("U-02.1", ["Fasadsten på källarväggarna", "Sektion och detaljer"], "1:10, 1:2,5, 1:2",
     "U-02.1 Fasadsten, sektion och detaljer"),
    ("U-02.2", ["Fasadsten på källarväggarna", "Fasad, positioner och dimensionering"], "1:20",
     "U-02.2 Fasadsten, fasad och positioner"),
]


def hd(nr):
    b = [x for x in BLADEN if x[0] == nr][0]
    return huvud(nr, b[1], b[2], UNDERLAG, DATUM, REV)


def positioner():
    """Positionsförteckning: samma nummer som bubblorna på U-02.1."""
    p = R["plugg"]
    rader = [
        ["1", "Vägg", "Sundolitt Kub 350-150 (U17), SINTEF TG 2216", "kärna 150 betong, cellplast 100 + 100", "–"],
        ["2", "Armeringsbruk med nät", "Mapei Mapetherm AR1 + Mapetherm Net, eller likvärdigt putssystem för "
         "cellplast med teknisk godkännande", "6 (5–7) i två lager, nät i yttre tredjedelen, skarv 100",
         "hela stenytan, ned 200 under mark"],
        ["3", "Isolerplugg", f"{P['produkt']}, {P['eta']}", f"L = {P['L']}, tallrik Ø{P['tallrik']}, borrdjup ≥ "
         f"{round(P_DJUP) + 10} i betongen", f"c/c {P['cc_x']} i skiftens mitthöjd, förskjutna {P['cc_x'] // 2} "
         f"({sv(p['n'], 1)} st/m²)"],
        ["4", "Fästmassa", "Mapei Keraflex Maxi S1 (C2TE S1) eller likvärdig C2 S1 för natursten",
         "9 (6–12), kombinerad metod", "100 % täckning"],
        ["5", "Fasadsten", "granit, sågad baksida, frostbeständig (SS-EN 12371), vattenupptagning ≤ 0,5 %",
         "40; ≤ 1 200 × 600, ≤ 0,72 m²", f"exempel {SB} × {SH}"],
        ["6", "Fogbruk", "Mapei Ultracolor Plus (CG2WA)", f"fog {FOG}, fullt djup", "–"],
        ["7", "Stödvinkel", "bockad plåt 5, EN 1.4404", f"{W['liv']} × {W['fot']}, L ≤ {sv(W['L_max'])}, "
         f"glipa {W['glipa']}; hål 18 × 30, avlånga längs vinkeln", "under nedersta skiftet"],
        ["8", "Gängstång i injektionsmassa", "fischer FIS V (ETA-02/0024) + gängstång M16 A4-70, 2 muttrar och "
         "2 brickor A4 per stång", f"hål Ø{S['hal_d']}, hef {S['hef']}", f"c/c ≤ {S['cc']}, ≤ {S['kant_max']} "
         "från vinkelns ände"],
        ["9", "Beslag", "plåt enligt arkitekt", "fall utåt, droppkant 15 utanför stenen", "stenens överkant"],
        ["10", "Rörelsefog", "bottningslist + Mapei Mapesil LM (neutral silikon för natursten)", "10",
         "inåtgående hörn, mot andra material, ≤ 6 m"],
    ]
    return dict(typ="tabell", kolumner=["Pos", "Del", "Produkt, material", "Mått (mm)", "Antal, avstånd"],
                bredd=(0, 0.9, 2.4, 1.7, 1.6), rader=rader, just=["l", "l", "l", "l", "l"], sz=6.6)


def dimensionering():
    L_, st, v, p = R["laster"], R["stang"], R["vinkel"], R["plugg"]
    d = lambda x, n=2: sv(x, n)  # noqa: E731
    rader = [
        ["Gängstång M16, böjning genom cellplasten", f"V = {d(st['V'])} kN, hävarm {d(st['l'], 0)} mm, "
         f"M = {d(st['M'], 3)} kNm", f"MRd = {d(st['MRd'], 3)} kNm", d(st['utn_M'])],
        ["Gängstång M16, bändbrott i betongen", f"V = {d(st['V'])} kN", f"VRd,cp = {d(st['VRd_cp'], 1)} kN",
         d(st['utn_cp'])],
        ["Gängstång, nedböjning", f"vinkelns framkant {d(st['fall'], 1)} mm", "–", "–"],
        ["Stödvinkel, ben och böjning", f"upplag {d(v['upplag'], 0)} mm", f"{d(v['f_d'], 0)} MPa",
         d(max(v['utn_ben'], v['utn_M']))],
        ["Isolerplugg, vindsug", f"wd = {d(L_['wd'])} kN/m²", f"{d(p['n'], 1)} × {d(p['NRd'])} kN/m²", d(p['utn'])],
    ]
    return [
        dict(typ="text", sz=6.4, rader=[
            f"Sten {d(L_['g_sten'])} + fästmassa {d(L_['g_fast'])} = {d(L_['g'])} kN/m². Vinkeln bär hela "
            f"stenhöjden {sv(H_MAX / 1000, 1)} m om fästet mot cellplasten går förlorat: qd = 0,91 · 1,35 · "
            f"{d(L_['qk'])} = {d(L_['qd'])} kN/m. Vindsug wd = 0,91 · 1,5 · {sv(IN['vind']['cpe'], 1)} · "
            f"{sv(IN['vind']['qp'], 2)} = {d(L_['wd'])} kN/m² (qp F-01).",
            "Gängstången räknas med hävarm genom cellplasten utan inspänning i vinkeln (SS-EN 1992-4 6.2.2.3, "
            f"αM = 1), MRk = 1,2 Wel fuk, γMs = {sv(max(1.25, S['fuk'] / S['fyk']), 2)}. Bändbrott: τRk,cr "
            f"{sv(S['tau_Rk_cr'], 1)} · ψc {sv(S['psi_c'], 2)} · ψ0sus {sv(S['psi0_sus'], 2)}, k8 2, γM 1,5. "
            "Plugg: NRk 1,5 kN, γM 2,0, minst 4 st/m² för natursten (DIBt Z-33.46-568). Beräkning: "
            "U-02/berakning.py."]),
        dict(typ="tabell", kolumner=["Kontroll", "Last", "Bärförmåga", "Utn."], bredd=(1.6, 1.8, 1.0, 0.4),
             rader=rader, just=["l", "l", "l", "r"], sz=6.6)]


def blad_detaljer():
    vyer = [sektion_a(), detalj_b(), detalj_c()]
    kol = [
        dict(typ="rubrik", text="Anvisningar"),
        dict(typ="lista", sz=7.0, rader=[
            "Gäller källarväggarnas ytterväggar av Sundolitt Kub 350-150 där fasadsten sätts ovan mark. Stenen "
            "limmas mot armeringsbruket, som hålls mot betongkärnan av isolerpluggarna genom nätet. Stödvinkeln "
            "under nedersta skiftet bär stenens tyngd om fästet mot cellplasten går förlorat. Inga infästningar i "
            "de enskilda stenarna.",
            "Cellplasten raspas plan. Det härdade armeringsbruket får avvika högst 2 mm över stenens längsta kant.",
            "Gängstängerna (8) först: hål Ø18 genom cellplasten och 100 mm in i betongen, blåses rena och "
            "injekteras. Den inre muttern och brickan ställs i ett urtag i cellplasten, med brickan i "
            "armeringsbrukets yta.",
            "Armeringsbruket (2) i två lager med nätet i den yttre tredjedelen, skarvar 100 mm och diagonalnät vid "
            "öppningarnas hörn. Isolerpluggarna (3) sätts genom nätet i det första lagret; tallrikarna täcks "
            "direkt av det andra.",
            "Stödvinkeln (7) på stängerna, rak och i våg (justeras med de inre muttrarna), yttre bricka och mutter.",
            "Stenen (5) sätts med fästmassa (4) på både vägg och sten, 100 % täckning; lyft en sten då och då och "
            "kontrollera. Armeringsbruket härdar först enligt produktbladet, normalt cirka en vecka. Lägst +5 °C "
            "vid läggning och härdning.",
            "Fogarna (6) fylls helt och komprimeras. Rörelsefogar (10) vid inåtgående hörn, mot andra material "
            "och högst var 6:e meter.",
            "Ingen cellplast får synas: beslag (9) över överkanten, sten eller plåt i öppningarnas smygar, "
            "armeringsbruket nedtill till 200 mm under mark.",
            "Avstånd till betongkärnans kanter (öppningar, väggens ände) och mellan infästningar minst 100 mm.",
            "Positioner, fasad och kontroller: U-02.2.",
        ]),
        dict(typ="rubrik", text="Teckenförklaring"),
        dict(typ="symboler", rader=[
            dict(form="yta", fyll="betong", stil="tunn", text="betong (Kub-kärna, bjälklag)"),
            dict(form="yta", fyll="eps", stil="tunn", text="cellplast (Kub)"),
            dict(form="yta", fyll=BRUK, stil="tunn", text="armeringsbruk, fästmassa"),
            dict(form="yta", fyll=STEN, stil="tunn", text="granit"),
            dict(form="yta", fyll="stal", stil=None, text="rostfritt stål EN 1.4404 (A4)"),
            dict(form="yta", fyll=GJUT, stil="tunn", text="injektionsmassa"),
            dict(form="linje", stil="dold", text="glasfibernät"),
            dict(form="bubbla", txt="1", text="position, se U-02.2")]),
    ]
    return Blad(hd("U-02.1"), REVISIONER, kol, vyer)


def blad_fasad():
    ve, info = fasad_e()
    block = [dict(x=24, y=162, w=300, innehall=[dict(typ="rubrik", text="Positionsförteckning"), positioner()]),
             dict(x=24, y=214, w=300, innehall=[dict(typ="rubrik", text="Dimensionering")] + dimensionering())]
    kol = [
        dict(typ="rubrik", text="Förutsättningar"),
        dict(typ="lista", sz=7.0, rader=[
            f"Källarväggar av Sundolitt Kub 350-150 (U17): betongkärna {KARNA} mm, cellplast {EPS} mm på var sida "
            "(SINTEF TG 2216). Betong enligt Sundolitt, räknas som C30/37.",
            f"Granit 40 mm, 108 kg/m². Sten högst 1 200 × 600 mm och 0,72 m² (största sten "
            f"{sv(R['sten']['kg_max'], 0)} kg). Stenhöjd på en stödvinkel högst {sv(H_MAX)} mm (modellen: "
            "0,8–2,0 m).",
            "Stenens framsida 55 mm utanför cellplasten, 155 mm utanför betongkärnan; väggen blir cirka 405 mm.",
            "Uppbyggnaden följer de godkända systemen för natursten på cellplast (t.ex. DIBt Z-33.46-568): sten "
            "limmad på armerat bruk, pluggat genom nätet, utan infästningar i stenarna. Stenen här är 40 mm i "
            "stället för högst 20 mm; den extra tyngden tas av stödvinkeln.",
            "Allt stål rostfritt EN 1.4404 eller 1.4571 (A4), även mutter och bricka.",
            "Fästmassa, armeringsbruk och fogbruk från samma leverantör; leverantören bekräftar systemet för "
            "40 mm granit på cellplast.",
            f"Fasad E visar ett exempel: {info['stenar']} stenar, {info['plugg']} isolerplugg och "
            f"{info['stanger']} gängstänger på {sv(info['B'] / 1000, 1)} m vägg.",
        ]),
        dict(typ="rubrik", text="Teckenförklaring"),
        dict(typ="symboler", rader=[
            dict(form="linje", stil="dold", text="isolerpluggens tallrik bakom stenen (3)"),
            dict(form="yta", fyll="stal", stil=None, text="stödvinkel (7)"),
            dict(form="yta", fyll=STAL_L, stil="tunn", text="mutter på gängstång (8)"),
            dict(form="yta", fyll=STEN, stil="tunn", text="granit"),
        ]),
    ]
    return Blad(hd("U-02.2"), REVISIONER, kol, [ve], block)


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
