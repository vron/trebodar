"""Golvvärmens geometri ur systemet (system.py): kretsarna (ett rör per krets, svept längs vägen med böjar),
fördelarnas stammar och matarledningarna, ett montage per våning. Delarna kontrolleras inte i modellens krockkontroll
(kontrollregler.UTOM_KONTROLL) och tar inga hål i andra delar; golvvärmen har en egen kontroll
(`./mod golvvarme kontroll`, med krockarna mot huset och de andra installationerna).
"""
from __future__ import annotations

from modellering import Del, Montage, Placering, cylinder, svep

from trebodar.material import FORDELARSTAM, GOLVVARME

from .katalog import GOLVVARMEROR, MATARROR
from .punkter import FIL, Fordelare
from .system import golvvarme

BOJ = 5.0                       # böjradien i rörets diametrar
D_STAM = 32.0                   # fördelarnas stam


def _fordelare(f: Fordelare) -> tuple[Del, Placering]:
    """Fördelarens stam (vågrät) från utgång 0 till utgången efter den sista."""
    lgd = (max(f.filer) + 2) * FIL
    return (Del(f.typ.namn, cylinder(D_STAM / 2, lgd), FORDELARSTAM),
            Placering.axlar(f.utgang(0), (0.0, 0.0, 1.0), f.riktning))


def montage() -> Montage:
    g = golvvarme()
    m = Montage("Golvvärme", beskrivning="Golvvärme i plan 1:s mellanbjälklag och bottenplattan, från fördelarna på V5 "
                                         "i källaren (hus/installationer/golvvarme)")
    delar = {1: Montage("Plan 1", beskrivning="Kretsarna i mellanbjälklaget"),
             0: Montage("Källare", beskrivning="Kretsarna i bottenplattan"),
             -1: Montage("Fördelare", beskrivning="Fördelarna på V5 och matarledningarna från värmepumpen")}
    for k in g.kretsar.values():
        delar[k.plan].lagg(Del(f"Golvvärme {k.zon.namn} ({GOLVVARMEROR.matt}, {k.langd:.0f} m)",
                               svep(k.vag, GOLVVARMEROR.d / 2, BOJ * GOLVVARMEROR.d), GOLVVARME), Placering(), k.id)
    for f in g.fordelare.values():
        delar[-1].lagg(*_fordelare(f), f.id)
    for namn, vag in g.matare.items():
        delar[-1].lagg(Del(f"Matarledning {MATARROR.matt}", svep(vag, MATARROR.d / 2, BOJ * MATARROR.d), GOLVVARME),
                       Placering(), namn)
    for d in delar.values():
        m.lagg(d)
    return m
