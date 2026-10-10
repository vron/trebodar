"""
U-02: fasadsten (granit 40 mm) på källarväggar av Sundolitt Kub 350-150, infästning. Kontroller av stödvinkel,
konsol, gängstänger, Halfen UHA-ankare och isolerplugg. Ritningarna (ritningar.py) läser resultat.json.

    python berakning.py      -> resultat.json och en sammanställning i terminalen

Stenen bärs i bruksskedet av fästmassan mot armeringsbruket. Stålet är dimensionerat så att det ensamt bär stenen
om fästet mot cellplasten går förlorat (brand, åldring): stödvinkeln tar hela stenhöjdens tyngd, Halfen-ankarna i
liggfogarna håller stenen mot vindsug och mot att falla ut. Isolerpluggarna håller armeringsbruket mot vindsug.

Koordinater (mm): x = 0 i betongkärnans yttre yta, utåt positivt; y = 0 i stödvinkelns överkant (stenens underkant).
"""
import json
import math
import tomllib
from pathlib import Path

HERE = Path(__file__).parent
IN = tomllib.loads((HERE / "indata.toml").read_text(encoding="utf-8"))
GM0 = 1.1                    # EN 1993-1-4, rostfritt stål
GM2 = 1.25


def lagen():
    """Skiktens lägen i x (mm från betongkärnans yta)."""
    v, s = IN["vagg"], IN["skikt"]
    x_eps = v["eps"]
    x_bruk = x_eps + s["armeringsbruk"]
    x_sten = x_bruk + s["fastmassa"]
    return dict(eps=x_eps, bruk=x_bruk, sten_bak=x_sten, sten_fram=x_sten + s["sten"],
                sten_mitt=x_sten + s["sten"] / 2)


def laster():
    s, l, vi = IN["sten"], IN["last"], IN["vind"]
    g_sten = s["densitet"] * 9.81 * IN["skikt"]["sten"] / 1e6           # kN/m²
    g_fast = s["fastmassa_densitet"] * 9.81 * IN["skikt"]["fastmassa"] / 1e6
    g = g_sten + g_fast
    qk = g * s["H_max"] / 1000                                            # kN/m på vinkeln
    qd = l["gamma_d"] * l["gamma_G"] * qk
    wd = l["gamma_d"] * l["gamma_Q"] * vi["cpe"] * vi["qp"]               # kN/m², sug
    return dict(g_sten=g_sten, g_fast=g_fast, g=g, qk=qk, qd=qd, wd=wd)


def vinkel(L_, X):
    """Bockad vinkel: vågrätt ben under stenen (x sten_bak … sten_fram − 5), lodrätt ben nedåt längst fram."""
    w = IN["vinkel"]
    t, liv, fot = w["t"], w["liv"], w["fot"]
    # delytor: (area, y-tyngdpunkt), y = 0 i överkant
    delar = [(fot * t, -t / 2), ((liv - t) * t, -t - (liv - t) / 2)]
    A = sum(a for a, _ in delar)
    yc = sum(a * y for a, y in delar) / A
    Ix = fot * t**3 / 12 + fot * t * (-t / 2 - yc) ** 2 + t * (liv - t) ** 3 / 12 + (liv - t) * t * (
        -t - (liv - t) / 2 - yc) ** 2
    W = Ix / max(abs(yc), abs(-liv - yc))
    cc = IN["konsol"]["cc"]
    M = L_["qd"] * (cc / 1000) ** 2 / 8                                  # kNm, fritt upplagd (på säker sida)
    sig = M * 1e6 / W
    f_d = w["fy"] / GM0
    u = 5 * L_["qk"] * cc**4 / (384 * w["E"] * Ix)                        # mm, qk i N/mm = kN/m
    # vågräta benet som konsol bakåt från det lodräta benet; lasten jämnt fördelad över stenens upplag
    x_fram = X["sten_fram"] - 5
    upplag = x_fram - X["sten_bak"]
    l_kons = upplag - t
    m_ben = L_["qd"] * (l_kons / upplag) * (l_kons / 2) / 1000            # kNm/m
    sig_ben = m_ben * 1e6 / (1000 * t**2 / 6)
    # vridning: lasten i upplagets mitt, skjuvcentrum i hörnet; vinkeln hålls mot vridning vid konsolerna
    e_T = upplag / 2 - t / 2
    It = (fot + liv - t) * t**3 / 3
    tT = L_["qd"] * e_T                                                   # Nmm/mm
    T = tT * cc / 2
    tau_T = T * t / It
    phi = tT * cc**2 / (8 * w["G"] * It)
    return dict(A=A, yc=yc, Ix=Ix, W=W, M=M, sig=sig, f_d=f_d, utn_M=sig / f_d, u=u, u_grans=cc / 500,
                upplag=upplag, sig_ben=sig_ben, utn_ben=sig_ben / f_d, tau_T=tau_T,
                utn_T=tau_T / (f_d / math.sqrt(3)), fall_fram=phi * upplag)


