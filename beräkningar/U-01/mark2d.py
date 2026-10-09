"""
U-01: tvådimensionell transient värmeledning i sektion A–A genom källaren, finita volymer på rektangulärt nät.

Modellen omfattar bottenplattan med cellplast, kantbalkar i L-element, plintar (som strimlor), Lecaväggarna,
fyllningen och marken. Källarens luft och uteluften är randvillkor: rummets och uteluftens celler är inaktiva och
ytorna mot dem får värmeövergång R_si respektive R_se. Golvvärmen ges som fast temperatur i slingornas lager.

Tidsstegning: implicit Euler med ett dygns steg. Det periodiska tillståndet, som marken når efter många år, löses
direkt: T0 = Φ(T0), där Φ(T) = M T + c är ett års tidsstegning. (I − M) T0 = c löses med GMRES.
Längder i m.
"""
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spl

DAG = 86400.0
MAT = ("mark", "makadam", "betong", "cellplast", "leca")
RUM, UTE = -1, -2
MAN = (0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334)   # första dagen i varje månad, dag 0 = 1 jan


def kanter(bp, fina, tak, k, h_max):
    """Cellkanter genom alla brytpunkter bp. fina: [(a, b, h)] zoner med cellstorlek h, utanför dem växer cellerna
    med k gånger avståndet. tak: [(a, b, h)] största cellstorlek i ett område."""
    def storlek(s):
        h = h_max
        for a, b, hf in fina:
            h = min(h, hf + k * max(a - s, 0.0, s - b))
        for a, b, ht in tak:
            if a <= s <= b:
                h = min(h, ht)
        return h

    bp = sorted({round(float(v), 6) for v in bp})
    e = [bp[0]]
    for a, b in zip(bp[:-1], bp[1:]):
        s, st = a, []
        while True:
            h = storlek(s)
            if s + h >= b - 0.3 * h:
                st.append(b - s)
                break
            st.append(h)
            s += h
        if len(st) > 1 and st[-1] < 0.5 * st[-2]:
            st = list(np.array(st[:-1]) * (b - a) / sum(st[:-1]))
        e.extend(a + np.cumsum(st))
    e = np.round(np.array(e), 9)
    e[-1] = bp[-1]
    return e


def geometri(P):
    """Sektionens delar i m: lista av (namn, x0, x1, z0, z1) i målningsordning, och nyckelmått."""
    t1, t2, t3 = (v / 1000 for v in P["vagg_skikt"])
    tv = t1 + t2 + t3
    xv, xo = P["xc_v"] - tv / 2, P["xc_o"] + tv / 2          # väggarnas ytterliv
    xiv, xio = xv + tv, xo - tv                               # väggarnas insida
    hp, te, hb, tf = P["h_platta"], P["t_eps"], P["h_balk"], P["t_fot"]
    bb, tb, ur, tm = P["b_balk"], P["t_ben"], P["urtag"], P["t_makadam"]
    zf, zk = -(hp + te), -(hb + tf)                           # cellplastens underkant i fält och under balkar
    zmin = min(zf, zk)
    D = [("makadam", xv - tb, xo + tb, zmin - tm, 0.0)]
    D += [("cellplast", xv + bb, xo - bb, zf, -hp), ("betong", xv + bb, xo - bb, -hp, 0.0)]
    for x0, x1, f0, f1 in ((xv, xv + bb, xv - tb, xv + bb), (xo - bb, xo, xo - bb, xo + tb)):   # kantbalkar och fot
        D += [("betong", x0, x1, -hb, 0.0), ("cellplast", f0, f1, zk, -hb)]
    D += [("cellplast", xv - tb, xv, -hb, 0.0), ("cellplast", xo, xo + tb, -hb, 0.0)]   # L-elementets ben
    for _, xc, b in P["plint"]:
        D += [("betong", xc - b / 2, xc + b / 2, -hb, 0.0), ("cellplast", xc - b / 2, xc + b / 2, zk, -hb)]
    for x0, s in ((xv, 1), (xo, -1)):                         # väggarna, från urtaget till bjälklaget
        lager = [(0, t1, "leca"), (t1, t1 + t2, "cellplast"), (t1 + t2, tv, "leca")]
        for a, b, m in lager:
            xa, xb = sorted((x0 + s * a, x0 + s * b))
            D.append((m, xa, xb, -ur, P["h_rum"]))
    g = dict(xv=xv, xo=xo, xiv=xiv, xio=xio, zf=zf, zk=zk, zmin=zmin, zfolie=-(hp + te / 2), B=xo - xv,
             gv=(xiv + P["golvvarme_kant"], xio - P["golvvarme_kant"], -P["golvvarme_z"]))
    return D, g


