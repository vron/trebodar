"""
Webbplatsens startsida (docs/index.html) och handlingarna (docs/handlingar/, kopior av bygglovet, rapporterna och
ritningarna).
`./bygg` skriver dem efter stegen, ur det som redan är byggt:

- projektets uppgifter och handlingsförteckningen ur F-01 (beräkningar/F-01/indata.toml), bygglovets beslut och
  handlingar ur bygglov/handlingar.toml;
- rapporternas revision och datum (rapportens projektuppgifter) och ritningsbladens nummer, titel, skala, revision
  och datum (bladens JSON i beräkningar/<nr>/);
- bilderna ur renderingarnas förteckning (docs/renderingar/bilder/renderingar.json, ur releasen bilder) med
  vyernas texter, och planerna (docs/renderingar/plan.json, `./mod kameraplan`).

Mallen är startsida.html: sidans form, stil och skript, med platshållarna <!--@namn--> för det som byggs här.
Saknas bilderna (lokalt utan publicerade bilder) blir startsidan utan bilder.
"""
from __future__ import annotations

import datetime
import html
import json
import math
import re
import shutil
import tomllib
import unicodedata
import urllib.parse
from pathlib import Path

MALL = Path(__file__).with_name("startsida.html")
REPO = "https://github.com/vron/trebodar"
HJALTE = "ute-nordost"            # startsidans stora bild
MODELLBILD = "stomme"             # bilden vid länken till modellen i 3D
# bildernas urval på startsidan, i den ordningen (vyns namn eller nummer, t.ex. I03); de andra visas i sina grupper
URVAL = ["ute-sydost", "I03", "I01", "ute-nordvast", "I07", "I06", "I02", "I12", "detalj-tak", "I14", "detalj-ph5",
         "detalj-sten", "I28", "I29", "detalj-fasad", "stomme"]
GRUPPER = {"ute": "Exteriör", "inne": "Interiör", "teknik": "Stomme och teknik"}
STATUS = {"beviljad": "Beviljad", "klar": "Klar", "upprattas": "Upprättas", "inlamnad": "Inlämnad", "ej aktuell": "Ej aktuell"}
MANAD = ["januari", "februari", "mars", "april", "maj", "juni", "juli", "augusti", "september", "oktober",
         "november", "december"]
# rutornas bredd i galleriet (img sizes), så att webbläsaren väljer den minsta bilden som räcker; de två första rutorna
# är större (STOR, sätts av skriptet)
RUTA = "(max-width: 560px) 100vw, (max-width: 960px) 50vw, (max-width: 1440px) 29vw, 420px"
STOR = "(max-width: 960px) 100vw, (max-width: 1440px) 44vw, 630px"
SKALSTOCK = 5000.0                # planernas skalstock [mm]
SVG_TEXT = 300.0                  # rumsnamnens höjd i planerna [mm]

e = html.escape


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def _lank(sokvag: str) -> str:
    return urllib.parse.quote(sokvag)


def _mb(p: Path) -> str:
    return f"{p.stat().st_size / 1e6:.1f}".replace(".", ",") + " MB"


# handlingarna -----------------------------------------------------------------------------------------------------

def _blad(rot: Path, nr: str) -> list[dict]:
    """Ritningsseriens blad (huvudena ur bladens JSON) i nummerordning."""
    def nyckel(p: Path) -> list:
        return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", p.stem)]
    blad = []
    for p in sorted((rot / "beräkningar" / nr).glob(f"{nr}.*.json"), key=nyckel):
        h = json.loads(p.read_text(encoding="utf-8")).get("huvud")
        if h:
            titel = h["titel"] if isinstance(h["titel"], str) else h["titel"][-1]
            blad.append({"nr": h["nummer"], "titel": titel, "skala": h["skala"], "rev": h["rev"], "datum": h["datum"]})
    return blad


