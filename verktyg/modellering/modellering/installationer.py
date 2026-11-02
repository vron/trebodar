"""Gemensamt för installationernas kommandon (`mod ventilation`, `mod vatten`, `mod golvvarme`): krockarna mellan en
installations delar och husets delar och de andra installationerna med egen kontroll (kontrollregler.INSTALLATIONER).

Installationerna är undantagna från modellens krockkontroll (kontrollregler.UTOM_KONTROLL): de går genom skikten utan
håltagning. Här prövas en installation för sig: stommens delar (virke, limträ, stål), armeringsjärnen och andra
installationers delar redovisas var för sig, genomföringarna i skikten (gips, isolering, betong) summerade per rör eller
kanal. Rör som gjuts in ska gå fria från järnen; kanaler genom ursparingar får armeringen omlagd runt sig.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from types import ModuleType

from . import kontroll
from .karna import Karna
from .modell import Montage

STOMME = ("C24", "Läkt", "GL30h", "GL30c", "S355", "S235", "Spikplåt")
ARMERING = "Armering"
INSTALLATIONER = "Hus/Installationer/"


@dataclass
class Krockar:
    stomme: list[str] = field(default_factory=list)         # mot stommens delar, var för sig
    armering: list[str] = field(default_factory=list)       # mot armeringsjärnen, var för sig
    installationer: list[str] = field(default_factory=list)  # mot andra installationer och teknikrummet (fel)
    skikt: list[str] = field(default_factory=list)          # genom skikten, per rör eller kanal

    @property
    def alla(self) -> list[str]:
        return [f"KROCK {k}" for k in self.installationer] + self.stomme + self.armering + self.skikt


def krockar(rot: Montage, karna: Karna, regler: ModuleType | None, trad: str) -> Krockar:
    """Installationens delar (delträdet trad, t.ex. "Hus/Installationer/Vatten") mot husets delar och de andra
    installationerna; installationens egna delar prövas inte mot varandra (installationens egen kontroll)."""
    andra = getattr(regler, "INSTALLATIONER", ())
    utom = {k: m for k, m in getattr(regler, "UTOM_KONTROLL", {}).items() if k != trad and k not in andra}
    r = kontroll.kor(rot, karna, ignorerade=getattr(regler, "IGNORERADE", None), utom=utom, bara=trad)
    delar = {v: d for v, d, _ in rot.platta()}
    ut = Krockar()
    skikt: dict[str, dict[str, int]] = {}
    for ka, kb, vol in r.krockar + [(x, y, v) for x, y, v, _ in r.tillatna]:
        if trad in ka and trad in kb:
            continue
        egen, annan = (ka, kb) if trad in ka else (kb, ka)
        mat = delar[annan].material.namn
        namn = egen.split("/")[-1]
        text = f"{namn} mot {mat} {annan.split('/', 2)[-1]} ({vol / 1000:.0f} cm³)"
        if INSTALLATIONER in annan:
            ut.installationer.append(text)
        elif mat in STOMME:
            ut.stomme.append(text)
        elif mat == ARMERING:
            ut.armering.append(text)
        else:
            element = namn.rsplit("-", 1)[0] if namn.count("-") > 1 else namn
            skikt.setdefault(element, {})[mat] = skikt.setdefault(element, {}).get(mat, 0) + 1
    ut.skikt = [f"{e}: genom " + ", ".join(f"{m} {n}" for m, n in sorted(ms.items()))
                for e, ms in sorted(skikt.items())]
    return ut
