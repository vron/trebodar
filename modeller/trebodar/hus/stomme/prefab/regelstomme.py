"""Regelstommens regler för väggarna (45×95 C24 i ytterväggarna, 45×70 eller 45×95 i innerväggarna), i väggens system
(u längs väggen, w genom väggen, z uppåt från bjälklaget):

- syll och hammarband längs väggen, delade i elementskarvarna (över en regel); syllen bryts vid öppningar till golvet;
- reglar i väggens ändar, gavlarnas hörnstolpar (en regel i änden och en 95×45 på insidan, K-03:s LA) och fria reglar,
  antingen c/c 600 från ett raster eller uppräknade; en rasterregel utgår inne i en öppning och närmare än GLAPP
  intill en annan stående del, och rasterregler som väggen saknar räknas upp;
- vid varje öppning (oppningar.py): karmreglar på båda sidor (dubbla där väggen anger det), överstycke i öppningens
  överkant (enkelt, med avväxling under hammarbandet eller dubbelt), bröstningsregel under fönster och kortlingar
  ovanför överstycket och under bröstningen, med lägen från öppningens början;
- stolpar av flera reglar sida vid sida (K-03) och dalbalkarnas upplag på gavlarna: en sänkt liggande under balkens
  ände, regelstycken upp till hammarbandets nivå intill balkens sida och reglar under liggaren;
- innerväggar under ett takfall: ett lutande hammarband 45 med överkanten i takfallets hammarbandsplan (takbalkarnas
  underkant utan TAKLYFT, som ytterväggarnas hammarband vid takfoten), ändarna lodräta eller vinkelräta mot lutningen,
  och reglarna upp till vågräta säten i hammarbandet.

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

R = 45.0                     # regelns bredd
CC = 600.0
GLAPP = 80.0                 # en rasterregel utgår närmare än så intill en annan stående del
SANKT = 695.0                # den sänkta liggande under en dalbalks ände på gaveln, från väggens ände

KORTLING_Z = 2199.5797       # kortlingarnas underkant i innerväggarna under takfallen (som i Onshape-modellen)

ENKELT, AVVAXLING, DUBBELT = "enkelt", "avväxling", "dubbelt"
LODRAT, VINKELRAT = "lodrät", "vinkelrät"


@dataclass(frozen=True)
class Karm:
    """Utförandet vid en öppning."""
    dubbel: bool = False                     # en karmregel till utanför varje karmregel
    overstycke: str = ENKELT                 # ENKELT, AVVAXLING (också en liggande under hammarbandet) eller DUBBELT
    kortlingar: tuple[float, ...] = ()       # kortlingarnas läge (u) från öppningens början


def vaggens_oppningar(kod: str) -> list[Oppning]:
    """Väggens öppningar ovanför bjälklaget (källarens fönster i 2NO:s system hör till källarväggarna)."""
    return [o for o in OPPNINGAR.get(kod, []) if o.z1 > 0.0]


def plattor(v: Plan, langd: float, skarvar: Sequence[float] = (), oppningar: Sequence[Oppning] = (),
            hammarband: tuple[float, float] | None = (0.0, 0.0)) -> None:
    """Syll från 0 till langd och hammarband över intervallet (inget om None, hela väggen om (0, 0)), delade i
    skarvarna; syllen bryts vid öppningar till golvet."""
    def bitar(a: float, b: float, hal: Sequence[tuple[float, float]]) -> list[tuple[float, float]]:
        kanter = sorted({a, b} | {s for s in skarvar if a < s < b} | {e for h in hal for e in h if a < e < b})
        return [(x, y) for x, y in zip(kanter, kanter[1:]) if not any(h0 <= x and y <= h1 for h0, h1 in hal)]
    for a, b in bitar(0.0, langd, [(o.u0, o.u1) for o in oppningar if o.z0 <= 0.0]):
        v.syll(a, b)
    if hammarband is None:
        return
    h0, h1 = hammarband if hammarband != (0.0, 0.0) else (0.0, langd)
    for a, b in bitar(h0, h1, []):
        v.hammarband(a, b)


def hornstolpe(v: Plan, u: float, inat: int, namn: tuple[str, str], z1: float | None = None
               ) -> list[tuple[float, float]]:
    """Gavelns hörnstolpe vid änden u (inat = +1 i början, −1 i slutet): en regel i änden och en regel 95×45 på
    insidan (w 50–95) intill den. Ger delarnas u-intervall."""
    a = u if inat > 0 else u - R
    v.regel(a, z1=z1, namn=namn[0])
    b = a + R if inat > 0 else a - 95.0
    v.regel(b, z1=z1, b=95.0, w0=50.0, w1=95.0, namn=namn[1])
    return [(a, a + R), (b, b + 95.0)]


def oppning(v: Plan, o: Oppning, k: Karm = Karm()) -> list[tuple[float, float]]:
    """Karmreglar, överstycke, bröstningsregel och kortlingar vid öppningen. Ger de stående delarnas u-intervall."""
    staende = [(o.u0 - R, o.u0), (o.u1, o.u1 + R)]
    if k.dubbel:
        staende += [(o.u0 - 2 * R, o.u0 - R), (o.u1 + R, o.u1 + 2 * R)]
    for a, _ in staende:
        v.regel(a)
    topp = o.z1 + R
    v.liggande(o.u0, o.u1, o.z1)
    if k.overstycke == DUBBELT:
        v.liggande(o.u0, o.u1, o.z1 + R)
        topp += R
    tak = v.hojd - R
    if k.overstycke == AVVAXLING:
        v.liggande(o.u0, o.u1, v.hojd - 2 * R)
        tak -= R
    fonster = o.z0 > 0.0
    if fonster:
        v.liggande(o.u0, o.u1, o.z0 - R)
    for d in k.kortlingar:
        if fonster:
            v.regel(o.u0 + d, z1=o.z0 - R)
        if tak > topp:
            v.regel(o.u0 + d, z0=topp, z1=tak)
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
        st += oppning(v, o, (karmar or {}).get(o.kod.split("-")[-1], Karm()))
    fria = list(reglar)
    if raster_origo is not None:
        fria += raster(raster_origo, langd, st + [(u, u + R) for u in reglar], [(o.u0, o.u1) for o in opp], utan)
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
                       saten: dict[float, float]) -> tuple[Polygon, dict[float, float]]:
    """Lutande hammarband 45 (vinkelrätt mot lutningen) med överkanten ok, från start till slut (u och LODRAT eller
    VINKELRAT: änden lodrät, eller vinkelrät mot lutningen genom underkantens hörn), med ett vågrätt säte på varje regel
    (regelns u: sätets bredd från regelns låga sida, hela regelns bredd vid en lodrät ände). Ger hammarbandets profil och
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
    toppar = {}
    for u, s in saten.items():
        z = uk(u + s) if k > 0 else uk(u + R - s)
        profil = profil.difference(box(u, -1e5, u + R, z))
        toppar[u] = z
    return profil, toppar
