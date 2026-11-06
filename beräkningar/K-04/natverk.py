"""Balkmodellen ur modellens bärverk (barverk.json, `./mod barverk` i verktyg/modellering).

Balkmodellen är det bärande systemet som en konstruktör ritar det: varje bärande del en balk längs sin systemlinje,
knutpunkterna där systemlinjerna möts och leder där delar slutar mot andra.

- Delarna: varje virkesdel längre än MIN_LANGD blir en balk längs sin axel (virkets fiberriktning, tvärsnittets
  mitt), med tvärsnittet b × h; nock- och dalbalkarna blir en balk var (limträet med stålplåtarna i full
  samverkan där plåtarna finns, limmade enligt K-01); stålbanden blir dragstänger mellan ändarna; spikplåtar,
  stålplåtar, takstolarnas toppklossar och korta bitar binder ihop delarna som ligger an mot dem.
- Takstolarnas ståndare och spikreglar ingår inte: de sitter där för skivorna och fästs när taket är lagt, så att
  de inte bär takstolen, som är en triangel av diagonaler och underram (K-03).
- Sammanfogade delar: parallella delar som ligger an mot varandra längs en sträcka (reglarna i en stolpe,
  hammarbandet och takstolens underram ovanpå det, ytterbalken på diagonalen, upplagsreglarna längs balkarna) får
  en gemensam systemlinje, den största delens axel, och verkar tillsammans utan samverkan.
- Knutpunkterna: delar som ligger an mot varandra förbinds där deras systemlinjer är närmast varandra, i en nod.
  Noden ligger på den viktigaste delen som går igenom knutpunkten (rang: syll och balk, hammarband, underram och
  fristående stolpar, reglar och diagonaler, takbalkar, övriga), där nästa del som går igenom korsar den; slutar
  alla delar i knutpunkten ligger noden där deras systemlinjer möts. Knutpunkter närmare varandra längs en del än
  halva delens höjd är en knutpunkt, och takstolarnas fötter och topp (spikplåtarna) är en knutpunkt var. Varje del
  är rak mellan sina yttersta knutpunkter. En del som slutar i en knutpunkt förlängs eller kortas längs sin axel
  till noden och har en led där (fria böjrotationer), utom en del som bara sitter i en knutpunkt, som annars kunde
  svänga fritt; där alla delar slutar med leder sitter den viktigaste fast.
- Gavlarna: väggens överkant och takstolens överram hålls raka i sidled av gavelns och takets skivor (bindningar),
  mellan gavelns hörn och mellan takstolens fot och topp.
- Upplagen: delar som står på bjälklaget (syllarna, stolparnas fötter) har låsta förskjutningar i sina noder nära
  bjälklaget (förankrade); reaktionerna är krafterna till bjälklaget och förankringen.
"""
from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

import fem

TOL_KONTAKT = 1.0        # delar närmare än så ligger an mot varandra [mm]
PARALLELL = 0.985        # |cos| för vinkeln mellan axlarna över detta: parallella delar
SAMMA = 15.0             # stationer närmare än så längs en del blir samma nod [mm]
BAND_ANDE = 250.0        # bandets anslutningar inom detta från ändarna [mm]
MIN_LANGD = 100.0        # kortare virkesbitar binder bara ihop (klossar, regelstycken) [mm]
UPPLAG_Z = 1.0           # delar vars underkant ligger högst så här över bjälklaget står på det [mm]
NARA = 400.0             # en knutpunkts nod högst så här långt från knutpunktens stationer [mm]
K_BIND = 1.0e5           # bindningarnas styvhet (gavelns överkant och överram i sidled) [N/mm]
FOT_ZON = 350.0          # takstolens delar som slutar så nära en spikplåt slutar i plåtens knutpunkt (fot, topp) [mm]
TRA = ("C24", "GL30c", "GL30h")
VRID = 0.01              # vridstyvheten i virket: knutpunkterna (spik, skruv, kontakt) överför i stort sett ingen vridning


