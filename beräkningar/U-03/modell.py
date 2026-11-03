"""U-03: luftflöde, värme och fukt i takets luftspalt timme för timme, som nätverk (geometri.py).

luftflöde  tryck i noderna (Newton) med vindtryck vid takfötter och gavelöppningar och termisk stigkraft i takfallen;
           tryckfall: friktion (laminär f·Re efter kanalens form, turbulent Blasius, störst av dem) och engångsförluster
värme      kvasistationär per cell: plåt (sol, långvågsstrålning mot himlen, konvektion ute), råspont, luft i spalten,
           strålning över spalten, träfiberskiva med värmeflöde inifrån; luften blandas i noderna efter flödena
fukt       transient: råspontens yt- och kärnskikt och träfiberskivan med isoleringens överdel som fuktbuffertar,
           ånga i spaltens luft (advektion, blandning i noderna), diffusion inifrån genom gips, fuktadaptiv ångbroms
           och isolering
mögel      VTT-modellen (Hukka & Viitanen 1999) på råspontens undersida och på träfiberskivan
"""
import gzip
import io
import math

import numpy as np
import scipy.sparse as sp

SIGMA, G, RV, RA, CP = 5.67e-8, 9.81, 461.5, 287.05, 1006.0
DELTA_A = 2.0e-10                     # ångpermeabilitet i luft [kg/(m s Pa)]
RHO = 1.25                            # luftens densitet i tryckfallen [kg/m³]


def psat(T):
    T = np.asarray(T, float)
    return np.where(T >= 0, 610.5 * np.exp(17.269 * T / (237.3 + T)), 610.5 * np.exp(21.875 * T / (265.5 + T)))


class Sorption:
    def __init__(self, phi, u):
        self.phi, self.u = np.array(phi, float), np.array(u, float)
        self.k = np.diff(self.u) / np.diff(self.phi)

    def u_av(self, phi):
        return np.interp(np.clip(phi, 0, 1), self.phi, self.u)

    def phi_av(self, u):
        return np.interp(u, self.u, self.phi)                    # u över kurvans slut ger φ = 1 (fritt vatten)

    def lutning(self, phi):
        i = np.clip(np.searchsorted(self.phi, np.clip(phi, 0, 0.999), side="right") - 1, 0, len(self.k) - 1)
        return self.k[i]


# ------------------------------------------------------------------ klimat
def klimat(I, katalog="."):
    C = I["klimat"]
    with gzip.open(f"{katalog}/{C['fil']}", "rt") as f:
        rader = [r for r in f if not r.startswith("#")]
    hdr = rader[0].strip().split(",")
    d = np.genfromtxt(io.StringIO("".join(rader[1:])), delimiter=",", dtype=None, encoding=None, names=hdr)
    t = np.array(d["tid"], dtype="datetime64[h]")
    T, RH, c = d["T"].astype(float), d["RF"] / 100.0, d["moln"] / 100.0
    e = RH * psat(T)
    eps_clr = 1.24 * (e / 100 / (T + 273.15)) ** (1 / 7)                 # Brutsaert
    eps_sky = (1 - 0.84 * c) * eps_clr + 0.84 * c                        # moln (Unsworth & Monteith)
    # solens läge mitt i timmen före (Open-Meteo), NOAA:s förenklade formler
    doy = (t - t.astype("datetime64[Y]")).astype(int) / 24.0
    hr = (t - t.astype("datetime64[D]")).astype(int) - 0.5
    gam = 2 * math.pi / 365 * (doy + (hr - 12) / 24)
    eqt = 229.18 * (0.000075 + 0.001868 * np.cos(gam) - 0.032077 * np.sin(gam) - 0.014615 * np.cos(2 * gam) - 0.040849 * np.sin(2 * gam))
    dec = (0.006918 - 0.399912 * np.cos(gam) + 0.070257 * np.sin(gam) - 0.006758 * np.cos(2 * gam) + 0.000907 * np.sin(2 * gam)
           - 0.002697 * np.cos(3 * gam) + 0.00148 * np.sin(3 * gam))
    ha = np.radians((hr * 60 + eqt + 4 * C["lon"]) / 4 - 180)
    la = math.radians(C["lat"])
    cz = np.sin(la) * np.sin(dec) + np.cos(la) * np.cos(dec) * np.cos(ha)
    zen = np.arccos(np.clip(cz, -1, 1))
    az = (np.degrees(np.arctan2(np.sin(ha), np.cos(ha) * np.sin(la) - np.tan(dec) * np.cos(la))) + 180) % 360
    return dict(t=t, T=T, RH=RH, e=e, U=d["U10"].astype(float), WD=d["vindriktning"].astype(float), c=c,
                Lsky=eps_sky * SIGMA * (T + 273.15) ** 4, GHI=d["GHI"].astype(float), DNI=d["DNI"].astype(float),
                DHI=d["DHI"].astype(float), P=d["p"] * 100.0, zen=zen, az=az)


