"""
analys.py – statik och partiell samverkan för nock- och dalbalkar (stål–trä-komposit), rev C.

Kompositbalk   FE för symmetrisk balk plåt–liv–plåt med eftergivlig förbindning. Egenskaperna kan
               variera längs balken: där plåt saknas är balken ett rent limträtvärsnitt.
               Linjärelastisk teori för mekaniskt sammanfogade balkar (SS-EN 1995-1-1 9.1.3 och bilaga B),
               för godtyckliga stöd, laster, plåtlägen och skruvdelning. Temperatur som initialtöjning.
Balkanalys     Lastfall (kontinuerlig balk med fältvis snö, förankrade och lyftande stöd, fritt upplagda
               fält), temperaturpåverkan, dimensionering av skruvzoner och kontroller.

Teckenkonvention: w uppåt positiv, last nedåt positiv, M positivt för fältmoment,
stödreaktion uppåt positiv. Enheter N, mm, MPa.
"""
import itertools
import math

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

_GP = np.polynomial.legendre.leggauss(4)
INF = np.inf


def _form(xi, h):
    """Formfunktioner i punkten xi ∈ [0, 1] för element med längd h (array)."""
    h = np.asarray(h, float)
    o = np.ones_like(h)
    return dict(
        Nw=np.array([(1 - 3 * xi**2 + 2 * xi**3) * o, h * (xi - 2 * xi**2 + xi**3), (3 * xi**2 - 2 * xi**3) * o, h * (-xi**2 + xi**3)]),
        dNw=np.array([(-6 * xi + 6 * xi**2) / h, (1 - 4 * xi + 3 * xi**2) * o, (6 * xi - 6 * xi**2) / h, (-2 * xi + 3 * xi**2) * o]),
        ddNw=np.array([(-6 + 12 * xi) / h**2, (-4 + 6 * xi) / h, (6 - 12 * xi) / h**2, (-2 + 6 * xi) / h]),
        dddNw=np.array([12 / h**3, 6 / h**2, -12 / h**3, 6 / h**2]),
        Nu=np.array([(1 - xi) * (1 - 2 * xi) * o, 4 * xi * (1 - xi) * o, xi * (2 * xi - 1) * o]),
        dNu=np.array([(4 * xi - 3) / h, (4 - 8 * xi) / h, (4 * xi - 1) / h]),
    )


