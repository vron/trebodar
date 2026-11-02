"""Hela elinstallationen ur modulerna (ett rum eller ett bjälklag per modul): punkterna, tändgrupperna och rören med
deras lägen i husets koordinater, kontrollen av installationen och utdrag för ritningarna och renderingen.

Varje modul har NAMN (montaget i modellen) och några av RUM, TANDGRUPPER, PUNKTER och ROR. Ny modul: lägg till den
i MODULER.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from functools import cache
from types import ModuleType

from trebodar.hus.invandigt.skikt import LAKT

from . import lakt
from .bjalklag import mellanbjalklag
from .punkter import PLAN, TAKSKIVOR, Apparat, Lampa, Punkt, Ror, Rum, Tandgrupp, Vek, anslutning, drivdonet, linsen
from .rum import allrum
from .typer import Armaturtyp

MODULER: tuple[ModuleType, ...] = (allrum, mellanbjalklag)


@dataclass(frozen=True)
class Installation:
    rum: dict[str, Rum]
    punkter: dict[str, Punkt]
    tandgrupper: dict[str, Tandgrupp]
    ror: dict[str, Ror]
    modul: dict[str, str]                      # punktens eller rörets modul (montagets namn)

    def styrs_av(self, tand: str) -> list[str]:
        return [p.id for p in self.punkter.values() if isinstance(p, Apparat) and tand in p.styr]

    def vag(self, r: Ror) -> list[Vek]:
        """Rörets mittlinje: från punktens anslutning genom brytpunkterna till den andra punktens."""
        return [anslutning(self.punkter[r.fran]), *r.via, anslutning(self.punkter[r.till])]

    def kontroll(self) -> tuple[list[str], list[str]]:
        """(fel, anmärkningar): referenser, styrning, armaturernas vinkel och djup, rörens böjar och anslutningar."""
        fel: list[str] = []
        anm: list[str] = []
        for p in self.punkter.values():
            if isinstance(p, Lampa):
                if p.tand not in self.tandgrupper:
                    fel.append(f"{p.id}: tändgruppen {p.tand} finns inte")
                vinkel = _vinkel(p.lage.normal, p.riktning)
                if vinkel > p.typ.vridbar + 0.5:
                    fel.append(f"{p.id}: ljuset ska vridas {vinkel:.0f}°, armaturen tillåter {p.typ.vridbar:.0f}°")
                if p.lage.yta == "tak" and p.lage.ref != "MB":
                    plats = TAKSKIVOR + LAKT
                    if p.typ.djup + p.typ.brandavstand > plats + 1e-6:
                        fel.append(f"{p.id}: {p.typ.djup:g} mm djup + {p.typ.brandavstand:g} mm till brännbart, "
                                   f"innertaket har {plats:g} mm")
                    x, y, _ = p.lage.punkt
                    rad = p.typ.hal_d / 2 + p.typ.brandavstand
                    for q in lakt.krockar(p.lage.ref, x, y, lakt.i_planet(rad), rad):
                        fel.append(f"{p.id}: hålet Ø{p.typ.hal_d:g} (med {p.typ.brandavstand:g} mm till brännbart) "
                                   f"tar i läkten x {q[0]:.0f}–{q[1]:.0f}")
                    if p.typ.drivdon:
                        lg, br, _ = p.typ.drivdon
                        for q in lakt.krockar(p.lage.ref, x, y + drivdonet(p), lakt.i_planet(br / 2), lg / 2):
                            fel.append(f"{p.id}: drivdonet ligger på läkten x {q[0]:.0f}–{q[1]:.0f}")
            if isinstance(p, Apparat):
                for g in p.styr:
                    if g not in self.tandgrupper:
                        fel.append(f"{p.id}: styr tändgruppen {g}, som inte finns")
                if p.styr and len(p.styr) > p.typ.kanaler:
                    fel.append(f"{p.id}: styr {len(p.styr)} tändgrupper, {p.typ.namn} har {p.typ.kanaler} kanaler")
        for tg in self.tandgrupper.values():
            if not any(isinstance(p, Lampa) and p.tand == tg.id for p in self.punkter.values()):
                anm.append(f"{tg.id}: inga lampor")
            if not self.styrs_av(tg.id):
                fel.append(f"{tg.id}: ingen brytare eller dimmer styr tändgruppen")
        anslutna: set[str] = set()
        for ro in self.ror.values():
            for a in (ro.fran, ro.till):
                if a not in self.punkter:
                    fel.append(f"{ro.id}: punkten {a} finns inte")
            if ro.fran in self.punkter and ro.till in self.punkter:
                anslutna |= {ro.fran, ro.till}
                b = bojar(self.vag(ro))
                if b > 270.0 + 1e-6:
                    anm.append(f"{ro.id}: böjarna är {b:.0f}° sammanlagt (mer än 270°: svårt att dra, dosa emellan?)")
        for p in self.punkter.values():
            if p.id not in anslutna:
                anm.append(f"{p.id}: inget rör ansluter till punkten")
        anm.append("matningen: centralen är inte placerad, rören slutar i dosor")
        return fel, anm

    def utdrag(self) -> dict[str, object]:
        """Allt som ritningarna och renderingen behöver, som JSON: rum, typer, punkter, tändgrupper och rör."""
        typer: dict[str, dict[str, object]] = {}
        punkter: dict[str, dict[str, object]] = {}
        for p in self.punkter.values():
            t = p.typ
            typer[t.kod] = {"namn": t.namn, "symbol": t.symbol,
                            **({"slag": "armatur", **_armatur(t)} if isinstance(t, Armaturtyp) else
                               {"slag": t.slag})}
            m = p.lage
            punkter[p.id] = {"slag": "lampa" if isinstance(p, Lampa) else "apparat" if isinstance(p, Apparat)
                             else "dosa", "typ": t.kod, "modul": self.modul[p.id], "punkt": list(m.punkt),
                             "normal": list(m.normal), "yta": m.yta, "ref": m.ref}
            if isinstance(p, Lampa):
                punkter[p.id] |= {"tand": p.tand, "riktning": list(p.riktning), "lins": list(linsen(p))}
            if isinstance(p, Apparat):
                punkter[p.id] |= {"styr": list(p.styr)}
            rum = self.rum.get(p.id.split("-")[0])
            if rum:
                punkter[p.id] |= {"rum": rum.kod, "over_golv": m.punkt[2] - PLAN[rum.plan]}
        return {"rum": {k: {"namn": r.namn, "plan": r.plan} for k, r in self.rum.items()},
                "typer": typer, "punkter": punkter,
                "tandgrupper": {k: {"namn": t.namn, "dimbar": t.dimbar, "styrs_av": self.styrs_av(k),
                                    "lampor": [p.id for p in self.punkter.values()
                                               if isinstance(p, Lampa) and p.tand == k]}
                                for k, t in self.tandgrupper.items()},
                "ror": {k: {"typ": r.typ.kod, "diameter": r.typ.ytterdiameter, "fran": r.fran, "till": r.till,
                            "modul": self.modul[k], "vag": [list(v) for v in self.vag(r)],
                            "langd": langd(self.vag(r)), "bojar": bojar(self.vag(r))}
                        for k, r in self.ror.items()}}


def _armatur(t: Armaturtyp) -> dict[str, object]:
    return {"tillverkare": t.tillverkare, "artikel": t.artikel, "url": t.url, "ljusflode": t.ljusflode,
            "effekt": t.effekt, "fargtemperatur": t.fargtemperatur, "stralvinkel": t.stralvinkel,
            "lysande_d": t.lysande_d, "hal_d": t.hal_d, "fotometri": t.fotometri, "fotometri_url": t.fotometri_url}


def _vinkel(a: Vek, b: Vek) -> float:
    d = sum(x * y for x, y in zip(a, b)) / (math.hypot(*a) * math.hypot(*b))
    return math.degrees(math.acos(max(-1.0, min(1.0, d))))


def langd(vag: list[Vek]) -> float:
    return sum(math.dist(a, b) for a, b in zip(vag, vag[1:]))


def bojar(vag: list[Vek]) -> float:
    """Summan av riktningsändringarna längs röret [°]."""
    s = 0.0
    for a, b, c in zip(vag, vag[1:], vag[2:]):
        u = tuple(y - x for x, y in zip(a, b))
        v = tuple(y - x for x, y in zip(b, c))
        if math.hypot(*u) > 1e-6 and math.hypot(*v) > 1e-6:
            s += _vinkel(u, v)  # type: ignore[arg-type]
    return s


@cache
def installation() -> Installation:
    rum: dict[str, Rum] = {}
    punkter: dict[str, Punkt] = {}
    tandgrupper: dict[str, Tandgrupp] = {}
    ror: dict[str, Ror] = {}
    modul: dict[str, str] = {}
    for m in MODULER:
        if hasattr(m, "RUM"):
            rum[m.RUM.kod] = m.RUM
        for samling, lista in ((tandgrupper, getattr(m, "TANDGRUPPER", [])), (punkter, getattr(m, "PUNKTER", [])),
                               (ror, getattr(m, "ROR", []))):
            for o in lista:
                if o.id in modul:
                    raise ValueError(f"id {o.id} finns två gånger ({m.NAMN})")
                samling[o.id] = o
                modul[o.id] = m.NAMN
    return Installation(rum, punkter, tandgrupper, ror, modul)