def handlingar(rot: Path, rapporter: dict[str, dict], ut: Path) -> tuple[list[tuple[str, str, list[dict]]], dict]:
    """Handlingsförteckningen: bygglovet (beslutet och handlingarna som tillhör det), F-01:s grupper (de reviderade
    bygglovsritningarna, handlingarna till tekniskt samråd och de egna underlagen) och övrigt (kameraplanen och pdf:er som inte står i förteckningen), med filerna kopierade till ut.
    rapporter: rapportens projektuppgifter per nummer (revision, datum). Returnerar grupperna och F-01:s indata."""
    shutil.rmtree(ut, ignore_errors=True)
    f01 = tomllib.loads((rot / "beräkningar" / "F-01" / "indata.toml").read_text(encoding="utf-8"))
    lov = tomllib.loads((rot / "bygglov" / "handlingar.toml").read_text(encoding="utf-8"))
    filer: dict[str, Path] = {}
    for mapp in ("rapporter", "ritningar"):
        for p in sorted((rot / mapp).glob("*.pdf")):
            nr = re.split(r"rev| ", nfc(p.stem), maxsplit=1)[0]
            filer[nr] = p
    kopior: dict[Path, str] = {}

    def fil(p: Path | None) -> dict | None:
        if p is None:
            return None
        if p not in kopior:
            dst = ut / p.parent.name / nfc(p.name)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(p, dst)
            kopior[p] = f"handlingar/{p.parent.name}/{nfc(p.name)}"
        return {"href": _lank(kopior[p]), "storlek": _mb(p)}

    def rad(nr: str, namn: str, status: str, rev: str = "", datum: str = "", notering: str = "",
            p: Path | None = None) -> dict:
        p = p or filer.pop(nr, None)
        if p is not None and p.parent.name == "rapporter" and (m := re.search(r"rev(\w+)", nfc(p.stem))):
            rev, datum = m.group(1), rapporter.get(nr, {}).get("datum", datum)
        if blad := _blad(rot, nr):
            rev, datum = max(b["rev"] for b in blad), max(b["datum"] for b in blad)
        return {"nr": nr, "namn": namn, "status": status, "rev": rev, "datum": datum, "notering": notering,
                "fil": fil(p), "blad": blad}

    grupper = [
        ("Bygglov", "Beslut D32 om bygglov och rivningslov, 2026-02-18, med handlingarna som tillhör beslutet.",
         [rad(h["nr"], h["namn"], "beviljad", h.get("rev", ""), h["datum"], h.get("notering", ""),
              p=rot / "bygglov" / h["fil"]) for h in lov["handling"]]),
        ("Bygglov, uppdaterade ritningar", "Bygglovsritningarna, reviderade efter beslutet.",
         [rad(b["nr"], b["namn"], "klar", b["rev"], b["datum"], b.get("andring", ""))
          for b in f01.get("bygglov", [])]),
        ("Tekniskt samråd", "Handlingarna till det tekniska samrådet.",
         [rad(h["nr"], h["namn"], h["status"]) for h in f01.get("handling", [])]),
        ("Egna underlag", "Utredningar och arbetsritningar för projekteringen och utförandet. Ingår inte i "
                          "handlingarna till samrådet.",
         [rad(h["nr"], h["namn"], h["status"]) for h in f01.get("ovrig", [])]),
    ]
    ovrigt = [rad(nr, nfc(p.stem).split(" ", 1)[-1], "klar") for nr, p in list(filer.items())]
    if (k := rot / "renderingar" / "kameraplan.pdf").exists():
        ovrigt.append(rad("–", "Kameraplan, renderingarnas kameror", "klar", p=k))
    if ovrigt:
        grupper.append(("Övrigt", "", ovrigt))
    return grupper, f01


def _status(s: str) -> str:
    nyckel = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return f'<span class="status s-{nyckel.replace(" ", "-")}">{e(STATUS.get(nyckel, s.capitalize()))}</span>'


