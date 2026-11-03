"""Kökets inbyggnad (ärende #20): kylen, frysen och skafferiet bakom en vägg av gips från golvet till innertaket,
framför L4:s skikt mot köket från L2:s linje till 3NV:s insida, och ett förråd ovanför som nås med en lucka i gaveln
mot gången. Kylen, frysen, skåpen, fronterna och skafferiets dörr och hyllor är inredning (hus/inredning/kok.py).

Väggarna (lägena i lattvaggar.py) är lätta väggar 45×70 C24 som de andra innerväggarna och står framför de befintliga
väggarnas färdiga skikt (L4, 3NV): fronten L15, gaveln L16 i L2:s linje och mellanväggarna L17 (mot huvudstolpen
LN1_3) och L18, mitt bakom frontens dubbla reglar mellan öppningarna. Fronten och gaveln går upp till innertaket
(fronten snett efter båda takfallen, med hammarbandet delat i nocken) och har mot köket och gången OSB 12 och gips 13
som de andra innerväggarna; fronten står 13 mm söder om huvudstolpens strävor och överstycke, som hamnar i förrådet.
Fronten har tre öppningar från golvet till 2 100 med överstycken: kylens och frysens nischer (600 fria) och
skafferiets dörr (500 fri), med smyg av vitmålad furu 15 i stommens och skivornas djup. Mellanväggarna går upp till
förrådsgolvet.

Förrådet: golv av OSB 22 med överkanten 2 167 på bärläkt 45×45 längs gaveln, fronten och (över skafferiet) L4 och
3NV, på mellanväggarnas hammarband och på en regel mitt över skafferiet. Över kylen och frysen slutar golvet 60 mm
från L4: där stiger luften från vitvarornas ventilation (in genom socklarna, upp bakom vitvarorna och skåpen) in i
förrådet och ut genom ett galler i fronten över varje nisch. Luckan i gavelns norra del (500 × 600 i stommen,
underkanten i golvets överkant) har smyg och blad av vitmålad furu i liv med väggen. Inuti gips 13: på gaveln mot
kylen och på frontens insida i skafferiet upp till bärläkten, på mellanväggarna upp till golvet och i skafferiets
tak; förrådet är oinklätt.
"""
from __future__ import annotations

from shapely.geometry import Polygon
from shapely.geometry import box as plan_box

from modellering import Del, Form, Kapad, Montage, Placering, box, prisma

from trebodar.byggdelar.virke import fmt, virke_i_lada
from trebodar.material import C24, FONSTERTRA, GIPS, OSB, VENTILATIONSDON

from .lattvaggar import (H_VIRKE, K_BAK, K_FRAM, K_LUCKA, K_OPPNINGAR, K_SMYG, K_STOLPE, K_X0, K_X1, K_YTA, KOKET,
                         LATTA, T)
from .skikt import SKIVOR, under_taket, upp_till_taket, vid_nocken

VAGGAR = {lv.kod: lv for lv in LATTA if lv.grupp == KOKET}
OSB_T, GIPS_T = SKIVOR[0][1], SKIVOR[1][1]
H_OPPNING = 2100.0                                          # öppningarna i fronten, från golvet
Z_GOLV = H_OPPNING + H_VIRKE                                # förrådsgolvets underkant: bärläkten och mellanväggarna
GOLV_T = 22.0
LAKT_T = 45.0                                               # bärläkten 45×45
SPRINGA = 60.0                                              # mellan förrådsgolvet och L4 över kylen och frysen
GALLER = (400.0, 100.0, 2650.0)                             # gallret över nischerna: bredd, höjd, underkant
CC = 600.0
assert K_LUCKA[2] == Z_GOLV + GOLV_T, "luckans underkant i förrådsgolvets överkant"

OPPNINGAR = {namn: (K_X0 + u0, K_X0 + u1) for namn, (u0, u1) in K_OPPNINGAR.items()}   # x i stommen
X_VAST = K_X0 - T - OSB_T - GIPS_T                         # gavelns yta mot gången
L17_X = (VAGGAR["L17"].origo[0] - T, VAGGAR["L17"].origo[0])
L18_X = (VAGGAR["L18"].origo[0] - T, VAGGAR["L18"].origo[0])
SKAFFERI = (L18_X[1] + GIPS_T, K_X1, K_BAK, K_FRAM - GIPS_T)  # skafferiets insida: x0, x1, y0, y1
Y_LUCKA = (K_BAK + K_LUCKA[0], K_BAK + K_LUCKA[1])


def fritt(namn: str) -> tuple[float, float]:
    """Öppningens fria bredd mellan smygarna (x)."""
    x0, x1 = OPPNINGAR[namn]
    return x0 + K_SMYG, x1 - K_SMYG


