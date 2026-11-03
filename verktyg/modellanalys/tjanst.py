"""
ma-tjänsten: en process som ligger kvar med biblioteken och modellen inlästa och kör ma:s kommandon och skripten
(kontroll_*.py), så att ett anrop slipper starta Python, läsa in biblioteken och modellen. Snitten av delar som inte
har ändrats återanvänds också, även när modellen har byggts om (geometri.snitt).

./ma startar tjänsten när den behövs (klient.py) och skickar kommandot dit; utdata och slutkod kommer tillbaka som
om kommandot körts i den egna processen. Ett anrop i taget, i anroparens mapp. Tjänsten avslutar sig själv efter
IDLE sekunder utan anrop och när modellanalysens kod ändras (nästa anrop startar en ny).

    ./ma tjanst            status
    ./ma tjanst stopp      avsluta
    MA_TJANST=0 ./ma …     kör i den egna processen

Protokoll (Unix-uttag, en JSON-rad per meddelande): anropet {"argv": [...], "cwd": "..."}; svaren {"ut": text},
{"fel": text} och sist {"slut": kod} eller {"omstart": true} (tjänstens kod har ändrats: anropa en ny tjänst).
"""
import contextlib
import hashlib
import io
import json
import os
import runpy
import socket
import sys
import time
import traceback
import warnings
from pathlib import Path

HERE = Path(__file__).resolve().parent
IDLE = 20 * 60                 # sekunder utan anrop innan tjänsten avslutas


def sockel():
    """Uttagets sökväg, en per utcheckning (kort: Unix-uttag tillåter knappt 104 tecken)."""
    return f"/tmp/ma-{os.getuid()}-{hashlib.sha1(str(HERE).encode()).hexdigest()[:10]}.sock"


def _kallkod():
    """Modellanalysens kod och miljö (./bygg skriver bygg-krav.txt när miljön byggs om): ändras de startas en ny tjänst."""
    return {p: p.stat().st_mtime_ns for p in [*HERE.glob("*.py"), HERE / ".venv" / "bygg-krav.txt"] if p.exists()}


class _Strom(io.TextIOBase):
    """sys.stdout/sys.stderr under ett anrop: text till klienten som JSON-rader."""

    def __init__(self, kanal, nyckel):
        self.kanal, self.nyckel = kanal, nyckel

    def writable(self):
        return True

    def write(self, s):
        if s:
            try:
                self.kanal.sendall((json.dumps({self.nyckel: s}) + "\n").encode())
            except OSError:            # klienten har gått (t.ex. avbruten); kommandot körs klart
                pass
        return len(s)

    def flush(self):
        pass


def _kor(argv):
    """Kommandot i den här processen: ett skript (*.py) eller ett av ma:s kommandon. Returnerar slutkoden."""
    try:
        if argv and argv[0].endswith(".py"):
            skript = Path(argv[0]).resolve()
            sys.argv = [str(skript), *argv[1:]]
            sys.path.insert(0, str(skript.parent))
            try:
                runpy.run_path(str(skript), run_name="__main__")
            finally:
                sys.path.remove(str(skript.parent))
        else:
            import ma
            sys.argv = ["ma", *argv]
            ma.main()
        return 0
    except SystemExit as e:
        if e.code is None or isinstance(e.code, int):
            return e.code or 0
        print(e.code, file=sys.stderr)
        return 1
    except BaseException:
        traceback.print_exc()
        return 1


def _bibliotek(mod):
    """Moduler som får ligga kvar mellan anropen: standardbiblioteket, paketen i miljön och modellanalysens egna."""
    f = getattr(mod, "__file__", None)
    if not f:
        return True
    f = str(Path(f).resolve())
    return f.startswith((sys.base_prefix, sys.prefix, str(HERE) + os.sep)) or ".venv" in f


def tjana():
    os.environ.setdefault("MPLBACKEND", "Agg")
    os.environ["MA_TJANST"] = "0"                     # underprocesser (t.ex. mod bygg) startar ingen ny tjänst
    sys.path.insert(0, str(HERE))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy  # noqa: F401
    import OCP  # noqa: F401
    import geometri  # noqa: F401
    import ma  # noqa: F401
    import modell  # noqa: F401
    import ritning  # noqa: F401
    kod = _kallkod()
    vag = sockel()
    with contextlib.suppress(FileNotFoundError):
        os.unlink(vag)
    srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    srv.bind(vag)
    inod = os.stat(vag).st_ino
    srv.listen(16)

    def slapp():
        """Ta bort uttaget (om det fortfarande är vårt) innan svaret, så att en ny tjänst kan starta direkt."""
        with contextlib.suppress(FileNotFoundError):
            if os.stat(vag).st_ino == inod:
                os.unlink(vag)
    srv.settimeout(IDLE)
    print(f"ma-tjänsten {os.getpid()} lyssnar på {vag}", flush=True)
    ut, fel, sokvag = sys.stdout, sys.stderr, list(sys.path)
    try:
        while True:
            try:
                kanal, _ = srv.accept()
            except socket.timeout:
                print("ingen aktivitet: avslutar", flush=True)
                return
            with kanal:
                rader = kanal.makefile("r", encoding="utf-8")
                fraga = json.loads(rader.readline() or "{}")
                if fraga.get("stopp"):
                    slapp()
                    kanal.sendall(b'{"slut": 0}\n')
                    return
                if fraga.get("status"):
                    kanal.sendall((json.dumps({"ut": f"ma-tjänsten {os.getpid()} på {vag}\n"}) + "\n").encode())
                    kanal.sendall(b'{"slut": 0}\n')
                    continue
                if _kallkod() != kod:
                    slapp()
                    kanal.sendall(b'{"omstart": true}\n')
                    return
                t0 = time.perf_counter()
                fore = set(sys.modules)
                sys.stdout, sys.stderr = _Strom(kanal, "ut"), _Strom(kanal, "fel")
                try:
                    os.chdir(fraga["cwd"])
                    with matplotlib.rc_context(), warnings.catch_warnings():
                        kod_ut = _kor(fraga["argv"])
                    plt.close("all")
                finally:
                    sys.stdout, sys.stderr = ut, fel
                    sys.path[:] = sokvag
                    os.chdir(HERE)
                    # skriptens egna moduler (t.ex. beräkningarnas) läses på nytt nästa gång
                    for namn in set(sys.modules) - fore:
                        if not _bibliotek(sys.modules[namn]):
                            del sys.modules[namn]
                print(f"{time.strftime('%H:%M:%S')} {' '.join(fraga['argv'])[:120]} -> {kod_ut} "
                      f"({time.perf_counter() - t0:.2f} s)", flush=True)
                with contextlib.suppress(OSError):
                    kanal.sendall((json.dumps({"slut": kod_ut}) + "\n").encode())
    finally:
        slapp()
        srv.close()


if __name__ == "__main__":
    tjana()
