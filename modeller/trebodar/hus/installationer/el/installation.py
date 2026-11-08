"""Hela elinstallationen ur modulerna (ett rum eller ett bjälklag per modul): punkterna, tändgrupperna och rören med
deras lägen i husets koordinater, kontrollen av installationen och utdrag för ritningarna och renderingen.

Varje modul har NAMN (montaget i modellen) och några av RUM, TANDGRUPPER, PUNKTER och ROR. Ny modul: lägg till den
i MODULER.
"""
from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from functools import cache
from types import ModuleType

from modellering import Form

from trebodar.byggdelar.genomforing import Lada
from trebodar.byggdelar.ror import stang
from trebodar.hus.invandigt.skikt import LAKT

from . import kedjor, lakt
from .grupper import GRUPP, GRUPPER, HUVUDBRYTARE, OVERSPANNINGSSKYDD
from .bjalklag import mellanbjalklag
from .bjalklag.ingjutna import korsningar
from shapely.geometry import LineString, Point

from ..montering import KALLARTAK, PLAN, TAKSKIVOR, Vek, enhet, flytt, langs_taket
from ..plattan import bage_punkter
from ..teknikrum import DRIVDON, DRIVDON_I_SKAPET
from .punkter import (SVEP_MAX, Apparat, Dosa, Krets, Lampa, Punkt, Ror, Rum, Tandgrupp, anslutning, bojar, drivdonet,
                      linjen, linsen, pendeln, vinkel)
from .rum import (allrum, badrum, gang, gastrum, hall, kallare, kok, kontor, kontor_litet, sovrum, sovrum_litet,
                  teknikrum, vardagsrum)
from .typer import Apparattyp, Armaturtyp

MODULER: tuple[ModuleType, ...] = (allrum, kok, gang, hall, vardagsrum, badrum, sovrum, kontor, sovrum_litet,
                                   kontor_litet, gastrum, teknikrum, kallare, mellanbjalklag, kedjor)
SLADD_MINST = 50.0                             # pendelns sladd under takkoppen, minst [mm]


SKAP = ("central", "drivdonsskap")          # rören börjar och slutar på skåpets ovansida (i via), inte i en dosa
SPANNINGSFALL = 3.0                          # 24 V-kretsarna: största spänningsfall till en ljuslinje [%]
LEDARE = (1.5, 2.5)                          # 24 V-kablarnas area [mm²], den minsta som räcker
RHO = 0.0183                                 # kopparens resistivitet vid 30 °C [Ω mm²/m]
KABEL_TILLAGG = 300.0                        # kabeln i varje ände utöver röret (i skåpet och i armaturens ficka) [mm]
DRIVDON_LAST = 0.8                           # drivdonens last högst så stor andel av märkeffekten (anmärkning)


@dataclass(frozen=True)
class Kretsresultat:
    """En 24 V-krets uträknad (Installation.kretsresultat)."""
    krets: Krets
    last: float                                # ljuslinjernas effekt [W]
    spanning: float                            # [V]
    area: float                                # ledarnas area [mm²]
    kabel: float                               # kablarnas längd, med genomgången i profilerna [m]
    fall: dict[str, float]                     # spänningsfallet till varje ljuslinje [%]
    fall_max: float                            # [%]
    ror: tuple[str, ...]                       # 24 V-rören från drivdonet

    def utdrag(self) -> dict[str, object]:
        k = self.krets
        return {"id": k.id, "tand": k.tand, "dimmer": k.dimmer, "kanal": k.kanal, "skap": k.skap,
                "drivdon": k.drivdon, "lampor": list(k.lampor), "last": self.last, "spanning": self.spanning,
                "area": self.area, "kabel": self.kabel, "fall": self.fall, "fall_max": self.fall_max,
                "ror": list(self.ror)}


