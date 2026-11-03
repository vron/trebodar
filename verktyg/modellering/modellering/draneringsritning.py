"""Dräneringens och dagvattnets ritning ur modellen (utdraget ur trebodar.hus.installationer.dranering.ledningar), i
ritningsmallen (A3): planen med ledningarna, brunnarna, stuprörens anslutningar och vattengångens höjder i
brytpunkterna (RH 2000), brunnen B1 i en större skala, och listan (markdown). Planen ur modellens snitt genom plan 1
(STEP-filen), med grundens ytterkant ur utdraget.
"""
from __future__ import annotations

import math
from collections.abc import Callable
from pathlib import Path

import numpy as np
from shapely.geometry import LineString, Point, Polygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import nearest_points, unary_union

from .planritning import Blad, Vy, blad, figur, kompilera, norrpil, papper, plan, plan_ytor, sv, vy

SERIE = "D-01 Dagvatten och dränering"
SKALA, DETALJ = 100.0, 20.0                       # planen och brunnen
PLANEN = (-3400.0, 16200.0, -3300.0, 17700.0)     # planens område (x0, x1, y0, y1) [mm]
BRUNNEN = (10450.0, 12050.0, -500.0, 1500.0)      # brunnens
MARK = ("Mark", "Fyllning", "Makadam", "Berg")    # materialen som ledningarna går i (inga krockar; berget redovisas)
STIL = {"dränering": "dr", "dagvatten": "dg", "anslutning": "dg_tunn", "utlopp": "dg", "spolrör": "dg_tunn"}
FARG = {"dränering": "dr", "dagvatten": "dg"}     # texternas färger (ritningsmallens FARG)
ROR = {"dränering": "#e3ecdc", "dagvatten": "#dce7f4"}   # rören i brunnens plan
SZ = 5.6                                          # höjdernas text [pt]
R_STUPROR, R_SPOL, R_SB = 1.0, 0.9, 1.2           # symbolernas mått på papperet [mm]

Pkt = tuple[float, float]


def bara_mark(krock: str, genom_sten: list[str]) -> bool:
    """Om en krock ur installationer.krockar ("element: genom Material n, …") bara gäller marken, som ledningarna
    går i, eller stenen som en stuprörsanslutning går lodrätt genom (utdragets genom_sten)."""
    element, _, mat = krock.partition(": genom ")
    tillatna = MARK + (("Natursten",) if element in genom_sten else ())
    return all(m.rsplit(" ", 1)[0] in tillatna for m in mat.split(", "))


def vg(u: dict, z: float) -> str:
    """Vattengången (rörets underkant z + godset) i RH 2000."""
    return "+" + sv((z + u["gods"] + u["rh0"]) / 1000, 3)


def rh(u: dict, z: float) -> str:
    return "+" + sv((z + u["rh0"]) / 1000, 3)


# ------------------------------------------------------------------ symboler (pappersmått)

def stupror(v: Vy, X: float, Y: float) -> None:
    v.cirkel(X, Y, R_STUPROR, fyll="vit", stil="dg_tunn")


def spolror(v: Vy, X: float, Y: float, stil: str = "dg_tunn") -> None:
    """Spolrör: cirkel med kryss."""
    v.cirkel(X, Y, R_SPOL, fyll="vit", stil=stil)
    k = v.m(R_SPOL) * math.sqrt(0.5)
    v.linje([(X - k, Y - k), (X + k, Y + k)], "tunn")
    v.linje([(X - k, Y + k), (X + k, Y - k)], "tunn")


def spolbrunn(v: Vy, X: float, Y: float) -> None:
    v.cirkel(X, Y, R_SB, fyll="vit", stil="normal")
    v.cirkel(X, Y, R_SB * 0.55, fyll=None, stil="tunn")


def brunn(v: Vy, X: float, Y: float, r: float) -> None:
    v.cirkel(X, Y, r, fyll="vit", stil="kontur")
    v.cirkel(X, Y, r * 0.4, fyll="svart", stil=None)


