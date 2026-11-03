"""
Läs en STEP-sammanställning (den kodgenererade modellen, Onshape-exporten eller annan AP242/AP214) och ge snabb
åtkomst till delarna.

    from modell import Modell
    m = Modell()                          # standardfilen, eller Modell("väg/till/fil.step")
    for d in m.valj("Källaren"):          # delsträng i sökvägen, glob (*?), #id eller #id-id
        print(d.id, d.sokvag, d.bbox, d.volym)
    s = m.form(d)                         # exakt B-rep (OCP TopoDS_Shape) i världskoordinater
    V, F = m.nat(d)                       # triangelnät (float32 N×3, int32 M×3) för rendering

Första inläsningen av en fil bygger en cache i .cache/<filnamn>-<hash>/ (index.json, nat.npz, former.bin),
därefter går allt snabbt. Ändras STEP-filen byggs cachen om automatiskt (hash på innehållet). De senast använda
cacherna per fil sparas.

Den kodgenererade modellen (standardfilen) analyseras i sitt senaste bygge: `mod bygg` skriver cachen direkt ur
modellen (verktyg/modellering, export/analys.py, med samma innehåll och funktioner, `egenskaper`, `triangulera` och
`skriv_cache`, och delarnas nycklar, recept och placering), för STEP-filen eller med `--format analys` utan den, och
pekar ut den i ut/trebodar.analys.json. Har modellens källor ändrats sedan dess byggs den om (`mod bygg --format
analys`, några sekunder) innan den läses; MA_BYGG=0 varnar bara.

Enhet mm, STEP-filens globala koordinatsystem. Färger i sRGB 0–1.
"""
import contextlib
import hashlib
import json
import sys
import re
import time
from dataclasses import dataclass, field
import fnmatch
from functools import cached_property, lru_cache
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
ROT = HERE.parent.parent
STANDARD = (ROT / "modeller" / "trebodar" / "ut" / "trebodar.step").resolve()  # den kodgenererade modellen (mod bygg)
REFERENS = ROT / "modeller" / "referens" / "trebodar-onshape.step"      # Onshape-modellen, fryst
CACHE = HERE / ".cache"
FORMAT = 2                     # höj när cacheformatet ändras (2: formerna binärt, delarnas nycklar)
BEHALL = 4                     # cacher per filnamn som sparas (de senast använda)
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
    nyckel: str | None = None  # delens geometri (recept och placering) när cachen skrivs ur modellen, annars None

    @property
    def storlek(self):
        b = self.bbox
        return (b[3] - b[0], b[4] - b[1], b[5] - b[2])

    @cached_property
    def lag(self):
        """Sökvägen med gemener (för urval)."""
        return self.sokvag.lower()

    @cached_property
    def leder(self):
        return self.lag.split("/")

    @property
    def grupp(self):
        return self.sokvag.rsplit("/", 1)[0] if "/" in self.sokvag else ""


# beräkningarna som modellen läser (armeringen ur R-04–R-06, balkarna ur K-01, grunden ur K-06 …)
BERAKNINGAR = ("K-01", "K-05", "K-06", "AR-01", "AR-02", "R-03", "R-04", "R-05", "R-06", "ritningsmall")


def pekare(step_fil):
    """Filen som pekar ut cachen för modellens senaste bygge (bredvid STEP-filen)."""
    step_fil = Path(step_fil)
    return step_fil.with_name(step_fil.stem + ".analys.json")


def _senaste_bygge(fil):
    """Det senaste bygget av standardmodellen: (cachekatalog, tid), ur pekaren om den är nyare än STEP-filen."""
    p = pekare(fil)
    tider = {f: f.stat().st_mtime for f in (fil, p) if f.exists()}
    if p in tider and tider[p] >= tider.get(fil, 0):
        with contextlib.suppress(ValueError, KeyError, OSError):
            katalog = CACHE / json.loads(p.read_text(encoding="utf-8"))["katalog"]
            if _las_index(katalog) is not None:
                return katalog, tider[p]
    return None, tider.get(fil)


def _nyare_kalla(fil, tid):
    """Den nyaste av modellens källor om den är nyare än tiden (modellens senaste bygge), annars None."""
    kallor = [*(ROT / "modeller" / "trebodar").rglob("*.py"), *(ROT / "verktyg" / "modellering" / "modellering").rglob("*.py")]
    for nr in BERAKNINGAR:
        kallor += [k for k in (ROT / "beräkningar" / nr).rglob("*") if k.suffix in (".py", ".toml", ".json", ".csv")
                   and ".venv" not in k.parts and "__pycache__" not in k.parts]
    nyast = max((k for k in kallor if k.exists()), key=lambda k: k.stat().st_mtime)
    return nyast if tid is None or nyast.stat().st_mtime > tid + 1 else None


