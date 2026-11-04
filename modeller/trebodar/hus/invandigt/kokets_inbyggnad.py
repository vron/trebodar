"""Kökets inbyggnad (ärende #20 och #21): kylen, frysen och skafferiet bakom en vägg av gips från golvet till
innertaket, framför L4:s skikt mot köket från L2:s linje till 3NV:s insida, och ett förråd ovanför som nås med en lucka
i gaveln mot gången. Kylen, frysen, skåpen, fronterna och skafferiets dörr och hyllor är inredning
(hus/inredning/kok.py).

Fronten L15 (läget i lattvaggar.py) är en lätt vägg 45×70 C24 som de andra innerväggarna och står framför de
befintliga väggarnas färdiga skikt (L4, 3NV); den går upp till innertaket (snett efter båda takfallen, med
hammarbandet delat i nocken) och har mot köket OSB 12 och gips 13. Gaveln L16 mot gången är under förrådet bara två
gipsskivor i L2:s yta mot gången, så att köket blir bredare (ärende #21); ovanför har den stomme 45×70 på en syll i
förrådsgolvets överkant, med luckan, och OSB och gips mot gången. Fronten har en egen ändregel innanför gavelns
gipsskivor, kylens vänstra sida. Frontens gips står mot
huvudstolpen LN1_3:s strävor och topregel (de slutar vid y 7 362) och går förbi dem; där strävorna når in i frontens
stomme upptill (över dem, strävornas underkant i stommens bakkant) har stommen och OSB:n ett urtag: hammarbandet
slutar på var sida, en kortling under strävorna mellan två reglar på överstyckena bär gipsen och regeln mellan kylen
och frysen slutar under kortlingen. Fronten har tre öppningar från golvet till 2 100 med överstycken: kylens och
frysens nischer (600 fria) och skafferiets dörr (564 fri, bänken längs 3NV öster om den), med en regel mellan
öppningarna och smyg av vitmålad furu 15 i stommens och skivornas djup. Mellan nischerna och mot skafferiet bara två
gipsskivor (L17 och L18, mitt bakom regeln mellan öppningarna), upp till förrådets reglar.

Förrådet: golv av OSB 22 med överkanten 2 167 på bärläkt 45×45 längs gaveln, fronten och (över skafferiet) L4 och
3NV, på reglar 45×45 över gipsväggarna (från fronten till huvudstolpen respektive L4) och på en regel mitt över
skafferiet. Över kylen och frysen slutar golvet 60 mm från L4: där stiger luften från vitvarornas ventilation (in
genom socklarna, upp bakom vitvarorna och skåpen) in i förrådet och ut genom ett galler i fronten över varje nisch.
Luckan i gavelns norra del (500 × 600 i stommen, underkanten i golvets överkant) har smyg och blad av vitmålad furu
i liv med väggen. Inuti gips 13 på frontens insida i skafferiet upp till bärläkten och i skafferiets tak; förrådet är
oinklätt.
"""
from __future__ import annotations

from shapely.geometry import Polygon
from shapely.geometry import box as plan_box

from modellering import Del, Form, Kapad, Montage, Placering, box, prisma

from trebodar.byggdelar.virke import fmt, virke_i_lada
from trebodar.hus.stomme.prefab.stolpar import ln1_3
from trebodar.material import C24, FONSTERTRA, GIPS, OSB, VENTILATIONSDON

from .lattvaggar import (H_VIRKE, K_BAK, K_FRAM, K_GIPS, K_GIPS_T, K_LUCKA, K_OPPNINGAR, K_SMYG, K_STOLPE, K_X0, K_X1,
                         K_X_OPP, K_YTA, KOKET, LATTA, T)
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