def html_handlingar(grupper: list[tuple[str, str, list[dict]]]) -> str:
    ut = []
    for rubrik, text, rader in grupper:
        ut.append(f'<div class="hgrupp"><div class="hrubrik"><h3>{e(rubrik)}</h3>'
                  + (f"<p>{e(text)}</p>" if text else "") + "</div>")
        ut.append('<table class="register"><thead><tr><th>Nr</th><th>Benämning</th><th>Rev</th><th>Datum</th>'
                  '<th>Status</th><th><span class="dold">Fil</span></th></tr></thead><tbody>')
        for r in rader:
            namn = e(r["namn"])
            if r["notering"]:
                namn += f'<small>{e(r["notering"])}</small>'
            if r["blad"]:
                namn += (f'<details><summary>{len(r["blad"])} blad</summary><ol class="blad">'
                         + "".join(f'<li><span>{e(b["nr"])}</span><span>{e(b["titel"])}</span>'
                                   f'<span>{e(b["skala"])}</span><span>{e(b["rev"])}</span></li>' for b in r["blad"])
                         + "</ol></details>")
            fil = (f'<a class="pdf" href="{r["fil"]["href"]}">PDF <span>{r["fil"]["storlek"]}</span></a>'
                   if r["fil"] else '<span class="ingen">–</span>')
            ut.append(f'<tr><td class="nr">{e(r["nr"])}</td><td class="namn">{namn}</td>'
                      f'<td class="rev">{e(r["rev"]) or "–"}</td><td class="datum">{e(r["datum"]) or "–"}</td>'
                      f'<td>{_status(r["status"])}</td><td class="fil">{fil}</td></tr>')
        ut.append("</tbody></table></div>")
    return "\n".join(ut)


# bilderna ---------------------------------------------------------------------------------------------------------

def bilder(docs: Path) -> list[dict]:
    """De publicerade bilderna med vyns text, grupp (ute, inne eller teknik) och plats i urvalet, grupp för grupp:
    vyerna av huset, stommen och inomhusbilderna (I01–I30) före detaljerna."""
    try:
        manifest = json.loads((docs / "renderingar" / "bilder" / "renderingar.json").read_text(encoding="utf-8"))
        plan = json.loads((docs / "renderingar" / "plan.json").read_text(encoding="utf-8"))
    except OSError:
        return []
    ut = []
    for k in plan["kameror"]:
        b = manifest.get(k["namn"])
        if not b:
            continue
        grupp = "teknik" if k.get("teknik") else ("ute" if k["plan"] == "ute" else "inne")
        urval = next((i for i, u in enumerate(URVAL) if k["namn"] == u or k["namn"].startswith(u + "-")), None)
        ut.append({"namn": k["namn"], "text": k["text"], "grupp": grupp, "urval": urval, "ljus": b["ljus"],
                   "renderad": b["renderad"][:10], "modell": b["modell"], "storlek": b["storlek"],
                   "src": [[f"renderingar/bilder/{_lank(f)}", w] for f, w in zip(b["filer"], b["bredder"])]})
    ordning = list(GRUPPER)
    ut.sort(key=lambda b: (ordning.index(b["grupp"]), not b["namn"].startswith(("I", "ute-", "stomme")), b["namn"]))
    return ut


def _srcset(b: dict) -> str:
    return ", ".join(f"{s} {w}w" for s, w in b["src"])


def ljustext(ljus: list) -> str:
    m, d, klocka, vader = ljus
    return f"{d} {MANAD[m - 1]} kl. {klocka.replace(':', '.')}, {vader}"


def html_bild(b: dict | None, sizes: str, prioritet: bool = False) -> str:
    """Bilden med alla storlekarna (srcset); webbläsaren väljer den som räcker."""
    if b is None:
        return ""
    w, h = b["storlek"]
    ladda = 'fetchpriority="high"' if prioritet else 'loading="lazy" decoding="async"'
    return (f'<img src="{b["src"][min(1, len(b["src"]) - 1)][0]}" srcset="{_srcset(b)}" sizes="{sizes}" '
            f'width="{w}" height="{h}" alt="{e(b["text"])}" {ladda}>')


def html_galleri(bl: list[dict]) -> tuple[str, str]:
    """Bildernas rutnät och knapparna för grupperna."""
    if not bl:
        return '<p class="tom">Inga bilder publicerade ännu.</p>', ""
    figurer = []
    for i, b in enumerate(bl):
        urval = "" if b["urval"] is None else f' data-urval="{b["urval"]}"'
        figurer.append(f'<figure data-grupp="{b["grupp"]}"{urval}><button type="button" data-i="{i}" '
                       f'aria-label="Visa {e(b["text"])}">'
                       + html_bild(b, RUTA)
                       + f'</button><figcaption>{e(b["text"])}</figcaption></figure>')
    antal = {g: sum(b["grupp"] == g for b in bl) for g in GRUPPER}
    knappar = ([("urval", "Urval", sum(b["urval"] is not None for b in bl))]
               + [(g, GRUPPER[g], antal[g]) for g in GRUPPER if antal[g]] + [("alla", "Alla", len(bl))])
    knappar = [k for k in knappar if k[2]]
    return ("\n".join(figurer),
            "".join(f'<button type="button" class="chip" data-filter="{k}" aria-pressed="{str(i == 0).lower()}">'
                    f'{e(t)} <span>{n}</span></button>' for i, (k, t, n) in enumerate(knappar)))


