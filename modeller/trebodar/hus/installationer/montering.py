"""Lägen på husets ytor för installationerna (el, ventilation, vatten): monteringen på innertaket, väggarnas färdiga
ytor, golven, källarens tak och väggar, ytterväggarnas utsida (fasaden) och takets yta, och punkter i väggarna,
installationsskiktet, under källarens tak och i bjälklaget. Lägena räknas fram ur husets geometri (innertakets fall,
väggarnas lägen och skikt, takets skikt), så att installationerna följer med när huset ändras.

Koordinater i mm (K-05): x, y i planet, z från mellanbjälklagets överkant (plan 1:s golv).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from trebodar import skelett as S
from trebodar.byggdelar import taklager as L
from trebodar.hus.armering.armering import bottenplattans_mellanrum, mellanbjalklagets_mellanrum
from trebodar.hus.grund import kallarvaggar as K
from trebodar.hus.invandigt.kallare import GIPS_T
from trebodar.hus.invandigt.skikt import (FOLIE, LAKT, SKIVA, innertak_vid, innertakets_fall, insidans_yta,
                                         installationsskikt)
from trebodar.hus.invandigt.vaggar import skiktets_tjocklek, vaggdef

Vek = tuple[float, float, float]

TAKSKIVOR = 2 * SKIVA                          # innertakets gips (2 × 12,5)
I_TAKET = TAKSKIVOR + LAKT / 2                 # installationsskiktets mitt ovanför takytan
PLAN = {1: 0.0, 0: S.Z_BOTTENPLATTA}           # golvets z: plan 1 och källaren
KALLARTAK = -S.H_BJALKLAG                      # källarens tak: mellanbjälklagets underkant
# elrörens nivåer i mellanbjälklaget (rörets mitt): de klena (Ø16) mellan golvvärmens rör och överkantsnätet, där de går
# över tappvattnets och golvvärmens rör; de grova (Ø20) i tappvattnets nivå, utan att korsa dess rör
BJALKLAG = {"MB": -51.0, "MB-UK": -100.0}

# installationernas skikt i betongen, mellan armeringsnäten (R-06, R-04): i mellanbjälklaget tappvattnets rör-i-rör
# (Ø28) närmast underkantsnätet och golvvärmens rör (Ø16) ovanför dem, under järnen under överkantsnätet; i
# bottenplattan golvvärmens rör mitt emellan näten
_MB, _BP = mellanbjalklagets_mellanrum(), bottenplattans_mellanrum()
I_BETONGEN = {"vatten": _MB[0] + 2.0 + 14.0, "golvvarme": _MB[0] + 2.0 + 28.0 + 4.0 + 8.0,
              "golvvarme_bottenplattan": (_BP[0] + _BP[1]) / 2}


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


def golv(x: float, y: float, plan: int = 1) -> Montering:
    """På golvet: plan 1:s betonggolv (mellanbjälklagets överkant) eller källarens (bottenplattans överkant)."""
    return Montering((float(x), float(y), PLAN[plan]), (0.0, 0.0, 1.0), "golv", "MB" if plan == 1 else "BP")


def kallarvagg(namn: str, s: float, z: float, sida: int) -> Montering:
    """På en källarväggs yta (gipsen) vid s längs väggen (x för väggar längs x, y för väggar längs y) och z över
    källarens golv; sida +1 eller −1: väggens sida mot växande y (längs x) eller växande x (längs y)."""
    v = next(w for w in K.VAGGAR if w.namn == namn)
    t = K.KARNA / 2 + K.CELL + GIPS_T
    c = v.c + sida * t
    p = (s, c) if v.riktning == "h" else (c, s)
    n = (0.0, float(sida)) if v.riktning == "h" else (float(sida), 0.0)
    return Montering((float(p[0]), float(p[1]), PLAN[0] + z), (n[0], n[1], 0.0), "vagg", namn)


def _ytan(kod: str, u: float, sida: int) -> tuple[float, float, float]:
    """Väggens färdiga yta vid u: (w, och väggens riktning w som x, y), för ytterväggar insidan."""
    if kod in S.YTTERVAGGAR:
        v = S.YTTERVAGGAR[kod]
        return insidans_yta(kod, u), v.w[0], v.w[1]
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


def langs_vaggen(kod: str, p: Vek) -> float:
    """Punktens läge u längs väggen (från väggens origo), som vagg och i_vagg tar."""
    v = S.YTTERVAGGAR[kod] if kod in S.YTTERVAGGAR else vaggdef(kod)
    return (p[0] - v.origo[0]) * v.u[0] + (p[1] - v.origo[1]) * v.u[1]


def i_vagg(kod: str, u: float, z: float, plan: int = 1) -> Vek:
    """I väggen vid u och z över golvet: i regelfacket (innerväggar) eller i ytterväggens installationsskikt."""
    v = S.YTTERVAGGAR[kod] if kod in S.YTTERVAGGAR else vaggdef(kod)
    assert kod not in S.YTTERVAGGAR or installationsskikt(kod), f"{kod} har inget installationsskikt (#110)"
    w = S.T_STOMME + FOLIE + LAKT / 2 if kod in S.YTTERVAGGAR else v.tjocklek / 2
    return vek((v.origo[0] + v.u[0] * u + v.w[0] * w, v.origo[1] + v.u[1] * u + v.w[1] * w, PLAN[plan] + z))


def i_vaggen(m: Montering, p: Vek) -> Vek:
    """Punkten inne i väggen bakom punkten p på väggens yta (montering m), i p:s höjd, där rör går lodrätt: i plan 1:s
    väggar som i_vagg, i källarväggarna mitt i cellplasten bakom gipsen."""
    v = next((w for w in K.VAGGAR if w.namn == m.ref), None)
    if v is None:
        return i_vagg(m.ref, langs_vaggen(m.ref, p), p[2] - PLAN[1])
    c = v.c + math.copysign(K.KARNA / 2 + K.CELL / 2, m.normal[1] if v.riktning == "h" else m.normal[0])
    return (p[0], c, p[2]) if v.riktning == "h" else (c, p[1], p[2])


def vid_tak(kod: str, u: float, sida: int = 1) -> tuple[Vek, Vek]:
    """Där ett rör går från väggen upp i innertaket på väggens sida: i väggen i innertakets höjd och i
    installationsskiktet 100 mm ut från väggen."""
    m = vagg(kod, u, 0.0, sida)
    x, y = m.punkt[0] + 100.0 * m.normal[0], m.punkt[1] + 100.0 * m.normal[1]
    i = i_tak(x, y)
    return i_vagg(kod, u, i[2]), i


def _fallet(x: float, y: float) -> str | None:
    t = innertakets_fall(x, y)
    return None if t is None else t.kod


def langs_taket(a: Vek, b: Vek, steg: float = 250.0) -> list[Vek]:
    """Sträckan a–b genom innertakets installationsskikt, med en brytpunkt där innertaket byter fall (nocken, en dal),
    så att röret följer skiktet i stället för att skära genom rummet; rak om inte båda punkterna ligger i skiktet.
    Fallen letas upp med steg mellan punkterna och gränsen mellan dem på 1 mm när."""
    fa, fb = _fallet(a[0], a[1]), _fallet(b[0], b[1])
    halv = LAKT / 2 / math.cos(math.radians(S.TAKVINKEL))       # skiktets halva tjocklek, lodrätt
    if fa is None or fb is None or abs(i_tak(a[0], a[1])[2] - a[2]) > halv or abs(i_tak(b[0], b[1])[2] - b[2]) > halv:
        return [a, b]
    n = max(1, math.ceil(math.hypot(b[0] - a[0], b[1] - a[1]) / steg))
    ut = [a]
    s0, f0 = 0.0, fa
    for k in range(1, n + 1):
        s1 = k / n
        f1 = _fallet(a[0] + (b[0] - a[0]) * s1, a[1] + (b[1] - a[1]) * s1)
        if f1 is None:
            return [a, b]
        if f1 != f0:
            lo, hi = s0, s1
            while (hi - lo) * math.hypot(b[0] - a[0], b[1] - a[1]) > 1.0:
                mid = (lo + hi) / 2
                if _fallet(a[0] + (b[0] - a[0]) * mid, a[1] + (b[1] - a[1]) * mid) == f0:
                    lo = mid
                else:
                    hi = mid
            ut.append(i_tak(a[0] + (b[0] - a[0]) * lo, a[1] + (b[1] - a[1]) * lo))
        s0, f0 = s1, f1
    return [*ut, b]


def i_bjalklag(x: float, y: float, bjalklag: str = "MB") -> Vek:
    """Ingjutet i bjälklaget, i elrörens nivå (BJALKLAG)."""
    return (float(x), float(y), BJALKLAG[bjalklag])


def under_kallartak(x: float, y: float, d: float) -> Vek:
    """d under källarens tak (mellanbjälklagets undersida), t.ex. en kanals mitt."""
    return (float(x), float(y), KALLARTAK - d)
