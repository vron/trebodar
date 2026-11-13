"""
U-05: köldbryggorna i skarvarna, tvådimensionellt enligt SS-EN ISO 10211 med invändiga mått (som Um i BBR).

Varje skarv är ett snitt med finita volymer (fv.py) och snitt 1–1,5 m från skarven (adiabatiska). Regelfacken och
takbalkarnas skikt homogeniseras med λ så att snittets endimensionella U blir byggdelens U ur komponenter.py (λ
genom skiktet; längs väggen λ för virke och isolering parallellt, eftersom reglarna leder i sin längdriktning).
ψ = L2D − Σ U·l, där l är byggdelarnas invändiga längd i snittet.

Skarvarna vid mellanbjälklaget har fyra omgivningar: rummet (i), källaren (b), ute (e) och golvvärmens plan (h, ett
tunt lager i rörens nivå med golvvärmens medeltemperatur). Där ger skarven en kopplingsmatris. Mark, källarväggar och
bjälklag räknas i 3D (mark3d.py); här räknas bara det som 3D-modellen inte har med. Därför räknas varje sådan skarv
två gånger: med alla detaljer, och så som 3D-modellen ser den (plattans kant och ytan under väggen adiabatiska,
ingen vägg ovanför). Skillnaden, minus väggens U·h, är skarvens tillskott ψ_kj per par av omgivningar.
"""
from __future__ import annotations

import math

import numpy as np

from fv import Modell, kanter
from komponenter import gavelspets_U, skikt_lam, tak_U, vaggtyp_U

TAN, COS, SIN = math.tan(math.radians(30)), math.cos(math.radians(30)), math.sin(math.radians(30))


def lam_ekv(U, R_ovrigt, t):
    """λ för ett homogeniserat skikt med tjockleken t [m] så att U blir det givna, när resten av uppbyggnaden
    (med ytmotstånden) har motståndet R_ovrigt."""
    return t / (1 / U - R_ovrigt)


class Vagg:
    """Ytterväggens skikt för snitten: (namn, λ genom, λ längs, w0, w1) med w från stommens utsida inåt [m]."""

    def __init__(self, P, typ="v95", f_tra=0.17, isolerat_inst=None):
        M = P["material"]
        Y = P["ytmotstand"]
        V = P["vaggtyp"][typ]
        r = vaggtyp_U(P, typ, f_tra, isolerat_inst)
        self.U = r["U"]
        t_st = dict(V["skikt"])["stomme"] / 1000
        R_ovr = Y["Rsi_vagrat"] + Y["Rse_ventilerad_vagg"]
        sk = []
        w = 0.0
        for n, t in reversed(V["skikt"]):        # utifrån och in
            t = t / 1000
            if n == "utegips":
                sk.append(("utegips", M["utegips"]["lam"], M["utegips"]["lam"], -t, 0.0))
                R_ovr += t / M["utegips"]["lam"]
                continue
            if n != "stomme":
                lam = skikt_lam(P, n, t * 1000, "vagrat", isolerat_inst)
                R_ovr += t / lam
            sk.append((n, None if n == "stomme" else lam, None, w, w + t))
            w += t
        lam_st = lam_ekv(self.U, R_ovr, t_st)
        lam_par = f_tra * M["tra"]["lam"] + (1 - f_tra) * M["mineralull"]["lam"]
        self.skikt = [(n, lam_st if n == "stomme" else a, lam_par if n == "stomme" else (a if b is None else b), w0, w1)
                      for n, a, b, w0, w1 in sk]
        self.t_stomme = t_st
        self.insida = w                           # insidans yta från stommens utsida
        self.lam_par = lam_par


def _psi(L, omg, ref):
    """ψ_kj = L_kj − referensen för varje par."""
    M = L.sum(axis=1)
    ut = {}
    for k in range(len(omg)):
        for j in range(k + 1, len(omg)):
            ut[f"{omg[k]}-{omg[j]}"] = M[k, j] - ref.get((omg[k], omg[j]), ref.get((omg[j], omg[k]), 0.0))
    return ut


