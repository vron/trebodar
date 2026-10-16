"""
Sätter ihop K-06 som PDF: läser resultat.json (berakning.py), ritar figurerna och kompilerar rapport/mall.typ.
"""
import json
import math
import os
import pickle

import numpy as np

import indata as I
import vaggar as VG
import modell06 as M
import figurer06 as FG

HERE = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(HERE, "resultat.json"), encoding="utf-8"))


def f(x, n=1):
    s = f"{x:,.{n}f}".replace(",", " ").replace(".", ",")
    return s.replace("-", "−")


def pr(x):
    return f"{x * 100:.0f} %"


def mm(x):
    return f"{x:,.0f}".replace(",", " ")


def jarn(a):
    return f"Ø{a[0]} s{a[1]}"


D = {}
ind = R["indata"]
VP = I.VIBROPLATTA
D["mat"] = dict(K0=f(ind["K0"], 2), KA=f(ind["KA"], 2), fi=f(ind["fi"], 0), gamma=f(ind["gamma"], 0), q=f(ind["q"]),
                H=mm(ind["H"]), Ls=f(ind["Ls"], 3), hfm=f(ind["h_fyll_mark"]), gmark=f(ind["g_mark"]),
                qmark=f(ind["q_mark"]), eps_mark=mm(I.EPS_MARK), komp=f(ind["sig_komp"], 0), P=f(ind["P_platta"], 0),
                vp_m=mm(VP["massa"]), vp_F=f(VP["F"], 0), vp_b=f(VP["b"], 1), lager=f(I.LAGER_FYLL, 1),
                gbygg=f(ind["g_bygg"], 2), qbygg=f(ind["q_bygg"], 2), e=mm(ind["e_topp"] * 1000),
                e_ut=f(ind["e_topp"] * 1000 - I.T_KARNA / 2, 1), fck=f(I.FCK_V, 0), kryp=f(I.KRYP_V, 1),
                svinn=f(I.SVINN_V * 1e3, 2), sv_mm=f(I.SVINN_V * I.H_VAGG, 2), gkub=f(I.G_KUB, 2), gsten=f(I.G_STEN, 1),
                c_in=mm(I.C_IN), c_ut=mm(I.C_UT), gjut1=mm(I.H_GJUT1), skarv=mm(I.SKARV), Ecm=mm(round(M.BV.Ecm, -2)),
                Ev_l=mm(round(M.BV.Ecm / (1 + I.KRYP_V), -2)))
arm = R["arm"]
D["arm"] = dict(txt=jarn(arm), d=str(arm[0]), s=str(arm[1]), As=mm(VG.As(*arm)), dv=mm(VG.d_lodrat(arm[0])),
                MRd=f(VG.MRd(VG.As(*arm), VG.d_lodrat(arm[0]))), MRd300=f(VG.MRd(VG.As(10, 300), VG.d_lodrat(10))),
                dh=mm(VG.D_H_IN), start=f"Ø{I.STARTJARN['d']} s{I.STARTJARN['s']}")

# ------------------------------------------------------------------ väggar
ANDE = {"h": "hörn", "f": "fri"}
rows = []
for v in R["vaggar"]:
    fy = v["fyll"]
    _n = lambda h: 1 if abs(h - round(h, 1)) < 1e-9 else 2
    fyll = "–" if max(fy) <= 0 else (f(fy[0], _n(fy[0])) if abs(fy[0] - fy[1]) < 1e-9
                                     else f"{f(fy[0], _n(fy[0]))}–{f(fy[1], _n(fy[1]))}")
    r = dict(namn=v["namn"], L=f(v["L"], 2), fyll=fyll, typ=v["typ"], aterfyllt=max(fy) > 0)
    if "dim" in v:
        d = v["dim"]
        r.update(M=f(d["M"]), Mj=f(d["Mjord"]), Mt=f(d["M_topp"]), MRd=f(d["MRd"]), utnM=pr(d["utn_M"]),
                 V=f(max(d["Rb"], d["Rt"])), VRd=f(d["VRd"], 0), utnV=pr(d["utn_V"]), Rt=f(d["Rt"]), Rb=f(d["Rb"]),
                 min=jarn(d["arm_min"]), fog=pr(d["fog_botten"]["utn"]))
    rows.append(r)
