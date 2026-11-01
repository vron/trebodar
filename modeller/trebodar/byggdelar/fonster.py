"""Fönster och dörrar från Elitfönster, parametriska efter tillverkarens snittritningar: karm, båge, isolerruta och
aluminiumbeklädnad med de synliga måtten exakta, i produktens eget system, så att en produkt kan sättas i vilken
öppning som helst och ändras för sig.

Produktens system: x längs bredden från karmens ytterkant, z uppåt från karmens underkant och y genom väggen med
y = 0 i karmens insida och negativt utåt (som väggarnas w). Bredden och höjden är karmens yttermått, modulmåttet − 20
(DREV runt om, Elitfönsters produktblad: modulen är minsta urtag i väggen). Profilerna anges med d utåt från karmens
insida och avstånd inåt från karmens ytterkant per sida (vänster, höger, under, över).

Ritningarna (Inwido):
- Original Alu 100 vridfönster 61-37-V221: karmdjup 115 (trä 105 och aluminium 10), karmen 53,5 bred inifrån, bågen
  50,5 vid sidorna, 48 upptill och 52 nedtill, glaskanten 104 / 101,5 / 105,5 från karmens ytterkant. Bottenstycket
  105 djupt med fall utåt och aluminiumprofil med droppnäsa.
- Fast karm 61-37-F221: glaset direkt i karmen, glaskanten 53,5 runt om.
- Altandörr 61-37-D221 (fönsterdörr, helglasad): karmen 52 vid sidorna och 53,5 upptill, tröskel 42, bågen 51,5 /
  53,5 / 52 och glaskanten 103,5 / 107 / 94.
- Isolerruta 3-glas 4-18-4-18-4 (48 mm), 40–88 mm utanför karmens insida, kanten 13,5 innanför glaskanten.
- Skjutdörr Alu ASP4 86-37-04 (2 skjutbara och 2 fasta delar): karmen 153 trä och 12 aluminium, de fasta delarna i
  det inre spåret 26 mm innanför karmen och de skjutbara i det yttre; glaskanten 131,2 från karmens ytterkant vid
  sidorna, 175,9 upptill och 161,2 nedtill och 219,8 mellan de skjutbara delarnas glas i mitten; tröskel av hårdträ
  (Merbau), 23 hög inne. Profilernas inre form är förenklad (rektanglar) och djupen är mätta på ritningen.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence

from modellering import Del, Form, Montage, Placering, Union, box, polyeder

from trebodar.byggdelar.polygon import prisma_x
from trebodar.byggdelar.virke import fmt
from trebodar.material import DORRBLAD, FONSTERALU, FONSTERTRA, GLAS, HARDTRA

Sidor = tuple[float, float, float, float]          # vänster, höger, under, över
Profil = Sequence[tuple[float, Sidor]]             # (d, sidor) runt en sluten polygon

DREV = 10.0                 # drevmån runt karmen
TRA, DJUP = 105.0, 115.0    # karmens trä och hela djup med aluminiumbeklädnaden
LAPP = 24.0                 # karmens läpp inifrån (med tätningslisten), bågen ligger an mot den
BAGE_IN, BAGE_TRA, BAGE_ALU = 24.0, 100.0, 112.0     # bågens insida, träets och aluminiumets yttersida (d)
RUTA = ((40.0, 44.0), (62.0, 66.0), (84.0, 88.0))   # isolerrutans glas (d)
RUTKANT, FALS = 13.5, 19.0  # rutans kant och glasfalsens botten innanför glaskanten


def _alla(v: float) -> Sidor:
    return (v, v, v, v)


NOLL = _alla(0.0)


def ram(b: float, h: float, profil: Profil) -> Form:
    """Rektangulär ram (karm, båge, beklädnad) med gering i hörnen: profilen svept runt bredden b och höjden h.
    Sidorna kan ha olika profil men lika många punkter; ytorna mellan två punkter är plana."""
    horn: list[tuple[float, float, float]] = []
    for d, (v, hg, u, o) in profil:
        horn += [(v, -d, u), (b - hg, -d, u), (b - hg, -d, h - o), (v, -d, h - o)]
    n = len(profil)
    ytor = [[4 * i + k, 4 * i + (k + 1) % 4, 4 * ((i + 1) % n) + (k + 1) % 4, 4 * ((i + 1) % n) + k]
            for i in range(n) for k in range(4)]
    return polyeder(horn, ytor)


def _plus(s: Sidor, d: float) -> Sidor:
    return (s[0] + d, s[1] + d, s[2] + d, s[3] + d)


def isolerruta(b: float, h: float, glas: Sidor, ruta: Sequence[tuple[float, float]] = RUTA) -> Form:
    """Isolerrutans glas, med kanten RUTKANT innanför glaskanten."""
    v, hg, u, o = _plus(glas, -RUTKANT)
    return Union(tuple(box(v, b - hg, -d1, -d0, u, h - o) for d0, d1 in ruta))


def _karm(b: float, h: float, lapp: Sidor, d_lapp: float, stomme: Sidor, botten_ut: float) -> Form:
    """Karmen i trä: läppen inifrån till d_lapp och karmens fulla djup närmast ytterkanten (stomme); bottenstyckets
    överkant faller utåt till botten_ut vid träets yttersida."""
    ut = (stomme[0], stomme[1], botten_ut, stomme[3])
    return ram(b, h, [(0.0, NOLL), (0.0, lapp), (d_lapp, lapp), (d_lapp, stomme), (TRA, ut), (TRA, NOLL)])


def _karm_alu(b: float, h: float, stomme: Sidor, z0: float) -> Form:
    """Karmens aluminiumbeklädnad på sidorna och upptill (från z0, ovanför bottenprofilen)."""
    s = (stomme[0], stomme[1], 1.0, stomme[3])
    r = ram(b, h, [(TRA, NOLL), (TRA, s), (DJUP, s), (DJUP, NOLL)])
    return r - box(-1.0, b + 1.0, -DJUP - 1.0, -TRA + 1.0, -1.0, z0)


def _bottenprofil(b: float, stomme: Sidor, lapp_ut: float, botten_ut: float, z_nasa: float) -> Form:
    """Bottenstyckets aluminiumprofil: 2 mm på bottenstyckets fall från d 60 och droppnäsan utanför träet."""
    fall = (lapp_ut - botten_ut) / (TRA - LAPP)

    def z(d: float) -> float:
        return lapp_ut - (d - LAPP) * fall
    platta = [(-60.0, z(60.0)), (-TRA, botten_ut), (-TRA, botten_ut + 2.0), (-60.0, z(60.0) + 2.0)]
    nasa = [(-TRA, z_nasa), (-DJUP, z_nasa), (-DJUP, botten_ut), (-TRA, botten_ut)]
    return Union((prisma_x(platta, stomme[0], b - stomme[1]), prisma_x(nasa, 0.0, b)))


def _bage(b: float, h: float, ytter: Sidor, glas: Sidor) -> Form:
    """Bågen i trä: insidan BAGE_IN bakom karmens insida, läppen till glaskanten och glasfalsen utifrån."""
    fals = _plus(glas, -FALS)
    return ram(b, h, [(BAGE_IN, ytter), (BAGE_IN, glas), (RUTA[0][0], glas), (RUTA[0][0], fals), (BAGE_TRA, fals),
                      (BAGE_TRA, ytter)])


def _bage_alu(b: float, h: float, ytter: Sidor, glas: Sidor) -> Form:
    """Bågens aluminiumbeklädnad med glaslisten, som sluttar från rutans utsida vid glaskanten."""
    fals = _plus(glas, -FALS)
    return ram(b, h, [(BAGE_TRA, ytter), (BAGE_TRA, fals), (RUTA[-1][1], fals), (RUTA[-1][1], glas),
                      (BAGE_ALU, _plus(glas, -13.0)), (BAGE_ALU, ytter)])


def _matt(b: float, h: float) -> str:
    return f"{fmt(b)}×{fmt(h)}"


# ------------------------------------------------------------------ vridfönster, fast karm och fönsterdörr
V_LAPP, V_STOMME, V_BOTTEN = _alla(53.5), (39.5, 39.5, 40.5, 39.5), 27.0
V_BAGE, V_GLAS = (43.0, 43.0, 44.0, 41.5), (104.0, 104.0, 105.5, 101.5)   # bågens ytterkant 2 mm från karmen upptill
F_GLAS = _alla(53.5)
D_LAPP, D_STOMME, D_BOTTEN = (52.0, 52.0, 42.0, 53.5), (37.5, 37.5, 28.0, 39.5), 20.5
D_BAGE, D_GLAS = (41.0, 41.0, 31.0, 41.5), (103.5, 103.5, 94.0, 107.0)
D_BLAD = 68.0               # ytterdörrens blad


def vridfonster(kod: str, b: float, h: float) -> Montage:
    """Elitfönster Original Alu 100 vridfönster (61-37-V221)."""
    m = Montage(kod, kod, f"Vridfönster Elitfönster Original Alu 100, karm {_matt(b, h)}")
    m.lagg(Del(f"Karm vridfönster {_matt(b, h)}", _karm(b, h, V_LAPP, LAPP, V_STOMME, V_BOTTEN), FONSTERTRA,
               artikel=f"Elitfönster Original Alu 100 vridfönster, karm {_matt(b, h)}"), Placering(), f"{kod}-KARM")
    m.lagg(Del(f"Karmbeklädnad aluminium {_matt(b, h)}", _karm_alu(b, h, V_STOMME, V_BOTTEN), FONSTERALU),
           Placering(), f"{kod}-KARMALU")
    m.lagg(Del(f"Bottenprofil aluminium {fmt(b)}", _bottenprofil(b, V_STOMME, V_STOMME[2], V_BOTTEN, 10.0),
               FONSTERALU), Placering(), f"{kod}-BOTTEN")
    m.lagg(Del(f"Båge vridfönster {_matt(b, h)}", _bage(b, h, V_BAGE, V_GLAS), FONSTERTRA), Placering(), f"{kod}-BAGE")
    m.lagg(Del(f"Bågbeklädnad aluminium {_matt(b, h)}", _bage_alu(b, h, V_BAGE, V_GLAS), FONSTERALU), Placering(),
           f"{kod}-BAGEALU")
    gb, gh = b - 2 * (V_GLAS[0] - RUTKANT), h - V_GLAS[2] - V_GLAS[3] + 2 * RUTKANT
    m.lagg(Del(f"Isolerruta 4-18-4-18-4 {_matt(gb, gh)}", isolerruta(b, h, V_GLAS), GLAS), Placering(), f"{kod}-GLAS")
    return m


def fast_karm(kod: str, b: float, h: float) -> Montage:
    """Elitfönster Original Alu 100 fast karm (61-37-F221): isolerrutan i karmen, glaslist av aluminium."""
    fals = _plus(F_GLAS, -FALS)
    m = Montage(kod, kod, f"Fast fönster Elitfönster Original Alu 100, karm {_matt(b, h)}")
    m.lagg(Del(f"Karm fast fönster {_matt(b, h)}", _karm(b, h, F_GLAS, RUTA[0][0], fals, fals[2]), FONSTERTRA,
               artikel=f"Elitfönster Original Alu 100 fast karm, karm {_matt(b, h)}"), Placering(), f"{kod}-KARM")
    alu = ram(b, h, [(TRA, NOLL), (TRA, fals), (RUTA[-1][1], fals), (RUTA[-1][1], F_GLAS),
                     (DJUP, _plus(F_GLAS, -13.0)), (DJUP, NOLL)])
    m.lagg(Del(f"Karmbeklädnad med glaslist aluminium {_matt(b, h)}", alu, FONSTERALU), Placering(), f"{kod}-KARMALU")
    m.lagg(Del(f"Isolerruta 4-18-4-18-4 {_matt(b - 2 * (F_GLAS[0] - RUTKANT), h - 2 * (F_GLAS[0] - RUTKANT))}",
               isolerruta(b, h, F_GLAS), GLAS), Placering(), f"{kod}-GLAS")
    return m


def _dorrkarm(m: Montage, kod: str, b: float, h: float, vad: str, artikel: str) -> None:
    """Dörrens karm med tröskeln (42) som bottenstycke, beklädnaden och tröskelns aluminiumprofil."""
    m.lagg(Del(f"Karm {vad} {_matt(b, h)}", _karm(b, h, D_LAPP, LAPP, D_STOMME, D_BOTTEN), FONSTERTRA,
               artikel=artikel), Placering(), f"{kod}-KARM")
    m.lagg(Del(f"Karmbeklädnad aluminium {_matt(b, h)}", _karm_alu(b, h, D_STOMME, D_BOTTEN), FONSTERALU),
           Placering(), f"{kod}-KARMALU")
    m.lagg(Del(f"Tröskelprofil aluminium {fmt(b)}", _bottenprofil(b, D_STOMME, D_STOMME[2], D_BOTTEN, 8.0),
               FONSTERALU), Placering(), f"{kod}-BOTTEN")


def fonsterdorr(kod: str, b: float, h: float) -> Montage:
    """Elitfönster Original Alu 100 altandörr, helglasad (61-37-D221), som linjerar med vridfönstren."""
    m = Montage(kod, kod, f"Fönsterdörr helglasad Elitfönster Original Alu 100, karm {_matt(b, h)}")
    _dorrkarm(m, kod, b, h, "fönsterdörr", f"Elitfönster Original Alu 100 altandörr helglasad, karm {_matt(b, h)}")
    m.lagg(Del(f"Dörrbåge {_matt(b, h)}", _bage(b, h, D_BAGE, D_GLAS), FONSTERTRA), Placering(), f"{kod}-BAGE")
    m.lagg(Del(f"Bågbeklädnad aluminium {_matt(b, h)}", _bage_alu(b, h, D_BAGE, D_GLAS), FONSTERALU), Placering(),
           f"{kod}-BAGEALU")
    gb, gh = b - 2 * (D_GLAS[0] - RUTKANT), h - D_GLAS[2] - D_GLAS[3] + 2 * RUTKANT
    m.lagg(Del(f"Isolerruta 4-18-4-18-4 {_matt(gb, gh)}", isolerruta(b, h, D_GLAS), GLAS), Placering(), f"{kod}-GLAS")
    return m


def ytterdorr(kod: str, b: float, h: float) -> Montage:
    """Ytterdörr (huvudentrén): dörrkarmen som fönsterdörrens och ett tätt dörrblad i bågens kontur."""
    m = Montage(kod, kod, f"Ytterdörr, karm {_matt(b, h)}")
    _dorrkarm(m, kod, b, h, "ytterdörr", f"Ytterdörr, karm {_matt(b, h)}")
    v, hg, u, o = D_BAGE
    m.lagg(Del(f"Dörrblad {_matt(b - v - hg, h - u - o)}×{fmt(D_BLAD)}",
               box(v, b - hg, -BAGE_IN - D_BLAD, -BAGE_IN, u, h - o), DORRBLAD), Placering(), f"{kod}-BLAD")
    return m


# ------------------------------------------------------------------ skjutdörr (lyftglid) med fyra delar
S_TRA, S_DJUP = 153.0, 165.0           # karmens trä och hela djup
S_SIDA, S_TOPP, S_TROSKEL = 43.0, 47.5, 23.0
S_TROSKEL_UT = (150.0, 160.0, 8.0)     # tröskelns fas utåt: från d, till d, höjd vid ytterkanten
S_FAST = (-26.0, 44.0, 52.0)           # fasta delarna: insida, träets och aluminiumets yttersida (d)
S_SKJUT = (80.0, 150.0, 160.0)         # skjutbara delarna
S_GLAS = (131.2, 175.9, 161.2)         # glaskanten från karmens ytterkant: sidorna, upptill, nedtill
S_MITT, S_MOTE = 219.8, 102.0          # mellan glasen: de skjutbara delarna i mitten, en fast och en skjutbar
S_STIL_FAST, S_STIL_SKJUT = 90.0, 100.0   # stilarnas bredd där en fast och en skjutbar del möts
S_RUTA = ((0.0, 4.0), (20.0, 24.0), (40.0, 44.0))   # 4-16-4-16-4 från rutans insida


def _skjutdel(x0: float, x1: float, z0: float, z1: float, glas: Sidor, djup: tuple[float, float, float],
              namn: str, kod: str, m: Montage) -> None:
    """En del (fast eller skjutbar): bågen i trä med spår för isolerrutan, aluminium utanpå och rutan."""
    b, h = x1 - x0, z1 - z0
    d_in, d_tra, d_alu = djup
    g0 = (d_in + d_tra) / 2 - S_RUTA[-1][1] / 2
    g1 = g0 + S_RUTA[-1][1]
    spar = _plus(glas, -RUTKANT)
    plac = Placering.flytt(x0, 0.0, z0)
    bage = ram(b, h, [(d_in, NOLL), (d_in, glas), (g0, glas), (g0, spar), (g1, spar), (g1, glas), (d_tra, glas),
                     (d_tra, NOLL)])
    m.lagg(Del(f"Båge skjutdörr {_matt(b, h)}", bage, FONSTERTRA), plac, f"{kod}-{namn}-BAGE")
    m.lagg(Del(f"Bågbeklädnad aluminium {_matt(b, h)}", ram(b, h, [(d_tra, NOLL), (d_tra, glas), (d_alu, glas),
                                                                   (d_alu, NOLL)]), FONSTERALU),
           plac, f"{kod}-{namn}-BAGEALU")
    ruta = tuple((g0 + a, g0 + c) for a, c in S_RUTA)
    gb, gh = b - glas[0] - glas[1] + 2 * RUTKANT, h - glas[2] - glas[3] + 2 * RUTKANT
    m.lagg(Del(f"Isolerruta 4-16-4-16-4 {_matt(gb, gh)}", isolerruta(b, h, glas, ruta), GLAS), plac,
           f"{kod}-{namn}-GLAS")


def skjutdorr(kod: str, b: float, h: float) -> Montage:
    """Elitfönster Skjutdörr Alu ASP4 (86-37-04): fasta delar vid sidorna i det inre spåret och två skjutbara delar i
    mitten i det yttre, som öppnas åt sidorna utanför de fasta. Rutorna är lika breda."""
    m = Montage(kod, kod, f"Skjutdörr Elitfönster Alu ASP4 (lyftglid, 2 skjutbara och 2 fasta delar), "
                          f"karm {_matt(b, h)}")
    zt = h - S_TOPP
    karm = Union((box(0.0, S_SIDA, -S_TRA, 0.0, S_TROSKEL, h), box(b - S_SIDA, b, -S_TRA, 0.0, S_TROSKEL, h),
                  box(S_SIDA, b - S_SIDA, -S_TRA, 0.0, zt, h)))
    m.lagg(Del(f"Karm skjutdörr {_matt(b, h)}", karm, FONSTERTRA,
               artikel=f"Elitfönster Skjutdörr Alu ASP4, karm {_matt(b, h)}"), Placering(), f"{kod}-KARM")
    alu = Union((box(0.0, S_SIDA, -S_DJUP, -S_TRA, S_TROSKEL, h), box(b - S_SIDA, b, -S_DJUP, -S_TRA, S_TROSKEL, h),
                 box(S_SIDA, b - S_SIDA, -S_DJUP, -S_TRA, zt, h)))
    m.lagg(Del(f"Karmbeklädnad aluminium {_matt(b, h)}", alu, FONSTERALU), Placering(), f"{kod}-KARMALU")
    d0, d1, z_ut = S_TROSKEL_UT
    troskel = [(-S_FAST[0], 0.0), (-d1, 0.0), (-d1, z_ut), (-d0, S_TROSKEL), (-S_FAST[0], S_TROSKEL)]
    m.lagg(Del(f"Tröskel hårdträ {fmt(b)}", prisma_x(troskel, 0.0, b), HARDTRA), Placering(), f"{kod}-TROSKEL")
    gs, gt, gu = S_GLAS
    g = (b - 2 * gs - 2 * S_MOTE - S_MITT) / 4                 # rutornas synliga bredd
    z0 = S_TROSKEL
    for sida, spegel in (("V", False), ("H", True)):
        def x(v: float) -> float:
            return b - v if spegel else v
        fx0, fx1 = sorted((x(S_SIDA), x(gs + g + S_STIL_FAST)))
        sx0, sx1 = sorted((x(gs + g + S_MOTE - S_STIL_SKJUT), x(b / 2)))
        glas_fast = (gs - S_SIDA, S_STIL_FAST, gu - z0, gt - S_TOPP)
        glas_skjut = (S_STIL_SKJUT, S_MITT / 2, gu - z0, gt - S_TOPP)
        if spegel:
            glas_fast = (glas_fast[1], glas_fast[0], glas_fast[2], glas_fast[3])
            glas_skjut = (glas_skjut[1], glas_skjut[0], glas_skjut[2], glas_skjut[3])
        _skjutdel(fx0, fx1, z0, zt, glas_fast, S_FAST, f"F{sida}", kod, m)
        _skjutdel(sx0, sx1, z0, zt, glas_skjut, S_SKJUT, f"S{sida}", kod, m)
    return m


PRODUKTER: dict[str, tuple[Callable[[str, float, float], Montage], float]] = {
    "vridfönster": (vridfonster, DJUP), "fast fönster": (fast_karm, DJUP), "fönsterdörr": (fonsterdorr, DJUP),
    "ytterdörr": (ytterdorr, DJUP), "skjutdörr": (skjutdorr, S_DJUP)}
