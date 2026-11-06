"""Altanen (ärende #30, #70): trädäck av grånad tryckimpregnerad trall 34 × 135 framför skjutpartiet 2SV, mellan
kropparnas fasader 1NV och 3SO, från 2SV ut FORBI förbi gaveln 1SV:s linje, med överkanten i golvets höjd (plan 1,
z 0; skjutpartiets tröskel 33 över), och breda trappsteg ned till marken längs framkanten och sidan. Varje bräda är
en egen del. Två val: LANGS (brädorna längs 2SV, annars tvärs, ut från huset) och RAM (en ram av brädor runt om och
brädorna innanför den, annars brädorna kant i kant över hela däcket); fogarna fördelas lika, nära FOG.

Under brädorna bjälkar 45×145 tvärs brädorna, c/c högst 600 (med ram en extra bjälke under ramens bräda vid
ändarna), på bärlinor 2 × 45×145 längs brädorna, som står på betongplintar Ø200 gjutna i borrade hål i berget
(marken har hål för dem, mark.py), fria från dräneringens och dagvattnets ledningar längs grunden
(installationer/dranering): en plint som skulle stå på dem flyttas längs bärlinan. Längs de fria kanterna
(framkanten, sidan förbi den högra kroppens hörn och kanten förbi gaveln 1SV) en sargbräda under brädorna, i liv med
dem, som täcker bjälkändarna; stommen slutar innanför den. Stuprören DB4-ST2 och DB2-ST2 i de inre hörnen går ned
genom däcket, med hål runt dem. Kanterna mot fasaderna har FRI mm luft. En lucka i däcket över spolrören och
spolbrunnarna under altanen (dräneringen, ärende #71): brädorna där är egna delar, kapade över en bjälke.

Trappstegen (ärende #70) går längs framkanten och sidan, så att man kan gå ned till marken var som helst: varje steg
är en bräda och en sargbräda högt (STEG_H) och STEG_BRADOR brädor djupt, ett litet däck med brädorna längs kanten på
bjälkar 45×145 tvärs kanten och en sargbräda framtill (sättsteget). Ett steg står på steget under (vars brädor går
in under det) eller, nederst, på betongplintar i berget. Antalet steg följer berget (BERG: Onshape-modellens berg
under och framför altanen är ett plan som faller österut), så att det nedersta steget ligger närmast berget: längs
framkanten börjar ett nytt steg där berget har fallit så långt, och sidan har lika många steg som hörnet."""
from __future__ import annotations

import math
from functools import cache

from modellering import Del, Form, Montage, Placering, cylinder, lada, minus
from shapely.geometry import LineString, Point
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from trebodar import skelett as S
from trebodar.byggdelar.virke import fmt, virke_i_lada
from trebodar.hus.installationer.dranering import ledningar as dr
from trebodar.hus.tak.dalar import STOS_D, STOS_FRI
from trebodar.material import BETONG, TRALL, TRYCKIMP

LANGS = False                 # brädorna längs 2SV (x), annars tvärs (y), ut från huset (ärende #70)
RAM = True                    # en ram av brädor runt om
TRALL_T, TRALL_B = 34.0, 135.0
FOG = 5.0                     # fogarna mellan brädorna, ungefär (lika fördelade)
FRI = 10.0                    # luft mot fasaderna
REGEL = (45.0, 145.0)         # bjälkarna, tvärs brädorna
CC_REGEL = 600.0
BALK = (45.0, 145.0)          # bärlinorna: två sida vid sida, längs brädorna
CC_BALK = 1800.0              # högst, mellan bärlinorna (bjälkarnas spännvidd)
CC_PLINT = 1600.0             # högst, mellan plintarna längs bärlinan
INDRAG = 300.0                # bärlinornas och plintarnas indrag från däckets kanter (tvärs bärlinorna)
BALK_INDRAG = 150.0           # bärlinornas ändar innanför stommens kant (bjälkarna kragar ut)
PLINT_D, PLINT_UK = 200.0, -800.0
HAL_FRI = 10.0                # runt stuprören
LEDNING_FRI = 50.0            # plintarna från dräneringens och dagvattnets rör och brunnar, i plan
SARG = (34.0, 145.0)          # sargbrädan längs de fria kanterna: tjocklek, höjd
FORBI = 250.0                 # däcket förbi gaveln 1SV:s linje (ärende #70)
STEG_BRADOR = 3               # trappstegens djup: brädor längs kanten
STEG_PLINT = 1000.0           # plintarna under det nedersta stegets bjälkar, c/c högst
# berget under och framför altanen (Onshape-modellens berg, som huset inte läser): planet
# z = BERG[1] + BERG[2] (x − BERG[0])
BERG = (4500.0, -409.0, -0.0748)
STEG_VAGG = 150.0             # sidans steg: bjälkarna (och plintarna) från den högra kroppens fasad
LUCKA_MARGINAL = 150.0        # luckan i däcket: runt spolrören och spolbrunnarna under altanen
LUCKA_MINST = 300.0           # brädbitar kortare än så mellan luckan och ramen kapas inte, luckan går till ramen
STEG_H = TRALL_T + SARG[1]                   # stegens höjd: brädan och sargbrädan (bjälkarna lika höga)
STEG_DJUP = STEG_BRADOR * (TRALL_B + FOG)    # med fogen mot steget ovanför


