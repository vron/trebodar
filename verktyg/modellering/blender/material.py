"""Procedurella material för Blender (Cycles), utan bildtexturer: varje material byggs av noder ur ett fåtal
parametrar, som modellens material anger (trebodar/material.py, `rendering(...)`).

Riktningar anges i delens eget system (objektets lokala koordinater i GLB-filen): `riktning` är axeln längs vilken
fibrer eller brädor löper ("x", "y" eller "z"), `tvars` axeln längs vilken brädorna upprepas. Mått i mm, färger
"#rrggbb" (sRGB). Det som skiljer delar av samma material åt (stenar, plåtbanor) slumpas per objekt. Typer:

| Typ | Parametrar |
|---|---|
| farg | farg, grovhet, metall, opacitet: enfärgad yta |
| virke | art (gran, furu, lark, ask), yta (obehandlad, olja, lack, vitpigmenterad), riktning, tvars, lamell, lamelltjocklek och artens värden (tra.ARTER): trä ur en stock per bit och lamell |
| tra | farg, farg2 (mörka ådror), riktning, arsring: enkelt virke med årsringar |
| limtra | som tra och lamell (axel), lamelltjocklek: limträ med lameller och limfogar |
| bradpanel | se nedan: sågade brädor |
| gips | farg, grovhet: målad gipsskiva (ytor.py) |
| betong | farg, farg2, golv_grovhet: slipat golv på ytor uppåt, annars gjuten yta (ytor.py) |
| kakel | farg, storlek, hojd, fog, fogfarg, variation, grovhet; sten, farg2, farg3, skala: plattor med fogar i väggens eller golvets plan, med sten = 1 av kalksten (ytor.py) |
| kalksten | farg, farg2, farg3, skala, grovhet: kalkstensimiterande skivor utan fogar (bänkskivorna) |
| plat | farg, metall, grovhet, variation, grovhet_variation, buckla, avstand, riktning, tvars: plåt i banor |
| granit | farg, farg2, farg3, rosa, andelar, korn, variation, varm, varmfarg, rost, rostfarg: kluven granit |
| pulverlack | farg, grovhet, skala: pulverlackerad metall med fin apelsinyta |
| patina | farg, farg2, andel, skala, grovhet, grovhet2: obehandlad metall (råmässing) med fläckar av oxid |
| bruk, berg, mark, grus, cellplast, isolering, papp | farg, farg2: brusiga ytor |
| glas | transmission, reflex_ior: fönsterglas (reflexen på den första ytan) |
| lins | farg, grovhet: armaturens lins, lyser för kameran när armaturen är tänd (objektens egenskaper) |
| folie | farg, opacitet: genomskinlig |

bradpanel: brädor med bredden `bredd` och fogen `fog` tvärs `tvars`, var och en sågad ur en stock: årsringarna är
skärningen mellan brädans yta och stockens ringar (`arsring` mellan ringarna), med märgen slumpad per bräda och
stocken något lutande, så att ringarna bildar flammor och spetsbågar. Kvistar (`kvistar` per meter bräda,
diameter `kvist`) med ringar och mörk kant, och ådringen böjer runt dem. Sågad yta: fibrer, ludd och sågmärken.
Strimmor (`strimmor`) längs brädorna, sågytans fibrer och ludd (`fibrer`, obehandlat trä) och färgskiftning per bräda
(`variation`); en del brädor är skarvade (andelen `skarvar`). Skruvar i rader (`skruv_cc`,
`skruv_start` längs brädorna, `skruv_per_brada`, `skruv_kant` från brädans kant, diameter `skruv`).
`behandling` ger utgångsvärden: tackfarg (färgen farg och farg2 täcker, ådring och kvistar anas genom färgen
med `genomslag`), jarnvitriol (grånat trä: farg vårved, farg2 sommarved, farg3 brunare brädor med andelen `brun`,
kvistfarg) och obehandlad.
"""
from __future__ import annotations

import math

import bpy

import tra
import ytor
from graf import Graf, linjar, rgba
from graf import tal as _f

# ------------------------------------------------------------------ materialtyper

def farg(g: Graf, p: dict) -> None:
    g.yta((*linjar(p["farg"]), 1.0), _f(p, "grovhet", 0.6), _f(p, "metall", 0.0))
    if _f(p, "opacitet", 1.0) < 1.0:
        g.bsdf.inputs["Alpha"].default_value = _f(p, "opacitet", 1.0)


