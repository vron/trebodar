"""Fasaderna utanpå ytterväggarnas regelverk: en grupp per vägg med utegips, ströläkt, spikläkt och panel.

Från stommen och utåt (w negativt i väggens system): utegips 10 mm, ströläkt 12×45 stående c/c 600 (och vid
karmarna), spikläkt 21×45 liggande c/c 600 (och vid karmarnas över- och underkant) och panel 22 mm (förenklad,
en skiva per vägg). Skikten går fram till fönstrens och dörrarnas karmar, vars aluminium ligger i panelens utsida.
Fasaden går ned till marken (MARKNIVA) och på väggarna med fasadsten till stenens överkant i bjälklagets
underkant (z −150). Vid takfötterna går den upp mellan takbalkarna (tänder) till takbalkarnas överkant i panelens
utsida, med en ströläkt mot varje takbalk och en spikläkt överst i varje fack; ovanför ligger takets luftspalt öppen
(luftintaget, U-03). I gavlarna slutar den mot takets hårdboard. I hörnen möts skikten var för sig (utegips mot
utegips, läkt mot läkt) och panelen täcker hela hörnet (fasad_u).
"""
from __future__ import annotations

from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

from modellering import Material, Montage

from trebodar import skelett as S
from trebodar.byggdelar import lagen
from trebodar.byggdelar import polygon as P
from trebodar.byggdelar.regelvagg import Plan
from trebodar.byggdelar.virke import fmt
from trebodar.hus.fonster_och_dorrar.oppningar import OPPNINGAR
from trebodar.hus.grund import fasadsten
from trebodar.hus.tak.tak import tak_underkant
from trebodar.material import C24_LAKT, PANEL_FALUROD, PANEL_JARNVITRIOL, UTEGIPS

Z_UK = -S.H_BJALKLAG
# marken vid fasaden (u, z) per vägg: panelens underkant, utom där fasadstenen går upp till bjälklaget (STENVAGGAR).
# Ur markmodellen (K-06:s fyllning mot källarväggarna, Onshape-modellens mark och makadamen runt plattan på mark),
# högsta punkt 0–150 mm utanför väggen och grundens delar i fasadens skikt, 2 mm över den sluttande marken;
# marknivåerna är inte bestämda (modell-todo). 2NV står på källarväggen och slutar i Z_UK.
MARKNIVA: dict[str, tuple[tuple[float, float], ...]] = {
    "1NO": ((-65, -250), (4435, -250)),
    "1SO": ((-95, -222), (2555, -222), (3755, -497), (5105, -497), (5130, -250), (12275, -250)),
    "1SV": ((-65, -398), (2285, -222), (4435, -223)),
    "1NV": ((0, -250), (1500, -250), (1525, -394), (4890, -394)),
    "2NO": ((-65, -250), (10, -250), (35, -1450), (4935, -1450)),
    "2SV": ((160, -250), (5160, -250)),
    "2SO": ((0, -250), (3590, -250)),
    "3SO": ((-95, -250), (1405, -250)),
    "3NO": ((160, -2250), (1985, -2249), (4385, -1458), (4410, -1421), (4660, -1419)),
    "3NV": ((-95, -1419), (680, -1395), (11280, -450), (11475, -450)),
    "3SV": ((-65, -450), (4335, -450), (4360, -250), (4435, -250)),
}
STENVAGGAR = {kod for b in fasadsten.BEKLADNAD if b.z1 >= Z_UK - 1e-6 for kod in b.vaggar}
UTEGIPS_T, STRO_T, SPIK_T, PANEL_T = 10.0, 12.0, 21.0, 22.0
LAKT_B = 45.0
CC = 600.0
GAVLAR = {"1NO", "1SV", "2NO", "2SV", "3NO", "3SV"}
# panelens utförande per huskropp (byt material här för att prova andra kulörer)
PANEL = {1: PANEL_FALUROD, 2: PANEL_JARNVITRIOL, 3: PANEL_JARNVITRIOL}
# renderingens skruvrader i panelen följer spikläkten: c/c CC från fasadens underkant, mitt på läkten
assert all((dict(p.rendering)["skruv_cc"], dict(p.rendering)["skruv_start"]) == (CC, Z_UK + LAKT_B / 2)
           for p in PANEL.values())
STOMMENS_UTSIDA = Polygon(S.KONTUR).buffer(S.STOMME_UT, join_style=2)


# skiktgrupperna med djup (inre, yttre) från stommens utsida, för hörnen
UG_DJUP = (0.0, UTEGIPS_T)
LAKT_DJUP = (UTEGIPS_T, UTEGIPS_T + STRO_T + SPIK_T)
PANEL_DJUP = (UTEGIPS_T + STRO_T + SPIK_T, S.T_FASAD)


