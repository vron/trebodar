"""Stommens förankring i mellanbjälklaget (#88, K-04): betongbultar genom syllarna, vinkelbeslag och
förankringsbeslag vid reglarna och stolparna som lyfter, ned i plattan.

Syllarna. Varje syll på plattan har en bult högst KANT_SYLL från vardera änden och högst CC isär, i facken mellan
reglarna (bulten dras uppifrån). I innerväggarna sitter bulten i syllens mitt. Ytterväggarnas syll står 30 mm utanför
plattans kant (K-05; också vid plattan på marks fria kanter, där L-elementens rygg är kantisoleringen), så där sitter
bulten FRAN_INSIDAN från syllens insida: kantavståndet till betongen blir då 45 mm.

Vinkelbeslagen (K-04:s förankring). Där syllen, bultarna och skruvarna snett genom regelns fot inte räcker får regeln
eller stolpen vid upplaget (VINKELBESLAG_PA) ett eller två vinkelbeslag ABR10525 (byggdelar/beslag.py) på sina fria
sidor längs väggen, fullt utskruvade i regeln och syllen, med en eller två betongbultar genom beslagets hål, syllen
och plattan. Beslagen sitter på regelns sidor, i ytterväggarna närmast insidan; räcker regelgruppens sidor inte (i
hörnen) sitter beslaget på den vinkelräta väggens regel intill. Fristående stolpar får beslagen på sina sidor, på
plattan. Når ett hål inte betongen med KANT till kanten (ytterväggarnas yttre hål) borras bulten snett inåt, SNETT
från lodlinjen, med snedbricka. Förankringsbeslaget WHT340 (FORANKRINGSBESLAG_PA) sitter på regelgruppens insida
(K-04:s särskilda förankring), på plattan med ankaret M16 innanför väggen.

Bultarna borras efter gjutningen, minst FRITT från alla rör i plattan (elens, tappvattnets med hylsorna, avloppets
och golvvärmens): syllens bult flyttas längs syllen till närmaste fria läge i ett fack utanför beslagen, och
beslagen väljer en sida där bultarna är fria. AR-03.4 visar dem, och gjutningens kontroll prövar avståndet.
Huvudstolpen LN1_3 förankras för lyftet med en bult genom vart och ett av sina vinkelbeslag vid foten (ln1_3.BULTAR,
K-03).

Beslagen är valda i K-04, som läser dem ur bärverket och prövar dem: ändras stommen, räknas K-04 om med ./bygg K-04,
som visar de beslag som behövs.
"""
from __future__ import annotations

import math
import warnings
from dataclasses import dataclass
from functools import cache
from typing import Any

import numpy as np

from shapely.geometry import LineString, Point, Polygon, box as rektangel
from shapely.ops import unary_union

from modellering import Del, Montage, Placering, cylinder
from modellering.form import i_foraldern, omslutande

from trebodar import skelett as S
from trebodar.byggdelar.beslag import (ABR_A, ABR_B, ABR_BREDD, ABR_T, BULT_U, BULT_V, WHT_ANKARE, WHT_B, WHT_D,
                                       WHT_BOTTEN, WHT_H, WHT_P, forankringsbeslag, vinkelbeslag)
from trebodar.material import BETONGBULT, FORANKRINGSBESLAG, VINKELBESLAG
from trebodar.hus.fonster_och_dorrar import fonster_och_dorrar
from trebodar.hus.inredning import inredning
from trebodar.hus.invandigt import invandigt
from trebodar.hus.installationer.avlopp.ledningar import ledningar as avloppets
from trebodar.hus.installationer.el.installation import installation
from trebodar.hus.installationer.golvvarme.system import golvvarme
from trebodar.hus.installationer.vatten.system import vatten
from trebodar.hus.stomme import lagen
from trebodar.hus.stomme.prefab.stolpar import ln1_3

