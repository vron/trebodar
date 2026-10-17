# R-03 rev A – Bärande system i betong, översikt i 3D

Ett blad (A3, den gemensamma mallen i [`../ritningsmall`](../ritningsmall/)) som visar betongarbetets bärande delar i 3D, utan mått, i den ordning de byggs: bottenplattan (delvis bortskuren, så att balkar, plintar, L-element och cellplast syns), källarväggarna och rören, mellanbjälklaget (delvis bortskuret) och ett snitt genom källarens västra del. Trästommen på plan 1 ingår inte.

| Fil | Innehåll |
|---|---|
| `scen.py` | Delarna i 3D ur samma geometri som R-04, R-05 och R-06 (`../R-05/kallare.py`) |
| `rendera.py` | Renderare: parallellprojektion, djupbuffert, platt skuggning och konturer |
| `ritningar.py` | Vyerna, hänvisningarna (placeras automatiskt på vit yta, utan korsande linjer) och bladet |

## Köra

```
python beräkningar/R-03/ritningar.py      # ritningar/R-03 Bärande system i betong.pdf
```

Bilderna och bladet skapas i `blad/` (versionshanteras inte).
