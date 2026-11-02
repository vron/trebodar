"""De invändiga skiktens uppbyggnad (F-01), gemensam för ytterväggarnas insida, innertaket, innerväggarna och
fönstrens smyg: ångbroms, installationsskikt och skivor, med tjocklekar och avstånd från stommen, och innertakets
underkant (den yttre gipsskivan) som väggarna och kaminen går upp till.
"""
from __future__ import annotations

from shapely.geometry import Point

from modellering import Material

from trebodar import skelett as S
from trebodar.hus.rum import BADRUM
from trebodar.hus.tak.takytor import REGIONER
from trebodar.material import ANGBROMS, C24_LAKT, GIPS, KAKEL, OSB, PLYWOOD, TATSKIKT

FOLIE, LAKT = 0.4, 45.0                        # ångbroms och installationsskikt 45×45
# skivorna på väggarna, från reglarna eller installationsläkten och utåt: OSB och gips, i badrummet plywood, gips,
# tätskikt med fix och kakel (namn, tjocklek, typ, material)
SKIVOR = (("OSB", 12.0, "OS", OSB), ("Gips", 13.0, "GI", GIPS))
SKIVOR_VATRUM = (("Plywood", 15.0, "PW", PLYWOOD), ("Gips", 12.0, "GI", GIPS), ("Tätskikt", 3.0, "TS", TATSKIKT),
                 ("Kakel", 8.0, "KA", KAKEL))
SKIVOR_T = sum(t for _, t, _, _ in SKIVOR)
SKIVOR_VATRUM_T = sum(t for _, t, _, _ in SKIVOR_VATRUM)
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
SKIVLAGER = {"vanligt": _med_lage(SKIVOR, FOLIE + LAKT), "vatrum": _med_lage(SKIVOR_VATRUM, FOLIE + LAKT)}


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