OPPNINGAR = {namn: (K_X_OPP + u0, K_X_OPP + u1) for namn, (u0, u1) in K_OPPNINGAR.items()}   # x i stommen
X_VAST = K_X0 - T - OSB_T - GIPS_T                         # gavelns yta mot gången ovanför förrådet
X_GANG = K_GIPS - 2 * K_GIPS_T                             # gavelns gipsskivor under förrådet, ytan mot gången
Z_SYLL = K_LUCKA[2] - H_VIRKE                              # gavelns syll ovanför förrådet: gipsskivorna under den
# gipsväggarna L17 och L18: två skivor mitt bakom frontens regel mellan öppningarna, och regeln över var och en
MITT = {kod: VAGGAR[kod].origo[0] - T / 2 for kod in ("L17", "L18")}
L17_X = (MITT["L17"] - GIPS_T, MITT["L17"] + GIPS_T)
L18_X = (MITT["L18"] - GIPS_T, MITT["L18"] + GIPS_T)
SKAFFERI = (L18_X[1], K_X1, K_BAK, K_FRAM - GIPS_T)        # skafferiets insida: x0, x1, y0, y1
# huvudstolpens strävor och topregel i frontens stomme: x0, x1 (lagren och spikplåtarna, med spel) och underkanten
# (strävans undre kant vid stommens bakkant, med spel)
STRAVOR = (ln1_3.X0 - ln1_3.SPIK_T - 3.0, ln1_3.X0 + ln1_3.LAGER * ln1_3.T + ln1_3.SPIK_T + 3.0,
           ln1_3.ZS + K_FRAM - (ln1_3.YM + ln1_3.B / 2) - 5.0)
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
    """Frontens reglar (x0): vid öppningarnas sidor (ändregeln mot gaveln är kylens vänstra), i änden mot 3NV och
    c/c högst 600 däremellan där väggen är hel."""
    xs = sorted({x for x0, x1 in OPPNINGAR.values() for x in (x0 - H_VIRKE, x1) if x > K_GIPS - 1.0}
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

    # fronten L15: syll där väggen når golvet, reglar till hammarbandet, överstycken över öppningarna; runt
    # strävornas toppar slutar hammarbandet, och en kortling mellan två reglar på överstyckena bär gipsen
    y0, y1 = K_FRAM, K_FRAM + T
    sx0, sx1, sz = STRAVOR
    hel = [(a, b) for a, b in zip([K_GIPS] + [x1 for _, x1 in OPPNINGAR.values()],
                                  [x0 for x0, _ in OPPNINGAR.values()] + [K_X1]) if b - a > 1.0]
    for a, b in hel:
        lagg("L15", "S", "Syll", box(a, b, y0, y1, 0.0, H_VIRKE))
    for x in _frontens_reglar():
        if x + H_VIRKE > sx0 and x < sx1:                                          # under strävorna
            lagg("L15", "R", "Regel", box(x, x + H_VIRKE, y0, y1, H_VIRKE, sz - H_VIRKE))
        else:
            lagg("L15", "R", "Regel", _regel(plan_box(x, y0, x + H_VIRKE, y1)))
    for x in (sx0 - H_VIRKE, sx1):
        lagg("L15", "R", "Regel", upp_till_taket(plan_box(x, y0, x + H_VIRKE, y1), H_OPPNING + H_VIRKE, H_VIRKE))
    lagg("L15", "K", "Kortling", box(sx0, sx1, y0, y1, sz - H_VIRKE, sz))
    for x0, x1 in OPPNINGAR.values():
        lagg("L15", "L", "Överstycke", box(x0, x1, y0, y1, H_OPPNING, H_OPPNING + H_VIRKE))
    for a, b in ((K_GIPS, sx0), (sx1, K_X1)):
        for f in _hammarband(plan_box(a, y0, b, y1)):
            lagg("L15", "H", "Hammarband", f)
    # gaveln L16 ovanför förrådet: syll från L4 till frontens ändregel med överkanten i förrådsgolvets (luckans
    # underkant), reglar vid luckans sidor (den norra mot L4) och överstycke; under förrådet bara gipsskivorna
    xa, xb = K_X0 - T, K_X0
    ya, yb = K_BAK, K_FRAM
    (u0, u1, z0, z1), (yl0, yl1) = K_LUCKA, Y_LUCKA
    lagg("L16", "S", "Syll", box(xa, xb, ya, yb, Z_SYLL, z0))
    for y in (yl0 - H_VIRKE, yl1):
        lagg("L16", "R", "Regel", upp_till_taket(plan_box(xa, y, xb, y + H_VIRKE), z0, H_VIRKE))
    lagg("L16", "L", "Överstycke", box(xa, xb, yl0, yl1, z1, z1 + H_VIRKE))
    for f in _hammarband(plan_box(xa, ya, xb, yb)):
        lagg("L16", "H", "Hammarband", f)
    return m


def _galler_x() -> list[tuple[str, float]]:
    return [(namn, sum(fritt(namn)) / 2) for namn in ("Kyl", "Frys")]


def _skikt() -> Montage:
    m = Montage("Skikt", beskrivning="Mot köket och gången OSB 12 och gips 13 upp till innertaket, inuti gips 13; "
                                      "gaveln under förrådet två gipsskivor")
    # fronten mot köket, förbi gavelns ände till dess yta mot gången, med hål för öppningarna och gallren
    halen: list[Form] = [box(x0, x1, K_FRAM, K_YTA + 1.0, -1.0, H_OPPNING) for x0, x1 in OPPNINGAR.values()]
    b, h, z = GALLER
    halen += [box(x - b / 2, x + b / 2, K_FRAM, K_YTA + 1.0, z, z + h) for _, x in _galler_x()]
    # gaveln mot gången, med hål för luckan
    (_, _, z0, z1), (yl0, yl1) = K_LUCKA, Y_LUCKA
    lucka = box(X_VAST - 1.0, K_X0, yl0, yl1, z0, z1)
    # i hörnet möts skikten var för sig: frontens OSB fram till gavelns skivor, dess gips fram till gavelns yta
    # under förrådet; gavelns skivor förbi frontens ände över dess OSB, så att gipsen går runt hörnet
    w = K_FRAM + T
    for kod, typ, mat, d0, d1, hal, slut, z in (
            ("L15", "OS", OSB, w, w + OSB_T, halen, K_GIPS, 0.0),
            ("L15", "GI", GIPS, w + OSB_T, K_YTA, halen, X_GANG, 0.0),
            ("L16", "OS", OSB, K_X0 - T - OSB_T, K_X0 - T, [lucka], w, Z_SYLL),
            ("L16", "GI", GIPS, X_VAST, K_X0 - T - OSB_T, [lucka], w + OSB_T, Z_SYLL)):
        yta = plan_box(slut, d0, K_X1, d1) if kod == "L15" else plan_box(d0, K_BAK, d1, slut)
        f = upp_till_taket(yta, z)
        for hl in hal:
            f = f - hl
        if typ == "OS" and kod == "L15":                                            # strävornas toppar
            f = f - upp_till_taket(plan_box(STRAVOR[0], d0 - 1.0, STRAVOR[1], d1 + 1.0), STRAVOR[2])
        namn = "OSB" if mat is OSB else "Gips"
        m.lagg(Del(f"{namn} {fmt(d1 - d0)} {kod}", f, mat), Placering(), f"{kod}-{typ}01")
    # gaveln under förrådet: två gipsskivor upp till syllen, förbi frontens ände
    for nr, (a, b) in enumerate(((X_GANG, X_GANG + K_GIPS_T), (X_GANG + K_GIPS_T, K_GIPS)), start=2):
        m.lagg(Del(f"Gips {fmt(K_GIPS_T)} L16", box(a, b, K_BAK, w + OSB_T, 0.0, Z_SYLL), GIPS), Placering(),
               f"L16-GI0{nr}")
    # inuti: gips på frontens insida i skafferiet upp till bärläkten och i skafferiets tak; gipsväggarna mellan
    # nischerna och mot skafferiet, två skivor upp till förrådets reglar
    x_dorr = OPPNINGAR["Skafferi"][1]
    m.lagg(Del(f"Gips {fmt(GIPS_T)} L15 insida", box(x_dorr, K_X1, K_FRAM - GIPS_T, K_FRAM, 0.0, H_OPPNING), GIPS),
           Placering(), "L15-GI02")
    for kod, (xa, xb), ya in (("L17", L17_X, K_STOLPE), ("L18", L18_X, K_BAK)):
        for nr, (a, b) in enumerate(((xa, MITT[kod]), (MITT[kod], xb)), start=1):
            m.lagg(Del(f"Gips {fmt(GIPS_T)} {kod}", box(a, b, ya, K_FRAM, 0.0, Z_GOLV - LAKT_T), GIPS), Placering(),
                   f"{kod}-GI0{nr}")
    sx0, sx1, sy0, sy1 = SKAFFERI
    m.lagg(Del(f"Gips {fmt(GIPS_T)} skafferiets tak", box(sx0, sx1, sy0, sy1, H_OPPNING - GIPS_T, H_OPPNING), GIPS),
           Placering(), "SKAFFERI-TAK")
    return m


def _forradet() -> Montage:
    """Förrådsgolvet: bärläkt längs väggarna, reglar över gipsväggarna och mitt över skafferiet, OSB 22."""
    m = Montage("Förrådet", beskrivning="Golv av OSB 22 på bärläkt 45×45 och reglar 45×45")
    za, zb = Z_GOLV - LAKT_T, Z_GOLV
    _, sx1, _, _ = SKAFFERI
    yf = K_FRAM - LAKT_T
    r17, r18 = ((MITT[k] - LAKT_T / 2, MITT[k] + LAKT_T / 2) for k in ("L17", "L18"))     # reglarna över gipsväggarna
    sx0 = r18[1]
    xm = (sx0 + sx1) / 2
    lakt = [box(K_X0, K_X0 + LAKT_T, K_BAK, yf, za, zb),                          # gaveln
            box(K_X0, r17[0], yf, K_FRAM, za, zb),                                # fronten över kylen
            box(r17[1], r18[0], yf, K_FRAM, za, zb),                              # fronten över frysen
            box(sx0, sx1, yf, K_FRAM, za, zb),                                    # fronten över skafferiet
            box(sx0, sx1, K_BAK, K_BAK + LAKT_T, za, zb),                         # L4 över skafferiet
            box(sx1 - LAKT_T, sx1, K_BAK + LAKT_T, yf, za, zb)]                   # 3NV
    for i, f in enumerate(lakt, start=1):
        m.lagg(Del(f"Bärläkt 45×{fmt(LAKT_T)} förrådet", f, C24), Placering(), f"FG-L{i:02d}")
    for i, (xa, xb, y0) in enumerate(((*r17, K_STOLPE), (*r18, K_BAK), (xm - LAKT_T / 2, xm + LAKT_T / 2,
                                                                       K_BAK + LAKT_T)), start=1):
        m.lagg(Del(f"Regel 45×{fmt(LAKT_T)} förrådet", box(xa, xb, y0, yf, za, zb), C24),
               Placering(), f"FG-R{i:02d}")
    # golvet: över kylen och frysen en springa mot L4 för vitvarornas ventilation
    ys = K_BAK + SPRINGA
    golv = [(K_X0, ys), (r18[0], ys), (r18[0], K_BAK), (K_X1, K_BAK), (K_X1, K_FRAM), (K_X0, K_FRAM)]
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
                                    "ovanför med lucka (ärende #20, #21): lätta väggar L15 och L16, gipsväggar L17 "
                                    "och L18")
    m.lagg(_stomme())
    m.lagg(_skikt())
    m.lagg(_forradet())
    m.lagg(_smygar())
    return m
