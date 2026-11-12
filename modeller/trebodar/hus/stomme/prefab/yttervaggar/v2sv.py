"""Yttervägg 2SV: mittre huskroppens gavel mot SV, upp till dalbalkarnas underkant, med skjutdörren D1 mellan
stolparna LD2_4 och LD4_2 (K-03) under dalbalk 2:s och dalbalk 4:s ände.

Regelverk 145 mm C24 (45×145, K-04) i väggens system (skelett.VAGGAR["2SV"]), byggt med reglerna i regelstomme.py:
syll (bruten vid dörren), ändreglar och stolparna intill dörröppningen. Hammarbandet går över dörren; över varje
stolpe ligger en stålplåt S235 i ett urtag i hammarbandets underkant, och stolpens reglar under plåten går upp till
den.
"""
from modellering import Montage

from trebodar import skelett as S
from trebodar.byggdelar.regelvagg import regelvagg
from trebodar.hus.stomme.prefab.regelstomme import R, plattor, stolpe, vaggens_oppningar
from trebodar.material import S235

DAL = S.BALKAR["DB2"].uk
PLAT_L, PLAT_B, PLAT_T = 500.0, 90.0, 16.0        # stålplåten över stolpen (längs väggen, genom väggen, tjocklek)
URTAG = 18.0                                      # urtaget i hammarbandet för plåten


def montage() -> Montage:
    v = regelvagg("2SV", hojd=DAL)
    langd = S.VAGGAR["2SV"].langd
    (d1,) = vaggens_oppningar("2SV")
    plattor(v, langd, oppningar=[d1], hammarband=None)
    uk_plat = DAL - R + URTAG - PLAT_T
    ld24 = stolpe(v, "LD2_4", d1.u0 - 3 * R, 3, z1=uk_plat)
    ld42 = stolpe(v, "LD4_2", d1.u1, 5, toppar=(uk_plat, uk_plat, uk_plat, None, None))   # den femte vid väggens ände
    v.regel(0.0)
    platar = [(ld24[0][0], ld24[0][0] + PLAT_L), (ld42[2][1] - PLAT_L, ld42[2][1])]
    hb = [(0.0, DAL), (0.0, DAL - R)]
    for a, b in platar:
        v.liggande(a, b, uk_plat, h=PLAT_T, w0=0.0, w1=PLAT_B, typ="P", material=S235, produkt="STALPLATAR-2SV")
        hb += [(a, DAL - R), (a, DAL - R + URTAG), (b, DAL - R + URTAG), (b, DAL - R)]
    v.profil(hb + [(langd, DAL - R), (langd, DAL)], typ="H")
    return v.montage()
