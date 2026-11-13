"""Kontroll av U-05:s mängder (beräkningar/U-05/indata.toml) mot modellen.

    ./ma kontroll_u05.py

U-05 (värmeförluster och energibehov) har sina mängder i sin egen indata. Den här kontrollen läser modellen
(modellens senaste bygge) och jämför:

    - ytterväggarna: invändig area (ångbromsens area) och virkesandelen i regelfacken mellan syll och hammarband
      (virkets volym mot virkets och mineralullens);
    - taket: takfallens invändiga mått i plan (rektanglarnas omfång mot ångbromsens: ångbromsen börjar vid
      väggstommens insida och slutar vid nock- och dalbalkarna, så omfången får skilja 150 mm) och takbalkarnas
      andel av isoleringsskiktet (takbalkar, avväxlingar och kortlingar, utan upplagsreglarna vid nock och dal, med
      mittstolen 2C:s överramar);
    - fönstren och dörrarna: karmens yttermått ur öppningarna i indata mot karmarna i modellen;
    - takfönstren: antal;
    - gavelspetsarna: om det finns isolering ovanför hammarbandet i gavlarna (indata: gavelspets.isolerad);
    - installationsskiktet: om det finns isolering innanför stommen i ytterväggarna (indata:
      installation.isolerad) och i innertakens grupper (indata: tak.installation_isolerad);
    - markytan utanför fasaderna (marken själv, utan entréavsatsen och trapporna) mot indatas marknivåer.

Koordinater i mm som i K-05. Skriver ingenting.
"""
import sys
import tomllib
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from geometri import linjeprob  # noqa: E402
from jamfor import jamfor, redovisa  # noqa: E402
from modell import Modell  # noqa: E402

IN = tomllib.loads((ROT / "beräkningar" / "U-05" / "indata.toml").read_text(encoding="utf-8"))
MG = IN["mangder"]
m = Modell(tyst=True)
_pl = [d for d in m.delar if d.namn == "MB-B"][0]
O = np.array([_pl.bbox[0], _pl.bbox[1], _pl.bbox[5]])          # K-05:s origo i filens koordinater


def grupp(slut):
    return [d for d in m.delar if d.grupp.endswith(slut)]


def vaggar():
    ut = {}
    for v in MG["vagg"]:
        k = v["kod"]
        A = sum(d.volym for d in grupp(f"Insida {k}/Ångbroms {k}")) / 0.4 / 1e6
        vf = 0.0
        for d in grupp(f"Ytterväggar/Vägg {k}"):
            if "-B" in d.namn and d.volym < 1e6:              # stålbanden
                continue
            z0, z1 = d.bbox[2] - O[2], d.bbox[5] - O[2]
            vf += d.volym * max(0.0, min(z1, 2445.0) - max(z0, 45.0)) / (z1 - z0)
        mw = sum(d.volym for d in grupp(f"Väggisolering {k}"))
        ut[k] = dict(A=round(A, 2), f_tra=round(vf / (vf + mw), 3))
    return ut


def tak():
    """Takbalkarnas andel av isoleringsskiktet och ångbromsens omfång i plan (x0, x1, y0, y1) per takfall."""
    ut = {}
    stol = grupp("Takstolar/Takstol 2C")
    for t in MG["takfall"]:
        k = t["kod"]
        ab = grupp(f"Innertak {k}/Ångbroms tak {k}")
        omfang = [round(min(d.bbox[0] for d in ab) - O[0]), round(max(d.bbox[3] for d in ab) - O[0]),
                  round(min(d.bbox[1] for d in ab) - O[1]), round(max(d.bbox[4] for d in ab) - O[1])]
        vb = sum(d.volym for d in grupp(f"Takbalkar/Takfall {k}") if "-UR-" not in d.namn)
        if k in ("2SO", "2NV"):
            vb += sum(d.volym for d in stol if d.namn in (("2C-D01",) if k == "2SO" else ("2C-D02",)))
        vi = sum(d.volym for d in grupp(f"Takisolering {k}"))
        ut[k] = dict(omfang=omfang, f_tra=round(vb / (vb + vi), 3))
    return ut


