"""Fönster och dörrar: Elitfönsters produkter (byggdelar/fonster.py) i ytterväggarnas öppningar och innerdörrarna
(skjutdörrar utanpå väggen eller fickdörrar i väggen, planritning 201 rev 02). Öppningarna och produkttyperna står i
oppningar.py.

Karmen sitter INDRAG (22 mm) innanför panelens utsida, med aluminiumbeklädnaden i panelens insida (w −43), och
10 mm drevmån runt om i regelverkets öppning (modulmåttet), drevad med mineralull. Fasaden går fram till karmen och
panelen 10 mm in över den vid sidorna och överkanten (fasad.py); under fönstren leder ett fönsterbleck i karmens
aluminium vattnet ut över panelen. Invändigt går väggens skikt fram till karmens linje (vagginsida.py) och smygen är
av oljad ask 20 mm i liv med karmens kant, med fibrerna längs varje bit: sidorna, överstycket och fönsterbänken med
20 mm utstick och öron 30 mm (dörrarna har ingen); i badrummet kakel runt om. Med smyglister (oppningar.SMYGLIST > 0)
slutar insidans skivor längre från karmen och lister av ask i skivornas tjocklek går runt smygen, sidorna från
fönsterbänken (dörrarna från golvet) och överstycket över dem, och fönsterbänkens öron blir lika mycket längre. Källarens fönster
och dess ytterdörr D1 (en pardörr) sitter i cellplastens smyg; smygens och bröstningens gips hör till källarväggarnas
insida (invandigt/kallare.py). Ytterdörrarnas blad har stående panel i den andra kulören än fasaden runt dem
(material.DORRPANEL: grått i det röda huset och tvärtom); källardörren i granitsockeln har panel i järnvitriol
(material.DORRPANEL_KALLARE).

I varianten velfac (trebodar/variant.py) är fönstren och fönsterdörrarna från VELFAC (byggdelar/velfac.py), monterade
enligt VELFAC:s montageanvisning och träfasaddetaljer (enhet_velfac): aluminiumets utsida INDRAG_V (20 mm) innanför
panelens utsida, så att karmträet ligger i utegipsens utsida, fogen FOG_V (15 mm) mot regelverket med drevning och
lufttät fog inifrån, fönstren på en påföring 18×114 med fönsterblecket från påföringen, anslutningsprofilen på
karmen upptill och vid sidorna med plåtarna därifrån ut och upp bakom läkten (vid det vändbara fönstrets sidor
utanför beslagets zon) och fasaden KLADD_V (10 mm) från karmen. Invändigt samma smyg av ask i karmens linje, med
fönsterbänken under bottenkarmen (fönstren från golvet: en bräda från golvet till karmen) och dörrarnas smyg från
golvet.
"""
from __future__ import annotations

from shapely.geometry import LineString

from modellering import Del, Material, Montage, Placering, box, prisma

from trebodar import skelett as S
from trebodar.byggdelar import fonster as F
from trebodar.byggdelar.polygon import prisma_x
from trebodar.byggdelar.virke import fmt, virke_i_lada, virke_profil
from trebodar.hus.invandigt.skikt import INSIDA_VATRUM_T, SKIVOR_T, insida_t
from trebodar.hus.invandigt.vaggar import FICKA_SKENA, skiktets_tjocklek, vaggdef
from trebodar.byggdelar import velfac as V
from trebodar.material import (ALUMINIUM, ANSLUTNINGSPLAT, ASK, C24, DORRPANEL, DORRPANEL_KALLARE, FOGMASSA, FURU, KAKEL,
                               KARM, MINERALULL, TATNINGSLIST)

from .oppningar import (BANK_V, BLECK_NAS_V, BLECK_T, BLECK_UPP_V, BLECK_UT_V, DORRAR, FICKA_UT, FOG_V,
                        INDRAG, INDRAG_V, INNERDORRAR, KLADD_V, OPPNINGAR, PAFORING_V, SMYGLIST, W_TRA_V, Innerdorr,
                        Oppning, velfac_bleck_z)

W_UT = -S.T_FASAD + INDRAG           # karmens utsida
SMYG_T, BANK_T = 20.0, 20.0          # smygen och fönsterbänken, ask
BLECK_UT, BLECK_FALL = 30.0, 8.0     # fönsterblecket: utstick från panelen och fall utåt
BLECK_NAS = 14.0                     # droppnäsan nedåt
BANK_UT, BANK_ORA = 20.0, 30.0       # fönsterbänkens utstick från väggen och öron förbi öppningen
KAKEL_T = 12.0                       # badrummets smyg (kakel på skiva, förenklat)
SKJUT_T, SKJUT_GLAPP = 40.0, 10.0   # skjutdörrens blad och dess avstånd till väggens skikt
DORRSMYG_T = 22.0                    # fickdörrarnas smyg, ask
SLITS = SKJUT_T / 2 + 3.0            # halva slitsen för bladet i fickdörrarnas delade smyg


