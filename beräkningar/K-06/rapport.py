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


D = {}
ind = R["indata"]
D["mat"] = dict(K0=f(ind["K0"], 2), fi=f(ind["fi"], 0), gamma=f(ind["gamma"], 0), q=f(ind["q"]), H=mm(ind["H"]),
                gM=f(ind["gM"]), gS=f(ind["gS"]), hfm=f(ind["h_fyll_mark"]), gmark=f(ind["g_mark"]),
                qmark=f(ind["q_mark"]), eps_mark=mm(I.EPS_MARK), svinn=f(I.SVINN_LECA * 1e3, 2),
                kryp=f(I.KRYP_LECA, 1), E_leca=mm(I.E_LECA), sv_mm=f(I.SVINN_LECA * I.H_VAGG, 2))
S = R["system"]
D["sys"] = {}
for s in ("A", "B"):
    x = S[s]
    D["sys"][s] = dict(namn=x["namn"], fk=f(x["fk"]), fxk1=f(x["fxk1"], 2), fxk2=f(x["fxk2"], 2), E=mm(1000 * x["fk"]),
                       arm=x["arm"], As=f(x["As_drag"]), d=f(x["d"], 0), fyk=mm(x["fyk"]),
                       mh1=f(x["mh"]["1"], 1), mh2=f(x["mh"]["2"], 1),
                       Asm1=mm(x["mh_detalj"]["1"]["As"]), z1=mm(x["mh_detalj"]["1"]["z"]),
                       vikt=f(x["vikt"], 2), skift=mm(x["skift"]))

# ------------------------------------------------------------------ väggar
ANDE = {"h": "hörn", "f": "fri"}
rows, stolp = [], []
for v in R["vaggar"]:
    fy = v["fyll"]
    _n = lambda h: 1 if abs(h - round(h, 1)) < 1e-9 else 2
    fyll = "–" if max(fy) <= 0 else (f(fy[0], _n(fy[0])) if abs(fy[0] - fy[1]) < 1e-9
                                     else f"{f(fy[0], _n(fy[0]))}–{f(fy[1], _n(fy[1]))}")
    r = dict(namn=v["namn"], L=f(v["L"], 2), fyll=fyll, typ=v["typ"], ande=f"{ANDE[v['ande'][0]]}/{ANDE[v['ande'][1]]}",
             vA=pr(v["A"]["vert"]["utn"]) if "vert" in v["A"] else "–",
             vB=pr(v["B"]["vert"]["utn"]) if "vert" in v["B"] else "–")
    if max(fy) > 0:
        A, B = v["A"], v["B"]
        r.update(regel="ja" if (v["regel"] and v["L"] <= v["regel"]["varannan"]) else "nej",
                 A2=f(A["2"]["lam0"], 2), A1=f(A["1"]["lam0"], 2), nA=str(A["1"]["stolpar"]),
                 B2=f(B["2"]["lam0"], 2), B1=f(B["1"]["lam0"], 2), nB=str(B["1"]["stolpar"]),
                 Rt=f(v["R_topp"]), Rb=f(v["R_botten"]), aterfyllt=True)
        for s in ("A", "B"):
            e = v[s]["1"]
            if e["stolpar"]:
                st = e["stolpe"]
                stolp.append(dict(sys=s, vagg=v["namn"], n=e["stolpar"], Lf=f(e["Lf"], 2), lam=f(e["lam"], 2),
                                  vkr=f"VKR {st['vkr'][0]}×{st['vkr'][0]}×{f(st['vkr'][1], 1)}", M=f(st["Mmax"]),
                                  MRd=f(st["MRd"]), utn=pr(st["utn"]), Rt=f(st["Rtop"]), Rb=f(st["Rbot"])))
    else:
        r.update(regel="", A2="", A1="", nA="", B2="", B1="", nB="", Rt="", Rb="", aterfyllt=False)
    rows.append(r)
