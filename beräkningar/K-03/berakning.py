"""
K-03: takbalkar, takstolar och stolpar enligt EKS 12 och SS-EN 1995-1-1.

    python berakning.py      # -> K-03_takbalkar_takstolar_stolpar.pdf

Läser indata.toml, geometri.json (K-03:s egen geometri, kontrollerad mot modellen med
verktyg/modellanalys/kontroll_k03.py), stolparnas laster ur K-05 (laster.py, som bygger på K-01) och huvudstolpens
krafter ur K-01:s resultat. Stoppar om K-05:s stödreaktioner (laster.K01, förda in för hand) inte är K-01:s.
Räknar takbalkarna per typ, takfönstren, upplagen mot nock- och dalbalkarna, takstolarna och stolparna, ritar
figurer (figurer03.py) och sätter ihop PDF via Typst (mall.typ).
"""
import json
import math
import sys
import tomllib
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "K-05"))
import laster as L05  # noqa: E402

IN = tomllib.loads((HERE / "indata.toml").read_text(encoding="utf-8"))
GEO = json.load(open(HERE / "geometri.json", encoding="utf-8"))
G05 = json.load(open(HERE.parent / "K-05" / "bild" / "geometri.json", encoding="utf-8"))
# ------------------------------------------------------------------ K-01:s resultat
K01 = json.loads((HERE.parent / "K-01" / "resultat.json").read_text(encoding="utf-8"))
KL, TB, UP = IN["klass"], IN["takbalk"], IN["upplag"]
LA = dict(IN["last"], q_p=K01["vind"]["qp_tal"])            # hastighetstrycket som i K-01 och F-01


def _tal(s):
    """Talet i en formaterad text ur K-01:s resultat ("−17,4", "5 632")."""
    return float(s.replace("−", "-").replace(",", ".").replace(" ", "").replace("\u00a0", ""))


def _mot_k01():
    """K-05:s stödreaktioner (laster.K01) mot K-01:s resultat: avvikelserna."""
    fel = []
    for b in K01["balkar"]:
        kod = ("N" if b["typ"] == "nock" else "D") + str(b["nr"])
        k05 = L05.K01[kod]
        stod = {s_["bok"]: s_ for s_ in b["stod"]}
        for bok, (x, Rmax, Rmin) in k05["stod"].items():
            s_ = stod.get(bok)
            if s_ is None or s_["vagg"]:
                fel.append(f"{kod} {bok}: stödet finns inte i K-01")
            elif abs(_tal(s_["x"]) - x) > 0.5 or abs(_tal(s_["Rmax"]) - Rmax) > 0.05 \
                    or abs(_tal(s_["Rmin"]) - Rmin) > 0.05:
                fel.append(f"{kod} {bok}: K-05 x {x}, Rmax {Rmax}, Rmin {Rmin}; K-01 x {s_['x']}, Rmax {s_['Rmax']}, "
                           f"Rmin {s_['Rmin']}")
        saknas = [bok for bok, s_ in stod.items() if not s_["vagg"] and bok not in k05["stod"]]
        if saknas:
            fel.append(f"{kod}: K-01:s stöd {', '.join(saknas)} saknas i K-05")
        vagg = next((s_ for s_ in b["stod"] if s_["vagg"]), None)
        if vagg is not None and abs(_tal(vagg["Rvagg_lyft"]) + k05["vagg_lyft"]) > 0.05:
            fel.append(f"{kod}: väggens lyft K-05 {k05['vagg_lyft']}, K-01 −{vagg['Rvagg_lyft']}")
        if abs(_tal(b["G"]) - L05.K01_LAST[b["typ"]][0]) > 0.005 or abs(_tal(b["S"]) - L05.K01_LAST[b["typ"]][1]) > 0.005:
            fel.append(f"{kod}: balkens last K-05 {L05.K01_LAST[b['typ']]}, K-01 G {b['G']}, S {b['S']}")
    return fel


if fel := _mot_k01():
    raise SystemExit("K-05:s stödreaktioner (K-05/laster.py: K01) är inte K-01:s. För in K-01:s värden och räkna om "
                     "K-05 (./bygg K-05):\n  " + "\n  ".join(fel))
GD, KMOD, KDEF = KL["gamma_d"], KL["k_mod"], KL["k_def"]
ALFA = math.radians(LA["takvinkel"])
CA, SA = math.cos(ALFA), math.sin(ALFA)


def fmt(x, n=1):
    from decimal import Decimal, ROUND_HALF_UP
    q = Decimal(repr(float(x))).quantize(Decimal(1).scaleb(-n), rounding=ROUND_HALF_UP)
    if q == 0:
        q = abs(q)
    s = f"{q:,.{n}f}".replace(",", " ").replace(".", ",")
    return s.replace("-", "−")


def pct(u):
    return f"{100 * u:.0f} %"


# ------------------------------------------------------------------ material och hjälpfunktioner (SS-EN 1995-1-1)
class Mat:
    def __init__(self, namn, kmod=KMOD):
        self.namn = namn
        self.__dict__.update(IN["material"][namn])
        g = self.gamma_M
        self.fmd, self.ft0d, self.fc0d = kmod * self.fmk / g, kmod * self.ft0k / g, kmod * self.fc0k / g
        self.fc90d, self.fvd = kmod * self.fc90k / g, kmod * self.fvk / g

    def kh(self, h):
        """Höjdfaktor för böjning och drag (3.2(3), 3.3(3))."""
        if self.namn.startswith("GL"):
            return min((600 / h) ** 0.1, 1.1) if h < 600 else 1.0
        return min((150 / h) ** 0.2, 1.3) if h < 150 else 1.0

    def kc(self, L, h):
        """Knäckningsfaktor (6.3.2) för knäcklängd L och tvärsnittets mått h i knäckningsriktningen."""
        lam = L * math.sqrt(12) / h
        lr = lam / math.pi * math.sqrt(self.fc0k / self.E005)
        if lr <= 0.3:
            return 1.0, lr
        k = 0.5 * (1 + self.beta_c * (lr - 0.3) + lr ** 2)
        return 1 / (k + math.sqrt(k ** 2 - lr ** 2)), lr

    def fc_alfa(self, a, kc90=1.0):
        """Tryckhållfasthet i vinkeln a [rad] mot fibrerna (6.16)."""
        return self.fc0d / (self.fc0d / (kc90 * self.fc90d) * math.sin(a) ** 2 + math.cos(a) ** 2)


