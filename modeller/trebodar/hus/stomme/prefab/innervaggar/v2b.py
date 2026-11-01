"""Bärande innervägg 2B: under dalbalk 2, med stolparna LD2_1–LD2_3.

Regelverk 70 mm C24 i väggens system (skelett.VAGGAR["2B"]): u från (9440; 1065) i växande y, w genom väggen från stommens ena sida, z uppåt från bjälklagets överkant.
"""
from modellering import Montage

from trebodar import skelett as S
from trebodar.byggdelar.regelvagg import regelvagg

DAL = S.BALKAR["DB2"].uk


def montage() -> Montage:
    v = regelvagg("2B", hojd=DAL)
    v.syll(0, 3992)
    v.regel(0)
    v.hammarband(0, 3984.5)
    v.regel(580)
    v.regel(1180)
    v.regel(1780)
    v.regel(2380)
    v.regel(2980)
    v.regel(3580)
    # karmstolparna LD2_1 och LD2_2 vid trapphålets långsidor (y 5 012 och 5 936, K-05), 2 × 45 i väggen
    v.regel(3902, namn="LD2_1-1")
    v.regel(3947, namn="LD2_1-2")
    v.hammarband(3984.5, 6162)
    v.liggande(3992, 4826, 2200)
    v.regel(4560, z0=2245)
    v.syll(4826, 6162)                 # söder om trappan sluten (planritning 201 rev 02)
    v.regel(4826, namn="LD2_2-1")
    v.regel(4871, namn="LD2_2-2")
    v.regel(5361)
    v.regel(5807)
    v.regel(6162, z0=0, z1=DAL, w0=-12.5, w1=82.5, namn="LD2_3-1")
    v.regel(6207, z0=0, z1=DAL, w0=-12.5, w1=82.5, namn="LD2_3-2")
    v.regel(6252, z0=0, z1=DAL, w0=-12.5, w1=82.5, namn="LD2_3-3")
    return v.montage()
