"""Innertaket (F-01): ångbroms, installationsskikt (utan isolering, U-03; skikt.ULL_I_INNERTAKET) och gips 2 × 12,5
under takbalkarna; i badrummet (BADRUM) är den
yttre skivan en spontad panel av gran, vitmålad, med brädorna längs takfallet (ärende #52).

Innertaket följer takfallen (snedtak) från ytterväggens insida upp till nocken, och ned till dallinjen där takfallet
slutar vid en dalbalk, med uppehåll vid mittstolen och öppningar för takfönstren. Under taket: korslagd läkt 45
(F-01), med en läkt längs takfallet vid gavlarna bakom gipsens kant, och gips 2 × 12,5. Den yttre gipsskivan går fri
under nock- och dalbalkarna och möter grannfallets i en skarp linje i nocken och under dalbalkarna; ångbromsen,
läkten och den inre gipsskivan slutar vid balkarna. Väggar, stolpar och strävor som står under innertaket går skikten
runt, och vid gavlarna slutar innertaket mot gavelns insida (vagginsida.py).
"""
from __future__ import annotations

from functools import cache

from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

from modellering import Montage

from trebodar import skelett as S
from trebodar.byggdelar import taklager as L
from trebodar.byggdelar.polygon import polygoner
from trebodar.byggdelar.regelvagg import Plan
from trebodar.hus.stomme import lagen
from trebodar.hus.stomme.prefab.takbalkar.takbalkar import FALT, balkens_sida
from trebodar.hus.rum import BADRUM
from trebodar.material import ANGBROMS, C24_LAKT, GIPS, MINERALULL, TAKPANEL

from .skikt import GIPS_INRE_W, GIPS_YTTRE_W, LAKT, LAKT_W, TAK_W, ULL_I_INNERTAKET, insida_vanlig_t
from .vagginsida import badrumsremsor, insidans_plan

CC = 400.0
FRI = 5.0                  # gipsens avstånd till stolpar, strävor och väggar som går genom innertaket


def _fritt_under_balkarna() -> float:
    """Minsta avstånd mellan innertakets yttre gipsskiva och nock- och dalbalkarnas underkant: i nocken är skivan
    högst i nocklinjen, vid en dalbalk vid balkens underkant på takfallets sida."""
    ut = []
    for kod, f in FALT.items():
        t = S.TAKFALL[kod]
        for b in (S.BALKAR[k] for k in (f.nock, f.dal) if k):
            x = b.x if b.typ == "nock" else b.x + t.riktning * S.BALK_B / 2
            ut.append(b.uk - (t.z_overkant(x) + GIPS_YTTRE_W[1] / S.COS))
    return min(ut)


assert _fritt_under_balkarna() >= FRI, "innertakets yttre gipsskiva går inte fri under nock- och dalbalkarna"


def _hinder_tak(t: S.Takfall, x_lo: float, x_hi: float) -> list[tuple[float, float, float, float, str]]:
    """Väggar och stolpar som når upp till innertaket i takfallet (mellan x_lo och x_hi), som (x0, x1, y0, y1, slag)
    per grupp: delar som går över gipsens underkant där innertaket är lägst ovanför dem. Slaget är "vägg", "stolpe"
    eller "skikt" (en ytterväggs insida). Takfotsväggen räknas inte (innertaket går över den)."""
    lador: dict[str, list[float]] = {}
    for d in lagen.prefab():
        x0, y0, _, x1, y1, z1 = d.lada
        if d.element == t.kod or not (x0 < x_hi and x_lo < x1):
            continue
        x = max(x0, x_lo) if t.riktning > 0 else min(x1, x_hi)           # där innertaket är lägst över delen
        if z1 <= t.z_overkant(x) + GIPS_YTTRE_W[0] / S.COS + 1.0:
            continue
        g = lador.setdefault(d.element, [x0, x1, y0, y1])
        g[:] = [min(g[0], x0), max(g[1], x1), min(g[2], y0), max(g[3], y1)]
    stolpar = {d.element for d in lagen.stolpar()}
    ut = [(g[0], g[1], g[2], g[3], "stolpe" if k in stolpar else "vägg") for k, g in lador.items()]
    # en ytterväggs insida går upp genom innertaket med väggen (en gavel som går förbi en dal under grannkroppens
    # takfall); innertaket möter skikten utan avstånd
    for k in lador:
        if k in S.YTTERVAGGAR:
            x0, y0, x1, y1 = insidans_plan(k).bounds
            ut.append((x0, x1, y0, y1, "skikt"))
    return ut


