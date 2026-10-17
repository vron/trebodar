"""
K-06: samverkande FE-modell av mellanbjälklaget (K-05) och bottenplattan.

    mellanbjälklaget (K-05:s nät och laster)
        |  källarväggarna (Kub 350-150): betongkärnan som fjäder E·t/h längs K-05:s upplagslinjer   rör: E·A/L
    bottenplattan 100 mm med kantbalkar, balkar under innerväggarna och plintar under rören
        |  cellplast: bädd E/t (olika under plattan och under balkar och plintar)
    berg/makadam (styvt)

Laster som står över en källarvägg (K-05: plats "vägg") går direkt ned i väggen och läggs på bottenplattan.
Väggarnas egentyngd och fasadstenen läggs som linjelast på bottenplattan. Alla delar är linjära, så lastfallen kan
kombineras.

    python modell06.py L300     -> nätstorlek, lastsummor och jämvikt
"""
import os
import sys

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
from matplotlib.path import Path as MplPath

import indata as I
import modell as M05              # K-05 (via sys.path i indata)
from platta import Platta, Dmat, Resultat
from ec2 import Betong
import laster as LA05

B = Betong(fck=25)
BV = Betong(fck=I.FCK_V)                 # källarväggarnas kärna
NU = 0.2
G = I.G05
STODLIN = [[(a, c), (bb, c)] if ax == "h" else [(c, a), (c, bb)] for ax, c, a, bb in G["stod"]]
VAGGLIN = [[(a, c), (bb, c)] if ax == "h" else [(c, a), (c, bb)] for ax, c, a, bb, typ, cs in G["vagg"]]
VTYP = [w[4] for w in G["vagg"]]
INRE = [i for i, t in enumerate(VTYP) if t == "inre"]
ROR = M05.rorstod()                                  # (namn, x, y, bx, by, antal rör); P7 är två rör (K-05)
PEL = [(x, y) for _, x, y, _, _, _ in ROR]           # stödens mitt
K_ROR = 210000 * M05.A_ROR / M05.L_ROR              # N/mm per rör


# ------------------------------------------------------------------ bottenplattans geometri
def ytterkontur():
    """Källarens yttre kontur = väggarnas ytterliv (K-05:s plattkant + 30 mm) = L-elementens ytterkant, utan delen med
    platta på mark, som avgränsas av V3:s och V20:s ytterliv."""
    k = Polygon(G["kontur"]).buffer(I.KI, join_style=2)
    y3, x20 = G["vagg"][2][1], G["vagg"][19][1]                       # V3 och V20, centrumlinjer
    ut = box(-500, y3 + I.T_VAGG / 2, x20 - I.T_VAGG / 2, 16500)
    return k.difference(ut)


def kallare():
    """Bottenplattans betong: ytterkonturen minskad med L-elementets yttre ben, 100 mm (betongens kant i kärnans
    yttre yta)."""
    return ytterkontur().buffer(-I.L_BEN, join_style=2)


def balkar(plint):
    """Kantbalk längs hela konturen, balkar under innerväggarna och plintar (sida plint[i]) under rören."""
    poly = kallare()
    kant = poly.difference(poly.buffer(-I.B_BALK, join_style=2))
    # V4–V6 står på en balk i hela linjen mellan V19 och V15, också under dörröppningarna. Ändarna förlängs en halv
    # balkbredd, så att balkarna är hela i hörnen och når kantbalken.
    y4, x19, x15 = G["vagg"][3][1], G["vagg"][18][1], G["vagg"][14][1]
    inre = unary_union([LineString(VAGGLIN[i]).buffer(I.B_BALK / 2, cap_style=3) for i in INRE] +
                       [LineString([(x19, y4), (x15, y4)]).buffer(I.B_BALK / 2, cap_style=3)])
    pl = [box(x - b / 2, y - b / 2, x + b / 2, y + b / 2) for (x, y), b in zip(PEL, plint)]
    return poly, kant, inre.intersection(poly), unary_union(pl).intersection(poly)


def _ring_coords(g):
    out = []
    for p in getattr(g, "geoms", [g]):
        if p.is_empty:
            continue
        out.append(list(p.exterior.coords)[:-1])
        for h in p.interiors:
            out.append(list(h.coords)[:-1])
    return out


