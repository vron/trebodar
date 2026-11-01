"""Öppningarna i ytterväggarna: fönster (F) och dörrar (D) per vägg, numrerade längs väggen.

Lägen i väggens system (skelett.VAGGAR): u längs väggen och z från bjälklagets överkant, som karmens yttermått i
Onshape-modellen. Huvudentrén 1SO-D1 (planritning 201) saknades där; bara öppningen i regelverket fanns, och dörren
ligger i den. Fasaden, isoleringen och insidan får hål här och fönster- och dörrmodulen sätter karmar, blad och glas
i dem.
"""
from __future__ import annotations

from dataclasses import dataclass

from trebodar import skelett as S


@dataclass(frozen=True)
class Oppning:
    kod: str                 # t.ex. "1SO-F1"
    vagg: str
    typ: str                 # "fönster", "dörr", "skjutdörr", "fönsterdörr"
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


_R = (
    ("1NO", "fönster", 750, 1750, 1100, 2100, "window_10x10_red"),
    ("1NO", "fönsterdörr", 3000, 3600, 0, 2100, "window_21x6_red"),
    ("1NV", "fönster", 865, 1865, 1100, 2100, "window_10x10_red"),
    ("1NV", "dörr", 3035, 4035, 0, 2100, "wdoor_21x10_red"),
    ("1SO", "fönster", 1118, 1718, 1400, 2000, "window_6x6_red"),
    ("1SO", "fönster", 2318, 2918, 1400, 2000, "window_6x6_red"),
    ("1SO", "dörr", 5080, 6080, 0, 2100, ""),                    # huvudentrén (planritning 201)
    ("1SO", "fönster", 10718, 11318, 1400, 2000, "window_6x6_red"),
    ("1SV", "fönster", 1135, 3235, 0, 2186, "window_21x21_red"),
    ("2NO", "fönster", 645, 1645, 1100, 2100, "window_10x10_gray"),
    ("2NO", "fönster", 2045, 3045, 1100, 2100, "window_10x10_gray"),
    ("2SO", "dörr", 490, 1590, 0, 2100, "wdoor_21x11_gray"),
    ("2SV", "skjutdörr", 260, 5060, 0, S.BALKAR["DB2"].uk - 45, "slidedoor"),   # upp till hammarbandet
    ("3NO", "fönsterdörr", 995, 1595, 0, 2100, "window_21x6_gray"),
    ("3NO", "fönster", 2845, 3845, 1100, 2100, "window_10x10_gray"),
    ("3NV", "fönster", 560, 1360, 1300, 2100, "window_8x8_gray"),
    ("3NV", "fönster", 2260, 3060, 1300, 2100, "window_8x8_gray"),
    ("3NV", "fönster", 3960, 4760, 1300, 2100, "window_8x8_gray"),
    ("3NV", "fönster", 7117.5, 8117.5, 1100, 2100, "window_10x10_gray"),
    ("3NV", "fönster", 8970, 9970, 1100, 2100, "window_10x10_gray"),
    ("3SO", "dörr", 172.5, 1072.5, 0, 2100, "wdoor_21x9_gray"),
    ("3SV", "fönster", 695, 1695, 1100, 2100, "window_10x10_gray"),
    ("3SV", "dörr", 2775, 3675, 0, 2100, "wdoor_21x9_gray"),
)


def _numrera() -> dict[str, list[Oppning]]:
    ut: dict[str, list[Oppning]] = {}
    for vagg, typ, u0, u1, z0, z1, ref in sorted(_R, key=lambda r: (r[0], r[2])):
        lst = ut.setdefault(vagg, [])
        bokstav = "D" if typ in ("dörr", "skjutdörr") else "F"
        n = sum(1 for o in lst if o.kod.split("-")[1][0] == bokstav) + 1
        lst.append(Oppning(f"{vagg}-{bokstav}{n}", vagg, typ, float(u0), float(u1), float(z0), float(z1), ref))
    return ut


OPPNINGAR = _numrera()


@dataclass(frozen=True)
class Innerdorr:
    """En innerdörr i en bärande innervägg (skelett.INNERVAGGAR) eller en lätt vägg (invandigt.vaggar.LATTA):
    öppningen u0–u1 längs väggen och skjutdörren utanpå väggen på sidan w < 0 (sida −1) eller w > tjockleken (+1),
    som öppnas åt växande (mot +1) eller minskande u. Bladet går fore och efter förbi öppningen."""
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

    @property
    def bredd(self) -> float:
        return self.u1 - self.u0


# skjutdörrarna enligt planritning 201 rev 02, med modellens väggar
INNERDORRAR = (
    Innerdorr("ID1", "L11", 920.0, 1820.0, -1, rum="badrummet (dörr 900)"),
    Innerdorr("ID2", "2B", 3992.0, 4826.0, -1, 2200.0, "trappan till källaren, mellan karmstolparna LD2_1 och LD2_2"),
    # korridorens hörn vid L1 och L2: ID5 öppnas mot väster och slutar före korridorväggen, ID3 börjar efter ID5:s blad
    Innerdorr("ID3", "L2", 120.0, 1066.0, 1, rum="kontoret i höger huskropp"),
    Innerdorr("ID4", "L2", 1927.0, 2852.0, 1, rum="kontoret/gästrummet"),
    Innerdorr("ID5", "L1", 558.0, 1460.0, 1, rum="sovrummet i höger huskropp", mot=-1, efter=0.0),
    Innerdorr("ID6", "L12", 0.0, 1060.0, 1, rum="sovrummet i mittre huskroppen, från allrummet", fore=-25.0),
)

# öppningar i innerväggarna utan dörr: (vägg, u0, u1, z0, z1, vad), hål i väggarnas skikt
INNEROPPNINGAR = (("2C", 1983.0, 2993.0, 0.0, 2045.0, "kaminen (Rais 600), planritning 201"),)
