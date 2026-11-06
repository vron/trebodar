"""Marken: berg, uppfyllnad och sovrumsavsatsen, som i Onshape-modellen (referensdelar), schaktet i berget runt
plattan på mark, entréavsatsen vid huvudentrén 1SO-D1, bänktrappan från sovrumsavsatsen till 2SO-D1 och källartrappan
till källardörren D1.

Schaktet går 100 mm utanför plattan på mark (hus/grund: L-element, cellplast, makadam och dränerande fyllning under
plattan); mellan L-elementen och schaktets kant ligger makadam upp till markytan, där berget eller uppfyllnaden låg.
Marken följer Onshape-modellens mark fram till huset; K-06:s fyllnadshöjder mot källarväggarna ligger högre och är
inte modellerade (ärende #43). Där Onshape-modellens mark inte når fram till källarväggarna ligger dränerande
återfyllning upp till markens nivå intill (framför 2SV) och vid nedgången till källardörren D1 upp till K-06:s
höjder; uppfyllnaden tas bort över nedgången. Sovrumsavsatsen och entréavsatsen är två separata avsatser av granit.
Sovrumsavsatsen är Onshape-modellens, breddad västerut till 1SO:s fasad (AVSATS_BREDARE), så att panelen på 1NO
slutar på avsatsen ända till hörnet: delen väster om AVSATS_SNITT, med de rundade stegen, flyttas västerut och
avsatsen förlängs med samma tvärsnitt (den är rak längs x där).

Entréavsatsen: granitblock framför 1SO-D1, ett trappsteg vid dörren, avsatsen och trappsteg längs fasaden ned mot
NO, med lika steghöjder från golvet (z 0) till marken vid trappans fot. Blocken går ned i marken.
Bänktrappan: lärk, två plank 90 × 180 sida vid sida ett steg ned från dörren, längs fasaden som bänk och trappsteg,
och ett steg till framför dörren, med lika steghöjder från sovrumsavsatsen (som lutar) till golvet; planken ligger på
ben av samma plank, som står på avsatsen.
Källartrappan: staplade granitblock längs fasaden, från avsatsen framför D1 upp mot NO till marken (K-06:s
fyllnadshöjd) i husets östra fasad (3NV), med lika stegdjup. Avsatsen ligger i källargolvets höjd, mellan
källarväggen V17 och trappan, och räcker förbi pardörrens huvudblad (mot trappan) uppslaget mot fasaden; det smala
bladet mot väggen öppnas mot V17. Brunnen B1:s lock ligger i avsatsen. Återfyllningen mot V9 följer avsatsen och
trappan.
"""
from __future__ import annotations

import math

from shapely.geometry import Point, Polygon
from shapely.geometry import box as rektangel
from shapely.ops import unary_union

from modellering import Del, Diff, Form, Montage, Placering, cylinder, flytt, minus, polyeder

from trebodar import skelett as S
from trebodar.hus.stomme import lagen
from trebodar.byggdelar.polygon import polygoner, prisma_ur
from trebodar.byggdelar.referensdel import importerad
from trebodar.byggdelar.virke import fmt
from trebodar.byggdelar import ytterdorrar as YD
from trebodar.hus.altan.altan import plintarnas_former, stegens_former
from trebodar.hus.fonster_och_dorrar.oppningar import OPPNINGAR
from trebodar.hus.grund import fasadsten, kallarvaggar
from trebodar.hus.grund.grund import H_L_MARK, MARK_PLATTA, MARK_UK, markplatta, markschakt
from trebodar.hus.installationer.dranering.ledningar import brunnar
from trebodar.material import BERG, FYLLNING, LARK, MAKADAM, MARK, NATURSTEN

