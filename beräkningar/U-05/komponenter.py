"""
U-05: byggdelarnas U-värden.

Väggarna och taket räknas i ett tvådimensionellt snitt vinkelrätt mot reglarna (takbalkarna), en halv period c/c 600
med symmetri i regelns mitt och mitt i facket, med finita volymer (fv.py). Virkesandelen i regelfacken är mätt i
modellen per vägg (reglar, karmreglar, hörnstolpar, kortlingar); i snittet samlas allt virke i regeln, som får
bredden andelen × 600. Installationsskiktet (liggande läkt 45×45 c/c 600 och luft) och andra skikt med virke som
löper vinkelrätt mot snittet homogeniseras med parallella vägar. Som kontroll räknas övre och undre gränsen enligt
SS-EN ISO 6946 (6.7.2): det tvådimensionella värdet ska ligga mellan dem.

Fönstren räknas enligt SS-EN ISO 10077-1 med ram, glas och glaskantens ψ.
"""
from __future__ import annotations

import numpy as np

from fv import Modell, kanter


def luftskikt_R(P, d_mm, riktning="vagrat"):
    """R för ett slutet luftskikt (ISO 6946 tabell 8, ε = 0,9), interpolerat i tjockleken."""
    L = P["luftskikt"]
    return float(np.interp(d_mm, L["d"], L[f"R_{riktning}"]))


def skikt_lam(P, namn, t_mm, riktning="vagrat", isolerat=None):
    """λ för ett homogent skikt eller ett homogeniserat installationsskikt (läkt och luft eller isolering;
    isolerat=None: som i indata, installation.isolerad i väggarna och tak.installation_isolerad i innertaket,
    riktning "uppat", där läkten också ligger tätare)."""
    M = P["material"]
    if namn == "installation":
        I = P["installation"]
        if isolerat is None:
            isolerat = P["tak"]["installation_isolerad"] if riktning == "uppat" else I["isolerad"]
        f = I["lakt_b"] / (P["tak"]["lakt_cc"] if riktning == "uppat" else I["lakt_cc"])
        lam_luft = (M["mineralull"]["lam"] if isolerat else t_mm / 1000 / luftskikt_R(P, t_mm, riktning))
        return f * M["tra"]["lam"] + (1 - f) * lam_luft
    return M[namn]["lam"]


def snitt(P, skikt, f_tra, isolering, Rsi, Rse, regel_cc=600.0, riktning="vagrat", isolerat_inst=None,
          h=1.0, fack_luft=False):
    """U-värdet [W/m²K] för en regelvägg eller ett tak i 2D (halv period) och ISO 6946:s gränser.
    skikt: [(namn, t_mm)] inifrån, där "stomme" är regelfacket (virke + isolering eller luft)."""
    M = P["material"]
    cc = regel_cc / 1000
    b_regel = f_tra * cc                       # all virke samlat i regeln
    xs = np.cumsum([0.0] + [t / 1000 for _, t in skikt])
    lam_fack = M[isolering]["lam"]
    if fack_luft:
        t_st = dict(skikt)["stomme"]
        lam_fack = t_st / 1000 / luftskikt_R(P, t_st, riktning)
    # nät: fint i x (genom väggen) och vid regelns kant
    ex = kanter(list(xs), fina=[(xs[0], xs[-1], h / 1000)], h_max=h / 1000)
    ey = kanter([0.0, b_regel / 2, cc / 2], fina=[(b_regel / 2 - 0.02, b_regel / 2 + 0.02, h / 1000)],
                h_max=4 * h / 1000)
    ex = np.r_[ex[0] - 0.001, ex, ex[-1] + 0.001]
    m = Modell([ex, ey])
    for (namn, t), a in zip(skikt, xs[:-1]):
        b = a + t / 1000
        if namn == "stomme":
            m.lada("fack", lam_fack, (a, 0), (b, cc))
            m.lada("tra", M["tra"]["lam"], (a, 0), (b, b_regel / 2))
        else:
            m.lada(namn, skikt_lam(P, namn, t, riktning, isolerat_inst), (a, 0), (b, cc))
    m.tom("inne", (-1, -1), (xs[0], 1), Rs=Rsi)
    m.tom("ute", (xs[-1], -1), (1, 1), Rs=Rse)
    m.bygg()
    L = m.koppling()
    U2d = L.sum(axis=1)[1, 0] / (cc / 2)
    # ISO 6946: övre gräns (parallella vägar) och undre gräns (skikt i serie med λ'' i de inhomogena skikten)
    R_lag = []
    for namn, t in skikt:
        if namn != "stomme":
            R_lag.append(t / 1000 / skikt_lam(P, namn, t, riktning, isolerat_inst))
    R_hom = Rsi + Rse + sum(R_lag)
    t_st = dict(skikt)["stomme"] / 1000
    R_tra = R_hom + t_st / M["tra"]["lam"]
    R_fack = R_hom + t_st / lam_fack
    R_ovre = 1 / (f_tra / R_tra + (1 - f_tra) / R_fack)
    R_undre = R_hom + t_st / (f_tra * M["tra"]["lam"] + (1 - f_tra) * lam_fack)
    R_T = 0.5 * (R_ovre + R_undre)
    return dict(U=U2d, U_iso=1 / R_T, U_ovre_gr=1 / R_undre, U_undre_gr=1 / R_ovre,
                U_utan_virke=1 / R_fack, modell=m)