C24, GL = Mat("C24"), Mat("GL30h")


def qd(G, S):
    """Dimensionerande last, största av 6.10a och 6.10b (snö huvudlast)."""
    return max(GD * (1.35 * G + 1.5 * 0.6 * S), GD * (1.2 * G + 1.5 * S))


G_H = LA["g_tak"] / CA                                   # egenvikt per m² horisontell yta
MU = {"dal": LA["mu_dal"], "takfot": LA["mu_takfot"]}


def johansen(t1, t2, d, fh1, fh2, My):
    """Bärförmåga per skjuvplan, enkelskäriga förband trä–trä (8.6), utan repverkan."""
    b = fh2 / fh1
    r = t2 / t1
    return min(fh1 * t1 * d, fh2 * t2 * d,
               fh1 * t1 * d / (1 + b) * (math.sqrt(b + 2 * b ** 2 * (1 + r + r ** 2) + b ** 3 * r ** 2) - b * (1 + r)),
               1.05 * fh1 * t1 * d / (2 + b) * (math.sqrt(2 * b * (1 + b) + 4 * b * (2 + b) * My / (fh1 * d * t1 ** 2)) - b),
               1.05 * fh1 * t2 * d / (1 + 2 * b) * (math.sqrt(2 * b ** 2 * (1 + b) + 4 * b * (1 + 2 * b) * My / (fh1 * d * t2 ** 2)) - b),
               1.15 * math.sqrt(2 * b / (1 + b)) * math.sqrt(2 * My * fh1 * d))


# ------------------------------------------------------------------ takbalkar
b_tb, h_tb, cc = TB["b"], TB["h"], TB["cc"] / 1000
A_tb, W_tb, I_tb = b_tb * h_tb, b_tb * h_tb ** 2 / 6, b_tb * h_tb ** 3 / 12
BALK = {b["namn"]: b for b in GEO["balkar"]}
XB = sorted(b["x"] for b in GEO["balkar"])
E_VAGG = 17.5                                            # ytterväggens centrum innanför plattans kant (K-05)


def spann(r):
    """Takbalkens spann (horisontellt mellan stödens centrumlinjer) och utkragning vid takfot, ur modellen [m]."""
    stod, utkr = [], 0.0
    for xe in (r["x0"], r["x1"]):
        nara = [b["x"] for b in GEO["balkar"] if b["y0"] - 50 <= r["y"] <= b["y1"] + 50 and abs(b["x"] - xe) < 160]
        if nara:
            stod.append(nara[0])
        else:                                            # takfot: ytterväggens centrum, plattans kant vid takbalkens y
            K = G05["kontur"]
            kanter = [p[0] for p, q in zip(K, K[1:] + K[:1]) if abs(p[0] - q[0]) < 1 and min(p[1], q[1]) - 50 <= r["y"] <= max(p[1], q[1]) + 50]
            xk = min(kanter, key=lambda v: abs(v - xe))
            xs = xk + E_VAGG if (r["x0"] + r["x1"]) / 2 > xk else xk - E_VAGG
            stod.append(xs)
            utkr = abs(xe - xs)
    return abs(stod[1] - stod[0]) / 1000, utkr / 1000


def takbalk(L, a, mu, bredd=cc):
    """Fritt upplagd takbalk med spann L och utkragning a vid takfot [m], last per horisontell meter."""
    qG, qS = G_H * bredd, mu * LA["s_k"] * bredd
    q = qd(qG, qS)
    Ra = q * (L + a) * ((L + a) / 2) / L                 # vid takfoten (utkragningens sida)
    Rb = q * (L + a) - Ra                                # vid nock eller dal (hak över upplagsregeln)
    x0 = Rb / q                                          # största fältmoment från nocksidan
    M = max(Rb * x0 - q * x0 ** 2 / 2, q * a ** 2 / 2)
    V = max(Ra - q * a, Rb, q * a)
    # nedböjning längs takbalken, last vinkelrätt balken per meter balk
    Ls = L / CA * 1000
    wG = 5 * qG * CA ** 2 * Ls ** 4 / (384 * C24.E0mean * I_tb)
    wS = 5 * qS * CA ** 2 * Ls ** 4 / (384 * C24.E0mean * I_tb)
    wfin = wG * (1 + KDEF) + wS * (1 + KL["psi2_sno"] * KDEF)
    return dict(qG=qG, qS=qS, q=q, M=M, V=V, Rb=Rb, Ra=Ra, Ls=Ls, wfin=wfin, wkrav=Ls / KL["nedbojning"],
                um=M * 1e6 / W_tb / (C24.kh(h_tb) * C24.fmd), uw=wfin / (Ls / KL["nedbojning"]))


