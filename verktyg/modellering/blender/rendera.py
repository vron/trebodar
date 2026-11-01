"""Blender (i bakgrunden): läs modellens GLB, sätt material efter materialnamn, ljus och kamera, rendera med Cycles.

    Blender -b --factory-startup -P rendera.py -- modell.glb vyer.json ut_mapp [--bredd 400] [--sampel 32]

vyer.json: {namn: {"kamera": [x, y, z], "mal": [x, y, z], "brannvidd": mm, "sol": [azimut, höjd], "inne": bool,
"dolj": [sökvägsdelar]}} i modellens mm (z upp). GLB-importen ger meter med z upp i Blender.
"""
import argparse
import json
import math
import sys

import bpy
from mathutils import Vector

a = argparse.ArgumentParser()
a.add_argument("glb")
a.add_argument("vyer")
a.add_argument("ut")
a.add_argument("--bredd", type=int, default=400)
a.add_argument("--sampel", type=int, default=32)
a.add_argument("--vy", action="append")
arg = a.parse_args(sys.argv[sys.argv.index("--") + 1:])
VYER = json.load(open(arg.vyer))

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=arg.glb)


def principled(mat):
    mat.use_nodes = True
    nt = mat.node_tree
    b = nt.nodes.get("Principled BSDF")
    if b is None:
        b = nt.nodes.new("ShaderNodeBsdfPrincipled")
        nt.links.new(b.outputs[0], nt.nodes["Material Output"].inputs[0])
    for n in list(nt.nodes):
        if n.type == "TEX_IMAGE":
            nt.nodes.remove(n)
    return nt, b


def satt(b, farg=None, grov=None, metall=None, alfa=None, transmission=None):
    if farg is not None:
        b.inputs["Base Color"].default_value = (*farg, 1.0)
    if grov is not None:
        b.inputs["Roughness"].default_value = grov
    if metall is not None:
        b.inputs["Metallic"].default_value = metall
    if alfa is not None:
        b.inputs["Alpha"].default_value = alfa
    if transmission is not None:
        for nyckel in ("Transmission Weight", "Transmission"):
            if nyckel in b.inputs:
                b.inputs[nyckel].default_value = transmission


def tra(mat, ljus, mork, skala=60.0, grov=0.65):
    """Proceduriella fibrer längs objektets lokala x (delarna har x längs fibrerna)."""
    nt, b = principled(mat)
    satt(b, grov=grov, metall=0.0)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (0.4, skala, skala)
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.wave_type = "RINGS"
    wave.rings_direction = "X"
    wave.inputs["Distortion"].default_value = 6.0
    wave.inputs["Detail"].default_value = 3.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*mork, 1)
    ramp.color_ramp.elements[1].color = (*ljus, 1)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], wave.inputs["Vector"])
    nt.links.new(wave.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])


def brus(mat, farg1, farg2, skala=0.6, grov=0.9):
    nt, b = principled(mat)
    satt(b, grov=grov, metall=0.0)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = skala
    n.inputs["Detail"].default_value = 8.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*farg1, 1)
    ramp.color_ramp.elements[1].color = (*farg2, 1)
    nt.links.new(tc.outputs["Generated"], n.inputs["Vector"])
    nt.links.new(n.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])


