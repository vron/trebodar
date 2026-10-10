"""
AR-01 Fasadsten på källarväggarna, infästning: egen arbetsritning för utförandet (F-01 avsnitt 6), A3 med
../ritningsmall:

    AR-01.1  Sektion och detaljer                         1:10, 1:2,5, 1:2
    AR-01.2  Fasad och positioner                         1:20

Underlag: indata.toml och resultat.json (berakning.py). Allt ritas i verkliga koordinater i mm: x = 0 i
betongkärnans yttre yta (utåt positivt), y = 0 i stödvinkelns överkant (stenens underkant). I fasaden (AR-01.2) är
x längs väggen. ritningsmall/ritning.py skalar till papperet.

Filen är uppdelad i:
    1. Underlag           mått ur indata och resultat
    2. Byggdelar          vägg, sten, vinkel, stång, plugg (ritas i flera vyer)
    3. Vyer               en funktion per vy
    4. Blad               högerkolumn, tabeller och ritningshuvud
    5. main               skriver AR-01.x.json och PDF:en i ritningar/

    python beräkningar/AR-01/berakning.py
    python beräkningar/AR-01/ritningar.py
"""
import json
import os
import random
import sys
import tomllib

HERE = os.path.dirname(os.path.abspath(__file__))
BER = os.path.dirname(HERE)
ROT = os.path.dirname(BER)
UT = os.path.join(ROT, "ritningar")
sys.path.insert(0, os.path.join(BER, "ritningsmall"))
from ritning import Vy, Blad, huvud, sv, svm, PROJEKT  # noqa: E402

# ================================================================== 1. underlag
IN = tomllib.loads(open(os.path.join(HERE, "indata.toml"), encoding="utf-8").read())
R = json.load(open(os.path.join(HERE, "resultat.json"), encoding="utf-8"))

REV, DATUM = IN["projekt"]["revision"], IN["projekt"]["datum"]
UNDERLAG = "Kub TG 2216, K-06"
REVISIONER = [dict(rev=REV, avser="Första utgåvan", datum=DATUM, sign=PROJEKT["signatur"])]

KARNA, EPS, GIPS = IN["vagg"]["karna"], IN["vagg"]["eps"], IN["vagg"]["gips"]
X = R["lagen"]
X_BRUK, X_STB = X["bruk"], X["sten_bak"]                              # 106, 115
X_STF, X_STF_MAX = X["sten_fram_min"], X["sten_fram_max"]             # 145, 165 (kluven framsida 30–50)
X_STM = X["sten_mitt"]
X_VF = X["vinkel_fram"]                                                # 156, vinkelns framkant (L 50 × 50 × 5)
DROPP = 5                                                              # beslagets droppkant utanför stenens yttersta del
ST = IN["sten"]
T_MIN, T_MAX = IN["skikt"]["sten_min"], IN["skikt"]["sten_max"]
FOG = ST["fog"]
SH = ST["hojd"]                                                        # 400
MOD_Y = SH + FOG                                                       # 410
L_MIN, L_MAX = ST["langd"]                                             # 600–1 200
H_MAX = ST["H_max"]
MARK = 50                                                              # färdig mark över vinkelns överkant
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