# hak över upplagsregeln: takbalkens överkant i balkens överkant, sätet på regeln ovanför balkens underplåt
z_sate = UP["plat"] + UP["regel_h"]
h_kvar_v = UP["balk_h"] - UP["regel_b"] * math.tan(ALFA) - z_sate   # i lodled vid hakets inre hörn (regelns ytterkant)
h_ef = h_kvar_v * CA                                     # vinkelrätt takbalken
a_n = h_ef / h_tb
x_n = UP["regel_b"] / 2 / CA                             # stödreaktionen till hakets hörn, längs balken
kv = min(1.0, 5.0 / (math.sqrt(h_tb) * (math.sqrt(a_n * (1 - a_n)) + 0.8 * x_n / h_tb * math.sqrt(1 / a_n - a_n ** 2))))
f_sate = C24.fc_alfa(math.pi / 2 - ALFA)                 # sätet: lodrät kraft, fibrerna 30° från vågrätt
d_s = UP["skruv_d"]
fh_regel = 0.082 * C24.rhok * d_s ** -0.3
fh_balk = 0.082 * UP["rho_balk"] * d_s ** -0.3
Fv_skruv = johansen(UP["regel_b"], UP["skruv_L"] - UP["regel_b"], d_s, fh_regel, fh_balk, UP["skruv_My"]) / 1000
Fv_skruv_d = KMOD * Fv_skruv / C24.gamma_M
# vindlyft per takbalksände (zon G), förankring med skruv snett genom takbalken in i balken
w_sug = abs(LA["cpe_cpi_G"]) * LA["q_p"]
Fax_d = KL["k_mod_vind"] * UP["skruv_fax"] * d_s * UP["lyft_skruv_lef"] * (UP["rho_balk"] / 350) ** 0.8 / 1000 / C24.gamma_M

TYPER = []
for T in IN["typ"]:
    rs = [r for r in GEO["takbalkar"] if r["typ"] == T["namn"]]
    sp = [spann(r) for r in rs]
    L = max(s[0] for s in sp)
    a = max(s[1] for s in sp)
    r = takbalk(L, a, MU[T["mu"]])
    tau = 1.5 * r["Rb"] * CA * 1000 / (KL["k_cr"] * b_tb * h_ef)
    r.update(namn=T["namn"], text=T["text"], antal=len(rs), L=L, a=a, mu=MU[T["mu"]],
             uv=tau / (kv * C24.fvd), tau=tau,
             usate=r["Rb"] * 1000 / (b_tb * UP["regel_b"] * f_sate),
             uregel=r["Rb"] * 1000 / ((b_tb + 60) * UP["regel_b"] * C24.fc90d),
             n_skruv=math.ceil(r["Rb"] / Fv_skruv_d),
             lyft=(1.5 * GD * w_sug - 1.0 * G_H) * cc * (L + a) / 2)
    r["u"] = max(r["um"], r["uv"], r["uw"], r["usate"])
    TYPER.append(r)
    print(f"takbalk {T['namn']:4s} {len(rs):3d} st L {L:.3f} a {a:.2f} μ {r['mu']}: M {r['M']:.2f} kNm ({r['um']:.0%}), "
          f"skjuv vid hak {r['uv']:.0%}, w {r['wfin']:.1f}/{r['wkrav']:.1f} ({r['uw']:.0%}), säte {r['usate']:.0%}, R {r['Rb']:.2f} kN, "
          f"skruv {r['n_skruv']} st, lyft {r['lyft']:.2f} kN")
TB_DIM = max(TYPER, key=lambda r: r["u"])
print(f"  hak: h_ef {h_ef:.0f} mm, α {a_n:.2f}, kv {kv:.2f}; skruv Ø{d_s:.0f} F_v,Rd {Fv_skruv_d:.2f} kN; förankring F_ax,Rd {Fax_d:.2f} kN")

# ------------------------------------------------------------------ takfönster
FON = []
for f in GEO["fonster"]:
    sida = [r for r in GEO["takbalkar"] if r["x0"] <= f["x0"] and r["x1"] >= f["x1"] and abs(r["y"] - f["y0"]) < 200]
    typ = next(T for T in TYPER if T["namn"] == sida[0]["typ"])
    bredd_trim = cc / 2 + IN["fonster"]["bredd"] / 2000          # takbalken bredvid fönstret: egen halva fack + halva öppningen
    ut = []
    for n in f["trimmer"]:
        r = takbalk(typ["L"], typ["a"], typ["mu"], bredd_trim / max(n, 1))
        ut.append(max(r["um"], r["uw"]))
    # avväxlingen: kortlingen (c/c 600) ger en punktlast mitt på regeln
    kort = takbalk(1.0, 0.0, typ["mu"])                            # last per meter kortling
    P_k = kort["q"] * 0.75                                         # kortling ≤ 0,75 m mellan avväxling och stöd, halva lasten
    M_v = P_k * IN["fonster"]["bredd"] / 1000 / 4
    u_v = M_v * 1e6 / W_tb / C24.fmd
    # råsponten över öppningens bredd utan kortlingar: nedböjning
    t = IN["fonster"]["rasspont_t"]
    qk = G_H * 0.3 + typ["mu"] * LA["s_k"]                        # råspont och tätskikt ≈ 0,3 kN/m², snö
    w_r = 5 * qk * IN["fonster"]["bredd"] ** 4 / (384 * IN["fonster"]["rasspont_E"] * 1000 * t ** 3 / 12)
    FON.append(dict(nr=f["nr"], y0=f["y0"], y1=f["y1"], typ=typ["namn"], trimmer=f["trimmer"], kortlingar=f["kortlingar"],
                    u_trim=ut, u_avv=u_v, w_rasspont=w_r, w_krav=IN["fonster"]["bredd"] / KL["nedbojning"]))
    print(f"takfönster {f['nr']}: typ {typ['namn']}, takbalkar vid sidorna {f['trimmer']} -> utn {[f'{u:.0%}' for u in ut]}, "
          f"avväxling {u_v:.0%}, kortlingar i modellen {f['kortlingar']}, råspont utan kortlingar w {w_r:.1f} mm (krav {IN['fonster']['bredd'] / KL['nedbojning']:.1f})")

