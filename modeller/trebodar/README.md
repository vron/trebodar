# Trebodar – kodgenererad modell

Husets 3D-modell som kod. Mappstrukturen följer modellträdet: varje montage är en mapp med en fil med samma namn
(`hus/stomme/stomme.py`) som sätter ihop montagets delar. Bygg och kontrollera med ramverket i
[`verktyg/modellering`](../../verktyg/modellering/) (`./mod bygg`, `./mod kontroll`).

Koordinater som i K-05 (mm): x och y från skärningen mellan mellanbjälklagets kanter, z från bjälklagets överkant.
Den gemensamma geometrin (huskroppar, väggarnas lägen, takfallen, nock- och dalbalkarna, nivåer) står i
[`skelett.py`](skelett.py), material i [`material.py`](material.py) och gemensamma byggdelar (regelväggar, takstolar,
takbalkar, virke) i [`byggdelar/`](byggdelar/).

## Modellträdet

```
Trebodar
└── Hus
    └── Stomme
        ├── Stomme prefab        trästommen ovanför mellanbjälklaget (en beställning)
        │   ├── Ytterväggar      Vägg 1NO … 3NV
        │   ├── Innerväggar      Vägg 1A–1D, 2A–2C, syllar för lätta väggar
        │   ├── Takstolar        Takstol 1NO, 1SV, 2NO, 2C, 2SV, 3NO, 3SV
        │   ├── Stolpar          LN1_1, LN1_2, LN1_3, LD4_1
        │   └── Takbalkar        Takfall 1SO, 1NV, 2SO, 2NV, 3SO, 3NV
        └── Nock- och dalbalkar  NB1, DB2, NB3, DB4, NB5 (en egen beställning, K-01)
```

## Namn

- Huskroppar 1 (vänster), 2 (mittre), 3 (höger). Ytterväggar: kropp och väderstreck, `1NO`, `1SO`, `1SV`, `1NV` osv.
  Bärande innerväggar: kropp och bokstav i växande y, `1A`–`1D`, `2A`–`2C`. Takstolar heter som väggen de står på.
  Takfall heter som takfotsväggen (`1SO` är vänstra huskroppens takfall mot SO).
- Nock- och dalbalkar NB1, DB2, NB3, DB4, NB5 (K-01), stolpar LN…, LD… och LA… (K-03, K-05), takfönster TF1–TF3.
- Delar: `<montage>-<typ><nr>`, numrerade längs väggen eller takfallet: S syll, H hammarband, R regel, L liggande
  (överstycke, bröstning), D diagonal, U underram, X sned del under taket, K kloss eller kortling, P plåt, T takbalk,
  A avväxling, UR upplagsregel. Delar som hör till en stolpe i handlingarna heter som stolpen (`LD2_1-1`).
