"""Ytterväggarnas breda syllar (#120): syllen 45 × SYLL_B ligger under reglarna 45 × 95 och sticker 25 mm in under
installationsskiktet, så att betongbulten kommer längre från plattans kant (forankring.py).

Den inre remsan finns bara på de fria sträckorna: den tas bort HORN från väggens ändar, där en annan yttervägg och
dess skikt står i hörnet, och där en annan del i stommen står mot väggens insida (de bärande innerväggarnas och
stolparnas syllar och reglar). Syllen kapas alltså med ett urtag där, i samma virke.
"""
from __future__ import annotations

import re
from dataclasses import replace

from modellering import Del, Form, Montage, Placering, box
from modellering.form import i_foraldern, minus, omslutande

from trebodar import skelett as S

HORN = 200.0                 # den inre remsan slutar så långt från väggens ändar (hörnens skikt, också badrummets)
_SYLL = re.compile(r"^(\d[A-Z]{2})-S\d+$")
Lada6 = tuple[float, float, float, float, float, float]


def breda() -> frozenset[str]:
    """Ytterväggarna med bred syll: de med reglar 45 × 95 (gavlarna med reglar 45 × 145 har syllen 45 × 145)."""
    return frozenset(k for k, v in S.YTTERVAGGAR.items() if abs(v.tjocklek - S.T_STOMME) < 0.5)


def _delar(m: Montage, p: Placering) -> list[tuple[Montage, int, Placering, Lada6]]:
    ut = []
    for k, i in enumerate(m.barn):
        q = p @ i.placering
        if isinstance(i.barn, Montage):
            ut += _delar(i.barn, q)
        elif isinstance(i.barn, Del):
            b = omslutande(i.barn.form)
            if b is not None:
                ut.append((m, k, q, i_foraldern(b, q)))
    return ut


def _varlden(kod: str, u0: float, u1: float, w0: float, w1: float) -> Lada6:
    """Lådan u0–u1, w0–w1 i väggens system, över syllens höjd, i världen."""
    pl = S.YTTERVAGGAR[kod].placering()
    a, b = pl.punkt((u0, w0, 0.0)), pl.punkt((u1, w1, S.SYLL_H))
    return (min(a[0], b[0]), min(a[1], b[1]), 0.0, max(a[0], b[0]), max(a[1], b[1]), S.SYLL_H)


def _snitt(a: Lada6, b: Lada6) -> Lada6 | None:
    c = (max(a[0], b[0]), max(a[1], b[1]), max(a[2], b[2]), min(a[3], b[3]), min(a[4], b[4]), min(a[5], b[5]))
    return c if c[3] - c[0] > 0.5 and c[4] - c[1] > 0.5 and c[5] - c[2] > 0.5 else None


def anpassa(m: Montage) -> None:
    """Kapar den inre remsan av ytterväggarnas breda syllar i hörnen och mot stommens andra delar."""
    alla = _delar(m, Placering())
    bred = breda()
    for mont, k, p, lada in alla:
        i = mont.barn[k]
        syll = i.barn
        traff = _SYLL.match(i.namn or "")
        if traff is None or traff.group(1) not in bred or not isinstance(syll, Del):
            continue
        kod = traff.group(1)
        v = S.YTTERVAGGAR[kod]
        remsa = _snitt(lada, _varlden(kod, -1e5, 1e5, v.tjocklek, S.SYLL_B + 1.0))
        if remsa is None:
            continue
        urtag: list[Lada6] = []
        for u0, u1 in ((-1e5, HORN), (v.langd - HORN, 1e5)):
            s = _snitt(remsa, _varlden(kod, u0, u1, v.tjocklek, S.SYLL_B + 1.0))
            if s:
                urtag.append(s)
        for mont2, k2, _, lada2 in alla:
            namn2 = mont2.barn[k2].namn or ""
            if namn2.startswith(kod + "-"):
                continue
            s = _snitt(remsa, lada2)
            if s:
                urtag.append(s)
        if urtag:
            verktyg: list[Form] = [box(a[0] - 0.5, a[3] + 0.5, a[1] - 0.5, a[4] + 0.5, -1.0, S.SYLL_H + 1.0)
                                   .placerad(p.invers()) for a in urtag]
            mont.barn[k] = replace(i, barn=replace(syll, form=minus(syll.form, verktyg)))
