"""Fasaderna utanpå ytterväggarnas regelverk: en grupp per vägg med utegips, ströläkt, spikläkt och panel.

Från stommen och utåt (w negativt i väggens system): utegips 10 mm, ströläkt 12×45 stående c/c 600 (och vid
karmarna), spikläkt 21×45 liggande c/c 600 (och vid karmarnas över- och underkant) och panel 22 mm (förenklad,
en skiva per vägg). Skikten går fram till fönstrens och dörrarnas karmar, vars aluminium ligger i panelens utsida.
Fasaden går ned till marken (MARKNIVA), utom där fasadstenen går upp till bjälklagets underkant (z −150) och över
källardörrarna, där den slutar i bjälklagets underkant. Vid takfötterna går den upp mellan takbalkarna (tänder) till takbalkarnas överkant i panelens
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
from trebodar.hus.grund import fasadsten, kallarvaggar
from trebodar.hus.tak.tak import tak_underkant
from trebodar.material import ALU_RAL3009, ALU_RAL7012, C24_LAKT, PANEL_FALUROD, PANEL_JARNVITRIOL, UTEGIPS

Z_UK = -S.H_BJALKLAG
# marken vid fasaden (u, z) per vägg: panelens underkant, utom där fasadstenen går upp till bjälklaget (STENVAGGAR,
# där linjen gäller stuprören). Ur den byggda modellen med verktyg/modellanalys/marknivaer.py: det högsta av marken,
# avsatserna, återfyllningen och grunden i ett band från stommen till 150 mm utanför panelen, 2,1–12,5 mm över det.
# Körs om när marken ändras (marknivåerna är inte bestämda, modell-todo).
MARKNIVA: dict[str, tuple[tuple[float, float], ...]] = {
    "1NO": ((-65, -1339), (185, -1339), (195, -739), (4425, -739)),
    "1SO": ((-138, -222), (2542, -222), (2552, -223), (3752, -497), (4562, -497), (4572, -306), (4962, -306),
            (4972, -152), (6182, -152), (6192, -306), (6582, -306), (6592, -461), (6882, -461), (6892, -616),
            (7182, -616), (7192, -770), (7482, -770), (7492, -925), (7762, -951), (7772, -737), (12282, -737),
            (12292, -1337), (12312, -1338)),
    "1SV": ((-65, -398), (2275, -223), (4435, -222)),
    "1NV": ((0, -409), (250, -409), (260, -394), (4930, -394)),
    "2NO": ((-65, -1449), (4885, -1449), (4895, -2247), (4935, -2247)),
    "2NV": ((-138, -2247), (832, -2247), (842, -226), (852, -147), (902, -147)),
    "2SV": ((105, -679), (1195, -694), (5015, -409), (5135, -409), (5145, -497), (5165, -497), (5175, -409),
            (5195, -409), (5205, -497), (5215, -497)),
    "2SO": ((80, -739), (3410, -841), (3420, -1441), (3630, -1448)),
    "3NO": ((105, -2247), (1985, -2247), (4385, -1455), (4395, -1419), (4655, -1419)),
    "3NV": ((-138, -1417), (11472, -1062), (11482, -960), (11512, -960)),
    "3SV": ((-65, -959), (4385, -662), (4405, -662), (4415, -774), (4435, -773)),
    "3SO": ((-138, -762), (992, -762), (1002, -679), (1402, -679)),
}
STENVAGGAR = {kod for b in fasadsten.BEKLADNAD if b.z1 >= Z_UK - 1e-6 for kod in b.vaggar}
UTEGIPS_T, STRO_T, SPIK_T, PANEL_T = 10.0, 12.0, 21.0, 22.0
LAKT_B = 45.0
CC = 600.0
GAVLAR = {"1NO", "1SV", "2NO", "2SV", "3NO", "3SV"}
# panelens utförande och fönstrens och dörrarnas aluminium per huskropp (byt material här för att prova andra kulörer)
PANEL = {1: PANEL_FALUROD, 2: PANEL_JARNVITRIOL, 3: PANEL_JARNVITRIOL}
ALUMINIUM = {1: ALU_RAL3009, 2: ALU_RAL7012, 3: ALU_RAL7012}
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


def till_bjalklaget(kod: str) -> list[tuple[float, float]]:
    """Intervallen (u0, u1) längs väggen där fasaden slutar i bjälklagets underkant: fasadsten upp till bjälklaget
    och källardörrar."""
    v = S.YTTERVAGGAR[kod]
    u0, u1 = fasadens_u(kod)
    ut = []
    for b in fasadsten.BEKLADNAD:
        if b.z1 >= Z_UK - 1e-6 and kod in b.vaggar:
            i = b.vaggar.index(kod)
            a = fasadsten._u(kod, b.start) if i == 0 else u0
            e = fasadsten._u(kod, b.slut) if i == len(b.vaggar) - 1 else u1
            ut.append((min(a, e), max(a, e)))
    langs_x = abs(v.u[0]) > 0.5
    for _, rikt, liv, a, e in kallarvaggar.dorrar():
        if (rikt == "h") == langs_x and abs(liv - (v.origo[1] if langs_x else v.origo[0])) < 1.0:
            o, r = (v.origo[0], v.u[0]) if langs_x else (v.origo[1], v.u[1])
            ut.append(tuple(sorted(((a - o) * r, (e - o) * r))))      # type: ignore[arg-type]
    return ut


def underkant(kod: str) -> list[tuple[float, float]]:
    """Fasadens underkant (u, z) över hela fasaden: marken (förlängd vågrätt till fasadens ändar), och Z_UK där
    fasaden slutar i bjälklagets underkant (till_bjalklaget), med lodräta steg vid intervallens kanter."""
    u0, u1 = fasadens_u(kod)
    iv: list[list[float]] = []
    for a, b in sorted(till_bjalklaget(kod)):              # intervallen ihopslagna
        if iv and a <= iv[-1][1] + 1.0:
            iv[-1][1] = max(iv[-1][1], b)
        else:
            iv.append([a, b])

    def z(u: float) -> float:
        inne = any(a - 1e-6 <= u <= b + 1e-6 for a, b in iv)
        return Z_UK if inne or kod not in MARKNIVA else mark_vid(kod, u)
    kanter = {e for a, b in iv for e in (a, b) if u0 < e < u1}
    ut: list[tuple[float, float]] = []
    for u in sorted({u0, u1} | {float(u) for u, _ in MARKNIVA.get(kod, ()) if u0 < u < u1} | kanter):
        if u in kanter:                                     # steget: först sidan före kanten, sedan efter
            ut += [(u, z(u - 0.5)), (u, z(u + 0.5))]
        else:
            ut.append((u, z(u)))
    return [p for k, p in enumerate(ut) if k == 0 or p != ut[k - 1]]


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
