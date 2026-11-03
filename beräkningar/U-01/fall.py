"""
U-01: ett fall (grundfallet med fallets ändringar) i periodiskt tillstånd, med temperaturerna i plattans kolumner och
fuktbalansen. Egen modul, så att berakning.py kan räkna fallen i parallella processer.
"""
import json
import time
import tomllib
from pathlib import Path

import numpy as np

import mark2d as M

HERE = Path(__file__).parent
IN = tomllib.loads((HERE / "indata.toml").read_text(encoding="utf-8"))
G05 = json.load(open(HERE.parent / "K-05" / "bild" / "geometri.json", encoding="utf-8"))
VAGG = {f"V{i}": v for i, v in enumerate(G05["vagg"], 1)}
# plintarnas mitt (dubbelrör: mitt emellan rören) och sida ur K-06 (bottenplattan L300)
PEL = {f"P{i}": (p[0] + IN["dubbelror"].get(f"P{i}", 0.0) / 2, p[1]) for i, p in enumerate(G05["pelare"], 1)}
R06 = json.load(open(HERE.parent / "K-06" / "resultat.json", encoding="utf-8"))
PLINT = {f"P{i}": float(b) for i, b in enumerate(R06["platta"]["L300"]["plint"], 1)}
MANAD = ("januari", "februari", "mars", "april", "maj", "juni", "juli", "augusti", "september", "oktober",
         "november", "december")
TYPER = (("falt", "Platta i fält"), ("plint", "Plint"), ("kant", "Kantbalk"))


def datum(d):
    m = max(i for i, s in enumerate(M.MAN) if s <= d)
    return f"{d - M.MAN[m] + 1} {MANAD[m][:3] if m != 4 else 'maj'}"


def par(fall):
    """Parametrar i m för mark2d: grundfallet med fallets ändringar."""
    s, pl, kl, dr = IN["sektion"], IN["platta"], IN["klimat"], IN["drift"]
    P = dict(xc_v=VAGG[s["vagg_v"]][1] / 1000, xc_o=VAGG[s["vagg_o"]][1] / 1000, mark_v=s["mark_v"] / 1000,
             mark_o=s["mark_o"] / 1000, h_rum=s["h_rum"] / 1000, utforande=s["utforande"],
             plint=sorted(((n, PEL[n][0] / 1000, b / 1000) for n, b in PLINT.items() if abs(PEL[n][1] - s["y"]) < b / 2),
                          key=lambda p: p[1]),
             vagg_skikt=IN["vagg"]["skikt"])
    P.update({k: v / 1000 for k, v in pl.items()})
    P.update(IN["material"]); P.update(kl); P.update(dr)
    P["nat"] = dict(IN["nat"])
    P["nat"].update({k: IN["nat"][k] / 1000 for k in ("h_fin", "h_falt", "h_vagg", "h_max")})
    for k, v in fall.items():
        if k in ("mark_v", "mark_o"):
            P[k] = v / 1000
        elif k == "utbredning":
            P["nat"][k] = v
        elif k != "namn":
            P[k] = v
    u = IN["utforande"][P["utforande"]]
    P["t_eps"], P["h_balk"] = u["t_eps"] / 1000, u["h_balk"] / 1000
    return P


def kondens(Tg, Tx, d, mu):
    """Fuktbalans dygnsvis (Glaser) i ytan Tx med marken Tg vid RF 100 % och cellplast d (m) emellan. Två varv av
    årscykeln; andra varvets största mängd (g/m²) och antal dygn med kondens."""
    g = IN["fukt"]["delta_luft"] / mu / d * (M.ps(Tg) - M.ps(Tx)) * M.DAG * 1000     # g/(m²·dygn)
    Mx, ut = 0.0, []
    for gg in np.concatenate([g, g]):
        Mx = max(0.0, Mx + gg)
        ut.append(Mx)
    ut = np.array(ut[365:])
    return float(ut.max()), int((ut > 0).sum())


_PERIODISK = {}                # (fall, f, n) -> nät, år och periodiskt tillstånd (samma fall räknas en gång)


def kor(fall, f=1.0, n=None, falt=()):
    t0 = time.time()
    P = par(fall)
    nyckel = (json.dumps(fall, sort_keys=True), f, n)
    if nyckel not in _PERIODISK:
        m = M.bygg(P, f)
        A = M.Ar(m, n or IN["nat"]["steg_per_dygn"])
        _PERIODISK[nyckel] = (m, A, *A.periodisk())
    m, A, T0, it, avv = _PERIODISK[nyckel]
    K = M.kolumner(m)
    nk = len(K)
    To, Tu, Tf = np.zeros((nk, 365)), np.zeros((nk, 365)), np.full((nk, 365), np.nan)

    def spara(T, d):
        for i, c in enumerate(K):
            To[i, d], Tu[i, d] = M.ytT(T, c["over"]), M.ytT(T, c["under"])
            if "folie" in c:
                Tf[i, d] = M.ytT(T, c["folie"])

    _, F = A.kor(T0, spara=spara, falt=set(falt))
    dT = To - Tu
    mu = IN["fukt"]["mu_eps"]
    res = dict(namn=fall.get("namn", ""), P=P, m=m, A=A, T0=T0, it=it, avv=avv, K=K, To=To, Tu=Tu, Tf=Tf, F=F,
               celler=m["N"], tid=time.time() - t0)
    for typ, _ in TYPER:
        ii = [i for i, c in enumerate(K) if c["typ"] == typ]
        i = min(ii, key=lambda i: dT[i].min())
        d = int(dT[i].argmin())
        dk = P["t_fot"] if typ != "falt" else P["t_eps"]
        Mk, Mn = max(kondens(Tu[j], To[j], dk, mu) for j in ii)
        r = dict(i=i, x=K[i]["x"], dT=float(dT[i, d]), dag=d, n_neg=int((dT[i] < 0).sum()),
                 medel=float(min(dT[j].mean() for j in ii)), Tg=float(Tu[i, d]), Ts=float(To[i, d]), M=Mk, M_dygn=Mn,
                 vinter=float(dT[i][A.pa].mean()),
                 n_neg_alla=int(max((dT[j] < 0).sum() for j in ii)))
        if typ == "falt":
            r["M_folie"], r["M_folie_dygn"] = max(kondens(Tu[j], Tf[j], P["t_eps"] / 2, mu) for j in ii)
            r["dT_folie"] = float(min((Tf[j] - Tu[j]).min() for j in ii))
        res[typ] = r
    res["M"] = max(res["falt"]["M"], res["falt"]["M_folie"], res["plint"]["M"], res["kant"]["M"])
    res["M_dygn"] = max(res["falt"]["M_dygn"], res["falt"]["M_folie_dygn"], res["plint"]["M_dygn"], res["kant"]["M_dygn"])
    res["dT"] = min(res[t]["dT"] for t, _ in TYPER)
    res["n_neg"] = max(res[t]["n_neg_alla"] for t, _ in TYPER)
    print(f"{res['namn'][:40]:40s} " + " | ".join(f"{t} {res[t]['dT']:5.2f} K {datum(res[t]['dag']):>6s} x {res[t]['x']:5.2f}"
                                                for t, _ in TYPER)
          + f" | kondens {res['M']:5.1f} g/m², {res['n_neg']} dygn | {it} it, {res['tid']:.0f} s", flush=True)
    return res




def kor_i_process(fall, f=1.0, n=None):
    """kor i en annan process: resultatet utan nätet, året och fälten (som inte går att skicka tillbaka)."""
    res = kor(fall, f, n)
    return {k: v for k, v in res.items() if k not in ("m", "A", "F")}
