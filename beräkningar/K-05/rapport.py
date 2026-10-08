"""
Sätter ihop K-05 som PDF: läser resultat.json, ritar figurerna och kompilerar rapport/mall.typ.
"""
import json
import math
import os

import numpy as np

import figurer as F
import laster as LA

HERE = os.path.dirname(os.path.abspath(__file__))
G = json.load(open(os.path.join(HERE, "bild/geometri.json")))
R = json.load(open(os.path.join(HERE, "resultat.json")))


def f(x, n=1):
    s = f"{x:,.{n}f}".replace(",", " ").replace(".", ",")
    return s.replace("-", "−")


def pr(x):
    return f"{x * 100:.0f} %"


def jarn(t):
    return "–" if not t else f"Ø{t[0]} s{t[1]}"


def mm(x):
    return f"{x:,.0f}".replace(",", " ")


ind = R["indata"]
b = R["bojning"]
D = {}
nu, no = ind["nat_uk"], ind["nat_ok"]
D["mat"] = dict(fck=f(ind["fck"], 0), fcd=f(ind["fcd"], 1), fctm=f(ind["fctm"], 2), Ecm=f(ind["Ecm"] / 1e3, 1),
                fyd=f(ind["fyd"], 0), c_uk=str(ind["c_uk"]), c_ok=str(ind["c_ok"]), band=f(ind["band"], 0),
                gk=f(ind["gk"], 2), qk=f(ind["qk"], 1), qv=f(ind["qv"], 1), nat_uk=jarn(nu), nat_ok=jarn(no),
                sank=f(ind["sank"], 0), konv=f(ind["konv"], 1), zonf=f(ind["konv"] * ind["zon"], 1))

# ------------------------------------------------------------------ laster
L = LA.alla()
D["enh"] = dict(g_betong=f(LA.G_BETONG, 2), g_golv=f(LA.G_GOLV, 2), gk=f(LA.G_BETONG + LA.G_GOLV, 2),
                q=f(LA.Q_NYTTIG), qv=f(LA.Q_VAGG), g_tak=f(LA.G_TAK, 2), g_tak_h=f(LA.G_TAK_H, 2), s=f(LA.S_K),
                g_vagg=f(LA.G_VAGG), h_vagg=f(LA.H_VAGG), utspr=f(LA.UTSPRANG), cc=f(LA.CC_TAKBALK),
                takstol=f(LA.G_TAKSTOL, 2), vinkel=f(LA.TAKVINKEL, 0), vagg_in=mm(LA.VAGG_IN),
                tr_l=f(LA.TRAPPA["langd"]), tr_b=f(LA.TRAPPA["bredd"], 2), tr_g=f(LA.TRAPPA["g"]), tr_q=f(LA.TRAPPA["q"]),
                t_mitt=f(2.405 / 2 + LA.UTSPRANG, 2), t_sida=f(2.155 / 2 + LA.UTSPRANG, 2))
PL = {"platta": "plattan", "vägg": "Lecavägg", "mark": "mark"}
D["punkter"] = [dict(namn=p["namn"], urspr=p["urspr"], delar=p["delar"], x=mm(p["x"]), y=mm(p["y"]), Gk=f(p["Gk"]),
                     Sk=f(p["Sk"]), Rd=f(p["Rd"]), Wd=f(p["Wd"]) if p["Wd"] else "–", plats=PL[p["plats"]])
                for p in L["punkter"]]


def stracka(w):
    (x0, y0), (x1, y1) = w["p0"], w["p1"]
    return f"y = {mm(y0)}, x {mm(x0)}–{mm(x1)}" if y0 == y1 else f"x = {mm(x0)}, y {mm(y0)}–{mm(y1)}"


def platser(w):
    d = [(w["L_vägg"], "Lecavägg"), (w["L_platta"], "fri kant"), (w["L_mark"], "mark")]
    d = [(l_, t) for l_, t in d if l_ > 100]
    if len(d) == 1:
        return d[0][1]
    return ", ".join(f"{t} {f(l_ / 1000)} m" for l_, t in d)


