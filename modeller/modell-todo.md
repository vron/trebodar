# Att ändra i modellen

Det som ska ändras i modellen (`modeller/trebodar`) för att den ska stämma med handlingarna. Punkterna tas bort när ändringen finns i modellen.

**Hitta platsen.** Lägen anges i K-05:s koordinater (x, y från skärningen mellan mellanbjälklagets kanter, z från bjälklagets överkant), samma som modellens. Delarnas namn är modellens (Onshape-modellens namn finns i `modeller/referens/namntabell.csv`).

**När modellen är uppdaterad:** kör `./mod kontroll` i `verktyg/modellering` och kontrollerna i `verktyg/modellanalys`. Beräkningarna läser inte modellen; där handlingarna ska följa ändringen rättas deras källfiler för hand, och sedan körs K-03, K-05, K-06, R-04, R-05, R-06 och R-03.

## Handlingarna (uppdateras när modellen är klar)

1. **K-01 med modellens stolplägen under nockbalk 1** (stöd B, C och D: LN1_1 y 2 795, LN1_2 4 686 och huvudstolpen
   6 602 i stället för 2 870, 4 770 och 6 670), sedan K-05:s `laster.py` och följande.
2. **K-03:s `geometri.json` efter modellen** (`kontroll_k03.py` redovisar skillnaderna): takets lyft 10 mm,
   takstolarnas diagonaler till balkens underkant och 2NO med 7 stavar, stolparna LN1_1 (ny), LD2_1, LD2_2 och LD4_2,
   reglarna 45–2 445, huvudstolpen med strävor på båda sidor och dalbalkarnas överkant i takplanens skärning (U-03).
   K-05:s `laster.STOLPLAGEN` för LD4_2: 4 438 → 4 392.
3. **Plattan på mark med L-element 500 (AR-02):** K-06 (cellplast 350, fyllningen bakom V3 och V20 upp till
   makadamens underkant −650), R-05 och R-03, och K-05 och R-06: betongen slutar vid L-elementens rygg, 70 mm
   innanför konturen vid de fria kanterna.
4. **U-03:** texten hänvisar till modell-todo punkt 7, som är gjord.

## Kontrollera och bestäm

5. **Marken mot K-06.** K-06:s fyllnadshöjder ligger över Onshape-modellens mark vid V7 och V18 (sovrumsavsatsen,
   överkant −742; K-06 −250) och V21 (uppfyllnaden −807 … −670); modellen följer K-06 inom 1,5 m från väggarna. På höger
   huskropp täcker K-06:s fyllning fasadstenen (AR-01, från z −2 150) vid V1 (fyllning till −450), V9 (−2 250 … −1 450)
   och V14 (−1 450 … −450). Bestäm marknivåerna där (och AR-01:s utbredning eller K-06:s fyllnadshöjder).
6. **Toppklossar på gavelstolarna.** Balken slutar i gavelväggens utsida, så gavelstolarna har bara en kloss, på
   insidan, och balken vilar på 90 mm (45 + 45) i stället för 135 mm. Kontrollera i K-03 eller ändra detaljen.

## Saknas i modellen

7. **Lätta innerväggar enligt planritning 201 rev 02.** Bara syllarna finns (`Syllar lätta väggar`, Onshape-modellens
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
8. **Takutsprång.** Planritning 201 visar takutstick 100 runt hela huset. I modellen slutar takets skikt i gavlarnas
   fasadliv och vid takfoten vid takbalkarnas ände, 70 mm utanför fasaden. Vindskivor, vindskivebeslag,
   takfotsplåtar och hängrännor saknas; detaljen behöver bestämmas.
