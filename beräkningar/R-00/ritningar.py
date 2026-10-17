"""
R-00 Bärande system i betong, översikt i 3D (F-01), A3 med ../ritningsmall:
    R-00.1  Bottenplatta, källarväggar, rör och mellanbjälklag i 3D (inga mått, ingen skala)
Fyra bilder i den ordning delarna byggs: bottenplattan (delvis bortskuren, så att balkarna och plintarna syns),
källarväggarna och rören, mellanbjälklaget (delvis bortskuret, så att rören syns under det) och ett snitt genom
källarens västra del. Geometrin är densamma som på R-03, R-04 och R-05 (scen.py); bilderna renderas med rendera.py.
    python beräkningar/R-00/ritningar.py
"""
import os
import sys

import numpy as np
from shapely.geometry import box

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import scen as S  # noqa: E402
from rendera import Kamera, Scen, rendera  # noqa: E402
from scen import K  # noqa: E402
from ritning import Vy, Blad, huvud, PROJEKT  # noqa: E402

ROT = K.ROT
UT = os.path.join(ROT, "ritningar")
BLADMAPP = os.path.join(HERE, "blad")
DPI = 300.0

NR = "R-00"
REV, DATUM = "A", "2026-10-17"
REVISIONER = [dict(rev=REV, avser="Första utgåvan", datum=DATUM, sign=PROJEKT["signatur"])]
BLADEN = [("R-00.1", ["Bärande system i betong", "Översikt i 3D"], "–", "R-00.1 Bärande system i betong, översikt i 3D")]

H, Z1 = S.H, S.Z1
Y_SNITT, X_SNITT = 5700.0, 5000.0          # vy 4: snitt genom källarens västra del


# ================================================================== vyerna
def vy1(s):
    """Bottenplattan; plattan bortskuren i sydvästra delen, så att balkarna, plintarna och cellplasten syns."""
    S.grund(s, kapa=box(-500, -500, 7600, 8000))


def vy2(s):
    S.grund(s)
    S.vaggar(s)
    S.ror(s)


def vy3(s):
    S.grund(s)
    S.vaggar(s)
    S.ror(s)
    S.bjalklag(s, kapa=box(6400, -500, 14500, 6300))


def vy4(s):
    S.grund(s)
    S.vaggar(s)
    S.ror(s)
    S.bjalklag(s)


VYER = [
    # (nr, rubrik, byggare, kamera (az, el), klipp, bildens ruta (x, y, b, h) på bladet)
    (1, "Bottenplatta (R-05)", vy1, (235, 30), None, (24, 16, 146, 112)),
    (2, "Källarväggar och rör (R-04)", vy2, (235, 30), None, (176, 16, 146, 112)),
    (3, "Mellanbjälklag (R-03)", vy3, (235, 30), None, (24, 152, 146, 112)),
    (4, "Snitt genom källarens västra del", vy4, (300, 20),
     box(-1000, Y_SNITT, X_SNITT, 9000), (176, 152, 146, 112)),
]


def bild(nr, byggare, kam, klipp, ruta):
    """Renderar vyn så att den fyller rutan; returnerar källa, bildens storlek på papperet (b, h) och en
    avbildning från modellens punkter till pappersmm inom rutan."""
    s = Scen(klipp=klipp)
    byggare(s)
    k = Kamera(*kam)
    _, _, ram = rendera(s, k, 0.01, ss=1)                      # utbredningen
    umin, vmin, umax, vmax = ram
    skala = min(ruta[2] / (umax - umin), ruta[3] / (vmax - vmin))   # pappersmm per modellmm
    px = skala * DPI / 25.4
    img, avb, _ = rendera(s, k, px, ram=ram, ss=2, kantbredd=2)
    os.makedirs(BLADMAPP, exist_ok=True)
    fil = os.path.join(BLADMAPP, f"vy{nr}.png")
    img.save(fil, dpi=(DPI, DPI))
    b, h = img.size[0] / px * skala, img.size[1] / px * skala
    dx, dy = (ruta[2] - b) / 2, (ruta[3] - h) / 2             # centrerad i rutan
    src = "/" + os.path.relpath(fil, ROT).replace(os.sep, "/")

    def papper(P):
        q = avb(np.asarray(P, float)) / px * skala
        return [(ruta[0] + dx + u, ruta[1] + dy + v) for u, v in q]

    return src, (ruta[0] + dx, ruta[1] + dy, b, h), papper, img


