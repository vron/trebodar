"""Regler för kontrollerna: materialpar som inte prövas och avsiktliga överlapp (`mod kontroll`), med motivering, och
modulernas lagerordning (`mod typ`)."""

# moduler (prefix) och vad de inte får importera ur paketet: beroendena går från skelettet och materialen via
# byggdelarna till husets system, och huset beror inte på marken
LAGER = {
    "trebodar.skelett": ("trebodar",),
    "trebodar.material": ("trebodar",),
    "trebodar.byggdelar": ("trebodar.hus", "trebodar.mark"),
    "trebodar.hus": ("trebodar.mark",),
}

# delar som inte kontrolleras alls (sökvägens början): elens rör, dosor, apparater och armaturer, ventilationens
# kanaler, don och fläktar och tappvattnets rör och dosor går genom skikten utan håltagning i modellen (ventilationen
# och vattnet har egna kontroller, mot huset och mot varandra: ./mod ventilation kontroll, ./mod vatten kontroll)
UTOM_KONTROLL = {
    "Hus/Installationer/El": "elinstallationen: rör, dosor, apparater och armaturer får gå genom andra delar",
    "Hus/Installationer/Ventilation": "ventilationen: kanaler, don och fläktar får gå genom andra delar "
                                      "(egen kontroll, ./mod ventilation kontroll)",
    "Hus/Installationer/Vatten": "tappvattnet: rör, dosor och fördelare får gå genom andra delar "
                                 "(egen kontroll, ./mod vatten kontroll)",
    "Hus/Installationer/Golvvärme": "golvvärmen: rör och fördelare får gå genom andra delar "
                                    "(egen kontroll, ./mod golvvarme kontroll)",
    "Hus/Installationer/Köldbärare": "köldbärarledningarna: skyddsrören får gå genom bottenplattan "
                                     "(egen kontroll, ./mod kollektor kontroll)",
    "Hus/Installationer/Brandlarm": "brandlarmet: kablar, dosor och brandvarnare får gå genom andra delar "
                                    "(egen kontroll, ./mod brandlarm kontroll)",
}

# installationerna som prövas mot varandra: ventilationen, vattnet, golvvärmen, köldbäraren och brandlarmet har egna
# krockkontroller mot husets delar (verktyg/modellering, installationer.py), där elens delar också prövas
INSTALLATIONER = ("Hus/Installationer/El", "Hus/Installationer/Ventilation", "Hus/Installationer/Vatten",
                  "Hus/Installationer/Golvvärme", "Hus/Installationer/Köldbärare", "Hus/Installationer/Brandlarm")

IGNORERADE = {
    frozenset(("Armering", "Betong")): "armeringen ligger i betongen",
    frozenset(("Armering",)): "järnen ligger mot varandra i korsningar och skarvar",
}

TILLATNA_OVERLAPP = {
    frozenset(("Armering", "Installation")): "golvvärmen och avloppet i betongen: järnen läggs om runt rören",
    frozenset(("Installation", "Betong")): "rör genom bjälklaget eller bottenplattan (genomföring)",
    frozenset(("Installation", "Cellplast")): "avloppet genom cellplasten under bottenplattan (genomföring)",
    frozenset(("Installation", "Cellplast S300")): "avloppet genom cellplasten under bottenplattan (genomföring)",
    frozenset(("Kamin",)): "rökrörets delar går in i varandra i böjarna",
    frozenset(("Kamin", "Rostfritt")): "rökröret går in i den isolerade skorstenens anslutning i kassen",
    frozenset(("Spikplåt", "Utegips")): "spikplåt 2 mm på gavelstolens utsida, utegipsen fräses ur",
}
