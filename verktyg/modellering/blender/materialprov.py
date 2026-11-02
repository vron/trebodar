"""Materialprov (Blender i bakgrunden): ett material på en uppsättning bitar under mjukt dagsljus, för att bedöma
materialet på nära håll och att bitarna inte blir lika varandra: tolv skåpluckor (600 × 700 × 19, fibrerna lodräta),
en bänkskiva (2 400 × 600 × 30) och några lösa brädor. Bitarna har modellens axlar för virke: x längs fibrerna, y
tvärs ytan och z genom tjockleken, så att lamell="y" ger lameller tvärs luckorna och bänkskivan.

    Blender -b --factory-startup -P materialprov.py -- prov.json

prov.json: {"namn": materialet, "parametrar": {...}, "ut": png, "bredd": px, "sampel": n}
"""
import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import material  # noqa: E402
import scen as S  # noqa: E402

P = json.load(open(sys.argv[sys.argv.index("--") + 1], encoding="utf-8"))
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene


def lada(namn: str, dx: float, dy: float, dz: float, pos: tuple[float, float, float],
         rot: tuple[float, float, float] = (0.0, 0.0, 0.0)) -> bpy.types.Object:
    """Rätblock (m) i objektets axlar, vridet med rot (Euler XYZ). Modellens y är Blenders z i objektet (glTF), så ett
    block med x längs fibrerna, y genom tjockleken och z tvärs ytan har modellens axlar för virke."""
    me = bpy.data.meshes.new(namn)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector(((v.co.x + 0.5) * dx, (v.co.y + 0.5) * dy, (v.co.z + 0.5) * dz))
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(namn, me)
    sc.collection.objects.link(ob)
    ob.location = pos
    ob.rotation_euler = rot
    return ob


mat = material.skapa(P["namn"], P["parametrar"])
# skåpluckor i två rader, fibrerna lodräta (blockets x lodrätt)
bitar = []
for i in range(6):
    for j in range(2):
        bitar.append(lada(f"Lucka {i}{j}", 0.70, 0.019, 0.60, (i * 0.62, 0.0, 0.05 + j * 0.72),
                          (0.0, -math.pi / 2, 0.0)))
# bänkskivan framför och lösa brädor på den, fibrerna längs skivan (tjockleken lodrät)
bitar.append(lada("Bänkskiva", 2.40, 0.03, 0.60, (0.6, -0.35, 0.0), (math.pi / 2, 0.0, 0.0)))
for k in range(4):
    bitar.append(lada(f"Bräda {k}", 1.6, 0.022, 0.12 + 0.02 * k, (0.9 + 0.05 * k, -0.71 + 0.14 * k, 0.03 + 0.022 * k),
                      (math.pi / 2, 0.0, 0.05 * k - 0.08)))
for b in bitar:
    b.data.materials.append(mat)
# rummet: grått golv och vägg bakom
golv = lada("Golv", 12.0, 12.0, 0.01, (-4.0, -8.0, -0.01))
vagg = lada("Vägg", 12.0, 0.05, 6.0, (-4.0, 0.08, -0.01))
grå = bpy.data.materials.new("Grå")
grå.use_nodes = True
grå.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.35, 0.35, 0.35, 1)
golv.data.materials.append(grå)
vagg.data.materials.append(grå)
# ljus: mulen himmel och ett stort fönster snett från vänster
w = bpy.data.worlds.new("Himmel")
sc.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.8, 0.85, 0.95, 1)
w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.6
lj = bpy.data.lights.new("Fönster", "AREA")
lj.shape, lj.size, lj.size_y, lj.energy = "RECTANGLE", 3.0, 2.0, 900.0
lo = bpy.data.objects.new("Fönster", lj)
sc.collection.objects.link(lo)
lo.location = (-2.0, -3.5, 2.6)
lo.rotation_euler = (Vector((1.6, 1.0, 0.5)) - lo.location).to_track_quat("-Z", "Y").to_euler()
kam = bpy.data.objects.new("Kamera", bpy.data.cameras.new("Kamera"))
sc.collection.objects.link(kam)
if P.get("nara"):
    # en lucka på nära håll (bilden ca 0,5 m bred)
    kam.location = (1.55, -0.75, 1.05)
    kam.rotation_euler = (Vector((1.55, 0.0, 0.95)) - kam.location).to_track_quat("-Z", "Y").to_euler()
    kam.data.lens = 50
else:
    kam.location = (1.75, -3.6, 1.55)
    kam.rotation_euler = (Vector((1.75, 0.0, 0.62)) - kam.location).to_track_quat("-Z", "Y").to_euler()
    kam.data.lens = 32
sc.camera = kam
S.cycles(sc, {"bredd": int(P.get("bredd", 1600)), "sampel": int(P.get("sampel", 128)), "troskel": 0.02,
              "studsar": 8})
S.vitbalans(sc, 6500.0)
S.exponering(sc, S.auto_ev(S.forhandsbild(sc), nyckel=0.4))
sc.render.filepath = P["ut"]
bpy.ops.render.render(write_still=True)
print("RENDERAD", P["ut"])
