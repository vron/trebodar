"""Garderoben i sovrummet i mittre huskroppen (ärende #16): inbyggd, från stolpen LD4_1 längs 2C och runt kaminens
kåpa fram till trapphålets vägg L7, med fronten i linje med L6 och ett snett hörn 600 × 600 mot fickdörren ID6.

Väggarna (lägena i invandigt/lattvaggar.py: GC vid stolpen, GB det sneda hörnet och GA fronten) är lätta väggar 45×70
C24 med syll, reglar och hammarband under innertaket. Mot rummet har de samma skikt som de andra innerväggarna, OSB 12
och gips 13, upp till innertaket (snett som taket); inuti gips 13 upp till garderobens tak. Hörnen är gerade och
skikten slutar mot stolpen, L7:s skikt och L6:s skikt, som går runt L7:s ände. Fronten har två öppningar (deras
smyg vitmålad furu 15) med par av dörrar, blad 22 i trä i liv med väggen. Garderobens tak, gips 13 på överstyckenas
höjd, stänger den uppåt; ovanför är ett tomrum upp till innertaket. Insidan bakom är de befintliga väggarnas skikt
(2C, kåpans väggar L14 och L13, L7).
"""
from __future__ import annotations

from shapely.geometry import LineString, Polygon
from shapely.geometry import box as plan_box

from modellering import Del, Form, Kapad, Montage, Placering, box, prisma

from trebodar import skelett as S
from trebodar.byggdelar.virke import fmt, virke_i_lada
from trebodar.hus.invandigt.lattvaggar import GARDEROB, H_VIRKE, LATTA, T
from trebodar.hus.invandigt.skikt import GIPS_YTTRE_W, innertakets_fall
from trebodar.hus.invandigt.vaggar import skiktets_tjocklek, vaggdef
from trebodar.hus.stomme.prefab.stolpar.stolpar import LD4_1, LD4_1_B
from trebodar.material import C24, FONSTERTRA, FURU, GIPS, OSB

VAGGAR = [lv for lv in LATTA if lv.grupp == GARDEROB]                 # GC, GB, GA i ordning längs rummets sida
GIPS_T, OSB_T, SMYG_T, BLAD_T = 13.0, 12.0, 15.0, 22.0
SPEL = 3.0                                                            # mellan bladen och ovanför dem
H_OPPNING = 2100.0                                                    # öppningarnas höjd
TAK_Z = H_OPPNING + H_VIRKE                                           # garderobens tak på överstyckena
HOJD = 6000.0                                                         # prismornas höjd före kapningen vid taket
POST_NORR = LD4_1[1] - LD4_1_B / 2                                    # stolpens norra sida (mot sovrummet)
# frontens öppningar i GA:s u: väster om kåpan (djup) och framför kåpan (grund), med två reglar emellan i linje
# med kåpans vägg L14
OPPNINGAR = ((90.0, 1038.0), (1128.0, 2158.0))
REGLAR = {"GC": (236.0,), "GB": (60.0, 400.0, 744.0), "GA": (0.0, 45.0, 1038.0, 1083.0, 2158.0, 2203.0)}


def _linje() -> list[tuple[float, float]]:
    """Rummets sida av stommen (w = 0) genom väggarna, från stolpen till L7:s skikt."""
    a = VAGGAR[-1]
    slut = (a.origo[0] + a.u[0] * a.langd, a.origo[1] + a.u[1] * a.langd)
    return [lv.origo for lv in VAGGAR] + [slut]


def _offset(d: float) -> list[tuple[float, float]]:
    """Linjen förskjuten d mot garderobens insida (vänster i linjens riktning), gerad i hörnen."""
    if abs(d) < 1e-9:
        return _linje()
    return [(float(x), float(y)) for x, y in LineString(_linje()).offset_curve(d, join_style="mitre").coords]


def _band(i: int, d0: float, d1: float) -> Polygon:
    """Skiktet mellan d0 och d1 längs vägg i (VAGGAR), gerat mot grannväggarna."""
    a, b = _offset(d0), _offset(d1)
    return Polygon([a[i], a[i + 1], b[i + 1], b[i]])


def _klipp(i: int, p: Polygon) -> Polygon:
    """Stommen och insidan vid stolpen slutar mot stolpens norra sida (GC)."""
    if VAGGAR[i].kod == "GC":
        x0, y0, x1, _ = p.bounds
        return p.intersection(plan_box(x0 - 1.0, y0 - 1.0, x1 + 1.0, POST_NORR))
    return p


