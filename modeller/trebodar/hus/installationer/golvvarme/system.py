"""Golvvärmen ur zonerna (plan1.py, kallare.py): slingorna, tilloppen och fördelarna, matarledningarna från
värmepumpen, kontrollen och utdraget för ritningarna (verktyg/modellering: `./mod golvvarme`).

En krets är ett rör från framledningens fördelare genom tilloppet, slingan och tilloppet tillbaka till returens.
Zonens yta är zonen på golvet (betongen utan väggarna, trapphålet och kaminen), MARGINAL från väggar och kanter,
utan tilloppens stråk, järnen i rörens nivå och det som ska hållas fritt (rör genom betongen, utrustning på golvet).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import cache
from types import ModuleType

from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

from trebodar import skelett as S
from trebodar.hus.armering.armering import jarnen_i_nivan
from trebodar.hus.grund import kallarvaggar as K
from trebodar.hus.invandigt.kallare import GIPS_T
from trebodar.hus.invandigt.kallarens_innervaggar import VAGGAR as INNERVAGGAR
from trebodar.hus.rum import KAMINKAPA

from ..genomforingar import Genomforing, Stycke, genomforingar, kallarvaggarna, vaggarna
from ..montering import KALLARTAK, PLAN as GOLV, Vek
from ..strak import filer, vag
from ..el.installation import installation
from ..kollektor.ledningar import D as KB_D
from ..kollektor.ledningar import ledningar as kollektorns
from ..teknikrum import UTRUSTNING, VARMEPUMP
from ..vatten.system import vatten
from . import kallare, plan1
from .katalog import FORDELARE, GOLVVARMEROR, MATARROR
from .punkter import FIL, FRITT, JARN, MARGINAL, Fordelare, Zon, langd, slinga

PLAN: dict[int, ModuleType] = {1: plan1, 0: kallare}
Y_MATARE = {"fram": 6000.0, "retur": 6050.0}       # matarledningarna österut genom hallen och KL3 söder om KD2
SPEL = 5.0                              # rörens fria avstånd till järnen och till varandra


@dataclass
class Krets:
    id: str
    zon: Zon
    plan: int
    yta: Polygon                    # slingans yta
    vag: list[Vek]                  # från framledningens utgång till returens
    slinga: tuple[int, int]         # slingans början och slut i vag (index)
    utgang: dict[str, int]          # utgången på framledningens och returens fördelare

    @property
    def langd(self) -> float:
        return langd(self.vag) / 1000.0


@dataclass
class Golvvarme:
    kretsar: dict[str, Krets]
    fordelare: dict[str, Fordelare]
    matare: dict[str, list[Vek]]
    fel: list[str] = field(default_factory=list)

    def stycken(self) -> list[Stycke]:
        ut = [Stycke(k.id, a, b, GOLVVARMEROR.d, GOLVVARMEROR.d, True, matt=GOLVVARMEROR.matt)
              for k in self.kretsar.values() for a, b in zip(k.vag, k.vag[1:])]
        ut += [Stycke(n, a, b, MATARROR.d, MATARROR.d, True, matt=MATARROR.matt)
               for n, v in self.matare.items() for a, b in zip(v, v[1:])]
        return ut

    def genomforingar(self) -> tuple[list[Genomforing], list[str]]:
        return genomforingar(self.stycken())

    def utdrag(self) -> dict[str, object]:
        """Allt som ritningarna behöver, som JSON: kretsarna (zonen, slingans yta och väg), fördelarna,
        matarledningarna, nivåerna och genomföringarna."""
        return {
            "kretsar": {k.id: {"zon": k.zon.id, "namn": k.zon.namn, "plan": k.plan, "cc": k.zon.cc,
                               "langd": k.langd, "volym": k.langd * GOLVVARMEROR.liter_per_m, "area": k.yta.area / 1e6,
                               "yta": [list(p) for p in k.yta.exterior.coords], "vag": [list(p) for p in k.vag],
                               "slinga": list(k.slinga), "utgang": k.utgang} for k in self.kretsar.values()},
            "fordelare": {f.id: {"typ": f.typ.namn, "media": f.media, "plan": int(f.id[2]), "start": list(f.utgang(0)),
                                 "slut": list(f.utgang(f.utgangar + 1)), "utgangar": f.utgangar}
                          for f in self.fordelare.values()},
            "matare": {k: [list(p) for p in v] for k, v in self.matare.items()},
            "ror": {"slingor": GOLVVARMEROR.namn, "matare": MATARROR.namn, "d": GOLVVARMEROR.d, "d_matare": MATARROR.d,
                    "max_langd": GOLVVARMEROR.max_langd},
            "nivaer": {"plan 1:s golv": GOLV[1], "golvvärmen i mellanbjälklaget": plan1.Z, "källarens tak": KALLARTAK,
                       "källarens golv": GOLV[0], "golvvärmen i bottenplattan": kallare.Z},
            "genomforingar": [{"del": x.del_, "atgard": x.atgard, "punkt": list(x.punkt), "matt": x.matt,
                               "element": x.element} for x in self.genomforingar()[0]],
            "jarn": {plan: [[list(c) for c in g.coords] for g, _ in jarnen(plan)] for plan in PLAN}}


@cache
def golvet(plan: int) -> Polygon:
    """Golvet där slingorna kan ligga: plan 1:s mellanbjälklag utan väggarna, trapphålet och kaminen, eller
    bottenplattan utan källarväggarna, källarens innerväggar och trappan."""
    if plan == 1:
        vaggar = unary_union([hel for hel, _, _, _ in vaggarna().values()])
        return Polygon(S.KONTUR).difference(Polygon(S.TRAPPHAL)).difference(KAMINKAPA).difference(vaggar)
    vaggar = unary_union([hel for hel, _ in kallarvaggarna().values()] +
                         [v.stomme().buffer(GIPS_T, join_style="mitre") for v in INNERVAGGAR.values()])
    return K.ytterkontur().difference(vaggar).difference(Polygon(S.TRAPPHAL))


def jarnen(plan: int) -> tuple[tuple[Point | LineString, float], ...]:
    """Järnen som går genom golvvärmens rör i betongen (plan och Ø)."""
    r, z = GOLVVARMEROR.d / 2, PLAN[plan].Z
    return jarnen_i_nivan(z - r, z + r)


@cache
def _hinder(plan: int) -> Polygon:
    """Det som slingorna ska hålla sig ifrån: järnen i rörens nivå, tappvattnets rör upp ur mellanbjälklaget och elens
    rör i det (plan 1), utrustningen på källarens golv och rören upp genom bottenplattan (servisen och köldbärarens
    skyddsrör, källaren)."""
    delar = [g.buffer(JARN) for g, _ in jarnen(plan)]
    if plan == 1:
        v = vatten()
        delar += [Point(a[0], a[1]).buffer(FRITT) for r in v.ror.values() for a, b in zip(v.vag(r), v.vag(r)[1:])
                  if abs(a[0] - b[0]) < 1.0 and abs(a[1] - b[1]) < 1.0 and min(a[2], b[2]) < 0.0 < max(a[2], b[2])]
        el = installation()
        delar += [LineString([a[:2], b[:2]]).buffer(FRITT) for r in el.ror.values()
                  for a, b in zip(el.vag(r), el.vag(r)[1:]) if KALLARTAK < min(a[2], b[2]) and max(a[2], b[2]) < 0.0]
    else:
        delar += [Point(k.vag[0][0], k.vag[0][1]).buffer(FRITT + KB_D / 2) for k in kollektorns().values()]
        for u in UTRUSTNING.values():
            if u.lage.yta != "golv":
                continue
            (x, y, _), (b, d, h) = u.lage.punkt, u.matt
            delar.append(box(x - b / 2, y - d / 2, x + b / 2, y + d / 2).buffer(MARGINAL, join_style="mitre") if h
                         else Point(x, y).buffer(FRITT))
    return unary_union(delar)


def _fordelare(plan: int, mod: ModuleType, filer_: dict[tuple[str, str], int]) -> dict[str, Fordelare]:
    ut = {}
    for media in ("fram", "retur"):
        f = tuple(sorted(n for (_, m), n in filer_.items() if m == media))
        ut[media] = Fordelare(f"FD{plan}-{media}", FORDELARE, media, (mod.X0, mod.Y_FD[media], mod.Z_FD[media]),
                              (1.0, 0.0, 0.0), f)
    return ut


def _vaning(plan: int, mod: ModuleType) -> tuple[dict[str, Krets], dict[str, Fordelare], list[str]]:
    """Kretsarna och fördelarna på en våning: slingorna i zonerna, filerna och tilloppen; zonernas ytor utan
    tilloppen (andra varvet)."""
    golv, hinder = golvet(plan), _hinder(plan)
    band = Polygon()
    fel: list[str] = []
    for _ in range(2):
        slingor = {}
        for z in mod.ZONER:
            yta = z.polygon().intersection(golv).buffer(-MARGINAL, join_style="mitre").difference(hinder).difference(
                band)
            yta = max(getattr(yta, "geoms", [yta]), key=lambda g: g.area) if not yta.is_empty else Polygon()
            s = slinga(yta, z.cc, z.riktning, z.start) if not yta.is_empty else None
            if s is None:
                fel.append(f"{z.id}: ytan rymmer ingen slinga")
                continue
            slingor[z.id] = (yta, s)
        rader: list[tuple[str, str, int | None, dict[str, tuple[float, float]]]] = [
            (z.id, z.strak, None, {"fram": slingor[z.id][1][0][0], "retur": slingor[z.id][1][1][-1]})
            for z in mod.ZONER if z.id in slingor]
        filer_, mitt = filer(rader, mod.strak, (mod.X0, mod.VAGG), (1.0, 0.0), FIL)
        fd = _fordelare(plan, mod, filer_)
        strak = mod.strak(mitt)
        tillopp: dict[str, dict[str, tuple[Vek, ...]]] = {}
        for z in mod.ZONER:
            if z.id not in slingor:
                continue
            tillopp[z.id] = {}
            for m in ("fram", "retur"):
                n = fd[m].filer.index(filer_[(z.id, m)]) + 1
                mal = slingor[z.id][1][0][0] if m == "fram" else slingor[z.id][1][1][-1]
                tillopp[z.id][m] = vag(fd[m].utgang(n), mod.Z, strak[z.strak], (mal,))
        band = unary_union([LineString([p[:2] for p in t[m]]).buffer(GOLVVARMEROR.d / 2 + FIL / 2)
                            for t in tillopp.values() for m in t])
    kretsar = {}
    for z in mod.ZONER:
        if z.id not in slingor:
            continue
        yta, (fram, retur) = slingor[z.id]
        ut = {m: fd[m].utgang(fd[m].filer.index(filer_[(z.id, m)]) + 1) for m in ("fram", "retur")}
        f = [ut["fram"], *tillopp[z.id]["fram"]]
        r = [*reversed(tillopp[z.id]["retur"]), ut["retur"]]
        mitt_ = [(x, y, mod.Z) for x, y in fram[1:]] + [(x, y, mod.Z) for x, y in retur[:-1]]
        kretsar[f"GV{plan}-{z.id}"] = Krets(f"GV{plan}-{z.id}", z, plan, yta, f + mitt_ + r,
                                             (len(f) - 1, len(f) + len(mitt_)),
                                             {m: fd[m].filer.index(filer_[(z.id, m)]) + 1 for m in ("fram", "retur")})
    return kretsar, fd, list(dict.fromkeys(fel))


def _matare(fd: dict[int, dict[str, Fordelare]]) -> dict[str, list[Vek]]:
    """Matarledningarna under källarens tak: värmepumpens fram och retur söderut genom KL10, österut genom hallen och
    KL3 (söder om dörren KD2) och norrut i trapphallen till plan 1:s fördelare (västra änden), och därifrån vidare till
    källarens (östra ändarna); fram och retur i olika höjder, så att de kan gå bredvid och över varandra."""
    vp = VARMEPUMP.anslutningar
    ut = {}
    for m, z, y, anslutning in (("fram", -350.0, Y_MATARE["fram"], "VS-fram"),
                                ("retur", -300.0, Y_MATARE["retur"], "VS-retur")):
        a, e1 = vp[anslutning], fd[1][m].utgang(0)
        ut[f"VS1-{m}"] = [a, (a[0], a[1], z), (a[0], y, z), (e1[0], y, z), (e1[0], e1[1], z), e1]
        b1, b0 = fd[1][m].utgang(fd[1][m].utgangar + 1), fd[0][m].utgang(fd[0][m].utgangar + 1)
        ut[f"VS0-{m}"] = [b1, (b1[0], b1[1], b0[2]), (b0[0], b1[1], b0[2]), b0]
    return ut


@cache
def golvvarme() -> Golvvarme:
    kretsar: dict[str, Krets] = {}
    fd: dict[int, dict[str, Fordelare]] = {}
    fel: list[str] = []
    for plan, mod in PLAN.items():
        k, f, e = _vaning(plan, mod)
        kretsar.update(k)
        fd[plan] = f
        fel += e
    return Golvvarme(kretsar, {f.id: f for d in fd.values() for f in d.values()}, _matare(fd), fel)


def kontroll(g: Golvvarme) -> tuple[list[str], list[str]]:
    """Fel och anmärkningar: zonerna utan slinga, kretsarnas längd, fördelarnas kretsar, rör som går i varandra eller
    i sig själva (i plan, i betongen) och rör mot järnen i sin nivå."""
    fel, anm = list(g.fel) + g.genomforingar()[1], []
    for k in g.kretsar.values():
        if k.langd > GOLVVARMEROR.max_langd:
            fel.append(f"{k.id}: {k.langd:.0f} m (högst {GOLVVARMEROR.max_langd:g} m)")
        elif k.langd < 0.4 * GOLVVARMEROR.max_langd:
            anm.append(f"{k.id}: {k.langd:.0f} m, kort krets (injusteras)")
    for f in g.fordelare.values():
        if f.utgangar > f.typ.kretsar:
            fel.append(f"{f.id}: {f.utgangar} kretsar, fördelaren har {f.typ.kretsar}")
    r = GOLVVARMEROR.d / 2
    for plan in PLAN:
        linjer = {k.id: LineString([p[:2] for p in k.vag if abs(p[2] - PLAN[plan].Z) < 1.0])
                  for k in g.kretsar.values() if k.plan == plan}
        ider = sorted(linjer)
        for i, a in enumerate(ider):
            for b in ider[i + 1:]:
                d = linjer[a].distance(linjer[b])
                if d < 2 * r + SPEL:
                    fel.append(f"{a} och {b} går i varandra ({d:.0f} mm)")
        for k_id, linje in linjer.items():
            if not linje.is_simple:
                fel.append(f"{k_id}: röret går i sig själv")
            for jarn, dj in jarnen(plan):
                if linje.distance(jarn) < r + dj / 2 + SPEL:
                    p = jarn.representative_point()
                    fel.append(f"{k_id}: mot järnet Ø{dj:g} vid ({p.x:.0f}, {p.y:.0f})")
    return list(dict.fromkeys(fel)), anm
