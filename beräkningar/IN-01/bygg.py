"""
IN-01: inköpslistan, specialprodukterna med status.

    python bygg.py            -> IN-01_inkopslista.pdf

Läser indata.toml och modellens utdrag (modeller/trebodar/ut/inkop.json, som `./mod inkop utdrag` skriver: de märkta
produkternas instanser i modellen), kontrollerar att de stämmer och sätter ihop PDF via Typst (mall.typ).
Kräver: pip install typst
"""
import json
import re
import tomllib
from collections import Counter
from pathlib import Path

import typst

HERE = Path(__file__).parent
UTDRAG = HERE.parents[1] / "modeller" / "trebodar" / "ut" / "inkop.json"
ARENDE = "https://github.com/vron/trebodar/issues/"
ALLMAN = ("ej vald", "ej valt", "förenklat")       # modellens beskrivning av en produkt som inte är vald

IN = tomllib.loads((HERE / "indata.toml").read_text(encoding="utf-8"))
MODELL = json.loads(UTDRAG.read_text(encoding="utf-8"))
STATUS, ROLLER, SKEDEN = list(IN["status"]), IN["roller"], IN["skeden"]


def typ(t: str) -> str:
    """Instansens typ i listan: modellens beskrivning utan Onshape-modellens namn."""
    return re.sub(r" \([^()]* i Onshape\)$", "", t)


def produkt(p: dict) -> dict:
    """Produkten i listan, med modellens instanser grupperade efter typ."""
    inst = MODELL.get(p["kod"], [])
    varianter = Counter(typ(i["typ"]) for i in inst)
    allman = p["status"] != STATUS[0] and any(a in t.lower() for t in varianter for a in ALLMAN)
    return {
        "kod": p["kod"], "namn": p["namn"], "vald": p.get("vald", ""), "status": p["status"],
        "ansvarig": ROLLER[p["ansvarig"]], "skede": SKEDEN[p["skede"]],
        "antal": str(len(inst)) if inst else p["omfattning"],
        "detaljer": [x for x in (p.get("dokument", ""), p.get("anm", ""),
                                 f"Leverantör: {p['leverantor']}" if p.get("leverantor") else "",
                                 "Modellen visar en allmän typ." if allman else "") if x],
        "arenden": [{"nr": n, "url": f"{ARENDE}{n}"} for n in p.get("arende", [])],
        "varianter": [{"typ": t, "antal": n, "id": ", ".join(i["namn"] for i in inst if typ(i["typ"]) == t)}
                      for t, n in varianter.items()],
    }


def kontroll() -> list[str]:
    """Listan mot sig själv och mot modellen."""
    koder = [p["kod"] for p in IN["produkt"]]
    fel = [f"{k}: står {n} gånger i listan" for k, n in Counter(koder).items() if n > 1]
    fel += [f"{k}: i modellen men inte i listan" for k in MODELL if k not in koder]
    for p in IN["produkt"]:
        k = p["kod"]
        fel += [f"{k}: {f} {p.get(f)!r} finns inte" for f, tillatna in
                (("status", STATUS), ("ansvarig", ROLLER), ("skede", SKEDEN)) if p.get(f) not in tillatna]
        if p.get("status") != STATUS[0] and not p.get("vald"):
            fel.append(f"{k}: status {p.get('status')!r} men ingen vald produkt (vald)")
        if k in MODELL and "omfattning" in p:
            fel.append(f"{k}: finns i modellen men anger omfattning")
        if k not in MODELL and "omfattning" not in p:
            fel.append(f"{k}: finns inte i modellen och anger ingen omfattning")
    return fel


if fel := kontroll():
    raise SystemExit("IN-01 stämmer inte med modellen eller sig själv:\n  " + "\n  ".join(fel))
grupper: dict[str, list[dict]] = {}
for p in IN["produkt"]:
    grupper.setdefault(p["grupp"], []).append(produkt(p))
alla = [p for ps in grupper.values() for p in ps]
oversikt = [{"skede": s, "antal": [sum(p["skede"] == s and p["status"] == st for p in alla) for st in STATUS]}
            for s in SKEDEN.values()]
R = {
    "projekt": IN["projekt"],
    "status": [{"namn": s, "text": t} for s, t in IN["status"].items()],
    "roller": list(ROLLER.values()),
    "skeden": list(SKEDEN.values()),
    "oversikt": [r | {"summa": sum(r["antal"])} for r in oversikt if sum(r["antal"])],
    "summa": [sum(r["antal"][i] for r in oversikt) for i in range(len(STATUS))],
    "grupper": [{"namn": g, "produkter": ps} for g, ps in grupper.items()],
    "produkter": len(alla),
    "instanser": sum(len(v) for v in MODELL.values()),
}
(HERE / "resultat.json").write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8")
pdf = HERE / f"{IN['projekt']['dokument']}_inkopslista.pdf"
typst.compile(str(HERE / "mall.typ"), output=str(pdf), font_paths=["/usr/share/fonts", str(HERE.parent / ".fonts")])
print(f"{len(alla)} specialprodukter, {R['instanser']} instanser i modellen: "
      + ", ".join(f"{n} {s}" for s, n in zip(STATUS, R["summa"]) if n))
print(pdf.name)