def _tak(p: Polygon, ned: float = 0.0) -> list[tuple[tuple[float, float, float], tuple[float, float, float]]]:
    """Innertakets plan över ytan (punkt, normal uppåt), ned mm under det: ett per takfall ytan ligger under."""
    c = p.centroid
    fall = {}
    for x, y in [*list(p.exterior.coords)[:-1], (c.x, c.y)]:
        t = innertakets_fall(x + (c.x - x) * 0.05, y + (c.y - y) * 0.05)
        if t:
            fall[t.kod] = t
    ut = []
    for t in fall.values():
        def z(x: float) -> float:
            return t.z_overkant(x) + GIPS_YTTRE_W[0] / S.COS - ned
        ut.append(((c.x, c.y, z(c.x)), (z(c.x) - z(c.x + 1.0), 0.0, 1.0)))
    return ut


def _upp_till_taket(p: Polygon, z0: float, ned: float = 0.0) -> Form:
    """Prisma över ytan från z0 upp till innertaket (ned mm under det)."""
    f: Form = prisma(list(p.exterior.coords)[:-1], HOJD - z0, z0=z0)
    for pkt, n in _tak(p, ned):
        f = Kapad(f, pkt, n)
    return f


def _yta(i: int, d0: float, d1: float) -> Polygon:
    return _klipp(i, _band(i, d0, d1))


def _oppningar_x() -> list[tuple[float, float]]:
    ga = VAGGAR[-1]
    return [(ga.origo[0] + u0, ga.origo[0] + u1) for u0, u1 in OPPNINGAR]


def _halen(y0: float, y1: float, z1: float = H_OPPNING) -> list[Form]:
    return [box(x0, x1, y0 - 1.0, y1 + 1.0, -1.0, z1) for x0, x1 in _oppningar_x()]


def _stomme() -> Montage:
    m = Montage("Stomme", beskrivning="Lätta väggar 45×70 C24: syll, reglar, överstycken och hammarband under taket")
    for i, lv in enumerate(VAGGAR):
        band = _yta(i, 0.0, T)
        n = {"S": 0, "R": 0, "H": 0, "L": 0}

        def lagg(typ: str, namn: str, form: Form) -> None:
            n[typ] += 1
            m.lagg(Del(namn, form, C24), Placering(), f"{lv.kod}-{typ}{n[typ]:02d}")
        # syllen, bruten vid frontens öppningar
        syll: Form = prisma(list(band.exterior.coords)[:-1], H_VIRKE)
        if lv.kod == "GA":
            for hal in _halen(lv.origo[1], lv.origo[1] + T):
                syll = syll - hal
        lagg("S", f"Syll 45×{fmt(T)} garderob {lv.kod}", syll)
        for bit in _vid_nocken(band):
            lagg("H", f"Hammarband 45×{fmt(T)} garderob {lv.kod}",
                 Kapad(_upp_till_taket(bit, 0.0), *_under(bit, H_VIRKE)))
        pl = vaggdef(lv.kod).placering()
        for u in REGLAR[lv.kod]:
            r = Polygon([pl.punkt((uu, w, 0.0))[:2] for uu, w in ((u, 0.0), (u + 45.0, 0.0), (u + 45.0, T), (u, T))])
            lagg("R", f"Regel 45×{fmt(T)} garderob {lv.kod}", _upp_till_taket(r, H_VIRKE, H_VIRKE))
        if lv.kod == "GA":
            for x0, x1 in _oppningar_x():
                y0, y1 = lv.origo[1], lv.origo[1] + T
                lagg("L", f"Överstycke 45×{fmt(T)} garderob", box(x0, x1, y0, y1, H_OPPNING, TAK_Z))
                xm = (x0 + x1) / 2 - 22.5
                lagg("R", f"Kortling 45×{fmt(T)} garderob",
                     _upp_till_taket(plan_box(xm, y0, xm + 45.0, y1), TAK_Z, H_VIRKE))
    return m


def _vid_nocken(p: Polygon) -> list[Polygon]:
    """Ytan delad vid nockbalkarnas linjer (ett takplan per del)."""
    bitar = [p]
    for b in S.BALKAR.values():
        if b.typ == "nock":
            ny = []
            for q in bitar:
                x0, y0, x1, y1 = q.bounds
                if x0 < b.x < x1:
                    ny += [q.intersection(plan_box(x0 - 1, y0 - 1, b.x, y1 + 1)),
                           q.intersection(plan_box(b.x, y0 - 1, x1 + 1, y1 + 1))]
                else:
                    ny.append(q)
            bitar = ny
    return [q for q in bitar if isinstance(q, Polygon) and q.area > 1.0]


def _under(p: Polygon, ned: float) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    """Planet ned mm under innertaket över ytan, med normalen nedåt (för att ta bort det som ligger under)."""
    (pkt, n), *_ = _tak(p, ned)
    return pkt, (-n[0], -n[1], -n[2])


