"""Öppningarna i ytterväggarna: fönster (F) och dörrar (D) per vägg, numrerade längs väggen, med produkttyp.

Lägen i väggens system (skelett.VAGGAR): u längs väggen och z från bjälklagets överkant. Måtten är regelverkets
öppning (Onshape-modellens mått).
Huvudentrén 1SO-D1 (planritning 201) saknades i Onshape-modellen; bara öppningen i regelverket fanns. Källarens
fönster F1–F3 (R-05) står i väggen 2NO:s system under bjälklaget. Fasaden, isoleringen och insidan får hål här och
fönster- och dörrmodulen sätter produkterna i dem.

Typerna: "vändfönster", "fast fönster" (med båge), "fönsterdörr" (1-luft), "skjutdörr" (2-luft skjutdörr mellan
två fasta partier), "ytterdörr" och "pardörr" (källarens dörr D1, i väggen 3NO:s system under bjälklaget).

Fönstren och fönsterdörrarna är från VELFAC (byggdelar/velfac.py), med VELFAC:s fogar: karmen FOG_V innanför
regelverket vid sidorna och upptill, fönstren på en påföring PAFORING_V över fogen nedtill och dörrarna på en bädd
BADD_V. Insidans skikt slutar i karmens linje, under fönstrens bottenkarm vid fönsterbänken (Oppning.inre).
Ytterdörrarna med panel (byggdelar/ytterdorrar.py) har karmen DREV innanför öppningen runt om.
"""
from __future__ import annotations

from dataclasses import dataclass

from trebodar import skelett as S
from trebodar.byggdelar import ytterdorrar as YD
from trebodar.byggdelar.ytterdorrar import DREV
from trebodar.byggdelar.velfac import DJUP as VELFAC_DJUP, PRODUKTER as VELFAC_PRODUKTER, TRA_UT as VELFAC_TRA_UT
from trebodar.hus.grund import kallarvaggar as K


INDRAG = 22.0                # ytterdörrarnas karm: utsidan innanför panelens utsida (i panelens insida)
BLECK_T = 1.5                # fönsterblecket under fönstren (fonster_och_dorrar.py, fasad.py)
# Smyglisterna (ärende #24): en extra synlig träkant runt fönstren och dörrarna invändigt [mm]. Insidans skivor (OSB
# och gips) slutar så mycket längre från karmen vid sidorna och överkanten, och lister av oljad ask i skivornas
# tjocklek fyller ut mot smygen (fonster_och_dorrar.py), så att träet syns 20 + SMYGLIST mm runt öppningen. 0: inga
# lister, bara smygen. Inte i badrummet (kakel runt om).
SMYGLIST = 0.0
# VELFAC: fogarna runt karmen, påföringen under fönstren och bädden under dörrarna, aluminiumets
# utsida INDRAG_V innanför panelens utsida (VELFAC:s minsta indrag är 20) och fasaden (panel och läkt) KLADD_V från
# karmen vid sidorna och upptill; fönsterbänken BANK_V under bottenkarmen (fonster_och_dorrar.py)
FOG_V, PAFORING_V, BADD_V = 15.0, 18.0, 10.0
INDRAG_V, KLADD_V, BANK_V = 20.0, 10.0, 20.0
# VELFAC:s fönsterbleck (fonster_och_dorrar.py, fasad.py): från påföringens utsida (karmträets utsida, i utegipsens
# utsida W_TRA_V) med fallet BLECK_FALL_V utåt till droppnäsan BLECK_UT_V utanför panelen
BLECK_FALL_V, BLECK_UT_V, BLECK_NAS_V, BLECK_UPP_V = 0.25, 30.0, 14.0, 15.0
W_TRA_V = -S.T_FASAD + INDRAG_V + VELFAC_TRA_UT


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
    def velfac(self) -> bool:
        """Produkten är från VELFAC (fönstren och fönsterdörrarna; inte ytterdörrarna med panel)."""
        return self.typ in VELFAC_PRODUKTER

    @property
    def karm(self) -> tuple[float, float, float, float]:
        """Karmens yttermått (u0, z0, u1, z1): VELFAC FOG_V innanför öppningen och påföringen eller bädden nedtill,
        ytterdörrarna med panel DREV runt om."""
        if self.velfac:
            nere = BADD_V if self.typ in DORRAR else FOG_V + PAFORING_V
            return (self.u0 + FOG_V, self.z0 + nere, self.u1 - FOG_V, self.z1 - FOG_V)
        return (self.u0 + DREV, self.z0 + DREV, self.u1 - DREV, self.z1 - DREV)

    @property
    def w_karm(self) -> float:
        """Karmens insida i väggens w: VELFAC:s aluminium INDRAG_V innanför panelens utsida, ytterdörrarnas karm med
        aluminiumet i panelens insida."""
        if self.velfac:
            return -S.T_FASAD + INDRAG_V + VELFAC_DJUP
        return -S.T_FASAD + INDRAG + YD.PRODUKTER[self.typ][1]

    @property
    def golvfonster(self) -> bool:
        """Fönster från golvet (en bräda från golvet till karmen i stället för fönsterbänken)."""
        return self.typ not in DORRAR and self.z0 == 0.0

    @property
    def inre(self) -> tuple[float, float, float, float]:
        """Linjen där insidans skikt slutar (u0, z0, u1, z1): karmens yttermått, vid fönstren nedtill under
        fönsterbänken (från golvet vid fönstren från golvet)."""
        ku0, kz0, ku1, kz1 = self.karm
        if self.typ not in DORRAR:
            kz0 = self.z0 if self.golvfonster else kz0 - BANK_V
        return (ku0, kz0, ku1, kz1)

    @property
    def skivornas_hal(self) -> tuple[float, float, float, float]:
        """Hålet i insidans skivor (u0, z0, u1, z1): insidans linje (dörrarna från golvet) och SMYGLIST till vid
        sidorna och överkanten, för smyglisterna."""
        ku0, kz0, ku1, kz1 = self.inre
        return (ku0 - SMYGLIST, self.z0 if self.typ in DORRAR else kz0, ku1 + SMYGLIST, kz1 + SMYGLIST)


