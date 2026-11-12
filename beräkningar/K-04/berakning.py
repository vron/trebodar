"""
K-04: trästommen och stabiliseringen enligt EKS 12, SS-EN 1995-1-1 och SS-EN 1993-1-1/-1-3.

    python berakning.py      # -> K-04_trastomme.pdf

Läser modellens bärverk (../../modeller/trebodar/ut/barverk.json, `./mod barverk` i verktyg/modellering), F-01:s
laster (../F-01/indata.toml), K-05:s stolplaster (../K-05/resultat.json) och indata.toml. Bygger balkmodellen
(natverk.py), lasterna (laster.py), löser kombinationerna (fem.py, analys.py), kontrollerar delarna per grupp
(kontroller.py), ritar figurerna (figurer.py) och sätter ihop rapporten via Typst (mall.typ).
"""
import json
import math
import time
import tomllib
from collections import defaultdict
from pathlib import Path

import numpy as np

import analys
import fem
import figurer
import forankring
import kontroller
import laster
import natverk

HERE = Path(__file__).parent
ROT = HERE.parents[1]
BARVERK = ROT / "modeller" / "trebodar" / "ut" / "barverk.json"
IN = tomllib.loads((HERE / "indata.toml").read_text(encoding="utf-8"))
F01 = tomllib.loads((HERE.parent / "F-01" / "indata.toml").read_text(encoding="utf-8"))
K05 = json.loads((HERE.parent / "K-05" / "resultat.json").read_text(encoding="utf-8"))


def fmt(x, n=1):
    from decimal import Decimal, ROUND_HALF_UP
    q = Decimal(repr(float(x))).quantize(Decimal(1).scaleb(-n), rounding=ROUND_HALF_UP)
    if q == 0:
        q = abs(q)
    return f"{q:,.{n}f}".replace(",", " ").replace(".", ",").replace("-", "−")


def pct(u):
    return f"{100 * u:.0f} %"


t0 = time.perf_counter()
N = natverk.bygg(BARVERK, IN["material"])
UG = IN.get("utegips", {})
OSB = dict(IN.get("osb", {}))


def johansen(d: float, t1: float, t2: float, f_u: float, rho_k: float, tra: bool = False) -> tuple[float, list[float]]:
    """Spikens bärförmåga i enskärigt förband skiva–trä (tra: trä–trä), karakteristisk [N] (SS-EN 1995-1-1 8.2.2
    (8.6) a–f, utan linverkan): hålkanthållfastheten i OSB f_h,1 = 65 d^−0,7 t^0,1 (8.22) och i virket utan
    förborrning f_h = 0,082 ρ_k d^−0,3 (8.15), flytmomentet M_y = 0,3 f_u d^2,6 (8.14)."""
    fh2 = 0.082 * rho_k * d ** -0.3
    fh1 = fh2 if tra else 65 * d ** -0.7 * t1 ** 0.1
    b, My, r = fh2 / fh1, 0.3 * f_u * d ** 2.6, t2 / t1
    F = [fh1 * t1 * d, fh2 * t2 * d,
         fh1 * t1 * d / (1 + b) * (math.sqrt(b + 2 * b * b * (1 + r + r * r) + b ** 3 * r * r) - b * (1 + r)),
         1.05 * fh1 * t1 * d / (2 + b) * (math.sqrt(2 * b * (1 + b) + 4 * b * (2 + b) * My / (fh1 * d * t1 ** 2)) - b),
         1.05 * fh1 * t2 * d / (1 + 2 * b) * (math.sqrt(2 * b * b * (1 + b) + 4 * b * (1 + 2 * b) * My
                                                          / (fh1 * d * t2 ** 2)) - b),
         1.15 * math.sqrt(2 * b / (1 + b)) * math.sqrt(2 * My * fh1 * d)]
    return min(F), F


if OSB.get("med"):
    OSB["F_k"], OSB["F_lagen"] = johansen(OSB["d"], OSB["t"], OSB["l"] - OSB["t"], OSB["f_u"], OSB["rho_k"])
    rho_m = math.sqrt(OSB["rho_m_tra"] * OSB["rho_m_skiva"])            # 7.1 (3)
    OSB["K_ser"] = rho_m ** 1.5 * OSB["d"] ** 0.8 / 30                    # tabell 7.1, spik utan förborrning
    OSB["K_u"] = 2 / 3 * OSB["K_ser"]                                    # 2.2.2 (2)
    OSB["K"] = natverk.skivans_styvhet(*OSB["skiva"], OSB["s"], OSB["s_mitt"], OSB["K_u"])
