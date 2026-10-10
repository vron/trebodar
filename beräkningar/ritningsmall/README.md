# Ritningsmall A3

Gemensam mall för alla ritningar (R-01 … R-05, U-02), A3 liggande, i samma stil som beräkningsrapporterna (Carlito, tunna linjer, ljusa fyllningar). Ram, ritningshuvud, linjetyper och färger ändras på ett ställe och gäller alla ritningar.

| Fil | Innehåll |
|---|---|
| `ritning.typ` | Bladet: ram (20 mm inbindning, 10 mm övriga), högerkolumn med anvisningar, teckenförklaring och tabeller, revisioner och ritningshuvud. Linjetyper (`STIL`) och fyllningar (`FYLL`). Ritar vyernas lager i ordning |
| `ritning.py` | `Vy` (skala, modellfönster, lager) med linjer, ytor, text, måttlinjer och måttkedjor (snedstreck), hänvisningar, positionsbubblor, fördelningslinjer, brottlinjer, snittmarkeringar och skalstock. `huvud()` och `Blad` (skriver JSON, kompilerar bladet och slår ihop en ritningsseries blad till en pdf med `Blad.serie`) |
| `projekt.json` | Projektets fasta uppgifter i ritningshuvudet: projekt, fastighet, upprättad, signatur |

Allt ritas i verkliga koordinater (mm, y uppåt). `Vy` räknar om till papperets mm, så att 1 mm på papperet är `skala` mm i verkligheten vid utskrift på A3 i 100 %. Bara linjetjocklekar, textstorlekar och avstånd för mått och etiketter anges i pappersmått. Elementen läggs i namngivna lager (`with v.lager("armering_uk"): ...`), som ritas i den ordning de skapas och kan döljas vid kompileringen.

Ett blad kan också kompileras direkt:

```
typst compile --root <repo> --input blad=/sökväg/till/blad.json [--input dolj=lager1,lager2] beräkningar/ritningsmall/ritning.typ ut.pdf
```

Varje ritningsserie blir en pdf i `ritningar/` med ett blad per sida; bladen kompileras var för sig och slås ihop. Exempel: [`../R-03/ritningar.py`](../R-03/ritningar.py).
