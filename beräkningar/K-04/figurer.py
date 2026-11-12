"""Figurerna i K-04: balkmodellen i 3D med stålbanden och utnyttjandet, och planen med väggarnas band."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib import font_manager  # noqa: E402

from natverk import Natverk  # noqa: E402

for _f in (Path(__file__).parent.parent / ".fonts").glob("*.ttf"):
    font_manager.fontManager.addfont(str(_f))
plt.rcParams.update({"font.family": "Carlito", "font.size": 8, "svg.fonttype": "none"})
GRA, BLA, ROD, ORANGE = "#9aa0a6", "#2f6db5", "#b5463a", "#d08a2c"


def _projektion(P: np.ndarray, az: float = -55.0, el: float = 28.0) -> np.ndarray:
    a, e = np.radians(az), np.radians(el)
    R = np.array([[np.cos(a), -np.sin(a), 0.0],
                  [np.sin(a) * np.sin(e), np.cos(a) * np.sin(e), np.cos(e)]])
    return P @ R.T


def modell(N: Natverk, K: dict[str, Any], fil: Path) -> None:
    """Balkmodellen i 3D: delarna grå (röda över 100 % utnyttjande), banden blå, upplagen."""
    m = N.modell
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    eta = K["eta_element"]
    for ok in (True, False):
        e = np.flatnonzero((eta <= 1.0) == ok)
        for i in e:
            P = _projektion(np.array([m.x[m.bi[i]], m.x[m.bj[i]]]))
            ax.plot(P[:, 0], P[:, 1], color=GRA if ok else ROD, lw=0.45 if ok else 1.2, zorder=1 if ok else 3)
    for k, (i, j) in enumerate(zip(m.ti, m.tj)):
        P = _projektion(np.array([m.x[i], m.x[j]]))
        ax.plot(P[:, 0], P[:, 1], color=BLA, lw=0.8, zorder=2)
    U = _projektion(m.x[m.upplag])
    ax.scatter(U[:, 0], U[:, 1], s=1.2, color="k", zorder=4)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.plot([], [], color=GRA, lw=1, label="del")
    ax.plot([], [], color=BLA, lw=1, label="stålband")
    ax.plot([], [], color=ROD, lw=1.5, label="utnyttjande över 100 %")
    ax.legend(loc="lower left", frameon=False, fontsize=7.5)
    fig.tight_layout(pad=0.1)
    fig.savefig(fil)
    plt.close(fig)


def plan(N: Natverk, K: dict[str, Any], fil: Path) -> None:
    """Planen: väggarna, banden i väggarna och takfallen och kropparnas nock- och dalbalkar."""
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    for v in N.ytor["vaggar"]:
        o, u = np.array(v["origo"]), np.array(v["u"])
        a, b = o, o + v["langd"] * u
        ax.plot([a[0], b[0]], [a[1], b[1]], color="#5a5f66" if v["yttervagg"] else "#9aa0a6",
                lw=2.4 if v["yttervagg"] else 1.6, solid_capstyle="butt", zorder=1)
        mitt = o + 0.5 * v["langd"] * u + np.array(v["w"]) * (-260 if v["yttervagg"] else 180)
        ax.text(mitt[0], mitt[1], v["kod"], fontsize=6.5, ha="center", va="center", color="#333")
    eta_b = K["eta_band"]
    for k, d in enumerate(N.band):
        b = N.delar[d]
        c = ROD if eta_b[k] > 1.0 else BLA
        ax.plot([b.a[0], b.b[0]], [b.a[1], b.b[1]], color=c, lw=1.4 if b.grupp == "band_vagg" else 0.6,
                alpha=1.0 if b.grupp == "band_vagg" else 0.6, zorder=3)
    for b in N.delar:
        if b.grupp == "balk":
            ax.plot([b.a[0], b.b[0]], [b.a[1], b.b[1]], color="k", lw=0.8, ls=(0, (4, 2)), zorder=2)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.plot([], [], color=BLA, lw=1.4, label="stålband i väggen (i plan)")
    ax.plot([], [], color=BLA, lw=0.6, alpha=0.6, label="stålband i takfallet")
    ax.plot([], [], color="k", lw=0.8, ls=(0, (4, 2)), label="nock- och dalbalkar")
    ax.legend(loc="upper right", frameon=False, fontsize=7)
    fig.tight_layout(pad=0.1)
    fig.savefig(fil)
    plt.close(fig)


FARG = {"C24": "#efe3c4", "GL30c": "#dcb878", "GL30h": "#dcb878", "S355": "#aab3bf", "S235": "#aab3bf",
        "Spikplåt": "#c4ccd6", "Distansregel": "#efe3c4"}


def sektion(N: Natverk, delar: list[dict[str, Any]], plan: dict[str, Any], F: np.ndarray, band: np.ndarray,
            felande: set[int], fil: Path) -> None:
    """Ett plan genom stommen (en vägg med takstolen på den, eller ett lodrätt snitt längs en takbalk), sett från
    utsidan: delarna ur modellen (felande delar röda), balkelementen med normalkraften i kombinationen (kN, rött
    tryck och grönt drag) och banden (blå) med sin kraft."""
    o, u, w = (np.asarray(plan[k], float) for k in ("o", "u", "w"))
    u0, u1, w0, w1 = plan["u0"], plan["u1"], plan["w0"], plan["w1"]

    def uz(P: np.ndarray) -> np.ndarray:
        return np.column_stack([(P[:, :2] - o) @ u, P[:, 2]])

    def ww(P: np.ndarray) -> np.ndarray:
        return (P[:, :2] - o) @ w
    nyckel = {(b.grupp, b.element, b.namn): b.nr for b in N.delar}
    fig, ax = plt.subplots(figsize=(7.2, 3.1))
    ztop = 0.0
    from scipy.spatial import ConvexHull
    from matplotlib.patches import Polygon as Poly
    for d in delar:
        if d["material"] == "Stålband":
            continue
        R, t = np.array(d["R"]), np.array(d["t"])
        x0, y0, z0, x1, y1, z1 = d["bb"]
        if "kontur" in d:
            k = np.array(d["kontur"])
            P = np.concatenate([np.column_stack([k, np.full(len(k), z)]) for z in (z0, z1)]) @ R.T + t
        else:
            P = np.array([[x, y, z] for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]) @ R.T + t
        W = ww(P)
        if W.max() < w0 or W.min() > w1:
            continue
        Q = uz(P)
        if Q[:, 0].max() < u0 or Q[:, 0].min() > u1:
            continue
        try:
            h = ConvexHull(Q)
        except Exception:                                                     # noqa: BLE001
            continue
        nr = nyckel.get((d["grupp"], d["element"], d["namn"]))
        fel = nr in felande
        ax.add_patch(Poly(Q[h.vertices], closed=True, facecolor="#f2b8ad" if fel else FARG.get(d["material"], "#eee"),
                          edgecolor=ROD if fel else "#7a7a7a", lw=1.0 if fel else 0.35, zorder=2 if fel else 1))
        ztop = max(ztop, Q[:, 1].max())
        if fel:
            c = Q.mean(axis=0)
            ax.text(c[0], c[1], d["namn"].split("-", 1)[-1], fontsize=6.5, color=ROD, ha="center", va="center",
                    fontweight="bold", zorder=6)
    m = N.modell
    X = uz(m.x)
    Wn = ww(m.x)
    inne = (Wn >= w0) & (Wn <= w1) & (X[:, 0] >= u0) & (X[:, 0] <= u1)
    for e in np.flatnonzero(inne[m.bi] & inne[m.bj]):
        Ne = F[e, 6] / 1e3
        q = X[[m.bi[e], m.bj[e]]]
        ax.plot(q[:, 0], q[:, 1], color="#b5463a" if Ne < -0.5 else "#2e7d32" if Ne > 0.5 else "#888",
                lw=0.5 + min(abs(Ne), 30) / 12, alpha=0.85, zorder=3)
        if abs(Ne) >= 3 and np.linalg.norm(q[1] - q[0]) > 250:
            c = q.mean(axis=0)
            ax.text(c[0], c[1], f"{Ne:.0f}", fontsize=5.6, color="#333", ha="left", va="bottom", zorder=5,
                    bbox=dict(boxstyle="square,pad=0.05", fc="white", ec="none", alpha=0.7))
    for k, (i, j) in enumerate(zip(m.ti, m.tj)):
        if inne[i] and inne[j]:
            q = X[[i, j]]
            ax.plot(q[:, 0], q[:, 1], color=BLA, lw=1.4, alpha=0.6, zorder=3)
            if band[k] > 500:
                c = q.mean(axis=0)
                ax.text(c[0], c[1], f"{band[k] / 1e3:.0f}", fontsize=5.6, color=BLA, ha="right", zorder=5)
    ax.scatter(X[inne, 0], X[inne, 1], s=2.5, color="k", zorder=4)
    ax.set_aspect("equal")
    ax.set_xlim(u0, u1)
    ax.set_ylim(-150, max(ztop, X[inne, 1].max() if inne.any() else 0) + 150)
    ax.axis("off")
    fig.tight_layout(pad=0.1)
    fig.savefig(fil)
    plt.close(fig)


def forankring(N: Natverk, FA: dict[str, Any], BV: dict[str, Any], fil: Path) -> None:
    """Förankringen i plan: väggarna, betongbultarna genom syllarna (lodräta och sneda), modellens vinkelbeslag och
    förankringsbeslag och upplagen där beslag saknas eller inte räcker."""
    fig, ax = plt.subplots(figsize=(7.2, 5.4))
    for v in N.ytor["vaggar"]:
        o, u = np.array(v["origo"]), np.array(v["u"])
        a, b = o, o + v["langd"] * u
        ax.plot([a[0], b[0]], [a[1], b[1]], color="#9aa0a6" if v["yttervagg"] else "#c4c8cc",
                lw=2.4 if v["yttervagg"] else 1.6, solid_capstyle="butt", zorder=1)
        mitt = o + 0.5 * v["langd"] * u + np.array(v["w"]) * (-300 if v["yttervagg"] else 200)
        ax.text(mitt[0], mitt[1], v["kod"], fontsize=6.5, ha="center", va="center", color="#333")
    lodr = [p for p in BV["bultar"]["lagen"] if p.get("lutning", 0.0) < 0.5]
    sned = [p for p in BV["bultar"]["lagen"] if p.get("lutning", 0.0) >= 0.5]
    ax.scatter([p["x"] for p in lodr], [p["y"] for p in lodr], s=6, color="#333", zorder=3, linewidths=0)
    ax.scatter([p["x"] for p in sned], [p["y"] for p in sned], s=9, facecolors="none", edgecolors="#333",
               linewidths=0.6, zorder=3)
    stil = {"ABR10525": dict(marker="s", s=14, color=BLA, linewidths=0),
            "WHT340": dict(marker="D", s=30, color="#b07a2a", linewidths=0)}
    for slag, st in stil.items():
        p = [b for b in BV.get("beslag", []) if b["slag"] == slag]
        if p:
            ax.scatter([b["x"] for b in p], [b["y"] for b in p], zorder=4, **st)
    fel = [b for b in FA["beslag"] if not b["eta"] <= 1.0]
    for b in fel:
        ax.scatter([b["x"]], [b["y"]], marker="x", s=40, color=ROD, zorder=5, linewidths=1.2)
        ax.annotate(b["del"], (b["x"], b["y"]), (6, 4), textcoords="offset points", fontsize=6, color=ROD)
    ax.scatter([], [], s=6, color="#333", label="betongbult genom syllen")
    ax.scatter([], [], s=9, facecolors="none", edgecolors="#333", linewidths=0.6, label="sned betongbult (inåt)")
    ax.scatter([], [], label="vinkelbeslag ABR10525", **stil["ABR10525"])
    ax.scatter([], [], label="förankringsbeslag WHT340", **stil["WHT340"])
    if fel:
        ax.scatter([], [], marker="x", s=40, color=ROD, linewidths=1.2, label="beslag saknas eller räcker inte")
    ax.set_aspect("equal")
    ax.axis("off")
    ax.legend(loc="upper right", frameon=False, fontsize=7)
    fig.tight_layout(pad=0.1)
    fig.savefig(fil)
    plt.close(fig)
