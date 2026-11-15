"""Förbanden i takets och väggarnas knutpunkter (#119): krafterna ur balkmodellen mot ett fästdon per slag av knutpunkt.

Balkmodellen har delarna ledat sammanfogade i knutpunkterna. Kraften som en del får av sin knutpunkt är summan av
ändkrafterna i delens element där, och den ska föras över av delens förband:

- takbalken mot hammarbandet (takfoten): lyft, kraft längs takbalken (i plan) och kraft tvärs den, längs väggen, mot
  ett par universalbeslag (ETA-07/0137: R_1 lyft, R_2/3 längs takbalken, R_4/5 tvärs den med excentriciteten e),
  med samverkan F_1/R_1 + F_2/R_2 + F_4/R_4 ≤ 1. Där ett av takfallets stålband slutar på takbalken (inom BAND_ANDE
  från hammarbandet) drar bandets komponent längs väggen takbalkens överkant i sidled: bandet spikas också i en
  kortling i facket bredvid, som står på hammarbandet med vinkelbeslag i ändarna och tar den kraften åt båda hållen
  (sidled och vältning F h / L), och takbalkens beslag prövas för lyftet och kraften längs takbalken;
- takbalken mot nock- eller dalbalken: drag längs takbalken mot ett stålband över balken som binder ihop takbalkarna
  på var sida, spikat i varje takbalk (antalet spik efter draget; trycket går i anliggning mot balken; utan takbalk
  mitt emot spikas bandet i limträets sida på andra sidan), och lyft mot förankringsskruven snett genom takbalken in
  i balken (K-03);
- regeln eller stolpen mot hammarbandet: drag i toppen mot skruvarna snett genom regeln (som i foten), annars ett
  vinkelbeslag (som vid foten, utan bult). Draget är delens ändkraft med väggskivornas hörnkraft i knutpunkten från
  delens egen vägg: balkmodellen samlar skivans kantkraft i hörnen, och skivan är spikad i både regeln och
  hammarbandet. Skikten i en sammansatt stolpe prövas tillsammans, andra delar i samma nod var för sig.

En takbalk som vilar på en nock- eller dalbalk räknas som knutpunkt mot balken också där en innervägg eller takstol
når samma nod. Takbalkens tryck mot balken går i anliggning.

Stålbandens ändar i takfallen spikas i takbalken där de slutar och vid takfoten också i kortlingen (kontroller.py
prövar spiken)."""
from __future__ import annotations

from typing import Any

import numpy as np

import natverk
from kontroller import Material, _krafter_langs

RORA = 5.0                                  # delar med högst så stor glipa ligger an mot varandra [mm]
VARAKT = (0.6, 0.7, 0.8, 0.9, 1.1)          # k_mod för permanent, lång, medellång, kort och momentan last (konstruktionsvirke)


def _knutkraft(N: Any, F: np.ndarray, Lam: np.ndarray, d: int, nod: int) -> np.ndarray:
    """Kraften på delen d från knutpunkten nod, i husets axlar: (kombination, 3) [N]."""
    m = N.modell
    tot = np.zeros((F.shape[0], 3))
    for el in np.flatnonzero((N.element_del == d) & ((m.bi == nod) | (m.bj == nod))):
        tot += (F[:, el, 0:3] if m.bi[el] == nod else F[:, el, 6:9]) @ Lam[el]
    return tot


