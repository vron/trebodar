"""Gemensamt för ritningarna ur modellen (kameraplanen, elritningarna och ljusplanerna): snitt ur STEP-filen
(verktyg/modellanalys `ma snitt`), planens väggar, fönster, dörrar och trappor i en vy, och bladen i den gemensamma
ritningsmallen beräkningar/ritningsmall (A3 med ram, högerkolumn och ritningshuvud, i samma stil som de andra
ritningarna). Vyerna täcker hela bladet (pappersmm från bladets hörn); planen placeras med `vy`.
"""
from __future__ import annotations

import datetime
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union

from .karna import ROT

if str(ROT / "beräkningar" / "ritningsmall") not in sys.path:
    sys.path.insert(0, str(ROT / "beräkningar" / "ritningsmall"))
from ritning import Blad, Vy, figur, huvud, sv, svm  # noqa: E402   (ritningsmallen)

__all__ = ["Blad", "Vy", "figur", "sv", "svm", "MINSTA_HAL", "UTOM", "VAGGAR", "blad", "kompilera", "norrpil",
           "origo", "papper", "plan", "plan_ytor", "polygoner", "rita_ytor", "sektion", "snitt", "vy"]

# delarna som inte ritas i planerna (sökvägens början)
UTOM = ("Mark/", "Hus/Armering", "Hus/Grund/Plattan", "Hus/Grund/Fasadsten", "Hus/Installationer", "Hus/Tak")
VAGGAR = ("Hus/Stomme", "Hus/Invändigt", "Hus/Fasad", "Hus/Isolering")       # väggarna i snittet, som en yta
VAGG = "#d6d6d6"
GLAS = "#dcebf4"
MINSTA_HAL = 0.5e6               # mindre hål i ytorna (väggarnas hålrum) fylls [mm²]
# planens ytor i ritordning: (sökvägens början, fyllning, linje); delarna i en grupp slås ihop till en yta
PLAN = (
    (VAGGAR, VAGG, "tunn"),
    (("Hus/Grund/Rör",), "stal", None),
    (("Hus/Grund",), "karna", "tunn"),
    (("Hus/Mellanbjälklag",), "betong", "tunn"),
    (("Hus/Fönster och dörrar",), "vit", "fin"),
    (("Hus/Trappa",), "vit", "fin"),
    (("Hus/Kamin",), "stal", "tunn"),
)
DATUM = datetime.date.today().isoformat()


def snitt(ma: Path, step: Path, z: float | str, json_ut: Path, delar: str | None = None) -> list[dict]:
    """Delarnas snittytor i planet z (mm, vågrätt) eller planet som text ("y=8220": lodrätt, med snittets x och z)
    ur STEP-filen (via ma-tjänsten, verktyg/modellanalys/tjanst.py); delar: bara de här (ma:s --delar, snabbare)."""
    plan_ = z if isinstance(z, str) else f"z={z:g}"
    subprocess.run([str(ma), "snitt", plan_, "--fil", str(step), "--json", str(json_ut), "--ingen-bild",
                    *(["--delar", delar] if delar else [])], check=True, capture_output=True)
    return json.loads(json_ut.read_text(encoding="utf-8"))["delar"]


def polygoner(delar: list[dict], bara: tuple[str, ...] = (), utom: tuple[str, ...] = UTOM) -> list[Any]:
    """Snittets ytor (med hål) för delarna vars sökväg börjar med något i `bara` (alla om den är tom), utom `utom`."""
    ut = []
    for d in delar:
        if d["sokvag"].startswith(utom) or (bara and not d["sokvag"].startswith(bara)):
            continue
        for y in d["ytor"]:
            if len(y[0]) >= 3:
                p = Polygon(y[0], [r for r in y[1:] if len(r) >= 3]).buffer(0)
                if not p.is_empty:
                    ut.append(p)
    return ut


def rita_ytor(v: Vy, g: Any, fyll: str | None, stil: str | None, minsta_hal: float = 0.0) -> None:
    """Ytorna i en geometri (Polygon, MultiPolygon eller samling) med hålen, utom hål mindre än minsta_hal [mm²]."""
    for p in getattr(g, "geoms", [g]):
        if isinstance(p, Polygon) and not p.is_empty:
            v.polygon(list(p.exterior.coords), fyll, stil,
                      hal=[list(r.coords) for r in p.interiors if Polygon(r).area >= minsta_hal])


def plan_ytor(delar: list[dict], vagg: str = VAGG) -> list[tuple[Any, str | None, str | None]]:
    """Planens snitt som ytor i ritordning (geometri, fyllning, linje): väggarna (stomme, invändigt, fasad och
    isolering) som en sammanhängande yta, betongen (grund, bjälklag), stålrören, fönster och dörrar (glaset
    ljusblått), trappan och kaminen; övrigt utan fyllning."""
    grupper: list[list[Any]] = [[] for _ in range(len(PLAN) + 2)]
    for d in delar:
        if d["sokvag"].startswith(UTOM):
            continue
        if "Fönster och dörrar" in d["sokvag"] and d["sokvag"].endswith("-GLAS"):
            i = len(PLAN)
        else:
            i = next((j for j, (pre, _, _) in enumerate(PLAN) if d["sokvag"].startswith(pre)), len(PLAN) + 1)
        grupper[i] += polygoner([d])
    stilar = [(f if i else vagg, s) for i, (_, f, s) in enumerate(PLAN)] + [(GLAS, "fin"), (None, "fin")]
    return [(unary_union(ytor), fyll, stil) for ytor, (fyll, stil) in zip(grupper, stilar) if ytor]


