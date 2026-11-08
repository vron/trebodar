"""R-02, konstruktionsritningen av trästommen (#91): ur modellens bärverk (`./mod barverk`, samma utdrag som K-04:s
balkmodell), så att bladen, ID:na, kapplistorna och måtten följer stommen när den ändras.

Bladen i byggordning: först en översikt i 3D med varje element märkt med sitt blad, och förteckningen över bladen;
sedan väggarna, en per blad (ytterväggarna huskropp för huskropp, sedan de bärande innerväggarna), stolparna,
takstolarna, takfallen (takbalkarna och stålbanden) och nock- och dalbalkarna (stålet på R-01).

Varje element ritas i sin egen vy: väggar, takstolar, stolpar och balkar i elevation (väggarna sedda utifrån,
innerväggarna från sidan w < 0), takfallen vinkelrätt mot takytan. Delarna är märkta med sitt ID (utan elementets
kod); längderna står bara i kapplistan på bladet (ID, tvärsnitt och material, längd, vinkelkap). Måtten är lägen som
på bygget: kedjemått från elementets vänstra ände till varje stående del (regel, stolpe, takbalk) med totalmått, och
i höjd till de liggande delarna och öppningarna.
"""
from __future__ import annotations

import math
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from shapely.geometry import MultiPoint, Polygon

from .karna import ROT
from .planritning import Blad, Vy, blad, svm

SERIE = "R-02"
TITEL = "Trästomme"
FYLL = {"C24": "mark", "GL30c": "limtra", "Stålband": "stal", "Spikplåt": "stal", "S235": "stal", "S355": "stal"}
KROPPAR = ("1", "2", "3")
INNERVAGGAR = ("1A", "1B", "1C", "1D", "2A", "2B", "2C")
RYTA = (25.0, 20.0, 300.0, 150.0)          # ritytan för elevationen: x, y, bredd, höjd (pappersmm)
SKALOR = (20.0, 25.0, 50.0, 100.0)
NIVA = 60.0                                # höjdmåttens nivåer närmare än så slås ihop [mm]
KAPP_B = 74.0                              # kolumnens bredd


@dataclass(frozen=True)
class Del:
    namn: str
    grupp: str
    element: str
    typ: str
    material: str
    R: np.ndarray
    t: np.ndarray
    bb: tuple[float, ...]
    kontur: tuple[tuple[float, float], ...] | None

    @property
    def matt(self) -> tuple[float, float, float]:
        return (self.bb[3] - self.bb[0], self.bb[4] - self.bb[1], self.bb[5] - self.bb[2])

    @property
    def langd(self) -> float:
        return max(self.matt)

    def horn(self) -> np.ndarray:
        """Hörnen i världen (N × 3)."""
        z0, z1 = self.bb[2], self.bb[5]
        if self.kontur:
            lok = [(x, y, z) for x, y in self.kontur for z in (z0, z1)]
        else:
            lok = [(x, y, z) for x in (self.bb[0], self.bb[3]) for y in (self.bb[1], self.bb[4]) for z in (z0, z1)]
        return np.asarray(lok) @ self.R.T + self.t

    def profil(self) -> list[tuple[float, float, float]] | None:
        """Konturen i världen i dess mittplan, om konturen är delens profil (inte dess tvärsnitt längs längden)."""
        if not self.kontur or self.matt[2] >= max(self.matt[:2]):
            return None
        zm = (self.bb[2] + self.bb[5]) / 2
        return [tuple(np.asarray((x, y, zm)) @ self.R.T + self.t) for x, y in self.kontur]

    @property
    def tvarsnitt(self) -> str:
        a, b = sorted(self.matt)[:2]
        return f"{svm(round(a))}×{svm(round(b))}"

    @property
    def vinkel(self) -> str:
        """Vinkelkapen: profilens kanter som inte är parallella med eller vinkelräta mot delens längd."""
        if not self.kontur or self.matt[2] >= max(self.matt[:2]):
            return ""
        lx = 0 if self.matt[0] >= self.matt[1] else 1
        v = set()
        for (x0, y0), (x1, y1) in zip(self.kontur, [*self.kontur[1:], self.kontur[0]]):
            d = (x1 - x0, y1 - y0)
            if math.hypot(*d) < 20.0:
                continue
            a = abs(math.degrees(math.atan2(d[1 - lx], d[lx]))) % 180.0
            a = min(a, 180.0 - a)
            if 1.0 < a < 89.0:
                v.add(round(90.0 - a))
        return ", ".join(f"{x}°" for x in sorted(v))


