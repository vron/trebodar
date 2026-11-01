"""Takbalkarna 45×170 C24 c/c 600 (K-03), ett montage per takfall med takfönstrens avväxlingar och kortlingar.

Takbalkarnas lägen (y) är Onshape-modellens, med en extra takbalk vid TF1:s övre sida (dubbel som vid de andra
fönstren). Profilerna följer reglerna i byggdelar/takbalk.py. Varje takbalk går från nockbalken till dalbalken där
en sådan finns i takbalkens läge, annars till takfoten.
"""
from __future__ import annotations

from dataclasses import dataclass

from modellering import Montage

from trebodar import skelett as S
from trebodar.byggdelar import takbalk as T
from trebodar.byggdelar.regelvagg import Plan


@dataclass(frozen=True)
class Takfonster:
    kod: str
    y0: float                # öppningen mellan takbalkarna
    y1: float
    x_ned: float             # öppningens nedre och övre kant i takplanet (x)
    x_upp: float


@dataclass(frozen=True)
class Falt:
    kod: str
    nock: str                # nockbalken
    dal: str | None          # dalbalken mot takfallets nedre kant, där den finns
    takfot: float            # takbalkarnas ände vid takfoten (x), 70 mm utanför fasaden
    y: tuple[float, ...]     # takbalkarnas lägen (lägsta y)
    fonster: tuple[Takfonster, ...] = ()


TF1 = Takfonster("TF1", 5540.0, 6740.0, 561.784, 1601.014)
TF2 = Takfonster("TF2", 7505.0, 8705.0, 10151.784, 11191.014)
TF3 = Takfonster("TF3", 9539.0, 10739.0, 561.784, 1601.014)

_C600 = lambda a, b: tuple(float(v) for v in range(a, b + 1, 600))          # noqa: E731
FALT = {f.kod: f for f in (
    Falt("1SO", "NB5", None, -165.0,
         (4205, 4805, 5450, 5495, 6740, 6785, 7049, 7649, 8249, 8849, 9449, 9494, 10739, 10784)
         + _C600(11640, 15240), (TF1, TF3)),
    Falt("1NV", "NB5", "DB4", 4475.0, _C600(4205, 10805) + _C600(11640, 15240)),
    Falt("2SO", "NB3", "DB4", 4335.0, _C600(615, 5415) + _C600(6550, 10150)),
    Falt("2NV", "NB3", "DB2", 9475.0, _C600(615, 5415) + _C600(6550, 10150)),
    Falt("3SO", "NB1", "DB2", 9335.0, _C600(1615, 7015) + (7415, 7460, 8705, 8750, 9350, 9950, 10550, 11395, 11850),
         (TF2,)),
    Falt("3NV", "NB1", None, 13975.0, _C600(1615, 11815)),
)}


def _sida(balk: str, t: S.Takfall) -> float:
    """Balkens sida mot takfallet."""
    b = S.BALKAR[balk]
    # takfallet ligger på den sida där planet sjunker bort från balken
    return b.x - S.BALK_B / 2 if t.riktning > 0 and b.typ == "nock" or t.riktning < 0 and b.typ == "dal" \
        else b.x + S.BALK_B / 2


def falt(f: Falt) -> Montage:
    t = S.TAKFALL[f.kod]
    m = Plan(f.kod, f"Takfall {f.kod}", 45.0, beskrivning=f"Takbalkar 45×170 C24, {S.HUSKROPPAR[t.kropp].namn}")
    ovre = T.Ande("balk", _sida(f.nock, t), f.nock)
    dal = S.BALKAR[f.dal] if f.dal else None
    pa_balk: dict[str, list[float]] = {f.nock: []}
    for y in f.y:
        if dal and dal.y0 <= y and y + 45 <= dal.y1:
            nedre = T.Ande("balk", _sida(dal.kod, t), dal.kod)
            pa_balk.setdefault(dal.kod, []).append(y)
        else:
            nedre = T.Ande("takfot", f.takfot)
        pa_balk[f.nock].append(y)
        m.profil(T.profil(t, nedre, ovre), y, y + 45, typ="T")
    for fo in f.fonster:
        # avväxlingar mellan de dubbla takbalkarna, nedanför och ovanför öppningen
        m.profil(T.avvaxling(t, fo.x_ned, True), fo.y0, fo.y1, typ="A", namn=f"{fo.kod}-A1")
        m.profil(T.avvaxling(t, fo.x_upp, False), fo.y0, fo.y1, typ="A", namn=f"{fo.kod}-A2")
        # kortlingar i öppningens mitt: nedåt till dalbalken eller takfoten, uppåt till nockbalken
        ym = 0.5 * (fo.y0 + fo.y1) - 22.5
        x_ned = T.langs(t, fo.x_ned, -45.0)
        x_upp = T.langs(t, fo.x_upp, 45.0)
        if dal and dal.y0 <= ym and ym + 45 <= dal.y1:
            fot = T.Ande("balk", _sida(dal.kod, t), dal.kod)
            pa_balk.setdefault(dal.kod, []).append(ym)
        else:
            fot = T.Ande("takfot", f.takfot)
        pa_balk[f.nock].append(ym)
        m.profil(T.profil(t, fot, T.Ande("vinkelrat", x_ned)), ym, ym + 45, typ="K", namn=f"{fo.kod}-K1")
        m.profil(T.profil(t, T.Ande("vinkelrat", x_upp), ovre), ym, ym + 45, typ="K", namn=f"{fo.kod}-K2")
    # upplagsreglar 45×45 på balkarnas sidor under takbalkarna; regeln delas där avståndet mellan takbalkarna är
    # större än 700 mm (takstolen 2C står där)
    for kod, ys in pa_balk.items():
        b = S.BALKAR[kod]
        xs = _sida(kod, t)
        utat = 1 if (xs > b.x) else -1
        zr = T.regel_ok(t, kod, xs, utat)
        x0, x1 = sorted((xs, xs + utat * T.UPPLAG_B))
        ys = sorted(ys)
        bitar = [[ys[0]]]
        for y in ys[1:]:
            (bitar[-1].append(y) if y - bitar[-1][-1] <= 700 else bitar.append([y]))
        for i, bit in enumerate(bitar, 1):
            m.lada("R", x0, x1, bit[0], bit[-1] + 45, zr - T.UPPLAG_B, zr, "w",
                   namn=f"{f.kod}-UR-{kod}" + (f"-{i}" if len(bitar) > 1 else ""))
    return m.montage()


def montage() -> Montage:
    m = Montage("Takbalkar", beskrivning="Takbalkar 45×170 C24 c/c 600 med takfönstrens avväxlingar (K-03)")
    for f in FALT.values():
        m.lagg(falt(f))
    return m
