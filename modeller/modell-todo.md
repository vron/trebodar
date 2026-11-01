# Att ändra i modellen

Det som ska ändras i modellen (`modeller/trebodar`) för att den ska stämma med handlingarna. Punkterna tas bort när ändringen finns i modellen.

**Hitta platsen.** Lägen anges i K-05:s koordinater (x, y från skärningen mellan mellanbjälklagets kanter, z från bjälklagets överkant), samma som modellens. Delarnas namn är modellens (Onshape-modellens namn finns i `modeller/referens/namntabell.csv`).

**När modellen är uppdaterad:** kör `./mod kontroll` i `verktyg/modellering` och kontrollerna i `verktyg/modellanalys`. Beräkningarna läser inte modellen; där handlingarna ska följa ändringen rättas deras källfiler för hand, och sedan körs K-03, K-05, K-06, R-04, R-05, R-06 och R-03.

## Kontrollera och bestäm

1. **Stolparnas lägen under nockbalk 1 mot K-01.**

    | Stöd | K-01 | Modellen |
    |---|---|---|
    | B | y 2 870 | LN1_1 vid 2 795 |
    | C | y 4 770 | LN1_2 vid 4 686 |
    | D | y 6 670 | huvudstolpen vid 6 602 |

    Skillnaden är 68–84 mm. Antingen flyttas stolparna, eller så räknas K-01 om med modellens lägen; säg till vilket.

2. **Innerväggarna 1A och 1C mot planritning 201 rev 02.** Planritningen (badrum, hall och kök uppdaterade) visar
   väggen mellan badrummet och garderoben vid y ≈ 7 260–7 345 och väggen söder om duschen vid y ≈ 8 300–8 456, alltså
   150–200 mm längre åt SV än de bärande väggarna 1A (y 7 115–7 185) och 1C (y 8 185–8 255) i modellen. 1B och 1D
   stämmer inom 10–30 mm (planritningens noggrannhet). Flyttas 1A och 1C ändras K-03 och K-05; säg till om
   planritningen eller modellen gäller.

3. **Marken mot källarväggarna.** Glipor mellan fyllning och berg vid V2 (y 10 865, x 4 545–9 645) och V16 (x 9 645, y 10 865–12 365). Ingen mark vid V9 (y 1 145, x 11 240–13 665) och V17 (x 9 165, y 145–1 145). Modellera marken där; fyllnadshöjderna i K-06 kontrolleras mot den.

4. **Plattan på mark.** AR-02 har L-element 500 med ytterkanten i väggarnas ytterliv och L-elementens och
   cellplastens underkant 500 under plattans överkant (+8,000); modellen har som K-06, R-05 och R-03 400 mm cellplast
   under plattan (underkant −550) på fyllning. Uppdatera handlingarna och modellen tillsammans.

## Saknas i modellen

5. **Lätta innerväggar enligt planritning 201 rev 02.** Bara syllarna finns (`Syllar lätta väggar`, Onshape-modellens
   läge, och stolparnas syllar `LN1_2-S01` och `LN1_3-S01`, som ligger under lätta väggar mellan rummen i höger
   huskropp). Modellera dem som regelväggar 45×70 med gips 2 × 12,5 på båda sidor (120 mm, som i planritningen),
   upp till innertaket. Gipsen på de bärande innerväggarna (1A–1D, 2A–2C) saknas också och byggs på samma sätt.
   Att bestämma först:
    - badrummets, garderobens och hallens väggar hänger ihop med punkt 2;
    - dörrarna: planritningen har skjutdörrar till sovrummet och de två kontoren i höger huskropp och en dörr 900 till
      badrummet, på andra ställen än innerdörrarna i modellen (kontoret y ≈ 3 030–3 810 mot ID3 3 671–4 651,
      kontoret/gästrummet y ≈ 4 760–5 680 mot ID4 5 562–6 542, sovrummet x ≈ 10 070–10 940 mot ID5 10 565–11 545,
      badrummet y ≈ 6 110–7 035 mot ID1 7 055–8 035);
    - väggen mellan kontoret/gästrummet och köket gör i planritningen ett hopp (y ≈ 6 540–6 680 vid 3NV,
      y ≈ 6 680–6 800 mot korridoren), så att huvudstolpen LN1_3 (y 6 542–6 662) hamnar utanför väggen.
6. **Toppklossar på gavelstolarna.** Balken slutar i gavelväggens utsida, så gavelstolarna har bara en kloss, på insidan, och balken vilar på 90 mm (45 + 45) i stället för 135 mm. Kontrollera i K-03 eller ändra detaljen.
7. **Takutsprång.** Planritning 201 visar takutstick 100 runt hela huset. I modellen slutar takets skikt i gavlarnas
   fasadliv och vid takfoten vid takbalkarnas ände, 70 mm utanför fasaden. Vindskivor, vindskivebeslag,
   takfotsplåtar och hängrännor saknas; detaljen behöver bestämmas.
