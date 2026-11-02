"""Material: densitet, materiallistans enhet och två utseenden: CAD-färgen (`cad`: STEP, Onshape, webbvisaren),
vald så att olika slags delar skiljer sig åt (i stil med handlingarnas ritningar: trä gulbrunt, läkt ljusgult,
limträ bärnsten, isolering rosa, cellplast ljusblått, gips vitt, betong gråbeige, stål blågrått, mark grönt), och
det verkliga utseendet för renderingen (farg och ett procedurellt material med parametrar;
verktyg/modellering/blender/material.py beskriver typerna).

Riktningar i renderingen gäller delens eget system: virke har x längs fibrerna; fasadens skivor x längs väggen och
y uppåt; takets skikt x längs takfallet och z längs nocken.
"""
from modellering import Material, rendering

# ------------------------------------------------------------------ trä
# Trä: varje bit sågad ur en egen stock (verktyg/modellering/blender/tra.py, typen virke: träslag och ytbehandling);
# renderingens färger är träslagets, farg är träets färg i webbvisaren
_GRAN = rendering(art="gran", riktning="x", tvars="y")
C24 = Material("C24", "Konstruktionsvirke C24", 420, "#e3cfa3", 0.74, textur="virke", rendering=_GRAN, cad="#d9b77e")
# läkt (ströläkt, spikläkt, installationsläkt) som eget material, så att den skiljer sig från stommen
C24_LAKT = Material("Läkt", "Läkt C24", 420, "#e3cfa3", 0.74, textur="virke", rendering=_GRAN, cad="#eee3a0")
FURU = Material("Furu", "Furu, hyvlad och oljad (trappa)", 500, "#dcb47e", 0.46, textur="virke",
                rendering=rendering(art="furu", yta="olja", riktning="x", tvars="y"), cad="#c98a52")
BRADA = Material("Bräda", "Hyvlade granbrädor 12 mm (fickdörrarnas fickor, i stället för OSB)", 450, "#e3cfa3", 0.74,
                 textur="virke", rendering=_GRAN, cad="#e3cb92")
LARK = Material("Lärk", "Sibirisk lärk, obehandlad (trätrappa ute)", 600, "#d2a872", 0.74, textur="virke",
                rendering=rendering(art="lark", riktning="x", tvars="y"), cad="#d6ad74")
GL30H = Material("GL30h", "Limträ GL30h", 430, "#e3cfa3", 0.7, textur="virke",
                 rendering=rendering(art="gran", riktning="x", tvars="y", lamell="z", lamelltjocklek=45.0, kvistar=1.2),
                 cad="#d39552")
GL30C = Material("GL30c", "Limträ GL30c", 430, "#e3cfa3", 0.7, textur="virke",
                 rendering=rendering(art="gran", riktning="x", tvars="y", lamell="z", lamelltjocklek=45.0, kvistar=1.6),
                 cad="#c47f3e")
DISTANS = Material("Distansregel", "Distansregel trä eller plywood 10 mm", 450, "#e3cfa3", 0.8, textur="virke",
                   rendering=_GRAN, cad="#c7b3d6")
# Ask, oljad: snickerier och bänkskivor (köket); lamell och lamelltjocklek för lamellimmade skivor
ASK = Material("Ask", "Ask, oljad (snickerier)", 680, "#dccbaa", 0.46, textur="virke",
               rendering=rendering(art="ask", yta="olja", riktning="x", tvars="y"), cad="#dccbaa")
RASPONT = Material("Råspont", "Råspont 20 mm", 450, "#d9bb8a", 0.85, textur="bradpanel", enhet="m2",
                   rendering=rendering(farg2="#b8955f", riktning="z", tvars="x", bredd=95.0, fog=1.5,
                                       behandling="obehandlad", variation=0.12), cad="#a88a5c")
# Fasadpanel: stående sågade granbrädor 22×145 (förenklat en skiva per vägg; brädorna, kvistarna och skruvarna ritas
# av renderingen). Skruvarna sitter i spikläkterna, c/c 600 från fasadens underkant (hus/fasad/fasad.py).
_PANEL: dict[str, float | str] = dict(riktning="y", tvars="x", bredd=145.0, fog=4.0, arsring=2.8, kvistar=2.2,
                                     kvist=24.0, skarvar=0.06, skruv_cc=600.0, skruv_start=-127.5, skruv_per_brada=2.0,
                                     skruv_kant=25.0, skruv=6.0)
PANEL_FALUROD = Material("Panel falu rödfärg", "Stående panel, sågad gran 22 mm, Falu rödfärg", 450, "#8f463a",
                         0.95, textur="bradpanel", enhet="m2",
                         rendering=rendering(**_PANEL, behandling="tackfarg", farg2="#743529", variation=0.07,
                                             genomslag=0.18, strimmor=0.5, relief=2.0, skruvfarg="#9a8580"),
                         cad="#b5463a")
