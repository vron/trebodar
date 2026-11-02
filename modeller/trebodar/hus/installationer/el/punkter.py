"""Elinstallationens beståndsdelar och hur de placeras.

Punkter: armaturer (Lampa), apparater (Apparat: brytare, dimrar, uttag) och dosor (Dosa), var och en med ett id, en
typ ur katalogen och en montering på en byggnadsyta: innertaket, en väggs färdiga yta eller betongbjälklagets
undersida. Monteringen räknas fram ur husets geometri (innertakets fall, väggarnas lägen och skikt), så att punkterna
följer med när huset ändras.

Funktion: tändgrupper (Tandgrupp) är lampor som tänds tillsammans; varje lampa hör till en tändgrupp, och brytare och
dimrar anger vilka tändgrupper de styr.

Förläggning: rör (Ror) från en punkt till en annan, med brytpunkter i innertakets installationsskikt, i väggar och i
bjälklagen (i_tak, i_vagg, vid_tak, i_bjalklag); rörets ändar är punkternas anslutningar (drivdonet vid armaturen,
dosans mitt).

Koordinater i mm (K-05): x, y i planet, z från mellanbjälklagets överkant (plan 1:s golv).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from trebodar import skelett as S
from trebodar.hus.invandigt.skikt import FOLIE, LAKT, SKIVA, innertak_vid, innertakets_fall, insida_t
from trebodar.hus.invandigt.vaggar import skiktets_tjocklek, vaggdef

from .typer import Apparattyp, Armaturtyp, Dosatyp, Rortyp

Vek = tuple[float, float, float]

TAKSKIVOR = 2 * SKIVA                          # innertakets gips (2 × 12,5)
I_TAKET = TAKSKIVOR + LAKT / 2                 # installationsskiktets mitt ovanför takytan
PLAN = {1: 0.0, 0: S.Z_BOTTENPLATTA}           # golvets z: plan 1 och källaren
KALLARTAK = -S.H_BJALKLAG                      # källarens tak: mellanbjälklagets underkant
BJALKLAG = {"MB": -S.H_BJALKLAG / 2}           # bjälklagens mitt, där rören gjuts in


@dataclass(frozen=True)
class Rum:
    kod: str                    # två bokstäver, början på punkternas id (t.ex. "AL")
    namn: str
    plan: int                   # 1 (plan 1) eller 0 (källaren)


@dataclass(frozen=True)
class Montering:
    """Var en punkt sitter: på ytan (takets eller väggens färdiga yta), normalen ut ur ytan in i rummet, ytans slag
    ("tak", "vagg") och vilket takfall, vilken vägg eller vilket bjälklag."""
    punkt: Vek
    normal: Vek
    yta: str
    ref: str


@dataclass(frozen=True)
class Tandgrupp:
    id: str
    namn: str
    dimbar: bool = True


@dataclass(frozen=True)
class Lampa:
    id: str
    typ: Armaturtyp
    lage: Montering
    tand: str                   # tändgruppen
    riktning: Vek = (0.0, 0.0, -1.0)            # ljusets riktning (vridbara armaturer), standard lodrätt ned


@dataclass(frozen=True)
class Apparat:
    id: str
    typ: Apparattyp
    lage: Montering
    styr: tuple[str, ...] = ()  # tändgrupperna som brytaren eller dimmern styr, en per kanal


@dataclass(frozen=True)
class Dosa:
    id: str
    typ: Dosatyp
    lage: Montering


Punkt = Lampa | Apparat | Dosa


@dataclass(frozen=True)
class Ror:
    """Rör från punkten fran till punkten till genom brytpunkterna via (i_tak, i_vagg, vid_tak, i_bjalklag)."""
    id: str
    typ: Rortyp
    fran: str
    till: str
    via: tuple[Vek, ...] = ()


def _vek(a: tuple[float, ...]) -> Vek:
    return (float(a[0]), float(a[1]), float(a[2]))


def _flytt(p: Vek, n: Vek, d: float) -> Vek:
    return (p[0] + n[0] * d, p[1] + n[1] * d, p[2] + n[2] * d)


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
    return Montering(_vek(p), (s * wx, s * wy, 0.0), "vagg", kod)


# ------------------------------------------------------------------ rörens brytpunkter

def i_tak(x: float, y: float) -> Vek:
    """I innertakets installationsskikt (mitt i läkten) över punkten (x, y) i taket."""
    m = tak(x, y)
    return _flytt(m.punkt, m.normal, -I_TAKET)


def i_vagg(kod: str, u: float, z: float, plan: int = 1) -> Vek:
    """I väggen vid u och z över golvet: i regelfacket (innerväggar) eller i ytterväggens installationsskikt."""
    v = S.YTTERVAGGAR[kod] if kod in S.YTTERVAGGAR else vaggdef(kod)
    w = S.T_STOMME + FOLIE + LAKT / 2 if kod in S.YTTERVAGGAR else v.tjocklek / 2
    return _vek((v.origo[0] + v.u[0] * u + v.w[0] * w, v.origo[1] + v.u[1] * u + v.w[1] * w, PLAN[plan] + z))


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


LINS_INDRAG = 8.0              # vridbara armaturers lins: så långt in från takytan (vridningens centrum)


def linsen(p: Lampa) -> Vek:
    """Mitten på armaturens lins, där ljuset kommer ut: på armaturens axel, LINS_INDRAG in från takytan."""
    return _flytt(p.lage.punkt, p.lage.normal, -LINS_INDRAG)


DRIVDON_AVSTAND = 30.0         # drivdonet på gipsen bredvid armaturens hus, längs y (mellan läkten)


def drivdonet(p: Lampa) -> float:
    """Drivdonets mitt från armaturens mitt längs y."""
    return p.typ.ring_d / 2 + DRIVDON_AVSTAND + (p.typ.drivdon[0] / 2 if p.typ.drivdon else 0.0)


def anslutning(p: Punkt) -> Vek:
    """Där rören ansluter till punkten: drivdonet i installationsskiktet vid armaturen, dosans mitt."""
    m = p.lage
    if isinstance(p, Lampa):
        return _flytt(m.punkt, m.normal, -I_TAKET)
    dosa = p.typ.dosa if isinstance(p, Apparat) else p.typ
    return _flytt(m.punkt, m.normal, -dosa.djup / 2)


# ------------------------------------------------------------------ hjälp för rummens listor

def lampor(prefix: str, typ: Armaturtyp, lagen: list[Montering], tand: str, start: int = 1) -> list[Lampa]:
    """Lampor med löpnummer: prefix + två siffror, t.ex. "AL-L01"."""
    return [Lampa(f"{prefix}{start + i:02d}", typ, m, tand) for i, m in enumerate(lagen)]
