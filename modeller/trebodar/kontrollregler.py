"""Regler för kontrollerna: materialpar som inte prövas och avsiktliga överlapp (`mod kontroll`), med motivering,
installationernas vägar (`mod kontroll`, `mod vagar`), modulernas lagerordning (`mod typ`) och inköpslistan som
specialprodukternas koder jämförs med (`mod kontroll`, `mod inkop`)."""
from __future__ import annotations

from pathlib import Path

from trebodar import skelett as S
from trebodar.hus.installationer.el.installation import stralar
from trebodar.hus.installationer.fria_volymer import dolda_volymer, fria_volymer

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
    "Hus/Installationer/Dränering": "dräneringen och dagvattnet: rören och brunnarna går i marken "
                                    "(egen kontroll, ./mod dranering kontroll)",
    "Hus/Installationer/Brandlarm": "brandlarmet: kablar, dosor och brandvarnare får gå genom andra delar "
                                    "(egen kontroll, ./mod brandlarm kontroll)",
    "Hus/Installationer/Avlopp": "badrummets avlopp: rören, golvbrunnen och vattenlåsen går genom bjälklaget, golvet "
                                 "och skåpen (egen kontroll, ./mod avlopp kontroll)",
}

# installationerna som prövas mot varandra: ventilationen, vattnet, golvvärmen, köldbäraren, brandlarmet, dräneringen
# och avloppet har egna krockkontroller mot husets delar (verktyg/modellering, installationer.py), där elens delar också
# prövas
INSTALLATIONER = ("Hus/Installationer/El", "Hus/Installationer/Ventilation", "Hus/Installationer/Vatten",
                  "Hus/Installationer/Golvvärme", "Hus/Installationer/Köldbärare", "Hus/Installationer/Brandlarm",
                  "Hus/Installationer/Dränering", "Hus/Installationer/Avlopp")

IGNORERADE = {
    frozenset(("Armering", "Betong")): "armeringen ligger i betongen",
    frozenset(("Armering",)): "järnen ligger mot varandra i korsningar och skarvar",
}

UNDER_SKIVAN = "i de smala väggarna går beslaget ut under den inre skivan, som fälls ur (K-04)"

TILLATNA_OVERLAPP = {
    frozenset(("Armering", "Installation")): "golvvärmen och avloppet i betongen: järnen läggs om runt rören",
    frozenset(("Installation", "Betong")): "rör genom bjälklaget eller bottenplattan (genomföring)",
    frozenset(("Installation", "Cellplast")): "avloppet genom cellplasten under bottenplattan (genomföring)",
    frozenset(("Installation", "Cellplast S300")): "avloppet genom cellplasten under bottenplattan (genomföring)",
    frozenset(("Kamin",)): "rökrörets delar går in i varandra i böjarna",
    frozenset(("Kamin", "Rostfritt")): "rökröret går in i den isolerade skorstenens anslutning i kassen",
    frozenset(("Spikplåt", "Utegips")): "spikplåt 2 mm på gavelstolens utsida, utegipsen fräses ur",
    frozenset(("Stålband", "C24")): "stålbanden (K-04) är infällda i reglarna, hammarbanden, syllarna och takbalkarna",
    frozenset(("Stålband",)): "stålbanden korsar varandra i kryssets mitt",
    frozenset(("Stålband", "Träfiberisolering")): "isoleringen i facken trycks undan vid de infällda stålbanden",
    frozenset(("Stålband", "Mineralull")): "isoleringen i facken trycks undan vid de infällda stålbanden",
    frozenset(("Betongbult", "C24")): "betongbultarna går genom syllarna (#88)",
    frozenset(("Betongbult", "Träfiberisolering")): "isoleringen i facket skärs ur kring bultens mutter (#88)",
    frozenset(("Betongbult", "Mineralull")): "isoleringen i facket skärs ur kring bultens mutter (#88)",
    frozenset(("Betongbult", "Betong")): "betongbultarna i mellanbjälklaget (#88)",
    frozenset(("Betongbult", "Armering")): "bultens hål borras fritt från järnen (järnsökare, bulten flyttas i facket)",
    frozenset(("Betongbult", "Vinkelbeslag")): "den sneda bulten går genom vinkelbeslagets hål (K-04)",
    frozenset(("Betongbult", "Förankringsbeslag")): "ankaret går genom förankringsbeslagets hål (K-04)",
    frozenset(("Vinkelbeslag", "Träfiberisolering")): "isoleringen i facket skärs ur kring vinkelbeslaget (K-04)",
    frozenset(("Vinkelbeslag", "Mineralull")): "isoleringen i facket skärs ur kring vinkelbeslaget (K-04)",
    frozenset(("Förankringsbeslag", "Träfiberisolering")): "isoleringen i facket skärs ur kring förankringsbeslaget "
                                                           "(K-04)",
    frozenset(("Förankringsbeslag", "Mineralull")): "isoleringen i facket skärs ur kring förankringsbeslaget (K-04)",
    frozenset(("Vinkelbeslag", "OSB")): UNDER_SKIVAN,
    frozenset(("Vinkelbeslag", "Plywood")): UNDER_SKIVAN,
    frozenset(("Vinkelbeslag", "Bräda")): UNDER_SKIVAN,
    frozenset(("Stålband", "Vinkelbeslag")): "stålbandet läggs utanpå beslaget vid regelns fot (K-04)",
    frozenset(("Stålband", "Förankringsbeslag")): "stålbandet läggs utanpå beslaget vid regelns fot (K-04)",
    # plåtarna runt fönstren och fönsterdörrarna (VELFAC) går från karmen upp och ut bakom läkten (läkten skruvas genom dem)
    frozenset(("Anslutningsplåt RAL 3009", "Läkt")): "plåten över och vid sidorna av fönstret går upp bakom läkten",
    frozenset(("Anslutningsplåt RAL 7012", "Läkt")): "plåten över och vid sidorna av fönstret går upp bakom läkten",
}

