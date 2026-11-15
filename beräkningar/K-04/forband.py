"""Förbanden i takets och väggarnas knutpunkter (#119): krafterna ur balkmodellen mot ett fästdon per slag av knutpunkt.

Balkmodellen har delarna ledat sammanfogade i knutpunkterna. Kraften som en del får av sin knutpunkt är summan av
ändkrafterna i delens element där, och den ska föras över av delens förband:

- takbalken mot hammarbandet (takfoten): lyft, kraft längs takbalken (i plan) och kraft tvärs den, längs väggen, mot
  ett par universalbeslag (ETA-07/0137: R_1 lyft, R_2/3 längs takbalken, R_4/5 tvärs den med excentriciteten e),
  med samverkan F_1/R_1 + F_2/R_2 + F_4/R_4 ≤ 1;
- takbalken mot nock- eller dalbalken: drag längs takbalken mot ett stålband över balken som binder ihop takbalkarna
  på var sida, spikat i varje takbalk (antalet spik efter draget; trycket går i anliggning mot balken), och lyft
  mot förankringsskruven snett genom takbalken in i balken (K-03);
- regeln eller stolpen mot hammarbandet: drag i toppen mot skruvarna snett genom regeln (som i foten), annars ett
  vinkelbeslag (som vid foten, utan bult).

Stålbandens ändar i takfallen spikas i hammarbandet eller balken där de slutar (kontroller.py prövar spiken), så att
bandets kraft går direkt dit och inte genom takbalkens förband.
"""
from __future__ import annotations

from typing import Any

import numpy as np

VARAKT = (0.6, 0.7, 0.8, 0.9, 1.1)          # k_mod för permanent, lång, medellång, kort och momentan last (konstruktionsvirke)


def _knutkraft(N: Any, F: np.ndarray, Lam: np.ndarray, d: int, nod: int) -> np.ndarray:
    """Kraften på delen d från knutpunkten nod, i husets axlar: (kombination, 3) [N]."""
    m = N.modell
    tot = np.zeros((F.shape[0], 3))
    for el in np.flatnonzero((N.element_del == d) & ((m.bi == nod) | (m.bj == nod))):
        tot += (F[:, el, 0:3] if m.bi[el] == nod else F[:, el, 6:9]) @ Lam[el]
    return tot


