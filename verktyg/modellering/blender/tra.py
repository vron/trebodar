"""Trä: konstruktionsvirke, limträ och sågade brädor (fasadpanel, råspont). Se material.py för parametrarna."""
from __future__ import annotations

import math

from graf import AXEL, Graf, Sockel, linjar, rgba, skala
from graf import tal as _f

def tra(g: Graf, p: dict) -> None:
    langs, tv, dj = g.axlar(p.get("riktning", "x"), p.get("tvars", "y"))
    ljus = linjar(p["farg"])
    mork = linjar(p.get("farg2", p["farg"]))
    v = g.vektor(langs, tv, dj)
    distorsion = g.brus(g.vektor(g.matte("MULTIPLY", langs, 0.6), tv, dj), 4.0, 3.0)
    ringar = g.nod("ShaderNodeTexWave", Vector=v, Scale=1000.0 / _f(p, "arsring", 4.0) / 6.0,
                   Distortion=6.0, Detail=3.0)
    ringar.wave_type = "RINGS"
    ringar.rings_direction = "X"
    fiber = g.brus(g.vektor(g.matte("MULTIPLY", langs, 4.0), g.matte("MULTIPLY", tv, 120.0),
                            g.matte("MULTIPLY", dj, 120.0)), 1.0, 6.0)
    fak = g.linj((g.utgang(ringar, "Factor", "Fac"), 0.7), (fiber, 0.3), (g.matte("SUBTRACT", distorsion, 0.5), 0.2))
    g.yta(g.ramp(fak, [(0.25, skala(mork, 0.85)), (0.65, (*ljus, 1.0)), (1.0, skala(ljus, 1.08))]),
          _f(p, "grovhet", 0.65), hojd=fiber, styrka=0.15)


def limtra(g: Graf, p: dict) -> None:
    tra(g, p)
    # lameller: färgskiftning per lamell och mörka limfogar
    lam = g.sep(g.koord)[AXEL[p.get("lamell", "z")]]
    t = _f(p, "lamelltjocklek", 45.0) / 1000.0
    nr = g.matte("FLOOR", g.matte("DIVIDE", lam, t))
    inom = g.matte("SUBTRACT", g.matte("DIVIDE", lam, t), nr)
    fog = g.matte("LESS_THAN", inom, 0.04)
    ljus = g.matte("ADD", 0.92, g.matte("MULTIPLY", g.slump(nr), 0.16))
    ljus = g.matte("MULTIPLY", ljus, g.matte("SUBTRACT", 1.0, g.matte("MULTIPLY", fog, 0.45)))
    bas = g.bsdf.inputs["Base Color"].links[0].from_socket
    g.nt.links.new(g.ljus(bas, ljus), g.bsdf.inputs["Base Color"])


BEHANDLING: dict[str, dict[str, object]] = {
    "tackfarg": {"tackning": 1.0, "genomslag": 0.10, "strimmor": 0.35, "grovhet": 0.93, "relief": 1.3},
    "jarnvitriol": {"tackning": 0.0, "kvistfarg": "#1f1b18", "farg3": "#76685a", "brun": 0.5, "strimmor": 1.1,
                    "fibrer": 1.8, "grovhet": 0.9, "relief": 1.2},
    "obehandlad": {"tackning": 0.0, "kvistfarg": "#6e4a2a", "farg3": "#c9a978", "brun": 0.3, "strimmor": 0.3,
                   "grovhet": 0.8, "relief": 0.7},
}


