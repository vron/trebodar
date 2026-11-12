"""Regelstommens regler för väggarna (45×95 C24 i ytterväggarna, 45×70 eller 45×95 i innerväggarna), i väggens system
(u längs väggen, w genom väggen, z uppåt från bjälklaget):

- syll och hammarband längs väggen, delade i elementskarvarna (över en regel); syllen bryts vid öppningar till golvet;
- reglar i väggens ändar, gavlarnas hörnstolpar (en regel i änden och en 95×45 på insidan, K-03:s LA) och fria reglar,
  antingen c/c 600 från ett raster eller uppräknade; en rasterregel utgår inne i en öppning och närmare än GLAPP
  intill en annan stående del, och rasterregler som väggen saknar räknas upp;
- takfotsväggarna: en regel under varje takbalk och kortling som vilar på väggens hammarband (takbalkar.py), så att
  takbalken står på regeln och hammarbandet inte bär den i böjning; över en öppning en kortregel från överstycket upp
  till hammarbandet. En rasterregel utgår där reglarna intill den står högst CC isär utan den (rastret behålls där
  inga takbalkar vilar på väggen), utom en regel under en elementskarv;
- vid varje öppning (oppningar.py): karmreglar på båda sidor (dubbla där väggen anger det), överstycke i öppningens
  överkant (enkelt, med avväxling under hammarbandet, dubbelt eller med dubbelt hammarband: ett andra hammarband under
  det första från karmregel till karmregel, som karmreglarna slutar under, så att de två bär var sin halva av en
  takbalk över öppningen utan att fästas till ett tvärsnitt), bröstningsregel under fönster och kortlingar
  ovanför överstycket och under bröstningen, med lägen från öppningens början;
- stolpar av flera reglar sida vid sida (K-03) och dalbalkarnas upplag på gavlarna: en sänkt liggande under balkens
  ände, regelstycken upp till hammarbandets nivå intill balkens sida och reglar under liggaren;
- innerväggar under ett takfall: ett lutande hammarband 45 med överkanten i takfallets hammarbandsplan (takbalkarnas
  underkant utan TAKLYFT, som ytterväggarnas hammarband vid takfoten), ändarna lodräta eller vinkelräta mot lutningen,
  och reglarna upp till vågräta säten i hammarbandet, halva regelns bredd från dess låga sida (hela bredden vid en
  lodrät ände).

Väggens egna data (raster eller reglar, skarvar och öppningarnas utförande) står i väggens fil, öppningarnas lägen
och storlek i oppningar.py: flyttas en öppning följer karmreglar, överstycke, bröstning och kortlingar med.
"""
from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from shapely.geometry import Polygon, box

from trebodar import skelett as S
from trebodar.byggdelar.regelvagg import Plan
from trebodar.hus.fonster_och_dorrar.oppningar import OPPNINGAR, Oppning
from trebodar.hus.stomme.prefab.takbalkar.takbalkar import FALT

R = 45.0                     # regelns bredd
CC = 600.0
GLAPP = 80.0                 # en rasterregel utgår närmare än så intill en annan stående del
SANKT = 695.0                # den sänkta liggande under en dalbalks ände på gaveln, från väggens ände

KORTLING_Z = 2200.0          # kortlingarnas underkant i innerväggarna under takfallen

ENKELT, AVVAXLING, DUBBELT, DUBBELT_HB = "enkelt", "avväxling", "dubbelt", "dubbelt hammarband"
LODRAT, VINKELRAT = "lodrät", "vinkelrät"


@dataclass(frozen=True)
class Karm:
    """Utförandet vid en öppning."""
    dubbel: bool = False                     # en karmregel till utanför varje karmregel
    overstycke: str = ENKELT                 # ENKELT, AVVAXLING (också en liggande under hammarbandet), DUBBELT eller
    #                                          DUBBELT_HB (ett andra hammarband över karmreglarna)
    kortlingar: tuple[float, ...] = ()       # kortlingarnas läge (u) från öppningens början


def vaggens_oppningar(kod: str) -> list[Oppning]:
    """Väggens öppningar ovanför bjälklaget (källarens fönster i 2NO:s system hör till källarväggarna)."""
    return [o for o in OPPNINGAR.get(kod, []) if o.z1 > 0.0]


def plattor(v: Plan, langd: float, skarvar: Sequence[float] = (), oppningar: Sequence[Oppning] = (),
            hammarband: tuple[float, float] | None = None) -> None:
    """Syll från 0 till langd och hammarband över intervallet (inget om None), delade i skarvarna; syllen bryts vid
    öppningar till golvet."""
    def bitar(a: float, b: float, hal: Sequence[tuple[float, float]]) -> list[tuple[float, float]]:
        kanter = sorted({a, b} | {s for s in skarvar if a < s < b} | {e for h in hal for e in h if a < e < b})
        return [(x, y) for x, y in zip(kanter, kanter[1:]) if not any(h0 <= x and y <= h1 for h0, h1 in hal)]
    for a, b in bitar(0.0, langd, [(o.u0, o.u1) for o in oppningar if o.z0 <= 0.0]):
        v.syll(a, b)
    for a, b in bitar(*hammarband, []) if hammarband else ():
        v.hammarband(a, b)