def sten(v, y0, y1, fro=0):
    """En sten i snitt med fästmassan bakom: sågad baksida, kluven framsida 30–50 mm (slumpad men fast profil)."""
    rng = random.Random(fro * 7919 + int(y0))
    n = max(3, int((y1 - y0) / 30))
    ys = [y0 + (y1 - y0) * i / n for i in range(n + 1)]
    t = [T_MIN + 4]
    for _ in ys[1:]:
        t.append(min(T_MAX, max(T_MIN, t[-1] + rng.uniform(-9, 9) + (T_MIN + T_MAX) / 2 * 0.08
                                 - t[-1] * 0.08)))
    t[-1] = T_MIN + 4
    with v.lager("sten"):
        v.rekt(X_BRUK, y0, X_STB, y1, fyll=BRUK, stil=None)
        v.polygon([(X_STB, y0)] + [(X_STB + ti, yi) for ti, yi in zip(t, ys)] + [(X_STB, y1)], fyll=STEN,
                  stil="tunn")


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
        v.polygon([(X_BRUK + W["t"], -250), (X_STF + 200, -250), (X_STF + 200, MARK), (X_STF_MAX + 3, MARK),
                   (X_STF_MAX + 3, 0), (X_BRUK + W["t"], 0)], fyll="jord", stil=None)
        v.linje([(X_STF_MAX + 3, MARK), (X_STF + 200, MARK)], "normal")
    vagg(v, -250, ytop, bryt=(True, False))
    with v.lager("vagg"):
        # bjälklaget gjuts med väggens översta del; cellplasten ute fortsätter som kantform
        v.rekt(-330, ytop, 0, ytop + hb, fyll="betong", stil=None)
        v.linje([(-330, ytop), (-KARNA - EPS - GIPS, ytop)], "tunn")
        v.linje([(-330, ytop + hb), (0, ytop + hb)], "tunn")
        v.rekt(0, ytop, EPS, ytop + hb + 60, fyll="eps", stil=None)
        v.linje([(EPS, ytop), (EPS, ytop + hb + 60)], "tunn"); v.linje([(0, ytop), (0, ytop + hb)], "tunn")
        v.brott((-330, ytop - 30), (-330, ytop + hb + 30), "tunn")
        v.rekt(X_BRUK, ytop + 20, X_STF_MAX + 5, ytop + 300, fyll=None, stil="dold")
        v.linje([(-150, ytop + hb), (-150, ytop + 300)], "dold")
    y0, k = 0, 0
    while y0 < ytop - 50:
        y1 = min(y0 + SH, ytop - 5)
        sten(v, y0, y1, k)
        y0, k = y1 + FOG, k + 1
    for kk in range(k):
        str_plugg(v, kk * MOD_Y + min(SH, ytop - 5 - kk * MOD_Y) / 2, enkel=True)
    vinkel_snitt(v)
    stang_snitt(v, enkel=True)
    with v.lager("stal"):
        v.linje([(EPS + 2, ytop + 60), (EPS + 2, ytop + 4), (X_STF_MAX + DROPP, ytop - 6),
                 (X_STF_MAX + DROPP, ytop - 22)], "normal")
    with v.lager("matt"):
        v.matty([0, H_MAX], X_STF_MAX + 40, [X_STF_MAX, X_STF_MAX], texter=[f"högst {sv(H_MAX)}"])
        v.mattx([0, EPS, X_STF_MAX], -180, [-60, -60, -60], texter=["100", "45–65"])
    etiketter(v, [
        ("beslag, fall utåt, droppkant 5 mm\nutanför stenens yttersta del", (X_STF_MAX + 3, ytop - 3), 9),
        ("Bohus Grå, 400 mm hög, 30–50 mm\ntjock, fog 10 mm", (X_STF + 5, 3 * MOD_Y + 250), 5),
        ("fästmassa 9 mm (6–12 mm)", (X_BRUK + 4, 3 * MOD_Y - 100), 4),
        ("armeringsbruk 6 mm med nät", (EPS + 3, 2 * MOD_Y + 300), 2),
        ("isolerplugg, 4,2 st/m²", (EPS - 30, 1 * MOD_Y + SH / 2), 3),
        ("Kub 350-150: kärna 150 mm,\ncellplast 100 + 100 mm", (-60, 1 * MOD_Y - 120), 1),
        ("stödvinkel L 50 × 50 × 5, under mark", (X_VF - 2, -2.5), 7),
        ("gängstång M16 c/c 300 mm", (40, S["y"]), 8),
    ], 230, 7.0, y_min=-150, y_max=2250)
    with v.lager("text"):
        v.text(-KARNA / 2, ytop + hb / 2, "mellanbjälklag", a="cm", sz=6.0, col="gra")
        v.text(X_STF_MAX + 12, ytop + 160, "vägg ovan", a="lm", sz=6.0, col="gra")
        v.text(X_STF + 70, -215, "färdig mark", a="lm", sz=6.0, col="gra", bg=True)
        v.text(-KARNA - EPS - GIPS - 35, 900, "inne", a="cm", sz=7.0, col="gra", rot=90)
        v.text(X_STF_MAX + 50, 800, "ute", a="cm", sz=7.0, col="gra", rot=90)
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
    sten(v, 0, yb1, 3)
    with v.lager("sten"):
        v.brott((X_BRUK - 10, yb1), (X_STF_MAX + 10, yb1), "tunn")
    with v.lager("mark"):
        v.polygon([(X_STF_MAX + 4, yb0), (X_STF_MAX + 60, yb0), (X_STF_MAX + 60, MARK), (X_STF_MAX + 4, MARK)],
                  fyll="jord", stil=None)
        v.polygon([(X_BRUK + W["t"], yb0), (X_STF_MAX + 4, yb0), (X_STF_MAX + 4, 0), (X_BRUK + W["t"], 0)],
                  fyll="grus", stil=None)
        v.linje([(X_STF_MAX + 4, MARK), (X_STF_MAX + 60, MARK)], "normal")
    vinkel_snitt(v)
    stang_snitt(v)
    with v.lager("matt"):
        v.mattx([0, EPS, X_BRUK, X_STB, X_STF, X_STF_MAX], 160, [yb1] * 6)
        v.mattx([X_BRUK, X_VF], -98, [-W["liv"], -W["t"]])
        v.matty([0, MARK], X_STF_MAX + 16, [X_STF_MAX + 10, X_STF_MAX + 4])
        v.mattx([-S["hef"], 0], -60, [S["y"] - S["hal_d"] / 2] * 2, texter=[f"{S['hef']} i betongen"])
        v.matty([-W["liv"], 0], X_VF + 20, [X_BRUK + W["t"], X_VF])
        v.matty([S["y"], 0], X_VF + 9, [X_BRUK + W["t"] + BRICKA + MUTTER_H, X_VF])
    etiketter(v, [
        ("granit 30–50 mm, kluven framsida", (X_STB + 20, 120), 5),
        ("fästmassa 9 mm", (X_STB - 4, 85), 4),
        ("armeringsbruk 6 mm med nät", (X_BRUK - 3, 60), 2),
        ("färdig mark 50 mm över vinkeln", (X_STF_MAX + 30, MARK), None),
        ("stödvinkel L 50 × 50 × 5, EN 1.4404", (X_VF - 3, -2.5), 7),
        ("mutter och bricka på båda sidor om\nlivet; den inre i urtag i cellplasten",
         (X_BRUK + W["t"] + BRICKA + 6, S["y"] + 8), None),
        ("gängstång M16 A4-70 i injektionsmassa", (-40, S["y"]), 8),
    ], 196, 7.0, y_min=-112, y_max=150)
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
            v.brott((-90, y), (X_STF_MAX + 10, y), "tunn")
    sten(v, yb0, yb1, 5)
    str_plugg(v, 0)
    with v.lager("matt"):
        v.mattx([-P_DJUP, 0, EPS, X_BRUK], -66, [-4, yb0, yb0, yb0],
                texter=[f"{round(P_DJUP)}", "100", "6"])
        v.mattx([-P_DJUP, EPS + 3.5], 55, [4, P["tallrik"] / 2], texter=[f"L = {P['L']}"])
    etiketter(v, [
        ("granit 30–50 mm", (X_STB + 18, 70), 5),
        ("fästmassa 9 mm", (X_STB - 4, 45), 4),
        ("andra lagret armeringsbruk", (X_BRUK - 1, 22), None),
        ("tallrik på första lagret, genom nätet", (EPS + 2, -10), None),
        ("nät i yttre tredjedelen", (EPS + 4.2, -45), None),
        ("EJOT STR U 2G, L = 155 mm, tallrik Ø60 mm", (40, 0), 3),
    ], 170, 7.0, y_min=-60, y_max=95)
    with v.lager("rubrik"):
        v.rubrik(-85, -100, "DETALJ C  Armeringsbruk och isolerplugg genom nätet", skala=2, sz=9)
    return v


