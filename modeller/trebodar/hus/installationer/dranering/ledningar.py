"""Dräneringen och dagvattnet (ärende #25): dränering runt grunden och dagvatten från stuprören, i separata ledningar
till en ny brunn utanför källarväggen V9, nära den gamla (som låg i väggen), ansluten till det befintliga utgående
röret Ø110 mot nordost (mot rampen in på tomten mellan boden och planteringen; överkant +5,759, AR-02).

Dräneringen: dränrör Ø110 i en ring AVSTAND["dränering"] utanför grundens ytterkant (källarväggarna och plattan på
mark), med överkanten i grundens underkant (UK: källaren och plattan på mark), så att den dränerar det kapillärbrytande
skiktet. Dagvattnet: täta rör Ø110 i en ring AVSTAND["dagvatten"] utanför grunden, TACKNING under marken vid
fasaden (markniva.MARKNIVA), och från varje stuprör en anslutning (lövsil vid stuprörets ände, lodrätt ned och en
sticka till ringen). Ringarna delas i punkten längst från brunnen i två grenar som faller mot den (FALL, minst),
i raka lutningar mellan brytpunkterna; där grundens eller markens nivå faller fortare faller ledningen med den,
brantare än 1:1 lodrätt i en spolbrunn (dräneringen mellan plattan på mark och källaren, dagvattnet där marken
sluttar). Under stenarna i marken (HINDER, entréavsatsen och sovrumsavsatsen) går ledningarna under stenarnas
underkant, utan spolbrunnar. Spolrör vid grenarnas början. Brunnen: Ø400 med sandfång under utloppet, locket i
marken.

Höjderna i modellens z (mm), rörens underkant; på ritningen vattengången (VG, + GODS) i RH 2000 (z / 1000 +
skelett.PLATS.hojd).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from functools import cache

import numpy as np
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import substring, unary_union

from trebodar import skelett as S
from trebodar.hus.fasad.markniva import mark_vid
from trebodar.hus.grund import grund as G
from trebodar.hus.grund import kallarvaggar as K
from trebodar.hus.tak import dalar, takkanter

D = 110.0                                            # rörens ytterdiameter
GODS = 3.4                                           # rörens gods: vattengången (insidans botten) är underkant + GODS
FALL = {"dränering": 1 / 200, "dagvatten": 1 / 100}   # minsta fall mot brunnen
AVSTAND = {"dränering": 300.0, "dagvatten": 600.0}    # ringarna utanför grundens ytterkant
TACKNING = 300.0                                     # dagvattnet under marken
UK = {"källaren": S.Z_BOTTENPLATTA - 300.0,          # bottenplattan: betong 100 och kantbalk 200 på cellplast
      "plattan": -G.H_L_MARK - G.T_MAKADAM}          # plattan på mark: L-element 500 och makadam 150
_V9 = next(v for v in K.VAGGAR if v.namn == "V9")
BRUNN = (11250.0, _V9.c - K.KARNA / 2 - K.CELL - 450.0)    # nya brunnens mitt: 450 utanför V9, vid den gamla
BRUNN_D, SANDFANG = 400.0, 300.0                     # brunnens diameter och sandfånget under utloppet
UTLOPP_OK = 5.759                                    # utgående rörets överkant vid brunnen [m RH 2000]
UTLOPP_RIKTNING = (0.064, -0.998)                    # mot nordost (passningen mot SWEREF, vyer.sweref_passning)
UTLOPP_L = 3000.0                                    # så långt det ritas; röret finns och fortsätter
STEG = 250.0                                         # ringarnas punkter för höjderna
# stenarna i marken som ledningarna går under (mark/mark.py: entréavsatsens block E-*, sovrumsavsatsen ur
# Onshape-modellen): område (x0, y0, x1, y1) och underkant. Under dem inga spolbrunnar och inga lodräta fall; en
# ändring syns i ./mod dranering kontroll (krockar med Natursten)
HINDER = {"entréavsatsen": ((-1595.0, 8355.0, -95.0, 11255.0), -1100.0),
          "sovrumsavsatsen": ((-77.0, 62.0, 4400.0, 3490.0), -1844.0)}
UNDER_HINDER = 50.0                                  # rörens överkant under stenarnas underkant
HINDER_KANT = 150.0                                  # schaktet utanför stenarnas kant
DJUPARE = {"dränering": 50.0, "dagvatten": 200.0}    # så mycket raka lutningar får gå under den högsta vattengången


def rh(z: float) -> float:
    """Modellens z (mm) i RH 2000 (m)."""
    return z / 1000 + S.PLATS.hojd


Z_UTLOPP = (UTLOPP_OK - S.PLATS.hojd) * 1000 - D     # utloppets vattengång vid brunnen


@dataclass(frozen=True)
class Ledning:
    id: str
    typ: str                                         # "dränering", "dagvatten", "anslutning", "spolrör", "utlopp"
    vag: tuple[tuple[float, float, float], ...]      # vattengången (x, y, z) i brytpunkterna
    beskrivning: str = ""


@dataclass(frozen=True)
class Brunn:
    id: str
    x: float
    y: float
    d: float
    z_botten: float
    z_lock: float
    beskrivning: str


@cache
def grunden() -> tuple[Polygon, Polygon]:
    """Grundens ytterkant: källarväggarnas (cellplastens utsida) och plattan på marks (L-elementens utsida)."""
    return K.ytterkontur(), Polygon(G.MARK_PLATTA).difference(K.ytterkontur())


@cache
def ring(typ: str) -> LineString:
    """Ringen runt grunden, moturs."""
    kallare, platta = grunden()
    yta = unary_union([kallare, platta]).buffer(1.0, join_style=2).buffer(AVSTAND[typ] - 1.0, join_style=2)
    r = LineString(list(yta.exterior.coords)).simplify(40.0)              # utan små språng (källaren–plattan)
    if Polygon(r.coords).exterior.is_ccw is False:
        r = LineString(list(r.coords)[::-1])
    return r


def under_hinder(x: float, y: float) -> str | None:
    """Stenen (HINDER) som punkten ligger under, med schaktet utanför kanten."""
    k = HINDER_KANT
    return next((n for n, ((x0, y0, x1, y1), _) in HINDER.items() if x0 - k <= x <= x1 + k and y0 - k <= y <= y1 + k),
                None)


def _nedre(typ: str, x: float, y: float) -> float:
    """Den högsta vattengången i punkten: dräneringens överkant i grundens underkant (källaren eller plattan på
    mark, den närmaste), dagvattnets överkant TACKNING under marken vid den närmaste fasaden; under en sten
    (HINDER) UNDER_HINDER under dess underkant."""
    h = under_hinder(x, y)
    z_h = HINDER[h][1] - UNDER_HINDER - D if h else math.inf
    p = Point(x, y)
    if typ == "dränering":
        kallare, platta = grunden()
        return min(z_h, UK["plattan" if platta.distance(p) < kallare.exterior.distance(p) else "källaren"] - D)
    kod = min(S.YTTERVAGGAR, key=lambda k: LineString([S.YTTERVAGGAR[k].placering().punkt((0.0, 0.0, 0.0))[:2],
                                                        S.YTTERVAGGAR[k].placering().punkt(
                                                            (S.YTTERVAGGAR[k].langd, 0.0, 0.0))[:2]]).distance(p))
    u = S.YTTERVAGGAR[kod].placering().invers().punkt((x, y, 0.0))[0]
    return min(z_h, mark_vid(kod, u) - TACKNING - D)


def _bit(r: LineString, s0: float, langd: float, fram: bool) -> list[tuple[float, float]]:
    """Ringens punkter från s0, langd längs ringen framåt (växande s) eller bakåt, runt ringens början."""
    L = r.length
    tre = LineString(list(r.coords) + list(r.coords)[1:] + list(r.coords)[1:])
    b = substring(tre, s0 + L, s0 + L + langd) if fram else substring(tre, s0 + L - langd, s0 + L)
    pkt = [(float(x), float(y)) for x, y in b.coords]
    return pkt if fram else pkt[::-1]


def _tat(pkt: list[tuple[float, float]]) -> tuple[list[tuple[float, float]], list[int]]:
    """Punkterna med högst STEG mellan, och hörnens index bland dem."""
    ut, horn = [pkt[0]], [0]
    for a, b in zip(pkt, pkt[1:]):
        n = max(1, math.ceil(math.dist(a, b) / STEG))
        ut += [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(1, n + 1)]
        horn.append(len(ut) - 1)
    return ut, horn


def _hojder(typ: str, pkt: list[tuple[float, float]]) -> list[tuple[float, float, float]]:
    """Vattengången nedströms i brytpunkterna. Först så högt som möjligt: i början i _nedre, sedan minst FALL och
    aldrig över _nedre. Sedan i raka lutningar, så långa som möjligt mellan hörnen (rören läggs i raka längder),
    under _nedre och högst DJUPARE under den första (schaktet bredvid grunden blir inte djupare än det behöver;
    under stenarna fritt). En lutning brantare än 1:1 faller i stället lodrätt i sin början (i en spolbrunn) och
    sedan med FALL, utom under stenarna, där spolbrunnen inte går att nå."""
    tat, horn = _tat(pkt)
    tak = np.array([_nedre(typ, *p) for p in tat])
    fri = np.array([under_hinder(*p) is not None for p in tat])
    s = np.concatenate([[0.0], np.cumsum([math.dist(a, b) for a, b in zip(tat, tat[1:])])])
    z = [float(tak[0])]
    for i in range(1, len(tat)):
        z.append(min(z[-1] - FALL[typ] * (s[i] - s[i - 1]), float(tak[i])))
    golv = np.where(fri, -math.inf, np.array(z) - DJUPARE[typ])
    vag: list[tuple[float, float, float]] = [(*tat[0], z[0])]
    a, za = 0, z[0]
    while a < len(tat) - 1:
        nasta = next(h for h in horn if h > a)
        j = next(k for k in range(nasta, a, -1)
                 if z[k] <= za - FALL[typ] * (s[k] - s[a]) + 1e-6
                 and np.all((zk := za + (z[k] - za) * (s[a + 1:k] - s[a]) / (s[k] - s[a])) <= tak[a + 1:k] + 1.0)
                 and np.all(zk >= golv[a + 1:k]))
        if za - z[j] > s[j] - s[a] and not fri[a]:                  # brantare än 1:1: lodrätt, i en spolbrunn,
            za = z[j] + FALL[typ] * float(s[j] - s[a])              # och vidare därifrån
            vag.append((*tat[a], za))
            continue
        vag.append((*tat[j], z[j]))
        a, za = j, z[j]
    # bara brytpunkterna: där riktningen ändras
    ut = [vag[0]]
    for p0, p1, p2 in zip(vag, vag[1:], vag[2:]):
        u = (p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])
        v = (p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2])
        lu, lv = math.hypot(*u), math.hypot(*v)
        if lu < 1e-6 or lv < 1e-6:
            continue
        if sum(p * q for p, q in zip(u, v)) / (lu * lv) < 1.0 - 1e-6:
            ut.append(p1)
    ut.append(vag[-1])
    return ut


@cache
def ledningar() -> dict[str, Ledning]:
    ut: dict[str, Ledning] = {}
    bx, by = BRUNN
    for typ, pre in (("dränering", "D"), ("dagvatten", "S")):
        r = ring(typ)
        L = r.length
        sw = r.project(Point(BRUNN))
        avst = r.interpolate(sw).distance(Point(BRUNN))
        halv = math.sqrt(max((BRUNN_D / 2) ** 2 - avst ** 2, 0.0))        # där ringen går in i brunnen
        sf = (sw + L / 2) % L                                               # längst från brunnen
        for nr, fram, langd in ((1, True, (sw - halv - sf) % L), (2, False, (sf - sw - halv) % L)):
            vag = _hojder(typ, _bit(r, sf, langd, fram))
            namn = "dränering runt grunden" if typ == "dränering" else "dagvatten runt huset"
            ut[f"{pre}{nr}"] = Ledning(f"{pre}{nr}", typ, tuple(vag), f"{namn}, gren {nr}")
        ut[f"{pre}0"] = Ledning(f"{pre}0", "spolrör", ((*ut[f"{pre}1"].vag[0][:2], ut[f"{pre}1"].vag[0][2]),
                                                      (*ut[f"{pre}1"].vag[0][:2], _mark(*ut[f"{pre}1"].vag[0][:2]))),
                                f"spolrör där grenarna börjar ({typ})")
    # stuprörens anslutningar till dagvattnet: lodrätt från stuprörets ände och en sticka till ringen
    r = ring("dagvatten")
    for namn, x, y, z_ande, _ in takkanter.stupror() + dalar.stupror():
        q = r.interpolate(r.project(Point(x, y)))
        gren, z_r = _hojd_vid(ut, "S", q.x, q.y)
        lat = math.hypot(q.x - x, q.y - y)
        z_a = z_r + FALL["dagvatten"] * lat
        ut[f"A-{namn}"] = Ledning(f"A-{namn}", "anslutning", ((x, y, z_ande), (x, y, z_a), (q.x, q.y, z_r)),
                                  f"stupröret {namn} till dagvattnet ({gren})")
    # utloppet: befintligt rör mot nordost
    ux, uy = UTLOPP_RIKTNING
    a = (bx + ux * BRUNN_D / 2, by + uy * BRUNN_D / 2, Z_UTLOPP)
    b = (a[0] + ux * UTLOPP_L, a[1] + uy * UTLOPP_L, Z_UTLOPP - FALL["dagvatten"] * UTLOPP_L)
    ut["U"] = Ledning("U", "utlopp", (a, b), "befintligt utgående rör Ø110 mot nordost (fortsätter)")
    return ut


def _mark(x: float, y: float) -> float:
    """Marken vid den närmaste fasaden."""
    return _nedre("dagvatten", x, y) + TACKNING + D


def _hojd_vid(ut: dict[str, Ledning], pre: str, x: float, y: float) -> tuple[str, float]:
    """Grenen och vattengången där punkten (på ringen) ligger, interpolerad."""
    bast: tuple[float, str, float] = (math.inf, "", 0.0)
    for nr in (1, 2):
        vag = ut[f"{pre}{nr}"].vag
        for a, b in zip(vag, vag[1:]):
            seg = LineString([a[:2], b[:2]])
            dist = seg.distance(Point(x, y))
            if dist < bast[0]:
                t = seg.project(Point(x, y)) / seg.length if seg.length > 0 else 0.0
                bast = (dist, f"{pre}{nr}", a[2] + (b[2] - a[2]) * t)
    return bast[1], bast[2]


@cache
def brunnar() -> dict[str, Brunn]:
    """Den nya brunnen och spolbrunnarna där ledningarna faller lodrätt."""
    bx, by = BRUNN
    ut = {"B1": Brunn("B1", bx, by, BRUNN_D, Z_UTLOPP - SANDFANG, _mark(bx, by),
                      "dagvatten- och dräneringsbrunn Ø400 med sandfång, ansluten till det befintliga utgående röret")}
    n = 0
    for led in ledningar().values():
        if led.typ not in ("dränering", "dagvatten"):
            continue
        for a, b in zip(led.vag, led.vag[1:]):
            if math.hypot(b[0] - a[0], b[1] - a[1]) < 1.0 and a[2] - b[2] > 1.0:
                n += 1
                ut[f"SB{n}"] = Brunn(f"SB{n}", a[0], a[1], 200.0, b[2] - 100.0, _mark(a[0], a[1]),
                                     f"spolbrunn Ø200 ({led.id}: {led.typ} faller {a[2] - b[2]:.0f} mm)")
    return ut


def kontroll() -> tuple[list[str], list[str]]:
    """(fel, anmärkningar): fallet, att grenarna når brunnen över utloppet, täckningen och längderna."""
    fel: list[str] = []
    anm: list[str] = []
    for led in ledningar().values():
        if led.typ in ("dränering", "dagvatten"):
            for a, b in zip(led.vag, led.vag[1:]):
                lgd = math.hypot(b[0] - a[0], b[1] - a[1])
                if lgd > 1.0 and (a[2] - b[2]) / lgd < FALL[led.typ] - 1e-6:
                    fel.append(f"{led.id}: fall 1:{lgd / max(a[2] - b[2], 1e-6):.0f} vid ({a[0]:.0f}, {a[1]:.0f}), "
                               f"minst 1:{1 / FALL[led.typ]:.0f}")
            slut = led.vag[-1][2]
            if slut < Z_UTLOPP + 20.0:
                fel.append(f"{led.id}: når brunnen på +{rh(slut):.3f}, under utloppets +{rh(Z_UTLOPP):.3f}")
            langd = sum(math.dist(a, b) for a, b in zip(led.vag, led.vag[1:]))
            anm.append(f"{led.id} ({led.beskrivning}): {langd / 1000:.1f} m, VG från +{rh(led.vag[0][2] + GODS):.3f} "
                       f"till +{rh(slut + GODS):.3f}")
        elif led.typ == "anslutning":
            (x, y, z0), (_, _, z1), _ = led.vag
            if (h := under_hinder(x, y)) is not None:
                anm.append(f"{led.id}: stupröret står på {h}; anslutningen går lodrätt genom stenen (håltagning)")
            if z1 + D > _mark(x, y) - TACKNING + 1.0:
                anm.append(f"{led.id}: stickan ligger {(_mark(x, y) - z1 - D):.0f} mm under marken")
    for br in brunnar().values():
        if br.z_lock - br.z_botten < 300.0:
            fel.append(f"{br.id}: brunnen är bara {br.z_lock - br.z_botten:.0f} mm djup")
    return fel, anm


def utdrag() -> dict:
    """För ritningen och listan: ledningarna, brunnarna och höjderna (RH 2000)."""
    return {"ledningar": {k: {"typ": v.typ, "vag": [list(p) for p in v.vag], "beskrivning": v.beskrivning}
                          for k, v in ledningar().items()},
            "brunnar": {k: {"punkt": [b.x, b.y], "d": b.d, "botten": b.z_botten, "lock": b.z_lock,
                            "beskrivning": b.beskrivning} for k, b in brunnar().items()},
            "stupror": {n: [x, y, z] for n, x, y, z, _ in takkanter.stupror() + dalar.stupror()},
            "hinder": {n: [list(omr), uk] for n, (omr, uk) in HINDER.items()},
            "genom_sten": [k for k, v in ledningar().items() if v.typ == "anslutning" and under_hinder(*v.vag[0][:2])],
            "grund": {"källaren": list(grunden()[0].exterior.coords), "plattan": list(grunden()[1].exterior.coords)},
            "uk": UK, "rh0": S.PLATS.hojd * 1000, "d": D, "gods": GODS, "fall": FALL, "avstand": AVSTAND,
            "utlopp": Z_UTLOPP, "utlopp_ok": UTLOPP_OK, "tackning": TACKNING, "sandfang": SANDFANG}