# ------------------------------------------------------------------ mellanbjälklagets kant
def bjalklagskant(P, typ="kallare", detalj=True, vagg_f=0.14, h=None, z_mark=None, isolerat_inst=None):
    """Snitt vinkelrätt mot bjälklagets kant. x utåt från plattans kant (K-05:s kontur), z från bjälklagets
    överkant [m]. typ "kallare": källarväggen under (Sundolitt Kub 350-150, kärnans mitt 145 innanför kanten), 1 m
    av den under bjälklaget, med uteluft utanför (eller mark under z_mark). typ "mark": plattan på mark med L-element
    500, cellplast 350 och marken (2D-modell med 20 m mark åt sidan och nedåt, symmetri mitt i plattan).
    detalj False: som 3D-modellen ser skarven."""
    M = P["material"]
    Y = P["ytmotstand"]
    B = P["bjalklag"]
    h = (h or P["nat"]["h_2d"]) / 1000
    vagg = Vagg(P, "v95", vagg_f, isolerat_inst)
    hb = B["h"] / 1000
    z_ror = -B["ror_z"] / 1000
    x_st = 0.03                                   # stommens utsida 30 mm utanför plattans kant
    x_in = x_st - vagg.insida                     # väggens insida
    H_vagg = 1.2
    if typ == "kallare":
        L_in = 2.5
        zb = -hb - 1.0
        bx = [-L_in, x_in, x_in - B["marginal"] / 1000, x_st - vagg.t_stomme, -0.32 - 0.0125, -0.32, -0.22, -0.07,
              0.0, x_st, x_st + 0.01, x_st + 0.2]
        bz = [zb, -hb, z_ror - 0.002, z_ror + 0.002, 0.0, 0.045, H_vagg, H_vagg + h]
        if z_mark is not None:
            bz.append(z_mark)
        fina = [(-0.6, x_st + 0.1, h)]
        ex = kanter(bx, fina=fina, h_max=0.05, tillvaxt=0.25)
        ez = kanter(bz, fina=[(-hb - 0.3, 0.3, h)], h_max=0.05, tillvaxt=0.25)
        m = Modell([ex, ez])
        m.lada("betong", M["betong"]["lam"], (-L_in, -hb), (0.0, 0.0))
        m.lada("eps", M["eps"]["lam"], (0.0, -hb), (x_st, 0.0))                       # kantisoleringen 30
        m.lada("eps", M["eps"]["lam"], (-0.32, zb), (-0.22, -hb))                     # Kub: cellplast inne
        m.lada("betong", M["betong"]["lam"], (-0.22, zb), (-0.07, -hb))               # kärnan
        m.lada("eps_mark", M["eps_mark"]["lam"], (-0.07, zb), (x_st, -hb))            # cellplast ute
        m.lada("gips", M["gips"]["lam"], (-0.3325, zb), (-0.32, -hb))
        # källaren och utsidan
        m.tom("kallare", (-L_in - 1, zb - 1), (-0.3325, -hb), Rs=Y["Rsi_vagrat"], etikett="källarvägg")
        m.tom("kallare", (-L_in - 1, -hb - 2 * h), (-0.3325 - 2 * h, -hb), Rs=Y["Rsi_nedat"], etikett="källartak")
        m.tom("ute", (x_st, zb - 1), (2, -hb), Rs=Y["Rse"], etikett="källarvägg ute")
        if z_mark is not None:
            m.tom(None, (x_st, zb - 1), (2, z_mark))                                 # marken: adiabatiskt (3D)
    else:
        L_in = 2.155                              # halva vänstra huskroppens bredd: symmetri mitt i plattan
        PM = P["platta_pa_mark"]
        zi = -hb - (PM["eps"]) / 1000             # cellplastens underkant
        zm = zi - PM["makadam"] / 1000
        z_mark = -0.40 if z_mark is None else z_mark
        D = 20.0
        bx = [-L_in, x_in, x_in - B["marginal"] / 1000, x_st - vagg.t_stomme, 0.0, x_st - 0.1, x_st, x_st + 0.01,
              x_st + 0.1, x_st + 0.2, x_st + D]
        bz = [zm - D, zm, zi, zi + 0.1, -hb, z_ror - 0.002, z_ror + 0.002, 0.0, 0.045, z_mark, H_vagg, H_vagg + h]
        ex = kanter(bx, fina=[(-0.5, x_st + 0.25, h)], h_max=1.5, tillvaxt=0.25)
        ez = kanter(bz, fina=[(zi - 0.1, 0.25, h), (z_mark - 0.05, z_mark + 0.05, h)], h_max=1.5, tillvaxt=0.25)
        m = Modell([ex, ez])
        m.lada("fyllning", M["fyllning"]["lam"], (-L_in, zm - D), (x_st + D, z_mark))
        m.lada("makadam", M["makadam"]["lam"], (-L_in, zm), (x_st + 0.1, zi))
        m.lada("eps_mark", M["eps_mark"]["lam"], (-L_in, zi), (x_st, -hb))
        # L-elementets rygg 100 ut till stommens utsida; den översta delen (plattans tjocklek) bara 30 (RYGG_KVAR)
        m.lada("eps_mark", M["eps_mark"]["lam"], (x_st - 0.1, zi), (x_st, -hb))
        m.lada("betong", M["betong"]["lam"], (-L_in, -hb), (0.0, 0.0))
        m.lada("eps", M["eps"]["lam"], (0.0, -hb), (x_st, 0.0))
        m.tom("ute", (x_st, z_mark), (x_st + D + 1, 0.0), Rs=Y["Rse"], etikett="markyta")
        # fasaden går ned till marken: L-elementets rygg och plattans kant ligger bakom panelens luftspalt
        m.tom("ute", (x_st, z_mark), (x_st + 0.01, -hb), Rs=Y["Rse_ventilerad_vagg"], etikett="sockel")
        m.tom("ute", (x_st, -hb), (x_st + 0.01, 0.0), Rs=Y["Rse_ventilerad_vagg"], etikett="kant ute")
    # golvvärmens plan
    x_v = x_in - B["marginal"] / 1000
    m.tom("varme", (-L_in - 1, z_ror - 0.002), (x_v, z_ror + 0.002), Rs=0.0, etikett="golvvärme")
    # rummet och väggen ovanför
    if detalj:
        m.tom("inne", (-L_in - 1, 0.0), (x_in, H_vagg), Rs=P["ytmotstand"]["R_golvvarme"], etikett="golv")
        m.tom("inne", (x_in - 2 * h, 0.0 + 2 * h), (x_in, H_vagg), Rs=Y["Rsi_vagrat"], etikett="vägg")
        for n, lam, lam_p, w0, w1 in vagg.skikt:
            a, b = sorted((x_st - w0, x_st - w1))
            lo = (a, 0.045 if n == "stomme" else 0.0)
            m.lada(f"v_{n}", (lam, lam_p), lo, (b, H_vagg))
        m.lada("tra", M["tra"]["lam"], (x_st - vagg.t_stomme, 0.0), (x_st, 0.045))   # syllen
        m.tom("ute", (x_st + 0.01, 0.0), (x_st + 1, H_vagg), Rs=Y["Rse_ventilerad_vagg"], etikett="vägg ute")
        if typ == "kallare":
            # fasaden (panel och läkt) täcker plattans kant: ventilerad spalt utanför kantisoleringen
            m.tom("ute", (x_st, -hb), (x_st + 1, 0.0), Rs=Y["Rse_ventilerad_vagg"], etikett="kant ute")
        m.tom(None, (x_in, H_vagg), (x_st + 1, H_vagg + 1))
    else:
        m.tom("inne", (-L_in - 1, 0.0), (x_in, H_vagg + 1), Rs=P["ytmotstand"]["R_golvvarme"], etikett="golv")
        m.tom(None, (x_in, 0.0), (x_st + 1, H_vagg + 1))
        m.tom(None, (0.0, -hb), (x_st + 1, 0.0))
    m.bygg()
    L = m.koppling()
    return dict(L=L, omg=list(m.omgivningar), etik=list(m.etiketter), modell=m, x_in=x_in, U_vagg=vagg.U,
                H_vagg=H_vagg)


