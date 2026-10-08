"""
Kontroller enligt SS-EN 1992-1-1 med svenska val enligt EKS 12 (BFS 2011:10 t.o.m. BFS 2022:4).

Enheter: N, mm, MPa. Moment per längdenhet i Nmm/mm (= kNm/m).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np


# ------------------------------------------------------------------ material
@dataclass
class Betong:
    fck: float = 30.0
    gamma_c: float = 1.5
    alfa_cc: float = 1.0          # EKS 12, 3.1.6(1)P
    RH: float = 50.0              # inomhus, uppvärmt
    t0: float = 28.0              # belastningsålder [dygn]
    cement: str = "N"

    @property
    def fcm(self):
        return self.fck + 8

    @property
    def fctm(self):               # tabell 3.1
        return 0.30 * self.fck ** (2 / 3) if self.fck <= 50 else 2.12 * math.log(1 + self.fcm / 10)

    @property
    def Ecm(self):
        return 22000 * (self.fcm / 10) ** 0.3

    @property
    def fcd(self):
        return self.alfa_cc * self.fck / self.gamma_c

    def kryptal(self, h0):
        """φ(∞, t0) enligt bilaga B.1 (RH, h0 [mm], t0)."""
        fcm = self.fcm
        a1, a2, a3 = (35 / fcm) ** 0.7, (35 / fcm) ** 0.2, (35 / fcm) ** 0.5
        if fcm <= 35:
            phiRH = 1 + (1 - self.RH / 100) / (0.1 * h0 ** (1 / 3))
        else:
            phiRH = (1 + (1 - self.RH / 100) / (0.1 * h0 ** (1 / 3)) * a1) * a2
        alfa = {"S": -1, "N": 0, "R": 1}[self.cement]
        t0 = max(self.t0 * (9 / (2 + self.t0 ** 1.2) + 1) ** alfa, 0.5)
        return phiRH * 16.8 / math.sqrt(fcm) / (0.1 + t0 ** 0.20)

    def krympning(self, h0):
        """εcs(∞) = εcd,∞ + εca,∞ enligt 3.1.4 och bilaga B.2."""
        ads1, ads2 = {"S": (3, 0.13), "N": (4, 0.12), "R": (6, 0.11)}[self.cement]
        bRH = 1.55 * (1 - (self.RH / 100) ** 3)
        ecd0 = 0.85 * ((220 + 110 * ads1) * math.exp(-ads2 * self.fcm / 10)) * 1e-6 * bRH
        kh = float(np.interp(h0, [100, 200, 300, 500], [1.0, 0.85, 0.75, 0.70]))
        eca = 2.5 * (self.fck - 10) * 1e-6
        return kh * ecd0 + eca


@dataclass
class Stal:
    fyk: float = 500.0
    gamma_s: float = 1.15
    Es: float = 200000.0

    @property
    def fyd(self):
        return self.fyk / self.gamma_s


@dataclass
class Lager:
    """Ett armeringslager i en riktning. y = avstånd från plattans ovansida till stångens centrum [mm]."""
    dia: float
    cc: float
    y: float

    @property
    def As(self):                 # mm²/mm
        return math.pi * self.dia ** 2 / 4 / self.cc


@dataclass
class Armering:
    """Under- och överkantsarmering i x- och y-riktning (mm²/mm och läge)."""
    h: float
    ux: Lager
    uy: Lager
    ox: Lager
    oy: Lager

    def lager(self, riktning, sida):
        return {("x", "u"): self.ux, ("y", "u"): self.uy, ("x", "o"): self.ox, ("y", "o"): self.oy}[(riktning, sida)]


# ------------------------------------------------------------------ böjning, 6.1
def MRd(As, d, b: Betong, s: Stal):
    """Momentkapacitet per mm bredd, rektangulärt spänningsblock (λ = 0,8, η = 1)."""
    x = As * s.fyd / (0.8 * b.fcd)
    return As * s.fyd * (d - 0.4 * x), x / d


def As_min(d, h, b: Betong, s: Stal):
    """9.3.1.1 / 9.2.1.1(1): As,min per mm bredd."""
    return max(0.26 * b.fctm / s.fyk * d, 0.0013 * d)


# ------------------------------------------------------------------ tvärkraft, 6.2.2
def k_size(d):
    return min(1 + math.sqrt(200 / d), 2.0)


def vmin(d, b: Betong):
    return 0.035 * k_size(d) ** 1.5 * math.sqrt(b.fck)


def vRdc(rho, d, b: Betong):
    """Tvärkraftskapacitet [MPa] utan tvärkraftsarmering (6.2), CRd,c = 0,18/γc, σcp = 0."""
    rho = min(rho, 0.02)
    return max(0.18 / b.gamma_c * k_size(d) * (100 * rho * b.fck) ** (1 / 3), vmin(d, b))


# ------------------------------------------------------------------ genomstansning, 6.4
def u1_rekt(c1, c2, d):
    return 2 * (c1 + c2) + 4 * math.pi * d


def genomstansning(VEd, c1, c2, d, rho, b: Betong, beta=1.15, u1=None, u0=None):
    """Kontroll enligt 6.4.3–6.4.5 för ett rektangulärt belastat område c1×c2 (pelarhuvud/plåt).
    Returnerar dict med utnyttjanden."""
    u1 = u1_rekt(c1, c2, d) if u1 is None else u1
    u0 = 2 * (c1 + c2) if u0 is None else u0
    vEd = beta * VEd / (u1 * d)
    vrdc = vRdc(rho, d, b)
    nu = 0.6 * (1 - b.fck / 250)
    vEd0 = beta * VEd / (u0 * d)
    vRdmax = 0.4 * nu * b.fcd                   # 6.4.5(3), rekommenderat värde (A1:2014)
    return dict(VEd=VEd, beta=beta, d=d, rho=rho, u1=u1, u0=u0, vEd=vEd, vRdc=vrdc, vmin=vmin(d, b),
                k=k_size(d), utn=vEd / vrdc, vEd0=vEd0, vRdmax=vRdmax, utn0=vEd0 / vRdmax,
                VRd=vrdc * u1 * d / beta)


def minsta_huvud(VEd, d, rho, b: Betong, beta=1.15):
    """Minsta kvadratiska belastade yta c×c [mm] så att genomstansning klaras utan skjuvarmering."""
    vr = vRdc(rho, d, b)
    u1 = beta * VEd / (vr * d)
    return max((u1 - 4 * math.pi * d) / 4, 0.0)


# ------------------------------------------------------------------ tvärsnitt för nedböjning och sprickor
_CACHE = {}


def tvarsnitt(h, lager, alfa_e, drag="u"):
    key = (h, tuple(lager), round(alfa_e, 9), drag)
    if key not in _CACHE:
        _CACHE[key] = _tvarsnitt(h, lager, alfa_e, drag)
    return _CACHE[key]


def _tvarsnitt(h, lager, alfa_e, drag="u"):
    """Okrossat (I) och sprucket (II) tvärsnitt per mm bredd.
    lager: [(As, y)] med y från ovansidan. drag='u' ger dragen underkant, 'o' dragen överkant
    (då speglas koordinaterna). Returnerar dict med I1, S1, yc1, Mcr-faktor och I2, S2, x.
    S är armeringens statiska moment kring tyngdpunkten, positivt för armering mot dragna sidan."""
    if drag == "o":
        lager = [(As, h - y) for As, y in lager]
    # stadium I, transformerat (αe − 1 för stål i betong)
    A = h + sum((alfa_e - 1) * As for As, y in lager)
    yc = (h * h / 2 + sum((alfa_e - 1) * As * y for As, y in lager)) / A
    I1 = h ** 3 / 12 + h * (h / 2 - yc) ** 2 + sum((alfa_e - 1) * As * (y - yc) ** 2 for As, y in lager)
    S1 = sum(alfa_e * As * (y - yc) for As, y in lager) / alfa_e     # geometriskt, αe läggs på i krökningen
    # stadium II: tryckzon 0..x
    def f(x):
        return x * x / 2 - sum((alfa_e if y > x else alfa_e - 1) * As * (y - x) for As, y in lager)
    lo, hi = 1e-6, h
    for _ in range(80):
        mid = (lo + hi) / 2
        if f(mid) > 0:
            hi = mid
        else:
            lo = mid
    x = (lo + hi) / 2
    I2 = x ** 3 / 3 + sum((alfa_e if y > x else alfa_e - 1) * As * (y - x) ** 2 for As, y in lager)
    S2 = sum(As * (y - x) for As, y in lager if y > x) + sum((alfa_e - 1) / alfa_e * As * (y - x) for As, y in lager if y <= x)
    return dict(I1=I1, S1=S1, yc=yc, W1=I1 / (h - yc), I2=I2, S2=S2, x=x)


def styvhet_effektiv(M, h, lager, b: Betong, s: Stal, phi, ecs, beta=0.5, fct=None):
    """Krökning enligt 7.4.3 (7.18) för moment M [Nmm/mm] i en riktning.
    Returnerar (EI_eff [Nmm²/mm], κcs i M:s riktning (positiv = samma som M), ζ)."""
    Eeff = b.Ecm / (1 + phi)
    ae = s.Es / Eeff
    drag = "u" if M >= 0 else "o"
    t = tvarsnitt(h, lager, ae, drag)
    fct = b.fctm if fct is None else fct
    Mcr = fct * t["W1"]
    Ma = abs(M)
    zeta = 1 - beta * (Mcr / Ma) ** 2 if Ma > Mcr else 0.0
    EI = Eeff / (zeta / t["I2"] + (1 - zeta) / t["I1"])
    kcs = ecs * ae * (zeta * t["S2"] / t["I2"] + (1 - zeta) * t["S1"] / t["I1"])
    if drag == "o":
        kcs = -kcs
    return EI, kcs, zeta


# ------------------------------------------------------------------ sprickbredd, 7.3.4
def sprickbredd(M, h, As, d, c, dia, b: Betong, s: Stal, phi=0.0, kt=0.4, lager=None):
    """wk enligt 7.3.4 för moment M [Nmm/mm] med dragarmering As [mm²/mm] på djupet d och täckskikt c.
    Spänning ur sprucket tvärsnitt med αe = Es/Ecm (korttid) eller Es/Ec,eff (phi > 0)."""
    ae = s.Es / (b.Ecm / (1 + phi))
    lag = lager if lager is not None else [(As, d)]
    t = tvarsnitt(h, lag, ae, "u")
    x = t["x"]
    sigma_s = abs(M) * ae * (d - x) / t["I2"]
    hceff = min(2.5 * (h - d), (h - x) / 3, h / 2)
    rho_eff = As / hceff
    ae_s = s.Es / b.Ecm
    de = (sigma_s - kt * b.fctm / rho_eff * (1 + ae_s * rho_eff)) / s.Es
    de = max(de, 0.6 * sigma_s / s.Es)
    sr = 3.4 * c + 0.425 * 0.8 * 0.5 * dia / rho_eff
    return dict(wk=sr * de, sigma_s=sigma_s, sr=sr, rho_eff=rho_eff, x=x)


# ------------------------------------------------------------------ stålpelare, SS-EN 1993-1-1
def vkr(b, t, r_o=None):
    """Kvadratisk konstruktionsrörprofil b×b×t med ytterradie r_o (standard 2t kallformad)."""
    r_o = 2 * t if r_o is None else r_o
    r_i = max(r_o - t, 0)
    A = b * b - (b - 2 * t) ** 2 - (4 - math.pi) * (r_o ** 2 - r_i ** 2)

    def Isq(a, r):            # kvadrat a×a med hörnradie r
        I = a ** 4 / 12
        # dra ifrån hörn (kvadrat r×r minus kvartscirkel) med Steiners sats
        Ac = (4 - math.pi) * r * r / 4
        yc = a / 2 - r + (10 - 3 * math.pi) / (12 - 3 * math.pi) * r   # hörnbitens tyngdpunkt
        return I - 4 * Ac * yc ** 2

    I = Isq(b, r_o) - Isq(b - 2 * t, r_i)
    return dict(A=A, I=I, i=math.sqrt(I / A))


def pelare_knackning(NEd, b, t, L, fy=355.0, kurva="c", gamma_M1=1.0, E=210000.0):
    """Böjknäckning 6.3.1, ledad i båda ändar (Lcr = L). Kallformad VKR: kurva c."""
    p = vkr(b, t)
    alfa = {"a": 0.21, "b": 0.34, "c": 0.49}[kurva]
    eps = math.sqrt(235 / fy)
    klass = "1–3" if (b - 3 * t) / t <= 42 * eps else "4"
    Ncr = math.pi ** 2 * E * p["I"] / L ** 2
    lam = math.sqrt(p["A"] * fy / Ncr)
    Phi = 0.5 * (1 + alfa * (lam - 0.2) + lam ** 2)
    chi = min(1.0, 1 / (Phi + math.sqrt(Phi ** 2 - lam ** 2)))
    NbRd = chi * p["A"] * fy / gamma_M1
    return dict(A=p["A"], I=p["I"], i=p["i"], lam=lam, chi=chi, NbRd=NbRd, utn=NEd / NbRd, klass=klass)


def huvudplat(VEd, a, b_ror, fy=355.0, gamma_M0=1.0):
    """Erforderlig tjocklek för kvadratisk huvudplåt a×a på rör b×b: plåtens utstick som konsol med
    jämnt tryck VEd/a² (plastiskt moment), på säker sida."""
    p = VEd / (a * a)
    e = (a - b_ror) / 2
    m = p * e * e / 2
    return math.sqrt(4 * m * gamma_M0 / fy)
