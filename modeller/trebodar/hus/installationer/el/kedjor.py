"""Rören mellan gruppernas punkter på plan 1 (#50, #51): gruppens rör från centralen kommer till dess första punkt
(bjalklag/mellanbjalklag.py), och därifrån går ett rör till varje följande punkt i gruppen (grupper.py), förgrenat i
apparatdosorna. Vägarna (dragning.py):

- mellan dosor på olika väggar upp i väggen, i innertakets installationsskikt och ned i den andra väggen;
- mellan dosor intill varandra eller på samma vägg och höjd rakt i väggen (regelfacket eller installationsskiktet);
- köksbänkens uttag i ytterväggens installationsskikt, under och över fönstren och runt hörnet mellan 3NV och 3SV;
- öns uttag och brandlarmets matningsdosa genom mellanbjälklaget.
"""
from __future__ import annotations

from ..montering import BJALKLAG, Vek, i_tak, i_vagg, langs_vaggen, vid_tak
from .dragning import upp_ur_bjalklaget, via_taket
from .katalog import FXP16
from .punkter import Punkt, Ror
from .rum import allrum, badrum, gang, gastrum, hall, kok, kontor, kontor_litet, sovrum, sovrum_litet, vardagsrum
from .bjalklag.mellanbjalklag import D01, PUNKTER as MB_PUNKTER

NAMN = "Gruppernas rör"

_P: dict[str, Punkt] = {p.id: p for m in (allrum, badrum, gang, gastrum, hall, kok, kontor, kontor_litet, sovrum,
                                          sovrum_litet, vardagsrum) for p in m.PUNKTER}
_P.update({p.id: p for p in MB_PUNKTER})


def _tak(grupp: str, n: int, a: str, b: str, forbi: tuple[tuple[float, float], ...] = ()) -> Ror:
    """Genom innertaket, förbi punkterna forbi (i plan) i installationsskiktet."""
    v = via_taket(_P[a].lage, _P[b].lage)
    return Ror(f"{grupp}-R{n}", FXP16, a, b, via=(*v[:2], *(i_tak(x, y) for x, y in forbi), *v[2:]))


def _rakt(grupp: str, n: int, a: str, b: str) -> Ror:
    return Ror(f"{grupp}-R{n}", FXP16, a, b)


def _i_ytterväggen(kod: str, y_eller_x: float, z: float) -> Vek:
    """I ytterväggens installationsskikt vid läget (y längs 3NV, x längs 3SV) och z över golvet."""
    p = (0.0, y_eller_x, 0.0) if kod == "3NV" else (y_eller_x, 0.0, 0.0)
    return i_vagg(kod, langs_vaggen(kod, p), z)


def _bjalklag(a: str, b: str) -> tuple[Vek, ...]:
    """Ned från dosan a till bjälklaget, i elrörens nivå (först längs x, sedan y) och upp till dosan b."""
    ua, ub = upp_ur_bjalklaget(_P[a]), upp_ur_bjalklaget(_P[b])
    z = BJALKLAG["MB"]
    return ua[1], ua[0], (ub[0][0], ua[0][1], z), ub[0], ub[1]


_Z_HOG = 2300.0                                  # köksbänkens rör över fönstren (uttagen ovanför dem)
_Y = {k: _P[k].lage.punkt[1] for k in ("KO-U8", "KO-U9")}
_X10 = _P["KO-U10"].lage.punkt[0]
_HORN = (_i_ytterväggen("3NV", 0.0, 0.0)[0], _i_ytterväggen("3SV", 0.0, 0.0)[1])
_Z_BANK = _P["KO-U9"].lage.punkt[2]
_d01 = upp_ur_bjalklaget(_P["AL-B2"])
_Y_FLAKT = kok.Y_HALL - 230.0                    # bredvid köksfläktens kanal genom innertaket
_vid_flakten = vid_tak("3NV", langs_vaggen("3NV", (0.0, _Y_FLAKT, 0.0)))

ROR = [
    _tak("G01", 1, "HA-B1", "VR-B1", ((400.0, 10850.0),)),          # runt takfönstret TF3
    _rakt("G01", 2, "VR-B1", "VR-B2"),
    _rakt("G02", 1, "AL-B1", "AL-B2"),
    Ror("G02-R2", FXP16, "AL-B2", "BL-D01",
        via=(_d01[1], _d01[0], (_d01[0][0], D01[1], BJALKLAG["MB"]), (D01[0], D01[1], BJALKLAG["MB"]))),
    _tak("G02", 3, "AL-B1", "GA-B1"),
    _rakt("G02", 4, "GA-B1", "KO-B1"),
    _rakt("G02", 5, "KO-B1", "KO-B2"),
    _tak("G03", 1, "SV-B1", "SV-U1"),
    _tak("G03", 2, "SV-B1", "KT-B1"),
    _tak("G04", 1, "GR-B1", "KL-B1"),
    _rakt("G04", 2, "KL-B1", "SL-B1"),
    _tak("G04", 3, "GR-B1", "GR-U1"),
    _rakt("G04", 4, "GR-U1", "KL-U1"),
    _tak("G04", 5, "KL-U1", "SL-U1"),
    _tak("G05", 1, "BA-B1", "BA-D2"),
    _tak("G06", 1, "HA-U1", "VR-U1"),
    _tak("G06", 2, "VR-U1", "VR-U2", ((1393.0, 12450.0),)),        # förbi brandvarnaren BV-VR (y 12 700)
    _rakt("G06", 3, "VR-U2", "VR-U3"),
    _tak("G06", 4, "HA-U1", "AL-U1"),
    _rakt("G06", 5, "AL-U1", "AL-U2"),
    _tak("G07", 1, "BA-U1", "BA-D1", ((2300.0, 6900.0),)),          # längs L9 och L11 i badrummets tak
    # köksbänken: upp över fönstren till uttagen ovanför dem och ned till bänkens uttag, runt hörnet i bänkens höjd
    Ror("G12-R1", FXP16, "KO-U8", "KO-U1", via=(_i_ytterväggen("3NV", _Y["KO-U8"], _Z_HOG),)),
    _rakt("G12", 2, "KO-U1", "KO-U2"),
    Ror("G12-R3", FXP16, "KO-U2", "KO-U9", via=(_i_ytterväggen("3NV", _Y["KO-U9"], _Z_HOG),)),
    Ror("G12-R4", FXP16, "KO-U9", "KO-U10", via=((*_HORN, _Z_BANK),)),
    Ror("G12-R5", FXP16, "KO-U10", "KO-U3", via=(_i_ytterväggen("3SV", _X10, _Z_HOG),)),
    Ror("G13-R1", FXP16, "KO-U11", "KO-U12", via=_bjalklag("KO-U11", "KO-U12")),
    _rakt("G15", 1, "KO-U4", "KO-U5"),
    # köksfläktens uttag inne i skorstenskåpan: ned i 3NV bredvid kanalen och i installationsskiktet till uttaget
    Ror("G15-R2", FXP16, "KO-U5", "KO-U13",
        via=(*via_taket(_P["KO-U5"].lage, _P["KO-U13"].lage)[:2], *_vid_flakten[::-1],
             _i_ytterväggen("3NV", _Y_FLAKT, _P["KO-U13"].lage.punkt[2]))),
]