# ------------------------------------------------------------------ mellanbjälklaget
def topp(hmax=200.0, k_mark=None):
    """K-05:s nät utan väggar och rör som stöd. Platta på mark (plan 1) på bädd k_mark [N/mm³]."""
    LASTER = M05.LASTER
    linjer = list(STODLIN) + [l["pl"] for l in LASTER["linjer"] if l["namn"] == "qD2"]
    punkter = [(p["x"], p["y"]) for p in LASTER["punkter"] if p["plats"] != "vägg"]
    stolpar = [(p["x"], p["y"]) for p in LASTER["punkter"] if p["plats"] == "platta"]
    P = Platta(G["kontur"], hal=[G["hal"]], linjer=linjer + [list(map(tuple, G["mark"])) + [tuple(G["mark"][0])]],
               punkter=punkter, rektanglar=[(x, y, bx, by) for _, x, y, bx, by, _ in ROR], hmax=hmax,
               finare=[(x, y, 1.5 * M05.PLAT, 50 * M05.FIN) for x, y in PEL] +
                      [(x, y, 300.0, 80.0 * M05.FIN) for pl in STODLIN for x, y in pl] +
                      [(x, y, 400.0, 60.0 * M05.FIN) for x, y in stolpar])
    P.stod_mark("mark", G["mark"], M05.K_EPS if k_mark is None else k_mark)
    return P


# ------------------------------------------------------------------ bottenplattan
def botten(utf, plint, hmax=200.0):
    poly, kant, inre, pl = balkar(plint)
    tjock = unary_union([kant, inre, pl])
    linjer = [list(c) + [c[0]] for c in _ring_coords(tjock)]
    linjer += [list(l) for l in STODLIN] + [list(l) for l in VAGGLIN]
    yttre = [list(c) for c in _ring_coords(poly)]
    assert len(yttre) == 1
    P = Platta(yttre[0], linjer=linjer, rektanglar=[(x, y, bx, by) for _, x, y, bx, by, _ in ROR], hmax=hmax,
               finare=[(x, y, 400.0, 60.0) for x, y in PEL] + [(x, y, 300.0, 80.0) for pl_ in STODLIN for x, y in pl_])
    cen = P.cen
    i_tjock = MplPath(np.zeros((1, 2))).contains_points(cen)       # alla falska
    for g in getattr(tjock, "geoms", [tjock]):
        sh = MplPath(np.asarray(g.exterior.coords))
        ins = sh.contains_points(cen)
        for hh in g.interiors:
            ins &= ~MplPath(np.asarray(hh.coords)).contains_points(cen)
        i_tjock |= ins
    P.h_el = np.where(i_tjock, utf["h_balk"], I.H_PLATTA)
    P.tjock = i_tjock
    P.geo06 = dict(poly=poly, kant=kant, inre=inre, plint=pl, tjock=tjock)
    return P


def styvheter(Pt, Pb, E_betong):
    Pt.styvhet(Dmat(E_betong * M05.H ** 3 / 12 / (1 - NU ** 2), NU))
    D = np.array([Dmat(E_betong * h ** 3 / 12 / (1 - NU ** 2), NU) for h in Pb.h_el])
    Pb.styvhet(D)


def badd(Pb, k_falt, k_balk):
    """Cellplast: k [N/mm³] per element (fördelat på noderna), under tjocka delar (balkar och plintar) k_balk, annars
    k_falt."""
    Pb.springs = {}
    k = np.where(Pb.tjock, k_balk, k_falt)
    kn = np.zeros(Pb.nn)
    for j in range(3):
        np.add.at(kn, Pb.tri[:, j], k * Pb.area / 3)
    for n in range(Pb.nn):
        Pb.springs[3 * n] = kn[n]
    Pb.k_nod = kn                                      # N/mm per nod
    an = np.zeros(Pb.nn)
    for j in range(3):
        np.add.at(an, Pb.tri[:, j], Pb.area / 3)
    Pb.a_nod = an                                      # mm² per nod


# ------------------------------------------------------------------ kopplingar
def _linje_vikter(P, pl):
    """Noderna på linjen pl, sorterade, och deras läge s längs linjen."""
    ls = LineString(pl)
    nod = P.noder_pa_linje(pl)
    s = np.array([ls.project(Point(P.xy[n])) for n in nod])
    o = np.argsort(s)
    return np.array(nod)[o], s[o], ls.length


