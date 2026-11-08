# Elinstallationen

Belysning, apparater, dosor och rör som data i modellen: var punkterna sitter, vad de är för produkter, vilka
lampor som tänds tillsammans och från vilka brytare, och hur rören går i bjälklag, väggar och innertak. Samma data
ger modellens geometri (armaturer, apparater, dosor och rör i 3D), renderingens ljus (armaturernas uppmätta
ljusfördelning), kontrollerna och elritningarna.

```
cd verktyg/modellering
./mod el kontroll     # referenser, styrning, armaturerna, rörens böjar och anslutningar, grupperna och krockarna
./mod el lista        # punkter, tändgrupper och rör (ut/el/elinstallation.md och .json)
./mod el ritning      # elritningarna E-01.1–E-01.6 (ut/el/E-01 Elinstallation.pdf, kräver STEP-filen: ./mod bygg)
./mod el hamta        # tillverkarnas fotometrifiler som saknas (till lokalt/el/, versionshanteras inte)
./mod rendera I02 --ljus 12 21 18:00 sol --tand AL-T1 AL-T2=0.5     # kväll, tändgrupperna tända (dimrad)
./mod rendera detalj-ph5 detalj-stav detalj-vl45 detalj-glob         # pendlarna på nära håll, kväll och tända
```

## Filerna

