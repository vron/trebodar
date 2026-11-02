"""Scenen i Blender: himmel och sol efter dagsljuset (modellering/dagsljus.py), marken runt modellen, ljusportaler i
fönstren, kameror och exponering, och Cycles inställningar per kvalitet.

Enheter: Blenders scen i meter (modellens mm / 1000, z uppåt) och ljuset fotometriskt: solens styrka (W/m² i Blender)
är belysningen vinkelrätt mot solen i lux / 683, och himlen skalas så att dess belysning på en horisontell yta blir
dagsljusets diffusa belysning (mäts med en liten panoramarendering av himlen). Exponeringen i Blender är 9,94 − EV100
(ett grått kort, 18 %, med luminansen 12,5·2^EV/100 cd/m² blir 0,18), eller räknas fram ur en snabb förhandsbild.
"""
from __future__ import annotations

import math
import os
import tempfile

import bpy
import numpy as np
from mathutils import Matrix, Vector

LUMEN_PER_WATT = 683.0
REC709 = np.array([0.2126, 0.7152, 0.0722])
SOLSKIVA = 0.53

# kvaliteter: upplösning (bredd; höjd 16:9), största antal sampel, brustrsöskel för adaptiv sampling, studsar
KVALITET = {
    "skiss": {"bredd": 640, "sampel": 48, "troskel": 0.05, "studsar": 6},
    "utkast": {"bredd": 1280, "sampel": 160, "troskel": 0.03, "studsar": 8},
    "normal": {"bredd": 1920, "sampel": 384, "troskel": 0.015, "studsar": 10},
    "slutlig": {"bredd": 3840, "sampel": 1024, "troskel": 0.01, "studsar": 12},
}


# ------------------------------------------------------------------ rendering

def cycles(sc: bpy.types.Scene, kvalitet: dict[str, float], hojd_bredd: float = 9 / 16) -> None:
    sc.render.engine = "CYCLES"
    c = sc.cycles
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "METAL"
        prefs.get_devices()
        for d in prefs.devices:
            d.use = True
        c.device = "GPU"
    except Exception:
        pass
    c.samples = int(kvalitet["sampel"])
    c.use_adaptive_sampling = True
    c.adaptive_threshold = float(kvalitet["troskel"])
    c.adaptive_min_samples = 0
    c.use_denoising = True
    c.denoiser = "OPENIMAGEDENOISE"
    c.denoising_input_passes = "RGB_ALBEDO_NORMAL"
    c.denoising_prefilter = "ACCURATE"
    try:
        c.denoising_quality = "HIGH"
        c.denoising_use_gpu = True
    except (AttributeError, TypeError):
        pass
    c.use_light_tree = True
    n = int(kvalitet["studsar"])
    c.max_bounces = n
    c.diffuse_bounces = max(4, n - 4)
    c.glossy_bounces = 4
    c.transmission_bounces = 12
    c.transparent_max_bounces = 32
    c.caustics_reflective = False
    c.caustics_refractive = False
    c.blur_glossy = 1.0
    c.sample_clamp_direct = 0.0
    c.sample_clamp_indirect = 0.0
    c.film_exposure = 1.0
    sc.render.use_persistent_data = True
    sc.render.resolution_x = int(kvalitet["bredd"])
    sc.render.resolution_y = round(kvalitet["bredd"] * hojd_bredd)
    sc.render.resolution_percentage = 100
    try:
        sc.view_settings.view_transform = "Khronos PBR Neutral"
    except TypeError:
        sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "None"


def vitbalans(sc: bpy.types.Scene, kelvin: float | None) -> None:
    """Kamerans vitbalans (som kamerans dagsljusinställning); None stänger av den."""
    vs = sc.view_settings
    vs.use_white_balance = kelvin is not None
    if kelvin is not None:
        vs.white_balance_temperature = kelvin
        vs.white_balance_tint = 0.0


# ------------------------------------------------------------------ himmel och sol