def kopplingar(Pt, Pb, E_vagg, ds=25.0):
    """Lista (k, [(dof, vikt), ...]) med vikt + för mellanbjälklaget och − för bottenplattan (offset nt).
    Väggarna: betongkärnan (t = T_KARNA) som linjefjäder E·t/h längs K-05:s upplagslinje, kärnans mitt."""
    nt = Pt.ndof
    out = []
    # rör: medelvärdet av noderna i rörets yta (200 × 200, ett dubbelrör över båda rören) i båda plattorna
    for namn, x, y, bx, by, antal in ROR:
        a = Pt.noder_i_rekt(x, y, bx, by)
        b = Pb.noder_i_rekt(x, y, bx, by)
        v = [(3 * n, 1 / len(a)) for n in a] + [(nt + 3 * n, -1 / len(b)) for n in b]
        out.append(dict(typ="rör", namn=namn, k=antal * K_ROR, v=v))
    # väggar: linjefjäder längs K-05:s upplagslinje, interpolerad mellan noderna i båda näten
    kw = E_vagg * I.T_KARNA / I.H_VAGG                 # N/mm per mm
    for i, pl in enumerate(STODLIN):
        nt_, st, L = _linje_vikter(Pt, pl)
        nb_, sb, _ = _linje_vikter(Pb, pl)
        n = max(int(np.ceil(L / ds)), 1)
        for s in (np.arange(n) + 0.5) / n * L:
            v = []
            for nod, ss, off, sg in ((nt_, st, 0, 1.0), (nb_, sb, nt, -1.0)):
                j = int(np.clip(np.searchsorted(ss, s), 1, len(ss) - 1))
                w = (s - ss[j - 1]) / max(ss[j] - ss[j - 1], 1e-9)
                v += [(off + 3 * int(nod[j - 1]), sg * (1 - w)), (off + 3 * int(nod[j]), sg * w)]
            out.append(dict(typ="vägg", namn=f"V{i + 1}", k=kw * L / n, v=v, s=s))
    return out


def kopplingsmatris(kopp, ndof):
    r, c, d = [], [], []
    for kp in kopp:
        idx = np.array([a for a, _ in kp["v"]]); w = np.array([b for _, b in kp["v"]])
        r.append(np.repeat(idx, len(idx))); c.append(np.tile(idx, len(idx))); d.append(kp["k"] * np.outer(w, w).ravel())
    return sp.coo_matrix((np.concatenate(d), (np.concatenate(r), np.concatenate(c))), shape=(ndof, ndof)).tocsr()


def kraft(kp, u):
    """Fjäderkraft (tryck positivt) i en koppling."""
    return kp["k"] * sum(w * u[a] for a, w in kp["v"])


# ------------------------------------------------------------------ laster
SPRIDNING = np.tan(np.radians(30))        # last sprids 60° mot horisontalplanet genom väggen (försiktigt för betong)


def spridd(Pb, x, y, v):
    """Last v [N] som står på en källarvägg i (x, y) sprids genom väggen ned till bottenplattan: jämnt fördelad längs
    väggens centrumlinje inom ±0,58·h från lastens läge (begränsad av väggens ändar och fördelad på alla väggar
    som går genom hörnet)."""
    pt = Point(x, y)
    nara = [LineString(pl) for pl in VAGGLIN if LineString(pl).distance(pt) < 250.0]
    if not nara:
        f = np.zeros(Pb.ndof); f[3 * Pb.nod(x, y)] += v
        return f
    r = SPRIDNING * I.H_VAGG
    delar = []
    for ls in nara:
        s0 = ls.project(pt)
        a, b = max(0.0, s0 - r), min(ls.length, s0 + r)
        if b - a > 1.0:
            delar.append((ls, a, b))
    Ltot = sum(b - a for _, a, b in delar)
    f = np.zeros(Pb.ndof)
    for ls, a, b in delar:
        seg = [ls.interpolate(a).coords[0], ls.interpolate(b).coords[0]]
        fs = Pb.last_linje(1.0, seg)
        f += fs * (v * (b - a) / Ltot) / fs.sum()
    return f


def vaggvikt(i):
    """Väggens egentyngd [N/mm] för vägg i (0-baserat): Kub-väggen i hela höjden och, på ytterväggarna utom V3 och
    V20 (plattan på mark), fasadsten från 50 mm under mark till mellanbjälklagets överkant (AR-01)."""
    namn = f"V{i + 1}"
    q = I.G_KUB * I.H_VAGG / 1000
    if VTYP[i] == "yttre":
        f = next((x for n, x in I.FYLL.items() if n == namn or namn in x.get("fasad", {}).get("omfattar", ())), None)
        if not (f and f.get("platta")):
            hf = min(f["h"]) if f else 0.0
            q += I.G_STEN * max((I.H_VAGG + I.H_MB) / 1000 + 0.05 - hf, 0.0)
    return q


