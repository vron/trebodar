"""Fönster och dörrar från VELFAC (VELFAC 200 ENERGY), för varianten velfac (trebodar/variant.py): karm, båge,
isolerruta, aluminium, bågprofiler och lister efter VELFAC:s systemritningar, i samma system som Elitfönsters
produkter (byggdelar/fonster.py), så att de sätts i öppningarna på samma sätt.

Produktens system: x längs bredden från karmens ytterkant, z uppåt från karmens underkant och y genom väggen med
y = 0 i karmens insida och negativt utåt. Profilerna anges som polygoner (d, e): d inåt från aluminiumets utsida
(y = d − DJUP) och e inåt från karmens ytterkant (negativt utanför den); varje sida är profilen svept längs sidan,
med gering 45° mot grannsidorna (eller rakt kapad där grannsidan saknas, som sidokarmarna mot tröskeln).

Systemritningarna (VELFAC 200 Energy, Standard details m.fl., utgåva 15, 07.26), förenklade till profilernas
ytterkonturer (kamrarna fyllda):
- Standard (A 3014.0817 överkarm, B 3014.0819 sidokarm, C 3014.0818 bottenkarm): karmen 149 djup, trä 114 och
  aluminium 35, karmträet 50 brett; bågen täcker karmen utifrån och glaskanten är 54 från karmens ytterkant runt om.
  Aluminiumlocket på karmträet upptill och vid sidorna (A, B), inte nedtill (C). Isolerruta 3-glas 48 mm.
- Vändbart fönster (G 3014.1271, sidokarm): karmträet 109 djupt vid ytterkanten med en aluminiumvinkel, bågens
  aluminium 6 mm innanför karmens ytterkant och beslagets zon 4 mm utanför den (inget får sitta där).
- Fönsterdörr, 24 mm tröskel (U 3014.3422): tröskel av aluminium mellan sidokarmarna, bågens underkant 6 mm över
  karmens underkant och en bottenprofil under bågen.
- Skjutdörr, 24 mm tröskel (J överkarm, K tröskel, M mittpost 3014.1509): bågen 30 mm över karmens underkant med
  hjulvagnen under (bågens bottenprofil), skena i överkarmen, och mötet mellan de två skjutbara bågarna med en
  träpost på den högra bågen; de fasta partierna har samma tröskel och kopplas till skjutdörren med en kopplingslist.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from modellering import Del, Form, Material, Montage, Placering, Union, box, polyeder, prisma

from trebodar.byggdelar.polygon import prisma_x
from trebodar.byggdelar.virke import fmt
from trebodar.material import BAGPROFIL, FONSTERTRA, GLAS, TATNINGSLIST

Profil = tuple[tuple[float, float], ...]          # (d, e)

DJUP = 149.0                # karmens djup med aluminiumet
TRA_UT = 35.0               # karmträets utsida (d)
SIKTLINJE = 54.0            # karmens ytterkant till glaskanten
GLASSKIVOR = ((8.35, 12.35), (30.35, 34.35), (52.35, 56.35))    # 3-glas 4-18-4-18-4 (d)
RUTKANT, DISTANS = 39.0, 49.5                                   # rutans kant och distanslistens insida (e)
DORR_BAGE, SKJUT_BAGE = 5.6, 30.3       # bågens underkant över karmens underkant: fönsterdörren och skjutdörren
KOPPLING, MOTE = 4.2, 4.0               # mellan partiernas karmar (locken möts), halva glipan mellan skjutbågarna
KOPPLING_D = 56.0                       # kopplingslisten mellan karmarna innanför locken (d)
POST_LANG = 50.0                        # skjutdörrens mittpost slutar under överkarmens trä


def _p(*pts: tuple[float, float]) -> Profil:
    return tuple(pts)


# ------------------------------------------------------------------ profilerna (d, e)
# standard (A, B, C): karmträet med spåret i ytterkanten och snedden mot bågen, aluminiumlocket (A, B) och bågen:
# aluminium utvändigt, bärande profil av glasfiberkomposit över rutan och den inre profilen med glaslisten
TRA_A = _p((35, 1.5), (36.5, 0), (105, 0), (105, 8), (115.5, 8), (115.5, 0), (146, 0), (149, 3), (149, 47),
           (146, 50), (80.5, 50), (80.5, 24.5), (79, 22), (37.5, 18), (35, 16))
LOCK_A = _p((5, -2.1), (56, -2.1), (56, 0), (5, 0))
BAGE_ALU_A = _p((0, 0.5), (0.5, 0), (5, 0), (5, 2), (3.5, 2), (3.5, 18.5), (28, 18.5), (28, 25.5), (25.5, 27.5),
                (23, 32.5), (28, 33.2), (28, 35.3), (3.5, 35.3), (3.5, 54), (0.5, 54), (0, 53.5))
KOMPOSIT_A = _p((23, 32.5), (25.5, 27.5), (30.5, 26.5), (36, 25.7), (55.5, 25.7), (57, 27), (73, 27.4), (74, 26.4),
                (76, 26.4), (76, 35.4), (73.5, 35.4), (73, 33.9), (58.5, 33.7), (57, 32.2), (45.7, 35.4), (33, 35.4),
                (28, 33.2))
INRE_A = _p((59.5, 35.4), (76, 35.4), (76, 40), (77.5, 40), (77.5, 54.5), (61, 55), (59.5, 53.5))
LIST_UT_A = _p((3.5, 41), (8.35, 41), (8.35, 54.5), (3.5, 54.5))                      # yttre glaslisten
LIST_IN_A = _p((56.35, 41), (59.5, 40), (59.5, 53.5), (57.5, 55.5), (56.35, 55))         # inre glaslisten
LIST_BAGE_A = _p((29, 19), (34, 17.8), (38, 18.05), (39.5, 21), (36, 25.7), (30.5, 26.5), (29, 26))   # mot karmen
LIST_KARM_A = _p((77.5, 37), (80.5, 37), (80.5, 47), (77.5, 47))                       # karmens tätningslist

# vändbart fönster, sidokarmen (G): karmträet grundare vid ytterkanten med aluminiumvinkeln (gångjärnsskenan) och
# bågen smalare, 6 mm innanför karmens ytterkant (beslagets zon); mittposten (M) har samma båge med aluminiumet ut
# till glipan mellan bågarna
TRA_G = _p((40.3, 0), (105.3, 0), (105.3, 7.7), (115.9, 7.7), (115.9, 0), (146.5, 0), (149, 2.5), (149, 47.2),
           (146.5, 49.7), (81.3, 49.7), (81.3, 24.5), (79.6, 22.5), (45.6, 18.8), (45.6, 10.1), (40.3, 9.9))
VINKEL_G = _p((37.8, 0), (40.3, 0), (40.3, 9.9), (45.6, 10.1), (45.6, 20.6), (35.5, 20.6), (35.5, 18.6), (43.5, 18.6),
              (43.5, 12.1), (37.8, 12.1))
BAGE_ALU_G = _p((0, 6.2), (5.5, 6.2), (5.5, 16.7), (25.5, 16.7), (25.5, 20.7), (5.5, 20.7), (5.5, 23.5), (20.6, 23.5),
                (20.6, 35), (3, 35), (3, 54), (0, 54))
BAGE_ALU_M = ((0.0, -0.5), (5.5, -0.5)) + BAGE_ALU_G[2:]
KOMPOSIT_G = _p((20.6, 23.7), (36, 23.7), (56.6, 29), (56.6, 33.5), (45.6, 35), (20.6, 35))
INRE_G = _p((56.6, 29), (78, 29), (80.5, 31.5), (80.5, 52.7), (62.5, 54.5), (59.5, 54.5), (59.5, 40.5), (56.6, 40.5))
INRE_M = _p((56.6, 29), (76, 29), (77.5, 31), (77.5, 52.7), (62.5, 54.5), (59.5, 54.5), (59.5, 40.5), (56.6, 40.5))
LIST_UT_G = _p((3, 41.7), (8.35, 41.7), (8.35, 54.5), (3, 54.5))
LIST_IN_G = _p((56.35, 41.7), (59.5, 40.5), (59.5, 54.5), (57.5, 55.5), (56.35, 55))
ZON_G = (-4.3, 6.3, 39.9)       # vändbeslagets zon utanför karmens ytterkant: e och d från, till

# skjutdörren: skenan i överkarmen (J) i stället för locket, tröskeln (K, samma som fönsterdörrens U), bågens
# bottenprofil med hjulvagnen (K) och fönsterdörrens bottenprofil (U), i (d, z) från karmens underkant
SKENA_J = _p((12.2, 2.5), (33, 0.8), (34.5, -1.5), (44, -1.5), (44, 0), (34.5, 0), (32.9, 1.5), (32.9, 16), (31.6, 16),
             (31.6, 4.5), (14.4, 5), (14.4, 10.3), (16.6, 10.3), (16.6, 11.8), (12.2, 11.8))
TROSKEL = _p((35, 0), (149, 0), (149, 21.5), (146.5, 23.8), (84, 23.8), (81.5, 21.5), (80.5, 13.5), (74.5, 11.5),
             (54, 8.5), (44, 6.5), (43, 9.3), (36.2, 9.8), (35, 6))
TROSKEL_H = 23.8
BOTTEN_K = _p((28, 21), (77.5, 21), (77.5, 65.7), (76, 65.7), (76, 56.0), (28, 56.0))
BOTTEN_U = _p((28, 14), (74.5, 11.5), (80.5, 13.5), (80.5, 41), (76, 41), (76, 31.3), (28, 31.3))
# mittposten (M) i (d, x från mötets mitt): trä 108 brett inifrån och smalare ut mellan bågarna
POST_M = _p((36, -23), (81, -28.5), (81, -54), (146, -54), (149, -51), (149, 51), (146, 54), (81, 54), (81, 20),
            (36, 9))


@dataclass(frozen=True)
class Sida:
    """En sidas profiler: karmens (trä, aluminium, lister) och bågens (aluminium, profil, lister) delar."""
    karm_tra: Profil | None = TRA_A
    karm_alu: Profil | None = LOCK_A
    karm_list: tuple[Profil, ...] = (LIST_KARM_A,)
    bage_alu: Profil = BAGE_ALU_A
    bage_profil: tuple[Profil, ...] = (KOMPOSIT_A, INRE_A)
    bage_list: tuple[Profil, ...] = (LIST_UT_A, LIST_IN_A, LIST_BAGE_A)
    kant: float = -2.1                   # karmens yttersta e vid anslutningsprofilen (aluminiumet utanför träet)


A = Sida()
C = Sida(karm_alu=None, kant=0.0)
A_DORR = Sida(bage_list=(LIST_UT_A, LIST_IN_A))          # dörrbågens underkant: bottenprofilen i stället för listen
G = Sida(karm_tra=TRA_G, karm_alu=VINKEL_G, karm_list=(), bage_alu=BAGE_ALU_G, bage_profil=(KOMPOSIT_G, INRE_G),
         bage_list=(LIST_UT_G, LIST_IN_G), kant=0.0)
J = Sida(karm_alu=SKENA_J, kant=-1.5)
M = Sida(karm_tra=None, karm_alu=None, karm_list=(), bage_alu=BAGE_ALU_M, bage_profil=(KOMPOSIT_G, INRE_M),
         bage_list=(LIST_UT_G, LIST_IN_G), kant=0.0)

Ram = tuple[float, float, float, float]          # x0, x1, z0, z1
GRANNAR = {"u": ("v", "h"), "o": ("v", "h"), "v": ("u", "o"), "h": ("u", "o")}   # vid början och slutet


def _punkt(sida: str, r: Ram, d: float, e: float, t: float) -> tuple[float, float, float]:
    x0, x1, z0, z1 = r
    y = d - DJUP
    return {"u": (t, y, z0 + e), "o": (t, y, z1 - e), "v": (x0 + e, y, t), "h": (x1 - e, y, t)}[sida]


def list_(sida: str, r: Ram, profil: Profil, gering: tuple[bool, bool]) -> Form:
    """Profilen svept längs sidan av ramen r (under och över längs x, sidorna längs z), med gering 45° i de ändar där
    gering är sann (profilens punkt med e ligger då e in från hörnet) och annars rakt kapad i ramens hörn."""
    x0, x1, z0, z1 = r
    a0, a1 = (x0, x1) if sida in "uo" else (z0, z1)
    horn = []
    for d, e in profil:
        horn += [_punkt(sida, r, d, e, a0 + e if gering[0] else a0), _punkt(sida, r, d, e, a1 - e if gering[1] else a1)]
    n = len(profil)
    ytor = [[2 * i for i in range(n)], [2 * i + 1 for i in range(n)]]
    ytor += [[2 * i, 2 * ((i + 1) % n), 2 * ((i + 1) % n) + 1, 2 * i + 1] for i in range(n)]
    return polyeder(horn, ytor)


def ram(r: Ram, sidor: dict[str, Profil | None], grannar: set[str] | None = None) -> Form | None:
    """En ram av profilerna per sida (u, o, v, h; None: ingen), med gering mot grannarna (standard: sidorna med
    profil) och rakt kapad mot de andra."""
    g = {s for s, p in sidor.items() if p is not None} if grannar is None else grannar
    listor = [list_(s, r, p, (GRANNAR[s][0] in g, GRANNAR[s][1] in g)) for s, p in sidor.items() if p is not None]
    if not listor:
        return None
    return listor[0] if len(listor) == 1 else Union(tuple(listor))


def _matt(b: float, h: float) -> str:
    return f"{fmt(b)}×{fmt(h)}"


@dataclass
class _Delar:
    """Delarna i en produkt, samlade per slag (en del per slag och parti)."""
    m: Montage
    kod: str
    alu: Material
    former: dict[str, list[Form]] = field(default_factory=dict)

    def lagg(self, slag: str, f: Form | None) -> None:
        if f is not None:
            self.former.setdefault(slag, []).append(f)

    def skriv(self, namn: str, slag: str, mat: Material, delnamn: str, artikel: str = "") -> None:
        f = self.former.pop(slag, [])
        if f:
            self.m.lagg(Del(delnamn, f[0] if len(f) == 1 else Union(tuple(f)), mat, artikel=artikel), Placering(),
                        f"{self.kod}-{namn}")


def _karm(p: _Delar, r: Ram, sidor: dict[str, Sida | None]) -> None:
    """Karmens trä, aluminium och lister i ramen r, med gering där karmträet möts."""
    g = {s for s, x in sidor.items() if x and x.karm_tra}
    p.lagg("tra", ram(r, {s: x.karm_tra if x else None for s, x in sidor.items()}, g))
    p.lagg("alu", ram(r, {s: x.karm_alu if x else None for s, x in sidor.items()}, g))
    n = max((len(x.karm_list) for x in sidor.values() if x), default=0)
    for i in range(n):
        p.lagg("list", ram(r, {s: x.karm_list[i] if x and i < len(x.karm_list) else None for s, x in sidor.items()},
                           g))


def _bage(p: _Delar, r: Ram, sidor: dict[str, Sida], slag: str = "") -> None:
    """Bågen i ramen r: aluminium, profiler, lister och isolerrutan (rutans kant RUTKANT innanför bågens kant)."""
    alla = set(sidor)
    p.lagg("bagealu" + slag, ram(r, {s: x.bage_alu for s, x in sidor.items()}))
    for i in range(2):
        p.lagg("bageprofil" + slag, ram(r, {s: x.bage_profil[i] for s, x in sidor.items()}))
    for i in range(max(len(x.bage_list) for x in sidor.values())):
        p.lagg("list" + slag, ram(r, {s: x.bage_list[i] if i < len(x.bage_list) else None for s, x in sidor.items()},
                                  alla))
    x0, x1, z0, z1 = r
    k = RUTKANT
    p.lagg("glas" + slag, Union(tuple(box(x0 + k, x1 - k, d0 - DJUP, d1 - DJUP, z0 + k, z1 - k) for d0, d1 in GLASSKIVOR)))
    for (_, a), (b, _) in zip(GLASSKIVOR[:-1], GLASSKIVOR[1:]):
        dist = _p((a, RUTKANT), (b, RUTKANT), (b, DISTANS), (a, DISTANS))
        p.lagg("list" + slag, ram(r, {s: dist for s in "uovh"}))


def _skriv_bage(p: _Delar, b: float, h: float, slag: str = "", namn: str = "") -> None:
    gb, gh = b - 2 * RUTKANT, h - 2 * RUTKANT
    p.skriv(f"{namn}BAGEALU", "bagealu" + slag, p.alu, f"Bågbeklädnad aluminium {_matt(b, h)}")
    p.skriv(f"{namn}BAGEPROFIL", "bageprofil" + slag, BAGPROFIL, f"Bågprofil komposit {_matt(b, h)}")
    p.skriv(f"{namn}GLAS", "glas" + slag, GLAS, f"Isolerruta 4-18-4-18-4 {_matt(gb, gh)}")


def _skriv_karm(p: _Delar, b: float, h: float, vad: str, artikel: str) -> None:
    p.skriv("KARM", "tra", FONSTERTRA, f"Karm {vad} {_matt(b, h)}", artikel)
    p.skriv("KARMALU", "alu", p.alu, f"Karmbeklädnad aluminium {_matt(b, h)}")


def vandbart(kod: str, b: float, h: float, alu: Material) -> Montage:
    """VELFAC 200 ENERGY vändbart fönster (toppvändbart, V228E): standardprofilerna upptill och nedtill (A, C) och
    vändfönstrets sidokarmar (G)."""
    m = Montage(kod, kod, f"Vändbart fönster VELFAC 200 ENERGY, karm {_matt(b, h)}")
    p = _Delar(m, kod, alu)
    r = (0.0, b, 0.0, h)
    _karm(p, r, {"u": C, "o": A, "v": G, "h": G})
    _bage(p, r, {"u": C, "o": A, "v": G, "h": G})
    _skriv_karm(p, b, h, "vändbart fönster", f"VELFAC 200 ENERGY vändbart fönster, karm {_matt(b, h)}")
    _skriv_bage(p, b, h)
    p.skriv("LIST", "list", TATNINGSLIST, f"Tätningslister {_matt(b, h)}")
    return m


def fast(kod: str, b: float, h: float, alu: Material) -> Montage:
    """VELFAC 200 ENERGY fast fönster med båge: standardprofilerna runt om, med samma siktlinje som de öppningsbara."""
    m = Montage(kod, kod, f"Fast fönster med båge VELFAC 200 ENERGY, karm {_matt(b, h)}")
    p = _Delar(m, kod, alu)
    r = (0.0, b, 0.0, h)
    _karm(p, r, {"u": C, "o": A, "v": A, "h": A})
    _bage(p, r, {"u": C, "o": A, "v": A, "h": A})
    _skriv_karm(p, b, h, "fast fönster", f"VELFAC 200 ENERGY fast fönster med båge, karm {_matt(b, h)}")
    _skriv_bage(p, b, h)
    p.skriv("LIST", "list", TATNINGSLIST, f"Tätningslister {_matt(b, h)}")
    return m


def _troskel(p: _Delar, x0: float, x1: float) -> None:
    """Tröskeln mellan sidokarmarnas trä (karmträet 50 brett)."""
    p.lagg("troskel", prisma_x([(d - DJUP, z) for d, z in TROSKEL], x0 + 50.0, x1 - 50.0))


def fonsterdorr(kod: str, b: float, h: float, alu: Material) -> Montage:
    """VELFAC 200 ENERGY 1-luft fönsterdörr (utåtgående) med 24 mm tröskel: sidokarmarna ned till karmens underkant,
    tröskeln mellan dem och bågen DORR_BAGE över karmens underkant med bottenprofilen."""
    m = Montage(kod, kod, f"Fönsterdörr VELFAC 200 ENERGY, 24 mm tröskel, karm {_matt(b, h)}")
    p = _Delar(m, kod, alu)
    _karm(p, (0.0, b, 0.0, h), {"u": None, "o": A, "v": A, "h": A})
    _troskel(p, 0.0, b)
    _bage(p, (0.0, b, DORR_BAGE, h), {"u": A_DORR, "o": A, "v": A, "h": A})
    p.lagg("botten", prisma_x([(d - DJUP, z) for d, z in BOTTEN_U], 50.0, b - 50.0))
    _skriv_karm(p, b, h, "fönsterdörr", f"VELFAC 200 ENERGY 1-luft fönsterdörr, 24 mm tröskel, karm {_matt(b, h)}")
    p.skriv("TROSKEL", "troskel", alu, f"Tröskel aluminium 24 mm {fmt(b - 100.0)}")
    _skriv_bage(p, b, h - DORR_BAGE)
    p.skriv("BOTTEN", "botten", alu, f"Bottenprofil dörrbåge {fmt(b - 100.0)}")
    p.skriv("LIST", "list", TATNINGSLIST, f"Tätningslister {_matt(b, h)}")
    return m


def partier(b: float) -> tuple[float, float]:
    """Skjutdörrens partier: de fasta och skjutdörren (karmarnas bredd), så att de fyra rutorna blir lika breda."""
    fast_b = (b - 2 * MOTE - 2 * KOPPLING) / 4
    return fast_b, 2 * fast_b + 2 * MOTE


def skjutdorr(kod: str, b: float, h: float, alu: Material) -> Montage:
    """VELFAC 200 ENERGY 2-luft skjutdörr med 24 mm tröskel mellan två fasta partier med samma tröskel, kopplade med
    kopplingslister: de två skjutbara bågarna i mitten skjuts ut och åt sidorna framför de fasta."""
    fb, sb = partier(b)
    m = Montage(kod, kod, f"Skjutdörr VELFAC 200 ENERGY, 2-luft med fasta partier, 24 mm tröskel, karm {_matt(b, h)}")
    p = _Delar(m, kod, alu)
    x = 0.0
    for parti, bredd in (("FV", fb), ("S", sb), ("FH", fb)):
        x0, x1 = x, x + bredd
        skjut = parti == "S"
        _karm(p, (x0, x1, 0.0, h), {"u": None, "o": J if skjut else A, "v": A, "h": A})
        _troskel(p, x0, x1)
        bagar: list[tuple[str, Ram, dict[str, Sida]]]
        if skjut:
            xm = (x0 + x1) / 2
            bagar = [("SV", (x0, xm - MOTE, SKJUT_BAGE, h), {"u": A_DORR, "o": A, "v": A, "h": M}),
                     ("SH", (xm + MOTE, x1, SKJUT_BAGE, h), {"u": A_DORR, "o": A, "v": M, "h": A})]
        else:
            bagar = [(parti, (x0, x1, SKJUT_BAGE, h), {"u": A_DORR, "o": A, "v": A, "h": A})]
        for namn, r, sidor in bagar:
            _bage(p, r, sidor, namn)
            # bågens bottenprofil med hjulvagnen, mellan karmträet och (vid mötet) mittpostens bågprofiler
            a = r[0] + (50.0 if sidor["v"] is A else SIKTLINJE + MOTE)
            e = r[1] - (50.0 if sidor["h"] is A else SIKTLINJE + MOTE)
            p.lagg("botten" + namn, prisma_x([(d - DJUP, z) for d, z in BOTTEN_K], a, e))
            bb, bh = r[1] - r[0], r[3] - r[2]
            _skriv_bage(p, bb, bh, namn, f"{namn}-")
            p.skriv(f"{namn}-BOTTEN", "botten" + namn, BAGPROFIL, f"Bågens bottenprofil med hjulvagn {fmt(e - a)}")
            p.skriv(f"{namn}-LIST", "list" + namn, TATNINGSLIST, f"Tätningslister {_matt(bb, bh)}")
        if skjut:
            post = [(xm + xc, d - DJUP) for d, xc in POST_M]
            m.lagg(Del(f"Mittpost trä {fmt(108.0)}×{fmt(h - POST_LANG - SKJUT_BAGE)}",
                       prisma(post, h - POST_LANG - SKJUT_BAGE, z0=SKJUT_BAGE), FONSTERTRA), Placering(),
                   f"{kod}-SH-POST")
        if parti != "FH":
            p.lagg("koppling", box(x1, x1 + KOPPLING, KOPPLING_D - DJUP, 0.0, 0.0, h))
        x = x1 + KOPPLING
    p.skriv("TROSKEL", "troskel", alu, f"Tröskel aluminium 24 mm, tre partier {fmt(b)}")
    _skriv_karm(p, b, h, "skjutdörr", f"VELFAC 200 ENERGY 2-luft skjutdörr, 24 mm tröskel, med två fasta partier, "
                                      f"karm {_matt(b, h)}")
    p.skriv("KOPPLING", "koppling", TATNINGSLIST, f"Kopplingslist {fmt(h)}")
    p.skriv("LIST", "list", TATNINGSLIST, f"Karmens tätningslister {_matt(b, h)}")
    return m


PRODUKTER = {"vridfönster": vandbart, "fast fönster": fast, "fönsterdörr": fonsterdorr, "skjutdörr": skjutdorr}
# karmens sidor upptill och vid sidorna (o, v, h) för anslutningarna runt fönstren och dörrarna (fonster_och_dorrar.py)
SIDOR: dict[str, dict[str, Sida]] = {"vridfönster": {"o": A, "v": G, "h": G}, "fast fönster": {"o": A, "v": A, "h": A},
                                     "fönsterdörr": {"o": A, "v": A, "h": A}, "skjutdörr": {"o": A, "v": A, "h": A}}
