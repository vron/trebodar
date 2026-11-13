"""Brandlarmet: brandvarnare för 230 V med reservbatteri, trådbundet sammankopplade så att alla larmar när en larmar.
Radio genom betongbjälklaget mellan källaren och plan 1 vore osäkert, så varnarna kopplas ihop med kabel.

Placeringen: en brandvarnare i varje huvudutrymme, högt i taket nära rummets mitt, eftersom de höga snedtaken gör att
röken tar lång tid till andra rum. På plan 1 i köket, sovrummet, vardagsrummet och hallen, i snedtaket AVSTAND_NOCK
från nocken i planet och mellan installationsskiktets läkt (som armaturerna, el/lakt.py); i källaren vid trappan och i
det öppna rummet norr om den, i betongtaket.

Kabeln (KABEL, rund Ø KABEL_D): från matningsdosan (D01, matad från grupp G02 i gruppcentralen: elens rör G02-R2 från
allrummets dosa AL-B2 ned i väggen L19, el/kedjor.py) som en stam klammad under källarens tak med kopplingsdosor, och
därifrån i en stigare per huskropp upp genom mellanbjälklaget (i hylsa) och i en innerväggs regelfack till innertaket,
där den går i installationsskiktets övre del (OVER_MITT över skiktets mitt, så att den går över elens rör, som ligger
mitt i skiktet) till varnarnas takdosor. Innertakets installationsskikt slutar vid dalbalkarna, så huskropparna förbinds i källaren. Stigarna står i
ett regelfack och går fria från bjälklagets järn och de ingjutna rören (..strak.mellan_jarnen, som
köldbärarledningarna); vägarna går med monteringens punkter (..montering: vid_tak, i_vagg, under_kallartak) som elens
rör. Koordinater i mm (K-05), z från plan 1:s golv.
"""
from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from functools import cache

from shapely.geometry import LineString, Point
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from trebodar import skelett as S
from trebodar.hus.grund import kallarvaggar as K
from trebodar.hus.installationer.el import lakt
from trebodar.hus.installationer.el.grupper import BRANDLARM_D01
from trebodar.hus.installationer.el.installation import installation
from trebodar.hus.invandigt import kallarens_innervaggar as KV
from trebodar.hus.invandigt import vaggar
from trebodar.hus.invandigt.lattvaggar import vaggdef
from trebodar.hus.stomme import lagen
from trebodar.hus.stomme.prefab.takbalkar.takbalkar import TF3

from ..genomforingar import Genomforing, Stycke, genomforingar, vaggarna
from ..passager import PASSAGER
from ..golvvarme.system import golvvarme
from ..montering import (I_TAKET, KALLARTAK, PLAN, Montering, Vek, flytt, i_tak, i_vagg, kallartak, langs_taket,
                        tak, under_kallartak, vid_tak)
from ..strak import mellan_jarnen
from ..vatten.system import vatten


@dataclass(frozen=True)
class Typ:
    kod: str
    namn: str
    diameter: float
    hojd: float


# produkterna är inte valda: måtten är typiska
BRANDVARNARE = Typ("BV230", "Brandvarnare 230 V med reservbatteri, optisk, trådbunden sammankoppling (SS-EN 14604, ej "
                            "vald)", 120.0, 48.0)
TAKDOSA = Typ("TAKDOSA", "Takdosa i innertakets installationsskikt, bakom gipsen (ej vald)", 68.0, 40.0)
YTDOSA = Typ("YTDOSA", "Kopplingsdosa utanpåliggande, under betongen (ej vald)", 80.0, 40.0)
KABEL_D = 10.0                               # kabeln 4G1,5, rund (installationskabel för fast förläggning)
KABEL = "installationskabel 4G1,5 (fas, nolla, skyddsjord och larmledaren), i hylsa genom bjälklaget"
AVSTAND_NOCK = 600.0                         # brandvarnarna i snedtaken: avståndet från nocken i planet
D_UNDER = 10.0                               # kabeln klammad under källarens tak: mitt så långt under betongen
OVER_ROREN = 14.0                            # i innertakets skikt över elens rör, där kabeln korsar dem
OVER_MITT = 15.0                             # kabeln i innertakets installationsskikt: så långt över skiktets mitt
SPEL_REGEL = 10.0                            # stigarna i regelfacket: fritt från reglarna
SPEL_ROR = 10.0                              # stigarna genom bjälklaget: fritt från de ingjutna rören


