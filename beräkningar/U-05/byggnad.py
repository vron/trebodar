"""
U-05: hela huset som ett nät av värmekonduktanser mellan omgivningarna (stationärt).

Omgivningarna: ute (uteluften), mark (markytan, med markens tröghet), kallare (källarens luft), inne (plan 1) och
varme (golvvärmens plan i mellanbjälklaget). Varje element är en konduktans H [W/K] mellan två omgivningar med en
kategori för redovisningen:

- husets nedre del ur 3D-modellen (mark3d.py), kopplingskoefficienterna per par, med 3D-modellens ytor (etiketter);
- skarvarna vid mellanbjälklaget (skarvar.py) gånger längden, per par av omgivningar;
- plan 1:s klimatskärm: väggar, gavelspetsar, tak, fönster, dörrar, takfönster och köldbryggor (U·A och ψ·l);
- källarens fönster och dörr (U·A i stället för väggen i 3D-modellen);
- ventilation och infiltration.

Källarens frånluft (FF3) tas från plan 1 genom trapphålet, så luften värms på plan 1 och för med sig värme ned i
källaren. Genom trapphålet blandas luften också när källaren är varmare än plan 1 (dubbelriktat flöde genom en
vågrät öppning, Epstein); är plan 1 varmare är skiktningen stabil och utbytet litet.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from shapely.geometry import Polygon

import komponenter as K
import skarvar as S

OMG = ("ute", "mark", "kallare", "inne", "varme")
RHO_C = 1200.0                     # luftens värmekapacitet per volym [J/(m³K)]


@dataclass
class Element:
    namn: str
    kategori: str
    a: str
    b: str
    H: float                       # W/K
    A: float = 0.0                 # area [m²] (för U-medel)
    l: float = 0.0                 # längd [m]
    U: float = 0.0
    psi: float = 0.0


def areor(P):
    """Atemp (plan 1 och källaren) och areor ur geometrin [m²]."""
    kontur = Polygon(P["_kontur"])
    plan1 = kontur.buffer(-0.135, join_style=2).area
    from mark3d import HALV, kallarens_kontur
    kall = Polygon(kallarens_kontur()).buffer(-HALV - 0.0125, join_style=2).area
    pm = Polygon(np.array(P["platta_pa_mark"]["kontur"]) / 1000)
    # takfallens planareor ska tillsammans vara plan 1:s invändiga area
    tak_plan = sum(takarea(P, t) for t in P["mangder"]["takfall"]) * math.cos(math.radians(P["tak"]["lutning"]))
    assert abs(tak_plan / plan1 - 1) < 0.005, f"takfallens plan {tak_plan:.2f} m², plan 1 {plan1:.2f} m²"
    return dict(Atemp_plan1=plan1, Atemp_kallare=kall, Atemp=plan1 + kall,
                platta_pa_mark=pm.buffer(0).intersection(kontur.buffer(-0.135, join_style=2)).area,
                kontur_omkrets=kontur.length,
                kallare_omkrets=Polygon(kallarens_kontur()).buffer(-HALV - 0.0125, join_style=2).length)


def langder(P):
    """Skarvarnas längder [m]."""
    kontur = Polygon(P["_kontur"])
    pm = Polygon(np.array(P["platta_pa_mark"]["kontur"]) / 1000)
    kant_pm = kontur.exterior.intersection(pm.exterior.buffer(0.01)).length
    kant = kontur.length
    # hörnen i stommens utsida: konvexa (ytterhörn) och konkava (innerhörn)
    pts = np.array(kontur.exterior.coords)[:-1]
    n = len(pts)
    yttre = inre = 0
    ccw = kontur.exterior.is_ccw
    for i in range(n):
        a, b, c = pts[i - 1], pts[i], pts[(i + 1) % n]
        cr = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
        if (cr > 0) == ccw:
            yttre += 1
        else:
            inre += 1
    kroppar = {k["nr"]: k for k in P["mangder"]["kropp"]}
    hojd = kroppar[1]["z_innertak"] / 1000
    # takfot: långsidorna (invändig längd ≈ stommens längd − 2 × 0,165)
    lage = P["mangder"]["lage"]
    takfot = sum(v["L"] / 1000 - 0.33 for v in lage if v["kod"] in ("1SO", "1NV", "2SO", "2NV", "3NV", "3SO"))
    nock = sum((n_["y"][1] - n_["y"][0]) / 1000 - 0.33 for n_ in P["balkar"]["nockar"])
    dal = sum((d["y"][1] - d["y"][0]) / 1000 - 0.33 for d in P["balkar"]["dalar"])
    # gavlarnas takkanter: två per gavel, innertakets längd från väggen till nocken
    vagg = {v["kod"]: v for v in P["mangder"]["vagg"]}
    gavelkant = sum(2 * kroppar[v["kropp"]]["halvbredd"] / 1000 / math.cos(math.radians(30))
                    for v in vagg.values() if v["gavel"])
    return dict(bjalklagskant=kant, bjalklagskant_pm=kant_pm, bjalklagskant_kallare=kant - kant_pm,
                ytterhorn=yttre * hojd, innerhorn=inre * hojd, n_ytterhorn=yttre, n_innerhorn=inre,
                takfot=takfot, nock=nock, dal=dal, gavelkant=gavelkant)


def takarea(P, t):
    """Takfallets invändiga area i takets lutning [m²], med takfönstren: planarean (rektanglarna från ytterväggens
    insida eller dalens mittlinje till nockens mittlinje) / cos lutningen."""
    plan = sum(abs(x1 - x0) * abs(y1 - y0) for x0, x1, y0, y1 in t["plan"]) / 1e6
    return plan / math.cos(math.radians(P["tak"]["lutning"]))


def gavelspets_area(P, kropp):
    """Gavelspetsens invändiga area ovanför hammarbandet (z > 2 490) under innertaket [m²]."""
    k = {k_["nr"]: k_ for k_ in P["mangder"]["kropp"]}[kropp]
    s = k["halvbredd"] / 1000 - (2.490 - k["z_innertak"] / 1000) / math.tan(math.radians(30))
    return s * s * math.tan(math.radians(30))


def element(P, L3d, omg3d, et3d, skarv, isolerat_inst=None):
    """Alla element. L3d: 3D-modellens kopplingar [k, e, j]; skarv: resultaten ur skarvarna."""
    E = []
    # ---------------------------------------------------------------- husets nedre del (3D), per etikett
    # Konduktansen mellan a och b genom ytan e: flödet in i a vid e när b har 1 K (L3d[a, e, b]). Etiketterna hör
    # till den omgivning vars celler de sitter på; för förlusterna används den inre omgivningens ytor (källarens
    # golv, väggar …), så att förlusten redovisas där den lämnar rummet.
    inre = ("kallare", "inne", "varme")
    for k, a in enumerate(omg3d):
        for j, b in enumerate(omg3d):
            if j == k or (a not in inre and b not in inre):
                continue
            if a in inre and b in inre and j < k:
                continue
            if a not in inre:
                continue
            for e, et in enumerate(et3d):
                H = L3d[k, e, j]
                if abs(H) < 1e-9:
                    continue
                E.append(Element(f"3D {a}–{b} ({et})", _kategori_3d(a, b, et), a, b, H))
    # ---------------------------------------------------------------- skarvarna vid mellanbjälklaget
    Lg = langder(P)
    for typ, l in (("kallare", Lg["bjalklagskant_kallare"]), ("mark", Lg["bjalklagskant_pm"])):
        for par, psi in skarv[f"bjalklag_{typ}"]["psi"].items():
            a, b = par.split("-")
            kat = "Mellanbjälklagets kant" if "ute" in (a, b) or "mark" in (a, b) else "Inre (mellanbjälklagets kant)"
            E.append(Element(f"Bjälklagskant ({'över källarvägg' if typ == 'kallare' else 'platta på mark'}) {par}",
                             kat, a, b, psi * l, l=l, psi=psi))
    # ---------------------------------------------------------------- plan 1:s klimatskärm
    gavelU = {}
    for v in P["mangder"]["vagg"]:
        r = K.vaggtyp_U(P, v["typ"], v["f_tra"], isolerat_inst)
        Ag = gavelspets_area(P, v["kropp"]) if v["gavel"] else 0.0
        E.append(Element(f"Vägg {v['kod']}", "Ytterväggar", "inne", "ute", r["U"] * (v["A"] - Ag), A=v["A"] - Ag,
                         U=r["U"]))
        if Ag:
            key = (v["typ"], P["gavelspets"]["isolerad"])
            if key not in gavelU:
                gavelU[key] = K.gavelspets_U(P, v["typ"], isolerat_inst)["U"]
            E.append(Element(f"Gavelspets {v['kod']}", "Gavelspetsar", "inne", "ute", gavelU[key] * Ag, A=Ag,
                             U=gavelU[key]))
    TF = P["takfonster"]
    A_tf = TF["b"] * TF["h"] / 1e6
    for t in P["mangder"]["takfall"]:
        r = K.tak_U(P, t["f_tra"], isolerat_inst)
        A = takarea(P, t) - t.get("takfonster", 0) * A_tf
        E.append(Element(f"Tak {t['kod']}", "Tak", "inne", "ute", r["U"] * A, A=A, U=r["U"]))
    E.append(Element("Takfönster TF1–TF3", "Takfönster", "inne", "ute", TF["Uw"] * A_tf * TF["antal"],
                     A=A_tf * TF["antal"], U=TF["Uw"]))
    E.append(Element("Takfönstrens anslutning", "Takfönster", "inne", "ute", TF["psi"] * 4 * TF["b"] / 1000 *
                     TF["antal"], l=4 * TF["b"] / 1000 * TF["antal"], psi=TF["psi"]))
    omkrets1 = 0.0
    Akall = 0.0
    for kod, typ, b, h, van, vagg in P["oppningar"]["lista"]:
        f = K.fonster(P, typ, b, h)
        if van == 1:
            kat = "Ytterdörr" if typ == "ytterdörr" else "Fönster och fönsterdörrar"
            E.append(Element(f"{kod} {typ}", kat, "inne", "ute", f["U"] * f["A"], A=f["A"], U=f["U"]))
            omkrets1 += 2 * (f["b"] + f["h"])
        else:
            U_kv = K.skiktat_U(P, P["kallarvagg"]["skikt"], P["ytmotstand"]["Rsi_vagrat"], P["ytmotstand"]["Rse"])
            E.append(Element(f"{kod} {typ} (källaren)", "Källarens fönster och dörr", "kallare", "ute",
                             (f["U"] - U_kv) * f["A"], A=f["A"], U=f["U"]))
            E.append(Element(f"{kod} anslutning", "Källarens fönster och dörr", "kallare", "ute",
                             P["_skarv_kallarfonster"] * 2 * (f["b"] + f["h"]), l=2 * (f["b"] + f["h"]),
                             psi=P["_skarv_kallarfonster"]))
            Akall += f["A"]
    psi_f = skarv["fonster"]["psi"]
    E.append(Element("Fönstrens och dörrarnas anslutning", "Köldbryggor plan 1", "inne", "ute", psi_f * omkrets1,
                     l=omkrets1, psi=psi_f))
    for namn, l, psi in (("Takfot", Lg["takfot"], skarv["takfot"]["psi"]),
                         ("Nock", Lg["nock"], skarv["nock"]["psi"]),
                         ("Dal", Lg["dal"], skarv["dal"]["psi"]),
                         ("Gavelns takkant", Lg["gavelkant"], P["_psi_gavelkant"]),
                         ("Ytterhörn", Lg["ytterhorn"], skarv["horn"]["psi"]),
                         ("Innerhörn", Lg["innerhorn"], P["_psi_innerhorn"])):
        E.append(Element(namn, "Köldbryggor plan 1", "inne", "ute", psi * l, l=l, psi=psi))
    return E


def _kategori_3d(a, b, et):
    par = {a, b}
    ute = "ute" in par or "mark" in par
    if "varme" in par and ute:
        return "Mellanbjälklaget till mark och ute"
    if "kallare" in par and ute:
        return {"källargolv": "Källarens golv", "källartak": "Mellanbjälklagets kant"}.get(et, "Källarens väggar")
    if "inne" in par and ute:
        return "Mellanbjälklagets kant"
    return "Inre"


def ventilation(P, T_e=0.0, vind=4.0, T_i=21.0):
    """Ventilationens och infiltrationens flöden [l/s]: frånluften (FF1–FF3, med köksfläktens forcering som
    medelvärde) och infiltrationen (LBL) ihop kvadratiskt, och källarens frånluft (FF3), som tas från plan 1."""
    V = P["ventilation"]
    forc = (V["FF1_forcerad"] - V["FF1"]) * V["forcering_min"] / (24 * 60)
    q_fr = V["FF1"] + V["FF2"] + V["FF3"] + forc
    q_inf = infiltration(P, T_i - T_e, vind)
    q_tot = math.sqrt(q_fr ** 2 + q_inf ** 2)
    return dict(franluft=q_fr, infiltration_lbl=q_inf, total=q_tot, extra=q_tot - q_fr, kallare=V["FF3"])


def infiltration(P, dT, vind):
    """Infiltrationen [l/s] med LBL-modellen: Q = ELA·√(Cs·|ΔT| + Cw·v²), ELA ur q50 (läckarean vid 4 Pa)."""
    I = P["infiltration"]
    A_om = P["_A_om"]
    Q50 = I["q50"] * A_om / 1000                          # m³/s vid 50 Pa
    Q4 = Q50 * (4 / 50) ** I["n"]
    ELA = Q4 / math.sqrt(2 * 4 / 1.2)                     # m²
    # Cs och Cw i (l/s)²/(cm⁴·K) och (l/s)²/(cm⁴·(m/s)²): Q [l/s] = ELA [cm²] · √(Cs·ΔT + Cw·v²)
    return ELA * 1e4 * math.sqrt(I["Cs"] * abs(dT) + I["Cw"] * vind ** 2)


def trapputbyte(P, T_b, T_i):
    """Luftutbytet genom trapphålet [l/s]: Epsteins samband för en vågrät öppning när luften under är varmare,
    0,055·√(g·ΔT/T·D⁵), D = öppningens hydrauliska diameter, minskat för trappan; annars litet (stabil skiktning)."""
    Tr = P["trapphal"]
    b, l = Tr["b"] / 1000, Tr["l"] / 1000
    D = 4 * b * l / (2 * (b + l))
    dT = T_b - T_i
    if dT <= 0:
        return 0.1 * 0.055 * math.sqrt(9.81 * 0.5 / 293 * D ** 5) * 1000 * Tr["reduktion"]
    return 0.055 * math.sqrt(9.81 * dT / 293 * D ** 5) * 1000 * Tr["reduktion"]


def matris(E, extra=()):
    """Konduktansmatrisen G mellan omgivningarna (symmetrisk, utan diagonal)."""
    G = np.zeros((len(OMG), len(OMG)))
    for e in list(E) + list(extra):
        i, j = OMG.index(e.a), OMG.index(e.b)
        G[i, j] += e.H
        G[j, i] += e.H
    return G


def stationart(P, E, T_e, T_mark, T_i=None, interna=(0.0, 0.0), vind=4.0, ftx=0.0):
    """Stationär värmebalans med rummet på T_i: golvvärmens effekt, golvvärmens och källarens temperaturer och
    flödena per element. interna: (plan 1, källaren) [W]."""
    T_i = P["drift"]["T_inne"] if T_i is None else T_i
    q = ventilation(P, T_e, vind, T_i)
    vent = [Element("Ventilation (frånluft)", "Ventilation", "inne", "ute", RHO_C * q["franluft"] / 1000 * (1 - ftx)),
            Element("Infiltration", "Infiltration", "inne", "ute", RHO_C * q["extra"] / 1000)]
    G = matris(E, vent)
    T_b = T_i
    for _ in range(60):
        q_tr = trapputbyte(P, T_b, T_i)
        H_tr = RHO_C * q_tr / 1000
        H_ff3 = RHO_C * q["kallare"] / 1000              # luften från plan 1 till källaren (FF3)
        # okända: T_h, T_b. Golvvärmens nod: Q_h = Σ G_hj (T_h − T_j); rummet: Σ G_ij (T_j − T_i) + ... = 0
        ih, ib, ii, ie, im = (OMG.index(x) for x in ("varme", "kallare", "inne", "ute", "mark"))
        T = {"ute": T_e, "mark": T_mark, "inne": T_i}
        # rummets balans: G_ih (T_h − T_i) + G_ib (T_b − T_i) + G_ie (T_e − T_i) + G_im (T_m − T_i)
        #                 + H_tr (T_b − T_i) − H_ff3 (T_i − T_i)·0 + interna_i = 0
        # källarens:     G_bh (T_h − T_b) + G_bi (T_i − T_b) + G_be (T_e − T_b) + G_bm (T_m − T_b)
        #                 + H_tr (T_i − T_b) + H_ff3 (T_i − T_b) + interna_b = 0
        A = np.array([[G[ii, ih], G[ii, ib] + H_tr],
                      [G[ib, ih], -(G[ib, ih] + G[ib, ii] + G[ib, ie] + G[ib, im] + H_tr + H_ff3)]])
        r = np.array([G[ii, ih] * 0 + (G[ii, ih] + G[ii, ib] + G[ii, ie] + G[ii, im] + H_tr) * T_i
                      - G[ii, ie] * T_e - G[ii, im] * T_mark - interna[0],
                      -(G[ib, ii] + H_tr + H_ff3) * T_i - G[ib, ie] * T_e - G[ib, im] * T_mark - interna[1]])
        T_h, T_b_ny = np.linalg.solve(A, r)
        if abs(T_b_ny - T_b) < 1e-6:
            T_b = T_b_ny
            break
        T_b = 0.5 * (T_b + T_b_ny)
    T = {"ute": T_e, "mark": T_mark, "inne": T_i, "kallare": T_b, "varme": T_h}
    Q_h = sum(G[ih, j] * (T_h - T[OMG[j]]) for j in range(len(OMG)) if j != ih)
    flod = []
    for e in list(E) + vent:
        flod.append((e, e.H * (T[e.a] - T[e.b])))
    # källarens frånluft (FF3) tas från plan 1 och lämnar huset med källarens temperatur: ventilationen ovan räknar
    # all frånluft med rummets temperatur, och det som källaren värmer luften är en förlust till
    H_ff3 = RHO_C * q["kallare"] / 1000
    flod.append((Element("Källarens frånluft (FF3)", "Ventilation", "kallare", "ute", H_ff3), H_ff3 * (T_b - T_i)))
    return dict(T=T, Q_h=Q_h, flod=flod, q=q, q_trapp=trapputbyte(P, T_b, T_i), H_tr=RHO_C * trapputbyte(P, T_b, T_i) / 1000,
                H_ff3=RHO_C * q["kallare"] / 1000, G=G)


def forluster(res):
    """Förlusterna till ute och mark per kategori [W] (positivt ut ur huset)."""
    ut = {}
    for e, Q in res["flod"]:
        if e.b in ("ute", "mark") and e.a not in ("ute", "mark"):
            q = Q
        elif e.a in ("ute", "mark") and e.b not in ("ute", "mark"):
            q = -Q
        else:
            continue
        ut[e.kategori] = ut.get(e.kategori, 0.0) + q
    return ut


def H_transmission(E):
    """Transmissionsförlustkoefficienten med alla uppvärmda delar på samma temperatur: summan av konduktanserna
    från inne, källaren och golvvärmen till ute och mark [W/K], per kategori."""
    ut = {}
    for e in E:
        inre = {"inne", "kallare", "varme"}
        if (e.a in inre) != (e.b in inre):
            ut[e.kategori] = ut.get(e.kategori, 0.0) + e.H
    return ut