def _hammarband(p: Polygon) -> list[Form]:
    return [Kapad(upp_till_taket(bit, 0.0), *under_taket(bit, H_VIRKE)) for bit in vid_nocken(p)]


def _regel(p: Polygon) -> Form:
    """Regel från syllen upp till hammarbandet."""
    return upp_till_taket(p, H_VIRKE, H_VIRKE)


def _frontens_reglar() -> list[float]:
    """Frontens reglar (x0): vid öppningarnas sidor (gaveln är kylens vänstra), i änden mot 3NV och c/c högst 600
    däremellan där väggen är hel."""
    xs = sorted({x for x0, x1 in OPPNINGAR.values() for x in (x0 - H_VIRKE, x1) if x > K_X0 - 1.0}
                | {K_X1 - H_VIRKE})
    ut = [xs[0]]
    for x in xs[1:]:
        hel = not any(a < x and ut[-1] + H_VIRKE < b for a, b in OPPNINGAR.values())    # ingen öppning emellan
        while hel and x - ut[-1] > CC + H_VIRKE:
            ut.append(ut[-1] + CC)
        ut.append(x)
    return ut


def _stomme() -> Montage:
    m = Montage("Stomme", beskrivning="Lätta väggar 45×70 C24: syll, reglar, överstycken och hammarband")
    n: dict[str, int] = {}

    def lagg(kod: str, typ: str, namn: str, form: Form) -> None:
        n[kod + typ] = n.get(kod + typ, 0) + 1
        m.lagg(Del(f"{namn} 45×{fmt(T)} {kod}", form, C24), Placering(), f"{kod}-{typ}{n[kod + typ]:02d}")

    # fronten L15: syll där väggen når golvet, reglar till hammarbandet, överstycken över öppningarna
    y0, y1 = K_FRAM, K_FRAM + T
    hel = [(a, b) for a, b in zip([K_X0] + [x1 for _, x1 in OPPNINGAR.values()],
                                  [x0 for x0, _ in OPPNINGAR.values()] + [K_X1]) if b - a > 1.0]
    for a, b in hel:
        lagg("L15", "S", "Syll", box(a, b, y0, y1, 0.0, H_VIRKE))
    for x in _frontens_reglar():
        lagg("L15", "R", "Regel", _regel(plan_box(x, y0, x + H_VIRKE, y1)))
    for x0, x1 in OPPNINGAR.values():
        lagg("L15", "L", "Överstycke", box(x0, x1, y0, y1, H_OPPNING, H_OPPNING + H_VIRKE))
    for f in _hammarband(plan_box(K_X0, y0, K_X1, y1)):
        lagg("L15", "H", "Hammarband", f)
    # gaveln L16 med luckan: reglar vid ändarna och luckans sidor, bröstning och överstycke
    xa, xb = K_X0 - T, K_X0
    ya, yb = K_BAK, K_FRAM + T
    (u0, u1, z0, z1), (yl0, yl1) = K_LUCKA, Y_LUCKA
    lagg("L16", "S", "Syll", box(xa, xb, ya, yb, 0.0, H_VIRKE))
    for y in sorted({ya, yl0 - H_VIRKE, yl1, yb - H_VIRKE}):                        # gavelns första är luckans
        lagg("L16", "R", "Regel", _regel(plan_box(xa, y, xb, y + H_VIRKE)))
    lagg("L16", "L", "Bröstning", box(xa, xb, yl0, yl1, z0 - H_VIRKE, z0))
    lagg("L16", "L", "Överstycke", box(xa, xb, yl0, yl1, z1, z1 + H_VIRKE))
    for f in _hammarband(plan_box(xa, ya, xb, yb)):
        lagg("L16", "H", "Hammarband", f)
    # mellanväggarna upp till förrådsgolvet: syll, reglar vid ändarna och i mitten, hammarband
    for kod, (xa, xb), ya in (("L17", L17_X, K_STOLPE), ("L18", L18_X, K_BAK)):
        lagg(kod, "S", "Syll", box(xa, xb, ya, K_FRAM, 0.0, H_VIRKE))
        for y in (ya, (ya + K_FRAM - H_VIRKE) / 2, K_FRAM - H_VIRKE):
            lagg(kod, "R", "Regel", box(xa, xb, y, y + H_VIRKE, H_VIRKE, Z_GOLV - H_VIRKE))
        lagg(kod, "H", "Hammarband", box(xa, xb, ya, K_FRAM, Z_GOLV - H_VIRKE, Z_GOLV))
    return m


def _galler_x() -> list[tuple[str, float]]:
    return [(namn, sum(fritt(namn)) / 2) for namn in ("Kyl", "Frys")]


