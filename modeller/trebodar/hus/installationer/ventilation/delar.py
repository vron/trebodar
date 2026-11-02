"""Ventilationens beståndsdelar och hur de placeras.

En gren (Gren) är en frånluft med egen fläkt: en kedja av element i luftens riktning, från donet där luften tas ut
ur rummet till avluftsdonet där den lämnar huset:

- don (Don): frånluftsdon, köksfläkt eller väggfläkt, monterat på en yta (montering.py: vagg, fri);
- kanaler (Kanal) med brytpunkter (via): från elementet före till elementet efter; följer två kanaler på varandra
  är den förstas sista brytpunkt den andras början;
- kanalfläktar (Flakt) och övergångar mellan kanaltyper (Overgang), med läge och luftens riktning;
- avluftsdon (Avluft): galler på fasaden (montering.utsida) eller huv på taket (montering.pa_tak).

Elementens id börjar med grenens (t.ex. "FF3-K2"): D don, K kanal, FL fläkt, O övergång, A avluftsdon.
Koordinater i mm (K-05), z från plan 1:s golv; flöden i l/s.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..montering import Montering, Vek, flytt
from .typer import Avluftstyp, Dontyp, Kanalflakttyp, Kanaltyp, Koksflakttyp, Overgangstyp, Vaggflakttyp


@dataclass(frozen=True)
class Don:
    """Donet där luften tas ut: frånluftsdonets front, köksfläktens kåpa (väggens yta i kåpans underkant, mitt för
    kåpan) eller väggfläktens front (väggens yta), normalen in i rummet."""
    id: str
    typ: Dontyp | Koksflakttyp | Vaggflakttyp
    lage: Montering


@dataclass(frozen=True)
class Flakt:
    id: str
    typ: Kanalflakttyp
    lage: Vek                   # fläktens mitt
    riktning: Vek               # luftens riktning


@dataclass(frozen=True)
class Overgang:
    id: str
    typ: Overgangstyp
    lage: Vek                   # övergångens mitt
    riktning: Vek               # luftens riktning
    bredd_langs: Vek = (1.0, 0.0, 0.0)          # den platta sidans bredd längs denna riktning


@dataclass(frozen=True)
class Avluft:
    """Avluftsdonet på fasaden eller taket, normalen ut från huset."""
    id: str
    typ: Avluftstyp
    lage: Montering


@dataclass(frozen=True)
class Kanal:
    id: str
    typ: Kanaltyp
    via: tuple[Vek, ...] = ()
    bredd_langs: Vek = (1.0, 0.0, 0.0)          # platta kanaler: bredden längs denna riktning


Element = Don | Flakt | Overgang | Avluft | Kanal


@dataclass(frozen=True)
class Gren:
    """En frånluft med egen fläkt: kedjan av element i luftens riktning, rummet, flödena och en beskrivning av vägen
    (anvisningar på ritningarna)."""
    id: str
    namn: str
    rum: str
    flode: float                # dimensionerande (forcerat) flöde [l/s]
    kedja: tuple[Element, ...]
    flode_normal: float = 0.0   # grundflöde [l/s]
    beskrivning: tuple[str, ...] = ()


def fri(p: Vek, normal: Vek, ref: str = "") -> Montering:
    """Fritt läge (t.ex. ett don på en kanal under källarens tak), normalen in i rummet."""
    return Montering(p, normal, "fri", ref)


def inlopp(e: Element) -> Vek:
    """Där luften kommer in i elementet (kanalen före slutar här)."""
    if isinstance(e, (Flakt, Overgang)):
        langd = e.typ.langd
        return flytt(e.lage, e.riktning, -langd / 2)
    if isinstance(e, Avluft):
        return e.lage.punkt
    raise ValueError(f"{e.id}: luften kommer inte in i ett don eller en kanal här")


def utlopp(e: Element) -> Vek:
    """Där luften lämnar elementet (kanalen efter börjar här): frånluftsdonets anslutning bakom fronten, köksfläktens
    utlopp i kåpans överkant, väggfläktens rör vid väggens yta, fläktens och övergångens utlopp."""
    if isinstance(e, Don):
        m, t = e.lage, e.typ
        if isinstance(t, Koksflakttyp):
            return flytt(flytt(m.punkt, m.normal, t.utlopp), (0.0, 0.0, 1.0), t.h)
        if isinstance(t, Dontyp):
            return flytt(m.punkt, m.normal, -t.djup)
        return m.punkt
    if isinstance(e, (Flakt, Overgang)):
        return flytt(e.lage, e.riktning, e.typ.langd / 2)
    raise ValueError(f"{e.id}: luften lämnar inte ett avluftsdon eller en kanal här")


def kanalernas_vagar(g: Gren) -> dict[str, list[Vek]]:
    """Varje kanals väg i grenen: från elementet före (eller den förra kanalens slut) genom brytpunkterna till
    elementet efter."""
    vagar: dict[str, list[Vek]] = {}
    p: Vek | None = None
    for i, e in enumerate(g.kedja):
        if isinstance(e, Kanal):
            if p is None:
                raise ValueError(f"{g.id}: kanalen {e.id} har inget element före")
            vag = [p, *e.via]
            nasta = g.kedja[i + 1] if i + 1 < len(g.kedja) else None
            if nasta is not None and not isinstance(nasta, Kanal):
                vag.append(inlopp(nasta))
            vagar[e.id] = vag
            p = vag[-1]
        elif not isinstance(e, Avluft):
            p = utlopp(e)
    return vagar
