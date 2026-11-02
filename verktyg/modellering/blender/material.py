"""Procedurella material för Blender (Cycles), utan bildtexturer: varje material byggs av noder ur ett fåtal
parametrar, som modellens material anger (trebodar/material.py, `rendering(...)`).

Riktningar anges i delens eget system (objektets lokala koordinater i GLB-filen): `riktning` är axeln längs vilken
fibrer eller brädor löper ("x", "y" eller "z"), `tvars` axeln längs vilken brädorna upprepas. Mått i mm, färger
"#rrggbb" (sRGB). Det som skiljer delar av samma material åt (stenar, plåtbanor) slumpas per objekt. Typer:

| Typ | Parametrar |
|---|---|
| farg | farg, grovhet, metall, opacitet: enfärgad yta |
| tra | farg, farg2 (mörka ådror), riktning, arsring: konstruktionsvirke med årsringar |
| limtra | som tra och lamell (axel), lamelltjocklek: limträ med lameller och limfogar |
| bradpanel | se nedan: sågade brädor |
| plat | farg, metall, grovhet, variation, grovhet_variation, buckla, avstand, riktning, tvars: plåt i banor |
| granit | farg, farg2, farg3, rosa, andelar, korn, variation, varm, varmfarg, rost, rostfarg: kluven granit |
| betong, bruk, berg, mark, grus, cellplast, isolering, papp | farg, farg2: brusiga ytor |
| glas, folie | farg, opacitet: genomskinliga |

bradpanel: brädor med bredden `bredd` och fogen `fog` tvärs `tvars`, var och en sågad ur en stock: årsringarna är
skärningen mellan brädans yta och stockens ringar (`arsring` mellan ringarna), med märgen slumpad per bräda och
stocken något lutande, så att ringarna bildar flammor och spetsbågar. Kvistar (`kvistar` per meter bräda,
diameter `kvist`) med ringar och mörk kant, och ådringen böjer runt dem. Sågad yta: fibrer, ludd och sågmärken.
Strimmor (`strimmor`) längs brädorna och färgskiftning per bräda (`variation`). Skruvar i rader (`skruv_cc`,
`skruv_start` längs brädorna, `skruv_per_brada`, `skruv_kant` från brädans kant, diameter `skruv`).
`behandling` ger utgångsvärden: tackfarg (färgen farg och farg2 täcker, ådring och kvistar anas genom färgen
med `genomslag`), jarnvitriol (grånat trä: farg vårved, farg2 sommarved, farg3 brunare brädor med andelen `brun`,
kvistfarg) och obehandlad.
"""
from __future__ import annotations

import math

import bpy

# Modellens axlar i objektets koordinater i Blender: glTF-importen vänder y uppåt till z uppåt i näten, så
# modellens (x, y, z) blir Blenders (x, −z, y). Mönstren bryr sig inte om tecknet.
AXEL = {"x": 0, "y": 2, "z": 1}

Sockel = object                   # nodsockel eller tal


