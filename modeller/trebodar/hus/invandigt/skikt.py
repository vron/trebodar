"""De invändiga skiktens uppbyggnad (F-01), gemensam för ytterväggarnas insida, innertaket, innerväggarna och
fönstrens smyg: ångbroms, installationsskikt och skivor, med tjocklekar och avstånd från stommen, och innertakets
underkant (den yttre gipsskivan) som väggarna och kaminen går upp till, med former som går upp till den (för de
inbyggda väggarna: garderoben och kökets inbyggnad).
"""
from __future__ import annotations

from typing import Any

from shapely.geometry import Point, Polygon
from shapely.geometry import box as plan_box

from modellering import Form, Kapad, Material, Union, prisma

from trebodar import skelett as S
from trebodar.hus.rum import BADRUM
from trebodar.hus.tak.takytor import REGIONER
from trebodar.material import ANGBROMS, C24_LAKT, GIPS, KAKEL, OSB, PLYWOOD, TATSKIKT, VATRUMSFARG

FOLIE, LAKT = 0.4, 45.0                        # ångbroms och installationsskikt 45×45
# skivorna på väggarna, från reglarna eller installationsläkten och utåt: OSB och gips, i badrummet plywood, gips,
# tätskikt med fix och kakel (namn, tjocklek, typ, material)
SKIVOR = (("OSB", 12.0, "OS", OSB), ("Gips", 13.0, "GI", GIPS))
SKIVOR_VATRUM = (("Plywood", 15.0, "PW", PLYWOOD), ("Gips", 12.0, "GI", GIPS), ("Tätskikt", 3.0, "TS", TATSKIKT),
                 ("Kakel", 8.0, "KA", KAKEL))
SKIVOR_T = sum(t for _, t, _, _ in SKIVOR)
SKIVOR_VATRUM_T = sum(t for _, t, _, _ in SKIVOR_VATRUM)
# badrummets målade väggar (#105): samma tjocklek, en våtrumsgips till i stället för kaklet och tätskiktet rollat
# under färgen, så att rummets ytor och inredningen ligger kvar
SKIVOR_VATRUM_MALAD = (("Plywood", 15.0, "PW", PLYWOOD), ("Gips", 12.0, "GI", GIPS), ("Våtrumsgips", 8.0, "GV", GIPS),
                       ("Tätskikt och våtrumsfärg", 3.0, "TF", VATRUMSFARG))
assert abs(sum(t for _, t, _, _ in SKIVOR_VATRUM_MALAD) - SKIVOR_VATRUM_T) < 1e-9
SKIVA = 12.5                                   # innertakets gipsskivor
TAK_W = (-S.TAKBALK_H - FOLIE, -S.TAKBALK_H)                 # under takbalkarnas underkant
LAKT_W = (TAK_W[0] - LAKT, TAK_W[0])
GIPS_INRE_W = (LAKT_W[0] - SKIVA, LAKT_W[0])
GIPS_YTTRE_W = (GIPS_INRE_W[0] - SKIVA, GIPS_INRE_W[0])
INSIDA_T = FOLIE + LAKT + SKIVOR_T
INSIDA_VATRUM_T = FOLIE + LAKT + SKIVOR_VATRUM_T


def _med_lage(skikt: tuple[tuple[str, float, str, Material], ...], a: float
              ) -> list[tuple[str, float, float, str, Material]]:
    """Skikten med deras avstånd från stommens insida (namn, a, b, typ, material), det första från a."""
    ut = []
    for namn, t, typ, mat in skikt:
        ut.append((namn, a, a + t, typ, mat))
        a += t
    return ut


# väggarnas skikt med avståndet från stommens insida
GRUND = _med_lage((("Ångbroms", FOLIE, "AB", ANGBROMS), ("Installationsskikt", LAKT, "IL", C24_LAKT)), 0.0)
SKIVLAGER = {"vanligt": _med_lage(SKIVOR, FOLIE + LAKT), "vatrum": _med_lage(SKIVOR_VATRUM, FOLIE + LAKT),
             "vatrum_malat": _med_lage(SKIVOR_VATRUM_MALAD, FOLIE + LAKT)}


