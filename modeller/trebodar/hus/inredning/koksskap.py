"""Köksskåpen (ärende #21): varje skåp byggs för sig, i sitt eget system, så att skåpen kan ritas var för sig och
sedan sättas på plats (kok.py): x längs skåpets bredd från dess vänstra sida sett framifrån, y in i skåpet från
stommens framkant och z uppåt från golvet.

Stommen av björkplywood 20 mm: sidorna från sparklisten (90) upp till bänkskivans underkant (888) och botten mellan
sidorna, 615 djupa (skivornas hela bredd, högst 615); ryggen av björkplywood 6 i en fals 10 × 6 i sidornas, bottnens
och (i hörnskåpet) takets bakkant, så att skåpet är 609 invändigt, för löparna NL 600, och det blir 43 mm bakom
skåpen mot väggen under bänkskivan 700 (frontens 22 och 20 mm utstick). Lådskåpens tak är av björkplywood 8 i en fals
i sidornas överkant, så att den översta lådans sidor blir höga nog för sinkningen under en front 115; över diskhon och
hällen är taket öppet, med en regel 20 fram och bak, och ryggen täcker takets och den bakre regelns bakkant. Fyra
fronter av fräst ask 22, från toppen 115, 115, 233 och 323 höga (i öns lådskåp tre, 115, 233 och 441, för högre
lådor) med 3 mm emellan och under bänkskivan, med ett linsformat grepp fräst nära överkanten; fronterna sitter utanpå
stommen, 6 mm in över sidorna, och mellan skåpen sitter en lodrät askbräda 22 över fogen, 3 mm från fronterna
(kok.py).

Lådorna av massiv björk 14 med botten av björkplywood 4 i spår runt om, sinkade med halvdolda sinkor frästa i ett
pass i Leigh D4R Pro (bruksanvisningen 2021, kap. 11), där sidan och stycket fräses samtidigt:

- fram- och bakstycket är lådans hela bredd och har tapparna, sidorna laxstjärtarna: sidorna går SINKA (ca 11 mm,
  fräsen 80-8, 8°) in i styckena, som täcker sidornas ändar med 3 mm (styckena minst 14 tjocka för den fräsen,
  fig. 11-2; sidorna 11–14, fig. 11-9), så sidorna är 2 × 3 mm kortare än lådan;
- brädornas bredd, lådsidornas höjd, väljs ur tabellen (fig. 11-8: 55, 83, 110 … 331, + 6 eller − 3 mm), så att
  det blir en halv tapp vid varje kant; alla fyra brädorna i en låda är lika höga och fräses med samma inställning;
- bottnens spår, 14–18 mm över underkanten, ligger i den nedersta laxstjärten och syns därför inte i lådans hörn.

Sinkorna är förenklade till ett urtag i styckenas ändar. Askfronten skruvas på den färdiga lådan. Löpare Blum
MOVENTO 760H med BLUMOTION S, NL 600 (760H6001S, 40 kg; under diskhon NL 350, 760H3501S) (tekniskt datablad
TD-132/1, 06.22):

- lådans invändiga bredd SKW = LW − 42 +0/−1,5 (LW skåpets invändiga bredd), här LW − 43, 1 mm innanför den övre
  gränsen; sidorna högst 16 mm (här 14), lådsidans insida 21 från skåpsidan (s. 5);
- lådans längd SKL = NL − 10 (NL löparens nominella längd), skåpets invändiga djup minst NL + 3 (s. 5; + 1 om
  löparna sätts i före skåpets montage och + 3 med djupjusteringen, NL + 7 = 607 mot skåpets 609);
- bottnens urtag 12–15 mm från sidornas underkant till bottnens undersida (s. 5), här 14: 2 mm till den nedre
  gränsen, som en slipad underkant eller en sviktande botten närmar sig, och 1 mm till den övre;
- löparen sitter under botten och sidan och behöver minst 28,5 mm under bottnens undersida, och dess skruvar sitter
  38 mm över dess underkant (s. 5: minst 38 från skåpets botten till skruvarna, + 1 om löparna sätts i före
  stommen): den nedersta lådans löpare 1 mm över skåpets botten; minst 7 mm fritt över lådsidan, till taket eller
  till löparen under lådan ovanför. Varje lådas löpare sitter bakom lådans egen front, inte under dess underkant,
  så att den går fritt från fronten under när lådan dras ut;
- bakstycket, som går ned till sidornas underkant, har ett urtag för löparen i varje nedre hörn, från sidans insida
  och upp till bottnens undersida (s. 5: 75 mm, med TIP-ON BLUMOTION 125);
- kopplingarna Blum T51.7601 (vänster och höger) ligger plant under botten vid framstyckets hörn. Fyrsidiga lådor
  har i TD-132 kopplingen skruvad lodrätt i en tjock botten (s. 19, bild 1a); med botten 4 mm skruvas den i stället
  med två skruvar 75° in i framstycket, som för tresidiga lådor (bild 1b) och i Blums monteringsanvisning för lådor
  med botten i spår, med borrmallen T65.1000.02 (Ø2,5 × 10). Därför går framstycket ned under botten;
- löparens hake i ett hål Ø6 × 10 i lådans bakkant, 7 mm från utsidan (mitt för sidan) och 11 mm upp (s. 5): genom
  bakstyckets 3 mm och in i sidans ände;
- löparen skruvas i skåpsidan (s. 13, montage på sidan) med spånskiveskruv Ø3,5 × 15 (609.1500) eller
  systemskruv Ø6 × 14,5 (661.1450.HG) i hålen LOPARENS_SKRUVAR från stommens framkant (löparen i liv med den); vid
  NL 600 som vid NL 550, och en skruv längst bak (utan mått i databladet) ger bäst stabilitet.

Löparna är förenklade (en profil per sida); kopplingarna, djupjusteringen och skruvarna ritas inte, och skruvhålen
står som data för skåpens ritningar. Skåptyperna: lådskåp med fyra lådor (i ön tre), diskbänksskåp (de två översta fronterna
fasta på en skiva, öppet tak för diskhon, kortare lådor för rören bakom) och hällskåp (den översta fronten fast, öppet
tak för hällen); diskmaskinen står i ett skåps ställe. Hörnskåpet (hornskap) har en dörr över hela höjden och stommen
förlängd in i hörnet bakom den andra bänkens ände, med en blindfront av plywood där, botten, tak 20 och en
mellanhylla; dörren hänger på två gångjärn Blum CLIP top BLUMOTION 110° (som skåpen i kok.py) i sidan bort från
hörnet.

Läs Blums datablad och Leighs bruksanvisning (kap. 11) innan skåpen eller lådorna ändras: stommens djup, lådornas
längd, bredd och höjd, löparnas lägen och sinkningen hänger ihop genom deras mått. Underlagen, som måtten ovan är
lästa ur, ligger i lokalt/manualer/ (versionshanteras inte; hämtas på nytt hit i en ny klon):

- Blum MOVENTO, tekniskt datablad TD-132/1 EN/06.22 ("Blum MOVENTO TD-132-1 EN 06.22.pdf"):
  https://d2.blum.com/services/BEC003/me13029704_td_dok_bau_$sen_$aof_$v1.pdf
- Leigh D4R Pro User Guide, 2021 ("Leigh D4R Pro User Guide 2021.pdf"; sidan med alla Leighs bruksanvisningar:
  https://www.leightools.com/instructional-videos-and-user-guides/):
  https://www.leightools.com/wp-content/uploads/2021/04/D4RPro-User-Guide-Complete-2021.pdf
- Blum MOVENTO, monteringsanvisning MD-047 ("Blum MOVENTO monteringsanvisning MD-047.pdf"): bara bilder av
  montaget, utan mått; finns bland MOVENTO:s dokument på https://www.blum.com.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from modellering import Del, Form, Montage, Placering, box, cylinder, prisma

from trebodar.byggdelar.virke import fmt
from trebodar.material import ASK, BESLAG, BJORK, BJORKPLYWOOD, LOPARE, VITVARA

T = 20.0                                   # stommen
T_RYGG, T_TAK, FALS = 6.0, 8.0, 10.0       # ryggen, lådskåpens tak och falsens bredd in i stommens skivor
T_LADA, T_BOTTEN, SPAR = 14.0, 4.0, 6.0    # lådans sidor och stycken, botten och bottnens spår
URTAG = 14.0                               # bottnens undersida över sidornas underkant (Blum 12–15)
URTAG_BAK = 75.0                           # bakstyckets urtag för löparen, från sidans insida (TD-132/1 s. 5)
HAKE = (6.0, 10.0, 7.0, 11.0)              # hålet för löparens hake i lådans bakkant: Ø, djup, från utsidan, upp
# Leigh D4R Pro, halvdolda sinkor i ett pass (bruksanvisningen kap. 11): brädans bredd ur tabellen (fig. 11-8),
# högst LEIGH_PLUS bredare eller LEIGH_MINUS smalare, och fräsens djup (fräsen 80-8, fig. 11-2), som är så långt
# sidorna går in i fram- och bakstycket
LEIGH = (55.0, 83.0, 110.0, 138.0, 166.0, 193.0, 221.0, 248.0, 276.0, 305.0, 331.0)
LEIGH_PLUS, LEIGH_MINUS, SINKA = 6.0, 3.0, 11.0
assert T_LADA >= SINKA + 3.0, "Leigh: stycket minst 3 mm tjockare än fräsens djup"
assert 11.0 <= T_LADA <= 14.3, "Leigh: lådsidan 11–14 mm"
# löparens skruvar i skåpsidan (TD-132 s. 13, 760H): avstånd från stommens framkant per NL; det första (19) kan bytas
# mot en spånskiveskruv Ø4 × 15, och vid NL 550 och 600 ger en skruv längst bak (utan mått) dessutom bäst stabilitet
LOPARENS_SKRUVAR = {600.0: (19.0, 37.0, 69.0, 243.0, 261.0, 293.0), 350.0: (19.0, 37.0, 69.0, 261.0)}
NL_TILLAGG_MAX = 7.0                       # + 1 om löparna sätts i före skåpets montage, + 3 med djupjusteringen
# löparen (TD-132/1 s. 5): utrymmet under bottnens undersida, skruvarnas axel över löparens underkant och (förenklat)
# profilens bredd under botten innanför lådsidan; + 1 mm under den nedersta lådan för löpare som sätts i före stommen
LOPARE_UNDER, LOPARE_SKRUV, LOPARE_BREDD, MONTAGE = 28.5, 38.0, 20.0, 1.0
FRITT_OVER = 7.0                           # Blum: fritt över lådsidan
SKW_AVDRAG, SKL_AVDRAG, NL_TILLAGG = 43.0, 10.0, 3.0    # Blum: SKW = LW − 42 +0/−1,5; här 1 mm innanför
assert 12.0 <= URTAG <= 15.0 and 42.0 <= SKW_AVDRAG <= 43.5, "Blums toleranser"
SOCKEL, Z_TOPP = 90.0, 888.0               # sparklisten och bänkskivans underkant
DJUP = 615.0                               # sidornas och bottnens djup: skivornas bredd, högst 615 (användaren)
FRONT_T, SPEL = 22.0, 3.0
FRONTER = (323.0, 233.0, 115.0, 115.0)     # nedifrån
FRONTER_ON = (441.0, 233.0, 115.0)         # öns lådskåp nedifrån: tre lådor, högre
OVER_SIDAN = 6.0                           # fronten in över stommens sida
GREPP = (280.0, 28.0, 10.0, 30.0)          # det frästa greppet: längd, höjd mitt på, djup, mitten under överkanten
REGEL = 40.0                               # takets reglar fram och bak där taket är öppet (diskho, häll)
DISKMASKIN = (598.0, 550.0)                # integrerad diskmaskin 60: bredd, djup (höjden från sparklisten)
HYLLA_IN = 20.0                            # hörnskåpets mellanhylla: indragen från stommens framkant
# gångjärnen Blum CLIP top BLUMOTION 110° (ärende #56; också kok.py): koppen Ø, djup och mitten från dörrens kant;
# plattan: mitten bakom dörrens baksida, längd, höjd, tjocklek; armen: bredd, höjd; de yttersta från dörrens kanter
KOPP = (35.0, 13.0, 22.5)
PLATTA = (37.0, 40.0, 40.0, 10.0)
ARM = (15.0, 14.0)
GANGJARN_KANT = 100.0
assert all(abs(SOCKEL + sum(f) + SPEL * len(f) - Z_TOPP) < 1e-9 for f in (FRONTER, FRONTER_ON)), \
    "fronterna fyller upp till bänkskivan"


@dataclass(frozen=True)
class Skaptyp:
    namn: str
    lador: tuple[bool, ...]                # per front nedifrån: låda (True) eller fast front
    nl: float = 600.0                      # löparnas nominella längd
    oppet_tak: bool = False                # taket reglar fram och bak (diskho, häll)
    fronter: tuple[float, ...] = FRONTER   # fronternas höjder nedifrån


LADSKAP = Skaptyp("Lådskåp", (True, True, True, True))
LADSKAP_ON = Skaptyp("Lådskåp med tre lådor", (True, True, True), fronter=FRONTER_ON)
DISKBANKSSKAP = Skaptyp("Diskbänksskåp", (True, True, False, False), nl=350.0, oppet_tak=True)
HALLSKAP = Skaptyp("Hällskåp", (True, True, True, False), oppet_tak=True)


def fronternas_z(fronter: tuple[float, ...] = FRONTER) -> list[tuple[float, float]]:
    """Fronternas (z0, z1) nedifrån."""
    ut, z = [], SOCKEL
    for h in fronter:
        ut.append((z, z + h))
        z += h + SPEL
    return ut


def sidhojd(hogst: float) -> float:
    """Lådsidans höjd för sinkningen (Leigh, fig. 11-8): den största bredden ur tabellen som ryms i hogst, eller
    upp till LEIGH_MINUS lägre där tabellens bredd inte ryms helt."""
    w = max(w for w in LEIGH if w - LEIGH_MINUS <= hogst)
    return min(w, float(math.floor(hogst)))


def ladornas_z(fronter: tuple[float, ...] = FRONTER) -> list[tuple[float, float]]:
    """Lådornas sidor (z0, z1) nedifrån, i hela mm: löparen bakom lådans egen front, inte under dess underkant, och
    den nedersta fritt över skåpets botten (+ 1, Blum); 7 mm fritt under löparen ovanför eller under taket; höjden
    ur Leighs tabell (sidhojd)."""
    under = LOPARE_UNDER - URTAG                            # löparens underkant under lådsidans
    z0 = [float(math.ceil(max(f0, SOCKEL + T + MONTAGE if i == 0 else f0) + under))
          for i, (f0, _) in enumerate(fronternas_z(fronter))]
    tak = [b - under - FRITT_OVER for b in z0[1:]] + [Z_TOPP - T_TAK - FRITT_OVER]
    return [(a, a + sidhojd(t - a)) for a, t in zip(z0, tak)]


def grepp_lins(x0: float, x1: float, z1: float, grepp_z: float | None = None) -> list[tuple[float, float]]:
    """Det frästa greppets lins (x, z) på fronten x0–x1: mitt på fronten, med mitten GREPP[3] under överkanten z1
    (eller i grepp_z, höga dörrar)."""
    L, h, _, under = GREPP
    xm, zm = (x0 + x1) / 2, z1 - under if grepp_z is None else grepp_z
    n = 24
    ovre = [(xm - L / 2 + L * i / n, zm + h / 2 * (1.0 - (2.0 * i / n - 1.0) ** 2)) for i in range(n + 1)]
    return ovre + [(x, 2 * zm - z) for x, z in reversed(ovre[1:-1])]


def front(x0: float, x1: float, z0: float, z1: float, grepp_z: float | None = None) -> Form:
    """Front av ask (y −22..0) med det frästa greppet (grepp_lins), i (u, v) = (x, −z) utdraget längs y från
    framsidan."""
    grepp = prisma([(x, -z) for x, z in grepp_lins(x0, x1, z1, grepp_z)], GREPP[2]).placerad(
        Placering.axlar((0.0, -FRONT_T, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)))
    return box(x0, x1, -FRONT_T, 0.0, z0, z1) - grepp


def _hake(x: float, y: float, z: float) -> Form:
    """Hålet för löparens hake, in i lådans bakkant y (x, z: hålets mitt)."""
    d, djup, _, _ = HAKE
    return cylinder(d / 2, djup + 1.0).placerad(Placering.axlar((x, y + 1.0, z), (1.0, 0.0, 0.0), (0.0, -1.0, 0.0)))


def _lada(m: Montage, kod: str, nr: int, bredd: float, nl: float, z0: float, z1: float) -> None:
    """Låda nr på löpare: fram- och bakstycket i lådans hela bredd med urtagen för sidornas sinkor, sidorna mellan
    dem, botten i spår runt om, bakstyckets urtag för löparna och hålen för deras hakar, och löparna."""
    lw = bredd - 2 * T
    skw, skl = lw - SKW_AVDRAG, nl - SKL_AVDRAG
    xs = T + (lw - skw - 2 * T_LADA) / 2                     # lådans utsida, 7,5 mm från skåpsidan
    xi0, xi1 = xs + T_LADA, xs + T_LADA + skw                 # lådans insida
    xy = xi1 + T_LADA                                         # lådans andra utsida
    tacker = T_LADA - SINKA                                   # styckena täcker sidornas ändar
    ya, yb = tacker, skl - tacker                             # sidornas ändar
    yi0, yi1 = T_LADA, skl - T_LADA                           # lådans insida fram och bak
    zb = z0 + URTAG
    assert any(w - LEIGH_MINUS <= z1 - z0 <= w + LEIGH_PLUS for w in LEIGH), "lådsidans höjd ur Leighs tabell"
    assert URTAG_BAK >= LOPARE_BREDD, "löparen går fritt i bakstyckets urtag"
    botten = box(xi0 - SPAR, xi1 + SPAR, yi0 - SPAR, yi1 + SPAR, zb, zb + T_BOTTEN)
    sida_v, sida_h = box(xs, xi0, ya, yb, z0, z1), box(xi1, xy, ya, yb, z0, z1)
    _, _, ut, upp = HAKE
    hakar = [_hake(xs + ut, skl, z0 + upp), _hake(xy - ut, skl, z0 + upp)]
    urtag = [box(xi0, xi0 + URTAG_BAK, yi1 - 1.0, skl + 1.0, z0 - 1.0, zb),
             box(xi1 - URTAG_BAK, xi1, yi1 - 1.0, skl + 1.0, z0 - 1.0, zb)]
    p = f"{kod}-LADA{nr}"
    h = fmt(z1 - z0)
    stycke = f"björk {fmt(T_LADA)} {fmt(xy - xs)}×{h}"
    for namn, f, mat, beskr in (
            ("SIDA-V", sida_v - botten - hakar[0], BJORK, f"Lådsida björk {fmt(T_LADA)} {fmt(yb - ya)}×{h}"),
            ("SIDA-H", sida_h - botten - hakar[1], BJORK, f"Lådsida björk {fmt(T_LADA)} {fmt(yb - ya)}×{h}"),
            ("BOTTEN", botten, BJORKPLYWOOD,
             f"Lådbotten {fmt(T_BOTTEN)} {fmt(skw + 2 * SPAR)}×{fmt(yi1 - yi0 + 2 * SPAR)}"),
            ("FRAM", box(xs, xy, 0.0, yi0, z0, z1) - sida_v - sida_h - botten, BJORK, f"Lådans framstycke {stycke}"),
            ("BAK", box(xs, xy, yi1, skl, z0, z1) - sida_v - sida_h - botten - urtag[0] - urtag[1] - hakar[0]
             - hakar[1], BJORK, f"Lådans bakstycke {stycke}")):
        m.lagg(Del(beskr, f, mat), Placering(), f"{p}-{namn}")
    # löparna (förenklade till sitt utrymme): från skåpsidan under lådsidan och LOPARE_BREDD in under botten, ned till
    # LOPARE_UNDER under bottnens undersida; i urtaget bakom framstycket (där kopplingen sitter) och genom bakstyckets
    zl = zb - LOPARE_UNDER
    for namn, (a, b, c) in (("V", (T, xi0 + LOPARE_BREDD, xi0)), ("H", (xi1 - LOPARE_BREDD, bredd - T, xi1))):
        under = box(a, b, 0.0, nl, zl, z0)
        inne = box(c, b, T_LADA, nl, z0, zb) if namn == "V" else box(a, c, T_LADA, nl, z0, zb)
        m.lagg(Del(f"Löpare MOVENTO 760H NL {fmt(nl)}", under | inne, LOPARE), Placering(), f"{p}-SKENA-{namn}")


def _stomme(m: Montage, kod: str, langd: float, tak: str) -> float:
    """Stommens sidor, botten, tak och rygg för ett skåp langd brett, med ryggen i fals i sidornas och bottnens
    bakkant. tak: "tunt" (T_TAK i fals i sidornas överkant, lådskåpen), "oppet" (reglar fram och bak) eller "helt"
    (T mellan sidorna, med fals för ryggen). Ger skåpets invändiga djup."""
    inne = DJUP - T_RYGG
    x0, x1 = T - FALS, langd - T + FALS                     # ryggens och det tunna takets kanter i sidornas falsar
    zr = SOCKEL + T - FALS                                  # ryggens underkant i bottnens fals
    fals_v = box(x0, T + 1.0, inne, DJUP + 1.0, SOCKEL - 1.0, Z_TOPP + 1.0)
    fals_h = box(langd - T - 1.0, x1, inne, DJUP + 1.0, SOCKEL - 1.0, Z_TOPP + 1.0)
    sida_v, sida_h = box(0.0, T, 0.0, DJUP, SOCKEL, Z_TOPP) - fals_v, box(langd - T, langd, 0.0, DJUP, SOCKEL,
                                                                           Z_TOPP) - fals_h
    botten = box(T, langd - T, 0.0, DJUP, SOCKEL, SOCKEL + T) - box(T - 1.0, langd - T + 1.0, inne, DJUP + 1.0, zr,
                                                                    SOCKEL + T + 1.0)
    skiva = f"Skåpstomme björkplywood {fmt(T)}"
    delar: list[tuple[str, Form, str]] = [("BOTTEN", botten, skiva)]
    z_rygg = Z_TOPP                                         # ryggen täcker takets och den bakre regelns bakkant
    if tak == "tunt":
        tak_v = box(x0, T + 1.0, -1.0, DJUP + 1.0, Z_TOPP - T_TAK, Z_TOPP + 1.0)
        tak_h = box(langd - T - 1.0, x1, -1.0, DJUP + 1.0, Z_TOPP - T_TAK, Z_TOPP + 1.0)
        sida_v, sida_h = sida_v - tak_v, sida_h - tak_h
        delar.append(("TAK", box(x0, x1, 0.0, inne, Z_TOPP - T_TAK, Z_TOPP), f"Tak björkplywood {fmt(T_TAK)}"))
    elif tak == "oppet":
        delar += [("TAK-F", box(T, langd - T, 0.0, REGEL, Z_TOPP - T, Z_TOPP), skiva),
                  ("TAK-B", box(T, langd - T, inne - REGEL, inne, Z_TOPP - T, Z_TOPP), skiva)]
    else:
        z_rygg = Z_TOPP - T + FALS
        delar.append(("TAK", box(T, langd - T, 0.0, DJUP, Z_TOPP - T, Z_TOPP)
                      - box(T - 1.0, langd - T + 1.0, inne, DJUP + 1.0, Z_TOPP - T - 1.0, z_rygg), skiva))
    delar = [("SIDA-V", sida_v, skiva), ("SIDA-H", sida_h, skiva)] + delar
    delar.append(("RYGG", box(x0, x1, inne, DJUP, zr, z_rygg), f"Rygg björkplywood {fmt(T_RYGG)}"))
    for namn, f, beskr in delar:
        m.lagg(Del(beskr, f, BJORKPLYWOOD), Placering(), f"{kod}-{namn}")
    return inne


def skap(kod: str, typ: Skaptyp, bredd: float) -> Montage:
    """Ett skåp av typen, bredd (stommens yttermått) längs x, i skåpets system."""
    m = Montage(kod, typ.namn, f"{typ.namn} {fmt(bredd)}×{fmt(DJUP)}, stomme av björkplywood 20, fronter av ask",
                produkt="KOKSSKAP")
    assert typ.nl in LOPARENS_SKRUVAR, "löparens skruvhål (TD-132 s. 13) för NL"
    assert len(typ.lador) == len(typ.fronter), "en uppgift (låda eller fast) per front"
    assert not (typ.oppet_tak and typ.lador[-1]), "den översta lådan går under ett tunt tak, inte under reglarna"
    inne = _stomme(m, kod, bredd, "oppet" if typ.oppet_tak else "tunt")
    assert typ.nl + NL_TILLAGG_MAX <= inne, "skåpets invändiga djup (Blum: minst NL + 3, + 4 med montage och djupjustering)"
    fz = fronternas_z(typ.fronter)
    fasta = [z for z, ar_lada in zip(fz, typ.lador) if not ar_lada]
    if fasta:
        # de fasta fronterna sitter på en skiva mellan sidorna, bakom dem upp till taket
        z0 = min(a for a, _ in fasta)
        m.lagg(Del(f"Skiva björkplywood {fmt(T)} för fasta fronter", box(T, bredd - T, 0.0, T, z0, Z_TOPP - T),
                   BJORKPLYWOOD), Placering(), f"{kod}-SKIVA")
    x0, x1 = T - OVER_SIDAN, bredd - T + OVER_SIDAN
    for nr, ((f0, f1), (l0, l1), ar_lada) in enumerate(zip(fz, ladornas_z(typ.fronter), typ.lador), start=1):
        m.lagg(Del(f"Front ask fräst {fmt(FRONT_T)} {fmt(x1 - x0)}×{fmt(f1 - f0)}" + ("" if ar_lada else " (fast)"),
                   front(x0, x1, f0, f1), ASK, produkt="KOKSFRONTER"), Placering(), f"{kod}-FRONT{nr}")
        if ar_lada:
            _lada(m, kod, nr, bredd, typ.nl, l0, l1)
    return m


def gangjarnens_z(za: float, zb: float) -> list[float]:
    """Gångjärnens höjder på en dörr za–zb: två upp till 900 mm dörrhöjd, tre upp till 1 600, fyra upp till 2 000 och
    fem däröver, de yttersta GANGJARN_KANT från dörrens kanter."""
    h = zb - za
    n = 2 if h <= 900 else 3 if h <= 1600 else 4 if h <= 2000 else 5
    a = min(GANGJARN_KANT, h / 4)
    return [za + a + i * (h - 2 * a) / (n - 1) for i in range(n)]


def _gangjarnen(x_fast: float, inat: float, x_kopp: float, za: float, zb: float) -> tuple[list[Form], list[Del]]:
    """Gångjärnen till en dörr za–zb i skåpets system (dörrens baksida i y = 0, skåpet i +y): kopparnas hål i dörren
    (mitten i x_kopp) och gångjärnens delar, med plattan på skåpsidans insida x_fast och armen åt inat (±1)."""
    d, djup, _ = KOPP
    pd, pl, ph, pt = PLATTA
    hal, delar = [], []
    for zc in gangjarnens_z(za, zb):
        kopp = cylinder(d / 2, djup).placerad(Placering.axlar((x_kopp, 0.0, zc), (1.0, 0.0, 0.0), (0.0, -1.0, 0.0)))
        xa, xb = sorted((x_fast, x_fast + inat * pt))
        platta = box(xa, xb, pd - pl / 2, pd + pl / 2, zc - ph / 2, zc + ph / 2)
        xa, xb = sorted((x_fast, x_fast + inat * ARM[0]))
        arm = box(xa, xb, 0.0, pd - pl / 2, zc - ARM[1] / 2, zc + ARM[1] / 2)
        hal.append(kopp)
        delar.append(Del("Gångjärn Blum CLIP top BLUMOTION 110° med monteringsplatta", kopp | arm | platta, BESLAG))
    return hal, delar


def hornskap(kod: str, bredd: float, langd: float) -> Montage:
    """Hörnskåpet i skåpets system: en dörr framför 0..bredd (som ett vanligt skåp av bredden), stommen förlängd till
    langd in i hörnet (åt +x) bakom den andra bänkens ände, med en blindfront av plywood från bredd till langd, botten,
    en mellanhylla och dörrens gångjärn i sidan vid x = 0 (bort från hörnet)."""
    m = Montage(kod, "Hörnskåp", f"Hörnskåp {fmt(langd)}×{fmt(DJUP)} med dörr {fmt(bredd)}, stomme av björkplywood "
                                 f"20, front av ask", produkt="KOKSSKAP")
    zh = (SOCKEL + Z_TOPP + T) / 2                          # mellanhyllans överkant: två lika höga fack
    assert langd > bredd, "hörnskåpet går in i hörnet"
    inne = _stomme(m, kod, langd, "helt")
    for namn, f in (("BLINDFRONT", box(bredd - T, langd - T, 0.0, T, SOCKEL + T, Z_TOPP - T)),
                    ("HYLLA", box(T, langd - T, HYLLA_IN, inne, zh - T, zh))):
        m.lagg(Del(f"Skåpstomme björkplywood {fmt(T)}" if namn != "HYLLA" else f"Hylla björkplywood {fmt(T)}", f,
                   BJORKPLYWOOD), Placering(), f"{kod}-{namn}")
    x0, x1 = T - OVER_SIDAN, bredd - T + OVER_SIDAN
    z0, z1 = SOCKEL, Z_TOPP - SPEL
    hal, gj = _gangjarnen(T, 1.0, x0 + KOPP[2], z0, z1)
    dorr = front(x0, x1, z0, z1)
    for h in hal:
        dorr = dorr - h
    m.lagg(Del(f"Front ask fräst {fmt(FRONT_T)} {fmt(x1 - x0)}×{fmt(z1 - z0)} (dörr)", dorr, ASK,
               produkt="KOKSFRONTER"), Placering(), f"{kod}-FRONT")
    for i, g in enumerate(gj, start=1):
        m.lagg(g, Placering(), f"{kod}-GANGJARN{i}")
    return m


def diskmaskin(kod: str, bredd: float) -> Montage:
    """Integrerad diskmaskin i ett skåps ställe (förenklad som en låda) med en front över hela höjden."""
    m = Montage(kod, "Diskmaskin", "Integrerad diskmaskin 60 med front av fräst ask")
    b, d = DISKMASKIN
    x0 = (bredd - b) / 2
    m.lagg(Del(f"Integrerad diskmaskin {fmt(b)}×{fmt(d)}", box(x0, x0 + b, 0.0, d, SOCKEL, Z_TOPP - SPEL), VITVARA,
               produkt="DISKMASKIN"), Placering(), kod)
    f0, f1 = SOCKEL, Z_TOPP - SPEL
    m.lagg(Del(f"Front ask fräst {fmt(FRONT_T)} {fmt(bredd - 2 * (T - OVER_SIDAN))}×{fmt(f1 - f0)}",
               front(T - OVER_SIDAN, bredd - T + OVER_SIDAN, f0, f1), ASK, produkt="KOKSFRONTER"), Placering(),
           f"{kod}-FRONT")
    return m
