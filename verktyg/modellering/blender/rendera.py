"""Blender (i bakgrunden): läs modellens GLB och scenens beskrivning, bygg de procedurella materialen (material.py),
himlen och solen efter dagsljuset, ljusportalerna i fönstren och en kamera per vy (scen.py), och rendera med Cycles.

    Blender -b --factory-startup -P rendera.py -- scen.json

scen.json (från `mod rendera`): {"glb": fil, "ut": mapp, "kvalitet": "skiss" … "slutlig", "bredd": px eller null,
"hojd_m": platsens höjd, "portaler": [...], "material": {namn: parametrar}, "vyer": {namn: vy}, "blend": fil eller
null}; vy: "kamera" och "mal" [x, y, z] i mm, "lins" (mm), "lodrat" (vågrät kamera), "inne", "ljus" (dagsljus.Ljus),
"ev" (EV100 eller null: automatisk), "vitbalans" (K, standard 5 500), "dolj" (delar av sökvägar).
"""
import json
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import material  # noqa: E402
import omgivning  # noqa: E402
import scen as S  # noqa: E402

SCEN = json.load(open(sys.argv[sys.argv.index("--") + 1], encoding="utf-8"))

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SCEN["glb"])
for namn, p in SCEN["material"].items():
    material.skapa(namn, p)

sc = bpy.context.scene
kvalitet = dict(S.KVALITET[SCEN["kvalitet"]])
if SCEN.get("bredd"):
    kvalitet["bredd"] = SCEN["bredd"]
S.cycles(sc, kvalitet)
himmel = S.Himmel(sc)
S.portaler(SCEN.get("portaler", []))
if SCEN.get("omgivning"):
    o = SCEN["omgivning"]
    omgivning.bygg((o["mitt"][0] / 1000, o["mitt"][1] / 1000), o["z_bas"] / 1000, o.get("terrang", "Mark/"),
                   SCEN.get("geodata"))
portaler = [o for o in bpy.data.objects if o.name.startswith("Portal ")]


def stall_in(namn: str, vy: dict) -> None:
    for o in bpy.data.objects:
        if o.type == "MESH":
            sok = o.get("sokvag", "") or o.name
            o.hide_render = any(d in sok for d in vy.get("dolj", []))
    for o in portaler:
        o.hide_render = not vy.get("inne", False)
    himmel.stall_in(vy["ljus"], SCEN.get("hojd_m", 0.0))
    S.vitbalans(sc, vy.get("vitbalans", 5500.0))
    sc.camera = S.kamera(namn, vy)


for namn, vy in SCEN["vyer"].items():
    stall_in(namn, vy)
    ev = vy.get("ev")
    if ev is None:
        ev = S.auto_ev(sc) + (0.0 if vy.get("inne") else 0.0)
    S.exponering(sc, ev)
    lj = vy["ljus"]
    print(f"LJUS {namn}: {lj['tid']} {lj['vader']}, sol {lj['sol_lux'] / 1000:.0f} klx, himmel "
          f"{lj['himmel_lux'] / 1000:.1f} klx, EV {ev:.1f}")
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_depth = "8"
    sc.render.filepath = os.path.join(SCEN["ut"], f"{namn}.png")
    bpy.ops.render.render(write_still=True)
    print("RENDERAD", sc.render.filepath)

if SCEN.get("blend"):
    namn, vy = next(iter(SCEN["vyer"].items()))
    stall_in(namn, vy)
    bpy.ops.wm.save_as_mainfile(filepath=SCEN["blend"])
    print("SPARAD", SCEN["blend"])
