"""Bärande innervägg 2B: under dalbalk 2, med stolparna LD2_1–LD2_3.

Regelverk 70 mm C24 i väggens system (skelett.VAGGAR["2B"]) upp till dalbalkens underkant, byggt med reglerna i
regelstomme.py: syll (bruten vid fickdörren ID2 till källartrappan och dess ficka mot norr) och hammarband,
karmstolparna LD2_1 vid fickans ände och LD2_2 vid dörren (två reglar, K-03) med överstycke över dörren och fickan
i skenans höjd och kortlingar c/c 600 över det, stolpen LD2_3 i väggens slut (tre reglar 45×95 från bjälklaget till
balken), en regel i början, reglar c/c 600 norr om fickan och två söder om dörren (planritning 201 rev 02). Dalbalken
spänner över dörren och fickan mellan karmstolparna (K-01).
"""
from modellering import Montage

from trebodar import skelett as S
from trebodar.byggdelar.regelvagg import regelvagg
from trebodar.hus.fonster_och_dorrar.oppningar import INNERDORRAR
from trebodar.hus.invandigt.lattvaggar import FICKA_SKENA
from trebodar.hus.stomme.prefab.regelstomme import CC, R, raster, stolpe

DAL = S.BALKAR["DB2"].uk
RASTER = 580.0               # reglarnas c/c-raster genom u 580


def montage() -> Montage:
    v = regelvagg("2B", hojd=DAL)
    langd = S.VAGGAR["2B"].langd
    d = next(d for d in INNERDORRAR if d.kod == "ID2")
    f0 = d.fickan[0]                                     # fickans norra ände
    over = d.hojd + FICKA_SKENA                          # överstyckets underkant
    u3 = langd - 3 * R
    skarv = f0 - R                                       # hammarbandets skarv mitt på LD2_1
    v.syll(0.0, f0)
    v.syll(d.u1, u3)
    v.hammarband(0.0, skarv)
    v.hammarband(skarv, u3)
    v.regel(0.0)
    staende = [(0.0, R)] + stolpe(v, "LD2_1", f0 - 2 * R, 2) + stolpe(v, "LD2_2", d.u1, 2)
    staende += stolpe(v, "LD2_3", u3, 3, z0=0.0, z1=DAL, w0=-12.5, w1=82.5)
    v.liggande(f0, d.u1, over)
    for u in (RASTER + CC * k for k in range(int(langd // CC) + 1)):
        if f0 < u and u + R < d.u1:
            v.regel(u, z0=over + R)
    reglar = [5361.0, 5807.0]
    staende += [(u, u + R) for u in reglar]
    for u in reglar + raster(RASTER, langd, staende, [(f0, d.u1)], utan=(5980.0,)):
        v.regel(u)
    return v.montage()