def _med_fri(hinder: list[tuple[float, float, float, float, str]]) -> list[tuple[float, float, float, float]]:
    """Hindren med gipsens avstånd: FRI längs x för väggar och stolpar, för stolpar också längs y."""
    return [(x0 - fx, x1 + fx, y0 - fy, y1 + fy) for x0, x1, y0, y1, slag in hinder
            for fx, fy in ((0.0 if slag == "skikt" else FRI, FRI if slag == "stolpe" else 0.0),)]


def _utan_hinder(k0: L.Kant, k1: L.Kant, s0: float, s1: float,
                 hinder: list[tuple[float, float, float, float]]) -> list[tuple[float, float, L.Kant, L.Kant]]:
    """Skiktets bitar mellan kanterna och y = s0 … s1 utanför hindren (x0, x1, y0, y1): (y0, y1, kant, kant)."""
    kl, kh = sorted((k0, k1), key=lambda k: k.x)
    ys = sorted({s0, s1} | {y for x0, x1, y0, y1 in hinder for y in (y0, y1)
                            if s0 < y < s1 and x0 < kh.x and kl.x < x1})
    ut = []
    for a, b in zip(ys, ys[1:]):
        intervall = [(kl.x, kh.x)]
        for x0, x1, y0, y1 in hinder:
            if y0 < b and a < y1:
                intervall = [d for xa, xb in intervall for d in ((xa, min(xb, x0)), (max(xa, x1), xb))
                             if d[1] - d[0] > 1.0]
        for xa, xb in intervall:
            ut.append((a, b, kl if xa == kl.x else L.Kant("lodratt", xa), kh if xb == kh.x else L.Kant("lodratt", xb)))
    return ut


def _strackor(kod: str) -> list[list[float]]:
    """Innertakets sträckor i y mellan gavlarnas insidor: facken ihopslagna över takbalkar och innerväggar (där
    väggarna står går skikten runt dem), men inte över mittstolen 2C (takstol med toppklossar)."""
    t = S.TAKFALL[kod]
    band = sorted([(y, y + S.TAKBALK_B) for y in FALT[kod].y] +
                  [(v.origo[1], v.origo[1] + v.tjocklek) for k, v in S.INNERVAGGAR.items()
                   if int(k[0]) == t.kropp and abs(v.u[0]) > 0.5 and k not in lagen.TAKSTOLSVAGGAR
                   and lagen.under_takfallet(k, kod)])
    tackt: list[list[float]] = []
    for a, b in band:
        if tackt and a <= tackt[-1][1] + 1e-6:
            tackt[-1][1] = max(tackt[-1][1], b)
        else:
            tackt.append([a, b])
    ut: list[list[float]] = []
    for y0, y1 in lagen.fack(kod):
        if ut and (y0 - ut[-1][1] <= S.TAKBALK_B + 1e-6 or
                   any(a <= ut[-1][1] + 1e-6 and y0 <= b + 1e-6 for a, b in tackt)):
            ut[-1][1] = y1
        else:
            ut.append([y0, y1])
    # vid gavlarna slutar innertaket vid gavelväggens insida (ångbroms, läkt och skivor; 1SV utan läkt)
    if ut:
        g0, g1 = lagen.GAVELVAGGAR[t.kropp]
        ut[0][0] += insida_vanlig_t(g0)
        ut[-1][1] -= insida_vanlig_t(g1)
    return ut


def _badrummet(s0: float, s1: float, k0: L.Kant, k1: L.Kant) -> list[tuple[float, float, L.Kant, L.Kant, bool]]:
    """Bitens delar i och utanför badrummet: (y0, y1, kant, kant, i badrummet), delad längs y vid badrummets hörn och
    lodrätt vid dess kanter (väggarnas mitt, BADRUM)."""
    kl, kh = sorted((k0, k1), key=lambda k: k.x)
    ys = sorted({s0, s1} | {y for _, y in BADRUM.exterior.coords if s0 < y < s1})
    ut = []
    for a, b in zip(ys, ys[1:]):
        g = BADRUM.intersection(LineString([(kl.x - 1.0, (a + b) / 2), (kh.x + 1.0, (a + b) / 2)]))
        inne = sorted((max(min(xs), kl.x), min(max(xs), kh.x)) for q in getattr(g, "geoms", [g]) if not q.is_empty
                      for xs in ([x for x, _ in q.coords],))
        x, kant = kl.x, kl
        for xa, xb in inne:
            if xb - xa < 1.0:
                continue
            if xa > x + 1.0:
                ut.append((a, b, kant, L.Kant("lodratt", xa), False))
                kant = L.Kant("lodratt", xa)
            slut = kh if xb >= kh.x - 1.0 else L.Kant("lodratt", xb)
            ut.append((a, b, kant, slut, True))
            x, kant = xb, slut
        if x < kh.x - 1.0:
            ut.append((a, b, kant, kh, False))
    return ut


