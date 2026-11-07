# Elinstallationen

Belysning, apparater, dosor och rör som data i modellen: var punkterna sitter, vad de är för produkter, vilka
lampor som tänds tillsammans och från vilka brytare, och hur rören går i bjälklag, väggar och innertak. Samma data
ger modellens geometri (armaturer, apparater, dosor och rör i 3D), renderingens ljus (armaturernas uppmätta
ljusfördelning), kontrollerna och elritningarna.

```
cd verktyg/modellering
./mod el kontroll     # referenser, styrning, armaturerna, rörens böjar och anslutningar, grupperna och krockarna
./mod el lista        # punkter, tändgrupper och rör (ut/el/elinstallation.md och .json)
./mod el ritning      # elritningarna E-01.1–E-01.4 (ut/el/E-01 Elinstallation.pdf, kräver STEP-filen: ./mod bygg)
./mod el hamta        # tillverkarnas fotometrifiler som saknas (till lokalt/el/, versionshanteras inte)
./mod rendera I02 --ljus 12 21 18:00 sol --tand AL-T1 AL-T2=0.5     # kväll, tändgrupperna tända (dimrad)
./mod rendera detalj-ph5 detalj-stav detalj-vl45 detalj-glob         # pendlarna på nära håll, kväll och tända
```

## Filerna

