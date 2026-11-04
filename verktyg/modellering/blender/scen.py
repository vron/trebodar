"""Scenen i Blender: himmel och sol efter dagsljuset (modellering/dagsljus.py), marken runt modellen, ljusportaler i
fönstren, kameror och exponering, och Cycles inställningar per kvalitet.

Enheter: Blenders scen i meter (modellens mm / 1000, z uppåt) och ljuset fotometriskt: solens styrka (W/m² i Blender)
är belysningen vinkelrätt mot solen i lux / 683, och himlen skalas så att dess belysning på en horisontell yta blir
dagsljusets diffusa belysning (mäts med en liten panoramarendering av himlen). Exponeringen i Blender är 9,94 − EV100
(ett grått kort, 18 %, med luminansen 12,5·2^EV/100 cd/m² blir 0,18), eller räknas fram ur en snabb förhandsbild.
"""
from __future__ import annotations

import json
import math
import os
import tempfile

import bmesh
import bpy
import numpy as np
import OpenImageIO as oiio
from mathutils import Matrix, Vector

LUMEN_PER_WATT = 683.0
# Cycles läser IES-filernas ljusstyrka [cd] som en faktor 0,0706 per cd på punktljusets P / 4π (kalibrerat: en
# likformig fil på 100 cd gav 7,06 · P / 4π rakt ned, och faktorn är linjär); med effekten 4π / (683 · 0,0706) W blir
# ljusstyrkan cd / 683, samma enheter som solen och himlen (lux / 683)
IES_EFFEKT = 4 * math.pi / (LUMEN_PER_WATT * 0.070576)
KALLA_BAKOM, KALLA_R = 20.0, 15.0     # armaturernas ljuskälla: så långt bakom linsen och dess radie [mm]
REC709 = np.array([0.2126, 0.7152, 0.0722])
SOLSKIVA = 0.53

