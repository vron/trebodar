"""
TP-01: tidsplan och organisation.

    python bygg.py            -> TP-01_tidsplan.pdf

Läser indata.toml (parterna, faserna och stegen) och inköpslistans indata (../IN-01/indata.toml: specialprodukterna
per fas), kontrollerar dem, ritar tidsplanerna (fig_*.svg) och sätter ihop PDF via Typst (mall.typ).
Kräver: pip install -r requirements.txt
"""
import datetime as dt
import json
import tomllib
from pathlib import Path

import matplotlib

matplotlib.use("svg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import typst  # noqa: E402
from matplotlib import font_manager  # noqa: E402

HERE = Path(__file__).parent
FONTS = HERE.parent / ".fonts"
IN = tomllib.loads((HERE / "indata.toml").read_text(encoding="utf-8"))
INKOP = tomllib.loads((HERE.parent / "IN-01" / "indata.toml").read_text(encoding="utf-8"))
MANAD = ("jan", "feb", "mar", "apr", "maj", "jun", "jul", "aug", "sep", "okt", "nov", "dec")
FARG = {"forberedelser": "#8a8a8a", "rivning": "#b5463a", "grund": "#7d6b57", "mellanbjalklag": "#5a6f86",
        "stomme": "#c98b3a", "tatt": "#2c4a6e", "installationer": "#6f8f5a", "invandigt": "#9a6f98",
        "utvandigt": "#4f8a8b"}
INK, GRA = "#1e1e1e", "#8a8a8a"
CM = 1 / 2.54
OVERSIKT = (dt.date(2026, 10, 1), dt.date(2028, 11, 1))     # hela projektet
BYGGET = (dt.date(2027, 8, 2), dt.date(2027, 12, 27))       # från byggstart till stommen, vecka för vecka
DETALJ = ("rivning", "grund", "mellanbjalklag", "stomme")

PARTER = {p["kod"]: p for p in IN["part"]}
FASER = {f["kod"]: f for f in IN["fas"]}
STEG = [s | {"start": dt.date.fromisoformat(s["start"]), "slut": dt.date.fromisoformat(s["slut"])} for s in IN["steg"]]
BYGGSTART = dt.date.fromisoformat(IN["projekt"]["byggstart"])


def tid(a: dt.date, b: dt.date) -> str:
    """Datum på svenska: 13 sep 2027, 9–13 aug 2027, 30 aug – 10 sep 2027."""
    if a == b:
        return f"{a.day} {MANAD[a.month - 1]} {a.year}"
    if (a.year, a.month) == (b.year, b.month):
        return f"{a.day}–{b.day} {MANAD[a.month - 1]} {a.year}"
    if a.year == b.year:
        return f"{a.day} {MANAD[a.month - 1]} – {b.day} {MANAD[b.month - 1]} {a.year}"
    return f"{a.day} {MANAD[a.month - 1]} {a.year} – {b.day} {MANAD[b.month - 1]} {b.year}"


def vecka(a: dt.date, b: dt.date) -> str:
    va, vb = a.isocalendar().week, b.isocalendar().week
    return f"v. {va}" if va == vb else f"v. {va}–{vb}"


def kontroll() -> list[str]:
    fel = [f"steg {s['namn']!r}: fasen {s['fas']!r} finns inte" for s in STEG if s["fas"] not in FASER]
    fel += [f"steg {s['namn']!r}: ansvarig {s['ansvarig']!r} finns inte bland parterna" for s in STEG
            if s["ansvarig"] and s["ansvarig"] not in PARTER]
    fel += [f"steg {s['namn']!r}: inblandad {p!r} finns inte bland parterna" for s in STEG
            for p in s.get("inblandade", []) if p not in PARTER]
    fel += [f"steg {s['namn']!r}: slutar före start" for s in STEG if s["slut"] < s["start"]]
    fel += [f"steg {s['namn']!r}: en milstolpe har ett datum" for s in STEG
            if s.get("milstolpe") and s["slut"] != s["start"]]
    fel += [f"IN-01 {p['kod']}: fasen {p.get('fas')!r} finns inte i tidsplanen" for p in INKOP["produkt"]
            if p.get("fas") not in FASER]
    return fel


def faserna() -> list[dict]:
    """Faserna i ordning med sina steg (i tidsordning), tid och specialprodukter ur IN-01."""
    ut = []
    for kod, f in FASER.items():
        steg = sorted((s for s in STEG if s["fas"] == kod), key=lambda s: (s["start"], s["slut"]))
        a, b = min(s["start"] for s in steg), max(s["slut"] for s in steg)
        ut.append({
            "kod": kod, "namn": f["namn"], "tid": tid(a, b), "start": a.isoformat(), "slut": b.isoformat(),
            "prel": all(s.get("prel") for s in steg if not s.get("klar")),
            "steg": [{
                "namn": s["namn"], "tid": tid(s["start"], s["slut"]), "vecka": vecka(s["start"], s["slut"]),
                "ansvarig": PARTER[s["ansvarig"]]["kort"] if s["ansvarig"] else "",
                "forslag": bool(s.get("forslag")),
                "inblandade": ", ".join(PARTER[p]["kort"] for p in s.get("inblandade", [])),
                "anm": s.get("anm", ""), "milstolpe": bool(s.get("milstolpe")), "klar": bool(s.get("klar")),
                "prel": bool(s.get("prel"))} for s in steg],
            "produkter": [{"namn": p["namn"], "status": p["status"]} for p in INKOP["produkt"] if p.get("fas") == kod],
        })
    return ut


def _stil() -> None:
    for f in sorted(FONTS.glob("*.ttf")) if FONTS.is_dir() else []:
        font_manager.fontManager.addfont(str(f))
    plt.rcParams.update({"font.family": "Carlito", "font.size": 7, "svg.fonttype": "none", "axes.linewidth": 0.5,
                         "hatch.linewidth": 0.6, "xtick.major.width": 0.5, "ytick.major.width": 0})


def _stapel(ax, rad: float, s: dict, h: float = 0.56) -> None:
    """Ett steg som stapel (preliminärt: ljusare med streck) eller en milstolpe som romb."""
    farg = FARG[s["fas"]]
    if s.get("milstolpe"):
        ax.plot(mdates.date2num(s["start"]), rad, marker="D", ms=4.2, color=farg, mec=INK, mew=0.4, zorder=4)
        return
    x0 = mdates.date2num(s["start"])
    w = mdates.date2num(s["slut"] + dt.timedelta(days=1)) - x0
    prel = bool(s.get("prel"))
    ax.barh(rad, w, left=x0, height=h, color=farg, alpha=0.45 if prel else 0.95, hatch="////" if prel else None,
            edgecolor=farg, linewidth=0.4, zorder=3)


def _uppehall(ax, a: dt.date, b: dt.date, med_namn: bool) -> None:
    for u in IN.get("uppehall", []):
        u0, u1 = dt.date.fromisoformat(u["start"]), dt.date.fromisoformat(u["slut"])
        if u1 < a or u0 > b:
            continue
        ax.axvspan(mdates.date2num(max(u0, a)), mdates.date2num(min(u1, b) + dt.timedelta(days=1)), color="#ececec",
                   zorder=1, lw=0)
        if med_namn:
            ax.text(mdates.date2num(u0 + (u1 - u0) / 2), -0.85, u["namn"], ha="center", va="center", fontsize=5.8,
                    color=GRA)


def figur_oversikt(fil: Path) -> None:
    """Hela projektet: en rad per fas, stegen som staplar, milstolparna som romber."""
    a, b = OVERSIKT
    rader = list(FASER)
    fig, ax = plt.subplots(figsize=(17.4 * CM, (1.2 + 0.52 * len(rader)) * CM))
    _uppehall(ax, a, b, med_namn=True)
    for s in STEG:
        if a <= s["start"] <= b:
            _stapel(ax, rader.index(s["fas"]), s)
    for namn, ha, dx in (("Tekniskt samråd", "right", -3), ("Startbesked", "left", 3), ("Byggstart", "center", 0),
                         ("Slutbesked", "center", 0)):
        s = next(x for x in STEG if x["namn"] == namn)
        ax.annotate(namn, (mdates.date2num(s["start"]), rader.index(s["fas"])), xytext=(dx, 6.5),
                    textcoords="offset points", ha=ha, fontsize=5.8, color=INK)
    idag = dt.date.fromisoformat(IN["projekt"]["datum"])
    ax.axvline(mdates.date2num(idag), color=INK, lw=0.6, ls=(0, (2, 1.5)), zorder=2)
    ax.text(mdates.date2num(idag), len(rader) - 0.35, " i dag", fontsize=5.8, va="bottom")
    ax.set_yticks(range(len(rader)), [FASER[k]["namn"] for k in rader])
    ax.set_ylim(len(rader) - 0.3, -1.3)
    ax.set_xlim(mdates.date2num(a), mdates.date2num(b))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: MANAD[mdates.num2date(x).month - 1][0].upper()))
    for ar in range(a.year, b.year + 1):
        x = mdates.date2num(max(a, dt.date(ar, 1, 1)))
        ax.text(x, len(rader) + 0.35, f" {ar}", fontsize=6.5, va="top", ha="left", weight="bold")
    ax.grid(axis="x", color="#dddddd", lw=0.4, zorder=0)
    ax.tick_params(axis="x", length=2, labelsize=6, pad=1.5)
    ax.tick_params(axis="y", length=0, labelsize=6.5)
    for k in ("top", "right", "left"):
        ax.spines[k].set_visible(False)
    fig.subplots_adjust(left=0.19, right=0.995, top=0.97, bottom=0.17)
    fig.savefig(fil)
    plt.close(fig)


