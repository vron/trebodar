"""Ytterdörrarna med panel (huvudentrén och källarens pardörr), parametriska efter Elitfönsters snittritning för
altandörren (Original Alu 100, 61-37-D221): karm med tröskel och aluminiumbeklädnad och blad med stående panel, med de
synliga måtten exakta, i produktens eget system, så att en dörr kan sättas i vilken öppning som helst och ändras för
sig. Fönstren och fönsterdörrarna är från VELFAC (byggdelar/velfac.py).

Produktens system: x längs bredden från karmens ytterkant, z uppåt från karmens underkant och y genom väggen med
y = 0 i karmens insida och negativt utåt (som väggarnas w). Bredden och höjden är karmens yttermått, öppningens mått
− 20 (DREV runt om). Profilerna anges med d utåt från karmens insida och avstånd inåt från karmens ytterkant per sida
(vänster, höger, under, över).

Karmen: djup 115 (trä 105 och aluminium 10), 52 bred vid sidorna och 53,5 upptill, tröskel 42 med aluminiumprofil och
droppnäsa.
"""
from __future__ import annotations

import math

from collections.abc import Callable, Sequence

from modellering import Del, Form, Material, Montage, Placering, Union, box, polyeder

from trebodar.byggdelar.polygon import prisma_x
from trebodar.byggdelar.virke import fmt, virke_i_lada
from trebodar.material import C24_LAKT, DORRBLAD, FONSTERTRA

Sidor = tuple[float, float, float, float]          # vänster, höger, under, över
Profil = Sequence[tuple[float, Sidor]]             # (d, sidor) runt en sluten polygon

DREV = 10.0                 # drevmån runt karmen
TRA, DJUP = 105.0, 115.0    # karmens trä och hela djup med aluminiumbeklädnaden
LAPP = 24.0                 # karmens läpp inifrån (med tätningslisten), bladet ligger an mot den
BAGE_IN = 24.0              # bladets insida (d)


def _alla(v: float) -> Sidor:
    return (v, v, v, v)


NOLL = _alla(0.0)


def ram(b: float, h: float, profil: Profil) -> Form:
    """Rektangulär ram (karm, beklädnad) med gering i hörnen: profilen svept runt bredden b och höjden h.
    Sidorna kan ha olika profil men lika många punkter; ytorna mellan två punkter är plana."""
    horn: list[tuple[float, float, float]] = []
    for d, (v, hg, u, o) in profil:
        horn += [(v, -d, u), (b - hg, -d, u), (b - hg, -d, h - o), (v, -d, h - o)]
    n = len(profil)
    ytor = [[4 * i + k, 4 * i + (k + 1) % 4, 4 * ((i + 1) % n) + (k + 1) % 4, 4 * ((i + 1) % n) + k]
            for i in range(n) for k in range(4)]
    return polyeder(horn, ytor)


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


def _matt(b: float, h: float) -> str:
    return f"{fmt(b)}×{fmt(h)}"


# ------------------------------------------------------------------ dörrarna
D_LAPP, D_STOMME, D_BOTTEN = (52.0, 52.0, 42.0, 53.5), (37.5, 37.5, 28.0, 39.5), 20.5
D_BAGE = (41.0, 41.0, 31.0, 41.5)                  # bladets ytterkant
# ytterdörrarnas blad (ärende #33): en kärna av plywood i karmen, liggande läkt och stående panel utanpå, i
# fasadpanelens plan (utanför karmen, som fasadpanelen) och över karmen fram till en fog mot panelen, som går
# PANEL_OVER in över karmen vid sidorna och upptill (hus/fasad): karmen syns inte utifrån, bara tröskeln
B_KARNA, B_PANEL = 44.0, 22.0
B_LAKT = DJUP - BAGE_IN - B_KARNA        # läkten fyller ut till karmens ytterkant
B_LAKT_B, B_LAKT_CC = 70.0, 400.0        # läkten: bredd och c/c (högst), nedtill och upptill på bladet
PANEL_OVER, B_FOG = 10.0, 4.0            # fasadpanelen över karmen och fogen mellan den och dörrens panel
P_HUVUD, P_MOTE = 900.0, 4.0             # pardörren: huvudbladet (till höger sett utifrån) och glipan mellan bladen


