"""
AR-01: fasadsten (Bohusgranit 30–50 mm) på källarväggar av Sundolitt Kub 350-150, infästning. Kontroller av stödvinkeln,
gängstängerna som bär den och isolerpluggarna. Ritningarna (ritningar.py) läser resultat.json.

    python berakning.py      -> resultat.json och en sammanställning i terminalen

Stenen limmas med fästmassa mot armeringsbruket, som är förankrat i betongkärnan med isolerplugg genom nätet.
Stödvinkeln under nedersta skiftet är dimensionerad för att ensam bära hela stenhöjden, om fästmassans fäste mot
cellplasten går förlorat (brand, åldring). Pluggarna håller armeringsbruket med stenen mot vindsug.

Koordinater (mm): x = 0 i betongkärnans yttre yta, utåt positivt; y = 0 i stödvinkelns överkant (stenens underkant).
"""
import json
import math
import tomllib
from pathlib import Path

HERE = Path(__file__).parent
IN = tomllib.loads((HERE / "indata.toml").read_text(encoding="utf-8"))
GM0 = 1.1                    # EN 1993-1-4, rostfritt stål


def lagen():
    """Skiktens lägen i x (mm från betongkärnans yta)."""
    v, s = IN["vagg"], IN["skikt"]
    x_bruk = v["eps"] + s["armeringsbruk"]
    x_sten = x_bruk + s["fastmassa"]
    return dict(eps=v["eps"], bruk=x_bruk, sten_bak=x_sten, sten_fram=x_sten + s["sten"],
                sten_fram_min=x_sten + s["sten_min"], sten_fram_max=x_sten + s["sten_max"],
                sten_mitt=x_sten + s["sten"] / 2, vinkel_fram=x_sten + s["sten_min"] - 5)


def laster():
    s, l, vi = IN["sten"], IN["last"], IN["vind"]
    g_sten = s["densitet"] * 9.81 * IN["skikt"]["sten"] / 1e6           # kN/m²
    g_fast = s["fastmassa_densitet"] * 9.81 * IN["skikt"]["fastmassa"] / 1e6
    g = g_sten + g_fast
    qk = g * s["H_max"] / 1000                                            # kN/m på vinkeln
    qd = l["gamma_d"] * l["gamma_G"] * qk
    wd = l["gamma_d"] * l["gamma_Q"] * vi["cpe"] * vi["qp"]               # kN/m², sug
    return dict(g_sten=g_sten, g_fast=g_fast, g=g, qk=qk, qd=qd, wd=wd)


def stang(L_, X):
    """Gängstång med hävarm genom cellplasten (SS-EN 1992-4 6.2.2.3, α_M = 1). Vinkeln är fastspänd mellan två
    muttrar, så stången tar även vinkelns vridmoment: lasten verkar i stenens mitt, hävarmen räknas från
    betongytan + d/2."""
    s, w = IN["stang"], IN["vinkel"]
    V = L_["qd"] * s["cc"] / 1000                                          # kN per stång
    Vk = L_["qk"] * s["cc"] / 1000
    l = X["sten_mitt"] + s["d"] / 2                                        # mm
    M = V * l / 1000                                                       # kNm
    d_s = math.sqrt(4 * s["As"] / math.pi)
    W = math.pi * d_s**3 / 32
    MRk = 1.2 * W * s["fuk"] / 1e6                                         # kNm
    gMs = max(1.25, s["fuk"] / s["fyk"])
    MRd = MRk / gMs
    NRk_p = s["psi0_sus"] * s["tau_Rk_cr"] * s["psi_c"] * math.pi * s["d"] * s["hef"] / 1000
    VRd_cp = s["k8"] * NRk_p / s["gM"]
    # nedböjning (bruksgräns): stången som konsol från betongytan till vinkelns liv, med lasten och dess moment
    I = math.pi * d_s**4 / 64
    a = X["bruk"] + w["t"] / 2
    m_tip = Vk * 1000 * (X["sten_mitt"] - a)                               # Nmm
    E = w["E"]
    dl = Vk * 1000 * a**3 / (3 * E * I) + m_tip * a**2 / (2 * E * I)
    th = Vk * 1000 * a**2 / (2 * E * I) + m_tip * a / (E * I)
    fall = dl + th * (X["vinkel_fram"] - a)
    h_min = s["hef"] + 2 * s["hal_d"]
    return dict(V=V, l=l, M=M, W=W, MRd=MRd, utn_M=M / MRd, NRk_p=NRk_p, VRd_cp=VRd_cp, utn_cp=V / VRd_cp,
                fall=fall, h_min=h_min, h_ok=h_min <= IN["vagg"]["karna"])


