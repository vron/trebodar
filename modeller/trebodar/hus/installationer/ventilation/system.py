"""Ventilationen ur grenarnas moduler (MODULER), kanalernas vägar, genomföringarna genom husets delar, kontrollen
och utdraget för ritningarna (verktyg/modellering: `./mod ventilation`).

Genomföringarna räknas fram ur husets geometri: ursparingar i mellanbjälklaget (skelett.KONTUR utan trapphålet),
håltagningar i källarväggarna (kallarvaggar.VAGGAR), genomföringar i ytterväggar och innerväggar, kanaler i väggarnas
regelfack (som ska rymmas i stommen), genomföringar i innertaket (ångbromsen tätas) och i taket (takhuven), och
kanalernas läge mellan takbalkarna (takbalkar.FALT).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from functools import cache
from types import ModuleType

from shapely.geometry import LineString, Point, Polygon

from trebodar import skelett as S
from trebodar.byggdelar import taklager as L
from trebodar.hus.fonster_och_dorrar.oppningar import OPPNINGAR
from trebodar.hus.grund import kallarvaggar as K
from trebodar.hus.invandigt.kallare import GIPS_T
from trebodar.hus.invandigt.skikt import INSIDA_T, innertak_vid, innertakets_fall
from trebodar.hus.rum import BADRUM
from trebodar.hus.invandigt.vaggar import LATTA, skiktets_tjocklek, vaggdef
from trebodar.hus.stomme.prefab.takbalkar.takbalkar import FALT

from ..montering import KALLARTAK, Vek
from .delar import Avluft, Don, Element, Flakt, Gren, Kanal, Overgang, kanalernas_vagar
from .grenar import badrum, kallare, kok
from .typer import Dontyp, Kanaltyp, Koksflakttyp, Vaggflakttyp

MODULER: tuple[ModuleType, ...] = (kok, badrum, kallare)

V_MAX, V_ANM = 7.0, 5.0        # lufthastighet i kanalerna [m/s]: fel över V_MAX, anmärkning över V_ANM
SPEL = 20.0                    # håltagningarnas spel runt kanalen (och isoleringen) på var sida [mm]
LAMBDA, ZETA_90 = 0.02, 0.3    # tryckfallet: friktionstal (spirokanal) och engångsförlust per 90° böj
RHO = 1.2                      # luftens densitet [kg/m³]


@dataclass(frozen=True)
class Genomforing:
    """Där en kanal går genom en byggdel: byggdelen, vad som görs, läget och måttet (håltagningen)."""
    del_: str
    atgard: str
    punkt: Vek
    matt: str
    element: str


def _avrunda(x: float, steg: float = 10.0) -> float:
    return math.ceil(x / steg - 1e-9) * steg


def _lutning(a: Vek, b: Vek) -> float:
    return math.hypot(b[0] - a[0], b[1] - a[1])


def _vinkel(u: Vek, v: Vek) -> float:
    nu, nv = math.sqrt(sum(x * x for x in u)), math.sqrt(sum(x * x for x in v))
    if nu < 1e-6 or nv < 1e-6:
        return 0.0
    return math.degrees(math.acos(max(-1.0, min(1.0, sum(a * b for a, b in zip(u, v)) / (nu * nv)))))


def bojar(vag: list[Vek]) -> list[float]:
    """Riktningsändringarna längs vägen [°]."""
    seg = [tuple(b[i] - a[i] for i in range(3)) for a, b in zip(vag, vag[1:]) if math.dist(a, b) > 1e-6]
    return [v for v in (_vinkel(u, w) for u, w in zip(seg, seg[1:])) if v > 1.0]  # type: ignore[arg-type]


def langd(vag: list[Vek]) -> float:
    return sum(math.dist(a, b) for a, b in zip(vag, vag[1:]))


def hastighet(flode: float, typ: Kanaltyp) -> float:
    """Lufthastigheten [m/s] för flödet [l/s] i kanalen."""
    return flode * 1000.0 / typ.area


# ------------------------------------------------------------------ husets delar för genomföringarna

def _vaggband(kod: str, w0: float, w1: float) -> Polygon:
    v = S.YTTERVAGGAR[kod] if kod in S.YTTERVAGGAR else vaggdef(kod)
    hörn = [(v.origo[0] + v.u[0] * u + v.w[0] * w, v.origo[1] + v.u[1] * u + v.w[1] * w)
            for u, w in ((0.0, w0), (v.langd, w0), (v.langd, w1), (0.0, w1))]
    return Polygon(hörn)


@cache
def _vaggarna() -> dict[str, tuple[Polygon, Polygon, float, bool]]:
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


@cache
def _kallarvaggarna() -> dict[str, Polygon]:
    """Källarväggarna i plan: kärnan, cellplasten och gipsen."""
    t = K.KARNA / 2 + K.CELL + GIPS_T
    return {v.namn: (Polygon([(v.a, v.c - t), (v.b, v.c - t), (v.b, v.c + t), (v.a, v.c + t)]) if v.riktning == "h"
                     else Polygon([(v.c - t, v.a), (v.c + t, v.a), (v.c + t, v.b), (v.c - t, v.b)]))
            for v in K.VAGGAR}


@cache
def _bjalklaget() -> Polygon:
    return Polygon(S.KONTUR).difference(Polygon(S.TRAPPHAL))


def _tvarsnitt(typ: Kanaltyp) -> tuple[float, float, str]:
    """Kanalens yttermått: (bredd, tjocklek) och håltagningens mått som text (med spelet)."""
    b, h = typ.yttre
    if typ.form == "rund":
        return b, b, f"Ø{_avrunda(b + 2 * SPEL):g}"
    return b, h, f"{_avrunda(b + 2 * SPEL):g} × {_avrunda(h + 2 * SPEL):g}"


def _halvbredd_y(typ: Kanaltyp, bredd_langs: Vek) -> float:
    """Kanalens halva utbredning i y (mellan takbalkarna), med isoleringen."""
    b, h = typ.yttre
    if typ.form == "rund":
        return b / 2
    return (b if abs(bredd_langs[1]) > 0.5 else h) / 2


# ------------------------------------------------------------------ ventilationen

@dataclass
class Ventilation:
    grenar: dict[str, Gren]

    def vagar(self) -> dict[str, list[Vek]]:
        return {k: v for g in self.grenar.values() for k, v in kanalernas_vagar(g).items()}

    def _stycken(self, g: Gren) -> list[tuple[str, Kanaltyp, Vek, Vek, Vek]]:
        """Grenens raka stycken: kanalernas sträckor och övergångarnas och fläktarnas axlar (element, typ, a, b,
        bredden längs)."""
        vagar = kanalernas_vagar(g)
        ut = []
        for e in g.kedja:
            if isinstance(e, Kanal):
                v = vagar[e.id]
                ut += [(e.id, e.typ, a, b, e.bredd_langs) for a, b in zip(v, v[1:]) if math.dist(a, b) > 1e-6]
            elif isinstance(e, Overgang):
                langd_ = e.typ.langd / 2
                a = tuple(e.lage[i] - e.riktning[i] * langd_ for i in range(3))
                b = tuple(e.lage[i] + e.riktning[i] * langd_ for i in range(3))
                kall = e.typ.till if e.typ.till.isolering >= e.typ.fran.isolering else e.typ.fran
                ut.append((e.id, kall, a, b, e.bredd_langs))  # type: ignore[arg-type]
        return ut

    def genomforingar(self) -> tuple[list[Genomforing], list[str]]:
        """Genomföringarna genom husets delar och felen från dem (kanaler som inte ryms i väggen, mot takbalkar eller
        oisolerade i kalla delar)."""
        ut: list[Genomforing] = []
        fel: list[str] = []
        vaggar = _vaggarna()
        for g in self.grenar.values():
            for eid, typ, a, b, bl in self._stycken(g):
                bredd, tjock, matt = _tvarsnitt(typ)
                lodratt = _lutning(a, b) < 1.0
                z0, z1 = sorted((a[2], b[2]))
                # mellanbjälklaget
                if z0 < -S.H_BJALKLAG + 1.0 and z1 > -1.0:
                    t = (-S.H_BJALKLAG / 2 - a[2]) / (b[2] - a[2])
                    p: Vek = (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]), -S.H_BJALKLAG / 2)
                    if _bjalklaget().contains(Point(p[0], p[1])):
                        ut.append(Genomforing("Mellanbjälklaget",
                                              "ursparing före gjutningen, armeringen läggs om (R-06)", p, matt, eid))
                # källarväggarna
                if z1 < KALLARTAK and not lodratt:
                    for namn, poly in _kallarvaggarna().items():
                        s = LineString([a[:2], b[:2]])
                        if s.intersection(poly).length > 1.0:
                            m = s.intersection(poly).centroid
                            ut.append(Genomforing(f"Källarvägg {namn}", "kärnborrning mellan armeringsjärnen",
                                                  (m.x, m.y, (a[2] + b[2]) / 2), f"Ø{_avrunda(bredd + 2 * SPEL):g}",
                                                  eid))
                # plan 1:s väggar
                if z1 > 0.0:
                    for kod, (hel, stomme, t_stomme, yttre) in vaggar.items():
                        if lodratt:
                            if stomme.buffer(1.0).contains(Point(a[0], a[1])):
                                topp = innertak_vid(a[0], a[1])
                                lo, hi = max(z0, 0.0), min(z1, topp)
                                if hi - lo < 1.0:
                                    continue
                                tvars = bredd if typ.form == "rund" or abs(_wkomp(kod, bl)) > 0.5 else tjock
                                urtag = "; syll och hammarband urtas" if lo < 1.0 and hi > topp - 1.0 else ""
                                ut.append(Genomforing(f"Vägg {kod}", f"i regelfacket, z {lo:.0f}–{hi:.0f}{urtag}",
                                                      (a[0], a[1], (lo + hi) / 2), typ.matt, eid))
                                if tvars > t_stomme - 2 * 4.0:
                                    fel.append(f"{eid}: kanalen ({tvars:g} mm tvärs väggen) ryms inte i {kod}:s stomme "
                                               f"({t_stomme:g} mm)")
                            continue
                        s = LineString([a[:2], b[:2]])
                        if s.intersection(hel).length > 1.0:
                            m = s.intersection(hel).centroid
                            vatrum = BADRUM.buffer(200.0).contains(Point(a[0], a[1])) or \
                                BADRUM.buffer(200.0).contains(Point(b[0], b[1]))
                            ut.append(Genomforing(f"{'Yttervägg' if yttre else 'Vägg'} {kod}",
                                                  ("väggenomföring" if yttre else "genomföring")
                                                  + ("; tätskiktet tätas med manschett (våtrum)" if vatrum else ""),
                                                  (m.x, m.y, (a[2] + b[2]) / 2), matt, eid))
                            if yttre and typ.isolering <= 0.0:
                                fel.append(f"{eid}: oisolerad kanal genom ytterväggen {kod} (kondens)")
                # innertaket, taket och takbalkarna
                if lodratt and innertakets_fall(a[0], a[1]) is not None:
                    tf = innertakets_fall(a[0], a[1])
                    assert tf is not None
                    zi = innertak_vid(a[0], a[1])
                    zt = L.z_skikt(tf, a[0], L.PLAT[1])
                    zab = tf.z_overkant(a[0]) - S.TAKBALK_HV
                    if z0 < zi < z1:
                        ut.append(Genomforing(f"Innertaket ({tf.kod})", "genomföring; ångbromsen tätas med manschett",
                                              (a[0], a[1], zi), matt, eid))
                    if z0 < zt <= z1 + 1.0:
                        ut.append(Genomforing(f"Taket ({tf.kod})", "genomföring i hårdboard, ströläkt, råspont, "
                                                                   "papp och plåt (takhuv)",
                                              (a[0], a[1], zt), matt, eid))
                    if z1 > zab + 1.0:
                        if typ.isolering <= 0.0:
                            fel.append(f"{eid}: oisolerad kanal i takets isolering (kondens)")
                        hy = _halvbredd_y(typ, bl)
                        for y in FALT[tf.kod].y:
                            if a[1] + hy > y - 5.0 and a[1] - hy < y + S.TAKBALK_B + 5.0:
                                fel.append(f"{eid}: kanalen går mot takbalken i y {y:g}–{y + S.TAKBALK_B:g} ({tf.kod})")
        # samma genomföring en gång (en kanal kan ha flera stycken i samma byggdel)
        unika: dict[tuple[str, str], Genomforing] = {}
        for gf in ut:
            unika.setdefault((gf.del_, gf.element), gf)
        return list(unika.values()), sorted(set(fel))

    def kontroll(self) -> tuple[list[str], list[str]]:
        """Fel (stoppar) och anmärkningar: kedjorna, anslutningarna, fläktarna, lufthastigheterna, genomföringarna
        och ventilationen som helhet (ersättningsluft, kaminen, avluft nära fönster och takhuvar nära dalar)."""
        fel: list[str] = []
        anm: list[str] = []
        sedda: set[str] = set()
        for g in self.grenar.values():
            k = g.kedja
            if not k or not isinstance(k[0], Don) or not isinstance(k[-1], Avluft):
                fel.append(f"{g.id}: kedjan ska börja med ett don och sluta med ett avluftsdon")
                continue
            for e in k:
                if e.id in sedda:
                    fel.append(f"{e.id}: id används två gånger")
                sedda.add(e.id)
                if not e.id.startswith(g.id + "-"):
                    fel.append(f"{e.id}: id ska börja med grenens ({g.id}-)")
            flaktar = [e for e in k if isinstance(e, Flakt) or isinstance(e, Don) and
                       isinstance(e.typ, (Koksflakttyp, Vaggflakttyp))]
            if len(flaktar) != 1:
                fel.append(f"{g.id}: {len(flaktar)} fläktar (en per gren)")
            for f in flaktar:
                if g.flode > f.typ.flode + 1e-6:
                    fel.append(f"{g.id}: flödet {g.flode:g} l/s är större än fläkten {f.id}:s {f.typ.flode:g} l/s")
            # anslutningarna mellan elementen
            for a, b in zip(k, k[1:]):
                d_ut = _anslutning(a, slut=True)
                d_in = _anslutning(b, slut=False)
                if d_ut and d_in and abs(d_ut - d_in) > 0.5:
                    fel.append(f"{a.id} – {b.id}: anslutningarna passar inte ({d_ut:g} och {d_in:g})")
            for e in k:
                if isinstance(e, Overgang):
                    i = k.index(e)
                    fore, efter = k[i - 1], k[i + 1]
                    if isinstance(fore, Kanal) and fore.typ != e.typ.fran or \
                            isinstance(efter, Kanal) and efter.typ != e.typ.till:
                        fel.append(f"{e.id}: övergången passar inte kanalerna före och efter")
            # lufthastigheterna och tryckfallet i kanalerna
            for e in k:
                if isinstance(e, Kanal):
                    v = hastighet(g.flode, e.typ)
                    if v > V_MAX:
                        fel.append(f"{e.id}: {v:.1f} m/s i {e.typ.matt} vid {g.flode:g} l/s (högst {V_MAX:g})")
                    elif v > V_ANM:
                        anm.append(f"{e.id}: {v:.1f} m/s i {e.typ.matt} vid {g.flode:g} l/s (ljud)")
            vinklar = [b for e in k if isinstance(e, Kanal) for b in bojar(kanalernas_vagar(g)[e.id])]
            if sum(vinklar) > 360.0:
                anm.append(f"{g.id}: {len(vinklar)} böjar, {sum(vinklar):.0f}° sammanlagt")
        fel += self.genomforingar()[1]
        # ventilationen som helhet
        kok_ = [g for g in self.grenar.values() if isinstance(g.kedja[0], Don) and isinstance(g.kedja[0].typ,
                                                                                               Koksflakttyp)]
        summa = sum(g.flode for g in self.grenar.values())
        if kok_:
            anm.append(f"köksfläkten forcerar {kok_[0].flode:g} l/s ({kok_[0].flode * 3.6:.0f} m³/h) och frånluften är "
                       f"sammanlagt {summa:g} l/s utan tilluft i modellen: ersättningsluft (uteluftsdon eller spjäll "
                       "som öppnar med fläkten) behövs, särskilt med kaminen i huset (undertryck)")
        for g in self.grenar.values():
            a = g.kedja[-1]
            if not isinstance(a, Avluft):
                continue
            if a.typ.slag == "galler" and a.lage.ref in OPPNINGAR:
                vd = S.YTTERVAGGAR[a.lage.ref]
                u = (a.lage.punkt[0] - vd.origo[0]) * vd.u[0] + (a.lage.punkt[1] - vd.origo[1]) * vd.u[1]
                nara = [o.kod for o in OPPNINGAR[a.lage.ref] if o.typ in ("vridfönster", "fönsterdörr")
                        and min(abs(u - o.u0), abs(u - o.u1), 0.0 if o.u0 <= u <= o.u1 else 1e9) < 1000.0]
                if nara:
                    anm.append(f"{a.id}: avluften går ut inom 1 m från de öppningsbara fönstren {', '.join(nara)}")
            if a.typ.slag == "takhuv":
                x = a.lage.punkt[0]
                for balk in S.BALKAR.values():
                    if balk.y0 <= a.lage.punkt[1] <= balk.y1 and abs(x - balk.x) < 500.0:
                        anm.append(f"{a.id}: takhuven {abs(x - balk.x):.0f} mm (i plan) från {balk.kod} ({balk.typ})")
        return sorted(set(fel), key=fel.index), anm

    def utdrag(self) -> dict[str, object]:
        """Allt som ritningarna behöver, som JSON: grenarna med elementen, kanalernas vägar, genomföringarna och
        typerna."""
        vagar = self.vagar()
        gf = self.genomforingar()[0]
        typer: dict[str, dict[str, object]] = {}
        element: dict[str, dict[str, object]] = {}
        for g in self.grenar.values():
            for e in g.kedja:
                t = e.typ
                typer[t.kod] = {"namn": t.namn, **_typdata(t)}
                d: dict[str, object] = {"gren": g.id, "slag": type(e).__name__.lower(), "typ": t.kod}
                if isinstance(e, Kanal):
                    v = vagar[e.id]
                    d |= {"vag": [list(p) for p in v], "langd": langd(v), "bojar": sum(bojar(v)),
                          "bredd_langs": list(e.bredd_langs), "hastighet": hastighet(g.flode, e.typ)}
                elif isinstance(e, (Flakt, Overgang)):
                    d |= {"punkt": list(e.lage), "riktning": list(e.riktning)}
                else:
                    d |= {"punkt": list(e.lage.punkt), "normal": list(e.lage.normal), "yta": e.lage.yta,
                          "ref": e.lage.ref}
                element[e.id] = d
        return {"grenar": {g.id: {"namn": g.namn, "rum": g.rum, "flode": g.flode, "flode_normal": g.flode_normal,
                                  "element": [e.id for e in g.kedja], "tryckfall": tryckfall(g),
                                  "beskrivning": list(g.beskrivning)}
                           for g in self.grenar.values()},
                "element": element, "typer": typer,
                "nivaer": {"plan 1:s golv": 0.0, "källarens tak": KALLARTAK, "källarens golv": S.Z_BOTTENPLATTA},
                "genomforingar": [{"del": x.del_, "atgard": x.atgard, "punkt": list(x.punkt), "matt": x.matt,
                                   "element": x.element} for x in gf]}


def _wkomp(kod: str, riktning: Vek) -> float:
    """Riktningens komponent tvärs väggen (väggens w)."""
    v = S.YTTERVAGGAR[kod] if kod in S.YTTERVAGGAR else vaggdef(kod)
    return riktning[0] * v.w[0] + riktning[1] * v.w[1]


def _anslutning(e: Element, slut: bool) -> float | None:
    """Anslutningens storlek (diameter, eller bredden för platta kanaler) i elementets början eller slut."""
    if isinstance(e, Kanal):
        return e.typ.b
    if isinstance(e, Overgang):
        return e.typ.till.b if slut else e.typ.fran.b
    return e.typ.anslutning


def _typdata(t: object) -> dict[str, object]:
    if isinstance(t, Kanaltyp):
        return {"slag": "kanal", "form": t.form, "b": t.b, "h": t.h, "isolering": t.isolering, "matt": t.matt}
    if isinstance(t, Koksflakttyp):
        return {"slag": "köksfläkt", "b": t.b, "d": t.d, "h": t.h, "skorsten": list(t.skorsten), "flode": t.flode}
    if isinstance(t, Vaggflakttyp):
        return {"slag": "väggfläkt", "anslutning": t.anslutning, "front": list(t.front), "flode": t.flode}
    if isinstance(t, Dontyp):
        return {"slag": "frånluftsdon", "anslutning": t.anslutning, "front_d": t.front_d, "flode": t.flode}
    d = {k: getattr(t, k) for k in ("slag", "anslutning", "b", "h", "d", "langd", "flode") if hasattr(t, k)}
    return {k: (v if isinstance(v, (int, float, str)) else str(v)) for k, v in d.items()}


def tryckfall(g: Gren) -> float:
    """Kanalernas tryckfall ungefär [Pa] vid det dimensionerande flödet: friktion och böjar (utan donen,
    avluftsdonen och övergångarna, som tillverkarna anger)."""
    s = 0.0
    vagar = kanalernas_vagar(g)
    for e in g.kedja:
        if isinstance(e, Kanal):
            v = hastighet(g.flode, e.typ)
            dh = e.typ.b / 1000 if e.typ.form == "rund" else 2 * e.typ.b * e.typ.h / (e.typ.b + e.typ.h) / 1000
            dyn = RHO * v * v / 2
            s += (LAMBDA * langd(vagar[e.id]) / 1000 / dh + sum(ZETA_90 * b / 90.0 for b in bojar(vagar[e.id]))) * dyn
    return s


@cache
def ventilation() -> Ventilation:
    return Ventilation({mod.GREN.id: mod.GREN for mod in MODULER})

