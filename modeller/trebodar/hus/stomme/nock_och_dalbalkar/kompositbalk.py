"""Nock- eller dalbalk enligt K-01: limträ GL30c 190×180 i hel längd, stålplåtar 190×10 i över- och underkant med
skruvhål enligt hålbilden och distansreglar 10 mm där plåt saknas (5 mm glipa mot plåtänden). Upplagsreglarna för
takbalkarna hör till takbalkarna (prefab).

Balkens mått, plåtlägen och hål läses ur K-01 (indata.toml och halbild_*.csv), så att modellen alltid följer
beräkningen. Balkens system: x längs balken från änden vid lägst y, y = 0 vid sidan mot växande x i huset (balkens
framsida i K-01), z = 0 vid underkanten.
"""
from __future__ import annotations

import csv
import tomllib
from functools import lru_cache
from pathlib import Path

from modellering import Del, Montage, Placering, lada, prisma

from trebodar import skelett as S
from trebodar.material import DISTANS, GL30C, S355

ROT = Path(__file__).resolve().parents[5]
K01 = ROT / "beräkningar" / "K-01"


@lru_cache(maxsize=1)
def indata() -> dict:  # type: ignore[type-arg]
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
    return m
