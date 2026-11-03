"""Renderingarna på webbplatsen (docs/renderingar/, https://vron.github.io/trebodar/renderingar/): planerna (plan 1,
källaren och ute, ur kameraplanens snitt) med vyernas kameror (trebodar.vyer: INNE och VYER) och bilderna.

Bilderna renderas lokalt (renderingar/rendera.sh) och versionshanteras inte. `./mod publicera` gör om dem till
JPEG i fyra storlekar (BREDDER) och laddar upp dem till releasen RELEASE på GitHub tillsammans med förteckningen
(MANIFEST: vyns kamera, objektiv och ljus när bilden renderades, modellens version och datum). Webbplatsens bygge
(GitHub Actions) hämtar dem därifrån, så bilderna ändras bara när de publiceras medan planerna och kamerorna alltid
följer modellen. En kamera som har flyttats sedan bilden renderades märks på sidan.
"""
from __future__ import annotations

import datetime
import json
import math
import shutil
import re
import subprocess
import tempfile
import unicodedata
from pathlib import Path
from typing import Any

from shapely.geometry import Polygon

from .karna import ROT
from .kameraplan import KALLARE, ORD, PLAN1
from .planritning import MINSTA_HAL, plan_ytor

RELEASE = "bilder"              # releasens tagg (inte "renderingar", som är en mapp: `git log renderingar` vore tvetydigt)
MANIFEST = "renderingar.json"
BREDDER = (480, 960, 1920, 3840)    # tumnagel, rutnät, skärm och original [px]
KVALITET = {480: 80}            # JPEG-kvaliteten (annars 86)
SIDA = Path(__file__).resolve().parents[1] / "webb" / "renderingar.html"
FYLL = {"karna": "#b9b3a9", "betong": "#ecebe7", "stal": "#5a5f66", "vit": "#ffffff"}   # ritningsmallens FYLL
FORENKLA = 4.0                  # planens ytor förenklas till den noggrannheten [mm]
MARGINAL = 2500.0               # runt huset och kamerorna i planen ute [mm]

__all__ = ["MANIFEST", "RELEASE", "publicera", "sidodata", "version", "webb"]


def version() -> str:
    """Repots version (kort commit), med "+" om modellens källor är ändrade sedan dess."""
    def git(*a: str) -> str:
        return subprocess.run(["git", *a], cwd=ROT, capture_output=True, text=True).stdout.strip()
    andrad = git("status", "--porcelain", "--", "modeller/trebodar", "verktyg/modellering")
    return git("rev-parse", "--short", "HEAD") + ("+" if andrad else "")


def sidodata(ut: Path, vyer: dict[str, dict], ljus: dict[str, list], kvalitet: str, sedan: float) -> list[str]:
    """Vyns data bredvid varje bild som renderats sedan tiden `sedan` (<namn>.json): kameran, målet, objektivet och
    dagsljuset (månad, dag, klocka, väder), kvaliteten, tiden och modellens version. `./mod publicera` läser dem."""
    tid = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    ver = version()
    klara = []
    for namn, v in vyer.items():
        png = ut / f"{namn}.png"
        if png.exists() and png.stat().st_mtime >= sedan:
            data = {"kamera": v["kamera"], "mal": v["mal"], "lins": v["lins"], "ljus": ljus[namn],
                    "kvalitet": kvalitet, "renderad": tid, "modell": ver}
            png.with_suffix(".json").write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            klara.append(namn)
    return klara


# planerna och kamerorna -------------------------------------------------------------------------------------------

def _svg(g: Any) -> str:
    """Ytorna som en SVG-väg i modellens mm med y nedåt (hålen som egna delvägar, utom de mindre än MINSTA_HAL)."""
    vagar = []
    for p in getattr(g, "geoms", [g]):
        if not isinstance(p, Polygon) or p.is_empty:
            continue
        p = p.simplify(FORENKLA, preserve_topology=True)
        for r in [p.exterior, *(r for r in p.interiors if Polygon(r).area >= MINSTA_HAL)]:
            k = list(r.coords)[:-1]
            if len(k) >= 3:
                vagar.append("M" + " ".join(f"{x:.0f} {-y:.0f}" for x, y in k) + "Z")
    return "".join(vagar)


def _ytor(delar: list[dict]) -> list[dict]:
    return [{"d": _svg(g), "f": FYLL.get(f, f) if f else None, "s": s} for g, f, s in plan_ytor(delar)]


