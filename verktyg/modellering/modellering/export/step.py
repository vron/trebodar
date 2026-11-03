"""STEP AP242 med sammanställningar, instanser, namn och färger (OCCT XCAF).

Montage blir sammanställningar och delar produkter. Med `unika_produkter` (standard) blir varje placerad del en
egen produkt med instansens namn (t.ex. "1NO-R03 Regel 45×95"), så att namnen syns i alla program (Onshape visar
produkternas namn). Annars delar likadana delar en produkt med delens namn.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

from OCP.BRepBuilderAPI import BRepBuilderAPI_Copy
from OCP.IFSelect import IFSelect_RetDone
from OCP.Interface import Interface_Static
from OCP.Quantity import Quantity_Color, Quantity_TOC_sRGB
from OCP.STEPCAFControl import STEPCAFControl_Writer
from OCP.STEPControl import STEPControl_AsIs
from OCP.TCollection import TCollection_ExtendedString
from OCP.TDataStd import TDataStd_Name
from OCP.TDF import TDF_Label
from OCP.TDocStd import TDocStd_Document
from OCP.TopLoc import TopLoc_Location
from OCP.XCAFDoc import XCAFDoc_ColorSurf, XCAFDoc_DocumentTool

from ..karna import Karna, trsf
from ..modell import Del, Montage


def _farg(h: str) -> Quantity_Color:
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return Quantity_Color(r, g, b, Quantity_TOC_sRGB)


def _namn(l: TDF_Label, n: str) -> None:
    TDataStd_Name.Set_s(l, TCollection_ExtendedString(n, True))


def produktnamn(instans: str, d: Del) -> str:
    return instans if instans == d.namn else f"{instans} {d.namn}"


def dokument(rot: Montage, karna: Karna, unika_produkter: bool = True) -> TDocStd_Document:
    doc = TDocStd_Document(TCollection_ExtendedString("XmlOcaf"))
    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    ct = XCAFDoc_DocumentTool.ColorTool_s(doc.Main())
    delade: dict[int, TDF_Label] = {}
    montage: dict[int, TDF_Label] = {}

    def produkt(d: Del, instans: str) -> TDF_Label:
        if not unika_produkter and id(d) in delade:
            return delade[id(d)]
        s = karna.form(d.form)
        if unika_produkter:
            s = BRepBuilderAPI_Copy(s, True, False).Shape()
        l = st.AddShape(s, False, False)
        _namn(l, produktnamn(instans, d) if unika_produkter else d.namn)
        ct.SetColor(l, _farg(d.material.cad_farg), XCAFDoc_ColorSurf)
        delade[id(d)] = l
        return l

    def sammanstallning(m: Montage) -> TDF_Label:
        if id(m) in montage:
            return montage[id(m)]
        l = st.NewShape()
        _namn(l, m.namn)
        for i in m.barn:
            barn = sammanstallning(i.barn) if isinstance(i.barn, Montage) else produkt(i.barn, i.namn)
            c = st.AddComponent(l, barn, TopLoc_Location(trsf(i.placering)))
            _namn(c, i.namn)
        montage[id(m)] = l
        return l

    sammanstallning(rot)
    st.UpdateAssemblies()
    return doc


def _tyst() -> None:
    """OCCT:s statistik vid skrivning till stdout stängs av."""
    from OCP.Message import Message, Message_Gravity
    p = Message.DefaultMessenger_s().Printers()
    for i in range(1, p.Length() + 1):
        p.Value(i).SetTraceLevel(Message_Gravity.Message_Fail)


def skriv(rot: Montage, fil: Path, karna: Karna, unika_produkter: bool = True) -> None:
    karna.forbered(d.form for _, d, _ in rot.platta())
    _tyst()
    doc = dokument(rot, karna, unika_produkter)
    Interface_Static.SetCVal_s("write.step.schema", "AP242DIS")
    Interface_Static.SetCVal_s("write.step.unit", "MM")
    Interface_Static.SetCVal_s("write.step.product.name", rot.namn)
    w = STEPCAFControl_Writer()
    # inga 2D-kurvor på ytorna (läsarna räknar fram dem), efter att skrivaren har registrerat inställningen
    Interface_Static.SetIVal_s("write.surfacecurve.mode", 0)
    w.SetColorMode(True)
    w.SetNameMode(True)
    w.Transfer(doc, STEPControl_AsIs)
    fil.parent.mkdir(parents=True, exist_ok=True)
    tmp = fil.with_name(f".{fil.name}.{os.getpid()}")      # bytes i ett steg: läsare ser aldrig en halv fil
    try:
        if w.Write(str(tmp)) != IFSelect_RetDone:
            raise RuntimeError(f"kunde inte skriva {fil}")
        _ascii(tmp)
        os.replace(tmp, fil)
    finally:
        tmp.unlink(missing_ok=True)


def _ascii(fil: Path) -> None:
    """ISO 10303-21 tillåter bara ASCII: övriga tecken skrivs \\X\\hh (Latin-1) eller \\X2\\hhhh\\X0\\."""
    data = fil.read_bytes()
    if data.isascii():
        return

    def kod(m: re.Match[bytes]) -> bytes:              # en följd av UTF-8-kodade tecken
        return "".join(f"\\X\\{o:02X}" if o < 256 else f"\\X2\\{o:04X}\\X0\\"
                       for o in map(ord, m.group().decode("utf-8"))).encode("ascii")
    fil.write_bytes(re.sub(rb"[\x80-\xff]+", kod, data))
