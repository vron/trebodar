"""Genomföringar: ett verktyg (t.ex. en cylinder kring en skorsten) skär hål i alla delar det når i ett montage, i
stället för att varje skikt räknar med hålet. Verktyget anges i montagets system med sin omslutande låda."""
from __future__ import annotations

from dataclasses import replace

from modellering import IDENTITET, Form, Montage, Placering, i_foraldern, minus, omslutande

Lada = tuple[float, float, float, float, float, float]


def _overlappar(a: Lada, b: Lada) -> bool:
    return all(a[i] < b[i + 3] and b[i] < a[i + 3] for i in range(3))


def genomfor(m: Montage, verktyg: Form, lada: Lada, plac: Placering = IDENTITET) -> int:
    """Delarna i montaget (och dess undermontage) vars låda når verktygets låda får formen minus verktyget. Ger
    antalet delar som skars."""
    n = 0
    for k, i in enumerate(m.barn):
        p = plac @ i.placering
        if isinstance(i.barn, Montage):
            n += genomfor(i.barn, verktyg, lada, p)
            continue
        b = omslutande(i.barn.form)
        if b is not None and _overlappar(i_foraldern(b, p), lada):
            m.barn[k] = replace(i, barn=replace(i.barn, form=minus(i.barn.form, [verktyg.placerad(p.invers())])))
            n += 1
    return n


def genomfor_alla(m: Montage, verktyg: list[tuple[Form, Lada]], plac: Placering = IDENTITET) -> int:
    """Som genomfor, med många verktyg (form, låda): varje del skärs en gång med de verktyg som når den. Ger antalet
    delar som skars."""
    n = 0
    for k, i in enumerate(m.barn):
        p = plac @ i.placering
        if isinstance(i.barn, Montage):
            n += genomfor_alla(i.barn, verktyg, p)
            continue
        b = omslutande(i.barn.form)
        if b is None:
            continue
        lb = i_foraldern(b, p)
        nar = [v.placerad(p.invers()) for v, lada in verktyg if _overlappar(lb, lada)]
        if nar:
            m.barn[k] = replace(i, barn=replace(i.barn, form=minus(i.barn.form, nar)))
            n += 1
    return n