RS = dict(IN.get("raspont", {}))
if RS.get("med"):
    # brädan (t) mot ströläkten (t2) på takbalken, trådspik utan förborrning i trä av samma densitet
    RS["F_k"], RS["F_lagen"] = johansen(RS["d"], RS["t"], RS["t2"], RS["f_u"], RS["rho_k"], tra=True)
    RS["K_ser"] = RS["rho_m"] ** 1.5 * RS["d"] ** 0.8 / 30                # tabell 7.1, spik utan förborrning
    RS["K_u"] = 2 / 3 * RS["K_ser"]                                      # 2.2.2 (2)
SKIKT = {"utegips": UG, "osb": OSB, "raspont": RS}
SK = natverk.skjuvskivor(N, SKIKT) if any(P.get("med") for P in SKIKT.values()) else []
A = fem.Analys(N.modell)
fall, LD = laster.lastfall(N, IN, F01)
komb = analys.kombinationer(fall, IN["kombination"])


def q_max(k: analys.Kombination, SK: list = SK) -> np.ndarray:
    """Skjuvskivornas bärförmåga Q = V_Rd · h i kombinationen: förbandets F_d = k_mod F_k / γ_M i
    brottgränstillståndet, F_k i bruksgränstillståndet. Gipsens k_mod efter kombinationens lastvaraktighet; OSB:ns
    förband sqrt(k_mod,virke · k_mod,OSB) (SS-EN 1995-1-1 2.3.2.1 (4)); råspontens (trä mot trä) virkets."""
    Fd = {}
    km = IN["kombination"]["k_mod"]
    nyckel = next((n for n, v in km.items() if abs(v - k.kmod) < 1e-9), None)
    for namn, P in SKIKT.items():
        if not P.get("med"):
            continue
        if k.slag != "STR":
            Fd[namn] = P["F_k"]
        elif namn == "osb":
            Fd[namn] = math.sqrt(km[nyckel] * P["k_mod"][nyckel]) * P["F_k"] / P["gamma_M"]
        elif namn == "raspont":                       # trä mot trä: virkets k_mod
            Fd[namn] = km[nyckel] * P["F_k"] / P["gamma_M"]
        else:
            Fd[namn] = P["k_mod"][nyckel] * P["F_k"] / P["gamma_M"]
    return np.array([Fd[s.skikt] * s.V_per_F * s.h for s in SK])


# 1SV: utegipsen är den svagare sidan (natverk.SVAGARE_ANDEL), per mm skivkant
assert not (UG.get("med") and OSB.get("med")) or UG["F_k"] / UG["s"] < OSB["F_k"] / OSB["s"]


L = analys.los(A, fall, komb, q_max if SK else None)
K = kontroller.kontrollera(N, L, IN)
B = kontroller.bruksgrans(N, L, IN)
BV = json.loads(BARVERK.read_text(encoding="utf-8"))
FA = forankring.kontrollera(N, L, IN, BV, kontroller.Material("C24", IN["material"]["C24"]))
tid = time.perf_counter() - t0
m = N.modell
namn_k = [k.namn for k in komb]

# ------------------------------------------------------------------ modellen
grupper = defaultdict(lambda: {"antal": 0, "dim": set(), "mat": set()})
for b in N.delar:
    if b.slag == "kontakt":
        continue
    g = kontroller.grupp_av(b)
    grupper[g]["antal"] += 1
    grupper[g]["dim"].add(f"{fmt(min(b.bredd, b.hojd), 0)}×{fmt(max(b.bredd, b.hojd), 0)}")
    grupper[g]["mat"].add({"Stålband": "S350GD"}.get(b.material, b.material))
modell = {"delar": sum(1 for b in N.delar if b.slag not in ("kontakt", "utgar")), "sekundara": len(N.sekundara),
          "kontakter": sum(1 for b in N.delar if b.slag == "kontakt"), "noder": len(m.x), "element": len(m.bi),
          "band_vagg": sum(1 for d in N.band if N.delar[d].grupp == "band_vagg"),
          "band_tak": sum(1 for d in N.band if N.delar[d].grupp == "band_tak"),
          "upplag": len(m.upplag), "utelamnade": N.utelamnade, "tid": fmt(tid, 1),
          "grupper": [{"namn": g, "antal": v["antal"], "dim": ", ".join(sorted(v["dim"])[:4])
                       + (" …" if len(v["dim"]) > 4 else ""), "mat": ", ".join(sorted(v["mat"]))}
                      for g, v in sorted(grupper.items())]}

# ------------------------------------------------------------------ lasterna
Le = np.linalg.norm(m.x[m.bj] - m.x[m.bi], axis=1)
last = {"g_tak": fmt(LD["g_tak"], 2), "kg_tak": fmt(LD["kg_tak"], 1), "sk": fmt(LD["sk"], 1),
        "mu_dal": fmt(IN["last"]["mu_dal"], 1), "mu_takfot": fmt(IN["last"]["mu_takfot"], 1),
        "qp": fmt(LD["qp"], 2), "h": fmt(LD["h"] / 1000, 1), "vagg_ytter": fmt(IN["last"]["vagg_ytter"], 2),
        "vagg_inner": fmt(IN["last"]["vagg_inner"], 2),
        "rho": fmt(IN["material"]["rho_tra"], 0),
        "antal_komb": sum(1 for k in komb if k.slag == "STR"), "antal_bruks": sum(1 for k in komb if k.slag != "STR")}

