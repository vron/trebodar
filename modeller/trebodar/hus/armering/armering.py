"""Armeringen i betongen enligt konstruktionsritningarna: mellanbjälklaget (R-06), källarväggarna (R-05) och
bottenplattan (R-04). Järnens lägen i plan och längder läses ur ritningarnas egna funktioner, de som ritar järnen och
räknar stålförteckningarna, så att modellen och ritningarna har samma källa; här får järnen höjd och blir stänger
(bockade järn av raka bitar, bockradierna förenklade bort). Lika järn är samma del.

Höjder: R-04 och R-05 räknar från bottenplattans överkant (z −2 250), R-06 från mellanbjälklagets underkant
(z −150). Järn i samma lager och riktning ligger i ett plan; där ritningen inte anger ordningen ligger x-led ytterst.
Där modellen avviker från ritningarna, eftersom de inte är uppdaterade (modell-todo): startjärnen under F3:s
bröstning (800) kortas till under bröstningens järn och ett startjärn närmare än 40 mm utanför en öppnings kant
flyttas ut till 40 mm. Mellanbjälklagets järn slutar vid plattan på marks fria kanter vid L-elementens rygg (AR-02),
som på R-06.
Kontrollen prövar inte armering mot betong eller mot annan armering (kontrollregler.IGNORERADE), men mot allt annat,
t.ex. rör och kanaler genom betongen.
"""
from __future__ import annotations

import importlib.util
import math
from functools import cache
from pathlib import Path
from types import ModuleType
from typing import Any, Sequence

import numpy as np
from shapely.geometry import LineString, Point, Polygon

from modellering import Del, Montage, Placering, Union, cylinder

from trebodar import skelett as S
from trebodar.hus.grund.grund import markplatta
from trebodar.material import ARMERING

ROT = Path(__file__).resolve().parents[4]
Z_BP = S.Z_BOTTENPLATTA                  # R-04 och R-05: z 0
Z_MB = -S.H_BJALKLAG                     # R-06: z 0

Punkt = tuple[float, float, float]
Jarn = tuple[str, list[Punkt], float]    # (position, polylinje, Ø)
_DELAR: dict[tuple[Any, ...], Del] = {}


