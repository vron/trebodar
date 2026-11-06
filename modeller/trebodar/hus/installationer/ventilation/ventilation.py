"""Ventilationens geometri: don, kanaler, kanalfläktar, övergångar och avluftsdon ur grenarna (system.py), ett montage
per gren. Delarna kontrolleras inte i modellens krockkontroll (kontrollregler.UTOM_KONTROLL) och tar inga hål i andra
delar; ventilationen har en egen kontroll (`./mod ventilation kontroll`) och redovisar genomföringarna.

Kanalerna är raka bitar längs mittlinjen, i böjarna förlängda så att hörnen fylls; platta kanaler med bredden längs
kanalens bredd_langs. Donen och avluftsdonen i ytans system: origo på ytan, z ut ur ytan, x vågrätt längs ytan och y
uppåt (väggar och fasader). Köksfläktens skorstenskåpa går upp till innertaket och följer dess lutning. Takfläkten
står på en sockel av takplåt, med underkanten i takets yta och en vågrät överkant.
"""
from __future__ import annotations

import math

from modellering import Del, Form, Montage, Placering, box, cylinder, polyeder, prisma

from trebodar import skelett as S
from trebodar.hus.invandigt.skikt import innertak_vid
from trebodar.material import (ALUMINIUM, FETTFILTER, FLAKT, KANALISOLERING, KOKSFLAKT, PLATTKANAL, SPIROKANAL,
                               TAKFLAKT, TAKPLAT, VENTILATIONSDON)

from ..montering import Montering, Vek, flytt
from .delar import Avluft, Don, Flakt, Gren, Kanal, Overgang, kanalernas_vagar
from .system import ventilation
from .typer import Dontyp, Kanaltyp, Koksflakttyp, Vaggflakttyp

N_RUND = 24                     # hörn i övergångarnas runda ände
KAPA_RAM = 15.0                 # den sluttande kåpans ram i underkanten


def _enhet(v: Vek) -> Vek:
    n = math.sqrt(sum(x * x for x in v))
    return (v[0] / n, v[1] / n, v[2] / n)


def _vinkelratt(v: Vek) -> Vek:
    a = (0.0, 0.0, 1.0) if abs(v[2]) < 0.9 else (1.0, 0.0, 0.0)
    return (v[1] * a[2] - v[2] * a[1], v[2] * a[0] - v[0] * a[2], v[0] * a[1] - v[1] * a[0])


def _tvars(bredd_langs: Vek, z: Vek) -> Vek:
    """bredd_langs vinkelrätt mot z (platta kanalers bredd), annars någon riktning vinkelrätt mot z."""
    k = sum(a * b for a, b in zip(bredd_langs, z))
    x = tuple(a - k * b for a, b in zip(bredd_langs, z))
    return _enhet(x) if math.sqrt(sum(c * c for c in x)) > 1e-6 else _vinkelratt(z)  # type: ignore[arg-type]


def _vagg(m: Montering) -> Placering:
    """Väggens eller fasadens system: x vågrätt längs ytan, y uppåt, z ut ur ytan (normalen)."""
    n = m.normal
    return Placering.axlar(m.punkt, (-n[1], n[0], 0.0), n)


def _material(typ: Kanaltyp):  # type: ignore[no-untyped-def]
    return KANALISOLERING if typ.isolering > 0 else PLATTKANAL if typ.form == "platt" else SPIROKANAL


def kanal(namn: str, vag: list[Vek], typ: Kanaltyp, bredd_langs: Vek) -> Montage:
    """Kanalen som raka bitar längs mittlinjen (med isoleringen ytterst), förlängda i böjarna."""
    m = Montage(namn, beskrivning=typ.namn)
    bitar = [(a, b) for a, b in zip(vag, vag[1:]) if math.dist(a, b) > 1.0]
    B, H = typ.yttre
    for i, (a, b) in enumerate(bitar):
        lgd = math.dist(a, b)
        z = _enhet((b[0] - a[0], b[1] - a[1], b[2] - a[2]))
        form: Form
        if typ.form == "rund":
            fore, efter = (B / 2 if i > 0 else 0.0), (B / 2 if i < len(bitar) - 1 else 0.0)
            form = cylinder(B / 2, lgd + fore + efter, (0.0, 0.0, -fore))
            pl = Placering.axlar(a, _vinkelratt(z), z)
        else:
            fore, efter = (H / 2 if i > 0 else 0.0), (H / 2 if i < len(bitar) - 1 else 0.0)
            form = box(-B / 2, B / 2, -H / 2, H / 2, -fore, lgd + efter)
            pl = Placering.axlar(a, _tvars(bredd_langs, z), z)
        m.lagg(Del(f"{typ.namn} L={lgd:.0f}", form, _material(typ)), pl, f"{namn}-{i + 1}")
    return m


