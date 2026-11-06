"""Genomföringar för installationerna (ventilation, vatten, värme): där raka stycken av kanaler och rör går genom
husets delar, räknat ur husets geometri: ursparingar och hylsor i mellanbjälklaget (skelett.KONTUR utan trapphålet) och
bottenplattan, ingjutna rör som kommer ut ur bjälklagets över- eller underkant, håltagningar i källarväggarnas kärna
(kallarvaggar.VAGGAR) och rör i deras cellplast bakom gipsen, genomföringar i ytterväggar och innerväggar, stycken i
väggarnas regelfack (som ska rymmas i stommen), genomföringar i innertaket (ångbromsen tätas) och i taket, och stycken
mellan takbalkarna (fria från dem, takbalkar.FALT). Ger också felen: stycken som inte ryms i stommen eller i
cellplasten, går mot takbalkar eller är oisolerade i kalla delar.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from functools import cache

from shapely.geometry import LineString, Point, Polygon

from trebodar import skelett as S
from trebodar.byggdelar import taklager as L
from trebodar.hus.grund import kallarvaggar as K
from trebodar.hus.grund.grund import H_PLATTA
from trebodar.hus.invandigt.kallare import GIPS_T
from trebodar.hus.invandigt.skikt import INSIDA_T, innertak_vid, innertakets_fall
from trebodar.hus.invandigt.vaggar import LATTA, skiktets_tjocklek, vaggdef
from trebodar.hus.rum import BADRUM
from trebodar.hus.stomme import lagen
from trebodar.hus.stomme.prefab.takbalkar.takbalkar import FALT

from .montering import KALLARTAK, Vek

SPEL = 20.0                    # håltagningarnas spel runt kanalen eller röret (och isoleringen) på var sida [mm]
HYLSA = 60.0                   # stycken med yttermått upp till detta får hylsor (gjutna eller kärnborrade) [mm]


@dataclass(frozen=True)
class Stycke:
    """Ett rakt stycke av en kanal eller ett rör: elementet, ändarna, tvärsnittet (bredd och tjocklek utan
    isolering, rund eller platt, bredden längs bredd_langs), isoleringen och måttet som det skrivs."""
    element: str
    a: Vek
    b: Vek
    bredd: float
    tjocklek: float
    rund: bool
    isolering: float = 0.0
    bredd_langs: Vek = (1.0, 0.0, 0.0)
    matt: str = ""

    @property
    def yttre(self) -> tuple[float, float]:
        return self.bredd + 2 * self.isolering, self.tjocklek + 2 * self.isolering


@dataclass(frozen=True)
class Genomforing:
    """Där ett stycke går genom en byggdel: byggdelen, vad som görs, läget, måttet (håltagningen) och elementet."""
    del_: str
    atgard: str
    punkt: Vek
    matt: str
    element: str


def _z(lo: float, hi: float) -> str:
    """Höjdintervallet som text (minustecken, "till" när det finns negativa tal)."""
    def t(v: float) -> str:
        return f"{v:.0f}".replace("-", "\u2212")
    return f"z {t(lo)}–{t(hi)}" if lo >= 0.0 else f"z {t(lo)} till {t(hi)}"


def avrunda(x: float, steg: float = 10.0) -> float:
    return math.ceil(x / steg - 1e-9) * steg


def _hal(st: Stycke) -> str:
    """Håltagningens mått med spelet: Ø för runda, b × h för platta."""
    b, h = st.yttre
    return f"Ø{avrunda(b + 2 * SPEL):g}" if st.rund else f"{avrunda(b + 2 * SPEL):g} × {avrunda(h + 2 * SPEL):g}"


def _vaggband(kod: str, w0: float, w1: float) -> Polygon:
    v = S.YTTERVAGGAR[kod] if kod in S.YTTERVAGGAR else vaggdef(kod)
    hörn = [(v.origo[0] + v.u[0] * u + v.w[0] * w, v.origo[1] + v.u[1] * u + v.w[1] * w)
            for u, w in ((0.0, w0), (v.langd, w0), (v.langd, w1), (0.0, w1))]
    return Polygon(hörn)


@cache
def vaggarna() -> dict[str, tuple[Polygon, Polygon, float, bool]]:
    """Plan 1:s väggar: (hela väggen med skikten, stommen, stommens tjocklek, yttervägg)."""
    ut = {}
    for kod in S.YTTERVAGGAR:
        ut[kod] = (_vaggband(kod, -S.T_FASAD, S.T_STOMME + INSIDA_T), _vaggband(kod, 0.0, S.T_STOMME), S.T_STOMME,
                   True)
    for kod in [*S.INNERVAGGAR, *(lv.kod for lv in LATTA)]:
        v = vaggdef(kod)
        u = v.langd / 2
        ut[kod] = (_vaggband(kod, -skiktets_tjocklek(kod, -1, u), v.tjocklek + skiktets_tjocklek(kod, 1, u)),
                   _vaggband(kod, 0.0, v.tjocklek), v.tjocklek, False)
    return ut


def _over_vaggen(kod: str, x: float, y: float, z: float) -> bool:
    """Om höjden z i punkten (x, y) på innerväggen kod ligger över väggen: de lätta väggarna och alla väggars skikt går
    upp till innertaket, de bärande innerväggarnas stomme där den går högre."""
    topp = innertak_vid(x, y)
    if kod in S.INNERVAGGAR:
        topp = max([topp, *(d.lada[5] for d in lagen.vagg(kod)
                            if d.lada[0] - 1.0 <= x <= d.lada[3] + 1.0 and d.lada[1] - 1.0 <= y <= d.lada[4] + 1.0)])
    return z > topp


@cache
def kallarvaggarna() -> dict[str, tuple[Polygon, Polygon]]:
    """Källarväggarna i plan: (hela väggen med cellplasten och gipsen, kärnan)."""
    def band(v: K.Kallarvagg, t: float) -> Polygon:
        return (Polygon([(v.a, v.c - t), (v.b, v.c - t), (v.b, v.c + t), (v.a, v.c + t)]) if v.riktning == "h"
                else Polygon([(v.c - t, v.a), (v.c + t, v.a), (v.c + t, v.b), (v.c - t, v.b)]))
    return {v.namn: (band(v, K.KARNA / 2 + K.CELL + GIPS_T), band(v, K.KARNA / 2)) for v in K.VAGGAR}


@cache
def bjalklaget() -> Polygon:
    return Polygon(S.KONTUR).difference(Polygon(S.TRAPPHAL))


@cache
def bottenplattan() -> Polygon:
    return K.ytterkontur()


def _wkomp(kod: str, riktning: Vek) -> float:
    """Riktningens komponent tvärs väggen (väggens w)."""
    v = S.YTTERVAGGAR[kod] if kod in S.YTTERVAGGAR else vaggdef(kod)
    return riktning[0] * v.w[0] + riktning[1] * v.w[1]


def _genom_platta(st: Stycke, z_ok: float, tjocklek: float, yta: Polygon, namn: str, ritning: str,
                  ut: list[Genomforing]) -> None:
    """Ett stycke genom en vågrät platta (överkant z_ok) inom ytan: hylsa för små rör, annars ursparing. Ett rör som
    slutar inne i plattan är ingjutet och kommer ut ur dess över- eller underkant (läggs före gjutningen)."""
    a, b = st.a, st.b
    z_uk = z_ok - tjocklek
    z0, z1 = sorted((a[2], b[2]))
    inne = [z_uk + 1.0 < p[2] < z_ok - 1.0 for p in (a, b)]
    if all(inne) or not (z0 < z_ok - 1.0 and z1 > z_uk + 1.0):
        return
    upp = z1 > z_ok - 1.0
    z = (z_ok if upp else z_uk) if any(inne) else z_ok - tjocklek / 2
    t = (z - a[2]) / (b[2] - a[2])
    p: Vek = (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]), z)
    if not yta.contains(Point(p[0], p[1])):
        return
    if any(inne):
        ut.append(Genomforing(namn, f"ingjutet, ut ur {'överkanten' if upp else 'underkanten'} mellan "
                              f"armeringsjärnen ({ritning})", p, st.matt, st.element))
    else:
        atgard = (f"hylsa ingjuten ({ritning}) eller kärnborrning mellan armeringsjärnen" if max(st.yttre) <= HYLSA
                  else f"ursparing före gjutningen, armeringen läggs om ({ritning})")
        ut.append(Genomforing(namn, atgard, p, _hal(st), st.element))


def genomforingar(stycken: list[Stycke]) -> tuple[list[Genomforing], list[str]]:
    """Genomföringarna genom husets delar och felen från dem (stycken som inte ryms i väggen, går mot takbalkar eller
    är oisolerade i kalla delar), varje genomföring en gång per element och byggdel."""
    ut: list[Genomforing] = []
    fel: list[str] = []
    for st in stycken:
        a, b = st.a, st.b
        bredd, tjock = st.yttre
        eid = st.element
        lodratt = math.hypot(b[0] - a[0], b[1] - a[1]) < 1.0
        z0, z1 = sorted((a[2], b[2]))
        _genom_platta(st, 0.0, S.H_BJALKLAG, bjalklaget(), "Mellanbjälklaget", "R-06", ut)
        _genom_platta(st, S.Z_BOTTENPLATTA, H_PLATTA, bottenplattan(), "Bottenplattan", "R-04", ut)
        # källarväggarna: genom kärnan (kärnborrning) eller lodrätt i cellplasten bakom gipsen
        if lodratt and z0 < KALLARTAK - 1.0 and z1 > S.Z_BOTTENPLATTA + 1.0:
            lo, hi = max(z0, S.Z_BOTTENPLATTA), min(z1, KALLARTAK)
            for namn, (hel, karna) in kallarvaggarna().items():
                q = Point(a[0], a[1])
                if not hel.contains(q):
                    continue
                if karna.buffer(bredd / 2).contains(q):
                    fel.append(f"{eid}: lodrätt i källarväggen {namn}:s kärna")
                else:
                    ut.append(Genomforing(f"Källarvägg {namn}", f"i cellplasten bakom gipsen (fräst spår), "
                                          f"{_z(lo, hi)}", (a[0], a[1], (lo + hi) / 2), st.matt, eid))
                    if bredd + 2 * 4.0 > K.CELL:
                        fel.append(f"{eid}: {bredd:g} mm ryms inte i källarväggens cellplast ({K.CELL:g} mm)")
        elif z1 < KALLARTAK and z0 > S.Z_BOTTENPLATTA:
            for namn, (hel, karna) in kallarvaggarna().items():
                s = LineString([a[:2], b[:2]])
                if s.intersection(karna).length > 1.0:
                    m = s.intersection(hel).centroid
                    ut.append(Genomforing(f"Källarvägg {namn}", "kärnborrning mellan armeringsjärnen",
                                          (m.x, m.y, (a[2] + b[2]) / 2), f"Ø{avrunda(bredd + 2 * SPEL):g}", eid))
        # plan 1:s väggar: i regelfacket (lodrätt) eller genom väggen
        if z1 > 0.0:
            for kod, (hel, stomme, t_stomme, yttre) in vaggarna().items():
                if lodratt:
                    if stomme.buffer(1.0).contains(Point(a[0], a[1])):
                        topp = innertak_vid(a[0], a[1])
                        lo, hi = max(z0, 0.0), min(z1, topp)
                        if hi - lo < 1.0:
                            continue
                        tvars = bredd if st.rund or abs(_wkomp(kod, st.bredd_langs)) > 0.5 else tjock
                        urtag = "; syll och hammarband urtas" if lo < 1.0 and hi > topp - 1.0 else \
                            "; syllen urtas" if lo < 1.0 else ""
                        ut.append(Genomforing(f"Vägg {kod}", f"i regelfacket, {_z(lo, hi)}{urtag}",
                                              (a[0], a[1], (lo + hi) / 2), st.matt, eid))
                        if tvars > t_stomme - 2 * 4.0:
                            fel.append(f"{eid}: {tvars:g} mm tvärs väggen ryms inte i {kod}:s stomme ({t_stomme:g} mm)")
                    continue
                s = LineString([a[:2], b[:2]])
                inne = hel.buffer(-1.0)
                if s.intersection(hel).length > 1.0 and not (inne.contains(Point(a[0], a[1])) and
                                                              inne.contains(Point(b[0], b[1]))):
                    m = s.intersection(hel).centroid
                    f = s.project(m) / s.length
                    if not yttre and not (hel.contains(Point(a[0], a[1])) or hel.contains(Point(b[0], b[1]))) and \
                            _over_vaggen(kod, m.x, m.y, a[2] + f * (b[2] - a[2]) - tjock / 2):
                        continue                                # i innertakets installationsskikt, över väggen
                    vatrum = s.difference(hel).intersects(BADRUM)      # stycket går ut i badrummet
                    ut.append(Genomforing(f"{'Yttervägg' if yttre else 'Vägg'} {kod}",
                                          ("väggenomföring" if yttre else "genomföring")
                                          + ("; tätskiktet tätas med manschett (våtrum)" if vatrum else ""),
                                          (m.x, m.y, (a[2] + b[2]) / 2), _hal(st), eid))
                    if yttre and st.isolering <= 0.0:
                        fel.append(f"{eid}: oisolerad genom ytterväggen {kod} (kondens)")
        # innertaket, taket och takbalkarna
        if lodratt and innertakets_fall(a[0], a[1]) is not None:
            tf = innertakets_fall(a[0], a[1])
            assert tf is not None
            zi = innertak_vid(a[0], a[1])
            zt = L.z_skikt(tf, a[0], L.PLAT[1])
            zab = tf.z_overkant(a[0]) - S.TAKBALK_HV
            if z0 < zi < z1:
                ut.append(Genomforing(f"Innertaket ({tf.kod})", "genomföring; ångbromsen tätas med manschett",
                                      (a[0], a[1], zi), _hal(st), eid))
            if z0 < zt <= z1 + 1.0:
                ut.append(Genomforing(f"Taket ({tf.kod})", "genomföring i hårdboard, ströläkt, råspont, papp och plåt "
                                                         "(takhuv eller takfläkt)", (a[0], a[1], zt), _hal(st), eid))
            if z1 > zab + 1.0:
                if st.isolering <= 0.0:
                    fel.append(f"{eid}: oisolerad i takets isolering (kondens)")
                hy = (bredd if st.rund or abs(st.bredd_langs[1]) > 0.5 else tjock) / 2
                for y in FALT[tf.kod].y:
                    if a[1] + hy > y - 5.0 and a[1] - hy < y + S.TAKBALK_B + 5.0:
                        fel.append(f"{eid}: går mot takbalken i y {y:g}–{y + S.TAKBALK_B:g} ({tf.kod})")
    unika: dict[tuple[str, str, str], Genomforing] = {}
    for gf in ut:
        unika.setdefault((gf.del_, gf.element, gf.atgard.split(", z")[0]), gf)
    return list(unika.values()), sorted(set(fel))
