"""Inre ytor: målad gips, betong (slipat golv uppåt, gjuten yta annars) och kakel. Se material.py för parametrarna.

Mönster som ska ligga i rummets riktningar (kakel) använder världens koordinater och ytans normal: väggarna går längs
x eller y, golv och tak ligger i xy.
"""
from __future__ import annotations

from graf import Graf, Sockel, rgba
from graf import tal as _f


def gips(g: Graf, p: dict) -> None:
    """Målad gipsskiva: matt, svagt varm vit (färgen farg) med rollens fina struktur (apelsinyta), mycket svag
    skiftning över stora ytor och lite glans i strykljus."""
    m, lin = g.matte, g.linj
    k = g.koord
    stor = g.brus(k, 0.6, 3.0, 0.5)
    roll = g.brus(k, 350.0, 3.0, 0.65)
    fin = g.brus(k, 1600.0, 2.0, 0.6)
    col = g.ljus(rgba(str(p["farg"])), lin((m("SUBTRACT", stor, 0.5), 0.035), (m("SUBTRACT", roll, 0.5), 0.012),
                                            bas=1.0))
    hojd = lin((m("SUBTRACT", roll, 0.5), 0.00012), (m("SUBTRACT", fin, 0.5), 0.00003))
    g.yta(col, lin((roll, 0.06), bas=_f(p, "grovhet", 0.86) - 0.03), 0.0, hojd, styrka=1.0, avstand=1.0)
    g.bsdf.inputs["Specular IOR Level"].default_value = 0.35


def betong(g: Graf, p: dict) -> None:
    """Betong: ytor som vetter uppåt är slipat och impregnerat golv (ballast i genomskärning, molnig ton och slipspår,
    halvmatt glans som skiftar), övriga gjuten yta mot form (porer, fläckar, matt)."""
    m, lin = g.matte, g.linj
    k = g.koord
    normal = g.nod("ShaderNodeNewGeometry").outputs["Normal"]
    golv = g.jamn(g.sep(normal)[2], 0.7, 0.9)
    c1, c2 = rgba(str(p["farg"])), rgba(str(p.get("farg2", p["farg"])))
    # slipat golv: ballasten (stenar 3–16 mm i genomskärning) i olika gråtoner, cementpasta emellan
    vor = g.nod("ShaderNodeTexVoronoi", Vector=g.vmatte("ADD", k, g.vmatte("SCALE", g.utgang(
        g.nod("ShaderNodeTexNoise", Vector=k, Scale=60.0, Detail=2.0), "Color"), 0.004)), Scale=110.0)
    cell = g.utgang(vor, "Color")
    sten = m("LESS_THAN", g.utgang(vor, "Distance"), lin((g.sep(cell)[0], 0.25), bas=0.18))
    stenton = g.blanda(g.sep(cell)[1], rgba("#6d6a66"), rgba("#c8c4bd"))
    moln = g.brus(k, 1.1, 4.0, 0.55)
    slip = g.brus(g.vektor(m("MULTIPLY", g.sep(k)[0], 3.0), m("MULTIPLY", g.sep(k)[1], 3.0), 0.0), 9.0, 3.0, 0.6)
    pasta = g.ljus(g.blanda(moln, c2, c1), lin((m("SUBTRACT", slip, 0.5), 0.12), bas=1.0))
    golvfarg = g.blanda(m("MULTIPLY", sten, 0.55), pasta, stenton)
    golvgrov = lin((moln, 0.18), (m("SUBTRACT", slip, 0.5), 0.12), (sten, -0.05), bas=_f(p, "golv_grovhet", 0.32))
    # gjuten yta: porer och fläckar
    por = g.jamn(g.brus(k, 900.0, 1.0), 0.72, 0.8)
    flack = g.brus(k, 4.0, 4.0, 0.6)
    form = g.ljus(g.blanda(flack, c2, c1), lin((por, -0.35), (m("SUBTRACT", g.brus(k, 30.0, 3.0), 0.5), 0.12),
                                              bas=1.0))
    col = g.blanda(golv, form, golvfarg)
    grov = lin((golv, 1.0), bas=0.0)
    grov = m("ADD", m("MULTIPLY", grov, golvgrov), m("MULTIPLY", m("SUBTRACT", 1.0, grov), lin((por, 0.05), bas=0.88)))
    hojd = lin((por, -0.0004), (m("SUBTRACT", g.brus(k, 200.0, 3.0), 0.5), 0.00015),
               (m("SUBTRACT", slip, 0.5), 0.00002))
    g.yta(col, grov, 0.0, hojd, styrka=1.0, avstand=1.0)