CC = 1200.0                 # bultarna högst så långt isär längs syllen [mm]
KANT_SYLL = 300.0           # och högst så långt från syllens ände
FRAN_INSIDAN = 20.0         # ytterväggarnas bult från syllens insida [mm]
FRITT_REGEL = 25.0          # bulten minst så långt från en regel och ett beslag (brickan och mutterdragaren)
D, DJUP, OVER = 12.0, 90.0, 15.0     # bultens diameter, djup i betongen och utstick över syllen (bricka och mutter)
SYLL_H = 45.0               # syllens höjd
FRITT = 50.0                # bulten minst så långt från rören i plattan [mm] (som AR-03.4:s gröna)
KANT = 35.0                 # bulten minst så långt från betongens kant i plattans överkant, annars snett inåt
SNETT = (45.0, 60.0)        # de sneda bultarnas vinklar från lodlinjen [°], den minsta som räcker
WHT_DJUP, WHT_OVER = 110.0, 30.0     # förankringsbeslagets ankare M16: i betongen och över bottenplattan
UNDER_SKIVAN = 12.0         # beslaget får gå så långt ut under den inre skivan (SKIVOR_UNDER) i de smala väggarna
SKIVOR_UNDER = frozenset({"OSB", "Plywood", "Bräda"})
ISOLERING = frozenset({"Mineralull", "Träfiberisolering"})
GLID = 2.5                  # fristående stolpar: beslaget flyttas längs sidan i steg om GLID, bort från hindren

# vinkelbeslagen (K-04): regeln eller stolpen vid upplaget -> (beslag, bultar per beslag)
VINKELBESLAG_PA: dict[str, tuple[int, int]] = {
    "LA5-1": (1, 1), "1NO-R01": (2, 1), "1NO-R05": (2, 1), "1SO-R09": (1, 1), "1NV-R01": (1, 1), "1NV-R07": (1, 1),
    "LA1-1": (1, 1), "2NO-R11": (2, 1), "2NO-R14": (1, 1), "LA2-2": (1, 1), "2NV-R03": (2, 1), "3NO-R10": (2, 1),
    "LA8-1": (1, 1), "3SV-R01": (2, 1), "3SV-R05": (2, 2), "3NV-R09": (1, 1), "3NV-R20": (1, 1), "3NV-R24": (1, 1),
    "1A-R02": (1, 1), "1A-R04": (1, 1), "1C-R04": (2, 1), "LN5_2-1": (1, 1), "LN3_1-1": (1, 1), "2B-R03": (1, 1),
    "2B-R05": (1, 1), "2C-R05": (1, 1), "2C-R09": (2, 1), "2C-R11": (2, 1), "LN1_1-R01": (1, 1),
    "LN1_2-R01": (1, 1), "LD4_1-R01": (2, 1), "1B-R01": (1, 1),
}
# förankringsbeslagen WHT340 (K-04) där vinkelbeslagen inte räcker eller inte får plats: på en fri sida av regeln, och
# i ytterväggarna annars på regelgruppens insida, på plattan
FORANKRINGSBESLAG_PA: tuple[str, ...] = (
    "3SV-R08", "1NO-R08", "1NO-R11", "1SO-R01", "1A-R01", "LA10-1", "1SV-R02", "1SV-R04", "1NV-R10", "2SO-R06",
    "2SV-R01", "LD2_4-1", "3NO-R02", "3NO-R07", "3SO-R01", "3SV-R11", "1A-R03", "1B-R02", "LN5_3-1", "1C-R02",
    "1C-R05", "LD2_1-1", "LD2_2-1", "2C-R03", "2C-R08", "LD2_3-1",
)


# upplag där rören i plattan ligger under alla lägen för beslagets bultar: beslaget sitter där ändå, och rören dras om
# runt bultarna när installationernas lägen bestäms (ROR_ARENDE; AR-03.4 visar bultarna som anmärkningar)
ROR_ARENDE = "#114"
ROR_KONFLIKT: dict[str, str] = {
    "1A-R03": "tappvattnet till badrummet korsar under regeln",
    "1C-R02": "elrören G03, G07, G08, G09 och G18 går intill regeln",
    "1B-R01": "elrören G03, G07, G08, G09 och G18 går under syllen",
}
# upplag där beslagen inte får plats utan att invändigt ändras: inget beslag i modellen, och K-04 visar upplaget som
# brist tills det är bestämt (ärendet)
UTAN_PLATS: dict[str, str] = {
    "2SO-R06": "#111",
    "LD4_1-R01": "#112",
    "LN1_1-R01": "#113",
}
# väggar där rören i plattan går längs syllen under alla lägen för dess bult: syllen saknar bulten där, och K-04 räknar
# med de bultar som finns (ROR_ARENDE)
SYLL_ROR_KONFLIKT: dict[str, str] = {
    "1B": "elrören G03, G07, G08, G09 och G18 går under syllen",
}


