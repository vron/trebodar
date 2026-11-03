"""Brandlarmets geometri ur larm.py: brandvarnarna med sina dosor (på plan 1 en takdosa i installationsskiktet bakom
gipsen, i källaren en utanpåliggande dosa under betongen), kopplingsdosorna och kablarna som raka bitar längs vägarna.
Delarna kontrolleras inte i modellens krockkontroll (kontrollregler.UTOM_KONTROLL); brandlarmet har en egen kontroll
(`./mod brandlarm kontroll`, med krockarna mot huset och de andra installationerna).
"""
from __future__ import annotations

import math

from modellering import Del, Material, Montage, Placering, cylinder

from trebodar.material import BRANDLARMSKABEL, BRANDVARNARE, ELDOSA

from ..montering import TAKSKIVOR, Montering, Vek, flytt
from .larm import BRANDVARNARE as BV
from .larm import KABEL_D, TAKDOSA, YTDOSA, Typ, brandlarm


def _vinkelratt(v: Vek) -> Vek:
    a = (1.0, 0.0, 0.0) if abs(v[0]) < 0.9 else (0.0, 1.0, 0.0)
    k = sum(p * q for p, q in zip(a, v))
    w = (a[0] - k * v[0], a[1] - k * v[1], a[2] - k * v[2])
    n = math.sqrt(sum(c * c for c in w))
    return (w[0] / n, w[1] / n, w[2] / n)


def _skiva(t: Typ, material: Material, origo: Vek, normal: Vek) -> tuple[Del, Placering]:
    """En rund del (brandvarnare eller dosa) från origo längs normalen."""
    d = Del(f"{t.namn.split(',')[0].split(' (')[0]} Ø{t.diameter:g}", cylinder(t.diameter / 2, t.hojd), material,
            t.namn)
    return d, Placering.axlar(origo, _vinkelratt(normal), normal)


def _punkt(id_: str, m: Montering, plan1: bool, varnare: bool) -> Montage:
    """Brandvarnaren (eller kopplingsdosan) med sin dosa: på plan 1 takdosan bakom gipsen, i källaren under betongen."""
    mm = Montage(id_, beskrivning=BV.namn if varnare else YTDOSA.namn)
    n = m.normal
    if plan1:
        mm.lagg(*_skiva(TAKDOSA, ELDOSA, flytt(m.punkt, n, -(TAKSKIVOR + TAKDOSA.hojd)), n), f"{id_}-DOSA")
        if varnare:
            mm.lagg(*_skiva(BV, BRANDVARNARE, m.punkt, n), f"{id_}-VARNARE")
        return mm
    mm.lagg(*_skiva(YTDOSA, ELDOSA, m.punkt, n), f"{id_}-DOSA")
    if varnare:
        mm.lagg(*_skiva(BV, BRANDVARNARE, flytt(m.punkt, n, YTDOSA.hojd), n), f"{id_}-VARNARE")
    return mm


def _kabel(namn: str, vag: tuple[Vek, ...]) -> Montage:
    """Kabeln som raka bitar längs mittlinjen (som elens rör)."""
    m = Montage(namn, beskrivning=f"Brandlarmets kabel Ø{KABEL_D:g}")
    for i, (a, b) in enumerate(zip(vag, vag[1:])):
        v = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
        langd = math.hypot(*v)
        if langd < 1.0:
            continue
        z = (v[0] / langd, v[1] / langd, v[2] / langd)
        d = Del(f"Kabel Ø{KABEL_D:g} L={langd:.0f} brandlarm", cylinder(KABEL_D / 2, langd), BRANDLARMSKABEL)
        m.lagg(d, Placering.axlar(a, _vinkelratt(z), z), f"{namn}-{i + 1}")
    return m


def montage() -> Montage:
    b = brandlarm()
    m = Montage("Brandlarm", beskrivning="Brandvarnare 230 V, trådbundet sammankopplade, med dosor och kablar "
                                        "(hus/installationer/brandlarm)")
    varnare = Montage("Brandvarnare", beskrivning=BV.namn)
    for v in b.varnare.values():
        varnare.lagg(_punkt(v.id, v.lage, v.plan == 1, True))
    m.lagg(varnare)
    dosor = Montage("Kopplingsdosor", beskrivning=YTDOSA.namn)
    for d in b.dosor.values():
        dosor.lagg(_punkt(d.id, d.lage, False, False))
    m.lagg(dosor)
    kablar = Montage("Kablar", beskrivning="Brandlarmets kabel, sammankopplingen")
    for r in b.kablar.values():
        kablar.lagg(_kabel(r.id, r.vag))
    m.lagg(kablar)
    return m
