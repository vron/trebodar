# Att ändra i modellen

Det som ska ändras i modellen (`modeller/trebodar`) för att den ska stämma med handlingarna. Punkterna tas bort när ändringen finns i modellen.

**Hitta platsen.** Lägen anges i K-05:s koordinater (x, y från skärningen mellan mellanbjälklagets kanter, z från bjälklagets överkant), samma som modellens. Delarnas namn är modellens (Onshape-modellens namn finns i `modeller/referens/namntabell.csv`).

**När modellen är uppdaterad:** kör `./mod kontroll` i `verktyg/modellering` och kontrollerna i `verktyg/modellanalys`. Beräkningarna läser inte modellen; där handlingarna ska följa ändringen rättas deras källfiler för hand, och sedan körs K-03, K-05, K-06, R-04, R-05, R-06 och R-03.

## Grunden (K-06, R-04)

1. **Valfritt: bottenplattans balkar, plintar och L-element.** Bottenplattan är i modellen 100 mm betong på 200 mm cellplast i hela källaren. Enligt R-04 har den också kantbalkar och balkar under innerväggarna 450 × 200 och plintar under rören (600–1 200 mm, R-04.1), alla på 100 mm S300, och längs kanten L-element S300, höjd 300 och bredd 600 (ryggen 100, avfasad upptill), med ytterkanten i väggarnas ytterliv; betongen börjar 100 mm innanför, i kärnans yttre yta.

## Kontrollera och bestäm

2. **Stolparnas lägen under nockbalk 1 mot K-01.**

    | Stöd | K-01 | Modellen |
    |---|---|---|
    | B | y 2 870 | LN1_1 vid 2 795 |
    | C | y 4 770 | LN1_2 vid 4 686 |
    | D | y 6 670 | huvudstolpen vid 6 602 |

    Skillnaden är 68–84 mm. Antingen flyttas stolparna, eller så räknas K-01 om med modellens lägen; säg till vilket.

3. **Syll utan vägg vid LN1_2.** Syllen `LN1_2-S01`, x 10 980–13 745, y 4 651–4 721, ligger utan vägg. Stolpen LN1_2 står fristående, och K-03 räknar den så. Finns en vägg där, modellera den; annars tas syllen bort.

4. **Marken mot källarväggarna.** Glipor mellan fyllning och berg vid V2 (y 10 865, x 4 545–9 645) och V16 (x 9 645, y 10 865–12 365). Ingen mark vid V9 (y 1 145, x 11 240–13 665) och V17 (x 9 165, y 145–1 145). Modellera marken där; fyllnadshöjderna i K-06 kontrolleras mot den.

## Saknas i modellen

5. **Lätta innerväggar.** Bara syllarna (`Syllar lätta väggar`) finns; väggarna med reglar och gips saknas (Onshape-modellen hade gipsskivorna som massiva kroppar, `gyp_w_*`). Modellera dem som regelväggar med gips på båda sidor.
6. **Toppklossar på gavelstolarna.** Balken slutar i gavelväggens utsida, så gavelstolarna har bara en kloss, på insidan, och balken vilar på 90 mm (45 + 45) i stället för 135 mm. Kontrollera i K-03 eller ändra detaljen.
