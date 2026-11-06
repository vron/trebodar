"""Köksskåpen (ärende #21): varje skåp byggs för sig, i sitt eget system, så att skåpen kan ritas var för sig och
sedan sättas på plats (kok.py): x längs skåpets bredd från dess vänstra sida sett framifrån, y in i skåpet från
stommens framkant och z uppåt från golvet.

Stommen av björkplywood 20 mm: sidorna från sparklisten (90) upp till bänkskivans underkant (888), botten och tak
mellan sidorna och ryggen mellan botten och tak; djupet 600, så att det blir 58 mm bakom skåpen mot väggen under
bänkskivan 700 (frontens 22 och 20 mm utstick). Fyra fronter av fräst ask 22, från toppen 115, 115, 233 och 323 höga
med 3 mm emellan och under bänkskivan, med ett linsformat grepp fräst nära överkanten; fronterna sitter utanpå
stommen, 6 mm in över sidorna, och mellan skåpen sitter en lodrät askbräda 22 över fogen, 3 mm från fronterna
(kok.py). Lådorna av massiv björk 14 med botten av björkplywood 4 i spår i sidorna och framstycket; bakstycket står
på botten, som går ut till lådans bakkant (Blums utförande utan urtag i bakstycket). Askfronten skruvas på den färdiga
lådan. Löpare Blum MOVENTO 760H med BLUMOTION S (teknisk datablad TD-132/1, 06.22):

- lådans invändiga bredd SKW = LW − 42 (LW skåpets invändiga bredd), sidorna högst 16 mm (här 14): 7 mm mellan
  lådsidan och skåpsidan, där löparen sitter;
- lådans längd SKL = NL − 10 (NL löparens nominella längd), skåpets invändiga djup minst NL + 3;
- bottnens urtag 12–15 mm över sidornas underkant (här 13): löparen under sidan och i urtaget under botten, högst
  28,5 mm in från skåpsidan;
- minst 7 mm fritt över lådsidan och minst 38 mm från skåpets botten till den nedersta lådans botten;
- kopplingarna Blum T51.7601 ligger plant under botten och skruvas med två skruvar 75° in i framstycket (mallen
  T65.1600.01), därför går framstycket ned under botten; löparens hake i ett hål Ø6 × 10 i sidans bakände, 7 mm från
  utsidan och 11 mm upp.

Löparna är förenklade (en profil per sida); kopplingarna, djupjusteringen och skruvhålen ritas inte. Skåptyperna: lådskåp
med fyra lådor, diskbänksskåp (de två översta fronterna fasta på en skiva, öppet tak för diskhon, kortare lådor för
rören bakom) och hällskåp (den översta fronten fast, öppet tak för hällen); diskmaskinen står i ett skåps ställe.
"""
from __future__ import annotations

from dataclasses import dataclass

from modellering import Del, Form, Montage, Placering, box, cylinder, prisma

from trebodar.byggdelar.virke import fmt
from trebodar.material import ASK, BJORK, BJORKPLYWOOD, LOPARE, VITVARA

T = 20.0                                   # stommen
T_LADA, T_BOTTEN, SPAR = 14.0, 4.0, 6.0    # lådans sidor, botten och bottnens spår i sidorna
URTAG = 13.0                               # bottnens urtag över sidornas underkant (Blum 12–15)
HAKE = (6.0, 10.0, 7.0, 11.0)              # hålet för löparens hake i sidans bakände: Ø, djup, från utsidan, upp
LOPARE_H, LOPARE_IN = 10.0, 28.5           # löparens profil under lådsidan och hur långt den når in från skåpsidan
FRITT_OVER, FRITT_UNDER = 7.0, 38.0        # Blum: fritt över lådsidan, skåpets botten till den nedersta lådans botten
SKW_AVDRAG, SKL_AVDRAG, NL_TILLAGG = 42.0, 10.0, 3.0
SOCKEL, Z_TOPP = 90.0, 888.0               # sparklisten och bänkskivans underkant
DJUP = 600.0
FRONT_T, SPEL = 22.0, 3.0
FRONTER = (323.0, 233.0, 115.0, 115.0)     # nedifrån
OVER_SIDAN = 6.0                           # fronten in över stommens sida
GREPP = (280.0, 28.0, 10.0, 30.0)          # det frästa greppet: längd, höjd mitt på, djup, mitten under överkanten
REGEL = 40.0                               # takets reglar fram och bak där taket är öppet (diskho, häll)
DISKMASKIN = (598.0, 550.0)                # integrerad diskmaskin 60: bredd, djup (höjden från sparklisten)
assert abs(SOCKEL + sum(FRONTER) + SPEL * len(FRONTER) - Z_TOPP) < 1e-9, "fronterna fyller upp till bänkskivan"