def hornstolpe(v: Plan, u: float, inat: int, namn: tuple[str, str], z1: float | None = None
               ) -> list[tuple[float, float]]:
    """Gavelns hörnstolpe vid änden u (inat = +1 i början, −1 i slutet): en regel i änden och en regel 95×45 på
    insidan (w 50–95, i 145-väggarna 100–145) intill den, för skivorna. Ger delarnas u-intervall."""
    a = u if inat > 0 else u - R
    v.regel(a, z1=z1, namn=namn[0])
    b = a + R if inat > 0 else a - 95.0
    v.regel(b, z1=z1, b=95.0, w0=v.tjocklek - 45.0, w1=v.tjocklek, namn=namn[1])
    return [(a, a + R), (b, b + 95.0)]


def takbalkarnas_u(kod: str) -> list[float]:
    """Takbalkarna och takfönstrens kortlingar som vilar på takfotsväggens hammarband (inte de som går till en
    dalbalk): deras början (u) i väggens system. Takfallet har takfotsväggens kod."""
    f = FALT.get(kod)
    if f is None:
        return []
    v = S.VAGGAR[kod]
    dal = S.BALKAR[f.dal] if f.dal else None
    ys = list(f.y) + [0.5 * (fo.y0 + fo.y1) - R / 2 for fo in f.fonster]
    ut = []
    for y in ys:
        if dal and dal.y0 <= y and y + R <= dal.y1:
            continue
        a = min((y - v.origo[1]) * v.u[1], (y + R - v.origo[1]) * v.u[1])
        if -1e-6 <= a <= v.langd - R + 1e-6:
            ut.append(a)
    return sorted(ut)


def _under_takbalkar(kod: str, st: Sequence[tuple[float, float]], opp: Sequence[Oppning]
                     ) -> tuple[list[float], dict[str, list[float]]]:
    """Reglarna under takbalkarna (u) och kortreglarna över öppningarna (öppningens kod: u). En takbalk som till minst
    halva bredden står på en stående del behöver ingen regel; står den till en mindre del på en, läggs regeln intill
    den delen, under resten av takbalken."""
    reglar: list[float] = []
    kort: dict[str, list[float]] = {}
    for u in takbalkarnas_u(kod):
        o = next((o for o in opp if u + R > o.u0 + 1e-6 and u < o.u1 - 1e-6), None)
        if o is not None:
            a = min(max(u, o.u0), o.u1 - R)
            kort.setdefault(o.kod, []).append(a)
            continue
        delar = list(st) + [(r, r + R) for r in reglar]
        over = [(a, b, min(b, u + R) - max(a, u)) for a, b in delar if a < u + R and u < b]
        if any(ov >= R / 2 - 1e-6 for *_, ov in over):
            continue
        for a, b, _ in over:                                  # intill delen, under resten av takbalken
            u = b if a < u else a - R
        reglar.append(u)
    return reglar, kort


def _glesa(raster_u: Sequence[float], fasta: Sequence[float], behall: Sequence[float]) -> list[float]:
    """Rasterreglarna som behövs: en rasterregel utgår där de stående delarna intill den står högst CC isär (c/c) utan
    den; reglarna i behall (elementskarvarna) står kvar."""
    ut: list[float] = []
    kvar = sorted(raster_u)
    for i, u in enumerate(kvar):
        if any(abs(u - b) < 1e-6 for b in behall):
            ut.append(u)
            continue
        fore = [a for a in list(fasta) + ut if a < u - 1e-6]
        efter = [a for a in list(fasta) + kvar[i + 1:] if a > u + 1e-6]
        if fore and efter and min(efter) - max(fore) <= CC + 1e-6:
            continue
        ut.append(u)
    return ut


