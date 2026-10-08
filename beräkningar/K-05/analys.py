"""
Analyser ovanpå plattmodellen: linjärelastisk brottgränsanalys och långtidsnedböjning enligt 7.4.3
med sprickbildning och krympning element för element.
"""
from __future__ import annotations

import numpy as np

from platta import Platta, Dmat
from ec2 import Betong, Stal, Armering, styvhet_effektiv


def elastisk(P: Platta, f, b: Betong, h, nu=0.2, E=None):
    """Linjärelastisk analys med okrossat tvärsnitt (5.4)."""
    E = b.Ecm if E is None else E
    D = E * h ** 3 / 12 / (1 - nu ** 2)
    P.styvhet(Dmat(D, nu))
    return P.los(f)


def _lager(arm: Armering, riktning):
    return [(arm.lager(riktning, "u").As, arm.lager(riktning, "u").y),
            (arm.lager(riktning, "o").As, arm.lager(riktning, "o").y)]


def nedbojning(P: Platta, f, arm: Armering, b: Betong, s: Stal, phi, ecs, beta=0.5, iter_max=30, tol=1e-3,
               fullt_sprucken=False, nu=0.0, fct=None, arm_fn=None):
    """Långtidsnedböjning för lasten f (kvasipermanent) enligt 7.4.3:
    för varje element och riktning interpoleras krökningen mellan stadium I och II med ζ (7.19),
    Ec,eff = Ecm/(1+φ) och krympkrökning (7.21). Ortotropt styvhetsfält, itereras tills nedböjningen
    konvergerar. fullt_sprucken=True ger ζ = 1 överallt."""
    h = arm.h
    cen = P.xy[P.tri].mean(axis=1)
    arms = [arm if arm_fn is None else arm_fn(*cen[e]) for e in range(P.ne)]
    Eeff = b.Ecm / (1 + phi)
    # start: okrossat
    r = elastisk(P, f, b, h, nu=0.2, E=Eeff)
    wprev = r.w.max()
    for it in range(iter_max):
        De = np.zeros((P.ne, 3, 3))
        chi0 = np.zeros((P.ne, 3))
        zx = np.zeros(P.ne); zy = np.zeros(P.ne)
        for e in range(P.ne):
            lx, ly = _lager(arms[e], "x"), _lager(arms[e], "y")
            mx, my, mxy = r.m_el[e]
            # vridmomentet läggs på det böjande momentet som i Wood–Armer (sprickbildning på säker sida)
            Mx = mx + np.sign(mx if mx != 0 else 1) * abs(mxy)
            My = my + np.sign(my if my != 0 else 1) * abs(mxy)
            EIx, kx, zx[e] = styvhet_effektiv(Mx, h, lx, b, s, phi, ecs, beta, fct)
            EIy, ky, zy[e] = styvhet_effektiv(My, h, ly, b, s, phi, ecs, beta, fct)
            if fullt_sprucken:
                EIx, kx, zx[e] = styvhet_effektiv(np.sign(Mx or 1) * 1e12, h, lx, b, s, phi, ecs, 0.0, fct)
                EIy, ky, zy[e] = styvhet_effektiv(np.sign(My or 1) * 1e12, h, ly, b, s, phi, ecs, 0.0, fct)
            De[e] = Dmat(EIx, nu, EIy)
            chi0[e] = [-kx, -ky, 0.0]          # krympkrökning, positiv κ = nedböjande ⇒ χ0 = −κ
        P.styvhet(De)
        r = P.los(f + P.last_krokning(chi0), chi0)
        w = r.w.max()
        if abs(w - wprev) < tol * abs(w):
            break
        wprev = w
    r.zeta = (zx, zy)
    r.iter = it + 1
    return r