D["vagg"] = rows
D["vagg_fyllda"] = [r for r in rows if r["aterfyllt"]]
_fasad = {n for f in I.FYLL.values() if "fasad" in f for n in f["fasad"]["omfattar"]}
D["vagg_ovriga"] = ", ".join(r["namn"] for r in rows if not r["aterfyllt"] and r["namn"] not in _fasad)
D["fasad"] = next(dict(namn=n, h=f(fv["h"][0], 2), L=f(next(v["L"] for v in R["vaggar"] if v["namn"] == n), 2))
                  for n, fv in I.FYLL.items() if "fasad" in fv)
_v18 = I.FYLL["V18"]["h"]
D["v18"] = dict(a=f(_v18[0], 2), b=f(_v18[1], 2))
D["stolp"] = stolp
D["nstolp"] = {s: sum(x["n"] for x in stolp if x["sys"] == s) for s in ("A", "B")}
D["stolp_vagg"] = {s: ", ".join(f"{x['vagg']} ({x['n']})" for x in stolp if x["sys"] == s) for s in ("A", "B")}
fyllda = [v for v in R["vaggar"] if max(v["fyll"]) > 0]
D["lamA"] = dict(min=f(min(v["A"]["1"]["lam"] for v in fyllda), 2))
D["lamB"] = dict(min=f(min(v["B"]["1"]["lam"] for v in fyllda), 2))
D["Rtop_max"] = f(max(v["R_topp"] for v in fyllda))
D["Rbot_max"] = f(max(v["R_botten"] for v in fyllda))
vmax = {s: max((v for v in R["vaggar"] if "vert" in v[s]), key=lambda v: v[s]["vert"]["utn"]) for s in ("A", "B")}
D["vert"] = {s: dict(namn=vmax[s]["namn"], utn=pr(vmax[s][s]["vert"]["utn"]), N=f(vmax[s][s]["vert"]["N"]),
                     NRd=f(vmax[s][s]["vert"]["NRd"]), Phi=f(vmax[s][s]["vert"]["Phi"], 2)) for s in ("A", "B")}
stmax = max((x for x in stolp), key=lambda x: float(x["utn"].rstrip(" %")))
D["stolp_max"] = stmax
# stolparnas infästning: foten trycker mot fickans kant (50 mm hög, stolpens bredd 100 mm), toppen M12 8.8 i
# avlånga hål, dubbelskäriga (två flattstål), och fyra svetsbultar Ø13 × 75 i bjälklaget (SS-EN 1994-1-1 6.6.3.1)
Rb_st = max(float(x["Rb"].replace(",", ".")) for x in stolp)
Rt_st = max(float(x["Rt"].replace(",", ".")) for x in stolp)
sig_fot = Rb_st * 1e3 / (100 * 50)
fcd = 25 / 1.5
FvM12 = 2 * 0.6 * 800 * 84.3 / 1.25 / 1e3
_d13 = 13.0
dym = 4 * min(0.8 * 450 * math.pi * _d13 ** 2 / 4, 0.29 * _d13 ** 2 * math.sqrt(25 * 31476)) / 1.25 / 1e3
D["stolpfast"] = dict(Rb=f(Rb_st), Rt=f(Rt_st), sig=f(sig_fot), fcd=f(fcd), utn_fot=pr(sig_fot / fcd),
                      Fv=f(FvM12, 0), dym=f(dym, 0), utn_topp=pr(Rt_st / min(FvM12, dym)))
_Y = json.load(open(os.path.join(I.K05, "ytterskikt.json"), encoding="utf-8"))["med"]
# LD4_2 (K-05: 44 kN dimensionerande, i hörnet V2/V20): spridning 45° genom bjälklaget och U-blocket
from shapely.geometry import box as _box
from shapely.ops import unary_union as _uu
F42, a42, h42 = 44.0, 95.0, 150.0 + 197.0
r42 = 30 + a42 + h42                       # från Lecans ytterliv (bjälklagets kant 30 mm innanför)
yttre = _uu([_box(0, 0, 100, r42), _box(0, 0, r42, 100)])
inre_ = _uu([_box(250, 250, 350, r42), _box(250, 250, r42, 350)])
A42 = (yttre.union(inre_)).intersection(_box(0, 0, r42, r42)).area
vV2 = next(v for v in R["vaggar"] if v["namn"] == "V2")
sig42 = F42 * 1e3 / A42
sigV2 = vV2["A"]["vert"]["N"] / I.T_SKIKT
fdA, fdB = I.SYSTEM["A"]["fk"] / I.GAMMA_M_MUR, I.SYSTEM["B"]["fk"] / I.GAMMA_M_MUR
D["ld42"] = dict(F=f(F42), h=mm(h42), A=mm(A42 / 1e3), sig=f(sig42, 2), sigV2=f(sigV2, 2), tot=f(sig42 + sigV2, 2),
                 fdA=f(fdA, 2), fdB=f(fdB, 2), utnA=pr((sig42 + sigV2) / fdA), utnB=pr((sig42 + sigV2) / fdB),
                 andel=pr(_Y["Y"] / (_Y["Y"] + _Y["V"])))