def karmar():
    """Karmens yttermått (bredd, höjd) i modellen och ur indatas öppningar."""
    Op = IN["oppningar"]
    modell, kalla = {}, {}
    for kod, typ, b, h, van, vagg in Op["lista"]:
        if typ in ("ytterdörr", "pardörr"):
            kb, kh = b - 2 * Op["drev"], h - 2 * Op["drev"]
        else:
            under = Op["badd"] if typ in ("fönsterdörr", "skjutdörr") else Op["fog"] + Op["paforing"]
            kb, kh = b - 2 * Op["fog"], h - Op["fog"] - under
        kalla[kod] = [kb, kh]
        k = [d for d in m.delar if d.namn == f"{kod}-KARM"]
        if not k:
            continue
        bb = k[0].bbox
        dx, dy = bb[3] - bb[0], bb[4] - bb[1]
        modell[kod] = [round(max(dx, dy) if typ != "skjutdörr" else max(dx, dy)), round(bb[5] - bb[2])]
    return kalla, modell


def gavelspetsar():
    """Finns det isolering ovanför hammarbandet (z > 2 490) inom gavlarnas stomme (högst 145 djup innanför
    stommens utsida, längs gaveln)?"""
    iso = [d for d in m.delar if "Isolering" in d.sokvag and d.bbox[5] - O[2] > 2600.0]
    gavlar = [v for v in MG["lage"] if any(w["kod"] == v["kod"] and w["gavel"] for w in MG["vagg"])]
    for v in gavlar:
        o, u, L = np.array(v["o"], float), np.array(v["u"], float), v["L"]
        n = np.array([u[1], -u[0]])                          # utåt
        for d in iso:
            lo, hi = np.array(d.bbox[:2]) - O[:2], np.array(d.bbox[3:5]) - O[:2]
            hörn = np.array([[x, y] for x in (lo[0], hi[0]) for y in (lo[1], hi[1])]) - o
            s_u, s_n = hörn @ u, hörn @ n
            if s_u.min() >= -1 and s_u.max() <= L + 1 and s_n.min() >= -146 and s_n.max() <= 1:
                return True
    return False


def installationsskikt():
    """Finns det isolering i installationsskiktet? Väggarna: isolering högst 50 mm innanför stommens insida, längs
    väggen och på plan 1 (väggar med installationsskikt). Taket: isolering i innertakens grupper."""
    iso = [d for d in m.delar if "isolering" in d.sokvag.lower()]
    typ = {v["kod"]: v["typ"] for v in MG["vagg"]}
    vagg = False
    for v in MG["lage"]:
        skikt = dict(IN["vaggtyp"][typ[v["kod"]]]["skikt"]) if v["kod"] in typ else {}
        if "installation" not in skikt:
            continue
        dj = skikt["stomme"]
        o, u, L = np.array(v["o"], float), np.array(v["u"], float), v["L"]
        n = np.array([u[1], -u[0]])                          # utåt
        for d in iso:
            if d.bbox[2] - O[2] < -10.0 or d.bbox[5] - O[2] > 2600.0:
                continue
            lo, hi = np.array(d.bbox[:2]) - O[:2], np.array(d.bbox[3:5]) - O[:2]
            hörn = np.array([[x, y] for x in (lo[0], hi[0]) for y in (lo[1], hi[1])]) - o
            s_u, s_n = hörn @ u, hörn @ n
            if s_u.min() >= -1 and s_u.max() <= L + 1 and s_n.max() <= -dj + 2 and s_n.min() >= -dj - 50:
                vagg = True
                break
        if vagg:
            break
    return dict(vagg=vagg, tak=any("Innertak" in d.sokvag for d in iso))