| Fil | Innehåll |
|---|---|
| [`typer.py`](typer.py) | Produkttyperna: `Armaturtyp` (tillverkarens data, mått, fotometrifil; `Tubhuvud` för spotar på stam, `Pendel` för pendlar, `Linjeprofil` för ljuslinjer), `Apparattyp` (brytare, dimrar, uttag; dimrarnas last), `Drivdonstyp` (24 V-drivdonen), `Dosatyp`, `Rortyp` |
| [`katalog.py`](katalog.py) | Produkterna: armaturerna (SG Armaturen Junistar Exclusive 903201, infälld; Tube Mini R 320696, tub på stam; pendlarna Louis Poulsen PH 5 och VL45 Radiohus Ø175, Ø250 och Ø370, Konsthantverk Stav och en glob i opalglas; en vägglampa med glob på arm; LEDVANCE PANEL COMPACT 600, utanpåliggande panel på betong med en ingjuten dosa ovanför; ljuslinjerna i ask, `ljuslinje(längd)` med profilen `ASKPROFIL`, egen tillverkning), drivdonet för ljuslinjerna (Hide-a-lite LED-dimtrafo FDIM 24V 60W, förslag), LED-dimrarna (Schneider Exxact, förslag) och tills vidare allmänna dosor, apparater och rör |
| [`punkter.py`](punkter.py) | Beståndsdelarna (`Lampa`, `Apparat`, `Dosa`, `Tandgrupp`, `Ror`, `Rum`), riktningarna (`mot` en punkt, `lutad` mot en vägg), uttag ovanför fönster (`ovan_fonstret`) och pendelns sladd (`pendeln`); lägena på husets ytor (`tak`, `kallartak`, `vagg` och rörens brytpunkter `i_tak`, `i_vagg`, `vid_tak`, `i_bjalklag`) i installationernas gemensamma [`../montering.py`](../montering.py) |
| [`lakt.py`](lakt.py) | Innertakets läkt ur innertakets geometri: `mellan_lakten` flyttar en armatur mitt emellan läkten |
| `rum/<rum>.py` | Ett rum: dess punkter, tändgrupper och rören i rummets väggar och innertak. Plan 1 efter belysningsplanen (ärende #8): allrum, kök, gång, hall, vardagsrum, sovrum, kontor, sovrum och kontor i högra huskroppen, gästrum; badrummet (ärende #52); i källaren teknikrummet (centralen och värmepumpen) och källarens övriga rum ([`rum/kallare.py`](rum/kallare.py), #51: ljuslinjerna, dimrarna, rören och 24 V-kretsarna; punkterna, rummen, panelerna, brytarna och uttagen i [`rum/kallarens_punkter.py`](rum/kallarens_punkter.py)) |
| `bjalklag/<bjälklag>.py` | Rören ingjutna i ett bjälklag: kartorna och vägarna (`ingjutna.py`, på [`../plattan.py`](../plattan.py)), gruppernas rör från centralen i knippen (mellanbjälklaget) och brandlarmets matningsdosa |
| [`grupper.py`](grupper.py) | Gruppcentralen och grupperna: säkring, faser, ledarnas area, jordfelsskydd och punkterna i rörens ordning |
| [`kedjor.py`](kedjor.py) | Rören mellan gruppernas punkter: genom innertaket, längs väggarna och genom bjälklaget |
| [`dragning.py`](dragning.py) | Rörens vägar: genom innertaket, i väggen och upp ur bjälklaget mellan järnen |
| [`matytor.py`](matytor.py) | Mätytorna för ljusplanerna (`./mod ljusplan`): vågräta ytor med höjd, område, rutnät och delområden |
| [`installation.py`](installation.py) | Allt ur modulerna (`MODULER`), 24 V-kretsarna (`kretsresultat`: last, ledarnas area, spänningsfall), kontrollen och utdraget för ritningarna och renderingen |
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
  (`i_bjalklag`). Rörets ändar är punkternas anslutningar: drivdonet bredvid armaturen, dosans mitt och
  ljuslinjens rörände i taket under profilens ände. Rören har sitt innehåll (`slag`): 230 V, 230 V dimrad (den
  dimrade fasen från en dimmer till drivdonen) eller 24 V.
- **Grupperna** ([`grupper.py`](grupper.py), #50, #51): gruppcentralen sitter i teknikrummet i källaren på V3 väster
  om vattenmätaren (`../teknikrum.GRUPPCENTRAL`, punkten `GC` i [`rum/teknikrum.py`](rum/teknikrum.py)), med
  huvudbrytare, överspänningsskydd och en personskyddsautomat (typ A 30 mA) per grupp. Varje grupp har sina punkter
  (apparater och dosor, lamporna matas genom brytarna) i rörens ordning: ett rör från centralen till den första
  ([`bjalklag/mellanbjalklag.py`](bjalklag/mellanbjalklag.py), `Gnn-M`, ingjutet i mellanbjälklaget) och därifrån rör
  mellan punkterna ([`kedjor.py`](kedjor.py), `Gnn-Rn`): i väggarna och innertaket, förgrenat i apparatdosorna.
- **Rören i mellanbjälklaget** (#87): raka och sneda direkt från punkt till punkt, med mjuka böjar med stor radie
  (upp till 600 mm) runt det de inte får gå genom, inga räta vinklar i plattan
  ([`../plattan.py`](../plattan.py), [`bjalklag/ingjutna.py`](bjalklag/ingjutna.py)). Två nivåer
  (`../montering.BJALKLAG`): plan 1:s klena rör (Ø16) i den övre, över tappvattnet och golvvärmen, och hällens (Ø20)
  och källarens i den undre, runt tappvattnets och avloppets rör. Rören går utanför pelarnas kontrollsnitt för
  genomstansning (2d) och helst utanför genomstansningszonen (6d), genom banden av vinkeljärn vid väggarna bara mellan
  järnen, mellan källarväggarnas lodräta järn och runt allt som går lodrätt genom nivån (andra rörs stigare, hylsor,
  ventilationen, golvbrunnen). De dras i tur och ordning och går helst inte genom de rör som redan är dragna: korsar
  två ändå varandra i samma nivå går det ena under (den övre nivån) eller över (den undre) det andra i en kort svacka.
  Nivån byts och rören korsar varandra inte i golvvärmens stråk (golvvärmens slingor går runt svackorna och ramperna,
  stråken ligger fast). Gruppernas rör från centralen går upp ur dess ovansida i två rader mellan underkantsnätets järn
  (den bakre i V3:s cellplast) och i knippen åt var sitt håll, rakt ut ur bandet över V3 och vidare som ett brett rör
  med en fil per rör ([`bjalklag/mellanbjalklag.py`](bjalklag/mellanbjalklag.py)); varje rör lämnar sitt knippe i en
  mjuk båge snett mot sin punkt, det som lämnar först ytterst, så att rören inte korsar varandra. Källarens grupper
  G17, G18 och G24 går i samma knippen ([`rum/kallarens_punkter.py`](rum/kallarens_punkter.py), `FRAN_CENTRALEN`).
  Rören går upp i väggarnas regelfack eller ytterväggarnas installationsskikt mellan överkantsnätets järn
  ([`dragning.py`](dragning.py)). Där ett av källarens rör ändå fick långt över 270° böjar går det genom en
  **dragdosa**: en ingjuten dosa i källarens tak, åtkomlig underifrån, där dess svängar delas lika (`DRAGDOSOR` i
  [`rum/kallare.py`](rum/kallare.py)): KA-D3 i KA-R6-3, KA-D4 i G24-R1 och KA-D5 i G18-R3 (rören a och b).
- **Dragdosor i innertaket** ([`kedjor.py`](kedjor.py), #87): ett rör mellan två punkter genom innertaket som får
  mer än 270° böjar delas i en dragdosa i innertaket (`DRAGDOSA_TAK`, infälld i gipsen med vitt blindlock, mitt i
  läktens fack), i den brytpunkt där böjarna delas jämnast, och vid behov igen; dosorna heter efter rummet vid den
  närmaste änden (t.ex. BA-DD1), två rör nära varandra delar dosa, och rörens delar heter a, b, c … i ordning.
  Böjarna räknas i `punkter.bojar`: rörets ände i en dosa (högst 100 mm från dosans mitt) räknas som en kort S-böj in
  genom dosans hål, inte som en rät böj.
- **Källarens arbetsrum** ([`rum/kallare.py`](rum/kallare.py), #51): paneler som ansluts i ingjutna dosor ovanför sig
  (mellan underkantsnätets järn, fria från rören i bjälklaget och pelarnas genomstansningszoner). Rören från brytarna
  går rakt upp ur dosorna i KL-väggarnas regelfack in i bjälklaget, helst i dess undre nivå (under plan 1:s rör), och in
  i en ingjuten dosa från sidan i den undre nivån. Det stora rummets grupp (G17) kommer från den bakre raden över
  centralen till en ingjuten kopplingsdosa i rummets tak (KA-D1), och därifrån till brytaren och panelerna. De små
  rummens grupp (G18) kommer från den främre raden och går ned i KL1, och fortsätter till dimrarna i de trevliga rummen.
- **Källarens trevliga rum** ([`rum/kallare.py`](rum/kallare.py), #51): trapphallen, tvättstugan, de två små rummen
  söder om V4–V6 och rummet norr om trapphallen har ljuslinjer i ask utanpå betongtaket (egen tillverkning, se
  Armaturerna), parallella med väggarna och efter hur rummen används: längs trapphallen och en tvärs ned mot trappans
  fot, längs tvättstugans hall och en över bänken vid V21, en mitt i var och en av de två delarna söder om V4–V6 och
  två parallella i rummet norr om trapphallen. Ingen dosa i taket: 24 V går i egna ingjutna rör (skilda från 230 V)
  som slutar i taket under profilens ände, pluggade och tätade vid gjutningen och täckta av armaturen, och ledaren
  går genom profilen till nästa linje. Drivdonen (24 V CV, fasdimbara med bakkant, ett per tändgrupp) sitter samlade
  och åtkomliga i drivdonsskåpet TK-LC på KL8 i teknikrummet (`../teknikrum.DRIVDONSSKAP`); vanliga vriddimrar vid
  ingångarna dimrar dem, och den dimrade fasen går i ett eget rör från varje dimmer till skåpet. Skåpet sitter öster om
  pelaren P4 i KL8, så att rören går upp ur dess ovansida i en rad (detaljen på AR-03.1) utanför pelarens
  kontrollsnitt; därifrån går de i knippen i bjälklagets undre nivå, norrut och söderut ur raden mot sina punkter.
  Knippena dras först, sedan G18:s rör mellan dimrarna, helst i den övre nivån (över knippena), och rören mellan
  ljuslinjerna. Dimrarna KA-B1 och KA-B4 på KL4 sitter så långt från pelarna P12 och P11 att deras rör går in i
  bjälklaget utanför kontrollsnitten; KA-B6 på KL1 och KA-B2 på KL3 sitter mellan sin dörr och en pelare (P8, P10),
  så att deras rör går in i bjälklaget innanför kontrollsnittet och leds rakt ut ur det.
- **24 V-kretsarna** (`KRETSAR` i [`rum/kallare.py`](rum/kallare.py), `Krets`): en per tändgrupp, med drivdonet i
  skåpet, dimmerns kanal och ljuslinjerna. `Installation.kretsresultat` räknar lasten, rören från drivdonet som ett
  träd (från skåpet till en ljuslinjes rörände och vidare, med ledaren genom profilerna), spänningsfallet till varje
  ljuslinje (koppar 0,0183 Ω mm²/m, kabeln 300 mm längre än röret i varje ände) och väljer den minsta arean (1,5 eller
  2,5 mm²) som håller det under 3 %; resultatet står på E-01.6.
- **Källarens uttag** ([`rum/kallare.py`](rum/kallare.py), [`rum/teknikrum.py`](rum/teknikrum.py), #51): i alla
  rum, tvättmaskinen och torktumlaren i tvättstugan och fläkten FF3:s anslutning. Rören går i källarväggarnas cellplast
  bakom gipsen och i KL-väggarnas regelfack, vågrätt i golvzonen (250 mm över golvet, under tappställenas rör) och upp
  eller ned till uttagen; de flesta grupperna kommer ur centralens baksida (`teknikrum.bakifran`), det stora rummets
  och fläktens (G24) genom bjälklaget till V20.

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
(`Tubhuvud`: en tub på en stam från frontplattan, som Tube Mini R, vridbar kring stammen och lutbar i leden), är
pendlar (`Pendel`, nedan) eller ljuslinjer (`Linjeprofil`, nedan).
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

### Ljuslinjerna

En ljuslinje (`ljuslinje(längd)` i [`katalog.py`](katalog.py), profilen `ASKPROFIL`) är en profil i ask 56 × 22 med
fasade undre långkanter, utanpå betongtaket, med ett spår underifrån som slutar 40 mm från ändarna. I spåret sitter
en aluminiumkanal (leder bort värmen), en COB-LED-list 24 V (ingen prickighet, Ra ≥ 97, R9 > 90, 3000 K, cirka 8 W/m)
och en opal diffusor (PC eller PMMA) klippt i kanalen. Den lysande längden är en multipel av 150 mm. Lampans läge är
profilens mitt och `langs` profilens riktning från matningens ände; `punkter.linjen` ger den lysande linjens ändar på
diffusorn, `punkter.rorande` rörändarna. Geometrin ([`el.py`](el.py)): askprofilen med spåret, kanalen, listen och
diffusorn, som lyser i renderingen. Där blir linjen ett rektangulärt ytljus med diffusorns bredd och den lysande
längden (lambertskt), med 560 lm per meter lysande längd: listens cirka 800 lm/m, varav 70 % antas komma ut genom
kanalen och diffusorn.

## Kontrollen

`./mod el kontroll` (fel stoppar, anmärkningar redovisas):

- referenserna: tändgrupper, styrda tändgrupper och rörens ändar finns, en brytare styr högst sina kanaler;
- styrningen: varje tändgrupp styrs av minst en brytare eller dimmer, och har lampor;
- armaturerna: vinkeln som ljuset ska vridas mot armaturens axel ryms i armaturens vridbarhet; inbyggnadsdjupet
  ryms i innertaket (gips och installationsskikt), och en armatur som inte får täckas med isolering har sin fria
  höjd och sin luft i läktens fack; hålet och drivdonet ligger inte på installationsskiktets läkt; pendlarna når ned
  (sladden minst 50 mm under takkoppen);
- rören: summan av böjarna mellan dosorna, där röret går upp eller ned ur bjälklaget, in i en vägg, centralen eller en
  dosa och skarpare hörn (mer än 270° är svårt att dra), och för sig de mjuka svepen i bjälklaget (radie minst 300 mm,
  `installation.MJUK_RADIE`; anmärkning över 270°), och att varje punkt har ett rör;
- rören i bjälklaget: att de inte går i varandra (mittlinjerna i 3D minst radierna isär, utom där två rör möts i
  samma dosa) eller genom en armaturs ingjutna dosa;
- grupperna: varje apparat och dosa (utom lamporna, centralen och ingjutningsdosorna) i en grupp, ett rör från
  centralen till gruppens första punkt, gruppens punkter hopkopplade med rör, och högst tio uttag på en grupp 10 A;
- krockarna (modellen byggs): rören och dosorna mot armeringsjärnen och de andra installationerna är fel (köksfläktens
  uttag inne i den ihåliga skorstenskåpan redovisas), genomföringarna i stommen och skikten räknas;
- ljuslinjerna och 24 V-kretsarna: varje ljuslinje i en krets och nådd med 24 V-rör från drivdonet, drivdonen i
  skåpet (ett per krets) och lasten inom drivdonets område (anmärkning över 80 %), dimmerns kanal styr tändgruppen
  och har ett eget rör med den dimrade fasen till skåpet, dimmerns last per kanal inom dess område, rörens ändar i
  taket under profilen och spänningsfallet högst 3 %.

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
- **E-01.2 rören i mellanbjälklaget**: de ingjutna rören med de mjuka böjarna och brytpunkterna numrerade, var rören
  går upp i väggarna ovanför, ingjutningsdosorna och ljuslinjernas rörändar i källarens tak, med plan 1:s väggar
  streckade, och rörens innehåll (230 V, dimrad, 24 V med ledarna), böjar och svep;
- **E-01.3 förteckningen** över plan 1:s apparater och dosor och rören i väggar och innertak;
- **E-01.4 gruppförteckningen**: centralen och grupperna med säkring, faser, area, jordfelsskydd, punkter och rör;
- **E-01.5 rörens punkter** i mellanbjälklaget, numrerade som på E-01.2: brytpunkterna (där rörets raka sträckor
  möts) med koordinaterna (K-05) och böjarnas radier;
- **E-01.6 källarens elplan**: armaturerna (ljuslinjerna i sin längd med rörändarna), apparaterna och dosorna,
  drivdonsskåpet, tändgruppernas styrning och rören i väggarna (rören i bjälklaget på E-01.2), och drivdonen och
  24 V-kretsarna med last, ledare, kabellängd och spänningsfall.

`./mod el lista` skriver punktlistan, tändgrupperna och rörlistan med kontrollen (markdown och JSON).

## Ljusplaner

`./mod ljusplan` räknar belysningsstyrkan [lux] på vågräta mätytor ([`matytor.py`](matytor.py): golvet och
bordshöjden på plan 1, köksbänkarna och ön, källarens golv; ytor och delområden läggs till där) i renderingen, med
armaturernas uppmätta ljusfördelning och reflexerna i rummen, och ritar ljusplaner (U-04.n i ritningsmallen, alla
mätytorna i en pdf) med belysningsstyrkan i färg, isolinjer och medel-, minsta och största värde och jämnhet per rum och
delområde (utan inredningen på mätytan: skåpen, sängen, bänkskivorna, källartrappan och källarens pelare, som lämnas vita; rummens namn ur
`RUMSNAMN` och `LJUSPLANENS_RUM` i `modeller/trebodar/vyer.py`, där källarens rum står). Ett delområde kan mätas
i en egen höjd: på planerna över plan 1 mäts köksbänkarna och ön där man arbetar, 10 mm över bänkskivorna (0,91 m),
och i källaren tvättbänken längs V21 (0,9 m):

```
./mod ljusplan plan1-golv kallare-golv              # alla tändgrupper tända, mörkt ute
./mod ljusplan plan1-bord --tand AL-T1 KO-T1=0.5    # bara några, en dimrad till hälften
./mod ljusplan plan1-bord --ljus 3 20 12:00 mulet --tand     # bara dagsljuset (inga lampor)
```

Flytta eller byt armaturer i rummens moduler och kör igen för att jämföra. Utredningen
[U-04](../../../../../beräkningar/U-04/) är ljusplanerna med all belysning tänd, med revision och datum, i
`rapporter/`; gör om den med `./bygg U-04` (i repots rot) när belysningen har ändrats.