def fasad_e():
    """E: fasad, exempel med Bohus Grå 400 hög i slumpade längder 600–1 200 och hörnstenar i vänstra hörnet.
    x längs väggen. 1:20"""
    B = 4000
    nsk = ST["skift_exempel"]
    Hf = nsk * MOD_Y - FOG
    v = Vy(x=24, y=12, w=300, h=150, skala=20, X0=-300, Y1=Hf + 400)
    with v.lager("mark"):
        v.polygon([(-150, MARK), (B + 150, MARK), (B + 150, -260), (-150, -260)], fyll="jord", stil=None)
        v.linje([(-150, MARK), (B + 150, MARK)], "normal")
    rng = random.Random(579)
    stenar = []
    with v.lager("sten"):
        v.rekt(0, MARK, B, Hf, fyll=BRUK, stil=None)
        for k in range(nsk):
            y0 = k * MOD_Y
            hornl = ST["horn"][1] if k % 2 == 0 else ST["horn"][0]
            x = 0
            ln = hornl
            while x < B:
                b = min(x + ln, B)
                if b - x > 50:
                    v.rekt(x, max(y0, MARK), b, y0 + SH, fyll=STEN if x > 0 else "#bdb6aa", stil="tunn")
                    stenar.append((k, x, b))
                x = b + FOG
                ln = rng.choice(range(L_MIN, L_MAX + 1, 100))
                if B - (x + ln) < L_MIN and B - x > ln:
                    ln = B - x
        v.linje([(0, MARK), (0, Hf)], "normal")
    plugg = []
    for k in range(nsk):
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
        v.rekt(0, -W["liv"], B, 0, fyll=None, stil="dold")
        for xx in stanger:
            v.cirkel(xx, S["y"], NYCKEL / 2, fyll=None, stil="dold", modell=True)
        v.linje([(-20, Hf + 8), (B + 20, Hf + 8)], "grov")
    with v.lager("matt"):
        v.mattx([0] + stanger[:3] + [stanger[-1], B], -330, [-W["liv"]] * 6,
                texter=[sv(S["kant_max"]), sv(cc), sv(cc), f"… {n} × {sv(cc)} …", sv(S["kant_max"])])
        v.matty([k * MOD_Y for k in range(nsk)] + [Hf], -120, [0] * (nsk + 1),
                texter=[f"{SH} + {FOG}"] * (nsk - 1) + [f"{SH}"])
        px = sorted(xx for xx, yy in plugg if abs(yy - SH / 2) < 1)
        v.mattx([px[0], px[1]], SH / 2 + 60, [SH / 2, SH / 2], texter=[f"c/c {P['cc_x']}"])

    with v.lager("text"):
        v.text(B + 80, -30, "stödvinkel (7) på gängstänger\nM16 (8), under mark", a="lm", sz=6.4)
        v.text(B + 80, MOD_Y + SH / 2, "isolerplugg (3) bakom\nstenen, i skiftens mitt", a="lm", sz=6.4)
        v.text(B + 80, Hf + 8, "beslag (9)", a="lm", sz=6.4)
        v.text(B + 80, 2 * MOD_Y + SH / 2, "Bohus Grå (5), längd\n600–1 200, slumpad", a="lm", sz=6.4)
        v.text(0, Hf + 40, "hörnstenar 400 och 200 i varannat skift (5)", a="lb", sz=6.4)
        for k_, a_, b_ in stenar:
            v.text((a_ + b_) / 2, k_ * MOD_Y + SH - 60, svm(b_ - a_), a="ct", sz=5.8, col="gra")
        v.text(-150, -140, "färdig mark", a="lm", sz=6.0, col="gra", bg=True)
    with v.lager("rubrik"):
        v.rubrik(-290, -440, "FASAD E  Exempel, Bohus Grå 400 hög i slumpade längder, utvändigt hörn till vänster",
                 skala=20, sz=9)
    return v, dict(plugg=len(plugg), stanger=len(stanger), stenar=len(stenar), B=B)