@dataclass(frozen=True)
class Installation:
    rum: dict[str, Rum]
    punkter: dict[str, Punkt]
    tandgrupper: dict[str, Tandgrupp]
    ror: dict[str, Ror]
    modul: dict[str, str]                      # punktens eller rörets modul (montagets namn)
    kretsar: dict[str, Krets]

    def styrs_av(self, tand: str) -> list[str]:
        return [p.id for p in self.punkter.values() if isinstance(p, Apparat) and tand in p.styr]

    def _med_radier(self, r: Ror) -> list[tuple[Vek, float]]:
        """Rörets brytpunkter med böjarnas radier (0: rörtypens minsta): från punktens anslutning (en ljuslinjes
        rörände i dess andra ände, mot nästa) genom brytpunkterna till den andra punktens, i innertakets
        installationsskikt över nocken och dalarna (montering.langs_taket); vid centralen och drivdonsskåpet börjar och
        slutar röret på skåpets ovansida, och i en ingjuten dosa där det går in i dosan från sidan."""
        fran, till = self.punkter[r.fran], self.punkter[r.till]
        rad = list(r.radier) + [0.0] * (len(r.via) - len(r.radier))
        p: list[tuple[Vek, float]] = list(zip(r.via, rad))
        if not (isinstance(fran, Dosa) and fran.typ.slag in SKAP and r.via) and not _i_dosan(fran, r.via[:1]):
            p.insert(0, (anslutning(fran, ut=True), 0.0))
        if not (isinstance(till, Dosa) and till.typ.slag in SKAP and r.via) and not _i_dosan(till, r.via[-1:]):
            p.append((anslutning(till), 0.0))
        ut = [p[0]]
        for (a, _), (b, rb) in zip(p, p[1:]):
            mellan = langs_taket(a, b)[1:]
            ut += [(q, 0.0) for q in mellan[:-1]] + [(mellan[-1], rb)]
        return ut

    def vag(self, r: Ror) -> list[Vek]:
        """Rörets brytpunkter (_med_radier)."""
        return [q for q, _ in self._med_radier(r)]

    def radier(self, r: Ror) -> list[float]:
        """Böjarnas radier i rörets brytpunkter (vag), 0 där röret har rörtypens minsta."""
        return [rr for _, rr in self._med_radier(r)]

    def mittlinje(self, r: Ror) -> list[Vek]:
        """Rörets mittlinje med de mjuka böjarna i plan rundade (bågar ur punkter)."""
        p = self._med_radier(r)
        ut: list[Vek] = [p[0][0]]
        for (a, _), (b, rb), (c, _) in zip(p, p[1:], p[2:]):
            if rb > 0.0 and abs(a[2] - b[2]) < 0.5 and abs(b[2] - c[2]) < 0.5:
                ut += [(x, y, b[2]) for x, y in bage_punkter(a[:2], b[:2], c[:2], rb)]
            else:
                ut.append(b)
        return [*ut, p[-1][0]] if len(p) > 1 else ut

    def kretsresultat(self) -> list[Kretsresultat]:
        """24 V-kretsarna: lasten, drivdonet, rören från drivdonet (ett träd: från skåpet till en ljuslinjes rörände,
        och från en ljuslinjes andra ände till nästa, med ledaren genom profilen emellan), ledarnas area (den minsta i
        LEDARE som ger högst SPANNINGSFALL till varje ljuslinje), kabelns längd och spänningsfallet till den sista."""
        ut: list[Kretsresultat] = []
        for k in self.kretsar.values():
            lampor = [p for q in k.lampor if isinstance(p := self.punkter.get(q), Lampa)]
            effekt = {p.id: p.typ.effekt for p in lampor}
            u = lampor[0].typ.linje.spanning if lampor and lampor[0].typ.linje else 24.0
            barn: dict[str, list[tuple[str, Ror]]] = {}
            for r in self.ror.values():
                if r.slag == "24 V" and r.till in effekt and (r.fran == k.skap or r.fran in effekt):
                    barn.setdefault(r.fran, []).append((r.till, r))

            def nedstroms(q: str) -> float:
                return effekt[q] + sum(nedstroms(c) for c, _ in barn.get(q, []))

            def fall(area: float) -> tuple[dict[str, float], float]:
                """Spänningsfallet till varje ljuslinje [V] och kablarnas längd [m]."""
                du: dict[str, float] = {}
                total = 0.0
                kvar = [(k.skap, 0.0)]
                while kvar:
                    q, d0 = kvar.pop()
                    for c, r in barn.get(q, []):
                        lgd = (langd(self.vag(r)) + 2 * KABEL_TILLAGG) / 1000.0
                        genom = 0.0
                        if q != k.skap:                    # genom profilen från rörändan i matningens ände
                            p = self.punkter[q]
                            assert isinstance(p, Lampa) and p.typ.linje is not None
                            genom = (p.typ.langd - 2 * p.typ.linje.ror_in) / 1000.0
                        i = nedstroms(c) / u
                        d = d0 + 2 * RHO * (lgd + genom) * i / area
                        total += lgd + genom
                        du[c] = d
                        kvar.append((c, d))
                return du, total
            val = None
            for area in LEDARE:
                du, total = fall(area)
                val = (area, du, total)
                if du and max(du.values()) / u * 100.0 <= SPANNINGSFALL:
                    break
            assert val is not None
            area, du, total = val
            ut.append(Kretsresultat(k, sum(effekt.values()), u, area, total,
                                    {q: d / u * 100.0 for q, d in du.items()},
                                    max(du.values()) / u * 100.0 if du else 0.0,
                                    tuple(sorted(r.id for v in barn.values() for _, r in v))))
        return ut

    def kontroll(self) -> tuple[list[str], list[str]]:
        """(fel, anmärkningar): referenser, styrning, armaturernas vinkel, djup och hål i innertakets gips (pendlarna:
        sladden räcker ned från takkoppen), rörens böjar och anslutningar."""
        fel: list[str] = []
        anm: list[str] = []
        for p in self.punkter.values():
            if isinstance(p, Lampa):
                if p.tand not in self.tandgrupper:
                    fel.append(f"{p.id}: tändgruppen {p.tand} finns inte")
                if p.typ.pendel is not None:
                    if p.typ.pendel.arm:
                        continue
                    if p.underkant is None:
                        fel.append(f"{p.id}: pendeln har ingen underkant")
                    elif (sladd := pendeln(p)[0][2] - pendeln(p)[1][2]) < SLADD_MINST:
                        fel.append(f"{p.id}: pendeln når inte ned, sladden blir {sladd:.0f} mm")
                    continue
                vriden = vinkel(p.lage.normal, p.riktning)
                if vriden > p.typ.vridbar + 0.5:
                    fel.append(f"{p.id}: ljuset ska vridas {vriden:.0f}°, armaturen tillåter {p.typ.vridbar:.0f}°")
                if p.lage.yta == "tak" and p.lage.ref != "MB":
                    plats = TAKSKIVOR + LAKT
                    x, y, _ = p.lage.punkt
                    if p.typ.djup > plats + 1e-6:
                        fel.append(f"{p.id}: {p.typ.djup:g} mm djup, innertaket har {plats:g} mm")
                    if not p.typ.isoleras and p.typ.min_djup > plats + 1e-6:
                        fel.append(f"{p.id}: får inte täckas med isolering och behöver {p.typ.min_djup:g} mm fritt "
                                   f"från takytan, innertaket har {plats:g} mm")
                    if not p.typ.isoleras and p.typ.min_volym > 0:
                        f = lakt.facket(p.lage.ref, x, y)
                        v = lakt.volym(f) if f else 0.0
                        if v < p.typ.min_volym:
                            fel.append(f"{p.id}: får inte täckas med isolering och behöver {p.typ.min_volym:g} l luft "
                                       f"runt sig, läktens fack har {v:.1f} l")
                    if not lakt.i_gipsen(p.lage.ref, x, y, p.typ.hal_d / 2):
                        fel.append(f"{p.id}: hålet Ø{p.typ.hal_d:g} ligger inte i innertakets gips (ett takfönsters "
                                   f"öppning eller innertakets kant)")
                    rad = p.typ.hal_d / 2
                    for q in lakt.krockar(p.lage.ref, x, y, lakt.i_planet(rad), rad):
                        fel.append(f"{p.id}: hålet Ø{p.typ.hal_d:g} tar i läkten x {q[0]:.0f}–{q[1]:.0f}")
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
                b = bojar(self.vag(ro), self.radier(ro))
                sv = bojar(self.vag(ro), self.radier(ro), svep=True)
                if b > 270.0 + 1e-6:
                    anm.append(f"{ro.id}: böjarna är {b:.0f}° sammanlagt (mer än 270°: svårt att dra, dosa emellan?)"
                               + (f", och svepen i plattan {sv:.0f}°" if sv > 0.5 else ""))
                elif sv > SVEP_MAX + 1e-6:
                    anm.append(f"{ro.id}: svepen i plattan är {sv:.0f}° sammanlagt (mer än {SVEP_MAX:.0f}°: långt att "
                               f"dra, och böjarna {b:.0f}°)")
        for p in self.punkter.values():
            if p.id not in anslutna:
                anm.append(f"{p.id}: inget rör ansluter till punkten")
        g_fel, g_anm = self._grupperna()
        k_fel, k_anm = self._kretsarna()
        return fel + g_fel + k_fel + self._i_bjalklaget(), anm + g_anm + k_anm

    def _kretsarna(self) -> tuple[list[str], list[str]]:
        """Ljuslinjerna och 24 V-kretsarna: varje ljuslinje i en krets och nådd med 24 V-rör från drivdonet,
        drivdonet i skåpet och lasten inom dess område, dimmerns kanal styr tändgruppen och har ett eget rör med den
        dimrade fasen till skåpet, dimmerns last inom dess område, rörens ändar under profilen och spänningsfallet."""
        fel: list[str] = []
        anm: list[str] = []
        i_krets: dict[str, list[str]] = {}
        for k in self.kretsar.values():
            for q in k.lampor:
                i_krets.setdefault(q, []).append(k.id)
        for p in self.punkter.values():
            if isinstance(p, Lampa) and p.typ.linje is not None and len(i_krets.get(p.id, [])) != 1:
                fel.append(f"{p.id}: i {len(i_krets.get(p.id, []))} 24 V-kretsar")
        platser = len(DRIVDON_I_SKAPET)
        drivdon = [k.drivdon for k in self.kretsar.values()]
        if len(set(drivdon)) != len(drivdon) or any(not 0 <= d < platser for d in drivdon):
            fel.append(f"24 V-kretsarna: drivdonen {drivdon}, skåpet har {platser} drivdon")
        if len(drivdon) != platser:
            fel.append(f"24 V-kretsarna: {len(drivdon)} kretsar men {platser} drivdon i skåpet")
        dimmerlast: dict[str, float] = {}
        for r in self.kretsresultat():
            k = r.krets
            for lid in k.lampor:
                lampa = self.punkter.get(lid)
                if not isinstance(lampa, Lampa) or lampa.typ.linje is None:
                    fel.append(f"{k.id}: {lid} är inte en ljuslinje")
                elif lampa.tand != k.tand:
                    fel.append(f"{k.id}: {lid} hör till tändgruppen {lampa.tand}, kretsen till {k.tand}")
                elif lid not in r.fall:
                    fel.append(f"{k.id}: inget 24 V-rör från drivdonet till {lid}")
            dimmer = self.punkter.get(k.dimmer)
            if not isinstance(dimmer, Apparat) or dimmer.typ.slag != "dimmer" or k.kanal >= len(dimmer.styr) \
                    or dimmer.styr[k.kanal] != k.tand:
                fel.append(f"{k.id}: {k.dimmer} kanal {k.kanal + 1} styr inte {k.tand}")
            elif not any(ro.slag == "230 V dimrad" and ro.fran == k.dimmer and ro.till == k.skap
                         for ro in self.ror.values()):
                fel.append(f"{k.id}: inget rör med den dimrade fasen från {k.dimmer} till {k.skap}")
            if not DRIVDON.minsta <= r.last <= DRIVDON.storsta:
                fel.append(f"{k.id}: {r.last:.1f} W, drivdonet {DRIVDON.namn} tar "
                           f"{DRIVDON.minsta:g}–{DRIVDON.storsta:g} W")
            elif r.last > DRIVDON_LAST * DRIVDON.storsta:
                anm.append(f"{k.id}: {r.last:.1f} W, mer än {DRIVDON_LAST:.0%} av drivdonets {DRIVDON.storsta:g} W")
            dimmerlast[k.dimmer] = dimmerlast.get(k.dimmer, 0.0) + r.last / DRIVDON.verkningsgrad
            if r.fall_max > SPANNINGSFALL:
                fel.append(f"{k.id}: spänningsfallet {r.fall_max:.1f} % med {LEDARE[-1]:g} mm² "
                           f"(högst {SPANNINGSFALL:g} %)")
        for did, w in dimmerlast.items():
            d = self.punkter[did]
            assert isinstance(d, Apparat)
            kanaler = sum(1 for k in self.kretsar.values() if k.dimmer == did)
            if d.typ.storsta_last and w / max(kanaler, 1) > d.typ.storsta_last:
                fel.append(f"{did}: {w:.0f} W på {kanaler} kanaler, dimmern tar {d.typ.storsta_last:g} W per kanal")
            if w / max(kanaler, 1) < d.typ.minsta_last:
                fel.append(f"{did}: {w:.1f} W, dimmern behöver minst {d.typ.minsta_last:g} W")
        # rörens ändar i taket under ljuslinjens profil (de täcks helt av armaturen)
        for ro in self.ror.values():
            for pid, ande in ((ro.fran, self.vag(ro)[0]), (ro.till, self.vag(ro)[-1])):
                lampa = self.punkter.get(pid)
                if isinstance(lampa, Lampa) and lampa.typ.linje is not None:
                    mitt, u = lampa.lage.punkt, enhet(lampa.langs)
                    dx, dy = ande[0] - mitt[0], ande[1] - mitt[1]
                    if (abs(dx * u[0] + dy * u[1]) > lampa.typ.langd / 2 - 10.0
                            or abs(-dx * u[1] + dy * u[0]) > lampa.typ.linje.bredd / 2 - 10.0
                            or abs(ande[2] - mitt[2]) > 1.0):
                        fel.append(f"{ro.id}: röret slutar inte i taket under {pid}:s profil")
        return fel, anm

    def _i_bjalklaget(self) -> list[str]:
        """Rören i mellanbjälklaget som går i varandra (mittlinjerna närmare än radierna, utom där två rör möts i
        samma punkt) eller genom en armaturs ingjutna dosa."""
        bitar = [(r.id, r.fran, r.till, a, b, r.typ.ytterdiameter / 2) for r in self.ror.values()
                 for a, b in zip(self.mittlinje(r), self.mittlinje(r)[1:])
                 if max(a[2], b[2]) > KALLARTAK + 1.0 and min(a[2], b[2]) < PLAN[1] - 1.0]
        dosor = [(p.id, p.lage.punkt, p.typ.dosa.diameter / 2) for p in self.punkter.values()
                 if isinstance(p, Lampa) and p.typ.dosa is not None]
        ut: set[str] = set()
        for i, (ra, fa, ta, a0, a1, rad_a) in enumerate(bitar):
            for rb, fb, tb, b0, b1, rad_b in bitar[i + 1:]:
                if ra == rb or (max(a0[0], a1[0]) + 60.0 < min(b0[0], b1[0]) or max(b0[0], b1[0]) + 60.0 < min(a0[0], a1[0])
                                or max(a0[1], a1[1]) + 60.0 < min(b0[1], b1[1])
                                or max(b0[1], b1[1]) + 60.0 < min(a0[1], a1[1])):
                    continue
                d, q = avstand(a0, a1, b0, b1)
                gemensam = {fa, ta} & {fb, tb}
                if d < rad_a + rad_b - 0.5 and not any(math.dist(q[:2], anslutning(self.punkter[g])[:2]) < 150.0
                                                       for g in gemensam):
                    ut.add(f"{ra} och {rb} går i varandra i bjälklaget ({d:.0f} mm mellan mittlinjerna)")
            for pid, c, r in dosor:
                if pid in (fa, ta):
                    continue
                d = Point(c[0], c[1]).distance(LineString([a0[:2], a1[:2]]) if math.dist(a0[:2], a1[:2]) > 0.5
                                               else Point(a0[0], a0[1]))
                if d < r + rad_a and min(a0[2], a1[2]) < c[2] + 70.0:
                    ut.add(f"{ra} går genom {pid}:s ingjutna dosa ({d:.0f} mm från dess mitt)")
        return sorted(ut)

    def _grupperna(self) -> tuple[list[str], list[str]]:
        """Grupperna (grupper.py): varje apparat och dosa utom lamporna och centralen i en grupp, gruppens punkter
        hopkopplade med rör från centralen, gruppens rör från centralen till dess första punkt, och belastningen."""
        fel: list[str] = []
        anm: list[str] = []
        i_grupp: dict[str, list[str]] = {}
        for g in GRUPPER:
            for pid in g.punkter:
                i_grupp.setdefault(pid, []).append(g.id)
                if pid not in self.punkter:
                    fel.append(f"{g.id}: punkten {pid} finns inte")
        for p in self.punkter.values():
            if isinstance(p, Lampa) or (isinstance(p, Dosa) and p.typ.slag == "central"):
                continue
            if isinstance(p, Dosa) and p.typ.slag in ("ingjutningsdosa", "kopplingsdosa") and p.id not in i_grupp:
                continue
            n = len(i_grupp.get(p.id, []))
            if n != 1:
                fel.append(f"{p.id}: i {n} grupper" + (f" ({', '.join(i_grupp[p.id])})" if n else ""))
        central = next((p.id for p in self.punkter.values() if isinstance(p, Dosa) and p.typ.slag == "central"), None)
        # dragdosorna och kopplingsdosorna utanför grupperna: gruppens rör går genom dem
        fria = {p.id for p in self.punkter.values() if isinstance(p, Dosa) and p.id not in i_grupp
                and p.typ.slag in ("ingjutningsdosa", "kopplingsdosa")}
        if central is None:
            return fel + ["centralen saknas"], anm
        grannar: dict[str, set[str]] = {}
        for r in self.ror.values():
            grannar.setdefault(r.fran, set()).add(r.till)
            grannar.setdefault(r.till, set()).add(r.fran)
        for g in GRUPPER:
            if not g.punkter or g.punkter[0] not in grannar.get(central, set()):
                fel.append(f"{g.id}: inget rör från centralen till gruppens första punkt {g.punkter[0]}")
            # gruppens punkter nås från den första genom gruppens egna punkter (förgrenat i dosorna)
            egna, nadda, kvar = set(g.punkter) | fria, {g.punkter[0]}, [g.punkter[0]]
            while kvar:
                for q in grannar.get(kvar.pop(), set()) & egna:
                    if q not in nadda:
                        nadda.add(q)
                        kvar.append(q)
            for pid in g.punkter:
                if pid not in nadda:
                    fel.append(f"{g.id}: {pid} har inget rör från gruppens andra punkter")
            appar = [self.punkter[pid] for pid in g.punkter if isinstance(self.punkter.get(pid), Apparat)]
            uttag = sum(a.typ.kanaler for a in appar if isinstance(a, Apparat) and a.typ.slag == "uttag")
            if g.sakring == 10 and g.faser == 1 and uttag > 10:
                anm.append(f"{g.id}: {uttag} uttag på 10 A")
        return fel, anm

    def utdrag(self) -> dict[str, object]:
        """Allt som ritningarna och renderingen behöver, som JSON: rum, typer, punkter, tändgrupper, rör (mittlinjen
        med de mjuka böjarna i plattan rundade, brytpunkterna och deras radier, böjarna och svepen, 24 V-rörens ledare
        ur kretsarna) och 24 V-kretsarna."""
        kretsar = self.kretsresultat()
        ledare = {rid: k.area for k in kretsar for rid in k.ror}
        typer: dict[str, dict[str, object]] = {}
        punkter: dict[str, dict[str, object]] = {}
        for p in self.punkter.values():
            t = p.typ
            typer[t.kod] = {"namn": t.namn, "symbol": t.symbol,
                            **({"slag": "armatur", **_armatur(t)} if isinstance(t, Armaturtyp) else
                               {"slag": t.slag, "kanaler": t.kanaler} if isinstance(t, Apparattyp) else
                               {"slag": t.slag, "diameter": t.diameter, "djup": t.djup})}
            m = p.lage
            punkter[p.id] = {"slag": "lampa" if isinstance(p, Lampa) else "apparat" if isinstance(p, Apparat)
                             else "dosa", "typ": t.kod, "modul": self.modul[p.id], "punkt": list(m.punkt),
                             "normal": list(m.normal), "yta": m.yta, "ref": m.ref}
            if isinstance(p, Lampa):
                punkter[p.id] |= {"tand": p.tand, "riktning": list(p.riktning), "lins": list(linsen(p))}
                if p.typ.pendel is not None:
                    punkter[p.id] |= {"underkant": p.underkant, "topp": list(pendeln(p)[1])}
                if p.typ.linje is not None:
                    a, b = linjen(p)
                    punkter[p.id] |= {"linje": {"a": list(a), "b": list(b), "langs": list(enhet(p.langs)),
                                                "ror_in": list(anslutning(p)), "ror_ut": list(anslutning(p, ut=True))}}
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
                            "modul": self.modul[k], "vag": [list(v) for v in self.mittlinje(r)],
                            "brytpunkter": [list(v) for v in self.vag(r)], "radier": self.radier(r),
                            "langd": langd(self.mittlinje(r)), "bojar": bojar(self.vag(r), self.radier(r)),
                            "svep": bojar(self.vag(r), self.radier(r), svep=True), "slag": r.slag,
                            "ledare": ledare.get(k),
                            "grupp": k.split("-")[0] if k.split("-")[0] in GRUPP else None}
                        for k, r in self.ror.items()},
                "kretsar": [k.utdrag() for k in kretsar],
                "drivdon": {"namn": DRIVDON.namn, "tillverkare": DRIVDON.tillverkare, "artikel": DRIVDON.artikel,
                            "minsta": DRIVDON.minsta, "storsta": DRIVDON.storsta, "spanning": DRIVDON.spanning,
                            "verkningsgrad": DRIVDON.verkningsgrad},
                "grupper": {g.id: {"namn": g.namn, "sakring": g.text, "faser": g.faser, "area": g.area,
                                   "jordfel": g.jordfel, "punkter": list(g.punkter)} for g in GRUPPER},
                "central": {"huvudbrytare": HUVUDBRYTARE, "overspanningsskydd": OVERSPANNINGSSKYDD}}


