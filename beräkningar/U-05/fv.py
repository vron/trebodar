"""
U-05: stationär värmeledning med finita volymer på rektangulärt nät, i två eller tre dimensioner.

Nätet ges av cellkanterna längs varje axel (m). Varje cell är antingen fast material (med λ, eventuellt olika längs
axlarna för homogeniserade skikt) eller tom. Tomma celler hör till en omgivning (rumsluft, uteluft, golvvärmens
slingor …) med ett ytmotstånd R_s mot de fasta celler de gränsar till, eller är adiabatiska. Nätets ytterränder är
adiabatiska om de inte får en omgivning (t.ex. ostörd mark på visst djup).

Värmeflödet över en yta mellan två fasta celler i och j längs axel a: G = A / (d_i/λ_i,a + d_j/λ_j,a), där d är
halva cellens storlek längs a. Mellan en fast cell och en omgivning: G = A / (d_i/λ_i,a + R_s). Systemet K T = b är
symmetriskt och positivt definit; det löses med LU (2D) eller med AMG-förbehandlad CG (3D, pyamg).

Eftersom allt är linjärt räknas kopplingskoefficienterna (SS-EN ISO 10211): omgivningarna får var för sig 1 K och
de andra 0, och flödet till varje omgivning och yta (etikett) summeras. Flödet vid godtyckliga temperaturer är sedan
Q = L · T. Etiketterna gör att flödet kan delas upp på byggdelarna (golvet, väggens insida, fönstret …).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spl


def kanter(brytpunkter, fina=(), h_max=0.2, tillvaxt=0.3, h_min=None):
    """Cellkanter (m) genom alla brytpunkter. fina: [(a, b, h)] zoner med cellstorleken h; utanför dem växer
    cellerna med tillvaxt gånger avståndet till zonen, högst h_max. Varje intervall mellan två brytpunkter delas i
    lika stora celler, så att materialgränserna alltid ligger på cellkanter."""
    bp = np.unique(np.round(np.asarray(brytpunkter, float), 9))

    def storlek(s):
        h = h_max
        for a, b, hf in fina:
            h = min(h, hf + tillvaxt * max(a - s, 0.0, s - b))
        return h

    e = [bp[0]]
    for a, b in zip(bp[:-1], bp[1:]):
        L = b - a
        if L < 1e-9:
            continue
        # cellstorleken i intervallet: den minsta som zonerna kräver i det (i änden närmast en fin zon)
        h = min(storlek(a), storlek(b), storlek(0.5 * (a + b)))
        if h_min:
            h = max(h, h_min)
        n = max(1, int(np.ceil(L / h - 1e-9)))
        if n > 4 and L > 4 * min(storlek(a), storlek(b)):
            # graderat: celler som växer från ändarna mot mitten
            ha, hb = storlek(a), storlek(b)
            s, ut = a, []
            while s < b - 1e-9:
                hs = min(storlek(s), ha + tillvaxt * (s - a), hb + tillvaxt * (b - s), h_max)
                ut.append(min(s + hs, b))
                s = ut[-1]
            if len(ut) > 1 and ut[-1] - ut[-2] < 0.4 * (ut[-2] - (ut[-3] if len(ut) > 2 else a)):
                ut.pop(-2)
            e.extend(ut)
        else:
            e.extend(a + L * np.arange(1, n + 1) / n)
    e = np.array(e)
    e[-1] = bp[-1]
    return e


@dataclass
class Omgivning:
    namn: str
    nr: int


@dataclass
class Modell:
    """Ett nät med material, omgivningar och etiketter. Koordinater i m."""
    kant: list                                   # cellkanter per axel
    material: list = field(default_factory=list)          # [(namn, λ per axel)]
    omgivningar: list = field(default_factory=list)       # [namn]
    etiketter: list = field(default_factory=list)         # [namn]

    def __post_init__(self):
        self.kant = [np.asarray(k, float) for k in self.kant]
        self.nd = len(self.kant)
        self.mitt = [0.5 * (k[1:] + k[:-1]) for k in self.kant]
        self.d = [np.diff(k) for k in self.kant]
        self.form = tuple(len(m) for m in self.mitt)
        self.mat = np.full(self.form, -1, np.int32)        # material, −1 = tom
        self.omg = np.full(self.form, -1, np.int32)        # omgivning för tomma celler, −1 = adiabatisk
        self.Rs = np.zeros(self.form)                      # ytmotstånd mot den tomma cellens omgivning
        self.etik = np.full(self.form, -1, np.int32)       # etikett för tomma celler
        self.rander = {}                                   # (axel, sida) -> (omgivning, R, etikett)
        self.kallor = np.zeros(self.form)                  # värmekällor i fasta celler [W] per enhet (för fall)

    # ------------------------------------------------------------------ definition
    def nytt_material(self, namn, lam):
        lam = np.broadcast_to(np.asarray(lam, float), (self.nd,)).copy()
        for i, (n, l) in enumerate(self.material):
            if n == namn:
                assert np.allclose(l, lam), namn
                return i
        self.material.append((namn, lam))
        return len(self.material) - 1

    def omgivning(self, namn):
        if namn not in self.omgivningar:
            self.omgivningar.append(namn)
        return self.omgivningar.index(namn)

    def etikett(self, namn):
        if namn not in self.etiketter:
            self.etiketter.append(namn)
        return self.etiketter.index(namn)

    def _urval(self, lo, hi):
        """Cellerna vars mittpunkt ligger i lådan [lo, hi] (som index-slices)."""
        sl = []
        for a in range(self.nd):
            m = self.mitt[a]
            i0 = np.searchsorted(m, lo[a], side="left")
            i1 = np.searchsorted(m, hi[a], side="right")
            sl.append(slice(i0, i1))
        return tuple(sl)

    def lada(self, namn, lam, lo, hi):
        """Fyll lådan med materialet (de senare lådorna skriver över de tidigare)."""
        i = self.nytt_material(namn, lam)
        s = self._urval(lo, hi)
        self.mat[s] = i
        self.omg[s] = -1
        self.etik[s] = -1
        return s

    def polygon(self, namn, lam, pkt):
        """2D: fyll cellerna vars mittpunkt ligger i polygonen."""
        from matplotlib.path import Path
        assert self.nd == 2
        i = self.nytt_material(namn, lam)
        X, Y = np.meshgrid(*self.mitt, indexing="ij")
        inne = Path(np.asarray(pkt)).contains_points(np.c_[X.ravel(), Y.ravel()]).reshape(self.form)
        self.mat[inne] = i
        self.omg[inne] = -1
        self.etik[inne] = -1
        return inne

    def tom(self, omgivning, lo, hi, Rs=0.0, etikett=None):
        """Gör lådan tom och till en omgivning (None = adiabatisk) med ytmotståndet Rs mot angränsande material."""
        s = self._urval(lo, hi)
        self.mat[s] = -1
        self.omg[s] = -1 if omgivning is None else self.omgivning(omgivning)
        self.Rs[s] = Rs
        self.etik[s] = -1 if omgivning is None else self.etikett(etikett or omgivning)
        return s

    def tom_mask(self, mask, omgivning, Rs=0.0, etikett=None):
        self.mat[mask] = -1
        self.omg[mask] = -1 if omgivning is None else self.omgivning(omgivning)
        self.Rs[mask] = Rs
        self.etik[mask] = -1 if omgivning is None else self.etikett(etikett or omgivning)

    def rand(self, axel, sida, omgivning, Rs=0.0, etikett=None):
        """Nätets ytterrand (sida 0 = låg, 1 = hög) mot en omgivning."""
        self.rander[(axel, sida)] = (self.omgivning(omgivning), Rs,
                                     self.etikett(etikett if etikett else omgivning))

    # ------------------------------------------------------------------ system
    def bygg(self):
        fast = self.mat >= 0
        N = int(fast.sum())
        idx = np.full(self.form, -1, np.int64)
        idx[fast] = np.arange(N)
        lam = np.zeros((self.nd,) + self.form)
        for i, (_, l) in enumerate(self.material):
            for a in range(self.nd):
                lam[a][self.mat == i] = l[a]
        rows, cols, vals = [], [], []
        diag = np.zeros(N)
        nomg, netik = len(self.omgivningar), len(self.etiketter)
        # randflöden: (cell, omgivning, etikett, G)
        rc, ro, re, rg = [], [], [], []
        for a in range(self.nd):
            # ytans area för celler längs axel a: produkten av de andra axlarnas storlekar
            A = np.ones(self.form)
            half = np.ones(self.form)
            for b in range(self.nd):
                shp = [1] * self.nd
                shp[b] = -1
                if b == a:
                    half = half * (self.d[b] / 2).reshape(shp)
                else:
                    A = A * self.d[b].reshape(shp)
            sa = [slice(None)] * self.nd
            sb = [slice(None)] * self.nd
            sa[a] = slice(0, -1)
            sb[a] = slice(1, None)
            sa, sb = tuple(sa), tuple(sb)
            fa, fb = fast[sa], fast[sb]
            ra = np.where(fa, half[sa] / np.where(fa, lam[a][sa], 1.0), 0.0)
            rb = np.where(fb, half[sb] / np.where(fb, lam[a][sb], 1.0), 0.0)
            Af = A[sa]
            # fast–fast
            m = fa & fb
            G = Af[m] / (ra[m] + rb[m])
            i, j = idx[sa][m], idx[sb][m]
            rows += [i, j]
            cols += [j, i]
            vals += [-G, -G]
            np.add.at(diag, i, G)
            np.add.at(diag, j, G)
            # fast–omgivning (åt båda hållen)
            for f_, g_, rf, sf, so in ((fa, fb, ra, sa, sb), (fb, fa, rb, sb, sa)):
                m = f_ & ~g_ & (self.omg[so] >= 0)
                if m.any():
                    G = Af[m] / (rf[m] + self.Rs[so][m])
                    c = idx[sf][m]
                    np.add.at(diag, c, G)
                    rc.append(c)
                    ro.append(self.omg[so][m])
                    re.append(self.etik[so][m])
                    rg.append(G)
            # ytterränder
            for sida in (0, 1):
                if (a, sida) not in self.rander:
                    continue
                o, R, e = self.rander[(a, sida)]
                s = [slice(None)] * self.nd
                s[a] = 0 if sida == 0 else -1
                s = tuple(s)
                m = fast[s]
                G = A[s][m] / (half[s][m] / lam[a][s][m] + R)
                c = idx[s][m]
                np.add.at(diag, c, G)
                rc.append(c)
                ro.append(np.full(c.shape, o))
                re.append(np.full(c.shape, e))
                rg.append(G)
        K = sp.csr_matrix((np.concatenate(vals + [diag]),
                           (np.concatenate(rows + [np.arange(N)]), np.concatenate(cols + [np.arange(N)]))),
                          shape=(N, N))
        self.N, self.idx, self.K = N, idx, K
        self.rc, self.ro = np.concatenate(rc), np.concatenate(ro)
        self.re, self.rg = np.concatenate(re), np.concatenate(rg)
        return self

    def los(self, T_omg, kalla=None, tol=1e-10):
        """Temperaturfältet för omgivningarnas temperaturer T_omg (lista eller dict namn -> °C) och värmekällor
        kalla (W per cell, i fältets form)."""
        T_omg = self._tvektor(T_omg)
        b = np.zeros(self.N)
        np.add.at(b, self.rc, self.rg * T_omg[self.ro])
        if kalla is not None:
            b += kalla[self.mat >= 0]
        x = self._losare()(b)
        T = np.full(self.form, np.nan)
        T[self.mat >= 0] = x
        return T

    def _tvektor(self, T_omg):
        if isinstance(T_omg, dict):
            v = np.zeros(len(self.omgivningar))
            for k, t in T_omg.items():
                if k in self.omgivningar:
                    v[self.omgivningar.index(k)] = t
            return v
        return np.asarray(T_omg, float)

    def _losare(self):
        if getattr(self, "_lu", None) is None:
            if self.nd == 2 or self.N < 150_000:
                lu = spl.splu(self.K.tocsc())
                self._lu = lu.solve
            else:
                import pyamg
                ml = pyamg.smoothed_aggregation_solver(self.K, symmetry="symmetric", max_coarse=400)

                def los(b, ml=ml):
                    res = []
                    x = ml.solve(b, tol=1e-11, accel="cg", maxiter=400, residuals=res)
                    assert res[-1] <= 1e-9 * max(res[0], 1e-30), f"CG konvergerade inte: {res[-1] / res[0]:.1e}"
                    return x
                self._lu = los
        return self._lu

    def flode_matris(self, T, T_omg):
        """Flöde till varje (omgivning, etikett) för fältet T: array [nomg, netik]."""
        T_omg = self._tvektor(T_omg)
        t = T[self.mat >= 0][self.rc]
        q = self.rg * (t - T_omg[self.ro])
        F = np.zeros((len(self.omgivningar), len(self.etiketter)))
        np.add.at(F, (self.ro, self.re), q)
        return F

    def koppling(self):
        """Kopplingskoefficienterna: L[k, e, j] = flödet till omgivning k vid etikett e när omgivning j har 1 K
        och de andra 0 K (W/K, i 2D W/(m·K)); för k ≠ j är det kopplingskoefficienten L_kj i SS-EN ISO 10211.
        Summan över k och e är noll (energibalans)."""
        n = len(self.omgivningar)
        L = np.zeros((n, len(self.etiketter), n))
        self.falt = []
        for j in range(n):
            T = self.los(np.eye(n)[j])
            self.falt.append(T)
            L[:, :, j] = self.flode_matris(T, np.eye(n)[j])
        return L


def kopplingar(L, omg):
    """Kopplingskoefficienterna mellan omgivningarna (summerat över etiketterna), L_kj, som dict."""
    M = L.sum(axis=1)
    return {(omg[k], omg[j]): M[k, j] for k in range(len(omg)) for j in range(len(omg)) if k != j}
