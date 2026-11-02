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
