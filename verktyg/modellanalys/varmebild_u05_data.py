"""Underlag till värmebilden av huset (varmebild_u05.py): värmeflödets täthet [W/m²] ut genom husets yttre ytor i
U-05:s grundfall vid 0 °C ute, stationärt.

Körs med beräkningarnas Python-miljö (varmebild_u05.py gör det):

    ../../beräkningar/.venv/bin/python varmebild_u05_data.py ut.npz

Husets nedre del räknas ur U-05:s 3D-modell (mark3d.py): temperaturfältet löses för grundfallets temperaturer
(resultat.json) och flödet räknas genom varje cellyta i den yta som omsluter källaren, bottenplattans cellplast,
mellanbjälklaget och plattan på mark: källarväggarnas utsida (över och under mark), cellplastens undersida och
plattan på marks kanter. Plan 1 ritas ur byggdelarna: väggarna, gavelspetsarna och takfallen med U gånger
temperaturskillnaden, och mellanbjälklagets kant (150 mm) med värmen genom kantisoleringen ur skarvarnas snitt.
Fönstren och dörrarna får sitt U gånger temperaturskillnaden (lägena tar varmebild_u05.py ur modellen).
Läser inte modellen.
"""
import json
import math
import sys
from pathlib import Path

import numpy as np

U05 = Path(__file__).resolve().parents[2] / "beräkningar" / "U-05"
sys.path.insert(0, str(U05))
import data  # noqa: E402
import mark3d  # noqa: E402
from mark3d import HALV, _forskjut, _inuti, kallarens_kontur  # noqa: E402
from shapely.geometry import Point, Polygon  # noqa: E402

P = data.las()
res = json.loads((U05 / "resultat.json").read_text(encoding="utf-8"))
T0 = res["stat"]["noll"]["T"]
m, info = mark3d.bygg(P)
Tf = m.los(dict(T0))

# ---------------------------------------------------------------- husets nedre del: ytan som omsluter den
X2, Y2 = np.meshgrid(m.mitt[0], m.mitt[1], indexing="ij")
zc = m.mitt[2]
kk = kallarens_kontur()
kontur = np.array(P["_kontur"])
platta = np.array(P["platta_pa_mark"]["kontur"]) / 1000
hb = P["bjalklag"]["h"] / 1000
BP = P["bottenplatta"]
z_eps = -2.25 - (BP["betong"] + BP["eps"]) / 1000
z_pm_eps = -hb - P["platta_pa_mark"]["eps"] / 1000
kall_ut = _inuti(_forskjut(kk, HALV), X2, Y2)
pm_ut = _inuti(_forskjut(platta, 0.03), X2, Y2) & ~kall_ut
stomme_ut = _inuti(_forskjut(kontur, 0.03), X2, Y2)


def kol(mask, za, zb):
    return mask[:, :, None] & ((zc > za) & (zc < zb))[None, None, :]


R = kol(kall_ut, z_eps, -hb) | kol(pm_ut, z_pm_eps, -hb) | kol(stomme_ut, -hb, 0.0)
fast = m.mat >= 0
lam = np.zeros((3,) + m.form)
for i, (_, l) in enumerate(m.material):
    for a in range(3):
        lam[a][m.mat == i] = l[a]
Tenv = np.array([T0[o] for o in m.omgivningar])
quads, qs = [], []
for a in range(3):
    b, c = [x for x in range(3) if x != a]
    half = (m.d[a] / 2).reshape([-1 if x == a else 1 for x in range(3)]) * np.ones(m.form)
    nedre = tuple(slice(0, -1) if x == a else slice(None) for x in range(3))
    ovre = tuple(slice(1, None) if x == a else slice(None) for x in range(3))
    for inne, ute, uppat in ((nedre, ovre, True), (ovre, nedre, False)):
        if a == 2 and uppat:
            continue                                    # uppåt: mot plan 1, ingen yttre yta
        msk = R[inne] & ~R[ute] & fast[inne]
        idx = np.argwhere(msk)
        Ti, ri = Tf[inne][msk], half[inne][msk] / lam[a][inne][msk]
        f_ut, o_ut = fast[ute][msk], m.omg[ute][msk]
        q = np.full(len(idx), np.nan)
        ro = half[ute][msk] / np.where(f_ut, lam[a][ute][msk], 1.0)
        q[f_ut] = (Ti[f_ut] - Tf[ute][msk][f_ut]) / (ri[f_ut] + ro[f_ut])                # mot marken
        e = ~f_ut & (o_ut >= 0)
        q[e] = (Ti[e] - Tenv[o_ut[e]]) / (ri[e] + m.Rs[ute][msk][e])                      # mot luften
        ok = ~np.isnan(q)
        idx, q = idx[ok], q[ok]
        Q = np.zeros((len(idx), 4, 3))
        b0, b1 = m.kant[b][idx[:, b]], m.kant[b][idx[:, b] + 1]
        c0, c1 = m.kant[c][idx[:, c]], m.kant[c][idx[:, c] + 1]
        for k, (bb, cc) in enumerate(((b0, c0), (b1, c0), (b1, c1), (b0, c1))):
            Q[:, k, a], Q[:, k, b], Q[:, k, c] = m.kant[a][idx[:, a] + 1], bb, cc
        quads.append(Q)
        qs.append(q)
quads, qs = np.concatenate(quads), np.concatenate(qs)
A = np.linalg.norm(np.cross(quads[:, 1] - quads[:, 0], quads[:, 3] - quads[:, 0]), axis=1)
print(f"husets nedre del: {len(qs)} ytor, {A.sum():.0f} m², {float((qs * A).sum()):.0f} W", flush=True)