D["vaggar"] = [dict(namn=w["namn"], text=w["text"], typ=w["typ"], str=stracka(w),
                    gk=(f(w["gk_min"], 2) if w["typ"] == "takfot" else f"{f(w['gk_min'], 2)}–{f(w['gk_max'], 2)}"),
                    sk=f(w["sk_max"], 2) if w["sk_max"] else "–", G=f(w["Gk"]), S=f(w["Sk"]) if w["Sk"] else "–",
                    plats=platser(w)) for w in L["vaggar"]]
qd2 = [l for l in L["linjer"] if l["namn"] == "qD2"]
qt = [l for l in L["linjer"] if l["namn"] == "qT"]
D["qD2"] = dict(gk=f(qd2[0]["gk"], 2), sk=f(qd2[0]["sk"], 2), wd=f(qd2[0]["wd"], 2),
                str=" och ".join(f"{mm(l['pl'][0][1])}–{mm(l['pl'][1][1])}" for l in qd2), x=mm(qd2[0]["pl"][0][0]))
D["qT"] = dict(gk=f(qt[0]["gk"], 2), qk=f(qt[0]["qk"], 2), x=" och ".join(mm(l["pl"][0][0]) for l in qt))
tot = R["jamvikt"]
ovanG = sum(p["Gk"] for p in L["punkter"]) + sum(w["Gk"] for w in L["vaggar"]) + sum(
    l["gk"] * (l["pl"][1][1] - l["pl"][0][1]) / 1000 for l in L["linjer"])
ovanS = sum(p["Sk"] for p in L["punkter"]) + sum(w["Sk"] for w in L["vaggar"]) + sum(
    l["sk"] * (l["pl"][1][1] - l["pl"][0][1]) / 1000 for l in L["linjer"])
D["tot"] = dict(Gp=f(tot["Gp"], 0), G=f(tot["G"], 0), Q=f(tot["Q"], 0), V=f(tot["V"], 0), S=f(tot["S"], 0),
                ovanG=f(ovanG, 0), ovanS=f(ovanS, 0))
from shapely.geometry import Polygon as _Poly  # noqa: E402
_K = _Poly(G["kontur"])
D["snotak"] = f(LA.S_K * (_K.area / 1e6 + _K.length / 1e3 * LA.UTSPRANG), 0)
D["yta"] = dict(mark=f(_Poly(G["mark"]).area / 1e6, 1), tot=f(_Poly(G["kontur"], [G["hal"]]).area / 1e6, 0))

# ------------------------------------------------------------------ böjning och zoner
D["boj"] = [
    dict(lage="Underkant, x", arm=jarn(nu), d=f(b["uk"]["d_x"], 0), As=f(b["uk"]["As"], 0), MEd=f(b["uk"]["MEd_x"] / 1e3),
         topp=f(b["uk"]["topp_x"] / 1e3), MRd=f(b["uk"]["MRd_x"] / 1e3), utn=pr(b["uk"]["MEd_x"] / b["uk"]["MRd_x"])),
    dict(lage="Underkant, y", arm=jarn(nu), d=f(b["uk"]["d_y"], 0), As=f(b["uk"]["As"], 0), MEd=f(b["uk"]["MEd_y"] / 1e3),
         topp=f(b["uk"]["topp_y"] / 1e3), MRd=f(b["uk"]["MRd_y"] / 1e3), utn=pr(b["uk"]["MEd_y"] / b["uk"]["MRd_y"])),
    dict(lage="Överkant, x", arm=jarn(no), d=f(b["ok"]["d_x"], 0), As=f(b["ok"]["As"], 0), MEd="", topp="",
         MRd=f(b["ok"]["MRd_x"] / 1e3), utn=""),
    dict(lage="Överkant, y", arm=jarn(no), d=f(b["ok"]["d_y"], 0), As=f(b["ok"]["As"], 0), MEd="", topp="",
         MRd=f(b["ok"]["MRd_y"] / 1e3), utn=""),
]
zon = []
for z in R["zoner"]:
    x0, y0, x1, y1 = z["bounds"]
    MEd = max(z["MEd_x"], z["MEd_y"])
    zon.append(dict(namn=z["namn"], x=f"{f(x0 / 1e3, 2)}–{f(x1 / 1e3, 2)}", y=f"{f(y0 / 1e3, 2)}–{f(y1 / 1e3, 2)}",
                    mat=f"{f((x1 - x0) / 1e3, 1)} × {f((y1 - y0) / 1e3, 1)}", jarn=jarn(z["tillagg"]),
                    MEd=f(MEd / 1e3) if MEd > 0 else "–", MRd=f(min(z["MRd_x"], z["MRd_y"]) / 1e3),
                    orsak=z["orsak"], ror=", ".join(z["pelare"])))
