"""2D stationär värmeledning (linjära triangelelement) för nocken: halva tvärsnittet, symmetri i nockens mitt."""
import math

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
import triangle as tr


def geometri(g):
    """Polygoner för halva tvärsnittet (x ≥ 0). Takets ytterplan går genom balkens övre hörn."""
    a = math.radians(g["takvinkel"])
    s = np.array([math.cos(a), -math.sin(a)])          # längs takfallet, nedåt
    n = np.array([math.sin(a), math.cos(a)])           # normal, utåt/uppåt
    B, tp, h = g["balk_b"] / 2, g["plat_t"], g["tra_h"]
    H = h + 2 * tp
    d = np.cumsum([0, g["masonit"], g["isolering"], g["installation"], g["gips"]])   # djup från ytterplanet
    T = g["tak_langd"]
    P0 = np.array([B, 0.0])

    def vid_x(dk, x):                                   # punkt på skiktgräns dk med givet x
        tt = (x - B + dk * n[0]) / s[0]
        return P0 + tt * s - dk * n

    E = [P0 + T * s - dk * n for dk in d]               # snitt vinkelrätt mot takfallet
    beam_y = [0.0, -tp, -tp - h, -H]
    reg = {}
    reg["plat_over"] = [(0, 0), (B, 0), (B, -tp), (0, -tp)]
    reg["limtra"] = [(0, -tp), (B, -tp), (B, -tp - h), (0, -tp - h)]
    reg["plat_under"] = [(0, -tp - h), (B, -tp - h), (B, -H), (0, -H)]
    m1, i2 = vid_x(d[1], B), vid_x(d[2], B)
    reg["masonit"] = [tuple(P0), tuple(E[0]), tuple(E[1]), tuple(m1)]
    reg["isolering"] = [tuple(m1), tuple(E[1]), tuple(E[2]), tuple(i2)]
    a3, a4 = vid_x(d[3], 0.0), vid_x(d[4], 0.0)
    reg["luft"] = [(0, -H), (B, -H), tuple(i2), tuple(E[2]), tuple(E[3]), tuple(a3)]
    reg["gips"] = [tuple(a3), tuple(E[3]), tuple(E[4]), tuple(a4)]
    ytter = [((0, 0), (B, 0)), (tuple(P0), tuple(E[0]))]
    inner = [(tuple(a4), tuple(E[4]))]
    return reg, ytter, inner, dict(s=s, n=n, d=d, a3=a3, a4=a4, E=E, H=H, B=B)


def natverk(reg, ytter, inner, ytor):
    """Triangelnät med regionattribut och randmarkering (10 = luftspalt, 20 = rum)."""
    pts, idx = [], {}

    def pid(p):
        k = (round(p[0], 6), round(p[1], 6))
        if k not in idx:
            idx[k] = len(pts); pts.append(k)
        return idx[k]
    segs, marks = {}, {}
    for poly in reg.values():
        ids = [pid(p) for p in poly]
        for a_, b_ in zip(ids, ids[1:] + ids[:1]):
            segs[tuple(sorted((a_, b_)))] = 0
    # dela upp segment som har andra hörn på sig (T-korsningar)
    P = np.array(pts)
    changed = True
    while changed:
        changed = False
        for (a_, b_) in list(segs):
            pa, pb = P[a_], P[b_]
            L = np.linalg.norm(pb - pa)
            for k in range(len(P)):
                if k in (a_, b_):
                    continue
                v = P[k] - pa
                tt = v @ (pb - pa) / L ** 2
                if 1e-9 < tt < 1 - 1e-9 and abs(v[0] * (pb - pa)[1] - v[1] * (pb - pa)[0]) / L < 1e-6:
                    del segs[(a_, b_)]
                    segs[tuple(sorted((a_, k)))] = 0; segs[tuple(sorted((k, b_)))] = 0
                    changed = True
                    break
            if changed:
                break

    def markera(lst, m):
        for p, q in lst:
            p, q = np.array(p), np.array(q)
            for (a_, b_) in segs:
                pa, pb = P[a_], P[b_]
                on = all(abs((x - p)[0] * (q - p)[1] - (x - p)[1] * (q - p)[0]) / np.linalg.norm(q - p) < 1e-6
                         and -1e-9 <= (x - p) @ (q - p) / np.linalg.norm(q - p) ** 2 <= 1 + 1e-9 for x in (pa, pb))
                if on:
                    segs[(a_, b_)] = m
    markera(ytter, 10); markera(inner, 20)
    namn = list(reg)
    regions = []
    for i, (k, poly) in enumerate(reg.items()):
        c = np.mean(np.array(poly), axis=0)
        regions.append([c[0], c[1], i, ytor[k]])
    S = np.array(list(segs.keys())); M = np.array(list(segs.values()))
    A = dict(vertices=P, segments=S, segment_markers=M, regions=np.array(regions))
    out = tr.triangulate(A, "pq30Aae")
    return out, namn