@dataclass
class Bar:
    nr: int
    namn: str
    grupp: str
    element: str
    typ: str
    stolpe: str | None
    material: str
    slag: str                                   # "balk", "band", "kontakt" eller "utgar" (ingår inte)
    a: np.ndarray                               # systemlinjen
    b: np.ndarray
    ez: np.ndarray                              # tvärsnittets höjdriktning (h)
    bredd: float
    hojd: float
    c: np.ndarray                               # lådan: mitt, axlar (rader), halva mått
    E: np.ndarray
    halv: np.ndarray
    platar: list[tuple[float, float, float, float]] = field(default_factory=list)   # (s0, s1, avstånd, area)
    upplagd: bool = False
    a0: np.ndarray = field(default_factory=lambda: np.zeros(3))    # delens egen axel (systemlinjen före sammanfogningen)
    b0: np.ndarray = field(default_factory=lambda: np.zeros(3))

    @property
    def L(self) -> float:
        return float(np.linalg.norm(self.b - self.a))

    @property
    def langd(self) -> float:
        """Delens egen längd (knäckning)."""
        return float(np.linalg.norm(self.b0 - self.a0))

    @property
    def ex(self) -> np.ndarray:
        return (self.b - self.a) / self.L

    def punkt(self, s: float) -> np.ndarray:
        return self.a + s * self.ex


def rang(b: Bar) -> int:
    """Delens vikt för knutpunkternas lägen (noden ligger på den viktigaste delen som går igenom knutpunkten)."""
    if b.grupp == "balk" or b.typ == "S" and b.grupp != "stolpe":
        return 5
    if b.typ in ("H", "U") or b.grupp == "stolpe" and b.typ == "R":
        return 4
    if b.grupp in ("yttervagg", "innervagg") or b.grupp == "takstol" and b.typ == "D":
        return 3
    if b.grupp in ("takbalk", "takstol"):
        return 2
    return 1


