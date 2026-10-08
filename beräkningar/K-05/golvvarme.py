"""
Golvvärme i mellanbjälklaget: stationär 2D-värmeledning i ett tvärsnitt genom plattan, en halv slangdelning
med symmetri på båda sidor. Jämför slangar högt, i mitten och lågt i plattan.

Skikt uppifrån: trägolv (limmat), betong 150 mm. Slang PEX med vattentemperatur på insidan.
Ovansida: rumsluft, värmeövergång uppåt. Undersida: källarluft, värmeövergång nedåt (värmeflöde nedåt).
"""
import math

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
import triangle as tr

# ------------------------------------------------------------------ indata
H_BET = 150.0        # mm
T_TRA = 20.0         # trägolv [mm]
LAM = dict(betong=1.7, tra=0.13, pex=0.35)      # W/mK (SS-EN ISO 10456: betong 1,65–2,0; trä 0,13; PE-X 0,35)
H_UPP = 10.8         # W/m²K, golvyta mot rum (SS-EN 1264-2 / ISO 11855, total konvektion + strålning)
H_NED = 1 / 0.17     # W/m²K, takyta i källaren, värmeflöde nedåt (SS-EN ISO 6946 Rsi = 0,17)
D_YTTER, T_VAGG = 17.0, 2.0                      # PEX 17×2 [mm]
DELNING = 200.0      # c/c [mm]
T_RUM = 20.0
Q_MAL = 40.0         # W/m² golvyta uppåt (dimensionerande effekt i ett välisolerat hus)


def modell(djup, delning=DELNING, h=3.0):
    """djup = slangens centrum under betongens ovansida [mm]. Returnerar nät och materialindex."""
    W = delning / 2
    y_top = H_BET + T_TRA
    yc = H_BET - djup
    r1, r0 = D_YTTER / 2, D_YTTER / 2 - T_VAGG
    V = [(0, 0), (W, 0), (W, H_BET), (W, y_top), (0, y_top), (0, H_BET)]
    S = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 2)]
    # halva cirklar (slangen ligger på symmetrilinjen x = 0)
    def halvcirkel(r, n):
        i0 = len(V)
        for k in range(n + 1):
            a = -math.pi / 2 + math.pi * k / n
            V.append((r * math.cos(a), yc + r * math.sin(a)))
        for k in range(n):
            S.append((i0 + k, i0 + k + 1))
        return i0, i0 + n
    a1, b1 = halvcirkel(r1, 24)
    a0, b0 = halvcirkel(r0, 20)
    S.append((a0, a1)); S.append((b0, b1))
    S.append((0, a1)); S.append((b1, 5))           # symmetrilinjen x = 0 utanför slangen
    geo = dict(vertices=np.array(V, float), segments=np.array(S),
               holes=np.array([[0.5, yc]]))      # vattnet (innanför r0) ingår inte
    m = tr.triangulate(geo, f"pq30a{0.433 * h * h:.2f}")
    xy, t = m["vertices"], m["triangles"]
    cen = xy[t].mean(1)
    rr = np.hypot(cen[:, 0], cen[:, 1] - yc)
    mat = np.where(cen[:, 1] > H_BET, LAM["tra"], np.where(rr < r1, LAM["pex"], LAM["betong"]))
    return xy, t, mat, yc, r0, y_top


def los(djup, T_vatten, T_kallare, delning=DELNING, h=3.0):
    xy, t, lam, yc, r0, y_top = modell(djup, delning, h)
    n = len(xy)
    x, y = xy[t, 0], xy[t, 1]
    b = np.stack([y[:, 1] - y[:, 2], y[:, 2] - y[:, 0], y[:, 0] - y[:, 1]], 1)
    c = np.stack([x[:, 2] - x[:, 1], x[:, 0] - x[:, 2], x[:, 1] - x[:, 0]], 1)
    A = 0.5 * np.abs((b * x).sum(1))
    # mm -> m: konduktivitet [W/mK] ger ledning per m djup; integranden ∇N·∇N A är dimensionslös i 2D
    Ke = lam[:, None, None] * (b[:, :, None] * b[:, None, :] + c[:, :, None] * c[:, None, :]) / (4 * A[:, None, None])
    rows = np.repeat(t, 3, axis=1).ravel(); cols = np.tile(t, (1, 3)).ravel()
    K = sp.coo_matrix((Ke.ravel(), (rows, cols)), shape=(n, n)).tocsr()
    f = np.zeros(n)
    # randkanter
    kanter = {}
    for tt in t:
        for i, j in ((0, 1), (1, 2), (2, 0)):
            e = tuple(sorted((tt[i], tt[j])))
            kanter[e] = kanter.get(e, 0) + 1
    rand = [e for e, k in kanter.items() if k == 1]
    Kr = sp.lil_matrix((n, n))
    for i, j in rand:
        (xi, yi), (xj, yj) = xy[i], xy[j]
        L = math.hypot(xj - xi, yj - yi) / 1000      # m
        for yy, hh, Tinf in ((y_top, H_UPP, T_RUM), (0.0, H_NED, T_kallare)):
            if abs(yi - yy) < 1e-6 and abs(yj - yy) < 1e-6:
                Kr[i, i] += hh * L / 3; Kr[j, j] += hh * L / 3; Kr[i, j] += hh * L / 6; Kr[j, i] += hh * L / 6
                f[i] += hh * Tinf * L / 2; f[j] += hh * Tinf * L / 2
    K = (K + Kr.tocsr()).tocsr()
    # vattnet: föreskriven temperatur på slangens insida
    fast = np.nonzero(np.abs(np.hypot(xy[:, 0], xy[:, 1] - yc) - r0) < 1e-6)[0]
    T = np.zeros(n); T[fast] = T_vatten
    fri = np.setdiff1d(np.arange(n), fast)
    T[fri] = spla.spsolve(K[fri][:, fri].tocsc(), f[fri] - K[fri][:, fast] @ T[fast])
    # flöden genom ovan- och undersidan [W per m golvyta]
    W = delning / 2 / 1000

    def flode(yy, hh, Tinf):
        q = 0.0; Ts = []
        for i, j in rand:
            if abs(xy[i, 1] - yy) < 1e-6 and abs(xy[j, 1] - yy) < 1e-6:
                L = math.hypot(*(xy[j] - xy[i])) / 1000
                q += hh * ((T[i] + T[j]) / 2 - Tinf) * L
                Ts += [T[i], T[j]]
        return q / W, min(Ts), max(Ts)
    q_upp, Tu_min, Tu_max = flode(y_top, H_UPP, T_RUM)
    q_ned, Tn_min, Tn_max = flode(0.0, H_NED, T_kallare)
    return dict(q_upp=q_upp, q_ned=q_ned, Tyta_min=Tu_min, Tyta_max=Tu_max, Ttak_min=Tn_min, Ttak_max=Tn_max,
                xy=xy, t=t, T=T)


