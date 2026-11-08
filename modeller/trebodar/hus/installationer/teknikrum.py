"""Teknikrummet i källarens vänstra del, i hörnet vid ytterväggen V3 och innerväggen V19 (under badrummet och hallen):
utrustningen för vatten, värme och el, som installationerna (vatten/, golvvarme/, el/) ansluter till, och dess
geometri.
Rummets väggar är källarens innerväggar KL8–KL10 (invandigt/kallarens_innervaggar.py) med en knyck runt värmepumpen;
YTA är den del av källaren som pekats ut för utrustningen.

- Bergvärmepumpen med inbyggd varmvattenberedare (allmän, ej vald: 600 × 620 × 1 800) med baksidan mot V19;
  anslutningarna på ovansidan: köldbärare in och ut, värme fram och retur till golvvärmen (golvvarme/, fördelarna på
  V5) och kallvatten in och varmvatten ut (vid baksidan, mot fördelarskåpet).
- Tappvattnets fördelarskåp (rör-i-rör) på V19 norr om värmepumpen, med kallvattnets och varmvattnets fördelare; rören
  går ut genom skåpets öppna ovansida, söder om ventilationens kanal FF3 under taket längs V3. Kort
  varmvattenledning från beredaren.
- Inkommande vatten (servisen) upp genom bottenplattan vid V3, med vattenmätare och huvudavstängning på V3. Servisens
  väg till huset är inte bestämd.
- Elens gruppcentral på V3 väster om vattenmätaren (el/grupper.py), rören ur dess ovansida upp i mellanbjälklaget.
- Drivdonsskåpet för källarens ljuslinjer (TK-LC, el/rum/kallare.py) på KL8:s norra sida: ett plåtskåp (ej valt) med
  ett 24 V-drivdon per tändgrupp, åtkomligt framifrån; rören (den dimrade fasen från dimrarna och 24 V till
  ljuslinjerna) ur dess ovansida i en rad upp i mellanbjälklaget.

Utrustningen kontrolleras i modellens krockkontroll (står på golvet och hänger på väggarna). Lägen i K-05:s
koordinater, z från plan 1:s golv (källarens golv z −2 250).
"""
from __future__ import annotations

from dataclasses import dataclass

from modellering import Del, Montage, Placering, box

from trebodar.hus.invandigt.kallare import GIPS_T
from trebodar.hus.invandigt.kallarens_innervaggar import VAGGAR as KL_VAGGAR
from trebodar.material import DRIVDON as DRIVDON_MAT, PLATSKAP, VVS_APPARAT

from .el.katalog import FDIM_24V_60W
from .montering import PLAN, Montering, Vek, golv, kallarvagg

_V19, _V3 = kallarvagg("V19", 0.0, 0.0, -1).punkt[0], kallarvagg("V3", 0.0, 0.0, -1).punkt[1]
YTA = (1500.0, _V19, 6900.0, _V3)               # (x0, x1, y0, y1): till V19:s och V3:s gips i öster och norr
Z_GOLV = PLAN[0]
PLAT = 1.5                                      # fördelarskåpets plåt


@dataclass(frozen=True)
class Utrustning:
    """Utrustning i teknikrummet: läget (golvet eller väggen, normalen ut i rummet), måtten (bredd längs väggen eller
    x, djup ut från väggen, höjd; höjd 0: bara en anslutning, ingen geometri) och anslutningarna."""
    id: str
    namn: str
    lage: Montering
    matt: tuple[float, float, float]
    anslutningar: dict[str, Vek]
    produkt: str = ""                   # specialprodukt i inköpslistan (IN-01): dess kod; tom: ingen


# bergvärmepumpen: baksidan 20 mm från V19:s gips, y 7 400–8 000; anslutningarna på ovansidan
_VP_X0, _VP_X1, _VP_Y0, _VP_Y1, _VP_H = YTA[1] - 20.0 - 620.0, YTA[1] - 20.0, 7400.0, 8000.0, 1800.0
_TOPP = Z_GOLV + _VP_H
VARMEPUMP = Utrustning(
    "TK-VP", "Bergvärmepump med inbyggd varmvattenberedare (ej vald)",
    golv((_VP_X0 + _VP_X1) / 2, (_VP_Y0 + _VP_Y1) / 2, plan=0), (_VP_X1 - _VP_X0, _VP_Y1 - _VP_Y0, _VP_H),
    {"KB-in": (_VP_X0 + 150.0, _VP_Y0 + 100.0, _TOPP), "KB-ut": (_VP_X0 + 150.0, _VP_Y0 + 200.0, _TOPP),
     "VS-fram": (_VP_X0 + 100.0, _VP_Y0 + 450.0, _TOPP), "VS-retur": (_VP_X0 + 160.0, _VP_Y0 + 450.0, _TOPP),
     "VV-ut": (_VP_X1 - 55.0, _VP_Y1 - 160.0, _TOPP), "KV-in": (_VP_X1 - 55.0, _VP_Y1 - 60.0, _TOPP)},
    produkt="VARMEPUMP")