def flode(v: Vy, a: Pkt, b: Pkt, stil: str) -> None:
    """Flödets riktning: en pil mitt på sträckan a–b."""
    t = np.subtract(b, a) / math.dist(a, b)
    m = np.add(a, b) / 2 + t * v.m(0.9)
    v.pil(tuple(m), tuple(t), langd=1.8, bredd=1.1, fyll="#2f6db3" if stil.startswith("dg") else "#4f7d3a")


def _flodestecken(v: Vy) -> None:
    v.linje([(-3.5, 0.0), (3.5, 0.0)], "dg")
    flode(v, (-3.5, 0.0), (3.5, 0.0), "dg")


TECKEN: list[tuple[Callable[[Vy], None] | dict, str]] = [
    (dict(form="linje", stil="dr"), "dränrör Ø110, slitsat, i makadam med fiberduk"),
    (dict(form="linje", stil="dg"), "dagvattenrör Ø110, tätt"),
    (dict(form="linje", stil="dg_tunn"), "stuprörets anslutning, tätt rör Ø110"),
    (lambda w: _flodestecken(w), "flödets riktning, mot brunnen"),
    (lambda w: stupror(w, 0.0, 0.0), "stuprör med stuprörsanslutning (lövsil)"),
    (lambda w: brunn(w, 0.0, 0.0, 1.2), "brunn B1 Ø400 med sandfång"),
    (lambda w: spolbrunn(w, 0.0, 0.0), "spolbrunn Ø200, ledningen faller lodrätt"),
    (lambda w: spolror(w, 0.0, 0.0), "spolrör upp till marken"),
    (dict(form="linje", stil="dold"), "grundens ytterkant (källarväggarnas cellplast, plattan på mark)"),
]


def _teckenforklaring() -> dict:
    return dict(typ="symboler", rader=[{**s, "text": t} if isinstance(s, dict) else {**figur(s), "text": t}
                                       for s, t in TECKEN])


# ------------------------------------------------------------------ texterna i planen

class Texter:
    """Texterna med hänvisningslinje, utan att gå över varandra, ledningarna eller väggarna: varje text prövas i
    några lägen bort från huset och tar det första som är fritt."""

    def __init__(self, v: Vy, hinder: list[BaseGeometry], texter: list[BaseGeometry], ram: Polygon):
        self.v = v
        self.upptaget: list[BaseGeometry] = list(hinder) + list(texter)
        self.texter: list[BaseGeometry] = list(texter)      # texternas rutor: hänvisningslinjerna går inte över dem
        self.ram = ram                                       # texterna inom vyn

    def ruta(self, q: np.ndarray, d: np.ndarray, b: float, h: float) -> tuple[Polygon, str, float]:
        """Textens ruta (modellmått) vid hänvisningslinjens ände q i riktningen d, textens justering och x."""
        m = self.v.m
        if d[0] > 0.35:
            x0, x1, a, xt = q[0] + m(0.4), q[0] + m(0.4 + b), "l", q[0] + m(0.4)
        elif d[0] < -0.35:
            x0, x1, a, xt = q[0] - m(0.4 + b), q[0] - m(0.4), "r", q[0] - m(0.4)
        else:
            x0, x1, a, xt = q[0] - m(b / 2), q[0] + m(b / 2), "c", q[0]
        if abs(d[0]) > 0.35:
            y0, y1 = q[1] - m(h / 2), q[1] + m(h / 2)
        elif d[1] > 0:
            y0, y1 = q[1] + m(0.3), q[1] + m(0.3 + h)
        else:
            y0, y1 = q[1] - m(0.3 + h), q[1] - m(0.3)
        return Polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)]), a, xt

    def satt(self, p: Pkt, riktning: Pkt, rader: list[tuple[str, str]], sz: float = SZ, fran: Pkt | None = None,
             langder: tuple[float, ...] = (2.5, 4.5, 6.5, 9.0, 12.0, 15.0, 19.0)) -> None:
        """Raderna (text, färg) vid punkten p, med hänvisningslinje i riktningen (från punkten fran om den ges)."""
        v = self.v
        rad_h = sz * 0.3528 * 1.18
        b = max(len(t) for t, _ in rader) * sz * 0.3528 * 0.5 + 0.4
        h = len(rader) * rad_h + 0.2
        d0 = np.array(riktning, float) / math.hypot(*riktning)
        # det första läget utan krockar, annars det med minst
        val: tuple[int, np.ndarray, Polygon, str, float] | None = None
        for L in langder:
            for vrid in (0.0, 20.0, -20.0, 40.0, -40.0, 60.0, -60.0):
                c, s = math.cos(math.radians(vrid)), math.sin(math.radians(vrid))
                d = np.array([d0[0] * c - d0[1] * s, d0[0] * s + d0[1] * c])
                q = np.array(p) + d * v.m(L)
                r, a, xt = self.ruta(q, d, b, h)
                linje = LineString([fran or p, tuple(q)])
                krockar = (0 if self.ram.contains(r) else 100) + sum(r.intersects(u) for u in self.upptaget) + \
                    sum(linje.intersects(u) for u in self.texter)
                if val is None or krockar < val[0]:
                    val = (krockar, q, r, a, xt)
                if krockar == 0:
                    break
            if val is not None and val[0] == 0:
                break
        assert val is not None
        _, q, r, a, xt = val
        self.upptaget.append(r)
        self.texter.append(r)
        v.linje([fran or p, tuple(q)], "tunn")
        v.cirkel(*p, 0.3, fyll="svart", stil=None)
        if fran:
            v.cirkel(*fran, 0.3, fyll="svart", stil=None)
        y_topp = r.bounds[3] - v.m(0.1)
        for i, (t, col) in enumerate(rader):
            v.text(xt, y_topp - v.m(rad_h * (i + 0.5)), t, a=a + "m", sz=sz, col=col, bg=True)