def enhet(o: Oppning) -> Montage:
    """Produkten i öppningen med drevning, smyg och fönsterbänk, i väggens system."""
    if o.velfac:
        return enhet_velfac(o)
    funktion, djup = F.PRODUKTER[o.typ]
    b, h = o.bredd - 2 * F.DREV, o.hojd - 2 * F.DREV
    # källarens fönster i cellplastens smyg som förut; dörrarna med panel som på plan 1 (panelen i fasadens plan)
    w_karm = o.w_karm                                    # karmens insida
    m = Montage(o.kod, o.kod, f"{o.typ.capitalize()} {fmt(o.bredd)}×{fmt(o.hojd)} (modul)" +
                (f" ({o.onshape} i Onshape)" if o.onshape else ""))
    plac = Placering.flytt(o.u0 + F.DREV, w_karm, o.z0 + F.DREV)
    kropp = int(o.vagg[0])
    panel = DORRPANEL_KALLARE if o.z1 <= 0.0 else DORRPANEL[kropp]
    produkt = (funktion(o.kod, b, h, ALUMINIUM[kropp], panel) if o.typ in F.MED_PANEL else
               funktion(o.kod, b, h, ALUMINIUM[kropp]))
    for i in produkt.barn:
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
        ora = BANK_ORA + SMYGLIST
        bank = [(ku0, w_karm), (ku1, w_karm), (ku1, w_yta), (ku1 + ora, w_yta), (ku1 + ora, w_yta + BANK_UT),
                (ku0 - ora, w_yta + BANK_UT), (ku0 - ora, w_yta), (ku0, w_yta)]
        d, pl = virke_profil(bank, BANK_T, ASK, prefix="Fönsterbänk ")
        m.lagg(d, Placering.flytt(0.0, 0.0, kz0) @ pl, f"{o.kod}-BANK")
    for namn, (u0, u1, z0, z1, fiber) in (("V", (ku0, ku0 + SMYG_T, zb, kz1 - SMYG_T, "z")),
                                          ("H", (ku1 - SMYG_T, ku1, zb, kz1 - SMYG_T, "z")),
                                          ("O", (ku0, ku1, kz1 - SMYG_T, kz1, "x"))):
        d, pl = virke_i_lada(u0, u1, w_karm, w_yta, z0, z1, fiber, ASK)
        m.lagg(d, pl, f"{o.kod}-SMYG-{namn}")
    if SMYGLIST > 0.0:
        # smyglisterna i skivornas tjocklek runt smygen (skivorna slutar vid dem, vagginsida.py): sidorna från
        # karmens underkant (bakom fönsterbänkens öron) eller golvet, överstycket över dem
        L, wl, zl = SMYGLIST, w_yta - SKIVOR_T, kz0 if o.typ not in DORRAR else o.z0
        for namn, (u0, u1, z0, z1, fiber) in (("V", (ku0 - L, ku0, zl, kz1, "z")), ("H", (ku1, ku1 + L, zl, kz1, "z")),
                                              ("O", (ku0 - L, ku1 + L, kz1, kz1 + L, "x"))):
            d, pl = virke_i_lada(u0, u1, wl, w_yta, z0, z1, fiber, ASK)
            m.lagg(Del(f"Smyglist ask {fmt(SKIVOR_T)}×{fmt(L)}", d.form, ASK), pl, f"{o.kod}-LIST-{namn}")
    return m


# VELFAC: drevningen och den lufttäta fogen i fogen mot regelverket (inifrån: fogen till regelns insida), den lufttäta
# fogen DREV_V till regelns insida; anslutningsprofilen 16×3,5 på karmen (d från aluminiumets utsida) och plåtarna 1 mm
# från den ut till utegipsens utsida och upp (vid sidorna ut) bakom läkten PLAT_UPP (PLAT_UT) förbi regelverket
DREV_V, FOGMASSA_V = (12.0, 75.0), (87.0, S.T_STOMME)
PROFIL_D, PLAT_T = (41.0, 57.0), 1.0
PLAT_UPP, PLAT_UT = 60.0, 45.0


