"""Stomme prefab: den bärande trästommen ovanför mellanbjälklaget, beställs som en leverans (utan nock- och
dalbalkarna, som är en egen beställning)."""
from modellering import Montage

from .innervaggar import innervaggar
from .stolpar import stolpar
from .takbalkar import takbalkar
from .takstolar import takstolar
from .yttervaggar import yttervaggar


def montage() -> Montage:
    m = Montage("Stomme prefab", beskrivning="Trästommen ovanför mellanbjälklaget: väggar, takstolar, stolpar och "
                                             "takbalkar")
    m.lagg(yttervaggar.montage())
    m.lagg(innervaggar.montage())
    m.lagg(takstolar.montage())
    m.lagg(stolpar.montage())
    m.lagg(takbalkar.montage())
    return m