def _fasad(kod: str) -> float:
    """Fasadens yta (panelens utsida), tvärs väggen: y för väggar längs x, x för väggar längs y."""
    p = S.YTTERVAGGAR[kod].placering().punkt((0.0, -S.T_FASAD, 0.0))
    return p[1] if abs(S.YTTERVAGGAR[kod].u[0]) > 0.5 else p[0]


X0, X1 = _fasad("1NV") + FRI, _fasad("3SO") - FRI
Y0, Y1 = _fasad("2SV") + FRI, _fasad("1SV") + FORBI
Y_GAVEL = _fasad("1SV")                   # gaveln 1SV:s linje: kanten X0 är fri härifrån
Y_HORN = _fasad("3SV")                    # den högra kroppens hörn: sidan X1 är fri härifrån
# stuprören i de inre hörnen (dalar.py: STOS_FRI från fasaderna)
STUPROR = [(_fasad(kx) + s * (STOS_FRI + STOS_D / 2), _fasad("2SV") + STOS_FRI + STOS_D / 2)
           for kx, s in (("1NV", 1.0), ("3SO", -1.0))]
Z_REGEL = -TRALL_T
Z_BALK = Z_REGEL - REGEL[1]
Z_PLINT = Z_BALK - BALK[1]


def _ab(stomme: bool = False) -> tuple[float, float, float, float]:
    """Däcket längs brädorna (a) och tvärs (b): a0, a1, b0, b1; stommen slutar innanför sargen (också vid X0, för
    sargen förbi gaveln 1SV)."""
    x0, x1, y1 = (X0 + SARG[0], X1 - SARG[0], Y1 - SARG[0]) if stomme else (X0, X1, Y1)
    return (x0, x1, Y0, y1) if LANGS else (Y0, y1, x0, x1)


def _xy(a0: float, a1: float, b0: float, b1: float) -> tuple[float, float, float, float]:
    return (a0, a1, b0, b1) if LANGS else (b0, b1, a0, a1)


def _jamnt(b0: float, b1: float, bredd: float, fog: float) -> list[tuple[float, float]]:
    """Brädor av bredden från b0 till b1 med lika fogar, nära fog."""
    n = max(1, round((b1 - b0 + fog) / (bredd + fog)))
    f = (b1 - b0 - n * bredd) / (n - 1) if n > 1 else 0.0
    return [(b0 + i * (bredd + f), b0 + i * (bredd + f) + bredd) for i in range(n)]


def _cc(a0: float, a1: float, b: float, cc: float) -> list[float]:
    """Lägen (början) för bitar av bredden b från a0 till a1, c/c högst cc, med en vid varje ände."""
    n = max(1, math.ceil((a1 - a0 - b) / cc))
    return [a0 + i * (a1 - a0 - b) / n for i in range(n + 1)]


def _del(namn: str, kod: str, lada: tuple[float, float, float, float, float, float], fiber: str, mat: object,
         m: Montage) -> None:
    """Virke i lådan (x0, x1, y0, y1, z0, z1), med hål runt stuprören som når det."""
    x0, x1, y0, y1, z0, z1 = lada
    d, pl = virke_i_lada(x0, x1, y0, y1, z0, z1, fiber, mat)                  # type: ignore[arg-type]
    r = STOS_D / 2 + HAL_FRI
    hal: list[Form] = [cylinder(r, z1 - z0 + 2.0, (sx, sy, z0 - 1.0)).placerad(pl.invers())
                       for sx, sy in STUPROR if x0 - r < sx < x1 + r and y0 - r < sy < y1 + r]
    m.lagg(Del(namn, minus(d.form, hal) if hal else d.form, mat), pl, kod)     # type: ignore[arg-type]