def _armatur(t: Armaturtyp) -> dict[str, object]:
    pe = t.pendel
    return {"tillverkare": t.tillverkare, "artikel": t.artikel, "url": t.url, "ljusflode": t.ljusflode,
            "effekt": t.effekt, "fargtemperatur": t.fargtemperatur, "ra": t.ra, "ip": t.ip, "dimring": t.dimring,
            "vridbar": t.vridbar, "stralvinkel": t.stralvinkel,
            "lysande_d": t.lysande_d, "hal_d": t.hal_d, "fotometri": t.fotometri, "fotometri_url": t.fotometri_url,
            "form": "pendel" if pe else "linje" if t.linje else "infalld" if t.huvud is None else "tub",
            **({"dosa": {"namn": t.dosa.namn, "diameter": t.dosa.diameter, "djup": t.dosa.djup}} if t.dosa else {}),
            **({"linje": {"langd": t.langd, "lysande": t.lysande_langd, "bredd": t.linje.bredd, "hojd": t.linje.hojd,
                          "diffusor": t.linje.diffusor[0], "lm_per_m": t.linje.lm_per_m, "w_per_m": t.linje.w_per_m,
                          "spanning": t.linje.spanning, "list": t.linje.list_namn, "kanal": t.linje.kanal_namn}}
               if t.linje else {}),
            **({"pendel": {"form": pe.form, "diameter": pe.diameter, "hojd": pe.hojd, "kalla_d": pe.kalla_d,
                           "ljuskalla": pe.ljuskalla, "lysande_yta": pe.lysande_yta,
                           "lysande_andel": pe.lysande_andel, "transmission": pe.transmission}} if pe else {})}


