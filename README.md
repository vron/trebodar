# Fritidshus Trebodar

Konstruktionshandlingar för Fritidshus Trebodar, Resö, Tanum: den kodgenererade modellen, beräkningarna, rapporterna och ritningarna.

- **Modellen i 3D:** https://vron.github.io/trebodar/
- **Handlingarna** (rapporter, ritningar och kameraplanen, byggda ur `main`): https://vron.github.io/trebodar/handlingar/

Webbplatsen byggs och publiceras av GitHub Actions ([`.github/workflows/bygg.yml`](.github/workflows/bygg.yml)) vid varje push till `main`. En tagg `rev-*` på `main` (t.ex. `rev-B`) publicerar dessutom handlingarna som en release.

## Bygga lokalt

```sh
./bygg            # allt som är inaktuellt: modellen, webbvisaren (docs/), beräkningarna, rapporterna och ritningarna
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
