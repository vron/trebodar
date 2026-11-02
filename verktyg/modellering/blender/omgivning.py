"""Omgivningen i Blender: marken från modellens terräng ut till höjdmodellen (geodata, `mod omgivning`), havet,
grannhusen och marktäcket (berg, skog, åker, gräs, vägar …) som material.

Marken är ett polärt nät från modellens mitt: den inre ringen vid terrängens ytterkant (strålar uppifrån) och ringar
utåt, där höjden går från kantens höjd till höjdmodellens på omkring 20 m. Marktäckets masker (tre RGBA-bilder,
geodata.KLASSER) läggs på efter världens x och y. Havet är ett plan på havsytans höjd till horisonten.
"""
from __future__ import annotations

import json
import math
import os

import bpy
import numpy as np
from mathutils import Vector

from graf import Graf, rgba

STRALAR = 1440
RINGAR = 120


class Rutnat:
    """Höjdmodellen: modellens z (m) i ett rutnät med cellen cell från (x0, y0)."""

    def __init__(self, mapp: str):
        self.besk = json.load(open(os.path.join(mapp, "omgivning.json"), encoding="utf-8"))
        b = self.besk
        self.n, self.cell, self.x0, self.y0 = b["n"], b["cell"], b["x0"], b["y0"]
        self.z = np.fromfile(os.path.join(mapp, "hojd.f32"), dtype=np.float32).reshape(self.n, self.n)
        self.mapp = mapp

    @property
    def radie(self) -> float:
        return self.cell * (self.n - 1) / 2

    def hojd(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        fx = np.clip((x - self.x0) / self.cell, 0, self.n - 1.001)
        fy = np.clip((y - self.y0) / self.cell, 0, self.n - 1.001)
        j, i = fx.astype(int), fy.astype(int)
        tx, ty = fx - j, fy - i
        z = self.z
        return (z[i, j] * (1 - tx) * (1 - ty) + z[i, j + 1] * tx * (1 - ty) + z[i + 1, j] * (1 - tx) * ty
                + z[i + 1, j + 1] * tx * ty)


def inre_ring(mitt: tuple[float, float], z_bas: float, terrang: str, vinklar: int = STRALAR
              ) -> list[tuple[float, float, float]]:
    """Terrängens ytterkant i varje riktning från mitt: (vinkel, radie, höjd), en bit innanför kanten."""
    sc = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    terr = {o.name for o in sc.objects if o.type == "MESH" and terrang in (o.get("sokvag", "") or o.name)}

    def traff(x: float, y: float) -> float | None:
        z0 = 300.0
        for _ in range(8):
            ok, loc, _, _, ob, _ = sc.ray_cast(dg, Vector((x, y, z0)), Vector((0, 0, -1)), distance=600.0)
            if not ok:
                return None
            if ob.name in terr:
                return loc.z
            z0 = loc.z - 0.001
        return None

    cx, cy = mitt
    ut = []
    for i in range(vinklar):
        th = 2 * math.pi * i / vinklar
        dx, dy = math.cos(th), math.sin(th)
        sist = None
        for r in range(1, 60):
            if traff(cx + r * dx, cy + r * dy) is not None:
                sist = float(r)
        if sist is None:
            continue
        a, b = sist, sist + 1.0
        for _ in range(7):
            m_ = (a + b) / 2
            a, b = (m_, b) if traff(cx + m_ * dx, cy + m_ * dy) is not None else (a, m_)
        r0 = a - 0.15
        z = traff(cx + r0 * dx, cy + r0 * dy)
        ut.append((th, r0, (z if z is not None else z_bas) - 0.02))
    return ut


def mark(mitt: tuple[float, float], inre: list[tuple[float, float, float]], rut: Rutnat | None, z_bas: float,
         radie: float = 3000.0) -> bpy.types.Object:
    """Marknätet från den inre ringen utåt."""
    yttre = rut.radie - 30.0 if rut else radie
    k = np.arange(RINGAR + 1) / RINGAR
    avst = yttre * k ** 2.3
    th = np.array([t for t, _, _ in inre])
    r0 = np.array([r for _, r, _ in inre])
    z0 = np.array([z for _, _, z in inre])
    R = r0[:, None] + avst[None, :]
    X = mitt[0] + R * np.cos(th)[:, None]
    Y = mitt[1] + R * np.sin(th)[:, None]
    if rut:
        zf = rut.hojd(X, Y)
        # mot nätets ytterkant ned under havsytan (havet fortsätter förbi höjdmodellen)
        kant = np.clip((avst - (yttre - 250.0)) / 250.0, 0, 1)[None, :]
        zf = zf * (1 - kant) + (rut.besk["z_hav"] - 3.0) * kant
    else:
        zf = z_bas + np.zeros_like(X)
    w = np.exp(-avst / 20.0)[None, :]
    Z = w * z0[:, None] + (1 - w) * zf
    verts = np.stack([X, Y, Z], axis=-1).reshape(-1, 3)
    n, kk = len(inre), RINGAR + 1
    i = np.arange(n)[:, None]
    a = np.arange(kk - 1)[None, :]
    j = (i + 1) % n
    faces = np.stack([i * kk + a, i * kk + a + 1, j * kk + a + 1, j * kk + a], axis=-1).reshape(-1, 4)
    me = bpy.data.meshes.new("Omgivning")
    me.from_pydata(verts.tolist(), [], faces.tolist())
    me.update()
    me.shade_smooth()
    ob = bpy.data.objects.new("Omgivning", me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def hav(z: float, radie: float = 40000.0) -> bpy.types.Object:
    me = bpy.data.meshes.new("Hav")
    n = 96
    verts = [(0.0, 0.0, z)] + [(radie * math.cos(2 * math.pi * i / n), radie * math.sin(2 * math.pi * i / n), z)
                              for i in range(n)]
    me.from_pydata(verts, [], [(0, 1 + i, 1 + (i + 1) % n) for i in range(n)])
    ob = bpy.data.objects.new("Hav", me)
    bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(vattenmaterial())
    return ob


# grannhusens färger: väggar (andel, sRGB) och tak
VAGGFARGER = [(0.40, "#8a3324"), (0.30, "#e8e4da"), (0.12, "#d9c58a"), (0.10, "#8c9599"), (0.08, "#5a4636")]
TAKFARGER = [(0.45, "#3a3c3e"), (0.2, "#1f2022"), (0.27, "#7a3a2a"), (0.08, "#9ea3a6")]


def _valj(lista: list[tuple[float, str]], r: float) -> str:
    s = 0.0
    for andel, f in lista:
        s += andel
        if r <= s:
            return f
    return lista[-1][1]


def byggnader(rut: Rutnat) -> bpy.types.Object | None:
    """Grannhusen: väggar till takfoten och valmat tak (ringen krympt mot mitten), färgerna slumpade per hus."""
    hus = rut.besk.get("byggnader", [])
    if not hus:
        return None
    rng = np.random.default_rng(7)
    verts: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    farger: list[tuple[float, float, float, float]] = []
    for h in hus:
        p = [tuple(v) for v in h["horn"]]
        if len(p) < 3:
            continue
        # moturs
        a = sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p)))
        if a < 0:
            p.reverse()
        cx = sum(v[0] for v in p) / len(p)
        cy = sum(v[1] for v in p) / len(p)
        z0 = h["z"] - 0.6
        zv = h["z"] + max(2.4, h["hojd"] - 2.2)
        zt = h["z"] + max(3.6, h["hojd"])
        bredd = min(math.dist(p[i], p[(i + 1) % len(p)]) for i in range(len(p)))
        k = max(0.0, 1.0 - min(0.9, (zt - zv) / max(bredd * 0.5, 0.5) * 0.9))
        vf = rgba(_valj(VAGGFARGER, rng.random()))
        tf = rgba(_valj(TAKFARGER, rng.random()))
        b = len(verts)
        n = len(p)
        verts += [(x, y, z0) for x, y in p] + [(x, y, zv) for x, y in p]
        verts += [(cx + (x - cx) * k, cy + (y - cy) * k, zt) for x, y in p]
        for i in range(n):
            j = (i + 1) % n
            faces.append((b + i, b + j, b + n + j, b + n + i))
            farger.append(vf)
            faces.append((b + n + i, b + n + j, b + 2 * n + j, b + 2 * n + i))
            farger.append(tf)
        faces.append(tuple(b + 2 * n + i for i in range(n)))
        farger.append(tf)
    me = bpy.data.meshes.new("Grannhus")
    me.from_pydata(verts, [], faces)
    me.update()
    attr = me.color_attributes.new("farg", "FLOAT_COLOR", "FACE")
    for i, c in enumerate(farger):
        attr.data[i].color = c
    ob = bpy.data.objects.new("Grannhus", me)
    bpy.context.scene.collection.objects.link(ob)
    mat = bpy.data.materials.new("Grannhus")
    g = Graf(mat)
    g.yta(g.nod("ShaderNodeAttribute", {"attribute_name": "farg"}).outputs["Color"], 0.8)
    ob.data.materials.append(mat)
    return ob