def bjalklagskant_psi(P, typ="kallare", **kw):
    """ψ_kj för bjälklagets kant: detaljerad skarv − 3D-modellens bild av den − väggens U·h."""
    d = bjalklagskant(P, typ, True, **kw)
    r = bjalklagskant(P, typ, False, **kw)
    omg = sorted(set(d["omg"]) | set(r["omg"]))
    def M(x):
        S = x["L"].sum(axis=1)
        o = x["omg"]
        return {(a, b): S[o.index(a), o.index(b)] for a in o for b in o if a != b}
    Md, Mr = M(d), M(r)
    psi = {}
    for i, a in enumerate(omg):
        for b in omg[i + 1:]:
            v = Md.get((a, b), 0.0) - Mr.get((a, b), 0.0)
            if {a, b} == {"inne", "ute"}:
                v -= d["U_vagg"] * d["H_vagg"]
            psi[f"{a}-{b}"] = v
    # flödet genom kantisoleringen (30 mm cellplast utanför betongens kant) ut till spalten bakom fasaden, per m och
    # omgivning: kant[j] = flödet ut när omgivning j har 1 K och de andra 0 K
    m = d["modell"]
    k, e = m.omgivningar.index("ute"), m.etiketter.index("kant ute")
    kant = {o: float(d["L"][k, e, j]) for j, o in enumerate(m.omgivningar)}
    return dict(psi=psi, detalj=d, repr=r, kant=kant)