@dataclass(frozen=True)
class Bult:
    """En betongbult: där den går genom ytan som brickan ligger på (syllens eller beslagets överkant) och riktningen
    nedåt."""
    genom: tuple[float, float, float]
    riktning: tuple[float, float, float]

    def i_plattan(self) -> tuple[float, float]:
        """Där bulten går in i plattans överkant (z 0)."""
        t = -self.genom[2] / self.riktning[2]
        return self.genom[0] + t * self.riktning[0], self.genom[1] + t * self.riktning[1]

    @property
    def lutning(self) -> float:
        """Vinkeln från lodlinjen [°]."""
        return math.degrees(math.acos(min(1.0, -self.riktning[2])))

    @property
    def snett(self) -> bool:
        return self.lutning > 0.5


@dataclass(frozen=True)
class Beslag:
    """Ett beslag: upplagets regel eller stolpe (nyckeln i tabellen), delen det sitter på, elementet, slaget
    (ABR10525 eller WHT340), placeringen (lokalt x ut från sidan, z uppåt) och bultarna."""
    nyckel: str
    del_: str
    element: str
    slag: str
    plac: Placering
    bultar: tuple[Bult, ...]


def _staende() -> list[lagen.Lage]:
    """Stommens stående delar från syllen eller plattan (reglar och stolpar)."""
    return [d for d in lagen.prefab() if d.lada[2] < 60.0 and d.lada[5] - d.lada[2] > 1000.0]


def _intill(a: lagen.Lada, b: lagen.Lada, tol: float = 1.0) -> bool:
    return all(a[i] <= b[i + 3] + tol and b[i] <= a[i + 3] + tol for i in (0, 1))


def _grupp(nyckel: str) -> list[lagen.Lage]:
    """Regeln och delarna som står tätt intill den (samma element först, sedan de andra väggarnas i hörnen)."""
    st = _staende()
    start = next(d for d in st if d.namn == nyckel)
    ut, kö = [start], [start]
    while kö:
        a = kö.pop()
        for b in st:
            if b not in ut and _intill(a.lada, b.lada):
                ut.append(b)
                kö.append(b)
    return sorted(ut, key=lambda d: (d.namn != nyckel, d.element != start.element))


def _ror_fritt(x: float, y: float) -> bool:
    return bool(ror_i_plattan().distance(Point(x, y)) >= D / 2 + FRITT)


def _avstand(a0: np.ndarray, a1: np.ndarray, b0: np.ndarray, b1: np.ndarray) -> float:
    """Det minsta avståndet mellan sträckorna a0–a1 och b0–b1."""
    t = np.linspace(0.0, 1.0, 41)[:, None]
    pa, pb = a0 + t * (a1 - a0), b0 + t * (b1 - b0)
    return float(np.min(np.linalg.norm(pa[:, None, :] - pb[None, :, :], axis=2)))


def _bult(genom: np.ndarray, sidor: list[np.ndarray], syll: Any = None, rorhansyn: bool = True,
          andra: tuple[Bult, ...] = ()) -> Bult | None:
    """Bulten genom punkten: lodrät om den når betongen med KANT till kanten och är fri från rören, annars snett åt
    någon av sidorna (vågräta riktningar, _sidor), med den minsta vinkeln i SNETT som räcker. Står den på en syll
    (syllens yta i plan) går bulten ut genom syllens undersida, och den går minst 2 D från de andra bultarna i samma
    beslag."""
    for v, sida in [(0.0, np.zeros(3))] + [(v, s) for v in SNETT for s in sidor]:
        s, c = math.sin(math.radians(v)), math.cos(math.radians(v))
        r = np.array([s * sida[0], s * sida[1], -c])
        b = Bult((float(genom[0]), float(genom[1]), float(genom[2])), (float(r[0]), float(r[1]), float(r[2])))
        x, y = b.i_plattan()
        spets = np.array([x, y, 0.0]) + DJUP * r
        if syll is not None and not syll.buffer(-D / 2).contains(Point(x, y)):
            continue
        if any(_avstand(np.array(b.genom), spets, np.array(a.genom),
                        np.array([*a.i_plattan(), 0.0]) + DJUP * np.array(a.riktning)) < 2 * D for a in andra):
            continue
        if betongen().contains(Point(x, y).buffer(KANT)) and (not rorhansyn or _ror_fritt(x, y) and
                                                               _ror_fritt(spets[0], spets[1])):
            return b
    return None


