"""Ventilationen ur grenarnas moduler (MODULER), kanalernas vägar, genomföringarna genom husets delar, kontrollen
och utdraget för ritningarna (verktyg/modellering: `./mod ventilation`).

Genomföringarna räknas fram ur husets geometri med installationernas gemensamma genomforingar.py: ursparingar i
mellanbjälklaget, håltagningar i källarväggarna, genomföringar i väggar, innertaket och taket, kanaler i regelfacken
och mellan takbalkarna.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from functools import cache
from types import ModuleType

from trebodar import skelett as S
from trebodar.hus.fonster_och_dorrar.oppningar import OPPNINGAR

from ..genomforingar import Genomforing, Stycke, genomforingar
from ..montering import KALLARTAK, Vek
from .delar import Avluft, Don, Element, Flakt, Gren, Kanal, Overgang, kanalernas_vagar
from .grenar import badrum, kallare, kok
from .typer import Dontyp, Kanaltyp, Koksflakttyp, Vaggflakttyp

MODULER: tuple[ModuleType, ...] = (kok, badrum, kallare)

V_MAX, V_ANM = 7.0, 5.0        # lufthastighet i kanalerna [m/s]: fel över V_MAX, anmärkning över V_ANM
LAMBDA, ZETA_90 = 0.02, 0.3    # tryckfallet: friktionstal (spirokanal) och engångsförlust per 90° böj
RHO = 1.2                      # luftens densitet [kg/m³]


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


# ------------------------------------------------------------------ ventilationen

@dataclass
class Ventilation:
    grenar: dict[str, Gren]

    def vagar(self) -> dict[str, list[Vek]]:
        return {k: v for g in self.grenar.values() for k, v in kanalernas_vagar(g).items()}

    def stycken(self, g: Gren) -> list[Stycke]:
        """Grenens raka stycken: kanalernas sträckor och övergångarnas axlar (med den kallare sidans typ)."""
        vagar = kanalernas_vagar(g)
        ut = []
        for e in g.kedja:
            if isinstance(e, Kanal):
                v = vagar[e.id]
                ut += [_stycke(e.id, e.typ, a, b, e.bredd_langs) for a, b in zip(v, v[1:]) if math.dist(a, b) > 1e-6]
            elif isinstance(e, Overgang):
                h = e.typ.langd / 2
                a: Vek = (e.lage[0] - e.riktning[0] * h, e.lage[1] - e.riktning[1] * h, e.lage[2] - e.riktning[2] * h)
                b: Vek = (e.lage[0] + e.riktning[0] * h, e.lage[1] + e.riktning[1] * h, e.lage[2] + e.riktning[2] * h)
                kall = e.typ.till if e.typ.till.isolering >= e.typ.fran.isolering else e.typ.fran
                ut.append(_stycke(e.id, kall, a, b, e.bredd_langs))
        return ut

    def genomforingar(self) -> tuple[list[Genomforing], list[str]]:
        """Genomföringarna genom husets delar och felen från dem (installationer/genomforingar.py)."""
        return genomforingar([st for g in self.grenar.values() for st in self.stycken(g)])

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
                nara = [o.kod for o in OPPNINGAR[a.lage.ref] if o.typ in ("vändfönster", "fönsterdörr")
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


def _stycke(eid: str, typ: Kanaltyp, a: Vek, b: Vek, bredd_langs: Vek) -> Stycke:
    return Stycke(eid, a, b, typ.b, typ.h, typ.form == "rund", typ.isolering, bredd_langs, typ.matt)


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