def _profil_rund(r: float) -> list[tuple[float, float]]:
    return [(r * math.cos(2 * math.pi * i / N_RUND), r * math.sin(2 * math.pi * i / N_RUND)) for i in range(N_RUND)]


def _profil_platt(b: float, h: float) -> list[tuple[float, float]]:
    """Rektangeln b × h med hörn i samma vinklar som den runda profilen (strålar från mitten)."""
    ut = []
    for i in range(N_RUND):
        v = 2 * math.pi * i / N_RUND
        c, s = math.cos(v), math.sin(v)
        t = min(b / 2 / abs(c) if abs(c) > 1e-9 else 1e9, h / 2 / abs(s) if abs(s) > 1e-9 else 1e9)
        ut.append((t * c, t * s))
    return ut


def _profil(typ: Kanaltyp) -> list[tuple[float, float]]:
    B, H = typ.yttre
    return _profil_rund(B / 2) if typ.form == "rund" else _profil_platt(B, H)


def _stympad_kon(r0: float, r1: float, z0: float, z1: float) -> Form:
    """Stympad kon längs z, radien r0 i z0 och r1 i z1."""
    v = [2 * math.pi * i / N_RUND for i in range(N_RUND)]
    horn = [(r0 * math.cos(a), r0 * math.sin(a), z0) for a in v] + [(r1 * math.cos(a), r1 * math.sin(a), z1) for a in v]
    n = N_RUND
    ytor = [tuple(range(n)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        ytor += [(i, j, n + j), (i, n + j, n + i)]
    return polyeder(horn, ytor)


def _under_ytan(normal: Vek, a: float, djup: float) -> Form:
    """Ett block under ytan genom origo med normalen (a åt alla håll längs ytan, djup under den)."""
    e1 = _enhet(_vinkelratt(normal))
    e2 = (normal[1] * e1[2] - normal[2] * e1[1], normal[2] * e1[0] - normal[0] * e1[2],
          normal[0] * e1[1] - normal[1] * e1[0])
    horn = [tuple(u * e1[k] + v * e2[k] + w * normal[k] for k in range(3))
            for w in (-djup, 0.0) for u, v in ((-a, -a), (a, -a), (a, a), (-a, a))]
    ytor = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return polyeder(horn, ytor)


def overgang(e: Overgang) -> Del:
    """Övergången som en kropp mellan den ena kanaltypens tvärsnitt och den andras (trianglar mellan profilerna)."""
    a, b = _profil(e.typ.fran), _profil(e.typ.till)
    L = e.typ.langd
    horn = [(x, y, 0.0) for x, y in a] + [(x, y, L) for x, y in b]
    n = N_RUND
    ytor = [tuple(range(n)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        ytor += [(i, j, n + j), (i, n + j, n + i)]
    kall = e.typ.till if e.typ.till.isolering else e.typ.fran
    return Del(e.typ.namn, polyeder(horn, ytor), _material(kall))


def _don(e: Don, g: Gren) -> Montage:
    t, m = e.typ, e.lage
    mm = Montage(e.id, beskrivning=t.namn, produkt=(t.produkt or None) if isinstance(t, Koksflakttyp) else None)
    if isinstance(t, Koksflakttyp):
        sys = _vagg(m)
        sb, sd = t.skorsten
        if t.sluttande:
            # ramen i underkanten och kåpan som sluttar upp mot skorstenen (x längs väggen, y uppåt, z ut från väggen)
            r = KAPA_RAM
            mm.lagg(Del(f"{t.namn}, ram {t.b:g} × {t.d:g}", box(-t.b / 2, t.b / 2, 0.0, r, 0.0, t.d), KOKSFLAKT), sys,
                    f"{e.id}-RAM")
            horn = [(-t.b / 2, r, 0.0), (t.b / 2, r, 0.0), (t.b / 2, r, t.d), (-t.b / 2, r, t.d),
                    (-sb / 2, t.h, 0.0), (sb / 2, t.h, 0.0), (sb / 2, t.h, sd), (-sb / 2, t.h, sd)]
            ytor = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
            mm.lagg(Del(f"{t.namn}, kåpa {t.b:g} × {t.d:g}", polyeder(horn, ytor), KOKSFLAKT), sys, f"{e.id}-KAPA")
        else:
            mm.lagg(Del(f"{t.namn}, kåpa {t.b:g} × {t.d:g}", box(-t.b / 2, t.b / 2, 0.0, t.h, 0.0, t.d), KOKSFLAKT),
                    sys, f"{e.id}-KAPA")
        mm.lagg(Del(f"{t.namn}, fettfilter", box(-t.b / 2 + 25.0, t.b / 2 - 25.0, -1.0, 2.0, 25.0, t.d - 25.0),
                    FETTFILTER), sys, f"{e.id}-FILTER")
        # skorstenskåpan: från kåpan upp till innertaket, överkanten i takets lutning (profil i ut-ur-väggen, upp)
        n = m.normal
        z0 = m.punkt[2]
        fram = flytt(m.punkt, n, sd)
        h_bak, h_fram = innertak_vid(m.punkt[0], m.punkt[1]) - z0, innertak_vid(fram[0], fram[1]) - z0
        x = (-n[1], n[0], 0.0)
        start = flytt(m.punkt, x, sb / 2)
        kapa = prisma([(0.0, t.h), (sd, t.h), (sd, h_fram), (0.0, h_bak)], sb)
        mm.lagg(Del(f"{t.namn}, skorstenskåpa {sb:g} × {sd:g}", kapa, KOKSFLAKT),
                Placering.axlar(start, n, (n[1], -n[0], 0.0)), f"{e.id}-SKORSTEN")
    elif isinstance(t, Vaggflakttyp):
        fb, fh, fd = t.front
        mm.lagg(Del(f"{t.namn}, front {fb:g} × {fh:g}", box(-fb / 2, fb / 2, -fh / 2, fh / 2, 0.0, fd),
                    VENTILATIONSDON), _vagg(m), f"{e.id}-FRONT")
    else:
        assert isinstance(t, Dontyp)
        sys = Placering.axlar(m.punkt, _vinkelratt(m.normal), m.normal)
        mm.lagg(Del(f"{t.namn}, front Ø{t.front_d:g}", cylinder(t.front_d / 2, 12.0), VENTILATIONSDON), sys,
                f"{e.id}-FRONT")
        mm.lagg(Del(f"{t.namn}, anslutning Ø{t.anslutning:g}", cylinder(t.anslutning / 2 - 1.0, t.djup,
                                                                           (0.0, 0.0, -t.djup)), VENTILATIONSDON),
                sys, f"{e.id}-HALS")
    return mm


def _avluft(e: Avluft) -> Montage:
    t, m = e.typ, e.lage
    mm = Montage(e.id, beskrivning=t.namn, produkt=t.produkt or None)
    if t.slag == "galler":
        alu = ALUMINIUM[int(m.ref[0])]                  # fönstrens aluminium på huskroppen
        sys = _vagg(m)
        mm.lagg(Del(f"{t.namn}, ram {t.b:g} × {t.h:g}", box(-t.b / 2, t.b / 2, -t.h / 2, t.h / 2, 0.0, 4.0), alu),
                sys, f"{e.id}-RAM")
        mm.lagg(Del(f"{t.namn}, huv", box(-t.b / 2 + 15.0, t.b / 2 - 15.0, -t.h / 2 + 15.0, t.h / 2 - 15.0, 4.0,
                                          t.djup), alu), sys, f"{e.id}-HUV")
    elif t.slag == "takfläkt":
        # sockeln av takplåt från takets yta till den vågräta överkanten, fläkten på den: bottenplattan, huset och
        # motorn under locket; en plåt runt sockeln i takets plan
        upp = Placering.axlar(m.punkt, (1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
        r = t.b / 2
        lag = r * math.tan(math.radians(S.TAKVINKEL)) + 50.0
        ring = cylinder(r, t.sockel + lag, (0.0, 0.0, -lag)) - cylinder(r - 1.0, t.sockel + lag + 2.0,
                                                                        (0.0, 0.0, -lag - 1.0))
        mm.lagg(Del(f"{t.namn}, sockel Ø{t.b:g}", ring - _under_ytan(m.normal, 2 * t.b, 2 * lag), TAKPLAT), upp,
                f"{e.id}-SOCKEL")
        z = t.sockel
        mm.lagg(Del(f"{t.namn}, bottenplatta Ø{t.b:g}", cylinder(r, 10.0, (0.0, 0.0, z)), TAKFLAKT), upp,
                f"{e.id}-PLATTA")
        hus = _stympad_kon(t.hus / 2, 0.3 * t.hus, z + 10.0, z + 0.78 * t.h)
        mm.lagg(Del(f"{t.namn}, hus Ø{t.hus:g}", hus, TAKFLAKT), upp, f"{e.id}-HUS")
        lock = cylinder(0.22 * t.hus, 0.22 * t.h, (0.0, 0.0, z + 0.78 * t.h))
        mm.lagg(Del(f"{t.namn}, motorns lock", lock, TAKFLAKT), upp, f"{e.id}-LOCK")
        a = r + 80.0
        mm.lagg(Del(f"{t.namn}, plåt i takets plan", box(-a, a, -a, a, 0.0, 2.0) - cylinder(r, 10.0, (0.0, 0.0, -5.0)),
                    TAKPLAT), Placering.axlar(m.punkt, (0.0, 1.0, 0.0), m.normal), f"{e.id}-PLAT")
    else:
        # takhuven av plåt: röret lodrätt från takets yta, huven överst och en plåt runt röret i takets plan
        r, t_ = t.anslutning / 2 + 3.0, 1.0
        upp = Placering.axlar(m.punkt, (1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
        ror = cylinder(r, t.h - 50.0, (0.0, 0.0, -40.0)) - cylinder(r - t_, t.h, (0.0, 0.0, -50.0))
        mm.lagg(Del(f"{t.namn}, rör Ø{2 * r:g}", ror, TAKPLAT), upp, f"{e.id}-ROR")
        huv = cylinder(t.b / 2, 50.0, (0.0, 0.0, t.h - 60.0)) - cylinder(t.b / 2 - t_, 50.0, (0.0, 0.0, t.h - 61.0))
        mm.lagg(Del(f"{t.namn}, huv Ø{t.b:g}", huv, TAKPLAT), upp, f"{e.id}-HUV")
        a = t.b / 2 + 80.0
        mm.lagg(Del(f"{t.namn}, plåt i takets plan", box(-a, a, -a, a, 0.0, 2.0) - cylinder(r, 10.0, (0.0, 0.0, -5.0)),
                    TAKPLAT), Placering.axlar(m.punkt, (0.0, 1.0, 0.0), m.normal), f"{e.id}-PLAT")
    return mm


def gren(g: Gren) -> Montage:
    """Grenens element i kedjans ordning."""
    vagar = kanalernas_vagar(g)
    m = Montage(f"{g.id} {g.namn}", beskrivning=f"Frånluft {g.rum}, {g.flode:g} l/s")
    for e in g.kedja:
        if isinstance(e, Kanal):
            m.lagg(kanal(e.id, vagar[e.id], e.typ, e.bredd_langs))
        elif isinstance(e, Don):
            m.lagg(_don(e, g))
        elif isinstance(e, Avluft):
            m.lagg(_avluft(e))
        elif isinstance(e, Flakt):
            r = e.riktning
            start = flytt(e.lage, r, -e.typ.langd / 2)
            m.lagg(Del(e.typ.namn, cylinder(e.typ.d / 2, e.typ.langd), FLAKT),
                   Placering.axlar(start, _vinkelratt(r), r), e.id)
        else:
            r = e.riktning
            start = flytt(e.lage, r, -e.typ.langd / 2)
            m.lagg(overgang(e), Placering.axlar(start, _tvars(e.bredd_langs, r), r), e.id)
    return m


def montage() -> Montage:
    v = ventilation()
    m = Montage("Ventilation", beskrivning="Frånluft: köksfläkten, badrumsfläkten och källarrummet "
                                          "(hus/installationer/ventilation)")
    for g in v.grenar.values():
        m.lagg(gren(g))
    return m
