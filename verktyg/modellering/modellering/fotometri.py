"""Armaturers ljusfördelning: läsa EULUMDAT (.ldt, tillverkarnas fotometrifiler), kontrollera ljusflödet och
strålvinkeln och skriva IES (LM-63), som Blender (Cycles) läser i lampornas ljus.

Fördelningen är ljusstyrkan I(C, γ) [cd] i C-planen (azimut runt armaturens axel) och vinkeln γ från nadir (γ = 0
rakt ut ur armaturen). EULUMDAT anger cd per 1 000 lm ljuskälla; här räknas den om till candela för armaturens flöde.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class Fordelning:
    namn: str
    c: np.ndarray                    # C-planens vinklar [°]
    gamma: np.ndarray                # γ [°], 0 = nadir
    cd: np.ndarray                   # ljusstyrkan [cd], form (len(c), len(gamma))
    flode_lampa: float               # ljuskällans flöde enligt filen [lm]
    lysande_d: float                 # den lysande ytans diameter (eller längd) [mm]

    def symmetrisk(self) -> np.ndarray:
        """Medelvärdet över C-planen: I(γ) för en rotationssymmetrisk armatur."""
        return self.cd.mean(axis=0)

    def flode(self) -> float:
        """Ljusflödet ur fördelningen [lm]: ∫ I dΩ (trapetsregeln i γ, medel över C)."""
        g = np.radians(self.gamma)
        return float(2 * math.pi * np.trapezoid(self.symmetrisk() * np.sin(g), g))

    def stralvinkel(self) -> float:
        """Strålvinkeln (full bredd där ljusstyrkan är hälften av den största) [°]."""
        i = self.symmetrisk()
        halv = i.max() / 2
        k = int(np.argmax(i < halv))
        g = self.gamma[k - 1] + (self.gamma[k] - self.gamma[k - 1]) * (i[k - 1] - halv) / (i[k - 1] - i[k])
        return float(2 * g)

    def skalad(self, flode: float) -> Fordelning:
        return Fordelning(self.namn, self.c, self.gamma, self.cd * flode / self.flode(), flode, self.lysande_d)

    def ies(self) -> str:
        """IES LM-63-2002, typ C, rotationssymmetrisk (ett plan), γ 0–180° (uppåt mörkt), absolut fotometri."""
        g = list(self.gamma)
        i = list(self.symmetrisk())
        if g[-1] < 180:
            steg = [a for a in np.arange(math.floor(g[-1] / 5) * 5 + 5, 180.001, 5.0)]
            g += steg
            i += [0.0] * len(steg)
        d = self.lysande_d / 1000
        rader = ["IESNA:LM-63-2002", f"[LUMINAIRE] {self.namn}", "TILT=NONE",
                 f"1 -1 1 {len(g)} 1 1 2 {-d:.4f} {-d:.4f} 0", "1 1 0",
                 " ".join(f"{a:g}" for a in g), "0", " ".join(f"{v:.3f}" for v in i)]
        return "\n".join(rader) + "\n"


def las_ldt(fil: Path) -> Fordelning:
    """EULUMDAT: rubriken (rad 1–26), lamporna, direktandelarna, vinklarna och ljusstyrkorna [cd/klm]."""
    r = [s.strip() for s in fil.read_text(encoding="latin-1").splitlines()]
    isym, mc, ng = int(r[2]), int(r[3]), int(r[5])
    n_set = int(r[25])
    lamp = 26
    # per uppsättning: antal lampor, typ, flöde [lm], färgtemperatur, färgåtergivning, effekt
    flode = sum(float(r[lamp + 2 + 6 * k].replace(",", ".")) * max(1, abs(int(r[lamp + 6 * k])))
                for k in range(n_set))
    a = lamp + 6 * n_set + 10                       # efter lamporna och de tio direktandelarna
    c = np.array([float(v) for v in r[a:a + mc]])
    gamma = np.array([float(v) for v in r[a + mc:a + mc + ng]])
    # antal C-plan i filen efter symmetrin: 1 (rotationssymmetrisk), 0–180, 180–360, 0–90 eller alla
    mc_fil = {0: mc, 1: 1, 2: mc // 2 + 1, 3: mc // 2 + 1, 4: mc // 4 + 1}[isym]
    v = np.array([float(x) for x in r[a + mc + ng:a + mc + ng + mc_fil * ng]]).reshape(mc_fil, ng)
    faktor = float(r[23].replace(",", "."))
    return Fordelning(r[8], c[:mc_fil] if isym else c, gamma, v * faktor * flode / 1000, flode,
                      float(r[15].replace(",", ".")))


def spot(stralvinkel: float, flode: float, namn: str = "spot") -> Fordelning:
    """Ersättning när fotometrifilen saknas: en rotationssymmetrisk stråle (gaussisk) med strålvinkeln (full bredd
    vid halva ljusstyrkan) och flödet, inget ljus över 90°."""
    gamma = np.arange(0.0, 91.0, 1.0)
    i = np.exp(-math.log(2) * (gamma / (stralvinkel / 2)) ** 2)
    i[-1] = 0.0
    return Fordelning(namn, np.array([0.0]), gamma, i[None, :], flode, 40.0).skalad(flode)