# förankring i toppen: Ø10 s600 i U-blocket (skjuvning i stången, f_yd/√3)
Rt = max(v["R_topp"] for v in fyllda)
VRd_bar = math.pi * 25 * 435 / math.sqrt(3) / 1e3
D["topp"] = dict(Rt=f(Rt), VRd=f(VRd_bar), utn=pr(Rt * 0.6 / VRd_bar), s="600")

# ------------------------------------------------------------------ bottenplatta
P = R["platta"]
D["platta"] = {}
for u in ("L300", "L400"):
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
        eps_3=(dict(uls=f(e["s300"]["uls"], 0), perm=f(e["s300"]["perm"], 0), qp=f(e["s300"]["qp"], 0),
                    fdM=f(e["s300"]["fdM"], 0), fdP=f(e["s300"]["fdP"], 0), kryp=f(e["s300"]["kryp"], 0),
                    utn=pr(e["s300"]["utn"])) if "s300" in e else
               dict(uls="–", perm="–", qp="–", fdM=f(e["S300"]["fdM"], 0), fdP=f(e["S300"]["fdP"], 0),
                    kryp=f(e["S300"]["kryp"], 0), utn="–")),
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
D["balkar"] = [dict(namn=b["namn"].replace("kant ", "K"), vagg=b["vagg"], L=f(b["L"] / 1000, 2),
                    Ms3=f(b["Msag"]), Mh3=f(b["Mhog"]), V3=f(b["V"]),
                    Ms4=f(b4["Msag"]), Mh4=f(b4["Mhog"]), V4=f(b4["V"]))
               for b, b4 in zip(p3["balkar"], P["L400"]["balkar"])]
ror = p3["ror"]
okade = [x for x in ror if x["kvot"] > 1.0]
D["ror"] = dict(max_kvot=pr(max(x["kvot"] for x in ror) - 1), namn=max(ror, key=lambda x: x["kvot"])["namn"],
                okade=", ".join(f"{x['namn']} {f(x['N'], 0)}/{f(x['N05'], 0)}" for x in okade),
                lag=pr(max(x["lag"] for x in ror)), lag_namn=max(ror, key=lambda x: x["lag"])["namn"])
gl = R["glidning"]
D["glid"] = dict(Fx=f(gl["Fx"], 0), Fy=f(-gl["Fy"], 0), Fd=f(gl["Fd"], 0), G=f(gl["G"], 0), my=f(gl["my"], 1),
                 Rd=f(gl["Rd"], 0), utn=pr(gl["utn"]))
D["plint_bredd"] = f"{mm(min(p3['plint']))}–{mm(max(p3['plint']))}"

# ------------------------------------------------------------------ kontroll av beräkningarna
H = I.H_VAGG / 1000
ones = lambda X, Y: np.ones_like(Y)
VG.H, Hs = 1.0, VG.H
l1 = VG.brottlinje(1.0, ones, 1.0, 0, 0, 1.0, ("h", "h"), n=200)[0]
VG.H = 1.0
l2 = VG.brottlinje(2.0, ones, 1.0, 0, 0, 1.0, ("h", "h"), n=200)[0]
r_ = 0.5
l2x = 24 / (math.sqrt(3 + r_ ** 2) - r_) ** 2
VG.H = 2.0
l3 = VG.brottlinje(4.0, ones, 1.0, 1.0, 1.0, 0.0, ("h", "h"), n=200)[0]
VG.H = Hs
D["valid"] = dict(l1=f(l1, 2), l2=f(l2, 2), l2x=f(l2x, 2), l3=f(l3 * 16 / 16, 3))
e3 = p3["eps"]["balk"]
Ed = I.EPS_KS * I.EPS["S200"]["Ek"] / 1000          # MPa
D["valid"].update(w_hand=f(e3["qp"] * 1e-3 * I.T_FOT / Ed + 0, 2), w_fe=f(p3["sattning"]["wmax"], 2),
                  sig=f(e3["qp"], 0), Ed=f(Ed * 1000, 0))