@cache
def _ledningarna(uk: float = PLINT_UK) -> BaseGeometry:
    """Där plintarnas mitt inte får stå: dräneringens och dagvattnets rör och brunnar i plan, utvidgade med
    plintens radie och LEDNING_FRI, där de går högre än plintarnas underkant uk."""
    ytor = []
    for led in dr.ledningar().values():
        for a, b in zip(led.vag, led.vag[1:]):
            if max(a[2], b[2]) + dr.D > uk - LEDNING_FRI:
                ytor.append(LineString([a[:2], b[:2]]).buffer(dr.D / 2 + LEDNING_FRI + PLINT_D / 2))
    ytor += [Point(br.x, br.y).buffer(br.d / 2 + LEDNING_FRI + PLINT_D / 2) for br in dr.brunnar().values()]
    return unary_union(ytor)


def plintar() -> list[tuple[float, float]]:
    """Plintarnas mitt (x, y): under varje bärlina, c/c högst CC_PLINT, och där en plint skulle stå på dräneringens
    eller dagvattnets ledningar flyttad längs bärlinan, så lite som möjligt, till där den går fri (under bärlinan)."""
    a0, a1, b0, b1 = _ab(stomme=True)
    lo, hi = a0 + BALK_INDRAG + PLINT_D / 2, a1 - BALK_INDRAG - PLINT_D / 2
    ror = _ledningarna()
    ut = []
    for b in _barlinor(b0, b1):
        for a in _cc(a0 + INDRAG - PLINT_D / 2, a1 - INDRAG + PLINT_D / 2, PLINT_D, CC_PLINT):
            for d in sorted(range(-1500, 1501, 5), key=abs):
                x, _, y, _ = _xy(a + PLINT_D / 2 + d, 0.0, b, 0.0)
                if lo <= a + PLINT_D / 2 + d <= hi and not ror.contains(Point(x, y)):
                    break
            ut.append((x, y))
    return ut


def plintarnas_former() -> list[Form]:
    """Plintarna som cylindrar (däckets och trappstegens), också för hålen i marken (mark.py)."""
    ut: list[Form] = [cylinder(PLINT_D / 2, Z_PLINT - PLINT_UK, (x, y, PLINT_UK)) for x, y in plintar()]
    return ut + [cylinder(PLINT_D / 2, z1 - z0, (x, y, z0)) for x, y, z0, z1 in _stegens_plintar()]


def _berget(x: float) -> float:
    """Berget under och framför altanen (BERG)."""
    return BERG[1] + BERG[2] * (x - BERG[0])


def _stegen() -> list[tuple[str, int, tuple[float, float, float, float]]]:
    """Trappstegens lådor (kant, steg k, (x0, x1, y0, y1)): steg k med överkanten −k STEG_H, från altanens kant ut
    k STEG_DJUP (det övre stegets låda står på den undre). Antalet där berget ligger på z: det nedersta stegets
    underkant närmast berget. Framkanten: steg k från X0 eller där berget faller under −(k + ½) STEG_H, vid närmaste
    bjälke i steget ovanför (som står på det), och ut genom hörnet; sidan, från den högra kroppens hörn till
    framkanten, med lika många steg som hörnet."""
    n = max(1, round(-_berget(X1) / STEG_H) - 1)
    ut: list[tuple[str, int, tuple[float, float, float, float]]] = []
    for k in range(1, n + 1):
        x_k = X0
        if k > 1:
            bor = min(X1, max(X0, BERG[0] + (-(k + 0.5) * STEG_H - BERG[1]) / BERG[2]))
            x_k = min((b[0] for b in _stegets_bjalkar("fram", *ut[-2][2])), key=lambda c: abs(c - bor))
        ut += [("fram", k, (x_k, X1 + k * STEG_DJUP, Y1, Y1 + k * STEG_DJUP)),
               ("sida", k, (X1, X1 + k * STEG_DJUP, Y_HORN + FRI, Y1))]
    return ut