Profil = tuple[tuple[tuple[float, float], ...], float, float, str]
MATERIAL = {"folie": ANGBROMS, "gips": GIPS, "lakt": C24_LAKT, "panel": TAKPANEL, "isolering": MINERALULL}


@cache
def skikten(kod: str) -> dict[str, tuple[Profil, ...]]:
    """Innertakets skikt under takfallet som profiler, utan delar: (profilens punkter (x, z), y0, y1, typ) per bit,
    för ångbromsen ("folie"), gipsen ("gips") och installationsskiktets läkt ("lakt"), i byggordning. Delarna byggs
    av takfall; elinstallationen läser läkten härifrån (armaturerna mellan läkten). I badrummet är den yttre skivan
    panel ("panel"). "isolering" är mineralullen i facken mellan läkten, om skiktet isoleras (skikt.py)."""
    t = S.TAKFALL[kod]
    f = FALT[kod]
    ut: dict[str, list[Profil]] = {"folie": [], "gips": [], "lakt": [], "panel": [], "isolering": []}

    def lagg(skikt: str, q: list[tuple[float, float]], a: float, b: float, typ: str) -> None:
        ut[skikt].append((tuple((float(x), float(z)) for x, z in q), float(a), float(b), typ))
    # ångbromsen, läkten och den inre gipsskivan slutar 10 mm från nockbalken och vid dalbalkens upplagsregel; den yttre
    # gipsskivan går till nocklinjen och dallinjen, där den möter grannfallets
    ovre = L.Kant("lodratt", balkens_sida(f.nock, t) - t.riktning * 10.0)
    ovre_g = L.Kant("lodratt", S.BALKAR[f.nock].x)
    dal = S.BALKAR[f.dal] if f.dal else None
    hinder = _hinder_tak(t, *sorted((min(t.x_insida, dal.x) if dal and t.riktning > 0 else
                                     max(t.x_insida, dal.x) if dal else t.x_insida, ovre_g.x)))
    hinder += [(*b, "vägg") for b in badrumsremsor(t)]
    hinder_s = [h[:4] for h in hinder]                     # ångbroms och läkt: mot hindren
    hinder_g = _med_fri(hinder)                            # gips: med avstånd
    strackor = _strackor(kod)
    gavlar = {strackor[0][0], strackor[-1][1]} if strackor else set()
    for y0, y1 in strackor:
        # vid gavlarna en läkt längs takfallet bakom innertakets gipskant (mot sprickor i hörnet mot gaveln)
        spik = [(ya, ya + LAKT) for ya in (y0,) if ya in gavlar] + [(yb - LAKT, yb) for yb in (y1,) if yb in gavlar]
        delar = [(y0, y1)]
        if dal and y0 < dal.y0 < y1:
            delar = [(y0, dal.y0), (dal.y0, y1)]
        if dal and y0 < dal.y1 < y1:
            delar = [d for a, b in delar for d in (((a, dal.y1), (dal.y1, b)) if a < dal.y1 < b else ((a, b),))]
        for a, b in delar:
            ym = 0.5 * (a + b)
            vid_dal = dal is not None and dal.y0 <= ym <= dal.y1
            nedre = L.Kant("lodratt", balkens_sida(dal.kod, t) + t.riktning * 45.0 if dal and vid_dal else t.x_insida)
            nedre_g = L.Kant("lodratt", dal.x) if dal and vid_dal else nedre
            # fönsteröppningar: skikten skärs vinkelrätt vid öppningens kanter
            snitt = [(a, b, (nedre, ovre), (nedre_g, ovre_g))]
            for fo in f.fonster:
                if a < fo.y0 and fo.y1 < b:
                    kn = L.Kant("vinkelrat", fo.x_ned)
                    ku = L.Kant("vinkelrat", fo.x_upp)
                    snitt = [(a, fo.y0, (nedre, ovre), (nedre_g, ovre_g)), (fo.y0, fo.y1, (nedre, kn), (nedre_g, kn)),
                             (fo.y0, fo.y1, (ku, ovre), (ku, ovre_g)), (fo.y1, b, (nedre, ovre), (nedre_g, ovre_g))]
            for s0, s1, (k0, k1), (g0, g1) in snitt:
                for sa, sb, ka, kb in _utan_hinder(k0, k1, s0, s1, hinder_s):
                    q = L.profil(t, *TAK_W, ka, kb)
                    if q:
                        lagg("folie", q, sa, sb, "AB")
                for (ga0, ga1), w, typ in (((k0, k1), GIPS_INRE_W, "GI"), ((g0, g1), GIPS_YTTRE_W, "GY")):
                    for sa, sb, ga, gb in _utan_hinder(ga0, ga1, s0, s1, hinder_g):
                        i_bad = _badrummet(sa, sb, ga, gb) if typ == "GY" else [(sa, sb, ga, gb, False)]
                        for ya, yb, ka, kb, bad in i_bad:
                            q = L.profil(t, *w, ka, kb)
                            if q:
                                lagg("panel" if bad else "gips", q, ya, yb, "PA" if bad else typ)
                # installationsskiktets läkt längs y, c/c 400 längs takfallet, avbruten vid hindren
                q = L.profil(t, *LAKT_W, k0, k1)
                if not q:
                    continue
                for c, e in spik:
                    if s0 <= c and e <= s1:
                        for sa, sb, ka, kb in _utan_hinder(k0, k1, c, e, hinder_s):
                            qs = L.profil(t, *LAKT_W, ka, kb)
                            if qs:
                                lagg("lakt", qs, sa, sb, "IL")
                ls0 = max([s0] + [e for c, e in spik if c <= s0 + 1e-6])
                ls1 = min([s1] + [c for c, e in spik if e >= s1 - 1e-6])
                ys = Polygon(q)
                x_lo, x_hi = ys.bounds[0], ys.bounds[2]
                langd = (x_hi - x_lo) / S.COS
                n = int(langd // CC)
                tackt: list[Polygon] = []                 # läktens och mineralullens profiler i skiktet
                for i in range(n + 1):
                    s = min(i * CC, langd - LAKT)
                    # läktens läge: s mm upp längs planet från den nedre kanten
                    x_start = x_lo if t.riktning > 0 else x_hi
                    xa = x_start + t.riktning * s * S.COS
                    xb = x_start + t.riktning * (s + LAKT) * S.COS
                    pl = L.profil(t, *LAKT_W, L.Kant("vinkelrat", min(xa, xb)), L.Kant("vinkelrat", max(xa, xb)))
                    if not pl:
                        continue
                    lp = Polygon(pl).intersection(ys)
                    if lp.area <= 100:
                        continue
                    tackt.append(lp)
                    bx0, bx1 = lp.bounds[0], lp.bounds[2]
                    bitar = [(ls0, ls1)]
                    for hx0, hx1, hy0, hy1 in hinder_s:
                        if hx0 < bx1 and bx0 < hx1:
                            bitar = [d for c, e in bitar for d in ((c, min(e, hy0)), (max(c, hy1), e))
                                     if d[1] - d[0] > 1.0]
                    for c, e in bitar:
                        lagg("lakt", [(float(x), float(z)) for x, z in list(lp.exterior.coords)[:-1]], c, e, "IL")
                # mineralull i skiktet utom läkten, om skiktet isoleras: facken mellan läkten och skiktets ändar,
                # avbruten vid hindren som läkten
                for fp in (polygoner(ys.difference(unary_union(tackt).buffer(1e-6)), 45.0 * 20.0)
                           if ULL_I_INNERTAKET else ()):
                    bx0, bx1 = fp.bounds[0], fp.bounds[2]
                    bitar = [(ls0, ls1)]
                    for hx0, hx1, hy0, hy1 in hinder_s:
                        if hx0 < bx1 and bx0 < hx1:
                            bitar = [d for c, e in bitar for d in ((c, min(e, hy0)), (max(c, hy1), e))
                                     if d[1] - d[0] > 1.0]
                    for c, e in bitar:
                        lagg("isolering", [(float(x), float(z)) for x, z in list(fp.exterior.coords)[:-1]], c, e, "II")
    return {k: tuple(v) for k, v in ut.items()}


def takfall(kod: str) -> Montage:
    m = Montage(f"Innertak {kod}", beskrivning="Ångbroms, installationsskikt 45" +
                (" med mineralull" if ULL_I_INNERTAKET else "") + " och gips 2 × 12,5 under takbalkarna (i badrummet "
                "gips och panel)")
    lager = {"folie": Plan(kod, f"Ångbroms tak {kod}", 1.0, material=ANGBROMS),
             "lakt": Plan(kod, f"Installationsskikt tak {kod}", LAKT, material=C24_LAKT),
             "isolering": Plan(kod, f"Isolering i installationsskiktet tak {kod}", LAKT, material=MINERALULL),
             "gips": Plan(kod, f"Gips tak {kod}", 1.0, material=GIPS),
             "panel": Plan(kod, f"Panel tak {kod}", 1.0, material=TAKPANEL)}
    for skikt, bitar in skikten(kod).items():
        for q, a, b, typ in bitar:
            lager[skikt].profil(q, a, b, typ=typ, material=MATERIAL[skikt])
    for p in lager.values():
        if p.bitar:
            m.lagg(p.montage())
    return m


def montage() -> Montage:
    m = Montage("Innertak")
    for kod in S.TAKFALL:
        m.lagg(takfall(kod))
    return m