# ------------------------------------------------------------------ takstolar
SP = IN["spikplat"]
fh_sp = 0.082 * C24.rhok * SP["spik_d"] ** -0.3
My_sp = 0.3 * SP["spik_fu"] * SP["spik_d"] ** 2.6
t1_sp = SP["spik_L"] - SP["t"]
Fv_spik = min(0.4 * fh_sp * t1_sp * SP["spik_d"], 1.15 * math.sqrt(2 * My_sp * fh_sp * SP["spik_d"])) / 1000   # tunn plåt (8.9)
Fv_spik_d = KMOD * Fv_spik / SP["gamma_M_forband"]
N_plat = 0.9 * (SP["bredd"] - SP["hal_per_rad"] * SP["hal"]) * SP["t"] * SP["fu"] / SP["gamma_M2"] / 1000
f_topp = C24.fc_alfa(math.pi / 2 - ALFA)                 # toppens säte under balken: lodrät kraft, fibrerna 30°
TK = IN["toppkloss"]
fh_c24 = 0.082 * C24.rhok * TK["skruv_d"] ** -0.3
Fv_kloss_d = KMOD * johansen(TK["t"], TK["skruv_L"] - TK["t"], TK["skruv_d"], fh_c24, fh_c24, TK["skruv_My"]) / 1000 / C24.gamma_M


def stod_k01(balk, bok):
    s = L05.stod(balk, bok)
    return s["Gk"], s["Sk"], L05.K01[balk]["stod"][bok][1]


ST = []
for T, g in zip(IN["takstol"], GEO["takstolar"]):
    stv = [s for s in g["staver"] if s["z0"] > 2000]
    xa_, xb_ = min(s["x0"] for s in stv), max(s["x1"] for s in stv)
    yrad = sorted({r["y"] for r in GEO["takbalkar"] if r["x1"] > xa_ + 300 and r["x0"] < xb_ - 300})
    diag = [s for s in stv if "diag" in s["namn"]]
    band = next(s for s in stv if any(k in s["namn"] for k in ("btm", "bottom", "coord")))
    x_topp = np.mean([s["x1"] if s["az"] > 0 else s["x0"] for s in diag])
    a = max(abs(x_topp - (s["x0"] if s["az"] > 0 else s["x1"])) for s in diag) / 1000      # halva spannet [m]
    hd = min(s["h"] for s in diag)                       # diagonalens höjd
    hb = band["z1"] - band["z0"]                         # dragbandets höjd
    # takremsa till takstolen: gavel = halva facket + utsprång, inne = halva facken på båda sidor
    yy = g["y"]
    under = max((v for v in yrad if v < yy - 30), default=None)
    over = min((v for v in yrad if v > yy + 30), default=None)
    if T["gavel"]:
        nara = over if (over is not None and (under is None or abs(over - yy) < abs(yy - under))) else under
        bredd = abs(nara - yy) / 2000 + LA["utsprang"]
    else:
        bredd = (over - under) / 2000
    Gk, Sk, P = stod_k01(*T["stod"])
    q = qd(G_H * bredd, LA["mu_dal"] * LA["s_k"] * bredd)
    V = P / 2 + q * a                                   # vid varje fot
    H = (P / 2 + q * a / 2) / math.tan(ALFA)             # dragband
    N = H * CA + V * SA                                 # diagonalen vid foten
    M = q * a ** 2 / 8
    Ld = a / CA * 1000
    kc, lr = C24.kc(Ld, hd)
    Ad, Wd_ = 45 * hd, 45 * hd ** 2 / 6
    u_diag = N * 1e3 / (kc * Ad * C24.fc0d) + M * 1e6 / (Wd_ * C24.kh(hd) * C24.fmd)
    u_band = H * 1e3 / (45 * hb) / (C24.kh(hb) * C24.ft0d)
    n_spik = math.ceil(H / 2 / Fv_spik_d)
    u_plat = H / 2 / N_plat
    # toppen under balken (säte = balkens bredd): diagonalernas ändar, fibrerna 30° (6.16), och toppklossarna med
    # vågräta fibrer, tryck vinkelrätt fibrerna med l_ef = bredden + 2 × 30 mm och k_c,90 (6.1.5); klossens del av
    # lasten går genom skruvarna till takstolen
    nk = len(g["klossar"])
    R_diag = UP["balk_b"] * 45 * f_topp / 1e3
    R_kloss = (UP["balk_b"] + 60) * TK["t"] * TK["kc90"] * C24.fc90d / 1e3
    u_topp = P / (R_diag + nk * R_kloss)
    n_kloss = math.ceil(P * R_kloss / (R_diag + nk * R_kloss) / Fv_kloss_d) if nk else 0   # per kloss
    l_fot = V * 1e3 / (45 * 1.5 * C24.fc90d)             # erforderlig upplagslängd på hammarbandet
    ST.append(dict(namn=T["namn"], text=T["text"], stod=f"{T['stod'][0]} {T['stod'][1]}", y=yy, P=P, Gk=Gk, Sk=Sk, a=a, hd=hd, hb=hb,
                   bredd=bredd, q=q, V=V, H=H, N=N, M=M, Ld=Ld, kc=kc, u_diag=u_diag, u_band=u_band, n_spik=n_spik, u_plat=u_plat,
                   nk=nk, u_topp=u_topp, n_kloss=n_kloss,
                   l_fot=l_fot, gavel=T["gavel"],
                   x_topp=x_topp, staver=g["staver"], platar=g["platar"]))
    print(f"takstol {T['namn']:9s} {T['stod'][0]} {T['stod'][1]}: P {P:5.1f} kN, a {a:.2f} m, remsa {bredd:.2f} m, diag 45×{hd:.0f} "
          f"N {N:.1f} kN M {M:.2f} kNm kc {kc:.2f} -> {u_diag:.0%}; band 45×{hb:.0f} H {H:.1f} kN -> {u_band:.0%}; "
          f"spik {n_spik}/plåt och stav, plåt {u_plat:.0%}; topp {nk} kloss -> {u_topp:.0%} ({n_kloss} skruv); fot l {l_fot:.0f} mm")