@dataclass(frozen=True)
class Skaptyp:
    namn: str
    lador: tuple[bool, ...]                # per front nedifrån: låda (True) eller fast front
    nl: float = 550.0                      # löparnas nominella längd
    oppet_tak: bool = False                # taket reglar fram och bak (diskho, häll)


LADSKAP = Skaptyp("Lådskåp", (True, True, True, True))
DISKBANKSSKAP = Skaptyp("Diskbänksskåp", (True, True, False, False), nl=350.0, oppet_tak=True)
HALLSKAP = Skaptyp("Hällskåp", (True, True, True, False), oppet_tak=True)


def fronternas_z() -> list[tuple[float, float]]:
    """Fronternas (z0, z1) nedifrån."""
    ut, z = [], SOCKEL
    for h in FRONTER:
        ut.append((z, z + h))
        z += h + SPEL
    return ut


def ladornas_z() -> list[tuple[float, float]]:
    """Lådornas sidor (z0, z1) nedifrån: 5 över frontens underkant, den nedersta 38 över skåpets botten (Blum), och
    7 mm fritt under löparen ovanför eller under taket."""
    z0 = [f0 + 5.0 for f0, _ in fronternas_z()]
    z0[0] = max(z0[0], SOCKEL + T + FRITT_UNDER - URTAG - T_BOTTEN)
    topp = [b - LOPARE_H - FRITT_OVER for b in z0[1:]] + [Z_TOPP - T - FRITT_OVER]
    return list(zip(z0, topp))


def front(x0: float, x1: float, z0: float, z1: float, grepp_z: float | None = None) -> Form:
    """Front av ask (y −22..0) med det frästa greppet: en lins nära överkanten (eller med mitten i grepp_z, höga
    dörrar), i (u, v) = (x, −z) utdragen längs y från framsidan."""
    L, h, d, under = GREPP
    xm, zm = (x0 + x1) / 2, z1 - under if grepp_z is None else grepp_z
    n = 24
    ovre = [(xm - L / 2 + L * i / n, zm + h / 2 * (1.0 - (2.0 * i / n - 1.0) ** 2)) for i in range(n + 1)]
    lins = ovre + [(x, 2 * zm - z) for x, z in reversed(ovre[1:-1])]
    grepp = prisma([(x, -z) for x, z in lins], d).placerad(
        Placering.axlar((0.0, -FRONT_T, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)))
    return box(x0, x1, -FRONT_T, 0.0, z0, z1) - grepp


def _hake(x: float, y: float, z: float) -> Form:
    """Hålet för löparens hake, in i sidans bakände y från bakänden (x, z: hålets mitt)."""
    d, djup, _, _ = HAKE
    return cylinder(d / 2, djup + 1.0).placerad(Placering.axlar((x, y + 1.0, z), (1.0, 0.0, 0.0), (0.0, -1.0, 0.0)))


