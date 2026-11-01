"""Modellträdet: material, delar (en form i eget koordinatsystem) och montage (placerade instanser av delar och
andra montage). Samma del eller montage kan placeras flera gånger."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator

from .form import Form
from .placering import IDENTITET, Placering


Parameter = float | str


@dataclass(frozen=True)
class Material:
    """Ett material med två utseenden: CAD-färgen (STEP, Onshape, webbvisaren), vald så att olika slags delar skiljer
    sig åt, och det verkliga utseendet för renderingen (farg, grovhet, metall och det procedurella materialet)."""
    namn: str                        # kort namn, t.ex. "C24", "GL30c", "S355", "Gips"
    beskrivning: str                 # för materiallistan, t.ex. "Konstruktionsvirke C24"
    densitet: float                  # kg/m³
    farg: str                        # "#rrggbb", sRGB: verklig färg (rendering)
    grovhet: float = 0.8             # PBR roughness
    metall: float = 0.0              # PBR metallic
    textur: str | None = None        # procedurellt material vid rendering (Blender), t.ex. "tra", "bradpanel"
    enhet: str = "st"                # materiallistans enhet: "st" (styck med kapmått), "m2", "m3", "kg"
    opacitet: float = 1.0            # < 1 för glas o.d.
    rendering: tuple[tuple[str, Parameter], ...] = ()   # parametrar till det procedurella materialet
    cad: str = ""                    # "#rrggbb", CAD-färgen; tom: den verkliga färgen

    @property
    def cad_farg(self) -> str:
        return self.cad or self.farg

    def renderdata(self) -> dict[str, Parameter]:
        """Allt som renderingen behöver om materialet: typ, färg och parametrar."""
        return {"typ": self.textur or "farg", "farg": self.farg, "grovhet": self.grovhet, "metall": self.metall,
                "opacitet": self.opacitet, **dict(self.rendering)}


def rendering(**p: Parameter) -> tuple[tuple[str, Parameter], ...]:
    """Parametrar till ett procedurellt material, t.ex. rendering(riktning="y", bredd=145)."""
    return tuple(sorted(p.items()))


@dataclass(frozen=True)
class Del:
    """En unik del: form i eget koordinatsystem + material. Namnet beskriver delen (som produkt i STEP)."""
    namn: str                        # t.ex. "Regel 45×95 L=2404"
    form: Form
    material: Material
    beskrivning: str = ""
    artikel: str | None = None       # beställningsbar produkt, t.ex. "Rothoblaas HBS PLATE EVO 10×80"
    dokument: str | None = None      # handling som bestämmer delen, t.ex. "K-01"


@dataclass(frozen=True)
class Instans:
    barn: Del | Montage
    placering: Placering
    namn: str                        # instansens kanoniska namn (unikt i montaget), t.ex. "1NO-R03"


@dataclass(eq=False)
class Montage:
    """Ett montage med eget koordinatsystem. `namn` visas i trädet, `kod` är beteckningen i handlingarna."""
    namn: str
    kod: str | None = None
    beskrivning: str = ""
    barn: list[Instans] = field(default_factory=list)

    def lagg(self, barn: Del | Montage, placering: Placering = IDENTITET, namn: str | None = None) -> Instans:
        """Placera en del eller ett montage i montaget. Namnet blir instansens (standard: barnets namn)."""
        n = namn or barn.namn
        if any(i.namn == n for i in self.barn):
            raise ValueError(f"{self.namn}: namnet {n!r} finns redan")
        i = Instans(barn, placering, n)
        self.barn.append(i)
        return i

    def __iter__(self) -> Iterator[Instans]:
        return iter(self.barn)

    def platta(self, plac: Placering = IDENTITET, vag: str = "") -> Iterator[tuple[str, Del, Placering]]:
        """Alla delar: (sökväg, del, placering i det här montagets system). Sökvägen börjar med montagets namn."""
        bas = vag or self.namn
        for i in self.barn:
            p = plac @ i.placering
            v = f"{bas}/{i.namn}"
            if isinstance(i.barn, Montage):
                yield from i.barn.platta(p, v)
            else:
                yield v, i.barn, p

    def montage(self) -> Iterator[tuple[str, Montage, Placering]]:
        """Alla montage i trädet (även detta), med sökväg och placering."""
        def ga(m: Montage, vag: str, p: Placering) -> Iterator[tuple[str, Montage, Placering]]:
            yield vag, m, p
            for i in m.barn:
                if isinstance(i.barn, Montage):
                    yield from ga(i.barn, f"{vag}/{i.namn}", p @ i.placering)
        return ga(self, self.namn, IDENTITET)

    def hitta(self, vag: str) -> tuple[Montage | Del, Placering]:
        """Barn på sökvägen "A/B/C" under detta montage (utan detta montages namn), med placering."""
        x: Montage | Del = self
        p = IDENTITET
        for n in [d for d in vag.split("/") if d]:
            if not isinstance(x, Montage):
                raise KeyError(vag)
            for i in x.barn:
                if i.namn == n:
                    x, p = i.barn, p @ i.placering
                    break
            else:
                raise KeyError(f"{vag}: {n!r} saknas i {x.namn}")
        return x, p

    def antal_delar(self) -> int:
        return sum(1 for _ in self.platta())