def _stegets_bjalkar(kant: str, x0: float, x1: float, y0: float, y1: float) -> list[tuple[float, float, float, float]]:
    """Stegets bjälkar (x0, x1, y0, y1) tvärs kanten, c/c högst CC_REGEL, bakom sättsteget (och framkantens gavel;
    sidans STEG_VAGG från fasaden)."""
    t = SARG[0]
    if kant == "fram":
        return [(c, c + REGEL[0], y0, y1 - t) for c in _cc(x0 + t, x1 - t, REGEL[0], CC_REGEL)]
    return [(x0, x1 - t, c, c + REGEL[0]) for c in _cc(y0 + STEG_VAGG, y1, REGEL[0], CC_REGEL)]


@cache
def _stegens_plintar() -> list[tuple[float, float, float, float]]:
    """Plintarna under det nedersta stegets bjälkar (x, y, underkant, överkant), där inget steg står under dem: c/c
    högst STEG_PLINT längs bjälken, ned i berget, och där en skulle stå på dräneringens eller dagvattnets ledningar
    flyttad längs bjälken; går det inte, slutar den LEDNING_FRI över röret (på schaktets återfyllning)."""
    lador = _stegen()
    ut = []
    for kant, k, (x0, x1, y0, y1) in lador:
        under = next((b for kk, kk_k, b in lador if kk == kant and kk_k == k + 1), None)
        z1 = -(k + 1) * STEG_H
        z0 = min(PLINT_UK, z1 - 300.0)
        ror = _ledningarna(z0)
        for bx0, bx1, by0, by1 in _stegets_bjalkar(kant, x0, x1, y0, y1):
            if under is not None and under[0] <= bx0 and bx1 <= under[1] and under[2] <= by0 and by1 <= under[3]:
                continue                                                    # står på steget under
            langs_y = kant == "fram"
            lo, hi = (by0, by1) if langs_y else (bx0, bx1)
            n = max(1, math.ceil((hi - lo) / STEG_PLINT))
            for i in range(n):
                mitt = lo + (hi - lo) * (i + 0.5) / n
                fri = False
                for d in sorted(range(-400, 401, 5), key=abs):
                    c = min(max(mitt + d, lo + PLINT_D / 2), hi - PLINT_D / 2)
                    x, y = ((bx0 + bx1) / 2, c) if langs_y else (c, (by0 + by1) / 2)
                    if fri := not ror.contains(Point(x, y)):
                        break
                if not fri:
                    c = min(max(mitt, lo + PLINT_D / 2), hi - PLINT_D / 2)
                    x, y = ((bx0 + bx1) / 2, c) if langs_y else (c, (by0 + by1) / 2)
                ut.append((x, y, z0 if fri else _over_ror(x, y) + LEDNING_FRI, z1))
    return ut


def _over_ror(x: float, y: float) -> float:
    """Den högsta överkanten av dräneringens och dagvattnets rör under en plint i (x, y)."""
    p, r = Point(x, y), dr.D / 2 + LEDNING_FRI + PLINT_D / 2
    return max((max(a[2], b[2]) + dr.D for led in dr.ledningar().values() for a, b in zip(led.vag, led.vag[1:])
                if LineString([a[:2], b[:2]]).distance(p) < r), default=PLINT_UK)


def stegens_former() -> list[Form]:
    """Trappstegens lådor som prismor, för urtaget i berget och uppfyllnaden (mark.py)."""
    return [lada(x1 - x0, y1 - y0, STEG_H, (x0, y0, -(k + 1) * STEG_H)) for _, k, (x0, x1, y0, y1) in _stegen()]


