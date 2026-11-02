"""Invändiga skikt (F-01): ångbroms (Intello Plus, åldringsbeständig plastfolie), installationsskikt och skivor.

Skiktens uppbyggnad och innertakets ytor står i skikt.py, innertaket i innertak.py, ytterväggarnas insida i
vagginsida.py, innerväggarna (de lätta väggarna och skikten på alla innerväggar) i vaggar.py och källarväggarnas gips
i kallare.py.
"""
from __future__ import annotations

from modellering import Montage

from . import innertak, kallare, vagginsida, vaggar


def montage() -> Montage:
    m = Montage("Invändigt", beskrivning="Ångbroms, installationsskikt och gips (F-01)")
    m.lagg(innertak.montage())
    m.lagg(vagginsida.montage())
    m.lagg(vaggar.montage())
    m.lagg(kallare.montage())
    return m