def markniva():
    """Markytan 100 mm utanför panelen på en fjärdedel, hälften och tre fjärdedelar av varje fasad (överkanten av
    marken och fyllningen); punkter under entréavsatsen och trapporna hoppas över."""
    mark = [d for d in m.valj("Mark") if not any(w in d.sokvag.lower() for w in ("entréavsats", "trapp"))]
    over = [d for d in m.valj("Mark") if any(w in d.sokvag.lower() for w in ("entréavsats", "trapp"))]
    ut, kalla = {}, {}
    for v in MG["lage"]:
        k = v["kod"]
        o, u, L = np.array(v["o"], float), np.array(v["u"], float), v["L"]
        n = np.array([u[1], -u[0]])                          # utåt
        prof = np.array(IN["mark"]["niva"][k], float)
        for f in (0.25, 0.5, 0.75):
            p = o + u * L * f + n * (65 + 100)
            a, b = np.r_[p, -5000.0] + O, np.r_[p, 2000.0] + O
            if linjeprob(m, over, a, b):
                continue
            iv = linjeprob(m, mark, a, b)
            topp = max((t1 for t0, t1, *_ in iv), default=None)
            if topp is None:
                continue
            ut[f"{k} {f:.2f}"] = round(-5000.0 + topp)
            kalla[f"{k} {f:.2f}"] = round(float(np.interp(L * f, prof[:, 0], prof[:, 1])))
    return kalla, ut


fel = []
mv = vaggar()
fel += jamfor({v["kod"]: dict(A=v["A"], f_tra=v["f_tra"]) for v in MG["vagg"]}, mv, tol=0.006, vag="vagg",
              utelamna=("2SV.f_tra",))          # 2SV: mest skjutdörr, små fält; antaget 0,30 i indata
fel += [f"vagg.{k}.A: källfilen {v['A']}, modellen {mv[k]['A']}" for v in MG["vagg"] for k in [v["kod"]]
        if abs(v["A"] - mv[k]["A"]) > 0.05]
fel = [f_ for f_ in fel if not (".A:" in f_ and "f_tra" not in f_ and abs(float(f_.split()[-3].rstrip(",")) -
                                                                          float(f_.split()[-1])) <= 0.05)]
mt = tak()
fel += jamfor({t["kod"]: t["f_tra"] for t in MG["takfall"]}, {k: v["f_tra"] for k, v in mt.items()}, tol=0.006,
              vag="takfall.f_tra")
plan = {t["kod"]: [min(r[0] for r in t["plan"]), max(r[1] for r in t["plan"]), min(r[2] for r in t["plan"]),
                   max(r[3] for r in t["plan"])] for t in MG["takfall"]}
fel += jamfor(plan, {k: v["omfang"] for k, v in mt.items()}, tol=150, vag="takfall.plan (omfång x0, x1, y0, y1)")
kk, km = karmar()
fel += jamfor({k: v for k, v in kk.items() if k in km}, km, tol=1.5, vag="karm")
fel += [f"karm.{k}: ingen karm i modellen" for k in kk if k not in km]
n_tf = len([d for d in m.delar if d.namn.endswith("-KARM") and d.namn.startswith("TF")])
fel += jamfor(IN["takfonster"]["antal"], n_tf, tol=0, vag="takfonster.antal")
fel += jamfor(IN["gavelspets"]["isolerad"], gavelspetsar(), vag="gavelspets.isolerad")
mi = installationsskikt()
fel += jamfor(IN["installation"]["isolerad"], mi["vagg"], vag="installation.isolerad")
fel += jamfor(IN["tak"]["installation_isolerad"], mi["tak"], vag="tak.installation_isolerad")
mk, mm_ = markniva()
fel += jamfor(mk, mm_, tol=150, vag="mark.niva")
sys.exit(redovisa("U-05 (värmeförluster och energibehov)", fel))
