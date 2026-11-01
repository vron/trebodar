"""Fasaderna utanpå ytterväggarnas regelverk: en grupp per vägg med utegips, ströläkt, spikläkt och panel.

Från stommen och utåt (w negativt i väggens system): utegips 10 mm, ströläkt 12×45 stående c/c 600 (och vid
öppningarna), spikläkt 21×45 liggande c/c 600 (och vid öppningarnas över- och underkant) och panel 22 mm (förenklad,
en skiva per vägg). Fasaden börjar i bjälklagets underkant (z −150), där fasadstenen tar vid, och slutar vid
takfötterna under takbalkarnas sätesplan (z 2 490) och i gavlarna mot takets hårdboard. I ytterhörnen går
gavelns skikt runt hörnet; i innerhörnen går långsidans skikt ut i hörnet.
"""
from __future__ import annotations

from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from modellering import Material, Montage

from trebodar import skelett as S
from trebodar.byggdelar import polygon as P
from trebodar.byggdelar.regelvagg import Plan
from trebodar.byggdelar.virke import fmt
from trebodar.hus.fonster_och_dorrar.oppningar import OPPNINGAR
from trebodar.hus.tak.tak import REGIONER
from trebodar.material import C24_LAKT, PANEL_FALUROD, PANEL_JARNVITRIOL, UTEGIPS

Z_UK = -S.H_BJALKLAG
UTEGIPS_T, STRO_T, SPIK_T, PANEL_T = 10.0, 12.0, 21.0, 22.0
LAKT_B = 45.0
CC = 600.0
GAVLAR = {"1NO", "1SV", "2NO", "2SV", "3NO", "3SV"}
# panelens utförande per huskropp (byt material här för att prova andra kulörer)
PANEL = {1: PANEL_FALUROD, 2: PANEL_JARNVITRIOL, 3: PANEL_FALUROD}
# renderingens skruvrader i panelen följer spikläkten: c/c CC från fasadens underkant, mitt på läkten
assert all((dict(p.rendering)["skruv_cc"], dict(p.rendering)["skruv_start"]) == (CC, Z_UK + LAKT_B / 2)
           for p in PANEL.values())
# fasadens utsträckning längs väggen (u), med hörnen enligt ovan
FASAD_U = {"1SO": (-95.0, 12275.0), "1NO": (-65.0, 4435.0), "1SV": (-65.0, 4435.0), "1NV": (0.0, 4890.0),
           "2NO": (-65.0, 4935.0), "2SO": (0.0, 3590.0), "2NV": (-95.0, 905.0), "2SV": (160.0, 5160.0),
           "3NO": (160.0, 4660.0), "3NV": (-95.0, 11475.0), "3SV": (-65.0, 4435.0), "3SO": (-95.0, 1405.0)}


def tak_underkant(x: float, y: float) -> float | None:
    """Takets hårdboards undersida (takbalkarnas överkant) i punkten (x, y), om taket täcker den."""
    z = []
    for kod, regioner in REGIONER.items():
        t = S.TAKFALL[kod]
        for r in regioner:
            xa, xb = sorted((r.nedre.x, r.nock.x))
            if r.y0 - 1e-6 <= y <= r.y1 + 1e-6 and xa - 1e-6 <= x <= xb + 1e-6:
                z.append(t.z_overkant(x))
    return min(z) if z else None


def _lagen(fasta: set[float], cc: list[float], b: float = LAKT_B) -> list[float]:
    """Läktlägen: de fasta (ändar, öppningar) och de jämnt fördelade som inte överlappar en fast."""
    ut = sorted(fasta)
    for v in cc:
        if all(abs(v - f) >= b for f in ut):
            ut.append(v)
    return sorted(ut)


def kontur(kod: str) -> Polygon:
    """Fasadens kontur i väggens (u, z)."""
    v = S.YTTERVAGGAR[kod]
    u0, u1 = FASAD_U[kod]
    if kod not in GAVLAR:
        return box(u0, Z_UK, u1, S.H_VAGG)
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
    return Polygon([(u0, Z_UK), (u1, Z_UK)] + topp[::-1])


def utsida(kod: str) -> Montage:
    fas = kontur(kod)
    hal = [box(o.u0, o.z0, o.u1, o.z1) for o in OPPNINGAR.get(kod, [])]
    oppen = unary_union(hal) if hal else Polygon()
    m = Montage(f"Utsida {kod}", beskrivning=f"Fasad på väggen {kod}: utegips, ströläkt, spikläkt, panel")
    w = 0.0

    def skikt(namn: str, typ: str, t: float, material: Material, del_namn: str) -> None:
        p = Plan(kod, f"{namn} {kod}", t, beskrivning=material.beskrivning, material=material)
        for g in P.polygoner(fas.difference(oppen)):
            p.skiva(P.kontur(g), P.hal(g), w - t, w, typ, material, f"{del_namn} {kod}")
        m.lagg(p.montage())

    def lakt(namn: str, typ: str, t: float, bitar: list[Polygon]) -> None:
        p = Plan(kod, f"{namn} {kod}", t, beskrivning=f"{namn} {fmt(t)}×45 C24", material=C24_LAKT)
        for b in bitar:
            for q in P.polygoner(b.intersection(fas).difference(oppen), 45 * 100):
                p.profil(P.kontur(q), w - t, w, typ=typ)
        m.lagg(p.montage())

    skikt("Utegips", "UG", UTEGIPS_T, UTEGIPS, "Utegips 10 mm")
    w -= UTEGIPS_T
    u0, u1 = FASAD_U[kod]
    zt = fas.bounds[3]
    fasta = {u0, u1 - LAKT_B}
    for o in OPPNINGAR.get(kod, []):
        fasta |= {o.u0 - LAKT_B, o.u1}
    fasta = {u for u in fasta if u0 - 1e-6 <= u <= u1 - LAKT_B + 1e-6}
    lagen = _lagen(fasta, [u0 + CC * k for k in range(1, int((u1 - u0) // CC) + 1) if u0 + CC * k < u1 - LAKT_B])
    lakt("Ströläkt", "SR", STRO_T, [box(u, Z_UK, u + LAKT_B, zt) for u in lagen])
    w -= STRO_T
    fasta = {Z_UK}
    for o in OPPNINGAR.get(kod, []):
        fasta |= {z for z in (o.z0 - LAKT_B, o.z1) if z >= Z_UK - 1e-6}
    rader = _lagen(fasta, [Z_UK + CC * k for k in range(1, int((zt - Z_UK) // CC) + 1)])
    lakt("Spikläkt", "SP", SPIK_T, [box(u0, z, u1, z + LAKT_B) for z in rader])
    w -= SPIK_T
    panel = PANEL[int(kod[0])]
    skikt("Panel", "PA", PANEL_T, panel, f"Panel 22 mm {panel.namn.removeprefix('Panel ')}")
    return m


def montage() -> Montage:
    m = Montage("Fasad", beskrivning="Ytterväggarnas utsida: utegips, ströläkt, spikläkt och panel")
    for kod in S.YTTERVAGGAR:
        m.lagg(utsida(kod), S.YTTERVAGGAR[kod].placering())
    return m
