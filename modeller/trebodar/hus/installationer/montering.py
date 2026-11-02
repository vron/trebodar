"""Lägen på husets ytor för installationerna (el och ventilation): monteringen på innertaket, väggarnas färdiga ytor,
källarens tak, ytterväggarnas utsida (fasaden) och takets yta, och punkter i väggarna, installationsskiktet, under
källarens tak och i bjälklaget. Lägena räknas fram ur husets geometri (innertakets fall, väggarnas lägen och skikt,
takets skikt), så att installationerna följer med när huset ändras.

Koordinater i mm (K-05): x, y i planet, z från mellanbjälklagets överkant (plan 1:s golv).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from trebodar import skelett as S
from trebodar.byggdelar import taklager as L
from trebodar.hus.invandigt.skikt import FOLIE, LAKT, SKIVA, innertak_vid, innertakets_fall, insida_t
from trebodar.hus.invandigt.vaggar import skiktets_tjocklek, vaggdef

Vek = tuple[float, float, float]

TAKSKIVOR = 2 * SKIVA                          # innertakets gips (2 × 12,5)
I_TAKET = TAKSKIVOR + LAKT / 2                 # installationsskiktets mitt ovanför takytan
PLAN = {1: 0.0, 0: S.Z_BOTTENPLATTA}           # golvets z: plan 1 och källaren
KALLARTAK = -S.H_BJALKLAG                      # källarens tak: mellanbjälklagets underkant
BJALKLAG = {"MB": -S.H_BJALKLAG / 2}           # bjälklagens mitt, där rören gjuts in


@dataclass(frozen=True)
class Montering:
    """Var en punkt sitter: på ytan (takets eller väggens färdiga yta, fasaden, takets yta), normalen ut ur ytan (in
    i rummet, eller ut från huset), ytans slag ("tak", "vagg", "fasad", "yttertak") och vilket takfall, vilken vägg
    eller vilket bjälklag."""
    punkt: Vek
    normal: Vek
    yta: str
    ref: str


def vek(a: tuple[float, ...]) -> Vek:
    return (float(a[0]), float(a[1]), float(a[2]))


def flytt(p: Vek, n: Vek, d: float) -> Vek:
    """Punkten p flyttad d längs n."""
    return (p[0] + n[0] * d, p[1] + n[1] * d, p[2] + n[2] * d)


def enhet(v: Vek) -> Vek:
    n = math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)
    return (v[0] / n, v[1] / n, v[2] / n)


# ------------------------------------------------------------------ montering på ytorna

def tak(x: float, y: float) -> Montering:
    """I innertaket på plan 1: på den yttre gipsskivans underkant, normalen vinkelrätt mot takfallet ned i rummet."""
    t = innertakets_fall(x, y)
    if t is None:
        raise ValueError(f"inget innertak i ({x:g}, {y:g})")
    v = math.radians(S.TAKVINKEL)
    return Montering((float(x), float(y), innertak_vid(x, y)), (t.riktning * math.sin(v), 0.0, -math.cos(v)), "tak",
                     t.kod)


def kallartak(x: float, y: float) -> Montering:
    """I källarens tak: mellanbjälklagets undersida (betong)."""
    return Montering((float(x), float(y), KALLARTAK), (0.0, 0.0, -1.0), "tak", "MB")


def _ytan(kod: str, u: float, sida: int) -> tuple[float, float, float]:
    """Väggens färdiga yta vid u: (w, och väggens riktning w som x, y), för ytterväggar insidan."""
    if kod in S.YTTERVAGGAR:
        v = S.YTTERVAGGAR[kod]
        return S.T_STOMME + insida_t(kod, u), v.w[0], v.w[1]
    v = vaggdef(kod)
    w = v.tjocklek + skiktets_tjocklek(kod, 1, u) if sida > 0 else -skiktets_tjocklek(kod, -1, u)
    return w, v.w[0], v.w[1]


def vagg(kod: str, u: float, z: float, sida: int = 1, plan: int = 1) -> Montering:
    """På väggens färdiga yta vid u längs väggen och z över golvet. sida: väggens sida i dess w-riktning (+1 eller
    −1); ytterväggar har insidan åt +w."""
    v = S.YTTERVAGGAR[kod] if kod in S.YTTERVAGGAR else vaggdef(kod)
    w, wx, wy = _ytan(kod, u, sida)
    s = 1 if kod in S.YTTERVAGGAR else sida
    p = (v.origo[0] + v.u[0] * u + wx * w, v.origo[1] + v.u[1] * u + wy * w, PLAN[plan] + z)
    return Montering(vek(p), (s * wx, s * wy, 0.0), "vagg", kod)


def utsida(kod: str, u: float, z: float) -> Montering:
    """På ytterväggens utsida (fasadens yta) vid u längs väggen och z över plan 1:s golv, normalen ut från huset."""
    v = S.YTTERVAGGAR[kod]
    w = -S.T_FASAD
    p = (v.origo[0] + v.u[0] * u + v.w[0] * w, v.origo[1] + v.u[1] * u + v.w[1] * w, float(z))
    return Montering(vek(p), (-v.w[0], -v.w[1], 0.0), "fasad", kod)


def pa_tak(x: float, y: float) -> Montering:
    """På takets yta (plåtens överkant) lodrätt över punkten (x, y), normalen vinkelrätt ut från takfallet."""
    t = innertakets_fall(x, y)
    if t is None:
        raise ValueError(f"inget tak i ({x:g}, {y:g})")
    v = math.radians(S.TAKVINKEL)
    return Montering((float(x), float(y), L.z_skikt(t, x, L.PLAT[1])),
                     (-t.riktning * math.sin(v), 0.0, math.cos(v)), "yttertak", t.kod)


# ------------------------------------------------------------------ punkter i väggar, skikt och bjälklag

def i_tak(x: float, y: float) -> Vek:
    """I innertakets installationsskikt (mitt i läkten) över punkten (x, y) i taket."""
    m = tak(x, y)
    return flytt(m.punkt, m.normal, -I_TAKET)


def angbromsen(x: float, y: float) -> float:
    """Innertakets ångbroms (överkanten, takbalkarnas underkant) lodrätt över punkten (x, y) [z]."""
    t = innertakets_fall(x, y)
    if t is None:
        raise ValueError(f"inget innertak i ({x:g}, {y:g})")
    return t.z_overkant(x) - S.TAKBALK_HV


def i_vagg(kod: str, u: float, z: float, plan: int = 1) -> Vek:
    """I väggen vid u och z över golvet: i regelfacket (innerväggar) eller i ytterväggens installationsskikt."""
    v = S.YTTERVAGGAR[kod] if kod in S.YTTERVAGGAR else vaggdef(kod)
    w = S.T_STOMME + FOLIE + LAKT / 2 if kod in S.YTTERVAGGAR else v.tjocklek / 2
    return vek((v.origo[0] + v.u[0] * u + v.w[0] * w, v.origo[1] + v.u[1] * u + v.w[1] * w, PLAN[plan] + z))


def vid_tak(kod: str, u: float, sida: int = 1) -> tuple[Vek, Vek]:
    """Där ett rör går från väggen upp i innertaket på väggens sida: i väggen i innertakets höjd och i
    installationsskiktet 100 mm ut från väggen."""
    m = vagg(kod, u, 0.0, sida)
    x, y = m.punkt[0] + 100.0 * m.normal[0], m.punkt[1] + 100.0 * m.normal[1]
    i = i_tak(x, y)
    return i_vagg(kod, u, i[2]), i


def i_bjalklag(x: float, y: float, bjalklag: str = "MB") -> Vek:
    """Ingjutet i bjälklaget (mitt i betongen)."""
    return (float(x), float(y), BJALKLAG[bjalklag])


def under_kallartak(x: float, y: float, d: float) -> Vek:
    """d under källarens tak (mellanbjälklagets undersida), t.ex. en kanals mitt."""
    return (float(x), float(y), KALLARTAK - d)