def _dorrkarm(m: Montage, kod: str, b: float, h: float, vad: str, artikel: str, alu: Material) -> None:
    """Dörrens karm med tröskeln (42) som bottenstycke, beklädnaden och tröskelns aluminiumprofil."""
    m.lagg(Del(f"Karm {vad} {_matt(b, h)}", _karm(b, h, D_LAPP, LAPP, D_STOMME, D_BOTTEN), FONSTERTRA,
               artikel=artikel), Placering(), f"{kod}-KARM")
    m.lagg(Del(f"Karmbeklädnad aluminium {_matt(b, h)}", _karm_alu(b, h, D_STOMME, D_BOTTEN), alu),
           Placering(), f"{kod}-KARMALU")
    m.lagg(Del(f"Tröskelprofil aluminium {fmt(b)}", _bottenprofil(b, D_STOMME, D_STOMME[2], D_BOTTEN, 8.0),
               alu), Placering(), f"{kod}-BOTTEN")


def _blad(m: Montage, kod: str, x0: float, x1: float, z0: float, z1: float, panel: Material, namn: str,
          px0: float, px1: float, pz1: float) -> None:
    """Ett ytterdörrblad: kärnan (x0–x1, z0–z1), liggande läkt (nedtill, upptill och c/c högst
    B_LAKT_CC) till karmens ytterkant och stående panel utanför karmen, från px0 till px1 och upp till pz1."""
    y = -BAGE_IN - B_KARNA
    m.lagg(Del(f"Dörrblad {_matt(x1 - x0, z1 - z0)}×{fmt(B_KARNA)}", box(x0, x1, y, -BAGE_IN, z0, z1), DORRBLAD),
           Placering(), f"{kod}-{namn}")
    n = max(1, math.ceil((z1 - z0 - B_LAKT_B) / B_LAKT_CC))
    for i in range(n + 1):
        z = z0 + i * (z1 - z0 - B_LAKT_B) / n
        d, pl = virke_i_lada(x0, x1, y - B_LAKT, y, z, z + B_LAKT_B, "x", C24_LAKT)
        m.lagg(d, pl, f"{kod}-{namn}-L{i + 1}")
    m.lagg(Del(f"{panel.namn.replace('Dörrpanel', 'Panel 22 mm')} {_matt(px1 - px0, pz1 - z0)}",
               box(px0, px1, -DJUP - B_PANEL, -DJUP, z0, pz1), panel), Placering(), f"{kod}-{namn}-PANEL")


def ytterdorr(kod: str, b: float, h: float, alu: Material, panel: Material) -> Montage:
    """Ytterdörr (huvudentrén): dörrkarmen och ett blad med panel."""
    m = Montage(kod, kod, f"Ytterdörr, karm {_matt(b, h)}")
    _dorrkarm(m, kod, b, h, "ytterdörr", f"Ytterdörr, karm {_matt(b, h)}", alu)
    v, hg, u, o = D_BAGE
    k = PANEL_OVER + B_FOG
    _blad(m, kod, v, b - hg, u, h - o, panel, "BLAD", k, b - k, h - k)
    return m


def pardorr(kod: str, b: float, h: float, alu: Material, panel: Material) -> Montage:
    """Pardörr (källaren): dörrkarmen som ytterdörrens och två blad med panel, huvudbladet P_HUVUD till höger sett
    utifrån (växande x) och ett smalare, som öppnas ibland, till vänster."""
    m = Montage(kod, kod, f"Pardörr, karm {_matt(b, h)}")
    _dorrkarm(m, kod, b, h, "pardörr", f"Pardörr, karm {_matt(b, h)}", alu)
    v, hg, u, o = D_BAGE
    k = PANEL_OVER + B_FOG
    xm = b - hg - P_HUVUD - P_MOTE / 2                     # mötet mellan bladen
    _blad(m, kod, v, xm - P_MOTE / 2, u, h - o, panel, "BLAD1", k, xm - P_MOTE / 2, h - k)
    _blad(m, kod, xm + P_MOTE / 2, b - hg, u, h - o, panel, "BLAD2", xm + P_MOTE / 2, b - k, h - k)
    return m


# produkterna med karmens djup; anropas med kod, bredd, höjd, aluminiumet och panelens material
PRODUKTER: dict[str, tuple[Callable[..., Montage], float]] = {"ytterdörr": (ytterdorr, DJUP), "pardörr": (pardorr, DJUP)}