@dataclass(frozen=True)
class Varnare:
    id: str
    rum: str
    plan: int                                # 1 eller 0 (källaren)
    lage: Montering
    takfall: str = ""                        # snedtaket (plan 1)


@dataclass(frozen=True)
class Dosa:
    id: str
    namn: str
    lage: Montering


@dataclass(frozen=True)
class Kabel:
    """En kabel från en punkt till en annan längs vägen (ändarna är punkternas anslutningar)."""
    id: str
    fran: str
    till: str
    vag: tuple[Vek, ...]


def _i_snedtaket(takfall: str, nock_x: float, sida: int, y: float) -> Montering:
    """I snedtaket AVSTAND_NOCK från nocken (sida −1 mot minskande x), mitt mellan läkten."""
    return tak(lakt.mellan_lakten(takfall, nock_x + sida * AVSTAND_NOCK, y), y)


def anslutning(m: Montering) -> Vek:
    """Där kabeln ansluter: på plan 1 i takdosan, i installationsskiktets övre del bakom gipsen, i källaren i dosan
    under betongen."""
    if m.yta == "tak" and m.ref != "MB":
        return flytt(m.punkt, m.normal, -(I_TAKET + OVER_MITT))
    return flytt(m.punkt, m.normal, D_UNDER)


def _reglar(kod: str) -> list[tuple[float, float]]:
    """Väggens reglar och stolpar (u0, u1) som står från golvet till taket."""
    if kod not in S.INNERVAGGAR:
        return vaggar.reglarna(kod)
    v = S.INNERVAGGAR[kod]
    Pi = v.placering().invers()
    ut = []
    for d in lagen.vagg(kod):
        x0, y0, z0, x1, y1, z1 = d.lada
        if z0 < 500.0 and z1 > 2000.0:
            us = [Pi.punkt((x, y, 0.0))[0] for x in (x0, x1) for y in (y0, y1)]
            ut.append((min(us), max(us)))
    return sorted(ut)


@cache
def _ingjutna() -> BaseGeometry:
    """De andra installationernas ingjutna rör i mellanbjälklaget (tappvattnet, golvvärmen, elens rör) i plan, med
    deras radie, kabelns och spelet: stigarna går utanför."""
    el = installation()
    ror = [(st.a, st.b, max(st.yttre)) for st in [*vatten().stycken(), *golvvarme().stycken()]]
    ror += [(p, q, r.typ.ytterdiameter) for r in el.ror.values() for p, q in zip(el.vag(r), el.vag(r)[1:])]
    ytor = []
    for a, b, d in ror:
        if min(a[2], b[2]) < 0.0 and max(a[2], b[2]) > -S.H_BJALKLAG:
            r = d / 2 + KABEL_D / 2 + SPEL_ROR
            ytor.append(LineString([a[:2], b[:2]]).buffer(r) if math.dist(a[:2], b[:2]) > 0.1
                        else Point(a[:2]).buffer(r))
    return unary_union(ytor)


