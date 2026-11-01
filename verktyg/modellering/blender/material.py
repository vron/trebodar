"""Procedurella material för Blender (Cycles), utan bildtexturer: varje material byggs av noder ur ett fåtal
parametrar, som modellens material anger (trebodar/material.py, `rendering(...)`).

Riktningar anges i delens eget system (objektets lokala koordinater i GLB-filen): `riktning` är axeln längs vilken
fibrer, brädor eller falsar löper ("x", "y" eller "z"), `tvars` axeln längs vilken brädorna eller falsarna upprepas.
Mått i mm. Typer:

| Typ | Parametrar |
|---|---|
| farg | farg, grovhet, metall, opacitet: enfärgad yta |
| tra | farg, farg2 (mörka ådror), riktning, arsring (mm): konstruktionsvirke med årsringar |
| limtra | som tra och lamell (axel), lamelltjocklek (mm): limträ med lameller och limfogar |
| bradpanel | farg, farg2, riktning, tvars, bredd, fog, behandling (tackfarg, jarnvitriol, obehandlad), variation: sågade brädor |
| falsad_plat | farg, riktning, tvars, avstand, fals (mm): bandtäckt plåt med stående falsar |
| sten | farg, farg2, skift, langd, fog (mm), fogfarg: stenbeklädnad i skift (skift längs z) |
| betong, berg, mark, grus, cellplast, isolering, papp | farg, farg2: brusiga ytor |
| glas, folie | farg, opacitet: genomskinliga |
"""
from __future__ import annotations

import bpy

# Modellens axlar i objektets koordinater i Blender: glTF-importen vänder y uppåt till z uppåt i näten, så
# modellens (x, y, z) blir Blenders (x, −z, y). Mönstren bryr sig inte om tecknet.
AXEL = {"x": 0, "y": 2, "z": 1}