# källartrappan vid D1: granitblock (djup, höjd; blocken överlappar, och de går över hela nedgångens bredd, från
# fasadstenen till schaktets kant), avsatsen förbi det uppslagna huvudbladet och ut från fasaden (nedgångens bredd),
# avsatsens tjocklek, marken vid trappans topp (K-06) och glipan mot fasadstenen
K_BLOCK = (350.0, 100.0)
K_FORBI = 150.0
K_AVSATS = (1500.0, 100.0)
K_TOPP = -1450.0
K_GLIPA = 10.0               # mot fasadstenen och runt brunnens lock
K_VAGG = 9340.0              # källarväggen V17:s utsida, nedgångens västra sida


def _kallartrappans_lage() -> tuple[float, float, float, int, float]:
    """Källartrappans läge: fasadens plan (y), avsatsens östra kant (trappans början, x), dess höjd, antalet steg och
    stegdjupet, så att det översta steget slutar i husets östra fasad (3NV, ärende #69)."""
    o = next(o for o in OPPNINGAR["3NO"] if o.typ == "pardörr")
    v = S.YTTERVAGGAR["3NO"]
    gangjarn = v.origo[0] + o.u1 - YD.D_BAGE[1]          # huvudbladets gångjärn (till höger sett utifrån)
    x0, n = gangjarn + YD.P_HUVUD + K_FORBI, round((K_TOPP - o.z0) / K_BLOCK[1])
    x_slut = S.YTTERVAGGAR["3NV"].placering().punkt((0.0, -S.T_FASAD, 0.0))[0]
    return v.origo[1], x0, o.z0, n, (x_slut - x0 - K_BLOCK[0]) / (n - 1)


# återfyllningen mot källarväggarnas utsida där Onshape-modellens mark inte når fram: bredd från väggen, punkter
# (läge längs väggen, z) på överkanten och hur långt den går vågrätt förbi den första och den sista
_Y_FASAD, _X_TRAPPA, _Z_AVSATS, _N_STEG, _K_STEG = _kallartrappans_lage()
_X_SLUT = _X_TRAPPA + (_N_STEG - 1) * _K_STEG + K_BLOCK[0]                     # trappans slut, i 3NV:s fasad
ATERFYLLNING = {
    "V2": (400.0, ((4545.0, -412.0), (8370.0, -698.0), (9645.0, -679.0)), (400.0, 400.0)),   # framför 2SV
    "V9": (K_AVSATS[0], ((K_VAGG, _Z_AVSATS), (_X_TRAPPA, _Z_AVSATS), (_X_SLUT, K_TOPP)),    # nedgången till D1
           (K_AVSATS[0], 0.0)),                                                              # (K-06)
}
NEDGANG = "V9"                # nedgången: uppfyllnaden tas bort över återfyllningen (ärende #69)

# entréavsatsen vid 1SO-D1: mått från panelens utsida och dörröppningen (y), höjder från golvet
E_MARK = -928.0              # marken vid trappans fot (Onshape-modellens mark)
E_STEG = 6                   # steghöjder från golvet till marken: dörrsteget, avsatsen och tre trappsteg
E_DORRSTEG = (400.0, 100.0)  # trappsteget vid dörren: djup, bredd utanför öppningen på var sida
E_AVSATS = (1500.0, 500.0)   # avsatsens djup och bredd utanför öppningen på var sida
E_PLANSTEG = 300.0           # trappstegens djup, längs fasaden
E_UK = -1100.0               # blockens underkant, i marken
# bänktrappan vid 2SO-D1 (ärende #76)
B_STEG = 3                   # steghöjder från sovrumsavsatsen till golvet: steget, bänken och dörren
B_PLANK = (90.0, 180.0)      # planken (och benen): tjocklek, bredd; två sida vid sida
B_FOG = 10.0                 # mellan planken
B_FRI = 10.0                 # bänken från fasaden
B_LANGD = 2400.0             # bänken längs fasaden, från B_UTANFOR söder om dörren mot norr
B_UTANFOR = 100.0            # steget framför dörren: bredd utanför öppningen på var sida
B_BEN_IN = 100.0             # benen innanför plankens ändar
B_BEN_CC = 1200.0            # benen, c/c högst
# sovrumsavsatsen (Onshape-modellen, västra sidan i x 170) breddad till 1SO:s fasad (ärende #67): snittet öster om
# de rundade stegen, där avsatsen är rak längs x
AVSATS_VAST = 170.0
AVSATS_SNITT = 2100.0


