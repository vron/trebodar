"""
Bygger allt som genereras ur källorna, i beroendeordning: modellen (STEP), webbvisaren, kameraplanen, granskningens
figur, beräkningarna, rapporterna, ritningarna och webbplatsen: startsidan med bilderna, planerna och
handlingarna (docs/, startsida.py). Se README.md.

    ./bygg                  allt som är inaktuellt
    ./bygg K-05 R-05        de stegen och det de bygger på
    ./bygg --snabb          bara de snabba stegen; de tunga ska vara räknade och incheckade (GitHub Actions)
    ./bygg --lista          stegen och om de är aktuella
    ./bygg --om K-01        bygg om även när steget är aktuellt
    ./bygg --markera U-03   ange att stegets resultat är aktuella utan att köra det (efter en ändring i källorna
                            som inte påverkar resultaten)
    ./bygg U-04             ett manuellt steg (ljusplanerna): görs bara när det väljs

Stegen körs parallellt (högst --jobb åt gången): ett steg startar när stegen det bygger på är klara. När flera
steg körs har deras utdata stegets namn först på raden.

Ett steg är aktuellt när dess kontrollsumma är oförändrad sedan det byggdes och dess utdata finns. Summan räknas
över stegets källor (alla filer i dess mappar som inte ignoreras av git, utom dess incheckade resultat), dess
kommandon och summorna för stegen det bygger på. Snabba steg sparar summan i .bygg/ (versionshanteras inte). Tunga
steg sparar den i <mapp>/räknat.json, som checkas in tillsammans med resultaten som andra steg läser och rapporten.
Manuella steg är tunga steg som bygger på hela modellen (ljusplanerna, som renderingarna): de görs bara när de väljs,
och ./bygg --snabb stoppar inte när de är inaktuella.
"""
import argparse
import fnmatch
import hashlib
import json
import os
import shutil
import subprocess
import threading
import time
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
import tomllib
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

import startsida

ROT = Path(__file__).resolve().parents[2]
STAMPAR = ROT / ".bygg"
BER = "beräkningar"
MALL = f"{BER}/ritningsmall"
MODELL = ["modeller/trebodar", "verktyg/modellering"]
PYTHON = "3.12"
MILJO_VERSION = "2"            # höj när miljöerna ska byggas om (2: bytekoden kompileras i förväg)

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
    manuell: bool = False                                # tungt steg som bara görs när det väljs (./bygg U-04)


def ber(nr: str, *kor: str | list[str], **kw) -> Steg:
    return Steg(nr, f"{BER}/{nr}", [["ber", *(k.split() if isinstance(k, str) else k)] for k in kor], **kw)


def ritning(nr: str, titel: str, *kor: str, bygger_pa: list[str] = (), kallor: list[str] = ()) -> Steg:
    return ber(nr, *(kor or ["ritningar.py"]), kallor=[MALL, *kallor], bygger_pa=list(bygger_pa),
               utdata=[f"ritningar/{nr} {titel}.pdf"])


def installation(nr: str, titel: str, system: str) -> Steg:
    """Installationsritningen nr (./mod <system> ritning) ur modellens snitt, till ritningar/."""
    return Steg(nr, "verktyg/modellering", [["mod", system, "ritning", "--ut", "../../ritningar"]],
                kallor=[*MODELL, MALL, "verktyg/modellanalys"], bygger_pa=["modell"], miljoer=["ma"],
                utdata=[f"ritningar/{nr} {titel}.pdf"])