# kvaliteter: upplösning (bredd; höjd 16:9), största antal sampel, brustrsöskel för adaptiv sampling, studsar
KVALITET = {
    "skiss": {"bredd": 640, "sampel": 48, "troskel": 0.05, "studsar": 6},
    "utkast": {"bredd": 1280, "sampel": 160, "troskel": 0.03, "studsar": 8},
    "normal": {"bredd": 1920, "sampel": 384, "troskel": 0.015, "studsar": 10},
    "slutlig": {"bredd": 2048, "sampel": 512, "troskel": 0.015, "studsar": 12},
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
            d.use = d.type != "CPU"          # bara grafikprocessorn: med processorn bredvid går det långsammare
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
    """Kamerans vitbalans i färgtemperatur; None stänger av den. Nyansen 10 är dagsljusets kurva (Blenders
    neutrala inställning, 6 500 K och 10, är D65); 0 vore Plancks kurva, och bilden blir då grönstickig."""
    vs = sc.view_settings
    vs.use_curve_mapping = False
    vs.use_white_balance = kelvin is not None
    if kelvin is not None:
        vs.white_balance_temperature = kelvin
        vs.white_balance_tint = 10.0


def dagsljusets_vitbalans(ljus: dict, grad: float = 0.7, mot: float = 5500.0, natt: float = 3300.0) -> float:
    """Vitbalansen ute [K]: dagsljusets färgtemperatur (solens och himlens, vägda efter belysningen på marken, i
    mired) till graden grad och resten mot `mot` (kamerans dagsljusinställning), så att kvällssolen förblir varm och
    mulet väder neutralt. I mörker (solen mer än 6° under horisonten) `natt`, varmare än månskenet (omkring 4 100 K),
    som ett nattfoto med glödljusinställning: det månbelysta landskapet och natthimlen blir blå och de tända fönstren
    varma."""
    if ljus["sol_hojd"] < -6.0:
        return natt
    es = ljus["sol_lux"] * max(0.0, math.sin(math.radians(ljus["sol_hojd"]))) if ljus.get("sol_cct") else 0.0
    eh = ljus["himmel_lux"] if ljus.get("himmel_cct") else 0.0
    if es + eh <= 0:
        return mot
    sol = es * 1e6 / ljus["sol_cct"] if es else 0.0
    himmel = eh * 1e6 / ljus["himmel_cct"] if eh else 0.0
    mired = grad * (sol + himmel) / (es + eh) + (1 - grad) * 1e6 / mot
    return min(8000.0, max(4000.0, 1e6 / mired))


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

    def stall_in(self, ljus: dict, hojd_m: float = 0.0, fil: str | None = None) -> None:
        """Himlen och solen efter dagsljuset (dagsljus.Ljus som dict); med en fotograferad himmel (fil, HDR) för det
        kameran ser (_fotohimmel)."""
        nyckel = repr(sorted((k, str(v)) for k, v in ljus.items())) + str(fil)
        if nyckel == self.nyckel:
            return
        self.nyckel = nyckel
        for n in list(self.nt.nodes):
            if n not in (self.ut, self.bg):
                self.nt.nodes.remove(n)
        # den beräknade himlen direkt till världen, så att mat_horisontell mäter den (inte en tom värld eller den
        # fotograferade himlen från förra vyn); _fotohimmel lägger sedan den fotograferade himlen emellan
        self.nt.links.new(self.bg.outputs["Background"], self.ut.inputs["Surface"])
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
        if fil and os.path.exists(fil):
            self._fotohimmel(fil, d, float(ljus["himmel_lux"]))

    _analyser: dict[str, dict] = {}

    @classmethod
    def _analys(cls, bild: bpy.types.Image) -> dict:
        """Den fotograferade himlens sol (riktningen i bilden), belysningen på en horisontell yta från himlen utom
        solen (Blenders enheter) och taket för det som visas (de ljusaste delarna utom solen)."""
        if bild.filepath in cls._analyser:
            return cls._analyser[bild.filepath]
        w, h = bild.size
        px = np.empty(w * h * 4, dtype=np.float32)
        bild.pixels.foreach_get(px)
        steg = max(1, w // 1024)
        px = px.reshape(h, w, 4)[::steg, ::steg, :3]
        lum = px @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
        hh, ww = lum.shape
        el = (np.arange(hh) + 0.5) / hh * math.pi - math.pi / 2               # rad 0 = nederst
        u = (np.arange(ww) + 0.5) / ww
        i, j = np.unravel_index(np.argmax(lum), lum.shape)
        sol_el, sol_alfa = float(el[i]), math.pi - 2 * math.pi * float(u[j])   # Cycles: u = (π − atan2(y, x)) / 2π
        E, A = np.meshgrid(el, math.pi - 2 * math.pi * u, indexing="ij")
        cosv = np.sin(E) * math.sin(sol_el) + np.cos(E) * math.cos(sol_el) * np.cos(A - sol_alfa)
        himmel = (E > 0) & (cosv < math.cos(math.radians(6.0)))
        d_omega = np.cos(E) * (math.pi / hh) * (2 * math.pi / ww)
        e = float(np.sum((lum * np.sin(E) * d_omega)[himmel]))
        tak = float(np.percentile(lum[himmel], 99.8))
        cls._analyser[bild.filepath] = {"alfa": sol_alfa, "e": e, "tak": tak}
        return cls._analyser[bild.filepath]

    def _fotohimmel(self, fil: str, sol: Vector, himmel_lux: float) -> None:
        """Den fotograferade himlen (Poly Haven, utan mark) för kamerans strålar och reflexer och det som syns genom
        glas (inga diffusa studsar före, inte ljusets strålar mot himlen): vriden så att dess sol står i solens
        azimut, med samma belysning från himlen som dagsljuset och solskivan avkapad (solen är sollampan). Ljuset
        i scenen kommer från den beräknade himlen."""
        bild = bpy.data.images.load(fil, check_existing=True)
        a = self._analys(bild)
        k = (himmel_lux / LUMEN_PER_WATT) / max(a["e"], 1e-9)
        tex = self._nod("ShaderNodeTexEnvironment",
                        Vector=self._nod("ShaderNodeMapping", Vector=self._nod("ShaderNodeTexCoord").outputs["Generated"],
                                         Rotation=(0.0, 0.0, a["alfa"] - math.atan2(sol.y, sol.x))).outputs[0])
        tex.image = bild
        skala = self._nod("ShaderNodeVectorMath", Vector=tex.outputs["Color"])
        skala.operation = "SCALE"
        skala.inputs[3].default_value = k
        tak = self._nod("ShaderNodeVectorMath", Vector=skala.outputs[0])
        tak.operation = "MINIMUM"
        tak.inputs[1].default_value = (a["tak"] * k,) * 3
        lp = self._nod("ShaderNodeLightPath")
        # solskivan avkapad bara i reflexerna (där sollampan redan ger högdagern), hel för kameran och genom glas
        val = self._nod("ShaderNodeMix", Factor=lp.outputs["Is Glossy Ray"])
        val.data_type = "RGBA"
        self.nt.links.new(skala.outputs[0], val.inputs[6])
        self.nt.links.new(tak.outputs[0], val.inputs[7])
        foto = self._nod("ShaderNodeBackground", Color=val.outputs[2], Strength=1.0)
        utan_studs = self._matte("LESS_THAN", lp.outputs["Diffuse Depth"], 0.5)
        f = self._matte("MULTIPLY", self._matte("MULTIPLY", utan_studs, self._matte("SUBTRACT", 1.0,
                        lp.outputs["Is Shadow Ray"])), self._matte("SUBTRACT", 1.0, lp.outputs["Is Diffuse Ray"]))
        mix = self._nod("ShaderNodeMixShader", Fac=f)
        self.nt.links.new(self.bg.outputs["Background"], mix.inputs[1])
        self.nt.links.new(foto.outputs["Background"], mix.inputs[2])
        self.nt.links.new(mix.outputs[0], self.ut.inputs["Surface"])

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


def lampor(grupper: dict[str, dict]) -> dict[str, list[bpy.types.Object]]:
    """Taklampor per grupp (modellens mm): fyrkantiga arealjus som lyser nedåt, med ljusflödet (lm / 683 som solen och
    himlen) och färgen; släckta tills en vy tänder sin grupp."""
    ut: dict[str, list[bpy.types.Object]] = {}
    for grupp, g in grupper.items():
        ut[grupp] = []
        for i, (x, y) in enumerate(g["lagen"]):
            namn = f"Lampa {grupp} {i + 1:02d}"
            lj = bpy.data.lights.new(namn, "AREA")
            lj.shape = "SQUARE"
            lj.size = g["sida"] / 1000
            lj.energy = g["lumen"] / LUMEN_PER_WATT
            lj.color = tuple(g["farg"])
            ob = bpy.data.objects.new(namn, lj)
            bpy.context.scene.collection.objects.link(ob)
            ob.location = (x / 1000, y / 1000, g["z"] / 1000)          # arealjuset lyser längs −Z, nedåt
            ob.hide_render = True
            ut[grupp].append(ob)
    return ut


class Armatur:
    """En armatur i scenen: punktljuset med armaturens ljusfördelning (IES) och färg, inne i armaturen bakom linsen
    (frontringen och huset skärmar av snett ljus, som i armaturen; linsen och spoten kastar inga skuggor), och linsens
    objekt, som lyser för kameran när armaturen är tänd (materialtypen lins). Pendlarna: ljuset i ljuskällans mitt
    ("kalla", med lampans radie), skärmarna skuggar och reflekterar, och glasets luminans kommer med ("luminans")."""

    def __init__(self, a: dict, ies: bpy.types.Text, linser: list[bpy.types.Object]):
        self.tand = a["tand"]
        lj = bpy.data.lights.new(a["id"], "POINT")
        lj.shadow_soft_size = (a["kalla_d"] / 2 if "kalla" in a else min(a["lysande_d"] / 2, KALLA_R)) / 1000
        lj.color = tuple(a["farg"])
        lj.use_nodes = True
        nt = lj.node_tree
        n = nt.nodes.new("ShaderNodeTexIES")
        n.mode = "INTERNAL"
        n.ies = ies
        nt.links.new(n.outputs["Fac"], nt.nodes["Emission"].inputs["Strength"])
        self.ljus = bpy.data.objects.new(a["id"], lj)
        bpy.context.scene.collection.objects.link(self.ljus)
        r = Vector(a["riktning"]).normalized()
        self.ljus.location = (Vector(a["kalla"]) if "kalla" in a else Vector(a["lins"]) - KALLA_BAKOM * r) / 1000
        self.ljus.rotation_euler = (-r).to_track_quat("Z", "Y").to_euler()      # ljusets −Z längs riktningen
        self.ljus.hide_render = True
        # linsens luminans rakt fram (största ljusstyrkan genom linsens yta), pendlarnas glas ur flödet genom det, i
        # Blenders enheter
        self.luminans = a.get("luminans", a["max_cd"] / (math.pi * (a["lysande_d"] / 2000) ** 2)) / LUMEN_PER_WATT
        self.linser = linser
        self.farg = tuple(a["farg"])
        for o in linser:
            o.visible_shadow = False
        self.tand_till(0.0)

    def tand_till(self, niva: float) -> None:
        """Tänd (niva 0–1, dimrad) eller släck."""
        self.ljus.hide_render = niva <= 0
        self.ljus.data.energy = IES_EFFEKT * niva
        for o in self.linser:
            o["lysande"] = self.luminans * niva
            o["lysande_farg"] = self.farg


def armaturer(lista: list[dict]) -> list[Armatur]:
    """Armaturerna ur scenens beskrivning; en IES-text per armaturtyp, linserna efter delarnas namn (<id>-LINS).
    Hålen i taket för de infällda armaturerna finns i modellen (el.installation.haltagningar)."""
    texter: dict[str, bpy.types.Text] = {}
    ut = []
    for a in lista:
        if a["typ"] not in texter:
            texter[a["typ"]] = bpy.data.texts.new(f"{a['typ']}.ies")
            texter[a["typ"]].from_string(a["ies"])
        namn = f"{a['id']}-LINS"
        linser = [o for o in bpy.data.objects if o.type == "MESH" and
                  (o.name.split(".")[0] == namn or str(o.get("sokvag", "")).endswith("/" + namn))]
        skugglosa = [o for o in bpy.data.objects if o.type == "MESH" and
                     o.name.split(".")[0] in (f"{a['id']}-SPOT", f"{a['id']}-BAFFEL")]
        for o in skugglosa:
            o.visible_shadow = False
        ut.append(Armatur(a, texter[a["typ"]], linser))
    return ut


def matyta(sc: bpy.types.Scene, m: dict, ut: str) -> None:
    """Belysningsstyrkan på en vågrät mätyta (m: omrade (x0, x1, y0, y1) och z i mm, cell i mm, direkt): ett vitt,
    perfekt diffust plan (Lambert) som bara kameran ser (det kastar inga skuggor och reflekterar inget ljus till
    scenen), ovanifrån med en ortografisk kamera, en pixel per ruta. Planets luminans är E / π, och ljuset är
    kalibrerat i lux / 683, så E = π · 683 · L lux. Allt annat är osynligt för kameran men lyser, skuggar och
    reflekterar som vanligt. Rutnätet (lux, rad 0 vid y0) sparas som <ut>.npy och beskrivningen som <ut>.json."""
    x0, x1, y0, y1 = (v / 1000 for v in m["omrade"])
    z = m["z"] / 1000
    nx, ny = max(2, round((x1 - x0) * 1000 / m["cell"])), max(2, round((y1 - y0) * 1000 / m["cell"]))
    me = bpy.data.meshes.new("Mätyta")
    bm = bmesh.new()
    for p in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        bm.verts.new((p[0], p[1], z))
    bm.faces.new(bm.verts)
    bm.to_mesh(me)
    bm.free()
    mat = bpy.data.materials.new("Mätyta")
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    diffus = nt.nodes.new("ShaderNodeBsdfDiffuse")
    diffus.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    diffus.inputs["Roughness"].default_value = 0.0
    nt.links.new(diffus.outputs[0], nt.nodes.new("ShaderNodeOutputMaterial").inputs["Surface"])
    me.materials.append(mat)
    plan = bpy.data.objects.new("Mätyta", me)
    sc.collection.objects.link(plan)
    for attr in ("visible_diffuse", "visible_glossy", "visible_transmission", "visible_volume_scatter",
                 "visible_shadow"):
        setattr(plan, attr, False)
    synliga = [o for o in bpy.data.objects if o is not plan and o.visible_camera]
    for o in synliga:
        o.visible_camera = False
    kam = bpy.data.objects.new("Mätkamera", bpy.data.cameras.new("Mätkamera"))
    sc.collection.objects.link(kam)
    kam.location = ((x0 + x1) / 2, (y0 + y1) / 2, z + 20.0)
    kam.rotation_euler = (0.0, 0.0, 0.0)
    kam.data.type = "ORTHO"
    kam.data.ortho_scale = max(x1 - x0, y1 - y0)
    kam.data.clip_end = 100.0
    r = sc.render
    spara = (sc.camera, r.resolution_x, r.resolution_y, r.filepath, r.image_settings.file_format,
             r.image_settings.color_depth, sc.cycles.max_bounces)
    sc.camera = kam
    r.resolution_x, r.resolution_y = nx, ny
    r.image_settings.file_format = "OPEN_EXR"
    r.image_settings.color_depth = "32"
    if m.get("direkt"):
        sc.cycles.max_bounces = 0
    r.filepath = ut + ".exr"
    bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(r.filepath)
    px = np.array(im.pixels[:], dtype=np.float64).reshape(ny, nx, 4)[:, :, :3]
    bpy.data.images.remove(im)
    lux = (px @ REC709) * math.pi * LUMEN_PER_WATT
    np.save(ut + ".npy", lux.astype(np.float32))
    with open(ut + ".json", "w", encoding="utf-8") as f:
        json.dump({**m, "nx": nx, "ny": ny}, f, ensure_ascii=False)
    (sc.camera, r.resolution_x, r.resolution_y, r.filepath, r.image_settings.file_format,
     r.image_settings.color_depth, sc.cycles.max_bounces) = spara
    for o in synliga:
        o.visible_camera = True
    bpy.data.objects.remove(plan)
    bpy.data.objects.remove(kam)


# ------------------------------------------------------------------ natthimlen

NATT_AVSTAND = 4000.0           # stjärnorna och månen så långt från kameran [m] (innanför kamerans clip_end)
STJARNA_VINKEL = 0.06           # stjärnornas skenbara storlek [°] (ett par bildpunkter)
STJARNA_LUM = 30.0              # en stjärna med magnituden 0 [cd/m²]: synlig i ett nattfoto exponerat för fönstren
MANE_DIAMETER = 0.518           # månens skenbara diameter [°]
MANE_LUM = 25.0                 # fullmånens yta [cd/m²] för kartans medelvärde: ljusare än fönstren, inte utbränd


def _stjarnfarg(bv: float) -> tuple[float, float, float]:
    """Stjärnans färg ur färgindex B−V (Ballesteros 2012: temperaturen; Planck som linjär Rec. 709, luminansen 1,
    ungefärligt)."""
    t = 4600.0 * (1 / (0.92 * bv + 1.7) + 1 / (0.92 * bv + 0.62))
    rgb = []
    for lam in (0.61, 0.55, 0.465):                                    # µm, ungefär R, G och B
        rgb.append(1 / (lam ** 5 * (math.exp(14388.0 / (lam * t)) - 1)))
    r, g, b = rgb
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return (r / y, g / y, b / y)


class Natthimmel:
    """Stjärnorna (små lysande rutor, bara för kamerans och reflexernas strålar), månen (en klot med NASA:s karta,
    upplyst från solens riktning) och månens ljus, runt kameran efter natthimlen (modellering/natthimmel.natt)."""

    def __init__(self, sc: bpy.types.Scene):
        self.sc = sc
        self.stj: bpy.types.Object | None = None
        self.mane: bpy.types.Object | None = None
        self.mane_sol: bpy.types.Node | None = None
        lampa = bpy.data.lights.new("Månljus", "SUN")
        self.ljus = bpy.data.objects.new("Månljus", lampa)
        sc.collection.objects.link(self.ljus)
        self.ljus.hide_render = True

    def _synlighet(self, ob: bpy.types.Object) -> None:
        ob.visible_diffuse = ob.visible_shadow = ob.visible_volume_scatter = False
        ob.visible_camera = ob.visible_glossy = ob.visible_transmission = True

    def _stjarnor(self, natt: dict, kamera: Vector) -> None:
        if self.stj is not None:
            me_gammal = self.stj.data
            bpy.data.objects.remove(self.stj)
            bpy.data.meshes.remove(me_gammal)
        s = NATT_AVSTAND * math.tan(math.radians(STJARNA_VINKEL)) / 2
        V, F, C = [], [], []
        for x, y, z, mag, bv in natt["stjarnor"]:
            d = Vector((x, y, z)).normalized()
            c = kamera + d * NATT_AVSTAND
            u = d.orthogonal().normalized() * s
            v = d.cross(u).normalized() * s
            n = len(V)
            V += [c - u - v, c + u - v, c + u + v, c - u + v]
            F.append((n, n + 1, n + 2, n + 3))
            k = 10 ** (-0.4 * mag) * natt["styrka"]
            C += [tuple(k * f for f in _stjarnfarg(bv)) + (1.0,)] * 4
        me = bpy.data.meshes.new("Stjärnor")
        me.from_pydata([tuple(p) for p in V], [], F)
        attr = me.color_attributes.new("farg", "FLOAT_COLOR", "CORNER")
        attr.data.foreach_set("color", np.array(C, dtype=np.float32).ravel())
        mat = bpy.data.materials.get("Stjärnor")
        if mat is None:
            mat = bpy.data.materials.new("Stjärnor")
            mat.use_nodes = True
            nt = mat.node_tree
            nt.nodes.clear()
            ut = nt.nodes.new("ShaderNodeOutputMaterial")
            em = nt.nodes.new("ShaderNodeEmission")
            at = nt.nodes.new("ShaderNodeAttribute")
            at.attribute_name = "farg"
            em.inputs["Strength"].default_value = STJARNA_LUM / LUMEN_PER_WATT
            nt.links.new(at.outputs["Color"], em.inputs["Color"])
            nt.links.new(em.outputs[0], ut.inputs["Surface"])
        me.materials.append(mat)
        self.stj = bpy.data.objects.new("Stjärnor", me)
        self.sc.collection.objects.link(self.stj)
        self._synlighet(self.stj)

    def _manen(self, karta: str | None) -> bpy.types.Object:
        if self.mane is not None:
            return self.mane
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=64, v_segments=32,
                                  radius=NATT_AVSTAND * math.tan(math.radians(MANE_DIAMETER / 2)))
        for f in bm.faces:
            f.smooth = True
        me = bpy.data.meshes.new("Månen")
        bm.to_mesh(me)
        bm.free()
        mat = bpy.data.materials.new("Månen")
        mat.use_nodes = True
        nt = mat.node_tree
        nt.nodes.clear()

        def nod(typ: str, **ing: object) -> bpy.types.Node:
            n = nt.nodes.new(typ)
            for k_, v_ in ing.items():
                if isinstance(v_, bpy.types.NodeSocket):
                    nt.links.new(v_, n.inputs[k_])
                else:
                    n.inputs[k_].default_value = v_
            return n

        def matte(op: str, a_: object, b_: object = 0.0) -> bpy.types.NodeSocket:
            n = nod("ShaderNodeMath")
            n.operation = op
            for i, v_ in enumerate((a_, b_)):
                if isinstance(v_, bpy.types.NodeSocket):
                    nt.links.new(v_, n.inputs[i])
                else:
                    n.inputs[i].default_value = v_
            return n.outputs[0]
        # kartan (longitud 0 mitt i bilden, öster åt höger) på klotet: objektets −y mot kameran och z uppåt
        p = nod("ShaderNodeSeparateXYZ", Vector=nod("ShaderNodeTexCoord").outputs["Object"])
        lon = matte("ARCTAN2", p.outputs["X"], matte("MULTIPLY", p.outputs["Y"], -1.0))
        lat = matte("ARCTAN2", p.outputs["Z"],
                    matte("SQRT", matte("ADD", matte("MULTIPLY", p.outputs["X"], p.outputs["X"]),
                                        matte("MULTIPLY", p.outputs["Y"], p.outputs["Y"]))))
        uv = nod("ShaderNodeCombineXYZ", X=matte("ADD", matte("DIVIDE", lon, 2 * math.pi), 0.5),
                 Y=matte("ADD", matte("DIVIDE", lat, math.pi), 0.5))
        farg: object = (0.12, 0.12, 0.12, 1.0)
        medel = 0.12
        if karta and os.path.exists(karta):
            bild = bpy.data.images.load(karta, check_existing=True)
            bild.colorspace_settings.name = "sRGB"
            px = np.array(bild.pixels[:], dtype=np.float32).reshape(-1, 4)[::97, :3]
            medel = float(np.mean(px @ np.array([0.2126, 0.7152, 0.0722])))
            tex = nod("ShaderNodeTexImage", Vector=uv.outputs[0])
            tex.image = bild
            tex.interpolation = "Cubic"
            farg = tex.outputs["Color"]
        # fasen: ytan upplyst från solens riktning
        self.mane_sol = nod("ShaderNodeCombineXYZ")
        geo = nod("ShaderNodeNewGeometry")
        dot = nod("ShaderNodeVectorMath", Vector=geo.outputs["Normal"])
        dot.operation = "DOT_PRODUCT"
        nt.links.new(self.mane_sol.outputs[0], dot.inputs[1])
        ljus = matte("MAXIMUM", dot.outputs["Value"], 0.0)
        em = nod("ShaderNodeEmission", Color=farg,
                 Strength=matte("MULTIPLY", ljus, MANE_LUM / LUMEN_PER_WATT / max(medel, 1e-3)))
        nt.links.new(em.outputs[0], nod("ShaderNodeOutputMaterial").inputs["Surface"])
        me.materials.append(mat)
        self.mane = bpy.data.objects.new("Månen", me)
        self.sc.collection.objects.link(self.mane)
        self._synlighet(self.mane)
        return self.mane

    def stall_in(self, natt: dict | None, kamera: Vector | None) -> None:
        """Natthimlen runt kameran (m), eller ingen."""
        m = natt.get("mane") if natt else None
        if self.stj is not None:
            self.stj.hide_render = natt is None or kamera is None
        if self.mane is not None:
            self.mane.hide_render = m is None or kamera is None
        self.ljus.hide_render = m is None or m["lux"] <= 0.0
        if natt is None or kamera is None:
            return
        self._stjarnor(natt, kamera)
        if m is None:
            return
        d = Vector(m["riktning"]).normalized()
        ob = self._manen(natt.get("kartan"))
        ob.location = kamera + d * NATT_AVSTAND
        ob.rotation_euler = (-d).to_track_quat("-Y", "Z").to_euler()
        sol = Vector(natt["sol"]).normalized()
        assert self.mane_sol is not None
        for i, k_ in enumerate("XYZ"):
            self.mane_sol.inputs[k_].default_value = sol[i]
        lampa = self.ljus.data
        lampa.energy = m["lux"] / LUMEN_PER_WATT
        lampa.color = (1.0, 0.93, 0.85)
        lampa.angle = math.radians(MANE_DIAMETER)
        self.ljus.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()


def manhimlen(ljus: dict, mane: dict) -> dict:
    """Dagsljuset (dagsljus.Ljus som dict) för Himmel.stall_in i månsken: den klara himlen med månen i solens ställe,
    med månhimlens belysning och färg (modellering/natthimmel), utan sol (månljuset är Natthimmel:s lampa)."""
    return {**ljus, "riktning": mane["riktning"], "sol_lux": 0.0, "himmel_lux": mane["himmel_lux"],
            "himmel_farg": mane["himmel_farg"]}


# Nattbilderna ute: rummen bakom de tända fönstren är omkring 10 steg ljusare än det månbelysta landskapet, så att
# fönstren och ljuset från dem på marken blir vita vid nattexponeringen. Som när man blandar exponeringar av ett
# nattfoto dämpas därför de ljusa partierna efter sin omgivning (en lokal tonkurva): luminansen relativt mellangrått
# (scenens linjära värden före vytransformen, kamerans exponering inräknad) i steg (log2), utjämnad med en bilateral
# oskärpa som stannar vid kanterna (fönstrens karmar), och över NATT_KNA steg tas bara NATT_LUTNING av stegen med.
# Detaljerna inom ett fönster behåller sin kontrast; landskapet, himlen och fasaderna i månsken ändras inte.
NATT_KNA = 1.0                  # steg över mellangrått där dämpningen börjar
NATT_LUTNING = 0.25             # den andel av stegen över knät som behålls
NATT_RADIE = 0.02               # utjämningens radie, andel av bildens bredd
NATT_TROSKEL = 1.5              # utjämningen stannar vid språng större än så här många steg
# I mörker sänks brusgränsen så mycket (brusgrans) att varje bildpunkt samplas till kvalitetens största antal: ljuset
# på marken och fasaderna kommer genom fönstren från lampor inne, så nattbilderna ute får så många gånger fler sampel
NATT_SAMPEL = 4
# och varje sampel får bidra med högst NATT_KLAMP steg över mellangrått, direkt och indirekt (klamp): lamporna inne är
# små och mycket ljusa (upp till 330 000 cd/m²), och genom fönstren glittrar de som enstaka ljusa bildpunkter i
# fasadernas, bergets och stenarnas reflexer, och de sällsynta studsarna in genom fönstren till de upplysta väggarna
# blir ljusa prickar i gräset; rummen bakom fönstren (omkring 10 steg) och månen (omkring 9,5) klampas inte
NATT_KLAMP = (11.0, 8.0)


def klamp(sc: bpy.types.Scene, steg: tuple[float, float] | None) -> None:
    """Största bidraget från ett sampel, (direkt, indirekt) steg över mellangrått vid exponeringen, eller inget.
    Efter exponering()."""
    c = sc.cycles
    m = 0.18 / 2 ** sc.view_settings.exposure
    c.sample_clamp_direct, c.sample_clamp_indirect = (0.0, 0.0) if steg is None else (m * 2 ** steg[0], m * 2 ** steg[1])


def nattkompression(sc: bpy.types.Scene, aktiv: bool) -> None:
    """Den lokala tonkurvan för nattbilderna ute (se ovan) i kompositören, eller ingen. Efter exponering()."""
    if not aktiv:
        sc.render.use_compositing = False
        return
    ng = bpy.data.node_groups.get("Nattkompression")
    if ng is None:
        ng = bpy.data.node_groups.new("Nattkompression", "CompositorNodeTree")
        ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
        n = ng.nodes

        def matte(op: str, a: object, b: object = 0.0, namn: str = "") -> bpy.types.NodeSocket:
            m = n.new("ShaderNodeMath")
            m.operation = op
            if namn:
                m.name = namn
            for i, v in enumerate((a, b)):
                if isinstance(v, bpy.types.NodeSocket):
                    ng.links.new(v, m.inputs[i])
                else:
                    m.inputs[i].default_value = v
            return m.outputs[0]
        bild = n.new("CompositorNodeRLayers").outputs["Image"]
        lum = n.new("CompositorNodeRGBToBW")
        ng.links.new(bild, lum.inputs[0])
        steg = matte("LOGARITHM", matte("MAXIMUM", matte("DIVIDE", lum.outputs[0], 1.0, "Mellangrått"), 1e-4), 2.0)
        jamn = n.new("CompositorNodeBilateralblur")
        jamn.name = "Utjämning"
        ng.links.new(steg, jamn.inputs["Image"])
        ng.links.new(steg, jamn.inputs["Determinator"])
        jamn.inputs["Threshold"].default_value = NATT_TROSKEL
        over = matte("MAXIMUM", matte("SUBTRACT", jamn.outputs[0], NATT_KNA), 0.0)
        forst = matte("POWER", 2.0, matte("MULTIPLY", over, -(1.0 - NATT_LUTNING)))
        mix = n.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs[0].default_value = 1.0
        ng.links.new(bild, mix.inputs[6])
        ng.links.new(forst, mix.inputs[7])
        ng.links.new(mix.outputs[2], n.new("NodeGroupOutput").inputs[0])
    ng.nodes["Mellangrått"].inputs[1].default_value = 0.18 / 2 ** sc.view_settings.exposure
    r = sc.render
    ng.nodes["Utjämning"].inputs["Size"].default_value = round(NATT_RADIE * r.resolution_x * r.resolution_percentage
                                                               / 100)
    sc.compositing_node_group = ng
    r.use_compositing = True


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


EV_TROSKEL = 7.0                # kvaliteternas brusgräns (troskel) gäller ned till inomhusbildernas exponering


def brusgrans(sc: bpy.types.Scene, troskel: float, ev: float) -> None:
    """Den adaptiva samplingens gräns efter exponeringen. Cycles jämför bruset med roten ur pixelns värde före
    exponeringen, så en mörk scen som exponeras upp (natten) skulle sluta sampla långt innan bruset blir lika litet
    i bilden; under EV_TROSKEL sänks gränsen med roten ur förstärkningen."""
    sc.cycles.adaptive_threshold = troskel * min(1.0, 2.0 ** ((ev - EV_TROSKEL) / 2))


def _exr_delar(fil: str) -> dict[str, np.ndarray]:
    """En flerlagers-EXR (Blender skriver varje pass som en egen del): passens RGB, pixlarna som rader."""
    inp = oiio.ImageInput.open(fil)
    ut: dict[str, np.ndarray] = {}
    i = 0
    while inp.seek_subimage(i, 0):
        spec = inp.spec()
        if spec.nchannels >= 3:
            namn = spec.channelnames[0].split(".")[-2]                 # "ViewLayer.Diffuse Direct.R"
            ut[namn] = np.asarray(inp.read_image(i, 0, 0, 3, "float"), dtype=np.float64).reshape(-1, 3)
        i += 1
    inp.close()
    return ut


def forhandsbild(sc: bpy.types.Scene, bredd: int = 320) -> dict[str, np.ndarray]:
    """En snabb förhandsbild för exponeringen och vitbalansen (linjär RGB, pixlarna som rader): bilden ("bild") och
    ljuset som når ytorna ("ljus": det direkta och indirekta diffusa ljuset, utan ytornas egen färg)."""
    r = sc.render
    vl = bpy.context.view_layer
    spara = (r.resolution_x, r.resolution_y, sc.cycles.samples, sc.cycles.use_adaptive_sampling, r.filepath,
             r.image_settings.file_format, r.image_settings.color_depth, sc.view_settings.exposure,
             vl.use_pass_diffuse_direct, vl.use_pass_diffuse_indirect)
    skala = bredd / r.resolution_x
    r.resolution_x, r.resolution_y = bredd, max(2, round(r.resolution_y * skala))
    sc.cycles.samples = 24
    sc.cycles.use_adaptive_sampling = False
    vl.use_pass_diffuse_direct = vl.use_pass_diffuse_indirect = True
    r.image_settings.media_type = "MULTI_LAYER_IMAGE"
    r.image_settings.file_format = "OPEN_EXR_MULTILAYER"
    r.image_settings.color_depth = "32"
    sc.view_settings.exposure = 0.0
    fil = os.path.join(tempfile.gettempdir(), "trebodar_forhand.exr")
    r.filepath = fil
    bpy.ops.render.render(write_still=True)
    delar = _exr_delar(fil)
    r.image_settings.media_type = "IMAGE"
    (r.resolution_x, r.resolution_y, sc.cycles.samples, sc.cycles.use_adaptive_sampling, r.filepath,
     r.image_settings.file_format, r.image_settings.color_depth, sc.view_settings.exposure,
     vl.use_pass_diffuse_direct, vl.use_pass_diffuse_indirect) = spara
    return {"bild": delar["Combined"], "ljus": delar["Diffuse Direct"] + delar["Diffuse Indirect"]}


def _urval(px: np.ndarray, hogdagrar: float) -> tuple[np.ndarray, np.ndarray]:
    lum = np.maximum(px @ REC709, 1e-6)
    valda = lum <= np.quantile(lum, hogdagrar)
    return px[valda], lum[valda]


INNE_LJUSARE = 0.5              # inomhusbilderna så mycket ljusare [EV] än medelvärdet ger: rummen ljusa som ögat ser dem
NATT_EV = -2.0                  # ute i mörker (solen mer än 6° under horisonten) högst så lång exponering, som ett
                                # nattfoto i månsken: huset och omgivningen syns, mörkare än på dagen, och de tända
                                # fönstren lyser


def auto_ev(px: dict[str, np.ndarray], nyckel: float = 0.18, hogdagrar: float = 0.97) -> float:
    """EV100 ur förhandsbilden: geometriska medelvärdet av luminansen (utan de ljusaste procenten, t.ex. fönstren)
    blir nyckel efter exponeringen."""
    _, lum = _urval(px["bild"], hogdagrar)
    medel = float(np.exp(np.mean(np.log(lum))))                     # Blenders enheter (· 683 = cd/m²)
    return 9.94 - math.log2(nyckel / medel)


RGB_XYZ = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])