# ================================================================== 4. blad
BLADEN = [
    ("AR-01.1", ["Fasadsten på källarväggarna", "Sektion och detaljer"], "1:10, 1:2,5, 1:2",
     "AR-01.1 Fasadsten, sektion och detaljer"),
    ("AR-01.2", ["Fasadsten på källarväggarna", "Fasad och positioner"], "1:20",
     "AR-01.2 Fasadsten, fasad och positioner"),
]


def hd(nr):
    b = [x for x in BLADEN if x[0] == nr][0]
    return huvud(nr, b[1], b[2], UNDERLAG, DATUM, REV)


def positioner():
    """Positionsförteckning: samma nummer som bubblorna på AR-01.1."""
    p = R["plugg"]
    rader = [
        ["1", "Vägg", "Sundolitt Kub 350-150 (U17), SINTEF TG 2216", "kärna 150 betong, cellplast 100 + 100", "–"],
        ["2", "Armeringsbruk med nät", "Mapei Mapetherm AR1 + Mapetherm Net (putssystem för cellplast)",
         "6 (5–7) i två lager, nät i yttre tredjedelen, skarv 100",
         "hela stenytan, ned 200 under mark"],
        ["3", "Isolerplugg", f"{P['produkt']}", f"L = {P['L']}, tallrik Ø{P['tallrik']}, borrdjup ≥ "
         f"{round(P_DJUP) + 10} i betongen", f"c/c {P['cc_x']} i skiftens mitthöjd, förskjutna {P['cc_x'] // 2} "
         f"({sv(p['n'], 1)} st/m²)"],
        ["4", "Fästmassa", "Mapei Keraflex Maxi S1 (C2TE S1, för natursten)",
         "9 (6–12), kombinerad metod", "100 % täckning"],
        ["5", "Fasadsten", "Beklädnadsgranit Bohus Grå, Stengrossen (order 579): kluven framsida, sågad baksida; "
         "hörnstenar Bohus Grå", f"{L_MIN}–{sv(L_MAX)} × {SH} × 30/50; hörn 200–400 × {SH} × 30/50",
         "28 m² och 9 hörnstenar"],
        ["6", "Fogbruk", "Mapei Ultracolor Plus (CG2WA)", f"fog {FOG}, fullt djup", "–"],
        ["7", "Stödvinkel", "vinkelstål L 50 × 50 × 5, EN 1.4404 (A4)", f"L ≤ {sv(W['L_max'])}, glipa "
         f"{W['glipa']}; hål 18 × 30, avlånga längs vinkeln", f"under nedersta skiftet, {MARK} under mark"],
        ["8", "Gängstång i injektionsmassa", "fischer FIS V (ETA-02/0024) + gängstång M16 A4-70, 2 muttrar och "
         "2 brickor A4 per stång", f"hål Ø{S['hal_d']}, {S['hef']} in i betongen", f"c/c ≤ {S['cc']}, ≤ {S['kant_max']} "
         "från vinkelns ände"],
        ["9", "Beslag", "plåt enligt ritning", f"fall utåt, droppkant {DROPP} utanför stenens yttersta del",
         "stenens överkant"],
        ["10", "Anslutningsfog", "bottningslist + Mapei Mapesil LM (neutral silikon för natursten)", "10",
         "mot dörr- och fönsterkarmar och andra material"],
    ]
    return dict(typ="tabell", kolumner=["Pos", "Del", "Produkt, material (eller motsvarande)", "Mått (mm)",
                                       "Antal, avstånd"],
                bredd=(0, 0.9, 2.4, 1.7, 1.6), rader=rader, just=["l", "l", "l", "l", "l"], sz=6.6)


