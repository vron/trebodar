"""Lasterna på balkmodellen (natverk.py), som utbredda laster per balkelement:

- egentyngden: delarnas egen tyngd (virket med F-01:s 500 kg/m³), takets skikt per m² takyta (F-01 utan takbalkarna,
  som är delar i modellen, och med ströläkten) och väggarnas skikt per m² vägg;
- snö på takfallen (per m² horisontell yta) och vind på takfallen och väggarna (per m² yta, vinkelrätt mot ytan,
  med invändig vindlast), med formfaktorerna efter SS-EN 1991-1-3 och -1-4 för var och en av huskropparna;
- ytorna delas i rutor om RUTA × RUTA mm; varje rutas last förs till den närmaste bärande delen i ytan (takbalkar,
  takstolarnas ytterbalkar och nock- och dalbalkar i taket, väggens reglar, syllar, hammarband, överstycken och
  takstolens delar i väggen), till balkelementet där rutan ligger längs delen, och delas jämnt över elementet.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np

from natverk import Natverk

RUTA = 100.0             # rutornas storlek [mm]
G_ACC = 9.81


@dataclass
class Lastfall:
    namn: str
    text: str
    slag: str                    # "G", "S" eller "W"
    q: np.ndarray                # (m, 3) globalt [N/mm]


def _segavstand(P: np.ndarray, A: np.ndarray, B: np.ndarray) -> np.ndarray:
    """Avståndet (p, s) från punkterna P (p, 2) till sträckorna A–B (s, 2)."""
    d = B - A
    L2 = np.maximum((d * d).sum(axis=1), 1e-9)
    t = np.clip(((P[:, None, :] - A[None]) * d[None]).sum(axis=2) / L2[None], 0.0, 1.0)
    Q = A[None] + t[..., None] * d[None]
    return np.linalg.norm(P[:, None, :] - Q, axis=2)


class Fordelning:
    """Fördelningen av rutornas laster till balkelementen."""

    def __init__(self, N: Natverk):
        self.N = N
        m = N.modell
        self.ne = len(m.bi)
        self.el_per_del: dict[int, tuple[np.ndarray, np.ndarray]] = {}
        for d in np.unique(N.element_del):
            el = np.flatnonzero(N.element_del == d)
            s0 = N.element_s[el, 0]
            ordning = np.argsort(s0)
            self.el_per_del[int(d)] = (el[ordning], s0[ordning])
        self.L = np.linalg.norm(m.x[m.bj] - m.x[m.bi], axis=1)

    def till_element(self, P3: np.ndarray, F: np.ndarray, delar: np.ndarray) -> np.ndarray:
        """Rutornas krafter F (p, 3) [N] i punkterna P3 (p, 3), förda till delarna `delar` (p,), som jämnt
        utbredda laster per element (m, 3) [N/mm]. En del som ligger an mot en större längs en gemensam systemlinje
        (ytterbalken på diagonalen, hammarbandet under underramen) för lasten till den större."""
        q = np.zeros((self.ne, 3))
        delar = np.array([self.N.linjer.get(int(d), int(d)) for d in delar], int)
        for d in np.unique(delar):
            k = delar == d
            b = self.N.delar[d]
            s = np.clip((P3[k] - b.a) @ b.ex, 0.0, b.L)
            el, s0 = self.el_per_del[int(d)]
            i = np.clip(np.searchsorted(s0, s, side="right") - 1, 0, len(el) - 1)
            np.add.at(q, el[i], F[k])
        return q / self.L[:, None]


def egentyngd(N: Natverk, rho_tra: float) -> np.ndarray:
    """Delarnas egen tyngd per element (m, 3) [N/mm]."""
    m = N.modell
    q = np.zeros((len(m.bi), 3))
    for e, d in enumerate(N.element_del):
        b = N.delar[d]
        rho = rho_tra if b.material in ("C24", "GL30c", "GL30h") else 7850.0
        A = m.bsek[e, 2] if not b.platar else b.bredd * b.hojd + sum(
            ap for s0, s1, _, ap in b.platar if s0 <= 0.5 * (N.element_s[e, 0] + N.element_s[e, 1]) <= s1)
        q[e, 2] = -rho * G_ACC * 1e-9 * A
    return q


# ---------------------------------------------------------------------------------------------------------- taket

@dataclass
class Takruta:
    P: np.ndarray            # (p, 3) punkterna i takplanet
    dA: np.ndarray           # (p,) area i plan [mm²]
    n: np.ndarray            # (3,) takplanets normal uppåt
    kod: str
    kropp: int
    riktning: int
    dal: np.ndarray          # (p,) rutan ligger i en region mot en dal
    delar: np.ndarray        # (p,) den bärande delen


def takrutor(N: Natverk) -> list[Takruta]:
    ut = []
    for t in N.ytor["takytor"]:
        r = t["riktning"]
        a = math.radians(t["lutning"])
        tan = math.tan(a)
        n = np.array([-r * math.sin(a), 0.0, math.cos(a)])
        ner = np.array([r * math.cos(a), 0.0, math.sin(a)])      # uppåt längs takfallet
        P, dA, dal = [], [], []
        for y0, y1, xn, xk in t["regioner"]:
            xa, xb = sorted((xn, xk))
            nx, ny = max(1, round((xb - xa) / RUTA)), max(1, round((y1 - y0) / RUTA))
            xs = xa + (np.arange(nx) + 0.5) * (xb - xa) / nx
            ys = y0 + (np.arange(ny) + 0.5) * (y1 - y0) / ny
            X, Y = np.meshgrid(xs, ys)
            P.append(np.column_stack([X.ravel(), Y.ravel()]))
            dA.append(np.full(X.size, (xb - xa) / nx * (y1 - y0) / ny))
            dal.append(np.full(X.size, abs(xn - t["x_takfot"]) > 1.0))
        P2 = np.concatenate(P)
        z = t["z_ref"] + r * tan * (P2[:, 0] - t["x_ref"])
        P3 = np.column_stack([P2, z])
        # bärande delar i takfallets plan: längs takfallet med överkanten i planet, och balkarna längs y i fallet
        kand = []
        for b in N.delar:
            if b.slag != "balk":
                continue
            if b.grupp == "balk":
                if min(abs(b.a0[0] - x) for x in (P2[:, 0].min(), P2[:, 0].max())) < 300.0 and \
                        P2[:, 1].min() - 100 < b.c[1] < P2[:, 1].max() + 100:
                    kand.append(b.nr)
                continue
            if abs(b.ex @ ner) < 0.95:
                continue
            h_n = abs(n @ b.ez) * b.hojd + abs(n @ np.cross(b.ex, b.ez)) * b.bredd
            d = n @ (b.a0 - np.array([t["x_ref"], 0.0, t["z_ref"]]))
            if abs(abs(d) - h_n / 2) < 25.0 and P2[:, 1].min() - 50 < b.c[1] < P2[:, 1].max() + 50:
                kand.append(b.nr)
        kand = np.array(kand)
        A = np.array([N.delar[k].a0[:2] for k in kand])
        B = np.array([N.delar[k].b0[:2] for k in kand])
        delar = kand[np.argmin(_segavstand(P2, A, B), axis=1)]
        ut.append(Takruta(P3, np.concatenate(dA), n, t["kod"], t["kropp"], r, np.concatenate(dal), delar))
    return ut


def _cpe_tak(tr: Takruta, kroppar: dict[int, dict[str, Any]], d: np.ndarray, variant: str, h: float,
             cp: dict[str, Any]) -> np.ndarray:
    """Utvändiga formfaktorer för rutorna i takfallet (SS-EN 1991-1-4 7.2.5, sadeltak 30°, varje kropp för sig)."""
    k = kroppar[tr.kropp]
    x, y = tr.P[:, 0], tr.P[:, 1]
    ky0, ky1 = k["ty0"], k["ty1"]
    kx0, kx1 = k["tx0"], k["tx1"]
    if abs(d[0]) > 0.5:                                     # θ = 0°: vinden vinkelrätt mot nocken
        e = min(ky1 - ky0, 2 * h)
        lovart = tr.riktning == np.sign(d[0])
        if lovart:
            kant = kx0 if d[0] > 0 else kx1
            dx = np.abs(x - kant)
            hornet = np.minimum(y - ky0, ky1 - y) < e / 4
            zon = np.where(dx < e / 10, np.where(hornet, "F", "G"), "H")
        else:
            dx = np.abs(x - k["nock"])
            zon = np.where(dx < e / 10, "J", "I")
        tab = cp["theta0"][variant]
    else:                                                   # θ = 90°: vinden längs nocken
        e = min(kx1 - kx0, 2 * h)
        kant = ky0 if d[1] > 0 else ky1
        dy = np.abs(y - kant)
        hornet = np.minimum(x - kx0, kx1 - x) < e / 4
        zon = np.where(dy < e / 10, np.where(hornet, "F", "G"), np.where(dy < e / 2, "H", "I"))
        tab = cp["theta90"]
    return np.array([tab[z] for z in zon])


# ---------------------------------------------------------------------------------------------------------- väggarna

@dataclass
class Vaggruta:
    P: np.ndarray            # (p, 3)
    dA: np.ndarray
    n_ut: np.ndarray         # utåt
    kod: str
    yttervagg: bool
    delar: np.ndarray


def vaggrutor(N: Natverk) -> list[Vaggruta]:
    tak = {t["kod"]: t for t in N.ytor["takytor"]}
    ut = []
    for v in N.ytor["vaggar"]:
        o, u, w = np.array(v["origo"]), np.array(v["u"]), np.array(v["w"])
        kand = np.array([b.nr for b in N.delar if b.slag == "balk" and b.element == v["kod"]])
        if not len(kand):
            continue
        # väggens överkant: takets överkant ovanför gavlarna, annars den högsta delen i väggen
        us = (np.arange(max(1, round(v["langd"] / RUTA))) + 0.5) * v["langd"] / max(1, round(v["langd"] / RUTA))
        xy = o[None] + us[:, None] * u[None]
        topp = max(max(N.delar[k].a0[2], N.delar[k].b0[2]) for k in kand) + 22.5
        ztop = np.full(len(us), topp)
        if v["yttervagg"] and abs(u[0]) > 0.5:
            kropp = int(v["kod"][0])
            fall = [t for t in tak.values() if t["kropp"] == kropp]
            zz = np.min([t["z_ref"] + t["riktning"] * math.tan(math.radians(t["lutning"])) * (xy[:, 0] - t["x_ref"])
                         for t in fall], axis=0)
            ztop = np.maximum(np.minimum(zz, topp + 2000.0), N.ytor["h_vagg"])
        P, dA = [], []
        for i, uu in enumerate(us):
            nz = max(1, round(ztop[i] / RUTA))
            zs = (np.arange(nz) + 0.5) * ztop[i] / nz
            P.append(np.column_stack([np.full(nz, xy[i, 0]), np.full(nz, xy[i, 1]), zs]))
            dA.append(np.full(nz, v["langd"] / len(us) * ztop[i] / nz))
        P3 = np.concatenate(P)
        dA = np.concatenate(dA)
        # närmaste del i väggens plan (u, z); rutor närmast bjälklaget (dörrar och glaspartier ner till golvet) går
        # direkt till bjälklaget
        def planet(X: np.ndarray) -> np.ndarray:
            return np.column_stack([(X[:, :2] - o) @ u, X[:, 2]])
        A = np.vstack([planet(np.array([N.delar[k].a0 for k in kand])), [[0.0, N.ytor["z_bjalklag"]]]])
        B = np.vstack([planet(np.array([N.delar[k].b0 for k in kand])), [[v["langd"], N.ytor["z_bjalklag"]]]])
        narm = np.argmin(_segavstand(planet(P3), A, B), axis=1)
        ok = narm < len(kand)
        ut.append(Vaggruta(P3[ok], dA[ok], -np.array([*w, 0.0]), v["kod"], v["yttervagg"], kand[narm[ok]]))
    return ut


def _cpe_vagg(vr: Vaggruta, d: np.ndarray, bygg: dict[str, float], h: float, cp: dict[str, Any]) -> np.ndarray:
    """Utvändiga formfaktorer för väggens rutor (SS-EN 1991-1-4 7.2.2, tabell 7.1)."""
    c = vr.n_ut[:2] @ d
    djup = bygg["dx"] if abs(d[0]) > 0.5 else bygg["dy"]
    bredd = bygg["dy"] if abs(d[0]) > 0.5 else bygg["dx"]
    hd = min(max(h / djup, 0.25), 1.0)
    D = cp["D"][0] + (cp["D"][1] - cp["D"][0]) * (hd - 0.25) / 0.75
    E = cp["E"][0] + (cp["E"][1] - cp["E"][0]) * (hd - 0.25) / 0.75
    if c < -0.5:
        return np.full(len(vr.dA), D)
    if c > 0.5:
        return np.full(len(vr.dA), E)
    e = min(bredd, 2 * h)
    if abs(d[0]) > 0.5:
        s = vr.P[:, 0] - bygg["x0"] if d[0] > 0 else bygg["x1"] - vr.P[:, 0]
    else:
        s = vr.P[:, 1] - bygg["y0"] if d[1] > 0 else bygg["y1"] - vr.P[:, 1]
    return np.where(s < e / 5, cp["A"], np.where(s < e, cp["B"], cp["C"]))


# ---------------------------------------------------------------------------------------------------------- lastfallen

def lastfall(N: Natverk, IN: dict[str, Any], f01: dict[str, Any]) -> tuple[list[Lastfall], dict[str, Any]]:
    """Lastfallen (karakteristiska) och lastdata för rapporten."""
    F = Fordelning(N)
    L = IN["last"]
    tak = takrutor(N)
    vagg = vaggrutor(N)
    # takets egentyngd: F-01:s skikt utom takbalkarna, med ströläkten
    kg = sum(s["kg"] for s in f01["tak"] if "Takbalkar" not in s["skikt"]) + sum(s["kg"] for s in L["tak_tillagg"])
    g_tak = kg * G_ACC / 1e3                                  # kN/m² takyta
    sk = f01["sno"]["sk"] * f01["sno"]["Ce"] * f01["sno"]["Ct"]
    v = f01["vind"]
    kr = 0.19 * (v["z0"] / v["z0_II"]) ** 0.07
    cr = kr * math.log(v["z"] / v["z0"])
    Iv = 1 / math.log(v["z"] / v["z0"])
    qp = (1 + 7 * Iv) * 0.5 * v["rho"] * (cr * v["vb"]) ** 2 / 1e3     # kN/m²
    h = v["z"] * 1000.0
    # huskropparnas tak i plan (för zonerna)
    kroppar: dict[int, dict[str, Any]] = {}
    for k in N.ytor["huskroppar"]:
        tr = [t for t in tak if t.kropp == k["nr"]]
        P = np.concatenate([t.P for t in tr])
        kroppar[k["nr"]] = {"tx0": P[:, 0].min() - RUTA / 2, "tx1": P[:, 0].max() + RUTA / 2,
                            "ty0": P[:, 1].min() - RUTA / 2, "ty1": P[:, 1].max() + RUTA / 2, "nock": k["nock"]}
    alla = np.concatenate([t.P for t in tak])
    bygg = {"x0": alla[:, 0].min(), "x1": alla[:, 0].max(), "y0": alla[:, 1].min(), "y1": alla[:, 1].max()}
    bygg["dx"], bygg["dy"] = bygg["x1"] - bygg["x0"], bygg["y1"] - bygg["y0"]
    rho = IN["material"]["rho_tra"]

    def ytlast(fun_tak: Any, fun_vagg: Any) -> np.ndarray:
        q = np.zeros((F.ne, 3))
        for t in tak:
            Fv = fun_tak(t)
            if Fv is not None:
                q += F.till_element(t.P, Fv, t.delar)
        for vr in vagg:
            Fv = fun_vagg(vr)
            if Fv is not None:
                q += F.till_element(vr.P, Fv, vr.delar)
        return q

    ned = np.array([0.0, 0.0, -1.0])
    utfall: list[Lastfall] = []
    # G: delarna, taket per m² takyta, väggarna per m² vägg
    gv = {True: L["vagg_ytter"], False: L["vagg_inner"]}
    qG = egentyngd(N, rho) + ytlast(
        lambda t: np.outer(t.dA / t.n[2] * g_tak * 1e-3, ned),
        lambda vr: np.outer(vr.dA * gv[vr.yttervagg] * 1e-3, ned))
    utfall.append(Lastfall("G", "Egentyngd", "G", qG))
    # snö: S1 med formfaktorerna mot dal och takfot; S2 och S3 osymmetriska (halva μ1 på ena sidan)
    alfa = f01["sno"]["alfa"]
    mu1 = 0.8 if alfa <= 30 else 0.8 * (60 - alfa) / 30 if alfa < 60 else 0.0      # SS-EN 1991-1-3 tabell 5.2
    mu_d, mu_t = L["mu_dal"], L["mu_takfot"]

    def sno(halv: int | None) -> np.ndarray:
        def f(t: Takruta) -> np.ndarray:
            mu = np.where(t.dal, mu_d, mu_t)
            if halv is not None and t.riktning == halv:
                mu = np.full(len(mu), 0.5 * mu1)
            return np.outer(mu * sk * t.dA * 1e-3, ned)
        return ytlast(f, lambda vr: None)
    utfall.append(Lastfall("S1", f"Snö, μ {mu_d:g} mot dalarna och {mu_t:g} mot takfoten", "S", sno(None)))
    utfall.append(Lastfall("S2", f"Snö, som S1 men μ {0.5 * mu1:g} på de nordvästra takfallen", "S", sno(-1)))
    utfall.append(Lastfall("S3", f"Snö, som S1 men μ {0.5 * mu1:g} på de sydöstra takfallen", "S", sno(+1)))
    # vind
    cp = IN["vind"]
    riktningar = {"+x": np.array([1.0, 0.0]), "−x": np.array([-1.0, 0.0]), "+y": np.array([0.0, 1.0]),
                  "−y": np.array([0.0, -1.0])}
    for rn, d in riktningar.items():
        varianter = ("sug", "tryck") if abs(d[0]) > 0.5 else ("",)
        for var in varianter:
            for cpi in cp["cpi"]:
                def ftak(t: Takruta) -> np.ndarray:
                    cpe = _cpe_tak(t, kroppar, d, var, h, cp)
                    p = qp * (cpe - cpi)                      # kN/m², positivt in mot ytan
                    return np.outer(p * t.dA / t.n[2] * 1e-3, -t.n)

                def fvagg(vr: Vaggruta) -> np.ndarray | None:
                    if not vr.yttervagg:
                        return None
                    cpe = _cpe_vagg(vr, d, bygg, h, cp)
                    p = qp * (cpe - cpi)
                    return np.outer(p * vr.dA * 1e-3, -vr.n_ut)
                namn = f"W{rn}{',' + var if var else ''},{cpi:+.1f}".replace("+0.", "+0,").replace("-0.", "−0,")
                text = (f"Vind {rn}" + (f" ({'sug' if var == 'sug' else 'tryck'} på lovartsidan)" if var else "")
                        + f", invändigt c_pi {cpi:+.1f}".replace(".", ","))
                utfall.append(Lastfall(namn, text, "W", ytlast(ftak, fvagg)))
    data = {"g_tak": g_tak, "kg_tak": kg, "sk": sk, "qp": qp, "kr": kr, "cr": cr, "Iv": Iv, "h": h,
            "bygg": bygg, "kroppar": kroppar}
    return utfall, data