def _sovrumsavsatsens_ok(y: float) -> float:
    """Sovrumsavsatsens överkant (Onshape-modellen): planet −0,0306 y + 0,9995 z = −848,4, som lutar längs y."""
    return (-848.406 + 0.0306 * y) / 0.9995


def _husets_fotavtryck() -> Form:
    """Källaren med fasadstenen och plattan på mark, som prisma från under bottenplattan till bjälklaget."""
    # stängning (+600, −530) så att öppningarna i fasaden räknas till huset
    p = kallarvaggar.ytterkontur().buffer(600.0, join_style=2).buffer(-530.0, join_style=2)
    p = p.union(Polygon(MARK_PLATTA).buffer(30.0, join_style=2))
    return prisma_ur(Polygon(max(polygoner(p), key=lambda g: g.area).exterior), -2900.0, 0.0)


def _fyllnad(v: kallarvaggar.Kallarvagg, bredd: float, punkter: tuple[tuple[float, float], ...],
             forbi: tuple[float, float], ovanfor: bool = False) -> Form:
    """Återfyllningen mot väggens utsida, från markmodellens underkant upp till överkanten genom punkterna längs
    väggen och vågrätt förbi dem (forbi: före den första och efter den sista); ovanfor: rummet ovanför den, upp till
    golvet (z 0)."""
    halv = kallarvaggar.KARNA / 2 + kallarvaggar.CELL
    mitt = (v.a + v.b) / 2
    prov = (mitt, v.c + halv + 10.0) if v.riktning == "h" else (v.c + halv + 10.0, mitt)
    s = -1.0 if kallarvaggar.ytterkontur().contains(Point(prov)) else 1.0       # utsidans riktning
    w0, w1 = sorted((v.c + s * halv, v.c + s * (halv + bredd)))
    st = [*([(punkter[0][0] - forbi[0], punkter[0][1])] if forbi[0] else []), *punkter,
          *([(punkter[-1][0] + forbi[1], punkter[-1][1])] if forbi[1] else [])]

    def punkt(u: float, w: float, z: float) -> tuple[float, float, float]:
        return (u, w, z) if v.riktning == "h" else (w, u, z)
    horn = [punkt(u, w, z) for u, zt in st
            for w, z in (((w0, zt), (w1, zt), (w1, 0.0), (w0, 0.0)) if ovanfor else
                         ((w0, MARK_UK), (w1, MARK_UK), (w1, zt), (w0, zt)))]
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


def _sovrumsavsatsen() -> Form:
    """Sovrumsavsatsen ur Onshape-modellen, breddad västerut till 1SO:s fasad: delen väster om AVSATS_SNITT flyttad
    lika långt västerut och delen öster om den, som möts i snittet (samma tvärsnitt, avsatsen är rak längs x där)."""
    a = importerad("sovrumsavsats.bbrep")
    d = AVSATS_VAST - S.YTTERVAGGAR["1SO"].placering().punkt((0.0, -S.T_FASAD, 0.0))[0]
    return a.kapad((AVSATS_SNITT, 0.0, 0.0), (-1.0, 0.0, 0.0)) | \
        a.kapad((AVSATS_SNITT + d, 0.0, 0.0), (1.0, 0.0, 0.0)).placerad(flytt(-d))