def plat(g: Graf, p: dict) -> None:
    """Plåt i banor (en bana per objekt): skiftning i ton och glans per bana, svagt kuddformade banor (bucklor
    i plåten mellan falsarna) och fläckig patina."""
    m = g.matte
    L, T, _ = g.axlar(p.get("riktning", "x"), p.get("tvars", "z"))
    rs = g.objslump()
    rs2 = m("FRACT", m("MULTIPLY", rs, 7.31))
    patina = g.brus(g.koord, 2.5, 3.0)
    col = g.ljus(rgba(p["farg"]), g.linj((m("SUBTRACT", rs, 0.5), 2 * _f(p, "variation", 0.04)),
                                         (m("SUBTRACT", patina, 0.5), 0.06), bas=1.0))
    grov = g.linj((m("SUBTRACT", rs2, 0.5), _f(p, "grovhet_variation", 0.12)),
                  (m("SUBTRACT", g.brus(g.koord, 15.0, 2.0), 0.5), 0.04), bas=_f(p, "grovhet", 0.38))
    a = _f(p, "avstand", 525.0) / 1000
    kudde = m("ABSOLUTE", m("SINE", m("MULTIPLY", T, math.pi / a)))      # 0 vid falsarna, 1 mitt på banan
    vag = m("SUBTRACT", g.brus(g.vektor(m("MULTIPLY", L, 1.5), m("MULTIPLY", T, 4.0), m("MULTIPLY", rs, 10.0)), 1.0,
                               2.0), 0.5)
    b = _f(p, "buckla", 0.0015)
    hojd = g.linj((m("MULTIPLY", kudde, m("ADD", 0.4, rs)), b), (vag, 1.5 * b))
    g.yta(col, grov, _f(p, "metall", 1.0), hojd, styrka=1.0, avstand=1.0)


def granit(g: Graf, p: dict) -> None:
    """Granit med kluven yta: mineralkorn (fältspat grå och rosa, kvarts, glimmer) i oregelbundna korn, skiftning
    och värme per sten, rostfläckar och en skrovlig yta."""
    m = g.matte
    korn = _f(p, "korn", 4.0) / 1000
    rs = g.objslump()
    rs2 = m("FRACT", m("MULTIPLY", rs, 13.7))
    brus = g.nod("ShaderNodeTexNoise", Vector=g.koord, Scale=0.35 / korn, Detail=2.0)
    forsk = g.vmatte("SCALE", g.vmatte("SUBTRACT", g.utgang(brus, "Color"), (0.5, 0.5, 0.5)), 1.5 * korn)
    pd = g.vmatte("ADD", g.koord, forsk)
    vor = g.nod("ShaderNodeTexVoronoi", Vector=pd, Scale=1.0 / korn)
    m1, m2, _ = g.sep(g.utgang(vor, "Color"))
    ab, aq, ar = (float(v) for v in p.get("andelar", (0.06, 0.22, 0.18)))   # glimmer, kvarts, rosa fältspat
    biotit = rgba(p.get("farg3", "#2f2c2a"))
    mineral = g.ramp(m1, [(0.0, biotit), (ab, rgba(p.get("farg2", "#cfccc6"))),
                          (ab + aq, rgba(p.get("rosa", "#b39a8d"))), (ab + aq + ar, rgba(p["farg"]))], konstant=True)
    mineral = g.ljus(mineral, g.linj((m2, 0.28), bas=0.86))
    fjall = m("LESS_THAN", g.sep(g.utgang(g.nod("ShaderNodeTexVoronoi", Vector=pd, Scale=2.6 / korn), "Color"))[0],
              0.03)
    col = g.blanda(fjall, mineral, biotit)
    col = g.ljus(col, g.linj((m("SUBTRACT", rs, 0.5), 2 * _f(p, "variation", 0.08)), bas=1.0))
    col = g.blanda(m("MULTIPLY", rs2, _f(p, "varm", 0.15)), col, rgba(p.get("varmfarg", "#a8907c")))
    rost = m("MULTIPLY", g.jamn(g.brus(g.koord, 3.0, 5.0), 0.62, 0.8), _f(p, "rost", 0.4))
    col = g.blanda(m("MULTIPLY", rost, 0.55), col, rgba(p.get("rostfarg", "#8b6a48")))
    col = g.ljus(col, g.linj((g.brus(g.koord, 9.0, 3.0), 0.2), (g.brus(g.koord, 2.5, 2.0), 0.18), bas=0.81))
    kvarts = m("MULTIPLY", m("GREATER_THAN", m1, ab), m("LESS_THAN", m1, ab + aq))
    grov = g.linj((kvarts, -0.3), bas=_f(p, "grovhet", 0.78))
    # kluven yta: små plana brottytor med slumpad lutning (Voronoi-celler), ovanpå stenens fasetter
    fas = g.nod("ShaderNodeTexVoronoi", Vector=pd, Scale=1000.0 / _f(p, "brott", 55.0))
    lutning = g.vmatte("SCALE", g.vmatte("SUBTRACT", g.utgang(fas, "Color"), (0.5, 0.5, 0.5)),
                       2 * _f(p, "brottlutning", 0.18))
    brott = g.vmatte("DOT_PRODUCT", g.vmatte("SUBTRACT", pd, g.utgang(fas, "Position")), lutning)
    hojd = g.linj((brott, 1.0), (m("SUBTRACT", g.brus(g.koord, 9.0, 3.0), 0.5), 0.004),
                  (m("SUBTRACT", g.brus(g.koord, 22.0, 6.0, 0.6), 0.5), 0.0016),
                  (m("SUBTRACT", g.brus(g.koord, 110.0, 3.0), 0.5), 0.0004),
                  (m("SUBTRACT", 0.5, g.utgang(vor, "Distance")), 0.00015))
    g.yta(col, grov, 0.0, hojd, styrka=1.0, avstand=1.0)