PANEL_JARNVITRIOL = Material("Panel järnvitriol", "Stående panel, sågad gran 22 mm, järnvitriol", 450, "#7f7b74",
                             0.9, textur="bradpanel", enhet="m2",
                             rendering=rendering(**_PANEL, behandling="jarnvitriol", farg="#938f89", farg2="#3b3835",
                                                 farg3="#6d6357", kvistfarg="#1f1b18", variation=0.22, strimmor=1.5,
                                                 relief=1.6, skruvfarg="#c9cbcd"), cad="#8c8579")
DORRBLAD = Material("Dörrblad", "Dörrblad", 500, "#3d4246", 0.5, cad="#7a7f88")

# ------------------------------------------------------------------ skivor och folier
HDF = Material("Hårdboard", "Hårdboard (masonit) 3 mm", 950, "#6b4a2f", 0.7, enhet="m2", cad="#6b4a2f")
UTEGIPS = Material("Utegips", "Utegips 10 mm", 750, "#d4cdb2", 0.9, enhet="m2", cad="#c5d3b4")
GIPS = Material("Gips", "Gipsskiva, målad", 720, "#eceae4", 0.88, textur="gips", enhet="m2", cad="#f2f2ee")
OSB = Material("OSB", "OSB/3", 620, "#c8a46c", 0.8, enhet="m2", cad="#c59a5f")
PLYWOOD = Material("Plywood", "Plywood (våtrum)", 520, "#d2b383", 0.7, enhet="m2", cad="#d8a679")
TATSKIKT = Material("Tätskikt", "Tätskikt och fix (våtrum)", 1400, "#4f6d8a", 0.6, enhet="m2", cad="#4f7fc0")
KAKEL = Material("Kakel", "Kakel och klinker", 2000, "#e9ebe8", 0.12, textur="kakel", enhet="m2",
                 rendering=rendering(storlek=200.0, fog=2.0, fogfarg="#cdcbc6"), cad="#8cc7c2")
KALCIUMSILIKAT = Material("Kalciumsilikat", "Kalciumsilikatskiva (brandskydd kring kaminen)", 450, "#ece6dc", 0.9,
                          enhet="m2", cad="#e3c7b0")
KAMIN = Material("Kamin", "Kamininsats, svart stål", 7850, "#232426", 0.6, 0.8, cad="#3a3d42")
ROSTFRITT = Material("Rostfritt", "Rostfritt stål (skorsten)", 7900, "#c4c8cc", 0.3, 1.0, cad="#b4bcc6")
ANGBROMS = Material("Ångbroms", "Hunton Intello Plus (åldringsbeständig plastfolie)", 900, "#c8d7e0", 0.6,
                    textur="folie", enhet="m2", opacitet=0.6, cad="#5fb3d9")
PAPP = Material("Underlagspapp", "Underlagspapp T-Roof YEP 2500", 1100, "#1d1e20", 0.9, textur="papp", enhet="m2",
                rendering=rendering(farg2="#2c2d30"), cad="#3b3d42")
# Takplåten i banor med falsar (hus/tak/tak.py); varje bana skiftar något i ton och glans och buktar mellan falsarna
TAKPLAT = Material("Takplåt", "Zink-magnesiumbelagd stålplåt 0,6 mm, bandtäckt", 7850, "#b9bdbe", 0.5, 1.0,
                   textur="plat", enhet="m2",
                   rendering=rendering(riktning="x", tvars="z", avstand=525.0, variation=0.035, grovhet_variation=0.14,
                                       buckla=0.0015), cad="#8796a5")

# ------------------------------------------------------------------ isolering
TRAFIBER = Material("Träfiberisolering", "Lösull av träfiber", 45, "#c9a46a", 1.0, textur="isolering", enhet="m3",
                    rendering=rendering(farg2="#a8844e"), cad="#e9a98e")
MINERALULL = Material("Mineralull", "Mineralullsskiva", 30, "#e8d27a", 1.0, textur="isolering", enhet="m3",
                      rendering=rendering(farg2="#cdb55e"), cad="#f2b6c6")
CELLPLAST = Material("Cellplast", "Cellplast EPS S100", 20, "#f3ecef", 0.95, textur="cellplast", enhet="m3",
                     rendering=rendering(farg2="#e2d8dc"), cad="#c6d6e8")
CELLPLAST_S300 = Material("Cellplast S300", "Cellplast EPS S300", 30, "#f2bfd2", 0.95, textur="cellplast",
                          enhet="m3", rendering=rendering(farg2="#e0aabe"), cad="#93b0d6")

# ------------------------------------------------------------------ betong, sten och mark
# betongen: ytor uppåt slipat och impregnerat golv (mellanbjälklaget, plattan på mark, bottenplattan), annars gjuten
BETONG = Material("Betong", "Betong C30/37", 2400, "#aeaca6", 0.95, textur="betong", enhet="m3",
                  rendering=rendering(farg2="#94928c", golv_grovhet=0.32), cad="#c8c2b6")
