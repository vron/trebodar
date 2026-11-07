"""Tappvattnets geometri ur systemet (system.py): rören (rör-i-rör, kopparrören och matarledningarna), dosorna,
väggfästena och hylsorna vid tappställena och fördelarna (underfördelarna med konsoler på väggen), ett montage per rum
och ett för teknikrummet. Delarna kontrolleras inte i modellens
krockkontroll (kontrollregler.UTOM_KONTROLL) och tar inga hål i andra delar; vattnet har en egen kontroll
(`./mod vatten kontroll`, med krockarna mot huset och ventilationen) och redovisar genomföringarna.

Rören är raka bitar längs mittlinjen med skyddsrörets ytterdiameter, i böjarna förlängda så att hörnen fylls. Dosorna
i ytans system: origo på ytan, z ut ur ytan, x vågrätt längs ytan (golvdosor: x från varmt till kallt).
"""
from __future__ import annotations

import math

from modellering import Del, Montage, Placering, box, cylinder

from trebodar.material import AVLOPPSROR, FORDELARSTAM, KOPPARROR, TAPPVATTEN_KV, TAPPVATTEN_VV, VATTENDOSA

from ..montering import KALLARTAK, PLAN, Vek, enhet
from .punkter import Fordelare, Tappstalle, forskjutning, hylsa
from .system import vatten
from .underfordelare import Underfordelare

MATERIAL = {"KV": TAPPVATTEN_KV, "VV": TAPPVATTEN_VV}
D_STAM = 32.0                   # fördelarnas stam
KONSOL = 30.0                   # underfördelarnas konsoler, bredd
HYLSANS_GODS = 1.8              # hylsornas godstjocklek (PP-avloppsrör 50)


def _vinkelratt(v: Vek) -> Vek:
    a = (0.0, 0.0, 1.0) if abs(v[2]) < 0.9 else (1.0, 0.0, 0.0)
    return (v[1] * a[2] - v[2] * a[1], v[2] * a[0] - v[0] * a[2], v[0] * a[1] - v[1] * a[0])


def ror(namn: str, beskrivning: str, vag: list[Vek], d: float, media: str, koppar: bool = False) -> Montage:
    """Röret som raka bitar längs mittlinjen, förlängda i böjarna så att hörnen fylls (rör-i-rör i skyddsrörets färg
    efter media, kopparrör i koppar)."""
    m = Montage(namn, beskrivning=beskrivning)
    bitar = [(a, b) for a, b in zip(vag, vag[1:]) if math.dist(a, b) > 1.0]
    r = d / 2
    for i, (a, b) in enumerate(bitar):
        lgd = math.dist(a, b)
        z = enhet((b[0] - a[0], b[1] - a[1], b[2] - a[2]))
        fore, efter = (r if i > 0 else 0.0), (r if i < len(bitar) - 1 else 0.0)
        m.lagg(Del(f"{beskrivning} L={lgd:.0f}", cylinder(r, lgd + fore + efter, (0.0, 0.0, -fore)),
                   KOPPARROR if koppar else MATERIAL[media]),
               Placering.axlar(a, _vinkelratt(z), z), f"{namn}-{i + 1}")
    return m


def _hylsor(t: Tappstalle) -> list[tuple[Del, Placering, str]]:
    """Tappställets hylsor genom mellanbjälklaget, en per rör (PP-avloppsrör, gjutna mellan järnen)."""
    d = t.dosa.b
    ror_ = cylinder(d / 2, PLAN[1] - KALLARTAK) - cylinder(d / 2 - HYLSANS_GODS, PLAN[1] - KALLARTAK + 2.0,
                                                           (0.0, 0.0, -1.0))
    return [(Del(f"Hylsa Ø{d:g} PP i bjälklaget", ror_, AVLOPPSROR),
             Placering.axlar((*hylsa(t, m), KALLARTAK), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0)), f"{t.id}-HYLSA-{m}")
            for m, q in (("KV", t.typ.kv), ("VV", t.typ.vv)) if q > 0]