def _ut(grund: BaseGeometry, p: Pkt) -> np.ndarray:
    """Riktningen bort från grunden i punkten."""
    n = np.subtract(p, nearest_points(grund, Point(p))[0].coords[0])
    return n / max(float(np.hypot(*n)), 1e-9)


def _brytpunkter(u: dict, lid: str) -> list[tuple[Pkt, list[float]]]:
    """Ledningens brytpunkter utom den sista (vid brunnen): punkten och vattengången, två där den faller lodrätt."""
    ut: list[tuple[Pkt, list[float]]] = []
    for p in u["ledningar"][lid]["vag"][:-1]:
        if ut and math.dist(ut[-1][0], p[:2]) < 1.0:
            ut[-1][1].append(p[2])
        else:
            ut.append(((p[0], p[1]), [p[2]]))
    return ut


# ------------------------------------------------------------------ planen

def _plan(u: dict, delar: list[dict], norr: tuple[float, float]) -> Vy:
    v = vy(SKALA, PLANEN, 24.0, 30.0)
    plan(v, delar)
    vaggar = unary_union([g for g, _, _ in plan_ytor(delar)])
    kallare, platta = Polygon(u["grund"]["källaren"]), Polygon(u["grund"]["plattan"])
    grund = unary_union([kallare, platta])
    with v.lager("grund"):
        for g in (kallare, platta):
            v.linje(list(g.exterior.coords), "dold")
    stentexter: list[BaseGeometry] = []
    with v.lager("stenar"):
        # stenarna i marken som ledningarna går under, med namnet i hörnet längst från grunden
        for namn, ((x0, y0, x1, y1), uk) in u["hinder"].items():
            v.polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], "#efede8", "fin")
            hx, hy = max(((x, y) for x in (x0, x1) for y in (y0, y1)), key=lambda q: grund.distance(Point(q)))
            sx, sy = (1.0 if hx == x0 else -1.0), (1.0 if hy == y0 else -1.0)
            txt = f"{namn}, underkant {rh(u, uk)}"
            tb, th = len(txt) * 5.4 * 0.3528 * 0.5, 5.4 * 0.3528 * 1.2
            if y1 - y0 > x1 - x0:                                # smal: längs den långa sidan, mitt på
                q = (hx + sx * v.m(0.8 + th), (y0 + y1) / 2)
                v.text(*q, txt, a="cb", sz=5.4, col="gra", i=True, rot=90)
                ruta = [(q[0] - sx * v.m(th), q[1] - v.m(tb / 2)), (q[0], q[1] - v.m(tb / 2)),
                        (q[0], q[1] + v.m(tb / 2)), (q[0] - sx * v.m(th), q[1] + v.m(tb / 2))]
            else:
                q = (hx + sx * v.m(0.8), hy + sy * v.m(0.8))
                v.text(*q, txt, a=("l" if sx > 0 else "r") + ("b" if sy > 0 else "t"), sz=5.4, col="gra", i=True)
                ruta = [q, (q[0] + sx * v.m(tb), q[1]), (q[0] + sx * v.m(tb), q[1] + sy * v.m(th)),
                        (q[0], q[1] + sy * v.m(th))]
            stentexter.append(Polygon(ruta))
    led = u["ledningar"]
    linjer: list[BaseGeometry] = []
    with v.lager("ledningar"):
        for lid, x in led.items():
            if x["typ"] == "spolrör":
                continue
            pkt = [(p[0], p[1]) for p in x["vag"]]
            pkt = [p for i, p in enumerate(pkt) if i == 0 or math.dist(p, pkt[i - 1]) > 1.0]
            v.linje(pkt, STIL[x["typ"]])
            linjer.append(LineString(pkt).buffer(v.m(0.5)))
            for a, b in zip(pkt, pkt[1:]):
                if math.dist(a, b) / v.s > 14.0 or (x["typ"] == "anslutning" and math.dist(a, b) / v.s > 3.5):
                    flode(v, a, b, STIL[x["typ"]])
        ut = led["U"]["vag"]
        v.pil(tuple(ut[-1][:2]), tuple(np.subtract(ut[-1][:2], ut[0][:2])), langd=2.6, bredd=1.6, fyll="#2f6db3")
    x0, y1 = papper(v, 22.0, 26.0)
    x1, y0 = papper(v, 228.0, 262.0)
    texter = Texter(v, [vaggar.buffer(-v.m(0.3)), grund.buffer(-v.m(0.6)), *linjer], stentexter,
                    Polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)]))
    symboler: list[BaseGeometry] = []
    with v.lager("symboler"):
        for n, (x, y, _) in u["stupror"].items():
            stupror(v, x, y)
            symboler.append(Point(x, y).buffer(v.m(R_STUPROR + 0.3)))
        for lid in ("D0", "S0"):
            p = led[lid]["vag"][0]
            spolror(v, p[0], p[1], "dr" if lid == "D0" else "dg_tunn")
            symboler.append(Point(p[:2]).buffer(v.m(R_SPOL + 0.3)))
        for bid, br in u["brunnar"].items():
            if bid == "B1":
                brunn(v, br["punkt"][0], br["punkt"][1], max(br["d"] / 2 / v.s, 1.6))
                symboler.append(Point(br["punkt"]).buffer(br["d"] / 2 + v.m(0.5)))
            else:
                spolbrunn(v, *br["punkt"])
                symboler.append(Point(br["punkt"]).buffer(v.m(R_SB + 0.3)))
    texter.upptaget += symboler
    sb = {(round(br["punkt"][0]), round(br["punkt"][1])): bid for bid, br in u["brunnar"].items() if bid != "B1"}

    def rad(typ: str, p: Pkt, z: list[float]) -> tuple[str, str]:
        t = " / ".join(vg(u, h) for h in z)
        b = sb.get((round(p[0]), round(p[1])))
        return (f"{b} {t}" if b else t), FARG[typ]

    with v.lager("höjder"):
        # dagvattnets brytpunkter, med dräneringens bredvid (på samma linje ut från grunden) i samma text
        dr = {lid: _brytpunkter(u, lid) for lid in ("D1", "D2")}
        dr_alla = {(round(p[0]), round(p[1])): (p, z) for b in dr.values() for p, z in b}
        anvanda: set[tuple[int, int]] = set()
        punkter: list[tuple[Pkt, list[tuple[Pkt, str, list[float]]]]] = []
        for lid in ("S1", "S2"):
            for p, z in _brytpunkter(u, lid):
                if any(math.dist(p, q) < 1.0 for q, _ in punkter):
                    continue
                d = _ut(grund, p)
                med: list[tuple[Pkt, str, list[float]]] = [(p, "dagvatten", z)]
                for k, (q, zq) in dr_alla.items():
                    if k in anvanda:
                        continue
                    w = np.subtract(p, q)
                    if np.hypot(*w) < 700.0 and abs(w[0] * d[1] - w[1] * d[0]) < 150.0 and np.dot(w, d) > 0:
                        med.append((q, "dränering", zq))
                        anvanda.add(k)
                        break
                punkter.append((p, med))
        for k, (q, zq) in dr_alla.items():
            if k not in anvanda:
                punkter.append((q, [(q, "dränering", zq)]))
        # de trängsta först (kortast till grannen), så att de får de bästa lägena
        def trangsel(e: tuple[Pkt, list]) -> float:
            return min((math.dist(e[0], f[0]) for f in punkter if f is not e), default=math.inf)
        for p, med in sorted(punkter, key=trangsel):
            ytterst = med[0][0]
            texter.satt(ytterst, tuple(_ut(grund, ytterst)), [rad(t, q, z) for q, t, z in med],
                        fran=med[-1][0] if len(med) > 1 else None)
        # stuprören och spolrören
        for n, (x, y, _) in u["stupror"].items():
            texter.satt((x, y), tuple(-_ut(grund, (x, y)) if grund.contains(Point(x, y)) else _ut(grund, (x, y))),
                        [(n, "dg")], sz=5.4)
        b1 = u["brunnar"]["B1"]
        texter.satt(tuple(b1["punkt"]), (-1.0, -0.6), [("B1 brunn Ø400, se brunnens plan", "ink"),
                                                       (f"lock {rh(u, b1['lock'])}", "ink")], sz=6.0,
                    langder=(8.0, 11.0, 14.0))
        e = ut[-1][:2]
        texter.satt(tuple(e), (1.0, 0.0), [
            ("befintligt utgående rör Ø110", "dg"), ("mot nordost (fortsätter), ÖK", "dg"),
            (f"+{sv(u['utlopp_ok'], 3)} vid brunnen (AR-02)", "dg")], sz=6.0, langder=(2.0, 4.0))
    norrpil(v, 14600.0, 16500.0, norr)
    v.rubrik(*papper(v, 24.0, 22.0), "Plan, dagvatten och dränering", round(v.s))
    with v.lager("skalstock"):
        v.skalstock(*papper(v, 24.0, 30.0 + (PLANEN[3] - PLANEN[2]) / v.s + 6.0), langd_m=5, steg_m=1)
    return v