class Himmel:
    """Världen: himlen (klar himmel med eller utan moln, eller mulen) och solen som en sollampa."""

    def __init__(self, sc: bpy.types.Scene):
        self.sc = sc
        w = bpy.data.worlds.get("Himmel") or bpy.data.worlds.new("Himmel")
        sc.world = w
        w.use_nodes = True
        self.nt = nt = w.node_tree
        for n in list(nt.nodes):
            nt.nodes.remove(n)
        self.ut = nt.nodes.new("ShaderNodeOutputWorld")
        self.bg = nt.nodes.new("ShaderNodeBackground")
        nt.links.new(self.bg.outputs["Background"], self.ut.inputs["Surface"])
        lampa = bpy.data.lights.get("Sol") or bpy.data.lights.new("Sol", "SUN")
        self.sol = bpy.data.objects.get("Sol") or bpy.data.objects.new("Sol", lampa)
        if self.sol.name not in sc.collection.objects:
            sc.collection.objects.link(self.sol)
        self.nyckel: str | None = None

    def _nod(self, typ: str, **ing: object) -> bpy.types.Node:
        n = self.nt.nodes.new(typ)
        for k, v in ing.items():
            if isinstance(v, bpy.types.NodeSocket):
                self.nt.links.new(v, n.inputs[k])
            else:
                n.inputs[k].default_value = v
        return n

    def _matte(self, op: str, a: object, b: object = 0.0) -> bpy.types.NodeSocket:
        n = self.nt.nodes.new("ShaderNodeMath")
        n.operation = op
        for i, v in enumerate((a, b)):
            if isinstance(v, bpy.types.NodeSocket):
                self.nt.links.new(v, n.inputs[i])
            else:
                n.inputs[i].default_value = v
        return n.outputs[0]

    def stall_in(self, ljus: dict, hojd_m: float = 0.0) -> None:
        """Himlen och solen efter dagsljuset (dagsljus.Ljus som dict)."""
        nyckel = repr(sorted((k, str(v)) for k, v in ljus.items()))
        if nyckel == self.nyckel:
            return
        self.nyckel = nyckel
        for n in list(self.nt.nodes):
            if n not in (self.ut, self.bg):
                self.nt.nodes.remove(n)
        d = Vector(ljus["riktning"]).normalized()
        el = math.degrees(math.asin(max(-1.0, min(1.0, d.z))))
        rot = math.atan2(d.x, d.y)                                  # Blenders himmel: från +y mot +x
        moln = float(ljus["moln"]) / 8.0
        himmel_lux = float(ljus["himmel_lux"])
        hrgb = np.array(ljus["himmel_farg"])
        if moln >= 0.999 or el <= 0.0:
            # CIE:s mulna himmel: L(θ) = Lz (1 + 2 cos θ) / 3, belysningen på horisontell yta 7π/9 Lz
            lz = 9 * (himmel_lux / LUMEN_PER_WATT) / (7 * math.pi)
            nz = self._nod("ShaderNodeSeparateXYZ", Vector=self._nod("ShaderNodeTexCoord").outputs["Generated"])
            uppat = self._matte("MAXIMUM", nz.outputs["Z"], 0.0)
            grad = self._matte("MULTIPLY", self._matte("ADD", self._matte("MULTIPLY", uppat, 2.0), 1.0), lz / 3)
            farg = self._nod("ShaderNodeVectorMath")
            farg.operation = "SCALE"
            farg.inputs[0].default_value = tuple(float(c) for c in hrgb)
            self.nt.links.new(grad, farg.inputs[3])
            self.nt.links.new(farg.outputs[0], self.bg.inputs["Color"])
            self.bg.inputs["Strength"].default_value = 1.0
        else:
            sky = self._nod("ShaderNodeTexSky")
            sky.sky_type = "SINGLE_SCATTERING"
            sky.sun_disc = False
            sky.sun_elevation = math.radians(el)
            sky.sun_rotation = rot
            sky.altitude = max(0.0, hojd_m)
            sky.air_density = 1.0
            sky.aerosol_density = max(0.0, float(ljus["beta"]) / 0.05)
            sky.ozone_density = float(ljus.get("ozon", 350.0)) / 350.0
            tint = self._nod("ShaderNodeMix")
            tint.data_type = "RGBA"
            tint.blend_type = "MULTIPLY"
            tint.inputs[0].default_value = 1.0
            self.nt.links.new(sky.outputs["Color"], tint.inputs[6])
            tint.inputs[7].default_value = (1.0, 1.0, 1.0, 1.0)
            ut = tint.outputs[2]
            self.nt.links.new(ut, self.bg.inputs["Color"])
            self.bg.inputs["Strength"].default_value = 1.0
            # himlens färg och styrka som dagsljusets: mät panoramat och färga om det
            e_rgb = self.mat_horisontell()
            mal = (himmel_lux / LUMEN_PER_WATT) * hrgb
            k = mal / np.maximum(e_rgb, 1e-9)
            tint.inputs[7].default_value = (float(k[0]), float(k[1]), float(k[2]), 1.0)
            if moln > 0.0:
                ut = self._moln(ut, d, moln, hrgb)
                self.nt.links.new(ut, self.bg.inputs["Color"])
                e_rgb = self.mat_horisontell()
                self.bg.inputs["Strength"].default_value = float(himmel_lux / LUMEN_PER_WATT / (e_rgb @ REC709))
        sol = self.sol.data
        sol_lux = float(ljus["sol_lux"])
        self.sol.hide_render = sol_lux <= 0.0 or el <= 0.0
        sol.energy = sol_lux / LUMEN_PER_WATT
        sol.color = tuple(float(c) for c in np.array(ljus["sol_farg"]) / max(ljus["sol_farg"]))
        sol.energy *= max(ljus["sol_farg"])
        sol.angle = math.radians(max(float(ljus.get("sol_vinkel", SOLSKIVA)), 0.05))
        self.sol.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()

    def _moln(self, klar: bpy.types.NodeSocket, sol: Vector, tackning: float, farg: np.ndarray
              ) -> bpy.types.NodeSocket:
        """Moln: en brusig molnmask i ett plan över marken (perspektiv mot horisonten) som täcker andelen tackning av
        himlen; molnen är ljusgrå, ljusare i solens riktning (framåtspridning)."""
        tk = self._nod("ShaderNodeTexCoord").outputs["Generated"]
        sep = self._nod("ShaderNodeSeparateXYZ", Vector=tk)
        z = self._matte("MAXIMUM", sep.outputs["Z"], 0.02)
        plan = self._nod("ShaderNodeCombineXYZ", X=self._matte("DIVIDE", sep.outputs["X"], z),
                         Y=self._matte("DIVIDE", sep.outputs["Y"], z), Z=0.0)
        brus = self._nod("ShaderNodeTexNoise", Vector=plan.outputs[0], Scale=0.9, Detail=8.0, Roughness=0.62,
                         Distortion=0.25)
        tal = brus.outputs.get("Factor") or brus.outputs["Fac"]
        grans = 0.5 + 0.17 * (1 - 2 * tackning)
        mask = self._nod("ShaderNodeMapRange", Value=tal)
        mask.interpolation_type = "SMOOTHSTEP"
        mask.inputs[1].default_value = grans - 0.06
        mask.inputs[2].default_value = grans + 0.10
        # framåtspridning: ljusare moln nära solen
        prik = self._nod("ShaderNodeVectorMath")
        prik.operation = "DOT_PRODUCT"
        self.nt.links.new(tk, prik.inputs[0])
        prik.inputs[1].default_value = tuple(sol)
        fram = self._matte("ADD", 0.7, self._matte("MULTIPLY", self._matte("POWER", self._matte(
            "MAXIMUM", prik.outputs["Value"], 0.0), 8.0), 1.5))
        mork = self._matte("ADD", 0.75, self._matte("MULTIPLY", brus.outputs.get("Factor") or brus.outputs["Fac"], 0.5))
        moln = self._nod("ShaderNodeVectorMath")
        moln.operation = "SCALE"
        moln.inputs[0].default_value = tuple(float(c) * 0.012 for c in farg)
        self.nt.links.new(self._matte("MULTIPLY", fram, mork), moln.inputs[3])
        mix = self._nod("ShaderNodeMix")
        mix.data_type = "RGBA"
        self.nt.links.new(mask.outputs[0], mix.inputs[0])
        self.nt.links.new(klar, mix.inputs[6])
        self.nt.links.new(moln.outputs[0], mix.inputs[7])
        return mix.outputs[2]

    def mat_horisontell(self, bredd: int = 256) -> np.ndarray:
        """Himlens belysning på en horisontell yta (RGB, Blenders enheter) ur en panoramarendering av världen."""
        sc = bpy.data.scenes.get("Himmelsmätning") or bpy.data.scenes.new("Himmelsmätning")
        sc.world = self.sc.world
        kam = bpy.data.objects.get("Panorama") or bpy.data.objects.new("Panorama", bpy.data.cameras.new("Panorama"))
        if kam.name not in sc.collection.objects:
            sc.collection.objects.link(kam)
        kam.data.type = "PANO"
        kam.data.panorama_type = "EQUIRECTANGULAR"
        kam.rotation_euler = (math.pi / 2, 0.0, 0.0)
        sc.camera = kam
        sc.render.engine = "CYCLES"
        sc.cycles.samples = 2
        sc.cycles.use_denoising = False
        sc.cycles.use_adaptive_sampling = False
        sc.render.resolution_x, sc.render.resolution_y = bredd, bredd // 2
        sc.render.resolution_percentage = 100
        sc.render.image_settings.file_format = "OPEN_EXR"
        sc.render.image_settings.color_depth = "32"
        fil = os.path.join(tempfile.gettempdir(), "trebodar_himmel.exr")
        sc.render.filepath = fil
        bpy.ops.render.render(write_still=True, scene=sc.name)
        im = bpy.data.images.load(fil)
        w, h = im.size
        px = np.array(im.pixels[:], dtype=np.float64).reshape(h, w, 4)[::-1, :, :3]
        bpy.data.images.remove(im)
        lat = math.pi / 2 - (np.arange(h) + 0.5) / h * math.pi
        vikt = (2 * math.pi / w) * (math.pi / h) * np.cos(lat) * np.maximum(np.sin(lat), 0.0)
        return (px * vikt[:, None, None]).sum((0, 1))


