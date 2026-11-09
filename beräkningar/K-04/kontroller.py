"""Kontrollerna enligt SS-EN 1995-1-1 (trä) och SS-EN 1993-1-1/-1-3 (stålbanden) med EKS, för varje del i
balkmodellen och varje lastkombination, samlade per grupp av delar (reglar, stolpar, syllar och hammarband,
överstycken, takbalkar, takstolar, stålband): det högsta utnyttjandet i gruppen, delen och kombinationen.

- Virket: normalkraft och böjning (6.17–6.20, med knäckning 6.23–6.24), tvärkraft (6.13) och vridning (6.14) i
  varje balkelement, med krafterna längs elementet (den utbredda lasten ger böjningen mellan noderna).
  Knäckning: reglar och stolpar i väggarna och takbalkarna i sin styva riktning över delens längd; i den veka
  riktningen stagas de av skivorna och läkten (som inte räknas för stabiliseringen). Fristående stolpar av flera
  reglar räknas som ett tvärsnitt (ihopskruvade, som K-03), knäckning åt båda hållen.
- Tryck vinkelrätt fibrerna där reglar och stolpar står på syllar eller under hammarband (6.1.5).
- Stålbanden: drag i nettotvärsnittet och spiken i ändarna (8.2.3, tunn stålplåt).
- Förankringen: lyft och horisontalkraft i upplagen.
- Bruksgränstillståndet: takbalkarnas nedböjning (w_fin) och väggarnas överkant i vind.
"""
from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from analys import Losning
from natverk import Bar, Natverk


@dataclass
class Rad:
    """En kontroll i en grupp: utnyttjandet, delen, kombinationen och värdena som förklarar det."""
    grupp: str
    kontroll: str
    eta: float
    del_: str
    komb: str
    detaljer: dict[str, Any] = field(default_factory=dict)


def sammansatta(N: Natverk) -> dict[int, list[int]]:
    """Stående delar i väggarna som står sida vid sida och är ihopspikade (en stolpe eller dubbla reglar): de
    ligger an mot varandra längs mer än 0,5 m och delar knutpunkterna i balkmodellen. Delen -> gruppens delar."""
    st = [b for b in N.delar if b.slag == "balk" and abs(b.ex[2]) > 0.9 and b.grupp in ("yttervagg", "innervagg")]
    lo = {b.nr: b.c - np.abs(b.E.T) @ b.halv for b in st}
    hi = {b.nr: b.c + np.abs(b.E.T) @ b.halv for b in st}
    far = {b.nr: b.nr for b in st}

    def rot(i: int) -> int:
        while far[i] != i:
            i = far[i]
        return i
    for i, a in enumerate(st):
        for b in st[i + 1:]:
            if a.element == b.element and np.all(lo[a.nr] <= hi[b.nr] + 1.0) and np.all(lo[b.nr] <= hi[a.nr] + 1.0) \
                    and min(a.b0[2], b.b0[2]) - max(a.a0[2], b.a0[2]) > 500.0:
                far[rot(a.nr)] = rot(b.nr)
    grp: dict[int, list[int]] = defaultdict(list)
    for b in st:
        grp[rot(b.nr)].append(b.nr)
    return {i: sorted(g, key=lambda j: N.delar[j].namn) for g in grp.values() for i in g}


def visa(N: Natverk, b: Bar, grupper: dict[int, list[int]]) -> str:
    """Delens namn i rapporten: takstolens delar märks (väggen och takstolen på den har samma kod), och delar som
    står ihop med andra visas som en sammansatt del med antal och tvärsnitt."""
    g = grupper.get(b.nr, [b.nr])
    if len(g) > 1:
        dim = f"{min(b.bredd, b.hojd):.0f}×{max(b.bredd, b.hojd):.0f}"
        namn = b.stolpe or "+".join([N.delar[g[0]].namn] + [N.delar[j].namn.split("-")[-1] for j in g[1:]])
        return f"{namn} ({len(g)} × {dim})"
    return f"takstol {b.namn}" if b.grupp == "takstol" else b.namn