# ------------------------------------------------------------------ lastvägarna: stolparna mot K-05
Fk = {k.namn: i for i, k in enumerate(komb)}
str_ = [i for i, k in enumerate(komb) if k.slag == "STR"]
stolpar = defaultdict(lambda: np.zeros(len(komb)))
for d in set(N.element_del):
    b = N.delar[d]
    if not b.stolpe or abs(b.ex[2]) < 0.9:
        continue
    el = np.flatnonzero(N.element_del == d)
    e = el[np.argmax(N.element_s[el, 1] - N.element_s[el, 0])]
    stolpar[b.stolpe] += -0.5 * (-L.F[:, e, 0] + L.F[:, e, 6])
k05 = {s["namn"]: s["Rd"] for s in K05["stolpar"]}
sno = [Fk[n] for n in ("G", "G+S1", "G+S2", "G+S3")]              # snö som huvudlast, som K-05
stolptab = []
for s in sorted(set(stolpar) | set(k05), key=lambda n: (n[:2], n)):
    if s not in stolpar:
        continue
    Ned = stolpar[s][sno].max()
    stolptab.append({"namn": s, "G": fmt(stolpar[s][Fk["G (k)"]] / 1e3, 1),
                     "S": fmt(stolpar[s][Fk["S1 (k)"]] / 1e3, 1), "Ned": fmt(Ned / 1e3, 1),
                     "Nmax": fmt(stolpar[s][str_].max() / 1e3, 1),
                     "K05": fmt(k05[s] / 1e3, 1) if s in k05 else "–",
                     "kvot": pct(Ned / k05[s]) if s in k05 else "–",
                     "over": bool(s in k05 and Ned > 1.05 * k05[s])})

# takstolarna mot K-03: diagonalens tryck och dragbandets drag mitt på (summan av delarna på systemlinjen), snö som
# huvudlast
K03 = json.loads((HERE.parent / "K-03" / "resultat.json").read_text(encoding="utf-8"))
k03 = {s["namn"]: s for s in K03["st"]}
pa_linje = defaultdict(list)
for d, k in N.linjer.items():
    pa_linje[k].append(d)


def linjekraft(b, P):
    """Normalkraften (drag +) i elementen på delens systemlinje närmast punkten P, summerad över delarna."""
    ut = np.zeros(len(komb))
    for d in (b.nr, *pa_linje.get(b.nr, [])):
        el = np.flatnonzero(N.element_del == d)
        if len(el):
            mitt = 0.5 * (m.x[m.bi[el]] + m.x[m.bj[el]])
            ut += L.F[:, el[np.argmin(np.linalg.norm(mitt - P, axis=1))], 6]
    return ut


takstolar = []
for el in sorted({b.element for b in N.delar if b.grupp == "takstol" and b.typ == "U" and b.slag == "balk"}):
    U = next(b for b in N.delar if b.grupp == "takstol" and b.element == el and b.typ == "U")
    D = [b for b in N.delar if b.grupp == "takstol" and b.element == el and b.typ == "D" and b.slag == "balk"]
    st = k03.get({"2C": "L2M"}.get(el, el))
    if not st or len(D) != 2:
        continue
    Nd = max((-linjekraft(d, 0.5 * (d.a0 + d.b0)))[sno].max() for d in D)
    Hd = linjekraft(U, 0.5 * (U.a + U.b))[sno].max()
    takstolar.append({"namn": el + (" (L2M)" if el == "2C" else ""), "N": fmt(Nd / 1e3, 1), "N03": st["N"],
                      "H": fmt(Hd / 1e3, 1), "H03": st["H"]})

# gavlarna: skivornas kraft där de håller gavelns överkant och takstolens överram i sidled
Bk = np.abs(L.bindning[str_]) if L.bindning.size else np.zeros((len(str_), 0))
gavel = {"max": "–", "gavel": "–", "komb": "–", "antal": len(N.bindningar)}
if Bk.size:
    k, c = np.unravel_index(np.argmax(Bk), Bk.shape)
    gavel.update({"max": fmt(Bk[k, c] / 1e3, 1), "gavel": N.bindningar[c], "komb": komb[str_[k]].namn})

# jämvikt: lasterna mot reaktionerna i lastfallen
jamvikt = []
for f in fall[:4]:
    tot = (f.q * Le[:, None]).sum(axis=0) / 1e3
    jamvikt.append({"namn": f.namn, "last": fmt(-tot[2], 1)})