def delar(utdrag: dict) -> list[Del]:
    return [Del(p["namn"], p["grupp"], p["element"], p["typ"], p["material"], np.asarray(p["R"], float),
                np.asarray(p["t"], float), tuple(p["bb"]), tuple(map(tuple, p["kontur"])) if p.get("kontur") else None)
            for p in utdrag["delar"]]


@dataclass
class Element:
    kod: str
    titel: str                  # bladets rubrik
    slag: str                   # vägg, stolpe, takstol, takfall, balk
    delar: list[Del]
    origo: np.ndarray           # vyns origo (världen)
    eu: np.ndarray              # vyns axlar i världen: u åt höger, v uppåt, n mot betraktaren
    ev: np.ndarray
    oppningar: list[tuple[float, float, float, float]]
    nr: str = ""

    def uv(self, p: np.ndarray) -> np.ndarray:
        q = np.atleast_2d(p) - self.origo
        return np.column_stack([q @ self.eu, q @ self.ev])


def _kort(d: Del, kod: str) -> str:
    return d.namn[len(kod) + 1:] if d.namn.startswith(kod + "-") else d.namn


def _yta(e: Element, d: Del) -> Polygon:
    """Delens yta i vyn: profilen om den ligger i vyns plan, annars det konvexa höljet."""
    n = np.cross(e.eu, e.ev)
    prof = d.profil()
    if prof is not None and abs(float(d.R[:, 2] @ n)) > 0.99:
        p = Polygon(e.uv(np.asarray(prof)))
        if p.is_valid and p.area > 1.0:
            return p
    return MultiPoint([tuple(q) for q in e.uv(d.horn())]).convex_hull