def kontrollera(N: Any, L: Any, A: Any, IN: dict[str, Any], skruv: tuple[float, float], beslag: tuple[float, float],
                band: dict[str, float], Fax03: float) -> dict[str, Any]:
    """Knutpunkternas krafter och förband. skruv: regelns skruvar i hammarbandet (karakteristiskt [N], γ_M), beslag:
    ett vinkelbeslag (karakteristiskt [N], γ_M), band: stålbandets NtRd och spikens FvRk [N], Fax03: K-03:s
    förankringsskruv [N, dimensionerande vid vind]."""
    P = IN["knutpunkter"]
    m, delar = N.modell, N.delar
    str_ = np.array([k.slag == "STR" for k in L.komb])
    kn = [k.namn for k in L.komb if k.slag == "STR"]
    kmod = np.array([k.kmod for k in L.komb])[str_]
    F = L.F[str_]
    gM, gB = P["gamma_M"], P["gamma_M_spik"]
    kW = float(IN["kombination"]["k_mod"]["W"])
    # universalbeslagen (två per takbalk): R_1,k med k_mod inräknat per lastvaraktighet, R_2/3 och R_4/5 ur spikens R_lat
    R1 = np.interp(kmod, VARAKT, P["R1k"]) * 1e3 / gM
    R23 = P["c23"] * kmod * P["Rlat_k"] * 1e3 / gM
    R45 = np.minimum(P["c45"] * kmod * P["Rlat_k"], np.interp(kmod, VARAKT, P["k1"]) * (P["b"] + P["k2"]) / P["e"]) * 1e3 / gM
    FvRd = kmod * band["FvRk"] / gB                      # en spik i stålbandet
    Fax = Fax03 * kmod / kW                              # förankringsskruven (K-03 räknar den för vind)
    vagg = ("yttervagg", "innervagg", "stolpe")
    takfot: list[dict[str, Any]] = []
    balk: list[dict[str, Any]] = []
    regel: list[dict[str, Any]] = []
    for d, lista in N.stationer.items():
        b = delar[d]
        if b.slag != "balk":
            continue
        if b.grupp == "takbalk" and b.typ == "T":
            for _, nod in lista:
                andra = [delar[x] for x in N.nod_delar[nod] if x != d]
                vid_vagg = any(a.typ == "H" and a.grupp in vagg for a in andra)
                if not vid_vagg and not any(a.grupp == "balk" for a in andra):
                    continue
                v = m.x[nod, :2] - b.c[:2]
                v = v / (np.linalg.norm(v) + 1e-9)       # längs takbalken i plan, mot knutpunkten
                FR = _knutkraft(N, F, A.Lam, d, nod)
                lyft = np.maximum(-FR[:, 2], 0.0)
                ax = FR[:, :2] @ v                       # drag +: knutpunkten drar takbalken mot sig
                tv = np.abs(FR[:, :2] @ np.array([-v[1], v[0]]))
                if vid_vagg:
                    u = lyft / R1 + np.abs(ax) / R23 + tv / R45
                    k = int(np.argmax(u))
                    takfot.append({"del": b.namn, "x": float(m.x[nod, 0]), "y": float(m.x[nod, 1]), "eta": float(u[k]),
                                   "komb": kn[k], "lyft": float(lyft[k]), "langs": float(ax[k]), "tvars": float(tv[k])})
                else:
                    drag = np.maximum(ax, 0.0)
                    n_spik = max(int(P["spik_min"]), int(np.ceil((drag / FvRd).max() - 1e-9)))
                    k = int(np.argmax(drag / FvRd))
                    n_skruv = max(1, int(np.ceil((lyft / Fax).max() - 1e-9)))
                    balk.append({"del": b.namn, "x": float(m.x[nod, 0]), "y": float(m.x[nod, 1]), "drag": float(drag[k]),
                                 "komb": kn[k], "spik": n_spik, "eta_band": float(drag.max() / band["NtRd"]),
                                 "tryck": float(np.maximum(-ax, 0.0).max()), "lyft": float(lyft.max()),
                                 "skruv": n_skruv, "eta_lyft": float((lyft / (n_skruv * Fax)).max())})
        elif b.grupp in ("yttervagg", "innervagg") and abs(b.ex[2]) > 0.9 and len(lista) > 1:
            (_, n0), (_, n1) = lista[0], lista[-1]
            topp = n1 if m.x[n1, 2] > m.x[n0, 2] else n0
            if not any(delar[x].typ == "H" for x in N.nod_delar[topp] if x != d):
                continue
            drag = np.maximum(_knutkraft(N, F, A.Lam, d, topp)[:, 2], 0.0)       # knutpunkten drar regeln uppåt
            Rs, Rb = kmod * skruv[0] / skruv[1], kmod * beslag[0] / beslag[1]
            med_beslag = bool(np.any(drag > Rs))
            u = drag / (Rb if med_beslag else Rs)
            k = int(np.argmax(u))
            regel.append({"del": b.namn, "drag": float(drag[k]), "komb": kn[k], "beslag": med_beslag, "eta": float(u[k])})
    tf = max(takfot, key=lambda r: r["eta"])
    bk = max(balk, key=lambda r: r["spik"] + r["drag"] * 1e-6)
    rg = max(regel, key=lambda r: r["drag"])
    return {"takfot": sorted(takfot, key=lambda r: -r["eta"]), "balk": sorted(balk, key=lambda r: -r["drag"]),
            "regel": sorted(regel, key=lambda r: -r["drag"]),
            "R1_W": float(np.interp(kW, VARAKT, P["R1k"]) * 1e3 / gM), "R23_W": float(P["c23"] * kW * P["Rlat_k"] * 1e3 / gM),
            "R45_W": float(min(P["c45"] * kW * P["Rlat_k"], np.interp(kW, VARAKT, P["k1"]) * (P["b"] + P["k2"]) / P["e"])
                           * 1e3 / gM),
            "FvRd_W": float(kW * band["FvRk"] / gB), "Fax_W": float(Fax03),
            "Rs_W": float(kW * skruv[0] / skruv[1]), "Rb_W": float(kW * beslag[0] / beslag[1]),
            "storst": {"takfot": tf, "balk": bk, "regel": rg},
            "ok": bool(tf["eta"] <= 1.0 and max(r["eta_band"] for r in balk) <= 1.0
                       and max(r["eta"] for r in regel) <= 1.0)}