def _kalksten(g: Graf, p: dict, k: Sockel) -> tuple[Sockel, Sockel, Sockel]:
    """Kalksten (Bricmate Jura): molnig ton mellan farg och farg2 i flera skalor, ljusare stråk, korn, fina porer och
    små fläckar (farg3), slipad och halvmatt; k är punkten (världens koordinater, förskjuten per platta). Ger färgen,
    grovheten och höjden."""
    m, lin = g.matte, g.linj
    c1, c2 = rgba(str(p["farg"])), rgba(str(p.get("farg2", p["farg"])))
    c3 = rgba(str(p.get("farg3", p.get("farg2", p["farg"]))))
    s = _f(p, "skala", 3.0)
    moln = g.brus(k, s, 6.0, 0.66)
    stor = g.brus(k, s * 0.35, 3.0, 0.5)
    ton = g.jamn(lin((moln, 0.8), (stor, 0.4), bas=-0.1), 0.44, 0.66)
    farg = g.blanda(ton, c1, c2)
    strak = g.jamn(g.brus(g.vmatte("MULTIPLY", k, g.vektor(1.0, 1.0, 4.0)), s * 2.2, 3.0, 0.6), 0.6, 0.72)
    farg = g.ljus(farg, lin((strak, 0.06), (m("SUBTRACT", g.brus(k, 120.0, 2.0, 0.6), 0.5), 0.1), bas=1.0))
    por = g.jamn(g.brus(k, 700.0, 1.0, 0.5), 0.68, 0.74)
    flack = g.jamn(g.brus(k, 90.0, 2.0, 0.55), 0.72, 0.78)
    farg = g.blanda(m("MAXIMUM", m("MULTIPLY", por, 0.6), m("MULTIPLY", flack, 0.75)), farg, c3)
    grov = lin((por, 0.15), bas=_f(p, "grovhet", 0.55))
    hojd = lin((por, -0.00015), (m("SUBTRACT", g.brus(k, 300.0, 2.0), 0.5), 0.00003))
    return farg, grov, hojd


def kalksten(g: Graf, p: dict) -> None:
    """Skivor av kalkstensimiterande granitkeramik (bänkskivorna): kalkstenen i världens koordinater, utan fogar."""
    farg, grov, hojd = _kalksten(g, p, g.nod("ShaderNodeNewGeometry").outputs["Position"])
    g.yta(farg, grov, 0.0, hojd, styrka=1.0, avstand=1.0)


def kakel(g: Graf, p: dict) -> None:
    """Kakel: plattor (storlek mm, och hojd mm uppåt på väggar och längs y på golv om den anges) med fogar (fog mm,
    fogfarg), svag skiftning per platta (variation) och lätt rundade kanter; rutnätet i världens koordinater, i
    väggens plan (x eller y efter normalen, och z) eller i golvets, så att fogarna går runt hörnen. Med sten = 1 är
    plattorna kalksten (_kalksten, olika i varje platta), annars blank glasyr i färgen farg."""
    m, lin = g.matte, g.linj
    pos = g.nod("ShaderNodeNewGeometry").outputs["Position"]
    x, y, z = g.sep(pos)
    n = g.sep(g.nod("ShaderNodeNewGeometry").outputs["Normal"])
    langs_y = m("GREATER_THAN", m("ABSOLUTE", n[0]), m("ABSOLUTE", n[1]))      # väggen går längs y
    plan = m("GREATER_THAN", m("ABSOLUTE", n[2]), 0.7)
    u = lin((m("MULTIPLY", langs_y, y), 1.0), (m("MULTIPLY", m("SUBTRACT", 1.0, langs_y), x), 1.0))
    v = lin((m("MULTIPLY", plan, y), 1.0), (m("MULTIPLY", m("SUBTRACT", 1.0, plan), z), 1.0))
    u = lin((m("MULTIPLY", plan, x), 1.0), (m("MULTIPLY", m("SUBTRACT", 1.0, plan), u), 1.0))
    su = _f(p, "storlek", 200.0) / 1000
    sv = _f(p, "hojd", su * 1000) / 1000
    f = _f(p, "fog", 2.0) / 1000
    iu, iv = m("FLOOR", m("DIVIDE", u, su)), m("FLOOR", m("DIVIDE", v, sv))
    fu = m("MULTIPLY", m("SUBTRACT", m("DIVIDE", u, su), iu), su)
    fv = m("MULTIPLY", m("SUBTRACT", m("DIVIDE", v, sv), iv), sv)
    kant = m("MINIMUM", m("MINIMUM", fu, m("SUBTRACT", su, fu)), m("MINIMUM", fv, m("SUBTRACT", sv, fv)))
    fog = g.jamn(kant, f / 2, f / 2 - 0.0004)
    rund = g.jamn(kant, f / 2 + 0.0015, f / 2)
    r = g.slump(m("ADD", m("MULTIPLY", iu, 17.13), m("MULTIPLY", iv, 3.71)))
    skift = lin((m("SUBTRACT", r, 0.5), _f(p, "variation", 0.04)), bas=1.0)
    if _f(p, "sten", 0.0) > 0.0:
        # varje platta har sin egen bit av stenen: punkten förskjuten per platta
        k = g.vmatte("ADD", pos, g.vektor(m("MULTIPLY", r, 37.0), m("MULTIPLY", iu, 11.3), m("MULTIPLY", iv, 7.9)))
        sten, grov_s, hojd_s = _kalksten(g, p, k)
        platta = g.ljus(sten, skift)
    else:
        platta = g.ljus(rgba(str(p["farg"])), skift)
        grov_s, hojd_s = _f(p, "grovhet", 0.12), lin((m("SUBTRACT", g.brus(g.koord, 40.0, 2.0), 0.5), 0.00004))
    col = g.blanda(fog, platta, rgba(str(p.get("fogfarg", "#c9c7c2"))))
    grov = lin((fog, 0.7), (grov_s, 1.0))
    hojd = lin((fog, -0.0012), (rund, -0.0004), (hojd_s, 1.0))
    g.yta(col, grov, 0.0, hojd, styrka=1.0, avstand=1.0)
