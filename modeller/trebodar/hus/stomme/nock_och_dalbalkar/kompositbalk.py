"""Nock- eller dalbalk enligt K-01: limträ GL30c 190×180 i hel längd, stålplåtar 190×10 i över- och underkant med
skruvhål enligt hålbilden och distansreglar 10 mm där plåt saknas (5 mm glipa mot plåtänden). Upplagsreglarna för
takbalkarna hör till takbalkarna (prefab).

Ovanpå balken limmas reglar som hårdboarden landar på: på nockbalkarna en regel 45 bred i mitten med överkanten
fasad efter de två takplanen (30°), på dalbalkarna en regel 45 bred längs vardera kanten med överkanten i takplanet
på den sidan. Reglarna har urtag 20 × 20 × 6 för skruvhuvudena (Ø16,5, 5 mm över plåten) där de står på dem.

Balkens mått, plåtlägen och hål läses ur K-01 (indata.toml och halbild_*.csv), så att modellen alltid följer
beräkningen. Balkens system: x längs balken från änden vid lägst y, y = 0 vid sidan mot växande x i huset (balkens
framsida i K-01), z = 0 vid underkanten.
"""
from __future__ import annotations

import csv
import tomllib
from functools import lru_cache
from pathlib import Path
from typing import Any

from modellering import Del, Form, Montage, Placering, box, lada, prisma

from trebodar import skelett as S
from trebodar.byggdelar.virke import fmt
from trebodar.material import C24, DISTANS, GL30C, S355

REGEL_B = 45.0                       # reglarna ovanpå balken
URTAG_B, URTAG_H = 20.0, 6.0         # urtagen för skruvhuvudena (fyrkantiga)

ROT = Path(__file__).resolve().parents[5]
K01 = ROT / "beräkningar" / "K-01"


@lru_cache(maxsize=1)
def indata() -> dict[str, Any]:
    return tomllib.loads((K01 / "indata.toml").read_text(encoding="utf-8"))


def halbild(k01_namn: str) -> dict[int, tuple[float, float, list[tuple[float, float, float]]]]:
    """Plåtbitar: nr -> (från, till, [(x, y_över, y_under)])."""
    fil = K01 / f"halbild_{k01_namn.lower().replace(' ', '')}.csv"
    rader = [r for r in fil.read_text(encoding="utf-8").splitlines() if not r.startswith("#")]
    bitar: dict[int, tuple[float, float, list[tuple[float, float, float]]]] = {}
    for r in csv.DictReader(rader, delimiter=";"):
        nr = int(r["bit"])
        if nr not in bitar:
            bitar[nr] = (float(r["plat_fran"]), float(r["plat_till"]), [])
        bitar[nr][2].append((float(r["x_mm"]), float(r["y_over"]), float(r["y_under"])))
    return bitar


def placering(b: S.Balklinje) -> Placering:
    """Balkens system i huset: x längs +y, y längs −x (från balkens sida vid växande x), z uppåt från underkanten."""
    return Placering(((0.0, -1.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0)), (b.x + S.BALK_B / 2, b.y0, b.uk))


def montage(kod: str) -> Montage:
    b = S.BALKAR[kod]
    IN = indata()
    g = IN["geometri"]
    B, t, h = float(g["b"]), float(g["t_pl"]), float(g["h_tra"])
    glipa = float(IN["distans"]["glipa"])
    d = float(IN["skruv"]["hal"])
    k01 = next(x for x in IN["balk"] if x["namn"] == b.k01)
    L = float(k01["total"])
    assert abs(L - (b.y1 - b.y0)) < 1e-6, f"{kod}: K-01 {L} mm, skelettet {b.y1 - b.y0} mm"
    m = Montage(kod, kod, f"{b.k01}: limträ GL30c 190×180 med stålplåtar 190×10 (K-01)")
    m.lagg(Del(f"{kod} limträ GL30c 190×180", lada(L, B, h), GL30C, dokument="K-01"), Placering.flytt(z=t),
           f"{kod}-LT")
    bitar = halbild(b.k01)
    for nr, (a, c, hal) in sorted(bitar.items()):
        for lage, z in (("U", 0.0), ("O", t + h)):
            namn = f"{kod}-{nr}-{lage}"
            form = prisma([(0, 0), (c - a, 0), (c - a, B), (0, B)], t,
                          cirkelhal=[(x - a, yu if lage == "U" else yo, d) for x, yo, yu in hal])
            m.lagg(Del(f"Plåt {namn} 190×10 L={c - a:g}", form, S355, artikel="Laserskuren plåt S355J2+N",
                       dokument="K-01"), Placering.flytt(a, 0.0, z), namn)
    # distansreglar där plåt saknas
    x, fria = 0.0, []
    for _, (a, c, _) in sorted(bitar.items()):
        if a - x > 1:
            fria.append((x, a - (glipa if a < L else 0)))
        x = c + (glipa if 0 < c < L else 0)
    if L - x > 1:
        fria.append((x, L))
    for i, (a, c) in enumerate(fria, 1):
        for lage, z in (("U", 0.0), ("O", t + h)):
            m.lagg(Del(f"Distansregel 190×10 L={c - a:g}", lada(c - a, B, t), DISTANS, dokument="K-01"),
                   Placering.flytt(a, 0.0, z), f"{kod}-D{i}-{lage}")
    skruvar = [(x, yo) for _, (_, _, hal) in bitar.items() for x, yo, _ in hal]
    huvud = float(IN["skruv"]["huvud"])
    assert huvud < URTAG_H and float(IN["skruv"]["huvud_d"]) < URTAG_B
    lagen_y = [(B / 2 - REGEL_B / 2, B / 2 + REGEL_B / 2)] if b.typ == "nock" else [(0.0, REGEL_B), (B - REGEL_B, B)]
    for i, (y0, y1) in enumerate(lagen_y, 1):
        namn = f"{kod}-NR" if b.typ == "nock" else f"{kod}-DR{i}"
        regel = _regel(b, L, y0, y1, 2 * t + h, skruvar)
        m.lagg(Del(f"{'Nockregel' if b.typ == 'nock' else 'Dalregel'} {fmt(REGEL_B)} L={fmt(L)}", regel, C24),
               Placering(), namn)
    return m


def _regel(b: S.Balklinje, L: float, y0: float, y1: float, z0: float, skruvar: list[tuple[float, float]]) -> Form:
    """Regeln ovanpå balken mellan y0 och y1 (balkens system), från plåtens överkant z0 till takplanen, med urtag
    för de skruvhuvuden den står på."""
    from trebodar.hus.fasad.fasad import tak_underkant
    ym = b.y0 + L / 2

    def z(y: float) -> float:
        """Takplanet (hårdboardens undersida) över balkens punkt y, i balkens system."""
        zt = tak_underkant(b.x + S.BALK_B / 2 - y, ym)
        assert zt is not None, (b.kod, y)
        return zt - b.uk
    ys = [y0, y1] if b.typ == "dal" else [y0, (y0 + y1) / 2, y1]
    kontur = [(y0, z0), (y1, z0)] + [(y, z(y)) for y in reversed(ys)]
    vrid = Placering(((0.0, 0.0, 1.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)), (0.0, 0.0, 0.0))   # (y, z, x) → (x, y, z)
    form: Form = prisma(kontur, L).placerad(vrid)
    r = URTAG_B / 2
    for x, ys_ in skruvar:
        if y0 - r < ys_ < y1 + r:
            form = form - box(x - r, x + r, ys_ - r, ys_ + r, z0 - 1.0, z0 + URTAG_H)
    return form