def _lada(d: dict[str, Any]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    R, t = np.array(d["R"]), np.array(d["t"])
    x0, y0, z0, x1, y1, z1 = d["bb"]
    mitt = np.array([(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2])
    return R @ mitt + t, R.T.copy(), np.array([x1 - x0, y1 - y0, z1 - z0]) / 2


def _axel(E: np.ndarray, halv: np.ndarray) -> int:
    """Delens längdaxel: lokala x om den är (nästan) längst, annars den längsta."""
    return 0 if halv[0] >= 0.9 * halv.max() else int(np.argmax(halv))


def _bar(nr: int, d: dict[str, Any], slag: str) -> Bar:
    c, E, halv = _lada(d)
    k = _axel(E, halv)
    ovr = [i for i in range(3) if i != k]
    ib, ih = sorted(ovr, key=lambda i: halv[i])
    a, b = c - E[k] * halv[k], c + E[k] * halv[k]
    return Bar(nr, d["namn"], d["grupp"], d["element"], d["typ"], d["stolpe"], d["material"], slag,
               a, b, E[ih].copy(), 2 * halv[ib], 2 * halv[ih], c, E, halv, a0=a.copy(), b0=b.copy())


def _komposit(nr: int, delar: list[dict[str, Any]]) -> Bar:
    """En nock- eller dalbalk: limträet med plåtarna (s0, s1 längs balken, avståndet från limträets mitt, area)."""
    lt = next(d for d in delar if d["material"].startswith("GL"))
    b = _bar(nr, lt, "balk")
    # lådan runt balkens alla delar i limträets system
    horn = []
    for d in delar:
        c, E, halv = _lada(d)
        for s in np.array(np.meshgrid([-1, 1], [-1, 1], [-1, 1])).T.reshape(-1, 3):
            horn.append(c + (s * halv) @ E)
    P = (np.array(horn) - b.c) @ b.E.T
    lo, hi = P.min(axis=0), P.max(axis=0)
    b.c = b.c + ((lo + hi) / 2) @ b.E
    b.halv = (hi - lo) / 2
    for d in delar:
        if d["material"] != "S355":
            continue
        c, E, halv = _lada(d)
        ext = np.abs(E @ b.ex) @ halv                    # plåtens halva längd längs balken
        s = float((c - b.a) @ b.ex)
        e = float((c - (b.a + s * b.ex)) @ b.ez)          # plåtens läge över limträets mitt
        dims = sorted(2 * halv)
        b.platar.append((s - ext, s + ext, e, dims[0] * dims[1]))
    b.namn = lt["element"]
    return b


def _sekundara(delar: list[Bar]) -> None:
    """Takstolarnas ståndare (R) och spikreglar (X vid sidan av diagonalerna) ingår inte; toppklossarna (K) är en del
    av toppens knutpunkt."""
    diagonaler: dict[str, list[Bar]] = defaultdict(list)
    for b in delar:
        if b.grupp == "takstol" and b.typ == "D":
            diagonaler[b.element].append(b)
    for b in delar:
        if b.grupp != "takstol" or b.slag != "balk":
            continue
        if b.typ == "R":
            b.slag = "utgar"
        elif b.typ == "K":
            b.slag = "kontakt"
        elif b.typ == "X" and all(abs((b.c - d.c) @ np.cross(d.ex, d.ez)) > 30.0 for d in diagonaler[b.element]):
            b.slag = "utgar"


def _obb_kontakt(A: list[Bar], par: np.ndarray, tol: float) -> np.ndarray:
    """Separerande axlar (15 per par) för lådorna: True där lådorna överlappar eller ligger närmare än tol."""
    ca = np.array([A[i].c for i in par[:, 0]])
    cb = np.array([A[j].c for j in par[:, 1]])
    Ea = np.array([A[i].E for i in par[:, 0]])
    Eb = np.array([A[j].E for j in par[:, 1]])
    ha = np.array([A[i].halv for i in par[:, 0]])
    hb = np.array([A[j].halv for j in par[:, 1]])
    axlar = [Ea[:, k] for k in range(3)] + [Eb[:, k] for k in range(3)]
    for k in range(3):
        for m in range(3):
            v = np.cross(Ea[:, k], Eb[:, m])
            n = np.linalg.norm(v, axis=1)
            axlar.append(np.where(n[:, None] > 1e-6, v / np.maximum(n, 1e-12)[:, None], Ea[:, 0]))
    ok = np.ones(len(par), bool)
    d = cb - ca
    for L in axlar:
        ra = np.einsum("pk,pk->p", ha, np.abs(np.einsum("pkj,pj->pk", Ea, L)))
        rb = np.einsum("pk,pk->p", hb, np.abs(np.einsum("pkj,pj->pk", Eb, L)))
        ok &= np.abs(np.einsum("pj,pj->p", d, L)) <= ra + rb + tol
    return ok


def _narmast(a0: np.ndarray, u: np.ndarray, La: float, b0: np.ndarray, v: np.ndarray, Lb: float) -> tuple[float, float]:
    """Parametrarna (s, t) för de närmaste punkterna på sträckorna a0 + s u (0 ≤ s ≤ La) och b0 + t v."""
    w0 = a0 - b0
    b = u @ v
    d, e = u @ w0, v @ w0
    nam = 1 - b * b
    s = (b * e - d) / nam if nam > 1e-12 else 0.0
    s = min(max(s, 0.0), La)
    t = min(max(b * s + e, 0.0), Lb)
    s = min(max(b * t - d, 0.0), La)
    return s, t


def _linjer(a0: np.ndarray, u: np.ndarray, b0: np.ndarray, v: np.ndarray) -> float | None:
    """Parametern s för punkten på linjen a0 + s u som är närmast linjen b0 + t v (None för parallella linjer)."""
    w0 = a0 - b0
    b = u @ v
    nam = 1 - b * b
    if nam < 1e-6:
        return None
    return float((b * (v @ w0) - u @ w0) / nam)


class _Unionfind:
    def __init__(self, n: int = 0) -> None:
        self.p: list[int] = list(range(n))

    def ny(self) -> int:
        self.p.append(len(self.p))
        return len(self.p) - 1

    def hitta(self, i: int) -> int:
        while self.p[i] != i:
            self.p[i] = self.p[self.p[i]]
            i = self.p[i]
        return i

    def forena(self, i: int, j: int) -> None:
        a, b = self.hitta(i), self.hitta(j)
        if a != b:
            self.p[max(a, b)] = min(a, b)


@dataclass
class Natverk:
    delar: list[Bar]
    x: np.ndarray                                # knutpunkternas lägen (en nod per knutpunkt)
    element_del: np.ndarray                      # balkelementens del
    element_s: np.ndarray                        # (m, 2) elementets början och slut längs delen
    stationer: dict[int, list[tuple[float, int]]]  # delens stationer: (läge längs delen, nod)
    modell: fem.Modell
    band: list[int]                              # dragstängernas delar
    nod_delar: list[list[int]]                   # delarna i varje knutpunkt
    ytor: dict[str, Any]
    utelamnade: list[str]                        # delar som inte sitter ihop med det som står på bjälklaget
    sekundara: list[str]                         # takstolarnas ståndare och spikreglar (ingår inte)
    linjer: dict[int, int]                       # delarna som har en annan dels systemlinje -> den delen
    bindningar: list[str]                        # gaveln för varje bindning i modellen (gavelns överkant och överram)


def _sammanfoga(delar: list[Bar], par: np.ndarray) -> dict[int, int]:
    """Parallella delar som ligger an mot varandra längs en sträcka får den största delens systemlinje (dess axel,
    förlängd). Ger delen -> delen vars linje den fått, för de delar som flyttats."""
    uf = _Unionfind(len(delar))
    for i, j in par:
        A, B = delar[i], delar[j]
        if A.slag != "balk" or B.slag != "balk" or abs(A.ex @ B.ex) < PARALLELL:
            continue
        p = sorted(float((q - A.a) @ A.ex) for q in (B.a, B.b))
        if min(p[1], A.L) - max(p[0], 0.0) >= 1.0:              # längs en sträcka, inte ände mot ände
            uf.forena(i, j)
    grupper: dict[int, list[int]] = defaultdict(list)
    for b in delar:
        if b.slag == "balk":
            grupper[uf.hitta(b.nr)].append(b.nr)
    flyttad = {}
    for g in grupper.values():
        if len(g) < 2:
            continue
        k = max(g, key=lambda i: (delar[i].bredd * delar[i].hojd + sum(p[3] for p in delar[i].platar) * 20,
                                  delar[i].L, -i))
        B = delar[k]
        for i in g:
            if i == k:
                continue
            A = delar[i]
            a = B.a + ((A.a - B.a) @ B.ex) * B.ex
            b = B.a + ((A.b - B.a) @ B.ex) * B.ex
            A.a, A.b = a, b
            flyttad[i] = k
    return flyttad


def bygg(fil: Path, material: dict[str, dict[str, float]]) -> Natverk:
    data = json.loads(fil.read_text(encoding="utf-8"))
    z_b = data["z_bjalklag"]
    delar: list[Bar] = []
    balkar: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for d in data["delar"]:
        if d["grupp"] == "balk":
            balkar[d["element"]].append(d)
            continue
        if d["material"] == "Stålband":
            delar.append(_bar(len(delar), d, "band"))
        elif d["material"] in TRA:
            b = _bar(len(delar), d, "balk")
            if b.L < MIN_LANGD:
                b.slag = "kontakt"
            delar.append(b)
        else:                                            # spikplåtar och stålplåtar
            delar.append(_bar(len(delar), d, "kontakt"))
    for el, dd in sorted(balkar.items()):
        delar.append(_komposit(len(delar), dd))
    _sekundara(delar)
    for b in delar:
        zmin = b.c[2] - np.abs(b.E[:, 2]) @ b.halv
        b.upplagd = b.slag == "balk" and b.grupp in ("yttervagg", "innervagg", "stolpe") and zmin <= z_b + UPPLAG_Z

    # kontakter: omslutande lådor (axelparallella) först, sedan lådorna
    med = [b for b in delar if b.slag != "utgar"]
    lo = np.array([b.c - np.abs(b.E.T) @ b.halv for b in med])
    hi = np.array([b.c + np.abs(b.E.T) @ b.halv for b in med])
    I, J = np.triu_indices(len(med), 1)
    m = np.all((lo[I] <= hi[J] + TOL_KONTAKT) & (lo[J] <= hi[I] + TOL_KONTAKT), axis=1)
    idx = np.array([b.nr for b in med])
    par = np.column_stack([idx[I[m]], idx[J[m]]])
    par = par[_obb_kontakt(delar, par, TOL_KONTAKT)]
    linjer = _sammanfoga(delar, par)

    uf = _Unionfind()
    stationer: dict[int, list[tuple[float, int]]] = defaultdict(list)

    def station(b: Bar, s: float) -> int:
        k = uf.ny()
        stationer[b.nr].append((min(max(s, 0.0), b.L), k))
        return k

    kontakter: dict[int, list[int]] = defaultdict(list)           # kontakt -> delar
    parallella: list[tuple[int, int, float, float]] = []
    for i, j in par:
        A, B = delar[i], delar[j]
        if A.slag == "kontakt" or B.slag == "kontakt":
            if A.slag == "kontakt" and B.slag == "kontakt":
                kontakter[i].append(j)
                kontakter[j].append(i)
            elif A.slag == "kontakt":
                kontakter[i].append(j)
            else:
                kontakter[j].append(i)
            continue
        if A.slag == "band" and B.slag == "band":
            continue
        if B.slag == "band":
            A, B = B, A
        if A.slag == "band":
            s, t = _narmast(A.a, A.ex, A.L, B.a, B.ex, B.L)
            if min(s, A.L - s) > BAND_ANDE:
                continue
            s = 0.0 if s < A.L / 2 else A.L
            t = float(np.clip((A.punkt(s) - B.a) @ B.ex, 0.0, B.L))
            uf.forena(station(A, s), station(B, t))
            continue
        if abs(A.ex @ B.ex) < PARALLELL:
            s, t = _narmast(A.a, A.ex, A.L, B.a, B.ex, B.L)
            uf.forena(station(A, s), station(B, t))
            continue
        # parallella: överlappen längs A
        p = sorted(float((q - A.a) @ A.ex) for q in (B.a, B.b))
        s0, s1 = max(p[0], 0.0), min(p[1], A.L)
        if s1 - s0 < 1.0:                                # ände mot ände
            s = s0 if abs(s0) < abs(s0 - A.L) else s1
            t = float(np.clip((A.punkt(s) - B.a) @ B.ex, 0.0, B.L))
            uf.forena(station(A, s), station(B, t))
            continue
        for s in (s0, s1):
            t = float(np.clip((A.punkt(s) - B.a) @ B.ex, 0.0, B.L))
            uf.forena(station(A, s), station(B, t))
        parallella.append((A.nr, B.nr, s0, s1))

    # takstolarnas ståndare: knutpunkter på underramen och diagonalen där ståndarna sitter (gavelns skivor och ståndare
    # håller underramen och överramen i sidled där, se bindningarna nedan)
    ytter = {v["kod"]: np.array([*v["w"], 0.0]) for v in data["vaggar"] if v["yttervagg"]}
    for st_ in delar:
        if st_.slag != "utgar" or st_.typ != "R" or st_.element not in ytter:
            continue
        stol = [b for b in delar if b.slag == "balk" and b.grupp == "takstol" and b.element == st_.element]
        U = [b for b in stol if b.typ == "U"]
        D = [b for b in stol if b.typ == "D"]
        if not U or not D:
            continue
        ned, upp = sorted((st_.a0, st_.b0), key=lambda p: p[2])
        u = U[0]
        d = min(D, key=lambda b: float(np.linalg.norm(b.punkt(float(np.clip((upp - b.a) @ b.ex, 0.0, b.L))) - upp)))
        station(u, float((ned - u.a) @ u.ex))
        station(d, float((upp - d.a) @ d.ex))

    # kontakterna (spikplåtar, stålplåtar, toppklossar, korta bitar): delarna som ligger an mot samma kontakt (eller
    # mot kontakter som ligger an mot varandra) förbinds i kontaktens mitt
    kuf = _Unionfind()
    kid = {k: kuf.ny() for k in kontakter}
    for k, ds in kontakter.items():
        for d in ds:
            if d in kid:
                kuf.forena(kid[k], kid[d])
    grupper: dict[int, list[int]] = defaultdict(list)
    for k in kontakter:
        grupper[kuf.hitta(kid[k])].append(k)
    for ks in grupper.values():
        mitt = np.mean([delar[k].c for k in ks], axis=0)
        medl = sorted({d for k in ks for d in kontakter[k] if delar[d].slag not in ("kontakt", "utgar")})
        stol = any(delar[k].grupp == "takstol" and delar[k].typ == "P" for k in ks)
        nycklar = []
        for d in medl:
            b = delar[d]
            s = float(np.clip((mitt - b.a) @ b.ex, 0.0, b.L))
            if b.slag == "band" or stol and b.grupp == "takstol" and min(s, b.L - s) < FOT_ZON:
                s = 0.0 if s < b.L / 2 else b.L     # bandets ände; takstolens del slutar i spikplåtens knutpunkt
            nycklar.append(station(b, s))
        for k in nycklar[1:]:
            uf.forena(nycklar[0], k)

    # parallella delar: också vid varandras knutpunkter inom överlappen
    for i, j, s0, s1 in parallella:
        A, B = delar[i], delar[j]
        for s, _ in list(stationer[i]):
            if s0 + SAMMA < s < s1 - SAMMA:
                t = float(np.clip((A.punkt(s) - B.a) @ B.ex, 0.0, B.L))
                uf.forena(station(A, s), station(B, t))
        for t, _ in list(stationer[j]):
            s = float((B.punkt(t) - A.a) @ A.ex)
            if s0 + SAMMA < s < s1 - SAMMA:
                uf.forena(station(A, s), station(B, t))

    # stationerna längs varje balk (ändarna alltid), sammanslagna inom SAMMA
    st_del: dict[int, list[tuple[float, int]]] = {}
    for b in delar:
        if b.slag not in ("balk", "band"):
            continue
        st = sorted(stationer[b.nr])
        if b.slag == "balk":
            st = sorted(st + [(0.0, uf.ny()), (b.L, uf.ny())])
        lista: list[tuple[float, int]] = []
        for s_, k in st:
            if lista and s_ - lista[-1][0] < SAMMA:
                uf.forena(lista[-1][1], k)
                continue
            lista.append((s_, k))
        st_del[b.nr] = lista

    # knutpunkterna: en nod per knutpunkt
    def vikt(t: tuple[int, float]) -> tuple[int, float]:
        b = delar[t[0]]
        return rang(b), b.bredd * b.hojd ** 3

    def nodlage(ms: list[tuple[int, float]]) -> tuple[np.ndarray, int]:
        """Noden på den viktigaste delen som går igenom knutpunkten, där nästa del som går igenom korsar den; slutar
        alla delar här: där deras systemlinjer möts. Ger läget och delen som noden ligger på."""
        bl = [(d, s_) for d, s_ in ms if delar[d].slag == "balk"] or ms
        mitt = np.mean([delar[d].punkt(s_) for d, s_ in bl], axis=0)
        genom = [(d, s_) for d, s_ in bl if delar[d].slag == "balk" and SAMMA < s_ < delar[d].L - SAMMA]
        d1, s1 = max(genom or bl, key=vikt)
        if genom:
            b1 = delar[d1]
            korsar = [t for t in genom if abs(delar[t[0]].ex @ b1.ex) < PARALLELL]
            if korsar:
                b2 = delar[max(korsar, key=vikt)[0]]
                s_ = _linjer(b1.a, b1.ex, b2.a, b2.ex)
                if s_ is not None and abs(s_ - s1) < NARA:
                    return b1.a + s_ * b1.ex, d1
            return b1.a + float((mitt - b1.a) @ b1.ex) * b1.ex, d1
        A = np.zeros((3, 3))
        r = np.zeros(3)
        for d, _ in bl:
            b = delar[d]
            M = (np.eye(3) - np.outer(b.ex, b.ex)) * rang(b)
            A += M
            r += M @ b.a
        if np.linalg.cond(A) < 1e6:
            P = np.linalg.solve(A, r)
            if np.linalg.norm(P - mitt) < NARA:
                return P, d1
        return delar[d1].punkt(s1), d1

    # knutpunkter närmare varandra längs en del än halva delens höjd är samma knutpunkt
    for _ in range(10):
        medlemmar: dict[int, list[tuple[int, float]]] = defaultdict(list)
        for d, lista in st_del.items():
            for s_, k in lista:
                medlemmar[uf.hitta(k)].append((d, s_))
        lage = {k: nodlage(ms)[0] for k, ms in medlemmar.items()}
        samma = [(uf.hitta(k0), uf.hitta(k1), s1 - s0, max(SAMMA, 0.5 * delar[d].hojd if delar[d].slag == "balk" else 0.0))
                 for d, lista in st_del.items() for (s0, k0), (s1, k1) in zip(lista, lista[1:])]
        samma = [(p, q) for p, q, ds, tol in samma if p != q and (ds < tol or np.linalg.norm(lage[p] - lage[q]) < tol)]
        if not samma:
            break
        for p, q in samma:
            uf.forena(p, q)

    # varje del rak mellan sina yttersta knutpunkter: noderna som ligger på delen (inte på en viktigare del) flyttas till
    # linjen mellan dem, de viktigaste delarna först (en takstols diagonal mellan foten och toppen, en takbalk mellan
    # upplagen)
    agare = {k: nodlage(ms)[1] for k, ms in medlemmar.items()}
    for b in sorted((b for b in delar if b.slag == "balk"), key=lambda b: (-rang(b), b.nr)):
        rr = [uf.hitta(k) for _, k in st_del[b.nr]]
        ansl = [r for r in rr if len({d for d, _ in medlemmar[r]}) > 1]
        if len(ansl) < 2:
            continue
        P0, P1 = lage[ansl[0]], lage[ansl[-1]]
        d01 = P1 - P0
        if d01 @ d01 < 100.0 ** 2:
            continue
        egna = {b.nr, linjer.get(b.nr, b.nr)}
        for r in set(rr) - {ansl[0], ansl[-1]}:
            if agare[r] in egna:
                lage[r] = P0 + float((lage[r] - P0) @ d01 / (d01 @ d01)) * d01

    nod_av: dict[int, int] = {}
    x, nod_delar, fast = [], [], []
    for k, ms in medlemmar.items():
        nod_av[k] = len(x)
        P = lage[k]
        x.append(P)
        nod_delar.append(sorted({dd for dd, _ in ms}))
        fast.append(any(delar[d].upplagd and delar[d].punkt(s_)[2] < z_b + 100.0 for d, s_ in ms))
    X = np.array(x)
    stationer_ut = {d: [(s_, nod_av[uf.hitta(k)]) for s_, k in lista] for d, lista in st_del.items()}

    # elementen: mellan delens stationer; leder i delens ändar där den sitter i andra delar (inte om delen bara sitter
    # i en knutpunkt, då den annars kunde svänga fritt)
    bi, bj, bz, bsek, eldel, els, li, lj = [], [], [], [], [], [], [], []
    for b in delar:
        if b.slag != "balk":
            continue
        lista = stationer_ut[b.nr]
        anslutna = {n_ for _, n_ in lista if len(nod_delar[n_]) > 1}
        led = len(anslutna) > 1
        mat = material[b.material]
        E, G = mat["E0mean"], mat["Gmean"]
        el = [(sa, p, sb, q) for (sa, p), (sb, q) in zip(lista, lista[1:])
              if p != q and np.linalg.norm(X[q] - X[p]) >= 1.0]
        for n_, (sa, p, sb, q) in enumerate(el):
            A_, Iy, Iz = b.bredd * b.hojd, b.bredd * b.hojd ** 3 / 12, b.hojd * b.bredd ** 3 / 12
            r = min(b.bredd, b.hojd) / max(b.bredd, b.hojd)
            J = min(b.bredd, b.hojd) ** 3 * max(b.bredd, b.hojd) * (1 / 3 - 0.21 * r * (1 - r ** 4 / 12)) * VRID
            Av = 5 / 6 * A_
            if b.platar:
                sm = 0.5 * (sa + sb)
                ns = material["S355"]["E0mean"] / E
                for s0, s1, e, ap in b.platar:
                    if s0 <= sm <= s1:
                        A_ += ns * ap
                        Iy += ns * ap * e ** 2
                        Iz += ns * ap * b.bredd ** 2 / 12
            bi.append(p)
            bj.append(q)
            bz.append(b.ez)
            bsek.append([E, G, A_, Iy, Iz, J, Av, Av, 0.0])
            eldel.append(b.nr)
            els.append((sa, sb))
            # leder i ändarna mot andra delar, och stående delars fötter på bjälklaget (inte inspända)
            li.append(n_ == 0 and (led and len(nod_delar[p]) > 1 or fast[p] and abs(b.ex[2]) > 0.9))
            lj.append(n_ == len(el) - 1 and (led and len(nod_delar[q]) > 1 or fast[q] and abs(b.ex[2]) > 0.9))

    # en knutpunkt där alla delar slutar med leder vore en mekanism: den viktigaste delen sitter fast i den
    ander: dict[int, list[tuple[int, bool]]] = defaultdict(list)
    for e, (p, q) in enumerate(zip(bi, bj)):
        ander[p].append((e, False))
        ander[q].append((e, True))
    for nod, ee in ander.items():
        if fast[nod] or not all(lj[e] if j else li[e] for e, j in ee):
            continue
        e, j = max(ee, key=lambda t: (rang(delar[eldel[t[0]]]), delar[eldel[t[0]]].bredd * delar[eldel[t[0]]].hojd ** 3))
        if j:
            lj[e] = False
        else:
            li[e] = False

    # gavlarna: väggens överkant (hammarbandet och underramen) och takstolens överram (diagonalen och ytterbalken) hålls i
    # sidled av gavelns och takets skivor, raka mellan gavelns hörn och mellan takstolens fötter och topp (förutsättning,
    # K-04); krafterna går till väggarna i hörnen och till takplanet i toppen
    pa_linje: dict[int, list[int]] = defaultdict(list)
    for d, k in linjer.items():
        pa_linje[k].append(d)

    def noder(b: Bar) -> set[int]:
        return {n_ for d in (b.nr, *pa_linje.get(b.nr, [])) for _, n_ in stationer_ut.get(d, [])}
    bind: list[tuple[str, np.ndarray, list[tuple[int, float]]]] = []
    for el, w in ytter.items():
        stol = [b for b in delar if b.slag == "balk" and b.grupp == "takstol" and b.element == el]
        U = [b for b in stol if b.typ == "U"]
        D = [b for b in stol if b.typ == "D"]
        if len(U) != 1 or len(D) != 2:
            continue
        fotter = [stationer_ut[U[0].nr][0][1], stationer_ut[U[0].nr][-1][1]]
        overkant = sorted(noder(U[0]), key=lambda n_: float(X[n_] @ U[0].ex))
        sidor = [(overkant[0], overkant[-1], set(overkant))]
        for d in D:
            nd = [n_ for _, n_ in stationer_ut[d.nr]]
            nedre = min(nd, key=lambda n_: X[n_, 2])
            sidor.append((min(fotter, key=lambda n_: float(np.linalg.norm(X[n_] - X[nedre]))),
                          max(nd, key=lambda n_: X[n_, 2]), noder(d)))
        for A_, B_, nn_ in sidor:
            AB = X[B_] - X[A_]
            for n_ in sorted(nn_ - {A_, B_}):
                t = float((X[n_] - X[A_]) @ AB / (AB @ AB))
                if 1e-3 < t < 1 - 1e-3:
                    bind.append((el, w, [(n_, 1.0), (A_, t - 1.0), (B_, -t)]))

    # band med båda ändarna i knutpunkter med andra delar
    band = []
    for b in delar:
        if b.slag == "band":
            lista = stationer_ut.get(b.nr, [])
            if len(lista) == 2 and lista[0][1] != lista[1][1] and all(len(nod_delar[n_]) > 1 for _, n_ in lista):
                band.append(b.nr)

    # bara det som sitter ihop med upplagen
    nn = len(X)
    grannar: dict[int, set[int]] = defaultdict(set)
    for p, q in zip(bi, bj):
        grannar[p].add(q)
        grannar[q].add(p)
    for d in band:
        p, q = stationer_ut[d][0][1], stationer_ut[d][1][1]
        grannar[p].add(q)
        grannar[q].add(p)
    nada = set(i for i in range(nn) if fast[i])
    stack = list(nada)
    while stack:
        i = stack.pop()
        for j in grannar[i]:
            if j not in nada:
                nada.add(j)
                stack.append(j)
    behall = [e for e in range(len(bi)) if bi[e] in nada]
    utelamnade = sorted({delar[eldel[e]].namn for e in range(len(bi)) if bi[e] not in nada})
    band = [d for d in band if stationer_ut[d][0][1] in nada]
    sel = np.array(behall, int)
    mod = fem.Modell(x=X, bi=np.array(bi)[sel], bj=np.array(bj)[sel], bz=np.array(bz)[sel],
                     bsek=np.array(bsek)[sel], led_i=np.array(li, bool)[sel], led_j=np.array(lj, bool)[sel],
                     ti=np.array([stationer_ut[d][0][1] for d in band], int),
                     tj=np.array([stationer_ut[d][1][1] for d in band], int),
                     tEA=np.array([material["Stålband"]["E0mean"] * delar[d].bredd * delar[d].hojd for d in band]),
                     upplag=np.array(sorted(i for i in range(nn) if fast[i])),
                     b_c=np.array([c for c, (_, _, tt) in enumerate(bind) for _ in tt], int),
                     b_nod=np.array([n_ for *_, tt in bind for n_, _ in tt], int),
                     b_vikt=np.array([v for *_, tt in bind for _, v in tt]),
                     b_e=np.array([w for _, w, _ in bind]).reshape(-1, 3), b_k=np.full(len(bind), K_BIND))
    sekundara = sorted(b.namn for b in delar if b.slag == "utgar")
    return Natverk(delar, X, np.array(eldel)[sel], np.array(els)[sel], stationer_ut, mod, band, nod_delar,
                   {k: data[k] for k in ("takytor", "vaggar", "huskroppar", "h_vagg", "z_bjalklag")}, utelamnade,
                   sekundara, linjer, [el for el, *_ in bind])