# ------------------------------------------------------------------ stolpar
PL = {p["namn"]: p for p in L05.punktlaster()}
SG = {s["namn"]: s for s in GEO["stolpar"]}
SI = {s["namn"]: s for s in IN["stolpe"]}
# huvudstolpen: krafterna och strävans fäste ur K-01:s balkmodell (resultat.json)
_hs = next(b["stolpe"]["tal"] for b in K01["balkar"] if b.get("stolpe"))
HS = dict(IN["huvudstolpe"], N_d=_hs["Nd"], M_d=_hs["Md"], F_strava=_hs["FE"], e=_hs["e"])


def stolpe(namn):
    p, g, S = PL[namn], SG[namn], SI.get(namn, {})
    Nd = p["Rd"]
    if "krav" in S:
        k = S["krav"]
        mat = Mat(k["mat"])
        delar = [dict(bx=k["b"], hy=k["h"], z0=k["z0"], z1=k["z1"]) for _ in range(k["delar"])]
        stag, utf, kalla = k["stagad"], k["text"], "krav"
    else:
        mat = Mat(S.get("mat", "C24"))
        delar = [dict(bx=d["x1"] - d["x0"], hy=d["y1"] - d["y0"], z0=d["z0"], z1=d["z1"]) for d in g["delar"]]
        stag, kalla = g["stagad"], "modell"
        utf = beskriv(g["delar"], mat)
    if not delar:
        return dict(namn=namn, saknas=True, Nd=Nd, p=p)
    z0, z1 = min(d["z0"] for d in delar), max(d["z1"] for d in delar)
    L = z1 - z0
    A = sum(d["bx"] * d["hy"] for d in delar)
    e = S.get("e", 0.0)
    if not stag:                                         # fristående: ihopskruvade, verkar som ett tvärsnitt
        X = sum(d["bx"] for d in delar) if len(delar) > 1 else delar[0]["bx"]
        Y = max(d["hy"] for d in delar)
        kcx, _ = mat.kc(L, X)
        kcy, _ = mat.kc(L, Y)
        kc = min(kcx, kcy)
        W = Y * X ** 2 / 6                               # böjning av excentricitet i x-led
        u = Nd * 1e3 / (kc * A * mat.fc0d) + Nd * 1e3 * e / (W * mat.kh(X) * mat.fmd)
        knack = f"fristående, L = {L:.0f}"
    else:
        NRd = 0.0
        for d in delar:
            k = 1.0
            if "x" not in stag:
                k = min(k, mat.kc(L, d["bx"])[0])
            if "y" not in stag:
                k = min(k, mat.kc(L, d["hy"])[0])
            NRd += k * d["bx"] * d["hy"] * mat.fc0d / 1e3
        kc = NRd * 1e3 / (A * mat.fc0d)
        u = Nd / NRd
        if e and stag in ("x", "y"):
            # lasten excentriskt i väggens plan (balken vilar på en del av stolpen): reglarna skruvade ihop till ett
            # tvärsnitt, böjning i väggens plan med knäckning ut ur planet (SS-EN 1995-1-1 6.24, km 0,7)
            X = sum(d["bx"] if stag == "x" else d["hy"] for d in delar)
            Y = max(d["hy"] if stag == "x" else d["bx"] for d in delar)
            u += 0.7 * Nd * 1e3 * e / (Y * X ** 2 / 6 * mat.kh(X) * mat.fmd)
        knack = {"x": "stagad i x-led (vägg)", "y": "stagad i y-led (vägg)", "xy": "stagad åt båda håll"}[stag]
    # tryck vinkelrätt fibrerna i syll (stolpen står på syll) och hammarband (stolpen slutar under hammarbandet)
    # syll och hammarband: belastad längd längs regeln + 30 mm åt båda hållen (6.1.5), regelns bredd = stolpens djup
    l90 = sum(min(d["bx"], d["hy"]) for d in delar)      # reglarna står sida vid sida längs syll och hammarband
    w90 = max(max(d["bx"], d["hy"]) for d in delar)
    A90 = (l90 + 60) * w90
    pa_syll = z0 > 20                                   # stolpen står på syllen
    direkt = any(abs(z1 - b["zu"]) < 15 for b in GEO["balkar"]) or z1 > 3000
    u_syll = Nd * 1e3 / (1.25 * C24.fc90d * A90) if pa_syll else 0.0
    u_ham = Nd * 1e3 / (1.5 * C24.fc90d * A90) if not direkt else 0.0
    return dict(namn=namn, p=p, Nd=Nd, mat=mat.namn, utf=utf, kalla=kalla, L=L, A=A, kc=kc, e=e, u=u, knack=knack,
                u_syll=u_syll, u_ham=u_ham, Wd=p["Wd"], gamla=S.get("gamla", ""), stag=stag, n=len(delar), saknas=False)


def beskriv(delar, mat):
    if not delar:
        return "saknas i modellen"
    from collections import Counter
    c = Counter(f"{min(d['x1'] - d['x0'], d['y1'] - d['y0']):.0f}×{max(d['x1'] - d['x0'], d['y1'] - d['y0']):.0f}" for d in delar)
    return " + ".join(f"{n} st {k}" for k, n in c.items()) + (f" {mat.namn}" if mat.namn != "C24" else " C24")