def kontrollera(N: Any, L: Any, A: Any, IN: dict[str, Any], skruv: tuple[float, float], beslag: tuple[float, float],
                band: dict[str, float], Fax03: float, SK: list[Any]) -> dict[str, Any]:
    """Knutpunkternas krafter och förband. skruv: regelns skruvar i hammarbandet (karakteristiskt [N], γ_M), beslag:
    ett vinkelbeslag (R_1,k och R_2/3,k [N], γ_M), band: stålbandets NtRd och spikens FvRk [N], Fax03: K-03:s
    förankringsskruv [N, dimensionerande vid vind], SK: skjuvskivorna (natverk.skjuvskivor)."""
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
    toppar: dict[int, list[int]] = {}
    vaggskikt = ("utegips", "osb")
    # takfallens stålband som slutar på en takbalk nära takfoten: (takbalk, station) -> bandets index
    band_ande: dict[int, list[float]] = {}
    for j, d in enumerate(N.band):
        if delar[d].grupp == "band_vagg":
            continue
        for n_ in (m.ti[j], m.tj[j]):
            for x in N.nod_delar[n_]:
                if delar[x].grupp == "takbalk" and delar[x].typ == "T":
                    band_ande.setdefault(x, []).extend(s for s, n2 in N.stationer[x] if n2 == n_)
    # kortlingens vinkelbeslag (som vid regelns fot): ett beslag, lyft och sidled
    R1b, R23b = kmod * beslag[0] / beslag[2], kmod * beslag[1] / beslag[2]
    hk, Lk = P["kortling_h"], P["kortling_L"]
    for d, lista in N.stationer.items():
        b = delar[d]
        if b.slag != "balk":
            continue
        if b.grupp == "takbalk" and b.typ == "T":
            sedda: set[int] = set()
            for s_nod, nod in lista:
                if nod in sedda:
                    continue
                sedda.add(nod)
                andra = [delar[x] for x in N.nod_delar[nod] if x != d]
                vid_balk = any(a.grupp == "balk" for a in andra)
                # takbalken vilar på nock- eller dalbalken också där en innervägg eller takstol når samma knutpunkt:
                # förbandet är bandet över balken, inte takfotens beslag
                vid_vagg = not vid_balk and any(a.typ == "H" and a.grupp in vagg for a in andra)
                if not vid_vagg and not vid_balk:
                    continue
                v = m.x[nod, :2] - b.c[:2]
                v = v / (np.linalg.norm(v) + 1e-9)       # längs takbalken i plan, mot knutpunkten
                FR = _knutkraft(N, F, A.Lam, d, nod)
                lyft = np.maximum(-FR[:, 2], 0.0)
                ax = FR[:, :2] @ v                       # drag +: knutpunkten drar takbalken mot sig
                tv = np.abs(FR[:, :2] @ np.array([-v[1], v[0]]))
                if vid_vagg:
                    # där ett av takfallets stålband slutar på takbalken (BAND_ANDE) drar bandet takbalken längs väggen,
                    # i takbalkens överkant: bandet spikas också i en kortling i facket bredvid, som står på
                    # hammarbandet med ett vinkelbeslag i var ände och tar den kraften (åt båda hållen). Beslagen på
                    # takbalken prövas då för lyftet och kraften längs den.
                    kort = any(abs(s - s_nod) <= natverk.BAND_ANDE for s in band_ande.get(d, []))
                    u = lyft / R1 + np.abs(ax) / R23 + (0.0 if kort else tv / R45)
                    k = int(np.argmax(u))
                    rad = {"del": b.namn, "x": float(m.x[nod, 0]), "y": float(m.x[nod, 1]), "eta": float(u[k]),
                           "komb": kn[k], "lyft": float(lyft[k]), "langs": float(ax[k]), "tvars": float(tv[k]),
                           "kortling": kort}
                    if kort:
                        # kraften F i kortlingens överkant: F/2 i sidled i varje beslag och F h/L i lyft i den ena änden;
                        # två beslag i var ände (ett på var sida) om ett inte räcker
                        for per_ande in (1, 2):
                            uk = tv * hk / (Lk * per_ande * R1b) + tv / (2 * per_ande * R23b)
                            if uk.max() <= 1.0:
                                break
                        kk = int(np.argmax(uk))
                        rad.update({"kortling_beslag": 2 * per_ande, "kortling_eta": float(uk[kk]),
                                    "kortling_kraft": float(tv[kk]), "kortling_komb": kn[kk]})
                    takfot.append(rad)
                else:
                    # en takbalk på andra sidan balken i samma knutpunkt: bandet över balken binder ihop dem; annars
                    # spikas bandet i limträets sida på andra sidan
                    mittemot = any(a.grupp == "takbalk" and a.typ == "T" and float((a.c[:2] - m.x[nod, :2]) @ v) > 0
                                   for a in andra)
                    drag = np.maximum(ax, 0.0)
                    n_spik = max(int(P["spik_min"]), int(np.ceil((drag / FvRd).max() - 1e-9)))
                    k = int(np.argmax(drag / FvRd))
                    n_skruv = max(1, int(np.ceil((lyft / Fax).max() - 1e-9)))
                    balk.append({"del": b.namn, "x": float(m.x[nod, 0]), "y": float(m.x[nod, 1]), "drag": float(drag[k]),
                                 "tvars": float(tv.max()), "mittemot": mittemot,
                                 "komb": kn[k], "spik": n_spik, "eta_band": float(drag.max() / band["NtRd"]),
                                 "tryck": float(np.maximum(-ax, 0.0).max()), "lyft": float(lyft.max()),
                                 "skruv": n_skruv, "eta_lyft": float((lyft / (n_skruv * Fax)).max())})
        elif b.grupp in ("yttervagg", "innervagg") and abs(b.ex[2]) > 0.9 and len(lista) > 1:
            (_, n0), (_, n1) = lista[0], lista[-1]
            topp = n1 if m.x[n1, 2] > m.x[n0, 2] else n0
            if any(delar[x].typ == "H" for x in N.nod_delar[topp] if x != d):
                toppar.setdefault(topp, []).append(d)
    # regelns topp: kraften mellan delen och det som ligger ovanpå, med väggskivornas hörnkraft i knutpunkten från delens
    # egen vägg (skivan är spikad i både regeln och hammarbandet; balkmodellen samlar skivans kantkraft i hörnen).
    # Skikten i en sammansatt stolpe prövas tillsammans; andra delar som balkmodellen låter mötas i samma nod (reglar i
    # andra väggar, en stolpe bredvid) prövas var för sig.
    Rs, Rb = kmod * skruv[0] / skruv[1], kmod * beslag[0] / beslag[2]
    vaggdef = {v["kod"]: (np.array(v["origo"][:2], float), np.array(v["u"][:2], float)) for v in N.ytor["vaggar"]}
    for topp, ds in toppar.items():
        under = set(ds) | {x for x in N.nod_delar[topp] if delar[x].slag == "balk" and abs(delar[x].ex[2]) > 0.9
                           and delar[x].grupp in vagg and m.x[topp, 2] >= max(m.x[n_, 2] for _, n_ in N.stationer[x]) - 1.0}
        # delar som ligger an mot varandra (glipan högst RORA) eller hör till samma stolpe verkar tillsammans
        lista_ = sorted(under)
        lador = {x: (delar[x].c - np.abs(delar[x].E.T) @ delar[x].halv, delar[x].c + np.abs(delar[x].E.T) @ delar[x].halv)
                 for x in lista_}
        rot = {x: x for x in lista_}

        def hitta(x: int) -> int:
            while rot[x] != x:
                x = rot[x]
            return x
        for i_, x in enumerate(lista_):
            for y in lista_[i_ + 1:]:
                (a0, a1), (b0, b1) = lador[x], lador[y]
                glipa = np.maximum(np.maximum(a0 - b1, b0 - a1), 0.0)
                if (delar[x].stolpe and delar[x].stolpe == delar[y].stolpe) or np.linalg.norm(glipa[:2]) <= RORA:
                    rot[hitta(y)] = hitta(x)
        grupper: dict[int, list[int]] = {}
        for x in lista_:
            grupper.setdefault(hitta(x), []).append(x)
        kraft_ = {g: sum(_knutkraft(N, F, A.Lam, x, topp)[:, 2] for x in ds_) for g, ds_ in grupper.items()}
        # skivans hörnkraft går till den del i skivans vägg som står närmast hörnet (facket u0–u1 längs väggen; i
        # toppen har u0-hörnet den lodräta termen −z, u1-hörnet +z)
        for c, n_, v in zip(m.s_c, m.s_nod, m.s_v):
            if n_ != topp or SK[c].skikt not in vaggskikt or abs(v[2]) < 1e-12:
                continue
            vg = vaggdef[SK[c].vagg]
            u_horn = SK[c].u0 if v[2] < 0 else SK[c].u1
            kand = [(abs(float((delar[x].c[:2] - vg[0]) @ vg[1]) - u_horn), g) for g, ds_ in grupper.items() for x in ds_
                    if delar[x].element == SK[c].vagg]
            if kand:
                g = min(kand)[1]
                kraft_[g] = kraft_[g] + L.skiva[str_, c] * v[2]
        for g, ds_ in grupper.items():
            drag = np.maximum(kraft_[g], 0.0)            # knutpunkten drar delen uppåt
            med_beslag = bool(np.any(drag > Rs))
            n_b = 1 if not med_beslag or np.all(drag <= Rb) else 2       # ett beslag på var sida om ett inte räcker
            u = drag / (n_b * Rb if med_beslag else Rs)
            k = int(np.argmax(u))
            namn_ = sorted(delar[x].namn for x in ds_)
            regel.append({"del": namn_[0], "delar": namn_, "nod": int(topp), "drag": float(drag[k]), "komb": kn[k],
                          "beslag": med_beslag, "n_beslag": n_b if med_beslag else 0, "eta": float(u[k])})
    tf = max(takfot, key=lambda r: r["eta"])
    bk = max(balk, key=lambda r: r["spik"] + r["drag"] * 1e-6)
    rg = max(regel, key=lambda r: r["drag"])
    return {"takfot": sorted(takfot, key=lambda r: -r["eta"]), "balk": sorted(balk, key=lambda r: -r["drag"]),
            "regel": sorted(regel, key=lambda r: -r["drag"]),
            "R1_W": float(np.interp(kW, VARAKT, P["R1k"]) * 1e3 / gM), "R23_W": float(P["c23"] * kW * P["Rlat_k"] * 1e3 / gM),
            "R45_W": float(min(P["c45"] * kW * P["Rlat_k"], np.interp(kW, VARAKT, P["k1"]) * (P["b"] + P["k2"]) / P["e"])
                           * 1e3 / gM),
            "FvRd_W": float(kW * band["FvRk"] / gB), "Fax_W": float(Fax03),
            "R1b_W": float(kW * beslag[0] / beslag[2]), "R23b_W": float(kW * beslag[1] / beslag[2]),
            "Rs_W": float(kW * skruv[0] / skruv[1]), "Rb_W": float(kW * beslag[0] / beslag[2]),
            "storst": {"takfot": tf, "balk": bk, "regel": rg},
            "ok": bool(tf["eta"] <= 1.0 and max(r["eta_band"] for r in balk) <= 1.0
                       and all(r["kortling_eta"] <= 1.0 for r in takfot if r["kortling"])
                       and max(r["eta"] for r in regel) <= 1.0)}