def bygg(P, f=1.0):
    """Nät, material, systemmatris och randvillkor. f skalar cellstorlekarna (nätkontroll)."""
    D, g = geometri(P)
    N_ = P["nat"]
    hf = f * N_["h_fin"]
    xv, xo, B = g["xv"], g["xo"], g["B"]
    ut = N_["utbredning"] * B
    zbot = min(P["mark_v"], P["mark_o"]) - ut
    gv0, gv1, zg = g["gv"]
    bx = [xv - ut, xo + ut, gv0, gv1] + [v for d in D for v in d[1:3]]
    bz = [zbot, P["h_rum"], zg - 0.025, zg + 0.025, g["zfolie"], P["mark_v"], P["mark_o"]] + [v for d in D for v in d[3:5]]
    fx = [(xv - 0.8, xv + 1.0, hf), (xo - 1.0, xo + 0.8, hf)] + [(xc - b / 2 - 0.3, xc + b / 2 + 0.3, hf) for _, xc, b in P["plint"]]
    fz = [(g["zmin"] - P["t_makadam"] - 0.15, 0.1, hf)] + [(m - 0.15, m + 0.15, 2 * hf) for m in (P["mark_v"], P["mark_o"])]
    ex = kanter(bx, fx, [(xv, xo, f * N_["h_falt"])], N_["tillvaxt"], f * N_["h_max"])
    ez = kanter(bz, fz, [(0.0, P["h_rum"], f * N_["h_vagg"])], N_["tillvaxt"], f * N_["h_max"])
    xc, zc = (ex[1:] + ex[:-1]) / 2, (ez[1:] + ez[:-1]) / 2
    dx, dz = np.diff(ex), np.diff(ez)
    nx, nz = len(xc), len(zc)
    X, Z = np.meshgrid(xc, zc, indexing="ij")

    mat = np.zeros((nx, nz), int)
    for namn, x0, x1, z0, z1 in D:
        mat[(X > x0) & (X < x1) & (Z > z0) & (Z < z1)] = MAT.index(namn)
    mat[(X > g["xiv"]) & (X < g["xio"]) & (Z > 0)] = RUM
    mat[((X < xv) & (Z > P["mark_v"])) | ((X > xo) & (Z > P["mark_o"]))] = UTE

    lamv = np.array([P[m][0] for m in MAT])
    rcv = np.array([P[m][1] * 1e6 for m in MAT])
    aktiv = mat >= 0
    lam = np.where(aktiv, lamv[np.clip(mat, 0, None)], np.nan)
    idx = -np.ones((nx, nz), int)
    N = int(aktiv.sum())
    idx[aktiv] = np.arange(N)
    rows, cols, vals = [], [], []
    diag = np.zeros(N)
    bi, be = np.zeros(N), np.zeros(N)                       # konduktans mot rummet och mot uteluften

    def ytor(ia, ib, ra, rb, L, Rsi):
        """Ytor mellan cellerna ia och ib (index i nätet, samma form), halva motstånden ra, rb, längd L."""
        ma_, mb_ = mat[ia], mat[ib]
        both = (ma_ >= 0) & (mb_ >= 0)
        G = L[both] / (ra[both] + rb[both])
        ka, kb = idx[ia][both], idx[ib][both]
        rows.extend([ka, kb]); cols.extend([kb, ka]); vals.extend([-G, -G])
        np.add.at(diag, ka, G); np.add.at(diag, kb, G)
        for egen, annan, r, k in ((ma_, mb_, ra, idx[ia]), (mb_, ma_, rb, idx[ib])):
            for kod, R, vek in ((RUM, Rsi, bi), (UTE, P["Rse"], be)):
                s = (egen >= 0) & (annan == kod)
                G = L[s] / (r[s] + R)
                np.add.at(diag, k[s], G); np.add.at(vek, k[s], G)

    # ytor i x-led (vertikala ytor) och i z-led (horisontella ytor)
    I = np.arange(nx)[:, None] * np.ones(nz, int)[None, :]
    J = np.ones(nx, int)[:, None] * np.arange(nz)[None, :]
    a, b = (I[:-1], J[:-1]), (I[1:], J[1:])
    ytor(a, b, dx[:-1, None] / (2 * lam[:-1]), dx[1:, None] / (2 * lam[1:]), np.broadcast_to(dz[None, :], (nx - 1, nz)), P["Rsi_vagg"])
    a, b = (I[:, :-1], J[:, :-1]), (I[:, 1:], J[:, 1:])
    ytor(a, b, dz[None, :-1] / (2 * lam[:, :-1]), dz[None, 1:] / (2 * lam[:, 1:]), np.broadcast_to(dx[:, None], (nx, nz - 1)), P["Rsi_golv"])

    rows = np.concatenate(rows + [np.arange(N)]); cols = np.concatenate(cols + [np.arange(N)])
    vals = np.concatenate(vals + [diag])
    K = sp.csr_matrix((vals, (rows, cols)), shape=(N, N))
    C = (rcv[np.clip(mat, 0, None)] * dx[:, None] * dz[None, :])[aktiv]
    gv = idx[aktiv & (X > gv0) & (X < gv1) & (np.abs(Z - zg) < 0.025)]
    return dict(K=K, C=C, bi=bi, be=be, gv=gv, N=N, ex=ex, ez=ez, xc=xc, zc=zc, dx=dx, dz=dz, mat=mat, lam=lam,
                idx=idx, aktiv=aktiv, g=g, D=D, P=P)