def _brunnen(u: dict) -> Vy:
    """Brunnen B1 i plan i större skala, med rören in och ut och deras vattengång."""
    v = vy(DETALJ, BRUNNEN, 232.0, 40.0)
    b1 = u["brunnar"]["B1"]
    bx, by = b1["punkt"]
    d = u["d"]
    with v.lager("rör"):
        for lid in ("D1", "D2", "S1", "S2", "U"):
            x = u["ledningar"][lid]
            vag = x["vag"]
            a, b = (vag[-2], vag[-1]) if lid != "U" else (vag[1], vag[0])
            t = np.subtract(b[:2], a[:2]) / math.dist(b[:2], a[:2])
            n = np.array([-t[1], t[0]])
            slut = np.array(b[:2])
            borjan = slut - t * 650.0
            typ = "dagvatten" if x["typ"] == "utlopp" else x["typ"]
            v.polygon([tuple(borjan + n * d / 2), tuple(slut + n * d / 2), tuple(slut - n * d / 2),
                       tuple(borjan - n * d / 2)], ROR[typ], STIL[typ])
            z = b[2] if lid != "U" else vag[0][2]
            if lid == "U":
                v.ptext(*(borjan + t * 150), 3.6, 0.0, f"U ut VG {vg(u, z)}", a="lm", sz=6.6, col="dg", bg=True)
            else:
                # dräneringen ovanför sitt rör, dagvattnet under, vid den bortre änden
                ovan = typ == "dränering"
                kant = (borjan[0], borjan[1] + (d / 2 if ovan else -d / 2))
                v.ptext(*kant, 0.0, 0.8 if ovan else -0.8, f"{lid} VG {vg(u, z)}",
                        a=("l" if t[0] > 0 else "r") + ("b" if ovan else "t"), sz=6.6, col=FARG[typ], bg=True)
    with v.lager("brunn"):
        v.cirkel(bx, by, b1["d"] / 2 / v.s, fyll="vit", stil="kontur")
        v.cirkel(bx, by, (b1["d"] / 2 - 10.0) / v.s, fyll=None, stil="tunn")
        v.ptext(bx, by, 0.0, 0.0, "B1", a="cm", sz=7.5, b=True)
    v.rubrik(*papper(v, 232.0, 32.0), "Brunnen B1, plan", round(v.s))
    y = 40.0 + (BRUNNEN[3] - BRUNNEN[2]) / v.s + 4.0
    rader = [f"Brunn Ø400, lock {rh(u, b1['lock'])} (i marken)",
             f"Botten {rh(u, b1['botten'])}: sandfång {u['sandfang']:.0f} mm under utloppet",
             f"Rören Ø{u['d']:.0f} in över utloppet; VG = vattengång (rörets innerbotten)"]
    for i, t in enumerate(rader):
        v.text(*papper(v, 232.0, y + i * 3.4), t, a="lt", sz=6.8)
    return v


