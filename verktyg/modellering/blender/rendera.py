"""Blender (i bakgrunden): läs modellens GLB, bygg de procedurella materialen (material.py) efter modellens
material, sätt himmel, sol och en kamera per vy, rendera med Cycles och spara eventuellt scenen.

    Blender -b --factory-startup -P rendera.py -- modell.glb material.json vyer.json ut_mapp
        [--bredd 400] [--sampel 32] [--vy NAMN ...] [--blend scen.blend]

material.json: {materialnamn: {"typ": ..., "farg": "#rrggbb", parametrar ...}} (från modellens material).
vyer.json: {namn: {"kamera": [x, y, z], "mal": [x, y, z], "brannvidd": mm, "sol": [azimut, höjd], "inne": bool,
"molnigt": bool, "dolj": [delar av sökvägar]}} i modellens mm (z upp). GLB-importen ger meter med z upp. Molnigt:
jämnt ljus från en ljusgrå himmel utan sol (som på foton i mulet väder, bra för att bedöma material).
"""
import argparse
import json
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import material  # noqa: E402

a = argparse.ArgumentParser()
a.add_argument("glb")
a.add_argument("material")
a.add_argument("vyer")
a.add_argument("ut")
a.add_argument("--bredd", type=int, default=400)
a.add_argument("--sampel", type=int, default=32)
a.add_argument("--vy", action="append")
a.add_argument("--blend")
arg = a.parse_args(sys.argv[sys.argv.index("--") + 1:])
MATERIAL = json.load(open(arg.material, encoding="utf-8"))
VYER = json.load(open(arg.vyer, encoding="utf-8"))

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=arg.glb)
for namn, p in MATERIAL.items():
    material.skapa(namn, p)

sc = bpy.context.scene
w = bpy.data.worlds.new("Himmel")
sc.world = w
w.use_nodes = True
sky = w.node_tree.nodes.new("ShaderNodeTexSky")
bg = w.node_tree.nodes["Background"]
moln = w.node_tree.nodes.new("ShaderNodeRGB")
moln.outputs[0].default_value = (0.80, 0.82, 0.85, 1.0)
sol = bpy.data.objects.new("Sol", bpy.data.lights.new("Sol", "SUN"))
sc.collection.objects.link(sol)
sol.data.angle = math.radians(0.6)
sol.data.energy = 3.0

kameror = {}
for namn, v in VYER.items():
    k = bpy.data.objects.new(f"Kamera {namn}", bpy.data.cameras.new(f"Kamera {namn}"))
    sc.collection.objects.link(k)
    p = Vector([c / 1000 for c in v["kamera"]])
    m = Vector([c / 1000 for c in v["mal"]])
    k.location = p
    k.rotation_euler = (m - p).to_track_quat("-Z", "Y").to_euler()
    k.data.lens = v.get("brannvidd", 35)
    k.data.clip_start = 0.05
    k.data.clip_end = 1000
    kameror[namn] = k

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
# Khronos PBR Neutral återger materialens färger troget även i sol (AgX bleker mättade färger mot vitt)
try:
    sc.view_settings.view_transform = "Khronos PBR Neutral"
except TypeError:
    sc.view_settings.view_transform = "AgX"


def stall_in(v: dict) -> None:
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
    inne, molnigt = v.get("inne", False), v.get("molnigt", False)
    w.node_tree.links.new((moln if molnigt else sky).outputs[0], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 1.0 if molnigt else 0.6 if inne else 0.25
    sol.hide_render = molnigt
    sol.rotation_euler = (math.radians(90 - el), 0, math.radians(-az))
    sc.view_settings.exposure = 1.2 if inne else -0.3


for namn, v in VYER.items():
    if arg.vy and namn not in arg.vy:
        continue
    stall_in(v)
    sc.camera = kameror[namn]
    sc.render.filepath = f"{arg.ut}/{namn}.png"
    bpy.ops.render.render(write_still=True)
    print("RENDERAD", sc.render.filepath)

if arg.blend:
    forsta = next(iter(VYER))
    stall_in(VYER[forsta])
    sc.camera = kameror[forsta]
    bpy.ops.wm.save_as_mainfile(filepath=arg.blend)
    print("SPARAD", arg.blend)