def stigaren(kod: str, p: tuple[float, float]) -> tuple[float, float]:
    """Stigarens läge (u, w) i väggen: i regelfacket närmast punkten p (så nära som facket tillåter), förskjutet längs och
    tvärs väggen så att kabeln går fritt från bjälklagets järn (mellan_jarnen) och stannar i facket och väggen. I en
    bärande vägg bara i dess installationspassager (../passager.py), där inga bultar borras (#114)."""
    v = vaggdef(kod)
    u_onskat = (p[0] - v.origo[0]) * v.u[0] + (p[1] - v.origo[1]) * v.u[1]
    reglar = [(0.0, 0.0), *_reglar(kod), (v.langd, v.langd)]
    fri = KABEL_D / 2 + SPEL_REGEL
    fack = [(a[1], b[0]) for a, b in zip(reglar, reglar[1:]) if b[0] - a[1] > 2 * fri]
    if kod in S.INNERVAGGAR:
        fack = [(max(f0, p.u0), min(f1, p.u1)) for f0, f1 in fack for p in PASSAGER.get(kod, ())
                if min(f1, p.u1) - max(f0, p.u0) > 2 * fri]
    tvars = (v.tjocklek - KABEL_D) / 2 - 5.0                # i väggens tjocklek, 5 mm från skikten
    for f0, f1 in sorted(fack, key=lambda f: abs(min(max(u_onskat, f[0] + 100.0), f[1] - 100.0) - u_onskat)):
        c = min(max(u_onskat, f0 + fri), f1 - fri)
        q = i_vagg(kod, c, 0.0)
        try:
            dx, dy = mellan_jarnen([(q[0], q[1])], -S.H_BJALKLAG, 0.0, KABEL_D / 2, langs=v.u, tvars=tvars,
                                   undvik=_ingjutna(), langst=min(300.0, (f1 - f0) / 2))
        except ValueError:
            continue
        u = c + dx * v.u[0] + dy * v.u[1]
        w = v.tjocklek / 2 + dx * v.w[0] + dy * v.w[1]
        if f0 + fri <= u <= f1 - fri:
            return u, w
    raise ValueError(f"{kod}: inget regelfack nära ({p[0]:g}, {p[1]:g}) där stigaren går fri från järnen")


@dataclass(frozen=True)
class Brandlarm:
    varnare: dict[str, Varnare]
    dosor: dict[str, Dosa]
    kablar: dict[str, Kabel]

    def punkt(self, id_: str) -> Montering:
        return (self.varnare[id_] if id_ in self.varnare else self.dosor[id_]).lage


def _hogt(x: float, y: float) -> Vek:
    """I installationsskiktets övre del, över elens rör (som ligger mitt i skiktet) som kabeln korsar."""
    m = tak(x, y)
    return flytt(m.punkt, m.normal, -(I_TAKET + OVER_ROREN))


def _upp(kod: str, p: tuple[float, float], sida: int, mal: Montering,
         forbi: tuple[tuple[float, float], ...] = ()) -> tuple[float, tuple[Vek, ...]]:
    """Stigaren i väggen kod nära punkten p: vägen från källarens tak under den upp genom bjälklaget, i regelfacket
    till innertaket på sidan sida och rakt i installationsskiktet (mellan läkten, över nocken, förbi punkterna forbi i
    plan) till varnarens dosa (mal)."""
    u, w = stigaren(kod, p)
    v = vaggdef(kod)
    dw = (w - v.tjocklek / 2) * v.w[0], (w - v.tjocklek / 2) * v.w[1]      # stigaren förskjuten tvärs väggen
    golv = i_vagg(kod, u, 0.0)
    golv = (golv[0] + dw[0], golv[1] + dw[1], golv[2])
    vagg_tak, skikt = vid_tak(kod, u, sida)
    skikt = flytt(skikt, tak(skikt[0], skikt[1]).normal, -OVER_MITT)          # i skiktets övre del
    vagg_tak = (vagg_tak[0] + dw[0], vagg_tak[1] + dw[1], skikt[2])
    a = anslutning(mal)
    genom = [i_tak(skikt[0], skikt[1]), *(i_tak(x, y) for x, y in forbi), i_tak(a[0], a[1])]
    mellan = [_hogt(q[0], q[1]) for b, c in zip(genom, genom[1:]) for q in langs_taket(b, c)[1:]][:-1]
    vag = (under_kallartak(golv[0], golv[1], D_UNDER), golv, vagg_tak, skikt, *mellan, a)
    return u, vag


def _rensa(vag: Sequence[Vek]) -> tuple[Vek, ...]:
    """Vägen utan punkter som ligger på varandra eller mitt på en rak sträcka."""
    ut: list[Vek] = []
    for p in vag:
        if ut and math.dist(p, ut[-1]) < 0.5:
            continue
        if len(ut) >= 2:
            a, b = ut[-2], ut[-1]
            u = [b[i] - a[i] for i in range(3)]
            w = [p[i] - b[i] for i in range(3)]
            kryss = math.hypot(u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0])
            if kryss < 1e-6 * math.dist(a, b) * math.dist(b, p) + 1e-9 and sum(u[i] * w[i] for i in range(3)) > 0:
                ut[-1] = p
                continue
        ut.append(p)
    return tuple(ut)


