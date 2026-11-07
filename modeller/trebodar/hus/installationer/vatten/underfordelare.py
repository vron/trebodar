"""Underfördelarna (ärendena #50 och #51): små fördelare utanpå en vägg i källaren, matade från huvudfördelarna i
fördelarskåpet med ett rör per media, som ett tappställe i deras ordning (teknikrum.ORDNING), och med egna utgångar
till sina tappställen. De sitter åtkomliga i ett rum med golvbrunn, utan fördelarskåp och läckageindikering: ett
läckage syns och rinner till golvbrunnen.

- UF1 i det stora rummet i högra huskroppen, på källarväggen V14 under köket intill diskhons avlopp, som går ned längs
  väggen (../avlopp): kallt och varmt till diskbänken KO-DB1 och kallt till diskmaskinen KO-DM1 i ön. Matningen kommer
  i stråket O norr om diskbänken och ned till stammarnas norra ände.
- UF2 i rummet öster om KL2 under badrummet, på KL1: kallt till WC:n BA-WC1 och till tvättmaskinen BA-TM1 i skåpet i
  badrummet, var sin utgång. Huvudfördelarnas filer räcker inte till ett rör till: det sjuttonde krockar med
  ventilationens kanal FF3-K2 (#50).

Stammarna som i fördelarskåpet: varmvattnet bakom och högre, kallvattnet framför, utgångarna uppåt c/c FIL i rörens
filer, och rören rakt upp i mellanbjälklaget mellan underkantsnätets järn: underfördelaren flyttas längs väggen så
lite som behövs för att alla rören, matningen och utgångarna, ska gå fria. Matningen kommer rakt ned ur bjälklaget
till stammarnas början (utgång 0). Rören till tappställena går i ett eget stråk från väggen in i rummet, en fil per
rör som i huvudfördelarnas stråk.

Dimensionerande flöde för matningen: det största normflödet och hälften av de andras.

Koordinater i mm (K-05), z från plan 1:s golv.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import cache

from trebodar.hus.invandigt.kallarens_innervaggar import GIPS_T, VAGGAR as KL

from ..montering import KALLARTAK, Montering, Vek, kallarvagg
from ..strak import Strak, mellan_jarnen
from .katalog import INLOPP, ROR_I_ROR_16, ROR_I_ROR_18, UNDERFORDELARE_KV, UNDERFORDELARE_VV
from .punkter import FIL, R_ROR, Z_ROR, Fordelare, Tappstalle
from .typer import Fordelartyp, Rortyp, Tappstalletyp

AVSTAND = {"VV": 40.0, "KV": 110.0}         # stammarnas mitt från väggens yta: varmvattnet bakom, kallvattnet framför
UNDER_TAKET = {"VV": 330.0, "KV": 450.0}    # stammarnas mitt under källarens tak, varmvattnet högre
TVARS = 40.0                                 # stammarna flyttas högst så långt ut från eller in mot väggen


@dataclass(frozen=True)
class Underfordelare:
    """En underfördelare: stammarnas början (inloppet) vid onskat längs väggens yta (normalen ut i rummet), utgångarna
    i riktning längs väggen, stammarna per media, matningens rör och dimensionerande flöde per media, rummet (montaget
    i modellen) och tappställenas ordning i dess stråk (tappställe: stråk och ben, som teknikrum.ORDNING), stråket
    langd ut från väggen."""
    id: str
    namn: str
    rum: str
    onskat: Vek                 # på väggens yta (z oviktigt)
    normal: Vek
    riktning: Vek
    typer: tuple[tuple[str, Fordelartyp], ...]
    ror: Rortyp
    flode: tuple[tuple[str, float], ...]
    ordning: tuple[tuple[str, tuple[str, int | None]], ...]
    strak_id: str
    langd: float

    @property
    def medier(self) -> tuple[str, ...]:
        return tuple(m for m, _ in self.typer)

    def _stam(self, media: str, fil: float, start: Vek) -> Vek:
        """Stammens punkt i filen fil för media (−1: inloppet, vid start längs väggen)."""
        n, r = self.normal, self.riktning
        return (start[0] + n[0] * AVSTAND[media] + r[0] * (fil + 1) * FIL,
                start[1] + n[1] * AVSTAND[media] + r[1] * (fil + 1) * FIL, KALLARTAK - UNDER_TAKET[media])

    @property
    def start(self) -> Vek:
        return _start(self)

    def inlopp(self) -> Tappstalle:
        """Inloppet som ett tappställe i huvudfördelarnas ordning: rören rakt ned ur bjälklaget till stammarnas
        början."""
        q = dict(self.flode)
        typ = Tappstalletyp(self.id, self.namn, q.get("KV", 0.0), q.get("VV", 0.0), "UF")
        return Tappstalle(self.id, typ, INLOPP, Montering(self.start, self.normal, "vagg", self.rum), self.ror,
                          anslutningar=tuple((m, self._stam(m, -1, self.start)) for m in self.medier))

    def fordelare(self, media: str, filer: tuple[int, ...]) -> Fordelare:
        """Stammen för media med utgångarna i filerna (filen 0 en fil efter inloppet)."""
        return Fordelare(f"{self.id}-{media}", dict(self.typer)[media], media, self._stam(media, 0, self.start),
                         self.riktning, filer)

    @property
    def borjan(self) -> tuple[float, float]:
        """Filen 0 vid kallvattnets stam, i plan (..strak.filer)."""
        p = self._stam("KV", 0, self.start)
        return p[0], p[1]

    def strak(self, mitt: dict[str, float]) -> dict[str, Strak]:
        """Stråket från väggen rakt ut i rummet genom filernas mitt (mitt: läget längs riktning)."""
        r, n, s = self.riktning, self.normal, self.start
        d = mitt[self.strak_id] - (s[0] * r[0] + s[1] * r[1])
        p0 = (s[0] + r[0] * d, s[1] + r[1] * d)
        return {self.strak_id: Strak(self.strak_id, (p0, (p0[0] + n[0] * self.langd, p0[1] + n[1] * self.langd)))}


@cache
def _start(u: Underfordelare) -> Vek:
    """Inloppet flyttat längs väggen (och högst TVARS från den) så att alla rör upp ur stammarna och ned till dem går
    fria från underkantsnätets järn."""
    n_filer = len(u.ordning) * len(u.medier)                   # högst: ett rör per tappställe och media
    punkter = [u._stam(m, k, u.onskat)[:2] for m in u.medier for k in range(-1, n_filer)]
    dx, dy = mellan_jarnen(punkter, KALLARTAK, Z_ROR, R_ROR, langs=(u.riktning[0], u.riktning[1]), tvars=TVARS)
    return (u.onskat[0] + dx, u.onskat[1] + dy, u.onskat[2])


_V14 = kallarvagg("V14", 8800.0, 0.0, -1)                     # under köket, inloppet i norra änden: stammarna söderut
#                                                               mot diskhons avlopp (y 8 359), fria från det
_KL1 = KL["KL1"]
_KL1_YTA = _KL1.c - _KL1.t / 2 - GIPS_T                       # KL1:s yta mot rummet öster om KL2
_KL2_YTA = KL["KL2"].c + KL["KL2"].t / 2 + GIPS_T

UNDERFORDELARE = [
    Underfordelare("UF1", "Underfördelare under köket", "Källare", _V14.punkt, _V14.normal, (0.0, -1.0, 0.0),
                   (("KV", UNDERFORDELARE_KV), ("VV", UNDERFORDELARE_VV)), ROR_I_ROR_18,
                   (("KV", 0.3), ("VV", 0.2)), (("KO-DM1", ("K", None)), ("KO-DB1", ("K", None))), "K", 2300.0),
    Underfordelare("UF2", "Underfördelare under badrummet", "Källare", (_KL2_YTA + 40.0, _KL1_YTA, 0.0),
                   (0.0, -1.0, 0.0), (1.0, 0.0, 0.0), (("KV", UNDERFORDELARE_KV),), ROR_I_ROR_18,
                   (("KV", 0.25),), (("BA-TM1", ("B", None)), ("BA-WC1", ("B", None))), "B", 1000.0),
]

# matningens rör till UF1:s varmvatten är klenare, så att varmvattnet når diskbänken inom tiden (system.VV_TID)
ROR_MATNING = {("UF1", "VV"): ROR_I_ROR_16}
