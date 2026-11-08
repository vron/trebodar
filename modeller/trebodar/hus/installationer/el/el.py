"""Elinstallationens geometri: armaturer, apparater, dosor och rör ur installationen (installation.py), ett montage
per modul (rum och bjälklag). Delarna kontrolleras inte mot annat (kontrollregler.UTOM_KONTROLL): rören och dosorna
går genom skikten utan håltagning.

Armaturen i sitt system: origo på takytan, z ut ur taket (in i rummet), x längs y i huset (i takfallets plan).
Pendlarna: takkoppen på takytan, sladden lodrätt ned och armaturen i ett lodrätt system med origo i dess överkant
(z uppåt, armaturen under origo), byggd av rotationskroppar ur formens mått (pendel_*).
Apparaterna: origo på väggens yta, z ut ur väggen, y uppåt.
"""
from __future__ import annotations

import math

from modellering import Del, Form, Montage, Placering, box, cylinder, polyeder, varv

from trebodar.byggdelar.ror import stang

from trebodar.material import (APPARAT, ARMATUR, ARMATUR_SVART, ARMATURLINS, ASK, DRIVDON, ELDOSA, ELROR,
                               FROSTAT_GLAS, LEDKANAL_ALU, LEDLIST, MASSING, OPALGLAS, RAMASSING, SLADD_SVART, SLADD_VIT)

from .installation import installation
from ..montering import TAKSKIVOR, Montering, Vek
from .punkter import LINS_INDRAG, PLATTA_T, Apparat, Dosa, Lampa, drivdonet, linsen, pendeln, tuben
from .typer import Apparattyp, Armaturtyp, Dosatyp, Pendel

RING_T = PLATTA_T                # frontringens tjocklek
SPOT_D, SPOT_H = 64.0, 30.0     # den vridbara spotens kropp
TUB_GODS = 2.0                  # tubens gods
BAFFEL = 10.0                   # bländskyddets djup in från tubens front


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


def _delar_tub(t: Armaturtyp) -> dict[str, Del]:
    h = t.huvud
    assert h is not None
    r = h.diameter / 2
    ri = r - TUB_GODS
    rl = min(t.lysande_d / 2, ri - 3.0)
    namn = f"{t.tillverkare} {t.artikel}"
    # tuben längs z från den bakre änden (0) till fronten (langd), ihålig framifrån till bakom reflektorn
    tub = cylinder(r, h.langd) - cylinder(ri, h.indrag + 40.0, (0.0, 0.0, h.langd - h.indrag - 40.0 + 1.0))
    baffel = (cylinder(ri, BAFFEL, (0.0, 0.0, h.langd - BAFFEL)) -
              cylinder(rl, BAFFEL + 2.0, (0.0, 0.0, h.langd - BAFFEL - 1.0)))
    return {"PLATTA": Del(f"{namn} frontplatta Ø{t.ring_d:g}", cylinder(t.ring_d / 2, PLATTA_T), ARMATUR),
            "KROPP": Del(f"{namn} dosa Ø{t.hal_d:g}", cylinder(t.hal_d / 2, t.djup, (0.0, 0.0, -t.djup)), ARMATUR),
            "STAM": Del(f"{namn} stam Ø{h.stam_d:g}", cylinder(h.stam_d / 2, h.stam), ARMATUR),
            "LED": Del(f"{namn} led", cylinder(h.stam_d / 2 + 3.0, h.stam_d + 6.0, (0.0, 0.0, -h.stam_d / 2 - 3.0)),
                       ARMATUR),
            "TUB": Del(f"{namn} tub Ø{h.diameter:g}×{h.langd:g}", tub, ARMATUR),
            "BAFFEL": Del(f"{namn} bländskydd", baffel, ARMATUR_SVART),
            "LINS": Del(f"{namn} reflektor Ø{2 * rl:g}", cylinder(rl, 1.0), ARMATURLINS)}


