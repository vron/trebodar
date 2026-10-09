"""
Hjälpmodul för ritningar i ritningsmall/ritning.typ (A3 liggande). Mallen är gemensam för alla ritningar:
ram, ritningshuvud och stil ändras bara här och i ritning.typ, projektets uppgifter i projekt.json.

Ett blad är en JSON-fil med ritningshuvud, revisioner, högerkolumn och vyer. En vy har en skala och ett
modellfönster. Allt ritas i modellens verkliga koordinater (mm, y uppåt); Vy räknar om till papperets mm
(y nedåt), så att skalan blir exakt. Bara linjetjocklekar, textstorlekar och avstånd för mått och etiketter
anges i pappersmått.

Elementen läggs i namngivna lager, som ritas i den ordning de skapas och kan döljas vid kompileringen:

    from ritning import Vy, Blad, huvud
    v = Vy(x=30, y=20, w=280, h=250, skala=50, X0=-500, Y1=12900)
    with v.lager("kontur"):
        v.linje([(0, 0), (1000, 0)], "kontur")
    Blad(huvud("R-03.2", [...], "1:50"), revisioner, kolumn, [v]).kompilera(...)
"""
import json
import math
import os

import numpy as np

MALL = os.path.dirname(os.path.abspath(__file__))
PROJEKT = json.load(open(os.path.join(MALL, "projekt.json"), encoding="utf-8"))
# ritytan: ramen (20/10/10/10 mm) minus högerkolumnen (84 mm)
YTA = dict(x0=20.0, y0=10.0, x1=420.0 - 10.0 - 84.0, y1=297.0 - 10.0)


def sv(x, n=0):
    return f"{x:,.{n}f}".replace(",", " ").replace(".", ",").replace("-", "−")


