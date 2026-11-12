"""Yttervägg 1NO: vänstra huskroppens gavel mot NO, med dalbalk 4:s ände i slutet. Hammarbandet och regelstyckena
intill balkens ände går fram till balkens sida.

Regelverk 95 mm C24 i väggens system (skelett.VAGGAR["1NO"]), byggt med reglerna i regelstomme.py: plattor,
hörnstolpen LA5, öppningarna (dubbla karmreglar, K-04, överstycken, bröstningar, kortlingar), en fri regel och
upplaget för dalbalk 4 med stolpen LA6 (K-03).
"""
from modellering import Montage

from trebodar.byggdelar.regelvagg import regelvagg
from trebodar.hus.stomme.prefab.regelstomme import Karm, balkens_sida, balkupplag, hornstolpe, vagg


def montage() -> Montage:
    v = regelvagg("1NO")
    staende = hornstolpe(v, 0.0, 1, ("LA5-1", "LA5-2"))
    staende += balkupplag(v, "1NO", "DB4", {4265.0: None, 4455.0: "LA6-2", 4550.0: "LA6-1"})
    vagg(v, "1NO", hammarband=(0.0, balkens_sida("1NO", "DB4")), ander=(False, False), staende=staende,
         reglar=(2355.0,), karmar={"F1": Karm(dubbel=True, kortlingar=(405.0,)),
                                   "F2": Karm(dubbel=True, kortlingar=(277.5,))})
    return v.montage()