# ------------------------------------------------------------------ material

def vattenmaterial() -> bpy.types.Material:
    """Havet: mörkt blågrönt med reflexer efter Fresnel och vågor i flera skalor (bump)."""
    mat = bpy.data.materials.get("Hav") or bpy.data.materials.new("Hav")
    g = Graf(mat)
    m = g.matte
    k = g.nod("ShaderNodeTexCoord").outputs["Object"]
    stora = g.brus(g.vmatte("MULTIPLY", k, (0.18, 0.06, 1.0)), 1.0, 3.0, 0.5)
    sma = g.brus(g.vmatte("MULTIPLY", k, (1.6, 0.9, 1.0)), 1.0, 4.0, 0.55)
    krus = g.brus(g.vmatte("MULTIPLY", k, (9.0, 7.0, 1.0)), 1.0, 2.0, 0.5)
    hojd = g.linj((stora, 0.25), (sma, 0.06), (krus, 0.012))
    g.yta(rgba("#0d2a33"), 0.035, 0.0, hojd, styrka=1.0, avstand=1.0)
    g.bsdf.inputs["IOR"].default_value = 1.33
    g.bsdf.inputs["Specular IOR Level"].default_value = 0.5
    _ = m
    return mat


def markmaterial(rut: Rutnat | None) -> bpy.types.Material:
    """Marken: västkustens hällmark som standard (gräs, ljung, en och berg i dagen efter brus och lutning) och
    marktäcket från geodata (berg, skog, åker, trädgård, snår, våtmark, sand, vägar, stigar, havsbotten)."""
    mat = bpy.data.materials.get("Omgivning mark") or bpy.data.materials.new("Omgivning mark")
    g = Graf(mat)
    m, lin = g.matte, g.linj
    k = g.nod("ShaderNodeTexCoord").outputs["Object"]
    x, y, z = g.sep(k)
    normal = g.nod("ShaderNodeNewGeometry").outputs["Normal"]
    lutning = m("SUBTRACT", 1.0, g.sep(normal)[2])                     # 0 plant, 1 lodrätt
    stor = g.brus(k, 0.025, 4.0, 0.6)
    mellan = g.brus(k, 0.25, 4.0, 0.6)
    fin = g.brus(k, 3.0, 3.0, 0.6)
    korn = g.brus(k, 40.0, 2.0, 0.6)
    # hällmarken: berg där det är brant eller där bruset säger så, annars gräs med ljung och en
    hall = g.jamn(lin((lutning, 2.2), (stor, 0.9), (mellan, 0.35), bas=-0.75), 0.35, 0.6)
    gras = g.blanda(g.jamn(mellan, 0.35, 0.65), rgba("#6f7a3e"), rgba("#8f8b4a"))
    gras = g.blanda(m("MULTIPLY", g.jamn(stor, 0.55, 0.7), 0.6), gras, rgba("#5b4f3d"))       # ljung
    gras = g.blanda(m("MULTIPLY", g.jamn(fin, 0.62, 0.72), 0.7), gras, rgba("#2f3b26"))       # enar
    berg = g.blanda(g.jamn(fin, 0.3, 0.7), rgba("#8b827a"), rgba("#a9a097"))
    berg = g.blanda(m("MULTIPLY", g.jamn(korn, 0.6, 0.75), 0.5), berg, rgba("#c9c6b8"))       # lavar
    berg = g.blanda(m("MULTIPLY", g.jamn(mellan, 0.62, 0.7), 0.6), berg, rgba("#4a4640"))     # mörka strimmor
    col = g.blanda(hall, gras, berg)
    grov = lin((hall, -0.15), bas=0.92)
    if rut:
        bilder = []
        for i in range(3):
            fil = os.path.join(rut.mapp, f"marktacke_{i}.png")
            im = bpy.data.images.load(fil, check_existing=True)
            im.colorspace_settings.name = "Non-Color"
            L = rut.cell * (rut.n - 1)
            uv = g.vektor(m("DIVIDE", m("SUBTRACT", x, rut.x0), L), m("DIVIDE", m("SUBTRACT", y, rut.y0), L), 0.0)
            t = g.nod("ShaderNodeTexImage", Vector=uv)
            t.image = im
            t.extension = "EXTEND"
            t.interpolation = "Cubic"
            bilder.append((g.sep(t.outputs["Color"]), t.outputs["Alpha"]))
        kanal = {}
        for i, namn in enumerate(rut.besk["kanaler"]):
            for j, kn in enumerate(namn):
                kanal[kn] = bilder[i][0][j] if j < 3 else bilder[i][1]

        def mask(namn: str, skarpa: float = 0.25) -> object:
            """Masken med brusig kant."""
            return g.jamn(lin((kanal[namn], 1.0), (m("SUBTRACT", mellan, 0.5), skarpa)), 0.35, 0.65)
        col = g.blanda(mask("tradgard"), col, g.blanda(g.jamn(fin, 0.4, 0.6), rgba("#5f7d38"), rgba("#73903f")))
        col = g.blanda(mask("aker"), col, g.blanda(g.jamn(mellan, 0.3, 0.7), rgba("#8e9a4b"), rgba("#b3a865")))
        col = g.blanda(mask("snar"), col, g.blanda(g.jamn(fin, 0.4, 0.6), rgba("#3e4a2c"), rgba("#59563a")))
        col = g.blanda(mask("vatmark"), col, rgba("#55603f"))
        col = g.blanda(mask("skog"), col, g.blanda(g.jamn(fin, 0.4, 0.6), rgba("#2c3322"), rgba("#46452f")))
        col = g.blanda(mask("berg", 0.4), col, berg)
        col = g.blanda(mask("sand", 0.1), col, rgba("#cdbb94"))
        col = g.blanda(mask("hav", 0.05), col, rgba("#4a4a40"))
        col = g.blanda(g.jamn(kanal["stig"], 0.3, 0.7), col, rgba("#8a7a62"))
        col = g.blanda(g.jamn(kanal["vag"], 0.3, 0.7), col, rgba("#4b4c4e"))
        grov = lin((kanal["vag"], -0.25), (mask("hav", 0.05), -0.4), bas=0.0)
        grov = m("ADD", grov, lin((hall, -0.15), bas=0.92))
    col = g.ljus(col, lin((m("SUBTRACT", korn, 0.5), 0.25), (m("SUBTRACT", fin, 0.5), 0.2), bas=1.0))
    hojd = lin((m("SUBTRACT", fin, 0.5), 0.08), (m("SUBTRACT", korn, 0.5), 0.02))
    g.yta(col, grov, 0.0, hojd, styrka=0.6, avstand=1.0)
    return mat


