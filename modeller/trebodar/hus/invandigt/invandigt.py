"""Invändiga skikt (F-01): ångbroms (Intello Plus, åldringsbeständig plastfolie), installationsskikt och gips
2 × 12,5 under takbalkarna och på ytterväggarnas insida.

Innertaket följer takfallen (snedtak) från ytterväggens insida upp till nocken, och ned till dallinjen där takfallet
slutar vid en dalbalk, med uppehåll vid mittstolen och öppningar för takfönstren. Under taket: korslagd läkt 45
(F-01), med en läkt längs takfallet vid gavlarna bakom gipsens kant, och gips 2 × 12,5. Den yttre gipsskivan går fri
under nock- och dalbalkarna och möter grannfallets i en skarp linje i nocken och under dalbalkarna; ångbromsen,
läkten och den inre gipsskivan slutar vid balkarna.
Väggar, stolpar och strävor som står under innertaket går skikten runt. Ytterväggarnas insida går från bjälklaget
upp till innertaket, kapad längs det så att gipsen möts i en skarp linje; gavlarnas insida följer snedtaket upp till
takbalkarnas underkant och innertaket slutar mot den. I dalarna, där en gavel går förbi en långsidas ände
(ytterhörn sett inifrån), går skikten runt hörnet var för sig: gavelns fram till långsidans och långsidans förbi
gaveln. Skivorna på väggarna: OSB 12 och gips 13, i badrummet plywood 15, gips 12, tätskikt och kakel.
Innerväggarna (de lätta väggarna och skikten på alla innerväggar) i vaggar.py, källarväggarnas gips i kallare.py.
"""
from __future__ import annotations

from functools import cache

from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

from modellering import Material, Montage, Placering, lada

from trebodar import skelett as S
from trebodar.byggdelar import lagen
from trebodar.byggdelar import taklager as L
from trebodar.byggdelar import polygon as P
from trebodar.byggdelar.genomforing import genomfor
from trebodar.byggdelar.regelvagg import Plan
from trebodar.hus.fonster_och_dorrar.oppningar import OPPNINGAR
from trebodar.hus.isolering.isolering import TAKSTOLSVAGGAR, _fack
from trebodar.hus.stomme.prefab.takbalkar.takbalkar import FALT, _sida
from trebodar.hus.tak.tak import tak_underkant
from trebodar.hus.rum import BADRUM
from trebodar.material import ANGBROMS, C24_LAKT, GIPS, KAKEL, OSB, PLYWOOD, TATSKIKT

from . import kallare

FOLIE, LAKT = 0.4, 45.0                        # ångbroms och installationsskikt 45×45
# skivorna på väggarna, från reglarna eller installationsläkten och utåt: OSB och gips, i badrummet plywood, gips,
# tätskikt med fix och kakel (namn, tjocklek, typ, material)
SKIVOR = (("OSB", 12.0, "OS", OSB), ("Gips", 13.0, "GI", GIPS))
SKIVOR_VATRUM = (("Plywood", 15.0, "PW", PLYWOOD), ("Gips", 12.0, "GI", GIPS), ("Tätskikt", 3.0, "TS", TATSKIKT),
                 ("Kakel", 8.0, "KA", KAKEL))
SKIVOR_T = sum(t for _, t, _, _ in SKIVOR)
SKIVOR_VATRUM_T = sum(t for _, t, _, _ in SKIVOR_VATRUM)
SKIVA = 12.5                                   # innertakets gipsskivor
TAK_W = (-S.TAKBALK_H - FOLIE, -S.TAKBALK_H)                 # under takbalkarnas underkant
LAKT_W = (TAK_W[0] - LAKT, TAK_W[0])
GIPS_INRE_W = (LAKT_W[0] - SKIVA, LAKT_W[0])
GIPS_YTTRE_W = (GIPS_INRE_W[0] - SKIVA, GIPS_INRE_W[0])
INSIDA_T = FOLIE + LAKT + SKIVOR_T
INSIDA_VATRUM_T = FOLIE + LAKT + SKIVOR_VATRUM_T
def _med_lage(skikt: tuple[tuple[str, float, str, Material], ...], a: float
              ) -> list[tuple[str, float, float, str, Material]]:
    """Skikten med deras avstånd från stommens insida (namn, a, b, typ, material), det första från a."""
    ut = []
    for namn, t, typ, mat in skikt:
        ut.append((namn, a, a + t, typ, mat))
        a += t
    return ut


