"""
U-05: kontroller av beräkningsverktygen mot kända lösningar.

1. Endimensionell vägg i skikt: U exakt (ingen diskretisering i genomgångsriktningen behövs).
2. Tvådimensionellt fält med analytisk lösning (Fourierserie): temperaturen ska konvergera med andra ordningen.
3. Regelväggarna: 2D-värdet ska ligga mellan SS-EN ISO 6946:s övre och undre gräns.
4. Platta på mark i 3D mot SS-EN ISO 13370 (9.1, 9.3).
5. Uppvärmd källare i 3D mot SS-EN ISO 13370 (9.3.3).
6. Energibalans: summan av flödena till alla omgivningar är noll i varje lösning.
"""
from __future__ import annotations

import math

import numpy as np

from fv import Modell, kanter


def test_1d():
    lag = [(0.013, 0.25), (0.012, 0.13), (0.095, 0.037), (0.010, 0.25)]
    xs = np.cumsum([0.0] + [t for t, _ in lag])
    ex = kanter(list(xs) + [-0.01, xs[-1] + 0.01], fina=[(-0.01, xs[-1] + 0.01, 0.002)])
    m = Modell([ex, np.linspace(0, 0.1, 3)])
    for i, ((t, l), a) in enumerate(zip(lag, xs[:-1])):
        m.lada(f"m{i}", l, (a, -1), (a + t, 1))
    m.tom("inne", (-1, -1), (0, 1), Rs=0.13)
    m.tom("ute", (xs[-1], -1), (1, 1), Rs=0.04)
    m.bygg()
    L = m.koppling()
    U = L.sum(axis=1)[1, 0] / 0.1
    U0 = 1 / (0.13 + 0.04 + sum(t / l for t, l in lag))
    return dict(namn="Vägg i skikt, 1D", fv=U, ref=U0, avvikelse=U / U0 - 1,
                balans=float(np.abs(L.sum(axis=(0, 1))).max()))


def test_2d():
    """Rektangel W × H, λ = 1, T = 0 i underkant, T = 1 på överkantens del x < a och 0 för x > a, adiabatiska sidor."""
    W, H, a = 1.0, 0.5, 0.4

    def serie(x, y, n=4000):
        k = np.arange(1, n + 1)
        c = 2 * np.sin(k * np.pi * a / W) / (k * np.pi)
        f = np.exp(np.outer(k, y - H) * np.pi / W) * (1 - np.exp(-2 * np.outer(k, y) * np.pi / W)) / \
            (1 - np.exp(-2 * k * np.pi * H / W))[:, None]
        return a / W * y / H + np.sum(c[:, None] * np.cos(np.outer(k, x) * np.pi / W) * f, axis=0)

    pts = [(0.2, 0.25), (0.4, 0.25), (0.7, 0.25), (0.3, 0.45), (0.5, 0.1)]
    ut = []
    for h in (0.02, 0.01, 0.005):
        ex = np.linspace(0, W, int(round(W / h)) + 1)
        ey = np.r_[-h, np.linspace(0, H, int(round(H / h)) + 1), H + h]
        m = Modell([ex, ey])
        m.lada("m", 1.0, (0, 0), (W, H))
        m.tom("T0", (-1, -1), (2, 0))
        m.tom("T1", (0, H), (a, 2))
        m.tom("T0", (a, H), (2, 2))
        m.bygg()
        T = m.los({"T1": 1.0, "T0": 0.0})
        err = []
        for px, py in pts:
            i = np.argmin(abs(m.mitt[0] - px))
            j = np.argmin(abs(m.mitt[1] - py))
            err.append(T[i, j] - serie(np.array([m.mitt[0][i]]), np.array([m.mitt[1][j]]))[0])
        ut.append((h, float(np.abs(err).max())))
    ordning = math.log(ut[0][1] / ut[-1][1]) / math.log(ut[0][0] / ut[-1][0])
    return dict(namn="2D-fält mot analytisk lösning", fel=ut, ordning=ordning)


def iso13370_platta(lam, B, L, R_f, w, Rsi=0.17, Rse=0.04):
    A, P = B * L, 2 * (B + L)
    Bp = A / (0.5 * P)
    dt = w + lam * (Rsi + R_f + Rse)
    if dt < Bp:
        U = 2 * lam / (math.pi * Bp + dt) * math.log(math.pi * Bp / dt + 1)
    else:
        U = lam / (0.457 * Bp + dt)
    return U * A, U, Bp, dt


def iso13370_kallare(lam, B, L, z, R_f, R_w, w, Rsi=0.17, Rsi_w=0.13, Rse=0.04):
    A, P = B * L, 2 * (B + L)
    Bp = A / (0.5 * P)
    dt = w + lam * (Rsi + R_f + Rse)
    if dt + 0.5 * z < Bp:
        Ubf = 2 * lam / (math.pi * Bp + dt + 0.5 * z) * math.log(math.pi * Bp / (dt + 0.5 * z) + 1)
    else:
        Ubf = lam / (0.457 * Bp + dt + 0.5 * z)
    dw = lam * (Rsi_w + R_w + Rse)
    d = dt if dw >= dt else dw
    Ubw = 2 * lam / (math.pi * z) * (1 + 0.5 * d / (d + z)) * math.log(z / dw + 1)
    return A * Ubf + z * P * Ubw, Ubf, Ubw, Bp, dt, dw