def _kameror(ute: dict[str, dict], inne: dict[str, dict], rum: dict[str, tuple], texter: dict[str, str],
             teknik: set[str]) -> list[dict]:
    """Vyernas kameror på planerna: inomhusbilderna (I01–I30) på plan 1 eller i källaren, de andra vyerna (ute,
    detalj) ute eller, när de är inne, på sitt plan. text: bildtexten (texter, annars ur namnet); teknik: bilden
    hör till stommen och installationerna; r: bildvinkelns kil i planen [mm]."""
    ut = []
    for namn, k in {**inne, **ute}.items():
        (x, y, z), (tx, ty, _) = k["kamera"], k["mal"]
        plan = ("kallare" if z < 0 else "plan1") if k.get("inne") else "ute"
        if namn in inne:
            nr, vynamn = namn.split("-", 1)
            ord_ = vynamn[len(str(k["rum"])) + 1:].split("-")[:-1]
            serie, etikett = "inne", nr
            text = f"{rum[str(k['rum'])][0]}, {' '.join(ORD.get(o, o) for o in ord_)}"
            r = 1500.0 if k["objektiv"] == "öga" else 1150.0
        else:
            serie = "detalj" if namn.startswith("detalj-") else "ute"
            etikett = namn.split("-", 1)[-1]
            text = texter.get(namn) or ", ".join(namn.split("-", 1)).capitalize()
            r = min(max(0.4 * math.hypot(tx - x, ty - y), 900.0), 6000.0)
        ut.append({"namn": namn, "etikett": etikett, "text": text, "plan": plan, "serie": serie,
                   "teknik": namn in teknik, "objektiv": k.get("objektiv"), "kamera": k["kamera"], "mal": k["mal"],
                   "lins": k["lins"],
                   "ljus": list(k["ljus"]), "r": round(r)})
    return ut


def webb(plan1: list[dict], kallare: list[dict], ute: dict[str, dict], inne: dict[str, dict], rum: dict[str, tuple],
         trapphal: list[tuple[float, float]], norr: tuple[float, float], ut: Path, texter: dict[str, str] | None = None,
         teknik: set[str] | None = None) -> Path:
    """Sidan med renderingarna (index.html) och dess data (plan.json, som startsidan också läser) i mappen ut;
    bilderna hämtas till ut/bilder (`./mod publicera`, GitHub Actions)."""
    kameror = _kameror(ute, inne, rum, texter or {}, teknik or set())
    hus = _ytor(plan1)
    xs = [PLAN1[0], PLAN1[1]] + [k["kamera"][0] for k in kameror if k["plan"] == "ute"]
    ys = [PLAN1[2], PLAN1[3]] + [k["kamera"][1] for k in kameror if k["plan"] == "ute"]

    def rumnamn(kallaren: bool) -> list[dict]:
        return [{"namn": n, "x": l[0], "y": l[1]} for n, l in rum.values() if (len(l) > 2 and l[2] == "k") == kallaren]

    data = {
        "version": version(),
        "byggd": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "norr": list(norr),
        "planer": {
            "plan1": {"namn": "Plan 1", "omrade": list(PLAN1), "ytor": hus, "rum": rumnamn(False),
                      "trappa": [list(p) for p in trapphal]},
            "kallare": {"namn": "Källare", "omrade": list(KALLARE), "ytor": _ytor(kallare), "rum": rumnamn(True)},
            "ute": {"namn": "Ute", "omrade": [min(xs) - MARGINAL, max(xs) + MARGINAL, min(ys) - MARGINAL,
                                              max(ys) + MARGINAL], "ytor": hus, "rum": []},
        },
        "kameror": kameror,
    }
    ut.mkdir(parents=True, exist_ok=True)
    (ut / "plan.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    shutil.copy(SIDA, ut / "index.html")
    return ut / "index.html"


# publiceringen ----------------------------------------------------------------------------------------------------

def _gh(*a: str, kontroll: bool = True) -> subprocess.CompletedProcess[str]:
    svar = subprocess.run(["gh", *a], cwd=ROT, capture_output=True, text=True)
    if kontroll and svar.returncode:
        raise SystemExit(f"gh {' '.join(a[:3])} …: {svar.stderr.strip()}")
    return svar


def _namn(png: Path) -> str:
    """Vyns namn ur bildens filnamn (NFC; macOS kan ge filnamnen i NFD)."""
    return unicodedata.normalize("NFC", png.stem)


def _filnamn(namn: str) -> str:
    """Filnamnet utan å, ä och ö (GitHub byter ut andra tecken än ASCII i releasens filnamn)."""
    ascii_ = unicodedata.normalize("NFKD", namn).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9_.-]", "-", ascii_)