def element(utdrag: dict, alla: list[Del]) -> list[Element]:
    """Elementen i byggordning."""
    vaggar = {v["kod"]: v for v in utdrag["vaggar"]}
    ut: list[Element] = []

    def plan_av(dl: list[Del]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Vyns origo och axlar för ett element som inte är en vägg: det lodräta planet där delarna har störst
        utbredning (u åt växande x eller y)."""
        P = np.vstack([d.horn() for d in dl])
        xy = P[:, :2] - P[:, :2].mean(axis=0)
        _, _, vt = np.linalg.svd(xy, full_matrices=False)
        u = np.array([*vt[0], 0.0])
        if u[0] < -1e-6 or (abs(u[0]) < 1e-6 and u[1] < 0):
            u = -u
        o = np.array([*P[:, :2].min(axis=0), 0.0]) if abs(u[0]) > 0.7 else np.array([P[:, 0].mean(), P[:, 1].min(), 0.0])
        return o, u, np.array([0.0, 0.0, 1.0])

    def vagg(kod: str, grupper: tuple[str, ...], titel: str, slag: str) -> None:
        dl = [d for d in alla if d.element == kod and d.grupp in grupper]
        if not dl:
            return
        v = vaggar[kod]
        u = np.array([*v["u"], 0.0])
        w = np.array([*v["w"], 0.0])
        o = np.array([*v["origo"], 0.0])
        # sett utifrån (ytterväggarna: w inåt) eller från sidan w < 0: u åt höger om w är synriktningen
        if np.cross(w, np.array([0.0, 0.0, 1.0])) @ u < 0:
            u, o = -u, o + np.array([*v["u"], 0.0]) * v["langd"]
        opp = [(a, b, c, d_) for a, b, c, d_ in v.get("oppningar", [])]
        if (u @ np.array([*v["u"], 0.0])) < 0:
            opp = [(v["langd"] - b, v["langd"] - a, c, d_) for a, b, c, d_ in opp]
        ut.append(Element(kod, titel, slag, dl, o, u, np.array([0.0, 0.0, 1.0]), opp))

    for k in KROPPAR:
        for s in ("NO", "SO", "SV", "NV"):
            kod = f"{k}{s}"
            if kod in vaggar:
                vagg(kod, ("yttervagg", "band_vagg"), f"Yttervägg {kod}", "vägg")
    for kod in INNERVAGGAR:
        vagg(kod, ("innervagg", "band_vagg"), f"Bärande innervägg {kod}", "vägg")
    for kod in sorted({d.element for d in alla if d.grupp == "stolpe"}):
        dl = [d for d in alla if d.element == kod and d.grupp == "stolpe"]
        o, u, v_ = plan_av(dl)
        ut.append(Element(kod, f"Stolpe {kod}", "stolpe", dl, o, u, v_, []))
    for kod in [k for k in (*[f"{a}{b}" for a in KROPPAR for b in ("NO", "SV")], "2C")
                if any(d.element == k and d.grupp == "takstol" for d in alla)]:
        dl = [d for d in alla if d.element == kod and d.grupp == "takstol"]
        if kod in vaggar:
            v = vaggar[kod]
            u = np.array([*v["u"], 0.0])
            o = np.array([*v["origo"], 0.0])
            w = np.array([*v["w"], 0.0])
            if np.cross(w, np.array([0.0, 0.0, 1.0])) @ u < 0:
                u, o = -u, o + np.array([*v["u"], 0.0]) * v["langd"]
        else:
            o, u, _ = plan_av(dl)
        ut.append(Element(kod, f"Takstol {kod}", "takstol", dl, o, u, np.array([0.0, 0.0, 1.0]), []))
    for t in utdrag["takytor"]:
        kod = t["kod"]
        dl = [d for d in alla if d.element == kod and d.grupp in ("takbalk", "band_tak")]
        if not dl:
            continue
        a = math.radians(t["lutning"])
        r = t["riktning"]                       # takfallet stiger mot nocken i x-riktningen r
        ev = np.array([r * math.cos(a), 0.0, math.sin(a)])
        eu = np.array([0.0, -r, 0.0]) if r > 0 else np.array([0.0, 1.0, 0.0])
        eu = eu if np.cross(eu, ev) @ np.array([-r * math.sin(a), 0.0, math.cos(a)]) > 0 else -eu
        ut.append(Element(kod, f"Takfall {kod}: takbalkar och stålband", "takfall", dl, np.zeros(3), eu, ev, []))
    for kod in sorted({d.element for d in alla if d.grupp == "balk"}):
        dl = [d for d in alla if d.element == kod and d.grupp == "balk"]
        o, u, v_ = plan_av(dl)
        ut.append(Element(kod, f"{'Nockbalk' if kod.startswith('NB') else 'Dalbalk'} {kod}", "balk", dl, o, u, v_, []))
    for i, e in enumerate(ut, start=2):
        e.nr = f"{SERIE}.{i}"
    return ut


def _staende(e: Element, d: Del, yta: Polygon) -> bool:
    """De delar vars lägen måtts längs elementet: reglar, stolpar och takbalkar (höga och smala i vyn)."""
    x0, y0, x1, y1 = yta.bounds
    return (y1 - y0) > 3.0 * (x1 - x0) and d.material not in ("Stålband", "Spikplåt")


def _kapplista(e: Element) -> list[list[str]]:
    rader = []
    for d in sorted(e.delar, key=lambda d: d.namn):
        typ = f"{d.tvarsnitt} {d.material}" if d.material not in ("Spikplåt",) else f"Spikplåt {d.tvarsnitt}"
        rader.append([_kort(d, e.kod), typ, svm(round(d.langd)), d.vinkel])
    return rader


def _elementblad(e: Element) -> Blad:
    ytor = {d.namn: _yta(e, d) for d in e.delar}
    alla_ytor = [g for g in ytor.values() if not g.is_empty]
    u0, v0, u1, v1 = MultiPoint([p for g in alla_ytor for p in (g.exterior.coords if hasattr(g, "exterior")
                                                                   else g.coords)]).bounds
    bredd, hojd = u1 - u0, v1 - v0
    rx, ry, rb, rh = RYTA
    skala = next((s for s in SKALOR if bredd / s <= rb - 20.0 and hojd / s <= rh - 30.0), SKALOR[-1])
    x = rx + 20.0 + (rb - 20.0 - bredd / skala) / 2
    y = ry + 12.0
    v = Vy(0.0, 0.0, 420.0, 297.0, skala, u0 - x * skala, v1 + y * skala)
    with v.lager("delar"):
        for d in sorted(e.delar, key=lambda d: (d.material in ("Stålband", "Spikplåt"), d.namn)):
            g = ytor[d.namn]
            if g.is_empty or not hasattr(g, "exterior"):
                continue
            v.polygon(list(g.exterior.coords)[:-1], FYLL.get(d.material, "mark"), "tunn")
    with v.lager("oppningar"):
        for a, b, c, d_ in e.oppningar:
            v.polygon([(a, c), (b, c), (b, d_), (a, d_)], None, "dold")
    with v.lager("id"):
        for d in e.delar:
            g = ytor[d.namn]
            if g.is_empty or d.material == "Spikplåt":
                continue
            c = g.representative_point()
            gx0, gy0, gx1, gy1 = g.bounds
            hog = (gy1 - gy0) > (gx1 - gx0)
            v.text(c.x, c.y, _kort(d, e.kod), a="cm", sz=4.6, rot=90 if hog else 0, col="ink")
    with v.lager("matt"):
        # de stående delarnas vänstra kanter; delar som ligger an mot den förra (dubbla reglar) måtts inte för sig
        st = sorted((ytor[d.namn].bounds[0], ytor[d.namn].bounds[2]) for d in e.delar
                    if _staende(e, d, ytor[d.namn]))
        xs, hoger = [round(u0)], u0
        for a, b in st:
            if a > hoger + 5.0 and a - xs[-1] > 5:
                xs.append(round(a))
            hoger = max(hoger, b)
        if round(u1) - xs[-1] > 5:
            xs.append(round(u1))
        y_linje = v0 - 8.0 * skala
        if len(xs) > 2:
            v.mattx(xs, y_linje, [v0] * len(xs), sz=5.6)
        v.mattx([xs[0], xs[-1]], y_linje - 7.0 * skala, [v0, v0], sz=6.4)
        if e.oppningar:
            ox = sorted({round(u0), round(u1), *(round(q) for a, b, _, _ in e.oppningar for q in (a, b))})
            v.mattx(ox, y_linje - 14.0 * skala, [v0] * len(ox), sz=5.6)
        # i höjd: de liggande delarnas underkant och öppningarnas kanter
        zs = {round(v0), round(v1)}
        for d in e.delar:
            g = ytor[d.namn]
            gx0, gy0, gx1, gy1 = g.bounds
            if (gx1 - gx0) > 3.0 * (gy1 - gy0) and d.material not in ("Stålband", "Spikplåt"):
                zs |= {round(gy0), round(gy1)}
        for _, _, c, d_ in e.oppningar:
            zs |= {round(c), round(d_)}
        ys: list[int] = []
        for a in sorted(zs):                            # nivåer närmare än NIVA slås ihop (dubbla hammarband)
            if not ys or a - ys[-1] >= NIVA:
                ys.append(a)
        if round(v1) - ys[-1] > 5:
            ys[-1] = round(v1)
        if len(ys) > 2 and e.slag != "takfall":
            v.matty(ys, u1 + 10.0 * skala, [u1] * len(ys), sz=5.6)
    kapp = _kapplista(e)
    block: list[dict] = []
    y_kapp = y + hojd / skala + (34.0 if e.oppningar else 27.0)
    rader = max(1, int((282.0 - y_kapp - 8.0) / 3.0))
    for i in range(0, len(kapp), rader):
        block.append(dict(x=rx + (i // rader) * (KAPP_B + 4.0), y=y_kapp, w=KAPP_B, innehall=[
            dict(typ="rubrik", text="Kapplista" if i == 0 else "Kapplista, forts."),
            dict(typ="tabell", kolumner=["ID", "Typ", "Längd", "Snedkap"], bredd=(0.7, 1.5, 0.6, 0.6),
                 just=["l", "l", "r", "r"], sz=5.8, rader=kapp[i:i + rader])]))
    vy_text = {"vägg": "sedd utifrån" if e.kod[0] in KROPPAR and len(e.kod) == 3 else "sedd från sidan w < 0",
               "takstol": "sedd utifrån", "stolpe": "i stolpens plan", "balk": "från sidan",
               "takfall": "vinkelrätt mot takytan, takfoten nedåt"}[e.slag]
    kol: list[dict] = [
        dict(typ="rubrik", text="Anvisningar"),
        dict(typ="lista", sz=7.0, rader=[
            f"{e.titel}, {vy_text}.",
            "Delarna är märkta med sitt ID (utan elementets kod). Längderna står bara i kapplistan; snedkap: kapens "
            "vinklar mot ett rätvinkligt kap.",
            "Måtten är lägen: kedjemått från elementets vänstra ände till varje stående dels vänstra kant, med "
            "totalmått; i höjd till de liggande delarnas kanter och öppningarna.",
            "Mått i mm. Ritningen ritas ur modellens stomme (./mod stomme ritning), samma underlag som K-04.",
            *(["Stålet i nock- och dalbalkarna (plåtar, distansreglar): se R-01."] if e.slag == "balk" else []),
        ]),
    ]
    return blad(e.nr, ["Trästomme", e.titel], f"1:{skala:g}", "Modellen", kol, [v], block)


# ------------------------------------------------------------------ översikten


def _iso(P: np.ndarray) -> np.ndarray:
    c, s = math.cos(math.radians(30.0)), math.sin(math.radians(30.0))
    return np.column_stack([(P[:, 0] - P[:, 1]) * c, (P[:, 0] + P[:, 1]) * s + P[:, 2]])


def _oversikt(elementen: list[Element], alla: list[Del]) -> Blad:
    proj = {d.namn: _iso(d.horn()) for d in alla}
    P = np.vstack(list(proj.values()))
    x0, y0 = P.min(axis=0)
    x1, y1 = P.max(axis=0)
    rb, rh = 290.0, 200.0
    skala = max((x1 - x0) / rb, (y1 - y0) / rh)
    skala = next(s for s in (50.0, 75.0, 100.0, 125.0, 150.0) if s >= skala)
    v = Vy(0.0, 0.0, 420.0, 297.0, skala, x0 - (25.0 + (rb - (x1 - x0) / skala) / 2) * skala, y1 + 18.0 * skala)
    with v.lager("delar"):
        for d in sorted(alla, key=lambda d: float((d.horn()[:, 0] + d.horn()[:, 1] - 2.0 * d.horn()[:, 2]).mean()),
                        reverse=True):
            h = MultiPoint([tuple(q) for q in proj[d.namn]]).convex_hull
            if hasattr(h, "exterior"):
                v.polygon(list(h.exterior.coords)[:-1], FYLL.get(d.material, "mark"), "fin")
    with v.lager("etiketter"):
        for e in elementen:
            Q = np.vstack([proj[d.namn] for d in e.delar])
            c = Q.mean(axis=0)
            v.text(c[0], c[1], f"{e.kod} · {e.nr}", a="cm", sz=6.2, b=True, bg=True)
    forteckning = [[f"{SERIE}.1", "Översikt och förteckning"], *([e.nr, e.titel] for e in elementen)]
    halv = (len(forteckning) + 1) // 2
    block = [dict(x=25.0 + i * 100.0, y=226.0, w=96.0, innehall=[
        dict(typ="rubrik", text="Bladen i byggordning" if i == 0 else "Bladen, forts."),
        dict(typ="tabell", kolumner=["Blad", "Innehåll"], bredd=(0.5, 2.2), just=["l", "l"], sz=5.8,
             rader=forteckning[i * halv:(i + 1) * halv])]) for i in range(2)]
    kol: list[dict] = [
        dict(typ="rubrik", text="Anvisningar"),
        dict(typ="lista", sz=7.0, rader=[
            "Trästommen ovanför mellanbjälklaget i 3D: väggarna, stolparna, takstolarna, takbalkarna, stålbanden och "
            "nock- och dalbalkarna. Varje element är märkt med sin kod och sitt blad.",
            "Bladen följer byggordningen: väggarna (ytterväggarna huskropp för huskropp, sedan de bärande "
            "innerväggarna), stolparna, takstolarna, takfallen och nock- och dalbalkarna.",
            "Stommens förankring i mellanbjälklaget: betongbultar genom syllarna (AR-03).",
            "Ritningen ritas ur modellens stomme (./mod stomme ritning), samma underlag som K-04.",
        ]),
    ]
    return blad(f"{SERIE}.1", ["Trästomme", "Översikt i 3D och förteckning"], "–", "Modellen", kol, [v], block)


def ritningar(utdrag: dict, mapp: Path, pdf: Path) -> Path:
    alla = delar(utdrag)
    elementen = element(utdrag, alla)
    bladen = [(f"{SERIE}.1", _oversikt(elementen, alla))] + [(e.nr, _elementblad(e)) for e in elementen]
    mapp.mkdir(parents=True, exist_ok=True)
    pdfer = [mapp / f"{nr}.pdf" for nr, _ in bladen]

    def kompilera(arg: tuple[tuple[str, Blad], Path]) -> None:
        (nr, b), p = arg
        jp = mapp / f"{nr}.json"
        b.spara(str(jp))
        b.kompilera(str(jp), str(p), str(ROT))

    with ThreadPoolExecutor(max_workers=8) as ex:
        list(ex.map(kompilera, zip(bladen, pdfer)))
    pdf.parent.mkdir(parents=True, exist_ok=True)
    Blad.serie([str(p) for p in pdfer], str(pdf))
    return pdf


def blad_nummer(utdrag: dict) -> Sequence[str]:
    return [f"{SERIE}.1", *(e.nr for e in element(utdrag, delar(utdrag)))]