def _riktningar(d: lagen.Lage) -> list[np.ndarray]:
    """Sidorna som ett beslag kan sitta på: längs väggen (±u) för väggens delar, alla fyra för fristående stolpar."""
    if d.element in S.VAGGAR:
        u = np.array(S.VAGGAR[d.element].u)
        return [u, -u]
    return [np.array(v) for v in ((1.0, 0.0), (-1.0, 0.0), (0.0, 1.0), (0.0, -1.0))]


def _inat(element: str) -> np.ndarray | None:
    """Ytterväggens riktning in i huset (w), annars None."""
    return np.array([*S.VAGGAR[element].w, 0.0]) if element in S.YTTERVAGGAR else None


def _sidor(element: str) -> list[np.ndarray]:
    """Riktningarna en bult får luta åt: in i huset i ytterväggarna (rakt in, annars snett in längs väggen, förbi
    beslagets andra bult), åt båda håll tvärs innerväggarna, åt alla håll vid fristående stolpar."""
    if element in S.YTTERVAGGAR:
        w, u = np.array([*S.VAGGAR[element].w, 0.0]), np.array([*S.VAGGAR[element].u, 0.0])
        return [w, (w + u) / math.sqrt(2), (w - u) / math.sqrt(2)]
    if element in S.VAGGAR:
        w = np.array([*S.VAGGAR[element].w, 0.0])
        return [w, -w]
    return [np.array(v) for v in ((1.0, 0.0, 0.0), (-1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, -1.0, 0.0))]


def _lada(plac: Placering, x0: float, x1: float, y0: float, y1: float, z0: float, z1: float) -> lagen.Lada:
    p = np.array([plac.punkt((x, y, z)) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)])
    return (*p.min(axis=0), *p.max(axis=0))


def _krock(a: lagen.Lada, b: lagen.Lada, tol: float = 0.5) -> bool:
    return all(a[i] < b[i + 3] - tol and b[i] < a[i + 3] - tol for i in range(3))


@cache
def _inne() -> tuple[tuple[lagen.Lada, float], ...]:
    """Det som står på plattan intill stommen och som beslagen inte får gå in i (invändigt, inredningen, fönstren och
    dörrarna), som lådor upp till förankringsbeslagets höjd, med den tolerans som beslaget får gå in i delen: i de smala
    väggarna går beslaget UNDER_SKIVAN ut under den inre skivan, som fälls ur. Isoleringen skärs ur kring beslagen."""
    ut = []
    for mod in (invandigt, inredning, fonster_och_dorrar):
        for _, d, p in mod.montage().platta():
            b = omslutande(d.form)
            if b is None or d.material.namn in ISOLERING:
                continue
            b = i_foraldern(b, p)
            if b[2] < SYLL_H + WHT_H and b[5] > 0.0:
                ut.append((b, UNDER_SKIVAN + 0.5 if d.material.namn in SKIVOR_UNDER else 0.05))
    return tuple(ut)


def _sida(d: lagen.Lage, n: np.ndarray, bredd: float, inat: np.ndarray | None) -> tuple[np.ndarray, float] | None:
    """Origo i sidan (mitt för beslaget, z 0) och sidans bredd, eller None om delen är för smal för beslaget (mer än
    15 mm på var sida)."""
    x0, y0, _, x1, y1, _ = d.lada
    lo, hi = np.array([x0, y0]), np.array([x1, y1])
    ax = 0 if abs(n[0]) > 0.5 else 1
    tx = 1 - ax
    c = hi[ax] if n[ax] > 0 else lo[ax]
    t0, t1 = lo[tx], hi[tx]
    if t1 - t0 < bredd - 30.0:
        return None
    if inat is not None and abs(inat[tx]) > 0.5 and t1 - t0 >= bredd + 5.0:     # ytterväggen: närmast insidan
        tm = t1 - bredd / 2 if inat[tx] > 0 else t0 + bredd / 2
    else:
        tm = (t0 + t1) / 2
    p = np.zeros(2)
    p[ax], p[tx] = c, tm
    return p, t1 - t0


@dataclass(frozen=True)
class _Slag:
    """Ett beslags mått i det lokala systemet: bredd (y), den liggande skänkelns djup (x), höjd, godset och hålen för
    bultarna (x, y), det inre först."""
    namn: str
    bredd: float
    djup: float
    hojd: float
    gods: float
    hal: tuple[tuple[float, float], ...]


ABR = _Slag("ABR10525", ABR_BREDD, ABR_B, ABR_A, ABR_T, ((BULT_U, -BULT_V), (BULT_U, BULT_V)))
WHT = _Slag("WHT340", WHT_B, WHT_P, WHT_H, WHT_BOTTEN, ((WHT_ANKARE, 0.0),))