# tappvattnets fördelarskåp (rör-i-rör) på V19 norr om värmepumpen, söder om ventilationens kanal FF3 längs V3
FORDELARSKAP = Utrustning("TK-FS", "Fördelarskåp för tappvatten, rör-i-rör, öppet uppåt (ej valt)",
                          kallarvagg("V19", 8510.0, 1250.0, -1), (1000.0, 120.0, 600.0), {})

# inkommande vatten: servisen upp ur bottenplattan, vattenmätaren och huvudavstängningen på V3 vid V19
X_VM = 3950.0
SERVIS = Utrustning("TK-SV", "Inkommande vatten (servis), läget ej bestämt", golv(X_VM, 8850.0, plan=0),
                    (63.0, 63.0, 0.0), {"ut": (X_VM, 8850.0, Z_GOLV)})
_VM = kallarvagg("V3", X_VM, 900.0, -1)
VATTENMATARE = Utrustning("TK-VM", "Vattenmätare med huvudavstängning och backventil", _VM, (200.0, 120.0, 250.0),
                          {"in": (_VM.punkt[0], _VM.punkt[1] - 60.0, _VM.punkt[2] - 125.0),
                           "ut": (_VM.punkt[0], _VM.punkt[1] - 60.0, _VM.punkt[2] + 125.0)})

# elcentralen (gruppcentralen, #51) på V3 väster om vattenmätaren, x 2 400–3 000, med FRITT_FRAMFOR fritt framför;
# ventilationens kanal FF3-K2 går längs V3 under taket från V19 till x 2 810 och där bort från väggen, över
# centralens östra del, så centralen sitter lägre (överkanten Z_GC_TOPP under kanalen) och rören går upp ur ovansidans
# västra del, väster om kanalen, rakt in i mellanbjälklaget (el/grupper.py, el/bjalklag/mellanbjalklag.py)
X_GC = 2700.0
FRITT_FRAMFOR = 800.0
GC_MATT = (600.0, 130.0, 900.0)                 # bredd, djup, höjd
Z_GC_TOPP = -420.0                              # centralens överkant, under kanalens underkant (z −367)
_GC = kallarvagg("V3", X_GC, Z_GC_TOPP - GC_MATT[2] / 2 - PLAN[0], -1)
GRUPPCENTRAL = Utrustning("TK-GC", "Gruppcentral, fyra rader (72 moduler), utanpåliggande (ej vald)", _GC,
                          GC_MATT, {"topp": (X_GC, _GC.punkt[1] - GC_MATT[1] / 2, Z_GC_TOPP)}, produkt="GRUPPCENTRAL")

# drivdonsskåpet för källarens ljuslinjer (el/rum/kallare.py, #51) på KL8:s norra sida mitt emot centralen, väster om
# avloppet AV7 i KL8 och söder om ventilationens kanal FF3-K2 och dess don: drivdonen 24 V (fasdimbara, ett per
# tändgrupp och kanal), de dimrade faserna från dimrarna in och 24 V ut till ljuslinjerna, rören rakt upp ur skåpets
# ovansida in i bjälklaget; åtkomligt framifrån
_KL8 = KL_VAGGAR["KL8"]
X_LC = 2730.0
LC_MATT = (500.0, 130.0, 600.0)                 # bredd, djup, höjd
Z_LC_TOPP = -300.0
_LC = Montering((X_LC, _KL8.c + _KL8.h + GIPS_T, Z_LC_TOPP - LC_MATT[2] / 2), (0.0, 1.0, 0.0), "vagg", "KL8")
DRIVDONSSKAP = Utrustning("TK-LC", "Drivdonsskåp för ljuslinjerna, plåtskåp utanpåliggande (ej valt)", _LC, LC_MATT,
                          {"topp": (X_LC, _LC.punkt[1] + LC_MATT[1] / 2, Z_LC_TOPP)}, produkt="DRIVDONSSKAP")
# drivdonen i skåpet, mot dess baksida (längd, bredd, höjd ur katalogen): x längs väggen och z, i två kolumner
DRIVDON_I_SKAPET = ((-120.0, -95.0), (120.0, -95.0), (-120.0, -205.0), (120.0, -205.0), (-120.0, -315.0))
DRIVDON = FDIM_24V_60W

UTRUSTNING = {u.id: u for u in (VARMEPUMP, FORDELARSKAP, SERVIS, VATTENMATARE, GRUPPCENTRAL, DRIVDONSSKAP)}


