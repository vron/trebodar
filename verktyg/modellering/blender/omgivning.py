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
NARA_STEG = 0.3                 # ringarnas avstånd över tomten (det fina rutnätet)
OVERGANG = 5.0                  # från modellens mark till höjdmodellen [m] (med det fina rutnätet)
LUMA = (0.2126, 0.7152, 0.0722)
# Poly Havens texturer (CC0) i tillgångarna (lokalt/polyhaven/texturer): sida [m]; kroma, hur mycket av texturens egna
# färgskiftningar som följer med (0: bara ljusheten, resten är markens färg); kontrast, hur mycket av dess
# ljusskiftningar; höjd, höjdkartans amplitud [m]
TEXTURER = {
    "berg": {"namn": "rock_01", "sida": 2.0, "kroma": 0.15, "kontrast": 0.8, "hojd": 0.012},
    "gras": {"namn": "leafy_grass", "sida": 2.0, "kroma": 0.3, "kontrast": 0.7, "hojd": 0.02},
    "barr": {"namn": "forrest_ground_03", "sida": 2.0, "kroma": 0.4, "kontrast": 0.9, "hojd": 0.01},
}
TALL_HOJD = (11.0, 15.0)        # de inmätta tallarnas höjd [m]
HALL_TRAD = 0.8                 # trädens täthet i hällmarkens dungar (skogen 1)
DUNGE_CELL = (45.0, 15.0)       # dungarnas två rutnät [m]
# Poly Havens modeller (CC0) i tillgångarna (lokalt/polyhaven/modeller): blend-filen och objektet för varje variant
MODELLER = {
    "tall": [("pine_tree_01/pine_tree_01_1k.blend", f"pine_tree_01_{v}_LOD2") for v in "abc"],
    "gran": [("fir_tree_01/fir_tree_01_1k.blend", f"fir_tree_01_{v}_LOD2") for v in "abc"],
    "block": [(f"namaqualand_boulder_0{n}/namaqualand_boulder_0{n}_2k.blend", f"namaqualand_boulder_0{n}_LOD1")
              for n in (4, 6)],
}
SKOGENS = {"tall": ("Tall", 10.0), "gran": ("Gran", 9.0)}    # modellerna i skogen: ersätter sorten, höjd [m]
# modellernas färgbilder: mättnaden gånger den första, sedan gånger färgen (linjärt), som granit och tallbarr på platsen
TONING = {"namaqualand_boulder_04": (0.3, (1.15, 1.2, 1.25)), "namaqualand_boulder_06": (0.3, (1.15, 1.2, 1.25)),
          "pine_tree_01_twig": (1.0, (0.72, 0.88, 0.8))}


def _bilinjar(z: np.ndarray, x0: float, y0: float, cell: float, x: np.ndarray, y: np.ndarray) -> np.ndarray:
    ny, nx = z.shape
    fx = np.clip((x - x0) / cell, 0, nx - 1.001)
    fy = np.clip((y - y0) / cell, 0, ny - 1.001)
    j, i = fx.astype(int), fy.astype(int)
    tx, ty = fx - j, fy - i
    return (z[i, j] * (1 - tx) * (1 - ty) + z[i, j + 1] * tx * (1 - ty) + z[i + 1, j] * (1 - tx) * ty
            + z[i + 1, j + 1] * tx * ty)


