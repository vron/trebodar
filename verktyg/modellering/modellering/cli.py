"""Kommandoraden: bygg, exportera och kontrollera modellen.

    mod trad [--djup N] [--del VÄG]
    mod bygg [--del VÄG] [--format step,glb,lista,index] [--delade]
    mod kontroll [--del VÄG]
    mod onshape [--del VÄG] [--dokument NAMN] [--mapp NAMN] [--publik]
"""
from __future__ import annotations

import argparse
import importlib
import math
import re
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


def _norr() -> tuple[float, float]:
    """Norr i modellens x och y (x mot platsens azimut_x, y 90° moturs)."""
    az = math.radians(importlib.import_module("trebodar.skelett").PLATS.azimut_x)
    return math.cos(az), math.cos(az - math.pi / 2)


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


def _blender(rot: Montage, karna: Karna, vyer: dict[str, dict], kvalitet: str, bredd: int | None, ut: Path,
             blender: str, blend: bool, natter: dict[str, dict] | None = None) -> None:
    """Modellens GLB och scenens beskrivning (vyerna med dagsljus och tända grupper, ljusportalerna, lamporna,
    omgivningen, armaturerna, materialen och natthimlen per tid, natthimmel.natt) och Blender (blender/rendera.py) i
    bakgrunden."""
    import json
    import subprocess
    from . import dagsljus
    from .export import glb
    vy_mod = importlib.import_module("trebodar.vyer")
    plats = importlib.import_module("trebodar.skelett").PLATS
    fil = UT / f"{filnamn(rot)}-rendering.glb"
    glb.skriv(_utan(rot, getattr(vy_mod, "RENDER_UTOM", [])), fil, karna)
    ut.mkdir(parents=True, exist_ok=True)
    scen = {"glb": str(fil), "ut": str(ut.resolve()), "kvalitet": kvalitet, "bredd": bredd,
            "hojd_m": plats.hojd, "portaler": vy_mod.portaler() if hasattr(vy_mod, "portaler") else [],
            "lampor": {k: {**g, "farg": dagsljus.svartkropp(float(g["kelvin"]))}
                       for k, g in getattr(vy_mod, "LAMPOR", {}).items()},
            "omgivning": getattr(vy_mod, "OMGIVNING", None),
            "geodata": (str(ROT / vy_mod.GEODATA["mapp"]) if hasattr(vy_mod, "GEODATA")
                        and (ROT / vy_mod.GEODATA["mapp"] / "omgivning.json").exists() else None),
            "tillgangar": (str(ROT / vy_mod.GEODATA["tillgangar"]) if "tillgangar" in getattr(vy_mod, "GEODATA", {})
                           and (ROT / vy_mod.GEODATA["tillgangar"]).is_dir() else None),
            "armaturer": _armaturer(),
            "material": {d.material.namn: d.material.renderdata() for _, d, _ in rot.platta()}, "vyer": vyer,
            "natter": natter or {},
            "blend": str((UT / f"{filnamn(rot)}.blend").resolve()) if blend else None}
    scenfil = UT / "scen.json"
    scenfil.write_text(json.dumps(scen, ensure_ascii=False, indent=1))
    skript = Path(__file__).resolve().parents[1] / "blender" / "rendera.py"
    cmd = [blender, "-b", "--factory-startup", "--python-exit-code", "1", "-P", str(skript), "--", str(scenfil)]
    t = time.perf_counter()
    svar = subprocess.run(cmd, capture_output=True, text=True)
    for rad in svar.stdout.splitlines():
        if rad.startswith(("RENDERAD", "SPARAD", "LJUS", "VITBALANS", "MATYTA")):
            print("  " + rad)
    if svar.returncode:
        print(svar.stdout[-4000:], svar.stderr[-3000:])
        raise SystemExit("Blender misslyckades")
    print(f"  ({time.perf_counter() - t:.0f} s)")


def _armaturer() -> list[dict[str, object]]:
    """Elinstallationens armaturer för renderingen (modellens el, om den finns): linsens läge, ljusets riktning,
    tändgruppen, färgen och ljusfördelningen (IES ur tillverkarens fotometrifil i lokalt/el/, annars en stråle med
    databladets strålvinkel). Pendlarna: ljuskällan i armaturen ("kalla", lika åt alla håll, eller en stråle för en
    armatur med strålvinkel), med flödet genom glas som omsluter den (transmissionen), och glasets luminans
    ("luminans", flödet genom glaset fördelat på dess yta, cd/m²)."""
    from . import dagsljus, fotometri
    try:
        inst = importlib.import_module("trebodar.hus.installationer.el.installation").installation()
    except ModuleNotFoundError:
        return []
    u = inst.utdrag()
    ut: list[dict[str, object]] = []
    fordelningar: dict[str, fotometri.Fordelning] = {}
    for pid, p in u["punkter"].items():
        if p["slag"] != "lampa":
            continue
        t = u["typer"][p["typ"]]
        if "linje" in p:                      # ljuslinje: diffusorns yta som ett lambertskt arealjus
            lj, tl = p["linje"], t["linje"]
            yta = tl["lysande"] * tl["diffusor"] * 1e-6
            ut.append({"id": pid, "typ": p["typ"], "tand": p["tand"], "lins": p["lins"], "riktning": p["riktning"],
                       "punkt": p["punkt"], "normal": p["normal"],
                       "linje": {"a": lj["a"], "b": lj["b"], "bredd": tl["diffusor"]}, "lumen": t["ljusflode"],
                       "farg": dagsljus.svartkropp(float(t["fargtemperatur"])),
                       "luminans": t["ljusflode"] / (math.pi * yta)})
            continue
        pe = t.get("pendel")
        if pe:
            flode = t["ljusflode"] * pe["transmission"]
            if p["typ"] not in fordelningar:
                fordelningar[p["typ"]] = (fotometri.spot(t["stralvinkel"], flode, t["namn"]) if t["stralvinkel"]
                                          else fotometri.jamn(flode, t["namn"], pe["kalla_d"]))
            f = fordelningar[p["typ"]]
            ut.append({"id": pid, "typ": p["typ"], "tand": p["tand"], "lins": p["lins"], "kalla": p["lins"],
                       "kalla_d": pe["kalla_d"], "riktning": p["riktning"], "punkt": p["punkt"],
                       "normal": p["normal"], "ies": f.ies(),
                       "farg": dagsljus.svartkropp(float(t["fargtemperatur"])), "lysande_d": t["lysande_d"],
                       "max_cd": float(f.cd.max()),
                       "luminans": t["ljusflode"] * pe["lysande_andel"] * pe["transmission"]
                       / (math.pi * pe["lysande_yta"] * 1e-6)})
            continue
        if p["typ"] not in fordelningar:
            ldt = ROT / "lokalt" / "el" / t["fotometri"]
            fordelningar[p["typ"]] = (fotometri.las_ldt(ldt).skalad(t["ljusflode"]) if ldt.exists() else
                                      fotometri.spot(t["stralvinkel"], t["ljusflode"], t["namn"]))
            if not ldt.exists():
                print(f"  {p['typ']}: fotometrifilen saknas ({ldt}), stråle {t['stralvinkel']:g}° (./mod el hamta)")
        f = fordelningar[p["typ"]]
        ut.append({"id": pid, "typ": p["typ"], "tand": p["tand"], "lins": p["lins"], "riktning": p["riktning"],
                   "punkt": p["punkt"], "normal": p["normal"], "ies": f.ies(),
                   "farg": dagsljus.svartkropp(float(t["fargtemperatur"])),
                   "lysande_d": t["lysande_d"], "max_cd": float(f.cd.max())})
    return ut


