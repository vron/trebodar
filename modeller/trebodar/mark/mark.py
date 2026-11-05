"""Marken: berg, uppfyllnad och sovrumsavsatsen, som i Onshape-modellen (referensdelar), schaktet i berget runt
plattan på mark, entréavsatsen vid huvudentrén 1SO-D1 och trätrappan från sovrumsavsatsen till 2SO-D1.

Schaktet går 100 mm utanför plattan på mark (hus/grund: L-element, cellplast, makadam och dränerande fyllning under
plattan); mellan L-elementen och schaktets kant ligger makadam upp till markytan, där berget eller uppfyllnaden låg.
Marken följer Onshape-modellens mark fram till huset; K-06:s fyllnadshöjder mot källarväggarna ligger högre och är
inte modellerade (ärende #43). Där Onshape-modellens mark inte når fram till källarväggarna ligger dränerande
återfyllning upp till markens nivå intill (framför 2SV) och vid nedgången till källardörren D1 upp till K-06:s
höjder. Sovrumsavsatsen och entréavsatsen är två separata avsatser av granit.

Entréavsatsen: granitblock framför 1SO-D1, ett trappsteg vid dörren, avsatsen och trappsteg längs fasaden ned mot
NO, med lika steghöjder från golvet (z 0) till marken vid trappans fot. Blocken går ned i marken.
Trätrappan: lärk, två vangstycken och plansteg mellan dem, från sovrumsavsatsen (som lutar) upp till 2SO-D1 med lika
steghöjder; vangstyckena står på avsatsen.
"""
from __future__ import annotations

from shapely.geometry import Point, Polygon
from shapely.geometry import box as rektangel
from shapely.ops import unary_union

from modellering import Del, Diff, Form, Montage, Placering, minus, polyeder

from trebodar import skelett as S
from trebodar.hus.stomme import lagen
from trebodar.byggdelar.polygon import polygoner, prisma_ur, prisma_y
from trebodar.byggdelar.referensdel import importerad
from trebodar.byggdelar.virke import fmt
from trebodar.hus.altan.altan import plintarnas_former
from trebodar.hus.fonster_och_dorrar.oppningar import OPPNINGAR
from trebodar.hus.grund import fasadsten, kallarvaggar
from trebodar.hus.grund.grund import H_L_MARK, MARK_PLATTA, MARK_UK, markplatta, markschakt
from trebodar.material import BERG, FYLLNING, LARK, MAKADAM, MARK, NATURSTEN

# återfyllningen mot källarväggarnas utsida där Onshape-modellens mark inte når fram: bredd från väggen och punkter
# (läge längs väggen, z) på överkanten, vågrätt förbi den första och den sista
ATERFYLLNING = {
    "V2": (400.0, ((4545.0, -412.0), (8370.0, -698.0), (9645.0, -679.0))),     # framför 2SV: marken 400 mm ut
    "V9": (1500.0, ((9340.0, -2250.0), (11240.0, -2250.0), (13665.0, -1450.0))),   # nedgången till D1 (K-06)
}

# entréavsatsen vid 1SO-D1: mått från panelens utsida och dörröppningen (y), höjder från golvet
E_MARK = -928.0              # marken vid trappans fot (Onshape-modellens mark)
E_STEG = 6                   # steghöjder från golvet till marken: dörrsteget, avsatsen och tre trappsteg
E_DORRSTEG = (400.0, 100.0)  # trappsteget vid dörren: djup, bredd utanför öppningen på var sida
E_AVSATS = (1500.0, 500.0)   # avsatsens djup och bredd utanför öppningen på var sida
E_PLANSTEG = 300.0           # trappstegens djup, längs fasaden
E_UK = -1100.0               # blockens underkant, i marken
# trätrappan till 2SO-D1
T_STEG = 5                   # steghöjder från sovrumsavsatsen till golvet
T_PLANSTEG = (280.0, 34.0)   # planstegens djup och tjocklek
T_VANG = (45.0, 220.0)       # vangstyckena: tjocklek, höjd
T_UTANFOR = 100.0            # trappans bredd utanför öppningen på var sida (mellan vangstyckena)
T_OVER = 40.0                # vangstyckets överkant över planstegens framkant


def _sovrumsavsatsens_ok(y: float) -> float:
    """Sovrumsavsatsens överkant (Onshape-modellen): planet −0,0306 y + 0,9995 z = −848,4, som lutar längs y."""
    return (-848.406 + 0.0306 * y) / 0.9995


def _husets_fotavtryck() -> Form:
    """Källaren med fasadstenen och plattan på mark, som prisma från under bottenplattan till bjälklaget."""
    # stängning (+600, −530) så att öppningarna i fasaden räknas till huset
    p = kallarvaggar.ytterkontur().buffer(600.0, join_style=2).buffer(-530.0, join_style=2)
    p = p.union(Polygon(MARK_PLATTA).buffer(30.0, join_style=2))
    return prisma_ur(Polygon(max(polygoner(p), key=lambda g: g.area).exterior), -2900.0, 0.0)