def bradpanel(g: Graf, p: dict) -> None:
    """Sågade brädor, se modulens beskrivning."""
    d = {**BEHANDLING[p.get("behandling", "tackfarg")], **p}
    m, kv = g.matte, g.kv
    L, T, D = g.axlar(str(d.get("riktning", "y")), str(d.get("tvars", "x")))
    b = _f(d, "bredd", 145.0) / 1000
    f = _f(d, "fog", 4.0) / 1000
    q = m("DIVIDE", T, b)
    nr = m("FLOOR", q)
    tm = m("MULTIPLY", m("SUBTRACT", q, nr), b)                  # tvärs brädan från dess kant [m]
    # skarvar: en del brädor är skarvade på en slumpad höjd (två kortare brädor); ovanför skarven är det en annan
    # bräda, sågad ur en annan stock
    j1, j2, _, _ = g.slump4(m("ADD", m("MULTIPLY", nr, 2.71), 5.3))
    ls = g.linj((j2, _f(d, "skarv_spann", 2.6)), bas=_f(d, "skarv_min", 0.5))
    har_skarv = m("LESS_THAN", j1, _f(d, "skarvar", 0.35))
    ovan = m("MULTIPLY", har_skarv, m("GREATER_THAN", L, ls))
    skarv = m("MULTIPLY", har_skarv, g.jamn(m("ABSOLUTE", m("SUBTRACT", L, ls)), 0.0016, 0.0006))
    nr = m("ADD", nr, m("MULTIPLY", ovan, 0.5))
    r0, r1, r2, r3 = g.slump4(nr)
    r4 = g.slump4(m("ADD", m("MULTIPLY", nr, 1.618), 11.3))[0]

    # kvistar: högst en per cell längs brädan, läge tvärs, storlek och förekomst slumpade per cell
    kc = 1.0 / max(_f(d, "kvistar", 3.0), 0.01)
    W = m("ADD", m("DIVIDE", L, kc), m("MULTIPLY", nr, 17.13))
    vor = g.nod("ShaderNodeTexVoronoi", {"voronoi_dimensions": "1D"}, W=W, Scale=1.0)
    dL = m("MULTIPLY", m("SUBTRACT", W, g.utgang(vor, "W")), kc)
    k1, k2, k3 = g.sep(g.utgang(vor, "Color"))
    finns = m("LESS_THAN", k1, _f(d, "kvistandel", 0.8))
    tk = m("MULTIPLY", m("ADD", 0.2, m("MULTIPLY", k2, 0.6)), b)
    # storleken: mest små och medelstora, några stora; utdragna olika mycket längs brädan
    rk = m("MULTIPLY", g.linj((m("POWER", k3, 2.5), 1.6), bas=0.35), _f(d, "kvist", 18.0) / 2000)
    langd = g.linj((m("FRACT", m("MULTIPLY", k2, 7.3)), 1.1), bas=1.15)
    rho = m("SQRT", m("ADD", kv(m("DIVIDE", dL, m("MULTIPLY", rk, langd))),
                      kv(m("DIVIDE", m("SUBTRACT", tm, tk), rk))))
    kvist = m("MULTIPLY", finns, g.jamn(rho, 1.0, 0.85))
    kvistkant = m("MULTIPLY", finns, m("MULTIPLY", g.jamn(rho, 0.7, 0.92), g.jamn(rho, 1.12, 0.98)))
    kvistring = m("MULTIPLY", kvist, g.jamn(m("FRACT", m("DIVIDE", m("MULTIPLY", rho, rk), 0.0015)), 0.4, 0.9))
    kvistzon = m("MULTIPLY", finns, m("MULTIPLY", g.jamn(rho, 2.2, 1.0), g.jamn(rho, 0.9, 1.0)))   # missfärgning runt
    halo = m("MULTIPLY", finns, m("EXPONENT", m("MULTIPLY", kv(m("DIVIDE", rho, 3.0)), -1.0)))

    # årsringar: brädans yta genom stockens ringar, märgen vid (tp, dp) i tvärsnittet, stocken något lutande
    tp = m("MULTIPLY", m("SUBTRACT", r1, 0.5), 2.5 * b)
    dp = m("ADD", 0.025, m("MULTIPLY", r2, 0.12))
    lut = m("MULTIPLY", m("SUBTRACT", r3, 0.5), 0.016)
    vag = m("MULTIPLY", m("SUBTRACT", g.brus(g.vektor(m("MULTIPLY", L, 1.3), m("MULTIPLY", nr, 3.1), 0.0), 1.0, 2.0),
                                     0.5), 0.006)
    dx = m("SUBTRACT", m("SUBTRACT", tm, b / 2), tp)
    dy = m("ADD", m("ADD", dp, m("MULTIPLY", lut, L)), vag)
    rad = m("SQRT", m("ADD", kv(dx), kv(dy)))
    ring = g.linj((m("DIVIDE", rad, _f(d, "arsring", 3.0) / 1000), 1.0), (halo, 1.2),
                  (m("SUBTRACT", g.brus1(m("MULTIPLY", rad, 80.0)), 0.5), 1.5))
    # sommarveden: mörk mot slutet av ringen, skarp mot nästa; tydligare på vissa brädor och partier
    sen = m("MULTIPLY", kv(g.jamn(m("FRACT", ring), 0.45, 0.93)),
            g.linj((r4, 0.35), (g.brus(g.vektor(m("MULTIPLY", L, 2.0), m("MULTIPLY", T, 8.0), nr), 1.0, 2.0), 0.4),
                   bas=0.45))

    # sågad yta: fibrer längs brädan, ludd och sågmärken; strimmor av väder
    fib = g.brus(g.vektor(m("MULTIPLY", L, 6.0), m("MULTIPLY", T, 600.0), m("MULTIPLY", D, 600.0)), 1.0, 5.0, 0.65)
    ludd = g.brus(g.vektor(m("MULTIPLY", L, 900.0), m("MULTIPLY", T, 2500.0), m("MULTIPLY", D, 2500.0)), 1.0, 2.0)
    strim = g.brus(g.vektor(m("MULTIPLY", L, 0.9), m("MULTIPLY", T, 16.0), m("MULTIPLY", nr, 0.37)), 1.0, 4.0, 0.55)
    flack = g.brus(g.vektor(m("MULTIPLY", L, 3.0), m("MULTIPLY", T, 3.0), m("MULTIPLY", D, 3.0)), 1.0, 3.0)
    sag = m("SINE", g.linj((L, 2 * math.pi / 0.0035), (T, 2 * math.pi / 0.0035 * 0.06), (fib, 4.0)))

    # fog mellan brädorna och brädans fasade kant
    i_fog = g.jamn(tm, f, 0.3 * f)
    kant = g.jamn(tm, b - 0.0025, b)

    # skruvar i raderna (spikläkterna)
    skruv: Sockel = 0.0
    if _f(d, "skruv_cc", 0.0) > 0:
        cc, s0 = _f(d, "skruv_cc", 600.0) / 1000, _f(d, "skruv_start", 0.0) / 1000
        dLs = m("SUBTRACT", L, m("ADD", s0, m("MULTIPLY", m("ROUND", m("DIVIDE", m("SUBTRACT", L, s0), cc)), cc)))
        ka = _f(d, "skruv_kant", 25.0) / 1000
        avst: Sockel | None = None
        for ts in ([b / 2] if _f(d, "skruv_per_brada", 2) < 1.5 else [ka, b - ka]):
            di = m("SQRT", m("ADD", kv(dLs), kv(m("SUBTRACT", tm, ts))))
            avst = di if avst is None else m("MINIMUM", avst, di)
        r = _f(d, "skruv", 7.0) / 2000
        skruv = g.jamn(avst, r, 0.8 * r)

    c1, c2 = rgba(str(d["farg"])), rgba(str(d.get("farg2", d["farg"])))
    var, strimmor = _f(d, "variation", 0.1), _f(d, "strimmor", 0.3)
    if _f(d, "tackning", 0.0) > 0.5:
        # täckfärg: färgen skiftar mellan farg2 och farg per bräda, i strimmor och fibrer; ådring och kvistar anas
        a = g.linj((m("SUBTRACT", r0, 0.5), 4 * var), (m("SUBTRACT", strim, 0.5), strimmor),
                   (m("SUBTRACT", fib, 0.5), 0.35), bas=0.72, klamp=True)
        col = g.ljus(g.blanda(a, c2, c1), g.linj((sen, -_f(d, "genomslag", 0.1)), bas=1.0))
        # färgen samlas i sågytans fåror: mörkare där luddet och fibrerna ligger lågt
        col = g.ljus(col, g.linj((m("SUBTRACT", ludd, 0.5), 0.3), (m("SUBTRACT", fib, 0.5), 0.22), bas=1.0))
        kf = rgba(str(d.get("kvistfarg") or d.get("farg2", d["farg"])), 0.7)
        col = g.blanda(g.linj((kvist, 0.5), (kvistkant, 0.3)), col, kf)
    else:
        # trä: vårved (farg) och sommarved (farg2), vissa brädor brunare (farg3), mörka kvistar
        col = g.blanda(m("MULTIPLY", sen, 0.85), c1, c2)
        col = g.blanda(m("MULTIPLY", r4, _f(d, "brun", 0.3)), col, rgba(str(d.get("farg3", d["farg"]))))
        fibrer = _f(d, "fibrer", 1.0)
        k = g.linj((m("SUBTRACT", r0, 0.5), 2 * var), (m("SUBTRACT", strim, 0.5), 0.6 * strimmor),
                   (m("SUBTRACT", flack, 0.5), 0.25 * strimmor), (m("SUBTRACT", fib, 0.5), 0.35 * fibrer),
                   (m("SUBTRACT", ludd, 0.5), 0.15 * fibrer), bas=1.0)
        col = g.ljus(col, k)
        # kvistarna: döda kvistar mörka, friska ljusare och bruna med synliga ringar (slumpat per kvist)
        kf = g.blanda(m("POWER", k1, 0.6), rgba(str(d.get("kvistfarg", "#3a2a1c"))),
                      rgba(str(d.get("farg3", d["farg"])), 0.62))
        col = g.blanda(m("MULTIPLY", kvistzon, 0.35), col, rgba(str(d.get("farg3", d["farg"])), 0.7))
        col = g.blanda(m("MULTIPLY", kvist, g.linj((kvistring, -0.5), bas=0.95)), col, kf)
        col = g.blanda(m("MULTIPLY", kvistkant, 0.75), col, rgba(str(d.get("kvistfarg", "#3a2a1c")), 0.7))
        # vädrets mörka strimmor längs fibrerna (sommarveden och smuts i fårorna)
        col = g.ljus(col, g.linj((g.jamn(m("SUBTRACT", fib, sen), 0.15, -0.25), -0.35 * strimmor), bas=1.0))
    col = g.ljus(col, m("MULTIPLY", g.linj((i_fog, -0.82), (skarv, -0.7), bas=1.0), g.linj((kant, -0.3), bas=1.0)))
    col = g.blanda(skruv, col, rgba(str(d.get("skruvfarg", "#b6b9bc"))))
    grov = g.linj((ludd, 0.12), (skruv, -0.55), bas=_f(d, "grovhet", 0.9) - 0.06)
    rel = _f(d, "relief", 1.0)
    hojd = g.linj((i_fog, -0.002), (skarv, -0.0012), (kant, -0.0005), (m("SUBTRACT", fib, 0.5), 0.00035 * rel),
                  (m("SUBTRACT", ludd, 0.5), 0.00012 * rel), (sen, 0.00012 * rel), (sag, 0.00005 * rel),
                  (kvist, 0.0002), (skruv, 0.0006))
    g.yta(col, grov, skruv, hojd, styrka=1.0, avstand=1.0)




