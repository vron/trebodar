# Ventilationen

Frånluften som data i modellen: var luften tas ut ur rummen, kanalernas väg genom huset, fläktarna och var luften
lämnar huset. Samma data ger modellens geometri (köksfläkten, donen, kanalerna, fläkten, gallren och takhuven i 3D),
genomföringarna genom husets delar, kontrollen och ventilationsritningarna. Ventilationen är fristående: den tar inga
hål i andra delar och ingår inte i modellens krockkontroll; den har en egen kontroll som redovisar genomföringarna
och krockarna mot husets delar.

```
cd verktyg/modellering
./mod ventilation kontroll     # kedjorna, flödena, genomföringarna och krockarna mot husets delar
./mod ventilation lista        # grenar, element, kanaler, genomföringar och krockar (ut/ventilation/)
./mod ventilation ritning      # ritningarna VL-01 (ut/ventilation/VL-01 Ventilation.pdf, kräver STEP-filen: ./mod bygg)
./mod rendera detalj-kallarkanal detalj-1c detalj-takhuv detalj-takflakt detalj-koket   # ventilationen i bild
```

## Filerna

| Fil | Innehåll |
|---|---|
| [`typer.py`](typer.py) | Produkttyperna: `Kanaltyp` (rund eller platt, med isolering), `Dontyp` (frånluftsdon), `Koksflakttyp` (med egen fläkt eller för en extern), `Vaggflakttyp`, `Kanalflakttyp`, `Overgangstyp` (rund–platt, rund–rund) och `Avluftstyp` (galler, takhuv, takfläkt) |
| [`katalog.py`](katalog.py) | Produkterna, tills vidare allmänna typer med vanliga mått och flöden (ej valda) |
| [`delar.py`](delar.py) | Grenen (`Gren`, också överluften mellan två rum) och dess element i luftens riktning: `Don`, `Kanal`, `Flakt`, `Overgang`, `Avluft`; hur kanalernas vägar följer av kedjan |
| `grenar/<gren>.py` | En gren: dess element, lägen och flöden |
| [`system.py`](system.py) | Allt ur grenarna (`MODULER`), genomföringarna, kontrollen och utdraget för ritningarna |
| [`ventilation.py`](ventilation.py) | Geometrin, ett montage per gren under `Hus/Installationer/Ventilation` |

Lägena på husets ytor är gemensamma med elen och vattnet: [`../montering.py`](../montering.py) (`vagg`, `utsida`,
`pa_tak`, `under_kallartak`, `angbromsen`), liksom genomföringarna ([`../genomforingar.py`](../genomforingar.py)). En
ny gren läggs till i `MODULER` i `system.py`.

## Begreppen

- **Gren** (`Gren`): en frånluft med egen fläkt, med id `FF<n>` (frånluftsfläkt), rummet och flödena (forcerat och
  grundflöde, l/s). Grenen är en kedja av element i luftens riktning, från donet i rummet till avluftsdonet ute.
- **Don** (`Don`): där luften tas ut, monterat på en yta: frånluftsdon, köksfläkt (kåpan på väggen, skorstenskåpan
  upp till innertaket) eller väggfläkt.
- **Kanal** (`Kanal`): från elementet före till elementet efter genom brytpunkterna (`via`); platta kanaler har sin
  bredd längs `bredd_langs`. Två kanaler i följd möts i den förstas sista brytpunkt (t.ex. kanalen i köksfläktens
  skorstenskåpa och genomföringen i väggen).
- **Kanalfläkt** (`Flakt`) och **övergång** (`Overgang`): med läge och luftens riktning.
- **Avluftsdon** (`Avluft`): galler på fasaden (`utsida`), takhuv på taket (`pa_tak`) eller takfläkt på en sockel i
  taket (`pa_tak`). Takfallens stålband (K-04) går inte över kanalerna till takhuvarna och takfläktarna.

Elementens id börjar med grenens: D don, K kanal, FL fläkt, O övergång, A avluftsdon (t.ex. `FF3-K2`).

## Grenarna

