"""
Bygger allt som genereras ur källorna, i beroendeordning: modellen (STEP), webbvisaren, kameraplanen, granskningens
figur, beräkningarna, rapporterna, ritningarna och webbplatsen med handlingarna (docs/). Se README.md.

    ./bygg                  allt som är inaktuellt
    ./bygg K-05 R-05        de stegen och det de bygger på
    ./bygg --snabb          bara de snabba stegen; de tunga ska vara räknade och incheckade (GitHub Actions)
    ./bygg --lista          stegen och om de är aktuella
    ./bygg --om K-01        bygg om även när steget är aktuellt
    ./bygg --markera U-03   ange att stegets resultat är aktuella utan att köra det (efter en ändring i källorna
                            som inte påverkar resultaten)

Ett steg är aktuellt när dess kontrollsumma är oförändrad sedan det byggdes och dess utdata finns. Summan räknas
över stegets källor (alla filer i dess mappar som inte ignoreras av git, utom dess incheckade resultat), dess
kommandon och summorna för stegen det bygger på. Snabba steg sparar summan i .bygg/ (versionshanteras inte). Tunga
steg sparar den i <mapp>/räknat.json, som checkas in tillsammans med resultaten som andra steg läser och rapporten.
"""
import argparse
import datetime
import fnmatch
import hashlib
import html
import json
import os
import shutil
import subprocess
import time
import tomllib
import unicodedata
import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path

ROT = Path(__file__).resolve().parents[2]
STAMPAR = ROT / ".bygg"
BER = "beräkningar"
MALL = f"{BER}/ritningsmall"
MODELL = ["modeller/trebodar", "verktyg/modellering"]
PYTHON = "3.12"

# Pythonmiljöerna: mapp med .venv och kravfilerna
MILJOER = {
    "ber": (BER, sorted(str(p.relative_to(ROT)) for p in (ROT / BER).glob("*/requirements.txt"))),
    "mod": ("verktyg/modellering", ["verktyg/modellering/requirements.txt"]),
    "ma": ("verktyg/modellanalys", ["verktyg/modellanalys/requirements.txt"]),
}


@dataclass
class Steg:
    namn: str
    mapp: str                                  # arbetsmapp (relativt roten); ingår i källorna
    kor: list[list[str]]                       # kommandon; första ordet är miljön: ber, ma (python) eller mod (./mod)
    kallor: list[str] = field(default_factory=list)      # fler mappar och filer i kontrollsumman
    bygger_pa: list[str] = field(default_factory=list)
    utdata: list[str] = field(default_factory=list)      # ska finnas efteråt (relativt roten)
    rapport: tuple[str, str] | None = None               # (pdf i mappen, titel) -> rapporter/<nr>rev<rev> <titel>.pdf
    tung: bool = False                                   # räknas lokalt; resultaten checkas in
    incheckat: list[str] = field(default_factory=list)   # genererade filer som checkas in (mönster relativt mappen)
    lokalt: list[str] = field(default_factory=list)      # tunga steg: mellanresultat som tunga steg efter läser
    miljoer: list[str] = field(default_factory=list)     # fler Pythonmiljöer som kommandona behöver


def ber(nr: str, *kor: str | list[str], **kw) -> Steg:
    return Steg(nr, f"{BER}/{nr}", [["ber", *(k.split() if isinstance(k, str) else k)] for k in kor], **kw)


def ritning(nr: str, titel: str, *kor: str, bygger_pa: list[str] = (), kallor: list[str] = ()) -> Steg:
    return ber(nr, *(kor or ["ritningar.py"]), kallor=[MALL, *kallor], bygger_pa=list(bygger_pa),
               utdata=[f"ritningar/{nr} {titel}.pdf"])