class Rutnat:
    """Höjdmodellen: modellens z (m) i ett rutnät med cellen cell från (x0, y0), och över tomten ett fint rutnät
    (nara, ur Lantmäteriets markhöjdmodell och inmätningarna, modellering/terrang.py) där det finns."""

    def __init__(self, mapp: str):
        self.besk = json.load(open(os.path.join(mapp, "omgivning.json"), encoding="utf-8"))
        b = self.besk
        self.n, self.cell, self.x0, self.y0 = b["n"], b["cell"], b["x0"], b["y0"]
        self.z = np.fromfile(os.path.join(mapp, "hojd.f32"), dtype=np.float32).reshape(self.n, self.n)
        self.nara = b.get("nara")
        if self.nara and os.path.exists(os.path.join(mapp, "nara.f32")):
            na = self.nara
            self.zn = np.fromfile(os.path.join(mapp, "nara.f32"), dtype=np.float32).reshape(na["ny"], na["nx"])
        else:
            self.nara = None
        self.mapp = mapp

    @property
    def radie(self) -> float:
        return self.cell * (self.n - 1) / 2

    @property
    def nara_radie(self) -> float:
        """Avståndet från rutnätets mitt där det fina rutnätet slutar (det minsta, 0 utan det)."""
        if not self.nara:
            return 0.0
        na = self.nara
        mx, my = self.x0 + self.radie, self.y0 + self.radie
        return float(min(mx - na["x0"], na["x0"] + na["cell"] * (na["nx"] - 1) - mx,
                         my - na["y0"], na["y0"] + na["cell"] * (na["ny"] - 1) - my))

    def hojd(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        z = _bilinjar(self.z, self.x0, self.y0, self.cell, x, y)
        if self.nara:
            na = self.nara
            inne = ((x >= na["x0"]) & (x <= na["x0"] + na["cell"] * (na["nx"] - 1)) & (y >= na["y0"])
                    & (y <= na["y0"] + na["cell"] * (na["ny"] - 1)))
            zn = _bilinjar(self.zn, na["x0"], na["y0"], na["cell"], x, y)
            z = np.where(inne & np.isfinite(zn), zn, z)
        return z


def inre_ring(mitt: tuple[float, float], z_bas: float, terrang: str, vinklar: int = STRALAR
              ) -> list[tuple[float, float, float]]:
    """Terrängens ytterkant i varje riktning från mitt: (vinkel, radie, höjd), en bit innanför kanten. Strålarna
    uppifrån träffar bara terrängen (ett BVH-träd av dess trianglar i världens koordinater)."""
    from mathutils.bvhtree import BVHTree
    dg = bpy.context.evaluated_depsgraph_get()
    hornen, trianglar, n = [], [], 0
    for o in bpy.context.scene.objects:
        if o.type != "MESH" or terrang not in (o.get("sokvag", "") or o.name):
            continue
        me = o.evaluated_get(dg).data
        me.calc_loop_triangles()
        co = np.zeros(len(me.vertices) * 3)
        me.vertices.foreach_get("co", co)
        M = np.array(o.matrix_world)
        hornen.append(co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3])
        tri = np.zeros(len(me.loop_triangles) * 3, dtype=np.int64)
        me.loop_triangles.foreach_get("vertices", tri)
        trianglar.append(tri.reshape(-1, 3) + n)
        n += len(me.vertices)
    if not hornen:
        return []
    bvh = BVHTree.FromPolygons(np.concatenate(hornen).tolist(), np.concatenate(trianglar).tolist())
    ned = Vector((0, 0, -1))

    def traff(x: float, y: float) -> float | None:
        loc = bvh.ray_cast(Vector((x, y, 300.0)), ned, 600.0)[0]
        return None if loc is None else loc.z

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
    if rut and rut.nara:
        # över tomten ringar tätt (NARA_STEG), så att det fina rutnätets former kommer med, sedan glesare utåt
        r_n = max(rut.nara_radie - 5.0, 10.0)
        tata = np.arange(0.0, r_n, NARA_STEG)
        avst = np.concatenate([tata, r_n + (yttre - r_n) * (np.arange(1, RINGAR + 1) / RINGAR) ** 2.3])
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
    w = np.exp(-avst / (OVERGANG if rut and rut.nara else 20.0))[None, :]
    Z = w * z0[:, None] + (1 - w) * zf
    verts = np.stack([X, Y, Z], axis=-1).reshape(-1, 3)
    n, kk = len(inre), len(avst)
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
    """Grannhusen: väggar till takfoten och valmat tak (ringen krympt mot mitten), eller platt tak ("tak": "platt");
    färgerna slumpade per hus, om de inte anges ("farg", "takfarg")."""
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
        zt = h["z"] + max(3.6, h["hojd"]) if h.get("tak") != "platt" else h["z"] + h["hojd"]
        zv = h["z"] + max(2.4, h["hojd"] - 2.2) if h.get("tak") != "platt" else zt - 0.01
        bredd = min(math.dist(p[i], p[(i + 1) % len(p)]) for i in range(len(p)))
        k = max(0.0, 1.0 - min(0.9, (zt - zv) / max(bredd * 0.5, 0.5) * 0.9))
        vf, tf = rgba(_valj(VAGGFARGER, rng.random())), rgba(_valj(TAKFARGER, rng.random()))
        vf, tf = rgba(h["farg"]) if "farg" in h else vf, rgba(h["takfarg"]) if "takfarg" in h else tf
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


