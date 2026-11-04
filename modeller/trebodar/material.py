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
TRALL = Material("Trall", "Trall, tryckimpregnerad furu NTR AB, grånad (altanen)", 550, "#a29d94", 0.86,
                 textur="virke", rendering=rendering(art="furu", yta="granad", riktning="x", tvars="y"), cad="#a7a198")
TRYCKIMP = Material("Tryckimpregnerat", "Tryckimpregnerat virke NTR AB (altanens bjälkar och bärlinor)", 550,
                    "#b9b48f", 0.8, textur="virke", rendering=rendering(art="furu", yta="impregnerad", riktning="x",
                                                                        tvars="y"), cad="#a9b58a")
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
ASK = Material("Ask", "Ask, oljad (snickerier)", 680, "#d5ccbb", 0.46, textur="virke",
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
# dörrarnas panel (ärende #33): stående panel på dörrbladet, brädorna på höjden (dörrens z), i den andra kulören än
# fasaden runt dörren (DORRPANEL nedan)
_DORRPANEL = {**_PANEL, "riktning": "z", "tvars": "x", "skruv_cc": 400.0, "skruv_start": 0.0}
DORRPANEL_FALUROD = Material("Dörrpanel falu rödfärg", "Stående panel på dörrbladet, sågad gran 22 mm, Falu rödfärg",
                             450, "#8f463a", 0.95, textur="bradpanel", enhet="m2",
                             rendering=rendering(**_DORRPANEL, behandling="tackfarg", farg2="#743529",
                                                 variation=0.07, genomslag=0.18, strimmor=0.5, relief=2.0,
                                                 skruvfarg="#9a8580"), cad="#b5463a")
DORRPANEL_JARNVITRIOL = Material("Dörrpanel järnvitriol", "Stående panel på dörrbladet, sågad gran 22 mm, järnvitriol",
                                 450, "#7f7b74", 0.9, textur="bradpanel", enhet="m2",
                                 rendering=rendering(**_DORRPANEL, behandling="jarnvitriol", farg="#938f89",
                                                     farg2="#3b3835", farg3="#6d6357", kvistfarg="#1f1b18",
                                                     variation=0.22, strimmor=1.5, relief=1.6, skruvfarg="#c9cbcd"),
                                 cad="#8c8579")
DORRBLAD = Material("Dörrblad", "Dörrbladets kärna, plywood", 550, "#c9a878", 0.6, cad="#d2b383")

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
KALCIUMSILIKAT_MALAD = Material("Kalciumsilikat målad", "Kalciumsilikatskiva, målad i väggarnas vita färg (kaminens front)",
                                450, "#eceae4", 0.88, textur="gips", enhet="m2", cad="#f2f2ee")
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
# VELFAC 200 ENERGY (fönstren och fönsterdörrarna, byggdelar/velfac.py): bågens bärande profil av glasfiberkomposit
# och de inre profilerna, svarta, tätnings- och distanslisterna och anslutningsplåtarna runt karmen i fönstrens kulör
# (en egen sort, som får gå upp bakom läkten: kontrollregler.TILLATNA_OVERLAPP)
BAGPROFIL = Material("Bågprofil", "Bågens profiler av glasfiberkomposit och plast, svarta (VELFAC 200 ENERGY)", 1800,
                     "#1e2022", 0.45, cad="#30353a")
TATNINGSLIST = Material("Tätningslist", "Tätnings-, distans- och anslutningslister, EPDM och plast, svarta", 1200,
                        "#141516", 0.75, cad="#202326")
FOGMASSA = Material("Fogmassa", "Lufttät fog, MS-polymer på bottningslist (fönstrens och dörrarnas fogar)", 1500,
                    "#3c4043", 0.8, cad="#5a6066")
PLAT_RAL3009 = Material("Anslutningsplåt RAL 3009", "Anslutningsplåt aluminium 1 mm pulverlackerad RAL 3009 oxidröd "
                        "(över- och sidoplåtar vid fönstren)", 2700, "#642424", 0.4, textur="pulverlack", cad="#8c3a32")
PLAT_RAL7012 = Material("Anslutningsplåt RAL 7012", "Anslutningsplåt aluminium 1 mm pulverlackerad RAL 7012 basaltgrå "
                        "(över- och sidoplåtar vid fönstren)", 2700, "#575d5e", 0.4, textur="pulverlack", cad="#5f676a")
INSTALLATION = Material("Installation", "Installationer (rör)", 1000, "#f08a24", 0.5, cad="#f08a24")

# ------------------------------------------------------------------ inredning (hus/inredning)
SKAPSTOMME = Material("Skåpstomme", "Skåpstommar och hyllor, vit melamin (köket, skafferiet)", 650, "#efeee9", 0.5,
                      cad="#e4e0ee")
VITVARA = Material("Vitvara", "Integrerade kyl- och frysskåp (förenklade som lådor)", 300, "#f2f2f0", 0.35,
                   cad="#9fc2dc")
SOCKELGALLER = Material("Sockelgaller", "Sockelgaller för vitvarornas ventilation, svartlackerad aluminium", 2700,
                        "#1d1d1e", 0.55, cad="#34363a")
# köksskåpen (hus/inredning/koksskap.py): stommar 20 mm och lådor 14 mm av björkplywood, lådbotten 4 mm
BJORKPLYWOOD = Material("Björkplywood", "Björkplywood, klarlackad (köksskåpens stommar och lådor)", 680, "#e4d6ba",
                        0.5, cad="#e9cf9c")
LOPARE = Material("Löpare", "Lådlöpare Blum MOVENTO 760H, förzinkat stål (förenklade)", 7850, "#a3a7ab", 0.45, 0.8,
                  cad="#8c96a0")
BANKSKIVA = Material("Bänkskiva", "Bänkskiva Bricmate Jura, granitkeramik 12 mm, slipad (honed)", 2400, "#d9d1c2",
                     0.55, cad="#cfc4ae")
SANGKLADER = Material("Sängkläder", "Madrass och sängkläder, vitt linne (sängen i sovrummet)", 250, "#ebe9e3", 0.95,
                      cad="#ebe7dd")
VIT_SKIVA = Material("Vit skiva", "Skiva, vitmålad (köksbänkens och öns sidor och öns baksida)", 700, "#efede7", 0.6,
                     cad="#f1efe9")
HALLGLAS = Material("Hällglas", "Induktionshällens glaskeramik, svart", 2500, "#111214", 0.06, cad="#2a2c30")

# ------------------------------------------------------------------ el (hus/installationer/el)
# armaturens lins lyser i renderingen när armaturen är tänd (typen lins); CAD-färgerna lyser fram i webbvisaren
ARMATUR = Material("Armatur", "Armatur, aluminium pulverlackerad matt vit RAL 9003", 2700, "#f2f2ef", 0.5,
                   textur="pulverlack", cad="#f4f1de")
ARMATUR_SVART = Material("Armatur svart", "Armaturens bländskydd, svart", 2700, "#161617", 0.55, cad="#2b2b2e")
ARMATURLINS = Material("Armaturlins", "Armaturens reflektor och lins", 2500, "#f7f5f0", 0.15, textur="lins",
                       cad="#ffd84a")
DRIVDON = Material("Drivdon", "Drivdon för LED (plast)", 1200, "#ececea", 0.6, cad="#8d96a3")
APPARAT = Material("Apparat", "Strömbrytare, dimrar och uttag, vit plast", 1200, "#f4f4f1", 0.35, cad="#fbfbf7")
ELDOSA = Material("Eldosa", "Dosor (plast)", 1000, "#7f8a95", 0.6, cad="#ff7a1a")
ELROR = Material("Elrör", "Flexrör (PVC)", 1400, "#8f9499", 0.6, cad="#ff9d2e")

# ------------------------------------------------------------------ brandlarmet (hus/installationer/brandlarm)
# röda i CAD-färgerna, så att brandlarmet skiljer sig från elen
BRANDVARNARE = Material("Brandvarnare", "Brandvarnare, vit plast", 1100, "#f3f3f0", 0.4, cad="#e8433a")
BRANDLARMSKABEL = Material("Brandlarmskabel", "Installationskabel 4G1,5, vit PVC-mantel (brandlarmet)", 2000,
                           "#ecebe6", 0.5, cad="#c8102e")
# pendlarna: mässing (blank och obehandlad med patina), opalglas och frostat glas (lyser som linsen när armaturen är
# tänd) och textilsladd
MASSING = Material("Mässing", "Mässing, blank (pendlarnas fästen)", 8500, "#d8b56e", 0.22, metall=1.0, cad="#c9a35b")
RAMASSING = Material("Råmässing", "Mässing, obehandlad med patina", 8500, "#c4a46a", 0.38, metall=1.0, textur="patina",
                     rendering=rendering(farg2="#8c7652", andel=0.22, skala=28.0, grovhet2=0.6), cad="#b39a5e")
OPALGLAS = Material("Opalglas", "Opalglas, munblåst (pendlarnas glober)", 2500, "#f6f4ef", 0.08, textur="lins",
                    cad="#fff6d5")
FROSTAT_GLAS = Material("Frostat glas", "Frostat glas (pendelns diffusor)", 2500, "#f2f0eb", 0.45, textur="lins",
                        cad="#fff6d5")
SLADD_VIT = Material("Textilsladd vit", "Textilsladd, vit", 1200, "#e9e8e3", 0.9, cad="#e9e8e3")
SLADD_SVART = Material("Textilsladd svart", "Textilsladd, svart", 1200, "#1b1b1c", 0.9, cad="#2a2a2c")

# ------------------------------------------------------------------ ventilation (hus/installationer/ventilation)
# ytterväggsgallren i fönstrens aluminium (ALUMINIUM per huskropp) och takhuven i takets plåt (TAKPLAT). Kanalerna,
# fläkten och köksfläkten är massiva i modellen: densiteten är plåtens massa fördelad på hela tvärsnittet (kanal
# Ø125 av 0,6 mm plåt ungefär 150 kg/m³), så att materiallistans massor stämmer ungefär
SPIROKANAL = Material("Spirokanal", "Spirokanal, förzinkad stålplåt", 150, "#b9bdc0", 0.4, 1.0, cad="#7fb2e5")
KANALISOLERING = Material("Kanalisolering", "Mineralull med aluminiumfolie runt kanalen", 100, "#c8ccd0", 0.45, 0.7,
                          cad="#a8c8e0")
PLATTKANAL = Material("Plattkanal", "Plattkanal, vit plast", 120, "#eeeeea", 0.45, cad="#9fd0f0")
KOKSFLAKT = Material("Köksfläkt", "Köksfläkt, borstat rostfritt stål", 100, "#c9ccce", 0.32, 1.0, cad="#b8c4cc")
FETTFILTER = Material("Fettfilter", "Köksfläktens fettfilter, aluminium", 500, "#8f9397", 0.5, 1.0, cad="#8f9397")
VENTILATIONSDON = Material("Ventilationsdon", "Frånluftsdon och väggfläktens front, vitlackerat", 1200, "#f1f1ee",
                           0.4, cad="#5aa9e6")
FLAKT = Material("Fläkt", "Kanalfläkt, lackerad stålplåt", 400, "#dcdedf", 0.45, cad="#3d8fd6")

# ------------------------------------------------------------------ tappvatten och teknikrum (hus/installationer)
# rören är massiva cylindrar med skyddsrörets ytterdiameter: densiteten är PEX-rörets och skyddsrörets massa fördelad
# på hela tvärsnittet (rör-i-rör 16/25 ungefär 0,17 kg/m); dosorna, fördelarna och apparaterna likaså
TAPPVATTEN_KV = Material("Tappvatten KV", "Tappvattenrör kallvatten, PEX (rör-i-rör i blått skyddsrör)", 350,
                         "#2f6db3", 0.5, cad="#2f6db3")
TAPPVATTEN_VV = Material("Tappvatten VV", "Tappvattenrör varmvatten, PEX (rör-i-rör i rött skyddsrör)", 350,
                         "#c4372f", 0.5, cad="#d23b2f")
VATTENDOSA = Material("Vattendosa", "Väggdosor, golvgenomföringar och väggfästen för rör-i-rör, plast", 200, "#e6e6e2",
                      0.5, cad="#8a95a0")
FORDELARSTAM = Material("Fördelare", "Fördelare för tappvatten och golvvärme, förnicklad mässing", 5000, "#c9c2a8",
                        0.3, 1.0, cad="#c9a646")
PLATSKAP = Material("Plåtskåp", "Fördelarskåp, vitlackerad stålplåt 1,5 mm", 7850, "#efefec", 0.4, cad="#c3ccd5")
VVS_APPARAT = Material("VVS-apparat", "Värmepump och vattenmätare (förenklade som lådor)", 250, "#eeeeea", 0.45,
                       cad="#dde3e8")

# ------------------------------------------------------------------ golvvärme (hus/installationer/golvvarme)
# rören är massiva: densiteten är rörets och vattnets massa fördelad på hela tvärsnittet (PE-RT 16 × 2,0 med vatten)
GOLVVARME = Material("Golvvärmerör", "Golvvärmerör PE-RT med syrespärr och matarledningar PEX, vattenfyllda", 970,
                     "#e0803a", 0.5, cad="#e8742a")

# ------------------------------------------------------------------ köldbärare (hus/installationer/kollektor)
# skyddsröret är massivt: densiteten är rörets och kollektorslangens massa fördelad på hela tvärsnittet (PE 110 × 4,2
# med två slangar PE 40 med köldbärare ungefär 3 kg/m)
# dräneringen och dagvattnet (hus/installationer/dranering): rören massiva i densiteten (PVC/PP)
DRANROR = Material("Dränrör", "Dränrör PVC Ø110, slitsat, med filterduk", 1400, "#d9a441", 0.6, cad="#e0b040")
DAGVATTENROR = Material("Dagvattenrör", "Markavloppsrör PP Ø110, tätt (dagvatten)", 900, "#c9662e", 0.5,
                        cad="#d0703a")
DRANBRUNN = Material("Dränbrunn", "Brunn PP (dagvatten- och dräneringsbrunn, spolbrunnar)", 900, "#3a3d40", 0.6,
                     cad="#4a4f55")
SKYDDSROR = Material("Skyddsrör", "Skyddsrör PE Ø110 med kollektorslangar", 320, "#2e3238", 0.6, cad="#3a7d44")

# panelens utförande och fönstrens och dörrarnas aluminium per huskropp (byt material här för att prova andra kulörer)
PANEL = {1: PANEL_FALUROD, 2: PANEL_JARNVITRIOL, 3: PANEL_JARNVITRIOL}
DORRPANEL = {1: DORRPANEL_JARNVITRIOL, 2: DORRPANEL_FALUROD, 3: DORRPANEL_FALUROD}   # den andra kulören än fasaden
DORRPANEL_KALLARE = DORRPANEL_JARNVITRIOL                                          # källardörren i granitsockeln
ALUMINIUM = {1: ALU_RAL3009, 2: ALU_RAL7012, 3: ALU_RAL7012}
ANSLUTNINGSPLAT = {1: PLAT_RAL3009, 2: PLAT_RAL7012, 3: PLAT_RAL7012}       # i fönstrens kulör