D["vagg_fyllda"] = [r for r in rows if r["aterfyllt"]]
_fasad = {n for fv in I.FYLL.values() if "fasad" in fv for n in fv["fasad"]["omfattar"]}
D["vagg_ovriga"] = ", ".join(r["namn"] for r in rows if not r["aterfyllt"] and r["namn"] not in _fasad)
fyllda = [v for v in R["vaggar"] if "dim" in v]
vmax = max(fyllda, key=lambda v: v["dim"]["utn_M"])
D["vmax"] = dict(namn=vmax["namn"], utn=pr(vmax["dim"]["utn_M"]), M=f(vmax["dim"]["M"]), MRd=f(vmax["dim"]["MRd"]),
                 y=f(vmax["dim"]["y"], 2), Mt=f(vmax["dim"]["M_topp"]), utnV=pr(max(v["dim"]["utn_V"] for v in fyllda)),
                 fog=pr(max(v["dim"]["fog_botten"]["utn"] for v in fyllda)),
                 utn300=pr(vmax["dim"]["M"] / VG.MRd(VG.As(10, 300), VG.d_lodrat(10))),
                 Rt=f(max(v["dim"]["Rt"] for v in fyllda)), Rb=f(max(v["dim"]["Rb"] for v in fyllda)))
fv = next(v for v in R["vaggar"] if v.get("fasad"))
fd = fv["fasad_d"]
D["fasad"] = dict(namn=fv["namn"], h=f(fv["fyll"][0], 2), L=f(fv["L"], 2), M=f(fv["dim"]["M"]),
                  pel=[dict(namn=p["namn"], b=f(p["b"], 2), faktor=f(p["faktor"], 2), M=f(p["M"])) for p in fd["pelare"]],
                  Mmax=f(max(p["M"] for p in fd["pelare"])), utn=pr(max(p["M"] for p in fd["pelare"]) /
                                                                     VG.MRd(VG.As(*arm), VG.d_lodrat(arm[0]))),
                  oppn=f(fd["oppning"], 2), p=f(fd["p"]), Mb=f(fd["M_brostning"], 2), MRdb=f(fd["MRd_brostning"]),
                  bro=" och ".join(f(b, 2) for b in I.BROSTNING))
# jämförelse: utan packningstrycket (bara vilojordtryck), 2,0 m fyllning
_s0 = I.SIG_KOMP
I.SIG_KOMP = 0.0
D["mat"]["M_K0"] = f(VG.strimla(2.0, 0.0, I.Q_MARK)["M"])
I.SIG_KOMP = _s0
D["mat"]["M_komp"] = f(VG.strimla(2.0, 0.0, I.Q_MARK)["M"])
_v18 = I.FYLL["V18"]["h"]
D["v18"] = f(_v18[0], 1)
D["v1"] = f(I.FYLL["V1"]["h"][0], 1)
# vertikal last
yv = [v for v in R["vaggar"] if "vert" in v and v["vert"]["metod"] == "armerad"]
iv = [v for v in R["vaggar"] if "vert" in v and v["vert"]["metod"] == "oarmerad"]
ym = max(yv, key=lambda v: v["vert"]["utn"])
im = max(iv, key=lambda v: v["vert"]["utn"])
nm = max(R["vaggar"], key=lambda v: v.get("vert", {}).get("N", 0))
D["vert"] = dict(ynamn=ym["namn"], yN=f(ym["vert"]["N"]), yutn=pr(ym["vert"]["utn"]), yM=f(ym["vert"]["M"]),
                 yMRd=f(ym["vert"]["MRd"]), inamn=im["namn"], iN=f(im["vert"]["N"]), iNRd=f(im["vert"]["NRd"], 0),
                 iutn=pr(im["vert"]["utn"]), Phi=f(im["vert"]["Phi"], 2), Nmax=f(nm["vert"]["N"]), Nnamn=nm["namn"],
                 lam=f(ym["vert"]["lam"], 0), lam_lim=f(min(v["vert"]["lam_lim"] for v in yv if "dim" in v), 0),
                 M2=", ".join(v["namn"] for v in yv if v["vert"]["M2"] > 0) or "inga")