# K05 under källarens tak från rummet norr om trapphallen söderut till Y_K05 och därifrån österut, söder om
# ljuslinjerna i det rummet (el/rum/kallare.py)
Y_K05 = 4400.0                  # mellan pelarna P16 och P14 i KL5, norr om P15 i det stora rummet
Y_D01 = 150.0                   # K01 och K07 från D01 först norrut, förbi elröret KA-B2-LC upp i bjälklaget
# K02 över nocken söder om badrummets elrör G07-R1 och i hallens tak väster om garderoben (elens dragdosor i dess tak)
FORBI_HALLEN = ((2500.0, 7300.0), (1450.0, 7600.0))


@cache
def brandlarm() -> Brandlarm:
    """Brandvarnarna, dosorna och kablarna."""
    nb1, nb3, nb5 = S.BALKAR["NB1"].x, S.BALKAR["NB3"].x, S.BALKAR["NB5"].x
    varnare = {v.id: v for v in (
        Varnare("BV-KO", "Köket", 1, _i_snedtaket("3NV", nb1, 1, 10400.0), "3NV"),
        Varnare("BV-SV", "Sovrummet", 1, _i_snedtaket("2NV", nb3, 1, 3750.0), "2NV"),
        Varnare("BV-VR", "Vardagsrummet", 1, _i_snedtaket("1SO", nb5, -1, 12700.0), "1SO"),
        Varnare("BV-HA", "Hallen", 1, _i_snedtaket("1SO", nb5, -1, 9300.0), "1SO"),
        Varnare("BV-KT", "Källaren vid trappan", 0, kallartak(6600.0, 5600.0)),
        Varnare("BV-KN", "Källaren, rummet norr om trappan", 0, kallartak(6600.0, 2700.0)),
    )}
    # stigarna, i lätta väggar (inte genom de bärande väggarnas spärrzoner, #114): hallen och vardagsrummet genom
    # badrummets väggbit L19 bredvid matningsdosan (vänstra huskroppen, över badrummet och nocken till hallen),
    # sovrummet genom garderobens sneda hörn GB och köket genom L4, nära varnarnas x
    gb = vaggdef("GB")
    u_v, upp_v = _upp("L19", (BRANDLARM_D01[0] - 200.0, BRANDLARM_D01[1]), 1, varnare["BV-HA"].lage,
                      forbi=FORBI_HALLEN)
    u_m, upp_m = _upp("GB", (gb.origo[0] + gb.u[0] * gb.langd * 0.85, gb.origo[1] + gb.u[1] * gb.langd * 0.85), -1,
                      varnare["BV-SV"].lage)
    u_h, upp_h = _upp("L4", (varnare["BV-KO"].lage.punkt[0], vaggdef("L4").origo[1]), 1, varnare["BV-KO"].lage)
    (xv, _, _), (xm, _, _), (xh, yh, _) = upp_v[0], upp_m[0], upp_h[0]
    dosor = {d.id: d for d in (
        Dosa("D01", "Matningsdosa: matningen från elcentralen, grupp G02 (el/grupper.py)", kallartak(*BRANDLARM_D01)),
        Dosa("DH", "Kopplingsdosa under stigaren till köket (L4)", kallartak(xh, yh)),
    )}
    a = {k: anslutning(v.lage) for k, v in varnare.items()} | {k: anslutning(d.lage) for k, d in dosor.items()}
    z = KALLARTAK - D_UNDER
    kt, kn = a["BV-KT"], a["BV-KN"]
    y_d01 = a["D01"][1] - Y_D01                                    # norr om D01, förbi källarens elrör KA-B2-LC
    x_tf3 = (TF3.x_upp + nb5) / 2                                  # förbi takfönstret TF3, mellan det och nocken,
    hogt = _hogt
    kablar = [
        Kabel("K01", "D01", "BV-KT", (a["D01"], (a["D01"][0], y_d01, z), (kt[0], y_d01, z), kt)),
        Kabel("K02", "D01", "BV-HA", (a["D01"], (xv, a["D01"][1], z), *upp_v)),
        Kabel("K03", "BV-HA", "BV-VR", (a["BV-HA"], hogt(x_tf3, a["BV-HA"][1]), hogt(x_tf3, a["BV-VR"][1]),
                                         a["BV-VR"])),
        Kabel("K04", "BV-KT", "BV-KN", (kt, kn)),
        Kabel("K05", "BV-KN", "DH", (kn, (kn[0], Y_K05, z), (xh, Y_K05, z), a["DH"])),
        Kabel("K06", "DH", "BV-KO", upp_h),
        Kabel("K07", "D01", "BV-SV", (a["D01"], (a["D01"][0], y_d01, z), (xm, y_d01, z), *upp_m)),
    ]
    return Brandlarm(varnare, dosor, {k.id: Kabel(k.id, k.fran, k.till, _rensa(k.vag)) for k in kablar})