G_tot = -(fall[0].q * Le[:, None]).sum(axis=0)[2] / 1e3

# horisontella lastvägar: väggarnas andel av vindlasten (karakteristisk), per huvudriktning
vagg_av_upplag = []
for n_ in m.upplag:
    d = next((d for d in N.nod_delar[n_] if N.delar[d].upplagd), N.nod_delar[n_][0])
    vagg_av_upplag.append(N.delar[d].element if N.delar[d].grupp != "stolpe" else "stolpar")
riktningar = []
for rn, vek in (("+x", (1, 0)), ("−x", (-1, 0)), ("+y", (0, 1)), ("−y", (0, -1))):
    kand = [i for i, k in enumerate(komb) if k.slag == "SLS-k" and next(iter(k.faktorer)).startswith(f"W{rn}")]
    i = kand[0]
    R = L.R[i][:, :2] @ np.array(vek, float)
    andel = defaultdict(float)
    for v, r in zip(vagg_av_upplag, R):
        andel[v] += -r
    tot = sum(andel.values())
    rader = sorted(((v, a) for v, a in andel.items() if abs(a) > 0.03 * abs(tot)), key=lambda t: -abs(t[1]))
    riktningar.append({"riktning": rn, "komb": namn_k[i], "tot": fmt(tot / 1e3, 1),
                       "vaggar": [{"vagg": v, "kN": fmt(a / 1e3, 1), "andel": pct(a / tot)} for v, a in rader[:8]]})

# ------------------------------------------------------------------ kontrollerna per grupp
ordning = ["Reglar i ytterväggarna", "Reglar i innerväggarna", "Stolpar i väggarna", "Fristående stolpar",
           "Syllar och hammarband", "Överstycken, bröstningar och kortlingar", "Upplag (tryck vinkelrätt fibrerna)",
           "Takbalkar och avväxlingar", "Takstolar", "Stålband i väggarna", "Stålband i takfallen"]
sammanf = []
for g in ordning:
    rr = [r for r in K["rader"] if r.grupp == g and r.kontroll != "Spik i bandets ände"]
    if not rr:
        continue
    r = max(rr, key=lambda r: r.eta)
    sammanf.append({"grupp": g, "antal": r.detaljer.get("antal", ""), "kontroll": r.kontroll, "eta": pct(r.eta),
                    "ok": r.eta <= 1.0, "del": r.del_, "komb": r.komb})
detalj = []
for r in sorted(K["rader"], key=lambda r: (ordning.index(r.grupp) if r.grupp in ordning else 99, -r.eta)):
    d = r.detaljer
    detalj.append({"grupp": r.grupp, "kontroll": r.kontroll, "eta": pct(r.eta), "ok": r.eta <= 1.0, "del": r.del_,
                   "komb": r.komb, **{k: (fmt(v / 1e3, 1) if k in ("N", "Nc", "Nt", "V", "NtRd", "FvRd", "FvRk")
                                       else fmt(v / 1e6, 2) if k in ("My", "Mz", "M", "T") else
                                       fmt(v, 2) if k in ("kc", "kmod", "kc90") else
                                       fmt(v, 0) if isinstance(v, float) else v)
                                    for k, v in d.items()}})
spik = {r.grupp: r for r in K["rader"] if r.kontroll == "Spik i bandets ände"}
band = {"NtRd": fmt(K["NtRd"] / 1e3, 1), "FvRk": fmt(K["FvRk"] / 1e3, 2), "b": fmt(IN["band"]["b"], 0),
        "t": fmt(IN["band"]["t"], 1), "spik": IN["band"]["spik"], "d0": fmt(IN["band"]["d0"], 0),
        "rader": [{"grupp": g, "N": fmt(r.detaljer["N"] / 1e3, 1), "n": r.detaljer["n"],
                   "FvRd": fmt(r.detaljer["FvRd"] / 1e3, 2), "del": r.del_} for g, r in spik.items()]}
fa = K["forankring"]
FK = FA["K"]
bit_ut = [{"vagg": b["vagg"], "syll": b["syll"], "langd": fmt(b["langd"], 0),
           "bultar": str(b["bultar"]) + (f" ({b['sneda']} snett)" if b["sneda"] else ""),
           "M": pct(b["eta_M"]) if b["eta_M"] else "–", "N": pct(b["eta_N"]) if b["eta_N"] else "–",
           "H": fmt(b["H"] / 1e3, 1), "V": fmt(b["V_bult"] / 1e3, 1), "uH": pct(b["eta_H"]), "beslag": str(b["beslag"]),
           "ok": max(b["eta_M"], b["eta_N"], b["eta_H"], b["eta_S"]) <= 1.0}
          for b in sorted(FA["bitar"], key=lambda b: (b["vagg"], b["syll"]))]
