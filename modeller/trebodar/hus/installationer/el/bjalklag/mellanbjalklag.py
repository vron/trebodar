"""Gruppernas rör från centralen ingjutna i mellanbjälklaget (#50, #51, #87): ett rör per grupp från gruppcentralen i
teknikrummet till gruppens första punkt på plan 1 (../grupper.py), och därifrån vidare mellan punkterna
(../kedjor.py); och källarens grupper som går genom bjälklaget (G17, G18 och G24, ../rum/kallarens_punkter.py).

Rören går upp ur centralens ovansida in i bjälklaget, i två rader mellan underkantsnätets järn: den främre (RAD_A)
ovanför centralen och den bakre (RAD_B) i V3:s cellplast bakom gipsen (rören går snett in i väggen ur centralens
ovansida). Där finns plats för dem väster om ventilationens kanal FF3-K2, som går över centralens östra del. Den
bakre raden har punkterna söder om V3, den främre de andra. Ovanför centralen ligger V3:s vinkeljärn (R-06) i elrörens
övre nivå, så rören går i knippen (ingjutna.knippe): rakt ut ur bandet mellan järnen, den främre raden norrut och den
bakre söderut över V3, och därifrån som ett brett rör med en fil per rör, raka och sneda med mjuka böjar runt det som
de inte får gå genom (ingjutna.py). Den främre raden har ett knippe norrut och ett österut, den bakre ett västerut och
ett österut; varje knippe får ett sammanhängande block av radens stigare, i ordning efter var rören lämnar det. Varje
rör lämnar sitt knippe i en mjuk båge (LAMNA) snett mot sin punkt, det som lämnar först ytterst, och därifrån går de i
tur och ordning runt de andra (Ingjutning.solfjader). De klena (Ø16) går i elrörens övre nivå, över tappvattnet och
golvvärmen (montering.BJALKLAG "MB"), hällens grova rör (Ø20) för sig i den undre, i tappvattnets nivå men runt dess
rör ("MB-UK").

Rören går upp ur bjälklaget lodrätt under punktens dosa, mellan överkantsnätets järn, och därifrån rakt in i dosan
underifrån (../dragning.py). Är punkten i en bärande vägg går röret i stället upp i en lätt vägg till en dragdosa i
innertaket (UPP_I_TAKET), så att inget rör går under stommens bultar (#114). Brandlarmets matningsdosa D01 (BL-D01,
../../brandlarm) matas från allrummets dimmer genom innertaket och en lätt vägg (../kedjor.py).
"""
from __future__ import annotations

import math
from collections.abc import Sequence

from shapely.geometry import LineString, Point
from shapely.geometry.base import BaseGeometry

from ...montering import BJALKLAG, KALLARTAK, PLAN, Vek, kallartak, langs_vaggen, tak, vagg, vid_tak
from ...plattan import Karta, Punkt, ledning
from ...strak import fri
from ...teknikrum import GRUPPCENTRAL, Z_GC_TOPP
from .. import lakt
from ..dragning import upp_i_vaggen, upp_till_dosan
from ..grupper import BRANDLARM_D01, GRUPPER
from ..katalog import BRANDLARM_MATNING, DRAGDOSA_TAK, FXP16, FXP20
from ..punkter import Dosa, Punkt as ElPunkt, Ror
from ..rum import allrum, badrum, gastrum, hall, kallarens_punkter as KP, kok, kontor, sovrum
from .ingjutna import KALLAREN, NIVAER, PLAN1, Ingjutning, Ror3, hinder, ingjutet, kartor_el, knippe

NAMN = "Mellanbjälklag"

_TOPP = GRUPPCENTRAL.anslutningar["topp"]
X_RAD = (_TOPP[0] - 292.0, 2735.0)          # rörens x på centralens ovansida: från dess västra kant till kanalen
CC = 21.0                                    # stigarnas avstånd i raderna (Ø16, 5 mm emellan)
RAD_A = _TOPP[1] - 42.0                      # främre raden, ovanför centralens framkant
RAD_B = _TOPP[1] + 40.0                      # bakre raden, ovanför centralens bakkant
SPEL = 5.0
Y_V3 = 9170.0                                # V3:s mitt: punkterna söder därom nås ur den bakre raden
UTANFOR = {"A": 8560.0, "B": 9330.0}         # y strax utanför bandet över centralen (norr) och V3 (söder)
LAMNA = 400.0                                # bågen där ett rör lämnar sitt knippe, högst