def _bygg_om_gammal(fil):
    """Bygg modellens analys (mod bygg --format analys) om dess källor har ändrats efter det senaste bygget;
    MA_BYGG=0: bara varna."""
    import os
    import subprocess
    nyast = _nyare_kalla(fil, _senaste_bygge(fil)[1])
    if nyast is None:
        return
    if os.environ.get("MA_BYGG", "1") == "0":
        print(f"OBS: {nyast.relative_to(ROT)} är nyare än modellens senaste bygge; kör verktyg/modellering/mod bygg",
              file=sys.stderr)
        return
    print(f"OBS: {nyast.relative_to(ROT)} är nyare än modellens senaste bygge: bygger (mod bygg --format analys) …",
          file=sys.stderr, flush=True)
    mod = ROT / "verktyg" / "modellering" / "mod"
    r = subprocess.run([str(mod), "bygg", "--format", "analys"], cwd=mod.parent, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, text=True)
    print("\n".join("  " + rad for rad in r.stdout.splitlines()), file=sys.stderr, flush=True)
    if r.returncode != 0:
        print("OBS: bygget misslyckades; analysen gäller modellens förra bygge", file=sys.stderr)


_HASHAR = {}                   # (fil, ändrad, storlek) -> hash
_INLASTA = {}                  # cachekatalog -> inläst index, delar, former och nät (ma-tjänsten läser varje en gång)


def filhash(fil):
    fil = Path(fil)
    st = fil.stat()
    k = (str(fil.resolve()), st.st_mtime_ns, st.st_size)
    if k not in _HASHAR:
        _HASHAR[k] = hashlib.sha1(fil.read_bytes()).hexdigest()[:12]
    return _HASHAR[k]


def cachekatalog(fil, hash_=None):
    fil = Path(fil)
    return CACHE / f"{fil.stem}-{hash_ or filhash(fil)}"