def fall(djup, T_kallare, delning=DELNING):
    """Vattentemperatur som ger Q_MAL uppåt (lösningen är linjär i temperaturerna)."""
    a = los(djup, T_RUM + 10, T_kallare, delning)
    b = los(djup, T_RUM + 20, T_kallare, delning)
    k = (b["q_upp"] - a["q_upp"]) / 10
    Tw = T_RUM + 10 + (Q_MAL - a["q_upp"]) / k
    r = los(djup, Tw, T_kallare, delning)
    r["T_vatten"] = Tw
    r["andel_ned"] = r["q_ned"] / (r["q_upp"] + r["q_ned"])
    return r


def endim(djup, T_kallare=20.0):
    """1D-kontroll: slangarna som ett plant värmeskikt på djupet djup. Andel nedåt för samma vattentemperatur."""
    Ru = djup / 1000 / LAM["betong"] + T_TRA / 1000 / LAM["tra"] + 1 / H_UPP
    Rn = (H_BET - djup) / 1000 / LAM["betong"] + 1 / H_NED
    return Ru / (Ru + Rn)


if __name__ == "__main__":
    for Tk in (20.0, 15.0):
        print(f"källare {Tk:.0f} °C")
        for djup in (50, 75, 100):
            r = fall(djup, Tk)
            print(f"    1D-kontroll andel nedåt {endim(djup)*100:.0f} %")
            print(f"  slang {djup:3d} mm under ovansidan: vatten {r['T_vatten']:.1f} °C, uppåt {r['q_upp']:.1f} W/m², "
                  f"nedåt {r['q_ned']:.1f} W/m² ({r['andel_ned']*100:.0f} %), golvyta {r['Tyta_min']:.1f}–{r['Tyta_max']:.1f} °C")


DJUP = (50, 75, 100)        # slangens centrum under betongens ovansida: under överkantsnätet, mitt, på underkantsnätet
KALLARE = (20.0, 15.0)


def tabell():
    return {(d, Tk): fall(d, Tk) for Tk in KALLARE for d in DJUP}


def rita(path, res):
    import figurer as F
    from matplotlib.tri import Triangulation
    plt = F.plt
    fig, axs = plt.subplots(1, 2, figsize=(4.6, 3.4))
    for ax, d in zip(axs, (DJUP[0], DJUP[-1])):
        r = res[(d, 20.0)]
        T = Triangulation(r["xy"][:, 0], r["xy"][:, 1], r["t"])
        cs = ax.tricontourf(T, r["T"], levels=np.arange(20, 38.1, 1), cmap=F.ROD, extend="both")
        ax.tricontour(T, r["T"], levels=np.arange(21, 38, 2), colors="#6b6b6b", linewidths=0.3)
        W = DELNING / 2
        ax.plot([0, W, W, 0, 0], [0, 0, H_BET + T_TRA, H_BET + T_TRA, 0], color=F.INK, lw=0.6)
        ax.plot([0, W], [H_BET, H_BET], color=F.INK, lw=0.5)
        ax.text(W / 2, H_BET + T_TRA / 2, "trägolv", ha="center", va="center", fontsize=6, style="italic")
        ax.text(W / 2, H_BET + T_TRA + 6, f"rum {T_RUM:.0f} °C", ha="center", va="bottom", fontsize=6.3)
        ax.text(W / 2, -6, "källare 20 °C", ha="center", va="top", fontsize=6.3)
        ax.set_title(f"slang {d} mm under ovansidan\nvatten {F.sv(r['T_vatten'], 1)} °C, nedåt {r['andel_ned']*100:.0f} %",
                     fontsize=7, pad=3)
        ax.set_aspect("equal"); ax.axis("off")
        ax.set_xlim(-5, W + 5); ax.set_ylim(-25, H_BET + T_TRA + 25)
    cb = fig.colorbar(cs, ax=axs, orientation="horizontal", fraction=0.05, pad=0.04, aspect=35)
    cb.ax.tick_params(labelsize=6); cb.outline.set_linewidth(0.4); cb.set_label("temperatur (°C)", fontsize=6.5)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
