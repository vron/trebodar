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

from trebodar.hus.fonster_och_dorrar.oppningar import OPPNINGAR

from ..montering import I_TAKET, PLAN, Montering, Vek, enhet, flytt, vagg
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
    underkant: float | None = None              # pendlar: armaturens underkant över plan 1:s golv [mm]
    langs: Vek = (1.0, 0.0, 0.0)                # ljuslinjer: profilens riktning i takets plan, från matningens ände
    #                                             (lage är profilens mitt)


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
    i_bjalklag). slag: vad röret har i sig, 230 V (gruppens ledare), den dimrade fasen från en dimmer till
    drivdonen ("230 V dimrad") eller 24 V från ett drivdon till ljuslinjerna (egna rör, skilda från 230 V)."""
    id: str
    typ: Rortyp
    fran: str
    till: str
    via: tuple[Vek, ...] = ()
    slag: str = "230 V"


@dataclass(frozen=True)
class Krets:
    """En 24 V-krets: ett drivdon i drivdonsskåpet (skap, drivdonets nummer där), dimrat av dimmerns kanal (kanal 0 är
    den första) för tändgruppen tand, och ljuslinjerna i rörens ordning från drivdonet."""
    id: str
    skap: str
    drivdon: int
    dimmer: str
    kanal: int
    tand: str
    lampor: tuple[str, ...]


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


def pendeln(p: Lampa) -> tuple[Vek, Vek]:
    """Pendelns sladd: från takkoppens front (takkoppens höjd ut från takytan längs normalen) lodrätt ned till
    armaturens överkant, så att armaturens underkant hamnar på underkant över golvet. Vägglampan (arm): från
    väggplattans front längs väggens normal ut till armens ände, där armaturen hänger."""
    pe = p.typ.pendel
    if pe is None or (p.underkant is None and not pe.arm):
        raise ValueError(f"{p.id}: inte en pendel med underkant")
    m = p.lage
    kopp = flytt(m.punkt, m.normal, pe.takkopp[1])
    if pe.arm:
        return kopp, flytt(kopp, m.normal, pe.arm)
    assert p.underkant is not None
    return kopp, (kopp[0], kopp[1], PLAN[1] + p.underkant + pe.hojd)


def linjen(p: Lampa) -> tuple[Vek, Vek]:
    """Ljuslinjens lysande del: diffusorns yta från matningens ände till den andra (mittlinjen)."""
    t = p.typ
    assert t.linje is not None
    m, u = p.lage, enhet(p.langs)
    yta = flytt(m.punkt, m.normal, t.linje.hojd - t.linje.diffusor[2])
    return flytt(yta, u, -t.lysande_langd / 2), flytt(yta, u, t.lysande_langd / 2)


def rorande(p: Lampa, ut: bool = False) -> Vek:
    """Ljuslinjens rörände i taket (rörets mitt i takytan, i fickan i profilens ände): i matningens ände, eller (ut)
    i den andra, där röret till nästa ljuslinje går (genomgående ledare i profilen)."""
    t = p.typ
    assert t.linje is not None
    s = t.langd / 2 - t.linje.ror_in
    return flytt(p.lage.punkt, enhet(p.langs), s if ut else -s)


def linsen(p: Lampa) -> Vek:
    """Mitten på armaturens lysande yta, där ljuset kommer ut: infällda på armaturens axel, LINS_INDRAG in från
    takytan; tubspotar huvud.indrag in från tubens front; pendlar ljuskällans mitt; ljuslinjer diffusorns mitt."""
    if p.typ.linje is not None:
        a, b = linjen(p)
        return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2)
    if p.typ.pendel is not None:
        topp = pendeln(p)[1]
        return (topp[0], topp[1], topp[2] - p.typ.pendel.kalla)
    if p.typ.huvud is not None:
        return flytt(tuben(p)[2], enhet(p.riktning), -p.typ.huvud.indrag)
    if p.typ.panel is not None:                     # utanpåliggande panel: dess undersida
        return flytt(p.lage.punkt, p.lage.normal, p.typ.panel[2])
    return flytt(p.lage.punkt, p.lage.normal, -LINS_INDRAG)


def mot(m: Montering, mal: tuple[float, float, float]) -> Vek:
    """Ljusets riktning från monteringen mot en punkt (riktade spotar)."""
    return enhet((mal[0] - m.punkt[0], mal[1] - m.punkt[1], mal[2] - m.punkt[2]))


def lutad(mot_xy: tuple[float, float], vinkel: float) -> Vek:
    """Ljusets riktning lodrätt ned, lutad vinkel grader mot riktningen mot_xy i planet (mot en vägg)."""
    lg = math.hypot(*mot_xy)
    s, c = math.sin(math.radians(vinkel)), math.cos(math.radians(vinkel))
    return (mot_xy[0] / lg * s, mot_xy[1] / lg * s, -c)


OVAN_OPPNINGEN = 200.0         # uttag ovanför fönster: mitten så högt över öppningens överkant


def ovan_fonstret(kod: str, u: float) -> Montering:
    """På ytterväggens insida ovanför fönstret eller dörren närmast u (längs väggen): vid u om u ligger inom
    öppningen, annars 100 mm in från dess närmaste ände, OVAN_OPPNINGEN över öppningens överkant."""
    o = min(OPPNINGAR[kod], key=lambda o: 0.0 if o.u0 <= u <= o.u1 else min(abs(u - o.u0), abs(u - o.u1)))
    if not o.u0 <= u <= o.u1:
        u = o.u0 + 100.0 if abs(u - o.u0) < abs(u - o.u1) else o.u1 - 100.0
    return vagg(kod, u, o.z1 + OVAN_OPPNINGEN)


DRIVDON_AVSTAND = 30.0         # drivdonet på gipsen bredvid armaturens hus, längs y (mellan läkten)


def drivdonet(p: Lampa) -> float:
    """Drivdonets mitt från armaturens mitt längs y."""
    return p.typ.ring_d / 2 + DRIVDON_AVSTAND + (p.typ.drivdon[0] / 2 if p.typ.drivdon else 0.0)


def anslutning(p: Punkt, ut: bool = False) -> Vek:
    """Där rören ansluter till punkten: drivdonet i installationsskiktet vid armaturen, dosans mitt; ljuslinjerna
    rörändan i taket i matningens ände (ut: i den andra, mot nästa ljuslinje)."""
    m = p.lage
    if isinstance(p, Lampa):
        if p.typ.linje is not None:
            return rorande(p, ut)
        if p.typ.dosa is not None:                  # utanpåliggande på betong: i den ingjutna dosan ovanför
            return flytt(m.punkt, m.normal, -p.typ.dosa.djup / 2)
        return flytt(m.punkt, m.normal, -I_TAKET)
    dosa = p.typ.dosa if isinstance(p, Apparat) else p.typ
    return flytt(m.punkt, m.normal, -dosa.djup / 2)
