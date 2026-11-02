"""Öppningarna i ytterväggarna: fönster (F) och dörrar (D) per vägg, numrerade längs väggen, med produkttyp.

Lägen i väggens system (skelett.VAGGAR): u längs väggen och z från bjälklagets överkant. Måtten är regelverkets
öppning (Onshape-modellens mått), som är Elitfönsters modulmått: karmen är 20 mm mindre (byggdelar/fonster.py).
Huvudentrén 1SO-D1 (planritning 201) saknades i Onshape-modellen; bara öppningen i regelverket fanns. Källarens
fönster F1–F3 (R-05) står i väggen 2NO:s system under bjälklaget. Fasaden, isoleringen och insidan får hål här och
fönster- och dörrmodulen sätter produkterna i dem.

Typerna: "vridfönster", "fast fönster", "fönsterdörr" (helglasad), "skjutdörr" (lyftglid, fyra delar) och
"ytterdörr".
"""
from __future__ import annotations

from dataclasses import dataclass

from trebodar import skelett as S
from trebodar.byggdelar.fonster import DREV
from trebodar.hus.grund import kallarvaggar as K


@dataclass(frozen=True)
class Oppning:
    kod: str                 # t.ex. "1SO-F1"
    vagg: str
    typ: str                 # produkttyp, se ovan
    u0: float
    u1: float
    z0: float
    z1: float
    onshape: str = ""        # namnet i Onshape-modellen

    @property
    def bredd(self) -> float:
        return self.u1 - self.u0

    @property
    def hojd(self) -> float:
        return self.z1 - self.z0

    @property
    def karm(self) -> tuple[float, float, float, float]:
        """Karmens yttermått (u0, z0, u1, z1): DREV innanför öppningen runt om."""
        return (self.u0 + DREV, self.z0 + DREV, self.u1 - DREV, self.z1 - DREV)


_R = (
    ("1NO", "vridfönster", 750, 1750, 1100, 2100, "window_10x10_red"),
    ("1NO", "fast fönster", 3000, 3600, 0, 2100, "window_21x6_red"),
    ("1NV", "vridfönster", 865, 1865, 1100, 2100, "window_10x10_red"),
    ("1NV", "fönsterdörr", 3035, 4035, 0, 2100, "wdoor_21x10_red"),
    ("1SO", "fast fönster", 1118, 1718, 1400, 2000, "window_6x6_red"),
    ("1SO", "fast fönster", 2318, 2918, 1400, 2000, "window_6x6_red"),
    ("1SO", "ytterdörr", 5080, 6080, 0, 2100, ""),                    # huvudentrén (planritning 201)
    ("1SO", "fast fönster", 10718, 11318, 1400, 2000, "window_6x6_red"),
    ("1SV", "fast fönster", 1135, 3235, 0, 2186, "window_21x21_red"),
    ("2NO", "vridfönster", 645, 1645, 1100, 2100, "window_10x10_gray"),
    ("2NO", "vridfönster", 2045, 3045, 1100, 2100, "window_10x10_gray"),
    ("2SO", "fönsterdörr", 490, 1590, 0, 2100, "wdoor_21x11_gray"),
    ("2SV", "skjutdörr", 260, 5060, 0, S.BALKAR["DB2"].uk - 45, "slidedoor"),   # upp till hammarbandet
    ("3NO", "fast fönster", 995, 1595, 0, 2100, "window_21x6_gray"),
    ("3NO", "vridfönster", 2845, 3845, 1100, 2100, "window_10x10_gray"),
    ("3NV", "vridfönster", 560, 1360, 1300, 2100, "window_8x8_gray"),
    ("3NV", "vridfönster", 2260, 3060, 1300, 2100, "window_8x8_gray"),
    ("3NV", "vridfönster", 3960, 4760, 1300, 2100, "window_8x8_gray"),
    ("3NV", "vridfönster", 7117.5, 8117.5, 1100, 2100, "window_10x10_gray"),
    ("3NV", "vridfönster", 8970, 9970, 1100, 2100, "window_10x10_gray"),
    ("3SO", "fönsterdörr", 172.5, 1072.5, 0, 2100, "wdoor_21x9_gray"),
    ("3SV", "vridfönster", 695, 1695, 1100, 2100, "window_10x10_gray"),
    ("3SV", "fast fönster", 2775, 3675, 0, 2100, "wdoor_21x9_gray"),
)
DORRAR = ("fönsterdörr", "skjutdörr", "ytterdörr")


