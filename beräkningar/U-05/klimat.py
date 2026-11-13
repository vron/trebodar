"""
U-05: klimatet på platsen ur ERA5 (U-03:s klimatfil, timvärden 2013–2023) och solinstrålningen mot husets ytor.

Solens läge räknas för varje timmes mitt (ERA5:s värde avser timmen före) med NOAA:s formler. Instrålningen mot en
lutande yta: direkt (DNI · cos θ), diffus från himlen isotropt (DHI · (1 + cos β)/2) och reflekterad från marken
(GHI · ρ · (1 − cos β)/2).
"""
from __future__ import annotations

import gzip
import math
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent


def las(P):
    fil = (HERE / P["klimat"]["fil"]).resolve()
    with gzip.open(fil, "rt", encoding="utf-8") as f:
        rader = [r for r in f if not r.startswith("#")]
    hdr = rader[0].strip().split(",")
    data = np.genfromtxt(rader[1:], delimiter=",", dtype=None, encoding="utf-8", names=hdr)
    tid = np.array(data["tid"], dtype="datetime64[m]")
    a0, a1 = P["klimat"]["ar"]
    ar = tid.astype("datetime64[Y]").astype(int) + 1970
    v = (ar >= a0) & (ar <= a1)
    K = {k: np.asarray(data[k], float)[v] for k in ("T", "RF", "U10", "GHI", "DNI", "DHI")}
    K["tid"] = tid[v]
    K["ar"] = ar[v]
    K["man"] = (tid[v].astype("datetime64[M]").astype(int) % 12) + 1
    return K


def solens_lage(tid, lat, lon):
    """Solens zenitvinkel och azimut (från norr, medurs) [rad] för tiderna (UTC, timmens mitt)."""
    t = (tid - np.timedelta64(30, "m")).astype("datetime64[m]")
    dag = (t.astype("datetime64[D]") - t.astype("datetime64[Y]")).astype(int)
    tim = (t - t.astype("datetime64[D]")).astype(int) / 60.0
    g = 2 * np.pi / 365 * (dag + (tim - 12) / 24)
    eqt = 229.18 * (0.000075 + 0.001868 * np.cos(g) - 0.032077 * np.sin(g) - 0.014615 * np.cos(2 * g)
                    - 0.040849 * np.sin(2 * g))
    dekl = (0.006918 - 0.399912 * np.cos(g) + 0.070257 * np.sin(g) - 0.006758 * np.cos(2 * g)
            + 0.000907 * np.sin(2 * g) - 0.002697 * np.cos(3 * g) + 0.00148 * np.sin(3 * g))
    tst = tim * 60 + eqt + 4 * lon
    ha = np.radians(tst / 4 - 180)
    phi = np.radians(lat)
    cz = np.sin(phi) * np.sin(dekl) + np.cos(phi) * np.cos(dekl) * np.cos(ha)
    zen = np.arccos(np.clip(cz, -1, 1))
    az = np.arctan2(np.sin(ha), np.cos(ha) * np.sin(phi) - np.tan(dekl) * np.cos(phi)) + np.pi
    return zen, az


def instralning(K, azimut, lutning, rho=0.2):
    """Instrålningen [W/m²] mot en yta med azimut (normalens riktning från norr, medurs, grader) och lutning
    (grader från vågrätt), och infallsvinkelns cosinus."""
    zen, az = K["_sol"]
    b = math.radians(lutning)
    g = math.radians(azimut)
    cos_t = np.cos(zen) * math.cos(b) + np.sin(zen) * math.sin(b) * np.cos(az - g)
    sol_uppe = zen < np.radians(89.5)
    direkt = np.where(sol_uppe, K["DNI"] * np.clip(cos_t, 0, None), 0.0)
    diffus = K["DHI"] * (1 + math.cos(b)) / 2
    mark = K["GHI"] * rho * (1 - math.cos(b)) / 2
    return direkt, diffus + mark, np.clip(cos_t, 0, 1)


def iam(cos_t, b0=0.15):
    """Infallsvinkelns inverkan på rutans g-värde (ASHRAE: 1 − b0 (1/cos θ − 1)); diffus strålning 0,85."""
    with np.errstate(divide="ignore"):
        f = 1 - b0 * (1 / np.maximum(cos_t, 1e-3) - 1)
    return np.clip(f, 0, 1)


def azimut(P, dx, dy):
    """Kompassriktningen [grader från norr, medurs] för en riktning (dx, dy) i K-05:s koordinater: +x mot
    azimut_x (318°, nordväst) och +y 90° moturs därifrån (228°, sydväst)."""
    return (P["klimat"]["azimut_x"] - math.degrees(math.atan2(dy, dx))) % 360


def graddagar(K, bas=17.0):
    """Graddagar (dygnsmedel under basen) per år."""
    T = K["T"]
    n = len(T) // 24 * 24
    d = T[:n].reshape(-1, 24).mean(axis=1)
    ar = K["ar"][:n].reshape(-1, 24)[:, 0]
    return {int(a): float(np.clip(bas - d[ar == a], 0, None).sum()) for a in np.unique(ar)}