STEG = [
    Steg("modell", "modeller/trebodar", [["mod", "bygg", "--format", "step"]], kallor=MODELL,
         utdata=["modeller/trebodar/ut/trebodar.step"]),
    Steg("webb", "verktyg/modellering/webb", [["mod", "webb"]], kallor=MODELL,
         utdata=["docs/index.html", "docs/vyer.json", "docs/modell/trebodar.glb"]),
    Steg("kameraplan", "renderingar", [["mod", "kameraplan"]], kallor=[*MODELL, "verktyg/modellanalys"],
         bygger_pa=["modell"], miljoer=["ma"],
         utdata=["renderingar/kameraplan.pdf", "docs/renderingar/index.html", "docs/renderingar/plan.json"]),
    Steg("granskning", "verktyg/modellanalys", [["ma", "kontroll_laster.py"]],
         kallor=[f"{BER}/{nr}" for nr in ("F-01", "K-01", "K-05", "K-06")], bygger_pa=["modell"],
         utdata=["verktyg/modellanalys/granskning/ytterväggens_läge.png"]),
    ber("F-01", "berakning.py", rapport=("F-01_forutsattningar.pdf", "Förutsättningar, referenser och laster")),
    ber("AV-01", "bygg.py", rapport=("AV-01_avfallshanteringsplan.pdf", "Avfallshanteringsplan")),
    ber("K-01", "berakning.py", rapport=("nock_och_dalbalkar_K-01.pdf", "Nock- och dalbalkar"),
        incheckat=["halbild_*.csv"]),
    ber("K-02", "berakning.py", rapport=("K-02_varmeflode_nockbalk.pdf", "Nocklbalk - temperatur i stålplåtarna")),
    ber("U-02", "berakning.py", bygger_pa=["K-01"], kallor=[f"{BER}/K-01/indata.toml"],
        rapport=("U-02_lyft_balkar.pdf", "Nock- och dalbalkar - lyft i två punkter")),
    ber("K-05", "laster.py", "berakning.py", "validering/konvergens.py", "validering/vaggande.py", "rapport.py",
        tung=True, rapport=("rapport/K-05_mellanbjalklag.pdf", "Mellanbjälklag och källarpelare"),
        incheckat=["resultat.json", "konvergens.json", "vaggande.json"], lokalt=["falt.npz", "nedb.npz"]),
    ber("K-03", "berakning.py", bygger_pa=["K-05"],
        rapport=("K-03_takbalkar_takstolar_stolpar.pdf", "Takbalkar, takstolar och stolpar")),
    ber("K-06", "berakning06.py", "berakning.py", "validering/natkonvergens.py", "rapport.py", bygger_pa=["K-05"],
        tung=True, rapport=("rapport/K-06_grund.pdf", "Bottenplatta och källarväggar"),
        incheckat=["resultat.json"]),
    ber("U-01", "berakning.py", bygger_pa=["K-05", "K-06"], tung=True,
        rapport=("U-01_bottenplatta_fukt.pdf", "Bottenplattan - temperatur och fukt under året")),
    ber("U-03", "berakning.py", tung=True,
        rapport=("U-03_takets_luftspalt.pdf", "Takets luftspalt - luftflöde, fukt och mögelrisk")),
    ritning("R-01", "Nock- och dalbalkar", bygger_pa=["K-01", "K-03", "K-05"], kallor=["modeller/balkplattor"]),
    ritning("R-05", "Källarstomme", bygger_pa=["K-05", "K-06"]),
    ritning("R-04", "Bottenplatta", bygger_pa=["R-05", "K-06"]),
    ritning("R-06", "Mellanbjälklag", bygger_pa=["R-05", "K-05", "K-06"]),
    ritning("R-03", "Bärande system i betong", bygger_pa=["R-04", "R-05", "R-06"]),
    ritning("AR-01", "Fasadsten på källarväggarna", "berakning.py", "ritningar.py"),
    ritning("AR-02", "Utsättning", bygger_pa=["R-05", "K-05"]),
]
STEG_NAMN = {s.namn: s for s in STEG}


def git(*arg: str) -> bytes:
    return subprocess.run(["git", *arg], cwd=ROT, capture_output=True, check=True).stdout


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


_summor: dict[str, str] = {}


