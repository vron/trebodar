# Elinstallationen

Belysning, apparater, dosor och rör som data i modellen: var punkterna sitter, vad de är för produkter, vilka
lampor som tänds tillsammans och från vilka brytare, och hur rören går i bjälklag, väggar och innertak. Samma data
ger modellens geometri (armaturer, apparater, dosor och rör i 3D), renderingens ljus (armaturernas uppmätta
ljusfördelning), kontrollerna och elritningarna.

```
cd verktyg/modellering
./mod el kontroll     # referenser, styrning, armaturernas vinkel, djup och läkt, rörens böjar, anslutningar
./mod el lista        # punkter, tändgrupper och rör (ut/el/elinstallation.md och .json)
./mod el ritning      # elritningarna E-01 (ut/el/E-01 Elinstallation.pdf, kräver STEP-filen: ./mod bygg)
./mod el hamta        # tillverkarnas fotometrifiler som saknas (till lokalt/el/, versionshanteras inte)
./mod rendera I02 --ljus 12 21 18:00 sol --tand AL-T1 AL-T2=0.5     # kväll, tändgrupperna tända (dimrad)
```

## Filerna

| Fil | Innehåll |
|---|---|
| [`typer.py`](typer.py) | Produkttyperna: `Armaturtyp` (tillverkarens data, mått, fotometrifil), `Apparattyp` (brytare, dimrar, uttag), `Dosatyp`, `Rortyp` |
| [`katalog.py`](katalog.py) | Produkterna: armaturerna (SG Armaturen Junistar Exclusive 903201, infälld; Tube Mini R 320696, tub på stam) och tills vidare allmänna dosor, apparater och rör |
| [`punkter.py`](punkter.py) | Beståndsdelarna (`Lampa`, `Apparat`, `Dosa`, `Tandgrupp`, `Ror`, `Rum`); lägena på husets ytor (`tak`, `kallartak`, `vagg` och rörens brytpunkter `i_tak`, `i_vagg`, `vid_tak`, `i_bjalklag`) i installationernas gemensamma [`../montering.py`](../montering.py) |
| [`lakt.py`](lakt.py) | Innertakets läkt ur innertakets geometri: `mellan_lakten` flyttar en armatur mitt emellan läkten |
| `rum/<rum>.py` | Ett rum: dess punkter, tändgrupper och rören i rummets väggar och innertak |
| `bjalklag/<bjälklag>.py` | Rören ingjutna i ett bjälklag och dess ingjutningsdosor |
| [`matytor.py`](matytor.py) | Mätytorna för ljusplanerna (`./mod ljusplan`): vågräta ytor med höjd, område, rutnät och delområden |
| [`installation.py`](installation.py) | Allt ur modulerna (`MODULER`), kontrollen och utdraget för ritningarna och renderingen |
| [`el.py`](el.py) | Geometrin, ett montage per modul under `Hus/Installationer/El` |

En ny rum- eller bjälklagsmodul läggs till i `MODULER` i `installation.py`.

## Begreppen

- **Punkt**: en armatur (`Lampa`), en apparat (`Apparat`: brytare, dimmer, uttag; med sin apparatdosa) eller en
  dosa (`Dosa`: kopplingsdosa, ingjutningsdosa). Varje punkt har ett **id** (`<rum>-<slag><nr>`: `AL-L01` lampa,
  `AL-B1` brytare eller dimmer, `AL-U1` uttag, `AL-D1` dosa; bjälklagen `MB-` och `BP-`), en **typ** ur katalogen
  och en **montering** på en byggnadsyta.
- **Montering**: läget räknas fram ur husets geometri, så att punkterna följer med när huset ändras:
  - `tak(x, y)`: i innertaket på plan 1, på gipsens yta, vinkelrätt mot takfallet (snedtak 30°);
  - `kallartak(x, y)`: i källarens tak (mellanbjälklagets undersida);
  - `vagg(vägg, u, z, sida)`: på en väggs färdiga yta, u längs väggen (väggarnas kod och system som i
    `skelett.py` och `invandigt/vaggar.py`), z över golvet, sidan ±1 (ytterväggar: insidan).
- **Tändgrupp** (`Tandgrupp`): lampor som tänds tillsammans; varje lampa hör till en. Brytare och dimrar anger vilka
  tändgrupper de styr (`styr`, en per kanal). Tändgruppen är det som tänds i renderingen (`--tand`).
- **Rör** (`Ror`): från en punkt till en annan, genom brytpunkter: i innertakets installationsskikt (`i_tak`), i
  väggens regelfack (`i_vagg`), där röret går från väggen upp i innertaket (`vid_tak`) och ingjutet i ett bjälklag
  (`i_bjalklag`). Rörets ändar är punkternas anslutningar: drivdonet bredvid armaturen och dosans mitt.
- **Matningen**: gruppcentralen och dess grupper läggs till när centralens läge är bestämt; tills dess slutar
  rören i ingjutningsdosor i källarens tak.

Exempel (`rum/allrum.py`): två rader med tre spotar i snedtaket, mitt emellan läkten, en tändgrupp per rad, en
dimmer med två kanaler och rören upp i väggen 2C och längs raderna:

```python
TANDGRUPPER = [Tandgrupp("AL-T1", "Allrum, spotar sydost"), Tandgrupp("AL-T2", "Allrum, spotar nordväst")]
PUNKTER = [
    *lampor("AL-L", JUNISTAR_EXCLUSIVE, [tak(mellan_lakten("2SO", 5705, y), y) for y in Y], "AL-T1"),
    ...
    Apparat("AL-B1", DIMMER_2, vagg("2C", 1350, 1050, sida=1), styr=("AL-T1", "AL-T2")),
]
ROR = [Ror("AL-R02", FXP16, "AL-B1", "AL-L01", via=vid_tak("2C", 1350)), Ror("AL-R03", FXP16, "AL-L01", "AL-L02"), ...]
```

## Armaturerna

Varje armaturtyp har tillverkarens data ur databladet (ljusflöde, effekt, färgtemperatur, färgåtergivning,
strålvinkel, vridbarhet, IP, dimring), måtten (frontring, håltagning, inbyggnadsdjup, lysande yta, separat
drivdon, avstånd till brännbart) och tillverkarens fotometrifil (EULUMDAT), som `./mod el hamta` hämtar till
`lokalt/el/` (filerna är tillverkarens och versionshanteras inte). Renderingen läser fotometrifilen
(`verktyg/modellering/modellering/fotometri.py`: ljusflödet och strålvinkeln kontrolleras, IES till Blender) och
ger varje armatur ett ljus med den uppmätta ljusfördelningen, flödet och färgtemperaturen; linsen lyser för kameran.
Utan fotometrifilen blir ljuset en stråle med databladets strålvinkel.

Armaturerna är infällda (ljuset ut genom takets hål, som Junistar Exclusive) eller har ett huvud under taket
(`Tubhuvud`: en tub på en stam från frontplattan, som Tube Mini R, vridbar kring stammen och lutbar i leden).
Ljuset riktas med `riktning` (standard lodrätt ned) eller mot en punkt med `mot(montering, punkt)`: i snedtaket vrids
Junistar Exclusive 30° (den tål 40°), och Tube Mini R lutas i leden (högst 90° från stammen, som står vinkelrätt mot
taket). Tubens läge (leden, tubens ändar och den lysande ytan) räknas fram i `punkter.tuben` och används av både
geometrin och renderingen.

## Kontrollen

`./mod el kontroll` (fel stoppar, anmärkningar redovisas):

- referenserna: tändgrupper, styrda tändgrupper och rörens ändar finns, en brytare styr högst sina kanaler;
- styrningen: varje tändgrupp styrs av minst en brytare eller dimmer, och har lampor;
- armaturerna: vinkeln som ljuset ska vridas mot armaturens axel ryms i armaturens vridbarhet; inbyggnadsdjupet
  och avståndet till brännbart ryms i innertaket (gips och installationsskikt); hålet och drivdonet ligger inte på
  installationsskiktets läkt;
- rören: summan av böjarna mellan dosorna (mer än 270° är svårt att dra) och att varje punkt har ett rör.

Elinstallationens delar ingår inte i modellens krockkontroll (`kontrollregler.UTOM_KONTROLL`): rören och dosorna går
genom skikten utan att andra delar får hål. I renderingen tar de infällda armaturerna hål i gipsen (bara där).

## Ritningarna

`./mod el ritning` ritar serien E-01 i den gemensamma ritningsmallen (`beräkningar/ritningsmall`, A3, 1:75) på
planer ur modellens snitt (STEP-filen):

- **E-01.1 elplanen** för plan 1: armaturer, apparater och dosor med symboler, tändgruppernas styrning (streckade
  bågar från brytaren till lamporna, färg per tändgrupp), rören i väggar och innertak, och tabeller över
  armaturerna, tändgrupperna, apparaterna och rören;
- **E-01.2 rören i mellanbjälklaget**: de ingjutna rören med numrerade punkter och deras koordinater (K-05), var
  rören går upp i väggarna ovanför och ingjutningsdosorna, med plan 1:s väggar streckade.

`./mod el lista` skriver punktlistan, tändgrupperna och rörlistan med kontrollen (markdown och JSON).

## Ljusplaner

`./mod ljusplan` räknar belysningsstyrkan [lux] på vågräta mätytor ([`matytor.py`](matytor.py): golvet och
bordshöjden på plan 1, köksbänken, källarens golv; ytor och delområden läggs till där) i renderingen, med
armaturernas uppmätta ljusfördelning och reflexerna i rummen, och ritar ljusplaner (E-02.n i ritningsmallen, en pdf
per mätyta) med belysningsstyrkan i färg, isolinjer och medel-, minsta och största värde och jämnhet per rum och
delområde:

```
./mod ljusplan plan1-golv kok-bank                  # alla tändgrupper tända, mörkt ute
./mod ljusplan plan1-bord --tand AL-T1 KO-T1=0.5    # bara några, en dimrad till hälften
./mod ljusplan plan1-bord --ljus 3 20 12:00 mulet --tand     # bara dagsljuset (inga lampor)
```

Flytta eller byt armaturer i rummens moduler och kör igen för att jämföra.
