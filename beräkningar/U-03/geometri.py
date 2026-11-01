"""Takets luftspalt som nätverk.

Taket delas längs y i remsor, ungefär ett fack (c/c 600) breda. I varje remsa går luftspalten längs x från takfot
över nockar och dalar till takfot. Noderna ligger vid nockar och dalar och vid takfönstrens kanter. Grenarna är:
  fall      spalten längs ett takfall mellan två noder eller mellan takfoten (ute) och en nod, med celler för värme och fukt
  samling   kanal längs en nock eller dal mellan remsorna (om ströläkten inte går över balken), utan celler
  gavel     öppning i gaveln vid en nocks eller dals ände, mot det fria
  omluft    kanal längs y ovanför och nedanför ett takfönster, genom uppehåll i ströläkten, till grannfacken
Ett takfönster bryter facken det står i: utan omluftning slutar spalten blint vid fönstrets över- och underkant.
Koordinater som i K-05 (mm), höjder från fasadlivets överkant (dalarna). Grenens riktning a → b är positiv.
"""
import math

import numpy as np


def nock_och_dallinjer(byggnader):
    """[(typ, x, y0, y1)]: nockar mitt i varje byggnad, dalar där två byggnader möts."""
    linjer = [("N", (b["x"][0] + b["x"][1]) / 2, *b["y"]) for b in byggnader]
    for b1 in byggnader:
        for b2 in byggnader:
            if b1["x"][1] == b2["x"][0]:
                y0, y1 = max(b1["y"][0], b2["y"][0]), min(b1["y"][1], b2["y"][1])
                if y1 > y0:
                    linjer.append(("D", b1["x"][1], y0, y1))
    return linjer


def remsor(byggnader, fonster, bredd):
    """Remsornas mitt och bredd [mm]: varje zon mellan två gavel- eller fönsterlägen delas i lika breda remsor ≤ bredd."""
    ys = sorted({v for b in byggnader for v in b["y"]} | {v for f in fonster for v in f["y"]})
    ut = []
    for y0, y1 in zip(ys[:-1], ys[1:]):
        n = math.ceil((y1 - y0) / bredd - 1e-9)
        w = (y1 - y0) / n
        ut += [(y0 + (k + 0.5) * w, w) for k in range(n)]
    return ut