# installationernas vägar (verktyg/modellering/modellering/vagar.py, ärende #34): rören, kablarna och kanalerna (delar
# av LEDNINGAR) ska gå dolda i skikten, ingjutna eller i marken, inte fritt genom rummens luft (eller fönstrens och
# takfönstrens öppningar). I UTANPA-zonerna (under z) får de gå utanpå väggarna och taket, högst så långt från ytan
# (på konsoler); SYNLIGA får synas; in i FRIA_VOLYMER (fickdörrarnas fickor) får de inte gå; i DOLDA_VOLYMER
# (ovanför de nedsänkta innertaken, inuti köksfläktens kåpa) är de dolda
LEDNINGAR = ("Elrör", "Brandlarmskabel", "Tappvatten KV", "Tappvatten VV", "Kopparrör", "Spirokanal", "Plattkanal",
             "Golvvärmerör")
VAGAR_UTOM = {
    "Hus/Installationer/Dränering": "dräneringen och dagvattnet går i marken",
    "Hus/Installationer/Köldbärare": "köldbärarledningarna går i marken och under bottenplattan",
}
UTANPA = (("källaren", -S.H_BJALKLAG, 300.0),)     # på konsoler eller i pendlar under taket
SYNLIGA = {                                          # delträd: motivering
    "Hus/Installationer/Vatten/Kök/KO-DB1-": "kopparrören upp till blandaren i diskbänksskåpet, bakom lådorna (#83)",
    "Hus/Installationer/Vatten/Kök/KO-DM1-": "kopparrörets ände under diskmaskinen, maskinens anslutning (#83)",
}
FRIA_VOLYMER = fria_volymer
DOLDA_VOLYMER = dolda_volymer
# armaturernas avstånd till brännbart material i ljusets riktning (vagar.py): inom det får ingen av husets ytor ligga
# framför den lysande ytan
STRALAR = stralar

# ytskiktens språng och springor (verktyg/modellering/modellering/ytskikt.py, ärende #36): där två skivor av
# YTSKIKT möts i samma plan ska ytan vara jämn, utan språng eller öppna springor (kaminkåpans omålade kalciumsilikat
# syns inte); YTSKIKT_UTOM: delträd vars ytor får ha det, med motivering
YTSKIKT = ("Gips", "Kakel", "Kalciumsilikat målad")
YTSKIKT_UTOM: dict[str, str] = {}


# inköpslistan (IN-01): koderna i modellens `produkt=` kontrolleras mot den (`mod kontroll`, `mod inkop`)
INKOPSLISTA = Path(__file__).resolve().parents[2] / "beräkningar" / "IN-01" / "indata.toml"