def laster(Pt, Pb):
    """Lastvektorer [N] för hela systemet (mellanbjälklag först, sedan bottenplatta)."""
    nt, nb = Pt.ndof, Pb.ndof
    LASTER = M05.LASTER
    z = lambda: (np.zeros(nt), np.zeros(nb))
    F = {k: z() for k in ("G", "S_V", "S_M", "S_H", "Qb", "W")}

    def punkt(fa, x, y, P_, v, sprid=False):
        if sprid:
            fa += spridd(Pb, x, y, v)
        else:
            fa[3 * P_.nod(x, y)] += v

    # mellanbjälklaget: egentyngd, golv (K-05)
    F["G"][0][:] += Pt.last_yta(M05.GK)
    # punktlaster
    for p in LASTER["punkter"]:
        tb = 1 if p["plats"] == "vägg" else 0
        Pp = Pb if tb else Pt
        punkt(F["G"][tb], p["x"], p["y"], Pp, p["Gk"] * 1e3, tb == 1)
        for kr, v in p["Sb"].items():
            punkt(F["S_" + kr][tb], p["x"], p["y"], Pp, v * 1e3, tb == 1)
        if p["plats"] == "platta":
            punkt(F["W"][0], p["x"], p["y"], Pt, p["Wd"] * 1e3)
    for w in LASTER["vaggar"]:
        for s in w["prov"]:
            tb = 1 if s["plats"] == "vägg" else 0
            Pp = Pb if tb else Pt
            punkt(F["G"][tb], s["x"], s["y"], Pp, s["G"] * 1e3)
            punkt(F["S_" + s["kropp"]][tb], s["x"], s["y"], Pp, s["S"] * 1e3)
    QT = np.zeros(nt)
    for l in LASTER["linjer"]:
        F["G"][0][:] += Pt.last_linje(l["gk"], l["pl"])
        fs = Pt.last_linje(l["sk"], l["pl"])
        for kr, v in l["skropp"].items():
            F["S_" + kr][0][:] += v * fs
        QT += Pt.last_linje(l["qk"], l["pl"])
        F["W"][0][:] += Pt.last_linje(l["wd"], l["pl"])
    # bottenplattan: egentyngd (verklig tjocklek), golv, väggarnas egentyngd och fasadsten, nyttig last i källaren
    fb = np.zeros(nb)
    q_el = 25e-6 * Pb.h_el + 0.5e-3                     # N/mm²
    np.add.at(fb, 3 * Pb.tri.ravel(), np.repeat(q_el * Pb.area / 3, 3))
    for i, pl in enumerate(VAGGLIN):
        fb += Pb.last_linje(vaggvikt(i), pl)
    F["G"][1][:] += fb
    F["Qb"][1][:] += Pb.last_yta(2.7e-3)
    # trappans fot på bottenplattan: halva trappan (K-05: 3,0 × 0,83 m, 1,0 + 2,0 kN/m²) vid hålets mitt
    hx, hy = np.mean(np.array(G["hal"]), axis=0)
    tr = LA05.TRAPPA
    punkt(F["G"][1], hx, hy, Pb, 0.5 * tr["langd"] * tr["bredd"] * tr["g"] * 1e3)
    punkt(F["Qb"][1], hx, hy, Pb, 0.5 * tr["langd"] * tr["bredd"] * tr["q"] * 1e3)
    # nyttig last i fält på mellanbjälklaget (K-05:s mönster), inklusive trappans nyttiga last
    from omhyllande import falt
    polys, monster = falt()
    FQ = []
    for p in polys:
        fq = Pt.last_yta(M05.QK + M05.QV, p)
        inne = MplPath(np.asarray(p, float)).contains_points(Pt.xy)
        fq[0::3] += np.where(inne, QT[0::3], 0.0)
        FQ.append((fq, np.zeros(nb)))
    vec = {k: np.concatenate(v) for k, v in F.items()}
    vec["Q"] = [np.concatenate(v) for v in FQ]
    vec["S"] = vec["S_V"] + vec["S_M"] + vec["S_H"]
    return vec, monster


def svinn(kopp, ndof, eps):
    """Lastvektor för betongkärnans krympning eps (förkortning eps·h) i väggfjädrarna."""
    f = np.zeros(ndof)
    d = eps * I.H_VAGG
    for kp in kopp:
        if kp["typ"] == "vägg":
            for a, w in kp["v"]:
                f[a] += kp["k"] * d * w
    return f


