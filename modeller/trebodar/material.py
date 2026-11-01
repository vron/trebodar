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
# Fasadpanel: stående sågade granbrädor 22×145 (förenklat en skiva per vägg; brädorna, kvistarna och skruvarna ritas
# av renderingen). Skruvarna sitter i spikläkterna, c/c 600 från fasadens underkant (hus/fasad/fasad.py).
_PANEL: dict[str, float | str] = dict(riktning="y", tvars="x", bredd=145.0, fog=4.0, arsring=2.8, kvistar=3.5,
                                     kvist=17.0, skruv_cc=600.0, skruv_start=-127.5, skruv_per_brada=2.0,
                                     skruv_kant=25.0, skruv=6.0)
PANEL_FALUROD = Material("Panel falu rödfärg", "Stående panel, sågad gran 22 mm, Falu rödfärg", 450, "#963c2b",
                         0.93, textur="bradpanel", enhet="m2",
                         rendering=rendering(**_PANEL, behandling="tackfarg", farg2="#79291e", variation=0.06,
                                             skruvfarg="#9a8580"))
PANEL_JARNVITRIOL = Material("Panel järnvitriol", "Stående panel, sågad gran 22 mm, järnvitriol", 450, "#7f7b74",
                             0.9, textur="bradpanel", enhet="m2",
                             rendering=rendering(**_PANEL, behandling="jarnvitriol", farg="#8b8780", farg2="#4f4a43",
                                                 farg3="#7a6b5a", kvistfarg="#27221d", variation=0.14,
                                                 skruvfarg="#c9cbcd"))
DORRBLAD = Material("Dörrblad", "Dörrblad", 500, "#3d4246", 0.5)

# ------------------------------------------------------------------ skivor och folier
HDF = Material("Hårdboard", "Hårdboard (masonit) 3 mm", 950, "#6b4a2f", 0.7, enhet="m2")
UTEGIPS = Material("Utegips", "Utegips 10 mm", 750, "#d4cdb2", 0.9, enhet="m2")
GIPS = Material("Gips", "Gipsskiva 12,5 mm", 720, "#eeece6", 0.9, enhet="m2")
ANGBROMS = Material("Ångbroms", "Hunton Intello Plus (åldringsbeständig plastfolie)", 900, "#c8d7e0", 0.6,
                    textur="folie", enhet="m2", opacitet=0.6)
PAPP = Material("Underlagspapp", "Underlagspapp T-Roof YEP 2500", 1100, "#1d1e20", 0.9, textur="papp", enhet="m2",
                rendering=rendering(farg2="#2c2d30"))
# Takplåten i banor med falsar (hus/tak/tak.py); varje bana skiftar något i ton och glans och buktar mellan falsarna
TAKPLAT = Material("Takplåt", "Zink-magnesiumbelagd stålplåt 0,6 mm, bandtäckt", 7850, "#bfc4c6", 0.36, 1.0,
                   textur="plat", enhet="m2",
                   rendering=rendering(riktning="x", tvars="z", avstand=525.0, variation=0.035, grovhet_variation=0.14,
                                       buckla=0.0015))

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
# Bohus Grå: medelkornig grå granit, kluven yta; stenarna är egna delar (hus/grund/fasadsten.py)
GRANIT = Material("Granit", "Beklädnadsgranit Bohus Grå", 2650, "#a39d98", 0.78, textur="granit", enhet="st",
                  rendering=rendering(farg="#9d9790", farg2="#bcb8b1", farg3="#45413d", rosa="#a99285", korn=5.5,
                                      variation=0.16, varm=0.3, rost=0.35))
FOGBRUK = Material("Fogbruk", "Fogbruk för natursten (Mapei Ultracolor Plus), cementgrå", 1900, "#8e8b86", 0.95,
                   textur="bruk", enhet="kg", rendering=rendering(farg2="#7c7974"))
ARMERINGSBRUK = Material("Armeringsbruk", "Armeringsbruk 6 mm med nät och fästmassa 9 mm (Mapei)", 1600, "#b3afa6",
                         0.95, textur="bruk", enhet="m2", rendering=rendering(farg2="#a19d94"))
BERG = Material("Berg", "Berg", 2700, "#77716a", 1.0, textur="berg", enhet="m3", rendering=rendering(farg2="#58534e"))
FYLLNING = Material("Fyllning", "Dränerande fyllning", 1900, "#8c867c", 1.0, textur="grus", enhet="m3",
                    rendering=rendering(farg2="#6c665c"))
MARK = Material("Mark", "Uppfyllnad", 1800, "#62744a", 1.0, textur="mark", enhet="m3",
                rendering=rendering(farg2="#4a5935"))

# ------------------------------------------------------------------ stål
S355 = Material("S355", "Stål S355J2+N, zinkrik grundfärg", 7850, "#6f747b", 0.5, 1.0, enhet="kg")
S235 = Material("S235", "Stål S235", 7850, "#7a7f86", 0.5, 1.0, enhet="kg")
SPIKPLAT = Material("Spikplåt", "Spikplåt S250GD+Z 2,0 mm", 7850, "#b8bcc2", 0.4, 1.0, enhet="st")

# ------------------------------------------------------------------ fönster, dörrar och installationer
GLAS = Material("Glas", "Fönsterglas", 2500, "#cfe3ea", 0.02, textur="glas", opacitet=0.35)
KARM = Material("Karm", "Fönster- och dörrkarm", 500, "#26292c", 0.5)
INSTALLATION = Material("Installation", "Installationer (rör)", 1000, "#f08a24", 0.5)