# ------------------------------------------------------------------ takfoten
def takfot(P, vagg_f=0.14, tak_f=0.08, h=None, isolerat_inst=None):
    """Snitt genom takfoten vinkelrätt mot ytterväggen (som 3NV): x inåt från stommens utsida, z från bjälklagets
    överkant [m]. Väggens skikt och takets skikt homogeniserade; hammarbandet 45, takbalkarna på hammarbandet,
    isolerstoppet 45 i väggens liv, isoleringen i facket ovanför hammarbandet, innertaket under takbalkarna."""
    M = P["material"]
    Y = P["ytmotstand"]
    h = (h or P["nat"]["h_2d"]) / 1000
    vagg = Vagg(P, "v95", vagg_f, isolerat_inst)
    rt = tak_U(P, tak_f, isolerat_inst)
    T = P["tak"]
    sk = dict(T["skikt"])
    t_balk = sk["stomme"] / 1000
    t_hb = sk["hardboard"] / 1000
    t_inst = sk["installation"] / 1000
    t_gips = sk["gips"] / 1000
    lam_inst = skikt_lam(P, "installation", t_inst * 1000, "uppat", isolerat_inst)
    R_ovr = Y["Rsi_uppat"] + Y["Rse_ventilerad_tak"] + t_hb / M["hardboard"]["lam"] + t_inst / lam_inst + \
        t_gips / M["gips"]["lam"]
    lam_tak = lam_ekv(rt["U"], R_ovr, t_balk)
    H_VAGG, UTSPRANG = 2.490, 0.070
    # takbalkens underkant: 10 mm över hammarbandet vid stommens insida (TAKLYFT, modellen: z 2 500 vid väggens
    # x_insida) och stigande inåt; takbalkarnas ände UTSPRANG utanför panelen
    x0 = -0.065 - UTSPRANG
    Lx = 1.6
    z_cut = 1.3
    t_st = vagg.t_stomme

    def zu(x):
        return H_VAGG + 0.010 + (x - t_st) * TAN
    zt = lambda x: zu(x) + t_balk / COS
    x_ins = vagg.insida
    bx = [x0 - 0.3, x0, -0.010, 0.0, 0.045, vagg.t_stomme, x_ins, Lx]
    bz = [z_cut, H_VAGG - 0.045, H_VAGG, zt(Lx) + 0.4]
    ex = kanter(bx, fina=[(bx[0], Lx, h)], h_max=h)
    ez = kanter(bz, fina=[(H_VAGG - 0.4, bz[-1], h)], h_max=0.03, tillvaxt=0.25)
    m = Modell([ex, ez])
    # väggen
    for n, lam, lam_p, w0, w1 in vagg.skikt:
        a, b = (w0, w1) if w1 > w0 else (w1, w0)
        m.lada(f"v_{n}", (lam, lam_p), (a, z_cut), (b, H_VAGG - 0.045 if n == "stomme" else zu(b) - 0.0))
    m.lada("tra", M["tra"]["lam"], (0.0, H_VAGG - 0.045), (vagg.t_stomme, H_VAGG))          # hammarbandet
    # taket: polygoner längs takfallet (x inåt, z uppåt)
    x1 = Lx + 0.5
    def band(z0f, z1f, xa, xb):
        return [(xa, z0f(xa)), (xb, z0f(xb)), (xb, z1f(xb)), (xa, z1f(xa))]
    m.polygon("tak_balkar", lam_tak, band(lambda x: zu(x), lambda x: zt(x), 0.045, x1))
    # isolerstoppet 45 i väggens liv (vid stommens utsida), upp till takbalkarnas överkant
    m.polygon("isolerstopp", M["tra"]["lam"], band(lambda x: H_VAGG, lambda x: zt(x), 0.0, 0.045))
    m.polygon("tak_balkar", lam_tak, band(lambda x: H_VAGG, lambda x: zt(x), 0.045, vagg.t_stomme))
    m.polygon("hardboard", M["hardboard"]["lam"], band(lambda x: zt(x), lambda x: zt(x) + t_hb / COS, 0.0, x1))
    # insidan under takbalkarna: installationsskikt och gips, från väggens insida
    zi1 = lambda x: zu(x)
    zi0 = lambda x: zu(x) - t_inst / COS
    zg0 = lambda x: zu(x) - (t_inst + t_gips) / COS
    m.polygon("t_inst", lam_inst, band(zi0, zi1, vagg.t_stomme, x1))
    m.polygon("gips", M["gips"]["lam"], band(zg0, zi0, x_ins - 0.0, x1))
    # rummet
    from matplotlib.path import Path
    X, Z = np.meshgrid(*m.mitt, indexing="ij")
    tom = m.mat < 0
    rum = tom & (X > x_ins) & (Z < zg0(X))
    m.tom_mask(rum, "inne", Rs=Y["Rsi_uppat"], etikett="tak")
    vagg_inne = tom & (X > x_ins) & (X < x_ins + 2 * h) & (Z < zg0(X) - 0.05)
    m.tom_mask(vagg_inne, "inne", Rs=Y["Rsi_vagrat"], etikett="vägg")
    ute = tom & ~rum & ~vagg_inne
    m.tom_mask(ute & (X < 0.0) & (Z < H_VAGG - 0.06), "ute", Rs=Y["Rse_ventilerad_vagg"], etikett="vägg ute")
    m.tom_mask(ute & ((X >= 0.0) | (Z >= H_VAGG - 0.06)), "ute", Rs=Y["Rse_ventilerad_tak"], etikett="tak ute")
    m.bygg()
    L = m.koppling()
    Q = L.sum(axis=1)[m.omgivningar.index("ute"), m.omgivningar.index("inne")]
    # invändiga längder: väggens insida från snittet till innertaket, innertakets längd från väggens insida
    z_tak_vagg = zg0(x_ins)
    l_vagg = z_tak_vagg - z_cut
    l_tak = (Lx - x_ins) / COS
    psi = Q - vagg.U * l_vagg - rt["U"] * l_tak
    return dict(psi=psi, L2D=Q, l_vagg=l_vagg, l_tak=l_tak, U_vagg=vagg.U, U_tak=rt["U"], modell=m,
                z_innertak_vid_vagg=z_tak_vagg)


