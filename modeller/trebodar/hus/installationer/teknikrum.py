"""Teknikrummet i källarens vänstra del, i hörnet vid ytterväggen V3 och innerväggen V19 (under badrummet och hallen):
utrustningen för vatten och värme, som installationerna (vatten/, senare värme) ansluter till, och dess geometri.
Rummets väggar är inte bestämda; ytan är den del av källaren som pekats ut för teknikrummet.

- Bergvärmepumpen med inbyggd varmvattenberedare (allmän, ej vald: 600 × 620 × 1 800) med baksidan mot V19, söder om
  ventilationens kanal FF3 under taket; anslutningarna på ovansidan: köldbärare in och ut, värme fram och retur,
  kallvatten in och varmvatten ut (vid baksidan, mot fördelarskåpet).
- Golvvärmens fördelare för källarens slingor på V3, där slingornas rör kommer upp ur bottenplattan.
- Tappvattnets fördelarskåp (rör-i-rör) på V19 norr om värmepumpen, med kallvattnets och varmvattnets fördelare; rören
  går ut genom skåpets öppna ovansida. Kort varmvattenledning från beredaren.
- Inkommande vatten (servisen) upp genom bottenplattan vid V3, med vattenmätare och huvudavstängning på V3. Servisens
  väg till huset är inte bestämd.

Utrustningen kontrolleras i modellens krockkontroll (står på golvet och hänger på väggarna). Lägen i K-05:s
koordinater, z från plan 1:s golv (källarens golv z −2 250).
"""
from __future__ import annotations

from dataclasses import dataclass

from modellering import Del, Montage, Placering, box

from trebodar.material import PLATSKAP, VVS_APPARAT

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


# bergvärmepumpen: baksidan 20 mm från V19:s gips, y 7 400–8 000; anslutningarna på ovansidan
_VP_X0, _VP_X1, _VP_Y0, _VP_Y1, _VP_H = YTA[1] - 20.0 - 620.0, YTA[1] - 20.0, 7400.0, 8000.0, 1800.0
_TOPP = Z_GOLV + _VP_H
VARMEPUMP = Utrustning(
    "TK-VP", "Bergvärmepump med inbyggd varmvattenberedare (ej vald)",
    golv((_VP_X0 + _VP_X1) / 2, (_VP_Y0 + _VP_Y1) / 2, plan=0), (_VP_X1 - _VP_X0, _VP_Y1 - _VP_Y0, _VP_H),
    {"KB-in": (_VP_X0 + 150.0, _VP_Y0 + 100.0, _TOPP), "KB-ut": (_VP_X0 + 150.0, _VP_Y0 + 200.0, _TOPP),
     "VS-fram": (_VP_X0 + 150.0, _VP_Y1 - 200.0, _TOPP), "VS-retur": (_VP_X0 + 150.0, _VP_Y1 - 100.0, _TOPP),
     "VV-ut": (_VP_X1 - 55.0, _VP_Y1 - 160.0, _TOPP), "KV-in": (_VP_X1 - 55.0, _VP_Y1 - 60.0, _TOPP)})

# golvvärmens fördelare för källaren: på V3 där slingornas rör kommer upp ur bottenplattan
GOLVVARMEFORDELARE = Utrustning("TK-GVF", "Golvvärmefördelare, källaren (ej vald)", kallarvagg("V3", 3505.0, 700.0, -1),
                                (400.0, 100.0, 400.0), {})

# tappvattnets fördelarskåp (rör-i-rör) på V19 norr om värmepumpen, fritt från ventilationens kanal FF3 (y 8 220)
FORDELARSKAP = Utrustning("TK-FS", "Fördelarskåp för tappvatten, rör-i-rör, öppet uppåt (ej valt)",
                          kallarvagg("V19", 8590.0, 1250.0, -1), (600.0, 110.0, 600.0), {})

# inkommande vatten: servisen upp ur bottenplattan, vattenmätaren och huvudavstängningen på V3 vid V19
X_VM = 3950.0
SERVIS = Utrustning("TK-SV", "Inkommande vatten (servis), läget ej bestämt", golv(X_VM, 8850.0, plan=0),
                    (63.0, 63.0, 0.0), {"ut": (X_VM, 8850.0, Z_GOLV)})
_VM = kallarvagg("V3", X_VM, 900.0, -1)
VATTENMATARE = Utrustning("TK-VM", "Vattenmätare med huvudavstängning och backventil", _VM, (200.0, 120.0, 250.0),
                          {"in": (_VM.punkt[0], _VM.punkt[1] - 60.0, _VM.punkt[2] - 125.0),
                           "ut": (_VM.punkt[0], _VM.punkt[1] - 60.0, _VM.punkt[2] + 125.0)})

UTRUSTNING = {u.id: u for u in (VARMEPUMP, GOLVVARMEFORDELARE, FORDELARSKAP, SERVIS, VATTENMATARE)}


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


def montage() -> Montage:
    """Teknikrummets utrustning: värmepumpen på golvet, fördelarskåpet, vattenmätaren och golvvärmens fördelare på
    väggarna."""
    m = Montage("Teknikrum", beskrivning="Utrustningen i teknikrummet: värmepump, fördelare och vattenmätare")
    for u in UTRUSTNING.values():
        b, d, h = u.matt
        if h <= 0:
            continue
        if u is FORDELARSKAP:
            m.lagg(_skap(u))
        elif u.lage.yta == "golv":
            m.lagg(Del(u.namn, box(-b / 2, b / 2, -d / 2, d / 2, 0.0, h), VVS_APPARAT), _placering(u), u.id)
        else:
            m.lagg(Del(u.namn, box(-b / 2, b / 2, 0.0, d, -h / 2, h / 2), VVS_APPARAT), _placering(u), u.id)
    return m