class Ar:
    """Ett års tidsstegning med dygnssteg, golvvärme på eller av, och det periodiska tillståndet."""

    def __init__(self, m, n=1):
        self.m, self.n = m, n                                 # n tidssteg per dygn
        P = m["P"]
        self.Mv = sp.diags(m["C"] * n / DAG)
        on, off = P["golvvarme"]
        self.pa = np.array([d >= MAN[on - 1] or d < MAN[off] for d in range(365)])
        d = np.arange(365) + 0.5
        self.Tute = P["Tm"] + P["A"] * np.cos(2 * np.pi * (d - P["dag_max"]) / 365)
        self.Trum = np.where(self.pa, P["T_rum_vinter"], P["T_rum_sommar"])
        A0 = (self.Mv + m["K"]).tocsr()
        A1 = A0.tolil()
        for k in m["gv"]:
            A1.rows[k] = [k]
            A1.data[k] = [1.0]
        self.los = {False: spl.factorized(A0.tocsc()), True: spl.factorized(A1.tocsc())}

    def steg(self, T, d, kraft=True):
        m = self.m
        for _ in range(self.n):
            b = self.Mv @ T
            if kraft:
                b = b + m["bi"] * self.Trum[d] + m["be"] * self.Tute[d]
            if self.pa[d]:
                b[m["gv"]] = self.m["P"]["T_golvvarme"] if kraft else 0.0
            T = self.los[bool(self.pa[d])](b)
        return T

    def balans(self, T0):
        """Värmebalans över ett år från T0 (J per m): golvvärme, rum, ute och lagrad värme."""
        m, K = self.m, self.m["K"]
        Q = dict(golvvarme=0.0, rum=0.0, ute=0.0)
        T = T0.copy()
        for d in range(365):
            for _ in range(self.n):
                T1 = self.steg_ett(T, d)
                r = self.Mv @ (T1 - T) + K @ T1 - m["bi"] * self.Trum[d] - m["be"] * self.Tute[d]
                dt = DAG / self.n
                if self.pa[d]:
                    Q["golvvarme"] += r[m["gv"]].sum() * dt
                Q["rum"] += (m["bi"] * (self.Trum[d] - T1)).sum() * dt
                Q["ute"] += (m["be"] * (self.Tute[d] - T1)).sum() * dt
                T = T1
        Q["lagrat"] = float((m["C"] * (T - T0)).sum())
        return Q

    def steg_ett(self, T, d):
        m = self.m
        b = self.Mv @ T + m["bi"] * self.Trum[d] + m["be"] * self.Tute[d]
        if self.pa[d]:
            b[m["gv"]] = m["P"]["T_golvvarme"]
        return self.los[bool(self.pa[d])](b)

    def kor(self, T0, kraft=True, spara=None, falt=()):
        """Ett år från T0. spara(T, d) anropas varje dygn; falt: dygn då hela fältet sparas."""
        T, F = T0.copy(), {}
        for d in range(365):
            T = self.steg(T, d, kraft)
            if spara is not None:
                spara(T, d)
            if d in falt:
                F[d] = T.copy()
        return T, F

    def periodisk(self, tol=1e-9):
        """T0 med Φ(T0) = T0. Returnerar T0, antal GMRES-iterationer och största avvikelse efter ett år."""
        N = self.m["N"]
        c, _ = self.kor(np.zeros(N))
        Mop = spl.LinearOperator((N, N), matvec=lambda x: x - self.kor(x, kraft=False)[0])
        n = [0]
        T0, info = spl.gmres(Mop, c, x0=c.copy(), rtol=tol, restart=60, maxiter=200,
                             callback=lambda r: n.__setitem__(0, n[0] + 1), callback_type="pr_norm")
        if info != 0:
            raise RuntimeError(f"GMRES konvergerade inte ({info})")
        T1, _ = self.kor(T0)
        return T0, n[0], float(np.max(np.abs(T1 - T0)))