h = R["hornlast"]
D["horn"] = dict(F=f(h["F"], 0), av=mm(h["av"]), ax=mm(h["ax"]), ay=mm(h["ay"]), d=mm(h["d"]), u=mm(h["u"]),
                 beta=f(h["beta"], 2), VRdmax=f(h["VRdmax"], 0), VRdc=f(h["VRdc"], 0), utn_max=pr(h["utn_max"]),
                 utn_c=pr(h["utn_c"]), T=f(h["T"]), TRd=f(h["TRd"], 0), utn_T=pr(h["utn_T"]),
                 utn=pr(max(h["utn_max"], h["utn_c"], h["utn_T"])))
# toppens moment av linjelasterna över väggarna: konsol i plattan till kärnans yta
qo = max(v["dim"]["q_ovan"] for v in fyllda)
D["kant"] = dict(q=f(qo), M=f(qo * (ind["e_topp"] - I.T_KARNA / 2000), 2), MRd=f(VG.MRd(VG.As(8, 150), 150 - 25 - 12, 25)))
# fogen vid 1 800 i färdigt läge
V18 = max(v["dim"]["V18"] for v in fyllda)
fog18 = VG.fog(V18, 0.0, VG.As(*arm), 0.7 * 0.3 * I.FCK_V ** (2 / 3) / 1.5, I.FCK_V / 1.5)
D["fog"] = dict(V18=f(V18), utn18=pr(fog18["utn"]), vr18=f(fog18["vr"], 2),
                utnb=pr(max(v["dim"]["fog_botten"]["utn"] for v in fyllda)),
                vrb=f(min(v["dim"]["fog_botten"]["vr"] for v in fyllda), 2))

# ------------------------------------------------------------------ byggskedet
B = R["bygg"]
A3, A20 = B["A"]["vaggar"]["V3"], B["A"]["vaggar"]["V20"]
vv = {v["namn"]: v for v in VG.vaggar()}
regel = B["regel"]
t_r = regel["t_eq"]["N"]
b3r = VG.bygg_v(vv["V3"], t_r, lodrat=tuple(arm))
_h = VG.BYGG_HOR["V3"]
VG.BYGG_HOR["V3"] = (10, 600)
b3s = VG.bygg_v(vv["V3"], 28.0, lodrat=tuple(arm))
VG.BYGG_HOR["V3"] = _h
D["bygg"] = dict(
    lam3=f(A3["f28"]["lam"], 2), lam20=f(A20["f28"]["lam"], 2), lam3_r=f(b3r["lam"], 2), lam3_std=f(b3s["lam"], 2),
    mh3=f(A3["f28"]["mh"]), mhn3=f(A3["f28"]["mhn"]), mv3=f(A3["f28"]["mv"]),
    sig=f(A3["f28"]["sig"], 0), lb=mm(A3["f28"]["lb"]), l0=mm(A3["f28"]["l0"]),
    V3=f(A3["f28"]["V"]), VRd3=f(A3["f28"]["VRd"], 0),
    hor3=jarn(VG.BYGG_HOR["V3"]), hor20=jarn(VG.BYGG_HOR["V20"]),
    fckA=f(B["A"]["fck"]), fckB=f(B["B"]["fck"]), vaggB=B["B"]["vagg"],
    regel=f(regel["fck"], 0), fcm=f(regel["fcm"], 0), andel=pr(regel["andel"]),
    sigB=f(B["B"]["f28"]["sig"], 0),
    dygn=[dict(T=f(float(T), 0), N=f(math.ceil(regel["dygn"]["N"][T]), 0), R=f(math.ceil(regel["dygn"]["R"][T]), 0),
               fN=f(math.ceil(B["frys"]["N"][T]), 0) + " dygn", fR=f(math.ceil(B["frys"]["R"][T]), 0) + " dygn")
          for T in regel["dygn"]["N"]],
    teqN=f(regel["t_eq"]["N"], 1), teqR=f(regel["t_eq"]["R"], 1),
)
D["bygg"]["d5N"] = D["bygg"]["dygn"][0]["N"]
D["bygg"]["d10N"] = D["bygg"]["dygn"][1]["N"]
D["bygg"]["d20N"] = D["bygg"]["dygn"][3]["N"]
D["bygg"]["d10R"] = D["bygg"]["dygn"][1]["R"]

