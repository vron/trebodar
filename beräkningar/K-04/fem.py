"""Linjär 3D-ramanalys: balkelement (Timoshenko, 12 frihetsgrader), dragstänger som bara tar drag (stålbanden),
stela förskjutningar mellan knutpunkternas noder (huvudnod och följare, med följarens rotationer fria eller låsta),
bindningar mellan nodernas förskjutningar i en riktning (med straff), fasta upplag och utbredda laster per element.
Enheter N och mm.

Följarnas förskjutningar uttrycks i huvudnodens (u_f = u_h + θ_h × r), så att excentriciteterna i knutpunkterna
ingår utan styva element. En följare är en led för böjning: rotationerna vinkelrätt mot följarens del är fria,
medan vridningen kring delens egen axel följer huvudnoden (delen kan inte snurra fritt i leden); en svag
rotationsfjäder mot huvudnoden (K_LED) ger de fria rotationerna en definierad styvhet. Upplagen är fasta (syllarna
står på och är förankrade i betongen och kan inte rulla).

Dragstängerna: styvheten med alla stänger fakturiseras en gång, och stänger som trycks tas bort med Woodburys
formel (rang = antalet borttagna), tills inga aktiva stänger trycks och inga borttagna förlängs.

Skjuvskivorna (skivverkan): en generaliserad stång per skiva, vars töjning är skivans skjuvvinkel γ ur hörnnodernas
förskjutningar (termer nod och vektor), med styvheten k (kraften Q = k γ, skjuvkraften Q / h). En skiva är elastisk
upp till sin bärförmåga Q_max och plastisk där: styvheten tas bort som för en slak stång och kraften hålls vid
±Q_max som en last; en plastisk skiva som avlastas blir elastisk igen.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spl

K_LED = 1.0e5            # svag rotationsfjäder i lederna [Nmm/rad]
K_JORD = 1.0e2           # försumbar rotationsfjäder mot marken i alla noder, mot vridning utan styvhet [Nmm/rad]


@dataclass
class Modell:
    x: np.ndarray                                   # nodernas lägen (n, 3) [mm]
    # balkelement: nod i, nod j, lokal z-axel (tvärsnittets höjdriktning), E, G, A, Iy, Iz, J, Avy, Avz
    bi: np.ndarray = field(default_factory=lambda: np.zeros(0, int))
    bj: np.ndarray = field(default_factory=lambda: np.zeros(0, int))
    bz: np.ndarray = field(default_factory=lambda: np.zeros((0, 3)))
    bsek: np.ndarray = field(default_factory=lambda: np.zeros((0, 9)))  # E, G, A, Iy, Iz, J, Avy, Avz, (reserv)
    led_i: np.ndarray = field(default_factory=lambda: np.zeros(0, bool))  # leder (böjning fri) i elementens ändar
    led_j: np.ndarray = field(default_factory=lambda: np.zeros(0, bool))
    # dragstänger: nod i, nod j, EA
    ti: np.ndarray = field(default_factory=lambda: np.zeros(0, int))
    tj: np.ndarray = field(default_factory=lambda: np.zeros(0, int))
    tEA: np.ndarray = field(default_factory=lambda: np.zeros(0))
    # knutpunkter: följare, huvudnod, låsta rotationer, följarens dels axel (vridningen följer huvudnoden)
    foljare: np.ndarray = field(default_factory=lambda: np.zeros(0, int))
    huvud: np.ndarray = field(default_factory=lambda: np.zeros(0, int))
    last_rot: np.ndarray = field(default_factory=lambda: np.zeros(0, bool))
    axel: np.ndarray = field(default_factory=lambda: np.zeros((0, 3)))
    upplag: np.ndarray = field(default_factory=lambda: np.zeros(0, int))     # fasta noder
    # bindningar (straff): g_c = Σ vikt · (u_nod · e_c) = 0, med termerna (bindning, nod, vikt), riktningen e_c och
    # styvheten k_c [N/mm] per bindning; kraften i bindningen är k_c · g_c
    b_c: np.ndarray = field(default_factory=lambda: np.zeros(0, int))
    b_nod: np.ndarray = field(default_factory=lambda: np.zeros(0, int))
    b_vikt: np.ndarray = field(default_factory=lambda: np.zeros(0))
    b_e: np.ndarray = field(default_factory=lambda: np.zeros((0, 3)))
    b_k: np.ndarray = field(default_factory=lambda: np.zeros(0))
    # skjuvskivor: termerna (skiva, nod, vektor) för skjuvvinkeln γ = Σ vektor · u_nod och styvheten k [N]
    s_c: np.ndarray = field(default_factory=lambda: np.zeros(0, int))
    s_nod: np.ndarray = field(default_factory=lambda: np.zeros(0, int))
    s_v: np.ndarray = field(default_factory=lambda: np.zeros((0, 3)))
    s_k: np.ndarray = field(default_factory=lambda: np.zeros(0))


def _lokala_axlar(dx: np.ndarray, z: np.ndarray) -> np.ndarray:
    """Rotationsmatriser (m, 3, 3): rader lokala x, y, z i globala koordinater (z: tvärsnittets höjdriktning,
    vinkelrät mot elementet; nästan parallell med elementet: en annan riktning vinkelrät mot det)."""
    L = np.linalg.norm(dx, axis=1)
    ex = dx / L[:, None]
    ez = z - (np.einsum("ij,ij->i", z, ex))[:, None] * ex
    n = np.linalg.norm(ez, axis=1)
    alt = np.cross(ex, np.where(np.abs(ex[:, 2:3]) < 0.9, np.array([[0.0, 0.0, 1.0]]), np.array([[1.0, 0.0, 0.0]])))
    ez = np.where(n[:, None] > 0.2, ez, alt)
    ez /= np.linalg.norm(ez, axis=1)[:, None]
    ey = np.cross(ez, ex)
    return np.stack([ex, ey, ez], axis=1)


def balkstyvhet(L: np.ndarray, s: np.ndarray) -> np.ndarray:
    """Lokala styvhetsmatriser (m, 12, 12) för Timoshenkobalkar. Frihetsgrader per nod: u, v, w, θx, θy, θz."""
    E, G, A, Iy, Iz, J, Avy, Avz = (s[:, k] for k in range(8))
    m = len(L)
    k = np.zeros((m, 12, 12))
    ea = E * A / L
    gj = G * J / L
    # böjning i x–y-planet (v, θz): skjuvdeformation med Avy
    py = 12 * E * Iz / (G * Avy * L ** 2)
    # böjning i x–z-planet (w, θy): skjuvdeformation med Avz
    pz = 12 * E * Iy / (G * Avz * L ** 2)
    k[:, 0, 0] = k[:, 6, 6] = ea
    k[:, 0, 6] = k[:, 6, 0] = -ea
    k[:, 3, 3] = k[:, 9, 9] = gj
    k[:, 3, 9] = k[:, 9, 3] = -gj
    a = 12 * E * Iz / (L ** 3 * (1 + py))
    b = 6 * E * Iz / (L ** 2 * (1 + py))
    c = (4 + py) * E * Iz / (L * (1 + py))
    d = (2 - py) * E * Iz / (L * (1 + py))
    for (i, j, v) in ((1, 1, a), (7, 7, a), (1, 7, -a), (1, 5, b), (1, 11, b), (5, 7, -b), (7, 11, -b),
                      (5, 5, c), (11, 11, c), (5, 11, d)):
        k[:, i, j] = v
        k[:, j, i] = v
    a = 12 * E * Iy / (L ** 3 * (1 + pz))
    b = 6 * E * Iy / (L ** 2 * (1 + pz))
    c = (4 + pz) * E * Iy / (L * (1 + pz))
    d = (2 - pz) * E * Iy / (L * (1 + pz))
    for (i, j, v) in ((2, 2, a), (8, 8, a), (2, 8, -a), (2, 4, -b), (2, 10, -b), (4, 8, b), (8, 10, b),
                      (4, 4, c), (10, 10, c), (4, 10, d)):
        k[:, i, j] = v
        k[:, j, i] = v
    return k


def leder(k: np.ndarray, f: np.ndarray, led_i: np.ndarray, led_j: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Styvheterna och de fasta ändkrafterna (lokala) med leder: böjrotationerna (θy, θz) i elementens ändar
    kondenseras bort (statisk kondensering), så att momenten där blir noll."""
    k, f = k.copy(), f.copy()
    for li, lj in ((True, False), (False, True), (True, True)):
        e = np.flatnonzero((led_i == li) & (led_j == lj))
        if not len(e):
            continue
        r = ([4, 5] if li else []) + ([10, 11] if lj else [])
        a = [i for i in range(12) if i not in r]
        krr = k[np.ix_(e, r, r)]
        kar = k[np.ix_(e, a, r)]
        inv = np.linalg.inv(krr)
        kc = k[np.ix_(e, a, a)] - kar @ inv @ np.transpose(kar, (0, 2, 1))
        fc = f[np.ix_(e, a)] - np.einsum("eij,ej->ei", kar @ inv, f[np.ix_(e, r)])
        k[np.ix_(e, a, a)] = kc
        k[np.ix_(e, r, range(12))] = 0.0
        k[np.ix_(e, range(12), r)] = 0.0
        f[np.ix_(e, a)] = fc
        f[np.ix_(e, r)] = 0.0
    return k, f