L3 = pickle.load(open(os.path.join(HERE, "res06_L300_lång.pkl"), "rb"))
K3 = pickle.load(open(os.path.join(HERE, "res06_L300_kort.pkl"), "rb"))
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
# kapacitetskurvor vid 2,0 m fyllning (vägg V1:s normalkraft)
kurvor = {}
for s in ("A", "B"):
    for var in (1, 2):
        Ls = np.arange(1.5, 8.01, 0.5)
        lam = []
        for L_ in Ls:
            v = dict(namn="V1", L=L_, fyll=(2.0, 2.0), ande=("h", "h"), platta=False)
            lam.append(VG.kontroll(v, s, var, 0)[0])
        kurvor[(s, var)] = (Ls, lam)
# längsta vägg med λ ≥ 1 (V1:s normalkraft, 2,0 m fyllning, hörn i båda ändar), linjär interpolation på 0,1 m
Lgr = {}
for s in ("A", "B"):
    for var in (1, 2):
        Ls = np.arange(1.5, 7.01, 0.1)
        lam = np.array([VG.kontroll(dict(namn="V1", L=L_, fyll=(2.0, 2.0), ande=("h", "h"), platta=False), s, var, 0)[0]
                        for L_ in Ls])
        i = int(np.argmax(lam < 1.0))
        Lgr[f"{s}{var}"] = f(Ls[i - 1] + (lam[i - 1] - 1) / (lam[i - 1] - lam[i]) * 0.1, 1)
D["Lgrans"] = Lgr
FG.rita_kapacitet(os.path.join(HERE, "fig_kapacitet.svg"), kurvor,
                  [(v["namn"], v["L"]) for v in R["vaggar"] if max(v["fyll"]) >= 1.7 and v["L"] <= 8])

# ------------------------------------------------------------------ figurer
poly = M.kallare()
FG.rita_kallare(os.path.join(HERE, "fig_kallare.svg"), R, poly)
_, kant, inre, _ = M.balkar(p3["plint"])
FG.rita_bottenplatta(os.path.join(HERE, "fig_bottenplatta.svg"), R, poly, kant, inre, p3["plint"])
FG.rita_detalj(os.path.join(HERE, "fig_detalj_A.svg"), "A")
FG.rita_detalj(os.path.join(HERE, "fig_detalj_B.svg"), "B")
FG.rita_lokala(os.path.join(HERE, "fig_lokala.svg"))
tj = __import__("shapely.ops", fromlist=["unary_union"]).unary_union([kant, inre, M.balkar(p3["plint"])[3]])
import kontroll06 as KO  # noqa: E402
L3m, K3m = KO.las("L300", "lång"), KO.las("L300", "kort")          # omhyllande med varianten (båda vangarna)
FG.rita_tryck(os.path.join(HERE, "fig_tryck.svg"), L3["xy_b"], L3["tri_b"],
              np.maximum(L3m["env"]["p_max"], K3m["env"]["p_max"]), L3["sls"]["wb_qp"], poly, tj)
json.dump(D, open(os.path.join(HERE, "rapport/data.json"), "w"), ensure_ascii=False, indent=1)

import typst  # noqa: E402
typst.compile(os.path.join(HERE, "rapport/mall.typ"), output=os.path.join(HERE, "rapport/K-06_grund.pdf"),
              font_paths=["/usr/share/fonts", os.path.join(os.path.dirname(HERE), ".fonts")], root=HERE)
print("K-06_grund.pdf")
