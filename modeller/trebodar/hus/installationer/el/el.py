"""Elinstallationens geometri: armaturer, apparater, dosor och rör ur installationen (installation.py), ett montage
per modul (rum och bjälklag). Delarna kontrolleras inte mot annat (kontrollregler.UTOM_KONTROLL): rören och dosorna
går genom skikten utan håltagning.

Armaturen i sitt system: origo på takytan, z ut ur taket (in i rummet), x längs y i huset (i takfallets plan).
Apparaterna: origo på väggens yta, z ut ur väggen, y uppåt.
"""
from __future__ import annotations

import math

from modellering import Del, Montage, Placering, box, cylinder

from trebodar.material import APPARAT, ARMATUR, ARMATURLINS, DRIVDON, ELDOSA, ELROR

from .installation import installation
from .punkter import LINS_INDRAG, TAKSKIVOR, Apparat, Dosa, Lampa, Montering, Vek, drivdonet
from .typer import Apparattyp, Armaturtyp, Dosatyp

RING_T = 2.0                    # frontringens tjocklek
SPOT_D, SPOT_H = 64.0, 30.0     # den vridbara spotens kropp


def _system(m: Montering) -> Placering:
    n = m.normal
    x = (0.0, 1.0, 0.0) if m.yta == "tak" else (-n[1], n[0], 0.0)
    return Placering.axlar(m.punkt, x, n)


def _vinkelratt(v: Vek) -> Vek:
    a = (0.0, 0.0, 1.0) if abs(v[2]) < 0.9 else (1.0, 0.0, 0.0)
    return (v[1] * a[2] - v[2] * a[1], v[2] * a[0] - v[0] * a[2], v[0] * a[1] - v[1] * a[0])


def _delar_armatur(t: Armaturtyp) -> dict[str, Del]:
    ring = cylinder(t.ring_d / 2, RING_T) - cylinder(t.ring_d / 2 - 11.0, RING_T + 2.0, (0.0, 0.0, -1.0))
    # huset: öppet nedåt (in i rummet), med 5 mm topp
    kropp = (cylinder(t.hal_d / 2, t.djup, (0.0, 0.0, -t.djup)) -
             cylinder(SPOT_D / 2 + 3.0, t.djup, (0.0, 0.0, -t.djup + 5.0)))
    spot = cylinder(SPOT_D / 2, SPOT_H, (0.0, 0.0, 1.0))
    ut = {"RING": Del(f"{t.tillverkare} {t.artikel} frontring Ø{t.ring_d:g}", ring, ARMATUR),
          "KROPP": Del(f"{t.tillverkare} {t.artikel} armaturhus Ø{t.hal_d:g}", kropp, ARMATUR),
          "SPOT": Del(f"{t.tillverkare} {t.artikel} vridbar spot", spot, ARMATUR),
          "LINS": Del(f"{t.tillverkare} {t.artikel} lins Ø{t.lysande_d:g}", cylinder(t.lysande_d / 2, 1.0),
                      ARMATURLINS)}
    if t.drivdon:
        l, b, h = t.drivdon
        ut["DRIVDON"] = Del(f"{t.tillverkare} {t.artikel} drivdon", box(-l / 2, l / 2, -b / 2, b / 2, 0.0, h), DRIVDON)
    return ut


def armatur(p: Lampa) -> Montage:
    """Armaturen: frontringen på takytan, huset i håltagningen och spoten vriden så att ljuset går i lampans
    riktning; drivdonet på gipsen bredvid huset."""
    t = p.typ
    d = _delar_armatur(t)
    sys = _system(p.lage)
    m = Montage(p.id, beskrivning=f"{t.tillverkare} {t.namn}")
    m.lagg(d["RING"], sys, f"{p.id}-RING")
    m.lagg(d["KROPP"], sys, f"{p.id}-KROPP")
    # spoten vriden kring linsens mitt (punkter.linsen), med sin axel (z) bakåt mot ljusets riktning
    r = sys.R
    lok: Vek = (sum(r[i][0] * p.riktning[i] for i in range(3)), sum(r[i][1] * p.riktning[i] for i in range(3)),
                sum(r[i][2] * p.riktning[i] for i in range(3)))
    spot = Placering.axlar((0.0, 0.0, -LINS_INDRAG), _vinkelratt(lok), (-lok[0], -lok[1], -lok[2]))
    m.lagg(d["SPOT"], sys @ spot, f"{p.id}-SPOT")
    m.lagg(d["LINS"], sys @ spot, f"{p.id}-LINS")
    if "DRIVDON" in d and t.drivdon:
        m.lagg(d["DRIVDON"], sys @ Placering.flytt(drivdonet(p), 0.0, -TAKSKIVOR - t.drivdon[2]), f"{p.id}-DRIVDON")
    return m