def faltvarde(m, T):
    """Temperaturen i nätets celler (nan i rum och ute)."""
    F = np.full(m["mat"].shape, np.nan)
    F[m["aktiv"]] = T
    return F


def kolumner(m):
    """Kolumner under plattan: typ (fält, kantbalk, plint), x och cellindex kring cellplastens över- och underkant
    och folien. Gränsytans temperatur vägs med cellernas halva motstånd."""
    g, P, xc, ez, zc = m["g"], m["P"], m["xc"], m["ez"], m["zc"]
    ut = []
    for i, x in enumerate(xc):
        if not (g["xv"] < x < g["xo"]):
            continue
        typ = "falt"
        if x < g["xv"] + P["b_balk"] or x > g["xo"] - P["b_balk"]:
            typ = "kant"
        for _, c, b in P["plint"]:
            if abs(x - c) < b / 2:
                typ = "plint"
        if typ == "falt":
            zo, zu = -P["h_platta"], g["zf"]
        else:
            zo, zu = -P["h_balk"], g["zk"]
        def yta(z):
            j = int(np.argmin(np.abs(ez - z)))                   # ytan mellan cell j−1 (under) och j (över)
            return m["idx"][i, j - 1], m["idx"][i, j], m["dz"][j - 1] / (2 * m["lam"][i, j - 1]), m["dz"][j] / (2 * m["lam"][i, j])
        r = dict(typ=typ, x=x, i=i, over=yta(zo), under=yta(zu))
        if typ == "falt":
            r["folie"] = yta(g["zfolie"])
        ut.append(r)
    return ut


def ytT(T, y):
    """Temperatur i gränsytan mellan två celler."""
    ku, ko, ru, ro = y
    return (T[ku] / ru + T[ko] / ro) / (1 / ru + 1 / ro)


def ps(T):
    """Mättnadsångtryck (Pa), Magnus."""
    return 610.5 * np.exp(17.269 * T / (237.3 + T))