# ------------------------------------------------------------------ nock och dal
def nock_dal(P, slag="nock", tak_f=0.08, h=None, plat=True, isolerat_inst=None):
    """Snitt genom nock- eller dalbalken vinkelrätt mot den, symmetri i balkens mitt: x från balkens mitt [m], z
    från takbalkens underkant vid balkens sida. Balken 190 × 200 (limträ 180 och stålplåt 10 över och under, där
    plåtarna finns). Nockbalkens överkant ligger i takbalkarnas överkant vid balkens sida, dalbalkens där takfallens
    vindskydd möts över balkens mitt (modellen). Upplagsregeln 45 × 45 sitter mot balkens sida i takbalkarnas
    underkant, och ovanför den går takets isolering fram till balken. Vindskyddet (hård träfiberskiva) går obrutet
    över balken, med nockregeln (dalreglarna) och slutna luftrum mellan skivan och balken. Innertakets gips följer
    takfallen in under balken och möts i en skarp linje under balkens mitt; installationsskiktet slutar vid
    nockbalkens sida och vid dalbalkens upplagsregel, och under balken är det luft."""
    M = P["material"]
    Y = P["ytmotstand"]
    Bk = P["balkar"]
    h = (h or P["nat"]["h_2d"]) / 1000
    rt = tak_U(P, tak_f, isolerat_inst)
    sk = dict(P["tak"]["skikt"])
    t_balk, t_hb = sk["stomme"] / 1000, sk["hardboard"] / 1000
    t_inst, t_gips = sk["installation"] / 1000, sk["gips"] / 1000
    lam_inst = skikt_lam(P, "installation", t_inst * 1000, "uppat", isolerat_inst)
    R_ovr = Y["Rsi_uppat"] + Y["Rse_ventilerad_tak"] + t_hb / M["hardboard"]["lam"] + t_inst / lam_inst + \
        t_gips / M["gips"]["lam"]
    lam_tak = lam_ekv(rt["U"], R_ovr, t_balk)
    b2 = Bk["b"] / 2000
    hB = Bk["h"] / 1000
    tp = Bk["plat_t"] / 1000
    ub = Bk["upplag_b"] / 1000
    s = 1 if slag == "nock" else -1               # nock: taket faller utåt (z minskar med x); dal: stiger
    Lx = 1.3
    zu = lambda x: -s * (x - b2) * TAN            # takbalkarnas underkant
    zt = lambda x: zu(x) + t_balk / COS           # takbalkarnas överkant (vindskyddets undersida)
    zi0 = lambda x: zu(x) - t_inst / COS          # gipsens översida
    zg0 = lambda x: zu(x) - (t_inst + t_gips) / COS
    zb1 = zt(b2) if slag == "nock" else zt(0.0)
    zb0 = zb1 - hB
    z_lo = min(zb0, zg0(0.0), zg0(Lx)) - 0.15
    z_hi = max(zb1, zt(0.0), zt(Lx)) + t_hb / COS + 0.15
    b_regel = ub / 2 if slag == "nock" else ub    # nockregeln (halva, i mitten) eller dalregeln (vid balkens kant)
    bx = [0.0, b_regel if slag == "nock" else b2 - b_regel, b2, b2 + ub, Lx]
    bz = [z_lo, zb0, zb0 + tp, zb1 - tp, zb1, z_hi]
    ex = kanter(bx, fina=[(0.0, Lx, h)], h_max=h)
    ez = kanter(bz, fina=[(z_lo, z_hi, h)], h_max=h)
    m = Modell([ex, ez])
    x1 = Lx + 0.5

    def band(z0f, z1f, xa, xb):
        return [(xa, z0f(xa)), (xb, z0f(xb)), (xb, z1f(xb)), (xa, z1f(xa))]
    m.polygon("tak_balkar", lam_tak, band(zu, zt, b2, x1))
    m.polygon("upplag", M["tra"]["lam"], band(zu, lambda x: zu(x) + ub, b2, b2 + ub))
    # installationsskiktet slutar vid nockbalkens sida och vid dalbalkens upplagsregel (modellen); under balken är
    # det luft mellan gipsen och balken
    x_inst = b2 if slag == "nock" else b2 + ub
    m.polygon("t_inst", lam_inst, band(zi0, zu, x_inst, x1))
    m.lada("limtra", M["limtra"]["lam"], (0.0, zb0), (b2, zb1))
    if plat:
        m.lada("stal", M["stal"]["lam"], (0.0, zb0), (b2, zb0 + tp))
        m.lada("stal", M["stal"]["lam"], (0.0, zb1 - tp), (b2, zb1))
    m.polygon("hardboard", M["hardboard"]["lam"], band(zt, lambda x: zt(x) + t_hb / COS, 0.0, x1))
    xr = (0.0, b_regel) if slag == "nock" else (b2 - b_regel, b2)
    m.polygon("regel", M["tra"]["lam"], band(lambda x: zb1, zt, *xr))
    m.polygon("gips", M["gips"]["lam"], band(zg0, zi0, 0.0, x1))
    X, Z = np.meshgrid(*m.mitt, indexing="ij")
    tom = m.mat < 0
    # slutna luftrum vid balken: mellan vindskyddet och balkens överkant och, där installationsskiktet inte når
    # upp, under balken
    luft = tom & (X < x_inst) & (Z > zg0(X)) & (Z < zt(X))
    m.mat[luft] = m.nytt_material("luft", P["luftskikt"]["d"][5] / 1000 / P["luftskikt"]["R_uppat"][5])
    tom = m.mat < 0
    m.tom_mask(tom & (Z < zg0(X) + 1e-9), "inne", Rs=Y["Rsi_uppat"], etikett="tak")
    m.tom_mask(tom & ~(Z < zg0(X) + 1e-9), "ute", Rs=Y["Rse_ventilerad_tak"], etikett="tak ute")
    m.bygg()
    L = m.koppling()
    Q = L.sum(axis=1)[m.omgivningar.index("ute"), m.omgivningar.index("inne")]
    l_tak = Lx / COS                               # innertakets längd från nockens (dalens) linje, halva snittet
    psi = 2 * (Q - rt["U"] * l_tak)               # hela skarven (två halvor)
    return dict(psi=psi, L2D=2 * Q, U_tak=rt["U"], modell=m)