@cache
def lucka() -> tuple[tuple[float, float], list[tuple[float, float]]]:
    """Luckan i däcket över spolrören och spolbrunnarna under altanen (LUCKA_MARGINAL runt dem): var brädorna kapas
    längs brädorna (a0, a1; vid ramen kapas de inte) och brädorna tvärs dem (b) som luckan tar."""
    a0, a1, b0, b1 = _ab()
    r = TRALL_B + FOG if RAM else 0.0
    pkt = [led.vag[0][:2] for led in dr.ledningar().values() if led.typ == "spolrör"]
    pkt += [(br.x + sx * br.d / 2, br.y + sy * br.d / 2) for br in dr.brunnar().values() if br.id != "B1"
            for sx in (-1, 1) for sy in (-1, 1)]
    pkt = [p for p in pkt if X0 < p[0] < X1 and Y0 < p[1] < Y1]
    if not pkt:
        return (a0 + r, a0 + r), []
    aa, bb = [p[0] if LANGS else p[1] for p in pkt], [p[1] if LANGS else p[0] for p in pkt]
    c0, c1 = min(aa) - LUCKA_MARGINAL, max(aa) + LUCKA_MARGINAL
    c0 = a0 + r if c0 - (a0 + r) < LUCKA_MINST else c0
    c1 = a1 - r if (a1 - r) - c1 < LUCKA_MINST else c1
    brador = [(e0, e1) for e0, e1 in _jamnt(b0 + r, b1 - r, TRALL_B, FOG)
              if e1 > min(bb) - LUCKA_MARGINAL and e0 < max(bb) + LUCKA_MARGINAL]
    return (c0, c1), brador


def _barlinor(b0: float, b1: float) -> list[float]:
    """Bärlinornas mitt tvärs brädorna, INDRAG från kanterna och utanför ledningarna som går längs dem: den yttersta
    flyttas in tills mindre än hälften av den går över dräneringens och dagvattnets schakt (_ledningarna)."""
    a0, a1, _, _ = _ab(stomme=True)
    ror = _ledningarna()

    def over(b: float) -> bool:
        x0, x1, y0, y1 = _xy(a0, a1, b, b)
        return bool(ror.intersection(LineString([(x0, y0), (x1, y1)])).length > (a1 - a0) / 2)
    lo, hi = b0 + INDRAG, b1 - INDRAG
    while over(lo) and lo < hi:
        lo += 10.0
    while over(hi) and hi > lo:
        hi -= 10.0
    return [b + BALK[0] for b in _cc(lo - BALK[0], hi + BALK[0], 2 * BALK[0], CC_BALK)]


def montage() -> Montage:
    m = Montage("Altan", beskrivning="Trädäck av grånad tryckimpregnerad trall 34×135 framför 2SV "
                                     f"({'längs' if LANGS else 'tvärs'}, {'med' if RAM else 'utan'} ram)")
    a0, a1, b0, b1 = _ab()
    fa, fb = ("x", "y") if LANGS else ("y", "x")                 # fibrerna längs a respektive b
    zt = (-TRALL_T, 0.0)
    namn = f"Trall {fmt(TRALL_T)}×{fmt(TRALL_B)} grånad"
    # brädorna: ramen och fältet innanför den
    r = TRALL_B + FOG if RAM else 0.0
    nr = 0
    if RAM:
        for i, (c0, c1) in enumerate(((b0, b0 + TRALL_B), (b1 - TRALL_B, b1)), 1):         # längs brädorna
            _del(namn, f"AL-RAM{i}", (*_xy(a0, a1, c0, c1), *zt), fa, TRALL, m)
        for i, (c0, c1) in enumerate(((a0, a0 + TRALL_B), (a1 - TRALL_B, a1)), 3):         # tvärs, vid ändarna
            _del(namn, f"AL-RAM{i}", (*_xy(c0, c1, b0 + r, b1 - r), *zt), fb, TRALL, m)
    (l0, l1), luckans = lucka()
    nl = 0
    for c0, c1 in _jamnt(b0 + r, b1 - r, TRALL_B, FOG):
        bitar = [(a0 + r, l0), (l0, l1), (l1, a1 - r)] if (c0, c1) in luckans else [(a0 + r, a1 - r)]
        for e0, e1 in bitar:
            if e1 - e0 < 1.0:
                continue
            if (e0, e1) == (l0, l1):                                        # luckans bräda
                nl += 1
                _del(namn, f"AL-LU{nl}", (*_xy(e0, e1, c0, c1), *zt), fa, TRALL, m)
            else:
                nr += 1
                _del(namn, f"AL-T{nr:02d}", (*_xy(e0, e1, c0, c1), *zt), fa, TRALL, m)
    # bjälkarna tvärs brädorna (med ram också under ramens inre kant vid ändarna och under luckans kanter),
    # bärlinorna och plintarna
    s0, s1, t0, t1 = _ab(stomme=True)
    lagen = _cc(s0, s1, REGEL[0], CC_REGEL)
    if RAM:
        lagen = sorted(set(lagen) | {a0 + TRALL_B - REGEL[0], a1 - TRALL_B})
    if luckans:
        lagen = sorted(set(lagen) | {c - REGEL[0] / 2 for c in (l0, l1) if a0 + r < c < a1 - r})
    for i, a in enumerate(lagen, 1):
        _del(f"Bjälke tryckimpregnerad {fmt(REGEL[0])}×{fmt(REGEL[1])}", f"AL-B{i:02d}",
             (*_xy(a, a + REGEL[0], t0, t1), Z_BALK, Z_REGEL), fb, TRYCKIMP, m)
    for i, b in enumerate(_barlinor(t0, t1), 1):
        for j, c in enumerate((b - BALK[0], b), 1):
            _del(f"Bärlina tryckimpregnerad {fmt(BALK[0])}×{fmt(BALK[1])}", f"AL-L{i}{'AB'[j - 1]}",
                 (*_xy(s0 + BALK_INDRAG, s1 - BALK_INDRAG, c, c + BALK[0]), Z_PLINT, Z_BALK), fa, TRYCKIMP, m)
    # sargen längs de fria kanterna, under brädorna
    zs = (-TRALL_T - SARG[1], -TRALL_T)
    sarg = f"Sargbräda {fmt(SARG[0])}×{fmt(SARG[1])} grånad"
    _del(sarg, "AL-S1", (X0, X1, Y1 - SARG[0], Y1, *zs), "x", TRALL, m)
    _del(sarg, "AL-S2", (X1 - SARG[0], X1, Y_HORN + FRI, Y1 - SARG[0], *zs), "y", TRALL, m)
    _del(sarg, "AL-S3", (X0, X0 + SARG[0], Y_GAVEL, Y1 - SARG[0], *zs), "y", TRALL, m)
    _trappstegen(m)
    for i, f in enumerate(plintarnas_former(), 1):
        m.lagg(Del(f"Betongplint Ø{fmt(PLINT_D)}", f, BETONG), Placering(), f"AL-P{i:02d}")
    return m