def brusig(g: Graf, p: dict, skala_: float, detalj: float = 6.0, bump: float = 0.3) -> None:
    c, c2 = linjar(p["farg"]), linjar(p.get("farg2", p["farg"]))
    n = g.brus(g.koord, skala_, detalj, 0.6)
    fin = g.brus(g.koord, skala_ * 12, 2.0, 0.7)
    fak = g.linj((n, 0.75), (fin, 0.25))
    g.yta(g.ramp(fak, [(0.3, (*c2, 1.0)), (0.7, (*c, 1.0))]), _f(p, "grovhet", 0.9), hojd=fin, styrka=bump)


def patina(g: Graf, p: dict) -> None:
    """Obehandlad metall med patina (råmässing): metallens färg och glans med fläckar av mörkare och mattare oxid
    (andelen `andel` av ytan, storleken efter `skala`) och finare variation, förskjutna per objekt så att likadana
    delar skiljer sig åt."""
    k = g.vmatte("ADD", g.koord, g.vektor(g.objslump(), g.matte("MULTIPLY", g.objslump(), 3.7), 0.0))
    s = _f(p, "skala", 40.0)
    flackar = g.linj((g.brus(k, s, 4.0, 0.6), 0.7), (g.brus(k, s * 7.0, 3.0, 0.5), 0.3))
    t = 0.5 + (0.5 - _f(p, "andel", 0.3)) * 0.3
    fak = g.jamn(flackar, t - 0.05, t + 0.05)
    farg = g.blanda(fak, (*linjar(p["farg"]), 1.0), (*linjar(p["farg2"]), 1.0))
    grovhet = g.linj((fak, _f(p, "grovhet2", 0.7) - _f(p, "grovhet", 0.4)), bas=_f(p, "grovhet", 0.4))
    g.yta(farg, grovhet, g.linj((fak, -0.35), bas=1.0), hojd=g.brus(k, s * 25.0, 2.0, 0.5), styrka=0.02)


def pulverlack(g: Graf, p: dict) -> None:
    """Pulverlackerad metall: jämn kulör, halvblank, med fin apelsinyta (ingen metallglans)."""
    hojd = g.brus(g.koord, _f(p, "skala", 800.0), 3.0, 0.5)
    g.yta((*linjar(p["farg"]), 1.0), _f(p, "grovhet", 0.4), 0.0, hojd=hojd, styrka=0.04)