def langd(vag: list[Vek]) -> float:
    return sum(math.dist(a, b) for a, b in zip(vag, vag[1:]))


def _i_dosan(p: Punkt, q: Sequence[Vek]) -> bool:
    """Om punkten q (rörets ände) ligger i den ingjutna dosan p (in i dosan från sidan): inom dosans radie i plan och
    mellan dess under- och överkant."""
    dosa = p.typ.dosa if isinstance(p, Lampa) else p.typ if isinstance(p, Dosa) else None
    if dosa is None or dosa.slag != "ingjutningsdosa" or not q:
        return False
    m = p.lage.punkt
    return math.dist(q[0][:2], m[:2]) <= dosa.diameter / 2 and m[2] - 1.0 <= q[0][2] <= m[2] + dosa.djup + 1.0


@cache
def installation() -> Installation:
    rum: dict[str, Rum] = {}
    punkter: dict[str, Punkt] = {}
    tandgrupper: dict[str, Tandgrupp] = {}
    ror: dict[str, Ror] = {}
    modul: dict[str, str] = {}
    kretsar: dict[str, Krets] = {}
    for m in MODULER:
        if hasattr(m, "RUM"):
            rum[m.RUM.kod] = m.RUM
        for samling, lista in ((tandgrupper, getattr(m, "TANDGRUPPER", [])), (punkter, getattr(m, "PUNKTER", [])),
                               (ror, getattr(m, "ROR", [])), (kretsar, getattr(m, "KRETSAR", []))):
            for o in lista:
                if o.id in modul:
                    raise ValueError(f"id {o.id} finns två gånger ({m.NAMN})")
                samling[o.id] = o
                modul[o.id] = m.NAMN
    # där två rör i bjälklaget ändå korsar varandra i samma nivå går det ena förbi det andra (bjalklag/ingjutna.py)
    for ro in korsningar(list(ror.values())):
        ror[ro.id] = ro
    return Installation(rum, punkter, tandgrupper, ror, modul, kretsar)