def bygg(I, samling=False, gavel=False, omluft=False):
    """Nätverket för ett fall. samling: kanaler längs nockar och dalar; gavel: öppningarna i [tak].gavlar;
    omluft: uppehåll i ströläkten ovanför och nedanför takfönstren."""
    T, S = I["tak"], I["stromning"]
    lut = math.radians(T["lutning"])
    h = I["uppbyggnad"]["spalt"] / 1000
    cc, b_kanal = T["cc"] / 1000, (T["cc"] - T["lakt_b"]) / 1000
    az_x = T["azimut_x"]
    az = {"+x": az_x % 360, "-x": (az_x + 180) % 360, "+y": (az_x - 90) % 360, "-y": (az_x + 90) % 360}
    B = sorted(I["byggnad"], key=lambda b: b["x"][0])
    F = T.get("fonster", [])
    linjer = nock_och_dallinjer(B)
    R = remsor(B, F, T["remsa"])
    nc = I["modell"]["celler"]
    tan, cos = math.tan(lut), math.cos(lut)
    yR = [yc for yc, _ in R]
    # remsor i fönstren och närmaste remsa på var sida
    i_fon = {k: [s for s, y in enumerate(yR) if f["y"][0] < y < f["y"][1]] for k, f in enumerate(F)}
    grann = {k: [min(ss) - 1, max(ss) + 1] for k, ss in i_fon.items()}

    noder, nod_z, nyckel = [], [], {}
    G = dict(a=[], b=[], typ=[], L=[], A=[], Dh=[], bredd=[], hojd=[], zeta=[], dz=[], az_a=[], az_b=[], remsa=[], fasad=[], x0=[], x1=[])

    def gren(a, b, typ, L, A, Dh, bredd, zeta, dz, az_a=np.nan, az_b=np.nan, remsa=-1, fasad=np.nan, x0=np.nan, x1=np.nan, hojd=h):
        for k, v in dict(a=a, b=b, typ=typ, L=L, A=A, Dh=Dh, bredd=bredd, hojd=hojd, zeta=zeta, dz=dz, az_a=az_a, az_b=az_b,
                         remsa=remsa, fasad=fasad, x0=x0, x1=x1).items():
            G[k].append(v)

    def zx(x, bygg_):
        return min(x - bygg_["x"][0], bygg_["x"][1] - x) * tan

    for s, (yc, w) in enumerate(R):
        finns = [b for b in B if b["y"][0] < yc < b["y"][1]]
        kedjor, k = [], []
        for b in finns:                                          # byggnader som ligger dikt an bildar en kedja
            if k and k[-1]["x"][1] != b["x"][0]:
                kedjor.append(k); k = []
            k.append(b)
        if k:
            kedjor.append(k)
        n_kan = w / 1000 / cc                                    # antal fack i remsan
        A_fl = n_kan * b_kanal * h
        Dh = 2 * b_kanal * h / (b_kanal + h)
        for k in kedjor:
            u = T["utsprang"]
            pkt = [("T", k[0]["x"][0] - u, -u * tan)]
            for i, b in enumerate(k):
                # fönster och omluftningspunkter i byggnaden, i x-ordning
                extra = []
                for kf, f in enumerate(F):
                    if not (b["x"][0] < f["x"][0] < b["x"][1]):
                        continue
                    if s in i_fon[kf]:
                        extra += [("F0", f["x"][0]), ("F1", f["x"][1])]
                    elif omluft and s in grann[kf]:
                        extra += [("O", f["x"][0]), ("O", f["x"][1])]
                xm = (b["x"][0] + b["x"][1]) / 2
                for typ, x in sorted(extra + [("N", xm)], key=lambda t: t[1]):
                    pkt.append((typ, x, zx(x, b)))
                if i < len(k) - 1:
                    pkt.append(("D", b["x"][1], 0.0))
            pkt.append(("T", k[-1]["x"][1] + u, -u * tan))
            idx = []
            for typ, x, z in pkt:
                if typ == "T":
                    idx.append(-1)
                else:
                    nyckel[(s, typ[0], x)] = len(noder)
                    idx.append(len(noder)); noder.append((s, typ, x, yc)); nod_z.append(z / 1000)
            for j in range(len(pkt) - 1):
                (ta, xa, za), (tb, xb, zb) = pkt[j], pkt[j + 1]
                if ta == "F0" and tb == "F1":                     # fönstret
                    continue
                L = (xb - xa) / cos / 1000
                zeta = sum(S["zeta_takfot"] if t == "T" else S["zeta_bock"] / 2 if t in ("N", "D") else 0.0 for t in (ta, tb))
                fasad = az["-x"] if zb > za else az["+x"]          # stigande mot +x: takfallet vettar mot −x
                gren(idx[j], idx[j + 1], 0, L, A_fl, Dh, b_kanal, zeta, (zb - za) / 1000,
                     az_a=az["-x"] if ta == "T" else np.nan, az_b=az["+x"] if tb == "T" else np.nan,
                     remsa=s, fasad=fasad, x0=xa, x1=xb)

    if samling:                                                  # kanal över balken mellan remsornas noder
        bs, hs = S["samling_b"] / 1000, S["samling_h"] / 1000
        for typ, x, y0, y1 in linjer:
            ss = [s for s, y in enumerate(yR) if y0 < y < y1 and (s, typ, x) in nyckel]
            for s1, s2 in zip(ss[:-1], ss[1:]):
                gren(nyckel[(s1, typ, x)], nyckel[(s2, typ, x)], 1, (yR[s2] - yR[s1]) / 1000, bs * hs,
                     2 * bs * hs / (bs + hs), bs, S["zeta_samling"], 0.0, hojd=hs)

    if gavel:
        bg = S["gavel_b"] / 1000
        for gv in T["gavlar"]:
            typ, x, y0, y1 = next(l for l in linjer if l[1] == gv["x"])
            ss = [s for s, y in enumerate(yR) if y0 < y < y1]
            s = ss[0] if gv["ande"] == "y0" else ss[-1]
            gren(nyckel[(s, typ, x)], -1, 2, bg, bg * h, 2 * bg * h / (bg + h), bg, S["zeta_gavel"], 0.0,
                 az_b=az["-y"] if gv["ande"] == "y0" else az["+y"])

    if omluft:                                                   # längs y vid fönstrets under- och överkant
        lo = S["omluft_l"] / 1000
        for kf, f in enumerate(F):
            ss = [grann[kf][0]] + i_fon[kf] + [grann[kf][1]]
            for x, t in ((f["x"][0], "F"), (f["x"][1], "F")):
                kedja = [nyckel[(s, "O" if s in grann[kf] else "F", x)] for s in ss]
                for (s1, n1), (s2, n2) in zip(zip(ss, kedja[:-1]), zip(ss[1:], kedja[1:])):
                    gren(n1, n2, 3, (yR[s2] - yR[s1]) / 1000, lo * h, 2 * lo * h / (lo + h), lo, S["zeta_omluft"], 0.0)

    G = {k: np.array(v, dtype=int if k in ("a", "b", "typ", "remsa") else float) for k, v in G.items()}
    fall = np.where(G["typ"] == 0)[0]
    return dict(noder=noder, z=np.array(nod_z), gren=G, fall=fall, remsor=R, linjer=linjer, celler=nc, h=h,
                bredd=np.array([R[s][1] / 1000 for s in G["remsa"][fall]]))


if __name__ == "__main__":
    import tomllib
    I = tomllib.load(open("indata.toml", "rb"))
    for sam, gav, om in ((False, False, False), (False, False, True), (True, True, True)):
        N = bygg(I, sam, gav, om)
        g = N["gren"]
        print(f"samling={sam} gavel={gav} omluft={om}: {len(N['noder'])} noder, {len(g['a'])} grenar, "
              f"{len(N['fall'])} takfall, {len(N['remsor'])} remsor")
    N = bygg(I)
    g = N["gren"]
    for s, (yc, w) in enumerate(N["remsor"]):
        f = [i for i in N["fall"] if g["remsa"][i] == s]
        print(f"remsa {s:2d} y = {yc:7.0f} b = {w:4.0f}: {len(f)} takfall, längd {sum(g['L'][f]):5.2f} m")
