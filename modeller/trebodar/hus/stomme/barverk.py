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
from trebodar.byggdelar import polygon as P
from trebodar.hus.fonster_och_dorrar.oppningar import OPPNINGAR
from trebodar.hus.invandigt import vaggar, vagginsida
from trebodar.hus.stomme import forankring
from trebodar.hus.stomme.prefab.takbalkar.takbalkar import FALT
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
    """Takfallen: kroppen, riktningen, takbalkarnas överkant z(x) = z_ref + riktning · tan · (x − x_ref),
    regionerna (y0, y1, nedre kant x, nock x) i plan och takfönstrens öppningar (y0, y1, nedre x, övre x)."""
    ut = []
    for kod, regioner in REGIONER.items():
        t = S.TAKFALL[kod]
        ut.append({"kod": kod, "kropp": t.kropp, "riktning": t.riktning, "lutning": S.TAKVINKEL,
                   "x_insida": t.x_insida, "x_utsida": t.x_utsida, "x_takfot": t.x_takfot,
                   "x_ref": t.x_insida, "z_ref": t.z_overkant(t.x_insida),
                   "regioner": [[r.y0, r.y1, r.nedre.x, r.nock.x] for r in regioner],
                   "fonster": [[fo.y0, fo.y1, fo.x_ned, fo.x_upp] for fo in FALT[kod].fonster]})
    return ut


def _polygoner(yta: Any) -> list[dict[str, Any]]:
    """Ytan som polygoner: ytterkonturen och hålen, (u, z) i mm."""
    def ring(r: Any) -> list[list[float]]:
        return [[round(x, 1), round(y, 1)] for x, y in list(r.coords)[:-1]]
    return [{"kontur": ring(g.exterior), "hal": [ring(h) for h in g.interiors]} for g in P.polygoner(yta, 1000.0)]


def _vaggar() -> list[dict[str, Any]]:
    """Väggarna: läge, längd, tjocklek, om väggen är en yttervägg, öppningarna (u0, u1, z0, z1) och, för de bärande
    innerväggarna, skivorna direkt på reglarna per sida (OSB, mot badrummet plywood), och för ytterväggarna utan
    installationsskikt (1SV) OSB:n på insidan (sida +1); de andra ytterväggarnas invändiga skivor sitter på
    installationsskiktet och ingår inte: {sida: polygoner i (u, z)}."""
    skivor = dict(vaggar.barande_skivor())
    for kod in S.YTTERVAGGAR:
        yta = vagginsida.barande_skivor(kod)
        if not yta.is_empty:
            skivor[(kod, 1)] = yta
    return [{"kod": kod, "origo": list(v.origo), "u": list(v.u), "w": list(v.w), "langd": v.langd,
             "tjocklek": v.tjocklek, "yttervagg": kod in S.YTTERVAGGAR,
             "oppningar": [[o.u0, o.u1, max(o.z0, 0.0), o.z1] for o in OPPNINGAR.get(kod, []) if o.z1 > 0.0],
             "skivor": {str(sida): _polygoner(skivor[(kod, sida)]) for sida in (-1, 1) if (kod, sida) in skivor}}
            for kod, v in S.VAGGAR.items()]


def _latta_reglar(rot: Montage) -> list[dict[str, Any]]:
    """De lätta väggarnas reglar (inte i K-04:s balkmodell): väggen och den omslutande lådan (x0, y0, z0, x1, y1, z1)
    i huset. En lätt vägg som möter en bärande vägg stagar den ut ur dess plan, där deras reglar ligger an mot
    varandra (hörnstolparna i 1B:s ändar)."""
    ut = []
    for vag, m, p in rot.montage():
        if vag.endswith("/Lätta väggar"):
            for dv, d, q in m.platta(p):
                namn = dv.rsplit("/", 1)[-1]
                k = re.fullmatch(r"(L\d+)-R\d+", namn)
                bb = omslutande(d.form)
                if k and bb is not None:
                    hornen = np.array([q.punkt((x, y, z)) for x in bb[0::3] for y in bb[1::3] for z in bb[2::3]])
                    ut.append({"vagg": k.group(1), "namn": namn,
                               "lada": [round(float(v), 4) for v in (*hornen.min(axis=0), *hornen.max(axis=0))]})
    return ut


def utdrag(rot: Montage) -> dict[str, Any]:
    stomme, p = rot.hitta("Hus/Stomme")
    assert isinstance(stomme, Montage)
    return {"version": VERSION, "z_bjalklag": 0.0, "h_vagg": S.H_VAGG,
            "huskroppar": [{"nr": k.nr, "x0": k.x0, "x1": k.x1, "y0": k.y0, "y1": k.y1, "nock": k.nock}
                           for k in S.HUSKROPPAR.values()],
            "delar": _delar(stomme, p), "takytor": _takytor(), "vaggar": _vaggar(), "latta_reglar": _latta_reglar(rot),
            # förankringen (inte i K-04:s balkmodell; K-04 prövar den och R-02 visar den): betongbultarna genom
            # syllarna (där de går genom syllen, med lutningen från lodlinjen) och beslagen med sina bultar
            "bultar": {"d": forankring.D, "djup": forankring.DJUP, "over": forankring.OVER,
                       "lagen": [_bult(k, b) for k, b in forankring.syllbultar()]},
            "beslag": [{"nyckel": b.nyckel, "del": b.del_, "element": b.element, "slag": b.slag,
                        "x": round(float(b.plac.t[0]), 1), "y": round(float(b.plac.t[1]), 1),
                        "z": round(float(b.plac.t[2]), 1),
                        "normal": [round(float(v), 4) for v in b.plac.riktning((1.0, 0.0, 0.0))[:2]],
                        "bultar": [_bult(b.element, bu) for bu in b.bultar]}
                       for b in forankring.beslag() + forankring.huvudstolpens_beslag()]}


def _bult(kod: str, b: Any) -> dict[str, Any]:
    """Bulten där den går genom ytan som brickan ligger på, och dess lutning från lodlinjen [°]."""
    return {"vagg": kod, "x": round(b.genom[0], 1), "y": round(b.genom[1], 1), "lutning": round(b.lutning, 1)}
