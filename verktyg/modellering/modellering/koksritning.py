"""AR-05, arbetsritningen av köksskåpen: ur modellens skåp (modeller/trebodar/hus/inredning/koksskap.py, uppställda
i koksbank.py), så att måtten följer skåpen när de ändras.

Blad 1 är en översikt: bänken och ön i plan och fronterna i elevation, med varje skåps position (B1–B10 längs bänken
från kökets inbyggnad, O1–O3 på ön norrifrån) och typ (KS1 …), och en förteckning över typerna med antal och över
askbrädorna mellan skåpen. Skåp med samma delar (namn, mått och material i skåpets eget system) är samma typ.

Sedan ett blad per typ: framifrån med fronterna, framifrån utan fronterna (stommen, lådorna och löparna), snitt A–A
från sidan, snitt B–B i plan genom den översta lådan och en detalj 1:2 av löparen och lådans nedre hörn, med
tabeller över stommens delar, fronterna, lådornas delar och beslagen. Vyerna och snitten räknas ur delarnas former
(rätblock, skillnader och unioner) i skåpets system: x längs bredden från vänster sida sett framifrån, y in i skåpet
från stommens framkant och z uppåt från golvet.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

from shapely.geometry import Point, Polygon, box as sbox
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from .form import Cylinder, Diff, Form, Lada, Prisma, Transf, Union, omslutande
from .modell import Montage
from .placering import Placering
from .planritning import Blad, Vy, blad, kompilera, svm

SERIE = "AR-05"
TITEL = "Köksskåp"
TOM = Polygon()
# fyllningarna per material: i vyerna och i snitten (snittade delar får en kraftigare kantlinje)
FYLL = {"Björkplywood": "mark", "Björk": "limtra", "Ask": "vit", "Löpare": "stal", "Beslag": "stal",
        "Vitvara": "eps"}
STOMME = {"SIDA-V": "Sida", "SIDA-H": "Sida", "BOTTEN": "Botten", "TAK": "Tak", "TAK-F": "Tak, regel fram",
          "TAK-B": "Tak, regel bak", "RYGG": "Rygg", "SKIVA": "Skiva för fasta fronter", "BLINDFRONT": "Blindfront",
          "HYLLA": "Mellanhylla"}
SKALOR = (10.0, 15.0, 20.0)
DETALJ = 2.0                    # detaljens skala
DETALJ_FONSTER = (-8.0, 78.0, 34.0)   # detaljens fönster: x från, x till, z under löparens överkant
DETALJ_HOJD = 90.0              # detaljens fönster i höjd [mm i verkligheten]
TOPP = 24.0                     # vyernas överkant på papperet (under rubriken)
VANSTER = 34.0                  # vyernas vänstra kant på papperet


# ------------------------------------------------------------------ skåpen ur modellen


@dataclass(frozen=True)
class Del:
    kod: str                    # instansens namn utan skåpets kod, t.ex. "LADA1-SIDA-V"
    namn: str                   # delens namn i modellen
    material: str
    form: Form                  # i skåpets system
    bb: tuple[float, float, float, float, float, float]


@dataclass
class Skap:
    kod: str                    # B1 …, O1 …
    typnamn: str                # Lådskåp, Hörnskåp, Diskmaskin …
    beskrivning: str
    placering: Placering        # skåpets system i huset
    delar: list[Del]
    typ: str = "–"              # KS1 …

    def signatur(self) -> tuple:
        return tuple(sorted((d.kod, d.namn, d.material, tuple(round(v, 1) for v in d.bb)) for d in self.delar))

    def del_(self, kod: str) -> Del:
        return next(d for d in self.delar if d.kod == kod)

    def med(self, prefix: str) -> list[Del]:
        return [d for d in self.delar if d.kod.startswith(prefix)]

    @property
    def bredd(self) -> float:
        return max(d.bb[3] for d in self.delar)

    @property
    def lador(self) -> list[int]:
        return sorted({int(d.kod[4:].split("-")[0]) for d in self.med("LADA")})


def skapen(bank: Montage, on: Montage) -> list[Skap]:
    """Skåpen och diskmaskinen i bänkens och öns montage, i ordning, med delarna i skåpets eget system."""
    ut = []
    for m in (bank, on):
        for i in m.barn:
            b = i.barn
            if not isinstance(b, Montage) or not (b.produkt == "KOKSSKAP" or b.kod == "Diskmaskin"):
                continue
            delar = []
            for vag, d, pl in b.platta():
                assert pl.ar_identitet(), "skåpets delar i skåpets system"
                bb = omslutande(d.form)
                assert bb is not None, vag
                delar.append(Del(vag.split("/")[-1].removeprefix(f"{b.namn}-"), d.namn, d.material.namn, d.form,
                                 bb))
            ut.append(Skap(b.namn, b.kod or "", b.beskrivning, i.placering, delar))
    typer: dict[tuple, str] = {}
    for s in ut:
        if s.typnamn == "Diskmaskin":
            continue
        typer.setdefault(s.signatur(), f"KS{len(typer) + 1}")
        s.typ = typer[s.signatur()]
    return ut


# ------------------------------------------------------------------ geometri: lådor, snitt


def _lador(f: Form) -> list[tuple[float, ...]]:
    """Formens rätblock (för vyerna): rätblocket, skillnadens bas, unionens delar; hål och fräsningar syns inte."""
    if isinstance(f, Lada):
        b = omslutande(f)
        return [b] if b else []
    if isinstance(f, Diff):
        return _lador(f.bas)
    if isinstance(f, Union):
        return [b for d in f.delar for b in _lador(d)]
    return []


AXLAR = {0: (1, 2), 1: (0, 2), 2: (0, 1)}


def _snitt(f: Form, ax: int, c: float) -> BaseGeometry:
    """Formens snitt med planet koordinat ax = c, i planets två andra koordinater (i stigande ordning)."""
    ui, vi = AXLAR[ax]
    if isinstance(f, Diff):
        return _snitt(f.bas, ax, c).difference(unary_union([_snitt(t, ax, c) for t in f.verktyg]))
    if isinstance(f, Union):
        return unary_union([_snitt(d, ax, c) for d in f.delar])
    b = omslutande(f)
    if b is None or not (b[ax] < c < b[ax + 3]):
        return TOM
    if isinstance(f, Transf) and isinstance(f.form, Cylinder):
        axel = [f.placering.R[i][2] for i in range(3)]
        if abs(abs(axel[ax]) - 1.0) < 1e-9:                     # axeln vinkelrät mot planet: en cirkel
            o = f.placering.punkt(f.form.origo)
            return Point(o[ui], o[vi]).buffer(f.form.radie, 24)
    if isinstance(f, (Lada, Transf, Prisma, Cylinder)):
        return sbox(b[ui], b[vi], b[ui + 3], b[vi + 3])
    return TOM


def _polygoner(g: BaseGeometry) -> list[Polygon]:
    if g.is_empty:
        return []
    return [g] if isinstance(g, Polygon) else [p for p in getattr(g, "geoms", []) if isinstance(p, Polygon)]


def _rita_polygon(v: Vy, p: Polygon, fyll: str | None, stil: str,
                  T: Callable[[float, float], tuple[float, float]] = lambda u, w: (u, w)) -> None:
    v.polygon([T(*q) for q in list(p.exterior.coords)[:-1]], fyll, stil,
              hal=[[T(*q) for q in list(r.coords)[:-1]] for r in p.interiors])


def _vy(s: float, u0: float, v1: float, px: float, py: float) -> Vy:
    """Vy över hela bladet där modellpunkten (u0, v1) hamnar i papperets (px, py)."""
    return Vy(0.0, 0.0, 420.0, 297.0, s, u0 - px * s, v1 + py * s)


def _projektion(v: Vy, s: Skap, ax: int, djup: Callable[[tuple[float, ...]], float], utom: Sequence[str] = (),
                bara_bortom: tuple[int, float, int] | None = None) -> None:
    """Delarnas rätblock projicerade längs axeln ax, de bortersta först (djup: större är längre bort). bara_bortom
    (ax, c, tecken): bara rätblocken på ena sidan om snittplanet."""
    ui, vi = AXLAR[ax]
    lador = []
    for d in s.delar:
        if any(d.kod.startswith(u) for u in utom):
            continue
        for b in _lador(d.form):
            if bara_bortom:
                a, c, t = bara_bortom
                if (t < 0 and b[a + 3] > c + 1e-6) or (t > 0 and b[a] < c - 1e-6):
                    continue
            lador.append((djup(b), b, d))
    for _, b, d in sorted(lador, key=lambda x: -x[0]):
        v.rekt(b[ui], b[vi], b[ui + 3], b[vi + 3], fyll=FYLL.get(d.material), stil="fin")


def _snittvy(v: Vy, s: Skap, ax: int, c: float, T: Callable[[float, float], tuple[float, float]] = lambda u, w: (u, w)
             ) -> None:
    for d in s.delar:
        for p in _polygoner(_snitt(d.form, ax, c)):
            _rita_polygon(v, p, FYLL.get(d.material), "normal", T)


def _greppen(v: Vy, s: Skap, kk: ModuleType) -> None:
    for d in s.med("FRONT"):
        x0, _, _, x1, _, z1 = d.bb
        v.polygon(kk.grepp_lins(x0, x1, z1), None, "tunn")


# ------------------------------------------------------------------ tabeller


def _matt(b: Sequence[float]) -> str:
    """Delens mått, störst först: längd × bredd × tjocklek."""
    m = sorted((b[3] - b[0], b[4] - b[1], b[5] - b[2]), reverse=True)
    return " × ".join(svm(x) for x in m)


def _stomrader(s: Skap) -> list[list[str]]:
    n: Counter[tuple[str, str, str]] = Counter()
    for d in s.delar:
        if d.kod in STOMME:
            n[(STOMME[d.kod], _matt(d.bb), d.material)] += 1
    return [[namn, str(k), m, mat] for (namn, m, mat), k in n.items()]


def _frontrader(s: Skap) -> list[list[str]]:
    rader = []
    lador = set(s.lador)
    for d in sorted(s.med("FRONT"), key=lambda d: d.bb[2]):
        nr = d.kod[5:] or "–"
        slag = "dörr" if "dörr" in d.namn else "låda" if nr.isdigit() and int(nr) in lador else "fast"
        rader.append([nr, f"{svm(d.bb[3] - d.bb[0])} × {svm(d.bb[5] - d.bb[2])}", slag])
    return rader


def _ladrader(s: Skap, z_botten: float) -> list[list[str]]:
    rader = []
    for nr in s.lador:
        p = f"LADA{nr}-"
        sida, fram, bak, botten = (s.del_(p + k).bb for k in ("SIDA-V", "FRAM", "BAK", "BOTTEN"))
        nl = s.del_(p + "SKENA-V").namn.split("NL ")[-1]
        rader.append([str(nr), f"{svm(sida[4] - sida[1])} × {svm(sida[5] - sida[2])}",
                      f"{svm(fram[3] - fram[0])} × {svm(fram[5] - fram[2])}",
                      f"{svm(bak[3] - bak[0])} × {svm(bak[5] - bak[2])}",
                      f"{svm(botten[3] - botten[0])} × {svm(botten[4] - botten[1])}", nl,
                      svm(sida[2] - z_botten)])
    return rader


# ------------------------------------------------------------------ typens blad


def _typblad(nr: str, s: Skap, alla: list[Skap], kk: ModuleType) -> Blad:
    W = s.bredd
    z_golv, z_bot, z_tak = kk.SOCKEL, kk.SOCKEL + kk.T, kk.Z_TOPP - kk.T     # stommens underkant, bottnens ovansida
    D = kk.DJUP
    F = kk.FRONT_T
    fronter = s.med("FRONT")
    fx0, fx1 = min(d.bb[0] for d in fronter), max(d.bb[3] for d in fronter)
    xc = (fx0 + fx1) / 2                                    # snitt A–A mitt genom fronterna
    lador = s.lador
    top = max(lador) if lador else None
    if top:
        sida = s.del_(f"LADA{top}-SIDA-V").bb
        zc = (sida[2] + sida[5]) / 2                         # snitt B–B mitt genom den översta lådans sidor
    else:
        zc = (z_bot + kk.Z_TOPP) / 2 - 150.0
    H = kk.Z_TOPP
    gap = 30.0
    skala = next((sk for sk in SKALOR if VANSTER + (2 * W + D + F) / sk + 2 * gap <= 312.0), SKALOR[-1])
    xA = VANSTER
    xB = xA + W / skala + gap
    xC = xB + W / skala + gap
    yR = TOPP + 6.0
    vyer: list[Vy] = []
    # --- framifrån med fronterna
    a = _vy(skala, 0.0, H, xA, yR)
    with a.lager("delar"):
        a.linje([(-60.0, 0.0), (W + 60.0, 0.0)], "normal")
        _projektion(a, s, 1, lambda b: b[1])
        _greppen(a, s, kk)
        if s.med("GANGJARN"):                               # dörrens öppningssymbol: spetsen mot gångjärnen
            d0 = s.del_("FRONT").bb
            xg = sum((g.bb[0] + g.bb[3]) / 2 for g in s.med("GANGJARN")) / len(s.med("GANGJARN"))
            xh, xf = (d0[0], d0[3]) if abs(xg - d0[0]) < abs(xg - d0[3]) else (d0[3], d0[0])
            zm = (d0[2] + d0[5]) / 2
            a.linje([(xf, d0[5]), (xh, zm), (xf, d0[2])], "dold")
    with a.lager("text"):
        for d in fronter:
            n = d.kod[5:]
            if n:
                a.text((d.bb[0] + d.bb[3]) / 2, (d.bb[2] + d.bb[5]) / 2 - 20.0, n, a="cm", sz=6.5, col="gra")
    with a.lager("matt"):
        a.mattx([0.0, fx0, fx1, W], -6.0 * skala, [z_golv] * 4, sz=6.0)
        a.mattx([0.0, W], -12.0 * skala, [z_golv] * 2, sz=6.4)
        zs = sorted({round(z, 1) for d in fronter for z in (d.bb[2], d.bb[5])} | {H})
        a.matty([0.0, z_golv, H], -6.0 * skala, [0.0, z_golv, z_golv], sz=6.0)
        a.matty(zs, W + 6.0 * skala, [W] * len(zs), sz=5.6,
                texter=[svm(b - a_) if b - a_ > 30.0 else "" for a_, b in zip(zs[:-1], zs[1:])])
        a.text(-2.0 * skala, -1.5 * skala, "golv", a="rt", sz=5.6, i=True)
    a.rubrik(0.0, H + 9.0 * skala, "Framifrån", skala=None)
    vyer.append(a)
    # --- framifrån utan fronterna
    b_ = _vy(skala, 0.0, H, xB, yR)
    with b_.lager("delar"):
        _projektion(b_, s, 1, lambda b: b[1], utom=("FRONT", "GANGJARN"))
        for d in s.med("GANGJARN"):
            for q in _lador(d.form):
                b_.rekt(q[0], q[2], q[3], q[5], fyll="stal", stil="fin")
    with b_.lager("matt"):
        b_.mattx([0.0, kk.T, W - kk.T, W], -6.0 * skala, [z_golv] * 4, sz=6.0)
        if lador:
            sv = s.del_(f"LADA{lador[0]}-SIDA-V").bb
            sh = s.del_(f"LADA{lador[0]}-SIDA-H").bb
            b_.mattx([sv[0], sh[3]], -12.0 * skala, [z_golv] * 2, sz=6.0)
            zl = [z_bot] + [s.del_(f"LADA{n}-SIDA-V").bb[2] for n in lador]
            b_.matty(zl, W + 12.0 * skala, [W - kk.T] * len(zl), sz=5.6,
                     texter=[svm(q - p) if q - p > 30.0 else "" for p, q in zip(zl[:-1], zl[1:])])
        if s.med("HYLLA"):
            hy = s.del_("HYLLA").bb
            b_.matty([z_bot, hy[2], hy[5], z_tak], W + 12.0 * skala, [W - kk.T] * 4, sz=5.6)
    with b_.lager("text"):
        for kod, txt in (("BLINDFRONT", "blindfront"), ("HYLLA", "mellanhylla")):
            for d in s.med(kod):
                b_.text((d.bb[0] + d.bb[3]) / 2, d.bb[5] + 2.0 * skala, txt, a="cb", sz=6.2, b=True)
        for nr_ in lador:
            q = s.del_(f"LADA{nr_}-FRAM").bb
            b_.text((q[0] + q[3]) / 2, (q[2] + q[5]) / 2, f"låda {nr_}", a="cm", sz=6.2, b=True)
    b_.rubrik(0.0, H + 9.0 * skala, "Framifrån utan fronter", skala=None)
    vyer.append(b_)
    # --- snitt A–A från sidan (sett från höger: fronten till vänster, y åt höger)
    c = _vy(skala, -F, H, xC, yR)
    with c.lager("delar"):
        _projektion(c, s, 0, lambda b: -b[0], bara_bortom=(0, xc, -1))
        _snittvy(c, s, 0, xc)
        c.linje([(-F - 60.0, 0.0), (D + 60.0, 0.0)], "normal")
    with c.lager("matt"):
        ys = [-F, 0.0]
        if lador:
            ys.append(s.del_(f"LADA{lador[0]}-SIDA-V").bb[4])
        ys.append(D - kk.T)
        c.mattx(sorted(set(ys)), -6.0 * skala, [z_golv] * len(set(ys)), sz=5.6)
        c.mattx([0.0, D], -12.0 * skala, [z_golv] * 2, sz=6.0)
    c.rubrik(-F, H + 9.0 * skala, "Snitt A–A", skala=None)
    vyer.append(c)
    # snittmarkeringarna i vyn utan fronter
    with b_.lager("snitt"):
        b_.snittpil((xc, H + 4.0 * skala), (xc, z_golv / 2), "A", sida=-1)
        b_.snittpil((-3.0 * skala, zc), (W + 3.0 * skala, zc), "B", sida=-1)
    # --- snitt B–B i plan (fronten nedåt)
    yP = yR + H / skala + 42.0
    p = _vy(skala, 0.0, D, xA, yP)
    with p.lager("delar"):
        _projektion(p, s, 2, lambda b: -b[5], bara_bortom=(2, zc, -1))
        _snittvy(p, s, 2, zc)
    with p.lager("matt"):
        p.mattx([0.0, W], -F - 6.0 * skala, [-F] * 2, sz=6.0)
        p.matty([-F, 0.0, D - kk.T, D], W + 6.0 * skala, [W] * 4, sz=5.6)
        if lador:
            fr = s.del_(f"LADA{top}-FRAM").bb
            p.mattx([kk.T, W - kk.T], D + 5.0 * skala, [D - kk.T] * 2, sz=5.6)
            p.mattx([fr[0], fr[3]], D + 11.0 * skala, [fr[4]] * 2, sz=5.6)
            p.text(fr[3] + 2.0 * skala, D + 11.0 * skala, "SKW", a="lm", sz=5.4, i=True)
            p.text(W - kk.T + 2.0 * skala, D + 5.0 * skala, "LW", a="lm", sz=5.4, i=True)
    p.rubrik(0.0, D + 18.0 * skala, "Snitt B–B", skala=None)
    vyer.append(p)
    # --- detalj 1:2: löparen och lådans nedre vänstra hörn i den nedersta lådan, snitt mitt i lådans längd
    block: list[dict] = []
    if lador:
        sv = s.del_(f"LADA{lador[0]}-SIDA-V").bb
        bo = s.del_(f"LADA{lador[0]}-BOTTEN").bb
        yc = (sv[1] + sv[4]) / 2
        u0, u1, ned = DETALJ_FONSTER
        z0 = sv[2] - ned
        dx = xA + W / skala + gap
        dy = yP + 4.0
        w_, h_ = (u1 - u0) / DETALJ, DETALJ_HOJD / DETALJ
        d = Vy(dx, dy, w_, h_, DETALJ, u0, z0 + DETALJ_HOJD, klipp=True)
        with d.lager("delar"):
            _snittvy(d, s, 1, yc)
        with d.lager("matt"):
            xi = sv[3]
            d.mattx([kk.T, sv[0], xi], sv[2] + 48.0, [sv[2] + 40.0] * 3, sz=5.4)
            d.mattx([xi - kk.SPAR, xi], bo[5] + 9.0, [bo[5]] * 2, sz=5.4)
            zk = [sv[2] - kk.LOPARE_H, sv[2], bo[2], bo[5]]
            d.matty(zk, u1 - 6.0, [xi] * 4, sz=5.4)
            d.matty([z_bot, sv[2]], u0 + 4.0, [kk.T] * 2, sz=5.4)
        with d.lager("text"):
            d.text(kk.T / 2, sv[2] + 30.0, f"stomme {svm(kk.T)}", a="cm", sz=5.0, rot=90, bg=True)
            d.text((sv[0] + xi) / 2, sv[2] + 30.0, f"lådsida {svm(kk.T_LADA)}", a="cm", sz=5.0, rot=90, bg=True)
            d.hanvisning((xi + 12.0, bo[2] + 2.0), (xi + 14.0, bo[5] + 22.0), f"botten {svm(kk.T_BOTTEN)}", a="lm",
                         sz=5.0)
            d.hanvisning((xi + 4.0, sv[2] - 4.0), (xi + 14.0, sv[2] - 22.0), "löpare", a="lm", sz=5.0)
        vyer.append(d)
        block.append(dict(x=dx, y=dy - 6.5, w=60.0, innehall=[
            dict(typ="text", rader=[f"Detalj, låda {lador[0]}, 1:2"], sz=7.0)]))
    # --- tabellerna: lådorna på ritytan, stommen, fronterna och beslagen i kolumnen
    if lador:
        bx = xA + W / skala + gap + (DETALJ_FONSTER[1] - DETALJ_FONSTER[0]) / DETALJ + 12.0
        block.append(dict(x=bx, y=yP - 2.0, w=326.0 - bx - 2.0, innehall=[
            dict(typ="rubrik", text="Lådorna (massiv björk 14, botten björkplywood 4)"),
            dict(typ="tabell", kolumner=["Låda", "Sidor, 2 st", "Framstycke", "Bakstycke", "Botten", "NL",
                                         "Löpare ök"],
                 bredd=(0.45, 0.9, 0.9, 0.9, 0.9, 0.4, 0.6), just=["c", "c", "c", "c", "c", "c", "c"], sz=6.0,
                 rader=_ladrader(s, z_bot)),
            dict(typ="text", sz=6.0, rader=[
                "Sidorna längd × höjd; framstycket och bakstycket bredd × höjd; bottnen bredd × djup. Löpare ök: "
                "löparens överkant (sidans underkant) över skåpbottnens ovansida."])]))
    positioner = [x.kod for x in alla if x.typ == s.typ]
    nl = sorted({d.namn.split("NL ")[-1] for d in s.med("LADA") if "SKENA" in d.kod})
    beslag = []
    if lador:
        beslag.append([f"Löpare Blum MOVENTO 760H, NL {', '.join(nl)}, par", str(len(lador))])
        beslag.append(["Kopplingar Blum T51.7601, par", str(len(lador))])
    if s.med("GANGJARN"):
        beslag.append(["Gångjärn Blum CLIP top BLUMOTION 110°", str(len(s.med("GANGJARN")))])
    skruvar = []
    for n in nl:
        hal = kk.LOPARENS_SKRUVAR.get(float(n))
        if hal:
            skruvar.append(f"NL {n}: " + ", ".join(svm(h) for h in hal))
    kol: list[dict] = [
        dict(typ="rubrik", text=f"{s.typ}: {s.typnamn.lower()}"),
        dict(typ="lista", sz=6.8, rader=[
            f"Antal {len(positioner)}: {', '.join(positioner)} (översikten {SERIE}.1).",
            f"Stommen {svm(W)} × {svm(D)} × {svm(kk.Z_TOPP - kk.SOCKEL)} (bredd × djup × höjd) av björkplywood "
            f"{svm(kk.T)}, från sparklisten {svm(kk.SOCKEL)} till bänkskivans underkant {svm(kk.Z_TOPP)}.",
            f"Fronterna av fräst ask {svm(F)}, {svm(kk.OVER_SIDAN)} mm in över stommens sidor, {svm(kk.SPEL)} mm "
            "spel mellan fronterna och under bänkskivan; lådorna och fronterna numrerade nedifrån.",
            *([f"Lådorna på Blum MOVENTO: SKW = LW − {svm(kk.SKW_AVDRAG)}, SKL = NL − {svm(kk.SKL_AVDRAG)}, bottnen "
               f"{svm(kk.URTAG)} över sidornas underkant; hålet för löparens hake Ø{svm(kk.HAKE[0])} × "
               f"{svm(kk.HAKE[1])} i sidans bakände, {svm(kk.HAKE[2])} från utsidan och {svm(kk.HAKE[3])} upp. "
               "Kopplingarna skruvas 75° in i framstycket (borrmall T65.1000.02)."] if lador else []),
            *([f"Löparens skruvhål från stommens framkant (TD-132/1 s. 13), {'; '.join(skruvar)}."]
              if skruvar else []),
            *([f"Gångjärnen: koppen Ø{svm(kk.KOPP[0])} × {svm(kk.KOPP[1])}, mitten {svm(kk.KOPP[2])} från dörrens "
               f"kant, {svm(kk.GANGJARN_KANT)} från dörrens över- och underkant."] if s.med("GANGJARN") else []),
            "Mått i mm. Ritas ur modellens skåp (./mod kok ritning).",
        ]),
        dict(typ="rubrik", text="Stommen"),
        dict(typ="tabell", kolumner=["Del", "St", "Mått", "Material"], bredd=(1.25, 0.3, 1.3, 1.0),
             just=["l", "c", "l", "l"], sz=6.0, rader=_stomrader(s)),
        dict(typ="rubrik", text="Fronterna (ask 22)"),
        dict(typ="tabell", kolumner=["Nr", "Bredd × höjd", "Slag"], bredd=(0.4, 1.4, 0.8), just=["c", "l", "l"],
             sz=6.0, rader=_frontrader(s)),
        *([dict(typ="rubrik", text="Beslag per skåp"),
           dict(typ="tabell", kolumner=["Beslag", "St"], bredd=(2.6, 0.35), just=["l", "c"], sz=6.0,
                rader=beslag)] if beslag else list[dict]()),
    ]
    return blad(nr, ["Köksskåp", f"{s.typ}, {s.typnamn.lower()} {svm(W)}"], f"1:{skala:g}, 1:2", "Modellen", kol,
                vyer, block)


# ------------------------------------------------------------------ översikten


def _hus(s: Skap, b: Sequence[float]) -> list[tuple[float, float, float]]:
    return [s.placering.punkt((x, y, z)) for x in (b[0], b[3]) for y in (b[1], b[4]) for z in (b[2], b[5])]


def _oversikt(alla: list[Skap], losa: list[tuple[str, str, str, tuple[float, ...], Form]], kb: ModuleType,
              kk: ModuleType, bladnr: dict[str, str]) -> Blad:
    skap = [s for s in alla]
    # planen 1:50, K-05:s x åt höger och y uppåt
    ps = 50.0
    P = [q for s in skap for d in s.delar for b in _lador(d.form) for q in _hus(s, b)]
    X0, X1 = min(q[0] for q in P), max(q[0] for q in P)
    Y0, Y1 = min(q[1] for q in P), max(q[1] for q in P)
    vp = _vy(ps, X0, Y1 + 400.0, 34.0, TOPP + 8.0)
    with vp.lager("vaggar"):
        vp.linje([(kb.X_VAGG, kb.K_YTA), (kb.X_VAGG, kb.Y_SYD), (X0 - 100.0, kb.Y_SYD)], "kontur")
        vp.text(kb.X_VAGG + 2.0 * ps, (kb.K_YTA + kb.Y_SYD) / 2, "3NV", a="cm", sz=6.0, rot=90, col="gra")
        vp.text(X0 + 300.0, kb.Y_SYD + 2.0 * ps, "3SV", a="cm", sz=6.0, col="gra")
    with vp.lager("delar"):
        for kod, _, mat, b, f in losa:
            if kod.endswith("SKIVA"):
                kontur = f.kontur if isinstance(f, Prisma) else [(b[0], b[1]), (b[3], b[1]), (b[3], b[4]),
                                                                    (b[0], b[4])]
                vp.polygon(list(kontur), None, "dold")
            else:
                vp.rekt(b[0], b[1], b[3], b[4], fyll=FYLL.get(mat, "vit"), stil="fin")
        for s in skap:
            for d in s.delar:
                if d.kod.startswith("LADA") or d.kod.startswith("GANGJARN"):
                    continue
                for b in _lador(d.form):
                    H = _hus(s, b)
                    xs, ys = [q[0] for q in H], [q[1] for q in H]
                    vp.rekt(min(xs), min(ys), max(xs), max(ys), fyll=FYLL.get(d.material), stil="fin")
    with vp.lager("text"):
        for s in skap:
            q = s.placering.punkt((s.bredd / 2, kk.DJUP / 2, 0.0))
            vp.text(q[0], q[1] + 1.4 * ps, s.kod, a="cm", sz=7.0, b=True, bg=True)
            vp.text(q[0], q[1] - 1.6 * ps, s.typ if s.typ != "–" else "DM", a="cm", sz=6.0, bg=True)
    vp.rubrik(X0, Y1 + 400.0 + 6.0 * ps, "Plan", skala=50)
    # fronterna i elevation 1:25, bänken längs 3NV sedd västerifrån, längs 3SV norrifrån och ön österifrån
    es = 25.0
    leder = (("Bänken längs 3NV, sedd från väster", lambda s: s.kod in {f"B{i}" for i in range(1, 8)},
              lambda b: abs(b[0] - kb.X_FRONT) < 1.0),
             ("Bänken längs 3SV, sedd från norr", lambda s: s.kod in {f"B{i}" for i in range(8, 11)},
              lambda b: abs(b[1] - kb.Y_FRONT) < 1.0),
             ("Ön, sedd från öster", lambda s: s.kod.startswith("O"), lambda b: abs(b[3] - kb.X_ON_FRONT) < 1.0))
    vyer = [vp]
    ex = 34.0 + (X1 - X0) / ps + 22.0
    lagen = [(ex, TOPP + 8.0)]                              # 3NV överst, 3SV och ön under den, bredvid varandra
    for i, (titel, valj, los) in enumerate(leder):
        sk = [s for s in skap if valj(s)]
        # sedd framifrån som skåpen: skåpens x (från vänster sett framifrån) åt höger på papperet
        r = sk[0].placering.riktning((1.0, 0.0, 0.0))
        assert all(max(abs(a_ - b_) for a_, b_ in zip(x.placering.riktning((1.0, 0.0, 0.0)), r)) < 1e-9 for x in sk)

        def U(q: Sequence[float], r: Sequence[float] = r) -> float:
            return q[0] * r[0] + q[1] * r[1]
        lo = [x for x in losa if los(x[3]) and not x[0].endswith("SKIVA") and "SPARK" not in x[0]]

        def u_av(b: Sequence[float], U: Callable = U) -> tuple[float, float]:
            us = [U((x, y, 0.0)) for x in (b[0], b[3]) for y in (b[1], b[4])]
            return min(us), max(us)

        spann = [u_av(x[3]) for x in lo] + [u_av(_bb_placerad(d.bb, s.placering)) for s in sk for d in s.med("FRONT")]
        u0, u1 = min(a for a, _ in spann), max(b for _, b in spann)
        px, py = lagen[i]
        v = _vy(es, u0, kk.Z_TOPP, px, py)
        with v.lager("delar"):
            v.linje([(u0 - 100.0, 0.0), (u1 + 100.0, 0.0)], "normal")
            for x in lo:
                ua, ub = u_av(x[3])
                v.rekt(ua, x[3][2], ub, x[3][5], fyll=FYLL.get(x[2], "vit"), stil="fin")
            for s in sk:
                for d in s.med("FRONT"):
                    ua, ub = u_av(_bb_placerad(d.bb, s.placering))
                    v.rekt(ua, d.bb[2], ub, d.bb[5], fyll="vit", stil="tunn")
                    lins = kk.grepp_lins(d.bb[0], d.bb[3], d.bb[5])
                    v.polygon([(U(s.placering.punkt((x, d.bb[1], 0.0))), z) for x, z in lins], None, "fin")
        with v.lager("text"):
            for s in sk:
                um = sum(u_av(_bb_placerad(d.bb, s.placering))[0] + u_av(_bb_placerad(d.bb, s.placering))[1]
                         for d in s.med("FRONT")[:1]) / 2
                v.text(um, -3.0 * es, f"{s.kod} · {s.typ if s.typ != '–' else 'DM'}", a="ct", sz=6.4, b=True)
        v.rubrik(u0, kk.Z_TOPP + 4.0 * es, titel, skala=None, sz=8)
        vyer.append(v)
        if i == 0:
            lagen.append((ex, py + kk.Z_TOPP / es + 26.0))
        elif i == 1:
            lagen.append((px + (u1 - u0) / es + 18.0, py))
    # förteckningen över typerna och askbrädorna
    typer: dict[str, list[Skap]] = {}
    for s in skap:
        if s.typ != "–":
            typer.setdefault(s.typ, []).append(s)
    rader = []
    for t, sk in typer.items():
        s = sk[0]
        n = len(s.lador)
        innehall = f"{n} lådor" if n else ("dörr, mellanhylla" if s.med("HYLLA") else "–")
        if s.med("SKIVA"):
            innehall += f", {len(s.med('FRONT')) - n} fasta fronter"
        rader.append([t, s.typnamn, f"{svm(s.bredd)} × {svm(kk.DJUP)} × {svm(kk.Z_TOPP - kk.SOCKEL)}", innehall,
                      str(len(sk)), ", ".join(x.kod for x in sk), bladnr[t]])
    dm = [s for s in skap if s.typ == "–"]
    for s in dm:
        fb = s.del_("FRONT").bb
        rader.append(["DM", "Diskmaskin (integrerad 60)", f"front {svm(fb[3] - fb[0])} × {svm(fb[5] - fb[2])}", "–",
                      "1", s.kod, "–"])
    brador: Counter[tuple[str, str]] = Counter()
    for kod, namn, mat, b, _ in losa:
        if mat == "Ask" and "SPARK" not in kod:
            brador[(namn.split(" ask")[0].split(" ")[0], _matt(b))] += 1
    yb = 165.0
    block = [
        dict(x=34.0, y=yb, w=200.0, innehall=[
            dict(typ="rubrik", text="Skåptyperna"),
            dict(typ="tabell", kolumner=["Typ", "Benämning", "Stomme b × d × h", "Innehåll", "Antal", "Positioner",
                                         "Blad"],
                 bredd=(0.4, 1.15, 1.15, 1.25, 0.4, 1.3, 0.55), just=["c", "l", "l", "l", "c", "l", "c"], sz=6.2,
                 rader=rader)]),
        dict(x=240.0, y=yb, w=84.0, innehall=[
            dict(typ="rubrik", text="Askbrädor mellan och vid skåpen"),
            dict(typ="tabell", kolumner=["Bräda", "Mått", "St"], bredd=(1.0, 1.3, 0.3), just=["l", "l", "c"],
                 sz=6.2, rader=[[n, m, str(k)] for (n, m), k in sorted(brador.items())])]),
    ]
    kol: list[dict] = [
        dict(typ="rubrik", text="Anvisningar"),
        dict(typ="lista", sz=7.0, rader=[
            "Köksskåpen i bänken och ön. Positionerna: B1–B10 längs bänken från kökets inbyggnad (B1–B7 längs 3NV "
            "söderut, B8–B10 längs 3SV västerut) och O1–O3 på ön norrifrån.",
            "Skåp med samma delar är samma typ (KS1 …); varje typ har ett eget blad med stommen, fronterna, lådorna "
            "och beslagen. DM: diskmaskinen med sin front.",
            "Skåpen ställs på ben; sparklisten (ask 16, 60 mm innanför fronterna) och bänkskivan (streckad i "
            "planen) ingår inte i skåpen.",
            "Mellan skåpen fogbrädor av ask 22 × 22 över fogen, 3 mm från fronterna; i hörnet ett hörnstycke av två "
            "brädor i vinkel, med benen minst 22 utanför den andra bänkens fronter, så att lådorna och dörren går "
            "fritt från handtag som sticker ut upp till 20 mm.",
            "Skåpen är hela mm breda; brädan mot kökets inbyggnad och hörnstyckets bräda längs 3NV tar upp resten "
            "och passas in på plats.",
            "Mått i mm. Ritas ur modellens skåp (./mod kok ritning).",
        ]),
    ]
    return blad(f"{SERIE}.1", ["Köksskåp", "Översikt, positioner och typer"], "1:50, 1:25", "Modellen", kol, vyer,
                block)


# ------------------------------------------------------------------ serien


def ritningar(kb: ModuleType, kk: ModuleType, mapp: Path, pdf: Path) -> Path:
    bank, on = kb.bank(), kb.on()
    alla = skapen(bank, on)
    losa = []
    for m in (bank, on):
        for i in m.barn:
            if not isinstance(i.barn, Montage):
                bb = omslutande(i.barn.form)
                assert bb is not None
                lp = i.placering
                lb = bb if lp.ar_identitet() else _bb_placerad(bb, lp)
                losa.append((i.namn, i.barn.namn, i.barn.material.namn, lb, i.barn.form))
    typer = sorted({s.typ for s in alla if s.typ != "–"}, key=lambda t: int(t[2:]))
    bladnr = {t: f"{SERIE}.{k + 2}" for k, t in enumerate(typer)}
    bladen = [(f"{SERIE}.1", _oversikt(alla, losa, kb, kk, bladnr))]
    for t in typer:
        s = next(x for x in alla if x.typ == t)
        bladen.append((bladnr[t], _typblad(bladnr[t], s, alla, kk)))
    kompilera(bladen, mapp, pdf)
    return pdf


def _bb_placerad(b: Sequence[float], p: Placering) -> tuple[float, ...]:
    H = [p.punkt((x, y, z)) for x in (b[0], b[3]) for y in (b[1], b[4]) for z in (b[2], b[5])]
    return (min(q[0] for q in H), min(q[1] for q in H), min(q[2] for q in H),
            max(q[0] for q in H), max(q[1] for q in H), max(q[2] for q in H))


__all__ = ["SERIE", "TITEL", "ritningar", "skapen"]
