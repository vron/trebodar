"""Balkmodellen ur modellens bärverk (barverk.json, `./mod barverk` i verktyg/modellering).

- Delarna: varje virkesdel längre än MIN_LANGD blir en balk längs sin axel (virkets fiberriktning, tvärsnittets
  mitt), med tvärsnittet b × h; nock- och dalbalkarna blir en balk var (limträet med stålplåtarna i full
  samverkan där plåtarna finns, limmade enligt K-01); stålbanden blir dragstänger mellan ändarna; spikplåtar,
  stålplåtar och korta bitar binder ihop delarna som ligger an mot dem.
- Knutpunkterna: delar som ligger an mot varandra (lådorna med toleransen TOL_KONTAKT) förbinds där deras axlar
  är närmast varandra, med en stel förskjutning mellan axlarna och en led (fria rotationer) i den anslutande
  delen; parallella delar (t.ex. reglarna i en stolpe, upplagsreglarna längs balkarna) förbinds vid
  överlappens ändar och vid varandras knutpunkter. Ett band förbinds bara vid sina ändar.
- Upplagen: delar som står på bjälklaget (syllarna, stolparnas fötter) har låsta förskjutningar i sina noder
  nära bjälklaget (förankrade); reaktionerna är krafterna till bjälklaget och förankringen.
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
    slag: str                                   # "balk", "band" eller "kontakt"
    a: np.ndarray
    b: np.ndarray
    ez: np.ndarray                              # tvärsnittets höjdriktning (h)
    bredd: float
    hojd: float
    c: np.ndarray                               # lådan: mitt, axlar (rader), halva mått
    E: np.ndarray
    halv: np.ndarray
    platar: list[tuple[float, float, float, float]] = field(default_factory=list)   # (s0, s1, avstånd, area)
    upplagd: bool = False

    @property
    def L(self) -> float:
        return float(np.linalg.norm(self.b - self.a))

    @property
    def ex(self) -> np.ndarray:
        return (self.b - self.a) / self.L

    def punkt(self, s: float) -> np.ndarray:
        return self.a + s * self.ex


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
    return Bar(nr, d["namn"], d["grupp"], d["element"], d["typ"], d["stolpe"], d["material"], slag,
               c - E[k] * halv[k], c + E[k] * halv[k], E[ih].copy(), 2 * halv[ib], 2 * halv[ih], c, E, halv)


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


class _Unionfind:
    def __init__(self) -> None:
        self.p: list[int] = []

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
    for b in delar:
        zmin = b.c[2] - np.abs(b.E[:, 2]) @ b.halv
        b.upplagd = b.slag == "balk" and b.grupp in ("yttervagg", "innervagg", "stolpe") and zmin <= z_b + UPPLAG_Z

    # kontakter: omslutande lådor (axelparallella) först, sedan lådorna
    lo = np.array([b.c - np.abs(b.E.T) @ b.halv for b in delar])
    hi = np.array([b.c + np.abs(b.E.T) @ b.halv for b in delar])
    n = len(delar)
    I, J = np.triu_indices(n, 1)
    m = np.all((lo[I] <= hi[J] + TOL_KONTAKT) & (lo[J] <= hi[I] + TOL_KONTAKT), axis=1)
    par = np.column_stack([I[m], J[m]])
    par = par[_obb_kontakt(delar, par, TOL_KONTAKT)]

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

    # kontakterna (spikplåtar, stålplåtar, korta bitar): delarna som ligger an mot samma kontakt (eller mot kontakter
    # som ligger an mot varandra) förbinds i kontaktens mitt
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
        medl = sorted({d for k in ks for d in kontakter[k] if delar[d].slag != "kontakt"})
        nycklar = []
        for d in medl:
            b = delar[d]
            s = float(np.clip((mitt - b.a) @ b.ex, 0.0, b.L))
            if b.slag == "band":
                s = 0.0 if s < b.L / 2 else b.L
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
        if b.slag == "kontakt":
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

    # knutpunkterna: en nod per knutpunkt, i den viktigaste delens axel (står på bjälklaget > går igenom > styvast)
    medlemmar: dict[int, list[tuple[int, float]]] = defaultdict(list)
    for d, lista in st_del.items():
        for s_, k in lista:
            medlemmar[uf.hitta(k)].append((d, s_))

    def poang(d: int, s_: float) -> float:
        b = delar[d]
        uppl = b.upplagd and b.punkt(s_)[2] < z_b + 100.0
        inre = SAMMA < s_ < b.L - SAMMA and b.slag == "balk"
        return 1e9 * uppl + 1e6 * inre + (b.bredd * b.hojd ** 3 if b.slag == "balk" else 0.0)
    nod_av: dict[int, int] = {}
    x, nod_delar, fast = [], [], []
    for k, ms in medlemmar.items():
        d, s_ = max(ms, key=lambda t: poang(*t))
        nod_av[k] = len(x)
        x.append(delar[d].punkt(s_))
        nod_delar.append(sorted({dd for dd, _ in ms}))
        fast.append(delar[d].upplagd and delar[d].punkt(s_)[2] < z_b + 100.0)
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
        for n_, ((sa, p), (sb, q)) in enumerate(zip(lista, lista[1:])):
            if p == q or np.linalg.norm(X[q] - X[p]) < 1.0:
                continue
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
            lj.append(n_ == len(lista) - 2 and (led and len(nod_delar[q]) > 1 or fast[q] and abs(b.ex[2]) > 0.9))

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
                     upplag=np.array(sorted(i for i in range(nn) if fast[i])))
    # noder som inte sitter ihop med upplagen låses (de har inga element kvar)
    return Natverk(delar, X, np.array(eldel)[sel], np.array(els)[sel], stationer_ut, mod, band, nod_delar,
                   {k: data[k] for k in ("takytor", "vaggar", "huskroppar", "h_vagg", "z_bjalklag")}, utelamnade)