# ------------------------------------------------------------------ marken, portaler och kamera

def portaler(lista: list[dict]) -> None:
    """Ljusportaler (Cycles samplar himlen genom dem): rektanglar i modellens koordinater (mm) med mitt, normal inåt,
    upp-riktning, bredd och höjd."""
    for i, p in enumerate(lista):
        namn = f"Portal {i + 1:02d}"
        lj = bpy.data.lights.get(namn) or bpy.data.lights.new(namn, "AREA")
        lj.shape = "RECTANGLE"
        lj.size, lj.size_y = p["bredd"] / 1000, p["hojd"] / 1000
        lj.cycles.is_portal = True
        ob = bpy.data.objects.get(namn) or bpy.data.objects.new(namn, lj)
        if ob.name not in bpy.context.scene.collection.objects:
            bpy.context.scene.collection.objects.link(ob)
        ob.location = Vector(p["mitt"]) / 1000
        # arealjuset lyser längs sitt −Z (portalens normal in i rummet), bredden längs X och höjden längs Y
        z = -Vector(p["normal"]).normalized()
        y = Vector(p["upp"]) - Vector(p["upp"]).dot(z) * z
        y.normalize()
        ob.rotation_euler = Matrix((y.cross(z), y, z)).transposed().to_euler()


def kamera(namn: str, vy: dict) -> bpy.types.Object:
    """Kameran: lodräta linjer lodräta (kameran vågrät, bilden flyttas upp eller ned med objektivförskjutning, som en
    arkitekturkamera), linsen i mm (36 mm sensor), eller som förut riktad mot målet (lodrat=False)."""
    k = bpy.data.objects.get(f"Kamera {namn}") or bpy.data.objects.new(f"Kamera {namn}",
                                                                        bpy.data.cameras.new(f"Kamera {namn}"))
    if k.name not in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.link(k)
    p = Vector(vy["kamera"]) / 1000
    m = Vector(vy["mal"]) / 1000
    k.location = p
    k.data.lens = float(vy.get("lins", 35.0))
    k.data.sensor_width = 36.0
    k.data.sensor_fit = "HORIZONTAL"
    k.data.clip_start = 0.02
    k.data.clip_end = 5000.0
    r = m - p
    if vy.get("lodrat", True) and abs(r.z) < r.length * 0.95:
        horisontell = Vector((r.x, r.y, 0.0))
        k.rotation_euler = horisontell.to_track_quat("-Z", "Y").to_euler()
        tanv = r.z / horisontell.length
        bild = bpy.context.scene.render
        k.data.shift_y = tanv * k.data.lens / k.data.sensor_width * (1.0 if bild.resolution_x >= bild.resolution_y
                                                                      else bild.resolution_y / bild.resolution_x)
        k.data.shift_x = 0.0
    else:
        k.rotation_euler = r.to_track_quat("-Z", "Y").to_euler()
        k.data.shift_y = 0.0
    return k


