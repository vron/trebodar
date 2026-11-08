"""Rören mellan gruppernas punkter på plan 1 (#50, #51): gruppens rör från centralen kommer till dess första punkt
(bjalklag/mellanbjalklag.py), och därifrån går ett rör till varje följande punkt i gruppen (grupper.py), förgrenat i
apparatdosorna. Vägarna (dragning.py):

- mellan dosor på olika väggar upp i väggen, i innertakets installationsskikt och ned i den andra väggen;
- mellan dosor intill varandra eller på samma vägg och höjd rakt i väggen (regelfacket eller installationsskiktet);
- köksbänkens uttag i ytterväggens installationsskikt, under och över fönstren och runt hörnet mellan 3NV och 3SV;
- öns uttag och brandlarmets matningsdosa genom mellanbjälklaget, raka och sneda med mjuka böjar runt
  grupprören och deras stigare (bjalklag/ingjutna.py).

Får ett rör genom innertaket (här och i rummens moduler) mer än BOJAR_MAX böjar delas det i en dragdosa i innertaket
(katalog.DRAGDOSA_TAK, #87):
i den brytpunkt i installationsskiktet där böjarna delas jämnast, mitt i läktens fack, och vid behov igen; dosorna
heter efter rummet vid den närmaste änden (t.ex. BA-DD1) och rörens delar a, b, c … i ordning.
"""
from __future__ import annotations

import math
from dataclasses import replace

from ..montering import BJALKLAG, Vek, i_tak, i_vagg, langs_taket, langs_vaggen, tak, vid_tak
from . import lakt
from .dragning import upp_till_dosan, via_taket
from .katalog import DRAGDOSA_TAK, FXP16
from .punkter import Dosa, Punkt, Ror, anslutning, bojar
from .rum import allrum, badrum, gang, gastrum, hall, kok, kontor, kontor_litet, sovrum, sovrum_litet, vardagsrum
from .bjalklag import mellanbjalklag as MB
from .bjalklag.ingjutna import Ingjutning
from .bjalklag.mellanbjalklag import PUNKTER as MB_PUNKTER

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


_ING = Ingjutning(MB.STIGARE, (), MB.ROR)


def _genom_bjalklaget(rid: str, a: str, b: str) -> Ror:
    """Röret från dosan a ned i bjälklaget, där raka och sneda (bjalklag/ingjutna.py) och upp i dosan b (eller till en
    punkt i källarens tak)."""
    ua = upp_till_dosan(_P[a])
    if b in _P and _P[b].lage.ref != "MB":
        ub = upp_till_dosan(_P[b])
        return _ING.dra(rid, FXP16, a, b, ua[0][:2], ub[0][:2], fore=ua[1:][::-1], efter=ub[1:])
    m = _P[b].lage.punkt
    ro = _ING.dra(rid, FXP16, a, b, ua[0][:2], (m[0], m[1]), fore=ua[1:][::-1])
    r = FXP16.ytterdiameter / 2                  # och rakt ned i källarens tak: en stigare genom den undre nivån
    _ING.stigare.append((m[0], m[1], r, m[2], ro.via[-1][2] + r))
    return ro


_Z_HOG = 2300.0                                  # köksbänkens rör över fönstren (uttagen ovanför dem)
_Y = {k: _P[k].lage.punkt[1] for k in ("KO-U8", "KO-U9")}
_X10 = _P["KO-U10"].lage.punkt[0]
_HORN = (_i_ytterväggen("3NV", 0.0, 0.0)[0], _i_ytterväggen("3SV", 0.0, 0.0)[1])
_Z_BANK = _P["KO-U9"].lage.punkt[2]
_Y_FLAKT = kok.Y_HALL - 230.0                    # bredvid köksfläktens kanal genom innertaket
_vid_flakten = vid_tak("3NV", langs_vaggen("3NV", (0.0, _Y_FLAKT, 0.0)))

ROR = [
    _tak("G01", 1, "HA-B1", "VR-B1", ((400.0, 10850.0),)),          # runt takfönstret TF3
    _rakt("G01", 2, "VR-B1", "VR-B2"),
    _rakt("G02", 1, "AL-B1", "AL-B2"),
    _genom_bjalklaget("G02-R2", "AL-B2", "BL-D01"),
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
    _genom_bjalklaget("G13-R1", "KO-U11", "KO-U12"),
    _rakt("G15", 1, "KO-U4", "KO-U5"),
    # köksfläktens uttag inne i skorstenskåpan: ned i 3NV bredvid kanalen och i installationsskiktet till uttaget
    Ror("G15-R2", FXP16, "KO-U5", "KO-U13",
        via=(*via_taket(_P["KO-U5"].lage, _P["KO-U13"].lage)[:2], *_vid_flakten[::-1],
             _i_ytterväggen("3NV", _Y_FLAKT, _P["KO-U13"].lage.punkt[2]))),
]
BOJAR_MAX = 270.0
SAMMA = 150.0                   # en dragdosa så nära en annan blir samma
LANG = 1500.0                   # och på så långa sträckor i skiktet kan den sitta mitt på


