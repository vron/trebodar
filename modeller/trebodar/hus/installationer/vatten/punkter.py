"""Tappvattnets beståndsdelar och hur rören dras.

- Tappställen (Tappstalle): det som förbrukar vatten, med typ (normflöden), anslutning (dosa), montering på en yta
  (montering.py: vagg, golv, kallarvagg) och rörtyp. Kallvattnet ansluter till höger och varmvattnet till vänster sett
  mot dosan.
- Fördelare (Fordelare): kallvattnets och varmvattnets stammar i fördelarskåpet, med utgångar uppåt i rörens filer;
  utgång 0 och utgången efter den sista är stammens ändar (inlopp och genomgång).
- Rör (Ror): från en fördelares utgång ("FD-KV:3"), en utrustning i teknikrummet ("TK-VP:VV-ut") eller ett tappställe
  till ett annat, med media (KV, VV) och brytpunkter. Rör-i-rör från fördelaren till varje tappställe (stjärnsystem:
  läckor syns i fördelarskåpet).
- Stråk (..strak.Strak): gemensamma vägar ingjutna i mellanbjälklaget, alla rör i en nivå närmast underkantsnätet
  (golvvärmen går ovanför), en fil per rör: kallt och varmt bredvid varandra. Röret följer filen till punkten närmast
  tappstället (på stråkets ben `ben`, om det anges) och går därifrån dit (..strak.vag): upp ur bjälklaget i väggens
  regelfack eller golvdosan på plan 1, eller ned ur bjälklaget i källarväggens cellplast bakom gipsen till väggdosan i
  källaren.

Koordinater i mm (K-05), z från plan 1:s golv.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..montering import I_BETONGEN, Montering, Vek, flytt, i_vaggen
from ..strak import Strak, vag
from .typer import Dosatyp, Fordelartyp, Rortyp, Tappstalletyp

R_ROR = 14.0                            # största skyddsrörets radie (rör-i-rör 18/28)
FIL = 40.0                              # rörens avstånd i stråken (c/c)
Z_ROR = I_BETONGEN["vatten"]            # i mellanbjälklaget, närmast underkantsnätet

Via = tuple[float | None, float | None]


@dataclass(frozen=True)
class Rum:
    kod: str                    # två bokstäver, början på tappställenas id (t.ex. "BA")
    namn: str
    plan: int                   # 1 (plan 1) eller 0 (källaren)


@dataclass(frozen=True)
class Tappstalle:
    """Ett tappställe: dosans mitt på ytan (normalen ut i rummet), rörtypen från fördelarna, för golvdosor riktningen
    från varmvattnet till kallvattnet (standard x) och punkter i plan som rören går förbi efter stråket (via, per
    media eller för båda; None i en koordinat: anslutningens)."""
    id: str
    typ: Tappstalletyp
    dosa: Dosatyp
    lage: Montering
    ror: Rortyp
    kallt: Vek | None = None
    via: Via | dict[str, Via] | None = None


@dataclass(frozen=True)
class Fordelare:
    """Kallvattnets eller varmvattnets fördelare längs riktning: utgångarna i filerna `filer` (filen 0 i lage, c/c
    FIL), utgång n i filen filer[n − 1]; ändarna en fil före den första och efter den sista."""
    id: str
    typ: Fordelartyp
    media: str                  # "KV" eller "VV"
    lage: Vek
    riktning: Vek
    filer: tuple[int, ...]

    @property
    def utgangar(self) -> int:
        return len(self.filer)

    def utgang(self, n: int) -> Vek:
        """Utgång n (0 och utgangar + 1: stammens ändar)."""
        fil = -1 if n == 0 else max(self.filer) + 1 if n == self.utgangar + 1 else self.filer[n - 1]
        return flytt(self.lage, self.riktning, fil * FIL)


@dataclass(frozen=True)
class Ror:
    """Rör från fran till till genom brytpunkterna via: fördelarens utgång ("FD-KV:3"), utrustning
    ("TK-VP:KV-in") eller tappställe ("BA-DU1")."""
    id: str
    typ: Rortyp
    media: str                  # "KV" eller "VV"
    fran: str
    till: str
    via: tuple[Vek, ...] = ()


def anslutning(t: Tappstalle, media: str) -> Vek:
    """Rörets ände vid tappstället: dosans mitt bakom ytan (väggdosa) eller på ytan; kallvattnet till höger och
    varmvattnet till vänster sett mot dosan, cc isär."""
    m, d = t.lage, t.dosa
    n = m.normal
    hoger = (-n[1], n[0], 0.0) if d.slag != "golv" else (t.kallt or (1.0, 0.0, 0.0))
    p = flytt(m.punkt, n, -d.djup / 2 if d.slag == "vägg" else d.djup / 2)
    return flytt(p, hoger, (d.cc / 2) * (1 if media == "KV" else -1)) if d.cc else p


def till_tappstallet(t: Tappstalle, media: str) -> tuple[tuple[tuple[float, float], ...], tuple[Vek, ...]]:
    """Rörets väg från stråket till tappstället: punkterna i plan (via och punkten lodrätt under eller över
    anslutningen, för väggdosor inne i väggen) och därifrån upp eller ned i väggen till dosans höjd."""
    a = anslutning(t, media)
    slut: tuple[Vek, ...] = ()
    if t.dosa.slag == "vägg":
        i = i_vaggen(t.lage, a)
        a, slut = i, (i,)
    genom: tuple[tuple[float, float], ...] = ((a[0], a[1]),)
    via = t.via.get(media) if isinstance(t.via, dict) else t.via
    if via:
        genom = ((a[0] if via[0] is None else via[0], a[1] if via[1] is None else via[1]), *genom)
    return genom, slut


def ror(t: Tappstalle, utgang: dict[str, int], strak: Strak, fordelare: dict[str, Fordelare],
        ben: int | None = None) -> list[Ror]:
    """Rören till tappstället från fördelarnas utgångar (per media), längs filerna i stråket: varmt och kallt, det
    som tappstället har."""
    ut = []
    for media in ("VV", "KV"):
        if media in utgang:
            fd = fordelare[media]
            genom, slut = till_tappstallet(t, media)
            ut.append(Ror(f"{t.id}-{media}", t.ror, media, f"{fd.id}:{utgang[media]}", t.id,
                          vag(fd.utgang(utgang[media]), Z_ROR, strak, genom, slut, ben)))
    return ut