beslag_ut = [{"del": b["del"], "u": fmt(b["u"], 0) if b["u"] == b["u"] else "–", "lyft": fmt(b["lyft"] / 1e3, 1),
              "H": fmt(b["Hmax"] / 1e3, 1) if b["sidled"] else "–", "komb": b["komb"], "modell": b["modell"],
              "krav": b["krav"], "eta": pct(b["eta"]) if math.isfinite(b["eta"]) else "saknas", "ok": b["eta"] <= 1.0}
             for b in sorted(FA["beslag"], key=lambda b: (b["element"], b["u"] if b["u"] == b["u"] else 0.0))]
halldon = [{"del": b["del"], "lyft": fmt(b["lyft"] / 1e3, 1), "H": fmt(b["Hmax"] / 1e3, 1), "komb": b["komb"],
            "eta": pct(b["eta"]), "ok": b["eta"] <= 1.0} for b in FA["beslag"] if b["halldon"]]
fa_ok = all(r["ok"] for r in bit_ut) and all(b["ok"] for b in beslag_ut)
for f in FA["forslag"]:
    print(f"  förankringen: beslag saknas eller räcker inte vid {f}")
forank = {"lyft": fmt(fa["lyft"] / 1e3, 1), "lyft_del": fa["lyft_del"], "lyft_komb": fa["lyft_komb"],
          "hor": fmt(fa["hor"] / 1e3, 1), "hor_del": fa["hor_del"],
          "n_upplag": str(FA["n_upplag"]), "n_lyft": str(FA["n_lyft"]),
          "NRd": fmt(FK["N_Rd"] / 1e3, 1), "VRd": fmt(FK["V_Rd"] / 1e3, 1), "d": fmt(IN["forankring"]["bult_d"], 0),
          "bricka": "×".join(fmt(v, 0) for v in IN["forankring"]["bricka"]),
          "Nbricka": fmt(min(FK["N_Rd"], FA["N_bult_W"]) / 1e3, 1),
          "Rbricka": fmt(float(IN["kombination"]["k_mod"]["W"]) * IN["material"]["C24"]["fc90k"]
                     / IN["material"]["C24"]["gamma_M"] * FK["A_bricka"] / 1e3, 1),
          "fhk": fmt(FK["fhk"], 1), "Fvk": fmt(FK["Fv_k"] / 1e3, 1), "Fvd": fmt(FA["Fv_d_W"] / 1e3, 1),
          "skruv": f"{IN['forankring']['skruv_n']} skruv {fmt(IN['forankring']['skruv_d'], 0)}×90",
          "Rskruv": fmt(FA["R_skruv_W"] / 1e3, 1), "beslag": IN["forankring"]["beslag"],
          "R1k": fmt(IN["forankring"]["beslag_R1k_par"], 1), "R23k": fmt(IN["forankring"]["beslag_R23k_par"], 1),
          "R1": fmt(FA["R_beslag_W"] / 1e3, 1), "R23": fmt(FA["R23_W"] / 1e3, 1),
          "band": fmt(IN["forankring"]["bandning"], 1), "Rkat": [fmt(r / 1e3, 1) for r in FA["R_kat_W"]],
          "halldon_namn": IN["forankring"]["halldon"], "Rhd": fmt(FA["R_hd_W"] / 1e3, 1),
          "hd_tra": fmt(IN["forankring"]["halldon_R1k_tra"], 1),
          "hd_stal": fmt(IN["forankring"]["halldon_R1k_stal"], 1),
          "hd_betong": fmt(IN["forankring"]["halldon_R1d_betong"], 1),
          "bitar": bit_ut, "beslag_rader": beslag_ut, "halldon": halldon,
          "n_beslag": str(FA["n_modell"]), "n_upplag_beslag": str(len(beslag_ut)),
          "sneda": str(sum(b["sneda"] for b in FA["bitar"])),
          "sneda_text": (f" ({sum(b['sneda'] for b in FA['bitar'])} av syllarnas bultar, de andra är beslagens);"
                         if any(b["sneda"] for b in FA["bitar"]) else ";"),
          "V_max": fmt(max(b["V_bult"] for b in FA["bitar"]) / 1e3, 1),
          "N_max": fmt(max(b["N_bult"] for b in FA["bitar"]) / 1e3, 1),
          "M_max": pct(max(b["eta_M"] for b in FA["bitar"])), "ok": fa_ok}