@cache
def beslag() -> tuple[Beslag, ...]:
    """Vinkelbeslagen och förankringsbeslagen, med bultarna: på de fria sidorna av regeln eller stolpen vid upplaget
    (och i hörnen den vinkelräta väggens regel), på syllen eller, för de fristående stolparna, på plattan."""
    ut: list[Beslag] = []
    hinder = list(lagen.prefab())
    syllar = [d for d in hinder if d.typ == "S" and d.lada[2] < 5.0]
    staende = [d for d in hinder if d.typ != "S" and d.lada[2] < 60.0 and d.lada[5] - d.lada[2] > 1000.0]
    upptaget: list[lagen.Lada] = []
    fel: list[str] = []

    def framfor(d: lagen.Lage, n: np.ndarray) -> float:
        """Det fria avståndet från delens sida n till nästa stående del framför den."""
        ax = 0 if abs(n[0]) > 0.5 else 1
        lo, hi = d.lada[1 - ax], d.lada[4 - ax]
        yta = d.lada[3 + ax] if n[ax] > 0 else d.lada[ax]
        avst = [(h.lada[ax] - yta) if n[ax] > 0 else (yta - h.lada[3 + ax]) for h in staende
                if h.namn != d.namn and h.lada[4 - ax] > lo + 1.0 and h.lada[1 - ax] < hi - 1.0]
        return min((a for a in avst if a > -1.0), default=math.inf)

    def underlag(d: lagen.Lage, fot: Any, n: np.ndarray, s: _Slag, plattan: bool) -> tuple[float, Any] | None:
        """Överkanten under den liggande skänkeln: en syll under hela dess djup (i de smalare väggarna går beslaget
        ut över syllens sidor, in i skivorna), annars plattan för en del som står på den (eller med plattan). Ger
        överkanten och syllens yta i plan (None på plattan)."""
        ax = 0 if abs(n[0]) > 0.5 else 1
        for sy in syllar:
            r = rektangel(sy.lada[0], sy.lada[1], sy.lada[3], sy.lada[4])
            i = r.intersection(fot)
            if i.area < 1.0:
                continue
            langs = i.bounds[2 + ax] - i.bounds[ax]
            tvars = i.bounds[3 - ax] - i.bounds[1 - ax]
            bredd = sy.lada[4 - ax] - sy.lada[1 - ax]
            return (sy.lada[5], r) if langs >= s.djup - 1.0 and tvars >= min(bredd, s.bredd) - 1.0 else None
        return (0.0, None) if (plattan or d.lada[2] < 1.0) and betongen().contains(fot) else None

    def placera(d: lagen.Lage, n: np.ndarray, s: _Slag, nb: int, egna: set[str], plattan: bool = False,
                rorhansyn: bool = True) -> tuple[Placering, tuple[Bult, ...]] | None:
        """Beslaget på delens sida n med nb bultar, om sidan är fri från de andra delarna (utom egna) och beslagen
        och bultarna når betongen fritt från rören."""
        sida = _sida(d, n, s.bredd, _inat(d.element))
        if sida is None:
            return None
        p0, bredd = sida
        ty = np.array([-n[1], n[0]])
        glid = abs(bredd - s.bredd) / 2 if d.element not in S.VAGGAR else 0.0
        for g in sorted(np.arange(-glid, glid + 1e-6, GLID) if glid > 0 else [0.0], key=abs):
            p = p0 + g * ty
            horn = [p + a * n + b * ty for a in (0.0, s.djup) for b in (-s.bredd / 2, s.bredd / 2)]
            und = underlag(d, Polygon([horn[0], horn[1], horn[3], horn[2]]), n, s, plattan)
            if und is None:
                continue
            z, syll = und
            plac = Placering.axlar((p[0], p[1], z), (n[0], n[1], 0.0), "z")
            env = [_lada(plac, 0.0, s.djup, -s.bredd / 2, s.bredd / 2, 0.0, s.gods),
                   _lada(plac, 0.0, s.gods, -s.bredd / 2, s.bredd / 2, 0.0, s.hojd)]
            if not any(any(h.namn not in egna and _krock(e, h.lada) and not (h.typ == "S" and h.lada[5] <= z + 0.5)
                           for h in hinder) or any(_krock(e, u) for u in upptaget)
                       or any(_krock(e, b, tol) for b, tol in _inne()) for e in env):
                break
        else:
            return None
        inat = _inat(d.element)
        mot = np.zeros(3) if inat is None else inat                    # det inre hålet först
        hal = sorted(s.hal, key=lambda h: -float(np.dot(plac.riktning((0.0, h[1], 0.0)), mot)))
        bultar: list[Bult] = []
        for x, y in hal[:nb]:
            b = _bult(np.array(plac.punkt((x, y, s.gods))), _sidor(d.element), syll, rorhansyn, tuple(bultar))
            if b is None:
                return None
            bultar.append(b)
        upptaget.extend(env)
        return plac, tuple(bultar)

    tabell = ([(k, ABR, a, nb) for k, (a, nb) in VINKELBESLAG_PA.items()]
              + [(k, WHT, 1, 1) for k in FORANKRINGSBESLAG_PA])
    for nyckel, s, antal, nb in tabell:
        satta: list[Beslag] = []
        grupp = _grupp(nyckel)
        rorhansyn = nyckel not in ROR_KONFLIKT
        # först de sidor som lämnar plats för syllens bult framför beslaget, sedan förankringsbeslagets plats på
        # regelgruppens insida och sist de trånga sidorna
        sidor = [(d, n) for d in grupp for n in _riktningar(d)]
        trang = [framfor(d, n) < s.djup + 2 * FRITT_REGEL + D for d, n in sidor]
        for d, n in [c for c, t in zip(sidor, trang) if not t]:
            if len(satta) < antal and (pl := placera(d, n, s, nb, {d.namn}, rorhansyn=rorhansyn)) is not None:
                satta.append(Beslag(nyckel, d.namn, d.element, s.namn, *pl))
        inat = _inat(grupp[0].element)
        if s is WHT and not satta and inat is not None:        # på regelgruppens insida, på plattan
            egen = [g for g in grupp if g.element == grupp[0].element]
            ladar = np.array([g.lada for g in egen])
            hel = lagen.Lage(grupp[0].element, nyckel, (*ladar[:, :3].min(axis=0), *ladar[:, 3:].max(axis=0)))
            pl = placera(hel, inat[:2], s, nb, {g.namn for g in egen}, plattan=True, rorhansyn=rorhansyn)
            if pl is not None:
                satta.append(Beslag(nyckel, nyckel, hel.element, s.namn, *pl))
        for d, n in [c for c, t in zip(sidor, trang) if t]:
            if len(satta) < antal and (pl := placera(d, n, s, nb, {d.namn}, rorhansyn=rorhansyn)) is not None:
                satta.append(Beslag(nyckel, d.namn, d.element, s.namn, *pl))
        if nyckel in ROR_KONFLIKT and satta:
            warnings.warn(f"förankringen vid {nyckel}: bultarna står i rörens zon ({ROR_KONFLIKT[nyckel]})")
        if len(satta) < antal and nyckel in UTAN_PLATS:
            warnings.warn(f"{s.namn} vid {nyckel}: {len(satta)} av {antal} får plats ({UTAN_PLATS[nyckel]})")
        elif len(satta) < antal:
            fel.append(f"{s.namn} vid {nyckel}: {len(satta)} av {antal} får plats")
        ut += satta
    assert not fel, "beslagen får inte plats: " + "; ".join(fel)
    return tuple(ut)