def grupp_av(b: Bar) -> str:
    if b.slag == "band":
        return "Stålband i väggarna" if b.grupp == "band_vagg" else "Stålband i takfallen"
    if b.grupp == "balk":
        return "Nock- och dalbalkar"
    if b.grupp == "stolpe":
        return "Fristående stolpar"
    if b.grupp in ("yttervagg", "innervagg"):
        if b.stolpe:
            return "Stolpar i väggarna"
        return {"R": "Reglar i ytterväggarna" if b.grupp == "yttervagg" else "Reglar i innerväggarna",
                "S": "Syllar och hammarband", "H": "Syllar och hammarband",
                "L": "Överstycken, bröstningar och kortlingar"}.get(b.typ, "Övrigt i väggarna")
    if b.grupp == "takbalk":
        return "Takbalkar och avväxlingar"
    if b.grupp == "takstol":
        return "Takstolar"
    return "Övrigt"


class Material:
    def __init__(self, namn: str, p: dict[str, float]):
        self.namn = namn
        self.__dict__.update(p)

    def kh(self, d: np.ndarray) -> np.ndarray:
        if self.namn.startswith("GL"):
            return np.where(d < 600, np.minimum((600 / d) ** 0.1, 1.1), 1.0)
        return np.where(d < 150, np.minimum((150 / d) ** 0.2, 1.3), 1.0)

    def kc(self, L: np.ndarray, d: np.ndarray) -> np.ndarray:
        """Knäckningsfaktorn (6.3.2) för knäcklängden L och tvärsnittets mått d i knäckningsriktningen (L 0: 1)."""
        lr = np.where(L > 0, L * math.sqrt(12) / d / math.pi * math.sqrt(self.fc0k / self.E005), 0.0)
        k = 0.5 * (1 + self.beta_c * (lr - 0.3) + lr ** 2)
        return np.where(lr <= 0.3, 1.0, 1 / (k + np.sqrt(np.maximum(k ** 2 - lr ** 2, 0.0))))


HORN_Z = 0.5             # en regel i ett hörn är stagad där en vinkelrät väggs regel ligger an längs minst så stor del
#                          av dess höjd


def _lada(b: Bar) -> tuple[np.ndarray, np.ndarray]:
    return b.c - np.abs(b.E.T) @ b.halv, b.c + np.abs(b.E.T) @ b.halv


def stagade_i_horn(N: Natverk) -> set[int]:
    """Stående delar i väggarna (reglar och stolpar) som en vinkelrät väggs regel ligger an mot (ihopspikade) längs
    minst HORN_Z av deras höjd: den andra väggen är styv i sitt plan, som är delens riktning ut ur dess vägg, och
    stagar delen åt det hållet (hörnen, som stolparna i 1B:s ändar och 1A:s ändregel mot varandra och mot den lätta
    väggen L20). Den andra väggens regel: en bärande väggs (en annan vägg) eller en lätt väggs (utdragets
    latta_reglar), vars tjockleksriktning är vinkelrät mot delens."""
    st = [b for b in N.delar if b.slag == "balk" and abs(b.ex[2]) > 0.9 and b.grupp in ("yttervagg", "innervagg")]
    andra: list[tuple[str, np.ndarray, np.ndarray, int]] = []
    for b in st:
        lo, hi = _lada(b)
        andra.append((b.element, lo, hi, int(np.argmax(np.abs(b.ez[:2])))))
    for r in N.ytor.get("latta_reglar", []):
        lo, hi = np.array(r["lada"][:3]), np.array(r["lada"][3:])
        andra.append((r["vagg"], lo, hi, int(np.argmax((hi - lo)[:2]))))
    ut = set()
    for b in st:
        lo, hi = _lada(b)
        k = int(np.argmax(np.abs(b.ez[:2])))             # ut ur väggens plan (x eller y)
        for el, lo2, hi2, k2 in andra:
            if el == b.element or k2 == k:
                continue
            glapp = np.maximum(lo2[:2] - hi[:2], lo[:2] - hi2[:2])        # > 0: isär, ≤ 0: överlapp
            an = bool(np.all(glapp <= 1.0) and np.any(glapp >= -1.0) and np.any(glapp < -10.0))
            hojd = min(hi[2], hi2[2]) - max(lo[2], lo2[2])
            if an and hojd >= HORN_Z * (hi[2] - lo[2]):
                ut.add(b.nr)
                break
    return ut