def bygg(mitt: tuple[float, float], z_bas: float, terrang: str, mapp: str | None) -> None:
    """Hela omgivningen: marken (med eller utan geodata), havet och grannhusen."""
    rut = Rutnat(mapp) if mapp and os.path.exists(os.path.join(mapp, "omgivning.json")) else None
    inre = inre_ring(mitt, z_bas, terrang)
    if len(inre) < 8:
        return
    ob = mark(mitt, inre, rut, z_bas)
    mm = markmaterial(rut)
    ob.data.materials.append(mm)
    # modellens terräng (fyllnaden runt huset) får samma material som omgivningen
    for o in bpy.context.scene.objects:
        if o.type == "MESH" and terrang in (o.get("sokvag", "") or o.name):
            for i, slot in enumerate(o.material_slots):
                if slot.material and slot.material.name == "Mark":
                    o.material_slots[i].material = mm
    if rut:
        hav(rut.besk["z_hav"])
        byggnader(rut)
        trad(ob, rut, mitt)


# ------------------------------------------------------------------ träd

def _trad_mesh(namn: str, stam_h: float, stam_r: float, krona: dict, stamfarg: str, kronfarg: str, fro: int
               ) -> bpy.types.Object:
    """Ett träd: stam (avsmalnande) och en krona av många små, bucklade klumpar inom kronans form (form: "klot" med
    mitt och radier, "kon" för granar: höjd från, till och radie vid basen), med luckor mellan klumparna."""
    import bmesh
    from mathutils import Matrix
    rng = np.random.default_rng(fro)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=False, segments=8, radius1=stam_r, radius2=stam_r * 0.35, depth=stam_h,
                          matrix=Matrix.Translation((0, 0, stam_h / 2)))
    nstam = len(bm.faces)
    for _ in range(int(krona["klumpar"])):
        if krona["form"] == "kon":
            z0, z1, rb = krona["z"]
            t = rng.random() ** 0.8
            z = z0 + (z1 - z0) * t
            rmax = rb * (1 - t) + 0.15
            v, rr = rng.uniform(0, 2 * math.pi), rmax * math.sqrt(rng.uniform(0.35, 1.0))
            c = (rr * math.cos(v), rr * math.sin(v), z - 0.25 * rr)
            r = rng.uniform(0.35, 0.65) * (0.6 + 0.4 * (1 - t))
            skala = (1.0, 1.0, 0.45)
        else:
            mz, rx, rz = krona["z"], krona["rx"], krona["rz"]
            u = rng.normal(size=3)
            u /= np.linalg.norm(u)
            rad = rng.uniform(0.55, 1.0) ** 0.5
            c = (u[0] * rx * rad, u[1] * rx * rad, mz + u[2] * rz * rad)
            r = rng.uniform(0.45, 0.9) * krona.get("klump", 1.0)
            skala = (1.0, 1.0, 0.7)
        ut = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=r, matrix=Matrix.Translation(c))
        for vert in ut["verts"]:
            d = vert.co - Vector(c)
            vert.co = Vector(c) + Vector((d.x * skala[0], d.y * skala[1], d.z * skala[2])) * rng.uniform(0.75, 1.25)
    me = bpy.data.meshes.new(namn)
    bm.to_mesh(me)
    bm.free()
    for i, p in enumerate(me.polygons):
        p.material_index = 0 if i < nstam else 1
        p.use_smooth = i >= nstam
    ob = bpy.data.objects.new(namn, me)
    for f, nm in ((stamfarg, "stam"), (kronfarg, "krona")):
        mat = bpy.data.materials.get(f"Träd {nm} {namn}") or bpy.data.materials.new(f"Träd {nm} {namn}")
        g = Graf(mat)
        k = g.nod("ShaderNodeTexCoord").outputs["Object"]
        if nm == "krona":
            ljus = g.brus(k, 2.5, 3.0, 0.6)
            col = g.ljus(rgba(f), g.linj((ljus, 0.5), (g.objslump(), 0.3), bas=0.6))
            g.yta(col, 0.9, 0.0, g.brus(k, 9.0, 2.0, 0.6), styrka=0.8, avstand=0.2)
            g.bsdf.inputs["Sheen Weight"].default_value = 0.25
        else:
            z = g.sep(k)[2]
            col = g.blanda(g.jamn(z, stam_h * 0.35, stam_h * 0.6), rgba("#5b5048"), rgba(f)) if "Tall" in namn \
                else g.blanda(g.jamn(g.brus(k, 8.0, 2.0), 0.6, 0.7), rgba(f), rgba("#2a2826")) if "Björk" in namn \
                else rgba(f)
            g.yta(col, 0.9)
        me.materials.append(mat)
    return ob