class Kompositbalk:
    """Överplåt axialförskjutning u, underplåt -u, liv 0 (symmetri). Glidning δ = u + a·w'.
    Energi per längd: ½·EI0·(w'')² + ½·2·EA·(u')² + ½·2·k·δ², k = K/s per fog [N/mm²].
    EI0, EA, k och EIw (livets andel av EI0, för temperaturkrökning) får variera per element.
    Axialfrihetsgrader i delar utan plåt (EA = k = 0) låses."""

    def __init__(self, xn, EI0, EA, a, k_el, EIw=None):
        xn = np.asarray(xn, float)
        self.xn, self.nn, self.ne = xn, len(xn), len(xn) - 1
        ne = self.ne
        self.EI0 = np.broadcast_to(np.asarray(EI0, float), (ne,)).copy()
        self.EA = np.broadcast_to(np.asarray(EA, float), (ne,)).copy()
        self.EIw = np.zeros(ne) if EIw is None else np.broadcast_to(np.asarray(EIw, float), (ne,)).copy()
        self.a = a
        self.ndof = 3 * self.nn + ne
        e = np.arange(ne)
        self.dofs = np.stack([3 * e, 3 * e + 1, 3 * e + 3, 3 * e + 4, 3 * e + 2, 3 * self.nn + e, 3 * e + 5], axis=1)
        h = np.diff(xn)
        self.h = h
        k = np.asarray(k_el, float)
        self.k = k
        ke = np.zeros((ne, 7, 7))
        z3, z4 = np.zeros((3, ne)), np.zeros((4, ne))
        for g, wg in zip(*_GP):
            S = _form(0.5 * (g + 1), h)
            B2 = np.vstack([S["ddNw"], z3])
            Bu = np.vstack([z4, S["dNu"]])
            Bd = np.vstack([a * S["dNw"], S["Nu"]])
            ke += (self.EI0[:, None, None] * np.einsum("ie,je->eij", B2, B2)
                   + 2 * self.EA[:, None, None] * np.einsum("ie,je->eij", Bu, Bu)
                   + 2 * k[:, None, None] * np.einsum("ie,je->eij", Bd, Bd)) * (wg * h / 2)[:, None, None]
        rows = np.repeat(self.dofs[:, :, None], 7, axis=2).ravel()
        cols = np.repeat(self.dofs[:, None, :], 7, axis=1).ravel()
        self.K = sp.csc_matrix((ke.ravel(), (rows, cols)), shape=(self.ndof, self.ndof))
        fw = -np.stack([h / 2, h * h / 12, h / 2, -h * h / 12], axis=1)
        self.Fmap = sp.csc_matrix((fw.ravel(), (self.dofs[:, :4].ravel(), np.repeat(e, 4))), shape=(self.ndof, ne))
        aktiv = (self.EA > 0) | (k > 0)
        alla_u = set(self.dofs[:, 4:].ravel().tolist())
        akt_u = set(self.dofs[aktiv, 4:].ravel().tolist())
        self.ufix = np.array(sorted(alla_u - akt_u), int)
        self._lu = {}

    # ------------------------------------------------------------------ lösning
    def _fria(self, fix):
        return np.setdiff1d(np.arange(self.ndof), np.union1d(fix, self.ufix))

    def _faktor(self, noder):
        key = tuple(sorted(set(int(n) for n in noder)))
        if key not in self._lu:
            if len(self._lu) > 200:
                self._lu.clear()
            fix = 3 * np.array(key, int)
            free = self._fria(fix)
            self._lu[key] = (fix, free, spla.splu(self.K[free][:, free].tocsc()))
        return key, self._lu[key]

    def los_F(self, F, noder):
        """Lösning för given lastvektor F (ndof, nfall)."""
        key, (fix, free, lu) = self._faktor(noder)
        U = np.zeros((self.ndof, F.shape[1]))
        U[free] = lu.solve(np.ascontiguousarray(F[free]))
        return U, list(key), (self.K @ U - F)[fix]

    def los(self, Q, noder):
        """Q: (ne, nfall) jämnt utbredd last nedåt per element [N/mm]. noder: stödnoder (w = 0)."""
        return self.los_F(self.Fmap @ Q, noder)

    def termisk_last(self, eps_a, kappa):
        """Lastvektor för fri töjning ±eps_a i över-/underplåt och fri krökning kappa i livet (per element)."""
        F = np.zeros(self.ndof)
        eps_a = np.broadcast_to(np.asarray(eps_a, float), (self.ne,))
        kappa = np.broadcast_to(np.asarray(kappa, float), (self.ne,))
        for g, wg in zip(*_GP):
            S = _form(0.5 * (g + 1), self.h)
            f = wg * self.h / 2
            np.add.at(F, self.dofs[:, 4:].T, 2 * self.EA * eps_a * S["dNu"] * f)
            np.add.at(F, self.dofs[:, :4].T, self.EIw * kappa * S["ddNw"] * f)
        return F[:, None]

    def los_kontakt(self, Q, fasta, ensidiga, fjader=None):
        """Stöd i 'fasta' tar tryck och drag. Stöd i 'ensidiga' tar endast tryck (balken kan lyfta).
        fjader: {nod: styvhet [N/mm]} – ensidigt elastiskt underlag (vägg) som bara tar tryck.
        Returnerar U, stödnoder, R (stöd × lastfall, 0 där balken lyft), fjäderkrafter, ändrade lastfall."""
        fjader = fjader or {}
        fn = sorted(fjader)
        kf = np.array([fjader[n] for n in fn])
        ens = sorted(set(ensidiga) - set(fasta))
        alla = sorted(set(fasta) | set(ens))
        pos = {n: i for i, n in enumerate(alla)}

        def los1(q, stod, aktiva_fj):
            akt = tuple(sorted(aktiva_fj))
            key = (tuple(sorted(stod)), akt)
            if key not in self._lu:
                if len(self._lu) > 200:
                    self._lu.clear()
                Kt = self.K
                if akt:
                    d = np.zeros(self.ndof)
                    d[3 * np.array(akt)] = [fjader[n] for n in akt]
                    Kt = Kt + sp.diags(d)
                fix = 3 * np.array(key[0], int)
                free = self._fria(fix)
                self._lu[key] = (fix, free, spla.splu(Kt.tocsc()[free][:, free].tocsc()))
            fix, free, lu = self._lu[key]
            F = self.Fmap @ q
            U = np.zeros((self.ndof, q.shape[1]))
            U[free] = lu.solve(np.ascontiguousarray(F[free]))
            Rf = np.zeros((len(fn), q.shape[1]))
            Fint = self.K @ U
            if akt:
                ia = [fn.index(n) for n in akt]
                Rf[ia] = -kf[ia, None] * U[3 * np.array(akt)]
                Fint[3 * np.array(akt)] += kf[ia, None] * U[3 * np.array(akt)]
            R = (Fint - F)[fix]
            return U, list(key[0]), R, Rf

        U, k0, R0, Rf = los1(Q, alla, fn)
        R = np.zeros((len(alla), Q.shape[1]))
        R[[pos[n] for n in k0]] = R0
        tol = 1e-7 * max(1.0, float(np.abs(R).max()) if R.size else 1.0)
        wf = U[3 * np.array(fn, int)] if fn else np.zeros((0, Q.shape[1]))
        andrad = np.zeros(Q.shape[1], bool)
        if ens:
            andrad |= (R[[pos[n] for n in ens]] < -tol).any(axis=0)
        if fn:
            andrad |= (wf > 1e-9).any(axis=0)
        for j in np.where(andrad)[0]:
            q = Q[:, [j]]
            aktiv, fa = set(ens), set(fn)
            sett = set()
            for _ in range(200):
                Uj, kj, Rj, Rfj = los1(q, set(fasta) | aktiv, fa)
                r = dict(zip(kj, Rj[:, 0]))
                drag = [n for n in aktiv if r[n] < -tol]
                pen = [n for n in ens if n not in aktiv and Uj[3 * n, 0] < -1e-9]
                fdrag = [n for n in fa if Uj[3 * n, 0] > 1e-9]
                fpen = [n for n in fn if n not in fa and Uj[3 * n, 0] < -1e-9]
                if not (drag or pen or fdrag or fpen):
                    break
                sett.add((frozenset(aktiv), frozenset(fa)))
                ny, nfa = (aktiv - set(drag)) | set(pen), (fa - set(fdrag)) | set(fpen)
                if (frozenset(ny), frozenset(nfa)) in sett:
                    if drag:
                        ny, nfa = aktiv - {min(drag, key=r.get)}, fa
                    elif pen:
                        ny, nfa = aktiv | {min(pen, key=lambda n: Uj[3 * n, 0])}, fa
                    elif fdrag:
                        ny, nfa = aktiv, fa - {max(fdrag, key=lambda n: Uj[3 * n, 0])}
                    else:
                        ny, nfa = aktiv, fa | {min(fpen, key=lambda n: Uj[3 * n, 0])}
                if len(set(fasta) | ny) + (2 if nfa else 0) < 2:
                    raise RuntimeError("balken saknar stöd i kontaktiterationen")
                aktiv, fa = ny, nfa
            else:
                raise RuntimeError("kontaktiterationen konvergerade inte")
            U[:, j] = Uj[:, 0]
            R[:, j] = 0.0
            for n, v in r.items():
                R[pos[n], j] = v
            Rf[:, j] = Rfj[:, 0]
        return U, alla, R, Rf, andrad

    def falt(self, U, pts=(0.05, 0.5, 0.95), eps_a=0.0):
        """Fält per element och punkt: x, w'', w''', N (överplåt, mekanisk), δ. Arrayer (element·punkter, lastfall)."""
        Ue = U[self.dofs]                                   # (ne, 7, nf)
        eps_a = np.broadcast_to(np.asarray(eps_a, float), (self.ne,))
        out = {k: [] for k in ("x", "e", "w2", "w3", "N", "dl")}
        for xi in pts:
            S = _form(xi, self.h)
            out["x"].append(self.xn[:-1] + xi * self.h)
            out["e"].append(np.arange(self.ne))
            out["w2"].append(np.einsum("ie,eif->ef", S["ddNw"], Ue[:, :4]))
            out["w3"].append(np.einsum("ie,eif->ef", S["dddNw"], Ue[:, :4]))
            out["N"].append(self.EA[:, None] * (np.einsum("ie,eif->ef", S["dNu"], Ue[:, 4:]) - eps_a[:, None]))
            out["dl"].append(self.a * np.einsum("ie,eif->ef", S["dNw"], Ue[:, :4]) + np.einsum("ie,eif->ef", S["Nu"], Ue[:, 4:]))
        o = {k: np.stack(v, axis=1) for k, v in out.items()}   # (ne, npts[, nf])
        return {k: (v.reshape(-1, v.shape[-1]) if v.ndim == 3 else v.reshape(-1)) for k, v in o.items()}


