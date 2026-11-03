"""Bärande innervägg 2C: mittre huskroppen, y 5 950, med takstolen 2C.

Regelverk 95 mm C24 i väggens system (skelett.VAGGAR["2C"]) upp till dalbalkarnas underkant, efter stolpen LD4_1
(140×140, stolpar.py) i väggens början: syll (bruten vid fickdörren ID6:s ficka, som går in från L12 söder om
stolpen, och vid kaminens öppning, oppningar.INNEROPPNINGAR) och hammarband, överstycke över fickan i skenans höjd
och vid kaminen, karmreglar, kortlingar över överstyckena, reglar i ändarna och fria reglar.
"""
from modellering import Montage

from trebodar import skelett as S
from trebodar.byggdelar.regelvagg import regelvagg
from trebodar.hus.fonster_och_dorrar.oppningar import INNEROPPNINGAR
from trebodar.hus.invandigt.lattvaggar import H_VIRKE, fickor
from trebodar.hus.stomme.prefab.regelstomme import R
from trebodar.hus.stomme.prefab.stolpar.stolpar import LD4_1, LD4_1_B

DAL = S.BALKAR["DB2"].uk


def montage() -> Montage:
    v = regelvagg("2C", hojd=DAL)
    w = S.VAGGAR["2C"]
    u0 = LD4_1[0] + LD4_1_B / 2 - w.origo[0]                        # stolpen LD4_1:s sida
    _, a, b, _, h, _ = next(o for o in INNEROPPNINGAR if o[0] == "2C")
    _, f1, z1, _ = next(f for f in fickor("2C") if f[3].kod == "ID6")
    over = z1 - H_VIRKE                                             # fickans överstycke
    u_f = 1200.0                                                    # regeln vid fickans ände
    assert f1 <= u_f, "ID6:s ficka når regeln vid fickans ände"
    v.hammarband(u0, w.langd)
    v.syll(u_f, a)
    v.syll(b, w.langd)
    v.liggande(u0, u_f, over)
    v.liggande(a, b, h)
    for u in (u0, 664.0):
        v.regel(u, z0=over + R)
    v.regel(a + 479.5, z0=h + R)
    for u in (u_f, a - R, b, 3662.5, 4262.5, 4795.0, 4840.0, w.langd - R):
        v.regel(u)
    return v.montage()