def _lada(m: Montage, kod: str, nr: int, bredd: float, nl: float, z0: float, z1: float) -> None:
    """Låda nr på löpare: sidor och framstycke med spår för botten, bakstycket på botten, botten och löparna."""
    lw = bredd - 2 * T
    skw, skl = lw - SKW_AVDRAG, nl - SKL_AVDRAG
    xs = T + (lw - skw - 2 * T_LADA) / 2                     # lådsidans utsida, 7 mm från skåpsidan
    xi0, xi1 = xs + T_LADA, xs + T_LADA + skw                 # lådans insida
    zb = z0 + URTAG
    spar_v = box(xi0 - SPAR, xi0, -1.0, skl + 1.0, zb, zb + T_BOTTEN)
    spar_h = box(xi1, xi1 + SPAR, -1.0, skl + 1.0, zb, zb + T_BOTTEN)
    spar_f = box(xi0 - 1.0, xi1 + 1.0, T_LADA - SPAR, T_LADA + 1.0, zb, zb + T_BOTTEN)
    _, _, ut, upp = HAKE
    p = f"{kod}-LADA{nr}"
    h = f"{fmt(skl)}×{fmt(z1 - z0)}"
    for namn, f, mat in (
            ("SIDA-V", box(xs, xi0, 0.0, skl, z0, z1) - spar_v - _hake(xs + ut, skl, z0 + upp), BJORK),
            ("SIDA-H", box(xi1, xi1 + T_LADA, 0.0, skl, z0, z1) - spar_h - _hake(xi1 + T_LADA - ut, skl, z0 + upp),
             BJORK),
            ("BOTTEN", box(xi0 - SPAR, xi1 + SPAR, T_LADA - SPAR, skl, zb, zb + T_BOTTEN), BJORKPLYWOOD),
            ("FRAM", box(xi0, xi1, 0.0, T_LADA, z0, z1) - spar_f, BJORK),
            ("BAK", box(xi0, xi1, skl - T_LADA, skl, zb + T_BOTTEN, z1), BJORK)):
        beskr = {"SIDA-V": f"Lådsida björk {fmt(T_LADA)} {h}", "SIDA-H": f"Lådsida björk {fmt(T_LADA)} {h}",
                 "BOTTEN": f"Lådbotten {fmt(T_BOTTEN)} {fmt(skw + 2 * SPAR)}×{fmt(skl - T_LADA + SPAR)}",
                 "FRAM": f"Lådans framstycke björk {fmt(T_LADA)} {fmt(skw)}×{fmt(z1 - z0)}",
                 "BAK": f"Lådans bakstycke björk {fmt(T_LADA)} {fmt(skw)}×{fmt(z1 - zb - T_BOTTEN)}"}[namn]
        m.lagg(Del(beskr, f, mat), Placering(), f"{p}-{namn}")
    # löparna: under lådsidan från skåpsidan och in under botten i urtaget, bakom framstycket (där kopplingen sitter)
    for namn, (a, b, c) in (("V", (T, T + LOPARE_IN, xi0)), ("H", (bredd - T - LOPARE_IN, bredd - T, xi1))):
        under = box(a, b, 0.0, nl, z0 - LOPARE_H, z0)
        inne = box(c, b, T_LADA, nl, z0, zb) if namn == "V" else box(a, c, T_LADA, nl, z0, zb)
        m.lagg(Del(f"Löpare MOVENTO 760H NL {fmt(nl)}", under | inne, LOPARE), Placering(), f"{p}-SKENA-{namn}")


def skap(kod: str, typ: Skaptyp, bredd: float) -> Montage:
    """Ett skåp av typen, bredd (stommens yttermått) längs x, i skåpets system."""
    m = Montage(kod, typ.namn, f"{typ.namn} {fmt(bredd)}×{fmt(DJUP)}, stomme av björkplywood 20, fronter av ask",
                produkt="KOKSSKAP")
    inne = DJUP - T
    assert typ.nl + NL_TILLAGG <= inne, "skåpets invändiga djup (Blum: minst NL + 3)"
    stomme = [("SIDA-V", box(0.0, T, 0.0, DJUP, SOCKEL, Z_TOPP)),
              ("SIDA-H", box(bredd - T, bredd, 0.0, DJUP, SOCKEL, Z_TOPP)),
              ("BOTTEN", box(T, bredd - T, 0.0, DJUP, SOCKEL, SOCKEL + T)),
              ("RYGG", box(T, bredd - T, inne, DJUP, SOCKEL + T, Z_TOPP - T))]
    if typ.oppet_tak:
        stomme += [("TAK-F", box(T, bredd - T, 0.0, REGEL, Z_TOPP - T, Z_TOPP)),
                   ("TAK-B", box(T, bredd - T, inne - REGEL, DJUP, Z_TOPP - T, Z_TOPP))]
    else:
        stomme.append(("TAK", box(T, bredd - T, 0.0, DJUP, Z_TOPP - T, Z_TOPP)))
    for namn, f in stomme:
        m.lagg(Del(f"Skåpstomme björkplywood {fmt(T)}", f, BJORKPLYWOOD), Placering(), f"{kod}-{namn}")
    fz = fronternas_z()
    fasta = [z for z, ar_lada in zip(fz, typ.lador) if not ar_lada]
    if fasta:
        # de fasta fronterna sitter på en skiva mellan sidorna, bakom dem upp till taket
        z0 = min(a for a, _ in fasta)
        m.lagg(Del(f"Skiva björkplywood {fmt(T)} för fasta fronter", box(T, bredd - T, 0.0, T, z0, Z_TOPP - T),
                   BJORKPLYWOOD), Placering(), f"{kod}-SKIVA")
    x0, x1 = T - OVER_SIDAN, bredd - T + OVER_SIDAN
    for nr, ((f0, f1), (l0, l1), ar_lada) in enumerate(zip(fz, ladornas_z(), typ.lador), start=1):
        m.lagg(Del(f"Front ask fräst {fmt(FRONT_T)} {fmt(x1 - x0)}×{fmt(f1 - f0)}" + ("" if ar_lada else " (fast)"),
                   front(x0, x1, f0, f1), ASK, produkt="KOKSFRONTER"), Placering(), f"{kod}-FRONT{nr}")
        if ar_lada:
            _lada(m, kod, nr, bredd, typ.nl, l0, l1)
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