def figur_bygget(fil: Path) -> None:
    """Från byggstart till stommen: ett steg per rad, vecka för vecka."""
    a, b = BYGGET
    steg = sorted((s for s in STEG if s["fas"] in DETALJ and a <= s["start"] <= b),
                  key=lambda s: (DETALJ.index(s["fas"]), s["start"], s["slut"]))
    fig, ax = plt.subplots(figsize=(17.4 * CM, (1.0 + 0.42 * len(steg)) * CM))
    _uppehall(ax, a, b, med_namn=False)
    for i, s in enumerate(steg):
        _stapel(ax, i, s, h=0.62)
    ax.set_yticks(range(len(steg)), [s["namn"] for s in steg])
    ax.set_ylim(len(steg) - 0.4, -0.6)
    ax.set_xlim(mdates.date2num(a), mdates.date2num(b))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO))
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: str(mdates.num2date(x).isocalendar().week)))
    ax.xaxis.tick_top()
    for m in range(a.month, b.month + 1):
        x = mdates.date2num(dt.date(a.year, m, 1))
        ax.axvline(x, color="#bbbbbb", lw=0.5, zorder=1)
        ax.text(x, len(steg) - 0.1, f" {MANAD[m - 1]} {a.year}", fontsize=6, va="top", color=GRA)
    ax.grid(axis="x", color="#e2e2e2", lw=0.4, zorder=0)
    ax.tick_params(axis="x", length=2, labelsize=5.8, pad=1.5)
    ax.tick_params(axis="y", length=0, labelsize=6.5)
    for k in ("right", "left", "bottom"):
        ax.spines[k].set_visible(False)
    fig.subplots_adjust(left=0.27, right=0.995, top=1 - 0.55 / (1.0 + 0.42 * len(steg)), bottom=0.03)
    fig.savefig(fil)
    plt.close(fig)