for mat in bpy.data.materials:
    n = mat.name.lower()
    if n.startswith(("c24", "distansregel", "dörrblad")):
        tra(mat, (0.78, 0.60, 0.38), (0.62, 0.45, 0.26))
    elif n.startswith(("gl30",)):
        tra(mat, (0.80, 0.62, 0.38), (0.66, 0.48, 0.28), 40)
    elif n.startswith("råspont"):
        tra(mat, (0.74, 0.58, 0.38), (0.58, 0.43, 0.26))
    elif n.startswith("panel"):
        tra(mat, (0.42, 0.30, 0.20), (0.30, 0.21, 0.14), 30, 0.7)
    elif n.startswith("hårdboard"):
        _, b = principled(mat); satt(b, (0.30, 0.20, 0.12), 0.6, 0.0)
    elif n.startswith(("takplåt",)):
        _, b = principled(mat); satt(b, (0.42, 0.45, 0.47), 0.35, 1.0)
    elif n.startswith(("s355", "s235", "spikplåt")):
        _, b = principled(mat); satt(b, (0.35, 0.36, 0.38), 0.45, 1.0)
    elif n.startswith("underlagspapp"):
        _, b = principled(mat); satt(b, (0.03, 0.03, 0.03), 0.9, 0.0)
    elif n.startswith(("gips", "utegips")):
        _, b = principled(mat); satt(b, (0.86, 0.85, 0.82), 0.9, 0.0)
    elif n.startswith("betong"):
        brus(mat, (0.45, 0.45, 0.44), (0.58, 0.58, 0.56), 2.0)
    elif n.startswith("cellplast"):
        _, b = principled(mat); satt(b, (0.92, 0.88, 0.86), 0.95, 0.0)
    elif n.startswith("granit"):
        brus(mat, (0.40, 0.38, 0.37), (0.66, 0.64, 0.62), 25.0, 0.8)
    elif n.startswith("berg"):
        brus(mat, (0.28, 0.27, 0.26), (0.45, 0.44, 0.42), 1.5)
    elif n.startswith("mark"):
        brus(mat, (0.12, 0.20, 0.07), (0.25, 0.33, 0.12), 3.0, 1.0)
    elif n.startswith("fyllning"):
        brus(mat, (0.35, 0.32, 0.28), (0.50, 0.47, 0.42), 8.0)
    elif n.startswith(("träfiber", "mineralull")):
        brus(mat, (0.62, 0.50, 0.30), (0.78, 0.66, 0.42), 20.0, 1.0)
    elif n.startswith("ångbroms"):
        _, b = principled(mat); satt(b, (0.55, 0.70, 0.80), 0.4, 0.0, alfa=0.5)
    elif n.startswith("glas"):
        _, b = principled(mat); satt(b, (0.85, 0.92, 0.95), 0.02, 0.0, transmission=1.0)
    elif n.startswith("karm"):
        _, b = principled(mat); satt(b, (0.10, 0.11, 0.12), 0.5, 0.0)

sc = bpy.context.scene
w = bpy.data.worlds.new("Himmel")
sc.world = w
w.use_nodes = True
sky = w.node_tree.nodes.new("ShaderNodeTexSky")
bg = w.node_tree.nodes["Background"]
w.node_tree.links.new(sky.outputs["Color"], bg.inputs["Color"])
sol = bpy.data.objects.new("Sol", bpy.data.lights.new("Sol", "SUN"))
sc.collection.objects.link(sol)
sol.data.angle = math.radians(0.6)
kam = bpy.data.objects.new("Kamera", bpy.data.cameras.new("Kamera"))
sc.collection.objects.link(kam)
sc.camera = kam
sc.render.engine = "CYCLES"
sc.cycles.samples = arg.sampel
sc.cycles.use_denoising = True
try:
    sc.cycles.device = "GPU"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "METAL"
    prefs.get_devices()
    for d in prefs.devices:
        d.use = True
except Exception:
    pass
sc.render.resolution_x = arg.bredd
sc.render.resolution_y = round(arg.bredd * 0.66)
sc.view_settings.view_transform = "AgX"

for namn, v in VYER.items():
    if arg.vy and namn not in arg.vy:
        continue
    for o in bpy.data.objects:
        if o.type == "MESH":
            sok = o.get("sokvag", "") or o.name
            o.hide_render = any(d in sok for d in v.get("dolj", []))
    az, el = v.get("sol", [230.0, 35.0])
    try:
        sky.sky_type = "NISHITA"
        sky.sun_elevation = math.radians(el)
        sky.sun_rotation = math.radians(az)
    except Exception:
        pass
    inne = v.get("inne", False)
    bg.inputs["Strength"].default_value = 0.6 if inne else 0.25
    sol.data.energy = 3.0
    sol.rotation_euler = (math.radians(90 - el), 0, math.radians(-az))
    sc.view_settings.exposure = 1.5 if inne else 0.0
    p = Vector([c / 1000 for c in v["kamera"]])
    m = Vector([c / 1000 for c in v["mal"]])
    kam.location = p
    kam.rotation_euler = (m - p).to_track_quat("-Z", "Y").to_euler()
    kam.data.lens = v.get("brannvidd", 35)
    kam.data.clip_start = 0.05
    kam.data.clip_end = 1000
    sc.render.filepath = f"{arg.ut}/{namn}.png"
    bpy.ops.render.render(write_still=True)
    print("RENDERAD", sc.render.filepath)