def kontrollera():
    """Ritningen byggs bara när alla kontroller i berakning.py är uppfyllda; resultaten skrivs inte ut."""
    if not R.get("ok"):
        raise SystemExit("AR-01: någon kontroll i berakning.py är inte uppfylld, se resultat.json (utn).")


def blad_detaljer():
    vyer = [sektion_a(), detalj_b(), detalj_c()]
    kol = [
        dict(typ="rubrik", text="Anvisningar"),
        dict(typ="lista", sz=7.0, rader=[
            "Gäller källarväggarnas ytterväggar av Sundolitt Kub 350-150 där fasadsten sätts ovan mark. Stenen "
            "limmas mot armeringsbruket, som hålls mot betongkärnan av isolerpluggarna genom nätet. Stödvinkeln "
            "under nedersta skiftet bär stenens tyngd om fästet mot cellplasten går förlorat. Inga infästningar i "
            "de enskilda stenarna.",
            "Det härdade armeringsbruket får avvika högst 4 mm över stenens längsta kant.",
            "Gängstängerna (8) först: hål Ø18 genom cellplasten och 100 mm in i betongen. Hålet borstas och "
            "blåses rent, fylls med injektionsmassa från botten och stången trycks in med en vridning. Verktyg: "
            "borrhammare, patronpistol för injektionsmassa, rensborste och blåspump. Den inre muttern och brickan "
            "ställs i ett urtag i cellplasten, med brickan i armeringsbrukets yta.",
            "Armeringsbruket (2) i två lager med nätet i den yttre tredjedelen, skarvar 100 mm och diagonalnät vid "
            "öppningarnas hörn. Isolerpluggarna (3) sätts genom nätet i det första lagret; tallrikarna täcks "
            "direkt av det andra.",
            f"Stödvinkeln (7) på stängerna, rak och i våg (justeras med de inre muttrarna), yttre bricka och mutter. "
            f"Vinkelns överkant {MARK} mm under färdig mark, så att den inte syns.",
            "Stenen (5) sätts med fästmassa (4) på både vägg och den sågade baksidan, 100 % täckning.",
            "Stenarna sätts skift för skift med fulla liggfogar, så att varje sten står på skiftet under. "
            "Hörnstenar i utvändiga hörn. Fogarna (6) fylls helt och komprimeras, utom dräneringsfogar: "
            "stötfogarna i nedersta skiftet lämnas öppna närmast ovan mark, högst 800 mm isär. Mot dörr- och "
            "fönsterkarmar och andra material: anslutningsfog (10). Rörelsefogar i stenytan behövs inte: stenen "
            "sitter på cellplasten, fri från betongen, och längs den längsta fasaden (cirka 11,7 m) rör den sig "
            "bara några millimeter, fördelat på fogarna.",
            "Ingen cellplast får synas: beslag (9) över överkanten, sten eller plåt i öppningarnas smygar, "
            "armeringsbruket nedtill till 200 mm under mark.",
            "Avstånd till betongkärnans kanter (öppningar, väggens ände) och mellan infästningar minst 100 mm.",
            "Positioner och fasad: AR-01.2. Allt stål rostfritt A4, även mutter och bricka.",
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
            dict(form="bubbla", txt="1", text="position, se AR-01.2")]),
    ]
    return Blad(hd("AR-01.1"), REVISIONER, kol, vyer)


