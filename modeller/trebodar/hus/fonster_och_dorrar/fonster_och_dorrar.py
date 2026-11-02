"""Fönster och dörrar: Elitfönsters produkter (byggdelar/fonster.py) i ytterväggarnas öppningar och innerdörrarna
(skjutdörrar utanpå väggen eller fickdörrar i väggen, planritning 201 rev 02). Öppningarna och produkttyperna står i
oppningar.py.

Karmen sitter med aluminiumbeklädnaden i panelens utsida (w −65) och 10 mm drevmån runt om i regelverkets öppning
(modulmåttet), drevad med mineralull. Fasaden går fram till karmen (fasad.py). Invändigt: smygbrädor 15 mm av
vitmålad furu från karmen till väggens yta och fönsterbänk 22 mm med 20 mm utstick och öron 30 mm (dörrarna har
ingen); i badrummet kakel runt om. Källarens fönster sitter i cellplastens smyg; smygens och bröstningens gips hör
till källarväggarnas insida (invandigt/kallare.py).
"""
from __future__ import annotations

from modellering import Del, Montage, Placering, box

from trebodar import skelett as S
from trebodar.byggdelar import fonster as F
from trebodar.byggdelar.virke import fmt
from trebodar.hus.fasad.fasad import ALUMINIUM
from trebodar.hus.invandigt.invandigt import INSIDA_VATRUM_T, SKIVOR_T, _insida_t
from trebodar.material import FONSTERTRA, FURU, KAKEL, KARM, MINERALULL

from .oppningar import DORRAR, FICKA_UT, INNERDORRAR, OPPNINGAR, Innerdorr, Oppning

W_UT = -S.T_FASAD                    # karmens utsida i panelens utsida
SMYG_T, BANK_T = 15.0, 22.0          # smygbrädor och fönsterbänk
BANK_UT, BANK_ORA = 20.0, 30.0       # fönsterbänkens utstick från väggen och öron förbi öppningen
KAKEL_T = 12.0                       # badrummets smyg (kakel på skiva, förenklat)


def enhet(o: Oppning) -> Montage:
    """Produkten i öppningen med drevning, smyg och fönsterbänk, i väggens system."""
    funktion, djup = F.PRODUKTER[o.typ]
    b, h = o.bredd - 2 * F.DREV, o.hojd - 2 * F.DREV
    w_karm = W_UT + djup                                 # karmens insida
    m = Montage(o.kod, o.kod, f"{o.typ.capitalize()} {fmt(o.bredd)}×{fmt(o.hojd)} (modul)" +
                (f" ({o.onshape} i Onshape)" if o.onshape else ""))
    plac = Placering.flytt(o.u0 + F.DREV, w_karm, o.z0 + F.DREV)
    for i in funktion(o.kod, b, h, ALUMINIUM[int(o.vagg[0])]).barn:
        m.lagg(i.barn, plac @ i.placering, i.namn)
    drev = box(o.u0, o.u1, 0.0, w_karm, o.z0, o.z1) - box(o.u0 + F.DREV, o.u1 - F.DREV, -1.0, w_karm + 1.0,
                                                          o.z0 + F.DREV, o.z1 - F.DREV)
    m.lagg(Del(f"Drevning {fmt(o.bredd)}×{fmt(o.hojd)}", drev, MINERALULL), Placering(), f"{o.kod}-DREV")
    if o.z1 <= 0.0:                                      # källaren: gipsen i invandigt/kallare.py
        return m
    t = _insida_t(o.vagg, (o.u0 + o.u1) / 2)
    w_yta = S.T_STOMME + t                               # väggens insida
    u0, u1, z0, z1 = o.u0, o.u1, o.z0, o.z1
    if t == INSIDA_VATRUM_T:
        k = KAKEL_T
        for namn, f in (("V", box(u0, u0 + k, w_karm, w_yta, z0, z1)), ("H", box(u1 - k, u1, w_karm, w_yta, z0, z1)),
                        ("U", box(u0 + k, u1 - k, w_karm, w_yta, z0, z0 + k)),
                        ("O", box(u0 + k, u1 - k, w_karm, w_yta, z1 - k, z1))):
            m.lagg(Del(f"Smyg kakel {fmt(w_yta - w_karm)}", f, KAKEL), Placering(), f"{o.kod}-SMYG-{namn}")
        return m
    # smygbrädorna står på fönsterbänken, vid dörrarna på golvet och vid skjutdörren på tröskeln, som går in i rummet
    zb = z0 + (BANK_T if o.typ not in DORRAR else F.DREV + F.S_TROSKEL if o.typ == "skjutdörr" else 0.0)
    if o.typ not in DORRAR:
        bank = box(u0, u1, w_karm, w_yta, z0, z0 + BANK_T) | box(u0 - BANK_ORA, u1 + BANK_ORA, w_yta, w_yta + BANK_UT,
                                                                 z0, z0 + BANK_T)
        m.lagg(Del(f"Fönsterbänk {fmt(o.bredd + 2 * BANK_ORA)}×{fmt(w_yta - w_karm + BANK_UT)}×{fmt(BANK_T)}", bank,
                   FONSTERTRA), Placering(), f"{o.kod}-BANK")
    d = w_yta - w_karm
    for namn, f in (("V", box(u0, u0 + SMYG_T, w_karm, w_yta, zb, z1)),
                    ("H", box(u1 - SMYG_T, u1, w_karm, w_yta, zb, z1)),
                    ("O", box(u0 + SMYG_T, u1 - SMYG_T, w_karm, w_yta, z1 - SMYG_T, z1))):
        m.lagg(Del(f"Smygbräda {fmt(d)}×{fmt(SMYG_T)}", f, FONSTERTRA), Placering(), f"{o.kod}-SMYG-{namn}")
    return m