D["zon"] = zon
D["zon_namn"] = [z["namn"] for z in R["zoner"]]
# överkant: utnyttjande utanför och inom zonerna
Fz0 = dict(np.load(os.path.join(HERE, "falt.npz")))
xy = Fz0["xy"]
inzon = np.zeros(len(xy), bool)
for z in R["zoner"]:
    x0, y0, x1, y1 = z["bounds"]
    inzon |= (xy[:, 0] >= x0) & (xy[:, 0] <= x1) & (xy[:, 1] >= y0) & (xy[:, 1] <= y1)
mox, moy = -Fz0["s_mox"], -Fz0["s_moy"]
u_ok = np.maximum(mox / b["ok"]["MRd_x"], moy / b["ok"]["MRd_y"])
u_okl = np.maximum(mox / b["ok"]["MRd_x_lag"], moy / b["ok"]["MRd_y_lag"])
D["ok_utan"] = pr(u_ok[~inzon].max())
D["ok_utan_lag"] = pr(u_okl[~inzon].max())
D["ok_MRd_lag"] = f(min(b["ok"]["MRd_x_lag"], b["ok"]["MRd_y_lag"]) / 1e3)

D["ok_utan_M"] = f(max(mox[~inzon].max(), moy[~inzon].max()) / 1e3)
bz = [z for z in R["zoner"] if z["orsak"] == "böjning"]
if bz:
    zz = max(bz, key=lambda z: max(z["MEd_x"] / z["MRd_x"], z["MEd_y"] / z["MRd_y"]))
    D["ok_zon"] = pr(max(zz["MEd_x"] / zz["MRd_x"], zz["MEd_y"] / zz["MRd_y"]))
    D["ok_zon_namn"] = zz["namn"]
    D["ok_zon_M"] = f(max(zz["MEd_x"], zz["MEd_y"]) / 1e3)
    D["ok_zon_MRd"] = f(min(zz["MRd_x"], zz["MRd_y"]) / 1e3)
    D["ok_zon_jarn"] = jarn(zz["tillagg"])
else:
    D["ok_zon"] = D["ok_zon_namn"] = D["ok_zon_M"] = D["ok_zon_MRd"] = D["ok_zon_jarn"] = "–"
D["uk_max"] = pr(max(b["uk"]["MEd_x"] / b["uk"]["MRd_x"], b["uk"]["MEd_y"] / b["uk"]["MRd_y"]))

# ------------------------------------------------------------------ genomstansning, lokalt tryck, rör
pel = []
for p in R["pelare"]:
    pel.append(dict(namn=p["namn"], VEd=f(p["VEd"] / 1e3), tillagg=jarn(p["tillagg"]), d=f(p["d"], 0),
                    rho=f(p["rho"] * 100, 2), beta=f(p["beta"], 2), u1=f(p["u1"], 0) + (" ¹" if p["nara"] else ""),
                    stolpar=", ".join(p["stolpar"]) or "–", Vnet=f(p["Vnet"] / 1e3), vf=f(p["vEd_f"], 2),
                    vfe=f(p["vEd_fe"], 2), vEd=f(p["vEd"], 2), vRd=f(p["vRdc"], 2), utn=pr(p["utn"]),
                    lag=pr(p["utn_lag"]), utn0=pr(p["utn0"]), knack=pr(p["knack"]), lokal=pr(p["utn_lokal"]),
                    Rl=f(p["R_lyft"] / 1e3)))
