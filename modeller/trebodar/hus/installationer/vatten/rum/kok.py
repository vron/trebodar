"""Köket (planritning 201 rev 02 och användarens markeringar): diskbänken på bänken längs 3NV mellan fönstret 3NV-F4
och köksfläkten, och diskmaskinen i öns skåp O1 (#50). Inga golvdosor och inga rör i bjälklaget (#83): kopparrör från
underfördelaren UF1 under köket (underfordelare.py) går under källarens tak och rakt upp genom var sin ingjuten hylsa,
alla kopplingar och avstängningar i källaren.

- Diskbänken: hylsorna står i diskbänksskåpet bakom de korta lådorna (NL 350), intill källarväggen V14:s gips, på
  samma sida om diskhons avlopp som underfördelaren och i samma maska i armeringsnätet: över V14 ligger nätet c/c 150
  och stödjärnen c/c 200 tätt, så hylsorna är Ø50 (två Ø75 ryms inte mellan järnen där). Kopparrören går rakt upp
  till blandarens slangar (kallt till höger, söder om varmt, sett mot blandaren).
- Diskmaskinen: hylsan under maskinens bakre del, kopparrörets ände med maskinens anslutning under den, nås när
  maskinen dras ut (hus/inredning/koksbank.py).
"""
from __future__ import annotations

from trebodar.hus.inredning.koksbank import diskhons_avlopp, diskmaskinens_anslutningar

from ...montering import golv
from ..katalog import DISKBANK, DISKMASKIN, HYLSA_50, KOPPAR_15
from ..punkter import Rum, Tappstalle

RUM = Rum("KO", "Kök", plan=1)

Z_BLANDARE = 500.0              # kopparrörens ände i diskbänksskåpet, där blandarens slangar ansluts
Z_DISKMASKIN = 40.0             # kopparrörets ände under diskmaskinen (maskinens anslutning)
DB_FRAN_AVLOPP = 180.0          # diskbänkens hylsor: kallvattnets från avloppet längs väggen, varmvattnets DB_ISAR
DB_ISAR = 70.0                  # längre bort (mot underfördelaren)
DB_IN = 27.0                    # rören väster om avloppet: mellan lådornas löpare och källarväggens gips (V14)

_x_avlopp, _y_avlopp = diskhons_avlopp()
_X_DB = _x_avlopp - DB_IN
_DB = {"KV": (_X_DB, _y_avlopp + DB_FRAN_AVLOPP), "VV": (_X_DB, _y_avlopp + DB_FRAN_AVLOPP + DB_ISAR)}

TAPPSTALLEN = [
    Tappstalle("KO-DB1", DISKBANK, HYLSA_50, golv(_X_DB, _y_avlopp + DB_FRAN_AVLOPP + DB_ISAR / 2), KOPPAR_15,
               kallt=(0.0, -1.0, 0.0),
               anslutningar=tuple((m, (*_DB[m], Z_BLANDARE)) for m in ("KV", "VV"))),
    Tappstalle("KO-DM1", DISKMASKIN, HYLSA_50, golv(*diskmaskinens_anslutningar()[0]), KOPPAR_15,
               anslutningar=(("KV", (*diskmaskinens_anslutningar()[0], Z_DISKMASKIN)),)),
]