_bM = max(FA["bitar"], key=lambda b: b["eta_M"])
_bN = max(FA["bitar"], key=lambda b: max(b["eta_N"], b["eta_H"], b["eta_S"]))
_bs = max(FA["beslag"], key=lambda b: b["eta"])
forank["sammanf"] = [
    {"grupp": "Förankring: syllarna", "kontroll": "Böjning mellan bultarna", "eta": pct(_bM["eta_M"]),
     "ok": _bM["eta_M"] <= 1.0, "del": _bM["syll"]},
    {"grupp": "Förankring: betongbultarna", "kontroll": "Drag och skjuvning, skruvarna",
     "eta": pct(max(_bN["eta_N"], _bN["eta_H"], _bN["eta_S"])),
     "ok": max(_bN["eta_N"], _bN["eta_H"], _bN["eta_S"]) <= 1.0, "del": _bN["syll"]},
    {"grupp": "Förankring: beslagen", "kontroll": "Lyft (och sidkraft)",
     "eta": pct(_bs["eta"]) if math.isfinite(_bs["eta"]) else "saknas",
     "ok": _bs["eta"] <= 1.0, "del": f"{_bs['del']}, {_bs['komb']}"}]
bruks = {"tak": {k: (fmt(v, 1) if isinstance(v, float) and k != "eta" else v) for k, v in B["takbalk"].items()},
         "drift": {k: (fmt(v, 1) if isinstance(v, float) and k != "eta" else v) for k, v in B["drift"].items()}}
bruks["tak"]["eta"] = pct(B["takbalk"]["eta"])
bruks["drift"]["eta"] = pct(B["drift"]["eta"])
bruks["tak"]["ok"] = B["takbalk"]["eta"] <= 1
bruks["drift"]["ok"] = B["drift"]["eta"] <= 1

alla_ok = all(r["ok"] for r in sammanf) and bruks["tak"]["ok"] and bruks["drift"]["ok"] and fa_ok
figurer.modell(N, K, HERE / "fig_modell.svg")
figurer.forankring(N, FA, BV, HERE / "fig_forankring.svg")
figurer.plan(N, K, HERE / "fig_plan.svg")

# snitt genom delarna som inte klarar lasterna: väggen (med takstolen) som delen står i, annars ett lodrätt snitt
# längs takbalken eller väggen närmast den fristående stolpen; ett snitt per plan, de högsta utnyttjandena först
vaggar = {v["kod"]: v for v in N.ytor["vaggar"]}
felande = {int(N.element_del[e]) for e in np.flatnonzero(K["eta_element"] > 1.0)}
felande |= {N.band[k] for k in np.flatnonzero(K["eta_band"] > 1.0)}
planen: dict[str, dict] = {}
fel_rader = [r for r in K["rader"] if r.eta > 1.0 and "nr" in r.detaljer and r.kontroll != "Spik i bandets ände"]
if B["drift"]["eta"] > 1.0:
    fel_rader.append(kontroller.Rad("Väggarnas överkant i vind", "u ≤ H/300", B["drift"]["eta"], B["drift"]["del"],
                                    B["drift"]["komb"], {"nr": next(b.nr for b in N.delar if b.namn == B["drift"]["del"])}))


def planet(b: natverk.Bar) -> tuple[str, dict]:
    if b.element in vaggar and b.grupp in ("yttervagg", "innervagg", "takstol", "band_vagg"):
        v = vaggar[b.element]
        return f"vägg {b.element}", {"o": v["origo"], "u": v["u"], "w": v["w"], "u0": -300.0, "u1": v["langd"] + 300.0,
                                     "w0": -80.0, "w1": v["tjocklek"] + 220.0, "text": f"Väggen {b.element}"
                                     + (" med takstolen" if any(d.grupp == "takstol" and d.element == b.element
                                                                for d in N.delar) else "")}
    if b.grupp == "stolpe":
        for v in vaggar.values():
            o, u, w = (np.array(v[k]) for k in ("origo", "u", "w"))
            if abs((b.c[:2] - o) @ w - v["tjocklek"] / 2) < 400 and -100 < (b.c[:2] - o) @ u < v["langd"] + 100:
                return f"vägg {v['kod']}", {"o": v["origo"], "u": v["u"], "w": v["w"], "u0": -300.0,
                                            "u1": v["langd"] + 300.0, "w0": -400.0, "w1": v["tjocklek"] + 400.0,
                                            "text": f"Väggen {v['kod']} med stolpen {b.element}"}
    d = b.b0[:2] - b.a0[:2]
    u = d / np.linalg.norm(d) if np.linalg.norm(d) > 1 else np.array([1.0, 0.0])
    w = np.array([-u[1], u[0]])
    o = b.a0[:2] - 1500 * u
    return f"snitt {b.namn}", {"o": o.tolist(), "u": u.tolist(), "w": w.tolist(), "u0": 0.0,
                                "u1": float(np.linalg.norm(d)) + 3000.0, "w0": -260.0, "w1": 260.0,
                                "text": f"Lodrätt snitt längs {b.namn}"}


for r in sorted(fel_rader, key=lambda r: -r.eta):
    b = N.delar[r.detaljer["nr"]]
    nyckel, pl = planet(b)
    if nyckel not in planen:
        planen[nyckel] = {"plan": pl, "komb": r.komb, "rader": []}
    planen[nyckel]["rader"].append(r)