D["pel"] = pel
D["pel_tillagg"] = [f"{p['namn']} {jarn(p['tillagg'])}" for p in R["pelare"] if p["tillagg"]]
mp = max(R["pelare"], key=lambda p: p["VEd"])
D["max_pel"] = mp["namn"]
D["max_VEd"] = f(mp["VEd"] / 1e3)
ms = max(R["pelare"], key=lambda p: p["utn"])
D["max_stans"] = dict(namn=ms["namn"], utn=pr(ms["utn"]), lag=pr(ms["utn_lag"]))
ml = max(R["pelare"], key=lambda p: p["utn_lag"])
D["max_lag"] = dict(namn=ml["namn"], utn=pr(ml["utn_lag"]))
D["max_knack"] = pr(max(p["knack"] for p in R["pelare"]))
kn = R["kontroll_netto"]
D["kn"] = dict(min=f(kn["min"], 2), max=f(kn["max"], 2))
sb = R["stolpe_B"]
D["stB"] = dict(N=f(sb["N"] / 1e3), M=f(sb["M"], 2), e=f(sb["e"], 0), L=f(sb["L"], 0), B=f(sb["B"], 0),
                b1=f(sb["b1"], 0), s=f(sb["sigma"], 2), kf=f(sb["kf"], 2), utn=pr(sb["utn"]), tmin=f(sb["t_min"], 1),
                t=f(sb["t"], 0), Wd=f(sb["Wd"]))
mf = max(R["pelare"], key=lambda p: p["vEd_fe"] / p["vEd_f"])
D["fe_beta"] = dict(namn=mf["namn"], kvot=f(mf["vEd_fe"] / mf["vEd_f"] * mf["beta"], 2),
                   styr=", ".join(p["namn"] for p in R["pelare"] if p["vEd_fe"] > p["vEd_f"]))
D["gemensam"] = ", ".join(f"{p['namn']} ({', '.join(p['gemensam'])})" for p in R["pelare"] if p["gemensam"])
stor = [p for p in R["pelare"] if p["plat"][0] > 80]
D["plat"] = [dict(namn=p["namn"], b=f(p["plat"][0], 0), t=f(p["plat"][1], 0), fy=f(p["plat"][2], 0), beff=f(p["c"], 0))
             for p in stor]
mvagg = max(R["pelare"], key=lambda p: p["VEd"])
D["vaggfall"] = dict(namn=mvagg["namn"], styv=f(mvagg["VEd_styv"] / 1e3), vagg=f(mvagg["VEd_vagg"] / 1e3),
                     n=sum(1 for p in R["pelare"] if p["VEd_vagg"] >= max(p["VEd_fjader"], p["VEd_styv"])))
lo = R["lokal"]
D["lokal"] = dict(utn=pr(lo["utn"]), namn=lo["namn"], t=f(lo["t_topp"], 1))
st = []
for s_ in R["stolpar"]:
    if s_["fall"] == "på plattan":
        st.append(dict(namn=s_["namn"], Rd=f(s_["Rd"] / 1e3), yta=f"{f(s_['yta'][0], 0)}×{f(s_['yta'][1], 0)}",
                       u1=f(s_["u1"], 0) + (" ¹" if s_["nara"] else ""), beta=f(s_["beta"], 2), vEd=f(s_["vEd"], 2),
                       vRd=f(s_["vRdc"], 2), utn=pr(s_["utn"]), lag=pr(s_["utn_lag"]), tillagg=jarn(s_["tillagg"]),
                       ror=", ".join(s_["ror"]) or "–"))