def _skikt() -> Montage:
    m = Montage("Skikt", beskrivning="Mot köket och gången OSB 12 och gips 13 upp till innertaket, inuti gips 13")
    # fronten mot köket, förbi gavelns ände till dess yta mot gången, med hål för öppningarna och gallren
    halen: list[Form] = [box(x0, x1, K_FRAM, K_YTA + 1.0, -1.0, H_OPPNING) for x0, x1 in OPPNINGAR.values()]
    b, h, z = GALLER
    halen += [box(x - b / 2, x + b / 2, K_FRAM, K_YTA + 1.0, z, z + h) for _, x in _galler_x()]
    # gaveln mot gången, med hål för luckan
    (_, _, z0, z1), (yl0, yl1) = K_LUCKA, Y_LUCKA
    lucka = box(X_VAST - 1.0, K_X0, yl0, yl1, z0, z1)
    # i hörnet möts skikten var för sig: frontens OSB fram till gavelns OSB och dess gips fram till gavelns yta,
    # gavelns gips förbi änden över frontens OSB, så att gipsen går runt hörnet
    w = K_FRAM + T
    for kod, typ, mat, d0, d1, hal, slut in (
            ("L15", "OS", OSB, w, w + OSB_T, halen, K_X0 - T - OSB_T),
            ("L15", "GI", GIPS, w + OSB_T, K_YTA, halen, X_VAST),
            ("L16", "OS", OSB, K_X0 - T - OSB_T, K_X0 - T, [lucka], w),
            ("L16", "GI", GIPS, X_VAST, K_X0 - T - OSB_T, [lucka], w + OSB_T)):
        yta = plan_box(slut, d0, K_X1, d1) if kod == "L15" else plan_box(d0, K_BAK, d1, slut)
        f = upp_till_taket(yta, 0.0)
        for hl in hal:
            f = f - hl
        namn = "OSB" if mat is OSB else "Gips"
        m.lagg(Del(f"{namn} {fmt(d1 - d0)} {kod}", f, mat), Placering(), f"{kod}-{typ}01")
    # inuti: gips på gaveln mot kylen och på frontens insida i skafferiet upp till bärläkten, på mellanväggarna upp
    # till förrådsgolvet och i skafferiets tak
    x_dorr = OPPNINGAR["Skafferi"][1]
    for kod, nr, lada in (
            ("L16", 2, (K_X0, K_X0 + GIPS_T, K_BAK, K_FRAM, 0.0, H_OPPNING)),
            ("L15", 2, (x_dorr, K_X1, K_FRAM - GIPS_T, K_FRAM, 0.0, H_OPPNING)),
            ("L17", 1, (L17_X[0] - GIPS_T, L17_X[0], K_STOLPE, K_FRAM, 0.0, Z_GOLV)),
            ("L17", 2, (L17_X[1], L17_X[1] + GIPS_T, K_STOLPE, K_FRAM, 0.0, Z_GOLV)),
            ("L18", 1, (L18_X[0] - GIPS_T, L18_X[0], K_BAK, K_FRAM, 0.0, Z_GOLV)),
            ("L18", 2, (L18_X[1], L18_X[1] + GIPS_T, K_BAK, K_FRAM, 0.0, Z_GOLV))):
        m.lagg(Del(f"Gips {fmt(GIPS_T)} {kod} insida", box(*lada), GIPS), Placering(), f"{kod}-GI0{nr}")
    sx0, sx1, sy0, sy1 = SKAFFERI
    m.lagg(Del(f"Gips {fmt(GIPS_T)} skafferiets tak", box(sx0, sx1, sy0, sy1, H_OPPNING - GIPS_T, H_OPPNING), GIPS),
           Placering(), "SKAFFERI-TAK")
    return m


