"""Tappvattnets beståndsdelar och hur rören dras.

- Tappställen (Tappstalle): det som förbrukar vatten, med typ (normflöden), anslutning (dosa), montering på en yta
  (montering.py: vagg, golv, kallarvagg) och rörtyp. Kallvattnet ansluter till höger och varmvattnet till vänster sett
  mot dosan.
- Fördelare (Fordelare): kallvattnets och varmvattnets stammar i fördelarskåpet, med utgångar uppåt i rörens filer;
  utgång 0 och utgången efter den sista är stammens ändar (inlopp och genomgång).
- Rör (Ror): från en fördelares utgång ("FD-KV:3"), en utrustning i teknikrummet ("TK-VP:VV-ut") eller ett tappställe
  till ett annat, med media (KV, VV) och brytpunkter. Rör-i-rör från fördelaren till varje tappställe (stjärnsystem:
  läckor syns i fördelarskåpet).
- Stråk (..strak.Strak): gemensamma vägar ingjutna i mellanbjälklaget, alla rör i en nivå närmast underkantsnätet
  (golvvärmen går ovanför), en fil per rör c/c 50 som armeringsnätens maskor: kallt och varmt bredvid varandra. Röret
  följer filen till punkten närmast tappstället (på stråkets ben `ben`, om det anges) och går därifrån dit
  (..strak.vag): upp ur bjälklaget i väggens regelfack eller golvdosan på plan 1, eller ned ur bjälklaget i
  källarväggens cellplast bakom gipsen till väggdosan i källaren.
- Där rören går upp eller ned genom bjälklaget går de mellan armeringsjärnen: golvdosan flyttas så lite som behövs,
  och rören i väggen flyttas längs väggen och går därifrån vågrätt till väggdosan (`forskjutning`).
- Tappställen med hylsor (dosans slag "hylsa", ärende #83) har inga rör i bjälklaget: kopparrören går från
  underfördelarens utgångar rakt upp till under källarens tak (Z_TAKET), där först tvärs och sedan längs till under
  sin hylsa och rakt upp genom den till anslutningen ovanför golvet. Hylsan (en per rör) står mellan
  armeringsjärnen, flyttad längs `kallt` (eller åt alla håll) så lite som behövs (`hylsa`).

Koordinater i mm (K-05), z från plan 1:s golv.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from shapely.geometry import box
from shapely.ops import unary_union

from trebodar import skelett as S
from trebodar.hus.grund.kallarvaggar import CELL

from ..genomforingar import vaggarna
from ..montering import I_BETONGEN, KALLARTAK, PLAN, Montering, Vek, flytt, i_vaggen
from ..strak import Strak, mellan_jarnen, vag
from .typer import Dosatyp, Fordelartyp, Rortyp, Tappstalletyp

R_ROR = 14.0                            # största skyddsrörets radie (rör-i-rör 18/28)
FIL = 50.0                              # rörens avstånd i stråken (c/c), som armeringsnätens maskor (s150)
Z_ROR = I_BETONGEN["vatten"]            # i mellanbjälklaget, närmast underkantsnätet
Z_TAKET = {"VV": KALLARTAK - 40.0, "KV": KALLARTAK - 80.0}     # kopparrören under källarens tak, varmvattnet överst
HYLSA_TVARS = 10.0                      # hylsan flyttas högst så långt tvärs `kallt`

Via = tuple[float | None, float | None]


@dataclass(frozen=True)
class Rum:
    kod: str                    # två bokstäver, början på tappställenas id (t.ex. "BA")
    namn: str
    plan: int                   # 1 (plan 1) eller 0 (källaren)


@dataclass(frozen=True)
class Tappstalle:
    """Ett tappställe: dosans mitt på ytan (normalen ut i rummet), rörtypen från fördelarna, för golvdosor riktningen
    från varmvattnet till kallvattnet (standard x) och punkter i plan som rören går förbi efter stråket (via, per
    media eller för båda; None i en koordinat: anslutningens). En underfördelares inlopp (underfordelare.py) har
    rörens ändar i anslutningar: stammarnas början per media, rakt under där rören kommer ned ur bjälklaget; ett
    tappställe med hylsor kopparrörens ändar ovanför golvet (hylsorna rakt under dem, flyttade längs kallt)."""
    id: str
    typ: Tappstalletyp
    dosa: Dosatyp
    lage: Montering
    ror: Rortyp
    kallt: Vek | None = None
    via: Via | dict[str, Via] | None = None
    anslutningar: tuple[tuple[str, Vek], ...] = ()


@dataclass(frozen=True)
class Fordelare:
    """Kallvattnets eller varmvattnets fördelare längs riktning: utgångarna i filerna `filer` (filen 0 i lage, c/c
    FIL), utgång n i filen filer[n − 1]; ändarna en fil före den första och efter den sista."""
    id: str
    typ: Fordelartyp
    media: str                  # "KV" eller "VV"
    lage: Vek
    riktning: Vek
    filer: tuple[int, ...]

    @property
    def utgangar(self) -> int:
        return len(self.filer)

    def utgang(self, n: int) -> Vek:
        """Utgång n (0 och utgangar + 1: stammens ändar)."""
        fil = -1 if n == 0 else max(self.filer) + 1 if n == self.utgangar + 1 else self.filer[n - 1]
        return flytt(self.lage, self.riktning, fil * FIL)


@dataclass(frozen=True)
class Ror:
    """Rör från fran till till genom brytpunkterna via: fördelarens utgång ("FD-KV:3"), utrustning
    ("TK-VP:KV-in") eller tappställe ("BA-DU1")."""
    id: str
    typ: Rortyp
    media: str                  # "KV" eller "VV"
    fran: str
    till: str
    via: tuple[Vek, ...] = ()


def _anslutning(t: Tappstalle, media: str) -> Vek:
    if t.anslutningar:
        return dict(t.anslutningar)[media]
    m, d = t.lage, t.dosa
    n = m.normal
    hoger = (-n[1], n[0], 0.0) if d.slag != "golv" else (t.kallt or (1.0, 0.0, 0.0))
    p = flytt(m.punkt, n, -d.djup / 2 if d.slag == "vägg" else d.djup / 2)
    return flytt(p, hoger, (d.cc / 2) * (1 if media == "KV" else -1)) if d.cc else p


def forskjutning(t: Tappstalle) -> tuple[float, float]:
    """Där rören går upp eller ned genom bjälklaget ska de gå mellan armeringsjärnen: golvdosans förskjutning (åt
    alla håll) eller rörens i väggen (längs väggen, upp ur bjälklaget på plan 1 eller ned ur det i källarväggen, och
    tvärs den inom regelfacket eller cellplasten); (0, 0) om de redan går fria."""
    if t.id not in _FORSKJUTNING:
        _FORSKJUTNING[t.id] = _forskjutning(t)
    return _FORSKJUTNING[t.id]


_FORSKJUTNING: dict[str, tuple[float, float]] = {}
INIFRAN = (60.0, 120.0, 180.0, 240.0, 300.0)   # rörets väg in till en yttervägg, prövad mot järnen


def _forskjutning(t: Tappstalle) -> tuple[float, float]:
    medier = [m for m, q in (("KV", t.typ.kv), ("VV", t.typ.vv)) if q > 0]
    r = t.ror.yttre / 2
    if t.dosa.slag == "golv":                                   # dosan fri från väggarna (deras lådor)
        k = t.kallt or (1.0, 0.0, 0.0)
        hx, hy = (t.dosa.b / 2, t.dosa.h / 2) if abs(k[0]) > 0.5 else (t.dosa.h / 2, t.dosa.b / 2)
        vaggar = unary_union([box(a - hx - 5.0, b - hy - 5.0, c + hx + 5.0, d + hy + 5.0)
                              for a, b, c, d in (hel.bounds for hel, _, _, _ in vaggarna().values())])
        return mellan_jarnen([_anslutning(t, m)[:2] for m in medier], Z_ROR, PLAN[1], r, undvik=vaggar)
    if t.dosa.slag != "vägg":                                    # utanpå; underfördelarna står mellan järnen
        return 0.0, 0.0
    n = t.lage.normal
    plan1 = t.lage.punkt[2] > PLAN[1] - 1.0
    z = (Z_ROR, PLAN[1]) if plan1 else (KALLARTAK, Z_ROR)
    facket = vaggarna()[t.lage.ref][2] if plan1 else CELL                 # regelfacket eller cellplasten
    tvars = facket / 2 - r - 2.0
    punkter = [i_vaggen(t.lage, _anslutning(t, m))[:2] for m in medier]
    langs = (-n[1], n[0])
    if not (plan1 and t.lage.ref in S.YTTERVAGGAR):
        return mellan_jarnen(punkter, *z, r, langs=langs, tvars=tvars)
    # en yttervägg: rören kommer in från rummet i sin nivå genom bandet vid kanten (vinkeljärnen och källarväggens
    # lodräta järn, #97) och går upp i väggen; båda ska gå fria, så förskjutningen prövas om tills de gör det
    inifran = [(x + n[0] * d, y + n[1] * d) for x, y in punkter for d in INIFRAN]

    def tvars_fri(pts: list[tuple[float, float]], z0: float, z1: float, tv: float) -> tuple[float, float] | None:
        """Förskjutningen tvärs väggen (högst tv) som gör punkterna fria, eller None."""
        try:
            return mellan_jarnen(pts, z0, z1, r, langs=langs, tvars=tv, langst=0.0)
        except ValueError:
            return None
    for steg in sorted(range(-40, 41), key=abs):                   # 5 mm steg, högst 200 mm åt var håll
        dx, dy = langs[0] * 5.0 * steg, langs[1] * 5.0 * steg
        upp = tvars_fri([(x + dx, y + dy) for x, y in punkter], *z, tvars)
        if upp is None:
            continue
        dx, dy = dx + upp[0], dy + upp[1]
        if tvars_fri([(x + dx, y + dy) for x, y in inifran], Z_ROR - r, Z_ROR + r, 0.0) == (0.0, 0.0):
            return dx, dy
    raise ValueError(f"{t.id}: inget läge mellan järnen för rören in i {t.lage.ref}")


def anslutning(t: Tappstalle, media: str) -> Vek:
    """Rörets ände vid tappstället: dosans mitt bakom ytan (väggdosa) eller på ytan (golvdosan förskjuten mellan
    järnen); kallvattnet till höger och varmvattnet till vänster sett mot dosan, cc isär. Med hylsor: kopparrörets
    ände rakt över sin hylsa."""
    a = _anslutning(t, media)
    if t.dosa.slag == "hylsa":
        x, y = hylsa(t, media)
        return (x, y, a[2])
    if t.dosa.slag != "golv":
        return a
    dx, dy = forskjutning(t)
    return (a[0] + dx, a[1] + dy, a[2])


def hylsa(t: Tappstalle, media: str) -> tuple[float, float]:
    """Hylsans mitt i plan för mediets rör: under rörets ände, flyttad längs `kallt` (högst HYLSA_TVARS tvärs) eller
    åt alla håll så lite som behövs för att gå fri från järnen genom hela bjälklaget."""
    if (t.id, media) not in _HYLSOR:
        a = _anslutning(t, media)
        k = t.kallt
        dx, dy = mellan_jarnen([a[:2]], KALLARTAK, PLAN[1], t.dosa.b / 2, langs=(k[0], k[1]) if k else None,
                               tvars=HYLSA_TVARS if k else 0.0)
        _HYLSOR[(t.id, media)] = (a[0] + dx, a[1] + dy)
    return _HYLSOR[(t.id, media)]


_HYLSOR: dict[tuple[str, str], tuple[float, float]] = {}


def till_tappstallet(t: Tappstalle, media: str) -> tuple[tuple[tuple[float, float], ...], tuple[Vek, ...]]:
    """Rörets väg från stråket till tappstället: punkterna i plan (via och punkten lodrätt under eller över
    anslutningen, för väggdosor inne i väggen, förskjuten längs väggen mellan järnen) och därifrån upp eller ned i
    väggen och vågrätt till dosan."""
    a = anslutning(t, media)
    slut: tuple[Vek, ...] = ()
    if t.dosa.slag == "fördelare":                              # rakt ned ur bjälklaget till stammens början
        slut = (a,)
    elif t.dosa.slag == "vägg":
        i = i_vaggen(t.lage, a)
        dx, dy = forskjutning(t)
        n = t.lage.normal
        tv = dx * n[0] + dy * n[1]                                 # förskjutningen tvärs väggen
        a = (i[0] + dx, i[1] + dy, i[2])
        e = (i[0] + n[0] * tv, i[1] + n[1] * tv, i[2])            # längs väggen till dosan, sedan tvärs
        slut = tuple(q for j, q in enumerate((a, e, i)) if j == 0 or math.dist(q, (a, e, i)[j - 1]) > 0.5)
    genom: tuple[tuple[float, float], ...] = ((a[0], a[1]),)
    via = t.via.get(media) if isinstance(t.via, dict) else t.via
    if via:
        genom = ((a[0] if via[0] is None else via[0], a[1] if via[1] is None else via[1]), *genom)
    return genom, slut


def ror_hylsa(t: Tappstalle, utgang: dict[str, int], fordelare: dict[str, Fordelare]) -> list[Ror]:
    """Kopparrören till ett tappställe med hylsor från underfördelarens utgångar (per media): rakt upp till under
    källarens tak (Z_TAKET), där först i x och sedan i y till under hylsan, och rakt upp genom den till änden."""
    ut = []
    for media in ("VV", "KV"):
        if media in utgang:
            fd = fordelare[media]
            u, a, z = fd.utgang(utgang[media]), anslutning(t, media), Z_TAKET[media]
            via: list[Vek] = []
            for q in ((u[0], u[1], z), (a[0], u[1], z), (a[0], a[1], z)):
                if not via or math.dist(q, via[-1]) > 0.5:
                    via.append(q)
            ut.append(Ror(f"{t.id}-{media}", t.ror, media, f"{fd.id}:{utgang[media]}", t.id, tuple(via)))
    return ut


def ror(t: Tappstalle, utgang: dict[str, int], strak: Strak, fordelare: dict[str, Fordelare],
        ben: int | None = None) -> list[Ror]:
    """Rören till tappstället från fördelarnas utgångar (per media), längs filerna i stråket: varmt och kallt, det
    som tappstället har."""
    ut = []
    for media in ("VV", "KV"):
        if media in utgang:
            fd = fordelare[media]
            genom, slut = till_tappstallet(t, media)
            ut.append(Ror(f"{t.id}-{media}", t.ror, media, f"{fd.id}:{utgang[media]}", t.id,
                          vag(fd.utgang(utgang[media]), Z_ROR, strak, genom, slut, ben)))
    return ut