# ------------------------------------------------------------------ bottenplatta
P = R["platta"]
D["platta"] = {}
for u in I.UTFORANDEN:
    p = P[u]
    e = p["eps"]
    bk = p["balkar"]
    kant = [b for b in bk if b["kant"]]
    inre = [b for b in bk if not b["kant"]]
    pl = p["plintar"]
    t = p["topp"]
    D["platta"][u] = dict(
        h=mm(p["h"]),
        eps_b=dict(uls=f(e["balk"]["uls"], 0), medel=f(e["balk"]["uls_medel"], 0), fdM=f(e["balk"]["fdM"], 0),
                   perm=f(e["balk"]["perm"], 0), fdP=f(e["balk"]["fdP"], 0), qp=f(e["balk"]["qp"], 0),
                   kryp=f(e["balk"]["kryp"], 0), utn=pr(max(e["balk"]["uls_medel"] / e["balk"]["fdM"],
                                                            e["balk"]["perm"] / e["balk"]["fdP"],
                                                            e["balk"]["qp"] / e["balk"]["kryp"]))),
        eps_3=dict(uls=f(e["s300"]["uls"], 0), perm=f(e["s300"]["perm"], 0), qp=f(e["s300"]["qp"], 0),
                   fdM=f(e["s300"]["fdM"], 0), fdP=f(e["s300"]["fdP"], 0), kryp=f(e["s300"]["kryp"], 0),
                   utn=pr(e["s300"]["utn"])),
        eps_f=dict(uls=f(e["falt"]["uls"], 0), fdM=f(e["falt"]["fdM"], 0), perm=f(e["falt"]["perm"], 0),
                   fdP=f(e["falt"]["fdP"], 0), qp=f(e["falt"]["qp"], 0), kryp=f(e["falt"]["kryp"], 0),
                   utn=pr(e["falt"]["utn"])),
        w=dict(max=f(p["sattning"]["wmax"], 1), min=f(p["sattning"]["wmin"], 1),
               ror=f"{f(p['sattning']['ror_min'], 1)}–{f(p['sattning']['ror_max'], 1)}",
               vagg=f"{f(p['sattning']['vagg_min'], 1)}–{f(p['sattning']['vagg_max'], 1)}",
               skillnad=f(p["sattning"]["skillnad"], 1)),
        falt=dict(mu=f(p["falt"]["mu_ra"]), mo=f(p["falt"]["mo_ra"]), MRu=f(p["falt"]["MRu"]), MRo=f(p["falt"]["MRo"]),
                  utn=pr(p["falt"]["utn_ra"]), d=mm(p["falt"]["d"]), topp=f(p["falt"]["topp_mu"])),
        kant=dict(Ms=f(max(b["Msag"] for b in kant)), Mh=f(max(b["Mhog"] for b in kant)), V=f(max(b["V"] for b in kant)),
                  MRd=f(kant[0]["uk"]["MRd"]), MRo=f(kant[0]["ok"]["MRd"]),
                  utnV=pr(max(b["skjuv"]["utn"] for b in kant)), VRd=f(kant[0]["skjuv"]["VRdc"]),
                  utnM=pr(max(max(b["Msag"] / b["uk"]["MRd"], b["Mhog"] / b["ok"]["MRd"]) for b in kant))),
        inre=dict(Ms=f(max(b["Msag"] for b in inre)), Mh=f(max(b["Mhog"] for b in inre)), V=f(max(b["V"] for b in inre)),
                  utnM=pr(max(max(b["Msag"] / b["uk"]["MRd"], b["Mhog"] / b["ok"]["MRd"]) for b in inre)),
                  utnV=pr(max(b["skjuv"]["utn"] for b in inre))),
        plint=dict(stans=pr(max(x["utn_stans"] for x in pl)), namn=max(pl, key=lambda x: x["utn_stans"])["namn"],
                   ute=pr(max(x["utn_ute"] for x in pl)), ute_namn=max(pl, key=lambda x: x["utn_ute"])["namn"],
                   max=pr(max(max(x["utn_stans"], x["utn_ute"]) for x in pl)),
                   boj=pr(max(x["utn_boj"] for x in pl)), Nmax=f(max(x["N"] for x in pl)),
                   d=mm(pl[0]["d"]), dt=mm(pl[0]["ute"]["d"]), beff=mm(pl[0]["beff"])),
        kant_d=dict(uk=mm(kant[0]["d_uk"]), ok=mm(kant[0]["d_ok"])),
        topp=dict(ok=pr(t["u_ok"]), uk=pr(t["u_uk"]), ok5=pr(t["u5_ok"]), uk5=pr(t["u5_uk"])),
        svinn=f(p["svinn"]["m_max"]),
        mark=dict(uls=f(p["mark"]["uls"], 0), fdM=f(p["mark"]["fdM"], 0), qp=f(p["mark"]["qp"], 0),
                  kryp=f(p["mark"]["kryp"], 0), utn=pr(max(p["mark"]["uls"] / p["mark"]["fdM"],
                                                          p["mark"]["qp"] / p["mark"]["kryp"]))),
    )