PUNKTER: list[Dosa] = []


def _utan_dubbla(pts: list[Vek]) -> tuple[Vek, ...]:
    """Brytpunkterna mellan ändarna, utan punkter som ligger på den föregående (eller på änden)."""
    ut = [pts[0]]
    for q in pts[1:]:
        if math.dist(q, ut[-1]) > 1.0:
            ut.append(q)
        elif q is pts[-1]:
            ut[-1] = q
    return tuple(ut[1:-1])


def _med_dragdosa(r: Ror) -> list[Ror]:
    """Röret r, eller i två delar genom en dragdosa i innertaket där böjarna delas jämnast (inga över BOJAR_MAX)."""
    if r.fran not in _P or r.till not in _P:
        return [r]
    grund = [anslutning(_P[r.fran], ut=True), *r.via, anslutning(_P[r.till])]
    pts = grund[:1]                                     # över nocken och dalarna i installationsskiktet
    for a, b in zip(grund, grund[1:]):
        for q in langs_taket(a, b)[1:]:
            p0 = pts[-1]
            if math.dist(p0, q) > LANG and abs(q[2] - p0[2]) < 0.9 * math.dist(p0, q):     # mitt på långa sträckor
                pts.append(tuple((x + y) / 2 for x, y in zip(p0, q)))                       # type: ignore[arg-type]
            pts.append(q)
    if bojar(pts) <= BOJAR_MAX:
        return [r]
    bast = None
    dragdosa = {d.id for d in PUNKTER}
    k0 = 1 if r.fran in dragdosa else 2                 # brytpunkterna i installationsskiktet (inte väggarnas)
    k1 = len(pts) - (1 if r.till in dragdosa else 2)
    for k in range(k0, k1):
        x, y, z = pts[k]
        try:
            m = tak(x, y)
        except ValueError:
            continue
        if abs(m.punkt[2] - z) > 120.0:
            continue
        xd = lakt.mellan_lakten(m.ref, x, y)            # mitt i läktens fack
        finns = next((d for d in PUNKTER if math.dist(d.lage.punkt[:2], (xd, y)) < SAMMA), None)  # två rör i en dosa
        if finns is not None and finns.id in (r.fran, r.till):
            continue
        delning = max(bojar(pts[:k + 1]), bojar(pts[k:]))
        if bast is None or delning < bast[0]:
            bast = (delning, k, xd, y, finns)
    if bast is None:
        return [r]
    _, k, x, y, finns = bast
    if finns is not None:
        did = finns.id
    else:                                               # i rummet vid den närmaste änden (förteckningen per rum)
        rum = min((r.fran, r.till), key=lambda q: math.dist(anslutning(_P[q])[:2], (x, y))).split("-")[0]
        did = f"{rum}-DD{sum(1 for p in PUNKTER if p.id.startswith(rum + '-DD')) + 1}"
        PUNKTER.append(Dosa(did, DRAGDOSA_TAK, tak(x, y)))
        _P[did] = PUNKTER[-1]
    ansl = anslutning(_P[did])
    delar = [replace(r, till=did, via=_utan_dubbla([pts[0], *pts[1:k], ansl])),
             replace(r, fran=did, via=_utan_dubbla([ansl, *pts[k + 1:-1], pts[-1]]))]
    return [d for del_ in delar for d in _med_dragdosa(del_)]


def _delad(r: Ror) -> list[Ror]:
    """Röret r, eller dess delar genom dragdosorna i ordning: a, b, c …"""
    delar = _med_dragdosa(r)
    if len(delar) == 1:
        return delar
    return [replace(d, id=f"{r.id}{chr(ord('a') + i)}") for i, d in enumerate(delar)]


ROR = [d for r in ROR for d in _delad(r)]
for _m in (allrum, badrum, gang, gastrum, hall, kok, kontor, kontor_litet, sovrum, sovrum_litet, vardagsrum):
    _m.ROR[:] = [d for r in _m.ROR for d in _delad(r)]      # rummens rör genom innertaket likaså
# stigarna genom bjälklaget (grupprörens och kedjornas), som hinder för källarens rör
STIGARE = _ING.stigare