def _tubspot(p: Lampa) -> Montage:
    """Tubspoten: frontplattan på takytan och dosan i håltagningen, stammen längs takets normal, leden och tuben
    riktad i ljusets riktning (punkter.tuben), bländskyddet och reflektorn i tubens front."""
    t = p.typ
    d = _delar_tub(t)
    sys = _system(p.lage)
    m = Montage(p.id, beskrivning=f"{t.tillverkare} {t.namn}", produkt=t.produkt or None)
    m.lagg(d["PLATTA"], sys, f"{p.id}-PLATTA")
    m.lagg(d["KROPP"], sys, f"{p.id}-KROPP")
    m.lagg(d["STAM"], sys @ Placering.flytt(0.0, 0.0, PLATTA_T), f"{p.id}-STAM")
    led, bak, _ = tuben(p)
    r = p.riktning
    tubsys = Placering.axlar(bak, _vinkelratt(r), r)
    # leden: en tvärgående axel genom stammens ände, vinkelrätt mot stammen och tuben
    n = p.lage.normal
    tvars = (n[1] * r[2] - n[2] * r[1], n[2] * r[0] - n[0] * r[2], n[0] * r[1] - n[1] * r[0])
    m.lagg(d["LED"], Placering.axlar(led, _vinkelratt(tvars) if math.hypot(*tvars) > 1e-6 else (1.0, 0.0, 0.0),
                                    tvars if math.hypot(*tvars) > 1e-6 else (0.0, 1.0, 0.0)), f"{p.id}-LED")
    m.lagg(d["TUB"], tubsys, f"{p.id}-TUB")
    m.lagg(d["BAFFEL"], tubsys, f"{p.id}-BAFFEL")
    lins = linsen(p)
    m.lagg(d["LINS"], Placering.axlar(lins, _vinkelratt(r), (-r[0], -r[1], -r[2])), f"{p.id}-LINS")
    return m


# ------------------------------------------------------------------ pendlar

Profil = list[tuple[float, float]]


def _forskjuten(kurva: Profil, t: float) -> Profil:
    """Kurvan (r, z) flyttad t längs sin högra normal (för en kurva utåt och nedåt: in under den)."""
    ut = []
    for i, (r, z) in enumerate(kurva):
        a, b = kurva[max(i - 1, 0)], kurva[min(i + 1, len(kurva) - 1)]
        dr, dz = b[0] - a[0], b[1] - a[1]
        lg = math.hypot(dr, dz)
        ut.append((r + t * dz / lg, z - t * dr / lg))
    return ut


def _plat(kurva: Profil, t: float) -> Form:
    """Spunnen plåt t tjock: rotationskroppen mellan kurvan (den synliga ytan) och samma kurva t in."""
    inre = _forskjuten(kurva, t)
    return varv(("kurva", kurva), ("linje", [kurva[-1], inre[-1]]), ("kurva", inre[::-1]),
                ("linje", [inre[0], kurva[0]]))


def _skiva(r0: float, r1: float, z0: float, z1: float) -> Form:
    """Ring (r0 > 0) eller skiva (r0 = 0) mellan z0 och z1."""
    return varv(("linje", [(r0, z0), (r1, z0), (r1, z1), (r0, z1), (r0, z0)]))


# PH 5, mätt ur produktbilden (Lampmasters 6090322, Ø500): (r, z) i mm från kåpans överkant, z skalat till
# katalogens höjd. Toppskärmen är en flack kon med en trumpet under, som slutar i en krona Ø175 strax ovanför
# huvudskärmens hål (Ø190): springan släpper upp ljus mot trumpeten och toppskärmen.
_PH5_TOPP = [(33.0, -60.0), (70.0, -63.5), (100.0, -67.5), (130.0, -72.5), (150.5, -77.0)]
_PH5_TRUMPET = [(149.0, -78.5), (135.0, -85.8), (118.0, -89.2), (102.0, -91.2), (93.5, -93.8), (89.0, -97.5),
                (87.5, -102.0), (88.5, -112.0), (90.0, -120.0), (90.8, -127.0)]