def _textur(g: Graf, k: bpy.types.NodeSocket, mapp: str, t: dict) -> tuple[object, object, object] | None:
    """Poly Havens textur t på marken efter världens x och y: (detalj, grovhet, höjd), där detalj är det som markens
    egen färg multipliceras med (texturens färg genom dess medelfärg, efter kroma och kontrast). Två avläsningar med
    olika skala och vridning blandas efter brus, så att upprepningen inte syns."""
    bas = os.path.join(mapp, t["namn"], t["namn"])
    if not all(os.path.exists(f"{bas}_{karta}_2k.jpg") for karta in ("diff", "rough", "disp")):
        return None
    fak = g.jamn(g.brus(k, 0.3, 2.0), 0.42, 0.58)
    vektorer = [g.nod("ShaderNodeMapping", Vector=k, Location=forskj, Rotation=(0.0, 0.0, vrid),
                      Scale=(1 / sida,) * 3).outputs["Vector"]
                for sida, vrid, forskj in ((t["sida"], 0.0, (0.0, 0.0, 0.0)), (t["sida"] * 1.37, 0.9, (0.31, 0.67, 0.0)))]

    def bild(karta: str) -> tuple[bpy.types.NodeSocket, bpy.types.Image]:
        im = bpy.data.images.load(f"{bas}_{karta}_2k.jpg", check_existing=True)
        if karta != "diff":
            im.colorspace_settings.name = "Non-Color"
        avl = []
        for v in vektorer:
            n = g.nod("ShaderNodeTexImage", Vector=v)
            n.image = im
            avl.append(n.outputs["Color"])
        return g.blanda(fak, *avl), im
    diff, im = bild("diff")
    px = np.empty(len(im.pixels), dtype=np.float32)
    im.pixels.foreach_get(px)
    c = px.reshape(-1, 4)[:, :3]
    medel = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4).mean(axis=0)     # linjärt, som i noderna
    ljus = float(medel @ np.array(LUMA))
    farg = g.vmatte("DIVIDE", diff, tuple(float(v) for v in medel))
    ljushet = g.vmatte("DOT_PRODUCT", diff, tuple(v / ljus for v in LUMA))
    r = g.vmatte("ADD", g.vmatte("SCALE", farg, t["kroma"]), g.vmatte("SCALE", ljushet, 1 - t["kroma"]))
    detalj = g.vmatte("ADD", g.vmatte("SCALE", r, t["kontrast"]), (1 - t["kontrast"],) * 3)
    hojd = g.matte("MULTIPLY", g.matte("SUBTRACT", bild("disp")[0], 0.5), t["hojd"])
    return detalj, bild("rough")[0], hojd


MARK_REFLEX_NATT = 0.0         # markens speglande del i nattbilderna ute (Principled: Specular IOR Level, annars 0,5)


def mark_i_morker(morker: bool) -> None:
    """Markens speglande del, i nattbilderna ute borttagen (MARK_REFLEX_NATT): i mörker är månen, den månbelysta himlen
    och fönstren markens enda ljus, och gräset och berget, förenklade till en yta med textur, speglar dem vid flacka
    vinklar som is och glittrar; på dagen försvinner det bredvid solljuset."""
    mat = bpy.data.materials.get("Omgivning mark")
    if mat is None:
        return
    for n in mat.node_tree.nodes:
        if n.type == "BSDF_PRINCIPLED":
            n.inputs["Specular IOR Level"].default_value = MARK_REFLEX_NATT if morker else 0.5