def exponering(sc: bpy.types.Scene, ev: float) -> None:
    sc.view_settings.exposure = 9.94 - ev


def auto_ev(sc: bpy.types.Scene, nyckel: float = 0.18, hogdagrar: float = 0.97, bredd: int = 320) -> float:
    """EV100 ur en snabb förhandsbild: geometriska medelvärdet av luminansen (utan de ljusaste procenten, t.ex.
    fönstren) blir nyckel efter exponeringen."""
    r = sc.render
    spara = (r.resolution_x, r.resolution_y, sc.cycles.samples, sc.cycles.use_adaptive_sampling, r.filepath,
             r.image_settings.file_format, r.image_settings.color_depth, sc.view_settings.exposure)
    skala = bredd / r.resolution_x
    r.resolution_x, r.resolution_y = bredd, max(2, round(r.resolution_y * skala))
    sc.cycles.samples = 24
    sc.cycles.use_adaptive_sampling = False
    r.image_settings.file_format = "OPEN_EXR"
    r.image_settings.color_depth = "32"
    sc.view_settings.exposure = 0.0
    fil = os.path.join(tempfile.gettempdir(), "trebodar_forhand.exr")
    r.filepath = fil
    bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(fil)
    w, h = im.size
    px = np.array(im.pixels[:], dtype=np.float64).reshape(h, w, 4)[:, :, :3]
    bpy.data.images.remove(im)
    (r.resolution_x, r.resolution_y, sc.cycles.samples, sc.cycles.use_adaptive_sampling, r.filepath,
     r.image_settings.file_format, r.image_settings.color_depth, sc.view_settings.exposure) = spara
    lum = np.maximum(px @ REC709, 1e-6).ravel()
    lum = lum[lum <= np.quantile(lum, hogdagrar)]
    medel = float(np.exp(np.mean(np.log(lum))))                     # Blenders enheter (· 683 = cd/m²)
    return 9.94 - math.log2(nyckel / medel)