# väggarnas skikt med avståndet från stommens insida
GRUND = _med_lage((("Ångbroms", FOLIE, "AB", ANGBROMS), ("Installationsskikt", LAKT, "IL", C24_LAKT)), 0.0)
SKIVLAGER = {"vanligt": _med_lage(SKIVOR, FOLIE + LAKT), "vatrum": _med_lage(SKIVOR_VATRUM, FOLIE + LAKT)}
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
    for grupp, _, (x0, y0, _, x1, y1, z1) in lagen.prefab():
        if grupp.endswith(f"Vägg {t.kod}") or not (x0 < x_hi and x_lo < x1):
            continue
        x = max(x0, x_lo) if t.riktning > 0 else min(x1, x_hi)           # där innertaket är lägst över delen
        if z1 <= t.z_overkant(x) + GIPS_YTTRE_W[0] / S.COS + 1.0:
            continue
        g = lador.setdefault(grupp, [x0, x1, y0, y1])
        g[:] = [min(g[0], x0), max(g[1], x1), min(g[2], y0), max(g[3], y1)]
    ut = [(g[0], g[1], g[2], g[3], "stolpe" if "/Stolpe " in f"/{k}" else "vägg") for k, g in lador.items()]
    # en ytterväggs insida går upp genom innertaket med väggen (en gavel som går förbi en dal under grannkroppens
    # takfall); innertaket möter skikten utan avstånd
    for k in lador:
        if k.startswith("Ytterväggar/Vägg "):
            x0, y0, x1, y1 = _insidans_plan(k.split("Vägg ")[-1]).bounds
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
                   if int(k[0]) == t.kropp and abs(v.u[0]) > 0.5 and k not in TAKSTOLSVAGGAR])
    tackt: list[list[float]] = []
    for a, b in band:
        if tackt and a <= tackt[-1][1] + 1e-6:
            tackt[-1][1] = max(tackt[-1][1], b)
        else:
            tackt.append([a, b])
    ut: list[list[float]] = []
    for y0, y1 in _fack(kod):
        if ut and (y0 - ut[-1][1] <= S.TAKBALK_B + 1e-6 or
                   any(a <= ut[-1][1] + 1e-6 and y0 <= b + 1e-6 for a, b in tackt)):
            ut[-1][1] = y1
        else:
            ut.append([y0, y1])
    # vid gavlarna slutar innertaket vid gavelväggens insida (ångbroms, läkt och gips)
    if ut:
        ut[0][0] += INSIDA_T
        ut[-1][1] -= INSIDA_T
    return ut