def markmaterial(rut: Rutnat | None, tillgangar: str | None = None) -> bpy.types.Material:
    """Marken: västkustens hällmark som standard (mest berg i dagen, efter brus och lutning, med sprickor av ljung och
    gräs och barr i svackorna; gräs, ljung och en emellan) och marktäcket från geodata (berg, skog, åker, trädgård, snår, våtmark, sand, vägar, stigar,
    havsbotten). Över tomten följer marktäcket de inmätta punkterna (nara_tacke.png): berg, gräsmatta och barr under
    träden. Med tillgångarna får berget, gräset och barren detaljer ur riktiga texturer (TEXTURER)."""
    mat = bpy.data.materials.get("Omgivning mark") or bpy.data.materials.new("Omgivning mark")
    g = Graf(mat)
    m, lin = g.matte, g.linj
    geo = g.nod("ShaderNodeNewGeometry")
    k = geo.outputs["Position"]                 # världens x och y (också på modellens terräng, med sina egna axlar)
    x, y, z = g.sep(k)
    normal = geo.outputs["Normal"]
    lutning = m("SUBTRACT", 1.0, g.sep(normal)[2])                     # 0 plant, 1 lodrätt
    stor = g.brus(k, 0.025, 4.0, 0.6)
    mellan = g.brus(k, 0.25, 4.0, 0.6)
    fin = g.brus(k, 3.0, 3.0, 0.6)
    korn = g.brus(k, 40.0, 2.0, 0.6)
    tx = {}
    for namn, t in TEXTURER.items() if tillgangar else ():
        if (v := _textur(g, k, os.path.join(tillgangar, "texturer"), t)) is not None:
            tx[namn] = v

    def detalj(farg: object, namn: str) -> object:
        return g.vmatte("MULTIPLY", farg, tx[namn][0]) if namn in tx else farg

    def tal(namn: str, i: int, annars: float) -> object:
        """Texturens grovhet (i = 1) eller höjd (2), annars."""
        return tx[namn][i] if namn in tx else annars

    def mix(f: object, a: object, b: object) -> object:
        """Från talet a till b efter f."""
        return m("ADD", a, m("MULTIPLY", f, m("SUBTRACT", b, a)))
    # hällmarken: mest berg i dagen (som i flygbilderna), i svackorna gräs med ljung och en
    hall = g.jamn(lin((lutning, 2.2), (stor, 1.6), (mellan, 0.6), bas=-0.6), 0.35, 0.6)
    gras = g.blanda(g.jamn(mellan, 0.35, 0.65), rgba("#525a2f"), rgba("#6c6a3a"))
    gras = g.blanda(m("MULTIPLY", g.jamn(stor, 0.55, 0.7), 0.6), gras, rgba("#5b4f3d"))       # ljung
    gras = detalj(g.blanda(m("MULTIPLY", g.jamn(fin, 0.62, 0.72), 0.7), gras, rgba("#2f3b26")), "gras")   # enar
    barr = detalj(g.blanda(g.jamn(mellan, 0.3, 0.7), rgba("#5f4a3a"), rgba("#7d5c44")), "barr")
    berg = g.blanda(g.jamn(fin, 0.3, 0.7), rgba("#8a8882"), rgba("#a19f98"))
    berg = g.blanda(m("MULTIPLY", g.jamn(korn, 0.6, 0.75), 0.5), berg, rgba("#bbbab2"))       # lavar
    berg = g.blanda(m("MULTIPLY", g.jamn(mellan, 0.62, 0.7), 0.6), berg, rgba("#4d4b47"))     # mörka strimmor
    # sprickorna i berget, med ljung och gräs: kanterna i ett starkt förvrängt Voronoi-mönster (celler om 15–20 m),
    # avbrutna efter brus
    vr = g.nod("ShaderNodeTexVoronoi", {"feature": "DISTANCE_TO_EDGE"}, Scale=0.06,
               Vector=g.vmatte("ADD", k, g.vmatte("SCALE", g.vmatte("SUBTRACT", g.nod(
                   "ShaderNodeTexNoise", Vector=k, Scale=0.12, Detail=4.0).outputs["Color"], (0.5, 0.5, 0.5)), 9.0)))
    spricka = m("MULTIPLY", g.jamn(vr.outputs["Distance"], 0.03, 0.008),
                g.jamn(g.brus(k, 0.07, 2.0), 0.4, 0.55))
    berg = g.blanda(spricka, berg, rgba("#3c3f2b"))
    svacka = m("MULTIPLY", g.jamn(g.brus(k, 0.9, 3.0, 0.6), 0.68, 0.73), 0.9)                  # barr i svackorna
    berg = g.blanda(svacka, detalj(berg, "berg"), barr)
    col = g.blanda(hall, gras, berg)
    grov = mix(hall, tal("gras", 1, 0.92), mix(svacka, tal("berg", 1, 0.77), tal("barr", 1, 0.95)))
    hojd_tx = mix(hall, tal("gras", 2, 0.0), mix(svacka, tal("berg", 2, 0.0), tal("barr", 2, 0.0)))
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
        col = g.blanda(mask("tradgard"), col, g.blanda(g.jamn(fin, 0.4, 0.6), rgba("#455734"), rgba("#52663f")))
        col = g.blanda(mask("aker"), col, g.blanda(g.jamn(mellan, 0.3, 0.7), rgba("#8e9a4b"), rgba("#b3a865")))
        col = g.blanda(mask("snar"), col, g.blanda(g.jamn(fin, 0.4, 0.6), rgba("#3e4a2c"), rgba("#59563a")))
        col = g.blanda(mask("vatmark"), col, rgba("#55603f"))
        col = g.blanda(mask("skog"), col, g.blanda(g.jamn(fin, 0.4, 0.6), rgba("#2c3322"), rgba("#46452f")))
        col = g.blanda(mask("berg", 0.4), col, berg)
        col = g.blanda(mask("sand", 0.1), col, rgba("#cdbb94"))
        col = g.blanda(mask("hav", 0.05), col, rgba("#4a4a40"))
        col = g.blanda(g.jamn(kanal["stig"], 0.3, 0.7), col, rgba("#8a7a62"))
        col = g.blanda(g.jamn(kanal["vag"], 0.3, 0.7), col, rgba("#4b4c4e"))
        grov = m("ADD", grov, lin((kanal["vag"], -0.25), (mask("hav", 0.05), -0.4)))
        tacke = os.path.join(rut.mapp, "nara_tacke.png")
        if rut.nara and os.path.exists(tacke):
            na = rut.nara
            uv = g.vektor(m("DIVIDE", m("SUBTRACT", x, na["x0"] - na["cell"] / 2), na["cell"] * na["nx"]),
                          m("DIVIDE", m("SUBTRACT", y, na["y0"] - na["cell"] / 2), na["cell"] * na["ny"]), 0.0)
            t = g.nod("ShaderNodeTexImage", Vector=uv)
            t.image = bpy.data.images.load(tacke, check_existing=True)
            t.image.colorspace_settings.name = "Non-Color"
            t.extension = "CLIP"
            t.interpolation = "Cubic"
            kant = m("SUBTRACT", mellan, 0.5)

            def nara(v: object, skarpa: float) -> object:
                """Tomtens mask med brusig kant."""
                return g.jamn(lin((v, 1.0), (kant, skarpa)), 0.3, 0.55)
            fb, fg, fbarr = (nara(v, s) for v, s in zip(g.sep(t.outputs["Color"]), (0.3, 0.15, 0.4)))
            fbarr = m("MULTIPLY", fbarr, g.jamn(g.brus(k, 0.6, 3.0, 0.6), 0.38, 0.6))          # fläckvis
            gmatta = detalj(g.blanda(g.jamn(fin, 0.35, 0.65), rgba("#4c6633"), rgba("#5a7639")), "gras")
            for f, farg, namn, gv in ((fb, berg, "berg", 0.77), (fg, gmatta, "gras", 0.92), (fbarr, barr, "barr", 0.95)):
                col = g.blanda(f, col, farg)
                grov = mix(f, grov, tal(namn, 1, gv))
                hojd_tx = mix(f, hojd_tx, tal(namn, 2, 0.0))
    col = g.ljus(col, lin((m("SUBTRACT", korn, 0.5), 0.25), (m("SUBTRACT", fin, 0.5), 0.2), bas=1.0))
    hojd = lin((m("SUBTRACT", fin, 0.5), 0.08), (m("SUBTRACT", korn, 0.5), 0.02))
    g.yta(col, grov, 0.0, m("ADD", hojd, hojd_tx) if tx else hojd, styrka=0.6, avstand=1.0)
    return mat