def oppning(v: Plan, o: Oppning, k: Karm = Karm(), uppe: Sequence[float] = ()) -> list[tuple[float, float]]:
    """Karmreglar, överstycke, bröstningsregel och kortlingar vid öppningen, och kortreglar från överstycket upp till
    hammarbandet i uppe (u, under takbalkarna). Ger de stående delarnas u-intervall."""
    staende = [(o.u0 - R, o.u0), (o.u1, o.u1 + R)]
    if k.dubbel:
        staende += [(o.u0 - 2 * R, o.u0 - R), (o.u1 + R, o.u1 + 2 * R)]
    dhb = k.overstycke == DUBBELT_HB
    for a, _ in staende:
        v.regel(a, z1=v.hojd - 2 * R if dhb else None)
    if dhb:
        v.liggande(min(a for a, _ in staende), max(b for _, b in staende), v.hojd - 2 * R, typ="H")
    topp = o.z1 + R
    v.liggande(o.u0, o.u1, o.z1)
    if k.overstycke == DUBBELT:
        v.liggande(o.u0, o.u1, o.z1 + R)
        topp += R
    tak = v.hojd - R
    if k.overstycke == AVVAXLING:
        v.liggande(o.u0, o.u1, v.hojd - 2 * R)
        tak -= R
    elif dhb:
        tak -= R
    fonster = o.z0 > 0.0
    if fonster:
        v.liggande(o.u0, o.u1, o.z0 - R)
    for d in k.kortlingar:
        if fonster:
            v.regel(o.u0 + d, z1=o.z0 - R)
        if tak > topp:
            v.regel(o.u0 + d, z0=topp, z1=tak)
    if tak > topp:
        for u in uppe:
            if all(abs(u - (o.u0 + d)) >= R - 1e-6 for d in k.kortlingar):
                v.regel(u, z0=topp, z1=tak)
    return staende