def blad_fasad():
    ve, info = fasad_e()
    block = [dict(x=24, y=152, w=300, innehall=[dict(typ="rubrik", text="Positionsförteckning"),
                                                dict(typ="text", sz=6.6, rader=[
                                                    "Infästningarna är kontrollerade i beräkningar/AR-01/"
                                                    "berakning.py."]), positioner()])]
    kol = [
        dict(typ="rubrik", text="Teckenförklaring"),
        dict(typ="symboler", rader=[
            dict(form="linje", stil="dold", text="isolerpluggens tallrik bakom stenen (3)"),
            dict(form="linje", stil="dold", text="stödvinkel (7) och muttrar (8), under mark"),
            dict(form="yta", fyll=STEN, stil="tunn", text="granit"),
            dict(form="yta", fyll="#bdb6aa", stil="tunn", text="hörnsten"),
        ]),
    ]
    return Blad(hd("AR-01.2"), REVISIONER, kol, [ve], block)


# ================================================================== 5. main
SERIE = "AR-01 Fasadsten på källarväggarna"


def main(dolj=()):
    kontrollera()
    os.makedirs(UT, exist_ok=True)
    bladmapp = os.path.join(HERE, "blad")
    os.makedirs(bladmapp, exist_ok=True)
    fn = {"AR-01.1": blad_detaljer, "AR-01.2": blad_fasad}
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