def linjar(h: str) -> tuple[float, float, float]:
    """sRGB "#rrggbb" -> linjär RGB."""
    def f(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return tuple(f(int(h[i:i + 2], 16) / 255) for i in (1, 3, 5))  # type: ignore[return-value]


def rgba(h: str, k: float = 1.0) -> tuple[float, float, float, float]:
    c = linjar(h)
    return (min(1.0, c[0] * k), min(1.0, c[1] * k), min(1.0, c[2] * k), 1.0)


def skala(rgb: tuple[float, float, float], k: float) -> tuple[float, float, float, float]:
    return (min(1.0, rgb[0] * k), min(1.0, rgb[1] * k), min(1.0, rgb[2] * k), 1.0)


class Graf:
    """Hjälp för att bygga ett nodträd: g.nod(typ, Input=värde eller sockel, ...), g.matte(op, a, b)."""

    def __init__(self, mat: bpy.types.Material):
        mat.use_nodes = True
        self.nt = mat.node_tree
        for n in list(self.nt.nodes):
            self.nt.nodes.remove(n)
        self.ut = self.nod("ShaderNodeOutputMaterial")
        self.bsdf = self.nod("ShaderNodeBsdfPrincipled")
        self.nt.links.new(self.bsdf.outputs["BSDF"], self.ut.inputs["Surface"])
        self.koord = self.nod("ShaderNodeTexCoord").outputs["Object"]

    def nod(self, typ: str, egenskaper: dict[str, object] | None = None, **ing: object) -> bpy.types.Node:
        """Ny nod med egenskaperna (sätts först, t.ex. dimensioner som avgör vilka ingångar som finns) och
        ingångarna."""
        n = self.nt.nodes.new(typ)
        for k, v in (egenskaper or {}).items():
            setattr(n, k, v)
        for k, v in ing.items():
            self.satt(n.inputs[k], v)
        return n

    def satt(self, sockel: bpy.types.NodeSocket, v: object) -> None:
        if isinstance(v, bpy.types.NodeSocket):
            self.nt.links.new(v, sockel)
        elif isinstance(v, tuple) and len(v) == 4 and len(sockel.default_value) == 3:
            sockel.default_value = v[:3]              # färg (RGBA) till en vektor
        else:
            sockel.default_value = v

    @staticmethod
    def utgang(n: bpy.types.Node, *namn: str) -> bpy.types.NodeSocket:
        """Utgången med något av namnen (Blender har bytt namn på en del, t.ex. Fac till Factor)."""
        for k in namn:
            s = n.outputs.get(k)
            if s is not None:
                return s
        raise KeyError(namn)

    def matte(self, op: str, a: Sockel, b: Sockel = 0.0, klamp: bool = False) -> bpy.types.NodeSocket:
        n = self.nt.nodes.new("ShaderNodeMath")
        n.operation = op
        n.use_clamp = klamp
        self.satt(n.inputs[0], a)
        self.satt(n.inputs[1], b)
        return n.outputs[0]

    def kv(self, a: Sockel) -> bpy.types.NodeSocket:
        return self.matte("MULTIPLY", a, a)

    def linj(self, *termer: tuple[Sockel, float], bas: float = 0.0, klamp: bool = False) -> Sockel:
        """bas + Σ vikt · (värde) – för att väga ihop mönster."""
        s: Sockel = bas
        for v, k in termer:
            s = self.matte("ADD", s, self.matte("MULTIPLY", v, k))
        return self.matte("ADD", s, 0.0, klamp) if klamp else s

    def axlar(self, riktning: str = "x", tvars: str = "y") -> tuple[bpy.types.NodeSocket, ...]:
        """(längs, tvärs, djup) i meter ur objektets koordinater."""
        ia, it = AXEL[riktning], AXEL[tvars]
        return self.sep(self.koord)[ia], self.sep(self.koord)[it], self.sep(self.koord)[3 - ia - it]

    def sep(self, v: Sockel) -> tuple[bpy.types.NodeSocket, ...]:
        n = self.nod("ShaderNodeSeparateXYZ", Vector=v)
        return n.outputs[0], n.outputs[1], n.outputs[2]

    def vektor(self, a: Sockel, b: Sockel, c: Sockel) -> bpy.types.NodeSocket:
        return self.nod("ShaderNodeCombineXYZ", X=a, Y=b, Z=c).outputs["Vector"]

    def vmatte(self, op: str, a: Sockel, b: Sockel) -> bpy.types.NodeSocket:
        """Vektoroperation; DOT_PRODUCT och LENGTH ger ett tal."""
        n = self.nt.nodes.new("ShaderNodeVectorMath")
        n.operation = op
        self.satt(n.inputs[0], a)
        self.satt(n.inputs[3] if op == "SCALE" else n.inputs[1], b)
        return n.outputs[1] if op in ("DOT_PRODUCT", "LENGTH", "DISTANCE") else n.outputs[0]

    def ramp(self, fak: Sockel, farger: list[tuple[float, tuple[float, float, float, float]]],
             konstant: bool = False) -> bpy.types.NodeSocket:
        n = self.nt.nodes.new("ShaderNodeValToRGB")
        self.satt(n.inputs["Fac"], fak)
        if konstant:
            n.color_ramp.interpolation = "CONSTANT"
        el = n.color_ramp.elements
        el[0].position, el[0].color = farger[0]
        el[1].position, el[1].color = farger[-1]
        for pos, c in farger[1:-1]:
            e = el.new(pos)
            e.color = c
        return n.outputs["Color"]

    def brus(self, vektor: Sockel, skala_: float, detalj: float = 4.0, grovhet: float = 0.5) -> bpy.types.NodeSocket:
        n = self.nod("ShaderNodeTexNoise", Vector=vektor, Scale=skala_, Detail=detalj, Roughness=grovhet)
        return self.utgang(n, "Factor", "Fac")

    def brus1(self, w: Sockel, skala_: float = 1.0, detalj: float = 2.0) -> bpy.types.NodeSocket:
        n = self.nod("ShaderNodeTexNoise", {"noise_dimensions": "1D"}, W=w, Scale=skala_, Detail=detalj)
        return self.utgang(n, "Factor", "Fac")

    def slump(self, varde: Sockel) -> bpy.types.NodeSocket:
        """Slumptal 0–1 per heltal (t.ex. brädans nummer)."""
        return self.slump4(varde)[0]

    def slump4(self, varde: Sockel) -> tuple[bpy.types.NodeSocket, ...]:
        """Fyra oberoende slumptal 0–1 per värde."""
        n = self.nt.nodes.new("ShaderNodeTexWhiteNoise")
        n.noise_dimensions = "1D"
        self.satt(n.inputs["W"], varde)
        return (n.outputs["Value"], *self.sep(n.outputs["Color"]))

    def objslump(self) -> bpy.types.NodeSocket:
        """Slumptal 0–1 per objekt (en sten, en plåtbana)."""
        return self.nod("ShaderNodeObjectInfo").outputs["Random"]

    def jamn(self, x: Sockel, a: float | Sockel, b: float | Sockel) -> bpy.types.NodeSocket:
        """Mjuk övergång från 0 vid a till 1 vid b (a > b vänder den)."""
        n = self.nt.nodes.new("ShaderNodeMapRange")
        n.interpolation_type = "SMOOTHSTEP"
        for i, v in enumerate((x, a, b, 0.0, 1.0)):
            self.satt(n.inputs[i], v)
        return n.outputs[0]

    def blanda(self, fak: Sockel, a: Sockel, b: Sockel) -> bpy.types.NodeSocket:
        n = self.nt.nodes.new("ShaderNodeMix")
        n.data_type = "RGBA"
        self.satt(n.inputs[0], fak)
        self.satt(n.inputs[6], a)
        self.satt(n.inputs[7], b)
        return n.outputs[2]

    def ljus(self, farg: Sockel, k: Sockel) -> bpy.types.NodeSocket:
        return self.vmatte("SCALE", farg, k)

    def yta(self, farg: Sockel, grovhet: Sockel = 0.8, metall: Sockel = 0.0, hojd: Sockel | None = None,
            styrka: float = 0.3, avstand: float = 0.002) -> None:
        self.satt(self.bsdf.inputs["Base Color"], farg)
        self.satt(self.bsdf.inputs["Roughness"], grovhet)
        self.satt(self.bsdf.inputs["Metallic"], metall)
        if hojd is not None:
            b = self.nod("ShaderNodeBump", Strength=styrka, Distance=avstand, Height=hojd)
            self.nt.links.new(b.outputs["Normal"], self.bsdf.inputs["Normal"])


def _f(p: dict, k: str, d: float) -> float:
    return float(p.get(k, d))


# ------------------------------------------------------------------ materialtyper

def farg(g: Graf, p: dict) -> None:
    g.yta((*linjar(p["farg"]), 1.0), _f(p, "grovhet", 0.6), _f(p, "metall", 0.0))
    if _f(p, "opacitet", 1.0) < 1.0:
        g.bsdf.inputs["Alpha"].default_value = _f(p, "opacitet", 1.0)


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
    "jarnvitriol": {"tackning": 0.0, "kvistfarg": "#2a2520", "farg3": "#7b6c5b", "brun": 0.45, "strimmor": 0.8,
                    "grovhet": 0.9, "relief": 1.0},
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
    rk = m("MULTIPLY", g.linj((kv(k3), 1.2), bas=0.55), _f(d, "kvist", 18.0) / 2000)
    langd = g.linj((m("FRACT", m("MULTIPLY", k2, 7.3)), 0.8), bas=1.0)
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
        kf = rgba(str(d.get("kvistfarg") or d.get("farg2", d["farg"])), 0.7)
        col = g.blanda(g.linj((kvist, 0.5), (kvistkant, 0.3)), col, kf)
    else:
        # trä: vårved (farg) och sommarved (farg2), vissa brädor brunare (farg3), mörka kvistar
        col = g.blanda(m("MULTIPLY", sen, 0.85), c1, c2)
        col = g.blanda(m("MULTIPLY", r4, _f(d, "brun", 0.3)), col, rgba(str(d.get("farg3", d["farg"]))))
        k = g.linj((m("SUBTRACT", r0, 0.5), 2 * var), (m("SUBTRACT", strim, 0.5), 0.6 * strimmor),
                   (m("SUBTRACT", flack, 0.5), 0.25 * strimmor), (m("SUBTRACT", fib, 0.5), 0.35),
                   (m("SUBTRACT", ludd, 0.5), 0.15), bas=1.0)
        col = g.ljus(col, k)
        kf = str(d.get("kvistfarg", "#3a2a1c"))
        col = g.blanda(m("MULTIPLY", kvistzon, 0.35), col, rgba(str(d.get("farg3", d["farg"])), 0.7))
        col = g.blanda(m("MULTIPLY", kvist, g.linj((kvistring, -0.45), bas=1.0)), col, rgba(kf))
        col = g.blanda(m("MULTIPLY", kvistkant, 0.7), col, rgba(kf, 0.6))
    col = g.ljus(col, m("MULTIPLY", g.linj((i_fog, -0.82), bas=1.0), g.linj((kant, -0.3), bas=1.0)))
    col = g.blanda(skruv, col, rgba(str(d.get("skruvfarg", "#b6b9bc"))))
    grov = g.linj((ludd, 0.12), (skruv, -0.55), bas=_f(d, "grovhet", 0.9) - 0.06)
    rel = _f(d, "relief", 1.0)
    hojd = g.linj((i_fog, -0.002), (kant, -0.0005), (m("SUBTRACT", fib, 0.5), 0.00035 * rel),
                  (m("SUBTRACT", ludd, 0.5), 0.00012 * rel), (sen, 0.00012 * rel), (sag, 0.00005 * rel),
                  (kvist, 0.0002), (skruv, 0.0006))
    g.yta(col, grov, skruv, hojd, styrka=1.0, avstand=1.0)


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


def pulverlack(g: Graf, p: dict) -> None:
    """Pulverlackerad metall: jämn kulör, halvblank, med fin apelsinyta (ingen metallglans)."""
    hojd = g.brus(g.koord, _f(p, "skala", 800.0), 3.0, 0.5)
    g.yta((*linjar(p["farg"]), 1.0), _f(p, "grovhet", 0.4), 0.0, hojd=hojd, styrka=0.04)


def glas(g: Graf, p: dict) -> None:
    g.yta((*linjar(p["farg"]), 1.0), 0.02)
    for k in ("Transmission Weight", "Transmission"):
        if k in g.bsdf.inputs:
            g.bsdf.inputs[k].default_value = 1.0
    g.bsdf.inputs["IOR"].default_value = 1.5


def folie(g: Graf, p: dict) -> None:
    g.yta((*linjar(p["farg"]), 1.0), 0.4)
    g.bsdf.inputs["Alpha"].default_value = _f(p, "opacitet", 0.5)


TYPER = {"farg": farg, "tra": tra, "limtra": limtra, "bradpanel": bradpanel, "plat": plat, "granit": granit,
         "glas": glas, "folie": folie, "pulverlack": pulverlack,
         "betong": lambda g, p: brusig(g, p, 3.0, 6.0, 0.2),
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
    if _f(p, "opacitet", 1.0) < 1.0:
        g.bsdf.inputs["Alpha"].default_value = _f(p, "opacitet", 1.0)
    return mat
