"""Regler för kontrollen (`mod kontroll`): avsiktliga överlapp mellan material, med motivering."""

TILLATNA_OVERLAPP = {
    frozenset(("Installation", "Betong")): "rör genom bjälklaget eller bottenplattan (genomföring)",
    frozenset(("Installation", "Cellplast")): "avloppet genom cellplasten under bottenplattan (genomföring)",
    frozenset(("Installation", "Cellplast S300")): "avloppet genom cellplasten under bottenplattan (genomföring)",
    frozenset(("Kamin",)): "rökrörets delar går in i varandra i böjarna",
    frozenset(("Kamin", "Rostfritt")): "rökröret går in i den isolerade skorstenens anslutning i kassen",
    frozenset(("Spikplåt", "Utegips")): "spikplåt 2 mm på gavelstolens utsida, utegipsen fräses ur",
}