def _dosa_del(t: Dosatyp) -> Del:
    return Del(f"{t.namn} Ø{t.diameter:g}", cylinder(t.diameter / 2, t.djup, (0.0, 0.0, -t.djup)), ELDOSA)


def _apparat_delar(t: Apparattyp) -> list[tuple[str, Del, Placering]]:
    b, h = t.ram
    ut = [("RAM", Del(f"{t.namn}, täckram {b:g}×{h:g}", box(-b / 2, b / 2, -h / 2, h / 2, 0.0, 9.0), APPARAT),
           Placering())]
    if t.slag == "uttag":
        for i in range(t.kanaler):
            x = (i - (t.kanaler - 1) / 2) * 71.0
            ut.append((f"UTTAG{i + 1}", Del(f"{t.namn}, uttag", cylinder(19.0, 3.0), APPARAT),
                       Placering.flytt(x, 0.0, 9.0)))
    else:
        w = (b - 16.0) / t.kanaler
        for i in range(t.kanaler):
            x = -b / 2 + 8.0 + (i + 0.5) * w
            ut.append((f"VIPPA{i + 1}", Del(f"{t.namn}, vippa", box(-w / 2 + 1.0, w / 2 - 1.0, -h / 2 + 10.0,
                                                                   h / 2 - 10.0, 0.0, 3.0), APPARAT),
                       Placering.flytt(x, 0.0, 9.0)))
    return ut


def apparat(p: Apparat) -> Montage:
    sys = _system(p.lage)
    m = Montage(p.id, beskrivning=p.typ.namn)
    m.lagg(_dosa_del(p.typ.dosa), sys, f"{p.id}-DOSA")
    for namn, d, pl in _apparat_delar(p.typ):
        m.lagg(d, sys @ pl, f"{p.id}-{namn}")
    return m


def dosa(p: Dosa) -> Montage:
    m = Montage(p.id, beskrivning=p.typ.namn)
    m.lagg(_dosa_del(p.typ), _system(p.lage), f"{p.id}-DOSA")
    return m


def ror(namn: str, vag: list[Vek], diameter: float) -> Montage:
    """Röret som raka bitar längs mittlinjen."""
    m = Montage(namn, beskrivning=f"Rör Ø{diameter:g}")
    for i, (a, b) in enumerate(zip(vag, vag[1:])):
        v = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
        langd = math.hypot(*v)
        if langd < 1.0:
            continue
        z = (v[0] / langd, v[1] / langd, v[2] / langd)
        d = Del(f"Rör Ø{diameter:g} L={langd:.0f}", cylinder(diameter / 2, langd), ELROR)
        m.lagg(d, Placering.axlar(a, _vinkelratt(z), z), f"{namn}-{i + 1}")
    return m


def montage() -> Montage:
    inst = installation()
    m = Montage("El", beskrivning="Elinstallationen: armaturer, apparater, dosor och rör (hus/installationer/el)")
    delar: dict[str, Montage] = {}
    for p in inst.punkter.values():
        mm = delar.setdefault(inst.modul[p.id], Montage(inst.modul[p.id]))
        mm.lagg(armatur(p) if isinstance(p, Lampa) else apparat(p) if isinstance(p, Apparat) else dosa(p))
    for r in inst.ror.values():
        mm = delar.setdefault(inst.modul[r.id], Montage(inst.modul[r.id]))
        mm.lagg(ror(r.id, inst.vag(r), r.typ.ytterdiameter))
    for mm in delar.values():
        m.lagg(mm)
    return m