p3 = P["L300"]
D["plintar"] = [dict(namn=x["namn"], b=mm(x["b"]), N=f(x["N"]), p=f(x["p"], 0), stans=pr(x["utn_stans"]),
                     ute=pr(x["utn_ute"]), boj=pr(x["utn_boj"])) for x in p3["plintar"]]
ror = p3["ror"]
okade = [x for x in ror if x["kvot"] > 1.0]
D["ror"] = dict(max_kvot=pr(max(x["kvot"] for x in ror) - 1), namn=max(ror, key=lambda x: x["kvot"])["namn"],
                okade=", ".join(f"{x['namn']} {f(x['N'], 0)}/{f(x['N05'], 0)}" for x in okade),
                lag=pr(max(x["lag"] for x in ror)), lag_namn=max(ror, key=lambda x: x["lag"])["namn"])
vg = p3["vaggar"]
D["vagglast"] = dict(storre=", ".join(x["namn"] for x in vg if x["q"] > x["q05"] + 0.05) or "inga")
gl = R["glidning"]
D["glid"] = dict(Fx=f(gl["K0"]["Fx"], 0), Fy=f(-gl["K0"]["Fy"], 0), Fd=f(gl["K0"]["Fd"], 0), G=f(gl["G"], 0),
                 my=f(gl["my"], 1), Rd=f(gl["Rd"], 0), utn=pr(gl["K0"]["utn"]), Fdk=f(gl["komp"]["Fd"], 0),
                 utnk=pr(gl["komp"]["utn"]))
D["plint_bredd"] = f"{mm(min(p3['plint']))}–{mm(max(p3['plint']))}"
D["horn_s300"] = str(len(M.yttre_horn()))

# ------------------------------------------------------------------ kontroll av beräkningarna
ones = lambda X, Y: np.ones_like(Y)
l1 = VG.brottlinje(1.0, 1.0, ones, 1.0, 0, 0, 1.0, ("h", "h"), n=200)[0]
l2 = VG.brottlinje(2.0, 1.0, ones, 1.0, 0, 0, 1.0, ("h", "h"), n=200)[0]
r_ = 0.5
l2x = 24 / (math.sqrt(3 + r_ ** 2) - r_) ** 2
l3 = VG.brottlinje(4.0, 2.0, ones, 1.0, 1.0, 1.0, 0.0, ("h", "h"), n=200)[0]
# platta med fri överkant, tre sidor ledat upplagda, lika moment: Johansen ger q L² / m för kvadraten (fri kant)
D["valid"] = dict(l1=f(l1, 2), l2=f(l2, 2), l2x=f(l2x, 2), l3=f(l3, 3))
# strimlan mot handberäkning: jämnt tryck σ över hela höjden ger M = q L² / 8
pk = 10.0
ys = np.linspace(0, VG.LS, 2001)
Mh = pk * VG.LS ** 2 / 8
D["valid"].update(Ms=f(Mh, 2))
e3 = p3["eps"]["balk"]
Ed = I.EPS_KS * I.EPS["S200"]["Ek"] / 1000          # MPa
D["valid"].update(w_hand=f(e3["qp"] * 1e-3 * I.T_FOT / Ed + 0, 2), w_fe=f(p3["sattning"]["wmax"], 2),
                  sig=f(e3["qp"], 0), Ed=f(Ed * 1000, 0))
# hållfasthetstillväxt: β_cc(7) för N-cement (SS-EN 1992-1-1 3.1.2), och mognadsfaktorn vid 10 °C
D["valid"].update(b7=f(math.exp(0.25 * (1 - math.sqrt(28 / 7))), 3), m10=f(VG.mognad(10.0), 3),
                  f7=f(VG.fck_t(7.0), 1))