def instralning(K, lutning, azim, rho_g=0.2):
    """Solinstrålning [W/m²] mot ett plan med lutningen och normalens azimut [°] (isotrop himmel)."""
    b = math.radians(lutning)
    cosi = np.cos(K["zen"]) * math.cos(b) + np.sin(K["zen"]) * math.sin(b) * np.cos(np.radians(K["az"] - azim))
    I = K["DNI"] * np.clip(cosi, 0, None) + K["DHI"] * (1 + math.cos(b)) / 2 + K["GHI"] * rho_g * (1 - math.cos(b)) / 2
    return np.where(K["zen"] < math.radians(90), I, 0.0)


# ------------------------------------------------------------------ vindtryck
def vinkel(wd, az):
    """Vinkeln [0, 180]° mellan vindens riktning (varifrån) och fasadens normal."""
    return np.abs(((wd - az + 180) % 360) - 180)


def cp_sc(theta):
    """Swami & Chandra (1988), låg byggnad, kvadratisk plan: Cp/Cp(0) mot vinkeln θ [°]."""
    t = np.radians(theta)
    return np.log(1.248 - 0.703 * np.sin(t / 2) - 1.175 * np.sin(t) ** 2 + 0.769 * np.cos(t / 2) + 0.717 * np.cos(t / 2) ** 2)


def cp(I, wd, az, typ):
    """Cp vid en takfot (typ 0) eller gavelöppning (typ 2) vars fasad vettar mot az."""
    V = I["vind"]
    cp0 = (V["a"] + V["c"]) / (cp_sc(0.0) - cp_sc(180.0))
    phi = vinkel(wd, az)
    if typ == 2:
        return cp0 * cp_sc(phi)
    m = cp0 * (cp_sc(phi) + cp_sc(180 - phi)) / 2
    p = np.minimum(phi, 180 - phi)
    d = np.sign(90 - phi) * (V["a"] * np.cos(np.radians(V["b"] * p)) + V["c"])
    return m + d / 2


# ------------------------------------------------------------------ nätverket: konstanter
def f_re(b, h):
    """Laminär f·Re för en rektangulär kanal (Shah & London)."""
    a = np.minimum(b, h) / np.maximum(b, h)
    return 96 * (1 - 1.3553 * a + 1.9467 * a ** 2 - 1.7012 * a ** 3 + 0.9564 * a ** 4 - 0.2537 * a ** 5)


class GlesLDL:
    """LDLᵀ för många symmetriska positivt definita matriser med samma glesa mönster (nätets Jacobian, en per
    timme): elimineringsordningen (minsta grad på nätets graf) och fyllnaden bestäms en gång, och faktoriseringen
    och lösningen räknas för alla timmar på en gång. Nätet är nästan ett träd, så det blir lite arbete."""

    def __init__(self, n, kanter):
        """n noder; kanter: nodpar (p, q), p ≠ q, som matriserna kan ha element i utanför diagonalen."""
        nb = [set() for _ in range(n)]
        for p, q in kanter:
            nb[p].add(q); nb[q].add(p)
        kvar, ordning, senare = set(range(n)), [], []
        while kvar:
            k = min(kvar, key=lambda i: (len(nb[i] & kvar), i))
            g = sorted(nb[k] & kvar - {k})
            for a in g:                                  # fyllnad: grannarna blir grannar till varandra
                nb[a].update(x for x in g if x != a)
            ordning.append(k); senare.append(g); kvar.remove(k)
        self.par = {}                                    # nodpar (p < q) -> kolumn bland elementen utanför diagonalen

        def kol(i, j):
            return self.par.setdefault((min(i, j), max(i, j)), len(self.par))
        for p, q in kanter:
            kol(p, q)
        self.steg = []
        for k, g in zip(ordning, senare):
            ab = [(a, b) for a in range(len(g)) for b in range(a + 1, len(g))]
            self.steg.append((k, np.array(g, int), np.array([kol(i, k) for i in g], int),
                              np.array([a for a, _ in ab], int), np.array([b for _, b in ab], int),
                              np.array([kol(g[a], g[b]) for a, b in ab], int)))
        self.n, self.m = n, len(self.par)

    def los(self, D, V, F):
        """x med A x = F per rad: A:s diagonal D (nh, n) och element utanför diagonalen V (nh, m, kolumner enligt
        par). D och V skrivs över."""
        d = np.empty_like(D)
        for k, g, ik, a, b, ij in self.steg:
            dk = D[:, k]
            d[:, k] = dk
            if len(g):
                W = V[:, ik]
                L = W / dk[:, None]
                D[:, g] -= W * L
                if len(ij):
                    V[:, ij] -= W[:, a] * L[:, b]
                V[:, ik] = L
        y = F.copy()
        for k, g, ik, *_ in self.steg:
            if len(g):
                y[:, g] -= V[:, ik] * y[:, k:k + 1]
        x = y / d
        for k, g, ik, *_ in reversed(self.steg):
            if len(g):
                x[:, k] -= (V[:, ik] * x[:, g]).sum(axis=1)
        return x