def bygg(mitt: tuple[float, float], z_bas: float, terrang: str, mapp: str | None, tillgangar: str | None = None
         ) -> None:
    """Hela omgivningen: marken (med eller utan geodata), havet, grannhusen och träden; med tillgångarna (Poly Haven,
    lokalt/polyhaven) markens texturer och tomtens inmätta träd och stenar."""
    rut = Rutnat(mapp) if mapp and os.path.exists(os.path.join(mapp, "omgivning.json")) else None
    inre = inre_ring(mitt, z_bas, terrang)
    if len(inre) < 8:
        return
    ob = mark(mitt, inre, rut, z_bas)
    mm = markmaterial(rut, tillgangar)
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
        trad(ob, rut, mitt, tillgangar=tillgangar)
        if tillgangar:
            inmatta(rut, tillgangar)


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


def tradsorter(tillgangar: str | None = None) -> bpy.types.Collection:
    """Tallar, granar, björkar och enar som förlagor för instanserna (två av vissa sorter); med tillgångarna är
    tallarna och granarna Poly Havens (SKOGENS)."""
    kol = bpy.data.collections.get("Träd") or bpy.data.collections.new("Träd")
    if kol.objects:
        return kol
    ersatta = set()
    for namn, (sort, h) in SKOGENS.items():
        for j, o in enumerate(_modell(tillgangar, namn)):
            ob = bpy.data.objects.new(f"{sort} {j + 1}", o.data)
            ob.scale = (h / _granser(o.data)[1][2],) * 3
            kol.objects.link(ob)
            ersatta.add(sort)
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
        if namn.split()[0] not in ersatta:
            kol.objects.link(_trad_mesh(namn, h, r, krona, sf, kf, i + 3))
    return kol


