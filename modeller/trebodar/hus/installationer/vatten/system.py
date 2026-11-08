"""Tappvattnet ur modulerna (MODULER): tappställena, rörens filer och fördelarnas utgångar (i tappställenas ordning
teknikrum.ORDNING, och underfördelarnas egna, underfordelare.py), rören från fördelarna till tappställena längs
stråken och matarledningarna, kontrollen, genomföringarna och utdraget för ritningarna (verktyg/modellering:
`./mod vatten`).

Rörens ändar: fördelarnas utgångar ("FD-KV:3", "UF1-KV:2"; utgång 0 och utgången efter den sista är stammens ändar:
underfördelarnas matning går till utgång 0), utrustningen i teknikrummet ("TK-VP:VV-ut", ..teknikrum.UTRUSTNING) och
tappställena (anslutningen i dosan, kallt och varmt).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, replace
from functools import cache
from collections.abc import Callable
from types import ModuleType

from shapely.geometry import LineString, Polygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from ..avlopp.ledningar import ledningar
from ..genomforingar import Genomforing, Stycke, genomforingar
from ..montering import KALLARTAK, PLAN, Vek
from ..teknikrum import UTRUSTNING
from . import teknikrum
from .katalog import FORDELARE_KV, FORDELARE_VV
from ..strak import Strak, filer
from .punkter import FIL, Z_ROR, Fordelare, Ror, Rum, Tappstalle, anslutning, hylsa, ror, ror_hylsa, till_tappstallet
from .rum import badrum, kallare, kok
from .underfordelare import ROR_MATNING, UNDERFORDELARE, Underfordelare

MODULER: tuple[ModuleType, ...] = (badrum, kok, kallare)

VV_TID = 10.0                  # varmvatten vid tappstället inom 10 s vid normflödet (BBR 6:62, Säker Vatten) [s]
V_MAX, V_ANM = 2.5, 2.0        # vattenhastighet vid normflödet [m/s]: fel över V_MAX, anmärkning över V_ANM


@dataclass
class Vatten:
    tappstallen: dict[str, Tappstalle]
    fordelare: dict[str, Fordelare]    # huvudfördelarna (FD-KV, FD-VV) och underfördelarnas stammar (UF1-KV …)
    ror: dict[str, Ror]
    rum: dict[str, Rum]
    modul: dict[str, str]              # tappställets eller rörets id -> rummets namn (matarledningarna: Teknikrum)
    strak: dict[str, Strak]
    utgangar: dict[str, tuple[str, dict[str, int]]]    # tappställe eller underfördelare -> (fördelare: "FD", "UF1",
    #                                                    media -> utgång)
    underfordelare: dict[str, Underfordelare]

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
        """Genomföringarna (..genomforingar); kopparrören genom bjälklaget går i sina ingjutna hylsor."""
        ut, fel = genomforingar(self.stycken())
        hylsor = {f"{t.id}-{m}": t.dosa for t in self.tappstallen.values() if t.dosa.slag == "hylsa"
                  for m in ("KV", "VV")}
        return [replace(g, atgard=f"hylsa Ø{g_d.b:g} ingjuten mellan armeringsjärnen (PP-avloppsrör), kopparröret "
                                  f"rakt upp genom den", matt=f"Ø{g_d.b:g}")
                if (g_d := hylsor.get(g.element)) and g.del_ == "Mellanbjälklaget" else g for g in ut], fel

    def hylsor(self) -> list[tuple[str, str, tuple[float, float], float]]:
        """De ingjutna hylsorna i mellanbjälklaget: rörets id, tappstället, mitten i plan och diametern."""
        return [(f"{t.id}-{m}", t.id, hylsa(t, m), t.dosa.b) for t in self.tappstallen.values()
                if t.dosa.slag == "hylsa" for m, q in (("KV", t.typ.kv), ("VV", t.typ.vv)) if q > 0]

    def vv_volym(self, tid: str) -> float:
        """Varmvattnets volym från beredaren till tappstället [l]: röret från fördelaren och rören uppströms till den
        (en underfördelares matning och matarledningen till huvudfördelaren)."""
        vv = [r for r in self.ror.values() if r.media == "VV"]
        r: Ror | None = next(r for r in vv if r.till == tid)
        summa = 0.0
        while r is not None:
            summa += langd(self.vag(r)) / 1000 * r.typ.liter_per_m
            fd = r.fran.split(":")[0]
            r = next((m for m in vv if m.till.split(":")[0] == fd), None)
        return summa

    def vv_tid(self, tid: str) -> float:
        """Tiden tills varmvattnet når tappstället vid dess normflöde [s] (volymen från beredaren)."""
        return self.vv_volym(tid) / self.tappstallen[tid].typ.vv

    def kontroll(self) -> tuple[list[str], list[str]]:
        """Fel och anmärkningar: ordningen och referenserna, varje tappställes anslutningar, tiden till varmvatten,
        vattenhastigheterna, fördelarnas utgångar, var rören lämnar stråket, sneda rör, rören som går i varandra och
        genomföringarna."""
        fel: list[str] = []
        anm: list[str] = []
        ordningar: dict[str, dict[str, tuple[str | None, int | None]]] = {
            "teknikrum.ORDNING": dict(teknikrum.ORDNING),
            **{f"{u.id}:s ordning": dict(u.ordning) for u in self.underfordelare.values()}}
        fel += [f"{t}: i {n} tappställenas ordningar" for t in self.tappstallen
                if (n := sum(t in o for o in ordningar.values())) != 1]
        fel += [f"{t}: i {k} men finns inte" for k, o in ordningar.items() for t in o
                if t not in self.tappstallen and t not in self.underfordelare]
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
        for u in self.underfordelare.values():                 # matningen vid det dimensionerande flödet
            for media, q in u.flode:
                r = self.ror[f"{u.id}-{media}"]
                v = q * 1000.0 / r.typ.area
                (fel if v > V_MAX else anm if v > V_ANM else []).append(
                    f"{r.id}: {v:.1f} m/s i {r.typ.matt} vid {q:g} l/s (dimensionerande flöde)")
        for fd in self.fordelare.values():
            anv = [int(ref.split(":")[1]) for r in self.ror.values() for ref in (r.fran, r.till)
                   if ref.split(":")[0] == fd.id]
            for n in sorted(set(anv)):
                if anv.count(n) > 1:
                    fel.append(f"{fd.id}: utgång {n} används av {anv.count(n)} rör")
            if fd.utgangar > fd.typ.utgangar:
                fel.append(f"{fd.id}: {fd.utgangar} utgångar men fördelaren har {fd.typ.utgangar}")
        for tid, (_, utg) in self.utgangar.items():
            if len(utg) == 2 and (tid not in self.tappstallen or self.tappstallen[tid].dosa.slag != "hylsa"):
                avvik = [_avvik(self.vag(self.ror[f"{tid}-{m}"])) for m in ("KV", "VV")]
                if math.dist(avvik[0], avvik[1]) < FIL - 1.0:
                    fel.append(f"{tid}: kallt och varmt lämnar stråket på samma ställe (vänd golvdosan eller ange "
                               f"via)")
        for r in self.ror.values():
            for a, b in zip(self.vag(r), self.vag(r)[1:]):
                if abs(a[2] - b[2]) > 0.5 and math.hypot(a[0] - b[0], a[1] - b[1]) > 0.5:     # i plan får de svepa
                    anm.append(f"{r.id}: snett stycke från ({_xyz(a)}) till ({_xyz(b)})")
        for r in self.ror.values():                         # rör-i-rör: skarpa böjar högst BOJAR_MAX (#87)
            if r.typ.skydd > 0 and (skarpa := bojar(self.vag(r))) > BOJAR_MAX + 1e-6:
                anm.append(f"{r.id}: de skarpa böjarna är {skarpa:.0f}° sammanlagt (mer än {BOJAR_MAX:.0f}°: svårt att byta "
                           f"röret), svepen {bojar(self.vag(r), svep=True):.0f}°")
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
                          "koppar": r.typ.kod.startswith("CU"),
                          "fran": r.fran, "till": r.till, "modul": self.modul[r.id], "vag": [list(p) for p in v],
                          "langd": langd(v), "volym": langd(v) / 1000 * r.typ.liter_per_m}
        ordning = {**teknikrum.ORDNING, **{t: s for u in self.underfordelare.values() for t, s in u.ordning}}

        def utgang(tid: str) -> str:
            fd, utg = self.utgangar.get(tid, ("FD", {}))
            txt = ", ".join(f"{m} {n}" for m, n in utg.items())
            return txt if fd == "FD" else f"{fd}: {txt}"

        def stam(f: Fordelare) -> dict[str, object]:
            return {"typ": f.typ.namn, "media": f.media, "start": list(f.utgang(0)),
                    "slut": list(f.utgang(f.utgangar + 1)), "utgangar": f.utgangar}

        return {"rum": {k: {"namn": x.namn, "plan": x.plan} for k, x in self.rum.items()},
                "tappstallen": {t.id: {"typ": t.typ.namn, "symbol": t.typ.symbol, "kv": t.typ.kv, "vv": t.typ.vv,
                                       "dosa": t.dosa.namn, "slag": t.dosa.slag, "punkt": list(t.lage.punkt),
                                       "normal": list(t.lage.normal), "rum": self.modul[t.id], "ror": t.ror.matt,
                                       "utgang": utgang(t.id), "strak": ordning[t.id][0] if t.id in ordning else None,
                                       "vv_tid": self.vv_tid(t.id) if t.typ.vv > 0 else 0.0,
                                       "vv_volym": self.vv_volym(t.id) if t.typ.vv > 0 else 0.0}
                                for t in self.tappstallen.values()},
                "fordelare": {f.id: stam(f) for f in self.fordelare.values() if f.id.split("-")[0] == "FD"},
                "underfordelare": {u.id: {"namn": u.namn, "rum": u.rum, "matning": utgang(u.id),
                                          "strak": teknikrum.ORDNING[u.id][0], "stammar": {
                                              m: stam(self.fordelare[f"{u.id}-{m}"]) for m in u.medier},
                                          "tappstallen": [t for t, _ in u.ordning],
                                          "flode": dict(u.flode)} for u in self.underfordelare.values()},
                "utrustning": {u.id: {"namn": u.namn, "punkt": list(u.lage.punkt), "normal": list(u.lage.normal),
                                      "yta": u.lage.yta, "matt": list(u.matt)} for u in UTRUSTNING.values()},
                "strak": {k: [list(p) for p in s.punkter] for k, s in self.strak.items()},
                "nivaer": {"plan 1:s golv": PLAN[1], "rören i bjälklaget": Z_ROR, "källarens tak": KALLARTAK,
                           "källarens golv": PLAN[0]},
                "ror": ror_,
                "genomforingar": [{"del": x.del_, "atgard": x.atgard, "punkt": list(x.punkt), "matt": x.matt,
                                   "element": x.element} for x in self.genomforingar()[0]],
                "hylsor": [{"ror": r, "tappstalle": t, "punkt": list(p), "d": d} for r, t, p, d in self.hylsor()]}


SPEL_AVLOPP = 10.0                      # rörens svep i bjälklaget fria från avloppsledningarna


@cache
def avloppen_i_nivan(r: float) -> BaseGeometry:
    """Avloppsledningarna som går genom rörens nivå i bjälklaget, i plan, förstorade med deras och rörets radie och
    SPEL_AVLOPP (svepen i hörnen går runt dem)."""
    g = []
    for led in ledningar().values():
        for a, b in zip(led.vag, led.vag[1:]):
            if min(a[2], b[2]) - led.d / 2 < Z_ROR + r and max(a[2], b[2]) + led.d / 2 > Z_ROR - r:
                g.append(LineString([a[:2], b[:2]]).buffer(led.d / 2 + r + SPEL_AVLOPP))
    return unary_union(g) if g else Polygon()


BOJAR_MAX = 270.0
SVEP_STEG = 20.0                        # riktningsändringar upp till så mycket i plan är svepens bågar [°]


def bojar(vag: list[Vek], svep: bool = False) -> float:
    """Summan av rörets skarpa böjar [°] (eller med svep bara svepen: de små riktningsändringarna i plan längs
    bågarna i bjälklaget)."""
    s = 0.0
    for a, b, c in zip(vag, vag[1:], vag[2:]):
        u = [y - x for x, y in zip(a, b)]
        w = [y - x for x, y in zip(b, c)]
        nu, nw = math.hypot(*u), math.hypot(*w)
        if nu < 1e-6 or nw < 1e-6:
            continue
        v = math.degrees(math.acos(max(-1.0, min(1.0, sum(x * y for x, y in zip(u, w)) / (nu * nw)))))
        i_plan = abs(u[2]) < 0.5 and abs(w[2]) < 0.5
        if (i_plan and v <= SVEP_STEG) == svep:
            s += v
    return s


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


def _filer(tapp: dict[str, Tappstalle], ordning: dict[str, tuple[str, int | None]],
           strak: Callable[[dict[str, float]], dict[str, Strak]], borjan: tuple[float, float],
           riktning: tuple[float, float]) -> tuple[dict[tuple[str, str], int], dict[str, float]]:
    """Rörens filer längs fördelaren (c/c FIL från borjan) i tappställenas ordning, och stråkens mitt (..strak.filer)."""
    rader = [(t, s, ben, {m: till_tappstallet(tapp[t], m)[0][0] for m, q in (("KV", tapp[t].typ.kv),
                                                                              ("VV", tapp[t].typ.vv)) if q > 0})
             for t, (s, ben) in ordning.items() if t in tapp]
    return filer(rader, strak, borjan, riktning, FIL)


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
    uf = {u.id: u for u in UNDERFORDELARE}
    huvud = {**tapp, **{u.id: u.inlopp() for u in uf.values()}}         # underfördelarnas inlopp som tappställen
    filer_, mitt = _filer(huvud, teknikrum.ORDNING, teknikrum.strak, (teknikrum.X["KV"], teknikrum.Y_FIL0), (0.0, 1.0))
    fd = {m: teknikrum.fordelare(m, typ, tuple(sorted(n for (_, mm), n in filer_.items() if mm == m)))
          for m, typ in (("KV", FORDELARE_KV), ("VV", FORDELARE_VV))}
    utgangar: dict[str, tuple[str, dict[str, int]]] = {}
    for (t_id, m), n in filer_.items():
        utgangar.setdefault(t_id, ("FD", {}))[1][m] = fd[m].filer.index(n) + 1
    strak = teknikrum.strak(mitt)
    ror_: dict[str, Ror] = {r.id: r for r in teknikrum.matarledningar(fd["KV"], fd["VV"])}
    modul.update({r: "Teknikrum" for r in ror_})
    for t_id, (_, utg) in list(utgangar.items()):
        s_id, ben = teknikrum.ORDNING[t_id]
        for r in ror(huvud[t_id], utg, strak[s_id], fd, ben, avloppen_i_nivan(huvud[t_id].ror.yttre / 2)):
            if t_id in uf:                                              # matningen till underfördelarens utgång 0
                r = replace(r, till=f"{t_id}-{r.media}:0", typ=ROR_MATNING.get((t_id, r.media), r.typ))
            ror_[r.id] = r
            modul[r.id] = uf[t_id].rum if t_id in uf else modul[t_id]
    fordelare = {f.id: f for f in fd.values()}
    for u in uf.values():
        ordning = dict(u.ordning)
        i_strak = {t: (s, b) for t, (s, b) in ordning.items() if s is not None}
        filer_u, mitt_u = (_filer(tapp, i_strak, u.strak, u.borjan, (u.riktning[0], u.riktning[1])) if i_strak
                           else ({}, {}))
        for t_id, (u_s, _) in ordning.items():           # kopparrören till hylsorna: filerna efter stråkets
            if u_s is None and t_id in tapp:
                for m, q in (("VV", tapp[t_id].typ.vv), ("KV", tapp[t_id].typ.kv)):
                    if q > 0:
                        filer_u[(t_id, m)] = len(filer_u)
        fd_u = {m: u.fordelare(m, tuple(sorted(n for (_, mm), n in filer_u.items() if mm == m))) for m in u.medier}
        for (t_id, m), n in filer_u.items():
            utgangar.setdefault(t_id, (u.id, {}))[1][m] = fd_u[m].filer.index(n) + 1
        strak_u = u.strak(mitt_u)
        strak.update(strak_u)
        for t_id in ordning:
            if t_id in tapp:
                u_s, u_ben = ordning[t_id]
                rr = (ror(tapp[t_id], utgangar[t_id][1], strak_u[u_s], fd_u, u_ben) if u_s is not None
                      else ror_hylsa(tapp[t_id], utgangar[t_id][1], fd_u))
                for r in rr:
                    ror_[r.id] = r
                    modul[r.id] = modul[t_id]
        fordelare.update({f.id: f for f in fd_u.values()})
    return Vatten(tapp, fordelare, ror_, rum, modul, strak, utgangar, uf)
