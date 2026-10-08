"""Uppmätning av geometrin för K-05 ur Onshape-skärmbilderna (källare: kallare.png, plan 1: plan1.png) och Plattor.pdf.
Koordinater i mm, x åt höger, y uppåt, origo i plattans nedre vänstra hörn (som i bilderna)."""
import json, numpy as np
from PIL import Image
from scipy import ndimage as nd

S = 5450 / (1636.8 - 1062.2)          # mm/px, uppmätt 5450 i källarbilden
KI = 30                                # kantisolering: Lecans ytterliv ligger 30 mm utanför plattans kant
E = 175 - KI                           # väggens centrumlinje innanför plattans kant (Lecavägg 350: 100 + 150 isolering + 100)
UPPL = 100                             # ytterväggar: upplag 75 mm in från väggens insida (EC2 5.3.2.2, a = min(h/2, t/2))
# passning: kärnans centrumlinje i px -> plattkant ± 175
X = [(618, E), (1092, 4500 + E), (2042, 13810 - E), (1619, 9500 + E)]
Y = [(1617, E), (1513, 1000 + E), (1240, 3590 + E), (331, 12510 - E), (489, 11010 - E)]
x0 = np.mean([m - S * p for p, m in X]); y0 = np.mean([m + S * p for p, m in Y])
fx = lambda p: S * p + x0
fy = lambda p: -S * p + y0

kontur = [(0, 0), (4500, 0), (4500, 3590), (0, 3590)][::-1]   # ersätts nedan
kontur = [(4500, 0), (9310, 0), (9310, 1000), (13810, 1000), (13810, 12510), (9500, 12510), (9500, 11010),
          (4310, 11010), (4310, 15900), (0, 15900), (0, 3590), (4500, 3590)]
hal = [(7350, 5050), (9420, 5050), (9420, 5878), (7350, 5878)]

# kärnor ur källarbilden (px): (riktning, läge, från, till)
a = np.array(Image.open('kallare.png').convert('RGB')).astype(int)
R, G, B = a[..., 0], a[..., 1], a[..., 2]
pink = (R > 200) & (G > 150) & (G < 205) & (B > 180) & (B < 232)
brown = (abs(R - 176) < 16) & (abs(G - 163) < 12) & (abs(B - 160) < 14)
core = nd.binary_closing(brown, iterations=3) & ~pink
bars = []
for ax, k in (("h", np.ones((1, 25), bool)), ("v", np.ones((25, 1), bool))):
    lab, n = nd.label(nd.binary_opening(core, structure=k))
    for s in nd.find_objects(lab):
        yy0, yy1, xx0, xx1 = s[0].start, s[0].stop, s[1].start, s[1].stop
        t = (yy1 - yy0) if ax == "h" else (xx1 - xx0)
        if not 7 <= t <= 12:
            continue
        if ax == "h":
            bars.append(("h", fy((yy0 + yy1 - 1) / 2), fx(xx0 - 2), fx(xx1 + 1)))
        else:
            bars.append(("v", fx((xx0 + xx1 - 1) / 2), fy(yy1 + 1), fy(yy0 - 2)))
# fäst vid plattkanterna
SNAP = {"h": [E, 1000 + E, 3590 + E, 11010 - E, 12510 - E], "v": [E, 4500 + E, 9310 - E, 9500 + E, 13810 - E]}
vagg = []
for ax, c, s0, s1 in bars:
    for v in SNAP[ax]:
        if abs(c - v) < 60: c = v
    vagg.append([ax, float(round(c, -1)), float(round(s0, -1)), float(round(s1, -1))])
# hörn: förläng ändar till vinkelrät vägg inom 120 mm
for w in vagg:
    for k in (2, 3):
        for o in vagg:
            if o[0] != w[0] and o[2] - 120 <= w[1] <= o[3] + 120 and abs(o[1] - w[k]) < 320:
                w[k] = o[1]
# dela väggar där marken börjar (y för källarens övre vägg i vänstra delen)
yH3_ = max(w[1] for w in vagg if w[0] == "h" and w[2] < 1000)
ny = []
for w in vagg:
    if w[0] == "v" and w[1] < 5000 and w[2] < yH3_ < w[3]:
        ny += [[w[0], w[1], w[2], yH3_], [w[0], w[1], yH3_, w[3]]]
    else:
        ny.append(w)
vagg = ny
vagg.sort(key=lambda w: (w[0], -w[1], w[2]))
# yttre/inre vägg och upplagslinje
from shapely.geometry import Polygon as SP_, Point as PT_
_slab = SP_(kontur)
def _ute(x, y):
    return (not _slab.contains(PT_(x, y))) or (x < 4310 + 1 and y > yH3_ + 1) or (4310 <= x <= 4550 + 1 and 9210 < y < 11010 and x < 4550)