def _rad(y: float, z: float, r: float = 8.0, over_v3: Sequence[float] = ()) -> list[float]:
    """Stigarnas x i en rad: tätt (CC) från centralens västra kant, där röret går fritt mellan järnen från källarens
    tak till nivån z (och, för rören som går ur raden över V3, i nivåerna över V3 mellan dess järn)."""
    ut: list[float] = []
    x = X_RAD[0]
    while x <= X_RAD[1]:
        if (not ut or x - ut[-1] >= CC - 1e-6) and fri(Point(x, y), r, KALLARTAK, z, SPEL) and all(
                fri(LineString([(x, y), (x, y + 400.0)]), 10.0, h - 1.0, h + 1.0, SPEL) for h in over_v3):
            ut.append(x)
        x += 1.0
    return ut


_RADER = {"A": (RAD_A, _rad(RAD_A, BJALKLAG["MB"])),
          "B": (RAD_B, _rad(RAD_B, BJALKLAG["MB"], over_v3=(BJALKLAG["MB"], BJALKLAG["MB-UK"])))}

_PUNKT: dict[str, ElPunkt] = {p.id: p for m in (allrum, badrum, gastrum, hall, kok, kontor, sovrum) for p in m.PUNKTER}
# hällens grova rör i den undre nivån, de andra i den övre
GROVA = {"G10": (FXP20, "MB-UK")}
# grupperna på plan 1: gruppens rör från centralen till dess första punkt
_PLAN1 = [(g.id, g.punkter[0]) for g in GRUPPER if g.punkter[0] in _PUNKT]

# grupperna vars första punkt sitter i en bärande vägg (#114): röret från centralen går inte in under väggen (genom
# bultarnas spärrzon, ../../passager.py) utan upp i en lätt vägg till en dragdosa i innertaket, och därifrån i
# innertakets installationsskikt till punkten (../kedjor.py). Hallens grupper går upp i hallgarderobens väggbit L20,
# väster om 1B:s spärrzon, kökets i inbyggnadens front L15 nära 3NV (utanför plattans kantband); dosorna sitter inne
# i garderoben och skafferiet. grupp: (väggen, u längs den, dragdosan)
UPP_I_TAKET: dict[str, tuple[str, float, str]] = {
    "G01": ("L20", 90.0, "HA-DD1"),
    "G02": ("L20", 140.0, "HA-DD2"),
    "G03": ("L20", 190.0, "HA-DD3"),
    "G06": ("L20", 240.0, "HA-DD4"),
    "G10": ("L15", 2445.0, "KO-DD1"),
    "G11": ("L15", 2345.0, "KO-DD2"),
    "G12": ("L15", 2245.0, "KO-DD3"),
}
DOSORNA_UT, DOSORNA_CC = 100.0, 160.0       # dosorna från väggen in i garderoben och skafferiet, och emellan


def _upp_i_taket(g: str) -> tuple[Punkt, tuple[Vek, ...], Dosa]:
    """Gruppens stigare i den lätta väggen (mellan överkantsnätets järn), vägen därifrån upp i väggen och in i
    installationsskiktet, och dragdosan (ut från väggen, de följande längre ut)."""
    kod, u, did = UPP_I_TAKET[g]
    typ, niva = GROVA.get(g, (FXP16, "MB"))
    a, _ = upp_i_vaggen(kod, u, 0.0, niva, typ.ytterdiameter)
    topp, skikt = vid_tak(kod, langs_vaggen(kod, a), sida=-1)
    n = vagg(kod, u, 0.0, sida=-1).normal
    j = [h for h in UPP_I_TAKET if UPP_I_TAKET[h][0] == kod].index(g)
    ut = DOSORNA_UT + j * DOSORNA_CC - 100.0            # vid_tak går 100 mm ut i skiktet
    x, y = skikt[0] + ut * n[0], skikt[1] + ut * n[1]
    m = tak(x, y)
    dosa = Dosa(did, DRAGDOSA_TAK, tak(lakt.mellan_lakten(m.ref, x, y), y))
    return (a[0], a[1]), ((a[0], a[1], topp[2]), skikt), dosa


_TAKET = {g: _upp_i_taket(g) for g in UPP_I_TAKET}




