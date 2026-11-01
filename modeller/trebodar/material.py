"""Material: densitet, utseende (STEP, Onshape) och materiallistans enhet, och för renderingen ett procedurellt
material med parametrar (verktyg/modellering/blender/material.py beskriver typerna).

Riktningar i renderingen gäller delens eget system: virke har x längs fibrerna; fasadens skivor x längs väggen och
y uppåt; takets skikt x längs takfallet och z längs nocken.
"""
from modellering import Material, rendering

# ------------------------------------------------------------------ trä
C24 = Material("C24", "Konstruktionsvirke C24", 420, "#d8b47c", 0.7, textur="tra",
               rendering=rendering(farg2="#b48a55", riktning="x", tvars="y", arsring=4.0))
GL30H = Material("GL30h", "Limträ GL30h", 430, "#e0bb82", 0.65, textur="limtra",
                 rendering=rendering(farg2="#c09a62", riktning="x", tvars="y", lamell="z", lamelltjocklek=45.0))
GL30C = Material("GL30c", "Limträ GL30c", 430, "#e3c08a", 0.65, textur="limtra",
                 rendering=rendering(farg2="#c49f68", riktning="x", tvars="y", lamell="z", lamelltjocklek=45.0))
DISTANS = Material("Distansregel", "Distansregel trä eller plywood 10 mm", 450, "#efdcae", 0.8, textur="tra",
                   rendering=rendering(farg2="#d9c08e", riktning="x", tvars="y", arsring=3.0))
RASPONT = Material("Råspont", "Råspont 20 mm", 450, "#d9bb8a", 0.85, textur="bradpanel", enhet="m2",
                   rendering=rendering(farg2="#b8955f", riktning="z", tvars="x", bredd=95.0, fog=1.5,
                                       behandling="obehandlad", variation=0.12))
# Fasadpanel: stående sågade granbrädor 22 mm (förenklat en skiva per vägg; brädorna ritas av renderingen)
PANEL_FALUROD = Material("Panel falu rödfärg", "Stående panel, sågad gran 22 mm, Falu rödfärg", 450, "#84291f",
                         0.93, textur="bradpanel", enhet="m2",
                         rendering=rendering(farg2="#5c1c16", riktning="y", tvars="x", bredd=145.0, fog=4.0,
                                             behandling="tackfarg", variation=0.10))
PANEL_JARNVITRIOL = Material("Panel järnvitriol", "Stående panel, sågad gran 22 mm, järnvitriol", 450, "#958a7b",
                             0.88, textur="bradpanel", enhet="m2",
                             rendering=rendering(farg2="#76634d", riktning="y", tvars="x", bredd=145.0, fog=4.0,
                                                 behandling="jarnvitriol", variation=0.18))
DORRBLAD = Material("Dörrblad", "Dörrblad", 500, "#3d4246", 0.5)

# ------------------------------------------------------------------ skivor och folier
HDF = Material("Hårdboard", "Hårdboard (masonit) 3 mm", 950, "#6b4a2f", 0.7, enhet="m2")
UTEGIPS = Material("Utegips", "Utegips 10 mm", 750, "#d4cdb2", 0.9, enhet="m2")
GIPS = Material("Gips", "Gipsskiva 12,5 mm", 720, "#eeece6", 0.9, enhet="m2")
ANGBROMS = Material("Ångbroms", "Hunton Intello Plus (åldringsbeständig plastfolie)", 900, "#c8d7e0", 0.6,
                    textur="folie", enhet="m2", opacitet=0.6)
PAPP = Material("Underlagspapp", "Underlagspapp T-Roof YEP 2500", 1100, "#1d1e20", 0.9, textur="papp", enhet="m2",
                rendering=rendering(farg2="#2c2d30"))
TAKPLAT = Material("Takplåt", "Zink-magnesiumbelagd stålplåt 0,6 mm, bandtäckt", 7850, "#9aa0a4", 0.4, 1.0,
                   textur="falsad_plat", enhet="m2",
                   rendering=rendering(riktning="x", tvars="z", avstand=525.0, fals=25.0))

# ------------------------------------------------------------------ isolering
TRAFIBER = Material("Träfiberisolering", "Lösull av träfiber", 45, "#c9a46a", 1.0, textur="isolering", enhet="m3",
                    rendering=rendering(farg2="#a8844e"))
MINERALULL = Material("Mineralull", "Mineralullsskiva", 30, "#e8d27a", 1.0, textur="isolering", enhet="m3",
                      rendering=rendering(farg2="#cdb55e"))
CELLPLAST = Material("Cellplast", "Cellplast EPS S100", 20, "#f3ecef", 0.95, textur="cellplast", enhet="m3",
                     rendering=rendering(farg2="#e2d8dc"))
CELLPLAST_S300 = Material("Cellplast S300", "Cellplast EPS S300", 30, "#f2bfd2", 0.95, textur="cellplast",
                          enhet="m3", rendering=rendering(farg2="#e0aabe"))

# ------------------------------------------------------------------ betong, sten och mark
BETONG = Material("Betong", "Betong C30/37", 2400, "#a9a8a3", 0.95, textur="betong", enhet="m3",
                  rendering=rendering(farg2="#8f8e89"))
GRANIT = Material("Granit", "Beklädnadsgranit Bohus Grå", 2650, "#a39a95", 0.8, textur="sten", enhet="m2",
                  rendering=rendering(farg2="#c7bfb9", skift=400.0, langd=900.0, fog=10.0, fogfarg="#6b6865"))
BERG = Material("Berg", "Berg", 2700, "#77716a", 1.0, textur="berg", enhet="m3", rendering=rendering(farg2="#58534e"))
FYLLNING = Material("Fyllning", "Dränerande fyllning", 1900, "#8c867c", 1.0, textur="grus", enhet="m3",
                    rendering=rendering(farg2="#6c665c"))
MARK = Material("Mark", "Uppfyllnad", 1800, "#5d7f3e", 1.0, textur="mark", enhet="m3",
                rendering=rendering(farg2="#43602a"))

# ------------------------------------------------------------------ stål
S355 = Material("S355", "Stål S355J2+N, zinkrik grundfärg", 7850, "#6f747b", 0.5, 1.0, enhet="kg")
S235 = Material("S235", "Stål S235", 7850, "#7a7f86", 0.5, 1.0, enhet="kg")
SPIKPLAT = Material("Spikplåt", "Spikplåt S250GD+Z 2,0 mm", 7850, "#b8bcc2", 0.4, 1.0, enhet="st")

# ------------------------------------------------------------------ fönster, dörrar och installationer
GLAS = Material("Glas", "Fönsterglas", 2500, "#cfe3ea", 0.02, textur="glas", opacitet=0.35)
KARM = Material("Karm", "Fönster- och dörrkarm", 500, "#26292c", 0.5)
INSTALLATION = Material("Installation", "Installationer (rör)", 1000, "#f08a24", 0.5)
