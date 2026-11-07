"""Avloppet i modellen (Hus/Installationer/Avlopp): ledningarna (ledningar.py) som rör längs sina punkter, badrummets
golvbrunn med kropp, klämring och sil, källarens golvbrunnar med kropp och sil, stammens rensningslock och vattenlåsen
under tvättstället, badkaret och diskhon och diskmaskinens i sockeln under öns skåp O2. Avloppet går genom skikten och
bjälklagen utan håltagning i modellen och ingår inte i modellens krockkontroll; dess egen kontroll
(./mod avlopp kontroll) prövar det mot husets delar och de andra installationerna."""
from __future__ import annotations

import math

from modellering import Del, Montage, Placering, cylinder

from trebodar import skelett as S
from trebodar.byggdelar.ror import ror
from trebodar.byggdelar.virke import fmt
from trebodar.hus import badrum as B
from trebodar.hus.inredning import koksbank as KB
from trebodar.hus.inredning import koksskap as K
from trebodar.material import AVLOPPSROR, ROSTFRITT

from .ledningar import (BADKAR_AVLOPP, BADKAR_BOTTEN, BRUNN, BRUNN_KALLARE, BRUNN_SIL, DISKHO, GODS,
                        GOLVBRUNNAR_KALLARE, ON_AVLOPP, STAM, TVATTSTALL_AVLOPP, Z_STAM, ledningar)

VATTENLAS = 32.0                    # tvättställets och badkarets vattenlås (förenklade som raka rör)
VATTENLAS_KOK = 40.0                # diskhons och diskmaskinens
Z_DM_VATTENLAS = 80.0               # diskmaskinens vattenlås i sockeln under skåpet O2
SIL_KALLARE = (190.0, 5.0)          # källarens golvbrunnar: silen i kroppens överkant (diameter, tjocklek)
LOCK = 20.0                         # stammens rensningslock


def montage() -> Montage:
    m = Montage("Avlopp", beskrivning="Avloppet (ärendena #52 och #49): badrummet till stammen under mellanbjälklaget, "
                                      "köket rakt ned, källarens golvbrunnar och tvätthon, stammen och grundledningen "
                                      "under bottenplattan mot förbindelsepunkten")
    for led in ledningar().values():
        for i, (a, b) in enumerate(zip(led.vag, led.vag[1:]), 1):
            if math.dist(a, b) < 1.0:
                continue
            m.lagg(Del(f"Avloppsrör PP Ø{fmt(led.d)}", ror(a, b, led.d, GODS[led.d]), AVLOPPSROR),
                   Placering(), f"{led.id}-{i:02d}")
    # golvbrunnen: kroppen i bjälklaget, klämringen i tätskiktet och silen i klinkern
    gx, gy = B.GOLVBRUNN
    d, h = BRUNN
    kropp = cylinder(d / 2, h, (gx, gy, -h)) - cylinder(d / 2 - 10.0, h - 10.0, (gx, gy, -h + 10.0))
    m.lagg(Del(f"Golvbrunn Ø{fmt(d)}, lodrätt utlopp Ø75", kropp, AVLOPPSROR, produkt="GOLVBRUNN"), Placering(),
           "AV-GB")
    m.lagg(Del(f"Golvbrunnens klämring Ø{fmt(BRUNN_SIL[1])}", cylinder(BRUNN_SIL[1] / 2, B.TATSKIKT_T, (gx, gy, 0.0)),
               ROSTFRITT), Placering(), "AV-GB-RING")
    m.lagg(Del(f"Golvbrunnens sil Ø{fmt(BRUNN_SIL[0])}",
               cylinder(BRUNN_SIL[0] / 2, B.KLINKER_T, (gx, gy, B.BRUNN_Z - B.KLINKER_T)), ROSTFRITT), Placering(),
           "AV-GB-SIL")
    # vattenlåsen: från tvättställets och karets botten ned till golvet, där ledningarna AV2 och AV3 börjar
    for kod, (xp, yp), z_botten in (("TS", TVATTSTALL_AVLOPP, B.Z_TVATTSTALL_BOTTEN),
                                    ("BK", BADKAR_AVLOPP, BADKAR_BOTTEN)):
        zg = B.golvniva(xp, yp)
        m.lagg(Del(f"Vattenlås Ø{fmt(VATTENLAS)}", ror((xp, yp, zg), (xp, yp, z_botten), VATTENLAS, GODS[VATTENLAS]),
                   AVLOPPSROR), Placering(), f"AV-VL-{kod}")
    # källarens golvbrunnar: kroppen i bottenplattans betong och silen i dess överkant
    d, h = BRUNN_KALLARE
    for kod, (x, y) in GOLVBRUNNAR_KALLARE.items():
        z0 = S.Z_BOTTENPLATTA - h
        kropp = cylinder(d / 2, h, (x, y, z0)) - cylinder(d / 2 - 10.0, h - 10.0, (x, y, z0 + 10.0))
        m.lagg(Del(f"Golvbrunn Ø{fmt(d)}, lodrätt utlopp Ø110", kropp, AVLOPPSROR, produkt="GOLVBRUNN_KALLARE"),
               Placering(), f"AV-{kod}")
        m.lagg(Del(f"Golvbrunnens sil Ø{fmt(SIL_KALLARE[0])}",
                   cylinder(SIL_KALLARE[0] / 2, SIL_KALLARE[1], (x, y, S.Z_BOTTENPLATTA - SIL_KALLARE[1])), ROSTFRITT),
               Placering(), f"AV-{kod}-SIL")
    # stammens rensningslock
    m.lagg(Del(f"Rensningslock Ø{fmt(STAM[2])}", cylinder(STAM[2] / 2, LOCK, (STAM[0], STAM[1], Z_STAM)), AVLOPPSROR),
           Placering(), "AV-RENS")
    # köket: diskhons vattenlås från hons botten ned till golvet bakom lådorna, diskmaskinens i sockeln under O2
    for kod, (xp, yp), z_topp in (("DB", DISKHO, K.Z_TOPP - KB.DISKHO[2]), ("DM", ON_AVLOPP, Z_DM_VATTENLAS)):
        las = ror((xp, yp, 0.0), (xp, yp, z_topp), VATTENLAS_KOK, GODS[VATTENLAS_KOK])
        m.lagg(Del(f"Vattenlås Ø{fmt(VATTENLAS_KOK)}", las, AVLOPPSROR), Placering(), f"AV-VL-{kod}")
    return m