@cache
def ritning(nr: str) -> ModuleType:
    """Konstruktionsritningens modul, beräkningar/<nr>/ritningar.py (läses, ritningen kompileras inte)."""
    fil = ROT / "beräkningar" / nr / "ritningar.py"
    spec = importlib.util.spec_from_file_location(f"ritning_{nr.replace('-', '_')}", fil)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _jarn(punkter: Sequence[Punkt], d: float) -> tuple[Del, Placering]:
    """Järnet Ø d längs polylinjen (i ett plan), som del i ett eget system med x längs den första sträckan, så att lika
    järn blir samma del, och delens placering."""
    P = np.array(punkter, dtype=float)
    e1 = (P[1] - P[0]) / np.linalg.norm(P[1] - P[0])
    n = next((c / np.linalg.norm(c) for c in (np.cross(e1, q - P[0]) for q in P[2:]) if np.linalg.norm(c) > 1e-6),
             None)
    if n is None:                                            # rakt järn
        ref = np.array([0.0, 0.0, 1.0]) if abs(e1[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
        n = np.cross(e1, ref) / np.linalg.norm(np.cross(e1, ref))
    e2 = np.cross(n, e1)
    lok = [(round(float((p - P[0]) @ e1), 1), round(float((p - P[0]) @ e2), 1)) for p in P]
    nyckel = (d, tuple(lok))
    if nyckel not in _DELAR:
        bitar = [cylinder(d / 2, math.dist(a, b)).placerad(
            Placering.axlar((a[0], a[1], 0.0), (0.0, 0.0, 1.0), (b[0] - a[0], b[1] - a[1], 0.0)))
            for a, b in zip(lok, lok[1:]) if math.dist(a, b) > 0.5]
        L = sum(math.dist(a, b) for a, b in zip(lok, lok[1:]))
        namn = f"Armering Ø{d:g} L={L:.0f}" + ("" if len(lok) == 2 else " bockad")
        _DELAR[nyckel] = Del(namn, bitar[0] if len(bitar) == 1 else Union(tuple(bitar)), ARMERING)
    r0, r1, r2 = ((float(e1[i]), float(e2[i]), float(n[i])) for i in range(3))
    return _DELAR[nyckel], Placering((r0, r1, r2), (float(P[0][0]), float(P[0][1]), float(P[0][2])))


def _montage(namn: str, kod: str, beskrivning: str, jarn: list[Jarn]) -> Montage:
    """Järnen som delar, numrerade per position."""
    m = Montage(namn, beskrivning=beskrivning)
    nr: dict[str, int] = {}
    for pos, pl, d in jarn:
        nr[pos] = nr.get(pos, 0) + 1
        del_, plac = _jarn(pl, d)
        m.lagg(del_, plac, f"{kod}-{pos}-{nr[pos]:03d}")
    return m


def _linje(seg: Any, z: float) -> list[Punkt]:
    (x0, y0), (x1, y1) = seg.coords[0], seg.coords[-1]
    return [(x0, y0, z), (x1, y1, z)]


def _klippt(pos: str, pl: list[Punkt], d: float, yta: Polygon) -> list[Jarn]:
    """Det raka vågräta järnet klippt till ytan (en eller flera bitar)."""
    g = LineString([p[:2] for p in pl]).intersection(yta)
    return [(pos, _linje(q, pl[0][2]), d) for q in getattr(g, "geoms", [g]) if q.geom_type == "LineString"
            and q.length > 50.0]


# ------------------------------------------------------------------ mellanbjälklaget (R-06)

def mellanbjalklag() -> Montage:
    r6 = ritning("R-06")
    return _montage("Mellanbjälklag", "MBA", f"Mellanbjälklagets armering (R-06): nät Ø{r6.DU} s{r6.SU} i underkant "
                    f"och Ø{r6.DO} s{r6.SO} i överkant, järn över rören, zoner, diagonaljärn och vinkeljärn",
                    list(_mellanbjalklagets_jarn()))


@cache
def _mellanbjalklagets_jarn() -> tuple[Jarn, ...]:
    r6 = ritning("R-06")

    def z(y: float) -> float:
        return Z_MB + y
    jarn: list[Jarn] = []
    # näten: underkant pos 1 (x) och 2 (y), överkant pos 11 (x) och 12 (y)
    for pos, d, sc, rikt, y in ((1, r6.DU, r6.SU, "x", r6.YU1), (2, r6.DU, r6.SU, "y", r6.YU2),
                                (11, r6.DO, r6.SO, "x", r6.YO1), (12, r6.DO, r6.SO, "y", r6.YO2)):
        jarn += [(f"A{pos}", _linje(seg, z(y)), d) for seg in r6.natjarn(sc, rikt)]
    # 2 + 2 Ø10 över rören i underkant (pos 3), i nätets lager i samma riktning
    for p0, p1, _ in r6.pos3_jarn():
        y = r6.YU1 if abs(p1[1] - p0[1]) < 1.0 else r6.YU2
        jarn.append(("A3", [(p0[0], p0[1], z(y)), (p1[0], p1[1], z(y))], 10))
    # zonernas tilläggsjärn i överkant (Ö1 …)
    for zn in r6.R["zoner"]:
        _, jj = r6.zonjarn(zn)
        for rikt, y in (("x", r6.YO1), ("y", r6.YO2)):
            jarn += [(zn["namn"], _linje(seg, z(y)), zn["tillagg"][0]) for seg in jj[rikt]]
    jarn += _mellanlagret()
    yta = _betongen()
    return tuple(j for pos, pl, d in jarn for j in ((_klippt(pos, pl, d, yta)) if pos != "A14" else [(pos, pl, d)]))


def _betongen() -> Polygon:
    """Mellanbjälklagets betong (vid plattan på marks fria kanter till L-elementens rygg, som på R-06) minus
    täckskiktet."""
    return Polygon(S.KONTUR, [S.TRAPPHAL]).difference(markplatta()[2]).buffer(-ritning("R-06").C_KANT, join_style=2)


def _mellanlagret() -> list[Jarn]:
    """Järnen mellan mellanbjälklagets nät: diagonaljärnen vid trapphålet (pos 13) och vinkeljärnen från
    ytterväggarnas kärna (pos 14), båda under överkantsnätet."""
    r6, r5 = ritning("R-06"), ritning("R-05")
    K = r5.K
    jarn: list[Jarn] = []
    # diagonaljärn i överkant (pos 13), under överkantsnätet
    diag, _ = r6.diagonaljarn()
    zd = Z_MB + r6.YO2 - r6.DO / 2 - 5.0
    jarn += [("A13", [(p0[0], p0[1], zd), (p1[0], p1[1], zd)], 10) for p0, p1 in diag]
    # vinkeljärn från ytterväggarnas kärna (pos 14): ben ned i väggen vid de lodräta järnen och in i bjälklaget under
    # överkantsnätet, med väggens lodräta järns avstånd
    p14 = r6.POS14
    zh = Z_BP + r5.Z_POS14
    for w in r5.V:
        if w["ute"] is None:
            continue
        s14 = r6.S14.get(w["namn"], p14["s"])
        t0 = w["mot_a"]["c"] + K.T_KARNA / 2 + 50.0 if w["mot_a"] else w["a"] + 40.0
        t1 = w["mot_b"]["c"] - K.T_KARNA / 2 - 50.0 if w["mot_b"] else w["b"] - 40.0
        q = w["ytterliv"] - w["ute"] * K.X_LODRAT
        for t in r5.fordela(t0, t1, s14):
            ned = (t, q) if w["ax"] == "h" else (q, t)
            inn = (t, q - w["ute"] * p14["in_"]) if w["ax"] == "h" else (q - w["ute"] * p14["in_"], t)
            jarn.append(("A14", [(ned[0], ned[1], zh - p14["ben"]), (ned[0], ned[1], zh), (inn[0], inn[1], zh)],
                         p14["d"]))
    return jarn


def bottenplattans_mellanrum() -> tuple[float, float]:
    """Utrymmet mellan bottenplattans armeringsnät (z), där golvvärmens rör gjuts in: underkantsnätets överkant och
    överkantsnätets underkant (R-04)."""
    r4 = ritning("R-04")
    return Z_BP - r4.HP + r4.C_UK + 2 * r4.NAT[0], Z_BP - r4.C_OK - 2 * r4.NAT[0]


def mellanbjalklagets_mellanrum() -> tuple[float, float]:
    """Utrymmet mellan mellanbjälklagets armeringsnät (z), där installationernas rör gjuts in: underkantsnätets
    överkant och överkantsnätets underkant (R-06)."""
    r6 = ritning("R-06")
    return Z_MB + r6.C_UK + 2 * r6.DU, Z_MB + r6.H - r6.C_OK - 2 * r6.DO


@cache
def jarnen_i_nivan(z0: float, z1: float) -> tuple[tuple[Point | LineString, float], ...]:
    """Järnen som går genom höjdintervallet z0–z1 (t.ex. ett ingjutet rör), i plan: lodräta järn som punkter, vågräta
    och lutande som linjer (delen inom intervallet), med Ø."""
    ut: dict[tuple[Any, ...], tuple[Point | LineString, float]] = {}
    for _, pl, d in (*_mellanbjalklagets_jarn(), *_kallarvaggarnas_jarn(), *_bottenplattans_jarn()):
        for a, b in zip(pl, pl[1:]):
            lo, hi = min(a[2], b[2]) - d / 2, max(a[2], b[2]) + d / 2
            if hi <= z0 or lo >= z1:
                continue
            ta, tb = 0.0, 1.0
            if abs(b[2] - a[2]) > 1e-6:                      # delen inom intervallet (järnets mitt ± Ø/2)
                ta, tb = sorted(((z0 - d / 2 - a[2]) / (b[2] - a[2]), (z1 + d / 2 - a[2]) / (b[2] - a[2])))
                ta, tb = max(ta, 0.0), min(tb, 1.0)
            p, q = ((round(a[0] + (b[0] - a[0]) * t, 1), round(a[1] + (b[1] - a[1]) * t, 1)) for t in (ta, tb))
            g: Point | LineString = Point(p) if math.dist(p, q) < 1.0 else LineString([p, q])
            ut[(*sorted((p, q)), d)] = (g, d)
    return tuple(ut.values())


# ------------------------------------------------------------------ källarväggarna (R-05)

def kallarvaggar() -> Montage:
    d_h = ritning("R-05").K.ARM_H[0]
    return _montage("Källarväggar", "KVA", f"Källarväggarnas armering (R-05): vågräta järn Ø{d_h}, vinkeljärn i hörn "
                    "och anslutningar, lodräta järn Ø10 och öppningarnas järn Ø12", list(_kallarvaggarnas_jarn()))


@cache
def _kallarvaggarnas_jarn() -> tuple[Jarn, ...]:
    r5 = ritning("R-05")
    K = r5.K

    def plan(w: dict[str, Any], t: float, q: float) -> tuple[float, float]:
        return (t, q) if w["ax"] == "h" else (q, t)

    def lager(namn: str) -> tuple[float, ...]:
        return tuple(K.Z_HOR_V3) if namn == "V3" else tuple(K.Z_HOR)
    jarn: list[Jarn] = []
    d_h = K.ARM_H[0]
    # vågräta raka järn (21, V3: 24) på båda ytorna i varje lager, och vinkeljärn i hörn (23) och anslutningar (25)
    for w in r5.V:
        pos = r5.POS["v3"] if w["namn"] == "V3" else r5.POS["hor"]
        for sida, t0, t1 in r5.raka(w):
            q = r5.jarnlinje(w, sida)
            jarn += [(f"A{pos}", [(*plan(w, t0, q), Z_BP + zz), (*plan(w, t1, q), Z_BP + zz)], d_h)
                     for zz in lager(w["namn"])]
    for pos, pl, n in r5.hornjarn():
        zs = K.Z_HOR_V3 if n == len(K.Z_HOR_V3) else K.Z_HOR
        jarn += [(f"A{pos}", [(x, y, Z_BP + zz) for x, y in pl], d_h) for zz in zs[:n]]
    # under bröstningarna är väggen hel: de vågräta järnen under bröstningen skarvas förbi öppningen (inom raden)
    for e in r5.ELEV:
        xa, xb = r5.karna_langs(e)
        for o in r5.oppningar_langs(e):
            if o["z0"] <= 0:
                continue
            w = r5.VAGG[o["vaggar"][0]]
            a, b = max(o["x0"] - 30.0 - K.SKARV, xa + 30.0), min(o["x1"] + 30.0 + K.SKARV, xb - 30.0)
            for sida in (1, -1):
                q = r5.jarnlinje(w, sida)
                jarn += [(f"A{r5.POS['hor']}", [(*plan(w, a, q), Z_BP + zz), (*plan(w, b, q), Z_BP + zz)], d_h)
                         for zz in lager(w["namn"]) if zz < o["z0"] - 40.0]
    # lodräta järn (22) upp under mellanbjälklagets överkantsnät, under bröstningarna (28) upp till bröstningens järn
    for w in r5.V:
        jarn += [(f"A{r5.POS['lod']}", [(x, y, Z_BP + 20.0), (x, y, Z_BP + K.L_LODRAT)], 10) for x, y in r5.lodrata(w)]
    for o in r5.OPPN:
        if o["typ"] != "yttre" or o["z0"] <= 0:
            continue
        w = r5.VAGG[o["vaggar"][0]]
        q = w["ytterliv"] - w["ute"] * K.X_LODRAT
        jarn += [(f"A{r5.POS['lod_under']}", [(*plan(w, t, q), Z_BP + 20.0), (*plan(w, t, q), Z_BP + o["z0"] - 40.0)],
                  10) for t in r5.lodrata_under(o)]
    # öppningarnas järn: 2 Ø12 vid sidorna (26) och under bröstningen (27)
    d_o = K.OPP["d"]
    for o in r5.OPPN:
        za, zb = r5.oppning_z(o)
        jarn += [(f"A{r5.POS['opp_sida']}", [(x, y, Z_BP + za + 20.0), (x, y, Z_BP + zb)], d_o)
                 for x, y in r5.oppningsjarn_plan(o)]
    for e in r5.ELEV:
        oppn = r5.oppningar_langs(e)
        xa, xb = r5.karna_langs(e)
        w = r5.VAGG[e["vaggar"][0]]
        for zz, a, b, _, _ in r5.brostningsjarn(oppn, xa, xb):
            for sida in (1, -1):
                q = r5.jarnlinje(w, sida) - sida * 11.0
                jarn.append((f"A{r5.POS['opp_under']}", [(*plan(w, a, q), Z_BP + zz), (*plan(w, b, q), Z_BP + zz)],
                             d_o))
    return tuple(jarn)


# ------------------------------------------------------------------ bottenplattan (R-04)

def bottenplatta() -> Montage:
    r4 = ritning("R-04")
    return _montage("Bottenplatta", "BPA", f"Bottenplattans armering (R-04): nät Ø{r4.NAT[0]} s{r4.NAT[1]} i båda "
                    "lagren, balkarnas järn och byglar, plintarnas järn, diagonaljärn och startjärn",
                    list(_bottenplattans_jarn()))


@cache
def _bottenplattans_jarn() -> tuple[Jarn, ...]:
    r4 = ritning("R-04")
    K, R4 = r4.K, r4.R4
    d_n = r4.NAT[0]
    jarn: list[Jarn] = []
    # näten Ø6 s150 i under- och överkant, hela plattan (även i balkar och plintar)
    z_uk, z_ok = R4.Z_NAT_UK, -25.0 - d_n / 2
    for pos, rikt, zz in ((r4.POS["uk_x"], "x", z_uk), (r4.POS["uk_y"], "y", z_uk + d_n),
                          (r4.POS["ok_x"], "x", z_ok), (r4.POS["ok_y"], "y", z_ok - d_n)):
        jarn += [(f"A{pos}", _linje(seg, Z_BP + zz), d_n) for seg in r4.natjarn(rikt)]
    # balkarnas längsjärn: 2 i underkant (35) och 2 i överkant (36), byglar Ø6 s600 (37)
    for pl in r4.balkjarn():
        for pos, zz in ((r4.POS["balk_uk"], R4.Z_BALK_UK), (r4.POS["balk_ok"], R4.Z_BALK_OK)):
            jarn.append((f"A{pos}", [(x, y, Z_BP + zz) for x, y in pl], r4.BALK_ARM["uk"][1]))
    d_b, s_b = r4.BALK_ARM["bygel"]
    halv = r4.BB / 2 - K.BYGEL_SIDA
    z0, z1 = Z_BP + R4.Z_BYGEL, Z_BP - 25.0 - d_b / 2
    kant = list(r4.BETONG.buffer(-r4.BB / 2, join_style=2).exterior.coords)
    inre = [((a[0] + c[0]) / 2, (a[1] + c[1]) / 2, (b[0] + e[0]) / 2, (b[1] + e[1]) / 2)
            for (a, b), (c, e) in zip(r4.balkjarn()[2::2], r4.balkjarn()[3::2])]
    linjer = [(*p, *q) for p, q in zip(kant, kant[1:])] + inre
    for x0, y0, x1, y1 in linjer:
        L = math.hypot(x1 - x0, y1 - y0)
        ux, uy = (x1 - x0) / L, (y1 - y0) / L
        for t in np.arange(s_b / 2, L - s_b / 4, s_b):
            cx, cy = x0 + ux * t, y0 + uy * t
            a, b = (cx - uy * halv, cy + ux * halv), (cx + uy * halv, cy - ux * halv)
            jarn.append((f"A{r4.POS['bygel']}", [(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1),
                                                  (a[0], a[1], z1), (a[0], a[1], z0)], d_b))
    # plintarnas järn Ø8 s150 i underkant (38)
    d_p = r4.PLINT_ARM[0]
    for r in K.ROR:
        linjer_p, _ = r4.plintjarn(r)
        for (p, q) in linjer_p:
            zz = -R4.HB + 30.0 + d_p / 2 + (d_p if abs(p[0] - q[0]) < 1.0 else 0.0)     # x-led ytterst
            jarn.append((f"A{r4.POS['plint']}", [(p[0], p[1], Z_BP + zz), (q[0], q[1], Z_BP + zz)], d_p))
    # diagonaljärn i överkant vid de inåtgående hörnen (39), under överkantsnätet
    zd = Z_BP + z_ok - d_n - d_n / 2 - r4.DIAG["d"] / 2
    jarn += [(f"A{r4.POS['diag']}", [(p[0], p[1], zd), (q[0], q[1], zd)], r4.DIAG["d"]) for p, q in r4.diagonaljarn()]
    # startjärn Ø10 till väggarna (40 utsidan, 41 innerväggarna): fot längs balken på byglarna, in mot väggens mitt,
    # och lodrätt ben upp; under en lägre bröstning bara till under bröstningens järn
    zf = Z_BP + R4.Z_BALK_UK - 5.0
    for (x, y), typ, namn in r4.startjarn():
        w = R4.VAGG[namn]
        t = x if w["ax"] == "h" else y
        for o in R4.OPPN:                                    # inte vid öppningens kant: 40 mm in i kärnan
            if o["ax"] == w["ax"] and abs(o["c"] - w["c"]) < 1.0:
                if o["x1"] < t < o["x1"] + 40.0:
                    t = o["x1"] + 40.0
                elif o["x0"] - 40.0 < t < o["x0"]:
                    t = o["x0"] - 40.0
        x, y = (t, y) if w["ax"] == "h" else (x, t)
        inat = 1.0 if (w["a"] + w["b"]) / 2 > t else -1.0
        fx, fy = (x + inat * r4.FOT_START, y) if w["ax"] == "h" else (x, y + inat * r4.FOT_START)
        upp = float(r4.START["upp"])
        for o in R4.OPPN:
            if 0 < o["z0"] and o["ax"] == w["ax"] and abs(o["c"] - w["c"]) < 1.0 and o["x0"] <= t <= o["x1"]:
                upp = min(upp, o["z0"] - 40.0 - K.OPP["d"] / 2 - r4.START["d"] / 2 - 10.0)
        pos = r4.POS["start_ute"] if typ == "ute" else r4.POS["start_inne"]
        jarn.append((f"A{pos}", [(fx, fy, zf), (x, y, zf), (x, y, Z_BP + upp)], r4.START["d"]))
    return tuple(jarn)


def montage() -> Montage:
    m = Montage("Armering", beskrivning="Armeringen i betongen enligt R-04, R-05 och R-06")
    m.lagg(bottenplatta())
    m.lagg(kallarvaggar())
    m.lagg(mellanbjalklag())
    return m
