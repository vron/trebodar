# Dräneringen och dagvattnet

Dräneringen runt grunden och dagvattnet från stuprören som data i modellen: två skilda ledningar runt huset till en
ny brunn B1 utanför källarväggen V9, nära den gamla brunnen (som låg i väggen), ansluten till det befintliga utgående
röret Ø110 mot nordost (mot rampen in på tomten mellan boden och planteringen; överkant +5,759 vid brunnen, AR-02).
Samma data ger modellens geometri (rören och brunnarna i 3D), kontrollen och ritningen med höjderna. Ledningarna går i
marken och ingår inte i modellens krockkontroll; den egna kontrollen prövar dem mot husets delar och de andra
installationerna (marken, berget och fyllningen räknas inte).

```
cd verktyg/modellering
./mod dranering kontroll     # fallet, höjderna vid brunnen, brunnarnas djup och krockarna mot husets delar och de
                             # andra installationerna (utom marken; ledningarna i berget redovisas)
./mod dranering lista        # ledningarna med brytpunkternas höjder och brunnarna (ut/dranering/dranering.md)
./mod dranering ritning      # ritningen D-01 (ut/dranering/D-01 Dagvatten och dränering.pdf, kräver STEP-filen:
                             # ./mod bygg)
```

## Filerna

| Fil | Innehåll |
|---|---|
| [`ledningar.py`](ledningar.py) | Måtten, ringarna runt grunden, vattengångens höjder, stuprörens anslutningar, utloppet, brunnarna, kontrollen och utdraget för ritningen |
| [`dranering.py`](dranering.py) | Geometrin under `Hus/Installationer/Dränering`: rören som raka bitar längs vattengången och brunnarna som rör med botten |

Stuprörens lägen kommer ur taket (`../../tak/takkanter.py` och `../../tak/dalar.py`: `stupror`), grundens ytterkant ur
källarväggarna och plattan på mark (`../../grund`) och marken vid fasaderna ur `../../fasad/markniva.py`.

## Ledningarna

- **Dräneringen** (D1, D2): dränrör Ø110 i en ring `AVSTAND` 300 mm utanför grundens ytterkant, med överkanten i
  grundens underkant (källaren och plattan på mark, den närmaste), fall 1:200. Längs källaren begränsas fallet av det
  befintliga utgående röret: grenarna faller där så brant som det går och når brunnen `UTLOPP_MARGINAL` 20 mm över
  rörets inmätta vattengång (AR-02 räknar rörets höjd 20 mm högre för mätosäkerheten), minst `FALL_MIN` 1:400.
- **Dagvattnet** (S1, S2): täta rör Ø110 i en ring 600 mm utanför grunden, minst 300 mm under marken vid den
  närmaste fasaden (marken själv, `MARKEN`, utanför fasadstenen), fall minst 1:100. Varje stuprör ansluts (A-…) med
  en stuprörsanslutning med lövsil vid stuprörets ände, lodrätt ned och en sticka till ringen.
- Ringarna delas under altanen (`SPOLROR`, i det inre hörnet mellan 1NV och 2SV, där berget är sprängt) i två
  grenar som faller åt var sitt håll mot brunnen, med spolrör (D0, S0) där de börjar; spolrören och spolbrunnen där
  dräneringen faller till källaren nås genom altanen. Höjderna räknas så högt som möjligt och läggs sedan i raka
  lutningar mellan brytpunkterna (rören läggs i raka längder), högst `DJUPARE` under den högsta vattengången, så att
  schaktet bredvid grunden inte blir djupare än det behöver. Där grunden eller marken faller brantare än 1:1 faller
  ledningen lodrätt i en spolbrunn Ø200 (SB).
- I berget i dagen utanför altanen (`BERG`: kropp 1:s södra del, från entréavsatsen runt gaveln 1SV, efter
  Onshape-modellens berg) står inga spolbrunnar eller spolrör: där faller ledningarna högst 1:1, med böjar 45°, och
  spolas från spolrören. Kontrollen ger fel för en brunn eller ett spolrör där.
- Under stenarna i marken (`HINDER`: entréavsatsen och sovrumsavsatsen i `mark`, som huset inte får läsa) går
  ledningarna under stenarnas underkant, utan spolbrunnar och lodräta fall. Ändras stenarna syns det som krockar i
  kontrollen.
- **Brunnen** B1: Ø400 med sandfång 300 mm under utloppet och locket i marken; alla fyra grenarna går in över
  utloppet.

Altanens plintar (`../../altan/altan.py`) står fria från ledningarna: bärlinor som skulle gå längs ett schakt flyttas
ut ur det, plintarna flyttas längs bärlinorna och trappstegens bjälkar, och en plint som inte går att flytta fri
slutar över röret. Köldbärarledningarna (`../kollektor`) går under dräneringen där de korsar den.

## Kontrollen

`./mod dranering kontroll`: fallet i varje sträcka (dräneringen minst 1:200, längs källaren minst 1:400, dagvattnet
1:100), att grenarna når brunnen minst 20 mm över utloppet, dräneringens fall längs källaren per gren, brunnarnas djup
och stickornas täckning, och krockarna ur modellens geometri mot husets delar och de andra installationerna (fel).
Krockar med marken, fyllningen och berget räknas inte; ledningarna i berget (schakt i berg) redovisas som anmärkning.
