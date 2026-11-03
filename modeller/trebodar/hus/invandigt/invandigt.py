"""Invändiga skikt (F-01): ångbroms (Intello Plus, åldringsbeständig plastfolie), installationsskikt och skivor.

Skiktens uppbyggnad och innertakets ytor står i skikt.py, innertaket i innertak.py, ytterväggarnas insida i
vagginsida.py, innerväggarna (de lätta väggarna och skikten på alla innerväggar) i vaggar.py, kökets inbyggnad (kyl,
frys och skafferi bakom en vägg till innertaket, förrådet ovanför) i kokets_inbyggnad.py, ändbrädorna där väggarna
slutar fritt i andbrador.py, källarväggarnas gips i kallare.py och källarens lätta innerväggar i
kallarens_innervaggar.py.
"""
from __future__ import annotations

from modellering import Montage

from . import andbrador, innertak, kallare, kallarens_innervaggar, kokets_inbyggnad, vagginsida, vaggar


def montage() -> Montage:
    m = Montage("Invändigt", beskrivning="Ångbroms, installationsskikt och gips (F-01)")
    m.lagg(innertak.montage())
    m.lagg(vagginsida.montage())
    m.lagg(vaggar.montage())
    m.lagg(kokets_inbyggnad.montage())
    m.lagg(andbrador.montage())
    m.lagg(kallare.montage())
    m.lagg(kallarens_innervaggar.montage())
    return m