class Natverk:
    def __init__(self, I, N):
        g, S = N["gren"], I["stromning"]
        self.N, self.I = N, I
        self.n, self.nb = len(N["noder"]), len(g["a"])
        self.a, self.b, self.typ = g["a"], g["b"], g["typ"]
        self.ain, self.bin = self.a >= 0, self.b >= 0
        h = N["h"]
        A, L, Dh = g["A"], g["L"], g["Dh"]
        k = S["k_frik"]
        self.R_lam = f_re(g["bredd"], g["hojd"]) * k * S["my"] * L / (2 * Dh ** 2 * A)
        self.C_t = 0.316 * k * (L / Dh) * (RHO / 2) * (RHO * Dh / S["my"]) ** -0.25 * A ** -1.75
        self.R2 = g["zeta"] * RHO / (2 * A ** 2)
        self.dz = g["dz"]
        # incidens (nettoutflöde) och Jacobianens mönster
        n, nb = self.n, self.nb
        rad, kol, val = [], [], []
        for j in range(nb):
            if self.ain[j]:
                rad.append(self.a[j]); kol.append(j); val.append(1.0)
            if self.bin[j]:
                rad.append(self.b[j]); kol.append(j); val.append(-1.0)
        self.Ainc = sp.csr_matrix((val, (rad, kol)), shape=(n, nb))
        r, c_, v = [], [], []
        for j in range(nb):
            ends = [x for x, ok in ((self.a[j], self.ain[j]), (self.b[j], self.bin[j])) if ok]
            for p in ends:
                for q in ends:
                    r.append(j); c_.append(p * n + q); v.append(1.0 if p == q else -1.0)
        self.SJ = sp.csr_matrix((v, (r, c_)), shape=(nb, n * n))
        # samma Jacobian glest: diagonalen och elementen mellan inre noder ur grenarnas ledningsförmåga
        inre = [j for j in range(nb) if self.ain[j] and self.bin[j] and self.a[j] != self.b[j]]
        self.ldl = GlesLDL(n, [(self.a[j], self.b[j]) for j in inre])
        r, c_, v = [], [], []
        for j in range(nb):
            for p, ok in ((self.a[j], self.ain[j]), (self.b[j], self.bin[j])):
                if ok:
                    r.append(j); c_.append(p); v.append(1.0)
        self.J_diag = sp.csr_matrix((v, (r, c_)), shape=(nb, n))
        self.J_utom = sp.csr_matrix((-np.ones(len(inre)), (inre, [self.ldl.par[(min(self.a[j], self.b[j]),
                                    max(self.a[j], self.b[j]))] for j in inre])), shape=(nb, self.ldl.m))
        # ändar vid inre noder för blandningen: (gren, nod, andra änden, är änden b)
        e_gren, e_nod, e_andra, e_arb = [], [], [], []
        for j in range(nb):
            if self.ain[j]:
                e_gren.append(j); e_nod.append(self.a[j]); e_andra.append(self.b[j]); e_arb.append(False)
            if self.bin[j]:
                e_gren.append(j); e_nod.append(self.b[j]); e_andra.append(self.a[j]); e_arb.append(True)
        self.e_gren, self.e_nod, self.e_andra, self.e_arb = map(np.array, (e_gren, e_nod, e_andra, e_arb))
        ne = len(self.e_gren)
        self.S_diag = sp.csr_matrix((np.ones(ne), (np.arange(ne), self.e_nod * n + self.e_nod)), shape=(ne, n * n))
        inre = self.e_andra >= 0
        self.S_off = sp.csr_matrix((np.ones(inre.sum()), (np.arange(ne)[inre], self.e_nod[inre] * n + self.e_andra[inre])),
                                   shape=(ne, n * n))
        # takfallen och deras celler
        f = N["fall"]
        self.fall = f
        self.nf, self.nc = len(f), N["celler"]
        self.fasad = g["fasad"][f]
        self.dl = g["L"][f] / self.nc
        self.A_cell = N["bredd"] * self.dl                         # yta per cell [m²]
        self.A_fl = A[f]
        self.h = h
        # cellernas mitt i plan [mm] och remsans y
        x0, x1 = g["x0"][f], g["x1"][f]
        t = (np.arange(self.nc) + 0.5) / self.nc
        self.cell_x = (x0[:, None] + (x1 - x0)[:, None] * t[None, :]).ravel()
        self.cell_y = np.repeat([N["remsor"][s][0] for s in g["remsa"][f]], self.nc)

    # -------------------------------------------------------------- luftflöde
    def gren_q(self, dP):
        """Grenflödet Q [m³/s] och dQ/dΔP för tryckskillnaden dP: ΔP = max(R_lam |Q|, C_t |Q|^1,75) sgn Q + R2 Q |Q|.
        Förlusten är konvex i |Q|; Newton från den laminära lösningen (som ger störst |Q|) närmar sig roten ovanifrån."""
        Q = 2 * dP / (self.R_lam + np.sqrt(self.R_lam ** 2 + 4 * self.R2 * np.abs(dP)))
        for _ in range(50):
            aq = np.abs(Q)
            Rt = self.C_t * aq ** 0.75
            tu = Rt > self.R_lam
            f = np.where(tu, Rt, self.R_lam) * Q + self.R2 * Q * aq - dP
            df = np.where(tu, 1.75 * Rt, self.R_lam) + 2 * self.R2 * aq
            dQ = f / df
            Q = Q - dQ
            if (np.abs(dQ) <= 1e-13 + 1e-10 * np.abs(Q)).all():
                break
        aq = np.abs(Q)
        Rt = self.C_t * aq ** 0.75
        df = np.where(Rt > self.R_lam, 1.75 * Rt, self.R_lam) + 2 * self.R2 * aq
        return Q, 1.0 / df

    def los_jacobian(self, g, F):
        """dP med J dP = F per timme, där J är Jacobianen för grenarnas ledningsförmåga g (nh, nb). Glest för många
        timmar på en gång, tätt (LAPACK) för få."""
        if len(g) < 16:
            J = (self.SJ.T @ g.T).T.reshape(len(g), self.n, self.n)
            return np.linalg.solve(J, F[..., None])[..., 0]
        return self.ldl.los(np.asarray(g @ self.J_diag), np.asarray(g @ self.J_utom), F)

    def flode(self, p_ext_a, p_ext_b, B, P0=None, tol=1e-9, maxit=40):
        """Flödet i alla grenar [m³/s] för timmarna i blocket (Newton med linjesökning per timme).
        p_ext: tryck ute vid grenändarna, B: stigkraft i grenarna [Pa]. Utan startvärde (P0) börjar Newton i det
        laminära nätets tryck; bara timmarna som inte har konvergerat räknas i varje iteration."""
        nh = B.shape[0]

        def res(P, r):
            Pa = np.where(self.ain, P[:, np.maximum(self.a, 0)], p_ext_a[r])
            Pb = np.where(self.bin, P[:, np.maximum(self.b, 0)], p_ext_b[r])
            Q, gq = self.gren_q(Pa - Pb + B[r])
            return Q, gq, (self.Ainc @ Q.T).T

        if P0 is None:                                         # det laminära nätet: ett linjärt system
            g0 = np.broadcast_to(1.0 / self.R_lam, (nh, self.nb))
            Pa0 = np.where(self.ain, 0.0, p_ext_a); Pb0 = np.where(self.bin, 0.0, p_ext_b)
            F0 = (self.Ainc @ (g0 * (Pa0 - Pb0 + B)).T).T
            P = -self.los_jacobian(g0, F0)
        else:
            P = P0.copy()
        Q, gq, F = res(P, slice(None))
        nF = np.abs(F).max(axis=1)
        for it in range(maxit):
            skala = tol + 1e-7 * np.abs(Q).max(axis=1)
            a = np.flatnonzero(nF >= skala)                   # konvergerade timmar flyttas inte
            if not len(a):
                break
            dP = self.los_jacobian(gq[a], F[a])
            lam = np.ones(len(a))
            kvar = np.ones(len(a), bool)                       # linjesökningen pågår
            P0, nF0 = P[a], nF[a]
            for _ in range(12):
                k = np.flatnonzero(kvar)
                r = a[k]
                Pn = P0[k] - lam[k, None] * dP[k]
                Qn, gn, Fn = res(Pn, r)
                nFn = np.abs(Fn).max(axis=1)
                ok = nFn < nF0[k]
                P[r[ok]], Q[r[ok]], gq[r[ok]], F[r[ok]], nF[r[ok]] = Pn[ok], Qn[ok], gn[ok], Fn[ok], nFn[ok]
                kvar[k[ok]] = False
                if not kvar.any():
                    break
                lam[kvar] /= 2
        return Q, P

    # -------------------------------------------------------------- blandning i noderna
    def blanda(self, Q, cF, dF, cB, dB, yttre, eps=1e-9):
        """Nodvärden (temperatur eller ångtryck) för timmarna i blocket.
        Takfallens överföring i flödets riktning: ut = c·in + d (cF, dF framåt a → b, cB, dB bakåt);
        samlingskanaler och gavelöppningar överför oförändrat. yttre: uteluftens värde per timme."""
        nh = Q.shape[0]
        c = np.ones_like(Q); d = np.zeros_like(Q)
        f = self.fall
        fram = Q[:, f] >= 0
        c[:, f] = np.where(fram, cF, cB); d[:, f] = np.where(fram, dF, dB)
        Qe = Q[:, self.e_gren]
        in_ = np.where(self.e_arb, Qe > 0, Qe < 0)                # flödet går in i noden genom den här änden
        w = np.abs(Qe) * in_
        ce, de = c[:, self.e_gren], d[:, self.e_gren]
        Mf = (self.S_diag.T @ w.T).T - (self.S_off.T @ (w * ce).T).T
        M = Mf.reshape(nh, self.n, self.n) + eps * np.eye(self.n)
        ute = (self.e_andra < 0)
        r = w * (de + ce * yttre[:, None] * ute)
        rhs = np.zeros((nh, self.n))
        np.add.at(rhs.T, self.e_nod, r.T)
        rhs += eps * yttre[:, None]
        return M, rhs