def fasad_u(kod: str, djup: tuple[float, float] = PANEL_DJUP) -> tuple[float, float]:
    """Skiktgruppens utsträckning längs väggen (u), djup (inre, yttre) från stommens utsida. Långsidornas stomme
    står mellan gavlarnas och gavlarnas stomme går till långsidornas insida i innerhörnen. I ytterhörnen går gavelns
    skikt runt hörnet, var och ett till den andra väggens motsvarande skikt (utegipsen till utegipsen, läkten till
    läkten och panelen till panelens utsida), och långsidans fram till gavelns; i innerhörnen går långsidans skikt ut
    i hörnet till gavelns och gavelns till långsidans. Panelen täcker då hela hörnet."""
    a, b = djup
    v = S.YTTERVAGGAR[kod]
    pl = v.placering()
    ut = []
    for u, r in ((0.0, -1.0), (v.langd, 1.0)):
        inne = STOMMENS_UTSIDA.contains(Point(pl.punkt((u + r * 10.0, -10.0, 0.0))[:2]))     # huset fortsätter
        if kod in GAVLAR:
            d = -(S.T_STOMME + b) if inne else b
        else:
            d = -a if inne else S.T_STOMME + a
        ut.append(u + r * d)
    return ut[0], ut[1]


def fasadens_u(kod: str) -> tuple[float, float]:
    """Hela fasadens utsträckning längs väggen (alla skikt)."""
    us = [fasad_u(kod, d) for d in (UG_DJUP, LAKT_DJUP, PANEL_DJUP)]
    return min(u for u, _ in us), max(u for _, u in us)


def _lagen(fasta: set[float], cc: list[float], b: float = LAKT_B) -> list[float]:
    """Läktlägen: de fasta (ändar, öppningar; av två som skulle överlappa den lägre) och de jämnt fördelade som inte
    överlappar en fast."""
    ut: list[float] = []
    for v in sorted(fasta):
        if not ut or v - ut[-1] >= b:
            ut.append(v)
    for v in cc:
        if all(abs(v - f) >= b for f in ut):
            ut.append(v)
    return sorted(ut)


def mark_vid(kod: str, u: float) -> float:
    """Marken vid fasaden i u (MARKNIVA; Z_UK där marken inte når fasaden)."""
    m = MARKNIVA.get(kod, ((0.0, Z_UK), (1.0, Z_UK)))
    for (ua, za), (ub, zb) in zip(m, m[1:]):
        if ua <= u <= ub:
            return za if ub == ua else za + (zb - za) * (u - ua) / (ub - ua)
    return float(m[0][1] if u < m[0][0] else m[-1][1])


def underkant(kod: str) -> list[tuple[float, float]]:
    """Fasadens underkant (u, z) över hela fasaden: marken (förlängd vågrätt till fasadens ändar), eller Z_UK där
    fasadstenen går upp till bjälklaget."""
    u0, u1 = fasadens_u(kod)
    mark = MARKNIVA.get(kod)
    if mark is None or kod in STENVAGGAR:
        return [(u0, Z_UK), (u1, Z_UK)]
    inne = [(float(u), float(z)) for u, z in mark if u0 < u < u1]
    return [(u0, mark_vid(kod, u0))] + inne + [(u1, mark_vid(kod, u1))]


def tander(kod: str) -> list[tuple[float, float, float]]:
    """Facken mellan takbalkarna (och takstolarnas delar) som går ut genom långsidans fasad ovanför hammarbandet:
    (u0, u1, z1), där fasaden går upp till takbalkarnas överkant z1 i panelens utsida."""
    t, v = S.TAKFALL[kod], S.YTTERVAGGAR[kod]
    x_ut = t.x_utsida - t.riktning * S.T_FASAD
    zon = box(min(t.x_utsida, x_ut), S.H_VAGG, max(t.x_utsida, x_ut), t.z_overkant(t.x_utsida))
    fria = [fasadens_u(kod)]
    for _, q, y0, y1 in lagen.takets_stomme():
        if q.intersection(zon).area > 1.0:
            a, b = sorted((y - v.origo[1]) * v.u[1] for y in (y0, y1))
            fria = [d for c, e in fria for d in ((c, min(e, a)), (max(c, b), e)) if d[1] - d[0] > 1.0]
    return [(a, b, t.z_overkant(x_ut)) for a, b in fria]