def los(out, namn, lam_fn, h_ute, T_ute, h_inne, T_inne, h_plat=None):
    """FE-lösning. lam_fn(region, centroid) -> λ [W/mK]. Längder i mm, λ omräknad till W/(mm·K).
    h_plat: ytövergång på överplåtens ovansida (y = 0) om den skiljer sig från h_ute."""
    X0 = out["vertices"]

    def hT(i, j, m):
        if m == 20:
            return h_inne, T_inne
        if h_plat is not None and abs(X0[i, 1]) < 1e-6 and abs(X0[j, 1]) < 1e-6:
            return h_plat, T_ute
        return h_ute, T_ute
    X = out["vertices"]; Tr = out["triangles"]; att = out["triangle_attributes"][:, 0].astype(int)
    nn = len(X)
    rows, cols, vals = [], [], []
    lam_e = np.zeros(len(Tr))
    for e, (i, j, k) in enumerate(Tr):
        xy = X[[i, j, k]]
        c = xy.mean(axis=0)
        lam = lam_fn(namn[att[e]], c) / 1000.0
        lam_e[e] = lam * 1000
        bmat = np.array([xy[1, 1] - xy[2, 1], xy[2, 1] - xy[0, 1], xy[0, 1] - xy[1, 1]])
        cmat = np.array([xy[2, 0] - xy[1, 0], xy[0, 0] - xy[2, 0], xy[1, 0] - xy[0, 0]])
        A2 = abs(np.linalg.det(np.c_[np.ones(3), xy]))
        Ke = lam / (2 * A2) * (np.outer(bmat, bmat) + np.outer(cmat, cmat))
        for a_ in range(3):
            for b_ in range(3):
                rows.append((i, j, k)[a_]); cols.append((i, j, k)[b_]); vals.append(Ke[a_, b_])
    F = np.zeros(nn)
    E = out["edges"]; EM = out["edge_markers"][:, 0]
    for (i, j), m in zip(E, EM):
        if m not in (10, 20):
            continue
        h, Tinf = hT(i, j, m)
        h = h / 1e6                                     # W/(mm²K)
        L = np.linalg.norm(X[j] - X[i])
        Ke = h * L / 6 * np.array([[2, 1], [1, 2]])
        for a_ in range(2):
            for b_ in range(2):
                rows.append((i, j)[a_]); cols.append((i, j)[b_]); vals.append(Ke[a_, b_])
        F[[i, j]] += h * Tinf * L / 2
    K = sp.csr_matrix((vals, (rows, cols)), shape=(nn, nn))
    T = spla.spsolve(K.tocsc(), F)
    # flöde genom ytterrand respektive innerrand [W/m nock, halva tvärsnittet]
    q = {}
    for (i, j), m in zip(E, EM):
        if m in (10, 20):
            h, Tinf = hT(i, j, m)
            L = np.linalg.norm(X[j] - X[i]) / 1000
            q[m] = q.get(m, 0.0) + h * L * ((T[i] + T[j]) / 2 - Tinf)
    return T, lam_e, q


def medel(out, T, namn, region):
    """Ytviktat medelvärde, min och max av temperaturen i en region."""
    X = out["vertices"]; Tr = out["triangles"]; att = out["triangle_attributes"][:, 0].astype(int)
    r = namn.index(region)
    sel = att == r
    A = 0.5 * np.abs(np.linalg.det(np.stack([np.c_[np.ones(3), X[t]] for t in Tr[sel]])))
    Tm = T[Tr[sel]].mean(axis=1)
    nod = np.unique(Tr[sel])
    return float((A * Tm).sum() / A.sum()), float(T[nod].min()), float(T[nod].max())
