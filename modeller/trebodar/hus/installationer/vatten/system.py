"""Tappvattnet ur modulerna (MODULER): tappställena, rörens filer och fördelarnas utgångar (i tappställenas ordning
teknikrum.ORDNING), rören från fördelarna till tappställena längs stråken och matarledningarna, kontrollen,
genomföringarna och utdraget för ritningarna (verktyg/modellering: `./mod vatten`).

Rörens ändar: fördelarnas utgångar ("FD-KV:3"; utgång 0 och utgången efter den sista är stammens ändar), utrustningen
i teknikrummet ("TK-VP:VV-ut", ..teknikrum.UTRUSTNING) och tappställena (anslutningen i dosan, kallt och varmt).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from functools import cache
from types import ModuleType

from ..genomforingar import Genomforing, Stycke, genomforingar
from ..montering import KALLARTAK, PLAN, Vek
from ..teknikrum import UTRUSTNING
from . import teknikrum
from .katalog import FORDELARE_KV, FORDELARE_VV
from ..strak import Strak, filer
from .punkter import FIL, Z_ROR, Fordelare, Ror, Rum, Tappstalle, anslutning, ror, till_tappstallet
from .rum import badrum, kallare, kok

MODULER: tuple[ModuleType, ...] = (badrum, kok, kallare)

VV_TID = 10.0                  # varmvatten vid tappstället inom 10 s vid normflödet (BBR 6:62, Säker Vatten) [s]
V_MAX, V_ANM = 2.5, 2.0        # vattenhastighet vid normflödet [m/s]: fel över V_MAX, anmärkning över V_ANM


@dataclass
class Vatten:
    tappstallen: dict[str, Tappstalle]
    fordelare: dict[str, Fordelare]
    ror: dict[str, Ror]
    rum: dict[str, Rum]
    modul: dict[str, str]              # tappställets eller rörets id -> rummets namn (matarledningarna: Teknikrum)
    strak: dict[str, Strak]
    utgangar: dict[str, dict[str, int]]    # tappställe -> media -> utgång

    def ande(self, ref: str, media: str) -> Vek:
        """Rörets ände: fördelarens utgång, utrustningens anslutning eller tappställets anslutning."""
        if ref in self.tappstallen:
            return anslutning(self.tappstallen[ref], media)
        kod, _, nr = ref.partition(":")
        if kod in self.fordelare:
            return self.fordelare[kod].utgang(int(nr))
        if kod in UTRUSTNING and nr in UTRUSTNING[kod].anslutningar:
            return UTRUSTNING[kod].anslutningar[nr]
        raise KeyError(ref)

    def vag(self, r: Ror) -> list[Vek]:
        return [self.ande(r.fran, r.media), *r.via, self.ande(r.till, r.media)]

    def stycken(self) -> list[Stycke]:
        return [Stycke(r.id, a, b, r.typ.yttre, r.typ.yttre, True, matt=f"{r.media} {r.typ.matt}")
                for r in self.ror.values() for a, b in zip(self.vag(r), self.vag(r)[1:]) if math.dist(a, b) > 1e-6]

    def genomforingar(self) -> tuple[list[Genomforing], list[str]]:
        return genomforingar(self.stycken())

    def vv_volym(self, tid: str) -> float:
        """Varmvattnets volym från beredaren till tappstället [l]: röret från fördelaren och matarledningen till den."""
        vv = [r for r in self.ror.values() if r.media == "VV"]
        till = next(r for r in vv if r.till == tid)
        fd = till.fran.split(":")[0]
        return sum(langd(self.vag(r)) / 1000 * r.typ.liter_per_m
                   for r in (till, *(m for m in vv if m.till.split(":")[0] == fd)))

    def vv_tid(self, tid: str) -> float:
        """Tiden tills varmvattnet når tappstället vid dess normflöde [s] (volymen från beredaren)."""
        return self.vv_volym(tid) / self.tappstallen[tid].typ.vv

    def kontroll(self) -> tuple[list[str], list[str]]:
        """Fel och anmärkningar: ordningen och referenserna, varje tappställes anslutningar, tiden till varmvatten,
        vattenhastigheterna, fördelarnas utgångar, var rören lämnar stråket, sneda rör, rören som går i varandra och
        genomföringarna."""
        fel: list[str] = []
        anm: list[str] = []
        fel += [f"{t}: inte i tappställenas ordning (teknikrum.ORDNING)" for t in self.tappstallen
                if t not in teknikrum.ORDNING]
        fel += [f"{t}: i tappställenas ordning men finns inte" for t in teknikrum.ORDNING if t not in self.tappstallen]
        for r in self.ror.values():
            for ref in (r.fran, r.till):
                try:
                    self.ande(ref, r.media)
                except (KeyError, ValueError):
                    fel.append(f"{r.id}: okänd ände {ref}")
        if fel:
            return fel, anm
        for t in self.tappstallen.values():
            for media, flode in (("KV", t.typ.kv), ("VV", t.typ.vv)):
                n = sum(1 for r in self.ror.values() if r.till == t.id and r.media == media)
                if flode > 0 and n != 1 or flode == 0 and n:
                    fel.append(f"{t.id}: {n} rör med {media} (normflöde {flode:g} l/s)")
            if t.typ.vv > 0 and any(r.till == t.id and r.media == "VV" for r in self.ror.values()):
                s, v = self.vv_tid(t.id), self.vv_volym(t.id)
                txt = f"{t.id}: varmvatten efter {s:.1f} s vid {t.typ.vv:g} l/s ({v:.2f} l från beredaren)"
                if s > VV_TID:
                    fel.append(f"{txt}, högst {VV_TID:g} s: kortare eller klenare rör, eller varmvattencirkulation")
                elif s > 0.8 * VV_TID:
                    anm.append(txt)
            for r in self.ror.values():
                if r.till == t.id:
                    q = t.typ.kv if r.media == "KV" else t.typ.vv
                    v = q * 1000.0 / r.typ.area
                    (fel if v > V_MAX else anm if v > V_ANM else []).append(
                        f"{r.id}: {v:.1f} m/s i {r.typ.matt} vid {q:g} l/s")
        for fd in self.fordelare.values():
            anv = [int(ref.split(":")[1]) for r in self.ror.values() for ref in (r.fran, r.till)
                   if ref.split(":")[0] == fd.id]
            for n in sorted(set(anv)):
                if anv.count(n) > 1:
                    fel.append(f"{fd.id}: utgång {n} används av {anv.count(n)} rör")
            if fd.utgangar > fd.typ.utgangar:
                fel.append(f"{fd.id}: {fd.utgangar} utgångar men fördelaren har {fd.typ.utgangar}")
        for tid, utg in self.utgangar.items():
            if len(utg) == 2:
                avvik = [_avvik(self.vag(self.ror[f"{tid}-{m}"])) for m in ("KV", "VV")]
                if math.dist(avvik[0], avvik[1]) < FIL - 1.0:
                    fel.append(f"{tid}: kallt och varmt lämnar stråket på samma ställe (vänd golvdosan eller ange "
                               f"via)")
        for r in self.ror.values():
            for a, b in zip(self.vag(r), self.vag(r)[1:]):
                if sum(abs(a[i] - b[i]) > 0.5 for i in range(3)) > 1:
                    anm.append(f"{r.id}: snett stycke från ({_xyz(a)}) till ({_xyz(b)})")
        fel += self._i_varandra()
        fel += self.genomforingar()[1]
        return fel, anm

    def _i_varandra(self) -> list[str]:
        """Rör som går i varandra: avståndet mellan två styckens mittlinjer mindre än summan av radierna."""
        bitar = [(r.id, a, b, r.typ.yttre / 2) for r in self.ror.values()
                 for a, b in zip(self.vag(r), self.vag(r)[1:]) if math.dist(a, b) > 1e-6]
        ut = set()
        for i, (ra, a0, a1, rad_a) in enumerate(bitar):
            for rb, b0, b1, rad_b in bitar[i + 1:]:
                if ra == rb:
                    continue
                d = _avstand(a0, a1, b0, b1)
                if d < rad_a + rad_b - 0.5:
                    ut.add(f"{ra} och {rb} går i varandra ({d:.0f} mm mellan mittlinjerna)")
        return sorted(ut)

    def utdrag(self) -> dict[str, object]:
        """Allt som ritningarna behöver, som JSON: rummen, tappställena, fördelarna, rören, utrustningen, stråken,
        nivåerna och genomföringarna."""
        ror_ = {}
        for r in self.ror.values():
            v = self.vag(r)
            ror_[r.id] = {"typ": r.typ.namn, "matt": r.typ.matt, "yttre": r.typ.yttre, "media": r.media,
                          "fran": r.fran, "till": r.till, "modul": self.modul[r.id], "vag": [list(p) for p in v],
                          "langd": langd(v), "volym": langd(v) / 1000 * r.typ.liter_per_m}
        utg = {t: (min(u.values()), teknikrum.ORDNING[t][0]) for t, u in self.utgangar.items()}
        return {"rum": {k: {"namn": x.namn, "plan": x.plan} for k, x in self.rum.items()},
                "tappstallen": {t.id: {"typ": t.typ.namn, "symbol": t.typ.symbol, "kv": t.typ.kv, "vv": t.typ.vv,
                                       "dosa": t.dosa.namn, "slag": t.dosa.slag, "punkt": list(t.lage.punkt),
                                       "normal": list(t.lage.normal), "rum": self.modul[t.id], "ror": t.ror.matt,
                                       "utgang": ", ".join(f"{m} {n}" for m, n in self.utgangar.get(t.id, {}).items()),
                                       "strak": utg[t.id][1] if t.id in utg else None,
                                       "vv_tid": self.vv_tid(t.id) if t.typ.vv > 0 else 0.0,
                                       "vv_volym": self.vv_volym(t.id) if t.typ.vv > 0 else 0.0}
                                for t in self.tappstallen.values()},
                "fordelare": {f.id: {"typ": f.typ.namn, "media": f.media, "start": list(f.utgang(0)),
                                     "slut": list(f.utgang(f.utgangar + 1)), "utgangar": f.utgangar}
                              for f in self.fordelare.values()},
                "utrustning": {u.id: {"namn": u.namn, "punkt": list(u.lage.punkt), "normal": list(u.lage.normal),
                                      "yta": u.lage.yta, "matt": list(u.matt)} for u in UTRUSTNING.values()},
                "strak": {k: [list(p) for p in s.punkter] for k, s in self.strak.items()},
                "nivaer": {"plan 1:s golv": PLAN[1], "rören i bjälklaget": Z_ROR, "källarens tak": KALLARTAK,
                           "källarens golv": PLAN[0]},
                "ror": ror_,
                "genomforingar": [{"del": x.del_, "atgard": x.atgard, "punkt": list(x.punkt), "matt": x.matt,
                                   "element": x.element} for x in self.genomforingar()[0]]}


def langd(vag: list[Vek]) -> float:
    return sum(math.dist(a, b) for a, b in zip(vag, vag[1:]))


def _xyz(p: Vek) -> str:
    return ", ".join(f"{c:.0f}" for c in p)


def _avstand(a0: Vek, a1: Vek, b0: Vek, b1: Vek) -> float:
    """Kortaste avståndet mellan två sträckor i rummet."""
    u = [a1[i] - a0[i] for i in range(3)]
    v = [b1[i] - b0[i] for i in range(3)]
    w = [a0[i] - b0[i] for i in range(3)]
    a, b, c = sum(x * x for x in u), sum(x * y for x, y in zip(u, v)), sum(y * y for y in v)
    d, e = sum(x * y for x, y in zip(u, w)), sum(x * y for x, y in zip(v, w))
    nam = a * c - b * b
    s_n, s_d, t_n, t_d = 0.0, nam, 0.0, nam
    if nam < 1e-9:
        s_n, s_d, t_n, t_d = 0.0, 1.0, e, c
    else:
        s_n, t_n = b * e - c * d, a * e - b * d
        if s_n < 0:
            s_n, t_n, t_d = 0.0, e, c
        elif s_n > s_d:
            s_n, t_n, t_d = s_d, e + b, c
    if t_n < 0:
        t_n = 0.0
        s_n, s_d = (0.0, s_d) if -d < 0 else ((s_d, s_d) if -d > a else (-d, a))
    elif t_n > t_d:
        t_n = t_d
        s_n, s_d = (0.0, s_d) if -d + b < 0 else ((s_d, s_d) if -d + b > a else (-d + b, a))
    sc = 0.0 if abs(s_n) < 1e-12 else s_n / s_d
    tc = 0.0 if abs(t_n) < 1e-12 else t_n / t_d
    return math.sqrt(sum((w[i] + sc * u[i] - tc * v[i]) ** 2 for i in range(3)))


def _avvik(vag: list[Vek]) -> tuple[float, float]:
    """Där röret lämnar stråket: den sista punkten i bjälklaget innan det går upp eller ned ur det."""
    i = next(i for i in range(len(vag) - 1, 0, -1) if abs(vag[i][2] - Z_ROR) < 1.0)
    return vag[i][0], vag[i][1]


def _filer(tapp: dict[str, Tappstalle]) -> tuple[dict[tuple[str, str], int], dict[str, float]]:
    """Rörens filer från söder (c/c FIL längs V19) i tappställenas ordning, och stråkens mitt (..strak.filer)."""
    rader = [(t, s, ben, {m: till_tappstallet(tapp[t], m)[0][0] for m, q in (("KV", tapp[t].typ.kv),
                                                                              ("VV", tapp[t].typ.vv)) if q > 0})
             for t, (s, ben) in teknikrum.ORDNING.items() if t in tapp]
    return filer(rader, teknikrum.strak, (teknikrum.X["KV"], teknikrum.Y_FIL0), (0.0, 1.0), FIL)


@cache
def vatten() -> Vatten:
    """Tappställena ur rummens moduler, rörens filer och fördelarnas utgångar, rören till tappställena och
    matarledningarna."""
    tapp: dict[str, Tappstalle] = {}
    rum: dict[str, Rum] = {}
    modul: dict[str, str] = {}
    for mod in MODULER:
        rum[mod.RUM.kod] = mod.RUM
        for t in mod.TAPPSTALLEN:
            tapp[t.id] = t
            modul[t.id] = mod.RUM.namn
    filer, mitt = _filer(tapp)
    fd = {m: teknikrum.fordelare(m, typ, tuple(sorted(n for (_, mm), n in filer.items() if mm == m)))
          for m, typ in (("KV", FORDELARE_KV), ("VV", FORDELARE_VV))}
    utgangar: dict[str, dict[str, int]] = {}
    for (t_id, m), n in filer.items():
        utgangar.setdefault(t_id, {})[m] = fd[m].filer.index(n) + 1
    strak = teknikrum.strak(mitt)
    ror_: dict[str, Ror] = {r.id: r for r in teknikrum.matarledningar(fd["KV"], fd["VV"])}
    modul.update({r: "Teknikrum" for r in ror_})
    for t_id, utg in utgangar.items():
        s_id, ben = teknikrum.ORDNING[t_id]
        for r in ror(tapp[t_id], utg, strak[s_id], fd, ben):
            ror_[r.id] = r
            modul[r.id] = modul[t_id]
    return Vatten(tapp, {f.id: f for f in fd.values()}, ror_, rum, modul, strak, utgangar)
