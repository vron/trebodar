"""Elinstallationens beståndsdelar och hur de placeras.

Punkter: armaturer (Lampa), apparater (Apparat: brytare, dimrar, uttag) och dosor (Dosa), var och en med ett id, en
typ ur katalogen och en montering på en byggnadsyta: innertaket, en väggs färdiga yta eller betongbjälklagets
undersida (installationernas gemensamma montering.py: tak, vagg, kallartak). Monteringen räknas fram ur husets
geometri, så att punkterna följer med när huset ändras.

Funktion: tändgrupper (Tandgrupp) är lampor som tänds tillsammans; varje lampa hör till en tändgrupp, och brytare och
dimrar anger vilka tändgrupper de styr.

Förläggning: rör (Ror) från en punkt till en annan, med brytpunkter i innertakets installationsskikt, i väggar och i
bjälklagen (montering.py: i_tak, i_vagg, vid_tak, i_bjalklag); rörets ändar är punkternas anslutningar (drivdonet vid
armaturen, dosans mitt).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from ..montering import I_TAKET, Montering, Vek, enhet, flytt
from .typer import Apparattyp, Armaturtyp, Dosatyp, Rortyp


@dataclass(frozen=True)
class Rum:
    kod: str                    # två bokstäver, början på punkternas id (t.ex. "AL")
    namn: str
    plan: int                   # 1 (plan 1) eller 0 (källaren)


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
    """Rör från punkten fran till punkten till genom brytpunkterna via (montering: i_tak, i_vagg, vid_tak,
    i_bjalklag)."""
    id: str
    typ: Rortyp
    fran: str
    till: str
    via: tuple[Vek, ...] = ()


LINS_INDRAG = 8.0              # vridbara armaturers lins: så långt in från takytan (vridningens centrum)
PLATTA_T = 2.0                 # frontplattans och frontringens tjocklek


def tuben(p: Lampa) -> tuple[Vek, Vek, Vek]:
    """Tubspotens läge: leden (stammens ände), tubens bakre och främre ände (mittpunkterna). Stammen går från
    frontplattan längs takets normal; leden sitter på tubens sida huvud.led från den bakre änden, och tubens axel
    går i ljusets riktning, en radie från leden bort från stammen."""
    h = p.typ.huvud
    assert h is not None
    n, d = p.lage.normal, enhet(p.riktning)
    led = flytt(p.lage.punkt, n, PLATTA_T + h.stam)
    # från leden in mot tubens axel: stammens riktning vinkelrätt mot axeln (rakt ned: tubens sida åt takets x)
    k = sum(a * b for a, b in zip(n, d))
    u = (n[0] - k * d[0], n[1] - k * d[1], n[2] - k * d[2])
    if math.sqrt(sum(a * a for a in u)) < 1e-6:
        u = (0.0, 1.0, 0.0)
    u = enhet(u)
    axel = flytt(led, u, h.diameter / 2)
    return led, flytt(axel, d, -h.led), flytt(axel, d, h.langd - h.led)


def linsen(p: Lampa) -> Vek:
    """Mitten på armaturens lysande yta, där ljuset kommer ut: infällda på armaturens axel, LINS_INDRAG in från
    takytan; tubspotar huvud.indrag in från tubens front."""
    if p.typ.huvud is not None:
        return flytt(tuben(p)[2], enhet(p.riktning), -p.typ.huvud.indrag)
    return flytt(p.lage.punkt, p.lage.normal, -LINS_INDRAG)


def mot(m: Montering, mal: tuple[float, float, float]) -> Vek:
    """Ljusets riktning från monteringen mot en punkt (riktade spotar)."""
    return enhet((mal[0] - m.punkt[0], mal[1] - m.punkt[1], mal[2] - m.punkt[2]))


DRIVDON_AVSTAND = 30.0         # drivdonet på gipsen bredvid armaturens hus, längs y (mellan läkten)


def drivdonet(p: Lampa) -> float:
    """Drivdonets mitt från armaturens mitt längs y."""
    return p.typ.ring_d / 2 + DRIVDON_AVSTAND + (p.typ.drivdon[0] / 2 if p.typ.drivdon else 0.0)


def anslutning(p: Punkt) -> Vek:
    """Där rören ansluter till punkten: drivdonet i installationsskiktet vid armaturen, dosans mitt."""
    m = p.lage
    if isinstance(p, Lampa):
        return flytt(m.punkt, m.normal, -I_TAKET)
    dosa = p.typ.dosa if isinstance(p, Apparat) else p.typ
    return flytt(m.punkt, m.normal, -dosa.djup / 2)


# ------------------------------------------------------------------ hjälp för rummens listor

def lampor(prefix: str, typ: Armaturtyp, lagen: list[Montering], tand: str, start: int = 1) -> list[Lampa]:
    """Lampor med löpnummer: prefix + två siffror, t.ex. "AL-L01"."""
    return [Lampa(f"{prefix}{start + i:02d}", typ, m, tand) for i, m in enumerate(lagen)]
