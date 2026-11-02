"""Elritningar ur modellens elinstallation (utdraget ur trebodar.hus.installationer.el): elplanen för ett plan
(armaturer, apparater och dosor med symboler, tändgruppernas styrning från brytare och dimrar, rören i väggar och
innertak) och rören i ett bjälklag (ingjutna rör med utsättningsmått, dosor och var rören går upp i väggarna), på
planritningar ur modellens snitt (STEP-filen). A3.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle

from .planritning import BLAD, plan

SKALA = 75.0
R_SYMBOL = 110.0                 # symbolernas radie i planet [mm] (1,5 mm på bladet i 1:75)
TANDFARGER = ("#c2410c", "#1d4ed8", "#15803d", "#7e22ce", "#b45309", "#0e7490", "#be123c", "#4d7c0f")
ROR_INNE, ROR_BJALKLAG = "#6b7280", "#ea580c"


def _tandfarg(utdrag: dict, grupp: str) -> str:
    return TANDFARGER[sorted(utdrag["tandgrupper"]).index(grupp) % len(TANDFARGER)]


def _symbol(ax: plt.Axes, slag: str, x: float, y: float, farg: str = "#111111") -> None:
    """Symbolerna (i stil med SS-EN 60617): spot (cirkel med kors), brytare (cirkel med streck), dimmer (dessutom
    en pil), uttag (halvcirkel med streck), dosa (fyrkant), ingjutningsdosa (fyrkant med diagonal)."""
    r = R_SYMBOL
    if slag == "tubspot":
        # spot på stam (riktad): cirkel med kors och en kort stam mot väggen/taket
        ax.add_patch(Circle((x, y), r, fc="white", ec=farg, lw=1.0, zorder=5))
        for k in (1, -1):
            ax.plot([x - r * 0.7, x + r * 0.7], [y - k * r * 0.7, y + k * r * 0.7], color=farg, lw=0.8, zorder=6)
        ax.add_patch(Circle((x, y), r * 0.35, fc=farg, ec="none", zorder=6))
    elif slag in ("spot", "armatur"):
        ax.add_patch(Circle((x, y), r, fc="white", ec=farg, lw=1.0, zorder=5))
        for k in (1, -1):
            ax.plot([x - r * 0.7, x + r * 0.7], [y - k * r * 0.7, y + k * r * 0.7], color=farg, lw=0.8, zorder=6)
    elif slag in ("brytare", "dimmer"):
        ax.add_patch(Circle((x, y), r * 0.6, fc="white", ec=farg, lw=1.0, zorder=5))
        ax.plot([x + r * 0.42, x + r * 1.3], [y + r * 0.42, y + r * 1.3], color=farg, lw=1.0, zorder=6)
        if slag == "dimmer":
            ax.add_patch(FancyArrowPatch((x - r * 0.9, y - r * 0.9), (x + r * 0.9, y + r * 0.9), arrowstyle="-|>",
                                         mutation_scale=6, color=farg, lw=0.6, zorder=6))
    elif slag == "uttag":
        ax.add_patch(Circle((x, y), r * 0.7, fc="white", ec=farg, lw=1.0, zorder=5))
        ax.plot([x - r, x + r], [y, y], color=farg, lw=1.0, zorder=6)
    else:
        s = r * 0.7
        ax.add_patch(Rectangle((x - s, y - s), 2 * s, 2 * s, fc="white", ec=farg, lw=1.0, zorder=5))
        if slag == "ingjutningsdosa":
            ax.plot([x - s, x + s], [y - s, y + s], color=farg, lw=0.8, zorder=6)


def _etikett(ax: plt.Axes, x: float, y: float, text: str, farg: str = "#111111", dx: float = 160.0,
             dy: float = 160.0, storlek: float = 6.0) -> None:
    ax.text(x + dx, y + dy, text, fontsize=storlek, color=farg, zorder=7,
            bbox={"boxstyle": "round,pad=0.1", "fc": "white", "ec": "none", "alpha": 0.8})


def _ror_i_planet(ax: plt.Axes, vag: list[list[float]], farg: str, lw: float, stil: str = "-") -> None:
    xs = [p[0] for p in vag]
    ys = [p[1] for p in vag]
    ax.plot(xs, ys, color=farg, lw=lw, ls=stil, zorder=3, solid_capstyle="round")


def _i_bjalklag(vag: list[list[float]], z0: float, z1: float) -> list[tuple[int, int]]:
    """Rörets delar inom bjälklaget (z0 ≤ z ≤ z1): index (första, sista) för sammanhängande följder av
    brytpunkter."""
    delar: list[tuple[int, int]] = []
    start = None
    for i, p in enumerate(vag + [[0.0, 0.0, z1 + 1e9]]):
        inne = z0 - 1.0 <= p[2] <= z1 + 1.0
        if inne and start is None:
            start = i
        elif not inne and start is not None:
            if i - 1 > start:
                delar.append((start, i - 1))
            start = None
    return delar


def _ram(fig: plt.Figure, titel: str, undertitel: str) -> None:
    fig.text(10 / BLAD[0], 287 / BLAD[1], titel, fontsize=15, weight="bold", va="top")
    fig.text(10 / BLAD[0], 278 / BLAD[1], undertitel, fontsize=8.5, va="top", color="#333333")
    fig.text(10 / BLAD[0], 6 / BLAD[1], f"Skala 1:{SKALA:g} (A3). Ur modellens elinstallation "
             "(modeller/trebodar/hus/installationer/el) med `./mod el ritning`.", fontsize=7.5, color="#555555")


def _armaturtabell(fig: plt.Figure, utdrag: dict, x_mm: float, y_mm: float) -> float:
    """Armaturtyperna med antal; returnerar y under tabellen [mm]."""
    antal: dict[str, int] = {}
    for p in utdrag["punkter"].values():
        if p["slag"] == "lampa":
            antal[p["typ"]] = antal.get(p["typ"], 0) + 1
    fig.text(x_mm / BLAD[0], y_mm / BLAD[1], "Armaturer", fontsize=9, weight="bold", va="top")
    y = y_mm - 5.5
    for kod, n in antal.items():
        t = utdrag["typer"][kod]
        fig.text(x_mm / BLAD[0], y / BLAD[1], f"{n} st {t['tillverkare']} {t['namn']} (art. {t['artikel']})",
                 fontsize=7.5, va="top")
        fig.text((x_mm + 4) / BLAD[0], (y - 4.2) / BLAD[1],
                 f"{t['ljusflode']:g} lm, {t['effekt']:g} W, {t['fargtemperatur']:g} K, strålvinkel "
                 f"{t['stralvinkel']:g}°, håltagning Ø{t['hal_d']:g}", fontsize=7, va="top", color="#444444")
        y -= 10.0
    return y


def _teckenforklaring(fig: plt.Figure, x_mm: float, y_mm: float, rader: list[tuple[str, str]]) -> float:
    """Symbolerna med förklaring, ritade i en egen liten axel."""
    fig.text(x_mm / BLAD[0], y_mm / BLAD[1], "Teckenförklaring", fontsize=9, weight="bold", va="top")
    h = 6.0 * len(rader)
    ax = fig.add_axes((x_mm / BLAD[0], (y_mm - 6 - h) / BLAD[1], 10 / BLAD[0], h / BLAD[1]))
    ax.set_xlim(-300, 300)
    ax.set_ylim(-h * SKALA / 2 * 0.8, h * SKALA / 2 * 0.8)
    ax.set_aspect("equal")
    ax.axis("off")
    for i, (slag, text) in enumerate(rader):
        ym = (len(rader) / 2 - i - 0.5) * 6.0 * SKALA * 0.8
        if slag in ("styrning", "ror", "ror_bjalklag"):
            farg = {"styrning": TANDFARGER[0], "ror": ROR_INNE, "ror_bjalklag": ROR_BJALKLAG}[slag]
            ax.plot([-250, 250], [ym, ym], color=farg, lw=1.6 if slag == "ror_bjalklag" else 0.9,
                    ls=(0, (4, 2)) if slag == "styrning" else "-")
        else:
            _symbol(ax, slag, 0.0, ym)
        fig.text((x_mm + 12) / BLAD[0], (y_mm - 6 - (i + 0.5) * 6.0) / BLAD[1], text, fontsize=7.5, va="center")
    return y_mm - 8 - h


def elplan(utdrag: dict, delar: list[dict], omrade: tuple[float, float, float, float], titel: str, rubrik: str,
           ut: Path, plan_nr: int = 1) -> None:
    """Elplanen för ett plan: punkterna på planet, styrningen och rören i väggar och innertak."""
    fig = plt.figure(figsize=(BLAD[0] / 25.4, BLAD[1] / 25.4))
    ax = plan(fig, (8.0, 14.0), omrade, delar, rubrik, SKALA, alfa=0.45)
    rummen = {k for k, r in utdrag["rum"].items() if r["plan"] == plan_nr}
    punkter = {k: p for k, p in utdrag["punkter"].items() if k.split("-")[0] in rummen}
    # rören i väggar och innertak (de i bjälklaget ritas på bjälklagets ritning)
    for k, r in utdrag["ror"].items():
        if r["fran"] in punkter or r["till"] in punkter:
            delar_ovan = [[p for p in r["vag"] if p[2] > -1.0]]
            for d in delar_ovan:
                if len(d) > 1:
                    _ror_i_planet(ax, d, ROR_INNE, 0.8)
                    m = d[len(d) // 2 - 1:len(d) // 2 + 1]
                    xm, ym = (m[0][0] + m[-1][0]) / 2, (m[0][1] + m[-1][1]) / 2
                    ax.text(xm, ym, f"{k} Ø{r['diameter']:g}", fontsize=5, color=ROR_INNE, ha="center",
                            va="bottom", zorder=4)
    # styrningen: bågar från brytaren eller dimmern till varje lampa i tändgrupperna
    for k, p in punkter.items():
        for g in p.get("styr", []):
            farg = _tandfarg(utdrag, g)
            for lid in utdrag["tandgrupper"][g]["lampor"]:
                q = utdrag["punkter"][lid]
                ax.add_patch(FancyArrowPatch(tuple(p["punkt"][:2]), tuple(q["punkt"][:2]),
                                             connectionstyle="arc3,rad=0.18", arrowstyle="-", lw=0.7, color=farg,
                                             ls=(0, (4, 2)), zorder=2))
    for k, p in punkter.items():
        t = utdrag["typer"][p["typ"]]
        x, y = p["punkt"][:2]
        if p["slag"] == "lampa":
            farg = _tandfarg(utdrag, p["tand"])
            r = p["riktning"]
            if abs(r[2]) < 0.999:                  # riktad: pil i ljusets riktning (i planet), från symbolens kant
                lp = (r[0] ** 2 + r[1] ** 2) ** 0.5
                ux, uy = r[0] / lp, r[1] / lp
                ax.add_patch(FancyArrowPatch((x + R_SYMBOL * ux, y + R_SYMBOL * uy),
                                             (x + 4.5 * R_SYMBOL * ux, y + 4.5 * R_SYMBOL * uy), arrowstyle="-|>",
                                             mutation_scale=8, color=farg, lw=1.0, zorder=6))
            _symbol(ax, t["symbol"], x, y, farg)
            _etikett(ax, x, y, f"{k}\n{p['tand']}", farg)
        else:
            _symbol(ax, t["symbol"], x, y)
            styr = ", ".join(p.get("styr", []))
            text = f"{k} {t['slag']}" + (f"\nstyr {styr}" if styr else "")
            if p["yta"] == "vagg" and "over_golv" in p:
                text += f"\n{p['over_golv']:.0f} över golvet"
            _etikett(ax, x, y, text, dy=-420.0)
    _ram(fig, titel, "Armaturer, apparater och dosor; tändgruppernas styrning (streckade bågar) och rör i väggar och "
                     "innertak. Rören i bjälklagen på bjälklagens ritningar.")
    y = _teckenforklaring(fig, 222.0, 262.0, [("spot", "Infälld spotlight (armatur)"),
                                               ("tubspot", "Spot på stam, riktad (pil: ljusets riktning)"),
                                               ("dimmer", "Dimmer"),
                                               ("brytare", "Strömbrytare"), ("uttag", "Vägguttag"),
                                               ("kopplingsdosa", "Kopplingsdosa"),
                                               ("styrning", "Styrning: brytare/dimmer – tändgrupp"),
                                               ("ror", "Rör i vägg och innertak")])
    y = _armaturtabell(fig, utdrag, 222.0, y - 4)
    fig.text(222 / BLAD[0], (y - 4) / BLAD[1], "Tändgrupper", fontsize=9, weight="bold", va="top")
    y -= 9.5
    for g, tg in utdrag["tandgrupper"].items():
        if not any(lid in punkter for lid in tg["lampor"]):
            continue
        fig.text(222 / BLAD[0], y / BLAD[1], f"{g}: {tg['namn']} ({len(tg['lampor'])} lampor, "
                 f"{'dimbar' if tg['dimbar'] else 'ej dimbar'}), styrs av {', '.join(tg['styrs_av'])}",
                 fontsize=7.5, va="top", color=_tandfarg(utdrag, g))
        y -= 4.6
    ut.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ut, dpi=200)
    plt.close(fig)


def bjalklag(utdrag: dict, delar: list[dict], vaggar: list[dict], omrade: tuple[float, float, float, float],
             z: tuple[float, float], titel: str, rubrik: str, ut: Path) -> None:
    """Rören ingjutna i ett bjälklag (z0–z1): rörens lägen med utsättningsmått i brytpunkterna, dosorna och var
    rören går upp ur bjälklaget (in i väggarna ovanför, plan 1:s väggar blekt som bakgrund)."""
    fig = plt.figure(figsize=(BLAD[0] / 25.4, BLAD[1] / 25.4))
    ax = plan(fig, (8.0, 14.0), omrade, delar, rubrik, SKALA, bara=("Hus/Mellanbjälklag",), alfa=0.6)
    for d in vaggar:
        if d["sokvag"].startswith(("Hus/Stomme", "Hus/Invändigt")):
            for yta in d["ytor"]:
                xs, ys = zip(*yta[0])
                ax.fill(xs, ys, fc="none", ec="#9ca3af", lw=0.3, zorder=1)
    rader = []
    for k, r in utdrag["ror"].items():
        for i0, i1 in _i_bjalklag(r["vag"], *z):
            d = r["vag"][i0:i1 + 1]
            _ror_i_planet(ax, d, ROR_BJALKLAG, 1.6)
            for p in d[1:-1]:
                ax.plot(p[0], p[1], "o", ms=2.2, color=ROR_BJALKLAG, zorder=4)
                ax.text(p[0] + 90, p[1] - 90, f"{p[0]:.0f}\n{p[1]:.0f}", fontsize=4.5, color="#7c2d12", zorder=5,
                        va="top")
            xm, ym = (d[0][0] + d[1][0]) / 2, (d[0][1] + d[1][1]) / 2
            ax.text(xm, ym + 80, f"{k} Ø{r['diameter']:g}", fontsize=6, color=ROR_BJALKLAG, ha="center", zorder=5)
            # där röret går upp ur bjälklaget (in i väggen ovanför)
            for i, j in ((i0, i0 - 1), (i1, i1 + 1)):
                if 0 <= j < len(r["vag"]) and r["vag"][j][2] > z[1] + 1.0:
                    ande = r["vag"][i]
                    ax.add_patch(Circle((ande[0], ande[1]), 70, fc=ROR_BJALKLAG, ec="none", zorder=5))
                    ax.text(ande[0] + 120, ande[1] + 60, "upp", fontsize=5.5, color="#7c2d12", zorder=5)
            rader.append((k, r))
    for k, p in utdrag["punkter"].items():
        if p["yta"] == "tak" and p["ref"] == "MB" or p["slag"] == "dosa" and p["punkt"][2] <= z[1] + 1:
            x, y = p["punkt"][0], p["punkt"][1]
            _symbol(ax, utdrag["typer"][p["typ"]]["symbol"], x, y)
            _etikett(ax, x, y, f"{k}\n{utdrag['typer'][p['typ']]['namn']}", dy=-380.0)
    _ram(fig, titel, "Rör ingjutna i bjälklaget (mitt i betongen) med utsättningsmått x, y [mm] (K-05) i "
                     "brytpunkterna; ● röret går upp i väggen ovanför.")
    y = _teckenforklaring(fig, 222.0, 262.0, [("ror_bjalklag", "Rör ingjutet i bjälklaget"),
                                               ("ingjutningsdosa", "Ingjutningsdosa (i källarens tak)")])
    fig.text(222 / BLAD[0], (y - 4) / BLAD[1], "Rör", fontsize=9, weight="bold", va="top")
    y -= 9.5
    for k, r in rader:
        fig.text(222 / BLAD[0], y / BLAD[1], f"{k}: {r['typ']} från {r['fran']} till {r['till']}, "
                 f"{r['langd'] / 1000:.1f} m, böjar {r['bojar']:.0f}°", fontsize=7.5, va="top")
        y -= 4.6
    ut.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ut, dpi=200)
    plt.close(fig)


def lista(utdrag: dict, kontroll: tuple[list[str], list[str]]) -> str:
    """Punktlista, tändgrupper, rörlista och kontrollen som markdown."""
    fel, anm = kontroll
    rad = ["# Elinstallationen", "", f"{len(utdrag['punkter'])} punkter, {len(utdrag['tandgrupper'])} tändgrupper, "
           f"{len(utdrag['ror'])} rör ({sum(r['langd'] for r in utdrag['ror'].values()) / 1000:.1f} m).", "",
           f"## Kontroll: {len(fel)} fel, {len(anm)} anmärkningar", ""]
    rad += [f"- FEL {f}" for f in fel] + [f"- {a}" for a in anm]
    rad += ["", "## Punkter", "", "| Id | Slag | Typ | x | y | z | Yta | Tändgrupp / styr |",
            "|---|---|---|---|---|---|---|---|"]
    for k, p in utdrag["punkter"].items():
        x, y, z = p["punkt"]
        rad.append(f"| {k} | {p['slag']} | {utdrag['typer'][p['typ']]['namn']} | {x:.0f} | {y:.0f} | {z:.0f} | "
                   f"{p['yta']} {p['ref']} | {p.get('tand', ', '.join(p.get('styr', [])))} |")
    rad += ["", "## Tändgrupper", "", "| Id | Namn | Lampor | Styrs av |", "|---|---|---|---|"]
    for k, t in utdrag["tandgrupper"].items():
        rad.append(f"| {k} | {t['namn']} | {', '.join(t['lampor'])} | {', '.join(t['styrs_av'])} |")
    rad += ["", "## Rör", "", "| Id | Typ | Från | Till | Längd [m] | Böjar [°] |", "|---|---|---|---|---|---|"]
    for k, r in utdrag["ror"].items():
        rad.append(f"| {k} | {r['typ']} | {r['fran']} | {r['till']} | {r['langd'] / 1000:.2f} | {r['bojar']:.0f} |")
    return "\n".join(rad) + "\n"