def huvudstolpens_beslag() -> tuple[Beslag, ...]:
    """Huvudstolpens vinkelbeslag vid foten (ln1_3, K-03) med sina bultar, för K-04."""
    return tuple(Beslag("LN1_3-R01", "LN1_3-R01", "LN1_3", "ABR10525", ln1_3.beslag(sida)[1],
                        (Bult((x, y, ln1_3.SYLL_H + ABR_T), (0.0, 0.0, -1.0)),))
                 for sida, (x, y) in zip((-1, 1), ln1_3.BULTAR))


@cache
def betongen() -> Any:
    """Mellanbjälklagets betong i plan, ut till plattans kant (också vid plattan på mark)."""
    return Polygon(S.KONTUR, [S.TRAPPHAL])


def _stycken(vag: Any, r: float) -> list[Any]:
    """Rörets delar i plattan (z −150 … 0) i plan, med radien r."""
    ut = []
    pts = list(vag)
    for a, b in zip(pts, pts[1:]):
        if min(a[2], b[2]) - r < 0.0 and max(a[2], b[2]) + r > -S.H_BJALKLAG:
            g = LineString([a[:2], b[:2]]) if abs(a[0] - b[0]) + abs(a[1] - b[1]) > 1.0 else Point(a[0], a[1])
            ut.append(g.buffer(r))
    return ut


