"""
Läs en STEP-sammanställning (t.ex. Onshape-export, AP242/AP214) och ge snabb åtkomst till delarna.

    from modell import Modell
    m = Modell()                          # standardfilen, eller Modell("väg/till/fil.step")
    for d in m.valj("Källaren"):          # delsträng i sökvägen, glob (*?), #id eller #id-id
        print(d.id, d.sokvag, d.bbox, d.volym)
    s = m.form(d)                         # exakt B-rep (OCP TopoDS_Shape) i världskoordinater
    V, F = m.nat(d)                       # triangelnät (float32 N×3, int32 M×3) för rendering

Första inläsningen av en fil bygger en cache i .cache/<filnamn>-<hash>/ (index.json, nat.npz, former.brep),
därefter går allt snabbt. Ändras STEP-filen byggs cachen om automatiskt (hash på innehållet).

Enhet mm, STEP-filens globala koordinatsystem. Färger i sRGB 0–1.
"""
import hashlib
import json
import re
import time
from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
ROT = HERE.parent.parent
STANDARD = ROT / "modeller" / "trebodar.step"
CACHE = HERE / ".cache"
FORMAT = 1                     # höj när cacheformatet ändras
NAT_LIN = 2.0                  # triangulering: kordavvikelse (mm)
NAT_VINKEL = 0.35              # triangulering: vinkelavvikelse (rad)
GRA = (0.7, 0.7, 0.7)


@dataclass
class Del:
    id: int
    sokvag: str                # "Hus Struktur <1>/Källaren <1>/K Pillar [3]" (utan rotens namn)
    namn: str
    farg: tuple
    bbox: tuple                # (xmin, ymin, zmin, xmax, ymax, zmax), snäv
    volym: float               # mm³
    tyngdpunkt: tuple
    area: float                # mm²
    solider: int
    ytor: dict = field(default_factory=dict)   # yttyp -> antal

    @property
    def storlek(self):
        b = self.bbox
        return (b[3] - b[0], b[4] - b[1], b[5] - b[2])

    @property
    def grupp(self):
        return self.sokvag.rsplit("/", 1)[0] if "/" in self.sokvag else ""


def filhash(fil):
    return hashlib.sha1(Path(fil).read_bytes()).hexdigest()[:12]


class Modell:
    def __init__(self, fil=None, tyst=False):
        self.fil = Path(fil) if fil else STANDARD
        if not self.fil.exists():
            raise FileNotFoundError(self.fil)
        self.hash = filhash(self.fil)
        self.cache = CACHE / f"{self.fil.stem}-{self.hash}"
        if not (self.cache / "index.json").exists() or json.loads(
                (self.cache / "index.json").read_text(encoding="utf-8")).get("format") != FORMAT:
            _bygg_cache(self.fil, self.cache, tyst)
        idx = json.loads((self.cache / "index.json").read_text(encoding="utf-8"))
        self.index = idx
        self.rot = idx["rot"]
        self.noder = idx["noder"]
        self.delar = [Del(**{k: (tuple(v) if isinstance(v, list) else v) for k, v in d.items()})
                      for d in idx["delar"]]
        self._former = None
        self._nat = None

    # ---- urval ----------------------------------------------------------------------------
    def valj(self, uttryck=None, utom=None):
        """Delar som matchar uttrycket (kommaseparerat): #12, #12-20, glob (*?[]) eller delsträng.
        Skiftlägesokänsligt mot sökvägen. Tomt uttryck = alla delar."""
        ut = self.delar if not uttryck else [d for d in self.delar if _matchar(d, uttryck)]
        if utom:
            ut = [d for d in ut if not _matchar(d, utom)]
        return ut

    def del_(self, id_):
        return self.delar[id_]

    # ---- geometri -------------------------------------------------------------------------
    def form(self, d):
        """Exakt B-rep för delen (världskoordinater, mm)."""
        if self._former is None:
            from OCP.BRep import BRep_Builder
            from OCP.BRepTools import BRepTools
            from OCP.TopoDS import TopoDS_Compound, TopoDS_Iterator, TopoDS_Shape
            s = TopoDS_Shape()
            BRepTools.Read_s(s, str(self.cache / "former.brep"), BRep_Builder())
            it = TopoDS_Iterator(s)
            self._former = []
            while it.More():
                self._former.append(it.Value())
                it.Next()
        return self._former[d.id if isinstance(d, Del) else d]

    def nat(self, d):
        """Triangelnät (V float32 N×3, F int32 M×3) för delen, utåtriktade normaler."""
        if self._nat is None:
            z = np.load(self.cache / "nat.npz")
            self._nat = {k: z[k] for k in z.files}
        i = d.id if isinstance(d, Del) else d
        v0, v1, f0, f1 = self._nat["offs"][i]
        return self._nat["V"][v0:v1], self._nat["F"][f0:f1]

    def bbox(self, delar=None):
        delar = self.delar if delar is None else delar
        if not delar:
            return None
        b = np.array([d.bbox for d in delar])
        return tuple(b[:, :3].min(0)) + tuple(b[:, 3:].max(0))

    def grupper(self):
        """Gruppnoder (sammanställningar) med sina delar."""
        ut = []
        for n in self.noder:
            if n["grupp"]:
                pre = n["sokvag"] + "/" if n["sokvag"] else ""
                ut.append((n, [d for d in self.delar if d.sokvag.startswith(pre)]))
        return ut


