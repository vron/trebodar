"""Bärverket ur modellen för K-04 (`./mod barverk`): stommens delar med läge och tvärsnitt, och ytorna som lasterna
verkar på (takfallen och väggarna). K-04 bygger sin balkmodell (FEM) ur utdraget, så att beräkningen följer modellen;
utdraget är gränssnittet mellan modellen och beräkningen och tolkar inte mer än delarnas namn och grupper.

Varje del (allt under Hus/Stomme: virke, limträ, stålplåtar, spikplåtar och stålband) med sin grupp (ytterväggar,
innerväggar, takstolar, stolpar, takbalkar, nock- och dalbalkar, stålband i väggar och i takfall), sitt element
(väggens, takstolens, stolpens, takfallets eller balkens kod), sin typ (bokstäverna i namnet <element>-<typ><nr>),
stolpen den hör till (namnet <stolpe>-<nr>, som LA1-1 eller LN5_1-2), materialet och formen: delens system i huset
(R: lokala axlar som kolumner, t: origo), den omslutande lådan i delens system och, för prismor, konturen. Virkets
lokala x går längs fibrerna (byggdelar/virke.py).
"""
from __future__ import annotations

import re
from typing import Any

import numpy as np

from modellering import Lada, Montage, Prisma, omslutande
from modellering.form import Diff, Form, Transf
from modellering.placering import Placering

from trebodar import skelett as S
from trebodar.hus.fonster_och_dorrar.oppningar import OPPNINGAR
from trebodar.hus.tak.takytor import REGIONER

VERSION = 1
GRUPPER = {"Ytterväggar": "yttervagg", "Innerväggar": "innervagg", "Takstolar": "takstol", "Stolpar": "stolpe",
           "Takbalkar": "takbalk", "Nock- och dalbalkar": "balk", "Väggar": "band_vagg", "Takfall": "band_tak"}
STOLPE = re.compile(r"^(L[A-Z]\d+(?:_\d+)?)-")


def _form(f: Form, p: Placering) -> tuple[Form, Placering]:
    """Formen som bestämmer delens läge (den första i en differens) och dess placering."""
    while isinstance(f, (Transf, Diff)):
        if isinstance(f, Transf):
            p, f = p @ f.placering, f.form
        else:
            f = f.bas
    return f, p


def _delar(stomme: Montage, plac: Placering) -> list[dict[str, Any]]:
    ut: list[dict[str, Any]] = []

    def ga(m: Montage, p: Placering, grupp: str, element: str | None) -> None:
        for i in m:
            q = p @ i.placering
            if isinstance(i.barn, Montage):
                if i.barn.namn != "Förankring":          # bultarna genom syllarna ingår inte i K-04:s balkmodell
                    ga(i.barn, q, GRUPPER.get(i.barn.namn, grupp), i.barn.kod or element)
                continue
            d = i.barn
            f, q = _form(d.form, q)
            bb = omslutande(f)
            if bb is None:
                continue
            el = element or ""
            typ = re.fullmatch(rf"{re.escape(el)}-([A-Za-z]+)\d*(?:-.*)?", i.namn)
            st = STOLPE.match(i.namn)
            del_: dict[str, Any] = {
                "namn": i.namn, "grupp": grupp, "element": el, "typ": typ.group(1) if typ else "",
                "stolpe": st.group(1) if st else None, "material": d.material.namn, "densitet": d.material.densitet,
                "R": np.round(np.array(q.R), 9).tolist(), "t": np.round(np.array(q.t), 4).tolist(),
                "bb": [round(v, 4) for v in bb]}
            if isinstance(f, Prisma) and not isinstance(f, Lada):
                del_["kontur"] = [[round(x, 4), round(y, 4)] for x, y in f.kontur]
            ut.append(del_)

    ga(stomme, plac, "", None)
    return ut


def _takytor() -> list[dict[str, Any]]:
    """Takfallen: kroppen, riktningen, takbalkarnas överkant z(x) = z_ref + riktning · tan · (x − x_ref) och
    regionerna (y0, y1, nedre kant x, nock x) i plan."""
    ut = []
    for kod, regioner in REGIONER.items():
        t = S.TAKFALL[kod]
        ut.append({"kod": kod, "kropp": t.kropp, "riktning": t.riktning, "lutning": S.TAKVINKEL,
                   "x_insida": t.x_insida, "x_utsida": t.x_utsida, "x_takfot": t.x_takfot,
                   "x_ref": t.x_insida, "z_ref": t.z_overkant(t.x_insida),
                   "regioner": [[r.y0, r.y1, r.nedre.x, r.nock.x] for r in regioner]})
    return ut


def _vaggar() -> list[dict[str, Any]]:
    """Väggarna: läge, längd, tjocklek, om väggen är en yttervägg och öppningarna (u0, u1, z0, z1)."""
    return [{"kod": kod, "origo": list(v.origo), "u": list(v.u), "w": list(v.w), "langd": v.langd,
             "tjocklek": v.tjocklek, "yttervagg": kod in S.YTTERVAGGAR,
             "oppningar": [[o.u0, o.u1, max(o.z0, 0.0), o.z1] for o in OPPNINGAR.get(kod, []) if o.z1 > 0.0]}
            for kod, v in S.VAGGAR.items()]


def utdrag(rot: Montage) -> dict[str, Any]:
    stomme, p = rot.hitta("Hus/Stomme")
    assert isinstance(stomme, Montage)
    return {"version": VERSION, "z_bjalklag": 0.0, "h_vagg": S.H_VAGG,
            "huskroppar": [{"nr": k.nr, "x0": k.x0, "x1": k.x1, "y0": k.y0, "y1": k.y1, "nock": k.nock}
                           for k in S.HUSKROPPAR.values()],
            "delar": _delar(stomme, p), "takytor": _takytor(), "vaggar": _vaggar()}
