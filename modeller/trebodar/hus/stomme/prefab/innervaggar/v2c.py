"""Bärande innervägg 2C: mittre huskroppen, y 5 950, med takstolen 2C.

Regelverk 95 mm C24 i väggens system (skelett.VAGGAR["2C"]) upp till dalbalkarnas underkant, efter stolpen LD4_1
(140×140, stolpar.py) i väggens början: syll (bruten vid fickdörren ID6:s ficka, som går in från L12 söder om
stolpen, och vid kaminens nisch, oppningar.NISCHER) och hammarband, överstycken över fickan i skenans höjd och över
nischen, kortlingar över dem, reglar i ändarna och fria reglar högst c/c 600. Kaminens murade skorsten står i nischen
mot skikten på garderobens sida (kamin.py, #102, #109).
"""
from modellering import Montage

from trebodar import skelett as S
from trebodar.byggdelar.regelvagg import regelvagg
from trebodar.hus.fonster_och_dorrar.oppningar import NISCHER
from trebodar.hus.invandigt.lattvaggar import H_VIRKE, fickor
from trebodar.hus.stomme.prefab.regelstomme import R
from trebodar.hus.stomme.prefab.stolpar.stolpar import LD4_1, LD4_1_B

DAL = S.BALKAR["DB2"].uk


def montage() -> Montage:
    v = regelvagg("2C", hojd=DAL)
    w = S.VAGGAR["2C"]
    u0 = LD4_1[0] + LD4_1_B / 2 - w.origo[0]                        # stolpen LD4_1:s sida
    _, f1, z1, _ = next(f for f in fickor("2C") if f[3].kod == "ID6")
    over = z1 - H_VIRKE                                             # fickans överstycke
    u_f = 1200.0                                                    # regeln vid fickans ände
    assert f1 <= u_f, "ID6:s ficka når regeln vid fickans ände"
    v.hammarband(u0, w.langd)
    _, _, a, b, _, h, _ = next(n for n in NISCHER if n[0] == "2C")     # kaminens nisch (#109)
    v.syll(u_f, a)
    v.syll(b, w.langd)
    v.liggande(u0, u_f, over)
    v.liggande(a, b, h)                                             # överstycke över nischen
    for u in (u0, 664.0):
        v.regel(u, z0=over + R)
    for u in (2185.0, 2677.5):                                      # kortlingar över nischen
        v.regel(u, z0=h + R)
    for u in (u_f, 1692.5, a - R, b, 3170.0, 3662.5, 4262.5, 4795.0, 4840.0, w.langd - R):
        v.regel(u)
    return v.montage()