def _dosa(t: Tappstalle) -> tuple[Del, Placering]:
    """Väggdosan i väggen (fronten i ytan), golvdosan på golvet (förskjuten mellan järnen) eller väggfästet utanpå
    väggen."""
    d, m = t.dosa, t.lage
    n = m.normal
    if d.slag == "golv":
        dx, dy = forskjutning(t)
        return (Del(d.namn, box(-d.b / 2, d.b / 2, -d.h / 2, d.h / 2, 0.0, d.djup), VATTENDOSA),
                Placering.axlar((m.punkt[0] + dx, m.punkt[1] + dy, m.punkt[2]), t.kallt or (1.0, 0.0, 0.0), n))
    z0, z1 = (-d.djup, 0.0) if d.slag == "vägg" else (0.0, d.djup)
    return (Del(d.namn, box(-d.b / 2, d.b / 2, -d.h / 2, d.h / 2, z0, z1), VATTENDOSA),
            Placering.axlar(m.punkt, (-n[1], n[0], 0.0), n))


def _fordelare(f: Fordelare) -> tuple[Del, Placering]:
    """Fördelarens stam från utgång 0 till utgången efter den sista."""
    lgd = (f.typ.utgangar + 1) * f.typ.delning
    return (Del(f.typ.namn, cylinder(D_STAM / 2, lgd), FORDELARSTAM),
            Placering.axlar(f.utgang(0), _vinkelratt(f.riktning), f.riktning))


def _underfordelare(u: Underfordelare, stammar: list[Fordelare]) -> Montage:
    """Underfördelarens stammar och två konsoler från väggen till den yttre stammen, vid stammarnas ändar."""
    m = Montage(u.id, beskrivning=u.namn)
    for f in stammar:
        m.lagg(*_fordelare(f), f.id)
    n, r = u.normal, u.riktning
    ut = max(stammar, key=lambda f: (f.lage[0] - u.start[0]) * n[0] + (f.lage[1] - u.start[1]) * n[1])
    djup = (ut.lage[0] - u.start[0]) * n[0] + (ut.lage[1] - u.start[1]) * n[1] + D_STAM / 2
    z0 = min(f.lage[2] for f in stammar) - D_STAM / 2
    z1 = max(f.lage[2] for f in stammar) + D_STAM / 2
    lgd = max((f.typ.utgangar + 1) * f.typ.delning for f in stammar)
    for i, s in enumerate((0.0, lgd)):
        p = (u.start[0] + r[0] * s, u.start[1] + r[1] * s, z0)
        m.lagg(Del("Konsol för underfördelaren", box(-KONSOL / 2, KONSOL / 2, 0.0, djup, 0.0, z1 - z0), FORDELARSTAM),
               Placering.axlar(p, (n[1], -n[0], 0.0), (0.0, 0.0, 1.0)), f"{u.id}-KONSOL{i + 1}")    # y ut ur väggen
    return m


def montage() -> Montage:
    v = vatten()
    m = Montage("Vatten", beskrivning="Tappvatten, kallt och varmt: rör-i-rör från fördelarskåpet i teknikrummet "
                                      "(hus/installationer/vatten)")
    delar = {"Teknikrum": Montage("Teknikrum", beskrivning="Fördelarna och matarledningarna")}
    delar.update({r.namn: Montage(r.namn) for r in v.rum.values()})
    for f in v.fordelare.values():
        if f.id.split("-")[0] not in v.underfordelare:
            delar["Teknikrum"].lagg(*_fordelare(f), f.id)
    for u in v.underfordelare.values():
        delar[u.rum].lagg(_underfordelare(u, [f for f in v.fordelare.values() if f.id.split("-")[0] == u.id]))
    for t in v.tappstallen.values():
        if t.dosa.slag == "hylsa":
            for d, pl, kod in _hylsor(t):
                delar[v.modul[t.id]].lagg(d, pl, kod)
        else:
            delar[v.modul[t.id]].lagg(*_dosa(t), t.id)
    for r in v.ror.values():
        delar[v.modul[r.id]].lagg(ror(r.id, f"{r.media} {r.typ.namn}", v.vag(r), r.typ.yttre, r.media,
                                      r.typ.kod.startswith("CU")))
    for x in delar.values():
        m.lagg(x)
    return m