delar_raa = json.loads(BARVERK.read_text(encoding="utf-8"))["delar"]
sektioner = []
for i, (nyckel, p_) in enumerate(list(planen.items())[:9]):
    k = namn_k.index(p_["komb"])
    fil = f"fig_snitt{i + 1}.svg"
    figurer.sektion(N, delar_raa, p_["plan"], L.F[k], L.band[k], felande, HERE / fil)
    fel = "; ".join(f"{r.del_} {pct(r.eta)} ({r.kontroll.lower()})" for r in p_["rader"])
    sektioner.append({"fil": fil, "text": f"{p_['plan']['text']}, kombination {p_['komb']}: normalkraften i delarna "
                                          f"(kN, rött tryck och grönt drag) och i banden (blå). Röda delar klarar inte "
                                          f"lasterna: {fel}."})

# ------------------------------------------------------------------ råsponten: styvhet och känslighet
def gt_band(kod: str) -> float:
    """Takfallets skjuvstyvhet G·t [N/mm] av stålbanden i fälten med kryss (en diagonal verksam, EA/L utan
    förskjutning i ändarna): Σ EA (b h)² / L³ / Σ b h."""
    EA = IN["material"]["Stålband"]["E0mean"] * IN["band"]["b"] * IN["band"]["t"]
    GA = A_ = 0.0
    for j in N.band:
        b = N.delar[j]
        if b.grupp == "band_tak" and b.element == kod:
            d = b.b0 - b.a0
            by, hs, Lb = abs(d[1]), math.hypot(d[0], d[2]), float(np.linalg.norm(d))
            GA += 0.5 * EA * (by * hs) ** 2 / Lb ** 3
            A_ += 0.5 * by * hs
    return GA / A_ if A_ else 0.0


def per_vagg(K_: dict, L_: analys.Losning) -> tuple[dict, dict]:
    """Väggarnas horisontella reaktion i vind ±x (karakteristisk) och deras högsta utnyttjande (delar och band)."""
    ut_R = {}
    for rn, s_ in (("+x", 1.0), ("−x", -1.0)):
        i = next(i for i, k in enumerate(komb) if k.slag == "SLS-k" and next(iter(k.faktorer)).startswith(f"W{rn}"))
        R = defaultdict(float)
        for v, rx in zip(vagg_av_upplag, L_.R[i][:, 0]):
            R[v] += -s_ * rx
        ut_R[rn] = R
    eta = defaultdict(float)
    for e, x in enumerate(K_["eta_element"]):
        eta[N.delar[N.element_del[e]].element] = max(eta[N.delar[N.element_del[e]].element], float(x))
    for j, x in enumerate(K_["eta_band"]):
        if N.delar[N.band[j]].grupp == "band_vagg":
            eta[N.delar[N.band[j]].element] = max(eta[N.delar[N.band[j]].element], float(x))
    return ut_R, eta


