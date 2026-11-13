"""
U-05: bergvärmepumpen timme för timme.

Värmefaktorn ur kondensorns och förångarens temperaturer, COP = η · T_k / (T_k − T_f) [K], med η bestämt så att
COP blir produktens värde vid B0/W35 (SS-EN 14511: köldbäraren in 0 °C och ut −3 °C, vattnet ut 35 °C). Lyftet T_k −
T_f räknas aldrig mindre än lyft_min: kompressorn behöver ett minsta tryckförhållande, och under det stiger
värmefaktorn inte.

- Kondensorn: golvvärmens framledning plus närmandet. Framledningen är golvvärmeplanets temperatur (ur
  simuleringen) plus rörens motstånd mot betongen gånger värmen per m² och halva temperaturfallet.
- Förångaren: köldbärarens utgående temperatur minus närmandet. Köldbärarens medeltemperatur är den ostörda
  berggrundens minus borrhålets motstånd gånger uttaget per meter och bergets motstånd gånger uttaget i tre
  tidsskalor: de senaste sex timmarna, de senaste 30 dygnen och medeluttaget under driftåren (linjekällan med
  superposition, som i ASHRAE:s dimensionering av borrhål). Uttaget är värmen som pumpen tar ur berget: värmen minus
  elen, också till varmvattnet.

Golvvärmeplanets temperatur är simuleringens; varmvattnet görs med en fast årsvärmefaktor (SS-EN 16147).
"""
from __future__ import annotations

import numpy as np

K0 = 273.15


def eta(VP):
    Tk = 35.0 + VP["approach"] + K0
    Tf = -VP["dT_koldbarare"] - VP["approach"] + K0
    return VP["COP_B0W35"] * (Tk - Tf) / Tk


def bergets_motstand(P):
    """Bergets motstånd mot uttaget per meter borrhål [m·K/W] för uttagets tre tidsskalor: R(t) = (ln(4at/r²) − γ)
    / (4πλ) för en linjekälla, med bergets λ och värmekapacitet. Returnerar (6 timmar, 30 dygn utöver 6 timmar,
    driftåren utöver 30 dygn)."""
    VP = P["varmepump"]
    B = P["material"]["berg"]
    lam, a, r = B["lam"], B["lam"] / (B["rc"] * 1e6), VP["borrhal_d"] / 2000

    def R(t):
        return (np.log(4 * a * t / r ** 2) - 0.5772) / (4 * np.pi * lam)
    R6, R30, Rar = R(6 * 3600.0), R(30 * 86400.0), R(VP["driftar"] * 365 * 86400.0)
    return float(R6), float(R30 - R6), float(Rar - R30)


def _glidande(x, n):
    """Medelvärdet av de n senaste värdena (de första fylls med de första n värdenas medel)."""
    kum = np.cumsum(np.r_[np.full(n, x[:n].mean()), x])
    return (kum[n:] - kum[:-n]) / n


def berakna(P, sim, A_varme, Q_tvv_ar):
    """Timserier och summor för värmepumpen. A_varme: golvvärmens yta [m²]; Q_tvv_ar: varmvattnets värme [kWh/år]."""
    VP = P["varmepump"]
    e = eta(VP)
    Q = np.asarray(sim["Q_h"], float)
    q = Q / A_varme
    T_fram = sim["T_h"] + q * VP["R_ror"] + VP["dT_vatten"] / 2
    Tk = T_fram + VP["approach"] + K0
    P_tvv = Q_tvv_ar * 1000 / 8760                      # varmvattnets medeleffekt [W]
    uttag_tvv = P_tvv * (1 - 1 / VP["COP_tvv"])
    R6, R30, Rar = bergets_motstand(P)
    cop = np.full(len(Q), 4.5)
    for _ in range(4):
        uttag = Q * (1 - 1 / cop) + uttag_tvv          # ur berget [W]
        ql = uttag / VP["borrhal_L"]
        T_kb = VP["T_berg"] - ql * VP["R_borrhal"] - _glidande(ql, 6) * R6 - _glidande(ql, 30 * 24) * R30 - \
            ql.mean() * Rar
        Tf = T_kb - VP["dT_koldbarare"] / 2 - VP["approach"] + K0
        cop = e * Tk / np.maximum(Tk - Tf, VP["lyft_min"])
    el = np.where(Q > 0, Q / cop, 0.0)
    pa = Q > 0
    return dict(eta=e, cop=cop, el=el, T_fram=T_fram, T_kb=T_kb, uttag=uttag,
                SCOP=float(Q.sum() / el.sum()) if el.sum() > 0 else 0.0,
                T_fram_max=float(T_fram[pa].max()) if pa.any() else 0.0,
                T_kb_min=float(T_kb.min()), T_kb_medel=float(T_kb.mean()),
                T_kb_drift=float((T_kb[pa] * Q[pa]).sum() / Q[pa].sum()) if pa.any() else 0.0,
                cop_min=float(cop[pa].min()) if pa.any() else 0.0,
                el_max=float(el.max()), R_berg=(R6, R30, Rar))