# ---------------------------------------------------------------- plan 1 ur byggdelarna
extra, qx, namn = [], [], []


def lagg(pts, q, n):
    extra.append(np.array(pts, float))
    qx.append(q)
    namn.append(n)


dT = T0["inne"] - T0["ute"]
TAN = math.tan(math.radians(P["tak"]["lutning"]))
kr = {k["nr"]: k for k in P["mangder"]["kropp"]}
dal = sorted(d["x"] for d in P["balkar"]["dalar"])
UT = 0.165                                             # väggens tjocklek innanför stommens utsida [m]


def z_tak(x):
    """Takets höjd [m] över x [mm] (innertaket lyft till takets utsida)."""
    k = kr[1 if x < dal[0] else (2 if x < dal[1] else 3)]
    return (k["z_innertak"] + (k["halvbredd"] - abs(x - k["nock"])) * TAN) / 1000 + 0.33


vagg = {v["kod"]: v for v in P["mangder"]["vagg"]}
Uv = {v["kod"]: v["U"] for v in res["vagg"]}
for v in P["mangder"]["lage"]:
    o, u, L = np.array(v["o"], float) / 1000, np.array(v["u"], float), v["L"] / 1000
    w, q = vagg[v["kod"]], Uv[v["kod"]] * dT
    Ug = res["gavel"][w["typ"]]
    # remsor längs väggen (0,15 m förbi ändarna, så att hörnen sluter) upp till taket; gavlarna över 2,49 m med
    # gavelspetsens U
    ss = np.linspace(-0.15, L + 0.15, 60 if w["gavel"] else 2)
    for s0, s1 in zip(ss[:-1], ss[1:]):
        p0, p1 = o + u * s0, o + u * s1
        zt0, zt1 = z_tak(p0[0] * 1000), z_tak(p1[0] * 1000)
        zh = 2.49 if w["gavel"] else 1e9
        lagg([(*p0, 0.0), (*p1, 0.0), (*p1, min(zh, zt1)), (*p0, min(zh, zt0))], q, "vägg " + v["kod"])
        if max(zt0, zt1) > zh:
            lagg([(*p0, zh), (*p1, zh), (*p1, max(zh, zt1)), (*p0, max(zh, zt0))], Ug * dT, "gavelspets " + v["kod"])
Ut = {x["kod"]: x["U"] for x in res["tak"]}
for tf in P["mangder"]["takfall"]:
    for x0, x1, y0, y1 in tf["plan"]:
        xa, xb = sorted((x0, x1))
        nock = kr[1 if 0.5 * (xa + xb) < dal[0] else (2 if 0.5 * (xa + xb) < dal[1] else 3)]["nock"]
        # från nocken eller dalen ut till stommens utsida vid takfoten och gavlarna
        xa -= 0 if (abs(xa - nock) < 1 or xa in dal) else UT * 1000
        xb += 0 if (abs(xb - nock) < 1 or xb in dal) else UT * 1000
        za = z_tak(xa + (1e-3 if xa < nock else -1e-3))
        zb = z_tak(xb - (1e-3 if xb > nock else -1e-3))
        ya, yb = (y0 - UT * 1000) / 1000, (y1 + UT * 1000) / 1000
        lagg([(xa / 1000, ya, za), (xb / 1000, ya, zb), (xb / 1000, yb, zb), (xa / 1000, yb, za)], Ut[tf["kod"]] * dT,
             "tak " + tf["kod"])
# mellanbjälklagets kant: bandet 150 mm högt med värmen genom kantisoleringen (skarvarnas snitt)
st0 = res["stat"]["noll"]
qk = {t: st0["kant"][t] / res["skarv"]["bjalklag_" + t]["l"] / hb for t in ("kallare", "mark")}
pm = Polygon(platta).buffer(0.12)
ytter = np.array(Polygon(kontur).buffer(0.045, join_style=2).exterior.coords)
for p0, p1 in zip(ytter[:-1], ytter[1:]):
    typ = "mark" if pm.contains(Point(*(0.5 * (p0 + p1)))) else "kallare"
    lagg([(*p0, -hb), (*p1, -hb), (*p1, 0.0), (*p0, 0.0)], qk[typ], "bjälklagskant")
# fönstren och dörrarna: flödets täthet per kod (lägena ur modellen)
TF = P["takfonster"]
fonster = {f["kod"]: f["U"] * ((T0["kallare"] if f["vaning"] == 0 else T0["inne"]) - T0["ute"]) for f in res["fonster"]}
fonster.update({f"TF{i}": TF["Uw"] * dT for i in range(1, TF["antal"] + 1)})
np.savez_compressed(sys.argv[1], quads=quads.astype(np.float32), q=qs.astype(np.float32),
                    extra=np.array(extra, np.float32), qx=np.array(qx, np.float32), namn=np.array(namn),
                    fonster_kod=np.array(list(fonster)), fonster_q=np.array(list(fonster.values()), np.float32),
                    tak=np.array([[k["nock"], k["halvbredd"], k["z_innertak"]] for k in kr.values()] , np.float32),
                    dal=np.array(dal, np.float32), lutning=P["tak"]["lutning"],
                    T=np.array([T0["ute"], T0["inne"], T0["kallare"], T0["varme"]]))
print(f"plan 1: {len(extra)} ytor; mellanbjälklagets kant {qk['kallare']:.1f} och {qk['mark']:.1f} W/m²")
