"""Fönster och dörrar: Elitfönsters produkter (byggdelar/fonster.py) i ytterväggarnas öppningar och innerdörrarna
(skjutdörrar utanpå väggen eller fickdörrar i väggen, planritning 201 rev 02). Öppningarna och produkttyperna står i
oppningar.py.

Karmen sitter INDRAG (22 mm) innanför panelens utsida, med aluminiumbeklädnaden i panelens insida (w −43), och
10 mm drevmån runt om i regelverkets öppning (modulmåttet), drevad med mineralull. Fasaden går fram till karmen och
panelen 10 mm in över den vid sidorna och överkanten (fasad.py); under fönstren leder ett fönsterbleck i karmens
aluminium vattnet ut över panelen. Invändigt går väggens skikt fram till karmens linje (vagginsida.py) och smygen är
av oljad ask 20 mm i liv med karmens kant, med fibrerna längs varje bit: sidorna, överstycket och fönsterbänken med
20 mm utstick och öron 30 mm (dörrarna har ingen); i badrummet kakel runt om. Källarens fönster sitter i
cellplastens smyg; smygens och bröstningens gips hör till källarväggarnas insida (invandigt/kallare.py).
"""
from __future__ import annotations

from modellering import Del, Montage, Placering, box, prisma

from trebodar import skelett as S
from trebodar.byggdelar import fonster as F
from trebodar.byggdelar.virke import fmt, virke_i_lada, virke_profil
from trebodar.hus.invandigt.skikt import INSIDA_VATRUM_T, SKIVOR_T, insida_t
from trebodar.hus.invandigt.vaggar import FICKA_SKENA, skiktets_tjocklek, vaggdef
from trebodar.material import ALUMINIUM, ASK, FURU, KAKEL, KARM, MINERALULL

from .oppningar import BLECK_T, DORRAR, FICKA_UT, INDRAG, INNERDORRAR, OPPNINGAR, Innerdorr, Oppning

W_UT = -S.T_FASAD + INDRAG           # karmens utsida
SMYG_T, BANK_T = 20.0, 20.0          # smygen och fönsterbänken, ask
BLECK_UT, BLECK_FALL = 30.0, 8.0     # fönsterblecket: utstick från panelen och fall utåt
BLECK_NAS = 14.0                     # droppnäsan nedåt
BANK_UT, BANK_ORA = 20.0, 30.0       # fönsterbänkens utstick från väggen och öron förbi öppningen
KAKEL_T = 12.0                       # badrummets smyg (kakel på skiva, förenklat)
SKJUT_T, SKJUT_GLAPP = 40.0, 10.0   # skjutdörrens blad och dess avstånd till väggens skikt


def enhet(o: Oppning) -> Montage:
    """Produkten i öppningen med drevning, smyg och fönsterbänk, i väggens system."""
    funktion, djup = F.PRODUKTER[o.typ]
    b, h = o.bredd - 2 * F.DREV, o.hojd - 2 * F.DREV
    w_ut = W_UT if o.z1 > 0.0 else -S.T_FASAD            # källarens fönster i cellplastens smyg som förut
    w_karm = w_ut + djup                                 # karmens insida
    m = Montage(o.kod, o.kod, f"{o.typ.capitalize()} {fmt(o.bredd)}×{fmt(o.hojd)} (modul)" +
                (f" ({o.onshape} i Onshape)" if o.onshape else ""))
    plac = Placering.flytt(o.u0 + F.DREV, w_karm, o.z0 + F.DREV)
    for i in funktion(o.kod, b, h, ALUMINIUM[int(o.vagg[0])]).barn:
        m.lagg(i.barn, plac @ i.placering, i.namn)
    # drevningen i regelverket; där karmen går längre in (skjutdörren) går insidans skikt fram till den
    w_drev = min(w_karm, S.T_STOMME)
    drev = box(o.u0, o.u1, 0.0, w_drev, o.z0, o.z1) - box(o.u0 + F.DREV, o.u1 - F.DREV, -1.0, w_drev + 1.0,
                                                          o.z0 + F.DREV, o.z1 - F.DREV)
    m.lagg(Del(f"Drevning {fmt(o.bredd)}×{fmt(o.hojd)}", drev, MINERALULL), Placering(), f"{o.kod}-DREV")
    if o.z1 <= 0.0:                                      # källaren: gipsen i invandigt/kallare.py
        return m
    ku0, kz0, ku1, kz1 = o.karm
    if o.typ not in DORRAR:
        m.lagg(*_fonsterbleck(o, ku1 - ku0), f"{o.kod}-BLECK")
    t = insida_t(o.vagg, (o.u0 + o.u1) / 2)
    w_yta = S.T_STOMME + t                               # väggens insida
    if t == INSIDA_VATRUM_T:
        k = KAKEL_T
        for namn, f in (("V", box(ku0, ku0 + k, w_karm, w_yta, kz0, kz1)),
                        ("H", box(ku1 - k, ku1, w_karm, w_yta, kz0, kz1)),
                        ("U", box(ku0 + k, ku1 - k, w_karm, w_yta, kz0, kz0 + k)),
                        ("O", box(ku0 + k, ku1 - k, w_karm, w_yta, kz1 - k, kz1))):
            m.lagg(Del(f"Smyg kakel {fmt(w_yta - w_karm)}", f, KAKEL), Placering(), f"{o.kod}-SMYG-{namn}")
        return m
    # smygen i karmens linje, inom karmens yttermått: sidorna står på fönsterbänken, vid dörrarna på golvet och vid
    # skjutdörren på tröskeln, som går in i rummet; överstycket går över sidorna
    zb = kz0 + (BANK_T if o.typ not in DORRAR else F.S_TROSKEL if o.typ == "skjutdörr" else -F.DREV)
    if o.typ not in DORRAR:
        bank = [(ku0, w_karm), (ku1, w_karm), (ku1, w_yta), (ku1 + BANK_ORA, w_yta), (ku1 + BANK_ORA, w_yta + BANK_UT),
                (ku0 - BANK_ORA, w_yta + BANK_UT), (ku0 - BANK_ORA, w_yta), (ku0, w_yta)]
        d, pl = virke_profil(bank, BANK_T, ASK, prefix="Fönsterbänk ")
        m.lagg(d, Placering.flytt(0.0, 0.0, kz0) @ pl, f"{o.kod}-BANK")
    for namn, (u0, u1, z0, z1, fiber) in (("V", (ku0, ku0 + SMYG_T, zb, kz1 - SMYG_T, "z")),
                                          ("H", (ku1 - SMYG_T, ku1, zb, kz1 - SMYG_T, "z")),
                                          ("O", (ku0, ku1, kz1 - SMYG_T, kz1, "x"))):
        d, pl = virke_i_lada(u0, u1, w_karm, w_yta, z0, z1, fiber, ASK)
        m.lagg(d, pl, f"{o.kod}-SMYG-{namn}")
    return m


