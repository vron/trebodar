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
A = fem.Analys(N.modell)
fall, LD = laster.lastfall(N, IN, F01)
komb = analys.kombinationer(fall, IN["kombination"])
L = analys.los(A, fall, komb)
K = kontroller.kontrollera(N, L, IN)
B = kontroller.bruksgrans(N, L, IN)
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
modell = {"delar": sum(1 for b in N.delar if b.slag != "kontakt"),
          "kontakter": sum(1 for b in N.delar if b.slag == "kontakt"), "noder": len(m.x), "element": len(m.bi),
          "band_vagg": sum(1 for d in N.band if N.delar[d].grupp == "band_vagg"),
          "band_tak": sum(1 for d in N.band if N.delar[d].grupp == "band_tak"),
          "upplag": len(m.upplag), "utelamnade": N.utelamnade, "tid": fmt(tid, 1),
          "grupper": [{"namn": g, "antal": v["antal"], "dim": ", ".join(sorted(v["dim"])[:4])
                       + (" …" if len(v["dim"]) > 4 else ""), "mat": ", ".join(sorted(v["mat"]))}
                      for g, v in sorted(grupper.items())]}

# ------------------------------------------------------------------ lasterna
Le = np.linalg.norm(m.x[m.bj] - m.x[m.bi], axis=1)
lastfall = [{"namn": f.namn, "text": f.text, "slag": f.slag,
             "F": [fmt(v / 1e3, 1) for v in (f.q * Le[:, None]).sum(axis=0)]} for f in fall]
last = {"g_tak": fmt(LD["g_tak"], 2), "kg_tak": fmt(LD["kg_tak"], 1), "sk": fmt(LD["sk"], 1),
        "mu_dal": fmt(IN["last"]["mu_dal"], 1), "mu_takfot": fmt(IN["last"]["mu_takfot"], 1),
        "qp": fmt(LD["qp"], 2), "h": fmt(LD["h"] / 1000, 1), "vagg_ytter": fmt(IN["last"]["vagg_ytter"], 2),
        "vagg_inner": fmt(IN["last"]["vagg_inner"], 2), "tillagg": IN["last"]["tak_tillagg"],
        "rho": fmt(IN["material"]["rho_tra"], 0), "fall": lastfall,
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
stolptab = []
for s in sorted(set(stolpar) | set(k05), key=lambda n: (n[:2], n)):
    if s not in stolpar:
        continue
    Ned = stolpar[s][str_].max()
    stolptab.append({"namn": s, "G": fmt(stolpar[s][Fk["G (k)"]] / 1e3, 1),
                     "S": fmt(stolpar[s][Fk["S1 (k)"]] / 1e3, 1), "Ned": fmt(Ned / 1e3, 1),
                     "K05": fmt(k05[s] / 1e3, 1) if s in k05 else "–",
                     "kvot": pct(Ned / k05[s]) if s in k05 else "–",
                     "over": bool(s in k05 and Ned > 1.05 * k05[s])})

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
forank = {"lyft": fmt(fa["lyft"] / 1e3, 1), "lyft_del": fa["lyft_del"], "lyft_komb": fa["lyft_komb"],
          "hor": fmt(fa["hor"] / 1e3, 1), "hor_del": fa["hor_del"],
          "vaggar": [{"vagg": v, "lyft": fmt(x["lyft"] / 1e3, 1), "skjuv": fmt(x["skjuv"] / 1e3, 1)}
                     for v, x in sorted(K["per_vagg"].items(), key=lambda t: -t[1]["lyft"])[:10]]}
bruks = {"tak": {k: (fmt(v, 1) if isinstance(v, float) and k != "eta" else v) for k, v in B["takbalk"].items()},
         "drift": {k: (fmt(v, 1) if isinstance(v, float) and k != "eta" else v) for k, v in B["drift"].items()}}
bruks["tak"]["eta"] = pct(B["takbalk"]["eta"])
bruks["drift"]["eta"] = pct(B["drift"]["eta"])
bruks["tak"]["ok"] = B["takbalk"]["eta"] <= 1
bruks["drift"]["ok"] = B["drift"]["eta"] <= 1

alla_ok = all(r["ok"] for r in sammanf) and bruks["tak"]["ok"] and bruks["drift"]["ok"]
figurer.modell(N, K, HERE / "fig_modell.svg")
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
    d = b.b[:2] - b.a[:2]
    u = d / np.linalg.norm(d) if np.linalg.norm(d) > 1 else np.array([1.0, 0.0])
    w = np.array([-u[1], u[0]])
    o = b.a[:2] - 1500 * u
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

R_ut = {"projekt": IN["projekt"], "modell": modell, "last": last, "stolpar": stolptab, "G_tot": fmt(G_tot, 1),
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
