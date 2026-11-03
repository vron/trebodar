"""
./ma: skickar kommandot till ma-tjänsten (tjanst.py), som startas om den inte redan körs, och skriver ut svaret.
Utan tjänsten (MA_TJANST=0, eller om den inte går att starta) körs kommandot i den egna processen. Bara
standardbiblioteket, så att anropet startar fort.
"""
import contextlib
import fcntl
import json
import os
import signal
import socket
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from tjanst import sockel  # noqa: E402  (bara standardbiblioteket på modulnivå)


def lokalt(argv):
    """Kommandot i en ny process med miljöns Python, som utan tjänsten."""
    mal = os.path.abspath(argv[0]) if argv and argv[0].endswith(".py") else os.path.join(HERE, "ma.py")
    rest = argv[1:] if argv and argv[0].endswith(".py") else argv
    os.execv(sys.executable, [sys.executable, mal, *rest])


def anslut(vag):
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        s.connect(vag)
        return s
    except OSError:
        s.close()
        return None


def starta(vag):
    """Starta tjänsten (en i taget, med lås) och vänta tills den lyssnar."""
    with open(vag + ".las", "w") as las:
        fcntl.flock(las, fcntl.LOCK_EX)
        s = anslut(vag)
        if s:
            return s
        logg = open(os.path.join(HERE, ".cache", "tjanst.log"), "a") if os.path.isdir(os.path.join(HERE, ".cache")) \
            else subprocess.DEVNULL
        subprocess.Popen([sys.executable, os.path.join(HERE, "tjanst.py")], stdin=subprocess.DEVNULL, stdout=logg,
                         stderr=subprocess.STDOUT, start_new_session=True, cwd=HERE)
        for _ in range(600):
            time.sleep(0.05)
            s = anslut(vag)
            if s:
                return s
    return None


def fraga(s, meddelande):
    """Skicka anropet och skriv ut svaren. Returnerar slutkoden, eller None om tjänsten vill startas om."""
    with s:
        s.sendall((json.dumps(meddelande) + "\n").encode())
        for rad in s.makefile("r", encoding="utf-8"):
            m = json.loads(rad)
            if "ut" in m:
                sys.stdout.write(m["ut"]); sys.stdout.flush()
            elif "fel" in m:
                sys.stderr.write(m["fel"]); sys.stderr.flush()
            elif "slut" in m:
                return m["slut"]
            elif m.get("omstart"):
                return None
    return None


def main():
    argv = sys.argv[1:]
    vag = sockel()
    if argv[:1] == ["tjanst"]:
        s = anslut(vag)
        if not s:
            print("ma-tjänsten körs inte")
            return 0
        return fraga(s, {"stopp": True} if argv[1:2] == ["stopp"] else {"status": True}) or 0
    if os.environ.get("MA_TJANST") == "0":
        lokalt(argv)
    for _ in range(3):
        s = anslut(vag) or starta(vag)
        if s is None:
            break
        kod = fraga(s, {"argv": argv, "cwd": os.getcwd()})
        if kod is not None:
            return kod
        time.sleep(0.1)               # tjänstens kod har ändrats: den avslutas, en ny startas
    lokalt(argv)


if __name__ == "__main__":
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)     # som andra kommandon när utdata stängs (t.ex. | head)
    with contextlib.suppress(KeyboardInterrupt):
        sys.exit(main())
    sys.exit(130)