def kontrollsumma(s: Steg) -> str:
    """Summan över stegets källor (utom README och andra .md), kommandon och de steg det bygger på (samma på alla
    datorer)."""
    if s.namn in _summor:
        return _summor[s.namn]
    h = hashlib.sha256(json.dumps([s.kor, [kontrollsumma(STEG_NAMN[b]) for b in s.bygger_pa]]).encode())
    utom = [f"{s.mapp}/{m}" for m in s.incheckat] + [f"{s.mapp}/räknat.json", "*.md"]
    filer = git("ls-files", "-z", "-co", "--exclude-standard", "--", s.mapp, *s.kallor).split(b"\0")
    for namn, f in sorted({(nfc(f.decode()), f.decode()) for f in filer if f}):   # namnet i NFC, filen som den heter
        if any(fnmatch.fnmatch(namn, nfc(u)) for u in utom):
            continue
        p = ROT / f
        h.update(namn.encode() + b"\0" + (hashlib.sha256(p.read_bytes()).digest() if p.is_file() else b"-"))
    _summor[s.namn] = h.hexdigest()[:16]
    return _summor[s.namn]


def stampel(s: Steg) -> Path:
    return ROT / s.mapp / "räknat.json" if s.tung else STAMPAR / f"{s.namn}.json"


def byggd_summa(s: Steg) -> str | None:
    try:
        return json.loads(stampel(s).read_text(encoding="utf-8"))["kontrollsumma"]
    except (OSError, ValueError, KeyError):
        return None


def rapportfil(s: Steg) -> Path | None:
    if not s.rapport:
        return None
    rev = revision(s)
    return ROT / "rapporter" / nfc(f"{s.namn}rev{rev} {s.rapport[1]}.pdf")


def revision(s: Steg) -> str:
    mapp = ROT / s.mapp
    if (mapp / "indata.toml").exists():
        rev = tomllib.loads((mapp / "indata.toml").read_text(encoding="utf-8")).get("projekt", {}).get("revision")
        if rev:
            return rev
    return json.loads((mapp / "rapport" / "projekt.json").read_text(encoding="utf-8"))["revision"]


def saknas(s: Steg) -> list[str]:
    filer = [ROT / u for u in s.utdata] + ([rapportfil(s)] if s.rapport else [])
    return [str(f.relative_to(ROT)) for f in filer if not f.exists()]


def aktuell(s: Steg) -> bool:
    return byggd_summa(s) == kontrollsumma(s) and not saknas(s)


def plan(valda: list[str], om: bool, snabb: bool) -> list[Steg]:
    """Stegen som ska köras, i ordning: de valda som är inaktuella och de inaktuella stegen de bygger på. Ett tungt
    steg som ska köras kräver de tunga stegens mellanresultat (lokalt) före sig och kör om dem som saknar dem."""
    kor: set[str] = set()

    def besok(namn: str, vald: bool) -> None:
        s = STEG_NAMN[namn]
        for b in s.bygger_pa:
            besok(b, False)
        if snabb and s.tung:
            return
        if not aktuell(s) or (vald and om):
            kor.add(namn)

    for namn in valda:
        besok(namn, True)
    andrat = True
    while andrat:
        andrat = False
        for namn in list(kor):
            for b in STEG_NAMN[namn].bygger_pa:
                d = STEG_NAMN[b]
                if (STEG_NAMN[namn].tung and d.tung and b not in kor
                        and any(not (ROT / d.mapp / f).exists() for f in d.lokalt)):
                    kor.add(b)
                    andrat = True
    return [s for s in STEG if s.namn in kor]