def _fyllnad(v: kallarvaggar.Kallarvagg, bredd: float, punkter: tuple[tuple[float, float], ...]) -> Form:
    """Återfyllningen mot väggens utsida, från markmodellens underkant upp till överkanten genom punkterna längs
    väggen och vågrätt lika långt som bredden förbi dem."""
    halv = kallarvaggar.KARNA / 2 + kallarvaggar.CELL
    mitt = (v.a + v.b) / 2
    prov = (mitt, v.c + halv + 10.0) if v.riktning == "h" else (v.c + halv + 10.0, mitt)
    s = -1.0 if kallarvaggar.ytterkontur().contains(Point(prov)) else 1.0       # utsidans riktning
    w0, w1 = sorted((v.c + s * halv, v.c + s * (halv + bredd)))
    st = [(punkter[0][0] - bredd, punkter[0][1]), *punkter, (punkter[-1][0] + bredd, punkter[-1][1])]

    def punkt(u: float, w: float, z: float) -> tuple[float, float, float]:
        return (u, w, z) if v.riktning == "h" else (w, u, z)
    horn = [punkt(u, w, z) for u, zt in st for w, z in ((w0, MARK_UK), (w1, MARK_UK), (w1, zt), (w0, zt))]
    sist = 4 * (len(st) - 1)
    ytor = [[0, 1, 2, 3], [sist, sist + 1, sist + 2, sist + 3]]
    for i in range(len(st) - 1):
        a, b = 4 * i, 4 * i + 4
        ytor += [[a, b, b + 1, a + 1], [a + 3, a + 2, b + 2, b + 3], [a, a + 3, b + 3, b], [a + 1, b + 1, b + 2, a + 2]]
    return polyeder(horn, ytor)


def _oppning_y(kod: str) -> tuple[float, float, float]:
    """Dörröppningens utbredning i y och panelens utsida (x) för en öppning i en långsida."""
    o = next(o for vagg in OPPNINGAR.values() for o in vagg if o.kod == kod)
    v = S.YTTERVAGGAR[o.vagg]
    pl = v.placering()
    y0, y1 = sorted(pl.punkt((u, 0.0, 0.0))[1] for u in (o.u0, o.u1))
    return y0, y1, pl.punkt((0.0, -S.T_FASAD, 0.0))[0]


def _entre() -> list[tuple[str, str, Form]]:
    """Entréavsatsens block (kod, namn, form): dörrsteget på avsatsen, avsatsen och trappstegen mot NO."""
    y0, y1, xp = _oppning_y("1SO-D1")
    h = -E_MARK / E_STEG
    djup, ut = E_AVSATS
    ds_djup, ds_ut = E_DORRSTEG
    ya = y0 - ut                                         # avsatsens NO-kant, där trappan börjar
    ut_: list[tuple[str, str, Form]] = [
        ("E-DS", f"Trappsteg vid dörren {fmt(y1 - y0 + 2 * ds_ut)}×{fmt(ds_djup)}",
         prisma_ur(rektangel(xp - ds_djup, y0 - ds_ut, xp, y1 + ds_ut), -2 * h, -h)),
        ("E-AV", f"Entréavsats {fmt(y1 - y0 + 2 * ut)}×{fmt(djup)}",
         prisma_ur(rektangel(xp - djup, ya, xp, y1 + ut), E_UK, -2 * h))]
    for k in range(1, E_STEG - 2):
        ut_.append((f"E-S{k}", f"Trappsteg {fmt(djup)}×{fmt(E_PLANSTEG)}",
                    prisma_ur(rektangel(xp - djup, ya - k * E_PLANSTEG, xp, ya - (k - 1) * E_PLANSTEG), E_UK,
                              -(2 + k) * h)))
    return ut_


