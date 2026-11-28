"""Spikplåtarna i takstolarna och huvudstolpen: hydrauliskt inpressade spikplåtar (punched metal plate fasteners)
enligt SS-EN 1995-1-1 8.8, med produktens deklarerade värden (SS-EN 14545) i indata.toml [spikplat].

Varje knutpunkt räknas med stavarnas ytterkonturer i elevation (stav()) och en rektangulär plåt med huvudriktningen
x längs en av stavarna. För plåtens storlek prövas tillverkarens standardmått, och plåten flyttas inom knutpunkten
tills förankringen i varje stav och plåten själv längs fogen klarar sig:

- förankringen (8.8.4, 8.8.5.1): F_A,Ed / A_ef ≤ f_a,α,β,d, med A_ef = kontaktytan minus 5 mm från stavens kanter
  och 6 t från ändarna (här 6 mm runt om), α vinkeln mellan kraften och plåtens x, β mellan kraften och fibrerna;
- plåten längs fogen (8.8.5.2): (F_x / F_x,Rd)² + (F_y / F_y,Rd)² ≤ 1 med fogens längd l under plåten;
- minsta överlapp på varje stav: 40 mm eller en tredjedel av stavens höjd (8.8.1).

Plåten antas centrerad över knutpunktens kraftlinjer, så att momentet i förankringen är litet. Tryck överförs genom
kontakt mellan stavarna (ändarna ligger an), drag och skjuvning genom plåtarna.
"""
from __future__ import annotations

import itertools
import math

import numpy as np
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union


def stav(s: dict) -> Polygon:
    """Stavens ytterkontur i elevation: remsan längs axeln (ax, az) med höjden h, kapad av stavens omfång
    (x0–x1, z0–z1). Remsans läge vinkelrätt axeln väljs så att den kapade remsans omfång blir stavens."""
    ux, uz = s["ax"], s["az"]
    nx, nz = -uz, ux
    bb = box(s["x0"], s["z0"], s["x1"], s["z1"])
    c = np.array([nx * x + nz * z for x, z in bb.exterior.coords[:4]])
    ln = 4 * s["L"] + 1e4
    p_mitt = np.array([(s["x0"] + s["x1"]) / 2, (s["z0"] + s["z1"]) / 2])
    u, n = np.array([ux, uz]), np.array([nx, nz])

    def remsa(c0):
        p0 = p_mitt + (c0 - n @ p_mitt) * n
        return Polygon([p0 - u * ln, p0 + u * ln, p0 + u * ln + n * s["h"], p0 - u * ln + n * s["h"]]).intersection(bb)

    def fel(c0):
        g = remsa(c0)
        return 1e9 if g.is_empty else sum(abs(a - b) for a, b in zip(g.bounds, bb.bounds))

    return remsa(min(np.linspace(c.min() - s["h"], c.max(), 801), key=fel))


def diagonal(d: dict, x: dict) -> Polygon:
    """Diagonalens kontur under ytterbalken x (samma lutning, samma sida): diagonalens överkant är ytterbalkens
    underkant (modellen: byggdelar/takstol.py), och konturen är remsan med diagonalens höjd kapad av dess omfång."""
    tan = abs(x["az"] / x["ax"])
    cos = abs(x["ax"])
    stiger = x["az"] * x["ax"] > 0                       # stiger mot växande x
    xt, zt = (x["x1"], x["z1"]) if stiger else (x["x0"], x["z1"])     # ytterbalkens överkant vid nocken
    dz_x, dz_d = x["h"] / cos, d["h"] / cos

    def ok(xx):
        return zt - dz_x - (xt - xx) * tan if stiger else zt - dz_x - (xx - xt) * tan

    a, b = d["x0"] - 1e4, d["x1"] + 1e4
    remsa = Polygon([(a, ok(a) - dz_d), (b, ok(b) - dz_d), (b, ok(b)), (a, ok(a))])
    return remsa.intersection(box(d["x0"], d["z0"], d["x1"], d["z1"]))