def fargtemperatur(rgb: np.ndarray) -> float:
    """Ljusets ungefärliga färgtemperatur (McCamy) ur linjär Rec. 709."""
    X, Y, Z = RGB_XYZ @ rgb
    x, y = X / (X + Y + Z), Y / (X + Y + Z)
    n = (x - 0.3320) / (0.1858 - y)
    return float(449 * n ** 3 + 3525 * n ** 2 + 6823.3 * n + 5520.33)


def anpassning(la: float, cct: float) -> float:
    """Graden av kromatisk adaptation (0 ingen, 1 hel): CIECAM02 för normal omgivning (F = 1) ur
    adaptationsluminansen la [cd/m²], minskad för varmt ljus, där ögat anpassar sig ofullständigt (faktorn 1 vid
    5 000 K och däröver, 0,75 vid 2 700 K, linjärt i mired)."""
    d = 1.0 - math.exp((-la - 42.0) / 92.0) / 3.6
    mired = 1e6 / max(cct, 1000.0)
    return d * min(1.0, max(0.6, 1.0 - (mired - 200.0) * 0.25 / 170.0))


def auto_vitbalans(sc: bpy.types.Scene, px: dict[str, np.ndarray], hogdagrar: float = 0.97
                   ) -> tuple[float, float, float]:
    """Vitbalansen som ögats anpassning till ljuset i rummet: ljuset som når ytorna (förhandsbildens diffusa ljus,
    utan ytornas egen färg men med färgen från det som ljuset studsat på) är det som ögat anpassar sig till, till
    graden ur anpassning(): ljust och neutralt ljus nästan helt, svagt och varmt ljus till en del, så att lampljus
    förblir varmt. Anpassningen (von Kries) görs med vykurvornas vitnivå, en faktor per kanal i scenens linjära
    färger före vytransformen, med samma luminans. Returnerar (ljusets färgtemperatur, adaptationsluminansen
    [cd/m²], graden)."""
    _, lum = _urval(px["bild"], hogdagrar)
    la = float(lum.mean()) * LUMEN_PER_WATT
    ljus = px["ljus"]
    giltiga = ljus @ REC709 > 1e-9
    c = ljus[giltiga].mean(axis=0) if giltiga.any() else _urval(px["bild"], hogdagrar)[0].mean(axis=0)
    w = c / float(c @ REC709)
    cct = fargtemperatur(w)
    d = anpassning(la, cct)
    forst = d / w + (1.0 - d)                                         # förstärkning per kanal
    forst /= float((w * forst) @ REC709)
    vs = sc.view_settings
    vs.use_white_balance = False
    vs.use_curve_mapping = True
    vs.curve_mapping.white_level = tuple(float(1.0 / v) for v in forst)
    vs.curve_mapping.update()
    return cct, la, d