def insida_t(kod: str, u: float) -> float:
    """Ytterväggens insida (ångbroms, läkt och skivor) vid u: tjockare i badrummet."""
    pl = S.YTTERVAGGAR[kod].placering()
    x, y, _ = pl.punkt((u, S.T_STOMME + 30.0, 0.0))
    return INSIDA_VATRUM_T if BADRUM.contains(Point(x, y)) else INSIDA_T


def innertak_underkant(t: S.Takfall, x: float) -> float:
    """Innertakets yttre gipsskivas underkant vid x under takfallet t."""
    return t.z_overkant(x) + GIPS_YTTRE_W[0] / S.COS


def innertakets_fall(x: float, y: float) -> S.Takfall | None:
    """Takfallet vars innertak ligger över punkten (i nocken det lägsta), eller None utanför innertaken."""
    fall = [S.TAKFALL[k] for k, rs in REGIONER.items() for r in rs
            if r.y0 - 1e-6 <= y <= r.y1 + 1e-6 and min(r.nedre.x, r.nock.x) - 1e-6 <= x <= max(r.nedre.x, r.nock.x) + 1e-6]
    return min(fall, key=lambda t: t.z_overkant(x)) if fall else None


def innertak_vid(x: float, y: float) -> float:
    """Innertakets underkant (den yttre gipsskivan) i punkten: takfallet vars område innehåller punkten (i nocken
    det lägsta)."""
    t = innertakets_fall(x, y)
    return t.z_overkant(x) + GIPS_YTTRE_W[0] / S.COS if t else S.H_VAGG


HOJD = 6000.0                                  # prismornas höjd före kapningen vid innertaket
Plan3 = tuple[tuple[float, float, float], tuple[float, float, float]]


def takplan(p: Polygon, ned: float = 0.0) -> list[Plan3]:
    """Innertakets plan över ytan p (punkt, normal uppåt), ned mm under det: ett per takfall ytan ligger under."""
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


def kapad_vid_taket(f: Form, p: Polygon, ned: float = 0.0, inv: Any = None) -> Form:
    """Formen f över ytan p kapad vid innertaket (ned mm under det). Under en nock (två takfall som stiger mot
    varandra) ligger delen under båda planen; under en dal (takfall som stiger från varandra, #94) under något av dem.
    inv: placeringens invers, när f är i en dels eget system."""
    plan = takplan(p, ned)
    if inv is not None:
        plan = [(inv.punkt(pkt), inv.riktning(n)) for pkt, n in plan]
    if len(plan) == 2:
        x0 = p.bounds[0] + 1.0
        t = innertakets_fall(x0, p.centroid.y)
        stiger_at_hoger = t is not None and t.z_overkant(x0 + 1.0) > t.z_overkant(x0)
        if t is not None and not stiger_at_hoger:          # dal: den vänstra delen faller mot dalen
            return Union(tuple(Kapad(f, pkt, n) for pkt, n in plan))
    for pkt, n in plan:
        f = Kapad(f, pkt, n)
    return f


def upp_till_taket(p: Polygon, z0: float, ned: float = 0.0) -> Form:
    """Prisma över ytan p från z0 upp till innertaket (ned mm under det)."""
    return kapad_vid_taket(prisma(list(p.exterior.coords)[:-1], HOJD - z0, z0=z0), p, ned)


def under_taket(p: Polygon, ned: float) -> Plan3:
    """Planet ned mm under innertaket över ytan p, med normalen nedåt (för att ta bort det som ligger under)."""
    (pkt, n), *_ = takplan(p, ned)
    return pkt, (-n[0], -n[1], -n[2])


def vid_nocken(p: Polygon) -> list[Polygon]:
    """Ytan p delad vid nockbalkarnas linjer (ett takplan per del)."""
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