L3 = pickle.load(open(os.path.join(HERE, "res06_L300_lång.pkl"), "rb"))
jv = L3["env"].get("jamvikt", {})
JNAMN = {"G": "egentyngd", "S_V": "snö V", "S_M": "snö M", "S_H": "snö H", "Qb": "nyttig last i källaren"}
D["jamvikt"] = [dict(namn=JNAMN.get(k, k), last=f(v["last"], 0), R=f(v["reaktion"], 0)) for k, v in jv.items()]
_NK = os.path.join(HERE, "natkonvergens.json")
if os.path.exists(_NK):
    nk = json.load(open(_NK))
    a, b = nk
    dr = max(abs(b["ror"][k] / a["ror"][k] - 1) for k in a["ror"] if a["ror"][k] > 5)
    D["nat"] = dict(ne1=mm(a["ne"]), ne2=mm(b["ne"]), p1=f(a["pmax"]), p2=f(b["pmax"]), w1=f(a["wmax"], 2),
                    w2=f(b["wmax"], 2), dr=f(dr * 100, 1))
else:
    D["nat"] = None

# ------------------------------------------------------------------ figurer
poly = M.kallare()
FG.rita_kallare(os.path.join(HERE, "fig_kallare.svg"), R, poly)
_, kant, inre, _ = M.balkar(p3["plint"])
FG.rita_bottenplatta(os.path.join(HERE, "fig_bottenplatta.svg"), R, poly, kant, inre, p3["plint"])
FG.rita_detalj(os.path.join(HERE, "fig_detalj.svg"), tuple(arm))
FG.rita_lokala(os.path.join(HERE, "fig_lokala.svg"))
# jordtryck och moment för en vägg med 2,0 m fyllning (V2: störst moment med lasterna över väggen)
v2 = next(v for v in R["vaggar"] if v["namn"] == vmax["namn"])
hf = v2["dim"]["hf"]
yy = np.linspace(0, VG.LS, 400)
z = np.clip(hf - yy, 0, None)
gG, gQ = VG.ULS_JORD["6.10a"]
s = VG.strimla(hf, 0.0, I.Q_MARK, v2["dim"]["M_topp"])
FG.rita_jordtryck(os.path.join(HERE, "fig_jordtryck.svg"), dict(
    y=yy, hf=hf, Ls=VG.LS, K0=np.where(z > 0, I.K0 * I.GAMMA_JORD * z, 0), komp=VG.sig_jord(z),
    p_d=VG.tryck_fn(hf, 0.0, I.Q_MARK, gG, gQ)(yy), ym=s["ys"], M=s["Mlinje"],
    MRd=[(VG.MRd(VG.As(10, 300), VG.d_lodrat(10)), "$M_{Rd}$, Ø10 s300 (TG 2216)", "--"),
         (VG.MRd(VG.As(*arm), VG.d_lodrat(arm[0])), f"$M_{{Rd}}$, {jarn(arm)}", "-")]))
FG.rita_hardning(os.path.join(HERE, "fig_hardning.svg"), VG.fck_t, VG.mognad, regel["fck"], 5.0)
tj = __import__("shapely.ops", fromlist=["unary_union"]).unary_union([kant, inre, M.balkar(p3["plint"])[3]])
import kontroll06 as KO  # noqa: E402
L3m, K3m = KO.las("L300", "lång"), KO.las("L300", "kort")
pmax = np.maximum(L3m["env"]["p_max"], K3m["env"]["p_max"])
FG.rita_tryck(os.path.join(HERE, "fig_tryck.svg"), L3["xy_b"], L3["tri_b"], pmax, L3["sls"]["wb_qp"], poly, tj,
              p_max=5 * math.ceil(float(np.percentile(pmax, 99.9)) / 5),
              w_niv=np.round(np.arange(np.floor(L3["sls"]["wb_qp"].min() * 10) / 10,
                                       L3["sls"]["wb_qp"].max() + 0.1, 0.1), 2))
json.dump(D, open(os.path.join(HERE, "rapport/data.json"), "w"), ensure_ascii=False, indent=1)

import typst  # noqa: E402
typst.compile(os.path.join(HERE, "rapport/mall.typ"), output=os.path.join(HERE, "rapport/K-06_grund.pdf"),
              font_paths=["/usr/share/fonts", os.path.join(os.path.dirname(HERE), ".fonts")], root=HERE)
print("K-06_grund.pdf")