def konsol(L_, X):
    k, w, inj = IN["konsol"], IN["vinkel"], IN["injektion"]
    V = L_["qd"] * k["cc"] / 1000                                         # kN per konsol
    e = X["sten_mitt"]
    M = V * e / 1000                                                      # kNm i fotplåtens plan
    h = k["flans_y"][1] - k["flans_y"][0]
    f_d = w["fy"] / GM0
    sig = M * 1e6 / (k["t"] * h**2 / 6)
    tau = 1.5 * V * 1e3 / (k["t"] * h)
    a = k["a_svets"]
    sig_w = M * 1e6 / (2 * a * h**2 / 6)
    tau_w = V * 1e3 / (2 * a * h)
    fvw = w["fu"] / (math.sqrt(3) * 1.0 * GM2)                            # βw = 1,0 för rostfritt
    sig_weq = math.hypot(sig_w, tau_w)
    # gängstängerna: tryck mot betongen vid fotplåtens underkant, dragning i den övre stången
    z = k["stang_y"][1] - k["fot_y"][0] - 10
    N = M * 1000 / z                                                      # kN
    Vst = V / 2
    d, hef = inj["d"], inj["hef"]
    NRk_p = inj["psi0_sus"] * inj["tau_Rk_cr"] * inj["psi_c"] * math.pi * d * hef / 1000
    NRk_c = inj["k_cr"] * math.sqrt(IN["vagg"]["fck"]) * hef**1.5 / 1000
    NRk_s = inj["As"] * inj["fuk"] / 1000
    NRd = min(NRk_p / inj["gM"], NRk_c / inj["gM"], NRk_s / inj["gMs"])
    VRd = min(0.5 * inj["As"] * inj["fuk"] / 1000 / inj["gMs_v"], 2 * min(NRk_p, NRk_c) / inj["gM"])
    utn_NV = (N / NRd) ** 1.5 + (Vst / VRd) ** 1.5
    h_min = hef + 2 * k["hal_d"]
    return dict(V=V, e=e, M=M, sig=sig, tau=tau, utn_flans=max(sig / f_d, tau / (f_d / math.sqrt(3))),
                sig_weq=sig_weq, fvw=fvw, utn_svets=sig_weq / fvw, z=z, N=N, Vst=Vst, NRk_p=NRk_p, NRk_c=NRk_c,
                NRd=NRd, VRd=VRd, utn_N=N / NRd, utn_NV=utn_NV, h_min=h_min, h_ok=h_min <= IN["vagg"]["karna"])


