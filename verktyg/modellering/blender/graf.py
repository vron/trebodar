"""Hjälp för att bygga procedurella material i Blender: nodträd (Graf), färger och parametrar."""
from __future__ import annotations

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


def tal(p: dict, k: str, d: float) -> float:
    return float(p.get(k, d))


