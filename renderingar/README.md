# Renderingar

Inomhusbilderna I01–I30 och de andra vyerna (ute och detaljer) ur den kodgenererade modellen (Blender, Cycles),
ritningen över var inomhusbilderna är tagna och webbplatsens sida med alla kamerorna på planerna:
https://vron.github.io/trebodar/renderingar/.

```
./rendera.sh                          # inomhusbilderna I01–I30 i 2K (2 048 × 1 152), slutlig kvalitet, till inne/
./rendera.sh I05 I07                  # bara några (namnen eller början av dem)
./rendera.sh --ute                    # de andra vyerna (ute-*, detalj-*, stomme) till ute/
./rendera.sh --kvalitet normal        # 1 920 × 1 080 (skiss 640, utkast 1 280)
./rendera.sh --ljus 12 21 13:00 mulet # ett annat dagsljus: månad, dag, klocka, väder (sol, lätt mulet, mulet)
./publicera.sh                        # alla renderade bilder till webbplatsen
./publicera.sh I05 I07                # bara några
./publicera.sh --lokalt               # bara till docs/renderingar/bilder (för ./bygg lokalt), utan att ladda upp
```

Bilderna hamnar i `inne/` och `ute/` och versionshanteras inte. Bredvid varje bild står vyns data när den
renderades (`<namn>.json`: kamera, mål, objektiv, ljus, kvalitet, tid och modellens version). Kameraplanen
[`kameraplan.pdf`](kameraplan.pdf) (I-01, i ritningsmallen) visar kamerornas lägen, riktningar och bildvinklar på
plan 1 och i källaren med en förteckning över bilderna; skriptet ritar den också (`./mod kameraplan` i
`verktyg/modellering`, ur STEP-filen, så bygg den först med `./mod bygg`).

## På webbplatsen

Sidan [renderingar](https://vron.github.io/trebodar/renderingar/) visar plan 1, källaren och huset ute med alla
vyernas kameror (läge, riktning och bildvinkel). Ett klick på en kamera visar bilden över hela fönstret; piltangenterna
eller ett svep går till nästa, Esc stänger, och adressen (`#<namn>`) går att dela. Startsidan visar bilderna i
ett galleri, med bildtexterna ur `TEXTER` i `vyer.py`.

Planerna och kamerorna byggs ur modellen vid varje bygge (`./bygg kameraplan`, även i GitHub Actions), men bilderna
renderas inte där: rendering tar för lång tid. `./publicera.sh` (`./mod publicera`) gör om de renderade bilderna till
JPEG i fyra bredder (480, 960, 1 920 och 3 840 px, högst bildens egen), laddar upp dem med förteckningen `renderingar.json` till releasen
[`bilder`](https://github.com/vron/trebodar/releases/tag/bilder) på GitHub (bilderna hamnar alltså inte i git) och
startar ett nytt bygge av webbplatsen, som hämtar dem därifrån. En publicering ersätter bara de bilder den tar med;
vyer som har tagits bort ur `vyer.py` tas bort. Kräver `gh` (inloggad). En kamera som har flyttats i `vyer.py` sedan
bilden renderades märks på sidan, och kameror utan bild visas ofyllda.

## Bilderna

Namnen är `<nummer>-<rum>-<vy>-<objektiv>`, t.ex. `I05-allrum-mot-hall-vid`. Två objektiv:

- **öga**: 40 mm i ögonhöjd 1,60 m, bildvinkeln 48° och perspektivet som när man står i rummet.
- **vid**: 20 mm på 1,45 m, bildvinkeln 84°, som vanliga vidvinkelbilder av rum.

Kameran hålls vågrät och bilden flyttas i höjdled med objektivförskjutning, så att lodräta linjer blir lodräta
(utom I28, trappan ned, där kameran lutar). Kamerorna och rummens namn står i
[`modeller/trebodar/vyer.py`](../modeller/trebodar/vyer.py) (`_INNE`, `RUMSNAMN`).

## Ljus och exponering

Dagsljuset är 20 april kl. 14.00 med sol (`INNE_LJUS` i `vyer.py`), räknat för platsen: solens riktning, färg och
styrka och himlens ljus (`./mod ljus 4 20 14:00 sol`). Himlen lyser in genom ljusportaler i fönstren, och utanför
syns omgivningen ur öppna geodata (`./mod omgivning --hamta`, sparas i `lokalt/omgivning/`; utan den en enkel mark).
Exponeringen och vitbalansen räknas fram ur en snabb förhandsbild per bild, som ögats anpassning till rummets ljus.
I källaren (I28–I30) är taklamporna tända (`LAMPOR` i `vyer.py`), eftersom de små fönstren ger för lite ljus.

En bild i 2K och slutlig kvalitet (högst 512 sampel per pixel, brusreducerad) tar omkring en minut att rendera på
en Mac med Apple M5 Max (Metal), och scenen tar ungefär en minut att bygga, en gång per körning.
