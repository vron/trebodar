# Golvvärmen

Golvvärmen som data i modellen: zonerna med en slinga var, tilloppen från fördelarna, fördelarna på V5 i källaren och
matarledningarna från värmepumpen. Plan 1:s slingor gjuts in i mellanbjälklaget ovanför tappvattnets rör, källarens
i bottenplattan. Samma data ger modellens geometri (rören och fördelarna i 3D), genomföringarna, kontrollen och
golvvärmeritningarna. Golvvärmen är fristående: den tar inga hål i andra delar och ingår inte i modellens
krockkontroll; den har en egen kontroll som redovisar genomföringarna och krockarna mot husets delar och de andra
installationerna.

```
cd verktyg/modellering
./mod golvvarme kontroll     # slingornas längd, fördelarna, rören i varandra och mot järnen, genomföringarna och
                             # krockarna mot husets delar och de andra installationerna
./mod golvvarme lista        # kretsar, fördelare och genomföringar (ut/golvvarme/)
./mod golvvarme ritning      # ritningarna VV-01 (ut/golvvarme/VV-01 Golvvärme.pdf, kräver STEP-filen: ./mod bygg)
```

## Filerna

| Fil | Innehåll |
|---|---|
| [`typer.py`](typer.py) | Produkttyperna: `Rortyp` (diameter, godstjocklek, slingans längsta längd) och `Fordelartyp` (högst antal kretsar) |
| [`katalog.py`](katalog.py) | Produkterna, tills vidare allmänna typer med vanliga mått (ej valda) |
| [`punkter.py`](punkter.py) | Zon, fördelare och hur slingan läggs (`slinga`), avstånden (`FIL`, `MARGINAL`, `FRITT`, `JARN`) |
| [`plan1.py`](plan1.py) | Plan 1: zonerna, stråken och fördelarens läge (FD1) |
| [`kallare.py`](kallare.py) | Källaren: zonerna, stråken och fördelarens läge (FD0) |
| [`system.py`](system.py) | Golvet, hindren, slingorna och tilloppen ur zonerna, matarledningarna, kontrollen, genomföringarna och utdraget för ritningarna |
| [`golvvarme.py`](golvvarme.py) | Geometrin under `Hus/Installationer/Golvvärme`: en del per krets (röret svept längs vägen), fördelarna och matarledningarna |

Stråken i betongen ([`../strak.py`](../strak.py): `Strak`, `vag`, `filer`, `glipa`) är gemensamma med tappvattnet,
liksom nivåerna i betongen (`I_BETONGEN` i [`../montering.py`](../montering.py)) och genomföringarna
([`../genomforingar.py`](../genomforingar.py)). Järnen som går genom rörens nivå läses ur armeringen
(`jarnen_i_nivan` i [`../../armering/armering.py`](../../armering/armering.py)).

## Begreppen

- **Zon** (`Zon`): en uppvärmd yta med en slinga, med id per våning (`AR`, `KM1` …): en rektangel eller polygon som
  skärs med golvet, rördelningen `cc`, radernas riktning (`x` eller `y`), hörnet där slingan börjar (`start`) och
  stråket som tilloppen kommer i. Kretsen heter `GV<våning>-<zon>` (våning 1 plan 1, 0 källaren). Zonernas och
  stråkens id (`HN`, `KS`, `ÖN` …) är koder, inte väderstreck; texterna följer planens (norr = lågt y).
- **Slinga** (`slinga`): dubbelslinga i meander, framledningen och returen bredvid varandra cc isär och raderna 2·cc
  isär, från raden närmast `start`; framledningen går ut till vändpunkten och returen tillbaka.
- **Fördelare** (`Fordelare`): framledningens och returens stammar (FD1 plan 1, FD0 källaren) på V5:s norra sida,
  med utgångarna i rörens filer, c/c 50.
- **Stråk** (`Strak`): en gemensam väg från fördelaren med en fil per rör; filerna c/c 50.

## Dragningen

