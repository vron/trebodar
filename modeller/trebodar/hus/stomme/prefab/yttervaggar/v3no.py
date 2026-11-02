"""Yttervägg 3NO: högra huskroppens gavel mot NO, med dalbalk 2:s ände i början. Hammarbandet och regelstyckena
intill balkens ände går fram till balkens sida.

Regelverk 95 mm C24 i väggens system (skelett.VAGGAR["3NO"]), byggt med reglerna i regelstomme.py: plattor,
upplaget för dalbalk 2 med regeln LA3 (K-03), öppningarna (karmreglar, överstycken, bröstningar, kortlingar), en fri
regel och hörnstolpen LA4.
"""
from modellering import Montage

from trebodar import skelett as S
from trebodar.byggdelar.regelvagg import regelvagg
from trebodar.hus.stomme.prefab.regelstomme import Karm, balkens_sida, balkupplag, hornstolpe, vagg


def montage() -> Montage:
    v = regelvagg("3NO")
    langd = S.VAGGAR["3NO"].langd
    staende = balkupplag(v, "3NO", "DB2", {0.0: None, 95.0: "LA3", 285.0: None})
    staende += hornstolpe(v, langd, -1, ("LA4-1", "LA4-2"))
    vagg(v, "3NO", hammarband=(balkens_sida("3NO", "DB2"), langd), ander=(False, False), staende=staende,
         reglar=(2195.0,), karmar={"F1": Karm(kortlingar=(277.5,)), "F2": Karm(kortlingar=(550.0,))})
    return v.montage()
