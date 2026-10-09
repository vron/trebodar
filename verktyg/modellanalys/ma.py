"""
ma – modellanalys av STEP-sammanställningar. Kör via ./ma <kommando> (använder .venv).

    ./ma oversikt                              omfång, grupper, färger
    ./ma trad [--djup 3] [--under Källaren]    sammanställningsträdet med id, storlek och färg
    ./ma delar "K Pillar" [--sortera x]        tabell över delar (urval: delsträng, glob, #id, #a-b)
    ./ma info "#42" [--horn]                   exakt geometri: plana ytor med läge, cylindrar, hörn
    ./ma vy [--fran iso,ovan] [--klipp "z<13000"] [--delar …] [--spok …] [--markera …] [--rutnat]
    ./ma snitt z=12500 [--bortom -3000] [--omrade x0,x1,y0,y1] [--koordinater]
    ./ma linje "x=1000,y=2000"                 alla delar längs en linje (skikttjocklekar)
    ./ma linje 0,0,0 1000,0,0                  … eller mellan två punkter
    ./ma punkt 1000,2000,12500                 vilka delar innehåller / är närmast punkten
    ./ma matt "Mittenplatta" "K Pillar"        minsta avstånd mellan två urval
    ./ma krock [urval] [urval2]                överlappande solider
    ./ma jamfor [annan.step]                   skillnader mot annan fil / föregående version

Gemensamt: --fil väg/till.step (standard ../../modeller/trebodar.step), --delar/--utom för urval.
Bilder hamnar i ut/ om inte --ut anges. Enhet mm.
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

from modell import CACHE, Modell  # noqa: E402

UT = HERE / "ut"


def mm(v):
    return f"{v:,.1f}".replace(",", " ")


def hexf(f):
    return "#%02x%02x%02x" % tuple(int(round(255 * c)) for c in f[:3])


def slug(s):
    return re.sub(r"[^\w.=-]+", "_", s).strip("_")[:60] or "bild"


def utfil(args, standard):
    ut = Path(args.ut) if getattr(args, "ut", None) else UT / standard
    ut.parent.mkdir(parents=True, exist_ok=True)
    return ut


def kort(d):
    """Delens namn och närmaste grupp, t.ex. 'R 2NO btm  ‹2NO <1>›'."""
    delar = d.sokvag.split("/")
    return f"{delar[-1]}  ‹{delar[-2]}›" if len(delar) > 1 else delar[-1]


def storlek_txt(s):
    return " × ".join(f"{v:.0f}" for v in s)


def urval(m, args, attr="delar"):
    return m.valj(getattr(args, attr, None), getattr(args, "utom", None))


def kontrollera(delar, uttryck):
    if not delar:
        sys.exit(f"inga delar matchar {uttryck!r}")


# ---- kommandon ---------------------------------------------------------------------------------

def k_oversikt(m, args):
    b = m.bbox()
    print(f"Fil:   {m.fil}  ({m.fil.stat().st_size / 1e6:.1f} MB, hash {m.hash})")
    print(f"Rot:   {m.rot} – {len(m.delar)} delar i {sum(n['grupp'] for n in m.noder)} grupper, "
          f"{m.index['nat']['trianglar']:,} trianglar".replace(",", " "))
    for i, a in enumerate("xyz"):
        print(f"  {a}: {mm(b[i]):>12} … {mm(b[i + 3]):>12}   ({mm(b[i + 3] - b[i])})")
    print(f"\nGrupper (djup ≤ {args.djup}):")
    for n, delar in m.grupper():
        if n["djup"] > args.djup or not delar:
            continue
        g = m.bbox(delar)
        print(f"  {'  ' * n['djup']}{n['namn'] or m.rot:<40.40} {len(delar):>4} delar   "
              f"{storlek_txt(np.array(g[3:]) - np.array(g[:3])):>24}   min ({g[0]:.0f}, {g[1]:.0f}, {g[2]:.0f})")
    toppdelar = [d for d in m.delar if "/" not in d.sokvag]
    if toppdelar:
        print("\nDelar direkt under roten:")
        for d in toppdelar:
            print(f"  #{d.id:<4} {d.namn:<36.36} {storlek_txt(d.storlek):>24}")
    print("\nFärger:")
    farger = {}
    for d in m.delar:
        farger.setdefault(hexf(d.farg), []).append(d)
    for f, ds in sorted(farger.items(), key=lambda x: -len(x[1])):
        namn = sorted({d.namn.split(" [")[0] for d in ds})
        print(f"  {f}  {len(ds):>4}  {', '.join(namn)[:110]}")


def k_trad(m, args):
    rot = None
    if args.under:
        traff = [n for n in m.noder if n["grupp"] and args.under.lower() in n["sokvag"].lower()]
        if not traff:
            sys.exit(f"ingen grupp matchar {args.under!r}")
        rot = traff[0]
    d0 = rot["djup"] if rot else 0
    pre = (rot["sokvag"] + "/") if rot and rot["sokvag"] else ""
    for n in m.noder:
        if rot and not (n is rot or n["sokvag"].startswith(pre)):
            continue
        rel = n["djup"] - d0
        if rel > args.djup:
            continue
        ind = "  " * rel
        if n["grupp"]:
            delar = [d for d in m.delar if d.sokvag.startswith(n["sokvag"] + "/" if n["sokvag"] else "")]
            print(f"{ind}▸ {n['namn'] or m.rot}  ({len(delar)} delar)")
        elif not args.grupper:
            d = m.del_(n["id"])
            print(f"{ind}  #{d.id:<4} {d.namn:<40.40} {storlek_txt(d.storlek):>22}  {hexf(d.farg)}")


def k_delar(m, args):
    delar = m.valj(args.urval, args.utom)
    kontrollera(delar, args.urval)
    nyckel = {"x": lambda d: d.bbox[0], "y": lambda d: d.bbox[1], "z": lambda d: d.bbox[2],
              "volym": lambda d: -d.volym, "namn": lambda d: d.sokvag, "id": lambda d: d.id}[args.sortera]
    print(f"{'id':>5}  {'dx × dy × dz':>22}  {'xmin':>9} {'ymin':>9} {'zmin':>9}  {'xmax':>9} {'ymax':>9} "
          f"{'zmax':>9}  {'vol m³':>8}  färg     sökväg")
    for d in sorted(delar, key=nyckel):
        b = d.bbox
        print(f"#{d.id:>4}  {storlek_txt(d.storlek):>22}  {b[0]:9.1f} {b[1]:9.1f} {b[2]:9.1f}  {b[3]:9.1f} "
              f"{b[4]:9.1f} {b[5]:9.1f}  {d.volym / 1e9:8.4f}  {hexf(d.farg)}  {d.sokvag}")
    g = m.bbox(delar)
    print(f"\n{len(delar)} delar, total volym {sum(d.volym for d in delar) / 1e9:.4f} m³, "
          f"omfång x {g[0]:.1f}…{g[3]:.1f}  y {g[1]:.1f}…{g[4]:.1f}  z {g[2]:.1f}…{g[5]:.1f}")


def k_info(m, args):
    from geometri import horn, ytanalys
    delar = m.valj(args.urval, args.utom)
    kontrollera(delar, args.urval)
    for d in delar[: args.max]:
        b = d.bbox
        print(f"#{d.id}  {d.sokvag}")
        print(f"  färg {hexf(d.farg)}   solider {d.solider}   ytor {d.ytor}")
        print(f"  bbox  x {b[0]:.3f} … {b[3]:.3f}   y {b[1]:.3f} … {b[4]:.3f}   z {b[2]:.3f} … {b[5]:.3f}")
        print(f"  storlek {d.storlek[0]:.3f} × {d.storlek[1]:.3f} × {d.storlek[2]:.3f}   volym {d.volym / 1e9:.5f} m³   "
              f"area {d.area / 1e6:.3f} m²   tyngdpunkt ({d.tyngdpunkt[0]:.1f}, {d.tyngdpunkt[1]:.1f}, {d.tyngdpunkt[2]:.1f})")
        s = m.form(d)
        plan, cyl, ovr = ytanalys(s)
        if plan:
            print("  plana ytor (utåtnormal, läge, antal, area):")
            for (n, dd), (k, A, c) in sorted(plan.items(), key=lambda x: (x[0][0], x[0][1])):
                ax = [i for i in range(3) if abs(n[i]) > 0.999999]
                if ax:
                    i = ax[0]
                    lage = f"{'+-'[int(n[i] < 0)]}{'xyz'[i]}   {'xyz'[i]} = {dd * n[i]:.3f}"
                else:
                    lage = f"n=({n[0]:.4f}, {n[1]:.4f}, {n[2]:.4f})  d={dd:.3f}  t.ex. ({c[0]:.1f}, {c[1]:.1f}, {c[2]:.1f})"
                print(f"    {lage:<60} {k:>3} st  {A / 1e6:9.4f} m²")
        if cyl:
            print("  cylindrar (axelriktning, axelpunkt, radie, antal):")
            for (ax_, p, r), (k, A) in sorted(cyl.items(), key=lambda x: (x[0][2], x[0][1])):
                print(f"    r={r:<9g} Ø{2 * r:<9g} axel ({ax_[0]:.3f}, {ax_[1]:.3f}, {ax_[2]:.3f}) genom "
                      f"({p[0]:.2f}, {p[1]:.2f}, {p[2]:.2f})  {k} st")
        for t, (k, A) in ovr.items():
            print(f"  {t}: {k} ytor, {A / 1e6:.4f} m²")
        if args.horn:
            h = horn(s)
            print(f"  hörn ({len(h)} unika):")
            for p in h[: args.horn]:
                print(f"    ({p[0]:.3f}, {p[1]:.3f}, {p[2]:.3f})")
        print()


def k_vy(m, args):
    from vy import rendera
    delar = urval(m, args)
    kontrollera(delar, args.delar)
    spok = m.valj(args.spok) if args.spok else []
    if args.spok_ovriga:
        valda = {d.id for d in m.valj(args.spok_ovriga)}
        spok = [d for d in m.delar if d.id not in valda]
        delar = m.delar if not args.delar else delar + [d for d in spok if d not in delar]
    markera = m.valj(args.markera) if args.markera else []
    etiketter = m.valj(args.etiketter) if args.etiketter else []
    fokus = m.valj(args.fokus) if args.fokus else None
    fran = args.fran.split(";") if ";" in args.fran else (
        args.fran.split(",") if not re.fullmatch(r"-?[\d.]+,-?[\d.]+", args.fran) else [args.fran])
    w, h = (int(v) for v in args.storlek.lower().split("x"))
    ut = utfil(args, f"vy_{slug('_'.join(fran) + ('_' + '_'.join(args.klipp) if args.klipp else '') + ('_' + args.delar if args.delar else ''))}.png")
    t = time.time()
    rendera(m, ut, delar, fran=fran, klipp=args.klipp or [], spok=spok, markera=markera, etiketter=etiketter,
            storlek=(w, h), rutnat=args.rutnat, perspektiv=args.perspektiv, fokus=fokus, kanter=not args.inga_kanter,
            titel=args.titel, zoom=args.zoom, lock=not args.utan_lock)
    print(f"{ut}   ({len(delar)} delar, {time.time() - t:.1f} s)")


def k_snitt(m, args):
    from geometri import Plan
    from ritning import rita_snitt
    plan = Plan.tolka(args.plan)
    if args.origo:
        plan.flytta(*[float(v) for v in args.origo.split(",")])
    delar = urval(m, args)
    kontrollera(delar, args.delar)
    omrade = [float(v) for v in args.omrade.split(",")] if args.omrade else None
    ut = utfil(args, f"snitt_{slug(plan.namn)}{'_b' + str(int(args.bortom)) if args.bortom else ''}"
                     f"{'_' + slug(args.delar) if args.delar else ''}.png")
    sd = rita_snitt(m, plan, delar, ut, bortom=args.bortom, omrade=omrade, etiketter=not args.inga_etiketter,
                    rutnat=args.rutnat, titel=args.titel, dpi=args.dpi)
    print(f"{ut}\n")
    a, b = plan.axlar
    print(f"{'id':>5}  {a + ' från':>10} {a + ' till':>10}  {b + ' från':>10} {b + ' till':>10}  {'area m²':>9}  del")
    for s in sorted(sd, key=lambda s: s.del_.sokvag):
        g = s.yta if not s.yta.is_empty else None
        if g is not None:
            x0, y0, x1, y1 = g.bounds
            A = g.area / 1e6
        else:
            P = np.concatenate(s.linjer)
            (x0, y0), (x1, y1) = P.min(0), P.max(0)
            A = 0.0
        print(f"#{s.del_.id:>4}  {x0:10.1f} {x1:10.1f}  {y0:10.1f} {y1:10.1f}  {A:9.4f}  {kort(s.del_)}")
    if args.koordinater:
        print()
        for s in sd:
            for poly in ([s.yta] if s.yta.geom_type == "Polygon" else list(getattr(s.yta, "geoms", []))):
                if poly.is_empty:
                    continue
                p = poly.simplify(0.01)
                print(f"#{s.del_.id} {s.del_.namn}  yttre: " + " ".join(f"({x:.1f},{y:.1f})" for x, y in p.exterior.coords[:-1]))
                for r in p.interiors:
                    print(f"    hål: " + " ".join(f"({x:.1f},{y:.1f})" for x, y in r.coords[:-1]))
    if args.json:
        data = [{"id": s.del_.id, "sokvag": s.del_.sokvag,
                 "ytor": [[list(map(list, p.exterior.coords))] + [list(map(list, r.coords)) for r in p.interiors]
                          for p in ([s.yta] if s.yta.geom_type == "Polygon" else list(getattr(s.yta, "geoms", [])))
                          if not p.is_empty],
                 "linjer": [l.tolist() for l in s.linjer]} for s in sd]
        Path(args.json).write_text(json.dumps({"plan": plan.namn, "axlar": plan.axlar, "delar": data}), encoding="utf-8")
        print(f"\nkoordinater → {args.json}")


def _linje_punkter(m, args):
    from geometri import tal3
    if args.p2:
        return tal3(args.p1), tal3(args.p2)
    v = dict(re.findall(r"([xyz])\s*=\s*(-?[\d.]+)", args.p1))
    fri = [a for a in "xyz" if a not in v]
    if len(fri) != 1:
        sys.exit("ange två koordinater, t.ex. 'x=1000,y=2000' (linje längs z), eller två punkter")
    b = m.bbox()
    i = "xyz".index(fri[0])
    p1 = np.array([float(v.get(a, 0)) for a in "xyz"]); p2 = p1.copy()
    p1[i], p2[i] = b[i] - 10, b[i + 3] + 10
    return p1, p2


def k_linje(m, args):
    from geometri import linjeprob
    p1, p2 = _linje_punkter(m, args)
    delar = urval(m, args)
    r = (p2 - p1) / np.linalg.norm(p2 - p1)
    ax = int(np.argmax(np.abs(r))) if np.max(np.abs(r)) > 0.999999 else None
    print(f"Linje ({p1[0]:.1f}, {p1[1]:.1f}, {p1[2]:.1f}) → ({p2[0]:.1f}, {p2[1]:.1f}, {p2[2]:.1f})\n")
    seg = linjeprob(m, delar, p1, p2)
    if not seg:
        print("träffar inga delar")
        return
    kol = f"{'xyz'[ax] + ' från':>12} {'xyz'[ax] + ' till':>12}" if ax is not None else f"{'från (x,y,z)':>26} {'till (x,y,z)':>26}"
    print(f"{kol}  {'tjocklek':>9}  del")
    slut = None
    for t0, t1, d, a, b in seg:
        if slut is not None and t0 - slut > 0.05:
            print(f"{'':>{len(kol)}}  {t0 - slut:9.1f}  · tomrum")
        if ax is not None:
            print(f"{a[ax]:12.1f} {b[ax]:12.1f}  {t1 - t0:9.1f}  #{d.id} {kort(d)}")
        else:
            print(f"({a[0]:7.1f},{a[1]:7.1f},{a[2]:7.1f}) ({b[0]:7.1f},{b[1]:7.1f},{b[2]:7.1f})  {t1 - t0:9.1f}  #{d.id} {kort(d)}")
        slut = t1 if slut is None else max(slut, t1)


def k_punkt(m, args):
    from geometri import punktfraga, tal3
    p = tal3(args.punkt)
    inne, nara = punktfraga(m, urval(m, args), p, args.n)
    print(f"Punkt ({p[0]:.1f}, {p[1]:.1f}, {p[2]:.1f})")
    print("  inuti: " + (", ".join(f"#{d.id} {kort(d)}" for d in inne) if inne else "–"))
    print("  närmast:")
    for dist, d, q in nara:
        print(f"    {dist:9.1f} mm  till ({q[0]:.1f}, {q[1]:.1f}, {q[2]:.1f})  #{d.id} {kort(d)}")


def k_matt(m, args):
    from geometri import minsta_avstand
    A, B = m.valj(args.a, args.utom), m.valj(args.b, args.utom)
    kontrollera(A, args.a); kontrollera(B, args.b)
    r = minsta_avstand(m, A, B)
    if not r:
        sys.exit("kunde inte beräkna avstånd")
    dist, a, b, pa, pb = r
    print(f"Minsta avstånd {dist:.3f} mm")
    print(f"  #{a.id} {a.sokvag}: ({pa[0]:.3f}, {pa[1]:.3f}, {pa[2]:.3f})")
    print(f"  #{b.id} {b.sokvag}: ({pb[0]:.3f}, {pb[1]:.3f}, {pb[2]:.3f})")
    print(f"  Δ = ({pb[0] - pa[0]:.3f}, {pb[1] - pa[1]:.3f}, {pb[2] - pa[2]:.3f})")


def k_krock(m, args):
    from geometri import krockar
    A = m.valj(args.a, args.utom)
    B = m.valj(args.b, args.utom) if args.b else None

    def fr(k, n):
        if k % 50 == 0:
            print(f"\r  {k}/{n} par …", end="", file=sys.stderr, flush=True)
    r = krockar(m, A, B, args.minvol, fr)
    print("\r", end="", file=sys.stderr)
    if not r:
        print("Inga överlapp.")
    for vol, a, b, bb in r:
        print(f"{vol / 1e6:10.3f} dm³   #{a.id} {kort(a)}  ×  #{b.id} {kort(b)}\n"
              f"{'':16}x {bb[0]:.0f}…{bb[3]:.0f}  y {bb[1]:.0f}…{bb[4]:.0f}  z {bb[2]:.0f}…{bb[5]:.0f}")


def k_jamfor(m, args):
    if args.annan:
        g = Modell(args.annan)
    else:
        aldre = sorted((p for p in CACHE.glob(f"{m.fil.stem}-*") if p != m.cache and (p / "index.json").exists()),
                       key=lambda p: p.stat().st_mtime)
        if not aldre:
            sys.exit("ingen tidigare version i cachen – ange en annan fil")
        idx = json.loads((aldre[-1] / "index.json").read_text(encoding="utf-8"))
        print(f"jämför med cachad version {aldre[-1].name} ({idx['skapad']})\n")

        class G:
            pass
        g = G()
        from modell import Del
        g.delar = [Del(**{k: (tuple(v) if isinstance(v, list) else v) for k, v in d.items()}) for d in idx["delar"]]
    gamla = {d.sokvag: d for d in g.delar}
    nya = {d.sokvag: d for d in m.delar}
    for s in sorted(set(gamla) - set(nya)):
        print(f"– borttagen   {s}")
    for s in sorted(set(nya) - set(gamla)):
        print(f"+ ny          #{nya[s].id} {s}   {storlek_txt(nya[s].storlek)}")
    for s in sorted(set(nya) & set(gamla)):
        a, b = gamla[s], nya[s]
        db = np.abs(np.array(a.bbox) - np.array(b.bbox)).max()
        dv = b.volym - a.volym
        andr = []
        if db > args.tol:
            andr.append("bbox " + " ".join(f"{'xyz'[i % 3]}{'01'[i // 3]}{b.bbox[i] - a.bbox[i]:+.1f}"
                                            for i in range(6) if abs(b.bbox[i] - a.bbox[i]) > args.tol))
        if abs(dv) > max(1.0, 1e-6 * abs(a.volym)):
            andr.append(f"volym {dv / 1e9:+.5f} m³")
        if tuple(a.farg) != tuple(b.farg):
            andr.append(f"färg {hexf(a.farg)}→{hexf(b.farg)}")
        if andr:
            print(f"~ ändrad      #{b.id} {s}: {'; '.join(andr)}")


# ---- argument ----------------------------------------------------------------------------------

def main():
    gem = argparse.ArgumentParser(add_help=False)
    gem.add_argument("--fil", help="STEP-fil (standard: modeller/trebodar.step)")
    gem.add_argument("--utom", help="urval att utesluta")
    p = argparse.ArgumentParser(prog="ma", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="kommando", required=True)

    a = sp.add_parser("oversikt", parents=[gem]); a.add_argument("--djup", type=int, default=2)
    a = sp.add_parser("trad", parents=[gem]); a.add_argument("--djup", type=int, default=99)
    a.add_argument("--under"); a.add_argument("--grupper", action="store_true", help="bara grupper")
    a = sp.add_parser("delar", parents=[gem]); a.add_argument("urval", nargs="?")
    a.add_argument("--sortera", default="id", choices=["id", "x", "y", "z", "volym", "namn"])
    a = sp.add_parser("info", parents=[gem]); a.add_argument("urval")
    a.add_argument("--horn", type=int, nargs="?", const=200, default=0, help="lista hörnpunkter (max N)")
    a.add_argument("--max", type=int, default=10)

    a = sp.add_parser("vy", parents=[gem])
    a.add_argument("--delar", help="visa bara dessa"); a.add_argument("--fran", default="iso",
                   help="iso, iso-no, ovan, fram, +x-y+z, 'az,el' … flera med komma (eller ; för az,el)")
    a.add_argument("--klipp", action="append", help="'z<13000', 'x>-3000', 'o=… n=…' (kan upprepas)")
    a.add_argument("--spok", help="visa genomskinligt"); a.add_argument("--spok-ovriga", help="allt utom detta som spöken")
    a.add_argument("--markera", help="färga rött"); a.add_argument("--etiketter", help="namnetiketter på dessa")
    a.add_argument("--fokus", help="kameran ramar in dessa"); a.add_argument("--zoom", type=float, default=1.0)
    a.add_argument("--rutnat", action="store_true", help="koordinatrutnät i mm")
    a.add_argument("--perspektiv", action="store_true"); a.add_argument("--inga-kanter", action="store_true")
    a.add_argument("--utan-lock", action="store_true", help="inga snittlock vid klipp")
    a.add_argument("--storlek", default="1600x1200"); a.add_argument("--titel"); a.add_argument("--ut")

    a = sp.add_parser("snitt", parents=[gem]); a.add_argument("plan", help="z=12500, x=-3000, 'o=x,y,z n=nx,ny,nz'")
    a.add_argument("--delar"); a.add_argument("--bortom", type=float, default=0.0,
                   help="visa geometri bortom snittet, mm med tecken (t.ex. -3000 = tittar mot -normal)")
    a.add_argument("--omrade", help="u0,u1,v0,v1 i ritningens koordinater")
    a.add_argument("--origo", help="u,v: ritningens origo i globala koordinater (alla 2D-mått blir relativa)")
    a.add_argument("--rutnat", type=float, help="rutnätsavstånd mm"); a.add_argument("--inga-etiketter", action="store_true")
    a.add_argument("--koordinater", action="store_true", help="skriv ut snittytornas hörn")
    a.add_argument("--json", help="spara snittgeometrin som JSON"); a.add_argument("--dpi", type=int, default=160)
    a.add_argument("--titel"); a.add_argument("--ut")

    a = sp.add_parser("linje", parents=[gem]); a.add_argument("p1"); a.add_argument("p2", nargs="?")
    a.add_argument("--delar")
    a = sp.add_parser("punkt", parents=[gem]); a.add_argument("punkt"); a.add_argument("--delar")
    a.add_argument("-n", type=int, default=6)
    a = sp.add_parser("matt", parents=[gem]); a.add_argument("a"); a.add_argument("b")
    a = sp.add_parser("krock", parents=[gem]); a.add_argument("a", nargs="?"); a.add_argument("b", nargs="?")
    a.add_argument("--minvol", type=float, default=1000.0, help="mm³")
    a = sp.add_parser("jamfor", parents=[gem]); a.add_argument("annan", nargs="?")
    a.add_argument("--tol", type=float, default=0.5)

    # koordinatlistor som börjar med minus (-5000,6000,13900) får inte tolkas som flaggor
    args = p.parse_args([" " + a if re.match(r"^-\d[\d.]*[,;]", a) else a for a in sys.argv[1:]])
    m = Modell(args.fil)
    globals()["k_" + args.kommando](m, args)


if __name__ == "__main__":
    main()