| Fil | Innehåll |
|---|---|
| [`typer.py`](typer.py) | Produkttyperna: `Armaturtyp` (tillverkarens data, mått, fotometrifil; `Tubhuvud` för spotar på stam, `Pendel` för pendlar), `Apparattyp` (brytare, dimrar, uttag), `Dosatyp`, `Rortyp` |
| [`katalog.py`](katalog.py) | Produkterna: armaturerna (SG Armaturen Junistar Exclusive 903201, infälld; Tube Mini R 320696, tub på stam; pendlarna Louis Poulsen PH 5 och VL45 Radiohus Ø175, Ø250 och Ø370, Konsthantverk Stav och en glob i opalglas; en vägglampa med glob på arm) och tills vidare allmänna dosor, apparater och rör |
| [`punkter.py`](punkter.py) | Beståndsdelarna (`Lampa`, `Apparat`, `Dosa`, `Tandgrupp`, `Ror`, `Rum`), riktningarna (`mot` en punkt, `lutad` mot en vägg), uttag ovanför fönster (`ovan_fonstret`) och pendelns sladd (`pendeln`); lägena på husets ytor (`tak`, `kallartak`, `vagg` och rörens brytpunkter `i_tak`, `i_vagg`, `vid_tak`, `i_bjalklag`) i installationernas gemensamma [`../montering.py`](../montering.py) |
| [`lakt.py`](lakt.py) | Innertakets läkt ur innertakets geometri: `mellan_lakten` flyttar en armatur mitt emellan läkten |
| `rum/<rum>.py` | Ett rum: dess punkter, tändgrupper och rören i rummets väggar och innertak. Plan 1 efter belysningsplanen (ärende #8): allrum, kök, gång, hall, vardagsrum, sovrum, kontor, sovrum och kontor i högra huskroppen, gästrum; badrummet (ärende #52) |
| `bjalklag/<bjälklag>.py` | Rören ingjutna i ett bjälklag: gruppernas rör från centralen (mellanbjälklaget) och brandlarmets matningsdosa |
| [`grupper.py`](grupper.py) | Gruppcentralen och grupperna: säkring, faser, ledarnas area, jordfelsskydd och punkterna i rörens ordning |
| [`kedjor.py`](kedjor.py) | Rören mellan gruppernas punkter: genom innertaket, längs väggarna och genom bjälklaget |
| [`dragning.py`](dragning.py) | Rörens vägar: genom innertaket, i väggen och upp ur bjälklaget mellan järnen |
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
- **Grupperna** ([`grupper.py`](grupper.py), #50, #51): gruppcentralen sitter i teknikrummet i källaren på V3 väster
  om vattenmätaren (`../teknikrum.GRUPPCENTRAL`, punkten `GC` i [`rum/teknikrum.py`](rum/teknikrum.py)), med
  huvudbrytare, överspänningsskydd och en personskyddsautomat (typ A 30 mA) per grupp. Varje grupp har sina punkter
  (apparater och dosor, lamporna matas genom brytarna) i rörens ordning: ett rör från centralen till den första
  ([`bjalklag/mellanbjalklag.py`](bjalklag/mellanbjalklag.py), `Gnn-M`, ingjutet i mellanbjälklaget) och därifrån rör
  mellan punkterna ([`kedjor.py`](kedjor.py), `Gnn-Rn`): i väggarna och innertaket, förgrenat i apparatdosorna.
- **Rören i mellanbjälklaget**: de klena (Ø16) i elrörens övre nivå, över tappvattnet och golvvärmen, hällens (Ø20) i
  den undre, fritt från tappvattnet (`../montering.BJALKLAG`). De går upp ur centralens ovansida i två rader mellan
  underkantsnätets järn (den bakre i V3:s cellplast) och i stråk (`../strak`, en fil per rör) genom glipan mellan
  källarväggarnas järn: söderut till badrummet och sovrummet, österut till allrummet, köket och högra huskroppen, och
  norrut över V3 till hallen, ön och hällen. Rören håller sig utanför ytterväggarnas vinkeljärn (R-06 pos 14), som
  går in i bjälklaget vinkelrätt mot väggarna, och korsar dem bara vinkelrätt; de går upp i väggarnas regelfack eller
  ytterväggarnas installationsskikt mellan överkantsnätets järn ([`dragning.py`](dragning.py)).

Exempel (`rum/vardagsrum.py`): två rader med fyra spotar i snedtaket, mitt emellan läkten och lutade mot närmaste
långsida, tre VL45 på olika höjd, en tändgrupp per rad och en för VL45, dimrarna på väggen 1D och rören upp i väggen
och längs raderna:

```python
PUNKTER = [
    *[Lampa(f"VR-L{4 * i + j + 1:02d}", JUNISTAR_EXCLUSIVE, tak(mellan_lakten(kod, x, y), y), tand,
            riktning=lutad((s, 0.0), LUTNING)) for i, (kod, x, ys, s, tand) in enumerate(RADER) for j, y in enumerate(ys)],
    *[Lampa(f"VR-L{9 + i:02d}", t, tak(x, y), "VR-T3", underkant=z) for i, (t, x, y, z) in enumerate(VL45)],
    Apparat("VR-B1", DIMMER_2, vagg("1D", U_B, 1050.0, sida=1), styr=("VR-T1", "VR-T2")),
    Apparat("VR-U1", UTTAG_1, ovan_fonstret("1NV", 1000.0)),
    ...
]
ROR = [Ror("VR-R01", FXP16, "VR-B1", "VR-L01", via=vid_tak("1D", U_B, sida=1)), ...]
```

## Armaturerna

Varje armaturtyp har tillverkarens data ur databladet (ljusflöde, effekt, färgtemperatur, färgåtergivning,
strålvinkel, vridbarhet, IP, dimring), måtten (frontring, håltagning, inbyggnadsdjup, lysande yta, separat
drivdon, avstånd till brännbart material i ljusets riktning), monteringsanvisningens krav (om den infällda armaturen
får täckas med isolering, annars den fria höjden ovanför takytan och luften runt den) och tillverkarens fotometrifil
(EULUMDAT), som `./mod el hamta` hämtar till `lokalt/el/` (filerna är tillverkarens och versionshanteras inte).
Renderingen läser fotometrifilen (`verktyg/modellering/modellering/fotometri.py`: ljusflödet och strålvinkeln
kontrolleras, IES till Blender) och ger varje armatur ett ljus med den uppmätta ljusfördelningen, flödet och
färgtemperaturen; linsen lyser för kameran. Utan fotometrifilen blir ljuset en stråle med databladets strålvinkel.

Armaturerna är infällda (ljuset ut genom takets hål, som Junistar Exclusive), har ett huvud under taket
(`Tubhuvud`: en tub på en stam från frontplattan, som Tube Mini R, vridbar kring stammen och lutbar i leden) eller är
pendlar (`Pendel`, nedan).
Ljuset riktas med `riktning` (standard lodrätt ned) eller mot en punkt med `mot(montering, punkt)`: i snedtaket vrids
Junistar Exclusive 30° (den tål 40°), och Tube Mini R lutas i leden (högst 90° från stammen, som står vinkelrätt mot
taket). Tubens läge (leden, tubens ändar och den lysande ytan) räknas fram i `punkter.tuben` och används av både
geometrin och renderingen.

### Pendlarna

En pendel hänger i en textilsladd från en takkopp på innertaket (takkoppen följer snedtaket, sladden hänger lodrätt)
med armaturens underkant `underkant` över golvet. Formen ger geometrin i [`el.py`](el.py) ur katalogens mått, byggd
av rotationskroppar (ramverkets `varv`): PH 5 med skärmarna mätta ur tillverkarens produktbild (toppskärmen, kronan
under den, huvudskärmen Ø500, mellanskivan, kupan och det frostade glaset), VL45 som en superellips av opalglas med
fot och ett fäste av mässing, globen som ett klot under en kåpa och Stav som en stav och ett rör av råmässing med
linsen i botten. Ljuskällan (lampan i sockeln, `ljuskalla`; utom i Stav inte vald) sitter `kalla` under armaturens
överkant och lyser lika åt alla håll (Stav: en stråle nedåt): i renderingen formar skärmarna ljuset (de skuggar och
reflekterar), medan glaset inte skuggar men lyser med flödet genom det fördelat på dess yta (`lysande_yta`,
`lysande_andel`; opalglasets `transmission` är en uppskattning). Ljusflödet i tabellerna är ljuskällans.

En vägglampa är en pendel på en vägg (`Pendel.arm`): väggplattan i takkoppens ställe på väggens yta och en arm av
mässing längs väggens normal, med armaturen under armens ände (badrummets glob över tvättstället).

## Kontrollen

`./mod el kontroll` (fel stoppar, anmärkningar redovisas):

- referenserna: tändgrupper, styrda tändgrupper och rörens ändar finns, en brytare styr högst sina kanaler;
- styrningen: varje tändgrupp styrs av minst en brytare eller dimmer, och har lampor;
- armaturerna: vinkeln som ljuset ska vridas mot armaturens axel ryms i armaturens vridbarhet; inbyggnadsdjupet
  ryms i innertaket (gips och installationsskikt), och en armatur som inte får täckas med isolering har sin fria
  höjd och sin luft i läktens fack; hålet och drivdonet ligger inte på installationsskiktets läkt; pendlarna når ned
  (sladden minst 50 mm under takkoppen);
- rören: summan av böjarna mellan dosorna (mer än 270° är svårt att dra) och att varje punkt har ett rör;
- grupperna: varje apparat och dosa (utom lamporna, centralen och ingjutningsdosorna) i en grupp, ett rör från
  centralen till gruppens första punkt, gruppens punkter hopkopplade med rör, och högst tio uttag på en grupp 10 A;
- krockarna (modellen byggs): rören och dosorna mot armeringsjärnen och de andra installationerna är fel (köksfläktens
  uttag inne i den ihåliga skorstenskåpan redovisas), genomföringarna i stommen och skikten räknas.

Avståndet till brännbart material i ljusets riktning prövas mot husets ytor i `./mod kontroll` (installationernas
vägar, `kontrollregler.STRALAR`): inom det får ingen yta ligga framför den lysande ytan.

Elinstallationens delar ingår inte i modellens krockkontroll (`kontrollregler.UTOM_KONTROLL`): rören och dosorna går
genom skikten utan att andra delar får hål. De infällda armaturerna har sin håltagning (typens hål, så djupt som
armaturen går in) i de invändiga skikten (`installation.haltagningar`, skärs i hus.py), så att ljuset kommer ut.

## Ritningarna

`./mod el ritning` ritar serien E-01 i den gemensamma ritningsmallen (`beräkningar/ritningsmall`, A3, 1:75) på
planer ur modellens snitt (STEP-filen), med etiketterna där de inte täcker symboler eller andra etiketter:

- **E-01.1 elplanen** för plan 1: armaturer (infällda, på stam och pendlar), apparater och dosor med symboler
  (apparater intill varandra på samma vägg bredvid varandra med en gemensam etikett), tändgruppernas styrning
  (streckade bågar från brytaren till lamporna, färg per tändgrupp), rören i väggar och innertak, och tabeller över
  armaturerna och tändgrupperna;
- **E-01.2 rören i mellanbjälklaget**: de ingjutna rören med numrerade punkter och deras koordinater (K-05), var
  rören går upp i väggarna ovanför och ingjutningsdosorna, med plan 1:s väggar streckade;
- **E-01.3 förteckningen** över plan 1:s apparater och dosor och rören i väggar och innertak;
- **E-01.4 gruppförteckningen**: centralen och grupperna med säkring, faser, area, jordfelsskydd, punkter och rör.

`./mod el lista` skriver punktlistan, tändgrupperna och rörlistan med kontrollen (markdown och JSON).

## Ljusplaner

`./mod ljusplan` räknar belysningsstyrkan [lux] på vågräta mätytor ([`matytor.py`](matytor.py): golvet och
bordshöjden på plan 1, köksbänkarna och ön, källarens golv; ytor och delområden läggs till där) i renderingen, med
armaturernas uppmätta ljusfördelning och reflexerna i rummen, och ritar ljusplaner (U-04.n i ritningsmallen, alla
mätytorna i en pdf) med belysningsstyrkan i färg, isolinjer och medel-, minsta och största värde och jämnhet per rum och
delområde (utan inredningen på mätytan: skåpen, sängen och bänkskivorna, som lämnas vita). Ett delområde kan mätas
i en egen höjd: på planerna över plan 1 mäts köksbänkarna och ön där man arbetar, 10 mm över bänkskivorna (0,91 m):

```
./mod ljusplan plan1-golv kallare-golv              # alla tändgrupper och källarens taklampor tända, mörkt ute
./mod ljusplan plan1-bord --tand AL-T1 KO-T1=0.5    # bara några, en dimrad till hälften
./mod ljusplan plan1-bord --ljus 3 20 12:00 mulet --tand     # bara dagsljuset (inga lampor)
```

Flytta eller byt armaturer i rummens moduler och kör igen för att jämföra. Utredningen
[U-04](../../../../../beräkningar/U-04/) är ljusplanerna med all belysning tänd, med revision och datum, i
`rapporter/`; gör om den med `./bygg U-04` (i repots rot) när belysningen har ändrats.