class Plat:
    """Plåtens hållfasthet (karakteristisk enligt deklarationen) och dimensioneringsvärden."""

    def __init__(self, SP: dict, kmod: float):
        self.SP, self.kmod = SP, kmod
        self.gM = SP["gamma_M"]

    def fa(self, alfa: float, beta: float) -> float:
        """f_a,α,β,d [N/mm²] (8.8.4), α och β i grader (0–90)."""
        S = self.SP
        a, b = abs(alfa) % 180, abs(beta) % 180
        a, b = min(a, 180 - a), min(b, 180 - b)
        a0 = S["alfa0"]
        fa0 = S["fa00"] + S["k1"] * a if a <= a0 else S["fa00"] + S["k1"] * a0 + S["k2"] * (a - a0)
        s_ = math.sin(math.radians(max(a, b)))
        if b <= 45:
            fk = max(fa0 - (fa0 - S["fa9090"]) * b / 45, S["fa00"] - (S["fa00"] - S["fa9090"]) * s_)
        else:
            fk = S["fa00"] - (S["fa00"] - S["fa9090"]) * s_
        return self.kmod * fk / self.gM

    def fog(self, Fx: float, Fy: float, l: float, alfa: float) -> float:
        """Plåtens utnyttjande längs fogen (8.8.5.2): Fx, Fy per plåt [N] i plåtens x och y, l fogens längd under
        plåten [mm], α fogens vinkel mot plåtens x [grader]."""
        S, g = self.SP, self.gM
        a = math.radians(alfa)
        fn0 = (S["ft0"] if Fx >= 0 else S["fc0"]) / g
        fn90 = (S["ft90"] if Fy >= 0 else S["fc90"]) / g
        g0 = math.radians(S["gamma0"])
        Fx_Rd = max(abs(fn0 * l * math.sin(a - g0 * math.sin(2 * a))), abs(S["fv0"] / g * l * math.cos(a)))
        k = 1 + S["kv"] * math.sin(2 * a) if Fx * math.sin(a) - Fy * math.cos(a) > 0 else 1.0
        Fy_Rd = max(abs(fn90 * l * math.cos(a)), abs(k * S["fv90"] / g * l * math.sin(a)))
        ux = (Fx / Fx_Rd) ** 2 if Fx else 0.0
        uy = (Fy / Fy_Rd) ** 2 if Fy else 0.0
        return math.sqrt(ux + uy)


def _djup(poly, normal: np.ndarray) -> float:
    """Polygonens utsträckning längs riktningen normal (för minsta överlapp)."""
    if poly.is_empty or poly.area <= 0:
        return 0.0
    from shapely import get_coordinates
    v = get_coordinates(poly) @ normal
    return float(v.max() - v.min())


def knutpunkt(pl: Plat, staver: dict, krafter: list, fog: LineString, fog_alfa: float,
              ankare, storlekar: list, sok: list, ovriga: list = ()) -> dict:
    """Standardplåtarna som klarar knutpunkten: {(w, L): bästa läge och utnyttjanden}.

    staver: {namn: (polygon, axel som enhetsvektor, höjd)}; krafter: lastfall [(Fx, Fy, {stav: (F, α, β)})] per plåt,
    Fx och Fy i plåtens x och y längs fogen; ankare(w, L, d) -> plåtens rektangel för förskjutningen d; sok:
    förskjutningarna som prövas; ovriga: andra stavar i samma plan som plåten får ligga på (räknas inte i förankringen)."""
    unionen = unary_union([p for p, _, _ in staver.values()] + list(ovriga)).buffer(0.5)
    inre = {n: p.buffer(-6.0) for n, (p, _, _) in staver.items()}
    klarar = {}
    for w, L in sorted(storlekar, key=lambda s: (s[0] * s[1], s[0])):
        bast = None
        for d in sok:
            rekt = ankare(w, L, d)
            if not unionen.contains(rekt):
                continue
            ok, ut = True, {}
            for n, (p, ax, h) in staver.items():
                kont = rekt.intersection(p)
                if _djup(kont, np.array([-ax[1], ax[0]])) < max(40.0, h / 3) - 1e-6:
                    ok = False
                    break
                ut[n] = rekt.intersection(inre[n]).area
            if not ok:
                continue
            l = fog.intersection(rekt).length
            u = 0.0
            for Fx, Fy, F in krafter:
                for n, (Fn, a, b) in F.items():
                    if Fn:
                        u = max(u, Fn / (ut[n] * pl.fa(a, b)) if ut[n] > 0 else 9.9)
                if l <= 0:
                    u = max(u, 9.9)
                else:
                    u = max(u, pl.fog(Fx, Fy, l, fog_alfa))
            if u <= 1.0 and (bast is None or u < bast["u"]):
                bast = dict(w=w, L=L, d=d, u=u, A_ef=ut, l=l, rekt=rekt)
        if bast:
            klarar[(w, L)] = bast
    return klarar


def gruppera(behov: dict, storlekar: list, n_max: int) -> dict:
    """Högst n_max storlekar för en grupp knutpunkter: behov = {knutpunkt: [storlekar som klarar den]}. Väljer de
    storlekar som ger minst sammanlagd plåtyta, där varje knutpunkt får den minsta valda storleken som klarar den."""
    alla = sorted({s for v in behov.values() for s in v}, key=lambda s: s[0] * s[1])
    bast = None
    for n in range(1, n_max + 1):
        for val in itertools.combinations(alla, n):
            yta, tilldelning = 0.0, {}
            for k, v in behov.items():
                kand = [s for s in val if s in v]
                if not kand:
                    break
                s = min(kand, key=lambda s: s[0] * s[1])
                tilldelning[k] = s
                yta += s[0] * s[1]
            else:
                if bast is None or yta < bast[0] - 1e-6:
                    bast = (yta, tilldelning)
    return bast[1] if bast else {}
