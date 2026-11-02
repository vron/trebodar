"""Produkterna i golvvärmen, tills vidare allmänna typer med vanliga mått (ej valda): rören i slingorna och
tilloppen, matarledningarna från värmepumpen och fördelarna.
"""
from __future__ import annotations

from .typer import Fordelartyp, Rortyp

GOLVVARMEROR = Rortyp("PERT16", "PE-RT 16 × 2,0 med syrespärr (ej valt)", 16.0, 2.0, max_langd=90.0)
MATARROR = Rortyp("PEX25", "PEX 25 × 3,5, isoleras (ej valt)", 25.0, 3.5)
FORDELARE = Fordelartyp("GVF12", "Golvvärmefördelare med flödesmätare och ställdon, högst 12 kretsar (ej vald)", 12)