# ------------------------------------------------------------------ en körning
def kor(I, N, K, fall, logg=print):
    """Kör ett fall över hela klimatserien. Returnerar resultat per cell och takfall."""
    U, F_, M_ = I["uppbyggnad"], I["fukt"], I["mogel"]
    nat = Natverk(I, N)
    S = Sorption(F_["phi"], F_["u"])
    nh_tot = len(K["T"])
    nf, nc = nat.nf, nat.nc
    ncell = nf * nc
    lut = math.radians(I["tak"]["lutning"])
    Fs, Fg = (1 + math.cos(lut)) / 2, (1 - math.cos(lut)) / 2
    g_d, g_i = 1 / U["R_dack"], 1 / U["R_in"]
    h_rg = 4 * SIGMA * 278.0 ** 3 / (2 / U["eps"] - 1)                  # råspont ↔ träfiberskiva över spalten
    eps_plat = fall.get("eps_plat", U["eps_plat"])                       # plåtens ovansida mot himlen
    manad = K["t"].astype("datetime64[M]").astype(int) % 12 + 1
    tomt = np.isin(manad, fall.get("tomt_manader", [])) if fall.get("T_tomt") is not None else np.zeros(nh_tot, bool)
    Ti_t = np.where(tomt, fall.get("T_tomt", 0.0), I["inne"]["T"])                # [°C] per timme
    fasader = sorted(set(np.round(nat.fasad, 3)))
    Isol = {fz: instralning(K, I["tak"]["lutning"], fz) for fz in fasader}
    vind = fall.get("vind", I["vind"]["faktor"])
    ovent = fall.get("oventilerad", False)
    g = N["gren"]
    cp_a = {j: cp(I, K["WD"], g["az_a"][j], 0 if g["typ"][j] == 0 else 2) for j in range(nat.nb) if not nat.ain[j]}
    cp_b = {j: cp(I, K["WD"], g["az_b"][j], 0 if g["typ"][j] == 0 else 2) for j in range(nat.nb) if not nat.bin[j]}
    # inneklimat
    v_e = K["e"] / (RV * (K["T"] + 273.15))

    def p_inne(tillskott, rf_max):
        dv = tillskott / 1000 * np.clip((20 - K["T"]) / 20, 0, 1)
        return np.minimum((v_e + dv) * RV * (Ti_t + 273.15), rf_max * psat(Ti_t))

    tillskott = np.where(tomt, fall.get("fukttillskott_tomt", 0.0), fall.get("fukttillskott", I["inne"]["fukttillskott"]))
    p_i = p_inne(tillskott, I["inne"]["RF_max"])
    bad = np.zeros(nat.nf * nat.nc, bool)
    sd_bad = None
    if fall.get("badrum"):
        Bd = I["inne"]["badrum"]
        bad = (nat.cell_x > Bd["x"][0]) & (nat.cell_x < Bd["x"][1]) & (nat.cell_y > Bd["y"][0]) & (nat.cell_y < Bd["y"][1])
        p_i_bad = p_inne(Bd["fukttillskott"], Bd["RF_max"])
        sd_bad = fall.get("sd_badrum")
    # fuktbuffertar och mögel
    m_r1 = F_["rho_raspont"] * F_["yt"] / 1000
    m_r2 = F_["rho_raspont"] * F_["karna"] / 1000
    k12 = DELTA_A / F_["my_tra"] / 0.010
    m_M = F_["m_masonit"]
    Z_mas = fall.get("sd_masonit", U["sd_masonit"]) / DELTA_A
    AB = U["angbroms"]
    ab_rf, ab_lnsd = np.array(AB["rf"]), np.log(np.array(AB["sd"]))
    u0 = fall.get("u0", F_["u0"])
    u1 = np.full(ncell, u0); u2 = np.full(ncell, u0); uM = np.full(ncell, S.u_av(0.5))
    Mr = np.zeros(ncell); Mm = np.zeros(ncell); tr_ogy = np.zeros(ncell); tm_ogy = np.zeros(ncell)
    t_utv = np.datetime64(I["klimat"]["utvardering"])
    utv = K["t"] >= t_utv
    Mr_max = np.zeros(ncell); Mm_max = np.zeros(ncell)
    dag0 = K["t"][0].astype("datetime64[D]")
    ndag = int((K["t"][-1].astype("datetime64[D]") - dag0).astype(int)) + 1
    dag = dict(Mr=np.zeros((ndag, ncell), np.float32), Mm=np.zeros((ndag, ncell), np.float32), RHr=np.zeros((ndag, ncell), np.float32),
               u2=np.zeros((ndag, ncell), np.float32), n=np.zeros(ndag))
    dagidx = (K["t"].astype("datetime64[D]") - dag0).astype(int)
    Qfall = np.zeros((nh_tot, nf), np.float32)
    cell_fall = np.repeat(np.arange(nf), nc)
    A_c = np.repeat(nat.A_cell, nc)
    blk = I["modell"]["block"]
    for i0 in range(0, nh_tot, blk):
        sl = slice(i0, min(i0 + blk, nh_tot))
        nh = sl.stop - sl.start
        Te, Uw, P = K["T"][sl], K["U"][sl], K["P"][sl]
        Ti = Ti_t[sl]
        rho_e = P / (RA * (Te + 273.15))
        q = 0.5 * rho_e * Uw ** 2 * vind
        p_ext_a = np.zeros((nh, nat.nb)); p_ext_b = np.zeros((nh, nat.nb))
        for j, v in cp_a.items():
            p_ext_a[:, j] = v[sl] * q
        for j, v in cp_b.items():
            p_ext_b[:, j] = v[sl] * q
        Tenv4 = Fs * K["Lsky"][sl] / SIGMA + Fg * (Te + 273.15) ** 4
        Tenv = Tenv4 ** 0.25 - 273.15
        h_ec = 4.0 + 2.0 * Uw
        qs = np.stack([fall.get("alfa_sol", U["alfa_sol"]) * Isol[round(fz, 3)][sl] for fz in nat.fasad], axis=1)   # (nh, nf)
        B = np.zeros((nh, nat.nb))
        Q = np.zeros((nh, nat.nb)); Pn_ = None
        n_varv = I["modell"]["varv"] if not ovent else 1
        Tp = np.repeat(Te[:, None], nf, 1)[:, :, None] * np.ones(nc)       # strålningen linjäriseras kring förra varvets plåt
        for varv in range(n_varv):
            if not ovent:
                Q, Pn_ = nat.flode(p_ext_a, p_ext_b, B, P0=Pn_)
            Qf = Q[:, nat.fall]
            v = np.abs(Qf) / nat.A_fl
            Re = v * 2 * nat.h / 1.4e-5
            h_c = np.maximum(2.7, 0.023 * Re ** 0.8 * 0.71 ** 0.4 * 0.025 / (2 * nat.h))                 # (nh, nf)
            C = RHO * CP * np.abs(Qf)
            NTU = np.where(C > 0, 2 * nat.A_cell * h_c / np.maximum(C, 1e-30), np.inf)
            psi = np.exp(-NTU)
            phi = np.where(np.isfinite(NTU), -np.expm1(-NTU) / np.where(np.isfinite(NTU), NTU, 1.0), 0.0)
            for rad in range(2 if varv == n_varv - 1 else 1):
                Tbar = 0.5 * (Tp + 273.15 + (Tenv4 ** 0.25)[:, None, None])
                h_lw = 4 * eps_plat * SIGMA * Tbar ** 3                                                  # (nh, nf, nc)
                k1 = (h_c * (1 - phi) / 2)[:, :, None]
                hc = h_c[:, :, None]
                a00 = -(h_lw + h_ec[:, None, None] + g_d)
                a11 = -(g_d + hc + h_rg) + k1
                a12 = h_rg + k1
                a22 = -(g_i + hc + h_rg) + k1
                r0 = -(qs[:, :, None] + h_lw * Tenv[:, None, None] + (h_ec * Te)[:, None, None])
                r1 = -(hc * phi[:, :, None]) * np.ones(nc)
                x = _los3(a00, g_d, a11, a12, a22, (r0, 0.0, -g_i * Ti[:, None, None]), (0.0, r1, r1))
                o0 = (1 - psi)[:, :, None] * (x[..., 1, 0] + x[..., 2, 0]) / 2
                o1 = (1 - psi)[:, :, None] * (x[..., 1, 1] + x[..., 2, 1]) / 2 + psi[:, :, None]
                cF, dF, cB, dB = _komponera(o0, o1)
                Mn, rhs = nat.blanda(Q, cF, dF, cB, dB, Te)
                Tn = np.linalg.solve(Mn, rhs[..., None])[..., 0]
                Tin = _inlopp(nat, Q, Tn, Te)
                Tcell_in = _celler_in(o0, o1, Tin, Qf >= 0)                                              # (nh, nf, nc)
                Tp = x[..., 0, 0] + x[..., 0, 1] * Tcell_in
                Tr = x[..., 1, 0] + x[..., 1, 1] * Tcell_in
                Tm = x[..., 2, 0] + x[..., 2, 1] * Tcell_in
            Ta = (1 - phi)[:, :, None] * (Tr + Tm) / 2 + phi[:, :, None] * Tcell_in
            rho_f = P[:, None] / (RA * (Ta.mean(axis=2) + 273.15))
            Bn = np.zeros((nh, nat.nb))
            Bn[:, nat.fall] = (rho_e[:, None] - rho_f) * G * nat.dz[nat.fall]
            B = Bn if varv == 0 else 0.5 * (B + Bn)
        Qfall[sl] = Qf
        # ---------------- fukt: överföringen i luften är oberoende av buffertarna inom timmen
        Tr = Tr.reshape(nh, ncell); Tm = Tm.reshape(nh, ncell)
        Ta_f = Ta.mean(axis=2)
        beta = 6.3e-9 * h_c                                                                              # Lewis [kg/(m² s Pa)]
        g_m = 1.0 / (Z_mas + 1.0 / beta)
        s = (nat.A_cell[None, :] * (beta + g_m))                                                         # (nh, nf)
        a_adv = np.abs(Qf) / (RV * (Ta_f + 273.15))
        NTUv = np.where(a_adv > 0, s / np.maximum(a_adv, 1e-30), np.inf)
        psiv = np.exp(-NTUv)
        phiv = np.where(np.isfinite(NTUv), -np.expm1(-NTUv) / np.where(np.isfinite(NTUv), NTUv, 1.0), 0.0)
        ones = np.ones((nh, nf, nc))
        cF, _, cB, _ = _komponera(np.zeros((nh, nf, nc)), psiv[:, :, None] * ones)
        Mn, _ = nat.blanda(Q, cF, np.zeros_like(cF), cB, np.zeros_like(cB), Te)
        Minv = np.linalg.inv(Mn)
        fram = Qf >= 0
        e_ute = K["e"][sl]
        bc = np.repeat(beta, nc, axis=1); gmc = np.repeat(g_m, nc, axis=1)
        psic = np.repeat(psiv, nc, axis=1).reshape(nh, nf, nc); phic = np.repeat(phiv, nc, axis=1)
        T_mem = Ti[:, None] - (Ti[:, None] - Tm) * U["R_innanfor_angbroms"] / U["R_in"]
        for t in range(nh):
            it = sl.start + t
            ps_r, ps_m = psat(Tr[t]), psat(Tm[t])
            phi1, phi2, phiM = S.phi_av(u1), S.phi_av(u2), S.phi_av(uM)
            p_r, p_M = phi1 * ps_r, phiM * ps_m
            peq = (bc[t] * p_r + gmc[t] * p_M) / (bc[t] + gmc[t])
            pe = peq.reshape(nf, nc)
            # d i flödets riktning för varje takfall
            ps_ = psic[t]
            dFw = np.zeros(nf); dBw = np.zeros(nf)
            for k in range(nc):
                dFw = ps_[:, k] * dFw + (1 - ps_[:, k]) * pe[:, k]
                kb = nc - 1 - k
                dBw = ps_[:, kb] * dBw + (1 - ps_[:, kb]) * pe[:, kb]
            d_t = np.where(fram[t], dFw, dBw)
            # nodernas ångtryck
            rhs = _rhs_fukt(nat, Q[t], d_t, cF[t], cB[t], e_ute[t])
            pn = Minv[t] @ rhs
            p_in_f = _inlopp1(nat, Q[t], pn, e_ute[t])
            # cellernas inlopp och medelvärde
            pin = np.empty((nf, nc))
            x_ = p_in_f.copy()
            for k in range(nc):
                kk = np.where(fram[t], k, nc - 1 - k)
                idx = (np.arange(nf), kk)
                pin[idx] = x_
                x_ = ps_[idx] * x_ + (1 - ps_[idx]) * pe[idx]
            pin = pin.reshape(ncell)
            pm = phic[t] * pin + (1 - phic[t]) * peq
            # råsponten: ytskikt och kärna (implicit i φ)
            c1 = m_r1 * S.lutning(phi1) / 3600
            phi1n = (c1 * phi1 + bc[t] * pm + k12 * phi2 * ps_r) / (c1 + (bc[t] + k12) * ps_r)
            fl1 = bc[t] * (pm - phi1n * ps_r) - k12 * (phi1n - phi2) * ps_r
            u1 = np.maximum(u1 + fl1 * 3600 / m_r1, 0)
            u2 = np.maximum(u2 + k12 * (phi1n - phi2) * ps_r * 3600 / m_r2, 0)
            # träfiberskivan och isoleringens överdel: inifrån genom gips, ångbroms och isolering
            pin_ = np.where(bad, p_i_bad[it], p_i[it]) if bad.any() else p_i[it]
            phi_mem = np.clip(0.5 * (pin_ + p_M) / psat(T_mem[t]), 0, 1)
            sd_ab = np.exp(np.interp(phi_mem, ab_rf, ab_lnsd))
            if sd_bad is not None:
                sd_ab = np.where(bad, sd_bad, sd_ab)
            Z_in = (U["sd_gips"] + sd_ab + U["sd_iso"]) / DELTA_A
            cM = m_M * S.lutning(phiM) / 3600
            phiMn = (cM * phiM + pin_ / Z_in + gmc[t] * pm) / (cM + (1 / Z_in + gmc[t]) * ps_m)
            uM = np.maximum(uM + ((pin_ - phiMn * ps_m) / Z_in - gmc[t] * (phiMn * ps_m - pm)) * 3600 / m_M, 0)
            RHr = np.minimum(S.phi_av(u1), 1.0); RHm = np.minimum(S.phi_av(uM), 1.0)
            Mr, tr_ogy = vtt_steg(Mr, tr_ogy, Tr[t], RHr, M_["W"], M_["SQ"])
            Mm, tm_ogy = vtt_steg(Mm, tm_ogy, Tm[t], RHm, M_["W"], M_["SQ"])
            if utv[it]:
                np.maximum(Mr_max, Mr, out=Mr_max); np.maximum(Mm_max, Mm, out=Mm_max)
            dd = dagidx[it]
            dag["Mr"][dd] = np.maximum(dag["Mr"][dd], Mr); dag["Mm"][dd] = np.maximum(dag["Mm"][dd], Mm)
            dag["RHr"][dd] += RHr; dag["u2"][dd] += u2; dag["n"][dd] += 1
        logg(f"  {str(K['t'][sl.start])[:10]}  M_r max {Mr_max.max():.2f}")
    dag["RHr"] /= np.maximum(dag["n"], 1)[:, None]; dag["u2"] /= np.maximum(dag["n"], 1)[:, None]
    return dict(Mr_max=Mr_max, Mm_max=Mm_max, Qfall=Qfall, dag=dag, nat=nat, cell_fall=cell_fall, u1=u1, u2=u2, uM=uM, bad=bad)