def balkar_i_sidled(N: Any, L: Any, IN: dict[str, Any], K01: dict[str, Any]) -> list[dict[str, Any]]:
    """Nock- och dalbalkarna i sidled: takbalkarnas krafter längs balken (banden över balken, takbalkar utan någon mitt
    emot) böjer limträet i sidled, vilket K-01 (lodrät last) inte räknar. Böjning i sidled ur balkmodellen, limträet utan
    plåtarna, med K-01:s utnyttjande i böjning och skjuvning lodrätt: SS-EN 1995-1-1 6.1.6 (k_m 0,7) och 6.1.7."""
    m = N.modell
    str_ = np.array([k.slag == "STR" for k in L.komb])
    kmod = np.array([k.kmod for k in L.komb])[str_]
    kn = [k.namn for k in L.komb if k.slag == "STR"]
    Le = np.linalg.norm(m.x[m.bj] - m.x[m.bi], axis=1)
    K_ = _krafter_langs(L.F[str_], L.q[str_], Le[None, :])
    kcr = float(IN["kontroll"]["k_cr"])
    k01 = {f"{'NB' if b['typ'] == 'nock' else 'DB'}{b['nr']}": b for b in K01["balkar"]}
    ut = []
    for d in sorted({int(x) for x in N.element_del if N.delar[x].grupp == "balk"}, key=lambda d: N.delar[d].namn):
        b = N.delar[d]
        Mt = Material(b.material, IN["material"][b.material]) if b.material in IN["material"] else None
        if Mt is None or b.namn not in k01:
            continue
        e = np.flatnonzero(N.element_del == d)
        bb, hh = b.bredd, b.hojd                          # bredden i sidled
        fmd = kmod[:, None] * Mt.fmk * float(Mt.kh(np.array(bb))) / Mt.gamma_M
        fvd = kmod[:, None] * Mt.fvk / Mt.gamma_M
        # böjningen i sidled i det samverkande tvärsnittet (limträet och plåtarna, limmade enligt K-01): balkmodellens
        # I_z i limträets E; plåtens spänning n gånger större vid samma avstånd från mitten (plåten lika bred)
        Iz, ns = m.bsek[e, 4], float(IN["material"]["S355"]["E0mean"]) / m.bsek[e, 0]
        sig = K_["Mz"][:, e] * (bb / 2) / Iz
        um = (sig / fmd).max(axis=1)
        S = IN["material"]["S355"]
        up = (ns * sig / (float(S["fy"]) / float(S["gamma_M0"]))).max(axis=1)
        uv = (1.5 * K_["Vy"][:, e] / (kcr * bb * hh) / fvd).max(axis=1)      # tvärkraften i limträet ensamt
        k = int(np.argmax(np.maximum(um, uv)))
        kon = {c["namn"]: float(c["u"].replace(",", ".")) / 100 for c in k01[b.namn]["kontroller"]}
        m1, v1 = kon.get("Limträ, böjspänning", 0.0), kon.get("Limträ, skjuvspänning", 0.0)
        p1 = kon.get("Plåt, normalspänning", 0.0)
        eta_m = max(m1 + 0.7 * um[k], 0.7 * m1 + um[k])
        eta_v = float(np.hypot(v1, uv[k]))                # skjuvspänningarna i de två riktningarna möts i mitten
        eta_p = p1 + float(up.max())                      # plåtens kant: lodrät och sidled, som en summa
        ut.append({"del": b.namn, "Mz": float(K_["Mz"][k, e].max()), "Vy": float(K_["Vy"][k, e].max()), "komb": kn[k],
                   "u_sidled": float(max(um[k], uv[k])), "eta_m": float(eta_m), "eta_v": eta_v, "eta_p": eta_p,
                   "eta": float(max(eta_m, eta_v, eta_p))})
    return ut