class Vy:
    def __init__(self, x, y, w, h, skala, X0, Y1, klipp=False):
        self.x, self.y, self.w, self.h, self.s = x, y, w, h, float(skala)
        self.X0, self.Y1 = X0, Y1
        self.klipp = klipp
        self.lagren = {}                    # lagrets namn -> element, i den ordning lagren skapas
        self._aktiv = []

    # ---------------------------------------------------------------- lager
    def lager(self, namn):
        """Aktivt lager. Används som `with v.lager("armering"): ...` (återgår efteråt) eller direkt."""
        self.lagren.setdefault(namn, [])
        self._aktiv.append(namn)
        return self

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self._aktiv.pop()

    def _add(self, e):
        namn = self._aktiv[-1] if self._aktiv else "standard"
        self.lagren.setdefault(namn, []).append(e)

    # ---------------------------------------------------------------- koordinater
    def P(self, X, Y):
        return [round((X - self.X0) / self.s, 3), round((self.Y1 - Y) / self.s, 3)]

    def m(self, papper_mm):
        """Pappersmått → modellmått."""
        return papper_mm * self.s

    # ---------------------------------------------------------------- grundelement
    def linje(self, pts, stil="normal"):
        self._add(dict(t="l", p=[self.P(*p) for p in pts], s=stil))

    def polygon(self, pts, fyll=None, stil=None):
        self._add(dict(t="pg", p=[self.P(*p) for p in pts], f=fyll, s=stil))

    def rekt(self, x0, y0, x1, y1, fyll=None, stil="tunn"):
        self.polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], fyll, stil)

    def cirkel(self, X, Y, r_papper, fyll=None, stil="tunn", modell=False):
        r = r_papper / self.s if modell else r_papper
        self._add(dict(t="c", c=self.P(X, Y), r=round(r, 3), f=fyll, s=stil))

    def text(self, X, Y, txt, a="lb", sz=7.5, rot=0, b=False, col="ink", bg=False, i=False):
        self._add(dict(t="tx", p=self.P(X, Y), txt=txt, a=a, sz=sz, rot=rot, b=b, col=col, bg=bg, i=i))

    # pappersrelativa element (offset i pappersmm från en modellpunkt)
    def ptext(self, X, Y, du, dv, txt, **kw):
        """Text förskjuten du, dv pappersmm (dv uppåt) från modellpunkten."""
        self.text(X + du * self.s, Y + dv * self.s, txt, **kw)

    # ---------------------------------------------------------------- symboler
    def pil(self, p_spets, riktning, langd=2.2, bredd=0.8, fyll="svart"):
        """Fylld pilspets i pappersmått, riktning = enhetsvektor i modellen."""
        d = np.asarray(riktning, float); d /= np.linalg.norm(d)
        n = np.array([-d[1], d[0]])
        sp = np.asarray(p_spets, float)
        b = sp - d * langd * self.s
        self.polygon([tuple(sp), tuple(b + n * bredd / 2 * self.s), tuple(b - n * bredd / 2 * self.s)], fyll, None)

    def bubbla(self, X, Y, txt, r=2.1, sz=7.0):
        """Positionsnummer i cirkel (r i pappersmm)."""
        self.cirkel(X, Y, r, fyll="vit", stil="tunn")
        self.text(X, Y, str(txt), a="cm", sz=sz, b=True)

    def hanvisning(self, mal, till, txt=None, a=None, sz=7.2, punkt=True, bubbla=None, bg=True, **kw):
        """Hänvisningslinje från modellpunkten mal till modellpunkten till (där texten eller bubblan står)."""
        if punkt:
            self.cirkel(*mal, 0.35, fyll="svart", stil=None)
        if bubbla is not None:
            d = np.subtract(mal, till); L = np.hypot(*d)
            r = 2.1 * self.s
            slut = np.asarray(till) + d / L * r if L > r else np.asarray(till)
            self.linje([mal, tuple(slut)], "tunn")
            self.bubbla(*till, bubbla)
            if txt:
                ax_ = 1 if (a or "lm")[0] == "l" else -1
                self.text(till[0] + ax_ * 3.0 * self.s, till[1], txt, a=a or "lm", sz=sz, bg=bg, **kw)
        else:
            self.linje([mal, till], "tunn")
            if txt:
                self.text(till[0], till[1], txt, a=a or "lm", sz=sz, bg=bg, **kw)

    def fordelning(self, p0, p1, stil="fordelning"):
        """Fördelningslinje för en grupp lika järn: linje med punkter i ändarna."""
        self.linje([p0, p1], stil)
        for p in (p0, p1):
            self.cirkel(*p, 0.5, fyll="svart", stil=None)

    def matt(self, p0, p1, avstand, txt=None, sz=7.0, ext=True, sida=1, hjalp_fran=None):
        """Måttlinje mellan p0 och p1, förskjuten avstand pappersmm åt vänster om riktningen p0→p1 (sida=-1 höger).
        Snedstreck i ändarna, hjälplinjer från punkterna (eller från hjalp_fran) och text ovanför linjen."""
        p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
        d = p1 - p0; L = np.linalg.norm(d)
        if L < 1e-6:
            return
        t = d / L; n = np.array([-t[1], t[0]]) * sida
        off = avstand * self.s
        q0, q1 = p0 + n * off, p1 + n * off
        if ext:
            for p, q in ((p0, q0), (p1, q1)):
                start = p + n * 1.0 * self.s
                self.linje([tuple(start), tuple(q + n * 1.5 * self.s)], "matt")
        self.linje([tuple(q0 - t * 1.5 * self.s), tuple(q1 + t * 1.5 * self.s)], "matt")
        sl = (t + n) / math.sqrt(2) * 1.1 * self.s
        for q in (q0, q1):
            self.linje([tuple(q - sl), tuple(q + sl)], "tunn")
        ang = math.degrees(math.atan2(t[1], t[0]))
        if ang > 90.5 or ang < -89.5:
            ang += 180
        mid = (q0 + q1) / 2
        nu = np.array([-math.sin(math.radians(ang)), math.cos(math.radians(ang))])
        pos = mid + nu * 0.8 * self.s
        self.text(pos[0], pos[1], txt if txt is not None else sv(L), a="cb", sz=sz, rot=round(ang, 2))

    def _tick(self, q, t, n):
        sl = (np.asarray(t) + np.asarray(n)) / math.sqrt(2) * 1.1 * self.s
        q = np.asarray(q, float)
        self.linje([tuple(q - sl), tuple(q + sl)], "tunn")

    def mattx(self, xs, Ylinje, Yfran, total=False, sz=6.8, texter=None):
        """Vågrät måttkedja på höjden Ylinje, hjälplinjer från (x, Yfran[i])."""
        g, f = 1.0 * self.s, 1.5 * self.s
        for x, y0 in zip(xs, Yfran):
            sg = 1 if Ylinje > y0 else -1
            self.linje([(x, y0 + sg * g), (x, Ylinje + sg * f)], "matt")
        self.linje([(xs[0] - f, Ylinje), (xs[-1] + f, Ylinje)], "matt")
        for x in xs:
            self._tick((x, Ylinje), (1, 0), (0, 1))
        for i, (a, b) in enumerate(zip(xs[:-1], xs[1:])):
            t = texter[i] if texter else sv(b - a)
            self.text((a + b) / 2, Ylinje + 0.8 * self.s, t, a="cb", sz=sz)

    def matty(self, ys, Xlinje, Xfran, total=False, sz=6.8, texter=None):
        """Lodrät måttkedja vid Xlinje, hjälplinjer från (Xfran[i], y); texten läses från höger."""
        g, f = 1.0 * self.s, 1.5 * self.s
        for y, x0 in zip(ys, Xfran):
            sg = 1 if Xlinje > x0 else -1
            self.linje([(x0 + sg * g, y), (Xlinje + sg * f, y)], "matt")
        self.linje([(Xlinje, ys[0] - f), (Xlinje, ys[-1] + f)], "matt")
        for y in ys:
            self._tick((Xlinje, y), (0, 1), (-1, 0))
        for i, (a, b) in enumerate(zip(ys[:-1], ys[1:])):
            t = texter[i] if texter else sv(b - a)
            self.text(Xlinje - 0.8 * self.s, (a + b) / 2, t, a="cb", sz=sz, rot=90)

    def kedja(self, pts, avstand, sida=1, sz=6.8, total=None):
        """Måttkedja längs punkterna (sorterade), med totalmått avstand + 6 mm om total."""
        for a, b in zip(pts[:-1], pts[1:]):
            self.matt(a, b, avstand, sida=sida, sz=sz)
        if total:
            self.matt(pts[0], pts[-1], avstand + 6, sida=sida, sz=sz)

    def brott(self, p0, p1, stil="tunn"):
        """Brottlinje (sicksack i mitten) mellan modellpunkterna p0 och p1."""
        p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
        d = p1 - p0; L = np.linalg.norm(d); t = d / L; n = np.array([-t[1], t[0]])
        z = 1.6 * self.s
        m = (p0 + p1) / 2
        pts = [p0, m - t * z, m - t * z * 0.4 + n * z * 1.2, m + t * z * 0.4 - n * z * 1.2, m + t * z, p1]
        self.linje([tuple(p) for p in pts], stil)

    def snittpil(self, p0, p1, namn, sida=1, sz=9):
        """Snittmarkering: grova streck i ändarna av snittlinjen, pilar åt synriktningen och bokstav."""
        p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
        t = (p1 - p0) / np.linalg.norm(p1 - p0); n = np.array([-t[1], t[0]]) * sida
        for p, sgn in ((p0, 1), (p1, -1)):
            self.linje([tuple(p), tuple(p + t * sgn * 6 * self.s)], "snitt")
            spets = p + n * 4.5 * self.s
            self.linje([tuple(p), tuple(spets - n * 1.8 * self.s)], "tunn")
            self.pil(tuple(spets), n, langd=2.0, bredd=1.4)
            tp = p - t * sgn * 2.2 * self.s + n * 2.2 * self.s
            self.text(tp[0], tp[1], namn, a="cm", sz=sz, b=True)

    def rubrik(self, X, Y, titel, skala=None, sz=10):
        """Vyns rubrik med understrykning och skala, vänsterjusterad i modellpunkten (X, Y) = baslinjen."""
        self.text(X, Y, titel, a="lb", sz=sz, b=True)
        if skala:
            self.text(X, Y - 4.2 * self.s, f"Skala 1:{skala}", a="lb", sz=7.2, col="gra")

    def skalstock(self, X, Y, langd_m=5, steg_m=1, hojd=1.2):
        """Skalstock i modellens enheter (m), nedre vänstra hörnet i (X, Y)."""
        h = hojd * self.s
        for i in range(int(langd_m / steg_m)):
            x0 = X + i * steg_m * 1000
            self.rekt(x0, Y, x0 + steg_m * 1000, Y + h, fyll="svart" if i % 2 == 0 else "vit", stil="tunn")
        for i in range(int(langd_m / steg_m) + 1):
            self.text(X + i * steg_m * 1000, Y - 1.0 * self.s, f"{i * steg_m:g}", a="ct", sz=6.2)
        self.text(X + langd_m * 1000 + 1.5 * self.s, Y + h / 2, "m", a="lm", sz=6.2)

    def json(self):
        return dict(x=self.x, y=self.y, w=self.w, h=self.h, klipp=self.klipp,
                    lager=[dict(namn=k, element=e) for k, e in self.lagren.items()])