def _los3(a00, g_d, a11, a12, a22, r_c, r_t):
    """Cellens system för (Tp, Tr, Tm), symmetriskt kopplat: rad 0 (plåt) a00·Tp + g_d·Tr, rad 1 (råspont)
    g_d·Tp + a11·Tr + a12·Tm, rad 2 (träfiberskiva) a12·Tr + a22·Tm. Två högerled: konstant och per °C inlopp.
    Returnerar x[..., i, j] som np.linalg.solve med högerleden som kolumner."""
    b11 = a11 - g_d ** 2 / a00
    det = b11 * a22 - a12 ** 2
    ut = []
    for r0, r1, r2 in (r_c, r_t):
        s1 = r1 - g_d * r0 / a00
        Tr = (s1 * a22 - a12 * r2) / det
        Tm = (b11 * r2 - a12 * s1) / det
        Tp = (r0 - g_d * Tr) / a00
        ut.append(np.stack(np.broadcast_arrays(Tp, Tr, Tm), axis=-1))
    return np.stack(ut, axis=-1)


def _komponera(o0, o1):
    """Takfallens överföring ut = c·in + d genom cellerna, framåt (a → b) och bakåt."""
    nh, nf, nc = o0.shape
    cF = np.ones((nh, nf)); dF = np.zeros((nh, nf)); cB = np.ones((nh, nf)); dB = np.zeros((nh, nf))
    for k in range(nc):
        cF, dF = o1[:, :, k] * cF, o1[:, :, k] * dF + o0[:, :, k]
        kb = nc - 1 - k
        cB, dB = o1[:, :, kb] * cB, o1[:, :, kb] * dB + o0[:, :, kb]
    return cF, dF, cB, dB


