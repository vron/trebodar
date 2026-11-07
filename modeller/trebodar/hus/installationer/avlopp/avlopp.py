"""Avloppet i modellen (Hus/Installationer/Avlopp): ledningarna (ledningar.py) som rör längs sina punkter, badrummets
golvbrunn med kropp, klämring och sil, källarens golvbrunnar med kropp och sil, stammens rensning, luftningshuven på
taket och vattenlåsen under tvättstället, badkaret och diskhon och för tvätten i badrummets skåp (på L10).
Avloppet går genom skikten och bjälklagen utan håltagning i modellen och ingår inte i modellens krockkontroll; dess
egen kontroll (./mod avlopp kontroll) prövar det mot husets delar och de andra installationerna."""
from __future__ import annotations

import math

from modellering import Del, Montage, Placering, box, cylinder

from trebodar import skelett as S
from trebodar.byggdelar.ror import ror
from trebodar.byggdelar.virke import fmt
from trebodar.hus import badrum as B
from trebodar.hus.inredning import koksbank as KB
from trebodar.hus.inredning import koksskap as K
from trebodar.hus.invandigt.kallarens_innervaggar import T_KL8 as KL_T
from trebodar.material import AVLOPPSROR, ROSTFRITT, TAKPLAT

from ..montering import pa_tak
from .ledningar import (BADKAR_AVLOPP, BADKAR_BOTTEN, BRUNN, BRUNN_KALLARE, BRUNN_SIL, DISKHO, GODS,
                        GOLVBRUNNAR_KALLARE, HUV, LUFT_DY, LUFTNING, RENSNING, STAM, TVATTSTALL_AVLOPP, ledningar)

VATTENLAS = 32.0                    # tvättställets och badkarets vattenlås (förenklade som raka rör)
VATTENLAS_KOK = 40.0                # diskhons
VATTENLAS_TVATT = (50.0, 180.0)     # tvättens vattenlås på L10: Ø och höjd (utanpå väggen, slangarna ovanifrån)
SIL_KALLARE = (190.0, 5.0)          # källarens golvbrunnar: silen i kroppens överkant (diameter, tjocklek)
LOCK = 20.0                         # rensningens lock
RENS_UT = 30.0                      # rensningens lock utanför KL8:s gips


def montage() -> Montage:
    m = Montage("Avlopp", beskrivning="Avloppet (ärendena #52 och #49): badrummet till stammen under mellanbjälklaget, "
                                      "köket rakt ned, källarens golvbrunnar och tvätthon, stammen och grundledningen "
                                      "under bottenplattan mot förbindelsepunkten")
    for led in ledningar().values():
        for i, (a, b) in enumerate(zip(led.vag, led.vag[1:]), 1):
            if math.dist(a, b) < 1.0:
                continue
            namn = f"Avloppsrör PEX Ø{fmt(led.d)}, pumpat" if led.pumpad else f"Avloppsrör PP Ø{fmt(led.d)}"
            m.lagg(Del(namn, ror(a, b, led.d, GODS[led.d]), AVLOPPSROR), Placering(), f"{led.id}-{i:02d}")
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
    # stammens rensning: en stos mot teknikrummet genom KL8:s gips, med lock
    sx, sy, sd = STAM
    z, sida = RENSNING
    lang = KL_T / 2 + RENS_UT
    stos = Placering.axlar((sx, sy, z), (1.0, 0.0, 0.0), (0.0, sida, 0.0))
    m.lagg(Del(f"Rensning Ø{fmt(sd)}", ror((0.0, 0.0, 0.0), (0.0, 0.0, lang), sd, GODS[sd]), AVLOPPSROR), stos,
           "AV-RENS")
    m.lagg(Del(f"Rensningens lock Ø{fmt(sd)}", cylinder(sd / 2, LOCK, (0.0, 0.0, lang)), AVLOPPSROR), stos,
           "AV-RENS-LOCK")
    # luftningshuven av plåt: röret lodrätt från takets yta, huven överst och en plåt runt röret i takets plan
    mt = pa_tak(sx, sy + LUFT_DY)
    upp = Placering.axlar(mt.punkt, (1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
    r = LUFTNING[1] / 2 + 3.0
    m.lagg(Del(f"Luftningshuv, rör Ø{fmt(2 * r)}", cylinder(r, HUV[1] - 50.0, (0.0, 0.0, -40.0))
               - cylinder(r - 1.0, HUV[1], (0.0, 0.0, -50.0)), TAKPLAT), upp, "AV-HUV-ROR")
    m.lagg(Del(f"Luftningshuv Ø{fmt(HUV[0])}", cylinder(HUV[0] / 2, 50.0, (0.0, 0.0, HUV[1] - 60.0))
               - cylinder(HUV[0] / 2 - 1.0, 50.0, (0.0, 0.0, HUV[1] - 61.0)), TAKPLAT), upp, "AV-HUV")
    kant = HUV[0] / 2 + 80.0
    m.lagg(Del("Luftningshuv, plåt i takets plan", box(-kant, kant, -kant, kant, 0.0, 2.0)
               - cylinder(r, 10.0, (0.0, 0.0, -5.0)),
               TAKPLAT), Placering.axlar(mt.punkt, (0.0, 1.0, 0.0), mt.normal), "AV-HUV-PLAT")
    # köket: diskhons vattenlås från hons botten ned till golvet bakom lådorna
    xp, yp = DISKHO
    las = ror((xp, yp, 0.0), (xp, yp, K.Z_TOPP - KB.DISKHO[2]), VATTENLAS_KOK, GODS[VATTENLAS_KOK])
    m.lagg(Del(f"Vattenlås Ø{fmt(VATTENLAS_KOK)}", las, AVLOPPSROR), Placering(), "AV-VL-DB")
    # tvätten i badrummets skåp: vattenlåset utanpå L10, med utloppet in i väggen där AV21 börjar
    x, z = B.TVATT_AVLOPP
    zg = B.golvniva(x, B.Y_L10 + 50.0)
    d, h = VATTENLAS_TVATT
    y = B.Y_L10 + d / 2
    m.lagg(Del(f"Vattenlås för tvättmaskin Ø{fmt(d)}", ror((x, y, zg + z - h / 2), (x, y, zg + z + h / 2), d, GODS[d]),
               AVLOPPSROR, produkt=None), Placering(), "AV-VL-TM")
    return m