def _tratrappa(avsats: Form) -> Montage:
    """Trätrappan från sovrumsavsatsen upp till 2SO-D1: plansteg mellan två vangstycken, vinkelrätt mot fasaden."""
    y0, y1, xp = _oppning_y("2SO-D1")
    g, tp = T_PLANSTEG
    tv, hv = T_VANG
    z_av = _sovrumsavsatsens_ok((y0 + y1) / 2)         # avsatsen under trappans mitt
    h = -z_av / T_STEG
    ya, yb = y0 - T_UTANFOR, y1 + T_UTANFOR
    m = Montage("Trätrappa 2SO-D1", beskrivning=f"Trätrappa av lärk från sovrumsavsatsen till 2SO-D1, {T_STEG} steg")
    for k in range(1, T_STEG):
        x0 = xp - (T_STEG - k) * g
        z = z_av + k * h
        m.lagg(Del(f"Plansteg {fmt(yb - ya)}×{fmt(g)}×{fmt(tp)}", prisma_ur(rektangel(x0, ya, x0 + g, yb), z - tp, z),
                   LARK), Placering(), f"TT-P{k}")
    # vangstycket: överkanten T_OVER över planstegens framkanter, upp till fasaden och ned till avsatsen, där det
    # kapas efter avsatsens yta
    x_fram = xp - (T_STEG - 1) * g
    lut = h / g

    def ok(x: float) -> float:
        return z_av + h + (x - x_fram) * lut + T_OVER
    d = hv * (1 + lut * lut) ** 0.5                    # vangstyckets höjd lodrätt
    x_fot = x_fram - (ok(x_fram) - z_av) / lut
    profil = Polygon([(x_fot, ok(x_fot) - d), (xp, ok(xp) - d), (xp, ok(xp)), (x_fot, ok(x_fot))])
    profil = profil.intersection(rektangel(x_fot, z_av - 100.0, xp, 1e5))
    xz = [(float(x), float(z)) for x, z in list(profil.exterior.coords)[:-1]]
    for i, (a, b) in enumerate(((ya - tv, ya), (yb, yb + tv)), 1):
        m.lagg(Del(f"Vangstycke {fmt(tv)}×{fmt(hv)}", minus(prisma_y(xz, a, b), [avsats]), LARK), Placering(),
               f"TT-V{i}")
    return m


def montage() -> Montage:
    m = Montage("Mark", beskrivning="Berg, uppfyllnad och sovrumsavsats (ur Onshape-modellen), schaktet runt plattan "
                                    "på mark, återfyllning, entréavsatsen och trätrappan till 2SO-D1")
    hus = _husets_fotavtryck()
    schakt = prisma_ur(markschakt(), MARK_UK - 10.0, 10.0)
    berg0, upp0, avsats0 = importerad("berg.bbrep"), importerad("uppfyllnad.bbrep"), importerad("sovrumsavsats.bbrep")
    # entréavsatsen: blocken går inte in i grunden (makadam och fyllning under plattan på mark, 100 mm utanför den)
    grund = prisma_ur(markschakt(), MARK_UK - 10.0, -H_L_MARK)
    entre = [(kod, namn, minus(f, [grund])) for kod, namn, f in _entre()]
    stenar = [f for _, _, f in entre]
    plintar = plintarnas_former()                       # altanens plintar, gjutna i borrade hål
    m.lagg(Del("Berg", minus(berg0, [schakt, *stenar, *plintar]), BERG), Placering(), "Berg")
    m.lagg(Del("Uppfyllnad", minus(upp0, [hus, avsats0, schakt, *stenar, *plintar]), MARK), Placering(), "Uppfyllnad")
    m.lagg(Del("Sovrumsavsats", minus(avsats0, [hus, schakt]), NATURSTEN), Placering(), "Sovrumsavsats")
    # makadam mellan L-elementen och schaktets kant, upp till markytan där berget eller uppfyllnaden låg
    for i, g in enumerate(polygoner(markschakt().difference(markplatta()[0]), 1e3), 1):
        ring = prisma_ur(g, -H_L_MARK, 10.0)
        m.lagg(Del("Makadam runt plattan på mark", (ring & berg0) | (ring & upp0), MAKADAM), Placering(), f"MA-{i}")
    # återfyllningen mot källarväggarna, utanför väggarna och fasadstenen, där marken inte når fram
    sten = unary_union([rektangel(x0, y0, x1, y1) for x0, y0, _, x1, y1, _ in lagen.ladar(fasadsten.montage())])
    hinder = [prisma_ur(kallarvaggar.ytterkontur(), MARK_UK - 10.0, 10.0), berg0, upp0, avsats0, schakt, *plintar]
    # fasadstenens kluvna yta följs inte: fyllningen slutar 5 mm utanför stenarnas omslutande lådor
    hinder += [prisma_ur(g, MARK_UK - 10.0, 10.0) for g in polygoner(sten.buffer(5.0, join_style=2))]
    vaggar = {v.namn: v for v in kallarvaggar.VAGGAR}
    tidigare: list[Form] = []
    for namn, (bredd, punkter) in ATERFYLLNING.items():
        band = f = _fyllnad(vaggar[namn], bredd, punkter)
        for h in hinder + tidigare:
            f = Diff(f, (h,))    # ett verktyg i taget (inte a - b, som slår ihop): överlappande verktyg gav fel
        m.lagg(Del(f"Återfyllning mot {namn}", f, FYLLNING), Placering(), f"FK-{namn}")
        tidigare.append(band)
    e = Montage("Entréavsats", beskrivning="Entréavsats av granit vid 1SO-D1: dörrsteg, avsats och trappsteg",
                produkt="ENTREAVSATS")
    for kod, namn, f in entre:
        e.lagg(Del(namn, f, NATURSTEN), Placering(), kod)
    m.lagg(e)
    m.lagg(_tratrappa(avsats0))
    return m