def _inlopp(nat, Q, Xn, yttre):
    """Inloppsvärdet för varje takfall: noden eller uteluften uppströms."""
    f = nat.fall
    a, b = nat.a[f], nat.b[f]
    fram = Q[:, f] >= 0
    up = np.where(fram, a, b)
    return np.where(up >= 0, np.take_along_axis(Xn, np.maximum(up, 0), axis=1), yttre[:, None])


def _inlopp1(nat, Qt, xn, yttre):
    f = nat.fall
    up = np.where(Qt[f] >= 0, nat.a[f], nat.b[f])
    return np.where(up >= 0, xn[np.maximum(up, 0)], yttre)


def _celler_in(o0, o1, Tin, fram):
    """Inloppstemperaturen för varje cell, i flödets riktning."""
    nh, nf, nc = o0.shape
    ut = np.empty((nh, nf, nc))
    xF = Tin.copy(); xB = Tin.copy()
    TF = np.empty_like(ut); TB = np.empty_like(ut)
    for k in range(nc):
        TF[:, :, k] = xF; xF = o1[:, :, k] * xF + o0[:, :, k]
        kb = nc - 1 - k
        TB[:, :, kb] = xB; xB = o1[:, :, kb] * xB + o0[:, :, kb]
    ut[:] = np.where(fram[:, :, None], TF, TB)
    return ut


