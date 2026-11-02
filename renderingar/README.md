# Renderingar

Inomhusbilderna I01–I30 ur den kodgenererade modellen (Blender, Cycles) och ritningen över var de är tagna.

```
./rendera.sh                          # alla 30 i 4K (3 840 × 2 160), slutlig kvalitet, till inne/
./rendera.sh I05 I07                  # bara några (namnen eller början av dem)
./rendera.sh --kvalitet normal        # 1 920 × 1 080 (skiss 640, utkast 1 280)
./rendera.sh --ljus 12 21 13:00 mulet # ett annat dagsljus: månad, dag, klocka, väder (sol, lätt mulet, mulet)
```

Bilderna hamnar i `inne/` och versionshanteras inte. Kameraplanen [`kameraplan.pdf`](kameraplan.pdf) (I-01, i
ritningsmallen) visar kamerornas lägen, riktningar och bildvinklar på plan 1 och i källaren med en förteckning över
bilderna; skriptet ritar den också (`./mod kameraplan` i `verktyg/modellering`, ur STEP-filen, så bygg den först med
`./mod bygg`).

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

En bild i 4K och slutlig kvalitet (högst 512 sampel per pixel, brusreducerad) tar knappt 4 minuter att rendera på
en Mac med Apple M5 Max (Metal), och scenen tar ungefär en minut att bygga, en gång per körning; hela serien tar
omkring två timmar.