_PH5_SKARM = [(95.0, -128.5), (127.6, -133.9), (152.3, -141.1), (176.4, -150.7), (201.6, -162.8), (224.3, -174.9),
              (241.4, -184.5), (248.6, -189.3), (250.0, -192.0)]
_PH5_KUPA = [(42.0, -193.5), (62.0, -195.0), (76.0, -198.5), (86.0, -204.0), (94.0, -212.0), (99.0, -222.0),
             (102.0, -232.0), (103.8, -241.0), (104.3, -247.0)]
_PH5_HOJD = 274.0                  # bildens höjd till glasets botten


def _ph5(t: Armaturtyp, pe: Pendel) -> list[tuple[str, Del]]:
    k = pe.hojd / _PH5_HOJD
    s = pe.diameter / 500.0

    def sk(c: Profil) -> Profil:
        return [(r * s, z * k) for r, z in c]
    namn = f"{t.tillverkare} {t.namn}"
    stag = cylinder(1.5, 46.0 * k)
    return [("KAPA", Del(f"{namn} kåpa", cylinder(33.5 * s, 59.0 * k, (0.0, 0.0, -59.0 * k)), ARMATUR)),
            ("ROR", Del(f"{namn} rör till sockeln", cylinder(6.0, 131.0 * k, (0.0, 0.0, -190.0 * k)), ARMATUR)),
            ("TOPPSKARM", Del(f"{namn} toppskärm Ø{301 * s:.0f}", _plat(sk(_PH5_TOPP), 1.2), ARMATUR)),
            ("TRUMPET", Del(f"{namn} trumpet", _plat(sk(_PH5_TRUMPET), 1.0), ARMATUR)),
            ("SKARM", Del(f"{namn} skärm Ø{500 * s:.0f}", _plat(sk(_PH5_SKARM), 1.2), ARMATUR)),
            ("MELLANSKIVA", Del(f"{namn} mellanskiva", _skiva(62.0 * s, 96.0 * s, -187.5 * k, -186.0 * k), ARMATUR)),
            ("KUPA", Del(f"{namn} kupa Ø{208 * s:.0f}", _plat(sk(_PH5_KUPA), 1.0), ARMATUR)),
            ("HALLARE", Del(f"{namn} glasets hållare", _skiva(56.0 * s, 61.0 * s, -251.0 * k, -249.0 * k), ARMATUR)),
            ("LINS", Del(f"{namn} frostat glas Ø{117 * s:.0f}",
                         varv(("linje", [(0.0, -251.0 * k), (58.7 * s, -251.0 * k), (54.5 * s, -274.0 * k),
                                         (0.0, -274.0 * k), (0.0, -251.0 * k)])), FROSTAT_GLAS)),
            *[(f"STAG{i + 1}", Del(f"{namn} stag", stag, ARMATUR)) for i in range(3)]]


def _ph5_stag(i: int, k: float) -> Placering:
    """Stagen mellan toppskärmen och huvudskärmen, tre på radien 120."""
    v = 2 * math.pi * i / 3 + math.pi / 6
    return Placering.flytt(120.0 * math.cos(v), 120.0 * math.sin(v), -134.0 * k)