def tradsorter() -> bpy.types.Collection:
    """Tallar, granar, björkar och enar som förlagor för instanserna (två av vissa sorter)."""
    kol = bpy.data.collections.get("Träd") or bpy.data.collections.new("Träd")
    if kol.objects:
        return kol
    sorter = [
        ("Tall", 10.0, 0.17, {"form": "klot", "z": 9.6, "rx": 2.4, "rz": 1.3, "klumpar": 70}, "#9a6a45", "#26331f"),
        ("Tall 2", 7.5, 0.15, {"form": "klot", "z": 7.0, "rx": 2.8, "rz": 1.4, "klumpar": 80}, "#9a6a45", "#2b3822"),
        ("Tall krokig", 5.0, 0.14, {"form": "klot", "z": 5.0, "rx": 2.6, "rz": 1.2, "klumpar": 60}, "#8a5f40",
         "#283421"),
        ("Gran", 1.0, 0.16, {"form": "kon", "z": (0.8, 11.0, 2.4), "klumpar": 260}, "#4d3a2c", "#1c271b"),
        ("Gran 2", 1.0, 0.14, {"form": "kon", "z": (0.6, 8.0, 1.9), "klumpar": 200}, "#4d3a2c", "#1f2b1d"),
        ("Björk", 4.5, 0.12, {"form": "klot", "z": 7.2, "rx": 2.3, "rz": 2.6, "klumpar": 90, "klump": 0.8}, "#dcd8cc",
         "#4a6328"),
        ("En", 0.2, 0.05, {"form": "kon", "z": (0.1, 2.2, 0.55), "klumpar": 40}, "#4d3a2c", "#24301e"),
    ]
    for i, (namn, h, r, krona, sf, kf) in enumerate(sorter):
        kol.objects.link(_trad_mesh(namn, h, r, krona, sf, kf, i + 3))
    return kol