def fasta_andkrafter(L: np.ndarray, q: np.ndarray) -> np.ndarray:
    """Ändkrafter (m, 12) i lokala axlar för fast inspända ändar och jämnt utbredd last q (m, 3) i lokala axlar
    [N/mm]; laster på noderna blir minus dessa."""
    f = np.zeros((len(L), 12))
    qx, qy, qz = q[:, 0], q[:, 1], q[:, 2]
    f[:, 0] = f[:, 6] = -qx * L / 2
    f[:, 1] = f[:, 7] = -qy * L / 2
    f[:, 2] = f[:, 8] = -qz * L / 2
    f[:, 5] = -qy * L ** 2 / 12
    f[:, 11] = qy * L ** 2 / 12
    f[:, 4] = qz * L ** 2 / 12
    f[:, 10] = -qz * L ** 2 / 12
    return f


class Analys:
    """Modellens styvhet med alla dragstänger, fakturiserad, och lösningar för lastfall och kombinationer."""

    def __init__(self, m: Modell):
        self.m = m
        n = len(m.x)
        self.n = n
        # elementens geometri
        dx = m.x[m.bj] - m.x[m.bi]
        self.L = np.linalg.norm(dx, axis=1)
        self.Lam = _lokala_axlar(dx, m.bz)
        kl = balkstyvhet(self.L, m.bsek)
        self.led_i = m.led_i if len(m.led_i) else np.zeros(len(self.L), bool)
        self.led_j = m.led_j if len(m.led_j) else np.zeros(len(self.L), bool)
        kl, _ = leder(kl, np.zeros((len(self.L), 12)), self.led_i, self.led_j)
        T = np.zeros((len(self.L), 12, 12))
        for b in range(4):
            T[:, 3 * b:3 * b + 3, 3 * b:3 * b + 3] = self.Lam
        self.T = T
        self.kl = kl
        self.kl_bas = balkstyvhet(self.L, m.bsek)
        kg = np.einsum("eji,ejk,ekl->eil", T, kl, T)
        dof = np.concatenate([6 * m.bi[:, None] + np.arange(6), 6 * m.bj[:, None] + np.arange(6)], axis=1)
        self.dof = dof
        rader = np.repeat(dof, 12, axis=1).ravel()
        kol = np.tile(dof, (1, 12)).ravel()
        K = sp.coo_matrix((kg.ravel(), (rader, kol)), shape=(6 * n, 6 * n)).tocsr()
        # svaga rotationsfjädrar i lederna
        led = ~m.last_rot
        fs, hs = m.foljare[led], m.huvud[led]
        r_, c_, v_ = [], [], []
        for a in range(3):
            for p, q, s in ((fs, fs, 1.0), (hs, hs, 1.0), (fs, hs, -1.0), (hs, fs, -1.0)):
                r_.append(6 * p + 3 + a)
                c_.append(6 * q + 3 + a)
                v_.append(np.full(len(p), s * K_LED))
        if r_:
            K = K + sp.coo_matrix((np.concatenate(v_), (np.concatenate(r_), np.concatenate(c_))),
                                  shape=(6 * n, 6 * n)).tocsr()
        # bindningarna
        self.G = sp.coo_matrix((np.concatenate([m.b_vikt * m.b_e[m.b_c, a] for a in range(3)]),
                                (np.tile(m.b_c, 3), np.concatenate([6 * m.b_nod + a for a in range(3)]))),
                               shape=(len(m.b_k), 6 * n)).tocsr()
        if len(m.b_k):
            K = K + self.G.T @ sp.diags(m.b_k) @ self.G
        # transformation till de oberoende frihetsgraderna: följarnas förskjutningar ur huvudnodernas
        self.Tr = self._transformation()
        # dragstängerna (i de oberoende frihetsgraderna)
        e = m.x[m.tj] - m.x[m.ti]
        self.tL = np.linalg.norm(e, axis=1)
        self.te = e / self.tL[:, None] if len(e) else e
        Bf = sp.lil_matrix((6 * n, len(m.ti)))
        for s, (i, j) in enumerate(zip(m.ti, m.tj)):
            for a in range(3):
                Bf[6 * j + a, s] += self.te[s, a]
                Bf[6 * i + a, s] -= self.te[s, a]
        self.Bf = Bf.tocsr()
        self.kt = m.tEA / self.tL if len(m.ti) else np.zeros(0)
        # skjuvskivorna som generaliserade stänger efter dragstängerna
        self.ns_band = len(self.kt)
        nsk = len(m.s_k)
        Bs = sp.coo_matrix((m.s_v.ravel(), (np.repeat(6 * m.s_nod, 3) + np.tile(np.arange(3), len(m.s_nod)),
                                            np.repeat(m.s_c, 3))), shape=(6 * n, nsk)).tocsr()
        self.Bs_full = Bs
        self.Bf = sp.hstack([self.Bf, Bs]).tocsr()
        self.kt = np.concatenate([self.kt, m.s_k])
        Kr = self.Tr.T @ K @ self.Tr
        rot = np.zeros(self.n_red, bool)
        rot[self.idx[:, 3:][self.idx[:, 3:] >= 0]] = True
        Kr = Kr + sp.diags(np.where(rot, K_JORD, 0.0))
        B = self.Tr.T @ self.Bf
        Kr = Kr + B @ sp.diags(self.kt) @ B.T
        # upplagen
        fri = np.ones(Kr.shape[0], bool)
        fri[self._upplagsdof()] = False
        self.fri = np.flatnonzero(fri)
        self.Kfull = K
        self.K0 = Kr
        self.Kff = Kr[self.fri][:, self.fri].tocsc()
        self.lu = spl.splu(self.Kff)
        self.B = B[self.fri]
        self.Z = self.lu.solve(self.B.toarray()) if self.B.shape[1] else np.zeros((len(self.fri), 0))
        self.BZ = self.B.T @ self.Z

    def _transformation(self) -> sp.csr_matrix:
        m, n = self.m, self.n
        ar_foljare = np.zeros(n, bool)
        ar_foljare[m.foljare] = True
        # oberoende frihetsgrader: alla för vanliga noder; rotationerna för följare med fria rotationer
        idx = -np.ones((n, 6), int)
        k = 0
        for i in range(n):
            if not ar_foljare[i]:
                idx[i] = np.arange(k, k + 6)
                k += 6
        # följare med leder: två fria rotationer vinkelrätt mot delens axel
        bas = {}
        for f, last, e in zip(m.foljare, m.last_rot, m.axel):
            if last:
                continue
            e = e / np.linalg.norm(e)
            t = np.array([1.0, 0.0, 0.0]) if abs(e[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
            e1 = np.cross(e, t)
            e1 /= np.linalg.norm(e1)
            bas[f] = (e, e1, np.cross(e, e1))
            idx[f, 3:5] = (k, k + 1)
            k += 2
        self.idx = idx
        rader, kol, v = [], [], []
        for i in range(n):
            if not ar_foljare[i]:
                rader += list(range(6 * i, 6 * i + 6))
                kol += list(idx[i])
                v += [1.0] * 6
        for f, h, last in zip(m.foljare, m.huvud, m.last_rot):
            r = m.x[f] - m.x[h]
            # u_f = u_h − skew(r) θ_h
            S = np.array([[0, -r[2], r[1]], [r[2], 0, -r[0]], [-r[1], r[0], 0]])
            for a in range(3):
                rader.append(6 * f + a)
                kol.append(idx[h, a])
                v.append(1.0)
                for b in range(3):
                    if S[a, b] != 0:
                        rader.append(6 * f + a)
                        kol.append(idx[h, 3 + b])
                        v.append(-S[a, b])
            if last:
                for a in range(3):
                    rader.append(6 * f + 3 + a)
                    kol.append(idx[h, 3 + a])
                    v.append(1.0)
            else:
                e, e1, e2 = bas[f]
                for a in range(3):
                    for b in range(3):
                        if abs(e[a] * e[b]) > 1e-12:
                            rader.append(6 * f + 3 + a)
                            kol.append(idx[h, 3 + b])
                            v.append(e[a] * e[b])
                    rader += [6 * f + 3 + a, 6 * f + 3 + a]
                    kol += [idx[f, 3], idx[f, 4]]
                    v += [e1[a], e2[a]]
        self.n_red = k
        return sp.coo_matrix((v, (rader, kol)), shape=(6 * n, k)).tocsr()

    def _upplagsdof(self) -> np.ndarray:
        ut = []
        for i in self.m.upplag:
            assert self.idx[i, 0] >= 0, "upplagen ska vara huvudnoder"
            ut += list(self.idx[i, :6])
        return np.array(ut, int)

    # ---------------------------------------------------------------- laster
    def nodlaster(self, q_glob: np.ndarray, P: np.ndarray | None = None) -> np.ndarray:
        """Lastvektorn (6n) ur utbredda laster per balkelement (m, 3) globalt [N/mm] och nodlaster P (n, 6)."""
        ql = np.einsum("eij,ej->ei", self.Lam, q_glob)
        _, fe = leder(self.kl_bas, fasta_andkrafter(self.L, ql), self.led_i, self.led_j)
        fe = -fe
        fg = np.einsum("eji,ej->ei", self.T, fe)
        f = np.zeros(6 * self.n)
        np.add.at(f, self.dof.ravel(), fg.ravel())
        if P is not None:
            f += P.ravel()
        return f

    def los(self, f: np.ndarray, Q_max: np.ndarray | None = None, max_iter: int = 200
            ) -> tuple[np.ndarray, np.ndarray, int]:
        """Förskjutningarna (6n) för lastvektorn f med dragstänger som bara tar drag och skjuvskivor som är plastiska
        vid Q_max (per skiva; None: elastiska). Ger u, de aktiva stängerna (dragstängerna, sedan skivorna: elastiska)
        och antalet iterationer. Skivornas krafter: skivkrafter(u)."""
        fr = (self.Tr.T @ f)[self.fri]
        u0 = self.lu.solve(fr)
        nb = self.ns_band
        ns = len(self.kt)
        aktiv = np.ones(ns, bool)
        tecken = np.zeros(ns - nb)                  # skivornas plastiska kraft: +1, −1 eller 0 (elastisk)
        qm = np.full(ns - nb, np.inf) if Q_max is None else np.asarray(Q_max, float)
        u = u0
        for it in range(1, max_iter + 1):
            bort = np.flatnonzero(~aktiv)
            plast = np.flatnonzero(tecken != 0)
            ub = u0 + self.Z[:, nb + plast] @ (-tecken[plast] * qm[plast]) if len(plast) else u0
            if len(bort):
                A = np.diag(1.0 / self.kt[bort]) - self.BZ[np.ix_(bort, bort)]
                u = ub + self.Z[:, bort] @ np.linalg.solve(A, self.B[:, bort].T @ ub)
            else:
                u = ub
            d = self.B.T @ u                         # förlängningarna och skivornas skjuvvinkel
            ny = d[:nb] > 0.0
            q = self.kt[nb:] * d[nb:]                # skivornas kraft om de vore elastiska
            nt = np.where(np.abs(q) > qm * (1 + 1e-9), np.sign(q), 0.0)
            # en plastisk skiva förblir plastisk så länge den inte avlastas
            nt = np.where((tecken != 0) & (tecken * q >= qm * (1 - 1e-9)), tecken, nt)
            if np.array_equal(ny, aktiv[:nb]) and np.array_equal(nt, tecken):
                break
            aktiv = np.concatenate([ny, nt == 0])
            tecken = nt
        self._sk = (tecken.copy(), qm.copy())
        ur = np.zeros(self.n_red)
        ur[self.fri] = u
        return self.Tr @ ur, aktiv, it

    def skivkrafter(self, u: np.ndarray) -> np.ndarray:
        """Skjuvskivornas kraft Q (k γ elastiskt, ±Q_max plastiskt) i senaste lösningen u."""
        if not len(self.kt) - self.ns_band:
            return np.zeros(0)
        tecken, qm = self._sk
        q = self.kt[self.ns_band:] * (self.Bs_full.T @ u)
        return np.where(tecken != 0, tecken * np.where(np.isfinite(qm), qm, 0.0), q)

    # ---------------------------------------------------------------- resultat
    def balkkrafter(self, u: np.ndarray, q_glob: np.ndarray) -> np.ndarray:
        """Ändkrafter (m, 12) i lokala axlar: N, Vy, Vz, T, My, Mz i nod i och j (krafterna som verkar på elementet)."""
        ue = u[self.dof]
        ul = np.einsum("eij,ej->ei", self.T, ue)
        ql = np.einsum("eij,ej->ei", self.Lam, q_glob)
        _, fc = leder(self.kl_bas, fasta_andkrafter(self.L, ql), self.led_i, self.led_j)
        return np.einsum("eij,ej->ei", self.kl, ul) + fc

    def stangkrafter(self, u: np.ndarray, aktiv: np.ndarray) -> np.ndarray:
        """Normalkraften i dragstängerna (drag positivt; noll för borttagna)."""
        nb = self.ns_band
        d = self.Bf[:, :nb].T @ u
        return np.where(aktiv[:nb], self.kt[:nb] * d, 0.0)

    def bindningskrafter(self, u: np.ndarray) -> np.ndarray:
        """Kraften i bindningarna: den som verkar på noden med vikten 1, mot riktningen e_c (positiv: noden hålls
        tillbaka åt −e_c)."""
        return self.m.b_k * (self.G @ u)

    def reaktioner(self, u: np.ndarray, f: np.ndarray, aktiv: np.ndarray) -> np.ndarray:
        """Upplagsreaktionerna (antal upplag, 3): krafterna från upplaget på stommen [N]."""
        nb = self.ns_band
        r = self.Kfull @ u + self.Bf[:, :nb] @ (np.where(aktiv[:nb], self.kt[:nb], 0.0) * (self.Bf[:, :nb].T @ u)) - f
        if len(self.kt) > nb:
            r = r + self.Bs_full @ self.skivkrafter(u)
        # krafterna i följarna förs över till huvudnoderna (upplagen är huvudnoder)
        rr = self.Tr.T @ r
        return np.array([rr[self.idx[i, :6]] for i in self.m.upplag])