def linjar(h: str) -> tuple[float, float, float]:
    """sRGB "#rrggbb" -> linjär RGB."""
    def f(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return tuple(f(int(h[i:i + 2], 16) / 255) for i in (1, 3, 5))  # type: ignore[return-value]


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

    def nod(self, typ: str, **ing: object) -> bpy.types.Node:
        n = self.nt.nodes.new(typ)
        for k, v in ing.items():
            self.satt(n.inputs[k], v)
        return n

    def satt(self, sockel: bpy.types.NodeSocket, v: object) -> None:
        if isinstance(v, bpy.types.NodeSocket):
            self.nt.links.new(v, sockel)
        else:
            sockel.default_value = v

    def matte(self, op: str, a: object, b: object = 0.0) -> bpy.types.NodeSocket:
        n = self.nt.nodes.new("ShaderNodeMath")
        n.operation = op
        self.satt(n.inputs[0], a)
        self.satt(n.inputs[1], b)
        return n.outputs[0]

    def axlar(self, riktning: str = "x", tvars: str = "y") -> tuple[bpy.types.NodeSocket, ...]:
        """(längs, tvärs, djup) i meter ur objektets koordinater."""
        sep = self.nod("ShaderNodeSeparateXYZ", Vector=self.koord)
        ia, it = AXEL[riktning], AXEL[tvars]
        idj = 3 - ia - it
        return sep.outputs[ia], sep.outputs[it], sep.outputs[idj]

    def vektor(self, a: object, b: object, c: object) -> bpy.types.NodeSocket:
        return self.nod("ShaderNodeCombineXYZ", X=a, Y=b, Z=c).outputs["Vector"]

    def ramp(self, fak: object, farger: list[tuple[float, tuple[float, float, float, float]]]) -> bpy.types.NodeSocket:
        n = self.nt.nodes.new("ShaderNodeValToRGB")
        self.satt(n.inputs["Fac"], fak)
        el = n.color_ramp.elements
        el[0].position, el[0].color = farger[0]
        el[1].position, el[1].color = farger[-1]
        for pos, c in farger[1:-1]:
            e = el.new(pos)
            e.color = c
        return n.outputs["Color"]

    def brus(self, vektor: object, skala_: float, detalj: float = 4.0, grovhet: float = 0.5) -> bpy.types.NodeSocket:
        return self.nod("ShaderNodeTexNoise", Vector=vektor, Scale=skala_, Detail=detalj,
                        Roughness=grovhet).outputs["Fac"]

    def slump(self, varde: object) -> bpy.types.NodeSocket:
        """Slumptal 0–1 per heltal (t.ex. brädans nummer)."""
        n = self.nt.nodes.new("ShaderNodeTexWhiteNoise")
        n.noise_dimensions = "1D"
        self.satt(n.inputs["W"], varde)
        return n.outputs["Value"]

    def yta(self, farg: object, grovhet: object = 0.8, metall: float = 0.0, hojd: object = None,
            styrka: float = 0.3, avstand: float = 0.002) -> None:
        self.satt(self.bsdf.inputs["Base Color"], farg)
        self.satt(self.bsdf.inputs["Roughness"], grovhet)
        self.bsdf.inputs["Metallic"].default_value = metall
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
    fak = g.matte("ADD", g.matte("MULTIPLY", ringar.outputs["Fac"], 0.7), g.matte("MULTIPLY", fiber, 0.3))
    fak = g.matte("ADD", fak, g.matte("MULTIPLY", g.matte("SUBTRACT", distorsion, 0.5), 0.2))
    g.yta(g.ramp(fak, [(0.25, skala(mork, 0.85)), (0.65, (*ljus, 1.0)), (1.0, skala(ljus, 1.08))]),
          _f(p, "grovhet", 0.65), hojd=fiber, styrka=0.15)


def limtra(g: Graf, p: dict) -> None:
    tra(g, p)
    # lameller: färgskiftning per lamell och mörka limfogar
    sep = g.nod("ShaderNodeSeparateXYZ", Vector=g.koord)
    lam = sep.outputs[AXEL[p.get("lamell", "z")]]
    t = _f(p, "lamelltjocklek", 45.0) / 1000.0
    nr = g.matte("FLOOR", g.matte("DIVIDE", lam, t))
    inom = g.matte("SUBTRACT", g.matte("DIVIDE", lam, t), nr)
    fog = g.matte("LESS_THAN", inom, 0.04)
    ljus = g.matte("ADD", 0.92, g.matte("MULTIPLY", g.slump(nr), 0.16))
    ljus = g.matte("MULTIPLY", ljus, g.matte("SUBTRACT", 1.0, g.matte("MULTIPLY", fog, 0.45)))
    bas = g.bsdf.inputs["Base Color"].links[0].from_socket
    mul = g.nt.nodes.new("ShaderNodeVectorMath")
    mul.operation = "SCALE"
    g.nt.links.new(bas, mul.inputs[0])
    g.satt(mul.inputs["Scale"], ljus)
    g.nt.links.new(mul.outputs[0], g.bsdf.inputs["Base Color"])


def bradpanel(g: Graf, p: dict) -> None:
    """Sågade brädor: fogar, färgskiftning per bräda, sågad yta och ådring under färgen."""
    langs, tv, dj = g.axlar(p.get("riktning", "y"), p.get("tvars", "x"))
    b = _f(p, "bredd", 145.0) / 1000.0
    fog = _f(p, "fog", 4.0) / 1000.0
    nr = g.matte("FLOOR", g.matte("DIVIDE", tv, b))
    inom = g.matte("SUBTRACT", g.matte("DIVIDE", tv, b), nr)
    i_fog = g.matte("LESS_THAN", inom, fog / b)
    slump = g.slump(nr)
    # sågad yta: fint brus utdraget längs fibrerna
    sagad = g.brus(g.vektor(g.matte("MULTIPLY", langs, 3.0), g.matte("MULTIPLY", tv, 90.0),
                            g.matte("MULTIPLY", dj, 90.0)), 1.0, 8.0, 0.7)
    # ådring: band tvärs brädan, förskjutna per bräda
    adr_v = g.vektor(g.matte("ADD", g.matte("MULTIPLY", tv, 1.0), g.matte("MULTIPLY", slump, 0.37)),
                     g.matte("MULTIPLY", langs, 0.05), dj)
    adring = g.nod("ShaderNodeTexWave", Vector=adr_v, Scale=180.0, Distortion=4.0, Detail=2.0)
    adring.wave_type = "BANDS"
    adring.bands_direction = "X"
    behandling = p.get("behandling", "tackfarg")
    var = _f(p, "variation", 0.08)
    fak = g.matte("ADD", 0.5, g.matte("MULTIPLY", g.matte("SUBTRACT", slump, 0.5), var * 2))
    if behandling == "tackfarg":
        fak = g.matte("ADD", fak, g.matte("MULTIPLY", g.matte("SUBTRACT", sagad, 0.5), 0.25))
        fak = g.matte("ADD", fak, g.matte("MULTIPLY", adring.outputs["Fac"], 0.04))
    else:
        # oljad, laserad eller järnvitriol: ådringen och strimmor längs fibrerna syns
        strimmor = g.brus(g.vektor(g.matte("MULTIPLY", langs, 0.4), g.matte("MULTIPLY", tv, 12.0), dj), 2.0, 5.0)
        fak = g.matte("ADD", fak, g.matte("MULTIPLY", g.matte("SUBTRACT", strimmor, 0.5), 0.5))
        fak = g.matte("ADD", fak, g.matte("MULTIPLY", adring.outputs["Fac"], 0.18))
        fak = g.matte("ADD", fak, g.matte("MULTIPLY", g.matte("SUBTRACT", sagad, 0.5), 0.2))
    fak = g.matte("MULTIPLY", fak, g.matte("SUBTRACT", 1.0, g.matte("MULTIPLY", i_fog, 0.7)))
    c = linjar(p["farg"])
    c2 = linjar(p.get("farg2", p["farg"]))
    if behandling == "jarnvitriol":
        farger = [(0.15, skala(c2, 0.55)), (0.45, (*c2, 1.0)), (0.62, (*c, 1.0)), (0.9, skala(c, 1.18))]
    else:
        farger = [(0.1, skala(c2 if "farg2" in p else c, 0.45)), (0.5, (*c, 1.0)), (0.9, skala(c, 1.25))]
    hojd = g.matte("SUBTRACT", g.matte("MULTIPLY", sagad, 0.6), g.matte("MULTIPLY", i_fog, 1.5))
    g.yta(g.ramp(fak, farger), g.matte("ADD", _f(p, "grovhet", 0.9) - 0.05, g.matte("MULTIPLY", sagad, 0.1)),
          hojd=hojd, styrka=0.35, avstand=0.003)


def falsad_plat(g: Graf, p: dict) -> None:
    """Bandtäckt plåt: stående falsar med jämna mellanrum, svag skiftning mellan banden."""
    langs, tv, dj = g.axlar(p.get("riktning", "x"), p.get("tvars", "z"))
    a = _f(p, "avstand", 525.0) / 1000.0
    f = _f(p, "fals", 25.0) / 1000.0
    nr = g.matte("FLOOR", g.matte("DIVIDE", tv, a))
    inom = g.matte("SUBTRACT", g.matte("DIVIDE", tv, a), nr)
    fals = g.matte("LESS_THAN", inom, f / a)
    kant = g.matte("MULTIPLY", g.matte("LESS_THAN", inom, f / a + 0.004), g.matte("GREATER_THAN", inom, f / a))
    brus = g.brus(g.vektor(langs, g.matte("MULTIPLY", tv, 3.0), dj), 6.0, 3.0)
    fak = g.matte("ADD", 0.5, g.matte("MULTIPLY", g.matte("SUBTRACT", g.slump(nr), 0.5), 0.12))
    fak = g.matte("ADD", fak, g.matte("MULTIPLY", g.matte("SUBTRACT", brus, 0.5), 0.1))
    fak = g.matte("ADD", fak, g.matte("MULTIPLY", fals, 0.12))
    fak = g.matte("SUBTRACT", fak, g.matte("MULTIPLY", kant, 0.3))
    c = linjar(p["farg"])
    g.yta(g.ramp(fak, [(0.2, skala(c, 0.7)), (0.5, (*c, 1.0)), (0.85, skala(c, 1.2))]), _f(p, "grovhet", 0.4),
          metall=_f(p, "metall", 1.0), hojd=fals, styrka=0.6, avstand=0.02)


def sten(g: Graf, p: dict) -> None:
    """Stenbeklädnad i skift: skiften längs z, stenarna förskjutna halv längd mellan skiften."""
    sep = g.nod("ShaderNodeSeparateXYZ", Vector=g.koord)
    z = sep.outputs[AXEL["z"]]
    langs = g.matte("ADD", sep.outputs[AXEL["x"]], sep.outputs[AXEL["y"]])
    h = _f(p, "skift", 400.0) / 1000.0
    L = _f(p, "langd", 900.0) / 1000.0
    fog = _f(p, "fog", 10.0) / 1000.0
    rad = g.matte("FLOOR", g.matte("DIVIDE", z, h))
    iz = g.matte("SUBTRACT", g.matte("DIVIDE", z, h), rad)
    forskj = g.matte("MULTIPLY", g.matte("MODULO", rad, 2.0), 0.5 * L)
    lx = g.matte("ADD", langs, forskj)
    sten_nr = g.matte("FLOOR", g.matte("DIVIDE", lx, L))
    ix = g.matte("SUBTRACT", g.matte("DIVIDE", lx, L), sten_nr)
    i_fog = g.matte("MAXIMUM", g.matte("LESS_THAN", iz, fog / h), g.matte("LESS_THAN", ix, fog / L))
    slump = g.slump(g.matte("ADD", sten_nr, g.matte("MULTIPLY", rad, 137.0)))
    korn = g.brus(g.koord, 180.0, 2.0, 0.8)
    flack = g.brus(g.koord, 6.0, 4.0)
    fak = g.matte("ADD", g.matte("MULTIPLY", slump, 0.35), g.matte("MULTIPLY", korn, 0.4))
    fak = g.matte("ADD", fak, g.matte("MULTIPLY", flack, 0.25))
    c, c2 = linjar(p["farg"]), linjar(p.get("farg2", p["farg"]))
    stenfarg = g.ramp(fak, [(0.25, skala(c2, 0.5)), (0.5, (*c, 1.0)), (0.75, (*c2, 1.0)), (0.9, skala(c2, 1.15))])
    fogfarg = (*linjar(p.get("fogfarg", "#6b6865")), 1.0)
    mix = g.nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    g.satt(mix.inputs[0], i_fog)
    g.satt(mix.inputs[6], stenfarg)
    mix.inputs[7].default_value = fogfarg
    hojd = g.matte("SUBTRACT", g.matte("MULTIPLY", korn, 0.3), g.matte("MULTIPLY", i_fog, 1.0))
    g.yta(mix.outputs[2], _f(p, "grovhet", 0.8), hojd=hojd, styrka=0.5, avstand=0.004)


def brusig(g: Graf, p: dict, skala_: float, detalj: float = 6.0, bump: float = 0.3) -> None:
    c, c2 = linjar(p["farg"]), linjar(p.get("farg2", p["farg"]))
    n = g.brus(g.koord, skala_, detalj, 0.6)
    fin = g.brus(g.koord, skala_ * 12, 2.0, 0.7)
    fak = g.matte("ADD", g.matte("MULTIPLY", n, 0.75), g.matte("MULTIPLY", fin, 0.25))
    g.yta(g.ramp(fak, [(0.3, (*c2, 1.0)), (0.7, (*c, 1.0))]), _f(p, "grovhet", 0.9), hojd=fin, styrka=bump)


def glas(g: Graf, p: dict) -> None:
    g.yta((*linjar(p["farg"]), 1.0), 0.02)
    for k in ("Transmission Weight", "Transmission"):
        if k in g.bsdf.inputs:
            g.bsdf.inputs[k].default_value = 1.0
    g.bsdf.inputs["IOR"].default_value = 1.5


def folie(g: Graf, p: dict) -> None:
    g.yta((*linjar(p["farg"]), 1.0), 0.4)
    g.bsdf.inputs["Alpha"].default_value = _f(p, "opacitet", 0.5)


TYPER = {"farg": farg, "tra": tra, "limtra": limtra, "bradpanel": bradpanel, "falsad_plat": falsad_plat,
         "sten": sten, "glas": glas, "folie": folie,
         "betong": lambda g, p: brusig(g, p, 3.0, 6.0, 0.2),
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