# ------------------------------------------------------------------ fönstrets anslutning
def _fonstersnitt(P, vagg, lam_f, h):
    """Snittet genom fönstrets sidokarm, med väggen (Vagg) eller fönstret ensamt (vagg None: karmens sida mot väggen
    adiabatisk, som när Uf bestäms enligt SS-EN ISO 10077-2). Returnerar flödet inne–ute [W/(m·K)] och modellen."""
    M = P["material"]
    Y = P["ytmotstand"]
    V = P["velfac"]
    d_karm = 0.149
    x_alu = -0.065 + 0.020                       # aluminiumets utsida (panelens utsida −65, indrag 20)
    x_karm_in = x_alu + d_karm
    s = V["siktlinje"] / 1000
    fog = P["oppningar"]["fog"] / 1000
    d_glas = 0.048
    lam_g = d_glas / (1 / V["Ug"] - Y["Rsi_vagrat"] - Y["Rse"])
    x_glas0 = x_alu + 0.010
    Lw, Lg = FONSTER_LW, FONSTER_LG
    y_karm = -fog                                 # karmens ytterkant
    t_st, x_ins = (vagg.t_stomme, vagg.insida) if vagg else (0.095, 0.165)
    # alla lådornas kanter är brytpunkter, så att geometrin inte flyttar sig med nätet
    bx = [x_alu - 0.2, -0.065, x_alu, x_alu + 0.035, x_glas0, x_glas0 + d_glas, 0.0, t_st, x_karm_in, x_ins,
          x_ins + 0.2] + ([w for *_, w0, w1 in vagg.skikt for w in (w0, w1)] if vagg else [])
    by = [-fog - s - Lg, y_karm - s, y_karm, 0.0, Lw]
    ex = kanter(bx, fina=[(bx[0], bx[-1], h)], h_max=0.01)
    ey = kanter(by, fina=[(y_karm - s - 0.05, 0.2, h)], h_max=0.03, tillvaxt=0.25)
    m = Modell([ex, ey])
    if vagg:
        for n, lam, lam_p, w0, w1 in vagg.skikt:
            a, b = (w0, w1) if w1 > w0 else (w1, w0)
            m.lada(f"v_{n}", (lam, lam_p), (a, 0.0), (b, Lw))
        m.lada("drev", 0.040, (x_alu + 0.035, y_karm), (x_karm_in, 0.0))                   # fogen, mineralull
        m.lada("smyg", M["tra"]["lam"], (t_st, y_karm), (x_ins, 0.0))                       # smygen (trä)
    m.lada("karm", lam_f, (x_alu, y_karm - s), (x_karm_in, y_karm))
    m.lada("glas", lam_g, (x_glas0, -fog - s - Lg), (x_glas0 + d_glas, y_karm - s))
    X, Y_ = np.meshgrid(*m.mitt, indexing="ij")
    tom = m.mat < 0
    # fönstrets insida: karmens insida och, innanför siktlinjen, glaset (med karmens sida mot glaset)
    inne_f = (Y_ < y_karm) & ((X > x_karm_in - 1e-9) | ((Y_ < y_karm - s) & (X > x_glas0 + d_glas - 1e-9)))
    if vagg:
        inne = tom & ((X > x_ins) | inne_f)
        m.tom_mask(inne, "inne", Rs=Y["Rsi_vagrat"])
        ute_v = tom & ~inne & (X < -0.010) & (Y_ > 0.0)
        m.tom_mask(ute_v, "ute", Rs=Y["Rse_ventilerad_vagg"], etikett="vägg ute")
        m.tom_mask(tom & ~inne & ~ute_v, "ute", Rs=Y["Rse"], etikett="fönster ute")
    else:
        m.tom_mask(tom & inne_f, "inne", Rs=Y["Rsi_vagrat"])
        m.tom_mask(tom & ~inne_f & (Y_ < y_karm), "ute", Rs=Y["Rse"], etikett="fönster ute")
    m.bygg()
    L = m.koppling()
    return float(L.sum(axis=1)[m.omgivningar.index("ute"), m.omgivningar.index("inne")]), m