@cache
def ror_i_plattan() -> Any:
    """Alla rör i mellanbjälklaget i plan (med sina radier): elens, tappvattnets (hylsorna), avloppets och
    golvvärmens."""
    g: list[Any] = []
    el = installation()
    for er in el.ror.values():
        g += _stycken(el.mittlinje(er), er.typ.ytterdiameter / 2)
    v = vatten()
    hylsor = {r: d for r, _, _, d in v.hylsor()}
    for vr in v.ror.values():
        g += _stycken(v.vag(vr), hylsor.get(vr.id, vr.typ.yttre) / 2)
    for led in avloppets().values():
        g += _stycken(led.vag, led.d / 2)
    utdrag: Any = golvvarme().utdrag()
    kretsar: dict[str, Any] = utdrag["kretsar"]
    for kr in kretsar.values():
        g += _stycken(kr["vag"], 10.0)
    return unary_union(g)


@cache
def _lagen() -> tuple[tuple[str, Bult], ...]:
    """Syllarnas bultar: (vägg, bult)."""
    ut: list[tuple[str, Bult]] = []
    saknas: list[str] = []
    fotter = []                                    # beslagens liggande skänklar i plan
    for b in beslag():
        x0, y0, _, x1, y1, _ = _lada(b.plac, 0.0, ABR_B if b.slag == "ABR10525" else WHT_P, -ABR_BREDD / 2,
                                     ABR_BREDD / 2, 0.0, 1.0)
        fotter.append(rektangel(x0, y0, x1, y1))
    for kod, v in S.VAGGAR.items():
        delar = lagen.vagg(kod)
        o, u, w = np.array(v.origo), np.array(v.u), np.array(v.w)

        def us(d: lagen.Lage) -> tuple[float, float]:
            x0, y0, _, x1, y1, _ = d.lada
            a, b = sorted(float((np.array(p) - o) @ u) for p in ((x0, y0), (x1, y1)))
            return a, b
        syllar = [(us(d), rektangel(d.lada[0], d.lada[1], d.lada[3], d.lada[4])) for d in delar
                  if d.typ == "S" and d.lada[2] < 5.0]
        reglar = [us(d) for d in delar if d.typ != "S" and d.lada[2] < 60.0 and d.lada[5] - d.lada[2] > 1000.0]
        band = rektangel(*np.min([o, o + v.langd * u + v.tjocklek * w], axis=0),
                         *np.max([o, o + v.langd * u + v.tjocklek * w], axis=0))
        for r in fotter:                           # beslagen på syllen: bulten går utanför dem, som utanför reglarna
            if r.intersects(band):
                x0, y0, x1, y1 = r.bounds
                reglar.append(us(lagen.Lage(kod, "", (x0, y0, 0.0, x1, y1, 0.0))))
        ww = v.tjocklek - FRAN_INSIDAN if kod in S.YTTERVAGGAR else v.tjocklek / 2
        sidor = _sidor(kod)

        def fack(x: float) -> bool:
            return all(x < a - FRITT_REGEL or x > b + FRITT_REGEL for a, b in reglar)

        def bult(x: float, syll: Any) -> Bult | None:
            p = o + x * u + ww * w
            return _bult(np.array([p[0], p[1], SYLL_H]), sidor, syll)

        for (u0, u1), syll in syllar:
            if u1 - u0 < 2 * FRITT_REGEL:
                continue
            n = max(2, int(np.ceil((u1 - u0 - 2 * KANT_SYLL) / CC)) + 1) if u1 - u0 > 2 * KANT_SYLL else 1
            kant = min(KANT_SYLL, (u1 - u0) / 2)
            mal = list(np.linspace(u0 + kant, u1 - kant, n)) if n > 1 else [(u0 + u1) / 2]
            for x in mal:                      # närmaste läge i ett fack, inom syllen
                kand = [k for k in (x + s * d for d in range(0, 400, 5) for s in (1, -1))
                        if u0 + FRITT_REGEL <= k <= u1 - FRITT_REGEL and fack(k)]
                if not kand:                   # ett syllstycke helt under reglar: reglarna håller det
                    continue
                b_ = next((b_ for k in kand if (b_ := bult(k, syll))), None)
                if b_ is not None:
                    ut.append((kod, b_))
                elif kod in SYLL_ROR_KONFLIKT:
                    p = o + x * u + ww * w
                    warnings.warn(f"syllen i {kod} vid ({p[0]:.0f}; {p[1]:.0f}) utan bult: {SYLL_ROR_KONFLIKT[kod]}")
                else:
                    p = o + x * u + ww * w
                    saknas.append(f"{kod} vid ({p[0]:.0f}; {p[1]:.0f})")
    assert not saknas, "syllens bult får inte plats: " + ", ".join(saknas)
    return tuple(dict.fromkeys(ut))