# Bohus Grå: medelkornig grå granit, kluven yta; stenarna är egna delar (hus/grund/fasadsten.py)
_GRANIT = rendering(farg="#9d9790", farg2="#bcb8b1", farg3="#45413d", rosa="#a99285", korn=5.5, variation=0.16,
                    varm=0.3, rost=0.35)
GRANIT = Material("Granit", "Beklädnadsgranit Bohus Grå", 2650, "#a39d98", 0.78, textur="granit", enhet="st",
                  rendering=_GRANIT, cad="#a9a196")
FOGBRUK = Material("Fogbruk", "Fogbruk för natursten (Mapei Ultracolor Plus), cementgrå", 1900, "#8e8b86", 0.95,
                   textur="bruk", enhet="kg", rendering=rendering(farg2="#7c7974"), cad="#e6dfd2")
ARMERINGSBRUK = Material("Armeringsbruk", "Armeringsbruk 6 mm med nät och fästmassa 9 mm (Mapei)", 1600, "#b3afa6",
                         0.95, textur="bruk", enhet="m2", rendering=rendering(farg2="#a19d94"), cad="#d8cdb7")
BERG = Material("Berg", "Berg", 2700, "#77716a", 1.0, textur="berg", enhet="m3", rendering=rendering(farg2="#58534e"),
                cad="#9c978d")
NATURSTEN = Material("Natursten", "Granit Bohus Grå, blocksteg och hällar (entréavsats och sovrumsavsats)", 2650,
                     "#a39d98", 0.8, textur="granit", enhet="m3", rendering=_GRANIT, cad="#b3aea8")
FYLLNING = Material("Fyllning", "Dränerande fyllning", 1900, "#8c867c", 1.0, textur="grus", enhet="m3",
                    rendering=rendering(farg2="#6c665c"), cad="#d9cba6")
MAKADAM = Material("Makadam", "Makadam 16–32", 1600, "#7d7a74", 1.0, textur="grus", enhet="m3",
                   rendering=rendering(farg2="#5c5955"), cad="#aab4bf")
MARK = Material("Mark", "Uppfyllnad", 1800, "#62744a", 1.0, textur="mark", enhet="m3",
                rendering=rendering(farg2="#4a5935"), cad="#b9cf9a")

# ------------------------------------------------------------------ stål
S355 = Material("S355", "Stål S355J2+N, zinkrik grundfärg", 7850, "#6f747b", 0.5, 1.0, enhet="kg", cad="#6f8196")
S235 = Material("S235", "Stål S235", 7850, "#7a7f86", 0.5, 1.0, enhet="kg", cad="#9aa0a8")
ARMERING = Material("Armering", "Armeringsstål B500B (R-04, R-05, R-06)", 7850, "#5e4a3e", 0.7, 0.6, enhet="kg",
                    cad="#b8462e")
SPIKPLAT = Material("Spikplåt", "Spikplåt S250GD+Z 2,0 mm", 7850, "#b8bcc2", 0.4, 1.0, enhet="st", cad="#b8c2cf")

# ------------------------------------------------------------------ fönster, dörrar och installationer
GLAS = Material("Glas", "Fönsterglas", 2500, "#cfe3ea", 0.02, textur="glas", opacitet=0.35, cad="#a9d8ec")
KARM = Material("Karm", "Fönster- och dörrkarm", 500, "#26292c", 0.5, cad="#414950")
FONSTERTRA = Material("Fönsterträ", "Lamellimmad furu, vitmålad NCS S 0502-Y (fönster, dörrar, smyg)", 500,
                     "#efede6", 0.55, cad="#e6dcc4")
# fönstrens och dörrarnas aluminiumbeklädnad, pulverlackerad: halvblank med apelsinyta, till skillnad från det målade
# träet (kulör per huskropp: ALUMINIUM nedan)
ALU_RAL3009 = Material("Aluminium RAL 3009", "Aluminiumbeklädnad pulverlackerad RAL 3009 oxidröd (fönster, dörrar)",
                       2700, "#642424", 0.4, textur="pulverlack", cad="#8c3a32")
ALU_RAL7012 = Material("Aluminium RAL 7012", "Aluminiumbeklädnad pulverlackerad RAL 7012 basaltgrå (fönster, dörrar)",
                       2700, "#575d5e", 0.4, textur="pulverlack", cad="#5f676a")
HARDTRA = Material("Hårdträ", "Merbau (skjutdörrens tröskel)", 830, "#7a4a2e", 0.6, cad="#8a5536")
INSTALLATION = Material("Installation", "Installationer (rör)", 1000, "#f08a24", 0.5, cad="#f08a24")

# panelens utförande och fönstrens och dörrarnas aluminium per huskropp (byt material här för att prova andra kulörer)
PANEL = {1: PANEL_FALUROD, 2: PANEL_JARNVITRIOL, 3: PANEL_JARNVITRIOL}
ALUMINIUM = {1: ALU_RAL3009, 2: ALU_RAL7012, 3: ALU_RAL7012}