if fel := kontroll():
    raise SystemExit("TP-01:\n  " + "\n  ".join(fel))
_stil()
figur_oversikt(HERE / "fig_oversikt.svg")
figur_bygget(HERE / "fig_bygget.svg")
FASLISTA = faserna()
R = {
    "projekt": IN["projekt"],
    "byggstart": tid(BYGGSTART, BYGGSTART),
    "parter": [{"roll": p["roll"], "namn": p["namn"] or "–", "status": p["status"] or "–", "uppgift": p["uppgift"]}
               for p in IN["part"]],
    "milstolpar": [{"namn": s["namn"], "tid": tid(s["start"], s["slut"]), "fas": FASER[s["fas"]]["namn"],
                    "lage": "klar" if s.get("klar") else "preliminär" if s.get("prel") else "planerad"}
                   for s in sorted(STEG, key=lambda s: s["start"]) if s.get("milstolpe")],
    "uppehall": [{"namn": u["namn"], "tid": tid(dt.date.fromisoformat(u["start"]), dt.date.fromisoformat(u["slut"]))}
                 for u in IN.get("uppehall", [])],
    "faser": FASLISTA,
    "ej_bestamda": sum(1 for s in STEG if not s["ansvarig"]),
}
(HERE / "resultat.json").write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8")
pdf = HERE / f"{IN['projekt']['dokument']}_tidsplan.pdf"
typst.compile(str(HERE / "mall.typ"), output=str(pdf), font_paths=["/usr/share/fonts", str(FONTS)])
print(f"{len(STEG)} steg i {len(FASER)} faser, {R['ej_bestamda']} utan bestämd ansvarig")
print(pdf.name)