def _blad(u: dict, delar: list[dict], norr: tuple[float, float]) -> Blad:
    led = u["ledningar"]

    def langd(vag: list) -> float:
        return sum(math.dist(a, b) for a, b in zip(vag, vag[1:])) / 1000

    rader = [[k, "dränering" if x["typ"] == "dränering" else "dagvatten", sv(langd(x["vag"]), 1),
              vg(u, x["vag"][0][2]), vg(u, x["vag"][-1][2])] for k, x in led.items() if k in ("D1", "D2", "S1", "S2")]
    anslutningar = [[k[2:], x["beskrivning"].rsplit("(", 1)[-1].rstrip(")"), vg(u, x["vag"][1][2]),
                     vg(u, x["vag"][2][2])] for k, x in led.items() if x["typ"] == "anslutning"]
    brunnar = [[k, f"Ø{x['d']:.0f}", rh(u, x["lock"]), rh(u, x["botten"])] for k, x in u["brunnar"].items()]
    uk = u["uk"]
    kol: list[dict] = [
        dict(typ="rubrik", text="Anvisningar"),
        dict(typ="lista", sz=6.6, rader=[
            f"Dränering: dränrör Ø110 runt grunden, {u['avstand']['dränering']:.0f} mm utanför grundens ytterkant med "
            f"överkanten i grundens underkant (källaren {rh(u, uk['källaren'])}, plattan på mark "
            f"{rh(u, uk['plattan'])}), i makadam 16–32 omsluten av fiberduk; fall minst "
            f"1:{1 / u['fall']['dränering']:.0f} mot brunnen.",
            f"Dagvatten: täta markavloppsrör Ø110 {u['avstand']['dagvatten']:.0f} mm utanför grunden, minst "
            f"{u['tackning']:.0f} mm under marken; fall minst 1:{1 / u['fall']['dagvatten']:.0f}. Stuprören ansluts "
            "med en stuprörsanslutning med lövsil vid marken, lodrätt ned och en sticka till ledningen. Dräneringen "
            "och dagvattnet är skilda ända till brunnen.",
            "Ledningarna delas längst från brunnen i två grenar som faller åt var sitt håll mot brunnen, med spolrör "
            "(D0, S0) där de börjar. Där grunden eller marken faller brantare än 1:1 faller ledningen lodrätt i en "
            "spolbrunn Ø200 (SB) med lock i marken.",
            "Under entréavsatsen och sovrumsavsatsen går ledningarna under stenarnas underkant, utan spolbrunnar; "
            "stenarna sätts efter ledningarna. Stupröret DB4-ST1 på sovrumsavsatsen ansluts lodrätt genom stenen. "
            "Ledningarna går till stor del i berget (schakt i berg, som grunden).",
            "Höjderna: vattengången (VG, rörets innerbotten) i RH 2000 i brytpunkterna, rak lutning mellan dem; "
            f"plan 1 ±0 = {rh(u, 0.0)}. Två höjder: före och efter spolbrunnen.",
            f"Brunnen B1 utanför källarväggen V9, nära den gamla. Utloppet till det befintliga utgående röret Ø110 "
            f"mot nordost (mot rampen in på tomten mellan boden och planteringen), ÖK +{sv(u['utlopp_ok'], 3)} vid "
            "brunnen (AR-02): kontrollera rörets läge och höjd på plats innan brunnen sätts.",
            "Produkterna är inte valda (allmänna typer med vanliga mått). Ritningen ritas med ./mod dranering ritning.",
        ]),
        dict(typ="rubrik", text="Teckenförklaring"),
        _teckenforklaring(),
        dict(typ="rubrik", text="Ledningar"),
        dict(typ="tabell", kolumner=["Id", "Vad", "Längd (m)", "VG början", "VG brunnen"],
             bredd=(0.4, 0.9, 0.7, 0.8, 0.8), just=["l", "l", "r", "r", "r"], sz=6.2, rader=rader),
        dict(typ="rubrik", text="Stuprörens anslutningar"),
        dict(typ="tabell", kolumner=["Stuprör", "Till", "VG vid stupröret", "VG vid ledningen"],
             bredd=(0.8, 0.4, 1.0, 1.0), just=["l", "l", "r", "r"], sz=6.2, rader=anslutningar),
        dict(typ="rubrik", text="Brunnar"),
        dict(typ="tabell", kolumner=["Id", "Ø", "Lock", "Botten"], bredd=(0.5, 0.5, 0.8, 0.8),
             just=["l", "l", "r", "r"], sz=6.2, rader=brunnar),
    ]
    nr = f"{SERIE.split()[0]}.1"
    return blad(nr, ["Dagvatten och dränering", "Plan"], f"1:{SKALA:g}, 1:{DETALJ:g}", "Modellen", kol,
                [_plan(u, delar, norr), _brunnen(u)])