def _banktrappa(avsats: Form) -> Montage:
    """Bänktrappan från sovrumsavsatsen upp till 2SO-D1: två plank längs fasaden ett steg ned från dörren (bänken,
    B_LANGD lång) och två plank framför dem, framför dörren (steget), med lika steghöjder; benen står på avsatsen och
    är kapade efter den."""
    y0, y1, xp = _oppning_y("2SO-D1")
    t, b = B_PLANK
    djup = 2 * b + B_FOG
    h = -_sovrumsavsatsens_ok((y0 + y1) / 2) / B_STEG
    m = Montage("Bänktrappa 2SO-D1", beskrivning=f"Bänktrappa av lärk vid 2SO-D1: bänk längs fasaden ett steg ned från "
                                                f"dörren och ett steg framför dörren, plank {fmt(t)}×{fmt(b)}")
    x_bank = xp - B_FRI - djup
    for kod, x0, ya, yb, z in (("B", x_bank, y1 + B_UTANFOR - B_LANGD, y1 + B_UTANFOR, -h),
                               ("S", x_bank - djup, y0 - B_UTANFOR, y1 + B_UTANFOR, -2 * h)):
        namn = "Bänk" if kod == "B" else "Steg"
        for i in range(2):
            xa = x0 + i * (b + B_FOG)
            m.lagg(Del(f"{namn}, plank {fmt(t)}×{fmt(b)}×{fmt(yb - ya)}", prisma_ur(rektangel(xa, ya, xa + b, yb),
                                                                                     z - t, z), LARK),
                   Placering(), f"BT-{kod}{i + 1}")
        # benen: två plank på högkant tvärs planken, från avsatsen (kapade efter den) till plankens underkant
        n = max(2, math.ceil((yb - ya - 2 * B_BEN_IN - t) / B_BEN_CC) + 1)
        for j in range(n):
            yc = ya + B_BEN_IN + t / 2 + j * (yb - ya - 2 * B_BEN_IN - t) / (n - 1)
            for i in range(2):
                xa = x0 + i * (b + B_FOG)
                ben = prisma_ur(rektangel(xa, yc - t / 2, xa + b, yc + t / 2), _sovrumsavsatsens_ok(yc) - 100.0, z - t)
                m.lagg(Del(f"{namn}sben, plank {fmt(t)}×{fmt(b)}", minus(ben, [avsats]), LARK), Placering(),
                       f"BT-{kod}B{2 * j + i + 1}")
    return m


def _kallartrappa() -> list[tuple[str, str, Form]]:
    """Källartrappans block (kod, namn, form): avsatsen framför D1 och trappstegen längs fasaden, över hela
    nedgångens bredd (ärende #69)."""
    d, h = K_BLOCK
    y1 = _Y_FASAD - S.T_FASAD - K_GLIPA                   # fasadstenens utsida
    b = y1 - (_Y_FASAD - K_AVSATS[0])                     # till nedgångens kant
    br = brunnar()["B1"]                                  # brunnens lock i avsatsen
    avsats: Form = prisma_ur(rektangel(K_VAGG, _Y_FASAD - K_AVSATS[0], _X_TRAPPA + d - _K_STEG, _Y_FASAD),
                             _Z_AVSATS - K_AVSATS[1], _Z_AVSATS) \
        - cylinder(br.d / 2 + K_GLIPA, K_AVSATS[1] + 20.0, (br.x, br.y, _Z_AVSATS - K_AVSATS[1] - 10.0))
    ut: list[tuple[str, str, Form]] = [
        ("K-AV", f"Källaravsats {fmt(_X_TRAPPA + d - _K_STEG - K_VAGG)}×{fmt(K_AVSATS[0])}", avsats)]
    for i in range(_N_STEG):
        x0 = _X_TRAPPA + i * _K_STEG
        ut.append((f"K-S{i + 1}", f"Trappsteg granit {fmt(b)}×{fmt(d)}×{fmt(h)}",
                   prisma_ur(rektangel(x0, y1 - b, x0 + d, y1), _Z_AVSATS + i * h, _Z_AVSATS + (i + 1) * h)))
    return ut