def _numrera() -> dict[str, list[Oppning]]:
    ut: dict[str, list[Oppning]] = {}
    for vagg, typ, u0, u1, z0, z1, ref in sorted(_R, key=lambda r: (r[0], r[2])):
        lst = ut.setdefault(vagg, [])
        bokstav = "D" if typ in DORRAR else "F"
        n = sum(1 for o in lst if o.kod.split("-")[1][0] == bokstav) + 1
        lst.append(Oppning(f"{vagg}-{bokstav}{n}", vagg, typ, float(u0), float(u1), float(z0), float(z1), ref))
    return ut


def _kallarfonster() -> list[Oppning]:
    """Källarens fönster (vridfönster) i fasadens plan ovanför, väggen 2NO (cellplastens utsida i w = 0): mellan
    smygarnas cellplast och från bröstningens cellplast till bjälklagets underkant (kallarvaggar)."""
    v = S.YTTERVAGGAR["2NO"]
    vaggar = {k.namn: k for k in K.VAGGAR}
    ut = []
    for namn, va, vb, zb in K.OPPNINGAR:
        if zb <= 0:
            continue
        a, b = vaggar[va], vaggar[vb]
        assert a.riktning == b.riktning == "h" and abs(a.c - K.KARNA / 2 - K.CELL - v.origo[1]) < 1e-6
        x0, x1 = max(a.a, a.b) + K.CELL, min(b.a, b.b) - K.CELL
        ut.append(Oppning(namn, "2NO", "vridfönster", x0 - v.origo[0], x1 - v.origo[0], K.Z0 + zb + K.CELL, K.Z1))
    return ut


OPPNINGAR = _numrera()
OPPNINGAR["2NO"] += _kallarfonster()


@dataclass(frozen=True)
class Innerdorr:
    """En innerdörr i en bärande innervägg (skelett.INNERVAGGAR) eller en lätt vägg (invandigt.vaggar.LATTA):
    öppningen u0–u1 längs väggen och skjutdörren utanpå väggen på sidan w < 0 (sida −1) eller w > tjockleken (+1),
    som öppnas åt växande (mot +1) eller minskande u. Bladet går fore och efter förbi öppningen. En fickdörr (ficka)
    går in i en ficka i väggen åt det håll den öppnas: bladet är FICKA_UT bredare än öppningen (så långt in i fickan
    står det i stängt läge) och fickan FICKA_SPEL längre än bladet."""
    kod: str
    vagg: str
    u0: float
    u1: float
    sida: int
    hojd: float = 2100.0
    rum: str = ""
    mot: int = 1
    fore: float = 30.0
    efter: float = 30.0
    ficka: bool = False

    @property
    def bredd(self) -> float:
        return self.u1 - self.u0

    @property
    def fickan(self) -> tuple[float, float]:
        """Fickans utsträckning längs väggen (u), från öppningens kant."""
        lp = self.bredd + FICKA_UT + FICKA_SPEL
        return (self.u1, self.u1 + lp) if self.mot > 0 else (self.u0 - lp, self.u0)


# fickdörrarna som i Onshape-modellen: blad 925 i ficka 980, bladet 75 in i fickan i stängt läge
FICKA_UT = 75.0              # bladet är så mycket bredare än öppningen
FICKA_SPEL = 55.0            # fickan är så mycket längre än bladet


# innerdörrarna som i Onshape-modellen (fickdörrarnas fickor där). ID2, ID5 och ID6 är skjutdörrar utanpå väggen:
# deras fickor i Onshape-modellen går genom stolparna LD2_2, LN1_1 och LD4_1, som inte fanns där (modell-todo)
INNERDORRAR = (
    Innerdorr("ID1", "L11", 1010.0, 1860.0, -1, rum="badrummet", ficka=True),
    Innerdorr("ID2", "2B", 3992.0, 4826.0, -1, 2200.0, "trappan till källaren, mellan karmstolparna LD2_1 och LD2_2"),
    # ID3 stängs mot L1:s gips, fickan slutar vid L3; ID4 börjar efter L3, fickan slutar vid L4
    Innerdorr("ID3", "L2", 25.0, 841.0, 1, rum="kontoret i höger huskropp", ficka=True),
    Innerdorr("ID4", "L2", 1891.0, 2732.0, 1, rum="kontoret/gästrummet", ficka=True),
    Innerdorr("ID5", "L1", 610.0, 1460.0, 1, rum="sovrummet i höger huskropp", mot=-1, efter=0.0),
    Innerdorr("ID6", "L12", 0.0, 1060.0, 1, rum="sovrummet i mittre huskroppen, från allrummet", fore=-25.0),
)

# öppningar i innerväggarna utan dörr: (vägg, u0, u1, z0, z1, vad), hål i väggarnas skikt
INNEROPPNINGAR = (("2C", 1983.0, 2993.0, 0.0, 2045.0, "kaminen (Rais 600), planritning 201"),)
