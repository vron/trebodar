"""Invändiga skikt (F-01): ångbroms (Intello Plus, åldringsbeständig plastfolie), installationsskikt och gips
2 × 12,5 under takbalkarna och på ytterväggarnas insida.

Innertaket följer takfallen (snedtak) från ytterväggens insida upp till nocken, och ned till dallinjen där takfallet
slutar vid en dalbalk, med uppehåll vid mittstolen och öppningar för takfönstren. Under taket: korslagd läkt 45
(F-01) och gips 2 × 12,5. Den yttre gipsskivan går fri under nock- och dalbalkarna och möter grannfallets i en
skarp linje i nocken och under dalbalkarna; ångbromsen, läkten och den inre gipsskivan slutar vid balkarna.
Väggar, stolpar och strävor som står under innertaket går skikten runt. Ytterväggarnas insida går från bjälklaget
upp till innertaket; gavlarnas insida följer snedtaket upp till takbalkarnas underkant. Lätta innerväggar är ännu
inte modellerade.
"""
from __future__ import annotations

from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from modellering import Montage, i_foraldern, omslutande

from trebodar import skelett as S
from trebodar.byggdelar import taklager as L
from trebodar.byggdelar import polygon as P
from trebodar.byggdelar.regelvagg import Plan
from trebodar.hus.fonster_och_dorrar.oppningar import OPPNINGAR
from trebodar.hus.isolering.isolering import TAKSTOLSVAGGAR, _fack
from trebodar.hus.stomme.prefab.takbalkar.takbalkar import FALT, _sida
from trebodar.material import ANGBROMS, C24_LAKT, GIPS

FOLIE, LAKT, GIPS_T = 0.4, 45.0, 25.0          # installationsskikt 45×45, gips 2 × 12,5
SKIVA = 12.5
TAK_W = (-S.TAKBALK_H - FOLIE, -S.TAKBALK_H)                 # under takbalkarnas underkant
LAKT_W = (TAK_W[0] - LAKT, TAK_W[0])
GIPS_INRE_W = (LAKT_W[0] - SKIVA, LAKT_W[0])
GIPS_YTTRE_W = (GIPS_INRE_W[0] - SKIVA, GIPS_INRE_W[0])
INSIDA_T = FOLIE + LAKT + GIPS_T
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


def _stommen() -> list[tuple[str, tuple[float, float, float, float, float, float]]]:
    """Ytterväggarnas, innerväggarnas och stolparnas delar som (grupp, omslutande låda i huset)."""
    from trebodar.hus.stomme.prefab.innervaggar import innervaggar
    from trebodar.hus.stomme.prefab.stolpar import stolpar
    from trebodar.hus.stomme.prefab.yttervaggar import yttervaggar
    ut = []
    for mont in (yttervaggar.montage(), innervaggar.montage(), stolpar.montage()):
        for vag, d, pl in mont.platta():
            b = omslutande(d.form)
            if b is not None:
                ut.append((vag.rsplit("/", 1)[0], i_foraldern(b, pl)))
    return ut


STOMMEN = _stommen()


def _hinder_tak(t: S.Takfall, x_lo: float, x_hi: float) -> list[tuple[float, float, float, float, bool]]:
    """Väggar och stolpar som når upp till innertaket i takfallet (mellan x_lo och x_hi), som (x0, x1, y0, y1,
    stolpe) per grupp: delar som går över gipsens underkant där innertaket är lägst ovanför dem. Takfotsväggen
    räknas inte (innertaket går över den)."""
    lador: dict[str, list[float]] = {}
    for grupp, (x0, y0, _, x1, y1, z1) in STOMMEN:
        if grupp.endswith(f"Vägg {t.kod}") or not (x0 < x_hi and x_lo < x1):
            continue
        x = max(x0, x_lo) if t.riktning > 0 else min(x1, x_hi)           # där innertaket är lägst över delen
        if z1 <= t.z_overkant(x) + GIPS_YTTRE_W[0] / S.COS + 1.0:
            continue
        g = lador.setdefault(grupp, [x0, x1, y0, y1])
        g[:] = [min(g[0], x0), max(g[1], x1), min(g[2], y0), max(g[3], y1)]
    return [(g[0], g[1], g[2], g[3], "/Stolpe " in f"/{k}") for k, g in lador.items()]


