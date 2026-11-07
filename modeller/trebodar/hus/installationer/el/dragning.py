"""Rörens vägar mellan punkterna (ärendena #50 och #51): genom innertaket (från en väggdosa upp i väggen och i
innertakets installationsskikt till nästa väggdosa), längs en vägg (i regelfacket eller i ytterväggens
installationsskikt) och upp ur mellanbjälklaget in i en vägg eller i inredningen, mellan överkantsnätets järn.
Brytpunkterna i husets koordinater (installationernas gemensamma montering.py).
"""
from __future__ import annotations

from trebodar import skelett as S
from trebodar.hus.invandigt.skikt import LAKT
from trebodar.hus.invandigt.vaggar import vaggdef

from ..montering import BJALKLAG, PLAN, Montering, Vek, i_vagg, langs_vaggen, vid_tak
from ..strak import mellan_jarnen
from .punkter import Punkt, anslutning
from .rum.kok import X_ON_ROR

D_ROR = 16.0                   # de klena rörens diameter (Ø16), för läget mellan järnen
GIPS = 12.5                    # innerväggarnas gips på var sida (regelfacket emellan)


def _ar_vagg(kod: str) -> bool:
    try:
        return kod in S.YTTERVAGGAR or vaggdef(kod) is not None
    except (KeyError, ValueError):
        return False


class _Vaggar:
    def __contains__(self, kod: object) -> bool:
        return isinstance(kod, str) and _ar_vagg(kod)


_VAGGAR = _Vaggar()


def _tvars(kod: str, d: float) -> float:
    """Så långt kan röret flyttas tvärs väggen inom regelfacket (innerväggar) eller installationsskiktet."""
    facket = LAKT if kod in S.YTTERVAGGAR else vaggdef(kod).tjocklek - 2 * GIPS
    return max(0.0, facket / 2 - d / 2 - 1.0)


def _vaggen(m: Montering) -> tuple[str, float, int]:
    """Väggen, läget u längs den och sidan för en montering på en väggs yta."""
    v = S.YTTERVAGGAR[m.ref] if m.ref in S.YTTERVAGGAR else vaggdef(m.ref)
    sida = 1 if m.normal[0] * v.w[0] + m.normal[1] * v.w[1] > 0 else -1
    return m.ref, langs_vaggen(m.ref, m.punkt), sida


def _langs(m: Montering) -> tuple[float, float]:
    """Väggens riktning (u) i plan."""
    v = S.YTTERVAGGAR[m.ref] if m.ref in S.YTTERVAGGAR else vaggdef(m.ref)
    return v.u[0], v.u[1]


def via_taket(a: Montering, b: Montering) -> tuple[Vek, ...]:
    """Från väggdosan a upp i väggen till innertaket, i installationsskiktet till väggen vid b och ned i den."""
    ta, tb = vid_tak(*_vaggen(a)), vid_tak(*_vaggen(b))
    return ta[0], ta[1], tb[1], tb[0]


def i_vaggen_vid(m: Montering, z: float) -> Vek:
    """I väggen bakom monteringen m, z över plan 1:s golv (regelfacket eller installationsskiktet)."""
    kod, u, _ = _vaggen(m)
    return i_vagg(kod, u, z)


def upp_i_vaggen(kod: str, u: float, z: float, niva: str = "MB", d: float = D_ROR) -> tuple[Vek, Vek]:
    """Från elrörens nivå i mellanbjälklaget upp i väggen kod vid u (flyttat längs väggen mellan överkantsnätets järn)
    till z över golvet."""
    v = S.YTTERVAGGAR[kod] if kod in S.YTTERVAGGAR else vaggdef(kod)
    i = i_vagg(kod, u, 0.0)
    dx, dy = mellan_jarnen([i[:2]], BJALKLAG[niva], PLAN[1], d / 2, langs=(v.u[0], v.u[1]), tvars=_tvars(kod, d))
    return (i[0] + dx, i[1] + dy, BJALKLAG[niva]), (i[0] + dx, i[1] + dy, PLAN[1] + z)


def upp_ur_bjalklaget(p: Punkt, niva: str = "MB", d: float = D_ROR) -> tuple[Vek, ...]:
    """Från elrörens nivå i mellanbjälklaget rakt upp till punktens dosa: i väggens regelfack eller ytterväggens
    installationsskikt under dosan, flyttat längs väggen (högst TVARS tvärs den) så lite som behövs för att gå fri
    mellan överkantsnätets järn, och upp till dosans höjd (därifrån in i dosan)."""
    a = anslutning(p)
    vagg = p.lage.yta == "vagg" and p.lage.ref in _VAGGAR
    i = i_vaggen_vid(p.lage, 0.0) if vagg else (X_ON_ROR, a[1], a[2]) if p.lage.ref == "Ön" else a
    langs = _langs(p.lage) if vagg else None
    dx, dy = mellan_jarnen([i[:2]], BJALKLAG[niva], PLAN[1], d / 2, langs=langs,
                           tvars=_tvars(p.lage.ref, d) if vagg else 0.0)
    x, y = i[0] + dx, i[1] + dy
    return (x, y, BJALKLAG[niva]), (x, y, a[2])
