"""Blender (i bakgrunden): läs modellens GLB och scenens beskrivning, bygg de procedurella materialen (material.py),
himlen och solen efter dagsljuset, ljusportalerna i fönstren och en kamera per vy (scen.py), och rendera med Cycles.

    Blender -b --factory-startup -P rendera.py -- scen.json

scen.json (från `mod rendera`): {"glb": fil, "ut": mapp, "kvalitet": "skiss" … "slutlig", "bredd": px eller null,
"hojd_m": platsens höjd, "portaler": [...], "lampor": {grupp: lampor}, "armaturer": [...] (elinstallationens, med
ljusfördelningen som IES), "material": {namn: parametrar}, "vyer": {namn:
vy}, "blend": fil eller null}; vy: "kamera" och "mal" [x, y, z] i mm, "lins" (mm), "lodrat" (vågrät kamera), "inne",
"lampor" (grupperna som är tända), "tand" (elinstallationens tändgrupper som är tända: {grupp: nivå 0–1}),
"ljus" (dagsljus.Ljus),
"ev" (EV100 eller null: automatisk), "vitbalans" (K; standard ute efter dagsljusets färgtemperatur och inne
automatisk, som ögats anpassning), "dolj" (delar av sökvägar).
"""
import json
import os
import sys
import time

import bpy
from mathutils import Vector

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
natthimmel = S.Natthimmel(sc)
S.portaler(SCEN.get("portaler", []))
if SCEN.get("omgivning"):
    o = SCEN["omgivning"]
    omgivning.bygg((o["mitt"][0] / 1000, o["mitt"][1] / 1000), o["z_bas"] / 1000, o.get("terrang", "Mark/"),
                   SCEN.get("geodata"), SCEN.get("tillgangar"))
portaler = [o for o in bpy.data.objects if o.name.startswith("Portal ")]
lampor = S.lampor(SCEN.get("lampor", {}))
armaturer = S.armaturer(SCEN.get("armaturer", []))


def stall_in(namn: str, vy: dict) -> None:
    for o in bpy.data.objects:
        if o.type == "MESH" and "sokvag" in o:                # modellens delar (inte hjälpobjekt som hålen)
            o.hide_render = any(d in o["sokvag"] for d in vy.get("dolj", []))
    for o in portaler:
        o.hide_render = not vy.get("inne", False)
    for grupp, obs in lampor.items():
        for o in obs:
            o.hide_render = grupp not in vy.get("lampor", [])
    for a in armaturer:
        a.tand_till(float(vy.get("tand", {}).get(a.tand, 0.0)))
    natt = SCEN.get("natter", {}).get(vy.get("natt") or "")
    natt_ute = natt is not None and not vy.get("inne")         # nattbilderna ute: månhimlen och tonkurvan
    mane = natt.get("mane") if natt_ute else None
    himmel.stall_in(S.manhimlen(vy["ljus"], mane) if mane else vy["ljus"], SCEN.get("hojd_m", 0.0), vy.get("himmel"))
    omgivning.mark_i_morker(natt_ute)
    S.nattkompression(sc, False)
    S.vitbalans(sc, vy.get("vitbalans") or S.dagsljusets_vitbalans(vy["ljus"]))
    if "matyta" not in vy:
        sc.camera = S.kamera(namn, vy)
    natthimmel.stall_in(natt, Vector(vy["kamera"]) / 1000 if "kamera" in vy else None)


for namn, vy in SCEN["vyer"].items():
    stall_in(namn, vy)
    if "matyta" in vy:                                    # belysningsstyrkan på en mätyta (ljusplan)
        S.matyta(sc, vy["matyta"], os.path.join(SCEN["ut"], namn))
        print("MATYTA", os.path.join(SCEN["ut"], namn))
        continue
    ev = vy.get("ev")
    auto_vit = vy.get("inne") and "vitbalans" not in vy
    if ev is None or auto_vit:
        px = S.forhandsbild(sc)
        if ev is None:
            ev = S.auto_ev(px) - (S.INNE_LJUSARE if vy.get("inne") else 0.0)
            if not vy.get("inne") and vy["ljus"]["sol_hojd"] < -6.0:
                ev = max(ev, S.NATT_EV)
        if auto_vit:
            cct, la, d = S.auto_vitbalans(sc, px)
            print(f"VITBALANS {namn}: ljuset {cct:.0f} K, adaptationsluminansen {la:.0f} cd/m², anpassning {d:.2f}")
    S.exponering(sc, ev)
    S.brusgrans(sc, kvalitet["troskel"], ev)
    S.nattkompression(sc, bool(vy.get("natt")) and not vy.get("inne"))
    lj = vy["ljus"]
    print(f"LJUS {namn}: {lj['tid']} {lj['vader']}, sol {lj['sol_lux'] / 1000:.0f} klx, himmel "
          f"{lj['himmel_lux'] / 1000:.1f} klx, EV {ev:.1f}")
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_depth = "8"
    sc.render.filepath = os.path.join(SCEN["ut"], f"{namn}.png")
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    print("RENDERAD", sc.render.filepath, f"({time.time() - t0:.0f} s)")

if SCEN.get("blend"):
    namn, vy = next(iter(SCEN["vyer"].items()))
    stall_in(namn, vy)
    bpy.ops.wm.save_as_mainfile(filepath=SCEN["blend"])
    print("SPARAD", SCEN["blend"])