def trad(mark_ob: bpy.types.Object, rut: Rutnat, mitt: tuple[float, float], fri: float = 18.0,
         tillgangar: str | None = None) -> None:
    """Träd i skogen (tät) och i dungar på hällmarken (_dungar), med Geometry Nodes: punkter på marken efter tätheten
    (attributet täthet per hörn: skogens mask, inget på hav, vägar, byggnader, nära huset och på tomten, där de inmätta
    träden står) och en slumpad sort, vridning och storlek per träd."""
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
    tathet = np.clip(mask["skog"] + HALL_TRAD * _dungar(co[:, 0], co[:, 1]) * (1 - mask["skog"])
                     * (1 - mask["tradgard"]) * (1 - mask["aker"]), 0, 1)
    tathet *= ((1 - mask["hav"]) * (1 - mask["vatten"]) * (1 - mask["vag"]) * (1 - mask["byggnad"])
               * (1 - mask["berg"] * 0.7))
    tathet *= np.clip((d - fri) / 25.0, 0, 1) * (d < 1800.0)
    tathet *= co[:, 2] > rut.besk["z_hav"] + 0.5
    if (omrade := _objekt(rut).get("omrade")):
        tathet *= ~_inuti(co[:, 0], co[:, 1], np.array(omrade))
    attr = me.attributes.new("tathet", "FLOAT", "POINT")
    attr.data.foreach_set("value", tathet.astype(np.float32))
    kol = tradsorter(tillgangar)
    ng = bpy.data.node_groups.new("Träd", "GeometryNodeTree")
    ng.interface.new_socket("Geometri", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometri", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N = ng.nodes
    inn, ut = N.new("NodeGroupInput"), N.new("NodeGroupOutput")
    ford = N.new("GeometryNodeDistributePointsOnFaces")
    ford.distribute_method = "POISSON"
    ford.inputs["Distance Min"].default_value = 3.2
    ford.inputs["Density Max"].default_value = 0.08
    fat = N.new("GeometryNodeInputNamedAttribute")
    fat.data_type = "FLOAT"
    fat.inputs["Name"].default_value = "tathet"
    ngl = ng.links
    ngl.new(inn.outputs[0], ford.inputs["Mesh"])
    ngl.new(fat.outputs["Attribute"], ford.inputs["Density Factor"])
    samling = N.new("GeometryNodeCollectionInfo")
    samling.inputs["Collection"].default_value = kol
    samling.inputs["Separate Children"].default_value = True
    samling.inputs["Reset Children"].default_value = False         # förlagorna står i origo, med sin skala
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
    stl.inputs["Min"].default_value = 0.45
    stl.inputs["Max"].default_value = 1.4
    stl.inputs["Seed"].default_value = 5
    ngl.new(stl.outputs["Value"], inst.inputs["Scale"])
    forena = N.new("GeometryNodeJoinGeometry")
    ngl.new(inn.outputs[0], forena.inputs[0])
    ngl.new(inst.outputs["Instances"], forena.inputs[0])
    ngl.new(forena.outputs[0], ut.inputs[0])
    mod = mark_ob.modifiers.new("Träd", "NODES")
    mod.node_group = ng


def _dungar(x: np.ndarray, y: np.ndarray, fro: int = 7) -> np.ndarray:
    """Tallarnas dungar på hällmarken: 0–1 ur slumptal i två rutnät (DUNGE_CELL m), bilinjärt och summerat, med en
    mjuk tröskel så att dungarna täcker nästan hälften av marken (som i flygbilderna)."""
    rng = np.random.default_rng(fro)
    f = np.zeros_like(x)
    for cell, vikt in zip(DUNGE_CELL, (0.65, 0.35)):
        x0, y0 = x.min() - cell, y.min() - cell
        nx, ny = int((x.max() - x0) / cell) + 3, int((y.max() - y0) / cell) + 3
        f += vikt * _bilinjar(rng.random((ny, nx)), x0, y0, cell, x, y)
    t = np.clip((f - 0.42) / 0.15, 0, 1)
    return t * t * (3 - 2 * t)


def _objekt(rut: Rutnat) -> dict:
    """Tomtens inmätta träd, stenar och området de är inmätta i (nara_objekt.json, modellering/terrang.py)."""
    fil = os.path.join(rut.mapp, "nara_objekt.json")
    return json.load(open(fil, encoding="utf-8")) if os.path.exists(fil) else {}


def _inuti(x: np.ndarray, y: np.ndarray, poly: np.ndarray) -> np.ndarray:
    """Punkterna (x, y) inuti polygonen poly (hörnen, n × 2)."""
    inne = np.zeros(len(x), dtype=bool)
    for (x1, y1), (x2, y2) in zip(poly, np.roll(poly, -1, axis=0)):
        if y1 != y2:
            inne ^= ((y1 > y) != (y2 > y)) & (x < (x2 - x1) * (y - y1) / (y2 - y1) + x1)
    return inne


def _tona(mat: bpy.types.Material, mattnad: float, farg: tuple[float, float, float]) -> None:
    """Materialets färgbilder (diff): mättnaden gånger mattnad, sedan gånger farg."""
    nt = mat.node_tree
    for n in [n for n in nt.nodes if n.type == "TEX_IMAGE" and n.image and "_diff" in n.image.name]:
        till = [lk.to_socket for lk in nt.links if lk.from_node == n and lk.from_socket.name == "Color"]
        hsv = nt.nodes.new("ShaderNodeHueSaturation")
        hsv.inputs["Saturation"].default_value = mattnad
        nt.links.new(n.outputs["Color"], hsv.inputs["Color"])
        mul = nt.nodes.new("ShaderNodeMix")
        mul.data_type, mul.blend_type = "RGBA", "MULTIPLY"
        mul.inputs[0].default_value = 1.0
        nt.links.new(hsv.outputs["Color"], mul.inputs[6])
        mul.inputs[7].default_value = (*farg, 1.0)
        for sockel in till:
            nt.links.new(mul.outputs[2], sockel)


_MODELLER: dict[str, list[bpy.types.Object]] = {}


def _modell(tillgangar: str | None, namn: str) -> list[bpy.types.Object]:
    """Varianterna av Poly Havens modell namn (MODELLER) med sina nät, material (tonade efter TONING) och bilder, en
    gång per scen; de som saknas i tillgångarna hoppas över."""
    if namn not in _MODELLER:
        _MODELLER[namn] = []
        for fil, objekt in MODELLER[namn] if tillgangar else ():
            fil = os.path.join(tillgangar, "modeller", fil)
            if not os.path.exists(fil):
                continue
            with bpy.data.libraries.load(os.path.abspath(fil), link=False) as (src, dst):
                dst.objects = [objekt] if objekt in src.objects else []
            _MODELLER[namn] += [o for o in dst.objects if o is not None]
        for mat in {m for o in _MODELLER[namn] for m in o.data.materials if m}:
            if mat.name in TONING:
                _tona(mat, *TONING[mat.name])
    return _MODELLER[namn]


def _granser(me: bpy.types.Mesh) -> tuple[np.ndarray, np.ndarray]:
    co = np.zeros(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    return co.min(axis=0), co.max(axis=0)


def inmatta(rut: Rutnat, tillgangar: str) -> None:
    """Tomtens inmätta träd och stenar (nara_objekt.json): Poly Havens tallar (tre sorter, TALL_HOJD höga, vridna och
    lite lutade) och rundade granitblock (två sorter), så stora som stenarna är inmätta och nedsjunkna i marken. Varje
    träd slumpas ur sitt läge, så att ett träd som läggs till eller tas bort inte ändrar de andra eller stenarna."""
    obj = _objekt(rut)
    if not obj:
        return
    kol = bpy.data.collections.new("Inmätta")
    bpy.context.scene.collection.children.link(kol)
    tallar = _modell(tillgangar, "tall")
    for i, (x, y, z) in enumerate(obj["trad"] if tallar else []):
        rng = np.random.default_rng([11, round(x * 1000) % 2 ** 32, round(y * 1000) % 2 ** 32])
        me = tallar[int(rng.integers(len(tallar)))].data
        s = rng.uniform(*TALL_HOJD) / _granser(me)[1][2]
        ob = bpy.data.objects.new(f"Tall {i + 1}", me)
        ob.scale = (s, s, s)
        ob.rotation_euler = (rng.normal(0, 0.03), rng.normal(0, 0.03), rng.uniform(0, 2 * math.pi))
        ob.location = (x, y, z - 0.2)                                   # rotfoten i marken, också i en slänt
        kol.objects.link(ob)
    block = [(o.data, *_granser(o.data)) for o in _modell(tillgangar, "block")]
    rng = np.random.default_rng(12)
    for i, (x, y, z, storlek, hojd) in enumerate(obj["stenar"] if block else []):
        me, lo, hi = block[int(rng.integers(len(block)))]
        sxy = storlek / max(hi[0] - lo[0], hi[1] - lo[1])
        sz = float(np.clip(hojd / (0.7 * hi[2]), 0.4 * sxy, 1.2 * sxy))
        ob = bpy.data.objects.new(f"Sten {i + 1}", me)
        ob.scale = (sxy, sxy, sz)
        ob.rotation_euler = (0.0, 0.0, rng.uniform(0, 2 * math.pi))
        ob.location = (x, y, min(z + hojd - hi[2] * sz, z - 0.05 - lo[2] * sz))
        kol.objects.link(ob)