# planerna ---------------------------------------------------------------------------------------------------------

def html_plan(p: dict, omrade: list[float], norr: list[float]) -> str:
    """Planen som SVG i modellens mm (y uppåt, som på renderingarnas sida) inom omrade (x0, x1, y0, y1; samma för
    planerna, så att de får samma skala), med rummen, norrpilen och skalstocken."""
    x0, x1, y0, y1 = omrade
    m = 700.0
    vb = (x0 - m, -y1 - m, x1 - x0 + 2 * m, y1 - y0 + 2 * m)
    ut = [f'<svg class="plan" viewBox="{" ".join(f"{v:.0f}" for v in vb)}" role="img" '
          f'aria-label="{e(p["namn"])}">']
    for y in p["ytor"]:
        ut.append(f'<path d="{y["d"]}" fill="{y["f"] or "none"}" class="{y["s"] or "kontur"}"/>')
    if p.get("trappa"):
        ut.append('<polygon class="trappa" points="' + " ".join(f"{x:.0f},{-y:.0f}" for x, y in p["trappa"])
                  + '"/>')
    for r in p["rum"]:
        ut.append(f'<text class="rum" x="{r["x"]:.0f}" y="{-r["y"]:.0f}" font-size="{SVG_TEXT:.0f}">'
                  f'{e(r["namn"])}</text>')
    # norrpilen uppe till höger (som på renderingarnas sida), N vid spetsen
    a = math.degrees(math.atan2(norr[0], norr[1]))
    ut.append(f'<g class="norr" transform="translate({vb[0] + vb[2] - 900:.0f} {vb[1] + 1100:.0f}) scale(36)">'
              f'<path transform="rotate({a:.1f})" d="M0 -18 L7 2 L0 -3 L-7 2 Z"/>'
              f'<text x="{27 * math.sin(math.radians(a)):.1f}" y="{-27 * math.cos(math.radians(a)):.1f}" '
              f'font-size="11">N</text></g>')
    # skalstocken nere till vänster: meter för meter, svart och vitt
    sx, sy, h = vb[0] + 700, vb[1] + vb[3] - 500, 110.0
    steg = SKALSTOCK / 5
    ut.append('<g class="skala">' + "".join(
        f'<rect x="{sx + i * steg:.0f}" y="{sy - h:.0f}" width="{steg:.0f}" height="{h:.0f}" '
        f'class="{"svart" if i % 2 == 0 else "vit"}"/>' for i in range(5))
        + f'<text x="{sx:.0f}" y="{sy + 300:.0f}" font-size="{SVG_TEXT * 0.85:.0f}">0</text>'
        f'<text x="{sx + SKALSTOCK:.0f}" y="{sy + 300:.0f}" font-size="{SVG_TEXT * 0.85:.0f}" '
        f'text-anchor="middle">{SKALSTOCK / 1000:g} m</text></g>')
    ut.append("</svg>")
    return "".join(ut)


def html_planer(docs: Path) -> str:
    """Plan 1 och källaren i samma skala."""
    try:
        plan = json.loads((docs / "renderingar" / "plan.json").read_text(encoding="utf-8"))
    except OSError:
        return ""
    planer = [plan["planer"][n] for n in ("plan1", "kallare") if n in plan["planer"]]
    omr = [p["omrade"] for p in planer]
    omrade = [min(o[0] for o in omr), max(o[1] for o in omr), min(o[2] for o in omr), max(o[3] for o in omr)]
    return "".join(f'<figure class="planfigur"><div class="papper">{html_plan(p, omrade, plan["norr"])}</div>'
                   f'<figcaption><span class="etikett">{e(p["namn"])}</span></figcaption></figure>' for p in planer)


# sidan ------------------------------------------------------------------------------------------------------------