def trad(mark_ob: bpy.types.Object, rut: Rutnat, mitt: tuple[float, float], fri: float = 18.0) -> None:
    """Träd i skogen (tät) och spridda på hällmarken (gles), med Geometry Nodes: punkter på marken efter tätheten
    (attributet täthet per hörn: skogens mask, inget på hav, vägar, byggnader och nära huset) och en slumpad sort,
    vridning och storlek per träd."""
    me = mark_ob.data
    co = np.zeros(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    mask = {}
    for i, namn in enumerate(rut.besk["kanaler"]):
        im = bpy.data.images.load(os.path.join(rut.mapp, f"marktacke_{i}.png"), check_existing=True)
        w, h = im.size
        px = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)        # rad 0 = söder (bildens nederkant)
        fx = np.clip((co[:, 0] - rut.x0) / rut.cell, 0, w - 1).astype(int)
        fy = np.clip((co[:, 1] - rut.y0) / rut.cell, 0, h - 1).astype(int)
        for j, kn in enumerate(namn):
            mask[kn] = px[fy, fx, j]
    d = np.hypot(co[:, 0] - mitt[0], co[:, 1] - mitt[1])
    tathet = np.clip(mask["skog"] + 0.06 * (1 - mask["skog"]) * (1 - mask["tradgard"]) * (1 - mask["aker"]), 0, 1)
    tathet *= (1 - mask["hav"]) * (1 - mask["vatten"]) * (1 - mask["vag"]) * (1 - mask["byggnad"]) * (1 - mask["berg"] * 0.7)
    tathet *= np.clip((d - fri) / 25.0, 0, 1) * (d < 1800.0)
    tathet *= co[:, 2] > rut.besk["z_hav"] + 0.5
    attr = me.attributes.new("tathet", "FLOAT", "POINT")
    attr.data.foreach_set("value", tathet.astype(np.float32))
    kol = tradsorter()
    ng = bpy.data.node_groups.new("Träd", "GeometryNodeTree")
    ng.interface.new_socket("Geometri", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometri", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N = ng.nodes
    inn, ut = N.new("NodeGroupInput"), N.new("NodeGroupOutput")
    ford = N.new("GeometryNodeDistributePointsOnFaces")
    ford.distribute_method = "POISSON"
    ford.inputs["Distance Min"].default_value = 3.2
    ford.inputs["Density Max"].default_value = 0.05
    fat = N.new("GeometryNodeInputNamedAttribute")
    fat.data_type = "FLOAT"
    fat.inputs["Name"].default_value = "tathet"
    ngl = ng.links
    ngl.new(inn.outputs[0], ford.inputs["Mesh"])
    ngl.new(fat.outputs["Attribute"], ford.inputs["Density Factor"])
    samling = N.new("GeometryNodeCollectionInfo")
    samling.inputs["Collection"].default_value = kol
    samling.inputs["Separate Children"].default_value = True
    samling.inputs["Reset Children"].default_value = True
    inst = N.new("GeometryNodeInstanceOnPoints")
    inst.inputs["Pick Instance"].default_value = True
    ngl.new(ford.outputs["Points"], inst.inputs["Points"])
    ngl.new(samling.outputs["Instances"], inst.inputs["Instance"])
    sort = N.new("FunctionNodeRandomValue")
    sort.data_type = "INT"
    sort.inputs["Min"].default_value = 0
    sort.inputs["Max"].default_value = len(kol.objects) - 1
    ngl.new(sort.outputs["Value"], inst.inputs["Instance Index"])
    vrid = N.new("FunctionNodeRandomValue")
    vrid.data_type = "FLOAT_VECTOR"
    vrid.inputs["Min"].default_value = (0.0, 0.0, 0.0)
    vrid.inputs["Max"].default_value = (0.08, 0.08, 2 * math.pi)
    vrid.inputs["Seed"].default_value = 3
    ngl.new(vrid.outputs["Value"], inst.inputs["Rotation"])
    stl = N.new("FunctionNodeRandomValue")
    stl.data_type = "FLOAT"
    stl.inputs["Min"].default_value = 0.65
    stl.inputs["Max"].default_value = 1.35
    stl.inputs["Seed"].default_value = 5
    ngl.new(stl.outputs["Value"], inst.inputs["Scale"])
    forena = N.new("GeometryNodeJoinGeometry")
    ngl.new(inn.outputs[0], forena.inputs[0])
    ngl.new(inst.outputs["Instances"], forena.inputs[0])
    ngl.new(forena.outputs[0], ut.inputs[0])
    mod = mark_ob.modifiers.new("Träd", "NODES")
    mod.node_group = ng