def _vl45(t: Armaturtyp, pe: Pendel) -> list[tuple[str, Del]]:
    """VL45: fästet (rör Ø8, ring Ø13 och krage av mässing) och globen, lika hög som bred med foten: en superellips
    (n = 2,6) och en fot i botten."""
    d, f = pe.diameter, pe.hojd - pe.diameter
    r_krage, r_fot, h_fot = 0.14 * d, 0.235 * d, 0.035 * d
    a, b = d / 2, d / 2 - h_fot / 2           # globens halva bredd och höjd (foten under)
    zc = -f - b
    n = 2.6

    def punkt(v: float) -> tuple[float, float]:
        c, s_ = math.cos(v), math.sin(v)
        return a * abs(c) ** (2 / n), zc + b * math.copysign(abs(s_) ** (2 / n), s_)
    v0 = math.acos((r_krage * 0.9 / a) ** (n / 2))
    v1 = -math.acos((r_fot / a) ** (n / 2))
    kurva = [punkt(v0 + (v1 - v0) * i / 40) for i in range(41)]
    z_fot = kurva[-1][1]
    glas = varv(("linje", [(0.0, kurva[0][1]), kurva[0]]), ("kurva", kurva),
                ("linje", [kurva[-1], (r_fot, z_fot - h_fot), (0.0, z_fot - h_fot), (0.0, kurva[0][1])]))
    namn = f"{t.tillverkare} {t.namn}"
    return [("ROR", Del(f"{namn} rör Ø8", cylinder(4.0, f - 12.0, (0.0, 0.0, -(f - 12.0))), MASSING)),
            ("RING", Del(f"{namn} ring Ø13", cylinder(6.5, 5.0, (0.0, 0.0, -(f - 7.0))), MASSING)),
            ("KRAGE", Del(f"{namn} krage Ø{2 * r_krage:.0f}", cylinder(r_krage, 7.0, (0.0, 0.0, -f)), MASSING)),
            ("LINS", Del(f"{namn} opalglas Ø{d:.0f}", glas, OPALGLAS))]


def _glob(t: Armaturtyp, pe: Pendel) -> list[tuple[str, Del]]:
    """Glob: fästet (en kåpa) och ett klot av opalglas under det."""
    f = pe.hojd - pe.diameter
    r = pe.diameter / 2
    kurva = [(r * math.sin(math.pi * i / 32), -f - r + r * math.cos(math.pi * i / 32)) for i in range(33)]
    namn = f"{t.tillverkare} {t.namn}"
    return [("KAPA", Del(f"{namn} kåpa", cylinder(38.0, f + 5.0, (0.0, 0.0, -f - 5.0)),
                         MASSING if pe.takkopp_massing else ARMATUR)),
            ("LINS", Del(f"{namn} opalglas Ø{pe.diameter:.0f}",
                         varv(("kurva", kurva), ("linje", [kurva[-1], kurva[0]])), OPALGLAS))]


def _stav(t: Armaturtyp, pe: Pendel) -> list[tuple[str, Del]]:
    """Stav: en stav Ø6 och ett rör Ø30 av råmässing; ljuskällan i rörets botten bakom en lins, 15 mm in."""
    h, r = pe.hojd, pe.diameter / 2
    namn = f"{t.tillverkare} {t.namn}"
    ror = varv(("linje", [(0.0, -111.0), (r, -111.0), (r, -h), (r - 2.5, -h), (r - 2.5, -h + 15.0), (0.0, -h + 15.0),
                          (0.0, -111.0)]))
    return [("STAV", Del(f"{namn} stav Ø6", cylinder(3.0, 111.0, (0.0, 0.0, -111.0)), RAMASSING)),
            ("ROR", Del(f"{namn} rör Ø{2 * r:.0f}", ror, RAMASSING)),
            ("LINS", Del(f"{namn} lins Ø24", cylinder(12.0, 1.0, (0.0, 0.0, -h + 14.0)), ARMATURLINS))]


_FORMER = {"ph5": _ph5, "vl45": _vl45, "glob": _glob, "stav": _stav}


