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
from .modell import Montage

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
    t = m.namn.lower()
    for a, b in (("å", "a"), ("ä", "a"), ("ö", "o")):
        t = t.replace(a, b)
    return "-".join(d for d in "".join(c if c.isalnum() else " " for c in t).split())


def _utan(m: Montage, utom: list[str], vag: str = "") -> Montage:
    """Kopia av trädet utan delar och montage vars sökväg innehåller någon av texterna."""
    ny = Montage(m.namn, m.kod, m.beskrivning)
    for i in m.barn:
        v = f"{vag}/{i.namn}" if vag else f"{m.namn}/{i.namn}"
        if any(u in v for u in utom):
            continue
        ny.lagg(_utan(i.barn, utom, v) if isinstance(i.barn, Montage) else i.barn, i.placering, i.namn)
    return ny


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
    pt = sub.add_parser("trad", help="modellträdet")
    pt.add_argument("--djup", type=int, default=4)
    pt.add_argument("--del", dest="vag")
    pb = sub.add_parser("bygg", help="bygg och exportera")
    pb.add_argument("--del", dest="vag")
    pb.add_argument("--format", default="step,glb,lista,index")
    pb.add_argument("--delade", action="store_true", help="likadana delar delar produkt i STEP")
    pb.add_argument("--ut", type=Path, default=UT)
    pk = sub.add_parser("kontroll", help="krockar, kontakter och glipor")
    pk.add_argument("--del", dest="vag")
    pk.add_argument("--ut", type=Path, default=UT)
    pr = sub.add_parser("rendera", help="rendera vyer med Blender (Cycles)")
    pr.add_argument("vyer", nargs="*", help="vyernas namn (standard: alla i trebodar.vyer)")
    pr.add_argument("--bredd", type=int, default=400)
    pr.add_argument("--sampel", type=int, default=32)
    pr.add_argument("--ut", type=Path, default=UT)
    pr.add_argument("--blender", default="/Applications/Blender.app/Contents/MacOS/Blender")
    pr.add_argument("--blend", action="store_true", help="spara scenen som modeller/trebodar/ut/trebodar.blend")
    wb = sub.add_parser("webb", help="webbvisaren (three.js) med modellen i docs/ för GitHub Pages")
    wb.add_argument("--ut", type=Path, default=ROT / "docs")
    sub.add_parser("typ", help="typkontroll (mypy) av ramverket och modellen")
    pj = sub.add_parser("jamfor", help="jämför med referensmodellen (Onshape)")
    pj.add_argument("--del", dest="vag")
    pj.add_argument("--urval", default=None, help="del av referensens sökväg, t.ex. 'Stomme prefab'")
    pj.add_argument("--ny", default=None, help="del av modellens sökväg att jämföra med")
    pj.add_argument("--ut", type=Path, default=UT)
    arg = a.parse_args(argv)

    if arg.kommando == "typ":
        import subprocess
        mapp = Path(__file__).resolve().parents[1]
        raise SystemExit(subprocess.run([sys.executable, "-m", "mypy", "--config-file", str(mapp / "mypy.ini"),
                                         "-p", "modellering", "-p", "trebodar"], cwd=mapp).returncode)
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
    elif arg.kommando == "rendera":
        import json
        import subprocess
        from .export import glb
        vyer = importlib.import_module("trebodar.vyer").VYER
        fil = arg.ut / f"{filnamn(rot)}.glb"
        glb.skriv(rot, fil, karna)
        (arg.ut / "bilder").mkdir(parents=True, exist_ok=True)
        (arg.ut / "vyer.json").write_text(json.dumps(vyer, ensure_ascii=False))
        material = {d.material.namn: d.material.renderdata() for _, d, _ in rot.platta()}
        (arg.ut / "material.json").write_text(json.dumps(material, ensure_ascii=False, indent=1))
        skript = Path(__file__).resolve().parents[1] / "blender" / "rendera.py"
        cmd = [arg.blender, "-b", "--factory-startup", "--python-exit-code", "1", "-P", str(skript), "--", str(fil),
               str(arg.ut / "material.json"), str(arg.ut / "vyer.json"), str((arg.ut / "bilder").resolve()),
               "--bredd", str(arg.bredd), "--sampel", str(arg.sampel)]
        for v in arg.vyer:
            cmd += ["--vy", v]
        if arg.blend:
            cmd += ["--blend", str((arg.ut / f"{filnamn(rot)}.blend").resolve())]
        t = time.perf_counter()
        ut = subprocess.run(cmd, capture_output=True, text=True)
        for rad in ut.stdout.splitlines():
            if rad.startswith(("RENDERAD", "SPARAD")):
                print("  " + rad)
        if ut.returncode:
            print(ut.stdout[-3000:], ut.stderr[-3000:])
        print(f"  ({time.perf_counter() - t:.0f} s)")
    elif arg.kommando == "webb":
        import json
        import shutil
        from .export import glb
        vy_mod = importlib.import_module("trebodar.vyer")
        utom = getattr(vy_mod, "WEBB_UTOM", [])
        webbrot = _utan(rot, utom)
        (arg.ut / "modell").mkdir(parents=True, exist_ok=True)
        glb.skriv(webbrot, arg.ut / "modell" / "trebodar.glb", karna)
        (arg.ut / "vyer.json").write_text(json.dumps(vy_mod.VYER, ensure_ascii=False, indent=1))
        shutil.copy(Path(__file__).resolve().parents[1] / "webb" / "index.html", arg.ut / "index.html")
        (arg.ut / ".nojekyll").write_text("")
        print(f"  {arg.ut}: index.html, vyer.json, modell/trebodar.glb "
              f"({(arg.ut / 'modell' / 'trebodar.glb').stat().st_size / 1e6:.1f} MB, utan {', '.join(utom) or '–'})")
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
              f"{len(r.skarvor)} numeriska skärvor < 5 mm³, "
              f"{len(r.glipor)} glipor, "
              f"{len(r.kontakter)} kontakter, {len(r.fria)} delar utan kontakt, {len(ogiltiga)} ogiltiga former "
              f"({r.sekunder:.1f} s) -> {fil}")
        for x, y, v in sorted(r.krockar, key=lambda q: -q[2])[:15]:
            print(f"    KROCK {x} / {y}: {v:.0f} mm³")


if __name__ == "__main__":
    main()
