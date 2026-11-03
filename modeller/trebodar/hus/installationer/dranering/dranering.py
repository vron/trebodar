"""Dräneringen och dagvattnet i modellen (Hus/Installationer/Dränering): ledningarna som rör Ø110 längs vattengången
(ledningar.py), brunnen och spolbrunnarna. Ledningarna går i marken och ingår inte i modellens krockkontroll; deras
egen kontroll (./mod dranering kontroll) prövar dem mot husets delar."""
from __future__ import annotations

from modellering import Del, Form, Montage, Placering, cylinder

from trebodar.byggdelar.ror import ror
from trebodar.byggdelar.virke import fmt
from trebodar.material import DAGVATTENROR, DRANROR, DRANBRUNN

from .ledningar import D, GODS, brunnar, ledningar

BRUNN_GODS = 10.0
NAMN = {"dränering": "Dränrör", "dagvatten": "Dagvattenrör", "anslutning": "Dagvattenrör, stuprörsanslutning",
        "spolrör": "Spolrör", "utlopp": "Utgående rör (befintligt)"}


def montage() -> Montage:
    m = Montage("Dränering", beskrivning="Dränering runt grunden och dagvatten från stuprören till brunnen B1")
    for led in ledningar().values():
        mat = DRANROR if led.typ == "dränering" or (led.typ == "spolrör" and led.id.startswith("D")) else DAGVATTENROR
        for i, (a, b) in enumerate(zip(led.vag, led.vag[1:]), 1):
            if sum((p - q) ** 2 for p, q in zip(a, b)) < 1.0:
                continue
            pa, pb = (a[0], a[1], a[2] + D / 2), (b[0], b[1], b[2] + D / 2)
            m.lagg(Del(f"{NAMN[led.typ]} Ø{fmt(D)}", ror(pa, pb, D, GODS), mat), Placering(), f"{led.id}-{i:02d}")
    for br in brunnar().values():
        h = br.z_lock - br.z_botten
        f: Form = cylinder(br.d / 2, h, (br.x, br.y, br.z_botten)) - cylinder(br.d / 2 - BRUNN_GODS, h,
                                                                                (br.x, br.y, br.z_botten + BRUNN_GODS))
        m.lagg(Del(f"{'Brunn' if br.id == 'B1' else 'Spolbrunn'} Ø{fmt(br.d)}", f, DRANBRUNN), Placering(), br.id)
    return m
