"""Ramverk för kodgenererade 3D-modeller: recept (form), modellträd (modell), kärna (OCCT, cache, parallellt),
export (STEP, GLB, materiallista) och kontroller (krockar, kontakter, jämförelse mot referens)."""
from .form import (Cylinder, Diff, Form, Importerad, Kapad, Lada, Prisma, Snitt, Speglad, Transf, Union, box,
                   cylinder, lada, prisma, rektangel)
from .modell import Del, Instans, Material, Montage
from .placering import IDENTITET, Placering, axlar, flytt, rot

__all__ = ["Cylinder", "Diff", "Form", "Importerad", "Kapad", "Lada", "Prisma", "Snitt", "Speglad", "Transf",
           "Union", "box", "cylinder", "lada", "prisma", "rektangel", "Del", "Instans", "Material", "Montage",
           "IDENTITET", "Placering", "axlar", "flytt", "rot"]
