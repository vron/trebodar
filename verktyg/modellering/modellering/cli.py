"""Kommandoraden: bygg, exportera och kontrollera modellen.

    mod trad [--djup N] [--del VÄG]
    mod bygg [--del VÄG] [--format step,glb,lista,index] [--delade]
    mod kontroll [--del VÄG]
"""
from __future__ import annotations

import argparse
import importlib
import sys
import time
from pathlib import Path

from .karna import ROT, Karna
from .modell import Del, Montage

MODELLMAPP = ROT / "modeller"
UT = ROT / "modeller" / "trebodar" / "ut"


def ladda(modul: str = "trebodar.trebodar") -> Montage:
    if str(MODELLMAPP) not in sys.path:
        sys.path.insert(0, str(MODELLMAPP))
    m = importlib.import_module(modul)
    rot = m.montage()
    assert isinstance(rot, Montage)
    return rot


def valj(rot: Montage, vag: str | None) -> Montage:
    if not vag:
        return rot
    x, _ = rot.hitta(vag)
    if not isinstance(x, Montage):
        raise SystemExit(f"{vag} är en del, inte ett montage")
    return x


def filnamn(m: Montage) -> str:
    t = m.namn.lower().replace(" ", "-")
    for a, b in (("å", "a"), ("ä", "a"), ("ö", "o")):
        t = t.replace(a, b)
    return t


def trad(m: Montage, djup: int, nivå: int = 0, namn: str | None = None) -> None:
    antal = m.antal_delar()
    print(f"{'  ' * nivå}▸ {namn or m.namn}  ({antal} delar){'  – ' + m.beskrivning if m.beskrivning and nivå < 3 else ''}")
    if nivå + 1 >= djup:
        return
    delar: dict[str, int] = {}
    for i in m.barn:
        if isinstance(i.barn, Montage):
            trad(i.barn, djup, nivå + 1, i.namn)
        else:
            delar[i.barn.namn] = delar.get(i.barn.namn, 0) + 1
    for n, k in delar.items():
        print(f"{'  ' * (nivå + 1)}  {k:3d} × {n}")


def main(argv: list[str] | None = None) -> None:
    a = argparse.ArgumentParser(prog="mod", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = a.add_subparsers(dest="kommando", required=True)
    t = sub.add_parser("trad", help="modellträdet")
    t.add_argument("--djup", type=int, default=4)
    t.add_argument("--del", dest="vag")
    b = sub.add_parser("bygg", help="bygg och exportera")
    b.add_argument("--del", dest="vag")
    b.add_argument("--format", default="step,glb,lista,index")
    b.add_argument("--delade", action="store_true", help="likadana delar delar produkt i STEP")
    b.add_argument("--ut", type=Path, default=UT)
    k = sub.add_parser("kontroll", help="krockar, kontakter och glipor")
    k.add_argument("--del", dest="vag")
    k.add_argument("--ut", type=Path, default=UT)
    j = sub.add_parser("jamfor", help="jämför med referensmodellen (Onshape)")
    j.add_argument("--del", dest="vag")
    j.add_argument("--urval", default=None, help="del av referensens sökväg, t.ex. 'Stomme prefab'")
    j.add_argument("--ny", default=None, help="del av modellens sökväg att jämföra med")
    j.add_argument("--ut", type=Path, default=UT)
    arg = a.parse_args(argv)

    t0 = time.perf_counter()
    rot = valj(ladda(), getattr(arg, "vag", None))
    t1 = time.perf_counter()
    if arg.kommando == "trad":
        trad(rot, arg.djup)
        return
    karna = Karna()
    karna.forbered(d.form for _, d, _ in rot.platta())
    print(f"{rot.namn}: {rot.antal_delar()} delar, modell {t1 - t0:.2f} s, former {karna.statistik['byggda']} nya "
          f"och {karna.statistik['cachade']} cachade ({karna.statistik['sekunder']:.2f} s)")
    if arg.kommando == "bygg":
        from .export import glb, lista, step
        namn = filnamn(rot)
        format_ = arg.format.split(",")
        if "step" in format_:
            t = time.perf_counter()
            step.skriv(rot, arg.ut / f"{namn}.step", karna, unika_produkter=not arg.delade)
            print(f"  STEP {arg.ut / (namn + '.step')} ({time.perf_counter() - t:.2f} s)")
        if "glb" in format_:
            t = time.perf_counter()
            glb.skriv(rot, arg.ut / f"{namn}.glb", karna)
            print(f"  GLB  {arg.ut / (namn + '.glb')} ({time.perf_counter() - t:.2f} s)")
        if "lista" in format_:
            lista.materiallista(rot, karna, arg.ut / f"{namn}-materiallista.csv", arg.ut / f"{namn}-materiallista.md")
            print(f"  materiallista {arg.ut / (namn + '-materiallista.md')}")
        if "index" in format_:
            lista.index(rot, karna, arg.ut / f"{namn}-index.json")
            print(f"  index {arg.ut / (namn + '-index.json')}")
    elif arg.kommando == "jamfor":
        from . import jamfor
        ref = importlib.import_module("trebodar.referens")
        jj = jamfor.jamfor(rot, karna, ref.FIL, ref.TRANSFORM, arg.urval, arg.ny)
        namn = filnamn(rot)
        txt = jamfor.rapport(jj, arg.ut / f"{namn}-jamforelse.md", arg.ut / f"{namn}-namntabell.csv")
        print("  " + txt.split("\n")[2])
        print(f"  -> {arg.ut / (namn + '-jamforelse.md')}, {arg.ut / (namn + '-namntabell.csv')}")
    elif arg.kommando == "kontroll":
        from . import kontroll
        try:
            regler = importlib.import_module("trebodar.kontrollregler")
            tillatna = getattr(regler, "TILLATNA_OVERLAPP", None)
        except ModuleNotFoundError:
            tillatna = None
        r = kontroll.kor(rot, karna, tillatna=tillatna)
        fil = arg.ut / f"{filnamn(rot)}-kontroll.md"
        kontroll.rapport(r, fil)
        ogiltiga = [d.namn for d in {id(d): d for _, d, _ in rot.platta()}.values()
                    if not karna.egenskaper(d.form).giltig]
        print(f"  {r.par} par ({r.nya_par} nya), {len(r.krockar)} krockar, {len(r.tillatna)} tillåtna överlapp, "
              f"{len(r.glipor)} glipor, "
              f"{len(r.kontakter)} kontakter, {len(r.fria)} delar utan kontakt, {len(ogiltiga)} ogiltiga former "
              f"({r.sekunder:.1f} s) -> {fil}")
        for x, y, v in sorted(r.krockar, key=lambda q: -q[2])[:15]:
            print(f"    KROCK {x} / {y}: {v:.0f} mm³")


if __name__ == "__main__":
    main()