def test_platta(h=0.1):
    """Platta på mark 8 × 12 m enligt ISO 13370:s modell: golvets värmemotstånd (cellplast 200 och betong 100) som
    ett ytmotstånd på markens yta, marken λ 2,0; kvartsmodell med symmetri, marken 20 m åt sidorna och nedåt
    (SS-EN ISO 10211)."""
    B, L, lam = 8.0, 12.0, 2.0
    R_f = 0.1 / 1.7 + 0.2 / 0.036
    D = 20.0
    ex = kanter([0, B / 2, B / 2 + D], fina=[(B / 2 - 0.5, B / 2 + 0.5, h)], h_max=2.0, tillvaxt=0.3)
    ey = kanter([0, L / 2, L / 2 + D], fina=[(L / 2 - 0.5, L / 2 + 0.5, h)], h_max=2.0, tillvaxt=0.3)
    ez = kanter([-D, 0.0, 0.05], fina=[(-0.5, 0.05, h / 2)], h_max=2.0, tillvaxt=0.3)
    m = Modell([ex, ey, ez])
    m.lada("mark", lam, (0, 0, -D), (99, 99, 0.0))
    m.tom("ute", (0, 0, 0.0), (99, 99, 1), Rs=0.04)
    m.tom("inne", (0, 0, 0.0), (B / 2, L / 2, 1), Rs=0.17 + R_f)
    m.bygg()
    Lk = m.koppling()
    H = 4 * Lk.sum(axis=1)[m.omgivningar.index("ute"), m.omgivningar.index("inne")]
    Hiso, U, Bp, dt = iso13370_platta(lam, B, L, R_f, 0.0)
    return dict(namn="Platta på mark 8 × 12 m mot ISO 13370", fv=H, ref=Hiso, avvikelse=H / Hiso - 1, N=m.N,
                balans=float(np.abs(Lk.sum(axis=(0, 1))).max()))


def test_kallare(h=0.1):
    """Uppvärmd källare 8 × 12 m (invändigt), helt under mark 2,0 m, enligt ISO 13370:s modell: väggarna ett skikt
    350 mm med väggens värmemotstånd (Kub 350-150), golvets värmemotstånd (betong 100 på cellplast 300) som
    ytmotstånd på marken; väggarnas krön adiabatiskt."""
    B, L, lam, z = 8.0, 12.0, 2.0, 2.0
    w = 0.35
    R_w = 0.1 / 0.036 + 0.15 / 1.7 + 0.1 / 0.038
    R_f = 0.1 / 1.7 + 0.3 / 0.038
    D = 20.0
    xb, yb = B / 2, L / 2
    ex = kanter([0, xb, xb + w, xb + w + D], fina=[(xb - 0.5, xb + w + 0.5, h)], h_max=2.0)
    ey = kanter([0, yb, yb + w, yb + w + D], fina=[(yb - 0.5, yb + w + 0.5, h)], h_max=2.0)
    ez = kanter([-z - D, -z, 0.0, 0.05], fina=[(-z - 0.5, 0.05, h)], h_max=2.0)
    m = Modell([ex, ey, ez])
    m.lada("mark", lam, (0, 0, -99), (99, 99, 0.0))
    m.lada("vagg", w / R_w, (0, 0, -z), (xb + w, yb + w, 0.0))
    m.tom("inne", (0, 0, -z), (xb, yb, 0.0), Rs=0.13)
    k = m._urval((0, 0, -z), (xb, yb, -z + 1e-3))
    golv = np.zeros(m.form, bool)
    i0 = np.searchsorted(m.kant[2], -z + 1e-9) - 1
    golv[:, :, i0] = (m.omg[:, :, i0] >= 0)
    m.Rs[golv] = 0.17 + R_f
    m.tom("ute", (0, 0, 0.0), (99, 99, 1), Rs=0.04)
    m.tom(None, (0, 0, 0.0), (xb + w, yb + w, 1))
    m.bygg()
    Lk = m.koppling()
    H = 4 * Lk.sum(axis=1)[m.omgivningar.index("ute"), m.omgivningar.index("inne")]
    Hiso, Ubf, Ubw, Bp, dt, dw = iso13370_kallare(lam, B, L, z, R_f, R_w, w)
    return dict(namn="Uppvärmd källare 8 × 12 m, 2 m under mark, mot ISO 13370", fv=H, ref=Hiso,
                avvikelse=H / Hiso - 1, N=m.N, Ubf=Ubf, Ubw=Ubw, balans=float(np.abs(Lk.sum(axis=(0, 1))).max()))


def alla():
    return [test_1d(), test_2d(), test_platta(), test_kallare()]


if __name__ == "__main__":
    import time
    for f in (test_1d, test_2d, test_platta, test_kallare):
        t = time.time()
        r = f()
        print(f"{time.time() - t:5.1f} s", {k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()})