def _knacklangd(N: Natverk) -> tuple[np.ndarray, np.ndarray]:
    """Knäcklängderna (Ly kring den styva axeln, h; Lz kring den veka, b) per del; 0 = stagad."""
    Ly = np.zeros(len(N.delar))
    Lz = np.zeros(len(N.delar))
    horn = stagade_i_horn(N)
    for b in N.delar:
        if b.slag != "balk" or b.grupp == "balk":
            continue
        if b.grupp == "stolpe":
            Ly[b.nr] = Lz[b.nr] = b.langd                   # fristående: båda hållen (stolparna kontrolleras som helhet)
        elif b.grupp in ("yttervagg", "innervagg") and b.typ in ("R", "") or b.stolpe:
            Ly[b.nr] = 0.0 if b.nr in horn else b.langd     # reglar och stolpar i väggen: ut ur väggens plan
        elif b.grupp == "takstol" or b.grupp == "takbalk" and b.typ == "T":
            Ly[b.nr] = b.langd                          # takbalkarna och takstolarnas delar i sitt plan
    return Ly, Lz


def _krafter_langs(F: np.ndarray, q: np.ndarray, L: np.ndarray) -> dict[str, np.ndarray]:
    """Största krafterna längs elementen (k, m): normalkraft (drag +) i ändarna, böjmoment längs elementet med den
    utbredda lasten, tvärkrafter och vridmoment."""
    f = F
    qx, qy, qz = q[..., 0], q[..., 1], q[..., 2]
    N0, NL = -f[..., 0], f[..., 6]
    punkter = [np.zeros_like(L), 0.5 * L, L]
    with np.errstate(divide="ignore", invalid="ignore"):
        xy = np.where(np.abs(qz) > 1e-12, -f[..., 2] / qz, 0.0)
        xz = np.where(np.abs(qy) > 1e-12, -f[..., 1] / qy, 0.0)
    My = np.zeros(f.shape[:2])
    Mz = np.zeros(f.shape[:2])
    for x in punkter + [np.clip(xy, 0, L), np.clip(xz, 0, L)]:
        My = np.maximum(My, np.abs(-f[..., 4] + x * f[..., 2] + x ** 2 * qz / 2))
        Mz = np.maximum(Mz, np.abs(-f[..., 5] - x * f[..., 1] - x ** 2 * qy / 2))
    Vy = np.maximum(np.abs(f[..., 1]), np.abs(f[..., 7]))
    Vz = np.maximum(np.abs(f[..., 2]), np.abs(f[..., 8]))
    T = np.maximum(np.abs(f[..., 3]), np.abs(f[..., 9]))
    return {"Nt": np.maximum(np.maximum(N0, NL), 0.0), "Nc": np.maximum(np.maximum(-N0, -NL), 0.0),
            "My": My, "Mz": Mz, "Vy": Vy, "Vz": Vz, "T": T}


