"""Tappvattnets geometri ur systemet (system.py): rören (rör-i-rör och matarledningarna), dosorna och väggfästena vid
tappställena och fördelarna, ett montage per rum och ett för teknikrummet. Delarna kontrolleras inte i modellens
krockkontroll (kontrollregler.UTOM_KONTROLL) och tar inga hål i andra delar; vattnet har en egen kontroll
(`./mod vatten kontroll`, med krockarna mot huset och ventilationen) och redovisar genomföringarna.

Rören är raka bitar längs mittlinjen med skyddsrörets ytterdiameter, i böjarna förlängda så att hörnen fylls. Dosorna
i ytans system: origo på ytan, z ut ur ytan, x vågrätt längs ytan (golvdosor: x från varmt till kallt).
"""
from __future__ import annotations

import math

from modellering import Del, Montage, Placering, box, cylinder

from trebodar.material import FORDELARSTAM, TAPPVATTEN_KV, TAPPVATTEN_VV, VATTENDOSA

from ..montering import Vek, enhet
from .punkter import Fordelare, Tappstalle
from .system import vatten

MATERIAL = {"KV": TAPPVATTEN_KV, "VV": TAPPVATTEN_VV}
D_STAM = 32.0                   # fördelarnas stam


def _vinkelratt(v: Vek) -> Vek:
    a = (0.0, 0.0, 1.0) if abs(v[2]) < 0.9 else (1.0, 0.0, 0.0)
    return (v[1] * a[2] - v[2] * a[1], v[2] * a[0] - v[0] * a[2], v[0] * a[1] - v[1] * a[0])


def ror(namn: str, beskrivning: str, vag: list[Vek], d: float, media: str) -> Montage:
    """Röret som raka bitar längs mittlinjen, förlängda i böjarna så att hörnen fylls."""
    m = Montage(namn, beskrivning=beskrivning)
    bitar = [(a, b) for a, b in zip(vag, vag[1:]) if math.dist(a, b) > 1.0]
    r = d / 2
    for i, (a, b) in enumerate(bitar):
        lgd = math.dist(a, b)
        z = enhet((b[0] - a[0], b[1] - a[1], b[2] - a[2]))
        fore, efter = (r if i > 0 else 0.0), (r if i < len(bitar) - 1 else 0.0)
        m.lagg(Del(f"{beskrivning} L={lgd:.0f}", cylinder(r, lgd + fore + efter, (0.0, 0.0, -fore)), MATERIAL[media]),
               Placering.axlar(a, _vinkelratt(z), z), f"{namn}-{i + 1}")
    return m


def _dosa(t: Tappstalle) -> tuple[Del, Placering]:
    """Väggdosan i väggen (fronten i ytan), golvdosan på golvet eller väggfästet utanpå väggen."""
    d, m = t.dosa, t.lage
    n = m.normal
    if d.slag == "golv":
        return (Del(d.namn, box(-d.b / 2, d.b / 2, -d.h / 2, d.h / 2, 0.0, d.djup), VATTENDOSA),
                Placering.axlar(m.punkt, t.kallt or (1.0, 0.0, 0.0), n))
    z0, z1 = (-d.djup, 0.0) if d.slag == "vägg" else (0.0, d.djup)
    return (Del(d.namn, box(-d.b / 2, d.b / 2, -d.h / 2, d.h / 2, z0, z1), VATTENDOSA),
            Placering.axlar(m.punkt, (-n[1], n[0], 0.0), n))


def _fordelare(f: Fordelare) -> tuple[Del, Placering]:
    """Fördelarens stam från utgång 0 till utgången efter den sista."""
    lgd = (f.typ.utgangar + 1) * f.typ.delning
    return (Del(f.typ.namn, cylinder(D_STAM / 2, lgd), FORDELARSTAM),
            Placering.axlar(f.utgang(0), _vinkelratt(f.riktning), f.riktning))


def montage() -> Montage:
    v = vatten()
    m = Montage("Vatten", beskrivning="Tappvatten, kallt och varmt: rör-i-rör från fördelarskåpet i teknikrummet "
                                      "(hus/installationer/vatten)")
    delar = {"Teknikrum": Montage("Teknikrum", beskrivning="Fördelarna och matarledningarna")}
    delar.update({r.namn: Montage(r.namn) for r in v.rum.values()})
    for f in v.fordelare.values():
        delar["Teknikrum"].lagg(*_fordelare(f), f.id)
    for t in v.tappstallen.values():
        delar[v.modul[t.id]].lagg(*_dosa(t), t.id)
    for r in v.ror.values():
        delar[v.modul[r.id]].lagg(ror(r.id, f"{r.media} {r.typ.namn}", v.vag(r), r.typ.yttre, r.media))
    for x in delar.values():
        m.lagg(x)
    return m
