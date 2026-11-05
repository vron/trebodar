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