def _jpeg(png: Path, mapp: Path) -> tuple[list[int], list[int]]:
    """Bilden som JPEG i BREDDER (högst bildens egen bredd) i mappen, <filnamn>-<bredd>.jpg: bredderna och
    storleken."""
    from PIL import Image
    with Image.open(png) as im:
        bild = im.convert("RGB")
    bredder = sorted({min(b, bild.width) for b in BREDDER})
    for b in bredder:
        liten = bild if b == bild.width else bild.resize((b, round(bild.height * b / bild.width)), Image.Resampling.LANCZOS)
        liten.save(mapp / f"{_filnamn(_namn(png))}-{b}.jpg", "JPEG", quality=KVALITET.get(b, 86), optimize=True,
                   progressive=True)
    return bredder, [bild.width, bild.height]


def publicera(mappar: list[Path], urval: list[str], webb_: Path, aktuella: set[str], lokalt: bool) -> None:
    """De renderade bilderna i mapparna (de med sidodata; urval: namnen eller början av dem, annars alla) som JPEG
    till webb_/bilder med förteckningen och, utom lokalt, till releasen RELEASE, varefter webbplatsen byggs om.
    Förteckningen slås ihop med den publicerade; vyer som inte finns längre tas bort."""
    hittade = sorted((p for m in mappar if m.is_dir() for p in m.glob("*.png") if p.with_suffix(".json").exists()
                      and (not urval or any(_namn(p).startswith(unicodedata.normalize("NFC", u)) for u in urval))),
                     key=_namn)
    if not hittade:
        raise SystemExit(f"inga renderade bilder med sidodata i {', '.join(map(str, mappar))}"
                         + (f" ({' '.join(urval)})" if urval else ""))
    mapp = webb_ / "bilder"
    mapp.mkdir(parents=True, exist_ok=True)
    forteckning: dict[str, dict] = {}
    if lokalt:
        if (mapp / MANIFEST).exists():
            forteckning = json.loads((mapp / MANIFEST).read_text(encoding="utf-8"))
    elif _gh("release", "view", RELEASE, kontroll=False).returncode:
        _gh("release", "create", RELEASE, "--title", "Renderingar", "--latest=false", "--notes",
            "Renderingarna på webbplatsen (https://vron.github.io/trebodar/renderingar/), publicerade med "
            "`./mod publicera` (renderingar/README.md). Bilderna versionshanteras inte; webbplatsens bygge hämtar "
            "dem härifrån.")
        print(f"  releasen {RELEASE} skapad")
    else:
        with tempfile.TemporaryDirectory() as tmp:
            if not _gh("release", "download", RELEASE, "-p", MANIFEST, "-D", tmp, kontroll=False).returncode:
                forteckning = json.loads((Path(tmp) / MANIFEST).read_text(encoding="utf-8"))
    idag = datetime.date.today().isoformat()
    nya: list[Path] = []
    bort: set[str] = set()
    for png in hittade:
        namn = _namn(png)
        bredder, storlek = _jpeg(png, mapp)
        filer = [f"{_filnamn(namn)}-{b}.jpg" for b in bredder]
        bort |= set(forteckning.get(namn, {}).get("filer", [])) - set(filer)
        forteckning[namn] = {**json.loads(png.with_suffix(".json").read_text(encoding="utf-8")),
                                 "storlek": storlek, "bredder": bredder, "filer": filer, "publicerad": idag}
        nya += [mapp / f for f in filer]
        print(f"  {namn}: {storlek[0]} × {storlek[1]}, {sum((mapp / f).stat().st_size for f in filer) / 1e6:.1f} MB")
    for namn in [n for n in forteckning if n not in aktuella]:
        bort |= set(forteckning.pop(namn)["filer"])
        print(f"  {namn}: borttagen (vyn finns inte längre)")
    for f in bort:
        (mapp / f).unlink(missing_ok=True)
    (mapp / MANIFEST).write_text(json.dumps(dict(sorted(forteckning.items())), ensure_ascii=False, indent=1) + "\n",
                                 encoding="utf-8")
    print(f"  {len(hittade)} bilder, {len(forteckning)} i förteckningen: {mapp}")
    if lokalt:
        return
    _gh("release", "upload", RELEASE, *map(str, nya), "--clobber")          # bilderna före förteckningen
    _gh("release", "upload", RELEASE, str(mapp / MANIFEST), "--clobber")
    for f in sorted(bort):
        _gh("release", "delete-asset", RELEASE, f, "--yes", kontroll=False)
    _gh("workflow", "run", "bygg.yml", "--ref", "main")
    print(f"  uppladdade till releasen {RELEASE}; webbplatsen byggs om (gh run list --workflow bygg.yml)")