# ================================================================== hänvisningar
def _ror(namn):
    r = K.ROR_D[namn]
    return r["ror"][0]


def hanvisningar(nr):
    """(text, modellpunkt) för varje vy; texterna placeras av placera()."""
    if nr == 1:
        x8, y8 = K.ROR_D["P8"]["mitt"]
        return [
            ("L-element S300 längs hela kanten", (20.0, 8000.0, 0.0)),
            ("kantbalk 450 × 200 under ytterväggarna", (300.0, 4300.0, -100.0)),
            ("plint under varje rör, fotplåt i överkant", (x8, y8, -100.0)),
            ("balk 450 × 200 under innerväggarna", (6000.0, 7515.0, -100.0)),
            ("cellplast S100, S300 under balkar och plintar", (3300.0, 4400.0, -100.0)),
            ("bottenplatta 100, bortskuren i bilden", (10500.0, 9000.0, 0.0)),
        ]
    if nr == 2:
        x5, y5 = _ror("P5")
        return [
            ("yttervägg mot jord, Sundolitt Kub 350-150", (145.0, 6500.0, H)),
            ("innervägg (V4–V6, V15, V19)", (7095.0, 7515.0, H)),
            ("stålrör VKR 80 × 80 på fotplåt i plinten (P1–P19)", (x5, y5, 1200.0)),
            ("dörröppningar D1–D3", (10390.0, 1145.0, 1000.0)),
            ("fasad med fönster F1–F3: pelare och bröstningar", (6215.0, 145.0, 1700.0)),
        ]
    if nr == 3:
        x15, y15 = _ror("P15")
        return [
            ("mellanbjälklag 150, vilar på väggarna och rören", (5000.0, 6500.0, Z1)),
            ("platta på mark, plan 1, på 400 mm cellplast", (1500.0, 13500.0, Z1)),
            ("trapphål", (8000.0, 5400.0, Z1)),
            ("rören bär bjälklaget med topplåt i plattans undersida", (x15, y15, 1600.0)),
        ]
    x8, y8 = _ror("P8")
    return [
        ("mellanbjälklag 150", (2500.0, Y_SNITT, Z1 - 75.0)),
        ("Kub-väggen bär bjälklaget och jordtrycket", (145.0, Y_SNITT, 1500.0)),
        ("kantbalk i L-element under väggen", (250.0, Y_SNITT, -150.0)),
        ("cellplast S100 under plattan", (1100.0, Y_SNITT, -200.0)),
        ("rör på fotplåt i plinten", (x8, y8, 900.0)),
        ("plint 200 på S300", (x8, Y_SNITT, -150.0)),
        ("innervägg V19 på balk", (4545.0, 8000.0, 1500.0)),
    ]


# ================================================================== placering av texterna
TXT_SZ = 6.4
MM_PER_TECKEN = 0.183 * TXT_SZ           # Carlito, medelbredd per tecken i mm
TXT_H = 2.7


def _korsar(p1, p2, p3, p4):
    def ccw(a, b, c):
        return (c[1] - a[1]) * (b[0] - a[0]) - (b[1] - a[1]) * (c[0] - a[0])
    return ccw(p3, p4, p1) * ccw(p3, p4, p2) < 0 and ccw(p1, p2, p3) * ccw(p1, p2, p4) < 0


def _seg_i_ruta(p, q, r):
    """Går sträckan p–q genom rutan r = (x0, y0, x1, y1)?"""
    for t in np.linspace(0, 1, 25):
        x, y = p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])
        if r[0] <= x <= r[2] and r[1] <= y <= r[3]:
            return True
    return False