def _plat(spar: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Plåtens tvärsnitt kring linjen (e, d): PLAT_T tjockt, med raka hörn."""
    g = LineString(spar).buffer(PLAT_T / 2, cap_style=2, join_style=2)
    return [(float(x), float(y)) for x, y in list(g.exterior.coords)[:-1]]


def _sida_v(kod: str, o: Oppning, sida: str, e0: float, e1: float, d0: float, d1: float, a0: float, a1: float,
            namn: str, mat: Material, del_namn: str, m: Montage, kontur: list[tuple[float, float]] | None = None) -> None:
    """En del längs en sida av VELFAC-karmen: tvärsnittet i (e, d) (e utåt negativt från karmens ytterkant, d från
    aluminiumets utsida), som rektangel (e0, e1, d0, d1) eller kontur, utdragen längs sidan från a0 till a1 (u upptill,
    z vid sidorna)."""
    ku0, kz0, ku1, kz1 = o.karm
    w_alu = -S.T_FASAD + INDRAG_V
    pts = kontur or [(e0, d0), (e1, d0), (e1, d1), (e0, d1)]
    if sida == "o":
        prof = [(w_alu + d, kz1 - e) for e, d in pts]
        f = prisma_x(prof, a0, a1)
    else:
        prof = [((ku0 + e) if sida == "v" else (ku1 - e), w_alu + d) for e, d in pts]
        f = prisma(prof, a1 - a0, z0=a0)
    m.lagg(Del(del_namn, f, mat), Placering(), f"{kod}-{namn}")


def enhet_velfac(o: Oppning) -> Montage:
    """VELFAC-produkten i öppningen med påföringen, fogen, anslutningarna (profilerna, plåtarna och fönsterblecket)
    och smygen och fönsterbänken av ask, i väggens system (se modulens beskrivning)."""
    kropp = int(o.vagg[0])
    alu = ALUMINIUM[kropp]
    ku0, kz0, ku1, kz1 = o.karm
    w_karm = o.w_karm                                    # karmens insida
    w_alu = w_karm - V.DJUP
    dorr = o.typ in DORRAR
    m = Montage(o.kod, o.kod, f"{o.typ.capitalize()} VELFAC {fmt(o.bredd)}×{fmt(o.hojd)} (regelöppning)" +
                (f" ({o.onshape} i Onshape)" if o.onshape else ""))
    plac = Placering.flytt(ku0, w_karm, kz0)
    for i in V.PRODUKTER[o.typ](o.kod, ku1 - ku0, kz1 - kz0, alu).barn:
        m.lagg(i.barn, plac @ i.placering, i.namn)
    # påföringen under fönstren, fogen runt om: drevning och lufttät fog
    karm = box(ku0, ku1, -1e3, 1e3, kz0 - (0.0 if dorr else PAFORING_V), kz1)
    if not dorr:
        m.lagg(Del(f"Påföring {fmt(PAFORING_V)}×{fmt(V.DJUP - V.TRA_UT)} {fmt(ku1 - ku0)}",
                   box(ku0, ku1, w_alu + V.TRA_UT, w_karm, kz0 - PAFORING_V, kz0), C24), Placering(), f"{o.kod}-PAF")
    for namn, (w0, w1), mat, vad in (("DREV", DREV_V, MINERALULL, "Drevning"), ("FOG", FOGMASSA_V, FOGMASSA, "Fog")):
        f = box(o.u0, o.u1, w0, w1, o.z0, o.z1) - karm
        m.lagg(Del(f"{vad} {fmt(o.bredd)}×{fmt(o.hojd)}", f, mat), Placering(), f"{o.kod}-{namn}")
    # anslutningsprofilen på karmen upptill och vid sidorna och plåtarna från den ut och upp (ut) bakom läkten
    sidor = V.SIDOR[o.typ]
    plat = ANSLUTNINGSPLAT[kropp]
    z_plat = kz0 if dorr else velfac_bleck_z(o, W_TRA_V) + BLECK_UPP_V
    for sida in ("o", "v", "h"):
        k = sidor[sida].kant                             # karmens yttersta e vid profilen
        ef = k - 3.5 / 2
        e2 = min(ef, V.ZON_G[0] - 1.2)                  # utanför det vändbara fönstrets beslagszon
        d_ug = V.TRA_UT - PLAT_T / 2                     # på utegipsens utsida
        langd = PLAT_UPP if sida == "o" else PLAT_UT
        spar = [(ef, PROFIL_D[0] - PLAT_T / 2), (e2, PROFIL_D[0] - PLAT_T / 2), (e2, d_ug)]
        delar: list[tuple[list[tuple[float, float]], float, float, str]]
        if sida == "o":                                  # i öppningen, och på utegipsen förbi sidoplåtarna
            a0, a1 = ku0, ku1
            ut = [(e2 + PLAT_T / 2, d_ug), (-FOG_V - langd, d_ug)]
            delar = [(spar[:-1] + [(e2, d_ug + PLAT_T / 2)], o.u0, o.u1, ""),
                     (ut, ku0 - FOG_V - PLAT_UT, ku1 + FOG_V + PLAT_UT, "U")]
        else:                                            # från fönsterblecket (dörrarna: karmen) till överplåten
            a0, a1 = kz0, kz1
            # till överplåten, men inte in i överkarmens lock (vändfönstrets sidor utan lock)
            topp = kz1 if k > sidor["o"].kant else kz1 - (sidor["o"].kant - 3.5 / 2) - PLAT_T / 2
            delar = [(spar + [(-FOG_V - langd, d_ug)], z_plat, topp, "")]
        _sida_v(o.kod, o, sida, k - 3.5, k, PROFIL_D[0], PROFIL_D[1], a0, a1, f"PROFIL-{sida.upper()}", TATNINGSLIST,
                f"Anslutningsprofil {fmt(a1 - a0)}", m)
        for linje, pa0, pa1, tillagg in delar:
            _sida_v(o.kod, o, sida, 0, 0, 0, 0, pa0, pa1, f"PLAT-{sida.upper()}{tillagg}", plat,
                    f"Anslutningsplåt {fmt(pa1 - pa0)}", m, _plat(linje))
    if not dorr:
        m.lagg(*_fonsterbleck_velfac(o), f"{o.kod}-BLECK")
    if o.z1 <= 0.0:                                      # källaren: smygens gips i invandigt/kallare.py
        return m
    # invändigt: smygen av ask i karmens linje och fönsterbänken under bottenkarmen
    t = insida_t(o.vagg, (o.u0 + o.u1) / 2)
    w_yta = S.T_STOMME + t
    _, zi, _, _ = o.inre
    if t == INSIDA_VATRUM_T:
        k = KAKEL_T
        for namn, f in (("V", box(ku0, ku0 + k, w_karm, w_yta, zi, kz1)), ("H", box(ku1 - k, ku1, w_karm, w_yta, zi, kz1)),
                        ("U", box(ku0 + k, ku1 - k, w_karm, w_yta, zi, max(zi + k, kz0))),
                        ("O", box(ku0 + k, ku1 - k, w_karm, w_yta, kz1 - k, kz1))):
            m.lagg(Del(f"Smyg kakel {fmt(w_yta - w_karm)}", f, KAKEL), Placering(), f"{o.kod}-SMYG-{namn}")
        return m
    if o.golvfonster:                                    # en bräda från golvet till karmen, i väggens yta
        d, pl = virke_i_lada(ku0, ku1, w_karm, w_yta, o.z0, kz0, "x", ASK)
        m.lagg(d, pl, f"{o.kod}-BANK")
    elif not dorr:
        ora = BANK_ORA + SMYGLIST
        bank = [(ku0, w_karm), (ku1, w_karm), (ku1, w_yta), (ku1 + ora, w_yta), (ku1 + ora, w_yta + BANK_UT),
                (ku0 - ora, w_yta + BANK_UT), (ku0 - ora, w_yta), (ku0, w_yta)]
        d, pl = virke_profil(bank, BANK_V, ASK, prefix="Fönsterbänk ")
        m.lagg(d, Placering.flytt(0.0, 0.0, kz0 - BANK_V) @ pl, f"{o.kod}-BANK")
    zb = o.z0 if dorr else kz0
    for namn, (u0, u1, z0, z1, fiber) in (("V", (ku0, ku0 + SMYG_T, zb, kz1 - SMYG_T, "z")),
                                          ("H", (ku1 - SMYG_T, ku1, zb, kz1 - SMYG_T, "z")),
                                          ("O", (ku0, ku1, kz1 - SMYG_T, kz1, "x"))):
        d, pl = virke_i_lada(u0, u1, w_karm, w_yta, z0, z1, fiber, ASK)
        m.lagg(d, pl, f"{o.kod}-SMYG-{namn}")
    if SMYGLIST > 0.0:
        L, wl = SMYGLIST, w_yta - SKIVOR_T
        for namn, (u0, u1, z0, z1, fiber) in (("V", (ku0 - L, ku0, zi, kz1, "z")), ("H", (ku1, ku1 + L, zi, kz1, "z")),
                                              ("O", (ku0 - L, ku1 + L, kz1, kz1 + L, "x"))):
            d, pl = virke_i_lada(u0, u1, wl, w_yta, z0, z1, fiber, ASK)
            m.lagg(Del(f"Smyglist ask {fmt(SKIVOR_T)}×{fmt(L)}", d.form, ASK), pl, f"{o.kod}-LIST-{namn}")
    return m


def _fonsterbleck_velfac(o: Oppning) -> tuple[Del, Placering]:
    """VELFAC-fönstrets bleck: uppvik BLECK_UPP_V mot påföringens utsida, fall utåt från påföringens underkant och
    droppnäsa BLECK_UT_V utanför panelen, mellan panelens kanter (KLADD_V utanför karmen); profilen (w, z)."""
    ku0, _, ku1, _ = o.karm
    t, w_in, w_ut = BLECK_T, W_TRA_V, -S.T_FASAD - BLECK_UT_V
    z_in = velfac_bleck_z(o, w_in)

    def z(w: float) -> float:
        return velfac_bleck_z(o, w)
    profil = [(w_in, z_in + BLECK_UPP_V), (w_in, z_in - t), (w_ut + t, z(w_ut + t) - t), (w_ut + t, z(w_ut) - BLECK_NAS_V),
              (w_ut, z(w_ut) - BLECK_NAS_V), (w_ut, z(w_ut)), (w_in - t, z(w_in - t)), (w_in - t, z_in + BLECK_UPP_V)]
    langd = ku1 - ku0 + 2 * KLADD_V
    return (Del(f"Fönsterbleck {fmt(langd)}", prisma_x(profil, ku0 - KLADD_V, ku1 + KLADD_V), ALUMINIUM[int(o.vagg[0])],
                "Fönsterbleck i karmens aluminium, med uppvik mot påföringen, fall och droppnäsa"), Placering())


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
    """Fickdörren i väggen, stängd: bladet mitt i väggens stomme (fickan, invandigt/vaggar.py) går FICKA_UT in i
    fickan; skenan under överstycket över öppningen och fickan. Öppningen har smyg av oljad ask DORRSMYG_T runt om
    utom vid golvet, genom hela väggen i liv med skivorna på båda sidor: hel på låssidan, där bladet stängs mot den, och
    delad vid fickan och i överstycket, med en slits för bladet; sidorna står på golvet och överstycket går över dem."""
    v = vaggdef(d.vagg)
    wm = v.tjocklek / 2
    a, b = d.fickan
    r = DORRSMYG_T
    ba, bb = (d.u0 + r, d.u1 + FICKA_UT + r) if d.mot > 0 else (d.u0 - FICKA_UT - r, d.u1 - r)
    m = Montage(d.kod, d.kod, f"Fickdörr {fmt(d.bredd)}×{fmt(d.hojd)}, {d.rum}")
    blad, pl = virke_i_lada(ba, bb, wm - SKJUT_T / 2, wm + SKJUT_T / 2, 10.0, d.hojd + 10.0, "z", FURU)
    m.lagg(Del(f"Dörrblad trä {fmt(bb - ba)}×{fmt(d.hojd)}", blad.form, FURU), pl, f"{d.kod}-BLAD")
    u0, u1 = min(d.u0, a), max(d.u1, b)
    m.lagg(Del(f"Skena fickdörr {fmt(u1 - u0)}", box(u0, u1, wm - 10.0, wm + 10.0, d.hojd + 10.0, d.hojd + FICKA_SKENA),
               KARM), Placering(), f"{d.kod}-SKENA")
    um = (d.u0 + d.u1) / 2
    wa, wb = -skiktets_tjocklek(d.vagg, -1, um), v.tjocklek + skiktets_tjocklek(d.vagg, 1, um)
    las, ficka = ((d.u0, d.u0 + r), (d.u1 - r, d.u1)) if d.mot > 0 else ((d.u1 - r, d.u1), (d.u0, d.u0 + r))
    delad = ((wa, wm - SLITS), (wm + SLITS, wb))
    bitar = [("L", *las, wa, wb, 0.0, d.hojd - r, "z")]
    bitar += [(f"F{i + 1}", *ficka, w0, w1, 0.0, d.hojd - r, "z") for i, (w0, w1) in enumerate(delad)]
    bitar += [(f"O{i + 1}", d.u0, d.u1, w0, w1, d.hojd - r, d.hojd, "x") for i, (w0, w1) in enumerate(delad)]
    for namn, x0, x1, w0, w1, z0, z1, fiber in bitar:
        smyg, pl = virke_i_lada(x0, x1, w0, w1, z0, z1, fiber, ASK)
        m.lagg(smyg, pl, f"{d.kod}-SMYG-{namn}")
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