| Gren | Rum | Flöde | Väg |
|---|---|---|---|
| FF1 | Köket | 111 l/s forcerat (400 m³/h), 56 l/s normalt | Kåpan Fjäråskupan Carisma 70, vit, utan egen fläkt, mitt emellan fönstren 3NV-F4 och 3NV-F5, 650 över hällen; utloppet Ø150 upp i skorstenskåpan mot takbalksfackets mitt, genom innertaket och ångbromsen, och isolerad Ø200 lodrätt genom taket till takfläkten Systemair TFSR 200 EC Sileo på en sockel Ø300 i takplåten |
| FF2 | Badrummet | 15 l/s forcerat, 10 l/s grund (fuktstyrd) | Väggfläkt i gaveln 1NO mellan fönstret 1NO-F1 och väggen L9, 2 300 över golvet, röret genom väggen och galler |
| FF3 | Stora källarrummet (under högra huskroppen) | 10 l/s, 5 l/s grund | Frånluftsdon och kanalfläkt under källarens tak; kanalen Ø100 lodrätt genom mellanbjälklaget och upp i kökets inbyggnad, i skafferiets inre hörn mot L4 och L18; över innertaket isolerad mellan takbalkarna och ut genom en takhuv på takfallet 3NV |
| FF4 | Tvättstugan (under hallen och badrummet) | 15 l/s forcerat (fuktstyrd), 5 l/s grund | Frånluftsdon och kanalfläkt under källarens tak; kanalen Ø100 lodrätt genom mellanbjälklaget och upp längst in i hörnet i hallens garderob, mot 1A och 1B; över innertaket isolerad och ut genom en takhuv på takfallet 1SO |
| OL1 | Källarrummet (mellan V19/V20, V2, V15 och V4–V6) | överluft, 5 l/s | Överluftsöppning Ø100 genom källarväggen V15, med don och galler: rummets luft går ut i det stora rummet och vidare till FF3 |

Kanalerna från källaren går lodrätt och syns på plan 1 bara inne i skafferiet och i hallens garderob (#134, #136).
En överluft (`Gren(..., overluft=True)`) har ingen fläkt, och dess flöde räknas inte till frånluften. Källarens
fläktar ansluts på väggen mitt för fläkten (elen: KA-D6 på V14 och KA-D7 på V21).

## Genomföringarna och kontrollen

`./mod ventilation kontroll` (fel stoppar, anmärkningar redovisas):

- kedjorna (don först, avluftsdon sist, en fläkt per gren) och anslutningarnas storlekar;
- fläkten klarar grenens flöde; lufthastigheten i kanalerna (anmärkning över 5 m/s, fel över 7 m/s) och kanalernas
  tryckfall ungefär (friktion och böjar);
- genomföringarna ur husets geometri: ursparingar i mellanbjälklaget (före gjutningen, R-06), kärnborrning i
  källarväggarna, väggenomföringar (i våtrum tätas tätskiktet), kanaler i väggarnas regelfack (som ska rymmas i
  stommen; syll och hammarband urtas), genomföringar i innertaket (ångbromsen tätas) och i taket (takhuven), och att
  kanalerna mellan takbalkarna går fria från dem;
- kalla delar: kanaler genom ytterväggen och takets isolering ska vara isolerade (kondens);
- helheten: ersättningsluften genom ventilerna i VELFAC-fönstrens överkarm (`katalog.UTELUFT_FONSTER`) och två väggventiler Ø100 (`grenar/uteluft.py`: uteluftsdon utan fläkt, `Gren.uteluft`, #108): undertrycket normalt och med köksfläkten forcerad, där mer än 10 Pa är accepterat; avluft nära öppningsbara fönster och
  takhuvar nära nock och dal;
- krockar ur modellens geometri mot husets delar: stommens delar (virke, läkt, limträ, stål) var för sig och
  genomföringarna i skikten (betong, armering, isolering, skivor, fasad, tak) per element; och mot elen, tappvattnet
  och teknikrummets utrustning (fel).

## Ritningarna

`./mod ventilation ritning` ritar serien VL-01 i den gemensamma ritningsmallen (`beräkningar/ritningsmall`, A3):

- **VL-01.1 plan 1** och **VL-01.2 källaren** (1:75): kanalerna med frånluft i skala, lodräta kanaler genom
  bjälklaget, donen, fläktarna, avluftsdonen och flödena, med tabeller över grenarna, kanalerna och produkterna;
- **VL-01.3 och VL-01.4 sektionerna** (1:50) längs det stora rummets och tvättstugans kanaler upp till takhuvarna, med genomföringarna och
  deras mått, och tabellen över alla genomföringar.