def _matchar(d, uttryck):
    for u in (x.strip() for x in uttryck.split(",")):
        if not u:
            continue
        m = re.fullmatch(r"#?(\d+)(?:-(\d+))?", u)
        if m:
            a = int(m.group(1)); b = int(m.group(2) or a)
            if a <= d.id <= b:
                return True
            continue
        s, ul = d.sokvag.lower(), u.lower()
        if any(c in u for c in "*?"):
            ul = ul.replace("[", "[[]")        # [n] i delnamn är bokstavligt, inte teckenklass
            if fnmatch(s, ul) or fnmatch(d.namn.lower(), ul) or fnmatch(s, "*" + ul + "*"):
                return True
        elif ul in s:
            return True
    return False


# ---- cachebygge --------------------------------------------------------------------------------

def _bygg_cache(fil, katalog, tyst=False):
    from OCP.BRep import BRep_Builder, BRep_Tool
    from OCP.BRepAdaptor import BRepAdaptor_Surface
    from OCP.BRepBndLib import BRepBndLib
    from OCP.BRepGProp import BRepGProp
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    from OCP.BRepTools import BRepTools
    from OCP.Bnd import Bnd_Box
    from OCP.GProp import GProp_GProps
    from OCP.IFSelect import IFSelect_ReturnStatus
    from OCP.Quantity import Quantity_Color
    from OCP.STEPCAFControl import STEPCAFControl_Reader
    from OCP.TCollection import TCollection_ExtendedString
    from OCP.TDF import TDF_Label
    from OCP.TDataStd import TDataStd_Name
    from OCP.TDocStd import TDocStd_Document
    from OCP.TopAbs import TopAbs_FACE, TopAbs_REVERSED, TopAbs_SOLID
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopLoc import TopLoc_Location
    from OCP.TopoDS import TopoDS, TopoDS_Compound
    from OCP.XCAFDoc import XCAFDoc_ColorGen, XCAFDoc_ColorSurf, XCAFDoc_ColorTool, XCAFDoc_DocumentTool
    from OCP.XCAFDoc import XCAFDoc_ShapeTool as ST
    from OCP.collections import Sequence_TDF_Label

    t0 = time.time()
    logg = (lambda *a: None) if tyst else (lambda *a: print("[cache]", *a, flush=True))
    logg(f"läser {fil.name} …")
    doc = TDocStd_Document(TCollection_ExtendedString("XmlOcaf"))
    r = STEPCAFControl_Reader()
    r.SetColorMode(True); r.SetNameMode(True); r.SetLayerMode(True)
    if r.ReadFile(str(fil)) != IFSelect_ReturnStatus.IFSelect_RetDone:
        raise RuntimeError(f"kunde inte läsa {fil}")
    r.Transfer(doc)
    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())

    def namn(l):
        a = TDataStd_Name()
        return a.Get().ToExtString() if l.FindAttribute(TDataStd_Name.GetID_s(), a) else ""

    def farg(*labels):
        c = Quantity_Color()
        for l in labels:
            for t in (XCAFDoc_ColorSurf, XCAFDoc_ColorGen):
                if XCAFDoc_ColorTool.GetColor_s(l, t, c):
                    return tuple(round(Quantity_Color.Convert_LinearRGB_To_sRGB_s(v), 4)
                                 for v in (c.Red(), c.Green(), c.Blue()))
        return None

    noder, leaf = [], []    # leaf: (sokvag, namn, farg, shape)

    def ga(l, loc, sokvag, djup, arvd_farg):
        ref = l
        if ST.IsReference_s(l):
            ref = TDF_Label()
            ST.GetReferredShape_s(l, ref)
            loc = loc.Multiplied(ST.GetLocation_s(l))
        f = farg(l, ref) or arvd_farg
        if ST.IsAssembly_s(ref):
            noder.append({"sokvag": sokvag, "namn": namn(l) or namn(ref), "djup": djup, "grupp": True})
            komp = Sequence_TDF_Label()
            ST.GetComponents_s(ref, komp)
            barn = [komp.Value(i) for i in range(1, komp.Length() + 1)]
            namnen = [namn(b) or "?" for b in barn]
            raknare = {}
            for b, n in zip(barn, namnen):
                if namnen.count(n) > 1:
                    raknare[n] = raknare.get(n, 0) + 1
                    n = f"{n} [{raknare[n]}]"
                ga(b, loc, f"{sokvag}/{n}" if sokvag else n, djup + 1, f)
        else:
            s = ST.GetShape_s(ref)
            if not loc.IsIdentity():
                s = s.Moved(loc)
            noder.append({"sokvag": sokvag, "namn": namn(l) or namn(ref), "djup": djup, "grupp": False,
                          "id": len(leaf)})
            leaf.append((sokvag, sokvag.rsplit("/", 1)[-1], f or GRA, s))

    fria = Sequence_TDF_Label()
    st.GetFreeShapes(fria)
    rotnamn = []
    for i in range(1, fria.Length() + 1):
        l = fria.Value(i)
        rotnamn.append(namn(l))
        # en ensam rotsammanställning ingår inte i sökvägarna; annars får varje fri form sitt namn
        ensam_grupp = fria.Length() == 1 and ST.IsAssembly_s(l)
        ga(l, TopLoc_Location(), "" if ensam_grupp else (namn(l) or f"{fil.stem}_{i}"), 0, None)
    logg(f"{len(leaf)} delar, {len([n for n in noder if n['grupp']])} grupper ({time.time() - t0:.1f} s)")

    # egenskaper, triangulering
    delar, V, F, offs = [], [], [], []
    nv = nf = 0
    comp = TopoDS_Compound()
    bb = BRep_Builder()
    bb.MakeCompound(comp)
    for i, (sokvag, nm, f, s) in enumerate(leaf):
        bb.Add(comp, s)
        b = Bnd_Box()
        BRepBndLib.AddOptimal_s(s, b, False, False)
        p, q = b.CornerMin(), b.CornerMax()
        g = GProp_GProps(); BRepGProp.VolumeProperties_s(s, g)
        a = GProp_GProps(); BRepGProp.SurfaceProperties_s(s, a)
        c = g.CentreOfMass()
        ytor, nsol = {}, 0
        e = TopExp_Explorer(s, TopAbs_SOLID)
        while e.More():
            nsol += 1; e.Next()
        BRepMesh_IncrementalMesh(s, NAT_LIN, False, NAT_VINKEL, True)
        vs, fs, n0 = [], [], 0
        e = TopExp_Explorer(s, TopAbs_FACE)
        while e.More():
            fa = TopoDS.Face(e.Current())
            typ = str(BRepAdaptor_Surface(fa).GetType()).split("_")[-1]
            ytor[typ] = ytor.get(typ, 0) + 1
            loc = TopLoc_Location()
            t = BRep_Tool.Triangulation_s(fa, loc)
            if t is not None:
                tr = loc.Transformation()
                pts = np.array([t.Node(k).Transformed(tr).Coord() for k in range(1, t.NbNodes() + 1)])
                tri = np.array([t.Triangle(k).Get() for k in range(1, t.NbTriangles() + 1)]) - 1
                if fa.Orientation() == TopAbs_REVERSED:
                    tri = tri[:, ::-1]
                vs.append(pts); fs.append(tri + n0); n0 += len(pts)
            e.Next()
        vs = np.concatenate(vs) if vs else np.zeros((0, 3))
        fs = np.concatenate(fs) if fs else np.zeros((0, 3), int)
        offs.append((nv, nv + len(vs), nf, nf + len(fs)))
        nv += len(vs); nf += len(fs)
        V.append(vs.astype(np.float32)); F.append(fs.astype(np.int32))
        delar.append({"id": i, "sokvag": sokvag, "namn": nm, "farg": list(f),
                      "bbox": [round(v, 3) for v in (p.X(), p.Y(), p.Z(), q.X(), q.Y(), q.Z())],
                      "volym": round(g.Mass(), 1), "tyngdpunkt": [round(v, 2) for v in c.Coord()],
                      "area": round(a.Mass(), 1), "solider": nsol, "ytor": ytor})
    katalog.mkdir(parents=True, exist_ok=True)
    BRepTools.Write_s(comp, str(katalog / "former.brep"))
    np.savez_compressed(katalog / "nat.npz", V=np.concatenate(V), F=np.concatenate(F),
                        offs=np.array(offs, dtype=np.int64))
    idx = {"format": FORMAT, "fil": str(fil), "hash": filhash(fil), "skapad": time.strftime("%Y-%m-%d %H:%M"),
           "rot": rotnamn[0] if len(rotnamn) == 1 else fil.stem, "noder": noder, "delar": delar,
           "nat": {"lin": NAT_LIN, "vinkel": NAT_VINKEL, "trianglar": nf}}
    (katalog / "index.json").write_text(json.dumps(idx, ensure_ascii=False, indent=1), encoding="utf-8")
    logg(f"klar: {nf} trianglar, {time.time() - t0:.1f} s → {katalog.relative_to(HERE)}")