def _skikt() -> Montage:
    m = Montage("Skikt", beskrivning="Mot rummet OSB 12 och gips 13 upp till innertaket, inuti gips 13")
    ga = VAGGAR[-1]
    for i, lv in enumerate(VAGGAR):
        utsida = _band(i, -skiktets_tjocklek(lv.kod, -1, lv.langd / 2), 0.0)
        for namn, d0, d1, mat, typ in (("OSB", -OSB_T, 0.0, OSB, "OS"),
                                        ("Gips", -OSB_T - GIPS_T, -OSB_T, GIPS, "GI")):
            assert utsida.contains(_band(i, d0, d1).buffer(-0.01)), "skikten mot rummet är OSB och gips"
            f = _upp_till_taket(_band(i, d0, d1), 0.0)
            if lv.kod == "GA":
                for hal in _halen(ga.origo[1] + d0, ga.origo[1] + d1):
                    f = f - hal
            m.lagg(Del(f"{namn} {fmt(d1 - d0)} garderob {lv.kod}", f, mat), Placering(), f"{lv.kod}-{typ}01")
        yta = _yta(i, T, T + GIPS_T)
        insida: Form = prisma(list(yta.exterior.coords)[:-1], TAK_Z)
        if lv.kod == "GA":
            for hal in _halen(ga.origo[1] + T, ga.origo[1] + T + GIPS_T):
                insida = insida - hal
        m.lagg(Del(f"Gips {fmt(GIPS_T)} garderob {lv.kod} insida", insida, GIPS), Placering(), f"{lv.kod}-GI02")
    # garderobens tak: inuti, mellan insidans gips och de befintliga väggarnas skikt
    inre = _offset(T + GIPS_T)
    x_l7 = 7278.0 - skiktets_tjocklek("L7", 1, 100.0)
    y_l13 = vaggdef("L13").origo[1] - skiktets_tjocklek("L13", -1, 100.0)
    x_l14 = vaggdef("L14").origo[0] - T - skiktets_tjocklek("L14", 1, 100.0)
    y_2c = vaggdef("2C").origo[1] - skiktets_tjocklek("2C", -1, 2000.0)
    x_post = LD4_1[0] + LD4_1_B / 2
    tak = Polygon([(inre[0][0], POST_NORR), inre[1], inre[2], (x_l7, inre[3][1]), (x_l7, y_l13), (x_l14, y_l13),
                   (x_l14, y_2c), (x_post, y_2c), (x_post, POST_NORR)])
    m.lagg(Del(f"Gips {fmt(GIPS_T)} garderobens tak", prisma(list(tak.exterior.coords)[:-1], GIPS_T, z0=TAK_Z),
               GIPS), Placering(), "G-TAK")
    return m


def _dorrar() -> Montage:
    """Frontens öppningar: smyg av vitmålad furu runt om och två dörrblad i varje, i liv med väggen, hängda i smygen."""
    m = Montage("Dörrar", beskrivning="Par av garderobsdörrar, blad 22 i trä, i öppningar med smyg av vitmålad furu")
    ga = VAGGAR[-1]
    y_rum = ga.origo[1] - skiktets_tjocklek("GA", -1, 1000.0)            # rummets yta
    y_in = ga.origo[1] + T + GIPS_T                                       # insidans yta
    for k, (x0, x1) in enumerate(_oppningar_x(), start=1):
        for namn, (a, b_, z0_, z1_, fiber) in (("V", (x0, x0 + SMYG_T, 0.0, H_OPPNING, "z")),
                                                ("H", (x1 - SMYG_T, x1, 0.0, H_OPPNING, "z")),
                                                ("O", (x0 + SMYG_T, x1 - SMYG_T, H_OPPNING - SMYG_T, H_OPPNING, "x"))):
            d, pl = virke_i_lada(a, b_, y_rum, y_in, z0_, z1_, fiber, FONSTERTRA)
            m.lagg(Del(f"Smygbräda {fmt(y_in - y_rum)}×{fmt(SMYG_T)} garderob", d.form, FONSTERTRA), pl,
                   f"GD{k}-SMYG-{namn}")
        fri = x1 - x0 - 2 * SMYG_T
        b = (fri - SPEL) / 2
        z0, z1 = 10.0, H_OPPNING - SMYG_T - SPEL
        for namn, a in (("V", x0 + SMYG_T), ("H", x1 - SMYG_T - b)):
            d, pl = virke_i_lada(a, a + b, y_rum, y_rum + BLAD_T, z0, z1, "z", FURU)     # fibrerna på höjden
            m.lagg(Del(f"Garderobsdörr trä {fmt(b)}×{fmt(z1 - z0)}", d.form, FURU), pl, f"GD{k}-BLAD-{namn}")
    return m


def montage() -> Montage:
    m = Montage(GARDEROB, "Garderob", "Inbyggd garderob i sovrummet i mittre huskroppen (ärende #16): lätta väggar 45×70 "
                                "med gips som de andra innerväggarna, två par dörrar och tak på dörrarnas höjd")
    m.lagg(_stomme())
    m.lagg(_skikt())
    m.lagg(_dorrar())
    return m