def miljo(namn: str) -> Path:
    """Skapar eller uppdaterar en Pythonmiljö (uv) när den saknas eller kravfilerna har ändrats."""
    mapp, krav = MILJOER[namn]
    venv = ROT / mapp / ".venv"
    python = venv / "bin" / "python"
    summa = hashlib.sha256(b"".join((ROT / k).read_bytes() for k in krav)).hexdigest()
    markering = venv / "bygg-krav.txt"
    if python.exists() and markering.exists() and markering.read_text() == summa:
        return python
    print(f"== miljö {mapp}/.venv", flush=True)
    if not python.exists():
        subprocess.run(["uv", "venv", "--python", PYTHON, str(venv)], check=True)
    subprocess.run(["uv", "pip", "install", "--python", str(python), *sum((["-r", str(ROT / k)] for k in krav), [])],
                   check=True)
    markering.write_text(summa)
    return python


def kor_steg(s: Steg) -> None:
    env = {**os.environ, "MPLBACKEND": "Agg", "PYTHONUNBUFFERED": "1"}
    for m in s.miljoer:
        miljo(m)
    for k in s.kor:
        if k[0] == "mod":
            miljo("mod")
            argv = [str(ROT / "verktyg/modellering/mod"), *k[1:]]
        else:
            argv = [str(miljo(k[0])), *k[1:]]
        print(f"   $ {' '.join(k[1:]) if k[0] != 'mod' else './mod ' + ' '.join(k[1:])}", flush=True)
        cwd = ROT / ("verktyg/modellering" if k[0] == "mod" else s.mapp)   # ./mod körs i sin egen mapp
        subprocess.run(argv, cwd=cwd, env=env, check=True)
    if s.rapport:
        dst = rapportfil(s)
        for gammal in (ROT / "rapporter").glob(f"{s.namn}rev*.pdf"):
            gammal.unlink()
        shutil.copy(ROT / s.mapp / s.rapport[0], dst)
    if fel := saknas(s):
        raise SystemExit(f"{s.namn}: utdata saknas efter bygget: {', '.join(fel)}")
    _summor.clear()                    # steget kan ha skrivit om källor (t.ex. K-01:s hålbilder)
    spara_summa(s)


def spara_summa(s: Steg) -> None:
    stampel(s).parent.mkdir(exist_ok=True)
    stampel(s).write_text(json.dumps({"kontrollsumma": kontrollsumma(s)}, indent=1) + "\n", encoding="utf-8")


def webbplats() -> None:
    """docs/handlingar/: en sida med länkar till rapporterna, ritningarna och kameraplanen (kopior bredvid)."""
    ut = ROT / "docs" / "handlingar"
    shutil.rmtree(ut, ignore_errors=True)
    grupper = [("Rapporter", sorted((ROT / "rapporter").glob("*.pdf"))),
               ("Ritningar", sorted((ROT / "ritningar").glob("*.pdf"))),
               ("Övrigt", [p for p in [ROT / "renderingar" / "kameraplan.pdf"] if p.exists()])]
    rader = []
    for rubrik, filer in grupper:
        rader.append(f"<h2>{rubrik}</h2>\n<ul>")
        for f in filer:
            dst = ut / f.parent.name / nfc(f.name)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(f, dst)
            lank = urllib.parse.quote(f"{f.parent.name}/{nfc(f.name)}")
            rader.append(f'<li><a href="{lank}">{html.escape(nfc(f.stem))}</a> '
                         f'<span>{f.stat().st_size / 1e6:.1f} MB</span></li>')
        rader.append("</ul>")
    version = git("rev-parse", "--short", "HEAD").decode().strip()
    tid = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    (ut / "index.html").write_text(f"""<!doctype html>
<html lang="sv">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Trebodar – handlingar</title>
<style>
  :root {{ --bg: #f4f3ef; --panel: #fff; --ink: #222; --dim: #777; --accent: #2f6f8f; }}
  @media (prefers-color-scheme: dark) {{ :root {{ --bg: #1b1d20; --panel: #26292d; --ink: #e8e6e1; --dim: #9a9a9a;
    --accent: #6fb3d3; }} }}
  body {{ margin: 0; background: var(--bg); color: var(--ink); font: 15px/1.45 system-ui, sans-serif; }}
  main {{ max-width: 760px; margin: 0 auto; padding: 24px 16px 48px; }}
  h1 {{ font-size: 22px; margin: 0 0 4px; }} h2 {{ font-size: 13px; margin: 28px 0 8px; color: var(--dim);
    text-transform: uppercase; letter-spacing: .04em; }}
  ul {{ list-style: none; margin: 0; padding: 0; background: var(--panel); border-radius: 6px; }}
  li {{ display: flex; justify-content: space-between; gap: 12px; padding: 8px 12px; border-top: 1px solid #8882; }}
  li:first-child {{ border-top: 0; }} li span, p {{ color: var(--dim); }} li span {{ white-space: nowrap; }}
  a {{ color: var(--accent); }}
</style>
</head>
<body>
<main>
<h1>Fritidshus Trebodar – handlingar</h1>
<p>Byggda ur källorna i <a href="https://github.com/vron/trebodar">vron/trebodar</a> ({version}, {tid}).
<a href="../">Modellen i 3D</a> · <a href="../renderingar/">Renderingar</a></p>
{chr(10).join(rader)}
</main>
</body>
</html>
""", encoding="utf-8")
    print(f"== webbplats: {ut.relative_to(ROT)}/index.html ({sum(len(f) for _, f in grupper)} filer)")


