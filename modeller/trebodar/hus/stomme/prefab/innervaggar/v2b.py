"""Bärande innervägg 2B: under dalbalk 2, med stolparna LD2_1–LD2_3.

Regelverk 70 mm C24 i väggens system (skelett.VAGGAR["2B"]) upp till dalbalkens underkant, byggt med reglerna i
regelstomme.py: syll (bruten vid dörren ID2 till källartrappan) och hammarband, karmstolparna LD2_1 och LD2_2 vid
dörren (två reglar, K-03) med överstycke i dörrens höjd och en kortling, stolpen LD2_3 i väggens slut (tre reglar
45×95 från bjälklaget till balken), en regel i början, reglar c/c 600 norr om dörren och två söder om den
(planritning 201 rev 02).
"""
from modellering import Montage

from trebodar import skelett as S
from trebodar.byggdelar.regelvagg import regelvagg
from trebodar.hus.fonster_och_dorrar.oppningar import INNERDORRAR
from trebodar.hus.stomme.prefab.regelstomme import R, raster, stolpe

DAL = S.BALKAR["DB2"].uk
SKARV = 3984.5               # hammarbandets skarv


def montage() -> Montage:
    v = regelvagg("2B", hojd=DAL)
    langd = S.VAGGAR["2B"].langd
    d = next(d for d in INNERDORRAR if d.kod == "ID2")
    u3 = langd - 3 * R
    v.syll(0.0, d.u0)
    v.syll(d.u1, u3)
    v.hammarband(0.0, SKARV)
    v.hammarband(SKARV, u3)
    v.regel(0.0)
    staende = [(0.0, R)] + stolpe(v, "LD2_1", d.u0 - 2 * R, 2) + stolpe(v, "LD2_2", d.u1, 2)
    staende += stolpe(v, "LD2_3", u3, 3, z0=0.0, z1=DAL, w0=-12.5, w1=82.5)
    v.liggande(d.u0, d.u1, d.hojd)
    v.regel(d.u0 + 568.0, z0=d.hojd + R)
    reglar = [5361.0, 5807.0]
    staende += [(u, u + R) for u in reglar]
    for u in reglar + raster(580.0, langd, staende, [(d.u0, d.u1)], utan=(5980.0,)):
        v.regel(u)
    return v.montage()