FONSTER_LW, FONSTER_LG = 1.2, 0.4                 # väggens och glasets längd i snittet [m]
_KARM_LAM = {}


def karmens_lambda(P, h):
    """λ för blocket som ersätter karmen (149 × siktlinjen): bestämt så att fönstret ensamt i snittet ger precis
    Uf · siktlinjen + Ug · glasets längd. Ett block med λ ur den endimensionella formeln leder för mycket: karmens
    sida mot glaset är också en yta mot rummet, och det ingår redan i Uf."""
    from scipy.optimize import brentq
    from komponenter import velfac_Uf
    V, Y = P["velfac"], P["ytmotstand"]
    nyckel = (round(h, 6), V["Ug"], V["psi_g"], V["Uw_ref"], V["siktlinje"])
    if nyckel not in _KARM_LAM:
        mal = velfac_Uf(P) * V["siktlinje"] / 1000 + V["Ug"] * FONSTER_LG
        lam_1d = 0.149 / (1 / velfac_Uf(P) - Y["Rsi_vagrat"] - Y["Rse"])
        _KARM_LAM[nyckel] = brentq(lambda lam: _fonstersnitt(P, None, lam, h)[0] - mal, 0.02, lam_1d, xtol=1e-5)
    return _KARM_LAM[nyckel]