STOLPAR = []
for namn in PL:
    if namn == "LN1_3":
        continue
    s = stolpe(namn)
    STOLPAR.append(s)
    if s["saknas"]:
        print(f"stolpe {namn}: SAKNAS, N_d {s['Nd']:.1f}")
        continue
    print(f"stolpe {namn:6s} ({s['gamla']:1s}) {s['utf']:34s} [{s['kalla']}] L {s['L']:.0f} {s['knack']:24s} N_d {s['Nd']:5.1f} "
          f"e {s['e']:.0f} -> {s['u']:.0%}  syll {s['u_syll']:.0%} hammarband {s['u_ham']:.0%}  lyft {s['Wd']:.1f}")
# huvudstolpen (LN1_3): K-01:s krafter, knäckning i strävornas plan
gH = SG["LN1_3"]
nH = len(gH["delar"])
bH = sum(d["x1"] - d["x0"] for d in gH["delar"])
hH = max(d["y1"] - d["y0"] for d in gH["delar"])
kcH, lrH = C24.kc(HS["L"], hH)
AH, WH = bH * hH, bH * hH ** 2 / 6
u_H = HS["N_d"] * 1e3 / (kcH * AH * C24.fc0d) + HS["M_d"] * 1e6 / (WH * C24.kh(hH) * C24.fmd)
F_strava_ax = HS["F_strava"] * math.sqrt(2)              # 45°
Ns = F_strava_ax / HS["strava_lager"]
kcS = min(C24.kc(HS["strava_L"], HS["strava_h"])[0], C24.kc(HS["strava_L"], HS["strava_b"])[0])
u_strava = Ns * 1e3 / (kcS * HS["strava_b"] * HS["strava_h"] * C24.fc0d)
u_topregel = HS["F_strava"] * 1e3 / (HS["strava_lager"] * HS["strava_b"] * HS["strava_h"]) / (C24.kh(HS["strava_h"]) * C24.ft0d)
# förankringen vid foten mot lyftet: två vinkelbeslag och en betongbult genom vart
HF = IN["huvudstolpe_fot"]
lyft_H = -PL["LN1_3"]["Wd"]
R1d_H = HF["R1_k"] * KL["k_mod_vind"] / HF["gamma_M"]
R1d_H_spik = HF["R1_k_spik"] * KL["k_mod_vind"] / HF["gamma_M"]
u_fot = lyft_H / R1d_H
N_bult = lyft_H / HF["n_beslag"] * HF["bandning"]
l_topregel = HS["F_strava"] * 1e3 / (HS["strava_lager"] * HS["strava_b"] * 1.5 * C24.fc90d)
n_spik_H = math.ceil(Ns / 2 / Fv_spik_d)
print(f"huvudstolpen: {nH} st 45×{hH:.0f}, b {bH:.0f}, L {HS['L']} kc {kcH:.2f}: N {HS['N_d']:.1f} M {HS['M_d']:.2f} -> {u_H:.0%}; "
      f"strävor {Ns:.1f} kN/lager -> {u_strava:.0%}; topregel drag {u_topregel:.0%}, upplag {l_topregel:.0f} mm; spik {n_spik_H}")

# ------------------------------------------------------------------ brister i modellen (det som inte räcker eller saknas)
# stolpar med krav i indata (modellens utförande räcker inte eller saknas), takfönster utan kortlingar, toppar som inte
# räcker och huvudstolpen utan strävor på båda sidor
huvud = dict(p=PL["LN1_3"], namn="LN1_3", gamla="F")
BRISTER, BRIST_STOLPAR = [], set()
for namn, S in SI.items():
    if "krav" not in S or namn not in SG:
        continue
    k = next(s for s in STOLPAR if s["namn"] == namn)
    SI[namn + "_modell"] = {kk: v for kk, v in S.items() if kk != "krav"}
    SG[namn + "_modell"], PL[namn + "_modell"] = SG[namn], PL[namn]
    mo = stolpe(namn + "_modell")
    BRISTER.append(dict(del_=f"Stolpe {namn}", modell="saknas" if mo["saknas"] else mo["utf"],
                        utn="–" if mo["saknas"] else pct(max(mo["u"], mo["u_syll"], mo["u_ham"])),
                        krav=f"{k['utf']}: {pct(max(k['u'], k['u_syll'], k['u_ham']))}"))
    BRIST_STOLPAR.add(namn)
if any(f["kortlingar"] == 0 for f in FON):
    wmax = max(f["w_rasspont"] for f in FON)
    BRISTER.append(dict(del_="Takfönster", modell="inga kortlingar, råsponten spänner 1,2 m",
                        utn=f"{fmt(wmax, 0)} mm mot {fmt(FON[0]['w_krav'], 0)} mm",
                        krav="kortlingar 45×170 c/c 600 ovanför och nedanför"))
if any(t["u_topp"] > 1 for t in ST):
    BRISTER.append(dict(del_="Takstolarnas toppar", modell="toppklossar som i modellen",
                        utn=", ".join(f"{t['namn'].replace('Stol ', '')} {pct(t['u_topp'])}" for t in ST if t["u_topp"] > 1),
                        krav="fler toppklossar"))
vert = [d for d in GEO["huvudstolpe"] if d["namn"] == "R L3 VertVert"]
strava = [d for d in GEO["huvudstolpe"] if d["namn"] == "R L3 VertDiag"]
y0H, y1H = min(d["y0"] for d in vert), max(d["y1"] for d in vert)
if not (any(d["y1"] <= y0H + 1 for d in strava) and any(d["y0"] >= y1H - 1 for d in strava)):
    BRISTER.append(dict(del_="Huvudstolpen LN1_3", modell="sträva bara på ena sidan", utn="–",
                        krav=f"strävor på båda sidor (dubbeltriangel enligt K-01): {pct(u_H)}"))