def huvud(nummer, titel, skala, underlag, datum, rev, status="FÖR GRANSKNING", granskad="–"):
    """Ritningshuvud: projektets fasta uppgifter ur projekt.json och bladets egna."""
    return dict(projekt=PROJEKT["projekt"], fastighet=PROJEKT["fastighet"], upprattad=PROJEKT["upprattad"],
                titel=titel, skala=skala, datum=datum, granskad=granskad, underlag=underlag, status=status,
                rev=rev, nummer=nummer)


class Blad:
    def __init__(self, huvud, revisioner, kolumn, vyer, block=()):
        """block: fristående textblock på ritytan, dict(x, y, w, innehall=[kolumnblock])."""
        self.d = dict(huvud=huvud, revisioner=revisioner, kolumn=kolumn, vyer=vyer, block=list(block))

    def spara(self, path):
        d = dict(self.d, vyer=[v.json() for v in self.d["vyer"]])
        with open(path, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, separators=(",", ":"))

    def kompilera(self, json_path, pdf_path, root, dolj=()):
        """Kompilerar ritning.typ med bladets JSON (sökväg relativ till root). dolj: lager som inte ritas."""
        import typst
        rel = "/" + os.path.relpath(os.path.abspath(json_path), os.path.abspath(root)).replace(os.sep, "/")
        typst.compile(os.path.join(MALL, "ritning.typ"), output=pdf_path, root=root,
                      font_paths=["/usr/share/fonts"], sys_inputs={"blad": rel, "dolj": ",".join(dolj)})
