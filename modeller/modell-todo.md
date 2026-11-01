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

7. **Takutsprång.** Planritning 201 visar takutstick 100 runt hela huset. I modellen slutar takets skikt i gavlarnas
   fasadliv och vid takfoten vid takbalkarnas ände, 70 mm utanför fasaden. Vindskivor, vindskivebeslag,
   takfotsplåtar och hängrännor saknas; detaljen behöver bestämmas.