def velfac_bleck_z(o: Oppning, w: float) -> float:
    """Fönsterbleckets översida vid djupet w (w ≤ W_TRA_V): påföringens underkant vid karmträets utsida och
    fallet utåt."""
    return o.z0 + FOG_V - (W_TRA_V - w) * BLECK_FALL_V


_R = (
    ("1NO", "vändfönster", 750, 1750, 1100, 2100, "window_10x10_red"),
    ("1NO", "fast fönster", 3000, 3600, 0, 2100, "window_21x6_red"),
    ("1NV", "vändfönster", 865, 1865, 1100, 2100, "window_10x10_red"),
    ("1NV", "fönsterdörr", 3035, 4035, 0, 2100, "wdoor_21x10_red"),
    ("1SO", "fast fönster", 1118, 1718, 1400, 2000, "window_6x6_red"),
    ("1SO", "fast fönster", 2318, 2918, 1400, 2000, "window_6x6_red"),
    ("1SO", "ytterdörr", 5080, 6080, 0, 2100, ""),                    # huvudentrén (planritning 201)
    ("1SO", "fast fönster", 10718, 11318, 1400, 2000, "window_6x6_red"),
    ("1SV", "fast fönster", 1135, 3235, 0, 2186, "window_21x21_red"),
    ("2NO", "vändfönster", 645, 1645, 1100, 2100, "window_10x10_gray"),
    ("2NO", "vändfönster", 2045, 3045, 1100, 2100, "window_10x10_gray"),
    ("2SO", "fönsterdörr", 490, 1590, 0, 2100, "wdoor_21x11_gray"),
    ("2SV", "skjutdörr", 260, 5060, 0, S.BALKAR["DB2"].uk - 45, "slidedoor"),   # upp till hammarbandet
    ("3NO", "fast fönster", 995, 1595, 0, 2100, "window_21x6_gray"),
    ("3NO", "vändfönster", 2845, 3845, 1100, 2100, "window_10x10_gray"),
    ("3NV", "vändfönster", 560, 1360, 1300, 2100, "window_8x8_gray"),
    ("3NV", "vändfönster", 2260, 3060, 1300, 2100, "window_8x8_gray"),
    ("3NV", "vändfönster", 3960, 4760, 1300, 2100, "window_8x8_gray"),
    ("3NV", "vändfönster", 7117.5, 8117.5, 1100, 2100, "window_10x10_gray"),
    ("3NV", "vändfönster", 8970, 9970, 1100, 2100, "window_10x10_gray"),
    ("3SO", "fönsterdörr", 172.5, 1072.5, 0, 2100, "wdoor_21x9_gray"),
    ("3SV", "vändfönster", 695, 1695, 1100, 2100, "window_10x10_gray"),
    ("3SV", "fast fönster", 2775, 3675, 0, 2100, "wdoor_21x9_gray"),
)
DORRAR = ("fönsterdörr", "skjutdörr", "ytterdörr", "pardörr")