def _pendel(p: Lampa) -> Montage:
    """Pendeln: takkoppen på takytan, sladden lodrätt ned från takkoppens mitt och armaturen under den."""
    t, pe = p.typ, p.typ.pendel
    assert pe is not None
    m = Montage(p.id, beskrivning=f"{t.tillverkare} {t.namn}", produkt=t.produkt or None)
    d, h = pe.takkopp
    m.lagg(Del(f"Takkopp Ø{d:g}", cylinder(d / 2, h), MASSING if pe.takkopp_massing else ARMATUR), _system(p.lage),
           f"{p.id}-TAKKOPP")
    kopp, topp = pendeln(p)
    if pe.arm:
        m.lagg(Del(f"Arm mässing Ø10 L={pe.arm:.0f}", stang(kopp, topp, 10.0), MASSING), Placering(), f"{p.id}-ARM")
    else:
        sladd = kopp[2] - topp[2]
        m.lagg(Del(f"Textilsladd Ø6 L={sladd:.0f}", cylinder(3.0, sladd),
                   SLADD_SVART if pe.sladd == "svart" else SLADD_VIT), Placering.flytt(*topp), f"{p.id}-SLADD")
    sys = Placering.flytt(*topp)
    for namn, del_ in _FORMER[pe.form](t, pe):
        pl = _ph5_stag(int(namn[-1]) - 1, pe.hojd / _PH5_HOJD) if namn.startswith("STAG") else Placering()
        m.lagg(del_, sys @ pl, f"{p.id}-{namn}")
    return m


def armatur(p: Lampa) -> Montage:
    """Armaturen: frontringen på takytan, huset i håltagningen och spoten vriden så att ljuset går i lampans
    riktning; drivdonet på gipsen bredvid huset."""
    t = p.typ
    if t.pendel is not None:
        return _pendel(p)
    if t.huvud is not None:
        return _tubspot(p)
    if t.panel is not None:
        return _panelen(p)
    if t.linje is not None:
        return _linjearmatur(p)
    d = _delar_armatur(t)
    sys = _system(p.lage)
    m = Montage(p.id, beskrivning=f"{t.tillverkare} {t.namn}", produkt=t.produkt or None)
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


def _linjearmatur(p: Lampa) -> Montage:
    """Ljuslinjen utanpå betongtaket: profilen i ask (fasade undre långkanter, längs x så att fibrerna går längs den)
    med spåret underifrån, som slutar ande från ändarna, aluminiumkanalen i spåret, LED-listen i kanalens botten och
    den opala diffusorn i kanalen (lins: den lyser i renderingen); systemets origo i profilens mitt på takytan, x längs
    profilen och z in i rummet."""
    t = p.typ
    pr = t.linje
    assert pr is not None
    lg, b, h, f, e = t.langd, pr.bredd, pr.hojd, pr.fas, pr.ande
    sb, sd = pr.spar
    db, dt, di = pr.diffusor
    lys = t.lysande_langd
    snitt = [(-b / 2, 0.0), (b / 2, 0.0), (b / 2, h - f), (b / 2 - f, h), (-b / 2 + f, h), (-b / 2, h - f)]
    n = len(snitt)
    horn = [(-lg / 2, y, z) for y, z in snitt] + [(lg / 2, y, z) for y, z in snitt]
    ytor = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))] + [(i, (i + 1) % n, n + (i + 1) % n, n + i)
                                                                     for i in range(n)]
    kropp = polyeder(horn, ytor) - box(-lg / 2 + e, lg / 2 - e, -sb / 2, sb / 2, h - sd, h + 1.0)
    g = pr.gods
    kanal = (box(-lys / 2, lys / 2, -sb / 2, sb / 2, h - sd, h)
             - box(-lys / 2 - 1.0, lys / 2 + 1.0, -sb / 2 + g, sb / 2 - g, h - sd + g, h + 1.0))
    namn = f"{t.namn}"
    m = Montage(p.id, beskrivning=f"{t.tillverkare}: {t.namn}", produkt=t.produkt or None)
    sys = Placering.axlar(p.lage.punkt, p.langs, p.lage.normal)
    m.lagg(Del(f"Askprofil {b:g} × {h:g}, L={lg:.0f}", kropp, ASK), sys, f"{p.id}-PROFIL")
    m.lagg(Del(f"{pr.kanal_namn}, L={lys:.0f}", kanal, LEDKANAL_ALU, produkt=pr.kanal_produkt or None), sys,
           f"{p.id}-KANAL")
    m.lagg(Del(f"{pr.list_namn}, L={lys:.0f}", box(-lys / 2, lys / 2, -pr.list_bredd / 2, pr.list_bredd / 2,
                                                    h - sd + g, h - sd + g + 0.4), LEDLIST,
               produkt=pr.list_produkt or None), sys, f"{p.id}-LIST")
    m.lagg(Del(f"{namn}, diffusor {db:g} mm", box(-lys / 2, lys / 2, -db / 2, db / 2, h - di - dt, h - di),
               ARMATURLINS), sys, f"{p.id}-LINS")
    return m