raspont = {}
if RS.get("med"):
    fall_utan = {**SKIKT, "raspont": {**RS, "med": False}}
    fall_fema = {**SKIKT, "raspont": {**RS, "G_d": IN["raspont_kanslighet"]["G_d"]}}
    varianter = {}
    for namn_v, sk_ in (("utan", fall_utan), ("fema", fall_fema)):
        SK_v = natverk.skjuvskivor(N, sk_)
        L_v = analys.los(fem.Analys(N.modell), fall, komb, lambda k, S_=SK_v: q_max(k, S_))
        varianter[namn_v] = per_vagg(kontroller.kontrollera(N, L_v, IN), L_v)
    natverk.skjuvskivor(N, SKIKT)                     # balkmodellen med de räknade skivorna igen
    varianter["med"] = per_vagg(K, L)
    VAGGAR_X = ["1NO", "2NO", "3NO", "1SV", "2SV", "3SV", "2C", "1A", "1C", "1D", "2A"]
    k_r = RS["K_u"] * RS["a"] ** 2 / 2
    km_W = IN["kombination"]["k_mod"]["W"]
    Qk = np.abs(L.skiva[str_]) if len(SK) else np.zeros((len(str_), 0))
    rad_tak = []
    for t in N.ytor["takytor"]:
        jj = [j for j, s_ in enumerate(SK) if s_.skikt == "raspont" and s_.vagg == t["kod"]]
        Gt = float(np.mean([SK[j].K / (SK[j].b * SK[j].h) for j in jj])) if jj else 0.0
        V = float((Qk[:, jj] / np.array([SK[j].h for j in jj])).sum(1).max()) if jj else 0.0
        rad_tak.append({"takfall": t["kod"], "fack": len(jj), "Gt_band": fmt(gt_band(t["kod"]), 0),
                        "Gt_rasp": fmt(Gt, 1), "kvot": f"{fmt(100 * Gt / gt_band(t['kod']), 1)} %",
                        "Gt_fema": fmt(IN["raspont_kanslighet"]["G_d"], 0),
                        "kvot_fema": pct(IN["raspont_kanslighet"]["G_d"] / gt_band(t["kod"])),
                        "V": fmt(V / 1e3, 2)})
    rad_vagg = []
    for v in VAGGAR_X:
        rr = {"vagg": v}
        for rn in ("+x", "−x"):
            for vn in ("utan", "med", "fema"):
                rr[f"R{vn}{rn}"] = fmt(varianter[vn][0][rn].get(v, 0.0) / 1e3, 1)
        for vn in ("utan", "med", "fema"):
            e_ = varianter[vn][1].get(v, 0.0)
            rr[f"eta_{vn}"] = pct(e_)
            rr[f"ok_{vn}"] = e_ <= 1.0
        rad_vagg.append(rr)
    raspont = {"produkt": RS["produkt"], "d": fmt(RS["d"], 1), "t": fmt(RS["t"], 0), "t2": fmt(RS["t2"], 0),
               "w": fmt(RS["w"], 0), "a": fmt(RS["a"], 0), "F_k": fmt(RS["F_k"], 0), "K_ser": fmt(RS["K_ser"], 0),
               "K_u": fmt(RS["K_u"], 0), "k_r": fmt(k_r / 1e3, 0), "Gt": fmt(k_r / (600.0 * RS["w"]), 1),
               "qRk": fmt(RS["F_k"] * RS["a"] / (600.0 * RS["w"]), 2),
               "qRd": fmt(km_W * RS["F_k"] / RS["gamma_M"] * RS["a"] / (600.0 * RS["w"]), 2),
               "G_d": fmt(IN["raspont_kanslighet"]["G_d"], 0), "tak": rad_tak, "vaggar": rad_vagg,
               "V_max": fmt(max(float(t["V"].replace(",", ".")) for t in rad_tak), 2),
               "dR": fmt(max(abs(varianter[a_][0][rn].get(v, 0.0) - varianter["utan"][0][rn].get(v, 0.0))
                             for v in VAGGAR_X for rn in ("+x", "−x") for a_ in ("med", "fema")) / 1e3, 1),
               "deta": fmt(100 * max(abs(varianter[a_][1].get(v, 0.0) - varianter["utan"][1].get(v, 0.0))
                                     for v in VAGGAR_X for a_ in ("med", "fema")), 0)}

skivor_ut = {"ug": {"F_k": fmt(UG.get("F_k", 0.0), 0), "s": fmt(UG.get("s", 0.0), 0), "K": fmt(UG.get("K", 0.0), 0)},
             "osb": {k: fmt(OSB[k], 0) for k in ("F_k", "K_ser", "K") if k in OSB} | {
                 "s": fmt(OSB.get("s", 0.0), 0), "s_mitt": fmt(OSB.get("s_mitt", 0.0), 0),
                 "produkt": OSB.get("produkt", "")},
             "andel": pct(natverk.SVAGARE_ANDEL),
             "antal": {sk: sum(1 for s_ in SK if s_.skikt == sk) for sk in ("utegips", "osb", "raspont")}}

R_ut = {"projekt": IN["projekt"], "raspont": raspont, "skivor": skivor_ut, "modell": modell, "last": last,
        "stolpar": stolptab, "G_tot": fmt(G_tot, 1),
        "takstolar": takstolar, "gavel": gavel,
        "riktningar": riktningar, "sammanf": sammanf, "detalj": detalj, "band": band, "forankring": forank,
        "bruks": bruks, "alla_ok": alla_ok, "sektioner": sektioner, "kombination": {k: (fmt(v, 2) if isinstance(v, float) else v)
                                                            for k, v in IN["kombination"].items()
                                                            if not isinstance(v, (list, dict))},
        "kmod": {k: fmt(v, 1) for k, v in IN["kombination"]["k_mod"].items()},
        "kontroll": {k: fmt(v, 2) if isinstance(v, float) else v for k, v in IN["kontroll"].items()}}
(HERE / "resultat.json").write_text(json.dumps(R_ut, ensure_ascii=False, indent=1,
                                               default=lambda o: o.item() if hasattr(o, "item") else str(o)),
                                    encoding="utf-8")

import typst  # noqa: E402

pdf = HERE / "K-04_trastomme.pdf"
typst.compile(str(HERE / "mall.typ"), output=str(pdf), font_paths=["/usr/share/fonts", str(HERE.parent / ".fonts")])
print(f"{len(komb)} kombinationer, {len(m.bi)} element, {len(N.band)} band, {tid:.1f} s; alla OK: {alla_ok} -> {pdf.name}")
for r in sammanf:
    print(f"  {r['eta']:>6} {r['grupp']:40} {r['kontroll']:28} {r['del']} ({r['komb']})")