# ------------------------------------------------------------------ figurer
import figurer03 as F  # noqa: E402

L2M = next(t for t in ST if t["namn"] == "Stol L2M")
F.BALK = dict(b=UP["balk_b"], h=UP["balk_h"])
F.oversikt(HERE / "fig_oversikt.svg", GEO, G05, ST, STOLPAR, huvud, BRIST_STOLPAR)
F.upplag(HERE / "fig_upplag.svg", UP, TB, h_ef)
F.takstol(HERE / "fig_takstol.svg", L2M, L2M["P"], L2M["H"], L2M["V"])
F.huvudstolpe(HERE / "fig_huvudstolpe.svg", GEO, HS, kcH, u_H)

# ------------------------------------------------------------------ resultat till mallen
grupp = lambda s: ("hörn" if s["namn"].startswith("LA") else "fri" if not s["stag"] else "vägg")
B = next(s for s in STOLPAR if s["namn"] == "LD4_1")


BAR = {"LD2_1": "D2, karm", "LD2_2": "D2, karm + ½ N3 C", "LD2_3": "D2, väggens ände"}
STAG = {"x": "vägg, x-led", "y": "vägg, y-led", "xy": "båda håll", "": "fristående"}


def stolprad(s):
    bar = BAR.get(s["namn"], s["p"]["delar"].replace(" + takstolens takremsa", "").replace("takstolens takremsa", ""))
    return dict(namn=s["namn"], gamla=s["gamla"], bar=bar, utf=s["utf"],
                krav=s["kalla"] == "krav", L=fmt(s["L"], 0), stag=STAG[s["stag"]], Nd=fmt(s["Nd"], 1),
                e=fmt(s["e"], 0), u=pct(s["u"]), syll=pct(s["u_syll"]) if s["u_syll"] else "–",
                ham=pct(s["u_ham"]) if s["u_ham"] else "–", lyft=fmt(-s["Wd"], 1),
                umax=max(s["u"], s["u_syll"], s["u_ham"]))


rader = [stolprad(s) for s in STOLPAR if not s["namn"].startswith("LA")]
LAs = [s for s in STOLPAR if s["namn"].startswith("LA")]
la = dict(namn="LA1–LA10", gamla="A", bar="gavlarnas hörn", utf="3 st 45×95 C24", krav=False,
          L=fmt(max(s["L"] for s in LAs), 0), stag="hörn", Nd=fmt(max(s["Nd"] for s in LAs), 1), e="0",
          u=pct(max(s["u"] for s in LAs)), syll=pct(max(s["u_syll"] for s in LAs)), ham=pct(max(s["u_ham"] for s in LAs)),
          lyft=fmt(max(-s["Wd"] for s in LAs), 1), umax=max(max(s["u"], s["u_syll"], s["u_ham"]) for s in LAs))