def main(argv: list[str] | None = None) -> None:
    a = argparse.ArgumentParser(prog="mod", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = a.add_subparsers(dest="kommando", required=True)
    pt = sub.add_parser("trad", help="modellträdet")
    pt.add_argument("--djup", type=int, default=4)
    pt.add_argument("--del", dest="vag")
    pb = sub.add_parser("bygg", help="bygg och exportera")
    pb.add_argument("--del", dest="vag")
    pb.add_argument("--format", default="step,glb,lista,index",
                    help="step, glb, lista, index; analys: bara modellanalysens cache (utan STEP-fil)")
    pb.add_argument("--delade", action="store_true", help="likadana delar delar produkt i STEP")
    pb.add_argument("--ut", type=Path, default=UT)
    pk = sub.add_parser("kontroll", help="krockar, kontakter och glipor")
    pk.add_argument("--del", dest="vag")
    pk.add_argument("--ut", type=Path, default=UT)
    pr = sub.add_parser("rendera", help="rendera vyer med Blender (Cycles)")
    pr.add_argument("vyer", nargs="*", help="vyernas namn eller början av dem, t.ex. I01 (standard: serien)")
    pr.add_argument("--serie", choices=("ute", "inne", "alla"), default="ute",
                    help="ute: VYER, inne: inomhusbilderna I01–I30 (trebodar.vyer)")
    pr.add_argument("--kvalitet", choices=("skiss", "utkast", "normal", "slutlig"), default="skiss",
                    help="skiss 640 px, utkast 1280, normal 1920, slutlig 2048 (2K)")
    pr.add_argument("--ljus", nargs=4, metavar=("MANAD", "DAG", "KLOCKA", "VADER"),
                    help="dagsljuset för alla vyerna, t.ex. 6 21 18:00 sol (annars vyns)")
    pr.add_argument("--ljusserie", help="ljusserien (trebodar.vyer.LJUSSERIER): samma tid och väder för alla vyerna "
                                        "och tändgrupperna, t.ex. B (annars vyns ljus, serien A)")
    pr.add_argument("--ev", type=float, help="exponering EV100 (annars automatisk ur en förhandsbild)")
    pr.add_argument("--bredd", type=int, help="bredd i pixlar (annars kvalitetens)")
    pr.add_argument("--ut", type=Path, default=UT / "bilder")
    pr.add_argument("--blender", default="/Applications/Blender.app/Contents/MacOS/Blender")
    pr.add_argument("--blend", action="store_true", help="spara scenen som modeller/trebodar/ut/trebodar.blend")
    pr.add_argument("--tand", nargs="*", default=[], metavar="GRUPP[=NIVÅ]",
                    help="tänd elinstallationens tändgrupper, t.ex. AL-T1 AL-T2=0.5 (dimrad till hälften)")
    wb = sub.add_parser("webb", help="webbvisaren (three.js) med modellen i docs/modell/ för GitHub Pages")
    wb.add_argument("--ut", type=Path, default=ROT / "docs")
    sub.add_parser("typ", help="typkontroll (mypy) av ramverket och modellen")
    po = sub.add_parser("onshape", help="ladda upp modellen (STEP) till ett nytt dokument i Onshape")
    po.add_argument("--del", dest="vag")
    po.add_argument("--dokument", help="dokumentets namn (standard: montaget, datum och git-version)")
    po.add_argument("--mapp", help="mappen på översta nivån i Onshape (standard: nyckelfilens eller TrebodarAuto)")
    po.add_argument("--delade", action="store_true", help="likadana delar delar produkt i STEP")
    po.add_argument("--publik", action="store_true", help="publikt dokument (krävs för Onshapes gratiskonton)")
    po.add_argument("--ut", type=Path, default=UT)
    pl = sub.add_parser("ljus", help="dagsljuset: solens läge, ljusets färg och styrka (dagsljus.py)")
    pl.add_argument("manad", type=int)
    pl.add_argument("dag", type=int)
    pl.add_argument("klocka", nargs="?", help="HH:MM lokal tid (utan: hela dagen)")
    pl.add_argument("vader", nargs="?", default="sol", help="sol, lätt mulet, mulet (sunny, slightlyovercast, overcast)")
    pl.add_argument("--steg", type=int, default=30, help="minuter mellan raderna för hela dagen")
    pl.add_argument("--diagram", type=Path, help="solens bana under året med fasadernas riktningar (png)")
    pp = sub.add_parser("ljusplan", help="belysningsstyrkan [lux] på mätytorna (el/matytor.py), som planritningar")
    pp.add_argument("ytor", nargs="*", help="mätytorna i MATYTOR (standard: plan1-golv)")
    pp.add_argument("--tand", nargs="*", default=None, metavar="GRUPP[=NIVÅ]",
                    help="tändgrupperna som är tända (standard: alla, och vyernas taklampor i LAMPOR, t.ex. kallare, "
                         "som tänds hela), t.ex. AL-T1 KO-T1=0.5")
    pp.add_argument("--ljus", nargs=4, default=["12", "21", "22:00", "mulet"], metavar=("MANAD", "DAG", "KLOCKA", "VADER"),
                    help="dagsljuset (standard: mörkt, 21 dec kl. 22), t.ex. 3 20 12:00 mulet")
    pp.add_argument("--kvalitet", choices=("skiss", "utkast", "normal", "slutlig"), default="utkast",
                    help="antal sampel (utkast räcker oftast)")
    pp.add_argument("--direkt", action="store_true", help="bara det direkta ljuset, utan reflexer i rummet")
    pp.add_argument("--nummer", default="U-04", help="handlingens nummer (bladen <nummer>.n efter mätytan)")
    pp.add_argument("--projekt", type=Path, help="indata.toml med [projekt]: bladens revision och datum (standard: "
                                                 "preliminära, utan revision)")
    pp.add_argument("--ut", type=Path, default=UT / "ljusplan")
    pp.add_argument("--blender", default="/Applications/Blender.app/Contents/MacOS/Blender")
    pe = sub.add_parser("el", help="elinstallationen: kontroll, listor, ritningar och tillverkarnas fotometrifiler")
    pe.add_argument("atgard", choices=("kontroll", "lista", "ritning", "hamta"),
                    help="kontroll: referenser, styrning, armaturernas vinkel, djup och läkt, rörens böjar; "
                         "lista: punkter, tändgrupper och rör (markdown); ritning: elplan och bjälklagets rör; "
                         "hamta: ladda ner fotometrifilerna som saknas i lokalt/el/")
    pe.add_argument("--ut", type=Path, default=UT / "el")
    pv = sub.add_parser("ventilation", help="ventilationen: kontroll (med krockar mot huset), lista och ritningar")
    pv.add_argument("atgard", choices=("kontroll", "lista", "ritning"),
                    help="kontroll: kedjorna, flödena, genomföringarna och krockarna mot husets delar; lista: grenar, "
                         "element, kanaler och genomföringar (markdown); ritning: planerna och sektionen (V-01)")
    pv.add_argument("--ut", type=Path, default=UT / "ventilation")
    pg = sub.add_parser("gjutning", help="arbetsritningarna för gjutningen av plattorna (AR-03, AR-04, #86)")
    pg.add_argument("atgard", choices=("ritning",))
    pg.add_argument("--ut", type=Path, default=ROT / "ritningar")
    pw = sub.add_parser("vatten", help="tappvattnet: kontroll (med krockar mot huset), lista och ritningar")
    pw.add_argument("atgard", choices=("kontroll", "lista", "ritning"),
                    help="kontroll: utgångarna, anslutningarna, tiden till varmvatten, hastigheterna, rören som går i "
                         "varandra, genomföringarna och krockarna mot husets delar och de andra installationerna; "
                         "lista: tappställen, rör och genomföringar (markdown); ritning: rören i mellanbjälklaget och "
                         "teknikrummet (VS-01)")
    pw.add_argument("--ut", type=Path, default=UT / "vatten")
    pg = sub.add_parser("golvvarme", help="golvvärmen: kontroll (med krockar mot huset), lista och ritningar")
    pg.add_argument("atgard", choices=("kontroll", "lista", "ritning"),
                    help="kontroll: slingornas längd, fördelarna, rören som går i varandra eller mot järnen i sin "
                         "nivå, genomföringarna och krockarna mot husets delar och de andra installationerna; lista: "
                         "kretsar och genomföringar (markdown); ritning: plan 1 och källaren med fördelarna (VG-01)")
    pg.add_argument("--ut", type=Path, default=UT / "golvvarme")
    pb = sub.add_parser("kollektor", help="köldbärarledningarna: kontroll (med krockar mot huset)")
    pb.add_argument("atgard", choices=("kontroll",),
                    help="kontroll: böjarna, genomföringarna och krockarna mot husets delar och de andra installationerna")
    pa = sub.add_parser("brandlarm", help="brandlarmet: kontroll (med krockar mot huset), lista och ritningar")
    pa.add_argument("atgard", choices=("kontroll", "lista", "ritning"),
                    help="kontroll: sammankopplingen, varnarnas placering, genomföringarna och krockarna mot husets "
                         "delar och de andra installationerna; lista: varnare, dosor, kablar och "
                         "genomföringar (markdown); ritning: plan 1 och källaren (B-01)")
    pa.add_argument("--ut", type=Path, default=UT / "brandlarm")
    pd = sub.add_parser("dranering", help="dräneringen och dagvattnet: kontroll (med krockar mot huset), lista och "
                                          "ritning")
    pd.add_argument("atgard", choices=("kontroll", "lista", "ritning"),
                    help="kontroll: fallet, höjderna vid brunnen, brunnarnas djup och krockarna mot husets delar och "
                         "de andra installationerna (inte marken); lista: ledningar och brunnar med höjderna "
                         "(markdown); ritning: planen med höjderna (D-01)")
    pd.add_argument("--ut", type=Path, default=UT / "dranering")
    pv = sub.add_parser("avlopp", help="avloppet: kontroll (med krockar mot huset), lista och ritning")
    pv.add_argument("atgard", choices=("kontroll", "lista", "ritning"),
                    help="kontroll: fallet, att ledningarna går under bjälklaget och ansluter ovanför vattengången, "
                         "den fria höjden, hålen i bjälklaget nära rören och krockarna mot husets delar (lådorna och "
                         "stommen är fel) och de andra installationerna; lista: ledningarna (markdown); ritning: "
                         "källarens plan med ledningarna och höjderna (VS-02)")
    pv.add_argument("--ut", type=Path, default=UT / "avlopp")
    pb = sub.add_parser("barverk", help="bärverket ur modellen (stommens delar och lastytorna) för K-04:s balkmodell")
    pb.add_argument("--ut", type=Path, default=UT / "barverk.json")
    pi = sub.add_parser("inkop", help="specialprodukterna i modellen mot inköpslistan (IN-01): kontroll och utdrag")
    pi.add_argument("atgard", choices=("kontroll", "utdrag"),
                    help="kontroll: koderna i modellen (produkt=) mot inköpslistan och tvärtom (ingår i kontroll); "
                         "utdrag: dessutom produkternas instanser i modellen (json) till IN-01")
    pi.add_argument("--ut", type=Path, default=UT / "inkop.json")
    pv = sub.add_parser("vagar", help="installationernas vägar: rören, kablarna och kanalerna dolda i skikten, inte "
                                      "fritt i rummen eller i fickdörrarnas fickor, och armaturernas avstånd till "
                                      "brännbart i ljusets riktning (kontrollregler, ingår i kontroll)")
    pv.add_argument("--trad", default=None, help="bara delträdet, t.ex. Hus/Installationer/El")
    sub.add_parser("ytor", help="ytskiktens språng och springor: gipsen och kaklet jämna där skivorna möts i samma plan "
                                "(kontrollregler, ingår i kontroll)")
    pk = sub.add_parser("kameraplan", help="ritningen över inomhusbildernas kameror (kräver STEP-filen, ./mod bygg)")
    pk.add_argument("--ut", type=Path, default=ROT / "renderingar" / "kameraplan.pdf")
    pk.add_argument("--webb", type=Path, default=ROT / "docs" / "renderingar",
                    help="sidan med renderingarna på planerna (index.html och plan.json)")
    pp = sub.add_parser("publicera", help="publicera de renderade bilderna på webbplatsen (releasen bilder på GitHub)")
    pp.add_argument("vyer", nargs="*", help="vyernas namn eller början av dem (standard: alla renderade)")
    pp.add_argument("--fran", type=Path, nargs="+",
                    help="mapparna med bilderna (png och sidodata, ./mod rendera; standard: renderingar/inne och ute "
                         "och ljusseriernas renderingar/B/inne … )")
    pp.add_argument("--lokalt", action="store_true",
                    help="bara till docs/renderingar/bilder, utan att ladda upp eller bygga om webbplatsen")
    pp.add_argument("--webb", type=Path, default=ROT / "docs" / "renderingar")
    pm = sub.add_parser("materialprov", help="ett material på skåpluckor, bänkskiva och brädor (Blender)")
    pm.add_argument("material", help="materialets namn i modellen, t.ex. Ask")
    pm.add_argument("--param", nargs="*", default=[], help="ändrade parametrar, t.ex. yta=lack lamell=y")
    pm.add_argument("--bredd", type=int, default=1600)
    pm.add_argument("--sampel", type=int, default=128)
    pm.add_argument("--nara", action="store_true", help="en lucka på nära håll")
    pm.add_argument("--ut", type=Path, default=UT / "bilder")
    pm.add_argument("--blender", default="/Applications/Blender.app/Contents/MacOS/Blender")
    pg = sub.add_parser("omgivning", help="omgivningen ur öppna geodata (OpenStreetMap, höjdmodell) för renderingen")
    pg.add_argument("--hamta", action="store_true",
                    help="ladda ner det som saknas (Overpass API, Terrarium-rutor, Poly Havens tillgångar)")
    pa = sub.add_parser("avtryck", help="spara modellens fingeravtryck eller jämför med det (oförändrad geometri)")
    pa.add_argument("atgard", choices=("spara", "jamfor"))
    pa.add_argument("--del", dest="vag")
    pa.add_argument("--fil", type=Path, default=None, help="standard: modeller/trebodar/ut/<modell>-avtryck.json")
    pj = sub.add_parser("jamfor", help="jämför med referensmodellen (Onshape)")
    pj.add_argument("--del", dest="vag")
    pj.add_argument("--urval", default=None, help="del av referensens sökväg, t.ex. 'Stomme prefab'")
    pj.add_argument("--ny", default=None, help="del av modellens sökväg att jämföra med")
    pj.add_argument("--ut", type=Path, default=UT)
    arg = a.parse_args(argv)

    if arg.kommando == "typ":
        import subprocess
        from .struktur import kontrollera
        mapp = Path(__file__).resolve().parents[1]
        kod = subprocess.run([sys.executable, "-m", "mypy", "--config-file", str(mapp / "mypy.ini"),
                              "-p", "modellering", "-p", "trebodar"], cwd=mapp).returncode
        if str(MODELLMAPP) not in sys.path:
            sys.path.insert(0, str(MODELLMAPP))
        lager = getattr(importlib.import_module("trebodar.kontrollregler"), "LAGER", None)
        fel = kontrollera(MODELLMAPP / "trebodar", "trebodar", lager)
        print("\n".join(fel) if fel else "Strukturen: inga importcykler, privata namn, importer i funktioner eller brott mot "
              "lagerordningen.")
        raise SystemExit(kod or (1 if fel else 0))
    if arg.kommando == "ljus":
        from . import dagsljus as dl
        if str(MODELLMAPP) not in sys.path:
            sys.path.insert(0, str(MODELLMAPP))
        plats = importlib.import_module("trebodar.skelett").PLATS
        vader = arg.vader
        if arg.klocka and not arg.klocka[:1].isdigit():
            vader, arg.klocka = arg.klocka, None
        if arg.klocka:
            print(dl.beskrivning(dl.dagsljus(arg.manad, arg.dag, arg.klocka, vader, plats)))
        else:
            print(dl.tabell(dl.dygn(arg.manad, arg.dag, vader, plats, arg.steg)))
        if arg.diagram:
            ax = plats.azimut_x
            dl.soldiagram(plats, str(arg.diagram), {"NV-fasaderna": ax, "SV-gavlarna": ax - 90,
                                                    "SO-fasaderna": ax + 180, "NO-gavlarna": ax + 90})
            print(f"  {arg.diagram}")
        return
    if arg.kommando == "el":
        import json
        import urllib.request
        from . import elritning
        from .planritning import snitt
        if str(MODELLMAPP) not in sys.path:
            sys.path.insert(0, str(MODELLMAPP))
        inst = importlib.import_module("trebodar.hus.installationer.el.installation").installation()
        utdrag = inst.utdrag()
        fel, anm = inst.kontroll()
        arg.ut.mkdir(parents=True, exist_ok=True)
        if arg.atgard == "kontroll":
            from . import installationer
            # krockarna: rören i bjälklagen och källaren mot järnen och de andra installationerna (fel); genom
            # skikten och stommen på plan 1 går de utan håltagning i modellen (räknas)
            rot_ = valj(ladda(), None)
            karna_ = Karna()
            karna_.forbered(d.form for _, d, _ in rot_.platta())
            kr = installationer.krockar(rot_, karna_, importlib.import_module("trebodar.kontrollregler"),
                                        "Hus/Installationer/El")
            # köksfläktens skorstenskåpa är en ihålig plåtkåpa (modellerad massiv): fläktens uttag sitter inne i den
            kapan = [k for k in kr.installationer if "-SKORSTEN" in k]
            fel += [f"krock med {k}" for k in kr.installationer + kr.armering if k not in kapan]
            anm += [f"inne i köksfläktens skorstenskåpa: {k.split(' mot ')[0]}" for k in kapan]
            print(f"  {len(inst.punkter)} punkter, {len(inst.tandgrupper)} tändgrupper, {len(inst.ror)} rör: "
                  f"{len(fel)} fel, {len(anm)} anmärkningar; genom stommen {len(kr.stomme)}, genom skikten "
                  f"{len(kr.skikt)} rör")
            for f in fel:
                print(f"    FEL {f}")
            for a in anm:
                print(f"    {a}")
            if fel:
                raise SystemExit(1)
        elif arg.atgard == "lista":
            fil = arg.ut / "elinstallation.md"
            fil.write_text(elritning.lista(utdrag, (fel, anm)), encoding="utf-8")
            (arg.ut / "elinstallation.json").write_text(json.dumps(utdrag, ensure_ascii=False, indent=1))
            print(f"  {fil}")
        elif arg.atgard == "ritning":
            step_fil = UT / "trebodar.step"
            if not step_fil.exists():
                raise SystemExit(f"{step_fil} saknas: bygg STEP-filen först (./mod bygg)")
            ma = ROT / "verktyg" / "modellanalys" / "ma"
            plan1 = snitt(ma, step_fil, 1200.0, UT / "el-plan1.json")
            mb = snitt(ma, step_fil, -75.0, UT / "el-mellanbjalklag.json")
            kallare = snitt(ma, step_fil, importlib.import_module("trebodar.skelett").Z_BOTTENPLATTA + 1200.0,
                            UT / "el-kallare.json")
            print(f"  {elritning.ritningar(utdrag, plan1, mb, kallare, _norr(), UT / 'el' / 'blad', arg.ut)}")
        else:
            for t in {v["typ"]: utdrag["typer"][v["typ"]] for v in utdrag["punkter"].values()
                      if v["slag"] == "lampa"}.values():
                fil = ROT / "lokalt" / "el" / str(t["fotometri"])
                if fil.exists():
                    print(f"  finns: {fil}")
                    continue
                fil.parent.mkdir(parents=True, exist_ok=True)
                with urllib.request.urlopen(str(t["fotometri_url"]), timeout=60) as svar:
                    fil.write_bytes(svar.read())
                print(f"  hämtad: {fil} ({fil.stat().st_size} byte)")
        return
    if arg.kommando == "kameraplan":
        from modellering import kameraplan
        if str(MODELLMAPP) not in sys.path:
            sys.path.insert(0, str(MODELLMAPP))
        vy_mod = importlib.import_module("trebodar.vyer")
        skel = importlib.import_module("trebodar.skelett")
        step_fil = UT / "trebodar.step"
        if not step_fil.exists():
            raise SystemExit(f"{step_fil} saknas: bygg STEP-filen först (./mod bygg)")
        ma = ROT / "verktyg" / "modellanalys" / "ma"
        plan1 = kameraplan.snitt(ma, step_fil, 1200.0, UT / "kameraplan-plan1.json")
        kallare = kameraplan.snitt(ma, step_fil, skel.Z_BOTTENPLATTA + 1200.0, UT / "kameraplan-kallare.json")
        kameraplan.rita(plan1, kallare, vy_mod.INNE, vy_mod.RUMSNAMN, list(skel.TRAPPHAL), _norr(), arg.ut,
                        UT / "kameraplan")
        print(f"  {arg.ut}")
        from modellering import renderingar
        sida = renderingar.webb(plan1, kallare, vy_mod.VYER, vy_mod.INNE, vy_mod.RUMSNAMN, list(skel.TRAPPHAL), _norr(),
                                arg.webb, getattr(vy_mod, "TEXTER", {}), getattr(vy_mod, "TEKNIK", set()))
        print(f"  {sida}")
        return
    if arg.kommando == "publicera":
        from modellering import renderingar
        if str(MODELLMAPP) not in sys.path:
            sys.path.insert(0, str(MODELLMAPP))
        vy_mod = importlib.import_module("trebodar.vyer")
        fran = arg.fran or [ROT / "renderingar" / s / d for s in ("", *[k for k in getattr(vy_mod, "LJUSSERIER", {})
                                                                        if k != "A"]) for d in ("inne", "ute")]
        renderingar.publicera(fran, arg.vyer, arg.webb, {*vy_mod.VYER, *vy_mod.INNE}, arg.lokalt)
        return
    if arg.kommando == "materialprov":
        import json
        import subprocess
        if str(MODELLMAPP) not in sys.path:
            sys.path.insert(0, str(MODELLMAPP))
        mat_mod = importlib.import_module("trebodar.material")
        mat = next((v for v in vars(mat_mod).values() if getattr(v, "namn", None) == arg.material), None)
        if mat is None:
            raise SystemExit(f"materialet {arg.material} finns inte i trebodar.material")
        p = mat.renderdata()
        for kv in arg.param:
            k, _, v = kv.partition("=")
            try:
                p[k] = float(v)
            except ValueError:
                p[k] = v
        arg.ut.mkdir(parents=True, exist_ok=True)
        ut = arg.ut / f"materialprov-{arg.material}{'-nara' if arg.nara else ''}.png"
        prov = UT / "materialprov.json"
        prov.write_text(json.dumps({"namn": mat.namn, "parametrar": p, "ut": str(ut.resolve()), "bredd": arg.bredd,
                                    "sampel": arg.sampel, "nara": arg.nara}, ensure_ascii=False))
        skript = Path(__file__).resolve().parents[1] / "blender" / "materialprov.py"
        blender = subprocess.run([arg.blender, "-b", "--factory-startup", "--python-exit-code", "1", "-P", str(skript),
                                  "--", str(prov)], capture_output=True, text=True)
        print("\n".join(x for x in blender.stdout.splitlines() if x.startswith("RENDERAD"))
              or blender.stdout[-3000:] + blender.stderr[-2000:])
        return
    if arg.kommando == "omgivning":
        import numpy as np
        from . import geodata
        if str(MODELLMAPP) not in sys.path:
            sys.path.insert(0, str(MODELLMAPP))
        vy_mod = importlib.import_module("trebodar.vyer")
        plats = importlib.import_module("trebodar.skelett").PLATS
        cfg = vy_mod.GEODATA
        passning, fel = vy_mod.sweref_passning()
        mitt = vy_mod.OMGIVNING["mitt"]
        lat, lon = geodata.wgs84(*passning.till_sweref(np.array([mitt[0]]), np.array([mitt[1]])))
        print(f"  modellens mitt {lat[0]:.5f} N {lon[0]:.5f} O (passningen mot SWEREF: restfel {fel:.1f} mm)")
        mapp = ROT / cfg["mapp"]
        if arg.hamta:
            geodata.hamta(float(lat[0]), float(lon[0]), cfg["radie"] + 300.0, str(mapp))
            if "tillgangar" in cfg:
                from . import polyhaven
                nya = polyhaven.hamta(str(ROT / cfg["tillgangar"]))
                print(f"  Poly Haven: {', '.join(nya) if nya else 'inget nytt'} -> {ROT / cfg['tillgangar']}")
            from . import natthimmel
            nya = natthimmel.hamta()
            print(f"  natthimlen: {', '.join(nya) if nya else 'inget nytt'} -> {natthimmel.MAPP}")
        besk = geodata.bygg(str(mapp), passning, (mitt[0], mitt[1]), cfg["radie"], cfg["cell"], plats.hojd)
        print(f"  {besk['n']}×{besk['n']} celler à {besk['cell']} m, {len(besk['byggnader'])} byggnader -> {mapp}")
        terr = ROT / cfg.get("terrang", "lokalt/terrang")
        if (terr / "hojd").is_dir():
            from . import terrang
            S = importlib.import_module("trebodar.skelett")
            from shapely.geometry import Polygon
            fasad = list(Polygon(S.KONTUR).buffer(95.0, join_style=2).exterior.coords)
            st = terrang.bygg(str(mapp), str(terr), passning, plats.hojd, fasad, cfg.get("byggnader", ()),
                              cfg.get("skog", ()), cfg.get("utan_trad", ()), cfg.get("nya_trad", ()),
                              cfg.get("baddar", ()), cfg.get("buskar", ()))
            na = st["nara"]
            print(f"  Lantmäteriets höjder ur {terr}; tomten {na['nx']}×{na['ny']} celler à {na['cell']} m, "
                  f"{st['uteslutna']} markpunkter avviker mer än {terrang.RATT_MAX} m och räknas inte")
            print("  inmätta punkter mot Lantmäteriet (median avvikelse, median |avvikelse| före och efter rättningen):")
            for k, (antal, med, fore, efter, mark) in st["punkter"].items():
                print(f"    {k:8s} {antal:4d}  {med:+.3f}  {fore:.3f} → {efter:.3f} m" + ("" if mark else "  (föremål)"))
        return
    t0 = time.perf_counter()
    rot = valj(ladda(), getattr(arg, "vag", None))
    t1 = time.perf_counter()
    if arg.kommando == "trad":
        trad(rot, arg.djup)
        return
    if arg.kommando == "barverk":
        import json
        if str(MODELLMAPP) not in sys.path:
            sys.path.insert(0, str(MODELLMAPP))
        utdrag = importlib.import_module("trebodar.hus.stomme.barverk").utdrag(rot)
        arg.ut.parent.mkdir(parents=True, exist_ok=True)
        arg.ut.write_text(json.dumps(utdrag, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        print(f"  {len(utdrag['delar'])} delar, {len(utdrag['takytor'])} takfall, {len(utdrag['vaggar'])} väggar "
              f"-> {arg.ut}")
        return
    if arg.kommando == "inkop":
        import json
        from . import inkop
        lista = importlib.import_module("trebodar.kontrollregler").INKOPSLISTA
        inst, fel = inkop.kontroll(rot, lista)
        print(f"{rot.namn}: {sum(map(len, inst.values()))} instanser av {len(inst)} specialprodukter i modellen, "
              f"{len(fel)} fel mot inköpslistan ({lista.relative_to(ROT)})")
        for f in fel:
            print(f"    FEL {f}")
        if fel:
            raise SystemExit(1)
        if arg.atgard == "utdrag":
            arg.ut.parent.mkdir(parents=True, exist_ok=True)
            arg.ut.write_text(json.dumps(inst, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"  -> {arg.ut}")
        return
    karna = Karna()
    karna.forbered(d.form for _, d, _ in rot.platta())
    print(f"{rot.namn}: {rot.antal_delar()} delar, modell {t1 - t0:.2f} s, former {karna.statistik['byggda']} nya "
          f"och {karna.statistik['cachade']} cachade ({karna.statistik['sekunder']:.2f} s)")
    if arg.kommando == "avtryck":
        from . import avtryck
        fil = arg.fil or UT / f"{filnamn(rot)}-avtryck.json"
        if arg.atgard == "spara":
            print(f"  {avtryck.spara(rot, karna, fil)} delar -> {fil}")
            return
        jf = avtryck.jamfor(rot, karna, fil)
        print(f"  {jf.antal[0]} -> {jf.antal[1]} delar: {len(jf.borta)} borta, {len(jf.nya)} nya, {len(jf.andrade)} ändrade, "
              f"{len(jf.flyttade)} flyttade i trädet, {len(jf.omdopta)} med nytt delnamn")
        for rubrik, lista_ in (("borta", jf.borta), ("nya", jf.nya), ("ändrade", jf.andrade)):
            for sokvag in lista_[:20]:
                print(f"    {rubrik}: {sokvag}")
            if len(lista_) > 20:
                print(f"    … och {len(lista_) - 20} till")
        for fran, till in jf.flyttade[:20]:
            print(f"    flyttad: {fran} -> {till}")
        for sokvag, fore, efter in jf.omdopta[:20]:
            print(f"    nytt delnamn: {sokvag}: {fore} -> {efter}")
        print("  Geometrin är oförändrad." if jf.lika else "  Geometrin har ändrats.")
        raise SystemExit(0 if jf.lika else 1)
    if arg.kommando == "bygg":
        from .export import glb, lista, step
        namn = filnamn(rot)
        format_ = arg.format.split(",")
        if "step" in format_:
            from .export import analys
            t = time.perf_counter()
            step.skriv(rot, arg.ut / f"{namn}.step", karna, unika_produkter=not arg.delade)
            print(f"  STEP {arg.ut / (namn + '.step')} ({time.perf_counter() - t:.2f} s)")
            if not arg.delade:                       # modellanalysens cache för STEP-filen (sökvägarna som i den)
                katalog, n, tid_ = analys.skriv(rot, karna, arg.ut / f"{namn}.step")
                print(f"  modellanalysens cache {katalog.name} ({n} nya, {tid_:.2f} s)")
        elif "analys" in format_:                    # bara modellanalysens cache, utan STEP-fil
            from .export import analys
            katalog, n, tid_ = analys.skriv(rot, karna, arg.ut / f"{namn}.step", med_step=False)
            print(f"  modellanalysens cache {katalog.name} ({n} nya, {tid_:.2f} s)")
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
        from . import dagsljus
        vy_mod = importlib.import_module("trebodar.vyer")
        plats = importlib.import_module("trebodar.skelett").PLATS
        alla = {**vy_mod.VYER, **getattr(vy_mod, "INNE", {})}
        if arg.vyer:
            valda = {n: v for n, v in alla.items() if any(n == x or n.startswith(x) for x in arg.vyer)}
        else:
            valda = {"ute": vy_mod.VYER, "inne": getattr(vy_mod, "INNE", {}), "alla": alla}[arg.serie]
        from . import renderingar
        serier = getattr(vy_mod, "LJUSSERIER", {"A": {}})
        if arg.ljusserie and arg.ljusserie not in serier:
            raise SystemExit(f"okänd ljusserie {arg.ljusserie} (finns: {', '.join(serier)})")
        serie = serier.get(arg.ljusserie or "A", {})
        valda = {n: v for n, v in valda.items() if not any(n.startswith(x) for x in serie.get("utan", ()))}
        if not valda:
            raise SystemExit(f"inga vyer: {' '.join(arg.vyer)}")
        serie_tand: dict[str, float] = {}
        if serie.get("tand") == "alla":
            inst = importlib.import_module("trebodar.hus.installationer.el.installation").installation()
            serie_tand = {g: 1.0 for g in inst.tandgrupper}
        from . import natthimmel, polyhaven
        tillgangar = (str(ROT / vy_mod.GEODATA["tillgangar"]) if "tillgangar" in getattr(vy_mod, "GEODATA", {})
                      else None)
        vyer, vyljus, natter = {}, {}, {}
        tand = {g: float(n) if n else 1.0 for g, _, n in (x.partition("=") for x in arg.tand)}
        for namn, v in valda.items():
            m, d, k, w = arg.ljus or serie.get("ljus") or v["ljus"]
            vyljus[namn] = [int(m), int(d), k, w]
            lj = dagsljus.dagsljus(int(m), int(d), k, w, plats)
            if lj.tid not in natter:
                natter[lj.tid] = natthimmel.natt(natthimmel.tidpunkt(lj.tid), plats)
            vyer[namn] = {**v, "ljus": lj.som_dict(), "ev": arg.ev, "natt": lj.tid if natter[lj.tid] else None,
                          "himmel": polyhaven.himmel(tillgangar, lj.vader, lj.sol_hojd) if tillgangar else None,
                          "tand": {**dict(v.get("tand", {})), **serie_tand, **tand}}
        start = time.time()
        try:
            _blender(rot, karna, vyer, arg.kvalitet, arg.bredd, arg.ut, arg.blender, arg.blend,
                     {t: n for t, n in natter.items() if n})
        finally:                       # även när Blender stannar efter några bilder
            renderingar.sidodata(arg.ut, valda, vyljus, arg.kvalitet, start, arg.ljusserie or "A")
    elif arg.kommando == "ljusplan":
        import json
        import numpy as np
        from . import dagsljus, ljusplan
        import tomllib
        from .planritning import kompilera, snitt, sv
        if str(MODELLMAPP) not in sys.path:
            sys.path.insert(0, str(MODELLMAPP))
        vy_mod = importlib.import_module("trebodar.vyer")
        skel = importlib.import_module("trebodar.skelett")
        mat_mod = importlib.import_module("trebodar.hus.installationer.el.matytor")
        ytor = mat_mod.MATYTOR
        inst = importlib.import_module("trebodar.hus.installationer.el.installation").installation()
        utdrag = inst.utdrag()
        okanda = [y for y in arg.ytor if y not in ytor]
        if okanda:
            raise SystemExit(f"okända mätytor: {', '.join(okanda)} (finns: {', '.join(ytor)})")
        # tändgrupperna och vyernas taklampor (LAMPOR, källaren), som tänds hela
        paneler = getattr(vy_mod, "LAMPOR", {})
        tand = ({g: float(n) if n else 1.0 for g, _, n in (x.partition("=") for x in arg.tand)}
                if arg.tand is not None else {g: 1.0 for g in [*utdrag["tandgrupper"], *paneler]})
        okanda = [g for g in tand if g not in utdrag["tandgrupper"] and g not in paneler]
        if okanda:
            raise SystemExit(f"okända tändgrupper: {', '.join(okanda)} (finns: "
                             f"{', '.join([*utdrag['tandgrupper'], *paneler])})")
        lampor = [g for g in paneler if tand.get(g, 0.0) > 0]
        tand = {g: n for g, n in tand.items() if g not in paneler}
        m, d, k, w = arg.ljus
        ljus = dagsljus.dagsljus(int(m), int(d), k, w, skel.PLATS)
        golv = {1: 0.0, 0: skel.Z_BOTTENPLATTA}
        vyer = {}
        for namn in arg.ytor or ["plan1-golv"]:
            y = ytor[namn]
            vyer[f"ljusplan-{namn}"] = {"matyta": {"namn": y.namn, "omrade": list(y.omrade), "cell": y.cell,
                                                    "z": golv[y.plan] + max(y.hojd, 2.0), "direkt": arg.direkt,
                                                    "upphojda": [[*z.omrade, golv[y.plan] + z.hojd] for z in y.zoner
                                                                 if z.hojd is not None and z.hojd != y.hojd]},
                                       "ljus": ljus.som_dict(), "tand": tand, "lampor": lampor, "inne": True}
        arg.ut.mkdir(parents=True, exist_ok=True)
        _blender(rot, karna, vyer, arg.kvalitet, None, arg.ut, arg.blender, False)
        step_fil = UT / "trebodar.step"
        if not step_fil.exists():
            raise SystemExit(f"{step_fil} saknas: bygg STEP-filen först (./mod bygg)")
        ma = ROT / "verktyg" / "modellanalys" / "ma"
        tid = ljus.tid[:16].replace("T", " kl. ")
        tanda = [f"{g} {utdrag['tandgrupper'][g]['namn']}" + (f" ({sv(100 * n)} %)" if n < 1 else "")
                 for g, n in tand.items() if n > 0]
        tanda += [f"taklamporna {g} ({len(paneler[g]['lagen'])} LED-paneler {sv(paneler[g]['sida'])} × "
                  f"{sv(paneler[g]['sida'])} mm, {sv(paneler[g]['lumen'])} lm och {sv(paneler[g]['kelvin'])} K)"
                  for g in lampor]
        scenario = [("Tända: " + "; ".join(tanda) + "." if tanda else "Inga armaturer tända."),
                    (f"Dagsljuset {tid}, {ljus.vader}: {sv(ljus.global_lux / 1000, 1)} klx ute (vågrätt)."
                     if ljus.global_lux > 1.0 else f"Inget dagsljus ({tid}).")
                    + (" Bara det direkta ljuset, utan reflexer." if arg.direkt else "")]
        huvud = {}
        if arg.projekt:
            pr = tomllib.loads(arg.projekt.read_text(encoding="utf-8"))["projekt"]
            huvud = {"rev": pr["revision"], "datum": pr["datum"], "status": "UTREDNING"}
        bladen = []
        for namn in arg.ytor or ["plan1-golv"]:
            y = ytor[namn]
            bas = arg.ut / f"ljusplan-{namn}"
            lux = np.load(str(bas) + ".npy")
            delar = snitt(ma, step_fil, golv[y.plan] + 1200.0, UT / f"ljusplan-{y.plan}.json")
            rum = {k: v for k, v in {**vy_mod.RUMSNAMN, **getattr(vy_mod, "LJUSPLANENS_RUM", {})}.items()
                   if (len(v[1]) > 2 and v[1][2] == "k") == (y.plan == 0)}
            hinder = ljusplan.inredningen([snitt(ma, step_fil, golv[y.plan] + h, UT / f"ljusplan-{namn}-{h:g}.json",
                                                 ",".join(ljusplan.INREDNING)) for h in mat_mod.INREDNING_SNITT
                                           if max(y.hojd, 2.0) <= h <= y.hojd + mat_mod.INREDNING_OVER])
            nr = f"{arg.nummer}.{list(ytor).index(namn) + 1}"
            b, stat = ljusplan.rita(lux, y, delar, utdrag, rum, scenario, _norr(), nr, UT / "ljusplan" / "blad",
                                    [(px, py, g["sida"]) for g in paneler.values() if (g["z"] < 0) == (y.plan == 0)
                                     for px, py in g["lagen"]], hinder, **huvud)
            bladen.append((nr, b))
            (bas.parent / (bas.name + "-statistik.json")).write_text(json.dumps(stat, ensure_ascii=False, indent=1))
            print(f"  {nr} {y.namn}")
            for s_ in stat:
                print(f"    {s_['namn']}: medel {s_['medel']:.0f} lux, minst {s_['minst']:.0f}, störst {s_['storst']:.0f}, "
                      f"jämnhet {s_['jamnhet']:.2f}")
        pdf = arg.ut / f"{arg.nummer}_ljusplaner.pdf"
        kompilera(bladen, UT / "ljusplan" / "blad", pdf)
        print(f"  {pdf}")
    elif arg.kommando == "onshape":
        import datetime
        import subprocess
        from . import onshape
        from .export import step
        fil = arg.ut / f"{filnamn(rot)}.step"
        step.skriv(rot, fil, karna, unika_produkter=not arg.delade)

        def montage(m: Montage) -> int:
            return sum(1 + montage(i.barn) for i in m.barn if isinstance(i.barn, Montage))
        if (n := montage(rot) + 1) > onshape.MAX_SAMMANSTALLNINGAR:
            print(f"  OBS: {n} montage; Onshape behåller högst {onshape.MAX_SAMMANSTALLNINGAR} sammanställningar per "
                  f"import och slår ihop de djupaste nivåerna. Ladda upp delträd (--del) för hela strukturen.")
        git = subprocess.run(["git", "-C", str(ROT), "describe", "--always", "--dirty=*"], capture_output=True,
                             text=True).stdout.strip()
        namn = arg.dokument or f"{rot.namn} {datetime.date.today().isoformat()} {git}".strip()
        print(f"  STEP {fil} ({fil.stat().st_size / 1e6:.1f} MB), laddar upp som \"{namn}\" …")
        t = time.perf_counter()
        adress, k, did, wid = onshape.ladda_upp(fil, namn, arg.mapp, f"{rot.beskrivning} (git {git})", arg.publik)
        flikar = k.flikar(did, wid)
        typer: dict[str, int] = {}
        for f in flikar:
            typer[f["elementType"]] = typer.get(f["elementType"], 0) + 1
        print(f"  importerad på {time.perf_counter() - t:.0f} s: {', '.join(f'{n} {t_}' for t_, n in typer.items())}, "
              f"{len(k.delar(did, wid))} delar\n  {adress}")
    elif arg.kommando == "webb":
        import json
        import shutil
        from .export import glb
        vy_mod = importlib.import_module("trebodar.vyer")
        utom = getattr(vy_mod, "WEBB_UTOM", [])
        webbrot = _utan(rot, utom)
        mapp = arg.ut / "modell"
        mapp.mkdir(parents=True, exist_ok=True)
        glb.skriv(webbrot, mapp / "trebodar.glb", karna)
        (mapp / "vyer.json").write_text(json.dumps(vy_mod.VYER, ensure_ascii=False, indent=1))
        shutil.copy(Path(__file__).resolve().parents[1] / "webb" / "index.html", mapp / "index.html")
        (arg.ut / ".nojekyll").write_text("")
        print(f"  {mapp}: index.html, vyer.json, trebodar.glb "
              f"({(mapp / 'trebodar.glb').stat().st_size / 1e6:.1f} MB, utan {', '.join(utom) or '–'})")
    elif arg.kommando == "jamfor":
        from . import jamfor
        ref = importlib.import_module("trebodar.referens")
        jj = jamfor.jamfor(rot, karna, ref.FIL, ref.TRANSFORM, arg.urval, arg.ny)
        namn = filnamn(rot)
        txt = jamfor.rapport(jj, arg.ut / f"{namn}-jamforelse.md", arg.ut / f"{namn}-namntabell.csv")
        print("  " + txt.split("\n")[2])
        print(f"  -> {arg.ut / (namn + '-jamforelse.md')}, {arg.ut / (namn + '-namntabell.csv')}")
    elif arg.kommando == "ventilation":
        import json
        from . import installationer, ventritning
        from .planritning import snitt
        regler = importlib.import_module("trebodar.kontrollregler")
        vent = importlib.import_module("trebodar.hus.installationer.ventilation.system").ventilation()
        utdrag = vent.utdrag()
        fel, anm = vent.kontroll()
        arg.ut.mkdir(parents=True, exist_ok=True)
        if arg.atgard in ("kontroll", "lista"):
            kr = installationer.krockar(rot, karna, regler, "Hus/Installationer/Ventilation")
            # köksfläktens skorstenskåpa är en ihålig plåtkåpa (modellerad massiv), med fläktens uttag inne i den
            kapan = [k for k in kr.installationer if k.startswith("FF1-D1-SKORSTEN") and "/El/" in k]
            fel += [f"krock med {k}" for k in kr.installationer if k not in kapan]
            anm += [f"elen inne i köksfläktens skorstenskåpa: {k.split('/')[-1].split(' ')[0]}" for k in kapan]
            krockar = kr.stomme + kr.armering + kr.skikt
        if arg.atgard == "kontroll":
            n_el, n_gf = len(utdrag["element"]), len(utdrag["genomforingar"])  # type: ignore[arg-type]
            print(f"  {len(vent.grenar)} grenar, {n_el} element, {n_gf} genomföringar: {len(fel)} fel, "
                  f"{len(anm)} anmärkningar")
            for f in fel:
                print(f"    FEL {f}")
            for x in anm:
                print(f"    {x}")
            print("  krockar mot husets delar (stommen var för sig):")
            for k in krockar:
                print(f"    {k}")
            if fel:
                raise SystemExit(1)
        elif arg.atgard == "lista":
            fil = arg.ut / "ventilation.md"
            fil.write_text(ventritning.lista(utdrag, (fel, anm), krockar), encoding="utf-8")
            (arg.ut / "ventilation.json").write_text(json.dumps(utdrag, ensure_ascii=False, indent=1))
            print(f"  {fil}")
        else:
            step_fil = UT / "trebodar.step"
            if not step_fil.exists():
                raise SystemExit(f"{step_fil} saknas: bygg STEP-filen först (./mod bygg)")
            ma = ROT / "verktyg" / "modellanalys" / "ma"
            skel = importlib.import_module("trebodar.skelett")
            plan1 = snitt(ma, step_fil, 1200.0, UT / "ventilation-plan1.json")
            kallare = snitt(ma, step_fil, skel.Z_BOTTENPLATTA + 1200.0, UT / "ventilation-kallare.json")
            sektioner = {(g, y): snitt(ma, step_fil, f"y={y:g}", UT / f"ventilation-sektion-{g}.json")
                         for g, y in ventritning.sektioner(utdrag)}
            pdf = ventritning.ritningar(utdrag, plan1, kallare, sektioner, _norr(), UT / "ventilation" / "blad", arg.ut)
            print(f"  {pdf}")
    elif arg.kommando == "gjutning":
        from . import gjutning
        from .planritning import snitt
        imp = importlib.import_module
        skel = imp("trebodar.skelett")
        el = imp("trebodar.hus.installationer.el.installation").installation()
        vat = imp("trebodar.hus.installationer.vatten.system").vatten()
        av = imp("trebodar.hus.installationer.avlopp.ledningar")
        gv = imp("trebodar.hus.installationer.golvvarme.system").golvvarme()
        vent = imp("trebodar.hus.installationer.ventilation.system").ventilation()
        bl = imp("trebodar.hus.installationer.brandlarm.larm")
        kol = imp("trebodar.hus.installationer.kollektor.ledningar")
        genomf = [*vat.genomforingar()[0], *gv.genomforingar()[0], *vent.genomforingar()[0],
                  *bl.genomforingarna()[0], *kol.genomforingarna()[0]]
        hal: dict[str, list[dict]] = {
            k: [{"punkt": list(g.punkt), "atgard": g.atgard, "matt": g.matt, "element": g.element}
                for g in genomf if g.del_ == del_ and not g.atgard.startswith("ingjutet, ut ur")]
            for k, del_ in (("MB", "Mellanbjälklaget"), ("BP", "Bottenplattan"))}
        avu = av.utdrag()
        for nyckel, (z_uk, z_ok) in (("MB", gjutning.MB), ("BP", gjutning.BP)):
            for k, led in avu["ledningar"].items():         # avloppets rör lodrätt genom plattan
                for a, b in zip(led["vag"], led["vag"][1:]):
                    if (abs(a[0] - b[0]) < 1.0 and abs(a[1] - b[1]) < 1.0 and min(a[2], b[2]) < z_ok - 1.0
                            and max(a[2], b[2]) > z_uk + 1.0 and max(a[2], b[2]) > z_ok - 1.0):
                        hal[nyckel].append({"punkt": [a[0], a[1], z_ok], "matt": f"Ø{led['d']:g}", "element": k,
                                            "atgard": f"{led['namn']}: " + ("röret läggs före gjutningen och gjuts in"
                                                                            if nyckel == "BP" else
                                                                            "hål eller hylsa för röret")})
                        break
            hal[nyckel] += [{"punkt": [*g["punkt"], z_ok], "atgard": "golvbrunnens kropp gjuts in, flänsen i överkant",
                             "matt": f"Ø{g['d']:g}", "element": k} for k, g in avu["golvbrunnar"].items()
                            if z_uk - 1.0 < g["golv"] < z_ok + 1.0]
        step_fil = UT / "trebodar.step"
        if not step_fil.exists():
            raise SystemExit(f"{step_fil} saknas: bygg STEP-filen först (./mod bygg)")
        ma = ROT / "verktyg" / "modellanalys" / "ma"
        snitt_ = {"plan1": snitt(ma, step_fil, 1200.0, UT / "gjutning-plan1.json"),
                  "kallare": snitt(ma, step_fil, skel.Z_BOTTENPLATTA + 1200.0, UT / "gjutning-kallare.json"),
                  "mb": snitt(ma, step_fil, -75.0, UT / "gjutning-mellanbjalklag.json"),
                  "bp": snitt(ma, step_fil, skel.Z_BOTTENPLATTA - 50.0, UT / "gjutning-bottenplattan.json")}
        arg.ut.mkdir(parents=True, exist_ok=True)
        tk = imp("trebodar.hus.installationer.teknikrum")
        arm = imp("trebodar.hus.armering.armering")
        pel = imp("trebodar.hus.grund.pelare")
        box_ = imp("shapely.geometry").box
        omr = [box_(o[0], o[2], o[1], o[3]) for o in gjutning.DETALJER]
        jarn = [{"linje": [list(g.coords[0])] if g.geom_type == "Point" else [list(c) for c in g.coords], "d": d}
                for g, d in arm.jarnen_i_nivan(-150.0, -51.0) if any(g.intersects(o) for o in omr)]
        gc = tk.GRUPPCENTRAL
        central = {"topp": list(gc.anslutningar["topp"]), "matt": [gc.matt[0], gc.matt[1]], "vagg": gc.lage.punkt[1],
                   "kanal": [2810.0 - 62.5, 8936.0 - 62.5, 4950.0, 8936.0 + 62.5]}
        lc = tk.DRIVDONSSKAP
        skap = {"topp": list(lc.anslutningar["topp"]), "matt": [lc.matt[0], lc.matt[1]], "vagg": lc.lage.punkt[1]}
        plattor: dict[str, list[dict]] = {"MB": [], "BP": []}
        fot = pel.fotplat_mitt()
        for k, (x, y) in pel.PELARE.items():
            n = pel.ANTAL.get(k, 1)
            for i in range(n):
                plattor["MB"].append({"namn": f"topplåt {k}" + (f"-{i + 1}" if n > 1 else ""),
                                      "mitt": [x + i * pel.VKR, y], "matt": [pel.VKR, pel.VKR],
                                      "text": f"{pel.VKR:g}×{pel.VKR:g}×{pel.TOPP_T:g}"})
            b, d = pel.plater(n)
            plattor["BP"].append({"namn": f"fotplåt {k}", "mitt": list(fot[k]), "matt": [b, d],
                                  "text": f"{b:g}×{d:g}×{pel.FOT_T:g}"})
        pdf, fel, anm = gjutning.ritningar(el.utdrag(), vat.utdrag(), avu, gv.utdrag(), hal,
                                           [list(p) for p in skel.TRAPPHAL], plattor, snitt_, _norr(),
                                           UT / "gjutning", arg.ut, jarn, central, skap)
        for p in pdf:
            print(f"  {p.relative_to(ROT)}")
        for t in anm:
            print(f"  anmärkning: {t}")
        for t in fel:
            print(f"  fel: {t}")
        if fel:
            raise SystemExit(f"{len(fel)} fel i arbetsritningarnas punkter mot modellen")
    elif arg.kommando == "vatten":
        import json
        from . import installationer, vattenritning
        from .planritning import snitt
        regler = importlib.import_module("trebodar.kontrollregler")
        vat = importlib.import_module("trebodar.hus.installationer.vatten.system").vatten()
        utdrag = vat.utdrag()
        fel, anm = vat.kontroll()
        arg.ut.mkdir(parents=True, exist_ok=True)
        if arg.atgard in ("kontroll", "lista"):
            kr = installationer.krockar(rot, karna, regler, "Hus/Installationer/Vatten")
            fel += [f"krock med {k}" for k in kr.installationer + kr.armering]
            fel += [f"krock med {k}" for k in kr.inredning if "-LADA" in k or "-SKENA" in k]   # fria från lådorna
            krockar = kr.stomme + kr.skikt
        if arg.atgard == "kontroll":
            n_gf = len(utdrag["genomforingar"])  # type: ignore[arg-type]
            print(f"  {len(vat.tappstallen)} tappställen, {len(vat.ror)} rör, {n_gf} genomföringar: {len(fel)} fel, "
                  f"{len(anm)} anmärkningar")
            for f in fel:
                print(f"    FEL {f}")
            for x in anm:
                print(f"    {x}")
            print("  krockar mot husets delar (stommen var för sig):")
            for k in krockar:
                print(f"    {k}")
            if fel:
                raise SystemExit(1)
        elif arg.atgard == "lista":
            fil = arg.ut / "vatten.md"
            fil.write_text(vattenritning.lista(utdrag, (fel, anm), krockar), encoding="utf-8")
            (arg.ut / "vatten.json").write_text(json.dumps(utdrag, ensure_ascii=False, indent=1))
            print(f"  {fil}")
        else:
            step_fil = UT / "trebodar.step"
            if not step_fil.exists():
                raise SystemExit(f"{step_fil} saknas: bygg STEP-filen först (./mod bygg)")
            ma = ROT / "verktyg" / "modellanalys" / "ma"
            skel = importlib.import_module("trebodar.skelett")
            plan1 = snitt(ma, step_fil, 1200.0, UT / "vatten-plan1.json")
            kallare = snitt(ma, step_fil, skel.Z_BOTTENPLATTA + 1200.0, UT / "vatten-kallare.json")
            mb = snitt(ma, step_fil, -75.0, UT / "vatten-mellanbjalklag.json")
            vyn = snitt(ma, step_fil, f"x={vattenritning.X_VY:g}", UT / "vatten-vy.json")
            vent = importlib.import_module("trebodar.hus.installationer.ventilation.system").ventilation().utdrag()
            pdf = vattenritning.ritningar(utdrag, plan1, kallare, mb, vyn, vent, _norr(), UT / "vatten" / "blad",
                                          arg.ut)
            print(f"  {pdf}")
    elif arg.kommando == "golvvarme":
        import json
        from . import golvvarmeritning, installationer
        from .planritning import snitt
        regler = importlib.import_module("trebodar.kontrollregler")
        gs = importlib.import_module("trebodar.hus.installationer.golvvarme.system")
        gv = gs.golvvarme()
        utdrag = gv.utdrag()
        fel, anm = gs.kontroll(gv)
        arg.ut.mkdir(parents=True, exist_ok=True)
        if arg.atgard in ("kontroll", "lista"):
            kr = installationer.krockar(rot, karna, regler, "Hus/Installationer/Golvvärme")
            fel += [f"krock med {k}" for k in kr.installationer + kr.armering]
            krockar = kr.stomme + kr.skikt
        if arg.atgard == "kontroll":
            n_gf = len(utdrag["genomforingar"])  # type: ignore[arg-type]
            print(f"  {len(gv.kretsar)} kretsar, {len(gv.fordelare)} fördelare, {n_gf} genomföringar: {len(fel)} fel, "
                  f"{len(anm)} anmärkningar")
            for f in fel:
                print(f"    FEL {f}")
            for x in anm:
                print(f"    {x}")
            print("  krockar mot husets delar (stommen var för sig):")
            for k in krockar:
                print(f"    {k}")
            if fel:
                raise SystemExit(1)
        elif arg.atgard == "lista":
            fil = arg.ut / "golvvarme.md"
            fil.write_text(golvvarmeritning.lista(utdrag, (fel, anm), krockar), encoding="utf-8")
            (arg.ut / "golvvarme.json").write_text(json.dumps(utdrag, ensure_ascii=False, indent=1))
            print(f"  {fil}")
        else:
            step_fil = UT / "trebodar.step"
            if not step_fil.exists():
                raise SystemExit(f"{step_fil} saknas: bygg STEP-filen först (./mod bygg)")
            ma = ROT / "verktyg" / "modellanalys" / "ma"
            skel = importlib.import_module("trebodar.skelett")
            plan1 = snitt(ma, step_fil, 1200.0, UT / "vatten-plan1.json")
            kallare = snitt(ma, step_fil, skel.Z_BOTTENPLATTA + 1200.0, UT / "vatten-kallare.json")
            mb = snitt(ma, step_fil, -75.0, UT / "vatten-mellanbjalklag.json")
            vyn = snitt(ma, step_fil, f"y={golvvarmeritning.Y_VY:g}", UT / "golvvarme-vy.json")
            kbl = importlib.import_module("trebodar.hus.installationer.kollektor.ledningar")
            kb = kbl.utdrag()
            x_kb = next(iter(kbl.ledningar().values())).vag[0][0]
            sek = snitt(ma, step_fil, f"x={x_kb:g}", UT / "golvvarme-kollektor.json")
            pdf = golvvarmeritning.ritningar(utdrag, plan1, kallare, mb, vyn, _norr(), UT / "golvvarme" / "blad",
                                             arg.ut, kb, sek)
            print(f"  {pdf}")
    elif arg.kommando == "brandlarm":
        import json
        from . import brandlarmritning, installationer
        from .planritning import snitt
        regler = importlib.import_module("trebodar.kontrollregler")
        bl = importlib.import_module("trebodar.hus.installationer.brandlarm.larm")
        utdrag = bl.utdrag()
        fel, anm = bl.kontroll()
        arg.ut.mkdir(parents=True, exist_ok=True)
        if arg.atgard in ("kontroll", "lista"):
            kr = installationer.krockar(rot, karna, regler, "Hus/Installationer/Brandlarm")
            fel += [f"krock med {k}" for k in kr.installationer + kr.armering]
            krockar = kr.stomme + kr.skikt
        if arg.atgard == "kontroll":
            print(f"  {len(utdrag['varnare'])} brandvarnare, {len(utdrag['dosor'])} dosor, "
                  f"{len(utdrag['kablar'])} kablar, {len(utdrag['genomforingar'])} genomföringar: {len(fel)} fel, "
                  f"{len(anm)} anmärkningar")
            for f in fel:
                print(f"    FEL {f}")
            for x in anm:
                print(f"    {x}")
            print("  krockar mot husets delar (stommen var för sig):")
            for k in krockar:
                print(f"    {k}")
            if fel:
                raise SystemExit(1)
        elif arg.atgard == "lista":
            fil = arg.ut / "brandlarm.md"
            fil.write_text(brandlarmritning.lista(utdrag, (fel, anm), krockar), encoding="utf-8")
            (arg.ut / "brandlarm.json").write_text(json.dumps(utdrag, ensure_ascii=False, indent=1))
            print(f"  {fil}")
        else:
            step_fil = UT / "trebodar.step"
            if not step_fil.exists():
                raise SystemExit(f"{step_fil} saknas: bygg STEP-filen först (./mod bygg)")
            ma = ROT / "verktyg" / "modellanalys" / "ma"
            skel = importlib.import_module("trebodar.skelett")
            plan1 = snitt(ma, step_fil, 1200.0, UT / "brandlarm-plan1.json")
            kallare = snitt(ma, step_fil, skel.Z_BOTTENPLATTA + 1200.0, UT / "brandlarm-kallare.json")
            pdf = brandlarmritning.ritningar(utdrag, plan1, kallare, _norr(), UT / "brandlarm" / "blad", arg.ut)
            print(f"  {pdf}")
    elif arg.kommando == "dranering":
        import json
        from . import draneringsritning, installationer
        from .planritning import snitt
        regler = importlib.import_module("trebodar.kontrollregler")
        dr = importlib.import_module("trebodar.hus.installationer.dranering.ledningar")
        utdrag = dr.utdrag()
        fel, anm = dr.kontroll()
        arg.ut.mkdir(parents=True, exist_ok=True)
        if arg.atgard in ("kontroll", "lista"):
            kr = installationer.krockar(rot, karna, regler, "Hus/Installationer/Dränering")
            fel += [f"krock med {k}" for k in kr.installationer + kr.armering + kr.stomme]
            krockar = [k for k in kr.skikt if not draneringsritning.bara_mark(k, utdrag["genom_sten"])]
            berg = sorted({re.sub(r"-\d\d$", "", k.split(":")[0]) for k in kr.skikt if " Berg " in k + " "})
            if berg:
                anm.append("i berget (schakt i berg): " + ", ".join(berg))
        if arg.atgard == "kontroll":
            print(f"  {len(utdrag['ledningar'])} ledningar, {len(utdrag['brunnar'])} brunnar: {len(fel)} fel, "
                  f"{len(anm)} anmärkningar")
            for f in fel:
                print(f"    FEL {f}")
            for x in anm:
                print(f"    {x}")
            print("  krockar mot husets delar (utom marken):")
            for k in krockar:
                print(f"    {k}")
            if fel or krockar:
                raise SystemExit(1)
        elif arg.atgard == "lista":
            fil = arg.ut / "dranering.md"
            fil.write_text(draneringsritning.lista(utdrag, (fel, anm), krockar), encoding="utf-8")
            (arg.ut / "dranering.json").write_text(json.dumps(utdrag, ensure_ascii=False, indent=1))
            print(f"  {fil}")
        else:
            step_fil = UT / "trebodar.step"
            if not step_fil.exists():
                raise SystemExit(f"{step_fil} saknas: bygg STEP-filen först (./mod bygg)")
            ma = ROT / "verktyg" / "modellanalys" / "ma"
            plan1 = snitt(ma, step_fil, 1200.0, UT / "dranering-plan1.json")
            pdf = draneringsritning.ritningar(utdrag, plan1, _norr(), UT / "dranering" / "blad", arg.ut)
            print(f"  {pdf}")
    elif arg.kommando == "avlopp":
        import json
        from . import installationer
        regler = importlib.import_module("trebodar.kontrollregler")
        av = importlib.import_module("trebodar.hus.installationer.avlopp.ledningar")
        utdrag = av.utdrag()
        fel, anm = av.kontroll()
        kr = installationer.krockar(rot, karna, regler, "Hus/Installationer/Avlopp")
        # samlingsledningen ansluter till stammen (Onshape-modellens, VVS); järnen läggs om runt hålen i bjälklaget
        # ledningarna i väggarnas regelfack (luftningen, tvätten) går lodrätt genom syll och hammarband (urtas); allt
        # annat i stommen är fel
        urtag = [k for k in kr.stomme if k.split("-")[0] in av.I_VAGGEN and re.search(r"-[SH]\d+ \(", k)]
        fel += [f"krock med {k}" for k in kr.installationer + kr.stomme if k not in urtag]
        fel += [f"krock med {k}" for k in kr.inredning if "-LADA" in k]        # vattenlåsen går fria från lådorna
        if urtag:
            anm.append("syll och hammarband urtas för ledningarna i väggarna: " + ", ".join(sorted(
                {k.split(" mot ")[1].split("/")[-1].split(" ")[0] for k in urtag})))
        if kr.armering:
            anm.append("hål i bjälklagen, järnen läggs om runt dem: "
                       + ", ".join(sorted({k.split(" mot ")[0] for k in kr.armering})))
        if arg.atgard == "ritning":
            from . import avloppsritning
            from .planritning import snitt
            step_fil = UT / "trebodar.step"
            if not step_fil.exists():
                raise SystemExit(f"{step_fil} saknas: bygg STEP-filen först (./mod bygg)")
            kallaren = snitt(ROT / "verktyg" / "modellanalys" / "ma", step_fil, -1000.0, UT / "avlopp-kallare.json")
            arg.ut.mkdir(parents=True, exist_ok=True)
            pdf = avloppsritning.ritningar(utdrag, kallaren, _norr(), UT / "avlopp" / "blad", arg.ut)
            print(f"  {pdf}")
        elif arg.atgard == "kontroll":
            print(f"  {len(utdrag['ledningar'])} ledningar: {len(fel)} fel, {len(anm)} anmärkningar")
            for f in fel:
                print(f"    FEL {f}")
            for x in anm:
                print(f"    {x}")
            print("  genomföringar (per rör):")
            for k in kr.skikt:
                print(f"    {k}")
            if fel:
                raise SystemExit(1)
        else:
            arg.ut.mkdir(parents=True, exist_ok=True)
            rader = ["# Avloppet", "", "| Ledning | | Ø | Längd | Vattengång från | till |",
                     "|---|---|---|---|---|---|"]
            for k, v in utdrag["ledningar"].items():
                vag, vg = v["vag"], v["vattengang"]
                langd = sum(math.dist(a, b) for a, b in zip(vag, vag[1:]))
                rader.append(f"| {k} | {v['namn']} | {v['d']:g} | {langd / 1000:.1f} m | "
                             + (f"{vg[0]:.0f} | {vg[1]:.0f} |" if vg else "lodrätt | |"))
            rader += ["", "## Kontrollen", ""] + [f"- FEL {f}" for f in fel] + [f"- {x}" for x in anm]
            rader += ["", "## Genomföringar", ""] + [f"- {k}" for k in kr.skikt]
            fil = arg.ut / "avlopp.md"
            fil.write_text("\n".join(rader) + "\n", encoding="utf-8")
            (arg.ut / "avlopp.json").write_text(json.dumps(utdrag, ensure_ascii=False, indent=1))
            print(f"  {fil}")
    elif arg.kommando == "kollektor":
        from . import installationer
        regler = importlib.import_module("trebodar.kontrollregler")
        kb = importlib.import_module("trebodar.hus.installationer.kollektor.ledningar")
        fel, anm = kb.kontroll()
        kr = installationer.krockar(rot, karna, regler, "Hus/Installationer/Köldbärare")
        fel += [f"krock med {k}" for k in kr.installationer + kr.armering]
        print(f"  {len(kb.ledningar())} rör, {len(kb.genomforingarna()[0])} genomföringar: {len(fel)} fel, "
              f"{len(anm)} anmärkningar")
        for f in fel:
            print(f"    FEL {f}")
        for x in anm:
            print(f"    {x}")
        print("  krockar mot husets delar (stommen var för sig):")
        for k in kr.stomme + kr.skikt:
            print(f"    {k}")
        for g in kb.genomforingarna()[0]:
            print(f"    {g.del_}: {g.atgard} ({g.element}, {g.punkt[0]:.0f}, {g.punkt[1]:.0f})")
        if fel:
            raise SystemExit(1)
    elif arg.kommando == "kontroll":
        from . import kontroll
        try:
            regler = importlib.import_module("trebodar.kontrollregler")
            tillatna = getattr(regler, "TILLATNA_OVERLAPP", None)
            ignorerade = getattr(regler, "IGNORERADE", None)
            utom = getattr(regler, "UTOM_KONTROLL", None)
        except ModuleNotFoundError:
            tillatna = ignorerade = utom = None
        r = kontroll.kor(rot, karna, tillatna=tillatna, ignorerade=ignorerade, utom=utom)
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
        if hasattr(regler, "LEDNINGAR"):
            from . import vagar
            vg = vagar.kontrollera(rot, karna, regler)
            print(f"  installationernas vägar: {vg.delar} ledningsdelar och {vg.stralar} armaturers ljus, "
                  f"{len(vg.fel)} fel, {len(vg.anm)} utanpåliggande ({vg.sekunder:.1f} s; alla: ./mod vagar)")
            for f in vg.fel:
                print(f"    FEL {f}")
        if hasattr(regler, "YTSKIKT"):
            from . import ytskikt
            yt = ytskikt.kontrollera(rot, karna, regler)
            print(f"  ytskikten: {yt.ytor} synliga ytor, {len(yt.fel)} språng och springor ({yt.sekunder:.1f} s; "
                  f"./mod ytor)")
            for f in yt.fel:
                print(f"    FEL {f}")
        if hasattr(regler, "INKOPSLISTA"):
            from . import inkop
            inst, fel = inkop.kontroll(rot, regler.INKOPSLISTA)
            print(f"  inköpslistan: {sum(map(len, inst.values()))} instanser av {len(inst)} specialprodukter, "
                  f"{len(fel)} fel (./mod inkop)")
            for f in fel:
                print(f"    FEL {f}")
    elif arg.kommando == "ytor":
        from . import ytskikt
        regler = importlib.import_module("trebodar.kontrollregler")
        yt = ytskikt.kontrollera(rot, karna, regler)
        print(f"  {yt.ytor} synliga ytor av {', '.join(getattr(regler, 'YTSKIKT', ()))}: {len(yt.fel)} språng och "
              f"springor ({yt.sekunder:.1f} s)")
        for f in yt.fel:
            print(f"    FEL {f}")
        if yt.fel:
            raise SystemExit(1)
    elif arg.kommando == "vagar":
        from . import vagar
        regler = importlib.import_module("trebodar.kontrollregler")
        vg = vagar.kontrollera(rot, karna, regler, arg.trad)
        print(f"  {vg.delar} ledningsdelar, {vg.kuber} kuber à {vagar.STEG:g} mm, {vg.stralar} armaturers ljus: "
              f"{len(vg.fel)} fel, {len(vg.anm)} utanpåliggande ({vg.sekunder:.1f} s)")
        for f in vg.fel:
            print(f"    FEL {f}")
        for x in vg.anm:
            print(f"    {x}")
        if vg.fel:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