def kontrollera(N: Natverk, L: Losning, IN: dict[str, Any]) -> dict[str, Any]:
    K = IN["kontroll"]
    mat = {k: Material(k, v) for k, v in IN["material"].items() if isinstance(v, dict) and "fmk" in v}
    m = N.modell
    str_ = np.array([k.slag == "STR" for k in L.komb])
    kmod = np.array([k.kmod for k in L.komb])[str_]
    kn = [k.namn for k in L.komb if k.slag == "STR"]
    F, q = L.F[str_], L.q[str_]
    eldel = N.element_del
    Le = np.linalg.norm(m.x[m.bj] - m.x[m.bi], axis=1)
    delar = N.delar
    rader: list[Rad] = []
    grupper = sammansatta(N)
    # ------------------------------------------------------------ virket per element
    K_ = _krafter_langs(F, q, Le[None, :])
    Ly, Lz = _knacklangd(N)
    b = np.array([delar[d].bredd for d in eldel])
    h = np.array([delar[d].hojd for d in eldel])
    A, Wy, Wz = b * h, b * h ** 2 / 6, h * b ** 2 / 6
    grupp = np.array([grupp_av(delar[d]) for d in eldel])
    kontrolleras = np.array([delar[d].grupp not in ("balk",) and delar[d].material in mat
                             and not (delar[d].grupp == "stolpe" and delar[d].typ == "R") for d in eldel])
    eta_nm = np.zeros(F.shape[:2])
    eta_v = np.zeros(F.shape[:2])
    for mn, M in mat.items():
        e = np.array([delar[d].material == mn for d in eldel]) & kontrolleras
        if not e.any():
            continue
        g = M.gamma_M
        kmd = kmod[:, None] / g
        fmy = kmd * M.fmk * M.kh(h[e])[None]
        fmz = kmd * M.fmk * M.kh(b[e])[None]
        ft = kmd * M.ft0k * M.kh(h[e])[None]
        fc = kmd * M.fc0k
        fv = kmd * M.fvk
        km = K["k_m"]
        st = K_["Nt"][:, e] / A[e]
        sc = K_["Nc"][:, e] / A[e]
        smy = K_["My"][:, e] / Wy[e]
        smz = K_["Mz"][:, e] / Wz[e]
        kcy = M.kc(Ly[eldel[e]], h[e])[None]
        kcz = M.kc(Lz[eldel[e]], b[e])[None]
        drag = np.maximum(st / ft + smy / fmy + km * smz / fmz, st / ft + km * smy / fmy + smz / fmz)
        tryck = np.maximum.reduce([(sc / fc) ** 2 + smy / fmy + km * smz / fmz, (sc / fc) ** 2 + km * smy / fmy + smz / fmz,
                                   sc / (kcy * fc) + smy / fmy + km * smz / fmz, sc / (kcz * fc) + km * smy / fmy + smz / fmz])
        eta_nm[:, e] = np.where(K_["Nt"][:, e] > 0, drag, tryck)
        tau = 1.5 * np.sqrt(K_["Vy"][:, e] ** 2 + K_["Vz"][:, e] ** 2) / (K["k_cr"] * A[e])
        bb, hh = np.minimum(b[e], h[e]), np.maximum(b[e], h[e])
        tor = K_["T"][:, e] / (bb ** 2 * hh / (3 + 1.8 * bb / hh))
        kshape = np.minimum(1 + 0.15 * hh / bb, 2.0)
        eta_v[:, e] = tor / (kshape * fv) + (tau / fv) ** 2
    # per grupp: högsta utnyttjandet
    for gn in sorted(set(grupp[kontrolleras])):
        for namn_k, eta, vad in (("Normalkraft och böjning", eta_nm, "nm"), ("Tvärkraft och vridning", eta_v, "v")):
            e = np.flatnonzero((grupp == gn) & kontrolleras)
            sub = eta[:, e]
            k, i = np.unravel_index(np.argmax(sub), sub.shape)
            el = e[i]
            d = delar[eldel[el]]
            det = {"N": float(F[k, el, 6]), "Nc": float(K_["Nc"][k, el]), "Nt": float(K_["Nt"][k, el]),
                   "My": float(K_["My"][k, el]), "Mz": float(K_["Mz"][k, el]),
                   "V": float(np.hypot(K_["Vy"][k, el], K_["Vz"][k, el])), "T": float(K_["T"][k, el]),
                   "b": float(d.bredd), "h": float(d.hojd), "L": float(d.langd), "Ly": float(Ly[d.nr]), "Lz": float(Lz[d.nr]),
                   "kmod": float(kmod[k]), "material": d.material, "antal": int(len({eldel[x] for x in e}))}
            g = grupper.get(d.nr, [d.nr])
            if len(g) > 1:                               # den sammansatta delens krafter: summan av reglarnas
                eg = np.flatnonzero(np.isin(eldel, g))
                for nyckel in ("Nc", "Nt", "My", "Mz"):
                    det[nyckel] = float(sum(K_[nyckel][k, eg[eldel[eg] == j]].max() for j in g))
                det["delar"] = len(g)
            det["nr"] = d.nr
            rader.append(Rad(gn, namn_k, float(sub[k, i]), visa(N, d, grupper), kn[k], det))
    # ------------------------------------------------------------ fristående stolpar som helhet
    stolpar: dict[str, list[int]] = defaultdict(list)
    for d in delar:
        if d.grupp == "stolpe" and d.slag == "balk" and d.typ == "R":
            stolpar[d.element].append(d.nr)
    best = None
    for kod, ds in stolpar.items():
        M = mat[delar[ds[0]].material]
        el = np.flatnonzero(np.isin(eldel, ds))
        Nc = np.zeros(len(kn))
        Mm = np.zeros(len(kn))
        for d in ds:
            ed = el[eldel[el] == d]
            Nc += K_["Nc"][:, ed].max(axis=1)
            Mm += np.hypot(K_["My"][:, ed], K_["Mz"][:, ed]).max(axis=1)
        # tvärsnittet: delarna sida vid sida
        X = sum(min(delar[d].bredd, delar[d].hojd) for d in ds)
        Y = max(max(delar[d].bredd, delar[d].hojd) for d in ds)
        if len(ds) == 1:
            X, Y = sorted((delar[ds[0]].bredd, delar[ds[0]].hojd))
        Ls = max(delar[d].langd for d in ds)
        As = X * Y
        kc = float(min(M.kc(np.array(Ls), np.array(X)), M.kc(np.array(Ls), np.array(Y))))
        fc = kmod * M.fc0k / M.gamma_M
        fm = kmod * M.fmk / M.gamma_M
        eta = Nc / (kc * As * fc) + Mm / (Y * X ** 2 / 6 * fm)
        k = int(np.argmax(eta))
        r = Rad("Fristående stolpar", "Tryck med knäckning", float(eta[k]), kod, kn[k],
                {"Nc": float(Nc[k]), "M": float(Mm[k]), "X": X, "Y": Y, "L": Ls, "kc": kc, "kmod": float(kmod[k]),
                 "material": M.namn, "antal": len(stolpar), "nr": ds[0]})
        if best is None or r.eta > best.eta:
            best = r
    if best:
        rader.append(best)
    # ------------------------------------------------------------ tryck vinkelrätt fibrerna: stående delar på syllar och
    # under hammarband
    C24 = mat["C24"]
    andar: dict[int, list[tuple[int, int]]] = defaultdict(list)      # nod -> (del, element) för delarnas ändar
    for d, lista in N.stationer.items():
        if delar[d].slag != "balk":
            continue
        for (s_, nod), forsta in ((lista[0], True), (lista[-1], False)):
            e = np.flatnonzero((eldel == d) & ((m.bi == nod) | (m.bj == nod)))
            if len(e):
                andar[nod].append((d, int(e[0])))
    best = None
    antal_upplag = 0
    for nod, ds in andar.items():
        lig = [delar[d] for d in N.nod_delar[nod] if delar[d].slag == "balk" and abs(delar[d].ex[2]) < 0.3
               and delar[d].typ in ("S", "H")]
        st = [(d, e) for d, e in ds if abs(delar[d].ex[2]) > 0.9]
        if not lig or not st:
            continue
        lig_ = lig[0]
        antal_upplag += 1
        Nc = np.zeros(len(kn))
        l_ = 0.0
        for d, e in st:
            b_ = delar[d]
            Nend = -F[:, e, 0] if m.bi[e] == nod else F[:, e, 6]
            Nc += np.maximum(-Nend, 0.0)
            l_ += abs(np.cross(b_.ex, b_.ez) @ lig_.ex) * b_.bredd + abs(b_.ez @ lig_.ex) * b_.hojd
        bredd = max(lig_.bredd, lig_.hojd) if abs(lig_.ez[2]) < 0.5 else min(lig_.bredd, lig_.hojd)
        kc90 = K["k_c90"] if lig_.typ == "S" else 1.5
        A90 = (l_ + 2 * K["l_extra"]) * bredd
        fc90 = kmod * C24.fc90k / C24.gamma_M
        eta = Nc / (kc90 * A90 * fc90)
        k = int(np.argmax(eta))
        namn = ", ".join(sorted({visa(N, delar[d], grupper) for d, _ in st}))
        r = Rad("Upplag (tryck vinkelrätt fibrerna)", "på syll" if lig_.typ == "S" else "under hammarband",
                float(eta[k]), f"{namn} på {lig_.namn}", kn[k],
                {"Nc": float(Nc[k]), "l": l_, "bredd": bredd, "kc90": kc90, "kmod": float(kmod[k]), "nr": st[0][0]})
        if best is None or r.eta > best.eta:
            best = r
    if best:
        best.detaljer["antal"] = antal_upplag
        rader.append(best)
    # ------------------------------------------------------------ stålbanden och spiken
    BD = IN["band"]
    SB = IN["material"]["Stålband"]
    A_b = BD["b"] * BD["t"]
    A_n = (BD["b"] - BD["d0"]) * BD["t"]
    NtRd = min(A_b * SB["fy"] / BD["gamma_M0"], 0.9 * A_n * SB["fu"] / BD["gamma_M2"])
    rhok = C24.rhok
    d_, t1 = BD["d"], BD["l"] - BD["t"]
    fhk = 0.082 * rhok * d_ ** -0.3
    Myk = 0.3 * BD["fu_spik"] * d_ ** 2.6
    Fax = 20e-6 * rhok ** 2 * d_ * t1
    Fv0 = min(0.4 * fhk * t1 * d_, 1.15 * math.sqrt(2 * Myk * fhk * d_))
    FvRk = Fv0 + min(Fax / 4, 0.5 * Fv0)
    Bn = L.band[str_]
    bandinfo = []
    for gn in ("Stålband i väggarna", "Stålband i takfallen"):
        idx = [i for i, d in enumerate(N.band) if grupp_av(delar[d]) == gn]
        if not idx:
            continue
        sub = Bn[:, idx]
        k, i = np.unravel_index(np.argmax(sub), sub.shape)
        Ned = float(sub[k, i])
        FvRd = kmod[k] * FvRk / BD["gamma_M_forband"]
        rader.append(Rad(gn, "Drag i nettotvärsnittet", Ned / NtRd, delar[N.band[idx[i]]].namn, kn[k],
                         {"N": Ned, "NtRd": NtRd, "A": A_b, "An": A_n, "antal": len(idx), "nr": N.band[idx[i]]}))
        nspik = math.ceil(Ned / FvRd)
        rader.append(Rad(gn, "Spik i bandets ände", Ned / (nspik * FvRd), delar[N.band[idx[i]]].namn, kn[k],
                         {"N": Ned, "n": nspik, "FvRd": FvRd, "FvRk": FvRk, "fhk": fhk, "Myk": Myk, "Fax": Fax,
                          "antal": len(idx)}))
        for j in idx:
            bandinfo.append({"namn": delar[N.band[j]].namn, "grupp": gn, "Nmax": float(Bn[:, j].max()),
                             "komb": kn[int(np.argmax(Bn[:, j]))]})
    # ------------------------------------------------------------ förankringen: lyft och horisontalkraft per upplag
    R = L.R[str_][..., :3]
    lyft = np.maximum(-R[..., 2], 0.0)
    hor = np.hypot(R[..., 0], R[..., 1])
    upp_del = [next((delar[d] for d in N.nod_delar[n_] if delar[d].upplagd), delar[N.nod_delar[n_][0]])
               for n_ in m.upplag]
    k, i = np.unravel_index(np.argmax(lyft), lyft.shape)
    forank = {"lyft": float(lyft[k, i]), "lyft_del": upp_del[i].namn, "lyft_komb": kn[k],
              "hor": float(hor.max()), "hor_del": upp_del[int(np.unravel_index(np.argmax(hor), hor.shape)[1])].namn}
    per_vagg: dict[str, dict[str, float]] = {}
    for vagg in sorted({d.element for d in upp_del}):
        j = [x for x, d in enumerate(upp_del) if d.element == vagg]
        per_vagg[vagg] = {"lyft": float(lyft[:, j].max()), "skjuv": float(np.abs(R[:, j, :2].sum(axis=1)).max()),
                          "tryck": float(np.maximum(R[:, j, 2], 0).max())}
    eta_el = np.maximum(eta_nm.max(axis=0), eta_v.max(axis=0))
    eta_band = Bn.max(axis=0) / NtRd if Bn.size else np.zeros(0)
    return {"rader": rader, "band": bandinfo, "NtRd": NtRd, "FvRk": FvRk, "forankring": forank,
            "per_vagg": per_vagg, "eta_element": eta_el, "eta_band": eta_band}