def _med_fri(hinder: list[tuple[float, float, float, float, bool]]) -> list[tuple[float, float, float, float]]:
    """Hindren med gipsens avstånd: FRI längs x, för stolpar också längs y."""
    return [(x0 - FRI, x1 + FRI, y0 - (FRI if st else 0.0), y1 + (FRI if st else 0.0)) for x0, x1, y0, y1, st in hinder]


def _utan_hinder(k0: L.Kant, k1: L.Kant, s0: float, s1: float,
                 hinder: list[tuple[float, float, float, float]]) -> list[tuple[float, float, L.Kant, L.Kant]]:
    """Skiktets bitar mellan kanterna och y = s0 … s1 utanför hindren (x0, x1, y0, y1): (y0, y1, kant, kant)."""
    kl, kh = sorted((k0, k1), key=lambda k: k.x)
    ys = sorted({s0, s1} | {y for x0, x1, y0, y1 in hinder for y in (y0, y1) if s0 < y < s1 and x0 < kh.x and kl.x < x1})
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
    hinder_s = [h[:4] for h in hinder]                     # ångbroms och läkt: mot hindren
    hinder_g = _med_fri(hinder)                            # gips: med avstånd
    lager = {"folie": Plan(kod, f"Ångbroms tak {kod}", 1.0, material=ANGBROMS),
             "lakt": Plan(kod, f"Installationsskikt tak {kod}", LAKT, material=C24_LAKT),
             "gips": Plan(kod, f"Gips tak {kod}", 1.0, material=GIPS)}
    for y0, y1 in _strackor(kod):
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
                    bitar = [(s0, s1)]
                    for hx0, hx1, hy0, hy1 in hinder_s:
                        if hx0 < bx1 and bx0 < hx1:
                            bitar = [d for c, e in bitar for d in ((c, min(e, hy0)), (max(c, hy1), e)) if d[1] - d[0] > 1.0]
                    for c, e in bitar:
                        lager["lakt"].profil([(float(x), float(z)) for x, z in list(lp.exterior.coords)[:-1]], c, e,
                                             typ="IL", material=C24_LAKT)
    for p in lager.values():
        if p.bitar:
            m.lagg(p.montage())
    return m


def _hinder() -> list[tuple[Polygon, float, float]]:
    """Delar som står mot ytterväggarnas insida: bärande innerväggar, syllar, stolparnas syllar och dalbalkarnas
    ändar, som (plan, z0, z1)."""
    from trebodar.hus.stomme.prefab.innervaggar.syllar import SYLLAR
    ut = []
    for v in S.INNERVAGGAR.values():
        ox, oy = v.origo
        ux, uy = v.u
        wx, wy = v.w
        t = v.tjocklek + 20.0                         # väggen och stolpar som sticker ut ur den
        h = [(ox, oy), (ox + ux * v.langd, oy + uy * v.langd), (ox + ux * v.langd + wx * t, oy + uy * v.langd + wy * t),
             (ox + wx * t, oy + wy * t)]
        ut.append((Polygon(h).buffer(15.0, join_style=2), 0.0, 4000.0))
    for x0, x1, y0, y1 in SYLLAR:
        ut.append((box(x0, y0, x1, y1), 0.0, 45.0))
    ut.append((box(10980, 4651, 13745, 4721), 0.0, 45.0))            # syllen vid LN1_2
    ut.append((box(10980, 6542, 13745, 6612), 0.0, 45.0))            # syllen vid LN1_3
    for b in S.BALKAR.values():
        ut.append((box(b.x - S.BALK_B / 2, b.y0, b.x + S.BALK_B / 2, b.y1), b.uk, b.ok))
    return ut


HINDER = _hinder()