def ritningar(utdrag: dict, plan1: list[dict], norr: tuple[float, float], arbete: Path, ut: Path) -> Path:
    """Dräneringens ritning (serien SERIE) som pdf i mappen ut (bladet för sig i arbetsmappen, under repots rot)."""
    nr = f"{SERIE.split()[0]}.1"
    pdf = ut / f"{SERIE}.pdf"
    kompilera([(nr, _blad(utdrag, plan1, norr))], arbete, pdf)
    return pdf


def lista(utdrag: dict, kontroll: tuple[list[str], list[str]], krockar: list[str]) -> str:
    """Ledningarna med höjderna, brunnarna, kontrollen och krockarna mot huset som markdown."""
    u = utdrag
    fel, anm = kontroll
    rad = ["# Dräneringen och dagvattnet", "", "Höjderna: vattengången (VG) i RH 2000.", "",
           f"## Kontroll: {len(fel)} fel, {len(anm)} anmärkningar", ""]
    rad += [f"- FEL {f}" for f in fel] + [f"- {a}" for a in anm]
    rad += ["", "## Krockar mot husets delar (utom marken)", ""] + ([f"- {k}" for k in krockar] or ["Inga."])
    rad += ["", "## Ledningar", "", "| Id | Typ | Beskrivning | Brytpunkter (x, y, VG) |", "|---|---|---|---|"]
    for k, x in u["ledningar"].items():
        pkt = " → ".join(f"({p[0]:.0f}, {p[1]:.0f}, {vg(u, p[2])})" for p in x["vag"])
        rad.append(f"| {k} | {x['typ']} | {x['beskrivning']} | {pkt} |")
    rad += ["", "## Brunnar", "", "| Id | Ø | Lock | Botten | x | y | Beskrivning |", "|---|---|---|---|---|---|---|"]
    for k, b in u["brunnar"].items():
        rad.append(f"| {k} | {b['d']:.0f} | {rh(u, b['lock'])} | {rh(u, b['botten'])} | {b['punkt'][0]:.0f} | "
                   f"{b['punkt'][1]:.0f} | {b['beskrivning']} |")
    return "\n".join(rad) + "\n"