def haltagningar() -> list[tuple[Form, Lada]]:
    """De infällda armaturernas håltagning i innertaket (typens hal_d), från takytan så djupt som armaturen går in:
    verktygen och deras lådor, som skärs ur de invändiga skikten (hus.py), så att ljuset kommer ut ur taket."""
    ut = []
    for p in installation().punkter.values():
        if isinstance(p, Lampa) and p.typ.pendel is None and p.typ.hal_d > 0 and p.typ.djup > 0:
            m, r = p.lage, p.typ.hal_d / 2
            a, b = flytt(m.punkt, m.normal, 1.0), flytt(m.punkt, m.normal, -p.typ.djup)
            lada = (min(a[0], b[0]) - r, min(a[1], b[1]) - r, min(a[2], b[2]) - r,
                    max(a[0], b[0]) + r, max(a[1], b[1]) + r, max(a[2], b[2]) + r)
            ut.append((stang(a, b, p.typ.hal_d), lada))
    return ut


def stralar() -> list[tuple[str, Vek, Vek, float]]:
    """Armaturernas ljus, för avståndet till brännbart material i ljusets riktning (kontrollregler.STRALAR, prövas mot
    husets ytor i ./mod kontroll): armaturen, den lysande ytans mitt, ljusets riktning och typens avstånd."""
    return [(p.id, linsen(p), enhet(p.riktning), p.typ.brandavstand) for p in installation().punkter.values()
            if isinstance(p, Lampa) and p.typ.brandavstand > 0]


def avstand(a0: Vek, a1: Vek, b0: Vek, b1: Vek) -> tuple[float, Vek]:
    """Kortaste avståndet mellan två sträckor i rummet och punkten på den första där det är."""
    u = [a1[i] - a0[i] for i in range(3)]
    v = [b1[i] - b0[i] for i in range(3)]
    w = [a0[i] - b0[i] for i in range(3)]
    a, b, c = sum(x * x for x in u), sum(x * y for x, y in zip(u, v)), sum(y * y for y in v)
    d, e = sum(x * y for x, y in zip(u, w)), sum(x * y for x, y in zip(v, w))
    nam = a * c - b * b
    s = 0.0 if nam < 1e-9 else min(1.0, max(0.0, (b * e - c * d) / nam))
    t = min(1.0, max(0.0, (b * s + e) / c)) if c > 1e-9 else 0.0
    s = min(1.0, max(0.0, (b * t - d) / a)) if a > 1e-9 else 0.0
    p = (a0[0] + s * u[0], a0[1] + s * u[1], a0[2] + s * u[2])
    q = (b0[0] + t * v[0], b0[1] + t * v[1], b0[2] + t * v[2])
    return math.dist(p, q), p