# ------------------------------------------------------------------ virke: trä ur en stock, per träslag

# Träslagen: vårved (farg) och sommarved eller porband (farg2), årsringens bredd [mm], märgens avstånd från bitens
# origo [m] (min, max), stockens lutning mot biten [°], kvistar per meter och deras diameter [mm], kärnved (andelen
# bitar som har den, radien [m], färgen), ringtyp ("barr": sommarveden mörknar mot ringens slut; "ringporig": ett
# band av stora porer i början av varje ring, som ask och ek, porband mm brett, och sommarveden något mörkare mot
# ringens slut), kontrasten mellan vår- och sommarved och varm, hur mycket de varmaste bitarna dras mot en gyllene ton
# (standard 0,25). Ringarnas tydlighet och porbandets bredd skiftar år från år. Askens färger är mätta på foton av
# hyvlad ask (blek, gråaktigt gräddvit, ådrorna gråbruna), vitbalanserade mot neutrala ytor.
ARTER: dict[str, dict[str, object]] = {
    "gran": {"farg": "#ecdcb6", "farg2": "#d0ad78", "arsring": 3.5, "marg": (0.0, 0.16), "lutning": 1.5,
             "kvistar": 2.2, "kvist": 22.0, "kvistfarg": "#8b5c30", "karnandel": 0.0, "ringtyp": "barr",
             "kontrast": 0.55, "variation": 0.07},
    "furu": {"farg": "#f0dcb8", "farg2": "#c08a55", "arsring": 3.0, "marg": (0.02, 0.2), "lutning": 1.5,
             "kvistar": 1.6, "kvist": 30.0, "kvistfarg": "#9a6436", "karnandel": 0.6, "karnradie": (0.04, 0.12),
             "karnfarg": "#d6a26c", "ringtyp": "barr", "kontrast": 0.8, "variation": 0.08},
    "lark": {"farg": "#ddb47c", "farg2": "#a66d3c", "arsring": 2.5, "marg": (0.03, 0.2), "lutning": 1.5,
             "kvistar": 1.2, "kvist": 20.0, "kvistfarg": "#6d4220", "karnandel": 0.8, "karnradie": (0.05, 0.15),
             "karnfarg": "#c08650", "ringtyp": "barr", "kontrast": 0.7, "variation": 0.09},
    "ask": {"farg": "#e1d6c5", "farg2": "#998368", "arsring": 3.4, "marg": (0.12, 0.45), "lutning": 2.5,
            "kvistar": 0.0, "kvist": 8.0, "kvistfarg": "#6e5638", "karnandel": 0.15, "karnradie": (0.05, 0.16),
            "karnfarg": "#a89278", "ringtyp": "ringporig", "porband": 0.7, "sommarved": 0.35, "kontrast": 1.0,
            "variation": 0.09, "varm": 0.1},
}