def bruksgrans(N: Natverk, L: Losning, IN: dict[str, Any]) -> dict[str, Any]:
    """Takbalkarnas nedböjning (w_fin, kontinuerliga med krypning: egentyngd och snö var för sig) och väggarnas
    överkant i karakteristisk vind."""
    K, KB = IN["kontroll"], IN["kombination"]
    m = N.modell
    namn = [k.namn for k in L.komb]
    U = L.u.reshape(len(namn), -1, 6)[..., :3]
    iG = namn.index("G (k)")
    iS = [i for i, k in enumerate(L.komb) if k.slag == "SLS-k" and k.faktorer.keys() == {next(iter(k.faktorer))}
          and next(iter(k.faktorer)).startswith("S")]
    iW = [i for i, k in enumerate(L.komb) if k.slag == "SLS-k" and next(iter(k.faktorer)).startswith("W")]
    Le = np.linalg.norm(m.x[m.bj] - m.x[m.bi], axis=1)
    EI = m.bsek[:, 0] * m.bsek[:, 3]
    best = {"eta": 0.0}
    for d, lista in N.stationer.items():
        b = N.delar[d]
        if b.grupp != "takbalk" or b.typ != "T":
            continue
        anslutna = [(s_, n_) for s_, n_ in lista if len(N.nod_delar[n_]) > 1]
        if len(anslutna) < 2:
            continue
        (s0, n0), (s1, n1) = anslutna[0], anslutna[-1]
        span = s1 - s0
        # vinkelrätt mot takbalken i dess vertikala plan
        nrm = np.cross(b.ex, np.cross(np.array([0.0, 0.0, 1.0]), b.ex))
        nrm /= np.linalg.norm(nrm)

        def w(i: int) -> float:
            ut = 0.0
            for e in np.flatnonzero(N.element_del == d):
                sa, sb = N.element_s[e]
                if sb <= s0 + 1 or sa >= s1 - 1:
                    continue
                ua, ub = U[i, m.bi[e]] @ nrm, U[i, m.bj[e]] @ nrm
                xa, xb = (sa - s0) / span, (sb - s0) / span
                u0, u1 = U[i, n0] @ nrm, U[i, n1] @ nrm
                kord = u0 + (u1 - u0) * 0.5 * (xa + xb)
                qn = abs(L.q[i, e, 2]) if abs(b.ez @ nrm) > 0.7 else abs(L.q[i, e, 1])
                ut = max(ut, abs(0.5 * (ua + ub) - kord) + 5 * qn * Le[e] ** 4 / (384 * EI[e]))
            return ut
        wG = w(iG)
        wS = max(w(i) for i in iS)
        wfin = wG * (1 + KB["k_def"]) + wS * (1 + KB["psi2_sno"] * KB["k_def"])
        eta = wfin / (span / K["nedb_tak"])
        if eta > best["eta"]:
            best = {"eta": float(eta), "del": b.namn, "wG": float(wG), "wS": float(wS), "wfin": float(wfin),
                    "L": float(span)}
    # väggarnas överkant: hammarbandens noder
    drift = {"eta": 0.0}
    for d, lista in N.stationer.items():
        b = N.delar[d]
        if b.typ != "H" or b.grupp not in ("yttervagg", "innervagg"):
            continue
        for s_, n_ in lista:
            H = m.x[n_, 2]
            for i in iW:
                u = float(np.hypot(*U[i, n_, :2]))
                if u / (H / K["drift"]) > drift["eta"]:
                    drift = {"eta": u / (H / K["drift"]), "u": u, "H": float(H), "del": b.namn, "komb": namn[i]}
    return {"takbalk": best, "drift": drift}