def vinkel(L_, X):
    """Vinkeln: vågräta benet som konsol från livet, och böjning mellan stängerna."""
    w, s = IN["vinkel"], IN["stang"]
    t = w["t"]
    f_d = w["fy"] / GM0
    x_liv = X["bruk"] + t
    hav = (X["sten_bak"] + X["vinkel_fram"]) / 2 - x_liv                    # lastens hävarm från livet
    m = L_["qd"] * hav / 1000                                             # kNm/m
    sig_ben = m * 1e6 / (1000 * t**2 / 6)
    # böjning mellan stängerna, fritt upplagd på säker sida; livet (60) ger böjstyvheten
    delar = [(w["fot"] * t, -t / 2), ((w["liv"] - t) * t, -t - (w["liv"] - t) / 2)]
    A = sum(a for a, _ in delar)
    yc = sum(a * y for a, y in delar) / A
    Ix = w["fot"] * t**3 / 12 + w["fot"] * t * (-t / 2 - yc) ** 2 + t * (w["liv"] - t) ** 3 / 12 + \
        (w["liv"] - t) * t * (-t - (w["liv"] - t) / 2 - yc) ** 2
    W = Ix / max(abs(yc), abs(-w["liv"] - yc))
    M = L_["qd"] * (s["cc"] / 1000) ** 2 / 8
    sig = M * 1e6 / W
    return dict(hav=hav, sig_ben=sig_ben, utn_ben=sig_ben / f_d, M=M, sig=sig, utn_M=sig / f_d, f_d=f_d,
                upplag=X["vinkel_fram"] - X["sten_bak"])


def plugg(L_):
    p = IN["plugg"]
    NRd = p["NRk"] / p["gM"]
    n = 1e6 / (p["cc_x"] * p["cc_y"])
    return dict(NRd=NRd, n=n, n_erf=L_["wd"] / NRd, n_min=p["n_min"], utn=L_["wd"] / (n * NRd),
                hD_max=p["L"] - 10 - p["hef"])


def main():
    X = lagen()
    L_ = laster()
    R = dict(lagen=X, laster=L_, stang=stang(L_, X), vinkel=vinkel(L_, X), plugg=plugg(L_))
    s = IN["sten"]
    kg = L_["g_sten"] / 9.81 * 1000
    R["sten"] = dict(kg_m2=kg, kg_max=s["langd"][1] * s["hojd"] / 1e6 * s["densitet"] * IN["skikt"]["sten_max"] / 1000)
    (HERE / "resultat.json").write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8")

    st, v, p = R["stang"], R["vinkel"], R["plugg"]
    print(f"Skikt: cellplast {X['eps']:.0f}, stenens baksida {X['sten_bak']:.0f}, framsida {X['sten_fram_min']:.0f}–"
          f"{X['sten_fram_max']:.0f} mm från betongkärnan ({X['sten_fram_min'] - X['eps']:.0f}–"
          f"{X['sten_fram_max'] - X['eps']:.0f} mm utanför cellplasten)")
    print(f"Last: sten {L_['g_sten']:.2f} + fästmassa {L_['g_fast']:.2f} = {L_['g']:.2f} kN/m², "
          f"qk = {L_['qk']:.2f}, qd = {L_['qd']:.2f} kN/m, vindsug wd = {L_['wd']:.2f} kN/m²")
    print(f"Stång M{IN['stang']['d']} c/c {IN['stang']['cc']}: V = {st['V']:.2f} kN, l = {st['l']:.0f} mm, "
          f"M = {st['M']:.3f} / {st['MRd']:.3f} kNm ({st['utn_M']:.2f}), bändbrott {st['utn_cp']:.2f}, "
          f"framkanten sjunker {st['fall']:.1f} mm, kärnan räcker: {st['h_ok']}")
    print(f"Vinkel: ben {v['utn_ben']:.2f}, mellan stängerna {v['utn_M']:.2f}, upplag {v['upplag']:.0f} mm")
    print(f"STR U 2G: {p['n']:.1f} st/m² (minst {p['n_min']}, behov {p['n_erf']:.1f}), utn {p['utn']:.2f}")
    print(f"Sten: {R['sten']['kg_m2']:.0f} kg/m², största sten {R['sten']['kg_max']:.0f} kg")


if __name__ == "__main__":
    main()
