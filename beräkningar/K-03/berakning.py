"""
K-03: takbalkar, takstolar och stolpar enligt EKS 12 och SS-EN 1995-1-1.

    python berakning.py      # -> K-03_takbalkar_takstolar_stolpar.pdf

Läser indata.toml, geometri.json (K-03:s egen geometri, kontrollerad mot modellen med
verktyg/modellanalys/kontroll_k03.py) och stolparnas laster ur K-05 (laster.py, som bygger på K-01).
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
KL, LA, TB, UP = IN["klass"], IN["last"], IN["takbalk"], IN["upplag"]
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
    t_krav = P * 1e3 / (200 * f_topp)                    # erforderlig tjocklek i toppen, säte 200 mm (balkens bredd)
    kloss = t_krav > 45 or TK.get("alla", False)
    n_kloss = math.ceil(P * 2 * TK["t"] / (45 + 2 * TK["t"]) / Fv_kloss_d) if kloss else 0
    l_fot = V * 1e3 / (45 * 1.5 * C24.fc90d)             # erforderlig upplagslängd på hammarbandet
    ST.append(dict(namn=T["namn"], text=T["text"], stod=f"{T['stod'][0]} {T['stod'][1]}", y=yy, P=P, Gk=Gk, Sk=Sk, a=a, hd=hd, hb=hb,
                   bredd=bredd, q=q, V=V, H=H, N=N, M=M, Ld=Ld, kc=kc, u_diag=u_diag, u_band=u_band, n_spik=n_spik, u_plat=u_plat,
                   t_krav=t_krav, u_topp45=t_krav / 45, u_topp135=t_krav / (45 + 2 * TK["t"]), kloss=kloss, n_kloss=n_kloss,
                   l_fot=l_fot, gavel=T["gavel"],
                   x_topp=x_topp, staver=g["staver"], platar=g["platar"]))
    print(f"takstol {T['namn']:9s} {T['stod'][0]} {T['stod'][1]}: P {P:5.1f} kN, a {a:.2f} m, remsa {bredd:.2f} m, diag 45×{hd:.0f} "
          f"N {N:.1f} kN M {M:.2f} kNm kc {kc:.2f} -> {u_diag:.0%}; band 45×{hb:.0f} H {H:.1f} kN -> {u_band:.0%}; "
          f"spik {n_spik}/plåt och stav, plåt {u_plat:.0%}; topp t_krav {t_krav:.0f} mm, kloss {kloss} ({n_kloss} skruv); fot l {l_fot:.0f} mm")

# ------------------------------------------------------------------ stolpar
PL = {p["namn"]: p for p in L05.punktlaster()}
SG = {s["namn"]: s for s in GEO["stolpar"]}
SI = {s["namn"]: s for s in IN["stolpe"]}
HS = IN["huvudstolpe"]


def stolpe(namn):
    p, g, S = PL[namn], SG[namn], SI.get(namn, {})
    Nd = p["Rd"]
    if "krav" in S:
        k = S["krav"]
        mat = Mat(k["mat"])
        delar = [dict(bx=k["b"], hy=k["h"], z0=k["z0"], z1=k["z1"]) for _ in range(k["delar"])]
        stag, utf, kalla = k["stagad"], k["text"], "krav"
    else:
        mat = GL if any("115" in d["namn"] for d in g["delar"]) else C24
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
# stolpe B som i modellen (115×115) för jämförelse
gB = SG["LD4_1"]
SI_B = dict(SI["LD4_1"])
SI_B.pop("krav")
SI["LD4_1_modell"] = SI_B
SG["LD4_1_modell"] = gB
PL["LD4_1_modell"] = PL["LD4_1"]
B_mod = stolpe("LD4_1_modell")
print(f"stolpe B som i modellen: {B_mod['utf']} -> {B_mod['u']:.0%}")

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
l_topregel = HS["F_strava"] * 1e3 / (HS["strava_lager"] * HS["strava_b"] * 1.5 * C24.fc90d)
n_spik_H = math.ceil(Ns / 2 / Fv_spik_d)
print(f"huvudstolpen: {nH} st 45×{hH:.0f}, b {bH:.0f}, L {HS['L']} kc {kcH:.2f}: N {HS['N_d']} M {HS['M_d']} -> {u_H:.0%}; "
      f"strävor {Ns:.1f} kN/lager -> {u_strava:.0%}; topregel drag {u_topregel:.0%}, upplag {l_topregel:.0f} mm; spik {n_spik_H}")

# ------------------------------------------------------------------ brister i modellen (det som inte räcker eller saknas)
huvud = dict(p=PL["LN1_3"], namn="LN1_3", gamla="F")
BRISTER = []
B_krav = next(s for s in STOLPAR if s["namn"] == "LD4_1")
BRISTER.append(dict(del_="Stolpe B (LD4_1)", modell=f"{B_mod['utf']}, {SI['LD4_1']['e']:.0f} mm excentrisk", utn=pct(B_mod["u"]),
                    krav=f"{B_krav['utf']}: {pct(B_krav['u'])}"))
k42 = next(s for s in STOLPAR if s["namn"] == "LD4_2")
SI_42 = dict(SI["LD4_2"]); SI_42.pop("krav")
SI["LD4_2_modell"], SG["LD4_2_modell"], PL["LD4_2_modell"] = SI_42, SG["LD4_2"], PL["LD4_2"]
m42 = stolpe("LD4_2_modell")
BRISTER.append(dict(del_="Stolpe LD4_2", modell=f"{m42['utf']} på syll", utn=pct(max(m42["u_syll"], m42["u_ham"])) + " (syll)",
                    krav=f"{k42['utf']}: {pct(max(k42['u'], k42['u_syll'], k42['u_ham']))}"))
k11 = next(s for s in STOLPAR if s["namn"] == "LN1_1")
BRISTER.append(dict(del_="Stolpe LN1_1 (nockbalk 1, stöd B)", modell="saknas", utn="–",
                    krav=f"{k11['utf'].replace(', ny', '')} i väggen vid y ≈ 2 795: {pct(k11['u'])}"))
kl = [t for t in ST if t["t_krav"] > 45]
BRISTER.append(dict(del_="Takstolarnas toppar", modell="45 mm under balken",
                    utn=", ".join(f"{t['namn'].replace('Stol ', '')} {pct(t['u_topp45'])}" for t in kl),
                    krav=f"toppklossar 45 mm på båda sidor, alla takstolar: högst {pct(max(t['u_topp135'] for t in ST))}"))
wmax = max(f["w_rasspont"] for f in FON)
BRISTER.append(dict(del_="Takfönster TF1–TF3", modell="inga kortlingar, råsponten spänner 1,2 m",
                    utn=f"{fmt(wmax, 0)} mm mot {fmt(FON[0]['w_krav'], 0)} mm", krav="kortlingar 45×170 c/c 600 ovanför och nedanför"))
BRISTER.append(dict(del_="Takbalkarnas upplag", modell="regel inuti HEA 200 (äldre balk)", utn="–",
                    krav=f"upplagsregel 45×45 och hak: högst {pct(max(t['uv'] for t in TYPER))}"))
BRISTER.append(dict(del_="Huvudstolpen LN1_3", modell="sträva bara på ena sidan", utn="–",
                    krav=f"strävor på båda sidor (dubbeltriangel enligt K-01): {pct(u_H)}"))
BRIST_STOLPAR = {"LD4_1", "LD4_2", "LN1_1"}

# ------------------------------------------------------------------ figurer
import figurer03 as F  # noqa: E402

L2M = next(t for t in ST if t["namn"] == "Stol L2M")
F.oversikt(HERE / "fig_oversikt.svg", GEO, G05, ST, STOLPAR, huvud, BRIST_STOLPAR)
F.upplag(HERE / "fig_upplag.svg", UP, TB, h_ef)
F.takstol(HERE / "fig_takstol.svg", L2M, L2M["P"], L2M["H"], L2M["V"])
F.huvudstolpe(HERE / "fig_huvudstolpe.svg", GEO, HS, kcH, u_H)

# ------------------------------------------------------------------ resultat till mallen
grupp = lambda s: ("hörn" if s["namn"].startswith("LA") else "fri" if not s["stag"] else "vägg")


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
                tkrav=fmt(t["t_krav"], 0), kloss="ja" if t["kloss"] else "–", nk=str(t["n_kloss"]) if t["kloss"] else "–",
                utopp=pct(t["u_topp135"] if t["kloss"] else t["u_topp45"]),
                lfot=fmt(t["l_fot"], 0), dim=t is L2M) for t in ST],
    "L2M": dict(P=fmt(L2M["P"], 1), a=fmt(L2M["a"], 2), q=fmt(L2M["q"], 2), V=fmt(L2M["V"], 1), H=fmt(L2M["H"], 1),
                N=fmt(L2M["N"], 1), M=fmt(L2M["M"], 2), kc=fmt(L2M["kc"], 2), Ld=fmt(L2M["Ld"], 0), ud=pct(L2M["u_diag"]),
                ub=pct(L2M["u_band"]), hd=fmt(L2M["hd"], 0), hb=fmt(L2M["hb"], 0), tkrav=fmt(L2M["t_krav"], 0),
                ut=pct(L2M["u_topp135"]), nk=str(L2M["n_kloss"]), spik=str(L2M["n_spik"]), plat=pct(L2M["u_plat"]),
                lfot=fmt(L2M["l_fot"], 0), bredd=fmt(L2M["bredd"], 2)),
    "sp": dict(Fv=fmt(Fv_spik_d, 2), Fvk=fmt(Fv_spik, 2), Nplat=fmt(N_plat, 1), ftopp=fmt(f_topp, 2), Fvk_kloss=fmt(Fv_kloss_d, 2)),
    "hs": dict(N=fmt(HS["N_d"], 1), M=fmt(HS["M_d"], 2), L=fmt(HS["L"], 0), n=str(nH), h=fmt(hH, 0), b=fmt(bH, 0), kc=fmt(kcH, 2),
               lr=fmt(lrH, 2), u=pct(u_H), F=fmt(HS["F_strava"], 1), Fax=fmt(F_strava_ax, 1), Ns=fmt(Ns, 1), us=pct(u_strava),
               ut=pct(u_topregel), lt=fmt(l_topregel, 0), spik=str(n_spik_H), e=fmt(HS["e"], 0),
               lyft=fmt(-PL["LN1_3"]["Wd"], 1)),
    "stolpar": rader, "uS": pct(uS),
    "B": dict(mod=pct(B_mod["u"]), krav=pct(B_krav["u"]), e=fmt(SI["LD4_1"]["e"], 0), N=fmt(B_krav["Nd"], 1),
              M=fmt(B_krav["Nd"] * SI["LD4_1"]["e"] / 1000, 2)),
    "brister": BRISTER,
    "sammanf": [
        dict(del_="Takbalkar 45×170 c/c 600", antal=str(len(GEO["takbalkar"])), dim=f"{TB_DIM['namn']}, hak", u=pct(TB_DIM["u"])),
        dict(del_="Takfönster", antal=str(len(FON)), dim="takbalk bredvid öppningen", u=pct(max(max(f["u_trim"]) for f in FON))),
        dict(del_="Takstolar", antal=str(len(ST)), dim="L2M, diagonal och topp med klossar",
             u=pct(max(max(t["u_diag"], t["u_band"], t["u_plat"], t["u_topp135"] if t["kloss"] else t["u_topp45"]) for t in ST))),
        dict(del_="Huvudstolpen LN1_3", antal="1", dim="knäckning och moment", u=pct(u_H)),
        dict(del_="Övriga stolpar", antal=str(len(STOLPAR)), dim=max(rader, key=lambda r: r["umax"])["namn"], u=pct(uS)),
    ],
}
(HERE / "resultat.json").write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8")

import typst  # noqa: E402

pdf = HERE / f"{IN['projekt']['dokument']}_takbalkar_takstolar_stolpar.pdf"
typst.compile(str(HERE / "mall.typ"), output=str(pdf), font_paths=["/usr/share/fonts", str(HERE.parent / ".fonts")])
print(pdf.name)
