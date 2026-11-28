"""Det som renderingen och ljusplanerna (blender/rendera.py) behöver utanför förrådet, i lokalt/ (versionshanteras
inte), och kontrollen före Blender. Utan något av det renderar Blender ändå, men utan träd, buskar, markens texturer,
fotohimlar, stjärnor eller armaturernas ljusfördelning, så `_blender` (cli.py) stannar i stället med listan över det
som saknas och hur det hämtas:

- omgivningen (vyer.GEODATA["mapp"]): rutnäten, maskerna och tomtens växter som `./mod omgivning` bygger ur de
  nedladdade höjderna och kartan (nedladdat/), Lantmäteriets höjder och inmätningen (GEODATA["terrang"]) och
  vyer.py. De byggs om före renderingen när något av det är nyare (nyare());
- Poly Havens texturer, modeller (blend-filerna med sina bilder) och alla himlarna (polyhaven.py);
- natthimlens stjärnkatalog och månkarta (natthimmel.py);
- armaturernas fotometrifiler (cli._armaturer, `./mod el hamta`).

Bilderna som blend-filerna själva pekar på kontrollerar Blender när scenen är byggd (blender/rendera.py)."""
from __future__ import annotations

from pathlib import Path

from . import natthimmel, polyhaven
from .karna import ROT

# det `./mod omgivning` skriver (geodata.bygg och terrang.bygg)
OMGIVNING = ("omgivning.json", "hojd.f32", "marktacke_0.png", "marktacke_1.png", "marktacke_2.png", "nara.f32",
             "nara_tacke.png", "nara_lag.png", "nara_objekt.json")
HAMTA = "./mod omgivning --hamta"


def _kallor(cfg: dict) -> list[Path]:
    """Det omgivningen byggs av: koden, vyerna och skelettet (GEODATA, tomtens kontur och läge) och indata."""
    kod = Path(__file__).resolve().parent
    filer = [kod / "geodata.py", kod / "terrang.py", ROT / "modeller" / "trebodar" / "vyer.py",
             ROT / "modeller" / "trebodar" / "skelett.py"]
    terr = ROT / cfg.get("terrang", "lokalt/terrang")
    for mapp in (ROT / cfg["mapp"] / "nedladdat", terr / "hojd", terr / "punkter"):
        filer += [f for f in mapp.rglob("*") if f.is_file()]
    return filer


def nyare(cfg: dict) -> str | None:
    """Det första av det omgivningen byggs av som är nyare än något av det som byggts (eller det som saknas), eller
    None när omgivningen är aktuell."""
    mapp = ROT / cfg["mapp"]
    byggt = [mapp / f for f in OMGIVNING]
    if not all(f.exists() for f in byggt):
        return next(f.name for f in byggt if not f.exists())
    t = min(f.stat().st_mtime for f in byggt)
    return next((str(f.relative_to(ROT)) for f in _kallor(cfg) if f.stat().st_mtime > t), None)


def kan_byggas(cfg: dict) -> bool:
    """Finns det nedladdade som omgivningen byggs av (geodata.bygg och terrang.bygg)?"""
    terr = ROT / cfg.get("terrang", "lokalt/terrang")
    ned = ROT / cfg["mapp"] / "nedladdat"
    return (ned / "osm" / "osm.json").exists() and any((ned / "hojd").glob("*")) and (terr / "hojd").is_dir()


def saknas(cfg: dict) -> list[str]:
    """Det som saknas, med hur det hämtas: [rad]."""
    fel = []
    mapp = ROT / cfg["mapp"]
    fel += [f"{(mapp / f).relative_to(ROT)} ({'./mod omgivning' if kan_byggas(cfg) else HAMTA})"
            for f in OMGIVNING if not (mapp / f).exists()]
    if "tillgangar" not in cfg:
        return fel + ['vyer.GEODATA["tillgangar"] (Poly Havens mapp) saknas']
    ph = ROT / cfg["tillgangar"]
    filer = [ph / "texturer" / n / f"{n}_{k}_{r}.jpg"
             for n, r in polyhaven.TEXTURER.items() for _, k in polyhaven.KARTOR]
    filer += [ph / "modeller" / n / f"{n}_{r}.blend" for n, r in polyhaven.MODELLER.items()]
    filer += [Path(polyhaven._himmelfil(str(ph), n)) for n in polyhaven.HIMLAR]
    filer += [natthimmel.KATALOG, natthimmel.MANKARTA]
    fel += [f"{f.relative_to(ROT)} ({HAMTA})" for f in filer if not f.exists()]
    return fel + [f"{(ph / 'modeller' / n / 'textures').relative_to(ROT)}/ tom (ta bort modellens mapp och {HAMTA})"
                  for n in polyhaven.MODELLER if not any((ph / "modeller" / n / "textures").glob("*"))]