def raster(origo: float, langd: float, staende: Sequence[tuple[float, float]], oppningar: Sequence[tuple[float, float]],
           utan: Sequence[float] = ()) -> list[float]:
    """Rasterreglarnas u: c/c CC genom origo över hela väggen, inte inne i en öppning (u0, u1), inte närmare än GLAPP
    intill en annan stående del (utom en som står på samma ställe) och inte de uppräknade."""
    ut = []
    u = origo - CC * int(origo // CC)
    while u + R <= langd + 1e-6:
        inne = any(u0 - R < u < u1 for u0, u1 in oppningar)
        nara = any(u < b + GLAPP and a < u + R + GLAPP and abs(u - a) > 1e-6 for a, b in staende)
        if not inne and not nara and all(abs(u - x) > 1e-6 for x in utan):
            ut.append(u)
        u += CC
    return ut


def vagg(v: Plan, kod: str, karmar: dict[str, Karm] | None = None, skarvar: Sequence[float] = (),
         hammarband: tuple[float, float] | bool = True, raster_origo: float | None = None, utan: Sequence[float] = (),
         reglar: Sequence[float] = (), ander: tuple[bool, bool] = (True, True),
         staende: Sequence[tuple[float, float]] = ()) -> None:
    """Väggens regelstomme enligt reglerna: syll och hammarband (hammarband: True längs hela väggen, ett intervall
    eller False när väggens fil lägger det själv), vanliga ändreglar (ander; hörnstolpar och specialdelar läggs av
    väggens fil och anges i staende), öppningarna och de fria reglarna (raster och uppräknade)."""
    langd = S.VAGGAR[kod].langd
    opp = vaggens_oppningar(kod)
    hb = (0.0, langd) if hammarband is True else hammarband or None
    plattor(v, langd, skarvar, opp, hb)
    st = list(staende)
    if ander[0]:
        v.regel(0.0)
        st.append((0.0, R))
    if ander[1]:
        v.regel(langd - R)
        st.append((langd - R, langd))
    for o in opp:
        st += [(o.u0 - R, o.u0), (o.u1, o.u1 + R)]
        if (karmar or {}).get(o.kod.split("-")[-1], Karm()).dubbel:
            st += [(o.u0 - 2 * R, o.u0 - R), (o.u1 + R, o.u1 + 2 * R)]
    tak, kort = _under_takbalkar(kod, st + [(u, u + R) for u in reglar], opp)
    for o in opp:
        oppning(v, o, (karmar or {}).get(o.kod.split("-")[-1], Karm()), kort.get(o.kod, ()))
    fria = list(reglar) + tak
    if raster_origo is not None:
        rast = raster(raster_origo, langd, st + [(u, u + R) for u in fria], [(o.u0, o.u1) for o in opp], utan)
        if tak:
            skarvreglar = [u for u in rast if any(abs(u + R / 2 - s) < 1e-6 for s in skarvar)]
            rast = _glesa(rast, [a for a, _ in st] + fria, skarvreglar)
        fria += rast
    upptagna = {round(a, 6) for a, _ in st}
    for u in fria:
        if round(u, 6) not in upptagna:
            v.regel(u)
            upptagna.add(round(u, 6))


def skarv(origo: float, nr: int) -> float:
    """Elementskarven mitt på rasterregel nr (räknat från origo)."""
    return origo + nr * CC + R / 2


def stolpe(v: Plan, namn: str, u: float, antal: int, z0: float = R, z1: float | None = None,
           toppar: Sequence[float | None] = (), w0: float = 0.0, w1: float | None = None) -> list[tuple[float, float]]:
    """Stolpe av `antal` reglar sida vid sida från u, namngivna <namn>-1 … (K-03); toppar: reglarnas överkant var för
    sig (None: väggens hammarband). Ger reglarnas u-intervall."""
    ut = []
    for i in range(antal):
        a = u + i * R
        topp = toppar[i] if i < len(toppar) else z1
        v.regel(a, z0=z0, z1=topp, w0=w0, w1=w1, namn=f"{namn}-{i + 1}")
        ut.append((a, a + R))
    return ut


def balkens_sidor(kod: str, balk: str) -> tuple[float, float]:
    """Dalbalkens sidor i gavelns u (balkarna går i y-led, gavlarna i x-led)."""
    b, w = S.BALKAR[balk], S.VAGGAR[kod]
    a, c = sorted((b.x + s * S.BALK_B / 2 - w.origo[0]) * w.u[0] for s in (-1, 1))
    return a, c


def balkens_sida(kod: str, balk: str) -> float:
    """Dalbalkens inre sida i gavelns u (mot väggens mitt), där hammarbandet slutar."""
    a, c = balkens_sidor(kod, balk)
    return c if a + c < S.VAGGAR[kod].langd else a


def balkupplag(v: Plan, kod: str, balk: str, reglar: dict[float, str | None]) -> list[tuple[float, float]]:
    """En dalbalks ände på gaveln: en sänkt liggande under balkens ände (SANKT från väggens ände) med en regel i
    hela höjden intill dess inre ände, två regelstycken från den upp till hammarbandets nivå intill balkens inre sida
    (hammarbandet slutar där, väggens fil anger det) och reglar (u: namn eller None) under den. Ger de stående
    delarnas u-intervall."""
    langd = S.VAGGAR[kod].langd
    sida = balkens_sida(kod, balk)
    i_borjan = 2 * sida < langd
    dal = S.BALKAR[balk].uk
    s0, s1 = (0.0, SANKT) if i_borjan else (langd - SANKT, langd)
    v.liggande(s0, s1, dal - R)
    inre = s1 if i_borjan else s0 - R
    v.regel(inre)
    for k in range(2):
        a = sida + k * R if i_borjan else sida - (k + 1) * R
        v.liggande(a, a + R, dal, h=v.hojd - R - dal)
    for u, namn in reglar.items():
        v.regel(u, z1=dal - R, namn=namn)
    return [(inre, inre + R)] + [(u, u + R) for u in reglar]


def hammarbandsplan(kod: str, takfall: str, lyft: float = 0.0) -> Callable[[float], float]:
    """Takfallets hammarbandsplan i väggens u (väggen går längs x): takbalkarnas underkant utan TAKLYFT, lyft högre."""
    t, w = S.TAKFALL[takfall], S.VAGGAR[kod]

    def z(u: float) -> float:
        return t.z_underkant(w.origo[0] + w.u[0] * u) - S.TAKLYFT + lyft
    return z


def lutande_hammarband(ok: Callable[[float], float], start: tuple[float, str], slut: tuple[float, str],
                       reglar: Sequence[float]) -> tuple[Polygon, dict[float, float]]:
    """Lutande hammarband 45 (vinkelrätt mot lutningen) med överkanten ok, från start till slut (u och LODRAT eller
    VINKELRAT: änden lodrät, eller vinkelrät mot lutningen genom underkantens hörn), med ett vågrätt säte på varje regel
    (u), halva regelns bredd från dess låga sida och hela bredden vid en lodrät ände. Ger hammarbandets profil och
    reglarnas överkant (u: z)."""
    k = (ok(1000.0) - ok(0.0)) / 1000.0
    c = 1.0 / math.sqrt(1.0 + k * k)                     # cos för lutningen

    def uk(u: float) -> float:
        return ok(u) - R / c

    def hornen(u: float, typ: str) -> tuple[tuple[float, float], tuple[float, float]]:
        """Ändens hörn i underkant och överkant."""
        if typ == LODRAT:
            return (u, uk(u)), (u, ok(u))
        return (u, uk(u)), (u - R * k * c, uk(u) + R * c)

    (a0, a1), (b0, b1) = hornen(*start), hornen(*slut)
    profil = Polygon([a0, b0, b1, a1])
    lodrata = [u for u, typ in (start, slut) if typ == LODRAT]
    toppar = {}
    for u in reglar:
        s = R if any(abs(u - e) < 1e-6 or abs(u + R - e) < 1e-6 for e in lodrata) else R / 2
        z = uk(u + s) if k > 0 else uk(u + R - s)
        profil = profil.difference(box(u, -1e5, u + R, z))
        toppar[u] = z
    return profil, toppar
