"""glTF 2.0 binär (GLB) för rendering (Blender) och webben (three.js).

Hierarki med namn, ett nät per unik del (instanser delar nät), PBR-material, UV i delens lokala koordinater
(texturens fibrer längs lokala x), metadata i `extras`. Meter, y uppåt (en rotnod vrider modellens z uppåt).
"""
from __future__ import annotations

import json
import struct
from pathlib import Path
from typing import Any

import numpy as np

from ..karna import Karna
from ..modell import Del, Montage


def _linjar(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _uv(V: np.ndarray, N: np.ndarray) -> np.ndarray:
    """Lådprojektion i lokala koordinater (m): fibrer längs x där ytan tillåter det."""
    a = np.abs(N)
    uv = np.empty((len(V), 2))
    mx = a[:, 0] >= np.maximum(a[:, 1], a[:, 2])
    my = ~mx & (a[:, 1] >= a[:, 2])
    mz = ~mx & ~my
    uv[mx] = V[mx][:, [1, 2]]
    uv[my] = V[my][:, [0, 2]]
    uv[mz] = V[mz][:, [0, 1]]
    return uv / 1000.0


def skriv(rot: Montage, fil: Path, karna: Karna, extra: dict[str, Any] | None = None) -> None:
    karna.forbered(d.form for _, d, _ in rot.platta())
    bin_ = bytearray()
    views: list[dict[str, Any]] = []
    accessors: list[dict[str, Any]] = []
    meshes: list[dict[str, Any]] = []
    materials: list[dict[str, Any]] = []
    nodes: list[dict[str, Any]] = []
    mat_index: dict[str, int] = {}
    mesh_index: dict[int, int] = {}

    def view(data: bytes, target: int) -> int:
        while len(bin_) % 4:
            bin_.append(0)
        views.append({"buffer": 0, "byteOffset": len(bin_), "byteLength": len(data), "target": target})
        bin_.extend(data)
        return len(views) - 1

    def accessor(arr: np.ndarray, typ: str, ctype: int, target: int, minmax: bool = False) -> int:
        a: dict[str, Any] = {"bufferView": view(arr.tobytes(), target), "componentType": ctype,
                             "count": len(arr), "type": typ}
        if minmax:
            a["min"] = arr.min(0).tolist()
            a["max"] = arr.max(0).tolist()
        accessors.append(a)
        return len(accessors) - 1

    def material(d: Del) -> int:
        m = d.material
        if m.namn not in mat_index:
            # CAD-färgen, matt; det verkliga utseendet följer med i extras (Blender bygger sina egna material)
            rgb = [_linjar(int(m.cad_farg[i:i + 2], 16) / 255) for i in (1, 3, 5)]
            mat: dict[str, Any] = {"name": m.namn, "pbrMetallicRoughness": {
                "baseColorFactor": rgb + [m.opacitet], "metallicFactor": 0.0, "roughnessFactor": 0.75},
                "extras": {"textur": m.textur, "densitet": m.densitet, "beskrivning": m.beskrivning,
                           "verklig": {"farg": m.farg, "metall": m.metall, "grovhet": m.grovhet}}}
            if m.opacitet < 1:
                mat["alphaMode"] = "BLEND"
            materials.append(mat)
            mat_index[m.namn] = len(materials) - 1
        return mat_index[m.namn]

    def mesh(d: Del) -> int | None:
        if id(d) not in mesh_index:
            n = karna.nat(d.form)
            if len(n.F) == 0:
                return None
            V = n.V.astype(np.float64)
            prim = {"attributes": {"POSITION": accessor((V / 1000).astype(np.float32), "VEC3", 5126, 34962, True),
                                   "NORMAL": accessor(n.N, "VEC3", 5126, 34962),
                                   "TEXCOORD_0": accessor(_uv(V, n.N).astype(np.float32), "VEC2", 5126, 34962)},
                    "indices": accessor(n.F.reshape(-1), "SCALAR", 5125, 34963),
                    "material": material(d)}
            meshes.append({"name": d.namn, "primitives": [prim]})
            mesh_index[id(d)] = len(meshes) - 1
        return mesh_index[id(d)]

    def nod(x: Del | Montage, namn: str, M: np.ndarray | None, vag: str) -> int:
        n: dict[str, Any] = {"name": namn}
        if M is not None and not np.allclose(M, np.eye(4)):
            T = M.copy()
            T[:3, 3] /= 1000.0
            n["matrix"] = T.T.reshape(-1).tolist()
        nodes.append(n)
        i = len(nodes) - 1
        if isinstance(x, Del):
            m = mesh(x)
            if m is not None:
                n["mesh"] = m
            n["extras"] = {"sokvag": vag, "del": x.namn, "material": x.material.namn,
                           **({"artikel": x.artikel} if x.artikel else {}),
                           **({"beskrivning": x.beskrivning} if x.beskrivning else {})}
        else:
            n["children"] = [nod(c.barn, c.namn, c.placering.matris(), f"{vag}/{c.namn}") for c in x.barn]
            n["extras"] = {"sokvag": vag, **({"kod": x.kod} if x.kod else {}),
                           **({"beskrivning": x.beskrivning} if x.beskrivning else {})}
        return i

    rotnod = nod(rot, rot.namn, None, rot.namn)
    nodes.append({"name": "z-upp", "matrix": [1, 0, 0, 0, 0, 0, -1, 0, 0, 1, 0, 0, 0, 0, 0, 1], "children": [rotnod]})
    gltf: dict[str, Any] = {"asset": {"version": "2.0", "generator": "verktyg/modellering"}, "scene": 0,
                            "scenes": [{"nodes": [len(nodes) - 1], **({"extras": extra} if extra else {})}],
                            "nodes": nodes, "meshes": meshes, "materials": materials, "accessors": accessors,
                            "bufferViews": views, "buffers": [{"byteLength": len(bin_)}]}
    js = json.dumps(gltf, ensure_ascii=False, separators=(",", ":")).encode()
    js += b" " * (-len(js) % 4)
    while len(bin_) % 4:
        bin_.append(0)
    fil.parent.mkdir(parents=True, exist_ok=True)
    with open(fil, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(bin_)))
        f.write(struct.pack("<II", len(js), 0x4E4F534A))
        f.write(js)
        f.write(struct.pack("<II", len(bin_), 0x004E4942))
        f.write(bin_)