def _forradet() -> Montage:
    """Förrådsgolvet: bärläkt längs väggarna, en regel mitt över skafferiet och OSB 22."""
    m = Montage("Förrådet", beskrivning="Golv av OSB 22 på bärläkt 45×45, mellanväggarnas hammarband och en regel")
    za, zb = Z_GOLV - LAKT_T, Z_GOLV
    sx0, sx1, _, _ = SKAFFERI
    yf = K_FRAM - LAKT_T
    xm = (sx0 + sx1) / 2
    lakt = [box(K_X0, K_X0 + LAKT_T, K_BAK, yf, za, zb),                          # gaveln
            box(K_X0, L17_X[0] - GIPS_T, yf, K_FRAM, za, zb),                     # fronten över kylen
            box(L17_X[1] + GIPS_T, L18_X[0] - GIPS_T, yf, K_FRAM, za, zb),        # fronten över frysen
            box(sx0, sx1, yf, K_FRAM, za, zb),                                    # fronten över skafferiet
            box(sx0, sx1, K_BAK, K_BAK + LAKT_T, za, zb),                         # L4 över skafferiet
            box(sx1 - LAKT_T, sx1, K_BAK + LAKT_T, yf, za, zb)]                   # 3NV
    for i, f in enumerate(lakt, start=1):
        m.lagg(Del(f"Bärläkt 45×{fmt(LAKT_T)} förrådet", f, C24), Placering(), f"FG-L{i:02d}")
    m.lagg(Del(f"Regel 45×{fmt(LAKT_T)} förrådet", box(xm - LAKT_T / 2, xm + LAKT_T / 2, K_BAK + LAKT_T, yf, za, zb),
               C24), Placering(), "FG-R01")
    # golvet: över kylen och frysen en springa mot L4 för vitvarornas ventilation
    ys = K_BAK + SPRINGA
    golv = [(K_X0, ys), (L18_X[0] - GIPS_T, ys), (L18_X[0] - GIPS_T, K_BAK), (K_X1, K_BAK), (K_X1, K_FRAM),
            (K_X0, K_FRAM)]
    m.lagg(Del(f"OSB {fmt(GOLV_T)} förrådets golv", prisma(golv, GOLV_T, z0=Z_GOLV), OSB), Placering(), "FG-OS01")
    return m


def _smygar() -> Montage:
    """Smyg av vitmålad furu i frontens öppningar och i luckan, luckans blad och gallren över nischerna."""
    m = Montage("Smygar, lucka och galler", beskrivning="Smyg och lucka av vitmålad furu, ventilationsgaller")

    def lagg(namn: str, lada: tuple[float, float, float, float, float, float], fiber: str, kod: str) -> None:
        d, pl = virke_i_lada(*lada, fiber, FONSTERTRA)
        m.lagg(Del(namn, d.form, FONSTERTRA), pl, kod)
    for namn, (x0, x1) in OPPNINGAR.items():
        kod = namn.upper()
        smyg = f"Smygbräda {fmt(K_YTA - K_FRAM)}×{fmt(K_SMYG)}"
        lagg(smyg, (x0, x0 + K_SMYG, K_FRAM, K_YTA, 0.0, H_OPPNING), "z", f"{kod}-SMYG-V")
        lagg(smyg, (x1 - K_SMYG, x1, K_FRAM, K_YTA, 0.0, H_OPPNING), "z", f"{kod}-SMYG-H")
        lagg(smyg, (x0 + K_SMYG, x1 - K_SMYG, K_FRAM, K_YTA, H_OPPNING - K_SMYG, H_OPPNING), "x", f"{kod}-SMYG-O")
    # luckan till förrådet: smyg runt om i gavelns djup och ett blad i liv med väggen, hängt i den norra smygen
    (_, _, z0, z1), (y0, y1) = K_LUCKA, Y_LUCKA
    smyg = f"Smygbräda {fmt(K_X0 - X_VAST)}×{fmt(K_SMYG)} luckan"
    lagg(smyg, (X_VAST, K_X0, y0, y0 + K_SMYG, z0, z1), "z", "LUCKA-SMYG-V")
    lagg(smyg, (X_VAST, K_X0, y1 - K_SMYG, y1, z0, z1), "z", "LUCKA-SMYG-H")
    lagg(smyg, (X_VAST, K_X0, y0 + K_SMYG, y1 - K_SMYG, z1 - K_SMYG, z1), "y", "LUCKA-SMYG-O")
    lagg(smyg, (X_VAST, K_X0, y0 + K_SMYG, y1 - K_SMYG, z0, z0 + K_SMYG), "y", "LUCKA-SMYG-U")
    spel, blad = 3.0, 22.0
    lagg(f"Lucka trä {fmt(y1 - y0 - 2 * K_SMYG - spel)}×{fmt(z1 - z0 - 2 * K_SMYG - 2 * spel)}",
         (X_VAST, X_VAST + blad, y0 + K_SMYG, y1 - K_SMYG - spel, z0 + K_SMYG + spel, z1 - K_SMYG - spel), "z",
         "LUCKA-BLAD")
    b, h, z = GALLER
    for namn, x in _galler_x():
        m.lagg(Del(f"Ventilationsgaller {fmt(b)}×{fmt(h)}", box(x - b / 2, x + b / 2, K_FRAM + T, K_YTA, z, z + h),
                   VENTILATIONSDON), Placering(), f"{namn.upper()}-GALLER")
    return m


def montage() -> Montage:
    m = Montage(KOKET, "Inbyggnad", "Kyl, frys och skafferi bakom en vägg av gips till innertaket, förråd "
                                    "ovanför med lucka (ärende #20): lätta väggar 45×70 L15–L18")
    m.lagg(_stomme())
    m.lagg(_skikt())
    m.lagg(_forradet())
    m.lagg(_smygar())
    return m