SKJUT_T, SKJUT_GLAPP, OVERLAPP = 40.0, 10.0, 30.0       # skjutdörrens blad, avståndet till väggens skikt


def fickdorr(d: Innerdorr) -> tuple[Montage, Placering]:
    """Fickdörren i väggen, stängd: bladet mitt i väggens stomme (fickan, invandigt/vaggar.py) täcker öppningen och
    går FICKA_UT in i fickan; skenan under överstycket över öppningen och fickan."""
    from trebodar.hus.invandigt.vaggar import FICKA_SKENA, vaggdef
    v = vaggdef(d.vagg)
    wm = v.tjocklek / 2
    a, b = d.fickan
    ba, bb = (d.u0, d.u1 + FICKA_UT) if d.mot > 0 else (d.u0 - FICKA_UT, d.u1)
    m = Montage(d.kod, d.kod, f"Fickdörr {fmt(d.bredd)}×{fmt(d.hojd)}, {d.rum}")
    m.lagg(Del(f"Dörrblad trä {fmt(bb - ba)}×{fmt(d.hojd)}", box(ba, bb, wm - SKJUT_T / 2, wm + SKJUT_T / 2, 10.0,
                                                                   d.hojd + 10.0), FURU), Placering(), f"{d.kod}-BLAD")
    u0, u1 = min(d.u0, a), max(d.u1, b)
    m.lagg(Del(f"Skena fickdörr {fmt(u1 - u0)}", box(u0, u1, wm - 10.0, wm + 10.0, d.hojd + 10.0, d.hojd + FICKA_SKENA),
               KARM), Placering(), f"{d.kod}-SKENA")
    return m, v.placering()


def skjutdorr(d: Innerdorr) -> tuple[Montage, Placering]:
    """Skjutdörren utanpå väggen, stängd: bladet täcker öppningen och skenan går en dörrbredd till åt det håll dörren
    öppnas, men inte in över en annan dörr på samma sida av väggen."""
    from trebodar.hus.invandigt.vaggar import skiktets_tjocklek, vaggdef
    if d.ficka:
        return fickdorr(d)
    v = vaggdef(d.vagg)
    t = skiktets_tjocklek(d.vagg, d.sida, (d.u0 + d.u1) / 2)
    yta = -t if d.sida < 0 else v.tjocklek + t                      # skiktets yta, skenan sitter på den
    wa, wb = sorted((yta + d.sida * SKJUT_GLAPP, yta + d.sida * (SKJUT_GLAPP + SKJUT_T)))
    sa, sb = sorted((yta, yta + d.sida * (2 * SKJUT_GLAPP + SKJUT_T)))
    a, b = d.u0 - d.fore, d.u1 + d.efter
    grannar = [(o.u0 - o.fore, o.u1 + o.efter) for o in INNERDORRAR
               if o.vagg == d.vagg and o.sida == d.sida and o != d and not o.ficka]
    if d.mot > 0:
        s0, s1 = a, min([b + d.bredd] + [g0 - 10.0 for g0, _ in grannar if g0 >= b])
    else:
        s0, s1 = max([a - d.bredd] + [g1 + 10.0 for _, g1 in grannar if g1 <= a]), b
    s0, s1 = max(s0, min(a, SKIVOR_T + 10.0)), min(s1, max(b, v.langd - SKIVOR_T - 10.0))     # inte förbi grannväggarna
    m = Montage(d.kod, d.kod, f"Skjutdörr {fmt(d.bredd)}×{fmt(d.hojd)}, {d.rum}")
    m.lagg(Del(f"Dörrblad trä {fmt(b - a)}×{fmt(d.hojd + 30)}", box(a, b, wa, wb, 10.0, d.hojd + 40.0), FURU),
           Placering(), f"{d.kod}-BLAD")
    m.lagg(Del(f"Skena {fmt(s1 - s0)}", box(s0, s1, sa, sb, d.hojd + 40.0, d.hojd + 80.0), KARM), Placering(),
           f"{d.kod}-SKENA")
    return m, v.placering()


def montage() -> Montage:
    m = Montage("Fönster och dörrar", beskrivning="Fönster och ytterdörrar (Elitfönster) och innerdörrar")
    ytter = Montage("Ytterväggarnas fönster och dörrar")
    for kod, lst in OPPNINGAR.items():
        for o in lst:
            ytter.lagg(enhet(o), S.YTTERVAGGAR[kod].placering())
    m.lagg(ytter)
    inner = Montage("Innerdörrar", beskrivning="Skjutdörrar (planritning 201 rev 02)")
    for d in INNERDORRAR:
        inner.lagg(*skjutdorr(d))
    m.lagg(inner)
    return m