def glas(g: Graf, p: dict) -> None:
    """Fönsterglas (varje ruta en tunn låda, isolerrutan tre rutor): för kameran och i speglingar genomskinligt med
    reflex efter Fresnel; skugg- och diffusa strålar går rakt igenom (inga kaustiker), så att solen och himlen lyser in
    utan brus. Transmissionen per yta (två per ruta) ger ljustransmissionen `transmission` för hela rutan.

    Reflexen sitter bara på den första glasyta som strålen träffar och står för hela isolerrutans reflektans
    (reflex_ior 1,9: ca 10 % rakt framifrån, mer i flack vinkel); ytorna bakom släpper igenom. Annars studsar
    speglingarna mellan rutorna tills studsarna tar slut, och glasen blir svarta i flack vinkel."""
    # farg är CAD-färgen (webbvisaren); glasets egen ton är mycket svagt grön (floatglas), per yta roten ur rutans
    t = _f(p, "transmission", 0.89)
    farg = tuple(min(1.0, (t * k) ** 0.5) for k in (0.993, 1.0, 0.996)) + (1.0,)
    genom = g.nod("ShaderNodeBsdfTransparent", Color=farg)
    reflex = g.nod("ShaderNodeBsdfGlossy", Color=(1.0, 1.0, 1.0, 1.0), Roughness=0.0)
    fresnel = g.nod("ShaderNodeFresnel", IOR=_f(p, "reflex_ior", 1.9))
    lp = g.nod("ShaderNodeLightPath")
    forsta = g.matte("LESS_THAN", lp.outputs["Transparent Depth"], 0.5)
    glasyta = g.nod("ShaderNodeMixShader", Fac=g.matte("MULTIPLY", fresnel.outputs["Fac"], forsta))
    g.nt.links.new(genom.outputs[0], glasyta.inputs[1])
    g.nt.links.new(reflex.outputs[0], glasyta.inputs[2])
    kamera = g.matte("ADD", lp.outputs["Is Camera Ray"], lp.outputs["Is Glossy Ray"], klamp=True)
    val = g.nod("ShaderNodeMixShader", Fac=kamera)
    g.nt.links.new(genom.outputs[0], val.inputs[1])
    g.nt.links.new(glasyta.outputs[0], val.inputs[2])
    g.nt.links.new(val.outputs[0], g.ut.inputs["Surface"])


def lins(g: Graf, p: dict) -> None:
    """Armaturens reflektor och lins: vit och blank; lyser för kameran och i speglingar när armaturen är tänd, med
    objektens egenskaper "lysande" (luminansen i Blenders enheter, 0 släckt) och "lysande_farg" (sätts per vy, se
    scen.Armatur). Ljuset i rummet kommer från armaturens punktljus, inte från linsen."""
    g.yta((*linjar(p["farg"]), 1.0), _f(p, "grovhet", 0.15))
    styrka = g.nod("ShaderNodeAttribute", {"attribute_type": "OBJECT", "attribute_name": "lysande"})
    farg = g.nod("ShaderNodeAttribute", {"attribute_type": "OBJECT", "attribute_name": "lysande_farg"})
    lp = g.nod("ShaderNodeLightPath")
    synlig = g.matte("ADD", lp.outputs["Is Camera Ray"], lp.outputs["Is Glossy Ray"], klamp=True)
    g.satt(g.bsdf.inputs["Emission Color"], g.utgang(farg, "Color"))
    g.satt(g.bsdf.inputs["Emission Strength"], g.matte("MULTIPLY", g.utgang(styrka, "Fac"), synlig))


def folie(g: Graf, p: dict) -> None:
    g.yta((*linjar(p["farg"]), 1.0), 0.4)
    g.bsdf.inputs["Alpha"].default_value = _f(p, "opacitet", 0.5)


TYPER = {"farg": farg, "tra": tra.tra, "limtra": tra.limtra, "virke": tra.virke, "bradpanel": tra.bradpanel,
         "gips": ytor.gips, "betong": ytor.betong, "kakel": ytor.kakel, "kalksten": ytor.kalksten, "plat": plat,
         "granit": granit,
         "glas": glas, "folie": folie, "pulverlack": pulverlack, "lins": lins, "patina": patina,
         "bruk": lambda g, p: brusig(g, p, 40.0, 4.0, 0.4),
         "berg": lambda g, p: brusig(g, p, 0.8, 8.0, 0.6),
         "mark": lambda g, p: brusig(g, p, 2.5, 6.0, 0.4),
         "grus": lambda g, p: brusig(g, p, 40.0, 3.0, 0.8),
         "cellplast": lambda g, p: brusig(g, p, 200.0, 2.0, 0.2),
         "isolering": lambda g, p: brusig(g, p, 60.0, 6.0, 0.5),
         "papp": lambda g, p: brusig(g, p, 300.0, 2.0, 0.4)}


def skapa(namn: str, p: dict) -> bpy.types.Material:
    """Materialet `namn` (befintligt eller nytt) byggt efter parametrarna."""
    mat = bpy.data.materials.get(namn) or bpy.data.materials.new(namn)
    g = Graf(mat)
    TYPER.get(p.get("typ", "farg"), farg)(g, p)
    if _f(p, "opacitet", 1.0) < 1.0 and p.get("typ") != "glas":
        g.bsdf.inputs["Alpha"].default_value = _f(p, "opacitet", 1.0)
    return mat