def _tak(kod: str) -> Montage:
    t = S.TAKFALL[kod]
    f = FALT[kod]
    m = Montage(f"Innertak {kod}", beskrivning="Ångbroms, installationsskikt 45 och gips 2 × 12,5 under takbalkarna")
    # ångbromsen, läkten och den inre gipsskivan slutar 10 mm från nockbalken och vid dalbalkens upplagsregel; den yttre
    # gipsskivan går till nocklinjen och dallinjen, där den möter grannfallets
    ovre = L.Kant("lodratt", _sida(f.nock, t) - t.riktning * 10.0)
    ovre_g = L.Kant("lodratt", S.BALKAR[f.nock].x)
    dal = S.BALKAR[f.dal] if f.dal else None
    hinder = _hinder_tak(t, *sorted((min(t.x_insida, dal.x) if dal and t.riktning > 0 else
                                     max(t.x_insida, dal.x) if dal else t.x_insida, ovre_g.x)))
    hinder += [(*b, "vägg") for b in _badrumsremsor(t)]
    hinder_s = [h[:4] for h in hinder]                     # ångbroms och läkt: mot hindren
    hinder_g = _med_fri(hinder)                            # gips: med avstånd
    lager = {"folie": Plan(kod, f"Ångbroms tak {kod}", 1.0, material=ANGBROMS),
             "lakt": Plan(kod, f"Installationsskikt tak {kod}", LAKT, material=C24_LAKT),
             "gips": Plan(kod, f"Gips tak {kod}", 1.0, material=GIPS)}
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
            nedre = L.Kant("lodratt", _sida(dal.kod, t) + t.riktning * 45.0 if dal and vid_dal else t.x_insida)
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
                        lager["folie"].profil(q, sa, sb, typ="AB", material=ANGBROMS)
                for (ga0, ga1), w, typ in (((k0, k1), GIPS_INRE_W, "GI"), ((g0, g1), GIPS_YTTRE_W, "GY")):
                    for sa, sb, ga, gb in _utan_hinder(ga0, ga1, s0, s1, hinder_g):
                        q = L.profil(t, *w, ga, gb)
                        if q:
                            lager["gips"].profil(q, sa, sb, typ=typ, material=GIPS)
                # installationsskiktets läkt längs y, c/c 400 längs takfallet, avbruten vid hindren
                q = L.profil(t, *LAKT_W, k0, k1)
                if not q:
                    continue
                for c, e in spik:
                    if s0 <= c and e <= s1:
                        for sa, sb, ka, kb in _utan_hinder(k0, k1, c, e, hinder_s):
                            qs = L.profil(t, *LAKT_W, ka, kb)
                            if qs:
                                lager["lakt"].profil(qs, sa, sb, typ="IL", material=C24_LAKT)
                ls0 = max([s0] + [e for c, e in spik if c <= s0 + 1e-6])
                ls1 = min([s1] + [c for c, e in spik if e >= s1 - 1e-6])
                ys = Polygon(q)
                x_lo, x_hi = ys.bounds[0], ys.bounds[2]
                langd = (x_hi - x_lo) / S.COS
                n = int(langd // CC)
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
                    bx0, bx1 = lp.bounds[0], lp.bounds[2]
                    bitar = [(ls0, ls1)]
                    for hx0, hx1, hy0, hy1 in hinder_s:
                        if hx0 < bx1 and bx0 < hx1:
                            bitar = [d for c, e in bitar for d in ((c, min(e, hy0)), (max(c, hy1), e))
                                     if d[1] - d[0] > 1.0]
                    for c, e in bitar:
                        lager["lakt"].profil([(float(x), float(z)) for x, z in list(lp.exterior.coords)[:-1]], c, e,
                                             typ="IL", material=C24_LAKT)
    for p in lager.values():
        if p.bitar:
            m.lagg(p.montage())
    return m


@cache
def _hinder() -> tuple[list[tuple[Polygon, float, float]], list[tuple[Polygon, float, float]]]:
    """Delar som står mot ytterväggarnas insida, som (plan, z0, z1): de bärande innerväggarnas delar och skikt,
    stolparnas delar och dalbalkarnas ändar; för skivorna också de lätta väggarnas stommar."""
    from .vaggar import barande_skikt, stommar
    ut = list(barande_skikt())
    for grupp, _, (x0, y0, z0, x1, y1, z1) in lagen.prefab():
        if not grupp.startswith("Ytterväggar/"):
            ut.append((box(x0, y0, x1, y1), z0, z1))
    for b in S.BALKAR.values():
        ut.append((box(b.x - S.BALK_B / 2, b.y0, b.x + S.BALK_B / 2, b.y1), b.uk, b.ok))
    return ut, ut + stommar()


def _innertakets_underkant(t: S.Takfall, x: float) -> float:
    """Innertakets yttre gipsskivas underkant vid x."""
    return t.z_overkant(x) + GIPS_YTTRE_W[0] / S.COS


def _yta(kod: str, u0: float, u1: float) -> Polygon:
    """Ytterväggens insida i väggens (u, z): vid takfoten upp till innertaket vid skiktens yta mot rummet (skikten
    kapas sedan längs innertaket, _kapa_vid_innertaket), på gavlarna längs taket upp till takbalkarnas underkant
    (innertaket slutar mot gavelns insida)."""
    v = S.YTTERVAGGAR[kod]
    if kod in S.TAKFALL:
        t = S.TAKFALL[kod]
        return box(u0, 0.0, u1, _innertakets_underkant(t, t.x_insida + t.riktning * INSIDA_VATRUM_T) + 1.0)
    pl = v.placering()

    def z(u: float) -> float:
        x, y, _ = pl.punkt((u, S.T_STOMME, 0.0))
        zt = tak_underkant(x, y)
        assert zt is not None, (kod, u)
        return zt - S.TAKBALK_HV
    # brytpunkter: nocken och dalarna (där gaveln går förbi en långsidas ände ligger grannkroppens takfall över den)
    brott = [S.HUSKROPPAR[int(kod[0])].nock] + [b.x for b in S.BALKAR.values() if b.typ == "dal"]
    us = sorted({u0, u1} | {u for u in ((x - v.origo[0]) * v.u[0] for x in brott) if u0 < u < u1})
    return Polygon([(u0, 0.0), (u1, 0.0)] + [(u, z(u)) for u in reversed(us)])


def _badrum_langs(kod: str, u0: float, u1: float, w0: float, w1: float) -> list[tuple[float, float]]:
    """Badrummets utbredning längs väggen kod (u-intervall) i bandet w0–w1 från stommens yttre yta."""
    pl = S.YTTERVAGGAR[kod].placering()
    band = Polygon([pl.punkt((u0, w0, 0))[:2], pl.punkt((u1, w0, 0))[:2], pl.punkt((u1, w1, 0))[:2],
                    pl.punkt((u0, w1, 0))[:2]])
    Pi = pl.invers()
    ut = []
    for g in P.polygoner(BADRUM.intersection(band)):
        us = [Pi.punkt((x, y, 0.0))[0] for x, y in g.exterior.coords]
        ut.append((min(us), max(us)))
    return sorted(ut)


def _badrumsremsor(t: S.Takfall) -> list[tuple[float, float, float, float]]:
    """Där badrummet ligger mot en gavel är gavelns insida tjockare och innertaket slutar vid den: remsorna (x0, x1,
    y0, y1) mellan den vanliga insidans och våtrumsskiktets yta."""
    ut = []
    for kod, v in S.YTTERVAGGAR.items():
        if kod in S.TAKFALL or int(kod[0]) != t.kropp:
            continue
        pl = v.placering()
        for a, b in _badrum_langs(kod, 0.0, v.langd, S.T_STOMME, S.T_STOMME + INSIDA_VATRUM_T):
            horn = [pl.punkt((u, S.T_STOMME + w, 0))[:2] for u in (a, b) for w in (INSIDA_T, INSIDA_VATRUM_T)]
            xs, ys = [x for x, _ in horn], [y for _, y in horn]
            ut.append((min(xs), max(xs), min(ys), max(ys)))
    return ut


def _insida_t(kod: str, u: float) -> float:
    """Ytterväggens insida (ångbroms, läkt och skivor) vid u: tjockare i badrummet."""
    pl = S.YTTERVAGGAR[kod].placering()
    x, y, _ = pl.punkt((u, S.T_STOMME + 30.0, 0.0))
    return INSIDA_VATRUM_T if BADRUM.contains(Point(x, y)) else INSIDA_T


def _stomme(kod: str) -> Polygon:
    """Ytterväggens stomme i plan."""
    v = S.YTTERVAGGAR[kod]
    pl = v.placering()
    return Polygon([pl.punkt((u, w, 0.0))[:2] for u, w in ((0.0, 0.0), (v.langd, 0.0), (v.langd, S.T_STOMME),
                                                            (0.0, S.T_STOMME))])


@cache
def _ytterhorn(kod: str, slut: bool) -> bool:
    """Väggens början eller slut är ett ytterhörn sett inifrån: rummet fortsätter förbi änden vid väggens insida.
    Så är det i dalarna, där en gavel går förbi en långsidas ände (1NO–2SO, 2SV–1NV, 2NV–3NO och 2SV–3SO)."""
    v = S.YTTERVAGGAR[kod]
    x, y, _ = v.placering().punkt((v.langd + 1.0 if slut else -1.0, S.T_STOMME + 1.0, 0.0))
    p = Point(x, y)
    hus = Polygon(S.KONTUR).buffer(S.STOMME_UT, join_style=2)
    return hus.contains(p) and not any(_stomme(k).contains(p) for k in S.YTTERVAGGAR)


def _u_granser(kod: str, a: float, b: float) -> tuple[float, float]:
    """Skiktet a–b (från stommens insida) längs väggen: långsidorna mellan gavlarna, gavlarna från långsidornas
    insida. I ett ytterhörn går gavelns skikt fram till långsidans skikt (a förbi änden) och långsidans skikt förbi
    gaveln och täcker gavelns skikt (gavelns tjocklek och b förbi änden), så att skikten möts var för sig."""
    v = S.YTTERVAGGAR[kod]
    gavel = kod not in S.TAKFALL
    forbi = a if gavel else S.T_STOMME + b
    u0 = -forbi if _ytterhorn(kod, False) else S.T_STOMME + _insida_t(kod, S.T_STOMME + 1.0) if gavel else 0.0
    u1 = (v.langd + forbi if _ytterhorn(kod, True) else
          v.langd - S.T_STOMME - _insida_t(kod, v.langd - S.T_STOMME - 1.0) if gavel else v.langd)
    return u0, u1


def _insidans_plan(kod: str) -> Polygon:
    """Ytterväggens insida i plan, med de vanliga skikten (badrummets tjockare insida har innertaket i
    _badrumsremsor)."""
    g = [_u_granser(kod, a, b) for _, a, b, _, _ in GRUND + SKIVLAGER["vanligt"]]
    u0, u1 = min(x[0] for x in g), max(x[1] for x in g)
    pl = S.YTTERVAGGAR[kod].placering()
    return Polygon([pl.punkt((u, w, 0.0))[:2] for u, w in ((u0, S.T_STOMME), (u1, S.T_STOMME),
                                                            (u1, S.T_STOMME + INSIDA_T), (u0, S.T_STOMME + INSIDA_T))])


def _vagg_insida(kod: str) -> Montage:
    """Ytterväggens insida: ångbroms, liggande installationsläkt 45×45 c/c 600, OSB och gips (i badrummet plywood,
    gips, tätskikt och kakel)."""
    v = S.YTTERVAGGAR[kod]
    m = Montage(f"Insida {kod}", beskrivning="Ångbroms, installationsskikt 45, OSB 12 och gips 13 (i badrummet plywood "
                                             "15, gips 12, tätskikt och kakel)")
    # skiktens utbredning längs väggen (_u_granser)
    granser = {(a, b): _u_granser(kod, a, b) for _, a, b, _, _ in GRUND + SKIVLAGER["vanligt"] + SKIVLAGER["vatrum"]}
    u0, u1 = min(g[0] for g in granser.values()), max(g[1] for g in granser.values())
    topp = _yta(kod, u0, u1).bounds[3]
    hal_lista = [box(o.u0, o.z0, o.u1, o.z1) for o in OPPNINGAR.get(kod, [])]
    # delar som står mot väggens insida: deras utbredning i u och z tas bort
    pl = v.placering()
    band = Polygon([pl.punkt((u0, S.T_STOMME, 0))[:2], pl.punkt((u1, S.T_STOMME, 0))[:2],
                    pl.punkt((u1, S.T_STOMME + INSIDA_VATRUM_T, 0))[:2],
                    pl.punkt((u0, S.T_STOMME + INSIDA_VATRUM_T, 0))[:2]])
    Pi = pl.invers()

    def oppet_mot(hinder: list[tuple[Polygon, float, float]]) -> Polygon:
        hal = list(hal_lista)
        for poly, z0, z1 in hinder:
            g = poly.intersection(band)
            if g.area > 1.0:
                x0, y0, x1, y1 = g.bounds
                us = [Pi.punkt((x, y, 0.0))[0] for x in (x0, x1) for y in (y0, y1)]
                hal.append(box(min(us), z0, max(us), z1))
        return unary_union(hal) if hal else Polygon()
    oppet, oppet_skivor = oppet_mot(_hinder()[0]), oppet_mot(_hinder()[1])
    if kod not in S.TAKFALL:
        # gavlarna: takets stomme i skiktens band (takbalken och upplagsregeln över 1NO vid dalbalk 4), exakt
        y_lo, y_hi = band.bounds[1], band.bounds[3]
        tak = unary_union([Polygon([((x - v.origo[0]) * v.u[0], z) for x, z in q.exterior.coords])
                           for _, q, y0, y1 in lagen.takets_stomme() if min(y1, y_hi) - max(y0, y_lo) > 1.0])
        oppet, oppet_skivor = oppet.union(tak), oppet_skivor.union(tak)
    for namn, a, b, typ, mat in GRUND:
        p = Plan(kod, f"{namn} {kod}", b - a, material=mat)
        ua, ub = granser[(a, b)]
        yta = _yta(kod, ua, ub)
        if namn == "Installationsskikt":
            # liggande läkt c/c 600 och överst i väggen (på gavlarna upp till snedtaket)
            rader = [0.0] + ([topp - LAKT] if kod in S.TAKFALL else [])
            rader += [z for z in (k * 600.0 for k in range(1, int(topp // 600) + 1))
                      if all(abs(z - r) >= LAKT for r in rader)]
            for z in sorted(rader):
                for q in P.polygoner(box(ua, z, ub, z + LAKT).intersection(yta).difference(oppet), 45 * 100):
                    p.profil(P.kontur(q), S.T_STOMME + a, S.T_STOMME + b, typ=typ, material=mat)
        else:
            for q in P.polygoner(yta.difference(oppet)):
                p.skiva(P.kontur(q), P.hal(q), S.T_STOMME + a, S.T_STOMME + b, typ, mat, f"{namn} {kod}")
        m.lagg(p.montage())
    # skivorna: våtrumsskikt där badrummet ligger mot väggen, annars OSB och gips
    bad = _badrum_langs(kod, u0, u1, S.T_STOMME, S.T_STOMME + INSIDA_VATRUM_T)
    vatrum = unary_union([box(a, -1.0, b, topp + 1.0) for a, b in bad])
    vanligt = box(u0 - 1.0, -1.0, u1 + 1.0, topp + 1.0).difference(vatrum)
    plan: dict[str, Plan] = {}
    for omrade, lager in ((vanligt, SKIVLAGER["vanligt"]), (vatrum, SKIVLAGER["vatrum"])):
        for namn, a, b, typ, mat in lager:
            p = plan.setdefault(namn, Plan(kod, f"{namn} {kod}", b - a, material=mat))
            for q in P.polygoner(_yta(kod, *granser[(a, b)]).intersection(omrade).difference(oppet_skivor)):
                p.skiva(P.kontur(q), P.hal(q), S.T_STOMME + a, S.T_STOMME + b, typ, mat, f"{namn} {kod}")
    for p in plan.values():
        if p.bitar:
            m.lagg(p.montage())
    if kod in S.TAKFALL:
        _kapa_vid_innertaket(m, kod, u0, u1)
    return m


def _kapa_vid_innertaket(m: Montage, kod: str, u0: float, u1: float) -> None:
    """Takfotsväggens insida kapas längs innertakets underkant, så att innertakets gips går över väggens skivor och
    möter dem i en skarp linje (väggens översta läkt och innertakets nedersta läkt bakom skivornas kanter)."""
    t = S.TAKFALL[kod]
    z0 = _innertakets_underkant(t, t.x_insida)
    w0 = S.T_STOMME - 100.0                    # verktyget börjar 100 mm utanför stommens insida, i planet
    origo = (u0 - 1000.0, w0, z0 - 100.0 * S.TAN)
    langs = 600.0
    verktyg = lada(u1 - u0 + 2000.0, langs, 1000.0).placerad(
        Placering.axlar(origo, (1.0, 0.0, 0.0), (0.0, -S.SIN, S.COS)))
    genomfor(m, verktyg, (u0 - 1000.0, w0 - 600.0, z0 - 200.0, u1 + 1000.0, w0 + langs, z0 + 1500.0))


def montage() -> Montage:
    m = Montage("Invändigt", beskrivning="Ångbroms, installationsskikt och gips (F-01)")
    tak = Montage("Innertak")
    for kod in S.TAKFALL:
        tak.lagg(_tak(kod))
    m.lagg(tak)
    vagg = Montage("Ytterväggarnas insida")
    for kod in S.YTTERVAGGAR:
        vagg.lagg(_vagg_insida(kod), S.YTTERVAGGAR[kod].placering())
    m.lagg(vagg)
    from .vaggar import montage as innervaggar
    m.lagg(innervaggar())
    m.lagg(kallare.montage())
    return m
