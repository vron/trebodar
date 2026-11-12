"""Lastkombinationerna (SS-EN 1990 med EKS: 6.10a och 6.10b med γd, gynnsam egentyngd vid lyft, karakteristisk och
kvasipermanent kombination i bruksgränstillståndet) och lösningarna för dem: krafterna i balkelementen, i banden
och i upplagen, och förskjutningarna."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

import fem
from laster import Lastfall


@dataclass
class Kombination:
    namn: str
    text: str
    faktorer: dict[str, float]
    kmod: float
    slag: str                    # "STR", "SLS-k" (karakteristisk) eller "SLS-qp" (kvasipermanent)


def kombinationer(fall: list[Lastfall], K: dict[str, Any]) -> list[Kombination]:
    gd, gQ = K["gamma_d"], K["gamma_Q"]
    ga, gb = K["gamma_G"]
    S = [f.namn for f in fall if f.slag == "S"]
    W = [f.namn for f in fall if f.slag == "W"]
    km = K["k_mod"]
    ut = [Kombination("G", "6.10a, egentyngd", {"G": gd * ga}, km["G"], "STR")]
    for s in S:
        ut.append(Kombination(f"G+{s}", f"6.10b, {s} huvudlast", {"G": gd * gb, s: gd * gQ}, km["S"], "STR"))
        for w in W:
            ut.append(Kombination(f"G+{s}+ψ{w}", f"6.10b, {s} huvudlast, {w}",
                                  {"G": gd * gb, s: gd * gQ, w: gd * gQ * K["psi0_vind"]}, km["W"], "STR"))
    for w in W:
        ut.append(Kombination(f"G+{w}", f"6.10b, {w} huvudlast", {"G": gd * gb, w: gd * gQ}, km["W"], "STR"))
        ut.append(Kombination(f"Gfav+{w}", f"gynnsam egentyngd, {w} huvudlast", {"G": K["gamma_Gfav"], w: gd * gQ},
                              km["W"], "STR"))
        for s in S:
            ut.append(Kombination(f"G+{w}+ψ{s}", f"6.10b, {w} huvudlast, {s}",
                                  {"G": gd * gb, w: gd * gQ, s: gd * gQ * K["psi0_sno"]}, km["W"], "STR"))
    # bruksgräns: egentyngd och snö var för sig (nedböjningen med krypning räknas i kontrollen), vind karakteristisk
    ut.append(Kombination("G (k)", "karakteristisk, egentyngd", {"G": 1.0}, km["G"], "SLS-k"))
    for s in S:
        ut.append(Kombination(f"{s} (k)", f"karakteristisk, {s}", {s: 1.0}, km["S"], "SLS-k"))
    for w in W:
        ut.append(Kombination(f"{w} (k)", f"karakteristisk, {w}", {w: 1.0}, km["W"], "SLS-k"))
    return ut


@dataclass
class Losning:
    komb: list[Kombination]
    F: np.ndarray               # (k, m, 12) balkelementens ändkrafter i lokala axlar
    q: np.ndarray               # (k, m, 3) elementens utbredda last i lokala axlar
    band: np.ndarray            # (k, s) bandens normalkraft
    R: np.ndarray               # (k, upplag, 3) upplagsreaktionerna
    u: np.ndarray               # (k, 6n) förskjutningarna
    bindning: np.ndarray        # (k, c) bindningarnas kraft
    skiva: np.ndarray           # (k, p) skjuvskivornas kraft Q (skjuvkraften Q / h)
    iter: np.ndarray            # (k,) iterationer för banden


def los(a: fem.Analys, fall: list[Lastfall], komb: list[Kombination],
        Q_max: Any = None) -> Losning:
    """Lösningarna per kombination; Q_max(kombination) ger skjuvskivornas bärförmåga (None: inga eller elastiska)."""
    namn = [f.namn for f in fall]
    fv = np.array([a.nodlaster(f.q) for f in fall])
    qv = np.array([f.q for f in fall])
    F, Q, B, R, U, It, Fj, Sk = [], [], [], [], [], [], [], []
    for k in komb:
        c = np.array([k.faktorer.get(n, 0.0) for n in namn])
        f = c @ fv
        qg = np.einsum("c,cij->ij", c, qv)
        u, aktiv, it = a.los(f, Q_max(k) if Q_max else None)
        F.append(a.balkkrafter(u, qg))
        Q.append(np.einsum("eij,ej->ei", a.Lam, qg))
        B.append(a.stangkrafter(u, aktiv))
        R.append(a.reaktioner(u, f, aktiv))
        U.append(u)
        It.append(it)
        Fj.append(a.bindningskrafter(u))
        Sk.append(a.skivkrafter(u))
    return Losning(komb, np.array(F), np.array(Q), np.array(B), np.array(R), np.array(U), np.array(Fj), np.array(Sk),
                   np.array(It))