def plan(v: Vy, delar: list[dict], vagg: str = VAGG, ram: Any = None) -> list[tuple[Any, str | None, str | None]]:
    """Planens snitt i vyn (plan_ytor), med hålrummen i väggarna fyllda. ram: bara inom den ytan (en del av
    planet). Ger ytorna (plan_ytor)."""
    ytor = plan_ytor(delar, vagg)
    with v.lager("snitt"):
        for u, fyll, stil in ytor:
            rita_ytor(v, u if ram is None else u.intersection(ram), fyll, stil, MINSTA_HAL)
    return ytor


# sektionernas ytor i ritordning (sökvägens början, fyllning, linje); delarna i en grupp slås ihop till en yta
SEKTION = (
    (("Mark/",), "mark", None),
    (("Hus/Grund", "Hus/Mellanbjälklag"), "betong", "tunn"),
    (("Hus/Isolering",), "isol", "fin"),
    (("Hus/Stomme", "Hus/Invändigt/Innerväggar/Lätta väggar"), "limtra", "tunn"),
    (("Hus/Invändigt", "Hus/Fönster och dörrar", "Hus/Trappa"), "vit", "fin"),
    (("Hus/Fasad",), VAGG, "fin"),
    (("Hus/Tak",), "#bdbdbd", "fin"),
    (("Hus/Kamin",), "stal", "tunn"),
)


def sektion(v: Vy, delar: list[dict], ram: Any = None) -> None:
    """En lodrät sektion (snittets x eller y och z) i vyn: marken, betongen, isoleringen, stommen, skivorna, fasaden,
    taket och kaminen, delarna i varje grupp som en yta (installationerna och armeringen utelämnade). ram: bara inom
    den ytan."""
    grupper: list[list[Any]] = [[] for _ in SEKTION]
    for d in delar:
        if d["sokvag"].startswith(("Hus/Armering", "Hus/Installationer")):
            continue
        i = next((j for j, (pre, _, _) in enumerate(SEKTION) if d["sokvag"].startswith(pre)), None)
        if i is not None:
            grupper[i] += polygoner([d], utom=())
    with v.lager("snitt"):
        for ytor, (_, fyll, stil) in zip(grupper, SEKTION):
            if ytor:
                u = unary_union(ytor)
                rita_ytor(v, u if ram is None else u.intersection(ram), fyll, stil, MINSTA_HAL)


def vy(skala: float, omrade: tuple[float, float, float, float], x: float, y: float) -> Vy:
    """En vy över hela bladet i skalan, med områdets övre vänstra hörn (x0, y1) i pappersmm (x, y) från bladets
    övre vänstra hörn; omrade = (x0, x1, y0, y1) i modellens mm."""
    return Vy(0.0, 0.0, 420.0, 297.0, skala, omrade[0] - x * skala, omrade[3] + y * skala)


def papper(v: Vy, x: float, y: float) -> tuple[float, float]:
    """Modellpunkten vid pappersmm (x, y) från bladets övre vänstra hörn (vyer från `vy`)."""
    return v.X0 + x * v.s, v.Y1 - y * v.s


def norrpil(v: Vy, X: float, Y: float, norr: tuple[float, float]) -> None:
    """Norrpilen i modellpunkten (X, Y), som på AR-02; norr: riktningen i modellens x och y."""
    with v.lager("norr"):
        c = np.array([X, Y])
        d = np.array(norr) / float(np.hypot(*norr))
        v.linje([tuple(c - d * v.m(7)), tuple(c + d * v.m(5))], "normal")
        v.pil(tuple(c + d * v.m(7)), tuple(d), langd=3.2, bredd=2.4)
        q = c + d * v.m(10.5)
        v.text(q[0], q[1], "N", a="cm", sz=9, b=True)


def origo(v: Vy) -> None:
    """Koordinatsystemets origo (K-05: skärningen mellan mellanbjälklagets kanter x = 0 och y = 0), som på R-05."""
    with v.lager("origo"):
        L = v.m(12)
        v.linje([(0, 0), (L, 0)], "tunn")
        v.pil((L + v.m(2), 0), (1, 0), langd=2.2, bredd=1.0)
        v.linje([(0, 0), (0, L)], "tunn")
        v.pil((0, L + v.m(2)), (0, 1), langd=2.2, bredd=1.0)
        v.ptext(L + v.m(2), 0, 0, 0.8, "x", a="cb", sz=7.5, i=True)
        v.ptext(0, L + v.m(2), 1.0, 0, "y", a="lm", sz=7.5, i=True)
        v.ptext(0, 0, 1.0, -1.0, "origo (0; 0)", a="lt", sz=6.4, col="gra")


def blad(nummer: str, titel: list[str], skala: str, underlag: str, kolumn: list[dict], vyer: list[Vy],
         block: list[dict] | None = None, rev: str = "–", datum: str = DATUM, status: str = "PRELIMINÄR") -> Blad:
    """Ett blad ur modellen: standard preliminärt, utan revision, daterat när det ritas."""
    return Blad(huvud(nummer, titel, skala, underlag, datum, rev, status=status), [], kolumn, vyer, block or [])


def kompilera(bladen: list[tuple[str, Blad]], mapp: Path, pdf: Path) -> list[Path]:
    """Bladen (nummer, blad) som JSON och pdf i mappen (under repots rot, för Typst) och ihopslagna till pdf:en, ett
    blad per sida."""
    mapp.mkdir(parents=True, exist_ok=True)
    pdfer = []
    for nr, b in bladen:
        jp = mapp / f"{nr}.json"
        b.spara(str(jp))
        pdfer.append(mapp / f"{nr}.pdf")
        b.kompilera(str(jp), str(pdfer[-1]), str(ROT))
    pdf.parent.mkdir(parents=True, exist_ok=True)
    Blad.serie([str(p) for p in pdfer], str(pdf))
    return pdfer