def _fonsterbleck(o: Oppning, langd: float) -> tuple[Del, Placering]:
    """Fönsterblecket under karmen, i karmens aluminium: under karmens utsida över spikläkten, med fall ut över
    panelen och droppnäsa BLECK_UT utanför den; profilen (w, z) från karmens underkant, längs karmens bredd."""
    _, kz0, _, _ = o.karm
    w_in, w_ut = W_UT + 21.0, -S.T_FASAD - BLECK_UT      # spikläktens djup under karmen, droppnäsans utsida
    t, fall = BLECK_T, BLECK_FALL
    z_in = -t - fall * (W_UT - (w_ut + t)) / (W_UT - w_ut)      # undersidan vid droppnäsans insida
    profil = [(w_in, 0.0), (W_UT, 0.0), (w_ut, -fall), (w_ut, -fall - BLECK_NAS), (w_ut + t, -fall - BLECK_NAS),
              (w_ut + t, z_in), (W_UT, -t), (w_in, -t)]
    # profilen i lokala (x, y) = (w, z), utdragen längs lokala z = väggens u
    plac = Placering(((0.0, 0.0, 1.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)), (o.karm[0], 0.0, kz0))
    return Del(f"Fönsterbleck {fmt(langd)}", prisma(profil, langd), ALUMINIUM[int(o.vagg[0])],
               "Fönsterbleck i karmens aluminium, med fall och droppnäsa"), plac



def fickdorr(d: Innerdorr) -> tuple[Montage, Placering]:
    """Fickdörren i väggen, stängd: bladet mitt i väggens stomme (fickan, invandigt/vaggar.py) täcker öppningen och
    går FICKA_UT in i fickan; skenan under överstycket över öppningen och fickan."""
    v = vaggdef(d.vagg)
    wm = v.tjocklek / 2
    a, b = d.fickan
    ba, bb = (d.u0, d.u1 + FICKA_UT) if d.mot > 0 else (d.u0 - FICKA_UT, d.u1)
    m = Montage(d.kod, d.kod, f"Fickdörr {fmt(d.bredd)}×{fmt(d.hojd)}, {d.rum}")
    blad, pl = virke_i_lada(ba, bb, wm - SKJUT_T / 2, wm + SKJUT_T / 2, 10.0, d.hojd + 10.0, "z", FURU)
    m.lagg(Del(f"Dörrblad trä {fmt(bb - ba)}×{fmt(d.hojd)}", blad.form, FURU), pl, f"{d.kod}-BLAD")
    u0, u1 = min(d.u0, a), max(d.u1, b)
    m.lagg(Del(f"Skena fickdörr {fmt(u1 - u0)}", box(u0, u1, wm - 10.0, wm + 10.0, d.hojd + 10.0, d.hojd + FICKA_SKENA),
               KARM), Placering(), f"{d.kod}-SKENA")
    return m, v.placering()


def skjutdorr(d: Innerdorr) -> tuple[Montage, Placering]:
    """Skjutdörren utanpå väggen, stängd: bladet täcker öppningen och skenan går en dörrbredd till åt det håll dörren
    öppnas, men inte in över en annan dörr på samma sida av väggen."""
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