def placera(texter, mal, ruta, bildruta, img, fri=()):
    """Lägen för texterna: på vit yta i rutan, nära målpunkten, utan att texterna överlappar varandra och utan att
    hänvisningslinjerna korsar varandra eller går genom andra texter. Kandidaterna ligger i ett rutnät; valet görs
    med lokal sökning (varje text väljer sitt bästa läge givet de andras, tills inget ändras), från flera
    startordningar. Returnerar [(läge (x, y), ankare "lm"/"rm")]."""
    bx, by, bb, bh = bildruta
    a = np.asarray(img.convert("L"), float) < 240
    kx, ky = a.shape[1] / bb, a.shape[0] / bh                 # bildpunkter per mm
    # summerad tabell: hur mycket som är ritat i en ruta
    S_ = np.zeros((a.shape[0] + 1, a.shape[1] + 1))
    S_[1:, 1:] = a.cumsum(0).cumsum(1)

    def ritat(x0, y0, x1, y1):
        i0, i1 = int((x0 - bx) * kx), int(np.ceil((x1 - bx) * kx))
        j0, j1 = int((y0 - by) * ky), int(np.ceil((y1 - by) * ky))
        i0, j0 = min(max(i0, 0), a.shape[1]), min(max(j0, 0), a.shape[0])
        i1, j1 = min(max(i1, 0), a.shape[1]), min(max(j1, 0), a.shape[0])
        if i1 <= i0 or j1 <= j0:
            return 0.0
        return S_[j1, i1] - S_[j0, i1] - S_[j1, i0] + S_[j0, i0]

    def over(p, q):
        n = 0
        for t in np.linspace(0, 1, 24):
            x, y = p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])
            n += ritat(x - 0.25, y - 0.25, x + 0.25, y + 0.25) > 0
        return n / 24

    kand = []
    for i, t in enumerate(texter):
        w = len(t) * MM_PER_TECKEN + 1.0
        k = []
        for px in np.arange(ruta[0], ruta[0] + ruta[2] + 0.1, 2.0):
            for py in np.arange(ruta[1] + 2, ruta[1] + ruta[3] - 1.9, 2.0):
                d = float(np.hypot(px - mal[i][0], py - mal[i][1]))
                if d < 4.0 or d > 85.0:
                    continue
                for ank in ("lm", "rm"):
                    r = (px, py - TXT_H / 2, px + w, py + TXT_H / 2) if ank == "lm" else \
                        (px - w, py - TXT_H / 2, px, py + TXT_H / 2)
                    if r[0] < ruta[0] or r[2] > ruta[0] + ruta[2]:
                        continue
                    # ledaren ska komma till textens ände från rätt håll
                    if (ank == "lm" and mal[i][0] > px + 0.5 * w) or (ank == "rm" and mal[i][0] < px - 0.5 * w):
                        continue
                    if any(r[0] < f[2] and f[0] < r[2] and r[1] < f[3] and f[1] < r[3] for f in fri):
                        continue
                    if ritat(r[0] - 1.0, r[1] - 1.0, r[2] + 1.0, r[3] + 1.0) > 0:
                        continue
                    k.append((d + 30.0 * over(mal[i], (px, py)), (float(px), float(py)), ank, r))
        k.sort(key=lambda c: c[0])
        kand.append(k[:250])
        if not k:
            raise RuntimeError(f"ingen plats för texten: {t}")

    def konflikt(i, ci, j, cj):
        _, pi, _, ri = kand[i][ci]
        _, pj, _, rj = kand[j][cj]
        n = 0
        if ri[0] < rj[2] + 1.5 and rj[0] - 1.5 < ri[2] and ri[1] < rj[3] + 1.2 and rj[1] - 1.2 < ri[3]:
            n += 1
        if _korsar(mal[i], pi, mal[j], pj):
            n += 1
        if _seg_i_ruta(mal[i], pi, rj) or _seg_i_ruta(mal[j], pj, ri):
            n += 1
        return n

    rng = np.random.default_rng(1)
    bast = None
    for start in range(12):
        val = [0] * len(texter)
        ordning = list(range(len(texter)))
        if start:
            rng.shuffle(ordning)
        for _ in range(40):
            andrat = False
            for i in ordning:
                besta = None
                for ci in range(len(kand[i])):
                    c = kand[i][ci][0] + 400.0 * sum(konflikt(i, ci, j, val[j]) for j in range(len(texter)) if j != i)
                    if besta is None or c < besta[0]:
                        besta = (c, ci)
                if besta[1] != val[i]:
                    val[i], andrat = besta[1], True
            if not andrat:
                break
        tot = sum(kand[i][val[i]][0] for i in range(len(texter)))
        fel = sum(konflikt(i, val[i], j, val[j]) for i in range(len(texter)) for j in range(i + 1, len(texter)))
        if bast is None or (fel, tot) < bast[0]:
            bast = ((fel, tot), list(val))
    (fel, _), val = bast
    if fel:
        print(f"  varning: {fel} konflikter kvar bland texterna")
    return [(kand[i][val[i]][1], kand[i][val[i]][2]) for i in range(len(texter))]


