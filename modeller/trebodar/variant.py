"""Modellens varianter: samma hus med andra val, för att jämföra dem i webbvisaren och renderingarna.

Varianten väljs med miljövariabeln TREBODAR_VARIANT (`./mod --variant velfac …` sätter den och lägger det som byggs i
ut/velfac/). Utan variant är modellen huset som det är projekterat; handlingarna och kontrollerna gäller den.

- velfac: alla fönster och fönsterdörrar från VELFAC (VELFAC 200 ENERGY, byggdelar/velfac.py) i stället för
  Elitfönster: vridfönstren blir vändbara fönster, de fasta fasta fönster med båge, fönsterdörrarna 1-luft
  fönsterdörrar och skjutdörren en 2-luft skjutdörr mellan två fasta partier. Ytterdörrarna med panel är desamma.
"""
from __future__ import annotations

import os

VARIANTER = {
    "": "huset som det är projekterat (Elitfönster)",
    "velfac": "fönstren och fönsterdörrarna från VELFAC (VELFAC 200 ENERGY)",
}
VARIANT = os.environ.get("TREBODAR_VARIANT", "")
if VARIANT not in VARIANTER:
    raise SystemExit(f"okänd variant TREBODAR_VARIANT={VARIANT} (finns: {', '.join(v for v in VARIANTER if v)})")
VELFAC = VARIANT == "velfac"