def _rhs_fukt(nat, Qt, d_t, cFt, cBt, yttre, eps=1e-9):
    c = np.ones(nat.nb); d = np.zeros(nat.nb)
    f = nat.fall
    fram = Qt[f] >= 0
    c[f] = np.where(fram, cFt, cBt); d[f] = d_t
    Qe = Qt[nat.e_gren]
    w = np.abs(Qe) * np.where(nat.e_arb, Qe > 0, Qe < 0)
    r = w * (d[nat.e_gren] + c[nat.e_gren] * yttre * (nat.e_andra < 0))
    rhs = np.bincount(nat.e_nod, weights=r, minlength=nat.n)
    return rhs + eps * yttre


# ------------------------------------------------------------------ mögel (VTT, furu splintved), vektoriserad
def vtt_steg(M, t_ogy, T, RH, W=0, SQ=0):
    """Ett timsteg i VTT-modellen för alla celler. RH 0–1."""
    rh = RH * 100
    Tc = np.clip(T, 0.01, 49.9)
    rh_k = np.where(T <= 20, -0.00267 * Tc ** 3 + 0.160 * Tc ** 2 - 3.13 * Tc + 100, 80.0)
    gynn = (T > 0) & (T < 50) & (rh > rh_k)
    rhc = np.maximum(rh, 1e-3)
    tm = np.exp(-0.68 * np.log(Tc) - 13.9 * np.log(rhc) + 0.14 * W - 0.33 * SQ + 66.02)
    tv = np.exp(-0.74 * np.log(Tc) - 12.72 * np.log(rhc) + 0.06 * W + 61.50)
    k1 = np.where(M >= 1, np.where(tv > tm, 2 / np.maximum(tv / tm - 1, 1e-9), 1.0), 1.0)
    x = (rh_k - rh) / (rh_k - 100)
    Mmax = 1 + 7 * x - 2 * x ** 2
    k2 = np.maximum(1 - np.exp(np.minimum(2.3 * (M - Mmax), 50.0)), 0)
    t_ogy = np.where(gynn, 0.0, t_ogy + 1)
    minskn = np.where(t_ogy <= 6, 0.00133, np.where(t_ogy <= 24, 0.0, 0.000667))
    M = np.where(gynn, M + k1 * k2 / (7 * tm) / 24, np.maximum(M - minskn, 0.0))
    return M, t_ogy