def vaggtyp_U(P, typ, f_tra, isolerat_inst=None):
    V = P["vaggtyp"][typ]
    Y = P["ytmotstand"]
    skikt = [(n, t) for n, t in V["skikt"]]
    return snitt(P, skikt, f_tra, "mineralull", Y["Rsi_vagrat"], Y["Rse_ventilerad_vagg"],
                 P["stomme"]["regel_cc"], "vagrat", isolerat_inst)


def tak_U(P, f_tra, isolerat_inst=None):
    T = P["tak"]
    Y = P["ytmotstand"]
    skikt = [(n, t) for n, t in T["skikt"]]
    return snitt(P, skikt, f_tra, "trafiber", Y["Rsi_uppat"], Y["Rse_ventilerad_tak"], T["balk_cc"], "uppat",
                 isolerat_inst)


def gavelspets_U(P, typ, isolerat_inst=None):
    """Gavelspetsen ovanför hammarbandet: väggens insida och gavelstolens fack (lika djupt som väggens stomme),
    isolerat med mineralull (grundfallet) eller med luft (som i modellen)."""
    G = P["gavelspets"]
    Y = P["ytmotstand"]
    V = P["vaggtyp"][typ]
    skikt = [(n, t) for n, t in V["skikt"]]
    return snitt(P, skikt, G["virkesandel"], "mineralull", Y["Rsi_vagrat"], Y["Rse_ventilerad_vagg"],
                 600.0, "vagrat", isolerat_inst, fack_luft=not G["isolerad"])


def skiktat_U(P, skikt, Rsi, Rse):
    """1D: U för homogena skikt [(material, t_mm)]."""
    M = P["material"]
    R = Rsi + Rse + sum(t / 1000 / M[n]["lam"] for n, t in skikt)
    return 1 / R


# ------------------------------------------------------------------ fönster (SS-EN ISO 10077-1)
def velfac_Uf(P):
    V = P["velfac"]
    s = V["siktlinje"] / 1000
    b, h = V["ref_b"] / 1000, V["ref_h"] / 1000
    Aw = b * h
    Ag = (b - 2 * s) * (h - 2 * s)
    lg = 2 * ((b - 2 * s) + (h - 2 * s))
    Af = Aw - Ag
    return (V["Uw_ref"] * Aw - V["Ug"] * Ag - V["psi_g"] * lg) / Af


def karm(P, typ, b_mm, h_mm):
    """Karmens yttermått [m] ur regelverkets öppning."""
    O = P["oppningar"]
    if typ in ("ytterdörr", "pardörr"):
        return (b_mm - 2 * O["drev"]) / 1000, (h_mm - 2 * O["drev"]) / 1000
    under = O["badd"] if typ in ("fönsterdörr", "skjutdörr") else O["fog"] + O["paforing"]
    return (b_mm - 2 * O["fog"]) / 1000, (h_mm - O["fog"] - under) / 1000


def fonster(P, typ, b_mm, h_mm):
    """Uw, area, glasarea och glasomkrets för ett fönster eller en dörr."""
    V = P["velfac"]
    b, h = karm(P, typ, b_mm, h_mm)
    Aw = b * h
    if typ in ("ytterdörr", "pardörr"):
        return dict(typ=typ, b=b, h=h, A=Aw, Ag=0.0, lg=0.0, U=P["ytterdorr"]["U"], g=0.0)
    s = V["siktlinje"] / 1000
    n = V["partier"].get(typ, 1)
    bg = b - 2 * s - (n - 1) * V["mittpost"] / 1000
    hg = h - 2 * s
    Ag = bg * hg
    lg = 2 * (bg + n * hg)
    Uf = velfac_Uf(P)
    U = (Ag * V["Ug"] + (Aw - Ag) * Uf + lg * V["psi_g"]) / Aw
    return dict(typ=typ, b=b, h=h, A=Aw, Ag=Ag, lg=lg, U=U, g=V["g"], Uf=Uf)