D["stolp"] = st
smax = max((s_ for s_ in R["stolpar"] if s_["fall"] == "på plattan"), key=lambda s_: s_["utn_lag"])
D["stolp_max"] = dict(namn=smax["namn"], utn=pr(smax["utn"]), lag=pr(smax["utn_lag"]))
_K = os.path.join(HERE, "konvergens.json")
if os.path.exists(_K):
    Kv = json.load(open(_K))
    fj = [k for k in Kv if k["ror"] == "fjäder" and k["h"] == 200]
    st_ = [k for k in Kv if k["ror"] == "styv" and k["h"] == 200]
    h300 = [k for k in Kv if k["ror"] == "fjäder" and k["h"] == 300][0]
    el = lambda ks: ", ".join(f(80 * k["fin"], 0) for k in ks[:-1]) + " och " + f(80 * ks[-1]["fin"], 0)
    dmu = max(abs(k["mu"] / fj[0]["mu"] - 1) for k in fj + [h300])
    dP = max(abs(k["P10"] / st_[0]["P10"] - 1) for k in st_)
    D["konv"] = (f"Med en kombination (6.10b, snö huvudlast) ökar största utjämnade stödmoment vid väggänden V15 "
                 f"(mjuka rör) från {f(fj[0]['mo'])} till " + " och ".join(f(k['mo']) for k in fj[1:]) +
                 f" kNm/m med {el(fj)} mm element vid väggändarna, och vid hörnet mot plattan på mark "
                 f"(styva rör) från {f(st_[0]['mo'])} till {f(st_[-1]['mo'])} kNm/m. Grundnätet 300 i stället för 200 mm "
                 f"ändrar {f(abs(h300['mo'] / fj[0]['mo'] - 1) * 100, 0)} %. Toppen kommer av att upplagslinjen är stel "
                 f"och slutar tvärt, och den konvergerar inte. Fältmomenten ändras högst {f(dmu * 100, 0)} % och "
                 f"rörlasterna högst {f(dP * 100, 1)} %.")
    _V = os.path.join(HERE, "vaggande.json")
    if os.path.exists(_V):
        Vg = json.load(open(_V))
        A15, AH = "V15 väggände", "hörn vid plattan på mark (LD4_2)"
        sel = lambda E, ror, k_: [v[k_] for v in Vg if v["E"] == E and v["ror"] == ror]
        rng = lambda a: f(min(a)) if f(min(a)) == f(max(a)) else f"{f(min(a))}–{f(max(a))}"
        dv = max(max(a) / min(a) - 1 for E in (5000.0, 2000.0) for a in (sel(E, "fjäder", A15), sel(E, "styv", AH)))
        D["konv"] += (f" Med väggarna som fjädrar med Lecans axialstyvhet E·t/h (inre skiktet 100 mm, höjd 2,6 m) "
                      f"blir momentet vid V15 {rng(sel(5000.0, 'fjäder', A15))} kNm/m med E = 5 000 MPa och "
                      f"{rng(sel(2000.0, 'fjäder', A15))} kNm/m med E = 2 000 MPa, och vid hörnet "
                      f"{rng(sel(5000.0, 'styv', AH))} respektive {rng(sel(2000.0, 'styv', AH))} kNm/m. Det ändras "
                      f"högst {f(dv * 100, 0)} % när elementen förfinas. Momenten vid väggändarna är alltså begränsade, och "
                      f"de stela linjerna ger värden på säker sida. Zonerna avgränsas med {f(ind['konv'], 1)} × FE-värdet "
                      f"och tilläggsjärnen dimensioneras för {f(ind['konv'] * ind['zon'], 1)} × FE-värdet, vilket också "
                      f"täcker den finaste indelningen med stela linjer ({f(fj[-1]['mo'])} mot {f(fj[0]['mo'])} kNm/m). "
                      f"Med fjädrande väggar och styva rör får rören mer last (P10 {rng(sel(2000.0, 'styv', 'P10'))} kN "
                      f"mot {f(st_[0]['P10'])} kN med stela väggar). Det fallet ingår därför i omhyllningen.")
else:
    D["konv"] = ""