def syllbultar() -> tuple[tuple[str, Bult], ...]:
    """Syllarnas bultar och huvudstolpens (genom dess beslag och syllen): (vägg eller stolpe, bult)."""
    return _lagen() + tuple(("LN1_3", Bult((x, y, ln1_3.SYLL_H + ABR_T), (0.0, 0.0, -1.0))) for x, y in ln1_3.BULTAR)


def rorkonflikter() -> tuple[tuple[str, float, float], ...]:
    """Beslagens bultar i rörens zon (ROR_KONFLIKT), där de går in i plattan: (vägg eller stolpe, x, y)."""
    return tuple(_i_plattan(b.element, bu) for b in beslag() if b.nyckel in ROR_KONFLIKT for bu in b.bultar)


def bultar() -> tuple[tuple[str, float, float], ...]:
    """Alla bultar där de går in i plattan (för AR-03.4 och avståndet till rören): (vägg eller stolpe, x, y)."""
    alla = list(syllbultar()) + [(b.element, bu) for b in beslag() for bu in b.bultar]
    return tuple(_i_plattan(k, bu) for k, bu in alla)


def _i_plattan(kod: str, bu: Bult) -> tuple[str, float, float]:
    x, y = bu.i_plattan()
    return kod, round(x, 1), round(y, 1)


def _bultdel(b: Bult, djup: float, over: float, d: float, namn: str, produkt: str | None) -> tuple[Del, Placering]:
    """Bulten från spetsen djup ned i betongen till over ovanför ytan som brickan ligger på."""
    r = np.array(b.riktning)
    x, y = b.i_plattan()
    spets = np.array([x, y, 0.0]) + djup * r
    langd = float(np.linalg.norm(np.array(b.genom) - spets)) + over
    upp = -r
    tvars = np.cross(upp, (0.0, 0.0, 1.0)) if b.snett else np.array([1.0, 0.0, 0.0])
    plac = Placering.axlar((spets[0], spets[1], spets[2]), (tvars[0], tvars[1], tvars[2]), (upp[0], upp[1], upp[2]))
    return Del(namn, cylinder(d / 2, langd), BETONGBULT, produkt=produkt), plac


def montage() -> Montage:
    m = Montage("Förankring", beskrivning="Betongbultar genom syllarna och vinkel- och förankringsbeslag "
                                          "i mellanbjälklaget (#88, K-04)")
    for i, (_, bu) in enumerate(syllbultar(), 1):
        m.lagg(*_bultdel(bu, DJUP, OVER, D, f"Betongbult M{D:.0f} genom syllen" + (" (snett)" if bu.snett else ""),
                         "BETONGBULT-SYLL"), f"BB{i:03d}")
    nr = {"ABR10525": 0, "WHT340": 0}
    for b in beslag():
        nr[b.slag] += 1
        if b.slag == "ABR10525":
            kort = f"VB{nr[b.slag]:03d}"
            m.lagg(Del("Vinkelbeslag ABR10525", vinkelbeslag(), VINKELBESLAG, produkt="VINKELBESLAG-STOMME"), b.plac,
                   kort)
            for j, bu in enumerate(b.bultar, 1):
                m.lagg(*_bultdel(bu, DJUP, OVER, D, f"Betongbult M{D:.0f} genom beslaget" + (" (snett)" if bu.snett
                                                                                                else ""),
                                 "BETONGBULT-SYLL"), f"{kort}-B{j}")
        else:
            kort = f"FB{nr[b.slag]:03d}"
            m.lagg(Del("Förankringsbeslag WHT340", forankringsbeslag(), FORANKRINGSBESLAG,
                       produkt="FORANKRINGSBESLAG"), b.plac, kort)
            m.lagg(*_bultdel(b.bultar[0], WHT_DJUP, WHT_OVER, WHT_D, f"Ankare M{WHT_D:.0f}", None), f"{kort}-A")
    return m