def _numrera() -> dict[str, list[Oppning]]:
    ut: dict[str, list[Oppning]] = {}
    for vagg, typ, u0, u1, z0, z1, ref in sorted(_R, key=lambda r: (r[0], r[2])):
        lst = ut.setdefault(vagg, [])
        bokstav = "D" if typ in DORRAR else "F"
        n = sum(1 for o in lst if o.kod.split("-")[1][0] == bokstav) + 1
        lst.append(Oppning(f"{vagg}-{bokstav}{n}", vagg, typ, float(u0), float(u1), float(z0), float(z1), ref))
    return ut


def _kallarfonster() -> list[Oppning]:
    """Källarens fönster (vändfönster) i fasadens plan ovanför, väggen 2NO (cellplastens utsida i w = 0): mellan
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
        ut.append(Oppning(namn, "2NO", "vändfönster", x0 - v.origo[0], x1 - v.origo[0], K.Z0 + zb + K.CELL, K.Z1))
    return ut


def _kallardorr() -> list[Oppning]:
    """Källarens ytterdörr D1 (pardörr, ärende #33) i fasadens plan ovanför, väggen 3NO (cellplastens utsida i
    w = 0): mellan smygarnas cellplast och från bottenplattan till bjälklagets underkant (kallarvaggar)."""
    v = S.YTTERVAGGAR["3NO"]
    vaggar = {k.namn: k for k in K.VAGGAR}
    ut = []
    for namn, va, vb, zb in K.OPPNINGAR:
        a, b = vaggar[va], vaggar[vb]
        if zb > 0 or a.typ != "yttre":
            continue
        assert a.riktning == b.riktning == "h" and abs(a.c - K.KARNA / 2 - K.CELL - v.origo[1]) < 1e-6
        x0, x1 = max(a.a, a.b) + K.CELL, min(b.a, b.b) - K.CELL
        ut.append(Oppning(namn, "3NO", "pardörr", x0 - v.origo[0], x1 - v.origo[0], K.Z0, K.Z1))
    return ut


OPPNINGAR = _numrera()
OPPNINGAR["2NO"] += _kallarfonster()
OPPNINGAR["3NO"] = OPPNINGAR.get("3NO", []) + _kallardorr()


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


# innerdörrarna som i Onshape-modellen (fickdörrarnas fickor där), alla fickdörrar; öppningarna mellan de färdiga
# ytorna som smygen sitter mot. ID2:s ficka går mot norr i 2B, med karmstolpen LD2_1 vid fickans ände (dalbalk 2 spänner
# över dörren och fickan, K-01), och öppningen börjar vid trapphålets vägg L6. ID5:s ficka går mot öster
# och slutar före stolpen LN1_1 (x 11 565), med 500 mm vägg väster om öppningen för garderober i sovrummet (blad 800,
# öppningen 725). ID6 stängs mot L11:s gips och fickan går från L12 in i 2C, söder om stolpen LD4_1 (som står 12 mm
# norr om fickan)
INNERDORRAR = (
    Innerdorr("ID1", "L11", 1010.0, 1860.0, -1, rum="badrummet", ficka=True),
    Innerdorr("ID2", "2B", 3994.5, 4826.0, -1, 2200.0, "trappan till källaren, mellan karmstolparna LD2_1 och LD2_2",
              mot=-1, ficka=True),
    # ID3 stängs mot L1:s gips, fickan slutar vid L3; ID4 börjar efter L3, fickan slutar vid L4
    Innerdorr("ID3", "L2", 25.0, 841.0, 1, rum="kontoret i höger huskropp", ficka=True),
    Innerdorr("ID4", "L2", 1891.0, 2732.0, 1, rum="kontoret/gästrummet", ficka=True),
    Innerdorr("ID5", "L1", 525.0, 1250.0, 1, rum="sovrummet i höger huskropp", ficka=True),
    Innerdorr("ID6", "L12", 25.0, 1060.0, 1, rum="sovrummet i mittre huskroppen, från allrummet", ficka=True),
)

# öppningar i innerväggarna utan dörr: (vägg, u0, u1, z0, z1, vad), hål i väggarnas skikt. Kaminens öppning (x 6 400–
# 7 236) är symmetrisk kring insatsen (x 6 818, kamin.X_MITT), så att fronten syns lika bred på båda sidorna; i
# planritning 201 är den bredare åt öster (u 2 993)
INNEROPPNINGAR = (("2C", 1983.0, 2819.0, 0.0, 2045.0, "kaminen (Rais 600), planritning 201"),)
