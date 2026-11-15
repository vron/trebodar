"""Förankringen i bjälklaget: upplagens lyft och horisontalkraft till syllarna, betongbultarna och beslagen i modellen.

Balkmodellen håller varje syllnod och stolpfot fast i bjälklaget. I verkligheten håller syllen bara där bultarna sitter
(modellens betongbultar, barverk.json, en del snett inåt där en lodrät bult inte når betongen): mellan dem bär syllen
lyftet i böjning (fritt upplagd mellan två bultar, konsol utanför den yttersta), och regeln eller stolpen hålls i
syllen av skruvar snett genom regelns fot. Där det inte räcker har modellen vinkelbeslag vid regeln eller stolpen
(skruvade i regeln och syllen, med betongbult genom beslaget och syllen) eller ett förankringsbeslag (hold-down) på
regelgruppens insida: de för upplagets lyft direkt till sina bultar. En syllbit utan egna bultar hålls av beslagen på
den, vars bultar eller ankare går genom syllen: de andra upplagen på biten lyfter genom dem.

Två steg:
- kravet: beslagen som behövs vid varje upplag, i ordning (ett beslag med en bult, två, två med två bultar
  vardera, och där inte ens det räcker ett förankringsbeslag) vid de upplag som lyfter mest tills syllarna, bultarna
  och skruvarna räcker;
- kontrollen: modellens beslag (barverk.json) mot lasterna, och syllarna och bultarna med upplagen utan beslag. Saknas
  beslag som behövs, visas raderna som ska in i modellens tabell (forankring.VINKELBESLAG_PA, FORANKRINGSBESLAG_PA).

Kontrollerna per kombination (brottgränstillståndet, k_mod efter kombinationen):
- syllens böjning flatt: M_Ed ≤ f_m,d k_h b h² / 6 (h = syllens höjd, b = dess bredd);
- bulten: dragkraften längs bulten ≤ betongbultens N_Rd (krav på produkten, IN-01) och brickans tryck vinkelrätt
  fibrerna, f_c,90,d A_ef (SS-EN 1995-1-1 6.1.5, 30 mm längs fibrerna på var sida); en sned bult bär lodrätt
  bärförmågan gånger cos(lutningen);
- regelns infästning i syllen: skruvarnas utdrag, n f_ax,k d l_ef k_mod / γ_M;
- horisontalkraften i varje syllbit: summan delad på bultarna (beslagens bultar inräknade), bultens bärförmåga i syllen
  enligt SS-EN 1995-1-1 8.2.3 (bulten fast i betongen som en tjock plåt, enskärig) och betongbultens V_Rd (krav);
- vinkelbeslaget: R_1,d per beslag (databladet, hälften av två beslag) och bultarnas drag med bändningsfaktorn;
- förankringsbeslaget: R_1,d i träet (spiken), i stålet och i betongen (ankaret, databladet).
- betongen kring varje bult och ankare (SS-EN 1992-4, sprucken betong utan tilläggsarmering), med bultens verkliga
  avstånd till plattans kant (barverk.json): betongkonbrott i drag (7.2.1.4) och kantbrott i skjuvning (7.2.2.5), mot
  kanten och längs den, med samverkan (N/N_Rd)^1,5 + (V/V_Rd)^1,5 ≤ 1.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np

HORN = 100.0             # en syllnod hör till syllbiten inom så långt från dess ände (hörnen)
KATEGORIER = ("syll", "1 beslag", "2 beslag", "2 beslag, 2 bultar vardera", "förankringsbeslag")


@dataclass
class Bit:
    """En syllbit: väggen, u-intervallet, tvärsnittet (bredd, höjd) och bultarna (u, cos lutningen)."""
    vagg: str
    namn: str
    u0: float
    u1: float
    b: float
    h: float
    bultar: list[tuple[float, float]] = field(default_factory=list)
    kant: list[float] = field(default_factory=list)          # bultarnas avstånd till betongens kant


def _u(v: dict[str, Any], p: Any) -> float:
    return float((np.asarray(p[:2]) - np.asarray(v["origo"])) @ np.asarray(v["u"]))


def betong_drag(F: dict[str, Any], c: float, hef: float) -> float:
    """Betongkonbrott för ett ensamt ankare med kantavståndet c [N], dimensionerande (SS-EN 1992-4 7.2.1.4,
    sprucken betong, k_1 = 7,7): N⁰ = k_1 √f_ck h_ef^1,5, ytan (c + 1,5 h_ef) / (3 h_ef) och ψ_s = 0,7 + 0,3 c / (1,5 h_ef)."""
    n0 = 7.7 * math.sqrt(F["betong_fck"]) * hef ** 1.5
    yta = min(1.0, (c + 1.5 * hef) / (3 * hef))
    psi = min(1.0, 0.7 + 0.3 * c / (1.5 * hef))
    return n0 * yta * psi / F["gamma_Mc"]


def betong_skjuv(F: dict[str, Any], c: float, d: float, hef: float) -> float:
    """Betongens kantbrott för skjuvning mot kanten, ett ensamt ankare med kantavståndet c [N], dimensionerande
    (SS-EN 1992-4 7.2.2.5, sprucken betong, k_9 = 1,7): V⁰ = k_9 d^α l_f^β √f_ck c^1,5, med plattans tjocklek
    (ψ_h = √(1,5 c / h) ≥ 1 ökar bärförmågan per ytenhet men ytan minskar: tillsammans faktorn √(h / (1,5 c)) ≤ 1)."""
    lf = min(hef, 12 * d)
    a, b = 0.1 * math.sqrt(lf / c), 0.1 * (d / c) ** 0.2
    v0 = 1.7 * d ** a * lf ** b * math.sqrt(F["betong_fck"]) * c ** 1.5
    return v0 * min(1.0, math.sqrt(F["betong_h"] / (1.5 * c))) / F["gamma_Mc"]


def kapaciteter(IN: dict[str, Any], C24: Any) -> dict[str, Any]:
    """Bärförmågorna som beror på k_mod: funktioner av k_mod (N per bult, Nmm per syll) och fasta värden."""
    F = IN["forankring"]
    d = F["bult_d"]
    # brickan: tryck vinkelrätt fibrerna, 30 mm längs fibrerna på var sida (6.1.5), hålet borträknat
    ba, bb = F["bricka"]
    A_bricka = ba * (bb + 2 * 30.0) - math.pi * (F["bult_hal"] / 2) ** 2
    # bulten i syllen (8.2.3, tjock plåt enskärig, utan repverkan): f_h,k och M_y,Rk
    t1 = F["syll_h"]
    fhk = 0.082 * (1 - 0.01 * d) * C24.rhok
    Myk = 0.3 * F["bult_fu"] * d ** 2.6
    Fv_k = min(fhk * t1 * d, fhk * t1 * d * (math.sqrt(2 + 4 * Myk / (fhk * d * t1 ** 2)) - 1),
               2.3 * math.sqrt(Myk * fhk * d))
    # skruvarna snett genom regelns fot ned i syllen
    Fax_k = F["skruv_n"] * F["skruv_fax"] * F["skruv_d"] * F["skruv_lef"]
    # vinkelbeslaget: hälften av två beslags R_1,k (databladet) per beslag
    R1k = F["beslag_R1k_par"] / 2
    R23k = F["beslag_R23k_par"] / 2
    return {"R23k": R23k, "A_bricka": A_bricka, "fhk": fhk, "Myk": Myk, "Fv_k": Fv_k, "Fax_k": Fax_k, "R1k": R1k,
            "N_Rd": F["bult_NRd"] * 1e3, "V_Rd": F["bult_VRd"] * 1e3, "bandning": F["bandning"],
            "gM_beslag": F["beslag_gamma_M"]}


def _bitar(N: Any, BV: dict[str, Any]) -> dict[str, list[Bit]]:
    """Syllbitarna per vägg med bultarna (barverk.json), och väggarna."""
    V = {v["kod"]: v for v in BV["vaggar"]}
    bitar: dict[str, list[Bit]] = {}
    for b in N.delar:
        if b.typ != "S" or b.element not in V or b.grupp not in ("yttervagg", "innervagg"):
            continue
        v = V[b.element]
        ua, ub = sorted((_u(v, b.a0), _u(v, b.b0)))
        # bredden är väggens: den bredare syllens inre remsa (ytterväggarna, urtagen i hörnen) räknas inte i böjningen
        bitar.setdefault(b.element, []).append(Bit(b.element, b.namn, ua - 25.0, ub + 25.0,
                                                   min(max(b.bredd, b.hojd), float(v["tjocklek"])),
                                                   min(b.bredd, b.hojd)))
    for x in BV["bultar"]["lagen"]:
        v = V.get(x["vagg"])
        if v is None:
            continue
        u = _u(v, np.array([x["x"], x["y"]]))
        for bit in bitar.get(x["vagg"], []):
            if bit.u0 <= u <= bit.u1:
                bit.bultar.append((u, math.cos(math.radians(x.get("lutning", 0.0)))))
                bit.kant.append(float(x.get("kant", 1e4)))
                break
    for lista in bitar.values():
        for bit in lista:
            ordning = sorted(range(len(bit.bultar)), key=lambda j: bit.bultar[j])
            bit.bultar = [bit.bultar[j] for j in ordning]
            bit.kant = [bit.kant[j] for j in ordning]
    return bitar


def _syll(bit: Bit, laster: list[tuple[float, np.ndarray]]) -> tuple[np.ndarray, np.ndarray]:
    """Syllens största moment (per kombination) och bultarnas lodräta kraft (per kombination, per bult) av lasterna
    (u, lyft per kombination): fritt upplagd mellan bultarna, konsol utanför de yttersta."""
    nk = len(laster[0][1]) if laster else 0
    nb = len(bit.bultar)
    M = np.zeros(nk)
    Nb = np.zeros((nk, nb))
    ub = [u for u, _ in bit.bultar]
    spann: dict[int, list[tuple[float, np.ndarray]]] = {}
    for u, F in laster:
        if u <= ub[0]:
            Nb[:, 0] += F
            M = np.maximum(M, F * (ub[0] - u))
        elif u >= ub[-1]:
            Nb[:, -1] += F
            M = np.maximum(M, F * (u - ub[-1]))
        else:
            j = int(np.searchsorted(ub, u)) - 1
            spann.setdefault(j, []).append((u, F))
    for j, ls in spann.items():
        a, b = ub[j], ub[j + 1]
        L = b - a
        RA = sum(F * (b - u) for u, F in ls) / L
        Nb[:, j] += RA
        Nb[:, j + 1] += sum(F * (u - a) for u, F in ls) / L
        for x, _ in ls:
            Mx = RA * (x - a) - sum(F * (x - u) for u, F in ls if u < x)
            M = np.maximum(M, Mx)
    return M, Nb


def _modellens_beslag(BV: dict[str, Any], nod_namn: list[set[str]]) -> dict[int, list[dict[str, Any]]]:
    """Modellens beslag per upplag (index): beslaget hör till upplaget där dess regel eller stolpe står."""
    ut: dict[int, list[dict[str, Any]]] = {}
    for b in BV.get("beslag", []):
        i = next((i for i, s in enumerate(nod_namn) if b["nyckel"] in s), None)
        if i is None:
            i = next((i for i, s in enumerate(nod_namn) if b["del"] in s), None)
        if i is not None:
            ut.setdefault(i, []).append(b)
    return ut


def _text(besl: list[dict[str, Any]]) -> str:
    if not besl:
        return "–"
    if any(b["slag"] != "ABR10525" for b in besl):
        return " + ".join(sorted({b["slag"] for b in besl}))
    nb = sorted({len(b["bultar"]) for b in besl})
    sneda = sum(1 for b in besl for x in b["bultar"] if x["lutning"] > 0.5)
    return (f"{len(besl)} beslag" + (f", {nb[0]} bultar vardera" if nb == [2] else "") +
            (f" ({sneda} snett)" if sneda else ""))


def _betongtabell(F: dict[str, Any], bitar: dict[str, list[Bit]], BV: dict[str, Any]) -> list[dict[str, Any]]:
    """Betongens bärförmåga per slag av ankare vid det minsta kantavståndet i modellen (för rapporten)."""
    ytter = {k for k in bitar if len(k) == 3}
    rader = []
    grupper = [
        ("Syllens bult M%g, ytterväggarna" % F["bult_d"], F["bult_d"], F["bult_hef"],
         [c for k, ls in bitar.items() if k in ytter for b in ls for c in b.kant]),
        ("Syllens bult M%g, innerväggarna" % F["bult_d"], F["bult_d"], F["bult_hef"],
         [c for k, ls in bitar.items() if k not in ytter for b in ls for c in b.kant]),
        ("Vinkelbeslagets bult M%g" % F["bult_d"], F["bult_d"], F["bult_hef"],
         [x.get("kant", 1e4) for b in BV.get("beslag", []) if b["slag"] == "ABR10525" for x in b["bultar"]]),
        ("Förankringsbeslagets ankare M%g" % F["halldon_d"], F["halldon_d"], F["halldon_hef"],
         [x.get("kant", 1e4) for b in BV.get("beslag", []) if b["slag"] != "ABR10525" for x in b["bultar"]]),
    ]
    for namn, d, hef, kanter in grupper:
        if kanter:
            c = min(kanter)
            rader.append({"namn": namn, "antal": len(kanter), "c": c, "hef": hef, "N": betong_drag(F, c, hef),
                          "V": betong_skjuv(F, c, d, hef)})
    return rader


K03_KOMB = "K-03: stolpens lyft"


def kontrollera(N: Any, L: Any, IN: dict[str, Any], BV: dict[str, Any], C24: Any,
                lyft03: dict[str, float]) -> dict[str, Any]:
    """Förankringen: kravet på beslag per upplag, modellens beslag mot lasterna och syllarnas och bultarnas
    utnyttjande och horisontalkraften per syllbit. lyft03 är K-03:s lyft per stolpe [N] (K-01:s minsta stödreaktion:
    vindlyft och fältvis snö på nock- och dalbalkarna, som balkmodellen inte har): det prövas som en egen kombination,
    delat lika på stolpens upplag, så att varje stolpe förankras för det största av de två."""
    F_ = IN["forankring"]
    K = kapaciteter(IN, C24)
    m, delar = N.modell, N.delar
    str_ = np.array([k.slag == "STR" for k in L.komb])
    kn = [k.namn for k in L.komb if k.slag == "STR"]
    kmod = np.array([k.kmod for k in L.komb])[str_]
    R = L.R[str_][..., :3]
    X = np.asarray(m.x)[m.upplag]
    upp = [next((delar[d] for d in N.nod_delar[n_] if delar[d].upplagd), delar[N.nod_delar[n_][0]])
           for n_ in m.upplag]
    nod_namn = [{delar[d].namn for d in N.nod_delar[n_]} for n_ in m.upplag]
    rad03 = np.zeros((1, R.shape[1], 3))
    for stolpe, kraft in lyft03.items():                         # upplagen under stolpens stående delar
        vid = [i for i, n_ in enumerate(m.upplag)
               if any(stolpe in (delar[d].stolpe, delar[d].namn) and delar[d].typ != "S" for d in N.nod_delar[n_])]
        assert vid, f"K-03:s stolpe {stolpe} har inget upplag i balkmodellen"
        rad03[0, vid, 2] = -kraft / len(vid)
    R = np.concatenate([R, rad03])
    kn.append(K03_KOMB)
    kmod = np.append(kmod, float(IN["kombination"]["k_mod"]["S"]))
    lyft = np.maximum(-R[..., 2], 0.0)                           # (k, upplag) [N]
    V = {v["kod"]: v for v in BV["vaggar"]}
    bitar = _bitar(N, BV)
    gM = C24.gamma_M
    fmd = kmod * C24.fmk / gM
    fc90d = kmod * C24.fc90k / gM
    R_skruv = kmod * K["Fax_k"] / gM
    N_bult = np.minimum(K["N_Rd"], fc90d * K["A_bricka"])        # bult med bricka, längs bulten
    R_beslag = kmod * K["R1k"] * 1e3 / K["gM_beslag"]             # ett beslag
    # kravets kategorier: ett beslag med en bult (bändningen), två, två med två bultar vardera
    kat_R = [None, np.minimum(R_beslag, K["N_Rd"] / K["bandning"]),
             2 * np.minimum(R_beslag, K["N_Rd"] / K["bandning"]),
             2 * np.minimum(R_beslag, 2 * K["N_Rd"] / K["bandning"])]
    R23_beslag = kmod * K["R23k"] * 1e3 / K["gM_beslag"]          # ett beslag, i sidled
    Hn = np.hypot(R[..., 0], R[..., 1])                           # (k, upplag)
    # förankringsbeslaget: träet (spiken), stålet och ankaret i betongen
    R_hd = np.minimum(np.minimum(kmod * F_["halldon_R1k_tra"] / F_["halldon_gamma_M_tra"],
                                 F_["halldon_R1k_stal"] / F_["halldon_gamma_stal"]),
                      betong_drag(F_, 1e4, F_["halldon_hef"]) / 1e3) * 1e3

    def kategori(i: int, sidled: bool = False) -> int:
        """Beslagen för lyftet (och för stolpar direkt på plattan också sidkraften: F1/R1 + F2/R2 ≤ 1)."""
        for c in (1, 2, 3):
            n = 1 if c == 1 else 2
            u = lyft[:, i] / kat_R[c] + (Hn[:, i] / (n * R23_beslag) if sidled else 0.0)
            if np.all(u <= 1.0 + 1e-6):
                return c
        return 4

    def bar(besl: list[dict[str, Any]]) -> np.ndarray:
        """Modellens beslag vid ett upplag: lodrät bärförmåga per kombination. Bultarna och ankaret bär högst
        betongens konbrott vid sitt kantavstånd."""
        r = np.zeros(len(kn))
        for b in besl:
            if b["slag"] == "ABR10525":            # bultarna genom beslaget: lodrätt N_Rd cos(lutningen)
                bultar = sum(min(K["N_Rd"], betong_drag(F_, x.get("kant", 1e4), F_["bult_hef"]))
                             * math.cos(math.radians(x["lutning"])) for x in b["bultar"]) / K["bandning"]
                r = r + np.minimum(R_beslag, bultar)
            else:
                kant = min((x.get("kant", 1e4) for x in b["bultar"]), default=1e4)
                r = r + np.minimum(R_hd, betong_drag(F_, kant, F_["halldon_hef"]))
        return r

    noder: dict[int, dict[str, Any]] = {}
    pa_bit: dict[tuple[str, int], list[int]] = {}
    for i, d in enumerate(upp):
        v = V.get(d.element)
        u = _u(v, X[i]) if v else float("nan")
        bit_i = None
        if v and d.typ == "S":
            avst = [max(bit.u0 - u, u - bit.u1, 0.0) for bit in bitar.get(d.element, [])]   # närmaste syllbit
            if avst and min(avst) <= HORN:
                bit_i = int(np.argmin(avst))
        noder[i] = {"del": d.namn, "element": d.element, "grupp": d.grupp, "u": u, "x": float(X[i, 0]),
                    "y": float(X[i, 1]), "bit": bit_i, "kat": 0, "sidled": False}
        if bit_i is not None:
            pa_bit.setdefault((d.element, bit_i), []).append(i)
        elif lyft[:, i].max() > 100.0 or Hn[:, i].max() > 100.0:   # stolpe eller regel direkt på plattan
            noder[i]["kat"] = kategori(i, sidled=True)
            noder[i]["sidled"] = True
    modell = _modellens_beslag(BV, nod_namn)

    def syllen(bit: Bit, idx: list[int]) -> tuple[np.ndarray, np.ndarray]:
        if not idx or not bit.bultar:
            return np.zeros(len(kn)), np.zeros((len(kn), max(len(bit.bultar), 1)))
        return _syll(bit, [(noder[i]["u"], lyft[:, i]) for i in idx])

    def bultens_drag(bit: Bit) -> np.ndarray:
        """Bultarnas lodräta bärförmåga (k, bult): brickan mot syllen, produktens krav och betongens konbrott."""
        nc = np.array([betong_drag(F_, c, F_["bult_hef"]) for c in bit.kant])
        return np.minimum(N_bult[:, None], nc[None, :]) * np.array([c for _, c in bit.bultar])[None, :]

    def syllen_ok(bit: Bit, M: np.ndarray, Nb: np.ndarray) -> bool:
        W = bit.b * bit.h ** 2 / 6
        kh = min((150 / bit.h) ** 0.2, 1.3)
        Nr = bultens_drag(bit)
        return bool(np.all(M <= fmd * kh * W + 1e-6) and np.all(Nb <= Nr + 1e-6))

    # kravet: noderna på syllen så länge syllen, bultarna och skruvarna räcker, annars beslag (störst lyft först)
    for (vagg, j), idx in sorted(pa_bit.items()):
        bit = bitar[vagg][j]
        kvar = [i for i in idx if lyft[:, i].max() > 1.0e-3]
        while True:
            for i in [i for i in kvar if np.any(lyft[:, i] > R_skruv)]:     # regelns skruvar räcker inte
                noder[i]["kat"] = kategori(i)
            kvar = [i for i in kvar if noder[i]["kat"] == 0]
            if not kvar:
                break
            if not bit.bultar:
                for i in kvar:
                    noder[i]["kat"] = kategori(i)
                continue
            M, Nb = syllen(bit, kvar)
            if syllen_ok(bit, M, Nb):
                break
            i = max(kvar, key=lambda i: lyft[:, i].max())
            noder[i]["kat"] = kategori(i)
    # en syllbit utan egna bultar men med beslag i modellen: beslagens bultar eller ankare går genom syllen och håller
    # den, så att de andra upplagen på biten lyfter genom beslagen (på säker sida tar varje beslag hela deras lyft)
    via: dict[int, list[int]] = {}
    tillagg = np.zeros_like(lyft)
    for (vagg, j), idx in pa_bit.items():
        if bitar[vagg][j].bultar:
            continue
        med = [i for i in idx if i in modell]
        utan = [i for i in idx if lyft[:, i].max() > 1.0e-3 and i not in modell]
        if med and utan:
            for i in utan:
                via[i] = med
            for i in med:
                tillagg[:, i] += lyft[:, utan].sum(axis=1)
    # kontrollen: modellens beslag, och syllarna och bultarna med upplagen utan beslag
    bit_ut = []
    for (vagg, j), idx in sorted(pa_bit.items()):
        bit = bitar[vagg][j]
        kvar = [i for i in idx if lyft[:, i].max() > 1.0e-3 and i not in modell and i not in via]
        M, Nb = syllen(bit, kvar)
        W = bit.b * bit.h ** 2 / 6
        kh = min((150 / bit.h) ** 0.2, 1.3)
        Nr = bultens_drag(bit) if bit.bultar else N_bult[:, None]
        eta_M = float(np.max(M / (fmd * kh * W))) if kvar else 0.0
        eta_N = float(np.max(Nb / Nr)) if kvar and bit.bultar else (math.inf if kvar else 0.0)
        eta_S = max((float(np.max(lyft[:, i] / R_skruv)) for i in kvar), default=0.0)     # regelns skruvar
        # horisontalkraften: summan på syllbiten, delad på bultarna och beslagens bultar
        H = np.hypot(R[:, idx, 0].sum(axis=1), R[:, idx, 1].sum(axis=1))
        n_b = len(bit.bultar) + sum(len(b["bultar"]) for i in idx for b in modell.get(i, []))
        Fv_d = np.minimum(kmod * K["Fv_k"] / gM, K["V_Rd"])
        eta_H = float(np.max(H / (max(n_b, 1) * Fv_d))) if n_b else (0.0 if H.max() < 1.0 else math.inf)
        # betongen kring syllens bultar: kantbrott av skjuvningen (mot kanten och längs den) och konbrott av draget
        eta_B, kant = 0.0, min(bit.kant, default=1e4)
        if bit.bultar and vagg in V and kant < 1000.0:
            wv = np.array([-V[vagg]["u"][1], V[vagg]["u"][0]])            # in i huset (w = z × u)
            uv = np.array(V[vagg]["u"])
            ut_ = np.maximum(R[:, idx, :2].sum(axis=1) @ wv, 0.0) / max(n_b, 1)       # mot kanten, per bult
            la_ = np.abs(R[:, idx, :2].sum(axis=1) @ uv) / max(n_b, 1)                # längs kanten
            vres = np.hypot(ut_, la_)
            with np.errstate(divide="ignore", invalid="ignore"):
                cos_a = np.where(vres > 1e-9, ut_ / vres, 0.0)
            psi = np.sqrt(1.0 / (cos_a ** 2 + 0.25 * (1.0 - cos_a ** 2)))             # 1 mot kanten, 2 längs den
            v_rd = betong_skjuv(F_, kant, F_["bult_d"], F_["bult_hef"]) * psi
            n_rd = betong_drag(F_, kant, F_["bult_hef"])
            nb_ = Nb.max(axis=1) if kvar else np.zeros(len(kn))
            eta_B = float(np.max((nb_ / n_rd) ** 1.5 + (vres / v_rd) ** 1.5))
        bit_ut.append({"eta_B": eta_B, "kant": kant,"vagg": vagg, "syll": bit.namn, "langd": bit.u1 - bit.u0 - 50.0, "bultar": len(bit.bultar),
                       "sneda": sum(1 for _, c in bit.bultar if c < 0.999),
                       "b": bit.b, "h": bit.h, "eta_M": eta_M, "eta_N": eta_N, "eta_H": eta_H, "eta_S": eta_S,
                       "H": float(H.max()), "V_bult": float((H / max(n_b, 1)).max()),
                       "N_bult": float(Nb.max()) if kvar and bit.bultar else 0.0,
                       "beslag": sum(1 for i in idx if i in modell)})
    # upplagen med beslag i modellen eller som kräver beslag
    beslag = []
    forslag = []
    for i, n in noder.items():
        besl = modell.get(i, [])
        if n["kat"] == 0 and not besl:
            continue
        sid = n["sidled"]

        def utn(i: int) -> np.ndarray:
            besl = modell[i]
            nb = sum(1 for b in besl if b["slag"] == "ABR10525")
            return ((lyft[:, i] + tillagg[:, i]) / bar(besl) +
                    (Hn[:, i] / (max(nb, 1) * R23_beslag) if noder[i]["sidled"] else 0.0))
        if besl:
            u = utn(i)
            text = _text(besl)
        elif i in via:                             # genom beslagen på samma syllbit
            u = np.max([utn(j) for j in via[i]], axis=0)
            text = " + ".join(f"{_text(modell[j])} (u {noder[j]['u']:.0f})".replace("-", "−")
                              for j in via[i]) + " på syllen"
        else:
            u = np.full(len(kn), math.inf)
            text = _text(besl)
        k = int(np.argmax(u)) if math.isfinite(float(u.max())) else int(np.argmax(lyft[:, i]))
        eta = float(u[k])
        if eta > 1.0 or not math.isfinite(eta):    # raden till modellens tabell: regeln i syllens vägg
            st = [delar[d] for d in N.nod_delar[m.upplag[i]] if delar[d].slag == "balk" and abs(delar[d].ex[2]) > 0.9]
            nyckel = next((s.namn for s in st if s.element == n["element"]), st[0].namn if st else n["del"])
            krav = {1: "(1, 1)", 2: "(2, 1)", 3: "(2, 2)", 4: "förankringsbeslag"}[n["kat"] or 1]
            forslag.append(f"{n['del']} u {n['u']:.0f}: {nyckel} {krav}")
        beslag.append({**n, "lyft": float(lyft[k, i]), "komb": kn[k], "eta": eta, "H": float(Hn[k, i]),
                       "Hmax": float(Hn[:, i].max()), "modell": text, "krav": KATEGORIER[n["kat"]],
                       "halldon": any(b["slag"] != "ABR10525" for b in besl)})
    beslag.sort(key=lambda b: -b["lyft"])
    antal = {KATEGORIER[c]: sum(1 for b in beslag if b["kat"] == c) for c in range(1, 5)}
    kw = float(IN["kombination"]["k_mod"]["W"])
    Rb_W = kw * K["R1k"] * 1e3 / K["gM_beslag"]
    R_kat_W = [min(Rb_W, K["N_Rd"] / K["bandning"]), 2 * min(Rb_W, K["N_Rd"] / K["bandning"]),
               2 * min(Rb_W, 2 * K["N_Rd"] / K["bandning"])]
    R_hd_W = min(kw * F_["halldon_R1k_tra"] / F_["halldon_gamma_M_tra"],
                 F_["halldon_R1k_stal"] / F_["halldon_gamma_stal"],
                 betong_drag(F_, 1e4, F_["halldon_hef"]) / 1e3) * 1e3
    return {"bitar": bit_ut, "beslag": beslag, "forslag": forslag, "antal": antal, "K": K, "R_kat_W": R_kat_W,
            "R23_W": kw * K["R23k"] * 1e3 / K["gM_beslag"], "R_hd_W": R_hd_W,
            "n_modell": sum(len(v) for v in modell.values()),
            "R_skruv_W": kw * K["Fax_k"] / gM, "N_bult_W": float(min(K["N_Rd"], kw * C24.fc90k / gM * K["A_bricka"])),
            "Fv_d_W": float(min(kw * K["Fv_k"] / gM, K["V_Rd"])), "R_beslag_W": Rb_W,
            "max_lyft": float(lyft.max()), "n_lyft": int((lyft.max(axis=0) > 1.0).sum()), "n_upplag": len(upp),
            "F": F_, "betong": _betongtabell(F_, bitar, BV)}