def montage() -> Montage:
    m = Montage("Mark", beskrivning="Berg, uppfyllnad och sovrumsavsats (ur Onshape-modellen), schaktet runt plattan "
                                    "på mark, återfyllning, entréavsatsen, trätrappan till 2SO-D1 och källartrappan")
    hus = _husets_fotavtryck()
    schakt = prisma_ur(markschakt(), MARK_UK - 10.0, 10.0)
    berg0, upp0, avsats0 = importerad("berg.bbrep"), importerad("uppfyllnad.bbrep"), _sovrumsavsatsen()
    # entréavsatsen: blocken går inte in i grunden (makadam och fyllning under plattan på mark, 100 mm utanför den)
    grund = prisma_ur(markschakt(), MARK_UK - 10.0, -H_L_MARK)
    entre = [(kod, namn, minus(f, [grund])) for kod, namn, f in _entre()]
    kallare = _kallartrappa()
    stenar = [f for _, _, f in entre + kallare]
    plintar = plintarnas_former()                       # altanens plintar, gjutna i borrade hål
    steg = stegens_former()                             # altanens trappsteg: urtaget under dem
    m.lagg(Del("Berg", minus(berg0, [schakt, *stenar, *plintar, *steg]), BERG), Placering(), "Berg")
    vaggar = {v.namn: v for v in kallarvaggar.VAGGAR}
    bredd, punkter, _ = ATERFYLLNING[NEDGANG]
    nedgang = _fyllnad(vaggar[NEDGANG], bredd, punkter, (0.0, 0.0), ovanfor=True)
    m.lagg(Del("Uppfyllnad", minus(upp0, [hus, avsats0, schakt, *stenar, *plintar, *steg, nedgang]), MARK),
           Placering(), "Uppfyllnad")
    m.lagg(Del("Sovrumsavsats", minus(avsats0, [hus, schakt]), NATURSTEN), Placering(), "Sovrumsavsats")
    # makadam mellan L-elementen och schaktets kant, upp till markytan där berget eller uppfyllnaden låg
    for i, g in enumerate(polygoner(markschakt().difference(markplatta()[0]), 1e3), 1):
        ring = prisma_ur(g, -H_L_MARK, 10.0)
        m.lagg(Del("Makadam runt plattan på mark", (ring & berg0) | (ring & upp0), MAKADAM), Placering(), f"MA-{i}")
    # återfyllningen mot källarväggarna, utanför väggarna och fasadstenen, där marken inte når fram
    sten = unary_union([rektangel(x0, y0, x1, y1) for x0, y0, _, x1, y1, _ in lagen.ladar(fasadsten.montage())])
    hinder = [prisma_ur(kallarvaggar.ytterkontur(), MARK_UK - 10.0, 10.0), berg0, upp0, avsats0, schakt, *plintar, *steg,
              *(f for _, _, f in kallare)]
    # fasadstenens kluvna yta följs inte: fyllningen slutar 5 mm utanför stenarnas omslutande lådor
    hinder += [prisma_ur(g, MARK_UK - 10.0, 10.0) for g in polygoner(sten.buffer(5.0, join_style=2))]
    tidigare: list[Form] = []
    for namn, (bredd, punkter, forbi) in ATERFYLLNING.items():
        band = f = _fyllnad(vaggar[namn], bredd, punkter, forbi)
        for h in hinder + tidigare:
            f = Diff(f, (h,))    # ett verktyg i taget (inte a - b, som slår ihop): överlappande verktyg gav fel
        m.lagg(Del(f"Återfyllning mot {namn}", f, FYLLNING), Placering(), f"FK-{namn}")
        tidigare.append(band)
    e = Montage("Entréavsats", beskrivning="Entréavsats av granit vid 1SO-D1: dörrsteg, avsats och trappsteg",
                produkt="ENTREAVSATS")
    for kod, namn, f in entre:
        e.lagg(Del(namn, f, NATURSTEN), Placering(), kod)
    m.lagg(e)
    k = Montage("Källartrappa", beskrivning="Källartrappa av granitblock vid D1: avsats och trappsteg",
                produkt="KALLARTRAPPA")
    for kod, namn, f in kallare:
        k.lagg(Del(namn, f, NATURSTEN), Placering(), kod)
    m.lagg(k)
    m.lagg(_banktrappa(avsats0))
    return m