def langd(vag: Sequence[Vek]) -> float:
    return sum(math.dist(p, q) for p, q in zip(vag, vag[1:]))


def bojar(vag: Sequence[Vek]) -> float:
    """Böjarnas summa [°] längs vägen."""
    ut = 0.0
    for a, b, c in zip(vag, vag[1:], vag[2:]):
        u = [b[i] - a[i] for i in range(3)]
        w = [c[i] - b[i] for i in range(3)]
        cos = sum(p * q for p, q in zip(u, w)) / math.dist(a, b) / math.dist(b, c)
        ut += math.degrees(math.acos(max(-1.0, min(1.0, cos))))
    return ut


def stycken() -> list[Stycke]:
    return [Stycke(r.id, p, q, KABEL_D, KABEL_D, True, matt=f"Ø{KABEL_D:g}") for r in brandlarm().kablar.values()
            for p, q in zip(r.vag, r.vag[1:])]


def genomforingarna() -> tuple[list[Genomforing], list[str]]:
    return genomforingar(stycken())


def kontroll() -> tuple[list[str], list[str]]:
    """(fel, anmärkningar): att alla varnare är sammankopplade med matningen, att varje plan har en varnare, dosornas
    plats mellan läkten, varnarnas avstånd till väggar, armaturer och nocken, kablarnas böjar och genomföringarna."""
    b = brandlarm()
    fel, anm = list(genomforingarna()[1]), []
    # sammankopplingen: alla varnare nås från matningsdosan
    granne: dict[str, set[str]] = {}
    for r in b.kablar.values():
        for p in (r.fran, r.till):
            if p not in b.varnare and p not in b.dosor:
                fel.append(f"{r.id}: punkten {p} finns inte")
        granne.setdefault(r.fran, set()).add(r.till)
        granne.setdefault(r.till, set()).add(r.fran)
    nadda, kvar = {"D01"}, ["D01"]
    while kvar:
        for q in granne.get(kvar.pop(), set()) - nadda:
            nadda.add(q)
            kvar.append(q)
    for v in b.varnare.values():
        if v.id not in nadda:
            fel.append(f"{v.id}: inte sammankopplad med de andra (ingen kabel från matningsdosan)")
    for plan, namn in ((1, "plan 1"), (0, "källaren")):
        if not any(v.plan == plan for v in b.varnare.values()):
            fel.append(f"{namn}: ingen brandvarnare")
    # varnarna: dosan mellan läkten, avståndet till väggarna (minst 500 mm), till armaturerna och till nocken
    vaggytor = unary_union([y for y, _, _, _ in vaggarna().values()])
    armaturer = _armaturer()
    for v in b.varnare.values():
        x, y, _ = v.lage.punkt
        if v.plan == 1:
            halv_x = lakt.i_planet(TAKDOSA.diameter / 2)
            for lk in lakt.krockar(v.takfall, x, y, halv_x, TAKDOSA.diameter / 2):
                fel.append(f"{v.id}: takdosan tar i läkten x {lk[0]:.0f}–{lk[1]:.0f}")
            nock = min(abs(x - bl.x) for bl in S.BALKAR.values() if bl.typ == "nock")
            anm.append(f"{v.id} ({v.rum}): {v.lage.punkt[2] - PLAN[1]:.0f} mm över golvet, {nock:.0f} mm från nocken")
            d_vagg = vaggytor.distance(Point(x, y))
        else:
            anm.append(f"{v.id} ({v.rum}): i betongtaket, {v.lage.punkt[2] - PLAN[0]:.0f} mm över golvet")
            d_vagg = _kallarvaggarna().distance(Point(x, y))
        if d_vagg < 500.0:
            fel.append(f"{v.id}: {d_vagg:.0f} mm från väggen (minst 500)")
        for aid, (g, az) in armaturer.items():
            d = g.distance(Point(x, y))
            if d < 500.0 and abs(az - v.lage.punkt[2]) < 1500.0:
                anm.append(f"{v.id}: {d:.0f} mm från armaturen {aid}")
    for r in b.kablar.values():
        if (bj := bojar(r.vag)) > 270.0 + 1e-6:
            anm.append(f"{r.id}: kabeln böjer {bj:.0f}° sammanlagt")
    total = sum(langd(r.vag) for r in b.kablar.values()) / 1000.0
    anm.append(f"{len(b.varnare)} brandvarnare, {len(b.dosor)} dosor, {len(b.kablar)} kablar, {total:.1f} m {KABEL}")
    anm.append("matningen: grupp G02 i gruppcentralen, elens rör G02-R2 till matningsdosan D01 (E-01)")
    return fel, anm