def _trappstegen(m: Montage) -> None:
    """Trappstegen: brädorna längs kanten (också under steget ovanför), bjälkarna, sättsteget och framkantens gavel
    (AL-FS<steg>-…, sidan AL-SS<steg>-…)."""
    namn = f"Trall {fmt(TRALL_T)}×{fmt(TRALL_B)} grånad"
    sarg = f"Sargbräda {fmt(SARG[0])}×{fmt(SARG[1])} grånad"
    t = SARG[0]
    for kant, k, (x0, x1, y0, y1) in _stegen():
        pre = f"AL-{'FS' if kant == 'fram' else 'SS'}{k}"
        zt, zb = -k * STEG_H, -(k + 1) * STEG_H                            # överkant, underkant
        for i in range(STEG_BRADOR * k):
            c0 = (y0 if kant == "fram" else x0) + FOG + i * (TRALL_B + FOG)
            box = (x0, x1, c0, c0 + TRALL_B) if kant == "fram" else (c0, c0 + TRALL_B, y0, y1)
            _del(namn, f"{pre}-T{i + 1:02d}", (*box, zt - TRALL_T, zt), "x" if kant == "fram" else "y", TRALL, m)
        for i, (bx0, bx1, by0, by1) in enumerate(_stegets_bjalkar(kant, x0, x1, y0, y1), 1):
            _del(f"Bjälke tryckimpregnerad {fmt(REGEL[0])}×{fmt(REGEL[1])}", f"{pre}-B{i:02d}",
                 (bx0, bx1, by0, by1, zb, zt - TRALL_T), "y" if kant == "fram" else "x", TRYCKIMP, m)
        if kant == "fram":
            _del(sarg, f"{pre}-S", (x0, x1, y1 - t, y1, zb, zt - TRALL_T), "x", TRALL, m)
            _del(sarg, f"{pre}-G", (x0, x0 + t, y0, y1 - t, zb, zt - TRALL_T), "y", TRALL, m)
        else:
            _del(sarg, f"{pre}-S", (x1 - t, x1, y0, Y1 + k * STEG_DJUP - t, zb, zt - TRALL_T), "y", TRALL, m)
