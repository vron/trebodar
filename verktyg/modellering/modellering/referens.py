"""Läs en referensmodell (STEP med sammanställningar, t.ex. Onshape-exporten) som platta instanser: sökväg,
namn, färg, form i produktens eget system och placering i världen (valfri global transform)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from OCP.IFSelect import IFSelect_RetDone
from OCP.Quantity import Quantity_Color
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TCollection import TCollection_AsciiString, TCollection_ExtendedString
from OCP.TDataStd import TDataStd_Name
from OCP.TDF import TDF_Label, TDF_Tool
from OCP.TDocStd import TDocStd_Document
from OCP.TopLoc import TopLoc_Location
from OCP.TopoDS import TopoDS_Shape
from OCP.XCAFDoc import XCAFDoc_ColorGen, XCAFDoc_ColorSurf, XCAFDoc_ColorTool, XCAFDoc_DocumentTool
from OCP.XCAFDoc import XCAFDoc_ShapeTool as ST
from OCP.collections import Sequence_TDF_Label

from .karna import placerad
from .placering import IDENTITET, Placering


@dataclass
class RefDel:
    vag: tuple[str, ...]                 # montagens namn från roten, utan delens eget namn
    namn: str                            # instansens namn (t.ex. "ÅYI [3]")
    produkt: str                         # produktens namn (t.ex. "ÅYI")
    etikett: str                         # produktens XCAF-etikett (samma för alla instanser av produkten)
    farg: str | None                     # "#rrggbb"
    form: TopoDS_Shape                   # i produktens eget system
    placering: Placering                 # produkt -> världen

    @property
    def sokvag(self) -> str:
        return "/".join(self.vag + (self.namn,))

    def varldsform(self) -> TopoDS_Shape:
        return placerad(self.form, self.placering)


def _namn(l: TDF_Label) -> str:
    a = TDataStd_Name()
    return a.Get().ToExtString() if l.FindAttribute(TDataStd_Name.GetID_s(), a) else ""


def _etikett(l: TDF_Label) -> str:
    s = TCollection_AsciiString()
    TDF_Tool.Entry_s(l, s)
    return s.ToCString()


def _farg(l: TDF_Label) -> str | None:
    c = Quantity_Color()
    for t in (XCAFDoc_ColorSurf, XCAFDoc_ColorGen):
        if XCAFDoc_ColorTool.GetColor_s(l, t, c):
            rgb = [Quantity_Color.Convert_LinearRGB_To_sRGB_s(v) for v in (c.Red(), c.Green(), c.Blue())]
            return "#" + "".join(f"{round(max(0.0, min(1.0, v)) * 255):02x}" for v in rgb)
    return None


def _plac(loc: TopLoc_Location) -> Placering:
    t = loc.Transformation()
    return Placering.fran_matris([[t.Value(i, j) for j in range(1, 5)] for i in range(1, 4)] + [[0, 0, 0, 1]])


def las(fil: Path, varld: Placering = IDENTITET) -> list[RefDel]:
    """Alla delinstanser i filen. `varld` transformerar filens globala system till det önskade."""
    doc = TDocStd_Document(TCollection_ExtendedString("XmlOcaf"))
    r = STEPCAFControl_Reader()
    r.SetColorMode(True)
    r.SetNameMode(True)
    if r.ReadFile(str(fil)) != IFSelect_RetDone:
        raise RuntimeError(f"kunde inte läsa {fil}")
    r.Transfer(doc)
    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    ut: list[RefDel] = []

    def ga(l: TDF_Label, loc: TopLoc_Location, vag: tuple[str, ...], farg: str | None) -> None:
        ref = l
        if ST.IsReference_s(l):
            ref = TDF_Label()
            ST.GetReferredShape_s(l, ref)
            loc = loc.Multiplied(ST.GetLocation_s(l))
        nm = _namn(l) or _namn(ref)
        farg = _farg(l) or farg
        if ST.IsAssembly_s(ref):
            komp = Sequence_TDF_Label()
            ST.GetComponents_s(ref, komp)
            for i in range(1, komp.Length() + 1):
                ga(komp.Value(i), loc, vag + (nm,), farg)
            return
        ut.append(RefDel(vag, nm, _namn(ref), _etikett(ref), _farg(ref) or farg, ST.GetShape_s(ref),
                         varld @ _plac(loc)))

    fria = Sequence_TDF_Label()
    st.GetFreeShapes(fria)
    for i in range(1, fria.Length() + 1):
        ga(fria.Value(i), TopLoc_Location(), (), None)
    return ut