def _armaturer() -> dict[str, tuple[BaseGeometry, float]]:
    """Elinstallationens armaturer i plan (linsens läge; ljuslinjerna hela den lysande linjen) och höjd, för
    avståndet till brandvarnarna."""
    punkter = installation().utdrag()["punkter"]
    assert isinstance(punkter, dict)
    return {pid: ((LineString([p["linje"]["a"][:2], p["linje"]["b"][:2]]) if "linje" in p else Point(p["lins"][:2])),
                  p["lins"][2]) for pid, p in punkter.items() if p["slag"] == "lampa"}


def _kallarvaggarna() -> BaseGeometry:
    """Källarväggarnas och källarens innerväggars ytor (gipsen) i plan."""
    return unary_union([K.i_plan(-1000.0).buffer(13.0, join_style=2)]
                       + [v.stomme().buffer(13.0, join_style=2) for v in KV.VAGGAR.values()])


def utdrag() -> dict[str, object]:
    """Varnarna, dosorna, kablarna och genomföringarna för ritningen och listan, som JSON."""
    b = brandlarm()
    return {
        "typer": {t.kod: {"namn": t.namn, "diameter": t.diameter, "hojd": t.hojd}
                  for t in (BRANDVARNARE, TAKDOSA, YTDOSA)},
        "kabel": KABEL, "kabel_d": KABEL_D, "avstand_nock": AVSTAND_NOCK,
        "varnare": {v.id: {"rum": v.rum, "plan": v.plan, "punkt": list(v.lage.punkt), "normal": list(v.lage.normal),
                           "over_golv": v.lage.punkt[2] - PLAN[v.plan], "takfall": v.takfall}
                    for v in b.varnare.values()},
        "dosor": {d.id: {"namn": d.namn, "punkt": list(d.lage.punkt)} for d in b.dosor.values()},
        "kablar": {r.id: {"fran": r.fran, "till": r.till, "vag": [list(p) for p in r.vag], "langd": langd(r.vag),
                       "bojar": bojar(r.vag)} for r in b.kablar.values()},
        "genomforingar": [{"del": g.del_, "atgard": g.atgard, "punkt": list(g.punkt), "matt": g.matt,
                           "element": g.element} for g in genomforingarna()[0]],
        "nivaer": {"källarens golv": PLAN[0], "källarens tak": KALLARTAK, "plan 1": PLAN[1]},
    }
