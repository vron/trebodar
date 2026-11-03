# Fritidshus Trebodar

Konstruktionshandlingar för Fritidshus Trebodar, Resö, Tanum: den kodgenererade modellen, beräkningarna, rapporterna och ritningarna.

- **Webbplatsen:** https://vron.github.io/trebodar/ – projektet, bilderna, planerna och handlingsförteckningen med
  rapporterna, ritningarna och kameraplanen (byggda ur `main`)
- **Modellen i 3D:** https://vron.github.io/trebodar/modell/
- **Renderingarna** på planerna (klicka på en kamera för bilden; renderas lokalt och publiceras med `renderingar/publicera.sh`): https://vron.github.io/trebodar/renderingar/

Webbplatsen byggs och publiceras av GitHub Actions ([`.github/workflows/bygg.yml`](.github/workflows/bygg.yml)) vid varje push till `main`. En tagg `rev-*` på `main` (t.ex. `rev-B`) publicerar dessutom handlingarna som en release.

## Bygga lokalt

```sh
./bygg            # allt som är inaktuellt: modellen, beräkningarna, rapporterna, ritningarna och webbplatsen (docs/)
./bygg --lista    # stegen och om de är aktuella
./bygg R-05       # en ritning och det den bygger på
```

Kräver [`uv`](https://docs.astral.sh/uv/) och typsnittet Carlito; Pythonmiljöerna skapas av skriptet. De genererade filerna hamnar på samma ställen som förut (`rapporter/`, `ritningar/`, `docs/` …) men versionshanteras inte. Undantagen är de tunga beräkningarnas resultat och rapporter, som räknas lokalt och checkas in. Se [`verktyg/bygg/README.md`](verktyg/bygg/README.md).

## Mappar

| Mapp | Innehåll |
|---|---|
| [`beräkningar/`](beräkningar/) | Källor per handling: indata, beräkning, rapportmall; `ritningsmall/` är den gemensamma A3-mallen |
| [`modeller/`](modeller/) | Den kodgenererade modellen (`trebodar/`), Onshape-modellen (`referens/`, fryst), balkar och balkplåtar |
| [`verktyg/`](verktyg/) | Modellering (`./mod`), modellanalys (`./ma`) och bygget (`./bygg`) |
| `rapporter/`, `ritningar/` | Byggda handlingar; bygglovsritningarna 200 och 201 är färdiga pdf:er utan källa |
| [`renderingar/`](renderingar/) | Inomhusbilderna (Blender) och kameraplanen |

Instruktionerna för arbetet står i [`CLAUDE.md`](CLAUDE.md).