def _yta(kod: str, u0: float, u1: float) -> Polygon:
    """Ytterväggens insida i väggens (u, z): vid takfoten upp till innertakets gips (vid stommens insida), på
    gavlarna längs snedtaket upp till takbalkarnas underkant (innertaket slutar mot gavelns insida)."""
    v = S.YTTERVAGGAR[kod]
    if kod in S.TAKFALL:
        t = S.TAKFALL[kod]
        return box(u0, 0.0, u1, t.z_overkant(t.x_insida) + GIPS_YTTRE_W[0] / S.COS)
    fall = [t for t in S.TAKFALL.values() if t.kropp == int(kod[0])]

    def z(u: float) -> float:
        return min(t.z_underkant(v.origo[0] + v.u[0] * u) for t in fall)
    nock = (S.HUSKROPPAR[int(kod[0])].nock - v.origo[0]) * v.u[0]
    us = sorted({u0, u1} | ({nock} if u0 < nock < u1 else set()))
    return Polygon([(u0, 0.0), (u1, 0.0)] + [(u, z(u)) for u in reversed(us)])


def _vagg_insida(kod: str) -> Montage:
    """Ytterväggens insida: ångbroms, liggande installationsläkt 45×45 c/c 600, gips 2 × 12,5."""
    v = S.YTTERVAGGAR[kod]
    m = Montage(f"Insida {kod}", beskrivning="Ångbroms, installationsskikt 45 och gips 2 × 12,5")
    # från grannväggarnas insidor: u från T_STOMME till langd − T_STOMME där väggen möter en annan vägg i hörnen
    # långsidorna står mellan gavlarna och går ut i hörnen; gavlarnas insida börjar vid långsidornas insida
    u0, u1 = S.T_STOMME + INSIDA_T, v.langd - S.T_STOMME - INSIDA_T
    if kod in S.TAKFALL:
        u0, u1 = 0.0, v.langd
    yta = _yta(kod, u0, u1)
    topp = yta.bounds[3]
    hal_lista = [box(o.u0, o.z0, o.u1, o.z1) for o in OPPNINGAR.get(kod, [])]
    # delar som står mot väggens insida: deras utbredning i u och z tas bort
    pl = v.placering()
    band = Polygon([pl.punkt((u0, S.T_STOMME, 0))[:2], pl.punkt((u1, S.T_STOMME, 0))[:2],
                    pl.punkt((u1, S.T_STOMME + INSIDA_T, 0))[:2], pl.punkt((u0, S.T_STOMME + INSIDA_T, 0))[:2]])
    Pi = pl.invers()
    for poly, z0, z1 in HINDER:
        g = poly.intersection(band)
        if g.area > 1.0:
            us = [Pi.punkt((x, y, 0.0))[0] for x, y in g.exterior.coords]
            hal_lista.append(box(min(us), z0, max(us), z1))
    oppet = unary_union(hal_lista) if hal_lista else Polygon()
    w = S.T_STOMME
    for namn, t, typ, mat in (("Ångbroms", FOLIE, "AB", ANGBROMS), ("Installationsskikt", LAKT, "IL", C24_LAKT),
                              ("Gips", GIPS_T, "GI", GIPS)):
        p = Plan(kod, f"{namn} {kod}", t, material=mat)
        if namn == "Installationsskikt":
            # liggande läkt c/c 600 och överst i väggen (på gavlarna upp till snedtaket)
            rader = [0.0] + ([topp - LAKT] if kod in S.TAKFALL else [])
            rader += [z for z in (k * 600.0 for k in range(1, int(topp // 600) + 1)) if all(abs(z - r) >= LAKT for r in rader)]
            for z in sorted(rader):
                for q in P.polygoner(box(u0, z, u1, z + LAKT).intersection(yta).difference(oppet), 45 * 100):
                    p.profil(P.kontur(q), w, w + t, typ=typ, material=mat)
        else:
            for q in P.polygoner(yta.difference(oppet)):
                p.skiva(P.kontur(q), P.hal(q), w, w + t, typ, mat, f"{namn} {kod}")
        m.lagg(p.montage())
        w += t
    return m


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
    return m