def uha(L_, X):
    u, s = IN["uha"], IN["sten"]
    k = X["sten_mitt"]                                                    # stiftets läge från betongytan
    A_max = u["cc"] / 1000 * s["max_hojd"] / 1000                         # m², halva stenen över och under
    H_max = L_["wd"] * A_max
    b, hh = s["exempel"]
    A_ex = 2 * (b * hh / 1e6) / 4                                         # 2 stift per sten och fog
    H_ex = L_["wd"] * A_ex
    return dict(k=k, k_ok=130 <= k <= 150, A_max=A_max, H_max=H_max, utn=H_max * 1000 / u["HH_Rd"],
                A_ex=A_ex, H_ex=H_ex, utn_ex=H_ex * 1000 / u["HH_Rd"], H_stift=H_max / 2,
                t0_ok=u["t0"] <= IN["vagg"]["karna"] - 30, h_ok=u["h_min"] <= IN["vagg"]["karna"])


def plugg(L_):
    p = IN["plugg"]
    NRd = p["NRk"] / p["gM"]
    n = 1e6 / (p["cc_x"] * p["cc_y"])
    n_erf = L_["wd"] / NRd
    return dict(NRd=NRd, n=n, n_erf=n_erf, n_min=p["n_min"], utn=L_["wd"] / (n * NRd),
                hD_max=p["L"] - 10 - p["hef"])


def main():
    X = lagen()
    L_ = laster()
    R = dict(lagen=X, laster=L_, vinkel=vinkel(L_, X), konsol=konsol(L_, X), uha=uha(L_, X), plugg=plugg(L_))
    s = IN["sten"]
    R["sten"] = dict(kg_m2=L_["g_sten"] / 9.81 * 1000, kg_max=s["max_yta"] * L_["g_sten"] / 9.81 * 1000,
                     kg_ex=s["exempel"][0] * s["exempel"][1] / 1e6 * L_["g_sten"] / 9.81 * 1000)
    (HERE / "resultat.json").write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8")

    v, k, u, p = R["vinkel"], R["konsol"], R["uha"], R["plugg"]
    print(f"Skikt: cellplast {X['eps']:.0f}, stenens baksida {X['sten_bak']:.0f}, framsida {X['sten_fram']:.0f} mm "
          f"från betongkärnan ({X['sten_fram'] - X['eps']:.0f} mm utanför cellplasten)")
    print(f"Last: sten {L_['g_sten']:.2f} + fästmassa {L_['g_fast']:.2f} = {L_['g']:.2f} kN/m², "
          f"qk = {L_['qk']:.2f}, qd = {L_['qd']:.2f} kN/m, vindsug wd = {L_['wd']:.2f} kN/m²")
    print(f"Vinkel: M = {v['M']:.3f} kNm, σ = {v['sig']:.0f} MPa ({v['utn_M']:.2f}), u = {v['u']:.2f} mm "
          f"(≤ {v['u_grans']:.1f}), ben {v['utn_ben']:.2f}, vridning {v['utn_T']:.2f}, "
          f"framkant sjunker {v['fall_fram']:.2f} mm")
    print(f"Konsol: V = {k['V']:.2f} kN, e = {k['e']:.0f} mm, M = {k['M']:.3f} kNm, fläns {k['utn_flans']:.2f}, "
          f"svets {k['utn_svets']:.2f}, stång N = {k['N']:.2f} kN / NRd {k['NRd']:.1f} ({k['utn_N']:.2f}), "
          f"N+V {k['utn_NV']:.2f}, kärnan räcker: {k['h_ok']}")
    print(f"UHA-7: k = {u['k']:.0f} mm (130–150: {u['k_ok']}), H = {u['H_max']:.2f} kN / 1,10 ({u['utn']:.2f}); "
          f"exemplet {u['H_ex']:.2f} kN ({u['utn_ex']:.2f})")
    print(f"STR U 2G: {p['n']:.1f} st/m² (minst {p['n_min']}, behov {p['n_erf']:.1f}), utn {p['utn']:.2f}, "
          f"cellplast + bruk ≤ {p['hD_max']:.0f} mm")
    print(f"Sten: {R['sten']['kg_m2']:.0f} kg/m², största sten {R['sten']['kg_max']:.0f} kg, "
          f"exemplet {R['sten']['kg_ex']:.0f} kg")


if __name__ == "__main__":
    main()