def _fakta(f01: dict) -> str:
    o = f01.get("objekt", {})
    lov = re.search(r"\d{4}-\d{2}-\d{2}", o.get("lov", ""))
    register = [h for h in f01.get("handling", []) + f01.get("ovrig", []) if h["status"] != "ej aktuell"]
    klara = sum(h["status"] in ("klar", "inlämnad") for h in register)
    fakta = [
        ("Plats", "Resö, Tanums kommun"),
        ("Byggnad", "Fritidshus i ett plan med källare"),
        ("Byggnadsarea", f"{o.get('bya', '–')} m²", "fritidshus och bygglovsbefriad tillbyggnad"),
        ("Bruttoarea", f"{o.get('bta', '–')} m²"),
        ("Rum", "Allrum, kök, vardagsrum, tre sovrum och två arbetsrum", "hall, badrum och källare med teknikrum"),
        ("Fasader", "Stående granpanel, falu rödfärg och järnvitriol", "sockel av granit"),
        ("Tak", f"Bandtäckt plåt, {f01.get('sno', {}).get('alfa', 30)}°", "tre sadeltak"),
        ("Bygglov", f"Beviljat {lov.group(0)}" if lov else "Beviljat",
         f"projektering inför tekniskt samråd, {klara} av {len(register)} handlingar klara"),
    ]
    return "".join(f'<div><dt>{e(f[0])}</dt><dd>{e(f[1])}'
                   + (f"<small>{e(f[2])}</small>" if len(f) > 2 else "") + "</dd></div>" for f in fakta)


def bygg(rot: Path, rapporter: dict[str, dict], version: str) -> Path:
    """Startsidan och handlingarna i rot/docs. rapporter: rapporternas projektuppgifter per nummer."""
    docs = rot / "docs"
    grupper, f01 = handlingar(rot, rapporter, docs / "handlingar")
    bl = bilder(docs)
    namn = {b["namn"]: b for b in bl}
    hjalte = namn.get(HJALTE) or next((b for b in bl if b["grupp"] == "ute"), None)
    modellbild = namn.get(MODELLBILD) or next((b for b in bl if b is not hjalte), None)
    figurer, knappar = html_galleri(bl)
    nu = datetime.datetime.now(datetime.timezone.utc)
    data = [{k: b[k] for k in ("namn", "text", "ljus", "renderad", "modell", "src", "storlek")} for b in bl]
    for d in data:
        d["ljus"] = ljustext(d["ljus"])
    ersatt = {
        "hjalte": html_bild(hjalte, "100vw", prioritet=True),
        "hjalteklass": "" if hjalte else " utan-bild",
        "hjaltetext": (f'{e(hjalte["text"])} · {e(ljustext(hjalte["ljus"]))}' if hjalte else ""),
        "fakta": _fakta(f01),
        "knappar": knappar,
        "galleri": figurer,
        "planer": html_planer(docs),
        "modellbild": html_bild(modellbild, "(max-width: 960px) 100vw, 50vw"),
        "handlingar": html_handlingar(grupper),
        "version": e(version),
        "byggd": f"{nu.day} {MANAD[nu.month - 1]} {nu.year}",
        "repo": REPO,
        "bilddata": json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/"),
        "ruta": RUTA,
        "stor": STOR,
    }
    sida = MALL.read_text(encoding="utf-8")
    for k, v in ersatt.items():
        sida = sida.replace(f"<!--@{k}-->", v)
    if rest := re.findall(r"<!--@(\w+)-->", sida):
        raise SystemExit(f"startsida.html: okända platshållare {', '.join(rest)}")
    (docs / "index.html").write_text(sida, encoding="utf-8")
    # den gamla adressen till handlingarna leder till förteckningen på startsidan
    (docs / "handlingar" / "index.html").write_text(
        '<!doctype html><meta charset="utf-8"><title>Trebodar – handlingar</title>'
        '<meta http-equiv="refresh" content="0; url=../#handlingar"><link rel="canonical" href="../#handlingar">'
        '<a href="../#handlingar">Handlingarna</a>\n', encoding="utf-8")
    print(f"== startsidan: docs/index.html ({len(bl)} bilder, {sum(len(r) for _, _, r in grupper)} handlingar)")
    return docs / "index.html"