def tid(t: float) -> str:
    return f"{t / 60:.1f} min" if t >= 60 else f"{t:.0f} s"


def main() -> None:
    a = argparse.ArgumentParser(prog="bygg", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("steg", nargs="*", help=f"stegen (standard: alla): {', '.join(STEG_NAMN)}")
    a.add_argument("--snabb", action="store_true", help="bara snabba steg; stoppa om ett tungt steg är inaktuellt")
    a.add_argument("--om", action="store_true", help="bygg om de valda stegen även om de är aktuella")
    a.add_argument("--lista", action="store_true", help="visa stegen och om de är aktuella")
    a.add_argument("--markera", action="store_true",
                   help="spara kontrollsumman för de valda stegen utan att köra dem (resultaten är aktuella)")
    arg = a.parse_args()
    if okanda := [n for n in arg.steg if n not in STEG_NAMN]:
        raise SystemExit(f"okända steg: {', '.join(okanda)} (finns: {', '.join(STEG_NAMN)})")
    if arg.lista:
        for s in STEG:
            tillstand = "aktuell" if aktuell(s) else "inaktuell" + (f" (saknas: {', '.join(saknas(s))})"
                                                                     if byggd_summa(s) == kontrollsumma(s) else "")
            print(f"{s.namn:11} {'tung ' if s.tung else '     '} {tillstand}")
        return
    if arg.markera:
        if not arg.steg:
            raise SystemExit("--markera kräver stegen")
        for namn in arg.steg:
            s = STEG_NAMN[namn]
            if fel := saknas(s):
                raise SystemExit(f"{namn}: utdata saknas: {', '.join(fel)}")
            spara_summa(s)
            print(f"{namn}: markerad som aktuell ({kontrollsumma(s)})")
        return
    if arg.snabb:
        if inaktuella := [s.namn for s in STEG if s.tung and byggd_summa(s) != kontrollsumma(s)]:
            raise SystemExit(f"De tunga stegen {', '.join(inaktuella)} är inte räknade efter ändringarna i deras "
                             f"källor. Kör ./bygg {' '.join(inaktuella)} lokalt och checka in resultaten och "
                             f"räknat.json.")
    steg = plan(arg.steg or list(STEG_NAMN), arg.om, arg.snabb)
    tider = []
    for s in steg:
        print(f"== {s.namn}{' (tung)' if s.tung else ''}", flush=True)
        t = time.perf_counter()
        kor_steg(s)
        tider.append((s.namn, time.perf_counter() - t))
        print(f"   klart ({tid(tider[-1][1])})", flush=True)
    if not arg.steg:
        webbplats()
    if tider:
        print(f"\nTid {tid(sum(t for _, t in tider))}: " + ", ".join(f"{n} {tid(t)}" for n, t in tider))
    else:
        print("Allt är aktuellt.")


if __name__ == "__main__":
    main()