_Y = os.path.join(HERE, "ytterskikt.json")
if os.path.exists(_Y):
    Y = json.load(open(_Y))
    D["ytter"] = dict(utan=f(Y["utan"]["mo_nara"]), med=f(Y["med"]["mo_nara"]), Y=f(Y["med"]["Y"], 0),
                      V=f(Y["med"]["V"], 0), Vu=f(Y["utan"]["V"], 0), zon=", ".join(Y["med"].get("zon", [])) or "–")

# ------------------------------------------------------------------ tvärkraft, nedböjning, sprickor
tv = R["tvarkraft"]
D["andar"] = [dict(vagg=f"V{a['vagg']}", x=f(a["x"] / 1e3, 2), y=f(a["y"] / 1e3, 2), V=f(a["V"] / 1e3), u=f(a["u"], 0),
                   vEd=f(a["vEd"], 2), vRd=f(a["vRdc"], 2), utn=pr(a["utn"])) for a in tv["andar"][:5]]
D["langs"] = dict(vEd=f(tv["langs"]["vEd"]), vRd=f(tv["langs"]["vRd"]), utn=pr(tv["langs"]["utn"]), d=f(tv["d"], 0),
                  vagg=f"V{tv['langs']['vagg']}")
nb = R["nedbojning"]
D["ned"] = dict(phi=f(nb["phi"], 2), ecs=f(nb["ecs"] * 1e3, 2), Eeff=f(nb["Eeff"] / 1e3, 1), wmax=f(nb["wmax"]),
                wkort=f(nb["wmax_kort"]), wspr=f(nb["wmax_spr"]),
                w=f(nb["ec2"]["w"]), L=f(nb["ec2"]["L"], 0), lim=f(nb["ec2"]["L"] / 250), utn=pr(nb["ec2"]["utn"]),
                w2=f(nb["sprucken"]["w"]), L2=f(nb["sprucken"]["L"], 0), lim2=f(nb["sprucken"]["L"] / 250),
                utn2=pr(nb["sprucken"]["utn"]))
sp = R["spricka"]
D["spr"] = [dict(lage="Underkant, fält", M=f(sp["uk"]["M"] / 1e3), s=f(sp["uk"]["sigma_s"], 0), wk=f(sp["uk"]["wk"], 2)),
            dict(lage="Överkant, bara nät", M=f(sp["ok_nat"]["M"] / 1e3), s=f(sp["ok_nat"]["sigma_s"], 0), wk=f(sp["ok_nat"]["wk"], 2)),
            dict(lage="Överkant, med tilläggsjärn", M=f(sp["ok_tillagg"]["M"] / 1e3), s=f(sp["ok_tillagg"]["sigma_s"], 0),
                 wk=f(sp["ok_tillagg"]["wk"], 2))]
D["spr_max"] = f(max(v["wk"] for v in sp.values()), 2)
mi = R["minarm"]
D["min"] = dict(uk=f(mi["uk"], 0), ok=f(mi["ok"], 0), uk_har=f(mi["uk_har"], 0), ok_har=f(mi["ok_har"], 0))
ro = R["ror"]
D["ror"] = dict(NbRd=f(ro["NbRd"] / 1e3, 0), lam=f(ro["lam"], 2), chi=f(ro["chi"], 2))
D["jv"] = {k: f(v, 0) for k, v in R["jamvikt"].items()}
ly = R["lyft"]
D["lyft"] = dict(mox=f(max(ly["mox"], ly["moy"]) / 1e3), Rmin=f(ly["Rmin"] / 1e3), namn=ly["Rmin_namn"],
                 utan=", ".join(ly.get("utan", [])),
                 ok_u=f(max(ly.get("mox_u", 0), ly.get("moy_u", 0)) / 1e3),
                 uk_u=f(max(ly.get("mux_u", 0), ly.get("muy_u", 0)) / 1e3),
                 utn=pr(max(ly.get("mox_u", 0) / b["ok"]["MRd_x"], ly.get("moy_u", 0) / b["ok"]["MRd_y"],
                            ly["mox"] / b["ok"]["MRd_x"], ly["moy"] / b["ok"]["MRd_y"])),
                 w=f(ly.get("w_upp", 0), 2))
