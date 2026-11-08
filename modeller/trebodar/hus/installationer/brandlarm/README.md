# Brandlarmet

Brandvarnarna (BBR: nya bostäder ska ha brandvarnare) som data i modellen: brandvarnare för 230 V med
reservbatteri, trådbundet sammankopplade, så att alla larmar när en larmar. Radio genom betongbjälklaget mellan
källaren och plan 1 vore osäkert, därför kabel. Brandlarmet är en egen installation, skild från elinstallationen fast
det matas från elcentralen. Samma data ger modellens geometri (varnarna, dosorna och kablarna i 3D), genomföringarna,
kontrollen och ritningen. Brandlarmet ingår inte i modellens krockkontroll; det har en egen kontroll som redovisar
genomföringarna och krockarna mot husets delar och de andra installationerna.

```
cd verktyg/modellering
./mod brandlarm kontroll     # sammankopplingen, varnarnas plats, genomföringarna och krockarna mot husets delar och
                             # de andra installationerna
./mod brandlarm lista        # varnare, dosor, kablar och genomföringar (ut/brandlarm/brandlarm.md)
./mod brandlarm ritning      # ritningen B-01 (ut/brandlarm/B-01 Brandlarm.pdf, kräver STEP-filen: ./mod bygg)
```

## Filerna

| Fil | Innehåll |
|---|---|
| [`larm.py`](larm.py) | Typerna och måtten, varnarnas och dosornas lägen, kablarnas vägar, stigarna, kontrollen, genomföringarna och utdraget för ritningen |
| [`brandlarm.py`](brandlarm.py) | Geometrin under `Hus/Installationer/Brandlarm`: brandvarnarna med sina dosor, kopplingsdosorna och kablarna som raka bitar längs vägarna |

Monteringens punkter ([`../montering.py`](../montering.py): `tak`, `kallartak`, `vid_tak`, `i_vagg`,
`under_kallartak`), stigarna mellan järnen ([`../strak.py`](../strak.py): `mellan_jarnen`), installationsskiktets
läkt ([`../el/lakt.py`](../el/lakt.py)) och genomföringarna ([`../genomforingar.py`](../genomforingar.py)) är
gemensamma med de andra installationerna.

## Placeringen

En brandvarnare i varje huvudutrymme, högt i taket nära rummets mitt, eftersom röken tar lång tid till andra rum under
de höga snedtaken:

- **Plan 1**: köket (BV-KO), sovrummet (BV-SV), vardagsrummet (BV-VR) och hallen (BV-HA), i snedtaket
  `AVSTAND_NOCK` (600 mm) från nocken i takets plan, mitt mellan installationsskiktets läkt. Takdosan sitter i skiktet
  bakom gipsen.
- **Källaren**: vid trappan (BV-KT) och i det öppna rummet norr om den (BV-KN), på en utanpåliggande dosa i
  betongtaket.

Kontrollen kräver minst 500 mm till väggarna och redovisar höjden över golvet, avståndet till nocken och armaturer
närmare än 500 mm (ljuslinjerna i källaren längs hela den lysande linjen).

## Kablarna

Kabeln är en installationskabel 4G1,5 (fas, nolla, skyddsjord och larmledaren), Ø `KABEL_D`:

- **Stammen** går klammad under källarens tak från matningsdosan D01 (där matningen från elcentralen kommer in;
  centralens läge är inte bestämt) via BV-KT och BV-KN och kopplingsdosorna DV, DM och DH, runt ljuslinjerna
  (`X_K02`, `Y_K08`).
- **Stigarna**: innertakets installationsskikt slutar vid dalbalkarna, så huskropparna förbinds i källaren, med en
  stigare per huskropp: genom väggen 1A till hallen och vardagsrummet, 2A till sovrummet och L4 till köket. Stigaren
  går genom mellanbjälklaget i en hylsa, fri från armeringens järn och de ingjutna rören (tappvattnet, golvvärmen och
  elens rör), och upp i ett regelfack i väggen (`stigaren`).
- **I innertaket** går kabeln i installationsskiktets övre del, `OVER_MITT` över skiktets mitt, så att den går över
  elens rör, som ligger mitt i skiktet, och raka vägen till varnarnas takdosor.

Kablarnas id är K01–K09 (från, till och väg i `brandlarm()`).

## Kontrollen

`./mod brandlarm kontroll`:

- **Fel**:
  - en varnare som inte nås från matningsdosan;
  - ett plan utan varnare;
  - en takdosa som tar i läkten;
  - en varnare närmare väggen än 500 mm;
  - genomföringar som inte går;
  - krockar med de andra installationerna eller armeringen.
- **Anmärkningar**:
  - krockar med stommen och skikten (kabeln borras genom syll och hammarband);
  - varnarnas höjd och avstånd till nocken;
  - kabelns totala längd.