def _malet(p: str, typ_niva: tuple[object, str]) -> tuple[Punkt, tuple[Vek, ...]]:
    """Punktens stigare i plan och vägen därifrån upp i dosan."""
    typ, niva = typ_niva
    upp = upp_till_dosan(_PUNKT[p], niva=niva, d=typ.ytterdiameter)       # type: ignore[attr-defined]
    return (upp[0][0], upp[0][1]), upp[1:]


def _grupprören() -> tuple[list[Ror], list[Ror3]]:
    """Gruppernas rör från centralen (plan 1:s och källarens som går genom bjälklaget): raden efter var punkten
    ligger, knippena efter riktningen, och vart och ett från där det lämnar sitt knippe till punkten genom elrörens
    nivåer. Ger rören och stigarna genom bjälklaget (hinder för de andra rören)."""
    mal = {g: _malet(p, GROVA.get(g, (FXP16, "MB"))) if g not in _TAKET else _TAKET[g][:2] for g, p in _PLAN1}
    mal |= {g: (b, efter) for g, (_, b, efter) in KP.FRAN_CENTRALEN.items()}
    till = (dict(_PLAN1) | {g: p for g, (p, _, _) in KP.FRAN_CENTRALEN.items()}
            | {g: d.id for g, (_, _, d) in _TAKET.items()})
    # källarens punkter i ett band av vinkeljärn i den övre nivån (fläktens anslutning i V20:s cellplast): röret når
    # dem genom ledningen ut ur bandet, som knippet går mot (inte mot stigaren bakom den)
    ovre = kartor_el(FXP16.ytterdiameter / 2)[0]
    ledb: dict[str, list[Punkt]] = {}
    for g in KP.FRAN_CENTRALEN:
        if any(b.contains(Point(mal[g][0])) for b in ovre.band):
            ledb[g] = ledning(ovre, mal[g][0], (X_RAD[0], RAD_B))
    # hindren: punkternas stigare (upp till plan 1, ned till källaren) och alla stigare i raderna över centralen
    alla: list[Ror3] = [(x, y, 8.0, BJALKLAG["MB-UK"] - 10.0, PLAN[1]) if g not in KP.FRAN_CENTRALEN else
                        (x, y, 8.0, KALLARTAK, BJALKLAG["MB"] + 8.0) for g, ((x, y), _) in mal.items()]

    def nivaer(g: str) -> tuple[str, ...]:
        return ("MB-UK",) if g in GROVA else NIVAER

    def kost(g: str) -> tuple[float, float]:
        return KALLAREN if g in KP.FRAN_CENTRALEN else PLAN1

    def kartorna(g: str) -> tuple[Karta, ...]:
        return kartor_el(GROVA.get(g, (FXP16, "MB"))[0].ytterdiameter / 2)

    def hindren(g: str, s: Punkt) -> tuple[list[BaseGeometry], ...]:
        return hinder(GROVA.get(g, (FXP16, "MB"))[0].ytterdiameter / 2, list(alla), KP.DOSOR, utom=(s, mal[g][0]))
    # raden: den bakre (söderut över V3) för punkterna söder om V3, den främre (norrut) för de andra; förslaget till
    # väg (för riktningen ut ur bandet) från en punkt utanför bandet mitt för raden
    val: dict[str, tuple[str, Sequence[Vek]]] = {}
    for g in mal:
        namn = "B" if mal[g][0][1] > Y_V3 else "A"
        y, xs = _RADER[namn]
        start = (xs[len(xs) // 2], UTANFOR[namn])
        try:
            via, _ = ingjutet(kartorna(g), start, mal[g][0], fran=nivaer(g), till=nivaer(g), hinder_=hindren(g, start),
                              kost=kost(g))
        except ValueError:
            via = ((*start, BJALKLAG["MB"]), (*mal[g][0], BJALKLAG["MB"]))
        val[g] = (namn, ((xs[len(xs) // 2], y, BJALKLAG["MB"]), *via))
    # knippena: den främre raden delad efter riktningen (norrut och österut), den bakre efter sidan (västerut till
    # hallen och österut till ön och källarens stora rum); hällens grova rör för sig i den undre nivån. Varje knippe
    # får ett sammanhängande block av radens stigare, i ordning efter riktningen.
    def riktning(g: str) -> float:
        linje = LineString([q[:2] for q in val[g][1]])
        a_, b_ = linje.interpolate(min(400.0, linje.length / 2)), linje.interpolate(min(1500.0, linje.length))
        return math.atan2(b_.x - a_.x, abs(b_.y - a_.y))
    knippen: dict[str, list[str]] = {}
    for g in val:
        if g in GROVA:
            continue
        namn = val[g][0]
        knippen.setdefault(namn + ("O" if riktning(g) > math.radians(40.0) else "V") if namn == "A" else
                           namn + ("O" if mal[g][0][0] > X_RAD[1] else "V"), []).append(g)
    stigare: dict[str, Punkt] = {}
    vagar: dict[str, tuple[list[Punkt], list[float]]] = {}
    for namn, (y, xs) in _RADER.items():
        grova = [g for g in GROVA if val[g][0] == namn]
        delar = [knippen[n] for n in (f"{namn}V", f"{namn}O") if n in knippen]
        antal = sum(len(d) for d in delar) + len(grova)
        if antal > len(xs):
            raise ValueError(f"raden {namn} över centralen har {len(xs)} stigare, {antal} rör behövs")
        lediga = list(xs)
        for d in delar:
            block, lediga = (lediga[:len(d)], lediga[len(d):]) if d is delar[0] else (lediga[-len(d):], lediga[:-len(d)])
            ut_ = (0.0, -1.0) if namn == "A" else (0.0, 1.0)
            slut_ = max((mal[g][0] for g in d), key=lambda q: math.dist(q, (block[0], y)))
            hd = hinder(FXP16.ytterdiameter / 2, list(alla), KP.DOSOR, utom=[*((x, y) for x in block), slut_])
            st, vg = knippe(kartorna(d[0]), [(x, y) for x in block], ut_,
                            {g: (ledb[g] or [mal[g][0]])[-1] if g in ledb else mal[g][0] for g in d}, slut_, hd)
            stigare.update(st)
            vagar.update(vg)
        for g in grova:                            # det grova röret där det har mest plats till grannarna
            anv = [q[0] for q in stigare.values() if abs(q[1] - y) < 1.0]
            x = max(lediga, key=lambda x_: min((abs(x_ - u) for u in anv), default=1e9))
            stigare[g] = (x, y)
            lediga.remove(x)
    alla += [(x, y, 8.0, Z_GC_TOPP, BJALKLAG["MB"] + 8.0) for x, y in stigare.values()]
    # rören i tur och ordning: de som inte går i ett knippe först, sedan i ordning efter var de lämnar sitt knippe
    bestallningar: list[dict[str, object]] = []
    for g in sorted(stigare, key=lambda g_: (g_ in vagar, LineString(vagar[g_][0]).length if g_ in vagar else 0.0)):
        typ = GROVA.get(g, (FXP16, "MB"))[0]
        s_ = stigare[g]
        z = BJALKLAG["MB"]
        upp = (s_[0], s_[1], Z_GC_TOPP)
        if g in vagar:
            pts, rr = vagar[g]
            bestallningar.append(dict(id_=f"{g}-M", typ=typ, fran="GC", till=till[g], a=pts[-1], b=mal[g][0],
                                      fore=(upp, *((q[0], q[1], z) for q in pts[:-1])), fore_radier=(0.0, *rr[:-1]),
                                      bage_a=LAMNA, led_a={"MB": []}, efter=mal[g][1], nivaer=(("MB",), nivaer(g)),
                                      kost=kost(g), **({"led_b": {"MB": ledb[g]}} if g in ledb else {})))
        else:
            bestallningar.append(dict(id_=f"{g}-M", typ=typ, fran="GC", till=till[g], a=s_, b=mal[g][0], fore=(upp,),
                                      efter=mal[g][1], nivaer=(nivaer(g), nivaer(g)), kost=kost(g)))
    ing = Ingjutning(alla, KP.DOSOR)
    ut = ing.solfjader(bestallningar)
    return sorted(ut, key=lambda r: r.id), ing.stigare


# brandlarmets matningsdosa D01 (../../brandlarm/larm.py): en punkt utan egen geometri, matad från allrummets dimmer;
# och dragdosorna i innertaket för UPP_I_TAKET
D01 = BRANDLARM_D01
PUNKTER = [
    Dosa("BL-D01", BRANDLARM_MATNING, kallartak(*D01)),
    *(d for _, _, d in _TAKET.values()),
]

# gruppernas rör från centralen, och alla stigare genom bjälklaget (upp ur centralen, upp till plan 1 och ned till
# källaren) som hinder för de andra rören i bjälklaget
ROR, STIGARE = _grupprören()