STEG = [
    Steg("modell", "modeller/trebodar", [["mod", "bygg", "--format", "step"]],
         kallor=[*MODELL, "verktyg/modellanalys/modell.py"],             # modellanalysens cache skrivs också
         utdata=["modeller/trebodar/ut/trebodar.step"]),
    Steg("webb", "verktyg/modellering/webb", [["mod", "webb"]], kallor=MODELL,
         utdata=["docs/modell/index.html", "docs/modell/vyer.json", "docs/modell/trebodar.glb"]),
    Steg("kameraplan", "renderingar", [["mod", "kameraplan"]], kallor=[*MODELL, "verktyg/modellanalys"],
         bygger_pa=["modell"], miljoer=["ma"],
         utdata=["renderingar/kameraplan.pdf", "docs/renderingar/index.html", "docs/renderingar/plan.json"]),
    Steg("granskning", "verktyg/modellanalys", [["ma", "kontroll_laster.py"]],
         kallor=[f"{BER}/{nr}" for nr in ("F-01", "K-01", "K-05", "K-06")], bygger_pa=["modell"],
         utdata=["verktyg/modellanalys/granskning/ytterväggens_läge.png"]),
    ber("F-01", "berakning.py", rapport=("F-01_forutsattningar.pdf", "Förutsättningar, referenser och laster")),
    ber("AV-01", "bygg.py", rapport=("AV-01_avfallshanteringsplan.pdf", "Avfallshanteringsplan")),
    ber("TP-01", "bygg.py", kallor=[f"{BER}/IN-01/indata.toml"],
        rapport=("TP-01_tidsplan.pdf", "Tidsplan och organisation")),
    Steg("IN-01", f"{BER}/IN-01", [["mod", "inkop", "utdrag"], ["ber", "bygg.py"]],
         kallor=[*MODELL, f"{BER}/TP-01/indata.toml"], rapport=("IN-01_inkopslista.pdf", "Inköpslista")),
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
    # balkmodellen ur modellens bärverk (./mod barverk): följer modellen vid varje bygge
    Steg("K-04", f"{BER}/K-04", [["mod", "barverk"], ["ber", "berakning.py"]],
         kallor=[*MODELL, f"{BER}/F-01/indata.toml", f"{BER}/K-05/resultat.json"],
         rapport=("K-04_trastomme.pdf", "Trästomme och stabilisering")),
    ber("K-06", "berakning06.py", "berakning.py", "validering/natkonvergens.py", "rapport.py", bygger_pa=["K-05"],
        tung=True, rapport=("rapport/K-06_grund.pdf", "Bottenplatta och källarväggar"),
        incheckat=["resultat.json"]),
    ber("U-01", "berakning.py", bygger_pa=["K-05", "K-06"], tung=True,
        rapport=("U-01_bottenplatta_fukt.pdf", "Bottenplattan - temperatur och fukt under året")),
    ber("U-03", "berakning.py", tung=True,
        rapport=("U-03_takets_luftspalt.pdf", "Takets luftspalt - luftflöde, fukt och mögelrisk")),
    # ljusplanerna renderas i Blender (med tillverkarnas fotometrifiler i lokalt/el) ur hela modellen: manuellt
    Steg("U-04", f"{BER}/U-04", [["mod", "ljusplan", "plan1-golv", "plan1-bord", "kok-bank", "kallare-golv",
                                  "--projekt", f"../../{BER}/U-04/indata.toml", "--ut", f"../../{BER}/U-04"]],
         kallor=[*MODELL, MALL, "verktyg/modellanalys"], bygger_pa=["modell"], miljoer=["ma"], tung=True,
         manuell=True, rapport=("U-04_ljusplaner.pdf", "Ljusplaner - belysningsstyrka med all belysning tänd")),
    # konstruktionsritningen av trästommen ur modellens bärverk, samma utdrag som K-04 (#91)
    Steg("R-02", "verktyg/modellering", [["mod", "stomme", "ritning"]], kallor=[*MODELL, MALL],
         utdata=["ritningar/R-02 Trästomme.pdf"]),
    ritning("R-01", "Nock- och dalbalkar", bygger_pa=["K-01", "K-03", "K-05"], kallor=["modeller/balkplattor"]),
    ritning("R-05", "Källarstomme", bygger_pa=["K-05", "K-06"]),
    ritning("R-04", "Bottenplatta", bygger_pa=["R-05", "K-06"]),
    ritning("R-06", "Mellanbjälklag", bygger_pa=["R-05", "K-05", "K-06"]),
    ritning("R-03", "Bärande system i betong", bygger_pa=["R-04", "R-05", "R-06"]),
    ritning("AR-01", "Fasadsten på källarväggarna", "berakning.py", "ritningar.py"),
    ritning("AR-02", "Utsättning", bygger_pa=["R-05", "K-05"]),
    # arbetsritningen för gjutningen av mellanbjälklaget ur installationernas data och modellens snitt (#86)
    Steg("gjutning", "verktyg/modellering", [["mod", "gjutning", "ritning"]],
         kallor=[*MODELL, MALL, "verktyg/modellanalys"], bygger_pa=["modell"], miljoer=["ma"],
         utdata=["ritningar/AR-03 Gjutning av mellanbjälklaget.pdf", "ritningar/AR-04 Gjutning av bottenplattan.pdf"]),
    # installationsritningarna ur installationernas data och modellens snitt (#90)
    installation("E-01", "Elinstallation", "el"),
    installation("E-02", "Brandlarm", "brandlarm"),
    installation("VS-01", "Tappvatten", "vatten"),
    installation("VS-02", "Avlopp", "avlopp"),
    installation("VS-03", "Dagvatten och dränering", "dranering"),
    installation("VV-01", "Golvvärme", "golvvarme"),
    installation("VL-01", "Ventilation", "ventilation"),
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


def projekt(s: Steg) -> dict:
    """Rapportens projektuppgifter (revision, datum …): [projekt] i indata.toml, annars rapport/projekt.json."""
    mapp = ROT / s.mapp
    if (mapp / "indata.toml").exists():
        p = tomllib.loads((mapp / "indata.toml").read_text(encoding="utf-8")).get("projekt", {})
        if p.get("revision"):
            return p
    return json.loads((mapp / "rapport" / "projekt.json").read_text(encoding="utf-8"))


def revision(s: Steg) -> str:
    return projekt(s)["revision"]


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
    summa = hashlib.sha256(MILJO_VERSION.encode() + b"".join((ROT / k).read_bytes() for k in krav)).hexdigest()
    markering = venv / "bygg-krav.txt"
    if python.exists() and markering.exists() and markering.read_text() == summa:
        return python
    print(f"== miljö {mapp}/.venv", flush=True)
    if not python.exists():
        subprocess.run(["uv", "venv", "--python", PYTHON, str(venv)], check=True)
    subprocess.run(["uv", "pip", "install", "--python", str(python), *sum((["-r", str(ROT / k)] for k in krav), [])],
                   check=True)
    # bytekoden i förväg: annars kompileras paketen vid varje start där Python inte får skriva den
    # (PYTHONDONTWRITEBYTECODE, t.ex. i Claude Code); inte i GitHub Actions, där miljöerna är nya varje gång
    if not os.environ.get("CI"):
        subprocess.run([str(python), "-m", "compileall", "-q", "-j", "0", str(venv / "lib")],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    markering.write_text(summa)
    return python


_UTSKRIFT = threading.Lock()


def skriv(rad: str, prefix: str = "") -> None:
    with _UTSKRIFT:
        print(f"{prefix}{rad}", flush=True)


def miljoer(steg: list[Steg]) -> None:
    """Skapa eller uppdatera stegens Pythonmiljöer före bygget (inte parallellt)."""
    for s in steg:
        for m in [*s.miljoer, *(k[0] for k in s.kor)]:
            miljo(m)


def kor_steg(s: Steg, prefix: str = "") -> None:
    """Stegets kommandon (miljöerna ska finnas), med utdata rad för rad (med prefix när flera steg körs)."""
    env = {k: v for k, v in os.environ.items() if k != "PYTHONDONTWRITEBYTECODE"}   # __pycache__ ignoreras av git
    env |= {"MPLBACKEND": "Agg", "PYTHONUNBUFFERED": "1"}
    for k in s.kor:
        if k[0] in ("mod", "ma"):                  # ./mod och ./ma (ma-tjänsten) i sina egna mappar
            argv = [str(ROT / {"mod": "verktyg/modellering/mod", "ma": "verktyg/modellanalys/ma"}[k[0]]), *k[1:]]
        else:
            argv = [str(miljo(k[0])), *k[1:]]
        skriv(f"   $ {'./mod ' if k[0] == 'mod' else ''}{' '.join(k[1:])}", prefix)
        cwd = ROT / ("verktyg/modellering" if k[0] == "mod" else s.mapp)
        with subprocess.Popen(argv, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                              errors="replace") as p:
            assert p.stdout
            for rad in p.stdout:
                skriv(rad.rstrip("\n"), prefix)
        if p.returncode:
            raise subprocess.CalledProcessError(p.returncode, argv)
    if s.rapport:
        dst = rapportfil(s)
        for gammal in (ROT / "rapporter").glob(f"{s.namn}rev*.pdf"):
            gammal.unlink()
        shutil.copy(ROT / s.mapp / s.rapport[0], dst)
    if fel := saknas(s):
        raise SystemExit(f"{s.namn}: utdata saknas efter bygget: {', '.join(fel)}")


def kor_alla(steg: list[Steg], jobb: int) -> list[tuple[str, float]]:
    """Stegen i beroendeordning, parallellt när de inte bygger på varandra. Returnerar (steg, tid) i den ordning
    de blev klara; ett steg som misslyckas stoppar bygget (de som redan körs får bli klara)."""
    kvar = list(steg)
    namn = {s.namn for s in steg}
    pagar: dict[Future[None], tuple[Steg, float]] = {}
    tider: list[tuple[str, float]] = []
    fel: BaseException | None = None
    flera = len(steg) > 1 and jobb > 1
    with ThreadPoolExecutor(max_workers=jobb) as ex:
        while (kvar and fel is None) or pagar:
            igang = {s.namn for s, _ in pagar.values()}
            for s in list(kvar):
                if fel is not None or len(pagar) >= jobb:
                    break
                vantar = [b for b in s.bygger_pa if b in namn and (b in igang or any(k.namn == b for k in kvar))]
                if not vantar:
                    kvar.remove(s)
                    skriv(f"== {s.namn}{' (tung)' if s.tung else ''}")
                    pagar[ex.submit(kor_steg, s, f"[{s.namn}] " if flera else "")] = (s, time.perf_counter())
                    igang.add(s.namn)
            klara, _ = wait(pagar, return_when=FIRST_COMPLETED)
            for f in klara:
                s, t = pagar.pop(f)
                try:
                    f.result()
                except BaseException as e:   # noqa: BLE001  (stegets fel rapporteras när de pågående är klara)
                    skriv(f"   {s.namn} misslyckades: {e}")
                    fel = fel or e
                    continue
                _summor.clear()                    # steget kan ha skrivit om källor (t.ex. K-01:s hålbilder)
                spara_summa(s)
                tider.append((s.namn, time.perf_counter() - t))
                skriv(f"   {s.namn} klart ({tid(tider[-1][1])})")
    if fel is not None:
        raise SystemExit(1) from fel
    return tider


def spara_summa(s: Steg) -> None:
    stampel(s).parent.mkdir(exist_ok=True)
    stampel(s).write_text(json.dumps({"kontrollsumma": kontrollsumma(s)}, indent=1) + "\n", encoding="utf-8")


def webbplats() -> None:
    """Webbplatsens startsida och handlingarna i docs/ (startsida.py), ur det som stegen har byggt."""
    startsida.bygg(ROT, {s.namn: projekt(s) for s in STEG if s.rapport},
                   git("rev-parse", "--short", "HEAD").decode().strip())


def tid(t: float) -> str:
    return f"{t / 60:.1f} min" if t >= 60 else f"{t:.0f} s"


def main() -> None:
    a = argparse.ArgumentParser(prog="bygg", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("steg", nargs="*", help=f"stegen (standard: alla): {', '.join(STEG_NAMN)}")
    a.add_argument("--snabb", action="store_true", help="bara snabba steg; stoppa om ett tungt steg är inaktuellt")
    a.add_argument("--om", action="store_true", help="bygg om de valda stegen även om de är aktuella")
    a.add_argument("--lista", action="store_true", help="visa stegen och om de är aktuella")
    a.add_argument("--jobb", type=int, default=max(1, (os.cpu_count() or 2) // 2),
                   help="högst så många steg samtidigt (standard: hälften av kärnorna)")
    a.add_argument("--markera", action="store_true",
                   help="spara kontrollsumman för de valda stegen utan att köra dem (resultaten är aktuella)")
    arg = a.parse_args()
    if okanda := [n for n in arg.steg if n not in STEG_NAMN]:
        raise SystemExit(f"okända steg: {', '.join(okanda)} (finns: {', '.join(STEG_NAMN)})")
    if arg.lista:
        for s in STEG:
            tillstand = "aktuell" if aktuell(s) else "inaktuell" + (f" (saknas: {', '.join(saknas(s))})"
                                                                     if byggd_summa(s) == kontrollsumma(s) else "")
            print(f"{s.namn:11} {'tung ' if s.tung else '     '} {tillstand}"
                  + (" (manuellt: ./bygg " + s.namn + ")" if s.manuell else ""))
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
        if inaktuella := [s.namn for s in STEG if s.tung and not s.manuell and byggd_summa(s) != kontrollsumma(s)]:
            raise SystemExit(f"De tunga stegen {', '.join(inaktuella)} är inte räknade efter ändringarna i deras "
                             f"källor. Kör ./bygg {' '.join(inaktuella)} lokalt och checka in resultaten och "
                             f"räknat.json.")
    steg = plan(arg.steg or [s.namn for s in STEG if not s.manuell], arg.om, arg.snabb)
    t0 = time.perf_counter()
    miljoer(steg)
    tider = kor_alla(steg, arg.jobb)
    if not arg.steg:
        webbplats()
    if tider:
        print(f"\nTid {tid(time.perf_counter() - t0)} (stegen sammanlagt {tid(sum(t for _, t in tider))}): "
              + ", ".join(f"{n} {tid(t)}" for n, t in tider))
    else:
        print("Allt är aktuellt.")


if __name__ == "__main__":
    main()