# ================================================================== bladet
def blad():
    vyer = []
    for nr, rubrik, byggare, kam, klipp, ruta in VYER:
        src, bruta, papper, img = bild(nr, byggare, kam, klipp, ruta)
        v = Vy(x=0, y=0, w=420, h=297, skala=1.0, X0=0.0, Y1=0.0)
        with v.lager("bild"):
            v.bild(bruta[0], -bruta[1], bruta[2], bruta[3], src)
        hv = hanvisningar(nr)
        mal = [papper([P])[0] for _, P in hv]
        rub = (ruta[0], ruta[1] + ruta[3] - 2.0, ruta[0] + 120.0, ruta[1] + ruta[3] + 8.0)     # rubriken
        lagen = placera([t for t, _ in hv], mal, ruta, bruta, img, fri=[rub])
        with v.lager("text"):
            for (txt, _), (mx, my), ((px, py), a) in zip(hv, mal, lagen):
                v.hanvisning((mx, -my), (px, -py), txt, a=a, sz=TXT_SZ)
        with v.lager("rubrik"):
            v.text(ruta[0], -(ruta[1] + ruta[3] + 6.0), f"{nr}  {rubrik.upper()}", a="lb", sz=9, b=True)
        vyer.append(v)
    kol = [
        dict(typ="rubrik", text="Bärande system"),
        dict(typ="lista", sz=6.8, rader=[
            "Bilderna visar betongarbetets bärande delar i 3D, i den ordning de byggs. Inga mått: mått och utförande "
            "på R-03 (mellanbjälklag), R-04 (källarstomme) och R-05 (bottenplatta).",
            "Mellanbjälklaget, 150 mm, bär plan 1 och vilar på källarväggarna och på stålrören P1–P19. Över "
            "fyllningen norr om källaren ligger det som platta på mark på 400 mm cellplast (K-05).",
            "Källarväggarna av Sundolitt Kub 350-150 bär bjälklaget och jordtrycket; ytterväggarna hålls i toppen av "
            "bjälklaget och i botten av bottenplattan. Fasaden mot söder har fönster F1–F3 mellan pelare (K-06).",
            "Rören står på fotplåtar som gjuts in i plintarnas överkant. Väggarna står på kantbalken i L-elementen "
            "och på balkarna under innerväggarna.",
            "Bottenplattan, 100 mm, gjuts i en gjutning med kantbalkarna, balkarna och plintarna. De fördelar lasten "
            "på cellplasten, S300 under balkar och plintar och S100 under plattan, som ligger på makadam på "
            "sprängt berg (K-06).",
            "Bilderna är förenklade: armering, fogar, smyglister och mindre delar visas inte."]),
        dict(typ="rubrik", text="Teckenförklaring"),
        dict(typ="symboler", rader=[
            dict(form="yta", fyll=S.FARG["betong"], stil="tunn", text="betong: bottenplatta, balkar, plintar, bjälklag"),
            dict(form="yta", fyll=S.FARG["karna"], stil="tunn", text="Kub-väggarnas betongkärna"),
            dict(form="yta", fyll=S.FARG["eps"], stil="tunn", text="cellplast: väggarna och S100 under plattan"),
            dict(form="yta", fyll=S.FARG["s300"], stil="tunn", text="cellplast S300: L-element, under balkar och plintar"),
            dict(form="yta", fyll=S.FARG["stal"], stil="tunn", text="stål: rör och fotplåtar")]),
    ]
    b = BLADEN[0]
    hd = huvud(b[0], b[1], b[2], "R-03, R-04, R-05", DATUM, REV)
    return Blad(hd, REVISIONER, kol, vyer)


SERIE = "R-00 Bärande system i betong"


def main():
    os.makedirs(UT, exist_ok=True)
    os.makedirs(BLADMAPP, exist_ok=True)
    b = blad()
    jp = os.path.join(HERE, "R-00.1.json")
    b.spara(jp)
    pdf = os.path.join(BLADMAPP, BLADEN[0][3] + ".pdf")
    b.kompilera(jp, pdf, ROT)
    Blad.serie([pdf], os.path.join(UT, SERIE + ".pdf"))
    print(f"ritningar/{SERIE}.pdf (1 sida)")


if __name__ == "__main__":
    main()