- Zonens yta är zonen på golvet (mellanbjälklaget utan plan 1:s väggar, trapphålet och kaminen; bottenplattan utan
  källarväggarna, källarens innerväggar KL1–KL10 och trappan), 150 mm (`MARGINAL`) från väggar och från zonens
  kanter, utan tilloppen och det som ska
  hållas fritt: järnen som går genom rörens nivå (`JARN`), tappvattnets rör upp ur bjälklaget, elens rör där de går
  genom rörens nivå (lodrätt, där de byter nivå och där de går under eller över ett annat rör) och avloppets rör och
  golvbrunn genom det (`FRITT`), och på källarens golv värmepumpen och servisen. Där en slinga skulle gå genom ett
  sådant hål mitt i zonen förlängs hålet längs raderna till zonens kant, så att raderna slutar vid det. Elrören byter
  inte nivå och korsar inte varandra i tilloppens stråk (`el/bjalklag/ingjutna.golvvarmens_strak`).
- Järnen i rörens nivå: källarväggarnas lodräta järn når upp i mellanbjälklaget (R-05) och delar plan 1:s golv i delar
  (allrummet söder om V4–V6, hallen och vardagsrummet söder om V3, resten); balkarnas överkantsjärn under V4–V6, V15 och
  V19 ligger i bottenplattans rörnivå (R-04), så källarrummet söder om V4–V6 värms inte. Slingorna stannar i sin del;
  stråken går över väggarnas järn i dörröppningarna eller mitt i en glipa mellan två järn (`glipa`).
- I källaren har varje rum sin slinga (det stora rummet tre), och stråken går genom innerväggarnas dörröppningar;
  trapphallen, där fördelarna sitter, värms av tilloppen.
- Rören går upp (FD1) eller ned (FD0) i betongen mellan armeringsnätets järn: utgångarna c/c 50 mitt för nätets
  maskor (s150), stammarna där deras rader ligger mellan nätets järn.
- Tilloppen går norrut från fördelaren och viker av i ordning: de som viker av först västerut eller österut närmast
  väggen, och i ett stråk det rör som viker av först ytterst mot sin sida. Zonernas ordning i `ZONER` är filernas
  ordning längs fördelaren. Röret lämnar sin fil vinkelrätt mot slingans början, så slingans rader går vinkelrätt mot
  stråkets sista sträcka; kontrollen visar rör som går i varandra.
- Matarledningarna går under källarens tak från värmepumpens anslutningar genom KL10, hallen och KL3 (norr om
  dörren KD2) till FD1:s västra ände; FD0 matas från FD1:s östra ände.

En zon flyttas eller delas i `plan1.py` eller `kallare.py` (rektangeln skärs med golvet, så små ändringar av väggarna
följer med). En ny zon läggs i `ZONER` i fördelarens ordning, med ett stråk som når den.

## Kontrollen

`./mod golvvarme kontroll` (fel stoppar, anmärkningar redovisas):

- zonerna: en slinga i varje zon;
- kretsarna: längden med tilloppen högst rörets längsta (90 m), anmärkning på korta kretsar (injusteras);
- fördelarna: högst fördelarens antal kretsar;
- rören i betongen: i varandra eller i sig själva (i plan, i samma nivå) och mot järnen som går genom nivån;
- genomföringarna ur husets geometri: rören upp ur bjälklagets underkant och ned i bottenplattans överkant vid
  fördelarna;
- krockar ur modellens geometri mot husets delar (stommen och armeringen var för sig, skikten per krets) och mot elen,
  ventilationen, tappvattnet och teknikrummets utrustning (fel).

## Ritningarna

`./mod golvvarme ritning` ritar serien VV-01 i den gemensamma ritningsmallen (`beräkningar/ritningsmall`, A3):

- **VV-01.1 plan 1 och källaren** (1:100): kretsarna i mellanbjälklaget och bottenplattan med zonerna, tilloppen och
  järnen i rörens nivå; tabeller över kretsarna;
- **VV-01.2 fördelarna** (1:20): planen och vyn mot V5 med stammarna, rören upp och ned i betongen och
  matarledningarna; tabeller över fördelarna, matarledningarna och genomföringarna;
- **VV-01.3 köldbärarledningarna** (1:100): planen och sektionen längs skyddsrören till energibrunnen
  (`../kollektor/`).