# väggar
D["vr"] = [dict(namn=v["namn"], L=f(v["L"] / 1000, 2), typ=v["vagg"]["typ"], Gk=f(v["Gk"]), Qk=f(v["Qk"]), Sk=f(v["Sk"]),
                oG=f(v["ovan_G"]) if v["ovan_G"] > 0.05 else "–", oS=f(v["ovan_S"]) if v["ovan_S"] > 0.05 else "–",
                gm=f(v["Gk"] / v["L"] * 1000), qd=f(v["qd_max"])) for v in R["vaggar"]]
# handberäkning och SINTEF
k = R["kontroll"]
D["hand"] = dict(
    ror=[dict(namn=r["namn"], A=f(r["A"], 2), stolpar=", ".join(r["stolpar"]) or "–", Rd=f(r["Rd"]), FE=f(r["FE"]),
              avv=pr(r["FE"] / r["Rd"] - 1)) for r in k["ror"]],
    qd=f(k["qd"], 2), L=f(k["L"]), Mf=f(k["M_falt"]), Ms=f(k["M_stod"]), FEf=f(k["FE_falt"]),
    FEs=f"{f(k['FE_stod'][0])}–{f(k['FE_stod'][1])}", inre=", ".join(k["inre"]), EI2=f(k["EI2"], 2), w=f(k["w_strimla"]),
    wFE=f(k["w_FE"]), qk=f(k["qk"], 2), stod_namn=", ".join(k["FE_stod_namn"]),
    stod_zon=all(any(n in z["pelare"] for z in R["zoner"]) for n in k["FE_stod_namn"]))
si = k["sintef"]
D["sintef"] = dict(w1=f(si["w_ec2"]), u1=pr(si["utn_ec2"]), w2=f(si["w_kons"]), u2=pr(si["utn_kons"]), lim=f(si["lim"], 0))
# golvvärme
import golvvarme as GV  # noqa: E402
VR = GV.tabell()
lage = {50: "högt, 50 mm (under överkantsnätet)", 75: "mitt, 75 mm", 100: "lågt, 100 mm (på underkantsnätet)"}
D["varme"] = [dict(Tk=f(Tk, 0), lage=lage[d], Tw=f(r_["T_vatten"]), qn=f(r_["q_ned"], 0), andel=pr(r_["andel_ned"]),
                   Ty=f"{f(r_['Tyta_min'])}–{f(r_['Tyta_max'])}") for (d, Tk), r_ in VR.items()]
GV.rita(os.path.join(HERE, "fig_golvvarme.svg"), VR)

# figurer
F.np = np
F.rita_geometri(os.path.join(HERE, "fig_geometri.svg"), G)
F.rita_laster(os.path.join(HERE, "fig_laster.svg"), G, L)
F.rita_tvarsnitt(os.path.join(HERE, "fig_tvarsnitt.svg"), R)
D["n_diag"] = F.rita_armering(os.path.join(HERE, "fig_armering.svg"), G, R)
Fz = dict(np.load(os.path.join(HERE, "falt.npz")))
Nz = dict(np.load(os.path.join(HERE, "nedb.npz")))
F.rita_moment(os.path.join(HERE, "fig_moment.svg"), G, Fz, R)
F.rita_nedbojning(os.path.join(HERE, "fig_nedbojning.svg"), G, Nz, R)
json.dump(D, open(os.path.join(HERE, "rapport/data.json"), "w"), ensure_ascii=False, indent=1)

import typst  # noqa: E402
typst.compile(os.path.join(HERE, "rapport/mall.typ"), output=os.path.join(HERE, "rapport/K-05_mellanbjalklag.pdf"),
              font_paths=["/usr/share/fonts"], root=HERE)
print("K-05_mellanbjalklag.pdf")