for w in vagg:
    ax_, c, a_, b_ = w
    m = (a_ + b_) / 2
    p1, p2 = ((m, c - 300), (m, c + 300)) if ax_ == "h" else ((c - 300, m), (c + 300, m))
    u1, u2 = _ute(*p1), _ute(*p2)
    if u1 and not u2:
        w += ["yttre", c + UPPL]
    elif u2 and not u1:
        w += ["yttre", c - UPPL]
    else:
        w += ["inre", c]
# upplagslinjernas ändar följer den vinkelräta väggens upplagslinje
for w in vagg:
    for k in (2, 3):
        for o in vagg:
            if o[0] != w[0] and abs(o[1] - w[k]) < 1 and o[2] - 1 <= w[1] <= o[3] + 1:
                w.append(("a" if k == 2 else "b", o[5]))
stod = []
for w in vagg:
    a_, b_ = w[2], w[3]
    for t in w[6:]:
        if t[0] == "a": a_ = t[1]
        else: b_ = t[1]
    stod.append([w[0], w[5], a_, b_])
vagg = [w[:6] for w in vagg]
# pelare
dark = a.sum(-1) < 350
lab, n = nd.label(dark)
pel = []
for s in nd.find_objects(lab):
    h, w = s[0].stop - s[0].start, s[1].stop - s[1].start
    if 15 <= h <= 18 and 15 <= w <= 18 and s[1].start > 560:
        pel.append((float(round(fx((s[1].start + s[1].stop - 1) / 2), -1)), float(round(fy((s[0].start + s[0].stop - 1) / 2), -1))))
pel.sort(key=lambda p: (-p[1], p[0]))
PLAT = 200
hx0, hy0, hx1, hy1 = hal[0][0], hal[0][1], hal[2][0], hal[2][1]
_p = []
for x, y in pel:
    if hx0 - PLAT <= x <= hx1 + PLAT and abs(y - hy1) < 200:
        y = hy1 + PLAT / 2
    elif hx0 - PLAT <= x <= hx1 + PLAT and abs(y - hy0) < 200:
        y = hy0 - PLAT / 2
    _p.append((x, y))
pel = _p
# yta på mark: vänstra delen ovanför källarens övre vägg
yH3 = max(w[1] for w in vagg if w[0] == "h" and w[2] < 1000)
xV3 = min(w[1] for w in vagg if w[0] == "v" and 4000 < w[1] < 5000 and w[3] > yH3)
mark = [(0, yH3), (xV3, yH3), (xV3, 11010), (4310, 11010), (4310, 15900), (0, 15900)]
# väggar på plan 1 (blå i plan1.png)
t2 = json.load(open('trans2.json'))
b2 = np.array(Image.open('plan1.png').convert('RGB')).astype(int)
blue = (b2[..., 2] > b2[..., 0] + 20) & (b2[..., 2] > 150)
blue = nd.binary_closing(blue, iterations=4)
plan1 = []
for ax, k in (("h", np.ones((1, 30), bool)), ("v", np.ones((30, 1), bool))):
    lab, n = nd.label(nd.binary_opening(blue, structure=k))
    for s in nd.find_objects(lab):
        yy0, yy1, xx0, xx1 = s[0].start, s[0].stop, s[1].start, s[1].stop
        X0, X1 = t2["sx"] * xx0 + t2["x0"], t2["sx"] * xx1 + t2["x0"]
        Y1, Y0 = -t2["sy"] * yy0 + t2["y0"], -t2["sy"] * yy1 + t2["y0"]
        plan1.append([ax, round(X0, -1), round(Y0, -1), round(X1, -1), round(Y1, -1)])
# uppmätta värden uppdateras; stolpar, balkar, linjelaster och fria kanter i geometri.json lämnas orörda
import os
gammal = json.load(open('geometri.json', encoding='utf-8')) if os.path.exists('geometri.json') else {}
gammal.update(dict(kontur=kontur, hal=hal, vagg=vagg, stod=stod, pelare=pel, mark=mark, plan1=plan1, skala=S, E=E))
json.dump(gammal, open('geometri.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(f"skala {S:.4f} mm/px, x0 {x0:.0f}, y0 {y0:.0f}")
print("väggar"); [print("  ", w, "  upplag", st) for w, st in zip(vagg, stod)]
print("pelare", len(pel)); [print("  ", i + 1, p) for i, p in enumerate(pel)]
from shapely.geometry import Polygon as SP
print("mark", mark, "yta", round(SP(mark).area / 1e6, 1), "m², platta", round(SP(kontur).area/1e6,1), "m²")
print("plan1-väggar", len(plan1))