# ------------------------------------------------------------------ system
class System:
    """Hela modellen för ett utförande (L300/L400) och en styvhetsvariant."""

    def __init__(self, utf, plint, eps_falt, eps_balk, variant, hmax=200.0, k_mark=None):
        self.utf = I.UTFORANDEN[utf] if isinstance(utf, str) else utf
        self.Pt = topp(hmax, k_mark)
        self.Pb = botten(self.utf, plint, hmax)
        lang = variant == "lång"
        Ec = B.Ecm / (1 + 2.8) if lang else B.Ecm             # betong: långtid med φ ≈ 2,8 (K-05)
        Ev = BV.Ecm / (1 + I.KRYP_V) if lang else BV.Ecm     # väggarnas kärna, C30/37
        ke = I.EPS_KS if lang else 1.0                         # cellplast: 0,4 E_k långtid, E_k korttid
        Ef, Eb = I.EPS[eps_falt]["Ek"] * 1e-3 * ke, I.EPS[eps_balk]["Ek"] * 1e-3 * ke   # MPa
        badd(self.Pb, Ef / self.utf["t_eps"], Eb / I.T_FOT)                 # före styvheten
        styvheter(self.Pt, self.Pb, Ec)
        self.k_falt, self.k_balk = Ef / self.utf["t_eps"], Eb / I.T_FOT
        self.kopp = kopplingar(self.Pt, self.Pb, Ev)
        nt, nb = self.Pt.ndof, self.Pb.ndof
        self.nt, self.ndof = nt, nt + nb
        K = sp.block_diag([self.Pt.K, self.Pb.K]).tocsr() + kopplingsmatris(self.kopp, self.ndof)
        self.K = K
        self.lu = spla.splu(K.tocsc())
        self.variant, self.eps = variant, (eps_falt, eps_balk)

    def los(self, f):
        return self.lu.solve(f)

    def delar(self, u):
        return u[:self.nt], u[self.nt:]

    def resultat(self, u, f):
        ut, ub = self.delar(u)
        ft, fb = self.delar(f)
        return Resultat(self.Pt, ut, np.zeros_like(ut), ft), Resultat(self.Pb, ub, np.zeros_like(ub), fb)

    def tryck(self, u):
        """Kontakttryck mot cellplasten per nod [kPa] (k_nod · w / nodarea)."""
        ub = u[self.nt:]
        return self.Pb.k_nod * ub[0::3] / self.Pb.a_nod * 1e3

    def krafter(self, u, eps=0.0):
        """Kraft i rör och väggar (tryck positivt). eps: kärnans krympning i lastfallet (fjäderns vilolängd
        är förkortad med eps·h, så kraften är k(Δw − eps·h))."""
        out = {}
        for kp in self.kopp:
            f = kraft(kp, u) - (kp["k"] * eps * I.H_VAGG if kp["typ"] == "vägg" else 0.0)
            out[kp["namn"]] = out.get(kp["namn"], 0.0) + f
        return out


if __name__ == "__main__":
    import time
    utf = sys.argv[1] if len(sys.argv) > 1 else "L300"
    t0 = time.time()
    S_ = System(utf, [1000.0] * len(PEL), I.EPS_FALT, I.EPS_BALK, "lång")
    print(f"topp {S_.Pt.ne} el, botten {S_.Pb.ne} el, dof {S_.ndof}, {time.time() - t0:.0f} s")
    F, mon = laster(S_.Pt, S_.Pb)
    for k in ("G", "S", "Qb"):
        u = S_.los(F[k])
        Rb = (S_.Pb.k_nod * u[S_.nt:][0::3]).sum() + (np.array([S_.Pt.springs.get(3 * n, 0) for n in range(S_.Pt.nn)]) * u[:S_.nt][0::3]).sum()
        print(f"{k}: last {F[k][0::3].sum() / 1e3:7.1f} kN, reaktion {Rb / 1e3:7.1f} kN")
    u = S_.los(F["G"])
    kr = S_.krafter(u)
    print("rör G:", {k: round(v / 1e3, 1) for k, v in kr.items() if k[0] == "P"})
    print("väggar G:", {k: round(v / 1e3, 1) for k, v in kr.items() if k[0] == "V"})
    p = S_.tryck(u)
    print(f"tryck G: max {p.max():.1f} kPa, min {p.min():.1f} kPa")