def snittkrafter(x, sup, R, segs):
    """M och V i punkter x ur stödreaktioner R (uppåt +) och laster segs = [(x0, x1, q)]."""
    x = np.asarray(x, float)
    V = np.zeros_like(x)
    M = np.zeros_like(x)
    for s, r in zip(sup, R):
        if r == 0.0:
            continue
        on = x > s
        V += np.where(on, r, 0.0)
        M += np.where(on, r * (x - s), 0.0)
    for a, b, q in segs:
        V -= q * np.clip(x - a, 0, b - a)
        M -= np.where(x > a, q * ((x - a) ** 2 - np.where(x > b, (x - b) ** 2, 0.0)) / 2, 0.0)
    return M, V


def rader_for(s, P):
    """Antal skruvrader per plåt för delningen s (växelvis), och radernas lägen från plåtkant."""
    n = 3 if s < P["s_tre_rader"] - 1e-9 else 2
    return n, P["rader"][n]


class Balkanalys:
    """Balk enligt B (dict): total, spann, typ ('nock'/'dal'), ev. vagg = [x0, x1] (balken vilar på vägg),
    ev. platar = [[x0, x1], ...] (plåtbitar; utan angivelse plåt hela längden).
    Utan vägg antas lika utstick i båda ändar: (total - summa spann) / 2."""

    def __init__(self, B, P, elementlangd=20.0):
        self.B, self.P = B, P
        L = float(B["total"])
        self.L = L
        if B.get("vagg"):
            v0, v1 = map(float, B["vagg"])
            huvud = [v1]
            for s in B["spann"]:
                huvud.append(huvud[-1] + s)
            self.zoner = [(0.0, v1)] + [(huvud[i], huvud[i + 1]) for i in range(len(huvud) - 1)]
            if huvud[-1] < L:
                self.zoner[-1] = (self.zoner[-1][0], L)
            self.vagg = (v0, v1)
        else:
            over = (L - sum(B["spann"])) / 2
            huvud = [over]
            for s in B["spann"]:
                huvud.append(huvud[-1] + s)
            self.zoner = [(huvud[i], huvud[i + 1]) for i in range(len(huvud) - 1)]
            self.zoner[0] = (0.0, self.zoner[0][1])
            self.zoner[-1] = (self.zoner[-1][0], L)
            self.vagg = None
        self.huvud = [float(h) for h in huvud]
        self.fria = [(huvud[i], huvud[i + 1]) for i in range(len(huvud) - 1)]
        self.platar = [tuple(map(float, p)) for p in B.get("platar", [[0.0, L]])]
        # nät
        p = sorted(set([0.0, L] + self.huvud + [z for zz in self.zoner for z in zz] + [q for pp in self.platar for q in pp]
                       + [float(f_[0]) for f_ in B.get("fjadrar", [])]
                       + ([B["koppling"]["x"] - B["koppling"]["e"], B["koppling"]["x"] + B["koppling"]["e"]] if B.get("koppling") else [])))
        xn = [0.0]
        for a, b in zip(p[:-1], p[1:]):
            n = max(1, int(math.ceil((b - a) / elementlangd - 1e-9)))
            xn += list(np.linspace(a, b, n + 1)[1:])
        self.xn = np.array(xn)
        self.ne = len(xn) - 1
        self.xm = 0.5 * (self.xn[:-1] + self.xn[1:])
        self.bit_el = np.full(self.ne, -1)
        for i, (p0, p1) in enumerate(self.platar):
            self.bit_el[(self.xm > p0) & (self.xm < p1)] = i
        self.plat_el = self.bit_el >= 0
        # ändavstånd för skruv per plåtände: vid balkände ändavstånd mot ändträ, annars mot plåtens ände
        self.bit_ande = [((P["ande"] if p0 < 1.0 else P["ande_plat"]), (P["ande"] if p1 > L - 1.0 else P["ande_plat"]))
                         for p0, p1 in self.platar]
        # tvärsnitt per element
        self.h_el = np.where(self.plat_el, P["hw"], P["h_tra"])
        self.egenskaper(P["E2fin"])
        nod = lambda x: int(np.argmin(np.abs(self.xn - x)))
        self.n_huvud = [nod(h) for h in self.huvud]
        self.fjader = {}
        if self.vagg:
            self.n_vagg = [i for i, x in enumerate(self.xn) if self.vagg[0] - 1e-6 <= x <= self.vagg[1] + 1e-6]
            kv = P.get("k_vagg", 1e4)
            v0, v1 = self.vagg
            for n in self.n_vagg:
                xl = self.xn[n - 1] if n > 0 else self.xn[n]
                xr = self.xn[n + 1] if n < self.ne else self.xn[n]
                self.fjader[n] = kv * (min(xr, v1) - max(xl, v0)) / 2
        else:
            self.n_vagg = []
        # övriga fjädrande stöd (t.ex. sträva): [[x, k]], tar bara tryck
        for xf_, kf_ in B.get("fjadrar", []):
            nf_ = nod(float(xf_))
            self.fjader[nf_] = self.fjader.get(nf_, 0.0) + float(kf_)
        # dubbeltriangel: två strävor på ömse sidor om en stolpe, kopplade som en gungbräda (styv triangel som
        # bara kan vrida sig kring stolpens topp, med stolpens böjstyvhet som rotationsfjäder)
        self.koppling = None
        if B.get("koppling"):
            kp = B["koppling"]
            nL, nR = nod(kp["x"] - kp["e"]), nod(kp["x"] + kp["e"])
            Kp, kr = 1.0e7, kp["kth"] / (2 * kp["e"]) ** 2
            self.koppling = (nL, nR, np.array([[Kp + kr, Kp - kr], [Kp - kr, Kp + kr]]), kp)
        # laster: egenvikt per element (plåt bara där den finns), snö på alla kombinationer av zoner
        typ = B["typ"]
        S = P["S"][typ]
        if "Gtak" in P:
            G0 = P["Gtak"][typ] + P["g_utan"]
            dG = P["g_med"] - P["g_utan"]
        else:
            G0, dG = P["G"][typ], 0.0
        self.G_el = G0 + dG * self.plat_el
        G = G0 + dG
        self.G, self.S = G, S
        gd, psi0 = P["gamma_d"], P["psi0"]
        self.qd = gd * (1.2 * G + 1.5 * S)
        self.qd_el = gd * (1.2 * self.G_el + 1.5 * S)
        self.r_psi = gd * (1.2 * G + 1.5 * psi0 * S) / self.qd      # snö som följdlast, relativt
        self.kombinationer = [("6.10b", gd * 1.2, gd * 1.5), ("6.10a", gd * 1.35, gd * 1.5 * psi0), ("G gynnsam", 1.0, gd * 1.5)]

        def gsegs(gG):
            return [(0.0, L, gG * G0)] + ([(p0, p1, gG * dG) for p0, p1 in self.platar] if dG else [])
        self._gsegs = gsegs
        nz = len(self.zoner)
        Q, segs, info = [], [], []
        for mask in itertools.product([0, 1], repeat=nz):
            for namn, gG, gS in self.kombinationer:
                q = gG * self.G_el.copy()
                sg = gsegs(gG)
                for i, on in enumerate(mask):
                    if on:
                        a_, b_ = self.zoner[i]
                        q = q + np.where((self.xm > a_) & (self.xm < b_), gS * S, 0.0)
                        sg.append((a_, b_, gS * S))
                Q.append(q); segs.append(sg); info.append((namn, mask))
        self.Q, self.segs, self.lastinfo = np.array(Q).T, segs, info
        # vindlyft: 1,0 G + gamma_d 1,5 W, med zonerna G/H/I räknade från båda balkändarna (vind längs nocken)
        self.QW, self.segsW = None, None
        V = P.get("vind")
        if V:
            w = V["w"][typ]                                     # dict zon -> linjelast [N/mm], uppåt negativ
            e10, e2 = V["e"] / 10, V["e"] / 2
            br = sorted(set([0.0, L] + [x for x in (e10, e2, L - e2, L - e10) if 0 < x < L]))
            sgW, qW = gsegs(1.0), self.G_el.copy()
            for x0, x1 in zip(br[:-1], br[1:]):
                d = min((x0 + x1) / 2, L - (x0 + x1) / 2)
                z = "G" if d < e10 else ("H" if d < e2 else "I")
                qz = gd * 1.5 * w[z]
                sgW.append((x0, x1, qz))
                qW = qW + np.where((self.xm > x0) & (self.xm < x1), qz, 0.0)
            self.QW, self.segsW = qW[:, None], [sgW]
        self.ss = []
        for a_, b_ in self.fria:
            lo = 0.0 if (a_ == self.huvud[0] and not self.vagg) else a_
            hi = L if b_ == self.huvud[-1] else b_
            self.ss.append((lo, hi, a_, b_))

    def egenskaper(self, E2):
        """Böjstyvheter per element för livets elasticitetsmodul E2."""
        P = self.P
        I_h = P["b"] * self.h_el ** 3 / 12
        self.EIw = E2 * I_h
        self.EI0 = np.where(self.plat_el, 2 * P["Es"] * P["I1"], 0.0) + self.EIw
        self.EA_el = np.where(self.plat_el, P["EA"], 0.0)
        return self.EI0, self.EA_el, self.EIw

    # ------------------------------------------------------------------ styvhet i fogen
    def k_fog(self, s_el, K, andzon=True, k_full=None):
        """Förbindningens styvhet per element och fog [N/mm²]. Utan plåt 0. Nära plåtändar (skruvfri
        ändsträcka) 0. k_full: jämn styvhet för limfog (ingen skruvfri ändsträcka)."""
        if k_full is not None:
            if np.ndim(k_full) > 0:
                return np.asarray(k_full, float)
            return np.where(self.plat_el, k_full, 0.0)
        with np.errstate(divide="ignore"):
            k = np.where(self.plat_el, K / s_el, 0.0)
        if andzon:
            for i, (p0, p1) in enumerate(self.platar):
                e0, e1 = self.bit_ande[i]
                sel = self.bit_el == i
                s = np.where(np.isfinite(s_el), s_el, 0.0)
                k = np.where(sel & ((self.xm < p0 + e0 - s / 2) | (self.xm > p1 - e1 + s / 2)), 0.0, k)
        return k

    def modell(self, k_el, xs=None):
        i0, i1 = (0, self.ne) if xs is None else xs
        m = Kompositbalk(self.xn[i0:i1 + 1], self.EI0[i0:i1], self.EA_el[i0:i1], self.P["a"], k_el[i0:i1], self.EIw[i0:i1])
        if self.koppling and xs is None:
            nL, nR, Kc, _ = self.koppling
            iL, iR = 3 * nL, 3 * nR
            M = sp.coo_matrix((Kc.ravel(), ([iL, iL, iR, iR], [iL, iR, iL, iR])), shape=m.K.shape)
            m.K = (m.K + M).tocsc()
            m._lu = {}
        return m

    def kopplingskrafter(self, U):
        """Strävornas krafter på balken (uppåt +) och deras lägen, för dubbeltriangeln."""
        if not self.koppling:
            return np.zeros((0, U.shape[1])), []
        nL, nR, Kc, _ = self.koppling
        F = -(Kc @ np.vstack([U[3 * nL], U[3 * nR]]))
        return F, [float(self.xn[nL]), float(self.xn[nR])]

    # ------------------------------------------------------------------ körning
    def kor(self, s_el, K, andzon=True, k_full=None):
        """Alla modeller för given skruvdelning och förskjutningsmodul.
        A: huvudstöd förankrade (tar drag), vägg ensidig.  B: alla stöd ensidiga (stöd kan lyfta).
        SS: varje fält fritt upplagt med full last."""
        k_el = self.k_fog(s_el, K, andzon, k_full)
        m = self.modell(k_el)
        res = []
        fasta = [n for n in self.n_huvud if n not in self.n_vagg]
        U, alla, R, Rf, _ = m.los_kontakt(self.Q, fasta, [], self.fjader)
        Fk, xk = self.kopplingskrafter(U)
        sup = [float(self.xn[n]) for n in alla] + [float(self.xn[n]) for n in sorted(self.fjader)] + xk
        wl = float(U[3 * np.array(sorted(self.fjader))].max()) if self.fjader else 0.0
        res.append(dict(typ="A", f=m.falt(U), R=np.vstack([R, Rf, Fk]), sup=sup, segs=self.segs, K=K, wlyft=wl, k_el=k_el))
        if self.QW is not None:
            # vindlyft: huvudstöd och vägg förankrade (tar drag)
            # vindlyft: huvudstöd förankrade, väggen som fjädrande underlag som också tar drag (balken fäst i väggen)
            fW = sorted(set(fasta))
            fn = sorted(self.fjader)
            d = np.zeros(m.ndof)
            if fn:
                d[3 * np.array(fn)] = [self.fjader[n] for n in fn]
            K2 = (m.K + sp.diags(d)).tocsc()
            fix = 3 * np.array(fW, int)
            free = m._fria(fix)
            F = m.Fmap @ self.QW
            UW = np.zeros((m.ndof, 1))
            UW[free] = spla.spsolve(K2[free][:, free], F[free]).reshape(-1, 1)
            RW = (K2 @ UW - F)[fix]
            if fn:
                RW = np.vstack([RW, -np.array([self.fjader[n] for n in fn])[:, None] * UW[3 * np.array(fn)]])
            FkW, xkW = self.kopplingskrafter(UW)
            res.append(dict(typ="A", vind=True, f=m.falt(UW), R=np.vstack([RW, FkW]),
                            sup=[float(self.xn[n]) for n in fW] + [float(self.xn[n]) for n in fn] + xkW,
                            segs=self.segsW, K=K, k_el=k_el))
        if not self.vagg:
            Ub, alla_b, Rb, _, andr = m.los_kontakt(self.Q, [], self.n_huvud)
            if andr.any():
                j = np.where(andr)[0]
                Fkb, xkb = self.kopplingskrafter(Ub[:, j])
                res.append(dict(typ="B", f=m.falt(Ub[:, j]), R=np.vstack([Rb[:, j], Fkb]), sup=[float(self.xn[n]) for n in alla_b] + xkb,
                                segs=[self.segs[i] for i in j], K=K, k_el=k_el))
        for lo, hi, a_, b_ in self.ss:
            i0 = int(np.argmin(np.abs(self.xn - lo)))
            i1 = int(np.argmin(np.abs(self.xn - hi)))
            ms = self.modell(k_el, (i0, i1))
            na = int(np.argmin(np.abs(ms.xn - a_))); nb = int(np.argmin(np.abs(ms.xn - b_)))
            Us, ks, Rs = ms.los(self.qd_el[i0:i1, None], [na, nb])
            f = ms.falt(Us)
            f["e"] = f["e"] + i0
            gd = self.P["gamma_d"]
            sgs = [(lo, hi, gd * 1.5 * self.S)] + [(max(lo, x0), min(hi, x1), gd * 1.2 * qq) for x0, x1, qq in self._gsegs(1.0)
                                                    if min(hi, x1) > max(lo, x0)]
            res.append(dict(typ="SS", f=f, R=Rs, sup=[float(ms.xn[n]) for n in ks], segs=[sgs], K=K, k_el=k_el))
        return res

    # ------------------------------------------------------------------ temperatur
    def temperatur(self, s_el, K, andzon=True, k_full=None):
        """Temperaturpåverkan (karakteristisk) per element för fallen i P['temperatur'].
        Antisymmetrisk del (olika temperatur i över- och underplåt, krökning i livet): FE med kontinuerlig
        balk (förankrade stöd) och fritt upplagda fält. Symmetrisk del (lika temperatur i plåtarna):
        skjuvförskjutning mellan plåt och liv, analytiskt per plåtbit. Returnerar per element största
        skjuvflöde q i en fog [N/mm], skruvkraft [N], största normalspänning i plåt [MPa] och
        nedböjning i varje fält [mm] (fritt upplagt, nedåt positiv)."""
        P = self.P
        k_el = self.k_fog(s_el, K, andzon, k_full)
        a = P["a"]
        q_max = np.zeros(self.ne)
        sig = np.zeros(self.ne)
        w_falt = np.zeros((len(self.fria), len(P["temperatur"])))
        c = 1 / P["EA"] + 2 / (P["Et"] * P["b"] * P["hw"])           # axialflexibilitet plåt + halva livet
        for jf, T in enumerate(P["temperatur"]):
            dTo, dTu = T["over"], T["under"]
            eps_a = np.where(self.plat_el, P["alfa_s"] * (dTo - dTu) / 2, 0.0)
            kappa = -P["alfa_t"] * (dTo - dTu) / (2 * a)
            qf = np.zeros(self.ne)          # detta fall: antisymmetrisk del (största av modellerna)
            sf = np.zeros(self.ne)
            # antisymmetrisk del, kontinuerlig balk (stöd och vägg låsta)
            m = self.modell(k_el)
            fasta = [n for n in self.n_huvud if n not in self.n_vagg] + list(self.n_vagg)
            U, _, _ = m.los_F(m.termisk_last(eps_a, kappa), fasta)
            f = m.falt(U, eps_a=eps_a)
            np.maximum.at(qf, f["e"], np.abs(k_el[f["e"]][:, None] * f["dl"]).max(axis=1))
            np.maximum.at(sf, f["e"], (np.abs(f["N"]).max(axis=1) / P["A1"]) * self.plat_el[f["e"]])
            # antisymmetrisk del, fritt upplagda fält
            for jj, (lo, hi, a_, b_) in enumerate(self.ss):
                i0 = int(np.argmin(np.abs(self.xn - lo)))
                i1 = int(np.argmin(np.abs(self.xn - hi)))
                ms = self.modell(k_el, (i0, i1))
                na = int(np.argmin(np.abs(ms.xn - a_))); nb = int(np.argmin(np.abs(ms.xn - b_)))
                Us, _, _ = ms.los_F(ms.termisk_last(eps_a[i0:i1], kappa), [na, nb])
                fs = ms.falt(Us, eps_a=eps_a[i0:i1])
                e = fs["e"] + i0
                np.maximum.at(qf, e, np.abs(k_el[e][:, None] * fs["dl"]).max(axis=1))
                np.maximum.at(sf, e, (np.abs(fs["N"]).max(axis=1) / P["A1"]) * self.plat_el[e])
                w_falt[jj, jf] = -Us[0:3 * len(ms.xn):3, 0].min()
            # symmetrisk del per plåtbit (skjuvförskjutning, lösning med hyperboliska funktioner)
            dTm = (dTo + dTu) / 2
            Ninf = abs((P["alfa_s"] - P["alfa_t"]) * dTm / c)
            for i, (p0, p1) in enumerate(self.platar):
                sel = np.where(self.bit_el == i)[0]
                kk = k_el[sel]
                if not (kk > 0).any():
                    continue
                xc, Lp = (p0 + p1) / 2, p1 - p0
                for sida in (-1, 1):
                    nara = sel[np.abs(self.xm[sel] - (p0 if sida < 0 else p1)) < 400]
                    kn = k_el[nara]
                    kref = kn[kn > 0].mean() if (kn > 0).any() else kk[kk > 0].mean()
                    lam = math.sqrt(kref * c)
                    half = sel[(self.xm[sel] - xc) * sida >= 0]
                    xr = np.abs(self.xm[half] - xc)
                    qf[half] += Ninf * lam * np.sinh(lam * xr) / math.cosh(lam * Lp / 2) * (k_el[half] > 0)
                    sf[half] += Ninf / P["A1"] * (1 - np.cosh(lam * xr) / math.cosh(lam * Lp / 2))
            q_max = np.maximum(q_max, qf)
            sig = np.maximum(sig, sf)
        with np.errstate(divide="ignore", invalid="ignore"):
            F_skruv = np.where(k_el > 0, q_max * K / np.where(k_el > 0, k_el, 1.0), 0.0)
        return dict(q=q_max, F=F_skruv, sig=sig, w=w_falt, k_el=k_el)

    def skruvkraft(self, res):
        """Största skruvkraft K·|δ| per element (bara där det finns skruv, k > 0)."""
        Fe = np.zeros(self.ne)
        for r in res:
            e = r["f"]["e"]
            F = r["K"] * np.abs(r["f"]["dl"]).max(axis=1) * (r["k_el"][e] > 0)
            np.maximum.at(Fe, e, F)
        return Fe

    def kombinera(self, F_last, F_temp):
        """Skruvkraft i brottgräns: snö huvudlast + temperatur följdlast, eller temperatur huvudlast + snö följdlast."""
        P = self.P
        c1 = P["gamma_d"] * 1.5 * P["psi0_T"]
        c2 = P["gamma_d"] * 1.5
        return np.maximum(F_last + c1 * F_temp, self.r_psi * F_last + c2 * F_temp)

    def utnyttjande(self, res, s_el, Lcr=None, sig_T=None):
        """Utnyttjandegrad per element för stål- och träkontroller (max över körningar och lastfall)."""
        P = self.P
        s_el = np.asarray(s_el, float)
        nr = np.where(s_el < P["s_tre_rader"] - 1e-9, 3, 2)
        Lcr = nr * s_el if Lcr is None else np.asarray(Lcr)
        NuRd = np.where(nr == 3, P["NuRd3"], P["NuRd"])
        U = {k: np.zeros(self.ne) for k in ("plat", "knack", "netto", "livbojning", "livskjuv")}
        pl = self.plat_el
        dsig = np.zeros(self.ne) if sig_T is None else P["gamma_d"] * 1.5 * P["psi0_T"] * sig_T
        for r in res:
            f, e = r["f"], r["f"]["e"]
            k = r["k_el"][e]
            he = self.h_el[e]
            S2 = P["b"] * he ** 2 / 8
            N = f["N"]
            w2 = np.abs(f["w2"])
            sig_pl = np.abs(N) / P["A1"] + P["Es"] * w2 * P["t"] / 2 + dsig[e][:, None]
            sig_m2 = P["E2fin"] * w2 * (he / 2)[:, None]
            tau = np.abs(k[:, None] * f["dl"] - P["E2fin"] * S2[:, None] * f["w3"]) / P["b"]
            with np.errstate(divide="ignore", invalid="ignore"):
                NbRd = np.where(np.isfinite(Lcr[e]), P["NbRd"](np.where(np.isfinite(Lcr[e]), Lcr[e], 1.0)), 1.0)
            Ntr = np.abs(N).max(axis=1) + dsig[e] * P["A1"]
            np.maximum.at(U["plat"], e, sig_pl.max(axis=1) / P["fyd"] * pl[e])
            np.maximum.at(U["knack"], e, Ntr / NbRd * pl[e])
            np.maximum.at(U["netto"], e, Ntr / NuRd[e] * pl[e])
            np.maximum.at(U["livbojning"], e, sig_m2.max(axis=1) / P["fmd"])
            np.maximum.at(U["livskjuv"], e, tau.max(axis=1) / P["tauRd"])
        return U

    # ------------------------------------------------------------------ dimensionering
    def dimensionera(self, s_lista, s_tak, zon_min=200.0, max_it=40, fonster=400.0, tak0=None):
        """Skruvdelning per element i plåtbitarna: så glest som möjligt (högst s_tak) med skruvkraft
        (laster + temperatur) ≤ F_Rd och stål-/träkontroller ≤ 1. Den godkända lösningen med minst skruv behålls."""
        P = self.P
        sl = sorted(float(v) for v in s_lista)
        pl = self.plat_el

        def till(s):
            ok = [v for v in sl if v <= s + 1e-9]
            return ok[-1] if ok else sl[0]

        def tatare(s):
            return sl[max(0, sl.index(till(s)) - 1)]

        tak = np.where(pl, till(s_tak), INF)
        if tak0 is not None:
            tak = np.where(pl, [till(v) if np.isfinite(v) else till(s_tak) for v in np.minimum(tak, tak0)], INF)
        s_el = tak.copy()
        hist, bast = [], None
        n = 0
        for it in range(max_it):
            res_up = self.kor(s_el, P["K_up"])
            res_lo = self.kor(s_el, P["K_low"])
            FT = self.temperatur(s_el, P["K_up"])
            Fe = self.kombinera(self.skruvkraft(res_up + res_lo), FT["F"])
            U = self.utnyttjande(res_up + res_lo, s_el, sig_T=FT["sig"])
            u_tra = np.maximum.reduce([U[k] for k in U])
            ok_F = Fe <= P["F_Rd"] * (1 + 1e-9)
            ok_u = u_tra <= 1.0 + 1e-9
            n = self.antal(s_el)
            hist.append((it, n, float(Fe.max() / P["F_Rd"]), float(u_tra.max())))
            if ok_F.all() and ok_u.all() and (bast is None or n < bast[0]):
                bast = (n, s_el.copy(), res_up, res_lo, Fe, U)
            if not ok_u.all():
                bad = self.xm[~ok_u & pl]
                nara = np.zeros(self.ne, bool)
                for xb in bad:
                    nara |= np.abs(self.xm - xb) <= fonster
                nara &= pl
                tak[nara] = np.array([tatare(s) for s in s_el[nara]])
            ny = s_el.copy()
            for i in np.where(pl)[0]:
                fakt = P["F_Rd"] / max(Fe[i], 1e-9) * 0.98
                ny[i] = till(min(s_el[i] * min(fakt, 1.5), tak[i]))
            ny = self._jamna(ny, zon_min, tak)
            if np.array_equal(ny, s_el):
                break
            s_el = ny
        self.historik = hist
        self.konvergerad = bast is not None
        if bast is None:
            bast = (n, s_el, res_up, res_lo, Fe, U)
        _, self.s_el, self.res_up, self.res_lo, self.Fe, self.U = bast
        return self.s_el

    def _jamna(self, s_el, zon_min, tak):
        """Slår ihop zoner kortare än zon_min inom varje plåtbit (zoner utan plåt lämnas orörda)."""
        s_el = np.minimum(s_el, tak).astype(float)
        for _ in range(5000):
            z = self.zoner_av(s_el)
            kort = [i for i, (x0, x1, s) in enumerate(z) if np.isfinite(s) and x1 - x0 < zon_min - 1e-6
                    and any(np.isfinite(z[j][2]) for j in (i - 1, i + 1) if 0 <= j < len(z))]
            if not kort:
                break
            i = min(kort, key=lambda k: z[k][1] - z[k][0])
            x0, x1, s = z[i]
            sel = np.where((self.xm > x0) & (self.xm < x1))[0]
            e0, e1 = int(sel[0]), int(sel[-1])
            bit = self.bit_el[e0]
            ib = np.where(self.bit_el == bit)[0]
            b0, b1 = int(ib[0]), int(ib[-1])
            nb = [z[j][2] for j in (i - 1, i + 1) if 0 <= j < len(z) and np.isfinite(z[j][2])]
            if s <= min(nb):
                vanster = True
                while self.xn[e1 + 1] - self.xn[e0] < zon_min - 1e-6 and (e0 > b0 or e1 < b1):
                    if (vanster and e0 > b0) or e1 == b1:
                        e0 -= 1
                    else:
                        e1 += 1
                    vanster = not vanster
                s_el[e0:e1 + 1] = np.minimum(s_el[e0:e1 + 1], s)
            else:
                s_el[e0:e1 + 1] = min(nb)
        return s_el

    def zoner_av(self, s_el=None):
        s_el = self.s_el if s_el is None else s_el
        z, start = [], 0
        for e in range(1, self.ne + 1):
            if e == self.ne or s_el[e] != s_el[start] or self.bit_el[e] != self.bit_el[start]:
                z.append((float(self.xn[start]), float(self.xn[e]), float(s_el[start])))
                start = e
        return z

    def praktiska_zoner(self, s_el=None, steg=10.0):
        """Zoner per plåtbit med inre gränser avrundade till 'steg' mm så att den tätare zonen aldrig blir kortare.
        Returnerar {bit: [(x0, x1, s), ...]}."""
        ut = {}
        for i, (p0, p1) in enumerate(self.platar):
            z = [zz for zz in self.zoner_av(s_el) if zz[0] >= p0 - 1e-6 and zz[1] <= p1 + 1e-6 and np.isfinite(zz[2])]
            gr = [p0]
            for (a0, b0, s0), (a1, b1, s1) in zip(z[:-1], z[1:]):
                gr.append(math.ceil(b0 / steg) * steg if s0 < s1 else math.floor(b0 / steg) * steg)
            gr.append(p1)
            rad = []
            for (x0, x1), (_, _, s) in zip(zip(gr[:-1], gr[1:]), z):
                if x1 - x0 > 1e-6:
                    if rad and rad[-1][2] == s:
                        rad[-1] = (rad[-1][0], x1, s)
                    else:
                        rad.append((x0, x1, s))
            ut[i] = rad
        return ut

    def skruvschema(self, s_el=None):
        """Skruvlägen per plåtbit. Från varje plåtände stegas med zonens delning s (med hänsyn till tätare zon
        inom steget), och de två serierna möts i den längsta glesaste zonen. Skruvarna sätts växelvis i de två
        raderna. Returnerar [(bit, x0, x1, s, antal)], {bit: lägen}."""
        pz = self.praktiska_zoner(s_el)
        rader, lagen = [], {}
        for i, (p0, p1) in enumerate(self.platar):
            z = pz[i]
            e0, e1 = self.bit_ande[i]
            a, b = p0 + e0, p1 - e1

            def s_vid(x):
                for x0, x1, s in z:
                    if x0 - 1e-9 <= x < x1 - 1e-9:
                        return s
                return z[-1][2]

            def s_min(u, v):
                return min(s for x0, x1, s in z if x1 > u + 1e-9 and x0 < v - 1e-9)

            def steg(p, r):
                st = s_vid(p if r > 0 else p - 1e-6)
                for _ in range(20):
                    st2 = s_min(p, p + st) if r > 0 else s_min(p - st, p)
                    if st2 >= st - 1e-9:
                        break
                    st = st2
                return st

            smax = max(s for _, _, s in z)
            zj = max((zz for zz in z if zz[2] == smax), key=lambda zz: zz[1] - zz[0])
            xj = min(max(0.5 * (zj[0] + zj[1]), a), b)
            vl, p = [], a
            while p <= xj + 1e-9:
                vl.append(p)
                p += steg(p, +1)
            hl, q = [], b
            while q > vl[-1] + 1e-6:
                hl.append(q)
                if q - vl[-1] <= s_min(vl[-1], q) + 1e-9:
                    break
                q -= steg(q, -1)
            pos = np.array(sorted(vl + hl))
            k = len(vl) - 1
            if 0 < k < len(pos) - 1 and pos[k + 1] - pos[k] < 0.5 * s_min(pos[k - 1], pos[k + 1]):
                pos[k] = 0.5 * (pos[k - 1] + pos[k + 1])
            # radplacering: i varje zon 2 eller 3 rader; skruven läggs i den rad som varit oanvänd längst,
            # med kravet c/c i raden ≥ a1 (7d)
            senast = {}
            ys = []
            for xp in pos:
                n_r, Y = rader_for(s_vid(xp), self.P)
                kand = sorted(Y, key=lambda y: senast.get(y, -1e9))
                val = next((y for y in kand if xp - senast.get(y, -1e9) >= self.P["a1_rad"] - 1e-6), kand[0])
                senast[val] = xp
                ys.append(val)
            lagen[i] = np.column_stack([pos, ys])
            for j, (x0, x1, s) in enumerate(z):
                sista = j == len(z) - 1
                nn = int(((pos >= x0 - 1e-9) & ((pos < x1 - 1e-9) | sista)).sum())
                rader.append((i, x0, x1, s, nn, rader_for(s, self.P)[0]))
        return rader, lagen

    def verifiera(self, lagen):
        """Kontroll av det verkliga skruvschemat (lägen per plåtbit). Varje element får avståndet mellan de två
        skruvar som omger det och knäcklängden c/c i samma rad. Ersätter resultaten från dimensioneringen."""
        P = self.P
        s_akt = np.full(self.ne, INF)
        Lcr = np.full(self.ne, INF)
        for i, xy in lagen.items():
            xy = np.asarray(xy, float)
            pos = xy[:, 0]
            g = np.diff(pos)
            sel = np.where(self.bit_el == i)[0]
            j = np.clip(np.searchsorted(pos, self.xm[sel]) - 1, 0, len(g) - 1)
            s_akt[sel] = g[j]
            # knäcklängd: största c/c i någon av zonens rader som spänner över elementet
            pz = self.praktiska_zoner()[i]
            for e in sel:
                sz = next((s for x0, x1, s in pz if x0 - 1e-9 <= self.xm[e] < x1 + 1e-9), pz[-1][2])
                _, Y = rader_for(sz, P)
                L = 0.0
                for y in Y:
                    px = pos[np.abs(xy[:, 1] - y) < 1e-6]
                    if len(px) >= 2:
                        k = np.clip(np.searchsorted(px, self.xm[e]) - 1, 0, len(px) - 2)
                        L = max(L, px[k + 1] - px[k])
                Lcr[e] = L if L > 0 else 2 * g[j[np.where(sel == e)[0][0]]]
        res_up = self.kor(s_akt, P["K_up"])
        res_lo = self.kor(s_akt, P["K_low"])
        FT = self.temperatur(s_akt, P["K_up"])
        self.s_akt, self.Lcr, self.FT = s_akt, Lcr, FT
        self.res_up, self.res_lo = res_up, res_lo
        self.Fe_last = self.skruvkraft(res_up + res_lo)
        self.Fe = self.kombinera(self.Fe_last, FT["F"])
        self.U = self.utnyttjande(res_up + res_lo, s_akt, Lcr, sig_T=FT["sig"])
        u = max(float(self.Fe.max() / P["F_Rd"]), max(float(v.max()) for v in self.U.values()))
        self.verifierad = u <= 1.0 + 1e-9
        return u

    def dimensionera_och_kontrollera(self, s_lista, s_tak, zon_min=200.0, fonster=400.0, max_varv=8):
        """Dimensionera, gör skruvschema och kontrollera med verkliga lägen. Klarar inte schemat kontrollen
        förtätas skruven kring de snitt som inte klarar sig och allt görs om."""
        sl = sorted(float(v) for v in s_lista)
        tak0 = np.where(self.plat_el, float(s_tak), INF)
        for _ in range(max_varv):
            self.dimensionera(sl, s_tak, zon_min=zon_min, fonster=fonster, tak0=tak0)
            rad, lagen = self.skruvschema()
            u = self.verifiera(lagen)
            if u <= 1.0 + 1e-9:
                return rad, lagen
            ufel = np.maximum.reduce([self.Fe / self.P["F_Rd"]] + [v for v in self.U.values()])
            for xb in self.xm[(ufel > 1.0 + 1e-9) & self.plat_el]:
                nara = (np.abs(self.xm - xb) <= fonster) & self.plat_el
                tak0[nara] = np.minimum(tak0[nara], [sl[max(0, sum(v <= s + 1e-9 for v in sl) - 2)] for s in self.s_akt[nara]])
        return rad, lagen

    def antal(self, s_el=None):
        """Antal skruvar per plåtlag (summa över plåtbitarna i över- eller underkant)."""
        return sum(len(p) for p in self.skruvschema(s_el)[1].values())

    # ------------------------------------------------------------------ resultat
    def alla_kor(self, med_full=True):
        return self.res_up + self.res_lo + (getattr(self, "res_full", []) if med_full else [])

    def k_limfog(self, k_lim, s_el, K_skruv, L_u):
        """Fogstyvhet med lim: k_lim i plåtbitarna utom inom L_u från varje plåtände (olimmad ändzon, där
        bara skruvarna verkar med K_skruv/s). L_u: ett värde eller [(vänster, höger)] per plåtbit. Returnerar styvhet och mask för limmad del."""
        k_skr = self.k_fog(s_el, K_skruv)
        lim = self.plat_el.copy()
        for i, (p0, p1) in enumerate(self.platar):
            u0, u1 = (L_u, L_u) if np.ndim(L_u) == 0 else L_u[i]
            lim &= ~(((self.xm > p0) & (self.xm < p0 + u0)) | ((self.xm < p1) & (self.xm > p1 - u1)))
        return np.where(lim, k_lim, k_skr), lim

    def full_samverkan(self, k_arr):
        """Samma modeller med limfog (styvhet per element k_arr)."""
        self.res_full = self.kor(np.where(self.plat_el, 100.0, INF), 1.0, andzon=False, k_full=k_arr)
        return self.omhyllning(korningar=self.res_full)

    def omhyllning(self, npunkt=2000, korningar=None):
        """Omhyllande M (max, min) och |V| ur statik med reaktionerna från samtliga körningar."""
        x = np.unique(np.r_[np.linspace(0, self.L, npunkt), np.array(self.huvud) - 1e-3, np.array(self.huvud) + 1e-3])
        x = x[(x >= 0) & (x <= self.L)]
        Mmax = np.zeros_like(x); Mmin = np.zeros_like(x); V = np.zeros_like(x)
        for r in (self.alla_kor() if korningar is None else korningar):
            for j, sg in enumerate(r["segs"]):
                Rj = r["R"][:, j]
                if r["typ"] == "SS":
                    lo, hi = sg[0][0], sg[0][1]
                    sel = (x >= lo) & (x <= hi)
                    M, Vv = snittkrafter(x[sel], r["sup"], Rj, sg)
                    Mmax[sel] = np.maximum(Mmax[sel], M); Mmin[sel] = np.minimum(Mmin[sel], M)
                    V[sel] = np.maximum(V[sel], np.abs(Vv))
                else:
                    M, Vv = snittkrafter(x, r["sup"], Rj, sg)
                    Mmax = np.maximum(Mmax, M); Mmin = np.minimum(Mmin, M); V = np.maximum(V, np.abs(Vv))
        return x, Mmax, Mmin, V

    def reaktioner(self):
        """Per huvudstöd: största reaktion (alla körningar) och minsta reaktion med förankrat stöd (körning A)."""
        out = []
        for s, n in zip(self.huvud, self.n_huvud):
            Rmax, Rmin = 0.0, 0.0
            first = True
            arvagg = bool(self.vagg and n in self.n_vagg)
            for r in self.alla_kor():
                if s in r["sup"] and not (arvagg and r["typ"] != "SS"):
                    v = r["R"][r["sup"].index(s)]
                    Rmax = max(Rmax, float(v.max()))
                    if r["typ"] == "A":
                        Rmin = float(v.min()) if first else min(Rmin, float(v.min()))
                        first = False
            d = dict(x=s, Rmax=Rmax, Rmin=Rmin, vagg=arvagg)
            if arvagg:
                tot, kant, lyft = 0.0, Rmax, 0.0
                for r in self.alla_kor():
                    if r["typ"] == "A":
                        xs = np.array(r["sup"])
                        iv = np.where((xs >= self.vagg[0] - 1e-6) & (xs <= self.vagg[1] + 1e-6))[0]
                        Rv = r["R"][iv]
                        tot = max(tot, float(Rv.sum(axis=0).max()))
                        kant = max(kant, float(Rv[xs[iv] >= self.vagg[1] - 500.0].sum(axis=0).max()))
                        if r.get("vind"):
                            lyft = min(lyft, float(Rv.sum(axis=0).min()))
                d.update(Rvagg=tot, Rmax=kant, Rmin=0.0, Rvagg_lyft=lyft)
            out.append(d)
        return out

    def max_utn(self):
        """Största utnyttjande per kontroll med läge."""
        o = {}
        for k, u in list(self.U.items()) + [("skruv", self.Fe / self.P["F_Rd"])]:
            i = int(np.argmax(u))
            o[k] = (float(u[i]), float(self.xm[i]))
        return o