def kontur(kod: str) -> Polygon:
    """Fasadens kontur i väggens (u, z), alla skikt (varje skiktgrupp skärs till sin utsträckning, fasad_u)."""
    v = S.YTTERVAGGAR[kod]
    u0, u1 = fasadens_u(kod)
    under = underkant(kod)
    if kod not in GAVLAR:
        vagg = Polygon(under + [(u1, S.H_VAGG), (u0, S.H_VAGG)])
        return unary_union([vagg] + [box(a, S.H_VAGG, b, z1) for a, b, z1 in tander(kod)])
    # gavel: överkanten följer takplanen; brytpunkter vid nockar och dalar
    y = v.origo[1] - v.w[1] * S.T_FASAD / 2           # mitt i fasadskiktet
    x_av = lambda u: v.origo[0] + v.u[0] * u           # noqa: E731
    xs = {x_av(u0), x_av(u1)}
    xs |= {k.nock for k in S.HUSKROPPAR.values()} | {S.BALKAR["DB2"].x, S.BALKAR["DB4"].x}
    xa, xb = sorted((x_av(u0), x_av(u1)))
    topp = []
    for x in sorted(x for x in xs if xa - 1e-6 <= x <= xb + 1e-6):
        z = tak_underkant(x, y)
        assert z is not None, (kod, x)
        topp.append(((x - v.origo[0]) * v.u[0], z))
    topp.sort()
    return Polygon(under + topp[::-1])


def utsida(kod: str) -> Montage:
    hela = kontur(kod)
    karmar = [o.karm for o in OPPNINGAR.get(kod, [])]                  # fasaden går fram till karmen
    hal = [box(*k) for k in karmar]
    oppen = unary_union(hal) if hal else Polygon()
    m = Montage(f"Utsida {kod}", beskrivning=f"Fasad på väggen {kod}: utegips, ströläkt, spikläkt, panel")
    w = 0.0

    def fas(djup: tuple[float, float]) -> Polygon:
        a, b = fasad_u(kod, djup)
        return hela.intersection(box(a, -1e5, b, 1e5))

    def skikt(namn: str, typ: str, t: float, material: Material, del_namn: str, djup: tuple[float, float]) -> None:
        p = Plan(kod, f"{namn} {kod}", t, beskrivning=material.beskrivning, material=material)
        for g in P.polygoner(fas(djup).difference(oppen)):
            p.skiva(P.kontur(g), P.hal(g), w - t, w, typ, material, f"{del_namn} {kod}")
        m.lagg(p.montage())

    def lakt(namn: str, typ: str, t: float, bitar: list[Polygon]) -> None:
        p = Plan(kod, f"{namn} {kod}", t, beskrivning=f"{namn} {fmt(t)}×45 C24", material=C24_LAKT)
        for b in bitar:
            for q in P.polygoner(b.intersection(fas(LAKT_DJUP)).difference(oppen), 45 * 100):
                p.profil(P.kontur(q), w - t, w, typ=typ)
        m.lagg(p.montage())

    skikt("Utegips", "UG", UTEGIPS_T, UTEGIPS, "Utegips 10 mm", UG_DJUP)
    w -= UTEGIPS_T
    u0, u1 = fasad_u(kod, LAKT_DJUP)
    fasl = fas(LAKT_DJUP)
    zt = fasl.bounds[3] if kod in GAVLAR else S.H_VAGG
    tand = [] if kod in GAVLAR else [(max(a, u0), min(b, u1), z1) for a, b, z1 in tander(kod)
                                     if min(b, u1) - max(a, u0) >= 3 * LAKT_B]
    fasta = {u0, u1 - LAKT_B}
    for ku0, _, ku1, _ in karmar:
        fasta |= {ku0 - LAKT_B, ku1}
    fasta = {u for u in fasta if u0 - 1e-6 <= u <= u1 - LAKT_B + 1e-6}
    staende = _lagen(fasta, [u0 + CC * k for k in range(1, int((u1 - u0) // CC) + 1) if u0 + CC * k < u1 - LAKT_B])
    zu = fasl.bounds[1]
    lakt("Ströläkt", "SR", STRO_T, [box(u, zu, u + LAKT_B, zt) for u in staende]
         + [box(u, S.H_VAGG, u + LAKT_B, z1) for a, b, z1 in tand for u in (a, b - LAKT_B)])
    w -= STRO_T
    fasta = {Z_UK, zu}                                   # och vid fasadens underkant
    for _, kz0, _, kz1 in karmar:
        fasta |= {z for z in (kz0 - LAKT_B, kz1) if z >= zu - 1e-6}
    # raderna c/c CC från bjälklagets underkant, uppåt och nedåt till marken
    rader = _lagen(fasta, [Z_UK + CC * k for k in range(-int((Z_UK - zu) // CC), int((zt - Z_UK) // CC) + 1) if k])
    lakt("Spikläkt", "SP", SPIK_T, [box(u0, z, u1, z + LAKT_B) for z in rader]
         + [box(a, z1 - LAKT_B, b, z1) for a, b, z1 in tand])
    w -= SPIK_T
    panel = PANEL[int(kod[0])]
    skikt("Panel", "PA", PANEL_T, panel, f"Panel 22 mm {panel.namn.removeprefix('Panel ')}", PANEL_DJUP)
    return m


def montage() -> Montage:
    m = Montage("Fasad", beskrivning="Ytterväggarnas utsida: utegips, ströläkt, spikläkt och panel")
    for kod in S.YTTERVAGGAR:
        m.lagg(utsida(kod), S.YTTERVAGGAR[kod].placering())
    return m