def _panelen(p: Lampa) -> Montage:
    """Utanpåliggande panel: ramen under taket (ihålig, med bakstycket mot taket, så att renderingens ljuskälla bakom
    linsen lyser ut), den lysande ytan i undersidan och den ingjutna dosan ovanför, där panelen ansluts."""
    t = p.typ
    assert t.panel is not None
    lgd, b, h = t.panel
    sys = _system(p.lage)
    m = Montage(p.id, beskrivning=f"{t.tillverkare} {t.namn}", produkt=t.produkt or None)
    ly = t.lysande_d / 2
    ram = box(-lgd / 2, lgd / 2, -b / 2, b / 2, 0.0, h - 2.0) - box(-ly, ly, -ly, ly, 2.0, h)   # öppen mot linsen
    m.lagg(Del(f"{t.namn} med ram", ram, ARMATUR), sys, f"{p.id}-RAM")
    m.lagg(Del(f"{t.namn}, lysande yta", box(-ly, ly, -ly, ly, h - 2.0, h), ARMATURLINS), sys, f"{p.id}-LINS")
    if t.dosa is not None:
        m.lagg(_ingjuten(t.dosa), sys, f"{p.id}-DOSA")
    return m


def _ingjuten(d: Dosatyp) -> Del:
    """Den ingjutna dosan ovanför en utanpåliggande armatur på betong, där armaturen ansluts."""
    return Del(f"{d.namn} Ø{d.diameter:g} × {d.djup:g}", cylinder(d.diameter / 2, d.djup, (0.0, 0.0, -d.djup)), ELDOSA)


UTAN_GEOMETRI = ("central", "brandlarm", "drivdonsskap")    # punkter vars geometri finns i ett annat montage
#                                                             (teknikrummet, brandlarmet)


def _dosa_del(t: Dosatyp) -> Del:
    return Del(f"{t.namn} Ø{t.diameter:g}", cylinder(t.diameter / 2, t.djup, (0.0, 0.0, -t.djup)), ELDOSA)


def _apparat_delar(t: Apparattyp, produkt: str | None = None) -> list[tuple[str, Del, Placering]]:
    """Täckramen och uttagen eller vipporna; produkt: varje vippa är en produkt (flera dimrar i en ram)."""
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
                                                                   h / 2 - 10.0, 0.0, 3.0), APPARAT, produkt=produkt),
                       Placering.flytt(x, 0.0, 9.0)))
    return ut


def apparat(p: Apparat) -> Montage:
    sys = _system(p.lage)
    per_vippa = p.typ.slag == "dimmer" and p.typ.kanaler > 1     # dimrarna i en flerfacksram: en produkt var
    m = Montage(p.id, beskrivning=p.typ.namn, produkt=None if per_vippa else (p.typ.produkt or None))
    m.lagg(_dosa_del(p.typ.dosa), sys, f"{p.id}-DOSA")
    for namn, d, pl in _apparat_delar(p.typ, (p.typ.produkt or None) if per_vippa else None):
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
        if isinstance(p, Dosa) and p.typ.slag in UTAN_GEOMETRI:
            continue
        mm = delar.setdefault(inst.modul[p.id], Montage(inst.modul[p.id]))
        mm.lagg(armatur(p) if isinstance(p, Lampa) else apparat(p) if isinstance(p, Apparat) else dosa(p))
    for r in inst.ror.values():
        mm = delar.setdefault(inst.modul[r.id], Montage(inst.modul[r.id]))
        mm.lagg(ror(r.id, inst.vag(r), r.typ.ytterdiameter))
    for mm in delar.values():
        m.lagg(mm)
    return m