def fonsteranslutning(P, vagg_f=0.14, h=None, isolerat_inst=None):
    """Vågrätt snitt genom fönstrets sidokarm (VELFAC 200): x genom väggen från stommens utsida inåt [m], y längs
    väggen från regelverkets öppning (y < 0 öppningen) [m]. Karmen 149 djup med aluminiumet 20 mm innanför panelens
    utsida, 15 mm fog (drevning) mot karmreglarna, smyg av trä invändigt. Karmen ersätts av ett block med λ så att
    fönstret ensamt ger Uf (karmens_lambda), glaset av en skiva med Ug. Karmreglarna ritas inte för sig: deras
    virke ingår i väggens virkesandel (mätt i modellen) och därmed i väggens U. ψ = snittet − väggens U · längden −
    fönstret ensamt."""
    from komponenter import velfac_Uf
    V = P["velfac"]
    h = (h or P["nat"]["h_2d"]) / 1000
    vagg = Vagg(P, "v95", vagg_f, isolerat_inst)
    Uf = velfac_Uf(P)
    lam_f = karmens_lambda(P, h)
    Q, m = _fonstersnitt(P, vagg, lam_f, h)
    psi = Q - vagg.U * FONSTER_LW - Uf * V["siktlinje"] / 1000 - V["Ug"] * FONSTER_LG
    return dict(psi=psi, L2D=Q, U_vagg=vagg.U, Uf=Uf, lam_karm=lam_f, modell=m)


# ------------------------------------------------------------------ hörn
def horn(P, vagg_f=0.14, h=None, isolerat_inst=None, inre=False):
    """Vågrätt snitt genom ett hörn mellan två väggar 45×95. Ytterhörn: rummet i kvadranten innanför båda väggarna;
    innerhörn (där huskropparna möts): rummet runt hörnet på tre sidor. Hörnstolparna ritas inte för sig: deras
    virke ingår i väggarnas virkesandel (mätt i modellen) och därmed i väggens U. Invändiga mått: väggarnas längd
    till hörnet på insidan."""
    M = P["material"]
    Y = P["ytmotstand"]
    h = (h or P["nat"]["h_2d"]) / 1000
    vagg = Vagg(P, "v95", vagg_f, isolerat_inst)
    Lw = 1.2
    t_ut = 0.010
    D = vagg.insida
    T = t_ut + D                                   # hela väggen med utegipsen
    if not inre:
        # ytterhörn: stommens utsida i x = 0 och y = 0, insidan i D
        bx = [-t_ut - 0.1, -t_ut, 0.0, vagg.t_stomme, vagg.t_stomme + 0.045, D, Lw] + \
            [w for *_, w0, w1 in vagg.skikt for w in (w0, w1)]
        ex = kanter(bx, fina=[(-0.12, 0.4, h)], h_max=0.03, tillvaxt=0.25)
        m = Modell([ex, ex.copy()])
        for n, lam, lam_p, w0, w1 in vagg.skikt:
            a, b = (w0, w1) if w1 > w0 else (w1, w0)
            m.lada(f"a_{n}", (lam, lam_p), (a, a), (b, Lw))
            m.lada(f"b_{n}", (lam_p, lam), (a, a), (Lw, b))
        X, Y_ = np.meshgrid(*m.mitt, indexing="ij")
        tom = m.mat < 0
        m.tom_mask(tom & (X > D) & (Y_ > D), "inne", Rs=Y["Rsi_vagrat"])
        m.tom_mask(tom & ~((X > D) & (Y_ > D)), "ute", Rs=Y["Rse_ventilerad_vagg"])
        l_int = 2 * (Lw - D)
    else:
        # innerhörn: väggarnas insida i x = 0 och y = 0, väggarna längs +y och +x; rummet x < 0 eller y < 0
        # (tre kvadranter), ute x > T och y > T
        bx = [-0.1, 0.0, D - vagg.t_stomme, D, D + 0.045, T, T + Lw] + [D - w for *_, w0, w1 in vagg.skikt for w in (w0, w1)]
        ex = kanter(bx, fina=[(-0.1, T + 0.4, h)], h_max=0.03, tillvaxt=0.25)
        m = Modell([ex, ex.copy()])
        for n, lam, lam_p, w0, w1 in vagg.skikt:
            a, b = sorted((D - w0, D - w1))
            m.lada(f"a_{n}", (lam, lam_p), (a, 0.0), (b, T + Lw))
            m.lada(f"b_{n}", (lam_p, lam), (0.0, a), (T + Lw, b))
        X, Y_ = np.meshgrid(*m.mitt, indexing="ij")
        tom = m.mat < 0
        m.tom_mask(tom & ((X < 0) | (Y_ < 0)), "inne", Rs=Y["Rsi_vagrat"])
        m.tom_mask(tom & (X > 0) & (Y_ > 0), "ute", Rs=Y["Rse_ventilerad_vagg"])
        l_int = 2 * (T + Lw)
    m.bygg()
    L = m.koppling()
    Q = L.sum(axis=1)[m.omgivningar.index("ute"), m.omgivningar.index("inne")]
    psi = Q - vagg.U * l_int
    return dict(psi=psi, L2D=Q, U_vagg=vagg.U, modell=m)
