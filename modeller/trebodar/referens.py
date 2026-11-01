"""Referensmodellen: Onshape-exporten som modellen ursprungligen byggdes efter (fryst, jämförs med `mod jamfor`)."""
from pathlib import Path

from trebodar.skelett import ONSHAPE_TILL_K05

FIL = Path(__file__).resolve().parents[1] / "referens" / "trebodar-onshape.step"
TRANSFORM = ONSHAPE_TILL_K05