rader.append(la)
uS = max(r["umax"] for r in rader)
R = {
    "projekt": IN["projekt"],
    "modell": dict(fil=GEO["kalla"]["fil"], hash=GEO["kalla"]["hash"]),
    "last": dict(g=fmt(LA["g_tak"], 2), gh=fmt(G_H, 2), sk=fmt(LA["s_k"], 1), mud=fmt(LA["mu_dal"], 1), mut=fmt(LA["mu_takfot"], 1),
                 sd=fmt(LA["mu_dal"] * LA["s_k"], 2), st=fmt(LA["mu_takfot"] * LA["s_k"], 2), qp=fmt(LA["q_p"], 2),
                 w=fmt(w_sug, 2), cpe=fmt(LA["cpe_cpi_G"], 1)),
    "mat": {k: {kk: fmt(v, 1) for kk, v in IN["material"][k].items()} for k in IN["material"]},
    "kl": dict(gd=fmt(GD, 2), kmod=fmt(KMOD, 1), kmodw=fmt(KL["k_mod_vind"], 1), kdef=fmt(KDEF, 1), kcr=fmt(KL["k_cr"], 2),
               ned=str(KL["nedbojning"])),
    "tb": dict(antal=str(len(GEO["takbalkar"])), n_typ=str(len(TYPER)), dim=TB_DIM["namn"], dimtext=TB_DIM["text"].lower(),
               h_ef=fmt(h_ef, 0), alfa=fmt(a_n, 2), kv=fmt(kv, 2), x=fmt(x_n, 0), z_sate=fmt(z_sate, 0),
               h_lod=fmt(h_tb / math.cos(ALFA), 0), balk_h=fmt(UP["balk_h"], 0), balk_b=fmt(UP["balk_b"], 0),
               fsate=fmt(f_sate, 2), Fv=fmt(Fv_skruv_d, 2), n_skruv=str(max(t["n_skruv"] for t in TYPER)),
               Fax=fmt(Fax_d, 2), lyft=fmt(max(t["lyft"] for t in TYPER), 2),
               ulyft=pct(max(t["lyft"] for t in TYPER) / Fax_d), ureg=pct(max(t["uregel"] for t in TYPER)),
               umax=pct(TB_DIM["u"])),
    "typer": [dict(namn=t["namn"], text=t["text"], antal=str(t["antal"]), L=fmt(t["L"], 2), a=fmt(t["a"], 2), mu=fmt(t["mu"], 1),
                   q=fmt(t["q"], 2), M=fmt(t["M"], 2), R=fmt(t["Rb"], 2), um=pct(t["um"]), uv=pct(t["uv"]), us=pct(t["usate"]),
                   w=f"{fmt(t['wfin'], 1)} / {fmt(t['wkrav'], 1)}", uw=pct(t["uw"]), dim=t is TB_DIM) for t in TYPER],
    "fon": [dict(nr=str(f["nr"]), y=f"{fmt(f['y0'], 0)}–{fmt(f['y1'], 0)}", typ=f["typ"],
                 trim=" / ".join(str(n) for n in f["trimmer"]), utrim=" / ".join(pct(u) for u in f["u_trim"]),
                 uavv=pct(f["u_avv"]), kort=str(f["kortlingar"]), w=fmt(f["w_rasspont"], 1)) for f in FON],
    "fon_wkrav": fmt(FON[0]["w_krav"], 1),
    "st": [dict(namn=t["namn"].replace("Stol ", ""), text=t["text"], stod=t["stod"], P=fmt(t["P"], 1), a=fmt(t["a"], 2),
                bredd=fmt(t["bredd"], 2), diag=f"45×{t['hd']:.0f}", N=fmt(t["N"], 1), M=fmt(t["M"], 2), ud=pct(t["u_diag"]),
                band=f"45×{t['hb']:.0f}", H=fmt(t["H"], 1), ub=pct(t["u_band"]), spik=str(t["n_spik"]),
                kloss=str(t["nk"]), nk=str(t["n_kloss"]) if t["nk"] else "–", utopp=pct(t["u_topp"]),
                lfot=fmt(t["l_fot"], 0), dim=t is L2M) for t in ST],
    "L2M": dict(P=fmt(L2M["P"], 1), a=fmt(L2M["a"], 2), q=fmt(L2M["q"], 2), V=fmt(L2M["V"], 1), H=fmt(L2M["H"], 1),
                N=fmt(L2M["N"], 1), M=fmt(L2M["M"], 2), kc=fmt(L2M["kc"], 2), Ld=fmt(L2M["Ld"], 0), ud=pct(L2M["u_diag"]),
                ub=pct(L2M["u_band"]), hd=fmt(L2M["hd"], 0), hb=fmt(L2M["hb"], 0), kloss=str(L2M["nk"]),
                ut=pct(L2M["u_topp"]), nk=str(L2M["n_kloss"]), spik=str(L2M["n_spik"]), plat=pct(L2M["u_plat"]),
                lfot=fmt(L2M["l_fot"], 0), bredd=fmt(L2M["bredd"], 2)),
    "sp": dict(Fv=fmt(Fv_spik_d, 2), Fvk=fmt(Fv_spik, 2), Nplat=fmt(N_plat, 1), ftopp=fmt(f_topp, 2), Fvk_kloss=fmt(Fv_kloss_d, 2),
               fc90=fmt(TK["kc90"] * C24.fc90d, 2), kc90=fmt(TK["kc90"], 1)),
    "hs": dict(N=fmt(HS["N_d"], 1), M=fmt(HS["M_d"], 2), L=fmt(HS["L"], 0), n=str(nH), h=fmt(hH, 0), b=fmt(bH, 0), kc=fmt(kcH, 2),
               lr=fmt(lrH, 2), u=pct(u_H), F=fmt(HS["F_strava"], 1), Fax=fmt(F_strava_ax, 1), Ns=fmt(Ns, 1), us=pct(u_strava),
               ut=pct(u_topregel), lt=fmt(l_topregel, 0), spik=str(n_spik_H), e=fmt(HS["e"], 0),
               lyft=fmt(lyft_H, 1), beslag=HF["beslag"], n_beslag=str(HF["n_beslag"]), skruv=HF["skruv"],
               R1k=fmt(HF["R1_k"], 1), R1d=fmt(R1d_H, 1), R1d_spik=fmt(R1d_H_spik, 1), ufot=pct(u_fot),
               bult=f"M{HF['bult_d']:.0f}", bult_djup=fmt(HF["bult_djup"], 0), Nb=fmt(N_bult, 1),
               Nb0=fmt(lyft_H / HF["n_beslag"], 1), band=fmt(HF["bandning"], 1)),
    "stolpar": rader, "uS": pct(uS),
    "B": dict(u=pct(B["u"]), utf=B["utf"], e=fmt(SI["LD4_1"]["e"], 0), N=fmt(B["Nd"], 1),
              M=fmt(B["Nd"] * SI["LD4_1"]["e"] / 1000, 2)),
    "brister": BRISTER,
    "sammanf": [
        dict(del_="Takbalkar 45×170 c/c 600", antal=str(len(GEO["takbalkar"])), dim=f"{TB_DIM['namn']}, hak", u=pct(TB_DIM["u"])),
        dict(del_="Takfönster", antal=str(len(FON)), dim="takbalk bredvid öppningen", u=pct(max(max(f["u_trim"]) for f in FON))),
        dict(del_="Takstolar", antal=str(len(ST)), dim="L2M, diagonal och topp med kloss",
             u=pct(max(max(t["u_diag"], t["u_band"], t["u_plat"], t["u_topp"]) for t in ST))),
        dict(del_="Huvudstolpen LN1_3", antal="1", dim="knäckning och moment", u=pct(u_H)),
        dict(del_="Övriga stolpar", antal=str(len(STOLPAR)), dim=max(rader, key=lambda r: r["umax"])["namn"], u=pct(uS)),
    ],
}
(HERE / "resultat.json").write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8")

import typst  # noqa: E402

pdf = HERE / f"{IN['projekt']['dokument']}_takbalkar_takstolar_stolpar.pdf"
typst.compile(str(HERE / "mall.typ"), output=str(pdf), font_paths=["/usr/share/fonts", str(HERE.parent / ".fonts")])
print(pdf.name)