def _las_index(katalog):
    """Cachens index, eller None om cachen saknas eller har ett annat format."""
    try:
        idx = json.loads((katalog / "index.json").read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    return idx if idx.get("format") == FORMAT else None


def _rensa(katalog):
    """Markera cachen som använd och ta bort de äldsta cacherna för samma filnamn utöver BEHALL, och cacher i ett
    äldre format."""
    import os
    import shutil
    try:
        os.utime(katalog)
    except FileNotFoundError:
        return
    for k in CACHE.glob("*/index.json"):
        with contextlib.suppress(OSError):
            with open(k, "rb") as f:
                m = re.search(rb'"format":\s*(\d+)', f.read(64))          # formatet står först i indexet
            if m and int(m.group(1)) != FORMAT:
                shutil.rmtree(k.parent, ignore_errors=True)
    stam = katalog.name.rsplit("-", 1)[0]
    andra = [k for k in CACHE.glob(f"{stam}-*") if k.is_dir() and re.fullmatch(r"m?[0-9a-f]{11,12}", k.name.rsplit("-", 1)[1])
             and k.name.rsplit("-", 1)[0] == stam]
    for k in sorted(andra, key=lambda k: k.stat().st_mtime, reverse=True)[BEHALL:]:
        if k != katalog:
            shutil.rmtree(k, ignore_errors=True)


class Modell:
    def __init__(self, fil=None, tyst=False):
        self.fil = Path(fil).resolve() if fil else STANDARD
        katalog = None
        if self.fil == STANDARD:
            _bygg_om_gammal(self.fil)
            katalog = _senaste_bygge(self.fil)[0]
        if katalog is None and not self.fil.exists():
            if self.fil == STANDARD:
                raise FileNotFoundError(f"{self.fil} saknas: bygg modellen med verktyg/modellering/mod bygg")
            raise FileNotFoundError(self.fil)
        self.cache = katalog or cachekatalog(self.fil, filhash(self.fil))
        self.hash = self.cache.name.rsplit("-", 1)[1]
        self._inlast = _INLASTA.get(self.cache)
        if self._inlast is None:
            idx = _las_index(self.cache)
            if idx is None:
                _bygg_cache(self.fil, self.cache, tyst)
                idx = _las_index(self.cache)
            delar = [Del(**{k: (tuple(v) if isinstance(v, list) else v) for k, v in d.items()}) for d in idx["delar"]]
            self._inlast = _INLASTA[self.cache] = {"index": idx, "delar": delar, "former": None, "nat": None}
            while len(_INLASTA) > 2:
                _INLASTA.pop(next(iter(_INLASTA)))
        _rensa(self.cache)
        self.index = self._inlast["index"]
        self.rot = self.index["rot"]
        self.noder = self.index["noder"]
        self.delar = self._inlast["delar"]

    # ---- urval ----------------------------------------------------------------------------
    def valj(self, uttryck=None, utom=None):
        """Delar som matchar uttrycket (kommaseparerat): #12, #12-20, glob (*?[]) eller delsträng.
        Skiftlägesokänsligt mot sökvägen. Tomt uttryck = alla delar."""
        ut = self.delar if not uttryck else [d for d in self.delar if _matchare(uttryck)(d)]
        if utom:
            ut = [d for d in ut if not _matchare(utom)(d)]
        return ut

    def del_(self, id_):
        return self.delar[id_]

    # ---- geometri -------------------------------------------------------------------------
    def form(self, d):
        """Exakt B-rep för delen (världskoordinater, mm)."""
        if self._inlast["former"] is None:
            from OCP.BinTools import BinTools
            from OCP.TopoDS import TopoDS_Iterator, TopoDS_Shape
            s = TopoDS_Shape()
            BinTools.Read_s(s, str(self.cache / "former.bin"))
            it = TopoDS_Iterator(s)
            former = []
            while it.More():
                former.append(it.Value())
                it.Next()
            self._inlast["former"] = former
        return self._inlast["former"][d.id if isinstance(d, Del) else d]

    def nat(self, d):
        """Triangelnät (V float32 N×3, F int32 M×3) för delen, utåtriktade normaler."""
        if self._inlast["nat"] is None:
            z = np.load(self.cache / "nat.npz")
            self._inlast["nat"] = {k: z[k] for k in z.files}
        nat = self._inlast["nat"]
        i = d.id if isinstance(d, Del) else d
        v0, v1, f0, f1 = nat["offs"][i]
        return nat["V"][v0:v1], nat["F"][f0:f1]

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


@lru_cache(maxsize=1024)
def _matchare(uttryck):
    """Uttrycket tolkat en gång: en funktion Del -> bool (se Modell.valj)."""
    villkor = []
    for u in (x.strip() for x in uttryck.split(",")):
        if not u:
            continue
        m = re.fullmatch(r"#?(\d+)(?:-(\d+))?", u)
        if m:
            a = int(m.group(1)); b = int(m.group(2) or a)
            villkor.append(lambda d, a=a, b=b: a <= d.id <= b)
            continue
        ul = u.lower()
        if any(c in u for c in "*?"):
            ul = ul.replace("[", "[[]")        # [n] i delnamn är bokstavligt, inte teckenklass
            # utan / mot hela delens namn eller en grupp i sökvägen (V*-K är källarväggarnas kärnor, inte allt med
            # ett V och sedan -K någonstans i sökvägen), med / mot sökvägen
            if "/" in ul:
                hel, inne = re.compile(fnmatch.translate(ul)).match, re.compile(fnmatch.translate("*" + ul + "*")).match
                villkor.append(lambda d, hel=hel, inne=inne: bool(hel(d.lag) or inne(d.lag)))
            else:
                led = re.compile(fnmatch.translate(ul)).match
                villkor.append(lambda d, led=led: any(led(k) for k in d.leder))
        else:
            villkor.append(lambda d, ul=ul: ul in d.lag)
    return lambda d: any(v(d) for v in villkor)


# ---- cachebygge --------------------------------------------------------------------------------

def egenskaper(s):
    """Delens egenskaper ur formen (i dess läge): snäv omslutande låda, volym, tyngdpunkt, area, solider och
    yttyper (fälten i Del utom id, namn, sökväg och färg)."""
    from OCP.BRepAdaptor import BRepAdaptor_Surface
    from OCP.BRepBndLib import BRepBndLib
    from OCP.BRepGProp import BRepGProp
    from OCP.Bnd import Bnd_Box
    from OCP.GProp import GProp_GProps
    from OCP.TopAbs import TopAbs_FACE, TopAbs_SOLID
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopoDS import TopoDS
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
    e = TopExp_Explorer(s, TopAbs_FACE)
    while e.More():
        typ = str(BRepAdaptor_Surface(TopoDS.Face(e.Current())).GetType()).split("_")[-1]
        ytor[typ] = ytor.get(typ, 0) + 1
        e.Next()
    return {"bbox": [round(v, 3) for v in (p.X(), p.Y(), p.Z(), q.X(), q.Y(), q.Z())],
            "volym": round(g.Mass(), 1), "tyngdpunkt": [round(v, 2) for v in c.Coord()],
            "area": round(a.Mass(), 1), "solider": nsol, "ytor": ytor}


def triangulera(s):
    """Triangelnät (V float64 N×3, F int64 M×3) i formens läge, utåtriktade normaler (NAT_LIN, NAT_VINKEL)."""
    from OCP.BRep import BRep_Tool
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    from OCP.TopAbs import TopAbs_FACE, TopAbs_REVERSED
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopLoc import TopLoc_Location
    from OCP.TopoDS import TopoDS
    BRepMesh_IncrementalMesh(s, NAT_LIN, False, NAT_VINKEL, True)
    vs, fs, n0 = [], [], 0
    e = TopExp_Explorer(s, TopAbs_FACE)
    while e.More():
        fa = TopoDS.Face(e.Current())
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
    return (np.concatenate(vs) if vs else np.zeros((0, 3)),
            np.concatenate(fs) if fs else np.zeros((0, 3), np.int64))


def skriv_cache(katalog, fil, rot, noder, delar, nat, former):
    """Skriv cachen: `delar` som dict med Del:s fält, `nat` (V, F) och `former` (OCP-former i världen) per del.
    Katalogen byts i ett steg (andra processer ser aldrig en halvfärdig cache)."""
    import os
    import shutil
    import tempfile
    from OCP.BinTools import BinTools, BinTools_FormatVersion
    from OCP.BRep import BRep_Builder
    from OCP.TopoDS import TopoDS_Compound
    CACHE.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix=f".{katalog.name}-", dir=katalog.parent))
    try:
        comp = TopoDS_Compound()
        bb = BRep_Builder()
        bb.MakeCompound(comp)
        for s in former:
            bb.Add(comp, s)
        BinTools.Write_s(comp, str(tmp / "former.bin"), False, False, BinTools_FormatVersion.BinTools_FormatVersion_CURRENT)
        offs, nv, nf = [], 0, 0
        for V, F in nat:
            offs.append((nv, nv + len(V), nf, nf + len(F)))
            nv += len(V); nf += len(F)
        np.savez(tmp / "nat.npz", V=np.concatenate([V for V, _ in nat]).astype(np.float32),
                 F=np.concatenate([F for _, F in nat]).astype(np.int32), offs=np.array(offs, dtype=np.int64))
        idx = {"format": FORMAT, "fil": str(fil), "hash": katalog.name.rsplit("-", 1)[1],
               "skapad": time.strftime("%Y-%m-%d %H:%M"), "rot": rot, "noder": noder, "delar": delar,
               "nat": {"lin": NAT_LIN, "vinkel": NAT_VINKEL, "trianglar": nf}}
        (tmp / "index.json").write_text(json.dumps(idx, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        if katalog.exists():
            shutil.rmtree(katalog, ignore_errors=True)
        os.rename(tmp, katalog)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)          # kvar bara om något gick fel (eller en annan process hann före)
    return nf


def _bygg_cache(fil, katalog, tyst=False):
    from OCP.IFSelect import IFSelect_ReturnStatus
    from OCP.Quantity import Quantity_Color
    from OCP.STEPCAFControl import STEPCAFControl_Reader
    from OCP.TCollection import TCollection_ExtendedString
    from OCP.TDF import TDF_Label
    from OCP.TDataStd import TDataStd_Name
    from OCP.TDocStd import TDocStd_Document
    from OCP.TopLoc import TopLoc_Location
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
            for b, n in zip(barn, unika_namn([namn(b) or "?" for b in barn])):
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

    delar, nat = [], []
    for i, (sokvag, nm, f, s) in enumerate(leaf):
        delar.append({"id": i, "sokvag": sokvag, "namn": nm, "farg": list(f), **egenskaper(s)})
        nat.append(triangulera(s))
    nf = skriv_cache(katalog, fil, rotnamn[0] if len(rotnamn) == 1 else fil.stem, noder, delar, nat,
                     [s for *_, s in leaf])
    logg(f"klar: {nf} trianglar, {time.time() - t0:.1f} s → {katalog.relative_to(HERE)}")


def unika_namn(namnen):
    """Syskonens namn i sökvägarna: ett namn som förekommer flera gånger numreras, "Regel [1]", "Regel [2]" …"""
    raknare, ut = {}, []
    for n in namnen:
        if namnen.count(n) > 1:
            raknare[n] = raknare.get(n, 0) + 1
            n = f"{n} [{raknare[n]}]"
        ut.append(n)
    return ut