# ytbehandlingar: grovhet, mörkning (exponent på färgen: oljan fördjupar och mättar), gulning (oljans och lackens
# bärnstenston, faktor per färgkanal), vitpigment, lack
YTOR: dict[str, dict[str, object]] = {
    "obehandlad": {"grovhet": 0.74, "gamma": 1.0, "ton": (1.0, 1.0, 1.0), "vit": 0.0, "lack": 0.0, "relief": 1.0},
    "olja": {"grovhet": 0.46, "gamma": 1.18, "ton": (1.0, 0.95, 0.84), "vit": 0.0, "lack": 0.0, "relief": 0.6},
    "lack": {"grovhet": 0.42, "gamma": 1.12, "ton": (1.0, 0.97, 0.9), "vit": 0.0, "lack": 0.7, "relief": 0.35},
    "vitpigmenterad": {"grovhet": 0.5, "gamma": 1.0, "ton": (1.0, 1.0, 1.0), "vit": 0.22, "lack": 0.0,
                       "relief": 0.6},
}


def virke(g: Graf, p: dict) -> None:
    """Trä ur en stock: varje bit (objekt) och varje lamell är sågad ur en egen stock, med märgen på ett slumpat avstånd
    och åt ett slumpat håll från biten och stocken något lutande mot biten, så att årsringarnas skärning med ytorna ger
    flammor, spetsbågar eller raka ränder (flader, halvkvarter, kvarter) och inga två bitar blir lika. Årsringarna är
    vågiga och olika breda år från år; barrträ har mörkare sommarved mot ringens slut, ringporigt trä (ask) ett band av
    porer i vårveden, som syns som mörka streck längs fibrerna. Kvistar som grenar från märgen, med egna ringar och
    mörk kant, och fibrerna som böjer runt dem; kärnved; fibrer och färgskiftning per bit; ytbehandling.

    Parametrar: art (gran, furu, lark, ask) och dess värden (ARTER), riktning (fibrerna) och tvars, lamell (axel) och
    lamelltjocklek [mm] för limträ och lamellskivor, yta (YTOR), variation. Färgerna kommer ur arten: materialets
    färg (farg, för webbvisaren) används inte."""
    d = {**ARTER[str(p.get("art", "gran"))], **{k: v for k, v in p.items() if k != "farg"}}
    yta = YTOR[str(d.get("yta", "obehandlad"))]
    m, kv, lin = g.matte, g.kv, g.linj
    rikt, tv = str(d.get("riktning", "x")), str(d.get("tvars", "y"))
    L, T, D = g.axlar(rikt, tv)
    rob = g.objslump()
    nr: Sockel = 0.0
    lam = d.get("lamell")
    if lam:
        tl = _f(d, "lamelltjocklek", 45.0) / 1000
        lc = g.sep(g.koord)[AXEL[str(lam)]]
        nr = m("FLOOR", m("DIVIDE", lc, tl))
        inom = m("SUBTRACT", lc, m("MULTIPLY", nr, tl))
        if lam == tv:
            T = inom
        else:
            D = inom
    # slumptal per bit och lamell
    s1, s2, s3, s4 = g.slump4(m("ADD", m("MULTIPLY", rob, 1000.0), m("MULTIPLY", nr, 7.31)))
    s5, s6, s7, s8 = g.slump4(m("ADD", m("MULTIPLY", rob, 517.3), m("MULTIPLY", nr, 3.17)))
    s9, s10, s11, s12 = g.slump4(m("ADD", m("MULTIPLY", rob, 263.9), m("MULTIPLY", nr, 11.9)))
    mmin, mmax = (float(v) for v in d["marg"])  # type: ignore[union-attr]
    rm = lin((s1, mmax - mmin), bas=mmin)
    fi = m("MULTIPLY", s2, 2 * math.pi)
    lut = math.tan(math.radians(_f(d, "lutning", 1.5)))
    dt = m("SUBTRACT", m("SUBTRACT", T, m("MULTIPLY", rm, m("COSINE", fi))),
           m("MULTIPLY", L, lin((s3, 2 * lut), bas=-lut)))
    dd = m("SUBTRACT", m("SUBTRACT", D, m("MULTIPLY", rm, m("SINE", fi))),
           m("MULTIPLY", L, lin((s4, 2 * lut), bas=-lut)))
    r0 = m("SQRT", m("ADD", m("ADD", kv(dt), kv(dd)), 1e-10))
    # vågiga ringar: avvikelsen beror på riktningen runt märgen och läget längs stocken
    ri = g.vektor(m("DIVIDE", dt, r0), m("DIVIDE", dd, r0), m("ADD", m("MULTIPLY", L, 0.35), m("MULTIPLY", s5, 31.0)))
    vag = m("SUBTRACT", g.brus(ri, 1.6, 3.0, 0.55), 0.5)
    r = lin((r0, 1.0), (m("MULTIPLY", r0, vag), 0.12),
            (m("SUBTRACT", g.brus(g.vektor(m("MULTIPLY", L, 2.5), m("MULTIPLY", dt, 9.0), m("MULTIPLY", dd, 9.0)),
                                  1.0, 2.0), 0.5), 0.0025))

    # kvistar: grenar från märgen, en möjlig per cell längs biten
    kvist: Sockel = 0.0
    kant: Sockel = 0.0
    kvistring: Sockel = 0.0
    if _f(d, "kvistar", 0.0) > 0:
        kc = 1.0 / _f(d, "kvistar", 1.0)
        W = m("ADD", m("DIVIDE", L, kc), m("MULTIPLY", s6, 97.0))
        vor = g.nod("ShaderNodeTexVoronoi", {"voronoi_dimensions": "1D"}, W=W, Scale=1.0)
        k1, k2, k3 = g.sep(g.utgang(vor, "Color"))
        lk = m("MULTIPLY", m("SUBTRACT", g.utgang(vor, "W"), m("MULTIPLY", s6, 97.0)), kc)
        fk = m("MULTIPLY", k1, 2 * math.pi)
        a = m("ADD", m("MULTIPLY", dt, m("COSINE", fk)), m("MULTIPLY", dd, m("SINE", fk)))       # längs grenen
        tv_ = m("SUBTRACT", m("MULTIPLY", dd, m("COSINE", fk)), m("MULTIPLY", dt, m("SINE", fk)))
        dl = m("SUBTRACT", m("SUBTRACT", L, lk), m("MULTIPLY", a, 0.22))
        rk = m("MULTIPLY", m("ADD", 0.45, m("MULTIPLY", g.jamn(a, 0.0, 0.06), 0.55)),
               m("MULTIPLY", lin((k3, 0.9), bas=0.55), _f(d, "kvist", 20.0) / 2000))
        rho = m("DIVIDE", m("SQRT", m("ADD", kv(tv_), kv(m("MULTIPLY", dl, 0.8)))), rk)
        finns = m("MULTIPLY", m("LESS_THAN", k2, 0.75), m("GREATER_THAN", a, 0.0))
        kvist = m("MULTIPLY", finns, g.jamn(rho, 1.0, 0.86))
        kant = m("MULTIPLY", finns, m("MULTIPLY", g.jamn(rho, 0.72, 0.93), g.jamn(rho, 1.12, 0.99)))
        kvistring = m("MULTIPLY", kvist, g.jamn(m("FRACT", m("DIVIDE", m("MULTIPLY", rho, rk), 0.0011)), 0.35, 0.85))
        # fibrerna böjer runt kvisten: ringarna buktar
        r = m("ADD", r, m("MULTIPLY", finns, m("MULTIPLY", m("EXPONENT", m("MULTIPLY", kv(rho), -0.35)), 0.004)))

    # årsringarna: olika breda år från år och bit från bit
    w = m("MULTIPLY", _f(d, "arsring", 3.0) / 1000, lin((s7, 0.6), bas=0.7))
    ar = lin((m("DIVIDE", r, w), 1.0), (m("SUBTRACT", g.brus1(m("ADD", m("MULTIPLY", r, 22.0), m("MULTIPLY", s8, 50.0)),
                                                          1.0, 3.0), 0.5), 1.4),
             (m("SUBTRACT", g.brus1(m("ADD", m("MULTIPLY", r, 150.0), m("MULTIPLY", s8, 70.0)), 1.0, 2.0), 0.5), 0.4))
    f = m("FRACT", ar)
    aret = lin((g.slump(m("ADD", m("FLOOR", ar), m("MULTIPLY", s8, 1000.0))), 0.7), bas=0.55)    # årets tydlighet
    porer: Sockel = 0.0
    if d.get("ringtyp") == "ringporig":
        # porbandet (porband mm) i början av ringen; sommarveden tät och ljus, något mörkare mot ringens slut
        fp = min(0.45, _f(d, "porband", 0.6) / _f(d, "arsring", 3.0))
        fpa = m("MULTIPLY", aret, fp)
        band = m("MULTIPLY", g.jamn(f, 0.0, 0.03), g.jamn(f, m("MULTIPLY", fpa, 1.4), m("MULTIPLY", fpa, 0.7)))
        sen = m("MULTIPLY", g.jamn(f, 0.6, 1.0), _f(d, "sommarved", 0.3))
        pv = g.vektor(m("MULTIPLY", L, 140.0), m("MULTIPLY", T, 3800.0), m("MULTIPLY", D, 3800.0))
        stora = g.jamn(g.brus(pv, 1.0, 1.0), 0.58, 0.68)
        sma = g.jamn(g.brus(g.vektor(m("MULTIPLY", L, 260.0), m("MULTIPLY", T, 7000.0), m("MULTIPLY", D, 7000.0)),
                            1.0, 1.0), 0.72, 0.8)
        porer = lin((m("MULTIPLY", m("MULTIPLY", band, stora), aret), 1.0), (m("MULTIPLY", sma, 0.25), 1.0), klamp=True)
        ton = m("MULTIPLY", lin((band, 0.55), (sen, 1.0), klamp=True), aret)
    else:
        ton = m("MULTIPLY", m("POWER", g.jamn(f, 0.48, 0.94), 1.6), aret)
    fib = g.brus(g.vektor(m("MULTIPLY", L, 7.0), m("MULTIPLY", T, 800.0), m("MULTIPLY", D, 800.0)), 1.0, 4.0, 0.6)
    flack = g.brus(g.vektor(m("MULTIPLY", L, 0.7), m("MULTIPLY", T, 4.0), m("MULTIPLY", D, 4.0)), 1.0, 2.0)

    c1, c2 = rgba(str(d["farg"])), rgba(str(d["farg2"]))
    col = g.blanda(m("MULTIPLY", ton, _f(d, "kontrast", 0.6)), c1, c2)
    if _f(d, "karnandel", 0.0) > 0:
        r0k, r1k = (float(v) for v in d.get("karnradie", (0.05, 0.15)))  # type: ignore[union-attr]
        rh = lin((s9, r1k - r0k), bas=r0k)
        karn = m("MULTIPLY", m("LESS_THAN", s10, _f(d, "karnandel", 0.0)),
                 g.jamn(m("ADD", r0, m("MULTIPLY", vag, 0.02)), m("ADD", rh, 0.008), m("SUBTRACT", rh, 0.008)))
        col = g.blanda(m("MULTIPLY", karn, 0.75), col, rgba(str(d.get("karnfarg", d["farg2"]))))
    var = _f(d, "variation", 0.07)
    col = g.ljus(col, lin((m("SUBTRACT", s11, 0.5), 2 * var), (m("SUBTRACT", flack, 0.5), 0.1),
                         (m("SUBTRACT", fib, 0.5), 0.16), (porer, -0.55), bas=1.0))
    col = g.blanda(m("MULTIPLY", s12, _f(d, "varm", 0.25)), col, rgba("#d8b27c")) if var > 0 else col  # varmare bitar
    if _f(d, "kvistar", 0.0) > 0:
        kf = rgba(str(d["kvistfarg"]))
        col = g.blanda(m("MULTIPLY", kvist, lin((kvistring, -0.35), bas=0.85)), col, kf)
        col = g.blanda(m("MULTIPLY", kant, 0.9), col, rgba(str(d["kvistfarg"]), 0.5))
    # ytbehandlingen: oljan fördjupar färgen, vitpigment ljusar
    if yta["gamma"] != 1.0:
        col = g.nod("ShaderNodeGamma", Color=col, Gamma=yta["gamma"]).outputs[0]
    if yta["ton"] != (1.0, 1.0, 1.0):
        col = g.vmatte("MULTIPLY", col, yta["ton"])
    if _f(yta, "vit", 0.0) > 0:
        col = g.blanda(yta["vit"], col, rgba("#f4efe6"))
    rel = _f(yta, "relief", 1.0) * _f(d, "relief", 1.0)
    hojd = lin((m("SUBTRACT", fib, 0.5), 0.00025 * rel), (porer, -0.00035 * rel), (ton, 0.00008 * rel),
               (kvist, 0.00005))
    grov = lin((porer, 0.12), (m("SUBTRACT", fib, 0.5), 0.08), bas=_f(yta, "grovhet", 0.7))
    g.yta(col, grov, 0.0, hojd, styrka=1.0, avstand=1.0)
    if _f(yta, "lack", 0.0) > 0:
        g.bsdf.inputs["Coat Weight"].default_value = _f(yta, "lack", 0.0)
        g.bsdf.inputs["Coat Roughness"].default_value = 0.08
