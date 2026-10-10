"""
Jämförelse av en beräknings egna geometridata med det som kontrollen läser ur modellen.

Beräkningarna har sina koordinater i sina egna källfiler och läser aldrig modellen. Kontrollerna här läser
modellen, räknar fram samma data och jämför med källfilen. Avvikelser rättas för hand i källfilen eller läggs i
modeller/modell-todo.md.
"""


def jamfor(kalla, modell, tol=0.5, vag="", utelamna=()):
    """Lista med avvikelser mellan källfilens data och modellens (tal inom tol räknas som lika)."""
    if any(vag.endswith(u) for u in utelamna):
        return []
    if isinstance(kalla, dict) and isinstance(modell, dict):
        fel = []
        for k in sorted(set(kalla) | set(modell)):
            if k not in modell:
                fel.append(f"{vag}.{k}: finns i källfilen men inte i modellen")
            elif k not in kalla:
                fel.append(f"{vag}.{k}: finns i modellen men inte i källfilen")
            else:
                fel += jamfor(kalla[k], modell[k], tol, f"{vag}.{k}", utelamna)
        return fel
    if isinstance(kalla, (list, tuple)) and isinstance(modell, (list, tuple)):
        if len(kalla) != len(modell):
            return [f"{vag}: {len(kalla)} element i källfilen, {len(modell)} i modellen"]
        fel = []
        for i, (a, b) in enumerate(zip(kalla, modell)):
            fel += jamfor(a, b, tol, f"{vag}[{i}]", utelamna)
        return fel
    if isinstance(kalla, (int, float)) and isinstance(modell, (int, float)) and not isinstance(kalla, bool):
        return [] if abs(kalla - modell) <= tol else [f"{vag}: källfilen {kalla}, modellen {modell}"]
    return [] if kalla == modell else [f"{vag}: källfilen {kalla!r}, modellen {modell!r}"]


def redovisa(namn, fel, max_rader=60):
    """Skriver resultatet och returnerar slutkoden (0 = allt stämmer)."""
    if not fel:
        print(f"{namn}: allt stämmer med modellen.")
        return 0
    print(f"{namn}: {len(fel)} avvikelser mot modellen:")
    for f in fel[:max_rader]:
        print("  " + f)
    if len(fel) > max_rader:
        print(f"  … och {len(fel) - max_rader} till")
    return 1