def _placering(u: Utrustning) -> Placering:
    """Utrustningens system: origo i lägets punkt, x längs väggen (golvet: x), y ut från väggen, z uppåt."""
    n = u.lage.normal
    if u.lage.yta == "golv":
        return Placering.axlar(u.lage.punkt, (1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
    return Placering.axlar(u.lage.punkt, (n[1], -n[0], 0.0), (0.0, 0.0, 1.0))


def _skap(u: Utrustning) -> Montage:
    """Fördelarskåpet som plåtlåda öppen uppåt (rören går ut genom ovansidan): baksida, dörr, sidor och botten."""
    b, d, h = u.matt
    m = Montage(u.id, beskrivning=u.namn)
    for namn, form in (("baksida", box(-b / 2, b / 2, 0.0, PLAT, -h / 2, h / 2)),
                       ("dörr", box(-b / 2, b / 2, d - PLAT, d, -h / 2, h / 2)),
                       ("sida 1", box(-b / 2, -b / 2 + PLAT, PLAT, d - PLAT, -h / 2, h / 2)),
                       ("sida 2", box(b / 2 - PLAT, b / 2, PLAT, d - PLAT, -h / 2, h / 2)),
                       ("botten", box(-b / 2 + PLAT, b / 2 - PLAT, PLAT, d - PLAT, -h / 2, -h / 2 + PLAT))):
        m.lagg(Del(f"Fördelarskåp, {namn}", form, PLATSKAP), _placering(u), f"{u.id}-{namn.replace(' ', '')}")
    return m


def _drivdonsskap(u: Utrustning) -> Montage:
    """Drivdonsskåpet: plåtlåda (baksida, dörr, sidor, tak och botten) med drivdonen mot baksidan."""
    b, d, h = u.matt
    m = Montage(u.id, beskrivning=u.namn, produkt=u.produkt or None)
    for namn, form in (("baksida", box(-b / 2, b / 2, 0.0, PLAT, -h / 2, h / 2)),
                       ("dörr", box(-b / 2, b / 2, d - PLAT, d, -h / 2, h / 2)),
                       ("sida 1", box(-b / 2, -b / 2 + PLAT, PLAT, d - PLAT, -h / 2, h / 2)),
                       ("sida 2", box(b / 2 - PLAT, b / 2, PLAT, d - PLAT, -h / 2, h / 2)),
                       ("tak", box(-b / 2 + PLAT, b / 2 - PLAT, PLAT, d - PLAT, h / 2 - PLAT, h / 2)),
                       ("botten", box(-b / 2 + PLAT, b / 2 - PLAT, PLAT, d - PLAT, -h / 2, -h / 2 + PLAT))):
        m.lagg(Del(f"Drivdonsskåp, {namn}", form, PLATSKAP), _placering(u), f"{u.id}-{namn.replace(' ', '')}")
    lg, br, hd = DRIVDON.matt
    for i, (x, z) in enumerate(DRIVDON_I_SKAPET):
        m.lagg(Del(f"{DRIVDON.tillverkare} {DRIVDON.namn} ({DRIVDON.artikel})",
                   box(x - lg / 2, x + lg / 2, PLAT, PLAT + hd, h / 2 + z - br / 2, h / 2 + z + br / 2), DRIVDON_MAT,
                   produkt=DRIVDON.produkt or None), _placering(u), f"{u.id}-DD{i + 1}")
    return m


def montage() -> Montage:
    """Teknikrummets utrustning: värmepumpen på golvet, fördelarskåpet, vattenmätaren, elcentralen och drivdonsskåpet
    på väggarna."""
    m = Montage("Teknikrum", beskrivning="Utrustningen i teknikrummet: värmepump, fördelare, vattenmätare, "
                                         "elcentral och drivdonen för källarens ljuslinjer")
    for u in UTRUSTNING.values():
        b, d, h = u.matt
        if h <= 0:
            continue
        if u is FORDELARSKAP:
            m.lagg(_skap(u))
        elif u is DRIVDONSSKAP:
            m.lagg(_drivdonsskap(u))
        elif u.lage.yta == "golv":
            m.lagg(Del(u.namn, box(-b / 2, b / 2, -d / 2, d / 2, 0.0, h), VVS_APPARAT, produkt=u.produkt or None),
                   _placering(u), u.id)
        else:
            mat = PLATSKAP if u is GRUPPCENTRAL else VVS_APPARAT
            m.lagg(Del(u.namn, box(-b / 2, b / 2, 0.0, d, -h / 2, h / 2), mat, produkt=u.produkt or None),
                   _placering(u), u.id)
    return m
